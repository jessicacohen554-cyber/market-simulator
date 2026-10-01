# PRECOMMIT — ercot-174: the UNIT-ATTRIBUTED partial-outage extract, and the unit-scoped event-cap composition

**Session ercot-174, 2026-08-06.** Written and pushed **BEFORE** the
unit-attribution derive is built and before any capture or solve. Everything
below — the attribution rule, the composition rule, the proofs, the
predictions, the stop rules and the gate assignment — is fixed here and is not
renegotiated afterwards. The kill gates are `PRECOMMIT-ercot172` §5 **inherited
verbatim** (as ercot-173 inherited them), not re-derived.

Charter: the handoff opening ercot-174 (the ercot-173-named successor). It
grants owner adjudication for the **derive half** (a rule-23 derive-construction
change: GRAIN, not constants) and specifies the mechanism half.

Base: `origin/main` at `241d8019` (the ercot-173 merge, verified present:
`results/calibration/FINDING-ercot173-event-cap-reconciliation-2026-08-06.md`
exists and `docs/mechanism-testing-matrix.md` §5.1 carries "Item 16 — EXECUTED
at ercot-173").

---

## 0. The object, and why a composition-wide fix cannot be it

`FINDING-ercot172` §3–§4 attributed the two 2024 shed hours to the event-cap
ceiling `f_ceiling = f_window × f_partial` sitting **below the plants' own
contemporaneous CEMS output** at 8/9 and 4/6 named plants. `FINDING-ercot173`
§2 built the blanket reconciliation (`min()` everywhere) and measured the
answer in **both** directions:

* at the ercot-172 plants the double-count is real — removing it restored
  **+1,118.8 MW** at h2827 (≥ shed 565.1 ⇒ CLEARS) and **+353.3 MW** at h3067,
  exactly as attributed; but
* fleet-wide the blanket `min()` re-admitted **+0.98 / +1.95 / +2.73 TWh/yr**
  of coal above the incumbent product ceiling (**G-COAL148 FAIL** at 2–5× its
  bar), moved class energy far past **G-SPAN**, and degraded tail formation
  (**G-C3c FAIL**). **REJECTED-AS-ARMED.**

`FINDING-ercot173` §3 fixed the structural reading, and this session's rule is
that reading made executable, **verbatim**:

> the `window` and `partial` layers measure the **SAME** units' downtime at
> some overlaps (the ercot-172 named plants — there `min()` is right and the
> product double-counts) and **DIFFERENT** units' downtime at most others
> (there the product is right and `min()` under-removes).

So the correction **must be unit-scoped, never composition-wide**. The blanket
`min()` composition stays **R** (DO-NOT-REDO); this session does not re-open it.

---

## 1. What this session may and may not do

**Granted (this handoff, rule 23):** re-emit the partial extract at **unit
grain**. This is a derive-**construction** change — the GRAIN of the emission —
and explicitly **not** a change to the detector's identification constants.

**Refused / out of scope, all standing:** the blanket `min()` composition (R,
ercot-173); the 2023 depth/excess-cheap-depth premise (REFUTED at the
aggregate, ercot-173 Phase 0 — no depth lever is re-opened);
`ercot_storage_rt_offer_surface` (R); `energy_online_capability_cap` (R); the
CC-headroom per-unit crosswalk (FILED-UNLICENSED); ALL coal offer-curve lanes
(CLOSED); per-year CT re-identification (REFUSED); West/Panhandle topology
(CLOSED); ercot-172's C3 — ceiling floored at contemporaneous output (REFUSED
under rule 13 `[R-MEASURED]`); no per-hour telemetered-HSL cap; no aggregate
capability cap.

**Holdout (rule 22).** ERCOT holds **no** `complete` marker: 2022 / 2019 /
H1-2026 stay quarantined. Every solve is `--year 2023 2024 2025`. The derive,
however, is **data prep**, which rule 22 as amended 2026-08-06 places outside
the spend gate entirely — *"WHAT IS HELD OUT IS THE SCORE, NEVER THE DATA …
Data intake needs NO per-ISO/per-window authorization and no marker. Prep it,
apply it to every year, keep it consistent."* The committed extract covers
**2018–2026**; the unit-attributed companion is therefore emitted over the
**same 2018–2026 span**, both because consistency demands it and because the
byte-equivalence proof (§2b) is only meaningful over the committed file's own
span. No out-of-training year is solved, scored or registered.

