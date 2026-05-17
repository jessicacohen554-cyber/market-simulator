"""Tests for fleet retirement mechanisms in ``market_sim.model.capacity``."""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.constants import (
    GAS_PRICE_BASE,
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HOURS_PER_YEAR,
    NEW_ENTRY_COSTS,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    CumulativeDeployment,
    _capital_recovery_factor,
    apply_economic_new_entry,
    apply_economic_retirements,
    apply_known_retirements,
    compute_clean_share,
    compute_lcoe,
    estimate_expected_revenue,
    evolve_fleet,
    wright_cost,
)
from market_sim.model.storage import compute_storage_annual_cost
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.constraints import get_active_policy_constraints
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
    """Revenue-driven retirement of persistently unprofitable thermal units.

    Economic retirement is now the sole retirement mechanism, with
    fuel-type-aware loss-year thresholds and fixed-cost multipliers, and a
    system-wide reliability floor.
    """

    T = 10

    def _dispatch_result(self, n_gen, level):
        """A dispatch stand-in with every generator producing ``level`` MW."""
        return SimpleNamespace(dispatch=np.full((n_gen, self.T), level))

    def test_coal_retires_after_one_unprofitable_year(self):
        # retirement_years_coal = 1, retirement_fom_multiplier_coal = 1.3.
        config = ScenarioConfig()
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # going_forward_cost = 40 * 1.3 * 100 * 1000 = 5_200_000.
        # net_revenue = 10 $/MWh * 10 MW * 10 h = 1_000 << cost.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 10.0)

        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        # A single unprofitable year is enough for coal.
        self.assertEqual(fleet1, [])
        self.assertNotIn("C0", losses1)

    def test_gas_cc_survives_two_unprofitable_years(self):
        # retirement_years_gas_cc = 3: two loss years are not enough.
        config = ScenarioConfig()
        fleet = [_gen("G0", "gas_cc", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # going_forward_cost = 12 * 1.0 * 100 * 1000 = 1_200_000.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 10.0)

        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        self.assertEqual([g.unit_id for g in fleet1], ["G0"])
        self.assertEqual(losses1["G0"], 1)

        fleet2, losses2 = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        # Two consecutive loss years -- still online (needs three).
        self.assertEqual([g.unit_id for g in fleet2], ["G0"])
        self.assertEqual(losses2["G0"], 2)

        fleet3, losses3 = apply_economic_retirements(
            fleet2, arrays, dispatch, prices, config, losses2, peak_demand=0.0
        )
        # Third consecutive loss year -- retired.
        self.assertEqual(fleet3, [])
        self.assertNotIn("G0", losses3)

    def test_gas_ct_retires_after_two_unprofitable_years(self):
        # retirement_years_gas_ct = 2.
        config = ScenarioConfig()
        fleet = [_gen("T0", "gas_ct", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # going_forward_cost = 8 * 1.0 * 100 * 1000 = 800_000.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 10.0)

        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        # First loss year: still online.
        self.assertEqual([g.unit_id for g in fleet1], ["T0"])
        self.assertEqual(losses1["T0"], 1)

        fleet2, losses2 = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        # Second consecutive loss year -- retired.
        self.assertEqual(fleet2, [])
        self.assertNotIn("T0", losses2)

    def test_coal_fom_multiplier_makes_marginal_coal_unprofitable(self):
        # net_revenue = 4500 $/MWh * 100 MW * 10 h = 4_500_000.
        # Base coal FOM cost = 40 * 100 * 1000 = 4_000_000 (revenue clears).
        # With the 1.3 multiplier = 5_200_000 (revenue falls short).
        config = ScenarioConfig()
        prices = np.full((1, self.T), 4500.0)
        dispatch = self._dispatch_result(1, 100.0)

        coal = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        fleet1, _ = apply_economic_retirements(
            coal, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        # The multiplier tips marginal coal into a loss -- retired in one year.
        self.assertEqual(fleet1, [])

        # The same revenue against a gas_cc (multiplier 1.0) stays profitable.
        gas = [_gen("G0", "gas_cc", pmax=100.0)]
        arrays_gas = generators_to_fleet_arrays(gas, ["Z0"], hours=self.T)
        fleet2, losses2 = apply_economic_retirements(
            gas, arrays_gas, dispatch, prices, config, {"G0": 2},
            peak_demand=0.0,
        )
        self.assertEqual([g.unit_id for g in fleet2], ["G0"])
        self.assertEqual(losses2["G0"], 0)

    def test_reliability_floor_prevents_over_retirement(self):
        # Peak demand 10000 MW, firm clean 2000 MW.
        # floor = (10000 - 2000) * 1.15 = 9200 MW of thermal must remain.
        config = ScenarioConfig()
        nuclear = [_gen("N0", "nuclear", pmax=2000.0)]
        # 12 coal units of 1000 MW, strictly increasing heat rate.
        coal = [
            _gen(f"C{i}", "coal", pmax=1000.0, heat_rate=9.0 + 0.1 * i)
            for i in range(12)
        ]
        fleet = nuclear + coal
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # Prices far too low: every coal unit is unprofitable.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(13, 10.0)

        survivors, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=10000.0
        )
        coal_survivors = [g for g in survivors if g.fuel_type == "coal"]
        # 10 coal units (10000 MW) kept to clear the 9200 MW floor.
        self.assertEqual(len(coal_survivors), 10)
        # The most efficient (lowest heat-rate) units are the ones kept.
        retired_hr = {
            g.heat_rate for g in coal
        } - {g.heat_rate for g in coal_survivors}
        survivor_hr = {g.heat_rate for g in coal_survivors}
        self.assertTrue(min(retired_hr) > max(survivor_hr))

    def test_highest_heat_rate_retires_first(self):
        # Reliability floor keeps the floor met; the least efficient units
        # are the ones actually retired.
        config = ScenarioConfig()
        coal = [
            _gen("C0", "coal", pmax=1000.0, heat_rate=9.0),
            _gen("C1", "coal", pmax=1000.0, heat_rate=10.0),
            _gen("C2", "coal", pmax=1000.0, heat_rate=11.0),
        ]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(3, 10.0)
        # floor = peak * 1.15; peak ~1739 -> floor ~2000, keeps 2 units.
        survivors, _ = apply_economic_retirements(
            coal, arrays, dispatch, prices, config, {}, peak_demand=1739.13
        )
        # The single highest-heat-rate unit is the one retired.
        self.assertEqual({g.unit_id for g in survivors}, {"C0", "C1"})

    def test_profitable_gen_resets_counter(self):
        config = ScenarioConfig()
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # net_revenue = 1e6 * 10 * 10 = 1e8, far above any fixed cost.
        prices = np.full((1, self.T), 1.0e6)
        dispatch = self._dispatch_result(1, 10.0)

        # Enter with one prior loss year on the books.
        fleet1, losses1 = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {"C0": 1}, peak_demand=0.0
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
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        self.assertEqual([g.unit_id for g in fleet1], ["W0"])
        self.assertEqual(losses1, {})


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

    def test_zero_renewable_cap_matches_fleet_only_share(self):
        # With no separately-tracked renewables, a pure-coal fleet is 0.0.
        coal = _gen("C0", "coal", pmax=100.0)
        self.assertEqual(compute_clean_share([coal]), 0.0)

    def test_renewable_cap_raises_share(self):
        # 100 MW coal + 1000 MW zonal renewables: clean share is the
        # renewable capacity over the combined total.
        coal = _gen("C0", "coal", pmax=100.0)
        share = compute_clean_share([coal], renewable_cap_mw=1000.0)
        self.assertAlmostEqual(share, 1000.0 / 1100.0)
        self.assertGreater(share, compute_clean_share([coal]))

    def test_renewable_cap_only_is_fully_clean(self):
        # An empty fleet whose only capacity is zonal renewables is 100% clean.
        self.assertAlmostEqual(
            compute_clean_share([], renewable_cap_mw=5000.0), 1.0
        )


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

    def test_learning_curve_lowers_wind_lcoe(self):
        # Cumulative deployment past the reference discounts wind capex,
        # and a lower capex flows through to a lower LCOE.
        config = ScenarioConfig()
        at_ref = compute_lcoe(
            "wind", 2030, config, cumulative_gw=WRIGHT_REFERENCE_GW["wind"]
        )
        grown = compute_lcoe(
            "wind", 2030, config, cumulative_gw=2 * WRIGHT_REFERENCE_GW["wind"]
        )
        self.assertLess(grown, at_ref)

    def test_learning_curve_applies_to_nuclear(self):
        # Nuclear is a candidate technology with its own reference capacity,
        # so the learning curve must work for it too.
        config = ScenarioConfig()
        at_ref = compute_lcoe(
            "nuclear", 2030, config,
            cumulative_gw=WRIGHT_REFERENCE_GW["nuclear"],
        )
        grown = compute_lcoe(
            "nuclear", 2030, config,
            cumulative_gw=2 * WRIGHT_REFERENCE_GW["nuclear"],
        )
        self.assertGreater(at_ref, 0.0)
        self.assertLess(grown, at_ref)

    def test_solar_itc_discounts_only_the_capital_component(self):
        # The IRA ITC reduces capex before annualization, so the credit
        # never discounts fixed O&M. The ITC-adjusted LCOE is therefore
        # higher than naively scaling the raw LCOE by (1 - itc).
        config = ScenarioConfig()  # ira_itc_solar = 0.30
        with_itc = compute_lcoe("solar", 2030, config)   # ITC active
        raw = compute_lcoe("solar", 2040, config)        # ITC expired
        self.assertLess(with_itc, raw)
        self.assertGreater(with_itc, raw * 0.70)

        # Verify the exact split: only capex * (1 - itc) is annualized.
        costs = NEW_ENTRY_COSTS["solar"]
        crf = _capital_recovery_factor(
            config.discount_rate, costs["lifetime_yr"]
        )
        gen_per_kw = HOURS_PER_YEAR * costs["base_cf"] / 1000.0
        expected = (
            costs["capex_per_kw"] * (1.0 - config.ira_itc_solar) * crf
            + costs["fom_per_kw_yr"]
        ) / gen_per_kw
        self.assertAlmostEqual(with_itc, expected)


class TestCumulativeDeployment(unittest.TestCase):
    """Global cumulative-deployment tracking for Wright's-Law learning."""

    def test_initial_starts_from_reference_capacities(self):
        cumulative = CumulativeDeployment.initial()
        for tech, gw in WRIGHT_REFERENCE_GW.items():
            self.assertAlmostEqual(cumulative.get(tech), gw)

    def test_advance_year_adds_global_deployment(self):
        cumulative = CumulativeDeployment.initial()
        cumulative.advance_year()
        for tech, annual_gw in GLOBAL_ANNUAL_DEPLOYMENT_GW.items():
            self.assertAlmostEqual(
                cumulative.get(tech),
                WRIGHT_REFERENCE_GW[tech] + annual_gw,
            )

    def test_advance_year_folds_in_local_builds(self):
        cumulative = CumulativeDeployment.initial()
        cumulative.advance_year({"wind": 10.0})
        self.assertAlmostEqual(
            cumulative.get("wind"),
            WRIGHT_REFERENCE_GW["wind"]
            + GLOBAL_ANNUAL_DEPLOYMENT_GW["wind"]
            + 10.0,
        )

    def test_get_untracked_technology_is_none(self):
        self.assertIsNone(CumulativeDeployment.initial().get("fusion"))


class TestStorageLearningCurve(unittest.TestCase):
    """Wright's-Law learning curves wired into storage costs."""

    def test_cumulative_deployment_lowers_storage_cost(self):
        config = ScenarioConfig()
        base = compute_storage_annual_cost("li_ion_4hr", 2030, config)
        learned = compute_storage_annual_cost(
            "li_ion_4hr", 2030, config,
            cumulative_gw=2 * WRIGHT_REFERENCE_GW["li_ion"],
        )
        self.assertLess(learned, base)

    def test_li_ion_8hr_shares_the_li_ion_learning_curve(self):
        # Both li-ion durations map to the "li_ion" reference key.
        config = ScenarioConfig()
        base = compute_storage_annual_cost("li_ion_8hr", 2030, config)
        learned = compute_storage_annual_cost(
            "li_ion_8hr", 2030, config,
            cumulative_gw=2 * WRIGHT_REFERENCE_GW["li_ion"],
        )
        self.assertLess(learned, base)


class TestIRACreditsToLCOE(unittest.TestCase):
    """IRA investment-credit adjustment to candidate LCOE."""

    def test_wind_ptc_subtracts_flat_amount(self):
        config = ScenarioConfig()  # ira_ptc_wind = 26.0
        adjusted = apply_ira_credits_to_lcoe("wind", 50.0, 2030, config)
        self.assertAlmostEqual(adjusted, 50.0 - 26.0)

    def test_solar_itc_not_applied_post_hoc(self):
        # The solar ITC is a capital credit: it is applied to capex inside
        # compute_lcoe, not as a post-hoc scaling of a finished LCOE (which
        # would wrongly discount the fixed-O&M component too).
        config = ScenarioConfig()  # ira_itc_solar = 0.30
        adjusted = apply_ira_credits_to_lcoe("solar", 50.0, 2030, config)
        self.assertEqual(adjusted, 50.0)

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


def _entry_by_tech(
    new_fleet: list, renewable_additions: dict[str, dict[str, float]]
) -> dict[str, float]:
    """Collapse a new-entry result into ``{fuel: total_mw}``.

    Thermal builds come from ``new_fleet`` Generators; wind and solar come
    from the ``renewable_additions`` dict, since they no longer enter as
    Generator objects.
    """
    by_tech: dict[str, float] = {}
    for g in new_fleet:
        by_tech[g.fuel_type] = by_tech.get(g.fuel_type, 0.0) + g.pmax_mw
    for by_fuel in renewable_additions.values():
        for fuel, mw in by_fuel.items():
            by_tech[fuel] = by_tech.get(fuel, 0.0) + mw
    return by_tech


class TestEconomicNewEntry(unittest.TestCase):
    """Revenue-driven capacity additions under per-tech and ISO queue caps."""

    def test_queue_cap_limits_annual_additions(self):
        # With every technology profitable, the ISO-level cap binds the
        # total while the per-tech caps bind each technology individually.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 250.0)  # high prices make entry profitable
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT"
        )

        by_tech = _entry_by_tech(new_fleet, additions)
        added_mw = sum(by_tech.values())
        # The ISO total cap (12 GW) binds: the per-tech caps sum to 13 GW.
        self.assertAlmostEqual(added_mw, QUEUE_CAP_GW["ERCOT"] * 1000.0)

        caps = QUEUE_CAP_PER_TECH_GW["ERCOT"]
        # No technology exceeds its own per-tech cap.
        for tech, built_mw in by_tech.items():
            self.assertLessEqual(built_mw, caps[tech] * 1000.0 + 1e-6)
        # gas_cc has the highest margin and wind the next, so both build
        # to their full per-tech caps; solar is squeezed by the ISO total.
        self.assertAlmostEqual(by_tech["gas_cc"], caps["gas_cc"] * 1000.0)
        self.assertAlmostEqual(by_tech["wind"], caps["wind"] * 1000.0)
        self.assertLess(by_tech["solar"], caps["solar"] * 1000.0)
        # Wind and solar are routed to the renewable pools, not the fleet.
        self.assertFalse(
            any(g.fuel_type in ("wind", "solar") for g in new_fleet)
        )

    def test_per_tech_cap_binds_below_iso_cap(self):
        # CAISO per-tech caps sum to 9 GW, above the 8 GW ISO cap, so at
        # least one per-tech cap binds before the ISO total is reached.
        config = ScenarioConfig(iso="CAISO")
        prices = np.full(8760, 250.0)
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "CAISO"
        )

        by_tech = _entry_by_tech(new_fleet, additions)
        caps = QUEUE_CAP_PER_TECH_GW["CAISO"]
        for tech, built_mw in by_tech.items():
            self.assertLessEqual(built_mw, caps[tech] * 1000.0 + 1e-6)
        total_mw = sum(by_tech.values())
        self.assertLessEqual(total_mw, QUEUE_CAP_GW["CAISO"] * 1000.0 + 1e-6)

    def test_no_entry_when_prices_too_low(self):
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 1.0)  # far below any technology's LCOE
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT"
        )
        self.assertEqual(new_fleet, [])
        self.assertEqual(additions, {})

    def test_gas_cc_charged_its_fuel_cost(self):
        # At a $40/MWh average price and $3.50/MMBtu gas, a gas CC's
        # expected variable fuel cost pushes its margin negative, so it
        # does not build. Ignoring fuel cost (the prior bug) would let it
        # build every year regardless of economics.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 40.0)

        priced, _ = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", gas_price_per_mmbtu=3.50
        )
        self.assertFalse(any(g.fuel_type == "gas_cc" for g in priced))

        # With fuel treated as free, the same screen builds gas CC.
        free, _ = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", gas_price_per_mmbtu=0.0
        )
        self.assertTrue(any(g.fuel_type == "gas_cc" for g in free))

    def test_nuclear_builds_only_when_prices_clear_capex(self):
        # Nuclear's ~$6800/kW capex needs high sustained prices to clear.
        config = ScenarioConfig(iso="ERCOT")

        high, _ = apply_economic_new_entry(
            [], np.full(8760, 250.0), 2030, config, "ERCOT"
        )
        nuclear = [g for g in high if g.fuel_type == "nuclear"]
        self.assertEqual(len(nuclear), 1)
        # A new nuclear unit is must-run, carbon-free and burns no fuel.
        self.assertTrue(nuclear[0].is_must_run)
        self.assertEqual(nuclear[0].heat_rate, 0.0)
        self.assertEqual(nuclear[0].emission_rate_co2, 0.0)

        low, _ = apply_economic_new_entry(
            [], np.full(8760, 40.0), 2030, config, "ERCOT"
        )
        self.assertFalse(any(g.fuel_type == "nuclear" for g in low))


