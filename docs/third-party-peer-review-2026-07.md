# Third-Party Peer Review — Market Simulation Model

**Date:** 2026-07-19 · **Reviewer stance:** independent third-party referee; no stake in the
model's calibration outcomes. **Scope:** design legitimacy and validity of the full
`src/market_sim` model versus the commercial and academic state of practice (PLEXOS, Aurora,
PROMOD, GridView, EnCompass, UPLAN, Dayzer, SERVM; GenX, ReEDS, US-REGEN, Switch, PyPSA,
TEMOA, OSeMOSYS, Cambium); classification of the model's role (capacity expansion vs
production cost vs hybrid); best-fit use cases; and an independent inventory of magic-number /
curve-fitting risk.

**Evidence base.** Direct review of `model-methodology-spec.md` (1,199 lines),
`docs/model-legitimacy-audit-2026-07.md` (the project's own 2026-07-02 internal audit),
CLAUDE.md rules 1–27, the keeper registry and verdicts (`frontend/data/backcast/keepers.json`,
`status.js`, registry sidecars), `docs/out-of-sample-results-2026-07.md`, the holdout-policy and
calibration-complete governance records, and targeted HEAD verification of every fitted-parameter
finding cited below (file:line as of commit `37d3923`, 2026-07-18). External model profiles were
compiled from vendor documentation, regulator filings, and peer-reviewed sources (cited inline).
The review is bounded by what is in the repository: it does not re-run solves, and external
comparisons rest on public documentation rather than hands-on benchmarking of the commercial
tools.

---

## 1. Executive summary

This is a **hybrid model with a production-cost center of gravity**: a full-8760 hourly, zonal,
pure-LP dispatch simulator of commercial-PCM lineage, wrapped in a myopic one-pass annual
capacity-evolution loop of the Aurora-LTCE class rather than the GenX/ReEDS co-optimized-CEM
class. Its dispatch/price-formation half is unusually complete for a non-commercial tool —
reserve co-optimization, ORDC/RCPF scarcity overlays, per-plant tranche offer curves, measured
seam ladders, RPS-as-constraint with REC-price duals — and sits comfortably inside the envelope
of commercial practice (closest to the LP-relaxation/heuristic-commitment tier that PLEXOS
"Rounded Relaxation," Aurora, and SERVM occupy, not the MIP-SCUC tier). Its capacity-evolution
half is structurally below academic CEM state of practice (no foresight, no co-optimized
builds/retirements/transmission, screen-based entry/exit outside the LP) but is a defensible
merchant-behavior representation with unusually careful market-design detail (per-ISO published
accreditation bases, sloped capacity demand curves, CCS retrofit-or-retire screens).

Three findings dominate the validity assessment:

1. **The calibration-governance regime is materially stricter than commercial or academic
   norms** — a written fitted-vs-structural taxonomy, DOF-ledger attestations, forced-energy
   budgets, mechanism-attribution diagnostics, frozen derive scripts, and a three-tier
   train/validation/locked-test holdout design. No surveyed commercial vendor or academic group
   publishes anything comparable. The project also finds and reverses its own violations on the
   record (the CAISO CT-forcing scrub, the ERCOT phantom-outage withdrawal), which is the
   behavioral signature of governance that actually operates.

2. **Forecast skill is nevertheless asserted, not yet demonstrated.** Despite the holdout
   architecture, **no out-of-training year has ever been solved**: the physical record (no
   holdout bench files, bundles, or registry entries; the G-19 execution hold reaffirmed through
   2026-07-13) shows the validation tiers exist on paper only, and one governance record
   (`calibration-complete.json`'s NEISO `locked_test_scored_on` note) asserts a locked-test score
   that the artifact record contradicts. In-sample skill is real and quantified (§5); out-of-sample
   skill is currently zero measured data points, and the one adverse proxy that exists (the
   2026-06-16 ERCOT statistical-mode A/B, failures doubling) was never repeated.

3. **The residual-fitted parameter surface is large, known, and honestly labeled, but its
   identification is thin.** The project's own census counts ~290 residual-identified scalars
   (dominated by per-ISO offer-band multipliers and coal-passthrough sigmoids), selected over
   ≥400 solves scored on the same three years. The project's own D-8 stability study shows the
   weakness concretely: coal-sigmoid asymptotes each pinned by a single gas regime, reliability-
   floor limbs whose temperature correlation flips sign out-of-training, and a CAISO CT floor
   that nearly equals the class it floors. Offer-curve tuning is an accepted commercial practice
   (PROMOD hurdle rates, SERVM bid adders are industry analogues) — the issue is not that tuning
   exists but that three years of data cannot identify this many parameters, and the designed
   remedy (holdout scoring) has not been executed.

**Bottom line:** as a calibrated in-sample simulator of six US ISO markets, the model is at or
above the demonstrated commercial grade on mean price, price shape, volume mix, and CO2 for the
ISOs its own rubric marks CALIBRATED (PJM) or CALIBRATED-WITH-CAVEATS (NYISO, NEISO), and it is
more transparent about its failures (ERCOT, CAISO, MISO marked NOT-YET) than any commercial
comparator. As a 2026–2050 forecasting tool — its stated mission — it is a well-architected
system whose central validity claim awaits the already-designed but never-executed out-of-sample
program. The distance between those two sentences is the model's principal open risk.

---

## 2. What the model is — role classification

### 2.1 Architecture (verified against spec and code)

- **Dispatch:** one ISO-agnostic LP per ISO-year, 8,760 hours, zonal (3–8 zones per ISO plus
  import nodes), HiGHS via direct CSC matrices. Variables `P/W/S/Chg/Dis/SOC/Flow/Slack/Dump`;
  prices are the energy-balance duals (spec §1.1–1.3). Renewables are decision variables with
  CF-bounded upper limits, not netted load. Storage is SOC-linked with a cyclic annual boundary
  (optional daily-cycling cap); transmission is pipe-and-bubble with interface groups and
  measured seam ladders.
- **Commitment:** pure LP, no MIP. P0 (base-cost) discovers run patterns; P1 (bid-cost with
  amortized startup markup) sets prices and is the scored production path; the legacy P2
  economic-commitment screen is archived behind `--enable-legacy-p2` (spec §1.6). Two P1-native
  commitment bridges (CAISO RA must-offer; gated ERCOT gas bridge) inject min-gen floors detected
  from the model's own P0 pattern.
- **Scarcity:** post-solve ORDC adder (ERCOT) and RCPF overlay (NYISO) on top of LP duals;
  reserve co-optimization with reserve duals feeding the capacity screens.
- **Capacity evolution:** myopic one-pass annual loop (spec §5.1): confirmed exits (registry of
  binding public instruments) → announced retirements (fossil deferred to economics) → CCS
  retrofit-or-retire screen → economic retirement on attainable inframarginal margin vs
  going-forward cost → known additions → economic new entry → optional reserve-margin backstop →
  dispatch with RPS as an LP row. Capacity-market revenue rides per-ISO published accreditation
  bases and (gated) sloped VRR demand curves.
- **Data:** EIA-860/923/930, EPA CAMPD/CEMS, eGRID, ISO disclosures, through a schema-validated
  raw→clean contract; backcast mode adds measured overlays (outage windows, delivered fuel,
  same-year CEMS rates) that are explicitly barred from forecast mode.

### 2.2 Role: hybrid, with an asymmetry the label hides

The honest classification is **"production-cost model with an endogenous fleet-evolution
wrapper,"** not "capacity-expansion model with operational detail":

- The dispatch half is where the engineering depth, the calibration evidence, and the governance
  attention all live. It is the part scored against history.
- The evolution half decides builds/retirements by *screens over the prior year's prices* —
  architecturally the same family as Aurora's LTCE iterative-NPV logic and ReEDS's
  recursive-dynamic mode, but with entry/exit decided outside any optimization. It has never been
  hindcast (no analogue of NREL's Cole & Vincent 2019 ReEDS builds-vs-actuals study exists for
  it), so its skill is currently untested in both directions.

This asymmetry matters for use-case fit (§7): conclusions that lean on the dispatch half inherit
measured in-sample skill; conclusions that lean on the evolution half (2030s–2040s fleet
composition, retirement timing, CCS uptake) currently inherit only design plausibility.

---

## 3. Comparison with commercial production-cost / market simulators

Profiles compiled from vendor documentation, regulator filings, and independent reports
(sources at end of section).

| Dimension | This model | Commercial norm |
|---|---|---|
| Formulation | Pure LP, 8760 chronological | MIP SCUC now the norm for nodal tools (PLEXOS ST, EnCompass, PSO, current PROMOD/GridView); LP-relaxation/heuristic tier has deep precedent (PLEXOS RR was the regulator-approved SEM standard until 2021; Aurora stack logic; SERVM lookahead heuristic) |
| Network | Zonal, 3–8 zones/ISO, pipe-and-bubble + interface groups | Nodal bus-level for PROMOD/GridView/Dayzer/UPLAN (thousands of flowgates); zonal for Aurora/SERVM |
| Unit commitment | None (P0/P1 startup-amortization heuristic + gated min-gen bridges) | Full SCUC with min up/down, start states (MIP tier); heuristic commitment (Aurora, SERVM, historical GridView) |
| Price formation | LP duals + post-solve ORDC/RCPF overlays | Marginal-cost duals post-commitment everywhere; uplift only as explicit configurable adders (PLEXOS Korean/SEM uplift); no commercial tool claims ELMP/fast-start-pricing replication |
| Scarcity pricing | ERCOT ORDC + NYISO RCPF overlays; ECRS design variants | Rare: SERVM is the only surveyed tool natively simulating ORDC/EEA scarcity formation; SEM PLEXOS runs with no scarcity pricing; static shortage bands otherwise |
| AS co-optimization | In-LP reserve co-opt; reserve duals feed retirement/entry screens | Standard in PLEXOS/UPLAN/EnCompass/PSO; targets in Aurora |
| Capacity expansion | Myopic annual screens (see §4) | Integrated co-optimized MIP (PLEXOS LT Plan, EnCompass) / iterative NPV (Aurora LTCE) / none (PROMOD pairs with EGEAS) |
| Calibration practice | Backcast on 3 years, machine-scored rubric, fitted parameters registered per-run | Backcast calibration is standard and regulator-endorsed (NERA SEM PLEXOS backcasts; SPP ITP PROMOD benchmark chapters; MISO hurdle-rate calibration to observed flows; Dayzer LMP-validation graphs; SERVM price-duration calibration) |

**Where it stands.** The pure-LP commitment choice is defensible on the record: the SEM
regulator ran its official PLEXOS model on LP-relaxation commitment for over a decade, and this
model's own probe history (the ercot27 finding that an AS-aware commitment pass added broad
price elevation with no scarcity signal) is an honest empirical basis for preferring P1 —
although NERA's opposite finding for the SEM (MIP commitment aligned prices better and reduced
uplift needs; SEM-25-010 §4.2) means the LP-only choice should be treated as ISO- and
regime-specific, not settled. The genuine capability gaps versus the commercial nodal tier are
**network resolution** (no congestion/basis/FTR work is possible at 3–8 zones, and the model
does not pretend otherwise) and **uplift/non-convex price formation** (absent, as in nearly all
commercial tools). The scarcity-pricing machinery is *ahead* of most commercial tools — only
SERVM is comparable — and the fitted-parameter discipline (rules 24–26: every tunable in
`ScenarioConfig`/`constants.py` + `run_config.json`, no env-var knobs, no cross-ISO leakage) is
stricter than the commercial norm, where fitted inter-regional hurdle rates and bid adders are
accepted devices that vendors do not even enumerate publicly.

