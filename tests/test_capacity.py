"""Tests for fleet retirement mechanisms in ``market_sim.model.capacity``."""

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from market_sim.config.constants import (
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HOURS_PER_YEAR,
    NEW_ENTRY_COSTS,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.confirmed_retirements import ConfirmedExit
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    CumulativeDeployment,
    _capital_recovery_factor,
    apply_announced_retirements,
    apply_confirmed_exits,
    apply_economic_new_entry,
    apply_economic_retirements,
    compute_clean_share,
    compute_lcoe,
    estimate_expected_revenue,
    evolve_fleet,
    wright_cost,
)
from market_sim.model.storage import compute_storage_annual_cost
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.constraints import get_active_policy_constraints
from market_sim.policy.ira import apply_ira_credits_to_lcoe, ira_phaseout_fraction
from market_sim.policy.rps import get_rps_target


def _gen(
    unit_id,
    fuel_type,
    pmax=100.0,
    heat_rate=10.0,
    zone="Z0",
    retirement_year=None,
    **kwargs,
):
    """Build a Generator with the attributes the retirement logic reads."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone=zone,
        fuel_type=fuel_type,
        pmax_mw=pmax,
        heat_rate=heat_rate,
        retirement_year=retirement_year,
        **kwargs,
    )


class TestAnnouncedRetirements(unittest.TestCase):
    """Announced (EIA-860 date) retirement removal by simulation year."""

    def test_unit_present_before_retirement_year(self):
        # Year < retirement_year keeps the unit regardless of fuel.
        fleet = [_gen("N0", "nuclear", retirement_year=2028)]
        survivors = apply_announced_retirements(fleet, 2027)
        self.assertEqual([g.unit_id for g in survivors], ["N0"])

    def test_reversed_plant_keeps_announced_unit(self):
        # Retirement-reversal supersession (capacity-economics Stage 2 /
        # confirmed-retirement plan §2.2 counter-instruments): a plant whose
        # announced exit was reversed by a public instrument (Byron/Dresden's
        # 2021 dates reversed by IL CEJA) keeps running — the stale vintage
        # date is ignored — while an identical twin without a reversal row
        # is still honored.
        reversed_n = _gen("N0", "nuclear", retirement_year=2021, plant_code=6023)
        twin = _gen("N1", "nuclear", retirement_year=2021, plant_code=7777)
        survivors = apply_announced_retirements(
            [reversed_n, twin],
            2022,
            reversed_plant_codes=frozenset({6023}),
        )
        self.assertEqual([g.unit_id for g in survivors], ["N0"])

    def test_reversal_flows_through_evolve_fleet(self):
        # evolve_fleet step 1 passes announced_reversal_plants through to the
        # announced channel.
        fleet = [_gen("N0", "nuclear", retirement_year=2021, plant_code=6023)]
        kept, _, _, _, _ = evolve_fleet(
            fleet,
            None,
            2022,
            ScenarioConfig(),
            {},
            announced_reversal_plants=frozenset({6023}),
        )
        self.assertEqual([g.unit_id for g in kept], ["N0"])
        gone, _, _, _, _ = evolve_fleet(fleet, None, 2022, ScenarioConfig(), {})
        self.assertEqual(gone, [])

    def test_nonfossil_unit_removed_at_retirement_year(self):
        # Non-fossil (nuclear/hydro/renewables) honor the announced EIA-860 date.
        fleet = [_gen("N0", "nuclear", retirement_year=2028)]
        survivors = apply_announced_retirements(fleet, 2028)
        self.assertEqual(survivors, [])

    def test_nonfossil_unit_removed_after_retirement_year(self):
        fleet = [_gen("N0", "nuclear", retirement_year=2028)]
        survivors = apply_announced_retirements(fleet, 2030)
        self.assertEqual(survivors, [])

    def test_fossil_unit_exempt_from_date_retirement_by_default(self):
        # Fossil phaseout is economic (forecast_fossil_retirement_economic=True
        # default): an announced coal/gas/oil retirement date does NOT remove it;
        # the economic-retirement screen governs the exit instead (default no-op).
        fleet = [_gen("C0", "coal", retirement_year=2028)]
        self.assertEqual(
            [g.unit_id for g in apply_announced_retirements(fleet, 2030)], ["C0"]
        )
        # Legacy behaviour (fossil_economic=False) honors the date.
        self.assertEqual(
            apply_announced_retirements(fleet, 2030, fossil_economic=False), []
        )

    def test_unit_without_schedule_is_kept(self):
        fleet = [_gen("G0", "gas_cc", retirement_year=None)]
        survivors = apply_announced_retirements(fleet, 2050)
        self.assertEqual([g.unit_id for g in survivors], ["G0"])

    def test_old_name_is_gone(self):
        # RC-3 rename: no alias left behind (deleted means deleted, rule 26).
        import market_sim.model.capacity as cap

        self.assertFalse(hasattr(cap, "apply_known_retirements"))


class TestNonFossilHorizonGate(unittest.TestCase):
    """RC-5: announced non-fossil dates gated to the EIA-860 data horizon."""

    # Vintage + horizon: with vintage 2025 and horizon 5, the last honored
    # announced non-fossil year is 2030; 2031+ is speculative unless confirmed.
    VINTAGE = 2025
    HORIZON = 5

    def _gate(self, fleet, year, confirmed=frozenset()):
        return apply_announced_retirements(
            fleet,
            year,
            vintage=self.VINTAGE,
            horizon_years=self.HORIZON,
            confirmed_plant_codes=confirmed,
        )

    def test_within_horizon_honored(self):
        # 2030 == vintage + horizon: still honored.
        fleet = [_gen("N0", "nuclear", retirement_year=2030)]
        self.assertEqual(self._gate(fleet, 2030), [])

    def test_beyond_horizon_ignored(self):
        # 2031 > vintage + horizon and not confirmed: announced date ignored,
        # unit stays (falls to the economic screen).
        fleet = [_gen("H0", "hydro", retirement_year=2031)]
        self.assertEqual([g.unit_id for g in self._gate(fleet, 2035)], ["H0"])

    def test_beyond_horizon_but_confirmed_honored(self):
        # 2031 beyond horizon but the plant carries a binding instrument.
        g = Generator(
            unit_id="9001_1",
            name="stat-hydro",
            zone="Z0",
            fuel_type="hydro",
            pmax_mw=100.0,
            retirement_year=2031,
            plant_code=9001,
        )
        self.assertEqual(self._gate([g], 2035, confirmed=frozenset({9001})), [])

    def test_no_gate_when_horizon_none(self):
        # horizon_years=None (legacy / channel-off) honors every non-fossil date.
        fleet = [_gen("H0", "hydro", retirement_year=2065)]
        self.assertEqual(apply_announced_retirements(fleet, 2065), [])


def _binned(unit_id, plant_code, pmax, pmin=0.0, nameplate=0.0, fuel="coal"):
    """A plant-binned CAMPD tranche Generator (is_campd_bin=True)."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="Z0",
        fuel_type=fuel,
        pmax_mw=pmax,
        pmin_mw=pmin,
        is_campd_bin=True,
        plant_group="COAL",
        plant_code=plant_code,
        bin_nameplate_mw=nameplate,
    )


def _unit(plant_code, generator_id, pmax, fuel="coal", retirement_year=None):
    """A unit-grain EIA-860 Generator (unit_id = '{plant_code}_{generator_id}')."""
    return Generator(
        unit_id=f"{plant_code}_{generator_id}",
        name=f"{plant_code}_{generator_id}",
        zone="Z0",
        fuel_type=fuel,
        pmax_mw=pmax,
        plant_code=plant_code,
        retirement_year=retirement_year,
    )


class TestConfirmedExits(unittest.TestCase):
    """Confirmed (binding-instrument) exit injector."""

    def _exit(self, plant_id, gen_id, year, month=None, mw=None):
        return ConfirmedExit(
            plant_id=plant_id,
            generator_id=gen_id,
            exit_year=year,
            exit_month=month,
            mw=mw,
        )

    def test_unit_grain_drop_at_exit_year(self):
        fleet = [_unit(100, "1", 200.0), _unit(100, "2", 200.0)]
        exits = [self._exit(100, "1", 2028, mw=200.0)]
        # Before the exit year: both present.
        keep_before = apply_confirmed_exits(fleet, 2027, exits)
        self.assertEqual({g.unit_id for g in keep_before}, {"100_1", "100_2"})
        # At the exit year: only the confirmed unit is dropped.
        keep = apply_confirmed_exits(fleet, 2028, exits)
        self.assertEqual([g.unit_id for g in keep], ["100_2"])

    def test_plant_bin_derate_math(self):
        # A 1000 MW plant in two bins; a 400 MW unit exits -> factor 0.6.
        fleet = [
            _binned("H_CC1", 200, 600.0, pmin=120.0, nameplate=600.0),
            _binned("H_CC2", 200, 400.0, pmin=80.0, nameplate=400.0),
        ]
        exits = [self._exit(200, "U1", 2028, mw=400.0)]
        keep = apply_confirmed_exits(fleet, 2028, exits)
        total = sum(g.pmax_mw for g in keep)
        self.assertAlmostEqual(total, 600.0, places=4)  # 1000 - 400
        for g in keep:
            self.assertAlmostEqual(
                g.pmax_mw, {"H_CC1": 360.0, "H_CC2": 240.0}[g.unit_id]
            )
            # pmin and bin nameplate scale by the same factor.
            self.assertAlmostEqual(g.pmin_mw / g.pmax_mw, 0.2, places=4)
            self.assertAlmostEqual(g.bin_nameplate_mw, g.pmax_mw, places=4)

    def test_plant_bin_full_derate_drops_tranche(self):
        # Exit MW >= plant MW -> factor 0 -> all bins dropped.
        fleet = [_binned("H_CC1", 200, 300.0), _binned("H_CC2", 200, 200.0)]
        exits = [self._exit(200, "U1", 2028, mw=500.0)]
        self.assertEqual(apply_confirmed_exits(fleet, 2028, exits), [])

    def test_confirmed_fossil_forced_out_while_announced_twin_survives(self):
        # RC-1: a confirmed fossil unit exits; an identical announced-only fossil
        # twin (no confirmed row) survives the confirmed step.
        confirmed = _unit(300, "1", 500.0, fuel="coal")
        announced_twin = _unit(301, "1", 500.0, fuel="coal", retirement_year=2028)
        fleet = [confirmed, announced_twin]
        exits = [self._exit(300, "1", 2028, mw=500.0)]
        keep = apply_confirmed_exits(fleet, 2028, exits)
        self.assertEqual([g.unit_id for g in keep], ["301_1"])
        # And the announced-only fossil twin stays with the economic screen: the
        # announced step is a default no-op for fossil.
        after_announced = apply_announced_retirements(keep, 2028)
        self.assertEqual([g.unit_id for g in after_announced], ["301_1"])

    def test_exit_month_first_half_vs_second_half(self):
        early = [_unit(400, "1", 100.0)]
        late = [_unit(401, "1", 100.0)]
        # month <= 6 -> effective in exit_year; month > 6 -> exit_year + 1.
        self.assertEqual(
            apply_confirmed_exits(early, 2028, [self._exit(400, "1", 2028, month=3)]),
            [],
        )
        keep_late = apply_confirmed_exits(
            late, 2028, [self._exit(401, "1", 2028, month=9)]
        )
        self.assertEqual([g.unit_id for g in keep_late], ["401_1"])
        # The next year the late exit takes effect.
        self.assertEqual(
            apply_confirmed_exits(late, 2029, [self._exit(401, "1", 2028, month=9)]),
            [],
        )

    def test_reliability_floor_cannot_rescue_confirmed_exit(self):
        # apply_confirmed_exits removes the unit outright, before the economic
        # screen (which houses the reliability floor) ever runs — so no floor can
        # keep it. Verified structurally: the unit is gone from the returned fleet.
        fleet = [_unit(500, "1", 900.0, fuel="coal")]
        keep = apply_confirmed_exits(
            fleet, 2028, [self._exit(500, "1", 2028, mw=900.0)]
        )
        self.assertEqual(keep, [])

    def test_no_effective_exit_is_noop(self):
        fleet = [_unit(600, "1", 100.0)]
        # Exit year in the future -> byte-identical fleet.
        out = apply_confirmed_exits(fleet, 2027, [self._exit(600, "1", 2030, mw=100.0)])
        self.assertEqual([g.unit_id for g in out], ["600_1"])
        self.assertEqual(out[0].pmax_mw, 100.0)


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

        fleet1, losses1, _ = apply_economic_retirements(
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

        fleet1, losses1, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        self.assertEqual([g.unit_id for g in fleet1], ["G0"])
        self.assertEqual(losses1["G0"], 1)

        fleet2, losses2, _ = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        # Two consecutive loss years -- still online (needs three).
        self.assertEqual([g.unit_id for g in fleet2], ["G0"])
        self.assertEqual(losses2["G0"], 2)

        fleet3, losses3, _ = apply_economic_retirements(
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

        fleet1, losses1, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        # First loss year: still online.
        self.assertEqual([g.unit_id for g in fleet1], ["T0"])
        self.assertEqual(losses1["T0"], 1)

        fleet2, losses2, _ = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        # Second consecutive loss year -- retired.
        self.assertEqual(fleet2, [])
        self.assertNotIn("T0", losses2)

    def test_gas_st_is_screened_and_retires_after_two_loss_years(self):
        # Regression: legacy gas steam (gas_st) used to be absent from the
        # retirement screen entirely (not gas_cc/gas_ct/coal), so it could
        # never retire on economics regardless of revenue. It is now screened
        # with retirement_years_gas_st = 2 and fixed_om_gas_st = 35 $/kW-yr.
        config = ScenarioConfig()
        fleet = [_gen("S0", "gas_st", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # going_forward_cost = 35 * 1.0 * 100 * 1000 = 3_500_000.
        # net_revenue = 10 $/MWh * 10 MW * 10 h = 1_000 << cost.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 10.0)

        fleet1, losses1, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        # First loss year: screened (counter increments), still online.
        self.assertEqual([g.unit_id for g in fleet1], ["S0"])
        self.assertEqual(losses1["S0"], 1)

        fleet2, losses2, _ = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        # Second consecutive loss year -- retired (was previously immortal).
        self.assertEqual(fleet2, [])
        self.assertNotIn("S0", losses2)

    def test_gas_st_kept_when_a_stress_year_clears_its_fixed_cost(self):
        # A stress-year price (the scarcity-rich case the reliability-
        # deployment overlay restores) clears the going-forward bar, so the
        # loss counter resets and the steam unit is kept.
        config = ScenarioConfig()
        # eford=0 so available capacity is the full 100 MW: the screen's
        # margin basis is the attainable pro-forma max(0, price - mc) x
        # pmax x availability (capacity-economics plan 2026-07 §5 step 2),
        # not realized dispatch, so the hand math below needs avail = 1.
        fleet = [_gen("S0", "gas_st", pmax=100.0, eford=0.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # margin/h = (3550 - 50) * 100 = 350_000; over 10 h = 3_500_000,
        # exactly the going-forward cost -> not a loss year.
        prices = np.full((1, self.T), 3550.0)
        mc = np.full((1, self.T), 50.0)
        dispatch = self._dispatch_result(1, 100.0)
        fleet1, losses1, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {"S0": 1},
            peak_demand=0.0,
            mc=mc,
        )
        self.assertEqual([g.unit_id for g in fleet1], ["S0"])
        self.assertEqual(losses1["S0"], 0)

    def test_every_fossil_class_and_nuclear_is_retirement_eligible(self):
        # Regression: oil, gas_cc_ccs and nuclear were not screened; now every
        # fossil class and nuclear can retire on economics. A deeply
        # unprofitable unit of each accumulates a loss year (is screened).
        from market_sim.model.capacity import _THERMAL_FOM

        for fuel in (
            "coal",
            "gas_cc",
            "gas_ct",
            "gas_st",
            "gas_cc_ccs",
            "oil",
            "nuclear",
        ):
            self.assertIn(fuel, _THERMAL_FOM, fuel)
        config = ScenarioConfig()
        for fuel in ("oil", "nuclear", "gas_cc_ccs"):
            fleet = [_gen("U0", fuel, pmax=100.0)]
            arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
            prices = np.full((1, self.T), 1.0)  # far below any fixed cost
            dispatch = self._dispatch_result(1, 1.0)
            _, losses, _ = apply_economic_retirements(
                fleet,
                arrays,
                dispatch,
                prices,
                config,
                {},
                peak_demand=0.0,
                mc=np.zeros((1, self.T)),
            )
            self.assertEqual(losses.get("U0"), 1, f"{fuel} not screened")

    def test_coal_fom_multiplier_makes_marginal_coal_unprofitable(self):
        # net_revenue = 4500 $/MWh * 100 MW * 10 h = 4_500_000.
        # Base coal FOM cost = 40 * 100 * 1000 = 4_000_000 (revenue clears).
        # With the 1.3 multiplier = 5_200_000 (revenue falls short).
        config = ScenarioConfig()
        prices = np.full((1, self.T), 4500.0)
        dispatch = self._dispatch_result(1, 100.0)

        coal = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        fleet1, _, _ = apply_economic_retirements(
            coal, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        # The multiplier tips marginal coal into a loss -- retired in one year.
        self.assertEqual(fleet1, [])

        # The same revenue against a gas_cc (multiplier 1.0) stays profitable.
        gas = [_gen("G0", "gas_cc", pmax=100.0)]
        arrays_gas = generators_to_fleet_arrays(gas, ["Z0"], hours=self.T)
        fleet2, losses2, _ = apply_economic_retirements(
            gas,
            arrays_gas,
            dispatch,
            prices,
            config,
            {"G0": 2},
            peak_demand=0.0,
        )
        self.assertEqual([g.unit_id for g in fleet2], ["G0"])
        self.assertEqual(losses2["G0"], 0)

    def test_reliability_floor_prevents_over_retirement(self):
        # Accredited-basis floor (plan §3.2): requirement =
        # peak x (1 + PRM_ERCOT) = 10000 x 1.1375 = 11375 MW of accredited
        # firm capacity must remain. Nuclear survives the screen (loss year
        # 1 < threshold 3) and contributes 2000 x 0.95 = 1900 MW UCAP; each
        # coal unit contributes 1000 x 0.95 = 950 MW UCAP, so 10 of 12 coal
        # units must be retained (1900 + 10 x 950 = 11400 >= 11375).
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

        survivors, _, retention_log = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=10000.0
        )
        coal_survivors = [g for g in survivors if g.fuel_type == "coal"]
        self.assertEqual(len(coal_survivors), 10)
        # Same-fuel merit ties break on heat rate: the most efficient
        # (lowest heat-rate) units are the ones kept.
        retired_hr = {g.heat_rate for g in coal} - {g.heat_rate for g in coal_survivors}
        survivor_hr = {g.heat_rate for g in coal_survivors}
        self.assertTrue(min(retired_hr) > max(survivor_hr))
        # Every retention is attributed (rule 20 analogue).
        self.assertEqual(len(retention_log), 10)

    def test_highest_heat_rate_retires_first(self):
        # Reliability floor keeps the requirement met; the least efficient
        # units are the ones actually retired. requirement =
        # 1650 x 1.1375 = 1876.9 MW; two coal UCAP = 1900 MW clears it.
        config = ScenarioConfig()
        coal = [
            _gen("C0", "coal", pmax=1000.0, heat_rate=9.0),
            _gen("C1", "coal", pmax=1000.0, heat_rate=10.0),
            _gen("C2", "coal", pmax=1000.0, heat_rate=11.0),
        ]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(3, 10.0)
        survivors, _, _ = apply_economic_retirements(
            coal, arrays, dispatch, prices, config, {}, peak_demand=1650.0
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
        fleet1, losses1, _ = apply_economic_retirements(
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

        fleet1, losses1, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        self.assertEqual([g.unit_id for g in fleet1], ["W0"])
        self.assertEqual(losses1, {})


class TestFomThresholdFlip(unittest.TestCase):
    """The retirement decision flips at the going-forward FOM bar.

    Behavioural acceptance for the capacity-economics recalibration Stage 1
    (``docs/handoffs/capacity-economics-plan-2026-07.md`` §1, §8): a gas-CT
    earning a fixed net revenue between the legacy bar (``fixed_om_gas_ct=8``
    $/kW-yr) and the NREL-ATB-2024 bar (``fixed_om_gas_ct=21`` $/kW-yr) is
    retained under the legacy FOM and retired under the ATB FOM — the same unit,
    the same revenue, only the FOM default moved. This is the identification
    check that the FOM level, not a residual, drives the retire flip (rule 1).
    """

    T = 10

    def _dispatch(self, level):
        return SimpleNamespace(dispatch=np.full((1, self.T), level))

    def _run_two_years(self, fom_gas_ct):
        # net_revenue = price x dispatch x T = 1500 x 100 x 10 = 1.5e6 $/yr
        # = 15 $/kW-yr on a 100 MW unit — between the 8 and 21 $/kW-yr bars.
        config = ScenarioConfig().with_overrides(fixed_om_gas_ct=fom_gas_ct)
        fleet = [_gen("T0", "gas_ct", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 1500.0)
        dispatch = self._dispatch(100.0)
        fleet1, losses1, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        fleet2, losses2, _ = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        return fleet1, losses1, fleet2, losses2

    def test_survives_under_legacy_bar(self):
        # 15 $/kW-yr net revenue > 8 $/kW-yr legacy bar -> profitable, never a
        # loss year, so the CT stays online across both years.
        fleet1, losses1, fleet2, losses2 = self._run_two_years(8.0)
        self.assertEqual([g.unit_id for g in fleet1], ["T0"])
        self.assertEqual(losses1["T0"], 0)
        self.assertEqual([g.unit_id for g in fleet2], ["T0"])
        self.assertEqual(losses2["T0"], 0)

    def test_retires_under_atb_bar(self):
        # 15 $/kW-yr net revenue < 21 $/kW-yr ATB bar -> a loss year each pass;
        # gas_ct retires after its two-year threshold.
        fleet1, losses1, fleet2, losses2 = self._run_two_years(21.0)
        self.assertEqual([g.unit_id for g in fleet1], ["T0"])
        self.assertEqual(losses1["T0"], 1)
        self.assertEqual(fleet2, [])
        self.assertNotIn("T0", losses2)


class TestReliabilityFloorAccredited(unittest.TestCase):
    """Accredited-basis reliability floor (capacity-economics plan §3.2/§8.3)."""

    T = 10

    def _dispatch_result(self, n_gen, level):
        return SimpleNamespace(dispatch=np.full((n_gen, self.T), level))

    def _screen(self, fleet, config, peak, losses=None, **kwargs):
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)  # deeply unprofitable for all
        dispatch = self._dispatch_result(len(fleet), 10.0)
        return apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            losses or {},
            peak_demand=peak,
            **kwargs,
        )

    def test_requirement_math_counts_pools_at_capacity_credit(self):
        # Hand-computed accredited sum (plan §8.3 item 3): one 1000 MW coal
        # unit, eford 0.05 -> UCAP 950. ERCOT requirement = peak x 1.1375.
        # With wind_pool 4000 MW (credit from RENEWABLE_CAPACITY_CREDIT) and
        # storage_firm 500 MW the requirement clears without the coal unit,
        # so it retires; with pools=0 (conservative default) the floor
        # rescues it.
        from market_sim.config.constants import RENEWABLE_CAPACITY_CREDIT

        config = ScenarioConfig()
        coal = [_gen("C0", "coal", pmax=1000.0)]
        peak = 1000.0
        requirement = peak * 1.1375
        pooled_firm = (
            4000.0 * RENEWABLE_CAPACITY_CREDIT["wind"]
            + 2000.0 * RENEWABLE_CAPACITY_CREDIT["solar"]
            + 500.0
        )
        self.assertGreaterEqual(pooled_firm, requirement)

        survivors, _, log = self._screen(
            coal,
            config,
            peak,
            wind_pool_mw=4000.0,
            solar_pool_mw=2000.0,
            storage_firm_mw=500.0,
        )
        self.assertEqual(survivors, [])  # pools cover the requirement
        self.assertEqual(log, [])

        survivors, _, log = self._screen(coal, config, peak)
        self.assertEqual([g.unit_id for g in survivors], ["C0"])
        self.assertEqual(len(log), 1)

    def test_retention_merit_cost_then_co2(self):
        # Crafted coal-vs-CT tie on $/firm-MW (plan §8.3 item 3): equalize
        # the going-forward cost keys so the CO2 rate decides — the CT
        # (0.55 t/MWh) is retained ahead of the coal unit (0.95 t/MWh)
        # even though coal's heat rate is lower (the old key got this
        # backwards).
        config = ScenarioConfig().with_overrides(
            fixed_om_coal=8.0, retirement_fom_multiplier_coal=1.0
        )
        fleet = [
            _gen("CO", "coal", pmax=1000.0, heat_rate=9.5, emission_rate_co2=0.95),
            _gen("CT", "gas_ct", pmax=1000.0, heat_rate=11.0, emission_rate_co2=0.55),
        ]
        # Requirement needs exactly one unit's UCAP (950): peak x 1.1375
        # in (0, 950] -> peak 800 -> requirement 910. The CT enters with one
        # prior loss year so both units hit their thresholds this year.
        survivors, _, log = self._screen(fleet, config, peak=800.0, losses={"CT": 1})
        self.assertEqual([g.unit_id for g in survivors], ["CT"])
        self.assertEqual(log[0]["unit_id"], "CT")
        self.assertEqual(log[0]["co2_rate"], 0.55)

    def test_retention_merit_cost_is_primary(self):
        # Cost stays the primary key: a cheap-adequacy CT (8 $/kW-yr) beats
        # coal (52 effective) regardless of CO2 — the floor is an adequacy
        # purchase, not an emissions ranking.
        config = ScenarioConfig()
        fleet = [
            _gen("CO", "coal", pmax=1000.0, emission_rate_co2=0.95),
            _gen("CT", "gas_ct", pmax=1000.0, emission_rate_co2=0.55),
        ]
        survivors, _, _ = self._screen(fleet, config, peak=800.0, losses={"CT": 1})
        self.assertEqual([g.unit_id for g in survivors], ["CT"])

    def test_floor_never_retires_only_unretires(self):
        # A profitable unit is never touched by the floor (plan §8.3
        # item 3): the floor operates only on the screen's own eligible
        # (retiring) set.
        config = ScenarioConfig()
        rich = _gen("RICH", "gas_cc", pmax=100.0)
        poor = _gen("POOR", "gas_ct", pmax=100.0)
        fleet = [rich, poor]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # RICH clears its bar (deeply negative mc -> huge inframarginal
        # margin); POOR is on its final loss year.
        prices = np.full((1, self.T), 10.0)
        mc = np.zeros((2, self.T))
        mc[0, :] = -1.0e6
        dispatch = self._dispatch_result(2, 10.0)
        survivors, _, log = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {"POOR": 1},
            peak_demand=50.0,
            mc=mc,
        )
        # Requirement 56.9 < RICH UCAP 95: POOR retires, RICH survives, and
        # the floor neither retired RICH nor logged anything.
        self.assertEqual([g.unit_id for g in survivors], ["RICH"])
        self.assertEqual(log, [])

    def test_retention_log_rows_complete(self):
        config = ScenarioConfig()
        coal = [_gen("C0", "coal", pmax=1000.0, emission_rate_co2=0.9)]
        _, losses, log = self._screen(coal, config, peak=800.0, year=2031)
        self.assertEqual(len(log), 1)
        row = log[0]
        self.assertEqual(
            set(row),
            {
                "year",
                "unit_id",
                "fuel_type",
                "pmax_mw",
                "ucap_mw",
                "going_forward_cost",
                "co2_rate",
                "loss_years",
            },
        )
        self.assertEqual(row["year"], 2031)
        self.assertEqual(row["fuel_type"], "coal")
        self.assertAlmostEqual(row["ucap_mw"], 950.0)
        # going_forward_cost = 40 x 1.3 x 1000 MW x 1000 = 52,000,000 $/yr.
        self.assertAlmostEqual(row["going_forward_cost"], 52.0e6)
        self.assertEqual(row["loss_years"], 1)
        # The floor-retained unit keeps its loss counter (re-screened next
        # year); it is un-retired, not absolved.
        self.assertEqual(losses["C0"], 1)

    def test_pools_zero_floor_at_least_as_conservative_as_nameplate(self):
        # With pools=0 and equal margin, the UCAP discount makes the
        # accredited floor retain at least as much as a nameplate floor
        # (plan §8.3 item 3): nameplate 2 x 1000 = 2000 clears a 1990
        # requirement, but accredited 2 x 950 = 1900 does not, so a third
        # unit is retained.
        config = ScenarioConfig().with_overrides(planning_reserve_margin_override=0.0)
        coal = [
            _gen(f"C{i}", "coal", pmax=1000.0, heat_rate=9.0 + 0.1 * i)
            for i in range(4)
        ]
        survivors, _, _ = self._screen(coal, config, peak=1990.0)
        self.assertEqual(len(survivors), 3)

    def test_locational_exemption_skips_ra_saturated_zone(self):
        # Under capacity_deliverability_limits, a unit in a zone already
        # long on deliverable firm capacity is exempt from floor retention
        # (mirror of the screens' _zone_is_long gate).
        config = ScenarioConfig()
        fleet = [
            _gen("A", "coal", pmax=1000.0, zone="Z0"),
            _gen("B", "coal", pmax=1000.0, heat_rate=12.0, zone="ZLONG"),
        ]
        arrays = generators_to_fleet_arrays(fleet, ["Z0", "ZLONG"], hours=self.T)
        prices = np.full((2, self.T), 10.0)
        dispatch = self._dispatch_result(2, 10.0)
        headroom = {"ZLONG": 500.0}  # RA saturated
        survivors, _, log = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=1500.0,
            deliverability_headroom=headroom,
        )
        # Requirement 1706 needs both units' UCAP, but ZLONG is exempt:
        # only A is retained; B retires.
        self.assertEqual([g.unit_id for g in survivors], ["A"])
        self.assertEqual([r["unit_id"] for r in log], ["A"])

    def test_peak_demand_next_drives_floor_through_evolve_fleet(self):
        # Plan §2.3 component 1: the floor tests the entering year's known
        # peak, not the prior-year bookkeeping peak. Two 1000 MW coal units
        # (UCAP 950 each): against the stale 500 MW prior peak (requirement
        # 569) one unit's UCAP suffices and the other retires; against the
        # known 1200 MW peak (requirement 1365) both are retained.
        config = ScenarioConfig(iso="ERCOT")
        coal = [
            _gen("C0", "coal", pmax=1000.0, heat_rate=9.0),
            _gen("C1", "coal", pmax=1000.0, heat_rate=10.0),
        ]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        prior = {
            "fleet_arrays": arrays,
            "dispatch_result": self._dispatch_result(2, 10.0),
            "prices": np.full((1, self.T), 10.0),
            "peak_demand": 500.0,
        }
        # (evolve_fleet re-aggregates the fleet into bin representatives, so
        # assert on retained MW and the retention log, not unit identity.)
        fleet, _, _, _, log = evolve_fleet(coal, prior, 2030, config, {})
        self.assertEqual(sum(g.pmax_mw for g in fleet), 1000.0)
        self.assertEqual(len(log), 1)

        fleet, _, _, _, log = evolve_fleet(
            coal, prior, 2030, config, {}, peak_demand_next=1200.0
        )
        self.assertEqual(sum(g.pmax_mw for g in fleet), 2000.0)
        self.assertEqual(len(log), 2)

    def test_resolve_planning_reserve_margin(self):
        from market_sim.model.capacity import resolve_planning_reserve_margin

        config = ScenarioConfig()
        self.assertEqual(
            resolve_planning_reserve_margin(config, "PJM"),
            PLANNING_RESERVE_MARGIN_BY_ISO["PJM"],
        )
        # Unknown ISO falls back to the config scalar.
        self.assertEqual(
            resolve_planning_reserve_margin(config, "NOPE"),
            config.planning_reserve_margin,
        )
        # The registered override lever beats the registry (tornado channel).
        config2 = config.with_overrides(planning_reserve_margin_override=0.10)
        self.assertEqual(resolve_planning_reserve_margin(config2, "PJM"), 0.10)


class TestReserveMarginBuild(unittest.TestCase):
    """The adequacy backstop: force-build firm capacity to the reserve margin."""

    def test_firm_capacity_accredits_by_resource(self):
        from market_sim.model.capacity import accredited_firm_capacity_mw

        fleet = [
            _gen("cc", "gas_cc", pmax=1000.0),  # eford default 0.05 in Generator
            _gen("n", "nuclear", pmax=1000.0),
        ]
        # Thermal nets to UCAP (1 - eford); pool renewables to their credit.
        firm = accredited_firm_capacity_mw(
            fleet,
            wind_pool_mw=1000.0,
            solar_pool_mw=1000.0,
            storage_firm_mw=500.0,
        )
        # 500 storage + 160 wind + 180 solar + thermal UCAP (both < nameplate).
        self.assertGreater(firm, 500.0 + 160.0 + 180.0)
        self.assertLess(firm, 500.0 + 160.0 + 180.0 + 2000.0)

    def test_backstop_builds_to_meet_margin(self):
        from market_sim.model.capacity import apply_reserve_margin_build

        config = ScenarioConfig(iso="ERCOT", reserve_margin_build_enabled=True)
        fleet = [_gen("cc", "gas_cc", pmax=1000.0)]
        new_fleet, built = apply_reserve_margin_build(
            fleet,
            firm_capacity_mw=5000.0,
            peak_demand_mw=8000.0,
            year=2030,
            config=config,
            iso="ERCOT",
        )
        # required = 8000 * 1.1375 = 9100; gap = 4100 firm -> >0 nameplate.
        self.assertGreater(built, 0.0)
        self.assertTrue(any(g.unit_id == "gas_ct_adequacy_2030" for g in new_fleet))

    def test_backstop_noop_when_disabled_or_adequate(self):
        from market_sim.model.capacity import apply_reserve_margin_build

        # Disabled: no build even when short.
        off = ScenarioConfig(iso="ERCOT")
        _, b0 = apply_reserve_margin_build([], 0.0, 8000.0, 2030, off, "ERCOT")
        self.assertEqual(b0, 0.0)
        # Enabled but already adequate: no build.
        on = ScenarioConfig(iso="ERCOT", reserve_margin_build_enabled=True)
        _, b1 = apply_reserve_margin_build([], 9999.0, 8000.0, 2030, on, "ERCOT")
        self.assertEqual(b1, 0.0)

    def test_ercot_parity_with_scalar_default(self):
        """ERCOT resolves to 0.1375 and the build matches today's behavior.

        The per-ISO registry leads, but ERCOT's registry target equals the
        historic scalar default, so the ERCOT reserve-margin build is
        byte-identical to the pre-registry behavior (the parity guard).
        """
        from market_sim.model.capacity import apply_reserve_margin_build

        # Registry parity: ERCOT's entry is exactly the old scalar default.
        self.assertEqual(PLANNING_RESERVE_MARGIN_BY_ISO["ERCOT"], 0.1375)
        self.assertEqual(
            PLANNING_RESERVE_MARGIN_BY_ISO["ERCOT"],
            ScenarioConfig().planning_reserve_margin,
        )
        config = ScenarioConfig(iso="ERCOT", reserve_margin_build_enabled=True)
        _, built_registry = apply_reserve_margin_build(
            [_gen("cc", "gas_cc", pmax=1000.0)],
            firm_capacity_mw=5000.0,
            peak_demand_mw=8000.0,
            year=2030,
            config=config,
            iso="ERCOT",
        )
        # Drop ERCOT from the registry so the scalar fallback (0.1375) is used
        # instead; the resolved margin -- and the build -- must be identical.
        with mock.patch.dict(PLANNING_RESERVE_MARGIN_BY_ISO, clear=False) as registry:
            del registry["ERCOT"]
            _, built_scalar = apply_reserve_margin_build(
                [_gen("cc", "gas_cc", pmax=1000.0)],
                firm_capacity_mw=5000.0,
                peak_demand_mw=8000.0,
                year=2030,
                config=config,
                iso="ERCOT",
            )
        self.assertGreater(built_registry, 0.0)
        self.assertEqual(built_registry, built_scalar)

    def test_higher_target_iso_builds_more_than_ercot(self):
        """A capacity-market ISO (PJM) force-builds more to its higher floor.

        PJM's installed-reserve-margin target (~17.8%) exceeds ERCOT's 13.75%,
        so for the same firm capacity and peak the adequacy backstop builds
        strictly more gas_ct in PJM than it would at ERCOT's margin.
        """
        from market_sim.model.capacity import apply_reserve_margin_build

        self.assertGreater(
            PLANNING_RESERVE_MARGIN_BY_ISO["PJM"],
            PLANNING_RESERVE_MARGIN_BY_ISO["ERCOT"],
        )
        config = ScenarioConfig(reserve_margin_build_enabled=True)
        # Identical firm/peak; only the resolved per-ISO margin differs. The
        # gap stays well under each ISO's queue cap so neither is clipped.
        _, built_ercot = apply_reserve_margin_build(
            [],
            firm_capacity_mw=5000.0,
            peak_demand_mw=8000.0,
            year=2030,
            config=config,
            iso="ERCOT",
        )
        _, built_pjm = apply_reserve_margin_build(
            [],
            firm_capacity_mw=5000.0,
            peak_demand_mw=8000.0,
            year=2030,
            config=config,
            iso="PJM",
        )
        self.assertGreater(built_ercot, 0.0)
        self.assertGreater(built_pjm, built_ercot)

    def test_explicit_scalar_overrides_for_iso_absent_from_registry(self):
        """The ScenarioConfig scalar drives any ISO absent from the registry.

        With the ISO removed from the registry, an explicit
        ``planning_reserve_margin`` is honored: a higher scalar builds strictly
        more than the registry target it replaces.
        """
        from market_sim.model.capacity import apply_reserve_margin_build

        # Registry PJM target (~0.178) vs an explicit, higher override (0.30).
        registry_config = ScenarioConfig(reserve_margin_build_enabled=True)
        _, built_registry = apply_reserve_margin_build(
            [],
            firm_capacity_mw=5000.0,
            peak_demand_mw=8000.0,
            year=2030,
            config=registry_config,
            iso="PJM",
        )
        override_config = ScenarioConfig(
            reserve_margin_build_enabled=True,
            planning_reserve_margin=0.30,
        )
        with mock.patch.dict(PLANNING_RESERVE_MARGIN_BY_ISO, clear=False) as registry:
            del registry["PJM"]
            _, built_override = apply_reserve_margin_build(
                [],
                firm_capacity_mw=5000.0,
                peak_demand_mw=8000.0,
                year=2030,
                config=override_config,
                iso="PJM",
            )
        self.assertGreater(built_override, built_registry)

    def test_iso_absent_from_registry_falls_back_to_scalar(self):
        """An ISO with no registry entry uses ``config.planning_reserve_margin``.

        ``.get(iso, config.planning_reserve_margin)`` returns the scalar
        fallback, so the resolved margin equals the default 0.1375 -- the same
        result as the ERCOT (registry) build at firm/peak parity.
        """
        from market_sim.model.capacity import apply_reserve_margin_build

        config = ScenarioConfig(reserve_margin_build_enabled=True)
        self.assertEqual(config.planning_reserve_margin, 0.1375)
        with mock.patch.dict(PLANNING_RESERVE_MARGIN_BY_ISO, clear=False) as registry:
            del registry["PJM"]
            _, built_fallback = apply_reserve_margin_build(
                [],
                firm_capacity_mw=5000.0,
                peak_demand_mw=8000.0,
                year=2030,
                config=config,
                iso="PJM",
            )
        # Same scalar (0.1375) applied to the same firm/peak as ERCOT.
        _, built_ercot = apply_reserve_margin_build(
            [],
            firm_capacity_mw=5000.0,
            peak_demand_mw=8000.0,
            year=2030,
            config=config,
            iso="ERCOT",
        )
        self.assertGreater(built_fallback, 0.0)
        self.assertEqual(built_fallback, built_ercot)


class TestRetirementMargin(unittest.TestCase):
    """The retirement screen nets variable cost against price.

    Gross revenue alone lets a unit "cover" fixed cost with money it spent
    on fuel (peer review B1): a unit dispatching at a price equal to its
    own marginal cost earns zero margin and must accumulate a loss year,
    however large its gross revenue.
    """

    T = 10

    def _setup(self, price, mc_value, level=100.0):
        config = ScenarioConfig()
        fleet = [_gen("G0", "gas_cc", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), price)
        mc = np.full((1, self.T), mc_value)
        dispatch = SimpleNamespace(dispatch=np.full((1, self.T), level))
        return config, fleet, arrays, dispatch, prices, mc

    def test_price_equal_to_mc_is_a_loss_year(self):
        # Gross revenue = 50 * 100 MW * 10 h = 50_000 -- far above the
        # 1_200_000/8760-scaled fixed cost would *not* be the issue here;
        # the point is margin = 0 regardless of how large gross gets.
        config, fleet, arrays, dispatch, prices, mc = self._setup(50.0, 50.0)
        fleet1, losses1, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=0.0,
            mc=mc,
        )
        self.assertEqual(losses1["G0"], 1)

    def test_margin_covering_fixed_cost_is_profitable(self):
        # going_forward_cost = 12 $/kW-yr * 1.0 * 100 MW * 1000 = 1_200_000.
        # The screen's basis is the attainable pro-forma margin on AVAILABLE
        # capacity (capacity-economics plan 2026-07 §5 step 2): with the
        # default eford 0.05, margin/h = (1313 - 50) $/MWh * 95 MW =
        # 119_985; over 10 h = 1_199_850 < 1_200_000 would be a loss, so
        # price 1313.2 -> (1263.2 * 95 * 10) = 1_200_040 clears the bar.
        config, fleet, arrays, dispatch, prices, mc = self._setup(1313.2, 50.0)
        fleet1, losses1, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=0.0,
            mc=mc,
        )
        self.assertEqual(losses1["G0"], 0)

    def test_gross_fallback_when_mc_absent(self):
        # Without an mc array the screen degrades to gross revenue (and
        # warns): the same price-equals-mc unit now looks profitable.
        # gross/h = 1250 * 100 = 125_000; over 10 h >> 1_200_000? No:
        # 1_250_000 > 1_200_000, so no loss year -- the old (buggy)
        # behavior, preserved only as an explicit fallback.
        config, fleet, arrays, dispatch, prices, _ = self._setup(1250.0, 1250.0)
        fleet1, losses1, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=0.0,
        )
        self.assertEqual(losses1["G0"], 0)

    def test_mc_flows_through_evolve_fleet(self):
        # evolve_fleet reads prior_results["mc_cost"] and passes it to the
        # retirement screen: price == mc for one full year retires coal
        # (threshold 1) where the gross-revenue path would have kept it.
        config = ScenarioConfig()
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prior = {
            "fleet_arrays": arrays,
            "dispatch_result": SimpleNamespace(dispatch=np.full((1, self.T), 100.0)),
            "prices": np.full((1, self.T), 100000.0),
            "mc_cost": np.full((1, self.T), 100000.0),
            "peak_demand": 0.0,
        }
        fleet1, tracker, _, _, _ = evolve_fleet(
            fleet,
            prior,
            2030,
            config,
            {},
        )
        self.assertNotIn("C0", [g.unit_id for g in fleet1])


class TestScreenReserveValue(unittest.TestCase):
    """Pro-forma margin + reserve-price valuation in the retirement screen.

    Capacity-economics plan 2026-07 §5 step 2 (the revenue-side fix): the
    screen's margin basis is the unit's attainable per-hour best use
    ``max(0, price - mc, reserve price)`` on available capacity — the
    Potomac-SOM net-revenue construction — never the prior LP's realized
    dispatch, and the hourly reserve signal is the SOLE thermal AS pricing
    when present (rule 19).
    """

    T = 10

    def _screen(self, fleet, prices, mc, config=None, dispatch_level=0.0, **kw):
        config = config or ScenarioConfig()
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        dispatch = SimpleNamespace(
            dispatch=np.full((len(fleet), self.T), dispatch_level)
        )
        return apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=0.0,
            mc=mc,
            **kw,
        )

    def test_proforma_counts_idle_hour_margin(self):
        # A unit the prior LP left IDLE (dispatch = 0) in hours where the
        # screen's price signal clears its full variable cost — exactly the
        # post-solve-ORDC-adder case — earns the margin the signal carries.
        # Under the old realized-dispatch basis its margin was 0 (a loss
        # year); the pro-forma basis clears the bar.
        # bar = 12 $/kW-yr x 100 MW x 1000 = 1_200_000;
        # margin = (1400 - 50) x 95 MW avail x 10 h = 1_282_500 > bar.
        fleet = [_gen("G0", "gas_cc", pmax=100.0)]
        prices = np.full((1, self.T), 1400.0)
        mc = np.full((1, self.T), 50.0)
        _, losses, _ = self._screen(fleet, prices, mc, dispatch_level=0.0)
        self.assertEqual(losses["G0"], 0)

    def test_reserve_signal_values_headroom_when_out_of_merit(self):
        # A quick-start CT priced out of the energy market all year
        # (price << mc) still earns the reserve price on its available
        # capacity: value = max(0, price - mc, r) = r.
        # bar = 8 $/kW-yr x 100 MW x 1000 = 800_000;
        # reserve value = 900 x 95 MW x 10 h = 855_000 > bar.
        fleet = [_gen("T0", "gas_ct", pmax=100.0)]
        prices = np.zeros((1, self.T))
        mc = np.full((1, self.T), 50.0)
        r = np.full(self.T, 900.0)
        _, losses, _ = self._screen(
            fleet,
            prices,
            mc,
            reserve_price_signal=r,
            reserve_price_signal_slow=r,
        )
        self.assertEqual(losses["T0"], 0)
        # Without the signal the same unit is a loss year.
        _, losses_off, _ = self._screen(fleet, prices, mc)
        self.assertEqual(losses_off["T0"], 1)

    def test_quick_start_uses_slow_tier_only(self):
        # The eligibility cascade: an offline-capable quick-start (gas_ct)
        # sees only the Non-Spin tier; a synchronized CC sees the
        # all-products tier. With a rich all-products price but a zero slow
        # tier, the CT stays a loss while the CC clears its bar.
        prices = np.zeros((1, self.T))
        mc = np.full((1, self.T), 50.0)
        r_all = np.full(self.T, 2000.0)  # 2000 x 95 x 10 = 1.9e6 > both bars
        r_slow = np.zeros(self.T)
        _, ct_losses, _ = self._screen(
            [_gen("T0", "gas_ct", pmax=100.0)],
            prices,
            mc,
            reserve_price_signal=r_all,
            reserve_price_signal_slow=r_slow,
        )
        self.assertEqual(ct_losses["T0"], 1)
        _, cc_losses, _ = self._screen(
            [_gen("G0", "gas_cc", pmax=100.0)],
            prices,
            mc,
            reserve_price_signal=r_all,
            reserve_price_signal_slow=r_slow,
        )
        self.assertEqual(cc_losses["G0"], 0)

    def test_reserve_signal_supersedes_exogenous_flat_rate(self):
        # Rule 19: exactly one mechanism prices thermal AS. The exogenous
        # flat rate alone clears the CT bar (multiplier scaled so the flat
        # credit > 800_000); with an hourly reserve signal present the flat
        # rate must be suppressed, so a near-zero signal leaves the unit in
        # a loss year instead of stacking both credits.
        from market_sim.model.ancillary import as_revenue_per_mw_yr

        config = ScenarioConfig(iso="ERCOT").with_overrides(as_revenue_enabled=True)
        base = as_revenue_per_mw_yr("gas_ct", 0.0, config)
        self.assertGreater(base, 0.0)
        needed = (900_000.0 / 100.0) / base  # flat credit ~ 9 $/kW-yr > bar 8
        config = config.with_overrides(as_revenue_multiplier=needed)
        fleet = [_gen("T0", "gas_ct", pmax=100.0)]
        prices = np.zeros((1, self.T))
        mc = np.full((1, self.T), 50.0)
        _, losses_flat, _ = self._screen(fleet, prices, mc, config=config)
        self.assertEqual(losses_flat["T0"], 0)  # flat rate alone clears
        tiny = np.full(self.T, 1.0)
        _, losses_sig, _ = self._screen(
            fleet,
            prices,
            mc,
            config=config,
            reserve_price_signal=tiny,
            reserve_price_signal_slow=tiny,
        )
        self.assertEqual(losses_sig["T0"], 1)  # signal supersedes, no stack

    def test_vre_entry_uses_zonal_hourly_cf_when_available(self):
        # Plan §6 CX-6c (mock-assert form): with zonal CF profiles + zone
        # ordering supplied, the wind/solar entry screen calls
        # estimate_expected_revenue with the build zone's HOURLY cf array;
        # without them, the scalar base-CF path still runs.
        from unittest.mock import patch

        from market_sim.config.iso_configs import get_iso_config as _gic
        from market_sim.data.renewables import get_renewable_zone

        iso = "ERCOT"
        zone_names = [z.name for z in _gic(iso).zones]
        n_zones = len(zone_names)
        prices = np.full((n_zones, self.T), 60.0)
        rng = np.random.default_rng(7)
        wind_cf = rng.uniform(0.1, 0.9, size=(n_zones, self.T))
        solar_cf = rng.uniform(0.0, 0.8, size=(n_zones, self.T))
        seen: dict[str, object] = {}
        real = estimate_expected_revenue

        def recorder(p, cf, *a, **kw):
            if isinstance(cf, np.ndarray):
                seen["hourly"] = cf.copy()
            return real(p, cf, *a, **kw)

        with patch("market_sim.model.capacity.estimate_expected_revenue", recorder):
            apply_economic_new_entry(
                [],
                prices,
                2030,
                ScenarioConfig(iso=iso),
                iso,
                gas_price_per_mmbtu=3.5,
                zone_names=zone_names,
                wind_cf=wind_cf,
                solar_cf=solar_cf,
            )
        self.assertIn("hourly", seen)
        wind_zone = get_renewable_zone(iso, "wind")
        solar_zone = get_renewable_zone(iso, "solar")
        hourly = seen["hourly"]
        self.assertTrue(
            np.array_equal(hourly, wind_cf[zone_names.index(wind_zone)])
            or np.array_equal(hourly, solar_cf[zone_names.index(solar_zone)])
        )
        # Scalar path still supported when profiles are absent.
        seen.clear()
        with patch("market_sim.model.capacity.estimate_expected_revenue", recorder):
            apply_economic_new_entry(
                [],
                prices,
                2030,
                ScenarioConfig(iso=iso),
                iso,
                gas_price_per_mmbtu=3.5,
            )
        self.assertNotIn("hourly", seen)


