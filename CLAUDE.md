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
  config/    → scenarios.py (ScenarioConfig dataclass), constants.py, iso_configs.py (6-ISO topology)
  data/      → eia_loader.py, fleet.py (CAMPD binning), renewables.py, fuel.py, outages.py, hydro.py, ownership.py
  model/     → dispatch.py (LP core), commitment.py (3-solve UC screen), transmission.py, storage.py, capacity.py
  policy/    → ira.py, rps.py, carbon.py, eac.py, constraints.py
  results/   → cache.py, outputs.py, emissions.py, export.py, calibration.py, plant_financials.py
  runner.py  → main orchestrator (P0→P1→P2 solve loop, year evolution)
tests/       → pytest, one file per module
data/        → all on-disk inputs; every path resolves through config/paths.py (never Path(__file__).parents[...])
  raw/       → immutable source downloads, NEVER modified in place — the single source root (W1 collapsed the old inputs/ + data/ roots into data/raw/)
               eia-930*/, eia-860/, fleet-egrid/, campd-{unit,facility}-level/, gas-prices/, lmp-data/, zone-specific-demand/, …
               reference/ (loose crosswalks: custom-bin-assignments.csv, master-plant-registry.csv, …),
               _processed-legacy/ (former inputs/processed), _validation-source/ (former inputs/calibration)
  clean/     → curated, schema-validated Parquet (DERIVED, disposable, gitignored)
  dictionary/→ the data contract: schema/<datatype>.schema.yaml + data-dictionary.md
