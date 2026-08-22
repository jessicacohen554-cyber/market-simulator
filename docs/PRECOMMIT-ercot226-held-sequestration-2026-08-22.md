# PRECOMMIT — ercot-226: the 2023 HELD-SEQUESTRATION factor program (`ercot_as_held_requirement` family) — factor table, identification instruments, kill preconditions and gates, pinned BEFORE any measurement and BEFORE any solve

**Session ercot-226 (owner-dispatched program), 2026-08-22, branch
`claude/ercot-2023-summer-scarcity-9lg3nm` (base = origin/main `317be02`).
Keeper at pin: `2026-08-20-ercot223-arm-eventrelease` (NOT-YET, fail set
{C3a-2023 −39.7 %, C3b-2023 NRMSE 0.729}, C3c ledgered CAVEAT ×3;
2024/2025 clean at +0.4 %/0.131/22 h and −7.6 %/0.099/1 h).** This file is
pushed and blob-verified BEFORE the derive reads any delivery-2023 row,
BEFORE any Phase-0 measurement is computed, and BEFORE any solve.

## 0. THE OWNER DISPATCH (verbatim, recorded per the X-1/X-2/B-1
signature-by-dispatch precedent)

The session prompt IS the owner speaking and carries owner authority. The
ruling and waivers, verbatim:

> OWNER RULING — WHY THIS IS IN-RULES: the 2023 ERCOT market design and
> operator conduct were measurably different (ECRS go-live 2023-06-10 with
> no price-based release until the 2024-08-01 reform; documented operator
> conservatism in AS procurement and capacity sequestration — the IMM's
> artificial-shortage record). Representing a real, dated, measured design
> regime is rule-1 structure, not tuning. The lane's "no admissible lever /
> Door D floor / lane rests" posture is a governance position, and I am
> overriding it.

> - W-1: The Door D floor and the lane-rests posture are SET ASIDE for this
>   program. Do not re-enter Door D; do not wait for 2026 SOM anchors.
> - W-2: 2023-ONLY solves are authorized as diagnostic probes (rule 16's own
>   probe clause). Single-year probes are NOT dashboard-registered (owner
>   waiver of per-probe rule-15 registration to honor rule 16's
>   no-single-year-bundles-on-dashboard clause); instead every probe's full
>   scored metrics land in a committed JSON + the FINDING's probe table.
>   Only the final combined 3-year bundle is registered.
> - W-3: The 2023 operator-conservatism object is RE-OPENED in year/window-
>   scoped, measured-input form. Admissible under rules 13/14 as measured
>   market-design/operator inputs: 2023 AS procurement and award quantities
>   (plans, ASPLANNP433, 60-day DAM awards), the pre-reform ECRS/RRS
>   deployment design and its demand-curve representation, measured RUC /
>   out-of-market commitment MW, the HASL carve depth, and operator
>   load-forecast conservatism — each entering as a formulaic input keyed to
>   its real design window or to measured data that is naturally near-zero
>   outside 2023. STILL FORBIDDEN, no exceptions: any scalar identified from
>   the price/volume residual; feeding realized prices or realized per-unit
>   dispatch back in; Door A fitted conduct (refused ×3); ercot-162 verbatim
>   offer surfaces; item 11 per-unit crosswalk (Q-B FINAL); item 8. If a
>   candidate factor coincides with an adjudicated matrix cell, name the
>   cell and the waiver invoked, or drop it — silent re-tests are still
>   banned.
> - W-4: ADOPTION AND PROMOTION ARE PRE-AUTHORIZED: any factor clearing the
>   precommitted adoption criteria goes into the combined config without a
>   further owner round-trip, and the final bundle, if it clears its gates,
>   is promoted to keeper in this session (my standing structural standard,
>   as at ercot-221, applies to borderline mechanical verdicts — escalate in
>   the handback rather than self-reject).
> - W-5: ercot-218b B-1 (telemetered capability reconciliation) stays
>   UNSIGNED — do not arm Stage 1. If your probe evidence says it is the
>   missing keystone, say so in the handback with the measurement; do not
>   build it.

Mid-session, on plan review, the owner added (verbatim, three messages):

> "Is this a complete list of potential factors? I want to be
> comprehensive. If yes, proceed but"
> "You can also give me prompts to run each factor in parallel in diff
> sessions"
> "To get this done faster then you review results for final combined run"

