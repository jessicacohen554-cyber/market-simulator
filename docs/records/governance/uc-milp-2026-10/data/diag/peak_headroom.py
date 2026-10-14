# UC-DIAG zero-LP reading (FINDING-ucmilp-diag-undercommit-2026-10-14). Usage: python <script> <bundle_dir> [<arm_dir>] <year>
import pandas as pd, numpy as np, sys
base, yr = sys.argv[1], sys.argv[2]
s=pd.read_parquet(f'{base}/hourly/system_{yr}.parquet'); s=s[s['pass']=='P1']
dem=s.groupby('hour').demand.sum()
pk=set(dem.sort_values().index[-100:])        # top-100 load hours
u=pd.read_parquet(f'{base}/hourly/uc_schedule_{yr}.parquet'); u=u[u.hour.isin(pk)]
um=pd.read_parquet(f'{base}/hourly/unit_marginal_{yr}.parquet',columns=['unit_id','plant_code','plant_group','hour','mw','cap_mw']); um=um[um.hour.isin(pk)]
cls=u[['plant_code','uc_class']].drop_duplicates()
g=um.plant_group.str.upper()
um['k']=np.select([g.str.startswith('CC'),g.str.startswith('COAL'),g.str.startswith('ST_GAS'),g.str.startswith('CT'),g.str.startswith('ST_OIL')|g.str.startswith('IC')],['cc','coal','st_gas','ct','other_peak'],'other')
m=um.merge(cls,on='plant_code',how='left')
m['integer']=m.uc_class==m.k
out={}
for k in ['cc','st_gas','coal','ct']:
    x=m[m.k==k]
    hi=x[x.integer].groupby('hour')[['cap_mw','mw']].sum(); lo=x[~x.integer].groupby('hour')[['cap_mw','mw']].sum()
    out[k]=dict(int_cap=hi.cap_mw.mean() if len(hi) else 0, int_disp=hi.mw.mean() if len(hi) else 0,
                int_head=(hi.cap_mw-hi.mw).mean() if len(hi) else 0,
                cont_cap=lo.cap_mw.mean() if len(lo) else 0, cont_head=(lo.cap_mw-lo.mw).mean() if len(lo) else 0)
print(base.split('/')[-1], yr, 'top-100 load h, mean demand', round(dem[list(pk)].mean()))
print(pd.DataFrame(out).T.round(0).to_string())
sched_cap=u.assign(full=lambda d:np.where(d.u>0,d.online_mw/d.u.clip(lower=1)*d.n,np.nan)).groupby(['uc_class','hour']).online_mw.sum().groupby('uc_class').mean()
print('uc_schedule online_mw', sched_cap.round(0).to_dict())
