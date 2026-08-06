"""Tests for results caching and Parquet round-tripping."""

import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import pyarrow as pa

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache, outputs
from market_sim.results.outputs import FleetContext


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
            test.assertTrue(np.allclose(exp, act), f"{field} arrays differ")
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

    def test_pass_label_keeps_p1_and_final_as_separate_files(self):
        # The P1 dataset and the final (primary) dataset coexist as
        # distinct files and load back independently.
        p1, final = _make_result(), _make_result()
        config = ScenarioConfig(iso="ERCOT")
        cache.save_result(p1, config, iso="ERCOT", year=2030, pass_label="p1")
        cache.save_result(final, config, iso="ERCOT", year=2030)

        key = config.cache_key()
        self.assertTrue(cache.is_cached("ERCOT", key, 2030))
        self.assertTrue(cache.is_cached("ERCOT", key, 2030, pass_label="p1"))
        self.assertNotEqual(
            cache.get_cache_path("ERCOT", key, 2030),
            cache.get_cache_path("ERCOT", key, 2030, pass_label="p1"),
        )
        _assert_results_match(
            self, p1, cache.load_result("ERCOT", key, 2030, pass_label="p1")
        )
        _assert_results_match(self, final, cache.load_result("ERCOT", key, 2030))


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


def _make_context(n_gen=5):
    """Build a ``FleetContext`` with deterministic per-generator attributes."""
    return FleetContext(
        fuel_types=["gas_cc", "gas_ct", "coal", "nuclear", "wind"][:n_gen],
        pmax_mw=[400.0, 150.0, 600.0, 1200.0, 300.0][:n_gen],
        emission_rate=[0.38, 0.6, 1.0, 0.0, 0.0][:n_gen],
        efficiency_bins=["h_class", "aero", "older", "default", "default"][:n_gen],
        heat_rates=[6.4, 9.8, 10.2, 10.4, 0.0][:n_gen],
        zones=["North", "South", "West", "Houston", "North"][:n_gen],
        unit_ids=["G0", "G1", "G2", "G3", "G4"][:n_gen],
        wind_cap_mw=40000.0,
        solar_cap_mw=25000.0,
        wind_potential_mwh=1.2e8,
        solar_potential_mwh=6.0e7,
        storage_energy_cap_mwh=32000.0,
    )


class TestFleetContext(CacheTestBase):
    """The fleet context survives the Parquet metadata round trip."""

    def test_context_round_trips(self):
        config = ScenarioConfig(iso="ERCOT")
        context = _make_context()
        cache.save_result(
            _make_result(), config, iso="ERCOT", year=2030, context=context
        )

        loaded = cache.load_fleet_context("ERCOT", config.cache_key(), 2030)
        self.assertEqual(loaded, context)

    def test_load_context_without_context_raises(self):
        config = ScenarioConfig(iso="ERCOT")
        cache.save_result(_make_result(), config, iso="ERCOT", year=2030)

        with self.assertRaises(ValueError):
            cache.load_fleet_context("ERCOT", config.cache_key(), 2030)

    def test_result_arrays_unaffected_by_context(self):
        config = ScenarioConfig(iso="ERCOT")
        result = _make_result()
        cache.save_result(
            result, config, iso="ERCOT", year=2030, context=_make_context()
        )

        loaded = cache.load_result("ERCOT", config.cache_key(), 2030)
        _assert_results_match(self, result, loaded)


class TestFleetContextFromArrays(unittest.TestCase):
    """``FleetContext.from_arrays`` derives the context from run inputs."""

    def test_maps_fuel_codes_and_sums_resources(self):
        generators = [
            Generator(
                unit_id="G0",
                name="G0",
                zone="North",
                fuel_type="coal",
                efficiency_bin="older",
                pmax_mw=600.0,
                heat_rate=10.2,
                emission_rate_co2=1.0,
            ),
            Generator(
                unit_id="G1",
                name="G1",
                zone="Houston",
                fuel_type="gas_cc",
                efficiency_bin="h_class",
                pmax_mw=400.0,
                heat_rate=6.4,
                emission_rate_co2=0.38,
            ),
        ]
        iso_config = get_iso_config("ERCOT")
        fleet = generators_to_fleet_arrays(generators, iso_config.zone_names, hours=4)

        context = FleetContext.from_arrays(
            fleet,
            iso_config,
            wind_cf=np.full((1, 4), 0.5),
            wind_cap=np.array([1000.0]),
            solar_cf=np.full((1, 4), 0.25),
            solar_cap=np.array([800.0]),
            storage_energy_cap=np.array([200.0, 300.0]),
        )

        self.assertEqual(context.fuel_types, ["coal", "gas_cc"])
        self.assertEqual(context.pmax_mw, [600.0, 400.0])
        self.assertEqual(context.emission_rate, [1.0, 0.38])
        self.assertEqual(context.efficiency_bins, ["older", "h_class"])
        self.assertEqual(context.heat_rates, [10.2, 6.4])
        self.assertEqual(context.zones, ["North", "Houston"])
        self.assertEqual(context.unit_ids, ["G0", "G1"])
        self.assertEqual(context.wind_cap_mw, 1000.0)
        # 0.5 capacity factor x 1000 MW x 4 hours.
        self.assertEqual(context.wind_potential_mwh, 2000.0)
        self.assertEqual(context.solar_potential_mwh, 800.0)
        self.assertEqual(context.storage_energy_cap_mwh, 500.0)


class TestMissingResult(CacheTestBase):
    """Loading a result that was never cached raises ``FileNotFoundError``."""

    def test_load_nonexistent_raises(self):
        with self.assertRaises(FileNotFoundError):
            cache.load_result("ERCOT", "deadbeefdeadbeef", 2099)

    def test_from_parquet_nonexistent_path_raises(self):
        missing = Path(self._tmp.name) / "nope.parquet"
        with self.assertRaises(FileNotFoundError):
            DispatchResult.from_parquet(missing)


def _legacy_list_column(array: np.ndarray) -> pa.Array:
    """The pre-optimization ``_list_column``: round-trips through Python.

    Used to write a Parquet file the old way so the new read path can be
    checked for backward compatibility.
    """
    by_hour = np.asarray(array, dtype=float).T
    return pa.array(by_hour.tolist(), type=pa.list_(pa.float64()))


class TestParquetSerialization(unittest.TestCase):
    """The zero-copy Parquet path round-trips and reads legacy files."""

    def test_round_trip_recovers_all_arrays(self):
        result = _make_result()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "result.parquet"
            result.to_parquet(path)
            loaded = DispatchResult.from_parquet(path)
        _assert_results_match(self, result, loaded)
        for field in ("dispatch", "prices", "storage_soc", "flows", "emissions"):
            exp, act = getattr(result, field), getattr(loaded, field)
            self.assertEqual(exp.shape, act.shape, f"{field} shape differs")
            self.assertTrue(np.allclose(exp, act), f"{field} values differ")

    def test_round_trips_per_zone_rps_vector_and_region_duals(self):
        # K-row compliance-region grain (FFR-7B Arm 2): the per-zone
        # rps_shadow_price vector and the per-region raw duals survive the
        # JSON metadata round trip as ndarrays; the legacy scalar stays a
        # scalar (every existing reader's type contract).
        result = _make_result()
        result.rps_shadow_price = np.array([0.0, 30.0])
        result.rps_region_duals = np.array([30.0, 0.0])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "krow.parquet"
            result.to_parquet(path)
            loaded = DispatchResult.from_parquet(path)
        self.assertIsInstance(loaded.rps_shadow_price, np.ndarray)
        np.testing.assert_array_equal(loaded.rps_shadow_price, [0.0, 30.0])
        np.testing.assert_array_equal(loaded.rps_region_duals, [30.0, 0.0])
        scalar = _make_result()
        scalar.rps_shadow_price = 12.5
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scalar.parquet"
            scalar.to_parquet(path)
            loaded = DispatchResult.from_parquet(path)
        self.assertEqual(loaded.rps_shadow_price, 12.5)
        self.assertIsNone(loaded.rps_region_duals)

    def test_reads_file_written_by_legacy_serializer(self):
        """A Parquet file written with the old ``.tolist()`` path still loads.

        The on-disk ``list<float64>`` schema is unchanged, so the new
        zero-copy read path must reconstruct legacy files identically.
        """
        result = _make_result()
        original = outputs._list_column
        outputs._list_column = _legacy_list_column
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "legacy.parquet"
                result.to_parquet(path)
                loaded = DispatchResult.from_parquet(path)
        finally:
            outputs._list_column = original
        _assert_results_match(self, result, loaded)


class TestParquetBenchmark(unittest.TestCase):
    """Micro-benchmark: a year-scale result must serialize quickly."""

    def test_to_and_from_parquet_under_two_seconds(self):
        # dispatch/emissions are sized per the task (200, 8760); zones,
        # storage and links use realistic ISO-scale widths.
        n_gen, n_zones, n_storage, n_links, T = 200, 8, 8, 12, 8760
        rng = np.random.default_rng(7)
        result = DispatchResult(
            dispatch=rng.random((n_gen, T)) * 100.0,
            wind_dispatched=rng.random((n_zones, T)) * 50.0,
            solar_dispatched=rng.random((n_zones, T)) * 40.0,
            slack=rng.random((n_zones, T)),
            dump=rng.random((n_zones, T)) * 0.01,
            prices=rng.random((n_zones, T)) * 80.0 - 10.0,
            storage_charge=rng.random((n_storage, T)),
            storage_discharge=rng.random((n_storage, T)),
            storage_soc=rng.random((n_storage, T)),
            flows=rng.random((n_links, T)) * 200.0 - 100.0,
            objective_value=1.0,
            status="Optimal",
            build_time=1.0,
            solve_time=1.0,
            emissions=rng.random((n_gen, T)) * 30.0,
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bench.parquet"

            start = time.perf_counter()
            result.to_parquet(path)
            write_s = time.perf_counter() - start

            start = time.perf_counter()
            loaded = DispatchResult.from_parquet(path)
            read_s = time.perf_counter() - start

        print(
            f"\n[benchmark] dispatch shape {result.dispatch.shape}: "
            f"to_parquet={write_s:.3f}s from_parquet={read_s:.3f}s"
        )
        self.assertTrue(np.allclose(result.dispatch, loaded.dispatch))
        self.assertLess(write_s, 2.0, f"to_parquet too slow: {write_s:.3f}s")
        self.assertLess(read_s, 2.0, f"from_parquet too slow: {read_s:.3f}s")


if __name__ == "__main__":
    unittest.main()
