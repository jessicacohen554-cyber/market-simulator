# UC-DIAG zero-LP reading (FINDING-ucmilp-diag-undercommit-2026-10-14). Usage: python <script> <bundle_dir> [<arm_dir>] <year>
import json, pandas as pd, numpy as np, sys
arm, yr = sys.argv[1], sys.argv[2]
cl=pd.DataFrame(json.load(open(f'{arm}/uc_solve_log_{yr}.json'))['clusters'])
cl['cap']=cl.pbar_mw*cl.n; cl=cl[cl.integer]
s=pd.read_parquet(f'{arm}/hourly/system_{yr}.parquet'); s=s[s['pass']=='P1']
dem=s.groupby('hour').demand.sum(); pk=dem.sort_values().index[-100:]
u=pd.read_parquet(f'{arm}/hourly/uc_schedule_{yr}.parquet',columns=['hour','cluster','u','n'])
up=u[u.hour.isin(pk)].groupby('cluster').apply(lambda d:(d.n-d.u).mean()).rename('off_units')
cl=cl.merge(up,left_on='cluster',right_index=True,how='left')
cl['off_mw']=cl.off_units*cl.pbar_mw
cl['utbin']=pd.cut(cl.ut_h,[0,8,24,72,1e9],labels=['<=8h','9-24h','25-72h','>72h'])
print(arm.split('/')[-1],yr)
for k in ['cc','st_gas','coal']:
    x=cl[cl.uc_class==k]
    if x.empty: continue
    t=x.groupby('utbin',observed=False).agg(cap_mw=('cap','sum'),off_at_peak_mw=('off_mw','sum'),n_cl=('cluster','count'))
    t['off_share']=t.off_at_peak_mw/t.cap_mw
    print(k,'cap-weighted median ut_h', np.round(np.interp(0.5,(x.sort_values('ut_h').cap.cumsum()/x.cap.sum()).values,x.sort_values('ut_h').ut_h.values),0),'src',x.src.apply(lambda s:s['ut_dt']).value_counts().to_dict())
    print(t.round(2).to_string())
