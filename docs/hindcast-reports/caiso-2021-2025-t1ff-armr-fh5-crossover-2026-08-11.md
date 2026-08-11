# T1-X crossover — CAISO (caiso-2021-2025-t1ff-armr-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-09-caiso-188-d1-micseam`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 34.608 | 7.813 | 4.43 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 42.295 | 5.802 | 7.29 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +15.6% | +3.4% | 4.57 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +22.5% | +10.4% | 2.15 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +49.1% | +12.9% | 3.79 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.480 | 0.075 | 6.40 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.421 | 0.145 | 2.90 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.522 | 0.164 | 3.18 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +35.7% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +57.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +76.0% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 95.745 | 65.043 | +47.2% | +9.4% | 5.02 | yes |
| `gas_twh` | 2024 | 98.415 | 57.249 | +71.9% | +4.8% | 15.04 | yes |
| `gas_twh` | 2025 | 97.983 | 50.263 | +94.9% | +7.2% | 13.17 | NO — reported only |
| `coal_twh` | 2023 | 0.162 | 0.063 | +158.1% | +100.0% | 1.58 | yes |
| `coal_twh` | 2024 | 0.151 | 0.074 | +104.8% | +100.0% | 1.05 | yes |
| `coal_twh` | 2025 | 0.177 | 0.076 | +132.9% | +100.0% | 1.33 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT, COAL_PRB] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

> capacity events not scored — no committed exit/addition target exists for CAISO (actuals not found: data/raw/_validation-source/capacity_actuals_caiso.csv — run scripts/data/build_capacity_actuals.py --iso CAISO); reported as absent, never fabricated

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
