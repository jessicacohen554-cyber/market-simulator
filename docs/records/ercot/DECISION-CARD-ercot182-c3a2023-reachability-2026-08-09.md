# DECISION CARD — ercot-182: is C3a-2023 reachable, and if not, what does ERCOT do?

**For the owner sitting. Session ercot-182, 2026-08-09, HEAD `ae7bd5e`.
NOTHING IS DECIDED HERE.** No lever was proposed, no `ScenarioConfig` field
added, no derive run, no LP solved, no run registered, no matrix cell minted,
the ERCOT keeper is untouched. Every number below is read off committed
artifacts — no re-derivation, no replay, no new measurement.

Scope: ERCOT only (rule 25). ERCOT holds **no `complete` and no `final`
marker** (`frontend/data/backcast/calibration-complete.json` — `complete` =
{NEISO, NYISO, PJM}, `final` = {}), so every year referenced is inside
{2023, 2024, 2025} (rule 22).

---

## 0. The record this card is written against

**Keeper: `2026-08-09-run181-position-tail`** (bundle
`results/calibration/ercot181_positiontail_B`), promoted at ercot-181.

> Determination **NOT-YET**, fail set **{C3a, C3b}**; C3a-2023 **−32.4 %**
> (2024/2025 PASS, 2025 at −9.1 %), C3b-2023 **0.602**, C3b-2024 **0.205**;
> C1/C2/C4/C6/C8 PASS; C3c ledgered CAVEAT ×3 at tail counts
> **61/181, 25/53, 3/31**. Shed 4/2/0.

*Provenance note.* This session opened at `ae7bd5e`, where the ercot-181
registration had not yet landed; it merged as PR **#3792** (`e63559f`) while the
card was being assembled, and the card was rebased onto it and re-checked against
the landed record. That record is now complete and self-consistent: control
`2026-08-09-run181-control-positiontail-pair` (reproduces run176 **array-equal**
in all three years), arm `2026-08-09-run181-position-tail` (**PROMOTED**), both
registered with all three years;
`FINDING-ercot181-position-tail-2026-08-09.md` committed; matrix cell
`ercot_offer_surface_position_tail` stamped `O → K`; log entry appended.
**Nothing in this card's analysis turns on the change**: the arm is
INERT-ON-THE-OBJECT (22 spring 2023 hours move +$0.006..+$0.57; annual
load-weighted **+$0.0004/MWh**) and **every scored criterion, tail count and shed
count is identical to the run176 control**, so the determination this card prices
is numerically the same one either way.

**Charter:** `FINDING-ercot181-position-tail-2026-08-09.md` §9 — *"ESCALATED: an
owner sitting on C3a-2023 reachability within this model class (the C3c-caveat
path) … the sitting must either amend the rubric, accept NOT-YET as ERCOT's
standing state, or authorize a model-class change such as sub-hourly/
cliff-resolving price formation."* Those are options (a), (b), (c) below.

---

## 1. THE QUESTION

> **May C3a-2023 join the accepted-limitation ledger?**

C3a is **LOAD-BEARING** tier. The scorer refuses model-class ledgering there
twice over, independently:

**Guard 1 — the v3.0 tier guard** (`calibration_verdict.py::_apply_ledger`):

> *"a model-class entry is admissible ONLY for a SUPPORTING-tier criterion;
> matched against a load-bearing or protective criterion it is ignored and the
> FAIL stands. Owner acceptance of a model-class limit never waves through the
> certifying or anti-self-deception tiers."*

**Guard 2 — the v3.1(a) owner amendment of 2026-08-06**, which narrowed
`LEDGERABLE_CRITERIA` to `{"price_tail"}` and named this exact case in its
rationale:

> *"Every other criterion is two-band scored against a published comparable,
> and for those the band IS the certification claim — **C3a mean LMP most of
> all: a mean-LMP miss beyond ±10 % is a MODEL MISS, and ledgering it certified
> a price level the model does not reproduce.**"*

So the answer under the rubric as written is **no**, and it is `no` by
fail-closed construction: an entry naming `price_mean` is ignored whatever its
kind or reason. Changing that is an owner amendment, not a session action —
which is why the three options below are the actual subject of the sitting.

**The magnitude at stake.** C3a-2023 is −32.4 % against a ±10 % band —
**3.2× the band**, not a graze. Closing it means moving the 2023 annual
load-weighted mean from **$43.45 to ≥ $57.89** (+$14.44/MWh, 69 % of the annual
$-gap), concentrated in ~50–180 summer-afternoon hours (ercot-177 §1/§7).

---

## 2. THE DECISIVE ARITHMETIC — a C3a carve-out changes ERCOT's determination by NOTHING

**This is the single most important fact in the card, and it should be settled
before the three options are debated on their merits.**

ERCOT's fail set is **{C3a, C3b}**, and criterion status aggregates over years:

