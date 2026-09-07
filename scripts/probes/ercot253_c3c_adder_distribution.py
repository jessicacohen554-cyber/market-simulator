"""ercot-253 work item B, phase 0: the C3c adder-DISTRIBUTION object, identified
on the TRAINING years 2023-2025 only (rule 22 step 3). Read-only: no LP, no
solve, no cell verdict. Committed keeper sidecars + the measured ERCOT ORDC
series; NaN-safe (2025's RTC+B tail has 648 uncovered measured hours)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

K = Path("results/calibration/ercot248_two_config_keeper/hourly")
O = Path("data/raw/ercot")
BANDS = [(0.01, 1), (1, 10), (10, 50), (50, 150), (150, 500), (500, 1000), (1000, 1e9)]
out = {}
for y in (2023, 2024, 2025):
    f = pd.read_parquet(K / f"reserve_family_{y}.parquet")
    f = f[(f.family == "ercot_ordc_total") & (f["pass"] == "P1")].sort_values("hour")
    m = pd.read_parquet(O / f"ercot_{y}_ordc_reserves_hourly.parquet").sort_values("hour")
    ma = f.dual.to_numpy(float).clip(min=0)
    mr, mq = f.held_mw.to_numpy(float), f.requirement_mw.to_numpy(float)
    pa, pr = m.rtorpa.to_numpy(float), m.rtolcap.to_numpy(float)
    cov = ~(np.isnan(pa) | np.isnan(pr))          # measured coverage mask
    pa_c = np.where(cov, np.nan_to_num(pa, nan=0.0).clip(min=0), np.nan)
    row = {
        "measured_coverage_h": int(cov.sum()),
        "writing_h": {"model": int((ma > 0).sum()),
                      "published": int(np.nansum(pa_c > 0))},
        "adder_dollar_sum": {"model": round(float(ma.sum()), 1),
                             "published": round(float(np.nansum(pa_c)), 1)},
        "bands": {(f"[{lo:g},{hi:g})" if hi < 1e9 else f">={lo:g}"): {
            "model": int(((ma >= lo) & (ma < hi)).sum()),
            "published": int(np.nansum((pa_c >= lo) & (pa_c < hi)))}
            for lo, hi in BANDS},
        "quantiles_on_own_writing_h": {
            "model": {str(q): round(float(np.percentile(ma[ma > 0], q)), 2)
                      for q in (50, 90, 99, 100)},
            "published": {str(q): round(float(np.percentile(pa_c[cov & (pa_c > 0)], q)), 2)
                          for q in (50, 90, 99, 100)}},
        "argument_of_the_curve": {
            "model_held_mw_p50": round(float(np.median(mr)), 0),
            "model_requirement_mw_p50": round(float(np.median(mq)), 0),
            "held_tracks_requirement_pct_h": round(float((mr >= mq - 1e-6).mean() * 100), 1),
            "measured_rtolcap_mw_p50": round(float(np.nanmedian(pr)), 0),
            "mean_rtolcap_minus_held_mw": round(float(np.mean(pr[cov] - mr[cov])), 0)},
        "model_writing_h_are_a_subset_of_published": bool(
            ((ma > 0) & ~(cov & (pa_c > 0))).sum() == 0),
    }
    out[y] = row
print(json.dumps(out, indent=2))
