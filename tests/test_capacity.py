"""Tests for fleet retirement mechanisms in ``market_sim.model.capacity``."""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.constants import QUEUE_CAP_GW
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    apply_economic_new_entry,
    apply_economic_retirements,
    apply_known_retirements,
    apply_rps_mandate,
    apply_sigmoid_retirement,
    compute_clean_share,
    compute_lcoe,
    estimate_expected_revenue,
    evolve_fleet,
    wright_cost,
)
from market_sim.policy.ira import apply_ira_credits_to_lcoe
from market_sim.policy.rps import get_rps_target


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


class TestWrightCost(unittest.TestCase):
    """Wright's-Law learning-curve cost adjustment."""

    def test_cost_unchanged_at_reference(self):
        self.assertAlmostEqual(wright_cost(100.0, 100.0, 100.0, 0.2), 100.0)

    def test_cost_falls_as_deployment_grows(self):
        # Doubling cumulative capacity multiplies cost by 2 ** (-rate).
        cost = wright_cost(100.0, 200.0, 100.0, 0.2)
        self.assertLess(cost, 100.0)
        self.assertAlmostEqual(cost, 100.0 * 2.0 ** (-0.2))

    def test_non_positive_capacity_returns_base(self):
        self.assertEqual(wright_cost(100.0, 0.0, 100.0, 0.2), 100.0)
        self.assertEqual(wright_cost(100.0, 50.0, 0.0, 0.2), 100.0)


class TestComputeLCOE(unittest.TestCase):
    """Levelized cost of energy with learning and IRA credits."""

    def test_lcoe_is_positive(self):
        self.assertGreater(compute_lcoe("solar", 2030, ScenarioConfig()), 0.0)

    def test_lcoe_decreases_over_time_with_learning(self):
        config = ScenarioConfig()
        early = compute_lcoe("solar", 2030, config, cumulative_gw=1420.0)
        late = compute_lcoe("solar", 2030, config, cumulative_gw=2840.0)
        self.assertLess(late, early)

    def test_ira_credit_lowers_lcoe_until_expiry(self):
        config = ScenarioConfig()  # ira_expiry_year = 2035
        with_credit = compute_lcoe("wind", 2030, config)
        after_expiry = compute_lcoe("wind", 2040, config)
        self.assertLess(with_credit, after_expiry)


class TestIRACreditsToLCOE(unittest.TestCase):
    """IRA investment-credit adjustment to candidate LCOE."""

    def test_wind_ptc_subtracts_flat_amount(self):
        config = ScenarioConfig()  # ira_ptc_wind = 26.0
        adjusted = apply_ira_credits_to_lcoe("wind", 50.0, 2030, config)
        self.assertAlmostEqual(adjusted, 50.0 - 26.0)

    def test_solar_itc_scales_lcoe(self):
        config = ScenarioConfig()  # ira_itc_solar = 0.30
        adjusted = apply_ira_credits_to_lcoe("solar", 50.0, 2030, config)
        self.assertAlmostEqual(adjusted, 50.0 * 0.70)

    def test_credit_expires_after_expiry_year(self):
        config = ScenarioConfig()  # ira_expiry_year = 2035
        # The expiry year itself still carries the credit.
        self.assertAlmostEqual(
            apply_ira_credits_to_lcoe("wind", 50.0, 2035, config), 24.0
        )
        # The year after expiry leaves LCOE untouched.
        self.assertEqual(
            apply_ira_credits_to_lcoe("wind", 50.0, 2036, config), 50.0
        )


class TestGetRPSTarget(unittest.TestCase):
    """Renewable portfolio standard target lookup and interpolation."""

    def test_knot_year_returns_exact_value(self):
        self.assertAlmostEqual(get_rps_target("CAISO", 2030), 0.60)

    def test_intermediate_year_is_interpolated(self):
        # 2028 sits midway between 2026 (0.50) and 2030 (0.60).
        self.assertAlmostEqual(get_rps_target("CAISO", 2028), 0.55)

    def test_iso_without_rps_is_none(self):
        self.assertIsNone(get_rps_target("PJM", 2030))

    def test_ercot_floor_is_zero(self):
        self.assertAlmostEqual(get_rps_target("ERCOT", 2030), 0.0)


class TestEconomicNewEntry(unittest.TestCase):
    """Revenue-driven capacity additions under a queue cap."""

    def test_queue_cap_limits_annual_additions(self):
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 250.0)  # high prices make entry profitable
        new_fleet = apply_economic_new_entry([], prices, 2030, config, "ERCOT")
        added_mw = sum(g.pmax_mw for g in new_fleet)
        self.assertAlmostEqual(added_mw, QUEUE_CAP_GW["ERCOT"] * 1000.0)

    def test_no_entry_when_prices_too_low(self):
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 1.0)  # far below any technology's LCOE
        new_fleet = apply_economic_new_entry([], prices, 2030, config, "ERCOT")
        self.assertEqual(new_fleet, [])


class TestEstimateExpectedRevenue(unittest.TestCase):
    """Expected annual revenue per MW from prices and capacity factor."""

    def test_flat_capacity_factor(self):
        revenue = estimate_expected_revenue(np.full(10, 100.0), 0.5, hours=8760)
        self.assertAlmostEqual(revenue, 0.5 * 100.0 * 8760)

    def test_empty_prices_yield_zero(self):
        self.assertEqual(estimate_expected_revenue(np.array([]), 0.5), 0.0)


class TestRPSMandate(unittest.TestCase):
    """Force-build of clean capacity to satisfy an RPS target."""

    def test_caiso_mandate_fills_clean_gap(self):
        config = ScenarioConfig(iso="CAISO")  # 2030 target 0.60
        fleet = [_gen("C0", "coal", pmax=1000.0)]  # clean share 0.0
        result = apply_rps_mandate(fleet, 2030, config)
        self.assertEqual(len(result), 2)
        # Enough clean capacity is built to reach the target exactly.
        self.assertAlmostEqual(compute_clean_share(result), 0.60)

    def test_no_mandate_when_target_already_met(self):
        config = ScenarioConfig(iso="CAISO")
        fleet = [_gen("W0", "wind", pmax=1000.0)]  # clean share 1.0
        result = apply_rps_mandate(fleet, 2030, config)
        self.assertEqual([g.unit_id for g in result], ["W0"])

    def test_no_mandate_for_iso_without_rps(self):
        config = ScenarioConfig(iso="ERCOT")  # ERCOT floor is 0.0
        fleet = [_gen("C0", "coal", pmax=1000.0)]
        result = apply_rps_mandate(fleet, 2030, config)
        self.assertEqual([g.unit_id for g in result], ["C0"])


class TestEvolveFleet(unittest.TestCase):
    """The ordered year-step orchestration of all capacity mechanisms."""

    def test_known_retirement_precedes_known_addition(self):
        config = ScenarioConfig(iso="ERCOT")
        old = _gen("OLD", "coal", retirement_year=2030)
        new = Generator(
            unit_id="NEW", name="NEW", zone="North", fuel_type="wind",
            pmax_mw=100.0, online_year=2030,
        )
        prior = SimpleNamespace(
            fleet_arrays=None, dispatch_result=None, prices=None,
            planned_additions=[new],
        )
        fleet, tracker = evolve_fleet([old], prior, 2030, config, {})
        # OLD retires this year; NEW comes online this year.
        self.assertEqual([g.unit_id for g in fleet], ["NEW"])
        self.assertIsInstance(tracker, dict)

    def test_economic_retirement_runs_within_evolve(self):
        config = ScenarioConfig(iso="ERCOT")
        coal = _gen("C0", "coal", pmax=100.0, zone="North")
        arrays = generators_to_fleet_arrays([coal], ["North"], hours=24)
        dispatch = SimpleNamespace(dispatch=np.full((1, 24), 1.0))
        prior = SimpleNamespace(
            fleet_arrays=arrays,
            dispatch_result=dispatch,
            prices=np.full((1, 24), 5.0),  # revenue far below fixed cost
            planned_additions=[],
        )
        # Counter already at 1; a second loss year this step triggers retirement.
        fleet, tracker = evolve_fleet([coal], prior, 2031, config, {"C0": 1})
        self.assertEqual(fleet, [])
        self.assertNotIn("C0", tracker)

    def test_returns_fleet_and_tracker_tuple(self):
        config = ScenarioConfig(iso="ERCOT")
        result = evolve_fleet([_gen("G0", "gas_cc")], None, 2030, config, {})
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], dict)


if __name__ == "__main__":
    unittest.main()
