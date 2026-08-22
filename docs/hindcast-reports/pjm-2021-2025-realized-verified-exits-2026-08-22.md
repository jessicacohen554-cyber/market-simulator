# Capacity hindcast — PJM 2021→2025 (realized fuel)

_Generated 2026-08-22 · W2-P5 · plan §1.4 · bundle `results/hindcast/pjm-2021-2025-realized-verified-exits/PJM/4c2c7907805e679b`_

Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. 2021 seeds the price signal (not scored); **2022 is the quarantine bridge — evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned.

## Retirements (thermal, cumulative 2021→2025)

| metric | actual | model | err | band |
|---|--:|--:|--:|:--|
| thermal GW retired | 15.062 | 18.147 | +20% | ❌ FAIL |
| unit recall >300MW | 20 units | 16 matched | 80% | ✅ PASS |
| false-retire (GW) | — | 7.839 | 43% of model | ❌ FAIL |

> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW coverage**, not exact unit identity — a real retired unit is *recalled* when the model derated ≥ its MW of the same fuel (its plant-binned tranche is derated by its MW), and *false-retire* is the model's per-fuel MW in **excess** of what that fuel actually retired. This retires the 94% false-retire artifact the old 1:1 `fuel+size` match produced against lumpy tranche/zone derates. Stricter plant-exact recall (same plant, reported only): **60%** (12/20). A false-retire that stays high after the grain fix is a genuine over-retirement (screen root-cause, e.g. G-30), not a scoring artifact.

> **Gate membership (D-24, signed 2026-08-06 (sitting Addendum X.6)):** the >=300 MW recall denominator is the **reachable** set — a target exit gates only if the unit exists in the run's fleet basis AND an admissible channel could produce its exit (economic with no exclusion recorded, or an instrument dated on or before the run's vintage cutoff **2020-12-31**). Members: **20 of 20** target rows >=300 MW.

No target exit is classified unreachable on committed evidence (fail-closed: the gate excludes only on positive, cited evidence).

Per-fuel retired GW:

| fuel | actual | model | err |
|---|--:|--:|--:|
| biomass | 0.207 | 0.009 | -96% |
| coal | 10.299 | 18.137 | +76% |
| gas_cc | 0.434 | 0.0 | -100% |
| gas_ct | 0.808 | 0.0 | -100% |
| gas_st | 2.702 | 0.0 | -100% |
| oil | 0.613 | 0.0 | -100% |

## Additions (cumulative 2021→2025) — **decision basis**

_Attribution basis: **decision** (owner decision D-9(ii), signed 2026-08-04 (sitting Addendum K.2)). Scored on the DECISION basis (D-9(ii)). Additions verdicts on this basis are NOT comparable to any additions verdict committed before 2026-08-04, which were scored on the COD basis — the metric means something different. Retirements-side comparability is unaffected. See docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md._

Basis effect — decided in-window with COD **after** the window (invisible under the COD basis): `{'wind': 1.5, 'solar': 4.882, 'gas_cc': 4.0}`; commissioned in-window from a **pre-window** decision (dropped under the decision basis): `none` (GW).

| tech | actual GW | model GW | err | band | Δ-share (pp) |
|---|--:|--:|--:|:--|--:|
| wind | 1.619 | 3.0 | +85% | ❌ FAIL | +7.0 |
| solar | 13.066 | 9.762 | -25% | ❌ FAIL | -9.6 |
| gas_cc | 8.525 | 8.118 | -5% | ✅ PASS | +1.7 |
| gas_ct | 0.442 | 1.013 | +129% | ❌ FAIL | +2.8 |
| storage | 0.283 | 0.0 | -100% | ❌ FAIL | -1.2 |

COD-basis comparison (**not** the graded instrument; model total 11.512 GW vs decision-basis 21.893 GW):

