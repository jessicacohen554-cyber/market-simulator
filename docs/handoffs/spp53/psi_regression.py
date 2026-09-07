"""SPP-53 leg 2: psi_f from the hub-spread / shadow-price decomposition (PRECOMMIT §2.1), OLS + HC1."""
import sys, numpy as np, pandas as pd
S=sys.argv[1]
H=pd.read_parquet(f"{S}/bc/hourly_asp_2325.parquet"); M=pd.read_parquet(f"{S}/bc/constraints_2325.parquet")
keep=M[M.hours>=263]["Constraint Name"].tolist()
W=H[H["Constraint Name"].isin(keep)].pivot_table(index=["year","hoy"],columns="Constraint Name",values="mean_asp",aggfunc="sum",fill_value=0.0)
L=pd.read_parquet("/home/user/market-simulator/data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet")
P=L.pivot_table(index=["year","hour"],columns="zone",values="rt"); P.index.names=["year","hoy"]
y=(P["SPPSOUTH_HUB"]-P["SPPNORTH_HUB"]).rename("spread")
D=W.join(y,how="right").dropna(subset=["spread"]).fillna(0.0)
cols=list(W.columns); X=np.column_stack([np.ones(len(D)),D[cols].values]); yv=D["spread"].values
n,k=X.shape; XtX_inv=np.linalg.pinv(X.T@X); beta=XtX_inv@X.T@yv; e=yv-X@beta
meat=(X*e[:,None]**2).T@X; cov=XtX_inv@meat@XtX_inv*(n/(n-k)); se=np.sqrt(np.diag(cov)); t=beta/se
r2=1-e.var()/yv.var()
res=pd.DataFrame({"Constraint Name":["_intercept"]+cols,"psi":beta,"se":se,"t":t}).merge(M,on="Constraint Name",how="left")
res["identified"]=(res.psi>0)&(res.t>=2.0)&(res.psi<=1.0)
res.to_parquet(f"{S}/bc/psi_all.parquet",index=False); res.to_csv(f"{S}/bc/psi_all.csv",index=False)
print(f"n={n} k={k} R2={r2:.3f} intercept={beta[0]:.3f} (t={t[0]:.1f})")
pd.set_option("display.width",250)
c=res[res.group.eq("n_s_corridor")].sort_values("hours",ascending=False)
print("\nCORRIDOR constituents (>=263 h):",len(c),"identified:",int(c.identified.sum()))
print(c[["Constraint Name","Monitored Facility","hours","psi","t","identified"]].to_string(index=False,max_colwidth=42))
for g in ("oklahoma_internal","sps_tie","other"):
    x=res[res.group.eq(g)]; print(f"\n{g}: n={len(x)} psi>0&t>=2: {int(((x.psi>0)&(x.t>=2)).sum())} psi<0&t<=-2: {int(((x.psi<0)&(x.t<=-2)).sum())} mean psi={x.psi.mean():.4f}")
# back-of-envelope aggregate: spread on corridor total |SP| alone
corr_cols=[c_ for c_ in cols if c_ in set(M[M.group.eq("n_s_corridor")]["Constraint Name"])]
Xa=np.column_stack([np.ones(len(D)),D[corr_cols].sum(axis=1).values]); ba=np.linalg.lstsq(Xa,yv,rcond=None)[0]
print(f"\naggregate single-regressor psi_corridor = {ba[1]:.4f} (intercept {ba[0]:.2f}); hours-weighted mean psi over identified corridor = {np.average(c[c.identified].psi,weights=c[c.identified].hours) if c.identified.any() else float('nan'):.4f}")
# sensitivity: BINDING-only vs including BREACHED is a later check; here: drop 2023 / 2024 / 2025 leave-one-year-out for the identified set
for yr in (2023,2024,2025):
    m=D.index.get_level_values("year")!=yr; Xl=X[m]; yl=yv[m]; bl=np.linalg.pinv(Xl.T@Xl)@Xl.T@yl
    sub=pd.Series(bl[1:],index=cols); print(f"LOYO drop {yr}: identified-corridor psi hours-weighted mean = {np.average(sub[c[c.identified]['Constraint Name']],weights=c[c.identified].hours):.4f}")
