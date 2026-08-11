# T1-X crossover — PJM (pjm-2021-2025-t1ff-armr-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-04-pjm-152-collapse`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 156.084 | 12.625 | 12.36 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 180.985 | 8.985 | 20.14 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +0.5% | +6.2% | 0.09 | PASS |
| C3a system load-weighted mean LMP | 2024 | +8.8% | +0.6% | 15.49 | PASS |
| C3a system load-weighted mean LMP | 2025 | +20.6% | +7.7% | 2.68 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.104 | 0.160 | 0.65 | PASS |
| C3b monthly price NRMSE | 2024 | 0.178 | 0.119 | 1.50 | PASS |
| C3b monthly price NRMSE | 2025 | 0.243 | 0.140 | 1.74 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +47.4% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +44.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +60.1% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 351.0 | 364.529 | +3.7% | +0.7% | 5.30 | yes |
| `gas_twh` | 2024 | 387.065 | 381.906 | +1.4% | +1.5% | 0.89 | yes |
| `gas_twh` | 2025 | 296.65 | 377.254 | +21.4% | +2.4% | 8.79 | NO — reported only |
| `coal_twh` | 2023 | 169.567 | 112.471 | +50.8% | +0.1% | 461.45 | yes |
| `coal_twh` | 2024 | 155.088 | 115.195 | +34.6% | +0.9% | 37.64 | yes |
| `coal_twh` | 2025 | 253.177 | 136.864 | +85.0% | +4.3% | 19.76 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT, COAL_PRB, COAL_WC] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 15.062 | 8.096 | -46% | FAIL |
| unit recall >300MW | 20 units | 5 matched | 25% | FAIL |
| total additions | — | 16.88 GW | (actual 24.092 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **20 of 20** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
