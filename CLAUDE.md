# Market Simulation Model — Claude Code Instructions

Concise answers: lead with the result, expand only when asked. Copy-paste
artifacts (handoff prompts, commands, configs, commit messages) go whole, in
one fenced block, never built up across turns.

**Where things are.** This file holds the rules and the shape of the model.
The procedure a calibration session follows is `docs/RUNBOOK.md`. The rule
genealogy (every amendment, incident and owner ruling behind a rule) is
`docs/governance/rule-history.md`; cite rule IDs, not history, in code and docs.
Session records (FINDING / PRECOMMIT / RESULT / ...) live under
`docs/records/<lane>/`; git history is the record for anything pruned.

## What this is

LP-based electricity market dispatch simulator: forecast 2026–2050, with a
historical backcast mode for calibration. Nine regions share one ISO-agnostic
LP (`config/iso_configs.py`): ERCOT (the calibrated reference), CAISO, PJM,
MISO, NYISO, NEISO, SPP, NWPP (a WECC balancing-authority pool) and SOCO (a
single BA, no LMP market). Hourly 8760 dispatch, parameterized scenarios.

**Forecast vs backcast** is the explicit `ScenarioConfig.mode` field, never
inferred. Historic overlays (CAMPD outage windows, F923 delivered fuel,
same-year plant CEMS rates, weather-year pinning) are backcast-only; the
forecast methodology never reads them. Forecast-year emission rates for
existing units derive from multi-year CAMPD history conditioned on simulated
operation — a rule-13-admissible input, not an overlay.

## Stack

Python 3.11+, HiGHS via `highspy`, numpy, scipy.sparse, pandas, pyarrow,
pydantic, pyyaml. **FORBIDDEN:** Pyomo, PuLP, scipy.optimize, Numba. Direct CSC
matrix → HiGHS only. `uv sync` is the only install route (`pyproject.toml`
pins the numeric stack exactly; `pip install -e .` resolves a different solver).

## Architecture

```
src/market_sim/
  config/    → ScenarioConfig, constants, 9-region topology, path registry, reserve/interchange specs, taxonomy
  data/      → source loaders & derived inputs (demand, fleet/CAMPD binning, renewables, fuel, outages, hydro, emissions, offers)
  model/     → the ISO-agnostic LP: dispatch (duals = price), commitment, transmission, storage, capacity evolution, ancillary
  policy/    → IRA, RPS, carbon / cap-and-trade, EAC, constraints
  results/   → caching, outputs, emissions, export, calibration scoring, scarcity overlays, evolution ledger
  pipeline/  → shared per-year solve core (spec, kwargs, prior, backcast_config, commitment, solve)
  ensemble / matrix / uncertainty / structural_prior → forecast-uncertainty layer
  runner.py  → main orchestrator (P0→P1 solve loop, year evolution)
tests/       → pytest, mirrors src/ (docs/testing.md: lanes, marks, helpers)
scripts/     → standing entry points only (calibration / hindcast / forecast runners, scoring, dashboard, governance)
  data/      → fetch_* / curate_* / derive_* / build_*     lib/ → shared helpers     probes/ → only probes live code names
data/raw/    → immutable source downloads; every path resolves through config/paths.py
data/clean/  → curated Parquet (derived, gitignored; `scripts/regenerate_clean.py --solve-profile <ISO>`)
data/dictionary/ → the data contract (schema/<datatype>.schema.yaml + generated data-dictionary.md)
docs/codebase/   → per-module code reference (the full inventory behind the tree above)
```

## Non-negotiable rules

Stable IDs; ordinals never renumber. Full text and genealogy of every
amendment: `docs/governance/rule-history.md`.

