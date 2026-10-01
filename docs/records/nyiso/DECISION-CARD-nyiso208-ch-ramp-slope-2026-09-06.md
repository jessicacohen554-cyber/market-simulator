# DECISION CARD — nyiso-208: one live NYISO floor coefficient is **unidentified**. The shipped construction gives **2.04×** it, and nine constructions fail to reach it. What should happen to `CH_ST_ev`?

**For:** the owner. **From:** session nyiso-208, NYISO `backcast-calibration` lane, 2026-09-06.
**Zero solve. Nothing armed, nothing re-scored, no `src/market_sim/` change, no derive-script
change, no coefficient edit, no CSV edit, no scorer edit, no marker touched.**

**Evidence:** `docs/FINDING-nyiso208-ramp-slope-census-2026-09-06.md`; machine records
`results/calibration/_nyiso208_ramp_slope_census.json`, `_nyiso208_posthoc_addendumA.json`;
pre-registration `results/calibration/PREREG-nyiso208-ramp-slope-census.md` **+ addendum A, declared
POST-HOC and committed before it was run**.
**Keeper, unchanged:** `2026-09-06-nyiso-202-startup-aware` (CALIBRATED, fails 0).

> **Read this first.** **Nothing on this card is urgent, and nothing on it is a proposal to change a
> coefficient.** The limb passes both structural gates this session put to it, its forcing is
> **0.030 TWh over three years**, and the "repair" its own prose points at would make that forcing
> **larger**, not smaller. The lane's reading is **Option A**.

---

## 1. What was measured

nyiso-207 censused every live NYISO floor **percentile** and left one row explicitly undiagnosed —
`CH_ST_ev`'s cap knot, whose prose names a *regression*, not a percentile. This session ran the
complement: the ramp **slopes**, which no session had ever reproduced.

**The instrument is the shipped derive script itself**, run with its own defaults. It emits all four
zones in one pass, and for the controls **everything it prints matches the frozen CSV to the digit**:

| control | frozen / prose | measured | |
|---|---:|---:|:---:|
| NYC ST slope | 0.0628 | 0.0628 | ✓ |
| Long_Island ST slope | 0.0424 | 0.0424 | ✓ |
| downstate CT slope | 0.0535 | 0.0535 | ✓ |
| six percentiles (NYC / LI / CT) | — | all match | ✓ |
| NYC / LI evening Pearson r | +0.186 / +0.547 | +0.186 / +0.547 | ✓ |
| **Capital_Hudson ST slope** | **0.0246** | **0.0502** | **✗ — 2.041×** |

Two independent cross-checks confirm the instrument: the percentiles agree with nyiso-207's
separately-written census, and this session's CH forced-energy sizing lands on **0.03035 TWh**,
matching nyiso-207 §6's CH figure to five decimals.

**Nine constructions were measured; none reaches 0.0246. The minimum is 0.0400 — 1.63× frozen.**

| construction | slope | ÷ frozen |
|---|---:|---:|
| shipped, pooled 2023–25 | 0.0502 | 2.04× |
| 2023 / 2024 / 2025 alone | 0.0443 / 0.0586 / 0.0474 | 1.80–2.38× |
| 2023–24 / 2024–25 | 0.0509 / 0.0535 | 2.07 / 2.17× |
| nameplate basis (derate off) | **0.0400** | **1.63×** |
| CF clipped at the 1.0 physical bound | 0.0496 / 0.0400 | 2.02 / 1.63× |

**The session's own alternative hypothesis is refuted, in direction.** PREREG §5 P2 predicted CH
might be a stale **pre-guard-fix** value — which would have made it *too high*. It is *too low*, and
the mechanism is dead on its own terms: the outage derate reaches **99.64 %** of CH hours, and
removing it moves the slope only to 0.0400.

## 2. What cuts the other way — and it is most of the story

Both were pre-registered, and both **PASS**:

- **The frozen floor does not over-force.** **64.6 %** of CH hot days meter at or above the applied
  fraction. The floor reaches 0.0812 at the median hot day and **0.2609** at the hottest observed
  day (35.6 °C) against a hot-day median CF of **0.311** — **below** the class's own conduct even at
  the top of the range. No rule-17 `[R-FLOOR-WINDOW]` over-forcing defect.
- **The h14–21 window is correct for this zone.** Hot-day median CF inside the window is **4.49×**
  the complementary hours, and the block profile peaks at **h16–19, inside it**. The charter's
  alternative object closes as a **clean negative**.

## 3. Why it is nonetheless the owner's call and not a lane fix

- **Rule 23 `[R-FROZEN-DERIVE]` has no trigger.** No source data has updated. This is the same
  binding objection nyiso-203 §7 and nyiso-207 §7 raised, and this session does not disturb it.
- **It would MOVE a live coefficient on a CALIBRATED ISO** (`fails 0`), so it is a mechanism change
  owing its own PREREG, rule-29 screen and full span — none of which this session has or should have.
- **The leading explanation is untested by this session's own binding.** A **pre-2023 identification
  span** would explain the gap; testing it means reading `NY_2019/2020/2021/2022`, which PREREG §7
  declared out of bounds. It is named here rather than resolved.
- **The same untested exposure exists on five other ISOs** — both derive scripts have per-ISO
  siblings whose slopes are equally unreproduced — and rule 25 `[R-ISO-SCOPE]` makes that owner
  court, exactly as nyiso-206 §5 and nyiso-207 §7 refused.

## 4. The direction is the decision-relevant fact

Pooled 2023–2025, over the limb's own h14–21 hours:

| | frozen 0.0246 | measured 0.0502 |
|---|---:|---:|
| floor energy demanded | 0.334 TWh | 0.607 TWh |
| **excess over metered** | **0.030 TWh** | **0.072 TWh** |
| floor fraction at 35.6 °C | 0.2609 (**below** hot-day median 0.311) | 0.532 (**above** it) |

**nyiso-207's construction gap, if repaired, REDUCES forcing (−0.068 TWh on the largest live evening
limb). This one, if "repaired" toward its own named construction, INCREASES it by +0.042 TWh** — and
pushes the floor above the class's observed hot-day conduct, which is the condition rule 17 calls a
defect. **The two open coefficient questions point in opposite directions.** That, more than either
magnitude, is what this card asks you to weigh.

## 5. Options, each with its measured cost

### Option A — **change nothing; record the measured slope and the gap in the row's own prose** *(the lane's recommendation)*

State in row 47's `threshold_basis` that the frozen 0.0246/°C does **not** reproduce from the shipped
hot-day regression at HEAD (which gives 0.0502), that nine constructions were tested and none
reaches it, and that the value is **retained deliberately** because it sits below the class's
observed conduct while the reproducing value would sit above it.

- **Solve impact: zero.** Byte-identical for every ISO, every keeper, every year.
- **DOF: zero.** No parameter moves.
- **Cost:** the model keeps one live coefficient whose stated construction does not produce it.
  Option A does not close that — it stops the CSV asserting a derivation it cannot reproduce.
- **Defensible on:** §2 and §4 — the limb passes both structural gates, forces 0.030 TWh, and the
  reproducing value is the *worse* one on rule-17 grounds.

### Option B — **re-derive to 0.0502 (the shipped construction, zero new free parameters)**

- **Measured effect:** floor energy 0.334 → 0.607 TWh; excess over metered 0.030 → **0.072 TWh**;
  the floor at CH's hottest observed hour rises from 0.2609 to **0.532, above** the class's hot-day
  median CF of 0.311.
- **Cost 1 — no rule-23 trigger** (§3).
- **Cost 2 — it makes the structural picture worse, not better.** P5's margin (64.6 %) falls to
  61.3 % and the limb starts forcing above observed conduct at the top of its range.
