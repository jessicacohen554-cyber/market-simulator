# Forecast Determination Rubric (v1.0)

Status: **canonical for the Forecast Finalization Program. RUBRIC VERSION 1.0**
(2026-07-17, FF-0A — authored per `docs/forecast-development-plan-2026-07.md` §3;
changes are owner-signed amendments, mirroring the backcast rubric's version
discipline). This document is the single auditable definition of how a
**forecast bundle** is judged at each tier of the test ladder (plan §2.1) and
what "promoted" means at each gate. The machine scorer is
`scripts/forecast_verdict.py`: it reads a bundle's **committed artifacts only**
(evolution ledgers, full-horizon summaries, invariant output, hindcast/crossover
scores, driver-battery output, benchmark tables) and emits one
`PASS`/`CAVEAT`/`FAIL`/`SKIPPED` line per category FC-1..FC-8 plus one overall
determination per tier — `PROMOTE`, `PROMOTE-WITH-CAVEATS`, or `HOLD`.
Re-running it on the same artifacts always yields the same verdict. **No LP is
ever solved inside the scorer.**

Precedent: `docs/calibration-determination-rubric.md` (the backcast rubric,
C1–C8). This rubric is its forecast-side sibling and inherits its governance
posture wholesale: a bundle is promoted because its **mechanisms** are
structurally faithful and its evidence is complete — never because a number was
tuned to land inside a band (CLAUDE.md rules 1/13/14/21/23). Every band below
is **pre-registered**: derived from design targets, external practice (§1), or
already-committed measured evidence that predates any run this rubric will
score — never from the numbers of a run under judgment. **Bands are never
widened in response to a result** (rule 22 discipline; a FAIL is a root-cause
investigation).

**What a determination certifies.** A tier-N `PROMOTE` certifies that the
bundle's evidence supports entering tier N+1 of the solve ladder
(T0→T1→T2→T3, plan §2.1) — it is a *promotion* claim, not an accuracy claim.
Accuracy claims live only where a measured instrument exists (FC-3 hindcast
bands, FC-4 crossover gap) and are quoted with their instruments' own caveats.
A T3 (golden) `PROMOTE` additionally requires the golden-attestation checklist
(§5) — that is the only determination that certifies a deliverable.

---

## 0. What the scorer reads (reproducibility contract)

The determination is reproducible from committed artifacts only. The scorer
never re-solves the LP and never reads gitignored dispatch parquets. Per tier
it reads (all optional inputs recorded `SKIPPED`, never silently passed):

