# Market Simulation Model — Claude Code Instructions

## Response Style

Default to concise answers: lead with the result/answer, keep prose tight, and
expand only when asked. Prefer short paragraphs and small lists over long
blocks of text. Don't restate the question or pad with preamble.

**Deliver copy-paste artifacts whole, in one block.** Whenever the output is
something the user will copy and use as a unit — a handoff prompt for a new
session, a command, a config snippet, a commit message, a block of code — emit
the complete, final version in a single fenced code block, ready to paste. Never
build such an artifact incrementally across multiple turns and expect the user to
stitch the pieces together. If new information means an artifact needs to change,
re-send the entire updated artifact in one block, not a diff or an addendum.

## What This Is

LP-based electricity market dispatch simulator. Forecasting model (2026–2050) with a historical-backcast mode for calibration. Multi-ISO: six ISOs registered in `config/iso_configs.py` — ERCOT (7 zones, 6 carry load; the calibrated reference), CAISO (3 zones + WECC import node), PJM (8 zones), MISO (6 zones), NYISO (5 zones), NEISO (4 zones + HQ import node) — sharing one ISO-agnostic LP. Hourly 8760 dispatch, parameterized scenario system.

**Forecast vs backcast:** the model forecasts by default; the switch is the explicit `ScenarioConfig.mode` field (`"forecast"`/`"backcast"`), never inferred from other parameters. Historic overlays — CAMPD outage windows, F923 delivered fuel prices, **same-year plant-specific CEMS emission rates**, weather-year pinning — are **backcast/calibration only**; never treat them as the forecast methodology. (Forecast-year emission rates for existing units are *derived from* multi-year CAMPD history conditioned on model-simulated operation — a rule-13-admissible measured input, not an overlay; see `docs/handoffs/emissions-co2-rate-plan-2026-07.md`.)

## Stack

- Python 3.11+, HiGHS via `highspy`, numpy, scipy.sparse, pandas, pyarrow, pydantic, pyyaml
- **FORBIDDEN:** Pyomo, PuLP, scipy.optimize, Numba. Direct CSC matrix → HiGHS only.

## Architecture

```
src/market_sim/
  config/    → ScenarioConfig, constants, 6-ISO topology, on-disk path registry, reserve/interchange specs, crosswalks, taxonomy
  data/      → source loaders & derived inputs (demand, fleet/CAMPD binning, renewables, fuel, outages, hydro, emissions, offer curves, capacity/reserve inputs)
  model/     → the ISO-agnostic LP: dispatch (LP core, duals=price), commitment, transmission, storage, capacity evolution, ancillary
  policy/    → IRA, RPS, carbon / cap-and-trade, EAC, constraints
  results/   → caching, outputs, emissions, export, calibration/scoring, scarcity overlays, evolution ledger
  pipeline/  → shared per-year solve core (spec, kwargs, prior, result, backcast_config, commitment, solve)
  ensemble / matrix / uncertainty / structural_prior → ensemble & forecast-uncertainty layer
  runner.py  → main orchestrator (P0→P1 solve loop, year evolution)
  (full, current per-module inventory: docs/codebase/01-architecture.md — kept in sync with the code; this tree is the elevator view)
tests/       → pytest, one file per module
scripts/     → core entry points & standing tooling ONLY (calibration/hindcast/forecast runners, scoring, dashboard, governance) — see scripts/README.md
  data/      → data fetching & processing (fetch_*, curate_*, derive_*, per-source build_*) — not core engine
  archive/   → retired one-off run drivers/probes/analyses; historical record, not maintained
  lib/       → shared helpers; probes/ → per-run probe scripts (calibration record)
data/        → all on-disk inputs; every path resolves through config/paths.py (never Path(__file__).parents[...])
  raw/       → immutable source downloads, NEVER modified in place — the single source root (W1 collapsed the old inputs/ + data/ roots into data/raw/)
               eia-930*/, eia-860/, fleet-egrid/, campd-{unit,facility}-level/, gas-prices/, lmp-data/, zone-specific-demand/, …
               reference/ (loose crosswalks: custom-bin-assignments.csv, master-plant-registry.csv, …),
               _processed-legacy/ (former inputs/processed), _validation-source/ (former inputs/calibration)
  clean/     → curated, schema-validated Parquet (DERIVED, disposable, gitignored)
  dictionary/→ the data contract: schema/<datatype>.schema.yaml + data-dictionary.md
```

## Non-Negotiable Rules

Each rule carries a stable ID (`[R-STRUCT]`, `[R-PUSH]`, …). Cite the ID in code
comments and docs; the ordinals are never renumbered, so both remain valid.