| criterion | tier | 2023 | 2024 | 2025 | ledgerable? |
|---|---|---|---|---|---|
| C3a mean LMP (±10 %) | LOAD | **FAIL −32.4 %** | PASS | PASS (−9.1 %) | no (v3.0 + v3.1) |
| C3b price shape (NRMSE ≤ 0.20) | LOAD | **FAIL 0.602** | **FAIL 0.205** | PASS | no (v3.1) |
| C3c price tail | SUPPORT | CAVEAT 61/181 | CAVEAT 25/53 | CAVEAT 3/31 | **yes** — already spent |
| C1, C2, C4, C6, C8 | — | PASS | PASS | PASS | — |

Consequences:

1. **Carving out C3a-2023 alone leaves C3b failing in two years.** ERCOT stays
   **NOT-YET**. The amendment buys nothing.
2. **Carving out the whole 2023 object (C3a-2023 + C3b-2023) still leaves
   C3b-2024 (0.205).** ERCOT stays **NOT-YET**.
3. C3b-2024 is **a different root entirely** — the two 2024 shed hours the model
   over-amplifies to VOLL, whose only named structural route is the ercot-172
   fault-3 partial-layer re-charter, **FROZEN** behind
   `docs/handoffs/DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md`
   (ercot-177 §7). It is an adjudicated *mechanism collision awaiting an owner
   ruling*, not a model-class limitation, so it is not carve-out-eligible on any
   honest construction.

**Therefore: the only path by which ERCOT's determination can move at all is
closing BOTH the 2023 price object AND C3b-2024 on the merits.** Every ledgering
option is determination-neutral for ERCOT today. What a C3a amendment would
actually change is the *rubric*, for all six ISOs, for zero ERCOT gain.

A second, independent objection to any C3a/C3c-linked carve-out: ercot-177 §7
establishes that **"C3a-2023 and C3c-2023 are the same object."** If they are the
same object, the C3c model-class entry has *already absorbed* that limitation and
already spent the single ledgerable slot (`MAX_LEDGERED_CAVEATS = 1`). Ledgering
the same limitation a second time on a load-bearing criterion is not a carve-out
— it is counting one accepted limit twice across two tiers, which is precisely
what the tier split exists to prevent.

---

## 3. OPTION (a) — a scoped rubric amendment (C3a regime-year carve-out)

**What it is.** Admit a C3a FAIL to the ledger in a year where C3c already
carries a model-class entry and the C3a miss is demonstrated to be the same
object, i.e. a *dependent* model-class caveat.

**The rubric text it requires.** Two coordinated changes to
`scripts/calibration_verdict.py`, both owner-signed:

```python
# v3.3(a) OWNER AMENDMENT <date> — DEPENDENT MODEL-CLASS CAVEAT.
# LEDGERABLE_CRITERIA gains "price_mean", admissible ONLY as a dependent
# entry: kind "model-class-dependent", scoped to a single year, admissible
# iff (i) C3c in the SAME year already carries a model-class entry or the
# standing rule, (ii) the entry cites a committed same-object demonstration,
# and (iii) the dependent entry consumes its OWN ledger slot.
LEDGERABLE_CRITERIA = frozenset({"price_tail", "price_mean"})
MAX_LEDGERED_CAVEATS = 2  # the dependent entry cannot be free

# and, in _apply_ledger, an explicit hole in the v3.0 tier guard:
if entry.get("kind") == "model-class-dependent":
    if rec["criterion"] != "price_mean":
        return rec
    # ... the v3.0 supporting-tier guard is BYPASSED here by construction ...
```

**What it costs, itemised.**

* **It reverses a 3-day-old owner amendment on the amendment's own stated
  grounds.** v3.1(a) did not omit C3a by oversight; it named C3a as the case it
  most meant to exclude. The card cannot present (a) as a refinement of v3.1 —
  it is a repeal of its central clause.
