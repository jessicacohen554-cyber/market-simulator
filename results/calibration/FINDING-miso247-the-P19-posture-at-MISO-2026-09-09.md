# FINDING miso-247 — **MISO's keeper was the last artifact in the program still standing on inputs owner ruling P19 had already replaced, and ONE OF THE TWO REPAIRS IS UNGATED so MISO could never have declined it.** Promoted. **My own rule-29 screen gate `G-1` FAILED and is published first, unrepaired, with no bar moved**

**KEEPER → `2026-09-09-miso-247-p19-posture`** (bundle `results/calibration/miso247_fullspan_K`),
full span **2023–2025 in ONE invocation and ONE bundle** (rule 16 `[R-ALLYEARS]`).
**DETERMINATION CALIBRATED**, C3c the single ledgered non-downgrading caveat, grade summary
**scored 8 / target 7 / ledgered 1 / fails 0**, **DOF 41/2** — every one **identical** to the
`2026-09-08-miso-245-ladderfix` predecessor, **C3c's hour counts included** (model 3/7/11 h > \$200
against a measured 30/37/88).

**Rule 22 `[R-HOLDOUT]`: 2023–2025 ONLY.** MISO holds no `complete` marker; **none was sought,
inferred or granted**, and no out-of-training year was solved, scored or registered. **C3c is
untouched** and was a target in neither direction.

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** —
`f923_gas_price_plausibility_screen` at MISO. **Records, each pushed BEFORE the numbers it
governs:** `PREREG-miso247-the-P19-posture-at-MISO-2026-09-09.md` and four ADDENDA
(the probe repair; `D-1` + the predictor repair; the `CT_PEAKER` scope disclosure; the `G-1`
failure). Machine records `_miso247_p19_posture_phase0.json`, `_miso247_p3prime_reclear.json`,
`_miso247_screen_gates.json`, `_miso247_g4_collateral.json`.

---

## 0. STATED FIRST, AGAINST INTEREST

### 0a. **MY OWN SCREEN GATE `G-1` FAILED, AND IT IS NOT REPAIRED**

| class | `P-3′` pred | realised (arm − keeper) | **ratio** | scope | `G-1` |
|---|---:|---:|---:|---|---|
| **ST_GAS** | +0.5964 | **+1.9554** | **3.279** | in | **FAIL** |
| COAL | −0.8474 | −1.7200 | 2.030 | in | PASS |
| CC_REGULAR | −0.6602 | −0.7527 | 1.140 | in | PASS |
| CC_CHP | +0.7082 | +0.3651 | 0.515 | in | PASS |
| *CT_PEAKER* | *+0.2849* | *+1.3440* | ***4.717*** | *out* | *—* |
| *import* | *−0.2094* | *−1.3128* | ***6.269*** | *out* | *—* |

**`ST_GAS` misses by 0.279 on a `[1/3, 3]` band I fixed myself**, before either predictor existed,
justified on SPP-49's own ~3.6× predictor miss. **THE GATE WAS SATISFIABLE** — three of four in-scope
classes clear it — **so it is a RESULT, not a broken gate. No bar was moved and no repair was made.**
Re-scoping to the passing classes, widening to 3.3×, dropping `ST_GAS`, or reverting to the
pre-repair predictor would each convert the failure into a pass **by construction**; each is named
and refused in ADDENDUM 4. **The full span was spent on the OWNER's explicit instruction and on
rules 1/14 — NOT on the screen's authority**, and that is §5.

### 0b. **MY OWN PREDICTOR REPAIR MOVED `CT_PEAKER` — THE CLASS THE HANDOFF NAMES FIRST — OUT OF THE GATE THAT COULD HAVE KILLED THE ARM**

Disclosed in ADDENDUM 3 **before any realised number existed**, with the `R-ALL` reporting duty
attached; honoured above: **`CT_PEAKER` WOULD ALSO HAVE FAILED (4.717), and so would `import`
(6.269).** A reader is entitled to suspect the repair; the answer is that it was declared on a defect
identified from the predictor's own construction (it served **117.7 TWh** of wind + solar from the
thermal stack, mechanically exaggerating top-of-stack classes) before `P-3′` was computed. **Every
in-scope miss is in the SAME direction — the LP responds MORE than the predictor, on every class.
That explains the failure; it does not excuse it, and it moved no bar.**

### 0c. **A PREDECESSOR'S AUDIT WAS INCOMPLETE — disclosed as an extension, not a criticism**

miso-246 §4 concluded `f923_gas_price_plausibility_screen` was *"the SINGLE declared default flip on
the MISO backcast solve path"*. **True, and not the whole audit**: its enumeration was flips and
`ScenarioConfig` fields, and the second P19 object is **neither**. The adverse consequence landed on
this session, not on it: the handoff's instruction that pinning the screen to `False` restores rule
29(b) form 4 is **measured FALSE**.

### 0d. **MY FIRST PROBE USED THE RECONSTRUCTION `replay_keeper` EXPLICITLY FORBIDS**

`build_kwargs` splatted into `run_year` — the caiso-243 lookalike-recipe defect. It **crashed** rather
than silently measuring a different recipe, which was **luck, not design** (ADDENDUM 1). Repaired to
`run_year_kwargs` + `derived_run_year_inputs` with two **added** checks.

## 1. THE OBJECT — and why it is not an ordinary lever

Owner ruling **P19** (2026-09-08, repo-wide) landed two **rule 14 `[R-ACCURATE]`** construction
repairs, both **after** the predecessor's own solve commit `d059fcf7`, **neither ever carried by a
MISO solve**:

| | id | gate | at HEAD | in the predecessor? |
|---|---|---|---|---|
| **A** | `f923_gas_price_plausibility_screen` | `ScenarioConfig`, frozen drop `"False"` | **default ON** | **ABSENT** |
| **B** | `eia860.py::_apply_simple_cycle_hr_floor` | **NONE — ungated, unkeyed** | **always on** | **ABSENT** |

**A**: an own-reported EIA-923 Natural Gas plant-month outside `[0.5, 2.0] ×` its **own state's**
measured EIA delivered-to-electric-power price falls back to that reference, and the nearby-plant
donor pool is rebuilt from screened months. **B**: a simple-cycle-only (GT/IC) plant's eGRID heat
rate is clamped to `EGRID_CT_HR_PHYSICAL_FLOOR = HEAT_RATE_BINS["gas_ct"]["aero"]`.

**Both bands are DECLARED constants, fixed before any number existed and forbidden from being swept.
ZERO free parameters: DOF 41/2 unchanged.** The basis is rule 14 and **never** the residual — an
average cost carrying a fixed transport charge over a near-zero burn denominator is on a different
basis than the marginal fuel cost the LP prices, and a plant of bare turbines cannot beat the best
bare turbine.

> **B CANNOT BE DECLINED.** It carries **no `ScenarioConfig` field, no cache-key entry**,
> `SOLVE_EPOCHS` is `()`, and `data.fleet.eia860` is absent from `SURFACE_MODULES` — so the capx-D79
> fingerprint does not re-key for it either. **Every future MISO solve carries it**, and leaving the
> keeper on the pre-repair inputs would have left MISO's designated keeper **unreproducible at
> HEAD**. That is the structural reason this promotion is not optional in the way a lever is.

## 2. `G-DRIFT`, RE-RUN AND EXTENDED — the finding that reshaped the session

* **`D-1` MEASURED, not read: `B` is LIVE at MISO — 55 rows / 624.8 MW in ALL THREE years.**
  `hr_after` takes exactly **`{9.0, 9.9, 39.6}`** (the floor on legacy-bin rows; the floor through
  the CAMPD tranche multipliers on per-plant rows) and `min_signed_dhr = 0.0` — **the clamp never
  lowers a rate**, so `P-2`'s identity `max(hr, floor)` holds exactly. Eight legacy plants plus 33
  `CT_PEAKER` tranche rows.
* **⇒ RULE 29(b) FORM 4 IS FALSIFIED**, and pinning `A` does not recover it. **A control solve was
  EARNED** and spent on the screen year alone, exactly as PREREG §2a fixed in advance.
* **`D-2` / `D-3` INERT, measured:** the `floors.py` net-load-drag refactor leaves the assembled
  per-unit `min_gen` **bit-identical** in all three years on a keeper that **does** run
  `ct_netload_drag=True`; `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` carries **only NYISO**.
