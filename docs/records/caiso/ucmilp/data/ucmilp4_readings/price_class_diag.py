"""Zero-LP readings for RESULT-ucmilp4-caiso: load-weighted price (5 CAISO zones), tercile split by control price,
<= $15 hours, uplift share, class TWh deltas (control / UC-3 uc-1.5 / U4). Run from the repo root with the three spans on disk."""
import pandas as pd, json
Z = ['LA_BASIN', 'NP15', 'SDGE', 'SP15_rest', 'ZP26']
B = {'ctrl': 'results/calibration/closeout_caiso_w1_a2_span',
     'uc15': 'docs/records/caiso/ucmilp/data/ucmilp15_caiso_span',
     'u4': 'docs/records/caiso/ucmilp/data/ucmilp4_caiso_span'}
def lw(b, y):
    d = pd.read_parquet(f'{b}/hourly/system_{y}.parquet'); d = d[d.zone.isin(Z)]
    return (d.price * d.demand).groupby(d.hour).sum() / d.demand.groupby(d.hour).sum(), (d.price * d.demand).sum()
def tw(b, y):
    d = pd.read_parquet(f'{b}/hourly/class_hourly_{y}.parquet')
    return d.groupby('klass').mw.sum() / 1e6
for y in range(2019, 2026):
    pc, _ = lw(B['ctrl'], y); pu, _ = lw(B['uc15'], y); pa, tot = lw(B['u4'], y)
    terc = pd.qcut(pc, 3, labels=['low', 'mid', 'high'])
    up = pd.read_parquet(f"{B['u4']}/hourly/uc_uplift_{y}.parquet")['uplift_usd'].sum()
    print(y, 'price ctrl %.2f uc15 %.2f U4 %.2f' % (pc.mean(), pu.mean(), pa.mean()),
          ' '.join('%s %+.2f' % (t, (pa - pc)[terc == t].mean()) for t in ['low', 'mid', 'high']),
          '<=$15h %d->%d' % ((pc <= 15).sum(), (pa <= 15).sum()), 'uplift %.3f%%' % (100 * up / tot))
    c, u, a = tw(B['ctrl'], y), tw(B['uc15'], y), tw(B['u4'], y)
    print('  ', ' '.join('%s %+.2f' % (k, a.get(k, 0) - c.get(k, 0)) for k in ['CC_REGULAR', 'import', 'CT_PEAKER', 'ST_GAS']))
