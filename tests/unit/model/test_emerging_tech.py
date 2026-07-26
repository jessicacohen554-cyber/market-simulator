"""Tests for emerging generation technologies.

Covers the hydrogen fuel-cost derivation, hydrogen / CCUS marginal costs,
geothermal and offshore-wind dispatch, capacity-evolution gating, IRA
credit treatment and electrolyzer-efficiency interpolation.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    CCUS_PARAMS,
    CO2_RATES,
    HEAT_RATE_BINS,
    HYDROGEN_TURBINE_PARAMS,
    MMBTU_PER_MWH,
    OFFSHORE_WIND_MIN_CF,
    OFFSHORE_WIND_PARAMS,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    assemble_mc,
    generators_to_fleet_arrays,
)
from market_sim.data.renewables import (
    derive_offshore_wind_profile,
    inject_offshore_wind_availability,
)
from market_sim.data.hydrogen import (
    compute_h2_fuel_cost,
    get_electrolyzer_efficiency,
    h2_fuel_cost_per_mmbtu,
)
from market_sim.model.capacity import (
    _emerging_lcoe,
    _make_new_generator,
    _new_entry_candidates,
    apply_economic_new_entry,
)
from market_sim.model.capacity import compute_lcoe
from market_sim.model.dispatch import solve_dispatch
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    ccus_45q_credit_per_mwh,
    h2_45v_credit_per_mmbtu,
)


def _gen(unit_id, fuel_type, pmax, **kw):
    """Build a Generator with explicit, outage-free attributes for tests."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z0",
        fuel_type=fuel_type,
        pmax_mw=pmax,
        eford=kw.pop("eford", 0.0),
        **kw,
    )


class TestH2FuelCostDerivation(unittest.TestCase):
    """Hydrogen fuel cost is derived from renewable LCOE and efficiency."""

    def test_formula_matches_worked_example(self):
        # (25 / 0.65) / 3.412 = 11.27 $/MMBtu.
        cost = h2_fuel_cost_per_mmbtu(25.0, 0.65)
        self.assertAlmostEqual(cost, (25.0 / 0.65) / 3.412, places=6)
        self.assertAlmostEqual(cost, 11.273, places=2)

    def test_cost_falls_when_renewable_lcoe_falls(self):
        # Wright's Law: cheaper renewables make cheaper hydrogen.
        self.assertLess(
            h2_fuel_cost_per_mmbtu(20.0, 0.65),
            h2_fuel_cost_per_mmbtu(25.0, 0.65),
        )

    def test_cost_falls_when_electrolyzer_improves(self):
        # A more efficient electrolyzer needs less electricity per MMBtu.
        self.assertLess(
            h2_fuel_cost_per_mmbtu(25.0, 0.72),
            h2_fuel_cost_per_mmbtu(25.0, 0.65),
        )

    def test_compute_picks_cheaper_renewable(self):
        # compute_h2_fuel_cost uses min(wind_lcoe, solar_lcoe).
        config = ScenarioConfig(iso="ERCOT")
        wind = compute_lcoe("wind", 2030, config)
        solar = compute_lcoe("solar", 2030, config)
        eta = get_electrolyzer_efficiency(2030, config)
        expected = h2_fuel_cost_per_mmbtu(min(wind, solar), eta)
        self.assertAlmostEqual(
            compute_h2_fuel_cost(2030, config, "ERCOT"), expected, places=6
        )

    def test_uses_mmbtu_per_mwh_identity(self):
        self.assertAlmostEqual(MMBTU_PER_MWH, 3.412)


class TestH2TurbineMarginalCost(unittest.TestCase):
    """Hydrogen turbines dispatch like any thermal unit on a derived fuel."""

    def _mc(self, generators, h2_cost, nox_price=0.0):
        fleet = generators_to_fleet_arrays(generators, ["Z0"], hours=1)
        fuel_prices = np.full((len(generators), 1), h2_cost)
        return assemble_mc(fleet, fuel_prices, 0.0, nox_price)

    def test_h2_ct_and_ccgt_marginal_cost(self):
        config = ScenarioConfig(iso="ERCOT")
        ct = _make_new_generator("hydrogen_ct", 100.0, "Z0", 2035, 0, config, "ERCOT")
        ccgt = _make_new_generator(
            "hydrogen_ccgt", 100.0, "Z0", 2035, 1, config, "ERCOT"
        )
        h2_cost = 11.0
        mc = self._mc([ct, ccgt], h2_cost)
        # mc = heat_rate * h2_fuel_cost + vom (emission rate is zero).
        self.assertAlmostEqual(mc[0, 0], 9.5 * h2_cost + 4.0, places=6)
        self.assertAlmostEqual(mc[1, 0], 6.9 * h2_cost + 3.5, places=6)

    def test_ccgt_cheaper_than_ct(self):
        config = ScenarioConfig(iso="ERCOT")
        ct = _make_new_generator("hydrogen_ct", 100.0, "Z0", 2035, 0, config, "ERCOT")
        ccgt = _make_new_generator(
            "hydrogen_ccgt", 100.0, "Z0", 2035, 1, config, "ERCOT"
        )
        mc = self._mc([ct, ccgt], 11.0)
        self.assertLess(mc[1, 0], mc[0, 0])

    def test_nox_cost_enters_marginal_cost(self):
        config = ScenarioConfig(iso="ERCOT")
        ct = _make_new_generator("hydrogen_ct", 100.0, "Z0", 2035, 0, config, "ERCOT")
        params = HYDROGEN_TURBINE_PARAMS["h2_ct"]
        mc = self._mc([ct], 11.0, nox_price=10000.0)
        expected = 9.5 * 11.0 + 4.0 + params["nox_rate"] * 10000.0
        self.assertAlmostEqual(mc[0, 0], expected, places=6)


class TestCCUSMarginalCost(unittest.TestCase):
    """CCUS becomes competitive against unabated gas as carbon prices rise."""

    def _mc(self, generators, gas_price, carbon_price):
        fleet = generators_to_fleet_arrays(generators, ["Z0"], hours=1)
        fuel_prices = np.full((len(generators), 1), gas_price)
        return assemble_mc(fleet, fuel_prices, carbon_price, 0.0)

    def setUp(self):
        config = ScenarioConfig(iso="ERCOT")
        self.unabated = _make_new_generator(
            "gas_cc", 100.0, "Z0", 2035, 0, config, "ERCOT"
        )
        self.ccs = _make_new_generator(
            "gas_cc_ccs", 100.0, "Z0", 2035, 1, config, "ERCOT"
        )

    def test_ccs_has_penalized_heat_rate_and_reduced_emissions(self):
        base_hr = min(HEAT_RATE_BINS["gas_cc"].values())
        base_co2 = min(CO2_RATES["gas_cc"].values())
        penalty = CCUS_PARAMS["gas_cc_ccs_90"]["heat_rate_penalty"]
        self.assertAlmostEqual(self.ccs.heat_rate, base_hr * penalty)
        self.assertAlmostEqual(self.ccs.emission_rate_co2, base_co2 * 0.10)

    def test_ccs_dearer_without_carbon_price(self):
        # Parasitic load, solvent VOM and CO2 transport make CCS dearer
        # than unabated gas when carbon is free.
        mc = self._mc([self.unabated, self.ccs], gas_price=4.0, carbon_price=0.0)
        self.assertGreater(mc[1, 0], mc[0, 0])

    def test_ccs_cheaper_at_high_carbon_price(self):
        # At $100/tCO2 capture avoids most of the carbon cost.
        mc = self._mc([self.unabated, self.ccs], gas_price=4.0, carbon_price=100.0)
        self.assertLess(mc[1, 0], mc[0, 0])

    def test_carbon_price_crossover_exists(self):
        # There is a carbon price between $0 and $100 where CCS overtakes
        # unabated gas.
        crossover = None
        for carbon in range(0, 101):
            mc = self._mc(
                [self.unabated, self.ccs],
                gas_price=4.0,
                carbon_price=float(carbon),
            )
            if mc[1, 0] < mc[0, 0]:
                crossover = carbon
                break
        self.assertIsNotNone(crossover)
        self.assertTrue(20 < crossover < 90)


class TestGeothermalDispatch(unittest.TestCase):
    """Geothermal dispatches as cheap, near-free baseload."""

    def test_geothermal_fills_first_gas_sets_price(self):
        geo = _gen("GEO", "geothermal", 100.0, vom=1.0)
        gas = _gen("GAS", "gas_cc", 200.0)
        fleet = generators_to_fleet_arrays([geo, gas], ["Z0"], hours=1)
        mc = np.array([[1.0], [40.0]])
        demand = np.array([[150.0]])
        zeros = np.zeros((1, 1))
        result = solve_dispatch(
            fleet, demand, zeros, np.zeros(1), zeros, np.zeros(1), mc=mc
        )
        self.assertAlmostEqual(result.dispatch[0, 0], 100.0, places=3)
        self.assertAlmostEqual(result.dispatch[1, 0], 50.0, places=3)
        self.assertAlmostEqual(result.prices[0, 0], 40.0, places=3)


class TestDeriveOffshoreProfile(unittest.TestCase):
    """Pure derivation of the offshore CF profile from the onshore profile."""

    def test_derive_offshore_profile_mean_matches_target(self):
        # The smoothed/floored profile is rescaled to the target average CF.
        rng = np.random.RandomState(0)
        onshore = rng.rand(8760)
        onshore *= 0.35 / onshore.mean()
        derived = derive_offshore_wind_profile(onshore, target_avg_cf=0.45)
        self.assertLess(abs(derived.mean() - 0.45), 0.001)

    def test_derive_offshore_profile_clips_to_unit_interval(self):
        # An extreme onshore profile plus a high target stays within [0, 1].
        onshore = np.full(8760, 0.98)
        onshore[::2] = 0.99
        derived = derive_offshore_wind_profile(onshore, target_avg_cf=0.95)
        self.assertTrue(np.all(derived >= 0.0))
        self.assertTrue(np.all(derived <= 1.0))


class TestOffshoreWindProfileShape(unittest.TestCase):
    """Smoothing and the minimum floor of the derived offshore profile."""

    def test_offshore_profile_smoother_than_onshore(self):
        rng = np.random.RandomState(1)
        onshore = rng.rand(8760)  # high variance, uniform noise
        derived = derive_offshore_wind_profile(onshore, target_avg_cf=0.45)
        self.assertLess(derived.std(), onshore.std())

    def test_offshore_profile_has_minimum_floor(self):
        onshore = np.linspace(0.0, 0.6, 8760)  # includes zero hours
        derived = derive_offshore_wind_profile(onshore, target_avg_cf=0.45)
        self.assertTrue(np.all(derived >= OFFSHORE_WIND_MIN_CF))


class TestOffshoreWindDispatch(unittest.TestCase):
    """Offshore wind dispatches against an hourly availability profile."""

    @staticmethod
    def _onshore(hours):
        """Return a (1, hours) sinusoidal onshore wind profile."""
        t = np.arange(hours)
        profile = 0.35 + 0.25 * np.sin(2 * np.pi * t / 24.0)
        return profile.reshape(1, hours)

    def test_offshore_has_hourly_varying_availability(self):
        # After injection the offshore availability row varies hour-to-hour
        # and averages the target offshore CF.
        hours = 48
        ow = _gen("OW", "offshore_wind", 500.0)
        gas = _gen("GAS", "gas_ct", 300.0)
        fleet = generators_to_fleet_arrays([ow, gas], ["Z0"], hours=hours)
        config = ScenarioConfig(iso="ERCOT")
        inject_offshore_wind_availability(fleet, self._onshore(hours), config, "ERCOT")
        avail = fleet.availability[0]
        self.assertGreater(avail.std(), 0.0)
        target = OFFSHORE_WIND_PARAMS["fixed_bottom"]["base_cf"]
        self.assertLess(abs(avail.mean() - target), 0.001)
        # The gas row keeps its flat availability.
        self.assertAlmostEqual(fleet.availability[1].std(), 0.0, places=9)

    def test_offshore_dispatch_varies_with_profile(self):
        # 500 MW offshore + 300 MW gas, constant 300 MW demand: offshore
        # output tracks its hourly profile and gas fills the residual.
        hours = 24
        ow = _gen("OW", "offshore_wind", 500.0)
        gas = _gen("GAS", "gas_ct", 300.0)
        fleet = generators_to_fleet_arrays([ow, gas], ["Z0"], hours=hours)
        config = ScenarioConfig(iso="ERCOT")
        inject_offshore_wind_availability(fleet, self._onshore(hours), config, "ERCOT")
        mc = np.tile(np.array([[0.0], [70.0]]), (1, hours))
        demand = np.full((1, hours), 300.0)
        zeros = np.zeros((1, hours))
        result = solve_dispatch(
            fleet, demand, zeros, np.zeros(1), zeros, np.zeros(1), mc=mc
        )
        offshore = result.dispatch[0]
        self.assertGreater(offshore.std(), 0.0)
        for t in range(hours):
            self.assertAlmostEqual(
                result.dispatch[0, t] + result.dispatch[1, t], 300.0, places=3
            )

    def _solve_flat(self, demand_mw):
        # A controlled, constant 0.45 offshore availability — the state the
        # injected profile collapses to when the input has no variation.
        ow = _gen("OW", "offshore_wind", 500.0)
        gas = _gen("GAS", "gas_ct", 300.0)
        fleet = generators_to_fleet_arrays([ow, gas], ["Z0"], hours=1)
        fleet.availability[0, :] = 0.45
        mc = np.array([[0.0], [70.0]])
        demand = np.array([[demand_mw]])
        zeros = np.zeros((1, 1))
        return solve_dispatch(
            fleet, demand, zeros, np.zeros(1), zeros, np.zeros(1), mc=mc
        )

    def test_offshore_capped_by_capacity_factor(self):
        # Demand 400 > 225 MW available offshore: gas fills the rest.
        result = self._solve_flat(400.0)
        self.assertAlmostEqual(result.dispatch[0, 0], 225.0, places=3)
        self.assertAlmostEqual(result.dispatch[1, 0], 175.0, places=3)
        self.assertAlmostEqual(result.prices[0, 0], 70.0, places=3)

    def test_offshore_alone_serves_low_demand(self):
        # Demand 150 < 225 MW available: offshore covers it, gas idle.
        result = self._solve_flat(150.0)
        self.assertAlmostEqual(result.dispatch[0, 0], 150.0, places=3)
        self.assertAlmostEqual(result.dispatch[1, 0], 0.0, places=3)
        self.assertLess(result.prices[0, 0], 1.0)


class TestEmergingCapacityEvolution(unittest.TestCase):
    """Availability-year gating and queue caps for emerging new entry."""

    def test_h2_absent_before_available_year(self):
        config = ScenarioConfig(iso="ERCOT")  # h2_available_year = 2035
        fleet, _ = apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2030,
            config,
            "ERCOT",
            gas_price_per_mmbtu=3.5,
        )
        self.assertFalse(any("hydrogen" in g.fuel_type for g in fleet))

    def test_h2_builds_after_available_year_when_economic(self):
        # Year 2027: gas is expensive and carbon is high, so unabated gas
        # CC is uneconomic, leaving the shared queue cap for hydrogen. The
        # §45V credit ends after 2027 (OBBBA), so the test sits inside the
        # credit window with H2 turbines made available a year earlier.
        config = ScenarioConfig(iso="ERCOT", h2_available_year=2026)
        fleet, _ = apply_economic_new_entry(
            [],
            np.full(8760, 100.0),
            2027,
            config,
            "ERCOT",
            gas_price_per_mmbtu=12.0,
            carbon_price=150.0,
        )
        self.assertTrue(any("hydrogen" in g.fuel_type for g in fleet))
        self.assertFalse(any(g.fuel_type == "gas_cc" for g in fleet))

    def test_ccus_needs_high_carbon_price(self):
        # Hydrogen and geothermal disabled so CCUS competes for the shared
        # gas_cc queue group against unabated gas alone. A $110/MWh flat
        # screening price gives the (FF-1E) ATB-derived CCS its margin at high
        # carbon; the mechanism under test is the carbon-dependence (no CCS at
        # carbon 0, CCS at carbon 200), not the exact threshold. (Pre-FF-1E this
        # used $67.5 tuned to the then-understated CCS capex; the operative
        # new-build CCS cost — CCUS_PARAMS, reconciled to ATB 2024's 95% CCS
        # class — is now ~$3,100/kW / ~$71/kW-yr, so CCS clears at a higher
        # screening price.)
        config = ScenarioConfig(
            iso="ERCOT", h2_available_year=2099, egs_available_year=2099
        )
        # Year 2032 is the last year the §45Q credit is available (OBBBA).
        cheap_carbon, _ = apply_economic_new_entry(
            [],
            np.full(8760, 110.0),
            2032,
            config,
            "ERCOT",
            gas_price_per_mmbtu=4.0,
            carbon_price=0.0,
        )
        self.assertFalse(any(g.fuel_type == "gas_cc_ccs" for g in cheap_carbon))
        dear_carbon, _ = apply_economic_new_entry(
            [],
            np.full(8760, 110.0),
            2032,
            config,
            "ERCOT",
            gas_price_per_mmbtu=4.0,
            carbon_price=200.0,
        )
        self.assertTrue(any(g.fuel_type == "gas_cc_ccs" for g in dear_carbon))

    def test_geothermal_absent_in_ercot_before_egs_year(self):
        config = ScenarioConfig(iso="ERCOT")  # egs_available_year = 2030
        fleet, _ = apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2029,
            config,
            "ERCOT",
        )
        self.assertFalse(any(g.fuel_type == "geothermal" for g in fleet))

    def test_geothermal_builds_in_ercot_after_egs_year(self):
        config = ScenarioConfig(iso="ERCOT")
        fleet, _ = apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2035,
            config,
            "ERCOT",
        )
        geo = [g for g in fleet if g.fuel_type == "geothermal"]
        self.assertEqual(len(geo), 1)
        # Geothermal carries a 20%-of-rated turn-down floor.
        self.assertAlmostEqual(geo[0].pmin_mw, 0.20 * geo[0].pmax_mw)

    def test_offshore_wind_candidate_only_in_eligible_iso(self):
        # Offshore wind joins the candidate pool in CAISO but not ERCOT.
        config = ScenarioConfig()
        self.assertIn("offshore_wind", _new_entry_candidates(2035, config, "CAISO"))
        self.assertNotIn("offshore_wind", _new_entry_candidates(2035, config, "ERCOT"))

    def test_offshore_wind_not_built_in_ineligible_iso(self):
        # ERCOT is not in offshore_wind_eligible_isos by default, so no
        # offshore-wind generator can enter there.
        config = ScenarioConfig(iso="ERCOT")
        fleet, _ = apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2035,
            config,
            "ERCOT",
        )
        self.assertFalse(any(g.fuel_type == "offshore_wind" for g in fleet))

    def test_offshore_wind_built_in_eligible_iso(self):
        # In CAISO, with geothermal pushed out and a strong offshore
        # resource (CF override), offshore wind clears the screen.
        config = ScenarioConfig(
            iso="CAISO",
            egs_available_year=2099,
            offshore_wind_cf_override=0.75,
        )
        fleet, _ = apply_economic_new_entry(
            [],
            np.full(8760, 250.0),
            2035,
            config,
            "CAISO",
        )
        self.assertTrue(any(g.fuel_type == "offshore_wind" for g in fleet))

    def test_queue_caps_bind_total_additions(self):
        # Every technology is wildly profitable; total build still cannot
        # exceed the ISO interconnection cap.
        from market_sim.config.constants import QUEUE_CAP_GW

        config = ScenarioConfig(iso="CAISO")
        fleet, additions = apply_economic_new_entry(
            [],
            np.full(8760, 500.0),
            2035,
            config,
            "CAISO",
        )
        built = sum(g.pmax_mw for g in fleet)
        built += sum(mw for by in additions.values() for mw in by.values())
        self.assertLessEqual(built, QUEUE_CAP_GW["CAISO"] * 1000.0 + 1e-6)


class TestEmergingIRACredits(unittest.TestCase):
    """IRA 45V (hydrogen), 45Q (CCUS) and the geothermal PTC."""

    def test_45v_credit_active_then_expires(self):
        config = ScenarioConfig()  # ira_h2_45v_last_year = 2027
        self.assertGreater(h2_45v_credit_per_mmbtu(2027, config), 0.0)
        self.assertEqual(h2_45v_credit_per_mmbtu(2040, config), 0.0)

    def test_45v_credit_reduces_effective_h2_fuel_cost(self):
        config = ScenarioConfig(iso="ERCOT")
        gross = compute_h2_fuel_cost(2027, config, "ERCOT")
        credit = h2_45v_credit_per_mmbtu(2027, config)
        effective = max(0.0, gross - credit)
        self.assertLess(effective, gross)

    def test_45q_credit_active_then_expires(self):
        config = ScenarioConfig()
        self.assertGreater(ccus_45q_credit_per_mwh(0.3, 2030, config), 0.0)
        self.assertEqual(ccus_45q_credit_per_mwh(0.3, 2040, config), 0.0)

    def test_45q_credit_lowers_ccus_lcoe(self):
        config = ScenarioConfig(iso="ERCOT")
        with_credit = _emerging_lcoe(
            "gas_cc_ccs", 2030, config, "ERCOT", 0.55, 4.0, 50.0
        )
        after_expiry = _emerging_lcoe(
            "gas_cc_ccs", 2040, config, "ERCOT", 0.55, 4.0, 50.0
        )
        self.assertLess(with_credit, after_expiry)

    def test_geothermal_ptc_matches_wind_ptc(self):
        # Within the full-credit window both earn the same flat PTC.
        config = ScenarioConfig()  # ira_ptc_wind = 26.0
        geo = apply_ira_credits_to_lcoe("geothermal", 50.0, 2027, config)
        wind = apply_ira_credits_to_lcoe("wind", 50.0, 2027, config)
        self.assertAlmostEqual(geo, wind)
        self.assertAlmostEqual(geo, 50.0 - config.ira_ptc_wind)

    def test_geothermal_ptc_expires(self):
        config = ScenarioConfig()
        self.assertAlmostEqual(
            apply_ira_credits_to_lcoe("geothermal", 50.0, 2040, config), 50.0
        )


class TestElectrolyzerEfficiencyInterpolation(unittest.TestCase):
    """Electrolyzer efficiency interpolates between milestone years."""

    def test_base_year_is_base_efficiency(self):
        config = ScenarioConfig()  # pem
        self.assertAlmostEqual(get_electrolyzer_efficiency(2026, config), 0.65)

    def test_milestone_year_2035(self):
        config = ScenarioConfig()
        self.assertAlmostEqual(get_electrolyzer_efficiency(2035, config), 0.72)

    def test_intermediate_year_is_interpolated(self):
        config = ScenarioConfig()
        # 2030 sits 4/9 of the way from 2026 (0.65) to 2035 (0.72).
        expected = 0.65 + (0.72 - 0.65) * (2030 - 2026) / (2035 - 2026)
        self.assertAlmostEqual(get_electrolyzer_efficiency(2030, config), expected)

    def test_late_year_capped_at_2045_value(self):
        config = ScenarioConfig()
        self.assertAlmostEqual(get_electrolyzer_efficiency(2050, config), 0.76)

    def test_override_supersedes_lookup(self):
        config = ScenarioConfig(electrolyzer_efficiency_override=0.90)
        self.assertAlmostEqual(get_electrolyzer_efficiency(2030, config), 0.90)

    def test_alkaline_differs_from_pem(self):
        pem = get_electrolyzer_efficiency(2026, ScenarioConfig())
        alkaline = get_electrolyzer_efficiency(
            2026, ScenarioConfig(electrolyzer_type="alkaline")
        )
        self.assertNotAlmostEqual(pem, alkaline)


if __name__ == "__main__":
    unittest.main()
