# PREREG — miso-136: survey of a within-day MISO CT offer-conduct identification (the miso-134 named successor's data prerequisite)

**Session:** miso-136, 2026-08-06, branch `claude/miso-136-calibration-t4olnw`,
off `origin/main` at `8f09152b`. Charter lane **(a)**.

**Committed and pushed BEFORE any MISO / IMM / FERC source is opened.** No LP
will be solved in this lane. Nothing will be written under `data/raw/`
(assessment, not intake — the miso-135 ask-§5 posture). No mechanism will be
built, sized, or armed. MISO keeper unchanged at
`2026-08-05-miso-132b-cc-committed`.

---

## §0 — Everything already in hand (disclosed before the survey)

**Keeper state (from the handoff, not re-derived):** NOT-YET; sole FAIL C7
`COAL_PRB` 2025 `cv_ratio` 0.338 vs 0.50 via `R_dfrac` 0.347; 2023/2024 pass
0.505/0.524; ledgered caveats 2/3 {C3a, C3c}; budget SATURATED, C7 not
ledgerable.

**The assertion under test** (miso-134 FINDING §9.3, verbatim): *"MISO
publishes no submitted-curve corpus at the grain the `measured_offer_surface`
family needs, and without such a source the mechanism is a rule-21/24 fitted
path and inadmissible."* Asserted, never surveyed. The
`measured_offer_surface` MISO cell is `U` **by absence of a testable input**
and its ground is this unsurveyed claim (miso-135 §10 record repair).

**What the family's grain is** (matrix row `measured_offer_surface` def/note,
read before this PREREG): participant-submitted DAM offer curves at unit
grain, class-resolvable (the working ISOs derive per-class multipliers:
ERCOT 60-day DAM disclosure, CAISO OASIS DAM public bids, PJM Data Miner
masked energy offers, NEISO `hbdayaheadenergyoffer`), hourly, condition-binnable.
The miso-134 successor needs specifically **within-day** (hour-of-day) CT
offer conduct.

**Repo facts already known (grepped from this repo before this PREREG):**

* The repo ALREADY consumes MISO daily market reports machine-readably from
  `https://docs.misoenergy.org/marketreports/` — LMP (`*_da_expost_lmp.csv`),
  PBC, outages (`*_mom.xlsx`), and — decisive for the prior — the **masked
  cleared-offers ancillary-service report `YYYYMMDD_asm_rt_co.zip`**
  (`scripts/data/fetch_miso_asm.py`), which carries per-masked-unit,
  per-interval cleared reserve MW with a Region attribute. So (a) the
  endpoint is reachable from this environment class, and (b) MISO
  demonstrably publishes masked cleared-offer data for AS.
* PJM precedent in-repo (`pjm128_da_award_feed_scope.json`): PJM's masked
  offer codes are changed annually and carry no published crosswalk — the
  shape a bridge-failure NO could take here.
* `docs.misoenergy.org` retains a **rolling ~3.5-year window** of daily
  reports (`fetch_miso_hub_lmp.py` docstring) — coverage of 2023 is
  therefore a real question, not a formality.

**Model-memory prior, disclosed as a prior and not evidence:** I recall MISO
publishing daily masked ENERGY offer reports (names of the form `da_co` /
`rt_co`, "Day-Ahead/Real-Time Cleared Offers") under the FERC Order-719-family
transparency requirements, with a lag on the order of 90 days; I am uncertain
whether the files carry any unit-type/fuel attribute, and uncertain about
masked-ID persistence. Every one of these recollections must be verified
against the live source before being cited.

**Numbers in hand that could tempt a post-hoc gate:** the miso-134 measured
CT band levels (`marg_econ_low_p50` 0.687/0.691, Δ_max $7.321/MWh) and the C7
2025 shortfall series. **None of these may enter any gate below**; this lane
measures the *existence and grain of a source*, never a conduct statistic.

---

## §1 — The question and the enumerated sources

**Q: Does a public identification for within-day MISO CT offer conduct exist
that is NOT the C7 residual?** Answer YES-with-source, NO-and-closed, or the
pre-declared CONDITIONAL (§4). Sources to be surveyed, each closed
individually:

* **S1** — MISO Market Reports: daily energy offer reports (the `da_co` /
  `rt_co` family, whatever their real names prove to be).
* **S2** — MISO Data Exchange (`apim.misoenergy.org`) product catalog.
* **S3** — Potomac Economics MISO SOM: report body, appendices, workpapers.
* **S4** — FERC EQR.
* **S5** — anything the survey itself surfaces (recorded even if closed).

**The miso-135 purpose test is applied FIRST to each source**: state what the
publication exists to do, predict its grain from that purpose, and check
whether the only bridge from its grain to the model's grain is a forbidden
series — before budgeting any deep search of it.

---

## §2 — Gates (all declared before any source is opened)

* **G-0 access (GATING):** the source is enumerable and a sample covering the
  training years is fetchable from this environment. Fetching is restricted
  to 2023–2025-dated files (rule 22; T5 below).
