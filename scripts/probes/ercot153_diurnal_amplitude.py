"""ercot-153: ERCOT hour-of-day price-amplitude decomposition (xiso-1 follow-on).

No-LP. Decomposes the ERCOT diurnal amplitude deficit (xiso-1: model reproduces
52.9/38.2/36.7% of measured DA hour-of-day amplitude 2023/24/25) on the
ercot150b keeper's committed hourly sidecars vs the actual RT/DA LMP parquet:
per year, hour-of-day mean profiles (load-weighted system price), amplitude
split into PEAK half (hours above the daily mean: evening ramp) and TROUGH half
(below), by season; and the overlay/reserve columns' contribution at the
deficit hours. Committed record: results/calibration/ercot153_amplitude.json.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / 'results/calibration/ercot150_zonalanchor_B/hourly'


def sys_price(year: int) -> pd.DataFrame:
    f = pd.read_parquet(BUNDLE / f'system_{year}.parquet')
    g = f.groupby('hour')
    price = g.apply(lambda x: np.average(x['price'], weights=x['demand'].clip(lower=1e-9)),
                    include_groups=False)
    extras = g[['reserve_price', 'rtordpa_overlay', 'ordc_adder']].mean()
    out = pd.DataFrame({'model': price})
    return out.join(extras)


def hod_profile(s: pd.Series) -> np.ndarray:
    hod = np.arange(len(s)) % 24
    return np.array([s[hod == h].mean() for h in range(24)])


def main() -> None:
    act = pd.read_parquet(REPO / 'data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet')
    out = {}
    for year in (2023, 2024, 2025):
        m = sys_price(year)
        a = act[act['year'] == year].set_index('hour').reindex(range(8760))
        rec = {}
        mon = pd.date_range(f'{year}-01-01', periods=8760, freq='h').month
        seasons = {'annual': np.ones(8760, bool),
                   'summer_JJAS': np.isin(mon, [6, 7, 8, 9]),
                   'winter_DJF': np.isin(mon, [12, 1, 2]),
                   'shoulder': np.isin(mon, [3, 4, 5, 10, 11])}
        for name, mask in seasons.items():
            prof_m = hod_profile(m['model'][mask].reset_index(drop=True))
            prof_rt = hod_profile(a['rt'][mask].reset_index(drop=True))
            prof_da = hod_profile(a['da'][mask].reset_index(drop=True))
            amp = lambda p: float(p.max() - p.min())
            mean_of = lambda p: float(np.nanmean(p))
            peak_excess = lambda p: float(np.nanmax(p) - np.nanmean(p))
            trough_def = lambda p: float(np.nanmean(p) - np.nanmin(p))
            rec[name] = {
                'amp_model': round(amp(prof_m), 2), 'amp_rt': round(amp(prof_rt), 2),
                'amp_da': round(amp(prof_da), 2),
                'amp_ratio_vs_rt': round(amp(prof_m) / amp(prof_rt), 3),
                'amp_ratio_vs_da': round(amp(prof_m) / amp(prof_da), 3),
                'peak_excess_model': round(peak_excess(prof_m), 2),
                'peak_excess_rt': round(peak_excess(prof_rt), 2),
                'trough_deficit_model': round(trough_def(prof_m), 2),
                'trough_deficit_rt': round(trough_def(prof_rt), 2),
                'peak_hour_model': int(np.nanargmax(prof_m)),
                'peak_hour_rt': int(np.nanargmax(prof_rt)),
                'reserve_price_at_peak_hours': round(float(np.nanmean(
                    hod_profile(m['reserve_price'][mask].reset_index(drop=True))[17:22])), 2),
                'rtordpa_at_peak_hours': round(float(np.nanmean(
                    hod_profile(m['rtordpa_overlay'][mask].reset_index(drop=True))[17:22])), 2),
            }
        out[str(year)] = rec
    path = REPO / 'results/calibration/ercot153_amplitude.json'
    path.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
