"""Tests for exogenous Environmental Attribute Credits (EACs).

Exogenous EACs shift the dispatch cost vector (real bidding behavior)
and the capacity-economics revenue terms. In dispatch they may stack
with IRA credits, but in capacity evolution the attribute payment is
``max(eac, rps_shadow_price)`` -- the certificate is sold once. Every
``eac_price_*`` defaults to ``0.0`` so existing behavior is preserved.
"""

import unittest

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR, STORAGE_TIEBREAKER_EPSILON
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import compute_attribute_revenue
from market_sim.model.dispatch import VariableLayout, build_cost_vector, solve_dispatch
from market_sim.policy.eac import (
    apply_eac_to_mc,
    compute_eac_dispatch_credits,
    get_eac_price_for_new_entry,
)
from market_sim.policy.ira import compute_dispatch_credits


def _fleet(fuel_types, hours=4, pmax=1000.0):
    """Build ``FleetArrays`` with one generator per entry of ``fuel_types``."""
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone="Z0",
            fuel_type=ft,
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, ft in enumerate(fuel_types)
    ]
    return generators_to_fleet_arrays(gens, ["Z0"], hours=hours)


def _no_renewables(n_zones, hours):
    """Zero wind/solar inputs for a thermal-only ``solve_dispatch`` call."""
    return dict(
        wind_cf=np.zeros((n_zones, hours)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, hours)),
        solar_cap=np.zeros(n_zones),
    )


class TestApplyEacToMc(unittest.TestCase):
    """Per-generator EAC reductions to the dispatch marginal cost."""

    def test_nuclear_mc_reduction(self):
        # One nuclear gen at MC $10 with a $17 ZEC should bid -$7.
        config = ScenarioConfig(eac_price_nuclear=17.0)
        fleet = _fleet(["nuclear"])
        mc = np.full((1, 4), 10.0)
        result = apply_eac_to_mc(mc, fleet, config)
        self.assertIs(result, mc)
        self.assertTrue(np.allclose(result, -7.0))

    def test_gas_cc_ccs_mc_reduction(self):
        # A gas_cc_ccs gen with a $10 CCS EAC has its MC reduced by $10.
        config = ScenarioConfig(eac_price_gas_cc_ccs=10.0)
        fleet = _fleet(["gas_cc_ccs"])
        mc = np.full((1, 4), 45.0)
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, 35.0))

    def test_conventional_gas_cc_untouched(self):
        # The CCS EAC must NOT touch conventional unabated gas CC.
        config = ScenarioConfig(eac_price_gas_cc_ccs=10.0)
        fleet = _fleet(["gas_cc"])
        mc = np.full((1, 4), 30.0)
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, 30.0))

    def test_other_fuels_untouched(self):
        # Coal and gas_ct earn no EAC.
        config = ScenarioConfig(
            eac_price_nuclear=17.0, eac_price_gas_cc_ccs=10.0
        )
        fleet = _fleet(["coal", "gas_ct"])
        mc = np.full((2, 4), 40.0)
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, 40.0))


class TestWindSolarStacking(unittest.TestCase):
    """Exogenous wind/solar EACs stacking with the IRA production credit."""

    def test_wind_eac_stacks_with_ira_ptc(self):
        # IRA PTC $26 + exogenous wind EAC $8 -> total wind_mc = -$34.
        # In dispatch the EAC is real bidding behavior, so it stacks with
        # the PTC; the non-stacking rule applies to capacity economics.
        config = ScenarioConfig(ira_ptc_wind=26.0, eac_price_wind=8.0)
        wind_mc, solar_mc = compute_dispatch_credits(config, 2027)
        wind_eac, solar_eac, _ = compute_eac_dispatch_credits(config)
        wind_mc -= wind_eac
        solar_mc -= solar_eac
        self.assertAlmostEqual(wind_mc, -34.0)
        self.assertAlmostEqual(solar_mc, 0.0)


class TestStorageDischargeCredit(unittest.TestCase):
    """Exogenous storage EAC lowering the discharge slot cost."""

    def test_discharge_cost_net_of_credit(self):
        # eac_price_storage $5 -> discharge slot cost = epsilon - 5.
        config = ScenarioConfig(eac_price_storage=5.0)
        _, _, storage_eac = compute_eac_dispatch_credits(config)
        self.assertEqual(storage_eac, 5.0)

        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=3)
        mc = np.zeros((1, 3))
        cost = build_cost_vector(
            layout, mc, voll=5000.0, storage_discharge_eac=storage_eac
        )
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dis_slots = block[:, layout._dis_off : layout._soc_off]
        self.assertTrue(
            np.allclose(dis_slots, STORAGE_TIEBREAKER_EPSILON - 5.0)
        )
        # Charge slots stay at the plain cycling penalty.
        chg_slots = block[:, layout._chg_off : layout._dis_off]
        self.assertTrue(np.allclose(chg_slots, STORAGE_TIEBREAKER_EPSILON))


class TestOffshoreWindEac(unittest.TestCase):
    """Offshore-wind EAC reduces per-generator MC below zero."""

    def test_offshore_wind_mc_goes_negative(self):
        # Offshore wind is a zero-MC generator; a $25 EAC drives MC to -25.
        config = ScenarioConfig(eac_price_offshore_wind=25.0)
        fleet = _fleet(["offshore_wind"])
        mc = np.zeros((1, 4))
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, -25.0))

    def test_offshore_wind_dispatched_over_gas(self):
        # With MC = -25 offshore wind clears ahead of $30 gas and supplies
        # the load even though its bid is negative.
        T = 4
        config = ScenarioConfig(eac_price_offshore_wind=25.0)
        fleet = _fleet(["offshore_wind", "gas_cc"], hours=T, pmax=200.0)
        mc = np.vstack([np.zeros(T), np.full(T, 30.0)])
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc[0], -25.0))

        demand = np.full((1, T), 80.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, voll=5000.0,
            **_no_renewables(1, T),
        )
        self.assertEqual(result.status, "Optimal")
        self.assertGreater(result.dispatch[0].sum(), 0.0)
        self.assertAlmostEqual(result.dispatch[1].sum(), 0.0, places=3)


class TestGeothermalEac(unittest.TestCase):
    """Geothermal EAC reduces per-generator MC like nuclear."""

    def test_geothermal_mc_reduction(self):
        # Geothermal MC $1.00 with a $10 clean-firm EAC bids -$9.00.
        config = ScenarioConfig(eac_price_geothermal=10.0)
        fleet = _fleet(["geothermal"])
        mc = np.full((1, 4), 1.0)
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc, -9.0))

    def test_geothermal_dispatched_over_gas(self):
        T = 4
        config = ScenarioConfig(eac_price_geothermal=10.0)
        fleet = _fleet(["geothermal", "gas_cc"], hours=T, pmax=200.0)
        mc = np.vstack([np.full(T, 1.0), np.full(T, 30.0)])
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.allclose(mc[0], -9.0))

        demand = np.full((1, T), 80.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=T, voll=5000.0,
            **_no_renewables(1, T),
        )
        self.assertEqual(result.status, "Optimal")
        self.assertGreater(result.dispatch[0].sum(), 0.0)
        self.assertAlmostEqual(result.dispatch[1].sum(), 0.0, places=3)


class TestCcsEacScope(unittest.TestCase):
    """The CCS EAC applies only to gas_cc_ccs, never conventional gas CC."""

    def test_ccs_eac_excludes_conventional_gas_cc(self):
        config = ScenarioConfig(eac_price_gas_cc_ccs=20.0)
        # Row 0 conventional gas_cc (MC 35), row 1 gas_cc_ccs (MC 45).
        fleet = _fleet(["gas_cc", "gas_cc_ccs"])
        mc = np.array([np.full(4, 35.0), np.full(4, 45.0)])
        apply_eac_to_mc(mc, fleet, config)
        # Conventional gas CC is untouched; CCS gas CC drops by $20.
        self.assertTrue(np.allclose(mc[0], 35.0))
        self.assertTrue(np.allclose(mc[1], 25.0))


class TestRetirementAttributeRevenue(unittest.TestCase):
    """Attribute revenue for economic retirement uses max(), not sum."""

    def test_nuclear_saved_by_zec(self):
        # A nuclear unit earns $15M of energy revenue against $18M of FOM:
        # unprofitable on energy alone. A $17/MWh ZEC over ~4 TWh of annual
        # generation adds $68M, lifting total revenue to $83M > $18M FOM.
        energy_revenue = 15e6
        fom = 18e6
        annual_gen_mwh = 4e6  # 4 TWh

        self.assertLess(energy_revenue, fom)

        attribute_revenue = compute_attribute_revenue(
            "nuclear", annual_gen_mwh, eac_price=17.0
        )
        self.assertAlmostEqual(attribute_revenue, 68e6)

        net_revenue = energy_revenue + attribute_revenue
        self.assertAlmostEqual(net_revenue, 83e6)
        self.assertGreater(net_revenue, fom)

    def test_eac_and_rps_do_not_stack_in_retirement(self):
        # Nuclear plant: FOM $200,000/MW-yr, 7,500 MWh/MW-yr generation,
        # energy revenue $25/MWh * 7,500 = $187,500/MW-yr (below FOM).
        fom = 200_000.0
        generation = 7_500.0
        energy_revenue = 25.0 * generation

        # Case A: EAC $17, RPS shadow $0 -> attribute = max(17, 0) * gen.
        case_a = compute_attribute_revenue(
            "nuclear", generation, eac_price=17.0, rps_shadow_price=0.0
        )
        self.assertAlmostEqual(case_a, 127_500.0)
        self.assertGreater(energy_revenue + case_a, fom)  # survives

        # Case B: EAC $17, RPS shadow $22 -> attribute = max(17, 22) * gen.
        case_b = compute_attribute_revenue(
            "nuclear", generation, eac_price=17.0, rps_shadow_price=22.0
        )
        self.assertAlmostEqual(case_b, 165_000.0)
        self.assertGreater(energy_revenue + case_b, fom)  # survives

        # Case C: stacking would (wrongly) give (17 + 22) * 7,500 = 292,500.
        # The model must produce Case B's $165,000, never the stacked sum.
        self.assertNotAlmostEqual(case_b, 292_500.0)
        self.assertAlmostEqual(case_b, 22.0 * generation)

    def test_eac_acts_as_attribute_price_floor(self):
        # RPS barely binding ($5): the $12 wind EAC is the binding signal.
        low_rps = compute_attribute_revenue(
            "wind", 1.0, eac_price=12.0, rps_shadow_price=5.0
        )
        self.assertAlmostEqual(low_rps, 12.0)
        # RPS very binding ($20): RPS compliance is the higher-value buyer.
        high_rps = compute_attribute_revenue(
            "wind", 1.0, eac_price=12.0, rps_shadow_price=20.0
        )
        self.assertAlmostEqual(high_rps, 20.0)


class TestNewEntryAttributeRevenue(unittest.TestCase):
    """Exogenous EAC raising new-entry expected revenue, using max()."""

    def test_eac_for_offshore_wind_and_geothermal(self):
        config = ScenarioConfig(
            eac_price_offshore_wind=30.0, eac_price_geothermal=12.0
        )
        self.assertEqual(
            get_eac_price_for_new_entry("offshore_wind", config), 30.0
        )
        self.assertEqual(
            get_eac_price_for_new_entry("geothermal", config), 12.0
        )

    def test_gas_cc_ccs_credit_flips_margin(self):
        # gas_cc_ccs LCOE $45/MWh, energy revenue $35/MWh: negative margin.
        # A $15/MWh CCS EAC adds revenue and flips the margin positive.
        config = ScenarioConfig(eac_price_gas_cc_ccs=15.0)
        base_cf = 0.55
        lcoe = 45.0
        energy_price = 35.0

        annual_cost = lcoe * HOURS_PER_YEAR * base_cf
        effective_revenue = energy_price * base_cf * HOURS_PER_YEAR
        self.assertLess(effective_revenue - annual_cost, 0.0)

        exogenous_eac = get_eac_price_for_new_entry("gas_cc_ccs", config)
        self.assertEqual(exogenous_eac, 15.0)
        effective_revenue += exogenous_eac * base_cf * HOURS_PER_YEAR
        self.assertGreater(effective_revenue - annual_cost, 0.0)

    def test_new_entry_uses_max_not_sum(self):
        # Solar candidate: LCOE $30/MWh, expected energy revenue $25/MWh.
        # EAC $8, RPS shadow $3 -> attribute = max(8, 3) = 8, total $33.
        config = ScenarioConfig(eac_price_solar=8.0)
        lcoe = 30.0
        energy_revenue = 25.0
        rps_shadow_price = 3.0

        eac_price = get_eac_price_for_new_entry("solar", config)
        effective_attribute = max(eac_price, rps_shadow_price)
        self.assertEqual(effective_attribute, 8.0)

        total = energy_revenue + effective_attribute
        self.assertEqual(total, 33.0)
        self.assertGreater(total, lcoe)  # builds
        # Stacking would wrongly give 25 + 8 + 3 = 36.
        self.assertNotEqual(total, 36.0)

        # EAC $0, RPS shadow $3 -> attribute = 3, total $28 < $30: no build.
        no_eac = max(
            get_eac_price_for_new_entry("solar", ScenarioConfig()),
            rps_shadow_price,
        )
        self.assertEqual(energy_revenue + no_eac, 28.0)
        self.assertLess(energy_revenue + no_eac, lcoe)

        # EAC $0, RPS shadow $8 -> attribute = 8, total $33 > $30: builds.
        high_rps = max(
            get_eac_price_for_new_entry("solar", ScenarioConfig()), 8.0
        )
        self.assertEqual(energy_revenue + high_rps, 33.0)
        self.assertGreater(energy_revenue + high_rps, lcoe)


class TestZeroEacRegression(unittest.TestCase):
    """All-default (zero) EAC prices preserve existing behavior."""

    def test_apply_eac_to_mc_is_noop(self):
        config = ScenarioConfig()
        fleet = _fleet(["nuclear", "gas_cc"])
        mc = np.array([[30.0, 31.0, 32.0, 33.0], [20.0, 21.0, 22.0, 23.0]])
        mc_before = mc.copy()
        apply_eac_to_mc(mc, fleet, config)
        self.assertTrue(np.array_equal(mc, mc_before))

    def test_dispatch_credits_all_zero(self):
        config = ScenarioConfig()
        self.assertEqual(
            compute_eac_dispatch_credits(config), (0.0, 0.0, 0.0)
        )

    def test_revenue_and_new_entry_zero(self):
        config = ScenarioConfig()
        self.assertEqual(
            compute_attribute_revenue("nuclear", 4e6, eac_price=0.0), 0.0
        )
        for tech in ("wind", "solar", "gas_cc_ccs", "offshore_wind",
                     "geothermal"):
            self.assertEqual(get_eac_price_for_new_entry(tech, config), 0.0)

    def test_cost_vector_unchanged_with_zero_credit(self):
        # build_cost_vector with the default storage_discharge_eac=0.0
        # leaves discharge slots at the plain cycling penalty.
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=3)
        mc = np.zeros((1, 3))
        cost = build_cost_vector(layout, mc, voll=5000.0)
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dis_slots = block[:, layout._dis_off : layout._soc_off]
        self.assertTrue(
            np.allclose(dis_slots, STORAGE_TIEBREAKER_EPSILON)
        )

    def test_zero_eac_dispatch_matches_no_eac_module(self):
        # Running the EAC pipeline with all-zero prices yields a dispatch
        # identical to one that never touched the EAC module.
        T = 6
        config = ScenarioConfig()
        fleet = _fleet(["gas_cc", "gas_ct"], hours=T, pmax=200.0)
        base_mc = np.vstack([np.full(T, 25.0), np.full(T, 60.0)])
        demand = np.full((1, T), 150.0)

        plain = solve_dispatch(
            fleet, demand, mc=base_mc.copy(), T=T, voll=5000.0,
            **_no_renewables(1, T),
        )

        eac_mc = base_mc.copy()
        apply_eac_to_mc(eac_mc, fleet, config)
        wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
        with_eac = solve_dispatch(
            fleet, demand, mc=eac_mc, T=T, voll=5000.0,
            wind_mc=0.0 - wind_eac, solar_mc=0.0 - solar_eac,
            storage_discharge_eac=storage_eac, **_no_renewables(1, T),
        )

        np.testing.assert_allclose(with_eac.dispatch, plain.dispatch)
        np.testing.assert_allclose(with_eac.prices, plain.prices)


class TestDumpCostSafety(unittest.TestCase):
    """Overgeneration dump cost stays above any production credit."""

    def test_dump_cost_exceeds_negative_wind_mc(self):
        # A $30 wind EAC makes wind_mc = -$30; the dump cost must exceed
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
            layout, mc, voll=5000.0, storage_discharge_eac=30.0
        )
        block = cost.reshape(layout.T, layout.vars_per_hour)
        dump_slots = block[:, layout._dump_off :]
        self.assertTrue(np.all(dump_slots > 30.0))


if __name__ == "__main__":
    unittest.main()