- **Cost 3 — the estimator is poor for this class.** CH's response to heat is a **commitment**
  response, not a loading one: hot-day median CF 0.311 vs mild-day **0.000**, yet **40.2 % of hot
  days are at exactly zero**, Pearson r **+0.041**, Spearman +0.104, max CF 4.63. An OLS slope on
  daily CF is a weak instrument for a binary start decision — which is **pending ruling (i)**
  (nyiso-206: is `floor_pct` a class-commitment share or a per-unit loading rule?) showing up as a
  live case. **Not proposed.**

### Option C — **resolve the identification: test the pre-2023 span**

Re-run the same construction on 2019–2022 to find the span that produces 0.0246. **Source data only,
zero LP, minutes.** This session declined it under its own PREREG §7 binding, not because it is
hard.

- **Buys:** the actual answer, most likely. If a pre-2023 span reproduces 0.0246, the coefficient is
  identified-but-stale and the question becomes a clean rule-23 one.
- **Cost:** it means **reading** out-of-training CAMPD extracts. Rule 22 `[R-HOLDOUT]` says plainly
  that *"what is held out is the SCORE, never the DATA"* and that the spend is **solving, scoring or
  registering** — none of which this is. **The lane's reading is that Option C is permitted by rule
  22 as written**, and it declined only because its own pre-registration had bound it. **Confirming
  that reading is what this card most needs from you**, because it is a precedent beyond this row.

### Option D — **measure the same slope census on the other five ISOs**

Both derive scripts have per-ISO siblings; no ISO's ramp slopes have ever been reproduced.

- **Buys:** whether an unreproducible slope is a NYISO peculiarity or the norm.
  `DECISION-CARD-nyiso193` §5.1 is the cautionary precedent — two ISOs measured, **both** breached.
- **This lane cannot run it** (rule 25). It is the **same cross-ISO tasking** that
  `DECISION-CARD-nyiso206` and `-nyiso207` each ask for, on the same grounds; **all three could be
  tasked together as one census.**

## 6. What a ruling would need to say

1. **Is Option C permitted?** Reading (not solving or scoring) an out-of-training extract to identify
   a frozen coefficient — the lane reads rule 22 as **yes** and did not act on it. This is the
   precedent question and it outlives this row.
2. **If 0.0246 turns out to be a pre-2023 draw, does that constitute a rule-23 source-data trigger?**
   The data did not change; the *span* did. That is a different thing and is unruled.
3. **Does a coefficient that does not reproduce, but is conservative and passes its structural
   gates, need repairing at all?** §4 says repairing it makes the structure worse.
4. **Should the three pending cross-ISO censuses (nyiso-206, -207, -208 Option D) be tasked as one?**
5. **Nothing here is urgent.** NYISO reads `fails 0`; the limb forces 0.030 TWh over three years
   against 2.358 TWh of metered CH evening energy; and no gate, criterion or determination moves
   either way.

## 7. What the lane refuses to do

**Edited no coefficient**, **proposed no replacement value** (0.0502 / 0.0400 / 0.0496 are
measurements of the gap, and PREREG §7 + addendum §A.4 bound that in every branch *before* the
numbers were seen), **changed no derive script**, **re-tested nothing** marked `R`/`I`/`G`, and
**measured no other ISO**. It did not touch the `offer_curve_by_group` channel (owner court,
carve-out condition (c)), opened no metrics file, price series or scored criterion, and read no
out-of-training extract. NYISO's keeper is unchanged and its markers are untouched (`complete`
WITHDRAWN under Q5; `frontier` withdrawn on the determination limb; C-19 / Q51 PARKED).
`DECISION-CARD-nyiso193`, `-nyiso206` and `-nyiso207` all stay **UNRULED**.

---

*(nyiso-208, 2026-09-06. Zero LP. Nine of ten live coefficients reproduce exactly; the tenth does
not, under any of nine constructions — and repairing it would make the model worse. The ruling is
the owner's.)*
