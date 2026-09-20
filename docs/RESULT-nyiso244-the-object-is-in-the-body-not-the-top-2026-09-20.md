# RESULT — nyiso-244: the measured offer surface is REFUSED at the gate, and the refusal locates the object precisely — it is in the BODY of the offer curve, not the TOP

**Session** nyiso-244 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container, no
shard launched**).
**Date** 2026-09-20. **Base** `origin/main` at `95825f63`.
**PRECOMMIT** `docs/PRECOMMIT-nyiso244-measured-offer-surface-design-2026-09-20.md`, committed
at **`2e5097a5`** before any number below was computed.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025} —
**UNCHANGED. Nothing armed, screened, solved, promoted or registered. No `ScenarioConfig`
field moves. NYISO still reads `CALIBRATED` on its ISO tier.**
**Predecessor** `docs/RESULT-nyiso243-the-tail-is-not-an-availability-object-2026-09-20.md` §6.

> ## HEADLINE
> 1. **THE GATE REFUSES IT, ON REACH.** The shared conditional-offer-surface kernel prices
>    **peak rungs only**. In the 70 missed winter hours of 2022 the idle sub-$300 capacity —
>    the only capacity whose offer can move the energy dual — sits **74.5 % on ECON rungs
>    (3,839.3 MW)** and **14.5 % on peak rungs (745.7 MW)**. Against the 4,715.7 MW object the
>    peak-rung form reaches **15.8 %**, against a pre-registered bar of 50 %. **Refused before
>    a solve, per PRECOMMIT §3 G3.**
> 2. **AND IT REFUSES HARDER ON THE SCOPE THE IDENTIFICATION WOULD HAVE PRODUCED.** The only
>    cohort P-27's masking admits is the quick-start fleet, i.e. `CT_PEAKER`. The CT family's
>    idle sub-gate capacity on peak rungs is **6.1 MW — 0.1 % of the object.**
> 3. **THE COHORT ALSO FAILS ITS OWN VALIDATION**, which was pre-registered and is reported at
>    full magnitude. NYISO's own 10-minute non-synchronized reserve product selects **51 masked
>    gens / 2,374.0 MW** against a model CT family of **58 plants / 3,404.7 MW** — the *count*
>    lands (V2 n 0.121 ≤ 0.30) and the *size distribution does not* (V3 median relative gap
>    **1.328** against a 0.25 bar; V2 MW 0.303 against 0.25). Cohort median unit **46.1 MW**
>    against a model CT-family median plant of **6.5 MW**. Under PRECOMMIT §3 G2 no fleet-wide
>    substitute is taken.
> 4. **RULE 19 IS THE ONE BLOCKER THAT CLEARS, AND IT CLEARS CLEANLY.** `gas_offer_net_revenue_
>    margin` is **provably INERT on the NYISO peak band of every CC class** — `phys_peak == peak
>    == 2.250` for `CC_REGULAR` and `CC_CHP`, so its markup there is **exactly 0.0** — and where
>    it is live (`CT_PEAKER` 3.000, `ST_GAS` 3.200) it prices the **registered** increment
>    `(m − phys)` at a fuel-invariant anchor while a surface prices the **measured scarcity**
>    increment `(M − m)` at the hour's fuel. Two disjoint increments of one curve; **overlap 0
>    by construction, not by tolerance.** This answer survives the refusal and is the
>    reusable part of this session.
> 5. **THE CONDITIONING DRIVER HOLDS ON THE FULL KEEPER SPAN** (G4, the one gate nyiso-243 had
>    only measured on two years): the measured DAM MW offered above $300 rises monotonically
>    across the DA ladder in **3 of 4 years** (2022 ✓, 2023 ✓, 2024 ✓ over its three populated
>    rungs, **2025 ✗**). Rule 13 `[R-MEASURED]` admissibility is not what fails here.
> 6. **THE REFUSAL LOCATES THE SUCCESSOR, AND FOR ONCE IT IS A MEASURED LOCATION — WITH NO
>    COHORT NEEDED.** The object is the **body** of NYISO's offer curve, not its top. A
>    **system** offer curve is class-free, so masking cannot block it, and differencing it
>    (missed vs ordinary winter, the statistic that cancels the two fleets' constant ~9.4 GW
>    level difference) puts the object at **+4,989 MW at $200** and **+4,064 MW at $150**
>    against an object of **4,715.7 MW — a 5.8 % match**. The real market lifts **6,203 MW**
>    out of sub-$200 when the event arrives; the model lifts **1,213 MW**. Above $300 the two
>    curves agree to within 907 MW. **The model is not missing a scarcity wall; it has a
>    ceiling in the $150–$200 body that the real curve does not have.**
> 7. **NO SHARD, DELIBERATELY** (rule 34 `[R-SHARD-PROMOTABLE]`: a solve that cannot back a
>    promotion is not spent). **`measured_offer_surface` NYISO `U` → `G`**, with a re-open
>    condition that is specific rather than decorative.

