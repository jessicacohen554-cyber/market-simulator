# Calibration Determination Rubric (v2)

Status: **canonical, machine-enforced. RUBRIC VERSION 2.4** (2026-07-06
fitness-for-purpose re-anchor + 2026-07-07 C8 grounded-above-budget escalation
+ 2026-07-09 C3a/C3b single-band re-set and C5a full-plant CO2 re-base
+ 2026-07-09 C3a/C3b like-for-like load-weighted actual basis —
`docs/rubric-v24-price-basis-memo-2026-07.md`; v1 history in §9). This document is the single
auditable definition of when an ISO backcast may be declared *calibrated*. It
replaces the ad-hoc, per-run sidecar judgement (“this looks good enough”) with a
fixed rubric that a scorer reproduces byte-for-byte:
`scripts/calibration_verdict.py` reads a keeper’s committed artifacts and emits
a `PASS` / `CAVEAT` / `FAIL` per criterion and one overall determination —
`CALIBRATED`, `CALIBRATED-WITH-CAVEATS`, or `NOT-YET`. Re-running it on the same
keeper always yields the same verdict.

**What the determination certifies (v2).** `CALIBRATED-WITH-CAVEATS` certifies
that the model **delivers on its intended uses (§0) at or above the
demonstrated commercial-model grade** on every load-bearing criterion, with
every deviation either inside an evidence-anchored commercial band (listed) or
an explicitly ledgered measured-input limitation (budgeted). `CALIBRATED`
additionally requires every criterion at the stricter *target* grade with
nothing unscored. Both determinations remain conditional on the protective
anti-self-deception gates (C6/C7/C8) — those are UNCHANGED from v1 and are what
make the accuracy claims believable at all. Every band in this rubric is
anchored to a *published external benchmark* wherever one exists
(`docs/rubric-v2-benchmark-memo-2026-07.md` — the comparison table is also on
the Calibration Status dashboard page); where no published comparable exists,
the rubric says so and states the internal rationale instead.

This rubric **codifies the governance rule in `claude.md`** (measured/defensible
over what-fits, rules #1, #11, #12): a run is a keeper because it is the most
structurally faithful, *not* because it has the lowest error, and a determination
of “calibrated” is a claim that the model’s *mechanisms* reproduce the market —
not that its residuals were tuned to zero. The rubric certifies **fitness for
purpose**; it never picks keepers by MAE. It remains built to
**fail a current keeper**: any out-of-tolerance criterion that is not explicitly
documented as an accepted measured-input limitation forces `NOT-YET`. If it could
not return `NOT-YET` for a real keeper, it would be theatre. (At the v2
re-score, four of six keepers still score `NOT-YET`.)

Downstream consumer: `docs/forecast-validation-plan.md` Phase 3 (statistical-mode
dispatch backcast) uses this determination as the gate that backcast tuning has
“reached an acceptable state” before the forecast-validation program starts. A
`NOT-YET` ISO is not yet eligible to seed the forecast-error prior.

---

## 0. Statement of intended use — what this model is asked to deliver

The backcast test exists to certify the model for its actual jobs. The owner’s
known use cases:

1. **Multi-ISO price forecasting, 2026–2050** — annual and monthly
   load-weighted price levels and seasonal shape per ISO, feeding plant
   pro-forma revenue, retirement/entry screens, and portfolio valuation.
2. **Dispatch & generation-mix forecasting** — annual generation by plant
   class (the coal/gas/renewables balance and its evolution), the basis of
   every capacity-evolution and fuel-demand result.
3. **Emissions forecasting** — system CO2 per ISO-year, feeding policy and
   portfolio carbon accounting.
4. **Capacity-evolution scenarios** — retirements, new entry, storage growth
   under scenario assumptions; requires the *economic signals* (inframarginal
   margins, capacity value, duration-curve spread) to be right at annual scale.
5. **Policy analysis (RPS / carbon / IRA)** — differences between policy
   scenarios; requires the mix, CO2 and the price formation channel that
   policies act through.
6. **Probability bands (PB program)** — forecast distributions whose priors
   are seeded from backcast error; requires the backcast errors to be honest
   (protective gates) more than small.

**Criterion triage against those uses:**

| Bucket | What | Criteria |
|---|---|---|
| **LOAD-BEARING** — the test must certify these | Annual/monthly price level & seasonal shape (uses 1, 4, 5, 6); generation mix by class & family (2, 4, 5); system CO2 (3, 5) | C1, C2, C3a, C3b, C5a |
| **SUPPORTING** — informative, not certification-critical | Hourly dispatch timing (r/NRMSE); storage cycling volume/season; scarcity-tail hour counts (the *level* contribution of scarcity is already in C3a/C3b; the count is a diagnostic of the scarcity mechanism, and no intended use consumes exact tail-hour counts) | C3c, C4, C5b, C5c |
| **PROTECTIVE** — make the other rows believable | Governance (no residual fitting / pinning); diurnal-shape reality of the duty classes; forced-energy budget (floors are scaffolding, not dispatch) | C6, C7, C8 — **unchanged from v1** |
| **OUT OF REPRESENTATION** — the test must not demand these | RT sub-hourly transients (5-minute ramp scarcity, forecast-error re-dispatch — `docs/multi-iso/miso-scarcity-tail-diagnosis.md` §1); the DA−RT risk premium (DART) an offer-cost LP cannot price without fitting; hourly-exact dispatch of individual units (NREL TP-581-42305’s explicit guidance) | scored as report-only diagnostics (C3a DA row; C3c’s non-gated basis row — RT for DA-gated ISOs, DA for ERCOT since v2.6), never gated |

A criterion’s tier decides how its tolerance is set and budgeted (§1, §2) —
it does NOT decide whether a `FAIL` matters: **an undocumented `FAIL` on any
tier still forces `NOT-YET`** (supporting criteria carry wide,
gross-defect-catching bands, not exemptions).

---

## 0a. What the scorer reads (reproducibility contract)

The determination is reproducible **from committed artifacts only**. The scorer
never re-solves the LP and never reads the (gitignored) `dispatch/*.parquet` or
`system.parquet`. For a run it reads:

| Artifact | Committed at | Supplies |
|---|---|---|
| `frontend/data/backcast/registry/<id>.json` | sidecar | id, ISO, declared years, label, definition, bundle path |
| `frontend/data/backcast/runs/<id>.js` | run payload (gzip+base64) | model side: `gmModel` (grid-LP TWh by class), `fuelRows` (per-fuel model TWh + hourly r + NRMSE), `lmp` (model load-weighted price + monthly), `ordc` (ERCOT tail hours) |
| `frontend/data/backcast/bench/<ISO>/<year>.json.gz` | benchmark part | authoritative actuals: `classFull` (grid-delivered EIA-923−BTM TWh by class, vintage-reconciled), `e930` (EIA-930 grid totals by fuel), `avgLMP` (actual DA/RT mean + monthly) |
| `frontend/data/backcast/tail/actual_tail.json` | committed part (`scripts/derive_actual_tail.py`) | the C3c actual: per-(ISO, year) DA-expressible and RT scarcity-tail hour counts at the §5 threshold, with coverage fractions (2023–2025 only — rule-22 holdout guard in the deriver) |
| `results/calibration/<name>/run_config.json`, `meta.json` | bundle | governance config (outage source, lever flags), gas vintage |
| `results/calibration/<name>/calibration_attestation.json` | bundle (this rubric) | governance attestation + the exceptions ledger |
| `results/calibration/<name>/legitimacy_diagnostics.json` | bundle (S1 suite) | machine artifact of `scripts/legitimacy_diagnostics.py --json-out` — D-1 diurnal-shape rows and the D-2 per-class forced-share summary that C7/C8 score; the verdict never recomputes the diagnostics |

The model payload and benchmark parts are the **same numbers the dashboard
renders** (`scripts/render_calibration_html.py:build_payload`), so the verdict
and the dashboard can never disagree. The model side is the **grid-delivered
basis** (grid LP dispatch, no behind-the-meter CHP add-back); the actual side is
EIA-923 minus the per-class BTM host supply — model-grid vs actual-grid, per
`scripts/lib/session_score.py` and the 2026-06-14 directive.

---

## 0b. Benchmark basis — the actual-side construction (go-forward default, all ISOs)

**Owner directive 2026-07-12** (session_01SfBzT4EggvRfh35MYgoYXH): the actual-side
(benchmark) construction below is **THE default for every ISO**, unconditional —
no flag, no env knob, no `getattr` fallback can re-arm the retired basis
(CLAUDE.md rule 24). It is three mechanisms, all landed 2026-07-11/12 and pinned
by `tests/test_benchmark_basis_default.py` (the integration guard) plus the
per-mechanism unit tests. **The governing invariant: no raw EIA-930 per-fuel cell
ever gates a scored class or family number** — EIA-930's BA-reported gas/coal
attribution mis-splits vs CEMS by 7–21 TWh/yr, so it is used for the fossil
*level* only, never the *split*.

1. **G-21 combined-fossil reconcile** (`render_calibration_html.reconcile_vintage_classes`).
   The EIA-923 row-level + CAMPD-backfilled fossil total reconciles to EIA-930 as
   ONE combined gas+coal family — the fossil LEVEL is corrected (both directions,
   within `_VINTAGE_RECONCILE_FRAC = 0.97`) while the CEMS-validated 923 gas/coal
   SPLIT is preserved (every fossil class scaled by the same factor). The retired
   per-family reconcile scaled gas and coal each to their own unreliable EIA-930
   cell, manufacturing PJM's phantom "+21 TWh CC_REGULAR over-run" from a ~+3 TWh
   real miss. Log: 2026-07-11 "SCORER FIX (all ISOs)" + 2026-07-12 pjm-98
   promotion; `docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md`.
2. **#2049 unit-class CAMPD backfill bucketing** (`run_calibration_full._backfill_eia923_with_campd`
   × `_plant_class_shares`). A genuinely mixed non-ERCOT plant's CAMPD net is
   split across the classes physically at it by its measured EIA-923 prime-mover
   class shares, mass-preserving. The retired last-generator-wins path
   double-counted minority-class plants (PJM Linden p2406 ≈9.5 → ≈4.8 TWh),
   changing SCORED complete-year non-ERCOT benchmarks. ERCOT keeps its curated
   bin-sheet single-class path (`class_shares=None`), byte-identical.
