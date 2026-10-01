# FINDING — nyiso-181 (`stgas-floor` lane): the C1-2023 `ST_GAS` over-generation is **ONE PLANT**, it is **ECONOMIC, not forced**, and the class aggregate that hid it also hides a 0.96 TWh/yr under-count in the committed D-2 forced-energy row

**Session:** nyiso-181, `stgas-floor` lane (`claude/nyiso-181-stgas-floor`), NYISO
backcast-calibration track, 2026-09-03. **Solves run: ZERO.**
**Keeper at entry and exit: `2026-09-02-nyiso-177-vintage-matched`**
(`results/calibration/nyiso177_vintage_B1p`) — determination **NOT-YET**, target grade 5,
fail set **{C1-2023 `ST_GAS` +3.86 TWh, C3a-2025 −11.2 %, C3c}**. **Unchanged.** No parameter
touched, no band swept, no `ScenarioConfig` field added, no arm built, `src/market_sim/`
untouched.
**Pre-registration:** `results/calibration/PREREG-nyiso181-stgas-floor-overgeneration.md`,
committed and **pushed to origin at `a1f717b5`** before the first measurement.
**Machine record:** `results/calibration/_nyiso181b_stgas_floor_overgeneration.json`
(probe `scripts/probes/nyiso181b_stgas_floor_overgeneration.py`).
**NO LEVER OPENED — PREREG §4 S2 FIRED**, on its own pre-declared terms.

---

## 1. The result in one paragraph

The 2023 `ST_GAS` cell misses by **+3.879 TWh** (model 12.020 against the scorer's
grid-delivered actual 8.141). Both hypotheses the pre-registration named — H1 that the
reliability floor binds in hours its driver evidence contradicts, H2 that the 2023 offer is too
cheap — **fail their material bars, and they fail because both are CLASS-AGGREGATE tests while
the class aggregate is a CANCELLATION.** At plant grain the object is one machine:
**Ravenswood (2500) runs +5.472 TWh above its own meter — more than the entire class miss —
while the other ten `ST_GAS` plants net −2.365 TWh.** (Both figures are measured against CAMPD
gross, on which the class total is +3.107 TWh; the scorer's grid-delivered basis puts the class
at +3.879. The ~9 % gross/net wedge changes no sign and no order of magnitude below.) Ravenswood's excess is **economic, not
forced**: 5.631 of its 6.328 TWh clears in or at the money, and its model availability is
**0.700 against a measured capacity factor of 0.062 — a ratio of 11.3, the largest in the class
by capacity.** Meanwhile the floor is doing the *opposite* job at the two Long Island plants
nyiso-140 confirmed run a genuine persistent baseline: Northport and Barrett take **1.920 of the
floor's 3.454 TWh** and are simultaneously **−3.415 TWh short economically**. The pre-registered
H1 violation is real and reported at full magnitude — **0.316 TWh of forced energy lands in
hours the plant's own CAMPD meter reads zero, 9.2 % of the mechanism**, above D-4's own 0.05 bar
— but it is **8.2 % of the miss**, not its carrier. A second, unlooked-for result falls out of
the same instrument: measured at its **native unit grain**, the reliability floor forces
**0.961 / 0.795 / 0.569 TWh a year more** `ST_GAS` than the committed plant-grain D-2 row
records, because `aggregate_floors_by_plant` nets a pinned unit against a free one at the same
site.

---

## 2. What was run, and the instrument

Zero solves for the adjudication. Dispatch, the LP's **own installed offer** (`mc`) and its
**reduced cost** come from `unit_hourly_stgas_<year>.parquet`; prices from the keeper's own
`system_<year>.parquet`; the floor matrices from `legitimacy_diagnostics.load_or_rebuild_floors`
/ `at_floor_mask` — **the D-2/D-4 gate's own basis, imported rather than re-implemented**, so the
`ct_only` skip and the span-union vintage guard are the ones the committed gates apply. The
measured per-plant series is D-4's own `bench_plant_view` view.

