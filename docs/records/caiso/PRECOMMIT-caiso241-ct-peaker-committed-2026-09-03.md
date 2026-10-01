# PRECOMMIT — caiso-241: the `CT_PEAKER` `committed` band — ADMISSIBILITY RULING, and the grounding arm it authorises

**Session caiso-241, 2026-09-03. Branch `claude/caiso-ct-peaker-admissibility-bnjtvb`.**
Parent object: `FINDING-caiso240-gas-vs-eia930-2026-09-03.md` §3–§4 (CAISO's
`CT_PEAKER` is dispatched at **2.5 % / 0.8 % / 0.4 %** capacity factor against a
measured **7.4 % / 7.5 % / 4.1 %**, uniform across every zone and month,
worsening, on identical nameplate — a **dispatch** miss worth
−2.71 / −3.84 / −2.11 TWh that C1 passes because the class fits inside the
±8 TWh / ±3.0 pp bands).

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read and any solve stays inside **2023–2025**.

Keeper at open: **`2026-09-03-caiso-240-b1-stgas`**
(`results/calibration/caiso240_b1_stgas_peak_measured`), **NOT-YET**, one
load-bearing FAIL — C3a **+4.1 / +12.6 / +15.6 %** (2023 PASSES).

---

## §0 — WHAT THIS SESSION IS, AND THE DISCLOSURES THAT CONDITION IT

**§0.1 — THE FIRST DELIVERABLE IS A RULING, NOT A SOLVE.** caiso-238 graded the
five live CAISO `committed` bands **F4 — refused on rule** under the adjudicated
Lever-A lesson, and caiso-231 applied that refusal uniformly. §1 below decides,
**on the record and before any arm is designed**, whether grounding
`CT_PEAKER.committed` on its own measured **physical** counterpart is inside or
outside that refusal. Had the ruling come out INSIDE, this file would end at §1
with the measurement and an owner ask. It comes out **OUTSIDE**, on five limbs,
three of them new; §2–§5 are therefore reached.

**§0.2 — FULL DISCLOSURE: WHAT WAS READ BEFORE THIS FILE WAS PUSHED.** Following
the caiso-238 §0.6 / caiso-239 §0.2 / caiso-240 §0.3 pattern, and stated first
because it conditions what §4 can honestly pre-register. Read before pushing:
**source** — `pipeline/backcast_config.py` (`_CAISO_OFFER_CURVE`,
`_NYISO_OFFER_CURVE`, `_NEISO_OFFER_CURVE`, the CAISO measured-surface arming
block), `data/fleet/assembly.py` (`bins_to_fleet` tranche construction and
`Generator` emission), `model/commitment.py` (`_startup_cost`,
`compute_monthly_markup`), `data/fleet/eia860.py`
(`BIN_STARTUP_COST_PER_MW`), `data/offer_curves.py` (signatures only);
**committed artifacts** — the keeper's `run_config.json`,
`data/raw/reference/caiso_campd_marginal_hr_summary.csv`,
`data/raw/_validation-source/caiso_offer_curve_measured.json`; and the
caiso-238/239/240 assessments, findings and precommits.

**NO FLEET HAS BEEN REBUILT, NO FOOTPRINT MEASURED, NO BOUND EVALUATED, NO LP
RUN.** That is the whole point of the caiso-238 lesson this family keeps
re-learning: **a scalar's VALUE is not its FOOTPRINT**, and route reasoning
without measurement is exactly the error caiso-240 §6/P-1 caught itself making.
Every quantity in §3–§5 is registered against **unmeasured** quantities. The
per-cell bound is deliberately NOT in this file — it is computed after this push
and registered in an **ADDENDUM pushed before any solve**, the caiso-240
two-file pattern.

**§0.3 — HARD STOPS.** Training window only (2023 / 2024 / 2025); if a solve
happens, all three years in **one invocation and one bundle** (rule 16
`[R-ALLYEARS]`), **sequential** (rule 12 `[R-PARALLEL]`). No
`calibration-complete.json`, no `holdout-freeze.json`, no other ISO's keeper
shard or matrix shard touched. **No mechanism armed outside CAISO** (rule 25
`[R-ISO-SCOPE]`) — §1 limb 4 establishes that NYISO and NEISO carry the *same*
defect, and that is an **ASK for those lanes, never an arm here, and never a
value transfer in either direction.** No P2. No off-registry knob (rule 24). No
derive script re-run (rule 23 `[R-FROZEN-DERIVE]`).

**§0.4 — DO-NOT-REDO ACKNOWLEDGED (rule 28(a)).** Re-read in full: caiso-240 §7,
caiso-239 §8, caiso-230 §9. Not re-opened, not re-proposed, and not offered as a
C3a instrument anywhere below:
1. **The measured BID committed multipliers (CC 1.030 / CT 1.166) are NOT armed
   for any CAISO gas class.** The Lever-A refusal stands uniformly on the bid
   route. This session's instrument is the **PHYSICAL** basis
   (`phys_committed` 0.991), which caiso-238 §3 already established is a
   different object — *"That refusal covers the measured bid committed
   multiplier (CT bucket 1.166, self-commitment conduct); grounding on the
   physical min-load burn is the same class of instrument Lever A itself used."*
   The two are deliberately not merged, and 1.166 appears below only as a
   **bracketing fact** (§1 limb 1c), never as a candidate value.