1. `[R-STRUCT]` **Right market structure first, offer-curve tuning second; backcast fit is not the objective.** A structurally real mechanism stays in even if the fit worsens (then fix the root cause). Never reach a number through a mechanism that is not real (a fitted adder, a load proxy, a haircut tuned to the residual). A keeper is the most structurally faithful run, not the lowest MAE. **One authorized price-tuning channel** (owner, 2026-09-05): the registered `offer_curve_by_group` band multipliers (`committed` / `econ_low` / `econ_high` / `peak`) may be tuned on price, provided (a) only those bands — never `phys_*`, the structural shares, or any new adder/offset/haircut; (b) one value across every scored year; (c) set ex ante in the PRECOMMIT and never swept against the gates; (d) merit-order effects are intended; (e) declared in the attestation's `authorized_price_tuning` block and ledgered as a free parameter (rule 21).
2. `[R-VECTOR]` **No Python loops over hours in LP construction.** np.tile / np.repeat / sparse.kron / block_diag.
3. `[R-RENEW-VAR]` **Renewables are decision variables** (MC = 0, upper bound CF × capacity), never netted from demand.
4. `[R-DUALS]` **Prices are the LP duals** on the energy-balance rows. No separate pricing model.
5. `[R-NO-MAGIC]` **No magic numbers.** Every value comes from ScenarioConfig or constants.py with a citation.
6. `[R-SOA]` **Struct-of-arrays before LP construction.** Pydantic → FleetArrays; the builder touches arrays and scalars only.
7. `[R-PARQUET]` **Parquet results, one file per scenario-year, check-before-run caching.**
8. `[R-8760]` **Full 8760 hours always.** No representative days or weeks.
9. `[R-EPSILON]` **Storage tiebreaker ε = 0.001 $/MWh** on charge + discharge.
10. `[R-ONE-PASS]` **One-pass capacity evolution.** No within-year convergence iteration.
11. `[R-DOCSTRING]` **Every public function and module has a docstring.**
12. `[R-PARALLEL]` **Independent solves run in parallel, years within one run sequentially.** A year's LP uses several GB; ≤ 2 concurrent per-plant multi-zone runs per box.
13. `[R-MEASURED]` **Measured data is a reproducible physical/market input, never the answer.** Admissible iff the same quantity could be produced for a forward year from forward drivers and would respond to changed conditions (outage windows, delivered fuel, CEMS rates, an AS reservation). Forbidden: pinning a unit to observed generation, an offset/haircut/adder tuned to a residual, rescaling an input so the output lands on actuals. The only exception is rule 1's offer-band channel. A measured input that fails the test exists only as a default-off, labelled diagnostic probe.
14. `[R-ACCURATE]` **Prefer measured data over estimates; never revert to an estimate because it fits better.** A worse fit after swapping in real data is a discovered bug elsewhere. The only exception: data defined on a boundary/aggregation that does not map to our representation — then document the misalignment and use a reconciled form of the real data.
15. `[R-DASHBOARD]` **Every completed backcast run is registered on the dashboard in the session that produced it** (`docs/codebase-site/backcast-runs.html`, `calibration-status.html`; `scripts/promote_keeper.py` for keepers, `scripts/dashboard_add_run.py` for a probe). Retention is **keeper-only**: each ISO's dashboard and `results/calibration/` carry only its designated keeper run(s) (folded touchpoints included); everything else is pruned at the promotion that supersedes it. Keeper bundles commit their `hourly/` sidecars so later sessions read instead of replaying — since 2026-10-01 including `unit_marginal_<year>.parquet` for EVERY year, in every ISO (owner: *"Moving forward for all ISOs"*; card *"Slim layer"*): per-unit `mw`/`cap_mw`/P1 offer `mc` plus an int8 `marginal` flag, written by every solve (`scripts/lib/unit_marginal.py`; the full `unit_hourly`, 69–81 MB/yr for PJM, stays gitignored) and enforced at promotion by `scripts/promote_keeper.py` preflight (it derives the layer from `unit_hourly` when absent and refuses a new keeper with neither). Forecast-family runs go on the separate forecast dashboard via `scripts/register_forecast_run.py`, never the backcast registry.
16. `[R-ALLYEARS]` **A registrable run solves every year the ISO carries, in one bundle.** A single-year solve is a throwaway probe, never a keeper.
17. `[R-FLOOR-WINDOW]` **No floor without a window, a driver and a forward story.** A floor binding where its own driver says the class is offline is a bug.
18. `[R-PHYSICS]` **Commitment physics by parameters, not class names** (`min_down_hours`, startup cost). Fast-start units are never bridged beyond their min-down.
19. `[R-ONE-MECH]` **One mechanism per phenomenon.** Enumerate what already floors a class (D-2) before adding another; replace or reconcile, never stack.
20. `[R-FORCED-BUDGET]` **Forced energy is budgeted.** A keeper fails if a merchant class ≥ 2 % of ISO load dispatches > 30 % (peakers > 15 %) of its energy at binding floors — unless every binding mechanism clears D-4 (binds only in its declared window) and the class's D-1 diurnal profile clears the gates, which is a clean conditional pass. Scored from the committed `legitimacy_diagnostics.json`.
21. `[R-DOF]` **Every keeper carries a DOF ledger** (`scripts/build_dof_ledger.py`): each free parameter with its identification source. A residual closable only by a tuned value is an open root-cause issue, not a parameter — except the rule-1 authorized band multiplier, which is ledgered with the ruling as its source. No zero-forcing ablation twin is required.
22. `[R-C3C]` **A lone C3c failure is an auto-ledgered caveat that does not downgrade the determination.** Guards: lone failure only (in 2023–2025; dropped for out-of-training years), governance (C6) must pass, supporting tier only, never a PASS. Every other caveat route still downgrades. There is no holdout regime: any year may be solved, scored and registered, and no year is a certified out-of-sample number. `calibration-complete.json` survives only as the keeper designation and the forecast program's gate-(a) input.
23. `[R-FROZEN-DERIVE]` **Derive scripts are frozen against residuals.** Measured-behaviour parameters re-derive only when their source data updates; the commit cites the data change.
24. `[R-REGISTRY]` **No off-registry tuning channels.** Every solve-affecting tunable is in ScenarioConfig/constants.py and the run's `run_config.json` — no env-var knobs, per-plant dicts in `data/`, or `getattr` fallbacks in the offer path.
25. `[R-ISO-SCOPE]` **Tuned curves never cross ISO boundaries.** Generic fallbacks carry neutral (1.0) bands.
26. `[R-DELETE]` **Deleted means deleted.** Deprecated knobs are removed, not zeroed; dead render paths are removed, not hidden.
27. `[R-PUSH]` **Core files are never bulk-rewritten over the API; Sonnet never edits infrastructure.** Edit locally and push the on-disk bytes; after any push touching a file ≥ 300 lines, verify the remote blob (line count + hash). Never commit a placeholder or partial version of an existing file. Sessions touching `src/`, `scripts/run_*|score_*`, `CLAUDE.md`, the spec or `.github/workflows/` are Opus or Fable. Enforced by `file-integrity-guard.yml` (`intentional-shrink` label for deliberate shrinks).
28. `[R-MECH-MATRIX]` **The mechanism matrix is the single test ledger.** Rows in `docs/codebase-site/data/mechanism-matrix.js`; per-ISO verdicts in `mechanism-matrix/<ISO>.js` (a lane edits only its ISO's shard); protocol and lever queues in `docs/mechanism-testing-matrix.md`. Check the queue before proposing a lever; never re-test a cell adjudicated `R`/`I`/`G` without new evidence; update the cell (verdict + citation) in the session that tests it; a PR adding a solve-affecting `ScenarioConfig` field adds its row and a cell in every shard (CI: `check_mechanism_matrix.py`). Verdicts are per-ISO; transfers enter the target ISO as `U`.
29. `[R-SCREEN]` **No screen year; a new config goes straight to the full span.** Surviving clauses: (b) no control solves — the incumbent keeper's committed bundle is the control, and HEAD drift is a zero-LP code audit (G-DRIFT: classify every changed hunk on the backcast path as INERT-with-reason or LIVE; only a LIVE hunk earns a control solve); (c) screen/control bundles never reach `main` (`.gitignore`, never `rm`). Zero-LP phase 0 remains the practice: compute what can be computed without an LP first.
30. `[R-TOUCHPOINT-FOLD]` **A touchpoint is the keeper on another year.** Stamp it to the keeper (`stamp_touchpoint_holdout.py`, done by `promote_keeper.py --fold`) so the Run Explorer folds it into the keeper's year selector — no separate card, no per-year prose, scores and charts only. The Calibration Status page carries the per-year ladder. **The ISO's determination covers every registered year** (keeper scopes plus every folded run, worst-of, per-run caveat budgets): a held-out year that reads NOT-YET makes the ISO NOT-YET. Computed once by `calibration_verdict.py::iso_determination`.
31. `[R-RETAIN]` **Never delete a solve's results until the owner has ruled on promotion.** A session recommends; it never destroys evidence. `.gitignore` discharges the keep-off-`main` duties, never `rm`. Delete only after the owner's ruling or on genuine disk exhaustion (stated, named). Ask the promotion question explicitly in the final report and say the bundles will not survive the container.
32. `[R-SHARD]` **Every solve runs in a shard; the orchestrating session never runs an LP.** The parent does phase 0, writes the PRECOMMIT, launches shards (`scripts/shard_prompt.py` emits the prompt; `source_revision` is a full 40-char SHA, never a branch; its own out-dir and branch; hard stops; forbidden commands; what to report; "a shard that stops with a clear report is a success, one that repairs infrastructure is a failure"), then composes, scores and registers once. One shard commit is ≤ 20 minutes of runtime; a shard approaching the budget with no artifact stops and reports. Memory: the runners call `ensure_solve_container` themselves; never `--no-container-preflight`, never read `free`.
33. `[R-SHARD-ARCHIVE]` **Archive a shard the moment the parent has fetched, checked out and verified its bundle** — never before, never while running. Record a leg by full SHA as provenance only: a shard branch is transport, not storage, is cut when the lane's PR merges, and cannot be deleted by a session (403). What must survive lands on `main` inside the registered keeper bundle before the PR merges; never mirror a shard branch to a side ref. Sweep and archive every shard before the session ends; name any left alive and why.
34. `[R-SHARD-PROMOTABLE]` **A solve that could ever be promoted pushes its full bundle**, including `dispatch/<year>_P1.parquet`, by a `.gitignore` negation of its own out-dir plus a plain `git add` (never `-f`). A screen is not an exception. Solve every year the ISO's keeper carries, one shard per year. Before archiving, the parent verifies `git ls-tree -r <sha> -- <bundle>` is non-empty **and** has the bytes in hand. The RESULT names where each bundle is on `main` and what a promotion would cost.
35. `[R-PROMOTE]` **A promotion is one command and is not done until the outgoing keeper's files are gone and the incoming keeper carries every year the ISO has run.** `scripts/promote_keeper.py` enforces the order: enumerate the registered year set, register, attest (the outgoing keeper's exceptions ledger carried forward, C3c entries re-measured; an entry that no longer applies is refused unless dropped with a recorded reason), designate, fold, re-key (`calibration-complete.json`, forecast gate-(a) stamp), rebuild status, audit every check but E13, prune the outgoing three stores (`prune_iso_runs.py`, own ISO only), audit strict, parity. A promotion that would shrink the year set is refused. Invariant (`audit_keepers.py` E13): every run registered for an ISO is its keeper or stamped to it.
36. `[R-YEAR-ISOLATION]` **A backcast year is solved alone, in its own shard container, from one `--years <year>` invocation; the parent composes the legs** (`scripts/probes/_miso260_compose_span.py`). No cross-year state or warm start (`MARKET_SIM_WARMSTART_XYEAR` / `MARKET_SIM_P1_BASIS_SEED` default off; setting one is a declared solve-affecting choice). A forecast is the opposite: its years run sequentially in one invocation because year N's builds set year N+1's fleet.

