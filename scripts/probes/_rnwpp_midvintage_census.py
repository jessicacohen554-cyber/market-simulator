"""R-NWPP phase 0: fleet footprint of mid_vintage_exit_carry on the R-NWPP arm, 2019-2024. ZERO LP.

Writes results/calibration/_rnwpp_midvintage_census.json (per year: thermal plants whose
available TWh moves when the flag is added to the arm recipe of _rnwpp_census.py).
Usage: PYTHONPATH=.:src python3 scripts/probes/_rnwpp_midvintage_census.py
"""
import sys, json
sys.path.insert(0,'.')
from scripts.probes import _rnwpp_census as c
out = {}
for y in [2019,2020,2021,2022,2023,2024]:
    base={**c.F1_FLAGS_ARM, **c.OUTAGE_ARM}
    a=c._frame(c._build(y, base)); b=c._frame(c._build(y, {**base,'mid_vintage_exit_carry':True}))
    th=('coal','gas_cc','gas_ct','gas_st','oil')
    pa=a[a.fuel.isin(th)].groupby(['plant','name']).agg(mw=('pmax','sum'),twh=('avail_twh','sum'))
    pb=b[b.fuel.isin(th)].groupby(['plant','name']).agg(mw=('pmax','sum'),twh=('avail_twh','sum'))
    m=pa.join(pb,how='outer',lsuffix='_off',rsuffix='_on').fillna(0); m['d']=m.twh_on-m.twh_off
    mv=m[m.d.abs()>0.001].round(3).reset_index()
    out[y]=mv.to_dict('records')
    print(y,'units',len(a),'->',len(b),'| moves:',[(r['plant'],r['name'][:16],r['mw_on'],r['twh_off'],r['twh_on']) for r in out[y]])
json.dump(out,open('results/calibration/_rnwpp_midvintage_census.json','w'),indent=1,default=str)
