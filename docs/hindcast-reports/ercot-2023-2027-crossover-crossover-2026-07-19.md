# T1-X crossover — ERCOT (ercot-2023-2027-crossover)

_Generated 2026-07-19 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-07-18-ercot82-measured-rtolcap`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 97.849 | 11.247 | 8.70 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 91.125 | 9.234 | 9.87 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 1.386 | 44.89 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +69.2% | +21.8% | 3.17 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +44.4% | +2.1% | 21.06 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +25.5% | +3.4% | 7.45 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.166 | 0.449 | 2.60 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.501 | 0.303 | 1.65 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.274 | 0.086 | 3.19 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +48.9% | +2.5% | 19.63 | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +46.2% | +0.5% | 92.32 | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +55.3% | +1.3% | 43.56 | FAIL |

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `shape` — C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.534 | 21.066 | +1273% | FAIL |
| unit recall >300MW | 3 units | 1 matched | 33% | FAIL |
| total additions | — | 16.0 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 131.8812 | 281.459 | True | True |
| 2027 | 139.9513 | 316.643 | True | True |
