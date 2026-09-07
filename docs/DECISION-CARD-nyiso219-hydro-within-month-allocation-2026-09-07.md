# DECISION CARD — nyiso-219: the hydro daily-driver question is **answered and two of its three routes are closed**. The residual is a missing **bound**, not a missing **driver**. What, if anything, should be built?

**For:** the owner. **From:** session nyiso-219, NYISO `backcast-calibration` lane, 2026-09-07.
**ZERO LP. Nothing armed, nothing screened, nothing solved, nothing registered, no
`src/market_sim/` change, no scorer change, no marker touched, no matrix cell letter changed, no
held-out year spent.**

**Evidence:** `docs/FINDING-nyiso219-hydro-daily-driver-data-question-2026-09-07.md`; machine
records `results/calibration/_nyiso219_hydro_daily_driver_census.json`,
`_nyiso219_posthoc_overresponse.json`, cached source data `_nyiso219_usgs_daily_discharge.csv.gz`;
pre-registration `results/calibration/PREREG-nyiso219-hydro-daily-driver-data-question.md`,
**committed and pushed before any number was read**.
**Keeper, unchanged:** `2026-09-07-nyiso-213-summer-seam` — **CALIBRATED, grade 7/8, zero failing
criteria** across 2023–2025, C3c the lone ledgered caveat.

> **Read this first.** **Nothing on this card is urgent.** NYISO has **no in-sample rubric
> failures**, and the object here **is not a rubric criterion at all** — no hydro row in `fuelRows`,
> no hydro record in any C-criterion. This session was chartered to answer an open **data** question
> and it did: the data exists and is excellent, and it **cannot** close the residual. Two of the
> three candidate routes are now **closed on measurement**, which is the deliverable. The lane's
> reading on what remains is **Option A**, and no option on this card should be started without
> your instruction.

---

## 1. What was asked, and what came back

nyiso-218 §8 localized NYISO's hydro shape residual **completely** — month energy r ≈ 1.000,
hour-of-day r ≈ 0.98, but **within-month day-to-day energy r 0.207–0.392** — and handed over an open
data question rather than a mechanism: *does a forward-drivable, condition-responsive daily
inflow/flow driver exist for NYISO's basins at usable quality?*

**Answer: yes, and it does not help.**

| | measured |
|---|---|
| fleet resolved to a **published** EIA-860 `Name of Water Source` | **163 of 163 plants, 100.00 % of 4,681.0 MW, 0 unmatched** |
| USGS daily-discharge coverage on every material basin, 2019–2025 | **100.0 %**, **100 % USGS-approved**, **public domain**, forward-available |
| **Great-Lakes outflow share of fleet MW** | **71.38 % in two plants** (Niagara 51.89 %, St Lawrence 19.48 %) |
| **within-month daily r** of measured basin discharge vs actual `NG: WAT` | **0.243 mean** (0.095–0.327) — **below** the keeper's own 0.392 in 2023 and 0.358 in 2022 |
| **within-month daily r** of a multi-year climatological daily shape | **0.031 mean**, max \|r\| **0.074** — indistinguishable from noise |
| Niagara's own mean r, on **51.9 % of fleet MW** | **0.079** |
| the best single flow predictor — a **3.95 %**-of-MW Adirondack cascade | **0.265** |

**Why**, in one line: the Niagara is Lake Erie's outflow and the St Lawrence is Lake Ontario's, each
buffered by an inland sea and each governed by a published regulation plan rather than by last
week's rain. Their **within-month daily flow CV is 4.01 % and 3.11 %** against a runoff river's
**56.48 %**. **There is no daily inflow signal to give the model for 71.4 % of its hydro fleet** —
not because the measurement is missing, but because the physical quantity is nearly constant.

## 2. What the measurement found that it did not predict

Reported **post-hoc**, moving no gate, model output read for **2023–2025 only**:

| year | **model** r with daily load | **actual** r with daily load | **model / actual** within-month daily sd |
|---|---:|---:|---:|
| 2023 | **0.647** | 0.467 | **1.858×** |
| 2024 | **0.686** | 0.204 | **1.941×** |
| 2025 | **0.616** | 0.410 | **2.247×** |

And across 2019–2025 the **actual** fleet tracks **daily load** (mean r **0.308**) *better than it
tracks measured **flow*** (0.243).

**The model is not missing a driver. It has the right driver and responds to it about twice too
hard.** The real fleet genuinely dispatches to system conditions; the LP dispatches to the same
conditions roughly twice as aggressively, because inside a monthly budget — with a day-invariant
ceiling above and a month-constant floor below — **nothing bounds how much water it may move between
the days of a month.** That single fact also explains nyiso-218's two overturned readings at once:
the run flat out at the ceiling on 32–49 % of annual energy, and the day-grain price correlation.

**The ceiling on any driver-based approach, measured:** an OLS on **both** admissible drivers
together (load + measured flow), fitted with hindsight, reaches mean multiple r **0.402**. The
keeper already sits at **0.207–0.392** on the same statistic. **The headroom a driver-based
mechanism could buy is a few hundredths of r, and in 2023 it is negative.**

## 3. Rule 13 `[R-MEASURED]`, applied in writing

* **Measured basin discharge — ADMISSIBLE, INSUFFICIENT.** In a *hindcast* it regenerates trivially.
  In a genuine *forecast* year it cannot — 2035's Niagara discharge is not measurable in 2026 — so a
  forecast run falls back to the climatology, **which measures 0.031**. The construction that
  regenerates forward is **not** the construction that carries the signal: exactly the failure mode
  rule 13 exists to catch.
* **Multi-year climatological daily shape — ADMISSIBLE and PROVABLY EMPTY.** Closed on measurement.
* **A daily shape pinned to the year's own measured `NG: WAT` — FORBIDDEN, and not built.** It is an
  outcome pin reaching r = 1.000 by construction, which is precisely why it must not be used. It is
  named in the finding only as the scale anchor and the tripwire.

**Boundary discipline held** (nyiso-214, nyiso-218): `NG: WAT` is an ISO aggregate, there is no
per-plant hourly hydro series, and **this session invented none** — the census assigns **basins**
from a published EIA field and every driver enters as a fleet-aggregate series.

## 4. The question for you

**The residual is a missing BOUND on day-to-day water transfer, not a missing driver.** The real
fleet's bounds are external and published — usable forebay and reservoir storage, the 1950 Niagara
Treaty's scenic-flow schedule, and the IJC Plan-2014 regulation of Lake Ontario outflow — and unlike
a year's streamflow, **those regenerate for a forward year without knowing that year's weather.**
That is what makes the family *potentially* admissible where the inflow driver is not.

**It is also where the rule-13 trap re-appears in a new dress, and the lane names that in advance
rather than discovering it later:** the *convenient* way to parameterize such a bound is at the
actual's own measured within-month daily standard deviation (**5.7–8.0 % of the daily mean**;
p95 |dev| 11.1–15.6 %, max 20.3–32.3 %). **That would be an outcome-derived number and is
forbidden.** An admissible bound would have to come from **published usable-storage volumes and
licence flow schedules**, converted to shiftable MWh — and **whether that data exists at usable
quality for NYPA's Niagara/St-Lawrence forebays and the Brookfield cascades is an OPEN DATA QUESTION
this session did not answer and does not assert.** Answering it is zero-LP and would be the first
step of any Option B.

## 5. Options

**Option A — CLOSE the object. Record the characterization, build nothing.** *(The lane's reading.)*
The keeper is CALIBRATED with zero failing criteria; hydro is not a rubric criterion; two of the
three candidate routes are closed on measurement; and the measured ceiling on the third-party
drivers (0.402 with hindsight, against a keeper already at 0.207–0.392) says the available headroom
is a few hundredths of r. **Cost:** the residual stays, characterized and documented, and the
NYISO hydro shape remains ~2× too swingy day to day. **Benefit:** no LP spent, no free parameter
added, and the two dead routes are permanently marked so no future session re-spends on them.

**Option B — commission the storage-bound DATA question (zero LP).** A follow-on session
establishes, with no solve, whether published usable-storage volumes and licence flow schedules
exist for the material projects (FERC licence documents, NYPA filings, USACE/IJC publications), at
what coverage and licence, and whether they convert to a fleet-aggregate shiftable-MWh bound without
touching a measured outcome. **This is the same shape of deliverable as this session and costs the
same: nothing but a session.** It ends in a second decision card, not a mechanism. **Risk:** the
data may not exist at fleet-aggregate grain, in which case Option B terminates in a clean negative
and Option A stands.

**Option C — route it to the LP formulation instead of to an input.** The standard hydro
representation damps this endogenously: an opportunity-cost **water value** on stored energy rather
than a hard monthly budget with free intra-month reallocation. That is a **model-structure** change
on the shared ISO-agnostic LP, not a NYISO input, so it reaches every ISO and needs its own charter,
its own cross-ISO screen (rule 29 `[R-SCREEN]`) and its own matrix row. **The lane does not
recommend opening it off the back of one ISO's hydro residual**, and names it only so the option is
on the record.

**Option D — re-scope: decide the object is not worth work.** Explicitly rule that a non-gated,
non-criterion structural residual on a CALIBRATED ISO is below the line, and retire it from the
lever queue. This differs from Option A only in that it forecloses Option B as well.

## 6. What is CLOSED regardless of which option you pick

* **The daily inflow driver** as a route to this residual — the data is excellent and the signal is
  not there for 71.4 % of the fleet.
* **The multi-year climatological daily shape** — measured at r 0.031.
* `hydro_ror_split` (**G**, nyiso-111) and `hydro_budget_nameplate_aware` (**I**, nyiso-107) remain
  adjudicated and were **not** re-tested.

## 7. Discipline record

**Eight predictions were pre-registered with sign, magnitude and exhaustive partitions; three were
confirmed, two split, two missed as written, and one — the confirmed one that matters — said in
advance that an accurate driver might score WORSE than the model does now and would stay anyway.**
The falsification branch P3b (D-B ≥ 0.55 ⇒ *"my reading is wrong, build the inflow driver"*) **did
not fire under any of five independent D-B constructions**, the highest value in any year being
0.327. P2b/P2c's absolute 5 % threshold was **too tight** and is reported as a miss on one of two
constructions the PREREG had left un-pinned and had **named as a gap in advance**; P3c's ≥ 0.25
threshold holds in 5 of 7 years, not 7 of 7. **No gate was restated after its number was seen.**

**Instrument self-check:** reconstructing the keeper's own within-month daily r from its committed
hourlies returns **0.3916 / 0.2476 / 0.2066** against nyiso-218's committed **0.392 / 0.248 /
0.207** — ±0.0004. Both probes are deterministic: re-running each reproduces its JSON
byte-identically.

**No eighth pending owner ruling is opened by this card** — it *is* this session's chartered
deliverable (b). The seven pending rulings (nyiso-206 `floor_pct` basis; nyiso-207
identification-vs-application; nyiso-203 §6; DECISION-CARD-nyiso193 §5/5.1 unit-grain; nyiso-208
out-of-training CAMPD read; nyiso-214 §6 duct membership; nyiso-215 §6 duty-role level basis) are
untouched.
