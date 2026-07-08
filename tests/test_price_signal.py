"""Tests for the capacity-screen price signal (EWMA + lookahead re-price).

Capacity-economics plan 2026-07 §2.2 (EWMA anti-whipsaw blend) and §2.3.2
(growth-scaled lookahead via stack re-price), acceptance list §8 item 2.
Trivial-first per CLAUDE.md: 3-unit stacks, hand-computed hourly prices.
"""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import evolve_fleet
from market_sim.results.scarcity import scarcity_prices
from market_sim.runner import _blend_price_signal, _lookahead_reprice_signal


class TestBlendPriceSignal(unittest.TestCase):
    """EWMA blend: byte-identical at alpha=1.0, exact arithmetic below it."""

    def test_alpha_one_returns_same_object(self):
        econ = np.full((2, 4), 30.0)
        prev = np.full((2, 4), 99.0)
        out = _blend_price_signal(econ, prev, 1.0)
        self.assertIs(out, econ)  # byte-identical: the SAME array object

    def test_no_prior_signal_returns_same_object(self):
        econ = np.full((2, 4), 30.0)
        self.assertIs(_blend_price_signal(econ, None, 0.6), econ)

    def test_ewma_arithmetic(self):
        econ = np.array([[40.0, 60.0]])
        prev = np.array([[20.0, 20.0]])
        out = _blend_price_signal(econ, prev, 0.6)
        np.testing.assert_allclose(out, [[0.6 * 40 + 0.4 * 20, 0.6 * 60 + 0.4 * 20]])


class TestLookaheadReprice(unittest.TestCase):
    """Stack re-price of next year's known net load (plan §2.3.2)."""

    def _fixture(self):
        # 3-unit stack: mc [10, 20, 50] $/MWh, 5000 MW each, full
        # availability -> cumulative capacity [5000, 10000, 15000] MW
        # (GW-scale so the ORDC's MW parameters read sensibly).
        T = 4
        fleet_arrays = SimpleNamespace(
            pmax=np.array([5000.0, 5000.0, 5000.0]),
            availability=np.ones((3, T)),
        )
        mc_cost = np.tile(np.array([[10.0], [20.0], [50.0]]), (1, T))
        result = SimpleNamespace(
            wind_dispatched=np.zeros((1, T)),
            solar_dispatched=np.zeros((1, T)),
        )
        # next_year == weather_year (2024) -> growth factor exactly 1, so the
        # hand-computed net load is the demand itself.
        base_demand = np.array([[2000.0, 7000.0, 12000.0, 20000.0]])
        return fleet_arrays, mc_cost, result, base_demand

    def test_three_unit_stack_hand_computed(self):
        fleet_arrays, mc_cost, result, base_demand = self._fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        self.assertFalse(config.scarcity_price_overlay)  # no tail here
        signal = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=2
        )
        self.assertEqual(signal.shape, (2, 4))
        # Hour loads 2/7/12 GW clear units 1/2/3; the 20 GW hour exhausts
        # the stack and (scarcity off) prices at the top of the stack.
        np.testing.assert_allclose(signal[0], [10.0, 20.0, 50.0, 50.0])
        np.testing.assert_allclose(signal[1], signal[0])  # system-wide

    def test_prior_year_vre_output_nets_the_load(self):
        fleet_arrays, mc_cost, result, base_demand = self._fixture()
        # 5 GW of prior-year wind output shifts every hour down one unit.
        result.wind_dispatched = np.full((1, 4), 5000.0)
        config = ScenarioConfig(iso="ERCOT", mode="forecast")
        signal = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        # net load [-3000, 2000, 7000, 15000]: negative clips to 0 -> the
        # cheapest unit prices it.
        np.testing.assert_allclose(signal[0], [10.0, 10.0, 20.0, 50.0])

    def test_demand_next_total_override_bypasses_scale_demand(self):
        # Hindcast path (G-30): the caller supplies the realized next-year total
        # demand directly, so the growth-scaled weather-year base is ignored.
        fleet_arrays, mc_cost, result, base_demand = self._fixture()
        config = ScenarioConfig(iso="ERCOT", mode="forecast", hindcast=True)
        self.assertFalse(config.scarcity_price_overlay)  # no tail here
        realized_next = np.array([2000.0, 7000.0, 12000.0, 20000.0])
        signal = _lookahead_reprice_signal(
            config,
            2024,
            base_demand * 999.0,  # deliberately wrong base: must be unused
            fleet_arrays,
            mc_cost,
            result,
            n_zones=1,
            demand_next_total=realized_next,
        )
        # Identical hand-computed result to the _scale_demand fixture, proving
        # the override load — not base_demand — set the net load.
        np.testing.assert_allclose(signal[0], [10.0, 20.0, 50.0, 50.0])

    def test_scarcity_tail_applies_ordc_curve(self):
        fleet_arrays, mc_cost, result, base_demand = self._fixture()
        config = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            scarcity_pricing_enabled=True,
            scarcity_price_overlay=True,
        )
        signal = _lookahead_reprice_signal(
            config, 2024, base_demand, fleet_arrays, mc_cost, result, n_zones=1
        )
        # Same curve the runner's capacity-economics overlay uses: reserves =
        # stack top (15000) - net load, lambda = the stack price.
        stack_prices = np.array([10.0, 20.0, 50.0, 50.0])
        reserves = 15000.0 - base_demand[0]
        expected_adder = scarcity_prices(config, 2024, reserves, stack_prices)[
            "scarcity_adder"
        ]
        np.testing.assert_allclose(signal[0], stack_prices + expected_adder)
        # The exhausted hour (reserves -5000) prices near VOLL; the 13 GW-
        # reserve first hour carries no material adder.
        self.assertGreater(signal[0, 3], 50.0)
        self.assertLess(signal[0, 0] - 10.0, 1.0)


class TestScreensConsumeSignal(unittest.TestCase):
    """The screens read price_signal in place of raw prices (screens-only)."""

    T = 10

    def test_evolve_fleet_prefers_price_signal(self):
        # Raw prices say "deeply unprofitable"; the signal says "rich". The
        # retirement screen must follow the signal (plan §2.2: consumed by
        # the screens in place of raw prices).
        config = ScenarioConfig(iso="ERCOT")
        coal = [
            Generator(
                unit_id="C0",
                name="C0",
                zone="Z0",
                fuel_type="coal",
                pmax_mw=100.0,
                heat_rate=10.0,
            )
        ]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        prior = {
            "fleet_arrays": arrays,
            "dispatch_result": SimpleNamespace(dispatch=np.full((1, self.T), 100.0)),
            "prices": np.full((1, self.T), 10.0),
            "price_signal": np.full((1, self.T), 1.0e6),
            "peak_demand": 0.0,
            "mc_cost": np.zeros((1, self.T)),
        }
        fleet, tracker, _, _, _ = evolve_fleet(coal, prior, 2030, config, {})
        # Rich signal -> profitable year -> counter resets, the coal stays
        # (the rich signal also pulls in economic new entry; assert on the
        # coal fuel class, not fleet size).
        self.assertEqual(sum(g.pmax_mw for g in fleet if g.fuel_type == "coal"), 100.0)
        # Without the signal the same raw prices retire coal in one year.
        prior_no_signal = dict(prior)
        prior_no_signal.pop("price_signal")
        fleet, tracker, _, _, _ = evolve_fleet(coal, prior_no_signal, 2030, config, {})
        self.assertEqual(sum(g.pmax_mw for g in fleet if g.fuel_type == "coal"), 0.0)


if __name__ == "__main__":
    unittest.main()
