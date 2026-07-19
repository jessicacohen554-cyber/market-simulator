# Refactor, Documentation & Repo Organization Plan — 2026-07

> Status: ACTIVE — program charter for the consolidation lane.
> Companion prompt pack: `docs/refactor-consolidation-prompt-pack-2026-07.md`.
> Produced from a 12-lane parallel audit of the post-cleanup tree (main @ `37d3923`,
> after PR #2486 reorganized `scripts/`). Scope: everything PR #2486 did NOT fix.

## 0. Executive summary

PR #2486 solved the *directory* problem for `scripts/` (459 flat files → 85 top-level +
`data/` 231 + `archive/` 144 + `lib/` + `probes/` + `diagnostics/`). It did not touch the
five deeper problems this plan addresses:

1. **No safety net.** The CI that CLAUDE.md rule 22 cites (`ci.yml` quarantine-gates,
   `lint.yml`) does not exist on the tree — no workflow runs pytest, ruff, or any
   governance gate. The only PR gate is file-integrity-guard (which also does a ~4 GiB
   full checkout per event). Every refactor below is unsafe until this is fixed.
2. **Security/hygiene debt.** A **tracked `.env` with 5 live API keys** (EIA, MISO ×2,
   ERCOT, data.gov), 22 tracked CAISO LMP zips (194 MB) at repo root (15 byte-duplicates,
   7 unique payloads that belong in `data/raw/`), a pending un-applied patch
   (`patches/pjm-m1-code.patch`) broken by the reorg, 760 result bundles tracked vs 64
   dashboard-registered, 11 orphaned dashboard payloads, and root detritus
   (`PROBE_TEST_FILE_DELETE_ME.txt`, scratchpads, logs).
3. **Duplication debt.** The same functionality implemented many times: the 8760
   calendar in **44 files**, sys.path bootstrap in **382 live scripts** (8+ variants),
   argparse in **353**, dashboard registry/payload IO in **8+ load-bearing scripts** (two
   different regexes for the same wire format), fit metrics in **6+ copies**, the
   backcast flag surface encoded **three times** (232 argparse flags → ~200-kwarg
   `run_year` signature → `backcast_config.py`), and the scorer's constants hand-mirrored
   into dashboard inline JS.
4. **Structural debt in `src/`.** ~50k of ~90k lines in 9 god-files (`fleet.py` 10,270;
   `scenarios.py` 7,834; `constants.py` 7,413; `transmission.py` 5,299 — ~70% per-ISO;
   `dispatch.py` 4,807; `fuel.py` 4,641; `capacity.py` 4,241; `eia_loader.py` 3,232;
   `reserve_config.py` 2,932), single functions of 1,700–3,500 lines, inverted layering
   (`config/` importing `data/` and `model/`), 53 load-bearing lazy import cycles, and
   163 `iso == "..."` ladders where the repo's own convention is per-ISO registries.
5. **Wall-clock levers unexploited.** The solve phase is 74–83% of a year's wall time.
   Cross-year warm-start is shipped for the backcast (2.14–2.52× on warm-year P0) but the
   P1-native floor path (CAISO **every** backcast year) still forces a cold second solve,
   year-1 P0 is always cold across the calibrate-iterate loop, the 25-year forecast path
   is entirely cold, tests run serially with no xdist, and multi-ISO concurrency is
   hand-launched.

The plan is organized as **eight workstreams (A–H)** with a strict dependency spine:
**A (safety net) → B (hygiene/security) → C (shared libraries) → D (src structure) /
E (scripts phase 2) / F (tests) / G (docs & governance) / H (wall-clock)**. C–H are
heavily parallelizable; the prompt pack maps them to concrete session waves.

## 1. Binding constraints (read before any session)

Everything below inherits these. They come from CLAUDE.md's Non-Negotiable Rules and
from frozen surfaces the audit verified on the tree.

- **Rule 27 / push integrity.** No bulk rewrite of any existing ≥300-line file. Local
  Edit-tool changes only; push exact on-disk bytes via `mcp__github__push_files`; verify
  the blob after any push touching a ≥300-line file. God-file splits legitimately shrink
  files >30% — those PRs carry the `intentional-shrink` label, isolated from unrelated
  changes. **All core-infrastructure sessions are Opus/Fable, never Sonnet.**
