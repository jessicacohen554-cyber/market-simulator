"""SPP-48 instrument: the identity legs and the before/after wind delta, per ISO.

Builds the LP's wind bound through the REAL path — ``_eia860_monthly_capacity ->
(the backcast cf_profile selection) -> _wind_zone_reanalysis_shapes ->
_distribute_by_eia860`` — twice for the same ISO-year: once from the committed
(six-largest-plants) wind-shape parquets and once from the repaired (R-LEVEL,
whole-fleet) ones, and reports

  C-1  the redistribution identity  Sum_z cap_z cf_z(t) == M(t), max relative
       error over all 8,760 hours, for BOTH builds (PRECOMMIT P3)
  C-2  every cf <= 1 and no water-filling overflow lost, for BOTH builds
  C-5  the model-level partition-consistency residual: how far the model's own
       per-zone weight cap_z is from being proportional to the builder's own
       per-zone capacity sum C_z (PRECOMMIT §3.1 — the only thing that keeps P2
       from carrying end-to-end exactly)
  D-1  per-zone annual wind potential (TWh) before and after, and the implied
       change to the LP's wind upper bound cap_z*cf_z(t): annual, mean |.|,
       p1/p99, max, and the December-window hours

Zero LP: every number is arithmetic over committed inputs plus the repaired
shapes. Nothing here writes to the solve path.

usage:
  python docs/handoffs/spp48/wind_delta.py --iso SPP  --after <dir> [--years ...]
  python docs/handoffs/spp48/wind_delta.py --iso MISO --after <dir>
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

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import wind_shape_dir  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import renewables as rn  # noqa: E402
from scripts.lib import wind_shape as ws  # noqa: E402

# The 2025-12-21 window SPP-54's C-3 is scored on (local hours 00:00 -> 24:00).
WINDOW = range(8496, 8521)


def backcast_cf_profile(iso: str, year: int, monthly: np.ndarray) -> np.ndarray:
    """Return the ISO-wide wind CF series a backcast solve would use.

    Mirrors ``renewables.load_renewable_profiles``' own selection for
    ``fuel="wind"`` in backcast mode: the measured HSL profile when the ISO-year
    has one, else the forecast uncurtailed CF for a high-curtailment ISO with a
    reference rate, else the delivered EIA-930 profile.

    Args:
        iso: ISO identifier.
        year: Calibration year.
        monthly: ``(n_zones, 12)`` operable wind capacity by month.

    Returns:
        A ``(HOURS_PER_YEAR,)`` ISO-wide hourly CF series.
    """
    cf = rn._hsl_cf_profile(iso, year, "wind", monthly)
    if cf is None and iso in rn._UNCURTAILED_FALLBACK_ISOS:
        cf = rn._forecast_uncurtailed_cf(iso, year, "wind", monthly)
    if cf is None:
        cf = rn._eia_hourly_cf_profile(iso, year, "wind", monthly)
    return cf


def build_bound(
    iso: str, year: int, zones: list[str], shape_dir: Path | None, cfg: ScenarioConfig
) -> dict:
    """Return the LP's per-zone wind bound and its identity legs for one build.

    Args:
        iso: ISO identifier.
        year: Calibration year.
        zones: Ordered model-zone names.
        shape_dir: Wind-shape directory to read; ``None`` uses the ISO's
            registered (committed) directory.
        cfg: Scenario config carrying the per-ISO wind-shape gate.

    Returns:
        ``{"mw": (n_zones, 8760) potential MW, "cap": per-zone MW, "M": system
        MW, "rel": max relative identity error, "lost": lost-overflow hours,
        "max_cf": max per-zone CF, "shapes": the raw per-zone shapes}``.
    """
    monthly = rn._eia860_monthly_capacity(iso, "wind", zones, year)
    cf_profile = backcast_cf_profile(iso, year, monthly)
    installed = float(monthly[:, -1].sum())
    shapes = rn._wind_zone_reanalysis_shapes(
        iso, "wind", zones, year, data_dir=shape_dir, config=cfg
    )
    if shapes is None:
        raise SystemExit(f"no per-zone wind shape for {iso} {year} in {shape_dir}")
    cf, cap = rn._distribute_by_eia860(cf_profile, installed, monthly, True, shapes)
    cf_flat, _ = rn._distribute_by_eia860(cf_profile, installed, monthly, True, None)
    system = (cap[:, None] * cf_flat).sum(axis=0)
    mw = cap[:, None] * cf
    total = mw.sum(axis=0)
    return {
        "mw": mw,
        "cap": cap,
        "M": system,
        "rel": float((np.abs(total - system) / np.maximum(system, 1.0)).max()),
        "lost": int((total < system - 1e-6).sum()),
        "max_cf": float(cf.max()),
        "shapes": shapes,
        "monthly": monthly,
    }


def main() -> int:
    """Run the identity legs and the before/after delta for one ISO."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--after", type=Path, required=True, help="repaired shape dir")
    ap.add_argument(
        "--before",
        type=Path,
        default=None,
        help="baseline shape dir (default: the ISO's committed directory)",
    )
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out", type=Path, default=None, help="CSV to write")
    args = ap.parse_args()

    iso = args.iso.upper()
    zones = list(get_iso_config(iso).zone_names)
    before_dir = args.before or wind_shape_dir(iso)
    cfg = ScenarioConfig(iso=iso, mode="backcast")
    rows: list[dict] = []

    for year in args.years:
        before = build_bound(iso, year, zones, before_dir, cfg)
        after = build_bound(iso, year, zones, args.after, cfg)
        # C-5: the model's per-zone weight vs the builder's own capacity sum.
        fleets = ws.load_zone_wind_fleet(year, zones, iso)
        builder_cap = np.array([sum(p[2] for p in fleets[z]) for z in zones])
        ratio = np.divide(
            after["cap"],
            builder_cap,
            out=np.full(len(zones), np.nan),
            where=builder_cap > 0,
        )
        finite = ratio[np.isfinite(ratio)]
        spread = (
            float(finite.max() / finite.min() - 1.0) if finite.size else float("nan")
        )

        d = after["mw"] - before["mw"]
        print(f"\n===== {iso} {year} =====")
        print(
            f"C-1 identity  before max rel {before['rel']:.3e} | after {after['rel']:.3e}"
            f"   (gate 1e-9)  ->  {'PASS' if max(before['rel'], after['rel']) <= 1e-9 else 'STOP'}"
        )
        print(
            f"C-2 overflow  before lost {before['lost']} h, max cf {before['max_cf']:.6f} | "
            f"after lost {after['lost']} h, max cf {after['max_cf']:.6f}  ->  "
            f"{'PASS' if (before['lost'] == 0 and after['lost'] == 0) else 'STOP'}"
        )
        print(
            f"C-5 model weight cap_z vs builder capacity C_z: ratio "
            f"{dict(zip(zones, np.round(ratio, 6)))}; spread max/min-1 = {spread:.3e}"
        )
        print(
            f"    system total M: {before['M'].sum() / 1e6:.4f} TWh (identical by "
            f"construction: max |dM| = {np.abs(after['M'] - before['M']).max():.3e} MW)"
        )
        print("    per-zone annual potential TWh, and the LP wind upper-bound delta:")
        print(
            f"      {'zone':<16}{'cap MW':>10}{'before':>10}{'after':>10}{'d TWh':>10}"
            f"{'d %':>8}{'mean|d| MW':>12}{'p1 MW':>9}{'p99 MW':>9}{'max|d| MW':>11}"
        )
        for i, z in enumerate(zones):
            b, a = before["mw"][i].sum() / 1e6, after["mw"][i].sum() / 1e6
            print(
                f"      {z:<16}{after['cap'][i]:>10,.0f}{b:>10.3f}{a:>10.3f}"
                f"{a - b:>+10.3f}{(100 * (a - b) / b if b else 0):>+8.2f}"
                f"{np.abs(d[i]).mean():>12.1f}{np.percentile(d[i], 1):>+9.0f}"
                f"{np.percentile(d[i], 99):>+9.0f}{np.abs(d[i]).max():>11.0f}"
            )
            rows.append(
                {
                    "iso": iso,
                    "year": year,
                    "zone": z,
                    "cap_mw": float(after["cap"][i]),
                    "before_twh": float(b),
                    "after_twh": float(a),
                    "delta_twh": float(a - b),
                    "delta_pct": float(100 * (a - b) / b) if b else 0.0,
                    "mean_abs_delta_mw": float(np.abs(d[i]).mean()),
                    "p1_delta_mw": float(np.percentile(d[i], 1)),
                    "p99_delta_mw": float(np.percentile(d[i], 99)),
                    "max_abs_delta_mw": float(np.abs(d[i]).max()),
                    "identity_rel_before": before["rel"],
                    "identity_rel_after": after["rel"],
                    "lost_overflow_before": before["lost"],
                    "lost_overflow_after": after["lost"],
                    "cap_over_builder_cap": float(ratio[i]),
                }
            )
        print(
            f"    max |delta| over all zone-hours: {np.abs(d).max():,.0f} MW  "
            f"(re-baseline threshold: > 1 MW in any hour)"
        )
        if year == 2025 and iso == "SPP":
            win = np.array(list(WINDOW))
            print(
                "    Dec-21-2025 window, per-zone wind potential MW (before -> after):"
            )
            for h in win:
                cells = "  ".join(
                    f"{z}: {before['mw'][i, h]:7.0f} -> {after['mw'][i, h]:7.0f}"
                    for i, z in enumerate(zones)
                )
                print(f"      h{h}  {cells}")

    if args.out:
        pd.DataFrame(rows).to_csv(args.out, index=False)
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    assert HOURS_PER_YEAR == 8760
    sys.exit(main())
