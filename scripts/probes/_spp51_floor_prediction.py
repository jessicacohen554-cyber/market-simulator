"""Phase-0 item 4: ZERO-LP prediction, written BEFORE any solve."""
import sys; sys.path.insert(0,'src')
import numpy as np, pandas as pd

BUN = {y:'results/calibration/spp42_span_a' for y in (2023,2024,2025)}
BUN.update({y:'results/calibration/spp49_benchmembership_span' for y in (2019,2020,2021,2022)})
tr = pd.read_csv('data/raw/_processed-legacy/thermal_tranches_SPP.csv')
coal = tr[(tr.plant_group=='COAL')&(tr.status=='ok')].copy()
coal['f_new'] = coal.nameplate_mw*coal.mustrun_online_pct/100.0
coal['f_cur'] = coal.nameplate_mw*coal.mustrun_pct/100.0

rows=[]
for y in sorted(BUN):
    sysd = pd.read_parquet(f'{BUN[y]}/hourly/system_{y}.parquet'); sysd=sysd[sysd['pass']=='P1']
    load = sysd.groupby('hour')['demand'].sum().to_numpy()
    ch = pd.read_parquet(f'{BUN[y]}/hourly/class_hourly_{y}.parquet'); ch=ch[ch['pass']=='P1']
    def cls(k):
        return ch[ch.klass==k].groupby('hour')['mw'].sum().reindex(range(8760),fill_value=0.0).to_numpy()
    prb, lig = cls('COAL_PRB'), cls('COAL_LIGNITE')
    coal_tot = prb+lig
    wind = cls('wind')
    rank = load.argsort().argsort()/8759.0
    # aggregate floor per hour under (i) the EXISTING peak-ranked window, (ii) an all-hours window
    F_peak = np.zeros(8760); F_all = np.zeros(8760)
    for r in coal.itertuples():
        k=int(round(r.online_frac*8760)); thr=1.0-k/8760.0
        F_peak[rank>=thr] += r.f_new
        F_all += r.f_new*r.online_frac   # energy-equivalent, spread flat
    d_peak = np.maximum(0.0, F_peak-coal_tot).sum()/1e6
    d_all  = np.maximum(0.0, F_all -coal_tot).sum()/1e6
    rows.append(dict(year=y, coal_TWh=coal_tot.sum()/1e6, wind_TWh=wind.sum()/1e6,
        add_peakwin_TWh=d_peak, add_allhr_TWh=d_all,
        forced_share_peak=F_peak.sum()/1e6/ (coal_tot.sum()/1e6),
        h_below_Fpeak=int((coal_tot<F_peak).sum())))
r=pd.DataFrame(rows); pd.set_option('display.width',220)
print("=== ZERO-LP PREDICTION: coal energy the online-Pmin floor would add ===")
print("  add_peakwin = existing top-k PEAK-LOAD window (as coded)")
print("  add_allhr   = same MW held in every hour, scaled by online_frac (a correctly-windowed floor)")
print(r.to_string(index=False,float_format=lambda v:f'{v:9.3f}'))
print()
print(f"  mean add (peak window) = {r.add_peakwin_TWh.mean():.3f} TWh/yr")
print(f"  mean add (all hours)   = {r.add_allhr_TWh.mean():.3f} TWh/yr")
print(f"  target: mean fossil miss -9.990 TWh, mean wind excess +10.144 TWh")
