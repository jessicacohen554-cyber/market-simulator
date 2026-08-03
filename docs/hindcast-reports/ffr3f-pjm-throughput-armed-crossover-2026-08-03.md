# T1-X crossover — PJM (ffr3f-pjm-throughput-armed)

_Generated 2026-08-03 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-03-pjm-147b-chp-heat`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 146.851 | 12.007 | 12.23 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 173.451 | 9.205 | 18.84 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +2.1% | +6.6% | 0.32 | PASS |
| C3a system load-weighted mean LMP | 2024 | +8.0% | +0.2% | 49.69 | PASS |
| C3a system load-weighted mean LMP | 2025 | +18.5% | +7.2% | 2.56 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.106 | 0.162 | 0.65 | PASS |
| C3b monthly price NRMSE | 2024 | 0.169 | 0.118 | 1.43 | PASS |
| C3b monthly price NRMSE | 2025 | 0.224 | 0.135 | 1.66 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +46.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +41.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +59.2% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 356.954 | 364.529 | +2.1% | +0.4% | 5.20 | yes |
| `gas_twh` | 2024 | 399.435 | 381.906 | +4.6% | +1.1% | 4.17 | yes |
| `gas_twh` | 2025 | 300.241 | 377.254 | +20.4% | +3.0% | 6.87 | NO — reported only |
| `coal_twh` | 2023 | 108.769 | 112.471 | +3.3% | +0.4% | 7.65 | yes |
| `coal_twh` | 2024 | 93.936 | 115.195 | +18.5% | +0.5% | 33.56 | yes |
| `coal_twh` | 2025 | 203.419 | 136.864 | +48.6% | +4.7% | 10.37 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT, COAL_PRB, COAL_WC] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `shape` — C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 11.121 | 0.057 | -100% | FAIL |
| unit recall >300MW | 17 units | 0 matched | 0% | FAIL |
| total additions | — | 0.01 GW | (actual 24.092 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
