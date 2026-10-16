"""UC-4-NEISO interim readings (zero LP): S2, U, D, P/T1-T2, X for 2020-21."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
REPO=Path("/home/user/market-simulator"); sys.path[:0]=[str(REPO),str(REPO/"src")]
from scripts.probes import _ucmilp_benefit_screen as bs
ARM=REPO/"results/calibration/ucmilp4_neiso_u4_span"
CTL=REPO/"results/calibration/w0_neiso_span"
UC15=REPO/"docs/records/neiso/ucmilp/data/ucmilp3_neiso_uc15_span"
cp=bs.committed_pct("NEISO")
out={}
for y in (2020,2021):
    r={}
    for name,b in (("ctl",CTL),("arm",ARM)):
        s=bs.screen_year("NEISO",b,y,cp)
        r[name+"_starts"]={g:(c["m1_starts_model"],c["m1_starts_cems"],c["m1_starts_ratio"]) for g,c in s["classes"].items()}
        r[name+"_M3"]=s.get("M3")
    # UC log
    lg=json.loads((ARM/f"uc_solve_log_{y}.json").read_text())
    r["summary"]={k:lg["summary"][k] for k in ("n_windows","uc_total_s","milp_s_sum","milp_s_mean","milp_s_p95","nodes_p50","nodes_p95","gap_p95","time_limit_hits","peak_rss_gb")}
    r["nonopt"]=sum(1 for w in lg["windows"] if str(w.get("status","Optimal"))!="Optimal")
    r["status_set"]=sorted({str(w.get("status")) for w in lg["windows"]})
    r["cd"]=lg["engine"].get("commitment_demand")
    r["integer"]=sum(1 for c in lg["clusters"] if c.get("integer")); r["nclusters"]=len(lg["clusters"])
    # uplift
    up=pd.read_parquet(ARM/f"hourly/uc_uplift_{y}.parquet")
    sysf=pd.read_parquet(ARM/f"hourly/system_{y}.parquet")
    p1=sysf[sysf["pass"].astype(str).str.upper().str.contains("1")] if "pass" in sysf else sysf
    ecost=float((p1.price*p1.demand).sum())
    r["uplift_usd"]=float(up.uplift_usd.sum()); r["energy_cost_usd"]=ecost; r["uplift_pct"]=100*r["uplift_usd"]/ecost
    r["unserved_mwh"]=float(p1.slack.sum())
    # price by tercile vs control and uc15
    def lw(b):
        f=pd.read_parquet(b/f"hourly/system_{y}.parquet"); f=f[f["pass"].astype(str).str.contains("1")]
        g=f.groupby("hour").apply(lambda d: pd.Series({"p":(d.price*d.demand).sum()/d.demand.sum(),"L":d.demand.sum(),"slack":d.slack.sum()}))
        return g
    C,A,U=lw(CTL),lw(ARM),lw(UC15)
    terc=pd.qcut(C.L,3,labels=["low","mid","high"])
    def m(G): return {"all":float((G.p*G.L).sum()/G.L.sum()),**{t:float((G.p[terc==t]*G.L[terc==t]).sum()/G.L[terc==t].sum()) for t in ["low","mid","high"]}}
    r["price_lw"]={"ctl":m(C),"arm":m(A),"uc15":m(U)}
    r["unserved_ctl"]=float(C.slack.sum())
    # uc15 starts from its own schedule-free slim? only class-level: skip
    sch=pd.read_parquet(ARM/f"hourly/uc_schedule_{y}.parquet")
    r["sched_v_by_class"]=sch.groupby("uc_class").v.sum().round(1).to_dict()
    s15=pd.read_parquet(UC15/f"hourly/uc_schedule_{y}.parquet")
    r["uc15_sched_v_by_class"]=s15.groupby("uc_class").v.sum().round(1).to_dict()
    out[y]=r
print(json.dumps(out,indent=1,default=str))
