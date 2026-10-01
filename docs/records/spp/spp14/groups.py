"""SPP-14 — the four-group binding-share table (data/raw/spp-binding-constraints/README.md,
fixed before the data). Membership RULES are this session's judgement, recorded here and in
the FINDING; the GROUPS are the README's. Inputs: the 2023-2025 RTBM binding rows
(State == BINDING) from SPP's own rollups (binding_E_<year>.parquet, built by census.py)."""
import pandas as pd, numpy as np, re, json
S="/tmp/claude-0/-home-user-market-simulator/1865f405-6252-5de2-847a-c8d1ca7ab210/scratchpad"
KANSAS={"WR","SECI","KCPL","MPS","KACY"}              # between the Nebraska North hub and the Oklahoma South hub
OKLA={"OKGE","WFEC","GRDA"}                            # Oklahoma-only utilities
OKLA_PLUS=OKLA|{"CSWS"}                                # CSWS (AEP West / PSO) spans OK-TX-AR-LA: admitted only beside an OKLA token
NORTH_HUB={"NPPD","OPPD","LES"}; SOUTH_HUB={"OKGE","WFEC","CSWS"}   # from Hub_Definitions.csv x SL map (449 / 460 nodes)
WEST={"WACM","WAUW","PSCO","BHBA","PRPA","BEPM","TSGT","CRCG","WAPA","BLKH","MPC"}  # WEIS / Western Interconnection tokens
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
rows=[]; detail=[]
for y in (2023,2024,2025):
    b=pd.read_parquet(f"{S}/bc/binding_E_{y}.parquet"); b["Shadow Price"]=pd.to_numeric(b["Shadow Price"],errors="coerce")
    b["tok"]=b["Contingent Facility"].map(tokens)
    gr=b.apply(group,axis=1,result_type="expand"); b["group"]=gr[0]; b["why"]=gr[1]
    b["hour"]=pd.to_datetime(b["hour"])
    hours_in_year=int(pd.Timestamp(f"{y+1}-01-01").dayofyear and (pd.Timestamp(f"{y+1}-01-01")-pd.Timestamp(f"{y}-01-01")).total_seconds()//3600)
    any_hours=b["hour"].nunique()
    for g in ("n_s_corridor","sps_tie","oklahoma_internal","other"):
        x=b[b.group==g]; h=x["hour"].nunique()
        rows.append({"year":y,"group":g,"binding_hours":h,"share_of_8760":round(h/8760,4),"share_of_year_hours":round(h/hours_in_year,4),"binding_intervals":len(x),"mean_shadow_price_while_binding":round(float(x["Shadow Price"].mean()),3) if len(x) else None,"mean_abs_shadow_price":round(float(x["Shadow Price"].abs().mean()),3) if len(x) else None,"n_constraints":x["Constraint Name"].nunique()})
    rows.append({"year":y,"group":"ANY (>=1 flowgate binding)","binding_hours":any_hours,"share_of_8760":round(any_hours/8760,4),"share_of_year_hours":round(any_hours/hours_in_year,4),"binding_intervals":len(b),"mean_shadow_price_while_binding":round(float(b["Shadow Price"].mean()),3),"mean_abs_shadow_price":round(float(b["Shadow Price"].abs().mean()),3),"n_constraints":b["Constraint Name"].nunique()})
    # sub-lines of other + sensitivity
    for why,x in b[b.group=="other"].groupby("why"):
        detail.append({"year":y,"kind":"other sub-line","label":why,"hours":x["hour"].nunique(),"intervals":len(x),"mean_abs_sp":round(float(x["Shadow Price"].abs().mean()),3)})
    for g in ("n_s_corridor","sps_tie","oklahoma_internal"):
        x=b[b.group==g]; top=x.groupby(["Constraint Name","Monitored Facility","Contingent Facility"]).agg(hours=("hour","nunique"),mean_sp=("Shadow Price","mean")).reset_index().sort_values("hours",ascending=False).head(8)
        for _,r in top.iterrows(): detail.append({"year":y,"kind":f"top {g}","label":f"{r['Constraint Name']} | {r['Monitored Facility']} | {str(r['Contingent Facility'])[:40]}","hours":int(r.hours),"intervals":None,"mean_abs_sp":round(abs(float(r.mean_sp)),3)})
    # sensitivity: POTTER_S out of sps_tie; CSWS-only rows into oklahoma
    pot=b[b.why=="Potter County interchange (monitored)"]; detail.append({"year":y,"kind":"sensitivity","label":"sps_tie hours WITHOUT the Potter County rule","hours":b[(b.group=="sps_tie")&(b.why!="Potter County interchange (monitored)")]["hour"].nunique(),"intervals":len(pot),"mean_abs_sp":None})
    csws=b[(b.group=="other")&(b.why=="other areas: CSWS")]; detail.append({"year":y,"kind":"sensitivity","label":"oklahoma_internal hours IF CSWS-only contingencies were admitted","hours":pd.concat([b[b.group=="oklahoma_internal"],csws])["hour"].nunique(),"intervals":len(csws),"mean_abs_sp":None})
    m2m=b[b["Constraint Name"].isin(set(pd.read_csv(f"{S}/bc/census.csv").query("year==@y and `Constraint Type`=='M2M'")["Constraint Name"]))]
    detail.append({"year":y,"kind":"note","label":"binding rows on M2M-type constraints (seam flowgates), all groups","hours":m2m["hour"].nunique(),"intervals":len(m2m),"mean_abs_sp":round(float(m2m["Shadow Price"].abs().mean()),3) if len(m2m) else None})
    b[["hour","Constraint Name","Monitored Facility","Contingent Facility","Shadow Price","group","why"]].to_parquet(f"{S}/bc/grouped_{y}.parquet",index=False)
T=pd.DataFrame(rows); D=pd.DataFrame(detail)
T.to_csv(f"{S}/bc/four_group_table.csv",index=False); D.to_csv(f"{S}/bc/four_group_detail.csv",index=False)
print(T.to_string(index=False)); print(); print(D.to_string(index=False,max_colwidth=110))
