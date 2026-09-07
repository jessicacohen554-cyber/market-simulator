# FINDING nyiso-218 §8 — NYISO's hydro shape residual is **NOT** a diurnal-shape defect. It is a **within-month, day-to-day allocation** defect, and the model **over-swings** the river by ~2×

**Session:** nyiso-218, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-hr6c08`, on `main` at `bfbb0b6a`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **unchanged; nothing armed, screened or registered
by this section, no marker moved, no mechanism proposed for arming.**
**ZERO LP.** Every input is a committed artifact.
**Instruments:** `scripts/probes/nyiso218_hydro_shape_decomposition.py` (committed) plus two
census scripts whose full records are committed as
`results/calibration/_nyiso218_hydro_envelope_census.json` and
`_nyiso218_hydro_ceiling_mechanism.json`.

**The handoff names `scripts/probes/nyiso92_hourly_r_decomposition.py` as "THE instrument" for this
object. It does not exist at this HEAD** — pruned under the delete-not-archive discipline. The
decomposition here is its replacement, written from the construction nyiso-92's finding describes.

---

## 0. The result in one paragraph

The keeper reproduces hydro **volume** almost exactly (−2.18 / −0.82 / −0.15 / −0.19 % in
2022–2025) while hourly **r** sits at 0.694 / 0.677 / 0.757 / 0.723. Decomposing that residual into
four layers localizes it completely, and **not where the handoff's framing expected**: the
**hour-of-day profile is essentially exact** (r **0.975–0.989**) and the **monthly energy is
essentially exact** (r **0.898–1.000**), while **within-month, day-to-day energy allocation is
nearly uncorrelated with reality** (r **0.207 / 0.248 / 0.358 / 0.392**). Both dimensions a
mechanism constrains are matched; **all of the error lives in the one dimension no armed mechanism
touches.** Two further measurements say what is happening there, and **both overturned a reading I
had already written down**: the model sits **at** its own month × hour-of-day deliverability ceiling
in **27–42 %** of hours and delivers **32–49 % of its annual hydro energy** on that ceiling (my
annual-max proxy had said ~0.05 % and I reported the wrong conclusion from it); and the model's
within-month daily energy **varies 1.86–2.25× MORE than the actual's**, not less as I had
hypothesized. With `day-residual ~ day-price` **r = +0.33…+0.46**, the coherent reading is that the
LP is **arbitraging water across days inside a monthly budget nothing else constrains** — running
flat out at the cap on a third to a half of its energy and holding back otherwise — while the river
delivers on flow.

**Nothing here is a mechanism proposal.** It is an identification, handed to the owner as §5.

---

## 1. The measurement, and its basis

Model = keeper `hourly/class_hourly_<yr>.parquet`, P1, `klass == 'hydro'` (2022 from the stamped
touchpoint bundle `nyiso213_tp2022`). Actual = `load_eia_hourly_benchmark('NYISO', yr)['hydro']`,
i.e. EIA-930 `NG: WAT`.

**Basis verified by execution, not assumed.** NYISO is in **neither** `EIA930_PS_FOLDED_INTO_WAT`
(MISO, PJM) **nor** `EIA930_PS_SPLIT_COMPLETE_FROM` (NEISO: 2025), so `eia930_wat_level_folded`
is False in every year: `NG: WAT` is conventional-hydro only, and Blenheim-Gilboa pumped storage is
booked under the model's `storage` klass, not `hydro`. **Conventional-only on both sides.**

**This is not a rubric criterion.** There is no hydro row in `fuelRows`, no hydro record in any
C-criterion, and no gate anywhere reads it. It is a structural object.

## 2. The four-layer decomposition — the defect is localized

| year | hourly r | **month energy r** | **within-month day energy r** | day energy r | **hour-of-day profile r** | within-day residual r | volume err |
|---|---|---|---|---|---|---|---|
| 2022 | 0.694 | 0.949 | **0.358** | 0.561 | 0.988 | 0.785 | −2.18 % |
| 2023 | 0.677 | 0.898 | **0.392** | 0.514 | 0.975 | 0.760 | −0.82 % |
| 2024 | 0.757 | 1.000 | **0.248** | 0.666 | 0.987 | 0.804 | −0.14 % |
| 2025 | 0.723 | 0.998 | **0.207** | 0.460 | 0.989 | 0.723* | −0.19 % |

\* 0.841 as measured; the table's within-day column is the model-minus-day-mean correlation.

**Read the two "good" columns honestly — they are largely NOT skill.** The month-energy r ≈ 1.000
is the hydro **budget** mechanism doing its job: monthly energy is pinned to the measured monthly
total, so it is closer to an *input* than an output (2023's 0.898 is one outlier month, May, 65.06
vs 72.05 GWh). Likewise the hour-of-day r ≈ 0.98 is largely `hydro_dispatch_envelope` (a month ×
hour-of-day percentile ceiling) and `hydro_min_flow_floor` (month-constant) doing theirs. Quoting
either as evidence the model "gets hydro right" would be misleading, and that is precisely why the
third column matters: **the armed mechanisms constrain the month level and the diurnal shape, and
the residual has retreated into the dimension between them.**

## 3. What is happening in that dimension — two measurements, both of which corrected me

**(a) The envelope binds far more than I first reported.** My first pass used a cheap proxy — the
share of hours within 0.5 % of the model's *annual* max — and read **~0.05 %**, from which I wrote
that the model is interior in ~97 % of hours and therefore that price-shaping, not the envelope,
must be the driver. **That was wrong, and the proper census overturned it.** Against each hour's
own month × hour-of-day ceiling (`measured_hydro_hourly_envelope`, the mechanism's own producer):

| year | hours AT the ceiling | share | interior (< 99 % of ceiling) | model/ceiling p50 | share of ANNUAL ENERGY on the ceiling |
|---|---:|---:|---:|---:|---:|
| 2022 | 2,359 | 26.9 % | 72.4 % | 0.859 | **32.4 %** |
| 2023 | 2,842 | 32.4 % | 66.4 % | 0.899 | **38.1 %** |
| 2024 | 3,692 | 42.2 % | 57.0 % | 0.926 | **49.4 %** |
| 2025 | 3,646 | 41.6 % | 57.7 % | 0.940 | **48.4 %** |

The annual-max proxy understates binding by construction (a month × hour bucket's p95 ceiling sits
well below the annual max), and it understated it by nearly three orders of magnitude. **The
proxy's conclusion is withdrawn; the census's stands.** The envelope is a *heavily* binding
constraint, and roughly a third to a half of the model's hydro energy is delivered against it.

**(b) The model OVER-swings day to day — the opposite of my hypothesis.** Having found the ceiling
binding, I predicted that because the ceiling is *day-invariant within a month* it would
**suppress** the model's day-to-day variation, mechanically producing the low within-month r. The
first half is confirmed exactly — the ceiling's within-month daily coefficient of variation is
**0.00000** in all four years, as its month × hour-of-day construction requires. **The second half
is falsified.** The model's within-month daily energy standard deviation is **larger** than the
actual's in every year:

| year | model sd (GWh/day) | actual sd (GWh/day) | **model / actual** |
|---|---:|---:|---:|
| 2022 | 10.72 | 5.71 | **1.879×** |
| 2023 | 9.21 | 4.96 | **1.858×** |
| 2024 | 8.12 | 4.19 | **1.941×** |
| 2025 | 11.58 | 5.15 | **2.247×** |

So the model does not under-vary; **it swings roughly twice as hard as the river, in a pattern
uncorrelated with the river's** (r 0.21–0.39). Reported as a falsified hypothesis rather than
restated.

**(c) The price signature is strongest at exactly the grain where the defect lives.** The
model-minus-actual hydro residual correlates with the load-weighted system price at **r = +0.164 /
+0.219 / +0.212 / +0.261** hourly, but at **r = +0.371 / +0.462 / +0.326 / +0.377** on *daily*
totals against *daily* mean price — roughly double, and at the day grain, which is where the
residual is.

**The coherent reading**, stated as a reading and not as a proven mechanism: inside a monthly
budget, with a day-invariant ceiling above and a month-constant floor below, **nothing constrains
how the LP allocates water between the days of a month**, so it allocates by price — flat out at
the cap on a third to a half of its energy, held back otherwise. That is a bang-bang arbitrage
pattern, not a river.

## 4. Why this is a good object, and what it is NOT

* **Flat across all four years** (within-month r 0.207–0.392 with no trend), so 2022's value is not
  a 2022 effect and the object is **identifiable entirely on the training tier with ZERO rule-22
  exposure**. No held-out year is needed to work it, and none is spent by it.
* **Material:** hydro is 24–27 TWh/yr, ~20 % of NYISO generation, and at r 0.68–0.76 the
  worst-tracking non-degenerate component in the fleet.
* **It is NOT "arm the hydro shape mechanism."** `hydro_dispatch_envelope`,
  `hydro_min_flow_floor` and `nyiso_hydro_reserve_eligible` are **already armed** in the keeper;
  `hydro_ror_split` is **G** (governance-refused, nyiso-111, falsified ex ante) and
  `hydro_budget_nameplate_aware` is **I** (provably inert, nyiso-107). None is re-tested here, and
  none may be without new evidence. **This section proposes no cell letter change**, and NYISO's
  matrix shard records it as an annotation only.
* **It is nyiso-92's residual, not a fresh failure.** nyiso-92's arm moved hourly r from
  0.594/0.549/0.381 to 0.741/0.778/0.552; this is what it left behind, and the decomposition says
  the arm succeeded precisely in the two dimensions it constrains.

## 5. The successor object, handed to the owner — NOT built, NOT proposed for arming

The missing constraint is a **within-month, day-to-day hydro allocation** driver. **Rule 13
`[R-MEASURED]`'s test is the whole game here and is applied in writing before anything is
proposed:** *"could this same quantity be produced for a forward year from forward drivers, and
would it respond to changed conditions?"*

* **FORBIDDEN, and named so it is not reached for:** a daily hydro shape pinned to the year's own
  measured `NG: WAT` daily totals. That is an outcome pin — the dispatch being validated would not
  be the dispatch being forecast — and it would close this residual almost exactly, which is
  precisely why it must not be used.
* **Potentially admissible, if and only if it clears the same bar the existing envelope clears:** a
  daily inflow/runoff driver that regenerates forward and responds to changed conditions — e.g. a
  multi-year climatological daily-inflow shape, or a measured streamflow series for the Niagara /
  St. Lawrence / Mohawk basins, entering as a *daily energy availability* rather than as a target.
  Whether such a series exists at usable quality for NYISO's basins is an open data question this
  session did not answer and does not assert.
* **Boundary discipline, carried from nyiso-214:** `NG: WAT` is an **ISO aggregate**. There is no
  per-plant hourly hydro series, which is why `allocate_min_flow_floor` splits the fleet floor
  pro-rata by budget rather than inventing per-plant structure. **This section invents none
  either**, and Robert Moses Niagara (~52 % of NYISO hydro MW, treaty/flow-governed) is named as
  the reason a plant-grain claim would need a basis it does not have.

**Rule 14 `[R-ACCURATE]` cuts both ways here and is stated in advance:** hydro is ~20 % of
generation, so re-timing it **will** move C3a/C3b/C3c. If a more accurate hydro shape makes the
price fit worse, **the accurate shape stays** and the worse fit is a discovered root-cause
question — not a reason to revert (rule 1 `[R-STRUCT]`, first half, untouched). nyiso-92 flagged
exactly this, and it is why this object is handed over as an identification rather than as a
tuning lever.

**No eighth owner card is opened.** The seven pending rulings are untouched. This is an
identification for whichever lane the owner routes it to.
