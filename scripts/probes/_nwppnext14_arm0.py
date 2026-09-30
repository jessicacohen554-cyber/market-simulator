"""NWPP-NEXT-14 phase 0 (ZERO LP): LP-array delta of the arm on keeper #18's recipe.

Fleet-only rebuilds with and without ``eia923_cc_family_heat_rates`` +
``campd_unit_fuel_split``; prints every LP unit whose pmax, heat rate, mean
offer, available energy or min_gen moves. Usage: ``python3
scripts/probes/_nwppnext14_arm0.py 2023 2024``. Record: FINDING-nwppnext14 §3.
"""

import sys
import json
from pathlib import Path

REPO = Path(".").resolve()
for p in (str(REPO), str(REPO / "src")):
    sys.path.insert(0, p)
import numpy as np
import pandas as pd
from scripts import run_calibration_full as rcf
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
from scripts.run_calibration import run_year
from market_sim.pipeline.reference import henry_hub_actual
from market_sim.config.paths import set_eia860_vintage

B = REPO / "results/calibration/nwppnext13pu_span"
meta = json.loads((B / "meta.json").read_text())
V = {"B": {}, "A": {"eia923_cc_family_heat_rates": True, "campd_unit_fuel_split": True}}
out = {}
for y in [int(a) for a in sys.argv[1:]]:
    fr = {}
    for v, fl in V.items():
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(B, y))
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **fl}
        if y <= 2022:
            kw["prb_overrides"]["hydro_backfill_year"] = None
        st = run_year(
            y,
            "NWPP",
            8760,
            henry_hub_actual(rcf._load_reference(), y),
            {},
            fleet_only=True,
            **kw,
        )
        fa = st["fleet_arrays"]
        av = np.asarray(fa.availability, float)
        mg = getattr(fa, "min_gen", None)
        fr[v] = pd.DataFrame(
            {
                "u": list(fa.unit_ids),
                "pc": np.asarray(fa.plant_code).astype(int),
                "g": list(fa.plant_group),
                "pmax": np.asarray(fa.pmax, float),
                "hr": np.asarray(fa.heat_rate, float),
                "mc": [
                    float(np.mean(st["mc_base"][i])) for i in range(len(fa.unit_ids))
                ],
                "avail": np.asarray(fa.pmax, float) * av.sum(axis=1),
                "ming": np.asarray(mg, float).sum(axis=1) if mg is not None else 0.0,
            }
        )
        set_eia860_vintage(None)
    d = (
        fr["B"]
        .merge(fr["A"], on=["u", "pc", "g"], how="outer", suffixes=("", "_a"))
        .fillna(0)
    )
    mv = d[
        (abs(d.hr - d.hr_a) > 1e-9)
        | (abs(d.pmax - d.pmax_a) > 1e-6)
        | (abs(d.avail - d.avail_a) > 1)
        | (abs(d.ming - d.ming_a) > 1)
        | (abs(d.mc - d.mc_a) > 1e-6)
    ]
    print(y)
    print(
        mv[
            [
                "u",
                "pmax",
                "pmax_a",
                "hr",
                "hr_a",
                "mc",
                "mc_a",
                "avail",
                "avail_a",
                "ming",
                "ming_a",
            ]
        ]
        .round(3)
        .to_string(index=False)
    )
