# Testing

The test suite lives in `tests/` (one file per module, ~355 files). This page
documents the **directory layout**, the **two lanes** you run it in, the
**marker taxonomy** that separates them, the **shared helper layer**, and the
**two golden systems**.

## Directory layout

The flat 355-file `tests/` directory was reorganized by Wave 5A of the
refactor-consolidation plan. `testpaths = ["tests"]` in `pyproject.toml` is
unchanged and still resolves every subdirectory (it exists to keep root
`pytest` out of `scope2-lce-portfolio/tests`, whose conftest imports a
non-dependency — G-47). There is exactly one `conftest.py` under `tests/`; the
subdirectories deliberately add none, so the fixtures and the `slow` autotag
apply everywhere.

| Directory | Holds |
|---|---|
| `tests/unit/{config,data,model,pipeline,policy,results}/` | Mirrors `src/market_sim/`: the hermetic unit tests for each subpackage. |
| `tests/curation/` | The `data/raw` → `data/clean` pipeline: `test_curate_*`, `test_consume_*`, `test_derive_*`, `test_fetch_*`, `test_build_*`, plus the `clean_io`/registry/data-dictionary contract tests. |
| `tests/iso/{ercot,caiso,miso,nyiso,neiso,pjm}/` | Per-ISO mechanism, bin, seam and offer-surface tests. |
| `tests/scoring/` | Verdict, keeper, benchmark/basis, dashboard-payload and legitimacy-diagnostic tests. |
| `tests/regression/` | Smoke, golden, byte-identity and frozen-surface guards — including the nine facade / persisted-identity tests that CI's **blocking** `refactor-guards` job names by exact path. |
| `tests/helpers/` | Shared builders, mixins and `REPO_ROOT` (below). Stays put. |
| `tests/golden/`, `tests/fixtures/` | Committed artifacts. Stay put — `tests/fixtures/backcast_runs/` holds the three statmode run payloads `test_structural_prior.py` symlinks back in after the dashboard prune, so none of them is stale. |

Two conventions the layout depends on:

* **Never derive the repo root by counting `__file__` parents.** Import
  `REPO_ROOT` from `tests.helpers` — it is depth-independent, so a test keeps
  working wherever it lands. Committed artifacts under `tests/` are addressed
  as `REPO_ROOT / "tests" / "golden" / ...`.
* **No per-file `sys.path` bootstrap for the repo root or `src/`.** The root
  `conftest.py` already puts both on `sys.path`. Only the handful of tests that
  import a loose `scripts/` or `scripts/data/` module still insert a path, and
  they build it from `REPO_ROOT`.

## The two lanes

| Lane | Command | When |
|---|---|---|
| **Fast** | `pytest -n auto -m "not slow and not integration and not fulldata"` | Every edit / pre-commit. Hermetic unit tests only, run in parallel across cores (`pytest-xdist`). Seconds-to-a-minute. |
| **Full** | `pytest` | Pre-push / CI. Everything, serial. Includes the data-backed parity tests and full-8760 LP solves. |

`addopts = "--strict-markers"` is set in `pyproject.toml` — an unregistered
`@pytest.mark.<typo>` is a hard error, not a silently-ignored no-op. There is
deliberately **no default `-m` deselection** in `addopts`: a bare `pytest`
always runs the full suite; the fast lane is opted into on the command line.

Run the fast lane under `-n auto` (xdist) for the parallel speedup; the full
lane runs serial because the data-backed and LP tests each hold several GB and
must not run concurrently (CLAUDE.md rule 12).

## Marker taxonomy

Registered in `pyproject.toml` (`[tool.pytest.ini_options].markers`):

| Marker | Meaning |
|---|---|
| `slow` | Regenerates clean data, runs the model, or builds a full-8760 LP. |
| `integration` | Exercises the real data tree; not a hermetic unit test. |
| `fulldata` | Needs the real `data/raw` tree present. Applied automatically by the `requires_raw` helper (below); replaces the old ad-hoc raw-data `skipif`s. |
| `golden` | A byte-identity / band-regression golden guard (see below). |

