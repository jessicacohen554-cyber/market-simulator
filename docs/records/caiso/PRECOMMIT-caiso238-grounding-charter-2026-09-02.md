# PRECOMMIT — caiso-238: the GROUNDING CHARTER for the four class-(c) live residual DOF rows

**Registered 2026-09-02, session caiso-238. Branch
`claude/caiso-backcast-calibration-238-is2suy`, cut fresh from `origin/main`
(`d06e6866`). PUSHED BEFORE ANY MEASUREMENT IS COMPUTED.**

Keeper at entry: **`2026-09-01-caiso-231-b1-ungrounded`** (bundle
`results/calibration/caiso231_b1_ungrounded`), determination **NOT-YET**, **C3a the
SOLE load-bearing FAIL** (+4.1 / +12.5 / +15.6 %, 2023 passes); C1 12/12 free 8/8;
C3b PASS; C3c the single ledgered caveat (standing rule, non-downgrading); C6
attested; C8 PASS. CAISO holds **no `complete` and no `final` marker**; the holdout
spend freeze is **ACTIVE**. Every read in this session stays inside **2023–2025**.

---

## §0 — WHAT THIS SESSION IS, AND WHAT IT MAY NOT BECOME

**§0.1 — The CAISO lane is at a TERMINAL REST WITH A DECISION MAP** (owner ruling
caiso-222 Q1 on the caiso-201 rest). The C3a residual is designated **attributed and
closed at this representation grain**. The in-model lever queue is exhausted **by
measurement**, not by fatigue.

**§0.2 — This session is admissible under that rest for the same reason caiso-236
and caiso-237 were: it is NOT a lever hunt.** It is a rule-21 `[R-DOF]` /
rule-14 `[R-ACCURATE]` **grounding-charter** lane. caiso-236 §10 left **four residual
rows LIVE AND MATERIAL and deliberately untouched** — `offer_curve_by_group`, the
`ST_GAS 0.81` committed band, `offer_curve_smoothing`, `battery_dispatch_adder` — and
recorded in terms that name this session's object exactly: *"Grounding a live
residual is a funded-object question under the resting ruling, not a ledger-audit
session's to take."* The deliverable is therefore a **costed, pre-adjudicated ask
put to the owner** — four objects converted from "live and material, untouched" into
"fundable / not fundable, and why". **PROPOSE, DO NOT EXECUTE.**

**§0.3 — C3a IS NEVER THIS SESSION'S OBJECTIVE, AND IS NEVER AN ARGUMENT FOR OR
AGAINST FUNDING AN OBJECT.** No conclusion here may be argued from the price residual
(rule 1 `[R-STRUCT]`). Grounding a fitted scalar on measured data is a
**structural-integrity** act whose merit is independent of the residual: caiso-231 is
the governing precedent — it was promoted **knowing it cost C3a** (+0.062/+0.037/
+0.031 $/MWh), because a measured multiplier replacing an ERCOT-fitted one is right
whatever the fit does. Any object whose expected C3a direction is knowable is
reported with that direction **disclosed, never used as a ranking criterion** (rule
14 `[R-ACCURATE]`: a worse fit from an accurate input is a discovered bug elsewhere,
not a reason to keep the estimate).

**§0.4 — HARD STOPS.** Zero solves. No LP built, no solver called. **No
`ScenarioConfig` field is added, removed, changed or armed.** No derive script is
run or re-run (rule 23 `[R-FROZEN-DERIVE]`). No bundle, no registration (rule 15 does
not attach — no calibration run is produced). No matrix **verdict** moves; at most an
evidence append (rule 28(b)). No keeper shard, `calibration-complete.json`,
`holdout-freeze.json` or other ISO's file is touched. If assessing an object requires
a solve or a replay to answer, the answer recorded is **UNMEASURABLE WITHOUT A
SOLVE** — never an estimate dressed as a measurement.

**§0.5 — DO-NOT-REDO acknowledged (rule 28(a)).** None of the following is re-opened
or proposed here, and no object below is offered as a C3a instrument: the
above-floor decomposition on this keeper (caiso-230 §9); zonal congestion / Path-15 /
sub-zonal topology as a C3a instrument; re-attributing the term to peaking; the
below-stack wedge, both doors (caiso-229, sign/depth/coupling and size); the three
refused import-depth estimators and the `spot_capacity` DOF (**CLOSED as not
identifiable**, caiso-233/234/235); the FSNO static DMM-cap arm (**R**, caiso-224);
the south-belly surplus-pricing object (**killed with measurement**, caiso-221);
`caiso_solar_cap_at_delivered` (**barred permanently**, rule 13); the W-1/W-2/W-3
watch sweep, whose next execution is **DATED** to the Order-881 AAR effective date
(≤ 2026-12-01) — an earlier re-run is the re-survey the caiso-218 §F fences forbid,
so **this session does not sweep**.

