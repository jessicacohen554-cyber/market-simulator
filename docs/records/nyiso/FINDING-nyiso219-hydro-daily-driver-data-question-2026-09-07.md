# FINDING nyiso-219 — the daily-inflow driver **exists and is excellent**, and it **cannot close this residual**. The real NYISO hydro fleet tracks **load** better than it tracks **flow**

**Session:** nyiso-219, NYISO backcast calibration. **Branch:**
`claude/nyiso-hydro-within-month-cq14o1`, on `main` at `ad78cc3e`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **untouched. Nothing armed, screened, solved or
registered; no marker moved; no matrix cell letter changed; no held-out year spent.**
**ZERO LP.** **PREREG:** `results/calibration/PREREG-nyiso219-hydro-daily-driver-data-question.md`,
committed and pushed **before any number below was read**.
**Instruments (both committed, both deterministic — re-running each reproduces its JSON
byte-identically):** `scripts/probes/nyiso219_hydro_daily_driver_census.py` →
`results/calibration/_nyiso219_hydro_daily_driver_census.json`;
`scripts/probes/nyiso219_posthoc_overresponse.py` →
`_nyiso219_posthoc_overresponse.json`; cached source data
`_nyiso219_usgs_daily_discharge.csv.gz` (USGS NWIS, public domain).

---

## 0. The result in one paragraph

nyiso-218 §8 localized NYISO's hydro residual to **within-month, day-to-day allocation**
(r 0.207–0.392) and handed over an open data question: does a forward-drivable,
condition-responsive daily flow driver exist for NYISO's basins? **It does, and the data is better
than expected** — 100 % of the fleet resolves to a published EIA-860 water source, and every
material basin has a USGS daily-discharge record at **100.0 % coverage and 100 % USGS-approved**
across 2019–2025, public domain, forward-available in near-real time. **And it cannot close this
residual.** Measured basin discharge reaches within-month daily **r = 0.243 mean (0.095–0.327)**
against the actual — *below* the keeper's own 0.392 in 2023 and its 0.358 in 2022 — because
**71.4 % of the fleet's MW sits on regulated Great-Lakes outflow** whose day-to-day signal is
almost nil: Niagara (**51.9 % of MW**) mean r **0.079**, St Lawrence (**19.5 %**) **0.080**, against
a 4 %-of-MW Adirondack cascade at **0.265**. A leave-one-year-out day-of-year climatology — the
other candidate nyiso-218 floated — carries **essentially zero** information (mean r **0.031**, max
|r| 0.074), so that option is now **closed**. What the measurement *did* find, and did not predict:
the **actual** fleet's within-month daily allocation tracks **daily load at mean r 0.307** — *higher
than flow* — while the keeper tracks load at **0.616–0.686** with **1.86–2.25×** the actual's
day-to-day amplitude. **The model is not missing a driver. It has the right driver and responds to
it about twice too hard.**

**Nothing here is a mechanism proposal.** The successor object is handed to the owner as §6.

---

## 1. What was asked, and the scope discipline

**Deliverable (a) of the handoff:** a measured answer to the daily-inflow data question, with
coverage, vintage, licence and fleet mapping stated, and rule 13 `[R-MEASURED]`'s test applied in
writing. This finding is that answer; §7 is deliverable (b) built on top of it.

**There are NO in-sample rubric failures.** NYISO's keeper reads **CALIBRATED**, grade 7/8, **zero
failing criteria** across 2023–2025, C3c the lone ledgered caveat. The only failing cells in the
NYISO record are on the **2022 validation holdout**, and rule 22 `[R-HOLDOUT]` forbids targeting
them. **This session targets none of them.** Its object is structural and is **not a rubric
criterion at all** — no hydro row in `fuelRows`, no hydro record in any C-criterion.

**No held-out year is spent.** §§3–5 read **measured data only** outside 2023–2025 (EIA-930
`NG: WAT` actuals; USGS discharge). **No out-of-training model output is read, no score is computed
for one, nothing is solved or registered.** Rule 22 is explicit that what is held out is the
**score**, never the **data**. The one place model output enters (§5, PH-1) is restricted to the
**training tier 2023–2025** and the keeper's own committed hourlies.