**Artifact provenance, disclosed:** the unit slice is committed in
`results/calibration/nyiso180_unitdispatch`, which lives on the **UNMERGED** PR #4656
(`claude/nyiso-180-per-generator-dispatch`, head `6addbda5`). It is **not on `main`**, so every
number below reproduces only against that branch until it merges. This session verified rather
than inherited its provenance (§3 I1).

## 3. Instrument checks — all three PASS, so no S1

| check | bar | measured | verdict |
|---|---|---|---|
| **I1** — the unit bundle IS the keeper | 0 differing class-hour cells, 0 differing zonal prices | **0 / 122,640** and **0 / 52,560**, max abs delta **0.0**, all three years | **PASS** |
| **I2** — the slice is the whole class | slice = `class_hourly` `ST_GAS` + a share of the pooled `oil` class | **12.0196 / 9.8326 / 10.1686** vs `class_hourly` 11.9990 / 9.7986 / 10.0143; residual **0.0206 / 0.0340 / 0.1543** | **PASS** |
| **I3** — `red_cost` sign is a valid in/out-of-the-money test | p95 \|Ω\| ≤ \$0.01/MWh | **4.7e-06 / 5.3e-06 / 6.2e-06** | **PASS** |

I1 independently reproduces PR #4656's bit-identity claim. I2's residual reproduces
**nyiso-180 §5's dual-fuel `oil` undercount to the fourth decimal** (0.021 / 0.034 / 0.154), from
a different artifact — an unplanned cross-check of that result. I3 re-confirms
nyiso-181 (merged lane) §6.4: whatever the non-energy rows charge this class, it is nothing.

**One population trap, found and fixed before any gate ran.** The committed slice is cut on
**fuel** (`gas_st`), so it carries the `ST_CHP` plant group too — 1.262 / 0.917 / 1.399 TWh of
it. Summed unfiltered it reads 13.281 TWh in 2023 against the class's 12.020, and every share
below would have been wrong by 10 %. `plant_group` is the pre-re-attribution class key
(nyiso-180's `klass_base`), so filtering on it is exactly what makes I2 close. **The model's
11 `ST_GAS` plants match the bench's 11 `ST_GAS` class slices one-for-one**, so nyiso-174's
East River adjudication is re-confirmed here as well: plant 2493 is `ST_CHP` on both sides and
contributes nothing to this cell.

---

## 4. THE PRE-REGISTERED GATES, AS MEASURED — three pass, two fail, and S2 fires

| prediction | bar | measured (2023) | verdict |
|---|---|---|---|
| **P1a** rule-17 violation | Z / reliability_floor forced ≥ **0.05** | **0.0916** | **PASS — the floor IS binding off its driver** |
| **P1b** H1 is the material carrier | Z ≥ **0.97 TWh** (25 % of the miss) | **0.3164 TWh** (8.2 % of the miss) | **FAIL** |
| **P1c** membership signature | top-2 plants ≥ **0.60** of Z | **0.7941** | **PASS** |
| **P2a** H2 is the material carrier | unforced excess ≥ **0.97 TWh** | **+0.3496 TWh** | **FAIL** |
| **P2b** 2023 clears more steam economically than 2024 | ≥ **5 pp** | **+8.2 pp** (0.7064 vs 0.6244) | **PASS** |
| **P3** the forced term must NOT carry the between-year swing | share explained **< 0.25** | **−0.041** | **CONFIRMED** |

**PREREG §4 S2 therefore fires: both P1b and P2a failed, so NO LEVER IS OPENED.** That was
pre-declared, it is honoured, and §5–§6 explain why it is also the substantively right call.

### 4.1 The partition, on the LP's own offer

Every dispatched `ST_GAS` unit-hour assigned once: **A** out of the money (`mc > price + $0.01`),
**B** marginal, **C** in the money.

| year | model | actual (`classFull`) | miss | **A forced** | B | C | A at a `reliability_floor` cell | A at no floor at all |
|---|---|---|---|---|---|---|---|---|
| 2023 | 12.020 | 8.141 | **+3.879** | **3.529** | 0.185 | 8.305 | 3.435 | 0.094 |
| 2024 | 9.833 | 9.913 | −0.081 | **3.693** | 0.140 | 6.000 | 3.525 | 0.168 |
| 2025 | 10.169 | 13.712 | −3.544 | **3.040** | 0.109 | 7.020 | 2.885 | 0.155 |

**97 % of the out-of-the-money energy sits at a reliability-floor cell**, and the floor is
essentially the *only* thing forcing this class: the gas commitment bridge is 0.11–0.17 TWh on
the committed D-2, and `A_not_at_any_floor` is 0.09–0.17 TWh. **Rule 19 `[R-ONE-MECH]` is
discharged and the answer is unambiguous — there is one mechanism here, and it is the
reliability floor.**

### 4.2 P3, and the shape of the problem

The forced term is nearly flat (3.529 / 3.693 / 3.040) while the miss swings +3.879 → −0.081.
Δ(A) between 2023 and 2024 is **−0.163 TWh** against a Δ(miss) of **+3.960** — it moves the
**wrong way**, explaining **−4.1 %** of the swing. The swing is carried entirely by the
*unforced* side: the model's economic `ST_GAS` falls **8.490 → 6.140 → 7.129** while the
measured class rises **8.141 → 9.913 → 13.712**.

---

## 5. WHY BOTH HYPOTHESES FAILED — the class aggregate is a cancellation

**POST-HOC.** Everything from here on was computed after the gate record above was written; the
`predictions`, `years`, `I1`–`I3` and `P3` blocks of the JSON are **byte-identical** before and
after the post-hoc block was added, verified programmatically. **No bar moved** (the nyiso-180
§8.1 / nyiso-181 §6.1 discipline: repair the instrument, never the threshold).

Measured per plant against the bench's own `ST_GAS` CAMPD slices (gross basis — the class
total is 8.913 gross against 8.141 grid-delivered, so plant deltas carry a ~9 % gross/net
wedge that changes no sign and no order of magnitude):