A test that reads real data should carry `integration` (and `slow` if it also
solves); a test that reads `data/raw` specifically should gate with
`requires_raw`, which adds `fulldata` for you.

## Shared helpers (`tests/helpers/`)

Import the common builders and mixins instead of re-rolling them:

```python
from tests.helpers import (
    make_gen, make_fleet, base_scenario, backcast_scenario,  # builders.py
    solve_tiny,                                               # solve.py
    CleanDirTestCase, RawFixtureTestCase, requires_raw,       # base.py
    assert_clean_valid, read_clean_or_fail,                   # clean_asserts.py
    REPO_ROOT,
)
from tests.helpers import raw_fixtures  # per-source raw-fixture writers
```

* **`make_gen` / `make_fleet`** — one `Generator` / a `FleetArrays` with
  trivial-case defaults (the 1-gen/1-zone shape). `make_fleet` is byte-compatible
  with the old inline `_make_fleet` wrappers.
* **`base_scenario(mode, iso, **overrides)`** — a flat `ScenarioConfig`.
  **`backcast_scenario(...)`** — the calibration config via
  `pipeline.backcast_config` (the single source of truth for backcast wiring).
* **`solve_tiny(fleet, demand_by_zone, hours=24, ...)`** — wraps the
  incidence/TTC/availability assembly around `solve_dispatch` for the
  trivial-case LP. Every extra kwarg passes straight through.
* **`CleanDirTestCase`** — `unittest` mixin that redirects `paths.CLEAN_DIR` to a
  per-test tempdir and restores it. Subclass it and call `super().setUp()`
  instead of hand-rolling the save/point/restore dance. `RawFixtureTestCase`
  adds a scratch `raw_dir`. The pytest-native equivalent is the `tmp_clean_dir`
  fixture in `tests/conftest.py`.
* **`requires_raw(*paths)`** — decorator that marks a test `fulldata` **and**
  skips it when a required `data/raw` path is missing. Supersedes the per-file
  `@pytest.mark.skipif(not _raw_present(), ...)` idiom.
* **`raw_fixtures`** — reusable per-source writers (`write_eia860`,
  `campd_unit_extract`, `eia930_hourly`, generic `write_csv`/`write_parquet`).

Path handling: root `conftest.py` puts the repo root and `src/` on `sys.path`
so `market_sim.*` and `scripts.*` resolve however pytest is invoked;
`tests/conftest.py` adds the `repo_root` and `tmp_clean_dir` fixtures.

## The two golden systems

1. **Forecast band goldens** (`tests/golden/ercot_2026_2040.json` +
   `.run_config.json`, guarded by `tests/regression/test_golden_forecast_bands.py`). The
   fixture-presence check runs every PR; the real 15-year ERCOT solve is gated
   behind `RUN_GOLDEN_FORECAST=1` (weekly tier). A band FAIL is a finding —
   never auto-regenerate; reseeding requires
   `scripts/golden_forecast_bands.py seed --reason ...`.
2. **Byte-identity keeper goldens** (the refactor contract). Pure code motion
   must reproduce keeper solves byte-for-byte: capture before with
   `scripts/capture_keeper_goldens.py`, gate after with
   `scripts/regression_gate.py --mode byte` (atol=rtol=0). Regenerating
   `tests/golden/ercot_2026_2040.json` needs `seed --force --reason` with owner
   authorization. The escalation procedure on a byte-mode failure is codified in
   `docs/refactor-consolidation-plan-2026-07.md` §8.

## Regenerating clean data

The data-backed lane needs the derived `data/clean` tree, which is gitignored.
Regenerate it from `data/raw` with `python scripts/regenerate_clean.py`
(`--list` shows the datatypes; pass names to rebuild a slice). Curation tests
never touch the real tree — they redirect `CLEAN_DIR` via `CleanDirTestCase` /
`tmp_clean_dir`.