2. **EIA-930's CISO NG cell is never used as a CAISO gas benchmark.** Formally
   corrupt from 2023 (`EIA930_NG_CORRUPT_ONSET`), folds ~13 TWh/yr of
   geothermal + biomass, drifts +10.5 % → +21.1 % → +32.8 % against two records
   that agree within 2.3 %. The valid benchmark is the plant-level
   EIA-923 / CAMPD pair, and it is what every volume number below is measured
   against.
3. **`_DEFAULT_HR_MULT_BY_GROUP` is not re-censused** (all 28 cells × 6 keepers
   × 3 years measured, `_caiso240_default_hr_mult_census.json`, both method
   falsifiers passing); **the five gas `mr` literals are not re-proposed** (dead
   by construction — `bins_to_fleet` builds a must-run tranche only for non-CHP
   coal); **`ST_GAS:econ` is not armed by picking a ramp endpoint**; and
   **`ST_GAS_PEAKER_PLANTS`'s offer scope is not split as posed** (the
   admissible move remains the byte-identity rename, ASSESSMENT-caiso240 §7.3).
   None of these is this session's object.
4. The whole caiso-229 / 230 / 233 / 234 / 235 / 224 / 221 closure list; the
   W-1/W-2/W-3 sweep, **DATED** to the Order-881 AAR effective date
   (≤ 2026-12-01) and **not swept here**.

