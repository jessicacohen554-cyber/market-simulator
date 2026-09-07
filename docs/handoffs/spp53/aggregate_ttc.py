"""SPP-53 §2.1 aggregation: T*_f = L_f / psi_f over identified corridor constituents; hours-weighted median."""
import sys, re, numpy as np, pandas as pd
S=sys.argv[1]
psi=pd.read_parquet(f"{S}/bc/psi_all.parquet"); c=psi[psi.group.eq("n_s_corridor")].copy()
lim=pd.read_csv(f"{S}/bc/limits_2026_by_constraint.csv")
xc=pd.read_csv(f"{S}/bc/registry_xcheck.csv")
def key(s):
    s=str(s).upper(); s=re.sub(r"^(XFMR|XF|LN)\s+","",s); s=re.sub(r"\s+\d+(/\d+)?\s*KV$","",s)
    a=[re.sub(r"\d+$","",x.strip()) for x in s.split(" - ")]
    if len(a)==1: return a[0]
    if len(a)==2 and a[0]==a[1]: return a[0]
    return " - ".join(sorted(a)) if len(a)==2 else s
lim["k"]=lim["Monitored Facility"].map(key); c["k"]=c["Monitored Facility"].map(key)
lim_by_name=lim.set_index("Constraint Name"); lim_by_elem=lim.groupby("k").agg(n_bind=("n_bind","sum"),rtel_med=("rtel_med","median"),rtel_p10=("rtel_p10","min"),rtel_p90=("rtel_p90","max"),src_med=("src_med","median"),derate_share=("derate_share","mean"),names=("Constraint Name",lambda s:"|".join(s)))
out=[]
for _,r in c.iterrows():
    n=r["Constraint Name"]; src="none"; L=np.nan; nb=0; p10=p90=srcm=der=np.nan; joined=""
    if n in lim_by_name.index and lim_by_name.loc[n,"n_bind"]>=100:
        x=lim_by_name.loc[n]; src="2026 archive (same Constraint Name)"; L=x.rtel_med; nb=int(x.n_bind); p10,p90,srcm,der=x.rtel_p10,x.rtel_p90,x.src_med,x.derate_share; joined=n
    elif r.k in lim_by_elem.index and lim_by_elem.loc[r.k,"n_bind"]>=100:
        x=lim_by_elem.loc[r.k]; src="2026 archive (same Monitored Facility)"; L=x.rtel_med; nb=int(x.n_bind); p10,p90,srcm,der=x.rtel_p10,x.rtel_p90,x.src_med,x.derate_share; joined=x.names
    else:
        y=xc[xc["Constraint Name"].eq(n)].iloc[0]
        import ast
        if pd.notna(y.temp_norm): src="registry Temp_Flowgate NormLimit"; L=y.temp_norm
        elif pd.notna(y.perm_normal_mean): src="registry Flowgates seasonal Normal mean"; L=y.perm_normal_mean
        elif isinstance(y.elem_temp_norm_range,str) and y.elem_temp_norm_range!="None": src="registry Temp_Flowgate NormLimit (same element, other id)"; L=float(re.findall(r"\((\d+\.?\d*)",y.elem_temp_norm_range)[0])
        elif isinstance(y.elem_perm_normal_range,str) and y.elem_perm_normal_range!="None": src="registry Flowgates seasonal Normal mean (same element, other id)"; L=float(re.findall(r"\((\d+\.?\d*)",y.elem_perm_normal_range)[0])
    T=L/r.psi if (r.identified and pd.notna(L)) else np.nan
    out.append({"Constraint Name":n,"Monitored Facility":r["Monitored Facility"],"why":r.why,"hours":int(r.hours),"psi":r.psi,"t":r.t,"identified":bool(r.identified),"L_source":src,"L_f":L,"n_bind_2026":nb,"rtel_p10":p10,"rtel_p90":p90,"src_med":srcm,"derate_share":der,"joined":joined,"T_star":T})
O=pd.DataFrame(out).sort_values("hours",ascending=False); O.to_csv(f"{S}/bc/tstar_table.csv",index=False)
pd.set_option("display.width",320); print(O.drop(columns=["joined"]).to_string(index=False,max_colwidth=30))
I=O[O.identified & O.T_star.notna()].sort_values("T_star")
w=I.hours.values; cw=np.cumsum(w)/w.sum()
def wq(q): return float(I.T_star.values[np.searchsorted(cw,q)])
med=wq(0.5); p25=wq(0.25); p75=wq(0.75)
print(f"\nidentified with L_f: {len(I)} (R1 needs >=3) | hours-weighted median T* = {med:,.0f} MW -> TTC = {round(med,-2):,.0f} MW | weighted p25 {p25:,.0f} p75 {p75:,.0f} ratio {p75/p25:.2f} (R4 fails if >10) | R2 (>=23,300) {'FAIL' if med>=23300 else 'pass'} | R3 (>=37,400) {'FAIL' if med>=37400 else 'pass'}")
print("unweighted median",I.T_star.median(),"min",I.T_star.min(),"max",I.T_star.max())
# S->N set (psi<0, t<=-2): reported, not aggregated
Sn=O[(O.psi<0)&(O.t<=-2)&O.L_f.notna()].copy(); Sn["T_star_SN"]=Sn.L_f/(-Sn.psi)
print("\nS->N-loaded constituents (psi<0, t<=-2):"); print(Sn[["Constraint Name","Monitored Facility","hours","psi","t","L_source","L_f","T_star_SN"]].to_string(index=False,max_colwidth=30))
if len(Sn): 
    Sn=Sn.sort_values("T_star_SN"); cws=np.cumsum(Sn.hours.values)/Sn.hours.sum(); print("S->N hours-weighted median T*:",float(Sn.T_star_SN.values[np.searchsorted(cws,0.5)]))