```

## Non-Negotiable Rules

1. **Right market structure first, offer-curve tuning second — backcast match is NOT the objective.** The goal is a model whose *mechanisms* mirror the real market (reserve withholding/co-optimization, scarcity pricing, congestion, commitment, fuel/passthrough physics). Build the correct structure, *then* tune offer curves to calibrate the level. **Never judge a structurally-correct mechanism by whether it improves the backcast fit, and never reject/revert it because the residual didn't move** — a real market behaviour stays in even if it makes the fit worse (then fix the actual root cause per #11). Conversely, never reach the right number through a mechanism that isn't real (a fitted adder, a load proxy, a haircut tuned to the residual). A run is a "keeper" because it is the most structurally faithful, not because it has the lowest MAE; a more-accurate run that is missing real structure is **not** a keeper.
1. **No Python loops over hours in LP construction.** Use np.tile, np.repeat, scipy.sparse.kron, block_diag. If you write `for t in range(8760):` in the matrix builder, stop and vectorize.
1. **Renewables are decision variables** on LHS of energy balance with MC=0, upper bound = CF × capacity. NOT netted from demand.
1. **Prices = LP duals** on energy balance constraints. No separate pricing model.
1. **No magic numbers.** Every value from ScenarioConfig or constants.py with citation comment.
1. **Struct-of-arrays before LP construction.** Convert Pydantic objects → FleetArrays (parallel numpy arrays). LP builder only touches arrays and scalars.
1. **Parquet for results.** One file per scenario-year. Check-before-run caching.
1. **Full 8760 hours always.** No representative days/weeks.
1. **Storage tiebreaker ε = 0.001 $/MWh** on charge+discharge to prevent degeneracy.
1. **One-pass capacity evolution.** No within-year convergence iteration.
1. **Every public function gets a docstring.** Every module gets a module-level docstring.
1. **Run independent calibration solves in parallel, never consecutively — but always solve years sequentially within a single run.** Each `run_calibration_full.py` LP solve is minutes long; when launching multiple *separate invocations* (different ISOs or configs, each with its own `--out-dir`) with no dependency between them, start them as concurrent background jobs — don't wait for one to finish before starting the next. e.g. launch `--iso PJM --out-dir …/pjm` and `--iso CAISO --out-dir …/caiso` at the same time. **Within a single invocation**, however, years (`--year 2023 2024 2025`) must always run **sequentially** — never in parallel threads/processes — because a single year's LP already uses several GB of RAM and concurrent year solves will OOM on most ISOs. The year loop in `runner.py` is intentionally sequential; do not parallelize it. Separate-invocation concurrency: cap at ~2 simultaneous runs for per-plant (`plant_level_fleet`) multi-zone LPs to stay within memory limits.
1. **Measured data is allowed only as a *reproducible physical/market input*, never as the *answer* — no pinning the backcast to actuals.** Real measured data may be used when it is grounded in physics or market design **and** enters as a formulaic input that would regenerate for a future year and respond to changed conditions in a forecast — e.g. unit outage windows (a physical availability event), delivered fuel prices, plant-specific CEMS emission rates, a measured ancillary-service power reservation. The admissibility test is: **could this same quantity be produced for a forward year from forward drivers, and would it respond to changed conditions?** If yes, it is a legitimate input *even in backcast mode*. What is **forbidden** is feeding a measured *outcome* back in to force the backcast to match: pinning a unit to its observed CEMS generation, adding an offset/haircut/adder tuned to the price or volume residual, or rescaling an input so the model's *output* lands on the actuals. Those have no forward analogue — the dispatch being validated is then not the dispatch being forecast, so the "fit" measures plumbing, not skill. A measured input that fails the test may exist only as an explicitly-labelled, default-**off** diagnostic probe; it must never be enabled in a keeper or quoted as evidence of forecast skill. (This sharpens #1 and #11; the concrete forecast-vs-backcast line is methodology spec §1.7, and the live overlay inventory is `docs/backcast-measured-data-audit-2026-06.md`.)
1. **Prefer accurate/measured data over estimates whenever it's available — never revert to an estimate just because it fits the backcast better.** If swapping a hand estimate for real data (a measured TTC/GTC limit, metered load, actual outages, real fuel prices, etc.) makes the backcast *worse*, that is a signal that **something else in the model is miscalibrated** and the estimate was silently compensating for it. Treat the worse fit as a discovered bug: keep the accurate input, find and fix the real root cause (offer curves, must-run, passthrough sigmoids, fleet/zone assignment, etc.). Do **not** bury the error back inside an inaccurate input. The *only* exceptions — where an estimate may be kept — are when the accurate data is genuinely **misaligned to our representation** so that using it literally would make overall results *less* reflective of reality, e.g.: the data is defined on a different boundary than our zones (a single GTC that is one of several parallel paths our reduced network collapses into one link), a different time/area aggregation, or units/sign conventions that don't map. In those cases, document the misalignment explicitly in a comment and prefer a *reconciled* version of the real data over a pure guess. When in doubt, use the real data and open the root-cause investigation.
1. **Every completed backcast run goes on the dashboard — results live there, not in chat.** The moment a calibration run finishes (keeper *or* rejected probe), register it on the backcast results dashboard and commit+push it **in the same session it was produced** — use the `calibration-report` skill / `scripts/dashboard_add_run.py`, then `build_manifest.py`. The dashboard is the codebase-site pages — `docs/codebase-site/backcast-runs.html` (run explorer, `#iso=<ISO>&run=<id>`) and `docs/codebase-site/calibration-status.html` (all-ISO keeper summary, `#iso=<ISO>`); the old root `backcast-results.html` is a static redirect stub, never regenerated. The committed per-run files (`results/calibration/<name>/` bundle + `frontend/data/backcast/registry/<id>.json` + `runs/<id>.js` + changed `bench/`) are the deliverable; `manifest.js`/`benchmark.js` are deploy-workflow-owned and auto-refreshed at deploy. A run is **not "done" until its bundle and dashboard files are committed and pushed** — do not just narrate metrics in chat and move on. Honour the top-15-per-ISO retention (PJM labels `pjm N <keyword>`). Lead with the dashboard result; keep the prose minimal.
1. **Always solve and register ALL available backcast years in one bundle — never a single-year keeper.** Every multi-year ISO's calibration run covers every year the ISO can score, in a single `--year` invocation and a single bundle: **CAISO / PJM / NEISO / NYISO → `--year 2023 2024 2025`** (add new years as they land). A one-year solve (e.g. 2024-only) is permitted *only* as a throwaway diagnostic probe to isolate a single-year effect — it must **never** be registered on the dashboard as a keeper, and any 2024-only bundle found on the dashboard should be re-solved across all years or pruned. When re-gating or re-solving a keeper, reproduce its full year span, not just the year you happen to be studying.
1. **No floor without a window, a driver, and a forward story.** Every min-gen/commitment floor
    states (a) its external driver, (b) the hours it may bind and why, (c) how it regenerates in a
    forecast year. A floor binding in hours its own driver evidence says the class is offline
    (CT overnight CF ≈ 0) is a bug by definition, whatever it does to the residual.