3. **G-21b C2 preliminary-vintage split anchor** (`calibration_verdict.score_sysvol`
   + `_fallback_coal_anchor`). An incomplete family gates on the EIA-930
   COMBINED-fossil LEVEL with a **CEMS-anchored coal/gas split** — coal =
   CAMPD CEMS coal × the run's complete-vintage CEMS→923-grid ratio `k`; gas =
   930 combined minus that coal anchor — never the raw 930 per-fuel cell. The
   `e930.coal_cems` anchor is built inside `render_calibration_html` (its SOLE
   writer; an earlier post-hoc splice script was deleted 2026-07-12). Only when
   the anchor is unavailable (a bench part predating `coal_cems`, or no complete
   coal vintage in the run) does the explicitly-labelled legacy raw-930 fallback
   apply. All 18 committed bench parts carry `coal_cems`, so every re-score and
   every new registration already takes the anchor path.

**Determination flips under this basis are honest and stand** (pjm-98
CAVEAT→FAIL / PASS-reversal precedent): a number that moves because the benchmark
was corrected is a fixed defect, not a regression, and nothing may be tuned to
un-flip it (rules 1/13/23). Existing keepers re-score in place; frontier keepers
whose committed `classFull` predates fixes 1+2 are re-rendered on a controlled
re-solve by the owner (staleness inventory:
`docs/handoffs/benchmark-basis-inventory-2026-07.md`).

---

## 1. Criteria

Each criterion below names: **the metric**, **the authoritative actual source**,
**the per-year tolerance**, and **the failure classification** — `MODEL MISS`
(the model’s mechanism is wrong; do not paper over it) vs `ACCEPTED
MEASURED-INPUT LIMITATION` (the *actual* is itself partial/zeroed for a
documented, forward-valid reason, and the miss is not a model defect). A miss is
`MODEL MISS` **by default**; it is reclassified to `ACCEPTED MEASURED-INPUT
LIMITATION` only by a matching entry in the exceptions ledger (§3).

Criteria carry a **tier** (§0): `LOAD-BEARING`, `SUPPORTING`, or `PROTECTIVE`.
The v1 HARD/SOFT split is retired — it conflated strict data gates (C1/C2) with
the anti-gaming gates (C6/C7/C8); the protective tier keeps the v1 hard-gate
semantics unchanged.

**Two-band scoring (v2), graded load-bearing criteria only.** Where a published
external comparable exists (C2 family fallback, C3a, C3b, C5a), the criterion
carries TWO bands:

- **TARGET band** — the standard we hold ourselves to (unchanged from the
  2026-07-02 values). Inside → `PASS`.
- **COMMERCIAL band** — the demonstrated commercial/public-model grade,
  anchored to a citation (memo §2). Between target and commercial → an
  **auto `CAVEAT`** classified `WITHIN COMMERCIAL BAND (TARGET MISS)`: recorded
  with its magnitude, requires no ledger entry, and does **not** consume the
  caveat budget (§2) — it is inside the certification claim by construction.
- **Beyond the commercial band → `FAIL`**, reclassifiable only by an explicit
  measured-input ledger entry, exactly as in v1.

C1 (per-class mix) and the supporting criteria stay single-band: no vendor or
public model publishes per-class volumes, hourly fleet correlation, storage
cycling or tail-hour accuracy at all (memo §2 — we score STRICTER than
commercial practice there, deliberately, because the intended uses consume the
class mix while nothing external certifies it).

### C1 — Fuel-mix by class, grid-delivered  *(LOAD-BEARING, single-band)*

- **Metric:** annual generation by model plant-class, grid-delivered TWh.
- **Model:** `gmModel[class]` — the grid LP dispatch summed per class, **no CHP
  add-back** (the behind-the-meter host steam was held out of the LP, so it is
  not the model’s to dispatch).
- **Actual:** `classFull[class]` — EIA-923 Schedule-5 whole-plant net generation
  **minus** that class’s behind-the-meter CHP host supply (`btm.parquet`), i.e.
  grid-delivered generation by class. (Solar/wind are *not* in this gate — see
  C-VRE note; they route to EIA-930 per `calibration.actuals_source`.)
- **Per-year tolerance (the universal class gate).** A class passes iff
  **both** bands hold (mirrors `scripts/probes/_backcast_shell.py:classInTol`, so
  the determination and the dashboard scorecard agree):
  - **Volume:** the grid-delivered miss `|model − actual|` is within
    **`min(2.0% of ISO total load, 8 TWh)`** (`SUM_TOL_LOAD_FRAC = 0.02`,
    `SUM_TOL_LOAD_CAP = 8` — model grid-LP + non-fossil vs (EIA-923 − BTM) +
    EIA-930 nuclear/wind/solar). Total load = generation + net imports, so
    net-importing ISOs (NEISO, NYISO) get the correct ≈2 pp band; for
    energy-only ISOs with no interchange, load = gen and the band is unchanged.
    The percent term scales with system size (≈2 pp of load) but is **capped at
    an absolute 8 TWh** so the band can’t balloon on large ISOs (2% of an
    ~800 TWh system would be 16 TWh, letting a small steam-gas class drift far on
    the margin and still pass). Applied uniformly across classes and ISOs.
    Changed from generation to load basis on 2026-06-30; **loosened from
    `min(1.0% load, 5 TWh)` on 2026-07-02** (re-balance, §1-note below): the old
    band hard-failed keepers on ±1–2 TWh small-class residuals that are
    reporting/assignment noise, not a structural miss, while a genuine
    structural miss (e.g. MISO `CC_REGULAR` +47 TWh) fails the new band by ~6×.
  - **Share:** the class’s **share of total generation** is within **3.0
    percentage points** of the actual share (`SUM_TOL_SHARE_PP = 3.0`; loosened
    from 1.5 pp on 2026-07-02) — so a class cannot pass on volume alone while
    still misrepresenting the mix (MISO `CC_REGULAR` +7.7 pp still fails).
- **Excluded / again-excluded classes (each justified):**
  - **`CT_CHP` — excluded, every ISO.** A behind-the-meter cogeneration peaker
    whose output follows host steam demand and is held out of the grid LP; its
    grid-delivered model total is ~0 by construction, so a percentage error is
    undefined and an absolute band would penalise a class the model deliberately
    does not dispatch to the grid. (This is the exclusion already hard-coded in
    `session_score.py:judge`.)
  - **`OTHER` / `OTHER_FOSSIL` — excluded from the per-class gate** (kept in the
    C2 family totals). `OTHER_FOSSIL` is the coin-flip scoring bucket for
    genuinely-mixed gas-thermal plants (`apply_other_fossil_scoring`); it is a
    reconciliation device, not a real merit-order class, so a per-class band on
    it scores a labelling artefact rather than a dispatch decision.
- **Per-(ISO, class) completeness gate for a preliminary vintage (2026-06-27).**
  The per-class actual (`classFull`) is built from EIA-923 Schedule-5. A
  **preliminary** 923 vintage (current-year release, year ≥
  `PRELIM_923_FROM_YEAR` = 2025) under-reports because plants are still filing
  their monthly reports — at audit time the 2025 release carried only ~43% of the
  plants present in the complete 2024 vintage. Whether a given class is usable is
  **not uniform across ISOs and classes**: a class dominated by large always-on
  units that file early (e.g. ERCOT’s PRB/lignite coal fleet) can be fully
  reported while the peaker-heavy gas classes are not. So instead of a blanket
  per-year skip, a **completeness audit** (`scripts/audit_eia923_completeness.py`)
  measures, per (ISO, class), two vintage-internal signals — **plant-reporting
  retention** (of the prior complete year’s material plants, how many report this
  vintage) and **plant-month coverage** (how many of the 12 monthly cells the
  reporting plants carry). A class is flagged **`gate`** only when it is itself
  complete **and** its whole fossil family reported (so the vintage-reconcile,
  §C2, leaves its per-class actual un-scaled). The audit writes a committed part,
  `frontend/data/backcast/completeness/eia923_<year>.json`, that both this scorer
  and the dashboard read.
  - **Gated classes** (verified complete) score the full PASS/FAIL band exactly
    like a complete vintage. For 2025 that is **ERCOT `COAL_PRB` and
    `COAL_LIGNITE`** only.
  - **Every other fossil class** is recorded `SKIPPED` (not gated, never a silent
    pass), with the raw `model − actual` gap kept as a report-only annotation
    (`vintage_gap_twh`, plus a `completeness` tag). The **C2 family system-volume
    gate still covers these** via the authoritative EIA-930 grid reconcile (§C2).
  - Complete-vintage years (no completeness part — today 2023 and 2024) gate every
    class as before. The map **auto-extends**: re-run the audit as the 2025 release
    finalises and the now-complete classes begin gating with no code change.