**§0.5 — PROCESS DEVIATION, DECLARED: NO CONTROL ARM.** Standing owner directive
recorded at caiso-231 (*"that's one in like 1000 runs … I don't want to measure
drift"*): a single-delta calibration arm is solved ONCE and scored against the
committed keeper. **G-CTRL is not a spent LP run.** §5 records the price this
directive charges *this particular* arm, and flags it to the owner — see §0.6(2).

**§0.6 — TWO INHERITED GATE-SPEC CORRECTIONS, ADOPTED HERE, NOT RE-DISCOVERED.**

1. **THE caiso-230 §H FORM IS NOT A STRICT UPPER BOUND.** caiso-230, caiso-231
   and caiso-239 all describe it that way; **caiso-240 FALSIFIED it** — its 2024
   leg under-predicted by 4.5× (+0.0011 predicted vs +0.0049 measured). §H sums
   only over zone-hours where the repriced rung is **itself** the matched
   marginal rung and is structurally **blind to indirect re-dispatch**. It
   over-predicts when the repriced rung's own marginal hours dominate and
   **under-predicts when displaced energy lands on rungs already marginal
   elsewhere**. **This session's arm is squarely in the second regime by
   construction**: it lowers a band on a class that is 66–90 % absent, so the
   dominant channel is energy *attracted into* a class that is currently not
   running, i.e. re-dispatch, not re-pricing of an already-marginal rung. §3
   therefore **does not use §H as a ceiling**. It states the bound
   **TWO-SIDED** and replaces the direct leg's estimator with a
   **crossing-envelope estimator (§H′)** that can see re-dispatch, and says
   exactly why (§3.1).
2. **G-CTRL AS "ONE `run_config` FIELD DIFFERS" IS UNSATISFIABLE** against any
   keeper more than a day old (caiso-239 measured 22 differing fields, every one
   HEAD drift). caiso-240 re-specified it as a **dispatch-identity** check in a
   year where the mechanism is measured inert. **THIS ARM IS EXPECTED TO BE LIVE
   IN ALL THREE YEARS** — it reprices a tranche that exists in every year
   regardless of whether it dispatches — **so the dispatch-identity leg has no
   inert year to bind on, and under the caiso-231 no-control-arms directive this
   session has NO independent dispatch-level check at all.** This is exactly the
   gap caiso-239 §6.1 raised, that caiso-240 §6.3 did not have to answer, and
   that this session **does**. It is **FLAGGED TO THE OWNER** (§5, G-CTRL) and
   the substitute is registered in advance: a **pre-solve FLEET-IDENTITY proof**
   (G-STRUCT), which establishes the mechanism's footprint exactly but **cannot**
   establish that nothing else drifted between the keeper's `git_sha` and HEAD.
   That limitation is stated now, not after a miss.

**§0.7 — THE DIRECTION IS FAVOURABLE TO THE SOLE FAILING GATE. THIS IS A
DISCLOSURE, NOT AN ARGUMENT, AND IT IS THE SESSION'S PRINCIPAL HAZARD.**
Lowering `CT_PEAKER.committed` toward its measured basis is expected to (a)
raise CT_PEAKER volume — a C1 improvement on a class missing by 66–90 % — and
(b) put a cheaper rung into the evening merit order, pushing C3a **DOWN** in
hours it is over (required move 0.00 / −0.848 / −1.893 $/MWh). Per rule 1
`[R-STRUCT]` **that is not an argument for the repair, and this object must never
be presented or re-proposed as a C3a lever.** It is a rule-14 `[R-ACCURATE]` /
rule-21 `[R-DOF]` grounding of a fitted scalar against its own measured
counterpart and is argued and gated as one throughout.

**The inverse hazard is named because it is the real one:** a favourable
direction makes it easy to stop checking. Two counter-measures are registered
here, before any measurement:
* **§4's predictions are written to be uncomfortable.** P-2 predicts the arm
  does **NOT** close the volume gap; P-4 predicts a specific *smaller-than-naive*
  price effect; P-6 predicts the arm is **not** the CT_PEAKER defect's dominant
  cause. Each has a falsifier that fires in the direction that would flatter the
  session.
* **The promotion rule (§5.9) does not key on C3a at all.** A C3a improvement is
  reported and is explicitly **NOT** part of the promotion basis.

**§0.8 — FUNDING STATUS: THE LANE IS AT TERMINAL REST, AND THIS FILE IS THE
FUNDING CASE, NOT A SPEND.** caiso-201/222 Q1 put the CAISO calibration lane at
terminal rest: **no further CAISO calibration session without new funded data.**
caiso-240's CT_PEAKER measurement is new evidence and is the funding case.
**THEREFORE: this session pushes the ruling (§1), the design (§2), the bound
estimator (§3), the predictions (§4) and the gates (§5), and STOPS BEFORE THE
SOLVE pending an explicit owner decision to fund it.** Everything that does not
depend on that answer is delivered first. No LP is run under this precommit
without that decision on the record.

---

## §1 — THE ADMISSIBILITY RULING

### §1.0 — The question, stated exactly

`_CAISO_OFFER_CURVE["CT_PEAKER"]["committed"] = 1.35` is a fitted scalar. Its
own band dict carries a measured physical counterpart,
`phys_committed = 0.991` (`caiso_campd_marginal_hr_summary.csv`,
`avg_committed_p50`, **n = 75**, IQR **[0.969, 1.085]**). **Is substituting the
measured value for the fitted one inside the caiso-238 F4 / Lever-A refusal?**

### §1.1 — VERDICT: **OUTSIDE THE REFUSAL.**

Five independent limbs. Limbs 1 and 2 are already adjudicated in the codebase
and are cited, not re-argued. Limbs 3, 4 and 5 are **new**, and any ONE of them
would carry the ruling alone.

---

**LIMB 1 — THE REFUSAL IS ROUTE-SCOPED, AND caiso-238 SAID SO IN THE SAME
DOCUMENT THAT ISSUED THE F4.**

caiso-238 §3 Q3/Q4, on `ST_GAS.committed`:

> *"`phys_committed = 1.683` … is a **physical burn** measurement, not bid
> conduct — so it is **not** the object the Lever-A lesson withholds. That
> refusal covers the measured **bid** committed multiplier (CT bucket 1.166,
> self-commitment conduct); grounding on the physical min-load burn is the same
> class of instrument Lever A itself used when it set 1.00 as 'still
> CONSERVATIVE vs the true (>avg) min-load HR'."*

caiso-238 graded the five committed bands **F4 at the bid route** and, **in the
same assessment**, graded a committed band **F1 — GROUNDABLE NOW** at the
physical route. The F4 is a grade on an **instrument**, not a quarantine on a
**band**. This session's instrument is the physical one.

**(1c) A BRACKETING FACT, recorded and then set aside.** The measured *bid*
committed for the CT bucket is **1.166** (`caiso_offer_curve_measured.json`
`CT_PEAKER.unarmed.committed` — deliberately held in an `unarmed` block).
So `1.350 > 1.166 > 0.991`: **the armed value sits above BOTH measured
counterparts.** The *direction* of the repair is therefore invariant to which
measurement route one accepts; only the *value* depends on it, and under
DO-NOT-REDO 1 the value is the physical one. 1.166 is **not** a candidate here.

---

**LIMB 2 — LEVER A'S OWN STATED GROUND REFUSES 1.35, SYMMETRICALLY. READING THE
REFUSAL TO PROTECT 1.35 INVERTS IT.**

Lever A's ground, in `_CAISO_OFFER_CURVE`'s own words (CC_REGULAR comment):

> *"any avoided-startup credit belongs in an explicit UC layer, not the P1
> offer (rule #1; DOF ledger E8)."*

That is a rule against pricing **commitment conduct** into the P1 offer — in
**either direction**. And `_CAISO_OFFER_CURVE`'s own comment on the value at
issue reads:

> *"The committed min-load **start-cost hurdle** is lowered from the ERCOT 1.55
> (which parks peakers idle) to 1.35 (NYISO-grounded): CAISO's fast-start CTs
> and aeroderivatives serve the steep net-load evening ramp and should clear on
> the ramp rather than forcing the CC duct-fire + startup tranches to set the
> evening price."*

**1.35 IS commitment conduct priced into the P1 offer, by its author's own
description.** Lever A removed a *sub-cost* commitment adder that emulated
commitment downward; 1.35 is a *supra-cost* commitment adder that emulates
commitment upward. Reading the refusal as protecting it produces the absurdity
that the rule preserves an unidentified commitment adder **because** it is
unidentified, while withholding the identified measurement that would retire it.

---

**LIMB 3 — NEW: rule 19 `[R-ONE-MECH]` DOUBLE-COUNT, ON THE MODEL'S OWN TERMS.**

The `_committed` tranche is **the only tranche that carries the plant's start
cost.** `bins_to_fleet`'s docstring:

> *"`_committed` — the part-load range when started. **Carries the bin's start
> cost and min-run window — starting this tranche is starting the plant.**"*
> … *"Economic and Peaking are incremental loading of a running unit, so they
> **carry neither a start cost nor a min-run window**."*

And the model **already prices that start cost, explicitly and by an identified
parameter**:
* `assembly.py` emits the committed tranche with
  `startup_cost_per_mw = BIN_STARTUP_COST_PER_MW["CT_PEAKER"] = $20/MW`, cited
  to **NREL/SR-5500-55433 (Kumar et al. 2012)**;
* **P1 is defined as base cost + amortized startup markup** (CLAUDE.md, Dispatch
  & Commitment), and `commitment.compute_monthly_markup` applies
  `markup = startup_cost / avg_run_length` to that tranche, from the **P0**
  run pattern, with **no CT exemption** (the exemptions are CHP, warm-boiler
  coal, and gas-steam-under-a-gate).
* On this keeper `tranche_startup_amortization = False`, so the committed
  tranche is the **sole** carrier of the startup markup — the double-count is
  concentrated on exactly the band at issue, not diluted across the class.

So the committed tranche carries **two** start-cost mechanisms:
| | mechanism | identified? | responds to conditions? |
|---|---|---|---|
| (a) | P1 amortized startup markup, `$20/MW ÷ P0 run length` | **YES** — NREL SR-5500-55433 | **YES** — re-amortizes on the P0 run pattern each month |
| (b) | the offer band's `committed = 1.35` "start hurdle" | **NO** — uncited, circular (limb 4) | **NO** — a fixed multiplier |

Rule 19 `[R-ONE-MECH]`: *"Before adding a floor/bridge, enumerate what already
[prices] the same class … and replace or reconcile — never stack a new
[mechanism] on the unexplained residual of an old one."* Grounding (b) to its
physical basis **removes the unidentified limb and leaves the identified one**.
That is rule 19 executed, not evaded — and it is the reason a zero offer-curve
margin on this band is *correct* rather than incoherent (§2.3).

*(Third mechanism, recorded for completeness and NOT touched: the keeper also
arms `caiso_ra_mustoffer` / `caiso_ra_startup_bridge` /
`caiso_ra_bridge_startup_aware`, a P1-native commitment bridge. This session
does not go near it; it is named so the rule-19 enumeration is complete.)*

---

**LIMB 4 — NEW: rule 25 `[R-ISO-SCOPE]`. THE VALUE'S PROVENANCE IS A THREE-WAY
CITATION RING WITH NO MEASUREMENT IN IT.**

`committed = 1.35` on `CT_PEAKER` appears **three times** in
`backcast_config.py`, in three ISOs' curves, each citing the others:

| ISO | the comment | that ISO's own `phys_committed` | n |
|---|---|--:|--:|
| CAISO | *"NYISO-grounded start hurdle"* | **0.991** | 75 |
| NYISO | *"NYISO/CAISO-grounded evening-ramp start hurdle"* | **0.843** | 70 |
| NEISO | *"NYISO/CAISO-grounded start hurdle"* | **0.985** | 18 |

**Not one of the three cites a measurement; each cites the other two.** Under
rule 25 a multiplier that arrived from another ISO's curve carries no CAISO
warrant, and rule 5 `[R-NO-MAGIC]` is not satisfied by a citation ring.

**And the three ISOs' own measurements agree with each other and disagree with
1.35.** Three independent CAMPD samples (n = 70 / 18 / 75) put the CT min-load
burn ratio at **0.843 / 0.985 / 0.991** — i.e. a simple-cycle CT's min-load heat
rate is ≈ its plant-average heat rate, which is physically coherent (a peaker's
plant average is itself dominated by part-load bursts, so the min-load block is
not a *further* penalty relative to it — unlike a CC, whose measured ratios in
the same artifacts are 1.10 / 1.03). Every one of the three ISOs prices its CT
min-load block at **1.35–1.60× its own measurement**.

**Rule 25 disposition, executed strictly:** this is an **ASK for the NYISO and
NEISO lanes**, filed in §6. **No value crosses an ISO boundary in either
direction** — CAISO arms CAISO's own 0.991 and nothing else, and the NYISO /
NEISO cells stay `U` until their own lanes derive their own values.

---

**LIMB 5 — NEW, AND DECISIVE: THE BAND IS NOW THE CLASS'S MOST EXPENSIVE. THE
MERIT ORDER IS INVERTED — AND THE INVERSION WAS *CREATED* BY APPLYING THE
REFUSAL TO ONE BAND OF FOUR.**

`CT_PEAKER` on the current keeper (`run_config.json`, verbatim):

```
committed 1.350   econ_low 1.145   econ_high 1.166   peak 1.166
peak_ladder [[0.2,1.166] x5]        phys_* 0.991 / 0.686 / 0.710 / 1.0
```

**The committed band is the highest multiplier on the class — above econ_low,
above econ_high, above `peak`, and above every rung of the peak ladder.** The
offer curve does not rise; it is a spike at the bottom of a flat surface. The
min-load block is the most expensive MW a CAISO peaker can offer.

This is the pathology Lever A exists to remove, in mirror image — Lever A's own
words: *"0.90x avg priced the min-load block … below econ_low (0.95) — an
**INVERTED merit order**."* Lever A removed `committed < econ_low`; the keeper
now carries `committed > peak`.

**And it did not exist when 1.35 was set.** At that time the class read
`1.35 / 1.10 / 1.50 / 4.0` — a properly rising curve with 1.35 sitting between
`econ_low` and `econ_high`. The inversion appeared when the **measured static
surface was armed** (`caiso_offer_surface_measured` +
`caiso_offer_surface_measured_ungrounded`, promoted at caiso-231), which
re-grounded `econ_low` / `econ_high` / `peak` on measured bid conduct to
1.145 / 1.166 / 1.166 **while withholding `committed` under the refusal.** The
arming block's own comment states the withholding:

> *"The measured committed band is deliberately NOT armed (the Lever-A inversion
> lesson — commitment conduct belongs to a UC layer, not the P1 offer)."*

**So the refusal, as implemented, produced the opposite of its intent on this
class.** Withholding the measured bid 1.166 — to avoid pricing commitment
conduct into the offer — left standing a **larger, unmeasured** commitment adder
of 1.350, and inverted the class's merit order in the process. A refusal cannot
coherently be read to require maintaining the defect it was created to remove.

*(Falsifiable scoping, and it is what confines this arm to one class: CT_PEAKER
is the **only** CAISO gas class that is (a) armed above **both** its measured
counterparts and (b) inverted at the top. CC_REGULAR 1.000 < peak 1.386;
CC_CHP 1.000 < 1.386; CT_CHP 1.100 < 1.166; ST_GAS 0.810 < 1.166 — all four
rise. CC_REGULAR/CC_CHP/ST_GAS are armed **below** both their measured bid and
their measured physical basis; CT_CHP is armed below its bucket bid. The
scoping is **measured and falsifiable, not chosen** — its falsifier is registered
as P-1.)*

### §1.2 — WHAT THE RULING DOES **NOT** ESTABLISH

Stated here so it cannot be read into the session later:
1. It does **not** establish that this repair closes, or mostly closes, the
   CT_PEAKER volume miss. §4 P-2 and P-6 predict it does **not**. The tranches
   are independent LP generators with `pmin = 0` and no commitment coupling on
   the P1 path, so the committed band does **not** gate the class's econ and
   peak tranches; a story in which repricing it "unlocks" the class is a route
   story and is registered as **falsifiable**, not asserted.
2. It does **not** re-open the bid route, for this or any other class.
3. It does **not** authorise a solve. §0.8 governs that.

---

## §2 — THE MECHANISM

**§2.1 — `ScenarioConfig.caiso_ct_peaker_committed_measured`** — gated, **default
off**, CAISO-gated, threaded onto `--replay-bundle`, registered in
`_BACKCAST_ONLY_OVERLAY_FIELDS` only if it fails the rule-13 forward test — it
does **not**: `avg_committed_p50` regenerates for a forward year from CAMPD
conduct and responds to fleet change, so it is a **rule-13-admissible measured
input in both modes** and is **not** a backcast-only overlay. *(This differs from
caiso-240's sibling, which armed measured OASIS **bid** conduct.)*

**§2.2 — ZERO NEW NUMBERS ANYWHERE.** The arm sets

```
offer["committed"] := offer["phys_committed"]        # CT_PEAKER, CAISO only
```

reading the value the band dict **already carries**, already cited to
`caiso_campd_marginal_hr_summary.csv`, already frozen under rule 23
`[R-FROZEN-DERIVE]`. There is no new literal, no new registry constant to
choose, and no endpoint to pick. It is the strictest available form of a rule-14
`[R-ACCURATE]` substitution: **a fitted scalar retires to the measured
counterpart already resolved onto its own band.**

* A CAISO `CT_PEAKER` band without a `phys_committed` key is a **hard error**,
  never a silent no-op.
* The gate is **CAISO-only**; another ISO arming it is a **hard error** at the
  config gate (rule 25) — NYISO's 0.843 and NEISO's 0.985 are their lanes' to
  arm, from their own artifacts, in their own sessions.
* **Band-disjoint** from its caiso-239 (`ST_GAS.mc` via the bypass) and
  caiso-240 (`ST_GAS:peak` via the bypass) siblings, and from the caiso-231
  measured surface (which arms `econ_low`/`econ_high`/`peak` only, never
  `committed`). A unit test pins that arming all four moves exactly four
  disjoint band sets.

**§2.3 — THE ONE REAL DESIGN OBJECTION, ANSWERED IN ADVANCE.**
`gas_offer_net_revenue_margin` computes `markup_hr = max(0, mult − phys) ×
base_hr` and prices it as a fuel-invariant `markup_hr × anchor`. Setting
`mult := phys` drives this band's markup to **exactly 0**, so the committed
tranche would offer at bare measured physical cost while every other CAISO gas
tranche offers at bid with a compressed margin. caiso-240 §5.1 named precisely
this asymmetry as a reason to refuse an analogous ST_GAS move, so it must be
answered, not stepped around.

**It is answered by limb 3, and the answer is the point of the repair.** The
economically correct offer-curve margin on a *min-load block* is its
**commitment cost**, and P1 supplies that separately and by an identified
parameter (`$20/MW ÷ P0 run length`, NREL SR-5500-55433). Under the current
config the band carries **both**. Driving the offer-curve margin to zero leaves
**exactly one** mechanism pricing commitment on the tranche that the code says
*is* the commitment tranche. The ST_GAS `econ` case caiso-240 refused is
different in kind: an **econ** band's margin is competitive net revenue, for
which P1 supplies no substitute, so zeroing it there would leave the phenomenon
unpriced. Here zeroing it leaves the phenomenon priced **once**.

**§2.4 — WHY NOT 1.00 (the "conservative Lever A value").** Rejected as a **free
parameter**. Lever A's 1.00 was justified by *"still CONSERVATIVE vs the true
(>avg) min-load HR"* — a rationale that depends on min-load HR exceeding plant
average. For CT_PEAKER the measurement says the opposite (0.991 < 1.0, IQR
[0.969, 1.085]), so the Lever-A rationale does not transfer, and adopting 1.00
would be choosing a number rather than measuring one. Rule 21 `[R-DOF]`: a
value that can only be reached by choosing it is not a parameter, it is an open
issue.

**§2.5 — DOF.** −1 fitted scalar (the circular 1.35 retires to measured).
`n_residual` 6 → 5 **only if** the entry is a distinct ledger row; the DOF
counter reads `offer_curve_by_group`, so unlike the last three sessions' arms
this one **is** in the counter's scope. **P-7** registers the prediction.

---

## §3 — THE ADVERSE/FAVOURABLE BOUND: TWO-SIDED, WITH ITS ESTIMATOR NAMED

**§3.1 — §H IS NOT USED AS A CEILING, AND WHY.** Per §0.6(1), the caiso-230 §H
form counts only zone-hours where the repriced rung is **itself** the matched
marginal rung, and caiso-240 measured it under-predicting by 4.5× in exactly the
regime this arm sits in. This arm **lowers** a band on a class that is 66–90 %
absent: its dominant channel is **energy attracted into a class that is not
currently running**, i.e. indirect re-dispatch, which §H cannot see. Using it as
a ceiling here would be quoting it wrongly, which is the caiso-240 correction's
whole content.

**I replace the estimator rather than merely widening §H**, and the replacement
is stated before it is evaluated.

**§3.2 — THE CROSSING-ENVELOPE ESTIMATOR (§H′).** Computed from the keeper's
**committed** `hourly/` sidecars only (`class_hourly_<year>.parquet`,
`system_<year>.parquet`) plus the rebuilt fleet — **no LP run**. For each
zone-hour `(z, t)` and each CAISO `CT_PEAKER` `_committed` tranche `g`:

```
mc_old(g,t) = 1.350 × HR_g × fuel(g,t) + (1.350 − 0.991) × HR_g × anchor + adders(g,t)
mc_new(g,t) = 0.991 × HR_g × fuel(g,t) +          0                      + adders(g,t)
crossing(g,z,t) = 1{ mc_old(g,t) > p(z,t) ≥ mc_new(g,t) }
```

(`adders` = VOM + CARB carbon + NOx, identical on both sides and therefore
cancelling from the *crossing test's* threshold only where it is a pure
difference; they are carried explicitly, not netted, so the level is right.)

* **Magnitude envelope** `B(z,year) = mean_t [ (p(z,t) − mc_new(g*,t))⁺ ·
  crossing ]`, capacity-weighted across the tranches, where `g*` is the
  cheapest crossing tranche in the hour. This is the price fall **if the
  repriced tranche sets price in every hour it newly clears** — the maximum the
  channel can deliver.
* **Two-sided interval, signed:** `ΔP̄(year) ∈ [ −B(year), +ε ]` with
  `ε = +0.05 $/MWh`, the small positive allowance for the genuine possibility
  that re-commitment raises price somewhere (a cheaper peaker rung can shift
  storage and hydro scheduling, and nothing guarantees a one-signed outcome).
* **Both endpoints are live falsifiers.** A measured mean price move **below
  −B** falsifies the envelope (the channel delivered more than its maximum ⇒ the
  estimator or the mechanism is wrong). A measured move **above +ε** falsifies
  the sign (the arm moved price the *unexpected* way at material size).
* **Degeneracy is declared in advance** (inherited correction §0.6(2), caiso-239's
  second gate-spec defect): if a year has **zero** crossing zone-hours, `B = 0`
  is reported as *"zero to within the estimator's attribution tolerance"*, never
  as an exact zero, and a small measured move in that year is a **bound-form
  limitation, not a falsification**.
* **A bound violation is a defect in the estimator or the mechanism, reported as
  such, and is NEVER RE-FITTED.** The envelope is pushed to `origin` in the
  ADDENDUM before any solve.

**§3.3 — WHAT §H′ STILL CANNOT SEE, STATED NOW.** It prices the *crossing*
directly, so it sees energy attracted into the repriced tranche — the channel §H
misses. It still cannot see (i) second-order re-dispatch among *other* classes
that the CT's new energy displaces, (ii) storage/hydro re-scheduling, or (iii)
any change in which hours are scarce. It is therefore an envelope on **one
dominant channel**, not a proof. That is why it is stated two-sided with a
positive tolerance rather than as a bound.

---

## §4 — PREDICTIONS, EACH WITH ITS FALSIFIER (registered before any measurement)

Written to be uncomfortable (§0.7). Scored against interest in the FINDING.

| # | prediction | falsifier |
|---|---|---|
| **P-1** | **The scoping is measured, not chosen.** On the rebuilt fleet, `CT_PEAKER` is the ONLY CAISO gas class whose armed `committed` exceeds both its `phys_committed` and the measured bid for its bucket, AND the only one with `committed > peak`. | Any other live CAISO gas class satisfies either condition. |
| **P-2** | **THE ARM DOES NOT CLOSE THE VOLUME GAP.** CT_PEAKER's model capacity factor rises but stays **below half** the measured actual in at least two of the three years (i.e. model CF < 3.7 / 3.8 / 2.1 %). The committed band is not a gate: the econ and peak tranches are independent `pmin = 0` LP rows and are already cheaper. | CT_PEAKER CF reaches ≥ half the actual in two or more years. |
| **P-3** | **The committed tranche is a minority of the class's capacity.** `Pct_Committed` for CAISO CT plants puts < 25 % of `CT_PEAKER` grid capacity in `_committed` tranches. | ≥ 25 %. |
| **P-4** | **The price effect is materially SMALLER than the raw multiplier ratio suggests.** Because `gas_offer_net_revenue_margin` re-expresses the 1.35→0.991 move as the loss of a **fixed** `$≈18.7/MWh` margin plus a fuel-scaled reduction, and because the committed band was only ≈ $2/MWh above `econ_low` at 2024 fuel *after* that decomposition, the measured annual mean price move is **smaller in magnitude than 0.35 $/MWh** in every year. | \|ΔP̄\| ≥ 0.35 $/MWh in any year. |
| **P-5** | **G-STRUCT is exact.** Exactly the CAISO `CT_PEAKER` `_committed` rows change, at the exact heat-rate ratio 0.991/1.350 = **0.734074074074**, with `offer_markup_hr` → exactly 0.0 on those rows and unchanged on every other row; 0 rows in any other class, band, or ISO. | Any row moves at any other ratio, or any non-`CT_PEAKER`-committed row moves. |
| **P-6** | **THE ARM IS NOT THE DOMINANT CAUSE OF THE CT_PEAKER DEFECT.** After the arm, the residual CT_PEAKER volume miss remains the largest single-class gas miss in at least two of the three years — i.e. the caiso-240 object survives this repair and a further root cause is still open. | CT_PEAKER ceases to be the largest single-class gas miss in ≥ 2 years. |
| **P-7** | **The DOF ledger DOES move this time.** Unlike the last three arms (whose retired literals lived in `campd_bins.py`, outside `_count_scalars`), this one retires a scalar inside `offer_curve_by_group`, which the counter reads — so `n_residual` falls by 1 (6 → 5) or the fitted count falls by 1. | The ledger is unchanged. |
| **P-8** | **No inert year exists.** The mechanism is live (non-byte-identical class energy) in all three years, so the §0.6(2) dispatch-identity leg of G-CTRL cannot bind and the owner flag stands. | Any year reproduces the keeper to within 0.001 TWh in every class. |

---

## §5 — GATES, EACH WITH ITS FALSIFIER

**G-STRUCT** — *pre-solve fleet-identity proof.* Rebuild the CAISO fleet flag-off
and flag-on at HEAD, all three years, and diff every row. **PASS** iff exactly
the `CT_PEAKER` `_committed` rows change, at ratio 0.734074074074, with
`offer_markup_hr` → 0.0 on those rows only, 0 rows elsewhere in any band, class
or ISO. **FALSIFIER:** any other row moves, or any row moves at another ratio.
*This is the substitute for the missing dispatch-level control (§0.6(2)); it
proves the footprint, not the absence of HEAD drift.*

**G-INERT** — **PASS** iff the arm is **not** byte-identical to the keeper (a
measured mechanism that changes nothing is a wiring failure, per caiso-239).
**FALSIFIER:** all three years reproduce the keeper exactly.

**G-CTRL** — **EXPECTED UNSATISFIABLE, AND FLAGGED TO THE OWNER RATHER THAN
QUIETLY DROPPED.** The `run_config` field-diff form is dead against a keeper
more than a day old; the caiso-240 dispatch-identity form needs an inert year and
P-8 predicts there is none. **Reported as `NOT AVAILABLE — no inert year`**, with
G-STRUCT standing as the fleet-level substitute. **FALSIFIER of the report:** an
inert year exists (P-8 falsified), in which case the dispatch-identity leg is run
and scored as caiso-240 specified. **This is caiso-239 §6.1's open item reaching
the case it was raised for; the owner is asked in §6 whether the no-control-arms
directive should carve out an arm that is live in every year.**

**G-C1** — **PASS** iff the C1 verdict does not regress (12/12, free 8/8).
CT_PEAKER volume is expected to improve; that is reported, never argued from.
**FALSIFIER:** any C1 leg regresses.

**G-C3a** — **TWO LEGS.** *Verdict leg:* **PASS** iff no year's C3a verdict flips
**adversely** (2023 must stay PASS). *Envelope leg:* **PASS** iff the measured
annual mean price move lies inside `[−B, +0.05]` per §3.2. **FALSIFIERS:** an
adverse verdict flip; or a move outside the interval. **A favourable C3a move is
reported and is explicitly NOT part of the promotion basis (§5.9).**

**G-C3b** — **PASS** iff unchanged or improved. **FALSIFIER:** any regression.

**G-C8** — **PASS** iff the forced-share budget verdict is unchanged. Note the
arm reduces an *offer* level and adds no floor, so no mechanism enters D-2/D-4.
**FALSIFIER:** any material class crosses its cap, or a new mechanism appears in
the D-2 attribution.

**G-CAVEAT** — **PASS** iff the caveat budget is unchanged: **1 of 1** ledgered
(C3c alone) and **0** protective. **FALSIFIER:** a second ledgered caveat or any
protective caveat appears.

**G-C6** — attestation regenerated (an unattested C6 makes C3c FAIL rather than
CAVEAT). **FALSIFIER:** attestation absent or failing.

**§5.9 — THE PROMOTION RULE, FIXED BEFORE THE SOLVE.** Promote to keeper **iff**
G-STRUCT, G-INERT, G-C1, G-C3b, G-C8, G-CAVEAT and G-C6 pass **and** G-C3a's
**verdict** leg passes. **The promotion basis is structural: one uncited,
cross-ISO-circular scalar retires to CAISO's own measured counterpart, removing a
rule-19 double-count and a class-internal merit-order inversion, with zero free
parameters.** A C3a improvement, if any, is **reported and excluded from the
basis** (rule 1 `[R-STRUCT]`, §0.7). An envelope-leg failure is **disclosed as an
estimator or mechanism defect and never re-fitted** (§3.2). The owner's standing
standard — *"if structural integrity improves but gates regress that may still be
a keeper"* — applies as written.

---

## §6 — DELIVERABLES, AND THE ASKS

**This session delivers:** this precommit; an **ADDENDUM** carrying the evaluated
§H′ envelope, pushed **before any solve**; the G-STRUCT fleet-identity artifact;
and — **only if the owner funds it (§0.8)** — the arm, its bundle, its dashboard
registration (rule 15, same session, keeper or rejected probe), its matrix base
row + CAISO cell (rule 28(b)/(c)), and a FINDING scoring §4's predictions against
interest.

**ASKS PUT TO THE OWNER:**
1. **FUND THE SOLVE?** The lane is at terminal rest (caiso-201/222 Q1). §1 rules
   the object admissible and §2 shows it costs zero free parameters. The solve is
   ~65 min of LP plus the post-solve chain. *(§0.8.)*
2. **THE NO-CONTROL-ARMS DIRECTIVE vs AN ARM LIVE IN EVERY YEAR.** caiso-239
   §6.1 raised it, caiso-240 §6.3 escaped it, this arm meets it. Should the
   directive carve out a dispatch-level control for an arm with no inert year, or
   is the G-STRUCT fleet-identity proof sufficient? *(§0.6(2), G-CTRL.)*
3. **NYISO AND NEISO CARRY THE SAME DEFECT** — the identical uncited `1.35`
   against their own measured 0.843 (n=70) and 0.985 (n=18), with the same
   mutually-citing comments. Under rule 25 these are **their lanes' asks**; this
   session arms neither and transfers nothing. *(§1 limb 4.)*
4. **THE CT_PEAKER OBJECT LIKELY SURVIVES THIS REPAIR** (P-2, P-6). If it does,
   the remaining root cause is a separate, larger object and needs its own
   funding decision.

**STILL OPEN, NOT FUNDED, NOT STARTED:** caiso-238 object 4
(`battery_dispatch_adder` → measured AS reservation + ATB degradation; F2, the
strongest standing ask, materiality COMPOUNDING li-ion 1.87 → 5.29 % of
generation); object 3 (own-curve shape derive); the SoCalGas OFO arm
(`PRECOMMIT-caiso227-ofo-arm-2026-08-31.md`); the `IMPORT_TRANCHES[CAISO]` LEVEL
object; the `ST_CHP` cross-ISO asks and the `COAL:mr` citation ask (rule 25 —
other lanes').
