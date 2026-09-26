"""Zero-LP fleet dump for G-DRIFT / G-FOOT. argv: repo bundle year out.npz [overrides-json]"""
import sys, json
from pathlib import Path
import numpy as np
repo=Path(sys.argv[1]); sys.path.insert(0,str(repo)); sys.path.insert(0,str(repo/'src'))
import market_sim; print("market_sim from", market_sim.__file__)
from scripts.lib.bundle_fleet import full_run_year_kwargs, bundle_gas_price, ensure_probe_path
ensure_probe_path()
from scripts.replay_keeper import derived_run_year_inputs
from scripts.run_calibration import run_year
bundle=Path(sys.argv[2]); Y=int(sys.argv[3]); ov=json.loads(open(sys.argv[5]).read()) if len(sys.argv)>5 else {}
meta=json.loads((bundle/'meta.json').read_text())
kw=full_run_year_kwargs(meta)
if ov:
    p=dict(kw.get('prb_overrides') or {}); p.update(ov); kw['prb_overrides']=p
st=run_year(Y,meta['iso'],int(meta['hours']),bundle_gas_price(meta,Y),**kw,**derived_run_year_inputs(bundle,Y))
fa=st['fleet_arrays']; out={}
for k in ('pmax','pmin','availability','min_gen','heat_rate','vom','emission_rate','nox_rate','zone_idx'):
    v=getattr(fa,k,None)
    if v is not None: out[k]=np.asarray(v)
out['mc_base']=np.asarray(st['mc_base']); out['demand']=np.asarray(st['demand'])
out['unit_ids']=np.array([str(u) for u in fa.unit_ids])
for k in ('wind_cap','solar_cap','wind_cf','solar_cf'):
    if k in st and st[k] is not None: out[k]=np.asarray(st[k])
np.savez_compressed(sys.argv[4],**out); print('dumped',Y,len(out['unit_ids']))