1. **Commitment physics by parameters, not class names.** Bridge/commit eligibility gates on unit
    physics (`min_down_hours`, startup cost) — never a hard-coded class tuple. Fast-start units
    (min-down ≤ 2 h, startup < $30/MW) are never economically bridged beyond their min-down.
1. **One mechanism per phenomenon.** Before adding a floor/bridge, enumerate what already floors
    the same class (D-2 attribution) and replace or reconcile — never stack a new floor on the
    unexplained residual of an old one.
1. **Forced energy is budgeted.** A keeper fails if any merchant class dispatches > 30 %
    (peakers: > 10 %) of its energy at binding floors. Floors are commitment scaffolding, not the
    dispatch model.
1. **Every keeper carries a DOF ledger and an ablation twin.** The attestation lists each free
    parameter with its identification source; a zero-forcing ablation run is registered alongside.
    A residual that can only be closed by a tuned value is an open root-cause issue, not a parameter.
1. **Hold out data, and score it exactly once.** The designated holdouts — **2022 and H1-2026 —
    are under FULL quarantine: no solves, no scoring, and no data intake for those years**, until
    an ISO's calibration is declared complete (its marker in
    `frontend/data/backcast/calibration-complete.json`). At that moment the holdouts are scored
    **EXACTLY ONCE** with the frozen keeper configs — the required 2022/H1-2026 data intake
    (bench actuals, CAMPD unit-level, delivered fuel; the coverage gap is itemized in
    `docs/out-of-sample-results-2026-07.md` §1) happens *at that moment*, as step 1 of the
    one-shot validation, never before. The results are recorded whatever they are, and **no
    calibration change may respond to them** without designating a new never-touched holdout.
    Structural mechanism changes are still scored leave-one-year-out *within 2023–2025* before
    promotion. In-sample improvement with held-out degradation is overfitting, not skill. CI
    enforces the quarantine on every pull request (`.github/workflows/ci.yml`, `quarantine-gates`
    job): `scripts/legitimacy_diagnostics.py --keepers` and `scripts/audit_keepers.py --check` FAIL
    the PR if any registered bundle contains a solve year outside 2023–2025 before that ISO's
    calibration-complete marker exists.
1. **Derive scripts are frozen against residuals.** Measured-behaviour parameters (min-stable
    loads, drag hinges, sigmoid anchors, committed shares) re-derive only when their *source data*
    updates — never because a residual moved. Re-derivation commits must cite the data change.
1. **No off-registry tuning channels.** Every tunable that can change a solve appears in
    `ScenarioConfig`/`constants.py` and the run's `run_config.json` — no env-var knobs, no
    hardcoded per-plant dicts in `data/` modules, no `getattr` fallback literals in the offer path.
1. **Tuned curves never cross ISO boundaries.** A multiplier fitted on one ISO's residual is that
    ISO's; generic fallbacks carry neutral (1.0) bands. (Makes the existing informal rule
    CI-enforced; see D-9.)
1. **Deleted means deleted.** Deprecated fitted knobs are removed, not zeroed — a deprecated
    parameter that still parses is a re-armable answer key (the ORDC offset was re-swept *after*
    deprecation).

Rules 17–26 are the protective rules from `docs/model-legitimacy-audit-2026-07.md` §8 (numbered
**16–25 there** — this file gained rule 16, all-years-one-bundle, after the audit was written; a
doc reference to "audit rule N" maps to rule N+1 here). Rule 22 (holdouts) carries the owner's
strict-quarantine amendment, superseding the audit's original D-6/rule-21 wording.

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

