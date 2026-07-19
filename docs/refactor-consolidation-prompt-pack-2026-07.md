# Refactor Consolidation — Prompt Pack (Parallel Lane Waves) — 2026-07

> Status: ACTIVE. Companion charter: `docs/refactor-consolidation-plan-2026-07.md`
> (read its §1 constraints and §8 verification protocol — every prompt below assumes
> them). Each prompt is self-contained: paste the **Standing Preamble** plus one prompt
> into a fresh session. Model assignments follow CLAUDE.md rule 27 (core
> infrastructure = Opus/Fable only; Sonnet only for purely-additive new docs).

## How to run the waves

- **Within a wave, sessions run in parallel** (they touch disjoint files). Across
  waves, respect the ordering — Wave 0 arms the safety net every later wave relies on.
- **Concurrency caps:** any session whose verification requires keeper/golden solves
  counts against rule 12 — at most 2 such sessions solving at once, never two
  per-plant/co-opt ISOs together. Wave 3 runs **max 2 sessions concurrently**, in the
  listed order (artifact-inert splits first).
- Every session pushes to its own `phase-refactor/<slug>` branch via
  `mcp__github__push_files`, small commits, blob-verify any ≥300-line file after push.
- If a session discovers its lane's audit numbers are wrong (see plan §10
  verify-first), it re-measures, records the correction in its PR body, and proceeds
  on the measured truth.

## Standing Preamble (paste at the top of every session)

```text
You are working the refactor-consolidation lane of market-simulator. Read
docs/refactor-consolidation-plan-2026-07.md (§1 constraints, §8 verification) and
CLAUDE.md before touching anything. Binding for this session:
- Rule 27: never bulk-rewrite an existing ≥300-line file; local Edit-tool diffs only;
  push exact on-disk bytes via mcp__github__push_files; verify pushed blobs (line
  count + hash) for every ≥300-line file; splits that shrink a core file >30% carry
  the intentional-shrink label in an isolated PR.
- Byte identity: structural changes to any solve-path file are gated by
  capture_keeper_goldens.py (before) + regression_gate.py --mode byte (after), with
  the plan §8 escalation procedure. Never regenerate a golden to make a gate pass.
- Frozen surfaces: pickle-borne class module paths; ScenarioConfig flat fields +
  cache_key; frontend/data/backcast location + all wire formats; meta.json /
  run_config.json keys; run-id slugs; registered bundle paths; deploy-pages script
  paths; run_calibration_full.py exported symbol names (incl. _load_reference);
  scripts/probes/ and scripts/archive/ are frozen history — never retrofit them.
- Rules 23/25: consolidation is code-motion only — tuned values transplant
  byte-for-byte with parity tests; per-ISO fitted parameters never merge into
  generic defaults; no re-derivation.
- No new per-task GitHub workflows; all verification runs in-session under rule 12
  memory limits (years sequential; ≤2 concurrent solve invocations).
- Push to branch phase-refactor/<your-slug>; commits imperative present tense; do
  not create a PR unless asked.
```

---

## Wave 0 — Arm the gates (run first; 0A–0D parallel)

### 0A · CI restoration & guard economy — **Opus** *(needs owner decision D-2 first)*

```text
Task: restore the missing CI safety net and make file-integrity-guard cheap.
1. Adjudicate history: on a FULL clone (git fetch --unshallow if needed), determine
   whether .github/workflows/ci.yml, lint.yml, clean-parity.yml,
   forecast-invariants.yml were deleted or never existed (git log --all --follow --
   .github/workflows/). Record the answer in the PR body — it decides restore-vs-create
   framing. Owner sign-off D-2 authorizes ONE durable ci.yml (this is sanctioned CI
   infrastructure, not a per-task workflow).
2. Create .github/workflows/ci.yml, PR-triggered, path-filtered, no cron, jobs:
   (a) quarantine-gates: python scripts/audit_keepers.py --check &&
       python scripts/legitimacy_diagnostics.py --keepers &&
       python scripts/check_registry_payload_parity.py
   (b) lint: uv run ruff check . && uv run ruff format --check .
   (c) fast-tests: uv sync then pytest -n 2 -m "not slow and not integration and not
       fulldata" (add pytest-xdist to dev deps if Wave-0B hasn't yet; coordinate).
   (d) refactor-guards: python -m compileall -q src scripts; a pkgutil.walk_packages
       import-walk of market_sim; a script-reference lint that regex-scans tracked
       files (EXCLUDING scripts/archive/**, scripts/probes/**, results/calibration/**,
       CHANGELOG.md, docs/sessions/**) for scripts/[\w/.-]+\.py and asserts each path
       exists — seed its allowlist from the ~45 currently-dangling references rather
       than fixing them here (Wave 1D fixes them).
   Keep total runtime ≈2–4 min. No LP solves, no data regen on runners.
3. file-integrity-guard.yml: add filter: blob:none to its checkout step (one line —
   stops the ~4 GiB download per event). Change nothing else in the guard.
4. Surgical Edits to make enforcement text true again: CLAUDE.md rule 22 enforcement
   sentence; .claude/hooks/session-start.sh:8 and ruff-autofix.sh lint.yml comments;
   scripts/run_calibration_full.py:6159 calibration-run.yml comment.
Verify: run each ci.yml command locally and confirm green before pushing; open a
draft PR so the workflow executes once; confirm all jobs pass.
```

### 0B · Persisted-state tripwires, conftest, env stamping — **Opus**

```text
Task: land the regression tripwires every later refactor depends on. All additive.
1. NEW tests/test_persisted_identity.py: (a) for each frozen pickle path
   {market_sim.data.fleet: [Generator, FleetArrays], market_sim.model.dispatch:
   [DispatchResult], market_sim.config.scenarios: [ScenarioConfig],
   market_sim.model.storage: [StorageUnit], market_sim.results.outputs:
   [FleetContext], market_sim.config.iso_configs: [TransferLink]} assert the class
   resolves there AND cls.__module__ equals that path; (b) assert
   ScenarioConfig().cache_key() == a pinned literal (compute once, commit it);
   (c) AST-walk src/market_sim asserting zero module-level import cycles.
2. NEW smoke test: gunzip+unpickle the smallest committed p2_state pickle
   (results/calibration/*/p2_state/*.pkl.gz) — load only, no LP.
3. p2_state envelope: in scripts/run_calibration_full.py wrap _save_p2_state's payload
   as {'format_version': 2, 'git_sha': ..., 'state': p2_state}; reader treats a bare
   dict as v1. Harden run_p2_layer's config rebuild: reconstruct via
   ScenarioConfig(**{k: v for k, v in vars(old).items() if k in current_field_names})
   instead of with_overrides on the stale instance (the current call raises for the
   committed 2026-era pickles — add a test proving the rebuild path works).
4. NEW root conftest.py (5 lines): insert repo root and src/ on sys.path.
5. Environment stamping: add an 'environment' block (python_version, platform,
   importlib.metadata versions for highspy/numpy/scipy/pandas/pyarrow/pydantic) to
   write_run_config (~run_calibration_full.py:1979) and meta.json; replay_keeper.py
   prints a loud WARNING (not failure) on mismatch. CONFIRM the --reuse-solved
   prior-config comparator (~:2128-2255) ignores the new key — add a test.
6. NEW .python-version (3.11). Consolidate the duplicated dev dependency groups in
   pyproject.toml (optional-dependencies.dev vs dependency-groups.dev) into one
   [dependency-groups].dev {pytest, ruff, tzdata, pytest-xdist}; update
   .claude/hooks/session-start.sh to plain `uv sync`; regenerate uv.lock +
   requirements.txt via the documented uv export. Do NOT bump any package version.
Verify: full fast pytest green; the new tests fail if you deliberately rename a class
(spot-check one, revert).
```

