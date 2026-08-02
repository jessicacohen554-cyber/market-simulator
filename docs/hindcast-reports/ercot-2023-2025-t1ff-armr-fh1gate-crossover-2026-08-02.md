# T1-X crossover — ERCOT (ercot-2023-2025-t1ff-armr-fh1gate)

_Generated 2026-08-02 · FF-0E · plan §2.2 · vintage 2023 · forward boundary 2023 · keeper `2026-08-01-ercot149-gas-event-cap`_

Crossover forecast-mode run: **2023-2025** on realized inputs scored for dispatch skill + capacity events; **forward years (>= 2026)** are invariants/plausibility only — the scorer structurally refuses to read any bench or actual for them (rule 22). Nothing here is tuned; no LP was solved.

## (a) Dispatch skill vs bench — with keeper input-gap (FC-4)

`input_gap = |forecast_err| / |keeper_backcast_err|` — the backcast→forecast input gap (1.0 = forecast drivers reproduce the backcast-overlay skill; > 1 = forecast is worse).

| metric | year | forecast err | keeper backcast err | input-gap | status |
|---|--:|--:|--:|--:|:--|
| C1 fuel-mix (grid-delivered TWh) | 2023 | 85.566 | 8.752 | 9.78 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2024 | 85.921 | 6.332 | 13.57 | FAIL |
| C1 fuel-mix (grid-delivered TWh) | 2025 | 62.215 | 2.216 | 28.07 | FAIL |
| C3a system load-weighted mean LMP | 2023 | +68.5% | +33.3% | 2.06 | FAIL |
| C3a system load-weighted mean LMP | 2024 | +42.1% | +0.8% | 54.01 | FAIL |
| C3a system load-weighted mean LMP | 2025 | +21.0% | +9.1% | 2.32 | FAIL |
| C3b monthly price NRMSE | 2023 | 1.166 | 0.616 | 1.89 | FAIL |
| C3b monthly price NRMSE | 2024 | 0.480 | 0.198 | 2.42 | FAIL |
| C3b monthly price NRMSE | 2025 | 0.227 | 0.112 | 2.03 | FAIL |
| C5a system CO2 (full-plant basis) | 2023 | +45.9% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2024 | +41.0% | — | — | FAIL |
| C5a system CO2 (full-plant basis) | 2025 | +51.2% | — | — | FAIL |

**Deferred metrics** (not reconstructible from a crossover bundle):
- `sysvol` — C2 EIA-930 family system-volume: needs the bench e930 family reconcile the crossover bundle does not carry in a scorer-ready form.
- `price_tail` — C3c hourly scarcity tail: needs the ORDC/scarcity overlay payload (ordc.hoursGt200) the crossover DispatchResult does not carry.
- `dispatch_corr` — C4 per-plant hourly correlation: needs the per-plant CAMPD b64 hourly bench + per-plant model hourly series (calibration-bundle only).
- `shape` — C7 diurnal shape: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).
- `forced_share` — C8 forced-share: needs the bundle's legitimacy_diagnostics.json (not produced for a crossover bundle).

## (b) Capacity events 2023-2025 vs registry actuals

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.534 | 21.048 | +1272% | FAIL |
| unit recall >300MW | 3 units | 1 matched | 33% | FAIL |
| total additions | — | 6.356 GW | (actual 55.436 GW) | — |

## (c) Forward years (>= 2026) — invariants / plausibility only

> invariants / plausibility only — years >= 2026 are quarantined (locked test / forward edge, rule 22); no bench or actual is read and no skill is scored. Numbers below are model-only forecast output (physical CO2, grid generation).

_No forward-year parquet in the bundle._
