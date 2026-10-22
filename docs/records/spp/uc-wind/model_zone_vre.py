"""UC-SPP-WIND, zero LP: the keeper's per-zone wind/solar MW (data layer only, load_renewable_profiles).

Recipe = the keeper bundle's run_config_<y>.json. Run from the repo root with PYTHONPATH=. after
`scripts/regenerate_clean.py --solve-profile SPP`. Usage: model_zone_vre.py <out.csv.gz>
"""
import json, dataclasses, sys
import numpy as np, pandas as pd
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.renewables import load_renewable_profiles
out = sys.argv[1]
rows = []
for y in range(2019, 2026):
    rc = json.load(open(f'results/calibration/closeout_spp_nuc_span/run_config_{y}.json'))
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    c = ScenarioConfig(**{k: v for k, v in rc['scenario_config'].items() if k in fields})
    iso = get_iso_config('SPP')
    wcf, wcap, scf, scap = load_renewable_profiles('SPP', y, iso, c)
    zn = iso.zone_names
    df = pd.DataFrame({'year': y, 'hour': np.arange(wcf.shape[1])})
    for i, z in enumerate(zn):
        df[f'wind_{z}'] = wcf[i] * wcap[i]
        df[f'solar_{z}'] = scf[i] * scap[i]
    print(y, zn, wcap, scap, flush=True)
    rows.append(df)
pd.concat(rows).round(1).to_csv(out, index=False, compression='gzip')