**Basis re-verified by execution, not assumed:** NYISO is in neither `EIA930_PS_FOLDED_INTO_WAT`
(MISO, PJM) nor `EIA930_PS_SPLIT_COMPLETE_FROM` (NEISO: 2025), so `eia930_wat_level_folded` is
**False in every year** — `NG: WAT` is conventional hydro only and Blenheim-Gilboa pumped storage is
booked under the model's `storage` klass. **Conventional-only on both sides.**

**Keeper `cache_key` re-measured at this HEAD:** `95d4d8d167373eb7`, identical to the value recorded
at `71e62675`, `12e71b89` and `bfbb0b6a`. Fleet instrument validated
(`nyiso196_rebuild_checks.py --year 2024` exit 0, working tree clean). **No G-DRIFT audit is owed:
no solve was performed, so there is no arm, no control and no keeper-differencing.**

**Cells already adjudicated — not re-tested, not re-proposed:** `hydro_ror_split` **G**
(governance-refused, nyiso-111), `hydro_budget_nameplate_aware` **I** (provably inert, nyiso-107).
`hydro_dispatch_envelope`, `hydro_min_flow_floor`, `nyiso_hydro_reserve_eligible` are **K** and
already armed.

## 2. M1 — the fleet → water-source census: **the data is complete**

Every one of NYISO's **163 conventional-hydro plants (4,681.0 MW)** joins the EIA-860 plant file and
carries a published **`Name of Water Source`**. No geocoding, no guess.

| water source | MW | plants | % fleet MW | cumulative |
|---|---:|---:|---:|---:|
| **Niagara River** | 2,429.1 | 1 | **51.893** | 51.893 |
| **St Lawrence River** | 912.0 | 1 | **19.483** | 71.376 |
| Hudson River | 257.3 | 11 | 5.497 | 76.872 |
| Raquette River | 184.9 | 18 | 3.950 | 80.822 |
| Black River | 108.6 | 17 | 2.320 | 83.142 |
| Mohawk River | 76.7 | 5 | 1.639 | 84.781 |
| Sacandaga River | 60.5 | 2 | 1.292 | 86.073 |
| Genesee River | 55.1 | 3 | 1.177 | 87.251 |
| Oswego River | 53.4 | 8 | 1.141 | 88.391 |
| … 30+ further sources … | | | | |

**Predictions scored as written:**

| id | prediction | measured | verdict |
|---|---|---|---|
| **P1b** | ≥ 6 distinct water sources needed for 95 % of fleet MW | **18** | **CONFIRMED** |
| **P1c** | no single non-Great-Lakes source > 12 % of fleet MW | largest is **Hudson 5.50 %** | **CONFIRMED** |
| **P1d** | ≥ 90 % of the 163 plants resolve to a non-empty water source | **100.0 %** of plants, **100.00 %** of MW, **0 unmatched** | **CONFIRMED**, partition branch (i) |

**Great-Lakes outflow = 71.38 % of fleet MW in two plants.** That single number governs everything
below: the fleet is not a river fleet, it is **two lake-outflow projects plus a long tail**.

## 3. M2 — the gauge census: **the data exists, and it is excellent**

USGS NWIS daily mean discharge (parameter `00060`, statistic `00003`), 2019–2025, per material water
source. **Licence: public domain** — a work of the U.S. Geological Survey, an agency of the U.S.
government, carrying no use restriction. **Forward availability:** the same NWIS daily-values
service publishes provisional values within ~1 day and approves them on the annual review cycle, so
the identical query regenerates for any future year.

