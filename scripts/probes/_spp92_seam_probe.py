"""SPP-92 (zero LP): why the keeper's North-South seam almost never separates.

Reads only committed artifacts:
  * the keeper's hourly/system_<y>.parquet (zonal P1 duals; |S-N| > tol <=> the 3,400 MW link is at bound,
    sign gives direction: S dearer => N->S at bound),
  * data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet (RT hubs, model clock),
  * data/raw/spp-binding-constraints RTBM BC files (BINDING/BREACHED rows), grouped with SPP-14's rules
    (docs/records/spp/spp14/groups.py, copied verbatim via spp53/parse_2325.py) and mapped to the model clock
    from GMTIntervalEnd (model clock = CST hour-beginning, non-leap 8760; SPP-91 §2 clock note).
Writes docs/records/spp/spp92/_spp92_seam_probe.json (gitignored-style scratch record) and prints the tables.
"""
import glob, json, re, sys, zipfile
import numpy as np, pandas as pd

ROOT = "/home/user/market-simulator"
KEEP = f"{ROOT}/results/calibration/spp86_arm_span/hourly"
R = f"{ROOT}/data/raw/spp-binding-constraints"
YEARS = range(2019, 2026)
TOL = 0.01  # $/MWh: dual difference below this = link not at bound (LP degeneracy noise)

# ---- SPP-14 group rules, verbatim (docs/records/spp/spp14/groups.py) --------------------------
KANSAS={"WR","SECI","KCPL","MPS","KACY"}; OKLA={"OKGE","WFEC","GRDA"}; OKLA_PLUS=OKLA|{"CSWS"}
WEST={"WACM","WAUW","PSCO","BHBA","PRPA","BEPM","TSGT","CRCG","WAPA","BLKH","MPC"}
sl=pd.read_csv(f"{ROOT}/data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv",dtype=str,usecols=["NODE_AREA"])
AREAS=set(sl.NODE_AREA.dropna().unique())|WEST|{"SPA","AECI","AMRN","MEC","OTP","GRE","NSP","ALTW","DPC","MDU","MHEB","SOUC","TVA","EES","CLEC","LAFA","EDE","SPRM","INDN","SPS","WAUE","NPPD","OPPD","LES"}
def tokens(cf):
    if not isinstance(cf,str) or cf.strip()=="BASE": return frozenset()
    return frozenset(t for t in re.split(r"[\s/]+",cf.split(":")[0].strip()) if t in AREAS)
def group(name, mon, t):
    mon=str(mon)
    if name in ("SPPSPSTIES","SPSNMTIES"): return "sps_tie"
    if "OSAGE_OG - WEBBTAP4" in mon or "RUSSETT - SBROWN" in mon: return "oklahoma_internal"
    if "POTTER_S" in mon: return "sps_tie"
    if t & WEST: return "other"
    if "SPS" in t and (t-{"SPS"}): return "sps_tie"
    if t and t<=OKLA_PLUS and (t&OKLA): return "oklahoma_internal"
    if t & KANSAS: return "n_s_corridor"
    return "other"
# ---------------------------------------------------------------------------------------------

def model_hoy(ts_gmt_end):
    """GMT interval-end stamp -> model clock (CST hour-beginning, non-leap 8760; Feb 29 -> -1)."""
    t = ts_gmt_end - pd.Timedelta(minutes=1) - pd.Timedelta(hours=6)
    doy = t.dt.dayofyear.values.copy(); leap = t.dt.is_leap_year.values
    feb29 = leap & (t.dt.month.values == 2) & (t.dt.day.values == 29)
    doy = np.where(leap & (doy > 59), doy - 1, doy)
    return np.where(feb29, -1, (doy - 1) * 24 + t.dt.hour.values), t.dt.year.values

def load_bc():
    files = sorted(glob.glob(f"{R}/RTBM-BC-YEARLY-*.zip")) + sorted(glob.glob(f"{R}/RTBM-BC-MONTHLY-2025*.csv.zip"))
    out = []
    for f in files:
        z = zipfile.ZipFile(f); n = [x for x in z.namelist() if x.endswith(".csv")][0]
        df = pd.read_csv(z.open(n), usecols=["GMTIntervalEnd","Constraint Name","State","Shadow Price",
                         "Monitored Facility","Contingent Facility"], dtype={"Shadow Price": float})
        df.columns = [c.strip() for c in df.columns]
        df = df[df.State.isin(["BINDING","BREACHED"])].copy()
        df["g"] = pd.to_datetime(df["GMTIntervalEnd"], format="mixed")
        df["hoy"], df["year"] = model_hoy(df["g"])
        df = df[(df.hoy >= 0) & df.year.isin(list(YEARS))]
        key = df[["Constraint Name","Monitored Facility","Contingent Facility"]].drop_duplicates()
        key["grp"] = [group(a, b, tokens(c)) for a, b, c in key.itertuples(index=False)]
        df = df.merge(key, on=["Constraint Name","Monitored Facility","Contingent Facility"], how="left")
        df["asp"] = df["Shadow Price"].abs() / 12.0      # hourly-mean |SP| contribution of one 5-min interval
        out.append(df[["year","hoy","Constraint Name","grp","asp"]])
        print(f, len(df), file=sys.stderr, flush=True)
    return pd.concat(out)

