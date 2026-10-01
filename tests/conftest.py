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


# The fast lane's time budget (cleanup-A, 2026-10-01). These are real behaviour
# tests that each run a multi-year runner or a full-data loader for 20-85 s on
# 2 workers; together they were ~1/3 of the fast tier's 10m39s wall at
# 4471ad31. Listed by exact node id with the measured duration; add a line when
# a test crosses ~20 s, remove it when the test is made cheap.
SLOW_NODEIDS = {
    "tests/scoring/test_crossover_harness.py::TestCrossoverRunnerPath::test_forward_year_demand_not_from_realized_loader",  # 83 s
    "tests/unit/data/test_retiree_window_extension.py::TestPreserveIsStrictlyAdditive::test_shared_key_keeps_preserved_record_and_new_key_is_added",  # 81 s
    "tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py::TestSeamPeakInertWhereThereIsNoMeasuredLoad::test_crossover_forward_year_keeps_the_growth_path",  # 81 s
    "tests/test_regional_renewable_cf.py::test_matches_the_egrid_derivation",  # 69 s
    "tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py::TestSeamPeakArmed::test_arming_adds_no_demand_read",  # 55 s
    "tests/unit/pipeline/test_runner.py::TestRunScenarioIso::test_rerun_skips_all_cached_years",  # 53 s
    "tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py::TestSeamPeakInertWhereThereIsNoMeasuredLoad::test_forecast_run_is_byte_identical_armed_and_unarmed",  # 51 s
    "tests/curation/test_eia_loader.py::TestWeatherPoolWidening::test_pjm_2019_2020_demand_resolves_from_hourly_extract",  # 48 s
    "tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py::TestSeamPeakArmed::test_armed_hindcast_screens_see_the_measured_peak",  # 48 s
    "tests/curation/test_eia923_renewable_backfill.py::TestLiveCaiso2025::test_full_year_per_class_benchmark",  # 38 s
    "tests/unit/data/test_dam_outage_wiring.py::DamOutageWiringTest::test_caiso_per_plant_precedence_and_fallback",  # 35 s
    "tests/scoring/test_calibration_verdict_price_unscored.py::RegisteredRunsTests::test_no_registered_run_carries_the_block",  # 31 s
    "tests/curation/test_egrid.py::LoaderTests::test_build_fossil_co2_rates",  # 30 s
    "tests/unit/pipeline/test_runner.py::TestRunSweep::test_two_configs_create_two_cache_dirs",  # 29 s
    "tests/unit/pipeline/test_capacity_screen_peak_measured_hindcast.py::TestSeamPeakArmed::test_unarmed_hindcast_screens_see_the_GROWN_weather_peak",  # 27 s
    "tests/unit/results/test_ensemble_sampler.py::TestExportSamplerEnsemble::test_structural_prior_adds_published_layer",  # 26 s
    "tests/unit/pipeline/test_runner.py::TestRunScenarioIso::test_three_years_create_three_cache_files",  # 26 s
    "tests/curation/test_eia_loader.py::TestDemandProfileCleanSeam::test_load_demand_uses_repaired_partition_over_raw_spike",  # 24 s
    "tests/curation/test_eia_loader.py::TestWeatherPoolWidening::test_pjm_2021_demand_and_renewables_full_year",  # 24 s
    "tests/iso/caiso/test_caiso_locational_as.py::test_loader_shape_and_keys[2023]",  # 22 s
}


def pytest_collection_modifyitems(config, items):
    """Tag the measured-slow tests (classes above, node ids in SLOW_NODEIDS) ``slow``."""
    slow = pytest.mark.slow
    for item in items:
        if item.nodeid in SLOW_NODEIDS or any(
            sub in item.nodeid for sub in _SLOW_NODEID_SUBSTRINGS
        ):
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


@pytest.fixture
def published_acr_clean_dir(tmp_path, monkeypatch) -> Path:
    """A tmp ``CLEAN_DIR`` carrying the REAL published avoidable-cost-rate table.

    The capx D62 / D74 gates read PJM's published default gross Avoidable Cost
    Rate through :mod:`market_sim.data.avoidable_cost_rate`, whose seam reads
    the ``capacity-market-avoidable-cost-rate`` clean datatype — a DERIVED,
    gitignored partition that no test fixture ever built. Marking those tests
    ``fulldata`` was necessary but NOT sufficient: with ``data/raw`` fully
    present and the clean tree simply unbuilt, every value-returning entry
    point in that seam raises ``PublishedBarUnavailable`` by design (so an
    armed gate can never degrade silently), so the tests were red on any
    checkout that had not happened to run the curation script (capx D89).

    So build it here instead of assuming it: curate the TRACKED raw source
    through the real intake pipeline into a scratch tree. The assertions then
    read whatever ``data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv``
    currently says — the live source of truth — rather than whatever some
    earlier session last curated onto this host, so a stale or absent real
    ``data/clean`` can neither pass them nor fail them.

    Pair it with :func:`tests.helpers.base.requires_raw` on the raw CSV: that
    decorator carries the ``fulldata`` marker AND skips when the raw input is
    genuinely absent, which is the repo's standing idiom for a raw dependency
    and the half a bare ``fulldata`` marker cannot express.
    """
    from market_sim.data import avoidable_cost_rate as acr_seam
    from scripts.data import curate_capacity_market_avoidable_cost_rate as curate_acr
    from scripts.lib import capacity_market_avoidable_cost_rate as acr

    clean = tmp_path / "clean"
    monkeypatch.setattr(paths, "CLEAN_DIR", clean)
    # ``_read`` is ``lru_cache``d, so a frame read under the real CLEAN_DIR by
    # an earlier test would survive the redirect. Clear on the way in and on
    # the way out, so this fixture neither inherits nor leaks a cached frame.
    acr_seam._read.cache_clear()
    written = curate_acr.curate(isos=["PJM"])
    if not written:
        raise AssertionError(
            "published avoidable-cost-rate raw source produced no partition; "
            f"expected {acr.raw_dir_for('PJM', paths.RAW_DIR) / 'pjm.csv'}"
        )
    yield clean
    acr_seam._read.cache_clear()


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