1. `[R-STRUCT]` **Right market structure first, offer-curve tuning second — backcast match is NOT the objective.** The goal is a model whose *mechanisms* mirror the real market (reserve withholding/co-optimization, scarcity pricing, congestion, commitment, fuel/passthrough physics). Build the correct structure, *then* tune offer curves to calibrate the level. **Never judge a structurally-correct mechanism by whether it improves the backcast fit, and never reject/revert it because the residual didn't move** — a real market behaviour stays in even if it makes the fit worse (then fix the actual root cause per #11). Conversely, never reach the right number through a mechanism that isn't real (a fitted adder, a load proxy, a haircut tuned to the residual). A run is a "keeper" because it is the most structurally faithful, not because it has the lowest MAE; a more-accurate run that is missing real structure is **not** a keeper.
1. `[R-VECTOR]` **No Python loops over hours in LP construction.** Use np.tile, np.repeat, scipy.sparse.kron, block_diag. If you write `for t in range(8760):` in the matrix builder, stop and vectorize.
1. `[R-RENEW-VAR]` **Renewables are decision variables** on LHS of energy balance with MC=0, upper bound = CF × capacity. NOT netted from demand.
1. `[R-DUALS]` **Prices = LP duals** on energy balance constraints. No separate pricing model.
1. `[R-NO-MAGIC]` **No magic numbers.** Every value from ScenarioConfig or constants.py with citation comment.
1. `[R-SOA]` **Struct-of-arrays before LP construction.** Convert Pydantic objects → FleetArrays (parallel numpy arrays). LP builder only touches arrays and scalars.
1. `[R-PARQUET]` **Parquet for results.** One file per scenario-year. Check-before-run caching.
1. `[R-8760]` **Full 8760 hours always.** No representative days/weeks.
1. `[R-EPSILON]` **Storage tiebreaker ε = 0.001 $/MWh** on charge+discharge to prevent degeneracy.
1. `[R-ONE-PASS]` **One-pass capacity evolution.** No within-year convergence iteration.
1. `[R-DOCSTRING]` **Every public function gets a docstring.** Every module gets a module-level docstring.
1. `[R-PARALLEL]` **Run independent calibration solves in parallel, never consecutively — but always solve years sequentially within a single run.** Each `run_calibration_full.py` LP solve is minutes long; when launching multiple *separate invocations* (different ISOs or configs, each with its own `--out-dir`) with no dependency between them, start them as concurrent background jobs — don't wait for one to finish before starting the next. e.g. launch `--iso PJM --out-dir …/pjm` and `--iso CAISO --out-dir …/caiso` at the same time. **Within a single invocation**, however, years (`--year 2023 2024 2025`) must always run **sequentially** — never in parallel threads/processes — because a single year's LP already uses several GB of RAM and concurrent year solves will OOM on most ISOs. The year loop in `runner.py` is intentionally sequential; do not parallelize it. Separate-invocation concurrency: cap at ~2 simultaneous runs for per-plant (`plant_level_fleet`) multi-zone LPs to stay within memory limits.
1. `[R-MEASURED]` **Measured data is allowed only as a *reproducible physical/market input*, never as the *answer* — no pinning the backcast to actuals.** Real measured data may be used when it is grounded in physics or market design **and** enters as a formulaic input that would regenerate for a future year and respond to changed conditions in a forecast — e.g. unit outage windows (a physical availability event), delivered fuel prices, plant-specific CEMS emission rates, a measured ancillary-service power reservation. The admissibility test is: **could this same quantity be produced for a forward year from forward drivers, and would it respond to changed conditions?** If yes, it is a legitimate input *even in backcast mode*. What is **forbidden** is feeding a measured *outcome* back in to force the backcast to match: pinning a unit to its observed CEMS generation, adding an offset/haircut/adder tuned to the price or volume residual, or rescaling an input so the model's *output* lands on the actuals. Those have no forward analogue — the dispatch being validated is then not the dispatch being forecast, so the "fit" measures plumbing, not skill. A measured input that fails the test may exist only as an explicitly-labelled, default-**off** diagnostic probe; it must never be enabled in a keeper or quoted as evidence of forecast skill. (This sharpens #1 and #11; the concrete forecast-vs-backcast line is methodology spec §1.7, and the live overlay inventory is `docs/backcast-measured-data-audit-2026-06.md`.)
1. `[R-ACCURATE]` **Prefer accurate/measured data over estimates whenever it's available — never revert to an estimate just because it fits the backcast better.** If swapping a hand estimate for real data (a measured TTC/GTC limit, metered load, actual outages, real fuel prices, etc.) makes the backcast *worse*, that is a signal that **something else in the model is miscalibrated** and the estimate was silently compensating for it. Treat the worse fit as a discovered bug: keep the accurate input, find and fix the real root cause (offer curves, must-run, passthrough sigmoids, fleet/zone assignment, etc.). Do **not** bury the error back inside an inaccurate input. The *only* exceptions — where an estimate may be kept — are when the accurate data is genuinely **misaligned to our representation** so that using it literally would make overall results *less* reflective of reality, e.g.: the data is defined on a different boundary than our zones (a single GTC that is one of several parallel paths our reduced network collapses into one link), a different time/area aggregation, or units/sign conventions that don't map. In those cases, document the misalignment explicitly in a comment and prefer a *reconciled* version of the real data over a pure guess. When in doubt, use the real data and open the root-cause investigation.
1. `[R-DASHBOARD]` **Every completed backcast run goes on the dashboard — results live there, not in chat.** The moment a calibration run finishes (keeper *or* rejected probe), register it on the backcast results dashboard and commit+push it **in the same session it was produced** — use the `calibration-report` skill / `scripts/dashboard_add_run.py`, then `build_manifest.py`. The dashboard is the codebase-site pages — `docs/codebase-site/backcast-runs.html` (run explorer, `#iso=<ISO>&run=<id>`) and `docs/codebase-site/calibration-status.html` (all-ISO keeper summary, `#iso=<ISO>`); the old root `backcast-results.html` is a static redirect stub, never regenerated. The committed per-run files (`results/calibration/<name>/` bundle + `frontend/data/backcast/registry/<id>.json` + `runs/<id>.js` + changed `bench/`) are the deliverable; the Pages deploy workflow rebuilds `manifest.js`/`benchmark.js`/`completeness.js` from the sidecars at deploy time, so a registered run shows on the LIVE dashboard once the deploy runs (committing those generated files is optional, local-`file://`-preview only — see Git & Pushing §3). A run is **not "done" until its bundle and dashboard files are committed and pushed** — do not just narrate metrics in chat and move on. Honour the top-15-per-ISO retention (PJM labels `pjm N <keyword>`). Lead with the dashboard result; keep the prose minimal. KEEPER bundles additionally commit their `hourly/` sidecars (`class_hourly_<year>.parquet` + `system_<year>.parquet`, written by every solve since 2026-07-19; plus `reserve_family_<year>.parquet` since 2026-08-03 — the per-family reserve balance-row dual, requirement, held MW and ORDC shortfall, which is the ONLY artifact in which a locational reserve family's binding is observable, since `system`'s `reserve_price` is the cross-family SUM broadcast identically to every zone) so later diagnostic sessions read the keeper's class-dispatch/price hourlies instead of replaying the solve — a keeper replay is justified only for unit-level questions. **Forecast-family runs** (T1-F / T1-X / T1-H / CES-POC hindcasts & full-horizon summaries) go on the SEPARATE forecast dashboard — `docs/codebase-site/forecast-runs.html` (run explorer, `#iso=<ISO>&run=<id>`) + `forecast-status.html` (per-ISO §2.1b gate board) over the `frontend/data/forecast/` namespace, registered via the SINGLE `scripts/register_forecast_run.py` path. The namespace `registry/<id>.json` + `runs/<id>.js` + `manifest.js` + `program-status.js` are GENERATED (gitignored — the Pages deploy is their single writer; `--reindex` regenerates them locally for the `file://` preview) and fully derived from the COMMITTED inputs: the hindcast sidecars + the FF-2D verdict snapshot `frontend/data/forecast/ff-verdicts.json` + the board seed `program-status.json`. `--reindex` bakes the FF-2D rubric verdicts and doubles as the stdlib deploy assembly (`deploy-pages.yml` runs `--reindex --site-dir _site`). NEVER the backcast registry — the backcast CI gates stay blind to the forecast namespace (forecast plan §7.5).
1. `[R-ALLYEARS]` **Always solve and register ALL available backcast years in one bundle — never a single-year keeper.** Every multi-year ISO's calibration run covers every year the ISO can score, in a single `--year` invocation and a single bundle: **CAISO / PJM / NEISO / NYISO / MISO → `--year 2023 2024 2025`** (add new years as they land). A one-year solve (e.g. 2024-only) is permitted *only* as a throwaway diagnostic probe to isolate a single-year effect — it must **never** be registered on the dashboard as a keeper, and any 2024-only bundle found on the dashboard should be re-solved across all years or pruned. When re-gating or re-solving a keeper, reproduce its full year span, not just the year you happen to be studying.
1. `[R-FLOOR-WINDOW]` **No floor without a window, a driver, and a forward story.** Every min-gen/commitment floor
    states (a) its external driver, (b) the hours it may bind and why, (c) how it regenerates in a
    forecast year. A floor binding in hours its own driver evidence says the class is offline
    (CT overnight CF ≈ 0) is a bug by definition, whatever it does to the residual.
1. `[R-PHYSICS]` **Commitment physics by parameters, not class names.** Bridge/commit eligibility gates on unit
    physics (`min_down_hours`, startup cost) — never a hard-coded class tuple. Fast-start units
    (min-down ≤ 2 h, startup < $30/MW) are never economically bridged beyond their min-down.
1. `[R-ONE-MECH]` **One mechanism per phenomenon.** Before adding a floor/bridge, enumerate what already floors
    the same class (D-2 attribution) and replace or reconcile — never stack a new floor on the
    unexplained residual of an old one.
1. `[R-FORCED-BUDGET]` **Forced energy is budgeted.** A keeper fails if any merchant class dispatches > 30 %
    (peakers: > 15 %) of its energy at binding floors. Floors are commitment scaffolding, not the
    dispatch model. This budget applies only to classes whose
    annual energy (max of model and actual, so forcing can't hide a class below the line) is ≥ 2 %
    of total ISO load; smaller classes are reported by the D-1/D-2 diagnostics but never gated —
    trivial-class shape/forcing is not worth structural work. *(The standalone C7 diurnal-shape
    gate that shared this materiality floor was RETIRED by the rubric v3.1 owner amendment
    2026-08-06 — no commercial-grade model gates or publishes diurnal-shape accuracy. The D-1
    measurement is untouched and still binds through this rule's own shape leg below, which is
    now its sole gating path.)* A material class **above** its cap is
    not an automatic fail. It escalates to a conditional pass on **provenance + shape**: it passes
    iff (a) every binding non-exempt mechanism forcing it clears **D-4 off-window binding** (binds
    only in its driver-justified window — a mechanism with no declared window fails, per rule 12),
    **and** (b) its **D-1** diurnal profile clears the gates (`profile_r`/`cv_ratio`). Rationale:
    forcing can be legitimate past the budget when it is a real grid/RA/AS driver that reproduces
    the observed dispatch — *as much as needed* may be forced on a class if it is structurally
    grounded and shape-faithful; what the gate targets is forcing whose **shape or window doesn't
    match reality** (the "forcing variables are wrong" signal). A grounded pass is a **clean PASS
    surfaced as a report note, never a caveat**; a miss FAILs as a forcing shape/provenance
    mismatch. This is scored entirely from the committed `legitimacy_diagnostics.json` (D1/D2/D4
    rows + gates), so it is scorer-only — no re-solve, no bundle regen, and existing keepers
    re-score in place. **To actually ground a specific keeper's over-budget class**, its mechanism
    needs a cited `D4_WINDOWS` entry in `scripts/legitimacy_diagnostics.py` and that bundle
    re-generated so the D-4 row exists; and any mechanism-change-driven verdict flip is scored
    leave-one-year-out within 2023–2025 before the keeper is promoted. *(Amendment narratives, and
    the "rule 12" ↔ rule 17 `[R-FLOOR-WINDOW]` numbering: `docs/governance/rule-history.md` §2–§3.)*
1. `[R-DOF]` **Every keeper carries a DOF ledger.** The attestation lists each free parameter with its
    identification source. A residual that can only be closed by a tuned value is an open
    root-cause issue, not a parameter. *Amended 2026-07-14 (owner): the zero-forcing ablation
    twin is NO LONGER required — keepers no longer build or register a paired zero-forcing run.
    Forcing-legitimacy now rests on the DOF ledger plus the D-2 / `legitimacy_diagnostics.json`
    mechanism attribution (the C8 forced-share gate and D-4 off-window-binding check) alone.
    Already-registered twins may remain on the dashboard as historical artifacts; no new twin is
    produced (probe, candidate, or keeper).*
1. `[R-HOLDOUT]` **Hold out data across three tiers — train, validation, locked test — and never let a
    locked-test result re-enter tuning.** *(Amendment genealogy:
    `docs/handoffs/holdout-policy-memo-2026-07.md` §(e)–(f), indexed in
    `docs/governance/rule-history.md` §4.)* The tiers:
    - **Train / calibration = 2023–2025.** The ONLY years tuned against. Every keeper is built and
      scored here, all three in one bundle (rule 16).
    - **THE PROGRAM'S WORKING SPAN IS 2019–2025 FOR ALL ISOs.** *(Owner decision 2026-08-06.)*
      **2018 and earlier are DROPPED** — removed from `VALIDATION_YEARS`, so `tier_for_year`
      falls through to its fail-closed default and treats them as **locked-test tier**: they
      need a `final` marker no ISO holds, and are unsolvable in practice. This is a
      RESTRICTION, not a relaxation. The substantive reason beyond simplicity: NEISO's 2018
      basis is **unrepairable** — ISO-NE migrated its newswire mid-2018 and the Mar–Jun recaps
      were never carried over, so those four rows stay on the seasonally-inverted EIA N3050MA3
      proxy and June-2018 (+6.2124) is one of the inverted summer values
      (`FINDING-neiso86-gas-basis-intake-2026-08-06.md` §5.1).
    - **Validation holdout = 2022**, extensible backward as a staged ladder (2022 → 2020–2022,
      as data lands and is authorized; **the ladder now bottoms out at 2020**). **Iterable.**
      After an ISO's `complete` marker
      exists, 2022 may be solved and scored, and a miss MAY send you back to re-tune
      2023–2025 and re-solve — that is its purpose (model selection). Because it is iterated
      against, a validation number is selection evidence, **NOT** a certified out-of-sample skill
      number, and must never be quoted as one. **RE-KEY ON PROMOTION** (owner decision D-5(b),
      signed 2026-08-02, `docs/handoffs/ffr-owner-sitting-2026-08-02.md` Addendum C.1): the
      `complete` entry's `keeper` field tracks the ISO's CURRENT designated keeper, so every
      promotion in a `complete` ISO updates it **and re-verifies the entry's `determination`
      against the new run** (`scripts/calibration_verdict.py --run-id <id>` — committed
      artifacts only, never a solve) before the promotion commit lands. A re-verified
      determination that is *worse* stops the promotion and escalates to the owner; it is never
      silently written. The declaration-time run is preserved in `keeper_at_declaration`, and a
      SPENT locked-test one-shot keeps its own frozen config in `locked_test_scored_on` and is
      never re-keyed. Enforced by `scripts/audit_keepers.py` check M1, which the
      `calibration-keeper-auditor` agent runs on every keeper-shard edit.
    - **Locked test = 2019 and H1-2026.** **Touch-once, ever.** Scored EXACTLY ONCE per ISO with
      the frozen keeper config; the result is recorded whatever it is. **No calibration change may
      respond to a locked-test result** without designating a new never-touched year as its
      replacement. This is the honest out-of-sample number. (2019 is the clean-regime test;
      H1-2026 is the forward-edge test. Pre-2020 years exercise a structurally different fleet —
      grade against regime drift, not raw MAE.)
    - **The two tiers carry SEPARATE markers** (owner decision 2026-07-31), because one
      declaration must never spend both: `calibration-complete.json`'s **`complete`** block
      authorizes the validation ladder and **`final`** authorizes the locked test. An ISO in
      `complete` but not `final` may spend 2022 and **nothing else**. Absence from `final` is NOT
      self-explaining — read the ISO's `locked_test` note, which distinguishes "never authorized"
      from "authorized once, **SPENT**, never re-grantable". **NO ISO IS CURRENTLY IN THE SPENT
      state: no locked-test year has ever been solved, scored or registered for any ISO.**
      *(Corrected 2026-08-06, owner decision D-23: this clause previously read "(NEISO is the
      latter)" — i.e. that NEISO's 2019 + H1-2026 one-shot had been SPENT on 2026-07-07 and was
      never re-grantable. That was false. The artifact record carries no NEISO 2019 or H1-2026
      solve of any kind — every NEISO registry sidecar ever committed declares years drawn only
      from {2022, 2023, 2024, 2025}, `bench/NEISO/` holds 2022–2025, `actual_tail.json` has no
      2019 row to score against, and the memo cited as the authorization never mentions 2019.
      NEISO's locked test is **NEVER GRANTED**, not spent. The correction changes only which
      question is open — "should a never-granted one-shot be granted now" rather than "may a
      spent one be re-granted" — and **grants nothing**: NEISO stays absent from `final`, the
      gates still refuse it, and its `final` readiness answer is **NOT YET** on the merits
      (2019 is unsolvable at HEAD and cannot discriminate on C3c). Citation chain:
      `results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
      `docs/third-party-peer-review-2026-07.md` §6.3 item 1 → D-23 / sitting Addendum X.6;
      genealogy in `docs/governance/rule-history.md` §4.)* Tier
      membership and the block mapping live in `scripts/lib/holdout_policy.py`; the
      **holdout spend freeze** (`holdout-freeze.json`) outranks both blocks and is checked first.
    - **C3c STANDING RULE (owner, 2026-08-06; EXTENDED TO EVERY YEAR 2026-08-09): a LONE C3c
      failure in ANY year — training, validation or locked test — is an AUTO-LEDGERED
      `CALIBRATED-WITH-CAVEATS`, in every ISO, going forward.** When C3c (price tail /
      scarcity, RT hourly) is the **only** failing criterion and the governance gate passes,
      `calibration_verdict.py::_apply_c3c_standing_rule` reclassifies it to a CAVEAT
      (`ACCEPTED MODEL-CLASS LIMITATION`) instead of failing the run to `NOT-YET`. It
      **cannot become a general escape hatch**, and the guards that stop it are unchanged:
      (a) **lone failure only** — if any other criterion fails, the rule stays silent and
      *every* failure stands, C3c's included. This is the real guard: it fires only on a model
      that is otherwise clean, so it can never mask a second defect; (b) **governance must
      PASS** — a failing or unattested C6 blocks it; (c) **supporting tier only, fail-closed**
      — it classifies `model-class`, which the v3.0 guard admits only for a SUPPORTING-tier
      criterion, so it can never reach load-bearing (C1/C2/C3a/C3b) or protective (C6/C8);
      (d) it is **never a PASS** — the miss is reported at full magnitude, the run can never
      read `CALIBRATED`, and the caveat still spends the single ledgerable slot.
      **Why extending it to in-sample years is not a loosening.** The former clause (c),
      *out-of-training ONLY*, was never a statement about C3c's severity — band, tier and
      reported magnitude are identical in every year. In-sample the SAME reclassification was
      already reachable through an explicit exceptions-ledger entry, and that is the route
      every current keeper carrying a C3c caveat actually used; the split governed only who
      typed the justification, not what a run could claim. Since rubric v3.1 C3c is the ONLY
      ledgerable criterion at all, so the two routes had already collapsed onto one criterion —
      2026-08-09 collapses them onto one *rule*.
      **A defect fixed in the same amendment (rubric v3.2), which was suppressing the rule as
      originally declared:** "lone" was measured over EVERY scored record, including the
      REPORTED-ONLY streams the rubric has demoted out of the determination (C5a `co2`, removed
      at v2.9). A `co2` FAIL silenced the rule even though co2 contributes no status, no caveat
      budget and no reason line. It is now measured over `CRITERIA` membership. This
      under-fired **out-of-training years too**, so it is a correction rather than part of the
      widening. **Effect at amendment, measured over all 66 registered runs against a
      pre-change snapshot:** 2 determinations change, both NYISO **non-keeper** probes
      (`2026-08-06-nyiso-130-control`, `-n11-tsl`: `NOT-YET → CALIBRATED-WITH-CAVEATS`), both
      unlocked by the defect fix rather than by the widening; **every keeper of all six ISOs is
      unchanged**. `2026-08-06-pjm-158-novirtual-disarmed` is a lone C3c failure and still does
      not reclassify — its C6 is UNATTESTED, i.e. guard (b) working.
    - **Crossover window = 2024–H1 2026** is scored in BOTH modes — backcast (measured overlays)
      and forecast (forward drivers) — against the same actuals, to measure the backcast→forecast
      input gap. Diagnostic, not a locked test; its forecast side uses no measured actuals so it is
      unrestricted (see the 2026 clause below).

    **WHAT IS HELD OUT IS THE *SCORE*, NEVER THE *DATA* OR THE *ARCHITECTURE*.** *(Owner
    clarification 2026-08-06, session neiso-86 — this REPLACES the former per-window intake
    authorization regime, which had it backwards.)* Measured data inputs are **collected once and
    applied CONSISTENTLY ACROSS ALL YEARS** against the keeper. There is no such thing as an input
    that is "held out": an input is either the best measured representation of a physical/market
    quantity or it is not, and if it is, it belongs in **every** year — 2019 through 2025 alike.
    The whole point is that when we hit **go** on 2019, it is already configured **precisely** like
    the frontier / `complete` / `final` keeper, with nothing left to prepare and no input newer
    than the moment the config froze. Concretely:
    - **Data intake needs NO per-ISO/per-window authorization and no marker.** Prep it, apply it to
      every year, keep it consistent. A measured-input fix (e.g. the neiso-86 gas-basis repair)
      lands across the full span in one pass, not year-by-year under separate grants.
    - **Architecture, mechanisms and config are likewise never "held out"** — the keeper recipe is
      one recipe, and the out-of-training years run it unchanged.
    - What remains restricted is exactly one thing: **looking at the answer.** Solving, scoring or
      registering an out-of-training year is the spend, because it consumes the year's power to
      surprise you.

    **THE TOUCHPOINT LOOP — how 2020/2021/2022 are actually used** *(owner, 2026-08-06)*. These
    are **iterative diagnostic instruments, not one-shots**, and **nothing is ever trained or
    fitted to them**:
    1. Run the touchpoint year on the frozen keeper recipe.
    2. **Diagnose what it surfaces** — the object, not the residual (neiso-85/86 is the model
       case: 2022 surfaced an inverted fuel input; the fix was a data repair with zero DOF, never
       a parameter tuned to 2022).
    3. **Re-train on 2023–2025 around the diagnosed issue** — the training window is the only
       place fitting ever happens.
    4. **Re-test the touchpoint** to see whether it resolved. Repeat as needed, and repeat the
       same loop on 2021 and 2020.
    A touchpoint number is therefore *diagnostic evidence*, never a skill claim — the discipline
    that makes it honest is step 3, that no parameter is ever identified against the touchpoint
    year itself.

    **2019 is THE one-touch year.** It is spent exactly once, at the end, against the fully
    prepared frontier/`complete`/`final` keeper. It is the only year whose result is a certified
    out-of-sample number, and the only one that cannot be re-run.
    Standing clauses:
    - **No solve, no scoring, no registration** may touch an out-of-training year until the ISO
      holds **that year's tier marker** in `frontend/data/backcast/calibration-complete.json`
      (`complete` for the validation touchpoints 2020–2022, `final` for the 2019/H1-2026 locked
      test). This gates the **spend**, i.e. looking at the answer — it does NOT gate preparing the
      inputs or the config, which are unrestricted per the clause above. A `complete` ISO may
      re-run its touchpoints iteratively as the loop requires; the marker is the standing
      authorization for that, not a one-shot ticket.
    - **2026 forecast runs are permitted:** forecast-mode runs (`ScenarioConfig.mode="forecast"`)
      span 2026+ and use no measured H1-2026 actuals (overlays are backcast-only by construction) —
      NOT restricted. Only a *backcast* of H1-2026 on real data, or scoring output against measured
      H1-2026 actuals, is quarantined.
    - Structural mechanism changes are still scored leave-one-year-out within 2023–2025 before
      promotion. In-sample gain with held-out degradation is overfitting, not skill.
    Enforcement (**TIER-AWARE since 2026-07-31; SPEND-ONLY since 2026-08-06** — the gates below check solve/score/register, never data prep): CI (`.github/workflows/ci.yml`,
    `quarantine-gates` job) fails any PR whose registered bundle contains a solve year outside
    2023–2025 before that ISO holds **the marker for that year's tier**, and
    `scripts/run_calibration_full.py` hard-fails any `--year` outside {2023, 2024, 2025} unless
    `--holdout-authorized` is passed AND the target ISO carries that tier's marker — `complete`
    for a validation year, `final` for a locked-test year. A `--year` spanning both tiers needs
    both. All three gates (the CLI year gate, `legitimacy_diagnostics.run_d6_quarantine`,
    `audit_keepers`) read the tier map from `scripts/lib/holdout_policy.py`, which **fails closed**:
    a year in none of the enumerated sets is treated as locked-test, the strictest tier. *(This
    supersedes the former "the CI gate is tier-agnostic … a locked-test year re-solved after its
    one-shot is a governance breach, not a CI failure" clause: spending the touch-once tier now
    requires its own declaration, so the distinction is enforced, not merely disciplined. Re-solving
    an ALREADY-SPENT locked test remains a governance breach rather than a CI failure — CI checks
    the grant, not the spend history, which is what the marker's `locked_test` note records.)*
1. `[R-FROZEN-DERIVE]` **Derive scripts are frozen against residuals.** Measured-behaviour parameters (min-stable
    loads, drag hinges, sigmoid anchors, committed shares) re-derive only when their *source data*
    updates — never because a residual moved. Re-derivation commits must cite the data change.
1. `[R-REGISTRY]` **No off-registry tuning channels.** Every tunable that can change a solve appears in
    `ScenarioConfig`/`constants.py` and the run's `run_config.json` — no env-var knobs, no
    hardcoded per-plant dicts in `data/` modules, no `getattr` fallback literals in the offer path.
1. `[R-ISO-SCOPE]` **Tuned curves never cross ISO boundaries.** A multiplier fitted on one ISO's residual is that
    ISO's; generic fallbacks carry neutral (1.0) bands. (Makes the existing informal rule
    CI-enforced; see D-9.)
1. `[R-DELETE]` **Deleted means deleted.** Deprecated fitted knobs are removed, not zeroed — a deprecated
    parameter that still parses is a re-armable answer key (the ORDC offset was re-swept *after*
    deprecation).
1. `[R-PUSH]` **Core files are never bulk-rewritten over the API, and Sonnet never edits infrastructure.**
    *(Owner order 2026-07-15; the incident that produced it — the `constants.py` 6,368 → 33-line
    truncation and its five fragment "restores" — is recorded in
    `docs/governance/rule-history.md` §5.)* Two binding halves:
    - **Push-integrity protocol (all models, every session).** Never rewrite an existing source
      file ≥300 lines by pushing regenerated full content from the model's response — edit
      locally (Edit tool) and push the exact on-disk bytes. After ANY `push_files` call touching
      a file ≥300 lines, **verify the pushed blob before doing anything else** (fetch the file
      back; compare line count + content hash to local); a mismatch is a stop-the-line event.
      Never commit a placeholder, stub, or partial "stage N" version of an existing source file
      — not even as a temporary restore step: incremental restores live on a branch and merge
      only after byte-verification against the last-good blob. A session that finds a core file
      truncated stops its own task and restores from the last good commit first. If a large file
      genuinely must move in pieces, append chunks across multiple commits and verify the blob
      after each — never overwrite with less than the full known-good content. Enforced by
      `.github/workflows/file-integrity-guard.yml` (fails any PR — and flags any push to main —
      that shrinks a core file >30 % or deletes it, unless the PR carries the
      `intentional-shrink` label).
    - **Model assignment.** Sessions whose scope writes core infrastructure — anything under
      `src/market_sim/`, `scripts/run_*.py` / `scripts/score_*.py`, `CLAUDE.md`,
      `model-methodology-spec.md`, or `.github/workflows/` — are assigned to **Opus or Fable,
      never Sonnet**. Sonnet remains eligible only for purely additive data-intake/docs sessions
      (new files under `data/raw/` + handoff docs). For the retirement-calibration lane
      specifically (`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md`), **ALL
      remaining sessions are Opus/Fable regardless of scope** (owner order, this rule's
      incident).
1. `[R-MECH-MATRIX]` **The cross-ISO mechanism matrix is the single test ledger — check it before
    proposing a lever, update it in the session that tests one.** The matrix
    (SHARDED PER ISO since 2026-08-11: mechanism-level rows in
    `docs/codebase-site/data/mechanism-matrix.js`, each ISO's cell verdicts / fc / evidence /
    keeper+gates stamps in `docs/codebase-site/data/mechanism-matrix/<ISO>.js` — a lane edits
    ONLY its own ISO's shard; rendered at
    `docs/codebase-site/mechanism-matrix.html`; protocol, ISO-similarity analysis, per-ISO lever
    queues and glossary: `docs/mechanism-testing-matrix.md`) records, per mechanism × ISO ×
    lane (backcast keeper / forecast default), whether the mechanism is armed and its tested
    verdict (`K` keeper / `R` rejected / `I` inert / `G` governance-refused / `O` open /
    `U` untested / `·` n/a) with the evidence citation. Binding duties: (a) **handoff prompts
    that open a calibration or forecast session cite the matrix and the target ISO's lever
    queue**; the session picks its lever from the queue or states why it goes off-queue, and
    never re-tests a cell already adjudicated `R`/`I`/`G` without new evidence (the
    DO-NOT-REDO discipline). (b) **The session that tests a mechanism — probe, candidate, or
    keeper — updates that mechanism's cell (status + citation) in its own ISO's shard in the
    same session**, rejected
    outcomes included, alongside the rule-15 dashboard registration. (c) **A PR that adds a new
    solve-affecting mechanism adds its matrix row in the same PR** (base row + a cell line in
    every ISO shard — the one deliberately non-parallel edit) — a mechanism missing from
    the matrix is an unregistered tuning channel in spirit (rule 24). (d) Verdicts are strictly
    per-ISO (rule 25): a verdict in one ISO never fills another ISO's cell — transfer candidates
    enter the target ISO as `U`, and the target session derives its own parameters from its own
    market's data. When a keeper changes, the promoting session re-stamps its ISO's matrix shard
    (keeper id + open gates) and re-checks that ISO's column. Enforcement: CI
    (`.github/workflows/ci.yml`, `mechanism-matrix-guard` job → `scripts/check_mechanism_matrix.py`)
    validates matrix integrity and FAILS any PR that adds a `ScenarioConfig` field absent from the
    matrix (duty c); it WARNS on new run registrations or calibration CLI flags with no matrix
    touch (duty b). The `.claude/hooks/mechanism-matrix-reminder.sh` SessionStart hook surfaces
    these duties at the start of every session.

Rules 17–26 are the protective rules from `docs/model-legitimacy-audit-2026-07.md` §8, numbered
**16–25 there** — a doc reference to "audit rule N" maps to rule N+1 here. Mapping table, per-rule
amendment genealogy and the incident record: `docs/governance/rule-history.md`.

## LP Variable Layout (per ISO-year)

Flat column vector: P[g,t] | W[z,t] | S[z,t] | Chg[s,t] | Dis[s,t] | SOC[s,t] | Flow[l,t] | Slack[z,t] | Dump[z,t]
Total columns = T × (n_gen + 4×n_zones + 3×n_storage + n_links), T=8760

## Objective

min Σ mc[g,t]×P[g,t] + ε×(Chg+Dis) + dis_cost[s]×Dis + VOLL×Slack + dump_cost×Dump
Where mc = heat_rate × fuel_price + vom + emission_rate × carbon_price + nox_rate × nox_price + …
dis_cost = per-unit storage throughput adder (PS per-ISO calibrated; batteries ScenarioConfig.battery_dispatch_adder, default 0)
dump_cost = max(ε, -min(wind_mc, solar_mc) + ε) — prevents gaming of negative-MC production credits

## Key Constraints

- Energy balance (per zone, per hour): thermal + wind + solar + discharge - charge + net_flow + slack - dump = demand
- Generator bounds: pmin ≤ P[g,t] ≤ pmax × availability[g,t]
- Renewable bounds: 0 ≤ W/S ≤ cf × capacity
- Storage SOC: SOC[t] = SOC[t-1] + η_chg×Chg[t] - Dis[t]/η_dis, cyclic boundary
- Transmission: -TTC ≤ Flow ≤ TTC
- Capacity value is locational when `capacity_deliverability_limits` is on (default off): a zone whose deliverable accredited capacity already clears its published LDA/LRZ/locality/local-area requirement is RA-saturated and the marginal capacity payment there collapses.

## Capacity Evolution (per year, one-pass)

0. Confirmed exits (`apply_confirmed_exits`, GATED `confirmed_exits_enabled` default-on) → 1. Announced retirements (`apply_announced_retirements`) → 2. CCS retrofit screen (existing gas-CC — BEFORE economic retirements since W2-C: steps 2+3 are the joint retrofit-or-retire choice) → 3. Economic retirements (fuel-type-aware thresholds + reliability floor; this-year retrofits exempt) → 4. Known additions → 5. Economic new entry → 6. Reserve-margin adequacy backstop (GATED `reserve_margin_build_enabled`, default off) → 7. dispatch with RPS as an LP constraint (shadow price feeds next year's entry screen). Same step numbering as `model-methodology-spec.md` §5.1.

Mechanism detail is the spec's job (§5.2–§5.9) and the code's; what CLAUDE.md pins is which gate owns which step:

- **Step 0, confirmed exits** — `data.confirmed_retirements.load_confirmed_exits` over `data/raw/confirmed-retirements`, GATED `confirmed_exits_enabled` (default on), forecast-mode only. A row needs an enforceable public instrument (RTO deactivation acceptance, consent decree, statute, regulatory order, RMR end); this is **the ONLY exogenous fossil exit channel** and it **bypasses the reliability floor**. Hindcast information gate: a row applies only when `instrument_date` ≤ the vintage cutoff. (Spec §5.1–§5.2; `docs/handoffs/confirmed-retirement-plan-2026-07.md`.)
- **Step 1, announced retirements** — `apply_announced_retirements`, `load_announced_reversal_plants`, `forecast_fossil_retirement_economic` (default True ⇒ **for fossil this step is a default no-op**: the economic screen governs its phaseout), `EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS` (default 5) bounds honored non-fossil dates. (Spec §5.1.)
- **Step 2, CCS retrofit** — `ccs_retrofit_available_year`, `eac_price_gas_cc_ccs`, `ira_ccus_45q_last_year`, `ira_45q_credit_window_years`; ≥15 yr remaining life, 3 GW/yr/ISO cap, valued as the **incremental uplift over the best unabated state**, screened jointly with retirement. (Spec §5.6.)
- **Step 3, economic retirement** — screens the **attainable (pro-forma) inframarginal margin**, `Σ_t max(0, price − full variable cost, reserve price) × pmax × availability` (Potomac-SOM net revenue, `mc_cost` via `prior_results`): **never gross revenue, never realized dispatch**. Against FOM-only going-forward cost. Per-fuel thresholds are `ScenarioConfig` fields, not hardcoded, and apply to the **legacy** rule only (`retirement_rule="legacy"`; under the pipeline rule the decision is uniform and the per-fuel physics lives in `retirement_execution_lag_*`): coal=3yr, gas_ct=2yr, gas_cc=3yr; coal FOM multiplier 1.3×. *(Corrected 2026-08-02 by FFR-3B: this read "coal=1yr", but `scenarios.py` ships `retirement_years_coal: int = 3`, identified under rule 23 to the EIA-860 announced-to-deactivation capacity-weighted/≥300 MW median of 3 yr. Code is the source of truth.)* `screen_reserve_value_enabled` (default on) — the co-opt's own reserve duals under `ercot_thermal_as_endogenous`, else the ORDC scarcity adder; when present it is the **SOLE** thermal AS pricing (rule 19 `[R-ONE-MECH]`). Floor: `accredited_firm_capacity_mw` vs `peak × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)`, one requirement shared with the build backstop, `floor_retention_log` attribution. (Spec §5.2.)
- **Steps 4–5, additions and entry** — `load_planned_additions` (EIA-860 proposed pipeline, construction-committed statuses, forecast mode only). **RPS is not a force-build step** — it is an annual LP constraint whose dual is the REC price. (Spec §5.3–§5.4, §1.4.)
- **Storage entry** — an economics-based **value stack, not compound growth**: arbitrage net of cycling degradation **plus** RA capacity value, paid only where the per-ISO `MARKET_DESIGN` registry has a capacity market (energy-only ERCOT pays none). `STORAGE_TECH_BUILD_SHARE_CAP`, base-year fleet `storage_deployment` with all later growth endogenous; toggles `storage_capacity_value`, `storage_degradation`. (Spec §5.5.)
- **Locational deliverability** — `capacity_deliverability_limits`, GATED default off; published PJM CETO/CETL, MISO LRR/LCR/CIL, NYISO LCR/TSL, ISO-NE LSR/MCL, CAISO LCR/MIC crosswalked onto model zones. Structural mechanism (rule 1 `[R-STRUCT]`). In a backcast only the measured-seam-import half fires (CAISO MIC → WECC_import; the CAISO keeper enables it via `--capacity-deliverability-limits`, caiso-51); **the RA-saturation half remains unvalidated in any keeper**. (Spec §5.8; `docs/capacity-deliverability-wiring.md`.)

## Dispatch & Commitment (per year)

**P0 and P1 are the only two passes** (`runner.py`, `model/commitment.py`): **P0** base-cost (discover run lengths) → **P1** bid-cost (base + amortized startup markup, sets clearing prices). **P1 is THE main run**: the production/forecast path and what **every run is scored on**. Pure LP — no MIP. (Spec §1.6.)

**P2 is ARCHIVED — a legacy artifact kept intact as a last resort, never a calibration option.** The former third solve (`commitment_enabled` / `ercot_as_aware_commitment`) is hidden from the calibration CLI: its flags (`--commitment`, `--ercot-as-aware-commitment`, `--run-p2`, `--no-coal-p2`, `--persist-p2-state`, `--class-commitment-overrides`) error unless `--enable-legacy-p2` is passed (both `scripts/run_calibration_full.py` and `scripts/run_calibration.py`). **No keeper uses it; it is not part of any default or recommended configuration.** The machinery (`pipeline/commitment.py::run_commitment_pass`) stays in place for that path only. (Spec §1.6.)

**Three P1-native commitment bridges**, all applied as a `min_gen` floor detected from the base-cost **P0** run pattern and injected at the P0→P1 seam (`pipeline/solve.py::run_energy_solve`) — so the ISO keeps its commitment structure and is still scored on P1, and **none triggers a P2 pass**. They are ISO-exclusive (each gates on its own ISO) and share one detector, `model/commitment.py::caiso_ra_mustoffer_min_gen`:

- `caiso_ra_mustoffer` — RA must-offer, CAISO default-on.
- `ercot_gas_commitment_bridge` — default off, ERCOT-only, merchant gas-CC only (rule 19 `[R-ONE-MECH]`); `min_load_frac` = the measured committed-CC LSL/HSL cap-weighted p50, 0.574; D-2 id `gas_commitment_bridge`.
- `nyiso_gas_commitment_bridge` — default off, NYISO-only, merchant slow-start gas (CC_REGULAR + ST_GAS, eligibility by unit physics per rule 18 `[R-PHYSICS]`: min-down 4–12 h, $35–50/MW starts; the 1 h-min-down CT classes are never bridged). Two per-class `min_load_frac`s MEASURED from CAMPD unit conduct — NYISO publishes no 60-Day-DAM equivalent, so the ERCOT LSL/HSL identification is reconstructed via the WP-3 loading-when-on construction (`scripts/data/derive_campd_gas_commitment_params.py`): CC 0.523, ST_GAS 0.239. Adds the **minimum-run-duration** leg (`nyiso_gas_bridge_min_run`) — a detected P0 run shorter than the unit's min-run is extended and the extension floored at min-load, with the extended blocks defining the run pattern the gap bridges then scan. D-2 id `nyiso_gas_commitment_bridge`. It is the **replacement** for the h14-21 peak-window reliability-floor limbs (owner directive 2026-07-27), so it is armed WITH `iso_configs.NYISO_PEAK_WINDOW_FLOORS_OFF` applied via `reliability_floor_overrides`, never stacked on them.

Mechanism detail: spec §1.6. Per-limb floor overrides accept an optional fourth key segment selecting one `ramp_group` (`"<ZONE>:<CLASS>:<driver>:<ramp_group>"`, `_none` for the ungrouped step limbs) — needed wherever one (zone, class, driver) mixes an always-on base with a windowed ramp family.

The ERCOT offer-surface and negative-price variants (`ercot_offer_surface_lowcurve`, `ercot_offer_surface_lowcurve_floorscoped`, `wind_ptc_vintage_offers`, `negative_renewable_offers`) all stay **default-off** — probe-refuted, probe-adjudicated provably inert, or rule-25 `[R-ISO-SCOPE]`-refused. Adjudications, the trough/spread lane's frontier status, and the reasoning that **CLOSED the West/Panhandle topology split** (do not re-open it as a topology change) are in `docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10.

