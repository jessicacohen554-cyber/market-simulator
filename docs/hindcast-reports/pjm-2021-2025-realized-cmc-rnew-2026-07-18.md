# Capacity hindcast — PJM 2021→2025 (realized fuel)

_Generated 2026-07-18 · W2-P5 · plan §1.4 · bundle `results/hindcast/pjm-2021-2025-realized-cmc-rnew/PJM/784e354a7b8b7317`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 11.121 | 15.643 | +41% | ❌ FAIL |
| unit recall >300MW | 17 units | 13 matched | 76% | ✅ PASS |
| false-retire (GW) | — | 8.749 | 56% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **35%** (6/17). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.189 | 0.009 | -95% |
| coal | 6.885 | 11.537 | +68% |
| gas_ct | 3.491 | 0.0 | -100% |
| nuclear | 0.0 | 4.097 |  |
| oil | 0.555 | 0.0 | -100% |

## Additions (cumulative 2021→2025)

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 1.619 | 6.0 | +271% | ❌ FAIL | +9.3 |
| solar | 13.066 | 24.0 | +84% | ❌ FAIL | +9.8 |
| gas_cc | 8.525 | 5.0 | -41% | ❌ FAIL | -22.1 |
| gas_ct | 0.447 | 2.5 | +459% | ❌ FAIL | +4.8 |
| storage | 0.283 | 0.0 | -100% | ❌ FAIL | -1.2 |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 278.8 | 407.1 | -32% | (report-only) |
| 2024 | 268.8 | 420.6 | -36% | (report-only) |
| 2025 | 301.8 | 448.7 | -33% | ❌ FAIL |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |

---

## IS-2020 re-score (T-R8, 2026-07-18) — no re-solve

Scoring-hygiene re-score of the **committed** bundle against RC-0B §c.5: **raw** grades realized usefulness against latest truth; **IS-2020** grades forecast skill against what was knowable at the 2020 vintage cutoff (V = 2020-12-31). Both are reported side by side — neither replaces the other. No LP was solved; the originals above are preserved. The RD-5 actuals-coverage fix (plants 8907 Indian Point, 1715 Palisades) is already reflected in the raw pass; IS-2020 adds the Byron/Dresden reversal exclusion (§c.5-1).

| retirement metric | raw | IS-2020 |
|---|--:|--:|
| false-retire (GW) | 8.749 (❌ FAIL) | 4.652 (❌ FAIL) |
| false-retire (% of model) | 56% | 40% |
| unit recall >300MW | 76% (13/17) | 76% (13/17) |
| plant-exact recall (diagnostic) | 35% (6/17) | (same) |
| reversal exposure (GW, §c.5-1) | — | 4.097 |

> **Reversal exclusion (§c.5-1):** 4.097 GW of model nuclear retirement is information-set-correct (mandated by an instrument public ≤ V) but reality-reversed by a post-V counter-instrument, so it is **excluded from IS-2020 false-retire** and reported as `reversal_exposure_gw`. Raw scoring keeps it as false-retire (the unit runs today). Reversing instrument(s): Dresden 2 (869_2); Dresden 3 (869_3); Byron 1 (6023_1); Byron 2 (6023_2) — Illinois Climate and Equitable Jobs Act (P.A. 102-0662, signed 2021-09-15) — CMC award; retirement reversed 2021-09-15.

Per-channel recall + false-retire (§c.5-4, legacy `known` → announced):

| channel | retired GW | false-retire GW | recall (matched / big-actual) |
|---|--:|--:|--:|
| announced | 4.106 | 4.097 | 0/17 |
| economic | 11.537 | 4.652 | 13/17 |

> **Additions (§c.5-2):** Post-V restart additions excluded from IS-2020 additions (§c.5-2). Inert in the RD-5 actuals as landed — the coverage fix booked only the physical exit, no restart addition row exists.
