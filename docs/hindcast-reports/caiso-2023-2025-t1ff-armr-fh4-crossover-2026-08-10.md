# T1-X crossover — CAISO (caiso-2023-2025-t1ff-armr-fh4)

_Generated 2026-08-10 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-09-caiso-188-d1-micseam`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 27.379 | 7.813 | 3.50 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 37.202 | 5.802 | 6.41 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +17.6% | +3.4% | 5.16 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +23.7% | +10.4% | 2.27 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +55.6% | +12.9% | 4.30 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.477 | 0.075 | 6.36 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.423 | 0.145 | 2.92 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.585 | 0.164 | 3.57 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +16.6% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +44.5% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +63.5% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 82.821 | 65.043 | +27.3% | +9.4% | 2.91 | yes |
| `gas_twh` | 2024 | 90.903 | 57.249 | +58.8% | +4.8% | 12.30 | yes |
| `gas_twh` | 2025 | 91.553 | 50.263 | +82.2% | +7.2% | 11.39 | NO — reported only |
| `coal_twh` | 2023 | 0.349 | 0.063 | +457.4% | +100.0% | 4.57 | yes |
| `coal_twh` | 2024 | 0.345 | 0.074 | +367.7% | +100.0% | 3.68 | yes |
| `coal_twh` | 2025 | 0.359 | 0.076 | +371.6% | +100.0% | 3.72 | NO — reported only |

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
