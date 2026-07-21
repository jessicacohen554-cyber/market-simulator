# FF-3H -- Probability-bounds band machinery, T1 exercise (findings)

**Session:** FF-3H (L-PB lane). **Date:** 2026-07-21. **Model:** Opus.
**Scope:** exercise the landed PB machinery at a T1 window to prove it emits
fan-chart bands end-to-end. **NOT** the PB-5 production band run (deferred behind
the sec. 2.1b full-solve gate -- plan sec. 2.1b, gap-register G-35). No
full-horizon solve.

## TL;DR

The PB sampler -> solve -> aggregate -> bands -> export -> fan-chart-page path
**runs end-to-end at T1**, once **one plumbing gap is fixed**: the ensemble band
aggregation hardcoded the full 2026-2050 horizon, so any sub-2050 (T1) ensemble
**crashed at aggregation** with `FileNotFoundError` on the first unsolved year.
Fixed to derive the horizon from the run's own config. A real 5-draw ERCOT
2026-2030 fan now emits `bands.parquet` and publishes to the forecast-bands page
(`ercot-pb-bands-t1`). The sampler is reproducibly seeded and the band
percentiles are exactly numpy Hyndman-Fan type-7 on the fan. No band widening, no
tuning (rules 1/6).

## What runs end-to-end at T1 vs. what only the gated PB-5 run can produce

| Capability | T1 (this session) | PB-5 (gated, sec. 2.1b) |
|---|---|---|
| Sampler (LHS + Gaussian copula, seeded, reproducible) | YES verified | same machinery, n=64 |
| Per-member forecast solve (real HiGHS) | YES 5 members x 2026-2030 | 64 members x 2026-2050 |
| Horizon-aware band aggregation (`_member_metric_values`) | YES **fixed here** | (was OK only because full-horizon members hit every year) |
| `bands.parquet` parametric layer (P10/P50/P90 + bootstrap CI + n) | YES | YES statistically meaningful |
| `export_forecast_bands.py` -> page payload + manifest + markdown | YES `ercot-pb-bands-t1` | YES |
| `forecast-bands.html` consumes it (banners, fan, table) | YES verified (inflates to the JS contract) | YES |
| Published band (parametric (+) D-7 structural prior, PB-3) | PARTIAL: convolution machinery verified via inline `fit_prior`; `default_prior()` blocked (see sec. 6) | YES (needs committed statmode payloads) |
| Scenario-matrix envelope (PB-0, 13 named cases) | NO (separate deferred artifact) | YES |
| Statistical content (n large enough for a real quantile) | NO -- n=5 has none, machinery proof only | YES n=64, bootstrap-CI-quantified (plan sec. 2.4) |

## 1. The plumbing gap (found + fixed)

**Symptom.** `market_sim.ensemble._member_metric_values` and `summarize_ensemble`
iterated `range(START_YEAR, END_YEAR + 1)` -- the **module constants 2026-2050** --
regardless of the run's horizon. `cache.load_result` raises `FileNotFoundError`
on a missing year, so a member solved only over a T1 window has no cache past its
`end_year` and the aggregation crashes:

```
FileNotFoundError: no cached result for iso=ERCOT cache_key=... year=2031 ...
```

The full-horizon PB-5 attempts (the 2026-07-12 partial exercise, e.g.
`ercot-pb5-band-v2`, n=16 over 2026-2050) never hit this **only because their
members solved every year 2026-2050**, matching the hardcoded range. A T1 window
(<=5 solve-years) is exactly what exposes it. Confirmed by a no-solve repro
(short-horizon fake cache) before any solve time was spent.

**Fix.** `src/market_sim/ensemble.py` now derives the aggregation horizon from the
run's config (`_config_year_range`, mirroring `runner.evolve_fleet`; and
`_members_year_range`, which reads it back from a member's cached config).
`export_sampler_ensemble` threads the authoritative `base_config` range in. At the
default (`start_year=end_year=None`) horizon the range resolves to 2026-2050 --
**byte-identical to the prior behaviour**, so the full-horizon PB-5 path and every
existing test are unchanged.

**Regression tests** (`tests/test_ensemble_sampler.py`): `TestConfigYearRange`
(None -> module default; explicit bounds honoured) and
`TestShortHorizonAggregation` (a 2026-2028 ensemble aggregates over its own 3
years, not 2026-2050, and asserts the sampler preserves the base horizon on every
member). Full sampler suite 14/14 green; `ruff check`/`format` clean.

This is the *only* code change. No band width, no offer curve, no sampler
distribution was touched (rules 1/6/23).

## 2. What was run (the T1 fan)