| water source | % fleet MW | USGS site | coverage 2019–25 | approved | **CV whole-period** | **CV within-month** |
|---|---:|---|---:|---:|---:|---:|
| Niagara River | 51.89 | 04216000 Buffalo NY | **100.0 %** | **100 %** | 6.04 % | **4.01 %** |
| St Lawrence River | 19.48 | 04264331 Cornwall Ont nr Massena NY | **100.0 %** | **100 %** | 8.25 % | **3.11 %** |
| Hudson River | 5.50 | 01327750 Fort Edward NY | **100.0 %** | **100 %** | 59.76 % | 24.31 % |
| Raquette River | 3.95 | 04267500 South Colton NY | **100.0 %** | **100 %** | 63.05 % | 37.23 % |
| Black River *(sub-threshold)* | 2.32 | 04260500 Watertown NY | **100.0 %** | **100 %** | 74.69 % | 38.98 % |
| **Mohawk *(runoff comparator)*** | 1.64 | 01357500 Cohoes NY | **100.0 %** | **100 %** | **97.57 %** | **56.48 %** |

Every material basin lands in partition **branch (i)** — approved daily series at ≥ 99 % coverage.
Branches (ii)–(v) did not fire for any basin; **no instrument failure occurred**.

**Predictions scored as written, including a disclosed miss:**

| id | prediction | measured | verdict |
|---|---|---|---|
| **P2a** | non-Great-Lakes material basins have ≥ 99 % daily coverage 2019–25 | Hudson **100.0 %**, Raquette **100.0 %**, both 100 % approved | **CONFIRMED** |
| **P2b** | Niagara day-to-day CV **< 5 %** | within-month **4.01 %**; whole-period **6.04 %** | **SPLIT — confirmed on one construction, MISSED by 1.04 pts on the other** |
| **P2c** | St Lawrence day-to-day CV **< 5 %** | within-month **3.11 %**; whole-period **8.25 %** | **SPLIT — confirmed on one construction, MISSED by 3.25 pts on the other** |
| **P2d** | a Mohawk-class runoff river CV **> 40 %** | within-month **56.48 %**; whole-period **97.57 %** | **CONFIRMED on both** |

**The P2b/P2c miss is reported, not rewritten.** The PREREG wrote "day-to-day coefficient of
variation" **without pinning the construction**, and named that gap in advance. Both readings are
therefore reported and both predictions scored against both. On the **within-month** construction —
the one the object is defined on, and the one nyiso-218 used for its own 0.00000 ceiling CV — P2b
and P2c are confirmed. On the **whole-period** construction, which carries the seasonal cycle, both
miss the 5 % threshold. **The absolute threshold was set too tight; the separation it was testing
for is not in doubt in either reading:** the regulated Great-Lakes outflows carry **14–18×** less
within-month day-to-day variation than the Mohawk (4.01 / 3.11 vs 56.48 %), and **9–16×** less on
the whole-period reading. That separation is the substantive claim, and it survives both
constructions.

## 4. M3 — the decisive measurement: **no admissible driver carries the missing signal**

Every candidate scored on the **identical statistic** whose model-vs-actual value is 0.207–0.392
(Pearson r of `daily_total − that day's calendar-month mean`, 365 days), against measured
EIA-930 `NG: WAT`:

| year | **D-A** LOYO climatology | **D-B** basin discharge | **D-C** daily load | Mohawk alone | *keeper's own* |
|---|---:|---:|---:|---:|---:|
| 2019 | 0.048 | 0.197 | 0.166 | 0.140 | — |
| 2020 | −0.035 | 0.095 | 0.283 | 0.112 | — |
| 2021 | 0.067 | 0.309 | 0.267 | 0.255 | — |
| 2022 | 0.025 | 0.223 | 0.358 | 0.163 | *0.358* |
| 2023 | −0.016 | 0.301 | **0.467** | 0.156 | *0.392* |
| 2024 | 0.055 | 0.249 | 0.204 | 0.084 | *0.248* |
| 2025 | 0.074 | 0.327 | **0.410** | 0.043 | *0.207* |
| **mean** | **0.031** | **0.243** | **0.308** | 0.136 | — |

*(The keeper column is the inherited nyiso-218 value, shown for scale; 2022 is its stamped
touchpoint. **D-X, the forbidden outcome pin, is r = 1.000 by construction** — named only as the
scale anchor and the tripwire, never built.)*