| Artifact | Produced by | Supplies |
|---|---|---|
| `full_horizon_summary.json` | `scripts/run_full_horizon.py` | meta (ISO, window, `capacity_market_clearing`), invariant results I1–I14, per-year trajectory rows (reserve margin, scarcity-hour counts `hours_ge_*`, CO2, capacity by fuel, builds/retires), per-year wall/RSS |
| `evolution_<year>.json` ledgers | `runner.py` (via the summary's trajectory rows) | retirements/additions with channel attribution (`confirmed`/`announced`/`economic`; `planned`/`economic`/`reserve_backstop`), floor retention, reserve margin |
| invariant JSON | `scripts/check_forecast_invariants.py --json` | standalone I1–I14 results when no summary embeds them; paired P1–P3 results (`--paired`) |
| hindcast `score.json` + sidecar | `scripts/run_capacity_hindcast.py` + `score_capacity_hindcast.py` | FC-3: the §1.4 band verdicts (retirements, additions, CO2), baselines |
| crossover score JSON | `scripts/score_crossover.py` (FF-0E) | FC-4: per-metric forecast-mode vs keeper-backcast errors 2023–2025; the ≥2026 refusal marker |
| driver-battery JSON | `scripts/run_driver_battery.py` | FC-6: ladder/rung/expectation rows with gate/report status |
| corridor table JSON | FF-0D intake → committed benchmark tables (§6) | FC-5: external anchors (AEO2025 / StdScen / ISO planning docs) + per-row divergence dispositions |
| `run_config.json` | the run | FC-7 machine checks (mode, flags, registry completeness) |
| `dof_ledger.json` | the producing session | FC-7: free parameters → identification sources |
| `forecast_attestation.json` | the producing session (T3) | §5 golden attestation |

**Namespace discipline:** every artifact lives in the forecast-validation
namespaces (`results/hindcast/`, `results/full-horizon/`, future
`results/ff-*/`, `frontend/data/hindcast/`, future `frontend/data/forecast/`)
— never the backcast registry (plan §2.3).

---

## 1. Research grounding — how external practice judges capacity-expansion output

Per plan §4 (standing order), surveyed before any threshold was set. What was
adopted, adapted, and rejected:

1. **EPA IPM (v6 / Post-IRA documentation + the 2022 peer-review record).**
   IPM's published validation is *procedural*, not banded: QA by the
   contractor, stakeholder corroboration of inputs/results, and a formal
   five-reviewer peer review of the reference case. No retrospective error
   band on capacity decisions is published at all.
   **Adopted:** the *provenance* posture — inputs individually cited and
   defensible (our FC-7/DOF ledger is the machine-checkable version of this).
   **Rejected:** validation-by-review alone — this program requires measured
   instruments (FC-3/FC-4) because the owner's charter says skill claims must
   be *measured, not asserted* (plan §0.2).
2. **NREL ReEDS — "Historical Comparison of Capacity Build Decisions from the
   ReEDS Model" (NREL/TP-6A20-71916) and the Standard Scenarios practice.**
   The one published CEM backtest of record: initialize from a historical
   year, run forward, compare capacity-by-technology builds/retirements
   against realized EIA data; differences are attributed to input error vs
   structural error, and generation totals are reconciled against EIA-923.
   Standard Scenarios additionally publish their outputs *next to* AEO and
   other public projections as context, without treating any as truth.
   **Adopted:** (a) the vintage-initialized hindcast as the primary
   capacity-skill instrument (our T1-H, already built — FC-3 imports its
   bands); (b) the input-error vs structural-error decomposition (our
   realized-fuel vs as-known variants and the CO2 decomposition table);
   (c) projection-vs-projection context tables (our FC-5 corridor, with the
   sharper divergence-explanation discipline from
   `docs/handoffs/cross-model-corridor-2026-07-13.md` — divergence is not
   failure; *unexplained* divergence is).
   **Rejected:** ReEDS' documented practice of adjusting state-level cost
   coefficients until generation matches history — that is answer-key fitting
   under rule 13 and is exactly what FC-7/the DOF ledger forbid.
3. **Retrospective-evaluation literature** (Wilson et al. 2021, *Evaluating
   long-term model-based scenarios of the energy system*, Energy Strategy
   Reviews; Wen & Trutnevyte 2022, *Accuracy indicators for evaluating
   retrospective performance of energy system models*, Applied Energy —
   the D-EXPANSE 31-country hindcast).
   **Adopted:** (a) hindcast skill is *necessary but not sufficient* — future
   structure may not resemble the past, so no FC-3 pass is ever quoted as a
   forward-accuracy guarantee (echoed in §7's honest-unfit posture);
   (b) scale-robust error indicators (their sMAPE/growth-error findings are
   why FC-3's bands are fraction-of-actual and share-delta based, not raw
   MW); (c) the finding that only a handful of models ever backtest at all —
   which is why the T1-H instrument, not the corridor, is the primary
   capacity-skill evidence.
   **Rejected:** purely statistical scoring without mechanism attribution —
   every FAIL here routes to a named mechanism/lane (the P-1A convention),
   because an error number without a mechanism owner cannot drive the
   program.
4. **EIA AEO Retrospective Review practice.** EIA publishes its own projection
   error distributions (the anchor set already cited in the backcast rubric's
   benchmark memo: 1–3-yr gas-generation error SD 5.7–9.6%, CO2 SD 3.2–4.9%).
   **Adopted:** as the external error-scale context for FC-4/FC-5 magnitudes
   (a forecast-input dispatch error inside the AEO short-horizon envelope is
   commercial-grade). **Rejected:** as pass/fail targets in themselves —
   corridor benchmarks are context, never fit targets (rule 13, plan §7.6).
5. **Monitor/market-design anchors** (Potomac SOM net-revenue tables, ORDC
   design parameters, RTO planning reserve margins/VRR curves — the on-disk
   corpus plus `docs/handoffs/cross-model-corridor-2026-07-13.md` §2).
   **Adopted:** as the design-target source for FC-2's adequacy/equilibrium
   corridors (planning-RM bands, ORDC-plausible scarcity frequency,
   position-vs-curve via T-R4). These are market-design facts, not fitted
   values.

---

## 2. Categories FC-1..FC-8

Each category names: **inputs**, **metric(s)**, **threshold(s)** (each with a
pre-registration rationale line), and **severity semantics**. Category-level
status is the worst of its row statuses (`FAIL` > `CAVEAT` > `PASS`);
`SKIPPED` is tracked separately and never a silent pass. Rows marked
*(report-only)* can annotate but never gate.

### FC-1 — Structural integrity *(hard gate, every tier)*

- **Inputs:** the I1–I14 results embedded in `full_horizon_summary.json`, or a
  standalone `check_forecast_invariants.py --json` output.
- **Metric:** the invariant statuses themselves. **The I-thresholds stay owned
  by `check_forecast_invariants.py`** (its `Thresholds` dataclass); this rubric
  consumes its output and never re-derives or re-litigates an invariant.
- **Threshold:** any invariant `FAIL` ⇒ FC-1 `FAIL` (with the offending ids +
  details). Any `WARN` ⇒ `CAVEAT` (ids listed). All `PASS` ⇒ `PASS`.
  *Rationale: I1–I14 are physical/accounting coherence checks (energy balance,
  capacity accounting closure, no retire-reenter, SOC integrity…) — a
  trajectory that violates them is not evidence about anything downstream, so
  this is the T0→T1 gate verbatim (plan §2.1) and a precondition for every
  other category.*
- Missing invariant output ⇒ `SKIPPED` (⇒ `HOLD`, §4 — a bundle without its
  invariant record is unscored, not passing).

### FC-2 — Adequacy & equilibrium behavior

- **Inputs:** trajectory rows (reserve margin, `hours_ge_*`, builds/retires by
  source), I12/I13 results, `capacity_market_clearing` flag, and — for
  curve-ON ISOs — a committed position-validation artifact
  (`validate_capacity_prices.py` output).
- **Rows:**
  1. **Reserve-margin band (consumes I12).** I12 `FAIL` ⇒ row `FAIL`; I12
     `WARN` ⇒ `CAVEAT`.
     *Rationale: I12's band ([planning floor, floor + 15 pp], FAIL on 3+
     consecutive breach years) is already the design corridor; restating it
     here would risk a looser second copy (forbidden by charter).*
  2. **Terminal drift (T2/T3 only).** Final-window-year reserve margin within
     **[floor − 10 pp, floor + 25 pp]**, floor =
     `PLANNING_RESERVE_MARGIN_BY_ISO`. Beyond ⇒ `FAIL`.
     *Rationale: pre-registered from external planning practice, not from any
     run: RTO planning targets sit at ~13.75–18% RM and CPUC's procurement
     band tops out ~25%; no external outlook plans to > floor+25 pp (the
     corridor memo's D11/D13 fixed-price overshoot signatures reached
     +35–50 pp), and sustained RM < floor−10 pp is chronic shortage no ISO
     tolerates in planning. This catches the two-phase de-firm/over-build
     trajectory (plan §1.2-4) at the tier where equilibrium behavior is the
     question.*
  3. **Cobweb (consumes I13).** Any I13 `WARN` ⇒ row `FAIL` at every scored
     tier. *Rationale: plan §2.1 makes "no I13 cobweb" an explicit T1→T2 gate
     condition and its absence a T2→T3 stability condition; an
     alternating-build entry loop is a mechanism defect (entry sizing), never
     acceptable behavior.*
  4. **Backstop share of additions.** Cumulative `reserve_backstop`-sourced
     thermal additions ÷ total additions (thermal + renewable + storage MW)
     over the window: **≤ 10% `PASS`; 10–30% `CAVEAT`; > 30% `FAIL`.**
     *Rationale: the backstop models administrative reliability procurement
     (MISO-style backstop, CAISO CPM), which in real markets is a
     single-digit-percent residual channel — entry is supposed to be carried
     by the economic screens. A model whose build path is >30% administrative
     is substituting the safety valve for the entry mechanism (BLK-10's
     over-fire signature). Bounds set from the design role of the channel,
     before any FF-0B baseline exists.*
  5. **Curve-ON position trajectory (curve-ON ISOs only).** Import **T-R4 by
     reference** (`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md`
     §3): model position vs published auction position within T-R4's own
     bands; scored from the committed position-validation artifact. Absent
     artifact for a curve-ON ISO ⇒ `SKIPPED` (counts as unscored evidence).
     Curve-OFF ISOs: not applicable (recorded).
     *Rationale: the T-R battery already pre-registered these bands; this
     rubric may not restate them looser (charter), so it imports them.*
  6. **ERCOT scarcity-hour frequency (ERCOT only; T2/T3 gate, T1 report).**
     Quantity: the trajectory's committed `hours_ge_500` count per year
     (the $500/MWh threshold is the lowest committed trajectory threshold
     that unambiguously indicates scarcity-adder pricing rather than tight
     gas). Window mean ∈ **[2, 200] h/yr** ⇒ `PASS`; window mean = 0 ⇒
     `CAVEAT` ("scarcity never forms" — the known BLK-6/G-31 gap, reported
     not hidden); any single year > **800 h** ⇒ `FAIL`.
     *Rationale: ORDC design math, not model output: at equilibrium the ORDC
     is designed to deliver ≈ net-CONE (~$100–140/kW-yr, PUCT 2024 planning
     CONE) of scarcity rent; at characteristic adder levels ($2–4k/MWh) that
     is on the order of 25–70 full-price-hours/yr, and realized RT history
     (ex-Uri) has ranged from single digits to a few hundred hours — hence
     an order-of-magnitude corridor [2, 200] on the mean. >800 h in one year
     is sustained-VOLL behavior no external outlook contemplates (corridor
     memo D6). At T1-F the window is too short to score an equilibrium
     frequency; the count is reported.*

### FC-3 — Capacity-evolution skill *(instrument: T1-H hindcast)*

- **Inputs:** the committed hindcast `score.json` (+ sidecar) for the ISO —
  `score_capacity_hindcast.py` output on the 2021–2025 (2020-vintage,
  2022-bridged) window; optionally a committed T-R scorecard.
- **Metric & thresholds: imported by reference, never restated.** The gating
  bands are exactly `docs/handoffs/forecast-validation-program-2026-07.md`
  §1.4 (cumulative thermal retired ±10% total / ±20% per fuel; unit recall
  ≥ 70% for >300 MW units; false-retire ≤ 15%; timing ≤ 1.5 yr; additions by
  tech ±15% wind/solar/gas, ±25% storage; tech-mix shares Δ ≤ 5 pp; hindcast
  2025 CO2 ±10% headline) **plus** the applicable T-R rows
  (`forecast-retirement-calibration-plan-2026-07.md` §3, incl. T-R7 zero
  economic nuclear exits and — once FF-1A lands it — T-R10 no-inversion).
  The scorer **reads the `band` verdicts already computed and committed by
  `score_capacity_hindcast.py`** — it never recomputes a band, so a looser
  restatement is structurally impossible.
  *Rationale: those bands were pre-registered by their own documents before
  the probe runs; this rubric's job is composition, not re-derivation.*
- **Aggregation:** any gated band `FAIL` ⇒ FC-3 `FAIL` (offending metrics
  listed). All gated bands `PASS` plus baselines beaten (the §1.4 requirement:
  beat frozen-fleet and announced-only on retirement recall and addition mix,
  when the baseline block is present in the score) ⇒ `PASS`. Baselines absent
  from the committed score ⇒ `CAVEAT` (skill-vs-baseline unproven, recorded).
- **T1-X capacity events (2 evolution steps)** are *(report-only)* context
  here — the program pre-declared them weak-alone (plan §2.2); they may
  annotate FC-3 but never gate it.
- No committed hindcast score for the ISO ⇒ `SKIPPED` (the NEISO state —
  "evidence-free" is a recorded hold, not a pass).

### FC-4 — Crossover dispatch skill *(instrument: T1-X)*

- **Inputs:** the committed `score_crossover.py` output: per-metric
  forecast-mode errors for 2023–2025 side-by-side with the ISO's committed
  keeper backcast errors, plus the structural **≥2026 refusal marker** (the
  scorer's proof it never read bench/actuals for 2026+).
- **Rows:**
  1. **Quarantine integrity.** The refusal marker must be present and clean.
     Absent or violated ⇒ FC-4 `FAIL` outright. *Rationale: rule 22 — a
     crossover score that touched ≥2026 actuals is inadmissible evidence,
     whatever its numbers.*
  2. **Absolute dispatch skill under forward inputs.** Per metric — annual
     load-weighted price, system CO2, gas-family TWh, coal-family TWh — the
     forecast-mode |error| for each of 2023–2025 must sit within the
     **backcast rubric's commercial band × the ISO's input-gap multiple
     K_iso**: price ±10%×K, CO2 ±10%×K, family volume ±5%×K, with
     **K = 1.5 for ERCOT/NEISO/CAISO/NYISO and K = 3.0 for PJM/MISO.**
     Beyond ⇒ `FAIL`; within band but beyond 1.0× the commercial band ⇒
     `CAVEAT` (the measured input gap, listed with magnitudes).
     *Rationale (the plan §3 instruction "FF-0A sets the acceptable input-gap
     multiple from the D-7 statmode evidence"): the D-7 study
     (`forecast-validation-program-2026-07.md` §5, committed 2026-07-05 —
     evidence that predates every run this rubric will score) measured what
     the backcast-only overlays carry per ISO: ERCOT/NEISO statmode CO2 stays
     inside the keeper's PASS band (overlays carry little system-level skill
     ⇒ forward inputs should land near commercial grade ⇒ K=1.5), while
     PJM/MISO statmode CO2 degrades to +11–27% (overlays carry real skill in
     outage- and coal-cost-sensitive fleets ⇒ a forward-input run should be
     expected near ~3× the commercial band ⇒ K=3.0, ceiling ±30% CO2 — which
     the D-7 worst case, PJM +26.6%, sits just inside). CAISO/NYISO's D-7
     rows are confounded (stale keepers), so they take the tight multiple
     rather than the lenient one — a deliberate strict default.*
  3. **Input-gap ratio** — (forecast-mode error) ÷ (keeper backcast error)
     per metric-year — is *(report-only)*: it is THE program-level headline
     (the honest answer to "how much accuracy do the overlays carry") but a
     ratio over a near-zero keeper denominator is degenerate, so it annotates
     and is quoted, never gated.
- No committed crossover score ⇒ `SKIPPED`.

### FC-5 — External corridor *(context discipline, T2/T3 gate)*

- **Inputs:** committed benchmark tables (§6 inventory; intaken by FF-0D) and
  the bundle's 2030/2035(/2040 where the window reaches) capacity-mix,
  energy-mix, and CO2 snapshots; a per-row **disposition table** authored by
  the scoring session (the corridor memo's discipline).
- **Metric:** per quantity-row, the model value vs the external anchor(s),
  with the `cross-model-corridor-2026-07-13.md` convention imported whole:
  divergence **> 15% (or opposite sign/direction)** requires a written
  ours-vs-theirs explanation naming the mechanism; verdicts per row are
  `IN CORRIDOR` / `EXPLAINED DIVERGENCE` / `UNEXPLAINED`.
- **Threshold:** any `UNEXPLAINED` row ⇒ FC-5 `FAIL` (routes to root cause —
  the D5 precedent). All rows in-corridor ⇒ `PASS`. Explained divergences
  only ⇒ `CAVEAT` (each listed with its blocker/mechanism reference).
  *Rationale: benchmarks are context, never fit targets (rule 13, plan §7.6)
  — so conformance cannot be a numeric band (that would make AEO a fit
  target). What IS gateable is the explanation discipline: "divergence is not
  failure; unexplained divergence is" (corridor memo §1). The 15% trigger is
  the corridor memo's own pre-registered convention, reused unchanged.*
- At T1 tiers FC-5 is *(report-only)* (announced-pipeline / ISO-forecast
  plausibility context); it gates at T2/T3 per plan §2.1.
- Benchmark tables absent on disk ⇒ `SKIPPED` with the missing-source list
  (feeds §6; a T2 bundle cannot promote with FC-5 unscored).

### FC-6 — Driver response

- **Inputs:** committed `run_driver_battery.py` machine output (Tier-1
  monotonicity ladders) at the bundle's config vintage; paired-invariant
  results P1–P3 from `check_forecast_invariants.py --paired`.
- **Rows:**
  1. **Tier-1 gate rows:** any ladder expectation marked `gate` that `FAIL`s
     ⇒ FC-6 `FAIL` (e.g. the T1.4a #2064 non-monotone scarcity).
  2. **Vacuous passes:** a gate row that passed on an empty or all-constant
     series (the T1.6a/T1.7a findings of `driver-battery-2026-07-12.md`) is
     `CAVEAT`, never `PASS` — the scorer checks the row's series metadata
     (`n_rungs_solved`, constant-series flag) where the battery output
     carries it, and trusts an explicit `vacuous` marker otherwise.
     *Rationale: the 2026-07-12 battery report's own instruction — a vacuous
     PASS "should not be cited as confirmation".*
  3. **Paired invariants:** P1 or P2 `FAIL` ⇒ `FAIL` (sign responses to
     carbon/gas are the model's economic core); P3 `WARN` ⇒ `CAVEAT`
     (cliff-edge sensitivity, reported).
  4. Report-only ladder rows and elasticity magnitudes annotate the verdict.
- **Threshold rationale:** monotonicity/sign expectations were pre-registered
  in the driver-battery plan before its first run; the rubric composes their
  outcomes and adds nothing numeric of its own.
- Battery output absent ⇒ `SKIPPED` (required at T2/T3; optional-but-recorded
  at T1-F where the plan's gate battery, FF-2D, supplies it).

### FC-7 — Provenance & DOF *(the governance gate; mirrors backcast C6)*

- **Inputs:** `run_config.json`, `dof_ledger.json`,
  `forecast_attestation.json` (T3).
- **Rows (machine checks):**
  1. `run_config.json` present, parses, `mode == "forecast"` (hindcast tiers:
     the harness's own mode), and records the full flag surface (rule 24 —
     every tunable visible; the scorer checks a non-empty config dump and the
     presence of the tier's expected gates, e.g. `capacity_market_clearing`).
  2. **No backcast overlay may be armed in a forecast-mode run:**
     `outage_source` must be a statistical/forward source and the
     backcast-only overlay flags (CAMPD outage windows, F923 delivered fuel,
     same-year CEMS rates, weather-year pinning) must be off. Any armed
     overlay ⇒ `FAIL`. *Rationale: forecast methodology by construction
     (CLAUDE.md "Forecast vs backcast"); an overlay-armed "forecast" is a
     category error, not a caveat.*
  3. **DOF ledger:** every entry names {parameter, value, identification
     source}; parameters whose identification is open must be listed as open
     (rule 21). Ledger present and well-formed ⇒ `PASS` row; absent ⇒
     `CAVEAT` at T1/T2, **`FAIL` at T3** (a golden candidate without its DOF
     ledger is unattestable by plan §0.1).
  4. **Attestation (T3 only):** the §5 checklist assertions all present and
     true; absent ⇒ `FAIL` (`UNATTESTED` — you cannot certify a golden run
     you have not attested; the C6 posture verbatim).
- *Rationale: these are rules 5/13/21/24 made executable on the forecast
  side; thresholds are structural (present/absent/armed), so there is nothing
  numeric to tune.*

### FC-8 — Runtime feasibility *(WARN-level, never blocking)*

- **Inputs:** per-year wall/RSS from the summary (`per_year_perf`,
  `global_peak_rss_mb`, `total_wall_s`).
- **Metric & thresholds:** total wall vs the plan §2.4 tier budget —
  t1f/t1x ≤ 45 min, t1h ≤ 2.5 h, t2 ≤ 2 h (BAU), t3 ≤ 9 h — and peak RSS vs
  the 15 GB box anchor (≥ 8.6 GB flags the "no co-run" condition).
  Over budget ⇒ `CAVEAT` (with the measured numbers — this is FF-3C's
  trigger data); within ⇒ `PASS`; missing perf ledger ⇒ `SKIPPED`.
  **FC-8 can never `FAIL` and never blocks promotion** (plan §3: WARN-level,
  reported).
  *Rationale: budgets are the plan's own measured scheduling anchors (§2.4),
  imported by reference; runtime is a program-management signal, not a model
  quality claim.*

---

## 3. Tier applicability & promotion logic

`--tier {t1f,t1x,t1h,t2,t3}` selects the applicability row. **R** = required
(must be scored; `SKIPPED` ⇒ `HOLD`), **O** = optional (scored if artifacts
present; absence recorded), **rpt** = report-only at that tier, **—** = not
applicable. FC-8 is required-but-never-blocking (its `SKIPPED` does not
`HOLD`).

| Category | t1f (2026–30) | t1x (2023–27 crossover) | t1h (2021–25 hindcast) | t2 (2026–35) | t3 (2026–50 golden) |
|---|---|---|---|---|---|
| FC-1 structural | **R** | **R** (invariants incl. 2026–27) | O | **R** | **R** |
| FC-2 adequacy/equilibrium | **R** (rows 1,3,4; 5 if curve-ON; 6 rpt) | O | — | **R** (all rows) | **R** (all rows) |
| FC-3 capacity skill | — | rpt (2-step events) | **R** | **R** (imported t1h score) | **R** (imported t1h score) |
| FC-4 crossover skill | — | **R** | — | **R** (imported t1x score) | **R** (imported t1x score) |
| FC-5 external corridor | rpt | rpt | — | **R** | **R** |
| FC-6 driver response | O | — | — | **R** | **R** |
| FC-7 provenance/DOF | **R** | **R** | **R** | **R** | **R** (+ attestation) |
| FC-8 runtime | R* | R* | R* | R* | R* |

Promotion gates (restating plan §2.1 in category terms — this table is the
executable form):

- **T0→T1:** FC-1 `PASS` on the feature probe (invariants only; the scorer's
  `--tier t1f` run on a T0 probe covers this).
- **T1→T2:** FC-1 `PASS`; FC-2 no-`FAIL`; FC-3 within its imported bands (no
  `FAIL`, from the ISO's t1h instrument); FC-4 within its bands (from t1x);
  FC-6 gate rows green. A category `SKIPPED` that the tier requires ⇒ the
  gate is not met (`HOLD`) — unscored evidence never promotes.
- **T2→T3:** adds FC-5 (no `UNEXPLAINED` divergence) and stability through
  2035: no I12 breach trend (I12 `FAIL`, or a `WARN` chain of ≥ 3 consecutive
  years inside 2031–2035, fails row FC-2.1 at t2), no I13.
- **T3 (golden):** all categories scored, no `FAIL`, plus the §5 attestation.

**Determination per tier run:**

| Outcome | Conditions |
|---|---|
| `PROMOTE` | every required category scored; no `FAIL`; no `CAVEAT` |
| `PROMOTE-WITH-CAVEATS` | every required category scored; no `FAIL`; ≥ 1 `CAVEAT` (all listed with magnitudes) |
| `HOLD` | any required category `FAIL` or `SKIPPED` (except FC-8) |

Caveats are **listed, never budgeted** in v1.0: the forecast program's caveat
taxonomy should be derived from measured T1 evidence, not guessed — a caveat
budget (the backcast §2 pattern) is deferred to a v1.x amendment once FF-2D's
gate battery shows which caveat classes recur. Until then every caveat prints
and none is silently absorbed. A failed ISO/feature goes back to its lane; it
never "rides along" into a longer solve (plan §2.1).

---

## 4. Anti-gaming clauses (inherited, binding)

1. **Bands never widen in response to a result** — a miss is a root-cause
   investigation routed to a lane (rules 1/11/14). Amending a band requires
   an owner-signed rubric version bump with an external rationale.
2. **Benchmarks are context, never fit targets** (rule 13): nothing in the
   model may be tuned toward an FC-5 anchor; FC-5 gates *explanation*, not
   proximity.
3. **Imported bands rule:** FC-3/FC-2.5 thresholds live in their source
   documents/scorers and are consumed as committed verdicts — this rubric
   cannot restate them and therefore cannot loosen them.
4. **No promotion on partial evidence:** required-`SKIPPED` ⇒ `HOLD`. The
   NEISO precedent (no hindcast pair at all) reads `HOLD`, not
   benefit-of-the-doubt.
5. **Vacuous evidence is caveated evidence** (FC-6.2): an untested claim is
   never quoted as a confirmation.
6. **Quarantine supremacy:** any artifact that touched a quarantined year
   (2022, 2019, ≤2021 outside the hindcast's {2021} allowance, H1-2026) is
   inadmissible; FC-4's refusal marker makes this machine-checked where the
   risk is structural (rule 22, plan §2.3).

---

## 5. Golden-attestation checklist (T3)

A T3 bundle carries `forecast_attestation.json` with all of:

1. **DOF ledger complete** — every free parameter → identification source;
   open DOFs listed as open, not hidden (rule 21). (`dof_ledger.json`
   referenced by path + hash.)
2. **run_config reproducibility** — the committed `run_config.json` + code
   SHA regenerate the bundle (the FF-4B reproducibility check); SHA recorded.
3. **Honest-unfit list referenced** — the bundle names what it cannot claim
   (locational siting, forward-auction timing, gated mechanisms/ISOs — plan
   §0.3), by pointer to the FF-4B list.
4. **Quarantine attestation** — no locked-test or validation year was solved,
   scored, or read in producing the bundle (rule 22).
5. **No off-registry knobs** — every active tunable appears in
   `ScenarioConfig`/`constants.py` and the run's `run_config.json` (rule 24).
6. **Registration** — the bundle + rubric JSON sidecar are registered on the
   forecast-validation dashboard namespace in the producing session (plan
   §7.5).

The scorer verifies presence + internal consistency (machine-checkable
parts); the truth of the assertions is the attesting session's auditable
responsibility, exactly as backcast C6.

---

## 6. FC-5 benchmark inventory — on disk today vs intake gaps (for FF-0D)

Verified against `data/raw/` at authoring time (2026-07-17). FC-5 needs
**committed, machine-readable benchmark tables** (per-ISO rows: source,
vintage, year, quantity, value, unit) — today they do not exist; the corridor
memo was built from web fetches, which is not reproducible scoring input.

**On disk (usable already):**
- `data/raw/eia-aeo/` — AEO2025 **fuel-price** trajectories only (API-fetched;
  the `eia-aeo-fuel-prices` clean datatype). Usable for FC-5 fuel-path
  context rows; carries **no** capacity/generation/CO2 projections.
- `data/raw/nrel-atb/` — ATB 2024 **cost** data (entry-cost source), not
  Standard Scenarios projections.
- `data/raw/capacity-market/` — auction prices, demand curves, ELCC,
  accreditation filings (FC-2.5/T-R4 inputs — already the position
  instrument's source, not FC-5's).
- Monitor SOM PDFs on disk (`som-competitive-conduct/`, cited in the corridor
  memo §2) — support the net-revenue context rows, not the corridor tables.

**Intake gaps — the FF-0D list (do NOT intake in FF-0A):**
1. **EIA AEO2025 regional electricity projections** — capacity by fuel,
   generation by fuel, power-sector CO2, for the model's ISO regions
   (electricity-market-module regions), 2030/2035/2040. API route exists
   (same `aeo` route as the fuel-price fetch) — extend
   `scripts/data/fetch_eia_aeo.py`.
2. **NREL Standard Scenarios 2024 Mid-case** — regional capacity/generation
   2030/2035 (the corridor memo notes the viewer-only retrieval problem; the
   Scenario Viewer's underlying CSV download is the intake target; if only
   national grain is retrievable, record that limitation in the table).
3. **ERCOT CDR (Dec 2025 vintage)** — planned additions by tech to 2030,
   peak-load scenarios, reserve margins.
4. **PJM 2026 Load Forecast + 4R retirement study** — peak/energy growth,
   at-risk retirement GW by 2030.
5. **NYISO 2026 Gold Book** — Table-form capacity/load forecasts.
6. **ISO-NE CELT 2026** — energy/peak forecasts incl. the winter-flip rows
   (the D12 shape anchor).
7. **CAISO/CPUC** — CPUC PSP portfolio (D.24-02-047 / 2025-26 TPP new-build
   by tech to 2035) + CEC IEPR demand forecast.
8. **MISO futures / OMS-MISO survey** — capacity outlook rows (MISO was
   absent from the corridor memo's model side; its benchmark side should
   land anyway).
9. **Schema:** one curated `benchmark-corridor` datatype
   (`data/dictionary/schema/benchmark-corridor.schema.yaml`) with columns
   `{iso, source, vintage, target_year, quantity, tech?, value, unit, note}`
   so FC-5 scoring reads one parquet/JSON, per the data-intake skill contract.

Until (1)–(8) land, FC-5 scores `SKIPPED` with this list attached — which by
§3 holds any T2 promotion, making the intake self-enforcing.

---

## 7. Honest limits of this rubric (standing)

- FC-3 passing certifies *hindcast-window* capacity skill under realized
  inputs; it is necessary, not sufficient, for forward skill (§1.3
  literature). No determination here is a forecast-accuracy guarantee.
- FC-5 conformance certifies *explained position vs external views*, not
  correctness — external outlooks are themselves forecasts.
- The locked-test years (2019, H1-2026) and validation year (2022) are
  **outside this rubric entirely** (owner-run one-shots, plan §2.3); nothing
  here may quote them.
- Locational siting and forward-auction timing remain un-certified until the
  honest-unfit list says otherwise (plan §0.3).

## 8. Usage

```bash
# T1-F short-forecast bundle:
python scripts/forecast_verdict.py --tier t1f \
    --summary results/ff-t1f-baseline/ercot/full_horizon_summary.json \
    --json-out results/ff-t1f-baseline/ercot/forecast_verdict.json

# T1-H hindcast bundle (FC-3 primary):
python scripts/forecast_verdict.py --tier t1h \
    --hindcast-score results/hindcast/<run_id>/score.json \
    --run-config results/hindcast/<run_id>/run_config.json

# T2 gate (all instruments):
python scripts/forecast_verdict.py --tier t2 \
    --summary <t2 summary> --hindcast-score <t1h score> \
    --crossover-score <t1x score> --driver-battery <battery json> \
    --corridor <corridor table> --dof-ledger <dof> --json-out <sidecar>
```

The JSON sidecar (`forecast-verdict/v1` schema) is the future forecast
dashboard's per-run rubric block (plan §8 / FF-5A).

## 9. Version history

- **v1.0 (2026-07-17, FF-0A)** — initial rubric: categories FC-1..FC-8 per
  plan §3, tier ladder T0→T3 promotion logic, golden-attestation checklist,
  FC-5 benchmark-intake inventory, research grounding (§1). All thresholds
  pre-registered before any T1 gate battery run; no threshold derives from
  any run produced after 2026-07-16 or from any run this rubric has scored.