---

## 2. PHASE A — the unit-attributed extract (derive only, no LP)

### 2a. What changes, and what may not

The detector's frozen identification constants
(`scripts/lib/outage_detect.py`: `_MIN_DAYS = 5`, `_SMOOTH_DAYS = 7`,
`_CEILING_FRAC = 0.65`, `_RUN_FLOOR_CF = 0.06`, and
`derive_partial_outages._BASELOAD_CF = 0.55`, `_DETECT_GROUPS`) are **imported
verbatim and not re-valued** (rule 23 `[R-FROZEN-DERIVE]`). Same windows, same
`derate_factor`s. The **only** change is that each plateau now also carries
**which CAMPD units carry it** and their `unit_capacity_mw`.

**Emission target — a COMPANION file, not a replacement.**
`data/raw/campd-partial-outages.csv` (plant grain) is left byte-untouched, so
every incumbent consumer is provably inert. The unit grain is written to
`data/raw/campd-partial-outages-units.csv` by the **same script and the same
detection pass** (`scripts/data/derive_partial_outages.py --emit-units`), so
the two files come from one in-memory row set and the equivalence is
structural, not merely re-measured.

**No new curated datatype is minted**, so the schema/clean contract is not
engaged: the companion is read from raw exactly like its siblings
`campd-unit-outages-short-<ISO>.csv` and `campd-partial-outages-<ISO>.csv`
(`unit_outage_short_derate_factors` / `unit_partial_outage_derate_factors` both
read their raw CSV with no clean partition). Established precedent in the same
module.

### 2b. The attribution rule — FIXED HERE, zero new constants

For each detected plateau at plant `p`, year `y`, day window `[d0, d1)`, and
for each CAMPD unit `u` at facility `p` in `y` (from
`data/raw/campd-unit-level/TX_{y}.parquet`, the same source the window extract
uses):

* `cf_u` = the unit's own hourly gross on the year clock (CAMPD-omitted hours
  zero-filled, the standard construction) divided by `detect_cap_u`, where
  `detect_cap_u` is the EIA-860 nameplate resolved by the window deriver's own
  `unit_capacity_mw()` ladder (exact id → unique trailing digits → observed
  CAMPD peak). **Deliberately the same capacity index the window extract
  uses**, so unit capacities are consistent across the two layers.
* `ref_u` = the 90th percentile of the unit's daily-max `cf_u` over its
  **running** days (`daily mean > _RUN_FLOOR_CF`) — the plant detector's own
  `ref` statistic, at unit grain.
* `ceil_u` = the **median of the unit's daily-max `cf_u` over the plateau
  window** — the plant detector's own `ceiling` statistic, at unit grain.
* **`u` CARRIES the plateau iff `ref_u > 0` and `ceil_u < _CEILING_FRAC ×
  ref_u`.**

That is the detector's own frozen depressed-ceiling test, applied to the unit's
own series. **No new constant is introduced** — `_CEILING_FRAC` and
`_RUN_FLOOR_CF` are imported from the frozen module. **G-DOF is satisfied by
construction.**

A plateau with **no** carrying unit is emitted with an **empty `unit_id`**, so
the aggregation identity below is exact and the Phase-B consumer sees an empty
unit set (⇒ product ⇒ byte-identical to the incumbent). Fail-safe in the
conservative direction: the arm can never act on an attribution it does not
have.

Emitted columns: the committed file's seven verbatim (`oris_code`,
`plant_name`, `plant_group`, `year`, `outage_start`, `outage_stop`,
`derate_factor`) plus `unit_id`, `unit_capacity_mw`, `capacity_source`,
`n_units_carrying`.

### 2c. BYTE-EQUIVALENCE PROOF — the rule-23 proof that only the GRAIN changed