— which (a) demands the §4 completeness sweep and (b) restructures Phase 1
as HUB-AND-SPOKES (§7): this session emits one complete handoff prompt per
surviving factor for parallel execution in separate sessions, and remains
the single reviewing/combining/recording session.

## 0b. Directive-premise corrections (recorded; substance unaffected)

1. **B-1 is SIGNED, not unsigned.** The record
   (`docs/DECISION-CARD-ercot218b-artificial-shortage-structural-2026-08-18.md`,
   signature appendix, commit `ecbad28`) carries "B-1 SIGNED (owner, by
   dispatch of ERCOT-219, 2026-08-18)"; it was spent at ercot-219 and the
   arm was REJECTED-AS-ARMED. The card that is UNSIGNED (with a DO-NOT-SIGN
   recommendation) is **B-2** (commitment-side reconciliation,
   `DECISION-CARD-ercot220`). W-5's intent is honored exactly as written in
   substance: `ercot_capability_reconciliation` stays OFF (Stage 1 not
   armed), and B-2 stays unsigned. Nothing in this program touches either.
2. **"W-3" namespace.** Card W (ercot-200 §5) has a VACANT instrument slot
   also labelled W-3, with its own standing fence: the IMM's own
   quantification of the 2023 effect (×2 Jun–Dec, $12 B, the 75 %-release
   counterfactual) is never usable as identification (the refused FFR-6A
   row-4 shape). This file writes "waiver W-3 (ercot-226)" for the owner
   waiver above and honors the card-W fence throughout: no factor is
   identified from the IMM's quantification; the IMM record supplies
   *drivers and windows*, never parameter values.
3. **Environment pins.** `requirements.txt` pins highspy 1.14.0 /
   pandas 3.0.3 / pyarrow 24.0.0; the keeper environment is highspy
   **1.15.1** / pandas **3.0.5** / pyarrow **25.0.1** (python 3.11.15,
   numpy 2.4.6, scipy 1.17.1 match). Every solving session (hub and spokes)
   installs the requirements THEN re-pins those three, and verifies before
   its control replay — otherwise G-REPRO fails spuriously on solver
   version, not on model content.

## 1. THE OBJECT (what the measured record already pins, and the channel
doctrine every factor must honor)

- At the missed 2023 tail hours the model reproduces ERCOT's physical
  dispatch fuel-by-fuel (±8 %; demand == EIA-930 generation sum to 0.6 MW)
  while clearing 3–5× low; reality's own ORDC was nearly silent there
  (RTORPA p50 $0.84 with PRC 5.7–7.7 GW, never < 4,132 MW, 0 hours under
  the EEA-1 2,300 MW trigger). The missing dollars are "in the offer at the
  clearing point, not in the MW at the clearing point"
  (FINDING-ercot216 §3/§5).
- The armed sequestration (`ercot_ecrs_conservative_deployment`,
  `ercot_nonreleasable_as_withholding`, the measured ASPLANNP433 plan) is
  present and correctly dated, but SLACK at the missed hours (reserve dual
  binds 2/88, mean $0.1): the model satisfies the requirement while
  retaining "more responsive headroom than the real grid retained" — the
  ~2.7 GW wedge (FINDING-ercot217 §5; RESEARCH-ercot218b §4 names the same
  object as the first NOT-CARRIED row). Forcing the bind was rejected at
  +700–800 % C3a (ercot41/43).
- Even reality's own PRC under the registered LOLP curve gives windowed
  offers p50 $650 against measured conduct $3,361–5,000 (ercot-220 L5) —
  the standing bound on any margin→ORDC-mediated depth mechanism.
- The armed conduct mechanism (`ercot_storage_adaptive_expectation` +
  `ercot_adaptive_event_release`) is starved by the model's own path:
  7 spike days vs reality's 23 (ercot-221/223).

**CHANNEL DOCTRINE (binding on every factor):** admissible factors act on
the ENERGY/TIGHTNESS channel — the supply physically available to SCED at
the margin (rigid-family carve depth and location) — and thereby also feed
the armed adaptive conduct mechanism more of its own spike days. NO factor
may manufacture price through the ORDC-adder channel: reality's RTORPA at
the target hours is ≈$1, so an adder-channel "fix" would reach the number
through a mechanism the real market did not use (rule 1). Every probe
reports channel attribution (§5.2) and a withheld-family VOLL-shortfall
engagement count (§5.3); improvement carried by manufactured reserve
shortfall is a FAIL, whatever it does to C3a.