## Fleet Representation

ERCOT default is **CAMPD per-plant binning** (`use_campd_bins=True`): one LP unit per plant, each split into must-run / committed / economic / peaking tranches forming a rising offer curve (coal take-or-pay + PRB sigmoid passthrough). See `docs/binning-methodology.md`. Other ISOs / `use_campd_bins=False` use legacy equal-width heat-rate bins.

## Naming Conventions

- Python: snake_case. Functions: verb_noun (solve_dispatch, evolve_fleet, load_eia_profiles).
- Single-letter vars only in LP construction: t=hour, g=generator, z=zone, s=storage, with comment.
- Feature branches: phase-N/description. Commits: imperative present tense.

## Cloning & session data (partial clone + a declared data profile)

**The repo is cloned blobless, and each session hydrates only the `data/raw`
subtrees it needs.** The pack is 7.44 GiB and **7.37 GiB of that is live at the
tip of `main`** (measured 2026-08-13; only 82 MB is dead history), so a full
clone stalls through the egress proxy — that is the "Cloning the git_repository
source took longer than the allowed time" failure. **A history rewrite does not
fix it** (it would reclaim ~1.1%) and **neither does `--depth 1`** (a shallow
clone still transfers the whole tip tree). The fix is `--filter=blob:none` plus
sparse-checkout. Recipe, measurements and the three partial-clone traps:
`docs/fast-clone.md`. (Those figures are the 2026-08-13 measurement and are
**pre-prune**; the BLOAT-B corpus conversions below shrink what is live at tip
without touching pack size, since history is kept. BLOAT-B-2 alone took 361.8
MiB off tip. Re-measure before quoting a current number.)