* **G-1 kind:** the quantity is a **participant offer parameter recorded ex
  ante of dispatch** — submitted or as-offered curves (price/MW segments,
  econ limits, availability declarations). A *cleared*-offers file passes
  kind iff what it records is the offer curve itself rather than a
  reconstruction from dispatch. **FAILS kind:** any outcome series
  (generation, burn, LMP, cleared MW as a quantity), IMM-*estimated*
  reference levels or markups, any model-derived curve.
* **G-2 grain & bridge:** (i) hourly / within-day resolution; (ii) CT-class
  assignability by an **admissible bridge**:
  - **Bridge class A (admissible, direct):** an in-source unit-type / fuel
    attribute.
  - **Bridge class B (admissible in kind, CONDITIONAL):** a classifier over
    in-source **offer-side declarations only** (econ max/min structure,
    emergency ranges, availability structure, self-schedule structure),
    validatable at distribution level against registration-grain class
    aggregates (e.g. EIA-860 CT fleet counts/capacity) **without touching
    any dispatch outcome**. Class B can at most yield CONDITIONAL (§4) —
    this survey will not build or validate such a classifier.
  - **FORBIDDEN bridges (either fails G-2 outright):** matching masked units
    to observed generation/dispatch/emissions series (the miso-103 answer-key
    family); classifying units by the very conduct statistic the successor
    would measure (circular).
* **G-3 coverage:** all three training years retrievable footprint-wide, and
  the corpus plausibly contains the offered CT fleet (order-of-magnitude
  check of unit counts against the ~249-unit / 22.3 GW class scale from
  miso-134 — used ONLY as a scale reference, no conduct read).

**Prior (two-sided, declared):** existence of an energy cleared-offers corpus
(S1 passing G-0/G-1) is MORE likely than not, given the ASM sibling and the
disclosed memory. Full clearance including the class bridge is genuinely
uncertain — the purpose test warns that a transparency corpus masks identity
*by purpose*, so **G-2 is the likely failure point**; NO/CONDITIONAL on the
full stack is at least as likely as a clean YES.

---

## §3 — Look-alike traps, named in advance

* **T1** — hourly unit **generation** (CEMS, EIA-930) dressed as "within-day
  conduct". It is an outcome — the C7 residual's kin. Fails G-1.
* **T2** — IMM **reference levels** / SOM estimated markups. Modelled
  estimates, not conduct. Fails G-1.
* **T3** — the corpus exists, is real, hourly and offer-kind — **and its only
  CT bridge is dispatch-matching.** Then the answer is NO/CONDITIONAL despite
  existence: the right quantity at the wrong grain is the wrong source
  (miso-135). This is the trap a session under pressure would wave through.
* **T4** — SOM aggregate offer figures: right kind, wrong grain (annual /
  class-aggregate, not within-day corpus).
* **T5** — rule-22 hazard: the daily archives span 2022 and 2026. Only
  2023–2025-dated files are fetched; no out-of-training quantity is read,
  extracted, or tabulated.

---

## §4 — Decision rule and outcome categories (pre-committed)

* **YES-with-source:** some source passes G-0 ∧ G-1 ∧ G-2(A) ∧ G-3. The
  successor's data prerequisite is DISCHARGED; the finding records the
  source, grain, and bridge. (Even then, NO mechanism is armed this session;
  arming needs its own PREREG with kills per the handoff METHOD BARS.)
* **CONDITIONAL:** a source passes G-0 ∧ G-1 ∧ G-3 and the only bridge is
  class B (admissible in kind, undemonstrated). Recorded as
  "corpus-exists / bridge-unproven". This does **NOT** discharge the
  prerequisite and does **NOT** license any lever; the bridge demonstration
  becomes the chartered successor question. It is not a weasel category: it
  is the honest state "the miso-134 §9.3 assertion is FALSE but the
  prerequisite is still open".
* **NO-and-closed:** no source passes. Every enumerated source is closed
  with its reason (purpose/kind/grain/coverage), the miso-134 §9.3 assertion
  is recorded TRUE-as-surveyed, and charter lane (c) — the owner-facing
  assessment — is opened in this same session per the handoff.

**Consistency rules (kills):** K1 no LP; K2 nothing under `data/raw/`; K3 no
threshold or gate above altered after first fetch; K4 no conduct statistic
computed from any fetched offer file beyond structural checks (headers, unit
counts, grain, attribute presence, ID persistence) — measuring CT conduct is
the successor's job, not this survey's; K5 no cell verdict minted (no
mechanism is tested); K6 rule 25 — nothing here transfers any other ISO's
verdict onto MISO; K7 the trap register above is closed out explicitly in the
finding (each trap: fired / did not fire).

---

## §5 — Procedure

1. Push this PREREG. 2. Probe
`scripts/probes/_miso136_ct_offer_conduct_survey.py`: enumerate S1 candidate
report names against `docs.misoenergy.org/marketreports/`, fetch ≤2 sample
days per training year per existing report, parse headers and structural
facts only; survey S2 catalog; survey S3 index/appendix listing; adjudicate
S4 on the purpose test. 3. Record
`results/calibration/_miso136_ct_offer_conduct_survey.json`. 4. FINDING +
§5.4 queue stamp + `measured_offer_surface` MISO note ground update (record
repair of "unsurveyed" → surveyed, no verdict) + calibration-log entry, all
this session. 5. If NO: open lane (c) in this session.