## 2. THE FACTOR TABLE

Each row: (a) external driver + citation; (b) identification source +
formula (zero residual-fitted scalars); (c) window/data-key + why 2024–2025
are untouched; (d) predicted sign on summer-2023 scarcity hours; DOF row;
adjudicated-cell coincidences named per waiver W-3 (ercot-226).

### F1 — held-depth: telemetered RT AS responsibilities deepen the rigid families
- **(a) Driver:** documented 2023 operator conservatism in AS procurement
  and real-time holds — IMM 2023 SOM §II.G (the artificial-shortage
  record); the HASL carve is Nodal Protocols §6.5.7.6.2.3 / §3.17.
- **(b) Identification:** NP3-965 60-Day SCED Gen Resource Data
  (`data/raw/ercot/SCED/*.parquet`), ONLINE∖ONTEST resources, the five
  telemetered per-product columns `Ancillary Service {REGUP, RRS, RRSFFR,
  NSRS, ECRS}` (MW) — the instrument ercot-218 §1.4 built and verified
  (HASL ≈ HSL − Σ resp at (hour, class) grain). System-level hourly
  per-product series derived once (§6, C1). **Formula:** for each rigid
  product p ∈ {REGUP, RRS, ECRS} and hour t inside its armed rigid window,
  `requirement_p(t) = max(plan_p(t), held_p(t))`. held_RRS uses the `RRS`
  column alone (RRSFFR written separately and EXCLUDED from the sum —
  the ercot-218 nesting-arithmetic refusal; conservative under the max).
  The conservatism object is `delta_p(t) = max(0, held_p(t) − plan_p(t))`.
- **(c) Window/data-key:** measured-where-published. The tracked corpus
  covers delivery-2023 (pubs 2023-03..2024-03); an absent file/column reads
  all-zero → `max(plan, 0) = plan` → **2024 and 2025 arm ≡ control BY
  CONSTRUCTION**. Disclosures: (i) the "≈0 outside the window" claim for
  2024+ is not measurable on-disk (2024-04+ payloads gitignored and
  history-stripped); the mechanism is therefore explicitly data-keyed, not
  merely empirically small. (ii) Delivery-June-2023 ECRS is under-measured
  (the ECRS column first appears in pub 2023-08 shards): June ECRS stays at
  plan; NO reconstruction from HSL−HASL−Σ others (that construction is the
  rule-13 line the RTC+B adapter also refuses to cross). (iii) held is Gen
  Resource only — Load Resource provision is inside the plan, so RRS
  deepening is conservative. Forward story (rule 17/13): the held series is
  a measured market quantity that regenerates for any year ERCOT publishes
  the disclosure; post-RTC+B the rigid families themselves retire, so the
  mechanism dies with the design it represents.
- **(d) Predicted sign:** + via energy displacement (deeper rigid carve →
  less merchant headroom at the margin → λ up in tight hours → more model
  spike days → adaptive expression up). **Honest risk, pre-registered:**
  Σ held ≈ plan is plausible (the plan IS the operator's conservative
  product), in which case the depth is not in the system-level quantity —
  see the §5.4 kill precondition.
- **DOF row:** zero new fitted scalars. Inputs: the measured held series
  (source above), the existing plan series, the existing rigid-window date
  machinery. New boolean `ercot_as_held_requirement` (default False).
