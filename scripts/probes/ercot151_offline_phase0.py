"""ercot-151 Phase 0: offline-increment composition at the missed 2023 tail hours.

All inputs committed: keeper ercot150b system hourly (model price, zonal),
actual RT LMP parquet, 60-Day DAM Gen Resource 2023 parquets (statuses, HSL/LSL,
DAM offer curves, AS awards). No LP, no solve.
"""
import json
import numpy as np
import pandas as pd

ROOT = '/home/user/market-simulator'

# --- model price basis: load-weighted zonal -> system hourly (ercot101 basis) ---
sysf = pd.read_parquet(f'{ROOT}/results/calibration/ercot150_zonalanchor_B/hourly/system_2023.parquet')
sysf = sysf[sysf['pass'] == sysf['pass'].max()] if 'pass' in sysf and sysf['pass'].nunique() > 1 else sysf
# load-weighted system price per hour
g = sysf.groupby('hour')
model_price = g.apply(lambda x: np.average(x['price'], weights=x['demand'].clip(lower=1e-9)), include_groups=False)
model_price = model_price.reindex(range(8760))

act = pd.read_parquet(f'{ROOT}/data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet')
act23 = act[act['year'] == 2023].set_index('hour')['rt'].reindex(range(8760))

TAIL = 300.0
MISS_MODEL_LT = 200.0
tail_hours = act23[act23 > TAIL].index
missed = [h for h in tail_hours if model_price.get(h, np.nan) < MISS_MODEL_LT]
hit = [h for h in tail_hours if model_price.get(h, np.nan) >= MISS_MODEL_LT]
print(f'actual>{TAIL:.0f}: {len(tail_hours)} h | missed(model<{MISS_MODEL_LT:.0f}): {len(missed)} | hit: {len(hit)}')
print(f'missed hours: model p50 ${np.nanmedian(model_price[missed]):.0f} '
      f'mean ${np.nanmean(model_price[missed]):.0f} | actual mean ${np.nanmean(act23[missed]):.0f}')

# --- DAM disclosure statuses at those hours ---
# fixed CST hour-of-year -> (month, day, hourending). 2023 non-leap.
idx = pd.date_range('2023-01-01', periods=8760, freq='h')
frames = []
for span in ['Jan-Mar', 'Apr-Jun', 'Jul-Sep', 'Oct-Nov']:
    import pyarrow.parquet as _pq
    _names = _pq.ParquetFile(f'{ROOT}/data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_{span}.parquet').schema.names
    want = ['Delivery Date', 'Hour Ending', 'Resource Name', 'Resource Type',
            'HSL', 'LSL', 'Resource Status', 'Awarded Quantity',
            'RegUp Awarded', 'RRSPFR Awarded', 'RRSFFR Awarded', 'RRSUFR Awarded',
            'NonSpin Awarded', 'ECRSSD Awarded']
    f = pd.read_parquet(
        f'{ROOT}/data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_{span}.parquet',
        columns=[c for c in want if c in _names])
    if 'ECRSSD Awarded' not in f.columns:
        f['ECRSSD Awarded'] = 0.0
    frames.append(f)
dam = pd.concat(frames, ignore_index=True)
for c in ['HSL', 'LSL', 'Awarded Quantity', 'RegUp Awarded', 'RRSPFR Awarded',
          'RRSFFR Awarded', 'RRSUFR Awarded', 'NonSpin Awarded', 'ECRSSD Awarded']:
    dam[c] = pd.to_numeric(dam[c], errors='coerce')
dam['he'] = pd.to_numeric(dam['Hour Ending'].astype(str).str.split(':').str[0], errors='coerce')
dam['date'] = pd.to_datetime(dam['Delivery Date'], errors='coerce')

# map missed hours to (date, HE). Model hour h = hour-beginning CST -> HE = h%24+1
sel_keys = set()
for h in missed:
    ts = idx[h]
    sel_keys.add((ts.strftime('%Y-%m-%d'), ts.hour + 1))
dam['key'] = list(zip(dam['date'].dt.strftime('%Y-%m-%d'), dam['he']))
sub = dam[dam['key'].isin(sel_keys)].copy()
print(f'DAM rows at {len(sel_keys)} missed (date,HE) keys: {len(sub)}')

GAS_TYPES = {'CCGT90': 'CC', 'CCLE90': 'CC', 'SCGT90': 'CT', 'SCLE90': 'CT',
             'GSREH': 'ST', 'GSNONR': 'ST', 'GSSUP': 'ST'}