| tech | model GW (COD) | model GW (decision) | band (COD) |
|---|--:|--:|:--|
| wind | 1.5 | 3.0 | ✅ PASS |
| solar | 4.881 | 9.762 | ❌ FAIL |
| gas_cc | 4.118 | 8.118 | ❌ FAIL |
| gas_ct | 1.013 | 1.013 | ❌ FAIL |
| storage | 0.0 | 0.0 | ❌ FAIL |

## System CO2 (headline: 2025, ±10%)

| year | model Mt | actual Mt | err | band |
|---|--:|--:|--:|:--|
| 2023 | 284.7 | 407.1 | -30% | (report-only) |
| 2024 | 263.8 | 420.6 | -37% | (report-only) |
| 2025 | 297.2 | 448.7 | -34% | ❌ FAIL |

> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** (the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new capacity-path information). Supply the keeper CO2 gap to attribute the split; absent it, the table reports the *total* hindcast error only. Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly overcounts (El Paso/SPP-side TX plants).

## Skill baselines (must beat on retirement recall + addition mix)

| baseline | retire GW | add GW | note |
|---|--:|--:|---|
| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |
| (b) announced-only | 65.381 | 147.445 | 2020-vintage planned schedule |
| (c) AEO2021 regional | — | — | report-only context (not computed here) |

---

## Verification — announced-exit verification ARMED vs ex-ante control

_Added 2026-08-22 by the verified-exits session. Paired arms, **one variable**:
`hindcast_verified_announced_exits` `True` (this bundle, key `4c2c7907805e679b`) vs
`False` (`results/hindcast/pjm-2021-2025-realized-exante-control`, key
`f9d5d795106d9c74`, `--no-verified-announced-exits`). Same tree, same posture
(`shipped`), same `retirement_rule` (`pipeline`), same vintage (2020), same solve
years [2021, 2023, 2024, 2025] with 2022 bridged. Nothing tuned; no parameter moved._

> **Why a purpose-solved control.** Neither committed PJM leg is a single-variable
> twin at HEAD. `pjm-2021-2025-realized` (2026-07-05) predates the field entirely —
> its `config.yaml` carries no `capacity_market_clearing` key and
> `retirement_years_coal: 1` where HEAD ships `3` — and both it and
> `pjm-2021-2025-shipped-ffr2e` ran `retirement_rule: legacy` where HEAD runs
> `pipeline`. The scorer's *actuals* have also moved (thermal actual 15.062 GW and a
> 20-unit >=300 MW denominator on the D-24 reachable set, against 11.121 GW / 17
> units in the 2026-07-05 leg). A treated-vs-committed delta would therefore
> confound the mechanism with code-vintage drift, so the control above was solved
> for this comparison.

### The four checks

| # | check | result |
|---|---|:--|
| 1 | `meta.json` records `hindcast_verified_announced_exits: true`, solved-sourced | ✅ `true`, `FromConfig` per META_RECORD_SPEC (reads the SOLVED gate, FFR-3R); `leakage_violations: []` |
| 2 | no retirement event for `6023_1` / `6023_2` / `869_2` / `869_3` | ✅ **zero events, 0.0 MW**, in every solved year |
| 3a | `retirements.per_fuel.nuclear.model_gw == 0.0` (was 4.097) | ✅ substantively — the `nuclear` key is **absent entirely** (the scorer emits a fuel only when it has events), not present as `0.0` |
| 3b | §c.5-1 lane shows zero reversal exposure | ✅ `reversal_exposure_gw: 0.0`, `reversal_instruments: []`, `reversal_rows: []` |
| 4 | false-retire delta attributable to the 4.1 GW nuclear alone | ❌ **NO — see the finding below.** The *suppression* is exact, but it induces a second, larger fleet change |

The control reproduces the phantom exactly, so the A/B is anchored: it retires
4.097 GW of nuclear and the scorer names the reversing instrument (IL CEJA
P.A. 102-0662, CMC award, 2021-09-15), carrying `reversal_exposure_gw: 4.097`.

### What the verification suppressed — surgical