### 0C · Secrets remediation — **Opus** *(owner decision D-1: rotate keys first)*

```text
Task: remove the tracked .env credential leak. Owner rotates all 5 keys (EIA, MISO
pricing, MISO load, ERCOT, DATA_GOV) at their portals BEFORE this lands.
1. git rm --cached .env; add `.env` and `.env.*` to .gitignore; commit a .env.example
   containing key NAMES only. Never print or commit key values anywhere.
2. NEW scripts/lib/env_keys.py (stdlib-only): get_api_key(name, *, required=True,
   hint="") — os.environ first, then parse repo-root .env if present, exit with the
   registration-URL hint when required and missing.
3. Port the 8 hand-rolled .env parsers to it: scripts/data/fetch_eia930_hourly.py,
   fetch_miso_hub_lmp.py, fetch_eia860.py, fetch_eia_aeo.py, fetch_eia_delivered_gas.py,
   fetch_eia_coal_prices.py, fetch_aeo_electricity.py, scripts/lib/benchmark_corridor/aeo.py.
   Leave scripts/archive/ copies untouched.
4. NEW docs/security-note-env-2026-07.md: record the rotation, the untracking, and the
   explicit decision NOT to rewrite history (shallow grafted clone; API-only push;
   rewrite would orphan git.sha provenance in every bundle sidecar).
Verify: grep confirms no tracked file matches the old key values (do not echo them);
each ported fetcher's --help runs; .env absent from git ls-files.
```

### 0D · Backcast artifact contract doc — **Sonnet** *(purely additive doc)*

```text
Task: write docs/backcast-artifact-contract.md — the missing written schema for the
dashboard/bundle artifact chain. Documentation ONLY: read code, write one new doc,
change nothing else.
Cover, with field tables and the producing/consuming script for each: bundle files
(meta.json ~200 flag keys and its role as the replay contract; run_config.json incl.
the new environment block; metrics.json; legitimacy_diagnostics.json
legitimacy-diagnostics/v1 D1/D2/D4/D5/D9/D10 rows+gates; calibration_attestation.json;
floors/<year>_P1.npz dtypes; p2_state envelope v1/v2); registry sidecar ENTRY_FIELDS;
runs/<id>.js window.BC.runGz wrapper string + payload year keys; bench parts
(meta/bench, groups/zones/years, avgLMP variants, e930, co2); manifest.js/benchmark.js/
completeness.js/status.js; keepers.json (config + API consumers list);
calibration-complete.json; tail/actual_tail.json; statmode_d7.json. Document the three
byte codecs exactly (gzb64 json defaults + compresslevel=9 mtime=0; CF uint8
round(100*mw/npl); int16-delta little-endian with -32768 NaN sentinel) and the
window.BC.* global names as WIRE FORMAT. End with the FROZEN list (fields/paths that
rule-20 re-score-in-place forbids renaming) and the byte-determinism rationale
(conflict-free concurrent registration). Sources to read: render_calibration_html.py
(build_payload, _b64/_b64_i16), render_backcast.py, build_manifest.py,
calibration_verdict.py (load_artifacts, _decode_run_js), legitimacy_diagnostics.py,
build_status.py, check_registry_payload_parity.py, replay_keeper.py,
capture_keeper_goldens.py, docs/codebase-site/js/bc-data.js, deploy-pages.yml.
```

---

## Wave 1 — Hygiene & dead paths (1A–1E parallel, after Wave 0)

### 1A · Root cleanup & gitignore — **Opus** *(owner decisions D-4, D-10)*

```text
Task: clean the repo root. Every delete/move listed with checksums in the PR body.
1. LMP zips (22 tracked at root, CAISO OASIS payloads with ERCOT-style names):
   md5-verify against data/raw/lmp-data/CAISO/; git mv the 7 unique payloads there
   under base names (GRP_01, GRP_12, GRP_13, GRP_14, DAM 20230106/09/10); git rm the
   15 byte-duplicates; also git rm the 2 in-data ' 2.zip' byte-dups (GRP_09/GRP_10).
   data/raw is never modified in place — this is add+remove, no content edits.
2. git rm PROBE_TEST_FILE_DELETE_ME.txt .latetest.txt probe_run.log
   scratch/binprobe.json.gz; git mv scratchpad_miso_dispatch.py +
   scratchpad_miso_srmc.py -> scripts/probes/; git mv us-gen-ownership.md -> docs/
   and update the two docstring citations in src/market_sim/data/ownership.py.
3. Rename 'data/raw/fleet-egrid/egrid2023_data_rev2 2.xlsx' -> base name in THIS PR
   with its 5 hardcoded references (zone_assignment.py:53, egrid.py:60,
   scripts/data/process_eia860.py:215, curate_egrid.py:39,
   build_calibration_reference.py:137) — string-literal Edits only.
4. .gitignore: consolidate the 472 accreted lines into pattern rules (keep data/raw
   exclusions with provenance comments verbatim); add .env/.env.*, /scratchpad_*.py,
   /probe_run*.log, /scratch/, /*.log. Prove parity: git status --ignored byte-diff
   before/after, git ls-files diff empty.
5. Do NOT touch: root *.html, learning-hub/ (deploy stages them verbatim), configs/,
   tools/, scope2-lce-portfolio/, context/, run-simulator.*.
Verify: extract_caiso_hubs.py glob still resolves; full fast pytest; deploy-pages
paths untouched.
```

### 1B · Dead `inputs/` path repair — **Opus**

