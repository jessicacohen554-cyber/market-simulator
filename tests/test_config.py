"""Tests for the scenario configuration system."""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.config.constants import DEMAND_GROWTH_RATES, NEW_ENTRY_COSTS
from market_sim.config.scenarios import (
    ScenarioConfig,
    SweepDefinition,
    resolve_demand_growth_rate,
    resolve_new_entry_costs,
    resolve_policy_bundle,
)
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
        self.assertEqual(ScenarioConfig(mode="backcast").mode, "backcast")

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
        self.assertEqual(loaded.nominal_discount_rate, defaults.nominal_discount_rate)

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
        expected = 50.0 * (1.022**10)
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

    def test_cases_mode_one_config_per_named_case(self):
        matrix = SweepDefinition(
            cases={
                "REF": {},
                "GAS-LO": {"gas_price_path": "low"},
                "GAS-HI": {"gas_price_path": "high"},
            }
        )
        configs = matrix.case_configs()
        self.assertEqual(list(configs.keys()), ["REF", "GAS-LO", "GAS-HI"])
        self.assertEqual(configs["REF"].gas_price_path, "mid")
        self.assertEqual(configs["GAS-LO"].gas_price_path, "low")
        self.assertEqual(configs["GAS-HI"].gas_price_path, "high")

    def test_cases_mode_overrides_onto_base_config(self):
        base = ScenarioConfig(iso="CAISO", carbon_price=5.0)
        matrix = SweepDefinition(cases={"GAS-LO": {"gas_price_path": "low"}})
        configs = matrix.case_configs(base)
        # The case override applies, and every other base field is preserved.
        self.assertEqual(configs["GAS-LO"].gas_price_path, "low")
        self.assertEqual(configs["GAS-LO"].iso, "CAISO")
        self.assertEqual(configs["GAS-LO"].carbon_price, 5.0)

    def test_generate_dispatches_to_cases_mode(self):
        matrix = SweepDefinition(
            cases={"REF": {}, "GAS-HI": {"gas_price_path": "high"}}
        )
        configs = matrix.generate()
        self.assertEqual(len(configs), 2)
        self.assertEqual(configs[1].gas_price_path, "high")

    def test_case_configs_raises_when_not_cases_mode(self):
        sweep = SweepDefinition(sweep={"carbon_price": [0.0, 50.0]})
        with self.assertRaises(ValueError):
            sweep.case_configs()

    def test_sweep_and_cases_are_mutually_exclusive(self):
        with self.assertRaises(ValueError):
            SweepDefinition(
                sweep={"carbon_price": [0.0, 50.0]},
                cases={"REF": {}},
            )

    def test_from_yaml_loads_cases(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "matrix.yaml"
            path.write_text(
                "mode: cases\ncases:\n  REF: {}\n  GAS-LO:\n    gas_price_path: low\n"
            )
            matrix = SweepDefinition.from_yaml(path)
        self.assertEqual(list(matrix.cases.keys()), ["REF", "GAS-LO"])
        configs = matrix.case_configs()
        self.assertEqual(configs["GAS-LO"].gas_price_path, "low")


class TestScenarioMatrixYaml(unittest.TestCase):
    """The committed 13-case matrix (probability-bounds-plan-2026-07.md §1.2)."""

    _MATRIX_PATH = (
        Path(__file__).resolve().parents[1] / "configs" / "scenario_matrix.yaml"
    )

    def test_thirteen_named_cases_match_the_plan(self):
        matrix = SweepDefinition.from_yaml(self._MATRIX_PATH)
        expected_names = [
            "REF",
            "GAS-LO",
            "GAS-HI",
            "LOAD-LO",
            "LOAD-HI",
            "POL-TIGHT",
            "POL-ROLLBACK",
            "TECH-LO",
            "TECH-HI",
            "RET-FAST",
            "RET-SLOW",
            "CORNER-HI-EMIT",
            "CORNER-LO-EMIT",
        ]
        self.assertEqual(list(matrix.cases.keys()), expected_names)

    def test_ref_case_is_all_default(self):
        matrix = SweepDefinition.from_yaml(self._MATRIX_PATH)
        configs = matrix.case_configs()
        defaults = ScenarioConfig()
        ref = configs["REF"]
        self.assertEqual(ref.gas_price_path, defaults.gas_price_path)
        self.assertEqual(ref.demand_growth_path, defaults.demand_growth_path)
        self.assertEqual(ref.policy_bundle, defaults.policy_bundle)
        self.assertEqual(ref.tech_cost_path, defaults.tech_cost_path)
        self.assertEqual(
            ref.retirement_aggressiveness, defaults.retirement_aggressiveness
        )

    def test_corner_cases_move_every_axis_coherently(self):
        matrix = SweepDefinition.from_yaml(self._MATRIX_PATH)
        configs = matrix.case_configs()

        hi_emit = configs["CORNER-HI-EMIT"]
        self.assertEqual(hi_emit.gas_price_path, "low")
        self.assertEqual(hi_emit.demand_growth_path, "high")
        self.assertEqual(hi_emit.policy_bundle, "rollback")
        self.assertEqual(hi_emit.tech_cost_path, "high")
        self.assertEqual(hi_emit.retirement_aggressiveness, "slow")

        lo_emit = configs["CORNER-LO-EMIT"]
        self.assertEqual(lo_emit.gas_price_path, "high")
        self.assertEqual(lo_emit.demand_growth_path, "low")
        self.assertEqual(lo_emit.policy_bundle, "tight")
        self.assertEqual(lo_emit.tech_cost_path, "low")
        self.assertEqual(lo_emit.retirement_aggressiveness, "aggressive")

    def test_one_at_a_time_cases_move_exactly_one_axis_off_ref(self):
        matrix = SweepDefinition.from_yaml(self._MATRIX_PATH)
        one_at_a_time = [
            "GAS-LO",
            "GAS-HI",
            "LOAD-LO",
            "LOAD-HI",
            "POL-TIGHT",
            "POL-ROLLBACK",
            "TECH-LO",
            "TECH-HI",
            "RET-FAST",
            "RET-SLOW",
        ]
        for name in one_at_a_time:
            self.assertEqual(
                len(matrix.cases[name]),
                1,
                f"{name} should override exactly one axis, got {matrix.cases[name]}",
            )

    def test_all_case_configs_are_forecast_mode(self):
        matrix = SweepDefinition.from_yaml(self._MATRIX_PATH)
        for name, config in matrix.case_configs().items():
            self.assertEqual(config.mode, "forecast", name)


class TestProbabilityBoundsLevers(unittest.TestCase):
    """Tests for the PB-1 uncertainty-lever plumbing (fields + resolvers).

    docs/handoffs/probability-bounds-plan-2026-07.md §1.1/§2.1/§2.5 item 4.
    """

    # -- Neutral defaults reproduce today's resolved config exactly --------

    def test_new_entry_costs_neutral_default_matches_constants(self):
        """A keeper-shaped config's neutral tech-cost fields change nothing."""
        keeper_like = ScenarioConfig(
            iso="ERCOT", carbon_price=0.0, retirement_aggressiveness="mid"
        )
        self.assertEqual(resolve_new_entry_costs(keeper_like), NEW_ENTRY_COSTS)

    def test_policy_bundle_current_is_identity(self):
        keeper_like = ScenarioConfig(iso="PJM", carbon_price_path="zero")
        self.assertIs(resolve_policy_bundle(keeper_like), keeper_like)

    def test_demand_growth_neutral_percentile_matches_path_lookup(self):
        for iso in DEMAND_GROWTH_RATES:
            for path in ("low", "mid", "high"):
                config = ScenarioConfig(iso=iso, demand_growth_path=path)
                for year, era in ((2027, "near"), (2040, "long")):
                    self.assertAlmostEqual(
                        resolve_demand_growth_rate(config, year),
                        DEMAND_GROWTH_RATES[iso][path][era],
                    )

    def test_demand_growth_falls_back_for_iso_without_table(self):
        config = ScenarioConfig(iso="MISO", demand_growth_rate=0.02)
        self.assertEqual(resolve_demand_growth_rate(config, 2030), 0.02)

    # -- Each lever moves the intended quantity monotonically --------------

    def test_tech_cost_percentile_monotonic_on_capex(self):
        capex = [
            resolve_new_entry_costs(ScenarioConfig(tech_cost_percentile=p))["solar"][
                "capex_per_kw"
            ]
            for p in (0.0, 0.25, 0.5, 0.75, 1.0)
        ]
        self.assertEqual(capex, sorted(capex))
        self.assertLess(capex[0], capex[2])
        self.assertLess(capex[2], capex[-1])

    def test_tech_cost_percentile_monotonic_on_learning_rate(self):
        # Cheaper-future (low) cases carry a steeper learning rate than the
        # costlier-future (high) cases -- the multiplier direction flips.
        learning = [
            resolve_new_entry_costs(ScenarioConfig(tech_cost_percentile=p))["wind"][
                "learning_rate"
            ]
            for p in (0.0, 0.5, 1.0)
        ]
        self.assertGreater(learning[0], learning[1])
        self.assertGreater(learning[1], learning[2])

    def test_demand_growth_percentile_monotonic(self):
        rates = [
            resolve_demand_growth_rate(
                ScenarioConfig(iso="ERCOT", demand_growth_percentile=p), 2027
            )
            for p in (0.0, 0.25, 0.5, 0.75, 1.0)
        ]
        self.assertEqual(rates, sorted(rates))

    def test_tech_cost_path_and_percentile_precedence(self):
        # percentile at its neutral default defers to the discrete path.
        via_path = resolve_new_entry_costs(ScenarioConfig(tech_cost_path="high"))
        via_percentile = resolve_new_entry_costs(
            ScenarioConfig(tech_cost_percentile=1.0)
        )
        self.assertEqual(via_path, via_percentile)

    # -- Policy bundle resolution -------------------------------------------

    def test_policy_bundle_tight_extends_ira_and_sets_carbon_path(self):
        config = ScenarioConfig(policy_bundle="tight")
        resolved = resolve_policy_bundle(config)
        self.assertEqual(resolved.carbon_price_path, "mid")
        self.assertEqual(
            resolved.ira_wind_solar_last_year, config.ira_wind_solar_last_year + 5
        )
        self.assertEqual(
            resolved.ira_ccus_45q_last_year, config.ira_ccus_45q_last_year + 5
        )

    def test_policy_bundle_rollback_pulls_ira_sunset_earlier(self):
        config = ScenarioConfig(policy_bundle="rollback")
        resolved = resolve_policy_bundle(config)
        self.assertEqual(resolved.carbon_price_path, "zero")
        self.assertFalse(resolved.state_carbon_pricing)
        self.assertEqual(
            resolved.ira_wind_solar_last_year, config.ira_wind_solar_last_year - 2
        )

    def test_policy_bundle_invalid_raises(self):
        config = ScenarioConfig(policy_bundle="not_a_bundle")
        with self.assertRaises(ValueError):
            resolve_policy_bundle(config)

    # -- Backcast guard (rule 13) --------------------------------------------

    def test_gas_price_factor_neutral_in_backcast(self):
        config = ScenarioConfig(mode="backcast", gas_price_factor=1.0)
        self.assertEqual(config.gas_price_factor, 1.0)

    def test_gas_price_factor_nonneutral_in_backcast_raises(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(mode="backcast", gas_price_factor=1.1)

    def test_gas_price_factor_nonneutral_allowed_in_forecast(self):
        config = ScenarioConfig(mode="forecast", gas_price_factor=1.2)
        self.assertEqual(config.gas_price_factor, 1.2)


if __name__ == "__main__":
    unittest.main()
