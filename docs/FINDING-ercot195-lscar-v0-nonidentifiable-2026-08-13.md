# FINDING — ercot-195 / L-SCAR-SCREEN-2: the L-1 rent function is NOT IDENTIFIABLE from measured tightness; the lane STOPS at V0

> Session `l-scar-screen-2`, 2026-08-13, branch
> `claude/l-scar-screen-2-implement-lo897d`, HEAD `c9aeeb6`.
> **Outcome: V0 FAIL — 4/14 folds within a bar the charter requires on 14/14.**
> The failure is **structural non-identifiability**, not a tuning miss: a
> model-free bound shows *no* function of any candidate conditioning variable
> can pass V0 on this data.
> **No `ScenarioConfig` field was added, nothing was wired into
> capacity-evolution, no A/B was solved, nothing was registered, nothing was
> promoted.** Per card S1 — *"stay inside that distinction or stop"* — the lane
> stops.

Authority: `docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md`, S1/S2/S3
signed by the owner 2026-08-13. §3's **V0 identification gate** is
pre-registered and gates the lane; §3 states a miss "routes to diagnosis …
never to widening a band or re-fitting `R_f` against the miss."

---

## 1. What was chartered, and what the gate asked

The chartered term (card §2.2) is

```
term_f(y) = max(0, R_f(tau_model(y)) - S_f(y))          [$ /kW-yr]
```

whose admissibility (card §2.6, the half the owner personally signed) rests on
four checkable properties. The load-bearing one here is **property 3**:

> **Its identification is measured-vs-measured** (SOM rent vs measured
> tightness, cross-year); the refused knob was scaled to make a model output
> land on actuals.

V0 is the gate that tests exactly that property. Its pre-registered terms:

| V0 clause | value |
|---|---|
| vintage floor | **>= 5** anchor vintages ("no 3-point fit proceeds") |
| method | leave-one-vintage-out: fit on N-1, predict the held-out vintage |
| PASS bar | within **+-25 % or +-15 $/kW-yr, whichever is LARGER**, on CT **and** CC, on **EVERY** fold |
| selects | the conditioning-variable form, "by this gate alone" |

---

## 2. The vintage floor was CLEARED — the intake succeeded

The charter noted only 2023–2025 on disk (3 vintages) and made the 2018–2022
intake a precondition. That intake is **done and committed**, so the floor is
no longer what blocks the lane:

| vintage | CT $/kW-yr | CC $/kW-yr | source (PDF page) | monitor's own attribution of the level |
|---|---|---|---|---|
| 2019 | 125–129 | 149–154 | 2019 SOM p.97 | — |
| 2020 | 37–41 | 48–54 | 2020 SOM p.93 | — |
| 2021 | ~700 (ex-Uri 60–78) | ~800 (ex-Uri 81–105) | 2021 SOM p.114 | **Winter Storm Uri**, under the then-$9,000/MWh SWCAP (since lowered to $5,000) |
| 2022 | 137–193 | 173–234 | 2022 SOM p.108 | **"primarily due to the ORDC changes implemented at the beginning of the year"** |
| 2023 | 224–257 | 228–272 | 2023 SOM p.108 | **ECRS** — the monitor attributes **50 %** of the year's net revenue to ECRS price effects (`ecrs_effect_share_of_net_revenue = 0.5`, already on disk) |
| 2024 | 68 | 89 | 2024 SOM p.119 | normalised |
| 2025 | 52.59 | 82.96 | 2025 SOM p.125 | normalised |

**7 anchor vintages, floor 5 — CLEARED.**

Two intake facts worth carrying forward:

* **The SOM prints its multi-year net-revenue history only as unlabelled bar
  charts.** A vintage's value is transcribable **only** from the report that
  reports that year as its own subject year, in prose. A later report's history
  figure is *not* a transcribable source. (This is why the intake required
  fetching four additional reports rather than reading history columns off the
  three already on disk, as card §2.2 anticipated.)
* **The 2018 ERCOT SOM is absent from the Potomac document library** (2017 and
  2019 are both present). 2018 is outside the program's 2019–2025 working span
  (rule 22) in any case, so the identification span is 2019–2025.

Rule 22 compliance: this is **data intake, unrestricted** under the 2026-08-06
owner clarification ("what is held out is the SCORE, never the DATA"). **No
year was solved, scored or registered.** The stale quarantine notes in
`data/raw/som-competitive-conduct/README.md` and the datatype schema — which
still read "pending explicit owner authorization" — were corrected to match the
clarification.

---

## 3. V0 FAILED — 4/14 folds, best of eight candidates

Measured tightness comes from the committed NP6-905-CD reserve telemetry
(`data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`), Physical
Responsive Capability (`prc`). **Honesty gate, enforced in code:** the
tightness side reads a **MW quantity only** — `system_lambda`, `rtorpa`,
`rtoffpa`, `rtordpa` are price columns of the same parquet and are never read.
A price-conditioned tightness variable would make `tau_model` inherit the
model's own measured under-formation of the tail, so `R_f(tau_model)` would be
evaluated at an artificially loose point and the term would silently defeat
itself.

| year | n_hours | prc_mean | prc_p1 | frac_below_X | depth_below_X | CT | CC |
|---|---|---|---|---|---|---|---|
| 2019 | 8760 | 4988.7 | 3055.1 | 0.0071 | 0.818 | 127.00 | 151.50 |
| 2020 | 8760 | 5075.7 | 3121.4 | 0.0035 | 0.253 | 39.00 | 51.00 |
| 2021 | 8760 | 4871.0 | 3109.1 | 0.0089 | 6.134 | 700.00 | 800.00 |
| 2022 | 8760 | 5256.4 | 3327.6 | 0.0006 | 0.099 | 165.00 | 203.50 |
| 2023 | 8760 | 7018.0 | 4700.4 | 0.0001 | 0.035 | 240.50 | 250.00 |
| 2024 | 8760 | 9122.0 | 5816.4 | 0.0000 | 0.000 | 68.00 | 89.00 |
| 2025 | 8112 | 11092.0 | 6493.0 | 0.0000 | 0.000 | 52.59 | 82.96 |

(X = 3,000 MW, the ORDC minimum contingency level, OBDRR038 — a design
constant, not a swept threshold. 2025 has 8,112 telemetry hours because the
ORDC series ends at RTC+B go-live, 2025-12-05.)

Eight candidates were run — four conditioning forms x {linear, log} — and
**every one failed**:

| form | space | folds within bar | max abs err |
|---|---|---|---|
| **prc_mean** | **log** | **4 / 14** | 664.0 |
| prc_p1 | linear | 3 / 14 | 646.8 |
| prc_p1 | log | 2 / 14 | 669.3 |
| depth_below_x | log | 2 / 14 | 563.8 |
| prc_mean | linear | 2 / 14 | 641.1 |
| frac_below_x | linear | 1 / 14 | 689.3 |
| depth_below_x | linear | 0 / 14 | 668.9 |
| frac_below_x | log | 0 / 14 | 698.1 |

**V0 FAIL: 4/14, where the bar is required on every fold.**

**The SOM's own ex-Uri counterfactual makes it WORSE, not better: 2/14.** So
Winter Storm Uri is not the cause, and removing it is not a repair.

---

## 4. THE DIAGNOSIS — non-identifiability, proved model-free

The charter routes a miss to diagnosis, so: **which component failed?** Not the
functional form, not the fold count, and not Uri. The conditioning variable
itself carries no information about the rent.

**The rank inversion.** Order the years by measured tightness and by rent:

```
by tightness (tightest first): 2021, 2019, 2020, 2022, 2023, 2024, 2025
by rent      (highest first):  2021, 2023, 2022, 2019, 2024, 2025, 2020
```

**2020 is the 3rd-tightest year and has the LOWEST rent of all seven. 2023 is
the 3rd-LOOSEST and has the 2nd-HIGHEST.** They are inverted at both ends.

**The identifiability bound (this is the finding).** Any function `R_f(tau)`
must assign near-equal predictions to two years that are near-tied in `tau`.
So its best-case error on such a pair is at least half the pair's rent gap —
*regardless of functional form, fitting method, or sample size*:

| form | near-tied pair | tied to (% of range) | rent gap | irreducible error | tightest fold tol | verdict |
|---|---|---|---|---|---|---|
| prc_mean | 2020 vs 2021 | 3.3 % | $661 | **>= $330** | $15 | fold fails for ANY `R_f` |
| prc_p1 | 2020 vs 2021 | 0.4 % | $661 | **>= $330** | $15 | fold fails for ANY `R_f` |
| frac_below_x | **2023 vs 2025** | 1.3 % | $188 | **>= $94** | $15 | fold fails for ANY `R_f` |
| depth_below_x | **2020 vs 2023** | 3.6 % | $202 | **>= $101** | $15 | fold fails for ANY `R_f` |

Two of the four binding pairs **do not involve 2021 at all**, which is why
deleting Uri cannot rescue the fit.

The cleanest single instance: **2019 and 2020 sit within 1.7 % of each other on
`prc_mean` (4,989 vs 5,076 MW) and pay 127 vs 39 $/kW-yr — a 3.3x spread at
effectively identical measured tightness.**

**Why the data looks like this — the monitor says so itself.** Three of the
seven vintages have the IMM's own published attribution to a *market-design
change or an extreme event*, not to tightness: 2021 = Winter Storm Uri under a
price cap that no longer exists; 2022 = "primarily due to the ORDC changes
implemented at the beginning of the year"; 2023 = ECRS, **half the year's net
revenue by the monitor's own number**. The ERCOT merchant rent series over
2019–2025 is a **regime series, not a tightness series.**

This is a coherent result rather than a surprise: it is the same fact the
program already signed from the other side. The C3c ledger accepts that the
scarcity tail is *not a function of fundamentals the model can condition on* —
and `R_f(tau)` is precisely an attempt to make it one.

---

## 5. WHY THE LANE STOPS HERE rather than proceeding to the A/B

