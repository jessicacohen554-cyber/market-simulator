"""Zero-LP fleet census for the pjm-168 F1 screen (gates G1 and G3's denominator).

Rebuilds the pjm-167 touchpoint recipe's PJM fleet for one year twice — once as
committed (control) and once with ``eia860_vintage_tracks_solve_year`` armed
(arm) — through ``run_calibration.run_year(fleet_only=True)``, and reports
registry capacity by class.

This reproduces the FINDING-pjm167 §3.3 census *inside the solve path*, which is
exactly what gate G1 of
``docs/handoffs/PRECOMMIT-pjm167-fleet-vintage-screen-2026-09-06.md`` §4 asks
for. No LP is solved.

Usage:
    python scripts/probes/_pjm168_f1_fleet_census.py [--year 2021]
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

KEEPER = REPO / "results/calibration/pjm_tp2022_2021_k162"
HOURS = 8760

#: FINDING-pjm167 §3.3 groups the three coal plant_groups into one COAL row.
COAL_GROUPS = ("COAL", "COAL_BIT", "COAL_PRB", "COAL_WC")


def build_fleet(year: int, vintage_tracks: bool) -> dict:
    """Build the keeper's PJM fleet for *year*, optionally arming F1.

    Args:
        year: solve year to build the registry for.
        vintage_tracks: arm ``eia860_vintage_tracks_solve_year``.

    Returns:
        The ``run_year(fleet_only=True)`` state dict.
    """
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
    else:  # layered through the generic override channel
        prb = dict(call.get("prb_overrides") or {})
        prb["eia860_vintage_tracks_solve_year"] = vintage_tracks
        call["prb_overrides"] = prb
    return rc.run_year(**call)


def census(state: dict) -> dict[str, float]:
    """Registry pmax MW by plant_group, plus the grouped COAL total."""
    gens = state["fleet"]
    fa = state["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    by = defaultdict(float)
    for g, mw in zip(gens, pmax):
        by[g.plant_group] += float(mw)
    out = {k: round(v, 1) for k, v in sorted(by.items())}
    out["_COAL_TOTAL"] = round(sum(by[c] for c in COAL_GROUPS), 1)
    out["_TOTAL"] = round(sum(by.values()), 1)
    return out


def main() -> int:
    """Run the control/arm fleet census and print the delta table."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2021)
    args = ap.parse_args()

    print(f"--- CONTROL fleet (as committed), {args.year} ---")
    ctrl = census(build_fleet(args.year, False))
    print(f"--- ARM fleet (eia860_vintage_tracks_solve_year=True), {args.year} ---")
    arm = census(build_fleet(args.year, True))

    keys = sorted(set(ctrl) | set(arm))
    print(f"\n{'class':<16} {'control':>12} {'arm':>12} {'delta':>12}")
    for k in keys:
        c, a = ctrl.get(k, 0.0), arm.get(k, 0.0)
        print(f"{k:<16} {c:>12.1f} {a:>12.1f} {a - c:>+12.1f}")

    out = {"year": args.year, "control": ctrl, "arm": arm,
           "delta": {k: round(arm.get(k, 0.0) - ctrl.get(k, 0.0), 1) for k in keys}}
    dest = REPO / f"results/calibration/_pjm168_f1_census_{args.year}.json"
    dest.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
