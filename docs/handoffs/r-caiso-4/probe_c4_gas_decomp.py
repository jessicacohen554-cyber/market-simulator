import json,gzip,base64,sys
import numpy as np, pandas as pd
sys.path.insert(0,'scripts')
import calibration_verdict as cv
p=json.load(open('/tmp/claude-0/payload.json'))
res={}
for Y in ('2022','2023','2024','2025'):
    yp=p['years'][Y]; yb=json.load(gzip.open(f'frontend/data/backcast/bench/CAISO/{Y}.json.gz'))['bench']
    rows={r.get('fuel'):r for r in yp['fuelRows']}; mt=rows['gas'].get('m')
    t=8760; model=np.zeros(t); act=np.zeros(t); btm=0; per={}
    for code,bp in yb['plants'].items():
        if bp.get('group') not in cv.GAS_CLASSES or bp.get('nodata'): continue
        cap=float(bp.get('npl') or 0); pp=yp['plants'].get(str(code))
        if cap<=0 or not bp.get('campd') or not pp or not pp.get('m'): continue
        a=np.frombuffer(base64.b64decode(bp['campd'])[:t],np.uint8)*cap/100; m=np.frombuffer(base64.b64decode(pp['m'])[:t],np.uint8)*cap/100
        act[:len(a)]+=a; model[:len(m)]+=m; btm+=float(bp.get('btm') or 0)
        per[code]=(bp.get('name'),bp.get('group'),m.sum()/1e6,a.sum()/1e6,((m-a)).copy())
    bm=btm*1e6/t; act=act-bm+float(yb['e930']['gas_cogen_grid'])*1e6/t
    core=model.sum()/1e6-btm; fill=(mt-core)*1e6/t; model=model-bm+fill
    r,n=cv._pearson_nrmse(list(model),list(act)); 
    e=model-act; om=act.mean()
    idx=pd.date_range(f'{Y}-01-01',periods=t,freq='h')
    df=pd.DataFrame({'e2':e**2,'e':e,'m':model,'a':act},index=idx)
    mon=df.groupby(df.index.month).agg(e2=('e2','sum'),bias=('e','mean'),m=('m','mean'),a=('a','mean'))
    mon['share']=mon.e2/df.e2.sum()
    hod=df.groupby(df.index.hour).agg(e2=('e2','sum'),bias=('e','mean'))
    hod['share']=hod.e2/df.e2.sum()
    print(Y,'r',round(r,3),'nrmse',round(n,4),'mean act MW',round(om),'bias MW',round(e.mean()),'fill MW',round(fill),'model TWh',mt)
    # nrmse decomposition: bias^2 + var
    print('  bias part of MSE',round(e.mean()**2/(e**2).mean(),3))
    if Y in('2025','2023'):
        print(mon.round(3).to_string()); print(hod[['share','bias']].round(3).T.to_string())
        # top plants by SSE contribution approx: per-plant error sum of squares cross term ignored; report sum abs err
        top=sorted(per.items(),key=lambda kv:-np.abs(kv[1][4]).sum())[:10]
        for c,(nm,g,mm,aa,ee) in top: print('   ',c,nm,g,'model',round(mm,2),'act',round(aa,2),'MAE MW',round(np.abs(ee).mean(),1))
