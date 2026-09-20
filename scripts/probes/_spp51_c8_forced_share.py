"""C8 risk: D-2-style forced share (energy at a BINDING floor), not floor capacity."""
import sys; sys.path.insert(0,'src')
import numpy as np, pandas as pd
BUN={y:'results/calibration/spp42_span_a' for y in (2023,2024,2025)}
BUN.update({y:'results/calibration/spp49_benchmembership_span' for y in (2019,2020,2021,2022)})
tr=pd.read_csv('data/raw/_processed-legacy/thermal_tranches_SPP.csv')
co=tr[(tr.plant_group=='COAL')&(tr.status=='ok')].copy(); co['f']=co.nameplate_mw*co.mustrun_online_pct/100.
rows=[]
for y in sorted(BUN):
    s=pd.read_parquet(f'{BUN[y]}/hourly/system_{y}.parquet'); s=s[s['pass']=='P1']
    load=s.groupby('hour')['demand'].sum().to_numpy(); tot=load.sum()
    ch=pd.read_parquet(f'{BUN[y]}/hourly/class_hourly_{y}.parquet'); ch=ch[ch['pass']=='P1']
    coal=ch[ch.klass.isin(['COAL_PRB','COAL_LIGNITE'])].groupby('hour')['mw'].sum().reindex(range(8760),fill_value=0.).to_numpy()
    rank=load.argsort().argsort()/8759.
    F=np.zeros(8760)
    for r in co.itertuples():
        k=int(round(r.online_frac*8760)); F[rank>=(1.-k/8760.)]+=r.f
    binding = F>coal
    forced=F[binding].sum(); newcoal=coal.sum()+np.maximum(0.,F-coal).sum()
    rows.append(dict(year=y, h_bind=int(binding.sum()),
        forced_TWh=forced/1e6, coal_after_TWh=newcoal/1e6,
        forced_share=forced/newcoal,
        cap_upper_bound=F.sum()/newcoal,
        coal_share_of_load=newcoal/tot))
r=pd.DataFrame(rows); pd.set_option('display.width',200)
print("=== C8 RISK: D-2-style forced share = energy at a BINDING floor / class energy ===")
print("   rule 20 cap for a material merchant class = 30 %")
print(r.to_string(index=False,float_format=lambda v:f'{v:9.4f}'))
