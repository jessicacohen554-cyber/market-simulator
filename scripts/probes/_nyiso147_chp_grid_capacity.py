#!/usr/bin/env python3
"""nyiso-147 phase 0c — the LP grid capacity actually carried per NYISO CHP plant.

Rebuilds the control keeper's 2023 fleet (fleet_only, no LP — the
`_nyiso147_upstate_offer_anatomy` machinery) and dumps, for every CHP-class
plant: the sum of tranche pmax (the LP's grid capacity), mean availability,
and mean offer per tranche — against the plant's nameplate and the measured
Gold-Book / EIA-923 net-energy identity computed by the phase-0 notebook.

Usage:
    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso147_chp_grid_capacity.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso146_control"
OUT = REPO / "results" / "calibration" / "_nyiso147_chp_grid_capacity.json"


def main() -> None:
    spec = importlib.util.spec_from_file_location(
        "_anatomy", REPO / "scripts" / "probes" / "_nyiso147_upstate_offer_anatomy.py"
    )
    an = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(an)

    state = an._keeper_fleet(BUNDLE, 2023)
    fa = state["fleet_arrays"]
    mc = np.asarray(state["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], 8760, axis=1)
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)
    groups = np.asarray(fa.plant_group, dtype=object)
    codes = np.asarray(fa.plant_code, dtype=int)
    unit_ids = np.asarray(fa.unit_ids, dtype=object)

    out: dict = {}
    chp_rows = np.array([("CHP" in str(g)) for g in groups])
    for code in sorted(set(codes[chp_rows])):
        sel = chp_rows & (codes == code)
        rows = []
        for r in np.nonzero(sel)[0]:
            rows.append(
                {
                    "unit_id": str(unit_ids[r]),
                    "pmax": round(float(pmax[r]), 1),
                    "avail_mean": round(float(avail[r].mean()), 3),
                    "offer_mean": round(float(mc[r].mean()), 2),
                }
            )
        out[str(code)] = {
            "grid_pmax_sum": round(float(pmax[sel].sum()), 1),
            "rows": rows,
        }
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    for code, d in out.items():
        print(f"{code:>7}: grid pmax {d['grid_pmax_sum']:>7.1f} MW, {len(d['rows'])} rows")


if __name__ == "__main__":
    main()
