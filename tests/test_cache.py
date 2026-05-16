"""Tests for results caching and Parquet round-tripping."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache


def _make_result(*, with_storage=True, with_flows=True, with_emissions=True):
    """Build a ``DispatchResult`` with deterministic pseudo-random arrays."""
    rng = np.random.default_rng(42)
    T = 48  # hours
    n_gen, n_zones, n_storage, n_links = 5, 3, 2, 4

    storage_kwargs = {
        "storage_charge": rng.random((n_storage, T)),
        "storage_discharge": rng.random((n_storage, T)),
        "storage_soc": rng.random((n_storage, T)),
    }
    return DispatchResult(
        dispatch=rng.random((n_gen, T)) * 100.0,
        wind_dispatched=rng.random((n_zones, T)) * 50.0,
        solar_dispatched=rng.random((n_zones, T)) * 40.0,
        slack=rng.random((n_zones, T)),
        dump=rng.random((n_zones, T)) * 0.01,  # small overgeneration
        prices=rng.random((n_zones, T)) * 80.0 - 10.0,
        storage_charge=storage_kwargs["storage_charge"] if with_storage else None,
        storage_discharge=(
            storage_kwargs["storage_discharge"] if with_storage else None
        ),
        storage_soc=storage_kwargs["storage_soc"] if with_storage else None,
        flows=rng.random((n_links, T)) * 200.0 - 100.0 if with_flows else None,
        objective_value=123456.789,
        status="Optimal",
        build_time=1.25,
        solve_time=3.75,
        emissions=rng.random((n_gen, T)) * 30.0 if with_emissions else None,
    )


def _assert_results_match(test, expected, actual):
    """Assert two ``DispatchResult`` objects hold equal arrays and scalars."""
    for field in (
        "dispatch",
        "wind_dispatched",
        "solar_dispatched",
        "slack",
        "dump",
        "prices",
        "storage_charge",
        "storage_discharge",
        "storage_soc",
        "flows",
        "emissions",
    ):
        exp = getattr(expected, field)
        act = getattr(actual, field)
        if exp is None:
            test.assertIsNone(act, f"{field} should be None")
        else:
            test.assertIsNotNone(act, f"{field} should not be None")
            test.assertTrue(
                np.allclose(exp, act), f"{field} arrays differ"
            )
    test.assertAlmostEqual(expected.objective_value, actual.objective_value)
    test.assertEqual(expected.status, actual.status)
    test.assertAlmostEqual(expected.build_time, actual.build_time)
    test.assertAlmostEqual(expected.solve_time, actual.solve_time)


class CacheTestBase(unittest.TestCase):
    """Base fixture redirecting the cache root to a temp directory."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()


class TestRoundTrip(CacheTestBase):
    """Save a result, load it back, and confirm every array survives."""

    def test_save_then_load_recovers_all_arrays(self):
        result = _make_result()
        config = ScenarioConfig(iso="ERCOT")
        cache.save_result(result, config, iso="ERCOT", year=2030)

        loaded = cache.load_result("ERCOT", config.cache_key(), 2030)
        _assert_results_match(self, result, loaded)

    def test_round_trip_without_storage_flows_or_emissions(self):
        result = _make_result(
            with_storage=False, with_flows=False, with_emissions=False
        )
        config = ScenarioConfig(carbon_price=25.0)
        cache.save_result(result, config, iso="CAISO", year=2031)

        loaded = cache.load_result("CAISO", config.cache_key(), 2031)
        _assert_results_match(self, result, loaded)


class TestIsCached(CacheTestBase):
    """``is_cached`` tracks the presence of the Parquet file."""

    def test_false_before_save_true_after(self):
        config = ScenarioConfig()
        key = config.cache_key()
        self.assertFalse(cache.is_cached("ERCOT", key, 2030))

        cache.save_result(_make_result(), config, iso="ERCOT", year=2030)
        self.assertTrue(cache.is_cached("ERCOT", key, 2030))

    def test_distinct_years_cache_independently(self):
        config = ScenarioConfig()
        key = config.cache_key()
        cache.save_result(_make_result(), config, iso="ERCOT", year=2030)

        self.assertTrue(cache.is_cached("ERCOT", key, 2030))
        self.assertFalse(cache.is_cached("ERCOT", key, 2031))


class TestConfigSidecar(CacheTestBase):
    """``save_result`` writes a ``config.yaml`` beside the Parquet file."""

    def test_config_yaml_present_alongside_parquet(self):
        config = ScenarioConfig(iso="ERCOT", carbon_price=40.0)
        cache.save_result(config=config, result=_make_result(), iso="ERCOT", year=2030)

        parquet = cache.get_cache_path("ERCOT", config.cache_key(), 2030)
        config_yaml = cache.get_config_path("ERCOT", config.cache_key(), 2030)
        self.assertTrue(parquet.exists())
        self.assertTrue(config_yaml.exists())
        self.assertEqual(config_yaml.parent, parquet.parent)

        reloaded = ScenarioConfig.from_yaml(config_yaml)
        self.assertEqual(reloaded.cache_key(), config.cache_key())


class TestMissingResult(CacheTestBase):
    """Loading a result that was never cached raises ``FileNotFoundError``."""

    def test_load_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            cache.load_result("ERCOT", "deadbeefdeadbeef", 2099)

    def test_from_parquet_nonexistent_path_raises(self):
        missing = Path(self._tmp.name) / "nope.parquet"
        with self.assertRaises(FileNotFoundError):
            DispatchResult.from_parquet(missing)


if __name__ == "__main__":
    unittest.main()
