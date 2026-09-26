"""neiso-119 zero-LP LP-input diff: keeper recipe vs the armed recipe, per year.

fleet_only rebuild twice on ``neiso118_span``'s recipe — (control) unchanged,
(arm) with ``gas_offer_margin_anchor_vintage`` and
``neiso_winter_fuelsec_conduct_roster`` routed through ``prb_overrides`` exactly as
``replay_keeper.py --set`` routes them — and reports what moves: the resolved
anchor, the winter-fuelsec floor energy by plant, and the mean mc_base shift by
class. Writes ``lp_input_diff_<Y>.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
BUNDLE = REPO / "results/calibration/neiso118_span"
ARM = {
    "gas_offer_margin_anchor_vintage": True,
    "neiso_winter_fuelsec_conduct_roster": True,
}


def _build(y: int, arm: bool) -> dict:
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.floor_mechanisms import MECH_WINTER_FUELSEC
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = rk.run_year_kwargs(meta)
    kw.update(rk.derived_run_year_inputs(BUNDLE, y))
    if arm:
        kw.setdefault("prb_overrides", {}).update(ARM)
        kw["gas_offer_margin_anchor_vintage"] = True
    st = run_year(
        y,
        "NEISO",
        8760,
        henry_hub_actual(rcf._load_reference(), y),
        {},
        fleet_only=True,
        **kw,
    )
    set_eia860_vintage(None)
    fa = st["fleet_arrays"]
    mech = np.asarray(fa.min_gen_mechanism)
    mg = np.asarray(fa.min_gen, float)
    fs = mech == MECH_WINTER_FUELSEC
    plant = np.asarray(fa.plant_code).astype(int)
    floor = {
        int(p): round(float((mg[plant == p] * fs[plant == p]).sum()) / 1e6, 4)
        for p in sorted(set(plant[fs.any(1)]))
    }
    return {
        "cfg": st["config"],
        "mc": np.asarray(st["mc_base"], float),
        "grp": np.asarray(fa.plant_group).astype(str),
        "uid": list(fa.unit_ids),
        "floor": floor,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    y = ap.parse_args().year
    os.chdir(REPO)
    c, a = _build(y, False), _build(y, True)
    assert c["uid"] == a["uid"], "unit ids moved"
    d = a["mc"] - c["mc"]
    by = {}
    for g in sorted(set(c["grp"])):
        m = c["grp"] == g
        if m.any():
            by[g or "(oil)"] = round(float(d[m].mean()), 3)
    out = {
        "year": y,
        "anchor": {
            "control": c["cfg"].gas_offer_margin_anchor,
            "arm": a["cfg"].gas_offer_margin_anchor,
        },
        "fuelsec_floor_twh": {"control": c["floor"], "arm": a["floor"]},
        "mean_mc_shift_by_class": by,
        "units_with_mc_change": int((np.abs(d) > 1e-9).any(1).sum()),
    }
    Path(__file__).with_name(f"lp_input_diff_{y}.json").write_text(
        json.dumps(out, indent=1)
    )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
