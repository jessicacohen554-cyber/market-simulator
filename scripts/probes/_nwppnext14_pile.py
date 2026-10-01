"""NWPP-NEXT-14 phase 0 (ZERO LP): Jim Bridger's 2023 coal-yard pile rows and offers.

Fleet-only rebuild of keeper #18 (nwppnext13pu_span) for one year, then the
three coal-yard builders run past the fleet_only exit (build_coal_plant_budget,
build_coal_take_floor, build_coal_monthly_pile) to print Bridger's month-end
ceiling / floor and its tranche offers. Needs data/clean coal stocks/receipts
(curate_coal_stocks.py / curate_coal_receipts.py). Record: FINDING-nwppnext14 §1.
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
from market_sim.data.coal_fuel_inventory import (
    build_coal_plant_budget,
    build_coal_take_floor,
    build_coal_monthly_pile,
)

S = sys.argv[1]
y = int(sys.argv[2]) if len(sys.argv) > 2 else 2023
B = REPO / "results/calibration/nwppnext13pu_span"
meta = json.loads((B / "meta.json").read_text())
kw = run_year_kwargs(meta)
kw.update(derived_run_year_inputs(B, y))
kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
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
T = 8760
pc = np.asarray(fa.plant_code).astype(int)
cp = build_coal_plant_budget(fa, y, hours=T)
gi, bud, mi, coef, grp, prov = cp
floor, tf = build_coal_take_floor(fa, y, gi, grp, coef, bud, prov.yard_keys)
bud2, floor2, mi2, pile = build_coal_monthly_pile(
    fa, gi, grp, coef, bud, prov.stock_mmbtu, tf.parts, T
)
keys = list(prov.yard_keys)
print("yards", keys)
out = {}
uid = list(fa.unit_ids)
for k, yk in enumerate(keys):
    gens = gi[grp == k]
    plants = sorted(set(pc[gens]))
    if 8066 not in plants:
        continue
    print("yard", yk, "plants", plants, "units", [uid[g] for g in gens])
    print("coef MMBtu/MWh", coef[grp == k] if np.ndim(coef) == 1 else "hourly")
    print("ceiling TBtu", np.round(bud2[k] / 1e6, 2).tolist())
    print("floor   TBtu", np.round(floor2[k] / 1e6, 2).tolist())
    pm = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    for g in gens:
        print(
            uid[g],
            fa.plant_group[g],
            round(pm[g], 1),
            "avail mean",
            round(float(av[g].mean()) if av.ndim == 2 else float(av[g]), 3),
            "mc_base mean",
            round(float(np.mean(st["mc_base"][g])), 2) if "mc_base" in st else None,
            "min_gen TWh",
            round(float(np.asarray(fa.min_gen)[g].sum()) / 1e6, 3)
            if getattr(fa, "min_gen", None) is not None
            else None,
        )
    out = {
        "ceil": bud2[k].tolist(),
        "floor": floor2[k].tolist(),
        "coef": np.asarray(coef[grp == k]).tolist(),
    }
json.dump(out, open(f"{S}/pile_{y}.json", "w"))
print(list(st.keys()))
fp = st["fuel_prices"]
for g in gi[grp == keys.index(8066)]:
    f = np.asarray(fp[g]) if np.ndim(fp) > 1 else fp[g]
    print(
        uid[g],
        "fuel $/MMBtu mean",
        round(float(np.mean(f)), 3),
        "vom",
        getattr(fa, "vom", None)[g] if getattr(fa, "vom", None) is not None else None,
        "hr",
        fa.heat_rate[g],
        "mc_base month means",
        pd.Series(
            np.asarray(st["mc_base"][g]).ravel()[:8760]
            if np.ndim(st["mc_base"][g]) > 0 and np.size(st["mc_base"][g]) >= 8760
            else [float(np.mean(st["mc_base"][g]))] * 8760,
            index=pd.date_range("2023-01-01", periods=8760, freq="h"),
        )
        .resample("MS")
        .mean()
        .round(2)
        .tolist(),
    )
# other coal plants econ offers
for c in (6165, 8069, 6076, 4158, 7790, 4162, 6101, 8224, 3845):
    gg = [g for g in range(len(uid)) if pc[g] == c and "econlo" in uid[g]]
    for g in gg:
        print(c, uid[g], round(float(np.mean(st["mc_base"][g])), 2))
