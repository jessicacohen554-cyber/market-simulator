"""Tests for the weather-year forecast ensemble runner and reporting."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import (
    END_YEAR,
    START_YEAR,
    WEATHER_YEAR_POOL,
    weather_year_pool,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.ensemble import (
    _aggregate_year,
    _distribution,
    export_ensemble_json,
    summarize_ensemble,
    weather_ensemble_configs,
)
from market_sim.model.dispatch import DispatchResult
from market_sim.results import cache
from market_sim.results.outputs import FleetContext


def _make_result(seed, *, price_scale=80.0, dispatch_scale=100.0):
    """Build a small deterministic ``DispatchResult`` for one member-year."""
    rng = np.random.default_rng(seed)
    T, n_gen, n_zones = 24, 3, 2
    return DispatchResult(
        dispatch=rng.random((n_gen, T)) * dispatch_scale,
        wind_dispatched=rng.random((n_zones, T)) * 50.0,
        solar_dispatched=rng.random((n_zones, T)) * 40.0,
        slack=np.zeros((n_zones, T)),
        dump=np.zeros((n_zones, T)),
        prices=rng.random((n_zones, T)) * price_scale,
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=1.0,
        status="Optimal",
        build_time=0.1,
        solve_time=0.1,
        emissions=None,
    )


def _make_context():
    """Build a small ``FleetContext`` aligned with ``_make_result``."""
    return FleetContext(
        fuel_types=["gas_cc", "gas_ct", "coal"],
        pmax_mw=[400.0, 150.0, 600.0],
        emission_rate=[0.38, 0.6, 1.0],
        efficiency_bins=["h_class", "aero", "older"],
        heat_rates=[6.4, 9.8, 10.2],
        zones=["North", "South", "North"],
        unit_ids=["G0", "G1", "G2"],
        wind_cap_mw=10000.0,
        solar_cap_mw=8000.0,
        wind_potential_mwh=1.0e7,
        solar_potential_mwh=5.0e6,
        storage_energy_cap_mwh=0.0,
    )


class TestEnsembleConfigs(unittest.TestCase):
    """Config expansion: one config per distinct, forecast-only weather draw."""

    def test_default_pool_used_when_unspecified(self):
        # ScenarioConfig() defaults to ERCOT, whose verified pool is wider
        # than the cross-ISO WEATHER_YEAR_POOL fallback (2026-07 widening).
        configs = weather_ensemble_configs(ScenarioConfig())
        self.assertEqual(tuple(configs), weather_year_pool("ERCOT"))
        self.assertGreater(len(configs), len(WEATHER_YEAR_POOL))
        for wy, config in configs.items():
            self.assertEqual(config.weather_year, wy)

    def test_default_pool_is_per_iso(self):
        # CAISO has no verified pre-2023 EIA-930 hourly coverage (see
        # docs/weather-pool-coverage-2026-07.md), so it stays on the common
        # fallback pool while ERCOT/NEISO get the widened one.
        caiso = weather_ensemble_configs(ScenarioConfig(iso="CAISO"))
        self.assertEqual(tuple(caiso), WEATHER_YEAR_POOL)
        neiso = weather_ensemble_configs(ScenarioConfig(iso="NEISO"))
        self.assertEqual(tuple(neiso), weather_year_pool("NEISO"))
        self.assertIn(2019, neiso)

    def test_only_weather_year_varies(self):
        base = ScenarioConfig(iso="CAISO", carbon_price=40.0)
        configs = weather_ensemble_configs(base, [2024, 2023])
        # Sorted ascending regardless of input order.
        self.assertEqual(list(configs), [2023, 2024])
        for config in configs.values():
            self.assertEqual(config.iso, "CAISO")
            self.assertEqual(config.carbon_price, 40.0)
        # Distinct cache keys, one per draw.
        keys = {c.cache_key() for c in configs.values()}
        self.assertEqual(len(keys), 2)

    def test_backcast_mode_rejected(self):
        with self.assertRaises(ValueError):
            weather_ensemble_configs(ScenarioConfig(mode="backcast"))

    def test_empty_and_duplicate_years_rejected(self):
        with self.assertRaises(ValueError):
            weather_ensemble_configs(ScenarioConfig(), [])
        with self.assertRaises(ValueError):
            weather_ensemble_configs(ScenarioConfig(), [2024, 2024])


class TestDistribution(unittest.TestCase):
    """The distribution helper reports the expected order statistics."""

    def test_basic_statistics(self):
        dist = _distribution([10.0, 20.0, 30.0])
        self.assertEqual(dist["mean"], 20.0)
        self.assertEqual(dist["min"], 10.0)
        self.assertEqual(dist["max"], 30.0)
        self.assertEqual(dist["p50"], 20.0)
        self.assertAlmostEqual(dist["std"], float(np.std([10, 20, 30])), places=4)

    def test_single_member_collapses_to_point(self):
        dist = _distribution([42.0])
        for key in ("mean", "min", "max", "p10", "p50", "p90"):
            self.assertEqual(dist[key], 42.0)
        self.assertEqual(dist["std"], 0.0)


class TestAggregateYear(unittest.TestCase):
    """Cross-member aggregation covers scalars, fuels and raw members."""

    def test_fuel_union_with_zero_fill(self):
        members = {
            2023: {
                "avg_price": 30.0,
                "generation_twh": {"gas_cc": 100.0, "wind": 20.0},
            },
            2024: {
                "avg_price": 50.0,
                "generation_twh": {"gas_cc": 80.0, "solar": 10.0},
            },
        }
        agg = _aggregate_year(members)
        self.assertEqual(agg["avg_price"]["mean"], 40.0)
        # Fuel union across members; a fuel absent in a member counts as zero.
        self.assertEqual(set(agg["generation_twh"]), {"gas_cc", "solar", "wind"})
        self.assertEqual(agg["generation_twh"]["wind"]["min"], 0.0)
        self.assertEqual(agg["generation_twh"]["wind"]["max"], 20.0)
        self.assertEqual(agg["generation_twh"]["solar"]["max"], 10.0)
        self.assertEqual(set(agg["by_member"]), {"2023", "2024"})


class _CacheBacked(unittest.TestCase):
    """Fixture redirecting the cache root and seeding member runs on disk."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._original_root = cache.CACHE_ROOT
        cache.CACHE_ROOT = Path(self._tmp.name)
        self.iso = "ERCOT"
        # Two members differing only by weather year; seed every forecast year.
        self.members: dict[int, str] = {}
        for offset, wy in enumerate((2023, 2024)):
            config = ScenarioConfig(iso=self.iso, weather_year=wy)
            for year in range(START_YEAR, END_YEAR + 1):
                cache.save_result(
                    _make_result(
                        seed=offset * 1000 + year, price_scale=50.0 + offset * 40.0
                    ),
                    config,
                    iso=self.iso,
                    year=year,
                    context=_make_context(),
                )
            self.members[wy] = config.cache_key()

    def tearDown(self):
        cache.CACHE_ROOT = self._original_root
        self._tmp.cleanup()


