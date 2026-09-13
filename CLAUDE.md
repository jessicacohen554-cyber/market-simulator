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

LP-based electricity market dispatch simulator. Forecasting model (2026–2050) with a historical-backcast mode for calibration. Multi-ISO: seven ISOs registered in `config/iso_configs.py` — ERCOT (7 zones, 6 carry load; the calibrated reference), CAISO (3 zones + WECC import node), PJM (8 zones), MISO (6 zones), NYISO (5 zones), NEISO (4 zones + HQ import node), SPP (2 zones) — sharing one ISO-agnostic LP. Hourly 8760 dispatch, parameterized scenario system.

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
  pipeline/  → shared per-year solve core (spec, kwargs, prior, backcast_config, commitment, solve)
  ensemble / matrix / uncertainty / structural_prior → ensemble & forecast-uncertainty layer
  runner.py  → main orchestrator (P0→P1 solve loop, year evolution)
  (full, current per-module inventory: docs/codebase/01-architecture.md — kept in sync with the code; this tree is the elevator view)
tests/       → pytest, one file per module
scripts/     → core entry points & standing tooling ONLY (calibration/hindcast/forecast runners, scoring, dashboard, governance) — see scripts/README.md
  data/      → data fetching & processing (fetch_*, curate_*, derive_*, per-source build_*) — not core engine
  lib/       → shared helpers; probes/ → only the probe scripts live code still imports or names
               (scripts/archive/ and the record-only probes were DELETED 2026-09-05, owner instruction:
               superseded per-run scripts are deleted, never archived; git history is the record)
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

