"""Tests for fleet retirement mechanisms in ``market_sim.model.capacity``."""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    apply_economic_retirements,
    apply_known_retirements,
    apply_sigmoid_retirement,
    compute_clean_share,
)


def _gen(unit_id, fuel_type, pmax=100.0, heat_rate=10.0, zone="Z0",
         retirement_year=None):
    """Build a Generator with the attributes the retirement logic reads."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone=zone,
        fuel_type=fuel_type,
        pmax_mw=pmax,
        heat_rate=heat_rate,
        retirement_year=retirement_year,
    )


class TestKnownRetirements(unittest.TestCase):
    """Scheduled-retirement removal by simulation year."""

    def test_unit_present_before_retirement_year(self):
        fleet = [_gen("C0", "coal", retirement_year=2028)]
        survivors = apply_known_retirements(fleet, 2027)
        self.assertEqual([g.unit_id for g in survivors], ["C0"])

    def test_unit_removed_at_retirement_year(self):
        fleet = [_gen("C0", "coal", retirement_year=2028)]
        survivors = apply_known_retirements(fleet, 2028)
        self.assertEqual(survivors, [])

    def test_unit_removed_after_retirement_year(self):
        fleet = [_gen("C0", "coal", retirement_year=2028)]
        survivors = apply_known_retirements(fleet, 2030)
        self.assertEqual(survivors, [])

    def test_unit_without_schedule_is_kept(self):
        fleet = [_gen("G0", "gas_cc", retirement_year=None)]
        survivors = apply_known_retirements(fleet, 2050)
        self.assertEqual([g.unit_id for g in survivors], ["G0"])


class TestEconomicRetirements(unittest.TestCase):
    """Revenue-driven retirement of persistently unprofitable thermal units."""

    T = 10

    def _dispatch_result(self, n_gen, level):
        """A dispatch stand-in with every generator producing ``level`` MW."""
        return SimpleNamespace(dispatch=np.full((n_gen, self.T), level))

    def test_unprofitable_unit_retires_after_two_loss_years(self):
        config = ScenarioConfig()  # retirement_consecutive_years = 2
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # going_forward_cost = 40 $/kW-yr * 100 MW * 1000 = 4_000_000.
        # net_revenue = 10 $/MWh * 10 MW * 10 h = 1_000 << cost.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 10.0)

        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}
        )
        # First loss year: counter at 1, below the threshold -- still online.
        self.assertEqual([g.unit_id for g in fleet1], ["C0"])
        self.assertEqual(losses1["C0"], 1)

        fleet2, losses2 = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1
        )
        # Second consecutive loss year: counter hits 2 -- retired.
        self.assertEqual(fleet2, [])
        self.assertNotIn("C0", losses2)

    def test_profitable_unit_resets_counter(self):
        config = ScenarioConfig()
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # net_revenue = 1e6 * 10 * 10 = 1e8, far above the 4e6 fixed cost.
        prices = np.full((1, self.T), 1.0e6)
        dispatch = self._dispatch_result(1, 10.0)

        # Enter with one prior loss year on the books.
        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {"C0": 1}
        )
        self.assertEqual([g.unit_id for g in fleet1], ["C0"])
        self.assertEqual(losses1["C0"], 0)

    def test_non_thermal_units_are_never_economically_retired(self):
        config = ScenarioConfig()
        fleet = [_gen("W0", "wind", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.zeros((1, self.T))
        dispatch = self._dispatch_result(1, 0.0)

        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}
        )
        self.assertEqual([g.unit_id for g in fleet1], ["W0"])
        self.assertEqual(losses1, {})


class TestSigmoidRetirement(unittest.TestCase):
    """Clean-share-driven logistic attrition of the fossil fleet."""

    def _coal_fleet(self, n=10):
        """``n`` coal units, each 100 MW, with strictly increasing heat rate."""
        return [
            _gen(f"C{i}", "coal", pmax=100.0, heat_rate=8.0 + 0.1 * i)
            for i in range(n)
        ]

    def test_high_clean_share_retires_substantial_coal(self):
        # clean_share 0.6, midpoint 0.5: fraction ~= 0.77 of coal capacity.
        config = ScenarioConfig()
        fleet = self._coal_fleet(10)
        survivors = apply_sigmoid_retirement(fleet, 0.6, config)
        coal = [g for g in survivors if g.fuel_type == "coal"]
        self.assertGreater(len(coal), 0)
        self.assertLess(len(coal), 10)

    def test_low_clean_share_retires_minimal_coal(self):
        # clean_share 0.3, midpoint 0.5: fraction ~= 0.08 -- minimal attrition.
        config = ScenarioConfig()
        fleet = self._coal_fleet(10)
        survivors = apply_sigmoid_retirement(fleet, 0.3, config)
        coal = [g for g in survivors if g.fuel_type == "coal"]
        self.assertGreaterEqual(len(coal), 8)

    def test_least_efficient_units_retire_first(self):
        config = ScenarioConfig()
        fleet = self._coal_fleet(10)
        survivors = apply_sigmoid_retirement(fleet, 0.6, config)
        retired_hr = {
            g.heat_rate for g in fleet
        } - {g.heat_rate for g in survivors}
        survivor_hr = {g.heat_rate for g in survivors}
        # Every retired unit is less efficient than every survivor.
        self.assertTrue(min(retired_hr) > max(survivor_hr))

    def test_retirement_order_is_coal_then_gas(self):
        # Both classes face the same fraction; both should shed capacity.
        config = ScenarioConfig()
        fleet = [
            _gen(f"C{i}", "coal", heat_rate=10.0 + i) for i in range(6)
        ] + [
            _gen(f"G{i}", "gas_cc", heat_rate=7.0 + i) for i in range(6)
        ]
        survivors = apply_sigmoid_retirement(fleet, 0.7, config)
        self.assertLess(
            len([g for g in survivors if g.fuel_type == "coal"]), 6
        )
        self.assertLess(
            len([g for g in survivors if g.fuel_type == "gas_cc"]), 6
        )


class TestComputeCleanShare(unittest.TestCase):
    """Clean-capacity fraction accounting."""

    def test_mixed_fleet_share(self):
        fleet = [
            _gen("W0", "wind", pmax=100.0),
            _gen("S0", "solar", pmax=100.0),
            _gen("C0", "coal", pmax=100.0),
            _gen("G0", "gas_cc", pmax=100.0),
        ]
        self.assertAlmostEqual(compute_clean_share(fleet), 0.5)

    def test_nuclear_and_hydro_count_as_clean(self):
        fleet = [
            _gen("N0", "nuclear", pmax=100.0),
            _gen("H0", "hydro", pmax=100.0),
            _gen("G0", "gas_ct", pmax=200.0),
        ]
        self.assertAlmostEqual(compute_clean_share(fleet), 0.5)

    def test_empty_fleet_is_zero(self):
        self.assertEqual(compute_clean_share([]), 0.0)


if __name__ == "__main__":
    unittest.main()