class TestSummarizeEnsemble(_CacheBacked):
    """``summarize_ensemble`` loads cached members into a distribution payload."""

    def test_payload_shape_and_member_keys(self):
        payload = summarize_ensemble(self.members, self.iso)
        self.assertEqual(payload["iso"], "ERCOT")
        self.assertEqual(payload["weather_years"], [2023, 2024])
        self.assertEqual(set(payload["members"]), {"2023", "2024"})
        # The shared base config is reported without the per-draw weather year.
        self.assertNotIn("weather_year", payload["base_config"])
        # Every forecast year present with a distribution per scalar metric.
        self.assertEqual(
            set(payload["distribution"]),
            {str(y) for y in range(START_YEAR, END_YEAR + 1)},
        )
        year0 = payload["distribution"][str(START_YEAR)]
        self.assertIn("avg_price", year0)
        self.assertIn("mean", year0["avg_price"])
        self.assertEqual(set(year0["by_member"]), {"2023", "2024"})

    def test_member_2024_prices_higher_than_2023(self):
        # member 2024 was seeded with a wider price scale, so its draw sits
        # at the top of the avg_price distribution.
        payload = summarize_ensemble(self.members, self.iso)
        year0 = payload["distribution"][str(START_YEAR)]
        members = year0["by_member"]
        self.assertGreater(members["2024"]["avg_price"], members["2023"]["avg_price"])
        dist = year0["avg_price"]
        self.assertEqual(dist["min"], members["2023"]["avg_price"])
        self.assertEqual(dist["max"], members["2024"]["avg_price"])

    def test_export_writes_json(self):
        out = Path(self._tmp.name) / "out" / "ensemble.json"
        path = export_ensemble_json(self.members, self.iso, out)
        self.assertTrue(path.exists())
        payload = json.loads(path.read_text())
        self.assertEqual(payload["iso"], "ERCOT")
        self.assertEqual(payload["weather_years"], [2023, 2024])

    def test_missing_member_raises(self):
        with self.assertRaises(FileNotFoundError):
            summarize_ensemble({2025: "deadbeefdeadbeef"}, self.iso)


if __name__ == "__main__":
    unittest.main()