**2023**

| plant | model TWh | measured TWh | **Δ** | A (forced) | B+C (economic) | **economic excess** | floor forced | model avail | measured CF |
|---|---|---|---|---|---|---|---|---|---|
| **2500 Ravenswood** | 6.328 | 0.857 | **+5.472** | 0.697 | 5.631 | **+4.775** | 0.699 | **0.700** | **0.062** |
| 2490 Arthur Kill | 2.177 | 1.119 | +1.058 | 0.669 | 1.508 | +0.389 | 0.662 | 0.756 | 0.159 |
| 2625 Bowline | 0.129 | 0.976 | −0.847 | 0.021 | 0.108 | −0.868 | 0.036 | 0.135 | 0.105 |
| 2511 E F Barrett | 0.555 | 1.386 | −0.831 | 0.459 | 0.096 | −1.290 | 0.458 | 0.619 | 0.464 |
| 2516 Northport | 1.899 | 2.558 | −0.659 | 1.466 | 0.434 | **−2.125** | 1.462 | 0.473 | 0.200 |
| 2527 Greenidge | 0.164 | 0.665 | −0.501 | 0.034 | 0.131 | −0.535 | 0.000 | 0.852 | 0.794 |
| 2517 Port Jefferson | 0.078 | 0.325 | −0.247 | 0.033 | 0.045 | −0.280 | **0.000** | 0.819 | 0.105 |
| 8906 Astoria Gen | 0.610 | 0.780 | −0.170 | 0.149 | 0.461 | −0.319 | 0.135 | 0.169 | 0.105 |
| 8006 Roseton | 0.058 | 0.209 | −0.151 | 0.002 | 0.057 | −0.152 | 0.001 | 0.054 | 0.021 |
| 2682 S A Carlson | 0.000 | 0.017 | −0.017 | 0.000 | 0.000 | −0.017 | 0.000 | — | — |
| 2480 Danskammer | 0.021 | 0.020 | +0.001 | 0.001 | 0.020 | +0.000 | 0.001 | 0.281 | 0.007 |

