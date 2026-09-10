"""Zero-LP phase-0 census for lane SPP-61 (the Harrington 6193 fuel-vintage repair).

Measures, with no LP solved, both sides of the two-sided defect
``docs/handoffs/CHARTER-spp-61-2026-09-10.md`` §2 names:

* **model side** — the SPP fleet registry built by the keeper's recipe, as
  committed (control) and with ``eia860_vintage_tracks_solve_year`` armed
  (arm): per-class ``pmax`` MW and plant 6193's own class assignment.
* **bench side** — ``run_calibration_full._fleet_group_by_code``, the map the
  EIA-923/CAMPD benchmark backfill buckets a plant by, under each vintage.

Usage:
    python scripts/probes/_spp61_phase0_census.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402

from scripts import replay_keeper as rk  # noqa: E402
from scripts import run_calibration as rc  # noqa: E402

KEEPER = REPO / "results/calibration/spp52a_fossil93"
HOURS = 8760
HARRINGTON = 6193


def build_fleet(year: int, vintage_tracks: bool) -> dict:
    """Build the keeper's SPP fleet for *year*, optionally arming the vintage gate."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    sig = set(rc.run_year.__code__.co_varnames[: rc.run_year.__code__.co_argcount])
    call = {k: v for k, v in kwargs.items() if k in sig}
    call["year"] = year
    call["iso"] = meta["iso"]
    call["hours"] = HOURS
    call["fleet_only"] = True
    call["gas_price"] = float(meta["gas_prices"][str(year)])
    call["ttc_overrides"] = {}
    call.pop("years", None)
    if "eia860_vintage_tracks_solve_year" in sig:
        call["eia860_vintage_tracks_solve_year"] = vintage_tracks
    else:
        prb = dict(call.get("prb_overrides") or {})
        prb["eia860_vintage_tracks_solve_year"] = vintage_tracks
        call["prb_overrides"] = prb
    return rc.run_year(**call)


def census(state: dict) -> tuple[dict[str, float], dict[str, float]]:
    """Return (registry pmax MW by plant_group, Harrington's own MW by group)."""
    gens = state["fleet"]
    pmax = np.asarray(state["fleet_arrays"].pmax, dtype=float)
    by: dict[str, float] = defaultdict(float)
    harr: dict[str, float] = defaultdict(float)
    for g, mw in zip(gens, pmax):
        by[g.plant_group] += float(mw)
        if int(getattr(g, "plant_code", 0) or 0) == HARRINGTON:
            harr[g.plant_group] += float(mw)
    by["_TOTAL"] = sum(v for k, v in by.items() if k != "_TOTAL")
    return {k: round(v, 1) for k, v in sorted(by.items())}, {
        k: round(v, 1) for k, v in sorted(harr.items())
    }


def bench_group(year: int, vintage: int | None) -> str:
    """Return ``_fleet_group_by_code``'s class for Harrington under *vintage*."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.paths import set_eia860_vintage

    from scripts.run_calibration_full import _fleet_group_by_code

    set_eia860_vintage(vintage)
    try:
        gbc = _fleet_group_by_code("SPP", get_iso_config("SPP"), year)
    finally:
        set_eia860_vintage(None)
    return gbc.get(HARRINGTON, "<absent>")


def main() -> int:
    """Print the control/arm fleet + bench-map census for each year."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    args = ap.parse_args()

    out: dict = {"harrington": HARRINGTON, "years": {}}
    for year in args.years:
        ctrl, ctrl_h = census(build_fleet(year, False))
        arm, arm_h = census(build_fleet(year, True))
        keys = sorted(set(ctrl) | set(arm))
        print(f"\n===== {year} =====")
        print(f"{'class':<16} {'control':>12} {'arm':>12} {'delta':>12}")
        for k in keys:
            c, a = ctrl.get(k, 0.0), arm.get(k, 0.0)
            if abs(a - c) > 0.05 or k == "_TOTAL":
                print(f"{k:<16} {c:>12.1f} {a:>12.1f} {a - c:>+12.1f}")
        print(f"  Harrington control: {dict(ctrl_h)}")
        print(f"  Harrington arm    : {dict(arm_h)}")
        bg_ctrl = bench_group(year, None)
        bg_arm = bench_group(year, year)
        print(f"  bench group_by_code[6193]  control={bg_ctrl}  arm={bg_arm}")
        out["years"][year] = {
            "control": ctrl,
            "arm": arm,
            "delta": {k: round(arm.get(k, 0.0) - ctrl.get(k, 0.0), 1) for k in keys},
            "harrington_control": ctrl_h,
            "harrington_arm": arm_h,
            "bench_group_control": bg_ctrl,
            "bench_group_arm": bg_arm,
        }
    dest = REPO / "results/calibration/_spp61_phase0_census.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