* **It punches the first hole in the v3.0 tier guard.** That guard is what makes
  the C3c standing rule safe (`_apply_c3c_standing_rule`'s docstring rests on it:
  *"it classifies MODEL_LIMIT, which `_apply_ledger`'s v3.0 guard admits only for
  a SUPPORTING-tier criterion, so the rule can never reach C1/C2/C3a/C3b or
  C6/C8"*). Once load-bearing ledgering is reachable by any construction, the
  standing rule's own safety argument no longer holds as written.
* **It raises the caveat budget.** `MAX_LEDGERED_CAVEATS` is 1 today precisely
  because exactly one criterion is ledgerable; a dependent entry needs its own
  slot or it is free, and a free excuse is the thing the budget exists to stop.
* **It certifies a price level the model does not reproduce**, at 3.2× the band,
  in the ISO that is the calibrated reference for the other five.
* **Cross-ISO blast radius:** the guard is rubric-global. CAISO
  (`2026-08-06-caiso-175-tac-intake`, C3a 2024 +11.7 % / 2025 +14.8 %) and MISO
  (`2026-08-05-miso-132b-cc-committed`, C3a 2025 −14.0 %) were moved to NOT-YET
  *by v3.1(a) itself*. A dependent-caveat hole is a live re-litigation path for
  both — a rubric change with three ISOs' determinations downstream of it.
* **And, per §2, it delivers ERCOT no determination change whatsoever.**

**Verdict offered to the owner: refuse.** Maximum cost, zero ERCOT benefit.

---

## 4. OPTION (b) — accept NOT-YET as ERCOT's standing determination and redirect

**What it is.** Record NOT-YET as ERCOT's honest current determination, publish
the C3a-2023 residual as a *named, measured, open* item rather than an excused
one, and point the program at the two things that are actually actionable.

**The rubric text it requires: NONE.** This is the status quo the rubric already
produces. The only artifacts are narrative: this card, the calibration-log entry,
and the keeper note.

**What the redirect targets, in priority order.**

**(b1) C3b-2024 — RULE ON THE FROZEN MEMO.** This is the highest-leverage owner
action available today, and the only failing criterion-year in ERCOT with a
live, named, *unexplored* structural route.
`DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md` has been pending since
2026-08-07. Its own §4/§5 adjudicate the field:

| option | status on the existing record |
|---|---|
| A — keep the product cap, stay frozen | keeps a knowingly-wrong mechanism (rule 1 tension), keeps the 2024 defect |
| B — adopt a composition fix (blanket / unit-scoped `min()`) | both arms already `R`; floods 2023/2025 coal +1–2.7 TWh/yr; fails G-COAL148 at 2–5× |
| **C — re-charter the PARTIAL LAYER's construction first (ercot-172 fault 3)** | **NOT built. The memo's own recommendation. The sole remaining structural route** (ercot-174 §3b item 3) |

The memo's recommendation is C, *"sequenced after the currently-authorized
ercot-151 lane"* — and **both of ERCOT-151's §4 asks are now discharged** (ask
(1) at ercot-157, ask (2) at ercot-176, matrix §5.1 item 19). **The sequencing
precondition is met; only the ruling is missing.** The ruling text the memo
drafts for signature:

> *"The ceiling lane stays frozen for composition-rule work; a fault-3
> partial-layer construction re-charter is authorized as its successor, with
> G-COAL148 carried live."*

**(b2) The rule-18 grain defect — the standing owner item.** Fleet assembly
records unit physics on the **committed tranche only**, so every `econ*`/`peak*`
bid row reads `min_down = min_run = 0`. A rule-18 `[R-PHYSICS]` gate is therefore
**vacuous at tranche-row grain**, and the *armed keeper mechanism*
`ercot_faststart_pool_offer` consequently admits every CT bid row regardless of
physics — its effective scope is the `CT_PEAKER` class map, not the intended
min-down test. Raised at ercot-176 and carried un-acted through ercot-178/180/181
(PRECOMMIT-ercot181 §4: *"CARRIED, NOT TOUCHED"*; FINDING-ercot181 §10 carries it
again unchanged). Source: the ercot-176 keeper note and registry sidecar, and
matrix §5.1 item 19. **Fixing it moves the keeper** and needs its own
pre-registered round. It is a *legitimacy* item, not a residual item: an armed
mechanism whose licensing gate does not bind is a rule-18 defect independent of
whether fixing it improves any metric.

**(b3) Publish C3a-2023 as a bounded open residual**, with the §7 evidence
appendix as its standing measurement, and stop opening offer-side lanes against
it without new evidence (§7.5 DO-NOT-REDO).

**Cost.** ERCOT publicly reads NOT-YET for the foreseeable term, including as
the multi-ISO reference. That is the honest reading and it is what the model
currently earns.

---

## 5. OPTION (c) — charter a model-class change as a costed forecast-lane workstream

**What it is.** Accept that the residual is a property of the model *class*
(hourly, class-aggregate, frictionless-substitution LP) and authorize a study —
**costed before any build** — of a price-formation representation that can
resolve it. Two distinct sub-variants; they are not interchangeable.

**(c1) Sub-hourly dispatch.** Reality's price forms per 5-minute SCED interval
against intra-hour ramp feasibility; the LP clears an hourly average with no
ramp friction between intervals. Costing from committed facts:

* 8,760 → 105,120 periods is **12× the column count** in the flat LP layout
  (`T × (n_gen + 4·n_zones + 3·n_storage + n_links)`).
* A single ERCOT per-plant hourly year already measures **~6.6 GB RSS and
  ~20 min/year** (PRECOMMIT-ercot181 §9), against a rule-12 cap of ~2 concurrent
  per-plant runs on a 15 GB box. 12× is not a tuning exercise — it is a
  different solver-scale program.
* It touches rule 8 `[R-8760]`, the P0→P1 seam, every derive's time grain, the
  bench/scoring calendar, and all six ISOs' inputs.
