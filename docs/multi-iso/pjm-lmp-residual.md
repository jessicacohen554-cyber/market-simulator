# PJM hourly LMP overlay — localizing the summer scarcity residual (J3a)

**Date:** 2026-06-11.
**Data:** `inputs/calibration/actual_lmp_hourly_PJM.parquet` (hub-mean hourly
RT/DA LMP across the 12 PJM trading hubs, 2023–2025, fixed 8760-hour local
calendar), built by `scripts/derive_actual_lmp.py` from the hourly Data Miner
exports in `inputs/raw-data/lmp-data/PJM_{year}_rt_da_monthly_lmps.csv`
(hourly despite the filename — 12 hubs × 8,760 local hours per file).
**Runs:** `pjm_9_chp_solar` (2023+2024) and `pjm_10d_chp` (2024 re-solve);
the two agree to ~$0.01 on every 2024 statistic below.
**Regenerate:**

```bash
python scripts/derive_actual_lmp.py
python scripts/analyze_lmp_residual.py results/calibration/pjm_10d_chp \
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
  with `scripts/analyze_lmp_residual.py` (or
  `market_sim.results.calibration.check_price_duration_curve`, which the
  hourly parquet can now feed as `benchmarks["prices"]`).

## J4 — net-load reserve-demand scarcity overlay (the afternoon regime)

**Date:** 2026-06-16. **Code:** `scarcity.netload_scarcity_adder`,
`scripts/derive_pjm_scarcity.py`, `constants.PJM_SCARCITY_CURVE`. Post-solve
overlay (no LP re-solve); writes `scarcity.parquet` consumed by
`analyze_lmp_residual.py --with-scarcity`.

### Honesty gate — why this is *not* the ERCOT ORDC

A reserve-keyed ORDC curve (the ERCOT mechanism, `ordc_adder`) **cannot work
for PJM** and was rejected on the pre-implementation diagnostic. ERCOT's
energy-only LP is genuinely thin in its priciest hours (~8.6 GW headroom,
near the 3 GW MCL), so the published LOLP×(VOLL−λ) curve self-targets. PJM's
LP instead sits on **~60 GW of idle headroom during the hours actual RT ≥
$100** (never below 28 GW idle all year), and the model's online-flexible
reserve (dispatched gas + storage) is **flat at ~11 GW across every actual
price band** (rho ≈ +0.18). A reserve-keyed curve would smear a uniform
adder, not self-target the peak — the honesty gate forbids that.

The discriminating variable is **net load** (demand − wind − solar): the
energy-only residual is monotone in the net-load percentile (≈0 below p50,
+4.7 at p90, +33 at p99; rho(load, actual) = 0.52; 56% of actual ≥$75 h sit
in the top load decile). So the adder is keyed on net load — a reduced-form
reserve-demand curve, the PJM analogue of ERCOT's reliability-deployment
offset, anchored to PJM's administrative reserve **penalty factors**, not a
physically-derived LOLP.

### Curve and calibration

`adder = penalty_max · clip((nl − onset_frac·peak_nl)/(peak_nl −
onset_frac·peak_nl), 0, 1)^exponent`, per year (self-normalising across load
growth). `PJM_SCARCITY_CURVE` = onset_frac **0.82**, penalty_max **$220**,
exponent **1.4**, calibrated against the hub-mean hourly RT actuals. The $220
peak adder is a deliberately conservative *typical-scarcity* anchor — below
PJM's Synchronized-Reserve penalty-factor cap (~$850/MWh historically; raised
under the Oct-2022 Energy Price Formation reform) — so it reproduces routine
afternoon scarcity and intentionally leaves the rare deep spikes on the table
(actual 2024/2025 max $439/$1,722).

Result on the `pjm_26` keeper (energy-only → +overlay):

| year | annual resid | Jul/Aug resid | monthly MAE | >$200 h (act/eo/ov) |
|---|---|---|---|---|
| 2023 | −0.86 → **+0.29** | −6.24 → **−1.10** | 3.59 → 2.69 | 6 / 0 / 9 |
| 2024 | −2.98 → **−0.72** | −8.82 → **+1.57** | 3.58 → 2.42 | 18 / 0 / 21 |
| 2025 | −8.62 → **−7.19** | −11.25 → **−6.52** | 8.61 → 7.22 | 59 / 0 / 14 |

The afternoon ramp is the fix: 2024 hour-of-day residual hour 15 −20.9 →
+0.2, hour 16 −35.4 → −5.8, hour 17 −40.4 → −1.5.

### Known limitations

1. **Evening overshoot (18:00–20:00).** Net load peaks ~1–2 h *after* the
   actual price peak (load still high, solar gone), so the curve over-lifts
   the early evening: 2024 hour-18/19/20 residual +12.9/+26.7/+19.5. Intrinsic
   to a net-load-only proxy; a v2 ramp/solar-aware coincidence weighting would
   refine it. Note this **compounds with the measured-interchange evening
   overshoot** (J3a interchange A/B), so the two fixes must be re-balanced
   together, not stacked naively.
2. **2025 broad level miss survives.** 2025 is under in *every* month
   (−4 to −22), not just the peak — a level/fuel-basis issue the scarcity
   overlay correctly does **not** paper over.

## J3b status (CAMPD unit-level coverage)

Blocked on uploads: `inputs/raw-data/campd-unit-level/` still has **no
MD/DE/NC/TN extracts and only MI 2024**. TN is now in
`campd.ISO_STATES["PJM"]`, so once `{MD,DE,NC,TN,MI}_{year}.parquet` land,
regenerate with:

```bash
python scripts/derive_campd_unit_outages.py --iso PJM --years 2023 2024 2025
```
