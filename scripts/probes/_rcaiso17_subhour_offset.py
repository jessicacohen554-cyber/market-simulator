"""R-CAISO-17 phase 0 (zero LP): sub-hour offset of the 2019-2021 CISO EIA-930 cells.

For each offset tau (5-min steps) correlates the differenced EIA-930 hour-ENDING
value stamped s with the mean of CAISO Outlook 5-minute samples over the hour
window ending at s + tau (Outlook wall clock converted to UTC independently).
tau = 0 is the true clock; tau = +60 is a clean one-hour-early stamp.
Measured: NG: SUN / NG: NG / NG: WND peak at tau = +45 min; -Total interchange
peaks at tau = 0 (docs/handoffs/r-caiso-17/PRECOMMIT-r-caiso-17-2026-09-30.md).
"""
import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parent))
import _rcaiso17_pre2022_clock_scan as m, pandas as pd, numpy as np
e=pd.read_parquet(m.RAW/'eia-930-hourly'/'CISO hourly.parquet')
u=pd.DatetimeIndex(e['UTC time']); u=u.tz_convert('UTC').tz_localize(None) if u.tz is not None else u
E=pd.DataFrame({k:pd.to_numeric(e[v],errors='coerce').to_numpy() for k,v in {'SUN':'NG: SUN','GAS':'NG: NG','WND':'NG: WND','IMP':'Total interchange','D':'Demand'}.items()},index=u)  # index = hour-ENDING stamp
E['IMP']=-E['IMP']; E=E[~E.index.duplicated()]; E.index=E.index.astype("datetime64[ns]")
for yr in (2019,2021):
    o=pd.read_csv(m.RAW/'caiso-outlook-fuelsource'/f'fuelsource_{yr}.csv.gz')
    w=pd.to_datetime(o['date']+' '+o['time'],errors='coerce'); o=o.assign(w=w).dropna(subset=['w'])
    loc=pd.DatetimeIndex(o.w).tz_localize('US/Pacific',ambiguous='NaT',nonexistent='NaT')
    o['u']=loc.tz_convert('UTC').tz_localize(None); o=o.dropna(subset=['u']).set_index('u')
    o=o[~o.index.duplicated()]
    f=o[['solar','natural_gas','wind','imports']].apply(pd.to_numeric,errors='coerce').asfreq('5min')
    roll=f.rolling(12,min_periods=10).mean(); roll.index=roll.index.astype("datetime64[ns]")   # value at time T = mean over (T-55min .. T) samples
    res={}
    for tau in range(-24,25,3):   # 5-min steps: window end offset relative to EIA hour-ending stamp s
        # window of 12 samples ending at s + tau*5min (stamp T covers samples T-55..T)
        r=roll.shift(-tau)  # r at T = roll at T+tau*5
        rr=r.reindex(E.index - pd.Timedelta(minutes=5)); rr.index=E.index
        row={}
        for a,b in (('SUN','solar'),('GAS','natural_gas'),('WND','wind'),('IMP','imports')):
            j=pd.concat([E[a],rr[b]],axis=1).dropna(); j=j[(j.index.year==yr)].diff().dropna()
            row[a]=round(j.iloc[:,0].corr(j.iloc[:,1]),3)
        res[tau*5]=row
    print(yr); print(pd.DataFrame(res).T.to_string())
