# FINDING nyiso-220 — the instrument question is SETTLED, and the answer is **not FERC**. St. Lawrence's budget period is **one week, in words**; Niagara's governing instruments state **no period at all**

**Session:** nyiso-220, NYISO `backcast-calibration` lane. **Branch:**
`claude/nyiso-hydro-operating-ranges-4jfj0b`, on `main` at `7486cb9b`. **Date:** 2026-09-08.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **untouched.**
**ZERO LP.** Nothing armed, screened, solved or registered; no `ScenarioConfig` field; no
`src/market_sim/` change; no marker moved; no matrix cell letter changed; **no held-out year spent.**
**PRECOMMIT:** `results/calibration/PRECOMMIT-nyiso220-hydro-operating-ranges.md`, committed and
pushed **before any substantive document was read**.
**Instrument (committed, deterministic — re-running reproduces its JSON byte-identically):**
`scripts/probes/nyiso220_hydro_instrument_index.py` →
`results/calibration/_nyiso220_hydro_instrument_index.json`.

---

## 0. The result in one paragraph

nyiso-219 flagged, and deliberately asserted nothing about, the question of **which instrument
actually binds the water** at NYISO's two dominant hydro projects — warning that a FERC pull could
return the wrong document for 71 % of the fleet. **It would have.** For **both** projects and for
**both** quantities — water entitlement *and* operating band — the governing instrument is
**international, not the FERC licence**: Niagara under the **1950 Niagara Diversion Treaty** plus the
**International Niagara Board of Control's 1993 Directive** (revised 2017) over the Chippawa-Grass
Island Pool; the St. Lawrence under the **IJC's 2016 Supplementary Order of Approval** with
**Regulation Plan 2014**, and, for within-week variation, the Commission's **directive on peaking and
ponding**. That last document does something no volume conversion could: **it states the conservation
periods in words.** The ILOSLRB's own glossary defines *ponding* as **"variation in the day-to-day
flows over the course of a week"** and its reports state that ponding preserves **"the total weekly
flow"** while peaking preserves **"the total daily flow"**. So for Robert Moses St. Lawrence
(19.48 % of fleet MW) the authorised budget period is **one week — 168 h — identified from a
published categorical duration class with zero fitted scalars** (rule 21 `[R-DOF]` case 2). For
Robert Moses Niagara (51.89 %) the answer is a **structural negative that is stronger than a
retrieval failure**: neither governing instrument states any energy or volume conservation period at
all — verified mechanically against the full treaty text, which contains **zero** occurrences of
*elevation, reservoir, storage, pondage, forebay, pool, monthly, weekly, accounting* or *average*.
**Neither project's governing instrument contains anything resembling the LP's monthly budget
period.**

## 1. Access — re-measured here, and one FERC negative made more precise

Per the handoff, all four routes were re-tested at this container before anything was planned around
them, plus four the handoff did not name.

| route | outcome here |
|---|---|
| `www.ferc.gov`, `cms.ferc.gov` | **403** with a browser `User-Agent` — reproduces nyiso-219 |
| `elibrary.ferc.gov` shell | **200, 22,464 bytes** — reproduces nyiso-219's measured shell size exactly |
| `eLibrary/api/search`, `/api/v1/search` | **200 / 22,464** — the SPA catch-all. Confirmed, not re-discovered |
| pre-pinned Chromium | **untested here** — the `playwright` Python package is absent and `playwright install` is forbidden. Reported as untested, **not** as failed |
| **`WebFetch` on `www.ferc.gov`** *(a route nyiso-219 did not have)* | **403** — does not bypass FERC's edge |
| egress control (`example.com`) | **200** — the 403 is FERC's own edge, not our network |
| `ijc.org`, `nypa.gov`, `govinfo.gov`, `loc.gov`, `glerl.noaa.gov` | **200** |

**The more precise FERC negative.** nyiso-219 concluded eLibrary has "no public API". Nearly right,
and worth sharpening so nobody re-spends: the SPA's own config at
`elibrary.ferc.gov/eLibrary/assets/config/app-settings.json` (HTTP 200) declares
`"apiUrl": "/eLibraryWebAPI/api/"` — **a real ASP.NET Web API** returning genuine JSON error bodies
rather than the SPA catch-all, and the compiled chunks name its endpoints and full request payloads
(`Search/GeneralSearch`, `Search/AdvancedSearch`, `Docket`, `Document`, `File`,
`DocFamily/GetDocFamily`). **But the search controllers are not deployed there:** `Search`,
`Document` and `DocFamily` return **404**, while `Docket` returns the ASP.NET scaffold
`["value1","value2"]` for *any* id and `File` returns empty. **The API route is a characterized dead
end, not an unexplored one.** *(Also recorded so it is not re-chased: the `"/api/v2/"` string in the
main bundle is **Datadog RUM telemetry** (`ddforward`), not FERC's API — the same class of false
positive nyiso-219 hit.)*

FERC's bot protection was **not** attempted — an organisation/edge 403 is reported, not worked
around. Reading a public site's own published config to find its documented endpoints is ordinary
use; the 403 hosts were left alone.

**This is why the instrument question mattered so much:** `ijc.org` **is** reachable where FERC is
not, so settling the instrument decided whether the session had a corpus at all.

## 2. The instrument question — SETTLED, per quantity, per project

`_nyiso220_hydro_instrument_index.json` records this per plant. Coverage:

| instrument class | plants | MW | % fleet MW |
|---|---:|---:|---:|
| **NIAGARA** (treaty + INBC Directive) | 1 | 2,429.1 | **51.893** |
| **ST_LAWRENCE** (IJC Order + Plan 2014 + peaking/ponding directive) | 1 | 912.0 | **19.483** |
| **DOMESTIC** (FERC licence article — unreachable) | 161 | 1,339.9 | 28.624 |

### 2a. Robert Moses Niagara — P-2216 — 51.89 % of fleet MW

* **Water entitlement → the 1950 Niagara Diversion Treaty**, not FERC. Art. III defines the
  available water; **Art. IV** forbids power diversions that reduce the flow over the Falls below
  **100,000 cfs** between 08:00–22:00 EST (Apr 1 – Sep 15) and 08:00–20:00 EST (Sep 16 – Oct 31),
  and below **50,000 cfs at any other time**; Art. V makes the excess divertible; **Art. VI** divides
  it **equally** between the two countries; Art. VII creates the representatives (the International
  Niagara Committee) who "ascertain, determine and record the amounts of water available".
* **Operating band → the INBC 1993 Directive (revised 2017)**, over the **Chippawa-Grass Island
  Pool**, not FERC. It requires OPG and NYPA to operate the International Niagara Control Works to
  maintain an **operational long-term average CGIP level of 171.16 m (561.55 ft), IGLD 1985**,
  "establishes tolerances for the CGIP's level as measured at the **Material Dock gauge**", and caps
  the **maximum permissible accumulated deviation at ±0.91 meter-months** (the measured accumulated
  deviation from 1973-03-01 to 2023-08-31 was **0.13 meter-months**).
* **Conservation period → NONE, and this is verified rather than inferred.** The treaty's only
  temporal structure is a **recurring time-of-day schedule of instantaneous minimum flow rates** —
  a rate constraint, not a volumetric budget over a period. The CGIP Directive constrains a
  **level** to a long-term average with an accumulated-deviation tolerance in **meter-months**,
  i.e. a long-horizon level constraint, not an energy budget.

### 2b. Robert Moses St. Lawrence — P-2000 — 19.48 % of fleet MW

* **Outflow entitlement → the IJC Supplementary Order of Approval of 2016-12-08 with Regulation
  Plan 2014 (Bv7)**, not FERC. The Board Directive: the Board sets flows through the Moses-Saunders
  and Long Sault Dams "in accordance with the Order of Approval, **normally as specified by the
  approved weekly flow regulation plan**"; Plan 2014 is "a set of release rules (algorithms) that
  produce an unambiguous release amount **each week**". Numeric limits recovered: the **J limit**
  (max week-to-week flow change **700 m³/s**, or **1,420 m³/s** above 75.2 m without ice forming),
  the **M limit** (Seaway-season flow limited to keep the **weekly mean** level of Lake St. Lawrence
  at Long Sault Dam from falling below **72.60 m**, IGLD 1985), and the **I limit** (winter
  constraint preventing the Long Sault level falling below **71.8 m**).
* **Within-week operating band → the Commission's directive on peaking and ponding**, conditions in
  **Addendum No. 3 to the Operational Guides for Regulation Plan 1958-D** (IJC letter **1983-10-13**
  authorising OPG and NYPA; renewed **2016-11-04** for 2016-12-01…2021-11-30; renewed **2021-11-30**
  for 2021-12-01…2026-11-30 — **a window that spans every scored year of this lane**). Peaking is
  curtailed when outflows exceed the **7,930 m³/s (280,000 cfs)** threshold.
* **Conservation periods → STATED EXPLICITLY, in words, and this is the identification.** ILOSLRB
  glossary, verbatim: *"**Peaking** — variations in the hourly flows over the course of a day"*;
  *"**Ponding** — variation in the day-to-day flows over the course of a week"*. And §2.8 of the
  progress reports: peaking increases demand-hour flows *"while still keeping **the total daily
  flow** the same as though a constant flow had passed through the turbines during the 24 hours"*;
  ponding raises high-demand-day flows *"while still keeping **the total weekly flow** the same as
  though a constant flow had passed through the turbines during the seven days"*.

**So the outer conservation period — the one a hydro budget row's period length corresponds to — is
ONE WEEK (168 h), with a nested daily conservation inside it.** It is read off the instrument in
words, not converted from a volume, so it needs no stage–storage relationship and carries **zero
fitted scalars**.

### 2c. The other 161 plants — 28.62 % of fleet MW

Domestic rivers, so the operating band is in each project's **FERC licence article** — **not
retrieved**, per §1. This is 28.62 % of fleet MW across ~109 dockets and is the residual the handoff
anticipated.

## 3. Rule 13 `[R-MEASURED]` — the admissibility test, applied in writing

The test: *could this same quantity be produced for a forward year from forward drivers, and would
it respond to changed conditions?*

* **Forward-producible — YES.** The weekly conservation period is a property of a **standing
  instrument** (the IJC Order of 2016-12-08 and a peaking/ponding authorisation renewed on five-year
  cycles since 1983), not of any year's weather or outcome. A 2035 forecast year reads the same
  instrument and gets the same period. It re-derives only when its **source instrument** updates —
  rule 23 `[R-FROZEN-DERIVE]` satisfied by construction.
* **Responds to changed conditions — YES, in the right place.** The **period** is structural and does
  not vary; the **energy** inside it still comes from the existing hydro budget, which scales with
  the water year. The mechanism would therefore *remove arbitrage freedom* without pinning any
  outcome — and a shorter period is strictly a **restriction of the feasible set**, so it can only
  remove freedom, never add it.
* **Not an outcome-derived number.** It is not the actual's measured within-month daily sd (the
  forbidden number the handoff named); it is not fitted to any residual; it was **not swept**; and
  it was read from a published document rather than from any model output. Rule 21 `[R-DOF]` case 3
  is undisturbed — **this session neither chose nor swept a period length.**
* **Rule 25 `[R-ISO-SCOPE]` — clean.** NEISO's `HDP`/`HDR`/`HW` taxonomy was **not** borrowed and is
  not cited as a source. The weekly period comes from **NYISO's own project's own governing
  instrument**. NEISO remains an existence proof only.

**The Niagara half fails the *retrieval* test but passes the *admissibility* test vacuously:** there
is no quantity to admit, because the instruments state none.

## 4. Scoring the PRECOMMIT — in the words it was written in

### 4a. Thresholds

| | as written | outcome |
|---|---|---|
| **T1** — instrument settled iff, for each project, the governing instrument is named **for each of two distinct quantities separately** and a retrievable document cited | | **MET.** §2a and §2b name entitlement and operating band separately for both projects, each with a citation |
| **T2** — a **numeric operating band** retrieved with units and datum, from a citable public document, for **≥ 50 % of fleet MW** | | **MISS.** What was recovered is *level constraints*, not a band: Niagara a **long-term average target** (171.16 m) with an accumulated-deviation tolerance (±0.91 meter-months); St. Lawrence **floors** (72.60 m weekly mean, 71.8 m ice). **A floor is not a band, and a long-term-average target is not a band.** Reported as a miss |
| **T3** — period length derived iff **T2's band** converts to hours without a fitted scalar or an unpublished input | | **NOT MET AS WRITTEN** — its precondition (T2) failed, so the stated conversion route was never available. A period length was nonetheless identified for St. Lawrence **by a route T3 did not contemplate** (the instrument states the period categorically, in words). That is reported as a **separate labelled result**, not as a T3 pass |

**T2 and T3 are reported as misses rather than restated.** The categorical route is genuinely better
than the one T3 imagined — it needs no stage–storage curve — but saying so does not convert a failed
threshold into a passed one, and the PRECOMMIT forbade exactly that move.

### 4b. Predictions

| | prediction | outcome |
|---|---|---|
| **P1** | international instruments govern both quantities at both projects; FERC defers rather than restating | **CONFIRMED** (§2) |
| **P2** *(written to hurt: I put P(convertible for Niagara) < 0.5)* | the instruments give a **level** band and a **flow** regime but **not a usable volume**, needing an unpublished stage–storage relation | **MECHANISM CONFIRMED EXACTLY** — that is precisely why T2 missed, and for **Niagara the feared outcome landed in full**. The **consequence** was partly averted for St. Lawrence only because the instrument states its period in words, which I did not anticipate |
| **P3** | any derived length ≤ the NID full-volume pondage bound (St. Lawrence ≤ **73.07 h**) | **MISS.** The derived period is **168 h > 73.07 h.** Diagnosis, offered without rescuing the prediction: **P3 conflated two different objects** — a *conservation period* (how long the instrument preserves a total) with a *storage bound* (how much energy the pool can hold). They are complementary, not contradictory: the instrument sets the **period**, the pondage bounds **how much can actually move within it**. The prediction was mis-specified, and it is scored as a miss |
| **P4** *(the self-falsification test, aimed at the lane's largest number)* | Niagara's inter-day shaping is carried by **Lewiston**, a separate EIA plant the model holds as **storage**, outside plant 2693's hydro budget | **CONFIRMED on all three legs** (§5) |
| **P5** | coverage ≤ 75 % of fleet MW; **no fleet-grain** per-plant period | **CONFIRMED** — 71.376 %, two plants; 28.62 % remains on unreachable FERC articles |

### 4c. A gap in my own outcome partition — reported, not papered over

The PRECOMMIT's partition offered **O3** as *"instrument identified, band retrieved, but not
convertible to a length"*. **Niagara is not that.** There is no band of the relevant kind to
retrieve, and the instruments **affirmatively state that no conservation period exists** — a
*positive structural finding*, not a retrieval failure. My partition had no cell for
"the instrument settles the question by containing nothing", and it should have. St. Lawrence lands
cleanly in **O2**. **A gate that misses is a result**, so the gap is recorded here rather than
resolved by relabelling Niagara into O3.

## 5. P4 in full — the test that could have cost the lane its headline

The charter's central number is Robert Moses Niagara's **0.244 h** of pondage against a **730-hour**
budget period. If Lewiston's reservoir were inside plant 2693, that number would be badly
overstated. Three independent legs, all zero-LP:

1. **HILARRI**: Lewiston is **EIA plant 2692**, NID dam **NY00689**, mode **"Pumped storage"** —
   distinct from Robert Moses Niagara (2693, NID `NY16253`), though under the **same FERC docket
   P-2216**.
2. **The hydro budget excludes it on both legs.** `data/hydro.py` sets
   `HYDRO_PRIME_MOVER = "HY"` and excludes prime mover `PS` by construction ("it is a storage unit,
   not an inflow unit"); and NYISO is in **neither** `EIA930_PS_FOLDED_INTO_WAT` (`{MISO, PJM}`) nor
   `EIA930_PS_SPLIT_COMPLETE_FROM` (`{NEISO: 2025}`), so NYISO's `NG: WAT` **level** excludes pumped
   storage too.
3. **The model carries it, separately and in the right zone**:
   `Upstate_West_eia860_pumped_storage`, **220 MW / 2,200 MWh** — a **10.0 h** duration object in
   Niagara's own zone.

**P4 = TRUE, and it strengthens the charter's premise rather than weakening it.** The model already
represents Niagara's genuine inter-day shaping as a 10-hour storage unit; what the hydro budget row
governs is the **inflow plant alone**, whose forebay holds **0.244 h** — and the LP grants it a
**730-hour** arbitrage window. The **41× separation** between the two objects is the model's own
independent corroboration, which is the §7 cross-check discipline the PRECOMMIT required.

*(Lewiston's dam `NY00689` is correctly **absent** from `data/raw/nid/` — that intake scoped
conventional-hydro dams. Consistent, not a gap.)*

## 6. Traps caught — the pre-declared §7 guard, and one new instance of nyiso-219's class

**A near-miss worth recording, because it would have produced a confidently wrong number.** A search
for the peaking-and-ponding directive returned `ijc.org/en/**lsbc**/who/directives/peaking` — which
is the **Lake Superior** Board of Control's directive for the **St. Marys River**, not the
St. Lawrence. Two different IJC boards each have a "peaking and ponding" directive. It was caught
only because the fetch was asked for **verbatim** provisions and reported that the document never
mentions Moses-Saunders. **This is nyiso-219's trap class in a new register** — an external
authority keyed at a different scope than the one being asked about — and it was caught the same way
all three of theirs were: by cross-checking against an independently known fact, not by re-reading.

**Cross-checks performed before publishing figures**, per the pre-declared guard:

* the boundary-water share **71.376 %** recomputed from the committed index and reconciled against
  nyiso-219's independently derived cumulative **71.38 %** — agree;
* NID surface area for `NY00678` (**37,500 acres ≈ 151.8 km²**) checked against the commonly
  published Lake St. Lawrence area of ~150 km² — agree;
* the treaty's silence checked **mechanically** (a term-frequency scan over the full text) rather
  than from a summary — the summary and the scan agree;
* the probe re-run and confirmed **byte-identical**.

**A precision note against my own convenience:** the treaty scan returns 0 for the literal token
`daily`, but Art. IV does say *"each day between the hours of…"*. The defensible claim is therefore
the narrower one made in §2a — **no volumetric accounting period; a recurring time-of-day schedule
of instantaneous rate limits** — and not "the treaty says nothing daily".

## 7. Q2 — still blocked, but the blocker is now NARROWED to one project

The owner's **Q2** ruling puts the rule-19 `[R-ONE-MECH]` replace-vs-reconcile choice at **phase 0**,
on the overlap arithmetic between a shortened period and `hydro_dispatch_envelope` (armed in the
keeper, binding **27–42 %** of hours carrying **32–49 %** of annual hydro energy). That arithmetic
needs a period length **for the plants that dominate the binding**, and:

* **St. Lawrence now has one** — 168 h, published, zero scalars — but it is **19.48 %** of fleet MW;
* **Niagara, at 51.89 %, has none**, and §2a establishes that **none exists in its governing
  instruments**.

**So the Q2 arithmetic is not attempted here.** Running it on 19.48 % of fleet MW while the dominant
plant has no period would produce a number that looks like an answer and is not one. **The blocker
has moved**, though, and that is the useful part of this result: it is no longer "FERC is
unreachable" (a corpus problem for 71 % of the fleet) but the far narrower **"what is the right
budget-period representation for a plant whose instruments impose no conservation period at all?"**
— a *modelling* question for the owner, not a retrieval question, and one the §8 observation bears
on directly.

## 8. What this changes, and what it does not

**Does not change:** the pondage conclusion, which never depended on any of this — 72.01 % of scored
fleet MW cannot hold one day of its own full output, and Niagara holds 0.244 h. Nothing about the
keeper, any determination, any marker, or any matrix cell. **No mechanism was tested, so
rule 28 `[R-MECH-MATRIX]` duty (b) is not engaged** and no cell letter moves.

**Does change:** the charter's premise is now supported from a **third independent direction** —
after dispatch (nyiso-218/219) and hydrology (nyiso-219's pondage bound), now **from the governing
instruments themselves**. Stated plainly: **neither dominant project's governing instrument contains
anything resembling a monthly budget period.** One states a **weekly** conservation explicitly; the
other states **no** conservation period and holds its pool to a long-term average level. The LP's
730-hour month is not a simplification of either.

**An observation the owner may want, offered as an observation and not a proposal:** for Niagara the
faithful representation implied by §2a is not merely a *shorter* period but **essentially no
inter-day budget freedom at all** — a flow-following plant whose genuine shaping the model already
carries separately as 2,200 MWh of pumped storage. That is a materially different object from
"shorten the period", it applies to **51.89 %** of fleet MW, and **this session does not propose,
design or cost it.** Rule 14 `[R-ACCURATE]` is restated before anyone acts on it: hydro is ~20 % of
NYISO generation, so re-timing it **will** move C3a/C3b/C3c, and **if the faithful representation
makes the price fit worse it stays**, with the worse fit a discovered root-cause question — the
2026-07-25 precedent (C3a-2023 +18.3 → +22.2 %, recorded as mechanism confirmed) is the standard.

## 9. Deliverable status, against the handoff's own terms

The handoff asked for **(a)** the licensed operating ranges with the instrument question settled, or
**(b)** a measured, cited negative. **The outcome is a genuine split, and it is reported as one:**

* **The instrument question — the thing nyiso-219 could not settle and explicitly left open — is
  SETTLED for 100 % of the fleet**, with citations, and the answer overturns the corpus a FERC pull
  would have targeted for 71.38 % of fleet MW.
* **(a) for St. Lawrence, 19.48 % of fleet MW:** a period length of **168 h**, from a published
  categorical duration class, zero fitted scalars, rule 13 test applied in writing (§3).
* **(b) for Niagara, 51.89 %:** a **cited structural negative** — no conservation period exists in
  either governing instrument, verified mechanically — which forecloses the question rather than
  leaving it open, so no future session need re-spend on it.
* **(b) for the remaining 28.62 %:** FERC licence articles, **not retrievable from this container**,
  with every route tried and its outcome recorded (§1).

**A clean negative is a success**, and two-thirds of this result is negative. What it buys is that
**no future session should pull FERC for Niagara or the St. Lawrence** — the documents that govern
them are the treaty, the INBC Directive, the IJC Order, Plan 2014 and the peaking-and-ponding
directive, all of them reachable, all of them now cited.

**No eighth owner card is opened.** The seven pending rulings (nyiso-206, -207, -203,
DECISION-CARD-nyiso193 §5/5.1, -208, -214 §6, -215 §6) are untouched.
