"""PJM-NEXT-5 card 3(a) zero-LP census — what ``unit_outage_full_rederive`` moves. ZERO LP.

For each year a ``fleet_only`` rebuild of the keeper recipe
(``pjmnext4_c1_span`` via ``replay_keeper.run_year_kwargs``) is built twice —
as recorded, and with ``unit_outage_full_rederive=True`` in a local override —
and every fleet row's available capacity-hours (``pmax x availability``) and
``min_gen`` energy are differenced. Offers (``mc_base``) are checked unchanged.

Run: ``python3 scripts/probes/pjm_next5_card3a_f2_census.py 2019 ... 2025``
Writes ``results/phase0/pjm/_pjm_next5_card3a_f2_census.json``.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
BUNDLE = REPO / "results/calibration/pjmnext4_c1_span"


def _rebuild(meta: dict, y: int, arm: bool) -> dict:
    """Fleet-only rebuild of year ``y``, optionally with the F2 companion armed."""
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(BUNDLE, y))
    kw["pjm_da_virtual_bids"] = False
    if arm:
        kw.setdefault("prb_overrides", {})
        kw["prb_overrides"] = dict(kw["prb_overrides"], unit_outage_full_rederive=True)
    return run_year(y, meta["iso"], 8760, meta.get("gas_price"), {}, fleet_only=True, **kw)


def main() -> None:
    """Difference the armed and recorded fleet per requested year."""
    logging.disable(logging.CRITICAL)
    meta = json.loads((BUNDLE / "meta.json").read_text())
    pov = (meta.get("coal_prb_sigmoid_overrides") or {})
    assert pov.get("unit_outage_membership_repair") and pov.get("unit_outage_unit_fuel_routing"), pov.keys()
    out: dict = {"what": __doc__.splitlines()[0], "years": {}}
    for y in [int(a) for a in sys.argv[1:]] or list(range(2019, 2026)):
        r0, r1 = _rebuild(meta, y, False), _rebuild(meta, y, True)
        assert r1["config"].unit_outage_full_rederive and not r0["config"].unit_outage_full_rederive
        f0, f1 = r0["fleet_arrays"], r1["fleet_arrays"]
        assert list(f0.unit_ids) == list(f1.unit_ids)
        pm = np.asarray(f0.pmax, float)
        a0, a1 = np.asarray(f0.availability, float), np.asarray(f1.availability, float)
        c0, c1 = pm * a0.sum(1) / 1e6, pm * a1.sum(1) / 1e6
        mg = lambda f: (np.asarray(f.min_gen, float).sum(1) / 1e6) if f.min_gen is not None else np.zeros(len(pm))
        d = pd.DataFrame({
            "unit": f0.unit_ids, "plant": np.asarray(f0.plant_code, int),
            "cls": np.asarray(f0.plant_group).astype(str), "dcap": c1 - c0, "dmg": mg(f1) - mg(f0),
        })
        mv = d[(d.dcap.abs() > 1e-6) | (d.dmg.abs() > 1e-6)]
        offers_equal = bool(np.array_equal(np.asarray(r0["mc_base"]), np.asarray(r1["mc_base"])))
        yr = {
            "rows_moved": int(len(mv)), "plants_moved": int(mv.plant.nunique()),
            "dcap_twh_by_class": mv.groupby("cls").dcap.sum().round(3).to_dict(),
            "dcap_twh_total": round(float(mv.dcap.sum()), 3),
            "dmin_gen_twh": round(float(d.dmg.sum()), 3),
            "offers_byte_identical": offers_equal,
            "top_plants": mv.groupby("plant").dcap.sum().sort_values().round(3).head(8).to_dict()
            | mv.groupby("plant").dcap.sum().sort_values().round(3).tail(8).to_dict(),
        }
        out["years"][str(y)] = yr
        print(y, json.dumps(yr), flush=True)
    dest = REPO / "results/phase0/pjm/_pjm_next5_card3a_f2_census.json"
    dest.write_text(json.dumps(out, indent=1))
    print("wrote", dest)


if __name__ == "__main__":
    main()