**Calibration transparency comparison.** The only commercial backcast published at comparable
grain is the SEM PLEXOS series (NERA 2025: +0.09 €/MWh average price error over 2020–2023, with
settings explicitly iterated against the backcast). Both NERA ("a seemingly near perfect
historical alignment could be somewhat coincidental") and Astrapé ("the intent was not to force
the model to replicate history") state the anti-overfitting position this repo codifies as rules
1/13. This model's dashboard — per-criterion pass/fail with magnitudes, rejected probes retained,
NOT-YET verdicts published — has no commercial equivalent; vendors publish successes.

*Commercial-model sources:* SEM-25-010 / SEM-08-062 (semcommittee.com); PLEXOS LT Plan
documentation (portal.energyexemplar.com); Idaho Power AURORA Overview and PSE 2023 IRP App. G;
ICC docket P2014-0494 Exh. 8.2N and MISO PSC hurdle-rate methodology (PROMOD); Brattle 2017
CAISO TPP modeling review (GridView/PSO commitment tiers); Yes Energy/Anchor EnCompass
documentation; EIA STEO model documentation (UPLAN); CES Dayzer brochure; 2020 ERCOT Reserve
Margin Study (SERVM ORDC formulation) and Brattle 2018 EORM study.

---

## 4. Comparison with academic / open capacity-expansion models

| Dimension | This model | GenX / ReEDS / US-REGEN / Switch / PyPSA norm |
|---|---|---|
| Expansion mechanics | Screens outside the LP; myopic; one pass | Co-optimized build/retire (all); + transmission expansion (GenX, ReEDS, Switch, PyPSA); intertemporal foresight (Switch, US-REGEN, TEMOA; optional in GenX/ReEDS) |
| Temporal resolution | Always 8760 chronological | 17 time-slices → 33 representative days (ReEDS); representative hours (US-REGEN); configurable 8760 (GenX, PyPSA) |
| Operational fidelity | Per-plant tranches, reserves, scarcity, measured seams | Clustered/linearized UC at best; no ORDC, no AS revenue stacks, no offer curves |
| Hourly price credibility | Design goal; scored vs actuals per ISO | Explicit non-goal: NREL interposes a PCM (Cambium/PLEXOS) and decomposes energy vs capacity marginal cost rather than trusting CEM duals |
| Policy layer | IRA per-credit expiries, 45Q windows, RPS dual = REC price, cap-and-trade resolver, CES premium | ReEDS is the IRA reference; RPS-as-constraint-with-dual is the standard CEM construction — this model is at or above CEM practice in mechanism coverage |
| Validation practice | 3-year per-ISO price/volume/CO2 backcast + designed holdout tiers | Intercomparison and transparency, not calibration: EMF 32; the 2024/25 four-model open-CEM harmonization (<1% cost spread once inputs were harmonized); exactly one institutional hindcast (Cole & Vincent 2019, ReEDS builds vs actuals — quantities, not prices); one open price hindcast (PyPSA-Eur 2020–24 retrospective, ~21% weekly SMAPE, arXiv:2606.16486) |

**Where it stands.** Operationally the model exceeds every surveyed CEM; structurally its
expansion half is below CEM state of practice. Myopia is a defensible representation of merchant
behavior (and ReEDS's default mode is also recursive-dynamic), but myopic evolution is known to
under-build long-lead and storage assets relative to foresighted runs, and deciding entry/exit
in screens rather than an optimization forgoes the internal consistency (builds consistent with
the prices they will create) that defines the CEM class. The model is unusual — arguably
distinctive — in refusing the standard CEM→PCM soft-linking divide (NREL's CEPCoLT/Cambium
pattern): it embeds the PCM-grade 8760 LP *inside* the annual evolution loop, i.e. Cambium's
pipeline collapsed into one code base. The cost of that choice is that no external reference
implementation exists for its evolution half, so validation falls entirely on its own (not yet
executed) hindcast program. Notably, the single published open-model price hindcast (PyPSA-Eur's
2022-crisis retrospective) independently converged on this model's backcast methodology —
measured fuel prices, outages, and must-run structure are required to approach observed prices —
which corroborates the design of the backcast overlay system (and its honest classification as
backcast-only inputs).

---

## 5. Demonstrated accuracy — what the record actually supports

From `frontend/data/backcast/status.js` (rubric v2.x, machine-scored) for the six current
keepers, train years 2023–2025, RT basis:

| ISO | Determination | C3a mean LMP error by year | C3b shape NRMSE | C3c scarcity-tail capture (>$200–300/h) | C5a CO2 |
|---|---|---|---|---|---|
| PJM | **CALIBRATED** | +4.8% / −4.4% / −9.1% | 0.17 / 0.14 / 0.16 | 7v6 / 9v18 / 40v59 h (pass) | −1.8/−3.2/+2.9% |
| NYISO | CALIBRATED-W-CAVEATS | +3.1% / −7.0% / −8.1% | 0.15 / 0.20 / 0.17 | 28v10 / 3v12 / 25v42 h (caveats) | +3.5/+2.8/+8.3% |
| NEISO | CALIBRATED-W-CAVEATS | −3.1% / −0.3% / +6.0% | 0.13 / 0.18 / 0.13 | 0v15 / 0v8 / 0v20 h (misses tail) | −2.8/−2.4/+4.3% |
| ERCOT | **NOT-YET** | −21.8% / +2.1% / −3.4% | 0.45 / 0.30 / 0.09 | 58v181 / 22v53 / 0v31 h | +2.5/+0.5/+1.3% |
| CAISO | **NOT-YET** | +6.2% / +7.3% / +11.6% | 0.09 / 0.12 / 0.15 | 20v47 / 0v35 / 0v8 h | −10 to −14% (fail) |
| MISO | **NOT-YET** | −2.5% / −8.9% / −15.4% | 0.08 / 0.14 / 0.20 | 0v30 / 6v37 / 0v88 h | −4.5/−3.6/+1.1% |

Context anchors the repo's own benchmark memo assembles (and which this review verified as
fairly characterized): the SEM regulator's criterion for its official PLEXOS model is ±5%
aggregate over 3–5 years; NYISO's accepted GE MAPS benchmark ran −2% to −17% zonal; market
monitors' competitive re-simulations sit 0–4% from actuals; PyPSA-Eur's academic hindcast runs
20–26% weekly SMAPE. Against those anchors the PJM/NYISO/NEISO mean-price and shape results are
genuinely commercial-grade, and no surveyed tool publishes scarcity-tail-hour accuracy at all —
this rubric scores it anyway, which is why three ISOs carry honest NOT-YET verdicts driven
substantially by tail formation.

Three caveats an outside reader must attach:

1. **All of this is in-sample.** These are the same three years the ~290 fitted scalars were
   selected on, over a ≥400-solve lineage with a purpose-built Jacobian joint-move optimizer
   (`scripts/derive_offer_curve_jacobian.py`). The internal audit's own conclusion — "forecast
   skill is asserted, not measured" — remains true at HEAD (§6.3).
2. **The scored surface is partially fed by measured realizations.** The audit's leakage
   inventory (L1–L8) stands: renewable CF upper bounds from delivered EIA-930 output where no
   potential series exists, per-year measured nuclear monthly CF, hydro monthly budgets, the
   measured CHP export floor, NYISO's interchange reconciliation band. Each has a defensibility
   argument (and PLEXOS/Aurora boundary-flow practice is comparable), but jointly they mean
   gas/coal/CT are the classes genuinely earned by the model — the C1 rows for pinned classes
   overstate skill. The project knows this (diagnostic D-10 exists for exactly this reason).
3. **A backcast with admissible measured inputs is the ceiling, not the forecast.** The one
   statistical-mode A/B ever run (ERCOT, 2026-06-16) doubled the failure count with overlays
   off. The project has since reframed this delta as the "backcast→forecast input gap" — a fair
   framing — but the gap has been measured once, on one ISO, before substantial rebuilds.

---

## 6. Magic numbers and curve fitting — independent inventory

The project's internal audit already produced a candid census; this review verified its major
items at HEAD (`37d3923`) and grades the current state.

### 6.1 The sanctioned fitted surface (real, large, labeled)

- **Per-ISO coal-passthrough sigmoids** — `COAL_SIGMOID_DEFAULTS`
  (`src/market_sim/config/scenarios.py:7156`), self-described in-code as "the per-ISO tuned"
  curves. Still the largest fitted table in the model. The D-8 identifiability analysis
  (`docs/out-of-sample-results-2026-07.md` §2C) shows each asymptote is effectively pinned by a
  single gas regime (floor by 2024, midpoint/ceiling by 2025) — "weakly identified / borderline
  unidentified" is the project's own accurate phrase.
- **Per-ISO offer-band multipliers** (~230 scalars across keepers' `run_config.json` files, per
  the audit census; core defaults like `cc_committed_hr_mult = 1.23`,
  `scenarios.py:813`). Sanctioned by rule 1 (tune offer curves after structure), registered per
  rule 24, ISO-scoped per rule 25. Identification is in-sample-only; the three-year gas-regime
  spread ($2.19–$3.52) is the sole mitigant.
- **ERCOT AS revenue + saturation curve** — `constants.py:3482,3973–4006` (storage $169/kW-yr;
  `REF_GW 4.0`, exponent 2.5), calibrated to reproduce the observed 2023→25 AS revenue crash.
  Live in forecast capacity economics. The endogenous alternative
  (`ercot_storage_as_endogenous`, reserve-dual-derived) exists and is the structurally right
  successor; the fitted curve remains the default fallback.
- **NYISO Long Island self-supply share 0.45** (`constants.py:4870`) — anchored "a touch below"
  the realized share rather than on the LMIC requirement; audit C-17, unchanged at HEAD.
- **Merchant CHP behind-the-meter share 35%** (`constants.py:213`) — now honestly commented
  "residual-identified, forecast-risk — no independent source yet." The honest label does not
  supply the missing identification, but industrial/commercial shares are now EIA-923
  Schedule-8-sourced (resolved half of audit C-4).
- **CAISO WECC simultaneous-import cap 7,500 MW** (`iso_configs.py:437`) — the audit's
  flagship fitted scalar is still the static default, hand-tightened from the measured 8,300
  MW p01; the current keeper lineage supersedes it with the published CAISO MIC via
  `capacity_deliverability_limits`, so it persists as documented fallback (closeout:
  `docs/caiso-c5-wecc-cap-closeout-2026-07-03.md`).
- **NYISO year-keyed import-ladder scarcity rungs** (audit C-6 remainder) and **per-ISO gas
  availability factors carrying "was 0.83/0.88" adjustment trails** (audit C-18) — unchanged.

### 6.2 Resolved since the audit (verified at HEAD)

- **CAISO CT three-engine forcing** — scrubbed and re-verified (CV 0.000 → 3.05–3.52; off-window
  binding 62–66% → 0%); bridge eligibility now gates on physics (`min_down ≥ 4h`,
  `constants.py` `RA_BRIDGE_ECON_MIN_DOWN_HOURS`), not class tuples.
- **NEISO and MISO seam ladders** — re-derived from measured data only by frozen scripts
  (Q-Q duration coupling of measured LMPs and EIA-930 flows), replacing residual-fitted ladders.
- **Per-plant coal CF ceilings** — re-grounded from outcome-shaped caps to CAMPD p99 physical
  capability (`constants.py:1835–1838` documents plants excluded because their CEMS shows no
  sub-nameplate limit).
- **The deprecated ORDC offset** — deleted outright, not zeroed (`scenarios.py:917`), closing
  the "re-armable answer key" incident that motivated rule 26.
- **Env-var tuning channels** — the interchange-shape knobs are now registered `ScenarioConfig`
  fields (`scenarios.py:1328–1350`); remaining `os.environ` reads in `src/` are solver/debug/
  data-root only (verified by sweep).
- **The retired PJM pumped-storage $10 adder** — `PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` is now
  an empty registry with the mis-measured-residual post-mortem in the comment.

### 6.3 Open validity risks (this review's own findings)

1. **The holdout program exists only on paper, and one governance record overstates it.**
   `calibration-complete.json` (NEISO entry) states the 2019 + H1-2026 locked test "was scored
   ONCE with the frozen neiso-53 config and STANDS," and two handoff docs repeat it. The
   artifact record contradicts this: no registry entry, bundle, or bench file for any
   out-of-training year exists (`frontend/data/backcast/bench/NEISO/` holds 2023–2025 only);
   `docs/out-of-sample-results-2026-07.md` records D-6 as NOT RUN; and the
   calibration-complete memo's own decision record ends with the owner's same-day G-19
   execution hold, reaffirmed in intake logs through 2026-07-13. On the evidence, **no holdout
   year has ever been solved**, and the "scored once and stands" claim is documentation drift
   that should be corrected before it is ever cited as an out-of-sample result.
2. **The CI enforcement described in the governance rules does not exist at HEAD.** CLAUDE.md
   rule 22 cites a `.github/workflows/ci.yml` `quarantine-gates` job; the workflows directory
   contains only `deploy-pages.yml`, `fetch-caiso-oasis-bulk.yml`, and
   `file-integrity-guard.yml`, and no `ci.yml` appears anywhere in git history. The quarantine
   is in fact enforced by `run_calibration_full.py`'s hard-fail and by manually-run audit
   scripts (`scripts/audit_keepers.py`, `scripts/legitimacy_diagnostics.py` — both present).
   In-process enforcement is real but weaker than the documented CI backstop; either the
   workflow should exist or the rule text should say what actually enforces it.
3. **Coefficient identification is demonstrably fragile out-of-training** (the project's own
   D-8): drag-hinge slope drift of 16–18% for PJM/CAISO leave-2025-out, three reliability-floor
   limbs whose temperature correlation flips sign, and a CAISO CT drag floor ≈ 90% of the
   measured class energy — "close to fitting the CT class outright." These mechanisms remain in
   keepers. Publishing D-8 alongside the keepers was the right act; shipping sign-flipped limbs
   is still a validity exposure.
4. **Measured-input saturation concentrates all skill claims on gas/coal/CT** (§5 caveat 2),
   and those are exactly the classes the tuned offer scalars target. The D-10 "free-class-only
   rescore" diagnostic that would price this in has been specified but the review found no
   published per-keeper D-10 number on the dashboard payloads examined.
5. **Selection pressure is structural.** ≥400 solves scored on three years, a top-15-per-ISO
   retention policy that hides ~80% of the search, and a Jacobian joint-move optimizer are a
   textbook multiple-comparisons environment. The countervailing discipline (structure-first
   keeper promotions logged with worsened fit, probes rejected on mechanism grounds, refusals
   to tune recorded) is real and unusual — but it is discipline against a headwind the
   validation design was meant to remove and has not yet.

### 6.4 The ERCOT phantom-outage incident (case study)

On 2026-07-17 the project withdrew ERCOT's frontier declaration after discovering that the
CAMPD facility-outage detector had hard-zeroed 1.9–5.7 GW of daily-cycling CC capability that
its own CEMS showed generating — the scarcity tail had been calibrated against an artificially
tightened fleet. The fix was adopted, the keeper re-solved on corrected data, the 2023 summer
over-shoot resolved ($1,068 → $242), the real scarcity tail un-caught (179 → 53 of 181 hours),
and the determination honestly reverted to NOT-YET with the note "we can't have a keeper on
inaccurate data" (keepers.json, frontier.ERCOT). Cross-ISO re-audit lanes were opened because
the detector is shared. This incident cuts both ways and the review weighs it accordingly: it
demonstrates that a multi-month calibration can silently absorb a data defect into its fitted
layer (the core epistemic risk of residual tuning), *and* that the governance regime detects,
publishes, and takes the accuracy loss rather than keeping the flattering artifact — behavior
with no analogue in commercial vendor practice.

---

## 7. Best-fit use cases

**Well-suited today (dispatch-half-dominant, in-sample-supported):**

1. **Scenario and policy mechanism analysis in the calibrated ISOs** — carbon price paths,
   RPS/CES designs, IRA credit expiries, cap-and-trade adders: the policy layer is at or above
   CEM practice, mechanisms enter structurally (constraint rows/adders with meaningful duals),
   and scenario deltas are less exposed to fitted-level error than absolute levels.
2. **Zonal price-shape and revenue-environment studies** (energy + AS + capacity stack) for
   PJM/NYISO/NEISO, where mean, shape, and volume are demonstrated at commercial grade —
   including storage-arbitrage and thermal net-revenue screening at annual/monthly grain.
3. **Emissions accounting and CO2-trajectory work** — system CO2 within ±5% for four of six
   ISOs on a full-plant basis, with per-plant CEMS-derived forward rates and a leave-one-year-out
   certified estimator: stronger provenance than any surveyed CEM's emissions layer.
4. **Market-design what-ifs on the represented mechanisms** — ORDC parameters, reserve demand
   curves, ECRS deployment designs, RA must-offer, capacity-market demand-curve vintages —
   because these exist as explicit structure rather than post-processing.

**Usable with stated caveats:**

5. **Long-horizon (2026–2050) fleet and price trajectories** — the mission the model was built
   for. The machinery is thoughtful (confirmed-exit registry, retrofit-or-retire screens,
   published ELCC curves, sloped capacity curves), but until the holdout program runs and a
   fleet-evolution hindcast exists, outputs should be treated as internally-consistent scenario
   arithmetic, not validated forecasts — and presented with the backcast→forecast input gap
   (D-7) attached.
6. **ERCOT/CAISO/MISO applications** — currently NOT-YET on the model's own rubric (scarcity
   tail formation ERCOT/MISO; CO2 and 2025 price level CAISO); usable for mechanism studies,
   not yet for level-sensitive conclusions.