1. `[R-STRUCT]` **Right market structure first, offer-curve tuning second — backcast match is NOT the objective.** The goal is a model whose *mechanisms* mirror the real market (reserve withholding/co-optimization, scarcity pricing, congestion, commitment, fuel/passthrough physics). Build the correct structure, *then* tune offer curves to calibrate the level. **Never judge a structurally-correct mechanism by whether it improves the backcast fit, and never reject/revert it because the residual didn't move** — a real market behaviour stays in even if it makes the fit worse (then fix the actual root cause per #11). Conversely, never reach the right number through a mechanism that isn't real (a fitted adder, a load proxy, a haircut tuned to the residual). A run is a "keeper" because it is the most structurally faithful, not because it has the lowest MAE; a more-accurate run that is missing real structure is **not** a keeper. **AMENDED 2026-09-05 (owner ruling) — THE REGISTERED OFFER-CURVE BAND MULTIPLIERS ARE AN AUTHORIZED PRICE-TUNING CHANNEL, and tuning them on price is NOT the forbidden "fitted adder".** The owner ruled: *"We should definitely be able to fit the fossil offer curves to the price… as long as it's the same config across the 3 years it is fine to do… The offer curve multipliers are meant to allow us to tune on price & adjust merit order."* This carve-out is **narrow and conditioned**, and every condition binds: (a) the channel is the `offer_curve_by_group` band multipliers ONLY (`committed` / `econ_low` / `econ_high` / `peak`) — never `phys_*` (measured physics), never the structural shares (`econ_low_share`, `pct_peaking`), and never a new adder, offset, haircut or proxy, all of which remain forbidden; (b) **ONE config across EVERY scored year** — a per-year value is per-year fitting and is still refused; (c) the value is set **ex ante and declared in the PREREG before the solve**, and **never swept against the gates** — selecting a factor by which one makes a criterion pass is the fitted-mechanism selection this rule exists to forbid, and it stays forbidden; (d) merit-order adjustment across classes is an INTENDED effect, not a defect; (e) the run declares the channel in its attestation's `authorized_price_tuning` block (C6 FAILS without it) and carries the value as a **free parameter in the DOF ledger** (rule 21 `[R-DOF]`), identified by the ruling rather than by a measured source. **The first half of this rule is UNTOUCHED**: structure still comes first, a structurally-correct mechanism is still never judged by the residual, and a level-tuned run that is missing real structure is still not a keeper. What the amendment changes is only that a declared, year-invariant, un-swept multiplier is no longer disqualifying *in itself*. Genealogy: `docs/governance/rule-history.md` §11.
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
1. `[R-MEASURED]` **Measured data is allowed only as a *reproducible physical/market input*, never as the *answer* — no pinning the backcast to actuals.** Real measured data may be used when it is grounded in physics or market design **and** enters as a formulaic input that would regenerate for a future year and respond to changed conditions in a forecast — e.g. unit outage windows (a physical availability event), delivered fuel prices, plant-specific CEMS emission rates, a measured ancillary-service power reservation. The admissibility test is: **could this same quantity be produced for a forward year from forward drivers, and would it respond to changed conditions?** If yes, it is a legitimate input *even in backcast mode*. What is **forbidden** is feeding a measured *outcome* back in to force the backcast to match: pinning a unit to its observed CEMS generation, adding an offset/haircut/adder tuned to the price or volume residual, or rescaling an input so the model's *output* lands on the actuals. *(AMENDED 2026-09-05, owner ruling — ONE EXCEPTION, and only one: the registered `offer_curve_by_group` band multipliers are an authorized price-tuning channel under rule 1 `[R-STRUCT]`'s carve-out, subject to every condition (a)–(e) there. The exception is for the OFFER CURVE and nothing else — an offset, haircut, adder, load proxy, or a rescaled measured input remains forbidden however it is motivated, and pinning an output to an actual remains forbidden absolutely. A multiplier SWEPT against the gates is not in the exception: it is per-criterion selection, which condition (c) refuses.)* Those have no forward analogue — the dispatch being validated is then not the dispatch being forecast, so the "fit" measures plumbing, not skill. A measured input that fails the test may exist only as an explicitly-labelled, default-**off** diagnostic probe; it must never be enabled in a keeper or quoted as evidence of forecast skill. (This sharpens #1 and #11; the concrete forecast-vs-backcast line is methodology spec §1.7, and the live overlay inventory is `docs/backcast-measured-data-audit-2026-06.md`.)
1. `[R-ACCURATE]` **Prefer accurate/measured data over estimates whenever it's available — never revert to an estimate just because it fits the backcast better.** If swapping a hand estimate for real data (a measured TTC/GTC limit, metered load, actual outages, real fuel prices, etc.) makes the backcast *worse*, that is a signal that **something else in the model is miscalibrated** and the estimate was silently compensating for it. Treat the worse fit as a discovered bug: keep the accurate input, find and fix the real root cause (offer curves, must-run, passthrough sigmoids, fleet/zone assignment, etc.). Do **not** bury the error back inside an inaccurate input. The *only* exceptions — where an estimate may be kept — are when the accurate data is genuinely **misaligned to our representation** so that using it literally would make overall results *less* reflective of reality, e.g.: the data is defined on a different boundary than our zones (a single GTC that is one of several parallel paths our reduced network collapses into one link), a different time/area aggregation, or units/sign conventions that don't map. In those cases, document the misalignment explicitly in a comment and prefer a *reconciled* version of the real data over a pure guess. When in doubt, use the real data and open the root-cause investigation.
1. `[R-DASHBOARD]` **Every completed backcast run goes on the dashboard — results live there, not in chat.** The moment a calibration run finishes (keeper *or* rejected probe), register it on the backcast results dashboard and commit+push it **in the same session it was produced** — use the `calibration-report` skill / `scripts/dashboard_add_run.py`, then `build_manifest.py`. The dashboard is the codebase-site pages — `docs/codebase-site/backcast-runs.html` (run explorer, `#iso=<ISO>&run=<id>`) and `docs/codebase-site/calibration-status.html` (all-ISO keeper summary, `#iso=<ISO>`); the old root `backcast-results.html` is a static redirect stub, never regenerated. The committed per-run files (`results/calibration/<name>/` bundle + `frontend/data/backcast/registry/<id>.json` + `runs/<id>.js` + changed `bench/`) are the deliverable; the Pages deploy workflow rebuilds `manifest.js`/`benchmark.js`/`completeness.js` from the sidecars at deploy time, so a registered run shows on the LIVE dashboard once the deploy runs (committing those generated files is optional, local-`file://`-preview only — see Git & Pushing §3). A run is **not "done" until its bundle and dashboard files are committed and pushed** — do not just narrate metrics in chat and move on. **Retention is KEEPER-ONLY** (owner instruction 2026-09-05, executed by session ercot-248 — `docs/calibration-log/ercot.md` "## ercot-248 — 2026-09-05"; verbatim: *"Combine the ERCOT calibrated keeper config into one run for the run explorer html page so it should combine the 2023 config that is calibrated plus the 2024/2025 config into one run then remove all the others that aren't that keeper so it's just showing one run. Also prune all the other non keeper runs from there so just show the keeper for each ISO for now."*), which SUPERSEDES the former top-15-per-ISO age cap and its PJM `pjm N <keyword>` labels. Each ISO's dashboard and `results/calibration/` carry **only that ISO's designated keeper run(s)** — a partitioned keeper's several configs included, whether composed into one registered run or kept as the per-config runs the ISO's keeper shard names — plus any bundle still referenced by a `results/regression-goldens/*/manifest.json` capture record or by the parity allowlist (`check_registry_payload_parity.KEEP_REQUIRED_UNMAPPED_BUNDLES`); every other run is pruned through `scripts/prune_iso_runs.py` — **at the PROMOTION that supersedes it, in that session**, since rule 35 `[R-PROMOTE]` (a) replaced this rule's original "at the next registration" timing (that deferral is what let 47 runs accumulate against 7 keepers by 2026-09-12). Registration is otherwise unchanged: a rejected probe still registers the moment it finishes, exactly as this rule requires, and is pruned once superseded — **git history is the record**, the same delete-not-archive discipline the Architecture tree states for superseded per-run scripts (deleted, never archived). Lead with the dashboard result; keep the prose minimal. KEEPER bundles additionally commit their `hourly/` sidecars (`class_hourly_<year>.parquet` + `system_<year>.parquet`, written by every solve since 2026-07-19; plus `reserve_family_<year>.parquet` since 2026-08-03 — the per-family reserve balance-row dual, requirement, held MW and ORDC shortfall, which is the ONLY artifact in which a locational reserve family's binding is observable, since `system`'s `reserve_price` is the cross-family SUM broadcast identically to every zone) so later diagnostic sessions read the keeper's class-dispatch/price hourlies instead of replaying the solve — a keeper replay is justified only for unit-level questions. **Forecast-family runs** (T1-F / T1-X / T1-H / CES-POC hindcasts & full-horizon summaries) go on the SEPARATE forecast dashboard — `docs/codebase-site/forecast-runs.html` (run explorer, `#iso=<ISO>&run=<id>`) + `forecast-status.html` (per-ISO §2.1b gate board) over the `frontend/data/forecast/` namespace, registered via the SINGLE `scripts/register_forecast_run.py` path. The namespace `registry/<id>.json` + `runs/<id>.js` + `manifest.js` + `program-status.js` are GENERATED (gitignored — the Pages deploy is their single writer; `--reindex` regenerates them locally for the `file://` preview) and fully derived from the COMMITTED inputs: the hindcast sidecars + the FF-2D verdict snapshot `frontend/data/forecast/ff-verdicts.json` + the board seed `program-status.json`. `--reindex` bakes the FF-2D rubric verdicts and doubles as the stdlib deploy assembly (`deploy-pages.yml` runs `--reindex --site-dir _site`). NEVER the backcast registry — the backcast CI gates stay blind to the forecast namespace (forecast plan §7.5).
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
    produced (probe, candidate, or keeper).* *Cross-reference (owner ruling R-AY, 2026-09-06,
    Model Audit & Release-Finalization Program, card "DOF / C6" — "Count them in the DOF ledger,
    C6 passes under the declaration"): an `offer_curve_by_group` band multiplier tuned on price
    through the rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` authorized channel IS a ledgered free
    parameter whose identification source is the ruling itself — "price residual, authorized
    channel (rules 1/13 amendment 2026-09-05)" — not a measured input; it is reported at full
    magnitude on the determination basis; and its presence does NOT by itself make the residual
    it closes an "open root-cause issue" under this rule, while every OTHER tuned value still
    does and no gate moves. Genealogy: `docs/governance/rule-history.md` §13.*
1. `[R-C3C]` **A LONE C3c failure is an AUTO-LEDGERED caveat that does NOT downgrade the
    determination, in every ISO and every year.** *(Owner, 2026-08-06; extended to every year
    2026-08-09; non-downgrading since 2026-08-17. This rule occupies the ordinal formerly held by
    `[R-HOLDOUT]`, which was REMOVED 2026-09-09 — see the coda below and
    `docs/governance/rule-history.md` §18. The ordinal does not move; only the ID changed, and a
    doc reference to "rule 22" still lands here.)*
    Since rubric v3.3 (owner, 2026-08-17, verbatim: *"NYISO should be declared calibrated. C3c is
    an acceptable miss and shouldn't change a declaration from calibrated to calibrated with
    caveats because it's a known model limitation that's been ledgered"*) an otherwise-clean run
    carrying a ledgered C3c reads **`CALIBRATED`**, with the caveat reported on its determination
    basis. When C3c (price tail / scarcity, RT hourly) is the **only** failing criterion and the
    governance gate passes, `calibration_verdict.py::_apply_c3c_standing_rule` reclassifies it to
    a CAVEAT (`ACCEPTED MODEL-CLASS LIMITATION`) instead of failing the run to `NOT-YET`. It
    **cannot become a general escape hatch**, and the guards that stop it are unchanged:
    (a) **lone failure only** — if any other criterion fails, the rule stays silent and *every*
    failure stands, C3c's included. This is the real guard: it fires only on a model that is
    otherwise clean, so it can never mask a second defect; (b) **governance must PASS** — a
    failing or unattested C6 blocks it; (c) **supporting tier only, fail-closed** — it classifies
    `model-class`, which the v3.0 guard admits only for a SUPPORTING-tier criterion, so it can
    never reach load-bearing (C1/C2/C3a/C3b) or protective (C6/C8); (d) it is **never a PASS** —
    C3c reads CAVEAT, never PASS, so `grade_summary.target_grade` never absorbs it; the miss is
    reported at full magnitude and named on the determination basis even of a `CALIBRATED` run;
    it is still listed in `caveats.ledgered`; and it still spends the single ledgerable slot.
    The budgets are checked FIRST and are untouched: >1 ledgered or >0 protective caveats is
    still `NOT-YET`, and every OTHER caveat route — commercial-band misses, protective caveats,
    unscored criteria, data-blocked years — still downgrades. A run reads `CALIBRATED` only when
    a ledgered C3c is its SINGLE blemish.
    **The v3.6 out-of-training limb SURVIVES the holdout removal.** On a year outside 2023–2025
    the lone-failure condition of guard (a) is dropped, so C3c reads CAVEAT there whatever else
    that year does (owner, 2026-09-05: *"c3c should be an accepted caveat on all holdout years"*).
    Guards (b)–(d) still bind. This limb reads `scripts/lib/holdout_policy.tier_for_year`, which
    **survives as a PURE YEAR CLASSIFIER carrying no authorization meaning** — it answers "is this
    year inside 2023–2025", nothing more. Measured at the removal over all 15 registered runs
    carrying an out-of-training year: **0 determination flips** either way.
    **Why "lone" is measured over `CRITERIA` membership** (rubric v3.2): it formerly counted every
    scored record, including REPORTED-ONLY streams the rubric has demoted out of the determination
    (C5a `co2`, removed at v2.9), so a `co2` FAIL silenced the rule even though co2 contributes no
    status, no caveat budget and no reason line.

    **CODA — `[R-HOLDOUT]` IS REMOVED (owner instruction 2026-09-09: "Remove the holdout year
    rule").** The three-tier train / validation / locked-test regime and **every gate that
    enforced it** are gone: the `complete` / `final` markers as spend authorizations, the
    `holdout-freeze.json` spend freeze, the `--holdout-authorized` CLI flag, the
    `run_calibration_full` year gate, the `dashboard_add_run` registration marker gate (R-AZ), the
    D-6 quarantine diagnostic, the `audit_keepers` M1 marker re-key check, and the CI
    `quarantine-gates` job. **Any year may now be solved, scored and registered with no
    authorization, no marker and no one-shot.** What that costs is stated rather than hidden:
    there is no longer a certified out-of-sample number anywhere in this program, because no year
    is protected from being iterated against. Runs on any year are model-SELECTION evidence, and
    **a skill claim built on a year that has been tuned against is not a skill claim** — say what
    a number is when quoting it. `calibration-complete.json` SURVIVES for the two jobs it does
    that are not authorization: designating each ISO's current keeper, and feeding the forecast
    program's gate (a). Genealogy, and the full text of the removed rule:
    `docs/governance/rule-history.md` §18.
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

1. `[R-SCREEN]` **Screen a new config on ONE year before spending the full span — and screen it on
    what the mechanism DOES, never on whether the residual moved.** *(Owner rule, 2026-09-05: "only
    run in calibrated years thru new configs first … instead of wasting runs on 3 full years before
    we've addressed whether config actually solves the issue".)* A 3-year CAISO/PJM/MISO/NYISO/NEISO
    replay is ~35–70 min of LP **per arm**, and an A/B spends two of them. The order is now:
    - **(0) Zero-LP phase 0 first, wherever one exists.** An on-recipe `fleet_only` rebuild, an
      offer-array delta, a footprint census or a committed-sidecar reconstruction costs ~90 s and
      kills more arms than any solve. An arm that has a computable pre-solve gate does not reach a
      solve until that gate passes.
    - **(1) A SCREEN solve on ONE year.** The screen year is **named in the PRECOMMIT before the
      screen runs**, and it is the year the mechanism's **own measured footprint is largest**
      (from step 0) — **never** the year with the biggest residual, which would make the choice a
      residual-driven one. A control for the same single year is screened alongside it when
      G-CTRL needs one.
    - **(2) The full span only if the screen clears its pre-registered gate**, as one
      `--year 2023 2024 2025` invocation and ONE bundle. Rule 16 `[R-ALLYEARS]` is untouched: the
      screen bundle is a **throwaway diagnostic probe** — never registered on the dashboard, never
      a keeper, never quoted as a keeper number, and its year is re-solved inside the full bundle.

    **The screen gate is STRUCTURAL and it is a STOP gate only.** It asks whether the mechanism
    does what its own arithmetic says it does — the dispatch response has the direction and order
    of magnitude the pre-solve delta implies; the footprint is confined to the rows the mechanism
    claims; the identity it asserts holds; no non-target load-bearing criterion flips PASS → FAIL.
    It **may kill an arm; it may never promote one**, it never contributes to a determination, and
    it is **never gated on the target residual** (a screen that reads "did C3a improve" is exactly
    the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year at a time).
    A screen that kills an arm is reported as the session's result and the remaining years are
    never spent.

    **Where it does not apply:** a mechanism measured INERT in the candidate screen year (screen it
    where it is live, or go straight to the full span — G-CTRL form 2's inert-year logic already
    depends on that); and a year-scoped mechanism whose object only exists in one year, which is
    the screen and the full span at once.

    **(b) NO CONTROL SOLVES. The incumbent keeper's COMMITTED bundle IS the control** *(owner rule,
    2026-09-05: "stop doing control solves … just use the last keeper as the control")*. G-CTRL
    **form 4** — differencing the arm against the keeper's committed numbers — is the DEFAULT, and
    a control solve is never spent to establish HEAD drift. The question form 4 was being voided
    over ("solve-path files changed since the keeper's `git_sha`") is a **code** question, so it is
    answered with a **code-level drift audit, `G-DRIFT`**, at zero LP cost:

    > `git diff <keeper git_sha> HEAD -- src/market_sim scripts/run_calibration.py
    > scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`,
    > and classify **every** changed hunk on the backcast path as INERT for this ISO with its
    > reason cited — forecast-only path (capacity evolution / capacity market, which a
    > `mode="backcast"` run never enters), another ISO's branch, a `ScenarioConfig` flag that is
    > default-off AND absent from the keeper's recipe, a per-ISO artifact this ISO does not have,
    > or pure timing/diagnostics accounting — or as **LIVE**.

    **All hunks INERT ⇒ form 4 is valid and the keeper is the control.** A **LIVE** hunk is the
    only thing that earns a control solve, and then only for the years the screen needs (clause a).
    G-DRIFT is *stronger* than a control solve for this question, not weaker: a control solve shows
    that two numbers differ, while the audit says which line did it — and it costs seconds. The
    audit is recorded in the PRECOMMIT (or its addendum) before the arm is solved, so it cannot be
    written to fit the result. A "files changed, therefore void" heuristic with no audit behind it
    is not a reason to spend an LP.

    **(c) DELETE BEFORE MERGE — which means KEEP IT OUT OF `main`, NOT erase it from disk.
    SUBORDINATE TO RULE 31 `[R-RETAIN]`: nothing is removed from local disk until the owner has
    ruled on promotion.** A screen bundle, and any control bundle a screen earns under
    (b)'s LIVE-hunk case, must not be committed or merged *(owner
    ruling R-AV, audit-program director sitting 2026-09-05, verbatim: "Delete before merge";
    executed by Y-13, `docs/handoffs/FINDING-y13-ci-plumbing-2026-09-05.md`)*. The PRECOMMIT /
    FINDING doc carries **every number the session will ever cite** from such a bundle — the
    gate table with its values, the control differencing, the verdict — so the record is the
    doc, never the parquet, and git history is the record for the bytes exactly as rule 15
    `[R-DASHBOARD]` already says of pruned runs. The enforcement is
    `scripts/check_registry_payload_parity.py`'s bundle-retention sweep (Class-E point 4,
    `frontend/data/backcast/keepers/README.md`): **an unregistered bundle dir is a gate RED, not
    an allowlist candidate** — `KEEP_REQUIRED_UNMAPPED_BUNDLES` is not the route for a screen or
    a control, and neither is registering it (clause (2) above: a screen bundle is never
    registered). This resolves the collision the v31 second coda recorded (`da99f34b`): a lane
    that obeyed rule 29 exactly ("never registered on the dashboard") turned the parity gate red
    *by obeying it*, because the bundle was committed and outlived its PR. The two duties compose
    only when the bundle does not reach `main` at all — **and `.gitignore` achieves that on its
    own.** *(AMENDED 2026-09-07, owner instruction — the ercot-255 incident. This clause said
    "deleted from `results/calibration/`", and a lane read it as `rm -rf` and destroyed four
    solved bundles that were ALREADY gitignored, i.e. already incapable of reaching `main` or
    turning the gate red; when the owner asked to promote the result an hour later it cost
    ~50 min of re-solves that should have been zero. The requirement was always about the
    REPOSITORY, never the working tree. Gitignoring the bundle family discharges this clause in
    full. See rule 31 `[R-RETAIN]`; genealogy `docs/governance/rule-history.md` §16.)*

1. `[R-TOUCHPOINT-FOLD]` **A touchpoint is the keeper, on another year — publish it that way, never
    as a separate run to click into.** *(Owner ruling 2026-09-05, verbatim: "the runs should all be
    combined with the keeper in html not separate runs… like it's the same config I don't need to
    click into multiple things to see the results".)* A held-out-year replay IS the
    designated keeper's frozen recipe replayed on a held-out year — same config, different year —
    so splitting it onto its own dashboard card makes a reader open two pages to read one
    configuration. Every touchpoint session owes three things, in the session that produces it:
    - **(a) STAMP IT TO THE KEEPER.** Run `scripts/stamp_touchpoint_holdout.py --run-id <touchpoint>
      --keeper-id <keeper>` so the sidecar carries `holdout.keeper`. That one field is what folds
      the run: the Run Explorer hides it from the run list, offers its years in the **keeper's**
      year selector, and renders every folded year **exactly as it renders a training year — an
      ordinary year column in the keeper's Report, with no separate panel, no optgroup split, no
      tier suffix and no per-year badge.** A deep link to a folded id still resolves — it opens the
      keeper on that year — so no URL breaks. An unstamped touchpoint is a second card for the same
      config, which is the defect this rule names. *(AMENDED 2026-09-06, owner instruction, verbatim:
      "the formatting on the html dashboard for holdout years shouldn't be any different than the 3
      training years, it should show the results in the report view on run explorer and does not
      need a special designation." This clause previously MANDATED "columns of ONE combined
      **Validation Touchpoints** panel … beside the in-sample column"; that panel, the year-selector
      optgroup split and tier suffix, and the "<year> is a held-out year" provenance banner are all
      **DELETED, not hidden** (rule 26 `[R-DELETE]` — a dead render path is a re-armable answer),
      and the Report's year set is now `selectableYears()` rather than `runYears()`. **DO NOT
      "restore" the panel as a regression fix.** What is UNCHANGED: the fold itself, the stamp, the
      deep-link redirect. Rule 30(c) is untouched and this changes no
      determination: it is presentation only, no scorer path was modified, and every keeper
      re-scores byte-identically. Executed by session neiso-103; genealogy:
      `docs/governance/rule-history.md` §14.)* *(AMENDED AGAIN the SAME DAY, owner instruction,
      verbatim: "Delete the stupid per year determination from the run explorer I do not need
      narrative from you in my results viewing ANYWHERE I just want the scores and charts and make
      it so every iso with holdout years run has them SHOW up in the report." **THE RUN EXPLORER'S
      REPORT IS SCORES AND CHARTS ONLY.** The morning's amendment had kept ONE designation here —
      the former rule 22's tier caveat as a footnote — and that footnote is now **DELETED too**, along with
      every other prose panel in the results view: the **run-definition** panel (whose registry text
      had itself become the per-year determination essay the instruction names — "2023 = the
      CARVE-OUT config … DETERMINATION CALIBRATED"), the **zero-forcing ablation twin** panel and
      its market story (a twin rule 20 `[R-DOF]` stopped requiring on 2026-07-14, carried by no
      registered run), and the **auto-generated diagnostics** findings. Deleted, not hidden
      (rule 26 `[R-DELETE]`), render path and all — **DO NOT "restore" any of them as a regression
      fix.** The run's identity (id · date · keeper pill) moves to the page sub-header, where it
      serves every view. **Rule 22's substance is UNCHANGED and now rests entirely on (b)'s
      surface**: the Calibration Status page's per-year table carries the Tier column and the
      "reported, not gating" line, so a validation number still never reads as a certified
      out-of-sample skill number. Nothing scored moves — the browser computes no verdict, grade,
      caveat budget or determination, and every deleted block was display prose over data that
      still lives in the committed sidecar or in `scripts/calibration_verdict.py`. The instruction's
      second half is a RESTATEMENT of the fold, not a new duty: the fold now also treats a
      **dangling** `holdout.keeper` stamp — one naming a keeper since pruned under rule 15's
      keeper-only retention — as unstamped, so a promotion can no longer silently drop an ISO's
      held-out years off its report. Guard: `tests/scoring/test_holdout_render_parity.py`.
      Genealogy: `docs/governance/rule-history.md` §15.)*
    - **(b) PUT IT ON THE CALIBRATION STATUS PAGE.** `scripts/build_status.py --iso <ISO>` derives
      the **holdout ladder** (one row per held-out year, scored per year) from the registry
      automatically — so the duty is to *rebuild and commit the status part*, never to hand-author
      a block that would go stale the moment a rung is re-spent. Per-year is the load-bearing
      detail: a multi-year touchpoint bundle carries ONE run-level determination that can hide a
      rung which passed on its own (NEISO 2020+2021 reads NOT-YET as a bundle; 2021 alone is
      CALIBRATED). Where the two rungs of a bundle diverge, the sidecar also carries a `perYear`
      block so the ladder says which year did what. **This clause is UNAFFECTED by the (a)
      amendment**: the de-designation is the Run Explorer's Report view only — the status page's
      holdout ladder is per-year by design, is a different surface, and stays.
    - **(c) A HELD-OUT YEAR NEVER DOWNGRADES THE ISO.** *(Owner ruling 2026-09-05, verbatim: "An
      iso can stay calibrated even if it degrades on holdout years".)* The ISO's calibration
      determination is the **train-tier (2023–2025) verdict** and nothing else. A validation-tier
      score is iterable model-SELECTION evidence and cannot be quoted as a certified skill
      number, so it cannot certify and it cannot decertify. (Since `[R-HOLDOUT]` was removed
      2026-09-09 that is true of EVERY year, not only held-out ones — no year is protected
      from being iterated against any more, so no year certifies. Rule 22's ordinal now
      carries `[R-C3C]`.) A degraded rung is REPORTED — on the
      keeper's panel, on the status card, and in the session's assessment doc — and the ISO's
      headline is untouched. Both surfaces state this in place rather than leaving a reader to
      infer that a NOT-YET rung beside a CALIBRATED headline is a contradiction.

    The companion scorer change is rubric **v3.6** (owner, same sitting, verbatim: *"c3c should be
    an accepted caveat on all holdout years"*): on an out-of-training year the C3c standing rule's
    **lone-failure condition is dropped**, so C3c reads CAVEAT there whatever else that year does.
    Every other guard is untouched — governance must still pass, supporting-tier only, never a
    PASS, both caveat budgets checked first — and in-training years keep the lone-failure guard,
    now measured over what is still failing after the holdout reclassification. Rationale and the
    measured no-op effect over every registered run: `scripts/calibration_verdict.py` header, v3.6.


1. `[R-RETAIN]` **NEVER DELETE A SOLVE'S RESULTS UNTIL THE OWNER HAS DECIDED ON PROMOTION.**
    *(Owner instruction 2026-09-07, verbatim: "Do not delete results until I've decided on
    promotion make it a rule". The incident: session ercot-255 solved a 2025 screen arm, its
    control, the 2023–2025 full span and a 2021 re-test, wrote them up, judged the mechanism
    not-promotable **on its own reading**, and `rm -rf`'d all four under rule 29 `[R-SCREEN]`
    clause (c). The owner then ruled the opposite — promote it — and the artifacts a dashboard
    run needs were gone, so the promotion cost a full re-solve of every year. Genealogy:
    `docs/governance/rule-history.md` §16.)*
    - **The bar is the OWNER'S decision, not the session's.** A session may *recommend* against
      promotion; it may never act on that recommendation by destroying the evidence. "Not a
      keeper in my judgement" is a sentence in the RESULT, never a licence to delete. The owner
      routinely promotes what a session declined to — that is what a promotion decision **is**.
    - **What discharges the delete-before-merge duties is `.gitignore`, not `rm`.** Rule 29
      `[R-SCREEN]` (c) and rule 15 `[R-DASHBOARD]`'s keeper-only retention both govern **what
      reaches `main` and what the dashboard shows** — neither has ever required erasing a
      working-tree file. Add the bundle family to `.gitignore` the moment it is written; the
      parity gate (`check_registry_payload_parity.py`) only ever sees committed dirs, so an
      ignored bundle can sit on local disk indefinitely without turning anything red.
    - **Delete only on one of two triggers**: (i) the owner has ruled on promotion and the
      bundle is not needed — a superseded, pruned or declined run may then be removed, and git
      history plus the RESULT doc remain the record exactly as rules 15/29 say; or (ii) the disk
      allowance is genuinely exhausted and the session says so explicitly, naming what it is
      removing and why, before removing it.
    - **SURFACE THE DECISION BEFORE THE SESSION ENDS.** This container is ephemeral: an
      uncommitted, gitignored bundle does not survive reclamation, so "keep it" is only
      meaningful while the session is alive. A session that has solved anything promotable
      therefore **asks the promotion question explicitly in its final report**, states that the
      bundles are on local disk and will not survive the session, and never lets the question go
      unasked. If the owner has not ruled by the end of the session, say so plainly rather than
      tidying up.
    - **A cost estimate is owed BEFORE re-solving, not after.** If results were lost anyway, the
      session states the LP cost of reproducing them and waits, rather than silently launching
      hours of solves.

1. `[R-SHARD]` **EVERY SOLVE RUNS IN A SHARD. THE SESSION YOU ARE READING THIS IN NEVER RUNS AN LP,
    AND ONE SHARD COMMIT IS AT MOST 20 MINUTES OF RUNTIME.** *(Owner instruction 2026-09-09,
    verbatim: "I want runs to only use shards from now on that limit runtime to 20 min per shard
    commit as a rule with directions on successfully launching shards". The incident: session
    ercot-264 ran two ERCOT years as background jobs inside its own container, two at a time under
    rule 12's memory cap, while five idle containers were available for the asking — serialising
    ~70 min of independent LP into one ephemeral box that also had to stay alive to orchestrate.)*
    - **(a) THE PARENT NEVER SOLVES.** A session that receives a run request is an ORCHESTRATOR: it
      does phase 0, writes the PRECOMMIT, launches shards, then composes, scores and registers what
      comes back. It does not call `run_calibration_full.py`, `run_calibration.py` or
      `replay_keeper.py` itself — not in the foreground, not with `nohup`, not "just this one year".
      Its container is ephemeral and single; a shard's is neither. **Zero-LP work — phase 0 census,
      offer-array deltas, replaying committed sidecars, scoring, composition — stays in the parent**,
      because none of it is a solve.
    - **(b) ONE REGISTRABLE RUN = ONE SHARD = ONE SOLVE. SLIM PER-YEAR FAN-OUT IS BANNED.**
      *(AMENDED 2026-09-12, owner instruction, verbatim: "Ok ban slim shards this is dumb I should
      only have to wait for one solve wtf". This clause previously read "ONE SHARD = ONE COMMIT =
      ≤ 20 MINUTES — a multi-year span shards **per year**", and that instruction is what
      produced the incident: lane SPP-36 fanned a 2023–2025 span into three per-year shards,
      each pushing the slim committed file set, then found the legs could not be composed and had to
      solve the whole span again in one container. The owner waited for four solves to get one run.
      Genealogy: `docs/governance/rule-history.md` §19.)*
      **A run that will be REGISTERED is solved by ONE shard, in ONE `--years <all>` invocation,
      into ONE bundle** (which is what rule 16 `[R-ALLYEARS]` already demanded of the bundle);
      years stay sequential inside it (rule 12). That shard also attests, registers and pushes,
      the way the SPP-27 span shard did — the (c)(6) ban on `dashboard_add_run.py` targets
      CONCURRENT shards colliding on the shared generated files, and a single span shard registering
      once is the established pattern, not a violation.
      **WHY THE FAN-OUT CANNOT WORK, measured rather than asserted.** A shard can only push what
      `.gitignore` lets it commit — the slim set. Registration needs more than the slim set:
      `render_calibration_html.build_payload` reads the bundle-root `system.parquet`, and the
      per-plant D-1/D-2/D-4 diagnostics fall back to the registered run payload when
      `dispatch/<year>_<pass>.parquet` is absent, so on an unregistered composite they return
      **zero rows and PASS VACUOUSLY**. `--reuse-solved` gates on those same two artifacts
      (`plan_reuse_solved`), so a chain cannot carry years across containers either. **Both
      composition routes therefore end in a re-solve, always** — the fan-out buys nothing and
      costs a full extra span.
      **The 20-minute ceiling still governs, and it is now a STOP rule rather than a split rule.**
      A shard approaching 20 minutes with no artifact **stops and reports**; it never pushes a
      half-written bundle (rule 27 `[R-PUSH]`). Where a whole span genuinely cannot fit — a
      per-plant multi-zone ISO, not a 2-zone one like SPP, whose full span is ~500 s — the
      answer is a longer single shard with the budget stated in its prompt, **not** a fan-out whose
      legs cannot be reassembled. Subdividing (per zone family, per pass, per stage) remains
      available for DIAGNOSTIC work that will never be registered, and only there.
      **A single-year shard is still correct for a rule-29 `[R-SCREEN]` SCREEN**, which is a
      throwaway probe that is never registered and whose numbers live in the PRECOMMIT/RESULT doc.
      The ban is on fanning out a run that has to come back together.
    - **(c) HOW TO LAUNCH ONE SO IT ACTUALLY WORKS.** `mcp__Claude_Code_Remote__create_session`, and
      every one of these or the shard is wasted:
      1. **`source_revision` is a FULL 40-CHARACTER IMMUTABLE SHA — never a branch name.** Branches
         here are auto-merged and DELETED within minutes; a shard that clones one races a tombstone.
         Push your PRECOMMIT first, pin its SHA, and give the shard `git rev-parse HEAD` must equal
         `<sha>` as its first hard stop. A SHA cannot be raced. **The shard NEVER rebases, NEVER
         `git pull`s, and NEVER "syncs" itself** — in ercot-261 ten shards did and all ten were
         discarded.
      2. **`source_url` is the repo**, and the prompt names the `DATA PROFILE` so the shard hydrates
         only its own ISO's subtree.
      3. **Its own everything, so nothing collides**: its own `--out-dir`
         (`results/calibration/<lane>_<year>/`), its own branch (`claude/<lane>-<year>`), and it
         commits **only** its own bundle path — `git add -f <that path>` then `git status --short`,
         which MUST show nothing outside it.
      4. **Give it self-checkable HARD STOPS** — the pinned SHA; the config signature its leg must
         show (for ERCOT: carve-out `ercot_offer_swcap_clip: true` + `CC_REGULAR.peak 151.008`
         versus forward `false` + `4.576`); which years take `--holdout-authorized` and which must
         not (rule 22). **A shard that sees otherwise STOPS and does not push.**
      5. **Tell it what to REPORT**, in numbers, in its final message — the parent may never get to
         read its disk.
      6. **FORBID, explicitly and by name**: `git add -A` and `git add .` (ercot-261 swept 183
         unrelated bundle files onto `main` that way); `dashboard_add_run.py`, `build_manifest.py`,
         `build_status.py`, `prune_iso_runs.py` and anything under `frontend/data/backcast/**`
         (shared generated files — five shards writing them WILL collide, and registration is the
         parent's job, once, at the end); any edit under `src/` or `scripts/` (in ercot-262 one
         shard patched `replay_keeper.py` and burned its whole budget, and a second then deduped the
         same patch); opening a PR; and deleting any result (rule 31 `[R-RETAIN]`).
      7. **"A shard that stops with a clear report is a SUCCESS; a shard that repairs
         infrastructure is a FAILURE."** Put that sentence in the prompt.
      8. **MEMORY: the ceiling is the NESTED cgroup, never `free`, and a per-plant MISO/PJM year
         needs SWAP.** *(2026-09-12, the miso-252/253 incident: a CCR bash cgroup is capped at
         **13.34 GiB** on a box whose `free`/`MemTotal`/root cgroup read 15.7; a MISO year peaks
         above that inside HiGHS `run()`, and every MISO solve that ever fit here fit because an
         8 GiB swapfile was provisioned first — `scripts/prepare_solve_container.py`, 2026-09-09.
         Five shards whose prompts skipped it were OOM-killed at 13.30 GiB and the OOM was
         misdiagnosed as a model regression.)* The runners now do it themselves:
         `run_calibration_full.solve_and_persist` (hence `replay_keeper.py`) and
         `run_calibration.py` call `scripts/lib/solve_container.ensure_solve_container` before
         the first loader — binding-cgroup ceiling read, swapfile up to 24 GiB, the single-thread
         solve-profile pins — and log the cgroup's true peak (RSS and RSS+swap) at the end, so a
         finished run finally reports what it needed. A shard prompt therefore names NO memory
         recipe of its own beyond: run the runner unmodified, never pass
         `--no-container-preflight`, and REPORT the `container preflight:` and `memory peak:`
         log lines. A prompt-side probe, if one is written at all, reads
         `P=$(grep -E '^[0-9]+:memory:' /proc/self/cgroup | cut -d: -f3);
         cat /sys/fs/cgroup/memory$P/memory.limit_in_bytes` (v1) or `/sys/fs/cgroup$P/memory.max`
         (v2) — never `free`, never MemTotal, never the root cgroup.
    - **(d) THE PARENT OWNS THE SEAM.** Composition, `stamp_config_partition.py --check`, scoring,
      the dashboard registration (rule 15) and the promotion question (rule 31) happen ONCE, in the
      parent, after the shards land. Per-year shard bundle dirs are **kept out of `main`** — the
      composite is what gets registered, and an unregistered per-year dir left committed is the
      exact Class-E parity RED rule 29(c) already forbids.
    Genealogy: `docs/governance/rule-history.md` §18.

1. `[R-SHARD-ARCHIVE]` **ARCHIVE EVERY SHARD THE MOMENT ITS RESULT IS IN YOUR HANDS — AND PULL THE
    BYTES BEFORE YOU DO.** *(Owner instruction 2026-09-12: "Can you archive all your shards when you
    don't need them anymore plz and make that a new rule". The occasion: nyiso-229 spent NINE shard
    containers across a screen and a span, and four sat IDLE holding containers after the parent had
    already fetched and scored their bundles.)* This is hygiene, not bookkeeping: a shard's container
    is a real resource, an idle one blocks the concurrency the next lane needs, and the environment
    reclaims containers on its own schedule rather than the parent's.
    - **(a) THE TRIGGER IS "THE PARENT HAS IT", NOT "THE SHARD FINISHED".** Archive as soon as the
      parent has (i) fetched the shard's branch, (ii) checked out its bundle, and (iii) verified it —
      the config signature and, where the lane pins one, the input artifact's `sha256`. Until all
      three hold, the shard stays alive: it is the only thing that can re-push what it solved. After
      all three hold, keeping it alive buys nothing.
    - **(b) NEVER ARCHIVE A SHARD THAT IS STILL RUNNING**, and never archive one whose report you
      have not read. A shard that STOPPED with a blocker is archived like any other — its FINDING doc
      on its branch is the record (rule 32(c)(7)), not its container.
    - **(c) ARCHIVING IS NOT DELETING, and rule 31 `[R-RETAIN]` is untouched.** Archiving makes a
      session read-only and releases its container; it destroys no branch, no commit and no bundle.
      Nothing about it licenses removing a result the owner has not ruled on. Conversely, archiving
      is **not** a substitute for pulling the bytes: an archived shard cannot push, so (a)'s order is
      the whole of the safety here.
    - **(d) RECORD RECOVERY BY IMMUTABLE SHA, NEVER BY BRANCH NAME.** Shards rebase and force-push
      even when the prompt forbids it — measured in nyiso-229, where four of nine did, moving
      `arm-2023` to `651de9a3` and `arm-2025` to `3d76ad76` after the parent had already fetched
      them. A branch name is a moving target and branches here are deleted within minutes; the
      `git checkout <sha> -- <path>` line in the `.gitignore` comment or the RESULT doc is what makes
      a promotion cost zero re-solves, so it carries a **full SHA**. This is rule 32(c)(1)'s pinning
      discipline applied to the return trip.
    - **(e) SWEEP BEFORE THE SESSION ENDS.** A session that launched shards lists them
      (`list_sessions`, filtering on its own `parent_session_id`) as part of wrapping up, archives
      every one that is idle or complete, and **names in its final report any it deliberately left
      alive and why** — a still-solving leg is a legitimate reason, a forgotten one is not.
    - **(f) DELETE THE SHARD BRANCH TOO — BUT ONLY ONCE THE BYTES ARE SOMEWHERE THAT IS NOT THAT
      BRANCH, AND NEVER WHILE A PROMOTION IS UNDECIDED.** *(Owner instruction 2026-09-12: "Should
      also delete shard branches once data is recovered".)* A finished shard branch is litter and
      goes. But deletion here is **not** the same act as archiving: archiving releases a container
      and destroys nothing, while **deleting a branch makes its commits unreachable and eventually
      garbage-collected** — so a shard branch is frequently the ONLY durable copy of a bundle, the
      parent's own checkout living on a container that is reclaimed. Deleting it while the owner has
      not ruled on promotion is the ercot-255 incident one layer over, and rule 31 `[R-RETAIN]`
      forbids it in exactly those words. The order is therefore fixed, and each step is a
      precondition for the next:
      1. **RESCUE ANY UNIQUE RECORD.** A shard's own FINDING / blocker doc exists nowhere else —
        commit it onto the parent's branch first. (Docs the shard merely inherited from `main` need
        no rescue; check which is which rather than assuming.)
      2. **THEN DELETE, IF AND ONLY IF the branch carries no bundle the lane may still need.** A
        branch holding only docs, or only a failed attempt, goes immediately. A branch holding a
        **screen** bundle may go once the PRECOMMIT/RESULT doc carries every number the lane will
        ever cite from it — which rule 29 `[R-SCREEN]` (c) already requires, and which is what makes
        a screen bundle disposable where a candidate bundle is not.
      3. **A BRANCH CARRYING A BUNDLE A PROMOTION WOULD REGISTER STAYS UNTIL THE OWNER HAS RULED.**
        Registration needs the per-plant layer, not just the summary numbers, so deleting these is
        deleting a result — rule 31, no exceptions, and the promotion question gets asked rather
        than pre-empted by a cleanup. Once the owner rules, promoted or declined, the branch goes.
      4. **RE-PIN NOTHING TO A DELETED SHA.** Clause (d)'s recovery line must name a commit that
        still resolves; when a branch is deleted, the recovery route in the doc changes from "check
        out this sha" to "re-solve, cost stated", and the doc is updated to say so honestly instead
        of keeping a command that will fail.
      5. **A SESSION MAY NOT BE ABLE TO DELETE AT ALL, and that is not a transport flake to retry
        around.** Measured 2026-09-12: `git push origin --delete <branch>` returns **HTTP 403** here
        — the session's credential can create and update refs but not delete them — and the GitHub
        MCP server exposes no branch-deletion tool (`create_branch` exists, no counterpart). The
        symptom is misleading: git reports `send-pack: unexpected disconnect` and then
        `Everything up-to-date`, which reads like the HTTP/2 flake the Git & Pushing section says to
        retry on HTTP/1.1 — it is not, and on HTTP/1.1 the underlying 403 becomes visible. So a
        session does steps 1–3, and if deletion is refused it **says so and leaves the branch**
        rather than reporting a cleanup it did not perform. The normal disposal route stays what it
        always was: a merged shard branch is auto-deleted by the environment.

1. `[R-SHARD-PROMOTABLE]` **A SOLVE THAT COULD EVER BE PROMOTED MUST PUSH ITS BUNDLE. NEVER LAUNCH
    A SHARD WHOSE RESULT CANNOT BACK A PROMOTION, AND SOLVE EVERY YEAR THE KEEPER CARRIES — ALL OF
    THEM.** *(Owner instruction 2026-09-12: "change the repo rules to never do shard runs that can't
    backup a promotion to keeper", and "All years go into keepers". The incident: miso-255 sharded a
    five-year screen, had every shard `.gitignore` its bundle under rule 29 `[R-SCREEN]` (c), and
    reported a clean result. The owner then ruled promote — and every bundle was stranded on an
    ephemeral shard container the parent had no way to reach, so a decided promotion cost a FULL
    RE-SOLVE OF EVERY YEAR. Rule 31 `[R-RETAIN]` already forbids deleting a result before the owner
    rules; this rule closes the hole rule 31 does not cover, which is a result that was never
    RETRIEVABLE in the first place.)*
    - **(a) THE BUNDLE IS PUSHED, ALWAYS. `.gitignore` IS FOR THE PARENT'S TREE, NEVER THE SHARD'S.**
      A shard commits its own bundle to **its own branch** and pushes it — by appending a
      `.gitignore` NEGATION for its own out-dir and then using a **PLAIN `git add`**, NEVER
      `git add -f`:
      `printf '\n!results/calibration/<out-dir>/**\n' >> .gitignore` then
      `git add .gitignore && git add results/calibration/<out-dir>`.
      *(CORRECTED 2026-09-12, same day this rule was written: it originally prescribed
      `git add -f <its out-dir>`, which is **the exact command the auto-mode classifier
      refuses** as [Modify Shared Resources] — and in miso-255 that refusal then hardened
      one shard's permission state until even the plain `git add` that had worked at solve
      time was denied, costing a re-solve. `-f` is needed only because `.gitignore` line
      ~651 ignores `results/calibration/*/dispatch/` repo-wide on the stated belief that
      "~80 MB would trip the remote's 413 push limit" — a belief FALSIFIED the same day:
      102,367,743 bytes pushed as a single-blob pack over plain `git push` with no 413.
      Full chain: `docs/FINDING-miso255-why-the-dispatch-pushes-failed-2026-09-12.md`.)*
      **The bundle MUST include `dispatch/<year>_P1.parquet`** — `render_calibration_html.
      build_payload` reads it per year and registration raises `FileNotFoundError` without
      it. Committed precedent: `caiso275_B_gascoupling_{2022,2023,2024,2025}` (45-49 MB
      each) and `nyiso_fuelvintage_H2` (21.4 MB), all on `main`.
      Rule 29 `[R-SCREEN]` (c)'s "delete before merge" governs what reaches **`main`** — it has never
      governed what reaches a shard branch, and a shard branch is not `main`. The parent keeps the
      per-year dirs out of `main` (rule 32(d)) by fetching them, composing, and committing only the
      composite; that is the seam where the duty lives, not on the shard. **A shard prompt that tells
      its shard to gitignore or omit the bundle is a defect in the prompt.**
    - **(b) A SCREEN IS NOT AN EXCEPTION, BECAUSE YOU CANNOT KNOW IT IS ONE UNTIL THE OWNER RULES.**
      The whole point of rule 31 is that the owner routinely promotes what a session declined. So
      "this is only a screen, the doc carries the numbers" is not a reason to strand the bytes: the
      numbers support a WRITE-UP, and a registration needs the per-plant payload. Push the bundle;
      the doc is still required and still carries every number the lane will cite.
    - **(c) SOLVE EVERY YEAR THE ISO'S KEEPER CARRIES, IN THE SAME BATCH — HELD-OUT YEARS INCLUDED.**
      **All years go into keepers.** A promotion re-keys the ISO's whole registered set, so a batch
      that solves only the training span leaves the ISO's other years pointing at a superseded recipe
      — and under rule 30 `[R-TOUCHPOINT-FOLD]` (a) a dangling `holdout.keeper` stamp reads as
      unstamped, silently dropping those years off the ISO's report. Before launching, enumerate the
      ISO's registered years from `frontend/data/backcast/registry/*.json` and launch one shard for
      **each**, against that year's own committed control. For MISO at this writing that is SIX years
      (2020-2025), not three. A year deliberately left out is named in the PRECOMMIT with its reason.
    - **(d) THE PARENT VERIFIES RETRIEVABILITY BEFORE IT ARCHIVES ANYTHING.** Rule 33
      `[R-SHARD-ARCHIVE]` (a) already requires fetch + checkout + verify before archiving; this rule
      adds the check that makes it possible — `git ls-tree -r <shard sha> -- <bundle path>` must
      return **more than zero files**. Zero means the bytes exist only on a container, and the
      correct report is that the run is **not promotable without a re-solve**, stated at the time,
      with the cost — not discovered later when the owner asks for the promotion.
    - **(e) STATE THE RETRIEVABILITY IN THE RESULT.** Every RESULT doc for a sharded solve says, in
      one line, where each bundle is and what a promotion would cost from that state. "On ephemeral
      shard disk, ~N min to re-solve" is an acceptable sentence only if (a) was impossible for a
      stated reason; it is never the default outcome.

1. `[R-PROMOTE]` **A PROMOTION IS NOT DONE UNTIL THE OUTGOING KEEPER'S FILES ARE GONE — AND THE
    INCOMING KEEPER CARRIES EVERY YEAR THE ISO HAS ALREADY RUN, HELD-OUT YEARS INCLUDED.** *(Owner
    instruction 2026-09-12, verbatim: "make it a rule that keeper promotion deletes the Pripr keeper
    filed and all solves/keepers include any holdout years that have already been run" — read as
    "the PRIOR keeper's FILES". The incident is the state the rule was written out of, not a single
    session's error: rule 15 `[R-DASHBOARD]` has required keeper-only retention since 2026-09-05, but
    it defers the sweep to "the next registration" — and across the promotions of the following week
    nobody swept. Measured 2026-09-12 before the clean-out: **47 registered runs against 7 designated
    keepers** (33 superseded), 92 bundle dirs under `results/calibration/`, five of them holding
    `check_registry_payload_parity.py` RED, and 579 MB where the keepers need 198. The same day's
    NYISO promotion to `nyiso229-hourgrain-span` left both superseded `nyiso-221` runs registered
    behind it. A duty deferred to "next time" is an unowned duty; this rule gives it an owner and a
    deadline. Genealogy: `docs/governance/rule-history.md` §20.)*
    - **(a) THE PROMOTING SESSION DELETES, IN THE SESSION THAT PROMOTES.** The session that writes a
      new id into `frontend/data/backcast/keepers/<ISO>.json` also removes the outgoing keeper's
      **three stores** — `registry/<id>.json`, `runs/<id>.js` and the `bundle` dir its sidecar names —
      through `scripts/prune_iso_runs.py --iso <ISO>`, which deletes all three together so they
      cannot drift into orphans. **This TIGHTENS rule 15 `[R-DASHBOARD]` and supersedes its "pruned at
      the next registration" timing**; everything else in rule 15 stands unchanged, the keep-set
      included. Scope stays per-ISO exactly as the keeper shards do (`keepers/README.md`): a
      promoting lane prunes **its own ISO only**, never another's.
    - **(b) ENUMERATE THE YEAR SET BEFORE YOU DELETE — THE DELETE DESTROYS THE EVIDENCE.** The
      registry is the only mechanical record of which years an ISO has run; once the outgoing keeper's
      sidecars are gone, "which held-out years has this ISO already run" is answerable only from git
      history and prose. So the order is fixed: read the union of `years` over **every** sidecar for
      that ISO — the outgoing keeper's and each run folded to it — write that set into the promotion's
      PRECOMMIT/RESULT, and only then prune.
    - **(c) THE INCOMING KEEPER MUST COVER THAT UNION. A PROMOTION THAT SHRINKS AN ISO'S YEAR SET IS
      INCOMPLETE, NOT FINISHED.** *"All solves/keepers include any holdout years that have already
      been run"*: a year the ISO has run once is a year its keeper carries from then on, whether it
      sits in the training span or was held out. Cover it in the registered keeper bundle itself or in
      a run stamped to it (rule 30 `[R-TOUCHPOINT-FOLD]` (a)) — either satisfies this; an unstamped
      run does not, because a dangling `holdout.keeper` reads as unstamped and the year drops off the
      ISO's report silently. If a year is missing, **do not prune**: solve it (rule 34
      `[R-SHARD-PROMOTABLE]` (c) launches one shard per year, which is how the set is met in the first
      place), or leave the outgoing keeper registered and say in the RESULT which years are
      outstanding and what they cost. A partial promotion that deletes anyway converts a gap into a
      silent loss.
    - **(d) WHAT THE DELETE TOUCHES, AND WHAT IT MUST NOT.** It touches the three stores and nothing
      else. It does **not** rewrite the governance narrative: the superseded id stays wherever
      `calibration-complete.json`, the keeper shards and the `FINDING`/`RESULT` records cite it as
      history — those citations are the audit trail of how the current keeper came to be, and **git
      history is the record** for the bytes, exactly as rule 15 says. Because `prune_iso_runs.py`
      blocks on any governance mention, `--force-uncite` is the **intended** route here and not a
      safety override — the guard exists to make the operator look, and this rule is the looking.
      Two bundle classes stay on disk even as their run comes off the site, and the script prints
      both: one a `results/regression-goldens/*/manifest.json` capture record names, and one on
      `check_registry_payload_parity.KEEP_REQUIRED_UNMAPPED_BUNDLES`.
    - **(e) PROMOTE, VERIFY, THEN DELETE — IN THAT ORDER.** The incoming keeper must be registered
      and its sidecar, payload and bundle present *before* the outgoing one is removed, or a failed
      promotion leaves the ISO with no keeper at all. `scripts/audit_keepers.py` (E1) is the check
      that the incoming three stores resolve; run it between the promotion and the prune, not after.
      Rule 31 `[R-RETAIN]` is untouched and outranks this rule: the outgoing keeper is deletable
      because **the owner has ruled on promotion** — that ruling is trigger (i) — and nothing here
      licenses deleting a bundle whose promotion is still open.
    - **(f) THE INVARIANT, STATED SO IT CAN BE CHECKED.** After a promotion, every run registered for
      that ISO is either its designated keeper or stamped to it, and the ISO's registered year set is
      no smaller than before. Enforced by `scripts/audit_keepers.py` check **E13**, which fails an ISO
      carrying a registered run that is neither — the gap this rule was written for, since `audit_keepers`
      passed cleanly on all 47 runs the day 33 of them were superseded.

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

- **Step 0, confirmed exits** — `data.confirmed_retirements.load_confirmed_exits` over `data/raw/confirmed-retirements`, GATED `confirmed_exits_enabled` (default on), forecast-mode only. A row needs an enforceable public instrument (RTO deactivation acceptance, consent decree, statute, regulatory order, RMR end); this is the **instrument-bound** exogenous fossil exit channel and it **bypasses the reliability floor**. *(It was the ONLY one until owner ruling Q30, 2026-09-02, armed the owner-filed-date limb at step 1b below — which is a different admissibility class: an owner's filed plan, not a binding instrument, and it rides this step's machinery.)* Hindcast information gate: a row applies only when `instrument_date` ≤ the vintage cutoff. (Spec §5.1–§5.2; `docs/handoffs/confirmed-retirement-plan-2026-07.md`.)
- **Step 1, announced retirements** — `apply_announced_retirements`, `load_announced_reversal_plants`, `EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS` (default 5) bounds honored non-fossil dates. **For FOSSIL the owner's own filed EIA-860 Schedule-3 date is honored as an exogenous step-1 input** — limb 1b, `fossil_announced_exits_enabled` **default ON since 2026-09-02** (owner ruling Q30 on the capx D42 A/B, executed by D44) — **vintage-gated** (a date is admissible in year Y only because it was on file at the run's information cutoff, the same gate step 0 applies to `instrument_date`, and the identical construction regenerates for a forecast year from the then-current 860), with the **reversal registry armed** (a plant countered by a later public instrument is dropped; under `hindcast_verified_announced_exits` a re-filed or withdrawn date is honored per unit as the later vintage's information — it may defer or cancel a vintage exit, never inject or advance one). The rows ride step 0's own matcher/derate machinery, so they bypass the reliability floor like every exogenous exit. Rule 19 `[R-ONE-MECH]`: a plant carrying a pending filed date is **exempt from the economic screen**, which therefore decides only the **residual UNDATED fleet** — no unit's exit is decided twice, and `forecast_fossil_retirement_economic` (default True) now governs only what the date channel does not reach. Evidence: MISO T1-H unit recall 5/19 → 16/19, every non-coal exit class opened, `false_retire` 0.0, **zero** economic exits displaced (`docs/handoffs/FINDING-capx-d42-fossil-dates-ab-2026-09-02.md`). What it does not close, stated at the gate: the undated cohort, the December-dated majority-of-year roll into the next year, and genuine deferrals. (Spec §5.1.)
- **Step 2, CCS retrofit** — `ccs_retrofit_available_year`, `eac_price_gas_cc_ccs`, `ira_ccus_45q_last_year`, `ira_45q_credit_window_years`; ≥15 yr remaining life, 3 GW/yr/ISO cap, valued as the **incremental uplift over the best unabated state**, screened jointly with retirement. `ccs_retrofit_capex_co2_scaling` (capx D50, **default ON since 2026-09-05** — owner ruling Q42 on the D50/D50-R A/B, executed by capx D60): sizes the capture island to the host's captured CO2 against the ATB reference host (0.323 t/MWh — the same host the new-build CCS LCOE charges the ATB increment against, zero DOF) and excludes CC_CHP hosts — the D49 §1.5 construction repair of the flat-per-kW seam, under which the retrofit margin had risen with host emissions. A **posture, not a transfer** (rule 25 `[R-ISO-SCOPE]` intact: no ISO's fitted number is carried), landed as a (b′-1) declared default flip with the frozen cache-key drop value left at `False`, so an explicit `False` still selects the pre-flip construction and keeps its key. Inert below `ccs_retrofit_available_year` (2028) by construction, so every backcast, hindcast and crossover horizon is byte-identical. Evidence: at carbon 0 the repair closes the screen (ERCOT 3.79 GW → 0; PJM 5.74 → 0 in 2028; MISO 4,631.1 MW → 0 across the window) and under RGGI it does not (NEISO 12.79 → 12.38 GW) — the asymmetry, not the level, is its signature (`docs/handoffs/FINDING-capx-d50-2026-09-04.md`). (Spec §5.6.)
- **Step 3, economic retirement** — screens the **attainable (pro-forma) inframarginal margin**, `Σ_t max(0, price − full variable cost, reserve price) × pmax × availability` (Potomac-SOM net revenue, `mc_cost` via `prior_results`): **never gross revenue, never realized dispatch**. Against FOM-only going-forward cost. Per-fuel thresholds are `ScenarioConfig` fields, not hardcoded, and apply to the **legacy** rule only (`retirement_rule="legacy"`; under the pipeline rule the decision is uniform and the per-fuel physics lives in `retirement_execution_lag_*`): coal=3yr, gas_ct=2yr, gas_cc=3yr; coal FOM multiplier 1.3×. *(Corrected 2026-08-02 by FFR-3B: this read "coal=1yr", but `scenarios.py` ships `retirement_years_coal: int = 3`, identified under rule 23 to the EIA-860 announced-to-deactivation capacity-weighted/≥300 MW median of 3 yr. Code is the source of truth.)* `screen_reserve_value_enabled` (default on) — the co-opt's own reserve duals under `ercot_thermal_as_endogenous`, else the ORDC scarcity adder; when present it is the **SOLE** thermal AS pricing (rule 19 `[R-ONE-MECH]`). Floor: `accredited_firm_capacity_mw` vs `peak × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)`, one requirement shared with the build backstop, `floor_retention_log` attribution. (Spec §5.2.)
- **Steps 4–5, additions and entry** — `load_planned_additions` (EIA-860 proposed pipeline, construction-committed statuses, forecast mode only). **RPS is not a force-build step** — it is an annual LP constraint whose dual is the REC price. (Spec §5.3–§5.4, §1.4.)
- **Storage entry** — an economics-based **value stack, not compound growth**: arbitrage net of cycling degradation **plus** RA capacity value, paid only where the per-ISO `MARKET_DESIGN` registry has a capacity market (energy-only ERCOT pays none). `STORAGE_TECH_BUILD_SHARE_CAP`, base-year fleet `storage_deployment` with all later growth endogenous; toggles `storage_capacity_value`, `storage_degradation`. (Spec §5.5.)
- **PJM capacity-market clearing (the clearing half, capx D57)** — `capacity_market_supply_clearing_by_iso` (`{iso: bool}`, dataclass default `None`; requires the curve gate): the retirement screen clears the fleet's net-ACR sell-offer stack (`offer = max(0, going-forward cost − E&AS margin) / accredited MW`, every other accredited MW a $0 price taker) against the delivery year's published VRR curve — cleared units earn the clearing price, uncleared units $0, so **the screen's failing set IS the auction's uncleared set**; entry and storage read the clearing price as price takers through the one `capacity_price_per_firm_mw_yr` seam. **ARMED FOR PJM** with the two D48 accreditation-design fields through `iso_configs.py::_pjm_config` `default_scenario_overrides` (owner ruling 2026-09-05 on the D57 A/B; `FINDING-capx-d57-2026-09-05.md` §8.1) — the shared defaults stay off, every other ISO and every backcast keeper byte-identical, `--no-…` reaches the control. Measured: cleared position within 0.5 / 1.0 / 2.8 pts of the published; price 1.5–5.7× the published because the CT / ST / oil E&AS operand is zero in the hindcast prices (the named successor), never haircut. (Spec §5.9; `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md`.)
- **PJM published adequacy requirement (the clearing half's denominator, capx D67)** — `capacity_adequacy_requirement_published_by_iso` (`{iso: bool}`, dataclass default `None`): the bar the reliability floor, the reserve-margin build backstop and the CR-1 position all test becomes the ISO's **own published whole-RTO Reliability Requirement in MW** for the delivery year the screen prices, in place of the model's `screen peak × FPR` reconstruction — injected at the single `gross_adequacy_requirement_mw` seam all three reach through, so arming moves **one** object (rule 19 `[R-ONE-MECH]`). The defining property: in every in-table delivery year the requirement is **independent of the model's peak** (`∂R/∂peak = 0`). **Zero scalar fields** (rules 21/24): the MW are digitized from the committed `data/raw/capacity-market/demand-curve/pjm/pjm.csv` `reliability_requirement` rows and reconciled against them byte-for-byte by test; the **vintage rule** (the whole-RTO row, never the `_frr_adj + ee_addback` RPM-only comparator, which is net of a 31–32 GW FRR block the model does not carve out) and the **hold-last rule** (pre-table years, the in-table gap and everything past the forward edge fall through to the FPR path — which for PJM *is* the ratio hold-last, since `RR = forecast peak × FPR` by definition, so no absolute MW is ever held forward) were both fixed before any solve and neither is selectable by a result. **ARMED FOR PJM** through `iso_configs.py::_pjm_config` `default_scenario_overrides` (**owner ruling Q52**, 2026-09-06, on the D67 A/B; `FINDING-capx-d67-2026-09-06.md` §7.1, executed by `FINDING-capx-d67arm-2026-09-06.md`) — the shared default stays `None`, every other ISO and every backcast keeper byte-identical, `--no-capacity-adequacy-requirement-published` reaches the pre-arm posture and keeps its key. Measured: `arm − published = 0.000 MW` in all four screened delivery years, and the card moves **two** delivery years *away* from the published position and two toward it — the signature of a real operand rather than a fitted one, and why it was screened structurally. Stated at the gate: the two FALL years are a genuine cost whose root cause is routed to the demand path, not absorbed. (Spec §5.9.)
- **PJM VRE accreditation vintage (the VRE half of the D48 devintage, capx D75-R)** — `pjm_vre_accreditation_vintage` (bool, dataclass default `False`): PJM wind and solar are accredited at each delivery year's **own published ELCC class ratings** (`RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO`) instead of `RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]`, which is digitized from the 2026/27+ *marginal*-ELCC ratings and **clamps** on every PJM pool in the window — i.e. applies one post-reform rating to three delivery years that cleared under a different published construct. A **sub-gate inside the D48 family, not a mechanism beside it** (rule 19 `[R-ONE-MECH]`): the predicate also requires `pjm_accreditation_design_vintage`, so the VRE and thermal halves are never devintaged apart. **Zero scalar fields**, one declared cross-vintage reconciliation under rule 14's misalignment exception (PJM's own Table-5 mix `1189/(1189+8713)`, and the conclusion is mix-insensitive). **ARMED FOR PJM** through `iso_configs.py::_pjm_config` `default_scenario_overrides` (**owner ruling Q55**, 2026-09-06, on the D75-R A/B; `FINDING-capx-d75r-2026-09-06.md` §8, executed by `PRECOMMIT-capx-d75r-arm-2026-09-06.md`) — the shared default stays `False`, every other ISO and every backcast keeper byte-identical (21 of 153 committed run configs move, all PJM forecast), `--no-pjm-vre-accreditation-vintage` reaches the pre-arm posture and keeps its key. Measured: accredited VRE **down** 754.6 / 332.9 / 148.3 MW in DY 2023/24–2025/26, reproducing the zero-LP prediction to ~0.001 MW; **all 26 scored bands byte-identical**, and rule 14 — not the residual — is the reason it arms. Stated at the gate: it removes *false* exits without finding missing *true* ones (`unit_recall_gt300` unchanged at 0.65), and the 2024/25–2025/26 census move the wrong way through fleet propagation — D66 card B's remaining half, routed not absorbed. (Spec §5.8.)
- **PJM retirement-screen sector gate (capx D53 / D78, ARMED FOR PJM by Q56)** — `retirement_sector_gate` (bool, dataclass default `False`): a thermal unit whose plant's EIA-860 `Sector` is 1 (a regulated electric utility, read at the run's active vintage) still **offers** its accredited MW into the D57 capacity clearing at its net-ACR cap — PJM's must-offer requirement keys on existing-and-in-footprint, never on ownership (Manual 18 Rev 62 §1.2 / §5.4.1) — but is **partitioned out of the step-3 economic exit decision**, which models a merchant choice its owner never faces; a utility exit is an IRP / rate-case filing carried by step 0's instruments and step 1b's owner-filed dates, so no unit's exit is decided twice (rule 19 `[R-ONE-MECH]`, one seam: `exit_exempt_unit_ids`). **Zero free parameters** (rules 21/24): a partition on one published per-plant boolean. **ARMED FOR PJM** through `iso_configs.py::_pjm_config` `default_scenario_overrides` (**owner ruling Q56**, 2026-09-06, served by `FINDING-capx-d78r3-2026-09-06.md` §5 on the D78-R2 / D78-R3 full window; executed by `PRECOMMIT-capx-d78arm-2026-09-06.md`; the armed `pjm-t1h` re-solve and its registration are still owed by that lane) beside the D48 / D57 / D67 / Q55 entries — the same way MISO's D53 arm sits on MISO's own ISOConfig — so the shared default stays `False`, every other ISO and every backcast keeper byte-identical (25 of 173 committed run configs move at HEAD 2026-09-07, all PJM forecast), `--no-retirement-sector-gate` reaches the pre-arm (Q55) posture and keeps its key. The decision rests on structure, never on the residual (rules 1/14): the partition is exact in all five window years (every control-only failing row sector-1, the arm-only set empty, zero sector-1 rows in any decision ledger), the window decided total lands on the pre-registered exact-partition point value 9,394.156 MW to the milli-MW, the whole-ledger diff finds zero unclassified rows, and purity holds on D57 §4's per-delivery-year zero-E&AS set (1,354 gated shared rows, 0 moved). Reported at full magnitude and **not a criterion in either direction**: `retire.total_gw` 18.058 → 15.937 GW crosses FAIL → PASS against 15.062 actual, `unit_recall_gt300` **falls** 0.650 → 0.550 as a partition removing matched sector-1 exits must, the 2025/26 clearing price moves 358.267 → 236.945 $/MW-day on the steep VRR limb, and limb (d) cannot discriminate on recall in either leg. Stated at the gate: `false_retire` stays FAIL and the CT / ST / oil E&AS operand (D57 §4) remains the named successor for the retirement bands. (Spec §5.2.)
- **MEASURED hindcast capacity-screen PEAK (capx D76, ARMED FOR EVERY ISO by Q58)** — `capacity_screen_peak_measured_hindcast` (bool, **dataclass default `True` since 2026-09-07**): the peak every capacity screen tests becomes, **in a hindcast year only**, that year's **own measured load — the identical array the same year's LP dispatches** — instead of the weather year's load de-grown across the span by `_scale_demand`. One seam (`runner.py`, the year loop's `peak_demand`), under the **LP's own branch predicate** (`config.hindcast and not config.is_crossover_forward_year(year)`), **replacing** the de-grown peak and never stacking on it (rule 19 `[R-ONE-MECH]`, whose consumer enumeration — CR-1 position, D59 locality peaks, the adequacy requirement, the accreditation census, and via `evolve_fleet` the retirement reliability floor, the entry screen and the reserve-margin backstop — is `FINDING-capx-d76-2026-09-06.md` §4.2, re-verified complete at the arm). The measured array is built once per year and shared with the LP, so an armed year performs exactly the demand reads an unarmed year does. **Zero scalar fields, zero free parameters** (rules 21/24) and nothing transferred between ISOs (rule 25 `[R-ISO-SCOPE]` — one shared seam, the same repair everywhere, no per-ISO number). **ARMED AS THE DEFAULT POSTURE** by the (b′-1) route (**owner ruling Q58**, director sitting r#55, 2026-09-07, on `FINDING-capx-d76-arm-2026-09-07.md`; executed by `PRECOMMIT-capx-d76-arm-b-2026-09-07.md`), in **two halves**: the flip declared by appending to `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` with the frozen drop value left at `"False"`, **plus** a `__post_init__` coercion back to that frozen declaration whenever `not config.hindcast`. Without the second half the flip re-keys 93 configs the gate cannot reach, ten of them backcast keepers; with it, **34 keys move and every one is a hindcast bundle the gate governs** (PJM 10, MISO 9, NEISO 6, NYISO 5, ERCOT 3, CAISO 1) — **zero backcast moves, zero non-hindcast forecast moves**, every backcast keeper byte-identical, and `--no-capacity-screen-peak-measured-hindcast` reaches the pre-arm posture and keeps its key. **The basis is rule 14 `[R-ACCURATE]`, never the residual**: the de-grown estimate is wrong by **−23.3 % to +15.4 %** against the array the LP dispatches, and rule 14's misalignment exception cannot apply *because it is the same array*. Inert by construction — and **by test at both layers** — in every forecast run, every crossover forward year and every backcast, so the growth path remains **the** forecast methodology and rule 13's forward test is met. Stated at the gate: decisions move in only **2 of 6** ISOs (CAISO −2,532.391 MW of backstop gas CT; MISO 343.312 MW of coal saved from a 2024 exit, outside the scored window) — that is evidence the gate is well-behaved and **a point for neither side**; arming only where it bites was offered and refused as fitted-mechanism selection (rule 1 `[R-STRUCT]`). The 34 hindcast bundles carry the superseded operand under their own keys and are re-solved by their own ISO's lane on its natural cadence. (Spec §5.1–§5.2, §5.8.)
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
subtrees it needs.** Post-rewrite measurement (2026-08-16, after the BLOAT-B
prunes and the 2026-08-16 history rewrite): the pack a full clone transfers is
**5.46 GiB**, of which **4.13 GiB packed (8,777 blobs) is live at the tip of
`main`**; a full bare clone completed in **162 s** through the egress proxy, so
the old hard stall ("Cloning the git_repository source took longer than the
allowed time") is no longer automatic — but minutes vs seconds still argues
for the standard recipe: **`--filter=blob:none` plus sparse-checkout**
(3.5 s / 13.7 MB, code checkout 306 MB). `--depth 1` still transfers the whole
tip tree — never the fix. Recipe, measurements and the three partial-clone
traps: `docs/fast-clone.md`. (Never measure pack size with `--mirror` against
GitHub: `refs/pull/*` still pins the pre-rewrite objects, ~20 GiB.)

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
  bulk payload at tip while keeping its `README.md` + `SHA256SUMS.txt` tracked.
  **The 2026-08-16 history rewrite stripped the untracked payloads from history
  too — "the bytes stay recoverable forever" is FALSE as of that date, and the
  README pin shas / `git restore --source=<pin>` commands are dead** (repaired
  in place; `docs/FINDING-history-rewrite-2026-08-16.md`). What each corpus
  README now carries: the verified source-URL table, the re-fetch command (the
  primary recovery route), the honest retention status — some payloads are
  **unrecoverable from this repository** (the CAISO OASIS GRP dailies; pre-slim
  SCED columns past MIS retention) — and the `SHA256SUMS.txt` identity record.
  Read the corpus README before concluding data is missing. Converted so far:
  `pjm-energy-offers`, `caiso-public-bids`, `pjm-da-virtuals`, `pjm-zonal-lmp`,
  `ercot/SCED-CT`, `miso-energy-offers`, `pjm-binding-constraints`, (BLOAT-B-2)
  `caiso-dam-outages/daily`, the publication PDFs under `ERCOT/` `MISO/` `NYISO/`
  `PJM-AS/`, and `NYISO/nyiso load reports *.zip`; and (BLOAT-S2, 2026-08-17,
  the Stage-2 (a)-only O2 grant — recovery is re-fetch ONLY, never a pin)
  `storage-as-awards/CAISO/*.xlsx`, the whole orphaned `PJM/` corpus, the
  `eia-930` per-BA long files + 2018 BALANCE halves, the `campd-unit-level`
  2018 vintage, and the two `iso-specific-transmission` PJM-2018 drops
  (−444.5 MiB at tip; per-corpus verdicts incl. what deliberately STAYS
  tracked: `docs/FINDING-bloat-s2-evidence-passes-2026-08-17.md`).

`.github/workflows/cleanup-large-blobs.yml` **was executed for real on
2026-08-16** (run 31955205445 — an explicit owner decision superseding the
former standing NO-GO of `docs/FINDING-rewrite-prep-2026-08-11.md` §8 /
Addendum AQ; that NO-GO is annotated as superseded, not deleted). It stripped
7,254 superseded blobs / 7,373.4 MiB and force-pushed the rewritten history —
which is why every pre-2026-08-16 commit-sha citation outside
`docs/governance/citation-commit-map.txt` is now a dead (or, for short
prefixes, possibly WRONG) reference. Full record and the post-rewrite
recovery rules: `docs/FINDING-history-rewrite-2026-08-16.md`. Any FUTURE
rewrite remains owner-gated and must archive its commit-map artifacts first
(finding §7 open item 2).

A session's `results/<ISO>/<key>/` reuse is no longer decided by the config
alone: since capx D79 (owner ruling Q54) `cache_key()` also carries a **solve-surface
fingerprint** — a per-name, per-ISO value hash of the seven
`config/solve_surface.py` `SURFACE_MODULES`, dropped at each name's frozen
declaration in `config/solve_surface_declared.py`, so a re-derived registry table
re-keys the ISOs whose rows moved (it landed at zero key moves, and every bundle
records what it solved on in `solve_surface.json`).

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
- `docs/calibration-log.md` (frozen archive ≤2026-07-19) + `docs/calibration-log/<iso>.md` per-ISO continuations (`governance.md` for cross-ISO), `docs/calibration-session-log.md` — calibration history. Keeper promotions are per-ISO lanes: edit `frontend/data/backcast/keepers/<ISO>.json` + rebuild `status/<ISO>.js` (`build_status.py --iso`) — never another ISO's files (see `frontend/data/backcast/keepers/README.md`); the same session also re-keys the ISO's `calibration-complete.json` entry to the new keeper — that file survives `[R-HOLDOUT]`'s removal as the keeper designation and the forecast program's gate-(a) input, and no longer authorizes any year
- `docs/forecast-development-plan-2026-07.md` — THE forecast program (Forecast Finalization Program): tier ladder, lanes/waves, prompt pack, rubric charter. All prior forecast plans are superseded as coordination docs by it (its §9 migration ledger).
- **Code is the source of truth.** When docs and code disagree, fix the docs (run `/sync-docs`). When the methodology is genuinely ambiguous, the spec wins.