| id | prediction | measured | verdict |
|---|---|---|---|
| **P3a** | D-A climatology ≤ 0.20 **in every year** | max **0.074**, mean **0.031** | **CONFIRMED, by a wide margin** |
| **P3b** | D-B lands in **0.20 < r < 0.55** | **5 of 7 years** in band; **2019 (0.197) and 2020 (0.095) fall in the ≤ 0.20 branch**; mean 0.243 | **PARTIAL MISS — hit in 5/7, missed low in 2/7. The ≥ 0.55 flip branch did NOT fire in any year.** |
| **P3c** | actual-vs-load ≥ +0.25 **in every year** | **5 of 7** ≥ 0.25; **2019 (0.166) and 2024 (0.204)** land in the (0, 0.25) band the PREREG named as confirming neither limb | **MISS as written** — but **positive in all seven years** (mean 0.308), so the "≤ 0 ⇒ load-indifferent" branch did not fire either |
| **P3d** | an accurate driver may score **worse** than the model does now, and stays anyway | **it does — see below** | **CONFIRMED, and it is the load-bearing one** |

**P3b is the prediction that was written to falsify this session's own preferred answer, and it did
not fire.** The flip branch (D-B ≥ 0.55 ⇒ "build the inflow driver") required r ≥ 0.55; the highest
value in any year under any construction is **0.327**. **Robustness — every alternative D-B
construction was computed, and none reaches the flip:**

| D-B construction | mean r | max in any year |
|---|---:|---:|
| MW-weighted, mean-normalized *(the pre-registered one)* | 0.243 | 0.327 |
| equal-weighted across the four material basins | 0.267 | 0.417 |
| alternative gauges (Hudson at Hadley, Raquette at Raymondville) | 0.217 | 0.313 |
| non-Great-Lakes basins only (Hudson + Raquette + Black) | 0.251 | 0.400 |
| Raquette alone — the single best flow predictor | 0.265 | 0.362 |

**A construction note that cuts against the inflow hypothesis, stated rather than buried:** the D-B
weights are **nameplate MW**, not energy. Niagara and St Lawrence are high-capacity-factor
run-of-river projects, so their share of fleet *energy* exceeds their 71.4 % share of MW. An
energy-weighted index would be **more** dominated by the two near-flat series and would score
**lower**. The pre-registered construction is therefore **generous** to the inflow hypothesis, and
it still does not reach the flip.

### 4a. Why — the per-basin decomposition

Mean within-month daily r against actual `NG: WAT`, 2019–2025:

| water source | **% fleet MW** | **mean r** |
|---|---:|---:|
| **Niagara River** | **51.89** | **0.079** |
| **St Lawrence River** | **19.48** | **0.080** |
| Hudson River | 5.50 | 0.142 |
| **Raquette River** | **3.95** | **0.265** |

**The river under 52 % of the fleet's MW carries almost none of the day-to-day signal, and the best
single flow predictor is a 4 %-of-MW Adirondack cascade.** This is not a data-quality problem — both
Great-Lakes records are 100 % complete and 100 % approved. It is **hydrology and treaty law**: the
Niagara is Lake Erie's outflow and the St Lawrence is Lake Ontario's, each buffered by an inland sea
and each governed by a published regulation plan rather than by last week's rain. Their **day-to-day
flow barely moves** (§3: within-month CV 4.01 % and 3.11 %), so **there is no daily inflow signal to
give the model for 71.4 % of its hydro fleet** — not because the measurement is missing, but because
the physical quantity is nearly constant.

## 5. What the measurement found that it did not predict — **POST-HOC, moves no gate**

**Every number in this section is post-hoc.** It was computed after the pre-registered numbers were
read, it scores no criterion, it moves no gate, and it is reported as a follow-up reading rather
than as a confirmed prediction. It is here so that §6's successor object rests on evidence rather
than on inference. Model output is read for **2023–2025 only** (rule 22).

**Instrument self-check first:** reconstructing the keeper's own within-month daily r from its
committed `hourly/class_hourly_<year>.parquet` returns **0.3916 / 0.2476 / 0.2066**, reproducing
nyiso-218's committed **0.392 / 0.248 / 0.207** to **±0.0004**. The statistic is the same statistic.

**PH-1 — the model has the right driver and responds about twice too hard.**

