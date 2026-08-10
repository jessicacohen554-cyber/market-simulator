# T1-X crossover — NEISO (neiso-2023-2025-t1ff-armk-fh4)

_Generated 2026-08-10 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-06-neiso-87-control`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 26.118 | 1.044 | 25.02 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 25.947 | 0.830 | 31.26 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +60.7% | +3.5% | 17.38 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +33.7% | +5.7% | 5.88 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +24.5% | +2.5% | 9.77 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.660 | 0.086 | 7.67 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.494 | 0.159 | 3.11 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.571 | 0.058 | 9.85 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +42.0% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +39.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +31.8% | — | — | FAIL |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 31.115 | 54.218 | +42.6% | +0.6% | 72.22 | yes |
| `gas_twh` | 2024 | 35.609 | 58.599 | +39.2% | +0.3% | 115.38 | yes |
| `gas_twh` | 2025 | 39.733 | 57.996 | +31.5% | +5.1% | 6.14 | NO — reported only |
| `coal_twh` | 2023 | 0.646 | 0.203 | +217.8% | +66.5% | 3.27 | yes |
| `coal_twh` | 2024 | 0.057 | 0.254 | +77.6% | +51.6% | 1.50 | yes |
| `coal_twh` | 2025 | 0.008 | 0.271 | +97.0% | +22.1% | 4.38 | NO — reported only |

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
| thermal GW retired | 3.253 | 4.705 | +45% | FAIL |
| unit recall >300MW | 4 units | 0 matched | 0% | FAIL |
| total additions | — | 4.0 GW | (actual 2.981 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2023-12-31**). Members: **4 of 4** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