**Out of scope (by design; the model does not claim otherwise):**

- Nodal congestion, basis, FTR/CRR valuation (needs PROMOD/Dayzer/UPLAN-class networks).
- Resource-adequacy certification — LOLE/ELCC studies (needs SERVM/PRAS-class Monte Carlo;
  the model consumes published ELCC, it cannot produce one).
- Uplift/ELMP/fast-start price formation, multi-settlement DA/RT spreads, virtual bidding.
- Short-term operational forecasting; AC power flow; stability.
- Regulatory IRP-of-record use, until out-of-sample validity is demonstrated — most IRP
  jurisdictions accept Aurora/PLEXOS on stakeholder-reviewed databases, but this model's
  differentiator (calibration rigor) is also its openest liability until the holdout numbers
  exist.

---

## 8. Recommendations (referee's list, priority order)

1. **Execute the designed validation.** Run the one-shot 2022 validation and the locked tests
   under the exact frozen-config protocol already written (§4–5 of the NEISO memo are a model
   of pre-registration); publish results whatever they are. Until then, remove or correct the
   `locked_test_scored_on` claim (§6.3-1). A capacity-evolution hindcast (2015→2025 builds/
   retirements vs actuals, Cole & Vincent-style) would do for the evolution half what the
   backcast does for dispatch.
