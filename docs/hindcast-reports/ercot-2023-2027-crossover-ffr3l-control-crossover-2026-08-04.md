# T1-X crossover — ERCOT (ercot-2023-2027-crossover-ffr3l-control)

_Generated 2026-08-04 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-03-ercot158-pool-arm`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 98.815 | 8.198 | 12.05 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 91.183 | 6.279 | 14.52 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.346 | 26.52 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +68.7% | +32.8% | 2.09 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +45.9% | +1.8% | 24.80 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +26.9% | +8.1% | 3.32 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.163 | 0.610 | 1.91 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.514 | 0.199 | 2.58 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.283 | 0.105 | 2.69 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +49.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +46.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +53.0% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 156.101 | 194.218 | +19.6% | +0.0% | 981.50 | yes |
| `gas_twh` | 2024 | 167.35 | 199.716 | +16.2% | +0.3% | 50.66 | yes |
| `gas_twh` | 2025 | 143.077 | 191.266 | +25.2% | +0.1% | 229.00 | NO — reported only |
| `coal_twh` | 2023 | 39.243 | 60.42 | +35.0% | +3.6% | 9.79 | yes |
| `coal_twh` | 2024 | 29.716 | 57.617 | +48.4% | +1.6% | 30.46 | yes |
| `coal_twh` | 2025 | 78.62 | 62.214 | +26.4% | +3.8% | 7.00 | yes |

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
| total additions | — | 16.356 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 159.5725 | 293.9 | True | True |
| 2027 | 149.4916 | 330.346 | True | True |
