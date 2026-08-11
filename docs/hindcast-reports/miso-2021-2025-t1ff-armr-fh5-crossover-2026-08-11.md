# T1-X crossover — MISO (miso-2021-2025-t1ff-armr-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-09-miso-148-basis-aware`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 237.819 | 14.913 | 15.95 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 252.620 | 20.284 | 12.45 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +16.3% | +2.0% | 8.21 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +19.3% | +8.1% | 2.39 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +27.5% | +15.6% | 1.76 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.192 | 0.082 | 2.34 | PASS |
| C3b monthly price NRMSE | 2024 | 0.224 | 0.125 | 1.79 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.302 | 0.212 | 1.43 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +67.0% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +61.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +77.5% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 205.484 | 199.309 | +3.1% | +4.0% | 0.77 | yes |
| `gas_twh` | 2024 | 233.17 | 207.1 | +12.6% | +1.1% | 11.14 | yes |
| `gas_twh` | 2025 | 139.316 | 194.461 | +28.4% | +6.9% | 4.10 | NO — reported only |
| `coal_twh` | 2023 | 256.079 | 185.787 | +37.8% | +3.3% | 11.33 | yes |
| `coal_twh` | 2024 | 231.366 | 176.316 | +31.2% | +3.4% | 9.13 | yes |
| `coal_twh` | 2025 | 343.205 | 212.156 | +61.8% | +0.7% | 84.62 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT, COAL_LIGNITE, COAL_PRB] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 17.369 | 6.254 | -64% | FAIL |
| unit recall >300MW | 19 units | 9 matched | 47% | FAIL |
| total additions | — | 1.146 GW | (actual 31.981 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **19 of 19** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