- **Failure classification:** `MODEL MISS` by default — an out-of-tolerance class
  is a merit-order / offer-curve / must-run defect (e.g. CT_PEAKER under-dispatch
  ⇒ peaker offer band too high). Reclassify to `ACCEPTED MEASURED-INPUT
  LIMITATION` (a `CAVEAT`, never silent) where the *actual* is the limitation,
  e.g. **NEISO’s model-zeroed `CT_PEAKER`** (the ISO’s oil/gas peakers run a
  handful of scarcity hours the energy-only LP cannot see; the grid-delivered
  actual is itself near the measurement floor). (Preliminary-vintage years are now
  handled upstream by the complete-vintage `SKIPPED` rule above, not by a per-class
  vintage credit.)

### C2 — System volume error, gas & coal families  *(LOAD-BEARING; two-band on the preliminary-vintage fallback)*

- **Metric:** annual grid-delivered TWh summed over the **gas family**
  (`CC_REGULAR, CC_CHP, CT_PEAKER, CT_CHP, ST_GAS, ST_CHP`) and the **coal
  family** (`COAL_PRB, COAL_LIGNITE, COAL_BIT, COAL_WC, COAL`). Membership is the
  `plant_taxonomy.classes_for_fuel930` roll-up, not a hand list.
- **Model:** sum of `gmModel[class]` over the family (grid LP, grid-delivered).
- **Immateriality cut-off:** a family whose actual is **< 10 TWh** is *not*
  gated here — a band on a near-zero family (e.g. NEISO coal ≈ 0.3 TWh)
  is pure noise; its per-class C1 absolute band governs it instead. The criterion
  is recorded `SKIPPED` (“immaterial, governed by C1”) for that family.
