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
  config/    → scenarios.py (ScenarioConfig dataclass), constants.py, iso_configs.py (6-ISO topology), paths.py (on-disk path registry), reserve_config.py (reserve co-opt config), interchange_config.py (interchange/seam spec), capacity_area_crosswalk.py (ISO capacity-area↔zone crosswalk), plant_taxonomy.py (fuel/class taxonomy)
  data/      → eia_loader.py, fleet.py (CAMPD binning), renewables.py, fuel.py, outages.py, hydro.py, ownership.py, ownership_config.py, campd.py (CEMS loader), egrid.py, eia923.py (delivered fuel cost), coal.py, chp.py, cod_ramp.py (COD vintage ramp), confirmed_retirements.py, emission_rates.py (forward CO2-rate estimator), offer_curves.py, floor_mechanisms.py (D-2 floor attribution registry), zone_assignment.py, neighbor_price.py, gtc.py, local_capacity.py, capacity_deliverability.py, winter_fuel_inventory.py, hydrogen.py, nyiso_reserve_requirements.py (measured NYISO hourly reserve-requirement series), miso_reserve_requirements.py (measured MISO hourly cleared-reserve series), ramp_capability.py (measured per-plant ramp/fast-start capability intake)
  model/     → dispatch.py (LP core), commitment.py (3-solve UC screen), transmission.py, storage.py, capacity.py, ancillary.py (ERCOT AS revenue)
  policy/    → ira.py, rps.py, carbon.py, eac.py, constraints.py, cap_and_trade.py (unified carbon-program resolver)
  results/   → cache.py, outputs.py, emissions.py, export.py, calibration.py, plant_financials.py, rcpf.py (NYISO RCPF scarcity overlay), scarcity.py (ERCOT ORDC scarcity overlay), evolution_ledger.py (persisted per-year capacity ledger)
  pipeline/  → spec.py, kwargs.py, prior.py, result.py, backcast_config.py (backcast ScenarioConfig builder), commitment.py (shared P2 commitment pass), solve.py (shared P0/P1 energy solve loop) — shared per-year solve-core typed contracts (orchestrator-unification)
  ensemble.py         → weather-year / scenario ensemble aggregation
  matrix.py           → deterministic scenario-matrix runner (PB-0/1.1)
  uncertainty.py      → multivariate forecast-uncertainty sampler (PB-2)
  structural_prior.py → structural-error prior + convolution (PB-3)
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
1. **Every completed backcast run goes on the dashboard — results live there, not in chat.** The moment a calibration run finishes (keeper *or* rejected probe), register it on the backcast results dashboard and commit+push it **in the same session it was produced** — use the `calibration-report` skill / `scripts/dashboard_add_run.py`, then `build_manifest.py`. The dashboard is the codebase-site pages — `docs/codebase-site/backcast-runs.html` (run explorer, `#iso=<ISO>&run=<id>`) and `docs/codebase-site/calibration-status.html` (all-ISO keeper summary, `#iso=<ISO>`); the old root `backcast-results.html` is a static redirect stub, never regenerated. The committed per-run files (`results/calibration/<name>/` bundle + `frontend/data/backcast/registry/<id>.json` + `runs/<id>.js` + changed `bench/`) are the deliverable; the Pages deploy workflow rebuilds `manifest.js`/`benchmark.js`/`completeness.js` from the sidecars at deploy time, so a registered run shows on the LIVE dashboard once the deploy runs (committing those generated files is optional, local-`file://`-preview only — see Git & Pushing §3). A run is **not "done" until its bundle and dashboard files are committed and pushed** — do not just narrate metrics in chat and move on. Honour the top-15-per-ISO retention (PJM labels `pjm N <keyword>`). Lead with the dashboard result; keep the prose minimal.
1. **Always solve and register ALL available backcast years in one bundle — never a single-year keeper.** Every multi-year ISO's calibration run covers every year the ISO can score, in a single `--year` invocation and a single bundle: **CAISO / PJM / NEISO / NYISO / MISO → `--year 2023 2024 2025`** (add new years as they land). A one-year solve (e.g. 2024-only) is permitted *only* as a throwaway diagnostic probe to isolate a single-year effect — it must **never** be registered on the dashboard as a keeper, and any 2024-only bundle found on the dashboard should be re-solved across all years or pruned. When re-gating or re-solving a keeper, reproduce its full year span, not just the year you happen to be studying.
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
    (peakers: > 15 %) of its energy at binding floors. Floors are commitment scaffolding, not the
    dispatch model. *Owner amendment 2026-07-06 (rubric v2.1):* peaker cap raised 10 → 15 %, and
    this budget — plus the C7 diurnal-shape gate — applies only to classes whose annual energy
    (max of model and actual, so forcing can't hide a class below the line) is ≥ 2 % of total ISO
    load; smaller classes are reported by the D-1/D-2 diagnostics but never gated — trivial-class
    shape/forcing is not worth structural work. *Owner amendment 2026-07-07 (rubric v2.2 —
    grounded-above-budget escalation):* the 15 %/30 % caps and the 2 % floor are unchanged, but a
    material class **above** its cap is no longer an automatic fail. It escalates to a conditional
    pass on **provenance + shape**: it passes iff (a) every binding non-exempt mechanism forcing it
    clears **D-4 off-window binding** (binds only in its driver-justified window — a mechanism with
    no declared window fails, per rule 12), **and** (b) its **D-1** diurnal profile clears the gates
    (`profile_r`/`cv_ratio`). Rationale: forcing can be legitimate past the budget when it is a real
    grid/RA/AS driver that reproduces the observed dispatch — *as much as needed* may be forced on a
    class if it is structurally grounded and shape-faithful; what the gate now targets is forcing
    whose **shape or window doesn't match reality** (the "forcing variables are wrong" signal). A
    grounded pass is a **clean PASS surfaced as a report note, never a caveat**; a miss FAILs as a
    forcing shape/provenance mismatch. This is scored entirely from the committed
    `legitimacy_diagnostics.json` (D1/D2/D4 rows + gates), so it is scorer-only — no re-solve, no
    bundle regen, and existing keepers re-score in place (the change only *relaxes* C8: below-cap is
    unchanged, above-cap gains a pass-path). **To actually ground a specific keeper's over-budget
    class**, its mechanism needs a cited `D4_WINDOWS` entry in `scripts/legitimacy_diagnostics.py`
    and that bundle re-generated so the D-4 row exists; and any mechanism-change-driven verdict flip
    is scored leave-one-year-out within 2023–2025 before the keeper is promoted.
1. **Every keeper carries a DOF ledger.** The attestation lists each free parameter with its
    identification source. A residual that can only be closed by a tuned value is an open
    root-cause issue, not a parameter. *Amended 2026-07-14 (owner): the zero-forcing ablation
    twin is NO LONGER required — keepers no longer build or register a paired zero-forcing run.
    Forcing-legitimacy now rests on the DOF ledger plus the D-2 / `legitimacy_diagnostics.json`
    mechanism attribution (the C8 forced-share gate and D-4 off-window-binding check) alone.
    Already-registered twins may remain on the dashboard as historical artifacts; no new twin is
    produced (probe, candidate, or keeper).*
1. **Hold out data across three tiers — train, validation, locked test — and never let a
    locked-test result re-enter tuning.** *Amended 2026-07-07 (owner) — supersedes the earlier
    two-window "holdouts are 2022 + H1-2026, score once" wording with an explicit
    train/validation/test split (`docs/handoffs/holdout-policy-memo-2026-07.md`); the quarantine
    machinery in the standing clauses below is unchanged.* The tiers:
    - **Train / calibration = 2023–2025.** The ONLY years tuned against. Every keeper is built and
      scored here, all three in one bundle (rule 16).
    - **Validation holdout = 2022**, extensible backward as a staged ladder (2022 → 2020–2022 →
      earlier as data lands and is authorized). **Iterable.** After an ISO's calibration-complete
      marker exists, 2022 may be solved and scored, and a miss MAY send you back to re-tune
      2023–2025 and re-solve — that is its purpose (model selection). Because it is iterated
      against, a validation number is selection evidence, **NOT** a certified out-of-sample skill
      number, and must never be quoted as one.
    - **Locked test = 2019 and H1-2026.** **Touch-once, ever.** Scored EXACTLY ONCE per ISO with
      the frozen keeper config; the result is recorded whatever it is. **No calibration change may
      respond to a locked-test result** without designating a new never-touched year as its
      replacement. This is the honest out-of-sample number. (2019 is the clean-regime test;
      H1-2026 is the forward-edge test. Pre-2020 years exercise a structurally different fleet —
      grade against regime drift, not raw MAE.)
    - **Crossover window = 2024–H1 2026** is scored in BOTH modes — backcast (measured overlays)
      and forecast (forward drivers) — against the same actuals, to measure the backcast→forecast
      input gap. Diagnostic, not a locked test; its forecast side uses no measured actuals so it is
      unrestricted (see the 2026 clause below).

    Standing quarantine clauses (from the 2026-07-06 amendment — G-17 Option 2,
    `docs/handoffs/holdout-policy-memo-2026-07.md` §(e) — unchanged except tier wording):
    - **Data intake is permitted** for any out-of-training period (validation or locked), but ONLY
      under explicit, session-logged owner authorization, and validation of intaken data is no-LP
      only (byte-identity / loader-resolvability checks — never a dispatch solve). Codifies the
      authorized 2026-07-04 ERCOT/PJM intake (PRs #1298/#1300/#1304); each further intake (per-ISO,
      per-window — now including 2018–2021, itemized in `docs/out-of-sample-results-2026-07.md` §1)
      requires its own authorization.
    - **No solve, no scoring, no registration** may touch ANY out-of-training year (2022, 2019,
      ≤2021, H1-2026) — no backcast, no diagnostic probe, no "throwaway" solve — until the ISO's
      calibration-complete marker exists in `frontend/data/backcast/calibration-complete.json`.
    - **2026 forecast runs are permitted:** forecast-mode runs (`ScenarioConfig.mode="forecast"`)
      span 2026+ and use no measured H1-2026 actuals (overlays are backcast-only by construction) —
      NOT restricted. Only a *backcast* of H1-2026 on real data, or scoring output against measured
      H1-2026 actuals, is quarantined.
    - Structural mechanism changes are still scored leave-one-year-out within 2023–2025 before
      promotion. In-sample gain with held-out degradation is overfitting, not skill.
    Enforcement: CI (`.github/workflows/ci.yml`, `quarantine-gates` job) fails any PR whose
    registered bundle contains a solve year outside 2023–2025 before that ISO's marker exists, and
    `scripts/run_calibration_full.py` hard-fails any `--year` outside {2023, 2024, 2025} unless
    `--holdout-authorized` is passed AND the target ISO carries a calibration-complete marker. The
    CI gate is tier-agnostic — it enforces the marker, not the validation/locked distinction, which
    is a discipline clause above (a locked-test year re-solved after its one-shot is a governance
    breach, not a CI failure).
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
1. **Core files are never bulk-rewritten over the API, and Sonnet never edits infrastructure.**
    *(Owner order 2026-07-15, after a Sonnet session truncated `constants.py` 6,368 → 33 lines
    via a response-budget-clipped `push_files` full-file rewrite, and five follow-up "restore"
    commits merged fragments — 0 / 500 / 1,020 / 1,000 lines — onto main.)* Two binding halves:
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

Rules 17–26 are the protective rules from `docs/model-legitimacy-audit-2026-07.md` §8 (numbered
**16–25 there** — this file gained rule 16, all-years-one-bundle, after the audit was written; a
doc reference to "audit rule N" maps to rule N+1 here). Rule 22 (holdouts) carries the owner's
strict-quarantine amendment, further amended 2026-07-07 into the three-tier
train(2023–2025)/validation(2022)/locked-test(2019 + H1-2026) split, superseding the audit's
original D-6/rule-21 wording.

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

**Confirmed vs announced retirements.** *Confirmed* exits — units bound by an enforceable public instrument (RTO deactivation acceptance, consent decree, statute, regulatory order, RMR end) — are the ONLY exogenous fossil exit channel: step 0 force-retires (or derates a plant-binned tranche by the exiting unit's MW) at the instrument date, any fuel, bypassing the reliability floor. Read forecast-forward from the `confirmed-retirements` registry (`data/raw/confirmed-retirements`, `data.confirmed_retirements.load_confirmed_exits`); GATED `confirmed_exits_enabled` (default **on**, flipped 2026-07-05 — owner sign-off once the registry covered all six ISOs and its two open primary-document caveats were resolved; `docs/handoffs/confirmed-retirement-plan-2026-07.md` §7), forecast-mode only; superseded rows (a counter-instrument suspends the exit) revert to the economic screen. **Hindcast information gate (rule 27 lane, RC-1B 2026-07-15):** in hindcast mode confirmed rows and reversal suppressions apply only when `instrument_date` ≤ the vintage cutoff. *Announced* retirements (`apply_announced_retirements`, RC-3 rename of the old `apply_known_retirements`) honor an EIA-860 planned date: **for fossil this step is a default no-op** (`forecast_fossil_retirement_economic=True` — an announced fossil date is not a certainty; the economic screen governs its phaseout and the confirmed registry is its exogenous channel); non-fossil dates are honored only within the EIA-860 data horizon (`EIA860_OPERABLE_VINTAGE + NONFOSSIL_ANNOUNCED_HORIZON_YEARS`, default 5), and beyond it only when the unit is in the confirmed registry — so speculative 2040-2072 EOL placeholders stop force-retiring (the horizon gate activates with the confirmed channel, which is now on by default; setting `confirmed_exits_enabled=False` reverts to honoring all non-fossil dates, byte-identical to the pre-flip behavior). See `docs/handoffs/confirmed-retirement-plan-2026-07.md`.

Economic retirement screens the **attainable (pro-forma) inframarginal margin** — `Σ_t max(0, price − full variable cost, reserve price) × pmax × availability`, the Potomac-SOM net-revenue construction (`mc_cost` threaded via `prior_results`; never gross revenue, never realized dispatch — realized dispatch structurally misses the post-solve ORDC adder's scarcity rent) — against FOM-only going-forward cost, with per-fuel thresholds, now `ScenarioConfig` fields (not hardcoded): coal=1yr, gas_ct=2yr, gas_cc=3yr; coal FOM multiplier 1.3× for regulatory/ESG risk. The hourly reserve-price signal (`screen_reserve_value_enabled`, default on) is the co-opt's own reserve duals under `ercot_thermal_as_endogenous`, else the ORDC scarcity adder (RTORPA/RTOFFPA pay reserves the same ORDC price — Nodal Protocols §6.5.7.5); when present it is the SOLE thermal AS pricing (rule 19). Accredited reliability floor: `accredited_firm_capacity_mw` (UCAP/ELCC, incl. wind/solar pools + storage ELCC) vs `peak × (1 + PLANNING_RESERVE_MARGIN_BY_ISO)` — one requirement shared with the build backstop; cheapest-firm-adequacy retention (CO₂ tie-break), `floor_retention_log` attribution. Announced dates reversed outright by a public counter-instrument (registry rows ALL superseded — Byron/Dresden vs IL CEJA) are ignored by the announced channel regardless of `confirmed_exits_enabled` (`load_announced_reversal_plants`). Known additions are the EIA-860 proposed pipeline (`load_planned_additions`, construction-committed statuses, forecast mode only). RPS is **not** a force-build step — it's an annual LP constraint whose dual is the REC price (see methodology spec §1.4, §5).

CCS retrofit (§5.6, redesigned W2-C — national-ces plan §11): gas-CC units with ≥15 yr life left are screened jointly with retirement (step 2 runs first, so a distressed CCGT whose retrofit continuation clears converts instead of exiting; retire only when both continuations fail). The screen values the retrofit as the **incremental uplift over the best unabated state** — attainable inframarginal margins at the post-retrofit cost basis (HR penalty + VOM adder + transport, residual carbon; utilization endogenous, no fixed CF) with the certificate (`max(eac_price_gas_cc_ccs, premium × capture-fraction credit)`, cesa_ci nets the unabated partial credit) and §45Q (stacks — separate instrument) as bid offsets. §45Q is eligibility-gated on `ira_ccus_45q_last_year` at the commit year and paid for `min(ira_45q_credit_window_years, remaining life)` years (statutory 12; `None` = indefinite-extension scenario) via a two-segment payback; the same window levelizes the new-build CCS LCOE's 45Q term. Capped at 3 GW/yr/ISO (cap-displaced units fall back to the unabated loss counter), gated on `ccs_retrofit_available_year`, annual re-screen.

Storage grows via an economics-based **value stack** (not compound growth): duration-sized arbitrage windows (net of cycling degradation) **plus** resource-adequacy capacity value, paid only in capacity markets via the per-ISO `MARKET_DESIGN` registry (energy-only ERCOT pays none; PJM/NYISO/ISO-NE/CAISO pay net-CONE × ELCC × saturation derate). ELCC rises with duration → tilts entry toward long-duration at high penetration. Build budget diversifies across techs (`STORAGE_TECH_BUILD_SHARE_CAP`); base-year fleet from `storage_deployment`, all later growth endogenous, capped per ISO. Toggles: `storage_capacity_value`, `storage_degradation`. (Methodology spec §5.5.)

Locational deliverability gate (`capacity_deliverability_limits`, GATED default off): reads each ISO's published capacity-deliverability parameters (PJM CETO/CETL, MISO LRR/LCR/CIL, NYISO LCR/TSL, ISO-NE LSR/MCL, CAISO LCR/MIC), crosswalks areas onto model zones, and (a) replaces the calibrated simultaneous-import scalar with the measured seam import limit where published (CAISO MIC → WECC_import), and (b) collapses the marginal capacity payment in RA-saturated zones across the retirement, new-entry, and storage-entry screens. Structural mechanism (rule #1). In a backcast only part (a) fires (no capacity evolution); the CAISO keeper enables it (`--capacity-deliverability-limits`, caiso-51, 2026-07-03) so the published MIC replaces the audit-flagged fitted 7,500 MW WECC cap. Part (b) remains unvalidated in any keeper. (Methodology spec §5.8; worked example `docs/capacity-deliverability-wiring.md`.)

## Dispatch & Commitment (per year)

**P0 and P1 are the only two passes** (`runner.py`, `model/commitment.py`): **P0** base-cost (discover run lengths) → **P1** bid-cost (base + amortized startup markup, sets clearing prices). **P1 is THE main run**: the production/forecast path and what **every run is scored on**. Pure LP — no MIP.

**P2 is ARCHIVED — a legacy artifact kept intact as a last resort, never a calibration option.** The former third solve (`commitment_enabled` / `ercot_as_aware_commitment`, the economic commitment screen that decommits unprofitable CC/CT runs via an IRR hurdle + min-run/min-down + adequacy backstop) is hidden from the calibration CLI and gated: its flags (`--commitment`, `--ercot-as-aware-commitment`, `--run-p2`, `--no-coal-p2`, `--persist-p2-state`, `--class-commitment-overrides`) error unless `--enable-legacy-p2` is passed (both `scripts/run_calibration_full.py` and `scripts/run_calibration.py`). No keeper uses it; it is not part of any default or recommended configuration (the ercot27 probe showed the AS-aware P2 adds broad price elevation and no scarcity-month signal — 2026-07-03 calibration-log entry). The machinery (`pipeline/commitment.py::run_commitment_pass`) stays in place for the `--enable-legacy-p2` path.

**CAISO RA must-offer bridge is P1-native** (`caiso_ra_mustoffer`, CAISO default-on). It used to run *through* P2; since P2 is archived and P1 scores better, the bridge is now applied as a `min_gen` floor **before** the single P1 solve — detected from the base-cost **P0** run pattern (`pipeline/commitment.py::caiso_ra_p1_floor_fleet` / `build_caiso_ra_p1_prep`, injected at the P0→P1 seam in `pipeline/solve.py::run_energy_solve`, reusing `model/commitment.py::caiso_ra_mustoffer_min_gen`). So CAISO keeps its RA structure and is scored on P1. It no longer triggers a P2 pass.

**ERCOT gas commitment bridge is the same P1-native construction behind its own gate** (`ercot_gas_commitment_bridge`, default off, ERCOT-only — ERCOT-63, 2026-07-12). The ISO-neutral detector scoped to merchant gas-CC only (CT is physics-inert for the economic leg, ST_GAS is owned by its own drag mechanism — rule 19), `min_load_frac` = the measured committed-CC LSL/HSL cap-weighted p50 (0.574, 60-Day DAM disclosure 2023-2025), economic ≥ min-down bridging on the startup-restart inequality at the model's own P0 duals, bounded to one DA operating day; the CAISO startup-aware screen is deliberately not exposed (dropped with cause — `docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §7). D-2 id `gas_commitment_bridge` (17). Supplies the committed-STATE half of the ERCOT trough/spread circle; `ercot_offer_surface_lowcurve` stays default-off (the tranche-wide LSL markdown is probe-refuted even in composition with the state), and the FLOOR-SCOPED variant `ercot_offer_surface_lowcurve_floorscoped` (ERCOT-64 — the measured LSL bid only in the bridge's own floored plant-hours, sharing ONE floor computation with the fleet hook via `pipeline/commitment.py::build_ercot_gas_bridge_p1_preps`) is probe-adjudicated **provably inert** (the bridge floor clips at the committed-tranche bound, so the markdown's whole window is pinned — diagnosis §8) and also stays default-off. The LSL price-side enumeration is closed, and ERCOT-65 (2026-07-13) closed the negative-price-epoch pair too: ERCOT wind already bids the flat −$26 PTC on every MW (`compute_dispatch_credits` — never a $0 floor), the honest EIA-860 vintage scoping (`wind_ptc_vintage_offers`, default off) is probe-adjudicated dispatch-byte-inert (only the Panhandle epoch dual moves, −26 → −27), arming `negative_renewable_offers` with the CAISO $20 REC value is rule-25 refused, and the WP-B `ercot_wtx_curtailment_driver` turned out to be LIVE in the keeper all along (the `prb_overrides` channel stomps the explicit kwarg; run_config recorder defect fixed + keeper records corrected 2026-07-13) — and a ceiling-clipped variable can never price an epoch. The trough/spread lane is AT FRONTIER (draft block in the 2026-07-13 log entry, owner sign-off pending); the remaining named lever is the West/Panhandle topology split (its own charter). See diagnosis §9.

## Fleet Representation

ERCOT default is **CAMPD per-plant binning** (`use_campd_bins=True`): one LP unit per plant, each split into must-run / committed / economic / peaking tranches forming a rising offer curve (coal take-or-pay + PRB sigmoid passthrough). See `docs/binning-methodology.md`. Other ISOs / `use_campd_bins=False` use legacy equal-width heat-rate bins.

## Naming Conventions

- Python: snake_case. Functions: verb_noun (solve_dispatch, evolve_fleet, load_eia_profiles).
- Single-letter vars only in LP construction: t=hour, g=generator, z=zone, s=storage, with comment.
- Feature branches: phase-N/description. Commits: imperative present tense.

## Git & Pushing (API-only — never `git push`)

**Rule: always push via the GitHub MCP API (`mcp__github__push_files`), never
`git push`.** `git push` over this remote rejects large packs with **HTTP 413**
and retries just re-fail — do **not** attempt `git push` at all, not even for
small source-only commits. `push_files` commits server-side and bypasses git's
pack negotiation, so it never 413s regardless of payload size. Workflow:

1. **Start fresh on main.** `git fetch origin main` then branch/rebase the work
   onto the latest `origin/main` so your commits carry *only* your own new
   objects, not a divergent base.
2. **Push every commit via `mcp__github__push_files`** — one call per logical
   change, **small commits** (a bundle's slim files + sidecar + run payload +
   bench in one call, docs/code in another). This is the only push path; do not
   fall back to `git push`.
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
4. **Verify after push (rule 27).** Any `push_files` call that touches a source file ≥300
   lines is followed immediately by a blob verification (fetch the pushed file, compare line
   count + hash to local) before the next commit. Full-file rewrites of large existing files
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
  via `mcp__github__push_files` (the API-only path above) — not a CI job.
- **Scheduled (`cron`) workflows spend money with nobody watching.** Do not add
  one without explicit owner sign-off, and prefer `workflow_dispatch`-only.

## Testing Pattern

Always test with trivial cases first: 1 gen, 1 zone, 24 hours. Then scale up.

## Reference Docs (in repo)

- `model-methodology-spec.md` — LP formulation, commitment, fleet/offer curves, capacity evolution, outage modelling, scenario architecture (THE SPEC)
- `market-sim-build-plan.md` — phase plan, extraction manifest, directory structure
- `docs/binning-methodology.md` — CAMPD per-plant binning & tranche offer curves (ERCOT default)
- `docs/parameter-citations.md` — every numeric input traced to a primary source
- `docs/multi-iso/` — protocol & status for adding ISOs beyond ERCOT
- `docs/calibration-log.md`, `docs/calibration-session-log.md` — calibration history
- `docs/forecast-development-plan-2026-07.md` — THE forecast program (Forecast Finalization Program): tier ladder, lanes/waves, prompt pack, rubric charter. All prior forecast plans are superseded as coordination docs by it (its §9 migration ledger).
- **Code is the source of truth.** When docs and code disagree, fix the docs (run `/sync-docs`). When the methodology is genuinely ambiguous, the spec wins.
