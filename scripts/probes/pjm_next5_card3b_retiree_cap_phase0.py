"""PJM-NEXT-5 card 3(b) phase 0 — what ``retiree_cems_cap`` touches on the keeper. ZERO LP.

For each year: (1) the plants ``retiree_availability_caps('PJM', y)`` returns
(the within-window retiree set with a CEMS envelope below 1.0), their retiree
nameplate and the capacity-hours the envelope would remove; (2) a ``fleet_only``
rebuild of the keeper recipe (``replay_keeper.run_year_kwargs``) — which rows of
the SOLVED fleet carry one of those plant codes, and the availability-weighted
capacity-hours on them. A cap that reaches zero fleet rows is inert in the
solve whatever it would remove on paper.

Run: ``python3 scripts/probes/pjm_next5_card3b_retiree_cap_phase0.py 2019 ... 2025``
Writes ``results/calibration/_pjm_next5_card3b_retiree_cap_phase0.json``.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/pjmnext4_c1_span"


def main() -> None:
    """Census the retiree cap per year against the keeper's solved fleet."""
    logging.disable(logging.CRITICAL)
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_retired_within_window
    from market_sim.data.outages import retiree_availability_caps
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    assert meta.get("retiree_cems_cap") is True
    retirees = load_retired_within_window("PJM", get_iso_config("PJM"))
    name_of = {int(g.plant_code): (g.plant_group, g.state) for g in retirees}
    np_of: dict[int, float] = {}
    for g in retirees:
        np_of[int(g.plant_code)] = np_of.get(int(g.plant_code), 0.0) + float(g.pmax_mw)
    out: dict = {"what": __doc__.splitlines()[0], "n_retiree_units": len(retirees), "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or list(range(2019, 2026)):
        # lru_cache ORDER MATTERS: clear, let the rebuild populate the cache with
        # the IN-RUN value (vintage-resolved membership), read it back, then
        # clear and read the out-of-run (canonical-membership) "paper" value.
        retiree_availability_caps.cache_clear()
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["pjm_da_virtual_bids"] = False
        r = run_year(y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)
        called_in_run = retiree_availability_caps.cache_info().currsize > 0
        in_run = retiree_availability_caps("PJM", y, 8760)
        retiree_availability_caps.cache_clear()
        caps = retiree_availability_caps("PJM", y, 8760)
        retiree_availability_caps.cache_clear()
        paper = {
            str(pc): {
                "class": name_of.get(pc, ("?", "?"))[0],
                "state": name_of.get(pc, ("?", "?"))[1],
                "retiree_mw": round(np_of.get(pc, 0.0), 1),
                "removed_twh_paper": round(np_of.get(pc, 0.0) * float((1.0 - c).sum()) / 1e6, 3),
            }
            for pc, c in caps.items()
        }
        fa = r["fleet_arrays"]
        pc = np.asarray(fa.plant_code, int)
        hit = np.isin(pc, list(caps))
        avail = np.asarray(fa.availability, float)
        if avail.ndim == 1:
            avail = avail[:, None] * np.ones((1, 8760))
        out["years"][str(y)] = {
            "called_in_run": called_in_run,
            "in_run_cap_plants": len(in_run),
            "in_run_fleet_rows_hit": int(np.isin(np.asarray(fa.plant_code, int), list(in_run)).sum()),
            "cap_plants": len(caps),
            "cap_plants_retiree_mw": round(sum(np_of.get(p, 0.0) for p in caps), 1),
            "removed_twh_paper": round(sum(v["removed_twh_paper"] for v in paper.values()), 3),
            "solved_fleet_rows_hit": int(hit.sum()),
            "solved_fleet_mw_hit": round(float(np.asarray(fa.pmax, float)[hit].sum()), 1),
            "solved_fleet_cap_twh_on_hit_rows": round(
                float((np.asarray(fa.pmax, float)[hit, None] * avail[hit]).sum() / 1e6), 3
            ),
            "plants": paper,
        }
        print(y, {k: v for k, v in out["years"][str(y)].items() if k != "plants"}, flush=True)
    dest = REPO / "results/calibration/_pjm_next5_card3b_retiree_cap_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
