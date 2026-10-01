"""NWPP-NEXT-15 census (ZERO LP): parent vs LIVE dispatched-bin denominator.

Fleet-only rebuilds (``run_year(fleet_only=True)``) of the NWPP keeper bundle on
its own recipe, one per year. For each year it builds the dispatched-bin roster
the two constructions divide by —

* ``parent`` — ``lp_bin_capacity_index`` as miso-266's
  ``unit_outage_dispatched_bin_denominator`` builds it (every dispatched row);
* ``live``   — the same roster with ``live_year=<year>``
  (``unit_outage_dispatched_bin_live_denominator``, NWPP-NEXT-15), which drops
  the dated exit-cohort rows retired before the solve year —

and prints them for Centralia 3845 and Colstrip 6076 (FINDING-nwppnext13 §1.3),
plus every other (plant, group) bin whose denominator the sub-gate moves. The
roster depends only on the dispatched fleet, so the keeper recipe is rebuilt
unchanged (no flag flipped); nothing is solved.

Usage::

    python scripts/probes/_nwppnext15_live_denominator_census.py --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/nwppnext13pu_span"
FOCUS = (3845, 6076)


def _rows(fleet_arrays) -> list[SimpleNamespace]:
    """The attributes ``lp_bin_capacity_index`` reads, off ``FleetArrays``."""
    return [
        SimpleNamespace(plant_code=int(c), plant_group=str(g), unit_id=str(u))
        for c, g, u in zip(
            fleet_arrays.plant_code, fleet_arrays.plant_group, fleet_arrays.unit_ids
        )
    ]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--bundle", default=str(BUNDLE))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.outages import exit_cohort_tag, lp_bin_capacity_index
    from market_sim.pipeline.reference import henry_hub_actual

    bundle = Path(args.bundle)
    meta = json.loads((bundle / "meta.json").read_text())
    res: dict[str, dict] = {}
    for y in args.years:
        gas = henry_hub_actual(rcf._load_reference(), y)
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(bundle, y))
        if y <= 2022:
            kw["prb_overrides"] = {
                **(kw.get("prb_overrides") or {}),
                "hydro_backfill_year": None,
            }
        st = run_year(y, "NWPP", 8760, gas, {}, fleet_only=True, **kw)
        set_eia860_vintage(None)
        fa = st["fleet_arrays"]
        rows = _rows(fa)
        pmax = np.asarray(fa.pmax, dtype=float)
        parent = dict(lp_bin_capacity_index(rows, pmax))
        live = dict(lp_bin_capacity_index(rows, pmax, live_year=y))
        dead = sorted(
            {
                r.unit_id
                for r in rows
                if (t := exit_cohort_tag(r)) is not None and t[0] < y
            }
        )
        moved = {
            f"{k[0]}:{k[1]}": [round(v, 1), round(live.get(k, 0.0), 1)]
            for k, v in sorted(parent.items())
            if abs(v - live.get(k, 0.0)) > 1e-6
        }
        focus = {
            f"{k[0]}:{k[1]}": [round(v, 1), round(live.get(k, 0.0), 1)]
            for k, v in sorted(parent.items())
            if k[0] in FOCUS
        }
        res[str(y)] = {"focus": focus, "moved": moved, "dead_rows": dead}
        print(f"{y}: focus parent->live {focus}  |  bins moved: {len(moved)}")
        for k, (a, b) in moved.items():
            if int(k.split(":")[0]) not in FOCUS:
                print(f"    other moved {k}: {a} -> {b}")
    Path(args.out).write_text(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