sub = sub[sub['Resource Type'].isin(GAS_TYPES)].copy()
sub['cls'] = sub['Resource Type'].map(GAS_TYPES)
stat = sub['Resource Status'].astype(str).str.strip().str.upper()
sub['is_on'] = stat.isin(['ON', 'ONREG', 'ONDSR', 'ONRUC', 'ONRR', 'ONOS', 'ONEMR'])
sub['is_off_startable'] = stat.isin(['OFF', 'OFFQS', 'OFFNS'])
sub['is_out'] = stat.isin(['OUT', 'OUTL', 'EMR', 'EMRSWGR'])

per_hour = sub.groupby(['key', 'cls']).apply(
    lambda x: pd.Series({
        'on_gw': x.loc[x.is_on, 'HSL'].sum() / 1000,
        'off_startable_gw': x.loc[x.is_off_startable, 'HSL'].sum() / 1000,
        'out_gw': x.loc[x.is_out, 'HSL'].sum() / 1000,
    }), include_groups=False).reset_index()
agg = per_hour.groupby('cls')[['on_gw', 'off_startable_gw', 'out_gw']].mean()
print('\nMean GW at missed hours (per class):')
print(agg.round(2))
print('\nCC+CT startable-but-OFF mean: %.2f GW | ON %.2f GW' % (
    agg.loc[['CC', 'CT'], 'off_startable_gw'].sum(), agg.loc[['CC', 'CT'], 'on_gw'].sum()))

# status census of the OFF block
print('\nStatus census (missed hours, gas):')
print(sub.groupby(stat)['HSL'].agg(['count', 'sum']).sort_values('sum', ascending=False).head(10))

# --- DAM offer curves of the OFF block: how cheap is the phantom depth? ---
# For OFF rows, reconstruct submitted DAM curve MW below price thresholds.
off = sub[sub.is_off_startable]
frames2 = []
for span in ['Jul-Sep', 'Apr-Jun', 'Oct-Nov', 'Jan-Mar']:
    f = pd.read_parquet(
        f'{ROOT}/data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_{span}.parquet')
    f['he'] = pd.to_numeric(f['Hour Ending'].astype(str).str.split(':').str[0], errors='coerce')
    f['date'] = pd.to_datetime(f['Delivery Date'], errors='coerce')
    f['key'] = list(zip(f['date'].dt.strftime('%Y-%m-%d'), f['he']))
    f = f[f['key'].isin(sel_keys) & f['Resource Type'].isin(GAS_TYPES)]
    frames2.append(f)
full = pd.concat(frames2, ignore_index=True)
stat2 = full['Resource Status'].astype(str).str.strip().str.upper()
full = full[stat2.isin(['OFF', 'OFFQS', 'OFFNS'])].copy()
mwc = [f'QSE submitted Curve-MW{i}' for i in range(1, 11)]
prc = [f'QSE submitted Curve-Price{i}' for i in range(1, 11)]
for c in mwc + prc + ['HSL']:
    full[c] = pd.to_numeric(full[c], errors='coerce')

def mw_below(row, thresh):
    tot = 0.0
    prev = 0.0
    for m, p in zip(mwc, prc):
        if pd.isna(row[m]) or pd.isna(row[p]):
            break
        if row[p] <= thresh:
            tot = row[m]
        prev = row[m]
    return tot

for th in (100, 200, 300):
    full[f'mw_le_{th}'] = full.apply(lambda r: mw_below(r, th), axis=1)
n_keys = len(sel_keys)
res = full.groupby(full['Resource Type'].map(GAS_TYPES))[
    ['mw_le_100', 'mw_le_200', 'mw_le_300', 'HSL']].sum() / n_keys / 1000
print('\nOFF-startable block: mean GW of SUBMITTED DAM offer at or below threshold (per missed hour):')
print(res.round(2).rename(columns={'HSL': 'hsl_gw'}))

out = {
    'tail_hours': int(len(tail_hours)), 'missed': int(len(missed)), 'hit': int(len(hit)),
    'model_mean_at_missed': float(np.nanmean(model_price[missed])),
    'actual_mean_at_missed': float(np.nanmean(act23[missed])),
    'off_startable_gw': {k: float(v) for k, v in agg['off_startable_gw'].items()},
    'on_gw': {k: float(v) for k, v in agg['on_gw'].items()},
    'off_dam_mw_le_200_gw': {k: float(v) for k, v in res['mw_le_200'].items()},
}
with open(f'{ROOT}/results/calibration/ercot151_offline_phase0.json', 'w') as fh:
    json.dump(out, fh, indent=1)
print('\nwrote results/calibration/ercot151_offline_phase0.json')
