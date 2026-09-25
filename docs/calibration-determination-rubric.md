# Calibration Determination Rubric (v2)

Status: **canonical, machine-enforced. RUBRIC VERSION 3.4** (2026-08-18 owner
amendment, session caiso-c1-lmp-pricing. Directive verbatim: *"Ccgt is fine at
-1.8% for passing c1 gate … I want … a shift that declares c1 for 2023
calibrated"*. **The C1 volume band is floored at the share leg's own
materiality scale**:
`vol_band = min(max(2.0% of ISO load, 3.0% of ACTUAL total generation), 8 TWh)`
(`calibration_verdict._fuelmix_vol_band`). **No new constant** — the floor is
`FUELMIX_SHARE_PP` (3.0) applied to the actual-side generation total, the same
±3.0-pp-of-mix materiality the share leg already declares. Coherence repair,
not a residual fit: on a deep net-importing ISO the 2%-of-load term could bind
*tighter* than the rubric's own declared mix-materiality on the same class
(CAISO 2023: ±4.15 TWh of load vs ±5.27 TWh = 3% of actual generation),
failing a class whose miss the share standard calls fine (`CC_REGULAR`
−4.24 TWh = −2.4% of actual generation, share −1.8 pp). The floor is measured
in raw |model−actual| TWh over the **actual** generation denominator —
deliberately not the model-vs-actual share difference, which a system-total
shrink (e.g. over-import displacing the class) flatters. Unchanged: the 8 TWh
cap still tops the band (large-ISO bands bit-identical), the ±3.0 pp share leg
still binds independently (MISO `CC_REGULAR` +47 TWh / +7.7 pp still fails
both legs), and the 2%-of-load term still governs wherever it is the wider
one. Effects, measured over all 26 registered runs against a pre-change
snapshot: **exactly one row flips** — CAISO keeper
`2026-08-17-caiso-200-h1-memberpanel` C1 2023 `CC_REGULAR` `FAIL → PASS`
(C1 criterion `FAIL → PASS`; its determination stays `NOT-YET` on the standing
C3a mean-LMP miss). No other record and no determination label changes
anywhere. Scorer-only: no re-solve, keepers re-score in place. Prior banner,
v3.3: (2026-08-17 owner
amendment, session nyiso-calibration-declaration. Directive verbatim: *"NYISO
should be declared calibrated. C3c is an acceptable miss and shouldn't change a
declaration from calibrated to calibrated with caveats because it's a known
model limitation that's been ledgered"*. **A ledgered caveat no longer
DOWNGRADES the determination.** Since v3.1 ledgering is restricted to C3c alone,
so this is exactly and only the owner's rule: an accepted, ledgered C3c
price-tail limitation is **reported** but is not the thing that turns
`CALIBRATED` into `CALIBRATED-WITH-CAVEATS`. This **withdraws** the v3.0–v3.2
clause *"never `CALIBRATED`"*; CLAUDE.md rule 22's C3c standing-rule guard (d)
is amended in step. What is **not** loosened: the C3c band, tier and reported
magnitude are untouched; C3c still reads `CAVEAT` and never `PASS`, so
`grade_summary.target_grade` does not absorb it; the ledger entry (or the
standing rule's auto-entry) is still required; **every other route to a caveat
still downgrades** — commercial-band target misses, protective-gate caveats,
unscored criteria and data-blocked years; and the budgets are untouched and
still checked first. So a run reads `CALIBRATED` only when a ledgered C3c is its
**single** blemish. Effects, measured over all 26 registered runs against a
pre-change snapshot: **6 determinations change, all `CALIBRATED-WITH-CAVEATS →
CALIBRATED`**, of which **two are keepers** — NYISO
`2026-08-16-nyiso-140-layup-exclusion` (the requested ISO) and NEISO
`2026-08-17-neiso-99-joint-p1` (an unavoidable cross-ISO consequence: the scorer
is one instrument, and an ISO-scoped verdict rule would be an off-registry
tuning channel in spirit, rules 24/25). No `NOT-YET` is reclassified;
CAISO/ERCOT/MISO/PJM are unchanged. Scorer-only: no re-solve, keepers re-score
in place. Full detail in §9. Prior banner, v3.2: (2026-08-09 owner
amendment, session neiso-keeper-87-control. Directive verbatim: *"make sure c3c
is an acceptable caveat for any holdout or training year"*. **(a) The C3c
standing rule fires in EVERY year**, not out-of-training only — a LONE C3c
`FAIL` with governance passing auto-ledgers to `CALIBRATED-WITH-CAVEATS` on
2023–2025 exactly as it already did on the holdout tiers. Not a loosening of the
band: in-sample the same reclassification was already reachable via an explicit
exceptions-ledger entry — the route every current keeper with a C3c caveat used
— so the split governed who typed the justification, not what a run could claim.
The guards are unchanged: lone failure only, governance must PASS, supporting
tier only (fail-closed), never `CALIBRATED` *(this clause of the v3.2 banner is
**superseded by v3.3 above** — every other guard it lists survives intact)*, and
it still spends the single
ledgerable slot. **(b) A defect is fixed in the same amendment**: "lone" was
measured over every scored record including the REPORTED-ONLY streams the rubric
demoted out of the determination (C5a `co2`, removed at v2.9), so a `co2` FAIL
silenced the rule — it is now measured over `CRITERIA` membership. That
under-fired out-of-training years too, so (b) is a correction, not part of (a).
Effects, measured over all 66 registered runs: **2 determinations change, both
NYISO non-keeper probes** (`2026-08-06-nyiso-130-control`/`-n11-tsl`, `NOT-YET →
CALIBRATED-WITH-CAVEATS`), both unlocked by (b); **every keeper of all six ISOs
is unchanged**. Scorer-only: no re-solve, keepers re-score in place. Full detail
in §9. Prior banner, v3.1: (2026-08-06 owner
amendment, session-logged. TWO changes, both narrowing what a determination may
excuse. **(a) Ledgering is restricted to C3c alone** —
`calibration_verdict.LEDGERABLE_CRITERIA`, fail-closed: an exceptions-ledger
entry naming any other criterion is ignored and the FAIL stands. C3c is the one
criterion with no published commercial comparable, so a documented bound is its
honest reporting form; every other criterion is scored against a published
comparable and its band **is** the certification claim. Both caveat budgets
collapse as a consequence — protective 1 → **0**, non-protective 3 → **1**.
**(b) C7 diurnal shape is RETIRED** from the report and the determination
outright, on the finding — already recorded in §8 before the amendment — that
the protective gates are "beyond commercial practice" with no external anchor;
`score_shape` and `C7_GATED_CLASSES` are deleted per rule 26 `[R-DELETE]`, while
the D-1 measurement they read survives untouched and still gates through C8's
grounded-above-budget escalation. Scorer-only: no re-solve, keepers re-score in
place. Effects: CAISO CALIBRATED-WITH-CAVEATS → **NOT-YET** (C3a 2024 +11.7 %,
2025 +14.8 %, formerly ledgered) and its `complete` marker + frontier claim
withdrawn; MISO C3a `CAVEAT → FAIL`, label unchanged; NEISO/PJM/NYISO/ERCOT
unchanged. Full detail in §2, §3, §9. Prior banner, v3.0,
2026-08-05 owner amendment, ERCOT-2023-diagnosis session: a second ledgered
caveat kind, **`ACCEPTED MODEL-CLASS LIMITATION`** — exceptions-ledger entries
carrying `"kind": "model-class"` reclassify a FAIL to a budgeted ledgered
CAVEAT exactly like the measured-input kind, but are admissible **only for
SUPPORTING-tier criteria** (fail-closed: matched against a load-bearing or
protective criterion the entry is ignored and the FAIL stands). Each entry is
an owner-signed acceptance of a limitation of the model *class* itself and
must cite the exhaustion record that bounds it plus any still-open residual
lane — it documents a bound, it never closes root-causing; a later mechanism
that fixes the criterion simply PASSes and the entry goes inert. First
application: ERCOT C3c 2023–2025 (§3, §9). The "3.0" is forced by the
one-decimal version float (2.9 + 0.1), **not** a re-anchor of the v2 criterion
set — every criterion, band and tier is unchanged from v2.9. Prior banner,
v2.9, 2026-07-27 owner amendment: **C5a CO2 vs eGRID REMOVED from the rubric
and demoted to REPORTED-ONLY** — eGRID's latest released workbook is the 2024 vintage and
`data.egrid.egrid_vintage_for_year` falls any later year back to it, so a 2025
C5a "actual" is the 2024 intensities standing in rather than a measurement, and
a criterion whose actual does not exist for a scored year cannot be
load-bearing. Same grounds and same mechanism as the v2.7 C5b/C5c removal:
`score_co2` still runs and its number stays on the payload and the dashboard run
pages, but `co2` is no longer in `CRITERIA`, so it contributes no status to the
determination and consumes no caveat budget. Restoration is an owner act and
should be **year-scoped** — 2023 and 2024 DO have their own released vintages;
only years past the latest vintage lack a measured actual. **Knock-on:** C5a was
the last criterion with a distinct commercial band (C3a/C3b collapsed to
single-band at v2.3; C2's band survives only on the preliminary-EIA-923 fallback
path that v2.5 made SKIPPED-never-gated), so **no scored criterion can currently
produce an auto COMMERCIAL_BAND caveat** — pinned by an invariant assertion in
`tests/scoring/test_calibration_verdict.py`. Prior: 2026-07-06
fitness-for-purpose re-anchor + 2026-07-07 C8 grounded-above-budget escalation
+ 2026-07-09 C3a/C3b single-band re-set, C5a full-plant CO2 re-base and
like-for-like load-weighted actual basis
(`docs/rubric-v24-price-basis-memo-2026-07.md`) + 2026-07-13 C2
complete-vintage-only gating + 2026-07-16 v2.6/v2.7 owner amendments: C3c
gated on the actual RT hourly scarcity tail for every ISO, C5b/C5c storage
criteria removed from the rubric; full history in §9). This document is the single
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
nothing unscored — **except**, since v3.3, a single ledgered C3c caveat, which
is reported on the determination basis instead of downgrading the row. So
`CALIBRATED` no longer implies "nothing was missed"; it implies "nothing was
missed **other than** an owner-accepted, ledgered scarcity-tail limitation,
stated in the verdict". Read `caveats.ledgered` / `grade_summary.ledgered` to
see whether a given `CALIBRATED` run carries one.
Both determinations remain conditional on the protective
anti-self-deception gates (C6/C8 — C7 was retired at v3.1), which are what
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
| **SUPPORTING** — informative, not certification-critical | Hourly dispatch timing (r/NRMSE); scarcity-tail hour counts (the *level* contribution of scarcity is already in C3a/C3b; the count is a diagnostic of the scarcity mechanism, and no intended use consumes exact tail-hour counts) | C3c, C4 |
| **REMOVED** — no longer part of the rubric (v2.7) | Storage cycling volume/season (ex-C5b/C5c): EIA-930 storage-dispatch data is not reliable enough to participate in a calibration determination at any level (missing/partial breakouts; the one scored year was fabricated zeros). Removed outright by the 2026-07-16 owner amendment (v2.6(c) had briefly held them report-only). Storage numbers stay visible on the dashboard run pages as payload/bench diagnostics. | (ex-C5b, ex-C5c) |
| **PROTECTIVE** — make the other rows believable | Governance (no residual fitting / pinning); forced-energy budget (floors are scaffolding, not dispatch), including the D-1 diurnal-shape test its grounded-above-budget escalation applies | C6, C8 — v1 logic, minus C7 (retired v3.1) and with no ledgered excuse available (budget 0, v3.1) |
| **OUT OF REPRESENTATION** — the test must not demand these | The DA−RT risk premium (DART) an offer-cost, realized-weather LP cannot price without fitting; hourly-exact dispatch of individual units (NREL TP-581-42305’s explicit guidance) | scored as report-only diagnostics (C3a DA row; C3c’s non-gated DA companion row — every ISO gates on the actual RT hourly tail since v2.7), never gated |

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
| `frontend/data/backcast/tail/actual_tail.json` | committed part (`scripts/data/derive_actual_tail.py`) | the C3c actual: per-(ISO, year) RT (gated, v2.7) and DA (diagnostic) scarcity-tail hour counts at the §5 threshold, with coverage fractions (2023–2025 only — rule-22 holdout guard in the deriver) |
| `results/calibration/<name>/run_config.json`, `meta.json` | bundle | governance config (outage source, lever flags), gas vintage |
| `results/calibration/<name>/calibration_attestation.json` | bundle (this rubric) | governance attestation + the exceptions ledger |
| `results/calibration/<name>/legitimacy_diagnostics.json` | bundle (S1 suite) | machine artifact of `scripts/legitimacy_diagnostics.py --json-out` — the D-2 per-class forced-share summary C8 scores, plus the D-1 diurnal-shape rows C8's grounded-above-budget escalation reads (D-1 is still measured and still gates through C8; the C7 criterion that also read it was retired v3.1). The verdict never recomputes the diagnostics |

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
LIMITATION` only by a matching entry in the exceptions ledger (§3) — and since
**v3.1, only for C3c**: on every other criterion a miss is a `MODEL MISS` that
no ledger entry can excuse.

Criteria carry a **tier** (§0): `LOAD-BEARING`, `SUPPORTING`, or `PROTECTIVE`.
The v1 HARD/SOFT split is retired — it conflated strict data gates (C1/C2) with
the anti-gaming gates (C6/C8, and C7 until its v3.1 retirement); the protective
tier keeps the v1 hard-gate semantics, and since v3.1 no protective criterion is
ledgerable at all.

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
    **`min(max(2.0% of ISO total load, 3.0% of actual total generation),
    8 TWh)`** (`SUM_TOL_LOAD_FRAC = 0.02`, gen-floor = `SUM_TOL_SHARE_PP`/100,
    `SUM_TOL_LOAD_CAP = 8` — model grid-LP + non-fossil vs (EIA-923 − BTM) +
    EIA-930 nuclear/wind/solar; `calibration_verdict._fuelmix_vol_band`).
    Total load = generation + net imports, so
    net-importing ISOs (NEISO, NYISO) get the correct ≈2 pp band; for
    energy-only ISOs with no interchange, load = gen and the band is unchanged.
    The percent term scales with system size (≈2 pp of load, floored at the
    share leg's own ±3.0-pp-of-mix materiality on the actual-generation basis —
    the **v3.4 owner amendment**, 2026-08-18, banner above: the volume leg may
    never bind tighter than the mix-materiality the share leg itself declares,
    measured on the un-flatterable actual-side denominator) but is **capped at
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
    universal per-class gate (|model−actual| within min(max(2.0% of ISO total
    load, 3.0% of actual total generation), 8 TWh) **and** share within
    ±3.0 pp; actual = `classFull` = EIA-923 − BTM). C1 already
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
- **C3c — Tail / scarcity, actual RT hourly.** *(SUPPORTING, single wide band)*
  - *Metric:* count of hours with price above the per-ISO threshold (§5),
    model vs the **actual RT scarcity tail** — hours the real-time market’s
    hourly hub average cleared the threshold — for **every ISO** (v2.7,
    owner amendment 2026-07-16). The RT hourly tail is the scarcity the
    market actually realized; that is the judged quantity. The **DA count is
    the report-only diagnostic row**: it prices scarcity *expectations*, and
    its wedge over RT is the day-ahead weather/load **forecast-risk
    premium**, which a realized-weather (perfect-foresight) backcast is out
    of representation to price — the DA row stays visible next to the gate
    so neither count ever disappears from the verdict.
    *Basis history:* v2 gated the DA-expressible tail everywhere on the
    sub-hourly-transient argument
    (`docs/multi-iso/miso-scarcity-tail-diagnosis.md` §1 decomposed MISO
    2023’s entire 30-hour RT tail into single-hour 5-minute events; DA tail
    that year: 1 h); v2.6(a) moved ERCOT to RT (its DA tail runs *above* RT
    — 2023: 311 vs 181 h — the forecast-risk-premium mirror image); v2.7
    makes RT the uniform judged basis: the owner’s determination is that
    the tail criterion judges realized scarcity, not the DA market’s
    forecast of it. Both counts are hourly hub averages; sub-hourly
    transients that push an hourly RT average over the threshold are part
    of realized scarcity and now gate.
  - *Actual:* the committed `tail/actual_tail.json` part
    (`scripts/data/derive_actual_tail.py`, from the hub RT/DA hourly series;
    coverage-annotated, 2023–2025 only).
  - *Tolerance:* model tail hours within **[0.5×, 2.0×]** of the RT actual —
    a **collapsed tail (0 hours where the RT market had scarcity) FAILs**, and
    an **invented tail (> 2× actual) FAILs**; bounded both ways on purpose.
    When the RT actual is **< 10 h** the ratio is degenerate and
    **|model − actual| ≤ 10 h** gates instead (this also replaces the v1
    token guard against inventing a tail over a ~0 actual, tightened from
    50 h to 10 h). Band width rationale: **no commercial or public model
    publishes tail-hour-count accuracy at all** — the closest practice
    *excludes* spike hours from scoring (ECA excluded ~50–100 h/month) or
    absorbs them into tuned hurdle rates (NYISO); this rubric keeps scoring
    the tail, with the band’s job being order-of-magnitude realism on the
    measured benchmark, not count precision. Supporting tier: the
    *level* contribution of scarcity is already load-bearing via C3a/C3b.
  - *Classification:* `MODEL MISS` (missing scarcity pricing / over-aggressive
    peaker offers). Since v3.0 a C3c FAIL may be reclassified to a ledgered
    `ACCEPTED MODEL-CLASS LIMITATION` by an owner-signed `"kind":
    "model-class"` exceptions entry (§3) — first application ERCOT 2023–2025,
    where the realized RT tail formed on equilibrium scarcity-hour ENERGY
    offers (predominantly storage at $500–3,000 with measured RTORPA ≈ $1–5
    and PRC ≈ 5.8 GW at the missed hours) that a competitive-offer LP cannot
    reproduce, and the within-class mechanism space is exhaustion-cited
    (ercot-95/97/102/107/108/155/159/161/162/163). `SKIPPED` when the model scarcity series is not in the
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

### C5 — CO2  *(C5a REPORTED-ONLY as of v2.9; C5b/C5c REMOVED from the rubric, v2.7)*

> **v2.9 (owner amendment 2026-07-27): C5a is REMOVED from the scored rubric.**
> It is **REPORTED-ONLY** — computed, carried on the payload and rendered on the
> dashboard run pages, but contributing no status to the determination and no
> caveat budget. Reason: eGRID publishes no 2025 vintage, so C5a's 2025 "actual"
> is the 2024 intensities standing in, not a measurement. The definition below
> is retained verbatim as the reported metric's spec and as the restoration
> text; restoring it to LOAD-BEARING is an owner act and should be year-scoped
> to years with their own released eGRID workbook (2022-2024 today).

- **C5a — CO2 vs eGRID.** *(REPORTED-ONLY since v2.9; was LOAD-BEARING two-band)*
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
- **C5b / C5c — Storage throughput and dispatch shape: REMOVED.** *(v2.7
  owner amendment 2026-07-16.)* EIA-930 storage-dispatch data is not
  reliable enough to participate in a calibration determination at any
  level — breakouts are missing or partial for most BA-years, and the one
  fully "scored" year (ERCOT 2024 C5c) turned out to be a correlation
  against nine fabricated pre-breakout zeros (the v2.6(b) data-honesty
  finding). v2.6(c) had retired both criteria to report-only the same
  morning; the owner's follow-up decision removed them from the rubric
  outright — not scored, not printed, no criterion ids in the verdict.
  What remains: the storage payload/bench numbers (throughput TWh, monthly
  discharge vectors) stay committed and rendered on the dashboard run pages
  as diagnostics, and the bench builder keeps the v2.6(b) observed-months
  honesty rule (null, never fabricated 0.0, for unobserved months). Old
  keeper attestations carrying dormant C5b/C5c ledger entries keep them as
  history (they match no criterion and are inert). The pre-removal
  definitions — including the 2026-07-03 discharge-basis alignment fix and
  the CV degeneracy guard — live in this doc's v2.6 history entry and git
  history; re-introducing storage as a criterion is a future owner decision
  and would re-enter as a new amendment.

### D-A — Diurnal price amplitude  *(REPORTED-ONLY and BAND-FREE as of v3.5; never a criterion)*

> **This is a disclosure, not a gate.** D-A is **not** a member of `CRITERIA`.
> It contributes **no status** to the determination, consumes **no caveat
> budget**, is **not** in `LEDGERABLE_CRITERIA`, and its status value
> (`REPORTED`) is deliberately none of the four scored statuses. It exists so
> that a defect present in 36/36 measured cells is visible on every run rather
> than invisible to the model's own quality gate. **Nothing may gate on it**
> — making it gating is an owner amendment, and §9's v3.5 entry records what
> the band sweep found about attempting that.

- **Metric:** the model's **hour-of-day mean price profile range** as a
  percentage of the measured one, plus the phase check (model vs measured peak
  and trough hour, ±1 h) and the hour-of-day profile correlation.
- **Basis:** **RT**, the same benchmark C3a gates the price level on — the model
  is structurally a real-time analogue, so RT is the honest comparison. The
  measured DA profile is carried in the part as the companion.
- **Actual:** committed part `frontend/data/backcast/amplitude/actual_amplitude.json`
  (`scripts/data/derive_actual_amplitude.py`), the measured hour-of-day profile
  per ISO-year over **complete days only** — a day with any missing hour is
  dropped and counted, never interpolated.
- **Model:** reconstructed from the run payload's own `lmpDeltaHr` (hourly
  `model − actual RT`). The hour-of-day mean is linear, so
  `hod(model) = hod(actual) + hod(delta)`. **This is what makes D-A
  scorer-only:** no LP solve, no bundle regeneration and no re-registration —
  every already-registered run scores in place, the same property that made the
  C3c standing rule scorer-only. Hours carrying the `-32768` NOT-A-NUMBER
  sentinel drop their whole day.
- **Tolerance:** **none — band-free by construction.** No external comparable
  exists to anchor one (§9, v3.5), so the number is published without a verdict.
  `tol` is `None` and `classification` is `None` on every record.
- **`SKIPPED`** when no measured part is committed for the ISO-year, when the
  payload predates the `lmpDeltaHr` field, or when the measured profile is
  degenerate. A skip here costs nothing but the disclosure — D-A never gates, so
  it can never turn a skip into a determination effect.
- **Validation:** agrees with the parquet-based reference implementation
  (`scripts/probes/_xiso1_diurnal_amplitude_audit.py`) to a **worst 0.31 pp**
  across all six keepers × three years.

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

### C7 — Diurnal shape  *(RETIRED 2026-08-06, rubric v3.1 owner amendment)*

**C7 is no longer a criterion.** It is dropped from the calibration report and
from the determination altogether — it produces no `PASS`/`FAIL`/`CAVEAT`, it
appears in no verdict output, and it consumes no caveat budget. This is a
**full removal**, stricter than the C5a/C5b/C5c retirements, which left those
criteria computed and `REPORTED_ONLY`: `calibration_verdict.score_shape` and
`C7_GATED_CLASSES` are **deleted** per CLAUDE.md rule 26 `[R-DELETE]`, so the
gate cannot be silently re-armed.

- **Why.** The owner's condition was: retire it *if no other commercial-grade
  model gates or publishes on it*. That condition is met on **this rubric's own
  benchmark evidence**, and was already recorded here before the amendment —
  §8's comparables table scores the protective gates *"beyond commercial
  practice"* and states in terms that C7/C8 gate *"the diurnal shape and
  forced-energy share **no external model reports**"*. Every other graded
  criterion in this rubric is two-band scored against a **published**
  comparable (`docs/rubric-v2-benchmark-memo-2026-07.md`); C7 never had one, so
  its thresholds (`r ≥ 0.8`, CV ratio `≥ 0.5`) were self-set numbers gating a
  determination against nothing external.
- **What survives, deliberately.** The **D-1 measurement itself is untouched**:
  `scripts/legitimacy_diagnostics.py` still computes the per-class hour-of-day
  profile rows, they are still written to every bundle's
  `legitimacy_diagnostics.json`, and **C8 still gates on them** through
  `_d1_shape`. CLAUDE.md rule 20 `[R-FORCED-BUDGET]` makes an over-budget
  class's conditional pass depend on its D-1 profile clearing
  `profile_r`/`cv_ratio`, so retiring the C7 *gate* must not retire the D-1
  *measurement* — and does not.
- **The anti-flat-floor protection is not lost.** The caiso-42 signature
  (model off-peak CV 0.000 against a real 0.35–0.45) was caught twice: by C7 on
  a fixed class tuple, and by C8's grounded-above-budget escalation. It is
  still caught by the second, and the second is the better-aimed test — C7
  gated a hard-coded list of classes, while C8's escalation reads the same D-1
  row for **whichever class is actually being forced past its budget**. Pinned
  as a regression by `DeterminationTests.test_flat_floor_forces_not_yet`.
- **Effect at amendment.** C7 was `PASS` on the CAISO/NYISO/PJM/ERCOT keepers,
  `SKIPPED` on NEISO and `FAIL` on MISO (COAL_PRB 2025). Only MISO's reported
  basis changes, and its `NOT-YET` label is unaffected — C3a fails it
  independently under the same amendment's ledger narrowing.
- **Historical record.** The retired criterion's full specification — metric,
  gated-class set, tolerances, materiality floor and the D-7 statistical-mode
  evidence that motivated it in 2026-07-04 — is preserved in this file's git
  history at the v3.0 revision.

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
- **Coal is scored per SUBCLASS (v3.9, owner ruling C8-SUBCLASS 2026-09-25):**
  `COAL_BIT`, `COAL_PRB`, `COAL_LIGNITE` and `COAL_WC` are each a C8 class in
  their own right — each with its own D-2 forced share and class denominator,
  its own ≥ 2 %-of-load materiality test on max(model, actual) **subclass**
  energy, its own 30 % merchant cap and its own grounded-above-budget
  escalation (D-1 already emitted per subclass; every coal-mechanism D-4
  window is class-agnostic, so no window moved). An over-cap subclass can no
  longer hide inside a coal family whose pooled share passes, and a subclass
  below 2 % of load is `SKIPPED`-immaterial even where coal as a whole is
  material. No constant was added or moved. An artifact written before v3.9
  carries one legacy `COAL` family row per year and still reads as the family
  (`PLANT_GROUP_MEMBERS`); every registered run's artifact was re-split in
  place by `legitimacy_diagnostics.py --resplit-coal-d2` (zero LP).
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
- **Ledgered caveats** — an out-of-tolerance (beyond-commercial) criterion
  reclassified by an explicit exceptions-ledger entry (§3). Two
  classifications share one budget pool: `ACCEPTED MEASURED-INPUT LIMITATION`
  (the actual/benchmark is the limitation — the v2 kind, unchanged) and, since
  v3.0, `ACCEPTED MODEL-CLASS LIMITATION` (ledger entry `"kind":
  "model-class"` — an owner-signed acceptance that the model *class* cannot
  express the judged behaviour, admissible for **supporting-tier criteria
  only** and requiring a cited exhaustion record; see §3).

  **v3.1 (owner amendment 2026-08-06) — only C3c is ledgerable at all.** The
  budgets below are no longer independent numbers; they are the arithmetic
  consequence of that one restriction, since caveats aggregate per criterion:
  - **Ledgerable set:** `{C3c}` (`calibration_verdict.LEDGERABLE_CRITERIA`).
    Every other criterion stands or falls on its own band, ledger entry or not.
  - **Protective criteria (C6/C8):** budget **0** — no protective criterion is
    ledgerable, so a C8 forced-share `FAIL` is `NOT-YET`, full stop. This is
    *stricter* than v1/v2, which allowed one protective gate to be excused;
    CLAUDE.md rule 20 / audit D-1/D-2 enforcement is hardened, not relaxed.
  - **Everything else:** budget **1** — C3c is the single ledgerable
    criterion, so 1 is the true ceiling and publishing “0/3” would advertise
    slots that cannot be filled.
  Both budget checks are retained as defense-in-depth invariants: they are the
  assertion that re-widening the ledgerable set without an owner amendment
  cannot silently buy back excuse capacity.

  **v3.3 (owner amendment 2026-08-17) — a ledgered caveat is REPORTED, not
  DOWNGRADING.** A within-budget ledgered caveat no longer moves the overall
  determination from `CALIBRATED` to `CALIBRATED-WITH-CAVEATS`. Because the
  ledgerable set is `{C3c}`, this says exactly one thing: *a known, ledgered
  scarcity-tail limitation is not a caveat on the calibration*. It changes what
  the caveat **costs**, not what it **is** —
  - C3c still reads `CAVEAT`, **never `PASS`**, so `grade_summary.target_grade`
    does not absorb it and the miss is visible on every report;
  - the magnitude is still printed in full, the criterion is still listed in
    `caveats.ledgered` and counted in `grade_summary.ledgered`, and the caveat is
    still named on the determination basis of a `CALIBRATED` run;
  - the ledger entry (or the C3c standing rule's auto-entry) is still required,
    with its exhaustion citation;
  - **the budgets are unchanged and are checked first**, so >1 ledgered or >0
    protective caveats is still `NOT-YET`. The 1-slot ledgered budget is now the
    *sole* numeric bound on what may be carried without a downgrade;
  - **every other caveat route still downgrades** — commercial-band target
    misses, protective-gate caveats, `SKIPPED` criteria and data-blocked years
    are untouched *(amended at v3.7 below: a `SKIPPED` **C3c** is now exempt
    from this route too; every other `SKIPPED` criterion still downgrades)*;
  - and the `FAIL` path is untouched: a C3c miss that is not ledgerable, because
    a second criterion also fails or governance does not pass, still stands as a
    `FAIL` and still carries the run to `NOT-YET`.

  **v3.7 (owner instruction 2026-09-10) — an UNSCORED C3c does not downgrade
  either.** Verbatim: *"If c3c is the only caveat the status should be
  calibrated not with caveats."* v3.3 above delivers that for a **ledgered**
  C3c, but only through `_apply_c3c_standing_rule`, which sees C3c **only when
  it is scored and failing**. Where the ISO-year has no scarcity bench, C3c is
  `SKIPPED` instead, falls into the unscored-criteria route, and downgrades by a
  path the standing rule cannot reach. The same accepted model-class limitation
  therefore downgraded or did not **depending on whether a bench happened to
  exist** — a property of the data, not of the model. C3c is now exempt from
  that route as well.
  - **Fail-closed on v3.1's own restriction:** the exemption reaches
    `LEDGERABLE_CRITERIA` (`{C3c}`) **and** only at SUPPORTING tier, so it can
    never reach an unscored load-bearing (C1/C2/C3a/C3b) or protective (C6/C8)
    criterion. An unscored C8 still downgrades as an *unscored PROTECTIVE*
    criterion, and governance is tested before this branch, so a failing or
    unattested C6 still short-circuits to `NOT-YET`.
  - **Still reported, which is what stops it being an escape hatch:** C3c keeps
    its `SKIPPED` status, stays in `criteria`, and is **named on the
    determination basis** by its own explicitly non-downgrading reason line —
    the same contract the v3.3 ledgered line carries.
  - **Both caveat budgets are untouched and are still checked first.**
  - **Effect at amendment, measured over all 36 registered runs and every
    per-year subset against a pre-change snapshot rather than asserted: ZERO
    determinations change.** No committed row has C3c as its only downgrading
    item; the single record that moves is MISO `2026-09-10-miso-251-tp2020`,
    whose reason line splits from `unscored criteria: price_mean, price_shape,
    price_tail` into `unscored criteria: price_mean, price_shape` plus the new
    non-downgrading C3c line — and it stays `CALIBRATED-WITH-CAVEATS`, because
    two **load-bearing** criteria are still unscored there. This is a
    forward-looking correction governing the first ISO-year to lose only its
    tail bench. No solve ran; every keeper re-scores in place.

  **Why C3c and nothing else.** C3c is the one criterion with *no published
  commercial comparable at all* (§5 / the C3c band note: no commercial or
  public model publishes tail-hour-count accuracy), so a documented,
  exhaustion-cited bound is the honest reporting form for it. Every other
  criterion is scored against a published comparable (§8), and for those the
  band **is** the certification claim. C3a mean LMP is the case that forced
  the amendment: a mean-LMP miss beyond ±10% is a `MODEL MISS`, and ledgering
  it certified a price level the model does not reproduce.

  *Superseded budget rationale (v2, retained for genealogy):* the former
  3-slot non-protective budget replaced the 2026-07-02 3→2 cut on the argument
  that the recurring documented data-limitation classes are three by
  construction — the preliminary-923 vintage, EIA-930 storage-series coverage,
  and a data-blocked scarcity-requirement series — and that a budget of 2
  mechanically forced `NOT-YET` on *data availability* rather than model
  quality. Two of those three classes attached to criteria the rubric has
  since removed outright (C5b/C5c storage, v2.7) or made
  `SKIPPED`-never-gated (the C2 preliminary-vintage fallback, v2.5), so the
  surviving class is the scarcity-tail series — C3c, exactly the one slot v3.1
  keeps.

**Determination:**

| Outcome | Conditions (all must hold) |
|---|---|
| **CALIBRATED** | C6 governance `PASS`; no `FAIL`; no `SKIPPED`; no data-blocked target year; no commercial-band caveat and no protective caveat. **v3.3:** a **ledgered** caveat is permitted here — it can only be C3c, it is within budget by the row below, and it is reported on the determination basis rather than downgrading the row. (Through v3.2 this row required *every* criterion at clean target grade.) |
| **CALIBRATED-WITH-CAVEATS** | C6 governance `PASS`; **no** `FAIL` on any criterion; ledgered caveats within budget (v3.1: ≤0 protective, ≤1 other — and only C3c is ledgerable at all) and **every** ledgered caveat has a ledger entry; one or more of {a **commercial-band** caveat exists, a criterion is `SKIPPED` (e.g. C8 with no committed `legitimacy_diagnostics.json` — named explicitly in the reasons), a target year is data-blocked}. *(v3.3 removed "any caveat exists" from this trigger list: the ledgered kind no longer downgrades, the other kinds still do.)* **Certifies: intended-use delivery at or above commercial grade.** |
| **NOT-YET** | anything else — governance not `PASS`/`UNATTESTED`; **or any criterion `FAIL`** (an out-of-tolerance criterion with no ledger entry is a `FAIL` *by construction*); or a ledgered-caveat budget is exceeded. |

The decisive rule, restated: **a determination with an undocumented
out-of-tolerance criterion is `NOT-YET`.** The only way a beyond-commercial-band
criterion is compatible with a passing determination is an explicit ledgered
caveat — `ACCEPTED MEASURED-INPUT LIMITATION`, or (supporting tier only, v3.0)
`ACCEPTED MODEL-CLASS LIMITATION` — and only within the caveat budget.

Where an actual is not committed for an ISO-year (historically the tail and
CO2, both now committed), the criterion is `SKIPPED`, which **caps the best
attainable determination at `CALIBRATED-WITH-CAVEATS`** until a run surfaces
it. This is intended: you may not claim a *fully* calibrated ISO while any
criterion is unscored. (v2.6(c) briefly carried a report-only RETIRED
exception for C5b/C5c; v2.7 removed those criteria outright, so every
criterion in the rubric is again a judgment.)

---

## 3. The exceptions ledger (required, auditable)

**v3.1 (owner amendment 2026-08-06) — C3c is the only ledgerable criterion.**
An entry naming any other criterion is **ignored**, whatever its kind or reason,
and the `FAIL` stands (`calibration_verdict.LEDGERABLE_CRITERIA`, enforced
fail-closed in `_apply_ledger`). Entries for other criteria that already sit on
committed attestations are **not deleted** — they stay on their bundles as the
historical record of what was accepted and why — they simply stop reclassifying
anything, so every keeper re-scores in place from committed artifacts with no
re-solve and no bundle regeneration. The rest of this section describes the
mechanics that still apply, now scoped to C3c.

Every **ledgered** `CAVEAT` must be earned by an explicit ledger entry (auto
commercial-band caveats are machine-derived from the committed artifacts and
need none — they are listed by the scorer itself). The ledger lives in the
bundle at `results/calibration/<name>/calibration_attestation.json` (per-run,
conflict-free, committed with the bundle). A beyond-commercial-band criterion
with **no matching ledger entry is a `FAIL`** — silence is never a pass.

Each entry must name **the metric (criterion, and class/family where the criterion
is per-class), the year, the magnitude (the observed error), and the reason it is
an accepted measured-input limitation rather than a model defect.**

**Model-class entries (v3.0).** An entry carrying `"kind": "model-class"` is the
owner-signed variant for a limitation of the model *class* itself rather than of
the benchmark. It is admissible **only for supporting-tier criteria** (the
scorer ignores it — fail-closed — against load-bearing and protective
criteria), and its `reason` must additionally carry: (a) the **owner decision**
(date + session), (b) the **exhaustion record** — the runs/probes that bound
the limitation and refuted the within-class mechanism families, and (c) any
**still-open residual lane**, because the caveat documents a bound and never
closes root-causing — a mechanism that later fixes the criterion simply PASSes
and the entry goes inert in place.

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

**What is ledgerable, after v3.1:** the C3c scarcity-tail count, and nothing
else. Either kind applies to it — `ACCEPTED MEASURED-INPUT LIMITATION` where a
data-blocked scarcity-requirement series is the binding constraint, or the
owner-signed `ACCEPTED MODEL-CLASS LIMITATION` of v3.0 once the within-class
mechanism space is exhaustion-cited (C3c is supporting-tier, so the v3.0
tier guard admits it).

**Everything else is `MODEL MISS` and must be fixed, not excused** — a coal/gas
split error, a fleet-correlation floor breach, an over-cycling storage fleet, a
preliminary-vintage system-volume residual, and **C3a mean LMP above all**. C3a
is the case that forced the amendment: CAISO's keeper carried +11.7 % (2024)
and +14.8 % (2025) as ledgered measured-input limitations and was certified
`CALIBRATED-WITH-CAVEATS` on that basis, which certified a price level the
model does not reproduce. A mean-LMP band is not an excuse budget; it is the
claim. An empty in-model lever queue on a non-ledgerable criterion is an **open
root-cause item** (CLAUDE.md rule 1 `[R-STRUCT]`, rule 20 `[R-DOF]`: “a
residual that can only be closed by a tuned value is an open root-cause issue,
not a parameter”), never a documentable bound — and it never licenses closing
the residual with an adder, haircut or any value tuned to it (rules 1/13).

*(Superseded examples, retained for genealogy: NEISO's model-zeroed
`CT_PEAKER` C1 entry and the 2025 preliminary-923 vintage C2 residual were the
v2 named accepted-limitation cases. Both are now inadmissible; both are dormant
on their bundles rather than active, so no determination moved on them.)*

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
scored on a criterion set another ISO isn’t. **v2.7 restores full basis
parity:** every ISO gates on the **actual RT hourly tail**, with the DA
count as the report-only diagnostic — see §C3c (v2.6 had briefly split the
basis per-ISO via `TAIL_BASIS`, ERCOT RT / others DA; that switch is gone).
(The same parity rule applies to the reported D-7 statistical-mode gap:
quote fail counts on the same criterion denominator for every ISO — the
2026-07-03 measurements mixed C1–C8 and C1–C5c denominators and are flagged
stale for re-measurement.)

| ISO | Threshold (hub LMP) | Gated basis (v2.7) | Scarcity driver |
|---|---|---|---|
| ERCOT | $200/MWh | **RT hourly** (DA = diagnostic) | summer/ramp scarcity; DA embeds the forecast-risk premium |
| PJM, MISO, CAISO | $200/MWh | **RT hourly** (DA = diagnostic) | summer/ramp scarcity |
| NYISO, NEISO | $300/MWh | **RT hourly** (DA = diagnostic) | winter city-gate scarcity sets the tail higher |

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
| C1 per-class mix | min(max(2% load, 3% actual gen), 8 TWh) & 3 pp | (single-band) | **none published** — external validations stop at family/zonal level; we score stricter deliberately |
| C2 family volume (prelim fallback) | ±2.5% | ±5% | NYISO zonal energy ~0–4%; AEO 1–3-yr gas-gen SD 5.7–9.6% (forecast upper bound) |
| C5a CO2 (full-plant basis, v2.3) | ±7% | ±10% | **no published PCM backcast CO2 error**; AEO 1–3-yr CO2 SD 3.2–4.9% (forecast) |
| C3c tail hours (actual RT hourly basis, v2.7) | [0.5×, 2×] | (single wide band) | **none published** — practice excludes spike hours from scoring (ECA) or tunes hurdle rates (NYISO); we keep scoring it |
| C4 hourly fleet r | r ≥ 0.70, NRMSE ≤ 0.30 | (single-band) | **none published**; NREL guidance: hourly comparison “not a valid test” — we score stricter deliberately |
| C6/C8 protective | pass/fail | — | **beyond commercial practice**: NYISO closed its residual with tuned hurdle rates; SEM tunes generator markups; our C6 forbids exactly that. *(This row is the evidence C7 was retired on at v3.1: “beyond commercial practice” means **no external anchor exists** for the protective gates. C6 and C8 keep their places anyway — they enforce CLAUDE.md rules 13/20 rather than claim accuracy against a comparable — but a diurnal-shape ACCURACY gate with no published counterpart was doing neither.)* |

Honesty in both directions: where the six keepers sit **below** commercial
grade (CAISO mean price +20–42%; MISO CC_REGULAR +44 TWh; collapsed RT tails
in MISO/CAISO and the NYISO 2024 tail miss surfaced by the v2.7 RT re-basis),
the verdict says `NOT-YET` — the benchmark table is never a curve to grade
down to.

> **Ratification note (owner decision 2026-07-27, miso-96).** v2.8 widened a
> PROTECTIVE gate set — a change that retroactively re-graded designated
> keepers in two lanes it was not itself working in (ERCOT-115 C7 PASS → FAIL,
> MISO-88 → NOT-YET, both named in its own commit message) — but it shipped
> WITHOUT the `owner amendment <date>` marker every prior tolerance change
> carries (v2.1, v2.2, v2.3, v2.7). The owner reviewed it on 2026-07-27 and
> **ratified it as written**: the widening is scope-only (which classes may
> fail), the thresholds are unchanged at `profile_r ≥ 0.8` / `cv_ratio ≥ 0.5`,
> and the failures it exposed are real — MISO COAL_PRB was independently
> confirmed and root-caused by A/B in miso-96
> (`results/calibration/FINDING-miso96-coal-prb-offpeak-2026-07.md`). The
> ERCOT COAL_LIGNITE 2023 exposure (r 0.745, cv_ratio 0.294) is NOT yet
> diagnosed and is an open item for that lane.
>
> **The precedent is the marker, not the outcome:** a change to a protective
> gate set, a tolerance, or anything else that can flip a determination is an
> owner amendment and must be dated and attributed as one at the point of
> change. Ratifying this one after the fact does not license the next one.

## 9. Version history

- **v3.9 (2026-09-25, owner ruling C8-SUBCLASS — "Yes" to the open question of
  `docs/handoffs/RESULT-coal-sub-2026-09-25.md` §6, "Keep family-level C8, or
  move C8 to per-subclass?")** — **C8 scores each coal subclass as its own
  class** (`COAL_BIT` / `COAL_PRB` / `COAL_LIGNITE` / `COAL_WC`): own D-2 forced
  share and denominator, own ≥ 2 %-of-load materiality on max(model, actual)
  subclass energy, own 30 % merchant cap, own grounded-above-budget escalation
  (§1 C8). **No constant added or moved; no D-4 window keyed on coal existed**
  (every coal-mechanism window is `(mech, None)`). The change is in
  `legitimacy_diagnostics.aggregate_floors_by_plant` (the coal-family fold of
  the plant-class vote is deleted, rule 26) plus `_resplit_legacy_coal`
  (a pre-COAL-SUB floors npz is re-split by `unit_id` against a `fleet_only`
  rebuild — exact, never positional). The scorer already iterated the
  artifact's own class rows; its one change repairs the legacy family
  reader, whose v2.8 member-bridge stayed shut whenever a pre-COAL-SUB
  payload carried a non-zero generic-bucket `COAL` value — SPP 2019–2021 coal
  (~74–96 TWh) had been read as 0.0 % of load and `SKIPPED`-immaterial. Every
  registered run's `legitimacy_diagnostics.json` was re-split in place,
  zero LP (`--resplit-coal-d2`: committed run payload + `fleet_only` floors;
  non-coal rows byte-identical; per-year family cross-check recorded under
  `coal_subclass_resplit`). **Effect: no C8 status and no determination
  changes on any registered run**; per-subclass shares, the SPP un-blinding
  and the cross-check are in `docs/handoffs/RESULT-c8-coal-subclass-2026-09-25.md`.

- **v3.5 (2026-08-25, owner decision — session xiso-amplitude-rubric-card;
  the owner selected option (B) of
  `docs/DECISION-CARD-xiso-diurnal-amplitude-rubric-2026-08.md`)** — adds
  **D-A, the BAND-FREE REPORTED-ONLY diurnal price-amplitude measurement**
  (`calibration_verdict.score_diurnal_amplitude`, §5a below). **No criterion is
  added to `CRITERIA`; `LEDGERABLE_CRITERIA` (`{price_tail}`) and
  `MAX_LEDGERED_CAVEATS` (1) are UNCHANGED; no determination moves.**

  **The defect it discloses.** xiso-1 (2026-08-01) measured diurnal price-
  amplitude compression in **36 of 36** ISO × year × benchmark cells: daily MAX
  under-priced and daily MIN over-priced *everywhere*, hour-of-day amplitude a
  mean **~45 % of measured vs RT**, while the annual LEVEL is right to ~7 % and
  the PHASE is right in 34/36 rows. The level **passes by cancellation** — the
  trough is over-priced by about as much as the peak is under-priced — and **no
  criterion sees it**: C3a is a level test, C3b a 12-month load-weighted NRMSE
  structurally blind to hour-of-day for every ISO, C3c a tail count, and C7 —
  the one criterion that ever scored a diurnal shape — was retired at v3.1. A
  keeper can read `CALIBRATED` on 8/8 criteria while reproducing **29.5 %** of
  the measured daily price swing, which is PJM's today.

  **Why REPORTED-ONLY and BAND-FREE rather than a gate.** The xiso-6 sweep
  (`scripts/probes/_xiso6_amplitude_criterion_band_probe.py`, transcript
  `results/calibration/PROBE-xiso6-amplitude-criterion-bands-2026-08-25.txt`)
  measured what a *gating* criterion would do at ten candidate bands × six ISOs
  × three candidate tiers, offline over the committed records. It is **vacuous**
  below a 25 % amplitude floor — every keeper passes, including one at 20.8 % —
  and **universal** above 45 %, where five or six of six ISOs FAIL and all three
  `CALIBRATED` determinations are lost. The entire dynamic range is floors
  **20–45 %**, and **no external comparable exists** anywhere in it: every graded
  criterion here is two-band scored against a published anchor (C3a's ±10 % is
  SEM-20-004; C3b's 0.20 NRMSE is SEM's accepted backcast), and there is no
  published counterpart for diurnal price amplitude. That is **precisely the
  ground C7 was retired on at v3.1** (§8's comparables row: *"a diurnal-shape
  ACCURACY gate with no published counterpart"*). So v3.5 applies v3.1's own
  disposition to prices: **the gate is not built and the measurement is kept.**
  The measurement therefore carries **no band, no threshold and no verdict** —
  its status is `REPORTED`, which is not one of the four scored statuses.

  Three further findings from the sweep, recorded because they bear on any
  future attempt to gate this:
  - **Tier is nearly inert.** Load-bearing and supporting tier give *identical*
    determination tables (a FAIL forces `NOT-YET` at every tier; a
    commercial-band caveat downgrades identically), and protective is strictly
    harsher (`MAX_PROTECTIVE_CAVEATS` = 0). Supporting tier's only benefit —
    model-class ledgering — is unreachable twice over: `LEDGERABLE_CRITERIA` is
    `{price_tail}` alone since v3.1, and the single ledger slot is **already
    occupied by a ledgered C3c at five of six ISOs**.
  - **It would gate at least four different objects with one number** (rule 19
    `[R-ONE-MECH]`). The four ISOs that have decomposed their own cell disagree:
    NYISO's is reserve-price formation (its reserve-stripped energy swing is
    117/97/107 % of actual — essentially *no* energy-side defect), NEISO's is
    explicitly *not* NYISO's (reserve owns 33/43/32 %; the miss is an
    over-dear trough), MISO's is a two-sided night floor, and CAISO's is
    south-concentrated with NP15 **under**-priced in its mid bucket — opposite
    sign. Marking NYISO down on a statistic its own decomposition explains away
    would be a false negative the rubric could not detect.
  - **The cancellation coupling.** The trough half is over-priced in **18 of 18**
    ISO-years; a peak-only repair moves the C3a level error up 3–13 pp and flips
    **load-bearing, non-ledgerable** C3a from PASS to FAIL at PJM 2023, CAISO
    2024 and NEISO 2024. A gate rewarding closed amplitude would price a real
    criterion against a synthetic one.

  **Verified, not asserted.** All 55 registered runs were re-scored before and
  after: **zero determination diffs, zero per-criterion status diffs, zero
  caveat/grade-summary diffs**, with 161 D-A records produced and 0 skipped.
  Pinned by `DiurnalAmplitudeReportedOnlyTests.test_IT_CANNOT_GATE`.

  **Two fixes carried in the same amendment, reported rather than buried:**
  - `REPORTED_ONLY` records were **computed and then silently dropped** — only
    `CRITERIA` members reach `per_criterion`, so C5a `co2` has been scored and
    discarded by the verdict since v2.9. "Reported-only" reported nothing. The
    verdict now carries a `reported` block, rendered in `render_text` and
    condensed into `metrics.json`, assembled *after* the determination and
    feeding nothing back into it.
  - **A latent instrument defect:** `lmpDeltaHr` reserves `-32768` as its
    NOT-A-NUMBER sentinel, and MISO 2025 hour 8759 has no committed actual.
    Read as a value it blows that ISO-year's amplitude from 20.8 % to 186.9 %.
    The scorer masks the sentinel and drops the whole day. *Filed for other
    lanes, not acted on here (rule 25): at least seven committed probes decode
    `lmpDeltaHr` directly and may carry the same corruption.*

- **v3.4 (2026-08-18, owner amendment — session caiso-c1-lmp-pricing;
  directive verbatim: "Ccgt is fine at -1.8% for passing c1 gate … I want … a
  shift that declares c1 for 2023 calibrated")** — **the C1 volume band is
  floored at the share leg's own materiality scale:**
  `vol_band = min(max(2.0% of ISO load, 3.0% of ACTUAL total generation),
  8 TWh)` (`calibration_verdict._fuelmix_vol_band`).

  **No new constant.** The floor is `FUELMIX_SHARE_PP` (3.0) applied to the
  actual-side generation total — the same ±3.0-pp-of-mix materiality the share
  leg already declares. The amendment reconciles C1's two legs rather than
  introducing a tolerance: before it, on a deep net-importing ISO the
  2%-of-load volume term could bind **tighter** than the rubric's own declared
  mix-materiality on the very same class — CAISO 2023: 2% of 207.4 TWh load =
  ±4.15 TWh, vs 3% of 175.7 TWh actual generation = ±5.27 TWh — failing a
  class whose miss the share standard calls fine (`CC_REGULAR` −4.24 TWh =
  −2.4% of actual generation, share −1.8 pp).

  **Why the floor is measured on actual generation and not on `share_pp`.** The
  model-vs-actual share difference can be *flattered* by a system-total shrink:
  when over-import displaces a class, both the class volume and the total
  generation fall together, so `share_pp` under-reads the miss (the same CAISO
  CC row reads −1.8 pp on share but −2.4 pp of actual generation). The floor
  gates on raw `|model − actual|` over the **actual** total — un-flatterable by
  construction — so it is strictly *harder* than the share leg it mirrors.

  **What is unchanged.** The 8 TWh cap still tops the band after the floor, so
  large-ISO bands are bit-identical (PJM/MISO-scale: the cap binds either way).
  The ±3.0 pp share leg still binds independently (MISO `CC_REGULAR` +47 TWh /
  +7.7 pp still fails both legs by a wide margin). The 2%-of-load term still
  governs wherever it is the wider term — the floor binds only where actual
  generation > (2/3) × load. The C2 preliminary-family fallback inherits the
  same band through the shared helper, and the dashboard mirrors it via
  `rubric-consts.js` (`fuelmixVolGenFloorFrac`) rather than a JS-side copy.

  **Effect at amendment, measured over all 26 registered runs against a
  pre-change snapshot rather than asserted:** exactly **one row** flips —
  CAISO keeper `2026-08-17-caiso-200-h1-memberpanel` C1 2023 `CC_REGULAR`
  `FAIL → PASS` (|−4.244| ≤ 5.272 with share −1.8 pp in band), taking the
  run's C1 criterion `FAIL → PASS`. Its determination stays `NOT-YET` on the
  standing C3a mean-LMP miss (+12.8% / +15.7% in 2024/2025). No other record
  of any run of any ISO changes status, and no determination label changes
  anywhere. Scorer-only: no re-solve, every keeper re-scores in place from its
  committed artifacts.

- **v3.3 (2026-08-17, owner amendment — session nyiso-calibration-declaration;
  directive verbatim: "NYISO should be declared calibrated. C3c is an acceptable
  miss and shouldn't change a declaration from calibrated to calibrated with
  caveats because it's a known model limitation that's been ledgered")** — a
  **ledgered caveat no longer downgrades the overall determination.**

  Since v3.1 the ledgerable set is `{C3c}`, so the amendment says exactly one
  thing and cannot say more: an accepted, ledgered scarcity-tail limitation is
  reported, but it is not what turns `CALIBRATED` into
  `CALIBRATED-WITH-CAVEATS`. It **withdraws** the v3.0–v3.2 clause *"never
  `CALIBRATED`"*, which is left verbatim in those entries as genealogy; every
  other guard those entries list survives intact. CLAUDE.md rule 22's C3c
  standing-rule guard (d) is amended in step.

  **Why this is a reporting change and not a band change.** The C3c band, tier
  and measured magnitude are untouched, and the criterion still reads `CAVEAT`
  and **never `PASS`** — so `grade_summary.target_grade` does not absorb it, the
  magnitude is still printed in full, the criterion is still listed in
  `caveats.ledgered` and counted in `grade_summary.ledgered`, and the caveat is
  still named on the determination basis of a `CALIBRATED` run. What changed is
  what the caveat *costs*, on the owner's determination that a known, ledgered
  model-class limitation is not a caveat on the calibration itself.

  **What still binds, unchanged.** The ledger entry (or the standing rule's
  auto-entry, with its exhaustion citation) is still required. The budgets are
  untouched and are checked **before** this branch, so >1 ledgered or >0
  protective caveats is still `NOT-YET` — the 1-slot ledgered budget is now the
  *sole* numeric bound on what may be carried without a downgrade. Every other
  caveat route still downgrades: commercial-band target misses, protective-gate
  caveats, `SKIPPED` criteria and data-blocked years. And the `FAIL` path is
  untouched — a C3c miss that is not ledgerable, because a second criterion also
  fails or governance does not pass, still stands as a `FAIL` and still carries
  the run to `NOT-YET`. So a run reads `CALIBRATED` only when a ledgered C3c is
  its **single** blemish.

  **Effect at amendment, measured over all 26 registered runs against a
  pre-change snapshot rather than asserted:** six determinations change, all
  `CALIBRATED-WITH-CAVEATS → CALIBRATED`, and all six are the same shape (lone
  ledgered C3c; zero band caveats, zero protective caveats, nothing `SKIPPED`,
  nothing data-blocked). **Two are keepers** — NYISO
  `2026-08-16-nyiso-140-layup-exclusion`, the ISO this amendment was requested
  for, and NEISO `2026-08-17-neiso-99-joint-p1`. The NEISO flip is an
  **unavoidable cross-ISO consequence, carried openly**: the scorer is one
  instrument, and an ISO-scoped verdict rule would be an off-registry tuning
  channel in spirit (rules 24 `[R-REGISTRY]` / 25 `[R-ISO-SCOPE]`), so there is
  no honest way to move NYISO's determination without moving every run of the
  same shape. The other four are non-keepers: NYISO
  `2026-08-08-nyiso-133-cod-arm` and `2026-08-17-nyiso-142-stackdup`, NEISO
  `2026-08-17-neiso-97-dstrepair` and `2026-08-06-neiso-2022-corrected-basis`.
  No `NOT-YET` is reclassified in either direction, and CAISO / ERCOT / MISO /
  PJM are unchanged (each keeper either fails a criterion outright or carries no
  ledgered C3c). Scorer-only: no re-solve, every keeper re-scores in place from
  its committed artifacts.

- **v3.2 (2026-08-09, owner amendment — session neiso-keeper-87-control;
  directive verbatim: "make sure c3c is an acceptable caveat for any holdout or
  training year")** — two changes, one widening the C3c standing rule's *scope*
  and one *correcting* a defect that had been suppressing the rule as declared.

  **(a) The C3c standing rule now fires in EVERY year.** Declared at v3.1-time
  (2026-08-06) for out-of-training years only, `_apply_c3c_standing_rule`
  reclassifies a **lone** C3c `FAIL` — governance passing — to a ledgered
  `CAVEAT` (`ACCEPTED MODEL-CLASS LIMITATION`), so the run reads
  `CALIBRATED-WITH-CAVEATS` rather than `NOT-YET`. That now applies to 2023–2025
  exactly as it already did to 2020–2022 / 2019 / H1-2026.

  **This is not a loosening of the band, and the guard that matters is
  untouched.** The removed scope split was never a statement about C3c's
  severity — band, tier and reported magnitude are identical in every year. It
  was procedural: in-sample, the same reclassification was already reachable
  through an explicit exceptions-ledger entry, and that is the route **every**
  current keeper carrying a C3c caveat actually used, so the split governed who
  typed the justification rather than what a run could claim. Since v3.1 C3c is
  the only ledgerable criterion at all, the two routes had already collapsed
  onto one criterion; v3.2 collapses them onto one rule. What still stops it
  being an escape hatch: **lone failure only** (any second failing criterion and
  the rule is silent and every failure stands, C3c's included — so it can only
  ever fire on an otherwise-clean model), **governance must PASS**, **supporting
  tier only** (the v3.0 fail-closed guard refuses `model-class` on load-bearing
  and protective criteria), **never `CALIBRATED`** *(superseded by v3.3 — the
  ledgered caveat no longer downgrades; every other guard in this list stands)*,
  and the caveat still spends
  the single ledgerable slot.

  **(b) "Lone" is now measured over the determination's own criteria.** The test
  read EVERY scored record, including the **reported-only** streams the rubric
  has demoted out of the determination — C5a `co2`, removed at v2.9 because
  eGRID's latest released vintage is 2024. A `co2` `FAIL` therefore silenced the
  rule even though co2 contributes no status, no caveat budget and no reason
  line. It is now filtered to `CRITERIA` membership. **This under-fired
  out-of-training years too**, so (b) is a correction, not part of (a).

  **Effect at amendment — measured over all 66 registered runs against a
  pre-change snapshot, not asserted.** 2 determinations change, both NYISO
  **non-keeper** probes from the `nyiso_li_tsl_n11_security` pair
  (`2026-08-06-nyiso-130-control` and `-n11-tsl`: `NOT-YET →
  CALIBRATED-WITH-CAVEATS`, C3c `FAIL → CAVEAT`, nothing else moves), and both
  are unlocked by **(b)**, not by (a). **Every keeper of all six ISOs is
  unchanged** — each either has no C3c failure, already carries an explicit
  ledger entry for it, or fails a second criterion. `2026-08-06-pjm-158-novirtual-disarmed`
  is a lone C3c failure and still does **not** reclassify: its C6 is
  `UNATTESTED`, i.e. the governance guard working. **Scorer-only: no re-solve,
  no bundle regeneration, keepers re-score in place.**

- **v3.1 (2026-08-06, owner amendment — session-logged; directive: "Any ISOs
  backcast calibrated with caveats on LMP exceeding 10% from actual should be
  reverted to not yet, frontier and complete labels stripped. 3c3 is only
  acceptable ledgered caveat, and … we should drop [C7] from the calibration
  report and declaration altogether if no other commercial grade model is
  gating or publishing on that.")** — two changes, both narrowing what a
  determination may excuse.

  **(a) Ledgering narrowed to C3c alone** (`LEDGERABLE_CRITERIA`, enforced
  fail-closed in `_apply_ledger`). C3c is the one criterion with no published
  commercial comparable, so a documented bound is its honest reporting form;
  every other criterion is scored against a published comparable (§8) and its
  band **is** the certification claim. Both caveat budgets collapse as an
  arithmetic consequence: protective **1 → 0** (no protective criterion is
  ledgerable, so a C8 `FAIL` is `NOT-YET` full stop — the anti-self-deception
  tier gets *stricter*), non-protective **3 → 1** (one ledgerable criterion,
  and caveats aggregate per criterion). Ledger entries for other criteria stay
  on their committed attestations as the historical record and simply go
  inert. **Scorer-only: no re-solve, no bundle regeneration, keepers re-score
  in place.**

  **Effects at amendment (all six keepers re-scored from committed
  artifacts):** **CAISO `2026-08-06-caiso-175-tac-intake`
  CALIBRATED-WITH-CAVEATS → NOT-YET** — C3a mean LMP 2024 +11.7 % (model
  \$38.63 vs actual \$34.60) and 2025 +14.8 % (\$39.46 vs \$34.39) were
  ledgered and now `FAIL`; 2023 (+4.2 %) still passes; C3c remains its single
  ledgered caveat and no other criterion moves. **MISO
  `2026-08-05-miso-132b-cc-committed`** keeps `NOT-YET`, with C3a 2025
  −14.0 % moving `CAVEAT → FAIL`. NEISO (C3a `PASS`; C3c its only caveat), PJM
  (zero caveats), NYISO and ERCOT are unchanged. Dormant non-C3c entries on
  NEISO's and MISO's attestations (C1 `fuelmix`, C2 `sysvol`, C5b/C5c
  `storage*`, `governance`) were reclassifying nothing and remain inert.

  **Governance consequence:** a `complete` marker cannot rest on a `NOT-YET`
  keeper, so **CAISO's `complete` marker and its frontier claim were withdrawn
  the same day** (`frontend/data/backcast/calibration-complete.json`,
  `withdrawn`.CAISO). Nothing was spent under it — the holdout freeze covered
  its whole life — and CAISO's never-authorized locked test (2019, H1-2026)
  stays available. Its frontier *evidence* is not retracted (the walled hourly
  PS water state, the sign-refused export family, the closed offer rungs, the
  inert reserve co-optimization all stand as adjudicated and stay DO-NOT-REDO);
  what is withdrawn is the claim that an empty lever queue on C3a is terminal.
  On a non-ledgerable criterion an empty queue is an **open root-cause item**,
  not a documentable bound.

  **(b) C7 diurnal shape RETIRED** — dropped from the calibration report and
  the determination altogether, on the owner's stated condition that no other
  commercial-grade model gates or publishes on it. **That condition is met on
  this rubric's own prior evidence**: §8's comparables row scores the
  protective gates *"beyond commercial practice"* and says in terms that C7/C8
  gate *"the diurnal shape and forced-energy share no external model
  reports"* — so C7's thresholds were self-set numbers gating a determination
  against nothing external, while every graded criterion here is two-band
  scored against a published comparable. A **full removal**, harder than the
  C5a/C5b/C5c retirements that left those criteria `REPORTED_ONLY`:
  `score_shape` and `C7_GATED_CLASSES` are deleted per CLAUDE.md rule 26
  `[R-DELETE]` so the gate cannot be silently re-armed.

  **What survives:** the **D-1 measurement is untouched** —
  `legitimacy_diagnostics.py` still writes the diurnal rows to every bundle,
  and **C8 still gates on them** via `_d1_shape`, because CLAUDE.md rule 20
  `[R-FORCED-BUDGET]` makes an over-budget class's conditional pass depend on
  its D-1 profile. The caiso-42 flat-floor signature was caught twice (C7's
  fixed class tuple, C8's escalation); it is still caught by the second, which
  is the better-aimed test since it reads the D-1 row for whichever class is
  *actually* being forced. Pinned by
  `DeterminationTests.test_flat_floor_forces_not_yet`.

  **Effects at amendment:** C7 was `PASS` on CAISO/NYISO/PJM/ERCOT, `SKIPPED`
  on NEISO, `FAIL` on MISO (COAL_PRB 2025). Only MISO's reported basis changes,
  and its `NOT-YET` is unaffected — C3a fails it independently under (a). The
  v2.8 gate-set widening and its 2026-07-27 ratification note below are now
  historical: they describe a criterion that no longer exists.

- **v3.0 (2026-08-05, owner amendment — session-logged, ERCOT-2023-diagnosis
  session; directive: "make C3c an accepted caveat because of known
  limitations of LP modeling underestimating the scarcity tail — across all
  3 years")** — adds the second ledgered caveat kind, **`ACCEPTED MODEL-CLASS
  LIMITATION`** (`"kind": "model-class"` exceptions entries): reclassifies a
  FAIL to a budgeted ledgered CAVEAT exactly like the measured-input kind
  (same ≤3 non-protective pool), admissible **only for supporting-tier
  criteria** — the scorer ignores a model-class entry matched against a
  load-bearing or protective criterion (fail-closed), so the certifying and
  anti-self-deception tiers cannot be waved through this door. Required
  entry content: owner decision (date + session), exhaustion record, open
  residual lane (§3). Numbering note: "3.0" is forced by the one-decimal
  version float (2.9 + 0.1); the v2 criterion set, bands and tiers are
  untouched. **First application and effects at amendment:** the ERCOT
  keeper (`2026-08-04-ercot165-unpooled-share`) gains three `price_tail`
  model-class entries (2023 58 vs 181 h; 2024 20 vs 53 h; 2025 0 vs 31 h) —
  its exhaustion record is ercot-95/97/102/107/108/155/159/161/162/163 (the
  realized RT tail formed on equilibrium scarcity-hour ENERGY offers,
  predominantly storage at $500–3,000, with measured RTORPA ≈ $1–5 and PRC
  ≈ 5.8 GW at the missed hours; the offer-side arm collapsed discharge when
  tried, every reserve/quantity-side family fabricated scarcity elsewhere),
  and its named open residual lanes are the storage AS-vs-energy capability
  split and the CC headroom identification. C3c flips FAIL → CAVEAT
  [ledgered] in all three years; the ERCOT determination stays NOT-YET with
  its basis narrowed to the 2023-only C3a/C3b FAILs + the C7 2023-lignite
  cv-leg. No other ISO carries a model-class entry, so every other keeper's
  verdict is byte-stable.
- **v2.8 (2026-07-27, coal gate-blindness correction — ERCOT-121 owner
  charter: "the fix … is a scorer/gate correction that RE-SCORES every
  existing keeper in place (no re-solve), and it may flip verdicts";
  RATIFIED as an owner amendment 2026-07-27, miso-96)** — two
  distinct blind spots that together hid the entire coal fleet from the
  C7/C8 protective gates, both corrected scorer-side so committed artifacts
  re-score without regeneration.
  **(a) C8 materiality vocabulary bug:** the D-2 per-class summary labels
  classes by CAMPD `plant_group` — coal plants are `"COAL"` — while the run
  payload's `gmModel` and bench `classFull` carry the scored-class rank
  split (`COAL_LIGNITE`/`COAL_PRB`/…). `_class_load_share("COAL")` read
  0.0 TWh on both sides and SKIPPED-immaterial ("COAL immaterial (0.0% of
  ISO load)") the coal fleet of every coal ISO — ERCOT 13–14 %, MISO
  33–36 %, PJM 14–16 % of load — while the artifact's own `load_share`
  field said material. Fixed with the `PLANT_GROUP_MEMBERS` aggregate
  bridge (sums the member classes on both sides).
  **(b) C7 gate-set scope:** `score_shape` scored only artifact-baked
  `gated` rows, and `D1_GATED_CLASSES` was peaker/intermediate only — so a
  merchant-coal class pinned flat (the exact caiso-42 signature C7 exists
  to catch) was reported by D-1 and never scored. C7 now derives gatedness
  rubric-side (`C7_GATED_CLASSES` = `CT_PEAKER`, `ST_GAS` + merchant coal)
  and evaluates stored metrics against the artifact's gates block (verified
  zero drift against every baked verdict on previously-gated rows across
  all six keepers). `CC_REGULAR` stays ungated pending an owner call (it
  passes D-1 in all six keepers today; widening beyond the evidenced
  blindness is an owner amendment).
  **Effects at amendment (all six keepers re-scored):** ERCOT-115 C7
  PASS → FAIL on COAL_LIGNITE 2023 (profile r 0.745, off-peak CV ratio
  0.294 — the lignite fleet held flat at its availability ceiling; machine
  confirmation of the ERCOT-121 owner observation) — determination stays
  NOT-YET (C3a/b/c already failing); **MISO-88 flips
  CALIBRATED-WITH-CAVEATS → NOT-YET** (C7 FAIL COAL_PRB in all three
  years, cv_ratio 0.364–0.453 on a 33–36 %-of-load class) — an honest new
  open item exactly like the v2.7 NYISO flip, not a regression; PJM-121
  stays CALIBRATED (COAL_BIT passes D-1 r 0.835–0.884 / cv_ratio 0.85–1.16;
  COAL_PRB/COAL_WC immaterial); CAISO/NYISO (no coal rows) and NEISO
  (COAL_BIT 0.2–0.3 TWh immaterial) unchanged. No C8 flips: every coal
  fleet's non-exempt forced share is 0.0–0.4 % — the newly-gated rows all
  PASS; the correction closes the blindness rather than reversing any
  existing C8 outcome.
- **v2.7 (2026-07-16, owner amendments — session-logged, second of the day,
  calibration-rubric-updates session)** — two changes, both scorer/doc level
  (no re-solve, no payload or bench change; every keeper re-scores in place).
  **(a) C3c gates on the ACTUAL RT scarcity tail for EVERY ISO.** Owner
  directive: the tail criterion is judged on actual RT scarcity hours, not
  DA. v2.6(a) had moved only ERCOT to the RT hourly basis; v2.7 extends it
  to all six ISOs — the RT hourly hub tail is the scarcity the market
  actually realized, and the DA count (scarcity *expectations*, carrying the
  day-ahead forecast-risk premium a realized-weather backcast cannot price)
  becomes the report-only diagnostic row everywhere. The per-ISO
  `TAIL_BASIS` switch is deleted — the basis is uniform again (§5 parity
  restored, now on RT). The v2 sub-hourly-transient argument for DA gating
  (miso-scarcity-tail-diagnosis.md §1) is consciously superseded: both
  counts are hourly hub averages, and transients that push an hourly RT
  average over the threshold are part of realized scarcity. Both actuals
  were already committed for every ISO-year (`tail/actual_tail.json`), so
  the flip is scorer-only. Re-score impact at amendment: ERCOT unchanged
  (already RT); PJM-114 stays CALIBRATED (2023 small-count, 2024 0.50×,
  2025 0.68×); NEISO-59 keeps its ledgered-caveat determination; CAISO/MISO
  stay NOT-YET (their tails were failing on either basis); **NYISO-62 flips
  CALIBRATED-WITH-CAVEATS → NOT-YET** (2024: model 3 h vs RT 12 h, 0.25× —
  the old DA actual was 0 h and passed on the small-count rule) — an honest
  new open item, not a regression.
  **(b) C5b + C5c REMOVED from the rubric.** Owner directive (same message):
  storage-dispatch data is not reliable enough to be a calibration gate.
  v2.6(c) had retired both to report-only hours earlier; the follow-up
  removes them outright — no criterion ids in the verdict, no report rows,
  scorer functions and tolerances (`STORAGE_TOL`,
  `STORAGE_SHAPE_R_FLOOR/MIN_CV`) deleted, and the `TIER_RETIRED` tier
  (which existed only for them) deleted with them. The storage
  payload/bench diagnostics stay committed and rendered on the run pages,
  and the bench builder keeps the v2.6(b) observed-months rule. Dormant
  C5b/C5c ledger entries in old attestations remain as inert history. The
  pre-removal definitions are preserved in the v2.6 entry below;
  re-introduction is a future owner amendment.
- **v2.6 (2026-07-16, owner amendments — session-logged, ERCOT-73 session)** —
  three changes, all scorer/bench level (no re-solve, no payload change).
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
  **(c) C5b + C5c RETIRED to report-only, every ISO.** Owner decision (same
  session, following from (b)): EIA-930 storage-dispatch data is not yet
  reliable enough to be a **calibration judgment** for any ISO. At retirement
  the two criteria had never functioned as real gates — C5c: one FAIL
  (ERCOT 2024, the fabricated-zeros artifact of (b)), one ledgered caveat
  (MISO), four SKIPPED; C5b: ledgered caveats in MISO/NEISO, SKIPPED
  everywhere else. Both stay computed and PRINTED on every keeper
  (`TIER_RETIRED`, tag `RETD` — the numbers remain visible and auditable)
  but are never PASS/FAIL, never consume ledger budget, and never cap the
  determination (they are exempt from the unscored-criterion cap: a retired
  criterion is not an unscored judgment, it is not a judgment). MISO/NEISO's
  existing C5b/C5c ledger entries go dormant in place (attestation history,
  matched by no FAIL). Re-arming when reliable storage data lands is a
  future owner decision; the pre-retirement definitions stay in §C5.
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
  re-based in place (`scripts/archive/retrofit_co2_payloads.py`; bench parts carry
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
