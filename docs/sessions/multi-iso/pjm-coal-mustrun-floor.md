# PJM coal must-run floor — audit and refutation as the coal-over lever

**Date:** 2026-06-21.
**Baseline:** `pjm_37` keeper (config = `pjm_28` + forecast-grade reference-price
interchange seam + neighbor price-vs-load convexity + within-window retiree CEMS
cap). Re-solved 2025 (the confound-free year — zero within-window retirees) as
`pjm_38base_2025`; reproduces the keeper exactly: coal-tot +8.7%, BIT +7.8%,
PRB +27.4%, gas +3.0% PASS, nuclear −0.6%, LMP −11.8%, interchg +28.2%.
**Question:** is the operable-coal must-run floor the lever for the ~+8.7%
(~+12 TWh) coal over-generation (prior-session probe #1 / finding #4)?
**Answer:** **No.** The floor is already CEMS-measured, it is *non-binding* in
the production config, and the over is a broad merit-order level shift, not a
floor-shape artifact. Detail below.

## 1. The PJM coal must-run floor is already a measured CEMS minimum

`fleet.COAL_MUSTRUN_BY_PLANT` is **ERCOT-only** (10 hand-curated TX plants); no
PJM plant is in it, so the `config.coal_mustrun_per_plant` branch in
`bins_to_fleet` / `split_coal_tranches` never fires for PJM. PJM coal `pct_mr`
comes from `thermal_tranches_PJM.csv` (`mustrun_pct`), written by
`scripts/derive_thermal_tranches.py`:

> `mustrun = min(P5(available-CF over ALL hours), 0.60)`  (line ~449)

i.e. each plant's 5th-percentile output as a fraction of its outage-adjusted
available capacity, pooled over 2023–25, capped at 60%. This **is** the
"CEMS-observed minimum sustained output per plant" probe #1 proposed to build —
it already exists. Cap-weighted PJM coal `mustrun_pct` ≈ 43.6%; cyclers
self-derive ~0 (Brandon Shores, Kincaid, Seward = 0.0), genuine baseload high
(Harrison/Cardinal/Keystone at the 60 cap). Deriving a new per-plant CEMS
min-gen floor would reproduce this artifact — a no-op.

## 2. The floor is NON-BINDING in the production config (`commitment=False`)

The keeper runs the energy-only LP (`commitment=False`; confirmed in
`pjm_28/run_config.json`). In that path **coal carries no forced min_gen**:

- The coal `_mustrun` tranche is created with `pmin_mw=0.0`
  (`fleet.py` ~5332/5348); `must_run_pct` is set only on the `_committed`
  tranche and is consumed **only in `commitment.py`** (warm-boiler start
  exemption), which does not run when commitment is disabled.
- The `min_gen` forcing in `generators_to_fleet_arrays` (~1204–1390) covers
  export sinks, ST_GAS summer floors, CHP grid steam, and CT/RD reliability
  deployment — **never coal**.

So the coal "mustrun" band is simply the **cheapest cost band** of the coal
offer curve (lowest heat-rate tranche), dispatched purely economically.
Measured directly in the 2025 dispatch:

| coal `_mustrun` band (fleet) | value |
|---|---|
| MW at fleet trough vs cap | 4,904 / 14,862 = **33%** |
| unit-hours running < 99% of unit cap | **65.4%** |
| unit-hours at ~zero | **18.9%** |

A forced floor would sit pinned at its cap; this band backs down to a third of
cap and goes dark a fifth of the time. **"Must-run" is a misnomer here.**

Corollary — `pct_mr` is nearly dispatch-neutral: the coal band heat-rate
multipliers are `mr=1.0, committed=1.15, econ=1.0, peak=1.05`
(`_DEFAULT_HR_MULT_BY_GROUP["COAL"]`). The must-run and econ bands are priced
**identically** (×1.0), so moving capacity between them by changing `pct_mr`
leaves the merit order unchanged; only the (smaller) committed ×1.15 band
differs. Tuning `pct_mr` to the residual would be an offer-curve cost edit on a
fraction of capacity — i.e. curve-fitting — for a bounded effect.

## 3. The over is a uniform merit-order level shift, not a floor artifact

2025 model coal by tranche (TWh): mustrun 77.8, committed 56.9, econ 13.4,
peak 1.3 — total 149.4 vs CEMS net 137.5 (**+11.9 TWh**).

CEMS-net vs model hourly coal **duration curve** (GW, CEMS unit-level
`grossLoad` summed over the 28 PJM coal plants × 0.97 parasitic):

| pctile | p1 | p5 | p25 | p50 | p75 | p95 | p99 | min | max |
|---|---|---|---|---|---|---|---|---|---|
| CEMS  | 6.5 | 8.1 | 10.9 | 13.5 | 18.8 | 25.9 | 28.1 | 5.6 | 29.8 |
| model | 8.0 | 9.6 | 11.9 | 15.1 | 21.6 | 28.7 | 30.7 | 7.0 | 32.0 |

The model sits **+1.0 to +2.8 GW above CEMS at every percentile** — a broad
level shift, not a tail/floor divergence.

Over attributed by **CEMS-coal decile** (decile 0 = lowest-coal hours, where a
too-high floor would concentrate the error):

| decile | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| over (TWh) | 1.48 | 1.06 | 0.58 | 0.74 | 0.49 | 0.93 | **1.76** | **1.76** | **1.87** | 1.20 |

The over is spread across all deciles and is **largest in the high-load hours
(6–8), not the cheap hours (0)**. By hour-of-day the over is a flat +1.7…+2.4 GW
(model day/night peakiness 1.10 vs CEMS 1.14 — the model is, if anything,
slightly *too flat*, but the effect is small). A floor forcing coal on through
cheap hours would put the over in decile 0 / overnight; the data shows the
opposite weighting.

## Reading

- **Probe #1's premise is refuted.** There is no forced coal must-run floor in
  the production PJM config, and the must-run band already backs to zero
  economically. The +8.7% coal over is a merit-order outcome — operable coal
  clears ~+2 GW too much in essentially every hour — not a baseload-floor
  artifact. Lowering or re-deriving the floor cannot fix it (and `pct_mr` is
  ~dispatch-neutral because the mustrun and econ bands are co-priced).
- **The floor-shaped residual is tiny.** Even at the bottom of the curve the
  model floor is only ~+1.5 GW high; decile 0 carries +1.48 TWh of the 11.9.
  Letting coal dip the last ~1.4 GW in the cheapest hours is a *commitment /
  cycling-cost* effect (coal declining marginal MWh in negative-/low-price
  hours), worth ≲0.7 TWh — not the frontier, and out of this branch's scope.
- **The real coal-over co-occurs with the over-export.** 2025: coal +11.9, gas
  +10.7, net-export **+5.1 TWh (+28%)**. The PJM thermal stack clears too cheap
  against its neighbors, so PJM over-generates and over-exports, the export
  served by the cheapest unit (coal). The prior session flagged the over-export
  as **forecast-native** (single MISO heat rate 12.9 > measured 12.5/12.2) and
  not fixable without breaking forecastability; a material share of the coal
  over rides on it. Heat rate is also refuted as the coal lever (prior
  finding #3: Homer City measured ~10.2 < model ~12, so the model already
  over-prices coal yet over-runs it — the pressure is on the gas/export side,
  not coal cost).

## Recommendation

Do **not** ship a coal must-run-floor change for the coal-over — the lever does
not exist in the production config, and any `pct_mr`/band-cost edit tuned to the
residual is curve-fitting (claude.md #1/#11). The next structurally-honest
levers, in priority:

1. **Price formation (`pjm-lmp-residual.md`).** The same cheap coal flooring the
   stack suppresses the afternoon $75–200 regime (LMP −11.8%); the overnight
   +$2–6 overshoot is the broad over-commitment. Treat coal-over and LMP-under
   as one defect on the supply-cost/commitment side.
2. **Over-export structural acceptance / neighbor seam.** Quantify how much of
   the coal over is the forecast-native MISO-HR over-export before attributing
   any of it to PJM-internal coal cost.

This run produced **no keeper** — there is no faithful change that improves the
coal residual, which is the correct outcome under the "structural faithfulness,
not lowest MAE" rule.

## Reproduce

```bash
# baseline (confound-free year)
uv run python scripts/probes/_pjm_retiree_run.py 2025 results/calibration/pjm_38base_2025
uv run python scripts/probes/_pjm_aswh_merge.py results/calibration/pjm_38base \
    results/calibration/pjm_38base_2025
uv run python scripts/probes/_pjm_score.py pjm_38base
# the tranche / duration-curve / decile diagnostics were run ad hoc against
# results/calibration/pjm_38base_2025/dispatch/2025_P1.parquet and the PJM
# coal plants in data/raw/campd-unit-level/<ST>_2025.parquet.
```