**Ravenswood is +5.472 TWh; the other ten plants together are −2.365 TWh, on the same gross
basis that puts the class at +3.107.** On the *economic* (B+C) column the cancellation is
starker still: Ravenswood **+4.775** against **−5.197** everywhere else, netting **−0.422**
gross / **+0.350** on the scorer's delivered basis — which is the number P2a read, and it read
"no economic excess". **That is a defect in the
altitude of my own instrument, and the bar was mine.** It is reported here rather than argued
around: the pre-registered verdict stands as FAIL and the plant grain is what corrects it.

### 5.1 Ravenswood is the object, and it is not a floor problem

* Its excess is **economic**: **5.631 of 6.328 TWh** clears in or at the money.
* The floor is a bystander there — even at unit grain it forces **0.699 TWh**, and the
  committed plant-grain D-4 row sees only **0.0099 TWh over 57 hours**.
* The model runs it at **65 % of its available capacity**; the meter says **8.9 % of
  available** (6.2 % of maximum). **Availability 0.700 against a measured CF of 0.062.**
* It persists, shrinking as its availability falls: **+5.472 / +2.787 / +1.618 TWh** at
  availability **0.700 / 0.425 / 0.280**.

**This is not a new object — it is nyiso-177's, measured from the other end.** That session
established, with no solve, that `(2500, ST_GAS)`'s availability on the accurate per-unit
outage basis reads **0.129 / 0.097 / 0.111** against the keeper path's **0.772 / 0.465 /
0.297**, and its G2 found the `ST_GAS` outage envelope **over-booked 3.5–5×** on keeper and arm
alike, calling that "**the larger object**" and leaving it open (§6). **This session supplies
the dispatch-side consequence and one sharpening: the over-booking is not uniform — it is
INVERTED against measured conduct at exactly the plants that barely ran.** The ratio of model
availability to measured capacity factor, 2023: Danskammer **39.2×**, **Ravenswood 11.3×**,
Port Jefferson **7.8×**, Arthur Kill **4.8×**, Northport 2.4×, Barrett 1.3×, Greenidge 1.07×.
The plants nearest their meters are the ones that actually ran; the outliers are the
economically idle ones — **the nyiso-140 lay-up class, and Ravenswood is 1,580 MW of it.**

### 5.2 The floor is doing the OPPOSITE job at the plants that did run

Northport and Barrett — the two nyiso-140 verified as carrying a genuine 24-h baseline (cool-day
median CF 0.313 / 0.254 at h00–05) — take **1.920 of the floor's 3.454 TWh** in 2023 and are
**−3.415 TWh short economically**. Port Jefferson, the plant nyiso-140 excluded, takes
**exactly 0.000** in all three years: **the membership correction is verified live at unit
grain**, from an artifact that did not exist when it was made.

So the floor is substituting for a real economic deficit at the plants whose conduct justifies
it, while a separate, larger, purely economic excess sits at Ravenswood. **They are two
different objects that happen to nearly cancel in the class total** — which is why removing the
floor to close C1-2023 would be exactly wrong: it would deepen 2024 (−0.081 → −3.774) and 2025
(−3.544 → −6.583) to buy a year that a different defect is over-filling. The nyiso-140 cell's
standing warning — *"do NOT reach for this row to buy back volume"* — holds in the mirror
image here.

---

## 6. THE SECOND RESULT — the committed D-2 forced-energy row under-counts by ~1 TWh a year

