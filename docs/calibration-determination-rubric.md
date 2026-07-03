# Calibration Determination Rubric

Status: **canonical, machine-enforced.** This document is the single auditable
definition of when an ISO backcast may be declared *calibrated*. It replaces the
ad-hoc, per-run sidecar judgement (“this looks good enough”) with a fixed rubric
that a scorer reproduces byte-for-byte: `scripts/calibration_verdict.py` reads a
keeper’s committed artifacts and emits a `PASS` / `CAVEAT` / `FAIL` per criterion
and one overall determination — `CALIBRATED`, `CALIBRATED-WITH-CAVEATS`, or
`NOT-YET`. Re-running it on the same keeper always yields the same verdict.

This rubric **codifies the governance rule in `claude.md`** (measured/defensible
over what-fits, rules #1, #11, #12): a run is a keeper because it is the most
structurally faithful, *not* because it has the lowest error, and a determination
of “calibrated” is a claim that the model’s *mechanisms* reproduce the market —
not that its residuals were tuned to zero. The rubric is therefore built to
**fail a current keeper**: any out-of-tolerance criterion that is not explicitly
documented as an accepted measured-input limitation forces `NOT-YET`. If it could
not return `NOT-YET` for a real keeper, it would be theatre.

Downstream consumer: `docs/forecast-validation-plan.md` Phase 3 (statistical-mode
dispatch backcast) uses this determination as the gate that backcast tuning has
“reached an acceptable state” before the forecast-validation program starts. A
`NOT-YET` ISO is not yet eligible to seed the forecast-error prior.

---

## 0. What the scorer reads (reproducibility contract)

The determination is reproducible **from committed artifacts only**. The scorer
never re-solves the LP and never reads the (gitignored) `dispatch/*.parquet` or
`system.parquet`. For a run it reads:

| Artifact | Committed at | Supplies |
|---|---|---|
| `frontend/data/backcast/registry/<id>.json` | sidecar | id, ISO, declared years, label, definition, bundle path |
| `frontend/data/backcast/runs/<id>.js` | run payload (gzip+base64) | model side: `gmModel` (grid-LP TWh by class), `fuelRows` (per-fuel model TWh + hourly r + NRMSE), `lmp` (model load-weighted price + monthly), `ordc` (ERCOT tail hours) |
| `frontend/data/backcast/bench/<ISO>/<year>.json.gz` | benchmark part | authoritative actuals: `classFull` (grid-delivered EIA-923−BTM TWh by class, vintage-reconciled), `e930` (EIA-930 grid totals by fuel), `avgLMP` (actual DA/RT mean + monthly) |
| `results/calibration/<name>/run_config.json`, `meta.json` | bundle | governance config (outage source, lever flags), gas vintage |
| `results/calibration/<name>/calibration_attestation.json` | bundle (this rubric) | governance attestation + the exceptions ledger |

The model payload and benchmark parts are the **same numbers the dashboard
renders** (`scripts/render_calibration_html.py:build_payload`), so the verdict
and the dashboard can never disagree. The model side is the **grid-delivered
basis** (grid LP dispatch, no behind-the-meter CHP add-back); the actual side is
EIA-923 minus the per-class BTM host supply — model-grid vs actual-grid, per
`scripts/lib/session_score.py` and the 2026-06-14 directive.

---

## 1. Criteria

Each criterion below names: **the metric**, **the authoritative actual source**,
**the per-year tolerance**, and **the failure classification** — `MODEL MISS`
(the model’s mechanism is wrong; do not paper over it) vs `ACCEPTED
MEASURED-INPUT LIMITATION` (the *actual* is itself partial/zeroed for a
documented, forward-valid reason, and the miss is not a model defect). A miss is
`MODEL MISS` **by default**; it is reclassified to `ACCEPTED MEASURED-INPUT
LIMITATION` only by a matching entry in the exceptions ledger (§3).

Criteria are **HARD** (a `FAIL` forces `NOT-YET`; not caveatable beyond the tight
hard-gate budget) or **SOFT** (a documented out-of-tolerance becomes a `CAVEAT`).

### C1 — Fuel-mix by class, grid-delivered  *(HARD)*

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

### C2 — System volume error, gas & coal families  *(HARD)*

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
    EIA-930 carries no per-class split), so the **±2.5% family fallback** against
    the authoritative EIA-930 grid total is retained — the only volume check the
    data supports, with the EIA-930
    incomplete-vintage handling made explicit. The current-year EIA-923 release is a preliminary
    monthly survey that under-counts thermal generation the CAMPD backfill cannot
    fully repair. The benchmark applies `_VINTAGE_RECONCILE_FRAC = 0.97`
    (`render_calibration_html.py`): when the grid-delivered 923 family total falls
    **below 0.97 ×** the complete EIA-930 grid series the model is calibrated to,
    the family’s classes are scaled up to the EIA-930 total (inter-class split and
    monthly shape preserved); a complete vintage (≥ 0.97×) is left untouched
    (byte-identical). For the preliminary year the scorer therefore takes the
    **authoritative actual = EIA-930 grid total** (`e930[gas|coal]`) and records
    the reconcile that fired, so the model is compared against a *complete*
    benchmark, not a partial survey.
