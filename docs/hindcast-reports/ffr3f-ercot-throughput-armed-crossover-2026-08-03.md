# T1-X crossover — ERCOT (ffr3f-ercot-throughput-armed)

_Generated 2026-08-03 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-02-ercot150b-zonal-anchor`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 85.558 | 8.258 | 10.36 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 85.815 | 6.571 | 13.06 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.331 | 26.69 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +68.5% | +32.6% | 2.10 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +42.0% | +1.7% | 25.32 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +22.9% | +8.2% | 2.77 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.166 | 0.607 | 1.92 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.479 | 0.199 | 2.41 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.244 | 0.106 | 2.30 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.9% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +41.0% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +50.7% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 169.378 | 194.218 | +12.8% | +0.0% | 1279.00 | yes |
| `gas_twh` | 2024 | 187.086 | 199.716 | +6.3% | +0.5% | 12.90 | yes |
| `gas_twh` | 2025 | 151.176 | 191.266 | +21.0% | +0.0% | 1048.00 | NO — reported only |
| `coal_twh` | 2023 | 39.96 | 60.42 | +33.9% | +3.5% | 9.65 | yes |
| `coal_twh` | 2024 | 31.855 | 57.617 | +44.7% | +1.8% | 25.26 | yes |
| `coal_twh` | 2025 | 85.218 | 62.214 | +37.0% | +3.8% | 9.86 | yes |

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
| total additions | — | 10.356 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