Run before anything consumes the companion; **stop-the-line on failure**.

* **BE-1 — the committed extract reproduces.** The **unmodified** deriver, run
  over 2018–2026, reproduces `data/raw/campd-partial-outages.csv`
  **sha256-identically**. *(Run as a feasibility precondition BEFORE this
  document was written, on frozen code with no session change in it, and
  disclosed here rather than omitted: **PASS**, sha256
  `8d6f049e165b1b6574b38d57cc1bd8542dc3ccda86a5a5a5e313cde86ac736b5`. It is an
  identity check on committed code and carries no information about the
  mechanism.)*
* **BE-2 — the plant-grain emission is unchanged by the `--emit-units` work.**
  With the attribution code in place, the plant-grain file the same run writes
  is **sha256-identical** to the committed extract (same hash as BE-1).
* **BE-3 — the unit-grain file aggregates back exactly.** Projecting
  `campd-partial-outages-units.csv` onto the seven committed columns,
  de-duplicating and re-sorting on the committed sort key
  (`["year", "oris_code", "outage_start"]`) yields a frame **equal** to the
  committed extract — same row count, same order, same values, **sha256
  identical** when re-serialised with the committed writer. Plateau count,
  per-year window count and per-year plant count all match exactly.

Only BE-1/2/3 all passing establishes "the GRAIN is the only change."

---

## 3. PHASE B — the unit-scoped composition (ONE default-off gate)

### 3a. The gate

**New `ScenarioConfig` field `ercot_dam_availability_event_cap_unit_scoped`,
default `False`**, matrix row in the same PR (rule 28c), registered in the
cache-key default-drop list (the ERCOT-148/149 treatment), recorded in both
bundles' `run_config.json` (rule 24).

The ercot-173 field `ercot_dam_availability_event_cap_reconciliation` is
**KEPT at default-off with its `R` verdict intact** — it is a boolean
structural gate, not a fitted knob, so rule 26 `[R-DELETE]` does not call for
its removal (established precedent: `ercot_storage_rt_offer_surface`,
`ercot_energy_online_capability_cap`, both `R`, both still present at default).
Repurposing its NAME to different semantics would corrupt the `R` record, so a
new field is used. The unit-scoped gate **takes precedence** when both are set;
the arm sets only the new one.

### 3b. THE COMPOSITION RULE — verbatim, fixed here

Inside the existing ERCOT-148/149 event-cap block
(`src/market_sim/data/fleet/arrays.py`, the `_evcap_scope` block) — **no second
cap layer, no new mechanism** (rule 19 `[R-ONE-MECH]`). For each generator bin
`b = (plant_code, plant_group)` in `_evcap_scope` and each hour `t`:

* `f_w(b,t)` — the **window-family** ceiling: the composition of `_cap_layers`
  **exactly as today** (incumbent product among themselves; on the keeper
  recipe `unit_outage_short_windows` and `unit_partial_outage_windows` are both
  `False`, so `_cap_layers` is the single `unit_outage_derate_factors` layer).
  **Unchanged by this session.**
* `f_p(b,t)` — the ERCOT plant-grain partial-plateau ceiling, keyed by the
  extract's own `(oris_code, plant_group)` (the ercot-173 **C1** grain repair,
  carried forward here; proven **inert** on the current bins sheet by the
  ercot-173 SP-3 seam proof, and re-asserted as SP-3 below).
* `U_w(b,t)` — the set of CAMPD unit ids whose **window**-extract rows are
  active at `t` and route to bin `b` via `_unit_outage_target`, under the same
  `duration_days >= UNIT_OUTAGE_MIN_DAYS` filter the factor itself uses.
* `U_p(b,t)` — the set of CAMPD unit ids **attributed** (§2b) to the partial
  plateaus active at `t` and routing to bin `b` via the **same**
  `_unit_outage_target`.

Then

```
ceil(b,t) = min(f_w(b,t), f_p(b,t))      if  U_w(b,t) ∩ U_p(b,t) ≠ ∅
            f_w(b,t) × f_p(b,t)          otherwise
```

