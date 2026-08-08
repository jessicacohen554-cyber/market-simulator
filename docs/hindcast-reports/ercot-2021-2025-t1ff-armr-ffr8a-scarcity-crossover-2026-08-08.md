# T1-X crossover — ERCOT (ercot-2021-2025-t1ff-armr-ffr8a-scarcity)

_Generated 2026-08-08 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-07-run176-control-offline-increment`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 87.650 | 11.278 | 7.77 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 87.330 | 6.457 | 13.53 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.392 | 26.01 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +69.2% | +32.5% | 2.13 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +47.2% | +2.5% | 19.02 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +29.3% | +8.0% | 3.66 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.168 | 0.602 | 1.94 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.524 | 0.205 | 2.56 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.306 | 0.101 | 3.03 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.9% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +42.6% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +50.9% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 169.311 | 194.218 | +12.8% | +1.5% | 8.60 | yes |
| `gas_twh` | 2024 | 182.506 | 199.716 | +8.6% | +0.0% | 215.50 | yes |
| `gas_twh` | 2025 | 151.735 | 191.266 | +20.7% | +0.5% | 41.34 | NO — reported only |
| `coal_twh` | 2023 | 39.802 | 60.42 | +34.1% | +0.2% | 189.56 | yes |
| `coal_twh` | 2024 | 29.919 | 57.617 | +48.1% | +1.6% | 29.31 | yes |
| `coal_twh` | 2025 | 81.967 | 62.214 | +31.8% | +3.8% | 8.27 | yes |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 2.294 | 6.501 | +183% | FAIL |
| unit recall >300MW | 0 units | 0 matched | n/a | SKIP |
| total additions | — | 17.0 GW | (actual 55.436 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **0 of 2** target rows >=300 MW — recall **n/a** (never 0/N): no target exit >= 300 MW is reachable by an admissible channel on this run's fleet basis — reported n/a, never 0/N (D-24).

**Unreachable exits — NON-GATED diagnostic** (5 rows, 2 of them >=300 MW and therefore out of the denominator). Nothing here bands:

| unit | MW | fuel | exit | driver | why unreachable | gated |
|---|--:|---|--:|---|---|:--|
| `56611_S01` Sandy Creek 1 | 1008.0 | coal | 2025 | not margin-driven (exit decode); no confirmed-registry instrument exists | no_instrument — no admissible channel — economic screen must not retire it (primary-year margin 73.41 vs bar 58.5 $/kW-yr in 2024 (unit_net), bar-invariant), and no confirmed-registry instrument exists | yes |
| `3548_2` Decker Creek 2 | 405.0 | gas_st | 2022 | not margin-driven (exit decode); no confirmed-registry instrument exists | not_in_fleet_basis — ABSENT (3548 carries only CT8, CT_PEAKER 206.0 MW) — no screen can retire capacity the run's fleet never carried | yes |
| `3612_2` V H Braunig 2 | 252.0 | gas_st | 2025 | confirmed instrument ercot-nso-braunig-2 (rto_deactivation, instrument_date 2024-03-13) | post_vintage_instrument — no admissible channel — economic screen must not retire it (primary-year margin 63.35 vs bar 35.0 $/kW-yr in 2024 (unit_net), bar-invariant), and its only instrument (ercot-nso-braunig-2, 2024-03-13) post-dates the vintage cutoff 2020-12-31 | no (below size threshold) |
| `3612_1` V H Braunig 1 | 225.0 | gas_st | 2025 | confirmed instrument ercot-nso-braunig-1 (rto_deactivation, instrument_date 2024-03-13) | post_vintage_instrument — no admissible channel — economic screen must not retire it (primary-year margin 69.74 vs bar 35.0 $/kW-yr in 2024 (unit_net), bar-invariant), and its only instrument (ercot-nso-braunig-1, 2024-03-13) post-dates the vintage cutoff 2020-12-31 | no (below size threshold) |
| `52120_G-66` Freeport Energy G-66 | 119.0 | gas_cc | 2023 | not margin-driven (exit decode); no confirmed-registry instrument exists | no_instrument — no admissible channel — economic screen must not retire it (primary-year margin 176.44 vs bar 30.0 $/kW-yr in 2022 (class_proxy), bar-invariant), and no confirmed-registry instrument exists | no (below size threshold) |

_Evidence, per unit: FFR-7C §2.2 (per-unit margin table) / §2.4 (fleet-basis facts) — docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md; `data/raw/confirmed-retirements/ercot.csv`. Excludes only on positive, cited evidence; a unit with no evidence either way stays in the member set._

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
