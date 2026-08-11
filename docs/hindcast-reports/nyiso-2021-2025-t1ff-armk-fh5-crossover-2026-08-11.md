# T1-X crossover — NYISO (nyiso-2021-2025-t1ff-armk-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-08-nyiso-132-cf-arm`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 12.658 | 7.676 | 1.65 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 16.639 | 3.303 | 5.04 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +25.7% | +8.8% | 2.93 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +0.3% | +0.7% | 0.37 | PASS |
| C3a system load-weighted mean LMP | 2025 | +41.1% | +3.5% | 11.90 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.316 | 0.130 | 2.43 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.284 | 0.172 | 1.65 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.540 | 0.155 | 3.48 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +15.3% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +20.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +26.4% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 50.672 | 58.505 | +13.4% | +0.5% | 27.90 | yes |
| `gas_twh` | 2024 | 50.063 | 65.497 | +23.6% | +2.1% | 11.33 | yes |
| `gas_twh` | 2025 | 47.195 | 67.736 | +30.3% | +3.1% | 9.62 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2023: family not benchmarked for this ISO
- coal_twh 2024: family not benchmarked for this ISO
- coal_twh 2025: family not benchmarked for this ISO

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.711 | 1.036 | -39% | FAIL |
| unit recall >300MW | 1 units | 1 matched | 100% | PASS |
| total additions | — | 6.601 GW | (actual 3.375 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **1 of 1** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
