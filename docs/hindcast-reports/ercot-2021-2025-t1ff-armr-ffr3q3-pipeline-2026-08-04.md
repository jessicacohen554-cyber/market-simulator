# Capacity hindcast — ERCOT 2021→2025 (realized fuel)

_Generated 2026-08-04 · W2-P5 · plan §1.4 · bundle `results/hindcast/ercot-2021-2025-t1ff-armr-ffr3q3-pipeline/ERCOT/6a824992b5fb1baf`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.534 | 0.0 | -100% | ❌ FAIL |
| unit recall >300MW | 3 units | 0 matched | 0% | ❌ FAIL |
| false-retire (GW) | — | 0.0 | 0% of model | ✅ PASS |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **0%** (0/3). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.019 | 0.0 | -100% |
| coal | 0.932 | 0.0 | -100% |
| gas_cc | 0.08 | 0.0 | -100% |
| gas_ct | 0.502 | 0.0 | -100% |

## Additions (cumulative 2021→2025) — **decision basis**

_Attribution basis: **decision** (owner decision D-9(ii), signed 2026-08-04 (sitting Addendum K.2)). Scored on the DECISION basis (D-9(ii)). Additions verdicts on this basis are NOT comparable to any additions verdict committed before 2026-08-04, which were scored on the COD basis — the metric means something different. Retirements-side comparability is unaffected. See docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md._

Basis effect — decided in-window with COD **after** the window (invisible under the COD basis): `{'gas_cc': 3.0, 'gas_ct': 3.0, 'wind': 5.0}`; commissioned in-window from a **pre-window** decision (dropped under the decision basis): `none` (GW).

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 12.663 | 10.0 | -21% | ❌ FAIL | +8.4 |
| solar | 25.08 | 0.0 | -100% | ❌ FAIL | -45.2 |
| gas_cc | 0.244 | 3.0 | +1130% | ❌ FAIL | +8.9 |
| gas_ct | 3.692 | 3.0 | -19% | ❌ FAIL | +2.7 |
| storage | 13.691 | 16.0 | +17% | ✅ PASS | +25.3 |

COD-basis comparison (**not** the graded instrument; model total 21.0 GW vs decision-basis 32.0 GW):

| tech | model GW (COD) | model GW (decision) | band (COD) |
|---|--:|--:|:--|
| wind | 5.0 | 10.0 | ❌ FAIL |
| solar | 0.0 | 0.0 | ❌ FAIL |
| gas_cc | 0.0 | 3.0 | ❌ FAIL |
| gas_ct | 0.0 | 3.0 | ❌ FAIL |
| storage | 16.0 | 16.0 | ✅ PASS |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 112.1 | 191.4 | -41% | (report-only) |
| 2024 | 107.7 | 191.3 | -44% | (report-only) |
| 2025 | 149.8 | 193.6 | -23% | ❌ FAIL |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |
