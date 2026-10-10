"""FIX-4 readings for one ERCOT UC bundle-year: forced peak-tranche TWh, uplift, unserved (zero LP)."""

import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.compute as pc_
import pyarrow.parquet as pq

b, y = Path(sys.argv[1]), int(sys.argv[2])
h = b / "hourly"

t = pq.read_table(
    h / f"unit_marginal_{y}.parquet",
    columns=[
        "pass",
        "unit_id",
        "plant_code",
        "plant_group",
        "zone",
        "hour",
        "mw",
        "mc",
    ],
)
t = t.filter(pc_.match_substring_regex(pc_.cast(t["unit_id"], "string"), r"_peak\d*$"))
um = t.to_pandas()
um = um[um["pass"] == "P1"]
sysf = pd.read_parquet(h / f"system_{y}.parquet")
sysf = sysf[sysf["pass"] == "P1"]
sch = pd.read_parquet(h / f"uc_schedule_{y}.parquet")
up = pd.read_parquet(h / f"uc_uplift_{y}.parquet")
fam = {"CC_REGULAR": "cc", "CC_CHP": "cc", "ST_GAS": "st_gas"}
pc = um["plant_code"].astype(int)
pref = (
    pd.to_numeric(um["unit_id"].astype(str).str.split("_").str[0], errors="coerce")
    .fillna(0)
    .astype(int)
)
um = um.assign(
    pc=np.where(pc > 0, pc, pref), fam=um["plant_group"].astype(str).map(fam)
)
on = sch[sch["u"] > 0][["plant_code", "uc_class", "hour"]].rename(
    columns={"plant_code": "pc", "uc_class": "fam"}
)
peak = um[um["unit_id"].astype(str).str.contains(r"_peak\d*$") & um["fam"].notna()]
peak = peak.merge(on, on=["pc", "fam", "hour"], how="inner")
peak = peak.merge(sysf[["zone", "hour", "price"]], on=["zone", "hour"], how="left")
forced = peak[(peak["mw"] > 1e-3) & (peak["mc"] > peak["price"] + 0.01)]
fw = forced["mw"].to_numpy()
order = np.argsort(forced["mc"].to_numpy())
cum = np.cumsum(fw[order])
med_mc = (
    float(forced["mc"].to_numpy()[order][np.searchsorted(cum, cum[-1] / 2)])
    if fw.size
    else None
)
energy_cost_sys = float((sysf["price"] * sysf["demand"]).sum())
log = json.loads((b / f"uc_solve_log_{y}.json").read_text())
out = {
    "forced_peak_twh": round(float(fw.sum()) / 1e6, 3),
    "forced_peak_by_family_twh": {
        k: round(float(v) / 1e6, 3)
        for k, v in forced.groupby("fam")["mw"].sum().items()
    },
    "forced_peak_median_mc": None if med_mc is None else round(med_mc, 1),
    "peak_tranche_energy_while_committed_twh": round(float(peak["mw"].sum()) / 1e6, 3),
    "uplift_musd": round(float(up["uplift_usd"].sum()) / 1e6, 1),
    "uc_energy_cost_musd": round(float(up["energy_cost_usd"].sum()) / 1e6, 1),
    "system_energy_cost_musd": round(energy_cost_sys / 1e6, 1),
    "uplift_pct_of_system_energy_cost": round(
        100 * float(up["uplift_usd"].sum()) / energy_cost_sys, 2
    ),
    "unserved_mwh": round(float(sysf["slack"].sum()), 1),
    "engine": log["engine"].get("version"),
    "reused_schedule": log["engine"].get("reused_schedule"),
    "uc_total_s": log["summary"].get("uc_total_s"),
}
print(json.dumps(out, indent=1))
