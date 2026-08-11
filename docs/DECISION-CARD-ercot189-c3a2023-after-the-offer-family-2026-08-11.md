> Status: ACTIVE (awaiting owner signature on card Q; the measurement sections are RECORD)

# DECISION CARD — ercot-189: "How have we still seen no improvement?" — C3a-2023 after the offer family

**For the owner sitting. Session ercot-189, 2026-08-11, HEAD `f6381c5`. NOTHING IS
DECIDED HERE.** No lever was proposed, no `ScenarioConfig` field added, no derive run, no
LP solved, no run registered, no matrix cell minted, and the ERCOT keeper is untouched.
This session performed exactly ONE new measurement — a **read-only counterfactual
re-scoring** of the keeper's committed hourly sidecars against the committed actuals,
using the rubric's own scorer (`scripts/probes/ercot189_c3a_c3c_overlap.py`, output
`results/calibration/ercot189_c3a_c3c_overlap.json`). Actuals enter only counterfactual
*scoring*, never any model input (rule 13 `[R-MEASURED]` clean). Every other number below
is read off committed artifacts.

Scope: ERCOT only (rule 25 `[R-ISO-SCOPE]`). ERCOT holds **no `complete` and no `final`
marker**, so every year referenced is inside {2023, 2024, 2025} (rule 22 `[R-HOLDOUT]`).

**Keeper at assembly:** `2026-08-11-run188-arm-topfine-cliff` — determination **NOT-YET**,
fail set **{C3a-2023, C3b-2023}**, C3c a ledgered CAVEAT (`ACCEPTED MODEL-CLASS
LIMITATION`) in all three years at 58/181, 23/53, 3/31 — one entry, the single
per-criterion ledgerable slot.

**Why now.** The owner asked, verbatim: *"How have we still seen no improvement?"* The
offer family is measured shut (items 21–23, 26), the (c2) lane the owner authorized at
ercot-182 ran to its own measured refusal and was built anyway (E2) with a sign-flip
result, and signature A1 has just opened the only remaining named object's prerequisite.
Since ercot-185 cleared C3b-2024, the 2023 price object is **the entire distance** between
NOT-YET and ERCOT's ceiling — so before the program spends on the last untried face, the
owner is owed a quantified answer to what C3a-2023 actually *is*, and a fairly-argued
option to stop.

---

## 0. THE BOARD

| card | decision | blocking? | recommendation |
|---|---|---|---|
| **Q** | What does the program do about C3a-2023 after the offer family — continue behind A1, stop, or checkpoint? | blocks all further ERCOT C3a-2023 spend | **(Q-C) checkpoint behind A1, decision rule tilted to STOP** |

One signable card. Sections 1–3 and 5 are its evidence; section 4 is the card.

---

## 1. WHY NO IMPROVEMENT — the answer to the owner's question

> **THE QUESTION: "How have we still seen no improvement?"**

Because every admissible lever tested worked a channel whose *measured* total budget is
about a fifth of the bar, while two-thirds of the miss sits in 181 hours whose price is
equilibrium conduct the accepted C3c entry already declares un-formable by a
competitive-offer LP — and the only face that could move it (quantity/capability) has
been killed twice at aggregate grain and is unlicensed at unit grain. In detail:

### 1.1 The lever ledger, at full magnitude

The record's own count at ercot-182 was *"**fourteen** levers inside the class failed"*
(card §10 D1, 2026-08-09 — written before ercot-184/186/188); the rows below extend that
ledger to HEAD and any larger count is this card's arithmetic, not a quotation.

