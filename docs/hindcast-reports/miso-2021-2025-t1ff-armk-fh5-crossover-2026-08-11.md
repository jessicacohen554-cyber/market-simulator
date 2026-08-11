# T1-X crossover — MISO (miso-2021-2025-t1ff-armk-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-09-miso-148-basis-aware`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 230.954 | 14.913 | 15.49 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 229.750 | 20.284 | 11.33 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +5.1% | +2.0% | 2.57 | PASS |
| C3a system load-weighted mean LMP | 2024 | +1.4% | +8.1% | 0.17 | PASS |
| C3a system load-weighted mean LMP | 2025 | +26.0% | +15.6% | 1.66 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.130 | 0.082 | 1.58 | PASS |
| C3b monthly price NRMSE | 2024 | 0.150 | 0.125 | 1.20 | PASS |
| C3b monthly price NRMSE | 2025 | 0.296 | 0.212 | 1.40 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +72.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +62.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +67.3% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 169.129 | 199.309 | +15.1% | +4.0% | 3.77 | yes |
| `gas_twh` | 2024 | 222.392 | 207.1 | +7.4% | +1.1% | 6.53 | yes |
| `gas_twh` | 2025 | 208.411 | 194.461 | +7.2% | +6.9% | 1.04 | NO — reported only |
| `coal_twh` | 2023 | 308.727 | 185.787 | +66.2% | +3.3% | 19.81 | yes |
| `coal_twh` | 2024 | 261.616 | 176.316 | +48.4% | +3.4% | 14.15 | yes |
| `coal_twh` | 2025 | 283.037 | 212.156 | +33.4% | +0.7% | 45.77 | NO — reported only |

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
| thermal GW retired | 17.369 | 14.477 | -17% | FAIL |
| unit recall >300MW | 19 units | 15 matched | 79% | PASS |
| total additions | — | 10.854 GW | (actual 31.981 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **19 of 19** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
