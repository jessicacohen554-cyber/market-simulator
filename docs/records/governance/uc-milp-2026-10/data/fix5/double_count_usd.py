"""UC-1-FIX-5 phase 0 (zero LP): the no-load double count in $, per class, from a uc-1.x bundle.

double count = sum_t nl[c,t] * P1[c,t] / pbar_c  (the no-load heat the average-rate
energy already carries, priced at the cluster's no-load $/MMBtu), next to the
explicit no-load sum_t nl[c,t] * u[c,t] and the UC energy cost (uc_uplift).
Usage: python double_count_usd.py <bundle_dir> <year>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from market_sim.model.uc.params import FAMILY_BY_GROUP

B, Y = Path(sys.argv[1]), int(sys.argv[2])
log = json.load(open(B / f"uc_solve_log_{Y}.json"))
cl = pd.json_normalize(log["clusters"])
cl = cl[cl.integer].set_index("cluster")
sch = pd.read_parquet(B / "hourly" / f"uc_schedule_{Y}.parquet")
sch = sch[sch.cluster.isin(cl.index)]
um = pd.read_parquet(B / "hourly" / f"unit_marginal_{Y}.parquet",
                     columns=["pass", "plant_code", "plant_group", "hour", "mw"])
um = um[um["pass"] == "P1"]
um["uc_class"] = um.plant_group.astype(str).map(FAMILY_BY_GROUP)
P = um.groupby(["plant_code", "uc_class", "hour"]).mw.sum().rename("P").reset_index()
s = sch.merge(P, on=["plant_code", "uc_class", "hour"], how="left").fillna({"P": 0.0})
s["pbar"] = cl.loc[s.cluster, "pbar_mw"].to_numpy()
s["explicit"] = s.noload_usd_per_unit_h * s.u
s["double"] = s.noload_usd_per_unit_h * s.P / s.pbar
up = pd.read_parquet(B / "hourly" / f"uc_uplift_{Y}.parquet")
e = up.groupby("uc_class")[["energy_mwh", "energy_cost_usd"]].sum()
g = s.groupby("uc_class")[["explicit", "double", "P"]].sum().join(e)
g["double_share_of_energy_cost"] = g.double / g.energy_cost_usd
g["double_usd_per_mwh"] = g.double / g.energy_mwh
g["double_share_of_explicit"] = g.double / g.explicit
out = {"engine": log["engine"]["version"], "iso": log["engine"]["iso"], "year": Y,
       "by_class": (g / [1e6, 1e6, 1e6, 1e6, 1e6, 1, 1, 1]).round(4).to_dict(orient="index")}
print(json.dumps(out, indent=1))