Rules 17–26 are the protective rules of `docs/model-legitimacy-audit-2026-07.md` §8 (numbered 16–25 there).

## LP

Flat column vector per ISO-year: P[g,t] | W[z,t] | S[z,t] | Chg[s,t] | Dis[s,t] | SOC[s,t] | Flow[l,t] | Slack[z,t] | Dump[z,t]; T = 8760.

`min Σ mc·P + ε·(Chg+Dis) + dis_cost·Dis + VOLL·Slack + dump_cost·Dump`, with
mc = heat_rate × fuel + vom + emission_rate × carbon_price + nox_rate × nox_price + …;
dis_cost = per-unit storage throughput adder; dump_cost = max(ε, −min(wind_mc, solar_mc) + ε).

Constraints: energy balance per zone-hour (thermal + wind + solar + discharge − charge + net_flow + slack − dump = demand); pmin ≤ P ≤ pmax × availability; 0 ≤ W/S ≤ CF × capacity; cyclic SOC with efficiencies; −TTC ≤ Flow ≤ TTC. Capacity value is locational when `capacity_deliverability_limits` is on (default off).

## Dispatch and commitment (per year)

**P0 base-cost → P1 bid-cost** are the only two passes; P1 is the run everything is scored on. Pure LP, no MIP. P2 is archived behind `--enable-legacy-p2`; no keeper uses it. Three P1-native commitment bridges inject a `min_gen` floor detected from P0 at the P0→P1 seam, each ISO-exclusive and sharing `model/commitment.py::caiso_ra_mustoffer_min_gen`: `caiso_ra_mustoffer` (CAISO, default on), `ercot_gas_commitment_bridge` (merchant gas-CC, min-load 0.574 measured), `nyiso_gas_commitment_bridge` (slow-start gas by unit physics, min-load CC 0.523 / ST_GAS 0.239 measured, plus a min-run leg; replaces the NYISO peak-window floor limbs, never stacked on them). A default-off fourth family, the commitment posture (`ercot_commitment_posture`, `miso_commitment_posture`, `spp_commitment_posture`), is an in-LP clustered-UC relaxation (`model/lp/rows.py::_build_posture_energy_rows`: online `U`/start-up `SU` columns, measured min-load, start-up charge), not a floor, never stacked on a gas bridge (rule 19); no keeper arms it (spec §1.6). ERCOT offer-surface and negative-price variants stay default-off (adjudicated in `docs/records/ercot/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10; the West/Panhandle topology split is closed).

## Capacity evolution (per year, one pass; spec §5)

0 confirmed exits (`confirmed_exits_enabled`, instrument-bound, bypasses the reliability floor; vintage-gated on `instrument_date`) → 1 announced retirements (non-fossil bounded by `NONFOSSIL_ANNOUNCED_HORIZON_YEARS`; fossil owner-filed EIA-860 dates honored under `fossil_announced_exits_enabled`, default on, vintage-gated, reversal registry armed; dated plants are exempt from the economic screen) → 2 CCS retrofit screen (joint with retirement; `ccs_retrofit_capex_co2_scaling` default on) → 3 economic retirement (attainable inframarginal margin vs FOM-only going-forward cost; per-fuel thresholds in ScenarioConfig; reliability floor shared with the build backstop) → 4 known additions (EIA-860 proposed pipeline) → 5 economic entry → 6 reserve-margin backstop (`reserve_margin_build_enabled`, default off) → 7 dispatch with RPS as an LP constraint (its dual is the REC price). Storage entry is a value stack (arbitrage net of degradation + RA value where a capacity market exists), never compound growth.

Per-ISO arms live in `iso_configs.py::_<iso>_config` `default_scenario_overrides`, shared defaults stay off, and each has a `--no-…` reaching the pre-arm posture: PJM capacity-market clearing (`capacity_market_supply_clearing_by_iso`), PJM published adequacy requirement (`capacity_adequacy_requirement_published_by_iso`), PJM VRE accreditation vintage (`pjm_vre_accreditation_vintage`, inside the D48 family), PJM/MISO retirement sector gate (`retirement_sector_gate`). `capacity_screen_peak_measured_hindcast` (default on, hindcast years only) makes every capacity screen test the year's own measured load. Locational deliverability (`capacity_deliverability_limits`, default off) is structural; only its measured-import half is validated in a keeper (CAISO).

## Fleet

ERCOT uses CAMPD per-plant binning (`use_campd_bins=True`: one LP unit per plant split into must-run / committed / economic / peaking tranches, `docs/binning-methodology.md`); other ISOs use legacy heat-rate bins. **There is no `COAL` class**: every coal unit carries `COAL_LIGNITE` / `COAL_PRB` / `COAL_BIT` / `COAL_WC` (`plant_taxonomy.COAL_CLASSES`, resolved by `data.coal.coal_subclass`); a config naming `COAL` is refused and `replay_keeper` translates older recipes.

## Conventions

snake_case; verb_noun functions; single-letter vars only in LP construction (t, g, z, s). Branches `claude/<lane>`; commits imperative present tense.

## Data: partial clone + a declared profile

The repo is cloned blobless; a session hydrates only the `data/raw` subtrees it needs: `python3 scripts/hydrate_data.py --profile <code|shared|ercot|…|all>` (profiles derive from directory names, `configs/data-profiles.yaml`). `code` is right for docs, governance, dashboard and refactor sessions; a solving lane hydrates its ISO. `data/clean` is derived and gitignored: `scripts/regenerate_clean.py --solve-profile <ISO>` builds only what that ISO's solve reads and skips unchanged datatypes (`docs/clean-data-profiles.md`). In a partial clone never resolve a blob you do not mean to download (read trees only; `GIT_NO_LAZY_FETCH=1` for read-side git). Some corpus payloads are gitignored at tip and some are unrecoverable from this repository — read the corpus `README.md` before concluding data is missing (`docs/records/governance/FINDING-history-rewrite-2026-08-16.md`). Every handoff prompt declares `DATA PROFILE: <name>`.

`cache_key()` carries a solve-surface fingerprint (`config/solve_surface.py`, declarations in `solve_surface_declared.py`), so a moved registry value re-keys the ISOs it touches; every bundle records its surface in `solve_surface.json`.

## Git and pushing

Pick the transport by pack size: `git push` for small packs (including a dashboard run payload); `mcp__github__push_files` for small multi-file text commits (≈457 KB cap per payload — never a run payload). Start every branch fresh on `origin/main` so a pack holds only your objects. On HTTP 408/500 set `git config http.version HTTP/1.1` and retry before concluding anything. Generated dashboard files (`manifest.js`, `benchmark.js`, `completeness.js`) are rebuilt by the Pages deploy; committing them is preview-only. Verify the blob after any push touching a ≥ 300-line source file (rule 27). A session cannot delete a remote branch (403): report leftovers for the owner.

## GitHub Actions

Private repo, billed minutes: **never offload a solve, intake or one-off chore to CI**, never add a per-task workflow, never a cron without owner sign-off. Workflows are durable infrastructure only (CI on PRs, the Pages deploy, the file-integrity guard, a parameterized fetch).

## Testing

`docs/testing.md`: fast lane `pytest -n auto -m "not slow and not integration and not fulldata"` on every edit; full lane `pytest` pre-push. Trivial cases first (1 gen, 1 zone, 24 h), then scale. A test asserts behaviour, never a stored digest, version or registered number.

## Reference docs

`docs/README.md` (index) · `docs/RUNBOOK.md` (the lane procedure) · `model-methodology-spec.md` (THE SPEC) · `docs/codebase/` (code reference) · `docs/governance/rule-history.md` · `docs/testing.md` · `docs/binning-methodology.md` · `docs/parameter-citations.md` · `docs/calibration-determination-rubric.md` · `docs/mechanism-testing-matrix.md` · `docs/multi-iso/` · `docs/calibration-log/<iso>.md` · `docs/forecast-development-plan-2026-07.md` (the forecast program) · `frontend/data/backcast/keepers/README.md`.

**Code is the source of truth.** When docs and code disagree, fix the docs (`/sync-docs`). When the methodology is ambiguous, the spec wins.