* **`D-4` INERT, every remaining hunk with a cited reason** — `interchange/*` is PJM's own
  neighbour-anchored registry under a default-off flag and **`MISO_SEAM_LADDER_BY_YEAR` has ZERO
  diff lines in the whole window**; `capacity_evolution/*` is forecast-only; `results/cache.py` is
  **prose only**; the capx-D88 duplicate-`unit_id` guard only `raise`s and MISO's fleet built
  **twelve times** here without raising.
* **`D-5` MEASURED:** of `actual_lmp.json`'s seven per-ISO blocks, **only CAISO moved**.

## 3. THE ATTRIBUTION THE CONTROL BOUGHT — and it falsifies nothing

| class | **A** = arm − control | **B** = control − keeper |
|---|---:|---:|
| ST_GAS | **+1.9155** | +0.0399 |
| COAL | **−1.7948** | +0.0748 |
| CT_PEAKER | **+1.6171** | **−0.2732** |
| import | **−1.3788** | +0.0660 |
| CC_REGULAR | **−0.8167** | +0.0640 |

**A carries essentially the whole response; B is small and correctly signed** — the floor makes
624.8 MW of small simple-cycle plant dearer, `CT_PEAKER` falls 0.2732 TWh, everything else moves
under 0.08 TWh as re-clearing. **No class moved in `control − keeper` that `D-1` had not predicted,
so `D-4` is not falsified.** Had the audit missed a hunk, this is the column where it would show.

## 4. THE BANDS, AT FULL MAGNITUDE AND NOT NETTED — **zero flips, 14 toward, 9 away**

**TOWARD:** `CT_PEAKER` fuelmix 2023 **−3.056 → −0.687** and 2024 −1.83 → −0.482; `ST_GAS` 2024
**−5.038 → −3.167**, 2023 +0.401 → +0.171; `CC_REGULAR` 2023 −6.46 → −6.306, 2024 +3.87 → +3.149;
`CC_CHP` both years; `ST_CHP` 2024; system **gas** volume 2023 −13.83 → −11.55 and 2024 −6.47 →
−3.52; **mean price 2023 2.11 → 1.69 and 2024 1.19 → 0.54**.

**AWAY — and this is the honest cost: EVERY scored coal band regresses.** `COAL_PRB` 2023 −1.781 →
−2.619 and 2024 −3.36 → −4.59; `COAL_BIT` 2023 −2.953 → −3.356 and 2024 −3.532 → −3.988;
`COAL_LIGNITE` both years; system **coal** volume 2023 −5.26 → −6.54 and 2024 −7.55 → −9.27; plus
`ST_CHP` 2023 (−2.718 → −2.741) and **mean price 2025 −2.4 → −2.86**.

> **THE COAL REGRESSION IS A DISCOVERED SIGNAL, ROUTED AND NOT ABSORBED.** The model was short on
> **both** gas and coal. Pricing gas correctly moved gas toward its actual and displaced coal
> **further below** its own — which is rule 14's *"treat the worse fit as a discovered bug"*
> exactly. **MISO's coal deficit is a SEPARATE, unaddressed object** and is the successor's named
> first candidate. **Nothing was tuned to close it, and no offer, adder or multiplier was touched.**

## 5. WHY THIS IS A KEEPER — the authority named, and it is not the screen's

1. **Rules 1 `[R-STRUCT]` + 14 `[R-ACCURATE]`.** Two zero-DOF measured-input repairs replacing
   demonstrably wrong inputs. Rule 14 says keep the accurate input **even if the fit gets worse**;
   rule 1 says a structurally-correct mechanism is **never** judged by the residual.
2. **`B` is ungated** (§1) — the pre-repair posture was not available to keep.
3. **Nothing scored degraded in status:** zero PASS→FAIL flips in any criterion-year, determination,
   grade summary, caveat and DOF all identical to the predecessor.
4. **The owner's explicit mid-session instruction**, verbatim: *"Is this a recommended keeper
   candidate? If so plz promote. If structural integrity improves but gates regress that may still
   be a keeper.."*

