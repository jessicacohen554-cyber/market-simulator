# T1-X crossover — NEISO (neiso-2021-2025-t1ff-armk-fh5)

_Generated 2026-08-11 · FF-0E · plan §2.2 · vintage 2020 · forward boundary 2021 · keeper `2026-08-06-neiso-87-control`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 7.861 | 1.044 | 7.53 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 12.376 | 0.830 | 14.91 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +29.1% | +3.5% | 8.34 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +15.2% | +5.7% | 2.65 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +30.5% | +2.5% | 12.13 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.419 | 0.086 | 4.87 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.413 | 0.159 | 2.60 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.606 | 0.058 | 10.45 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +15.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +22.6% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +22.4% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 46.726 | 54.218 | +13.8% | +0.6% | 23.42 | yes |
| `gas_twh` | 2024 | 46.59 | 58.599 | +20.5% | +0.3% | 60.27 | yes |
| `gas_twh` | 2025 | 45.956 | 57.996 | +20.8% | +5.1% | 4.05 | NO — reported only |
| `coal_twh` | 2023 | 0.875 | 0.203 | +330.4% | +66.5% | 4.97 | yes |
| `coal_twh` | 2024 | 0.865 | 0.254 | +240.8% | +51.6% | 4.67 | yes |
| `coal_twh` | 2025 | 0.863 | 0.271 | +218.2% | +22.1% | 9.86 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [COAL_BIT] would bias the family total; reported, not banded

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 3.253 | 5.274 | +62% | FAIL |
| unit recall >300MW | 4 units | 0 matched | 0% | FAIL |
| total additions | — | 5.556 GW | (actual 2.981 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **4 of 4** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
