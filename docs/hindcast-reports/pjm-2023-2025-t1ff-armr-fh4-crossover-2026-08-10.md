# T1-X crossover — PJM (pjm-2023-2025-t1ff-armr-fh4)

_Generated 2026-08-10 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-04-pjm-152-collapse`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 145.096 | 12.625 | 11.49 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 175.184 | 8.985 | 19.50 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +1.9% | +6.2% | 0.31 | PASS |
| C3a system load-weighted mean LMP | 2024 | +7.8% | +0.6% | 13.65 | PASS |
| C3a system load-weighted mean LMP | 2025 | +18.4% | +7.7% | 2.39 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.105 | 0.160 | 0.66 | PASS |
| C3b monthly price NRMSE | 2024 | 0.167 | 0.119 | 1.40 | PASS |
| C3b monthly price NRMSE | 2025 | 0.224 | 0.140 | 1.60 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +46.5% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +41.2% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +58.7% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 355.137 | 364.529 | +2.6% | +0.7% | 3.69 | yes |
| `gas_twh` | 2024 | 402.811 | 381.906 | +5.5% | +1.5% | 3.62 | yes |
| `gas_twh` | 2025 | 303.456 | 377.254 | +19.6% | +2.4% | 8.05 | NO — reported only |
| `coal_twh` | 2023 | 108.5 | 112.471 | +3.5% | +0.1% | 32.09 | yes |
| `coal_twh` | 2024 | 94.639 | 115.195 | +17.8% | +0.9% | 19.39 | yes |
| `coal_twh` | 2025 | 204.338 | 136.864 | +49.3% | +4.3% | 11.46 | NO — reported only |

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
| thermal GW retired | 15.062 | 0.057 | -100% | FAIL |
| unit recall >300MW | 20 units | 0 matched | 0% | FAIL |
| total additions | — | 7.51 GW | (actual 24.092 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2023-12-31**). Members: **20 of 20** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