- **Byte-identity is the refactor contract.** Pure code motion must reproduce keeper
  solves byte-identically: capture goldens before (`scripts/capture_keeper_goldens.py`),
  gate after (`scripts/regression_gate.py --mode byte`, atol=rtol=0). The escalation
  procedure when byte-mode fails (determinism double-run → builder-tolerance 1e-9 →
  tie-localization → stop-the-line) is codified in §8 below. Never "fix" a failure by
  regenerating a golden; `tests/golden/ercot_2026_2040.json` regen requires
  `seed --force --reason` with owner authorization.
- **Pickle identity is frozen.** 12 committed `p2_state` pickles bind these classes to
  their exact module paths: `data.fleet.{Generator,FleetArrays}`,
  `model.dispatch.DispatchResult`, `config.scenarios.ScenarioConfig`,
  `model.storage.StorageUnit`, `results.outputs.FleetContext`,
  `config.iso_configs.TransferLink`. When a defining module becomes a package, define
  these classes **physically in the package `__init__.py`** so `__module__` is
  byte-identical in both directions.
- **`ScenarioConfig` stays a single flat dataclass** with frozen field names/defaults:
  `cache_key` hashes `asdict(self)`; regrouping fields orphans every on-disk cache and
  breaks keeper reproducibility. Splits of `scenarios.py` may move methods, resolvers,
  and module-level tables only.
- **Frozen dashboard/artifact surfaces** (rule 15 + rule 20 re-score-in-place): the
  `frontend/data/backcast/` location; registry sidecar `ENTRY_FIELDS`; the
  `window.BC.*` wire formats (`runGz` wrapper string, bench parts, manifest); byte-
  deterministic gzb64 (`compresslevel=9, mtime=0`, default json separators);
  `legitimacy-diagnostics/v1` D1/D2/D4 row+gate field names; `meta.json` /
  `run_config.json` keys (replay + goldens + `--reuse-solved` all reconstruct from
  them); run-id slug derivation; bundle paths of registered runs; the three scripts
  named in `deploy-pages.yml` paths+commands (`build_manifest.py`,
  `build_codebase_site_backcast.py`, `register_hindcast.py` — stdlib-only, sparse
  checkout, no installed deps).
- **Frozen history.** `scripts/probes/` and `scripts/archive/` are the calibration
  record — exempt from all boilerplate retrofits. `run_calibration_full.py`'s exported
  symbols (including the private `_load_reference`) are imported by 138 live + 71
  archived files: extraction leaves permanent same-name aliases; never rename.
- **Rules 23/25 during moves.** Consolidating derive/per-ISO code is code-motion only —
  tuned values transplant byte-for-byte with parity tests; no re-derivation, no merging
  per-ISO fitted parameters into generic defaults.
- **No new per-task workflows; no CI solves.** One durable `ci.yml` is sanctioned
  infrastructure (owner sign-off, §2-A); everything else runs in-session. Rule 12
  memory limits apply to all verification solves (years sequential; ≤2 concurrent
  invocations; never two per-plant/co-opt ISOs together on small hosts).
- **Verify-first list (§9).** The audit's critic flagged claims measured against
  different denominators (test-file counts, the `inputs/` dead-path inventory 10 vs 18
  vs 34, `run_scenario_iso` line span, ci.yml never-existed vs deleted). Sessions
  building on those numbers re-measure them first; the prompt pack bakes this in.

## 2. Workstream A — Safety net (land FIRST, blocks everything)

**A1. Restore CI (owner decision D-2, then one durable `ci.yml`).** First adjudicate
history (`git log --all` on a full clone: was ci.yml deleted or never committed?), then
either restore or create one PR-triggered workflow with jobs, each seconds-to-a-minute:
  - `quarantine-gates`: `python scripts/audit_keepers.py --check` +
    `python scripts/legitimacy_diagnostics.py --keepers` (D-6/D-9 — re-arms rules
    22/24/25 enforcement) + `scripts/check_registry_payload_parity.py`.
  - `lint`: `ruff check .` + `ruff format --check .` (makes the two `.claude` hook
    comments true again).
  - `fast-tests`: `pytest -n 2 -m "not slow and not integration and not fulldata"`.
  - `refactor-guards`: `python -m compileall -q src scripts` + pkgutil import-walk of
    `market_sim`; script-reference lint (regex-scan tracked files excluding
    archive/probes/results/frozen docs for `scripts/…​.py` paths and assert existence —
    seeded by fixing the 45 currently-dangling references); facade re-export tests as
    splits land.
  No cron without separate sign-off. Then update CLAUDE.md rule 22's enforcement
  sentence to match reality (surgical edit).