- **Every handoff prompt declares its profile** on its own line —
  `DATA PROFILE: <code|shared|ercot|caiso|pjm|miso|nyiso|neiso|all>`. Omitted
  means `code`. A session hydrates with
  `python3 scripts/hydrate_data.py --profile <name>`, and may widen later at any
  time; hydration is incremental.
- **`code` is the default and is right for most sessions** — docs, governance,
  dashboard, code review, refactors, CI, matrix updates. Only a lane that runs
  `run_calibration_full.py` needs `data/raw`, and then only its own ISO's
  profile (rule 12 `[R-PARALLEL]` already makes concurrent invocations per-ISO).
- **Profiles are DERIVED, not enumerated** (`configs/data-profiles.yaml`): a
  `data/raw` child is attributed to an ISO by name token, else to `shared`, and
  per-ISO split directories (`lmp-data/MISO`, `storage-as-awards/CAISO`, …) are
  detected. A newly-added subtree is picked up with no table to maintain.
- **In a partial clone, never resolve a blob you do not intend to download** —
  any git read of a missing blob silently fetches it, so a stray
  `cat-file --batch-check` over `data/raw` pulls all 7.4 GB. Read trees only, and
  run read-side git calls under `GIT_NO_LAZY_FETCH=1` so a regression fails loudly.
- **Some corpus payloads are GITIGNORED, so hydrating a profile no longer
  materializes them — and the profile is that much smaller.** The corpus
  conversion class (`docs/bloat-removal-plan-2026-08.md` §4) untracks a corpus's
  bulk payload at tip while keeping its `README.md` + `SHA256SUMS.txt` tracked;
  history is never rewritten, so the bytes stay recoverable forever. **Every such
  corpus README carries the same three things: the verified source-URL table, the
  re-fetch command, and the pin sha with its
  `git restore --source=<pin> -- <path>` recovery command** — read the corpus
  README before concluding data is missing, and prefer restore-from-pin when you
  need the exact bytes rather than a fresh download. Converted so far:
  `pjm-energy-offers`, `caiso-public-bids`, `pjm-da-virtuals`, `pjm-zonal-lmp`,
  `ercot/SCED-CT`, `miso-energy-offers`, `pjm-binding-constraints`, and (BLOAT-B-2)
  `caiso-dam-outages/daily`, the publication PDFs under `ERCOT/` `MISO/` `NYISO/`
  `PJM-AS/`, and `NYISO/nyiso load reports *.zip`.

`.github/workflows/cleanup-large-blobs.yml` is safe to run as of its 2026-08-12
patch but **will not speed up clones** — it protects blobs live at tip, which are
exactly the 7.37 GiB. Standing NO-GO on rewriting for size:
`docs/FINDING-rewrite-prep-2026-08-11.md` §8.

