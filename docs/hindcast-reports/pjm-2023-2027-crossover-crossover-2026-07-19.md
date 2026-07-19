# T1-X crossover — PJM (pjm-2023-2027-crossover)

_Generated 2026-07-19 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2026 · keeper `2026-07-18-pjm-115-unit-only`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 145.314 | 13.263 | 10.96 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 173.928 | 13.111 | 13.27 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | — | — | — | SKIPPED |
| C3a system load-weighted mean LMP | 2023 | +3.2% | +4.8% | 0.66 | PASS |
| C3a system load-weighted mean LMP | 2024 | +9.4% | +4.4% | 2.14 | PASS |
| C3a system load-weighted mean LMP | 2025 | +18.9% | +9.1% | 2.08 | FAIL |
| C3b monthly price NRMSE | 2023 | 0.110 | 0.172 | 0.64 | PASS |
| C3b monthly price NRMSE | 2024 | 0.179 | 0.137 | 1.31 | PASS |
| C3b monthly price NRMSE | 2025 | 0.229 | 0.158 | 1.45 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.7% | +1.8% | 25.13 | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +42.4% | +3.2% | 13.26 | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +57.9% | +2.9% | 19.96 | FAIL |

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `shape` — C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 11.121 | 0.057 | -100% | FAIL |
| unit recall >300MW | 17 units | 0 matched | 0% | FAIL |
| total additions | — | 17.5 GW | (actual 24.092 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

| year | model CO2 (Mt, physical) | total gen (TWh) | dispatch ≥ 0 | price finite |
|---|--:|--:|:--|:--|
| 2026 | 277.8585 | 781.057 | False | True |
| 2027 | 282.165 | 798.478 | False | True |