**A2. file-integrity-guard economy:** add `filter: blob:none` to its checkout — cuts a
  ~4 GiB download per PR/push to seconds. One line.
**A3. Persisted-state tripwires (new test files, no LP):**
  `tests/test_persisted_identity.py` (the 7 pickle-borne classes resolve at frozen
  paths AND `__module__` equals those paths; `ScenarioConfig().cache_key()` equals a
  pinned literal), a smoke test that gunzip+unpickles the smallest committed `p2_state`
  pickle, and an AST test asserting zero module-level import cycles in `src/market_sim`.
**A4. p2_state version envelope:** wrap `_save_p2_state` payload as
  `{'format_version': 2, 'git_sha': …, 'state': …}` (bare dict = v1); harden
  `run_p2_layer`'s config rebuild (defaults-merge instead of `with_overrides` on stale
  instances — the current call is latently broken for the committed pickles).
**A5. Root `conftest.py`** inserting repo root + `src/` on `sys.path` — makes the 98–106
  `scripts.*`-importing test files invocation-independent and is the precondition for
  the tests reorg (F).
**A6. Environment stamping:** add an `environment` block (python, platform,
  highspy/numpy/scipy/pandas/pyarrow/pydantic versions) to `write_run_config` and
  `meta.json`; `replay_keeper.py` warns on mismatch. Confirm the `--reuse-solved`
  comparator ignores the new key. Byte-identity claims are currently unverifiable
  across environments. Add `.python-version` (3.11) and a dependency-upgrade policy
  (any solver/numerics bump ⇒ keeper replay through the D-13 gate first).

## 3. Workstream B — Security & hygiene

**B1. Secrets (owner decision D-1, same-day).** Rotate all 5 keys (self-service
  portals); `git rm --cached .env`; add `.env`/`.env.*` to `.gitignore`; commit
  keys-only `.env.example`; add `scripts/lib/env_keys.py::get_api_key()` and port the 8
  hand-rolled `.env` parsers. **No history rewrite** — the clone is shallow/grafted,
  push_files can't force-push, and a rewrite would orphan the `git.sha` provenance in
  every bundle; record this decision in a docs security note. Optional: enable GHAS
  secret scanning (billed).
**B2. Root cleanup (owner decision D-4 for raw-data moves/deletes).** Checksum-verify,
  then `git mv` the 7 unique root LMP zips into `data/raw/lmp-data/CAISO/` (base names)
  and `git rm` the 15 byte-duplicates + the 2 in-data ` 2.zip` dups; `git rm`
  `PROBE_TEST_FILE_DELETE_ME.txt`, `.latetest.txt`, `probe_run.log`,
  `scratch/binprobe.json.gz`; `git mv` the two `scratchpad_miso_*.py` →
  `scripts/probes/`; `git mv us-gen-ownership.md` → `docs/` (+2 docstring cites).
  Rename `egrid2023_data_rev2 2.xlsx` → base name in ONE PR with its 5 hardcoded
  references. Consolidate the 472-line `.gitignore` into pattern rules with
  `git status --ignored` parity checked before/after; add the missing hygiene block.
  Do NOT touch: root HTML + `learning-hub/` (deploy stages them verbatim), `configs/`,
  `tools/`, `scope2-lce-portfolio/`, `context/`.
**B3. `patches/pjm-m1-code.patch` (owner decision D-5).** It is *pending work* broken
  by the reorg (`git apply` fails; fix content absent from tree; its regen is
  apply-exactly-once). Either rebase onto new paths and execute the README protocol
  once (Opus/Fable), or owner declares it abandoned and it archives with a superseded
  note. Never silently delete.
**B4. Retention (owner decision D-3).** Extend `scripts/dashboard_add_run.py` so
  pruning a registry sidecar also deletes `frontend/data/backcast/runs/<id>.js` and the
  mapped `results/calibration/<bundle>/`; extend `check_registry_payload_parity.py`
  with the payload→sidecar direction; delete the 11 verified orphan payloads; one-time
  owner-signed sweep of unregistered bundles (keep anything cited by DIAGNOSIS/handoff
  docs and anything in a sidecar `bundle` field — verified-list PR, not a glob);
  flatten the nonconforming `results/calibration/MISO/` nesting; archive the 10 bare-
  numeric legacy dirs and sweep loose `.md`/`.log` clutter out of `results/calibration/`.

## 4. Workstream C — Shared libraries (the de-duplication layer)

New modules, each adopted **opportunistically** (standing tools first; probes/archive
never retrofitted). All stdlib-only where a consumer requires it (`calibration_verdict`
is deliberately no-numpy; deploy runs on bare python3).

| Module | Kills | Copies today |
|---|---|---|
| `src/market_sim/utils/hour_calendar.py` | non-leap 8760 calendar: `hour_of_year`, `month_of_hour`, `hour_index`, `std_hour_index`, `to_model_hour`, `by_month`, DAYS_IN_MONTH | 44 files (one DST scoring artifact already caused) |
| `src/market_sim/results/metrics.py` | `pearson_r`, `nrmse`, `mae`, `pct_diff` (promote from `results/calibration.py`) | 6+ copies across runners/renderers/derives |
| `src/market_sim/data/clean_access.py` | the `_use_clean()` env gate + lazy `clean_io` import shims | 9–10 copied shims in `data/` modules |
| `scripts/lib/backcast_artifacts.py` (stdlib-only; name `bundle_io` is taken) | gzb64/ungzb64, encode/decode `runs/<id>.js`, bench-part read/write, manifest write/parse pair, sidecar iterate, `resolve_run_id`, path constants | 8 live scripts + 2 JS-side copies; two regexes for one format |
| `scripts/lib/benchmark_semantics.py` (stdlib-only) | EIA-930 corrupt-cell set, vintage-reconcile frac, gas fold-in — scorer currently mirrors renderer by comment | `render_calibration_html.py` ↔ `calibration_verdict.py` |
| `scripts/lib/cli.py` + `iso_configs.SUPPORTED_ISOS` export | canonical bootstrap header, `add_iso_arg`/`add_years_arg` (documents the rule-22 gate)/`add_out_dir_arg`/`add_bundle_arg` | 353 argparse copies, 48 `--iso`, 9 hardcoded ISO tuples |
| `scripts/lib/bundle_io.py` **extension** | `bundles_root()`, `resolve_bundle()`, `bundle_meta()`, `dispatch_path()` | 228 hand-joins of `results/calibration`, 133 meta.json parses |
| `scripts/lib/env_keys.py`, `scripts/lib/fetch.py`, `scripts/lib/pjm_dataminer.py` | API-key resolution, retry sessions, DataMiner2 client | 8 + 27 + 4 copies |
| `scripts/lib/holdout_policy.py` | CALIBRATION_YEARS + marker path | duplicated across the two rule-22 gates (+audit_keepers) |
| `scripts/lib/datatype_registry.py` | generic IsoSpec/register factory | 15 near-identical `scripts/lib/*/__init__.py`, ~3,275 lines |
| `scripts/lib/determinism.py`, `scripts/lib/lp_capture.py` | golden/replay env pins; bench LP-capture spy | 2–3 copies each |
| `tests/helpers/` + `tests/conftest.py` | `tmp_clean_dir`, `CleanDirTestCase`, `make_gen`/`make_fleet`/`base_scenario`, `solve_tiny`, raw-fixture writers, `REPO_ROOT` | 63 CLEAN_DIR dances, 101 TemporaryDirectory lifecycles, ~20 `_gen()` wrappers, 972 inline ScenarioConfigs |

Also: single-home decisions — `caiso_zonal_sufficiency` onto its own lib like
NYISO/NEISO; per-ISO reserve-requirement loaders into one spec-table module; the
zero-consumer `validation` clean datatype either wired into `_load_reference` or
parked; `derive_plant_emissions` v1 retired per rule 26 once v2 defaults (existing
emissions lane owns it); NYISO/NEISO settlement-zone crosswalks + `ALL_ISOS` into
config; `hf7_quantile` deduped.

## 5. Workstream D — `src/market_sim` structure

**Split pattern (uniform):** module → package with `__init__.py` re-exporting the
entire current public surface *plus test-imported privates*; pickle-borne classes
defined physically in `__init__`; moves in verified chunks (rule 27); each split PR
carries `intentional-shrink`, lands its facade re-export test, and passes the §8
byte-identity gate. **Order is by persisted-artifact risk** (artifact-inert first):

1. `constants.py` → `config/capacity_market.py`, `config/fuel_trajectories.py`,
   `config/ercot_envelopes.py` + facade (it holds ~2,300 lines of classes/functions).
2. `eia_loader.py` → `data/eia930/` (demand.py with a `DEMAND_LOADERS` registry
   replacing the if/elif ladder, frames, envelopes, weather, actuals, zonal_shares).
3. `fuel.py` → `data/fuel/` (trajectories, hubs, `basis/{nyiso,ercot,pjm,miso,caiso}.py`
   behind a `ZONAL_BASIS_APPLIERS` registry, dual_fuel, plant_prices, resolve).
4. `capacity.py` → `model/capacity_evolution/` (retirements, new_entry, adequacy, ccs,
   evolve) — cheapest facade surface.
5. Layering fix: `reserve_config.py` → `model/reserves/` and `interchange_config.py` →
   `model/interchange/spec.py` (config-level facades left behind); extract
   `data/fleet/models.py` leaf (Generator/FleetArrays) so config-layer code stops
   importing the 10k-line loader; then delete interchange_config's duplicated constants
   (CARB EF, NYISO gas basis) and import the canonical ones (+ parity test).
6. `transmission.py` → `model/interchange/` (core, import_nodes, per-ISO modules,
   registry consumed by `apply_interchange_injections`) — ~70% of the file is per-ISO.
7. `dispatch.py` → `model/lp/` (layout, costs, rows, reserve_rows, bounds, model) —
   DispatchResult/CrossYearBasis defined in `__init__`.
8. `fleet.py` → `data/fleet/` (models, arrays, withholding, floors, offer_surfaces,
   legacy_bins, eia860, campd_bins, assembly) — Generator/FleetArrays in `__init__`;
   decompose the 1,704-line `generators_to_fleet_arrays` into pure array helpers with a
   golden FleetArrays byte-check; collapse the four per-ISO
   `build_*_offer_surface_conditional_markup` wrappers onto the shared kernel behind a
   spec registry (names kept as aliases — tests import them).
9. `scenarios.py` LAST and methods-only: extract PB-1 resolvers + `SweepDefinition`
   (~900 lines); dataclass untouched.

**Orchestrator unification (its own lane, highest value):** finish Stages 5–6 —
extract the per-year body shared by `runner.run_scenario_iso` (~1.8k lines;
re-measure first) and `scripts/run_calibration.py::run_year` (~3,510 lines, ~200
kwargs) into `pipeline/year.py` + `pipeline/ttc.py`, preserving the documented
forecast/backcast asymmetries (xyear cache OFF on forecast; overlays backcast-only).
Then the **declarative flag registry**: one table (CLI spelling ↔ ScenarioConfig field
↔ default ↔ help) generating both the 232-flag argparse group and the config build —
this is the structural fix for the ERCOT-65 recorder-defect class. Then Stage 7
getattr folds (288 sites) per rules 24/26. Promote a public
`pipeline/api.py::run_scenario(config, iso)` + public `run_pair` (picklable) and
migrate the 12+ private-`_run_pair`/`run_scenario_iso` importers behind a contract
test before decomposing further. Extraction target for `run_calibration_full.py`'s
library half (`solve_and_persist` 1,934 lines / ~219-line signature, `_load_reference`,
`report_run`, reporting/persistence families) is `market_sim/pipeline/`
(persist/report/reference), with permanent same-name shims in the script.

**Cross-cutting:** convert the highest-value `iso ==` ladders to registries
(backcast_config's per-ISO tuned ternaries → per-ISO constant modules, byte-for-byte,
making rule 25 structural); move `pipeline/stage7_getattr_extraction_design.md` out of
the package into `docs/handoffs/`; keep the lazy-import-cycle AST test green throughout.

## 6. Workstream E — scripts/ phase 2 + Workstream F — tests/

**E (scripts):** fix the dead `inputs/` paths (authoritative re-inventory first —
audit counts disagree 10/18/34; includes two silently-skipping validation gates,
`tools/launcher.py` config discovery, `export_tranche_config.py --out`) routing
through `config/paths.py`; archive the post-cleanup residue (miso-73 rejected trio,
`regen_caiso_bench_cems.py`, self-declared SUPERSEDED build script) and write the
keeper-rotation rule into `scripts/README.md`; standardize `from scripts.lib import …`
(convert the 7 `from lib` users; **no** `__init__.py` under `scripts/` — PEP-420 is
load-bearing); move the two argparse mains out of `lib/`; move
`profile_lp_memory.py`/`diff_warmstart_bundles.py` → `diagnostics/`. Keep all standing
solve/governance/dashboard scripts at top level — their literal paths are quoted by
CLAUDE.md, skills, deploy-pages, and tests; any move updates every reference in the
same PR. Replace the two `importlib.spec_from_file_location` chains in the dashboard
toolchain with package imports.

