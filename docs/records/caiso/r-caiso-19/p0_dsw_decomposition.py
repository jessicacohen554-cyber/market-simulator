"""R-CAISO-19 phase 0 (ZERO LP): per-tranche / hod / month DSW import decomposition.

Reads the R-CAISO-18 leg bundles (unit_hourly + system) extracted from their
shard commits (RESULT-r-caiso-18 Retrievability SHAs, provenance only) into
the directory given as argv[1] as <dir>/legs/<year>/hourly/, and the measured
EIA-930 DSW corridor net import (derive_caiso_import_tranches.corridor_net_import).
Writes <dir>/p0_hourly.json. Usage: PYTHONPATH=.:src:scripts python3 <this> <dir>
"""

import sys
import json
import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts"]
from scripts.data.derive_caiso_import_tranches import corridor_net_import  # noqa: E402

S = sys.argv[1]
meas = corridor_net_import(years=range(2019, 2026))
hod = np.arange(8760) % 24
mon = pd.date_range("2019-01-01", periods=8760, freq="h").month.to_numpy()
out = {}
CLEAN = [
    "DSW_surplus_clean",
    "DSW_overnight_clean",
    "DSW_daytime_clean",
    "DSW_lateevening_clean",
]
for y in range(2019, 2026):
    u = pd.read_parquet(
        f"{S}/legs/{y}/hourly/unit_hourly_{y}.parquet",
        filters=[("zone", "in", ["WECC_DSW"]), ("pass", "==", "P1")],
    )
    sysd = pd.read_parquet(f"{S}/legs/{y}/hourly/system_{y}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    lam = sysd.pivot(index="hour", columns="zone", values="price")
    mw = u.pivot(index="hour", columns="unit_id", values="mw").fillna(0)
    mw.columns = [c.replace("WECC_DSW_", "") for c in mw.columns]
    cap = u.pivot(index="hour", columns="unit_id", values="cap_mw").fillna(0)
    cap.columns = mw.columns
    mc = u.pivot(index="hour", columns="unit_id", values="mc")
    mc.columns = mw.columns
    exp = [c for c in mw.columns if c.startswith("export")]
    model = (mw.drop(columns=exp).sum(axis=1) - mw[exp].sum(axis=1)).to_numpy()
    m = (
        meas.loc[y, "DSW"].to_numpy()
        if "DSW" in meas.columns
        else meas.loc[y].iloc[:, 0].to_numpy()
    )
    d = model - m
    r = {"model_twh": model.sum() / 1e6, "eia_twh": np.nansum(m) / 1e6}
    r["def_by_hod"] = [round(float(np.nansum(d[hod == h])) / 1e6, 2) for h in range(24)]
    r["def_by_month"] = [
        round(float(np.nansum(d[mon == k])) / 1e6, 2) for k in range(1, 13)
    ]
    r["meas_mean_by_hod"] = [round(float(np.nanmean(m[hod == h]))) for h in range(24)]
    r["model_mean_by_hod"] = [round(float(np.mean(model[hod == h]))) for h in range(24)]
    for t in ["DSW_solar_PV", "DSW_CCGT", "DSW_CT", "WECC_scarcity"] + CLEAN:
        if t in mw:
            r[t] = {
                "twh": round(mw[t].sum() / 1e6, 2),
                "cap_twh": round(cap[t].sum() / 1e6, 2),
                "mc_mean": round(float(mc[t].mean()), 2),
                "lam_sp15_minus_mc_mean": round(
                    float((lam["SP15_rest"] - mc[t]).mean()), 2
                ),
                "hrs_mc_below_sp15": int((mc[t] < lam["SP15_rest"]).sum()),
                "cf_when_cheaper": round(
                    float(
                        mw[t][mc[t] < lam["SP15_rest"]].sum()
                        / max(cap[t][mc[t] < lam["SP15_rest"]].sum(), 1)
                    ),
                    3,
                ),
            }
    r["clean_by_hod_mw"] = [
        round(float(mw[[c for c in CLEAN if c in mw]].sum(axis=1)[hod == h].mean()))
        for h in range(24)
    ]
    r["sp15_mean"] = round(float(lam["SP15_rest"].mean()), 2)
    r["dsw_node_zone_in_system"] = "WECC_DSW" in lam.columns
    if "WECC_DSW" in lam:
        r["dsw_lam_mean"] = round(float(lam["WECC_DSW"].mean()), 2)
    out[y] = r
json.dump(out, open(f"{S}/p0_hourly.json", "w"), indent=1, default=float)
for y, r in out.items():
    print(
        y,
        "model",
        round(r["model_twh"], 1),
        "eia",
        round(r["eia_twh"], 1),
        "sp15",
        r["sp15_mean"],
        "dswλ",
        r.get("dsw_lam_mean"),
    )
    for t in ["DSW_solar_PV", "DSW_CCGT", "DSW_CT", "WECC_scarcity"] + CLEAN:
        if t in r:
            print("   ", t, r[t])
    print("   def_hod", r["def_by_hod"])
    print("   def_mon", r["def_by_month"])
    print("   clean_hod", r["clean_by_hod_mw"])
    print("   meas_hod", r["meas_mean_by_hod"])
    print("   model_hod", r["model_mean_by_hod"])