**§0.6 — WHAT WAS ALREADY READ BEFORE THIS FILE WAS PUSHED, DISCLOSED SO THE
PREDICTIONS BELOW ARE HONESTLY CONDITIONED.** (i) The keeper's
`calibration_attestation.json` free-parameter ledger in full — it is the *object*,
not evidence about it; (ii) `data/raw/_validation-source/caiso_offer_curve_measured.json`
in full, **including that it carries measured `committed` bands (CC_REGULAR 1.030,
CT_PEAKER 1.166) under an explicit `unarmed` key**; (iii) the "Lever-A inversion
lesson" statements in `docs/calibration-log/caiso.md`, the mechanism-matrix base row
and the CAISO shard; (iv) the column schema (not the contents) of the keeper's
`hourly/class_hourly_*.parquet`. **NOT read at push time:** the keeper's
`run_config.json` armed band values, any hourly sidecar contents, the storage
sidecar, `derive_campd_gas_commitment_params.py`, the `offer_curve_smoothing`
consumer code, the `battery_dispatch_adder` consumer code, and the CAISO fleet's
class inventory.

---

## §1 — THE FUNDABILITY TAXONOMY, FIXED IN ADVANCE

Every one of the four objects is assigned to exactly one class. **The class
determines the ask; the ask is not chosen after the fact.**

| class | definition | the ask put to the owner |
|---|---|---|
| **F1 — GROUNDABLE NOW** | a measured counterpart for the **exact quantity at the model's own grain** exists and is **already committed in this repo**, and arming it is a zero-free-parameter substitution admissible under rules 13/19/24/25 | a **solve-round** ask: A/B against a bit-zero control, pre-registered, adverse direction declared in advance (the caiso-231 shape) |
| **F2 — GROUNDABLE, INSTRUMENT NOT IN HAND** | a measured counterpart is **identified and publicly available** but must be intaken through the data contract first | a **data-intake** ask (caiso-218 §F.2/§F.3 fences: intake first, never a solve), with the intake's own feasibility stated |
| **F3 — NOT GROUNDABLE AT THIS GRAIN** | no measured object maps onto the quantity at the model's representation grain — the caiso-188 `IMPORT_TRANCHES` class ("no published object maps onto either") | **no ask.** The row stays residual and is declared to the owner as such |
| **F4 — REFUSED ON RULE** | a measured counterpart exists, and arming it is **refused by a standing rule or an already-adjudicated lesson** (rule 19 `[R-ONE-MECH]`, rule 13 `[R-MEASURED]`, rule 25 `[R-ISO-SCOPE]`) | **no ask at this grain**, and the refusal is recorded so it is never re-proposed |

**A fifth outcome is permitted and must be reported against interest:**
**MIS-CLASSIFIED AT caiso-236** — if an object turns out **not** to be live-and-
material (dead, or arithmetically inert), it is a caiso-236 classification error,
reported as such, and its correct action is caiso-236's class (a) DELETE or class (b)
NEUTRALIZE, **not** a grounding ask. This session does not execute that action
either; it files it.

---

## §2 — THE FIVE QUESTIONS ASKED OF EVERY OBJECT, IN ORDER

**Q1 LIVE?** Is the value read on the keeper's own configuration? Answered from the
committed `run_config.json` gates + the consumer code, never from a solve.

**Q2 MATERIAL, AND HOW MUCH OF IT?** What does the scalar actually price on **this
keeper**, measured on its own committed `hourly/` sidecars. For a per-group surface
the measurement is the **live fitted remainder**: how many of the row's scalars sit
on a class that (i) exists in CAISO's built fleet and (ii) carries non-trivial
dispatch. A scalar on an unpopulated class is counted separately and is **not** part
of the ask.

**Q3 INSTRUMENT?** Does a measured counterpart exist for the quantity **at the
model's grain**; where; and is it committed, public-but-unintaken, or absent.

**Q4 ADMISSIBLE?** Rule 13 forward-analogue test (could this same quantity be
produced for a forward year and respond to changed conditions?); rule 19
(does another armed mechanism already own the phenomenon?); rules 24/25 (registry,
no cross-ISO transfer). **A measured object that fails any of these is F4, however
attractive.**

**Q5 COST?** DOF delta (scalars retired vs added — an object that *adds* a free
parameter is refused outright under rule 21), the session shape required, and the
**expected C3a direction disclosed** per §0.3.

---

## §3 — PER-OBJECT PREDICTIONS, REGISTERED IN ADVANCE

Predictions are conditioned on the §0.6 disclosure. Each carries a **falsifier** —
the observation that would make the prediction wrong.