## Git & Pushing (transport by PACK size — `git push` permitted for small packs)

**Rule: choose the push transport by the size of the PACK the push would send —
never by single-file size.** The remote rejects large **packs** with HTTP 413;
it is a pack-size limit, not a blob limit. Measured 2026-07-25 (PR #2878, the
caiso-119 registration): a **434,784-byte single-blob** dashboard-payload
commit pushed over `git push` with **no 413**, the remote blob sha
byte-identical to local. Both transports are live:

- **`git push` is PERMITTED** and is the correct transport for a commit whose
  pack is small — in particular the one class of file `push_files` cannot
  carry: a dashboard run payload (`frontend/data/backcast/runs/<id>.js`,
  ~400 KB–1 MB). It remains **NOT licensed** for a full bundle directory
  (`caiso119_base_A` alone is ~120 MB of parquet/npz) or for a divergent
  branch that would pack hundreds of MB — the original 413 rationale still
  holds there, and no measurement covers it.
- **`mcp__github__push_files` stays fully available and stays preferred for
  small multi-file commits** (atomic, server-side, no local git state, no
  pack negotiation at all). Its **~457 KB per-payload cap** is the hard
  reason it cannot carry a run payload — which is exactly when to use
  `git push` instead. A sidecar pushed without its payload is silently
  invisible in the Run Explorer; that cap is what stranded runs sidecar-only
  (see `docs/handoffs/dashboard-payload-push-gap-2026-07.md`).