| session | lever / object | outcome | measured C3a-2023 move |
|---|---|---|---|
| ERCOT-154 | storage evening discharge-offer surface | REFUSED (curve flat, 1.6 $/MWh/GW) | buys $1.38–3.05 |
| ercot-155 | offer-dispersion arm | REFUSED; re-pointed to commitment state | — |
| ERCOT-158 | fast-start pool armed (`ercot_faststart_pool_offer`) | ENGAGED-but-INERT | 91 missed >$300 h bit-identical |
| **ERCOT-159** | `energy_online_capability_cap` (aggregate) | **R — four kill gates** | −24.5% → **+44.7%** (overshoot) |
| ercot-161 | armed RT wall | EXONERATED on its own population | λ formed on storage $1,500–5,000 offers |
| ercot-162 | `ercot_storage_rt_offer_surface` | **R** — battery discharge −74%/yr | gap set $441 → $457 |
| ERCOT-163 | "~8 GW cheap CC offline block" | **DOES NOT EXIST** (96.4% committed / 98.0% loaded) | object renamed: ~2.7 GW capability |
| ercot-167 | storage AS SOC reservation | owner-promoted on structural standard | tail counts unchanged |
| ercot-168 | per-year 2023 coal curves | KEEPER; C7-2023 CLOSED | **C3a-2023 unmoved** |
| ercot-170 | CC-headroom per-unit crosswalk | **FILED-UNLICENSED** (licence fails both legs) | no arm buildable |
| ercot-173 | 2023 "excess cheap depth" premise | REFUTED / FILED-REDIRECTED | — |
| ercot-175 | offered-vs-deliverable wedge | FILED-REDIRECTED (right size, wrong shape) | — |
| ERCOT-176 | offline-increment slow-start tier | provably INERT (`pool_frac_CC` 0.0002–0.0007) | not solved |
| ercot-177 | `temp_dependent_derate` | REFUSED ex ante; cell corrected to R | — |
| **ercot-178** | item 21 — continuous conditioning grain | **R on reach** | **+$8.18 headline; 67.5% manufactured VOLL shed; +$2.62 real** |
| **ercot-180** | item 22 — top-scoped grain | **R — zero admissible edges** (best rank 0.99486, KS p 0.017 vs 0.01) | no derive licensed |
| **ercot-181** | item 23 — position-tail completion | **K, INERT-ON-THE-OBJECT** | **+$0.0004/MWh** |
| ercot-184 | (c2) whole re-slicing family, costed | **REFUSED ON REACH** | ceiling **+$1.99** = 13.8% of bar |
| ercot-185 | item 24 — shaped partial derate | KEEPER (C3b-2024 → PASS) | 2023 INERT |
| ercot-186 | item 25 — rule-18 grain repair | STOPPED by its own pre-registered rule | no A/B |
| **ercot-188** | item 26 — (c2) SCHEME R1 built anyway (E2) | **R → K by owner promotion** | **−$0.21/MWh — a SIGN FLIP** vs the +$1.99 ceiling |

Not one admissible lever moved C3a-2023 by more than +$2.62/MWh real, and the last one
moved it the wrong way.

### 1.2 The face-closure map — what "no improvement" was measured against

Every face of the object has been closed **on measurement, not on fatigue**
(ercot-188 card §H; none is re-opened here):

* **Offer level** — items 21–23: the conditioning family's genuine offer-formation
  budget measured **~$2.6/MWh** (ercot-178 §7a).
* **Offer grain** — both forms `R`: continuous (item 21, shed-contaminated) and
  top-scoped (item 22, **zero admissible conduct edges at identification**).
* **Offer position** — item 23: the measured cliff conduct added and **+$0.0004/MWh**.
* **Offer resolution** — item 26 / MEMO-ercot184: the whole MW-preserving re-slicing
  family's ceiling **+$1.99/MWh**, delivered **−$0.21** at solve grain.
* **ORDC / RTORPA / reserve level** — ercot-177 §3: on the top-50 gap hours the model's
  scarcity adder is $107.92 vs the measured $104.82 (+3%), it holds 5,902 MW against a
  measured PRC of 5,471 MW, and the $1,454/MWh mean miss decomposes **energy-stack
  $1,529 (100.2%) / scarcity-adder −$3 (−0.2%)**. The scarcity machinery is *right*.
* **Quantity, aggregate form** — killed twice: `energy_online_capability_cap`
  (ERCOT-159, four kill gates) and the online-capacity envelope (ERCOT-107/108,
  **963-vs-69 h bistable — "No calibrated middle exists"**).
* **Sub-hourly** — (c1) refused on scale (ercot-182 §5/D5: 12× LP columns against a
  measured ~6.6 GB / ~20 min per per-plant year; a spec-level program, not a lane).
