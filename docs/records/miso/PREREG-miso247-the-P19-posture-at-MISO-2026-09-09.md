# PREREG miso-247 — **MISO's keeper is stale against TWO repo-wide owner-ruled (P19) measured-input repairs, and one of them is UNGATED.** The G-DRIFT audit is re-run to my head and EXTENDED; every gate below is fixed before its number exists

**Keeper: `2026-09-08-miso-245-ladderfix`** (bundle `results/calibration/miso245_ladderfix_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered non-downgrading caveat, DOF **41/2**.
**Rule 22 `[R-HOLDOUT]`: 2023–2025 ONLY.** MISO holds no `complete` marker; **none is sought,
inferred or granted here**, and no out-of-training year will be solved, scored or registered.

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** —
`f923_gas_price_plausibility_screen` at MISO (`LIVE`, E1, `MEASURED` basis in
`_miso246_census_adjudication.json`; FINDING-miso246 §6 route (ii)).

---

## 0. STATED FIRST, AGAINST INTEREST — **miso-246's G-DRIFT audit was INCOMPLETE, and the gap is on the same solve path**

miso-246 §4 classified the `d059fcf7..HEAD` window by enumerating **declared default flips** and
**new `ScenarioConfig` fields**, and concluded that `f923_gas_price_plausibility_screen` was *"the
SINGLE declared default flip on the MISO backcast solve path"*. **That statement is true and it is
not the whole audit.** Owner ruling **P19** (2026-09-08) landed a **second** repo-wide change in the
same window which is **neither** a flip **nor** a field, so that enumeration could not see it:

> **`market_sim.data.fleet.eia860::_apply_simple_cycle_hr_floor`** (SPP-46 R-2) — clamps a
> simple-cycle-only plant's eGRID heat rate to `EGRID_CT_HR_PHYSICAL_FLOOR`. It is applied
> **unconditionally** at `eia860.py:1188`. It carries **no `ScenarioConfig` field**, so it cannot be
> pinned; **no cache-key entry**; `SOLVE_EPOCHS` is `()`; and `market_sim.data.fleet.eia860` is
> **not** in `solve_surface.SURFACE_MODULES`, so the capx-D79 fingerprint does not re-key for it
> either. `EGRID_CT_HR_PHYSICAL_FLOOR` and `F923_GAS_PRICE_PLAUSIBILITY_BAND` were both appended to
> `solve_surface_declared.DECLARED` **at their frozen registration hash**, which by that module's own
> design *"moves no key"*.

**This is disclosed as an extension of a predecessor's audit, not a criticism of it:** miso-246 was a
zero-LP census whose §4 was explicitly labelled **POST-HOC and not pre-registered**, and its stated
scope was flips and fields. **The consequence for this session is material and adverse to the easy
path:** the handoff's instruction — *"the keeper's committed bundle IS a valid rule 29(b) form-4
control ONLY with that field explicitly set to `False`"* — **is not sufficient on its own.** Pinning
`f923_gas_price_plausibility_screen=False` does not recover form 4 if the eGRID floor also moves a
MISO row, because there is no flag to pin it with. **§2 therefore MEASURES it rather than reading its
gate, and §2a fixes in advance what happens in each branch.**

**I have not measured any of it yet.** Every number in §2–§5 is computed only after this PREREG and
its probe are pushed.

## 1. THE OBJECT

Owner ruling **P19** (2026-09-08, repo-wide) landed two **rule 14 `[R-ACCURATE]`** construction
repairs to measured inputs, both **AFTER** the keeper's own solve commit `d059fcf7`, and **NEITHER
has ever been carried by a MISO solve of any kind**:

| | id | gate | posture at HEAD | in the keeper? |
|---|---|---|---|---|
| **A** | `f923_gas_price_plausibility_screen` | `ScenarioConfig`, frozen drop `"False"` | **default ON** (`203c031e`, 06:40Z) | **ABSENT** |
| **B** | `_apply_simple_cycle_hr_floor` | **NONE — ungated, unkeyed** | **always on** | **ABSENT** |

Both carry **ZERO free parameters**: A's band is the declared constant
`F923_GAS_PRICE_PLAUSIBILITY_BAND = (0.5, 2.0)`, fixed in `PRECOMMIT-spp-46` §3(E) before any number
existed and forbidden from being swept by rule 1 (c); B's floor is
`EGRID_CT_HR_PHYSICAL_FLOOR = HEAT_RATE_BINS["gas_ct"]["aero"]`, a physical bound from EIA Table 8.
Both reconcile a measured input to a **different measured input on the correct basis**, which is
rule 14's misalignment exception, and both regenerate for a forward year (rule 13's forward test).

**A is REACHABLE at MISO by construction:** the keeper records
`gas_plant_monthly_fuel_pricing=True`, `nearby_fuel_price_fallback=True`,
`class_aware_fuel_price_fallback=True`, so both the plant's own months and the class-aware donor pool
consume the screened frame.

**THE SESSION'S QUESTION IS NOT "SHOULD MISO ARM A LEVER".** Both repairs are already the program's
declared posture; **B cannot be declined at all** without editing owner-ruled code, and A is the
repo-wide default. The question is whether MISO's keeper, which is the only artifact still standing
on the pre-repair inputs, should be re-solved onto that posture. **No criterion, band or residual
appears in any bar below, in either direction.**

## 2. `G-DRIFT` — re-run from `d059fcf7` to MY head, and MEASURED where a gate cannot settle it

Scope is rule 29(b)'s enumerated path. Window at this PREREG: **26 files, +2,026/−44** (miso-246
audited 25 / +1,817/−36 — `origin/main` moved). **Verified before the audit:** `git fetch origin
main`; `git cat-file -t d059fcf7` → `commit`; `git merge-base --is-ancestor d059fcf7 origin/main` →
**true**.

Every hunk is classified **INERT with its reason cited** or **LIVE**. Where a hunk is a refactor with
a default branch, or a shared data seam, **it is MEASURED, not read** (handoff, binding):

* **`D-1` (MEASURED).** Rebuild the MISO fleet on the keeper's exact recipe via
  `run_calibration.run_year(fleet_only=True)` (kwargs from `replay_keeper.build_kwargs(meta)`) on
  both trees, for **each of 2023 / 2024 / 2025**. Report the number of generator rows whose
  `fleet_arrays.heat_rate` differs, the pmax MW they carry, and the per-class max delta.
  **B is INERT at MISO iff ZERO rows move in all three years.**
* **`D-2` (MEASURED).** The `data/fleet/floors.py` net-load-drag refactor. The keeper runs
  `ct_netload_drag=True`, so MISO **does** reach this path; `netload_drag_merit_allocation` and
  `netload_drag_layup_window_mask` are both `False`. **INERT iff the assembled per-unit `min_gen`
  array is bit-identical between the two trees in all three years.**
* **`D-3` (MEASURED).** The `model/lp/rows.py` hydro-family refactor. **INERT iff
  `hydro.hydro_budget_period_hours("MISO", …, config)` returns `None`** on the keeper recipe (no
  MISO entry in `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`, flag default-off) **and** the resulting hydro
  row block is bit-identical.
* **`D-4` (READ, git).** Every remaining changed file classified INERT with a cited reason from the
  rule 29(b) list — forecast-only path a `mode="backcast"` run never enters, another ISO's branch, a
  default-off field absent from the keeper's recipe, a per-ISO artifact MISO does not have, or pure
  timing/diagnostics accounting. **Any hunk I cannot place in one of those classes is LIVE.**
* **`D-5` (MEASURED, already computed as part of writing this PREREG and reported here at full
  magnitude).** `data/raw/_validation-source/actual_lmp.json` moved in the window. Per-ISO canonical
  hashes at `d059fcf7` vs HEAD: **only CAISO moved**; ERCOT, **MISO**, NEISO, NYISO, PJM and SPP are
  identical. **No MISO scored band is exposed.**

### 2a. **WHAT EACH BRANCH COSTS, FIXED HERE BEFORE `D-1` IS RUN**

> **If `D-1` returns ZERO moved rows in all three years** → B is INERT, only A is LIVE, A is
> pinnable, and **rule 29(b) form 4 holds: the keeper's committed bundle is the control with
> `f923_gas_price_plausibility_screen=False`. NO control solve is spent.**
>
> **If `D-1` returns ANY moved row** → B is LIVE and **unpinnable**, so form 4 does **not** hold at
> all and the handoff's pinning instruction does not recover it. A LIVE hunk is the one thing that
> earns a control solve (rule 29(b)), and it is spent **for the screen year ONLY**, as
> **`control` = HEAD with `f923_gas_price_plausibility_screen=False`**. That control is strictly
> stronger than form 4 and it **falsifies my own audit**: `control − keeper's committed bundle`
> isolates **B** (and any drift `D-4` misclassified), while `arm − control` isolates **A**. If `D-1`
> says B is INERT but a control is spent for another reason, that difference must be zero.

## 3. PHASE 0 — the mechanism's own footprint, ZERO LP

* **`P-1` THE FOOTPRINT STATISTIC (defined here, before it is computed).**
  > **`F(y)` = the total `pmax` MW of MISO fleet generator rows whose hour-mean assembled marginal
  > cost `mc_base` changes by more than `$0.01/MWh` between the keeper posture and the arm posture,
  > in solve year `y`.**

  `mc_base` is the `fleet_only` state dict's assembled P0 objective — *"the SAME offer prices the LP
  solved on"* — so this is the LP's own operand, capacity-weighted, and **not a residual, a band or a
  criterion**. Reported three ways so the two repairs are attributed separately: **`F_A`** (A alone),
  **`F_B`** (B alone), **`F_AB`** (joint).
* **`P-2` THE IDENTITIES the two mechanisms assert** — checked on the rebuilt arrays: every screened
  plant-month equals its state reference exactly; every in-band month is byte-identical to its
  pre-screen value; every clamped row satisfies `hr_after == max(hr_before, floor)`; and no
  non-gas row is touched by A, no non-simple-cycle row by B.
* **`P-3` THE PRE-SOLVE ENERGY PREDICTION.** Re-clear the screen year's assembled offer stack against
  the keeper's own committed hourly load, both postures, and report the per-class energy delta
  (TWh). **This is `G-1`'s predictor and it is fixed before the LP runs.**

## 4. **THE SCREEN-YEAR SELECTION RULE — declared BEFORE the statistic is computed**

> **Screen year = `argmax_y F_AB(y)` over `y ∈ {2023, 2024, 2025}`. Ties (equal MW) resolve to the
> EARLIEST year.** If `D-1` returns B INERT, the arm is A alone and the rule reads `argmax_y F_A(y)`
> — which is the same selection, since `F_AB ≡ F_A` when `F_B ≡ 0`.

This is the year the **mechanism's own measured footprint is largest**, per rule 29(a). **It is NOT
the residual year, and no residual, band or criterion enters the selection.** I have not computed
`F` for any year. **If this rule overrules the handoff's or my own expectation, the rule wins** and
the fact is reported.

## 5. THE SCREEN GATES — **STRUCTURAL, STOP-ONLY, and none is the target residual**

All four are evaluated on the **screen year only**. **They may kill the arm; they may not promote
it**, and none contributes to a determination.

* **`G-1` DIRECTION & MAGNITUDE.** For each class where `|P-3 prediction| ≥ 0.5 TWh`, the realised
  screen-year energy delta must (i) carry the **same sign** as the prediction and (ii) fall within
  **[1/3, 3]×** its magnitude. *Bar rationale, fixed here: SPP-49 measured its own naive
  own-rows-only predictor at CT +13/+12/+9 TWh against a realised +3.6/+2.5/+1.0 — a ~3.6× miss —
  and named the pooled re-clearing path as the accurate one. `P-3` IS the pooled predictor, so a
  band of 3× is the honest tolerance for it and is set before any realised number exists.*
* **`G-2` FOOTPRINT CONFINEMENT.** Classes with no fuel-price and no heat-rate exposure (WIND, SOLAR,
  NUCLEAR, HYDRO, STORAGE) must have **bit-identical available-capacity arrays** between arm and
  control; their energy may move only through re-clearing. Any change to an input array outside the
  rows `P-1` named **FAILS**.
* **`G-3` IDENTITY.** `P-2`'s identities hold in the **solved** year's assembled arrays, not only in
  the offline rebuild.
* **`G-4` COLLATERAL.** `scripts/screen_collateral_gate.py --bundle <screen>
  --keeper-run-id 2026-09-08-miso-245-ladderfix --years <screen year>`: **no non-target load-bearing
  criterion (C1 / C2 / C3a / C3b / C6 / C8) may flip PASS → FAIL.** C3c is the designated frontier,
  is ledgered and non-downgrading, and **is not a target in either direction here.**

**Explicitly NOT a gate, in either direction: C3a, C3b, C3c, C1, C2, the price tail, the MAE, or any
band.** A gate reading *"did the residual improve"* is the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, and none is written.

## 6. IF THE SCREEN CLEARS

One invocation, one bundle, **`--year 2023 2024 2025`** (rule 16 `[R-ALLYEARS]`), on the arm posture.
`replay_keeper.py` writes neither `calibration_attestation.json` nor `metrics.json`, so the keeper's
attestation is carried forward with `governance.attested_by` and `disclosures` rewritten, or C6 reads
`UNATTESTED`. Registered under rule 15 `[R-DASHBOARD]` whatever the outcome; the MISO shard cell
updated in-session under rule 28(b). **Promotion is the OWNER's decision, not mine** (rule 31
`[R-RETAIN]`): **no solved bundle is deleted in this session**, and the promotion question is
surfaced explicitly in the final report.

## 7. NON-CLAIMS, fixed in advance

1. **No marker is sought, inferred or granted.** MISO's 2022 touchpoint is not solved, scored or
   registered, and the `complete` decision stays the owner's.
2. **No free parameter is created.** DOF stays **41/2** unless a gate says otherwise, and neither A
   nor B is a fitted value.
3. **C3c is untouched.** It stays the designated frontier and opens only by a new admissible measured
   identification plus an owner ruling. None is proposed here.
4. **MISO has no failing gate and this session does not invent one.**
5. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage**; no 2025 C1 pass will be read as
   evidence.
6. **If one of my own gates fails, it is published FIRST at full magnitude**, its pre-repair values
   fixed on the record, and **no bar is moved**. A gate that was satisfiable and simply failed is a
   **result**, not a broken gate.
