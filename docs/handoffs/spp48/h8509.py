"""SPP-48 instrument: SPP-54's C-3 feasibility check, re-run with the repaired levels.

SPP-54 stopped before any solve because one hour of the 2025-12-21 window —
**h8509** (12-21 13:00) — was feasible under the two-zone wind inputs (+440 MW
regional margin) and infeasible under the three-zone ones (-545 MW), at an
identical system total, identical demand, identical thermal availability and an
identical 3,400 MW import. That flip was the six-largest-plants LEVEL rule, not
the SPS pocket (FINDING-spp-54 §4.2 C-4). This re-runs the same arithmetic with
R-LEVEL.

Everything except wind is taken verbatim from SPP-54's committed
``docs/handoffs/spp54/dec21_window_2025.csv`` — the three-zone demand
(N / S / SPS), the thermal + hydro capability **net of keeper-3's own
availability arrays** and the regional solar, all produced by
``run_year(fleet_only=True)`` on keeper-3's recipe at design commit
``8d427adc``. Only the wind terms are replaced, so the comparison isolates the
level rule exactly as SPP-54's did.

SPP-54's margin, unchanged::

    region margin = th_S + th_SPS + w_S + w_SPS + solar + 3,400 - (d_S + d_SPS)

Four wind columns are reported per hour, because the repair moves BOTH sides of
SPP-54's comparison (PRECOMMIT §4 M2):

  (a) three-zone repaired      (b) two-zone repaired
  (c) three-zone as-built      (d) two-zone as-built  <- keeper-3's current input

and the STOP leg is SPP-54's own: is any window hour infeasible under the
three-zone inputs that was feasible under the two-zone inputs?

Zero LP.

usage:
  python docs/handoffs/spp48/h8509.py --three-zone-after <dir> --two-zone-after <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import renewables as rn  # noqa: E402

sys.path.insert(0, str(REPO / "docs/handoffs/spp48"))
from wind_delta import backcast_cf_profile  # noqa: E402

YEAR = 2025
WINDOW = list(range(8496, 8521))
NS_TTC = 3400.0  # the SPP-53 North<->South rating, as SPP-54's C-3 used it
ZONES3 = ["SPP-North", "SPP-South", "SPP-SPS"]
ZONES2 = ["SPP-North", "SPP-South"]


def zonal_wind_mw(zones: list[str], shape_dir: Path, monthly: np.ndarray) -> np.ndarray:
    """Return per-zone wind potential MW for one zone map and one shape build.

    Args:
        zones: Ordered model-zone names.
        shape_dir: Wind-shape directory to read.
        monthly: ``(n_zones, 12)`` operable wind capacity by month for ``zones``.

    Returns:
        A ``(n_zones, 8760)`` per-zone wind potential in MW.
    """
    cfg = ScenarioConfig(iso="SPP", mode="backcast")
    cf_profile = backcast_cf_profile("SPP", YEAR, monthly)
    installed = float(monthly[:, -1].sum())
    shapes = rn._wind_zone_reanalysis_shapes(
        "SPP", "wind", zones, YEAR, data_dir=shape_dir, config=cfg
    )
    if shapes is None:
        raise SystemExit(f"no per-zone wind shape for {zones} in {shape_dir}")
    cf, cap = rn._distribute_by_eia860(cf_profile, installed, monthly, True, shapes)
    return cap[:, None] * cf


def main() -> int:
    """Re-run SPP-54's C-3 with the repaired levels and print the verdict."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--three-zone-after", type=Path, required=True)
    ap.add_argument("--two-zone-after", type=Path, required=True)
    ap.add_argument(
        "--three-zone-before",
        type=Path,
        default=None,
        help="the as-built three-zone shapes (SPP-54's, rebuilt at 8d427adc)",
    )
    ap.add_argument(
        "--two-zone-before", type=Path, default=REPO / "data/raw/spp-wind-shape"
    )
    ap.add_argument("--out", type=Path, default=REPO / "docs/handoffs/spp48/h8509.csv")
    args = ap.parse_args()

    base = pd.read_csv(REPO / "docs/handoffs/spp54/dec21_window_2025.csv").set_index(
        "hour"
    )
    monthly3 = rn._eia860_monthly_capacity("SPP", "wind", ZONES3, YEAR)
    # The two-zone map is the three-zone one with SPS folded back into South —
    # the same reconstruction SPP-54's wind_reconcile.py used, so the two runs
    # differ ONLY in where the boundary sits.
    monthly2 = np.vstack([monthly3[0], monthly3[1] + monthly3[2]])

    w3a = zonal_wind_mw(ZONES3, args.three_zone_after, monthly3)
    w2a = zonal_wind_mw(ZONES2, args.two_zone_after, monthly2)
    w2b = zonal_wind_mw(ZONES2, args.two_zone_before, monthly2)
    w3b = (
        zonal_wind_mw(ZONES3, args.three_zone_before, monthly3)
        if args.three_zone_before
        else None
    )

    print(
        "\nSPP-48 / SPP-54 C-3 re-run, 2025-12-21 window. Demand, thermal+hydro "
        "availability and solar are SPP-54's committed fleet_only values; only wind moves.\n"
    )
    print(
        f"  {'h':>5} {'wS+wSPS':>9} {'wS(2z)':>9} | {'margin 3z':>10} {'margin 2z':>10} "
        f"{'delta':>8} | {'as-built 3z':>12} {'as-built 2z':>12} | STOP?"
    )
    rows = []
    for h in WINDOW:
        r = base.loc[h]
        fixed = (
            r["thermal_hydro_avail_south"]
            + r["thermal_hydro_avail_sps"]
            + r["solar_region"]
            + NS_TTC
            - (r["demand_south"] + r["demand_sps"])
        )
        reg3a = w3a[1, h] + w3a[2, h]
        m3a, m2a = fixed + reg3a, fixed + w2a[1, h]
        m3b = fixed + (w3b[1, h] + w3b[2, h]) if w3b is not None else np.nan
        m2b = fixed + w2b[1, h]
        stop = bool((m3a < 0) and (m2a >= 0))
        print(
            f"  {h:>5} {reg3a:>9.0f} {w2a[1, h]:>9.0f} | {m3a:>+10.0f} {m2a:>+10.0f} "
            f"{m3a - m2a:>+8.3f} | {m3b:>+12.0f} {m2b:>+12.0f} | {'STOP' if stop else 'ok'}"
        )
        rows.append(
            {
                "hour": h,
                "wind_region_3z_after": float(reg3a),
                "wind_south_2z_after": float(w2a[1, h]),
                "margin_3z_after": float(m3a),
                "margin_2z_after": float(m2a),
                "margin_3z_before": float(m3b),
                "margin_2z_before": float(m2b),
                "stop": stop,
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(args.out, index=False)

    dmax = float(np.abs(df["margin_3z_after"] - df["margin_2z_after"]).max())
    print(
        f"\nC-3 verdict (repaired): hours the three-zone inputs make infeasible while the "
        f"two-zone inputs were feasible: {int(df['stop'].sum())} -> "
        f"{'STOP' if df['stop'].any() else 'PASS'}"
    )
    print(
        f"P2 end-to-end: max |margin_3z - margin_2z| over the window = {dmax:.6f} MW "
        f"(the ex-ante prediction is 0 — a boundary change cannot move the region's own wind)"
    )
    h = 8509
    row = df[df["hour"] == h].iloc[0]
    print(
        f"\nh8509 (SPP-54's STOP hour): repaired three-zone margin "
        f"{row['margin_3z_after']:+.0f} MW; repaired two-zone {row['margin_2z_after']:+.0f}; "
        f"as-built three-zone {row['margin_3z_before']:+.0f}; as-built two-zone "
        f"{row['margin_2z_before']:+.0f} (SPP-54 read -545 / +440)"
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
