"""Phase-0: model vs actual SPP hourly price distribution, bottom tail."""
import sys; sys.path.insert(0,'src')
import numpy as np, pandas as pd

BUN = {y: 'results/calibration/spp42_span_a' for y in (2023,2024,2025)}
BUN.update({y: 'results/calibration/spp49_benchmembership_span' for y in (2019,2020,2021,2022)})

act = pd.read_parquet('data/raw/_validation-source/actual_lmp_hourly_SPP.parquet')

rows=[]
for y in sorted(BUN):
    df = pd.read_parquet(f'{BUN[y]}/hourly/system_{y}.parquet')
    df = df[df['pass']=='P1']
    # load-weighted system price per hour across zones
    g = df.groupby('hour')
    num = (df['price']*df['demand']).groupby(df['hour']).sum()
    den = df.groupby('hour')['demand'].sum()
    mp = (num/den).to_numpy()
    a = act[act['year']==y]
    art = a['rt'].to_numpy(); ada = a['da'].to_numpy()
    rows.append(dict(year=y, n_mod=len(mp),
        mod_min=mp.min(), mod_p01=np.percentile(mp,1), mod_p05=np.percentile(mp,5),
        mod_neg=(mp<0).sum(), mod_at_m26=(np.abs(mp+26.0)<1e-6).sum(), mod_below_m26=(mp<-26.0001).sum(),
        rt_min=art.min(), rt_p01=np.percentile(art,1), rt_p05=np.percentile(art,5),
        rt_neg=(art<0).sum(), rt_below_m26=(art<-26.0).sum(),
        da_min=ada.min(), da_p01=np.percentile(ada,1), da_p05=np.percentile(ada,5),
        da_neg=(ada<0).sum(), da_below_m26=(ada<-26.0).sum(), n_act=len(art)))
r=pd.DataFrame(rows)
pd.set_option('display.width',250)
print("=== BOTTOM TAIL: model (load-wtd system) vs actual RT and DA ===")
print(r.to_string(index=False, float_format=lambda v: f'{v:10.3f}'))
