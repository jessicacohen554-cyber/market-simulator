"""SPP-92 (zero LP): actual model-BUBBLE-average RT prices vs the hub pair and the keeper's zonal duals.

Input: the load-SL parquet written by ``scripts/probes/_spp92_load_lmp_fetch.py`` (argv[1]).
Bubble = the keeper's own load partition (``iso_configs._spp_config`` docstring; EIA-930 sub-BA grouping):
North = {EDE, INDN, KACY, KCPL, LES, MPS, NPPD, OPPD, SECI, SPRM, WAUE, WR}; South = {CSWS, GRDA, OKGE, SPS, WFEC}.
Area price = mean over that area's LOAD settlement locations; bubble price = area prices weighted by the area's
annual EIA-930 sub-BA energy (data/raw/zone-specific-demand/SPP). Clock: GMT HE - 7 h = model clock (SPP-91 §2),
verified here against the committed hub series. Record: docs/records/spp/FINDING-spp-92-seam-2026-09-27.md.
"""
import glob, json, sys
import numpy as np, pandas as pd

ROOT = "/home/user/market-simulator"
NORTH = {"EDE","INDN","KACY","KCPL","LES","MPS","NPPD","OPPD","SECI","SPRM","WAUE","WR"}
SOUTH = {"CSWS","GRDA","OKGE","SPS","WFEC"}

def model_hoy(ts):
    doy = ts.dt.dayofyear.values.copy(); leap = ts.dt.is_leap_year.values
    feb29 = leap & (ts.dt.month.values == 2) & (ts.dt.day.values == 29)
    doy = np.where(leap & (doy > 59), doy - 1, doy)
    return np.where(feb29, -1, (doy - 1) * 24 + ts.dt.hour.values), ts.dt.year.values

def main():
    L = pd.read_parquet(sys.argv[1])
    sl = pd.read_csv(f"{ROOT}/data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv", dtype=str,
                     usecols=["SETLOCNAME","SETLOCTYPE","NODE_AREA"]).drop_duplicates("SETLOCNAME")
    area = dict(zip(sl.SETLOCNAME, sl.NODE_AREA)); area["SPPNORTH_HUB"] = "HUB_N"; area["SPPSOUTH_HUB"] = "HUB_S"
    L["area"] = L["loc"].map(area)
    ts = pd.to_datetime(L["date"]).dt.normalize() + pd.to_timedelta(L["he"] - 7, unit="h")
    L["hour"], L["year"] = model_hoy(ts)
    L = L[(L.hour >= 0) & L.year.between(2019, 2025)]
    A = L.groupby(["year","hour","area"])["value"].mean().unstack("area")
    dem = pd.concat([pd.read_csv(f) for f in glob.glob(f"{ROOT}/data/raw/zone-specific-demand/SPP/spp_subba_demand_*.csv")])
    dem["year"] = dem.period.str[:4].astype(int)
    W = dem.groupby(["year","subba"])["value"].sum().unstack("subba")
    hubs = pd.read_parquet(f"{ROOT}/data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet").pivot_table(
        index=["year","hour"], columns="zone", values="rt")
    out = {}
    for y in range(2019, 2026):
        a = A.loc[y].reindex(range(8760))
        def bubble(S):
            cols = [c for c in S if c in a.columns]
            w = W.loc[y, cols].astype(float)
            v = a[cols]; m = v.notna()
            return (v.fillna(0) * w.values).sum(axis=1) / (m * w.values).sum(axis=1)
        bN, bS = bubble(NORTH), bubble(SOUTH)
        h = hubs.loc[y].reindex(range(8760))
        k = pd.read_parquet(f"{ROOT}/results/calibration/spp86_arm_span/hourly/system_{y}.parquet").query("`pass`=='P1'")
        K = k.pivot_table(index="hour", columns="zone", values="price")
        d = pd.DataFrame({"bN": bN, "bS": bS, "hN": h["SPPNORTH_HUB"], "hS": h["SPPSOUTH_HUB"],
                          "fN": a.get("HUB_N"), "fS": a.get("HUB_S"),
                          "mN": K["SPP-North"].values, "mS": K["SPP-South"].values}).dropna(subset=["bN","bS","hN","hS"])
        clock_r = float(np.corrcoef(d.fN.fillna(d.hN), d.hN)[0,1]); clock_err = float((d.fN - d.hN).abs().max())
        bSN, hSN, mSN = d.bS - d.bN, d.hS - d.hN, d.mS - d.mN
        hi = d[["hN","hS"]].max(axis=1) >= 30
        area_mean = {c: round(float(a[c].mean()), 2) for c in sorted((NORTH | SOUTH) & set(a.columns))}
        out[y] = {
          "n_hours": len(d), "clock_r_fetchedhub_vs_committed": round(clock_r, 4), "clock_maxabs_err": round(clock_err, 3),
          "mean_SminusN_hub": round(float(hSN.mean()), 2), "mean_SminusN_bubble": round(float(bSN.mean()), 2),
          "mean_SminusN_keeper": round(float(mSN.mean()), 2),
          "mean_abs_SminusN_hub": round(float(hSN.abs().mean()), 2), "mean_abs_SminusN_bubble": round(float(bSN.abs().mean()), 2),
          "mean_abs_SminusN_keeper": round(float(mSN.abs().mean()), 2),
          "hours_bubble_S_dearer_ge5": int((bSN >= 5).sum()), "hours_bubble_N_dearer_ge5": int((bSN <= -5).sum()),
          "hours_hub_S_dearer_ge5": int((hSN >= 5).sum()), "hours_keeper_S_dearer_ge5": int((mSN >= 5).sum()),
          "hi30_NminusS_hub": round(float(-hSN[hi].mean()), 2), "hi30_NminusS_bubble": round(float(-bSN[hi].mean()), 2),
          "hi30_NminusS_keeper": round(float(-mSN[hi].mean()), 2),
          "hi30_p10_NminusS_bubble": round(float((-bSN[hi]).quantile(.1)), 2),
          "r_bubbleSN_hubSN": round(float(np.corrcoef(bSN, hSN)[0,1]), 3),
          "r_keeperSN_bubbleSN": round(float(np.corrcoef(mSN, bSN)[0,1]), 3),
          "mean_bubbleN_minus_hubN": round(float((d.bN - d.hN).mean()), 2), "mean_bubbleS_minus_hubS": round(float((d.bS - d.hS).mean()), 2),
          "mean_keeperN_minus_bubbleN": round(float((d.mN - d.bN).mean()), 2), "mean_keeperS_minus_bubbleS": round(float((d.mS - d.bS).mean()), 2),
          "area_mean_lmp": area_mean,
        }
        d.to_parquet(f"{ROOT}/results/calibration/_spp92_seam_hourly_bubble_{y}.parquet")
    json.dump(out, open(f"{ROOT}/docs/records/spp/spp92/_spp92_bubble_spread.json", "w"), indent=1)
    print(pd.DataFrame({y: {k: v for k, v in r.items() if k != "area_mean_lmp"} for y, r in out.items()}).to_string())
    print(pd.DataFrame({y: r["area_mean_lmp"] for y, r in out.items()}).to_string())

if __name__ == "__main__":
    main()
