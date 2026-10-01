# FFR-5B — What a procurement channel for VRE entry would have to BE

**Lane:** structural scoping (owner decision **D-16(a)**, sitting Addendum R.3/R.5, signed
2026-08-05). **Design only.** No code landed, no solve run, no default moved, no parameter
proposed as a number. The deliverable is a design plus a rule-13 `[R-MEASURED]` admissibility
argument, and a proposed owner card for the implementation decision — which this lane does not
open.

**Head at start:** `origin/main` `547a7c38`; branch rebased onto it before any work, and rebased
again onto **`de804d07`** at push time (three PRs landed mid-session — neiso-83, nyiso-127 and
its Phase-0 intake). The interim commits touched `mechanism-matrix.js` and **neither keepers nor
`calibration-complete.json`**, so every state claim below is unchanged at the later head; the
matrix guard was re-run clean after the rebase (O.3 discipline — this lane changes no cell, so
there was none to re-check).

**State re-verified at this session's own head (not inherited from the prompt):** keepers
ERCOT `2026-08-04-ercot165-unpooled-share` · PJM `2026-08-04-pjm-152-collapse` · CAISO
`2026-08-04-caiso-172-measured-path15` · NYISO `2026-08-04-nyiso-125-seam-envelope` · NEISO
`2026-08-04-neiso81-chpheatrate` · MISO `2026-08-04-miso-127-onlinepmin`. Markers: `complete`
= {NEISO, NYISO, PJM}; `final` empty. Holdout freeze active and irrelevant here — this lane
solves nothing and scores nothing.

