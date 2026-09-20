"""Phase-0 item 4: can the EXISTING coal_sync floor reach the zero-coal hours?
Zero LP. Reads committed sidecars + the committed tranche artifact."""
import sys; sys.path.insert(0,'src')
import numpy as np, pandas as pd

BUN = {y:'results/calibration/spp42_span_a' for y in (2023,2024,2025)}
BUN.update({y:'results/calibration/spp49_benchmembership_span' for y in (2019,2020,2021,2022)})

tr = pd.read_csv('data/raw/_processed-legacy/thermal_tranches_SPP.csv')
coal = tr[(tr.plant_group=='COAL')&(tr.status=='ok')].copy()
coal['floor_mw_new'] = coal.nameplate_mw * coal.mustrun_online_pct/100.0
coal['floor_mw_cur'] = coal.nameplate_mw * coal.mustrun_pct/100.0
print(f"SPP COAL plants ok = {len(coal)}   nameplate = {coal.nameplate_mw.sum():,.0f} MW")
print(f"  current mustrun band  (mustrun_pct)        = {coal.floor_mw_cur.sum():,.1f} MW  "
      f"({(coal.mustrun_pct==0).sum()} plants at ZERO)")
print(f"  online-Pmin band (mustrun_online_pct)      = {coal.floor_mw_new.sum():,.1f} MW  "
      f"({(coal.mustrun_online_pct==0).sum()} plants at zero)")
print(f"  online_frac range {coal.online_frac.min():.3f}-{coal.online_frac.max():.3f} "
      f"(force-all threshold 0.99 -> {int((coal.online_frac>=0.99).sum())} plants all-hours)")
print()

rows=[]
for y in sorted(BUN):
    sysd = pd.read_parquet(f'{BUN[y]}/hourly/system_{y}.parquet')
    sysd = sysd[sysd['pass']=='P1']
    load = sysd.groupby('hour')['demand'].sum().to_numpy()
    price = ((sysd['price']*sysd['demand']).groupby(sysd['hour']).sum()
             / sysd.groupby('hour')['demand'].sum()).to_numpy()
    ch = pd.read_parquet(f'{BUN[y]}/hourly/class_hourly_{y}.parquet')
    ch = ch[ch['pass']=='P1']
    prb = ch[ch.klass=='COAL_PRB'].groupby('hour')['mw'].sum().reindex(range(8760),fill_value=0.0).to_numpy()
    zero = prb <= 1e-6
    # load percentile rank of the zero-coal hours (1.0 = highest load)
    rank = load.argsort().argsort()/ (len(load)-1)
    zr = rank[zero]
    # For each plant, does its top-k window cover the zero-coal hours?
    cov=[]
    for r in coal.itertuples():
        k = int(round(r.online_frac*8760))
        thresh = 1.0 - k/8760.0          # hours with rank >= thresh are in top-k
        cov.append((zr >= thresh).mean() if zero.any() else np.nan)
    rows.append(dict(year=y, h_zero=int(zero.sum()),
        zero_loadrank_med=np.median(zr) if zero.any() else np.nan,
        zero_loadrank_p90=np.percentile(zr,90) if zero.any() else np.nan,
        mean_cov=np.nanmean(cov) if zero.any() else np.nan,
        cap_wtd_cov=(np.nansum(np.array(cov)*coal.floor_mw_new.to_numpy())/coal.floor_mw_new.sum()) if zero.any() else np.nan,
        mean_price_zero=price[zero].mean() if zero.any() else np.nan))
r=pd.DataFrame(rows)
pd.set_option('display.width',200)
print("=== do the zero-coal hours fall inside the top-k PEAK-LOAD floor window? ===")
print("  zero_loadrank: 0.0 = lowest-load hour of the year, 1.0 = highest")
print("  cov = share of that year's zero-coal hours the plant's top-k window covers")
print(r.to_string(index=False,float_format=lambda v:f'{v:9.3f}'))
