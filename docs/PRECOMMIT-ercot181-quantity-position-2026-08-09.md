# PRECOMMIT — ercot-181: THE QUANTITY-POSITION LANE (`ercot_offer_surface_position_tail`)

**Session ercot-181, 2026-08-09. Pushed BEFORE any corpus measurement, any
derive, any build, and any solve.** Charter:
`results/calibration/FINDING-ercot180-topscoped-exhausted-2026-08-08.md` §4/§5
(matrix §5.1 item 22's `==>` clause) — reality's marginal price forms at a
POSITION far up a cliff-shaped submitted curve (q_act p50 0.9976 of the
marginal resource's own curve; actual RT inside the position band
[curve@q_mod, curve@q_act] in 94/100 top-gap hours), which no LEVEL statistic
of any conditional ladder can see. This session mints §5.1 item 23.

Object: **C3a-2023** (−32.4 % on keeper
`2026-08-07-run176-control-offline-increment`, NOT-YET, fail set {C3a, C3b});
owner standing instruction 2026-08-07: under 10 % **without disturbing
2024/2025** (both PASS C3a; 2025 at −9.1 %). C3b-2024 (0.205) is a DIFFERENT
root (frozen ceiling lane, memo PENDING) and is NOT entered.

**The honest framing is fixed up front.** The conditioning-grain family is
CLOSED (form (a) `R` on reach, form (b) `R` on identification; §5.1 items
21–22) and its offer-formation budget (~$2.6/MWh, ercot-178 P-3) is
unreachable by level statistics. The position lane's admissible mechanism
space is NARROW, and this precommit pre-registers the honest terminus as a
first-class outcome: **if no rule-13-admissible form survives the §5
adjudication, the lane is FILED-REFUSED and the deliverable is the escalation
to an owner sitting on C3a-2023 reachability within this model class (the
C3c-caveat path).** No mechanism is stretched, no scalar invented, to reach
−10 % (rule 1 [R-STRUCT], rule 23 [R-DOF]).

Everything below — instrument, mechanism-form election and refusals, the
inertness decision tree, guards, kill gates, and predictions — is fixed HERE
and is not renegotiated after any measurement or solve.

---

## 0. The rule-28(a) DO-NOT-REDO check (run FIRST, completed before this push)

* **No ERCOT cell adjudicates a quantity-position mechanism.** The matrix
  column was searched (`position`/`marginal`/`tail`): no row exists; item 22's
  `==>` clause charters exactly this lane as its named successor.
* **The conditioning-grain family is NOT re-opened.** Both forms are `R`
  (items 21–22) and stay closed; the only admissible grain re-open is a new
  precommit on a full-year 2024/2025 NP3-965 intake (the standing DATA
  BLOCKER), which this session does not touch. The distinction is structural,
  stated ex ante: the grain family conditioned the **HOUR axis** (which hours
  read which ladder — ercot-180's KS instrument adjudicated hour-rank
  sub-population breaks); this lane addresses the **POSITION axis** (where on
  the measured within-curve distribution a row's bid is read). The frozen
  netload-bin edges, all conditioners, and every hour-axis statistic are
  inherited byte-identical.
* Lanes NOT entered (all closed, carried verbatim from PRECOMMIT-ercot180 §0):
  ORDC/RTORPA/RTORDPA (closed vs ERCOT's own published adders — no `ordc_*`
  touch), reserve LEVEL (triple-corroborated), temp-derate (`R`),
  offline-increment slow-start tier (`I`), event-cap ceiling (FROZEN, memo
  PENDING), blanket `min()` (`R`), unit-scoped (`R`) — **binding here: no
  per-unit row representation is built**, 2023 depth premise (REFUTED),
  reserve-side family (CLOSED), ramp mechanisms (`R`) — **binding here: the
  intra-hour ramp friction that CAUSES the position wedge is not modeled as a
  constraint**, storage RT surface (`R`), `energy_online_capability_cap`
  (`R`), CC-headroom crosswalk (FILED-UNLICENSED), ALL coal offer lanes
  (CLOSED), per-year CT re-identification (REFUSED), West/Panhandle (CLOSED),
  ercot-172's C3 (REFUSED), every capability/availability face (closed on
  measurement), ERCOT-151 §0.2 (REFUTED). **Load shed as a pricing channel is
  the twice-rejected ercot-48/49 signature and the position lane is MORE
  exposed to it than grain was — G-SHED is PRIMARY (§7).**

## 1. The marginal-identification INSTRUMENT — fixed BEFORE looking at the corpus

The ercot-180 §4 proxy (max price-at-BP over ON gas resources) is an UPPER
ENVELOPE (p50 = the $5,000 HCAP wall vs actual RT p50 $1,032; share-of-gap
saturates > 1). Its replacement is fixed here, ex ante, per the charter's
named candidate:

**I-1 — interior price-at-BP clustering.** In an SCED-cleared market, a
resource dispatched strictly inside both its ramp-feasible envelope and its
own submitted curve has its offer price at Base Point equal to the system
lambda (SCED optimality; step granularity brackets it). Per 5-minute interval:

* **Population (residual-blind):** the 2023 hours whose within-year net-load
  rank exceeds 0.97 (the frozen top bin — 263 hours; net load = EIA-930
  demand − wind − solar, the artifacts' own conditioner; hour-of-year clock
  and gas-day normalization = the ercot-180 probe's, reused unchanged).
  Corpus: delivery-2023 NP3-965 (`data/raw/ercot/SCED/`, 315 shards,
  full-year, 7,917 hour-nodes). 2024/2025 sample-day corpora place nothing.
* **Interior resource:** ON-status merchant gas (`CLASS_OF_RESTYPE` classes
  CC/CT, the wall derive's own scope), with **LDL < BP < HDL** (strictly
  inside the ramp-feasible envelope: BP = HDL is ramp-pinned-up, its curve
  price at BP < λ; BP = LDL is pinned-down, price ≥ λ) **and** first-SCED2-
  step MW < BP < min(top-step MW, HASL) (strictly inside its own curve, away
  from both ends). Strict inequalities, no epsilon margin — SCED writes
  BP = HDL exactly when pinned, so strictness is the test.
* **Estimator:** per interval, λ̂ = the MEDIAN of interior resources'
  HCAP-clipped SCED2 step price at BP; dispersion = IQR. Per hour,
  λ̂_hour = median of the hour's interval λ̂ values.
* **Admissibility bars (instrument constants, fixed here, never swept):**
  * **I-B1 coverage:** ≥ 60 % of the population's intervals carry ≥ 3
    interior resources.
  * **I-B2 tightness:** median over covered intervals of IQR/λ̂ ≤ 0.25.
  * **I-B3 validation** *(diagnostic leg — realized prices admissible ONLY
    here, explicitly labelled)*: median over covered hours of
    |λ̂_hour − RT_actual| / RT_actual ≤ 0.25 against the committed
    `actual_lmp_hourly_ERCOT.parquet` hourly RT.
  If any bar fails, the sharper instrument is REFUSED-AS-MEASURED, reported
  at full magnitude; the ercot-180 envelope + containment statistic remain
  the lane's only sizing. The §5 mechanism adjudication proceeds either way —
  by construction it consumes NO instrument output.
* **I-2 — the honest re-sizing** *(diagnostic license: reads the control
  residual for hour selection, the DIAGNOSIS-ercot177 class; output BARRED
  from parameter identification)*: re-run the ercot-180 top-100 position
  statistics with the marginal resource = the interior resource whose
  price-at-BP is nearest λ̂ (replacing the envelope argmax): sharpened q_act,
  the marginal class mode, and a non-saturating share-of-gap. Same top-100
  hours (the committed JSON's), so the two instruments are directly compared.
* **I-3 — the wedge quantified from the corpus side** (same license): per
  covered interval, the distribution over ON merchant-gas resources of
  BP / curve-top MW (how loaded the real fleet runs), and the total MW of
  SCED2 curve segments priced BELOW λ̂ yet undispatched (BP below the
  segment) — the measured cheap-but-unaccepted mass the LP's frictionless
  substitution clears and reality's 5-minute ramp-feasible SCED does not.
  This is the quantity-position wedge measured directly, sizing the owner
  sitting whatever the §5 outcome.
* **Rule-13 boundary, restated:** I-1's BP inputs are realized dispatch
  outcomes → the instrument is DIAGNOSTIC in its entirety. NOTHING in §2–§5
  consumes λ̂, q_act, BP, or any I-1/I-2/I-3 output. Mechanism inputs are
  submitted conduct only.
* Probe: `scripts/probes/ercot181_interior_lambda.py`; committed record:
  `results/calibration/ercot181_interior_lambda.json`.

## 2. The mechanism-form election — one candidate, three ex-ante refusals

The model-side geometry was read from HEAD before this precommit (code study
only — no corpus read, no compose executed): the three armed priced members
share one truncation. The wall (CC/CT econ rows) and the pool (merchant-CT
top-sliver rows) read their measured ladders by within-plant position —
`rel = (share_g − boundary)/(1 − boundary)`, `np.interp(rel, ladder_q,
ladder(bin))` — and the conditional (peak rungs) reads rung-indexed quantile
statistics. All three ladders stop at **p90** (`LADDER_QUANTILES =
(0.1, 0.3, 0.5, 0.7, 0.9)`; `PEAK_LADDER_QUANTILES` likewise), and `np.interp`
END-CLAMPS: every row whose position exceeds 0.9 reads the p90 rung. **The
measured populations' top decile — where the cliff face lives (2023 top bin:
CC wall p90 = 202× delivered gas ≈ $526, rising to HCAP; CT 596×; pool CT
570×) — maps to NO model row's bid at ANY position.** Reality's 2023
top-hour energy price ($1,889.63 SCED system lambda ≈ 727× gas) sits inside
exactly that truncated decile.

**Form α — ELECTED: the position-tail completion
(`ercot_offer_surface_position_tail`).** Complete each armed rel-interpolated
ladder's position axis above its frozen p90 point with THE SAME STATISTIC on
its own measured support: the MW-weighted empirical quantile function of the
same population (wall: ON-spare BP→HASL SCED2 segments; pool: offline
above-LSL startable segments), i.e. every distinct (cumulative-MW-fraction,
multiplier) step point above 0.9, HCAP-clipped exactly as the parent derives
clip, per class-year-bin. Rows read at their own already-defined `rel` —
the members' own position mapping, unchanged. Zero fitted scalars: no new
quantile grid is chosen (the support is the distribution's own), no
level/statistic/conditioner/clamp changes, at-and-below p90 every ladder
point is byte-identical to the frozen artifacts, and `np.interp` below 0.9 is
unaffected by appended points (the sub-p90 read is byte-identical by
arithmetic, asserted as SP-α1). **Scope: the wall and pool members only** —
the two that possess a position axis. Zero-support rule (forced, not
chosen): a class-year-bin whose measured population above p90 is empty keeps
its frozen 5-point ladder byte-identical (today's clamp behavior); never a
cross-year borrow, never a synthetic point. **Forward story (rule 13):** a
forward year ranks its own net load, maps its own rows by its own boundaries,
and reads conditional submitted-offer conduct at its own position — the
completed tail regenerates from the same derive on any year's corpus and
responds to changed conduct. The composition (additive `mc_bid_adjust`,
`max(0, target − mc)`, 0.95 × VOLL cap, pool replace-by-mask, P1-only seam)
is byte-unchanged.

**Refused ex ante (never built, whatever the measurements say):**

* **Form β — comonotone (own-position) re-aggregation** (replace pooled-rung
  quantiles with the vertical statistic P_i(q) at common own-curve position
  q): at the model's clearing positions the real curves read their
  cheap-to-negative bodies (the ercot-180 containment: curve@q_mod p50 =
  −$50), so the form either marks the armed surfaces DOWN in the object hours
  (anti-object, and a markdown of keeper mechanisms — the form-(a)
  body-repricing channel re-imported) or is clamped inert. Refused.
* **Form γ — reading the curve at reality's position** (q_act, BP, λ̂, or any
  outcome-derived position as a mechanism input): a pin to the measured
  outcome with no forward analogue — rule 13's exact forbidden class.
  Refused.
* **Form δ — modeling the acceptance friction** (intra-hour ramp
  feasibility, deliverability, unit-scoped rows, or capability motion to
  push the model's clearing position up the curve): every face is
  adjudicated — ramp `R`, unit-scoped `R`, offered-vs-deliverable
  FILED-REDIRECTED, capability/availability closed on measurement,
  reserve level closed. Refused under rule 28(a).
* **The conditional (peak-rung) member is NOT extended**, stated with
  reason: its rows are rung-indexed with no position axis; resolving its top
  rung's within-slice cliff requires new rows, and row-count changes move
  P0 (baked heights enter the base fleet) — breaching the family's P1-only
  seam. Its p90-truncated top rung is disclosed as a REMAINING known
  limitation in the finding, not silently absorbed.

## 3. The mechanism as built (ONLY if §5 route B is reached)

`ScenarioConfig.ercot_offer_surface_position_tail: bool = False`. ERCOT-only
(rule 25). Default off. Matrix row in the same PR as the field (rule 28(c)).
Cache-key registered dropped-at-default in BOTH registries in the same commit
(the nyiso-119 discipline); the pinned default key must not move.

* **Artifacts:** two `*_positiontail.json` vintages
  (`ercot_sced_offer_wall_positiontail.json`,
  `ercot_faststart_pool_positiontail.json`) in
  `data/raw/_validation-source/`, derived by new `--position-tail` modes on
  the two existing derives. The frozen `_condbinned.json` and `_contpct.json`
  artifacts are byte-untouched (SP-α5).
* **Vintage tag:** `_provenance.conditioning = "positiontail-netload-bins"`,
  guarded in BOTH directions (the ercot-178/180 pattern): the new gate
  refuses stepped/contpct/topscoped artifacts; every other path refuses
  positiontail artifacts.
* **Mutual exclusion:** arming with either grain gate
  (`ercot_offer_surface_continuous`, `ercot_offer_surface_top_scoped`) is a
  hard error; the form-(a) compat guard (min_bin ≠ 0, unmigrated members) is
  SHARED, not weakened.
* **Read path:** the armed branch replaces the two members' fixed
  `(ladder_q, ladder)` pairs with each bin's own extended
  (x, value) vectors — same `np.interp`, same callers, no new solve-side
  machinery. `ercot_offer_surface_netload_pcts` is consulted exactly as the
  stepped path consults it (frozen bins).

## 4. Rule-19 reconciliation (one owner per row, unchanged) + the carried rule-18 defect

Ownership moves NOWHERE: CC/CT econ rows stay the wall's (the completion
refines the wall's own read above rel 0.9); pool row-hours stay the pool's
(replace-by-mask unchanged); peak rungs stay the conditional's (untouched);
ST_GAS stays out of scope (the steam leg is unarmed in the keeper and this
lane adds no class scope); committed/mustrun rows stay the bridge/floor
structure's. D-2/D-4 exposure is vacuous by construction — the mechanism
prices bids, touches no bound, forces no MW. **The rule-18 grain defect is
CARRIED, NOT TOUCHED** (owner item, not authorized here): econ*/peak*
tranche rows read `min_down = min_run = 0`, making the fast-start pool's
physics gate vacuous at the row grain — enumerated per the handoff, fix
requires its own pre-registered round.

## 5. The adjudication — a pre-registered decision tree, decided in order

**Step M-0 (build-free geometric identification — the ercot-180
died-at-identification pattern).** From the keeper control bundle state
(`reconstruct_bundle_fleet`, the ercot-178 probe's `_compose` mirror — SP-2
sha-matched to the registered control) and the FROZEN artifacts only — no
corpus read, no new artifact, no ScenarioConfig field:

1. Reproduce the two members' row geometry exactly (within-plant midpoints,
   per-bin boundaries, rel); **validate** by reproducing the composed
   gate-off markup byte-identically from (rel, ladder, gas, caps) for every
   priced row (a probe-vs-builder mismatch is stop-the-line).
2. Enumerate every (row, hour) with **rel > 0.9** under its hour's bin —
   the ONLY row-hours form α can change (`np.interp` sub-p90 invariance).
3. **M-1, the inertness criterion (fixed here):** form α is **PROVABLY
   INERT** iff for EVERY such row-hour in EVERY year 2023/2024/2025,
   `mc_base + composed_markup` (the control P1 bid EXCLUDING startup
   amortization — a LOWER bound on the true P1 bid, which is the
   conservative side: a lower bound above price proves the true bid above
   price) exceeds the control bundle's zonal price for the row's zone by
   more than $1 (the degeneracy margin; a row within $1 counts LIVE, forcing
   the honest build). An LP variable at bound with strictly positive reduced
   cost keeps the identical primal solution and duals when its cost rises —
   raising strictly-undispatched rows' bids cannot move any price.
4. **Route A — provably inert:** form α is refused as UNREACHABLE (no
   admissible form remains: α inert, β/γ/δ refused ex ante) → **the lane is
   FILED-REFUSED. NO field, NO derive, NO artifact, NO solve, NO run
   registered** (this clause pre-registers the absent registrations, the
   ercot-176/180 precedent). The finding escalates to an owner sitting on
   C3a-2023 reachability within this model class (the C3c-caveat path),
   sized by §1's I-2/I-3.
5. **Route B — live anywhere** (≥ 1 changed row-hour at/below price + $1 in
   any year): the mechanism is BUILT per §3, seam-proved per §6, and ONE A/B
   pair is solved per §9, adjudicated on §7's gates. No magnitude screen is
   applied at this step — a live structural completion is solved however
   small its expected movement (rule 1).
* Probe: `scripts/probes/ercot181_positiontail_reach.py`; committed record:
  `results/calibration/ercot181_positiontail_reach.json` (per-year changed
  row-hour counts, the bid-vs-price margins, the M-1 verdict, and the top-bin
  hour overlap with the object).
* **Ordering:** M-0 runs BEFORE §1's corpus probe (it reads no corpus and no
  residual-selected hours; its inputs are the frozen artifacts + the control
  bundle). §1 runs after, whatever M-1 says — the sitting needs its sizing.
  Neither step's output revises the other's constants.

## 6. Seam proofs (Route B only — run and committed BEFORE any solve)

Probe `scripts/probes/ercot181_positiontail_seamproof.py`; record
`results/calibration/ercot181_positiontail_seamproof.json`. Any assertion
failing STOPS the session.

* **SP-α1 (the core):** gate ON with the real positiontail artifacts: every
  row-hour with rel ≤ 0.9 composes BYTE-IDENTICAL `mc_bid_adjust` (and pool
  `own_mask`) to the gate-off control, all three years; the arm differs
  somewhere above rel 0.9 in 2023 (else Route A applied — asserted).
* **SP-α2 (null encoding):** positiontail artifacts whose tail points all
  carry the parent p90 value compose byte-identical to control EVERYWHERE —
  the appended axis is POSITION, never level.
* **SP-α3:** gate OFF at HEAD: composed sha identical to the recorded
  ercot-178/180 control sha (2023). **SP-α4:** non-ERCOT ISOs return None.
* **SP-α5:** the frozen stepped + contpct + topscoped artifacts byte-identical
  to HEAD after the derives run.
* **SP-α6:** no-markdown (markup ≥ 0; arm bid ≥ control bid on every row-hour;
  0.95 × VOLL cap holds), and monotone tails (each extended ladder
  non-decreasing in x).
* **SP-α7:** guard integrity — every forbidden combination raises (each grain
  gate × this gate; this gate × stepped/contpct/topscoped artifact; legacy
  path × positiontail artifact; min_bin ≠ 0; each unmigrated member).
  `check_mechanism_matrix.py` exit 0 with the new row.
* **SP-α8:** artifact conformance — sub-p90 points byte-equal the frozen
  ladders; tail x strictly increasing in (0.9, 1]; values HCAP-clipped;
  vintage tag correct; per class-year-bin tail support counts disclosed
  (the 2024/2025 sample-day disclosure duty).

## 7. Kill gates — inherited from PRECOMMIT-ercot180 §6 VERBATIM (Route B only)

* **G-SHED — PRIMARY FALSIFIER: no year's shed count may rise** above its
  control count (control at last scoring: 2023 = 4, 2024 = 2, 2025 = 0;
  re-read from this session's fresh control at scoring). A 2023 C3a gain
  bought by shedding is a REJECT however small — the ercot-48/49
  manufactured-shortage signature, twice-rejected; the position lane's
  cliff-top repricing is MORE exposed to it than grain was. If the tail
  completion manufactures shed, the form is REJECTED and the lane reports
  CLOSED at the measured geometry.
* **G-OWNER (hard, owner):** 2024 keeps its C3a PASS; 2025's C3a not beyond
  −9.1 %; no class's annual energy moves > 0.5 % in 2024 or 2025.
* **G-BIT — declared N/A with reason (the ercot-180 pattern):** the tail
  artifacts are populated per-year, so no year is expected byte-identical;
  replaced by **G-SPAN′** (2023 is the object; out-of-object years must not
  degrade; tail-count and shed clauses for all three years).
* **G-SPUR:** spurious mid-band tail hours must not increase in ANY year —
  the completion's named two-sided risk: repricing already-high hours
  further up (overshoot) while the object hours stand still.
* **G-C3c:** 61/181, 25/53, 3/31 must not degrade.
* **G-COAL148:** coal above the measured-window ceiling ≤ +0.5 TWh any year.
* **G-DOF:** zero new fitted scalars; the DOF ledger's `n_residual` does not
  grow (expected: zero new entries of any kind).
* **G-D2:** no class's forced share crosses its rule-20 cap (expected
  vacuous — no bound is touched).
* **Rule 22 LOYO** before any promotion; no `calibration-complete.json`
  re-key (ERCOT holds no marker).

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported and registered anyway
(rules 15/16). The gates are not renegotiated after the solve.**

## 8. Predictions — adjudicated at full magnitude whatever they read

* **P-1 (instrument):** I-1 passes its bars — interior price-at-BP
  concentrates at λ (that is SCED's own optimality) — and I-2 de-saturates
  the share-of-gap into a finite band with sharpened q_act still far above
  q_mod. If instead the clustering is loose or biased (I-B2/I-B3 fail), the
  envelope stands and the refusal is reported at full magnitude.
* **P-2 (THE CENTRAL PREDICTION — the geometric expectation, stated before
  any compose):** the model's marginal rows in the object hours read the
  p50–p70 region of the measured ladders (control prices $100–360 ≈
  multipliers 40–140 vs p90 rungs 202–596×), BELOW every truncation; rows
  with rel > 0.9 are confined to the thin pool top-sliver and at most the
  topmost econ rows, whose control bids ($500–1,550+) sit far above control
  prices in the very hours C3a-2023 needs moved. **The likeliest M-1 verdict
  is PROVABLY INERT → Route A → FILED-REFUSED.** The lane's value is then
  the honest terminus: the measured statement that the C3a-2023 tail is a
  quantity-position phenomenon an hourly class-aggregate LP cannot price
  without either quantity motion (faces closed on measurement) or an outcome
  pin (rule-13 forbidden) — escalated to the owner sitting with I-2/I-3
  sizing.
* **P-3 (if Route B):** C3a-2023 movement ≤ ~+$2/MWh and plausibly ≪ $1 —
  the bar (+$14.44) is NOT expected to be approached; movement concentrates
  in hours the model already prices near the p90 rungs (its 16–22 > $1,000
  hours), the G-SPUR overshoot face, not the $100–360 formation hours that
  own the gap.
* **P-4 (if Route B, shed):** tail reads approach the 0.95 × VOLL cap on the
  topmost rows; any hour whose residual demand pushes into them sheds at
  $5,000. If shed rises anywhere, G-SHED fires and the form dies on its
  primary falsifier — pre-accepted.
* **P-5 (if Route B, out-of-object years):** movement confined to their own
  above-p90-rel row-hours; class energy within the 0.5 % cap; C3b-2024
  within noise of 0.205. Violations fire G-OWNER/G-SPAN′.
* **P-6 (D-2/D-4):** vacuous — no bound touched; a non-zero D-2 attribution
  to this mechanism is a stop-the-line implementation error.
* **P-7 (the wedge stands):** I-3 measures a material cheap-but-unaccepted
  MW mass below λ̂ in the object hours (reality's friction the LP lacks) —
  the quantity-position wedge confirmed from the corpus side, independent of
  every model artifact. If instead I-3 finds ≈ 0 unaccepted mass below λ̂,
  the position lane's premise is REFUTED outright and the C3a-2023 residual
  returns to the owner sitting with THAT measurement — either way the
  sitting is sized.

## 9. The LP pair, registration, retention (Route B only)

ONE pair via `scripts/replay_keeper.py results/calibration/ercot176_control_A`,
`--years 2023 2024 2025` in ONE invocation each, control and arm STRICTLY
SEQUENTIAL (rule-12 memory cap, measured: two ERCOT per-plant solves OOM a
15 GB box; ~6.6 GB RSS, ~20 min/year each), SAME HEAD, no rebase between
solves, clean partitions regenerated first:

* **CONTROL** — zero deltas, `--out-dir results/calibration/ercot181_control_A`.
  Expected array-equal to the ercot-178/180-verified keeper prices (the
  keeper's next consecutive reproduction); asserted at scoring.
* **ARM** — single delta `ercot_offer_surface_position_tail=true`,
  `--out-dir results/calibration/ercot181_positiontail_B`.
* `legitimacy_diagnostics.json` + `calibration_attestation.json` BEFORE
  scoring (`scripts/calibration_verdict.py --run-id`). BOTH runs registered
  whatever the outcome (rules 15/16), each with all three years (rule 16).
* **Retention intent (stated now):** ERCOT sits at the 15-run cap; this pair
  evicts `2026-08-04-159-control-zerodelta` and
  `2026-08-04-159-energy-capability-cap` (the two oldest). **Route A
  registers nothing and evicts nothing** — pre-stated so the absence is
  never read as a skipped rule-15 duty.
* Promotion only if every §7 gate passes AND LOYO clears: re-key
  `keepers/ERCOT.json`, `build_status.py --iso ERCOT`,
  `calibration-keeper-auditor --iso ERCOT`.

## 10. Governance

* **Rule 22:** every tool invocation stays inside {2023, 2024, 2025}; the
  instrument reads delivery-2023 only; no out-of-training year is solved,
  scored, read, or registered.
* **Rule 23:** the frozen stepped/contpct/topscoped artifacts are never
  re-derived; Route B's positiontail artifacts are a NEW VINTAGE for a NEW
  pre-registered gate (identical statistics, the position axis completed on
  its own support — the ercot-178/180 admissible-vintage precedent); the
  trigger is the ercot-180 §5 structural charter, never a residual sweep.
  Zero fitted scalars in every route.
* **Rule 24:** at most ONE new ScenarioConfig field (Route B only), in
  `run_config.json`, cache-key registered dropped-at-default. Route A adds
  NO field. No env-var knob, no fallback literal.
* **Rule 25:** ERCOT-gated everywhere; no other ISO's files, bundles, or
  matrix column touched.
* **Rule 26:** nothing deleted, nothing zeroed; the stepped form remains the
  default; grain scaffolding stays merged default-off.
* **Rule 27:** `offer_surfaces.py`, `scenarios.py`, the two derives are
  ≥300-line files — edited locally, pushed as exact on-disk bytes,
  blob-verified against the REMOTE on both transports; run payloads and the
  matrix/log files go over `git push` (pack-size rule; `push_files` cannot
  carry them).
* **Rule 28:** duty (a) §0 preceded this push; duty (b) the
  cell verdict + citation lands in-session, refusal included; duty (c) any
  new field's matrix row lands in the SAME PR; duty (d) no cross-ISO verdict
  minted. §5.1 gains item 23.
* **GitHub Actions:** nothing offloaded; every probe, derive, solve, score
  and registration runs in-session (private repo, billed minutes).

---

**Adjudication order: §0 (done) → push this precommit → M-0/M-1 (§5) → §1
instrument → Route A finding OR Route B build/prove/solve → bookkeeping.
Next shorthand: ercot-182.**
