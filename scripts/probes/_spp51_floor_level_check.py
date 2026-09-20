"""Does the measured floor reproduce the REAL fleet's observed minimum?"""
import sys; sys.path.insert(0,'src')
import numpy as np, pandas as pd
BUN={y:'results/calibration/spp42_span_a' for y in (2023,2024,2025)}
BUN.update({y:'results/calibration/spp49_benchmembership_span' for y in (2019,2020,2021,2022)})
tr=pd.read_csv('data/raw/_processed-legacy/thermal_tranches_SPP.csv')
co=tr[(tr.plant_group=='COAL')&(tr.status=='ok')].copy()
co['f']=co.nameplate_mw*co.mustrun_online_pct/100.0
rows=[]
for y in sorted(BUN):
    s=pd.read_parquet(f'{BUN[y]}/hourly/system_{y}.parquet'); s=s[s['pass']=='P1']
    load=s.groupby('hour')['demand'].sum().to_numpy()
    ch=pd.read_parquet(f'{BUN[y]}/hourly/class_hourly_{y}.parquet'); ch=ch[ch['pass']=='P1']
    coal=ch[ch.klass.isin(['COAL_PRB','COAL_LIGNITE'])].groupby('hour')['mw'].sum().reindex(range(8760),fill_value=0.).to_numpy()
    rank=load.argsort().argsort()/8759.0
    F=np.zeros(8760)
    for r in co.itertuples():
        k=int(round(r.online_frac*8760)); F[rank>=(1.0-k/8760.0)]+=r.f
    lo=rank<0.10   # lowest-load decile
    rows.append(dict(year=y,
        floor_all_GW=co.f.sum()/1e3,
        F_lodecile_GW=F[lo].mean()/1e3, F_min_GW=F.min()/1e3,
        model_coal_lodecile_GW=coal[lo].mean()/1e3, model_coal_min_GW=coal.min()/1e3,
        model_coal_max_GW=coal.max()/1e3,
        floor_over_modelmax=F[lo].mean()/coal.max()))
r=pd.DataFrame(rows); pd.set_option('display.width',210)
print("=== FLOOR LEVEL vs the model's own coal, lowest-load decile ===")
print("  real SPP PRB fleet never falls below 8.1-17.5% of its own annual max (census leg B)")
print(r.to_string(index=False,float_format=lambda v:f'{v:9.3f}'))
