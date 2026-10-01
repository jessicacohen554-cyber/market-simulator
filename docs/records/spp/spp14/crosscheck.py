"""SPP-14 cross-check gate (rule 14): the per-hub series rebuilt live from SPP's own
portal, folded to the system hub as the NaN-skipping mean of SPPNORTH_HUB and
SPPSOUTH_HUB on the model's 8760 local calendar, against the COMMITTED
actual_lmp_hourly_SPP.parquet. Gate: annual RT mean within 1 % AND hourly
correlation >= 0.999 for each of 2023-2025. Also: byte-identity of a straight
rebuild of the system parquet, and mean / p90 |N - S| per year (P7)."""
import json, hashlib, numpy as np, pandas as pd
S="/tmp/claude-0/-home-user-market-simulator/1865f405-6252-5de2-847a-c8d1ca7ab210/scratchpad"
com=pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
reb=pd.read_parquet(f"{S}/spp/actual_lmp_hourly_SPP_rebuilt.parquet")
z=pd.read_parquet(f"{S}/spp/actual_lmp_hourly_zonal_SPP.parquet")
out={"byte_identity":{}, "gate":{}, "spread":{}}
h=lambda p: hashlib.sha256(open(p,"rb").read()).hexdigest()
out["byte_identity"]["committed_sha256"]=h("data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
out["byte_identity"]["rebuilt_sha256"]=h(f"{S}/spp/actual_lmp_hourly_SPP_rebuilt.parquet")
out["byte_identity"]["frames_equal"]=bool(com.equals(reb))
out["byte_identity"]["max_abs_diff_rt"]=float(np.nanmax(np.abs(com.rt.values-reb.rt.values))); out["byte_identity"]["max_abs_diff_da"]=float(np.nanmax(np.abs(com.da.values-reb.da.values)))
out["byte_identity"]["nan_pattern_equal"]=bool((com.rt.isna().values==reb.rt.isna().values).all() and (com.da.isna().values==reb.da.isna().values).all())
p=z.pivot_table(index=["year","hour"],columns="zone",values=["rt","da"])
allpass=True
for y in (2023,2024,2025):
    c=com[com.year==y].set_index("hour"); n=p.loc[y]
    for mkt in ("rt","da"):
        fold=n[(mkt,"SPPNORTH_HUB")].to_frame("n").join(n[(mkt,"SPPSOUTH_HUB")].to_frame("s")).mean(axis=1,skipna=True)  # NaN-skipping mean
        a=c[mkt].reindex(fold.index); m=~(a.isna()|fold.isna())
        mean_c=float(a.mean()); mean_f=float(fold.mean()); rel=abs(mean_f-mean_c)/abs(mean_c); corr=float(np.corrcoef(a[m],fold[m])[0,1]); maxd=float((a[m]-fold[m]).abs().max())
        ok=(rel<=0.01) and (corr>=0.999)
        out["gate"][f"{y}_{mkt}"]={"committed_mean":round(mean_c,4),"rebuilt_fold_mean":round(mean_f,4),"rel_diff":rel,"hourly_corr":corr,"max_abs_diff":maxd,"n_compared":int(m.sum()),"nan_committed":int(a.isna().sum()),"nan_fold":int(fold.isna().sum()),"PASS":bool(ok)}
        if mkt=="rt": allpass&=ok
    for mkt in ("rt","da"):
        d=(n[(mkt,"SPPNORTH_HUB")]-n[(mkt,"SPPSOUTH_HUB")]).dropna(); ad=d.abs()
        out["spread"][f"{y}_{mkt}"]={"n_hours":int(len(d)),"mean_S_minus_N":round(float(-d.mean()),3),"mean_abs":round(float(ad.mean()),3),"p50_abs":round(float(ad.quantile(0.5)),3),"p90_abs":round(float(ad.quantile(0.9)),3),"p99_abs":round(float(ad.quantile(0.99)),3),"max_abs":round(float(ad.max()),3),"frac_hours_N_above_S":round(float((d>0).mean()),4),"north_mean":round(float(n[(mkt,"SPPNORTH_HUB")].mean()),3),"south_mean":round(float(n[(mkt,"SPPSOUTH_HUB")].mean()),3)}
out["gate"]["ALL_RT_YEARS_PASS"]=bool(allpass)
out["zonal_rows"]=int(len(z)); out["zonal_zones"]=sorted(z.zone.unique().tolist()); out["zonal_sha256"]=h(f"{S}/spp/actual_lmp_hourly_zonal_SPP.parquet")
json.dump(out,open(f"{S}/spp/crosscheck.json","w"),indent=2); print(json.dumps(out,indent=1))