**POST-HOC**, and it is not NYISO-specific. `aggregate_floors_by_plant` sums a plant's unit
floors and its unit dispatch, then asks whether the **plant total** sits at the **plant total
floor**. At a multi-unit site where one unit is pinned at its own floor while another runs
freely above it, the plant total is above the plant floor and **the pinned unit's forced energy
disappears from D-2 entirely.** The unit-grain artifact PR #4650 landed makes the native
measurement possible for the first time:

| year | **unit grain** | plant grain (this session) | committed D-2 (`reliability_floor` + bridge) | **under-count** |
|---|---|---|---|---|
| 2023 | **3.454** | 2.493 | 2.3604 + 0.1135 = 2.474 | **0.962 TWh (27.8 %)** |
| 2024 | **3.562** | 2.767 | 2.6376 + 0.1622 = 2.800 | **0.795 TWh (22.3 %)** |
| 2025 | **2.934** | 2.365 | 2.2908 + 0.1664 = 2.457 | **0.569 TWh (19.4 %)** |

**The instrument is validated by the middle column**: re-aggregating *this session's* unit data
under D-2's own plant-sum convention reproduces the committed total to **0.8 % / 1.2 % / 3.8 %**,
the residue being the P1-seam bridge that `run_year(fleet_only=True)` cannot rebuild. So the
gap in the outer columns is **grain, not method**.

Ravenswood is the extreme case and shows the mechanism cleanly: **0.699 TWh forced at unit
grain against 0.0099 TWh at plant grain — 70×** — because its plant total dispatch is far above
its plant total floor in almost every hour.

### 6.1 What that means for C8, stated as an escalation and NOT acted on

Rule 20 `[R-FORCED-BUDGET]` caps a merchant class at 30 % forced. Measured at unit grain against
the class's own unit-grain dispatch, `ST_GAS` reads **0.287 / 0.362 / 0.289**, and these are
**LOWER bounds** (the bridge is missing from the rebuild). The committed C8 reads **0.177 /
0.237 / 0.198** and PASSES. **2024's 0.362 is above the cap.** Two grain effects push the same
way and compound:

* the **numerator** loses the pinned-unit energy above (§6);
* the **denominator** gains every co-located non-`ST_GAS` unit at an `ST_GAS`-labelled plant.
  All eleven `ST_GAS` plants take an `ST_GAS` plant-grain majority label, and four of them are
  mixed: **Ravenswood carries 7 `CC_REGULAR` LP units** beside its 8 steam units, and
  Barrett / Port Jefferson / S A Carlson carry 4 `CT_PEAKER` units each. The committed class
  total accordingly exceeds the class's own dispatch by **1.983 / 1.971 / 2.250 TWh** — of which
  at most **0.350 / 0.242 / 1.010 TWh** can be `CT_PEAKER` (the whole model class), so the
  balance is **Ravenswood's combined-cycle output sitting inside the steam row's denominator**.

