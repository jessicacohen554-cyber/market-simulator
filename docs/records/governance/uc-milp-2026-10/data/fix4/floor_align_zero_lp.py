"""Zero-LP: how much stricter is the P1 UC floor min(mlf*pbar*u, pbar*a*u) than window row (b) mlf*pbar*a*u?"""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

b, y = Path(sys.argv[1]), int(sys.argv[2])
log = json.loads((b / f"uc_solve_log_{y}.json").read_text())
cl = pd.DataFrame(log["clusters"])[
    ["cluster", "plant_code", "uc_class", "mlf", "pbar_mw"]
]
s = pd.read_parquet(b / "hourly" / f"uc_schedule_{y}.parquet")
s = s.merge(cl[["cluster", "mlf", "pbar_mw"]], on="cluster")
on = s[s["u"] > 0].copy()
on["a"] = on["online_mw"] / (on["u"] * on["pbar_mw"])
cur = np.minimum(
    on["mlf"] * on["pbar_mw"] * on["u"], on["online_mw"]
)  # injected (capped)
new = on["mlf"] * on["pbar_mw"] * on["a"] * on["u"]  # window row (b)
on["cur"], on["new"] = cur, new
on["delta"] = cur - new
fam = {
    "CC_REGULAR": "cc",
    "CC_CHP": "cc",
    "ST_GAS": "st_gas",
    "COAL_PRB": "coal",
    "COAL_LIGNITE": "coal",
    "COAL_BIT": "coal",
    "COAL_WC": "coal",
    "CT_PEAKER": "ct",
}
um = pq.read_table(
    b / "hourly" / f"unit_marginal_{y}.parquet",
    columns=["pass", "unit_id", "plant_code", "plant_group", "hour", "mw"],
).to_pandas()
um = um[um["pass"] == "P1"]
pc = um["plant_code"].astype(int)
pref = (
    pd.to_numeric(um["unit_id"].astype(str).str.split("_").str[0], errors="coerce")
    .fillna(0)
    .astype(int)
)
um = um.assign(
    plant_code=np.where(pc > 0, pc, pref),
    uc_class=um["plant_group"].astype(str).map(fam),
)
P = (
    um.dropna(subset=["uc_class"])
    .groupby(["plant_code", "uc_class", "hour"])["mw"]
    .sum()
    .rename("p1")
    .reset_index()
)
on = on.merge(P, on=["plant_code", "uc_class", "hour"], how="left").fillna({"p1": 0.0})
binding = on["p1"] <= on["cur"] + 0.5  # P1 output at the current floor
uc_energy = float(on["p1"].sum())
out = {
    "cluster_hours_on": int(len(on)),
    "cluster_hours_a_lt_1": int((on["a"] < 1 - 1e-9).sum()),
    "cluster_hours_a_lt_mlf": int((on["a"] < on["mlf"] - 1e-9).sum()),
    "floor_excess_mwh": round(float(on["delta"].sum()), 1),
    "floor_excess_pct_of_uc_energy": round(
        100 * float(on["delta"].sum()) / uc_energy, 3
    ),
    "binding_cluster_hours": int(binding.sum()),
    "binding_excess_mwh": round(float(on.loc[binding, "delta"].sum()), 1),
    "binding_excess_pct_of_uc_energy": round(
        100 * float(on.loc[binding, "delta"].sum()) / uc_energy, 3
    ),
    "uc_cluster_p1_energy_twh": round(uc_energy / 1e6, 3),
    "a_quantiles_when_on": {
        q: round(float(on["a"].quantile(q)), 3) for q in (0.01, 0.1, 0.5)
    },
    "excess_by_class_mwh": {
        k: round(float(v), 1) for k, v in on.groupby("uc_class")["delta"].sum().items()
    },
}
print(json.dumps(out, indent=1))