2. **Reconcile documented vs actual enforcement** (§6.3-2): either land the quarantine-gates CI
   job or amend rule 22's enforcement clause. The file-integrity guard shows the project knows
   how to make a rule mechanical.
3. **Retire or re-ground the surviving residual-identified scalars** on the audit's C-list
   (LI 0.45 → LMIC requirement; merchant CHP 35% → the sourced path in the host-load memo;
   NYISO year-keyed ladders → the NEISO/MISO measured-ladder construction, which is the proven
   template; gas availability factors → cited GADS values or a derive script).
4. **Publish D-10 (free-class-only) and D-11 (knob Jacobian) per keeper** on the dashboard, so
   the pinned-class inflation and single-knob fragility are visible where the headline metrics
   are.
5. **Treat the D-8 sign-flip limbs as disabled-by-default** until they re-identify on longer
   history, and disclose the CAISO CT drag's forced share beside its keeper.
6. **Bound storage foresight in keepers** (the daily-cycling flag exists; spec §1.3 documents
   the perfect-foresight bias) and state the choice per keeper.
7. **Independent replication** of one keeper from raw data by a party outside the project would
   convert the reproducibility architecture (frozen derives, schema contracts, cache keys) from
   design into evidence.

---

## 9. Verdict

| Question | Assessment |
|---|---|
| Is the architecture legitimate? | Yes. Prices from duals, renewables as decision variables, structure-first rules, measured-data admissibility test — the design is sound and in several respects (scarcity structure, policy mechanisms, data contract) ahead of its class. |
| Production cost, capacity expansion, or hybrid? | Hybrid: a commercial-grade zonal PCM (validated in-sample) driving an Aurora-LTCE-class myopic evolution wrapper (unvalidated). The label "hybrid" should not obscure that the two halves currently carry very different evidentiary weight. |
| Is the calibration honest? | Unusually so in process — machine-scored rubric, published failures, self-reversal on the record — while remaining wholly in-sample in substance. The fitted surface is large but registered, labeled, and ISO-scoped; its identification is thin and known to be thin. |
| Does curve fitting undermine validity? | It bounds it. In-sample results for PJM/NYISO/NEISO are commercial-grade and the structural mechanisms are real; but ~290 residual-identified scalars on three years of data, with zero executed out-of-sample scores, mean forecast validity is currently a design claim. The remedy is specified, pre-registered, and unexecuted. |
| Best single-sentence positioning | A six-ISO, open-architecture zonal market simulator with commercial-PCM operational depth, CEM-grade policy structure, better-than-industry calibration governance, and a validation program whose most important step has not yet been taken. |

*Prepared as an independent review. All repository citations verified at commit `37d3923`
(2026-07-18); external model characterizations rest on the public sources cited in §3–§4 and
were not verified by hands-on operation of those tools.*