def main():
    act = pd.read_parquet(f"{ROOT}/data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet")
    A = act.pivot_table(index=["year","hour"], columns="zone", values="rt")
    bc = load_bc()
    G = bc.groupby(["year","hoy","grp"])["asp"].sum().unstack("grp").fillna(0.0)
    G.index.names = ["year","hour"]
    res = {}
    for y in YEARS:
        s = pd.read_parquet(f"{KEEP}/system_{y}.parquet").query("`pass`=='P1'")
        M = s.pivot_table(index="hour", columns="zone", values="price")
        d = pd.DataFrame({"mN": M["SPP-North"].values, "mS": M["SPP-South"].values})
        a = A.loc[y].reindex(range(8760)); d["aN"] = a["SPPNORTH_HUB"].values; d["aS"] = a["SPPSOUTH_HUB"].values
        d = d.dropna(subset=["aN","aS"])
        g = G.loc[y].reindex(range(8760)).fillna(0.0) if y in G.index.get_level_values(0) else None
        for c in ("n_s_corridor","oklahoma_internal","sps_tie","other"):
            d[c] = g[c].reindex(d.index).values if (g is not None and c in g) else 0.0
        d["mSN"] = d.mS - d.mN; d["aSN"] = d.aS - d.aN
        bound = d.mSN.abs() > TOL; ns = d.mSN > TOL; sn = d.mSN < -TOL
        hi = (d[["aN","aS"]].max(axis=1) >= 30)   # SPP-91's slice: actual hub RT >= $30
        sepS = d.aSN >= 5; sepN = d.aSN <= -5
        r = {
          "keeper_at_bound_h": int(bound.sum()), "keeper_NtoS_h": int(ns.sum()), "keeper_StoN_h": int(sn.sum()),
          "keeper_mean_SminusN_when_bound_NtoS": round(float(d.mSN[ns].mean()), 2) if ns.any() else None,
          "keeper_mean_SminusN_when_bound_StoN": round(float(d.mSN[sn].mean()), 2) if sn.any() else None,
          "keeper_mean_abs_SminusN": round(float(d.mSN.abs().mean()), 2),
          "actual_mean_abs_SminusN": round(float(d.aSN.abs().mean()), 2),
          "actual_hours_S_dearer_ge5": int(sepS.sum()), "actual_hours_N_dearer_ge5": int(sepN.sum()),
          "actual_mean_SminusN": round(float(d.aSN.mean()), 2), "keeper_mean_SminusN": round(float(d.mSN.mean()), 2),
          "hi30_h": int(hi.sum()),
          "hi30_keeper_mean_NminusS": round(float(-d.mSN[hi].mean()), 2), "hi30_actual_mean_NminusS": round(float(-d.aSN[hi].mean()), 2),
          "hi30_keeper_p10_NminusS": round(float((-d.mSN[hi]).quantile(.1)), 2), "hi30_actual_p10_NminusS": round(float((-d.aSN[hi]).quantile(.1)), 2),
          # co-occurrence
          "in_actual_S_dearer_ge5__keeper_NtoS_share": round(float(ns[sepS].mean()), 3) if sepS.any() else None,
          "in_actual_S_dearer_ge5__keeper_mean_SminusN": round(float(d.mSN[sepS].mean()), 2) if sepS.any() else None,
          "in_actual_S_dearer_ge5__actual_mean_SminusN": round(float(d.aSN[sepS].mean()), 2) if sepS.any() else None,
          "in_actual_N_dearer_ge5__keeper_StoN_share": round(float(sn[sepN].mean()), 3) if sepN.any() else None,
          "in_keeper_NtoS__actual_mean_SminusN": round(float(d.aSN[ns].mean()), 2) if ns.any() else None,
          "in_keeper_StoN__actual_mean_SminusN": round(float(d.aSN[sn].mean()), 2) if sn.any() else None,
          # level: which side misses in the >=$30 slice
          "hi30_model_minus_actual_N": round(float((d.mN - d.aN)[hi].mean()), 2),
          "hi30_model_minus_actual_S": round(float((d.mS - d.aS)[hi].mean()), 2),
          "all_model_minus_actual_N": round(float((d.mN - d.aN).mean()), 2),
          "all_model_minus_actual_S": round(float((d.mS - d.aS).mean()), 2),
        }
        # measured congestion location in the actual separated hours (S dearer by >= $5)
        if g is not None:
            corr = d.n_s_corridor > 0; ok = d.oklahoma_internal > 0; oth = (d.other > 0) | (d.sps_tie > 0)
            r.update({
              "sepS_share_corridor_binding": round(float(corr[sepS].mean()), 3),
              "sepS_share_oklahoma_binding": round(float(ok[sepS].mean()), 3),
              "sepS_share_no_corridor_but_ok_or_other": round(float((~corr & (ok | oth))[sepS].mean()), 3),
              "all_share_corridor_binding": round(float(corr.mean()), 3),
              "sepS_mean_corridor_absSP": round(float(d.n_s_corridor[sepS].mean()), 1),
              "sepS_mean_oklahoma_absSP": round(float(d.oklahoma_internal[sepS].mean()), 1),
              "sepS_mean_other_absSP": round(float((d.other + d.sps_tie)[sepS].mean()), 1),
              "corr_r_aSN_corridorSP": round(float(np.corrcoef(d.aSN, d.n_s_corridor)[0,1]), 3),
              "corr_r_aSN_oklaSP": round(float(np.corrcoef(d.aSN, d.oklahoma_internal)[0,1]), 3),
              "corr_r_aSN_otherSP": round(float(np.corrcoef(d.aSN, d.other + d.sps_tie)[0,1]), 3),
            })
        res[y] = r
        d.to_parquet(f"{ROOT}/results/calibration/_spp92_seam_hourly_{y}.parquet")
    json.dump(res, open(f"{ROOT}/docs/records/spp/spp92/_spp92_seam_probe.json", "w"), indent=1)
    print(pd.DataFrame(res).to_string())

if __name__ == "__main__":
    main()
