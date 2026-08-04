# T1-X crossover — ERCOT (ercot)

_Generated 2026-08-03 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-02-ercot150b-zonal-anchor`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 98.815 | 8.258 | 11.97 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 79.982 | 6.571 | 12.17 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.331 | 26.69 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +68.7% | +32.6% | 2.11 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +41.2% | +1.7% | 24.85 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +22.5% | +8.2% | 2.73 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.163 | 0.607 | 1.92 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.471 | 0.199 | 2.37 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.241 | 0.106 | 2.27 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +49.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +42.7% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +50.6% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 156.101 | 194.218 | +19.6% | +0.0% | 1963.00 | yes |
| `gas_twh` | 2024 | 179.769 | 199.716 | +10.0% | +0.5% | 20.39 | yes |
| `gas_twh` | 2025 | 151.552 | 191.266 | +20.8% | +0.0% | 1038.00 | NO — reported only |
| `coal_twh` | 2023 | 39.243 | 60.42 | +35.0% | +3.5% | 9.99 | yes |
| `coal_twh` | 2024 | 32.233 | 57.617 | +44.1% | +1.8% | 24.89 | yes |
| `coal_twh` | 2025 | 85.36 | 62.214 | +37.2% | +3.8% | 9.92 | yes |

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
| total additions | — | 8.356 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 166.455 | 308.112 | True | True |
| 2027 | 175.3969 | 353.115 | True | True |
