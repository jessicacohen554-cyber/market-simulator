# Third-Party Audit — Market Simulator (Release-Finalization, AUDIT-A)

**STATUS: RECORD** — Wave-1 deliverable of the Model Audit & Release-Finalization
Program (`docs/model-audit-release-plan-2026-08.md` §3/WS1). Written 2026-08-15.

**Auditor stance.** Independent third-party assessment: the auditor did not build
this model and has no stake in it being good. Scorer-only on committed artifacts —
no LP was solved, no holdout year touched, no rubric band moved. Every claim about
this repository cites a file (with line numbers where load-bearing) or a committed
artifact, verified at `origin/main` @ `9f48419` (2026-08-15). Main advanced to
`870c4c8` (PR #3987, the neiso-96 H1-2026 actuals intake) while this audit was in
progress; the delta was reviewed before publication — it is a rule-22 data
intake (no LP; freeze re-verified active; NEISO's locked test re-verified never
granted/spent) and changes no determination cited here; its one new self-reported
finding is registered at gap O8. External-model claims carry public-source
citations and live principally in the companion matrix,
`docs/audit/model-positioning-matrix-2026-08.md`.

**Relationship to prior review.** An independent peer review already exists:
`docs/third-party-peer-review-2026-07.md` (2026-07-19, at commit `37d3923`). This
audit does not re-litigate it. It (a) re-verifies that review's load-bearing
findings at today's HEAD, (b) records what changed in the four weeks since — the
rubric tightened twice, every keeper moved, and the out-of-sample record went from
zero data points to two spent validation touchpoints — and (c) adds the
release-oriented deliverables the program charter asks for: a nine-comparator
positioning matrix and a routed gap register (§8).

---

## 1. Executive summary

1. **What it is.** A six-ISO, full-8760, zonal, pure-LP electricity-market
   simulator (194 modules / 132,921 lines under `src/market_sim/`) whose prices
   are LP duals, with in-LP reserve co-optimization and ORDC/RCPF scarcity
   structure, per-plant tranche offer curves, and a deliberate one-pass annual
   capacity-evolution wrapper. It forecasts by default (2026–2050) and carries a
   backcast mode, governed by a written admissibility rule for measured inputs,
   used to calibrate against 2023–2025.
2. **The governance regime is the model's most distinctive asset, and it is
   real.** A machine-scored, versioned, externally-anchored determination rubric
   that has demoted its own keepers when tightened; fail-closed three-tier
   holdout gates with an active spend freeze; ~206 pre-registration documents
   with direction-blind promotion rules; byte-identity golden gates; a
   10,139-line adjudicated mechanism-test ledger; and a public dashboard that
   registers rejected probes alongside keepers. No surveyed commercial or open
   comparator publishes anything comparable (companion matrix, "Validation
   norms").
3. **The evidence currently certifies less than the apparatus suggests.** At
   2026-08-15: PJM is the sole CALIBRATED ISO; NYISO and NEISO are
   CALIBRATED-WITH-CAVEATS; ERCOT, CAISO and MISO are NOT-YET on their own
   rubric — ERCOT arithmetically capped there by two 2023 load-bearing fails
   (C3a −33.2%, C3b 0.604). Scarcity-tail formation (C3c) is the weakest front
   program-wide: five of six ISOs spend their single ledgerable caveat on it.
4. **PJM's CALIBRATED — the strongest public claim — is qualified three ways by
   the repo's own records**: the keeper solved on a since-proven input-clock
   defect (corrected candidate pjm-162 registered, awaiting owner promotion); a
   C6 attestation generated retroactively and carried forward from a prior run,
   with two committed records now disagreeing on whether the gate is attested;
   and a 2022 out-of-sample touchpoint that scored NOT-YET.
5. **Out-of-sample evidence now exists but is thin and non-quotable.** Two
   validation-tier 2022 touchpoints have been spent (NEISO
   CALIBRATED-WITH-CAVEATS on the second attempt after a zero-parameter input
   repair; PJM NOT-YET). The locked test (2019, H1-2026) has never been spent
   for any ISO. The forecast program's own board reads HOLD for all six ISOs at
   the T1→T2 gate: **no certified forward-skill number exists**.
6. **Positioning.** Operationally the model sits in the commercial zonal-PCM
   tier (Aurora-class chronology, PLEXOS-class reserve co-optimization,
   ahead of most tools on scarcity-price structure); its capacity-evolution
   half is below the co-optimized CEM class (ReEDS/GenX/PyPSA) by explicit
   design choice; its calibration-governance regime exceeds every surveyed
   comparator, whose only analogue is the regulator-driven SEM PLEXOS backcast
   series. Deliberate divergences from commercial practice — pure LP, dual-based
   pricing with scarcity overlays, one-pass evolution, non-leap 8760, zonal
   topology — are documented choices with stated rationales, not defects (§2).
7. **Release posture.** The committed record supports honest publication today
   of: the architecture, the governance regime, the per-ISO determinations
   including the three NOT-YETs, and in-sample accuracy at the cited grain.
   It does not support: quoting any out-of-sample or forward-skill number,
   presenting ERCOT/CAISO/MISO as calibrated, or presenting 2026–2050 outputs
   as validated forecasts. The gap register (§8) routes 18 items to the
   program's lanes; none is a stop-ship for publishing the model *as what it
   is*, several are stop-quote for specific claims.

## 2. What the model is

A condensed technical identity; the authoritative detail is the code (both doc
sets lag it — see gap register rows D2/D3).

**Formulation.** One ISO-agnostic LP per ISO-year: full 8,760-hour
chronological, hour-major variable layout (`src/market_sim/model/lp/layout.py:19`),
assembled vectorized in scipy.sparse and handed directly to HiGHS
(`model/lp/model.py:603,627`); pure LP, no binaries — a governing rule
(`model-methodology-spec.md:1241`). Plant-level ERCOT reaches ~13.2M columns
(corroborated in-code at `model/lp/model.py:40`). Production runs are exactly
two solves per year: a cold P0 base-cost solve discovers run patterns, then P1
re-prices with bid costs (startup-amortization markup, per-class band
multipliers, and the optional fuel-invariant net-revenue gas-offer margin) via
`changeColsCost` warm-start on the same basis (`pipeline/solve.py:124,11-20`).
The legacy P2 commitment pass is archived behind `--enable-legacy-p2`
(`model-methodology-spec.md:316`). Warm-start levers (intra-year, cross-year
basis, persisted year-1 basis) are shipped with a basis-independence neutrality
argument (`pipeline/basis_cache.py:17-22`).

**Price formation.** Prices are LP duals on the energy-balance rows, recovered
at `model/lp/model.py:1087`; RPS-row duals are REC prices, capped by
construction at each region's ACP via escape columns (`model/lp/layout.py:71-79`).
Scarcity enters two ways, and the lane matters: (a) **in-LP reserve
co-optimization** with per-ISO reserve designs (`model/reserves/spec.py`),
including ERCOT ORDC demand steps — this is the mechanism live in backcast
keepers; (b) **post-solve overlays** — the published-formula ERCOT ORDC/RTORPA
adder (`results/scarcity.py:16-32`) and NYISO RCPF (`results/rcpf.py`) — which
in the forecast runner feed the capacity-economics price signal
(`runner.py:3109`, "persisted results are untouched"), except CAISO where the
overlay does move scored prices (`runner.py:3192`, rationale at `:3121-3126`).

**Capacity evolution.** A deliberate one-pass annual loop, never an equilibrium
iteration (`model-methodology-spec.md:728,1244`): confirmed exits → announced
retirements (fossil default-deferred to economics) → CCS retrofit-or-retire →
economic retirement on attainable pro-forma inframarginal margin (never
realized dispatch — `model-methodology-spec.md:771`) → known additions →
economic entry → optional adequacy backstop (default off) → dispatch with RPS
as an LP row (`model/capacity_evolution/evolve.py:82`). Retirement screens ride
published accreditation bases with ELCC curves; an accredited-basis reliability
floor un-retires cheapest-adequacy-first with a persisted ledger.

**Scope.** Six ISOs sharing one LP (`config/iso_configs.py:1203-1216`): ERCOT 7
zones (the calibrated reference), CAISO 6 (SP15 split into LCT-sourced
local-capacity areas 2026-07-09, `iso_configs.py:398-409`), MISO 6, PJM 8,
NYISO 5, NEISO 5 incl. the HQ import node. (Both the methodology spec and
CLAUDE.md still carry CAISO's pre-split "3 zones + WECC import" — gap D2.)
Transmission is pipe-and-bubble with interface groups and measured seam
ladders; priced interchange is modeled as import tranches / export sinks with
per-hub repricing. Fixed non-leap 8760 calendar on a standard-time clock, with
the DST-artifact rationale documented (`utils/hour_calendar.py:12-21`).

**Data layer.** 93 modules / 51,417 lines; EIA-860/923/930, EPA CAMPD/CEMS,
eGRID, ISO disclosures, through a schema-validated raw→clean contract (66
schema YAMLs, generated data dictionary, `data/dictionary/`). Results cache
keyed by a byte-stable `ScenarioConfig.cache_key()` with retired-field
re-insertion and path-invariance (`config/scenarios.py:12388-12420`).
`ScenarioConfig` carries ~695 registered fields; forecast vs backcast is an
explicit `mode` field, never inferred, and backcast measured overlays are
contractually barred from forecast mode (`docs/codebase/01-architecture.md:157-179`).

**Declared boundary.** The repo's own enumerated simplifications include: no
MIP/no binaries; no inter-hour ramp constraints; zonal not nodal (no PTDF, no
congestion/basis/FTR work at 3–8 zones); no marginal losses (one gated MISO
surface); perfect-foresight storage (upper bound on arbitrage, documented with
remedies ranked); perfect-foresight phantom reserve (corrected by the
online/offline split and measured supply caps); ~5% embedded curtailment in
non-HSL CF profiles; no multi-year cap banking; RCPF products not split by
ramp capability. These are disclosed design choices with stated rationales —
this audit treats them as scope boundaries, not defects, and the positioning
matrix maps them against comparator practice.

## 3. The validation and governance regime — how the evidence is produced

This section describes the machinery; §4 reports what it currently says. The
regime is unusual enough relative to industry practice (companion matrix,
"Validation norms") that it is itself a primary audit finding.

### 3.1 The determination rubric (machine-scored, versioned, owner-amended)

`docs/calibration-determination-rubric.md` — **rubric v3.2** at HEAD, enforced
by `scripts/calibration_verdict.py` (`RUBRIC_VERSION = 3.2`, line 252) — is the
single auditable definition of when an ISO backcast may be called calibrated.
The scorer reads committed artifacts only (registry sidecar, run payload,
benchmark parts, tail part, bundle `run_config.json` /
`calibration_attestation.json` / `legitimacy_diagnostics.json` — rubric §0a)
and emits PASS/CAVEAT/FAIL per criterion plus one of `CALIBRATED` /
`CALIBRATED-WITH-CAVEATS` / `NOT-YET`; re-running yields the same verdict.
Criteria at v3.2:

| Criterion | Tier | Gate |
|---|---|---|
| C1 fuel-mix by class (grid-delivered) | load-bearing | per-class volume within min(2% of load, 8 TWh) AND share within ±3 pp |
| C2 system volume, gas/coal families | load-bearing | defers to C1 for complete vintages; ±2.5%/±5% two-band on the preliminary-vintage EIA-930 fallback |
| C3a mean LMP (RT load-weighted) | load-bearing | ±10% |
| C3b monthly shape | load-bearing | NRMSE ≤ 0.20 |
| C3c scarcity tail (RT hourly, per-ISO threshold) | supporting | model within [0.5×, 2×] of actual (absolute ≤10 h when actual <10 h) |
| C4 fleet hourly dispatch correlation | supporting | r ≥ 0.70, NRMSE ≤ 0.30 (gas, coal) |
| C6 governance gate | protective | machine config check + four-assertion attestation; UNATTESTED ⇒ NOT-YET |
| C8 forced-energy share | protective | floor-forced share <15% peaker / <30% merchant, D-1 shape escalation |

Three structural properties matter for an auditor:

1. **Bands are externally anchored and move only by owner amendment, with the
   version history in the document itself** (rubric §9 and the banner chain
   v2.3→v3.2). The C3a ±10% band cites the accepted NYISO GE MAPS benchmark
   (−2% to −17% zonal) and the SEM/ECA regulator criterion; C3b's 0.20 cites
   the SEM backcast's seasonal biases; C3c's band exists although "no
   commercial or public model publishes tail-hour-count accuracy at all"
   (rubric §C3c). The anchor table is `docs/rubric-v2-benchmark-memo-2026-07.md`.
   One band (C1) was *loosened* on 2026-07-02 with its rationale stated in
   place — an auditor should note both directions exist on the record.
2. **Recent amendments narrowed, not widened.** v2.9 (2026-07-27) removed C5a
   CO2 from the determination because eGRID publishes no 2025 vintage — a
   criterion whose actual does not exist cannot be load-bearing. v3.1
   (2026-08-06) restricted the exceptions ledger to C3c alone, collapsed the
   caveat budgets 3→1 and 1→0, and retired C7 outright because its thresholds
   had no published external comparable. The measured effect of v3.1 was
   *adverse to the model's public claims* — CAISO fell from
   CALIBRATED-WITH-CAVEATS to NOT-YET and lost its `complete` holdout marker
   the same day, with the rubric history stating plainly that the earlier
   certification "certified a price level the model does not reproduce". A
   rubric that demotes its own keepers when tightened is operating as a gate,
   not as theatre.
3. **The rubric is explicitly built to fail keepers** ("If it could not return
   NOT-YET for a real keeper, it would be theatre" — rubric intro), and at HEAD
   three of six ISOs do fail it (§4).

The forecast side has a sibling: `docs/forecast-determination-rubric.md` (v1.0,
2026-07-17), scored by `scripts/forecast_verdict.py` over committed artifacts
only, with pre-registered bands ("Bands are never widened in response to a
result") and a T0→T3 promotion ladder whose determinations are promotion
claims, not accuracy claims.

### 3.2 Holdout discipline (three tiers, fail-closed, freeze-first)

`scripts/lib/holdout_policy.py` is the single home of the policy constants:
train = {2023, 2024, 2025} (line 52); validation tier = {2020, 2021, 2022}
(2018 removed 2026-08-06 with a substantive data reason); locked test =
{2019, 2026(H1)} (line 76), touch-once per ISO ever. Enforcement is three-fold
and fail-closed — `run_calibration_full.enforce_holdout_year_gate`,
`legitimacy_diagnostics.run_d6_quarantine`, and `audit_keepers` all import the
same constants, and `tier_for_year` returns the locked tier for any
unenumerated year. A spend **freeze**
(`frontend/data/backcast/holdout-freeze.json`) outranks both marker blocks and
is checked first; it is ACTIVE at HEAD. Data *intake* for out-of-training
years is a deliberately separate, no-LP channel requiring verbatim owner
authorization logged in
`frontend/data/backcast/calibration-complete.json:intake_log` — nine such
entries exist, each with its validation method recorded. Two honest asterisks
the repo itself documents: the non-`_full` script `scripts/run_calibration.py`
carries no year gate, and the validation-vs-locked distinction within the
marker mechanism is discipline, not machine enforcement
(`docs/calibration-and-validation-methodology.md` §3.2 asterisks; gap D6).

**Has a holdout year ever been spent?** Yes — twice, both validation-tier, both
under narrow owner lifts of the freeze, both recorded with the honest results:

- **NEISO 2022** (`2026-08-06-neiso-2022-corrected-basis`):
  CALIBRATED-WITH-CAVEATS out-of-sample — on the **second attempt**. The first
  touchpoint run (2026-08-05) scored NOT-YET with C3a/C3b degraded; the loop
  diagnosed a seasonally-inverted gas-basis *input* (EIA N3050MA3 LDC series),
  repaired it with zero free parameters, and re-keyed the touchpoint, with the
  superseded NOT-YET block preserved verbatim
  (`frontend/data/backcast/keepers/NEISO.json:holdout_touchpoint.rekeyed`).
  The record defends this as the rule-22 touchpoint loop working as designed —
  the fix was a data repair, nothing was fitted to 2022 — and this audit finds
  that defense supported by the artifacts; but a reader should know the good
  number is the second attempt at the year.
- **PJM 2022** (`2026-08-05-pjm-2022-touchpoint`): **NOT-YET out-of-sample** —
  C1 degraded (CC_REGULAR +18.28 TWh) and C3b degraded (NRMSE 0.206), recorded
  as-is in `frontend/data/backcast/keepers/PJM.json:holdout_touchpoint`. No
  re-tune was performed in response.

Both blocks carry the same mandatory disclaimer verbatim: "Validation tier:
ITERABLE model-SELECTION evidence, NOT a certified out-of-sample skill number
and never quotable as one."

**The locked test (2019, H1-2026) has never been spent for any ISO.** The
`final` block is deliberately empty for all six. The July peer review found one
governance record falsely asserting a NEISO locked-test spend; that record was
corrected on 2026-08-06 by owner decision D-23, the key renamed rather than
deleted "so the retracted assertion stays legible" — but the companion prose
methodology doc still carries the retracted claim as live fact (gap D1).

### 3.3 Reproducibility and anti-self-deception machinery

- **Byte-identity golden contract:** refactors are gated by
  `capture_keeper_goldens.py` before / `regression_gate.py --mode byte`
  (atol=rtol=0, `regression_gate.py:10-11`) after; a golden FAIL is a finding,
  never grounds to regenerate. The capture script's own docstring honestly
  bounds the claim: goldens are current-HEAD baselines under a determinism pin,
  "not byte-reproductions of the July-3 bundles," and the manifest hashes
  parquet content as a pre-screen, not file bytes.
- **Pre-registration is heavily practiced, not aspirational:** 206
  `PREREG*`/`PRECOMMIT*`/`PRECHECK*` documents across `docs/` and
  `results/calibration/`. Promotions execute under direction-blind rules that
  read only kill gates and LOYO, never the sign of residual movement — e.g.
  `docs/PRECOMMIT-ercot204-rtorpa-gate-and-rule26-successor-2026-08-15.md`
  §2.6, executed the morning of this audit; ercot202's precommit predicted its
  own null result ex ante.
- **Protective criteria with teeth:** C6 UNATTESTED alone forces NOT-YET —
  demonstrated live on candidate pjm-162, whose only determination blocker is
  exactly that (`docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §9); and
  the CAISO shard documents its own attestation gap being caught and repaired
  post-hoc, with the audit blind spot closed by a new check (E10) in the same
  session (`frontend/data/backcast/keepers/CAISO.json:disposition_note`,
  "THE SENTENCE ABOVE WAS ASPIRATIONAL WHEN WRITTEN").
- **Registered-run record:** 70 runs on the backcast dashboard
  (`frontend/data/backcast/registry/`), rejected probes included, under a
  top-15-per-ISO retention sweep plus owner site-retention directives — the
  dashboard is a pruned window (an auditor cannot reconstruct the full ≥400-solve
  search from it; the calibration logs can: 39,089 lines / ~849 headed entries
  across `docs/calibration-log/*.md`). 984 entries under `results/calibration/`
  (330 FINDING records); a 10,139-line adjudicated mechanism-test matrix
  (`docs/mechanism-testing-matrix.md`; sharded machine ledger with keeper-stamp
  drift guards, `scripts/check_mechanism_matrix.py:12-42`).
- **Keeper-promotion hygiene:** every keeper shard carries the promotion
  rationale, the superseded keeper's note preserved verbatim, and structural
  promotions with zero metric gain are labeled as such (ERCOT ercot-204:
  "NO METRIC GAIN IS CLAIMED, BECAUSE NONE EXISTS BY IDENTITY: all 12 committed
  hourly sidecars are sha256-IDENTICAL").

## 4. What the evidence currently says — per-ISO state at 2026-08-15

Keepers move daily (all six changed since the program plan's 2026-08-13
snapshot; ERCOT changed again the morning of this audit). Everything below was
read fresh at HEAD `9f48419` from `frontend/data/backcast/keepers/<ISO>.json`,
`frontend/data/backcast/status/<ISO>.js` (rubric-3.2 machine verdicts), and the
per-keeper verdict artifacts. All six keepers score years 2023–2025, zero
data-blocked years. `complete` (validation-tier) holdout markers: NEISO, NYISO,
PJM only; the `final` (locked-test) block is deliberately empty for all six
(`frontend/data/backcast/calibration-complete.json`).

### 4.1 Determinations and headline scores

| ISO | Keeper | Determination | C3a mean-LMP error (2023/24/25, band ±10%) | C3b shape NRMSE (≤0.20) | C3c tail model-vs-actual h |
|---|---|---|---|---|---|
| PJM | `2026-08-04-pjm-152-collapse` | **CALIBRATED** (sole) | +6.2 / −0.6 / −7.7% | 0.160 / 0.119 / 0.140 | 3v6, 10v18, 32v59 (all PASS) |
| NYISO | `2026-08-08-nyiso-133-cod-arm` | CALIBRATED-WITH-CAVEATS | +8.8 / +0.8 / −3.4% | 0.130 / 0.172 / 0.155 | 21v10 (2.1×, over-fired), 3v12, 24v42 |
| NEISO | `2026-08-14-neiso-93-envelope` | CALIBRATED-WITH-CAVEATS | +3.4 / +5.7 / +2.0% | 0.086 / 0.159 / 0.055 | 0v15, 0v8, 0v20 (tail collapsed) |
| ERCOT | `2026-08-15-ercot204-rule26-delete` | **NOT-YET** {C3a-2023, C3b-2023} | **−33.2** / −0.8 / −7.5% | **0.604** / 0.135 / 0.096 | 58v181, 22v53, 1v31 |
| CAISO | `2026-08-09-caiso-188-d1-micseam` | **NOT-YET** {C3a-2024, C3a-2025} | +3.4 / **+10.4** / **+12.9**% | 0.075 / 0.145 / 0.164 | 0v47, 1v35, 0v8 |
| MISO | `2026-08-09-miso-148-basis-aware` | **NOT-YET** {C3a-2025, C3b-2025} | −2.0 / −8.0 / **−15.6**% | 0.082 / 0.125 / **0.212** | 0v30, 4v37, 0v88 |

Supporting and protective rows: C4 fleet hourly dispatch correlation is
uniformly strong and passes everywhere (gas r 0.82–0.99 across all 18
ISO-years; coal SKIPPED-immaterial for CAISO/NEISO/NYISO, so C4 is a gas-only
test in half the fleet). C1/C2 pass on all six — but every ISO's 2025 fossil
classes are SKIPPED under the preliminary-EIA-923 completeness rule (5–8
classes per ISO), with the ungated residuals recorded honestly (e.g. MISO 2025
gas −9.9%). Roughly a third of the class-mix evidence in the most recent
training year is therefore not gated at all — recorded as SKIPPED, never
silently passed. C8 passes on PJM and MISO only via the grounded-above-budget
escalation (MISO 2025 ST_GAS forced share 48.4% against the 30% cap, resting
on its D-4 window + D-1 shape evidence).

### 4.2 Reading the table honestly

- **Scarcity-tail formation is the model's weakest front, program-wide.** Five
  of six ISOs spend their single ledgerable caveat slot on C3c, and the misses
  are large (NEISO and MISO carry fully collapsed tails in two-plus years;
  NYISO 2023 over-fires at 2.1×). PJM is the only clean three-year C3c pass.
  Under rubric v3.1's narrowing this is the *only* criterion a ledger can
  excuse — the caveat budget is fully consumed on the same phenomenon almost
  everywhere.
- **ERCOT's NOT-YET is arithmetically capped, not pending.** Two load-bearing
  2023 fails + a one-slot ledger already spent on C3c means no C3b work can
  change the determination while C3a-2023 (−33.2%) stands; the owner signed
  "hold NOT-YET as the honest public claim" (card R-A,
  `docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md`). The six
  ERCOT promotions since 2026-08-05 produced zero movement on the binding 2023
  criteria — they were structural/legitimacy repairs, explicitly labeled as
  claiming no metric gain
  (`docs/ASSESSMENT-ercot209-2023-scarcity-calibration-path-2026-08-15.md`).
  One inherited named permanent limitation stands: the offer-surface family's
  P0 bit-identity proof is forfeited on this keeper (ercot-188/E2, quoted in
  the keeper shard).
- **CAISO's fails are the exact residuals it used to ledger.** +10.4%/+12.9%
  (2024/2025) were carried as ledgered caveats under CALIBRATED-WITH-CAVEATS
  until v3.1 closed that route. CAISO's in-model lever queue is recorded EMPTY
  with the last free parameter a declared permanent residual and `final`
  recommended NO on executability (`docs/mechanism-testing-matrix.md` §5.2).
- **PJM's CALIBRATED — the program's strongest public claim — carries three
  unresolved qualifiers**, all from the repo's own records: (1) the keeper was
  solved on the PJM EIA-930 fueltype inputs that DEBUG-B has since proven ran
  one hour early in 2023–2024; the corrected-input candidate
  `2026-08-15-pjm-162-inputclock` is registered, scored (no criterion
  worsened), and awaits owner promotion
  (`docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §§1–3, 9). (2) Its C6
  governance attestation was generated retroactively at pjm-153 for a
  promotion that "shipped without one," carried forward from pjm-151 (with
  every premise recomputed, not typed —
  `results/calibration/pjm152_collapse_A/calibration_attestation.json:attested_by`);
  the committed status artifact scores C6 PASS / CALIBRATED
  (`frontend/data/backcast/status/PJM.js`) while the DEBUG-B finding's own
  like-for-like table scored the identical bundle C6 UNATTESTED / NOT-YET
  (finding §9 verdict table). Two committed records disagree about the
  program's strongest claim; this audit flags the discrepancy for resolution
  rather than adjudicating it (gap O2). (3) PJM's one out-of-sample number —
  the 2022 validation touchpoint — scored NOT-YET, and 2022 fueltype data
  remains on the uncorrected early clock (finding §6).
- **A cross-cutting caveat sits under every row above:** the holdout spend
  freeze's own stated basis — the 2026-07-25 CAMPD economic-layup finding that
  "every ISO books 23–46% of its CC capacity-year as outage against a real
  EFOR+planned norm of ~10–15%" (`frontend/data/backcast/holdout-freeze.json`)
  — remains unresolved. The availability envelope every keeper is calibrated
  against is flagged by the repo itself as likely to change materially. This
  is arguably a larger open threat to the accuracy claims than any individual
  criterion miss, and it is disclosed, not hidden (gap O4).

### 4.3 The forecast side — no ISO is validated for forward runs

The forecast program's own machine-scored board
(`frontend/data/forecast/program-status.json`, generated 2026-08-04) is
unambiguous: "No ISO clears the T1→T2 rubric gate at HEAD — all six read HOLD
… No ISO clears the §2.1b full-solve authorization gate either." FC-1
(structural invariants) FAILs for all six; ERCOT/PJM additionally fail FC-4
(crossover CO2); T2/T3 are deferred — "unschedulable until the full-solve gate
opens per ISO." The board's own framing is creditable: "Ten hours of compute
today would buy a mechanically-clean but structurally-flawed golden run.
Compute is not the binding constraint; the T1-F structural blockers are." The
forecast rubric certifies ladder promotion, never accuracy, and nothing has
been promoted. **No certified out-of-sample or forward-skill number exists for
any ISO**, and none may honestly be quoted.

Honest-claims check the charter requires: **ERCOT's public claim is NOT-YET and
this audit confirms it is still the honest claim at today's keeper** — the
basis has moved from the plan's dated citation (ercot-193 / card R-A) to
ercot-204's own promotion record, which carries the determination unchanged
with sha256-identical sidecars
(`docs/FINDING-ercot204-rtorpa-gate-and-rule26-2026-08-15.md`;
`frontend/data/backcast/keepers/ERCOT.json`).

## 5. What changed since the 2026-07-19 peer review

The July review's five open validity risks (its §6.3), re-examined at HEAD:

| July finding | State at 2026-08-15 |
|---|---|
| "The holdout program exists only on paper" + one overstated governance record | **Materially changed.** Two 2022 validation touchpoints spent (§3.2). The false NEISO locked-test claim was corrected by owner decision D-23 (2026-08-06) — but the stale prose methodology doc still repeats it (gap D1). Locked tests remain unspent by design. |
| "The CI enforcement described in the governance rules does not exist" | **Partially changed, new problem found.** `ci.yml` now exists with the quarantine/cache-key/mechanism-matrix guard jobs and the first completed runs are on record (31765772123 et seq., 2026-08-14). But the fast test tier has *never* completed on main's CI — the repo's data mass exceeds standard-runner disk/RAM (measured: 2 vCPU / 7.8 GiB / 15 GB free vs a ~17.7 GiB checkout), and `golden-data-tier.yml` is green-but-fragile (2 of 3 dispatches OOM-killed; the green "a capacity coin flip"). Root cause measured, fixes prototyped and runner-validated on PERF-A's NOT-FOR-MERGE branch — the first complete fast-tier CI run in repo history ran there, not on main (`docs/handoffs/perf-recheck-2026-08.md` §1; `docs/handoffs/debug-sweep-2026-08.md`). Gaps P1/P2. |
| Coefficient identification fragile out-of-training (D-8) | **Unchanged in substance; one closure attempted and honestly failed.** The CAISO CT-drag closure lane re-ran the A/B post-P2-archival and recorded "STILL FAILS" — the drag stays, its gap (G-15) stays open (`docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md`). The D-8 record (`docs/out-of-sample-results-2026-07.md` §2) stands. The two 2022 touchpoints are the first out-of-training evidence bearing on it: PJM's degradations are consistent with the concern; NEISO's second-attempt pass is mildly reassuring. |
| Measured-input saturation concentrates skill on gas/coal/CT; D-10 unpublished | **Remediated.** The D-10 free-class rescore is now implemented in the verdict scorer (`scripts/calibration_verdict.py:330-337, 2335-2344`) and appears in committed verdicts per keeper (e.g. NEISO "C1 all 12/12 · free 8/8"; pjm-162 "C1 all 16/16, free 12/12"). The July recommendation was executed. |
| Selection pressure structural (≥400 solves on 3 years) | Unchanged in kind; the countervailing discipline strengthened (v3.1/v3.2 narrowing, direction-blind precommits, 206 pre-registration docs). The dashboard remains a pruned window (top-15 + owner retention directives); the full search history lives in the calibration logs. |

Additional deltas an outside reader needs:

- **Rubric v2.x → v3.2** (§3.1): C5a removed (no 2025 eGRID vintage), C7
  retired (no external comparable), exceptions ledger narrowed to C3c with
  budget 1. Net effect adverse to headline claims (CAISO demoted). The July
  review's accuracy table (its §5) therefore no longer maps 1:1 onto current
  scoring — it should be read as a v2.x-era snapshot (gap D5).
- **Every keeper moved** since 2026-07-19, several on structural/legitimacy
  grounds with explicitly zero metric gain (§3.3). Keeper *replayability*
  decays as ScenarioConfig evolves: the superseded ERCOT-202 bundle and the
  pre-collapse PJM recipe are both recorded as unreplayable at HEAD, and two of
  the window's six promotions existed specifically to repair that decay.
- **A live solve-affecting input defect is mid-repair** (PJM input clock,
  §4.2), with candidate pjm-162 pending owner promotion (gaps O1/O3).

## 6. Positioning vs commercial and open models

Full nine-comparator matrix with public-source citations:
`docs/audit/model-positioning-matrix-2026-08.md`. The audit-relevant summary:

- **Formulation tier.** Pure-LP commitment with heuristic bridges places the
  model in the LP-relaxation/heuristic tier that Aurora, SERVM, and
  (historically) regulator-approved SEM PLEXOS occupy — below the MIP-SCUC
  tier (PLEXOS ST, EnCompass, GridView, nodal PROMOD) on commitment fidelity,
  identical in kind to ReEDS (pure LP) and to GenX/PyPSA/Switch in their LP
  configurations. Full-8760 chronology exceeds ReEDS/GenX/Switch practice
  (representative periods) and matches the commercial PCM norm.
- **Topology.** Zonal (5–8 zones/ISO) sits with Aurora/SERVM/ReEDS/Antares,
  below the nodal tier (GridView, EnCompass nodal, PyPSA-USA at full
  resolution). The model does not pretend otherwise: no congestion/basis/FTR
  claims.
- **Price formation.** Dual-based zonal pricing is the universal norm. The
  scarcity structure — in-LP ORDC demand steps, published-formula RTORPA
  overlay, nested RCPF stacking — exceeds documented commercial practice: the
  UT Austin ERCOT study found AURORAxmp approximating ORDC with a price adder
  and PLEXOS running "no scarcity pricing other than VoLL"; NREL's PLEXOS
  ERCOT study substituted administrative reserve-scarcity prices for the real
  ORDC. A reserve-shortage-indexed adder on LP duals is squarely within
  observed commercial practice; this model's in-LP variant is ahead of it.
- **Capacity evolution.** One-pass myopic screens sit below the co-optimized
  CEM class (ReEDS/GenX/PyPSA/Switch co-optimize builds/retires, some with
  foresight) and below PLEXOS LT Plan/EnCompass integrated expansion; the
  closest commercial analogue is Aurora's iterative LTCE. This is a documented
  deliberate divergence (`model-methodology-spec.md:728`), and the model is
  distinctive in embedding a PCM-grade 8760 LP *inside* the evolution loop
  rather than soft-linking CEM→PCM (the NREL Cambium pattern).
- **Calibration/validation.** No surveyed comparator publishes a machine-scored
  determination rubric, pre-registration protocol, or holdout policy. The only
  formal backcast practice found is regulator-driven (SEM Committee's recurring
  PLEXOS input-validation and backcast reports, produced with NERA); WECC's
  GridView ADS manual validates *datasets*, not model output; open models
  validate per-study. This repo's regime — machine-scored bands anchored to
  published comparables, published failures, three-tier holdout — exceeds the
  documented practice of every comparator. The honest counterweight: the SEM
  series is regulator-audited and this repo's regime is self-administered, and
  the comparators' commercial deployments carry decades of adversarial
  stakeholder review in IRP dockets that this model has never faced.
- **Runtime.** ~183–339 s per ISO-year (measured baseline) for a ~13.2M-column
  plant-level LP is credible performance for full-8760 zonal work; no
  comparator publishes comparable numbers at comparable grain (vendor runtimes
  are not public; open-model runtimes are configuration-dependent).

## 7. Fitness-for-purpose

Assessed against the model's own statement of intended use (rubric §0: six
uses — multi-ISO price forecasting 2026–2050, dispatch/mix, emissions,
capacity-evolution scenarios, policy analysis, probability bands), the current
determinations (§4), and the out-of-sample record (§3.2, §4.3).

**Credible today (in-sample-supported, PJM/NYISO/NEISO):**

1. **Scenario and policy-mechanism analysis** in the three passing ISOs —
   carbon/RPS/IRA designs enter as real structure (constraint rows and duals,
   REC prices ACP-capped by construction); scenario *deltas* are less exposed
   to fitted-level error than absolute levels.
2. **Zonal price-level, shape, and revenue-environment studies at annual and
   monthly grain** in PJM/NYISO/NEISO, where C3a sits within ±9% in every year
   and shape NRMSE within 0.17 — at or above the demonstrated commercial grade
   (GE MAPS −2..−17% zonal; SEM ±10% monthly criterion).
3. **Dispatch-timing studies** — gas-fleet hourly correlation 0.82–0.99 across
   all 18 ISO-years is strong at a grain no vendor publishes.
4. **Market-design what-ifs on represented mechanisms** (ORDC parameters,
   reserve demand curves, RA must-offer, capacity-market vintages) — these
   exist as explicit structure.

**Usable with stated caveats:**

5. **ERCOT/CAISO/MISO applications** — NOT-YET on the model's own rubric.
   Mechanism studies and deltas: defensible. Level-sensitive conclusions
   (absolute prices, revenue adequacy): not yet, and the honest per-ISO fail
   sets say exactly which dimension is broken (ERCOT 2023 level+shape; CAISO
   2024–25 level; MISO 2025 level+shape).
6. **Scarcity-tail-sensitive work anywhere** — C3c is the program-wide weak
   front (§4.2); tail-hour counts, scarcity-rent sizing, and reliability-price
   duration conclusions inherit it. The *level* contribution of scarcity is
   inside C3a/C3b where those pass.
7. **Emissions accounting** — C5a is reported-only since v2.9 (no 2025 eGRID
   vintage); 2023–2024 CO2 comparisons carry their own released vintages and
   the per-plant CEMS-derived rate machinery is strong, but no CO2 number is
   currently determination-certified.

**Not credible today (and the repo does not claim otherwise):**

8. **Any quoted out-of-sample or forward-skill number** — none exists; the two
   validation touchpoints are labeled non-quotable; all six ISOs HOLD at the
   forecast T1→T2 gate.
9. **2026–2050 outputs presented as validated forecasts** — they are
   internally-consistent scenario arithmetic until the FF program's structural
   blockers clear and holdout one-shots run. This was the July review's bottom
   line and it remains true at HEAD, with the qualifier that the machinery to
   change it (forecast rubric, tier ladder, hindcast/crossover instruments) is
   now built and scoring.
10. **Out-of-scope by design:** nodal congestion/basis/FTR; RA certification
    (LOLE/ELCC production — the model consumes published ELCC); uplift/ELMP
    and multi-settlement DA/RT spreads; short-term operational forecasting;
    AC power flow.

## 8. Gap register

Each row tagged for routing per the program charter (DEBUG / PERF / DOCS /
SITE / OWNER). "Evidence" cites the committed artifact that establishes the
gap. Items marked ▸ were already chartered by other lanes before this audit;
they are registered here for completeness and routing confirmation.

### PERF

| ID | Gap | Evidence | Routing note |
|---|---|---|---|
| P1 ▸ | Fast test tier has never completed on main's CI (checkout dies at repo data mass vs 2-vCPU/7.8-GiB/15-GB runners); first-ever green run exists only on PERF-A's NOT-FOR-MERGE branch. Blocks G2's "fast-tests green" leg and any required-check branch protection. | `docs/handoffs/perf-recheck-2026-08.md` §1.2–1.3; `docs/handoffs/debug-sweep-2026-08.md` CI health | PERF-B merges the tested sparse-checkout block (runner-validated, run 31873178938) |
| P2 ▸ | `golden-data-tier.yml` green is "a capacity coin flip": `curate_emissions` peak RSS 10.04 GiB vs 10.8 GiB ceiling; 2 of 3 dispatches OOM-killed. Blocks G3's proof mechanism. | `docs/handoffs/perf-recheck-2026-08.md` §1.1, §1.5; `docs/bloat-removal-report-2026-08.md` §4 | Low-mem prototype measured green (6.39 GiB); GOLDEN-TIER-FIX lane already chartered (plan §8, 2026-08-15) |

### DEBUG

| ID | Gap | Evidence | Routing note |
|---|---|---|---|
| B1 | ~~`scripts/run_calibration.py` (non-`_full`) carries no holdout year gate — the one solve entry point outside the three-gate enforcement.~~ **STALE — CORRECTED 2026-08-18 (AUDIT-FOLLOWUP, measured while tracing the gate's call sites for row O5).** The script **does** carry the gate, at `scripts/run_calibration.py:5888`: `rcf.enforce_holdout_year_gate(args.year, iso, args.holdout_authorized)`. It **delegates** to `run_calibration_full.enforce_holdout_year_gate` rather than importing `holdout_policy` directly — deliberately, “rather than a second copy of the policy (the `replay_keeper.py` / `backfill_nonfossil_hourly.py` pattern)” per the comment above the call, and stated in the module docstring at line 15 — which is why the import-grep that produced this row missed it. **No code change needed.** The row also named the wrong script: the genuinely ungated solve entry point was `scripts/knob_jacobian.py`, which no row had; found and fixed under row O5. | `scripts/run_calibration.py:5883-5888` + module docstring line 15; `AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §3 | **STALE — no action**; the real instance of this gap class is closed under O5 |
| B2 | PJM keeper replay is non-hermetic in a fresh clone: needs a ~2 h `data/clean` rebuild plus a live licensed PJM DataMiner fetch (intermittent 502s through the proxy). Material for any rule-15 same-session registration lane. | `docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §8 | Fold into PJM replay charter templates (with DOCS) |

### DOCS

| ID | Gap | Evidence | Routing note |
|---|---|---|---|
| D1 | **`docs/calibration-and-validation-methodology.md` carries the retracted NEISO locked-test claim as live fact** ("scored once … and stands", §3.2), a stale marker roster, a stale frontier roster (§5), and a v2.4 header against rubric v3.2 — with no correction notice. Every other retraction in this repo carries visible provenance; this one was missed. An outside reader of the "authoritative prose reference" would be misled on whether a locked-test year has been spent. | that doc §3.2/§5 vs `calibration-complete.json` (D-23 correction, `locked_test_scored_on_WITHDRAWN`) and `keepers/NYISO.json:frontier_cleared` | Highest-priority DOCS item; small surgical edit + banner, distinct from the DOCS-A/B manual work |
| D2 | Doc/code divergences in the two architecture doc sets, enumerated: production solve count (spec/docs say three-solve; production is two, P2 archived), retirement-year defaults (spec says coal=1; code ships 3), CAISO/MISO zone counts (spec + CLAUDE.md say CAISO "3 + import"; code has 6), `dispatch.py`/`capacity.py` documented as monoliths but now facades over `lp/` and `capacity_evolution/`, "three subcommands" vs four (`matrix`), `retirement_reserve_margin` documented live but deleted, `constants.py` size, CSR-vs-CSC wording. | spot-verified this audit: `model-methodology-spec.md:308,316,768,777` vs `config/scenarios.py:2167`; `iso_configs.py:398-409,583-588` vs spec line 7 and `CLAUDE.md` "What This Is"; `docs/codebase/02:3`, `03:10`, `07:19`, `08:85-86,171-180` | Feed the DOCS-A gap-audit memo (DOCS-A never dispatched — this list is a seed, not a substitute) |
| D3 | `model-methodology-spec.md` still carries unmarked Phase-0 build-agent content: §2.3 "Critical Performance Rules for the Build Agent" (with performance targets off by 1–2 orders of magnitude vs measured wallclock), §7 "Build Agent Instructions", §6.1 pool-executor pseudocode contradicting the 2-worker cap, §4.1 config sketch. The as-built markers cover structural growth but not these. | `model-methodology-spec.md:501-510, 1173-1203, 1222-1251` vs `docs/handoffs/wallclock-baseline-2026-07.md` | Already chartered as DOCS-B spec surgery; register confirms scope |
| D4 | `pipeline/solve.py:38` docstring says forecast cross-year warm-start is "default-OFF" while the dataclass default is `True` (`config/scenarios.py:11602`) and the shipped posture is disarmed via `shipped_forecast_xyear_warmstart()` (D-10, sitting Addendum K.3). Three statements, one truth — make the docstring cite the posture resolver. | `pipeline/solve.py:35-46`; `scenarios.py:11602`; `docs/handoffs/perf-a-warmstart-decision-memo-2026-08.md` | One-line DOCS fix; PERF-A memo already recommends closing plan §6 decision 1 as overtaken |
| D5 | Stale quantitative snapshots that will mislead future readers: `docs/testing.md` "~355 files" (454 at HEAD); the July peer review's §5 accuracy table is v2.x-era and no longer maps onto v3.2 scoring (needs a dated-snapshot pointer, not a rewrite — it is a record). | `docs/testing.md:3`; `docs/third-party-peer-review-2026-07.md` §5 vs `status/<ISO>.js` | DOCS sweep |

### SITE

| ID | Gap | Evidence | Routing note |
|---|---|---|---|
| S1 ▸ | `index.html` hero still claims "two ISOs (ERCOT and CAISO)" (line 27) and "Ten interactive pages" (line 92) at HEAD — confirmed live this audit. | `index.html:27,92` | SITE-A seed list; held to Wave 4 by design (or the owner's two-line hotfix option, plan §2) |

### OWNER

| ID | Gap | Evidence | Routing note |
|---|---|---|---|
| O1 | **pjm-162 promotion decision.** The corrected-input PJM candidate is registered and scored (no criterion worsened); the keeper remains on the defective clock until promoted. At promotion: mechanism-matrix re-stamp of items 12–13 + `seam_flow_envelopes` becomes due, and the candidate bundle needs its own C6 attestation (it has none, which is its only determination blocker). **RESOLVED 2026-08-16 (DEBUG-MGR reissue): owner signed PROMOTE by in-session card; executed same sitting — C6 attestation generated with computed premises, D-5(b) re-verification CALIBRATED, keeper/status/marker re-keyed, `audit_keepers --iso PJM` PASS, rule-28 re-stamps landed, matrix check green. Record: `docs/calibration-log/pjm.md` pjm-163 entry.** | `docs/FINDING-debug-b-pjm-input-clock-2026-08-15.md` §4, §9 | Owner promotes; the plan's D-5 pre-authorization covered the repair, not the promotion |
| O2 | **PJM C6 attestation discrepancy.** `status/PJM.js` scores the keeper C6 PASS / CALIBRATED; the DEBUG-B finding's like-for-like verdict table scored the identical bundle C6 UNATTESTED / NOT-YET. The attestation file exists with computed premises (retro-generated at pjm-153, carried from pjm-151). Two committed records disagree on the program's strongest public claim — likely scorer/artifact-schema drift; needs a definitive re-score and a one-paragraph resolution note. **RESOLVED 2026-08-16 (DEBUG-MGR reissue): not scorer drift — the finding's incumbent column was the registration-time rubric-2.9 snapshot (pre-pjm-153 attestation); the definitive `calibration_verdict.py --run-id` re-score at `8a118e7` confirms pjm-152 = CALIBRATED / C6 PASS and pjm-162 = NOT-YET solely on the missing promotion-time attestation. Resolution note: `docs/handoffs/debug-sweep-2026-08.md` Addendum §A.1.** | `results/calibration/pjm152_collapse_A/calibration_attestation.json`; `status/PJM.js`; finding §9 table | Resolve before any public "1 of 6 CALIBRATED" claim ships |
| O3 | **PJM ≤2022 fueltype clock uncorrected.** The committed extract now carries two clocks (corrected 2023–2025, early ≤2022); any PJM training/validation on ≤2022 fueltype data — including the already-spent 2022 touchpoint — is on the early clock. Extension is a one-line change needing an owner charter. **RESOLVED 2026-08-16 (DEBUG-MGR reissue): owner signed the extension charter by in-session card and it executed the same sitting — 2018–2022 fueltype +1 h, byte-verified per the DEBUG-B §2a protocol, July centroids 11.72–11.81 all inside the astronomical gate, 2023–2025 blocks byte-identical; data repair only, no ≤2022 year solved/scored/registered, freeze untouched. Execution record: finding §6 annotation + `debug-sweep-2026-08.md` Addendum §A.2.** | finding §6 | Charter before any further PJM validation-ladder spend |
| O4 | **Holdout-freeze premise unresolved.** The CAMPD economic-layup finding (CC outage booking 23–46% vs ~10–15% norm) that grounds the active freeze is still open; every keeper's availability envelope inherits it. Larger open threat to the accuracy claims than any single criterion miss. **RE-VERIFIED AT HEAD 2026-08-18 (AUDIT-FOLLOWUP, NO LP, NO HOLDOUT YEAR TOUCHED) — STILL OPEN; THE NUMERIC PREMISE SURVIVES THE GUARD, THE *DETECTOR* QUESTION DOES NOT.** The merit-order guard was ADOPTED 2026-07-26 and every ISO's extract re-derived guard-on, so this row's July figure could not be carried — it was **re-measured**: post-guard `CC_REGULAR` capacity-weighted outage share is **14.2–36.7 %** with **17 of 18 ISO-years still above the 15 % norm ceiling** (2023/24/25 — ERCOT 15.5/16.2/16.8, CAISO 25.8/31.3/36.7, PJM 18.2/16.2/17.0, MISO 16.9/17.9/21.4, NYISO 25.4/29.6/35.8, NEISO 32.9/27.4/14.2 %); the pre-guard column reproduces this row's 23–46 % range at 17.2–42.5 %, which is the check that the construction matches the finding's. The guard removed 1–16 pp — real, but it brought no ISO but NEISO-2025 into the norm band, so **every current keeper does still inherit an out-of-norm envelope**. **WHAT HAS MOVED IS THE INTERPRETATION, AND THIS ROW'S ROUTING NOTE IS NOW WRONG:** “resolve the detector question” is **not** an available option — charter §9 records the investigation CLOSED ON EVIDENCE across FOUR lanes (published-side re-measure PASSED, +0.70…+0.85 against ISO-NE's published `uncommitted_available_gen_nonfast_mw` and −0.85…−0.86 against published outages; commitment-economics discriminator NEGATIVE at AUC 0.47–0.57 over 18 configuration-years; LP-side closure NEGATIVE — restoring the envelope injects a first-order **15–38 TWh of phantom dispatch** no plausible price feedback (≈ −$3–4/MWh) closes; cross-ISO day-grain replacement NEGATIVE at 82/180 cells, median gain −0.0003), establishing the over-count as a **definitional seam** (published series measure *unavailability*; the CEMS detector measures *non-operation*) that no admissible discriminator can close — and §9 RECOMMENDS closing with cause and lifting fully. On that reading the gap to the ~10–15 % norm is expected rather than defective, and the envelope deletion is definitionally impure but **operationally load-bearing**. Live downstream corroboration that the corrected envelope is consumed correctly: NYISO's own keeper `nyiso-140-layup-exclusion` is a rule-17 `[R-FLOOR-WINDOW]` repair that exists *because* the guard un-booked lay-up (Port Jefferson 2517 → ~100 % model availability, absorbing 72.6 % of the LI ST_GAS limb's forcing), zero free parameters. **WHAT THE FREEZE COSTS, MEASURED AT HEAD:** three ISOs hold `complete` (NEISO, NYISO, PJM) and **all three now read `CALIBRATED`** under rubric v3.3 — none did at the last freeze sitting on 2026-08-06; `final` is EMPTY; exactly **two** out-of-training runs are registered at HEAD (both 2022, both narrow owner lifts: `2026-08-06-neiso-2022-corrected-basis`, `2026-08-05-pjm-2022-touchpoint`) out of 26 registered runs; **zero locked-test spends ever**; and **NYISO has held `complete` since 2026-07-31 without ever spending a touchpoint**. The freeze's own `lifts_when` — *“either the corrected detector is adopted and each affected ISO's keeper is re-audited on the corrected envelope, or the charter is closed with cause”* — now reads as satisfied on **both** branches (§8 adoption + all six ISOs carrying a registered re-audit arm; §9 close-on-evidence). It stays ACTIVE correctly: no session lifts it by inference. **WHAT IS OPEN IS THE DISPOSITION ACT ALONE.** Owner card with quantified impact and three options (recommendation: **(A)** close the charter with cause, lift the VALIDATION tier only, leave `final` empty, carry the seam explicitly): `docs/audit/AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4. Probe `scripts/probes/audit_followup_o4_cc_envelope.py` → `results/calibration/_audit_followup_o4_cc_envelope.json`. **RESOLVED 2026-08-26 (owner ruling, program-director sitting card 6): option (A) SIGNED as recommended and EXECUTED the same sitting** — the charter is CLOSED WITH CAUSE (its new §10), and the freeze is re-scoped rather than lifted outright: `holdout-freeze.json` now carries `active: true` with `scope.tiers = ["locked_test"]`, so the VALIDATION tier (2020–2022) is spendable by ISOs holding a `complete` marker (NEISO/NYISO/PJM) under `--holdout-authorized`, while **2019 and H1-2026 stay frozen for every ISO, `final` marker or not** — enforced by the new fail-closed `holdout_policy.frozen_tiers` reader (no parseable scope ⇒ every tier frozen) and verified behaviourally across all three rule-22 enforcement paths, 55/55 invocations, including the locked-test refusal for all six ISOs with and without the flag. `final` is untouched and still empty. **The closure states its cause honestly: the detector/seam question REMAINS OPEN** — the 14.2–36.7 % post-guard envelope (17/18 ISO-years above norm) is carried explicitly as a documented definitional seam that every keeper's availability envelope inherits; the lift is a decision to proceed WITH that known-open input question because validation years are iterable and model-selection-only, not a finding that it closed. Execution + verification record: `docs/FINDING-holdout-governance-2026-08-26.md`. | `frontend/data/backcast/holdout-freeze.json`; `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §8/§9/§10; `results/calibration/_audit_followup_o4_cc_envelope.json`; `AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2; `docs/FINDING-holdout-governance-2026-08-26.md` | **RESOLVED 2026-08-26** — owner signed option (A); charter closed with cause, validation tier lifted (scoped freeze), locked test stays frozen, `final` empty; the seam question stays open by design and is carried explicitly, not silently accepted |
| O5 |**NEISO legacy-P2 anomaly — RESOLVED 2026-08-17 (session neiso-99).** **CLOSED BY A RE-SOLVE, NOT BY A DOCUMENTED EXCEPTION.** The NEISO keeper is now `2026-08-17-neiso-99-joint-p1`, which persists `["P1"]` alone: all six designated keepers are on the production basis, and NEISO's published numbers and scored determination no longer come from the archived pass. The seam that propagated it is closed in the same change — `run_replay_bundle` and `replay_keeper.main` rebuilt their kwargs from `meta.json` **after** `_enforce_legacy_p2_gate` had run on parsed CLI args, so `commitment=true` re-armed P2 invisibly on every replay (which is how it crossed three keeper generations with no operator decision anywhere); `enforce_legacy_p2_kwargs` now gates the **reconstructed recipe** at both entry points and **hard-fails** rather than silently rewriting it (a silent rewrite would be the miso-50..53 lossy-reconstruction class). Unlock with `--enable-legacy-p2`, or move a recipe onto the production basis with `--set commitment=false`. **WHAT THE CHANGE COST, REPORTED AT FULL MAGNITUDE:** mean λ −0.0575 / −0.0110 / −0.0378 $/MWh for 2023/2024/2025 and the **2024 annual maximum of the max-across-zones price $256.93 → $218.24** — P2 had been standing **17.7 % above P1** on that price-formation statistic. **THE BASIS CHANGE IS A PURE RE-RENDER AND THAT IS MEASURED, NOT ARGUED:** the same-HEAD basis-only control `2026-08-17-neiso-99-basis-p1` (registered) is **BIT-IDENTICAL** to the superseded keeper's own persisted P1 in `system` / `class_hourly` / `reserve_family`, all three years, **0 differing cells of 192,720 rows per year** — P2 never fed back into P1, it was only ever what got published. **Determination UNCHANGED** at CALIBRATED-WITH-CAVEATS, criterion for criterion identical to the superseded keeper (0 FAILs, C3c the sole ledgered caveat, C1 all 12/12 · free 8/8); **no gate was traded**, and rule 22 D-5(b)'s worse-determination stop did not fire. The **frontier declaration was re-established on the new keeper's own sidecars** rather than carried forward (mandatory — this is the first NEISO keeper change since neiso-93 that is not a dispatch no-op): C3c model tail 0 h > $300/MWh in all three years **on the production P1 basis**, which is strictly stronger than the pass-independence neiso-98 could claim. Settled together with the Stony Brook 6081 outage routing in ONE re-solve exactly as neiso-98 recommended, so the two are not confounded. Record: `results/calibration/ASSESSMENT-neiso99-p2basis-routing-2026-08-17.md`; prereg `PREREG-neiso99-p2basis-routing-2026-08-17.md` (pushed before either arm solved); probe `scripts/probes/neiso99_arm_decomposition.py` → `_neiso99_arm_decomposition.json`. **PRIOR TEXT, preserved:** **NEISO legacy-P2 anomaly.** NEISO is the only ISO scored on the archived P2 commitment pass (all 15 NEISO bundles `commitment=true`; other five ISOs all false); `run_replay_bundle` re-injects the flag after the CLI gate, so replays carry it forward invisibly. Materiality small but nonzero (mean LMP +0.011..0.058 $/MWh; 2024 max +18%). Escalated in the keeper shard; resolving needs a re-solve decision. **RE-MEASURED AT HEAD 2026-08-17 (session neiso-98, NO LP, NO RUN, keeper unchanged) — STILL OPEN, AND SHARPENED.** Re-measured on all six *designated keepers'* own `meta.json` rather than a bundle census: CAISO `caiso-197`, ERCOT `ercot213`, MISO `miso-160`, NYISO `nyiso-140`, PJM `pjm-162` all `commitment=false` / `passes ["P1"]`; NEISO `2026-08-17-neiso-97-dstrepair` `commitment=true` / `passes ["P1","P2"]` — sole ISO of six, neither resolved nor worsened across three keeper generations. **THE SHARPENING: "scored on P2" is now MEASURED rather than inferred** — the registered run payload is *rendered from* P2, established on the current keeper's own bytes by two independent routes agreeing in all three years (payload `HQ_import` mean λ matches P2 to 0.001–0.003 vs P1 errors 0.0585/0.0130/0.0411; payload `gmModel` per-class annual TWh matches P2 at 0.0714/0.0717/**0.0003** TWh vs P1's 0.0992/0.0795/0.0106). So every published NEISO number and the scored determination sit on the archived pass, not merely an extra solve. The 2024 annual maximum spread is confirmed at $218.24 (P1) → $256.93 (P2), +18 %. **This does NOT disturb NEISO's frontier declaration**, which is pass-independent: the C3c model tail is 0 h > $300/MWh in all three years on BOTH passes. Best settled together with the plant-6081 Stony Brook outage routing (units 004/005 → `plant_group=CC_REGULAR`, 74 rows each, re-confirmed unchanged at HEAD) in ONE re-solve so the two are not confounded. Record: `results/calibration/ASSESSMENT-neiso98-frontier-verification-2026-08-17.md` §1.3/§4.1; probe `scripts/probes/neiso98_scored_pass_identity.py` → `_neiso98_scored_pass_identity.json`. `keepers/NEISO.json` frontier note item (5); `frontier.reverified` item (3)/(5) as re-stamped by neiso-98 Owner: authorize a P1-basis NEISO re-solve or document the exception **RE-VERIFIED AT HEAD 2026-08-18 (AUDIT-FOLLOWUP, NO LP) — CLOSURE HOLDS, AND HOLDS STRONGER THAN AS WRITTEN; ONE RESIDUAL FOUND AND FIXED IN-SESSION.** Re-derived from each designated keeper's own bundle `meta.json` on a **newer keeper set than the closing session could cite** — ERCOT and CAISO were both promoted after this row was written (`ercot213` → `2026-08-17-ercot215-arm-decontam`, `caiso-197` → `2026-08-17-caiso-200-h1-memberpanel`) — and all six read `commitment=false` / `passes [“P1”]`: ERCOT, CAISO, PJM `pjm-162`, MISO `miso-160`, NYISO `nyiso-140`, NEISO `neiso-99`. The production-basis property survived two promotions that happened after it was established. **THE RESIDUAL: the seam was closed at TWO of THREE paths.** neiso-99 gated `run_replay_bundle` and `replay_keeper.main`; `scripts/knob_jacobian.py::solve_year` (the standing D-11 knob-perturbation diagnostic) **also** rebuilds kwargs via `replay_keeper.build_kwargs(meta)` and calls `solve_and_persist` directly, and was gated by **neither** `enforce_legacy_p2_kwargs` **nor** `enforce_holdout_year_gate`. Both exposures are live, not hypothetical: two committed bundles still carry `commitment=true` (`neiso86_2022_corrected`, `neiso97_dstrepair_A`), and because the holdout gate lives at the *entry points* and never inside `solve_and_persist`, this script's free-`int` `--year 2019` would have solved a **locked-test year under an ACTIVE spend freeze** — while its own docstring asserted it “never touches the 2022/H1-2026 quarantine, rule 22”. Rule 22 names three gates; this solve path sat outside all three. (`run_calibration_full.py:3015` was checked and is NOT an exposure — it reconstructs prior kwargs only to *compare* them for `--reuse-solved` eligibility, never to solve.) **Second residual: the closure shipped with no test** — zero references to `legacy_p2` across all 460 test files at HEAD. **FIXED IN-SESSION, SOLVE-NEUTRAL** (fail-closed guards that change no solve's numbers and only refuse a solve that would otherwise run ungated): both gates added to `solve_year` ahead of `_load_reference()` and the solve, `--holdout-authorized` / `--enable-legacy-p2` threaded through `compute_jacobian`, and the docstring's rule-22 claim rewritten from an assertion into a citation of the enforcement; plus `tests/regression/test_recipe_replay_gates.py` (10 tests + 6 subtests) pinning the gate semantics — every `LEGACY_P2_KWARGS` name refused individually, the unlock, and that the refusal is a **hard fail that does not mutate the recipe** (a silent rewrite being the miso-50..53 lossy-reconstruction class) — pinning that all three replay paths call the gate, and pinning both knob-jacobian refusals with `solve_and_persist` asserted unreached. Verified that the `--year 2019` refusal fires on the **freeze** branch, ahead of both the flag and the marker. Record: `docs/audit/AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §1. | `keepers/NEISO.json` `note` / `disposition_note` / `frontier.reverified` as re-stamped by neiso-99; `calibration-complete.json` NEISO `keeper_rekey_history`; `AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §1 | **CLOSED** — no owner action outstanding; the 2026-08-18 residual was solve-neutral and is fixed |
| O6 | **Locked tests unspent; forecast validity still asserted.** The designed one-shots (2019, H1-2026) remain the single most important unexecuted step, as in July. The FF program's structural blockers (FC-1 for all six) gate the forward half. When keepers settle at G2, schedule the one-shots; a capacity-evolution hindcast (the July review's Cole & Vincent-style recommendation) remains absent — T1-H exists but four curve legs FAIL FC-3. **STANDING SCHEDULING POLICY RECORDED 2026-08-26 (owner ruling, program-director sitting card 7), verbatim: "Locked test is scheduled only after an ISO has run its 2020-2022 touchpoints and the loop has stopped surfacing repairs. Spends the one-shot against the most-prepared config, which is the whole design intent."** The precondition for any future `final` grant is therefore on record: 2020–2022 touchpoints run AND the loop quiescent make an ISO *eligible to be considered* — eligibility is not a grant, and `final` remains an explicit owner act per ISO every time. The two standing constraints restated so this is never read as a green light: NEISO's 2019 basis is UNREPAIRABLE (ISO-NE newswire migration mid-2018; Mar–Jun recaps never carried over) and its `final` readiness reads NOT YET on the merits; and NO ISO HAS EVER SPENT A LOCKED-TEST YEAR — `final` still carries only its `_note`, unchanged by the ruling. With the same sitting's card-6 validation lift, the touchpoint ladder this policy gates on is now actually runnable for the three `complete` ISOs. Recorded in CLAUDE.md rule 22 (locked-test bullet), `rule-history.md` §4, `docs/FINDING-holdout-governance-2026-08-26.md`. | `calibration-complete.json` `final._note`; `frontend/data/forecast/program-status.json`; `docs/governance/rule-history.md` §4 (2026-08-26) | **Standing policy recorded 2026-08-26; the grant itself remains an owner act, per ISO** — the one-shots stay unspent until an ISO clears the touchpoint precondition and the owner separately grants `final` |
| O7 | **ERCOT P0 bit-identity proof forfeited** (ercot-188/E2, unexpired): `ercot_econ_curve_top_refine` writes heat rates into the P0 objective, so offer-surface reproductions are whole-solve, not seam proofs. Disclosed in the keeper shard; restoration would need its own charter. | `keepers/ERCOT.json` promotion note | Accept-and-document or charter restoration |
| O8 | **NEISO SMD 2018–2023 workbook vintage is DST-naive** (found by neiso-96 during the H1-2026 intake, merged mid-audit): the committed LMP parquet is displaced by one hour on four days a year in those years — including in-sample 2023, which feeds the NEISO bench this audit's §4.1 numbers score against. Reported by that session, deliberately not repaired in an intake lane. **RESOLVED 2026-08-17 (DEBUG-B(NEISO), session neiso-97): owner signed the repair charter by in-session card (option A + promotion pre-signed on not-worse); executed same sitting.** Measured before the card: 562 hub cells across 2018–2023, max $40.17/MWh, six fabricated mean cells + one lost hour per year, C3c tail provably untouched. Value-preserving repair byte-verified per the PJM §2a protocol (2024–2026 blocks byte-identical; the twelve defective days now carry the market's published hours); keeper recipe re-solved full-span in ONE fresh bundle and promoted as `2026-08-17-neiso-97-dstrepair` — **dispatch bit-identical to the incumbent** (the instrument moved, the model did not), determination CALIBRATED-WITH-CAVEATS criterion for criterion identical, D-5(b) re-verified, `audit_keepers --iso NEISO` PASS 0/0. Not solve-affecting for NEISO (the routing note's "likely solve-affecting" resolved: no NEISO recipe flag consumes the series) but IS a live NYISO solve input via `nyiso_import_hub_prices` — filed for the NYISO lane. Record: `docs/FINDING-debug-b-neiso-smd-clock-2026-08-17.md`; `docs/calibration-log/neiso.md` neiso-97 entry. | `results/calibration/ASSESSMENT-neiso96-h12026-intake-2026-08-15.md` §1.4 (at `870c4c8`) | Owner: charter the repair (measured-input fix, likely solve-affecting → [R-ALLYEARS] re-solve) and re-score NEISO after |

---

*Prepared as the AUDIT-A deliverable. Repository citations verified at
`origin/main` @ `9f48419` (2026-08-15). No solve was run; no holdout year was
touched; no rubric band was moved. External-model claims rest on the public
sources cited in `docs/audit/model-positioning-matrix-2026-08.md` and were not
verified by hands-on operation of those tools.*
