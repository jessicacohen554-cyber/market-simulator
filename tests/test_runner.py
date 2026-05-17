"""Tests for the simulation runner and its command-line interface.

The dispatch LP is mocked throughout: ``solve_dispatch`` is patched to
return a synthetic :class:`DispatchResult` so the tests exercise the
runner's orchestration -- fleet evolution, caching, sweeps and CLI
parsing -- without the cost of solving a full-year model.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from market_sim import runner
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache


def _fake_solve(fleet, demand, *args, **kwargs):
    """Return a synthetic ``DispatchResult`` sized to the fleet and demand."""
    n_gen = fleet.n_gen
    T = demand.shape[1]
    n_zones = demand.shape[0]
    return DispatchResult(
        dispatch=np.full((n_gen, T), 5.0),
        wind_dispatched=np.zeros((n_zones, T)),
        solar_dispatched=np.zeros((n_zones, T)),
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=np.full((n_zones, T), 30.0),
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )


class RunnerTestBase(unittest.TestCase):
    """Base fixture redirecting the cache root to a temp directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()


class TestRunScenarioIso(RunnerTestBase):
    """A scenario run solves and caches every simulation year once."""

    def test_three_years_create_three_cache_files(self):
        config = ScenarioConfig(iso="ERCOT")
        with patch.object(runner, "END_YEAR", 2028), patch.object(
            runner, "solve_dispatch", side_effect=_fake_solve
        ) as solve:
            key = runner.run_scenario_iso(config, "ERCOT")

        # One solve per simulated year, 2026-2028.
        self.assertEqual(solve.call_count, 3)
        for year in (2026, 2027, 2028):
            self.assertTrue(cache.is_cached("ERCOT", key, year))

        parquets = sorted(
            (cache.CACHE_ROOT / "ERCOT" / key).glob("year_*.parquet")
        )
        self.assertEqual(len(parquets), 3)

    def test_rerun_skips_all_cached_years(self):
        config = ScenarioConfig(iso="ERCOT")
        with patch.object(runner, "END_YEAR", 2028), patch.object(
            runner, "solve_dispatch", side_effect=_fake_solve
        ) as solve:
            runner.run_scenario_iso(config, "ERCOT")
            self.assertEqual(solve.call_count, 3)

            # Re-running the identical scenario solves nothing new: every
            # year is loaded from the cache instead.
            runner.run_scenario_iso(config, "ERCOT")
            self.assertEqual(solve.call_count, 3)

    def test_iso_argument_overrides_config_iso(self):
        config = ScenarioConfig(iso="CAISO")
        with patch.object(runner, "END_YEAR", 2026), patch.object(
            runner, "solve_dispatch", side_effect=_fake_solve
        ):
            key = runner.run_scenario_iso(config, "ERCOT")

        # The run is cached under the requested ISO, not the config's.
        self.assertTrue(cache.is_cached("ERCOT", key, 2026))
        self.assertTrue((cache.CACHE_ROOT / "ERCOT" / key).is_dir())
        self.assertFalse((cache.CACHE_ROOT / "CAISO").exists())


class TestRunSweep(RunnerTestBase):
    """A sweep runs every expanded config and caches each independently."""

    def test_two_configs_create_two_cache_dirs(self):
        sweep = SweepDefinition(sweep={"carbon_price": [0.0, 50.0]})
        with patch.object(runner, "END_YEAR", 2027), patch.object(
            runner, "solve_dispatch", side_effect=_fake_solve
        ):
            keys = runner.run_sweep(sweep, workers=1)

        self.assertEqual(len(keys), 2)
        self.assertEqual(len(set(keys)), 2)

        cache_dirs = [
            d for d in (cache.CACHE_ROOT / "ERCOT").iterdir() if d.is_dir()
        ]
        self.assertEqual(len(cache_dirs), 2)
        self.assertEqual({d.name for d in cache_dirs}, set(keys))


class TestMainCLI(RunnerTestBase):
    """The ``run`` subcommand parses its arguments correctly."""

    def _write_config(self, **overrides) -> Path:
        config = ScenarioConfig(**overrides)
        path = Path(self._tmp.name) / "scenario.yaml"
        config.to_yaml(path)
        return path

    def test_run_subcommand_parses_config_and_iso(self):
        cfg_path = self._write_config(iso="CAISO", carbon_price=12.0)
        with patch.object(runner, "run_scenario_iso") as run:
            runner.main(["run", "--config", str(cfg_path), "--iso", "ERCOT"])

        run.assert_called_once()
        called_config, called_iso = run.call_args[0]
        self.assertEqual(called_iso, "ERCOT")
        self.assertEqual(called_config.carbon_price, 12.0)
        self.assertEqual(called_config.iso, "CAISO")

    def test_run_subcommand_defaults_iso_to_config(self):
        cfg_path = self._write_config(iso="CAISO")
        with patch.object(runner, "run_scenario_iso") as run:
            runner.main(["run", "--config", str(cfg_path)])

        _, called_iso = run.call_args[0]
        self.assertEqual(called_iso, "CAISO")


class TestDemandGrowth(unittest.TestCase):
    """Piecewise demand growth: near-term vs long-term rates by era."""

    def test_near_term_year_uses_near_rate(self):
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        self.assertAlmostEqual(runner._get_growth_rate(config, 2028), 0.05)

    def test_long_term_year_uses_long_rate(self):
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        self.assertAlmostEqual(runner._get_growth_rate(config, 2035), 0.025)

    def test_transition_boundary(self):
        # 2030 is the last near-term year; 2031 is the first long-term year.
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        self.assertAlmostEqual(runner._get_growth_rate(config, 2030), 0.05)
        self.assertAlmostEqual(runner._get_growth_rate(config, 2031), 0.025)

    def test_flat_override_when_no_structured_path(self):
        # An ISO/path with no structured rates falls back to the scalar.
        config = ScenarioConfig(
            iso="ERCOT", demand_growth_path="nonexistent",
            demand_growth_rate=0.07,
        )
        self.assertAlmostEqual(runner._get_growth_rate(config, 2028), 0.07)
        self.assertAlmostEqual(runner._get_growth_rate(config, 2040), 0.07)

    def test_scale_demand_compounds_year_by_year(self):
        config = ScenarioConfig(iso="ERCOT", demand_growth_path="mid")
        base = np.full((1, 8), 100.0)
        # 2026 is the base year: no growth applied.
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2026), base
        )
        # 2028: two years of the near rate (0.05).
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2028), base * 1.05 ** 2
        )
        # 2032: growth applied for 2026-2031 — five near years
        # (2026-2030) then one long year (2031).
        expected = base * 1.05 ** 5 * 1.025 ** 1
        np.testing.assert_allclose(
            runner._scale_demand(base, config, 2032), expected
        )


if __name__ == "__main__":
    unittest.main()
