"""Tests for exogenous REC prices in ``market_sim.policy.rec``.

Exogenous RECs shift the dispatch cost vector and the capacity-economics
revenue terms. They stack with IRA credits and the endogenous RPS shadow
price, and every ``rec_price_*`` defaults to ``0.0`` so existing behavior
is preserved.
"""

import unittest

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR, STORAGE_TIEBREAKER_EPSILON
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import VariableLayout, build_cost_vector
from market_sim.policy.ira import compute_dispatch_credits
from market_sim.policy.rec import (
    apply_rec_to_mc,
    compute_rec_dispatch_credits,
    compute_rec_revenue_per_mw,
    get_rec_price_for_new_entry,
)


def _fleet(fuel_types, hours=4):
    """Build ``FleetArrays`` with one generator per entry of ``fuel_types``."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone="Z0",
            fuel_type=ft,
            pmax_mw=1000.0,
        )
        for i, ft in enumerate(fuel_types)
    ]
    return generators_to_fleet_arrays(gens, ["Z0"], hours=hours)


class TestApplyRecToMc(unittest.TestCase):
    """Thermal-resource REC reductions to the dispatch marginal cost."""

    def test_nuclear_mc_reduction(self):
        # One nuclear gen at MC $10 with a $17 ZEC should bid -$7.
        config = ScenarioConfig(rec_price_nuclear=17.0)
        fleet = _fleet(["nuclear"])
        mc = np.full((1, 4), 10.0)
        result = apply_rec_to_mc(mc, fleet, config)
        self.assertIs(result, mc)
        self.assertTrue(np.allclose(result, -7.0))

    def test_gas_cc_mc_reduction(self):
        # One gas_cc gen with a $10 CCS REC has its MC reduced by $10.
        config = ScenarioConfig(rec_price_gas_cc=10.0)
        fleet = _fleet(["gas_cc"])
        mc = np.full((1, 4), 30.0)
        apply_rec_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, 20.0))

    def test_other_fuels_untouched(self):
        # Only nuclear and gas_cc are touched by apply_rec_to_mc.
        config = ScenarioConfig(rec_price_nuclear=17.0, rec_price_gas_cc=10.0)
        fleet = _fleet(["coal", "gas_ct"])
        mc = np.full((2, 4), 40.0)
        apply_rec_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, 40.0))


class TestWindSolarStacking(unittest.TestCase):
    """Exogenous wind/solar RECs stacking with the IRA production credit."""

    def test_wind_rec_stacks_with_ira_ptc(self):
        # IRA PTC $26 + exogenous wind REC $8 -> total wind_mc = -$34.
        config = ScenarioConfig(ira_ptc_wind=26.0, rec_price_wind=8.0)
        wind_mc, solar_mc = compute_dispatch_credits(config, 2030)
        wind_rec, solar_rec, _ = compute_rec_dispatch_credits(config)
        wind_mc -= wind_rec
        solar_mc -= solar_rec
        self.assertAlmostEqual(wind_mc, -34.0)
        self.assertAlmostEqual(solar_mc, 0.0)


class TestStorageDischargeCredit(unittest.TestCase):
    """Exogenous storage REC lowering the discharge slot cost."""

    def test_discharge_cost_net_of_credit(self):
        # rec_price_storage $5 -> discharge slot cost = epsilon - 5.
        config = ScenarioConfig(rec_price_storage=5.0)
        _, _, storage_rec = compute_rec_dispatch_credits(config)
        self.assertEqual(storage_rec, 5.0)

        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=3)
        mc = np.zeros((1, 3))
        cost = build_cost_vector(
            layout, mc, voll=5000.0, storage_discharge_credit=storage_rec
        )
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dis_slots = block[:, layout._dis_off : layout._soc_off]
        self.assertTrue(
            np.allclose(dis_slots, STORAGE_TIEBREAKER_EPSILON - 5.0)
        )
        # Charge slots stay at the plain cycling penalty.
        chg_slots = block[:, layout._chg_off : layout._dis_off]
        self.assertTrue(np.allclose(chg_slots, STORAGE_TIEBREAKER_EPSILON))


class TestRetirementRevenue(unittest.TestCase):
    """Exogenous REC revenue added to economic-retirement net revenue."""

    def test_nuclear_saved_by_zec(self):
        # A nuclear unit earns $15M of energy revenue against $18M of FOM:
        # unprofitable on energy alone. A $17/MWh ZEC over ~4 TWh of annual
        # generation adds $68M, lifting total revenue to $83M > $18M FOM.
        config = ScenarioConfig(rec_price_nuclear=17.0)
        energy_revenue = 15e6
        fom = 18e6
        annual_gen_mwh = 4e6  # 4 TWh

        # Without the ZEC the unit cannot cover fixed cost.
        self.assertLess(energy_revenue, fom)

        rec_revenue = compute_rec_revenue_per_mw(
            "nuclear", annual_gen_mwh, 1350.0, config
        )
        self.assertAlmostEqual(rec_revenue, 68e6)

        # With the ZEC the unit clears its going-forward fixed cost.
        net_revenue = energy_revenue + rec_revenue
        self.assertAlmostEqual(net_revenue, 83e6)
        self.assertGreater(net_revenue, fom)

    def test_rec_revenue_zero_for_unrecognized_fuel(self):
        config = ScenarioConfig(rec_price_nuclear=17.0)
        self.assertEqual(
            compute_rec_revenue_per_mw("coal", 4e6, 500.0, config), 0.0
        )


class TestNewEntryRevenue(unittest.TestCase):
    """Exogenous REC raising new-entry expected revenue."""

    def test_gas_cc_ccs_credit_flips_margin(self):
        # gas_cc LCOE $45/MWh, energy revenue $35/MWh: negative margin.
        # A $15/MWh CCS REC adds revenue and flips the margin positive.
        config = ScenarioConfig(rec_price_gas_cc=15.0)
        base_cf = 0.55
        lcoe = 45.0
        energy_price = 35.0

        annual_cost = lcoe * HOURS_PER_YEAR * base_cf
        effective_revenue = energy_price * base_cf * HOURS_PER_YEAR
        self.assertLess(effective_revenue - annual_cost, 0.0)

        exogenous_rec = get_rec_price_for_new_entry("gas_cc", config)
        self.assertEqual(exogenous_rec, 15.0)
        effective_revenue += exogenous_rec * base_cf * HOURS_PER_YEAR
        self.assertGreater(effective_revenue - annual_cost, 0.0)


class TestZeroRecRegression(unittest.TestCase):
    """All-default (zero) REC prices preserve existing behavior."""

    def test_apply_rec_to_mc_is_noop(self):
        config = ScenarioConfig()
        fleet = _fleet(["nuclear", "gas_cc"])
        mc = np.array([[30.0, 31.0, 32.0, 33.0], [20.0, 21.0, 22.0, 23.0]])
        mc_before = mc.copy()
        apply_rec_to_mc(mc, fleet, config)
        self.assertTrue(np.array_equal(mc, mc_before))

    def test_dispatch_credits_all_zero(self):
        config = ScenarioConfig()
        self.assertEqual(
            compute_rec_dispatch_credits(config), (0.0, 0.0, 0.0)
        )

    def test_revenue_and_new_entry_zero(self):
        config = ScenarioConfig()
        self.assertEqual(
            compute_rec_revenue_per_mw("nuclear", 4e6, 1000.0, config), 0.0
        )
        for tech in ("wind", "solar", "gas_cc"):
            self.assertEqual(get_rec_price_for_new_entry(tech, config), 0.0)

    def test_cost_vector_unchanged_with_zero_credit(self):
        # build_cost_vector with the default storage_discharge_credit=0.0
        # leaves discharge slots at the plain cycling penalty.
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=3)
        mc = np.zeros((1, 3))
        cost = build_cost_vector(layout, mc, voll=5000.0)
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dis_slots = block[:, layout._dis_off : layout._soc_off]
        self.assertTrue(
            np.allclose(dis_slots, STORAGE_TIEBREAKER_EPSILON)
        )


class TestDumpCostSafety(unittest.TestCase):
    """Overgeneration dump cost stays above any production credit."""

    def test_dump_cost_exceeds_negative_wind_mc(self):
        # A $30 wind REC makes wind_mc = -$30; the dump cost must exceed
        # that magnitude so the LP cannot overgenerate-and-dump for profit.
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=3)
        mc = np.zeros((1, 3))
        cost = build_cost_vector(layout, mc, voll=5000.0, wind_mc=-30.0)
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dump_slots = block[:, layout._dump_off :]
        self.assertTrue(np.all(dump_slots > 30.0))

    def test_dump_cost_accounts_for_storage_credit(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=3)
        mc = np.zeros((1, 3))
        cost = build_cost_vector(
            layout, mc, voll=5000.0, storage_discharge_credit=30.0
        )
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dump_slots = block[:, layout._dump_off :]
        self.assertTrue(np.all(dump_slots > 30.0))


if __name__ == "__main__":
    unittest.main()