```text
Task: produce the authoritative dead-path inventory and fix it. Audit lanes disagreed
(10 vs 18 vs 34 files) — first re-measure: grep every live (non-archive, non-probe)
script + src + tools for the deleted pre-W1 'inputs/' root, and classify each hit:
default-arg / hard-fail / SILENT-SKIP. Then fix all of them to route through
src/market_sim/config/paths.py constants (CALIBRATION_DIR, PROCESSED_DIR, RAW_DIR,
CAMPD_BINS_CSV, PLANT_REGISTRY_CSV, data/raw/reference/...). Known cases the fix must
include: validate_neighbor_price.py:45 (make it FAIL LOUDLY when the measured file is
absent — today the gate silently skips), caiso_zonal_sufficiency.py:34,
export_iso_bin_assignments.py:71 (silent {} fallback drops the CHP column — fail
loud), export_tranche_config.py:169, tag_mixed_plants.py:43, lib/reldeploy_zonal_report.py:47,
tools/launcher.py:56-57 + UI copy :239, and the 11+ scripts/data derive_*/fetch_*/
process_* offenders. Rule 23: derive scripts get PATH fixes only — never re-run a
derivation; verify by --help/dry-run path resolution, not regeneration.
render_calibration_html.py:617 is a deliberate documented fallback — leave it.
Deliver the inventory table (file, old path, new constant, resolution semantics) in
the PR body. Full fast pytest green.
```

### 1C · Retention & orphan sweep — **Opus** *(owner decision D-3)*

```text
Task: make dashboard retention govern all three stores, then sweep orphans.
1. Extend scripts/dashboard_add_run.py: when top-15-per-ISO pruning removes a registry
   sidecar, also delete frontend/data/backcast/runs/<id>.js and the mapped
   results/calibration/<bundle>/ dir. Extend check_registry_payload_parity.py with the
   payload->sidecar direction (orphan payloads fail).
2. Delete the 11 verified orphan payloads (2026-07-08-pjm-90-* .. 2026-07-10-pjm-96-
   seam-ladder, ~16 MB) — re-verify each has no sidecar before rm.
3. One-time bundle sweep (OWNER-SIGNED itemized list, not a glob): git rm
   results/calibration bundles with no registry sidecar, EXCEPT any dir named in a
   sidecar 'bundle' field, cited by a docs/DIAGNOSIS-*/handoff doc, holding p2_state
   pickles, or pinned by STATMODE_PROBE_RUNS (config/constants.py). Also: flatten
   results/calibration/MISO/* nesting to the flat convention; move the 10 bare-numeric
   legacy dirs (159..166) and loose DIAGNOSIS/FINDING/AUDIT .md + *_solve.log clutter
   to results/calibration/_archive/.
4. Write the retention rule into scripts/README.md and reference it from the
   calibration-report skill (surgical edit).
Verify: regen_dashboard.py --dry-run parity before/after; audit_keepers.py --check
green; build_manifest.py output byte-identical for surviving runs.
```

### 1D · Stale-reference & docs-truth sweep — **Opus**

```text
Task: fix every dangling/false reference the reorg left. First re-enumerate the
~45 dangling scripts/*.py references (ci-workflows audit) and classify.
1. src provenance citations (rule 23 load-bearing): scenarios.py:734, outages.py:12,
   fleet.py:1589 (derive_campd_outages.py -> absorbed into scripts/lib/outage_detect.py
   — cite that), fuel.py:802/1276/1529 (fetch_iroquois_daily_spot.py — locate or mark
   archived). Comment-only Edits.
2. Fix the source strings generate_parameter_registry.py reads, then regenerate
   frontend/data/parameters.json via the script (never hand-edit generated output).
   Same for calibration-complete.json's fetch_campd_unit_level.py path.
3. scripts/lib/session_score.py:3 pre-rename usage line.
4. .claude/skills/sync-docs/SKILL.md: fix dead inputs/ scope line, the
   inputs/custom-bin-assignments.csv row, lowercase claude.md; ADD map rows for
   src/market_sim/pipeline/*, scripts/legitimacy_diagnostics.py, docs/codebase/,
   docs/codebase-site content pages, forecast-development-plan, both rubrics,
   scripts/README.md, CONVENTIONS.md.
5. Doc truth fixes: docs/multi-iso/README.md seven-ISOs claim -> six (SPP = MISO RDT
   wheeling path only); README.md 'Further reading' rewrite (lead with
   docs/codebase/README.md, multi-iso/README.md, forecast-development-plan, rubric,
   dashboard pages); README scripts/ blurb -> one line + link to scripts/README.md;
   test-count claim -> point at CI. CLAUDE.md architecture tree: replace the drifted
   per-module inventory with subsystem one-liners + pointer to
   docs/codebase/01-architecture.md (surgical Edit, no other CLAUDE.md changes).
6. Status banners (one line under the H1, no content edits) on: code-docs-cleanup-plan,
   data-reorg-plan, iso-model-unification-plan, codebase-site/PLAN.md,
   codebase-site/UPDATE-PLAN-2026-07.md, fable-prompt-pack-2026-07.md, the 5
   *-session-prompt.md files, the 4 calibration-best-so-far*.md (HISTORICAL SNAPSHOT ->
   keepers.json + dashboard), docs/frontend-audit.md (superseded).
7. git mv the 8 docs/_*_log_entry.md staging files + executed session-prompts ->
   docs/sessions/ with index rows; git mv
   src/market_sim/pipeline/stage7_getattr_extraction_design.md -> docs/handoffs/.
Verify: the Wave-0A script-reference lint passes with its allowlist emptied of every
reference this session fixed; /sync-docs dry pass clean.
```

### 1E · Docs index — **Sonnet** *(purely additive new files)*

```text
Task: create the docs index layer. NEW FILES ONLY — do not edit existing docs.
1. docs/README.md: the four-layer IA index (L0 README -> L1 spec + docs/codebase/ ->
   L2 living references -> L3 dated records). One row per living doc: path, status,
   area, superseded-by. 'Moved ->' rows for anything Wave 1D relocated. State the
   status-header convention (> Status: ACTIVE | RECORD (frozen <date>) |
   SUPERSEDED-BY <path> | ARCHIVED) as the standing rule for new docs.
2. docs/handoffs/README.md: generated-once index (name, date, status) of the 160
   handoffs, reading the forecast-development-plan §9 ledger and Wave 1D's banners
   for status. Mark clearly it is a point-in-time index with a regen command note.
Do not move, delete, or edit any existing doc; do not touch CLAUDE.md.
```

---

## Wave 2 — Shared libraries (2A–2D parallel, after Wave 1)

### 2A · `backcast_artifacts` + scorer/renderer unification — **Opus**

