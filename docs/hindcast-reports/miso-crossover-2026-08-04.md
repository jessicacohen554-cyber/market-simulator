# T1-X crossover — MISO (miso)

_Generated 2026-08-04 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-03-miso-117b-ct-heat`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 233.161 | 18.588 | 12.54 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 235.945 | 19.234 | 12.27 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +13.6% | +1.0% | 14.02 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +13.9% | +6.3% | 2.21 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +27.4% | +14.1% | 1.95 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.173 | 0.074 | 2.34 | PASS |
| C3b monthly price NRMSE | 2024 | 0.236 | 0.114 | 2.07 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.300 | 0.190 | 1.58 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +63.3% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +58.9% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +75.5% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 218.25 | 199.309 | +9.5% | +5.5% | 1.74 | yes |
| `gas_twh` | 2024 | 238.382 | 207.1 | +15.1% | +3.0% | 5.07 | yes |
| `gas_twh` | 2025 | 144.412 | 194.461 | +25.7% | +8.0% | 3.22 | NO — reported only |
| `coal_twh` | 2023 | 187.628 | 185.787 | +1.0% | +1.7% | 0.60 | yes |
| `coal_twh` | 2024 | 173.528 | 176.316 | +1.6% | +1.4% | 1.16 | yes |
| `coal_twh` | 2025 | 284.453 | 212.156 | +34.1% | +0.1% | 309.82 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT, COAL_LIGNITE, COAL_PRB] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `shape` — C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 15.227 | 0.0 | -100% | FAIL |
| unit recall >300MW | 17 units | 0 matched | 0% | FAIL |
| total additions | — | 1.234 GW | (actual 31.981 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 349.4059 | 563.764 | True | True |
| 2027 | 341.0092 | 585.065 | True | True |