0. Confirmed exits (`apply_confirmed_exits`, GATED `confirmed_exits_enabled` default-off) → 1. Announced retirements (`apply_announced_retirements`) → 2. Economic retirements (fuel-type-aware thresholds + reliability floor) → 3. Known additions → 4. CCS retrofit screen (existing gas-CC) → 5. Economic new entry → 6. dispatch with RPS as an LP constraint (shadow price feeds next year's entry screen)

**Confirmed vs announced retirements.** *Confirmed* exits — units bound by an enforceable public instrument (RTO deactivation acceptance, consent decree, statute, regulatory order, RMR end) — are the ONLY exogenous fossil exit channel: step 0 force-retires (or derates a plant-binned tranche by the exiting unit's MW) at the instrument date, any fuel, bypassing the reliability floor. Read forecast-forward from the `confirmed-retirements` registry (`data/raw/confirmed-retirements`, `data.confirmed_retirements.load_confirmed_exits`); GATED `confirmed_exits_enabled` (default **on**, flipped 2026-07-05 — owner sign-off once the registry covered all six ISOs and its two open primary-document caveats were resolved; `docs/handoffs/confirmed-retirement-plan-2026-07.md` §7), forecast-mode only; superseded rows (a counter-instrument suspends the exit) revert to the economic screen. *Announced* retirements (`apply_announced_retirements`, RC-3 rename of the old `apply_known_retirements`) honor an EIA-860 planned date: **for fossil this step is a default no-op** (`forecast_fossil_retirement_economic=True` — an announced fossil date is not a certainty; the economic screen governs its phaseout and the confirmed registry is its exogenous channel); non-fossil dates are honored only within the EIA-860 data horizon (`EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS`, default 5), and beyond it only when the unit is in the confirmed registry — so speculative 2040-2072 EOL placeholders stop force-retiring (the horizon gate activates with the confirmed channel, which is now on by default; setting `confirmed_exits_enabled=False` reverts to honoring all non-fossil dates, byte-identical to the pre-flip behavior). See `docs/handoffs/confirmed-retirement-plan-2026-07.md`.

Economic retirement screens **inframarginal energy margin** — `Σ (price − full variable cost) × dispatch`, threaded as `prior_results["mc_cost"]`, never gross revenue — against FOM-only going-forward cost, with per-fuel thresholds, now `ScenarioConfig` fields (not hardcoded): coal=1yr, gas_ct=2yr, gas_cc=3yr; coal FOM multiplier 1.3× for regulatory/ESG risk; reliability floor prevents thermal below (peak - firm_clean) × 1.15. Known additions are the EIA-860 proposed pipeline (`load_planned_additions`, construction-committed statuses, forecast mode only). RPS is **not** a force-build step — it's an annual LP constraint whose dual is the REC price (see methodology spec §1.4, §5).

CCS retrofit (§5.6): gas-CC units with ≥15 yr life left retrofit when simple payback beats remaining life; capped at 3 GW/yr/ISO, gated on `ccs_retrofit_available_year`.

Storage grows via an economics-based **value stack** (not compound growth): duration-sized arbitrage windows (net of cycling degradation) **plus** resource-adequacy capacity value, paid only in capacity markets via the per-ISO `MARKET_DESIGN` registry (energy-only ERCOT pays none; PJM/NYISO/ISO-NE/CAISO pay net-CONE × ELCC × saturation derate). ELCC rises with duration → tilts entry toward long-duration at high penetration. Build budget diversifies across techs (`STORAGE_TECH_BUILD_SHARE_CAP`); base-year fleet from `storage_deployment`, all later growth endogenous, capped per ISO. Toggles: `storage_capacity_value`, `storage_degradation`. (Methodology spec §5.5.)

Locational deliverability gate (`capacity_deliverability_limits`, GATED default off): reads each ISO's published capacity-deliverability parameters (PJM CETO/CETL, MISO LRR/LCR/CIL, NYISO LCR/TSL, ISO-NE LSR/MCL, CAISO LCR/MIC), crosswalks areas onto model zones, and (a) replaces the calibrated simultaneous-import scalar with the measured seam import limit where published (CAISO MIC → WECC_import), and (b) collapses the marginal capacity payment in RA-saturated zones across the retirement, new-entry, and storage-entry screens. Structural mechanism (rule #1). In a backcast only part (a) fires (no capacity evolution); the CAISO keeper enables it (`--capacity-deliverability-limits`, caiso-51, 2026-07-03) so the published MIC replaces the audit-flagged fitted 7,500 MW WECC cap. Part (b) remains unvalidated in any keeper. (Methodology spec §5.8; worked example `docs/capacity-deliverability-wiring.md`.)

## Dispatch & Commitment (per year)

Three LP solves (`runner.py`, `model/commitment.py`): **P0** base-cost (discover run lengths) → **P1** bid-cost (base + amortized startup markup, sets clearing prices) → **P2** optional commitment screen (`commitment_enabled`, default off) that decommits unprofitable CC/CT runs via an IRR hurdle + min-run/min-down + storage-weighted margin discount, with an adequacy backstop. Still pure LP — no MIP. **P1 — the no-commitment solve — is THE main run**: the production/forecast path and what every keeper is scored on. P2 is an opt-in diagnostic layer that never runs unless explicitly enabled (`commitment_enabled`, `ercot_as_aware_commitment`, or `caiso_ra_mustoffer`); it is not part of any default or recommended configuration (the ercot27 probe showed the AS-aware P2 adds broad price elevation and no scarcity-month signal — see the 2026-07-03 calibration-log entry).

## Fleet Representation

ERCOT default is **CAMPD per-plant binning** (`use_campd_bins=True`): one LP unit per plant, each split into must-run / committed / economic / peaking tranches forming a rising offer curve (coal take-or-pay + PRB sigmoid passthrough). See `docs/binning-methodology.md`. Other ISOs / `use_campd_bins=False` use legacy equal-width heat-rate bins.

## Naming Conventions

- Python: snake_case. Functions: verb_noun (solve_dispatch, evolve_fleet, load_eia_profiles).
- Single-letter vars only in LP construction: t=hour, g=generator, z=zone, s=storage, with comment.
- Feature branches: phase-N/description. Commits: imperative present tense.

## Git & Pushing (avoid the 413 push loop)

`git push` over this remote rejects large packs with **HTTP 413** and retries
just re-fail — do **not** burn turns looping on `git push`. The committed
dashboard payloads (`frontend/data/backcast/runs/*.js`, `bench/`) plus a stale
base make the pack too big. Workflow:

1. **Start fresh on main.** `git fetch origin main` then branch/rebase the work
   onto the latest `origin/main` so the push pack carries *only* your own new
   objects, not a divergent base.
2. **Push file-content commits via the GitHub MCP API, not git.** Use
   `mcp__github__push_files` (one call per logical change, **small commits** —
   a bundle's slim files + sidecar + run payload + bench in one call, docs/code
   in another). The API commits server-side and bypasses git's pack
   negotiation, so it never 413s regardless of payload size.
3. **Only fall back to `git push` for small, source-only commits** (no
   `runs/*.js`/bundle payloads). If a `git push` 413s once, switch to
   `push_files` — never retry the same large `git push` more than once.
4. Never hand-commit the deploy-workflow-owned data files (`manifest.js`,
   `benchmark.js`, `completeness.js`) or anything under the gitignored
   `docs/codebase-site/data/backcast/`; the Pages deploy regenerates them.

## Testing Pattern

Always test with trivial cases first: 1 gen, 1 zone, 24 hours. Then scale up.

## Reference Docs (in repo)

- `model-methodology-spec.md` — LP formulation, commitment, fleet/offer curves, capacity evolution, outage modelling, scenario architecture (THE SPEC)
- `market-sim-build-plan.md` — phase plan, extraction manifest, directory structure
- `docs/binning-methodology.md` — CAMPD per-plant binning & tranche offer curves (ERCOT default)
- `docs/parameter-citations.md` — every numeric input traced to a primary source
- `docs/multi-iso/` — protocol & status for adding ISOs beyond ERCOT
- `docs/calibration-log.md`, `docs/calibration-session-log.md` — calibration history
- **Code is the source of truth.** When docs and code disagree, fix the docs (run `/sync-docs`). When the methodology is genuinely ambiguous, the spec wins.