"""SPP-55 phase 0: the design's requirement series on keeper-3's fleet vs SPP's posted cleared CR (zero LP)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
REPO=Path('/home/user/market-simulator'); sys.path.insert(0,str(REPO)); sys.path.insert(0,str(REPO/'src'))
from types import SimpleNamespace
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
from scripts.run_calibration import run_year
from market_sim.model.reserves.spec import _spp_design, _spp_largest_unit_nameplate, _reserve_eligible, SPP_BA_CR_REQUIREMENT_RATIO, SPP_RSG_CR_SCALING_FACTOR
S=Path('/tmp/claude-0/-home-user-market-simulator/1ff2487a-af08-5367-b9d9-cba4cd0fc66c/scratchpad')
BUNDLE=REPO/'results/calibration/spp43_screened_B'
meta=json.loads((BUNDLE/'meta.json').read_text()); kw=run_year_kwargs(meta)
out=[]
for year in (2023,2024,2025):
    kwy=dict(kw); kwy.update(derived_run_year_inputs(BUNDLE,year))
    r=run_year(year,'SPP',8760,float(meta['gas_prices'][str(year)]),{},fleet_only=True,**kwy)
    fa=r['fleet_arrays']
    d=_spp_design(SimpleNamespace(iso='SPP',mode='backcast',weather_year=year),fa,8760,['SPP-North','SPP-South'])
    fam=d.families[0]; req=fam.requirement
    lu=_spp_largest_unit_nameplate(fa.plant_code); elig=_reserve_eligible(fa)
    pc=np.asarray(fa.plant_code)
    top=sorted({(int(p),lu.get(int(p),0.0)) for p,e in zip(pc,elig) if e and int(p)>0}, key=lambda x:-x[1])[:6]
    print(year,'largest single units (plant, MW):',top)
    print(year,'requirement: min %.0f p5 %.0f median %.0f max %.0f | steps'%(req.min(),np.percentile(req,5),np.median(req),req.max()), fam.ordc_penalties, np.round(fam.ordc_step_widths,1))
    mssc=req/(SPP_BA_CR_REQUIREMENT_RATIO*SPP_RSG_CR_SCALING_FACTOR)
    mon=pd.Series(req).groupby(pd.Series(np.arange(8760)//24//30.4).astype(int).clip(0,11)+1).median().round(0)
    print(year,'monthly median requirement',mon.to_dict())
    pd.DataFrame({'hour':range(8760),'req':req,'mssc':mssc}).to_parquet(S/f'spp55/req_{year}.parquet')
    if year in (2023,2024):
        m=pd.read_parquet(S/f'or/or_spp_{year}.parquet'); t=pd.to_datetime(m['Interval'],format='%m/%d/%Y %H:%M:%S'); te=t-pd.Timedelta(minutes=1)
        keep=~((te.dt.month==2)&(te.dt.day==29)); m=m[keep]; te=te[keep]
        doy=te.dt.dayofyear.values
        if year==2024: doy=np.where(doy>60,doy-1,doy)
        hidx=(doy-1)*24+te.dt.hour.values
        tot=(m.Spin_Clr+m.Supp_Clr).groupby(hidx).mean().reindex(range(8760))
        ratio_t=tot.values/(SPP_RSG_CR_SCALING_FACTOR*mssc)
        print(year,'measured hourly cleared CR: median %.0f | model req median %.0f | model/measured: p5 %.3f median %.3f p95 %.3f | implied ratio (measured/(1.2*MSSC_model)) median %.3f'%(np.nanmedian(tot),np.median(req),np.nanpercentile(req/tot.values,5),np.nanmedian(req/tot.values),np.nanpercentile(req/tot.values,95),np.nanmedian(ratio_t)))
        mm=pd.DataFrame({'meas':tot.values,'model':req}).groupby(pd.Series(np.arange(8760)//24//30.4).astype(int).clip(0,11)+1).median().round(0)
        print(year,'monthly medians measured vs model'); print(mm.T.to_string())