**This session does not act on it, and the restraint is deliberate, not an oversight.** The
defect is in `scripts/legitimacy_diagnostics.py`, i.e. **code-generic across all six ISOs**;
re-basing C8 to unit grain would move every ISO's protective gate; PREREG §4 S4 forbids this
session from adding a mechanism; and rule 25 `[R-ISO-SCOPE]` keeps this lane inside NYISO. It is
**escalated to the scorer/governance lane as a measured fact**, with the caveat that a re-based
C8 breach would not be an automatic fail — rule 20 escalates a material class above its cap to a
conditional pass on **D-4 provenance + D-1 shape**, and **NYISO's D-4 currently reads
`passed: false`** on the per-unit conduct rider (2023 plants 2480 + 2500; 2024 plants 2480, 2500
and the bridge's 54574).

---

## 7. The rule-17 violation, at full magnitude

P1a passes, so it is stated plainly rather than buried under P1b's failure: **0.316 / 0.268 /
0.049 TWh a year of reliability-floor energy lands in hours the floored plant's own meter reads
exactly zero** — 9.2 % / 7.5 % / 1.7 % of the mechanism, against D-4's own 0.05 off-window bar.

| plant (2023) | floored TWh | unit-hours binding | of them at meter zero | **Z TWh** | Z / plant |
|---|---|---|---|---|---|
| 2490 Arthur Kill | 0.662 | 52,497 | 27.2 % | **0.173** | 0.261 |
| 2516 Northport | 1.462 | 65,718 | 10.2 % | 0.078 | 0.054 |
| 2500 Ravenswood | 0.699 | 30,237 | 6.5 % | 0.041 | 0.059 |
| 2511 E F Barrett | 0.458 | 67,435 | 4.8 % | 0.012 | 0.026 |
| 8906 Astoria Gen | 0.135 | 29,438 | 9.3 % | 0.007 | 0.055 |
| 2625 Bowline | 0.036 | 573 | 12.9 % | 0.004 | 0.101 |
| 2480 Danskammer | 0.0009 | 90 | **100 %** | 0.0009 | 1.000 |

**Arthur Kill (2490) carries 55 % of it** and is the only plant with a double-digit share of its
own forced energy manufactured in metered-off hours. It sits on the **NYC persistent 24-h base
limb** (`tmax @ −50 °C`, `floor_pct` 0.175, `pro_rata`), the one enabled `ST_GAS` limb that has
**never had a membership review** — the LI twin got one at nyiso-140, and the three evening ramp
families are disarmed on this keeper.

**Why no membership repair is proposed anyway** (PREREG §4 S3 fixed the only admissible form in
advance, and no plant meets its evidentiary standard): nyiso-140's conviction required a plant
with **median when-available CF exactly 0.000 in every hour block of every year**. Arthur Kill's
committed D-4 median over its binding hours is **96.6 MW** and it generated 1.119 TWh in 2023 —
it plainly runs. Danskammer meets the conduct standard (100 % of its binding hours at meter
zero) and is already a **D-4 FAIL** in the committed artifact, but it is **0.0009 TWh — 0.02 %
of the miss**, and manufacturing a limb edit for it would be motion, not repair. **The rule-17
violation is real, it is small, and it is recorded rather than traded.**

---

## 8. What this does and does not touch in the inherited record

**Corrected:**

* **The lever queue's top item.** The parallel-lane amendment reads *"Top of queue is therefore
  2023 OVER-generation: enumerate what FORCES steam on … and whether the 2023 offer level is too
  cheap."* Both branches are now measured and **neither is the carrier at class grain**; the
  carrier is **one plant's availability**, and the enumeration it asked for is complete (§4.1:
  one mechanism, the reliability floor).
* **"2023's total gap is an opposite-signed object, not blocked behind C3a-2025."** Half-right.
  2023's *class* miss is indeed positive, but §5 shows it decomposes into Ravenswood (+) and a
  **−2.365 TWh deficit across the other ten plants**. Measured on the economic column and
  holding Ravenswood out, the deficit is **−5.197 / −6.776 / −7.957 TWh** in 2023 / 2024 / 2025 —
  **the same sign, and the same order, in all three years.** The deficit object spans the whole
  training window; only its arithmetic sign *at class level* is year-specific, because
  Ravenswood's excess is largest in 2023.

**Untouched:**

* **The keeper, its determination, target grade, fail set and every scored metric.** Nothing was
  solved; `metrics.json` is not read except to state the gate.
* **C3a-2025 −11.2 %**, which stays owner-court
  (`DECISION-CARD-nyiso148-2025-level-remainder` Q1). Nothing here disturbs it.
* **Every DO-NOT-REDO cell**: the loss surface, the post-solve transform, the capacity/label
  basis, `ramp_envelopes`-as-dominant-carrier, and the retired ITM statistic (which this session
  did not compute or cite).
* **nyiso-140's LI membership correction**, independently re-verified live (§5.2).
* **nyiso-174's East River adjudication**, independently re-confirmed (§3).

---

## 9. Honest expected value — what is NOT delivered

* **No lever, and S2 pre-declared that outcome.** The result is an attributed object and a
  measured instrument defect, not a mechanism.
