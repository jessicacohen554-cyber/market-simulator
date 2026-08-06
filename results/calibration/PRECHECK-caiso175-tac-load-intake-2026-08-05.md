# PRECHECK — caiso-175: the CAISO TAC load-series intake (MWD-TAC + the 2023 coverage hole)

**Pre-registered 2026-08-05, BEFORE any price, dispatch or criterion value was read from
either arm.** Written while Arm A was still solving. Its purpose is the caiso-162 standing
lesson: fix the verdict rule and the quantity gate *first*, so the session cannot select a
rule that flatters the result it later sees.

Session id `caiso-175`. Lane: CAISO backcast calibration. Years **2023 / 2024 / 2025 only**
(rule 16 `[R-ALLYEARS]`, one bundle per arm, years sequential within the invocation per rule
12 `[R-PARALLEL]`). No out-of-training year is touched: CAISO holds a `complete` marker but
the **holdout spend freeze is ACTIVE and outranks it**, so 2022 / 2019 / ≤2021 / H1-2026 stay
fully quarantined. `calibration-complete.json` and `holdout-freeze.json` are **UNTOUCHED** —
both are owner acts.

---

## 1. Why this session exists

Two findings, both made before any solve, and neither of them a lever picked against a
residual.

### 1a. C7 and C8 were UNSCORED on the keeper — now closed, no LP

The keeper `2026-08-05-caiso-174-measured-fleet` carried **no
`legitimacy_diagnostics.json`**, so the two PROTECTIVE criteria scored `SKIPPED`:

```
[·] SKIPPED PROT  C7 diurnal shape (D-1)
[·] SKIPPED PROT  C8 forced-energy share (D-2)
```

The CAISO `complete` grant recorded this against interest as "a scorer-only gap under rule 21,
deliberately not repaired in this committed-artifacts-only lane". Rule 21 `[R-FORCED-BUDGET]`
says this class of gap is scorer-only — *"no re-solve, no bundle regen, and existing keepers
re-score in place"* — and the verdict tool itself names the fix. Generated and committed here.

**Result, recorded before the intake work began:** C7 **PASS**, C8 **PASS**, determination
**unchanged** at CALIBRATED-WITH-CAVEATS, 0 FAILs, same 2 ledgered caveats (C3a, C3c), D-10
12/12 · free 8/8. The keeper now scores **9 criteria instead of 7**.

