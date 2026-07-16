# Capacity hindcast — MISO 2021→2025 (realized fuel)

_Generated 2026-07-16 · W2-P5 · plan §1.4 · bundle `results/hindcast/miso-2021-2025-realized-cmc-probe-d1/MISO/33fcf9b6dbeeae55`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

> **RC-1A-D1 re-probe — curve-ON PROBE leg at the D1=3 default, seasonal RBDC grain (`--capacity-market-clearing`, capacity_market_clearing_by_iso={'MISO': True}; `retirement_years_coal=3` per RC-D1/PR #2335; defaults untouched).** Re-runs the RC-1A curve-ON probe (previously the near-pass-quality D1=1 leg: coal +8%, false-retire 0.874 GW PASS) on the shipping threshold. **Headline: D1=3 DESTROYS MISO's D1=1 near-pass by a per-fuel threshold INVERSION.** Raising only coal to 3 (gas_st stays at 2) makes gas_st the first-exiting fossil: gas_st econ exits 0 → **8.643 GW** in 2023 (a fuel that retired ZERO in reality — pure false-retire), while coal delays 2022→2024 and shrinks 11.809 → 3.558 GW (recall 76% → 29%). false-retire 0.874 GW (PASS) → **8.643 GW (FAIL)**; the 2025 shortage position lengthens 1.035 → 1.068 (pays $0 vs 24.5, vs the 243.3 cap-clearing) — WORSE on both position and skill. Provenance (RC-2B §3 M-2, resolved): the probe prices pre-2025 years on the vertical-at-CONE step, 2025 on the seasonal RBDC. Full A/B + wave-timing + LOYO analysis: docs/handoffs/position-calibration-d1-findings-2026-07-16.md. BEFORE control (D1-invariant): `miso-2021-2025-realized-cmc-before`; D1=1 counterpart: `miso-2021-2025-realized-cmc-probe`.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 15.227 | 12.986 | -15% | ❌ FAIL |
| unit recall >300MW | 17 units | 5 matched | 29% | ❌ FAIL |
| false-retire (GW) | — | 8.643 | 67% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **18%** (3/17). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.023 | 0.016 | -30% |
| coal | 10.934 | 3.558 | -68% |
| gas_cc | 0.521 | 0.0 | -100% |
| gas_ct | 2.435 | 0.0 | -100% |
| gas_st | 0.0 | 8.643 |  |
| nuclear | 0.812 | 0.768 | -5% |
| oil | 0.502 | 0.0 | -100% |

## Additions (cumulative 2021→2025)

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 7.2 | 12.0 | +67% | ❌ FAIL | +18.9 |
| solar | 18.649 | 12.0 | -36% | ❌ FAIL | -16.9 |
| gas_cc | 3.867 | 3.0 | -22% | ❌ FAIL | -1.7 |
| gas_ct | 1.379 | 2.0 | +45% | ❌ FAIL | +2.6 |
| storage | 0.744 | 0.0 | -100% | ❌ FAIL | -2.3 |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 284.3 | 288.9 | -2% | (report-only) |
| 2024 | 266.2 | 282.0 | -6% | (report-only) |
| 2025 | 326.9 | 301.4 | +8% | ✅ PASS |

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
| false-retire (GW) | 8.643 (❌ FAIL) | 8.643 (❌ FAIL) |
| false-retire (% of model) | 67% | 67% |
| unit recall >300MW | 29% (5/17) | 29% (5/17) |
| plant-exact recall (diagnostic) | 18% (3/17) | (same) |
| reversal exposure (GW, §c.5-1) | — | 0.0 |

Per-channel recall + false-retire (§c.5-4, legacy `known` → announced):

| channel | retired GW | false-retire GW | recall (matched / big-actual) |
|---|--:|--:|--:|
| announced | 0.784 | 0.0 | 0/17 |
| economic | 12.202 | 8.643 | 5/17 |

> **Additions (§c.5-2):** Post-V restart additions excluded from IS-2020 additions (§c.5-2). Inert in the RD-5 actuals as landed — the coverage fix booked only the physical exit, no restart addition row exists.
