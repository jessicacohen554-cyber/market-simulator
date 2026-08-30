# T1-X crossover — ERCOT (ercot-2023-2027-crossover-ffr2a)

_Generated 2026-08-02 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-01-ercot149-gas-event-cap`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 98.813 | 8.752 | 11.29 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 80.024 | 6.332 | 12.64 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.216 | 28.07 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +68.7% | +33.3% | 2.06 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +41.9% | +0.8% | 53.72 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +8.9% | +9.1% | 0.98 | PASS |
| C3b monthly price NRMSE | 2023 | 1.163 | 0.616 | 1.89 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.479 | 0.198 | 2.42 | FAIL |
| C3b monthly price NRMSE | 2025 | 1.129 | 0.112 | 10.08 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +49.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +42.7% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +51.2% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 156.104 | 194.218 | +19.6% | +0.2% | 122.62 | yes |
| `gas_twh` | 2024 | 179.785 | 199.716 | +10.0% | +0.1% | 66.53 | yes |
| `gas_twh` | 2025 | 152.24 | 191.266 | +20.4% | +0.1% | 136.00 | NO — reported only |
| `coal_twh` | 2023 | 39.24 | 60.42 | +35.0% | +2.9% | 11.88 | yes |
| `coal_twh` | 2024 | 32.192 | 57.617 | +44.1% | +2.3% | 19.27 | yes |
| `coal_twh` | 2025 | 85.928 | 62.214 | +38.1% | +3.6% | 10.71 | yes |

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
| thermal GW retired | 1.534 | 21.09 | +1275% | FAIL |
| unit recall >300MW | 3 units | 1 matched | 33% | FAIL |
| total additions | — | 6.356 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 169.5248 | 310.105 | True | True |
| 2027 | 170.0232 | 341.14 | True | True |

## Re-score — FC-4 co2 class-grain repair (2026-08-30)

Zero-solve rescore of the committed score: the model's unsplit `COAL` family energy (dropped from the scored CO2 by the bench-intensity-key iteration) is valued at the bench's actual-coal-CO2-weighted mean coal intensity. Volume/price rows untouched. See `rescore_co2_grain` in `crossover_score.json`.

| year | co2 signed before | after | unsplit COAL TWh | ī_coal | status |
|---|--:|--:|--:|--:|:--|
| 2023 | -49.2% | -25.2% | 39.24 | 1.0476 | FAIL |
| 2024 | -42.7% | -23.2% | 32.192 | 1.0442 | FAIL |
| 2025 | -51.2% | +1.3% | 85.928 | 1.038 | PASS |
