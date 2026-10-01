# FINDING ercot-232 — the keeper's 21 spurious mid-band hours are a Northeast **deliverability** artifact, and refining the tie placement to buy them back is measured-counterindicated; the seasonal end-of-season term is measured **inert**

**Date:** 2026-08-24 · **ISO:** ERCOT · **Keeper:** `2026-08-24-231-tie-zone-measured`
(bundle `results/calibration/ercot231_tiegtc_full`) · **Prior keeper (A/B
comparator):** `2026-08-20-ercot223-arm-eventrelease`
(`ercot223_release_arm`) · **Probe:**
`scripts/probes/ercot232_gspur_phase0.py` →
`results/calibration/ercot232_gspur_phase0.json`

**NO SOLVE, NO LP, NO MECHANISM BUILT, NO `ScenarioConfig` FIELD, NO RUN
REGISTERED, KEEPER UNCHANGED.** Every number below is read from artifacts
already committed at HEAD: the two keepers' hourly sidecars, the hub RT actual,
and the ERCOT NP6-86-CD SCED binding-constraint archive. Rule 28(b): a verdict
is minted for each of the two chartered moves; rule 28(c) is not engaged.

---

## 1. What was asked

The handoff named two admissible moves, in order, on the remaining rubric
failures `{C3a-2023 ≈ −38.0, C3b-2023 ≈ 0.696, C3c ledgered}`:

1. **G-SPUR diagnosis** on the new keeper from committed sidecars — what sets
   the 21 Aug-5..Sep-26 mid-band hours. *A measured refinement of tie placement
   is admissible only if phase-0 measurement names it* (zero fitted scalars,
   precommit first).
2. **The seasonal end-of-season term** — the only un-adjudicated adaptive
   successor (a fall-shape object, not summer depth) — *carded honestly*.

Both are answered here on measurement. **Neither yields an admissible lever**,
and move (1)'s measurement is not merely silent but **affirmatively
counter-indicates** the refinement it was scoped to look for.

---

## 2. Move (1), the anatomy: the spur is Northeast decoupling, λ-made

The keeper's 21 spurious hours reproduce exactly off the committed sidecars
(hours 5251, 5272, 5438–5441, 5443, 5465, 5466, 5492, 5660, 5684, 5731, 5804,
5821, 5822, 5850, 5874, 5995, 6306, 6450); 10 of them are new against the
prior keeper's 11. They are **λ-made, not adder-carried** (19/21 carry
λ ≥ $150; ORDC adder p50 ≈ $1.3, only h5684 above $40), carry **zero shed
hours**, and sit entirely in-season (2023-08-07 .. 2023-09-26, hod 13–20).

The zonal cut is the whole story. In **every one** of the 21 hours the six
non-Northeast zones price *identically* while **Northeast prices $24–126** —
a $65–221 separation. That separation is by construction the dual of the
`NE_LOB` export link (`Northeast→North`, `constants.ERCOT_GTC_LINK_MAP`).

**Mechanism.** The Northeast zone is the EAST weather zone: ~8 GW of
generation (Martin Lake, Welsh, Pirkey, Tenaska Gateway, Wilkes) serving 3.51 %
of system load behind a ~1,300 MW export limit. `ercot_tie_zonal_interchange`
places **600/820 of the measured SWPP DC-tie flow into that zone**. In an
import hour the lobe is already at its export bound, so the placed import
displaces local generation 1:1 and **delivers nothing to the rest of ERCOT** —
which the LP then prices as a tighter system. Under the superseded load-share
spread the same MW were scattered ~96.5 % into zones that could use them.

That is a real deliverability consequence of a real placement, not a bug: the
tie arm's whole measured gain (C3a-2023 −39.7 → −38.1) and its G-SPUR cost come
from **the same mechanism acting in different hours**.

## 3. The whole-year NE_LOB object — the placement is right in aggregate, and its *timing* was never right in either keeper