* **The C1-2023 gate is not moved.** This session removes two explanations and supplies one
  attribution; it does not repair anything.
* **My own P2a was a badly-chosen statistic** — a class aggregate over a population that
  cancels — and it FAILED while the thing it screened for is present at 4.775 TWh in one plant.
  The bar was mine, it stands as failed, and the plant grain is disclosed as post-hoc.
* **The Ravenswood attribution is an accounting identity, not a causal proof.** It says the
  model's economic dispatch there exceeds its meter by 5.472 TWh and that its availability is
  11.3× its measured CF. It does **not** prove the availability basis is the cause rather than
  the offer, and this session ran no A/B that could separate them.
* **The gross/net wedge is not eliminated.** Plant deltas are model-net against CAMPD-gross
  (class-level 8.913 gross vs 8.141 delivered, a 9 % wedge). No sign or order of magnitude in
  §5 turns on it; no plant claim rests on a margin narrower than it.
* **The C8 grain finding is measured, not adjudicated.** Whether the gate should be re-based is
  a scorer/governance decision for another lane; the numbers here are lower bounds.
* **Ω is not decomposed per row.** Inherited verbatim from nyiso-180 §3 / nyiso-181 §6.4; I3
  bounds it as negligible for this class and attributes none of it.
* **Reproducibility cost, named:** the unit slice lives on the unmerged PR #4656. Until that
  merges, every number here needs that branch (or a ~15-minute keeper replay).
* **Rule 15 registers nothing, and that is the correct outcome, not a gap** — no non-control
  solve was run (the nyiso-180 / nyiso-181 precedent for a zero-solve lane).

---

## 10. Governance

* **Rule 1 `[R-STRUCT]`** — no residual was consulted in choosing what to measure, and nothing
  was adopted or rejected on whether it moved a fit. §5.2 explicitly declines the fit-improving
  move (deleting the floor closes 2023 and breaks 2024/2025).
* **Rule 5 `[R-NO-MAGIC]` / 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero parameters touched,
  zero swept, nothing re-derived.** Every coefficient in §4.1 and the limb CSV was READ.
* **Rule 13 `[R-MEASURED]`** — measured CAMPD conduct is used **only to diagnose**, never as an
  input. PREREG §4 S4 pre-emptively forbade the same-year hourly-availability gate that would
  close this gate and has no forward analogue; it was not built.
* **Rule 14 `[R-ACCURATE]`** — §5.1 is this rule pointing at an open object: the accurate
  per-unit availability basis reads 0.129 for Ravenswood and the keeper path reads 0.772, and
  the *less* accurate value is the one currently manufacturing volume.
* **Rule 15 `[R-DASHBOARD]`** — zero solves, nothing to register (§9).
* **Rule 16 `[R-ALLYEARS]` / 12 `[R-PARALLEL]`** — every measurement spans 2023 + 2024 + 2025;
  no solve, so no year loop.
* **Rule 17 `[R-FLOOR-WINDOW]`** — §1 of the PREREG states each enabled limb's driver, window
  and forward story before anything was proposed; §7 measures the window's evidence per hour
  and reports the violation at full magnitude without trading on it.
* **Rule 19 `[R-ONE-MECH]`** — discharged in PREREG §1 before any proposal and confirmed
  numerically in §4.1: one mechanism floors this class.
* **Rule 20 `[R-FORCED-BUDGET]`** — §6.1, escalated as a measured fact, not acted on.
* **Rule 22 `[R-HOLDOUT]`** — every year is 2023 / 2024 / 2025. NYISO is absent from both
  `complete` and `final`; **no marker was requested**; the locked-test freeze is untouched.
* **Rule 24 `[R-REGISTRY]`** — **no new tunable**, no env-var knob, no CLI flag.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only; only the NYISO matrix shard edited. §6.1's
  code-generic defect is explicitly NOT repaired here for this reason.
