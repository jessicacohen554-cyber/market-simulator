# CHARTER — Option C, NYISO-first: the hydro **budget period**, not a new water-value term

**Owner instruction:** Option C, NYISO-first charter (2026-09-07, on
`DECISION-CARD-nyiso219-hydro-within-month-allocation-2026-09-07.md`).
**From:** session nyiso-219, NYISO `backcast-calibration` lane.
**ZERO LP. Nothing armed, screened, solved or registered. No `src/market_sim/` change, no
`ScenarioConfig` field, no scorer change, no marker touched, no matrix cell letter changed, no
held-out year spent.** This is a design charter and a feasibility census. **It authorizes nothing**;
building any of it is a separate owner decision on §9.

**Keeper, unchanged:** `2026-09-07-nyiso-213-summer-seam` — CALIBRATED, grade 7/8, zero failing
criteria, C3c the lone ledgered caveat. Hydro is **not a rubric criterion** and nothing here is
gated on a price residual (rule 1 `[R-STRUCT]`).

> **The headline, before the detail.** Option C does **not** need a new water-value term in the
> objective. **The LP already computes a water value** — it is the dual of the hydro budget row —
> and the defect is that there is **exactly one of them per month**. The faithful fix is to
> **shorten the budget period** to the fleet's pondage duration, which makes the water value
> time-varying endogenously. **The LP row builder already supports this with no code change**
> (§3). And this successor was **named in writing on 2026-07-25** and never taken up (§2) — this
> charter is its overdue statement, not a new idea.

---

## 1. Scope discipline, stated first

* **No in-sample rubric failures exist for NYISO**, and this charter targets none. The only failing
  cells in the NYISO record are on the 2022 validation holdout, which rule 22 `[R-HOLDOUT]` forbids
  targeting: it motivates, never gates.
* **Today's census numbers (§5) are NOT covered by the nyiso-219 PREREG.** They were taken *after*
  the pre-registered measurements were read, they carry **no predictions**, they adjudicate
  nothing, and they are reported as a **feasibility census** for this charter. They are labelled as
  such wherever they appear.