Measured truth is the NP6-86 archive's `NE_LOB` shadow price, reduced to the
hourly-equivalent dual (shadow price averaged over **all** SCED intervals in
the hour, non-binding at 0 — the correct analogue of an hourly LP's dual; the
binding-intervals-only average overstates a constraint that binds for part of
an hour). 2023: `NE_LOB` binds in **2,408 h**, annual dual sum **$69,932**.

| | prior keeper | **new keeper** | measured |
|---|---|---|---|
| model congested hours | 918 | **1,974** | 2,408 |
| annual dual sum | $13,719 (19.6 %) | **$55,816 (79.8 %)** | $69,932 |
| hours agreeing with measured | 71 | **443** | — |
| model-only (spurious) hours | 847 | **1,531** | — |
| measured-only (missed) hours | 2,337 | **1,965** | — |
| p50 dual on agreeing hours | $3.43 | **$8.71** | $25.91 |
| **corr(model, measured)** | **−0.059** | **−0.042** | — |

Three things follow, and they do not point the same way:

- **The tie placement moved the NE congestion object substantially toward
  measured on every aggregate** — magnitude 19.6 % → 79.8 % of measured,
  frequency 918 → 1,974 against 2,408, hour-agreement 71 → 443.
- **The model is *under*-deep, not over-deep.** On agreeing hours the model
  clears $8.71 against a measured $25.91. The spur hours read the other way
  (model p50 $149.68) only because they are a selected tail.
- **The timing is uncorrelated with reality — and was equally uncorrelated
  before.** corr = **−0.059** on the prior keeper, **−0.042** on the new one.
  The placement did not degrade the timing; it gave an already-mistimed
  congestion object ~4× more magnitude to misplace, which is what made the
  mistiming visible as G-SPUR hours.

At the 21 spur hours specifically, `NE_LOB` was measured **binding in 2/21**
(1/10 of the new hours) with **measured p50 dual $0.00** against the model's
$149.68. The model puts its deepest Northeast congestion precisely where
reality had none.

## 4. Verdict on move (1): NO ADMISSIBLE REFINEMENT — and the measurement counter-indicates one