* **Rule 27 `[R-PUSH]`** — **no existing source file was modified.** The probe is a new file;
  the pushed blobs are the exact local bytes.
* **Rule 28 `[R-MECH-MATRIX]`** — §11.

## 11. Matrix (rule 28 b)

NYISO shard only. **No verdict moves.**

* **`reliability_floor` stays `K`**, annotated with this session's measurement: it is the sole
  mechanism forcing `ST_GAS` (97 % of out-of-the-money energy), it forces 3.454 / 3.562 / 2.934
  TWh at **unit** grain (0.96 / 0.80 / 0.57 TWh more than the committed plant-grain D-2 row),
  and 9.2 % / 7.5 % / 1.7 % of that lands in metered-off hours — a real rule-17 violation, 55 %
  of it on the never-membership-reviewed **NYC** persistent-base limb, and **8.2 % of the
  C1-2023 miss**, so **not** its carrier.
* **`reliability_floor_plant_exclusions` stays `K`**, re-stamped: the nyiso-140 exclusion is
  **verified live at unit grain** (Port Jefferson takes exactly 0.000 TWh in all three years).
* **`campd_outage_merit_order_guard` / the availability family stays `K`**, annotated with the
  dispatch-side consequence of nyiso-177's open §6 object.
* `offer_curve_by_group`, `dual_fuel_switching`, `gas_commitment_bridge`, `ramp_envelopes` and
  `energy_reserve_coopt` are **not** re-opened and their cells are not rewritten.

## 12. Handed forward

1. **THE OBJECT IS RAVENSWOOD (2500), AND IT IS AN AVAILABILITY OBJECT, NOT A FLOOR ONE.**
   +5.472 / +2.787 / +1.618 TWh over its own meter; economic, not forced; model availability
   0.700 / 0.425 / 0.280 against measured CF 0.062 / 0.049 / 0.077. **This is nyiso-177 §6's
   open object with its dispatch consequence attached** — the successor should take it there,
   not in the floor.
2. **DO NOT DELETE OR NARROW THE `ST_GAS` RELIABILITY FLOOR TO CLOSE C1-2023.** It closes 2023
   by breaking 2024 (−0.081 → −3.774) and 2025 (−3.544 → −6.583), and it is substituting for a
   real economic deficit at the two plants whose conduct justifies it (§5.2). The
   nyiso-140 no-volume-buying warning applies in mirror image.
3. **THE DEFICIT OBJECT SPANS ALL THREE YEARS.** Excluding Ravenswood, `ST_GAS` is
   **−5.197 / −6.776 / −7.957 TWh** economically short (class totals including Ravenswood:
   −0.422 / −4.523 / −6.608). The class-level sign flip in 2023 is arithmetic, not a separate
   phenomenon (§8).
4. **THE NYC PERSISTENT-BASE LIMB HAS NEVER HAD A MEMBERSHIP REVIEW.** Its LI twin got one at
   nyiso-140. Arthur Kill manufactures 26.1 % of its own forced energy in metered-off hours.
   **No repair is proposed here** — no plant on it meets nyiso-140's evidentiary standard
   (§7) — but a lane that re-derives the limb should look at it, from source data, never at a
   residual.
5. **ESCALATED, NOT ACTED ON — the D-2 / C8 grain under-count** (§6). It is code-generic across
   six ISOs, so it needs the scorer lane, not this one. NYISO `ST_GAS` at unit grain is
   0.287 / **0.362** / 0.289 against rule 20's 0.30 cap, as lower bounds.
6. **MERGE PR #4656 OR THE NUMBERS HERE DO NOT REPRODUCE FROM `main`** (§2, §9).
7. **UNCHANGED and not opened:** C3c (SUPPORTING, not lone); C3a-2025 (owner-court); the
   measured-availability family as a *lever*, the merit guard, an `ST_GAS` duty curve,
   `gas_st_startup_cost`, `gas_st_committed_hr_mult`; the missing rung.