class TestRenewableNewEntryRouting(unittest.TestCase):
    """New wind/solar route to the zonal capacity pools, not the fleet.

    Variable-output renewables must dispatch through the ``W[z,t]`` /
    ``S[z,t]`` LP variables (bounded by ``CF * capacity``). Adding them as
    thermal Generators with flat availability would let a new solar plant
    dispatch around the clock instead of following the solar curve.
    """

    def test_economic_wind_build_reported_in_additions(self):
        # High prices make wind economic: the build MW lands in the
        # renewable-additions dict and no wind Generator joins the fleet.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 250.0)
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT"
        )
        wind_mw = sum(by.get("wind", 0.0) for by in additions.values())
        self.assertGreater(wind_mw, 0.0)
        self.assertFalse(any(g.fuel_type == "wind" for g in new_fleet))
        # Wind is allocated to ERCOT's designated wind zone.
        self.assertIn("West", additions)
        self.assertGreater(additions["West"].get("wind", 0.0), 0.0)

    def test_solar_additions_increment_solar_cap(self):
        # Mirror the runner's fold: a 1000 MW solar build increments the
        # zonal solar_cap by exactly 1000 MW; no solar Generator is created.
        zone_names = _zone_names("ERCOT")
        solar_cap = np.zeros(len(zone_names))
        renewable_additions = {"South": {"solar": 1000.0}}
        for zone_name, additions in renewable_additions.items():
            z_idx = zone_names.index(zone_name)
            solar_cap[z_idx] += additions.get("solar", 0.0)
        self.assertAlmostEqual(solar_cap[zone_names.index("South")], 1000.0)
        self.assertAlmostEqual(solar_cap.sum(), 1000.0)

    def test_gas_cc_entry_stays_a_thermal_generator(self):
        # gas_cc new entry remains a Generator in the fleet and never
        # appears in the renewable-additions dict.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 250.0)
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT"
        )
        gas = [g for g in new_fleet if g.fuel_type == "gas_cc"]
        self.assertEqual(len(gas), 1)
        self.assertGreater(gas[0].pmax_mw, 0.0)
        for by_fuel in additions.values():
            self.assertNotIn("gas_cc", by_fuel)


class TestEstimateExpectedRevenue(unittest.TestCase):
    """Expected annual revenue per MW from prices and capacity factor."""

    def test_flat_capacity_factor(self):
        revenue = estimate_expected_revenue(np.full(10, 100.0), 0.5, hours=8760)
        self.assertAlmostEqual(revenue, 0.5 * 100.0 * 8760)

    def test_empty_prices_yield_zero(self):
        self.assertEqual(estimate_expected_revenue(np.array([]), 0.5), 0.0)


class TestRECPriceInNewEntry(unittest.TestCase):
    """The RPS shadow price raises clean-tech revenue in the entry screen."""

    def test_rec_price_makes_renewables_economic(self):
        # Prices too low for any technology to clear its LCOE on energy
        # revenue alone: with no REC price, nothing is built.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 1.0)

        _, no_rec = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", rec_price=0.0
        )
        without = sum(
            mw for by_fuel in no_rec.values() for mw in by_fuel.values()
        )
        self.assertEqual(without, 0.0)

        # A REC price lifts wind and solar over the LCOE hurdle: the RPS
        # shadow price is added to their effective renewable revenue.
        _, with_rec = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", rec_price=500.0
        )
        with_rec_mw = sum(
            mw for by_fuel in with_rec.values() for mw in by_fuel.values()
        )
        self.assertGreater(with_rec_mw, without)

    def test_rec_price_lifts_renewable_margin_monotonically(self):
        # A higher REC price never builds less renewable capacity.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 1.0)
        builds = []
        for rec_price in (0.0, 100.0, 300.0):
            _, additions = apply_economic_new_entry(
                [], prices, 2030, config, "ERCOT", rec_price=rec_price
            )
            builds.append(
                sum(mw for by in additions.values() for mw in by.values())
            )
        self.assertLessEqual(builds[0], builds[1])
        self.assertLessEqual(builds[1], builds[2])


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
        fleet, tracker, _ = evolve_fleet(
            [old], prior, 2030, config, {}
        )
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
        fleet, tracker, _ = evolve_fleet(
            [coal], prior, 2031, config, {"C0": 1}
        )
        self.assertEqual(fleet, [])
        self.assertNotIn("C0", tracker)

    def test_returns_fleet_tracker_and_additions_tuple(self):
        config = ScenarioConfig(iso="ERCOT")
        result = evolve_fleet(
            [_gen("G0", "gas_cc")], None, 2030, config, {}
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], dict)
        # The third element is the {zone: {fuel: mw}} renewable additions.
        self.assertIsInstance(result[2], dict)


class TestResolveCarbonPrice(unittest.TestCase):
    """Carbon-price resolution: flat trajectory vs interpolated path."""

    def test_nonzero_flat_price_returned_directly(self):
        config = ScenarioConfig(carbon_price=42.0)
        # A flat price is returned unchanged for any year.
        self.assertEqual(resolve_carbon_price(config, 2026), 42.0)
        self.assertEqual(resolve_carbon_price(config, 2050), 42.0)

    def test_zero_price_interpolates_named_path(self):
        # carbon_price 0 + carbon_price_path "mid" -> CARBON_PRICE_PATHS["mid"].
        config = ScenarioConfig(carbon_price=0.0, carbon_price_path="mid")
        # 2030 is a knot year of the mid path.
        self.assertAlmostEqual(resolve_carbon_price(config, 2030), 15.0)
        # 2028 sits midway between 2026 (0) and 2030 (15).
        self.assertAlmostEqual(resolve_carbon_price(config, 2028), 7.5)
        # mid path interpolates to $50/tCO2 by 2050.
        self.assertAlmostEqual(resolve_carbon_price(config, 2050), 50.0)

    def test_zero_price_path_yields_zero(self):
        config = ScenarioConfig(carbon_price=0.0, carbon_price_path="zero")
        self.assertEqual(resolve_carbon_price(config, 2040), 0.0)

    def test_default_config_yields_zero_for_all_years(self):
        # Default config has carbon_price_path="zero": no carbon price.
        config = ScenarioConfig()
        for year in (2026, 2030, 2040, 2050):
            self.assertEqual(resolve_carbon_price(config, year), 0.0)

    def test_carbon_price_decoupled_from_gas_price_path(self):
        # gas_price_path no longer drives carbon price; only carbon_price_path does.
        config = ScenarioConfig(carbon_price=0.0, gas_price_path="mid")
        for year in (2026, 2030, 2040, 2050):
            self.assertEqual(resolve_carbon_price(config, year), 0.0)

    def test_explicit_price_overrides_path(self):
        # An explicit carbon_price is returned regardless of carbon_price_path.
        config = ScenarioConfig(carbon_price=25.0, carbon_price_path="mid")
        self.assertEqual(resolve_carbon_price(config, 2026), 25.0)
        self.assertEqual(resolve_carbon_price(config, 2050), 25.0)

    def test_unrecognized_path_yields_zero(self):
        # A carbon_price_path that is not a named carbon path -> 0.0.
        config = ScenarioConfig(carbon_price=0.0, carbon_price_path="bogus")
        self.assertEqual(resolve_carbon_price(config, 2030), 0.0)

    def test_years_outside_knot_range_clamp(self):
        config = ScenarioConfig(carbon_price=0.0, carbon_price_path="high")
        # Before the first knot takes the first value, after the last the last.
        self.assertAlmostEqual(resolve_carbon_price(config, 2000), 0.0)
        self.assertAlmostEqual(resolve_carbon_price(config, 2100), 110.0)


class TestPolicyConstraints(unittest.TestCase):
    """The constraint-policy extension point."""

    def test_returns_empty_list(self):
        config = ScenarioConfig()
        constraints = get_active_policy_constraints(config, 2030)
        self.assertEqual(constraints, [])
        self.assertIsInstance(constraints, list)


# --- Integration-test helpers ---------------------------------------------

def _zone_names(iso="ERCOT"):
    """Return the zone names of an ISO."""
    return get_iso_config(iso).zone_names


def _make_prior(fleet, zone_names, price=15.0, gas_cf=0.3, other_cf=0.5, T=8760):
    """Build a prior-year ``prior_results`` stand-in for ``evolve_fleet``.

    Thermal gas units are dispatched at ``gas_cf`` of capacity, everything
    else at ``other_cf``; the zonal price is flat at ``price``.
    """
    arrays = generators_to_fleet_arrays(fleet, zone_names, hours=T)
    dispatch = np.zeros((len(fleet), T))
    for i, g in enumerate(fleet):
        cf = gas_cf if g.fuel_type.startswith("gas") else other_cf
        dispatch[i] = g.pmax_mw * cf
    prices = np.full((len(zone_names), T), price)
    return SimpleNamespace(
        fleet_arrays=arrays,
        dispatch_result=SimpleNamespace(dispatch=dispatch),
        prices=prices,
        planned_additions=[],
    )


class TestEvolveFleetEdgeCases(unittest.TestCase):
    """Boundary conditions of the year-step orchestration."""

    def test_first_year_with_no_prior_results(self):
        # Year 2026, prior_results=None: only known retirements and known
        # additions run -- the price-driven steps are skipped, and the RPS
        # is no longer a force-build step.
        config = ScenarioConfig(iso="CAISO")
        coal = [
            _gen(f"C{i}", "coal", pmax=1000.0, heat_rate=9.0 + 0.2 * i)
            for i in range(5)
        ]
        retiring = _gen("C_RET", "coal", pmax=1000.0, heat_rate=8.0,
                        retirement_year=2026)
        fleet, tracker, additions = evolve_fleet(
            coal + [retiring], None, 2026, config, {}
        )

        self.assertIsInstance(fleet, list)
        self.assertIsInstance(tracker, dict)
        # The scheduled retirement is gone; the rest of the fleet remains.
        self.assertNotIn("C_RET", {g.unit_id for g in fleet})
        # The five surviving coal units share a bin and zone, so they
        # collapse into one representative unit carrying the group capacity.
        self.assertEqual({g.unit_id for g in fleet}, {"coal_default_Z0"})
        self.assertEqual(sum(g.pmax_mw for g in fleet), 5000.0)
        # No price signal yet, so economic new entry does not run.
        self.assertEqual(additions, {})

    def test_empty_fleet_after_retirements_is_refilled(self):
        # The whole fleet retires on schedule; new entry fills the gap.
        config = ScenarioConfig(iso="ERCOT")
        coal = _gen("C0", "coal", pmax=100.0, zone="North",
                    retirement_year=2027)
        prior = _make_prior([coal], _zone_names(), price=60.0)
        fleet, tracker, _ = evolve_fleet(
            [coal], prior, 2027, config, {}
        )

        # Known retirement empties the fleet, then economic new entry refills.
        self.assertNotIn("C0", {g.unit_id for g in fleet})
        self.assertGreater(len(fleet), 0)
        self.assertGreater(sum(g.pmax_mw for g in fleet), 0.0)


class TestCapacityIntegration(unittest.TestCase):
    """Multi-year fleet-evolution trajectories across the four mechanisms."""

    def test_three_year_trajectory_changes_each_year(self):
        # A small fleet evolved 2026-2028: composition shifts every year as
        # retirements and new entry reshape it. C_RET retires on schedule in
        # the first year, guaranteeing the year-one fleet differs.
        config = ScenarioConfig(iso="ERCOT")
        fleet = [
            _gen("C0", "coal", pmax=100.0, zone="North", heat_rate=10.0),
            _gen("C1", "coal", pmax=100.0, zone="North", heat_rate=10.5),
            _gen("G0", "gas_cc", pmax=100.0, zone="North", heat_rate=7.0),
            _gen("W0", "wind", pmax=100.0, zone="North"),
            _gen("W1", "wind", pmax=100.0, zone="North"),
            _gen("C_RET", "coal", pmax=100.0, zone="North", heat_rate=9.0,
                 retirement_year=2026),
        ]
        snapshots = [frozenset(g.unit_id for g in fleet)]
        tracker: dict[str, int] = {}
        prior = None
        for year in (2026, 2027, 2028):
            fleet, tracker, _ = evolve_fleet(
                fleet, prior, year, config, tracker
            )
            snapshots.append(frozenset(g.unit_id for g in fleet))
            prior = _make_prior(fleet, _zone_names(), price=10.0)

        # The fleet ends up different from where it started, and at least one
        # intermediate year shifts the composition.
        self.assertNotEqual(snapshots[0], snapshots[-1])
        self.assertTrue(any(s != snapshots[0] for s in snapshots[1:]))

    def test_gas_price_path_diverges_fleet_by_year_three(self):
        # Two scenarios identical but for gas_price_path. Higher gas prices
        # depress gas-plant revenue, so gas units retire economically and
        # the fleets diverge.
        def _fleet():
            # gas_ct peakers run at a thin, marginally profitable margin --
            # depressed revenue tips them into economic retirement.
            gas = [
                _gen(f"G{i}", "gas_ct", pmax=100.0, zone="North",
                     heat_rate=6.5 + 0.05 * i)
                for i in range(20)
            ]
            wind = [
                _gen(f"W{i}", "wind", pmax=100.0, zone="North")
                for i in range(4)
            ]
            return gas + wind

        def _run(gas_price_path):
            config = ScenarioConfig(iso="ERCOT", gas_price_path=gas_price_path)
            gas_price = GAS_PRICE_BASE["ERCOT"][gas_price_path]
            gas_cf = max(0.02, 0.6 - 0.1 * gas_price)
            fleet = _fleet()
            tracker: dict[str, int] = {}
            prior = None
            yearly = {}
            for year in (2026, 2027, 2028):
                fleet, tracker, _ = evolve_fleet(
                    fleet, prior, year, config, tracker
                )
                yearly[year] = fleet
                prior = _make_prior(
                    fleet, _zone_names(), price=15.0, gas_cf=gas_cf
                )
            return yearly

        low = _run("low")
        high = _run("high")

        def _gas(fleet):
            return sum(1 for g in fleet if g.fuel_type == "gas_ct")

        # Year 1 (2026, no prior results): the fleets are identical.
        self.assertEqual(
            {g.unit_id for g in low[2026]},
            {g.unit_id for g in high[2026]},
        )
        # By year 3 the high-gas scenario has shed its gas fleet
        # economically while the low-gas scenario retains it.
        self.assertGreater(_gas(low[2028]), _gas(high[2028]))
        self.assertNotEqual(
            {g.unit_id for g in low[2028]},
            {g.unit_id for g in high[2028]},
        )

    def test_scheduled_coal_retirement_across_trajectory(self):
        # A coal unit with retirement_year=2027 is present in 2026, gone after.
        config = ScenarioConfig(iso="ERCOT")
        fleet = [
            _gen("C_RET", "coal", pmax=100.0, zone="North", heat_rate=8.0,
                 retirement_year=2027),
            _gen("C_A", "coal", pmax=100.0, zone="North", heat_rate=11.0),
            _gen("C_B", "coal", pmax=100.0, zone="North", heat_rate=10.5),
            _gen("W0", "wind", pmax=100.0, zone="North"),
            _gen("W1", "wind", pmax=100.0, zone="North"),
        ]
        tracker: dict[str, int] = {}

        fleet, tracker, _ = evolve_fleet(
            fleet, None, 2026, config, tracker
        )
        self.assertIn("C_RET", {g.unit_id for g in fleet})

        fleet, tracker, _ = evolve_fleet(
            fleet, None, 2027, config, tracker
        )
        self.assertNotIn("C_RET", {g.unit_id for g in fleet})

    def test_fleet_capacity_never_zero_over_five_years(self):
        # New entry keeps the fleet alive even as retirements bite.
        config = ScenarioConfig(iso="ERCOT")
        fleet = [
            _gen("W0", "wind", pmax=100.0, zone="North"),
            _gen("W1", "wind", pmax=100.0, zone="North"),
            _gen("G0", "gas_cc", pmax=100.0, zone="North", heat_rate=7.0),
            _gen("G1", "gas_cc", pmax=100.0, zone="North", heat_rate=7.2),
        ]
        tracker: dict[str, int] = {}
        prior = None
        for year in range(2026, 2031):
            fleet, tracker, _ = evolve_fleet(
                fleet, prior, year, config, tracker
            )
            self.assertGreater(
                sum(g.pmax_mw for g in fleet), 0.0,
                f"fleet capacity hit zero in {year}",
            )
            prior = _make_prior(fleet, _zone_names(), price=60.0)

    def test_per_tech_queue_cap_builds_both_wind_and_solar(self):
        # With wind and solar both profitable, both are built and neither
        # exceeds its per-technology queue cap. Wind and solar are routed
        # to the renewable pools rather than the thermal fleet.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 250.0)
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT"
        )

        by_tech = _entry_by_tech(new_fleet, additions)
        caps = QUEUE_CAP_PER_TECH_GW["ERCOT"]

        # Both wind and solar entered.
        self.assertGreater(by_tech.get("wind", 0.0), 0.0)
        self.assertGreater(by_tech.get("solar", 0.0), 0.0)
        # Neither leaked into the thermal fleet as a Generator.
        self.assertFalse(
            any(g.fuel_type in ("wind", "solar") for g in new_fleet)
        )
        # Neither exceeds its per-tech cap.
        self.assertLessEqual(by_tech["wind"], caps["wind"] * 1000.0 + 1e-6)
        self.assertLessEqual(by_tech["solar"], caps["solar"] * 1000.0 + 1e-6)
        # The ISO-level cap still binds the total.
        self.assertLessEqual(
            sum(by_tech.values()), QUEUE_CAP_GW["ERCOT"] * 1000.0 + 1e-6
        )

    def test_renewable_capacity_grows_over_multi_year_run(self):
        # Over a five-year trajectory with economic entry profitable, the
        # accumulated wind + solar capacity is strictly higher by year five
        # than after year one. Mirrors how the runner folds each year's
        # renewable_additions into the zonal wind_cap/solar_cap pools.
        config = ScenarioConfig(iso="ERCOT")
        fleet = [_gen("G0", "gas_cc", pmax=1000.0, zone="North", heat_rate=7.0)]
        tracker: dict[str, int] = {}
        prior = None
        cumulative_renewable_mw = 0.0
        yearly_cap: dict[int, float] = {}
        for year in range(2026, 2031):
            fleet, tracker, additions = evolve_fleet(
                fleet, prior, year, config, tracker
            )
            for by_fuel in additions.values():
                cumulative_renewable_mw += sum(by_fuel.values())
            yearly_cap[year] = cumulative_renewable_mw
            prior = _make_prior(fleet, _zone_names(), price=250.0)

        # Year one (2026) has no prior results, so no economic entry runs;
        # later years accumulate profitable wind/solar builds.
        self.assertGreater(yearly_cap[2030], yearly_cap[2026])
        self.assertGreater(yearly_cap[2030], 0.0)


if __name__ == "__main__":
    unittest.main()