| year | **model** r with load | **actual** r with load | model within-month daily sd | actual sd | **sd ratio** |
|---|---:|---:|---:|---:|---:|
| 2023 | **0.647** | 0.467 | 9.206 GWh | 4.955 GWh | **1.858×** |
| 2024 | **0.686** | 0.204 | 8.123 GWh | 4.185 GWh | **1.941×** |
| 2025 | **0.616** | 0.410 | 11.580 GWh | 5.154 GWh | **2.247×** |

The keeper tracks daily load at r 0.62–0.69 where the real fleet tracks it at 0.20–0.47, and swings
**1.86–2.25×** as hard. Combined with §4 — where load (0.308) beats flow (0.243) as a predictor of
the **actual** — the coherent reading is that **the real NYISO hydro fleet is genuinely dispatching
to system conditions, and the model is dispatching to the same conditions roughly twice too
aggressively.** That is a *damping* defect, not a *missing-driver* defect. It also explains
nyiso-218's two overturned readings in one stroke: the model runs flat out at its ceiling on
32–49 % of its annual energy and holds back otherwise **because nothing bounds how much water it may
move between the days of a month**, and the price correlation is strongest at the day grain because
that is where the unbounded freedom lives.

**PH-2 — the ceiling on any driver-based approach.** An OLS on **both** admissible drivers together
(load + measured flow) reaches multiple r of **0.277 / 0.299 / 0.439 / 0.409 / 0.518 / 0.341 /
0.530** across 2019–2025, mean **0.402**. So *everything measurable, combined, perfectly weighted,
with hindsight* explains ~0.40 of the actual's within-month day-to-day allocation. The keeper
already sits at **0.207–0.392** on the same statistic. **The headroom a driver-based mechanism could
possibly buy is a few hundredths of r, and in 2023 it is negative.**

**PH-3 — the amplitude a limit would be stated in**, measured rather than assumed: the actual's
within-month daily energy deviates from its month mean by sd **5.7–8.0 %**, p95 |dev| **11.1–15.6 %**,
max **20.3–32.3 %**.

**P3d, confirmed and load-bearing.** In **2023** the best admissible driver (D-B, 0.301) scores
**below** the keeper's own 0.392, and in **2022** (0.223 vs 0.358) likewise. **Arming a pure
inflow-driver mechanism would make this statistic WORSE in two of the four years it can be scored
on.** Under rule 14 `[R-ACCURATE]` that would not by itself be a reason to reject an accurate input
— a more faithful input that scores lower stays, and the worse number becomes a root-cause question.
It *is*, however, a reason not to build one whose own arithmetic says it cannot carry the signal.

## 6. The answer to the data question, with rule 13 applied in writing

Rule 13 `[R-MEASURED]`'s test — ***"could this same quantity be produced for a forward year from
forward drivers, and would it respond to changed conditions?"*** — applied to each candidate:

* **D-B, measured basin discharge — ADMISSIBLE, and insufficient.** *Could it be produced forward?*
  For a **hindcast** year, yes, trivially (100 % coverage, approved, public domain). For a genuine
  **forecast** year, **no** — 2035's Niagara discharge is not measurable in 2026, so a forecast run
  would fall back to a climatology, and §4 measures that climatology at **r = 0.031**. The
  construction that regenerates forward is therefore **not the construction that carries the
  signal**, which is precisely the failure mode rule 13 exists to catch. *Would it respond to
  changed conditions?* Yes in a wet/dry year at the **monthly** level — but the monthly level is
  already carried by the hydro budget, and at the **daily** level within a month there is nothing
  to respond with for 71.4 % of the fleet. **Verdict: a legitimate measured input that does not
  answer this question.**
* **D-A, multi-year climatological daily shape — ADMISSIBLE and PROVABLY EMPTY.** It regenerates
  forward by construction and is the only form D-B could take in a forecast year. It carries
  **mean r 0.031, max |r| 0.074** — statistically indistinguishable from noise. **This option,
  which nyiso-218 floated as "potentially admissible", is now CLOSED on measurement.** No future
  session should spend LP on it.
