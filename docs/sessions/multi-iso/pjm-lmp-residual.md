# PJM hourly LMP overlay — localizing the summer scarcity residual (J3a)

**Date:** 2026-06-11.
**Data:** `data/raw/_validation-source/actual_lmp_hourly_PJM.parquet` (hub-mean hourly
RT/DA LMP across the 12 PJM trading hubs, 2023–2025, fixed 8760-hour local
calendar), built by `scripts/data/derive_actual_lmp.py` from the hourly Data Miner
exports in `data/raw/lmp-data/PJM_{year}_rt_da_monthly_lmps.csv`
(hourly despite the filename — 12 hubs × 8,760 local hours per file).
**Runs:** `pjm_9_chp_solar` (2023+2024) and `pjm_10d_chp` (2024 re-solve);
the two agree to ~$0.01 on every 2024 statistic below.
**Regenerate:**

```bash
python scripts/data/derive_actual_lmp.py
python scripts/archive/analyze_lmp_residual.py results/calibration/pjm_10d_chp \
    results/calibration/pjm_9_chp_solar          # add --out FILE.md to save
```

Model price is the dispatch LP's energy-balance dual, demand-weighted across
the 8 zones (the dashboard's average-LMP convention); actual is the unweighted
12-hub mean — the same pairing the summary page's monthly table already uses.

## Headline

The Jul/Aug residual is **−$4.90 (2023) / −$6.37 (2024)** — the upper end of
the ~−$6–8 estimate made from monthly means. The hourly overlay shows it is
**not a level bias**: the full-year p50 residual is +1.45 (2023) / +0.46
(2024). It is a missing **afternoon mid-scarcity regime**, concentrated three
ways:

1. **Duration curve** — the model's curve is too flat. Divergence starts at
   p75 and explodes in the tail (Jul/Aug 2024: p90 −34, p95 −49, p99 −110).

   | Jul/Aug 2024 | mean | p50 | p75 | p90 | p95 | p99 | max |
   |---|---|---|---|---|---|---|---|
   | model | 28.72 | 25.81 | 29.60 | 34.17 | 37.19 | 54.38 | 1,155.59 |
   | actual RT | 35.09 | 26.51 | 40.93 | 67.76 | 86.49 | 164.89 | 300.98 |

2. **Hour-of-day** — the gap lives in the 11:00–18:00 ramp, peaking at
   16:00–17:00 (−35/−39 $/MWh in 2024, −23/−26 in 2023). Overnight
   (00:00–05:00) the model runs **+$2–6 high**, partially masking the
   afternoon miss in the monthly mean. Evening hours 19:00–20:00 are at or
   above actuals.

3. **Actual-price band** — hours with actual RT ≥ $75 are ~4–7% of the
   Jul/Aug window but carry **92% of the 2024 $·h gap** (45% in 2023, where
   the $50–75 band carries another 45%). The model almost never enters that
   regime: 10 model hours > $75 vs 110 actual (2024); 4 vs 57 (2023).
   Meanwhile the model produces 3 spurious >$500 spikes (max $1,156) that
   actuals do not show (actual 2024 max $301) — residual hard-scarcity
   slack pricing, while the broad $75–200 regime in between is missing.

The same afternoon signature extends across May–Oct 2024 (May −6.8, Sep −5.6,
Oct −6.2), so "Jul/Aug scarcity residual" understates the season; winter
months are on or slightly above actuals (Jan +2.8, Dec +1.2).

## Reading

- The miss is the **$75–200 afternoon-peak price regime**, not VOLL events
  and not the offer-curve level (p50 matches). That is the shape of missing
  reserve scarcity pricing (ORDC-type adders), peak-hour congestion/uplift,
  and/or peak-coincident exports tightening supply (J1's +40 TWh net-export
  gap is peak-weighted). Cheaper structural candidates (J1 import/export
  node, E2/P5 storage cycling cost — model PS discharge currently floods the
  evening peak) should be re-measured against this overlay **before** any
  reserve/ORDC work, per the build-plan sequencing.
- The overnight +$2–6 overshoot is a second, separate signal (too much
  committed/must-run supply priced above actual overnight clearing) worth
  ~+$1.5/MWh of the monthly-mean offset.
- `actual_lmp.json` now carries `da_pct`/`rt_pct` duration-curve percentiles
  per PJM year, and any future run can be scored against the hourly series
  with `scripts/archive/analyze_lmp_residual.py` (or
  `market_sim.results.calibration.check_price_duration_curve`, which the
  hourly parquet can now feed as `benchmarks["prices"]`).

## J3b status (CAMPD unit-level coverage)

Blocked on uploads: `data/raw/campd-unit-level/` still has **no
MD/DE/NC/TN extracts and only MI 2024**. TN is now in
`campd.ISO_STATES["PJM"]`, so once `{MD,DE,NC,TN,MI}_{year}.parquet` land,
regenerate with:

```bash
python scripts/data/derive_campd_unit_outages.py --iso PJM --years 2023 2024 2025
```
