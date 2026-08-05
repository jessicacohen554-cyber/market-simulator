# T1-X crossover — ERCOT (ercot-2021-2025-t1ff-armr-ffr5d-unified)

_Generated 2026-08-05 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-05-run168b-year-curves`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 87.986 | 11.278 | 7.80 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 97.080 | 6.457 | 15.04 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.392 | 26.01 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +69.0% | +32.2% | 2.14 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +45.3% | +3.3% | 13.65 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +28.7% | +7.2% | 3.97 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.167 | 0.604 | 1.93 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.509 | 0.206 | 2.47 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.301 | 0.096 | 3.13 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +46.0% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +40.0% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +50.8% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 169.224 | 194.218 | +12.9% | +1.5% | 8.64 | yes |
| `gas_twh` | 2024 | 192.941 | 199.716 | +3.4% | +0.0% | 84.75 | yes |
| `gas_twh` | 2025 | 151.911 | 191.266 | +20.6% | +0.5% | 41.16 | NO — reported only |
| `coal_twh` | 2023 | 39.954 | 60.42 | +33.9% | +0.2% | 188.17 | yes |
| `coal_twh` | 2024 | 30.64 | 57.617 | +46.8% | +1.6% | 28.55 | yes |
| `coal_twh` | 2025 | 81.796 | 62.214 | +31.5% | +3.8% | 8.20 | yes |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `shape` — C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.534 | 10.943 | +614% | FAIL |
| unit recall >300MW | 3 units | 0 matched | 0% | FAIL |
| total additions | — | 17.0 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
