# Backcast-artifacts refactor — remaining consumer migrations (handoff)

> Status: ACTIVE handoff. Branch `claude/backcast-artifacts-refactor-8w5y8d`.
> The three shared libraries and 8 of the 13 consumer migrations are landed and
> byte-verified; this documents the 5 files not yet migrated and the exact,
> byte-parity-preserving edits each needs.

## What is done (landed on the branch, byte-verified)

New libraries (stdlib-only) + tests:
- `scripts/lib/backcast_artifacts.py` — the single home for dashboard artifact
  IO: `gzb64`/`ungzb64`, `encode_run_js`/`decode_run_js`,
  `write_bench_part`/`load_bench_part`, `render/write/parse_manifest_js`,
  `iter/load/write_sidecar`, `resolve_run_id`, `bundle_dir_for`, and the
  `DATA`/`REGISTRY`/`RUNS`/`BENCH` path constants. `tests/test_backcast_artifacts.py`
  round-trips every committed `runs/<id>.js` + bench part to identical bytes.
- `scripts/lib/benchmark_semantics.py` — `GAS_CLASSES`/`COAL_CLASSES`/`GAS_GROUPS`/
  `COAL_GROUPS`/`OTHER_FOSSIL`, `VINTAGE_RECONCILE_FRAC`, `EIA930_NG_CELL_CORRUPT`
  (+ `_ONSET`), `EIA930_GAS_FOLDS_GEO_BIOMASS`, `gas_foldin_deflation()`.
  `tests/test_benchmark_semantics.py` guards the hard-coded family tuples against
  the live `plant_taxonomy` roll-up.
- `scripts/lib/holdout_policy.py` — `CALIBRATION_YEARS` frozenset + `MARKER_FILE`.

Consumers migrated (each its own commit, verified):
`build_manifest.py`, `render_backcast.py` (+ its importlib→package import),
`check_registry_payload_parity.py`, `regen_dashboard.py` (importlib→package
import), `build_codebase_site_backcast.py`, `export_forecast_bands.py`,
`dashboard_add_run.py` (importlib→package import), `audit_keepers.py` (holdout).
Steps 5 (all three `importlib.spec_from_file_location` chains → `from scripts
import …`) and 6 (`viz-forecast-bands.js` imports `inflateGz` from `bc-data.js`)
are complete.

Verification baselines captured (unchanged data must reproduce these):
`build_manifest.py` → `manifest.js` sha256 prefix `b41dc5f6447cde5364a7`,
`benchmark.js` `ee9ad7258ac61cddfebd`, `completeness.js` `7fad6cf12ad5b4906701`.
Pre-existing parity-checker state: exit 1, only the nyiso-64 / neiso-60 keepers
missing their payloads (a repo condition, not from this refactor).

## Why these 5 are deferred

`git push` hangs on this remote (the shallow-clone large-pack 413 CLAUDE.md
warns about — confirmed by probe), so `mcp__github__push_files` with full file
content is the only push path. That is fine for files up to ~35 KB, but
`run_calibration_full.py` is **457 KB** — a single full-content push would be
truncated by the response budget (exactly the rule-27 incident). The other
three (88–116 KB) are feasible but large; do them one file per commit with the
mandatory ≥300-line blob verification after each push.

## Remaining edits (all byte-parity-preserving)

### 1. `scripts/score_crossover.py` (34 KB — backcast_artifacts)
- sys.path wrinkle: the module only puts `_SCRIPTS`/`_SRC` on `sys.path` at
  import time (REPO is added later, inside `_load_keepers`), so a module-level
  `from scripts.lib import …` does NOT resolve as-is. After `REPO = …` (~line 70)
  add `if str(REPO) not in sys.path: sys.path.insert(0, str(REPO))` then
  `from scripts.lib import backcast_artifacts as ba  # noqa: E402` (mirrors the
  existing `_SRC`/`_SCRIPTS` guard pattern and the in-function keeper_store import).