* **Costing verdict: out of scope for a calibration lane.** If it is entered at
  all it is a spec-level program with its own charter, not a workstream item.

**(c2) Cliff-resolving price formation at hourly grain — the cheaper and better-aimed variant.**
The measured defect is a *resolution* mismatch, and it is visible in committed
code. The model's per-plant economic ramp is sliced into
`offer_curve_smoothing_n = 6` **equal-width** MW slices
(`offer_curves._econ_curve_steps`: `slice_cap = curve_cap / n`), so the finest
within-plant position the model can express is ~1/6 of the econ ramp. Reality's
marginal price forms at **q_act p50 = 0.9976** of the marginal resource's own
submitted curve — inside its top **0.24 %**. (The two positions are defined on
different supports — submitted curve vs tranche ladder — so this is an
order-of-magnitude resolution statement, not an exact ratio. It is roughly two
orders of magnitude.)

The concrete shape of (c2) is therefore **non-uniform slicing: refine the top of
each plant's curve** so the ladder can carry a cliff instead of a diluted mean.
Its known cost, already identified ex ante in PRECOMMIT-ercot181 §2: **row-count
changes move P0** (baked heights enter the base fleet), so it breaches the
offer-surface family's P1-only seam and re-opens commitment. That is why the
ercot-181 lane could not reach it and explicitly declined to.

**What (c) must be charged with delivering *before* any build** (this is the
costing, and it is the whole point of chartering rather than building):

1. A **feasibility + cost memo** — expected column/RSS/wall-clock cost of (c2)
   under the current LP layout; what moves in P0; what re-derives.
2. A **falsifier stated ex ante**, G-SHED PRIMARY: the ercot-48/49
   manufactured-shortage signature has now killed this object **twice** — most
   recently at ercot-178, where +$8.18/MWh of apparent C3a-2023 gain was
   **67.5 % new VOLL shed hours** and only **+$2.62/MWh genuine offer formation**
   (18 % of the +$14.44 bar). Any cliff-resolving form is *more* shed-exposed,
   not less.
3. An **honest reachability statement**: the offer-formation budget of the whole
   conditioning family measured **~$2.6/MWh** against a **$14.44/MWh** bar. A
   charter that does not say up front that (c2) may also land short is not
   costed.
4. **Cross-ISO scope**: a fleet-representation change is not ERCOT-gated by
   construction, so rule 25 compliance is a design constraint, not an
   afterthought.

**Verdict offered to the owner:** (c1) refuse; (c2) admissible **as a costed
study only** — charter the memo, do not charter a build.

---

## 6. RECOMMENDATION

| | option | recommend |
|---|---|---|
| (a) | scoped C3a rubric carve-out | **REFUSE.** Repeals v3.1(a) on its own grounds, holes the v3.0 tier guard the C3c standing rule depends on, exposes CAISO/MISO determinations — **and changes ERCOT's determination by nothing** (§2) |
| (b) | accept NOT-YET, redirect | **ADOPT.** Zero rubric change. Two live targets: rule on the frozen 148/149 memo (option C), and schedule the rule-18 grain defect |
| (c) | model-class workstream | **(c1) refuse. (c2) charter the costing memo only** — no build authorization |

**The one-line reading.** ERCOT's C3a-2023 miss is a *measured, bounded,
correctly-diagnosed* limitation of an hourly class-aggregate LP, and the honest
label for a model that carries it is NOT-YET — not a ledgered caveat that would
certify a price level the model demonstrably does not produce. The program's
returns right now are in C3b-2024 (a frozen ruling, not a research problem) and
in the rule-18 legitimacy defect, not in a fourteenth lever against 2023.

---

## 7. EVIDENCE APPENDIX — committed artifacts, no re-derivation

### 7.1 The object, decomposed (`DIAGNOSIS-ercot177-c3a2023-anatomy-2026-08-07.md`)

* Model 2023 lw RT **$43.45** vs actual **$64.32** = **−32.4 %**.
* **Aug + Sep = 81.3 %** of the annual $-gap; Jun–Sep 91.9 %; every non-summer
  month within a few $/MWh, and the overnight body is *over*-priced.
* Within Aug–Sep the top 50 hours carry **80.6 %** of the gap. Entire gap in
  h12–h19. **~50–180 hours is the whole object.**
* **§3, the decisive decomposition** on the top-50 Aug–Sep gap hours, against
  ERCOT's own published `RT = system_lambda + RTORPA + RTORDPA`:

  | | model | ERCOT actual |
  |---|---|---|
  | RT price | 468.15 | 1,922.30 |
  | **energy-only** | **360.23** | **1,889.63** |
  | scarcity adder | 107.92 | 104.82 |
  | online reserve | 5,902 MW held | 5,471 MW PRC |

  **ENERGY-STACK term = $1,529 of the $1,454 mean miss = 100.2 %;
  SCARCITY-ADDER term = −$3 = −0.2 %.** ORDC/RTORPA is *already right* (3 %
  overshoot); reserve level is right (model is slightly *tighter* than reality
  and still prices 4× lower). Both faces CLOSED by measurement.

