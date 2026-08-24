# Capacity hindcast — CAISO 2021→2025 (realized fuel)

_Generated 2026-08-24 · W2-P5 · plan §1.4 · bundle `results/hindcast/caiso-2021-2025-realized-dumps/CAISO/af508406b2ecb737`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 0.293 | 2.24 | +664% | ❌ FAIL |
| unit recall >300MW | 0 units | 0 matched | n/a | — |
| false-retire (GW) | — | 2.24 | 100% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **—** (0/0). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **0 of 0** target rows >=300 MW — recall **n/a** (never 0/N): no target exit >= 300 MW is reachable by an admissible channel on this run's fleet basis — reported n/a, never 0/N (D-24).

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.073 | 0.0 | -100% |
| coal | 0.007 | 0.0 | -100% |
| gas_cc | 0.01 | 0.0 | -100% |
| gas_ct | 0.081 | 0.0 | -100% |
| gas_st | 0.092 | 0.0 | -100% |
| nuclear | 0.0 | 2.24 |  |
| oil | 0.029 | 0.0 | -100% |

## Additions (cumulative 2021→2025) — **decision basis**

_Attribution basis: **decision** (owner decision D-9(ii), signed 2026-08-04 (sitting Addendum K.2)). Scored on the DECISION basis (D-9(ii)). Additions verdicts on this basis are NOT comparable to any additions verdict committed before 2026-08-04, which were scored on the COD basis — the metric means something different. Retirements-side comparability is unaffected. See docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md._

Basis effect — decided in-window with COD **after** the window (invisible under the COD basis): `{'wind': 3.0, 'solar': 4.0, 'gas_cc': 1.0}`; commissioned in-window from a **pre-window** decision (dropped under the decision basis): `none` (GW).

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 0.7 | 6.0 | +757% | ❌ FAIL | +18.2 |
| solar | 10.502 | 8.0 | -24% | ❌ FAIL | -11.7 |
| gas_cc | 0.0 | 3.0 |  | — | +10.4 |
| gas_ct | 0.136 | 11.838 | +8630% | ❌ FAIL | +40.5 |
| storage | 15.147 | 0.0 | -100% | ❌ FAIL | -56.9 |

COD-basis comparison (**not** the graded instrument; model total 20.838 GW vs decision-basis 28.838 GW):

| tech | model GW (COD) | model GW (decision) | band (COD) |
|---|--:|--:|:--|
| wind | 3.0 | 6.0 | ❌ FAIL |
| solar | 4.0 | 8.0 | ❌ FAIL |
| gas_cc | 2.0 | 3.0 | — |
| gas_ct | 11.838 | 11.838 | ❌ FAIL |
| storage | 0.0 | 0.0 | ❌ FAIL |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 36.3 | 26.1 | +39% | (report-only) |
| 2024 | 36.6 | 22.6 | +62% | (report-only) |
| 2025 | 35.7 | 18.7 | +91% | ❌ FAIL |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |
