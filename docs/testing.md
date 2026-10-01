# Testing

## Layout

`tests/` mirrors the code; one `conftest.py` (fixtures, the solve-surface
neutralization and the slow-test list) applies everywhere.

| Directory | Holds |
|---|---|
| `tests/unit/{config,data,model,pipeline,policy,results}/` | Hermetic unit tests mirroring `src/market_sim/`. |
| `tests/curation/` | The `data/raw` → `data/clean` pipeline and the schema / data-dictionary contract. |
| `tests/iso/<iso>/` | Per-ISO mechanism, bin, seam and offer-surface tests. |
| `tests/scoring/` | Verdict rubric, keeper audit, dashboard payload and legitimacy-diagnostic tests. |
| `tests/regression/` | Smoke, facade re-export and persisted-identity guards. |
| `tests/helpers/`, `tests/golden/`, `tests/fixtures/` | Shared builders and committed fixtures. |

Import `REPO_ROOT` from `tests.helpers` (never count `__file__` parents); the
root `conftest.py` already puts the repo and `src/` on `sys.path`.

## Two lanes

| Lane | Command | When |
|---|---|---|
| Fast | `pytest -n auto -m "not slow and not integration and not fulldata"` | Every edit; the CI `fast-tests` job runs it on 2 workers. |
| Full | `pytest` | Pre-push; serial, includes data-backed parity tests and full-8760 solves. |

`--strict-markers` is on; there is no default `-m` deselection. Tests that take
over ~20 s on the fast lane are listed by node id in `tests/conftest.py`
(`SLOW_NODEIDS`, each with its measured duration) and carry `slow` from there;
add a line when a test crosses the budget, remove it when the test is made cheap.

## Marks

| Mark | Meaning |
|---|---|
| `slow` | Regenerates clean data, runs the model, or builds an 8760 LP. |
| `integration` | Exercises the real data tree. |
| `fulldata` | Needs `data/raw`; applied by the `requires_raw` helper, which also skips when the path is absent. |
| `golden` | Band-regression guard (`tests/regression/test_golden_forecast_bands.py`; the 15-year solve runs only with `RUN_GOLDEN_FORECAST=1`). |
| `solve_surface_live` | Opt out of the autouse solve-surface neutralization for a test that is about the surface entering the cache key. |

## One rule for new tests

A test asserts **behaviour**, never a stored digest, version string, cache-key
literal or registered number reproduced from a frozen derive. Such pin-ledger
tests go red on every unrelated data or default change and teach lanes to
ignore CI. Where an invariant matters, assert the property: an explicit default
hashes like an absent one; an armed key differs from the unarmed key; a derived
table equals its derive on the same inputs. (The solve-surface fingerprint pins,
pinned default keys, requirements-vs-lock equality and golden-digest tests were
removed on 2026-10-01 under this rule.)

## Shared helpers (`tests/helpers/`)

```python
from tests.helpers import (
    make_gen, make_fleet, base_scenario, backcast_scenario,  # builders
    solve_tiny,                                               # 24-h trivial LP
    CleanDirTestCase, RawFixtureTestCase, requires_raw,       # base classes / gate
    assert_clean_valid, read_clean_or_fail, REPO_ROOT,
)
from tests.helpers import raw_fixtures  # per-source raw-fixture writers
```

`CleanDirTestCase` and the `tmp_clean_dir` fixture redirect `paths.CLEAN_DIR`
to a tempdir, so curation tests never touch the real tree. Trivial cases first
(1 gen, 1 zone, 24 h), then scale.

## Refactor byte-identity (on demand)

Pure code motion must reproduce keeper solves byte-for-byte: capture before
with `scripts/capture_keeper_goldens.py`, gate after with
`scripts/regression_gate.py --mode byte`. Captures are not committed.

## Regenerating clean data

`data/clean` is gitignored. A solve container runs
`python scripts/regenerate_clean.py --solve-profile <ISO>` (≈45 s, incremental
via each datatype's `.manifest.json`; `--force` rebuilds); a bare
`regenerate_clean.py` rebuilds everything (20+ min, emissions alone 17 min).
Registry, manifest key and timings: `docs/clean-data-profiles.md`.