**Object 1 — `offer_curve_by_group` (112 scalars, identification `residual`).**
*Predicted class: **F4**, on a reduced live surface.* Specifically I predict (1a) a
**large majority of the 112 scalars are not on CAISO's binding path at all** — the
five `COAL*` groups plus the three `*_INTERMEDIATE` groups are ERCOT/PJM-lineage
family entries with little or no CAISO fleet behind them (caiso-236 measured CAISO
coal at 0.0442/0.0248/0.0393 % of energy), so the live fitted remainder is far
smaller than the ledger's 112; and (1b) after caiso-231 retired nine multipliers to
measured, **the fitted remainder that is both live and material is essentially the
five `committed` bands** (CC_REGULAR 1.000, CT_PEAKER 1.350, CC_CHP 1.000, CT_CHP
1.100, ST_GAS 0.810), whose measured counterparts exist but are **withheld by the
adjudicated Lever-A lesson** (min-load self-commitment conduct belongs to unit
commitment, not the P1 offer — rule 19). Hence F4.
*Falsifier:* **any non-`committed` CAISO band still carrying a fitted (non-measured)
value on a class holding ≥ 1 % of the keeper's annual gas-fleet energy.* If one
exists, object 1 is **F1 or F2**, not F4, and the charter must say so.

**Object 2 — `offer_curve_committed_below_floor[CAISO]`, `ST_GAS` = 0.81 (1 scalar).**
*Predicted class: **F4** on the offer side, **F2** on the commitment side.* The
value sits below the audit §2 0.85 physical floor with no written rationale (issue
#1302). A measured offer-side counterpart exists — ST_GAS falls in the measured
**CT** bucket (caiso-231), whose measured `committed` band is 1.166 — but arming it
is the same Lever-A refusal as object 1, and it would be a **+44 %** move on a band
the model uses as a floor. I predict the honest reading is that **the object is
mis-located**: a committed tranche priced below its own fuel cost is a
**must-run / self-commitment** phenomenon, and CAISO's three ST_GAS steamers are the
**OTC/RMR** units named by `derive_caiso_offer_surface.py`; so the grounding
instrument is a commitment-side must-offer obligation, not a bid multiplier.
*Falsifier:* **the ST_GAS group on the keeper's fleet is not the three OTC/RMR
steamers** (i.e. the class carries other, merchant units in material size). If so the
must-offer framing fails and the object is **F3**.

**Object 3 — `offer_curve_smoothing_n` = 6, `offer_curve_smoothing_exp` = 1.0
(2 scalars).** *Predicted class: **F3**.* No published object measures a within-class
econ-ramp smoother; it is a representation-grain shape knob, the class caiso-188
adjudicated as having no measured counterpart. I further predict a **material
possibility of the fifth outcome**: `exp = 1.0` is the identity exponent, and if the
smoother reduces to an identity at that value then the row is **arithmetically inert**
and caiso-236's class (c) was wrong for it.
*Falsifier:* the consumer code shows `exp = 1.0` is **not** an identity (the smoother
still reshapes the ramp at that value), in which case the row is genuinely live and
stays F3 rather than being re-classified.

**Object 4 — `battery_dispatch_adder` = 5.0 $/MWh (1 scalar).** *Predicted class:
**F2**.* This is the **only** one of the four whose ledger row already names its own
forward-valid replacement in writing — *"the measured AS power reservation
(`storage_as_commitment`) + an ATB-derived degradation cost"* — so Q3 and Q4 are
half-answered by the ledger itself, and it is the **strongest fundable ask of the
four**. I predict the instrument is **not in hand**: the CAISO storage-AS award
corpus is one of the BLOAT-S2 conversions whose payload is untracked at tip and
**recoverable by re-fetch only**, so the intake must re-fetch before anything can be
derived.
*Falsifier:* the CAISO storage-AS award payload is present and usable in the working
tree, **or** `storage_as_commitment` is already armed on the keeper — either makes
object 4 **F1**, a solve-round ask rather than an intake ask.

**Registered ranking prediction:** exactly **one** of the four (object 4) will be a
fundable ask this session can hand the owner; the other three will be refusals or
non-asks. **If all four come back fundable, that is evidence this charter has drifted
into a lever hunt and §0.4's stop applies.**

---

## §4 — THE (b)-CLASS ROLL-UP, SCOPE-BOUNDED

The charter also refreshes the status of the two **owner-fundable, currently
unfunded** objects the handoff names — the caiso-131 A3 **SoCalGas OFO** arm
(confirmed available and trivially feasible at caiso-225; its design already
pre-registered, unexecuted, in `PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`) and the
`IMPORT_TRANCHES[CAISO]` residual named by caiso-232 defect 2 as the December
**level** object. **This is a status roll-up only — no new measurement, no new
design, no re-adjudication.** Neither may be started without an owner grant, and this
session does not start either.

---

## §5 — DELIVERABLES DECLARED IN ADVANCE

1. This PRECOMMIT, pushed to `origin` before any measurement.
2. `scripts/probes/_caiso238_grounding_charter.py` + its JSON output — every Q2
   number, computed from committed artifacts only.
3. `ASSESSMENT-caiso238-grounding-charter-2026-09-02.md` — the four objects, each
   with its class, its five answers, its ask (or its refusal), and the §3 predictions
   **scored, hits and misses alike**.
4. The `docs/calibration-log/caiso.md` caiso-238 entry.
5. At most one CAISO mechanism-matrix **evidence append** (rule 28(b)); **no verdict
   moves**.

No dashboard registration is due. No keeper change is proposed. The determination
stays **NOT-YET**.
