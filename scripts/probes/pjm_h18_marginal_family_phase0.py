"""pjm-h18 phase 0 — which fuel family is on the model's margin, and what each carries. ZERO LP.

Rule 32 ``[R-SHARD]`` (a): no LP. For each year a ``fleet_only`` rebuild of the
PJM keeper recipe (the SAME ``mc_base`` offers the LP solved on) is joined to
the keeper's committed ``class_band_hourly`` P1 dispatch. The marginal
class-band in an hour is the partially-loaded band (2 % < utilisation < 98 %,
> 50 MW available) whose capacity-weighted offer is nearest the hour's
load-weighted system price. Each hour's error is then attributed to that band's
fuel family. STATED LIMIT: no measured marginal-fuel series is on disk, so the
split says where the MODEL's error sits, not how the model's marginal mix
compares with PJM's. Record: ``docs/FINDING-pjm-h18-price-object-localised-2026-09-23.md``.

Run: ``python3 scripts/probes/pjm_h18_marginal_family_phase0.py 2020 2021 2022 2023 2024 2025``
"""
import json,logging,sys,numpy as np,pandas as pd
sys.path.insert(0,'.'); sys.path.insert(0,'src')
logging.disable(logging.CRITICAL)
from pathlib import Path
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
from scripts.run_calibration import run_year
act=pd.read_parquet('data/raw/_validation-source/actual_lmp_hourly_PJM.parquet')
out={}
for y in [int(a) for a in sys.argv[1:]]:
    B=Path('results/calibration/hydro2_pjm_ror_'+('span' if y>=2023 else 'touchpoint'))
    meta=json.loads((B/'meta.json').read_text())
    kw=run_year_kwargs(meta); kw.update(derived_run_year_inputs(B,y)); kw['pjm_da_virtual_bids']=False
    r=run_year(y,meta['iso'],8760,meta.get('gas_price'),{},fleet_only=True,**kw)
    fa=r['fleet_arrays']; mc=np.asarray(r['mc_base'],float)
    if mc.ndim==1: mc=mc[:,None]*np.ones((1,8760))
    fp=np.asarray(r['fuel_prices'],float)
    T=mc.shape[1]
    cls=np.asarray(fa.plant_group).astype(str); band=np.array([u.rsplit('_',1)[-1] for u in fa.unit_ids])
    av=np.asarray(fa.pmax,float)[:,None]*(np.asarray(fa.availability,float) if np.ndim(fa.availability)==2 else np.asarray(fa.availability,float)[:,None])
    key=np.char.add(np.char.add(cls,'|'),band)
    cb=pd.read_parquet(B/'hourly'/f'class_band_hourly_{y}.parquet'); cb=cb[cb['pass']=='P1']
    cb['key']=cb.klass.astype(str).str.replace(r'^COAL_.*','COAL',regex=True)+'|'+cb.band.astype(str)
    disp=cb.pivot_table(index='key',columns='hour',values='mw',aggfunc='sum').reindex(columns=range(T)).fillna(0.0)
    s=pd.read_parquet(B/'hourly'/f'system_{y}.parquet'); s=s[(s['pass']=='P1')&(s.zone!='PJM_external')]
    s=s.assign(pdm=s.price*s.demand).groupby('hour')[['pdm','demand']].sum(); p=(s.pdm/s.demand).reindex(range(T)).to_numpy()
    a=act[act.year==y].sort_values('hour').rt.to_numpy(float)[:T]
    uk=[k for k in np.unique(key) if k in disp.index]
    capk=np.vstack([av[key==k].sum(0) for k in uk]); mck=np.vstack([(mc[key==k]*av[key==k]).sum(0)/np.maximum(av[key==k].sum(0),1e-9) for k in uk])
    mwk=disp.loc[uk].to_numpy()
    u=mwk/np.maximum(capk,1e-9)
    part=(u>0.02)&(u<0.98)&(capk>50)
    dist=np.where(part,np.abs(mck-p[None,:]),np.inf)
    j=np.argmin(dist,axis=0); marg=np.where(np.isfinite(dist.min(0)),np.array(uk)[j],'none|none')
    mcls=np.array([m.split('|')[0] for m in marg])
    fam=np.where(np.char.startswith(mcls,'COAL'),'coal',np.where(np.isin(mcls,['CC_REGULAR','CC_CHP']),'cc',np.where(np.isin(mcls,['CT_PEAKER','CT_CHP']),'ct',np.where(np.isin(mcls,['ST_GAS','ST_CHP']),'st',np.where(mcls=='none','none','other')))))
    w=s.demand.reindex(range(T)).to_numpy(); W=w.sum()
    gas=fp[np.isin(cls,['CC_REGULAR'])]; gmean=(gas*av[np.isin(cls,['CC_REGULAR'])]).sum(0)/av[np.isin(cls,['CC_REGULAR'])].sum(0)
    coal=np.char.startswith(cls,'COAL'); cmean=(fp[coal]*av[coal]).sum(0)/av[coal].sum(0)
    lo=a<=np.median(a)
    res={'gas_cc_capwtd':float(gmean.mean()),'coal_capwtd':float(cmean.mean()),'fam':{}}
    for f in ['coal','cc','ct','st','other','none']:
        m=fam==f
        res['fam'][f]={'share':float(m.mean()),'share_bottom50':float(m[lo].mean()),'share_top50':float(m[~lo].mean()),
            'err_contrib':float(((p-a)*w)[m].sum()/W),'model_p':float(p[m].mean()) if m.any() else None,'actual_p':float(a[m].mean()) if m.any() else None}
    # offer levels: cap-weighted econ-band mc, by class
    lv={}
    for c in ['CC_REGULAR','COAL','CT_PEAKER','ST_GAS']:
        for bb in ['mustrun','sync','committed','econc00','econc02','econc05','econ','peak']:
            m=(cls==c)&(band==bb)
            if m.sum(): lv[f'{c}|{bb}']=round(float((mc[m]*av[m]).sum()/av[m].sum()),2)
    res['offer_levels']=lv
    out[y]=res
    print(y,json.dumps({k:v for k,v in res.items() if k!='offer_levels'},indent=None)[:1500]); print(' offers',lv,flush=True)
Path('results/calibration/_pjm_h18_marginal_family.json').write_text(json.dumps(out,indent=1))
