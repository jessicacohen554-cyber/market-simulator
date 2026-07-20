# Testing

The test suite lives in `tests/` (one file per module, ~300 files). This page
documents the **two lanes** you run it in, the **marker taxonomy** that
separates them, the **shared helper layer**, and the **two golden systems**.

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
   `.run_config.json`, guarded by `tests/test_golden_forecast_bands.py`). The
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