A "measured refinement of tie placement" that reduces the 21 spur hours must
strand less import in the Northeast — i.e. move flow off the 600/820 East-tie
share. That would **reduce** the model's NE congestion magnitude, frequency and
agreement, all three of which the placement had just moved *toward* measured.
It trades a structurally-correct aggregate (79.8 % of measured congestion) for
a gate count, on a residual it is not identified against. That is precisely
what rule 1 `[R-STRUCT]` forbids ("never judge a structurally-correct mechanism
by whether it improves the backcast fit") and what rule 14 `[R-ACCURATE]`
names as burying the error back inside an inaccurate input.

Phase-0 therefore **does not name a refinement, and the licence in the handoff
is not met.** No precommit is opened, no flag is proposed, `ERCOT_DC_TIE_ZONE_MAP`
is untouched.

The measurement instead re-attributes the residual. Under rule 14's own logic —
an accurate input making a gate worse means *something else* was being
compensated — the object it exposes is **`NE_LOB` binding-hour timing**, which
was ~zero-correlated in both keepers and is therefore a **pre-existing defect
the load-share spread was masking**, not a defect of the tie placement.

**That object is not admissibly tunable at zonal grain**, and this is already
adjudicated. A generic transmission constraint binds on contingency/nodal
conditions a 7-zone reduction cannot carry;
`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §10 (ERCOT-117,
matrix cell `internal_congestion_split` = **G**) measured nodal-only binding at
36–47 % of all SCED intervals, concentrated in **138 kV single elements binding
66–83 % of intervals**, and refused sub-zonal splits because their link TTC
would have to be *invented* against the very residual they close (rules 5, 13,
14). The Northeast case differs only in that `NE_LOB` **is** in the aggregate-GTC
vocabulary and is already modeled explicitly with its measured limit — so the
admissible representation is already carried, and what remains is the
sub-zonal timing §10 closed. **DO-NOT-REDO** as a topology change.

**Consequence for the keeper: none, and the promotion basis is strengthened.**
The G-SPUR REJECTED-AS-ARMED record stands unrewritten, as it must. But the
mechanical verdict was reading a gate that counts spurious mid-band hours,
against a mechanism whose measured effect on the constraint it perturbs is a
4× move toward the published truth. That is the owner's standing structural
standard operating exactly as intended — measured here, after the fact, rather
than argued.

---

## 5. Move (2): the seasonal end-of-season term is REAL as a shape defect and MEASURED INERT as a lever

**Carded honestly, in both directions.**

**The defect is real.** The adaptive floor's seasonal envelope *lags the
season by a month and persists far past it*: monthly mean floor Jun $18 → Jul
$35 → Aug $62 → **Sep $232 (peak)** → Oct $130 → Nov $63 → Dec $27, still
armed in 124 December hours (max $257). The market it is meant to represent
de-scarcifies hard after August (actual hours > $200: Aug 100, Sep 32, Oct 4,
Nov 3, Dec 2). The half-life decay carries August's expectation into a season
that has no spikes. An end-of-season term is a **well-posed structural-hygiene
object**, and this is the first measurement to name it concretely.

**But it has no residual to grip, and cannot move the failing criteria.**

- **The 2023 residual is a summer-depth object, not a fall-shape object.**
  Share of the annual MWh-weighted under-pricing: **Aug 60.0 %**, Sep 18.8 %,
  Jun 14.1 %, Jul 4.2 % — **Jun–Sep = 97.1 %**. Oct 0.4 %, Nov 0.4 %.
- **The months an end-of-season term would touch are already the
  best-calibrated of the second half-year.** Oct −4.1 %, Nov −4.1 %, Dec +3.0 %;
  Oct–Dec together **−2.2 %** and **0.6 %** of the annual under-pricing.
- **The lingering floor is armed but effectively non-binding.** Across Oct–Dec
  it is armed in **368 hours** and pins the price in **4**. Decaying it is
  therefore inert on the scored digits by measurement, not by argument.
- **Direction is wrong where it is not inert.** Oct and Nov are *under*-priced;
  a decay term lowers them further. Only Dec (+3.0 %) would improve.

**Verdict: NON-VIABLE ON MATERIALITY** (measured inert), not on premise — a
distinction worth keeping, because the defect is genuine. If it is ever built
it must be built on a *measured* seasonal expectation and judged on structural
faithfulness alone under rule 1, never quoted against C3a/C3b-2023, which it
provably cannot move. It is **not** a live calibration lever and should not be
carried in the queue as one.

---

## 6. Disposition

Both chartered moves close on measurement, with no lever proposed, nothing
self-adjudicated and the keeper untouched:

1. **G-SPUR / tie-placement refinement — NOT ADMISSIBLE, counter-indicated.**
   The residual re-attributes to `NE_LOB` timing, which is the §10 sub-zonal
   object (cell `internal_congestion_split` = `G`). DO-NOT-REDO.
2. **Seasonal end-of-season term — NON-VIABLE ON MATERIALITY, measured inert
   (4 pinned hours in Oct–Dec; the fall is 0.6 % of the under-pricing).**

That exhausts the handoff's admissible list. **The remaining route is Door D**
(2026 SOM RTC+B anchors, ~mid-2027), exactly as the handoff anticipated for
this branch. The 2023 price object stands where card R / Q-B FINAL / R-A left
it: `{C3a-2023 −38.0 %, C3b-2023 0.696}` as the adjudicated model-class
limitation, C3c ledgered ×2, determination **NOT-YET**.

**Closed cells confirmed still closed and not re-tested:** the ORDC/adder
channel (RTORPA ≈ $1), aggregate capability (ercot-219 `R`), per-unit crosswalk
(item 11 / Q-B FINAL), cross-year seed (ercot-222 `R`), topology splits
(ERCOT-117 / §10 `G`).

**Hygiene:** no LP, no solve, no CI job, no workflow; committed artifacts and
`data/raw` reads only; years {2023} only (rule 22); ERCOT-only shards and cells
(rule 25); probe script committed as the calibration record, probe JSON
committed alongside the ercot-231 family.
