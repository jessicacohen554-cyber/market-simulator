"""caiso-287 (ZERO LP): is the gap-fusing a SIDE EFFECT, or entailed by the screen?

PRECOMMIT section 6.2 pre-registered this limb before any shard was launched,
because an (A) GAP-MERGING DOMINANT verdict does NOT license disarming
``startup_aware``. The screen has two effects that nothing currently separates:

* **INTENDED** -- a dropped (phantom) run must not ANCHOR a bridge leg.
* **THE FUSING** -- because ``runs`` is rebound to ``kept_runs``
  (``model/commitment.py:1114``), a dropped run also stops DELIMITING gaps, so
  two idle stretches either side of it become ONE longer gap. ``hold_cost``
  is linear in ``gap``, and past ``DA_COMMITMENT_HORIZON_HOURS`` the gap is
  excluded outright (line 1221).

This script classifies every kept-gap so the two can be told apart rather than
argued about:

* ``fused``     -- the gap spans at least one DROPPED run, i.e. it exists in
                   this form only because the screen removed that run.
* ``unfused``   -- the gap is bounded by kept runs with nothing dropped inside;
                   the screen did not change its length at all.
* ``over_da``   -- the gap exceeds the DA horizon and is therefore excluded
                   outright rather than merely repriced.

**The interpretive point this measurement exists to settle**, stated before the
numbers are read: the fusing may not be a defect at all. The screen's premise is
that a dropped run is one a real unit-commitment would never have started. If
the unit was never started, it was idle across that whole span, so the FUSED gap
is the true idle period and pricing the hold over all of it is correct -- the
fusing would then be ENTAILED by the premise, not a side effect of the
rebinding. What the census can show is how much of the removal rides on that
entailment, and how much rides on the harder-to-defend 24-hour exclusion.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent.parent
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "_split", REPO / "scripts/probes/caiso287_screen_split.py"
)
SPLIT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(SPLIT)

from market_sim.config.constants import (  # noqa: E402
    DA_COMMITMENT_HORIZON_HOURS,
    RA_BRIDGE_ECON_MIN_DOWN_HOURS,
)
from market_sim.model.commitment import (  # noqa: E402
    _ra_bridge_unit_params,
    find_runs,
)

T = SPLIT.T
FUEL_TYPES = ("gas_cc", "gas_ct")


def main(year: int, out: Path) -> None:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    bundle = REPO / f"results/calibration/caiso287_instr_{year}"
    belly, belly_sha = SPLIT.derive_belly(year)
    belly_set = np.zeros(T, dtype=bool)
    belly_set[belly] = True

    state, _ = reconstruct_bundle_fleet(bundle, year)
    gens = state["fleet"]
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    zone_idx = np.asarray(fa.zone_idx)
    heat_rate = np.asarray(fa.heat_rate, dtype=float)

    disp, _ = SPLIT.read_p0_dispatch(bundle, year)
    zone_names = SPLIT.zone_names_from_fleet(gens, zone_idx)
    prices = SPLIT.read_p0_prices(bundle, zone_names, year)

    plant_pmax: dict[str, float] = {}
    for g, gen in enumerate(gens):
        if getattr(gen, "is_campd_bin", False):
            key = gen.unit_id.rpartition("_")[0]
            plant_pmax[key] = plant_pmax.get(key, 0.0) + pmax[g]

    tally = {
        k: {"gaps": 0, "belly_mw": 0.0}
        for k in ("unfused", "fused_within_da", "fused_over_da", "unfused_over_da")
    }
    runs_detected = runs_dropped = 0

    for g, gen in enumerate(gens):
        if gen.plant_group.endswith("_CHP") or gen.fuel_type not in FUEL_TYPES:
            continue
        resolved = _ra_bridge_unit_params(gen, float(heat_rate[g]))
        if resolved is None:
            continue
        min_down, startup_per_mw = resolved
        if not (startup_per_mw > 0.0 and min_down >= RA_BRIDGE_ECON_MIN_DOWN_HOURS):
            continue

        runs = find_runs(disp[g, :] > pmax[g] * 0.05)
        if not runs:
            continue
        z = int(zone_idx[g])
        pm = max(float(pmax[g]), 1.0)
        kept, dropped = [], []
        for s, e in runs:
            margin = float(
                np.sum((prices[z, s:e] - mc[g, s:e]) * disp[g, s:e])
            ) / pm
            (kept if margin >= startup_per_mw else dropped).append((s, e))
        runs_detected += len(runs)
        runs_dropped += len(dropped)
        if len(kept) < 2:
            continue

        is_bin = getattr(gen, "is_campd_bin", False)
        floor_pmax = (
            plant_pmax.get(gen.unit_id.rpartition("_")[0], pmax[g]) if is_bin else pmax[g]
        )
        target_mw = min(SPLIT.MIN_LOAD_FRAC * floor_pmax, float(pmax[g]))

        for (_, end_prev), (start_next, _) in zip(kept[:-1], kept[1:]):
            gap = start_next - end_prev
            if gap <= 0 or gap < min_down:
                continue
            inside = [d for d in dropped if d[0] >= end_prev and d[1] <= start_next]
            over_da = gap > DA_COMMITMENT_HORIZON_HOURS
            if inside and over_da:
                key = "fused_over_da"
            elif inside:
                key = "fused_within_da"
            elif over_da:
                key = "unfused_over_da"
            else:
                key = "unfused"
            sl = slice(end_prev, start_next)
            in_belly = belly_set[sl]
            mw = float(np.sum(target_mw * avail[g, sl][in_belly]))
            tally[key]["gaps"] += 1
            tally[key]["belly_mw"] += mw

    for v in tally.values():
        v["mean_belly_mw"] = v["belly_mw"] / belly.size

    fused = tally["fused_within_da"]["mean_belly_mw"] + tally["fused_over_da"]["mean_belly_mw"]
    unfused = tally["unfused"]["mean_belly_mw"] + tally["unfused_over_da"]["mean_belly_mw"]
    over_da = tally["fused_over_da"]["mean_belly_mw"] + tally["unfused_over_da"]["mean_belly_mw"]
    total = fused + unfused

    rec = {
        "year": year,
        "belly_sha256_16": belly_sha,
        "runs_detected": runs_detected,
        "runs_dropped_by_screen": runs_dropped,
        "share_runs_dropped": runs_dropped / runs_detected if runs_detected else None,
        "kept_gap_classes": tally,
        "summary_mean_belly_mw": {
            "fused_gaps": fused,
            "unfused_gaps": unfused,
            "total_kept_gap_mw": total,
            "share_on_fused_gaps": fused / total if total else None,
            "over_da_horizon_excluded": over_da,
            "share_on_over_da": over_da / total if total else None,
        },
    }
    out.write_text(json.dumps(rec, indent=2, default=float))
    print(json.dumps(rec["summary_mean_belly_mw"], indent=2, default=float))
    print(
        f"runs dropped by the screen: {runs_dropped}/{runs_detected} "
        f"({rec['share_runs_dropped']:.2%})" if runs_detected else "no runs"
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    main(a.year, a.out or REPO / f"results/calibration/_caiso287_merge_census_{a.year}.json")