- **Failure classification:** `MODEL MISS` by default (the fleet is delivering the
  wrong amount of gas or coal to the grid — fuel-price passthrough, must-run, or
  interchange wedge wrong). `ACCEPTED MEASURED-INPUT LIMITATION` only for the
  **preliminary-923 vintage** when the residual sits inside the vintage’s
  reconciliation uncertainty (the 923-vs-930 gap the reconcile repaired) —
  ledgered for that year.

### C3 — Price (three independently-bounded sub-criteria)  *(all SOFT)*

A good mean price must not be allowed to mask a collapsed or over-fired tail, so
mean / shape / tail are **scored separately** and each can independently caveat or
fail.

**2026-07-02 re-balance (tightened, paired with the looser C1).** The rubric
previously over-weighted per-class generation-mix precision and under-weighted
price accuracy — the opposite of what the determination is *for*: an LP whose
duals reproduce the market’s price level, seasonal shape and scarcity tail is
demonstrating the market structure is right, while a ±2 TWh small-class residual
is usually reporting/assignment noise. So C1 loosened (above) and C3 tightened
to the numbers below. This is a re-weighting of the *grading*, not a change to
any mechanism, and the C6 governance gate is untouched: the tighter price bands
must be met by real structure (reserve co-optimization, scarcity pricing,
congestion), **never** by an adder or haircut tuned to the price residual —
a run that closes the price gap that way FAILs C6 regardless.

- **C3a — Mean LMP.**
  - *Metric:* system load-weighted mean LMP, $/MWh (model `lmp[zone].p` weighted
    across zones by `lmp[zone].d` annual demand).
  - *Actual:* `avgLMP.rt` (real-time), falling back to `avgLMP.da` when RT is
    absent — the derived `actual_lmp.json` hub mean.
  - *Tolerance:* **±5%** (tightened from ±8% on 2026-07-02) — the tight end of
    the playbook’s ~5–10% band. The **energy-only LP dual structurally
    under-shoots** the actual LMP (which carries reserve, scarcity and uplift
    adders); that known gap is what the structural reserve/scarcity mechanisms
    are for, and a wide tolerance was quietly absorbing it instead of surfacing
    it. A persistent under-shoot beyond 5% is a signal to build the missing
    mechanism — not to widen the band, and never to fit an adder (C6).
  - *Classification:* `MODEL MISS` (offer-curve level / scarcity mechanism).
- **C3b — Duration / shape (quantitative, not eyeballed).**
  - *Metric:* normalised RMSE between the model and actual **monthly
    load-weighted price vectors** (12 months; model `pMon` re-weighted across
    zones by `dMon`, actual `rt_mon`/`da_mon`). NRMSE = RMSE / mean(actual). This
    is the committed-artifact shape metric; where a run additionally commits the
    full hourly price-duration curve, the P50/P90 ratio check of
    `calibration.check_price_duration_curve` is scored in its place.
  - *Tolerance:* **NRMSE ≤ 0.15** (tightened from 0.20 on 2026-07-02).
  - *Classification:* `MODEL MISS` (seasonal merit-order / fuel-shape error).
- **C3c — Tail / scarcity.**
  - *Metric:* count of hours with price **> $200/MWh** (model vs actual), the
    scarcity-tail proxy. **Per-ISO tail definition** (§5): the threshold is
    $200/MWh by default; an ISO whose scarcity is set by a different proxy
    overrides it (ERCOT: ORDC reserve-price adder hours, read from the `ordc`
    block; winter-peaking NYISO/NEISO may use a higher city-gate threshold).
  - *Actual:* the ISO’s actual tail-hour count (ERCOT `ordc.hoursGt200.actual`;
    otherwise the hourly actual-LMP series when committed).
  - *Tolerance:* model tail hours within **[0.7×, 1.5×]** of actual (tightened
    from [0.5×, 2.0×] on 2026-07-02) — a **collapsed tail (0 hours where the
    market had scarcity) FAILs**, and an **over-fired tail (> 1.5× actual)
    FAILs**. Bounded both ways on purpose.
  - *Classification:* `MODEL MISS` (missing scarcity pricing / over-aggressive
    peaker offers). `SKIPPED` when the hourly price/scarcity series is not in the
    committed payload (most non-ERCOT runs today) — recorded as not-scored, never
    a silent pass.

### C4 — Dispatch correlation, fleet hourly  *(SOFT)*

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
  A fleet whose annual energy is **< 5 TWh** is `SKIPPED` (an hourly correlation
  on a near-zero series is degenerate — NEISO coal r ≈ 0 — and the C1 per-class
  band is the meaningful check). (Nuclear/wind/solar are report-only here — VRE hourly r is set by the input
  profile, not a dispatch decision, and nuclear is near-flat.)
