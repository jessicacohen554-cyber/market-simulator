# T1-X crossover — CAISO (caiso-2021-2025-t1ff-armk-fh5)

_Generated 2026-08-13 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-09-caiso-188-d1-micseam`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 34.313 | 7.813 | 4.39 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 40.013 | 5.802 | 6.90 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +7.0% | +3.4% | 2.06 | PASS |
| C3a system load-weighted mean LMP | 2024 | +37.0% | +10.4% | 3.54 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +42.5% | +12.9% | 3.29 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.458 | 0.075 | 6.11 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.514 | 0.145 | 3.54 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.457 | 0.164 | 2.79 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +36.6% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +47.3% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +83.7% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 96.255 | 65.043 | +48.0% | +9.4% | 5.11 | yes |
| `gas_twh` | 2024 | 92.352 | 57.249 | +61.3% | +4.8% | 12.83 | yes |
| `gas_twh` | 2025 | 102.397 | 50.263 | +103.7% | +7.2% | 14.39 | NO — reported only |
| `coal_twh` | 2023 | 0.162 | 0.063 | +158.1% | +100.0% | 1.58 | yes |
| `coal_twh` | 2024 | 0.159 | 0.074 | +116.3% | +100.0% | 1.16 | yes |
| `coal_twh` | 2025 | 0.162 | 0.076 | +112.5% | +100.0% | 1.12 | NO — reported only |

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