and the cap is applied as today, `availability[b] = min(availability[b],
ceil(b))`. Unit ids are matched **normalised** (`_norm_unit_id`); both sides
originate in the same CAMPD `unitId`, so raw equality is expected and any
normalisation-induced difference is reported as a diagnostic.

**Zero fitted scalars.** The only new information entering the LP is a set of
measured CAMPD unit attributions.

**What is deliberately NOT built.** For *disjoint* unit sets the exact answer
is **additive** in capacity share (each layer removes its own units), which is
strictly deeper than the incumbent product. Moving to additive would be a
second, deeper change confounding the measurement of this one, and it is not
what the handoff charters. **The incumbent product is retained on disjoint
sets**, unchanged. Recorded so it is not re-found and mis-attributed later.

### 3c. Structural properties — provable, and the pre-registered BRACKET

Since `min(x,y) ≥ x·y` for `x,y ∈ [0,1]`, pointwise for every scoped bin-hour:

```
ceil_product  ≤  ceil_unit_scoped  ≤  ceil_min
(incumbent)      (this arm)           (ercot-173, R)
```

with equality to `ceil_min` exactly on the shared-unit hours and to
`ceil_product` everywhere else. Two consequences fixed **now**:

1. The arm can only ever **RESTORE** capability relative to the incumbent,
   never remove more.
2. **Every measured movement of this arm is bounded in sign and magnitude by
   the ercot-173 record.** In particular G-COAL148 movement lies in
   `[0, +0.98 / +1.95 / +2.73 TWh]` for 2023/2024/2025, and the C3a-2023
   movement lies in `[−1.23 pp, 0]`.

---

## 4. PREDICTIONS and STOP RULES — recorded before any measurement

* **P-BE** — BE-1/2/3 all PASS. A failure is stop-the-line: the grain claim is
  false and nothing downstream may run.
* **AT-1 (pre-solve, attribution scale)** — the count and share of scoped
  bin-hours at which the composition switches from product to `min()` (i.e.
  where both layers are active AND their unit sets intersect). Predicted
  **small**: a minority of the both-layers-active hours. Reported exactly.
* **AT-2 (pre-solve, ceiling-lift ratio) — STOP RULE.** Per year, over scoped
  bin-hours,
  `ρ = Σ(ceil_unit_scoped − ceil_product) / Σ(ceil_min − ceil_product)`
  — the share of the blanket arm's total ceiling lift that survives unit
  scoping. Predicted **ρ well below 0.5**. **If ρ ≥ 0.5 in any year, STOP
  before the solve**: the attribution is not discriminating and the arm is the
  rejected ercot-173 blanket arm in disguise. Report as an attribution failure,
  do not solve, do not promote.
* **P-COAL148 (post-solve) — STOP RULE.** Expected coal-above-product-ceiling
  movement **+0.1 to +0.3 TWh/yr** — the ercot-172 named plants' shared-unit
  overlaps only — comfortably under the **+0.5 TWh** G-COAL148 bar. **If the
  measured movement reaches ≥ 0.5× the ercot-173 blanket number in any year
  (≥ +0.49 / +0.98 / +1.37 TWh), the unit attribution is WRONG**: stop, report
  as an attribution failure, no promotion — independently of whether G-COAL148
  itself passes.
* **P-2024** — the ercot-172 named plants (W A Parish, Martin Lake, Guadalupe,
  J K Spruce, Sandy Creek) are predicted to be **shared-unit overlaps**, so the
  two shed-hour restorations should reproduce the ercot-173 numbers or a large
  fraction of them: **+1,118.8 MW at h2827** (≥ shed 565.1 ⇒ 2024-04-28
  **CLEARS**) and **+353.3 MW at h3067** (< shed 550.3 ⇒ 2024-05-08 **SHRINKS**,
  may persist). **G-SHED: 2024 count 2 → ≤1.**