* **Two cells stay adjudicated and are NOT re-opened.** `hydro_ror_split` is **G**
  (governance-refused, nyiso-111 — its rule-1 mapping would flatten Robert Moses Niagara's
  treaty-structured diurnal shape) and `hydro_budget_nameplate_aware` is **I** (provably inert,
  nyiso-107). §5 reads the **same external sources** (ORNL EHA / HILARRI) for a **census**, which is
  not a re-test of either mechanism; and §5's census in fact **corroborates nyiso-111's refusal**
  (Niagara's EHA `Mode` is exactly the hybrid `Run-of-river/Peaking` label that refusal turned on).
* **Rule 25 `[R-ISO-SCOPE]`:** NEISO's published pondage-duration taxonomy (§5c) is cited as an
  **existence proof of the concept in North American practice**, never as a source NYISO may
  borrow. NYISO would derive its own from its own fleet's data or the mechanism does not arm here.

## 2. Four independent lines converge on one object — and the successor was already named

**This charter's object is not new. It was stated, in writing, fourteen months of sessions ago, and
no session took it up.** `docs/FINDING-nyiso-overnight-marginal-is-hydro-water-value-2026-07-25.md`
§6, verbatim:

> "A p95 hourly ceiling *bounds* the hoarding but leaves the monthly optimization intact: the LP
> still arbitrages one budget across ~700 hours, just under a cap. The physically faithful
> representation of a run-of-river fleet with hours-to-days of pondage is a **shorter budget
> period** (daily / pondage-duration), not a ceiling on top of a monthly budget. Pondage volume is
> a licensed physical parameter, so a duration-limited budget regenerates forward and responds to
> changed conditions. That is the named successor lane; it is a new mechanism and needs its own
> charter and owner sign-off — and under rule 19 it must **replace or reconcile with**
> `hydro_dispatch_envelope`, never stack on it."

It is logged at `docs/calibration-log/nyiso.md` lines 582–583 and has **no `ScenarioConfig` field,
no matrix row and no charter** at this HEAD. **This document is that charter.**

Four lines, taken independently and by different instruments, land on the same defect:

| line | evidence | what it says |
|---|---|---|
| **2026-07-25** | the overnight price-setter is the hydro budget **dual**; hydro absorbs 58–80 % of the marginal overnight MW | the LP over-arbitrages a monthly budget; the successor is a **shorter period** |
| **nyiso-92** (2026-07-28) | the envelope + floor arm moved hourly r 0.594/0.549/0.381 → 0.741/0.778/0.552 and became the keeper | the ceiling **bounds** the hoarding; it does not remove the freedom |
| **nyiso-218** (2026-09-07) | month energy r ≈ 1.000, hour-of-day r ≈ 0.98, **within-month day-to-day r 0.207–0.392**; amplitude **1.86–2.25×** the actual's | all the residual is in the dimension **between** the two armed mechanisms |
| **nyiso-219** (2026-09-07) | no admissible daily driver carries it (flow 0.243, climatology 0.031); the **actual** tracks load (0.308) better than flow; the **model** tracks load at 0.62–0.69 | the model is **not missing a driver** — it has the right driver and responds ~2× too hard |

**The mechanism that explains all four in one line:** inside a month the LP's water value is a
**single number** (the budget row's dual), identical on day 1 and day 28. Any price difference
between days of the same month is therefore pure arbitrage profit with **no offsetting cost**, so
the fleet swings freely between days. **That is the missing bound**, and it is a property of the
budget *period*, not of any input.

## 3. The structural finding that makes this cheap: **the LP row family is already general**

`model/lp/rows.py::_build_hydro_rows` builds one row per `(hydro generator, period)` from a
caller-supplied `(T,)` integer index and an `(n_hydro, n_periods)` energy matrix:

```python
month_index = np.asarray(hydro_month_index, dtype=int)   # (T,)  -- ARBITRARY period map
n_months    = energy.shape[1]                            #       -- ARBITRARY period count
rows = (g[:, None] * n_months + month_index[None, :]).ravel()
```

Nothing in it assumes twelve periods or calendar months. The caller
(`rows.py:1820`) merely *defaults* to `_hour_to_month_index(T)` when no index is supplied.
**Shortening the budget period is a re-indexing, not a new row family: `rows.py` needs no change at
all**, the vectorized `coo_matrix` assembly is untouched (rule 2 `[R-VECTOR]` satisfied by
construction), and the dual the pricing path reads (rule 4 `[R-DUALS]`) is the same dual, just one
per shorter period.

**Consequences worth stating plainly:**

* **Option C needs NO new objective term.** Hydro's marginal cost is `VOM["hydro"] = 1.4 $/MWh`
  (NREL ATB 2024) and nothing else — no fuel, no water price. The opportunity cost of water is
  *already* endogenous as the budget dual. Adding a water-value *coefficient* would be a fitted
  scalar and is **not** what this charter proposes.
* **The work is in `data/hydro.py` and the plumbing**, where the twelve-wide assumption actually
  lives (`HydroBudget.monthly_energy`, `_MONTHS_PER_YEAR`, `hours_per_month`, `load_hydro_budget`,
  `pipeline/spec.py`), plus **one gated `ScenarioConfig` field**.
* **A shorter period is strictly a restriction of the feasible set.** Every daily-budget solution is
  feasible for the monthly budget; the reverse is false. So the mechanism can only *remove*
  arbitrage freedom, never add it — which is the correct direction and makes its failure mode
  predictable (over-constraint, not over-freedom).

## 4. What a build would have to satisfy

**Rule 17 `[R-FLOOR-WINDOW]` (driver / window / forward story):**

* **Driver (a).** A plant's pondage — the usable forebay/reservoir volume between its licensed
  operating limits — physically bounds how much energy it can move between days. Robert Moses
  Niagara and St. Lawrence are large-flow, **limited-pondage** projects: their EHA operating modes
  (§5b) are `Run-of-river/Peaking` and `Peaking`, i.e. they shape **within** a short horizon, not
  across a month.
* **Window (b).** All 24 hours of every period — this is not a floor and pins no diurnal shape. It
  binds where the LP would move more energy between days than the forebay can hold.
* **Forward story (c).** Pondage volume is a **licensed physical parameter**, re-derived only when
  its source vintage updates (rule 23 `[R-FROZEN-DERIVE]`). It regenerates for any forward year
  without knowing that year's weather, and the *level* it constrains still scales with the water
  year through the existing budget. **This is exactly the property nyiso-219 measured that the
  daily inflow driver lacks** (a forecast year cannot have measured streamflow; it *can* have the
  same licensed volume).

**Rule 19 `[R-ONE-MECH]` — the hard part, and it must be settled BEFORE any solve.** Two mechanisms
already shape this fleet and **neither is inert**: nyiso-219 measured the model sitting **at** the
`hydro_dispatch_envelope` ceiling in **26.9 / 32.4 / 42.2 / 41.6 %** of hours, carrying
**32.4 / 38.1 / 49.4 / 48.4 %** of annual hydro energy there, with `hydro_min_flow_floor` beneath.
A shorter budget period would overlap both substantially. The 2026-07-25 finding is explicit that
the successor must **replace or reconcile with** the envelope, **never stack on it**. A charter that
did not name this would be proposing exactly the stacked-floor pattern rule 19 exists to forbid.
**Neither reconciliation is designed here**, and the two candidate postures are put to the owner as
§9 Q2.

**Rule 21 `[R-DOF]` — where the free parameter is, honestly.** The period length **is** the free
parameter. There are three possible identifications and only two are admissible:

1. **Per-plant, from licensed usable storage** (volume ÷ generation rate → hours of pondage).
   Zero fitted scalars; the number is the plant's own licence. **Admissible, and the target.**
2. **A published categorical operating class** naming the duration (NEISO's `HDP` = *daily*
   pondage, `HW` = *weekly* pondage, §5c). Zero fitted scalars, categorical-external — the same
   basis `hydro_ror_split`'s classifier uses. **Admissible if NYISO has such a field.**
3. **A length chosen because it makes a criterion move.** **FORBIDDEN** — that is fitted-mechanism
   selection (rule 1 `[R-STRUCT]`, and the rule 29 `[R-SCREEN]` gate is explicit that a screen
   "may kill an arm; it may never promote one" and is "never gated on the target residual").
   **A period-length sweep against the gates is not a screen, and this charter refuses one in
   advance.**

## 5. The data question, NARROWED from "does anything exist?" to a named join

*(Feasibility census, taken 2026-09-07, **not** pre-registered, **no predictions attached**.)*

**(a) The plant → dam linkage is already in the repo and is essentially complete.**
`data/raw/hilarri/HILARRI_v4.csv` (ORNL HILARRI v4, committed) joins EIA plant ids to dams:

| | measured |
|---|---|
| NYISO hydro plants with a HILARRI row | **163 of 163 — 100.0 % of 4,681.0 MW** |
| … carrying a **NID dam id** (the join key to storage) | **152 plants — 98.5 % of MW** |
| … carrying a USGS gauge id | 27 plants — 23.2 % of MW |
| Robert Moses Niagara (2693) | dam `ROBERT MOSES - NIAGARA`, **NID `NY16253`** |
| Robert Moses St. Lawrence (2694) | dam `ROBERT MOSES - ST. LAWRENCE`, **NID `NY00678`**, gauge `USGS-04264331` |

*(An incidental corroboration: HILARRI independently names `USGS-04264331` for St. Lawrence — the
identical gauge nyiso-219's census selected on its own, by river position.)*

**(b) The operating-mode census** — ORNL EHA FY2024 `Operational` sheet, **163 of 163 matched**,
weighted by nameplate:

| EHA `Mode` | MW | plants | % fleet MW |
|---|---:|---:|---:|
| **Run-of-river/Peaking** *(incl. Robert Moses Niagara)* | 2,471.4 | 9 | **52.80** |
| **Peaking** *(incl. St. Lawrence)* | 1,180.6 | 22 | **25.22** |
| Run-of-river | 477.7 | 70 | 10.21 |
| *(no Mode)* | 286.8 | 43 | 6.13 |
| Run-of-river/Upstream Peaking | 151.4 | 11 | 3.23 |
| Intermediate Peaking | 140.0 | 2 | 2.99 |
| Reregulating / Canal-Conduit | 32.1 | 6 | 0.69 |

**84.24 % of fleet MW carries a *peaking* component in its published operating mode** — that is
every label containing "Peaking", which is the committed probe's definition; on the two dominant
labels alone (`Run-of-river/Peaking` + `Peaking`) it is **78.02 %**. Both readings are given because
the wider one includes `Run-of-river/Upstream Peaking` (3.23 %), where the peaking is *upstream* of
the powerhouse and the plant itself may not shape — so the narrower figure is the conservative one
and neither is quoted alone. These plants are not price-takers and are not expected to be flat —
consistent with nyiso-219's measurement that the *actual* fleet tracks daily load at r 0.308. **The
question was never whether they shape. It is over what horizon**, and `Peaking` /
`Run-of-river/Peaking` are labels for **sub-monthly** pondage.
EHA's own `Water` field independently reproduces the M1 water-source census (`Niagara River`,
`St. Lawrence River`), a second source agreeing with EIA-860.

**(c) What is MISSING, named precisely.** Neither committed source carries a storage volume or a
head:

* **ORNL EHA `Operational`** has `Mode`, `CH_MW`, `CH_MWh`, `Water`, `HUC` — **no head, no storage**.
* **HILARRI** is a linkage table — **no storage volume**; it carries the `nidid` that *points at*
  one.
* **The National Inventory of Dams (USACE)** carries per-dam `normal storage` / `maximum storage`
  (acre-feet) and dam height, is public, and is **not in this repo** — it would be a new intake
  against **152 named dam ids**, which is a bounded, ordinary `data-intake` job rather than an open
  research question.
* **Head** (needed for acre-feet → MWh) is in none of the three. FERC licence documents carry it
  per project; NID dam height is a **proxy, not head**, and must not be silently substituted.
* **NEISO precedent, cited as an existence proof only (rule 25):** ISO-NE publishes a per-asset
  hydraulic unit type that *names the duration* — `HDP` conventional **daily** pondage, `HDR`
  conventional daily run-of-river, `HW` conventional **weekly** pondage — and this repo already
  ingests it (`data/raw/capacity-market/scc/neiso/`, capx-S4). **NYISO publishes no equivalent
  field**, so NYISO cannot borrow it; it establishes that the attribute is real, published and
  categorical somewhere in North American practice.

**Honest caveat, stated at the gate:** NID "normal storage" is a **reservoir** volume, not the
**licensed operating range**. For a large-flow, low-storage project the usable range can be a small
fraction of it, and using normal storage literally would **overstate** pondage — which would make
the mechanism too weak, not too strong. Whether the licensed range is recoverable at fleet grain is
the remaining open question and is put to the owner as §9 Q1.

## 6. What must NOT happen — named in advance

* **No period-length sweep against the gates.** §4 rule 21 case 3. If the licensed number cannot be
  identified, the mechanism does **not** arm on a chosen length.
* **No pin to measured `NG: WAT` daily totals** at any grain. nyiso-219 measured that this reaches
  r = 1.000 by construction, **which is exactly why it is forbidden** (rule 13 `[R-MEASURED]`).
  Tripwire: if a build's within-month r jumps to ~0.95, check whether it has become this.
* **No re-opening of `hydro_ror_split` (G) or `hydro_budget_nameplate_aware` (I)** without new
  evidence. §5b's census **corroborates** nyiso-111's refusal and does not disturb it.
* **No stacking on `hydro_dispatch_envelope`** (rule 19). §9 Q2.
* **No per-plant hourly structure invented.** `NG: WAT` is an ISO aggregate and there is no
  per-plant hourly hydro series (nyiso-214, nyiso-218, nyiso-219). A per-plant *pondage duration*
  from a published licence is a **static plant attribute**, not an hourly claim, and that
  distinction is what keeps it admissible.
* **No promotion on the residual.** Rule 14 `[R-ACCURATE]` cuts both ways and is stated before any
  number: hydro is ~20 % of NYISO generation, so re-timing it **will** move C3a/C3b/C3c. If the
  faithful representation makes the price fit worse, **it stays** and the worse fit is a discovered
  root-cause question (rule 1, first half). The 2026-07-25 probe is the precedent: it made C3a-2023
  *worse* (+18.3 % → +22.2 %) and was still recorded as **mechanism confirmed**.

## 7. How it would be screened (rule 29 `[R-SCREEN]`), if it is ever built

* **Phase 0, zero LP, first and blocking.** The NID intake + the pondage-duration derivation, and a
  **pre-solve footprint**: how many plant-periods would bind, on what share of fleet MW and energy,
  and — critically — **the overlap with the envelope's already-measured 27–42 % binding hours**
  (rule 19). If phase 0 shows the two mechanisms are substantially the same constraint, the arm
  never reaches a solve and the reconciliation question is answered on arithmetic.
* **One screen year, named in the PRECOMMIT before it runs**, chosen as the year the mechanism's own
  measured footprint is largest — **never** the year with the biggest residual.
* **The gate is STRUCTURAL and STOP-only:** does the dispatch response have the direction and
  magnitude the pre-solve footprint implies; is the day-to-day amplitude ratio (currently
  **1.86–2.25×**) reduced toward 1; is the footprint confined to the rows the mechanism claims; does
  no non-target load-bearing criterion flip PASS → FAIL. **It may kill the arm; it may never promote
  it, and it is never read on C3a.**
* **G-CTRL form 4** — the incumbent keeper's committed bundle **is** the control (rule 29(b)); a
  **G-DRIFT** code audit from the keeper's `git_sha`, not a control solve.
* **Rule 16 `[R-ALLYEARS]`** — the full span is one `--year 2023 2024 2025` invocation and one
  bundle; the screen bundle is a throwaway probe, never registered.
* **Rule 31 `[R-RETAIN]`** — gitignore the bundle family at the moment it is written; **never `rm`**;
  surface the promotion question before the session ends.

## 8. What this charter deliberately does NOT decide

It does not choose a period length, does not propose a `ScenarioConfig` field name, does not design
the rule-19 reconciliation, does not commit to the NID intake, and **does not claim the mechanism
would improve any criterion**. nyiso-219 measured the ceiling on driver-based approaches at mean
multiple r **0.402** against a keeper already at 0.207–0.392; **no comparable ceiling has been
measured for a budget-period change**, because it is a constraint on freedom rather than a
predictor, and this charter does not assert one.

## 9. The questions for the owner

* **Q1 — fund the NID intake?** A bounded `data-intake` job: USACE National Inventory of Dams
  storage attributes for **152 named dam ids** (98.5 % of NYISO hydro MW), plus the open question of
  whether the **licensed operating range** — not just normal storage — and **head** are recoverable
  at fleet grain. Zero LP. Ends in a measured answer, exactly as nyiso-219 did, and can return a
  clean negative that closes Option C cheaply.
* **Q2 — which rule-19 posture?** **(i) REPLACE:** the shorter budget period supersedes
  `hydro_dispatch_envelope`, which was itself described by its own author as the wrong instrument
  for this failure mode. **(ii) RECONCILE:** both stay, with the envelope demoted to the pure
  deliverability ceiling it is and the period carrying the inter-temporal bound, each with a
  disjoint declared window. **Stacking is not an option** and is not offered.
* **Q3 — is a `Peaking`-labelled fleet the right place to start?** §5b measures **78.02–84.24 % of
  fleet MW** carrying a peaking component. If the owner reads that as "these plants genuinely do
  shape across weeks", the object is smaller than this charter assumes and Option A stands. **The
  lane does not claim to have settled this**, and it is the one question that could close the object
  outright.

**No eighth pending owner ruling is opened.** The seven pending rulings (nyiso-206, -207, -203,
DECISION-CARD-nyiso193 §5/5.1, -208, -214 §6, -215 §6) are untouched. This charter is the Option C
deliverable the owner instructed, and it authorizes nothing on its own.

---

## 10. OWNER RULINGS, 2026-09-07 — and what executing them returned

All three §9 questions were answered the same day. **Recorded here as the authoritative record**;
the measurement that executes them is
`docs/FINDING-nyiso219-pondage-duration-2026-09-07.md`.

| | ruling | status |
|---|---|---|
| **Q1** | **Fund the full intake** — NID storage + licensed operating range + head | **EXECUTED, partially served — 1 of 3 recovered** (§10a) |
| **Q2** | **Decide the rule-19 posture at phase 0**, on the overlap arithmetic rather than by preference | **STANDING — not yet reachable** (§10c) |
| **Q3** | **Undecided — measure the shaping horizon**, from licence operating ranges rather than the categorical `Mode` label | **ANSWERED BY MEASUREMENT** (§10b) |

### 10a. Q1 — the intake ran, and returned one of its three targets

`data/raw/nid/` now holds the USACE National Inventory of Dams subset (vintage 2026-08-28, 189 dam
rows, public domain, provenance and checksum in its README) for the 152 NID ids naming NYISO's
hydro fleet.

* **Storage — RECOVERED**, `Normal`/`Max` present for **98.4–98.5 %** of fleet MW.
* **Head — MOSTLY NOT.** NID's `Hydraulic Height` covers only **20.80 %** of scored MW; the
  remainder falls back to a **labelled dam-height proxy** whose error runs in **both** directions.
* **Licensed operating range — NOT IN NID AT ALL.** `Normal Storage` is a reservoir volume, not an
  operating band; recovering it needs the projects' **FERC licence documents**, untouched here.

**§5's "missing" list was right about what was missing, and wrong about how much NID would fix.**
The charter expected NID to serve storage and leave head open; it served storage, left head *mostly*
open, and could not address the operating range at all.

### 10b. Q3 — ANSWERED: the fleet does not shape across weeks

Measured as an **upper bound** (full reservoir volume, efficiency 1.0, zero free parameters), so
that no refinement can rescue the monthly period:

* **72.01 %** of scored fleet MW cannot hold **one day** of its own full output;
* **97.54 %** cannot hold a week; **98.31 %** cannot hold a month;
* **Robert Moses Niagara — 51.89 % of fleet MW — holds 0.244 h ≈ fifteen minutes**, from a
  **71-acre**, 5,350 acre-ft forebay, against the LP's **730-hour** budget period;
* St. Lawrence (19.48 %) holds **73 h** on the full volume of Lake St. Lawrence — and its licensed
  band under IJC Plan-2014 is a small fraction of that.

**The charter's premise is confirmed from hydrology, independently of dispatch.** The EHA `Peaking`
labels §5b reported are not wrong — they describe genuine *diurnal* forebay cycling, exactly what a
15-minute-to-3-day pondage supports — but they **do not license a month**, which is what Q3 asked
and what the label alone could not settle. **The object stands.**

### 10c. Q2 — standing, and not yet reachable

The owner ruled the rule-19 posture is decided **at phase 0**, on the overlap between a shortened
period and `hydro_dispatch_envelope` (armed in the keeper, binding **27–42 %** of hours and carrying
**32–49 %** of annual hydro energy). That arithmetic needs a **period length**, and a period length
needs the **licensed operating range** — Q1's unserved half. **So Q2 is blocked behind a FERC-licence
intake, not behind a solve.** Nothing about it is decided here, and rule 21 `[R-DOF]` case 3 stands
undisturbed: **a length chosen because it makes a criterion move is forbidden**, and this session
neither chose nor swept one.

**§6's refusals are unchanged and still bind:** no `NG: WAT` pin, no period sweep against the gates,
no stacking on the envelope, no per-plant hourly structure invented, no promotion on the residual.