- **Tolerance — folded into the per-class universal gate (2026-06-24).** C2 no
  longer applies a percent-of-family band to complete-vintage years. A
  family-aggregate percent band had two failure modes: it **invented** a fail
  when a mid-size family’s small absolute miss exceeded the band as a percent of
  *itself* (ERCOT coal +1.75 TWh = +3.0% of a 58 TWh family, yet only +0.3 pp of
  generation and well inside the C1 volume band), and it **masked** a
  real per-class miss when offsetting class errors **netted** across the family (a
  CT_PEAKER over-build cancelled by a CC under-build summing to ≈0% at the family
  level). The fix scores at the class scale, sized to the *system* not to the
  class, so neither tiny nor mid-size classes blow up and nothing nets:
  - **Fully-reported family (every complete vintage, plus a preliminary-vintage
    family the completeness audit flags complete — e.g. ERCOT coal 2025):** the
    family **defers to C1** — it passes iff every constituent class is within the
    universal per-class gate (|model−actual| within min(2.0% of ISO total load,
    8 TWh) **and** share within ±3.0 pp; actual = `classFull` = EIA-923 − BTM). C1 already
    scores these classes as a HARD criterion, so any breach surfaces there; C2
    records `PASS` and echoes any C1-flagged class in its magnitude (no independent
    family pass/fail).
  - **Preliminary, not-fully-reported family (e.g. every ISO’s gas family in 2025):**
    there is **no trustworthy per-class actual** (missing plants under-report;
    EIA-930 carries no per-class split), so the **family fallback** against
    the authoritative EIA-930 grid total is retained — the only volume check the
    data supports, with the EIA-930 incomplete-vintage handling made explicit.
    **v2 two-band on this fallback: target ±2.5% / commercial ±5%.** Anchors
    (memo §2): family-level generation-by-fuel is the finest grain any external
    validation publishes — NYISO’s benchmark held total energy to ~0.1% (load
    is an input) with zonal energy within ~0–4%; AEO short-horizon
    gas-generation error SD is 5.7–9.6% (a forecast-mode upper bound) — and
    this fallback’s own benchmark carries the 923-vs-930 reconciliation
    uncertainty, so a 2.5–5% residual is recorded as commercial-band, never
    hard-failed at a grain the data cannot support. The current-year EIA-923 release is a preliminary
    monthly survey that under-counts thermal generation the CAMPD backfill cannot
    fully repair. The benchmark applies `_VINTAGE_RECONCILE_FRAC = 0.97`
    (`render_calibration_html.py`): when the grid-delivered 923 family total falls
    **below 0.97 ×** the complete EIA-930 grid series the model is calibrated to,
    the family’s classes are scaled up to the EIA-930 total (inter-class split and
    monthly shape preserved); a complete vintage (≥ 0.97×) is left untouched
    (byte-identical). For the preliminary year the scorer therefore takes the
    **authoritative actual on the EIA-930 grid LEVEL**, so the model is compared
    against a *complete* benchmark, not a partial survey.
    - **G-21b split anchor (2026-07-12, §0b): the fallback level is EIA-930 but
      the per-fuel SPLIT is CEMS-anchored, never the raw 930 cell.** EIA-930's
      BA-reported gas/coal attribution is demonstrably unreliable against CEMS
      (−17..−21 TWh below CEMS on MISO coal, +7..+11 above on PJM, with the mirror
      error in NG:NG), so gating a preliminary family on the raw `e930[gas|coal]`
      cell fabricates misses of exactly that size. Instead an incomplete **coal**
      family gates against the CEMS anchor (`_fallback_coal_anchor`: CAMPD CEMS
      coal × the run's complete-vintage CEMS→923-grid ratio `k`), and an
      incomplete **gas** family against the 930 COMBINED fossil total minus that
      coal anchor. The raw 930 per-fuel cell is used only on the labelled legacy
      path (no `coal_cems`, or no complete coal vintage in the run). The scorer
      records which source fired.
- **Failure classification:** `MODEL MISS` by default (the fleet is delivering the
  wrong amount of gas or coal to the grid — fuel-price passthrough, must-run, or
  interchange wedge wrong). `ACCEPTED MEASURED-INPUT LIMITATION` only for the
  **preliminary-923 vintage** when the residual sits inside the vintage’s
  reconciliation uncertainty (the 923-vs-930 gap the reconcile repaired) —
  ledgered for that year.

### C3 — Price (three independently-bounded sub-criteria)  *(C3a/C3b LOAD-BEARING two-band; C3c SUPPORTING)*

A good mean price must not be allowed to mask a collapsed or over-fired tail, so
mean / shape / tail are **scored separately** and each can independently caveat or
fail.

**2026-07-02 re-balance (tightened, paired with the looser C1)** — retained as
the v2 TARGET bands: an LP whose duals reproduce the market’s price level,
seasonal shape and scarcity tail is demonstrating the market structure is
right, while a ±2 TWh small-class residual is usually reporting/assignment
noise. **v2 adds the COMMERCIAL outer band** (§1 intro) so a miss between the
two grades is recorded as commercial-grade-but-not-target rather than
hard-failing at a stricter standard than any external model demonstrates. The
C6 governance gate is untouched: any price band must be met by real structure
(reserve co-optimization, scarcity pricing, congestion), **never** by an adder
or haircut tuned to the price residual — a run that closes the price gap that
way FAILs C6 regardless.

- **C3a — Mean LMP.** *(LOAD-BEARING, two-band)*
  - *Metric:* system load-weighted mean LMP, $/MWh (model `lmp[zone].p` weighted
    across zones by `lmp[zone].d` annual demand).
  - *Actual (v2.4, owner amendment 2026-07-09 — the like-for-like basis):*
    `avgLMP.rt_lw` (real-time, **load-weighted**), the basis ladder falling
    back to `da_lw`, then the LEGACY equal-hour hub fields `rt`/`da` (with an
    explicit "LEGACY equal-hour basis" label) for ISO-years the lw retrofit
    does not cover. The lw fields weight each ISO's committed hourly actual by
    the SAME measured demand the model dispatches
    (`eia_loader.load_demand`) — zone-resolved where a committed zonal archive
    exists (ERCOT: LZ settlement prices × measured zonal load, model-zone
    crosswalked), the system hub series × system load elsewhere
    (`derive_actual_lmp.py --lw-retrofit`, `src_lw` provenance per ISO-year).
    Rationale: the legacy basis compared a demand-weighted model mean against
    an equal-hour actual — a wedge that grows with tail realism; a
    byte-perfect ERCOT 2023 model scores **+33.5%** against its own actual on
    the legacy basis, and the pre-v2.4 single-digit C3a readings were partly
    shallow-tail-vs-wedge cancellations
    (`docs/rubric-v24-price-basis-memo-2026-07.md`).
  - *Coverage masking (2026-07-03):* when the actual series is **partial** (its
    committed monthly vector has empty months — e.g. CAISO 2023, whose Jan–Feb
    aged out of OASIS retention), the model mean is computed over the **same
    covered months** (pMon/dMon masked to the actual's non-null months), since
    the committed actual mean only averages the covered months. Comparing a
    full-year model mean (which correctly prices the Feb-2023 gas blowout)
    against a Mar–Dec actual is a calendar artifact, not a price error; the
    masking is recorded in the verdict record's metric label. Full-coverage
    years are unchanged.
  - *Tolerance:* **±10% passes clean** *(v2.3, owner amendment 2026-07-09:
    the target band is set to the commercial band, so there is no
    commercial-band caveat range on C3a — inside ±10% is a clean `PASS`,
    beyond it a `FAIL`)*. The band is the demonstrated planning-grade range:
    NYISO’s accepted GE MAPS 2021 benchmark ran **−2% to −17% zonal** (NYC
    −10.5%) and was adopted as the Outlook basis; the playbook’s 5–10%. The
    former stricter ±5% target (**the criterion the SEM (Ireland) regulator
    states for its official PLEXOS market model** — ECA SEM-20-004, monthly
    within ±10%; NERA’s 2025 SEM backcast achieved +0.1% on a 4-year mean)
    stays as a reported reference magnitude, not a gate: caveating a run
    between the SEM criterion and the published commercial envelope graded
    honest runs as second-class for a miss no published model avoids. Two
    floors below all of this: the market monitors’ own competitive
    re-simulations sit **0–4%** from actual prices (CAISO DMM 2021–24, MISO
    SOM 2023) — a market-conduct wedge a cost-based model cannot and *should
    not* close, so residuals under ~3% are inside the identification noise
    floor and must never be chased with tuning (rule 1, now with citable
    numbers). The **energy-only LP dual structurally under-shoots** the
    actual LMP; that known gap is what the structural reserve/scarcity
    mechanisms are for. A persistent miss beyond the band is a signal to
    build the missing mechanism — not to widen the band, and never to fit an
    adder (C6).
  - *Classification:* `MODEL MISS` (offer-curve level / scarcity mechanism).
- **C3b — Duration / shape (quantitative, not eyeballed).** *(LOAD-BEARING, two-band)*
  - *Metric:* normalised RMSE between the model and actual **monthly
    load-weighted price vectors** (12 months; model `pMon` re-weighted across
    zones by `dMon`, actual `rt_lw_mon`/`da_lw_mon` — the v2.4 load-weighted
    monthly basis, legacy `rt_mon`/`da_mon` as the labelled fallback, same
    ladder as C3a). NRMSE = RMSE / mean(actual). This
    is the committed-artifact shape metric; where a run additionally commits the
    full hourly price-duration curve, the P50/P90 ratio check of
    `calibration.check_price_duration_curve` is scored in its place.
  - *Tolerance:* **NRMSE ≤ 0.20 passes clean** *(v2.3, owner amendment
    2026-07-09: the target band is set to the commercial band — inside 0.20
    is a clean `PASS`, no caveat range; beyond it a `FAIL`)*. Anchor: SEM’s
    regulator-accepted backcast carried −9% winter-peak / +11% off-peak period
    biases; published monthly-shape norms for cost-based dispatch models run
    ~5–15% with correct seasonality (memo §2). A 12-month NRMSE of 0.20 is the
    outer edge of that demonstrated band (numerically the pre-2026-07-02
    ceiling, externally anchored rather than asserted); the former 0.15
    target stays visible as a reported magnitude, not a gate.
  - *Classification:* `MODEL MISS` (seasonal merit-order / fuel-shape error).
- **C3c — Tail / scarcity, hourly-expressible.** *(SUPPORTING, single wide band)*
  - *Metric:* count of hours with price above the per-ISO threshold (§5),
    model vs the actual on the ISO’s **gated basis** (`TAIL_BASIS`, v2.6 —
    ERCOT: RT hourly; every other ISO: DA). Default **DA, scope-consistent
    (v2):** the DA market is an hourly, commitment-aware market, the same
    temporal resolution as this model’s LP, so its tail count is the scarcity
    an hourly model is in scope to reproduce. The RT count mixes that with
    **sub-hourly transients** (5-minute ramp scarcity, forecast-miss
    re-dispatch) that are out of representation:
    `docs/multi-iso/miso-scarcity-tail-diagnosis.md` §1 decomposed MISO
    2023’s entire 30-hour RT tail into single-hour 5-minute events (DA tail
    that year: 1 h) and §4 records that matching them "would be reproducing
    forecast error the model doesn’t represent."
    **ERCOT gates on the RT hourly tail (v2.6, owner amendment 2026-07-16):**
    ERCOT’s DA tail is *larger* than its RT tail (2023: 311 vs 181 h — DA
    prices scarcity *expectations*), and that excess is the day-ahead
    weather/load **forecast-risk premium**, which a realized-weather
    (perfect-foresight) backcast is out of representation to price — the
    mirror image of the transient argument. Its RT hourly hub tail is
    ORDC-driven and hourly-expressible (keeper evidence: 179 h model vs
    181 h RT in 2023). The displaced basis is always emitted as a
    **report-only diagnostic row** next to the gate (RT for DA-gated ISOs,
    DA for ERCOT), so neither count ever disappears from the verdict.
  - *Actual:* the committed `tail/actual_tail.json` part
    (`scripts/derive_actual_tail.py`, from the hub RT/DA hourly series;
    coverage-annotated, 2023–2025 only).
  - *Tolerance:* model tail hours within **[0.5×, 2.0×]** of the DA actual —
    a **collapsed tail (0 hours where the DA market had scarcity) FAILs**, and
    an **invented tail (> 2× actual) FAILs**; bounded both ways on purpose.
    When the DA actual is **< 10 h** the ratio is degenerate and
    **|model − actual| ≤ 10 h** gates instead (this also replaces the v1
    token guard against inventing a tail over a ~0 actual, tightened from
    50 h to 10 h). Band width rationale: **no commercial or public model
    publishes tail-hour-count accuracy at all** — the closest practice
    *excludes* spike hours from scoring (ECA excluded ~50–100 h/month) or
    absorbs them into tuned hurdle rates (NYISO); this rubric keeps scoring
    the tail, with the band’s job being order-of-magnitude realism on the
    scope-consistent benchmark, not count precision. Supporting tier: the
    *level* contribution of scarcity is already load-bearing via C3a/C3b.
  - *Classification:* `MODEL MISS` (missing scarcity pricing / over-aggressive
    peaker offers). `SKIPPED` when the model scarcity series is not in the
    committed payload or the ISO-year is absent from the tail part — recorded
    as not-scored, never a silent pass.

### C4 — Dispatch correlation, fleet hourly  *(SUPPORTING, single-band)*

- **Metric:** hourly Pearson **r** and **NRMSE** of the modeled vs EIA-930 hourly
  generation series, for the **gas** and **coal** fleets (`fuelRows[fuel].r`,
  `.nrmse`). This is the fleet-level “is it running at the right *times*” check;
  the per-plant r/NRMSE/capture in the dashboard is the finer-grained companion.
- **CHP add-back basis (stated):** the per-*plant* r/NRMSE add the behind-the-meter
  CHP host steam back flat (CAMPD measures the whole plant, and a flat add is
  correlation-invariant — it shifts level, not shape). The fleet-level **gas** row
  scored here is on the **grid-delivered basis**: model non-CHP gas grid vs
  (EIA-930 gas − model CHP flat), so both sides exclude the BTM steam the LP never
  saw. Coal has no CHP and is whole-fleet on both sides.
- **Actual:** EIA-930 hourly net generation by fuel (`fuelRows[fuel].b` is the
  annual total of that series; r/NRMSE are computed against the hourly series at
  render time).
- **Tolerance (floors):** **r ≥ 0.70** and **NRMSE ≤ 0.30** for gas and for coal.
  (Stricter than external practice, deliberately: NREL guidance is that
  hour-by-hour comparison to actuals is not a valid PCM test at all, and no
  vendor publishes hourly fleet correlation — we keep it because dispatch
  *timing* feeds storage arbitrage and scarcity coincidence in the intended
  uses; supporting tier, single band.)
  A fleet whose annual energy is **< 5 TWh** is `SKIPPED` (an hourly correlation
  on a near-zero series is degenerate — NEISO coal r ≈ 0 — and the C1 per-class
  band is the meaningful check). (Nuclear/wind/solar are report-only here — VRE hourly r is set by the input
  profile, not a dispatch decision, and nuclear is near-flat.)
- **Failure classification:** `MODEL MISS` (commitment / ramp / outage-overlay
  timing). A low r driven by a documented measured-input gap (e.g. an outage
  series known incomplete for one state-year) may be ledgered.

### C5 — CO2 and storage  *(C5a LOAD-BEARING two-band; C5b/C5c SUPPORTING)*

- **C5a — CO2 vs eGRID.** *(LOAD-BEARING, two-band)*
  - *Metric:* annual system CO2, model vs the eGRID/CAMPD-rate actual, on the
    **full-plant CHP-inclusive basis** *(v2.3, owner amendment 2026-07-09)*:
    eGRID counts each cogen’s FULL net generation — behind-the-meter host
    self-supply included — so a grid-delivered comparison silently dropped the
    BTM CHP burn eGRID reports. Both sides now carry the measured BTM CHP
    host supply added back before the intensities are applied: the actual is
    the full EIA-923 class totals (`classFull` + the committed per-class
    `btmClass` add-back) × the net-gen-weighted eGRID/CAMPD class intensity,
    and the model is its grid LP dispatch (`gmModel`) + the same measured
    add-back × the same intensity. The add-back is the exact hold-out the LP
    never dispatched (`run_calibration_full._btm_frame` — EIA-923 class net
    generation × measured host shares, a pure function of committed inputs,
    rule #13), so the comparison stays a test of the model’s fuel split and
    emission-rate assignment, not of plumbing. The generation-mix criteria
    (C1/C2) remain grid-delivered; only system CO2 — the quantity the
    atmosphere and the policy uses integrate — is whole-burn.
  - *Actual:* committed bench-part `co2.egrid` (full-plant basis; the eGRID
    fleet-wide rates with CAMPD overrides, weighted over the ISO’s EIA-923
    fossil fleet).
  - *Tolerance:* **target ±7% / commercial ±10%.** Thinnest external evidence
    base of the load-bearing set (memo §2, stated honestly): no production-cost
    model publishes a backcast CO2 error; the citable anchors are NEMS/AEO
    retrospective energy-CO2 error SDs of **3.2–4.9% at 1–3-year horizons**
    (full forecasts, so an upper bound a backcast should beat) and 14.6%
    pooled all-horizon. ±10% ≈ the 2-σ short-horizon envelope; the ±7% target
    (mid of the playbook’s 5–10%) is retained and is *stricter than any
    published backcast requirement*.
  - *Classification:* `MODEL MISS` (emission-rate assignment or gas/coal split —
    note that with C1/C2 in tolerance a CO2 miss localises to the fuel *split*
    within a family or to emission-rate inputs). `SKIPPED` when no emissions
    actual is committed in the bundle.
- **C5b — Storage throughput.**
  - *Metric:* annual storage (battery + PS) discharge throughput TWh, model vs
    observed (cycling realism, not arbitrage perfection).
  - *Actual:* EIA-923 / ISO battery-report throughput.
  - *Tolerance:* **±30%** (the playbook’s cycling-realism band — the LP will
    over-cycle without a throughput cost; the band catches gross over/under-cycling
    while accepting that exact dispatch timing is not observable).
  - *Classification:* over-cycling ⇒ `MODEL MISS` (needs a throughput adder);
    under-cycling against a *partial* observed series may be `ACCEPTED
    MEASURED-INPUT LIMITATION`. `SKIPPED` when no throughput series is committed.
- **C5c — Storage dispatch shape.**
  - *Metric:* Pearson **r** of 12 monthly **discharge** GWh vectors (model vs
    EIA-930 battery + pumped-storage, positive half). Scores whether the model
    discharges storage in the right months, not just the right annual volume
    (C5b). **Discharge basis on both sides (2026-07-03 alignment fix):**
    several BAs report a discharge-only storage series (NEISO `NG: PS` —
    pumping appears as load, never as a negative value; ERCOT
    `battery_discharge` is pre-split positive), so a signed "net" sum of the
    actual is silently gross discharge, while a model-side net
    (discharge − charge) is ≤ 0 over any month by round-trip losses — a
    basis mismatch a perfectly-cycling model could never pass. Both sides now
    use the positive (discharge) half, the same basis C5b already scores.
  - *Actual:* EIA-930 monthly discharge for `battery` / `pumped_storage`
    series. Same coverage gate as C5b. **Observed months only (v2.6, owner
    amendment 2026-07-16):** a month with no real EIA-930 storage observation
    (below 90 % non-NaN hourly coverage — e.g. every ERCO month before the
    mid-Oct-2024 battery breakout) enters the bench vector as **null, never
    0.0**, and the scorer's null-month rule then SKIPs the year. Booking
    unreported months as zero fabricates an actual: the pre-v2.6 ERCOT 2024
    C5c FAIL (r = 0.451) correlated the model against nine structural zeros
    plus three real months — a benchmark-coverage artifact, not a model miss.
  - *Tolerance:* **r ≥ 0.50.** The floor is looser than fleet dispatch (C4,
    r ≥ 0.70) because monthly storage discharge is a 12-point vector with
    lower degrees of freedom and substantial noise from AS commitment.
  - *Degeneracy guard (2026-07-03, mirrors C4's <5 TWh rule):* when the
    **actual** monthly-discharge coefficient of variation is **< 0.25** the
    year is `SKIPPED` — a near-uniform actual (e.g. NEISO 2025 PS, CV ≈ 0.14:
    Northfield cycles near-daily year-round on reserves/regulation) has no
    seasonal shape to correlate, the 12-point Pearson is set by reporting
    noise, and a perfectly **flat (true) model would score r = 0 and FAIL** —
    a metric the truth itself cannot pass is degenerate. The under/over-cycling
    volume stays fully scored by C5b (never a silent pass).
  - *Classification:* `MODEL MISS` (storage dispatch timing — wrong charge/
    discharge season). `SKIPPED` when no EIA-930 storage breakout or the model
    bundle lacks `monthly_net_gwh`.

### C6 — Governance gate  *(PROTECTIVE, pass/fail only — never graded, never caveatable; UNCHANGED in v2)*

This is the `claude.md` rule made executable. **A run that fits to residuals
FAILS regardless of every score above.** Four assertions, all required:

1. **Every active lever traces to a measured input** (a physical/market quantity
   that would regenerate for a forward year and respond to changed conditions —
   the rule #13 admissibility test). No lever exists only to move a residual.
2. **No fitting to price residuals** — no adder/haircut/sigmoid tuned to the price
   error.
3. **No pinning to actuals** — no unit pinned to its observed CEMS generation, no
   input rescaled so the model *output* lands on the actuals.
4. **The outage filter keys on exogenous net load** — availability comes from
   measured unit-outage windows (`outage_source = "historic"`) or statistical
   outages (`"statistical"`), i.e. an exogenous availability event, never a filter
   keyed on the dispatch residual.

**How it is evaluated:**
- *Machine cross-check (from `run_config.json`):* `outage_source` must be a
  recognised exogenous source (`historic`/`statistical`); no flag on the forbidden
  list (output-pinning / price-residual-adder mechanisms) may be active. If the
  config contradicts the attestation, the gate is `FAIL`.
- *Attestation (from `calibration_attestation.json`):* the four assertions must be
  present and all `true`. The machine cannot detect every possible fitted
  mechanism, so the attestation is required and is part of the auditable record.
- *Result:* `PASS` iff machine-clean **and** attestation present with all four
  true; `FAIL` if the machine check trips or any attestation is false;
  **`UNATTESTED`** (⇒ `NOT-YET`) if no attestation file exists — you cannot certify
  a run you have not attested.

### C7 — Diurnal shape, gated classes  *(PROTECTIVE, added 2026-07-04, audit D-1; UNCHANGED in v2)*

- **Metric:** per plant-class hour-of-day mean profile, model vs CAMPD: the
  **profile correlation r** and the **off-peak (h0–14) CV ratio**
  (model CV / actual CV). Gated classes are the peaker/intermediate duty
  classes (`CT_PEAKER`, `ST_GAS`); every class is still reported.
- **Source:** the bundle's committed `legitimacy_diagnostics.json`, written by
  `scripts/legitimacy_diagnostics.py --json-out` (the S1 suite is the single
  implementation; this scorer only reads its rows). Model side is the run
  payload's per-plant hourly dispatch; actual side is the committed CAMPD
  bench series.
- **Tolerance:** profile **r ≥ 0.8** AND off-peak **CV ratio ≥ 0.5** (the
  thresholds are read from the artifact's `gates` block, set in
  `scripts/legitimacy_diagnostics.py` `D1_*`). A flat line — the caiso-42
  signature, model off-peak CV 0.000 vs actual 0.35–0.45 — fails both.
  **Materiality floor (v2.1, owner amendment 2026-07-06):** gated only for
  classes whose annual energy — **max(model, actual)**, so a forced floor
  cannot hide a class below the line by its own inflation — is
  **≥ 2 % of total ISO load** (`PROTECTIVE_MIN_LOAD_FRAC`); smaller classes
  are `SKIPPED`-immaterial with the D-1 readings annotated (reported, never
  gated — trivial-class shape is not worth structural work; mirrors C2/C4
  immateriality). At the amendment date this exempts NEISO ST_GAS/CT
  (0.1–0.7 % of load) and NYISO CT (1.4–1.9 %) while CAISO CT 2023/24
  (2.1–2.3 % — the motivating caiso-42 case), PJM/MISO CT (3.5–4.2 %) and
  every material ST_GAS (2.1–10.6 %) stay gated.
- **Why first-class (motivating evidence):** annual volume bands cannot see
  class-shape failure. The D-7 statistical-mode study
  (`docs/statistical-mode-results-2026-07.md`) showed the 2026-07-02-loosened
  C1 class band (`min(2% load, 8 TWh)`) **absorbed a >6× growth in the ERCOT
  CT_PEAKER miss** (2024: +0.04 → −6.27 TWh, still PASS), and **every ISO's
  CAVEAT count collapses to ~0 with the overlays off** — the soft-caveat band
  was absorbing overlay-narrowed near-misses, not model tolerance. A flat
  floor *helped* C1 while destroying the diurnal shape nothing scored
  (audit §5.4-1); C7 closes that hole so a flat floor can never again improve
  a keeper's score.
- **Failure classification:** `MODEL MISS` (a forced floor or missing
  merit-order shape — commitment/offer structure, per audit §1). Essentially
  never ledgerable: a flat profile is a mechanism defect by construction.
  `SKIPPED` (never a silent pass — and it caps the determination, §2) when
  the bundle carries no `legitimacy_diagnostics.json`.

### C8 — Forced-energy share  *(PROTECTIVE, added 2026-07-04, audit D-2 / CLAUDE.md rule 20; grounded-above-budget escalation v2.2 2026-07-07)*

- **Metric:** the share of a class's annual energy dispatched **AT a binding
  `min_gen` floor**, by class, attributed per mechanism via the int8
  mechanism-id array threaded through `FleetArrays`.
- **Source:** the D-2 per-class summary in the bundle's committed
  `legitimacy_diagnostics.json`. Floors come from the bundle's persisted
  `floors/<year>_<pass>.npz` or the `run_year(fleet_only=True)` rebuild; a
  rebuilt-floor share excludes the P1-dependent RA bridge and is recorded as
  a **lower bound** in the verdict record.
- **Tolerance:** forced share **< 15 %** for peaker classes (`CT_PEAKER` —
  raised from 10 % by the v2.1 owner amendment 2026-07-06, amending CLAUDE.md
  rule 20 in place), **< 30 %** for any merchant class. **Materiality floor
  (v2.1):** same ≥ 2 %-of-load gate as C7 — smaller classes are
  `SKIPPED`-immaterial with the D-2 share annotated. **Exempt:** nuclear,
  CHP-steam classes and the coal take-or-pay/mine-mouth must-run mechanisms —
  structural, owner-accepted must-run physics (audit §2). The scorer gates the
  artifact's **measured** `forced_share` against the rubric's own caps
  (`FORCED_SHARE_*` in `calibration_verdict.py`; `legitimacy_diagnostics.py`
  `D2_*` mirrors them for future artifacts' embedded verdicts) so artifacts
  written under earlier gate values re-score correctly without regeneration.
- **Why first-class:** floors are commitment scaffolding, not the dispatch
  model — ~50–55 % of modeled CAISO CT energy sat at the caiso-42 floor while
  the volume gates rewarded it (audit §1.1). Same statistical-mode evidence
  as C7: the class-volume band is structurally unable to distinguish
  merit-order dispatch from forced energy.
- **Grounded-above-budget escalation (v2.2, owner amendment 2026-07-07):** the
  caps and the materiality floor above are **unchanged** — a class within its
  cap still passes cheaply on the share alone. What changes is a material class
  **above** its cap: it is no longer an automatic `FAIL`, because forcing can be
  legitimate past the budget when it is a real grid/RA/AS driver that reproduces
  the observed dispatch (*as much as needed* may be forced if it is structurally
  grounded **and** shape-faithful). It escalates to a conditional pass requiring
  **both**:
    1. **Provenance (D-4):** every binding non-exempt mechanism forcing the class
       clears D-4 off-window binding — it binds only inside its driver-justified
       `D4_WINDOWS` window. A mechanism with **no declared window** fails here
       (CLAUDE.md rule 17 — "no floor without a window", cited as "rule 12" in
       older code comments), as does one that binds off-window.
    2. **Shape (D-1):** the class's D-1 hour-of-day profile clears the artifact
       gates (`profile_r ≥ d1_min_profile_r` and off-peak `cv_ratio ≥
       d1_min_cv_ratio`), applied to **any** escalating class (not only the
       default `d1_gated_classes`). This is the "shape mismatch ⇒ the forcing
       variables are wrong" test.
  Both clear → **clean `PASS`** classified `GROUNDED ABOVE BUDGET`, surfaced as a
  report **note** (never a caveat — owner decision), so the high forcing stays
  visible and auditable. Either fails → `FAIL` describing the miss as a forcing
  **shape/provenance mismatch**. All signals come from the committed
  `legitimacy_diagnostics.json` (D1/D2/D4 rows + gates), so this is **scorer-only
  — no re-solve, no bundle regen** — and existing keepers re-score in place (C8
  only *relaxes*: below-cap unchanged, above-cap gains a pass-path). To actually
  ground a specific keeper's over-budget class, its mechanism needs a **cited
  `D4_WINDOWS` entry** and that bundle re-generated so the D-4 row exists; a
  mechanism-driven flip is scored **leave-one-year-out** within 2023–2025 before
  promotion. (Wired 2026-07-07: the CAISO-58 CT_PEAKER `ra_mustoffer_bridge` and
  NYISO-53 `reliability_floor × ST_GAS` shares — both ~60 % — now FAIL with an
  *explicit* "no declared D-4 window" diagnosis rather than a flat over-cap fail.)
- **Failure classification:** `MODEL MISS` (stacked-floor creep / a floor
  fitting the class, or an above-cap class failing the provenance/shape
  escalation). Essentially never ledgerable. `SKIPPED` when the
  artifact or the year's floor data is absent — recorded, capping the
  determination.

### D-7 statistical-mode gap  *(REPORTED, never gating)*

Each keeper's Calibration Status entry carries the **statistical-mode
fail-count gap** — in-sample criterion fails with the keeper's overlays vs
fails with `--statistical-mode` (all per-hour/per-year answer-injection
overlays off), from the registered D-7 probes
(`docs/statistical-mode-results-2026-07.md`; data:
`frontend/data/backcast/statmode_d7.json`). It is a **reported line, not a
criterion — and not a caveat on the keeper's backcast determination**
*(reframed 2026-07-13, owner directive)*. The gap has two components read
differently: the part carried by **admissible measured inputs** (historic
outage windows, F923 fuel pricing — the rule-13 class) is the
**backcast→forecast input gap** — the year's correct physical inputs versus
their statistical stand-ins — which is forecast-uncertainty information for
error bars and the crossover window, never a deduction from backcast skill (a
backcast is scored with those inputs by construction). Only the component
carried by answer-injection floors (the D-9 quarantine class) bears on
legitimacy, and it is that component which should shrink release-over-release
(audit §7 D-7); re-measure the gap whenever a keeper changes.

### C-VRE note (solar / wind)

Solar and wind volumes are benchmarked against **EIA-930** (not 923) per
`calibration.actuals_source` (923 under-counts distributed/CISO VRE and collapses
in the incomplete current-year vintage). They are tracked as report-only context
rows in the verdict (±10% advisory), not a hard or soft gate — a backcast feeds
measured VRE potential, so a VRE volume miss is an input/curtailment-accounting
issue, surfaced but not gating the dispatch determination.

---

## 2. Decision logic — combining criteria into one determination

Let **scorable years** = the years present in the run payload. **Target years** =
the years the sidecar declares. A target year absent from the payload is a
**data-blocked year**: the ISO is **judged only on its scorable years**, and the
block is recorded in the verdict (it does not silently pass, and it caps the grade
— see below).

**Per-criterion aggregation across scorable years:** a criterion is `FAIL` if it
fails any scorable year; else `CAVEAT` if it caveats any year; else `PASS` if it
passes any year; else `SKIPPED` (no data in any year).

**Caveat kinds and budgets (v2):** two distinct kinds of `CAVEAT`, budgeted
differently:

- **Auto commercial-band caveats** (`WITHIN COMMERCIAL BAND (TARGET MISS)`) —
  a graded load-bearing criterion between its target and commercial bands.
  **Unbudgeted**: they are inside the certification claim by construction
  (“commercial-grade or better”), machine-derived, bounded by a cited external
  benchmark, and every one is listed with its magnitude in the verdict and on
  the dashboard. They are *listed, not excused* — an ISO whose load-bearing
  criteria all sit in the commercial band is certified `CALIBRATED-WITH-CAVEATS`
  and visibly not target-grade (the `grade_summary` line counts each tier).
- **Ledgered caveats** (`ACCEPTED MEASURED-INPUT LIMITATION`) — an
  out-of-tolerance (beyond-commercial) criterion reclassified by an explicit
  exceptions-ledger entry (§3). Budgeted:
  - **Protective criteria (C7/C8):** at most **1**, unchanged from v1’s
    hard-gate budget (C7/C8 are essentially never ledgerable — see their
    sections; C6 is never caveatable). This is CLAUDE.md rule 20 / audit
    D-1/D-2 enforcement, untouched.
  - **Everything else (C1, C2, C3a/b/c, C4, C5a/b/c):** at most **3** total.
    Re-derivation of the budget (replacing the 2026-07-02 3→2 cut, whose
    stated concern — all three price sub-criteria caveated at once — is now
    structurally addressed by the commercial band: a load-bearing price miss
    beyond ±10%/0.20 needs a *named measured-input reason*, not just a slot):
    the recurring documented data-limitation classes are three by construction
    — the preliminary-923 vintage, EIA-930 storage-series coverage, and a
    data-blocked scarcity-requirement series — and a budget of 2 mechanically
    forced `NOT-YET` on *data availability* rather than model quality (the
    nyiso-34 demotion had exactly this shape and no external rationale). The
    budget bounds excuses; it never grants them — each entry still names its
    metric, year, magnitude and measured-input reason, and the classes that
    are never ledgerable (§3) stay never ledgerable.

**Determination:**

| Outcome | Conditions (all must hold) |
|---|---|
| **CALIBRATED** | C6 governance `PASS`; **every** criterion `PASS` at target grade (no `FAIL`, no `CAVEAT` of either kind, no `SKIPPED`); **no** data-blocked target year. |
| **CALIBRATED-WITH-CAVEATS** | C6 governance `PASS`; **no** `FAIL` on any criterion; ledgered caveats within budget (≤1 protective, ≤3 other) and **every** ledgered caveat has a ledger entry; one or more of {any caveat exists, a criterion is `SKIPPED` (e.g. C7/C8 with no committed `legitimacy_diagnostics.json` — named explicitly in the reasons), a target year is data-blocked}. **Certifies: intended-use delivery at or above commercial grade.** |
| **NOT-YET** | anything else — governance not `PASS`/`UNATTESTED`; **or any criterion `FAIL`** (an out-of-tolerance criterion with no ledger entry is a `FAIL` *by construction*); or a ledgered-caveat budget is exceeded. |

The decisive rule, restated: **a determination with an undocumented
out-of-tolerance criterion is `NOT-YET`.** The only way a beyond-commercial-band
criterion is compatible with a passing determination is an explicit, ledgered
`ACCEPTED MEASURED-INPUT LIMITATION` (and only within the caveat budget).

Where an actual is not committed for an ISO-year (storage C5b/C5c for most
BAs today; historically the tail and CO2, both now committed), the criterion is
`SKIPPED`, which **caps the best attainable determination at
`CALIBRATED-WITH-CAVEATS`** until a run surfaces it. This is intended: you may
not claim a *fully* calibrated ISO while any criterion is unscored.

---

## 3. The exceptions ledger (required, auditable)

Every **ledgered** `CAVEAT` must be earned by an explicit ledger entry (auto
commercial-band caveats are machine-derived from the committed artifacts and
need none — they are listed by the scorer itself). The ledger lives in the
bundle at `results/calibration/<name>/calibration_attestation.json` (per-run,
conflict-free, committed with the bundle). A beyond-commercial-band criterion
with **no matching ledger entry is a `FAIL`** — silence is never a pass.

Each entry must name **the metric (criterion, and class/family where the criterion
is per-class), the year, the magnitude (the observed error), and the reason it is
an accepted measured-input limitation rather than a model defect.**

```json
{
  "schema": "calibration-attestation/v1",
  "governance": {
    "levers_trace_to_measured_input": true,
    "no_fit_to_price_residuals": true,
    "no_pinning_to_actuals": true,
    "outage_filter_exogenous_net_load": true,
    "attested_by": "neiso-23 session 2026-06-21",
    "note": "Levers: measured F923 monthly gas, CAMPD unit-outage overlay, EIA-860 BTM CHP pull-out, measured interchange schedule. No residual-tuned adders."
  },
  "exceptions": [
    {
      "criterion": "fuelmix",
      "klass": "CT_PEAKER",
      "year": 2024,
      "magnitude": "-1.8 TWh (model 0.2 vs grid-delivered 2.0)",
      "reason": "NEISO oil/gas peakers run a few scarcity hours the energy-only LP cannot see; the grid-delivered actual is itself near the measurement floor. ACCEPTED MEASURED-INPUT LIMITATION, not a merit-order defect."
    },
    {
      "criterion": "sysvol",
      "family": "gas",
      "year": 2025,
      "magnitude": "+3.1% vs EIA-930 grid",
      "reason": "2025 preliminary EIA-923 vintage; residual inside the 923-vs-930 reconciliation band the _VINTAGE_RECONCILE_FRAC=0.97 path repaired. Re-score when the final 923 vintage lands."
    }
  ]
}
```

Example accepted limitations (the named cases): NEISO’s model-zeroed `CT_PEAKER`;
the 2025 preliminary-923 vintage system-volume residual. Examples that are **never**
ledgerable (they are `MODEL MISS` and must be fixed, not excused): a coal/gas split
error, a collapsed price tail, a fleet-correlation floor breach, an over-cycling
storage fleet.

---

## 4. Which years count

- Only **scorable years** (present in the payload) are judged.
- A **data-blocked target year** (declared but absent — e.g. an ISO whose LMP
  portal year never uploaded, or a single-year bundle) is recorded as such in the
  verdict and caps the determination at `CALIBRATED-WITH-CAVEATS` (you cannot call
  an ISO fully calibrated on a partial year set).
- The **preliminary current-year vintage** (year ≥ 2025) is scorable, but its C2
  actual uses the EIA-930 vintage-reconcile path (§C2), and a C2/C1 residual there
  is the canonical ledgerable measured-input limitation.

## 5. Tail definition per ISO

**Unified in v2 (criterion-set parity):** every ISO scores the same C3c
definition — model tail hours vs the committed hourly actual count at the
ISO’s threshold. The *threshold* is per-ISO (a market-design fact, not a
criterion asymmetry): winter city-gate scarcity sets NYISO/NEISO higher.
The v1 asymmetries are retired: ERCOT no longer gates on its own ORDC-adder
proxy (the `ordc` block’s RT/adder counts and the > $500 deep-scarcity
companion remain **report-only** diagnostics in the payload), so no ISO is
scored on a criterion set another ISO isn’t. **v2.6 amends the basis half of
this parity wording:** the criterion, band, and threshold family stay
identical for every ISO, but the gated *actual’s basis* is per-ISO
(`TAIL_BASIS`) on a measured, documented asymmetry — see §C3c. (The same
parity rule applies to the reported D-7 statistical-mode gap: quote fail
counts on the same criterion denominator for every ISO — the 2026-07-03
measurements mixed C1–C8 and C1–C5c denominators and are flagged stale for
re-measurement.)

| ISO | Threshold (hub LMP) | Gated basis (v2.6) | Scarcity driver |
|---|---|---|---|
| ERCOT | $200/MWh | **RT hourly** (DA = diagnostic) | summer/ramp scarcity; DA embeds the forecast-risk premium |
| PJM, MISO, CAISO | $200/MWh | DA (RT = diagnostic) | summer/ramp scarcity |
| NYISO, NEISO | $300/MWh | DA (RT = diagnostic) | winter city-gate scarcity sets the tail higher |

`SKIPPED` for any ISO-year absent from the committed tail part or whose model
scarcity series is not in the payload, recorded with that reason.

## 6. Re-determination trigger

**Any keeper change re-runs the scorer.** The determination is not a one-time
stamp — it is recomputed whenever the run’s committed artifacts change. Concretely:

- `scripts/dashboard_add_run.py` calls `calibration_verdict.determine(...)` after
  registering/rendering a run and prints the determination, so **every registered
  run prints its determination** (the calibration-report skill surfaces it in its
  headline — see the skill’s steps).
- Editing a run’s exceptions ledger, re-rendering its payload, or re-registering
  the bundle all re-run the scorer; the printed determination reflects the current
  committed state.
- The verdict JSON (`calibration_verdict.py --json`) is the machine record a CI
  check or the forecast-validation gate can assert on.

---

## 7. Usage

```bash
# Human-readable determination for one keeper (by bundle or by run id):
python scripts/calibration_verdict.py results/calibration/neiso_23_outage_btm
python scripts/calibration_verdict.py --run-id 2026-06-21-neiso-23-outage-btm

# Machine-readable verdict (for CI / the forecast-validation gate):
python scripts/calibration_verdict.py --json results/calibration/pjm_26
```

The scorer is stdlib-only (no pandas, no LP, no model import) so it runs anywhere
the committed artifacts are checked out.

---

## 8. Commercial-benchmark anchor table (summary)

Full survey with citations, evidence-quality grades and the honest negative
findings: `docs/rubric-v2-benchmark-memo-2026-07.md`. The dashboard’s
Calibration Status page renders this comparison next to the live keeper scores
— that table is the scrutiny-survival artifact. Summary:

| Criterion | Our target band | Our commercial band | Best published comparable |
|---|---|---|---|
| C3a mean LMP | ±10% (v2.3: single band, passes clean) | ±10% (coincident) | SEM regulator criterion ±5% (ECA SEM-20-004); NERA SEM backcast +0.1% (4-yr); NYISO MAPS benchmark −2…−17% zonal, accepted; monitor competitive re-sims 0–4% (noise floor) |
| C3b monthly shape | NRMSE ≤ 0.20 (v2.3: single band, passes clean) | ≤ 0.20 (coincident) | SEM accepted −9% peak/+11% off-peak period bias; monthly norms ~5–15%; PyPSA-Eur weekly SMAPE 20–26% |
| C1 per-class mix | min(2% load, 8 TWh) & 3 pp | (single-band) | **none published** — external validations stop at family/zonal level; we score stricter deliberately |
| C2 family volume (prelim fallback) | ±2.5% | ±5% | NYISO zonal energy ~0–4%; AEO 1–3-yr gas-gen SD 5.7–9.6% (forecast upper bound) |
| C5a CO2 (full-plant basis, v2.3) | ±7% | ±10% | **no published PCM backcast CO2 error**; AEO 1–3-yr CO2 SD 3.2–4.9% (forecast) |
| C3c tail hours (per-ISO basis, v2.6: ERCOT RT, others DA) | [0.5×, 2×] | (single wide band) | **none published** — practice excludes spike hours from scoring (ECA) or tunes hurdle rates (NYISO); we keep scoring it |
| C4 hourly fleet r | r ≥ 0.70, NRMSE ≤ 0.30 | (single-band) | **none published**; NREL guidance: hourly comparison “not a valid test” — we score stricter deliberately |
| C5b storage cycling | ±30% | (single-band) | none published (cycling-realism band, internal) |
| C6/C7/C8 protective | pass/fail | — | **beyond commercial practice**: NYISO closed its residual with tuned hurdle rates; SEM tunes generator markups; our C6 forbids exactly that |

Honesty in both directions: where the six keepers sit **below** commercial
grade (CAISO mean price +20–42%; MISO CC_REGULAR +44 TWh; collapsed DA tails in
PJM/MISO/CAISO 2024–25), the verdict says `NOT-YET` — the benchmark table is
never a curve to grade down to.

## 9. Version history

- **v2.6 (2026-07-16, owner amendments — session-logged, ERCOT-73 session)** —
  two changes, both scorer/bench level (no re-solve, no payload change).
  **(a) C3c per-ISO gated basis (`TAIL_BASIS`): ERCOT moves to the RT hourly
  tail; every other ISO stays DA-gated.** Both actuals are hourly hub averages
  from the same committed tail part; only which one gates flips. Rationale:
  ERCOT's DA tail runs *above* its RT tail (2023: 311 vs 181 h) and the excess
  is the day-ahead weather/load **forecast-risk premium** — out of
  representation for a realized-weather (perfect-foresight) backcast exactly
  as sub-hourly transients are out of representation for an hourly LP, the
  argument that keeps the *other* ISOs DA-gated (MISO 2023's whole 30 h RT
  tail is single-interval 5-minute events). The displaced basis becomes the
  report-only diagnostic row in both directions, so nothing stops being
  visible. This consciously amends §5's v2 same-basis parity wording: the
  criterion, threshold family, and band stay identical for every ISO — only
  the *actual's basis* is per-ISO, on a measured, documented asymmetry.
  Keeper evidence at amendment: the ERCOT-71 keeper reads 179 h vs RT 181 h
  (0.99×) in 2023 where the DA gate read 0.58×; its 2024 tail (26 h) remains
  short on either basis (0.49× RT vs 0.38× DA) and stays covered by its
  ledgered G-22 scarcity-formation entry.
  **(b) C5c scores only OBSERVED months.** The bench builder
  (`render_calibration_html._actual_storage_monthly`) emits **null — never
  0.0 — for months without a real EIA-930 storage observation** (a month
  passes only at ≥ 90 % non-NaN hourly coverage), and the scorer's existing
  null-month rule then SKIPs the year. Before this, a partial-breakout year
  was scored against fabricated zeros: EIA-930 breaks ERCO batteries out of
  `Other` only from mid-Oct-2024, so the ERCOT 2024 "actual" vector was nine
  structural zeros + three real months, and the keeper's only undocumented
  FAIL (C5c 2024, r = 0.451) was a correlation against invented data — a
  benchmark-coverage artifact, not a model miss. ERCOT C5c has never had a
  fully-observed year (2023 no breakout, 2024 partial, 2025 CV-degenerate);
  it now honestly skips all three. C5b's accidental NaN-poisoning skip for
  partial years is documented in place and deliberately unchanged (an
  explicit rule would flip other ISOs' committed skips to scored rows —
  needs its own cross-ISO pass).
- **v2.5 (2026-07-13, owner amendment)** — C2 gates ONLY fully-reported
  EIA-923 families: a preliminary-vintage family (incomplete 923 booking,
  e.g. every ISO's 2025) is not gated against any fallback basis (the G-21b
  930-derived family total or the CAISO CEMS anchor) — those rows print as
  SKIPPED diagnostics and re-gate when the final vintage lands. Mirrors C1's
  incomplete-class skip. *(Recorded here 2026-07-16 — the amendment shipped
  in the scorer with its own header note but the doc's history lagged.)*
- **v2.4 (2026-07-09, owner amendment — second of the day)** — C3a/C3b score
  on the **like-for-like load-weighted actual** (`rt_lw`/`da_lw` bench
  fields — the committed hourly actual weighted by the same measured demand
  the model dispatches) instead of the legacy equal-hour hub mean; ISO-years
  without lw fields fall back with an explicit label. See
  `docs/rubric-v24-price-basis-memo-2026-07.md`. *(Recorded here 2026-07-16,
  same doc-lag note as v2.5.)*
- **v2.3 (2026-07-09, owner amendments)** — two changes, both scorer/payload
  level (no re-solve). **(a) C3a/C3b single-band re-set:** the price target
  bands are set to the commercial values — **±10% mean LMP and monthly NRMSE
  ≤ 0.20 now pass clean, with no commercial-band caveat range** on the two
  price criteria (the former ±5%/0.15 targets remain visible as reported
  magnitudes). Rationale: the caveat range between the SEM regulator
  criterion and the published commercial envelope graded honest runs as
  second-class for a miss no published model avoids; beyond ±10%/0.20 still
  FAILs, ledgerable only as a measured-input limitation. **(b) C5a full-plant
  CO2 re-base:** eGRID includes CHP — its per-plant rates and system totals
  count each cogen's full net generation including the behind-the-meter host
  supply — so the C5a comparison now adds the measured BTM CHP MWh back onto
  BOTH sides (actual = full EIA-923 class totals × intensity; model = grid
  LP dispatch + the same measured add-back × intensity) instead of comparing
  grid-delivered totals against CHP-inclusive rates. Committed payloads were
  re-based in place (`scripts/retrofit_co2_payloads.py`; bench parts carry
  `co2.btmClass` + `co2.basis = "full-plant"`), reconstruction validated
  exact against the full-923 class totals. C1/C2 stay grid-delivered.
  Effect at amendment: no keeper's overall determination flips; ERCOT/PJM/
  NYISO/NEISO/MISO price caveats clear to PASS where inside the band, all
  six keepers still PASS C5a on the new basis (NYISO 2024 keeps a
  commercial-band CO2 caveat at −7.3%).
- **v2.2 (2026-07-07, owner amendment)** — C8 **grounded-above-budget
  escalation**. The 15 %/30 % caps and the 2 % materiality floor are
  **unchanged**; what changes is that a material class **above** its cap is no
  longer an automatic `FAIL`. It escalates to a conditional pass on **provenance
  (D-4 off-window binding) + shape (D-1 profile)**: forcing may exceed the budget
  when it is a real grid/RA/AS driver that binds in its justified window *and*
  reproduces the observed diurnal shape (*as much as needed* may be forced if
  structurally grounded and shape-faithful; the gate now targets forcing whose
  **window or shape doesn't match reality**). A grounded pass is a **clean PASS
  surfaced as a report note, never a caveat** (owner decision); a miss FAILs as a
  forcing shape/provenance mismatch. Scorer-only (reads D1/D2/D4 rows + gates from
  the committed `legitimacy_diagnostics.json`) — no re-solve, no bundle regen;
  existing keepers re-score in place and C8 only *relaxes* (below-cap unchanged,
  above-cap gains a pass-path). Grounding a specific keeper's over-budget class
  requires a **cited `D4_WINDOWS` entry** for its mechanism + that bundle's regen,
  and a mechanism-driven flip is scored **leave-one-year-out** within 2023–2025
  before promotion. Effect at amendment: no keeper flips — CAISO-58 CT_PEAKER
  (`ra_mustoffer_bridge`, ~60 % forced) and NYISO-53 `reliability_floor × ST_GAS`
  (~60 %) now FAIL with an explicit **"no declared D-4 window"** diagnosis instead
  of a flat over-cap fail, naming exactly what would ground them.
- **v2.1 (2026-07-06, owner amendments)** — C7/C8 **materiality floor**: the
  protective shape and forced-share gates score only classes with annual
  energy (max of model/actual) **≥ 2 % of total ISO load**; smaller classes
  are reported by the D-1/D-2 diagnostics, never gated (the owner's directive:
  no structural work spent making a trivial class hit an r/CV or unforced
  target). **C8 peaker cap 10 % → 15 %** (CLAUDE.md rule 20 amended in place;
  no external anchor exists for either value — this is an owner
  risk-tolerance setting, recorded as such). The scorer now gates D-2's
  measured shares against the rubric's caps rather than the artifact's
  embedded verdicts. Supersedes the same-day C7-only 2.5 % cut landed by the
  L-15 lane (`f68ffed`/`29eafdf`): scope widened to C7+C8 per the owner's
  directive, X held at 2 % (owner-confirmed) so CAISO CT (2.1–2.3 % of load)
  and every PJM/MISO ST_GAS year stay gated, and the basis is max(model,
  actual) so forcing cannot self-exempt a class. Effects at amendment: ERCOT
  C8 (CT 12.4 %, 1.5–1.7 % of load) and PJM C8 (CT 12.1 % < 15 %) clear;
  NYISO's CT row (92.7 %, 1.4–1.9 % of load) and NEISO C7 (ST_GAS 0.1–0.3 %
  of load) become immaterial-skips; CAISO C7/C8 CT fails (27.5–32.6 % forced)
  stand — the caiso-42 flagship case remains caught. NYISO nonetheless scores
  NOT-YET at HEAD: the same-day D-2 legitimacy regeneration (PR #1512)
  surfaced ST_GAS forcing at 59.7–69.8 % on a fully material class
  (5.7–8.4 TWh, 3.9–5.5 % of load) with no ledger entry — the materiality
  floor correctly does not exempt it, and the undocumented FAIL governs.
- **v2 (2026-07-06)** — fitness-for-purpose re-anchor (this session): §0
  statement of intended use + criterion tiers (load-bearing / supporting /
  protective, replacing HARD/SOFT); two-band target/commercial tolerances on
  C2-fallback/C3a/C3b/C5a with published anchors (memo §2); C3c re-scoped to
  the DA-expressible tail (committed `tail/actual_tail.json`), band restored
  to [0.5×, 2×] with a <10 h absolute guard, RT reported as diagnostic;
  criterion set unified across ISOs (§5); caveat budgets re-derived
  (protective ≤1 unchanged; ledgered ≤3 replacing soft ≤2; commercial-band
  auto caveats listed, unbudgeted). **Unchanged: C6/C7/C8 logic and
  thresholds, C1 bands, C4/C5b/C5c bands, the exceptions-ledger mechanism,
  rule-13/14/22 protections, D-9/D-6/E9 gates, and the keeper =
  most-structurally-faithful principle.** Re-score result: NYISO and NEISO →
  `CALIBRATED-WITH-CAVEATS`; ERCOT/PJM/MISO/CAISO remain `NOT-YET`.
- **v1** (2026-06 → 2026-07-05) — original machine-enforced rubric; 2026-07-02
  re-balance (C1 loosened, C3 tightened, soft budget 3→2); 2026-07-04 C7/C8
  protective gates added (audit D-1/D-2).