### 7.2 The containment statistic — the lane's sizing number (`ercot180_marginal_position.json`)

Top-100 2023 gap hours, mean gap **$1,041/MWh**, actual RT p50 $1,032 vs model
p50 $156:

* **In 94/100 hours the actual RT price lies INSIDE the position band
  `[curve@q_mod, curve@q_act]` of the SAME submitted curve** — band typically
  [−$50, $5,000].
* q_act p50 **0.9976**; q_mod p50 **0.9117**; wedge **+0.079**; q_act > q_mod in
  **95/100**. Marginal resource is CC in 92/100.
* Real curves are **CLIFFS** (cheap-to-negative body, HCAP top sliver); the
  model's class-level ladder statistics **dilute** the cliff. That is why every
  LEVEL lever leaves the p97–99 formation untouched.
* Disclosed at full magnitude: the max-price-at-BP marginal proxy is an **UPPER
  ENVELOPE** (p50 = $5,000 HCAP, ≥ actual in 99/100), so "share explained by
  position" **saturates > 1** and is *not* the sizing number. **94/100 is.**

### 7.3 The I-B3 refusal — the sharper instrument saturated too (`ercot181_interior_lambda.json`)

PRECOMMIT-ercot181 §1 fixed an interior-resource price-at-BP instrument ex ante,
with three admissibility bars. Result:

| bar | value | verdict |
|---|---|---|
| I-B1 coverage ≥ 0.60 | **0.9990** | PASS |
| I-B2 median IQR/λ̂ ≤ 0.25 | **0.0000** | PASS — *degenerately* |
| I-B3 median \|λ̂−RT\|/RT ≤ 0.25 | **27.24** | **FAIL** |

`INSTRUMENT_ADMISSIBLE: false`. λ̂ hour-median **$5,000.00** vs RT hour-median
**$144.05**.

**Why it saturated — a mechanical, nameable cause.** The probe reads price-at-BP
by a **step lookup**: `_price_at` takes the price of the *first curve point whose
MW ≥ BP* (`np.argmax(m >= q)`), i.e. the upper endpoint of the bracketing
segment. On a cliff-shaped curve whose last segment jumps from the cheap body to
an HCAP-priced top point, **any** BP strictly inside that final segment returns
$5,000. That is also why I-B2's IQR is exactly 0.0 — every interior resource
returns the identical wall value, so the "tightness" bar passed on degenerate
agreement rather than on clustering at λ.

Consequently I-2 **did not de-saturate the envelope, it reproduced it**: the
sharpened q_act p50 **0.99769** vs ercot-180's envelope **0.99765**, and
share-explained-by-position p50 **6.014** — *identical to the saturating
envelope value to 15 significant figures*. Precommit **P-1 is FAILED on its
second half**, reported at full magnitude.

**The admissible FUTURE re-instrument, named here and not built:** read the
submitted curve as **piecewise-LINEAR between its submitted (MW, $) points**
rather than as a right-continuous step, so λ̂ at a BP interior to the cliff
segment is the interpolated value instead of the segment's upper endpoint. This
is an instrument *correction*, not a residual-driven re-sweep, so it is
admissible under rules 20/23 — but it needs **its own precommit**, because:
(i) whether ERCOT SCED interpolates linearly within an energy-offer-curve
segment is a market-design fact that must be cited to the Nodal Protocols /
NP3-965 documentation, not assumed; (ii) I-B1/I-B2/I-B3 must be re-measured
under the new read (I-B2's current pass is an artifact of the step read and
carries no information); and (iii) the whole ERCOT offer-surface derive family
reads steps, so a linear read is a new convention with no precedent in the
codebase. **It is not authorized by this card.**

### 7.4 I-3 — the corpus-side wedge, and what it actually says (`ercot181_interior_lambda.json`)

Measured over 1,051 covered intervals in the 263 top-bin 2023 hours, ON merchant
gas (CC/CT):

| quantity | p25 | p50 | p75 |
|---|---|---|---|
| unaccepted MW priced below λ̂, above BP, capped at HASL | **269** | **555** | **926** |
| fleet loading position (BP ÷ curve-top), per-interval medians | 0.730 | **0.884** | 0.977 |

**Two honest readings, both of which matter to the sitting.**

* **The mass number is an UPPER BOUND, and it is small.** Because λ̂ saturated at
  $5,000 (§7.3), "priced below λ̂" admits essentially every sub-HCAP step, so
  `unaccepted` is really *sub-HCAP online spare above Base Point*. The true
  mass below the true λ is **≤ 555 MW at the median**. Roughly half a gigawatt,
  fleet-wide, in the tightest 263 hours of the year. Precommit P-7's refutation
  branch ("≈ 0 unaccepted mass") is not met — the premise is not refuted — but
  the wedge is **bounded small**, and it corroborates ercot-175 and ercot-177 §3
  from a third instrument: **this is not a quantity story.** ERCOT's online gas
  fleet had almost no cheap unaccepted headroom; the price formed on the sliver.