**F (tests):** after A5 lands — shared `tests/helpers/` package + marks taxonomy
(`slow`, `integration`, `fulldata` replacing 39 ad-hoc skipifs, `golden`),
`--strict-markers`, pytest-xdist in dev deps, two documented lanes (fast `-n auto -m
"not slow and not integration and not fulldata"`; full serial pre-push) — never a
default `-m` in addopts. Then subdirectory migration mirroring src + scripts
(`unit/{config,data,model,pipeline,policy,results}`, `curation/`, `iso/{…}`,
`scoring/`, `regression/`) as pure `git mv` batches with collection verified per
batch (54 files carry `Path(__file__)` depth constants). New coverage priorities:
`backcast_config` flag→field mapping, `build_throughput` (zero tests today),
evolution ledger, configs-YAML round-trip glob test, direct src-loader tests.
Existing unittest-style files migrate opportunistically via mixins — never wholesale.

## 7. Workstream G — docs & governance; Workstream H — wall-clock

**G (docs):**
- `docs/backcast-artifact-contract.md` — the written schema for the entire bundle/
  registry/payload/bench/keepers chain (field tables, the three byte codecs, the
  FROZEN list). Precondition for every dashboard-adjacent refactor; documentation-only.
- Four-layer IA + `docs/README.md` index (README → spec + `docs/codebase/` → living
  per-area references → dated records); status-header convention
  (`ACTIVE | RECORD (frozen) | SUPERSEDED-BY | ARCHIVED`) applied to the ~12 unmarked
  executed/stale plans and the 4 `calibration-best-so-far*` snapshots (keeper truth is
  `keepers.json` + dashboard); handoffs index; move the 8 merged `_*_log_entry.md`
  staging files and executed session-prompts to `docs/sessions/`.
- README "Further reading" rewrite (it currently sends newcomers to executed plans and
  never links `docs/codebase/`, the multi-ISO index, the rubric, or the dashboard).
- `/sync-docs` skill map repair (dead `inputs/` scope, missing pipeline/codebase/rubric
  rows) — the drift-prevention tool is itself a drift source.
- CLAUDE.md: fix the drifted architecture tree (15 missing modules) by pointing at
  `docs/codebase/01-architecture.md`; add stable rule IDs (`[R-PUSH]`…) WITHOUT
  renumbering; then (owner decision D-6) slim ~43.7 KB → ~22–25 KB by moving amendment
  narratives to their canonical docs (rubric history, holdout memo, incident record) —
  normative sentences, gate/flag names, and enforcement pointers all stay; needs
  `intentional-shrink`.
- Correct `docs/multi-iso/README.md` (six ISOs, SPP = wheeling path only). Generate the
  ScenarioConfig reference from code (`generate_config_reference.py`) instead of two
  hand-maintained copies. Mark `forecast-validation.html` + preview JS as generated
  (`.gitattributes` + emitted header); extract the two inline dashboard JS modules to
  files and emit scorer constants from the scorer (kills the hand-mirroring); pin/vendor
  d3+gsap; supersede `docs/frontend-audit.md`; owner decision D-7 on the dormant
  `frontend/` scenario app (revive or archive).

**H (wall-clock), in expected-impact order** (solve = 74–83% of wall; cold P0
135–235 s; do NOT re-run recorded negative benches — IPM+crossover, thread scaling,
array setBasis):
1. **In-place P1 floor path** (`h.changeColsBounds` + re-solve from P0 basis instead of
   the full rebuild+cold P1 that every CAISO backcast year pays; floors enter the LP
   purely as column lower bounds). Same neutrality argument as the shipped warm starts;
   strictly better on RAM; gate with `diff_warmstart_bundles.py` on a CAISO 3-year
   bundle. PJM's kwargs-override case only if row-RHS-only.
2. **Persisted year-1 basis cache** per (iso, year, T) — kills the recurring 135–235 s
   cold P0 across calibrate-iterate loops; wrong basis costs iterations, never
   correctness; OFF for goldens/replay. Store as npz with a layout fingerprint, never
   pickle (compat clause 4).
