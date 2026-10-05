import pandas as pd, numpy as np
d=pd.read_parquet('data/raw/eia-930-interchange/PJM interchange hourly.parquet')
SEAM={'MISO':'MISO','NYIS':'NY','CPLE':'South','CPLW':'South','DUK':'South','TVA':'South','LGEE':'South'}
# current consumer convention: label = EPT hour-ending -> hour-beginning = label-1h
cur=d.local_time-pd.Timedelta(hours=1)
# corrected: label = UTC hour-beginning -> UTC hour-ending = label+1h -> EST hour-beginning = label+1-5-1 = label-5h
cor=d.local_time-pd.Timedelta(hours=5)
def table(t,yr,seam=None):
    m=(t.dt.year==yr)&~((t.dt.month==2)&(t.dt.day==29))
    x=d[m].assign(ts=t[m].values,seam=d[m].diba.astype(str).map(SEAM))
    if seam: x=x[x.seam==seam]
    per=-x.groupby('ts').mw.sum(min_count=1).dropna()
    per=per.groupby(level=0).first()
    df=pd.DataFrame({'v':per.values,'m':per.index.month,'h':per.index.hour})
    tab=df.groupby(['m','h']).v.quantile(0.9).unstack().reindex(index=range(1,13),columns=range(24))
    mean=df.groupby(['m','h']).v.mean().unstack().reindex(index=range(1,13),columns=range(24))
    return tab,mean,per.sum()/1e6
dpm=np.array([31,28,31,30,31,30,31,31,30,31,30,31])
for yr in range(2019,2026):
    out=[]
    for seam in [None,'MISO','NY','South']:
        a,am,ta=table(cur,yr,seam); b,bm,tb=table(cor,yr,seam)
        dd=(a-b).abs(); ddm=(am-bm).abs()
        sumabs=(dd.values*dpm[:,None]).sum()/1e6  # TWh-equivalent over a year of hours
        out.append(f"{seam or 'ALL'}: p90 Σ|Δ|={sumabs:.2f}TWh max={dd.values.max():.0f}MW meanΣ|Δ|={(ddm.values*dpm[:,None]).sum()/1e6:.2f}TWh annualΔ={tb-ta:+.3f}TWh")
    print(yr,' | '.join(out))
