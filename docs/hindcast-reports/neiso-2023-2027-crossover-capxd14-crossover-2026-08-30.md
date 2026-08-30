# T1-X crossover — NEISO (neiso-2023-2027-crossover-capxd14)

_Generated 2026-08-30 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-08-17-neiso-99-joint-p1`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 9.459 | 0.877 | 10.79 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 7.934 | 0.696 | 11.40 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +13.3% | +3.1% | 4.27 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +7.9% | +5.7% | 1.39 | PASS |
| C3a system load-weighted mean LMP | 2025 | +21.8% | +1.7% | 13.23 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.324 | 0.088 | 3.68 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.403 | 0.159 | 2.54 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.547 | 0.054 | 10.13 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +12.8% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +10.6% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +2.3% | — | — | PASS |

### Family volume (FC-4 `gas_twh` / `coal_twh`)

| family | year | model TWh | actual TWh | forecast err | keeper backcast err | input-gap | banded |
|---|--:|--:|--:|--:|--:|--:|:--|
| `gas_twh` | 2023 | 62.249 | 54.214 | +14.8% | +0.6% | 23.90 | yes |
| `gas_twh` | 2024 | 65.992 | 58.595 | +12.6% | +0.3% | 37.12 | yes |
| `gas_twh` | 2025 | 56.836 | 59.535 | +4.5% | +2.4% | 1.89 | NO — reported only |
| `coal_twh` | 2023 | 0.001 | 0.203 | +99.8% | +60.1% | 1.66 | yes |
| `coal_twh` | 2024 | 0.085 | 0.254 | +66.4% | +50.0% | 1.33 | yes |
| `coal_twh` | 2025 | 0.082 | 0.281 | +70.9% | +23.5% | 3.02 | NO — reported only |

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
| thermal GW retired | 4.997 | 3.563 | -29% | FAIL |
| unit recall >300MW | 6 units | 2 matched | 33% | FAIL |
| total additions | — | 4.5 GW | (actual 2.981 GW) | — |

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2023-12-31**). Members: **6 of 6** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 22.5351 | 106.116 | True | True |
| 2027 | 22.394 | 105.499 | True | True |

## Re-score — FC-4 co2 class-grain repair (2026-08-30)

Zero-solve rescore of the committed score: the model's unsplit `COAL` family energy (dropped from the scored CO2 by the bench-intensity-key iteration) is valued at the bench's actual-coal-CO2-weighted mean coal intensity. Volume/price rows untouched. See `rescore_co2_grain` in `crossover_score.json`.

| year | co2 signed before | after | unsplit COAL TWh | ī_coal | status |
|---|--:|--:|--:|--:|:--|
| 2023 | +12.8% | +12.8% | 0.001 | 0.8573 | FAIL |
| 2024 | +10.6% | +11.1% | 0.085 | 1.3862 | FAIL |
| 2025 | -2.3% | -1.8% | 0.082 | 1.3862 | PASS |