Workflow:

1. **Start fresh on main — this is what keeps a pack small.** `git fetch
   origin main` then branch/rebase the work onto the latest `origin/main` so
   your commits carry *only* your own new objects, not a divergent base. A
   freshly-fetched base means the pack `git push` sends holds nothing but this
   session's objects — that, not any per-file property, is what keeps a push
   under the limit.
2. **Push every commit via one of the two transports** — one commit per
   logical change, **small commits** (a bundle's slim files + sidecar + run
   payload + bench in one commit, docs/code in another). A commit carrying a
   run payload goes over `git push`; small text-only commits may use either
   path. **If `git push` fails with HTTP 408/500, set
   `git config http.version HTTP/1.1` and retry BEFORE concluding anything
   about pack size** — the failure is HTTP/2 negotiation, reproduced on a
   32 KB five-object pack (six consecutive failures, then first-try success
   on HTTP/1.1; `fh-5-armk-completion-2026-08-13.md` §6). Falling back to
   `push_files` on this misdiagnosis strands any ≥300-line file (rule 27).
3. **The generated data files are rebuilt by the Pages deploy — committing them
   is preview-only.** The Pages deploy workflow
   (`.github/workflows/deploy-pages.yml`, restored 2026-07-14) regenerates
   `manifest.js` / `benchmark.js` / `completeness.js` from the committed sidecars
   at deploy time and publishes them, so a **registered run appears on the LIVE
   dashboard once the deploy runs** — you do not need to commit those files for
   the live site. The simplified deploy does NOT commit the refreshed files back
   to main, so the committed `frontend/data/backcast/` copies are used only by the
   local `file://` preview (the `bc-data.js` fallback) and may lag the sidecars;
   run `scripts/build_manifest.py` and commit them if you want that preview
   current — optional. Only the gitignored `docs/codebase-site/data/backcast/`
   stays generated-not-committed (built into the artifact at deploy).
4. **Verify after push (rule 27) — on BOTH transports.** Any push (`git push` or
   `push_files`) that touches a source file ≥300 lines is followed immediately by a blob
   verification (fetch the pushed file, compare line count + hash to local) before the next
   commit. Full-file rewrites of large existing files
   from regenerated response content are forbidden — push the exact local on-disk bytes, and
   for unavoidable piecewise moves append verified chunks, never placeholder overwrites.

## GitHub Actions — never offload work to CI (this is a PRIVATE repo; runner minutes are billed)

**Do NOT create per-task GitHub Actions workflows, and do NOT run LP solves,
data intakes, patch-applies, or other one-shot chores on GitHub-hosted
runners.** This repo is private, so every runner-minute is billed to the owner;
the historical pattern of pushing a `*-solve-register.yml` / `apply-*.yml`
workflow per calibration run cost real money and is banned.

- **Run solves in the Claude session.** `scripts/run_calibration_full.py` runs
  in this environment — invoke it here (years sequential within a run; separate
  invocations concurrent per rule 12). If the session lacks RAM/time for a
  solve, say so and ask the owner how to proceed — do **not** silently spin up a
  CI job to do it.
- **No new `.github/workflows/*.yml` for a task.** A workflow is justified only
  as durable, reusable infrastructure (CI/lint on PRs, the Pages deploy, a
  parameterized data-fetch pipeline) — never as a one-off keyed to the branch
  you happen to be on. When in doubt, do the work in-session and push the result
  via `mcp__github__push_files` or a small-pack `git push` (per Git & Pushing
  above) — not a CI job.
- **Scheduled (`cron`) workflows spend money with nobody watching.** Do not add
  one without explicit owner sign-off, and prefer `workflow_dispatch`-only.

## Testing Pattern

Always test with trivial cases first: 1 gen, 1 zone, 24 hours. Then scale up.
Suite layout, the two run lanes, the marker taxonomy, the shared helper layer and
the two golden systems: `docs/testing.md`.

## Reference Docs (in repo)

- `docs/README.md` — the docs index; start here when you don't know which doc owns a topic
- `model-methodology-spec.md` — LP formulation, commitment, fleet/offer curves, capacity evolution, outage modelling, scenario architecture (THE SPEC)
- `docs/codebase/` — the living per-area code reference (01-architecture … 08-config-reference); the current per-module inventory behind this file's elevator-view tree
- `docs/governance/rule-history.md` — rule numbering (stable `[R-*]` IDs, the audit N↔N+1 map), per-rule amendment genealogy, and the incident record behind rule 27
- `market-sim-build-plan.md` — phase plan, extraction manifest, directory structure
- `docs/refactor-consolidation-plan-2026-07.md` + `docs/refactor-consolidation-prompt-pack-2026-07.md` — the refactor/organization program: binding constraints (§1), workstreams, the byte-identity verification protocol (§8), owner-decision register (§9), and the per-wave session prompts
- `docs/testing.md` — the `tests/` directory layout, run lanes, marker taxonomy, shared helpers, golden systems
- `docs/binning-methodology.md` — CAMPD per-plant binning & tranche offer curves (ERCOT default)
- `docs/parameter-citations.md` — every numeric input traced to a primary source
- `docs/multi-iso/` — protocol & status for adding ISOs beyond ERCOT
- `docs/calibration-log.md` (frozen archive ≤2026-07-19) + `docs/calibration-log/<iso>.md` per-ISO continuations (`governance.md` for cross-ISO), `docs/calibration-session-log.md` — calibration history. Keeper promotions are per-ISO lanes: edit `frontend/data/backcast/keepers/<ISO>.json` + rebuild `status/<ISO>.js` (`build_status.py --iso`) — never another ISO's files (see `frontend/data/backcast/keepers/README.md`); when the promoted ISO holds a `complete` marker, the same session also re-keys its `calibration-complete.json` entry with a determination re-verification (rule 22, D-5(b))
- `docs/forecast-development-plan-2026-07.md` — THE forecast program (Forecast Finalization Program): tier ladder, lanes/waves, prompt pack, rubric charter. All prior forecast plans are superseded as coordination docs by it (its §9 migration ledger).
- **Code is the source of truth.** When docs and code disagree, fix the docs (run `/sync-docs`). When the methodology is genuinely ambiguous, the spec wins.