```text
Task: single home for dashboard artifact IO. Contract doc (Wave 0D) is the spec.
1. NEW scripts/lib/backcast_artifacts.py — STDLIB-ONLY (json, gzip, base64, re,
   pathlib): gzb64/ungzb64 (exact current bytes: default json separators,
   compresslevel=9, mtime=0), encode_run_js/decode_run_js (exact wrapper string),
   write_bench_part/load_bench_part, write_manifest_js/parse_manifest_js (writer and
   parser as a PAIR), iter_sidecars/load_sidecar/write_sidecar, resolve_run_id,
   bundle_dir_for, and the DATA/REGISTRY/RUNS/BENCH path constants. Byte-parity test:
   round-trip an existing runs/<id>.js and bench part, assert identical bytes.
2. Migrate consumers ONE COMMIT EACH, parity-checked (check_registry_payload_parity +
   regen_dashboard --dry-run before/after): build_manifest.py, render_backcast.py,
   export_forecast_bands.py, calibration_verdict.py, legitimacy_diagnostics.py,
   regen_dashboard.py, register_hindcast.py, check_registry_payload_parity.py,
   build_codebase_site_backcast.py, score_crossover.py. Probes/archive untouched.
3. NEW scripts/lib/benchmark_semantics.py (stdlib-only): EIA930_NG_CELL_CORRUPT set,
   _VINTAGE_RECONCILE_FRAC, gas fold-in arithmetic, gas group membership — imported by
   BOTH render_calibration_html.py and calibration_verdict.py (delete the by-comment
   mirrors).
4. NEW scripts/lib/holdout_policy.py: CALIBRATION_YEARS frozenset + MARKER_FILE;
   imported by run_calibration_full.py's gate, legitimacy_diagnostics.py D-6, and
   audit_keepers.py (drop the parity-test workaround).
5. Replace the two importlib.spec_from_file_location chains (dashboard_add_run.py:43,
   render_backcast.py:56) with `from scripts import ...` package imports (the
   convention build_status.py/audit_keepers.py already use).
6. docs/codebase-site/js/viz-forecast-bands.js: import inflateGz from ./bc-data.js
   (delete the verbatim copy).
Constraints: calibration_verdict must stay numpy-free; every migrated file ≥300 lines
gets blob verification; manifest/bench bytes must be identical for unchanged data
(the conflict-free registration property).
```

### 2B · Calendar, metrics, clean-seam consolidation — **Opus**

```text
Task: kill the three most-copied src-level duplications. Pure code motion; the
byte-identity gate (plan §8) applies because fleet/fuel/eia_loader are solve-path.
1. NEW src/market_sim/utils/hour_calendar.py: DAYS_IN_MONTH_NOLEAP, MONTH_START_HOUR,
   hour_of_year(month, day, hour), month_of_hour(int|ndarray), hour_index(ts),
   std_hour_index(ts, year, tz), to_model_hour(dates, hour_end, year) (Feb-29-drop
   from miso_reserve_requirements), by_month(values, months); HOURS_PER_YEAR imported
   from constants only. One docstring stating the chronological-UTC convention and
   citing the DST scoring-artifact diagnosis. Migrate LIVE src modules
   (eia_loader, fleet, fuel, neighbor_price, coal, campd — remove campd's local
   HOURS_PER_YEAR/_DAYS_IN_MONTH shadows — outages, scarcity, transmission,
   miso_reserve_requirements) and live scripts/data callers file-by-file; leave every
   local name as a one-line alias so call sites do not churn; probes/archive exempt.
2. Promote metrics: NEW src/market_sim/results/metrics.py with pearson_r, nrmse, mae,
   pct_diff (moved from results/calibration.py, re-exported there). Point
   run_calibration_full.py:307/315, run_calibration_eia930.py:97/105,
   render_calibration_html.py:659, derive_offer_curve_jacobian.py:716 (path fix only —
   rule 23), derive_nyiso_rcpf_overlay.py:466, derive_ordc_overlay.py:276 at it.
   calibration_verdict.py stays stdlib-only — add a cross-reference comment only.
3. NEW src/market_sim/data/clean_access.py: use_clean() env gate + get_clean_io()
   lazy import; the 9-10 copied shims in data/ modules become one-line aliases.
   Behavior byte-identical; do NOT flip any clean path on.
4. Dedupe _hf7_quantile (ensemble.py:484 / structural_prior.py:412) into one public
   helper.
Verify: byte-mode regression gate on one ERCOT backcast year + full fast pytest.
```

### 2C · scripts CLI harness & curation libs — **Opus**

```text
Task: the shared script-side helpers. Adoption is opportunistic — convert the standing
top-level tools now, everything else only when next touched. Probes/archive exempt.
1. Export SUPPORTED_ISOS: tuple[str, ...] from src/market_sim/config/iso_configs.py
   (keys of _ISO_BUILDERS); replace the 9 live hardcoded six-ISO tuples.
2. NEW scripts/lib/cli.py: repo_root() (re-export paths.REPO_ROOT), the canonical
   3-line bootstrap documented in scripts/README.md, add_iso_arg(p, required, multi)
   with choices=SUPPORTED_ISOS, add_years_arg(p, default=(2023, 2024, 2025)) with
   help text naming the rule-22 holdout gate, add_out_dir_arg, add_bundle_arg.
3. EXTEND scripts/lib/bundle_io.py: bundles_root(), resolve_bundle(name_or_path),
   bundle_meta(run_dir), dispatch_path(run_dir, year, pass_label='P1'). Adopt in the
   standing governance/dashboard tools (calibration_verdict, legitimacy_diagnostics,
   render_calibration_html, audit_keepers, build_dof_ledger) one commit each.
4. NEW scripts/lib/fetch.py (retrying_session, download; keep agent-proxy CA behavior)
   and scripts/lib/pjm_dataminer.py (fetch_feed with paging/retries); port the four
   PJM fetchers; other fetch_* scripts adopt when next touched.
5. NEW scripts/lib/datatype_registry.py: make_registry(datatype, canonical_columns,
   spec_fields) factory; shrink 2-3 of the 15 IsoSpec __init__.py packages onto it as
   the proof (rest follow opportunistically); update the data-intake skill pointer.
6. Single-home fixes: port caiso_zonal_sufficiency.py onto scripts/lib/
   zonal_sufficiency (like its NYISO/NEISO siblings); unify the three per-ISO
   reserve-requirement loaders into one src/market_sim/data/reserve_requirements.py
   spec-table module preserving EXACT hard-error semantics (rule 13 — no graceful
   fallback), per-ISO sources unchanged.
7. Import style: convert the 7 `from lib import` users to `from scripts.lib import`;
   delete their sys.path.insert(REPO/'scripts') lines; do NOT add __init__.py
   anywhere under scripts/ (PEP-420 is load-bearing). Move the two argparse mains out
   of lib/ (session_score CLI shell, reldeploy_zonal_report) to scripts/ proper.
8. Adjudicate the zero-consumer 'validation' clean datatype: verify the scan, then
   either wire run_calibration.py::_load_reference to read_clean('validation') behind
   a default-off flag with a parity test, or add a PARKED banner to
   curate_validation.py — owner's pick in PR review.
Verify: every touched script's --help runs; fast pytest; byte-gate only if any
solve-path file was touched (reserve_requirements is — gate one NYISO/MISO year).
```

### 2D · Test helpers, marks, speed — **Opus**

```text
Task: the shared test layer (conftest landed in Wave 0B). All additive; no wholesale
rewrites of the 217 unittest-style files.
1. NEW tests/helpers/: __init__.py exporting REPO_ROOT; builders.py (make_gen,
   make_fleet(zones_of_gens, zone_names, hours, ...), base_scenario(mode, iso,
   **overrides), backcast_scenario via pipeline.backcast_config); base.py
   (CleanDirTestCase mixin: tmp dir + clean_io.paths.CLEAN_DIR redirect + restore;
   RawFixtureTestCase); solve.py (solve_tiny(fleet, demand_by_zone, hours=24, ...)
   wrapping incidence/TTC/availability assembly — the 1-gen/1-zone/24h pattern);
   raw_fixtures.py (per-source writer functions absorbed from the 17 _write_fixture
   variants); clean_asserts.py (assert_clean_valid, read_clean_or_fail).
   tests/conftest.py gains tmp_clean_dir (monkeypatch) + repo_root fixtures.
2. Marks: add `fulldata` and `golden` to pyproject markers; convert the 39 ad-hoc
   skipif-on-raw-data sites to one shared requires_raw helper; sweep the 91
   8760-referencing files and mark the unmarked full-8760 LP tests slow (e.g.
   test_caiso_storage_as_reservation.py:223). addopts = "--strict-markers" (and
   nothing else — never a default -m deselection).
3. Migrate ~10 of the worst CLEAN_DIR-dance files onto CleanDirTestCase as the
   pattern proof (one-line base-class swaps); the rest opportunistic. Update the
   data-intake skill's tmp-CLEAN_DIR guidance to point at the helper.
4. New coverage (all NEW files): tests/test_backcast_config.py (flag->field mapping,
   pattern from test_recorded_cfg_fidelity.py); tests/test_build_throughput.py (module
   has ZERO tests); tests/test_evolution_ledger.py (write/load round-trip, legacy
   tolerance; also write "ledger_version" into write_ledger's payload — additive — and
   fix the orphaned comment); one parametrized test globbing configs/**/*.yaml through
   the right loader per kind (ScenarioConfig.from_yaml / SweepDefinition /
   UncertaintySpec) — closes the 7-untested-YAML gap, no solves.
5. Document the two test lanes + the two golden systems in a short docs/testing.md.
Verify: pytest -n auto -m "not slow and not integration and not fulldata" green and
measurably faster; full serial suite green; collection count recorded before/after
(re-measure the disputed 275/279/282 file count and record it).
```

---

## Wave 3 — src structure (Fable, max 2 concurrent, in order)

Every 3x session: facade pattern per plan §5 (package `__init__` re-exports the full
current surface + test-imported privates; pickle-borne classes defined IN `__init__`);
`intentional-shrink` label; §8 byte-identity gate; facade re-export test added to the
Wave-0A refactor-guards job; import-cycle AST test stays green.

### 3A · `constants.py` split — **Fable**

```text
Task: split src/market_sim/config/constants.py (7,413 ln) additively: NEW
config/capacity_market.py (CapAndTradeProgram, CapacityDemandCurvePoint,
evaluate_demand_curve, MarketDesign, resolve_capacity_market_clearing, RBDC/vintage/
ELCC classes — the ~L2062-4422 block), NEW config/fuel_trajectories.py (L1039-2062),
NEW config/ercot_envelopes.py (L5810-7245). constants.py becomes scalars + facade
re-exports of every moved name. Resolve the constants->interchange_config lazy-import
edge deliberately (keep the lazy import; do not hoist). No value changes anywhere —
transplant byte-for-byte; every moved literal keeps its citation comment (rule 5).
Verify per plan §8 + persisted-identity + import-cycle tests; 40 src / 45 script / 51
test importers must resolve unchanged.
```

### 3B · `eia_loader.py` → `data/eia930/` — **Fable**

```text
Task: convert src/market_sim/data/eia_loader.py (3,232 ln) to a package: demand.py
(the six _load_<iso>_hourly_demand + a DEMAND_LOADERS: dict[str, Callable] registry
replacing the if/elif ladder ~L3030), frames.py, envelopes.py (hydro/interchange/
corridor/seam), weather.py, actuals.py, zonal_shares.py, with eia_loader-equivalent
__init__ re-exporting everything (45 script importers). Clean-seam shims already
aliased to clean_access (Wave 2B) move intact. Byte-gate one ERCOT + one CAISO
backcast year (demand loading differs per ISO).
```

### 3C · `fuel.py` → `data/fuel/` — **Fable**

```text
Task: convert src/market_sim/data/fuel.py (4,641 ln) to a package: trajectories.py,
hubs.py, basis/{nyiso,ercot,pjm,miso,caiso}.py behind a ZONAL_BASIS_APPLIERS registry
consumed by resolve.py (resolve_fuel_prices), dual_fuel.py, plant_prices.py, coal.py.
The per-ISO basis moves are rule-25-sensitive: fitted values transplant byte-for-byte
(add a parity test asserting the registry produces identical arrays to the old
functions on a fixture year). Byte-gate NYISO (largest basis family) + ERCOT.
```

### 3D · `capacity.py` → `model/capacity_evolution/` — **Fable**

```text
Task: convert src/market_sim/model/capacity.py (4,241 ln) to a package: retirements.py
(confirmed/announced/economic + reliability floor), new_entry.py, adequacy.py, ccs.py,
evolve.py. Smallest facade surface (7 src / 6 script / 14 test importers). Preserve
step ordering 0-7 exactly (spec §5.1). Forecast-path verification: the golden bands
test (RUN_GOLDEN_FORECAST=1) or, minimum, a 3-year forecast smoke with identical
evolution ledger output pre/post.
```

### 3E · Layering fix: config↔model inversion — **Fable**

