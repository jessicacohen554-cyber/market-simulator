"""SPP-57 (copied VERBATIM from spp53/parse_2325.py, unchanged): 2023-2025 RTBM binding rows -> hourly per-constraint mean |SP| on the LMP builder's
local non-leap 8760 clock, plus constraint metadata and SPP-14's group (rules copied VERBATIM
from docs/handoffs/spp14/groups.py -- unchanged)."""
import re, sys, zipfile, glob
import pandas as pd, numpy as np
S = sys.argv[1]
R = "/home/user/market-simulator/data/raw/spp-binding-constraints"
# ---- groups.py rules, verbatim -------------------------------------------------------------
KANSAS={"WR","SECI","KCPL","MPS","KACY"}
OKLA={"OKGE","WFEC","GRDA"}
OKLA_PLUS=OKLA|{"CSWS"}
WEST={"WACM","WAUW","PSCO","BHBA","PRPA","BEPM","TSGT","CRCG","WAPA","BLKH","MPC"}
sl=pd.read_csv("/home/user/market-simulator/data/raw/spp-planning/SL_to_Pnode_to_Zone_with_Area.csv",dtype=str,usecols=["NODE_AREA"])
AREAS=set(sl.NODE_AREA.dropna().unique())|WEST|{"SPA","AECI","AMRN","MEC","OTP","GRE","NSP","ALTW","DPC","MDU","MHEB","SOUC","TVA","EES","CLEC","LAFA","EDE","SPRM","INDN","SPS","WAUE","NPPD","OPPD","LES"}
def tokens(cf):
    if not isinstance(cf,str) or cf.strip()=="BASE": return frozenset()
    head=cf.split(":")[0]
    return frozenset(t for t in re.split(r"[\s/]+",head.strip()) if t in AREAS)
def group(row):
    name=row["Constraint Name"]; mon=str(row["Monitored Facility"]); t=row["tok"]
    if name in ("SPPSPSTIES","SPSNMTIES"): return "sps_tie","named ITP interface"
    if "OSAGE_OG - WEBBTAP4" in mon: return "oklahoma_internal","named Osage-Webber Tap"
    if "RUSSETT - SBROWN" in mon: return "oklahoma_internal","named Russett-S Brown"
    if "POTTER_S" in mon: return "sps_tie","Potter County interchange (monitored)"
    if t & WEST: return "other","west"
    if "SPS" in t and (t-{"SPS"}): return "sps_tie","SPS + East-area contingency"
    if t and t<=OKLA_PLUS and (t&OKLA): return "oklahoma_internal","contingency areas within OK utilities"
    if t & KANSAS: return "n_s_corridor","contingency touches a Kansas-corridor area"
    if t=={"SPS"}: return "other","SPS-internal"
    if not t: return "other","BASE / no area token"
    return "other","other areas: "+"+".join(sorted(t))
# ---------------------------------------------------------------------------------------------
def local_hoy(local_ts):
    """LMP builder convention: local Central clock, non-leap 8760, Feb 29 dropped. Interval stamps are
    interval END labels, so hour-beginning = (stamp - 1 min).hour."""
    t = local_ts - pd.Timedelta(minutes=1)
    doy = t.dt.dayofyear.values.copy()
    leap = t.dt.is_leap_year.values
    feb29 = leap & (t.dt.month.values == 2) & (t.dt.day.values == 29)
    doy = np.where(leap & (doy > 59), doy - 1, doy)   # after Feb 29 in a leap year, renumber
    h = (doy - 1) * 24 + t.dt.hour.values
    h = np.where(feb29, -1, h)
    return h, t.dt.year.values
frames=[]; meta=[]
files = sorted(glob.glob(f"{R}/RTBM-BC-YEARLY-*.csv.zip")) + sorted(glob.glob(f"{R}/RTBM-BC-MONTHLY-2025*.csv.zip"))
for f in files:
    z = zipfile.ZipFile(f); n = z.namelist()[0]
    df = pd.read_csv(z.open(n), usecols=["Interval","GMTIntervalEnd","Constraint Name","State","Shadow Price","Monitored Facility","Contingent Facility"], dtype={"Shadow Price":float})
    print(f, len(df), flush=True)
    df["Interval"] = pd.to_datetime(df["Interval"], format="%m/%d/%Y %H:%M:%S")
    hoy, yr = local_hoy(df["Interval"]); df["hoy"]=hoy; df["year"]=yr
    # intervals present per (year, hoy), for the hourly-mean divisor (fold-day hours have 24)
    niv = df.drop_duplicates(["year","hoy","GMTIntervalEnd"]).groupby(["year","hoy"]).size().rename("n_iv")
    b = df[df.State.eq("BINDING") & (df.hoy>=0)].copy()
    b["asp"] = b["Shadow Price"].abs()
    hs = b.groupby(["year","hoy","Constraint Name"])["asp"].sum().reset_index()
    hs = hs.join(niv, on=["year","hoy"]); hs["mean_asp"] = hs.asp / hs.n_iv
    frames.append(hs[["year","hoy","Constraint Name","mean_asp"]])
    m = b.groupby("Constraint Name").agg(hours=("hoy","nunique"), intervals=("asp","size"), mean_asp=("asp","mean"),
        mon=("Monitored Facility", lambda s: s.mode().iat[0]), con=("Contingent Facility", lambda s: s.mode().iat[0])).reset_index()
    m["year"]=int(yr[0]) if len(set(yr))==1 else -1; meta.append(m)
    del df, b
H = pd.concat(frames); H.to_parquet(f"{S}/bc/hourly_asp_2325.parquet", index=False)
M = pd.concat(meta)
Mp = M.groupby("Constraint Name").agg(hours=("hours","sum"), intervals=("intervals","sum"),
        mon=("mon", lambda s: s.mode().iat[0]), con=("con", lambda s: s.mode().iat[0])).reset_index()
Mp["Monitored Facility"]=Mp.mon; Mp["Contingent Facility"]=Mp.con
Mp["tok"]=Mp["Contingent Facility"].map(tokens)
gr = Mp.apply(group, axis=1, result_type="expand"); Mp["group"]=gr[0]; Mp["why"]=gr[1]
Mp.drop(columns=["tok","mon","con"]).to_parquet(f"{S}/bc/constraints_2325.parquet", index=False)
M.to_parquet(f"{S}/bc/constraints_by_year_2325.parquet", index=False)
print("constraints", len(Mp), "with >=263 h:", (Mp.hours>=263).sum(), Mp.groupby("group").size().to_dict(), flush=True)