* **D-X, a daily shape pinned to the year's own measured `NG: WAT` — FORBIDDEN and not built.** It
  is an outcome pin: the dispatch being validated would not be the dispatch being forecast. It
  reaches r = 1.000 by construction, **which is exactly why it must not be used**, and it is named
  here only as the scale anchor and the tripwire.

**Boundary discipline held (nyiso-214, nyiso-218).** `NG: WAT` is an **ISO aggregate**; there is no
per-plant hourly hydro series. **This session invented none.** The census assigns **basins** from a
published EIA field, every driver enters as a **fleet-aggregate** series, and no plant-grain claim
is made about Robert Moses Niagara beyond its published nameplate share and its published water
source.

**Rule 14 `[R-ACCURATE]`, stated in the PREREG and restated here:** hydro is ~20 % of NYISO
generation, so re-timing it **will** move C3a/C3b/C3c. If a more accurate hydro shape makes the
price fit worse, **the accurate shape stays** and the worse fit is a discovered root-cause question
(rule 1 `[R-STRUCT]`, first half, untouched).

## 7. The successor object, handed to the owner — NOT built, NOT proposed for arming

**The object is not a missing driver. It is a missing bound.** Three measurements converge:

1. the model's within-month daily energy swings **1.86–2.25×** the actual's (nyiso-218, reproduced);
2. the model tracks daily load at **r 0.62–0.69** where the actual tracks it at **0.20–0.47** (PH-1);
3. no admissible daily driver — flow, climatology, or both with load and hindsight — exceeds
   **r ≈ 0.40** against the actual, and flow alone is **below** the keeper's own score in 2 of 4
   scoreable years (§4, PH-2).

Inside a monthly budget, with a day-invariant ceiling above and a month-constant floor below,
**nothing bounds how much water the LP may move between the days of a month.** The real fleet is
bounded — by forebay and reservoir storage, by the Niagara Treaty's scenic-flow schedule, and by the
IJC Plan-2014 regulation of Lake Ontario outflow — and those bounds are **external, published,
physical, and regenerate for a forward year without knowing that year's weather.** Whether that
family of constraint can be expressed at fleet-aggregate grain, on what evidence, and at what cost
in free parameters, is a question for the owner and not a mechanism this session proposes.
**Deliverable (b), `DECISION-CARD-nyiso219`, puts it and its alternatives to the owner in §7 of this
lane's record.**

**What is now CLOSED and should not be re-spent:**

* the **daily inflow driver** as a route to this residual — the data is excellent and the signal is
  not there for 71.4 % of the fleet (§4, §4a);
* the **multi-year climatological daily shape** — measured at r 0.031 (§4);
* **`hydro_ror_split`** (G) and **`hydro_budget_nameplate_aware`** (I) remain adjudicated and were
  not re-tested.

## 8. Predictions scored, in one place — 3 confirmed, 2 split, 2 missed as written

| id | verdict |
|---|---|
| P1b, P1c, P1d | **CONFIRMED** (18 sources for 95 %; largest non-GL 5.50 %; 100 % resolved) |
| P2a | **CONFIRMED** (100.0 % coverage, 100 % approved) |
| P2b, P2c | **SPLIT** — confirmed on the within-month construction, **missed** on the whole-period one; the PREREG's threshold was too tight and its gap was named in advance |
| P2d | **CONFIRMED on both constructions** |
| P3a | **CONFIRMED** — climatology is empty (mean 0.031) |
| P3b | **PARTIAL MISS** — hit 5/7, missed low 2/7; **the falsification branch did not fire under any of five constructions** |
| P3c | **MISS as written** — the ≥ 0.25 threshold holds in 5/7, not 7/7; direction positive in all seven |
| P3d | **CONFIRMED** — the best admissible driver scores below the keeper in 2 of 4 scoreable years |

**No gate was restated after its number was seen.** P2b/P2c/P3b/P3c are reported in the words they
were written in, with the misses named and their magnitudes given.

**No eighth owner card is opened by this section** — §7's decision card is deliverable (b) of this
session's own charter, not a new pending ruling. The seven pending rulings (nyiso-206, -207, -203,
DECISION-CARD-nyiso193 §5/5.1, -208, -214 §6, -215 §6) are untouched.
