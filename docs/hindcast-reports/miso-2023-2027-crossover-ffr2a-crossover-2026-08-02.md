# T1-X crossover — MISO (miso-2023-2027-crossover-ffr2a)

_Generated 2026-08-02 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-07-31-miso-109b-hy-level`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 233.161 | 17.599 | 13.25 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 232.314 | 19.284 | 12.05 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +13.6% | +1.2% | 11.43 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +15.3% | +6.5% | 2.37 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +30.3% | +14.2% | 2.14 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.173 | 0.074 | 2.34 | PASS |
| C3b monthly price NRMSE | 2024 | 0.247 | 0.114 | 2.17 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.326 | 0.189 | 1.73 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +63.3% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +59.9% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +77.1% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 218.25 | 199.309 | +9.5% | +5.1% | 1.86 | yes |
| `gas_twh` | 2024 | 232.177 | 207.1 | +12.1% | +2.7% | 4.44 | yes |
| `gas_twh` | 2025 | 133.066 | 194.461 | +31.6% | +7.7% | 4.11 | NO — reported only |
| `coal_twh` | 2023 | 187.628 | 185.787 | +1.0% | +1.8% | 0.54 | yes |
| `coal_twh` | 2024 | 167.623 | 176.316 | +4.9% | +1.5% | 3.31 | yes |
| `coal_twh` | 2025 | 272.622 | 212.156 | +28.5% | +0.1% | 475.00 | NO — reported only |

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
| thermal GW retired | 15.227 | 6.679 | -56% | FAIL |
| unit recall >300MW | 17 units | 0 matched | 0% | FAIL |
| total additions | — | 9.234 GW | (actual 31.981 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 345.3284 | 551.946 | True | True |
| 2027 | 323.785 | 562.774 | True | True |

## Re-score — FC-4 co2 class-grain repair (2026-08-30)

Zero-solve rescore of the committed score: the model's unsplit `COAL` family energy (dropped from the scored CO2 by the bench-intensity-key iteration) is valued at the bench's actual-coal-CO2-weighted mean coal intensity. Volume/price rows untouched. See `rescore_co2_grain` in `crossover_score.json`.

| year | co2 signed before | after | unsplit COAL TWh | ī_coal | status |
|---|--:|--:|--:|--:|:--|
| 2023 | -63.3% | +1.2% | 187.628 | 1.0029 | PASS |
| 2024 | -59.9% | -1.8% | 167.623 | 0.9891 | PASS |
| 2025 | -77.1% | +13.4% | 272.622 | 0.993 | FAIL |
