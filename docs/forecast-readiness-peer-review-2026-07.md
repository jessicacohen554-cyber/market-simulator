# Forecast-readiness peer review vs commercial practice — 2026-07-31

**Session:** `forecast-readiness-prompts` (owner ask: "peer review this against how other commercial
grade models conduct production cost modeling and capacity expansion modeling forecasts").
**Docs-only review — no LP solved, no parameter or default changed, nothing registered.**
Written against `origin/main` HEAD `7b8c36a` (2026-07-31), alongside the same-day refresh of the
FFR execution pack (`docs/forecast-readiness-prompt-pack-2026-07.md`).

**Reviewed object:** the forecast methodology as specified (`model-methodology-spec.md` §5,
`docs/forecast-development-plan-2026-07.md`) plus the remediation program that prepares it for
production runs (`docs/forecast-readiness-audit-2026-07.md` FR-1..FR-27 and the FFR pack).

**Reference practice:** commercial production-cost models (PLEXOS, PROMOD, Aurora, EnCompass,
GridView, SERVM) and capacity-expansion models (ReEDS, EPA IPM, GenX, PLEXOS LT / Aurora LT,
EGEAS). This review does **not** re-derive the comparison tables — the repo already holds a deep
design-legitimacy review against exactly this reference set
(`docs/third-party-peer-review-2026-07.md`), a standing per-mechanism research mandate
(forecast plan §4, "consult the field before inventing"), and completed adopted/adapted/rejected
tables for the retirement rule (`docs/handoffs/ff-retirement-rule-redesign-2026-07.md`), the
entry stack (`docs/handoffs/ff-entry-stack-completion-2026-07.md`), new-build costs
(`docs/new-build-cost-methodology-2026-07.md`), fuel forwards
(`docs/fuel-forward-methodology-2026-07.md`), and capacity-price formation
(`docs/capacity-price-forward-methodology-2026-07.md`). What this review adds is the
**readiness-program question**: graded against how those models actually run forecasts in
production, is the FFR remediation plan complete — and where it is not, what changes.

No number in this doc is new: every quantitative claim carries its in-repo citation (audit
finding ID or methodology doc). Rule 5 applies.

---

## 1. Method

Each commercial-practice delta is graded into one of three buckets:

- **(A) Must-fix before trustworthy forecasts** — a defect or omission that a commercial shop
  would treat as a release blocker. Test: is it covered by an FFR prompt? If not, the pack gains
  one.
- **(B) Should-schedule structural work** — capabilities standard in the reference set that this
  model has chartered but not landed. Test: is it in Wave S / Wave P with an owner decision
  point?
- **(C) Accepted limitation — disclose, don't schedule** — a deliberate design position that
  diverges from commercial practice, defensible under the repo's own rules (one-pass, pure LP,
  full 8760). Test: is it on the standing disclosure list that accompanies every forecast
  deliverable (§4)?

The grading is conservative in one direction: where the divergence is *by design and defended in
the spec*, it lands in (C) with a disclosure obligation, not in (A) — re-litigating settled
architecture (e.g. LP-not-MIP) is out of scope and would violate the one-mechanism and
no-rewrite discipline.

---

## 2. Where the model already meets or exceeds the reference practice

Stated first so §3's negatives are calibrated (same convention as audit §3.6):

- **Chronological full-8760 dispatch every solve year.** Commercial CEMs almost universally
  compress time (ReEDS representative timeslices, IPM load-duration segments, GenX sampled
  weeks); this model never does (rule 8). Its dispatch tier sits with the LP-relaxation
  commercial PCMs (PLEXOS RR / Aurora / SERVM) per the third-party review's own placement.
- **Prices = LP duals** with an ORDC/scarcity overlay — the same price-formation family
  commercial PCMs use for energy-price forecasting (as opposed to MIP-cost runs whose prices
  need uplift reconstruction).
- **A measured, gated backcast calibration discipline.** The rubric-v2 benchmark memo's central
  finding stands: no commercial vendor publishes quantitative backcast accuracy at all
  (`docs/rubric-v2-benchmark-memo-2026-07.md`); EnCompass's public validation claim is
  regulatory adoption, and IPM's is procedural QA. Four of six ISOs currently hold
  CALIBRATED(-with-caveats) determinations on committed, re-scoreable evidence. This is
  genuinely beyond commercial state of practice.
- **A three-tier holdout policy with enforcement** (train / validation / locked test, rule 22,
  CI-gated, freeze-capable). No commercial analogue exists.
- **An uncertainty layer that separates deterministic scenarios from probability statements**:
  the 13-case AEO/IPM-style matrix is labelled "NOT a probability band" (`matrix.py`), the
  copula sampler anchors gas vol to NYMEX/STEO front and AEO spread back
  (`uncertainty.py`), and the structural prior widens-never-recenters and honestly labels its
  fleet-path term UNMEASURED (`structural_prior.py`). Vendor practice is typically
  deterministic-scenarios-only; SERVM does weather/outage Monte Carlo but not driver copulas.
- **Adopted-from-the-field mechanisms where the field is right**: ReEDS's 200 %-growth entry
  constraint (`ENTRY_GROWTH_LIMIT_MULTIPLE`), IPM-style going-forward-cost retirement screening
  (the FF-1A pipeline rule), Brattle net-CONE/VRR capacity-price formation with a sloped curve,
  published-ELCC accreditation curves. Each carries its adopted/adapted/rejected memo.

---

## 3. Delta register

### 3.1 Bucket A — must-fix, and their FFR coverage

| Delta vs commercial practice | Model state (audit ID) | Commercial anchor | FFR coverage |
|---|---|---|---|
| **Capacity ledger must close.** Every CEM in the reference set maintains an exact fleet balance identity (builds − retirements = Δcapacity); a leak of 1.3–1.6 GW per ISO (CAISO/MISO measured) would be a release blocker anywhere. | FR-1/FR-2/FR-13 — `confirmed_derates` documented but never written; partial-year exits never complete | ReEDS/IPM/GenX capacity accounting; audit §3.1 | **FFR-1A** ✔ |
| **Availability must age with the fleet.** PCMs key forced-outage rates to unit age/class (EFORd schedules in PROMOD/PLEXOS; SERVM draws unit EFOR); a fleet frozen at its 2024 age for 25 years — with negative-age entrants — is not a defensible forward availability envelope. | FR-7 — age keyed to `weather_year`, not solve year | Vendor EFORd-class practice; audit §3.2 | **FFR-1B** ✔ |
| **Historical single events never enter forward years.** Commercial forecast databases separate historical actuals from forward assumptions as a data-management invariant. | FR-8 — Martin Lake 2025 fire derate reachable in crossover forward years | Rule 13 itself is the stricter in-house form | **FFR-1B** ✔ |
| **Retirement economics = going-forward NPV, not a loss counter.** The shipped legacy rule (N loss-years → exit) has no analogue in the reference set; IPM screens horizon NPV vs going-forward cost, ReEDS uses lifetimes + operating margin, PLEXOS LT/Aurora integer NPV. The compliant redesign exists and is dormant. | FR-4 — `retirement_rule="legacy"` default | `ff-retirement-rule-redesign-2026-07.md` (the adopted/rejected table) | **FFR-2B → owner D-1** ✔ |
| **Entry must be damped.** Bang-bang build-the-whole-queue behavior is exactly what ReEDS growth constraints and interconnection/commissioning lags exist to prevent; the dampers exist and are default-off. | FR-5 — `entry_rate_limits`/`entry_commissioning_lag` off; MISO I13 cobweb | ReEDS growth penalty/limits; `ff-entry-stack-completion-2026-07.md` | **FFR-2B → owner D-2** ✔ |
| **RA accounting counts every accreditable resource.** Hydro carries NQC/UCAP/SAC credit in every RTO's RA construct and in every reference CEM's firm-capacity ledger; a structural zero is not a modeling choice, it is an omission (3.6/3.3 GW measured, CAISO/NYISO). | FR-3 — no hydro term in `accredited_firm_capacity_mw` | RTO RA manuals via FF-2B spec | **FFR-1C** ✔ |
| **Seam prices ride the same forward fuel path as the core.** Inconsistent fuel bases across a seam is a classic PCM QA failure (hurdle/seam calibration reviews exist for exactly this). | FR-9 — neighbor-price seam raw-indexes a backcast gas dict in crossover | audit §3.2 | **FFR-2A** ✔ |
| **Capacity-price anchors re-anchor to published auction results every cycle.** Holding a 2027/28 PJM net-CONE flat for 23 years while the 2028/29 BRA cleared +34 % higher (audit FR-19's citation) misprices the largest capacity market's exit/entry margin. | FR-19 — stale anchors; FF-G3 escalation inert | Brattle/RTO planning-parameter practice; `capacity-price-forward-methodology-2026-07.md` | **FFR-2C → owner D-3** ✔ |
| **Validate the configuration you ship.** Commercial validation (such as it is) exercises the production posture. The capacity hindcast scores fixed net-CONE pricing while production defaults clear the sloped VRR curve — so FC-3 evidence does not validate shipped price formation. | **FR-14 — previously covered by NO pack session** | audit §3.5 | **NEW: FFR-2E** (added to the pack this session) |
| **Evidence must be current and staleness detectable.** A verdict board scored 11+ days and ~20 keepers ago, with no drift detector, would fail any commercial QA regime (IPM's published validation is *precisely* procedural QA). | FR-21/FR-24/FR-25 | `forecast-determination-rubric.md` §IPM | **FFR-1D / FFR-3B / FFR-3A** ✔ |

**Net result for the pack:** one genuine coverage hole (FR-14 → new FFR-2E). Everything else in
bucket A was already mapped — the audit's remediation plan survives commercial-practice review
intact on content, and its main risk is the one §3.5 already names: evidence staleness, which
recurred in the 24 hours after the pack was written (see the pack's state-delta section).

### 3.2 Bucket B — chartered structural work (confirm, don't re-charter)

| Delta | Commercial anchor | Charter |
|---|---|---|
| Load-**shape** evolution (electrification/EV/heat-pump reshaping; winter-peak flips) — peak CAGR ≡ energy CAGR today (FR-16) | Vendor PCMs consume ISO hourly forecast shapes; NREL EFS/dsgrid layering is the CEM pattern the FF-G4 memo adopted | **FFR-SA** (implement Option B, default-off) |
| Nuclear license/SLR horizons as an exit driver (BLK-9/FR-18) | IPM and ReEDS both bound nuclear lifetimes by license horizon + SLR assumptions | **FFR-SB** (design memo; one-exit-mechanism constraint) |
| Committed transmission expansion in forward TTC (frozen base-year grid today) | Standard PCM practice: known-and-committed projects enter the forward network; endogenous TX build is CEM-only (ReEDS) and NOT proposed | **FFR-SC** (run the owed A/B; stays default-off) |
| Announced/confirmed retirement registry freshness + quarterly re-query cadence (FR-18; Eddystone §202(c) expiry 2026-08-22) | Vendor databases refresh announced retirements on a subscription cadence | **FFR-PA** (time-sensitive) |
| Cost-vintage currency: ATB 2024 → 2025/2026; §45Y/48E primary-statute verification (FR-20) | ReEDS re-vintages to each ATB release; IPM documents cost-chapter vintage | **FFR-PB** |

All five were already chartered; this review adds no new bucket-B items. One emphasis: **FFR-PA
is the only calendar-deadlined item in the entire program** (the Eddystone order expires
2026-08-22) and should be dispatched with Wave 1, not "anytime."

### 3.3 Bucket C — accepted limitations (disclose with every forecast deliverable)

These are deliberate positions, each defended in the spec or an adjudicated memo. Commercial
practice differs; the honest posture is a standing disclosure, not a rebuild. The consolidated
list is §4 — the items, with their commercial contrast:

1. **Pure-LP commitment (no MIP SCUC).** PROMOD/PLEXOS ST/EnCompass run MIP unit commitment;
   this model is LP-only by non-negotiable rule, with P0→P1 amortized-startup bidding and
   physics-gated commitment bridges (spec §1.6). The third-party review places this in the
   defensible LP-relaxation tier; the cost is understated block-commitment rigidity
   (no min-run MW integrality, startup costs amortized not discrete).
2. **Myopic one-pass capacity evolution.** No intertemporal optimization (IPM's LP, GenX
   perfect-foresight contrast) and no within-year convergence iteration (PLEXOS LT/Aurora
   iterate; forbidden here by rule 10). Known bias direction documented in
   `docs/model-audit-2026-06.md` (myopia as a systematic emissions-path bias). Partially
   mitigated by the entry lookahead reprice and the (owner-gated) dampers — never eliminated.
3. **Single pinned weather year in any one solve** (default 2024) for demand shape, renewable
   CFs, and hydro. Reliability-grade commercial practice (SERVM/Astrapé, RA studies) sweeps
   dozens of weather years. The machinery to do this **exists** (`market-sim ensemble` over the
   verified per-ISO weather pool; the copula sampler's weather/hydro dims) — what is missing is
   a decided posture for the golden runs. **This review's recommendation: the D-7 owner box in
   the pack now carries the explicit choice — single-draw golden labelled as
   weather-conditional, vs an ensemble-of-weather-years golden at ~N× compute.** A single-draw
   golden is defensible only with the label.
4. **Exogenous, non-demand-responsive fuel prices.** AEO-anchored low/mid/high trajectories;
   no gas supply curve (ReEDS makes AEO gas demand-responsive; IPM has endogenous fuel supply).
   A high-electrification scenario therefore cannot feed back into gas prices; the scenario
   matrix's GAS-LO/HI axis is the compensating instrument
   (`docs/fuel-forward-methodology-2026-07.md`).
5. **No intra-ISO hurdle rates.** Commercial zonal PCMs commonly apply hurdle rates between
   internal zones to reproduce observed seam friction; here internal flows are limited by
   TTC/interfaces only, and hurdles exist only on external seams
   (`model/interchange/spec.py`). Adding tuned internal hurdles would collide with rules 1/13
   (a fitted friction is a residual-tuned adder) — so this stays a disclosed representation
   choice unless a *published* hurdle basis is adopted.
6. **No inter-hour ramp-rate constraints** (spec §7.2 names it a future enhancement; reserve
   products partially proxy flexibility). Commercial PCMs carry MW/min ramps.
7. **Capacity-expansion (fleet-path) skill is unmeasured beyond T1-H.** The T1-H 2021–2025
   capacity hindcast is the in-house Cole & Vincent analogue, but the structural prior's
   fleet-path horizon term is pinned 0/UNMEASURED, so published bands are **dispatch-conditional
   — they exclude fleet-path structural error** (`structural_prior.py`). No forecast bundle
   carries a DOF ledger yet (FR-27; the FFR-3B stub makes the gap visible rather than closing
   it). Commercial vendors, for contrast, publish neither — but the disclosure obligation is
   ours because we claim calibration.
8. **RPS/CES as LP constraints with dual-price RECs; capacity prices from net-CONE/VRR, not a
   capacity-demand-curve equilibrium iteration.** Same family as ReEDS/IPM constraint-dual
   practice; differs from consultant-grade capacity-market simulators that iterate entry to
   equilibrium. One-pass rule again; disclosed.

---

## 4. Standing disclosure list for forecast deliverables

Every golden/full-horizon forecast deliverable (and any externally-shared T1 product) carries
this list verbatim until the underlying item changes state:

> This forecast is produced by a chronological full-8760 LP dispatch model with a one-pass
> annual capacity-evolution loop. It does not include: MIP unit commitment; intertemporal
> capacity optimization or within-year entry/exit convergence; inter-hour ramp constraints;
> intra-ISO hurdle rates; demand-responsive fuel pricing. Unless produced by the weather
> ensemble, results are conditional on a single pinned weather year (stated in the run config).
> Uncertainty bands are dispatch-conditional: the fleet-path (capacity-expansion) component of
> structural error is unmeasured and excluded. Deterministic scenario cases are a range, not a
> probability distribution.
>
> **Capacity-additions metric basis (from 2026-08-04).** Additions are scored against the year
> the model *decided* to build, not the year the unit commissions (owner decision D-9(ii),
> FFR-3S). This changes what the additions metric measures, so **every additions verdict
> committed before 2026-08-04 is non-comparable to one committed after**, and **the FF-2D
> regression baseline is not usable for additions specifically** — an additions band that
> "moves" across that date may be measuring the instrument, not the model. Retirements-side
> comparability is unaffected: the retirement channel has no commissioning lag and the change
> does not touch it. Cross-date additions comparisons require re-measuring both sides forward
> on the decision basis. Each new `score.json` carries both bases (`additions` = decision,
> `additions_cod_basis` = COD) plus an `additions_basis` provenance block, so the two ARE
> comparable within a single run.

(Wording lives here; the pack's every-prompt footer references it. FFR-3B's DOF-ledger stub and
any future FF-G4/weather-posture decisions shrink it item by item.)

---

## 5. Verdict

The FFR remediation program is **complete against commercial-practice review with one addition
and one re-prioritization**: FFR-2E (validate the shipped capacity-price posture, FR-14) is
added to Wave 2, and FFR-PA (retirements registry refresh) is promoted to dispatch-with-Wave-1
for its 2026-08-22 deadline. The bucket-A list is otherwise fully covered; bucket B was already
chartered; bucket C is now a maintained disclosure list rather than scattered caveats. The
model's genuinely differentiated position — a backcast-calibrated, holdout-disciplined,
full-8760 forecast system — survives the comparison; its honest weaknesses versus the
commercial reference set are the ones its own audit already named, plus the weather-posture
decision this review sends to the owner (D-7).