class TestQueueCapCoverage(unittest.TestCase):
    """Every registered ISO must carry queue-cap data (peer review B2)."""

    ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO")

    def test_every_registered_iso_has_queue_caps(self):
        for iso in self.ISOS:
            name = get_iso_config(iso).name
            self.assertIn(name, QUEUE_CAP_GW)
            self.assertIn(name, QUEUE_CAP_PER_TECH_GW)
            # The classic candidates must each have a per-tech entry so
            # .get(tech, 0.0) can't silently zero out a whole technology.
            for tech in ("wind", "solar", "gas_cc", "nuclear"):
                self.assertIn(tech, QUEUE_CAP_PER_TECH_GW[name])

    def test_missing_queue_cap_raises(self):
        # A missing entry must fail loudly, not silently build nothing.
        prices = np.full((1, 10), 60.0)
        removed = QUEUE_CAP_GW.pop("PJM")
        try:
            with self.assertRaises(KeyError):
                apply_economic_new_entry(
                    [],
                    prices,
                    2030,
                    ScenarioConfig(iso="PJM"),
                    "PJM",
                )
        finally:
            QUEUE_CAP_GW["PJM"] = removed

    def test_eastern_iso_entry_runs(self):
        # A PJM forward year previously died on a KeyError before any
        # screening happened; now it must at least screen and build.
        prices = np.full((1, 10), 200.0)  # rich prices: something builds
        fleet, additions = apply_economic_new_entry(
            [],
            prices,
            2030,
            ScenarioConfig(iso="PJM"),
            "PJM",
            gas_price_per_mmbtu=3.5,
        )
        built_mw = sum(g.pmax_mw for g in fleet) + sum(
            mw for zone in additions.values() for mw in zone.values()
        )
        self.assertGreater(built_mw, 0.0)


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
        self.assertAlmostEqual(compute_clean_share([], renewable_cap_mw=5000.0), 1.0)


