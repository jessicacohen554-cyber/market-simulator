# T1-X crossover — NYISO (nyiso-2023-2027-crossover-capxd10)

_Generated 2026-08-30 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-30-nyiso-157-par-attribution`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 24.139 | 5.082 | 4.75 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 24.288 | 7.014 | 3.46 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +29.9% | +1.0% | 30.16 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +2.5% | +2.0% | 1.28 | PASS |
| C3a system load-weighted mean LMP | 2025 | +24.0% | +12.0% | 2.00 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.337 | 0.116 | 2.90 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.252 | 0.173 | 1.46 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.394 | 0.203 | 1.94 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +10.1% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +10.3% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +3.9% | — | — | PASS |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 71.673 | 59.238 | +21.0% | +1.5% | 14.38 | yes |
| `gas_twh` | 2024 | 76.404 | 63.774 | +19.8% | +2.1% | 9.38 | yes |
| `gas_twh` | 2025 | 71.854 | 67.869 | +5.9% | +2.1% | 2.85 | NO — reported only |

**Rubric rows NOT covered by this run** (reported, never a pass):
- gas_twh 2025: preliminary EIA-923 vintage — incomplete class actual(s) [CC_CHP, CC_REGULAR, CT_PEAKER, ST_CHP, ST_GAS] would bias the family total; reported, not banded
- coal_twh 2023: family not benchmarked for this ISO
- coal_twh 2024: family not benchmarked for this ISO
- coal_twh 2025: family not benchmarked for this ISO

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.711 | 0.008 | -100% | FAIL |
| unit recall >300MW | 1 units | 0 matched | 0% | FAIL |
| total additions | — | 3.311 GW | (actual 3.375 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2023-12-31**). Members: **1 of 1** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 28.4222 | 141.108 | True | True |
| 2027 | 28.8747 | 141.888 | True | True |

## Re-score — FC-4 co2 class-grain repair (2026-08-30)

Zero-solve rescore of the committed score: the model's unsplit `COAL` family energy (dropped from the scored CO2 by the bench-intensity-key iteration) is valued at the bench's actual-coal-CO2-weighted mean coal intensity. Volume/price rows untouched. See `rescore_co2_grain` in `crossover_score.json`.

| year | co2 signed before | after | unsplit COAL TWh | ī_coal | status |
|---|--:|--:|--:|--:|:--|
| 2023 | +10.1% | +10.1% | 0.0 | 0.0 | FAIL |
| 2024 | +10.3% | +10.3% | 0.0 | 0.0 | FAIL |
| 2025 | +3.9% | +3.9% | 0.0 | 0.0 | PASS |