* **Topology** — the West/Panhandle split is CLOSED
  (`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§9–10).
* **Outcome pins** — forbidden outright (rule 13 `[R-MEASURED]`).

### 1.3 The convergent structural fact — the position wedge

The record's phrase is *"measured three independent ways"* (MEMO-ercot184 §8); the
citable instruments, kept metrically distinct because they live on different supports:

1. **ercot-180 §8** — the model's marginal row clears at **q_mod p50 0.9117** of its
   class curve; reality's accepted MW sits at **q_act p50 0.9976** (wedge +0.079;
   q_act > q_mod in 95/100 object hours).
2. **ercot-181 §4** — in the object hours the model's marginal rows read the
   **p50–p70 region** of the measured conduct ladders.
3. **ercot-181 §7 I-3** — reality's ON merchant-gas fleet held only **269/555/926 MW**
   (p25/p50/p75) of unaccepted spare priced below λ̂, at fleet position p50 0.884: *"the
   several-GW of $100–600-bid headroom that pins the model's top-hour price does not
   exist in real conduct."*
4. **ercot-184 §4.2/§4.4** — the keeper's marginal row sits at ladder **rel p50 0.643**;
   the best refinement moves it to **0.699** (scheme ceiling 0.833), and **0/100** object
   hours reach rel 0.9 under ANY MW-preserving scheme.
5. **ercot-188 §5.2** — at solve grain the refined curve carries 33 → **382** rows above
   rel 0.9 quoting up to 145× delivered gas: *"The model can now express a cliff; it
   still does not clear on one."*

MEMO-ercot184 §5 states the conclusion this card inherits: *"the LP goes on clearing at
ladder position ~0.70 because **what sets the clearing position is quantity, not
resolution**."*

### 1.4 The arithmetic that answers the question

C3a-2023 must move **+$14.66/MWh** on the current keeper ($43.23 → the $57.89 band edge;
the $14.44 figure quoted since ercot-177 is the same bar on the $43.44–43.45 vintage).
Against that bar:

| channel | measured value | share of bar |
|---|---|---|
| whole offer/conditioning family, genuine formation | **+$2.62/MWh** (item 21 decomposition) | **18%** |
| whole (c2) re-slicing family, ceiling across schemes | **+$1.99/MWh** | 13.8% |
| position-tail completion, delivered | +$0.0004/MWh | ~0% |
| (c2) SCHEME R1, delivered at solve grain | **−$0.21/MWh** | negative |

**Perfect execution of everything the offer family can admissibly do reaches ~18% of the
bar.** That is why fifteen rounds of correct, measured, admissible work produced no
improvement: the levers were real, and the object is elsewhere. Section 2 measures where.

---

## 2. HOW MUCH OF C3a-2023 IS THE ACCEPTED C3c OBJECT — the measurement

> **THE CLAIM UNDER TEST** (DIAGNOSIS-ercot177 §7, until now unquantified at annual
> grain): *"C3a-2023 and C3c-2023 are the same object, and C3a cannot reach the bar
> while C3c's tail deficit stands."*

**Method.** The probe rebuilds the keeper payload's price aggregates from the committed
`hourly/system_2023.parquet` with the payload builder's exact arithmetic, verifies
**dict-for-dict equality** with the committed payload and reproduces the scored keeper
(C3a −32.8%, C3b 0.608, tail 58/181, determination NOT-YET, 2024/2025 guards +1.2%/−8.0%
PASS) before emitting anything; then re-scores counterfactual price series **with the
rubric's own scorer functions**. `H_tail` := the **181 hours where the actual hub RT
series > $200 strict** — the committed `rt_gt` definition of the C3c actual. A
full-substitution seam gate (CF-0) bounds the crosswalk/rounding frame at
**−$0.01/MWh** against the bench `rt_lw` actual, so every row below is comparable to the
committed −32.8% at ~cent precision. (Definitional note: C3a weights zones by demand;
C3c counts model max-across-zones vs the actual hub; `H_tail` is pinned to the
actual-hub set and joined by hour index. All keys: `ercot189_c3a_c3c_overlap.json`.)

### 2.1 Where the miss lives (exact decomposition, no counterfactual)

In-frame annual demand-weighted gap: **$21.08/MWh** (positive-gap mass $28.39).

| hour set | n | contribution | share of net gap |
|---|---|---|---|
| **H_tail (actual hub > $200)** | **181** | **+$14.27/MWh** | **67.7%** |
| H_tail ∩ Aug–Sep (the ercot-177 "132/55" subset) | 132 | +$13.00 | 61.7% |
| Aug + Sep calendar months | 1,464 | +$17.00 | 80.7% |
| actual > $500 | 104 | +$11.18 | 53.0% |
| actual > $1000 | 61 | +$7.06 | 33.5% |
| everything except H_tail | 8,579 | +$6.81 | 32.3% |

Reconciliation against the committed instruments: this frame's Aug+Sep share **80.7%**
vs ercot-177's 81.3%; top-100-Aug–Sep share of positive gap **66.3%** vs MEMO-ercot184's
68.1%; the `lmpDeltaHr` top-181 negative-mass share reproduces **exactly** (0.8012 vs
0.801). The instruments differ by weighting, series and hour-set rule; they agree to a
few points, and the additivity identity closes to zero.

### 2.2 The counterfactual battery — the gate's own units

| counterfactual | C3a-2023 | C3b-2023 | model tail count | determination |
|---|---|---|---|---|
| baseline (keeper) | **−32.8%** FAIL ($43.23) | 0.608 FAIL | 58/181 | NOT-YET {C3a, C3b} |
| **CF-1: actual prices in all 181 H_tail hours** | **−10.6% FAIL ($57.51)** | **0.152 PASS** | 135/181 → C3c **PASS** | **NOT-YET {C3a only}** |
| CF-2: actual prices everywhere EXCEPT H_tail | −22.2% FAIL ($50.04) | 0.458 FAIL | — | NOT-YET |
| CF-3: tail floored at $200 (the C3c-inertness doorstep) | −29.7% FAIL ($45.24) | — | 58 | NOT-YET |
| CF-3: tail floored at $500 | −18.3% FAIL ($52.58) | — | 183 | NOT-YET |
| CF-3: tail floored at $1000 | +2.0% PASS ($65.61) | — | 183 | — |

**The three-number answer:**

1. **By dollars, C3a-2023 is two-thirds the accepted C3c object.** The 181 tail hours —
   2.1% of the year — carry **$14.27 of the $21.08** miss.
2. **By distance to the gate, it is ~97% of it.** Pricing the tail exactly as reality
   did moves C3a-2023 from −32.8% to **−10.6%** — **$14.28 of the $14.66 bar** — and
   collapses C3b-2023 (0.608 → 0.152 PASS) and C3c-2023 (the ledgered entry goes inert
   exactly as its own OPEN RESIDUAL LANE clause provides: *"a mechanism that lands there
   simply PASSes this criterion and this entry goes inert"*).
3. **And yet CF-1 does NOT quite clear the year.** A **$0.38/MWh** residual beyond the
   band edge remains — diffuse, spread across the 8,579 non-tail hours (which carry
   $6.81 of gap, of which the ±10% band absorbs $6.43). Under CF-1 the determination
   stays NOT-YET on **C3a-2023 alone at −10.6%**.

So the ercot-177 §7 claim is **confirmed with a measured refinement**: C3a-2023 is the
accepted C3c object *plus a ~$0.4/MWh sliver of diffuse base under-pricing*. The sliver
is real and this card does not round it away — but it is 2.6% of the bar, smaller than
the closed offer family's own $2.62 budget, and it matters **only if the tail is already
closed**. The decision therefore reduces to the tail.

### 2.3 What closing the tail actually requires — the number the next lane must beat

Within the 181 hours the model already clears a load-weighted mean of **$474/MWh**
against reality's **$945/MWh** (the top-50 extreme is $468 vs $1,922, ercot-177 §3). The
uniform tail price at which C3a-2023 exactly reaches the band edge is
**X\* = $709/MWh** (scorer-verified: PASS at −10.0%). Three consequences, stated
plainly:

* **The doorstep is worthless.** Reaching $200 in every tail hour — full C3c-count
  inertness — buys **+$2.01/MWh (13.7% of the bar)**. A mechanism can make the C3c
  caveat go inert and leave C3a-2023 essentially unmoved.
* **The requirement is conduct-level, not threshold-level.** The model must lift its
  tail clearing mean by **+$235/MWh — half the remaining distance to reality's tail
  level** — across 181 hours, while leaving 8,579 hours untouched. ERCOT-159 proved the
  level is *reachable* by force ($813 mean on the missed set) and that non-selective
  forcing fails four gates (+44.7% annual, 33 spurious tail hours, NRMSE 6.58).
* **C3b-2023 rides the same hours** (0.608 → 0.152 under CF-1 alone), confirming
  ercot-177 §7's corollary: the 2023 shape criterion is the tail seen monthly.

### 2.4 What this section does NOT do

It does not re-open the D1-refused carve-out, and its result would not support one:
ercot-182 §2 already held that if C3a-2023 and C3c-2023 are the same object, *"the C3c
model-class entry has already absorbed that limitation"* and ledgering it again on a
load-bearing criterion would be counting one accepted limit twice across the tiers. The
quantification above is decision evidence for §4 — not a rubric proposal.

---

## 3. THE PER-UNIT CAPABILITY LANE — the one untried face, priced honestly

**The object.** Item 11: the ~2.7 GW CC headroom/capability gap (ERCOT-163: model
**3.07 GW** of CC undispatched at the gap hours vs the market's **0.35 GW**, with model
CC *output* right to +0.30 GW — a depth ~9× reality's). ercot-170 confirmed its
provenance per-unit against the delivery-2023 SCED corpus: the pre-registered attribution
identity closes to **0.0000 GW** with the capability term at **102.4%** of the 2.648 GW
gap. This is the quantity face of §1.3's position wedge: the phantom sub-λ̂ headroom
(model several GW; reality 0.3–0.9 GW) is what parks the LP's clearing position at ~0.70.

**What it needs.** A per-unit SCED-train ↔ model-unit crosswalk. ercot-170's
pre-registered coverage licence **FAILED both legs** (L1 0.3375 vs a 0.90 bar; L2 0.1829
vs 0.10) → verdict `FILED-UNLICENSED`, *"no arm is named and none may be built on this
record."* The root blocker is ruling #9 — the DAM deriver's `_site()` cross-train
collapse takes the MAX not the SUM of ON rows (name-grain OFF CC 48.9 GW vs 14.1 GW
train-collapsed) — and **signature A1 (2026-08-11) has authorized its repair** as one
lane, #9 → #8 → #10. This card sequences around A1 and re-decides nothing about it.

**Standing constraint** (ERCOT-163 §4, carried at item 11): any fix is a rule-14
`[R-ACCURATE]` fleet-scope correction on the **existing**
`ercot_thermal_dam_availability_*` channel — never a new commitment gate, never an
aggregate cap, never a per-hour telemetered-HSL cap.

**Incremental cost over A1** (A1's own cost — re-derive all grains, re-gate every armed
DAM keeper, re-trigger the zone-anchor table under rule 23 — is signed and sunk):
1. the licence re-test on the repaired deriver — a phase-0 read, near-free;
2. only if licensed: a capability derive + precommit + per-plant A/B solves (the
   expensive tail, days of solve time under the rule-12 concurrency cap);
3. the risk carried from the family record.

**The honest prior.** The quantity family is 0-for-2 at aggregate grain, and the failure
mode is on the record: ERCOT-159 reached the object's price level and failed on
*selectivity* (its own verdict: **"THE DEFECT IS PRECISION, NOT PHYSICS"**); ERCOT-107/108
found **no calibrated middle** (963-vs-69 h). The per-unit form is precisely the
precision instrument that record calls for — that is the fair case for it — but nothing
in the record *predicts* it moves the residual: A1 was signed on data-correctness
grounds, with the card stating *"not because it will move the residual — nothing in the
record predicts that."* And §2.3 now fixes what success must mean: lift the tail
clearing mean **$474 → ≥$709** across 181 hours with the ERCOT-159 kill gates and
G-SHED held live, and with CF-3(200) proving that doorstep-grade capability tightening
is inert on the bar. The honest prior on clearing that bar is **low**; the honest value
of finding out is **one near-free licence read** once A1's #9 lands.

---

## 4. THE OPTIONS — card Q

> **THE QUESTION: after fifteen levers, a closed offer family, and the §2 measurement,
> what does the program do about C3a-2023?**

Not on the menu, by standing decisions this card honors: the C3a ledger carve-out
(REFUSED, ercot-182 card D1 — *"I want to actually fix the 2023 pricing"*); re-opening
any measured-closed face (§1.2); outcome pins (rule 13); re-deciding A1.

**The cost, stated before the decision.** Whatever is signed, A1's lane runs regardless
(it is a signed data-correctness repair). The marginal spend at stake here is everything
*after* it: the capability derive, the per-plant A/B rounds, and the sessions they
consume — against a measured-low prior and a $0.38 sliver that stays out of reach even
if the tail lands perfectly.

* **(Q-A) CONTINUE — authorize the per-unit capability lane behind A1.** Strictly
  sequenced: no capability work until A1's #9 lands; then the **pre-registered
  identification checkpoint** — re-run the ercot-170 coverage licence on the repaired
  deriver (bars unchanged: L1 ≥ 0.90, L2 ≤ 0.10) — and only a PASS authorizes phase-0
  identification. Any eventual arm inherits the ERCOT-159 kill gates verbatim, carries
  G-SHED live, and pre-registers §2.3's reach bar (tail lw mean ≥ $709 measured on the
  A/B, with the $200-doorstep result named as the inertness floor). **This option
  authorizes the checkpoint and phase-0 only — never a build.**
* **(Q-B) STOP — ERCOT stands at NOT-YET on C3a-2023 as a model-class limit, and the
  program stops spending on it.** Argued fairly, not as a strawman: this is a **budget
  decision, not a rubric decision**. The determination stays NOT-YET; C3a-2023 stands a
  MODEL MISS at full magnitude (−32.8%); no ledger text moves; D1 is honored. What it
  admits is now *measured* rather than suspected: the miss is two-thirds the accepted
  C3c object by dollars and ~97% of it by distance-to-gate, its closure requires
  equilibrium-conduct price formation ($709 mean across 181 hours) that the accepted
  limitation's own text says a competitive-offer LP cannot form, and the residual beyond
  it is $0.38. What it costs: §5's forecast posture, and the standing fact that the
  reference ISO reads NOT-YET *"for the foreseeable term"* (ercot-182 §4(b)). What it
  frees: the program's ERCOT spend, for ISOs with open faces. Why it is signable against
  *"I want to actually fix the 2023 pricing"*: the fix lane was granted and run to
  completion — D1(c) → D5 → ercot-184 costed it and recommended CLOSE; the owner built
  it anyway (E2); the measured answer was a sign flip. Stopping after the measurement is
  not giving up on the fix; it is believing it.
* **(Q-C) CHECKPOINT — sign the decision rule now, spend nothing until A1's #9 lands.**
  (Q-B)'s posture today, with one dated conditional: when the repaired deriver exists,
  run the licence re-test (near-free); **licence PASSES → (Q-A)'s phase-0 is authorized
  without a new sitting; licence FAILS → (Q-B) is automatic and final.** This is a
  signed rule, not deferred governance — the sitting happens once, here.

**Recommendation: (Q-C), with the rule's weight on (Q-B).** The branch logic was fixed
before the probe ran: *nearly-collapse + small doorstep → checkpoint tilted to stop*.
The measurement landed there — CF-1 takes the year to −10.6% (97% of the bar) and the
doorstep buys 13.7% — so the tail is confirmed as the whole decision, the only untried
instrument for it has a low prior and a near-free identification test already paid for
by A1, and nothing else on the ERCOT queue earns a session against this criterion. If
the owner would not authorize a build even on a passing licence, sign **(Q-B)** instead
— it is the same posture with the checkpoint's option value declined, and this card
presents it without prejudice.

---

## 5. WHAT EACH OPTION DOES TO THE FORECAST PROGRAMME

ERCOT is **the calibrated reference** among the six ISOs (CLAUDE.md; ercot-182 §3: the
alternative to fixing or honestly standing is *"certif[ying] a price level the model
does not reproduce … in the ISO that is the calibrated reference for the other five"*).
Four facts frame every option:

1. **The gate chain runs through the marker, not the determination string.** Forecast
   plan §2.1b gate (a) requires a designated keeper AND an entry in the `complete` block
   of `calibration-complete.json`. ERCOT's NOT-YET means the owner has not declared
   `complete`, so gate (a) is closed and **T2, T3 golden, the CES W4 campaign and PB-5
   remain "DEFERRED — unschedulable at any HEAD"** for ERCOT; the frozen ERCOT golden
   fixture stays frozen (a reseed is a 15-solve-year invocation against the 5-year cap).
   *(The committed board seed `program-status.json` reads gate (a) "determination
   NOT-YET; marker complete=False" — quoted with the caveat that the seed is dated
   2026-08-04 and still names the ercot158 keeper.)*
2. **The ceiling is CALIBRATED-WITH-CAVEATS, never CALIBRATED** (ercot-182 §10): even a
   fully successful capability arm leaves C3c a ledgered caveat or, at best, inert-with-
   history. Gate (a) does not distinguish the two — it keys on the marker — so under
   EVERY option the forecast question ultimately becomes an explicit owner judgment on
   declaring `complete` at the caveat posture.
3. **The transferable statement, now measured:** a forward year with 2023-like scarcity
   concentration carries an annual load-weighted price bias of up to **−$14/MWh on a
   $64 year (−22% of level)** from the accepted tail limitation, concentrated in ~2% of
   hours; years without that concentration score like 2024/2025 (+1.2%/−8.0%). This is
   the sentence the forecast lane owes its consumers whatever is signed below.
4. **The C3c limitation is propagated NOWHERE in the forecast namespace.** No forecast
   gate, caveat, or disclaimer carries it; `readiness_limits` (five disclaimers, none
   price-tail) is its natural home. **Under every option** this card proposes the same
   doc-only follow-up, outside this signature: add the §5.3 sentence as a
   `readiness_limits` price-tail disclaimer.

Per option:

* **(Q-A)** — the forecast posture is unchanged until an arm lands. If one ever clears
  2023, the fail set empties, the determination reads CALIBRATED-WITH-CAVEATS (or the
  C3c entry goes inert), and gate (a) turns on an ordinary `complete` declaration. The
  cost is time: the reference ISO's forecast lane stays deferred behind the longest and
  lowest-prior lane in the programme.
* **(Q-B)** — NOT-YET stands *as the honest reading*. Gate (a) stays closed **unless**
  the owner separately elects to declare `complete` on the measured record — §2 is
  exactly the evidence such a declaration would cite (miss quantified, two-thirds an
  accepted model-class object, remainder $0.38-beyond-band diffuse). (Q-B) does not
  mechanically doom the ERCOT forecast lane; it moves the decision from "wait for a
  mechanism" to "decide on the record", which is where §2 says it already lives.
* **(Q-C)** — (Q-B)'s posture until the checkpoint reads; at most one licence-read of
  delay before the (Q-A)/(Q-B) fork resolves itself by rule.

---

## RESOLUTIONS

*(placeholder — completed at the owner sitting; the card body above is preserved as put)*

| card | decision | **SIGNED** | vs. recommendation |
|---|---|---|---|
| **Q** | C3a-2023 after the offer family | — | — |

### What signing does NOT do

* **No rubric text changes** — `LEDGERABLE_CRITERIA`, the tier guard, the C3c standing
  rule and the caveat budget are untouched under every option.
* **No ledger entry is added, moved, or re-scoped**; C3a-2023 remains a MODEL MISS at
  full magnitude under every option.
* **No keeper movement, no matrix cell, no `ScenarioConfig` field, no solve** follows
  from any signature here; (Q-A)/(Q-C) authorize a checkpoint and phase-0 identification
  only, each behind A1's own lane.
* **No forecast gate or marker changes** — §5's `complete`-declaration question is named
  as the owner's, not decided.
* **A1's signed sequence (#9 → #8 → #10) is not modified** in scope, order, or content.

### Execution order implied by the signatures

1. A1's lane proceeds regardless (already signed, ercot-188 card A).
2. On (Q-C)/(Q-A): when #9 lands, run the ercot-170 licence re-test on the repaired
   deriver; record the read in the calibration log and item 11.
3. On a licence PASS under (Q-C)/(Q-A): phase-0 identification under item 11's charter,
   ERCOT-163 constraint intact; any build is a NEW sitting with §2.3's reach bar
   pre-registered.
4. On (Q-B), or a licence FAIL under (Q-C): no further ERCOT C3a-2023 spend; the §5
   `readiness_limits` disclaimer follow-up and the owner's `complete`-declaration
   question are the only remaining ERCOT-C3a items, both doc-grade.

---

## EVIDENCE APPENDIX — every figure above is read off these committed artifacts, with no re-derivation

* `results/calibration/ercot189_c3a_c3c_overlap.json` — this session's single new
  measurement (probe: `scripts/probes/ercot189_c3a_c3c_overlap.py`; baseline gate
  dict-equal, CF-0 seam −$0.01, additivity exact).
* `results/calibration/ercot188_topfine_arm_B/` — the keeper bundle:
  `hourly/system_2023.parquet` (the price/demand frame), `calibration_attestation.json`
  (the C3c exceptions text quoted in §2.2), `metrics.json`.
* `frontend/data/backcast/bench/ERCOT/2023.json.gz` (`avgLMP.rt_lw = 64.32`),
  `frontend/data/backcast/tail/actual_tail.json` (`rt_gt = 181`),
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet` and
  `actual_lmp_zonal_ERCOT.parquet` (H_tail and the substituted actuals).
* `scripts/calibration_verdict.py` (rubric v3.2 — the scorer whose functions produced
  every counterfactual score) and `scripts/render_calibration_html.py:2107–2155, 817`
  (the payload-builder and `_tail_hours` arithmetic the probe replicates).
* `docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §§2, 4, 5, 7, 10 —
  D1/D5 signatures, the 18%-of-bar decomposition, the double-count objection, (c1).
* `docs/MEMO-ercot184-cliff-resolution-costing-2026-08-09.md` §§2, 4, 5, 8 — the (c2)
  ceiling, the ~0.70 clearing position, the family budget.
* `docs/DIAGNOSIS-ercot177-c3a2023-anatomy-2026-08-07.md` §§3, 7 — the energy-stack
  decomposition, the same-object claim, the $14.44 bar.
* `results/calibration/FINDING-ercot180-topscoped-exhausted-2026-08-08.md` §8,
  `FINDING-ercot181-position-tail-2026-08-09.md` §§4, 7,
  `FINDING-ercot188-cliff-offer-curve-2026-08-11.md` §5.2 — the position instruments.
* `results/calibration/FINDING-ercot163-cc-commitment-state-refuted-2026-08-04.md`,
  `FINDING-ercot170-cc-headroom-crosswalk-2026-08-05.md`, matrix §5.1 item 11 — the
  capability object and its licence record.
* `docs/calibration-log/ercot.md` (ERCOT-159 entry: the four kill gates;
  ERCOT-107/108 entry: the bistability table) and
  `docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md` (A1–G, §H).
* `docs/forecast-development-plan-2026-07.md` §2.1b and
  `frontend/data/forecast/program-status.json` (stale-seed caveat stated in §5).

## GOVERNANCE — what this session did and did not do

* **Rule 1 `[R-STRUCT]`:** no mechanism built or tuned; the measurement reports the
  counterfactual answer at full magnitude, including the result that weakens this
  card's own simplest narrative (CF-1 does not fully clear the year).
* **Rule 13 `[R-MEASURED]`:** measured actuals were substituted **only inside
  counterfactual scoring** to size an overlap; nothing was fed to any model input, and
  no solve occurred. The probe's post-battery check re-verifies the committed artifacts
  still read NOT-YET.
* **Rule 15 `[R-DASHBOARD]`:** no run was produced, so nothing registers; the probe
  JSON is committed as the session's evidence artifact (measuring-session precedent:
  ercot-184).
* **Rule 22 `[R-HOLDOUT]`:** years touched = {2023, 2024, 2025} only; 2024/2025 only as
  committed-payload guard reads.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT only.
* **Rule 27 `[R-PUSH]`:** new files only; no source file ≥300 lines modified.
* **Rule 28 `[R-MECH-MATRIX]`:** no cell minted and no verdict written — this is a
  governance sitting with a read, not a mechanism test (precedent: the ercot-182
  sitting touched only its card and the calibration log).

**Next shorthand: ercot-190.**