- **Failure classification:** `MODEL MISS` (commitment / ramp / outage-overlay
  timing). A low r driven by a documented measured-input gap (e.g. an outage
  series known incomplete for one state-year) may be ledgered.

### C5 — CO2 and storage throughput  *(both SOFT)*

- **C5a — CO2 vs eGRID.**
  - *Metric:* annual system CO2, model vs eGRID ISO total.
  - *Actual:* eGRID ISO-year total (the bundle’s emissions summary / eGRID
    reference).
  - *Tolerance:* **±7%** (mid of the playbook’s 5–10%).
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
    series. Same coverage gate as C5b.
  - *Tolerance:* **r ≥ 0.50.** The floor is looser than fleet dispatch (C4,
    r ≥ 0.70) because monthly storage net-discharge is a 12-point vector with
    lower degrees of freedom and substantial noise from AS commitment.
  - *Classification:* `MODEL MISS` (storage dispatch timing — wrong charge/
    discharge season). `SKIPPED` when no EIA-930 storage breakout or the model
    bundle lacks `monthly_net_gwh`.

### C6 — Governance gate  *(HARD, pass/fail only — never graded, never caveatable)*

This is the `claude.md` rule made executable. **A run that fits to residuals
FAILS regardless of every score above.** Four assertions, all required:

1. **Every active lever traces to a measured input** (a physical/market quantity
   that would regenerate for a forward year and respond to changed conditions —
   the rule #12 admissibility test). No lever exists only to move a residual.
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

**Caveat budget (quorum):**
- HARD data criteria (C1 fuel-mix, C2 system volume): at most **1** may be a
  `CAVEAT`, and only with a ledger entry. C6 governance is never caveatable.
- SOFT criteria (C3a/b/c, C4, C5a/b/c): at most **2** `CAVEAT`s total (cut from
  3 on 2026-07-02 — Option A of the re-balance: C3 stays SOFT, but with three
  price sub-criteria a 3-caveat budget allowed *all* of price — mean, shape and
  tail — to be caveated away at once; 2 means price can no longer be caveated
  wholesale. The stronger alternative, promoting C3a to HARD, was considered and
  deliberately not taken: a HARD mean-LMP gate would make the known energy-only
  dual under-shoot un-caveatable even where it is a documented structural gap
  under active mechanism work).

**Determination:**

| Outcome | Conditions (all must hold) |
|---|---|
| **CALIBRATED** | C6 governance `PASS`; **every** criterion `PASS` (no `FAIL`, no `CAVEAT`, no `SKIPPED`); **no** data-blocked target year. |
| **CALIBRATED-WITH-CAVEATS** | C6 governance `PASS`; **no** `FAIL` on any criterion; caveats within budget (≤1 hard, ≤2 soft) and **every** caveat has a ledger entry; one or more of {a caveat exists, a soft criterion is `SKIPPED`, a target year is data-blocked}. |
| **NOT-YET** | anything else — governance not `PASS`/`UNATTESTED`; **or any criterion `FAIL`** (an out-of-tolerance criterion with no ledger entry is a `FAIL` *by construction*); or the caveat budget is exceeded. |

The decisive rule, restated: **a determination with an undocumented
out-of-tolerance criterion is `NOT-YET`.** The only way an out-of-tolerance
criterion is compatible with a passing determination is an explicit, ledgered
`ACCEPTED MEASURED-INPUT LIMITATION` (and only within the caveat budget).

Because the tail (C3c), CO2 (C5a) and storage (C5b) actuals are not in the
committed payload for most runs today, those criteria are `SKIPPED`, which **caps
the best attainable determination at `CALIBRATED-WITH-CAVEATS`** until a run
surfaces them. This is intended: you may not claim a *fully* calibrated ISO while
its CO2 and scarcity tail are unscored.

---

## 3. The exceptions ledger (required, auditable)

Every `CAVEAT` must be earned by an explicit ledger entry. The ledger lives in the
bundle at `results/calibration/<name>/calibration_attestation.json` (per-run,
conflict-free, committed with the bundle). An out-of-tolerance criterion with **no
matching ledger entry is a `FAIL`** — silence is never a pass.

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

The C3c tail proxy and threshold are per-ISO (the scorer’s `TAIL` table):

| ISO | Tail proxy | Threshold |
|---|---|---|
| ERCOT | ORDC reserve-price adder hours (`ordc` block: hours > $200, and > $500 as the deep-scarcity companion) | $200 / $500 |
| PJM, MISO, SPP | hours with hub LMP > $200/MWh | $200 |
| NYISO, NEISO | hours with zonal LMP > $300/MWh (winter city-gate scarcity sets the tail higher) | $300 |
| CAISO | hours with hub LMP > $200/MWh (net-load ramp scarcity) | $200 |

`SKIPPED` for any ISO-year whose hourly price/scarcity series is not in the
committed payload, recorded with that reason.

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
