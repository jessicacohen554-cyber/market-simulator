import pandas as pd, numpy as np, json, pyarrow.parquet as pq, pyarrow.compute as pc
C='results/calibration/closeout_caiso_w1_a2_span/hourly'; A='results/calibration/ucmilp15_caiso_span/hourly'; U='results/calibration/ucmilp3_caiso_span/hourly'
CZ=['NP15','ZP26','SP15_rest','LA_BASIN','SDGE']
def price(d,y):
    s=pd.read_parquet(f'{d}/system_{y}.parquet'); s=s[(s['pass']=='P1')&s.zone.isin(CZ)]
    g=s.assign(pd_=s.price*s.demand).groupby('hour')[['pd_','demand']].sum(); return (g.pd_/g.demand).to_numpy()
def klass(d,y):
    k=pd.read_parquet(f'{d}/class_hourly_{y}.parquet'); k=k[k['pass']=='P1']; return k.groupby('klass').mw.sum()/1e6
def marg(d,y,mask):
    t=pq.read_table(f'{d}/unit_marginal_{y}.parquet',columns=['pass','plant_group','zone','hour','marginal'])
    t=t.filter(pc.equal(t['marginal'],1)); m=t.to_pandas(); m=m[m.zone.isin(CZ)]
    m=m[m.hour.isin(np.where(mask)[0])]
    return (m.plant_group.astype(str).value_counts(normalize=True)*100).round(1).head(6).to_dict()
out={}
for y in range(2019,2026):
    pc_,pa=price(C,y),price(A,y); pu=price(U,y)
    hod=np.arange(len(pc_))%24
    terc=pd.qcut(pc_,3,labels=['low','mid','high'])
    r={'mean':[round(pc_.mean(),2),round(pu.mean(),2),round(pa.mean(),2)]}
    for t in ['low','mid','high']:
        m=np.asarray(terc==t); r['terc_'+t]=round(float((pa-pc_)[m].mean()),2)
    for nm,hs in [('night0-6',range(0,7)),('morn7-9',range(7,10)),('solar10-16',range(10,17)),('eve17-21',range(17,22)),('late22-23',range(22,24))]:
        m=np.isin(hod,list(hs)); r['hod_'+nm]=round(float((pa-pc_)[m].mean()),2)
    r['n_le15']=[int((pc_<=15).sum()),int((pa<=15).sum())]; r['n_neg']=[int((pc_<0).sum()),int((pa<0).sum())]
    kc,ka,ku=klass(C,y),klass(A,y),klass(U,y)
    dk=(ka-kc).round(2); r['dTWh']={k:v for k,v in dk.items() if abs(v)>=0.1}
    r['uc15_minus_uc14_TWh']={k:v for k,v in (ka-ku).round(2).items() if abs(v)>=0.1}
    low=np.asarray(terc=='low')
    r['marg_low_ctl']=marg(C,y,low); r['marg_low_arm']=marg(A,y,low)
    out[y]=r; print(y,json.dumps(r),flush=True)
json.dump(out,open('/tmp/claude-0/sp/diag15.json','w'),indent=1)