- `load_bench_year` (~line 139): `part = V.BENCH_DIR / iso / f"{year}.json.gz"` →
  `part = ba.BENCH / iso / f"{year}.json.gz"`; and
  `obj = json.loads(gzip.decompress(part.read_bytes()))` → `obj = ba.load_bench_part(part)`.
- Drop `import gzip` if it becomes unused (grep first — it likely is, once this is
  the only gzip use).
- Verify: `load_bench_year` returns the same dict for an ISO-year, and the
  quarantine guard still fires before the file open (`_assert_scoreable_year`
  unchanged); `ba.BENCH == V.BENCH_DIR` today (both `<repo>/frontend/data/backcast/bench`).

### 2. `scripts/calibration_verdict.py` (116 KB — backcast_artifacts + benchmark_semantics; MUST stay numpy-free)
backcast_artifacts:
- `DATA_DIR/REGISTRY_DIR/RUNS_DIR/BENCH_DIR` (lines 55–58) → `ba.DATA`/`ba.REGISTRY`/
  `ba.RUNS`/`ba.BENCH`; `COMPLETENESS_DIR = DATA_DIR / "completeness"` unchanged.
- Delete `_decode_run_js` (435–440) and `resolve_run_id` (443–464); instead
  `from scripts.lib.backcast_artifacts import decode_run_js as _decode_run_js, resolve_run_id`
  (ba's defaults equal calibration_verdict's REPO/REGISTRY, so behavior is identical;
  `resolve_run_id` stays re-exported for importers).
- `load_artifacts` bench loop (~484): `json.loads(gzip.decompress(part.read_bytes()))`
  → `ba.load_bench_part(part)`.

benchmark_semantics (delete the by-comment mirrors):
- `GAS_CLASSES`/`COAL_CLASSES` (158–159) → import from `bs`
  (`from scripts.lib import benchmark_semantics as bs`); note `bs.COAL_CLASSES`
  is the taxonomy order — a different order than the current literal but the
  same set, used only in sums/membership (byte-safe).
- `VINTAGE_RECONCILE_FRAC` (229) → `bs.VINTAGE_RECONCILE_FRAC`.
- `CEMS_GAS_ANCHOR_ISOS` (246) → `bs.EIA930_NG_CELL_CORRUPT`;
  `CEMS_GAS_ANCHOR_ONSET` (247) → `bs.EIA930_NG_CORRUPT_ONSET` (keep the local
  names as aliases so the ~1000-line body is untouched).
- The inline fold-in (1036–1041, inside `if fam == "gas" … "other" in e930`):
  `actual -= max(0.0, cf.get("OTHER",0)+cf.get("biomass",0)-e930.get("other",0))`
  → `actual -= bs.gas_foldin_deflation(cf, e930, iso)` (identical inside that guard).
- Verify (numpy-free, runnable here): `calibration_verdict.determine(<id>)` for all
  six keepers, diff the verdict dict before/after — must be identical.

### 3. `scripts/render_calibration_html.py` (100 KB — benchmark_semantics)
- `from scripts.lib import benchmark_semantics as bs`.
- `_GAS_GROUPS` (111) → `bs.GAS_GROUPS`; `_COAL_GROUPS` (112) → `bs.COAL_GROUPS`
  (byte-identical: `bs.GAS_GROUPS == (*classes_for_fuel930("gas"), OTHER_FOSSIL_CLASS)`,
  `bs.COAL_GROUPS == classes_for_fuel930("coal")` — verified against the live
  taxonomy). Keep the `_GAS_GROUPS`/`_COAL_GROUPS` names (tests + archive import them).
- `_VINTAGE_RECONCILE_FRAC` (126) → `bs.VINTAGE_RECONCILE_FRAC`;
  `EIA930_GAS_FOLDS_GEO_BIOMASS` (138) → `bs.EIA930_GAS_FOLDS_GEO_BIOMASS`;
  `EIA930_NG_CELL_CORRUPT` (153) → `bs.EIA930_NG_CELL_CORRUPT`;
  `EIA930_NG_CORRUPT_ONSET` (157) → `bs.EIA930_NG_CORRUPT_ONSET`.