| ledger events present in CONTROL only | year | fuel | MW | reason |
|---|--:|---|--:|---|
| `6023_1` (Byron 1) | 2022 | nuclear | 1164.0 | announced |
| `6023_2` (Byron 2) | 2022 | nuclear | 1136.0 | announced |
| `869_2` (Dresden 2) | 2022 | nuclear | 902.0 | announced |
| `869_3` (Dresden 3) | 2022 | nuclear | 895.0 | announced |

**4097.0 MW suppressed, of which 4097.0 MW is the four target units — OTHER = 0.0.**
Nothing outside the reversal set was touched, and **no exit was injected** by the
un-gated reversal read: the confirmed-EXIT channel keeps its RC-1B information gate,
as designed.

### FINDING — the mechanism induces +5.290 GW of additional coal over-retirement

The treated arm carries **24 retirement events the control does not**: all coal, all
`reason="economic"`, all in **2024**, totalling **+5.290 GW** (model coal 18.137 GW
vs the control's 12.847 GW, against 10.299 GW actual).

This is a real causal chain through the model's own economics, not noise, and the
screen's own diagnostics close it:

| screen year | coal `net_rev` $/kW-yr | going-forward bar | coal cap entering screen |
|---|--:|--:|--:|
| 2021 | 55.0 both arms | 58.5 | 46,399 MW both |
| 2022 (bridge) | 55.0 both arms | 58.5 | 46,399 MW both |
| **2023** | **treated 6.7 · control 8.7** | 58.5 | 46,399 MW both |
| 2024 | treated 155.2 · control 155.1 | 58.5 | **treated 28,262 MW (n=126) · control 33,552 MW (n=150)** |

Keeping 4.097 GW of zero-marginal-cost nuclear online from 2022 displaces fossil in
the merit order and softens energy prices, so 2023 coal net revenue lands **2.0
$/kW-yr lower** in the treated arm (6.7 vs 8.7, both far under the 58.5 bar). More
coal therefore clears the screen's consecutive-year test and executes in 2024 — the
5,290 MW cap gap at the 2024 screen is precisely the +5.290 GW delta.

The dispatch side corroborates the displacement: model CO2 is **lower** in the
treated arm in every scored year — by **23.098 / 27.137 / 29.162 Mt** in
2023 / 2024 / 2025 — consistent with ~32 TWh/yr of restored nuclear output backing
out coal. **Additions are byte-identical across every technology** (wind, solar,
gas_cc, gas_ct, storage all delta 0.000), so the entry screen is untouched; only the
retirement screen moved.

### Scoring effect — the fit gets WORSE, and the mechanism stays in (rule 1)

| metric | control (ex-ante) | treated (armed) |
|---|--:|--:|
| thermal GW retired (model) | 16.953 | 18.147 |
| err vs 15.062 actual | +12.6% ❌ | +20.5% ❌ |
| false-retire, RAW | 6.645 | 7.839 |
| false-retire, **IS-2020** | **2.548** | **7.839** |
| §c.5-1 reversal exposure | 4.097 | **0.0** |
| unit recall >=300 MW | 16/20 (80%) ✅ | 16/20 (80%) ✅ |

On the information-set-corrected basis — the one that *already* excludes the
reversal — the treated arm is **worse by 5.291 GW** (2.548 -> 7.839), because the raw
metric's 4.097 GW nuclear phantom is replaced by 5.290 GW of induced coal
over-retirement. Recall is unchanged at 80% PASS in both arms.

Per rule 1 `[R-STRUCT]` this is **not** a reason to revert. A plant that demonstrably
kept operating must not be false-retired, whatever it does to the residual, and the
degraded fit is the discovered root cause, not a regression: **PJM's coal economic
screen over-retires under softer prices**, and the nuclear phantom was partially
masking it — the phantom's 4.097 GW displaced coal that the screen would otherwise
have retired. The coal screen is the separate open question (rules 1/13/21); it is
**deliberately not chased here** and nothing was tuned to the score.
