# T1-X crossover — PJM (pjm-2023-2027-crossover-ffr2a)

_Generated 2026-08-02 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-07-31-pjm-143b-hy-level`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 148.821 | 11.851 | 12.56 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 167.078 | 9.189 | 18.18 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +3.6% | +6.3% | 0.58 | PASS |
| C3a system load-weighted mean LMP | 2024 | +7.5% | +0.4% | 19.66 | PASS |
| C3a system load-weighted mean LMP | 2025 | +17.2% | +7.5% | 2.29 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.111 | 0.160 | 0.69 | PASS |
| C3b monthly price NRMSE | 2024 | 0.166 | 0.119 | 1.40 | PASS |
| C3b monthly price NRMSE | 2025 | 0.214 | 0.136 | 1.57 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +42.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +57.3% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 363.237 | 364.529 | +0.4% | +0.2% | 1.59 | yes |
| `gas_twh` | 2024 | 395.635 | 381.906 | +3.6% | +0.9% | 3.83 | yes |
| `gas_twh` | 2025 | 313.735 | 377.254 | +16.8% | +3.2% | 5.30 | NO — reported only |
| `coal_twh` | 2023 | 97.9 | 112.471 | +13.0% | +0.2% | 81.00 | yes |
| `coal_twh` | 2024 | 86.147 | 115.195 | +25.2% | +0.8% | 31.52 | yes |
| `coal_twh` | 2025 | 163.908 | 136.864 | +19.8% | +4.5% | 4.43 | NO — reported only |

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
| total additions | — | 15.01 GW | (actual 24.092 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 335.2425 | 778.635 | False | True |
| 2027 | 332.6927 | 796.054 | False | True |

## Re-score — FC-4 co2 class-grain repair (2026-08-30)

Zero-solve rescore of the committed score: the model's unsplit `COAL` family energy (dropped from the scored CO2 by the bench-intensity-key iteration) is valued at the bench's actual-coal-CO2-weighted mean coal intensity. Volume/price rows untouched. See `rescore_co2_grain` in `crossover_score.json`.

| year | co2 signed before | after | unsplit COAL TWh | ī_coal | status |
|---|--:|--:|--:|--:|:--|
| 2023 | -45.1% | -7.4% | 97.9 | 1.0185 | CAVEAT |
| 2024 | -42.2% | -10.3% | 86.147 | 1.0107 | FAIL |
| 2025 | -57.3% | -1.1% | 163.908 | 1.0035 | PASS |
