# Capacity hindcast — MISO 2021→2025 (realized fuel)

_Generated 2026-07-16 · W2-P5 · plan §1.4 · bundle `results/hindcast/miso-2021-2025-realized-cmc-probe/MISO/fbf82e5c764d57ca`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

> **RC-1A A/B — curve-ON PROBE leg (`--capacity-market-clearing`, capacity_market_clearing_by_iso={'MISO': True}; defaults untouched), on the RC-1C SEASONAL RBDC grain.** The position-calibration measurement (plan §2.2): the screens price adequacy as MISO's own four-season RBDC revenue sum (RC-1C landed mid-session; this leg was re-solved on it — an earlier annual-grain diagnostic solve of the same leg is quoted as a sensitivity in the findings doc, not registered). First MISO fossil economic exits: coal 11.81 GW vs actual 10.93 (+8%), recall 0%→76%, false-retire 0.874 GW PASS (raw and IS-2020), 2025 CO2 +14%→+5%. Full A/B analysis: docs/handoffs/position-calibration-findings-2026-07-16.md. Counterpart control: `miso-2021-2025-realized-cmc-before`.


## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 15.227 | 12.593 | -17% | ❌ FAIL |
| unit recall >300MW | 17 units | 13 matched | 76% | ✅ PASS |
| false-retire (GW) | — | 0.874 | 7% of model | ✅ PASS |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **35%** (6/17). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.023 | 0.016 | -30% |
| coal | 10.934 | 11.809 | +8% |
| gas_cc | 0.521 | 0.0 | -100% |
| gas_ct | 2.435 | 0.0 | -100% |
| nuclear | 0.812 | 0.768 | -5% |
| oil | 0.502 | 0.0 | -100% |

## Additions (cumulative 2021→2025)

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 7.2 | 12.0 | +67% | ❌ FAIL | +27.5 |
| solar | 18.649 | 12.0 | -36% | ❌ FAIL | -8.3 |
| gas_cc | 3.867 | 0.0 | -100% | ❌ FAIL | -12.1 |
| gas_ct | 1.379 | 0.01 | -99% | ❌ FAIL | -4.3 |
| storage | 0.744 | 0.0 | -100% | ❌ FAIL | -2.3 |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 274.2 | 288.9 | -5% | (report-only) |
| 2024 | 259.3 | 282.0 | -8% | (report-only) |
| 2025 | 316.7 | 301.4 | +5% | ✅ PASS |

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
| false-retire (GW) | 0.874 (✅ PASS) | 0.874 (✅ PASS) |
| false-retire (% of model) | 7% | 7% |
| unit recall >300MW | 76% (13/17) | 76% (13/17) |
| plant-exact recall (diagnostic) | 35% (6/17) | (same) |
| reversal exposure (GW, §c.5-1) | — | 0.0 |

Per-channel recall + false-retire (§c.5-4, legacy `known` → announced):

| channel | retired GW | false-retire GW | recall (matched / big-actual) |
|---|--:|--:|--:|
| announced | 0.784 | 0.0 | 0/17 |
| economic | 11.809 | 0.874 | 13/17 |

> **Additions (§c.5-2):** Post-V restart additions excluded from IS-2020 additions (§c.5-2). Inert in the RD-5 actuals as landed — the coverage fix booked only the physical exit, no restart addition row exists.
