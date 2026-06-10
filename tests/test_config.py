"""Tests for the scenario configuration system."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.results.export import real_to_nominal


class TestScenarioConfig(unittest.TestCase):
    """Tests for ScenarioConfig caching, serialization, and overrides."""

    def test_cache_key_deterministic(self):
        config = ScenarioConfig()
        self.assertEqual(config.cache_key(), config.cache_key())

    def test_cache_key_changes_with_parameter(self):
        base = ScenarioConfig()
        modified = base.with_overrides(carbon_price=50.0)
        self.assertNotEqual(base.cache_key(), modified.cache_key())

    def test_mode_defaults_to_forecast(self):
        self.assertEqual(ScenarioConfig().mode, "forecast")

    def test_mode_backcast_accepted(self):
        self.assertEqual(
            ScenarioConfig(mode="backcast").mode, "backcast"
        )

    def test_invalid_mode_rejected(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(mode="hindcast")

    def test_gas_override_does_not_imply_backcast(self):
        # A forecast sensitivity may pin gas without flipping the
        # renewables loader into historical-actuals mode (peer review C9).
        config = ScenarioConfig(gas_price_override=3.50)
        self.assertEqual(config.mode, "forecast")

    def test_yaml_round_trip(self):
        config = ScenarioConfig(carbon_price=42.0, iso="CAISO", hours=24)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.yaml"
            config.to_yaml(path)
            loaded = ScenarioConfig.from_yaml(path)
        self.assertEqual(config, loaded)

    def test_yaml_partial_overrides_keep_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.yaml"
            path.write_text("carbon_price: 99.0\n")
            loaded = ScenarioConfig.from_yaml(path)
        defaults = ScenarioConfig()
        self.assertEqual(loaded.carbon_price, 99.0)
        self.assertEqual(loaded.iso, defaults.iso)
        self.assertEqual(
            loaded.nominal_discount_rate, defaults.nominal_discount_rate
        )

    def test_to_yaml_only_writes_non_defaults(self):
        config = ScenarioConfig(carbon_price=33.0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scenario.yaml"
            config.to_yaml(path)
            text = path.read_text()
        self.assertIn("carbon_price", text)
        self.assertNotIn("nominal_discount_rate", text)
        self.assertNotIn("iso", text)

    def test_with_overrides_does_not_mutate_original(self):
        base = ScenarioConfig()
        original_price = base.carbon_price
        base.with_overrides(carbon_price=75.0)
        self.assertEqual(base.carbon_price, original_price)

    def test_real_discount_rate(self):
        config = ScenarioConfig()
        expected = (1.08 / 1.022) - 1.0  # ~0.0568
        assert abs(config.real_discount_rate - expected) < 1e-6

    def test_real_discount_rate_custom(self):
        config = ScenarioConfig(nominal_discount_rate=0.10)
        expected = (1.10 / 1.022) - 1.0
        assert abs(config.real_discount_rate - expected) < 1e-6


class TestRealToNominal(unittest.TestCase):
    """Tests for the real-to-nominal dollar conversion utility."""

    def test_real_to_nominal_base_year_passthrough(self):
        """Values in the base year should be unchanged."""
        values = np.array([50.0])
        years = np.array([2026])
        result = real_to_nominal(values, years)
        assert abs(result[0] - 50.0) < 1e-10

    def test_real_to_nominal_future_year(self):
        """2036 is 10 years out, deflator = 1.022^10."""
        values = np.array([50.0])
        years = np.array([2036])
        expected = 50.0 * (1.022 ** 10)
        result = real_to_nominal(values, years)
        assert abs(result[0] - expected) < 1e-6


class TestSweepDefinition(unittest.TestCase):
    """Tests for parameter sweep expansion."""

    def test_factorial_sweep_cartesian_product(self):
        sweep = SweepDefinition(
            sweep={
                "carbon_price": [0.0, 50.0],
                "gas_price_path": ["low", "mid", "high"],
            }
        )
        configs = sweep.generate()
        self.assertEqual(len(configs), 6)
        keys = {c.cache_key() for c in configs}
        self.assertEqual(len(keys), 6)

    def test_from_yaml_loads_sweep(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sweep.yaml"
            path.write_text(
                "mode: factorial\n"
                "sweep:\n"
                "  carbon_price: [0.0, 50.0]\n"
                "  gas_price_path: [low, mid, high]\n"
            )
            sweep = SweepDefinition.from_yaml(path)
        self.assertEqual(sweep.mode, "factorial")
        self.assertEqual(len(sweep.generate()), 6)


if __name__ == "__main__":
    unittest.main()
