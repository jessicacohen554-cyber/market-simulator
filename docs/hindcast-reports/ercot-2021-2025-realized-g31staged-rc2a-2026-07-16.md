# Capacity hindcast — ERCOT 2021→2025 (realized fuel)

_Generated 2026-07-16 · W2-P5 · plan §1.4 · bundle `results/hindcast/ercot-2021-2025-realized-g31staged-rc2a/ERCOT/b98b4918585baa5f`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 1.534 | 12.727 | +730% | ❌ FAIL |
| unit recall >300MW | 3 units | 3 matched | 100% | ✅ PASS |
| false-retire (GW) | — | 11.292 | 89% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **33%** (1/3). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.019 | 0.0 | -100% |
| coal | 0.932 | 6.466 | +594% |
| gas_cc | 0.08 | 0.0 | -100% |
| gas_ct | 0.502 | 3.023 | +502% |
| gas_st | 0.0 | 3.237 |  |

## Additions (cumulative 2021→2025)

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 12.663 | 15.0 | +18% | ❌ FAIL | +7.8 |
| solar | 25.08 | 4.0 | -84% | ❌ FAIL | -37.1 |
| gas_cc | 0.244 | 6.0 | +2359% | ❌ FAIL | +11.8 |
| gas_ct | 3.692 | 6.0 | +62% | ❌ FAIL | +5.6 |
| storage | 13.691 | 16.0 | +17% | ✅ PASS | +8.0 |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 103.0 | 191.4 | -46% | (report-only) |
| 2024 | 92.8 | 191.3 | -51% | (report-only) |
| 2025 | 115.7 | 193.6 | -40% | ❌ FAIL |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |

---

## IS-2020 re-score (T-R8, 2026-07-16) — no re-solve

Scoring-hygiene re-score of the **committed** bundle against RC-0B §c.5: **raw** grades realized usefulness against latest truth; **IS-2020** grades forecast skill against what was knowable at the 2020 vintage cutoff (V = 2020-12-31). Both are reported side by side — neither replaces the other. No LP was solved; the originals above are preserved. The RD-5 actuals-coverage fix (plants 8907 Indian Point, 1715 Palisades) is already reflected in the raw pass; IS-2020 adds the Byron/Dresden reversal exclusion (§c.5-1).

| retirement metric | raw | IS-2020 |
|---|--:|--:|
| false-retire (GW) | 11.292 (❌ FAIL) | 11.292 (❌ FAIL) |
| false-retire (% of model) | 89% | 89% |
| unit recall >300MW | 100% (3/3) | 100% (3/3) |
| plant-exact recall (diagnostic) | 33% (1/3) | (same) |
| reversal exposure (GW, §c.5-1) | — | 0.0 |

Per-channel recall + false-retire (§c.5-4, legacy `known` → announced):

| channel | retired GW | false-retire GW | recall (matched / big-actual) |
|---|--:|--:|--:|
| economic | 12.727 | 11.292 | 3/3 |

> **Additions (§c.5-2):** Post-V restart additions excluded from IS-2020 additions (§c.5-2). Inert in the RD-5 actuals as landed — the coverage fix booked only the physical exit, no restart addition row exists.
