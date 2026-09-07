"""SPP-53 leg 1: the 2026 daily RTBM BC files -> (i) per-file column census, (ii) the reduced corridor
sidecar (PRECOMMIT §5), (iii) per-constituent limit-at-bind stats."""
import sys, glob, re, pandas as pd, numpy as np
S=sys.argv[1]; OUT=sys.argv[2]
exec(open(f"{S}/parse_2325.py").read().split("# ---------------------------------------------------------------------------------------------")[0].split("# ---- groups.py rules, verbatim")[1].replace("-------------------------------------------------------------",""))
files=sorted(glob.glob(f"{S}/daily/RTBM-DAILY-BC-*.csv"))
census=[]; rows=[]
for f in files:
    import csv
    C14=["Interval","GMTIntervalEnd","Constraint Name","Constraint Type","NERCID","TLR Level","State","Shadow Price","Monitored Facility","Contingent Facility","Source Limit","Real Time Effective Limit","Initial Effective Limit","Interconnect"]
    with open(f,newline="") as fh:
        rd=csv.reader(fh); hdr=next(rd); recs=[r for r in rd if r]
    n10=sum(1 for r in recs if len(r)==10); n14=sum(1 for r in recs if len(r)==14); nother=len(recs)-n10-n14
    day=f[-12:-4]
    census.append({"day":day,"hdr_ncol":len(hdr),"rows_10":n10,"rows_14":n14,"rows_other":nother,"nrow":len(recs),"has_rtel":n14>0})
    if n14==0: continue
    d=pd.DataFrame([r+[None]*(14-len(r)) for r in recs if len(r) in (10,14)],columns=C14)
    d=d[d["Real Time Effective Limit"].notna()]
    d=d[d.State.isin(["BINDING","BREACHED","ACTIVATED"])].copy()
    d["tok"]=d["Contingent Facility"].map(tokens)
    g=d.apply(group,axis=1,result_type="expand"); d["group"]=g[0]
    d=d[d.group.eq("n_s_corridor")]
    rows.append(d[["Constraint Name","Monitored Facility","Contingent Facility","State","Shadow Price","Source Limit","Real Time Effective Limit","Initial Effective Limit","Interconnect","GMTIntervalEnd"]])
C=pd.DataFrame(census); C.to_csv(f"{S}/bc/daily_census_2026.csv",index=False)
print("files",len(C),"14-col",int(C.has_rtel.sum()),"first 14-col day",C[C.has_rtel].day.min() if C.has_rtel.any() else None,"last",C.day.max())
print(C.groupby("has_rtel").agg(n=("day","size"),first=("day","min"),last=("day","max"),rows10=("rows_10","sum"),rows14=("rows_14","sum"),other=("rows_other","sum")).to_string()); print(C[(C.day>="20260315")&(C.day<="20260401")].to_string())
D=pd.concat(rows,ignore_index=True)
for c in ("Shadow Price","Source Limit","Real Time Effective Limit","Initial Effective Limit"): D[c]=pd.to_numeric(D[c],errors="coerce")
D["GMTIntervalEnd"]=pd.to_datetime(D["GMTIntervalEnd"],format="mixed",utc=True)
D=D.sort_values(["GMTIntervalEnd","Constraint Name"]).reset_index(drop=True)
D.to_parquet(OUT,index=False)
print("sidecar rows",len(D),"span",D.GMTIntervalEnd.min(),D.GMTIntervalEnd.max(),"constraints",D["Constraint Name"].nunique(),D.State.value_counts().to_dict(),D.Interconnect.value_counts().to_dict())
b=D[D.State.isin(["BINDING","BREACHED"])]
st=b.groupby(["Constraint Name","Monitored Facility"]).agg(n_bind=("State","size"),rtel_med=("Real Time Effective Limit","median"),rtel_p10=("Real Time Effective Limit",lambda s:s.quantile(.1)),rtel_p90=("Real Time Effective Limit",lambda s:s.quantile(.9)),src_med=("Source Limit","median"),init_med=("Initial Effective Limit","median"),derate_share=("Real Time Effective Limit",lambda s: float((s < b.loc[s.index,"Source Limit"]-1e-9).mean())),mean_asp=("Shadow Price",lambda s:s.abs().mean())).reset_index().sort_values("n_bind",ascending=False)
st.to_csv(f"{S}/bc/limits_2026_by_constraint.csv",index=False); pd.set_option("display.width",300)
print(st.head(40).to_string(index=False,max_colwidth=34))