- **ISO / mode / horizon:** ERCOT, `mode="forecast"`, **2026-2030**
  (`start_year`/`end_year` set), `use_campd_bins=False` (legacy heat-rate bins --
  the same structural config the forecast golden pins; bounds memory/time).
- **Sampler:** committed `configs/uncertainty_ercot.yaml`, **n=5** draws,
  **seed=7** (`spec_hash=931f75492daf6ede`, `gas_sigma_reference=0.8431`). Layer
  emitted: **parametric only** (PB-2 default).
- **Real default config:** `confirmed_exits_enabled=True` (registry regenerated,
  sec. 6) -- not a degraded run.
- **sec. 2.1b compliance:** each member is one T1-F invocation over 2026-2030 =
  **5 solve-years, at the per-invocation cap**; years sequential; workers=2
  (<=2 concurrent, rule 12).
- **Bundle (local, regenerable):**
  `results/ensemble/ercot-pb-bands-t1/{draws,metrics,bands}.parquet` +
  `ensemble_meta.json` + `bands_summary.md`. The binary parquet is not committed
  (regenerable at seed=7 via the driver below); the committed page payload embeds
  the full band data.
- **Registered (existing path):** `scripts/export_forecast_bands.py` ->
  `frontend/data/forecast/ercot-pb-bands-t1.js` + `manifest.json`.
  `register_hindcast.py` untouched (FF-5A owns it). Forecast namespace only -- the
  backcast CI gates stay blind to it (rule 11 / plan sec. 7.5).

The five draws span gas 0.30-2.64x, load percentile 0.001-0.93, weather
2021/2023/2024/2025, hydro dry/normal/wet, policy current/tight/rollback -- so the
fan reflects genuine input-uncertainty spread, e.g. emissions_mt (Mt CO2):

| Year | P10 | P50 | P90 |
|---|---|---|---|
| 2026 | 145.4 | 184.1 | 224.3 |
| 2028 | 178.0 | 209.0 | 260.6 |
| 2030 | 210.1 | 259.9 | 302.7 |