```text
Task: fix the inverted config-layer imports.
1. NEW leaf src/market_sim/data/fleet_models.py as a RE-EXPORT SHIM ONLY for now:
   Generator and FleetArrays STAY DEFINED in fleet.py until session 3H (pickle
   identity — __module__ must remain market_sim.data.fleet); the leaf exists so the
   config layer can import the types without importing the 10k-line loader module.
2. Relocate config/reserve_config.py -> model/reserves/ and config/
   interchange_config.py -> model/interchange/spec.py with config/-level facades left
   behind (their per-ISO _<iso>_design registries move intact).
3. Delete interchange_config's duplicated constants (CARB_UNSPECIFIED_IMPORT_EF,
   _GAS_BASIS_NYISO) once its fleet import routes through the leaf; import the
   canonical constants; add a single-definition test.
Byte-gate one CAISO year (interchange-heavy) + reserve co-opt ISO year (MISO or
NYISO). The 53 lazy cycles are load-bearing: re-run the AST cycle test after every
move; hoist nothing to module level.
```

### 3F · `transmission.py` → `model/interchange/` — **Fable**

```text
Task: convert src/market_sim/model/transmission.py (5,299 ln, ~70% per-ISO) into the
model/interchange/ package started in 3E: core.py (incidence/TTC/interface groups/
reliability floor), import_nodes.py, caiso.py (~2,300 ln), miso.py, pjm.py, nyiso.py,
neiso.py, registry.py mapping ISO -> injection functions consumed by
apply_interchange_injections. transmission.py stays as a full facade (12 scripts + 40
test files import it). Byte-gate CAISO + one eastern ISO year.
```

### 3G · `dispatch.py` → `model/lp/` — **Fable** *(after 3A–3F)*

```text
Task: convert src/market_sim/model/dispatch.py (4,807 ln) to model/lp/: layout.py,
costs.py, rows.py, reserve_rows.py, bounds.py, model.py. DispatchResult, CrossYearBasis
(and solve_dispatch) are defined PHYSICALLY in the new package __init__ so
__module__ == 'market_sim.model.dispatch' — the 12 committed p2_state pickles depend
on it (persisted-identity test proves it). Rule 2 review per-file: no hour loops may
appear during the move. Byte-gate: two ISOs, one with reserve co-opt
(_build_reserve_rows path) and ERCOT.
```

### 3H · `fleet.py` → `data/fleet/` — **Fable** *(after 3G)*

```text
Task: the big one — src/market_sim/data/fleet.py (10,270 ln) to data/fleet/: models.py
(absorbing the 3E leaf), arrays.py, withholding.py, floors.py, offer_surfaces.py,
legacy_bins.py, eia860.py, campd_bins.py, assembly.py. Generator + FleetArrays defined
IN __init__ (pickle identity). Re-export every public name PLUS test-imported privates
(_rows_to_generators, _hour_to_month_index, the per-ISO offer-surface builders — grep
tests first and enumerate). Two sub-tasks with their own gates:
(a) decompose generators_to_fleet_arrays (L983-2686, 1,704 ln) into pure array
    helpers (_availability_matrix, _apply_outage_overlays, _nuclear_monthly,
    _assemble_offer_tranches) with a golden FleetArrays byte-comparison on an ERCOT
    2023 fixture;
(b) collapse the four build_<iso>_offer_surface_conditional_markup wrappers onto the
    shared _conditional_surface_markup kernel behind a per-ISO spec registry, keeping
    the four names as aliases.
FUEL_TYPE_MAP and the Generator field names the evolution ledger reads are frozen
public API. Byte-gate: ERCOT (CAMPD bins path) + one legacy-bins ISO, plus the fast
suite's 111 fleet-importing test files.
```

### 3I · `scenarios.py` methods-only extraction — **Fable** *(last split)*

```text
Task: extract from src/market_sim/config/scenarios.py ONLY: the PB-1 resolvers
(_interpolate_low_mid_high, resolve_new_entry_costs, resolve_demand_growth_rate,
resolve_policy_bundle) -> NEW config/scenario_resolvers.py, and SweepDefinition ->
NEW config/sweeps.py, both re-exported from scenarios.py. The ScenarioConfig dataclass
is UNTOUCHED — no field moves, no nesting, no renames (cache_key + pickles + YAML +
meta.json all hang off it; the pinned cache_key literal test must still pass).
Enforce the contiguous field-group comment convention inside the class body and add a
generated field-group index note instead of moving code. Byte-gate: cache_key literal
unchanged + one forecast smoke year.
```

### 3J · Orchestrator unification + flag registry — **Fable** *(own track; not
concurrent with 3G/3H)*

```text
Task: finish the orchestrator-unification lane (its plan doc's remaining stages).
First RE-MEASURE the disputed spans (run_scenario_iso true line range; run_year).
1. Public facade first: NEW src/market_sim/pipeline/api.py exporting
   run_scenario(config, iso) -> cache_key and a PUBLIC, picklable, module-level
   run_pair; re-export from runner; migrate the 12+ callers (ensemble.py:160,
   matrix.py:94, pb5_member_slice.py:35, pb5_matrix_slice.py:24, golden_forecast_bands,
   run_full_horizon, run_capacity_hindcast, run_sensitivity_tornado,
   run_driver_battery, run_equilibrium_battery, run_foresight_ab, export_lce_lmp,
   capture_baseline); add a contract test (signature + picklability + the
   results/{iso}/{key}/year_{year}.parquet + config.yaml + evolution_{year}.json
   layout).
2. Extract the shared per-year body into pipeline/year.py + pipeline/ttc.py, called by
   BOTH runner.run_scenario_iso and scripts/run_calibration.py::run_year. PRESERVE the
   documented asymmetries: forecast path keeps xyear_cache=None (statically asserted
   by tests/test_xyear_warmstart_default.py); measured overlays stay backcast-only;
   mock patch points tests rely on (pipeline_solve.DispatchModel/solve_dispatch) keep
   their import paths.
3. Declarative flag registry: one table (CLI spelling, ScenarioConfig field, default,
   help) generating run_calibration_full.py's argparse group AND the backcast_config
   build, migrated INCREMENTALLY by flag family (coal, offer-surface, storage, ...) —
   each family lands with a recorded-config fidelity test (the ERCOT-65 defect class).
4. Extract run_calibration_full.py's library half into pipeline/persist.py,
   pipeline/report.py, pipeline/reference.py with PERMANENT same-name shims (incl.
   _load_reference) — staged, each stage <30% shrink or intentional-shrink labeled,
   gated by regression_gate + keeper replay.
5. Convert backcast_config.py's per-ISO tuned ternaries (L1505-1684) to per-ISO
   constant modules selected by dict — values byte-for-byte with a parity test
   (rules 23/25).
Verify: §8 gate on a full 3-year backcast bundle for TWO ISOs + one forecast smoke;
re-gate one keeper per touched ISO before merge; full fast suite.
```

---

## Wave 4 — Wall-clock (after Wave 3 lands or on a stable base; 4A/4B and 4C/4D
pairwise parallel)