**WHAT IS NOT CLAIMED: this is not a screen pass.** `G-1` stands `FAIL`, unrepaired, here and in the
attestation, the keeper shard, the matrix shard and §5.4's header.

## 6. WHAT IS HANDED FORWARD

1. **MISO's COAL DEFICIT is the named successor object** — every scored coal band and system coal
   volume regressed here, on a class the model was already short of, and §4 routes it rather than
   absorbing it. It is an **attribution** question first: the gas repair displaced coal, so the
   question is whether the coal shortfall is a fuel-cost, commitment or must-run object.
2. **`_apply_simple_cycle_hr_floor` IS AN UNREGISTERED SOLVE-AFFECTING CHANGE IN SPIRIT** (rule 24
   `[R-REGISTRY]` / rule 28(c)): it changes every ISO's fleet, carries no field, no key, no epoch
   and no matrix row of its own. **This is a cross-ISO governance item, not MISO's to close** — five
   other lanes' keepers are in the same position MISO was in this morning, and each is
   unreproducible at HEAD until it re-solves.
3. **The census's LIVE routes are otherwise untouched** (rule 28(a)): `gas_variable_transport` +
   `gas_marginal_commodity_pricing` (owner-ruled, sourced, killed on one gate by 37 MW at miso-225),
   the CC CAPACITY-BASIS family behind miso-246's h19-headroom pre-check, and
   `nearby_fuel_price_zone_donor_guard` / `fleet_state_from_eia860` — which share **this** F923
   input seam, so rule 19 `[R-ONE-MECH]` says charter **one**, and this session has now moved that
   seam.
4. **MISO's 2022 `complete` marker remains the owner's open decision.** Nothing here grants, infers
   or recommends it. What changes in the evidence: the queue is one route shorter and the lane
   armed something for the first time in twelve sessions.

## 7. Governance

**Rule 1** `[R-STRUCT]`: no criterion, band or residual appears in any bar; the case rests on
construction. **Rule 12** `[R-PARALLEL]`: years sequential within each invocation. **Rule 13**
`[R-MEASURED]`: both inputs regenerate for a forward year from the same published tables. **Rule 14**
`[R-ACCURATE]`: the basis, applied against a worse coal fit rather than around it. **Rule 15**
`[R-DASHBOARD]`: registered; miso-245 pruned (`--force-uncite`); MISO carries exactly one run.
**Rule 16** `[R-ALLYEARS]`: 2023 2024 2025, one invocation, one bundle. **Rule 19** `[R-ONE-MECH]`:
no floor or bridge added. **Rule 21** `[R-DOF]`: **41/2 unchanged, zero parameters created.**
**Rule 22** `[R-HOLDOUT]`: training tier only; no marker sought. **Rule 24** `[R-REGISTRY]`: no env
knob, no hardcoded dict; `B`'s registry gap is escalated in §6.2, not exploited. **Rule 25**
`[R-ISO-SCOPE]`: MISO's shard, section and lane only. **Rule 27** `[R-PUSH]`: on-disk edits, blobs
verified. **Rule 28**: the handoff's recommended item taken; the tested cell updated in MISO's shard
in-session; the R-T duty discharged (`program-status.json` gate (a) re-keyed, a stamp re-key only —
MISO stays `fail` on both sides, absent from `complete`). **Rule 29** `[R-SCREEN]`: phase 0 first,
one screen year named on the mechanism's own footprint, **and the screen FAILED — §0a/§5**.
**Rule 31** `[R-RETAIN]`: **nothing was deleted.** The screen and control bundles are retained in
the session scratchpad; the promotion question was answered by the owner mid-session.

## 8. NON-CLAIMS

1. **`G-1`'s failure is not withdrawn, re-scoped or explained away**, and no bar was moved anywhere.
2. **This is not a screen pass**, and the full span's authority is named rather than borrowed.
3. **The coal regression is real, reported at full magnitude, and closed by nothing here.**
4. **Zero free parameters**; both objects are repo-wide owner-ruled defaults, not MISO inventions.
5. **No marker sought or implied**; **C3c untouched**, still the designated frontier.
6. **2025 C1/C2 are SKIPPED** on the preliminary EIA-923 vintage; no 2025 C1 pass is read as
   evidence, and 2025's only scored band — mean price — **moved away**.