* **The dispersion is the structural point.** The typical ON merchant-gas
  resource ran at **0.884** of its curve top (p25–p75 **0.730–0.977**) while the
  *marginal* resource sat at **0.9976**. Reality prices a **dispersed** fleet at
  the cliff top of its most-loaded member; the LP clears a **homogeneous**
  class-aggregate ladder at one position. *(This is an interpretation of two
  committed statistics, offered as a framing for option (c2) — q_mod and
  fleet-position are defined on different supports and are not directly
  comparable.)*

### 7.5 The exhaustion chain — matrix §5.1 items 21–23 (DO-NOT-REDO)

| item | lane | outcome | evidence |
|---|---|---|---|
| **21** | conditioning grain, form (a) — CONTINUOUS net-load percentile | **`R` — REJECTED-AS-ARMED on reach.** C3a-2023 −32.4 % → ≈ −19.7 % (+$8.18 of the needed +$14.44), but **67.5 % of that is 10 NEW VOLL shed hours** (+$5.53); only **+$2.62 is offer formation**. Overshoots actual by >1.5× in 7 of 10 (2023-08-26 18:00: actual $570 → arm $5,000). **The ercot-48/49 signature verbatim** — not a keeper on structural grounds independent of its gates (rule 1). Also failed C3b-2024 (0.205 → 0.208) | `FINDING-ercot178-continuous-grain-2026-08-08.md` §7/§7a |
| **22** | conditioning grain, form (b) — TOP-SCOPED above p97 | **`R` — EXHAUSTED-AT-IDENTIFICATION.** ZERO admissible conduct edges: best candidate rank 0.99486, KS 0.0878, **p = 0.017 vs the pre-registered 0.01 bar**; argmax failure closes every smaller candidate a fortiori. No derive, no LP, no run. Rank-local structure in per-hour medians does not survive as a pooled MW-mass break — **the top-of-curve extremes are thin-MW** | `FINDING-ercot180-topscoped-exhausted-2026-08-08.md` |
| **23** | quantity-position — POSITION-TAIL completion | **`K` — but INERT-ON-THE-OBJECT.** M-0/M-1 falsified the provably-inert prediction (**598/528/48 live row-hours**; wall+pool geometry reproduced byte-identically, control compose shas match the ercot-178 record), so Route B bound; built, seam-proven (SP-α1–α8), solved, **all pre-registered gates PASS**, promoted on structural fidelity alone. **The measured object did not move**: 22 spring 2023 hours +$0.006..+$0.57, annual lw **+$0.0004/MWh**; summer object hours, tails and shed **identical to control**. The measured top decile of submitted conduct now replaces a silent p90 end-clamp — a real structural gain that buys nothing on C3a-2023 | `FINDING-ercot181-position-tail-2026-08-09.md` + `ercot181_positiontail_reach.json` + `ercot181_positiontail_seamproof.json` |

**With form (a) `R` on reach and form (b) `R` on identification, conditioning
grain is CLOSED as a family for the 2023 tail.** Combined with the ex-ante
refusals in PRECOMMIT-ercot181 §2 — form β comonotone re-aggregation (marks the
armed surfaces *down* in the object hours), form γ reading the curve at reality's
position (a rule-13 outcome pin), form δ modeling the acceptance friction (every
face separately adjudicated) — and with §7.1's closure of ORDC/RTORPA/reserve
level and §7.4's bounding of the quantity wedge, **the offer-side mechanism space
for C3a-2023 is exhausted.** No offer-side lever may be opened against it without
new evidence.

Also standing closed, carried verbatim from PRECOMMIT-ercot180 §0 /
PRECOMMIT-ercot181 §0: the ercot-48 shed signature (twice-rejected), unit-scoped
rows `R`, ramp mechanisms `R`, temp-derate `R`, offline-increment `I`, storage RT
surface `R`, `energy_online_capability_cap` `R`, CC-headroom crosswalk
FILED-UNLICENSED, offered-vs-deliverable wedge FILED-REDIRECTED, all coal offer
lanes CLOSED, per-year CT re-identification REFUSED, West/Panhandle CLOSED, the
2023 aggregate-depth premise REFUTED.

---

## 8. DATA BLOCKER FOR THE OWNER — the 2024/2025 NP3-965 full-year re-upload