### 4A · In-place P1 floor path — **Fable**

```text
Task: eliminate the cold second solve the P1-native floor hooks force
(pipeline/solve.py:191-223). When p1_fleet_prep returns a floored fleet, the ONLY LP
change is min_gen column lower bounds (dispatch.py col_lower block) — mutate the
EXISTING HiGHS model via h.changeColsBounds on the P[g,t] block (exact analogue of the
shipped changeColsCost P0->P1 re-cost) and re-solve from the P0 basis. Keep the cold
path as fallback behind an env/flag; CAISO backcast (caiso_ra_mustoffer default-ON
every year) is the payoff case; ERCOT gas bridge shares the path. For the PJM
reserve_supply_cap kwargs-override case: implement ONLY if it is row-RHS-only
(changeRowsBounds); if structural, leave cold and document why. Verify: identical
duals/dispatch via scripts/diff_warmstart_bundles.py on a CAISO 3-year bundle
(marginal-tie-only reshuffles per the existing warm-start neutrality standard); RSS
peak not above the sequential-build baseline on one big co-opt ISO; record timings in
docs/handoffs/wallclock-baseline-2026-07.md. Do not touch feasibility tolerances; do
not re-run the recorded negative benches.
```

### 4B · Persisted year-1 basis cache — **Opus**

```text
Task: kill the recurring year-1 cold P0 (135-235 s per calibrate-iterate run).
Persist DispatchModel.export_cross_year_basis() output per (iso, year, T) at bundle
close as NPZ (int status vectors + unit_ids + a layout fingerprint: hash of unit_ids,
n_zones, T, git SHA) — NEVER pickle (compat clause 4: disposable, schema key,
delete-and-recapture on mismatch). Opportunistically apply the newest stored basis at
year-1 P0 for the same iso-year; apply_cross_year_basis already remaps/repairs and
falls back cold, so a stale basis costs iterations, never correctness. Default ON for
calibration CLIs, hard OFF under the goldens/replay determinism env
(MARKET_SIM_WARMSTART_XYEAR=0 already pins those paths — verify). Store under a
gitignored results/basis-cache/. Verify: bit-identical objective/prices/dispatch vs
cold on one ERCOT + one MISO year (diff_warmstart_bundles); timing recorded in the
baseline doc.
```

### 4C · Forecast-path warm-start unblock — **Fable** *(owner decision D-9 to flip)*

```text
Task: warm-start backlog #4 — the 25-year forecast horizon runs every P0 cold. First
re-verify the current wiring (xyear default-ON for backcast CLIs; runner.py hard-codes
xyear_cache=None, statically asserted by tests/test_xyear_warmstart_default.py).
1. Audit exactly which evolve_fleet / storage-entry screen inputs read realized
   per-unit dispatch (basis-dependent) vs the price-based attainable-margin
   construction (basis-independent — prices are bit-identical under warm start).
2. Make the realized-dispatch readers tie-invariant (aggregate to plant level before
   thresholding, or round margins to a documented epsilon with a citation comment).
3. Thread xyear_cache through run_scenario_iso behind a DEFAULT-OFF flag
   (ScenarioConfig field, rule 24 — no env knob), update the static assertion test to
   pin the default rather than the wiring.
4. A/B: full-horizon run (scripts/run_full_horizon.py, one ISO) warm vs cold —
   capacity trajectory (evolution ledgers) must be IDENTICAL year-by-year. Present the
   A/B to the owner (D-9); do NOT flip the default in this session.
Deliverable: the audit table, the flag, the A/B evidence, timings. Expected ~1.9x per
warm year x 24 years.
```

### 4D · Operational wall-clock & forecast-surface fixes — **Opus**

```text
Task: the operational lever bundle.
1. NEW scripts/run_isos_concurrent.py: takes (iso, out-dir) jobs; enforces rule-12 cap
   (default 2; refuse two per-plant/co-opt-class ISOs together — encode the ISO memory
   classes from wallclock-baseline-2026-07.md); sets MALLOC_ARENA_MAX=2,
   MARKET_SIM_HIGHS_THREADS=1, OMP_NUM_THREADS=1; tees per-ISO logs; fails loudly on
   child OOM/nonzero exit. Pure orchestration, in-session only.
2. Sub-instrument the backcast results_write window (run_calibration_full.py
   ~:3873-4017) into parquet-write vs sidecar/scoring components (one log line). Only
   if parquet dominates: bench lz4/no-dictionary on a captured MISO-size table —
   check FIRST whether golden/repro gates hash bundle bytes (a compression change
   alters them) and report before adopting.
3. Run the one missing HiGHS bench — setOptionValue('parallel','on') / PAMI simplex —
   on the archived LP captures; record the verdict (either way) in
   wallclock-baseline-2026-07.md. Never touch tolerances.
4. Route results/cache.py CACHE_ROOT and matrix.py's results/ensemble path through
   NEW config/paths.py entries (RESULTS_ROOT, ENSEMBLE_DIR), keeping cache.CACHE_ROOT
   as a mutable module attribute (tests monkeypatch it) and adding the
   with cache.cache_root(tmp) contextmanager (absorbing the 11 copy-pasted
   save/patch/restore dances). Add the cache-epoch policy from compat clause 2 to the
   plan doc + a staleness note in cache.py's docstring.
5. run_sweep worker cap: NEW src/market_sim/pipeline/members.py
   run_member_configs(configs, iso, workers, cap=2, stride=None) with public run_pair;
   runner.run_sweep (currently UNCAPPED cpu-1 — rule-12 violation), ensemble._run_configs,
   matrix.run_matrix, and both pb5 drivers become thin callers. (Coordinate with 3J's
   api.py if both are in flight.)
6. Ensemble fixes: derive year ranges from the member's stored config (or is_cached
   guards) in summarize_ensemble/_member_metric_values — the committed narrowed-horizon
   YAMLs currently crash at aggregation; promote results/export._summarize_year to a
   public summarize_cached_run used by all three loops.
7. Shared pipeline/timing.py::log_year_phase_timing consumed by both orchestrators
   (the log format the baseline doc parses must not drift); convert the three
   remaining iterrows loops (fleet.py:7538, fleet.py:8822, renewables.py:791) to
   itertuples while touching.
8. Structural-prior inversion: commit the statmode residuals as the versioned JSON
   artifact structural_prior.write_prior_artifact already defines; fit_prior reads
   the artifact as canonical; the dashboard-payload regex decode becomes a
   consistency-check test; exempt STATMODE_PROBE_RUNS payloads from retention pruning
   (coordinate with 1C).
Verify: byte-identity where solve-touching (4, 5 are not; 7's iterrows conversions
are — gate them); fast suite green; timings recorded.
```

