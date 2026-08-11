# T1-X crossover — ERCOT (ercot-2021-2025-t1ff-armk-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-09-ercot185-shaped-partial`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 96.898 | 11.211 | 8.64 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 101.768 | 6.634 | 15.34 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.454 | 25.35 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +57.9% | +32.5% | 1.78 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +21.8% | +1.4% | 15.34 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +32.4% | +7.9% | 4.08 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.101 | 0.602 | 1.83 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.342 | 0.160 | 2.14 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.339 | 0.101 | 3.36 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +36.4% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +37.5% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +43.4% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 203.585 | 194.218 | +4.8% | +1.5% | 3.32 | yes |
| `gas_twh` | 2024 | 201.426 | 199.716 | +0.9% | +0.1% | 6.14 | yes |
| `gas_twh` | 2025 | 179.087 | 191.266 | +6.4% | +0.6% | 10.11 | NO — reported only |
| `coal_twh` | 2023 | 67.22 | 60.42 | +11.2% | +0.3% | 36.29 | yes |
| `coal_twh` | 2024 | 58.312 | 57.617 | +1.2% | +1.4% | 0.86 | yes |
| `coal_twh` | 2025 | 65.936 | 62.214 | +6.0% | +3.9% | 1.52 | yes |

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
| thermal GW retired | 2.294 | 0.354 | -85% | FAIL |
| unit recall >300MW | 0 units | 0 matched | n/a | SKIP |
| total additions | — | 32.947 GW | (actual 55.436 GW) | — |

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