- **Coincidences named:** Door A ×3 (ercot-210/211/218) used the SAME
  NP3-965 telemetry as a CONDUCT instrument — refused; F1 uses it as a
  measured QUANTITY input, the form waiver W-3 (ercot-226) explicitly
  re-opens ("the HASL carve depth", "AS procurement and award
  quantities"). Distinct from `ercot_artificial_shortage_pricing` R
  (rtolhsl ONLINE aggregate — dimensional wall) and from item 11 / Q-B
  (per-unit capability crosswalk): F1 is per-product system MW on the
  AVAILABLE basis, no capability level, no per-unit mapping.

### F1b — NSPIN held-depth sub-variant
- **(a)** Same driver; 2023 NSPIN procurement was large and front-loaded
  (monthly plan means 5,052 MW May → 2,206 MW Aug — ercot-217 §2 row 5);
  online Non-Spin responsibility carves HASL exactly like the other
  products.
- **(b)** Same instrument, `NSRS` column; formula `requirement_NSPIN(t) =
  max(plan(t), held_NSRS(t))` on the (non-rigid) NSPIN family, which keeps
  its standard ramp steps — matching the real design (online NSPIN energy
  is SCED-dispatchable at its offer; the 2024-08 reform was ECRS-specific).
- **(c)** Same data-key (measured-where-published; zeros elsewhere).
- **(d)** + but weaker (ramp-priced release, not VOLL). **Probed only if**
  the §5.4 F1b materiality screen passes. New boolean
  `ercot_as_held_requirement_nspin` (default False); zero fitted scalars.

### F2 — held-location: measured per-class allocation of the held MW
- **(a) Driver:** the same IMM record — WHERE the sequestered MW sat. The
  wedge hypothesis: the LP meets the requirement with the cheapest-to-hold
  (idle/extra-marginal) capacity, so the headroom rows stay slack
  (ercot-217 §5); reality held AS on specific online units (the HASL carve
  on marginal CC/coal), displacing marginal energy supply. Misallocated
  holds ARE cheap headroom the real market did not have — a licensed third
  basis at the ~2.7 GW wedge (per-unit route Q-B-closed; online-aggregate
  route ercot-219 R; neither is this).
- **(b) Identification:** the by-class NP3-965 responsibility series (C1's
  second output; RESTYPE→class map extending
  `build_ercot_as_by_restype_from_60day.py`), cross-checked against the
  committed `ercot_2023_as_by_restype_hourly.parquet` DAM awards.
  **Formula (Option A, LP-level):** for each holding thermal class C with
  measured held MW: a new reserve class + class-scoped headroom row
  `Σ_{g∈C∩z} P[g,t] + R[c_C,z,t] ≤ cap(C,z,t)`, a rigid family
  `{C}_held` with requirement `held_C_used(t) = min(held_C(t),
  Σ_{g∈C} pmax_g·avail_g(t))` (data-vs-data clip, no free parameter),
  and a conserving credit: each rigid product's system requirement reduced
  by the class-allocated MW so total held is conserved (no double-count).
  Storage excluded from the class rows (`headroom_storage` opt-out;
  storage AS is already measured-credited via
  `ercot_storage_as_product_credit`). `held_C(t)` sums the rigid products'
  class responsibilities inside their rigid windows.
- **(c) Window/data-key:** same measured-where-published key (2023-only
  coverage ⇒ 2024/2025 arm ≡ control by construction). Forward story:
  rule 13's own admissible example is "a measured ancillary-service power
  reservation"; the backcast uses the measured allocation exactly as it
  uses `outage_source="historic"`, and a forecast year uses the endogenous
  allocation. If a future intake extends the corpus into 2024/2025, the
  measured allocation applies there too and any drift must be non-degrading
  and attributed to that year's own data (R-ACCURATE posture) — never
  year-keyed away.
- **(d) Predicted sign:** + and potentially the largest (moves the carve
  onto the marginal units). **Build gate (data-gated, precommitted):** F2
  code is built only if the §5.4 location screen passes. Screen fails ⇒
  REFUTED-P0, recorded, no build. Screen ambiguous on the DO-NOT-REDO
  distinction ⇒ escalate in the handback rather than build (the owner's
  standing structural standard).
- **DOF row:** zero fitted scalars (measured held-by-class series; the
  class-capacity clip is data-vs-data). New boolean
  `ercot_as_held_location` (default False).
- **Coincidences named:** `energy_online_capability_cap` R (ERCOT-155/159)
  and `online_capacity_envelope` R are CAPABILITY-LEVEL objects — F2
  carries no capability level (class capacity enters only as a clip against
  the model's own `pmax·avail`); item 11 / Q-B is per-UNIT — F2 is class
  grain via the existing committed RESTYPE mapping; ercot-219 R is the
  online AGGREGATE — F2 is per-product, per-class, available-basis MW.

### F3 — measured RUC / out-of-market commitment MW [enumerated; expected REFUTED-P0]
- **(a)** IMM 2023 SOM: heavy RUC usage as conservative operations.
- **(b)** Would require a measured 2023 RUC commitment-MW series. **None is
  committed** (`data/raw/ercot/` holds RUC AS-disclosure files for
  2025/2026 only), and the repo carries no RUC-MW mechanism.
- **(c/d) Pre-registered honest analysis:** predicted sign through
  commitment is ~0/NEGATIVE — RUC ADDS supply (suppressing λ; that
  suppression's price correction is the measured RTORDPA overlay, cell
  `ercot_rtordpa_overlay` K, already armed and basis-complete, 2023
  demand-weighted $0.75 vs IMM $0.84), and the model already reproduces
  physical dispatch ±8 % at the target hours, so measured RUC floors would
  barely move dispatch. A "RUC-as-sequestration" reading double-counts the
  rule-19 ownership of the RUC price effect. Verdict expected at Phase-0:
  REFUTED-P0 (sign + rule-19 + data absence), no solve. Re-opening would
  need a data intake the owner has not chartered.

### F4 — operator load-forecast conservatism [enumerated; expected REFUTED-P0]
- **(a)** The operator's conservative demand forecasts drove procurement
  and commitment decisions in 2023.
- **(b)** No measured DA-load-forecast series exists in the repo (verified;
  only actual load series are on disk). Backcast demand is measured actual
  load and MUST remain so (the dispatch being validated serves the real
  load).
- **(c/d) Pre-registered honest analysis:** the admissible entry point for
  forecast conservatism is procurement sizing — but the AS plan
  (ASPLANNP433) IS the operator's realized conservative product, already
  armed as the requirement, so a separate forecast-conservatism factor
  double-counts it (rule 19). The ORDC-side entry (LOLP μ shift) is
  channel-forbidden (§1). Verdict expected at Phase-0: REFUTED-P0
  (no measured driver on disk + no admissible distinct entry point),
  documentation row.

### F5 — pre-reform deployment-design depth beyond the armed representation [measurement row]
The armed representation is already maximal: ECRS_withheld is a single
VOLL step at full requirement width (whole-2023, 2024 h<5088); RRS/RegUp
rigid through RTC+B (2025 h8112); the OBDRR048 multi-step floor is
date-gated at 2023-11-01. Phase-0 documents ALREADY-CARRIED across the full
design-feature list for the record: the LR-RRS (RRS-UFR) measured series
(armed), storage per-product AS awards + SOC-reserve backing (armed;
`ercot_storage_as_duration_gate` default-off is expected inert for the
requirement side because storage AS is measured-credited, not endogenous —
verify and record), online-NSPIN depth (→ F1b), and the release-reform /
RTC+B date gates. No solve; any deeper published design object found here
would be a new factor row for a successor, not a silent arm.

## 3. EXCLUDED-FOR-STRUCTURE (recorded; no probes)

- ORDC X-axis surgery / "ECRS not counted as reserve": NO WINDOW — reality's
  RTORPA ≈ $1 at the target hours (ercot-216 §5); an adder-channel fix is a
  rule-1 violation per §1.
- Aggregate capability reconciliation in any form, incl. on `rtolcap`
  (ercot-219 R, dimensional; DO-NOT-REDO).
- Commitment-state bound to T_tel (B-2: UNSIGNED, DO-NOT-SIGN, pre-measured
  kill).
- IMM-quantification-as-identification (card-W W-3 fence).
- Cross-year memory seed (ercot-222 R).
- `ercot_storage_rt_offer_surface` / measured offer surfaces fed back
  (ercot-162 R; rule 13).
- Mid-band adder legs (ercot-214/215 closed as a solved identification).
- Item 8 (daily gas basis — closed unconditionally, FINDING-ercot224);
  item 11 (Q-B FINAL).
- DAM AS MCPCs as offer or requirement floors: measured PRICE OUTCOME —
  the rule-13 forbidden form.
- Sub-hourly HDL/interval scarcity (17 % of 2023 tail hours clear on a
  minority of 15-minute intervals — adjudicated model-class, invisible to
  an hourly LP; ercot-216 §4).
- ERS (Emergency Response Service): deploys only in EEA; PRC ≥ 4,132 MW at
  every missed hour, 0 hours under EEA-1 — the same no-window measurement.

## 4. COMPLETENESS SWEEP (the owner's comprehensiveness demand)

The table was swept against the 2023 regime's full documented feature
space: AS plan quantities and composition (F1/F1b/F5), award/hold
allocation (F2), the no-release designs per product (armed; F5), RUC/OOM
(F3), operator load-forecast conservatism (F4), the HASL carve (F1/F2),
LR and storage participation (armed; F5), ORDC constants + floor dates
(armed, design-constant; adder channel excluded), outage-approval
conservatism (already embedded in the measured historic outage overlay),
DAM AS prices (excluded, outcome), ERS (excluded, no window), sub-hourly
effects (excluded, model-class). Every feature is live (F1/F1b/F2),
Phase-0-screened (F3/F4), already-carried (F5), or cited-excluded (§3).
The CONDUCT-side successors named in the keeper stamp (second adaptation
pass, cross-year post-Uri memory, seasonal term) are deliberately OUT OF
SCOPE for this quantity/design program — each needs its own identification
card; this program feeds them tightness rather than rebuilding them.

## 5. PRECOMMITTED MEASUREMENTS, KILL PRECONDITIONS AND GATES

### 5.1 The official-basis scorer (`scripts/probes/ercot226_official_score.py`)
Reproduces the registration pipeline's official numbers for an
UNREGISTERED bundle from `<bundle>/hourly/system_<y>.parquet` +
`frontend/data/backcast/bench/ERCOT/<y>.json.gz` +
`frontend/data/backcast/tail/actual_tail.json`, replicating the payload
rounding chain (zonal load-weighted means rounded to 2 dp, demand to 4 dp,
non-leap month edges; C3a vs `rt_lw`; C3b = monthly NRMSE vs `rt_lw_mon`;
C3c = hours max-zonal price > $200 vs `rt_gt`). **VALIDATION GATE:** on the
keeper bundle it must print exactly **−39.7 % / 0.729 / 74 h (2023),
+0.4 % / 0.131 / 22 h (2024), −7.6 % / 0.099 / 1 h (2025)** before any
probe is scored. Q-B/R-A note: 2023 official numbers remain side-effect
reporting at full magnitude — the ADOPTION criteria below are this
program's owner-chartered use of them under W-3/W-4.

### 5.2 The summer-scarcity measurement (per probe)
On 2023: the 181 actual-RT>$200 tail hours' caught/missed/phantom split
(vs 64/117/3 keeper), Δ(model price) distribution at the miss set, window
concentration (share of the total λ·demand improvement inside Jun-10–Sep-30
scarcity-episode hours), the calm-fortnight check (Jun-24–Jul-7 bias,
keeper +15.4 %, must not worsen beyond +2 pp), channel attribution (the
improvement decomposed λ/settle vs model adder from the system sidecar
columns — adder-carried improvement is a FAIL per §1), and
adaptive-expression diagnostics (spike days vs keeper 7, P_hat max,
window-hours floored ≥$1,000, from the adaptive sidecar).

### 5.3 The gate wrapper (`scripts/probes/ercot226_gates.py`)
Imports (never edits) `ercot221_gates` constructions and baselines; adds
`--years`. Gates per probe year: **G-CAP** (λ+adders ≤ VOLL, 0
violations), **G-SHED** (shed set ⊆ {∅, {3067}, ∅}), **G-SPUR banded**
(≤ baseline 9/11/1 + 5) **plus the lidless report-only block** (S_nolid /
S_band / S_top per the ercot-225 card vocabulary; keeper lidless 11·12·1;
the unsigned card's gate files are NOT edited), **G-BAT** (±25 %
EIA-930), **G-D2** (no new D-4 rows). Plus the F1-family diagnostics:
per-withheld-family VOLL-shortfall hours (`shortfall_mw > 0` on a withheld
family = manufactured-shortage signature; must be 0), family dual ≥ VOLL−ε
hours, supply-cap saturation counts (from `reserve_family_<y>.parquet`).

### 5.4 Phase-0 kill preconditions (computed BEFORE any solve; a factor
failing its precondition is REFUTED-P0 — recorded in the JSON, the FINDING
table and the matrix cell, and spends NO solve)
- **F1 kill:** at the keeper miss set (actual RT > 200 & keeper max-zonal
  ≤ 200, from the keeper's committed 2023 sidecar), p50 of
  Σ_{p∈{REGUP,RRS,ECRS}} delta_p < 100 MW ⇒ the depth is not in the
  system-level quantity ⇒ REFUTED-P0.
- **F1 feasibility:** hour-by-hour `margin_fast(t) = (rtolcap −
  LR − storage credits)(t) − Σ_fast req_F1_p(t)`; if any 2023 hour goes
  negative, the cap-clip variant (`ercot_as_held_requirement_capclip`,
  tighten-only, measured-vs-measured) is built and armed WITH F1; else it
  is not built (fewer DOF).
- **F1b materiality:** p50 of max(0, held_NSRS − plan_NSPIN) at the miss
  set < 100 MW ⇒ F1b not probed (recorded).
- **F2 location screen:** the held-by-class series at the miss set must
  show ≥ 500 MW p50 sitting on dispatch-relevant thermal classes
  (gas_cc/coal/gas_st combined) — else the misallocation hypothesis has no
  mass and F2 is REFUTED-P0 without the LP build.
- **F3/F4/F5:** the documentation measurements described in their rows.
(The 100/500 MW thresholds are materiality floors chosen ex ante — small
against the 2.7 GW wedge and the ~5 GW stack — not tuned quantities.)

### 5.5 Single-factor ADOPTION criteria (official basis; W-4 mechanical)
- C3a-2023 improves ≥ **1.5 pp** toward zero vs keeper −39.7 %;
- C3b-2023 ≤ keeper 0.729 + **0.005**;
- improvement window-concentrated (§5.2) and calm-fortnight clean;
- channel attribution clean (no adder-carried improvement; withheld-family
  VOLL-shortfall engagement = 0 hours);
- G-CAP / G-SHED / G-BAT / G-D2 clean; G-SPUR banded within bar (lidless
  reported both forms);
- C8/D-2 forced-share clean and no new D-4 rows (legitimacy diagnostics).

### 5.6 COMBINED-RUN acceptance gates
All §5.5 criteria on 2023 for the combined arm; combined C3a-2023 ≥ best
adopted single factor − 0.2 pp (destructive interaction ⇒ drop-one until
clean, every drop recorded); G-OWNER retention (official C3a/C3b 2024 and
2025 all remain PASS); the §5.7 invariance test.

### 5.7 The 2024/2025 invariance test
Primary: sha256 identity of the combined bundle's
`hourly/*_{2024,2025}.parquet` against the keeper's committed sidecars —
expected exactly, because every armed factor's driver series is
identically zero in 2024/2025 (data-keyed absence). Fallback (env drift):
the official scorer reproduces +0.4 / 0.131 / 22 and −7.6 / 0.099 / 1 to
the printed digit and the gate table is clean. Any drift beyond that must
be strictly non-degrading AND attributed to a data-keyed driver measurably
nonzero in that year (the owner's pre-reform-2024-H1 clause) — else the
factor responsible is dropped from the combined config.

### 5.8 Promotion rule (W-4)
If the combined 3-year bundle clears §5.6–5.7, it is registered and
PROMOTED to keeper this session (the determination will remain NOT-YET
while C3a-2023 is out of band — the ercot-221/223 promotion precedent:
most-structurally-faithful run, verdicts recorded unrewritten). If NO
factor clears §5.5, there is no combined run and the handback names each
factor's failed gate verbatim. Borderline mechanical verdicts escalate in
the handback per the owner's standing structural standard — never
self-rejected, never silently promoted.

### 5.9 The probe JSON schema (every probe, spoke or hub, commits exactly one)
`results/calibration/ercot226_probe_<factor>.json`:
`{probe, factor, charter, session (hub|spoke), branch_sha, env {python,
highspy, numpy, scipy, pandas, pyarrow}, control {out_dir, grepro
{sha_match_per_file, official_reproduction}}, arm {out_dir, set_flags},
official {c3a_2023, c3b_2023, c3c_2023}, probe_basis {c3a, c3b, tail},
gates {gcap, gshed, gspur_banded, gspur_lidless {s_nolid, s_band, s_top},
gbat, gd2}, family_diagnostics {withheld_shortfall_hours, dual_voll_hours,
cap_saturation_hours}, summer {caught, missed, phantom,
window_concentration, calm_fortnight_bias, channel_attribution},
adaptive {spike_days, p_hat_max, floored_hours_ge_1000},
verdict {adoption_pass, failed_criteria[]}}`.

## 6. EXECUTION PROTOCOL (hub-and-spokes, per the owner's parallel-session
instruction)

- **Hub = this session (ercot-226).** Owns: this precommit; the C1 derive
  (committed parquets); the C2 scorers + Phase-0 JSON; the C3 mechanism
  code, fields, cache-key/defaults registrations, matrix rows, tests; the
  spoke prompts; its own control replay; any un-farmed probes (spokes are
  an accelerator, not a dependency); ALL verdicts; the combined run and
  3-year chain; registration; the FINDING; the calibration-log entry
  (ercot-226; next shorthand ercot-227; ercot-199 remains unclaimed); ALL
  matrix cell stamps (centralized in the hub to avoid concurrent shard
  edits — a recorded deviation from rule 28(b)'s same-session-stamps under
  the owner's parallelization instruction; every spoke verdict is stamped
  by the hub same-day from the committed spoke JSON); the promotion.
- **Spokes (one per surviving live factor).** Each: fresh session on THIS
  branch at/after the C3 sha; env per §0b-3; its OWN control replay
  (G-REPRO on its own box — sha256 vs the keeper's committed 2023
  sidecars + §5.1 scorer reproduction; a non-reproducing box STOPS and
  commits the failure record, because an A/B off a non-reproducing box is
  meaningless); ONE arm with its single `--set`; §5.1–5.3 scoring; commits
  ONLY its own probe JSON (distinct path ⇒ clean `git pull --rebase`);
  reports the verdict. Spokes consume NO calibration-log shorthand, never
  register on the dashboard, never edit core files, the matrix, or the
  keeper, never touch other years or other factors.
- **Solve discipline:** every solve in a Claude session (never CI); one
  solve at a time per box (ERCOT per-plant ≈ 12.7 GB peak on 15 GB);
  cross-session parallelism is rule-12-sound because each remote session
  is its own container.
- **W-2:** probes are NOT dashboard-registered; the committed probe JSONs +
  the FINDING probe table are their record. Only the final combined 3-year
  bundle is registered (rule 15 in full: bundle + sidecar + payload +
  bench + hourly sidecars).

## 7. THE 2022 DUAL-CONFIG STANDING PROTOCOL (record only — NOT executed;
ERCOT holds no `complete` marker and 2022 stays untouched)

When the 2022 validation touchpoint is authorized, 2022 is scored under
BOTH the 2023 regime config and the 2024–2025 keeper config; whichever
clears calibration becomes the config for the remaining holdout years,
while 2023 itself remains tested single-year under its own regime config.
ECRS-keyed factors are naturally zero in 2022 (no ECRS before 2023-06-10),
so the comparison isolates the non-ECRS conservatism factors (the RRS/RegUp
held-depth and held-location legs, whose 2022 driver would come from a 2022
NP3-965 intake). This paragraph is copied into the FINDING, the
calibration-log entry, and the keeper notes at promotion.

## 8. PRIORS (pre-registered expected branches, ercot-225 style)

- P-1: F1's system-level delta at the miss hours is SMALL (held ≈ plan) —
  the likelier branch on the record; F1 then REFUTES-P0 and the program's
  weight moves to F2. If instead delta is material, F1's probe moves C3a by
  well under the 24 pp depth (energy-displacement through a still-fat
  stack), and its value is partly through adaptive re-expression.
- P-2: F2's location screen PASSES (the 5.1 GW August stack must have sat
  substantially on online CC/coal — that is what an HASL carve is), and
  F2 is the program's largest single mover. Confidence moderate; the
  ercot-220 L5 bound does NOT cap F2 (it bounds margin→ORDC channels, not
  merit-order displacement).
- P-3: F3 and F4 REFUTE-P0 as written in their rows.
- P-4: no probe manufactures withheld-family VOLL shortfall (feasibility
  margins stay positive; reality held these MW, and the armed supply cap
  is the same telemetry's capability).
- P-5: the combined arm's 2024/2025 sidecars are sha-identical to the
  keeper's (the data-keyed zeros), making §5.7's primary branch the
  operative one.
- P-6: even the full program leaves C3a-2023 short of −10 % (the conduct
  depth ceiling stands); the deliverable is the most structurally faithful
  ERCOT design bundle plus a measured statement of how much of the wedge
  was allocation, not a PASS claim.