* **P-NULL — the falsifier, admissible as an outcome.** If the attribution
  finds **no** shared units at the ercot-172 named plants, the arm is **INERT**
  (byte-identical to control) and `FINDING-ercot173` §3's structural claim is
  **REFUTED**. That is reported as such — a real result, not a failed session —
  and there is no promotion.
* **P-C3a-2023** (reported FIRST in the write-up whatever it does):
  availability can only rise, so the movement is **≤ 0**, bounded below by the
  ercot-173 **−1.23 pp**. Predicted **0 to −1.23 pp** (more negative). Limb 1
  was never the 2023 lever (ercot-173 §0) and this is not judged on C3a-2023
  moving; per rule 1 `[R-STRUCT]` it is judged on structural fidelity and the
  pre-registered gates.
* **P-SPAN** — class-energy movement strictly inside the ercot-173 numbers
  (which failed at 2023 COAL_PRB +1.9 %, 2025 COAL_PRB +5.1 %, CT_PEAKER
  −10.4 %); predicted **inside the 0.5 % band**, but no claim is made that it
  passes — G-SPAN decides.
* **Robustness, REPORTED and explicitly NON-SELECTING**: the shared-unit hour
  count under an alternative attribution test (`ceil_u < ref_u`, i.e. any
  depression, instead of the frozen `_CEILING_FRAC`). Reported as a band so the
  attribution's sensitivity is visible. **It is never used to choose**; the
  frozen-constant test is the mechanism, fixed here.

### 4a. SEAM PROOF — no LP, BEFORE the solve, stop-the-line on failure

Mirrors the ercot-173 SP pattern.

* **SP-1** — flag-ON capture equals the intended composition **exactly** on
  every layered scoped tranche: arm `== min(B, ceil_unit_scoped)` where
  `ceil_unit_scoped` is recomputed independently from the loaders by the §3b
  rule (tolerance 1e-6; y = 2023 and 2024).
* **SP-2** — every tranche **outside** `_evcap_scope` is byte-identical
  control vs arm.
* **SP-3** — **C1 inertness** re-asserted: class-grain and plant-grain partial
  dicts induce identical per-bin factors on the current bins sheet.
* **SP-4** — **gate-off no-op**: with the new flag at its default the composed
  availability is byte-identical to the control capture.
* **SP-5** — **strict-subset check**: on every scoped bin-hour,
  `ceil_product ≤ ceil_unit_scoped ≤ ceil_min` holds (§3c), and
  `ceil_unit_scoped ∈ {ceil_product, ceil_min}` pointwise.

---

## 5. KILL GATES — PRECOMMIT-ercot172 §5, inherited VERBATIM

Not renegotiated. **Failing any live gate ⇒ REJECTED-AS-ARMED**, reported as
such.

* **G-BIT — declared N/A NOW, pre-solve**, with the reason recorded: the rule
  is **year-agnostic** (an attribution rule with no year scope), so
  PRECOMMIT-ercot172 §3c(a) forbids a year-scoped correction and **G-SPAN
  replaces it**. The two are mutually exclusive; this is stated before the
  solve, never after.
* **G-SPAN** — in 2023 and 2025: no class's annual energy moves more than
  **0.5 %**, the shed-hour count does not increase, and the ledgered C3c tail
  counts (2023 61/181, 2025 3/31) do not degrade.
* **G-SHED** — the **2024** shed-hour count must **FALL**, and no year's shed
  count may rise.
* **G-SPUR** — the C3c spurious mid-band tail-hour count must not increase in
  any year.
* **G-C3c** — the three ledgered tail counts (61/181, 25/53, 3/31) must not
  degrade.
* **G-COAL148** — coal dispatch above the measured **PRODUCT** ceiling may not
  rise more than **+0.5 TWh** in any year, scored with the committed ercot-149
  probe machinery against the **INCUMBENT product** ceiling (the 4.36/4.98/5.01
  TWh comparability basis). The ERCOT-148/149 precedence is reconciled, never
  repealed.
* **G-DOF** — **zero** new fitted scalars (satisfied by construction, §2b/§3b).
* **G-D2** — no class's forced share may cross its rule-20
  `[R-FORCED-BUDGET]` cap as a result of the arm.
