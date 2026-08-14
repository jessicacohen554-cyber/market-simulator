# PRECOMMIT — ercot-196: the RULE-18 GRAIN REPAIR, re-registered (the chartered ercot-187 successor)

**Pre-registered and pushed BEFORE any measurement, any seam proof, any derive
and any solve.** The construction, the eligibility read, the seam proofs, the
kill gates, the honest-outcome clause, the direction-blind promotion rule and
the retention evictions are fixed here and are **not renegotiated after
measurement**.

Keeper at session start, verified at this session's HEAD:
**`2026-08-12-run192-arm-coal-peak`**, bundle
`results/calibration/ercot192_arm_B` — determination **NOT-YET**, fail set
**{C3a-2023, C3b-2023}**, C3c the single ledgered **CAVEAT ×3**.

---

## 0. Shorthand, authorization, scope

### 0.1 Shorthand reconciliation (recorded, not silently resolved)

The task prompt opens this lane as **ERCOT-195** and the designated branch is
`claude/ercot-195-lever-selection-scssqc`. **`ercot-195` is already spent on
`main`**: the L-SCAR-SCREEN-2 session (2026-08-13) registered
`## ercot-195 … L-SCAR-SCREEN-2: V0 FAIL` in `docs/calibration-log/ercot.md`
and closed with *"Next shorthand: **ercot-196**."*

This session is therefore **ercot-196** in every artifact, log entry, bundle and
run id. **The branch keeps its designated name** (`claude/ercot-195-…`) because
the branch is assigned, not chosen. The prompt was authored before the L-SCAR
session landed. Nothing else about the lane changes.

### 0.2 Authorization

The **chartered ercot-187 successor**, still open: ercot-187 was diverted to the
leap-day derive defect and the golden-hash attribution (both hygiene, no solve),
so the A/B this charter calls for has never been run. The charter is
`results/calibration/FINDING-ercot186-rule18-grain-2026-08-10.md` §5, which
descends from owner sitting 2026-08-09, decision card **D3 option (ii)**
(`docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §4(b2) + §10).

**Admissibility under card R-A (signed 2026-08-13).** R-A holds ERCOT at NOT-YET
and re-charters it **off the 2023 price criteria** — no C3a-2023 spend (Q-B
final, item 11 CLOSED) and **no C3b-2023-targeted determination rounds**. This
lane is neither. It is a **rule-18 `[R-PHYSICS]` correctness repair** of a
licensing gate that does not bind, on a mechanism already armed in the keeper.
Card D3 fixed that reading in advance: *"It is a **legitimacy** item, not a
residual item: an armed mechanism whose licensing gate does not bind is a
rule-18 defect independent of whether fixing it improves any metric."*

### 0.3 The C3b-2023 ceiling, stated up front (R-A requirement)

C3b-2023 movement in this session is a **side-effect, reported at full
magnitude, never an objective and never a promotion basis.** Its ceiling is
already measured on this keeper
(`results/calibration/ercot193_c3b_decomposition.json`):

| 2023 C3b counterfactual | NRMSE |
|---|---|
| as solved (keeper) | **0.6041** |
| Aug+Sep perfect | 0.1185 |
| Jun–Sep perfect | 0.0513 |
| **everything BUT Aug/Sep perfect** | **0.5923** |
| Aug+Sep share of squared residual | **0.9615** |

So C3b-2023 is **96.2 %** the same closed Aug/Sep-2023 model-class object as
C3a-2023: a run that were **perfect in all ten other months** still reads
**≈ 0.59** against the **0.20** bar. **No arm in this lane can pass C3b-2023,
and none is claimed to.** The fail set is expected to remain {C3a-2023,
C3b-2023} and the determination **NOT-YET**.

### 0.4 Scope fences (binding)

* **ERCOT only** (rule 25 `[R-ISO-SCOPE]`). The one non-ERCOT site sharing this
  grain defect — `model/commitment.py::_ra_bridge_unit_params`, the CAISO RA
  bridge, which carries its own class-table workaround for the zero-physics
  case — is **named and left untouched**, as at ercot-186.
* **`--years 2023 2024 2025` only, ONE invocation per bundle, years sequential**
  (rules 12/16/22). ERCOT holds **no** `complete` and **no** `final` marker, so
  2019–2022 and H1-2026 stay quarantined: unsolved, unscored, unread. No marker
  is sought.
* **No band is re-chosen.** `constants.FASTSTART_POOL_MIN_DOWN_HOURS = 2.0` is
  untouched and **no min-run bound is added** to this tier.
* **No composition change.** `own_mask` replace-by-mask, the ladder, the
  boundary, the VOLL cap and the P1-only seam are untouched.
* **No derive, no artifact re-derivation** (rule 23 `[R-FROZEN-DERIVE]` is not
  engaged by the lever): this session changes only **which rows are licensed to
  read** a frozen artifact.
* **No offer-side C3a-2023 lever**, no coal lane, no depth lever, no storage
  offer surface; West/Panhandle topology stays closed; ERCOT-148/149 stays armed
  and un-repealed; the frozen composition lane (fault-1 double-count) stays
  owner-gated and is not opened.

### 0.5 DO-NOT-REDO check, performed BEFORE this document (rule 28 duty (a))

`docs/codebase-site/data/mechanism-matrix/ERCOT.js`:

* `ercot_faststart_pool_plant_physics` — **`O`** (open; verdict not reached at
  ercot-186 because that session stopped at its seam proof).
* `ercot_faststart_pool_offer` — **`K`**, evidence ercot-158, carrying the
  ercot-176/186 annotation that names exactly this defect.

**No cell in this family is adjudicated `R`/`I`/`G` against a physics-grain
correction**, so nothing is being re-tested. The lever comes off the ERCOT queue
as §5.1 item 25's own named successor.

---

## 1. THE DEFECT (carried from ercot-186 §1, verified merged at HEAD)

`assembly.py` stamps `min_run`/`min_down` **only on the committed anchor slice**;
every `mustrun`/`sync`/`econ*`/`peak*` row is constructed `0, 0` — deliberately,
so a bid tranche acquires no UC coupling. The fast-start pool's rule-18 gate then
evaluates

```python
if float(getattr(gen, "min_down_hours", 0) or 0) > FASTSTART_POOL_MIN_DOWN_HOURS:
    continue
```

on rows that all read `0`. **The test is False for every row it can reach.** Its
only effective filter is its row universe, `{"CT_PEAKER"}` — a hard-coded class
tuple, which is what rule 18 `[R-PHYSICS]` forbids.

Measured at ercot-186 on the then-keeper fleet: the shipped gate rejects
**0 of 486 / 486 / 497** CT bid rows in 2023 / 2024 / 2025.

---

## 2. THE CONSTRUCTION — already merged, default-off, unchanged here

**This session adds no mechanism and writes no new solve-affecting code.** The
substrate landed at ercot-186 and is verified present at HEAD:

* `Generator.plant_min_run_hours` / `plant_min_down_hours`
  (`data/fleet/__init__.py:203-204`), stamped by `assembly.py:1224-1225` with
  the values assembly already computes (`bin_min_run` / `bin_min_down`). The
  UC-coupling tags `min_run_hours` / `min_down_hours` are **untouched**.
* `offer_surfaces._plant_unit_physics` (`:2593`) — the ercot-176 Amendment-2
  read generalized: `max` over the prefix's rows of **both** fields.
* Both pool bodies — stepped (`:2881`, gate at `:2897`) and the ercot-178/180
  `contpct` body (`:3076`, gate at `:3090`) — evaluate the **same unchanged
  bound** at plant grain under
  `ScenarioConfig.ercot_faststart_pool_plant_physics` (`scenarios.py:8179`,
  default **False**), cache-key registered dropped-at-default (`:882`, `:1173`)
  and tier-tagged (`:12982`).
* **Zero new fitted scalars.** The flag is a boolean, the bound is the existing
  constant, the stamped values are assembly's own.

**The pre-repair row-grain test is retained ONLY under `plant_md is None`**
(`:2913-2917`, `:3103-3107`) — i.e. exclusively on the flag-off path, so the
control replays the keeper byte-identically. Rule 26 `[R-DELETE]` is discharged
**on promotion**: if this arm becomes the keeper, the flag *and* the pre-repair
branch are deleted outright in the promoting commit. The flag is transitional —
an A/B switch, not a standing option — and this precommit is the record of that
obligation.

**What is deliberately NOT introduced** (unchanged from ercot-186 §2c): no
class-table fallback ladder (a plant reading `md = 0` is admitted; against a 2 h
**upper** bound the published `CT_COMMITMENT_PARAMS` table, uniformly 1 h, would
license identically, so a ladder would be a second mechanism for one phenomenon,
rule 19); no change to the row universe (`CT_PEAKER` remains the ladder's
*measured class provenance*, which after this change is a distinct filter from
the physics gate — exactly the state rule 18 requires). The residual weakness is
disclosed, not hidden: the corrected gate still cannot distinguish *measured 0*
from *unmeasured*, which is not load-bearing at this bound and must be revisited
by any future re-banding of this tier.

---

## 3. SEAM PROOFS — re-run at THIS HEAD, on the run192 keeper fleet, before any solve

`scripts/probes/ercot186_grain_seamproof.py`, all three years, no LP built,
written to `results/calibration/ercot196_grain_seamproof.json`.

**They are re-measured rather than inherited**: ercot-186 measured on the
`ercot185_shapedarm_B` fleet, and the fleet basis has moved twice since (run191's
DAM-deriver repairs, run192's year-keyed coal `_peak` level). Inheriting those
numbers would be quoting a measurement of a different object.

* **SP-1 — RESTATED CORRECTLY (this is the charter's first correction).**
  The pre-registered claim is what ercot-186 actually established, not what it
  asserted:
  1. the stamp equals `max(stamped, max-over-rows)` **by construction**; and
  2. it equals the ercot-176 Amendment-2 read **exactly on the prefixes that
     have a committed tranche** — 179 of 219 at ercot-186.

  **The 40 no-committed-tranche prefixes are the SECOND FACET of the defect, not
  a falsifier.** Their cause is mechanical and single: assembly drops any tranche
  with `cap <= 0.5` MW, so a CHP-dominated plant whose committed band sits below
  that threshold emits no committed row, and the physics is then recorded
  **nowhere in the fleet** — the ercot-176 row-read returns `0` for it too. The
  stamp does not depend on which tranches survive, so it repairs both facets.
  **Falsifier: the equality failing on any prefix that HAS a committed tranche.**
  The no-committed-tranche count is *reported*, not gated.
* **SP-2 (the defect is real).** With the flag OFF, the row-grain gate rejects
  **0** CT bid rows in every year. **Falsifier: any rejection** — the defect
  would be mis-stated and this session stops and re-reports.
* **SP-3 / SP-3b (the corrected gate's scope, MEASURED, reported at full
  magnitude).** With the flag ON: CT plants in the row universe, how many clear
  `md <= 2`, how many are excluded, the excluded plants' `md`, the plant min-down
  histogram, and whether the two candidate reads (stamped vs row-max) reach the
  same eligibility set. **No bound moves in response to this number** — the
  ercot-176 discipline (17 CC plants deliberately not recaptured) is standing.
* **SP-4 (inertness determination — a MEASUREMENT, not a prediction).** Whether
  the arm's `(markup, own_mask)` pair is array-equal to the control's, per year.
* **SP-5 (no other consumer moved).** `FleetArrays` built from the same fleet is
  array-equal with and without the stamp, field by field. **Falsifier: any array
  differs.**

**Falsifier discipline.** SP-2 / SP-4 / SP-5 and SP-1's *corrected* claim are
falsifiable stops: any of them firing ⇒ **stop, report, register nothing**.
SP-3/SP-3b are measurements with no falsifier by construction.

---

## 4. PREDICTIONS — falsifiable, fixed before measurement

* **P-1.** SP-2 holds: the shipped gate rejects zero rows in all three years.
  *Falsifier: any rejection.*
* **P-2 — THE INERTNESS PRIOR IS DEAD AND IS NOT RE-REGISTERED.** The matrix
  note's standing prior (*"CT physics is uniform at min-down 1 h … a loss of
  PROTECTION, not a known mis-scoping"*) was **FALSIFIED at ercot-186**. What is
  pre-registered instead is the **measured scope**, carried forward as the
  expectation to be re-tested at this HEAD: **2024 and 2025 array-equal; 2023
  moves ~76,845 row-hours, 173 → 168 rows priced, via the single exclusion of
  `CT_PEAKER_South_Central_p6243`.** **NO DIRECTION OF PRICE EFFECT IS
  PREDICTED, and none may be inferred**: composition is replace-by-mask, so
  withdrawing pool ownership of five rows returns those row-hours to the other
  surfaces' markup, which is not ordered against the pool's by construction.
  *Falsifier of the scope claim: the excluded-plant set or the moved-year set
  differs at this HEAD.* A falsified scope claim is **reported and the session
  continues** — it re-describes the object, it does not invalidate the repair.
* **P-3.** No live gate in §5 fails. *Falsifier: any live gate fails, reported
  as REJECTED-AS-ARMED at full magnitude before §6's promotion question.*

---

## 5. KILL GATES — verbatim from the ercot-186 charter, re-based to the run192 keeper

Baselines read **this session off the keeper's committed artifacts**
(`calibration_verdict.py --run-id 2026-08-12-run192-arm-coal-peak`;
`scripts/probes/_ercot173_ab.py` on `ercot192_ctl_A` → `ercot192_arm_B`;
max-zonal tails per the `gen_ercot193_attestation.py` basis). No solve was run to
produce them.

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a (rubric) | **FAIL −33.2 %** | PASS −0.8 % | PASS −7.5 % |
| C3b (rubric NRMSE) | **FAIL 0.604** | PASS 0.135 | PASS 0.096 |
| C3c model tail >$200, **max-zonal** (actual) | **58** (181) | **22** (53) | **1** (31) |
| C3c model tail, scorer demand-weighted basis | 57 | 22 | 1 |
| shed hours | **4** | **1** | **0** |
| spurious mid-band | **9** | **11** | **0** |
| scorer `c3a_hub_pct` | −24.38 | +7.88 | +0.73 |
| coal above product ceiling (TWh) | 0.1213 | 0.1838 | 0.1095 |

*Both C3c bases are pre-registered because they disagree in 2023 (58 max-zonal
vs 57 demand-weighted) — the ercot-192-filed basis defect. **The gate binds on
the max-zonal basis**, which is the ledgered one; the demand-weighted count is
reported alongside.*

* **G-SHED — PRIMARY.** Shed-hour counts **4 / 1 / 0** must not RISE in any
  year. *(The ercot-48/49 manufactured-shortage signature; this gate has killed
  price-formation arms in this ISO twice.)*
* **G-C3c.** The ledgered max-zonal tail counts **58/181, 22/53, 1/31** must not
  degrade (the model count must not move AWAY from the actual count) in any year.
* **G-COAL148 — CARRIED LIVE** (D2 lineage: PRECOMMIT-ercot172 §5, carried live
  by the 2026-08-09 owner ruling, and live on every keeper since). Coal dispatch
  above the measured product ceiling may not rise more than **+0.5 TWh** in any
  year. *Screened by construction: this session changes no availability, no
  ceiling and no coal row — the pool leg touches merchant CT bid rows only — so
  any non-zero coal move is a **falsifier of that claim**, not an accepted cost.*
  Harness `scripts/probes/ercot185_coal148.py`.
* **G-OWNER.** **C3a-2024 and C3a-2025 keep PASS**, and **C3b-2024 stays
  ≤ 0.20** — the criterion-years the keeper lane has already won, protected
  explicitly.
* **G-SPAN.** In every year: no class's annual energy moves more than **0.5 %**.
  *(G-BIT is declared **N/A pre-solve**: the correction is year-agnostic — it
  applies to every year's fleet identically — so a year-specific-rule gate has no
  object here, and G-SPAN replaces it. Same disposition and reason as
  PRECOMMIT-ercot185 §6 and PRECOMMIT-ercot186 §5.)*
* **G-SPUR.** The spurious mid-band count (**9 / 11 / 0**) must not increase in
  any year.
* **G-DOF.** **Zero** new fitted scalars; `n_entries 18` / `n_residual 6`
  unchanged. Satisfied by construction.
* **G-D2.** The pool's D-2 attribution and D-4 window both stay clean: the
  mechanism sets no `min_gen`, so forced-energy and off-window-binding exposure
  are vacuous by construction. Scored as **D-4 FAIL rows identical A↔B** (the
  pre-existing CT_PEAKER condition the keeper carries; C8 records CT_PEAKER
  immaterial at 1.6 % of ISO load with D-2 reading 10.7 % forced in 2023). **Any
  new row is a failure.**
* **Rule 22 LOYO** — leave-one-year-out within 2023–2025 before any promotion.

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such at full magnitude.
The gates are not renegotiated after the solve.**

---

## 6. THE HONEST OUTCOME, PRE-REGISTERED — three branches

**(i) The arm is INERT (SP-4 array-equal in all three years).** The correction is
a pure legitimacy repair: identical prices, identical dispatch, a gate that now
actually tests something. **Both runs are still registered, all three years**
(rules 15/16), and **both registrations state plainly that the two bundles are
numerically identical**, so the dashboard is never read as two independent
results. The ercot-176 Amendment-3 disposition (*"registering a bit-identical
duplicate would put the same numbers on the dashboard twice"*) is deliberately
**NOT** followed, and the difference is stated: at ercot-176 the arm was a
*candidate mechanism* that would have added nothing; here the arm is the
**corrected form of a mechanism already armed in the keeper**, so the keeper
itself must move onto it. Promotion in this branch is **on legitimacy alone**,
and the FINDING will say exactly that — no metric gain is claimed and none
exists.

**(ii) The arm MOVES the numbers and every live gate passes.** Promote, per §7,
with the per-year deltas reported in full and LOYO cleared first.

**(iii) The arm MOVES the numbers and a live gate FAILS — including if the fit
gets WORSE. THIS IS THE BRANCH MOST LIKELY TO FIRE**, because the arm moves
**only 2023** — the single year carrying both of ERCOT's failing criteria. Per
rule 1 `[R-STRUCT]` the correct physics **stays in**: a vacuous gate is not
restored because the residual moved the wrong way, and the resulting residual
becomes a named root-cause item, **not grounds to revert**. The mechanical
verdict is recorded **REJECTED-AS-ARMED and is not rewritten**; this session does
**not** self-promote over a failed gate. It escalates to the owner's standing
structural standard with the measurement attached. If the failure is **G-SHED**
(the primary), the escalation is stated rather than papered over: the honest
alternatives are (a) promote under the structural standard with the shed
regression disclosed, or (b) **disarm `ercot_faststart_pool_offer` entirely** —
because a mechanism that can only pass its gates while its licensing test is
vacuous has not earned its keeper slot. **This session will not choose (b)
unilaterally.**

---

## 7. DECISION RULE, and the DIRECTION-BLIND PROMOTION RULE

1. **SP-1(corrected) / SP-2 / SP-4 / SP-5 pass** — else stop, report, register
   nothing. SP-3/SP-3b are reported.
2. **Settle `p6243`** per §8 (it does not gate the A/B; it gates what is *said*
   about the exclusion).
3. **A/B pair** via `scripts/replay_keeper.py` on `ercot192_arm_B`, control and
   arm **STRICTLY SEQUENTIAL, ONE invocation at a time** (rule 12; ~12.7 GB peak
   on a 15 GB box):
   * control `results/calibration/ercot196_graincontrol_A` — **zero delta**, the
     same-HEAD reproduction that separates HEAD drift from the mechanism;
   * arm `results/calibration/ercot196_plantphysics_B` —
     `--set ercot_faststart_pool_plant_physics=true`, the single delta.
4. **Legitimacy diagnostics + attestation + scoring**, both runs.
5. **Both runs registered** on the dashboard whatever the outcome (rule 15),
   in this session.

**PROMOTION RULE — DIRECTION-BLIND, fixed here.** The promotion decision reads
**only** (a) each live kill gate's PASS/FAIL and (b) LOYO. It does **not** read
the sign or the size of any C3a, C3b or C3c movement.

* **All live gates PASS and LOYO clears ⇒ PROMOTE** — whether the residuals
  improved, worsened, or did not move at all. *This is the half that makes the
  rule direction-blind: a worse C3a-2023 or C3b-2023 is not grounds to withhold
  promotion of a correct physics gate (rule 1), and a better one is not the
  reason for it.* The promoting commit also discharges rule 26 (§2): the flag and
  the pre-repair branch are deleted.
* **Any live gate FAILS ⇒ DO NOT SELF-PROMOTE.** Record REJECTED-AS-ARMED
  unrewritten and escalate per §6(iii).

No residual movement is a gate, a target, or a promotion basis anywhere in this
lane.

---

## 8. THE `p6243` QUESTION — settled this session, with its rule fixed now

ercot-186 excluded exactly one plant, **`CT_PEAKER_South_Central_p6243`**,
assembled min-down **8 h** / min-run **8 h** — four times this tier's 2 h
SCED-startable bound, on a CT-classified plant. The charter requires this session
to settle whether that value is **correct** or a **CAMPD `Min_Down_Hours`
artifact**.

**Pre-registered decision rule (rule 14 `[R-ACCURATE]`), fixed before looking:**

* The question is decided **on the plant's own source evidence** — its CAMPD
  operating record (actual observed off-durations between runs), the bin-sheet
  provenance that produced `bin_min_down`, and the unit's identity/technology in
  the plant registry — **never** on whether excluding it is convenient, and
  **never** on what it does to a residual.
* **If the 8 h is CORRECT** (the plant's measured conduct is genuinely
  slow-cycling, e.g. it is not a simple-cycle peaker in fact): the exclusion is
  right, the gate is doing its job, and that is the finding. **The bound is not
  moved to recapture it** — the ercot-176 precedent (17 CC plants deliberately
  not recaptured) is the standing discipline and is not renegotiated here.
* **If the 8 h is an ARTIFACT** (a derivation defect in the bin sheet or the
  CAMPD read): the defect is **named and root-caused**, and the repair is a
  **separate, named successor with its own precommit** — it is *not* folded into
  this arm, because a data repair discovered mid-session and applied to the same
  A/B would make the A/B a two-delta comparison.
* **Either way the gate's grain is right**, and either way **this arm is
  unchanged**. What is open is one plant's *input*, not the licensing
  construction. The finding records the answer with its evidence whichever way it
  falls.

---

## 9. Governance, bookkeeping, retention

* **Rule 15 `[R-DASHBOARD]`** — both runs registered + committed + pushed in
  **this** session; the FINDING and the dashboard carry the result, not chat.
  The replay path writes no `metrics.json` and no `legitimacy_diagnostics.json`,
  so both are generated explicitly: `scripts/legitimacy_diagnostics.py --bundle`,
  and the metrics sidecar via `calibration_verdict.write_metrics_sidecar` on a
  **resolved** path. Attestations follow the `gen_ercot193_attestation.py`
  pattern on the **max-zonal** C3c basis.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, ONE invocation, ONE bundle
  each. No single-year keeper, no single-year registration.
* **Rule 22 `[R-HOLDOUT]`** — ERCOT holds no marker; `--years` never leaves
  {2023, 2024, 2025}; no out-of-training year is solved, scored, read or
  registered; none is sought.
* **Rule 23 `[R-FROZEN-DERIVE]`** — **not engaged by the lever.** No derive is
  re-run and no artifact re-derived; the pool artifact, its ladder and its
  `pool_frac` are frozen and untouched. (The §10 hygiene item is a *measurement
  and a convention adjudication*, and if it ends in a re-derivation that
  re-derivation is a **named successor with its own precommit**, never a change
  landed inside this lane.)
* **Rule 24 `[R-REGISTRY]`** — one registered `ScenarioConfig` field, already
  merged, cache-key registered dropped-at-default, recorded in both bundles'
  `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-gated throughout; the CAISO RA bridge's
  sibling defect is named, not touched. No cross-ISO verdict is minted.
* **Rule 26 `[R-DELETE]`** — the transitional flag and the retained pre-repair
  branch are **deleted on promotion**, in the promoting commit (§2, §7).
* **Rule 27 `[R-PUSH]`** — `offer_surfaces.py`, `assembly.py`,
  `fleet/__init__.py` and `scenarios.py` are ≥300-line core files. This session
  **expects to write none of them**; if any is touched, the edit is made LOCALLY,
  the exact on-disk bytes are pushed, and the blob is verified against the
  **remote** before the next commit. No push runs while an LP solve is running.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (a) the DO-NOT-REDO check preceded this
  document (§0.5); duty (b) the `ercot_faststart_pool_plant_physics` cell verdict
  + citation is stamped in **this** session, rejection included; duty (c) the row
  already exists (landed with the field at ercot-186); duty (d) no cross-ISO
  verdict.
* **No PR** unless asked. Pushes follow the pack-size rules.
* **Retention (top-15 per ISO).** ERCOT stands at **15** registered runs.
  Registering this pair displaces the **two oldest unprotected** runs —
  **`2026-08-06-run173b-event-cap-reconc`** and
  **`2026-08-07-run176-control-offline-increment`** — named here, before the
  fact, and subject to `dashboard_add_run.py`'s own protected-set check at
  registration.

---

## 10. HYGIENE — the ERCOT-137 anchoring convention (must not displace the lever)

Filed in the DOF ledger at ercot-192, on the `coal_offer_margin_level /
_anchor` (ERCOT-137, limb A) entry:

> *"OPEN, reported not buried: this identification pools the four subsets'
> `bot_p50` RAW, with no fuel anchoring, while its registered anchor 1.7387 is
> the THREE-year mean and the pool sits at the 2024/25 res-hours mean fuel
> ~1.7040 — anchoring it consistently would move the level +0.38 = 0.41× its own
> band. Inside the band, so not a defect that changes arming; it is a convention
> inconsistency in the committed ERCOT-137 derivation."*

**Disposition rule, fixed here.** This session **either** closes the convention
question on the record with its measurement attached, **or** re-files it with a
sharper measurement and a named successor. It does **not** re-derive
`coal_offer_margin_level` inside this lane: arming is unchanged either way (the
displacement is inside the band), and a re-derivation is a solve-affecting change
to a committed measured parameter that needs its own precommit and its own A/B.
**If the hygiene item and the lever ever compete for this session's time, the
lever wins and the hygiene item is re-filed.**

---

## 11. What this session does NOT claim, and does NOT touch

* **No claim on C3a-2023.** Card Q ruling **Q-B is final** (ercot-191); item 11
  is CLOSED. C3a-2023 movement is reported at full magnitude and is not a gate,
  a target, or a promotion basis.
* **No C3b-2023-targeted round** (card R-A). The ~**0.59** ceiling is stated in
  §0.3 up front; movement is a reported side-effect.
* **No C3c ledger change, no rubric amendment.** The single ledgered CAVEAT ×3
  stands as written; its magnitudes are re-measured on each new run and carried.
* **No holdout marker granted or spent.**
* **No re-band of any tier.** `FASTSTART_POOL_MIN_DOWN_HOURS` stays 2.0;
  ercot-176's `[4, 8]` / `≤ 12 h` band stays exactly where that session fixed it,
  including its 17 deliberately-excluded CC plants.
* **No composition, ladder, boundary or artifact change. No P0 movement** — the
  pool is P1-only via `mc_bid_adjust` and the stamp is inert. **The ercot-188/E2
  P0 bit-identity forfeiture is INHERITED UNEXPIRED**: `ercot_econ_curve_top_refine`
  writes heat rates into the P0 objective on this keeper, so the offer-surface
  family's P0 bit-identity proof remains forfeited and any control-vs-arm
  difference here is confounded with commitment-side motion — isolable by
  argument, never by proof. Stated so no §3 seam proof is over-read.

**Next shorthand: ercot-197.**
