# T1-X crossover — ERCOT (ercot-2023-2025-t1ff-armr-fh4gate)

_Generated 2026-08-09 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-09-run181-position-tail`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 99.383 | 11.276 | 8.81 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 115.342 | 6.457 | 17.86 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.392 | 26.01 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +65.1% | +32.5% | 2.01 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +14.9% | +2.5% | 6.00 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +13.6% | +8.0% | 1.69 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.137 | 0.602 | 1.89 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.682 | 0.205 | 3.33 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.162 | 0.101 | 1.60 | PASS |
| C5a system CO2 (full-plant basis) | 2023 | +35.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +27.6% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +35.4% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 208.276 | 194.218 | +7.2% | +1.5% | 4.86 | yes |
| `gas_twh` | 2024 | 234.733 | 199.716 | +17.5% | +0.0% | 438.25 | yes |
| `gas_twh` | 2025 | 206.669 | 191.266 | +8.1% | +0.5% | 16.10 | NO — reported only |
| `coal_twh` | 2023 | 48.264 | 60.42 | +20.1% | +0.2% | 111.78 | yes |
| `coal_twh` | 2024 | 39.087 | 57.617 | +32.2% | +1.6% | 19.61 | yes |
| `coal_twh` | 2025 | 91.927 | 62.214 | +47.8% | +3.8% | 12.44 | yes |

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
| thermal GW retired | 2.294 | 0.0 | -100% | FAIL |
| unit recall >300MW | 0 units | 0 matched | n/a | SKIP |
| total additions | — | 28.011 GW | (actual 55.436 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2023-12-31**). Members: **0 of 2** target rows >=300 MW — recall **n/a** (never 0/N): no target exit >= 300 MW is reachable by an admissible channel on this run's fleet basis — reported n/a, never 0/N (D-24).

**Unreachable exits — NON-GATED diagnostic** (5 rows, 2 of them >=300 MW and therefore out of the denominator). Nothing here bands:

| unit | MW | fuel | exit | driver | why unreachable | gated |
|---|--:|---|--:|---|---|:--|
| `56611_S01` Sandy Creek 1 | 1008.0 | coal | 2025 | not margin-driven (exit decode); no confirmed-registry instrument exists | no_instrument — no admissible channel — economic screen must not retire it (primary-year margin 73.41 vs bar 58.5 $/kW-yr in 2024 (unit_net), bar-invariant), and no confirmed-registry instrument exists | yes |
| `3548_2` Decker Creek 2 | 405.0 | gas_st | 2022 | not margin-driven (exit decode); no confirmed-registry instrument exists | not_in_fleet_basis — ABSENT (3548 carries only CT8, CT_PEAKER 206.0 MW) — no screen can retire capacity the run's fleet never carried | yes |
| `3612_2` V H Braunig 2 | 252.0 | gas_st | 2025 | confirmed instrument ercot-nso-braunig-2 (rto_deactivation, instrument_date 2024-03-13) | post_vintage_instrument — no admissible channel — economic screen must not retire it (primary-year margin 63.35 vs bar 35.0 $/kW-yr in 2024 (unit_net), bar-invariant), and its only instrument (ercot-nso-braunig-2, 2024-03-13) post-dates the vintage cutoff 2023-12-31 | no (below size threshold) |
| `3612_1` V H Braunig 1 | 225.0 | gas_st | 2025 | confirmed instrument ercot-nso-braunig-1 (rto_deactivation, instrument_date 2024-03-13) | post_vintage_instrument — no admissible channel — economic screen must not retire it (primary-year margin 69.74 vs bar 35.0 $/kW-yr in 2024 (unit_net), bar-invariant), and its only instrument (ercot-nso-braunig-1, 2024-03-13) post-dates the vintage cutoff 2023-12-31 | no (below size threshold) |
| `52120_G-66` Freeport Energy G-66 | 119.0 | gas_cc | 2023 | not margin-driven (exit decode); no confirmed-registry instrument exists | no_instrument — no admissible channel — economic screen must not retire it (primary-year margin 176.44 vs bar 30.0 $/kW-yr in 2022 (class_proxy), bar-invariant), and no confirmed-registry instrument exists | no (below size threshold) |

_Evidence, per unit: FFR-7C §2.2 (per-unit margin table) / §2.4 (fleet-basis facts) — docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md; `data/raw/confirmed-retirements/ercot.csv`. Excludes only on positive, cited evidence; a unit with no evidence either way stays in the member set._

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