**Recorded against interest — the raw D-1 diagnostic reports `FAIL` and the rubric does not.**
D-1 fails `ST_GAS` on profile correlation in 2024 (r 0.117) and 2025 (r −0.039). Those rows are
real and are **not** being dismissed. They do not raise a C7 FAIL because `score_shape` applies
rule 21's materiality screen — the gate binds only on classes ≥ 2 % of ISO load — and ST_GAS is
**0.6 / 0.4 / 0.1 %**. This is the rubric's own pre-existing constant (`PROTECTIVE_MIN_LOAD_FRAC
= 0.02`, owner amendment 2026-07-06), not a threshold chosen here, and rule 21 states the
consequence explicitly: *"smaller classes are reported by the D-1/D-2 diagnostics but never
gated — trivial-class shape/forcing is not worth structural work."* **No scorer constant is
touched by this session.** The divergence between `run_d1`'s own `gated` column (class-list
only) and `score_shape`'s (class-list **and** load share) is noted as a reporting inconsistency,
not repaired here, and not required for the verdict.

### 1b. The CAISO TAC load series was incomplete in two independent ways

Found by inspecting the committed input, not by chasing a residual.

**(i) MWD-TAC is missing entirely.** The live OASIS `SLD_FCST` domain carries **six**
CAISO-internal areas; `scripts/data/postprocess_oasis_downloads.CAISO_TACS` hard-coded
**five**, dropping `MWD-TAC` (Metropolitan Water District of Southern California). Because
`load_zonal_shares` **normalises the component TACs to 1.0**, this is not missing load — MWD's
load was silently re-apportioned **pro rata** across the other four. Named as an open
demand-input gap by caiso-172 §1.1, measured by caiso-173 §C (0.24–0.30 % of ISO load landing
north of Path 15 that belongs in SP15), and deliberately kept out of caiso-174 so that run's
one delta stayed attributable. **This is the session caiso-173 §C asked for**, in its own words:
*"Closing it means re-fetching the TAC series with `MWD-TAC` and adding its weights row: a
demand-input intake with its own authorization, in its own session."*

**(ii) 2023 covers 744 of 8,760 hours — and this was NOT previously on the record.** The
committed `CAISO_tac_load_hourly_2023.csv` spans **2023-01-01 → 2023-02-01 only**. The loader
says so out loud and falls back for the rest:

```
CAISO TAC-area load for 2023 covers 744/8760 hours; uncovered hours use the sample-average zone shares
```

So **91.5 % of 2023's hours ran on a flat January-average zonal split** — no diurnal shape, no
seasonal shape, for eleven months of a scored calibration year. Measured on the input: NP15's
hourly share standard deviation is **0.00374** in 2023 against **0.02615 / 0.03088** in
2024/2025, i.e. the 2023 series carries ~1/7th the hourly variation of the years either side of
it, purely as an artifact of the sample.

Both are rule 14 `[R-ACCURATE]` cases: the accurate data is public, fetchable and now on disk,
and the model was running on an estimate of it. Rule 14's exception (accurate data misaligned
to our representation) does **not** apply — this is the same series, same grain, same boundary,
merely complete.

---

## 2. THE PRE-REGISTERED VERDICT RULE — fixed before any number is read

This is an **input correction with zero free parameters**, not a tuned mechanism. Rule 1
`[R-STRUCT]` and rule 14 `[R-ACCURATE]` therefore govern the disposition, and they point the
same way: the corrected input **stays** regardless of which way the residual moves.

| Arm B outcome | Disposition |
|---|---|
| Determination holds (CALIBRATED-WITH-CAVEATS), **no new FAIL**, no new caveat slot | **PROMOTE** Arm B to keeper. The input is correct and the fit did not degrade. |
| Determination holds but a **criterion improves** | **PROMOTE**. Report the improvement as a consequence, never as the justification. |
| A criterion **degrades to a new FAIL**, or a new caveat slot is spent | **DO NOT PROMOTE. DO NOT REVERT THE INPUT.** Rule 14 is explicit: a worse fit on accurate data is a *discovered bug*, not a reason to restore the estimate. Keep Arm B registered as evidence, file the degradation as a root-cause issue, and **escalate to the owner**. |

**The third row is the one that binds.** The corrected TAC series is more faithful than the
truncated one whatever it does to C3a. Nothing in this session may be re-picked against a
residual (rules 5/13/24): the MWD weight is a 1:1 area containment, the 2023 coverage is simply
the rest of the same measurement, and there is no free parameter anywhere in either.

---

## 3. THE ARMS

Both arms are the **caiso-174 keeper recipe replayed byte-faithfully from its own `meta.json`**
via `scripts/replay_keeper.py` (the only sanctioned recipe reconstruction). They differ in
**exactly one object: the committed CAISO TAC load series on disk.** No `ScenarioConfig` field
differs, no flag differs, no offer curve differs.

| arm | bundle | TAC series |
|---|---|---|
| **A — CONTROL** | `caiso175_control` | as committed: 5 areas, 2023 = 744 h |
| **B — TREATED** | `caiso175_tac_intake` | corrected: 6 areas incl. MWD-TAC, 2023 = 8,759 h |

**Why a fresh control rather than differencing against the keeper's committed metrics.**
caiso-174 measured incidental code drift between head `789e28b8` and its own head at C3a
−0.02/−0.00/−0.01 $/MWh, and stated that without its control that residue *"would have been
misattributed"*. The keeper was solved at `ae7658d0`; this head is later. Arm A is what makes
`B − A` the input correction and nothing else.

**Arms run SEQUENTIALLY, never concurrently** (rule 12): one CAISO plant-level multi-zone LP
peaked at 8.31 GB resident at caiso-174 on this 15 GB / 4-core box.

### 3a. The attribution design — the two corrections separate BY YEAR, for free

This is why one A/B suffices and no third arm is needed:

* **2024 and 2025 were already fully covered**, so `B − A` there is **MWD-TAC alone**.
* **2023 carries both** corrections, so its `B − A` is MWD + the coverage restoration.

The MWD-only effect is therefore measured directly in 2024/2025 and the 2023 coverage effect is
the remainder. No arm is spent to separate them.

---

## 4. THE QUANTITY GATE — run and PASSED before Arm A was launched

The caiso-162 lesson: *a `run_config` recording an input as changed is not evidence the LP saw
it.* Verified on the input itself, before any solve.

**(a) The re-fetch is byte-faithful on everything it did not add.** Every pre-existing
(timestamp, area) row of the committed series is reproduced by the re-fetch to
**max |Δ| = 0.000000 MW**, with **0 rows differing** and **0 overlap rows missing**, in all
three years. The intake therefore *adds* and never *rewrites*.

| year | committed rows | corrected rows | new area | MWD mean |
|---|---:|---:|---|---:|
| 2023 | 3,720 | 52,560 | MWD-TAC | 119.1 MW |
| 2024 | 43,915 | 52,698 | MWD-TAC | 171.6 MW |
| 2025 | 43,800 | 52,560 | MWD-TAC | 144.1 MW |

**(b) The correction reaches the model's zonal shares, and by the predicted magnitude.**

| year | zone | control share | corrected share | Δ (pp) |
|---|---|---:|---:|---:|
| 2023 | NP15 | 0.40787 (sd 0.00374) | 0.39751 (sd **0.01998**) | **−1.036** |
| 2023 | LA_BASIN | 0.36977 | 0.38129 | +1.152 |
| 2023 | SP15_rest | 0.07654 | 0.08292 | +0.638 |
| 2024 | NP15 | 0.39248 | 0.38984 | −0.264 |
| 2024 | SP15_rest | 0.07991 | 0.08611 | +0.620 |
| 2025 | NP15 | 0.38390 | 0.38176 | −0.214 |
| 2025 | SP15_rest | 0.08095 | 0.08609 | +0.514 |

**caiso-173 §C is independently confirmed, not merely re-asserted.** It predicted MWD's
misplacement would move **0.241 / 0.297 / 0.243 %** of ISO load out of north-of-Path-15; the
measured NP15 deltas in the MWD-only years are **0.264 / 0.214 pp**. Same object, same order,
derived from the data rather than from its estimate.

**The 2023 coverage restoration is visible as shape, not just level:** NP15's hourly share sd
rises **0.00374 → 0.01998 (5.3×)**, into family with 2024/2025 (0.026 / 0.031). That is eleven
months of diurnal and seasonal structure the LP did not previously see.

**(c) The constants edit alone is INERT — verified, not assumed.** With the `MWD-TAC` weights
row present but the *control* series on disk (no MWD rows to match), the resolved shares
reproduce the pre-edit control values **exactly** (2023 NP15 = 0.40787, sd 0.00374). So Arm A is
a true control: the only live difference between the arms is the data.

---

## 5. What this session does NOT do

* **No scorer constant, threshold or gated-class set is changed.** C7/C8 close by generating the
  artifact the rubric already asks for.
* **No `ScenarioConfig` field is added.** Consequently no new mechanism-matrix row is minted by
  duty (c); the matrix touch is duty (b) on the existing `path15_load_split` row's neighbourhood
  plus a new `tac_load_coverage` row for the input object itself.
* **No out-of-training year is solved, scored or registered.** The freeze is active and outranks
  CAISO's `complete` marker.
* **No static `load_share` fallback in `iso_configs` is re-derived.** Those are LCT peak-load
  derived — a different basis — and are the fallback, not the binding path, for a year with
  measured hourly coverage. Touching them would be an unforced second change.
* **No attempt is made on C3a or C3c as such.** Their in-model lever queues are closed on the
  record and both rest on named data walls (caiso-141 A2 pumped storage; the SoCalGas OFO
  declaration record). If this input correction moves either, that is a consequence to be
  reported, not the goal it was chosen for — and it does not reopen a closed lane.

---

## 6. Rule 22 leave-one-year-out

This session fits nothing and moves no free parameter, so LOYO reduces to the
no-held-out-degradation check across 2023–2025. Recorded here so it cannot be reinterpreted
later: a result carried by a single year — in particular by 2023, which receives the larger of
the two corrections — must be reported as such, and the 2024/2025 MWD-only years are the
independent check that the direction is not a 2023 artifact.
