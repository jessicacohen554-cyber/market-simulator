# T1-X crossover — ERCOT (ercot-2021-2025-t1ff-armr-ffr5a-pipeline)

_Generated 2026-08-05 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-04-ercot165-unpooled-share`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 87.314 | 8.727 | 10.01 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 89.133 | 6.251 | 14.26 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.507 | 24.82 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +69.2% | +32.6% | 2.12 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +42.9% | +2.1% | 20.95 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +24.1% | +7.9% | 3.07 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.170 | 0.610 | 1.92 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.488 | 0.199 | 2.45 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.257 | 0.103 | 2.50 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +40.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +49.4% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 169.463 | 194.218 | +12.8% | +0.4% | 34.46 | yes |
| `gas_twh` | 2024 | 190.657 | 199.716 | +4.5% | +0.1% | 45.40 | yes |
| `gas_twh` | 2025 | 156.434 | 191.266 | +18.2% | +0.4% | 42.35 | NO — reported only |
| `coal_twh` | 2023 | 39.627 | 60.42 | +34.4% | +3.9% | 8.87 | yes |
| `coal_twh` | 2024 | 31.991 | 57.617 | +44.5% | +1.4% | 30.89 | yes |
| `coal_twh` | 2025 | 87.4 | 62.214 | +40.5% | +4.0% | 10.04 | yes |

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
| thermal GW retired | 1.534 | 0.0 | -100% | FAIL |
| unit recall >300MW | 3 units | 0 matched | 0% | FAIL |
| total additions | — | 27.0 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
