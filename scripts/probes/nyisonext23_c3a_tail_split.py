"""NYISO-NEXT-23 phase 0 (ZERO LP): zone-resolved C3a miss split by zone, actual-RT decile, hour band, month, >$150/>$300 hours; reads keeper hourly sidecars + actual_lmp_hourly_zonal_NYISO.parquet (NEXT-22 basis)."""
import pandas as pd, numpy as np
A=pd.read_parquet('data/raw/_validation-source/actual_lmp_hourly_zonal_NYISO.parquet')
for y in [2021,2022,2023,2024,2025]:
    b='nyisonext21_2021' if y==2021 else 'nyisonext21_span'
    s=pd.read_parquet(f'results/calibration/{b}/hourly/system_{y}.parquet'); s=s[s['pass']=='P1']
    a=A[A.year==y]
    m=s.merge(a,on=['zone','hour'])
    D=m.demand.sum(); m['w']=m.demand/D
    m['miss']=(m.price-m.rt)*m.w
    m['dec']=m.groupby('zone').rt.transform(lambda x: pd.qcut(x.rank(method='first'),10,labels=False)+1)
    m['band']=pd.cut(m.hour%24,[-1,5,11,17,23],labels=['night','morn','aft','eve'])
    mod=(m.price*m.w).sum(); act=(m.rt*m.w).sum()
    print(f'\n=== {y}  model {mod:.2f} actual {act:.2f} miss {mod-act:+.2f} ({(mod/act-1)*100:+.1f}%)')
    print(' by zone:', m.groupby('zone').miss.sum().round(2).to_dict())
    print(' by decile:', m.groupby('dec').miss.sum().round(2).to_dict())
    print(' by band:', m.groupby('band',observed=True).miss.sum().round(2).to_dict())
    # tail capped: model with actual clipped at 300, and decile-10 replaced
    t=m[m.dec==10]; print(' dec10 mean model/act by zone:', t.groupby('zone').apply(lambda g: f'{g.price.mean():.0f}/{g.rt.mean():.0f}',include_groups=False).to_dict())
    print(' miss from act>300 hours:', round(m.loc[m.rt>300,'miss'].sum(),2), ' n=',int((m.rt>300).sum()))
    print(' miss from act>150:', round(m.loc[m.rt>150,'miss'].sum(),2))
    print(' median-hour bias by zone (model-act median):', m.groupby('zone').apply(lambda g:(g.price-g.rt).median(),include_groups=False).round(2).to_dict())
    if y==2025:
        ds=m[m.zone.isin(['NYC','Long_Island','Lower_Hudson'])]
        print(' downstate band x decile miss:\n', ds.pivot_table(index='band',columns='dec',values='miss',aggfunc='sum',observed=True).round(2))
        m['mon']=(m.hour//24)//30.42
        print(' month miss:', m.groupby(m.mon.astype(int)).miss.sum().round(2).to_dict())