---

## Wave 5 — Restructure & polish (after Waves 2–4)

### 5A · tests/ subdirectory migration — **Opus**

```text
Task: reorganize the flat 275+-file tests/ dir. Preconditions landed: root conftest
(0B), helpers (2D). Structure: tests/unit/{config,data,model,pipeline,policy,results}/
mirroring src; tests/curation/ (test_curate_* + test_consume_* + lib tests);
tests/iso/{ercot,caiso,miso,nyiso,neiso,pjm}/; tests/scoring/ (verdict/keeper/
dashboard/legitimacy); tests/regression/ (smoke + golden). Execute as pure `git mv`
batches (never regenerated content — many files >300 lines); per batch: fix the
Path(__file__) depth constants in the moved files (54 files carry them — prefer
switching to tests.helpers.REPO_ROOT), run full collection, then push and
blob-verify. tests/golden/ and tests/fixtures/ stay put. testpaths stays ["tests"].
Delete the 21 per-file sys.path bootstrap headers (conftest covers them). Keep the
scoring cluster's paths quoted in .claude/docs updated in the same PR. Prune or
document tests/fixtures/backcast_runs stale fixtures. Verify: collected test count
identical before/after (record the authoritative number); full serial suite green.
```

### 5B · CLAUDE.md slim + stable rule IDs — **Fable** *(owner decision D-6)*

```text
Task: slim CLAUDE.md ~43.7 KB -> ~22-25 KB WITHOUT weakening enforcement. Surgical
Edits only; intentional-shrink label; owner pre-approves the diff (D-6).
1. Add stable inline IDs at each rule head ([R-STRUCT], [R-VECTOR], ... [R-HOLDOUT]
   for 22, [R-PUSH] for 27) keeping ordinal numbering intact — additive, done first
   in its own commit so citations gain a stable anchor before any slimming.
2. Move amendment/incident NARRATIVES (not norms) to their canonical homes and leave
   one-line pointers: rule 20's two owner-amendment stories -> rubric version history;
   rule 22's amendment genealogy -> holdout-policy-memo; rule 27's Sonnet-truncation
   incident -> NEW docs/governance/rule-history.md (which also owns the audit N<->N+1
   mapping paragraph). Every normative sentence, cap, gate/flag name, CI pointer, and
   the admissibility tests STAY verbatim.
3. Capacity Evolution section -> step chain + gate names + spec §5.x pointers;
   Dispatch & Commitment -> the 4-line operational summary (P0/P1 only; P2 archived
   behind --enable-legacy-p2; the two P1-native bridges by gate name) + pointers to
   spec §1.6 and the ERCOT diagnosis doc.
4. Update the Reference Docs list (add docs/codebase/, docs/README.md, the two new
   refactor docs).
Verify: a side-by-side norm inventory in the PR body proving every rule's normative
content survives; push with blob verification; file-integrity-guard passes via the
label.
```

### 5C · Dashboard frontend hardening — **Opus**

```text
Task: close the scorer-drift and generated-file traps on the deployed site.
1. Extract the two inline JS modules to files: docs/codebase-site/js/backcast-runs.js
   (~1,760 ln out of backcast-runs.html) and calibration-status.js — mechanical
   extraction, byte-preserving logic, intentional-shrink label (the HTML shrinks >30%).
2. Stop hand-mirroring scorer constants: emit them from calibration_verdict's module
   constants via build_status.py/build_manifest.py into a generated consts JS
   (window.BC.rubricConsts) the pages import; delete the 'mirrors ... exactly' copies;
   document that capScore's only remaining implementation is now generated-fed (its
   _backcast_shell.py reference no longer exists).
3. Generated-file marking: register_hindcast.render_page() emits an explicit
   GENERATED header into forecast-validation.html; add it + the preview copies of
   manifest.js/benchmark.js/completeness.js to .gitattributes as linguist-generated.
4. Pin one d3 + one gsap version from one CDN with SRI across all 18 pages, or vendor
   the two minified files into js/vendor/ (self-contained preferred — matches the
   site's data design).
5. Owner decision D-7 execution: archive or revive the dormant frontend/ scenario app
   (pages + js only — frontend/data/backcast NEVER moves); refresh
   docs/frontend-audit.md's successor note.
Verify: deploy-pages workflow_dispatch run renders the site correctly; dashboard
byte-parity for unchanged runs; keeper badge + hash routes work on the preview.
```

### 5D · scripts/ phase-2 residue — **Opus**

```text
Task: finish the scripts tree. 1. Archive (PR #2486 discipline: git mv + reference
rewrite): the miso-73 rejected-probe trio (gen_miso73_attestation.py,
miso73_perseam_validate.py, run_miso73_seam_probe.py — adjudicated REJECTED
2026-07-18), regen_caiso_bench_cems.py, scripts/data/
build_ercot_storage_as_2023_estimate.py (self-declared SUPERSEDED). Keep miso-72
(current keeper) and miso-74 (in-flight). 2. Write the keeper-rotation rule into
scripts/README.md (a superseded keeper's gen_*_attestation/driver/validate scripts
move to archive/ when the next keeper registers). 3. git mv profile_lp_memory.py +
diff_warmstart_bundles.py -> scripts/diagnostics/ (update any references same PR).
4. Optionally segregate scripts/probes/ non-Python repro artifacts (28 files, .patch/
.xz.b64/_chain.sh) into scripts/probes/artifacts/ with a README row. 5. Standing core
stays at top level — verify against the Wave-0A reference lint that nothing quoted by
CLAUDE.md/skills/workflows/tests moved. Verify: reference lint green; fast suite
green; scripts/README.md table updated.
```

---

## Sequencing summary

| Wave | Sessions | Parallelism | Models |
|---|---|---|---|
| 0 | 0A 0B 0C 0D | all parallel (0A after D-2) | Opus ×3, Sonnet ×1 |
| 1 | 1A 1B 1C 1D 1E | all parallel | Opus ×4, Sonnet ×1 |
| 2 | 2A 2B 2C 2D | all parallel | Opus ×4 |
| 3 | 3A→3I in order, 3J own track | **max 2 concurrent**; 3G/3H/3J serialized | Fable ×10 |
| 4 | 4A 4B 4C 4D | 4A∥4B, then 4C∥4D | Fable ×2, Opus ×2 |
| 5 | 5A 5B 5C 5D | all parallel | Fable ×1, Opus ×3 |

Owner-decision gates: D-1 before 0C; D-2 before 0A; D-3 before 1C's sweep; D-4/D-10
before 1A; D-5 anytime (separate session if "apply"); D-6 before 5B; D-7 before 5C
item 5; D-9 decides 4C's default flip only.