* **LOYO** — leave-one-year-out within 2023–2025 before any promotion. The
  rule is **parameter-free** (nothing is identified on any year), so LOYO is
  recorded with per-year deltas in its place, as at ercot-173.
* **G-NEUT** (PRECOMMIT-ercot172 §3c) is **not reached**: the attribution
  restricts no event-window population — it is a year-agnostic,
  class-agnostic refinement of how two existing layers compose — so the
  ercot-171 gate has nothing to bite on. Any future proposal that *does*
  restrict the window population must clear G-NEUT before it may be built.

---

## 6. The LP runs, and the ercot-167 SOC re-gate

**ONE LP run pair.** Control + arm, `--year 2023 2024 2025`, one bundle each,
**SAME-HEAD** — the tree is **not rebased between the two solves** (the
ercot-173 mid-rebase incident is the precedent: a control that began before a
rebase was not same-HEAD with its arm and had to be discarded). Years
sequential within each invocation, control and arm sequential (rule 12; the
per-plant multi-zone ERCOT LP is several GB). **Both runs are registered
whatever the outcome** (rules 15/16), keeper or rejected.

**ercot-167 SOC re-gate.** `ercot_storage_as_soc_reserve` stays armed in BOTH
arms; nothing is built for it. RG-1 and RG-2 are **re-scored on the
pre-registered ercot-173 definitions**. `FINDING-ercot167` §3's reopen
condition is *"after the 2024 defect's fix LANDS"* — so the re-gate is
**DISCHARGED in this record only if all gates pass AND the arm lands**. If the
arm is rejected, the re-gate stays **UNMET**, exactly as at ercot-173.

---

## 7. Governance

Rules honoured and how: **1** `[R-STRUCT]` the arm is judged on structural
fidelity and the pre-registered gates, never on the residual moving; **12**
years sequential within a run; **19** `[R-ONE-MECH]` one cap block, its
composition refined — never a second layer; **20** `[R-DOF]` zero new fitted
scalars, both halves; **22** solves 2023–2025 only, no holdout year solved,
scored or registered (derive is data prep, outside the spend gate); **23**
`[R-FROZEN-DERIVE]` the detector's constants are imported verbatim and the
GRAIN-only claim is proved by BE-1/2/3; **24** `[R-REGISTRY]` the new gate is a
registered `ScenarioConfig` field in `run_config.json`, no off-registry
channel; **25** `[R-ISO-SCOPE]` ERCOT-scoped; **26** `[R-DELETE]` §3a (boolean
structural gate, not a fitted knob — precedent cited); **27** `[R-PUSH]` every
push touching a ≥300-line file is blob-verified; **28** `[R-MECH-MATRIX]` the
new field's matrix row lands in the same PR, §5.1 gains item 17, and every
touched cell is re-stamped in this session — rejections included.

**Bookkeeping owed in this same session, whatever the outcome:** both runs
registered on the backcast dashboard; `docs/mechanism-testing-matrix.md` §5.1
item 17 + cell re-stamps; `results/calibration/FINDING-ercot174-*.md`;
`docs/calibration-log/ercot.md`.

**Surfaced, NOT decided (own lane, no solve):** the run168b keeper does not
reproduce at current main (ercot-173 §5 — control drift C3a-2023 −28.48 % vs
committed −29.88 %, 2023 spurious 10 vs ledgered 3, tail 66 vs 61, a fifth 2023
shed hour 4098). Whether that is re-keyed or re-solved at HEAD is a governance
question for the owner. This session scores every gate on its **own same-HEAD
A/B pair**, so the mechanism deltas are clean regardless.

**ERCOT status, unchanged going in:** determination **NOT-YET**, fail set
{C3a, C3b}; C3a 2023 −29.9 % hub / 2024 PASS / 2025 −9.1 %; C3b 2023 0.604,
2024 0.206; C7 CLOSED; C3c ledgered CAVEAT ×3. The queue is **not** cleared and
ERCOT is **not** calibrated; no frontier or `complete` assessment is in scope.