- Delete the `_gas_foldin_deflation` def (264–287); `_gas_foldin_deflation = bs.gas_foldin_deflation`
  (keep the name — `reconcile_vintage_classes` calls it).
- Keep `reconcile_vintage_classes` in place (unchanged; now uses the imported
  constants). Verify: `tests/test_benchmark_basis_default.py` (imports
  `rch._GAS_GROUPS`/`_COAL_GROUPS`/`reconcile_vintage_classes`) stays green.

### 4. `scripts/run_calibration_full.py` (457 KB — holdout_policy) — PUSH-BLOCKED
- `HOLDOUT_CALIBRATION_YEARS` (6267) → `CALIBRATION_YEARS` from
  `from scripts.lib.holdout_policy import CALIBRATION_YEARS, MARKER_FILE`;
  `HOLDOUT_MARKER_FILE` (6268) → `MARKER_FILE` (the relative-string form —
  identical to the current literal, so every message + `repo / …` join is
  byte-stable).
- **Blocker:** 457 KB cannot go through `push_files` in one response. Land it via
  a mechanism that can move a large file byte-exact (e.g. a session/host where
  `git push` works, or a chunked-append protocol). Until then the local literal
  is a parity-tested mirror: `tests/test_holdout_year_gate.py` asserts
  `_RCF.HOLDOUT_CALIBRATION_YEARS == legitimacy.D6_CALIBRATION_YEARS`, so it
  cannot silently drift from the single source.

### 5. `scripts/legitimacy_diagnostics.py` (88 KB — backcast_artifacts + holdout_policy)
- `from scripts.lib import backcast_artifacts as ba` and `from scripts.lib import holdout_policy`.
- `D6_CALIBRATION_YEARS` (410) → `holdout_policy.CALIBRATION_YEARS`;
  `D6_MARKER_FILE` (411) → `holdout_policy.MARKER_FILE` (relative string — the
  `repo_root / D6_MARKER_FILE` join at line 1307 and the `{D6_MARKER_FILE}`
  message at 1347 stay byte-identical).
- `load_bench` (1379–1380): `data = json.loads(gzip.open(path,"rt").read())` →
  `data = ba.load_bench_part(path)` (same dict).
- `load_payload_plants` (1411–1413) and `load_payload_total_load_mwh` (1436–1440):
  the `re.search(r'="(H4sI[^"]+)"', txt)` + gzip-decode is the second copy of the
  payload decoder — replace with `ba.decode_run_js(txt)`. Preserve
  `load_payload_total_load_mwh`'s None-on-missing by wrapping:
  `try: run = ba.decode_run_js(txt) except ValueError: return None`.
  (`ba.decode_run_js`'s general base64 regex extracts the identical string for a
  real payload — every committed payload's base64 begins `H4sI`.)
- Verify: run `legitimacy_diagnostics` D-1/D-2/D-4 on a keeper bundle with floors
  present; the `legitimacy_diagnostics.json` output must be byte-identical.

## Parity tests
Keep `tests/test_holdout_year_gate.py`, `tests/test_audit_keepers.py`,
`tests/test_legitimacy_diagnostics.py` — they still guard run_calibration_full's
un-migrated literal. Once #4 lands they become trivially-true and may be
simplified, but they never need to be deleted.

## Per-PR discipline (rule 27 + task)
Local Edit-tool diffs only; push exact on-disk bytes via `push_files`; after any
push touching a ≥300-line file, fetch it back and confirm the blob SHA equals
`git hash-object` on the local copy before the next commit. The repo's ruff hook
strips a momentarily-unused import on Edit, so add a lib import in the SAME edit
that introduces its first use (or add the use first, the import second).