**What is measured in this document, and where it came from.** Everything numeric below is
computed from committed on-disk data (`data/raw/eia-860/vintage_{2018..2024}/` proposed +
operable sheets, mapped ISO-wards through the repo's own `BA_CODE_TO_ISO`) or read off source
at head. No LP was solved. The two measured tables — §1.1's forward-skill census and §4's
per-ISO pipeline inventory — are new to this lane; everything else is cited to FFR-3V, FFR-4A
or the code.

---

## 0. Headline

**The verdict is a partition, not a single design, and the partition is the finding.** D-16's
gap is two gaps that FFR-3V's framing correctly named together and that a mechanism design must
separate:

1. **A near-term committed-procurement gap — REAL, rule-13 ADMISSIBLE, and a genuinely missing
   mechanism.** Step 4's known-additions channel (`load_planned_additions`) deliberately skips
   wind and solar on a premise the record refutes, so the only path VRE has into the fleet is
   the merchant screen. The admissible fix is a **VRE limb of the existing step-4 channel**,
   keyed to the EIA-860 proposed-generator pipeline at the run's own vintage — the additions-side
   analogue of the confirmed-retirement registry, sharing its instrument gate, its vintage
   information gate and its `source:` attribution. **Recommended.**
2. **A long-run policy-procurement gap — REAL, and NOT admissibly closed by a new channel.**
   Rule 19 `[R-ONE-MECH]` refuses it: a dated clean-energy share obligation driving procurement
   is *already* the RPS LP row's phenomenon. What is wrong is that row's **spatial grain and
   scope** — one ISO-wide annual row (`lp/rows.py::_build_rps_row`) carrying a *load-weighted
   blend* of state obligations, so a binding Minnesota 55 %-by-2035 statute is diluted to
   slackness by Arkansas's zero. **Recommend NO new channel here.** The correct work is inside
   the existing mechanism and belongs to its own later decision (§5.3).
3. **A residual with no admissible representation at all** — corporate PPAs and
   beyond-horizon procurement. **The honest deliverable is to say so and disclose it.** That is
   the null inside this design, and it is stated rather than papered over.

**Measured, so nobody reads §1 as a fix.** The construction-committed pipeline at vintage *V*
covers a **median 0.63 / 0.33 / 0.21** of realized solar COD over *V+1 / V+2 / V+3* across the
six ISOs (§1.1). The recommended channel therefore closes the near-term half of the gap and
**does not close MISO's 18.649 GW miss** — it is not intended to, and any follow-on session
whose move is to widen the status filter until MISO's number lands has crossed the line §3 exists
to draw.

**One free parameter is proposed in total: none.** The channel's whole surface is one gate flag
and one already-intaken data path (§2.5, rule 24 `[R-REGISTRY]`).

---

## 1. Limb 1 — what drives procurement volume, as a forward-regenerating input

The rubric is rule 13's test, verbatim: *could this same quantity be produced for a forward year
from forward drivers, and would it respond to changed conditions?* The confirmed-retirement plan
(`docs/handoffs/confirmed-retirement-plan-2026-07.md` §2.3) is the worked precedent for applying
it, and it supplies two sharpening sub-tests this lane adopts:

* **the instrument test** — is there a public, dated artifact a third party can re-query, so the
  row is reproducible rather than asserted? (The retirement side's "enforceable instrument";
  the additions side's `_PLANNED_FIRM_STATUSES`.)
* **the horizon test** — over what forward years does the driver have any content at all? A
  driver that is empty past *V+4* is not thereby inadmissible; it is admissible *and bounded*,
  and a design that hides the bound is the dishonest part.

Four candidates were worked. None was pre-approved; two are refused.

### 1.1 Candidate A — the EIA-860 proposed-generator pipeline cohort — **ADMISSIBLE, near-term only. The strongest limb.**

**What identifies it.** `data/raw/eia-860/vintage_<V>/eia860_generator_proposed.parquet`: one row
per proposed generator with `Nameplate Capacity (MW)`, `Status`, `Effective Year`/`Month`,
`Current Year`/`Month`, `Technology`, `Plant Code` and (via `eia860_plant.parquet`) balancing
authority and lat/lon. Already intaken. Already consumed by `load_planned_additions`
(`data/fleet/eia860.py:1916`) for thermal. Status vocabulary at vintage 2020 (national): `P` 456
rows / `U` 395 / `T` 344 / `V` 277 / `L` 234 / `TS` 96 / `OT` 3.

**At what vintage.** Annual EIA-860 release. The as-of machinery already exists and is already
correct: `config/paths.py::active_eia860_dir` / `set_eia860_vintage`, with
`fleet/models.py::operable_vintage_year` supplying the `Effective Year > vintage` guard that
`load_planned_additions` uses (`eia860.py:1992` — the FH-1 leak fix).

**Forward analogue.** Exact. Every future EIA-860 vintage carries a pipeline; the quantity is
produced for a forward year by reading that year's sheet, with no model input of any kind. This
is the same construction as the additions pipeline the thermal channel already runs on, and the
same construction as the confirmed-retirement registry's re-query cadence.

**Does it respond to changed conditions?** Partly, and the partial answer must be stated
honestly. Rows enter and leave, statuses advance (`P → L → T → U → V → TS`) and regress,
`Effective Year` slips — all responding to real-world cost, policy and interconnection
conditions. What it does **not** respond to is conditions *the model changes*: a modelled price
collapse does not empty the queue. That is not a defect, it is the definition of an exogenous
committed-decision channel, and it is exactly why the horizon bound in §3.3 is load-bearing
rather than cosmetic. A confirmed retirement has the same property.

**Horizon test — MEASURED.** At vintage 2024 the pipeline spans effective years 2025–2030 and is
front-loaded; past *V+4* it is essentially empty:

| eff. year | CAISO | ERCOT | MISO | NEISO | NYISO | PJM |
|---|---|---|---|---|---|---|
| 2025 | 1.31 | 9.63 | 4.74 | 0.02 | 0.32 | 4.08 |
| 2026 | 2.26 | 8.45 | 4.75 | 0.03 | 0.42 | 3.35 |
| 2027 | 1.52 | 5.88 | 2.06 | 0.20 | 1.22 | 2.85 |
| 2028 | 0.45 | 2.12 | 2.47 | 0.00 | 0.49 | 0.51 |
| 2029 | 0.06 | 0.61 | 0.06 | 0.32 | 0.18 | 0.00 |
| 2030 | 0.00 | 0.32 | 0.00 | 0.00 | 0.01 | 0.75 |

*(all-status proposed **solar** GW, `Effective Year > 2024`, vintage-2024 sheet)*

**Forward-skill test — MEASURED, and it is the number that decides the design.** For every
(ISO × vintage *V* ∈ {2019…2022} × horizon *h* ∈ {1,2,3}) cell with a non-trivial denominator,
the pipeline MW at vintage *V* with `Effective Year ≤ V+h` is compared against **realized COD MW
in *V+1…V+h*** read from the canonical operable sheet. Pooled median coverage (and IQR):

| tech | status basis | *h*=1 | *h*=2 | *h*=3 |
|---|---|---|---|---|
| **solar** | `U/V/TS` (construction-committed — the thermal channel's rule) | **0.63** (0.49–0.87) | **0.33** (0.16–0.44) | **0.21** (0.12–0.28) |
| solar | `U/V/TS/T` (+ approvals received) | 0.95 (0.77–1.08) | 0.50 (0.46–0.66) | 0.35 (0.28–0.46) |
| solar | ALL statuses (incl. `P`, `L`) | 1.33 (1.14–1.72) | 1.09 (0.86–1.32) | 0.86 (0.57–1.12) |
| **wind** | `U/V/TS` | 0.32 (0.19–0.50) | 0.22 (0.12–0.43) | 0.17 (0.07–0.31) |
| wind | ALL statuses | 0.61 (0.39–0.95) | 0.59 (0.49–1.06) | 0.54 (0.32–0.82) |

*(n = 23–24 cells for solar, 14–20 for wind; ISOs pooled ONLY to establish the design's horizon
shape — see the rule-25 caveat in §4)*

Three readings, and they are the substance of this limb:

1. **The pipeline is a genuinely informative forward volume signal for solar over 1–3 years**,
   which was not obvious in advance. The full-pipeline basis lands at median 0.86–1.33 of
   realized build across the whole 1–3 year window.
2. **The status filter matters enormously and cannot be inherited from the thermal channel.**
   `_PLANNED_FIRM_STATUSES = {U, V, TS}` is calibrated to a firm thermal unit — an appropriate
   bar when the row becomes a dispatchable `Generator` with a heat rate. On solar it captures
   only 21–63 % of realized build, because solar's permits→COD compresses much faster than a
   CC's. Choosing the status set is therefore a **deliberate confirmed-vs-announced judgment**,
   not an implementation detail, and §3.4 draws it.
3. **The signal decays with horizon in exactly the shape the horizon test predicts.** At *h*=1 the
   full pipeline over-states (1.33 — `P`/`L` rows slip or die); by *h*=3 it under-states (0.86)
   because projects that will commission in *V+3* had not entered the sheet at *V*. Both
   directions are properties of the source data, observable without the model.

**Verdict: ADMISSIBLE, and bounded to the near term.** It passes the rule-13 test on both
clauses, it has an instrument (the utility's own Form 860 filing), it has a vintage, and it has a
measured horizon past which it must fall silent.

### 1.2 Candidate B — state clean-energy statutes beyond the modelled RPS — **ADMISSIBLE AS DATA; REFUSED AS A CHANNEL (rule 19)**

**What identifies it.** Statute text with dated targets. Substantially encoded already:
`config/capacity_market.py::STATE_RPS_FLOORS` carries a fully-derived, per-state,
load-weighted blend for each ISO, and MISO's block is unusually well-documented — MN
(2023 HF7 / Minn. Stat. §216B.1691), MI (2023 PA 235), IL (CEJA / 20 ILCS 3855), MO, MT, WI,
with the zone weights (West .1466, Plains .1385, Illinois .0676, Indiana .1340, East .2422,
South .2711) and the state splits inside each zone spelled out.

**Forward analogue.** Perfect — a statute has published knots to 2050 and regenerates for any
forward year from its own text.

**But the code comment states what the blend deliberately excludes, and that exclusion is
correct:** the **carbon-free / clean tiers** (MN 80/90/100 % 2030–2040, MI 100 %-clean-by-2040,
IL 100 %-clean-by-2050) are held out of the renewable-tier blend because they count nuclear and
hydro; folding them into the wind+solar RPS row would let existing nuclear satisfy the target and
crush the REC dual toward zero — precisely the failure `lp/rows.py::_build_rps_row`'s docstring
already warns about (CX-6a).

**Why this is nonetheless refused as a procurement channel.** A dated share obligation driving
procurement **is already a modelled phenomenon**: the annual RPS row, whose dual is the REC price,
which already feeds `apply_economic_new_entry` as `rps_shadow_price`. Building a second mechanism
that force-builds MW to satisfy the same obligation is the stacked-mechanism failure rule 19
forbids by name, and the enumeration duty ("before adding a floor/bridge, enumerate what already
floors the same class and replace or reconcile") lands squarely on it.

**What the analysis exposes instead, and it is the largest single finding in this lane.** The RPS
row is **one ISO-wide annual row**: `_build_rps_row` puts a `+1` on every wind and solar column
across every zone and every hour, with `rhs = rps_target × Σ(ISO-wide demand)`. MISO's target is
a *blend of state obligations*. So a Minnesota utility's binding 55 %-by-2035 requirement is
averaged against Arkansas's zero into a single 11 % ISO-wide row that is slack at a 16.9 %
modelled VRE share — and pays nothing. **The obligation is real, it is binding at its own spatial
grain, and the model dissolves it by aggregation.** Under rule 14 `[R-ACCURATE]` this is the
textbook "data defined on a different boundary than our zones" case, and the reconciliation is
already sitting in the repo: the per-state → per-zone mapping needed for a **zonal** RPS row is
the same derivation the blend's own comment block performs. That is a spatial-grain correction to
an existing mechanism with zero new tunables — not a procurement channel — and it is escalated in
§5.3, not designed here.

**Verdict: the driver is admissible; a new channel for it is not.**

### 1.3 Candidate C — utility IRP targets / approved preferred portfolios — **INADMISSIBLE in its plan form**

**What identifies it.** Per-utility PDF filings in state PUC dockets (in MISO: MN, MI, IL, MO, IA
IOUs). **Nothing is on disk** — `data/raw/` has no IRP datatype — and there is no national
machine-readable registry; this would be a full human-in-the-loop curation intake per utility per
docket, larger than the confirmed-retirement registry and refreshed on a 2–3 year filing cycle.

**Why it fails.** An IRP preferred portfolio is a **plan, not an instrument**. This repo has
already adjudicated exactly this class, by name, on the retirement side: *"Announced retirements
(EIA-860 planned dates, **IRP**/press announcements) stay with the economic screen, because under
current demand growth plants scheduled for retirement keep staying online"*
(`confirmed-retirement-plan-2026-07.md` §0). Admitting IRP portfolios as an exogenous additions
driver while excluding IRP announcements as an exogenous exit driver would be incoherent, and the
asymmetry would run in the direction that flatters the residual.

There is one narrow admissible sub-form: a **PUC order approving a specific procurement** with MW
and a dated in-service obligation (an approved RFP/CPCN). That is a `regulatory_order` instrument
in the confirmed-retirement vocabulary — and a project with an approved CPCN and a signed IA is,
in practice, already a row in Candidate A's sheet. It collapses into Candidate A with a far worse
data pipeline and no independent content.

**Verdict: INADMISSIBLE as a volume driver. Not worth its own channel even in its admissible
sub-form.**

### 1.4 Candidate D — corporate PPA demand — **INADMISSIBLE (fails reproducibility AND the DOF test)**

**What identifies it.** Nothing admissible. The usable volume series (BNEF, LevelTen PPA Price
Index, S&P) are **proprietary** — they cannot enter `data/raw/` as a re-queryable source and a
future session cannot reproduce them at a vintage, which fails rule 13's reproducibility clause
before the forward clause is even reached. CEBA's public deal tracker is announcement-grade,
deal-count-oriented and not resolved to ISO or to an EIA plant identity.

**Forward analogue.** None exists. No published forward corporate-procurement volume series
exists at ISO grain, so a forward number would be a modeller's assumption — a free parameter,
refused by rule 20 `[R-DOF]` ("a residual that can only be closed by a tuned value is an open
root-cause issue, not a parameter") and by rule 24 the moment it needed a `ScenarioConfig` home.

**And its realized half is already inside Candidate A**: a corporate PPA that is actually signed
produces an interconnection agreement and a proposed-generator row. So the channel does not lose
the phenomenon — it loses only the *unsigned* part, which is the part nobody can observe.

**Verdict: INADMISSIBLE. This is where the null bites (§5.4).**

### 1.5 Limb-1 summary

| candidate | data on disk | forward analogue | responds to change | instrument | horizon | verdict |
|---|---|---|---|---|---|---|
| **A** EIA-860 proposed pipeline | **yes** | exact | yes (to world, not to model) | Form 860 filing | *V+1…V+4*, measured | **ADMISSIBLE — recommended** |
| **B** state CES statutes | partly (`STATE_RPS_FLOORS`) | exact | via the LP row | statute | to 2050 | driver admissible; **channel REFUSED (rule 19)** |
| **C** utility IRP portfolios | no | weak (plan, not instrument) | lagged | none | 15–20 yr | **INADMISSIBLE** |
| **D** corporate PPA demand | no (proprietary) | none | n/a | none | n/a | **INADMISSIBLE** |

---

## 2. Limb 2 — where it enters the capacity-evolution loop

**Design: a VRE limb of STEP 4 (known additions). Not step 5. Not a new step.**

### 2.1 Why step 4, and why not a new step

Step 4 already *is* the exogenous, committed, data-identified additions step. `load_planned_additions`
skips wind and solar because `_map_fuel_type` returns `None` for them
(`data/fleet/eia860.py:301`, verified at head), on the stated premise that *"renewable capacity
growth is handled by the zonal `wind_cap` / `solar_cap` pools"* (docstring, `eia860.py:1932`).
**FFR-3V §4.3 proved that premise false**: `renewable_additions` (runner.py:1231–1234) is the only
writer of those pools, and its sole upstream is the economic screen plus the commissioning
pipeline. So the pools are not an independent channel — they are the economic screen's output
buffer, and the economic screen is a single point of failure for all VRE in every forecast.

**The gap is therefore a hole inside an existing step, not a missing step.** Minting step 4b for
it would create a second additions mechanism alongside step 4 and violate rule 19 in the very act
of fixing a rule-19-shaped problem. It would also break the symmetry that makes the design
auditable: **step 0 confirmed exits : step 4 confirmed additions** — same instrument discipline,
same vintage gate, same `superseded` audit trail, same forward story.

### 2.2 The mechanical seam (zero new plumbing)

The channel writes into `renewable_additions[zone][tech] += mw` — the identical dict that step
4.5's pipeline commissioning already writes VRE rows into
(`capacity_evolution/evolve.py:583–585`) and that the runner folds into `wind_cap` / `solar_cap`
at `runner.py:1231–1234`. Zone assignment reuses `assign_zone_by_coords` on the proposed plant's
EIA-860 lat/lon, exactly as `load_planned_additions` already does (`eia860.py:2029–2035`) — so
procured MW lands in the zone it is actually being built in, **not** in the single
`RENEWABLE_ZONE_ALLOCATION` bucket the economic screen forces every MW into (FFR-3V §4.4). That
is a siting improvement obtained for free, and it should be stated as an expected side-effect
rather than discovered later.

Ordering within the year: **before** step 4.5 and step 5, so the screen sees the procured MW as
part of the year's committed volume rather than competing with it.

### 2.3 Composition with the caps FFR-4A audited — the part that must not become a second ladder

Two rules, and the second is the single most likely implementation error.

**(a) Procured MW is NOT itself capped by the ladder or the queue caps.** For the same reason a
confirmed exit bypasses the reliability floor: the caps model *the queue's annual throughput*, and
a row that is already in the queue with an effective year **is** that throughput. Capping it would
count the same physical constraint twice and would let a cap silently delete a project that
verifiably exists.

**(b) Procured MW MUST be netted from the economic screen's budgets in the year it commissions.**
The real queue has one throughput and both channels draw on it. Without this, the model builds
the committed pipeline *and* a full economic ladder on top of it — a double-count of exactly the
kind FFR-4A was chartered to remove. The netting must be applied to `queue_budget_mw` and to
`per_tech_cap_gw`'s `group_remaining` initialisation in `new_entry.py:1183–1188`.

**(c) The interaction with FFR-5C (D-17), stated precisely, because the two lanes are running in
the same wave.** FFR-5C removes the pending-pipeline **stock** netting from the flow caps, on
FFR-4A's derivation that netting a stock from a GW/yr cap is a dimensional double-count that
imposes an unintended `D ≤ C/L` and kills the ratchet at `K = L`. **The procurement channel's
netting is different in kind and does not re-introduce that defect:** it nets the MW *commissioning
in that year* — a flow, in GW/yr — from a flow cap. Same units, no stock, no `C/L`, no ratchet
effect. The binding design constraint, stated so an implementer cannot get it wrong by accident:

> **The procurement channel nets the CURRENT YEAR's commissioning flow, never a cumulative
> pipeline stock.** A design that accumulates procured MW and nets the running total re-creates
> FFR-4A's defect under a new name.

The two are therefore compatible and independent; neither is a precondition for the other.

### 2.4 Composition with the other live mechanisms

* **`entry_vre_capacity_revenue`** (default OFF globally, **ARMED for MISO** as its forecast
  default since owner D-2′, 2026-08-04 — `iso_configs::_miso_config`; matrix row
  `entry_vre_capacity_revenue`, MISO cell `K`). No structural conflict: that gate changes the
  economic screen's *margin*, and the procurement channel bypasses the margin entirely.
  **But it creates an attribution hazard** — with both live, MISO solar MW can arrive by either
  path, and no future rule-19 enumeration can proceed if the ledger cannot tell them apart. Hence
  §3.5.
* **The RPS LP row.** Procured MW raises the VRE share, which relieves the constraint. In MISO the
  row is already slack, so the REC dual stays zero and nothing changes. In an ISO where the row
  binds, procured MW correctly lowers the REC dual and *reduces* economic entry — the two
  mechanisms compose through the LP, which is the right composition and needs no special-casing.
* **The reserve-margin backstop (step 6).** Procured VRE lands in the pools before the backstop
  computes `accredited_firm_capacity_mw`, so its accredited contribution correctly reduces the
  backstop's deficit. This is the desired direction and follows from the step-4 placement.
* **Double-count against the base fleet.** Guarded by the identical condition
  `load_planned_additions` already enforces: `Effective Year > operable_vintage_year(data_dir)`
  (`eia860.py:1992`). A unit already in the operable snapshot can never be re-added.

### 2.5 The registry surface (rule 24 `[R-REGISTRY]`)

The **entire** tunable surface a future implementation may create:

* **one** `ScenarioConfig` field — `vre_procurement_additions_enabled: bool = False` (GATED,
  default OFF, forecast-mode only, with its `mechanism-matrix.js` row minted in the same PR per
  rule 28(c)); and
* **one** already-registered data path — the active EIA-860 vintage directory, resolved through
  `config/paths.py` like every other on-disk input.

**No other knob.** No status-set override, no horizon scalar, no realization multiplier, no
per-ISO dict, no env var. The status set is a *code constant with a citation* in the same shape as
`_PLANNED_FIRM_STATUSES` (§3.4), not a config field — because a config field is a channel through
which a residual can be closed, which is exactly what this design must not provide.

---

## 3. Limb 3 — how it fails safe: the line between an announced-procurement INPUT and a measured-outcome PIN

The forbidden pole is rule 13's: *pinning a unit to its observed generation, or rescaling an input
so the model's output lands on the actuals.* The additions-side version is **"paste the actual
build in."** Five guards, each a mechanism rather than a discipline.

### 3.1 The instrument gate — what may be a row

A row exists only if it carries a public, dated artifact a third party can re-query: **an EIA-860
proposed-generator row at the run's own vintage**, whose instrument is the utility's own Form 860
filing. Nothing else.

**Explicitly and permanently excluded: any row keyed to a plant's observed COD from the operable
or retired sheets.** This is the line, and it is one line of code wide:

> The **proposed** sheet at vintage *V* is a *forward statement of intent, filed before the
> outcome*. The **operable** sheet is *the outcome*. A design that reads
> `eia860_generator_operable.parquet`'s `Operating Year` to decide what to build has pasted the
> answer key in, however it is dressed.

Both files sit in the same directory with near-identical schemas. An implementation must never
import the operable sheet into the procurement path — not for cross-checking, not for
"validation", not for a coverage statistic computed at run time. (The coverage statistics in §1.1
are a *design-time* measurement of the source data's properties, computed in a scratch script and
never in the solve path; that distinction is the whole difference and must be preserved.)

### 3.2 The information gate — when a row may be seen

`instrument_date ≤ the vintage cutoff`, implemented by **reusing the existing vintage machinery
rather than reimplementing it**: only the run's own active vintage directory is read
(`active_eia860_dir()`, resolved once), and only rows with
`Effective Year > operable_vintage_year(that dir)` qualify. A run pinned to vintage 2020 may never
open the 2021 sheet. This is the confirmed-retirement precedent's gate
(`confirmed-retirement-plan-2026-07.md` §5.1, "a row applies only when `instrument_date` ≤ the
vintage cutoff"), and the FH-1 leak fix already proved what happens when the guard is written
against a hardcoded constant instead of the active snapshot.

**Corollary, stated as the design working rather than failing:** a 2021–2025 hindcast at vintage
2020 sees **2.919 GW** of MISO all-status solar pipeline and **can never see the 18.649 GW that
was actually built**. Anyone who "fixes" that shortfall by widening the vintage has spent the
gate, and the run that results measures plumbing, not skill.

### 3.3 The horizon gate — how long a row may act

The pipeline is empty past *V+4–5* (§1.1's table). The channel must therefore **fall silent past
the data horizon and hand the whole job back to the economic screen** — the same sentence
`load_planned_additions`' docstring already carries (*"beyond the EIA-860 data horizon the economic
new-entry screen owns all additions"*), and the same construction as
`NONFOSSIL_ANNOUNCED_HORIZON_YEARS`.

**No extrapolation of the pipeline forward, ever.** An extrapolated queue — "assume the *V+4*
cohort repeats" — is a free parameter wearing a data costume, and it would be the exact
mechanism by which a 2026–2050 forecast's whole VRE build silently became a fitted growth
assumption.

### 3.4 The realization treatment — how much of a row counts (the judgment call, labelled as one)

Three options, with §1.1's measured consequences:

| option | measured solar coverage *h*=1/2/3 | new parameters | precedent |
|---|---|---|---|
| **(a)** `U/V/TS` at face value | 0.63 / 0.33 / 0.21 | **0** | `_PLANNED_FIRM_STATUSES` — the repo's already-adjudicated line |
| (b) all statuses at face value | 1.33 / 1.09 / 0.86 | 0 | none; admits `P` (no regulatory approvals initiated) |
| (c) all statuses × per-status realization rate | best available | ≥1 derived scalar per status | none |

**Recommendation: (a), and the reason is the precedent, not the fit.** The confirmed-vs-announced
line on the additions side has already been drawn in this repo, with a citation:
*"`P` (planned-with-permits) is deliberately excluded here — appropriate for the renewables
capacity-ramp aggregation, too speculative to enter the dispatch fleet as a firm thermal unit"*
(`eia860.py:1907–1913`). Option (b) admits exactly the rows that comment excludes. Option (c)
introduces a scalar whose most natural identification is *pipeline MW vs realized COD MW* — and
realized COD is the outcome §3.1 just forbade importing; even derived offline and frozen, it sits
closer to rule 13's forbidden side than anything else in this design.

**Note the direction of the choice.** Option (a) is the option that makes the model build **less**,
i.e. it makes the MISO residual **worse** than (b) or (c) would. Choosing it is rule 1
`[R-STRUCT]` operating correctly: the admissible construction is preferred over the better-fitting
one, and the remaining residual stays visible as an open root cause rather than being absorbed.

If (c) is ever wanted, its preconditions are: derived per-status from the source data alone,
frozen under rule 23 `[R-FROZEN-DERIVE]` so it re-derives only when EIA-860 updates, registered
under rule 24, and scored **leave-one-year-out** before promotion per rule 22.

### 3.5 The attribution requirement

Every MW the channel injects carries `source: "procured"` in the evolution ledger with its
`plant_id`, mirroring step 4's `source: "planned"` and step 5's `source: "economic"`
(`evolve.py:546–558`). A channel whose MW cannot be separated from the economic screen's MW is
unauditable: no D-2 attribution can enumerate it, no rule-19 reconciliation can be performed
against it, and no future session can tell whether a build came from the queue or from a margin.
**This is a hard requirement of the design, not a nice-to-have** — it is what keeps the channel
from becoming an unattributable source of MW that later lanes tune around.

### 3.6 One precondition that is NOT satisfiable by this design

**FFR-3V §6.1 must be closed before this channel is armed in the hindcast lane.** A capacity
hindcast is `mode="forecast"` + `hindcast=True`, so `load_renewable_profiles`'
`is_backcast = config.mode == "backcast"` gate (`renewables.py:2327`) falls through to the
canonical constant: MISO's solar pool seeds at **7,000 MW against 2,056 MW actual at vintage
2020**, 3.4× over. Injecting vintage-gated procured MW on top of a pool that already contains
post-vintage capacity double-counts by construction, and would do so *invisibly* — the totals
would look plausible while the mechanism was wrong. Stated as a **blocking precondition on the
hindcast lane specifically**, not as a caveat. Plain 2026+ forecasts are unaffected.

---

## 4. Limb 4 — per-ISO scope (rule 25 `[R-ISO-SCOPE]`)

**MISO evidence charters MISO and nothing else.** This section states data availability so a
later per-ISO decision starts informed; it arms nothing and it fills no matrix cell anywhere.

Measured inventory at vintage 2024 (all-status proposed, `Effective Year > 2024`):

| ISO | solar GW (rows) | wind GW (rows) | data available | measured coverage caveat | status |
|---|---|---|---|---|---|
| **MISO** | **14.09** (165) | 2.19 (11) | yes | h=3 full-pipeline coverage 0.55 at v2022 — MISO's build outran even its own full queue | **the chartered candidate — still its own later decision** |
| ERCOT | 27.01 (131) | 3.23 (13) | yes | largest pipeline of the six; but ERCOT is energy-only and its VRE build is the most merchant-driven, so the channel's *rationale* is weakest exactly where its data is richest | not armed — own decision |
| PJM | 11.53 (151) | 3.51 (8) | yes | h=1 U/V/TS coverage as low as 0.13 (v2020) — its committed-status cohort is unusually thin | not armed — own decision |
| CAISO | 5.58 (78) | 0.24 (4) | yes | wind pipeline is effectively empty; a solar-only channel would be the honest scope | not armed — own decision |
| NYISO | 2.63 (51) | 2.13 (6) | yes | small denominators make its coverage statistics noisy (h=1 cells range 0.13–0.81) | not armed — own decision |
| NEISO | 0.56 (15) | 0.18 (2) | yes | **weakest of the six** — actual builds run 2–3× the whole pipeline at h≥2 (cov 0.68/0.57); much of NEISO's solar is distributed/behind-meter and never appears in the proposed sheet at all | not armed — own decision |

Three rule-25 cautions for whoever takes an ISO's arming decision:

1. **The pooled coverage statistics in §1.1 are a design-time horizon argument and may NOT be
   transferred into any ISO's parameterization.** A per-ISO channel derives its own numbers from
   its own market's data, or derives none at all (option (a) needs none).
2. **The pipeline → ISO mapping runs through `BA_CODE_TO_ISO` on the plant's reported balancing
   authority.** CAISO / NYISO / NEISO map through a single BA cleanly; MISO and PJM depend on
   per-plant BA reporting quality, which each ISO's own decision should check before arming.
3. **NEISO's behind-meter share is a structural mismatch, not a data gap.** A channel that only
   sees utility-scale proposed rows will systematically under-represent an ISO whose growth is
   distributed. That is a reason for a *different* answer in NEISO, not a reason to widen the
   channel's status set.

---

## 5. Limb 5 — the rule-13 admissibility verdict

### 5.1 The recommended design, argued against rule 13's test

**The design:** a default-OFF, forecast-mode-only VRE limb of step 4's known-additions channel,
reading the run's own EIA-860 vintage's proposed-generator sheet at construction-committed status
(`U/V/TS`), writing zone-assigned MW into `renewable_additions`, netting its current-year
commissioning flow from the economic screen's budgets, falling silent past the data horizon, and
tagging every MW `source: "procured"`.

**Could this same quantity be produced for a forward year from forward drivers?** Yes, and by
exactly the construction that already produces it for thermal. Every EIA-860 vintage carries a
proposed sheet; the quantity for forecast year *Y* is the rows in the run's own vintage with
`Effective Year = Y` and a committed status. No model output, no residual, no actuals enter the
computation at any point.

**Would it respond to changed conditions?** Yes, on the world's conditions — rows enter and leave,
statuses advance and regress, effective years slip, and the whole set turns over between vintages
(MISO's all-status solar pipeline moves 2.92 → 5.18 → 10.29 → 11.92 → 14.09 GW across vintages
2020→2024). It does **not** respond to the model's own prices, which is the defining property of
an exogenous committed-decision channel and precisely why §3.3's horizon gate is what keeps it
honest: past the queue, the price-responsive screen owns everything.

**Is it a measured OUTCOME fed back in?** No, and §3.1 is the guard that keeps it so. The proposed
sheet is filed before the outcome; the operable sheet is the outcome; the design reads only the
former and is forbidden the latter. It is the additions-side twin of the confirmed-retirement
registry, whose admissibility argument (`confirmed-retirement-plan-2026-07.md` §2.3) this
inherits point for point.

**Does it introduce a fitted quantity?** No. Zero free parameters (§2.5, §3.4 option (a)). The
status set is a cited code constant; the horizon is the data's own; the vintage is the run's own.

**Verdict: ADMISSIBLE.**

### 5.2 What it does NOT do, pre-registered

**It does not close MISO's 18.649 GW gap, and no version of it can.** At §1.1's measured coverage,
a `U/V/TS` channel delivers on the order of one-fifth of realized 3-year build, and the
vintage-2020 pipeline a 2021–2025 hindcast is *allowed to see* totals 2.919 GW all-status /
1.034 GW committed against 18.649 GW actual (FFR-3V §4.3 measured the same 1.034 GW
independently). Pre-registered here so it cannot later be read as a failure of the mechanism:
**a correctly-gated near-term channel is arithmetically incapable of reproducing a five-year build
from a two-year queue, and that is the information gate working.** Any session that reaches a
better MISO number by relaxing §3.1–§3.4 has spent the guard, not improved the model.

### 5.3 What is REFUSED, and where the long-run half actually belongs

The long-run half of D-16's gap must **not** be closed by this or any procurement channel
(§1.2, rule 19). It belongs inside the mechanism that already owns the phenomenon. Two findings
are escalated, neither designed nor landed here:

* **E-1 — the RPS row's spatial grain.** `_build_rps_row` builds one ISO-wide annual row against a
  load-weighted blend of state obligations, dissolving binding state requirements into a slack
  ISO-wide average. The per-state → per-zone reconciliation needed for a zonal row is already
  derived inside `STATE_RPS_FLOORS["MISO"]`'s own comment block. Zero new tunables; a spatial-grain
  correction under rule 14, not a new mechanism. **This is the largest single finding in this lane
  and it deserves its own scoping decision.**
* **E-2 — the clean/carbon-free tiers are represented nowhere.** They are correctly excluded from
  the *renewable* row (they would be satisfied by existing nuclear and would crush the REC dual),
  but the consequence is that MN's, MI's and IL's strongest statutory procurement drivers are
  invisible to the model entirely. Whether a second, nuclear-counting clean-energy row is the
  right answer — or whether it would merely be slack for the same aggregation reason as E-1 — is
  an open question this lane did not settle. It should be settled *with* E-1, not separately.

### 5.4 The null inside the design

**A part of D-16's gap has no admissible representation at all, and this lane's honest answer is
to disclose it rather than invent a driver for it.** Corporate PPA procurement (§1.4) has no
public, reproducible, ISO-resolved volume series and no forward analogue; the beyond-horizon
portion of utility procurement (§1.3) exists only as plans, which this repo has already adjudicated
as announcement-grade on the retirement side. Together they are a real share of MISO's 18.649 GW
and they are not recoverable by any construction that survives rule 13.

**The right disposition is a disclosed limitation with a named size**, not a channel. The size is
measurable from artifacts already committed — realized COD minus the vintage-gated committed
pipeline, per ISO-year — and computing it is a cheap follow-up this lane recommends but does not
perform.

---

## 6. What I did NOT decide

Stated explicitly, because the design above is additive only where it says so.

* **I did not open the implementation.** No code, no schema, no `ScenarioConfig` field, no matrix
  cell. §7 is a proposed card, not a charter.
* **I did not propose any parameter as a number.** §1.1's coverage medians are measurements of the
  *source data's* properties, presented to decide the design's horizon and status-set questions.
  They are not proposed as multipliers, they must not become any, and under rule 25 they must not
  cross into any ISO's parameterization.
* **I did not run a solve, score anything, or touch an out-of-training year.** Nothing on any
  dashboard changed; rule 15 does not apply (no run was produced).
* **I did not settle E-1 / E-2 (§5.3).** The zonal-RPS and clean-tier questions are stated as
  findings with their evidence and escalated. Designing them was outside D-16(a)'s charter, and
  they are large enough to deserve their own decision rather than a subsection here.
* **I did not size the §5.4 residual.** It is computable from committed artifacts and is
  recommended as a cheap follow-up; it was not this lane's charter and no number for it appears
  above.
* **I did not adjudicate the confirmed-vs-announced status line for any ISO but as a general
  design recommendation.** §3.4 recommends option (a) with its precedent; an arming decision for a
  specific ISO may reach a different conclusion on that ISO's own evidence, and §4 says so.
* **I did not verify FFR-5C's landed shape.** §2.3(c) is written against FFR-4A's derivation and
  D-17's charter text as signed. Whichever of FFR-5B/FFR-5C lands second re-checks the
  interaction — and the mechanism matrix, per the O.3 discipline.
* **Rule 28 discharge: NO matrix cell was changed.** A design lane adjudicates nothing, tests
  nothing and arms nothing, so no cell moved and no row was minted. The row for
  `vre_procurement_additions_enabled` is minted by the implementation PR that creates the field,
  per duty 28(c) — recorded here so that duty is not lost.
* **Rule 24 discharge: nothing to register.** No value was landed. §2.5 names the *entire*
  prospective surface (one gate flag, one existing data path) so that a future implementation
  cannot expand it without the expansion being visible against this document.

---

## 7. PROPOSED OWNER CARD — for the manager to put

```
### CARD D-18 — Implement the near-term VRE procurement channel?

**Measured (FFR-5B, docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md).** D-16's gap
splits in two, and only one half has an admissible mechanism. (i) THE NEAR-TERM HALF IS A REAL
MISSING MECHANISM: step 4's known-additions channel skips wind and solar (`_map_fuel_type`
returns None) on the premise that "the zonal pools handle renewable growth" — a premise FFR-3V
§4.3 refuted, since the pools' ONLY writer is the economic screen. So the merchant screen is a
single point of failure for all VRE in every forecast. The admissible input is the EIA-860
proposed-generator pipeline at the run's own vintage — already on disk, already consumed for
thermal, with the vintage information gate already built (`active_eia860_dir` +
`Effective Year > operable_vintage_year`). Measured across 6 ISOs × 4 vintages, the
construction-committed cohort covers a median 0.63 / 0.33 / 0.21 of realized solar COD at
horizons 1 / 2 / 3 years, and the pipeline is empty past V+4. (ii) THE LONG-RUN HALF IS REFUSED
A CHANNEL by rule 19: a dated share obligation driving procurement is already the RPS LP row's
phenomenon; what is wrong is that row's SPATIAL GRAIN (one ISO-wide row against a load-weighted
blend, so a binding Minnesota 55%-by-2035 statute is diluted to slackness by Arkansas's zero) —
a rule-14 correction inside an existing mechanism, escalated as FFR-5B E-1/E-2, NOT this card.
(iii) A RESIDUAL — corporate PPAs, beyond-horizon procurement — has NO admissible representation
at all and FFR-5B recommends disclosing it rather than inventing a driver.

**Recommendation — (a) CHARTER THE IMPLEMENTATION LANE for the near-term channel ONLY, gated
default-OFF, MISO-scoped.** One `ScenarioConfig` field
(`vre_procurement_additions_enabled: bool = False`) plus the existing EIA-860 vintage path —
ZERO other knobs, zero free parameters, with its matrix row in the same PR (rule 28c) and a
paired arm. Construction-committed statuses (U/V/TS) only, at face value: the option that builds
LESS and leaves the residual visible, chosen on the repo's own already-adjudicated
confirmed-vs-announced precedent rather than on fit. The shipped path stays byte-identical until
armed; arming anywhere, including MISO, is a separate decision (rule 25).

PRE-REGISTERED AND CARRIED, so the lane cannot be misread: **THIS DOES NOT CLOSE MISO's 18.649 GW
GAP.** A vintage-2020 hindcast is ALLOWED to see 1.034 GW of committed MISO solar pipeline against
18.649 GW actual — a correctly-gated near-term channel is arithmetically incapable of reproducing
a five-year build from a two-year queue, and that is the information gate WORKING. Anyone who
reaches a better MISO number by widening the status set, the vintage or the horizon has spent the
guard. BLOCKING PRECONDITION for the hindcast lane only: FFR-3V §6.1 (hindcast renewable pools
seed from the canonical constant, MISO solar 7,000 MW vs 2,056 MW actual at vintage 2020) must
close first, or injected MW double-counts invisibly. Plain 2026+ forecasts are unaffected.

**Option (b), widen the status set until MISO's build lands — I think this is wrong, and it is
the option the evidence will keep suggesting.** The all-status pipeline scores far better in
aggregate (median coverage 1.33 / 1.09 / 0.86 vs 0.63 / 0.33 / 0.21). Cost: it admits `P` rows
— "planned, regulatory approvals not initiated" — which is announcement-grade, the exact tier
this repo already excluded by name on the retirement side, and `eia860.py:1907` already excludes
by name on the additions side. Buying a better residual with a lower evidentiary bar is the
fitted-input failure rule 1 forbids, arriving as a status filter instead of an adder. If the
owner wants the better-calibrated basis anyway, it should come as an explicit, cited,
frozen-derived realization treatment (FFR-5B §3.4 option (c)) scored leave-one-year-out — never
as a quietly widened filter.

**Option (c), leave it as a disclosed limitation — I think this is wrong.** Cost: the economic
screen remains a single point of failure for ALL VRE in EVERY forecast in every ISO, with a
committed, publicly-filed, already-intaken pipeline sitting unread on disk next to the thermal
channel that reads it. Rule 14 `[R-ACCURATE]` points the other way: the accurate data is
available and the estimate (the merchant screen alone) is silently compensating for its absence.

**Sign-off D-18:** ☐ (a) charter near-term channel, gated default-OFF, MISO-scoped
☐ (b) widen the status basis  ☐ (c) disclosed limitation  ☐ other: ____________
owner: ________  date: ____
```

---

## 8. Reproduction

Design-time measurements only; all read committed on-disk data and shipped code, none touches the
solve path (§3.1's distinction). Scratch scripts, session scratchpad:

* `probe2.py` — proposed-pipeline GW by status × vintage × ISO × tech (§1.1 horizon table,
  §4 inventory).
* `probe3.py` / `probe4.py` — the forward-skill census: pipeline at vintage *V* vs realized COD in
  *V+1…V+h*, per cell and pooled (§1.1 coverage table).
* `probe5.py` — the vintage-2024 effective-year decomposition (§1.1).

Sources: `data/raw/eia-860/vintage_{2018..2024}/eia860_generator_proposed.parquet` +
`eia860_plant.parquet`; `data/raw/eia-860/eia860_generator_operable.parquet` (canonical, max COD
2025) for the realized side; ISO mapping via `market_sim.data.fleet.eia860.BA_CODE_TO_ISO`.
