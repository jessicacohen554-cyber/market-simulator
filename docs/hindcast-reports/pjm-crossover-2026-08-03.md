# T1-X crossover — PJM (pjm)

_Generated 2026-08-03 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-03-pjm-147b-chp-heat`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 148.821 | 12.007 | 12.39 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 174.536 | 9.205 | 18.96 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +3.6% | +6.6% | 0.55 | PASS |
| C3a system load-weighted mean LMP | 2024 | +6.6% | +0.2% | 40.94 | PASS |
| C3a system load-weighted mean LMP | 2025 | +15.7% | +7.2% | 2.18 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.111 | 0.162 | 0.69 | PASS |
| C3b monthly price NRMSE | 2024 | 0.160 | 0.118 | 1.36 | PASS |
| C3b monthly price NRMSE | 2025 | 0.200 | 0.135 | 1.48 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +40.4% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +54.2% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 363.237 | 364.529 | +0.4% | +0.4% | 0.88 | yes |
| `gas_twh` | 2024 | 407.416 | 381.906 | +6.7% | +1.1% | 6.07 | yes |
| `gas_twh` | 2025 | 336.121 | 377.254 | +10.9% | +3.0% | 3.67 | NO — reported only |
| `coal_twh` | 2023 | 97.9 | 112.471 | +13.0% | +0.4% | 30.14 | yes |
| `coal_twh` | 2024 | 87.683 | 115.195 | +23.9% | +0.5% | 43.42 | yes |
| `coal_twh` | 2025 | 168.942 | 136.864 | +23.4% | +4.7% | 5.00 | NO — reported only |

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

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 349.6301 | 806.823 | False | True |
| 2027 | 357.881 | 838.387 | False | True |