**These levels are uncalibrated forecast output and are NOT quoted as a forecast**
-- n=5 has no statistical content; this is a machinery proof (disclosed in the
run's `honest_limitations`).

Reproduce recipe (deterministic): base config `ScenarioConfig(iso="ERCOT",
mode="forecast", start_year=2026, end_year=2030, use_campd_bins=False)`; spec =
`configs/uncertainty_ercot.yaml` with `n=5`; `run_sampler_ensemble(base, spec,
iso="ERCOT", workers=2, out_dir=results/ensemble/ercot-pb-bands-t1)` then
`scripts/export_forecast_bands.py`. Run with `PYTHONPATH=.` (see sec. 7b).

## 3. Reproducibility + band-aggregation correctness (task item 2)

All checks pass on the **real T1 fan** (no new solves):

- **Seeded, reproducible sampler:** two `sample_draws(spec)` calls are
  bit-identical; the committed `draws.parquet` reproduces from `(spec, seed)`
  alone -- no wall-clock / unseeded-random leakage
  (`scipy.stats.qmc.LatinHypercube(seed=...)`; no Date.now/random pitfalls).
- **Band aggregation is exactly HF7:** every `bands.parquet` parametric value
  equals a hand `np.quantile(members, q, method="linear")` recomputed from
  `metrics.parquet` -- **max |delta| = 0.00** across all (year, metric, quantile).
- **Pure recompute parity:** `ensemble.bands_from_metrics` (the sec. 4.1
  metrics-only recompute the page path relies on) reproduces the committed bands.
- **n and horizon:** every band row carries `n=5`; years are exactly 2026-2030
  (the fix working end-to-end on real data).

## 4. End-to-end page-consumption check

The published `ercot-pb-bands-t1.js` inflates (gzip+base64) to precisely the
payload `js/viz-forecast-bands.js` reads: `iso=ERCOT`, `n_draws=5`,
`synthetic=false` (no synthetic banner), `dispatch_conditional=true` (the
fleet-path caveat banner fires), `layers_present=["parametric"]`, 18 metrics,
quantile keys `"0.1"/"0.5"/"0.9"`, and the five run-declared `honest_limitations`
banners. `manifest.json` now lists `ercot-pb-bands-t1` alongside the synthetic
fixture. No matrix => the envelope/case toggles correctly stay hidden.

## 5. `golden_forecast_bands.py` at T1

Its solve->metric->band-check **logic** is exercised at zero extra solve by
driving `compute_metrics` + `check_bands` on a cached T1 member run (`load_run`):
the five banded quantities extract over 2026-2030, `check_bands(m, m)`
self-consistency is clean, and a +50% CO2 perturbation is detected. **The
committed `check` itself is NOT a T1 instrument:** its pinned
`REFERENCE_SCENARIO_KWARGS` solve ERCOT **2026-2040 = 15 solve-years in a single
invocation**, which **exceeds the sec. 2.1b <=5-solve-year per-invocation cap**.
It is runnable only in its weekly CI tier or under an explicit full-solve
authorization -- its solve path is the same `run_scenario_iso` the T1 ensemble
already exercises.

## 6. What only the gated PB-5 run can produce (task item 4)

Everything below is **deferred behind the sec. 2.1b full-solve gate** and out of
scope here:

1. **A statistically meaningful band.** n=64 LHS draws over the full 2026-2050
   horizon (plan sec. 2.4/2.5), with the bootstrap CI making the sampling noise
   visible. n=5 here has none -- the P10/P90 are driven by the two extreme draws.
2. **The full 2026-2050 fan.** ~1.7-2.5 h/member x 64 / 2 concurrent ~= 2.7 days
   (plan sec. 5) -- a scheduled batch, not an interactive session.
3. **The published (parametric (+) structural) band via `default_prior()`.** The
   convolution *machinery* is verified here (inline `fit_prior` -> a
   `parametric_plus_structural` layer appears and the parametric P50 is unchanged,
   rule 13). But `default_prior()` reads the committed **D-7 statmode run
   payloads** (`frontend/data/backcast/runs/*statmode*.js`), which are **not
   tracked in the repo** (see sec. 7c), so the real published layer cannot be
   produced in a fresh checkout. PB-5 pairs the fitted prior with the real fan.
4. **The PB-0 scenario-matrix envelope** (13 named cases) and the combined
   three-claim chart.

## 7. Observations found in passing (NOT fixed -- out of scope for a plumbing session)

- **(a) `uncertainty_ercot.yaml`'s sigma comment is stale vs the current data.**
  The spec comment says `sigma_ref` resolves to ~0.464, but the current
  `constants.HENRY_HUB_TRAJECTORIES` 2050 case (low/mid/high =
  2.75/4.64/**13.67**) gives the AEO floor `ln(13.67/4.64)/1.2816 = 0.843`. The
  machinery is **correct**; the band width is the honest output of the committed
  data + spec and was **not** touched (rules 1/6/23). Recommend the spec author
  (or the AEO2026 API-pull task, PP-3.2(2)) reconcile the comment. Disclosed in
  the run's `honest_limitations`.
- **(b) `data/clean/confirmed-retirements` absent in a fresh checkout.**
  `data/clean` is derived/gitignored, and the confirmed-exit loader now **raises**
  (rather than the 2026-07-12 "inert/empty" degrade) when
  `confirmed_exits_enabled` is on. Fixed for this run by regenerating it
  (`scripts/data/curate_confirmed_retirements.py`, ERCOT: 2 live rows) so the
  **real default config** was solved. Environmental, not a code gap. (Solves must
  run with `PYTHONPATH=.` so `scripts.lib.clean_io` imports.)
- **(c) D-7 statmode run payloads untracked.** `tests/fixtures/backcast_runs/`
  carries only NEISO/NYISO/ERCOT32 statmode fixtures; CAISO/PJM/MISO are missing,
  and no `*statmode*.js` is tracked under `frontend/data/backcast/runs/`.
  Consequence: the **5 `tests/test_structural_prior.py` failures are
  pre-existing/environmental** (they reproduce with this session's `ensemble.py`
  change stashed) and `structural_prior.default_prior()` cannot fit in a fresh
  checkout. Unrelated to this session; flagged for a data-provisioning task.

## 8. Budget report (sec. 2.4, rule 5)

| Metric | Value |
|---|---|
| Probe (1 solve-year, workers=1) | 62.8 s wall, **1.43 GB** peak RSS |
| T1 fan total | **726 s** (12.1 min), 25 solve-years, **29.0 s/solve-year** @ workers=2 |
| Per invocation | 5 solve-years (= sec. 2.1b T1-F cap); <=2 concurrent; peak ~= 2.9 GB |
| Compute vs PB-5 | 25 solve-years ~= 1.6% of PB-5's 1600 (64x25) -- a machinery proof |

## 9. Artifacts

- **Code:** `src/market_sim/ensemble.py` (horizon-aware aggregation),
  `tests/test_ensemble_sampler.py` (regression).
- **Page data (committed):** `frontend/data/forecast/ercot-pb-bands-t1.js`,
  updated `frontend/data/forecast/manifest.json`.
- **Bundle (local/regenerable, not committed -- binary parquet):**
  `results/ensemble/ercot-pb-bands-t1/`.
- **Findings:** this doc.

Provenance: seed=7, n=5, `spec_hash=931f75492daf6ede`, ERCOT forecast 2026-2030,
`use_campd_bins=False`, `configs/uncertainty_ercot.yaml`.
