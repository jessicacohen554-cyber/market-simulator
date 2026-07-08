# Capacity hindcast — ERCOT 2021→2025 (realized fuel)

_Generated 2026-07-08 · W2-P5 · plan §1.4 · bundle `results/hindcast/ercot-2021-2025-realized-g30lookahead/ERCOT/26055f2dce2a3b90`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.534 | 15.834 | +932% | ❌ FAIL |
| unit recall >300MW | 3 units | 2 matched | 67% | ❌ FAIL |
| false-retire (GW) | — | 14.902 | 94% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **0%** (0/3). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.019 | 0.0 | -100% |
| coal | 0.932 | 13.964 | +1398% |
| gas_cc | 0.08 | 0.0 | -100% |
| gas_ct | 0.502 | 0.0 | -100% |
| gas_st | 0.0 | 1.87 |  |

## Additions (cumulative 2021→2025)

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 12.663 | 15.0 | +18% | ❌ FAIL | +7.2 |
| solar | 25.08 | 4.0 | -84% | ❌ FAIL | -37.2 |
| gas_cc | 0.244 | 6.0 | +2359% | ❌ FAIL | +11.6 |
| gas_ct | 3.692 | 6.0 | +62% | ❌ FAIL | +5.3 |
| storage | 13.691 | 16.0 | +17% | ✅ PASS | +7.3 |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 84.7 | 191.4 | -56% | (report-only) |
| 2024 | 79.0 | 191.3 | -59% | (report-only) |
| 2025 | 79.4 | 193.6 | -59% | ❌ FAIL |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |
