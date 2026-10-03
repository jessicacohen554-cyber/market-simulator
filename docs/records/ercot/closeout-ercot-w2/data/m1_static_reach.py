"""Zero-LP static reach of the ERCOT vintage-membership supplement on C3a/C3b.

Per year, fit price as a monotone (PAVA) function of total reserve shortfall over
Jun-Sep keeper hours, shift each shortfall hour's shortfall down by eff*ADD MW
(added summer capability; Decker ST1/ST2 by their EIA-860 retirement months,
DeCordova CT1-4 all years) and shift its price by the fitted delta. Non-shortfall
hours unchanged (the units sit above the CC stack; merit effect ignored).
"""
import pandas as pd, numpy as np, json, gzip, re, base64, math
B='results/calibration/closeout_ercot_l1_span/hourly/'
def pava_inc(x,y):
    o=np.argsort(x);x=x[o];y=y[o].astype(float);vals=[];w=[];st=[]
    for i,v in enumerate(y):
        vals.append(v);w.append(1.);st.append(i)
        while len(vals)>1 and vals[-2]>vals[-1]:
            nv=(vals[-2]*w[-2]+vals[-1]*w[-1])/(w[-2]+w[-1]);nw=w[-2]+w[-1];vals.pop();w.pop();st.pop();vals[-1]=nv;w[-1]=nw
    f=np.empty(len(y));b=st+[len(y)]
    for k in range(len(vals)):f[b[k]:b[k+1]]=vals[k]
    return x,f
def add_mw(y,mo):
    a=280  # DeCordova CT1-4 summer
    if (y,mo)<(2020,10): a+=320
    if (y,mo)<(2022,3): a+=404
    return a
s_=open('frontend/data/backcast/runs/2026-10-02-closeout-l1-coal-fuel.js').read()
run=json.loads(gzip.decompress(base64.b64decode(re.search(r'="([^"]+)"',s_).group(1))))
out={}
for y in range(2019,2026):
    r=pd.read_parquet(B+f'reserve_family_{y}.parquet');sf=r.groupby('hour').shortfall_mw.sum()
    s=pd.read_parquet(B+f'system_{y}.parquet')
    p=s.groupby('hour').apply(lambda d:(d.price*d.demand).sum()/d.demand.sum());D=s.groupby('hour').demand.sum()
    mo=(pd.Timestamp(f'{y}-01-01')+pd.to_timedelta(p.index,'h')).month
    df=pd.DataFrame({'p':p,'sf':sf,'D':D,'mo':mo}).fillna(0)
    sm=df[df.mo.isin([6,7,8,9])]; x,f=pava_inc(sm.sf.values,sm.p.values)
    act=json.load(gzip.open(f'frontend/data/backcast/bench/ERCOT/{y}.json.gz'))['bench']['avgLMP']
    am=act['rt_lw_mon']; arl=act['rt_lw']
    lmp=run['years'][str(y)]['lmp']
    mm=[sum(z['pMon'][k]*z['dMon'][k] for z in lmp.values())/sum(z['dMon'][k] for z in lmp.values()) for k in range(12)]
    dm=[sum(z['dMon'][k] for z in lmp.values()) for k in range(12)]
    res={}
    for eff in (0.5,0.9):
        cm=[]
        for k in range(12):
            d=df[df.mo==k+1]
            sh=np.clip(d.sf-add_mw(y,k+1)*eff,0,None)
            delta=np.where(d.sf>0,np.interp(sh,x,f)-np.interp(d.sf,x,f),0)
            lw=lambda v:(v*d.D).sum()/d.D.sum()
            cm.append(mm[k]+lw(delta))
        nr=lambda m:math.sqrt(sum((a-b)**2 for a,b in zip(m,am))/12)/(sum(am)/12)
        ann=lambda m:sum(a*w for a,w in zip(m,dm))/sum(dm)
        res[eff]=dict(c3b=round(nr(cm),3),c3a=round(ann(cm)/arl-1,3))
    res['keeper']=dict(c3b=round(math.sqrt(sum((a-b)**2 for a,b in zip(mm,am))/12)/(sum(am)/12),3),c3a=round(sum(a*w for a,w in zip(mm,dm))/sum(dm)/arl-1,3))
    out[y]=res; print(y,res)
json.dump(out,open('docs/records/ercot/closeout-ercot-w2/data/m1_static_reach.json','w'),indent=1)
