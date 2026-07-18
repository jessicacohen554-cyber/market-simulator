"""Derive the CAISO LOLP scarcity-price overlay for a solved bundle.

Post-solve only, and the CAISO analogue of ``derive_ordc_overlay.py`` (ERCOT):
reads a persisted calibration bundle, reconstructs the hourly fleet availability
the LP solved against (same config, same outage overlay — no LP is re-solved),
computes the netted reserve headroom, and applies CAISO's published smooth-LOLP
adder (``market_sim.results.scarcity.caiso_scarcity_overlay``: σ=2,500 MW,
VOLL=$2,000, MCL=1,400 MW). The overlay is written as a separate
``scarcity.parquet`` next to the energy-only LMP — the SAME schema
(``year, hour, reserves_mw, scarcity_adder, lmp, lmp_scarcity``) that
``render_calibration_html._load_scarcity_overlay`` reads, so C3c scores the
settlement price (LMP + adder) for CAISO exactly as for the other ISOs (G-20a).

CAISO has no in-LP co-opt reserve product in the backcast path (rule 19); the
LOLP overlay is the sole published scarcity signal. It is inert on the current
keeper (the C3c miss is the evening-merit / RA-commitment gap G-15/G-20d, not a
reserve-scarcity gap) — this deriver exists so the settlement tail is *scored*,
not to manufacture one. It nets no AS plan and subtracts no reliability
deployment (``as_plan_mw=0.0``), byte-identical to ``caiso_scarcity_overlay``.

The heavy reconstruction (fleet rebuild, online/offline reserve split, renewable
+ storage headroom, system lambda, gate metrics) is reused verbatim from
``derive_ordc_overlay`` — this module only swaps the adder formula.

Usage:
    python scripts/data/derive_caiso_scarcity_overlay.py results/calibration/caiso58_v2_regate
        [--years 2023 2024 2025] [--tag ...] [--rebuild-availability] [--diagnostic]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
from market_sim.results.scarcity import (  # noqa: E402
    CAISO_SCARCITY_MCL_MW,
    CAISO_SCARCITY_SHIFT_SIGMA,
    CAISO_SCARCITY_SIGMA_MW,
    CAISO_SCARCITY_VOLL,
    ordc_adder,
)

# Reuse the ERCOT deriver's reconstruction verbatim (same persisted-bundle
# contract, same online/offline reserve split, same headroom/lambda helpers).
from derive_ordc_overlay import (  # noqa: E402
    _demand_weights,
    _mae,
    _monthly_mae,
    _storage_headroom,
    _system_lambda,
    build_availability,
)

CAL_DIR = REPO / "data" / "raw" / "_validation-source"


def _actual_rt_caiso(year: int, hours: int) -> np.ndarray:
    """Actual hourly RT price for CAISO (rt, da-filled), NaN-padded to ``hours``.

    Mirrors ``derive_ordc_overlay._actual_rt`` but for the CAISO validation
    series (whose ``rt`` column is partly unpopulated — fall back to ``da``).
    Report-only; the scored actual comes from the committed DA-expressible tail.
    """
    p = CAL_DIR / "actual_lmp_hourly_CAISO.parquet"
    if not p.exists():
        return np.full(hours, np.nan)
    act = pd.read_parquet(p)
    act = act[act["year"] == year]
    out = np.full(hours, np.nan)
    if act.empty:
        return out
    rt = act["rt"].to_numpy(float)
    if "da" in act.columns:
        rt = np.where(np.isnan(rt), act["da"].to_numpy(float), rt)
    out[act["hour"].to_numpy()] = rt
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--tag", default=None, help="write scarcity_<tag>.parquet (scenario runs)"
    )
    ap.add_argument("--rebuild-availability", action="store_true")
    ap.add_argument(
        "--diagnostic",
        action="store_true",
        help="print the adder incidence / gate metrics only, write nothing",
    )
    args = ap.parse_args()

    bundle = args.bundle.resolve()
    meta = json.loads((bundle / "meta.json").read_text())
    if meta["iso"] != "CAISO":
        raise SystemExit("CAISO scarcity overlay is CAISO-only")
    years = args.years or meta["years"]
    hours = meta["hours"]

    print(f"bundle {bundle.name}: years {years}")
    avail = build_availability(bundle, years, meta, force=args.rebuild_availability)

    frames = []
    for year in years:
        a = avail[avail["year"] == year]
        cap_t = a["storage_power_cap_mw"].to_numpy(float)
        ren_headroom = a["renewable_avail_mw"].to_numpy(float) - a[
            "renewable_dispatch_mw"
        ].to_numpy(float)
        # Online/offline reserve split — identical construction to the ERCOT
        # deriver and to caiso_scarcity_overlay -> reserve_headroom(as_plan=0):
        # online tier = spinning thermal headroom + curtailed-renewable +
        # storage; offline tier = quick-start non-spin headroom. CAISO nets NO
        # AS plan and subtracts NO reliability deployment (as_plan_mw=0.0).
        r_offline = a["thermal_offline_mw"].to_numpy(float)
        r_online = (
            a["thermal_online_mw"].to_numpy(float)
            + ren_headroom
            + _storage_headroom(bundle, year, hours, cap_t)
        )
        lam = _system_lambda(bundle, year, hours)
        # The exact body of caiso_scarcity_overlay: smooth LOLP, no multi-step
        # floor, capped at VOLL - lambda (inside ordc_adder). mu=0.
        adder = ordc_adder(
            r_online + r_offline,
            np.nan_to_num(lam),
            voll=CAISO_SCARCITY_VOLL,
            mcl_mw=CAISO_SCARCITY_MCL_MW,
            mu_mw=0.0,
            sigma_mw=CAISO_SCARCITY_SIGMA_MW,
            shift_sigma=CAISO_SCARCITY_SHIFT_SIGMA,
            multistep_floor=False,
            reserves_online_mw=r_online,
        )
        frames.append(
            pd.DataFrame(
                {
                    "year": np.int16(year),
                    "hour": np.arange(hours, dtype=np.int32),
                    "reserves_mw": (r_online + r_offline).astype(np.float32),
                    "reserves_online_mw": r_online.astype(np.float32),
                    "scarcity_adder": adder.astype(np.float32),
                    "lmp": lam.astype(np.float32),
                    "lmp_scarcity": (lam + adder).astype(np.float32),
                }
            )
        )

        # Report: incidence + gate metrics vs the actual RT series ($200 tail).
        rt = _actual_rt_caiso(year, hours)
        w = _demand_weights(bundle, year, hours)
        mae0 = _monthly_mae(lam, rt, w)
        mae1 = _monthly_mae(lam + adder, rt, w)
        print(
            f"\n{year}: adder>$1 in {(adder > 1).sum()} h, >$10 in "
            f"{(adder > 10).sum()} h, >$100 in {(adder > 100).sum()} h, "
            f"max ${adder.max():,.0f}; mean ${adder.mean():.2f}"
        )
        print(
            f"  monthly LMP MAE (gate metric) {mae0:.1f} -> {mae1:.1f} "
            f"$/MWh; hourly dw-MAE {_mae(lam, rt, w):.1f} -> "
            f"{_mae(lam + adder, rt, w):.1f}"
        )
        print(
            f"  hours >$200: actual {int(np.nansum(rt > 200))}, model "
            f"{int(np.nansum(lam > 200))} -> {int(np.nansum((lam + adder) > 200))}; "
            f">$500: actual {int(np.nansum(rt > 500))}, model "
            f"{int(np.nansum(lam > 500))} -> "
            f"{int(np.nansum((lam + adder) > 500))}"
        )

    if args.diagnostic:
        return

    out = pd.concat(frames, ignore_index=True)
    name = f"scarcity_{args.tag}.parquet" if args.tag else "scarcity.parquet"
    out.to_parquet(bundle / name, index=False)
    print(f"\nwrote {bundle / name}")


if __name__ == "__main__":
    main()