3. **Forecast-path warm-start unblock** (25 sequential years, 24 would be warm at
   ~1.9×/yr): audit which `evolve_fleet`/storage-screen inputs read realized per-unit
   dispatch vs the basis-independent price construction; make them tie-invariant;
   thread `xyear_cache` behind a default-off flag; flip only after a full-horizon A/B
   shows an identical capacity trajectory (owner decision D-9).
4. **Operational:** `scripts/run_isos_concurrent.py` (rule-12 cap, ISO memory classes,
   env pins, log tee); pytest-xdist fast lane; `results_write` sub-instrumentation then
   a compression bench only if parquet dominates (bytes change ⇒ check golden hashing
   first); the one un-run HiGHS PAMI/`parallel` bench on archived captures (record the
   verdict either way); route `CACHE_ROOT`/`ENSEMBLE_DIR` through `config/paths.py`
   (cwd-dependence silently forks the results tree); cache-epoch policy for
   behavior-changing PRs (compat clause 2); `run_sweep` worker cap (currently
   uncapped cpu−1 — OOM hazard violating rule 12) via one shared
   `pipeline/members.py` helper absorbing the three parallel-runner copies; fix
   ensemble's narrowed-horizon crash; timing-summary helper shared by both
   orchestrators.

## 8. Verification protocol (every structural PR)

1. Capture `<lane>-before` goldens at the pre-change SHA (`capture_keeper_goldens.py
   --all`, pinned determinism env). 2. Apply the change. 3. Capture `<lane>-after`; run
   `regression_gate.py --mode byte`. 4. PASS ⇒ done. FAIL ⇒ run the after-capture twice
   (aa-run1/aa-run2): if they differ, the refactor introduced nondeterminism — always a
   bug, fix it. 5. Deterministic-but-different ⇒ `--mode builder` (1e-9) +
   `diff_warmstart_bundles.py` localization: tie-only reshuffle needs owner sign-off to
   reclassify + cache-epoch bump; anything else is a behavior change — stop the line.
6. Facade PRs also run the persisted-identity + import-cycle + facade re-export tests,
   and full fast-tier pytest. 7. Anything touching `run_calibration.py`'s scoring path
   re-gates at least one keeper bundle per affected ISO before merge. 8. Push via
   `push_files`, verify blobs for ≥300-line files, `intentional-shrink` label where the
   guard requires it.

## 9. Owner-decision register

| ID | Decision | Default recommendation |
|---|---|---|
| D-1 | Rotate 5 leaked API keys; untrack `.env`; optional GHAS | Do all same-day; no history rewrite (recorded rationale) |
| D-2 | Restore `ci.yml`+`lint.yml` vs amend CLAUDE.md rule 22 | Restore (sanctioned durable CI); adjudicate deleted-vs-never-existed first |
| D-3 | Bundle/payload retention sweep + prune-extension | Approve itemized-list PR; retention keyed to registry membership |
| D-4 | Root LMP zips: move 7 unique into `data/raw`, delete 15 dups | Approve with checksums in PR |
| D-5 | `patches/pjm-m1-code.patch`: apply or archive | Apply (it's a real pending clock repair), exactly once |
| D-6 | CLAUDE.md slim-down (>30% shrink) | Approve with `intentional-shrink`; normative content provably preserved |
| D-7 | Dormant `frontend/` scenario app: revive or archive | Archive pages/JS; data store stays (frozen path) |
| D-8 | Data-in-git long-term (4 GiB pack; LFS/side-channel) | Defer; document status quo |
| D-9 | Forecast warm-start default flip after A/B | Flip only on identical-capacity-trajectory evidence |
| D-10 | `egrid2023_data_rev2 2.xlsx` rename + 5 refs | Approve (one PR, atomic) |

## 10. Verify-first appendix (critic-flagged, re-measure before building)

Test-file counts (275/277/279/282 across lanes); the `inputs/` dead-path inventory
(10/18/34 — produce one authoritative list with resolution semantics); ci.yml
deleted-vs-never-existed; `run_scenario_iso` true span; wall-clock numbers are from
docs not fresh measurement (re-verify the xyear default-ON wiring before H work);
`.env` key liveness (rotation required regardless); the `validation` datatype
zero-consumer scan; the 45-dangling-reference list (classify: rule-23 provenance
citations count as load-bearing).
