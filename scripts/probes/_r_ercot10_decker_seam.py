"""Zero-LP probe (R-ERCOT-10 question c): ERCOT staggered unit retirements 2018-2025
vs the curated bin sheet. Reads EIA-860 retired + operable sheets only; no solve."""
import pandas as pd
from pathlib import Path

R = Path("/home/user/market-simulator/data/raw")
num = lambda s: pd.to_numeric(s, errors="coerce")
plant = pd.read_parquet(R / "eia-860/eia860_plant.parquet")
bacol = [c for c in plant.columns if "Balancing" in c and "Code" in c][0]
plant["pc"] = num(plant["Plant Code"])
erco = set(plant.loc[plant[bacol] == "ERCO", "pc"].dropna().astype(int))
ret = pd.read_parquet(R / "eia-860/eia860_generator_retired_and_canceled.parquet")
op = pd.read_parquet(R / "eia-860/eia860_generator_operable.parquet")
for d in (ret, op):
    d["pc"] = num(d["Plant Code"])
    d["mw"] = num(d["Nameplate Capacity (MW)"])
ret["ry"] = num(ret["Retirement Year"]); ret["rm"] = num(ret["Retirement Month"])
fossil = {"NG", "BIT", "SUB", "LIG", "DFO", "RFO", "OG", "PC", "WC", "BFG", "OBG", "LFG"}
r = ret[ret.pc.isin(erco) & ret.ry.between(2018, 2025) & ret["Status"].eq("RE")]
r = r[r["Energy Source 1"].isin(fossil)]
bins = pd.read_csv(R / "reference/custom-bin-assignments.csv")
binmw = bins.set_index("Plant_Code")["Nameplate_MW"]; bingrp = bins.set_index("Plant_Code")["Plant_Group"]
opmw = op[op.pc.isin(erco)].groupby("pc").mw.sum()
rows = []
for pc, g in r.groupby("pc"):
    pc = int(pc)
    for _, u in g.iterrows():
        rows.append(dict(pc=pc, name=u["Plant Name"], gen=u["Generator ID"], pm=u["Prime Mover"],
                         fuel=u["Energy Source 1"], mw=u.mw, ret=f"{int(u.ry)}-{int(u.rm) if u.rm==u.rm else 0:02d}",
                         plant_still_op_mw=float(opmw.get(pc, 0.0)),
                         in_bins=pc in binmw.index, bin_mw=float(binmw.get(pc, float('nan'))),
                         bin_group=bingrp.get(pc, "")))
df = pd.DataFrame(rows).sort_values(["ret", "pc"])
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
print(df.to_string(index=False))
print("\npartial-plant (plant still has operable units), MW >= 20:")
p = df[(df.plant_still_op_mw > 0) & (df.mw >= 20)]
print(p.to_string(index=False))
print(p.groupby(p.ret.str[:4]).mw.sum())
