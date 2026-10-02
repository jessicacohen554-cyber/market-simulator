"""closeout-NEISO wave 1: zero-LP reconciliation of the ISO Express hourly ROS reserve requirement against the Morning Report daily requirement (2019-2025)."""
import glob
import pandas as pd
rows=[]
for f in sorted(glob.glob('data/raw/NEISO-AS/requirements/requirements_*.csv')):
    for line in open(f):
        p=line.strip().split(',')
        if p[0]=='D' and p[3]=='7000':
            rows.append((p[1],p[2].rstrip('X'),float(p[4]),float(p[5]),float(p[6])))
h=pd.DataFrame(rows,columns=['date','he','tmsr','tmr','tot']).drop_duplicates()
h['he']=h.he.astype(int)
mr=pd.concat([pd.read_csv(f) for f in sorted(glob.glob('data/raw/neiso-operable-capacity/neiso_operable_capacity_20*.csv'))])
# morning report on date D reports peak-hour of D (forecast)
m=mr[['report_date','total_operating_reserve_req_mw','largest_first_contingency_mw','replacement_reserve_req_mw']].rename(columns={'report_date':'date'})
# hourly daily max/median
g=h[h.tmr>0].groupby('date').agg(tmr_med=('tmr','median'),tot_med=('tot','median'),tot_max=('tot','max'),tmr_max=('tmr','max'),tmsr_med=('tmsr','median'))
j=m.merge(g,left_on='date',right_index=True)
j['yr']=j.date.str[:4]
j['r_tot']=j.total_operating_reserve_req_mw/j.tot_max
j['r_tmr']=j.largest_first_contingency_mw/j.tmr_max
j['spin_frac']=j.tmsr_med/j.tmr_med
print(j.groupby('yr')[['r_tot','r_tmr','spin_frac']].describe().T.round(3).to_string())
# implied relationship TOT ~ TMR + 0.5*second? tot-tmr
h2=h[h.tmr>0]; h2=h2.assign(yr=h2.date.str[:4], d30=h2.tot-h2.tmr, sf=h2.tmsr/h2.tmr)
print(h2.groupby('yr')[['tmsr','tmr','tot','d30','sf']].mean().round(1))
# Elliott Dec 24 2022
print(h[h.date=='2022-12-24'][['he','tmsr','tmr','tot']].iloc[[0,12,17]])
