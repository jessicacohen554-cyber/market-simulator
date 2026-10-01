# PRECOMMIT — ercot-186: the RULE-18 GRAIN DEFECT (card D3, option (ii))

**Pre-registered and pushed BEFORE any measurement, any seam proof and any
solve.** The construction, the eligibility read, the seam proofs, the kill
gates, the honest-outcome clause and the retention evictions are fixed here and
are **not renegotiated after measurement**.

Keeper at session start, verified at this session's HEAD `fe9fa97f`:
**`2026-08-09-ercot185-shaped-partial`**, bundle
`results/calibration/ercot185_shapedarm_B` — determination **NOT-YET**,
fail set **{C3a-2023, C3b-2023}**.

> *Bundle-name correction, recorded because the handoff carried it.* The task
> prompt names the keeper bundle `results/calibration/ercot185_shaped_partial_B`.
> No such directory exists. The registry sidecar
> `frontend/data/backcast/registry/2026-08-09-ercot185-shaped-partial.json`
> resolves the keeper to **`results/calibration/ercot185_shapedarm_B`**, and its
> control to `results/calibration/ercot185_shapedcontrol_A`. Those are the
> bundles this session replays.

---

## 0. Authorization and scope

**Signed authorization** — owner sitting 2026-08-09, decision card **D3**,
option **(ii)**, *"authorized, sequenced after D2"*
(`docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §4(b2) + §10).
**D2 has landed** — `2026-08-09-ercot185-shaped-partial` is the keeper — so the
sequencing precondition is met.

The card's own statement of the object (§4(b2)):

> *"Fleet assembly records unit physics on the **committed tranche only**, so
> every `econ*`/`peak*` bid row reads `min_down = min_run = 0`. A rule-18
> `[R-PHYSICS]` gate is therefore **vacuous at tranche-row grain**, and the
> armed keeper mechanism `ercot_faststart_pool_offer` consequently admits every
> CT bid row regardless of physics — its effective scope is the `CT_PEAKER`
> class map, not the intended min-down test. … **Fixing it moves the keeper**
> and needs its own pre-registered round. It is a *legitimacy* item, not a
> residual item: an armed mechanism whose licensing gate does not bind is a
> rule-18 defect independent of whether fixing it improves any metric."*

**Scope fences (binding):**

* **ERCOT only** (rule 25 `[R-ISO-SCOPE]`). No other ISO's cell, keeper,
  artifact or matrix column is read or written. The one non-ERCOT site that
  shares this grain defect — `model/commitment.py::_ra_bridge_unit_params`, the
  CAISO RA bridge, which already carries its own class-table workaround for the
  zero-physics case — is **named and left untouched**.
* **`--year 2023 2024 2025` only, ONE invocation per bundle, years sequential**
  (rules 12/16/22). ERCOT holds **no** `complete` and **no** `final` marker, so
  2019–2022 and H1-2026 stay quarantined: unsolved, unscored, unread.
* **No band is re-chosen.** `constants.FASTSTART_POOL_MIN_DOWN_HOURS = 2.0`
  is untouched, and **no min-run bound is added** to this tier (it has never had
  one; adding one would be a new parameter, not a grain correction).
* **No composition change.** `own_mask` replace-by-mask, the ladder, the
  boundary, the VOLL cap and the P1-only seam are all untouched.
* **No offer-side C3a-2023 lever.** This session's object is the licensing gate,
  not the 2023 residual (that is the D1(c)/D5 lane).

**DO-NOT-REDO check, performed BEFORE pre-registration** (rule 28 duty (a)).
The ERCOT column of `docs/codebase-site/data/mechanism-matrix.js` carries
`ercot_faststart_pool_offer` at **`K`** with the ercot-176 annotation naming
exactly this defect and recording it as *"REPORTED NOT ACTED ON … NOT fixed
here"*. No cell in this family is adjudicated `R`/`I`/`G` against a
physics-grain correction, so nothing is being re-tested. The lever comes off the
ERCOT queue as the card's own D3 item.

---

## 1. THE DEFECT, at code grain

`src/market_sim/data/fleet/assembly.py` builds each plant's tranche ladder as
`(suffix, cap, hr, vom_mult, min_run, min_down, startup)` tuples and stamps
`min_run`/`min_down` **only on the committed anchor slice**
(`assembly.py:1140-1141` reading the `bin_min_run`/`bin_min_down` computed at
`assembly.py:808-814`). Every `mustrun`, `sync`, `econ*` and `peak*` row is
constructed with the literal `0, 0`. The deliberate reason is recorded in
assembly's own comment on the fast-start tranche pricing block: *"Min-run /
min-down stay 0 (bid markup only, no new UC coupling)"* — the bid tranches must
not acquire commitment coupling.

The consequence is a **grain mismatch, not a physics error**: the physics is
recorded correctly, one grain coarser (the plant) than the rows a bid-row gate
reads. So `build_ercot_faststart_pool_markup`'s rule-18 gate,

```python
# offer_surfaces.py:2839-2843 (stepped body) and :3017-3021 (contpct body)
if float(getattr(gen, "min_down_hours", 0) or 0) > FASTSTART_POOL_MIN_DOWN_HOURS:
    continue
```

evaluates `0 > 2.0` on **every** row it can ever reach — because the same
builder immediately restricts itself to `econ*`/`peak*` suffixes, which are
precisely the rows carrying `0`. The test is **False for every row, always**.
Its effective scope is therefore the row universe alone,
`{grp for grp, key in _ERCOT_CLEARED_SHARE_CLASS_OF.items() if key == "CT"}`
= `{"CT_PEAKER"}` — **a hard-coded class tuple, which is what rule 18
`[R-PHYSICS]` forbids**.

Enumerated at ercot-176 (`PRECOMMIT-ercot176` Amendment 2, `FINDING-ercot176`
§5) and carried un-acted through ercot-178 / 180 / 181 / 185.

**This is a loss of protection.** The gate is not testing anything, in either
direction: at tranche-row grain `min_down <= 2` admits every bid row and
`4 <= min_down <= 8` (the sibling tier's band) rejects every bid row.

---

## 2. THE CONSTRUCTION — fixed here, in two parts

### 2a. Part 1 — the source-side grain repair (`assembly.py`, `fleet/__init__.py`)

Every tranche row of a plant carries **the plant's own assembled unit physics**
on two NEW `Generator` fields:

```python
plant_min_run_hours: int = 0    # the PLANT's min-run, on EVERY tranche row
plant_min_down_hours: int = 0   # the PLANT's min-down, on EVERY tranche row
```

stamped by `assembly.py` with the **exact values it already computes**,
`bin_min_run` / `bin_min_down` — no new source, no new resolution, no new
constant. The existing `min_run_hours` / `min_down_hours` fields are
**UNTOUCHED**: they remain the UC-coupling anchor tags that
`model/commitment.py` and the startup-amortization path read, and the bid rows
keep their deliberate `0`.

**The stamp changes no solve by construction.** It writes two fields that no
existing consumer reads; `FleetArrays` gains no column; the LP sees nothing new.
Its entire purpose is to make the physics **readable at bid-row grain** so a
rule-18 gate can be non-vacuous.

### 2b. Part 2 — the licensing gate moves to plant grain (`offer_surfaces.py`)

In **both** fast-start pool bodies — the stepped
`build_ercot_faststart_pool_markup` and the ercot-178/180 refined-grain
`_faststart_pool_markup_contpct` — the per-row test above is **deleted**
(rule 26 `[R-DELETE]`: removed, not zeroed) and replaced by a per-plant test
evaluated once per plant prefix, before its rows are walked:

```
md(prefix) = max over the prefix's rows of ( plant_min_down_hours , min_down_hours )
skip the whole plant iff  md(prefix) > FASTSTART_POOL_MIN_DOWN_HOURS
```

This is the **ercot-176 Amendment-2 construction applied to the fast-start
pool's rows**, as the card directs. The `max` over both fields is the fixed
read: under CAMPD per-plant binning the two terms coincide (the stamp writes the
same `bin_min_down` the committed anchor already carries), and the `max` keeps
the read correct — and never *more* permissive than the row read — on any fleet
path that does not stamp (legacy heat-rate bins).

### 2c. What is NOT introduced, and why

* **No class-table fallback ladder.** A plant whose assembled physics is `0`
  reads `md = 0` and is **admitted**. That is stated ex ante and is not a
  loophole for *this* gate: the published class table this tier's own constant
  cites (`CT_COMMITMENT_PARAMS`, uniformly `min_down_hours = 1` at every heat
  rate) would license identically under an **upper-bound** test at 2 h. A tier
  with a LOWER bound — ercot-176's `4 <= md <= 8` — would need the ladder; that
  tier already reads measured values and is not touched here. Adding a fallback
  no gate outcome depends on would be a second mechanism for one phenomenon
  (rule 19 `[R-ONE-MECH]`).
  **The residual weakness is disclosed, not hidden:** the corrected gate still
  cannot distinguish "measured 0" from "unmeasured". Under a 2 h upper bound
  against a class whose published physics is 1 h, both readings license
  identically, so the distinction is not load-bearing at this bound — and any
  future re-banding of this tier must revisit it.
* **No new fitted scalar of any kind** (G-DOF, §5).
* **No change to the row universe.** `CT_PEAKER` remains the *measured class
  scope* of the pool ladder — which is a measurement provenance statement, not
  an eligibility test. After this change the class scope and the physics gate
  are two distinct filters, which is exactly the state rule 18 requires; before
  it, the class scope was silently doing both jobs.

### 2d. The arming flag

ONE registered `ScenarioConfig` field (rule 24 `[R-REGISTRY]`):

```python
ercot_faststart_pool_plant_physics: bool = False
```

Default **off** so the control replays the keeper byte-faithfully; armed in the
arm; **armed in the keeper if the arm is promoted**. Registered in
`_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (dropped at
its default, so the pinned default key `603c2498bf71d21d` does not move) and in
`TIER_TAGS`, in the same commit as the field. Its mechanism-matrix row lands in
the same PR (rule 28 duty (c)).

The **source-side stamp of §2a is NOT flag-gated** — it is inert by
construction, and gating an inert stamp would put a second switch on one
phenomenon. The control/arm delta is therefore exactly one boolean.

---

## 3. SEAM PROOFS — fixed here, run before any solve

Written to `results/calibration/ercot186_grain_seamproof.json`, all three years,
on the real keeper fleet.

* **SP-1 (equivalence to the ercot-176 read).** For every plant prefix in the
  fleet, `plant_min_down_hours` (constant across the plant's rows) equals
  `max over the plant's rows of min_down_hours`; likewise for min-run.
  *This is the proof that §2a is a pure grain restatement of what assembly
  already recorded, and that §2b reproduces ercot-176 Amendment 2 exactly.*
  **Falsifier: any prefix where they differ.**
* **SP-2 (the defect is real).** With the flag OFF, the number of CT bid rows
  the row-grain gate REJECTS is **0** in every year — i.e. the gate as shipped
  is vacuous, as claimed. **Falsifier: any rejection, which would mean the
  defect was mis-stated and this session stops and re-reports.**
* **SP-3 (the corrected gate's scope, MEASURED and reported at full
  magnitude).** With the flag ON: the number of CT_PEAKER plants in the row
  universe, how many clear `md <= 2`, how many are excluded, the excluded
  plants' `md` values, and the bid-row counts on each side — per year.
  **No bound moves in response to this number** (§2, and the ercot-176
  precedent, where 17 CC plants were excluded by a pre-registered bound that was
  deliberately NOT widened after the fact).
* **SP-4 (inertness determination).** Whether the arm's `(markup, own_mask)`
  pair is array-equal to the control's, per year. This is what decides §6's
  branch, and it is a *measurement*, not a prediction.
* **SP-5 (no other consumer moved).** `FleetArrays` built from the same fleet is
  array-equal with and without the §2a stamp, field by field.
  **Falsifier: any array differs — the stamp would then not be inert and the
  session stops.**

**Any SP falsifier fires ⇒ stop, report, register nothing.**

---

## 4. PREDICTIONS — falsifiable, fixed before measurement

* **P-1.** SP-2 holds: the shipped gate rejects zero rows in all three years.
  *Falsifier: any rejection.*
* **P-2 (the honest prior, on the record since ercot-176).** The matrix note
  states *"It is not currently believed to change WHICH rows are priced (CT
  physics is uniform at min-down 1 h), so this is a loss of PROTECTION, not a
  known mis-scoping."* This session therefore predicts **the corrected gate
  admits every CT_PEAKER plant and the arm is INERT** (SP-4 array-equal).
  *Falsifier: any plant excluded.* **If P-2 is falsified the exclusion stands** —
  the bound is not widened to recapture the excluded plants, and the measured
  price/dispatch consequence is reported at full magnitude whichever way it
  moves.
* **P-3.** No gate in §5 fails. *Falsifier: any live gate fails, which is
  reported as REJECTED-AS-ARMED at full magnitude before §6's promotion question
  is reached.*

---

## 5. KILL GATES — verbatim, all live unless marked

Baselines are the keeper `2026-08-09-ercot185-shaped-partial`, read off its
committed artifacts this session (`calibration_verdict.py --run-id`, and
`ercot185_ab.json` for shed/spurious):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a | **FAIL −32.5 %** | PASS +1.4 % | PASS −7.9 % |
| C3b | **FAIL 0.602** | PASS 0.160 | PASS 0.101 |
| model tail >$200 (actual) | 61 (181) | 23 (53) | 3 (31) |
| shed hours | 4 | 2 | 0 |
| spurious mid-band | 10 | 11 | 1 |

* **G-SHED — PRIMARY.** Shed-hour counts **4 / 2 / 0** must not RISE in any
  year. *(The ercot-48/49 manufactured-shortage signature; this gate has killed
  price-formation arms in this ISO twice.)*
* **G-C3c.** The ledgered tail counts **61/181, 23/53, 3/31** must not degrade
  (the model count must not move AWAY from the actual count) in any year.
* **G-COAL148.** Coal dispatch above the measured product ceiling may not rise
  more than **+0.5 TWh in any year**. *Carried live per the D2 ruling. Screened
  by construction here: this session changes no availability, no ceiling and no
  coal row — the pool leg touches merchant CT bid rows only — so the gate is
  scored from the pair's class energies and any non-zero coal move is a
  falsifier of that claim, not an accepted cost.*
* **G-OWNER.** **C3a-2024 and C3a-2025 keep PASS**, and **C3b-2024 stays
  ≤ 0.20** — the criterion-year ercot-185 just won, protected explicitly.
* **G-SPAN.** In every year: no class's annual energy moves more than **0.5 %**.
  *(G-BIT is declared **N/A pre-solve**, with the reason recorded here: the
  correction is year-agnostic — it applies to every year's fleet identically —
  so the year-specific-rule gate has no object, and G-SPAN replaces it. Same
  disposition and same reason as PRECOMMIT-ercot185 §6.)*
* **G-SPUR.** The spurious mid-band count (**10 / 11 / 1**) must not increase in
  any year.
* **G-DOF.** **Zero** new fitted scalars. Satisfied by construction: the field
  is a boolean, the bound is the existing constant, the stamped values are
  assembly's own.
* **G-D2.** The pool's D-2 attribution and D-4 window both stay clean: the
  mechanism sets no `min_gen`, so it has no forced-energy or off-window-binding
  exposure by construction; the gate is scored as **D-4 FAIL rows identical
  A↔B** (the pre-existing CT_PEAKER condition carried by the keeper), and any
  new row is a failure.
* **Rule 22 LOYO** — leave-one-year-out within 2023–2025 before any promotion.

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such at full
magnitude. The gates are not renegotiated after the solve.**

---

## 6. THE HONEST OUTCOME, PRE-REGISTERED

Three branches, all fixed now.

**(i) The arm is INERT (SP-4 array-equal, P-2 holds).** Then the correction is a
pure legitimacy repair: identical prices, identical dispatch, a gate that now
actually tests something. **Both runs are still registered, all three years**
(rules 15/16, and the task's explicit instruction) — and **both registrations
state plainly that the two bundles are numerically identical**, so the dashboard
is never read as two independent results. The ercot-176 Amendment-3 disposition
(*"registering a bit-identical duplicate would put the same numbers on the
dashboard twice"*) is **deliberately NOT followed here, and the difference is
stated**: at ercot-176 the arm was a *candidate mechanism* that would have added
nothing; here the arm is the **corrected form of a mechanism already armed in
the keeper**, so the keeper itself must move onto it — a keeper carrying an
armed mechanism whose licensing gate is vacuous is the rule-18 defect, whatever
the numbers say. **Promotion in this branch is on legitimacy alone, and the
FINDING will say exactly that** — no metric gain is claimed and none exists.

**(ii) The arm MOVES the numbers and every live gate passes.** Promote, with the
per-year deltas reported in full, and LOYO cleared first.

**(iii) The arm MOVES the numbers and a live gate FAILS — including if the fit
gets WORSE.** Per rule 1 `[R-STRUCT]` the correct physics **stays in**: a
vacuous gate is not restored because the residual moved the wrong way, and the
resulting residual becomes a named root-cause item, not grounds to revert. The
mechanical verdict is recorded **REJECTED-AS-ARMED and is not rewritten.**
Whether the run is nonetheless promoted is then the owner's standing structural
standard — the same standard ercot-185 was promoted under, over a
REJECTED-AS-ARMED verdict on 2 of 9 gates. **If that standard is what carries
this arm, this session says so explicitly**, records the mechanical verdict
unrewritten alongside the promotion, and does not present the promotion as a
gate pass. If the failure is G-SHED (the primary), the escalation is stated
rather than papered over: the honest alternatives are (a) promote under the
structural standard with the shed regression disclosed, or (b) **disarm
`ercot_faststart_pool_offer` entirely** — because a mechanism that can only pass
its gates while its licensing test is vacuous has not earned its keeper slot.
This session will not choose (b) unilaterally; it escalates it to the owner with
the measurement attached.

---

## 7. DECISION RULE

1. **SP-1 … SP-5 all PASS** — else stop, report, register nothing.
2. **A/B pair** via `scripts/replay_keeper.py` on `ercot185_shapedarm_B`,
   control and arm **STRICTLY SEQUENTIAL** (~6.6 GB RSS, ~20 min/year each; two
   concurrent ERCOT per-plant solves OOM a 15 GB box):
   * control `results/calibration/ercot186_graincontrol_A` — zero delta,
     the same-HEAD reproduction that separates HEAD drift from the mechanism;
   * arm `results/calibration/ercot186_plantphysics_B` —
     `--set ercot_faststart_pool_plant_physics=true`, the single delta.
3. **Legitimacy diagnostics + attestation, then scoring**, both runs.
4. **Both runs registered** on the dashboard whatever the outcome.
5. **Every live gate passes AND LOYO clears ⇒ promotion candidate**; otherwise
   §6(iii).

---

## 8. Governance, bookkeeping, retention

* **Rule 15 `[R-DASHBOARD]`** — both runs registered + committed + pushed in
  **this** session; the FINDING and the dashboard carry the result, not chat.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, ONE invocation, ONE bundle
  each. No single-year keeper.
* **Rule 22 `[R-HOLDOUT]`** — ERCOT holds no marker; `--year` never leaves
  {2023, 2024, 2025}; no out-of-training year is solved, scored, read or
  registered.
* **Rule 23 `[R-FROZEN-DERIVE]`** — **no derive is re-run and no artifact is
  re-derived.** The pool artifact, its ladder and its `pool_frac` are frozen and
  untouched; this session changes only which rows are licensed to read them.
* **Rule 24 `[R-REGISTRY]`** — one registered `ScenarioConfig` field,
  cache-key-registered dropped-at-default, recorded in both bundles'
  `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-gated throughout; the CAISO RA bridge's
  sibling defect is named, not touched.
* **Rule 26 `[R-DELETE]`** — the vacuous per-row test is **deleted**, not
  zeroed or left behind a dead branch.
* **Rule 27 `[R-PUSH]`** — `assembly.py` (1,717 lines), `offer_surfaces.py`
  (3,731), `fleet/__init__.py` (637) and `scenarios.py` are all ≥300-line core
  files: every edit is made LOCALLY with the Edit tool, the exact on-disk bytes
  are pushed, and every push is blob-verified against the **REMOTE** before the
  next commit.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (a) the DO-NOT-REDO check preceded this
  document (§0); duty (b) the `ercot_faststart_pool_offer` cell verdict +
  citation is stamped in **this** session; duty (c) the new field's row lands in
  the same PR as the field; duty (d) no cross-ISO verdict is minted.
* **Retention (top-15 per ISO).** ERCOT stands at **15** registered runs.
  Registering this pair evicts the **two oldest, neither protected and neither a
  keeper**: **`2026-08-04-run162a-storage-rt`** and
  **`2026-08-04-run162b-storage-rt`**. Named here, before the fact.

---

## 9. What this session does NOT claim, and does NOT touch

* **No claim on C3a-2023 or C3b-2023.** ERCOT's fail set is expected to stay
  **{C3a-2023, C3b-2023}** and the determination **NOT-YET**. This is a
  legitimacy repair, not a residual lever, and no reachability claim is made.
* **No re-band of any tier.** `FASTSTART_POOL_MIN_DOWN_HOURS` stays 2.0;
  ercot-176's `[4, 8]` / `<= 12 h` band stays exactly where that session fixed
  it, including the 17 CC plants it deliberately excluded.
* **No composition, ladder, boundary or artifact change.**
* **No P0 movement.** The pool is P1-only via `mc_bid_adjust`; the stamp is
  inert; commitment is untouched.
* **DO-NOT-REDO honoured in full** — no offer-side C3a-2023 lever, no coal lane,
  no depth lever, no storage offer surface, the West/Panhandle topology stays
  closed, ERCOT-148/149 stays armed and un-repealed, and the D5 cliff-resolving
  costing memo is a separate lane not touched here.

**Next shorthand: ercot-186.**