class TestWrightCost(unittest.TestCase):
    """Wright's-Law learning-curve cost adjustment."""

    def test_cost_unchanged_at_reference(self):
        self.assertAlmostEqual(wright_cost(100.0, 100.0, 100.0, 0.2), 100.0)

    def test_cost_falls_as_deployment_grows(self):
        # A learning rate is "fractional cost reduction per doubling":
        # doubling cumulative capacity multiplies cost by exactly
        # (1 - rate). The old ratio**(-rate) form gave only 2**(-0.2)
        # = 0.87 for a documented 20%/doubling rate (peer review B8).
        cost = wright_cost(100.0, 200.0, 100.0, 0.2)
        self.assertLess(cost, 100.0)
        self.assertAlmostEqual(cost, 80.0)

    def test_two_doublings_compound(self):
        self.assertAlmostEqual(wright_cost(100.0, 400.0, 100.0, 0.2), 100.0 * 0.8**2)

    def test_non_positive_capacity_returns_base(self):
        self.assertEqual(wright_cost(100.0, 0.0, 100.0, 0.2), 100.0)
        self.assertEqual(wright_cost(100.0, 50.0, 0.0, 0.2), 100.0)

    def test_zero_learning_rate_disables_learning(self):
        self.assertEqual(wright_cost(100.0, 400.0, 100.0, 0.0), 100.0)


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
        config = ScenarioConfig()  # ira_wind_solar_last_year = 2027
        with_credit = compute_lcoe("wind", 2027, config)
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
            "nuclear_smr",
            2030,
            config,
            cumulative_gw=WRIGHT_REFERENCE_GW["nuclear_smr"],
        )
        grown = compute_lcoe(
            "nuclear_smr",
            2030,
            config,
            cumulative_gw=2 * WRIGHT_REFERENCE_GW["nuclear_smr"],
        )
        self.assertGreater(at_ref, 0.0)
        self.assertLess(grown, at_ref)

    def test_nuclear_smr_cheaper_than_large(self):
        smr = compute_lcoe("nuclear_smr", 2030, ScenarioConfig())
        large = compute_lcoe("nuclear_large", 2030, ScenarioConfig())
        self.assertLess(smr, large)

    def test_solar_itc_discounts_only_the_capital_component(self):
        # The IRA ITC reduces capex before annualization, so the credit
        # never discounts fixed O&M. The ITC-adjusted LCOE is therefore
        # higher than naively scaling the raw LCOE by (1 - itc).
        config = ScenarioConfig()  # ira_itc_solar = 0.30
        with_itc = compute_lcoe("solar", 2027, config)  # ITC active
        raw = compute_lcoe("solar", 2040, config)  # ITC expired
        self.assertLess(with_itc, raw)
        self.assertGreater(with_itc, raw * 0.70)

        # Verify the exact split: only capex * (1 - itc) is annualized.
        costs = NEW_ENTRY_COSTS["solar"]
        crf = _capital_recovery_factor(config.real_discount_rate, costs["lifetime_yr"])
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
            WRIGHT_REFERENCE_GW["wind"] + GLOBAL_ANNUAL_DEPLOYMENT_GW["wind"] + 10.0,
        )

    def test_get_untracked_technology_is_none(self):
        self.assertIsNone(CumulativeDeployment.initial().get("fusion"))


