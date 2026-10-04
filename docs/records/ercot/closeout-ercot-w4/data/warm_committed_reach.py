"""closeout-ERCOT-w4 phase 0: static reach of the coal warm-boiler exemption (zero LP).

Usage: python docs/records/ercot/closeout-ercot-w4/data/warm_committed_reach.py 2019 2020 ...
"""
import sys,numpy as np,pathlib,pandas as pd
sys.path.insert(0,'.'); sys.path.insert(0,'src')
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet
B=pathlib.Path('results/calibration/closeout_ercot_w3_span')  # composed w3 span: keeper recipe + cliff split
for y in map(int,sys.argv[1:]):
    st,_=reconstruct_bundle_fleet(B,y,verbose=False)
    base={gen.unit_id:float(np.mean(st['mc_base'][g])) for g,gen in enumerate(st['fleet']) if gen.fuel_type=='coal' and gen.unit_id.endswith('_committed')}
    u=pd.read_parquet(f'results/calibration/closeout_ercot_w3_span/hourly/unit_marginal_{y}.parquet',columns=['plant_code','unit_id','zone','hour','mw','cap_mw','mc'])
    u=u[u.unit_id.isin(base)]
    s=pd.read_parquet(f'results/calibration/closeout_ercot_w3_span/hourly/system_{y}.parquet',columns=['zone','hour','price'])
    u=u.merge(s,on=['zone','hour'])
    u['base']=u.unit_id.map(base)
    add=np.where((u.price>u.base)&(u.price<=u.mc),u.cap_mw-u.mw,0.0)
    u['add']=add
    g=u.groupby('plant_code').agg(cap=('cap_mw','max'),base=('base','first'),p1_med=('mc','median'),twh=('mw',lambda x:x.sum()/1e6),add_twh=('add',lambda x:x.sum()/1e6))
    print(f'== {y}: static added committed coal TWh (upper bound, prices held) = {g.add_twh.sum():.2f}')
    print(g.round(2).to_string())
    mr={gen.unit_id:getattr(gen,'must_run_pct',None) for gen in st['fleet'] if gen.fuel_type=='coal' and gen.unit_id.endswith('_committed')}
    print('committed must_run_pct:',{k.split('_p')[-1]:v for k,v in mr.items()})
