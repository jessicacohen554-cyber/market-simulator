"""pytest fixtures shared across the test suite.

The repo-root ``conftest.py`` (one level up) only fixes ``sys.path``; this one
provides the reusable fixtures. Both the fixtures here and the unittest mixins
in :mod:`tests.helpers.base` redirect ``paths.CLEAN_DIR`` the same way — use the
fixture in pytest-style tests, the mixin in ``unittest.TestCase`` classes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market_sim.config import paths
from tests.helpers import REPO_ROOT

# Full-8760 LP-solving test classes that are genuinely slow (measured: the
# TestEndToEnd runner cases ~1-13 s each, the TestPerformance 8760 solve ~27 s)
# but live in a 900+-line module. Marking them here (rather than editing that
# large file) keeps the slow gate close to the lane config and avoids a
# rule-27 full-file rewrite. Matched by nodeid substring at collection time.
_SLOW_NODEID_SUBSTRINGS = (
    "test_soundness.py::TestEndToEnd",
    "test_soundness.py::TestPerformance",
    # HOUSE-2: same class of test, same reason. TestFullYearPerformance builds
    # and solves the 8760 x (200 gen + 7 zone + 5 storage) ERCOT LP and then
    # asserts WALL-CLOCK budgets on it (build < 3 s, build + solve < 30 s).
    # Serial it passes (~27 s of the 30 s budget); under the fast lane's
    # ``-n 2`` xdist contention the co-scheduled worker pushes it past the
    # budget and it fails intermittently. Both the marker taxonomy and the
    # lane definition already say where it belongs: ``slow`` is "runs the
    # model / full-8760 LP" and the fast lane is "hermetic unit tests only"
    # (docs/testing.md). Timing assertions are meaningless under contention
    # anyway — the full (serial) lane is the only place this budget means
    # anything, and it still runs there.
    "test_integration.py::TestFullYearPerformance",
)


def pytest_collection_modifyitems(config, items):
    """Tag the measured-slow full-8760 LP test classes with ``slow``."""
    slow = pytest.mark.slow
    for item in items:
        if any(sub in item.nodeid for sub in _SLOW_NODEID_SUBSTRINGS):
            item.add_marker(slow)


@pytest.fixture(autouse=True)
def _reset_eia860_vintage():
    """Restore the EIA-860 vintage PROCESS GLOBAL after every test.

    ``paths.set_eia860_vintage`` flips a module-level global that re-points every
    EIA-860-derived loader (fleet operable/retired/proposed snapshots, storage,
    COD map, the derive artifacts keyed on them) at
    ``data/raw/eia-860/vintage_<year>/``. ``runner.run_scenario_iso`` sets it
    once per solve from ``ScenarioConfig.eia860_vintage_year``, and NOTHING
    resets it when the solve returns — so any test that drives a backcast or a
    vintage-seeded hindcast through the runner silently re-points the loaders
    for the REST OF THE SESSION.

    That is the fast tier's order-dependent failure family (triage §6.2):
    ``tests/test_crossover_harness.py`` runs a 2023-vintage ERCOT crossover
    through ``run_scenario_iso``, and five later tests — the three
    ``test_fleet`` planned-additions / retired-within-window cases,
    ``test_derive_coal_sigmoid``'s MISO provenance freeze, and
    ``test_outages``'s NEISO floor-exemption case — then read the 2023 snapshot
    instead of the canonical one and fail. Every one passes in isolation, which
    is exactly why they read as flakes rather than as one leaked global.
    Bisected to the polluter 2026-07-26; this resets it at the source rather
    than adapting any victim.

    ``tests/test_cod_ramp.py::TestEia860VintageSelection`` already carried this
    teardown by hand ("never leak a vintage into other tests") — this generalizes
    that convention to the whole suite so a new runner-driving test cannot
    reintroduce the class.

    An independent 2026-07-27 bisect of the same family (the ``test_storage``
    EIA-860 members plus ``test_coal_sync_tranche``'s scope freeze) landed the
    standing detector ``scripts/diagnostics/repro_eia860_vintage_leak.py``
    (exit 1 if this leak ever returns) and an ``addCleanup`` reset in the
    polluting crossover-harness test itself, which keeps that file hermetic
    under bare ``unittest`` where this fixture does not run.
    """
    yield
    paths.set_eia860_vintage(None)


@pytest.fixture
def repo_root() -> Path:
    """The repository root (directory holding ``pyproject.toml``)."""
    return REPO_ROOT


@pytest.fixture
def tmp_clean_dir(tmp_path, monkeypatch) -> Path:
    """Redirect ``paths.CLEAN_DIR`` to a tempdir for one test.

    The pytest-native counterpart to :class:`tests.helpers.base.CleanDirTestCase`:
    ``monkeypatch`` restores the original attribute automatically at teardown,
    so a curation test can ``write_clean``/``read_clean`` against a scratch tree
    without touching the real ``data/clean``. Yields the redirected directory.
    """
    clean = tmp_path / "clean"
    monkeypatch.setattr(paths, "CLEAN_DIR", clean)
    return clean


# --------------------------------------------------------------------------- #
# The SOLVE SURFACE, neutralized by default (capx D79; ercot-253 2026-09-06)
# --------------------------------------------------------------------------- #
# Since capx D79 `ScenarioConfig.cache_key()` also carries any registry row that
# has MOVED off its frozen declaration. That is deliberate and it is how a
# registry repair takes its own bundle — but it means every test that pins a
# cache-key literal is pinning two independent things at once: the config's own
# field set and defaults, AND whatever registry values happen to be repaired at
# that moment. Those tests are named for a FIELD ("the D30 arming moves the
# ERCOT forecast key"), and a registry repair in an unrelated lane should not
# make them fail with "the arming moved the key".
#
# `tests/regression/test_persisted_identity.py` already solved this for its own
# pins with the `config_identity_only` fixture, whose docstring states the
# contract this fixture generalizes: "a registry move fails
# PINNED_SURFACE_ROWS_BY_ISO and nothing else". It held only inside that one
# file, so the FIRST real registry move (ercot-253's measured ERCOT
# `NUCLEAR_MONTHLY_CF_BY_YEAR` 2021 row, owner ruling 2026-09-06) failed 12
# field-arming pins across nine other lanes' files that had nothing to do with
# it. Making the neutralization the default is that contract, applied where the
# pins actually live.
#
# WHAT IS NOT WEAKENED. The surface's own pins are untouched and still fail
# loudly on any move: `PINNED_SURFACE_ROWS_BY_ISO` (per-ISO fingerprint + row
# count, each advance carrying a dated cause block) and
# `LEDGERED_SURFACE_MOVES_BY_ISO` (an UNLEDGERED move is still an error). Tests
# that are ABOUT the surface reaching the key opt out with
# `@pytest.mark.solve_surface_live`.
@pytest.fixture(autouse=True)
def _solve_surface_neutralized(request, monkeypatch):
    """Measure ``cache_key()`` as a statement about the CONFIG alone.

    Autouse, so it reaches ``unittest.TestCase`` methods too (they cannot take
    fixture arguments, but autouse fixtures still apply to them).
    """
    if request.node.get_closest_marker("solve_surface_live"):
        return
    from market_sim.config import scenarios as _scen

    monkeypatch.setattr(_scen, "moved_rows", lambda iso: {}, raising=True)
    monkeypatch.setattr(_scen, "applicable_epochs", lambda config: [], raising=True)