class TestStorageLearningCurve(unittest.TestCase):
    """Wright's-Law learning curves wired into storage costs."""

    def test_cumulative_deployment_lowers_storage_cost(self):
        config = ScenarioConfig()
        base = compute_storage_annual_cost("li_ion_4hr", 2030, config)
        learned = compute_storage_annual_cost(
            "li_ion_4hr",
            2030,
            config,
            cumulative_gw=2 * WRIGHT_REFERENCE_GW["li_ion"],
        )
        self.assertLess(learned, base)

    def test_li_ion_8hr_shares_the_li_ion_learning_curve(self):
        # Both li-ion durations map to the "li_ion" reference key.
        config = ScenarioConfig()
        base = compute_storage_annual_cost("li_ion_8hr", 2030, config)
        learned = compute_storage_annual_cost(
            "li_ion_8hr",
            2030,
            config,
            cumulative_gw=2 * WRIGHT_REFERENCE_GW["li_ion"],
        )
        self.assertLess(learned, base)


class TestIRACreditsToLCOE(unittest.TestCase):
    """IRA investment-credit adjustment to candidate LCOE."""

    def test_wind_ptc_subtracts_flat_amount(self):
        config = ScenarioConfig()  # ira_ptc_wind = 26.0
        adjusted = apply_ira_credits_to_lcoe("wind", 50.0, 2027, config)
        self.assertAlmostEqual(adjusted, 50.0 - 26.0)

    def test_solar_itc_not_applied_post_hoc(self):
        # The solar ITC is a capital credit: it is applied to capex inside
        # compute_lcoe, not as a post-hoc scaling of a finished LCOE (which
        # would wrongly discount the fixed-O&M component too).
        config = ScenarioConfig()  # ira_itc_solar = 0.30
        adjusted = apply_ira_credits_to_lcoe("solar", 50.0, 2030, config)
        self.assertEqual(adjusted, 50.0)

    def test_credit_expires_after_expiry_year(self):
        config = ScenarioConfig()  # ira_wind_solar_last_year = 2027
        # The last eligible year itself still carries the credit.
        self.assertAlmostEqual(
            apply_ira_credits_to_lcoe("wind", 50.0, 2027, config), 24.0
        )
        # The year after the cliff leaves LCOE untouched.
        self.assertEqual(apply_ira_credits_to_lcoe("wind", 50.0, 2028, config), 50.0)

    def test_ira_phaseout_fraction(self):
        config = ScenarioConfig()  # defaults: last_full=2028, end=2033
        self.assertEqual(ira_phaseout_fraction(2028, config), 1.0)
        self.assertAlmostEqual(ira_phaseout_fraction(2029, config), 0.8)
        self.assertAlmostEqual(ira_phaseout_fraction(2030, config), 0.6)
        self.assertAlmostEqual(ira_phaseout_fraction(2031, config), 0.4)
        self.assertEqual(ira_phaseout_fraction(2033, config), 0.0)
        self.assertEqual(ira_phaseout_fraction(2040, config), 0.0)


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
        # Emerging techs are pushed out so this exercises the classic four.
        config = ScenarioConfig(
            iso="ERCOT",
            h2_available_year=2099,
            ccs_available_year=2099,
            egs_available_year=2099,
            offshore_wind_available_year=2099,
        )
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
        # With free fuel at $250 the two dispatchable gas techs have the
        # highest margins, so both build to their full per-tech caps.
        self.assertAlmostEqual(by_tech["gas_cc"], caps["gas_cc"] * 1000.0)
        self.assertAlmostEqual(by_tech["gas_ct"], caps["gas_ct"] * 1000.0)
        # The ISO total cap (12 GW) binds below the 16 GW sum of per-tech
        # caps, so a lower-margin tech is squeezed below its own cap.
        self.assertLess(by_tech.get("solar", 0.0), caps["solar"] * 1000.0)
        # Wind and solar are routed to the renewable pools, not the fleet.
        self.assertFalse(any(g.fuel_type in ("wind", "solar") for g in new_fleet))

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
        # The price-duration screen runs a CC only when the price clears its
        # marginal (fuel) cost. At a flat $40/MWh with expensive $9/MMBtu gas
        # the CC's variable cost exceeds the price every hour, so its energy
        # margin is zero and it does not build. Ignoring fuel cost (the prior
        # bug) would let it build regardless of economics.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 40.0)

        priced, _ = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", gas_price_per_mmbtu=9.0
        )
        self.assertFalse(any(g.fuel_type == "gas_cc" for g in priced))

        # With fuel treated as free, the same $40 price clears the CC's cost
        # every hour, so it builds.
        free, _ = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", gas_price_per_mmbtu=0.0
        )
        self.assertTrue(any(g.fuel_type == "gas_cc" for g in free))

    def test_gas_ct_peaker_enters_on_scarcity_tail_not_flat_price(self):
        # A simple-cycle peaker (gas_ct) is now a new-entry candidate, priced
        # on its price-duration energy margin. It clears against a scarcity-
        # rich curve (a few hundred high-price hours, where a peaker earns its
        # margin) but not against a flat price that never exceeds its cost.
        config = ScenarioConfig(iso="ERCOT")
        tail = np.full(8760, 25.0)
        tail[:250] = 5000.0  # the scarcity hours a peaker lives on
        built, _ = apply_economic_new_entry(
            [], tail, 2030, config, "ERCOT", gas_price_per_mmbtu=3.5
        )
        self.assertTrue(any(g.fuel_type == "gas_ct" for g in built))

        flat = np.full(8760, 25.0)  # never clears the peaker's marginal cost
        none, _ = apply_economic_new_entry(
            [], flat, 2030, config, "ERCOT", gas_price_per_mmbtu=3.5
        )
        self.assertFalse(any(g.fuel_type == "gas_ct" for g in none))

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


class TestRPSShadowPriceInNewEntry(unittest.TestCase):
    """The RPS shadow price raises clean-tech revenue in the entry screen."""

    def test_rps_shadow_price_makes_renewables_economic(self):
        # Prices too low for any technology to clear its LCOE on energy
        # revenue alone: with no RPS shadow price, nothing is built.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 1.0)

        _, no_rps = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", rps_shadow_price=0.0
        )
        without = sum(mw for by_fuel in no_rps.values() for mw in by_fuel.values())
        self.assertEqual(without, 0.0)

        # An RPS shadow price lifts wind and solar over the LCOE hurdle:
        # it is credited as an attribute payment on renewable revenue.
        _, with_rps = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", rps_shadow_price=500.0
        )
        with_rps_mw = sum(
            mw for by_fuel in with_rps.values() for mw in by_fuel.values()
        )
        self.assertGreater(with_rps_mw, without)

    def test_rps_shadow_price_lifts_renewable_margin_monotonically(self):
        # A higher RPS shadow price never builds less renewable capacity.
        config = ScenarioConfig(iso="ERCOT")
        prices = np.full(8760, 1.0)
        builds = []
        for rps_shadow_price in (0.0, 100.0, 300.0):
            _, additions = apply_economic_new_entry(
                [],
                prices,
                2030,
                config,
                "ERCOT",
                rps_shadow_price=rps_shadow_price,
            )
            builds.append(sum(mw for by in additions.values() for mw in by.values()))
        self.assertLessEqual(builds[0], builds[1])
        self.assertLessEqual(builds[1], builds[2])


class TestEvolveFleet(unittest.TestCase):
    """The ordered year-step orchestration of all capacity mechanisms."""

    def test_known_retirement_precedes_known_addition(self):
        config = ScenarioConfig(iso="ERCOT")
        # Nuclear (non-fossil) honors its announced retirement date; a fossil
        # unit would instead be governed by the economic screen.
        old = _gen("OLD", "nuclear", retirement_year=2030)
        new = Generator(
            unit_id="NEW",
            name="NEW",
            zone="North",
            fuel_type="wind",
            pmax_mw=100.0,
            online_year=2030,
        )
        prior = SimpleNamespace(
            fleet_arrays=None,
            dispatch_result=None,
            prices=None,
            planned_additions=[new],
        )
        fleet, tracker, _, _, _ = evolve_fleet([old], prior, 2030, config, {})
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
        fleet, tracker, _, _, _ = evolve_fleet([coal], prior, 2031, config, {"C0": 1})
        self.assertEqual(fleet, [])
        self.assertNotIn("C0", tracker)

    def test_returns_fleet_tracker_and_additions_tuple(self):
        config = ScenarioConfig(iso="ERCOT")
        result = evolve_fleet([_gen("G0", "gas_cc")], None, 2030, config, {})
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 5)
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], dict)
        # The third element is the {zone: {fuel: mw}} renewable additions.
        self.assertIsInstance(result[2], dict)
        # The fourth element is the CCS retrofit log.
        self.assertIsInstance(result[3], list)
        # The fifth element is the reliability-floor retention log.
        self.assertIsInstance(result[4], list)


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


