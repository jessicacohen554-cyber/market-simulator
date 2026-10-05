import pandas as pd, numpy as np, glob
def dl(a,b,shifts=range(-10,11)):
    idx=pd.date_range(max(a.index.min(),b.index.min()),min(a.index.max(),b.index.max()),freq='h')
    a=a.reindex(idx).diff(); b=b.reindex(idx).diff()
    return {s: a.corr(b.shift(-s)) for s in shifts}
def best(L): return max(L,key=lambda k:-9 if np.isnan(L[k]) else abs(L[k]))
for f in sorted(glob.glob('data/raw/eia-930-interchange/*.parquet')):
    ba=f.split('/')[-1].split(' ')[0]
    d=pd.read_parquet(f); d=d[d.mw.abs()<1e5]
    h=pd.read_parquet(f'data/raw/eia-930-hourly/{ba} hourly.parquet')
    hu=h.set_index('UTC time')['Total interchange'].groupby(level=0).first()
    off=(h['UTC time']-h['Local time']).dt.total_seconds().div(3600).value_counts().to_dict()
    out=[]
    for yr in sorted(set(d.local_time.dt.year)):
        if yr<2019 or yr>2025: continue
        s=d[d.local_time.dt.year==yr].groupby('local_time').mw.sum(min_count=1)
        r=[]
        for nm,mo in [('W',[1,2,12]),('S',[6,7,8])]:
            ss=s[s.index.month.isin(mo)]
            L=dl(ss,hu[hu.index.year==yr]); b=best(L); r.append(f"{nm}{b:+d}({L[b]:.2f})")
        out.append(f"{yr}:"+'/'.join(r))
    print(ba, 'BAhourly UTC-local offsets',{int(k):v for k,v in off.items()}, ' '.join(out))