---

## 1. WHAT WAS GATED, AND WHY THE GATES WERE WRITTEN FIRST

nyiso-243 re-opened this cell `G` → `U` on the nyiso-115 refusal's own stated condition, and
handed forward **two blockers a successor owed before any shard** — masking, and a rule 19
`[R-ONE-MECH]` reconciliation against the armed `gas_offer_net_revenue_margin`. This session
owes those two and adds two more that the object itself requires: **does the mechanism reach**,
and **does its conditioning driver survive on every year the keeper carries** rather than the
two nyiso-243 happened to measure.

All five gates, their thresholds and the no-substitute rule on a G2 failure were fixed in
`PRECOMMIT-nyiso244` §3 and pushed at **`2e5097a5`** before a single conditioned number was
computed. That ordering is the whole point: G3 is the gate that refuses, and it refuses on a
bar (50 % of the object) that was written down before anyone knew the answer was 15.8 %.

**The mechanism under design.** `data/fleet/offer_surfaces.py::_conditional_surface_markup`,
the shared kernel behind `ercot_/neiso_/pjm_/caiso_offer_surface_conditional`: a **P1-only
additive markup** that reprices a class's **peak-rung** rows from the height the fleet built
them at (`offer_curve_by_group[cls]["peak"]`) to a measured heat-rate multiplier read out of a
frozen condition-binned JSON, keyed on the hour's within-year net-load-percentile bin. A NYISO
member would have been `nyiso_offer_surface_conditional` over a
`derive_nyiso_offer_surface.py` built from P-27.

Probe: `scripts/probes/nyiso244_offer_surface_design.py` →
`results/calibration/_nyiso244_offer_surface_design.json`.

---

## 2. G1 — RULE 19 `[R-ONE-MECH]`: RECONCILED, AND THIS IS THE PART THAT SURVIVES

The enumeration is taken from the keeper's own `run_config.json`, not from memory. Exactly
**four** armed fields can write a NYISO gas peak-rung offer, and they are one mechanism with
three gates: `gas_offer_net_revenue_margin`, `gas_offer_margin_zonal_anchor`,
`gas_offer_margin_zonal_anchor_vintage`, plus `nyiso_ct_peaker_committed_measured` — which
writes the **committed** band and never a peak rung. `cc_committed_offer_margin`,
`coal_peak_offer_margin`, `nyiso_ct_peaker_bands_measured` and every other ISO's surface are
**off**.

### 2.1 Measured: where the armed mechanism is inert, and where it is live

`gas_offer_net_revenue_margin` reprices the band's **above-physical** markup from
fuel-scaling to a fuel-invariant $/MWh at the anchor. Its reach on the peak band is therefore
exactly `peak − phys_peak`, and on NYISO's registered curve that is:

| class | `peak` (m) | `phys_peak` | registered markup `m − phys` | GONRM on the peak rung |
|---|---:|---:|---:|---|
| **CC_REGULAR** | 2.250 | 2.250 | **0.000** | **INERT** |
| **CC_CHP** | 2.250 | 2.250 | **0.000** | **INERT** |
| CC_INTERMEDIATE | 2.250 | — | — | INERT (no `phys_*`; neutral by the field's own construction) |
| CT_CHP | 1.000 | — | — | INERT |
| CT_INTERMEDIATE | 3.000 | — | — | INERT |
| ST_GAS_INTERMEDIATE | 2.200 | — | — | INERT |
| every COAL_* | 1.20–1.55 | — | — | INERT |
| **CT_PEAKER** | 4.000 | 1.000 | **3.000** | **LIVE** |
| **ST_GAS** | 4.200 | 1.000 | **3.200** | **LIVE** |

So the rule-19 question is not one question but two, and the *CC* half — the half a
CC-scoped surface would have needed — answers itself: **the armed mechanism does not touch
those rungs at all.** That is a measurement, not an argument.

### 2.2 And where it IS live, the two increments are disjoint

A peak rung's offer decomposes into three terms:

```
phys · HR_base · fuel(t)          physical burn, fuel-tracking
(m − phys) · HR_base · anchor     the REGISTERED markup — what gas_offer_net_revenue_margin reprices
(M − m)   · HR_base · fuel(t)     the MEASURED scarcity increment — what a surface would add
```

`gas_offer_net_revenue_margin` never touches `(M − m)`; the surface never touches
`(m − phys)`. **Overlap is 0 by construction**, so no MW is priced twice — the rule-19 test.
The repo's own ERCOT keeper (`ercot248_two_config_keeper`) arms both together on classes where
the registered markup is far larger than NYISO's (`CT_PEAKER` 12.150, `CC_REGULAR` 2.326),
which is a **precedent, not the argument**; the decomposition above is the argument.

**One construction limit is declared rather than resolved**, because a successor will meet it.
The shared kernel prices the scarcity increment **multiplicatively**, so it tracks the hour's
fuel — while `gas_offer_net_revenue_margin`'s own grounding is that real bidders express
scarcity in **$ terms**, not heat-rate multiples. A fuel-invariant form of the *same measured
increment* is therefore a legitimate successor question. It is not a defect in the
reconciliation and it is not why this session refuses.

---

## 3. G3 — REACH. THE GATE THAT REFUSES, AND THE MEASUREMENT THAT MAKES IT INTERESTING

### 3.1 The logic, which is the LP's and not a modeller's

nyiso-242 phase 0D: the energy-balance dual **is** the marginal tranche's offer, so a price
above $300 requires that every tranche offering below $300 is already fully dispatched. It
follows that a pricing mechanism can only reach this object by **raising the offers of the
idle sub-gate capacity itself**. Raising a tranche that is already above the margin moves no
dual.

### 3.2 The measurement, 2022 winter missed cluster, 70 hours

Construction, stated because it is a choice: per class and hour the class's own committed P1
dispatch (the keeper's `class_hourly` sidecar) is served by its **cheapest** rows, so the idle
set is the class's most expensive available capacity; what of that idle set is offered below
the gate is what a pricing mechanism must lift. Median MW over the 70 hours:

| class | available | dispatched | **idle < $300** | committed | **econ** | **peak** |
|---|---:|---:|---:|---:|---:|---:|
| ST_GAS | 3,338.1 | 332.9 | **2,079.9** | 320.8 | **1,655.5** | **0.0** |
| CT_PEAKER | 2,708.4 | 553.2 | **1,208.2** | 107.2 | **1,128.1** | **2.6** |
| CC_CHP | 2,993.6 | 1,551.3 | **1,128.6** | 12.2 | 849.0 | 223.6 |
| CC_REGULAR | 4,877.5 | 3,530.6 | **911.7** | 89.0 | 197.1 | 512.4 |
| CT_CHP | 343.9 | 293.5 | 50.3 | 37.3 | 9.6 | 3.5 |
| ST_CHP | 295.7 | 282.8 | 5.1 | 2.0 | 0.0 | 3.6 |
| **TOTAL** | | | **5,383.8** | **568.5** | **3,839.3** | **745.7** |

| rung family | MW | share of idle < gate | **share of the 4,715.7 MW object** |
|---|---:|---:|---:|
| must-run / sync | 0.0 | 0.0 % | 0.0 % |
| committed | 568.5 | 11.0 % | 12.1 % |
| **econ** | **3,839.3** | **74.5 %** | **81.4 %** |
| **peak** | **745.7** | **14.5 %** | **15.8 %** |

*(The 5,383.8 MW total is slightly above nyiso-242's 4,715.7 MW because it is built per class
rather than system-wide; the object is quoted against nyiso-242's number throughout so the two
sessions' arithmetic stays comparable. On either denominator the peak-rung share is 14–16 %.)*

### 3.3 The verdict, and the thing worth noticing in it

**G3 FAILS: 15.8 % against a 50 % bar.** And on the scope the identification would actually
have produced — the quick-start / CT family — it is **6.1 MW, 0.1 %**.

The precedent for refusing on reach is this lane's own: nyiso-242 §1.3 refused
`cc_winter_capability_basis` at 263.6 MW against the same object.

**What is worth noticing is WHY the peak rungs are not idle below the gate: they are already
offered above it.** `CT_PEAKER` peak sits at multiplier 4.000 and `ST_GAS` peak at 4.200, and
in these hours that puts them above $300 — so the model is *not* missing a scarcity wall at
the top of its curve. What it is missing is anywhere for the **body** of the curve to go: the
econ rungs sit at multipliers **0.95–1.00**, i.e. essentially at marginal cost, in every hour
of the year including the ones the real market cleared at $383.

---

## 4. G2 — THE MASKING BLOCKER. THE COHORT DOES NOT VALIDATE, AND THAT IS REPORTED IN FULL

The selector was fixed in the PRECOMMIT as a **published NYISO product definition, not a
fitted signature**: a resource offering **10-Minute Non-Synchronized Reserve** is, by NYISO's
own product, able to go from offline to full output in 10 minutes — the quick-start
population `CT_PEAKER` represents. This is the same *kind* of identification
`derive_neiso_offer_surface.py` uses on ISO-NE's equally-masked corpus (`Claim 30 ≥ 0.9 ×
EcoMax`, "selected by PHYSICS, not fuel labels"), and it is a **method**, never a transferred
parameter (rule 25 `[R-ISO-SCOPE]`).

| validation | measured | bar | verdict |
|---|---:|---:|---|
| **V1 scope** — P-27 39,899.6 MW / 333 gens vs model internal 38,250.4 MW / 306 plants | **0.043** | ≤ 0.15 | **PASS** |
| **V2 size** — cohort 2,374.0 MW vs model CT family 3,404.7 MW | **0.303** | ≤ 0.25 | **FAIL** |
| **V2 count** — cohort 51 gens vs model CT family 58 plants | **0.121** | ≤ 0.30 | PASS |
| **V3 fingerprint** — median relative gap of the sorted capacity vectors | **1.328** | ≤ 0.25 | **FAIL** |

**V1 is the useful pass**: the two corpora really do describe the same fleet, to 4.3 %. So the
failure is not a scope error — it is that **the cohort is not the model's CT fleet**. The
tell is the size distribution: cohort median unit **46.1 MW**, model CT-family median plant
**6.5 MW** against a mean of 58.7 MW. The model's CT family is a long tail of very small
plants; the quick-start bidders are a few dozen mid-sized ones. Counts coincide; the objects
do not.

**No fleet-wide substitute is taken**, exactly as the PRECOMMIT required in advance: posting
one level across every gas rung is the collapsed-heterogeneity failure the flat
`ercot_ct_offer_surface` was rejected for, and rule 1 `[R-STRUCT]` refuses a structurally
worse mechanism whatever it would do to the residual.

**A caveat against over-reading V3.** A P-27 "masked gen" need not be a model "plant" — NYISO
may mask at a different aggregation, and nothing in the corpus says which. V3 is therefore
evidence that *this* attribution is unvalidated, not proof that no attribution exists. That
distinction is why the cell's re-open condition below is written the way it is. **It does not
rescue the mechanism**, because G3 refuses the peak-rung form **independently of any cohort**:
15.8 % is a property of the model's own band structure.

---

## 5. G4 — THE CONDITIONING DRIVER, RE-MEASURED ON EVERY KEEPER YEAR

nyiso-243 measured this on 2022 and 2025. A surface armed across the keeper's four years owes
it on four. Median measured DAM MW offered above $300, by DA-price ladder:

| year | DA > $100 | DA > $150 | DA > $200 | DA > $300 | monotone |
|---|---:|---:|---:|---:|---|
| 2022 | 3,833.1 | 4,561.0 | 9,328.4 | 10,182.6 | **✓** |
| 2023 | 5,213.4 | 9,482.9 | 9,492.3 | 9,889.4 | **✓** |
| 2024 | 2,831.8 | 3,646.2 | 3,646.2 | *(0 hours)* | ✓ over three rungs |
| 2025 | 1,804.7 | 2,280.7 | 5,185.0 | 2,964.9 | **✗** |

**G4 PASSES at 3 of 4 against a bar of 3**, and it passes honestly rather than comfortably:
2024's top rung is **empty** (no hour cleared DA > $300), and 2025 breaks at the top — which
is the same 2025-summer object nyiso-243 §4 already separated out as *not* an energy-offer
phenomenon. **Rule 13 `[R-MEASURED]` admissibility is not what refuses this mechanism**; it is
the only one of nyiso-243's optimistic readings that survives contact with all four years.

---

## 6. THE SYSTEM OFFER CURVE — MODEL AGAINST MEASURED, WITH NO COHORT AT ALL

*(Descriptive. Not a gate, and nothing is selected on it. Recorded because it is the one
comparison masking cannot block, and it is what a successor should start from.)*

A **system** offer curve is class-free, so it needs no attribution. Both sides are
NYCA-internal generators (model side with `NYISO_external_*` and `NYISO_DR_*` removed, the
nyiso-243 §3 scope correction). Median MW offered **at or below** each price, 2022:

| price | model MW ≤ P | measured MW ≤ P | model − measured |
|---|---:|---:|---:|
| $0 | 0.0 | 5,077.4 | −5,077.4 |
| $25 | 7,980.7 | 8,072.0 | −91.3 |
| $50 | 8,408.9 | 9,318.9 | −910.0 |
| $75 | 8,441.4 | 10,318.5 | −1,877.1 |
| $100 | 10,687.6 | 11,488.4 | −800.8 |
| $150 | 16,656.1 | 14,890.3 | +1,765.8 |
| $200 | 19,785.1 | 20,264.2 | −479.1 |
| $300 | 22,319.9 | 28,474.6 | −6,154.7 |
| $500 | 24,555.6 | 32,746.8 | −8,191.2 |
| $1,000 | 25,206.6 | 34,629.2 | −9,422.6 |

**The levels are not the signal and must not be read as one.** The two fleets differ by a
near-constant **~9.4 GW** at the top of the curve (−9,422.6 in the missed hours, −9,504.6 in
ordinary ones) — the model believes ~25.2 GW of internal capacity where the market declared
~32.7 GW, which is precisely the level difference nyiso-243 Leg 2 measured and then **refuted
as an availability signal** by differencing it. The same discipline applies here: the
statistic that identifies is the **difference of differences**, in which any constant scope or
level error cancels exactly.

### 6.1 THE STATISTIC THAT IDENTIFIES — how much capacity each side WITHDRAWS from below a price when the event arrives

MW withdrawn from below price *P* in the 70 missed hours, relative to the 2,090 ordinary
winter hours (`ordinary − missed`; positive = the curve lifted capacity above *P*):

| price | **model withdrew** | **market withdrew** | **market − model** |
|---|---:|---:|---:|
| $25 | 207.3 | −47.4 | −254.7 |
| $50 | 381.1 | 894.0 | +512.9 |
| $75 | 6,118.3 | 2,749.0 | −3,369.3 |
| $100 | 7,296.1 | 5,426.4 | −1,869.7 |
| **$150** | 3,610.7 | **7,674.5** | **+4,063.8** |
| **$200** | 1,213.1 | **6,202.5** | **+4,989.4** |
| $300 | 748.6 | 1,655.4 | +906.8 |
| $500 | 8.8 | 180.0 | +171.2 |
| $1,000 | −609.6 | −527.6 | +82.0 |

**Read it from the bottom of the curve up, because the shape is the finding.**

* **Below $100 the model withdraws MORE than the market does** (6,118 vs 2,749 MW at $75).
  That is the delivered-gas spike working correctly — cold-snap fuel lifts the model's cheap
  capacity out of the sub-$100 region faster than the real fleet's offers did. Nothing is
  broken here.
* **At $150 and $200 the two curves part company, and by the size of the object.** The market
  keeps lifting capacity — **7,674 MW** out of sub-$150 and **6,203 MW** out of sub-$200 —
  while the model's curve **stalls**, lifting only 3,611 and 1,213 MW. The gap peaks at
  **+4,989 MW at $200**, against an object of **4,715.7 MW**: a **5.8 % match**, from an
  instrument that needed **no cohort, no class, no unit and no zone**.
* **Above $300 the two agree again** (+907, +171, +82). The model is **not** missing a
  scarcity wall at the top of its curve. §3.3 said the same thing from the model's side; this
  says it from the market's.

**So the object is a conditional withdrawal of roughly 5 GW from the $150–$200 region of the
offer curve — the BODY — and the model has a ceiling there that the real market does not.**
That is the same conclusion §3.2 reached from the rung families (74.5 % of the idle sub-gate
capacity on econ rungs), derived from the opposite side of the comparison and without any of
the assumptions that made the cohort fail.

Probe: `scripts/probes/nyiso244_system_offer_curve.py` →
`results/calibration/_nyiso244_system_offer_curve.json`.

---

## 7. MECHANISM MATRIX (rule 28 `[R-MECH-MATRIX]`)

**`measured_offer_surface` NYISO `U` → `G`.** Refused ex ante, no solve, on **reach** (G3,
15.8 % against a 50 % bar; 0.1 % on the identifiable scope) **and** on **identification** (G2,
V2/V3), either of which is sufficient. This follows the lane's own nyiso-242 precedent, which
moved `cc_winter_capability_basis` `U` → `G` on exactly that pair of legs.

**The re-open condition, specific rather than decorative.** The cell becomes live again if and
only if **both** hold:

1. a surface form exists that prices the **econ/midcurve** rungs rather than the peak rungs —
   the repo already carries that form for two ISOs
   (`ercot_offer_surface_midcurve_conditional`, `pjm_offer_midcurve_conditional`), and §3.2
   measures its reach at **74.5 %** of the object, which clears G3's bar; **and**
2. a cohort attribution passes a validation at least as strong as §4's — **or the form is
   shown to need none.** §6.1 is the reason that second limb is not a formality: the object
   is identified **system-wide, class-free, at +4,989 MW at $200**, so a successor has a
   measured target without ever attributing a masked bid to a class. What it would still owe
   is the **mapping** — how a system-level target is posted onto model rows — and that mapping
   is itself a modelling choice with the same burden of validation the cohort just failed.

**A successor should budget its zero-LP pass in that order** — form first (can an econ-rung
surface exist), mapping second (by class, by position, or system-wide), derive last. This
session's order was gates-first, and that is what kept it to zero solves.

**No other cell moves.** `cc_committed_offer_margin` stays `G` (its per-unit curve bottom is
still withheld by masking — unchanged by anything here). The availability family
(`temp_dependent_derate` `G`, `cc_winter_capability_basis` `G`,
`unit_outage_short_windows`/`_gas` `I`, the ST_GAS blanket DO-NOT-REDO) was **not re-opened**;
rule 28(a) was read and obeyed. No `ScenarioConfig` field is added, so duty (c) has no subject.

---

## 8. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — every threshold was fixed at `2e5097a5` before any conditioned
  number was computed, and the mechanism is refused on a structural bar rather than on a
  residual. The numbers that **favoured** the mechanism are reported at full magnitude beside
  the refusal: G1 clears, G4 clears, V1 clears at 4.3 %, and the measured object
  (4,986 MW above $300 against the model's 4,715.7 MW idle below it) is exactly the match
  nyiso-243 reported.
* **Rule 19 `[R-ONE-MECH]`** — §2 is the enumerate-and-reconcile nyiso-243 §6 owed, discharged
  **before** anything was built, with the armed mechanism's reach on the peak band measured
  per class rather than assumed.
* **Rule 13 `[R-MEASURED]`** — §5 extends the admissibility evidence from two years to four.
* **Rule 25 `[R-ISO-SCOPE]`** — every number here is NYISO's own. What is reused from NEISO is
  the *method* of selecting a cohort by published physics on a masked corpus, never a
  parameter; NEISO's own `Claim 30 ≥ 0.9 × EcoMax` threshold is **not** carried.
* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters, zero new literals, no
  `ScenarioConfig` field touched. The PRECOMMIT's thresholds are this session's decision gates,
  not model parameters.
* **Rules 32 / 33 / 34 / 35** — **zero LP, no shard launched**, so rules 33/34/35 have no
  subject. §3.3 is why launching one could not have backed a promotion: the mechanism cannot
  reach the object it was proposed for.
* **Rule 31 `[R-RETAIN]`** — nothing deleted. **No bundle was produced, so there is no
  promotion question to put to the owner.**
* **Rule 15 `[R-DASHBOARD]`** — no run produced, nothing to register; the keeper's dashboard
  entry is untouched.
* **Rule 27 `[R-PUSH]`** — no existing source file ≥300 lines was rewritten. The three new
  artefacts are new files.

**`tests/scoring`** — this session wrote **no solve-path code** (three new probe files, two new
docs, one matrix-shard cell), so it adds zero to the unowned baseline. The baseline was
**re-measured rather than assumed**, on this session's own clean checkout of `origin/main`
at `95825f63`: **22 failed, 1553 passed, 18 skipped, 178 subtests passed** in 109 s. That
reproduces the 22 failures the handoff reported as still unowned (the pass count differs from
the handoff's 1547 because tests have been added since it was written), and it remains
unowned — no session has claimed it, and this one does not either. The failing families are
`test_audit_keepers_lineage` and `test_golden_manifest_provenance`, neither of which this
session's files touch.

---

## 9. ARTEFACTS

| artefact | what it is |
|---|---|
| `docs/PRECOMMIT-nyiso244-measured-offer-surface-design-2026-09-20.md` | the five gates, fixed at `2e5097a5` |
| `scripts/probes/nyiso244_offer_surface_design.py` → `_nyiso244_offer_surface_design.json` | G1 / G2 / G3 / G4 |
| `scripts/probes/nyiso244_system_offer_curve.py` → `_nyiso244_system_offer_curve.json` | §6, descriptive, cohort-free |

**A correction owed to the record, repeated here from the PRECOMMIT so it is not buried.**
`nyiso243_offered_availability.py` Leg 3 reads "explicit AS offers" from the P-27 columns
`10 Min Non-Synch MW`, `10 Min Spin MW`, `30 Min Non-Synch MW`, `30 Min Spin MW` and
`Regulation MW`. Measured here, **the four reserve MW columns are 100 % null** in both DAM and
HAM across the archive — only `Regulation MW` is populated (8.7 % of DAM rows) — so Leg 3's
866 / 794 MW are **regulation only**, not the fleet's reserve holding. Leg 3 was explicitly a
diagnostic and never a gate, so **no nyiso-243 verdict moves**; the caveat it already carried
is simply larger than it stated. The reserve **Cost** columns *are* populated (15–22 % of DAM
rows), which is what §4's selector reads — the presence of an offer, not its size.
