# PRECOMMIT — capx D65-B: the coupled arming (Act A + Act B), one PR, one re-key

**Session:** capx D65-B · **Date:** 2026-09-06 · **Branch:** `claude/capx-d65b-coupled-arming-m4mzgv`
**Authority:** OWNER RULING **Q47** (capx ledger §3, r#42 amendment 2, verbatim option
*"Arm coupled, after D60-R3"*), released by r#46 am.1.
**Charter:** `FINDING-capx-d65-2026-09-05.md` §8.1 (why never Act A alone) and §9 (the six items);
`FINDING-capx-d64-2026-09-05.md` §2.4 (the level) and §4.5 closing clause.

Everything in this document is written **BEFORE the screen solve**. Its purpose is that no key,
no gate threshold and no expected direction can be chosen after seeing a result.

---

## 0. Preconditions, checked

| Precondition | Source | State |
|---|---|---|
| 1 — D60-R3 MERGED (#5038) | `git log origin/main` | **MET** (`15631b8c` closes the finding) |
| 2 — D77 CCS emission-rate seam fix MERGED (r#46 am.1, for item 6 only) | `git log origin/main --grep=D77` | **MET** — `ae8dd2a0`, an ancestor of this branch |

Both preconditions hold at branch creation, so items 1–5 and item 6 are unblocked in one pass.
The branch is cut FRESH off `origin/main` at `6887484f`.

---

## 1. The two acts

**Act B — a VALUE re-identification.** `ccs_retrofit_vom_adder` **8.0 → 2.95 $/MWh (2026$)**.
Read off the SAME ATB 2024 v4.0.0 basis as the screen's other two cost legs (capx D41 §2.3's rule:
host and island on ONE basis):

```
ATB Moderate NG 2-on-1 CC (F-Frame) 95% CCS  Variable O&M @2026 = 4.8
ATB Moderate NG 2-on-1 CC (F-Frame)          Variable O&M @2026 = 2.1
(4.8 − 2.1) × 1.090947  (2022$ → 2026$, constants.INFLATION_RATE) = 2.9456 → 2.95
```

NETL Rev 4a's 2.23 $/MWh (B31A→B31B.90) is the **cross-check**, not the basis. The shipped 8.0 was
`needs-citation`, stated no dollar-year, and cited a document that publishes 2.23.

**Act A — a (b′-1) DECLARED DEFAULT FLIP.** `ccs_retrofit_fixed_cost_co2_scaling` dataclass default
`False → True`; the frozen cache-key drop value stays `"False"`; the flip is declared in
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` dated `2026-09-06`.

**Why coupled** (D65 §8.1): Act A multiplies Act B's level by `k`, so arming the shape on an uncited
2.7× level compounds the error on exactly the high-`er` hosts the seam exists to re-price. Neither
half is admissible alone.

**DIRECTION, STATED BEFORE ANY SOLVE (rule 23):** re-identification makes retrofits **EASIER**.
Rule 14 `[R-ACCURATE]` keeps an accurate value whichever way it moves the answer.

---

## 2. Item 1 — the widened extract (D64 STOP 6), completed BEFORE Act B

* Source: OEDI `ATB/electricity/csv/2024/v4.0.0/ATBe.csv`, **102,696,929 B**, sha256
  `567dde9d85caa759bc3f2e42c9aa14a5f85e471ca4133ccc522e7a92e020297a` — **byte-for-byte the pinned
  source the committed extract already came from.** No new source, no new vintage.
* `fetch_nrel_atb.py` gains `EXTRA_PARAMETERS_BY_TECHNOLOGY = {"NaturalGas_FE": ["Variable O&M",
  "Heat Rate"]}` — a **per-technology** scope, so no other technology's row set grows.
* Regenerated `atb_2024v4_electricity_filtered.part{00..11}.csv`: **3,858 → 4,554 rows**.

**The regeneration is a STRICT SUPERSET, verified not asserted:**

| check | result |
|---|---|
| committed keys present in the regeneration | 3,858 / 3,858 |
| old-only keys (dropped) | **0** |
| `value` differing on a common key | **0 / 3,858** |
| `display_name` / `default` / `atb_year` differing | **0** |
| new-only keys | 696 = NaturalGas_FE × {Variable O&M, Heat Rate} (348 each) |

⇒ `NEW_ENTRY_COSTS` and `TECH_COST_MULTIPLIERS` **cannot move**, and
`tests/unit/config/test_atb_entry_cost_consistency.py` passes untouched.

**The asserted derivation** (`tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py
::TestRetrofitVomBasis`) pins `ccs_retrofit_vom_adder == derive_ccs_retrofit_vom_adder()`. It was
written and run BEFORE Act B and **failed for exactly the right reason** (`8.0 != 2.95`), which is
the evidence that item 1 is a precondition and not a rationalisation.

**A cross-check the widening closed as a by-product.** ATB's own unabated NG 2-on-1 CC (F-Frame)
**Heat Rate @2026 = 6.3 MMBtu/MWh**, which is exactly `min(HEAT_RATE_BINS["gas_cc"].values())` —
the `hr_ref` inside `ccs.ccs_retrofit_captured_ref_t_per_mwh` (the D50 seam-1 reference host). The
capex increment's host and the captured-flow reference host are now provably ONE host, from the
pinned bytes rather than by coincidence. Asserted by
`test_atb_host_heat_rate_is_the_seam_reference_host`.

---

## 3. THE RE-KEY, PRE-DECLARED

Act B is not a `_CACHE_KEY_OPTIONAL_FIELDS` member, so it has no drop value and **re-keys every
config unconditionally** (D65 §9 item 3; D41 §6.2's mechanic). Act A's own contribution is the
(b′-1) flip. Measured at HEAD, before any solve:

| ISO | mode | PRE-D65B | POST-D65B |
|---|---|---|---|
| CAISO | forecast | `0b0182cbddaa94af` | `2f3e1df634cae1d8` |
| CAISO | backcast | `0a71eefc01ae72b9` | `efebcc735768c122` |
| ERCOT | forecast | `b5ab30d0fae9f8a3` | `95d789d6dfb98831` |
| ERCOT | backcast | `65b24e52e89a348c` | `406cb30ad62bc27b` |
| MISO | forecast | `91be1877a6594913` | `6808780f515fce63` |
| MISO | backcast | `00263fcf15266128` | `b10d58628ba3a057` |
| NEISO | forecast | `51e4d85962487d16` | `31ca8b9d010f7e7f` |
| NEISO | backcast | `05e95034df140bbc` | `27e80d27acd995de` |
| NYISO | forecast | `20a7d5244dfa70ee` | `8e87bfe58f75212a` |
| NYISO | backcast | `b791330712d6c2fe` | `cadaba3d344e84b9` |
| PJM | forecast | `2c5d56102b3057bb` | `eaa3fbef5ff182c9` |
| PJM | backcast | `6f61207df8f4b398` | `3a566deac3a85682` |
| (global default) | forecast | `e5ecd4105ada3e58` | `547053bdfccd4264` |
| (global default) | backcast | `6a2845e50951394e` | `f61891696e671969` |

The PRE column is reconstructed at HEAD as
`ScenarioConfig(..., ccs_retrofit_vom_adder=8.0, ccs_retrofit_fixed_cost_co2_scaling=False)` — the
explicit `False` drops on the frozen drop value, so the config hashes as a pre-flip one. **It is
faithful**: its ERCOT forecast entry `b5ab30d0fae9f8a3` and the two global entries reproduce the
pins currently committed in `test_ercot_stageb_arming.py` / `test_persisted_identity.py` exactly.

**BACKCAST BEHAVIOUR IS BYTE-IDENTICAL** and so is every hindcast/crossover horizon ending before
2028: `ccs.py::apply_ccs_retrofit` returns at `if year < config.ccs_retrofit_available_year` (2028)
before any read of either field, and that call site is the only consumer of both. The backcast KEY
moves (a one-time cache MISS); no keeper, sidecar, determination or dashboard row does — committed
artifacts are files, not cache lookups. **No backcast keeper is re-solved by this lane.**

### 3.1 The STOP "the explicit-`False` path moving a key" — DOES NOT FIRE, and here is the decomposition

Read literally, that STOP would fire on a consequence the charter itself licenses (D65 §9 item 3:
Act B "re-keys every bare key unconditionally … there is no drop value to hide behind"). The STOP's
real content is that **Act A's drop-value mechanic must be intact**, which is measured by holding
the VOM at its shipped level:

| arm | explicit `seam 4 = False` key |
|---|---|
| **Act A alone** (`vom_adder` held at 8.0) | **`e5ecd4105ada3e58`** |
| pre-flip forecast default (the committed pin) | `e5ecd4105ada3e58` |
| both acts (HEAD) | `910b8cfcb2aa6a36` |

**Act A alone leaves the explicit-`False` path on the pre-flip key exactly.** The movement at HEAD
is Act B's, and it is unconditional by construction. STOP not fired.

---

## 4. A DEFECT THE CHARTER DID NOT ANTICIPATE, found and repaired before the screen

**What happened.** Act A's flip made the pair *(seam 1 EXPLICIT `False`, seam 4 at its default)*
**unconstructible**, because `__post_init__` refused seam 4 without seam 1. That pair is not
hypothetical — it is what the **D50/Q42 CONTROL ARM ITSELF** is
(`ScenarioConfig(ccs_retrofit_capex_co2_scaling=False)`, pinned by `test_d60_arming_batch.py`'s
*"(b′-1)'s useful inverse: a control arm keeps its bundle"*), plus **six committed bundles**:

`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing`,
`…/miso-2021-2025-realized-t1h-d53-sectorgate`, `…-d51ratio`,
`results/calibration/caiso251_arm_nomargin`, `…/nyiso192_astoria_panel`, `…/miso217_intermphys_B`.

All six carry `ccs_retrofit_capex_co2_scaling: false` with seam 4 **absent**. At the charter-literal
flip, reconstructing any of them raises — i.e. **the flip would have made the D50 control
unreachable**, which is the one thing rule 29(b) needs a control to be.

**Why the charter missed it.** Its line *"the validator's seam-1 requirement is satisfied because
Q42 armed seam 1"* is true of the DEFAULT path and says nothing about the explicit-seam-1-off path.

**The repair, and why it is the minimal one.** The distinction the guard actually wants is
**explicitness, not value**, and `__post_init__` provably cannot see it — it runs after binding,
which is the exact defect the repo's own `_scenario_config_init` / `_explicitly_set_fields` record
was built to fix (its docstring says so). So the pair resolution moves to that wrapper
(`_resolve_ccs_retrofit_fixed_cost_pair`):

* **explicit `seam 4 = True` with seam 1 off** → still **RAISES** (the incoherent ask; rule 24).
* **seam 4 at its default with seam 1 off** → **DEMOTED to `False`**: inert by construction
  (`k ≡ 1.0`), so this is the truthful record, and it drops from the hash on the frozen `"False"`
  drop value.
* **provenance unknown** (`dataclasses.replace`, `from_yaml` over a full dump re-pass every field)
  → demote, the same fallback convention `_explicitly_set_fields` already uses.

The dead `if …: raise` block in `__post_init__` is **deleted, not zeroed** (rule 26 `[R-DELETE]`).

**Verified:** all six bundles reconstruct with `seam 4 → False`; the explicit incoherent pair still
raises; and §3.1's decomposition (Act A alone → `e5ecd4105ada3e58`) is measured *through* this
repair, so the drop-value mechanic is intact under it.

**No solve-affecting behaviour changes for any armed config**: the default path is untouched
(seam 1 is on, so no demotion branch is reachable), and the demoted path is the one where seam 4
was inert anyway.

---

## 5. G-DRIFT (rule 29(b) doctrine), audited BEFORE the screen

`git diff <keeper sha> 6887484f -- src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference`, plus `constants.py` **first** (a matched cache key
is NOT a G-DRIFT verdict — `constants.py` is outside the key).

**Verdict: form 4 is VOID. A LIVE hunk exists, so the screen earns its control solve.**

| named hunk | classification | evidence |
|---|---|---|
| **SCN-LOAD `d14a7ed0`** (`DEMAND_GROWTH_RATES`, all six ISOs) | **LIVE** | Ancestry checked per incumbent: `9e48ff6` (ercot/neiso t1f), `2ef4326e` (miso), `e7412237` (nyiso), `b83e96ca` (caiso) are **PRE-hunk**; only `14f860fb` (pjm) and `e9d8263b` (GOLDEN-3) carry it. `constants.py` is outside the cache key, so a matched key would not have revealed this. |
| **wallclock P1 basis seed #5033** (`pipeline/solve.py`, `lp/model.py`) | INERT for the forecast path — timing/diagnostics accounting only | rule 29(b)'s "pure timing/diagnostics accounting" class |
| **D77 `ae8dd2a0`** (CCS retrofit emission-rate seam) | **LIVE**, and squarely in this seam | it is why r#46 am.1 made D77 a precondition of the batch: a converted unit's captured rate was being re-booked over by `campd_bins.apply_plant_emission_rates{,_v2}` after `evolve_fleet` |

**Consequences, stated at the gate rather than discovered later:**

1. The screen (item 5) uses a **same-HEAD ERCOT t1f control**, exactly as the charter pre-authorised
   — the committed ERCOT t1f is pre-hunk on `d14a7ed0` and cannot serve as form-4 control.
2. The batch's **board-level before/after is confounded by the demand vintage** for the four
   pre-hunk ISOs. This is reported at full magnitude and attributed, never netted. The clean
   comparison in this lane is the screen's arm-vs-same-HEAD-control differencing.
3. **The batch lands the whole T1-F board in ONE demand vintage — that is now one of its
   purposes**, and it is why the confound does not persist past this lane.

A second G-DRIFT re-audit is owed **before the batch** (r#46 doctrine) and will be recorded as an
addendum to this document.

---

## 6. Item 5 — the rule-29 SCREEN, pre-registered

**One leg, one year, on a CARBON-0 ISO.** RGGI ISOs are cap-bound on both constructions and cannot
discriminate (D65 §8.1), so NEISO is uninformative here. **Screen = ERCOT t1f** (~12 min), with a
**same-HEAD ERCOT t1f control** (§5 consequence 1).

**Screen year named before the screen runs:** the screen is the ERCOT t1f horizon's first retrofit
years, where D64 §2.4's census puts the mechanism's own measured footprint largest — **10.19 GW at
the ceiling in 2028 under Act B on the shipped shape, and 5.68 GW in 2029 under Act A + B** — never
the year with the biggest residual.

**The gate is STRUCTURAL and a STOP gate ONLY. It may kill the arm; it may never promote it.**
It is not gated on any residual.

| # | pre-registered structural gate | STOP if |
|---|---|---|
| G1 | every row that clears is an `er/phys` ≥ 1.27 host (D49 §1.3) | a row clears on an `er/phys` < 1.27 host |
| G2 | the identity `uplift/capex ∝ 1/k` holds on the cleared set | it does not |
| G3 | `k = 1` rows are byte-identical to the control | any `k = 1` row moves |
| G4 | no non-target load-bearing FC row flips PASS → FAIL | one does |
| G5 | the dispatch response has the direction and order of magnitude the pre-solve delta implies | it does not |
| G6 | wall/RSS within the leg's D60 envelope | beyond it |

**A carbon-0 ISO GAINING rows is NOT a STOP.** It is the accurate level's **pre-registered
signature** (D64 §4.5's closing clause, D65 §9 item 4). Recording it here, before the solve, is what
stops it being read as a regression afterwards.

Both screen bundles are **DELETED from `results/calibration/` before the PR merges** (rule 29(c),
owner ruling R-AV): every number this lane will ever cite from them lives in this document and in
`FINDING-capx-d65b-2026-09-06.md`, and git history is the record for the bytes.

---

## 7. Item 6 — the batch, pre-declared

Screen cleared **AND** D77 merged (both required). Sequential per rule 12 `[R-PARALLEL]`:

`ercot-t1f` → `neiso-t1f` (~8) → `nyiso-t1f` (~12) → `caiso-t1f` (~23) → `pjm-t1f` (~36) →
`miso-t1f` (~65) → `neiso-t3` GOLDEN-3 (~33 min).

Each: score → verdict → register **in place**, priors preserved at **`-pre-d65b`**. Reported at full
magnitude: FC-map moves against D64 §2.4's census and D65 §4's NEISO reading; the D50 §6.2 blast
radius reconciled; D77's §8 blast radius (retrofit-carrying bundles) reconciled.

**Matrix (six shards, one appended line each, last commit):** the `ccs_retrofit_screen` row's
`def`/`note` carries Act B (**no cell verdict moves** — Act B arms no mechanism); the
`ccs_retrofit_fixed_cost_co2_scaling` row's cells re-stamp `fc: K` where the arm is now the bare leg.

---

## 8. STOPs (the charter's, restated so none is reinterpreted later)

| STOP | state at this writing |
|---|---|
| extract/test absent (STOP 6) | **cleared** — §2 |
| a realized key ≠ its pre-declared value | armed; §3 is the declaration |
| any `k = 1` row moving | armed as screen gate G3 |
| a screen row clearing on any `er/phys` < 1.27 host | armed as screen gate G1 |
| the explicit-`False` path moving a key | **does not fire** — §3.1 decomposition |
| wall/RSS beyond each leg's D60 envelope | armed as screen gate G6 |

## 9. Scope discipline

Rules **22** (forecast mode only — no held-out year is solved, scored or registered by this lane),
**25** (a posture, no ISO's number crosses a boundary), **27** (exact on-disk bytes; blob-verify
every ≥300-line file after every push), **28**, **29**. Collisions: D60-R4 then D63 are the board
writers until they merge — **this batch registers AFTER both**. SCN lanes write the hindcast
namespace only. In `scenarios.py` this lane's lines sit in the D50 block; SCN-WS2a/2b's
`federal_ces_*` block and WS-1a's D34-guard region are not this lane's. Score and register **after
the final rebase**.
