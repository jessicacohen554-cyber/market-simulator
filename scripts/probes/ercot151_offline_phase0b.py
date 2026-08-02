"""ercot-151 Phase 0b: config-collapsed offline-increment at the missed 2023 tail hours."""
import json
import numpy as np
import pandas as pd

ROOT = '/home/user/market-simulator'

sysf = pd.read_parquet(f'{ROOT}/results/calibration/ercot150_zonalanchor_B/hourly/system_2023.parquet')
g = sysf.groupby('hour')
model_price = g.apply(lambda x: np.average(x['price'], weights=x['demand'].clip(lower=1e-9)),
                      include_groups=False).reindex(range(8760))
act = pd.read_parquet(f'{ROOT}/data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet')
act23 = act[act['year'] == 2023].set_index('hour')['rt'].reindex(range(8760))
tail_hours = act23[act23 > 300.0].index
missed = [h for h in tail_hours if model_price.get(h, np.nan) < 200.0]
idx = pd.date_range('2023-01-01', periods=8760, freq='h')
sel_keys = {(idx[h].strftime('%Y-%m-%d'), idx[h].hour + 1) for h in missed}

_CC_CONFIG_TAGS = ("_CC", "_CCU", "_GT", "_ST")
def _site(name, rtype):
    if rtype in ("CCGT90", "CCLE90"):
        for tag in _CC_CONFIG_TAGS:
            i = name.rfind(tag)
            if i > 0:
                return name[:i]
        return name.rsplit("_", 1)[0]
    return name

GAS_TYPES = {'CCGT90': 'CC', 'CCLE90': 'CC', 'SCGT90': 'CT', 'SCLE90': 'CT',
             'GSREH': 'ST', 'GSNONR': 'ST', 'GSSUP': 'ST'}
mwc = [f'QSE submitted Curve-MW{i}' for i in range(1, 11)]
prc = [f'QSE submitted Curve-Price{i}' for i in range(1, 11)]
frames = []
for span in ['Jan-Mar', 'Apr-Jun', 'Jul-Sep', 'Oct-Nov']:
    f = pd.read_parquet(
        f'{ROOT}/data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_{span}.parquet')
    f['he'] = pd.to_numeric(f['Hour Ending'].astype(str).str.split(':').str[0], errors='coerce')
    f['date'] = pd.to_datetime(f['Delivery Date'], errors='coerce')
    f['key'] = list(zip(f['date'].dt.strftime('%Y-%m-%d'), f['he']))
    f = f[f['key'].isin(sel_keys) & f['Resource Type'].isin(GAS_TYPES)]
    frames.append(f)
dam = pd.concat(frames, ignore_index=True)
for c in mwc + prc + ['HSL', 'LSL']:
    dam[c] = pd.to_numeric(dam[c], errors='coerce')
dam['cls'] = dam['Resource Type'].map(GAS_TYPES)
dam['site'] = [_site(n, t) for n, t in zip(dam['Resource Name'], dam['Resource Type'])]
st = dam['Resource Status'].astype(str).str.strip().str.upper()
dam['grp'] = np.select(
    [st.isin(['ON', 'ONREG', 'ONDSR', 'ONRUC', 'ONRR', 'ONOS', 'ONEMR', 'ONTEST']),
     st.isin(['OFF', 'OFFQS', 'OFFNS'])],
    ['on', 'off'], default='out')

def mw_below(row, thresh):
    tot = 0.0
    for m, p in zip(mwc, prc):
        if pd.isna(row[m]) or pd.isna(row[p]):
            break
        if row[p] <= thresh:
            tot = row[m]
    return tot
dam['mw_le_200'] = dam.apply(lambda r: mw_below(r, 200), axis=1)
dam['mw_le_300'] = dam.apply(lambda r: mw_below(r, 300), axis=1)

# config-collapse per (key, site): on = max HSL among on rows; off increment =
# max(0, max off HSL - on). Same for the cheap-offer MW (take the OFF config
# with max HSL as the representative curve).
rows = []
for (key, site, cls), gdf in dam.groupby(['key', 'site', 'cls']):
    on = gdf.loc[gdf.grp == 'on', 'HSL'].max()
    on = 0.0 if pd.isna(on) else on
    offs = gdf[gdf.grp == 'off']
    if len(offs):
        j = offs['HSL'].idxmax()
        off_hsl = offs.at[j, 'HSL']
        off_inc = max(0.0, off_hsl - on)
        frac = off_inc / off_hsl if off_hsl > 0 else 0.0
        off_le200 = offs.at[j, 'mw_le_200'] * frac
        off_le300 = offs.at[j, 'mw_le_300'] * frac
    else:
        off_inc = off_le200 = off_le300 = 0.0
    rows.append((key, site, cls, on, off_inc, off_le200, off_le300))
col = pd.DataFrame(rows, columns=['key', 'site', 'cls', 'on', 'off_inc', 'off_le200', 'off_le300'])
n = len(sel_keys)
agg = col.groupby('cls')[['on', 'off_inc', 'off_le200', 'off_le300']].sum() / n / 1000
print(f'missed hours: {len(missed)} (model mean ${np.nanmean(model_price[missed]):.0f}, actual ${np.nanmean(act23[missed]):.0f})')
print('\nConfig-collapsed mean GW per missed hour:')
print(agg.round(2))
print('\nCC+CT startable-OFF increment: %.2f GW (of it %.2f GW submitted-DAM <= $200)' % (
    agg.loc[['CC', 'CT'], 'off_inc'].sum(), agg.loc[['CC', 'CT'], 'off_le200'].sum()))
print('all-gas OFF increment <= $200: %.2f GW, <= $300: %.2f GW' % (
    agg['off_le200'].sum(), agg['off_le300'].sum()))

out = json.load(open(f'{ROOT}/results/calibration/ercot151_offline_phase0.json'))
out['config_collapsed'] = {
    'per_class_gw': {c: {k: round(float(v), 3) for k, v in agg.loc[c].items()} for c in agg.index},
    'cc_ct_off_increment_gw': round(float(agg.loc[['CC', 'CT'], 'off_inc'].sum()), 3),
    'cc_ct_off_le200_gw': round(float(agg.loc[['CC', 'CT'], 'off_le200'].sum()), 3),
}
json.dump(out, open(f'{ROOT}/results/calibration/ercot151_offline_phase0.json', 'w'), indent=1)
print('\nupdated results/calibration/ercot151_offline_phase0.json')
