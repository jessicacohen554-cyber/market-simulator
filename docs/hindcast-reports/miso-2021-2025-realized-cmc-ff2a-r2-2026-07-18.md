# Capacity hindcast — MISO 2021→2025 (realized fuel)

_Generated 2026-07-18 · W2-P5 · plan §1.4 · bundle `results/hindcast/miso-2021-2025-realized-cmc-ff2a-r2/MISO/6bfead0a82344b90`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 15.227 | 8.839 | -42% | ❌ FAIL |
| unit recall >300MW | 17 units | 13 matched | 76% | ✅ PASS |
| false-retire (GW) | — | 0.0 | 0% of model | ✅ PASS |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **35%** (6/17). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.023 | 0.016 | -30% |
| coal | 10.934 | 8.054 | -26% |
| gas_cc | 0.521 | 0.0 | -100% |
| gas_ct | 2.435 | 0.0 | -100% |
| nuclear | 0.812 | 0.768 | -5% |
| oil | 0.502 | 0.0 | -100% |

## Additions (cumulative 2021→2025)

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 7.2 | 12.0 | +67% | ❌ FAIL | +34.3 |
| solar | 18.649 | 3.709 | -80% | ❌ FAIL | -40.7 |
| gas_cc | 3.867 | 3.0 | -22% | ❌ FAIL | +2.1 |
| gas_ct | 1.379 | 0.0 | -100% | ❌ FAIL | -4.3 |
| storage | 0.744 | 2.4 | +223% | ❌ FAIL | +9.0 |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 284.4 | 288.9 | -2% | (report-only) |
| 2024 | 262.1 | 282.0 | -7% | (report-only) |
| 2025 | 322.6 | 301.4 | +7% | ✅ PASS |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |
