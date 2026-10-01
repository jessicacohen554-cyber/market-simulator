"""NYISO-NEXT-23 phase 0 (ZERO LP): Transco Z6 NY daily factor, current trade-date/interpolated vs flow-date staircase, and its daily correlation with NYC DA (diagnostic only; rule 14 convention is the case)."""
import sys; sys.path.insert(0,'src')
import numpy as np,pandas as pd
from market_sim.data.fuel import hubs
from market_sim.data.fuel._shared import _DAYS_IN_MONTH
dated=hubs._transco_z6_daily_dated(hubs.TRANSCO_Z6_NY_DAILY_PATH)
A=pd.read_parquet('data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet')
def cur(y):  # current: trade-date, linear interp, month-mean-preserved factor
    out=[]
    for m in range(12):
        d=dated.get(y,{}).get(m+1,{}); n=_DAYS_IN_MONTH[m]
        if not d: out+= [1.0]*n; continue
        days=np.array(sorted(d),float); v=np.array([d[int(x)] for x in days])
        f=np.interp(np.arange(n),days-1,v/v.mean()); out+=list(f/f.mean())
    return np.array(out)
def flow(y):
    s=hubs._flow_date_staircase(dated.get(y,{}),y,prior_year_dated=dated.get(y-1))
    out=[];i=0
    for m in range(12):
        n=_DAYS_IN_MONTH[m]; seg=s[i:i+n]; out+=list(seg/seg.mean()); i+=n
    return np.array(out)
for y in range(2021,2026):
    c,f=cur(y),flow(y)
    a=A[(A.year==y)&(A.zone=='NYC')].sort_values('hour'); da=a.da.values[:8760].reshape(365,24).mean(1)
    big=np.abs(f-c)>0.25
    print(f'{y}: days |Δfactor|>0.25: {big.sum():3d}; corr(factor,NYC DA daily) current {np.corrcoef(c,da)[0,1]:.3f} flow {np.corrcoef(f,da)[0,1]:.3f}; winter(J,F,D) current {np.corrcoef(c[np.r_[0:59,334:365]],da[np.r_[0:59,334:365]])[0,1]:.3f} flow {np.corrcoef(f[np.r_[0:59,334:365]],da[np.r_[0:59,334:365]])[0,1]:.3f}')
y=2025; c,f=cur(y),flow(y); a=A[(A.year==y)&(A.zone=='NYC')].sort_values('hour'); da=a.da.values[:8760].reshape(365,24).mean(1)
print(pd.DataFrame({'date':pd.date_range('2025-01-14',periods=11).date,'cur':c[13:24].round(2),'flow':f[13:24].round(2),'NYC_DA':da[13:24].round(0)}).to_string(index=False))