Card S1 signs the term as admissible **on the §2.6 distinction** and instructs:
*"stay inside that distinction or stop."* §2.6 property 3 is that the
identification is measured-vs-measured. **V0 is the test of property 3, and it
failed.**

With no identified `R_f`, any value the term could take would be a level chosen
without conditioning content — which is **exactly** FFR-6A verdict row 4's
refused *"scalar uplift/offset/multiplier … (any 'add $X', 'scale to
SOM/actuals')"*, the thing S1's distinction exists to exclude. Rule 1
`[R-STRUCT]` names the same object: *"never reach the right number through a
mechanism that isn't real (a fitted adder …)."*

So the downstream scope is **not reached, deliberately**:

* **No `ScenarioConfig` field.** Shipping a default-off field with no
  identified parameters would plant an unidentified, re-armable knob — rule 24
  `[R-REGISTRY]` and rule 26 `[R-DELETE]` ("a deprecated parameter that still
  parses is a re-armable answer key").
* **No matrix row.** Rule 28(c) attaches the row duty to *adding a
  `ScenarioConfig` field*; the matrix's own header records this reading
  explicitly ("… no matrix row by rule 28(c) because it adds NO ScenarioConfig
  field"). No field, no row. `scripts/check_mechanism_matrix.py` exits **0**.
* **No wiring, no A/B, no registration, no promotion.** V1 conditions on an
  identified `R_f`; there is none. Nothing was solved, so no forecast-namespace
  run exists to register.

**The measured screen-revenue movement this session produced is therefore
exactly $0.00/kW-yr against the ~50–70 $/kW-yr gap, and there is no retire/stay
confusion matrix, because no A/B was run.** Reporting a movement would require
first choosing the very knob the gate refused.

---

## 6. What this leaves standing, and what it does not

**Untouched (card §4 must-nots, all held):** no dispatch price, no LP
objective/bound, no scored series, no backcast artifact, no keeper, no bench,
no C3a/C3b/C3c contact, no ORDC/`screen_reserve_value` double-count (nothing
was added to double-count with). OVERRIDE-FIX / stage-B untouched (S3's
promotion hold is moot — there is nothing to promote). L-2 untouched. Card Q
stays closed.

**The defect is unchanged and still open.** Card §1's sizing stands: the screen
under-reads merchant revenue by ~50–70 $/kW-yr, every merchant thermal class
reads loss-making in every screen year, and retention rests on the measured
non-monotone admission cap (the D-20(a) defect). **This session did not fix
that; it established that L-1's chosen instrument cannot.** Frontier rank 2
stays open.

**What is now genuinely better, and durable:**

1. **The anchor set is 3 -> 7 vintages**, schema-validated, each row carrying
   `source_doc` + `source_page`. Any future lane in this family starts from
   real data rather than a 3-point corner.
2. **`scripts/data/derive_screen_scarcity_rent.py` is the standing test.** Its
   rule-23 re-derive trigger is a new SOM or telemetry vintage. A future
   session re-runs one command instead of re-deriving this conclusion — the
   DO-NOT-REDO discipline, in executable form.
3. **A transcription limit is now documented** (history exists only as
   unlabelled bar charts), so no future session plans an intake that cannot
   work.

**Where the owner's concern should go next.** The concern that motivated the
charter — *"high scarcity years like 2023 … will yield retirements that are not
realistic in forecast"* — is **unaddressed and, on this evidence, sharpened**:
2023's rent was half ECRS by the monitor's own accounting, so a forecast that
conditions merchant revenue on *tightness* will miss high-revenue years for a
second, independent reason beyond the C3c tail. Three routes remain, none
opened here:

* **L-2 (E1 dispersion)** — card §6's named structural complement; bounded by
  the same measured fact (2024's scarcity is λ-led, 149/184 of λ>$100 hours
  carried adders <= $10), so its expected reach is single-digit-to-~20 $/kW-yr.
* **Condition on market DESIGN rather than tightness** — the regime variable
  the data actually exhibits (ORDC curve vintage, ECRS existence, SWCAP level,
  RTC+B). This is a different mechanism from the one chartered and would need
  its own card; it is *not* authorised by S1/S2, and the RTC+B boundary means
  the forward regime has **zero** measured anchors until the 2026 SOM publishes
  (~mid-2027).
* **L-0 with the disclosure** — card §6's honest baseline: enter the second
  `readiness_limits` row naming the screen's measured ~50–70 $/kW-yr merchant
  revenue understatement, and re-classify frontier rank 2 from "open lane" to
  "accepted limit". The card is explicit that this re-classification **is a
  decision only the owner can sign**, so it is put here, not taken.

---

## 7. Reproduce

```
python scripts/data/derive_screen_scarcity_rent.py            # V0 gate -> exit 1 (FAIL)
python scripts/data/derive_screen_scarcity_rent.py --ex-uri   # ex-Uri sensitivity -> 2/14
python scripts/data/curate_som_competitive_conduct.py         # re-validate the intake
python scripts/check_mechanism_matrix.py                      # exit 0
```