class TestStateCarbonProgram(unittest.TestCase):
    """CA cap-and-trade allowance pricing for CAISO backcast years."""

    def test_caiso_backcast_years_pay_carb_allowance_price(self):
        # CARB quarterly-auction settlement averages (constants.py citation).
        config = ScenarioConfig(iso="CAISO", mode="backcast", weather_year=2024)
        self.assertAlmostEqual(resolve_carbon_price(config, 2023), 33.03)
        self.assertAlmostEqual(resolve_carbon_price(config, 2024), 35.23)
        self.assertAlmostEqual(resolve_carbon_price(config, 2025), 28.06)

    def test_nyiso_backcast_years_pay_rggi_allowance_price(self):
        # RGGI quarterly-auction clearing-price averages (constants.py citation).
        config = ScenarioConfig(iso="NYISO", mode="backcast", weather_year=2024)
        self.assertAlmostEqual(resolve_carbon_price(config, 2023), 13.49)
        self.assertAlmostEqual(resolve_carbon_price(config, 2024), 20.71)
        self.assertAlmostEqual(resolve_carbon_price(config, 2025), 22.09)

    def test_off_for_isos_without_a_state_program(self):
        # ERCOT/PJM backcasts stay carbon-free: their MC is unchanged.
        for iso in ("ERCOT", "PJM"):
            config = ScenarioConfig(iso=iso, mode="backcast", weather_year=2024)
            for year in (2023, 2024, 2025):
                self.assertEqual(resolve_carbon_price(config, year), 0.0)

    def test_state_carbon_pricing_flag_disables(self):
        config = ScenarioConfig(
            iso="CAISO",
            mode="backcast",
            weather_year=2024,
            state_carbon_pricing=False,
        )
        self.assertEqual(resolve_carbon_price(config, 2024), 0.0)

    def test_explicit_carbon_price_overrides_state_program(self):
        config = ScenarioConfig(iso="CAISO", carbon_price=50.0)
        self.assertEqual(resolve_carbon_price(config, 2024), 50.0)

    def test_caiso_forward_years_use_projected_program_price(self):
        # EM-6 seam fix: with the default (zero) RFF path, forward CAISO years
        # carry the PROJECTED CARB price — the last measured price (2025,
        # $28.06/t) escalated at the CARB floor-band rate (7%/yr) — not zero.
        config = ScenarioConfig(iso="CAISO", carbon_price_path="zero")
        self.assertAlmostEqual(
            resolve_carbon_price(config, 2030), 28.06 * 1.07**5, places=3
        )
        # An explicit RFF exogenous path still wins over the program projection.
        config = ScenarioConfig(iso="CAISO", carbon_price_path="mid")
        self.assertAlmostEqual(resolve_carbon_price(config, 2030), 15.0)


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
        # Pin the legacy date-retirement path so the coal C_RET exercises the
        # known-retirement orchestration (the new default exempts fossil — that
        # is covered by TestKnownRetirements).
        config = ScenarioConfig(iso="CAISO", forecast_fossil_retirement_economic=False)
        coal = [
            _gen(f"C{i}", "coal", pmax=1000.0, heat_rate=9.0 + 0.2 * i)
            for i in range(5)
        ]
        retiring = _gen(
            "C_RET", "coal", pmax=1000.0, heat_rate=8.0, retirement_year=2026
        )
        fleet, tracker, additions, _, _ = evolve_fleet(
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
        # Legacy date-retirement path so the coal unit retires on its date.
        config = ScenarioConfig(iso="ERCOT", forecast_fossil_retirement_economic=False)
        coal = _gen("C0", "coal", pmax=100.0, zone="North", retirement_year=2027)
        prior = _make_prior([coal], _zone_names(), price=60.0)
        fleet, tracker, _, _, _ = evolve_fleet([coal], prior, 2027, config, {})

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
        # Legacy date-retirement path so the coal C_RET retires on its date.
        config = ScenarioConfig(iso="ERCOT", forecast_fossil_retirement_economic=False)
        fleet = [
            _gen("C0", "coal", pmax=100.0, zone="North", heat_rate=10.0),
            _gen("C1", "coal", pmax=100.0, zone="North", heat_rate=10.5),
            _gen("G0", "gas_cc", pmax=100.0, zone="North", heat_rate=7.0),
            _gen("W0", "wind", pmax=100.0, zone="North"),
            _gen("W1", "wind", pmax=100.0, zone="North"),
            _gen(
                "C_RET",
                "coal",
                pmax=100.0,
                zone="North",
                heat_rate=9.0,
                retirement_year=2026,
            ),
        ]
        snapshots = [frozenset(g.unit_id for g in fleet)]
        tracker: dict[str, int] = {}
        prior = None
        for year in (2026, 2027, 2028):
            fleet, tracker, _, _, _ = evolve_fleet(fleet, prior, year, config, tracker)
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
                _gen(
                    f"G{i}",
                    "gas_ct",
                    pmax=100.0,
                    zone="North",
                    heat_rate=6.5 + 0.05 * i,
                )
                for i in range(20)
            ]
            wind = [_gen(f"W{i}", "wind", pmax=100.0, zone="North") for i in range(4)]
            return gas + wind

        def _run(gas_price_path):
            config = ScenarioConfig(iso="ERCOT", gas_price_path=gas_price_path)
            # A higher gas price path depresses gas-plant utilization: model
            # the prior-year gas CF the path implies so revenue tracks it.
            gas_cf = {"low": 0.35, "mid": 0.20, "high": 0.05}[gas_price_path]
            fleet = _fleet()
            tracker: dict[str, int] = {}
            prior = None
            yearly = {}
            for year in (2026, 2027, 2028):
                fleet, tracker, _, _, _ = evolve_fleet(
                    fleet, prior, year, config, tracker
                )
                yearly[year] = fleet
                prior = _make_prior(fleet, _zone_names(), price=15.0, gas_cf=gas_cf)
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
        # Legacy date-retirement path (the new default exempts fossil so its
        # phaseout is economic — covered in TestKnownRetirements).
        config = ScenarioConfig(iso="ERCOT", forecast_fossil_retirement_economic=False)
        fleet = [
            _gen(
                "C_RET",
                "coal",
                pmax=100.0,
                zone="North",
                heat_rate=8.0,
                retirement_year=2027,
            ),
            _gen("C_A", "coal", pmax=100.0, zone="North", heat_rate=11.0),
            _gen("C_B", "coal", pmax=100.0, zone="North", heat_rate=10.5),
            _gen("W0", "wind", pmax=100.0, zone="North"),
            _gen("W1", "wind", pmax=100.0, zone="North"),
        ]
        tracker: dict[str, int] = {}

        fleet, tracker, _, _, _ = evolve_fleet(fleet, None, 2026, config, tracker)
        self.assertIn("C_RET", {g.unit_id for g in fleet})

        fleet, tracker, _, _, _ = evolve_fleet(fleet, None, 2027, config, tracker)
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
            fleet, tracker, _, _, _ = evolve_fleet(fleet, prior, year, config, tracker)
            self.assertGreater(
                sum(g.pmax_mw for g in fleet),
                0.0,
                f"fleet capacity hit zero in {year}",
            )
            prior = _make_prior(fleet, _zone_names(), price=60.0)

    def test_per_tech_queue_cap_builds_both_wind_and_solar(self):
        # With wind and solar both profitable, both are built and neither
        # exceeds its per-technology queue cap. Wind and solar are routed
        # to the renewable pools rather than the thermal fleet. Emerging
        # techs are pushed out so this exercises the classic four.
        config = ScenarioConfig(
            iso="ERCOT",
            h2_available_year=2099,
            ccs_available_year=2099,
            egs_available_year=2099,
            offshore_wind_available_year=2099,
        )
        prices = np.full(8760, 250.0)
        # Expensive gas suppresses the dispatchable gas candidates (their
        # variable cost exceeds the price), isolating the renewable per-tech
        # cap behaviour this test targets.
        new_fleet, additions = apply_economic_new_entry(
            [], prices, 2030, config, "ERCOT", gas_price_per_mmbtu=50.0
        )

        by_tech = _entry_by_tech(new_fleet, additions)
        caps = QUEUE_CAP_PER_TECH_GW["ERCOT"]

        # Both wind and solar entered.
        self.assertGreater(by_tech.get("wind", 0.0), 0.0)
        self.assertGreater(by_tech.get("solar", 0.0), 0.0)
        # Neither leaked into the thermal fleet as a Generator.
        self.assertFalse(any(g.fuel_type in ("wind", "solar") for g in new_fleet))
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
            fleet, tracker, additions, _, _ = evolve_fleet(
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