**State of the corpus on disk** (`data/raw/ercot/SCED/`, 315 shards, publication-
month keyed so delivery = filename − 2): shards run `2023-03` … `2024-03`, i.e.
**delivery-2023 is complete and intact** (the 2026-08-03 re-upload; 7,917
hour-nodes). **Delivery 2024 and 2025 have no full-year corpus** — only the
sample-day corpora (**561 / 500 nodes** vs 2023's 7,917).

**Why they are missing.** PRECOMMIT-ercot181 Amendment 1: the frozen RT-wall
2024/2025 blocks were derived from a **2026-07-21 full-corpus intake that the
2026-07-22 large-blob history rewrite PURGED**. Today's disk cannot reconstruct
those blocks' populations — the `--position-tail` derive's frozen-ladder
reproduction assert **stopped on 2024** for exactly this reason, which is why the
position-tail artifacts carry tails for **2023 only**.

**What a full-year 2024/2025 NP3-965 re-upload would unblock — three distinct things:**

1. **2024/2025 position-tails become derivable.** Today they are forced empty by
   the zero-support rule at year grain, so the position-tail mechanism is
   structurally a 2023-only object and can never be evidenced out-of-object.
2. **It is the *named* re-open condition for the ercot-180 grain
   re-identification.** Item 22 died at **p = 0.017 against a 0.01 bar** on a
   corpus of 263 hours / 403,007 rows. FINDING-ercot180 records that a future
   re-identification is admissible **only under a NEW precommit on new
   evidence**, and names *"a full-year 2024/2025 NP3-965 intake enlarging the
   corpus"* as that evidence. A near-miss on a small corpus is exactly the case
   where more corpus is decisive — but **the re-open requires a new precommit,
   not a re-run of the old instrument** (the instrument must not be re-designed
   after seeing the answer). The scaffolding is already merged default-off
   (gate `ercot_offer_surface_top_scoped`, cache keys registered, vintage guards,
   `--top-scoped` derive modes, authored-never-run seam probe), so it would be a
   derive-and-prove session, not a rebuild.
3. **The frozen 2024/2025 RT-wall anchors become reproducible again.** Right now
   two *armed keeper* artifacts rest on a population that no longer exists on
   disk. That is a reproducibility gap in the keeper itself, independent of any
   lever — and it is the more serious of the three.

**Ask:** authorize the re-upload (a `data/raw/` intake, unrestricted under rule
22's data-intake clause — the holdout regime gates *looking at answers*, never
preparing inputs). Note the blob-size constraint that caused the original purge:
the intake must be sized and staged so it does not repeat the 2026-07-22 history
rewrite.

---

## 9. GOVERNANCE — what this session did and did not do

* **Rule 1 `[R-STRUCT]`:** no mechanism proposed, none stretched to reach −10 %.
* **Rule 13 `[R-MEASURED]`:** every I-1/I-2/I-3 figure quoted here is
  DIAGNOSTIC-licensed and is quoted as *sizing*, never as a parameter or an
  input. No output of any probe enters any mechanism.
* **Rule 15/16:** no run solved, none registered — nothing to register. ercot-181's
  own registration duty is discharged on its own record (both runs, all three
  years, PR #3792).
* **Rule 22:** ERCOT holds no `complete` and no `final` marker; no out-of-training
  year was solved, scored, read or registered. §8's ask is a data intake, which
  the rule's own clause places outside the spend gate.
* **Rule 23 `[R-DOF]` / 24 `[R-REGISTRY]`:** zero new scalars, zero new
  `ScenarioConfig` fields, no off-registry channel.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT only. No other ISO's files, bundles, keeper
  shard or matrix column touched. (§3 names CAISO/MISO solely as *blast radius of
  a rubric change*, which is rubric-global by construction.)
* **Rule 27 `[R-PUSH]`:** no source file ≥300 lines modified.
* **Rule 28 `[R-MECH-MATRIX]`:** **no cell minted and no verdict written** — this
  is a governance sitting, not a mechanism test. Item 23's `O → K` was stamped by
  ercot-181, the session that holds the A/B evidence (duty b); this card only
  cites it.
* **Keeper:** `2026-08-09-run181-position-tail`, **untouched** — no promotion, no
  demotion, no re-key, no keeper-shard edit.
* **GitHub Actions:** nothing offloaded.

**Next shorthand: ercot-183.**

---

## 10. RESOLUTIONS — ALL FIVE SIGNED BY THE OWNER, 2026-08-09

The sitting was held and every card is signed. Recorded verbatim; where the
owner departed from the card's recommendation the departure is stated as such,
not smoothed over.

| # | Decision | **SIGNED** | vs. recommendation |
|---|---|---|---|
| **D1** | May C3a-2023 join the accepted-limitation ledger? | **(c) NO — go at the root: the model-class lane is AUTHORIZED** | Departs from the card's (b). See D1 note |
| **D2** | The frozen ERCOT-148/149 ceiling lane | **C — re-charter the partial layer (fault 3)** | As recommended |
| **D3** | The rule-18 grain defect round | **(ii) authorized, sequenced after D2** | As recommended |
| **D4** | The 2024/2025 NP3-965 full-year re-upload | **AUTHORIZED** | As recommended |
| **D5** | How far the cliff-resolving work goes now | **Costing memo ONLY — no build authorization** | As recommended |

### D1 — the ledger question is answered NO, and the object is not parked

**The carve-out is refused.** No rubric text changes: `LEDGERABLE_CRITERIA`
stays `{"price_tail"}`, `MAX_LEDGERED_CAVEATS` stays 1, the v3.0 tier guard is
untouched, and C3a-2023 stands as a **MODEL MISS at full magnitude (−32.4 %)**.
ERCOT's determination remains **NOT-YET {C3a, C3b}**. Nothing about CAISO, MISO
or any other ISO's rubric position moves.

**What the owner chose beyond that.** The card recommended (b) — accept and
redirect. The owner took **(c)**, which is (b)'s rubric posture *plus* an active
root-cause lane: C3a-2023 is to be treated as a real open defect to be **fixed**,
not parked. The owner's stated reason, recorded because it governs the lane's
scope: *"I want to actually fix the 2023 pricing."*

**The distinction that decided it.** (a) changes what the rubric excuses and
produces byte-identical prices; (c2) is the only remaining candidate that can
change the price. The model class is the hourly, class-aggregate,
frictionless-within-the-hour LP; C3a-2023 is a property of those three
structural facts, which is why fourteen levers inside the class failed — the
last of them (the position-tail, item 23) added the correct measured cliff
conduct and moved the answer **+$0.0004/MWh**, because the LP's clearing
position sits at q_mod 0.912 while reality's price forms at q_act 0.9976. The
model can now *quote* the cliff; it does not *reach* it.

### D5 — the lane's first step, and the question the memo must answer

D1(c) authorizes the lane; D5 scopes its first step to a **costing memo, no
build**. (c1) sub-hourly is refused on scale (12× the LP columns against a
measured ~6.6 GB / ~20 min per per-plant year and a rule-12 two-run cap; a
spec-level program, not a calibration lane). (c2) — non-uniform slicing that
refines the top of each plant's econ ramp, against today's
`offer_curve_smoothing_n = 6` **equal-width** blocks — is the chartered object.

**The memo's load-bearing question, stated here so the lane cannot drift off
it:** can a resolution change **move the LP's clearing position up the curve**,
or does it merely price the top of the curve more accurately? Item 23 already
proved the second is inert. If (c2) cannot move the clearing position it is
another inert completion, and the memo must say so before any build is
authorized.

Deliverables unchanged from §5: (1) feasibility and cost under the current LP
layout, what moves in P0, what re-derives; (2) **G-SHED as the ex-ante primary
falsifier** — the ercot-48/49 manufactured-shortage signature has killed this
object twice, most recently ercot-178 at 67.5 % of its apparent gain; (3) an
honest reachability statement, including that the family's measured
offer-formation budget is ~$2.6/MWh against a $14.44/MWh bar and that (c2) may
land short; (4) rule-25 cross-ISO scope, since fleet representation is not
ERCOT-gated by construction.

### The path to a clean determination, now that both halves have a lane

ERCOT needs **both** halves closed on the merits — no ledger action can
substitute for either:

* **the 2024 half** — C3b-2024 (0.205) → **D2**, the fault-3 partial-layer
  re-charter;
* **the 2023 half** — C3a-2023 (−32.4 %) and C3b-2023 (0.602), one object
  (ercot-177 §7: C3b-2023 is a shape metric over the same hours and moves with
  it) → **D1(c)/D5**.

Only if both land does C3c become the lone failing criterion, at which point the
standing rule reads the run **CALIBRATED-WITH-CAVEATS** — never CALIBRATED.

### Execution order

1. **D4 — the NP3-965 re-upload.** Independent of everything and the longest
   lead time, so it starts first. Staged against the blob-size limit that caused
   the 2026-07-22 purge.
2. **D2 — the fault-3 re-charter.** The determination-moving lane. Own precommit,
   own gates, G-COAL148 carried live.
3. **D5 — the (c2) costing memo.** Cheap and parallel to D2; it is decision
   support, not a build.
4. **D3 — the rule-18 grain defect round.** After D2, per its own signature.

### What these five signatures do NOT do

* **No rubric amendment of any kind was signed.** D1 refused the carve-out; the
  scorer is byte-unchanged.
* **No build was authorized.** D5 is a memo; D2 and D3 each still require their
  own pre-registered round before any solve.
* **ERCOT-148/149 is not repealed.** The product cap stays armed until a
  re-chartered arm passes its own gates (D2's ruling text is explicit).
* **No holdout marker was granted or spent.** ERCOT still holds no `complete`
  and no `final`; the D4 intake is a data-preparation action, which rule 22
  places outside the spend gate.
* **The keeper did not move.** `2026-08-09-run181-position-tail` stands
  unchanged, NOT-YET {C3a, C3b}.
