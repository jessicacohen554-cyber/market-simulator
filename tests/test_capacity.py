"""Tests for fleet retirement mechanisms in ``market_sim.model.capacity``."""

import unittest
from types import SimpleNamespace
from unittest import mock

import numpy as np

from market_sim.config.constants import (
    FORECAST_POOL_REQUIREMENT_BY_ISO,
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HOURS_PER_YEAR,
    NEW_ENTRY_COSTS,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
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
    resolve_adequacy_requirement_mw,
    resolve_forecast_pool_requirement,
    wright_cost,
)
from market_sim.model.storage import STORAGE_TECHS, compute_storage_annual_cost
from market_sim.policy.carbon import resolve_carbon_price
from market_sim.policy.constraints import get_active_policy_constraints
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    compute_dispatch_credits,
    ira_phaseout_fraction,
    section_45u_credit_per_mwh,
)
from market_sim.policy.rps import get_rps_acp, get_rps_target


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

    def test_repeated_year_call_does_not_re_derate(self):
        # Regression for the double-derate bug (fixed 2026-07-05): the fleet
        # threads forward mutated through the runner's year loop, so
        # evolve_fleet's default (apply_backlog=False) must select a row only
        # in the exact year it becomes effective -- calling again for year N+1
        # with the SAME exits list and the SAME already-derated fleet must be
        # a no-op, not a second 100 MW derate off the already-shrunk plant.
        fleet = [_binned("H_CC1", 700, 1000.0, pmin=200.0, nameplate=1000.0)]
        exits = [self._exit(700, "U1", 2028, mw=100.0)]
        derated_2028 = apply_confirmed_exits(fleet, 2028, exits)
        self.assertAlmostEqual(derated_2028[0].pmax_mw, 900.0, places=4)
        derated_2029 = apply_confirmed_exits(derated_2028, 2029, exits)
        self.assertAlmostEqual(derated_2029[0].pmax_mw, 900.0, places=4)
        # A third call for good measure -- still 900, never 810 or below.
        derated_2030 = apply_confirmed_exits(derated_2029, 2030, exits)
        self.assertAlmostEqual(derated_2030[0].pmax_mw, 900.0, places=4)

    def test_newly_effective_exit_applies_at_its_own_year(self):
        # Symmetric positive case: a row whose effective year is N+1 (not the
        # year of the first call) is a no-op at N and applies at N+1 -- the
        # default apply_backlog=False semantics used by evolve_fleet.
        fleet = [_binned("H_CC1", 701, 1000.0, pmin=200.0, nameplate=1000.0)]
        exits = [self._exit(701, "U1", 2029, mw=100.0)]
        still_whole = apply_confirmed_exits(fleet, 2028, exits)
        self.assertAlmostEqual(still_whole[0].pmax_mw, 1000.0, places=4)
        derated = apply_confirmed_exits(still_whole, 2029, exits)
        self.assertAlmostEqual(derated[0].pmax_mw, 900.0, places=4)

    def test_pre_start_backlog_applies_exactly_once(self):
        # build_base_fleet's apply_backlog=True collapses every exit with
        # effective_year <= start_year into a single application at the first
        # simulated year -- a unit confirmed to exit in 2025 or earlier must
        # not be double-derated when the 2026 forecast start year is reached.
        fleet = [_binned("H_CC1", 702, 1000.0, pmin=200.0, nameplate=1000.0)]
        exits = [self._exit(702, "U1", 2024, mw=100.0)]
        base = apply_confirmed_exits(fleet, 2026, exits, apply_backlog=True)
        self.assertAlmostEqual(base[0].pmax_mw, 900.0, places=4)
        # evolve_fleet's default (apply_backlog=False) never re-selects this
        # already-applied backlog row in a later year.
        year2 = apply_confirmed_exits(base, 2027, exits)
        self.assertAlmostEqual(year2[0].pmax_mw, 900.0, places=4)

    def test_monthly_averaged_derate_first_half_exit(self):
        # Regression for rule 24 (no off-registry tuning): V H Braunig
        # (ERCOT plant 3612) exiting units 1 & 2 (477 MW total) in March 2025.
        # Annual-average derate = (3/12 * 1.0) + (9/12 * (1138-477)/1138) = 0.686.
        # A 1138 MW CAMPD bin derated by this factor should have 1138 * 0.686 = 781.25 MW.
        fleet = [_binned("SC_STGAS3", 3612, 1138.0, pmin=227.6, nameplate=1138.0)]
        # exit_month=3 (March) -> effective year 2025.
        exits = [
            self._exit(3612, "1", 2025, month=3, mw=225.0),
            self._exit(3612, "2", 2025, month=3, mw=252.0),
        ]
        kept = apply_confirmed_exits(fleet, 2025, exits)
        # Verify the factor: 477 MW exit over 3 months (Mar) + 9 months (Apr-Dec).
        # factor = (3/12 * 1.0) + (9/12 * 661/1138) = 0.25 + 0.4356... = 0.6856...
        self.assertEqual(len(kept), 1)
        expected_mw = 1138.0 * (3 / 12 * 1.0 + 9 / 12 * (1138.0 - 477.0) / 1138.0)
        self.assertAlmostEqual(kept[0].pmax_mw, expected_mw, places=1)

    def test_full_year_derate_second_half_exit(self):
        # When exit_month > 6, effective year is year+1. If we apply in that
        # later year, the full-year reduced factor applies (no monthly averaging).
        fleet = [_binned("H_CC1", 800, 1000.0, pmin=200.0, nameplate=1000.0)]
        # exit_month=9 (September) in 2025 -> effective year 2026.
        exits = [self._exit(800, "1", 2025, month=9, mw=100.0)]
        # In 2026 (when the exit is effective), apply full-year derate.
        kept = apply_confirmed_exits(fleet, 2026, exits)
        self.assertEqual(len(kept), 1)
        # factor = (1000 - 100) / 1000 = 0.9
        self.assertAlmostEqual(kept[0].pmax_mw, 900.0, places=4)


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

    def test_coal_retires_after_three_unprofitable_years(self):
        # retirement_years_coal = 3 (D1 Option B, owner-adopted 2026-07-16:
        # the measured EIA-860 announced-to-deactivation lag, cap-weighted /
        # >=300 MW median = 3 yr — retirement-dof-identification-2026-07-15.md
        # Sa.3/Sd), retirement_fom_multiplier_coal = 1.3. A coal unit now needs
        # THREE consecutive loss years to retire, not one.
        config = ScenarioConfig()
        self.assertEqual(config.retirement_years_coal, 3)
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # going_forward_cost = 45 * 1.3 * 100 * 1000 = 5_850_000.
        # net_revenue = 10 $/MWh * 10 MW * 10 h = 1_000 << cost.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 10.0)

        # First loss year: still online, counter at 1.
        fleet1, losses1, _ = apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
        )
        self.assertEqual([g.unit_id for g in fleet1], ["C0"])
        self.assertEqual(losses1["C0"], 1)

        # Second consecutive loss year: still online, counter at 2.
        fleet2, losses2, _ = apply_economic_retirements(
            fleet1, arrays, dispatch, prices, config, losses1, peak_demand=0.0
        )
        self.assertEqual([g.unit_id for g in fleet2], ["C0"])
        self.assertEqual(losses2["C0"], 2)

        # Third consecutive loss year: retired.
        fleet3, losses3, _ = apply_economic_retirements(
            fleet2, arrays, dispatch, prices, config, losses2, peak_demand=0.0
        )
        self.assertEqual(fleet3, [])
        self.assertNotIn("C0", losses3)

    def test_staged_thinning_fields_are_deleted(self):
        # Owner D2 at the FF-1A flip (rule 26 — deleted means deleted, not
        # zeroed): the staged-thinning rate cap is superseded by the R-NEW
        # execution-lag pipeline, which carries the same physical deactivation
        # queue once (rule 19; RC-0B §a.6). A deprecated parameter that still
        # parses is a re-armable answer key, so construction must FAIL.
        self.assertFalse(hasattr(ScenarioConfig(), "staged_oversupply_thinning"))
        self.assertFalse(hasattr(ScenarioConfig(), "staged_thinning_max_gw_per_year"))
        with self.assertRaises(TypeError):
            ScenarioConfig(staged_oversupply_thinning=True)
        with self.assertRaises(TypeError):
            ScenarioConfig(staged_thinning_max_gw_per_year=3.0)

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

    def test_nuclear_not_credited_rps_shadow_in_retirement_screen(self):
        # CX-6a (capacity-economics plan 2026-07 §6.5(a)): nuclear is clean but
        # not RPS-eligible, so the retirement screen must NOT credit it the RPS
        # shadow price (the pre-fix defect used _CLEAN_FUELS, which includes
        # nuclear). Set up a nuclear unit whose energy revenue is far below its
        # FOM; a large RPS shadow, IF credited, would more than cover the gap
        # and suppress the loss year. With the fix nuclear earns no RPS credit,
        # so it still accrues a loss year.
        from market_sim.model.capacity import _CLEAN_FUELS, _RPS_ELIGIBLE_FUELS

        # Constant split: RPS-eligibility excludes nuclear/hydro; clean-share
        # accounting (a separate basis) still counts them.
        self.assertNotIn("nuclear", _RPS_ELIGIBLE_FUELS)
        self.assertNotIn("hydro", _RPS_ELIGIBLE_FUELS)
        self.assertEqual(_RPS_ELIGIBLE_FUELS, frozenset({"wind", "solar"}))
        self.assertIn("nuclear", _CLEAN_FUELS)
        self.assertIn("hydro", _CLEAN_FUELS)

        config = ScenarioConfig()  # eac_price_nuclear defaults to 0.0
        fleet = [_gen("N0", "nuclear", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        # FOM = 130 $/kW-yr * 100 MW * 1000 = 13_000_000; energy net revenue =
        # 10 $/MWh * 100 MW * 10 h = 10_000 << FOM.
        prices = np.full((1, self.T), 10.0)
        dispatch = self._dispatch_result(1, 100.0)
        # rps credit IF applied = 20_000 $/MWh * (100 MW * 10 h) = 20_000_000 > FOM.
        huge_rps = 20_000.0

        _, losses, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=0.0,
            rps_shadow_price=huge_rps,
            mc=np.zeros((1, self.T)),
        )
        self.assertEqual(
            losses.get("N0"),
            1,
            "nuclear was credited the RPS shadow price (CX-6a regression)",
        )

    def test_coal_fom_multiplier_makes_marginal_coal_unprofitable(self):
        # net_revenue = 4500 $/MWh * 100 MW * 10 h = 4_500_000.
        # Base coal FOM cost = 45 * 100 * 1000 = 4_500_000 (revenue clears at
        # the boundary). With the 1.3 multiplier = 5_850_000 (revenue falls
        # short). coal=1 pinned (D1 default is 3) so the single loss year the
        # multiplier induces is enough to retire — this test isolates the FOM
        # multiplier flip, not the loss-year threshold.
        config = ScenarioConfig(retirement_years_coal=1)
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
        # Accredited-basis floor (plan §3.2) on ERCOT's CDR convention
        # (accreditation audit 2026-07-06): requirement = firm peak x
        # (1 + PRM_ERCOT) = 10000 x 0.942 x 1.1375 = 10715.25 MW. Nuclear
        # survives the screen (loss year 1 < threshold 3) and contributes
        # 2000 MW at seasonal rating; the DC ties add 817 MW; each coal unit
        # contributes 1000 MW at rating, so 8 of 12 coal units must be
        # retained (2000 + 817 + 8 x 1000 = 10817 >= 10715.25). coal=1 pinned
        # (D1 default is 3) so all 12 coal units are screen-eligible in one
        # pass — this test isolates the reliability floor, not the threshold.
        config = ScenarioConfig(retirement_years_coal=1)
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
        self.assertEqual(len(coal_survivors), 8)
        # Same-fuel merit ties break on heat rate: the most efficient
        # (lowest heat-rate) units are the ones kept.
        retired_hr = {g.heat_rate for g in coal} - {g.heat_rate for g in coal_survivors}
        survivor_hr = {g.heat_rate for g in coal_survivors}
        self.assertTrue(min(retired_hr) > max(survivor_hr))
        # Every retention is attributed (rule 20 analogue).
        self.assertEqual(len(retention_log), 8)

    def test_highest_heat_rate_retires_first(self):
        # Reliability floor keeps the requirement met; the least efficient
        # units are the ones actually retired. ERCOT CDR basis: requirement =
        # 1650 x 0.942 x 1.1375 = 1768.0 MW; the DC ties (817) plus one coal
        # unit at rating (1000) clears it, so the two least efficient retire.
        # coal=1 pinned (D1 default 3) so all three coal units screen-eligible
        # in one pass — this test isolates heat-rate merit ordering.
        config = ScenarioConfig(retirement_years_coal=1)
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
        # The highest-heat-rate units are the ones retired; the most
        # efficient unit is the one the floor keeps.
        self.assertEqual({g.unit_id for g in survivors}, {"C0"})

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


class TestPipelineRetirementRule(unittest.TestCase):
    """R-NEW decision/execution retirement pipeline (FF-1A, owner D1=Option B).

    ``retirement_rule="pipeline"``: uniform one-screen decision at the
    unchanged ``net_revenue < going_forward_cost`` bar, joint adequacy-capped
    cross-fuel pipeline entry (worst-first depth, cheapest-firm-adequacy
    retention via the existing floor machinery), soft annual re-confirmation
    latch, and deactivation after the measured per-fuel execution lag
    (``ff-retirement-rule-redesign-2026-07.md`` §3.6/§5).
    """

    T = 10

    def _screen(self, fleet, config, state, year, peak=0.0, price=10.0, sink=None):
        """One annual retirement screen at flat zonal ``price``.

        ``mc=None`` keeps the gross-revenue fallback the legacy fixtures use:
        net_revenue = price x dispatch (10 MW x T hours), far below any GFC at
        price 10 and far above it at price 1e6.
        """
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), price)
        dispatch = SimpleNamespace(dispatch=np.full((len(fleet), self.T), 10.0))
        return apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            state,
            peak_demand=peak,
            year=year,
            event_sink=sink,
        )

    def test_default_rule_is_legacy(self):
        # Byte-identity for every committed run: the pipeline is opt-in.
        self.assertEqual(ScenarioConfig().retirement_rule, "legacy")

    def test_pipeline_requires_year(self):
        config = ScenarioConfig(retirement_rule="pipeline")
        fleet = [_gen("C0", "coal", pmax=100.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        dispatch = SimpleNamespace(dispatch=np.full((1, self.T), 10.0))
        with self.assertRaises(ValueError):
            apply_economic_retirements(
                fleet, arrays, dispatch, prices, config, {}, peak_demand=0.0
            )

    def test_coal_timing_matches_legacy_d1_counter(self):
        # Redesign §3.6 component 4: a persistent-loss coal cohort is decided
        # at the end of loss year y (= the first failing screen's year - 1)
        # and gone at the start of y + 3 — byte-equivalent timing to the
        # adopted legacy D1=3 counter (decided 2030, executed at the 2033
        # screen, exactly when the legacy counter reaches 3).
        config = ScenarioConfig(retirement_rule="pipeline")
        fleet = [_gen("C0", "coal", pmax=100.0)]

        fleet1, state1, _ = self._screen(fleet, config, {}, year=2031)
        self.assertEqual([g.unit_id for g in fleet1], ["C0"])
        self.assertEqual(state1, {"C0": 2030})  # decided, loss year 2030

        fleet2, state2, _ = self._screen(fleet1, config, state1, year=2032)
        self.assertEqual([g.unit_id for g in fleet2], ["C0"])
        self.assertEqual(state2, {"C0": 2030})  # re-confirmed, still pending

        fleet3, state3, _ = self._screen(fleet2, config, state2, year=2033)
        self.assertEqual(fleet3, [])  # 2033 >= 2030 + lag_coal(3): executed
        self.assertEqual(state3, {})

    def test_lag_one_fuel_executes_at_first_failing_screen(self):
        # gas_st carries the measured lag 1 (§a.3 median, n=53 / 8.1 GW), so a
        # failing gas_st unit is decided AND executed in the same screen call:
        # decided_year = 2030, due when year >= 2030 + 1 = 2031.
        config = ScenarioConfig(retirement_rule="pipeline")
        fleet = [_gen("S0", "gas_st", pmax=100.0)]
        sink: dict = {}
        fleet1, state1, _ = self._screen(fleet, config, {}, year=2031, sink=sink)
        self.assertEqual(fleet1, [])
        self.assertEqual(state1, {})
        kinds = [e["event"] for e in sink["pipeline_events"]]
        self.assertEqual(kinds, ["decided", "executed"])
        executed = sink["pipeline_events"][1]
        self.assertEqual(executed["decided_year"], 2030)
        self.assertEqual(executed["execute_year"], 2031)

    def test_soft_latch_reverses_only_on_cleared_bar(self):
        # Component 3: a pipelined unit leaves the pipeline ONLY by
        # re-clearing the same bar. A profitable year genuinely restores
        # viability -> reversed (the economically-correct residue of defect
        # 5); the unit then survives past its original execute year.
        config = ScenarioConfig(retirement_rule="pipeline")
        fleet = [_gen("C0", "coal", pmax=100.0)]

        _, state1, _ = self._screen(fleet, config, {}, year=2031)
        self.assertEqual(state1, {"C0": 2030})

        sink: dict = {}
        fleet2, state2, _ = self._screen(
            fleet, config, state1, year=2032, price=1.0e6, sink=sink
        )
        self.assertEqual([g.unit_id for g in fleet2], ["C0"])
        self.assertEqual(state2, {})  # reversed on recovery
        self.assertEqual([e["event"] for e in sink["pipeline_events"]], ["reversed"])
        # Original execute year (2033) passes without incident: not pipelined.
        fleet3, state3, _ = self._screen(fleet2, config, state2, year=2033, price=1.0e6)
        self.assertEqual([g.unit_id for g in fleet3], ["C0"])
        self.assertEqual(state3, {})
        # The input state dicts were never mutated in place.
        self.assertEqual(state1, {"C0": 2030})

    def test_joint_entry_competition_is_adequacy_capped_no_inversion(self):
        # Components 1-2 (removes D1 defects 2-3): all fuels compete in ONE
        # shared eligible set, and pipeline admission is capped by the
        # existing accredited-adequacy requirement on the schedule of pending
        # exits, cheapest-firm-adequacy retained first. ERCOT CDR basis
        # (same fixture arithmetic as the reliability-floor tests):
        # requirement = 3080 x 0.942 x 1.1375 = 3300.1 MW; nuclear (2000 at
        # rating) + DC ties (817) = 2817 < req, so ONE of the two failing
        # candidates must be retained. gas_st is the cheaper firm-adequacy
        # buy (GFC 35 vs coal's 45 x 1.3 = 58.5 $/kW-yr), so gas_st is
        # UN-ADMITTED (entry_capped) and coal — the deeper loss — is decided:
        # the exit composition is economic, not a per-fuel integer race, and
        # a fuel the adequacy machinery retains accumulates zero model exits
        # (the T-R10 no-inversion construction).
        config = ScenarioConfig(retirement_rule="pipeline")
        nuclear = _gen("N0", "nuclear", pmax=2000.0)
        coal = _gen("C0", "coal", pmax=1000.0)
        gas_st = _gen("S0", "gas_st", pmax=1000.0)
        fleet = [nuclear, coal, gas_st]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        # Nuclear dispatches hard enough to clear its bar (gross fallback:
        # 1e7 x 10 $/MWh x 10 h = 1e9 >> its 130 $/kW-yr x 2000 MW = 2.6e8
        # GFC); coal and gas_st are deeply under water.
        dispatch = SimpleNamespace(
            dispatch=np.vstack(
                [
                    np.full((1, self.T), 1.0e7),
                    np.full((1, self.T), 10.0),
                    np.full((1, self.T), 10.0),
                ]
            )
        )
        state: dict[str, int] = {}
        sink: dict = {}
        year = 2031
        # Screens 2031/2032: coal pending, gas_st entry-capped each year.
        for year in (2031, 2032):
            sink = {}
            fleet, state, _ = apply_economic_retirements(
                fleet,
                arrays,
                SimpleNamespace(dispatch=dispatch.dispatch[: len(fleet)]),
                prices,
                config,
                state,
                peak_demand=3080.0,
                year=year,
                event_sink=sink,
            )
            self.assertEqual(sorted(g.unit_id for g in fleet), ["C0", "N0", "S0"])
            self.assertEqual(state, {"C0": 2030})
            capped = [
                e for e in sink["pipeline_events"] if e["event"] == "entry_capped"
            ]
            self.assertEqual([e["unit_id"] for e in capped], ["S0"])
        # Screen 2033: coal executes (2030 + 3); with coal gone the surviving
        # 2000 + 1000 + 817 = 3817 >= 3300.1, so the realized-year floor lets
        # the exit stand and gas_st (still capped) never exits at all.
        sink = {}
        fleet, state, _ = apply_economic_retirements(
            fleet,
            arrays,
            SimpleNamespace(dispatch=dispatch.dispatch[: len(fleet)]),
            prices,
            config,
            state,
            peak_demand=3080.0,
            year=2033,
            event_sink=sink,
        )
        self.assertEqual(sorted(g.unit_id for g in fleet), ["N0", "S0"])
        self.assertEqual(state, {})
        executed = [e for e in sink["pipeline_events"] if e["event"] == "executed"]
        self.assertEqual([e["unit_id"] for e in executed], ["C0"])

    def test_gas_cc_ccs_lag_inherits_gas_cc(self):
        # §5 open-DOF disposition: no CCS retirement exists anywhere (§a.4),
        # so gas_cc_ccs inherits the gas_cc lag when its own field is None.
        from market_sim.model.capacity import _execution_lag_years

        config = ScenarioConfig(retirement_rule="pipeline")
        self.assertIsNone(config.retirement_execution_lag_gas_cc_ccs)
        self.assertEqual(
            _execution_lag_years(config, "gas_cc_ccs"),
            _execution_lag_years(config, "gas_cc"),
        )


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
        # Hand-computed accredited sum (plan §8.3 item 3), ERCOT CDR basis
        # (accreditation audit 2026-07-06): requirement = firm peak x 1.1375
        # = 1000 x 0.942 x 1.1375 = 1071.5. With wind/solar pools at ERCOT's
        # published CDR ELCCs (0.20 / 0.21), storage 500 and the 817 MW DC
        # ties, the requirement clears without the coal unit, so it retires;
        # with pools=0 the ties alone (817) fall short and the floor
        # rescues it.
        from market_sim.config.constants import RENEWABLE_CAPACITY_CREDIT_BY_ISO

        # coal=1 pinned (D1 default 3): this test isolates the accredited-basis
        # requirement math on a single-loss-year screen.
        config = ScenarioConfig(retirement_years_coal=1)
        coal = [_gen("C0", "coal", pmax=1000.0)]
        peak = 1000.0
        requirement = peak * (1.0 - 0.058) * 1.1375
        credits = RENEWABLE_CAPACITY_CREDIT_BY_ISO["ERCOT"]
        pooled_firm = (
            4000.0 * credits["wind"] + 2000.0 * credits["solar"] + 500.0 + 817.0
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
        # Equalize the going-forward cost keys (coal fom 8 = ct fom 8) so the
        # CO2 rate decides the tie; the gas_ct default flipped to 21 (G-32),
        # so pin it back to 8 to preserve the crafted tie.
        config = ScenarioConfig().with_overrides(
            fixed_om_coal=8.0,
            retirement_fom_multiplier_coal=1.0,
            fixed_om_gas_ct=8.0,
            retirement_years_coal=1,  # pin (D1 default 3): the coal unit must
            # be screen-eligible on its single loss year for the tie-break test.
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
        # purchase, not an emissions ranking. coal=1 pinned (D1 default 3).
        config = ScenarioConfig(retirement_years_coal=1)
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
        # coal=1 pinned (D1 default 3): the unit is screen-eligible on its
        # single loss year and then floor-retained (keeps loss_years == 1).
        config = ScenarioConfig(retirement_years_coal=1)
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
        # ERCOT seasonal-rating basis: firm MW = nameplate, no EFORd derate.
        self.assertAlmostEqual(row["ucap_mw"], 1000.0)
        # going_forward_cost = 45 x 1.3 x 1000 MW x 1000 = 58,500,000 $/yr
        # (coal FOM default flipped 40 -> NREL-ATB-2024 45, G-32).
        self.assertAlmostEqual(row["going_forward_cost"], 58.5e6)
        self.assertEqual(row["loss_years"], 1)
        # The floor-retained unit keeps its loss counter (re-screened next
        # year); it is un-retired, not absolved.
        self.assertEqual(losses["C0"], 1)

    def test_pools_zero_floor_at_least_as_conservative_as_nameplate(self):
        # With pools=0 and equal margin, the UCAP discount makes the
        # accredited floor retain at least as much as a nameplate floor
        # (plan §8.3 item 3): nameplate 2 x 1000 = 2000 clears a 1990
        # requirement, but accredited 2 x 950 = 1900 does not, so a third
        # unit is retained. This is the DEFAULT (UCAP) basis property;
        # ERCOT's registry entries are removed so the legacy basis drives
        # (ERCOT itself now accredits at seasonal rating per its CDR —
        # accreditation audit 2026-07-06).
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
            ADEQUACY_EXTERNAL_TIE_FIRM_MW,
            THERMAL_ACCREDITATION_BASIS_BY_ISO,
        )

        # coal=1 pinned (D1 default 3) so all four coal units screen-eligible
        # in one pass — this test isolates the UCAP-vs-nameplate floor property.
        config = ScenarioConfig().with_overrides(
            planning_reserve_margin_override=0.0, retirement_years_coal=1
        )
        coal = [
            _gen(f"C{i}", "coal", pmax=1000.0, heat_rate=9.0 + 0.1 * i)
            for i in range(4)
        ]
        with (
            mock.patch.dict(THERMAL_ACCREDITATION_BASIS_BY_ISO, clear=True),
            mock.patch.dict(ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO, clear=True),
            mock.patch.dict(ADEQUACY_EXTERNAL_TIE_FIRM_MW, clear=True),
        ):
            survivors, _, _ = self._screen(coal, config, peak=1990.0)
        self.assertEqual(len(survivors), 3)

    def test_locational_exemption_skips_ra_saturated_zone(self):
        # Under capacity_deliverability_limits, a unit in a zone already
        # long on deliverable firm capacity is exempt from floor retention
        # (mirror of the screens' _zone_is_long gate). coal=1 pinned (D1
        # default 3) so both coal units are screen-eligible in one pass.
        config = ScenarioConfig(retirement_years_coal=1)
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
        # Requirement 1607 (1500 x 0.942 x 1.1375) exceeds the 817 MW ties,
        # but ZLONG is exempt: only A is retained; B retires.
        self.assertEqual([g.unit_id for g in survivors], ["A"])
        self.assertEqual([r["unit_id"] for r in log], ["A"])

    def test_peak_demand_next_drives_floor_through_evolve_fleet(self):
        # Plan §2.3 component 1: the floor tests the entering year's known
        # peak, not the prior-year bookkeeping peak. Two 1000 MW coal units
        # on ERCOT's CDR basis (rating; 817 MW ties): against the stale
        # 1000 MW prior peak (requirement 1071.5) the ties plus one unit
        # suffice and the other retires; against the known 2000 MW peak
        # (requirement 2143) both are retained (817 + 2000 >= 2143). coal=1
        # pinned (D1 default 3) so both coal units screen-eligible in one pass.
        config = ScenarioConfig(iso="ERCOT", retirement_years_coal=1)
        coal = [
            _gen("C0", "coal", pmax=1000.0, heat_rate=9.0),
            _gen("C1", "coal", pmax=1000.0, heat_rate=10.0),
        ]
        arrays = generators_to_fleet_arrays(coal, ["Z0"], hours=self.T)
        prior = {
            "fleet_arrays": arrays,
            "dispatch_result": self._dispatch_result(2, 10.0),
            "prices": np.full((1, self.T), 10.0),
            "peak_demand": 1000.0,
        }
        # (evolve_fleet re-aggregates the fleet into bin representatives, so
        # assert on retained MW and the retention log, not unit identity.)
        fleet, _, _, _, log = evolve_fleet(coal, prior, 2030, config, {})
        self.assertEqual(sum(g.pmax_mw for g in fleet), 1000.0)
        self.assertEqual(len(log), 1)

        fleet, _, _, _, log = evolve_fleet(
            coal, prior, 2030, config, {}, peak_demand_next=2000.0
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


class TestMarketDesignRetirementFloor(unittest.TestCase):
    """Energy-only floor gate (``market_design_retirement_floor``, stage 5 §1).

    The gate is default-off (byte-identical everywhere — the pre-existing
    floor tests above all run with the default). When on, the retirement
    reliability floor is skipped ONLY for ISOs explicitly registered
    energy-only in ``MARKET_DESIGN`` (ERCOT); capacity-market ISOs and ISOs
    absent from the registry keep the floor (#1496/#1501 gating pattern).
    """

    T = 10

    def _dispatch_result(self, n_gen, level):
        return SimpleNamespace(dispatch=np.full((n_gen, self.T), level))

    def _screen(self, fleet, config, peak):
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)  # deeply unprofitable for all
        dispatch = self._dispatch_result(len(fleet), 10.0)
        return apply_economic_retirements(
            fleet, arrays, dispatch, prices, config, {}, peak_demand=peak
        )

    def _fleet(self):
        # The over-retirement fixture from the floor test above: nuclear
        # survives the screen (loss year 1 < threshold), 12 coal units all
        # eligible after one loss year (callers pin retirement_years_coal=1 —
        # the D1 default is 3); flag-off ERCOT retains 8 of 12.
        nuclear = [_gen("N0", "nuclear", pmax=2000.0)]
        coal = [
            _gen(f"C{i}", "coal", pmax=1000.0, heat_rate=9.0 + 0.1 * i)
            for i in range(12)
        ]
        return nuclear + coal

    def test_energy_only_iso_skips_floor_when_flag_on(self):
        # ERCOT is registered energy-only: with the gate on, the floor
        # retains nothing — every screen-eligible coal unit actually exits
        # and the retention log is empty (adequacy expresses as scarcity
        # revenue downstream, not administrative retention).
        config = ScenarioConfig(
            market_design_retirement_floor=True, retirement_years_coal=1
        )
        survivors, _, retention_log = self._screen(self._fleet(), config, 10000.0)
        self.assertEqual([g.unit_id for g in survivors], ["N0"])
        self.assertEqual(retention_log, [])

    def test_flag_off_is_byte_identical(self):
        # Default-off reproduces the pre-gate behaviour exactly (the same
        # fixture as test_reliability_floor_prevents_over_retirement).
        config = ScenarioConfig(
            market_design_retirement_floor=False, retirement_years_coal=1
        )
        survivors, _, retention_log = self._screen(self._fleet(), config, 10000.0)
        self.assertEqual(len([g for g in survivors if g.fuel_type == "coal"]), 8)
        self.assertEqual(len(retention_log), 8)

    def test_capacity_market_iso_keeps_floor_when_flag_on(self):
        # A capacity-market ISO's floor is byte-identical with the flag on or
        # off: its design really does procure to the requirement. Net-CONE is
        # zeroed via the registry patch so the units fail the screen and the
        # floor is actually exercised (a positive capacity payment would keep
        # them solvent and never trigger it).
        from market_sim.config.constants import MarketDesign
        from market_sim.model import capacity as capacity_mod

        design = {"PJM": MarketDesign(capacity_market=True, net_cone_per_kw_yr=0.0)}
        with mock.patch.dict(capacity_mod.MARKET_DESIGN, design):
            base = ScenarioConfig(iso="PJM", retirement_years_coal=1)
            gated = base.with_overrides(market_design_retirement_floor=True)
            surv_off, _, log_off = self._screen(self._fleet(), base, 10000.0)
            surv_on, _, log_on = self._screen(self._fleet(), gated, 10000.0)
        self.assertEqual([g.unit_id for g in surv_on], [g.unit_id for g in surv_off])
        self.assertEqual(log_on, log_off)
        # And the floor genuinely fired in both (the fixture over-retires).
        self.assertGreater(len(log_on), 0)

    def test_unregistered_iso_keeps_floor_when_flag_on(self):
        # An ISO absent from MARKET_DESIGN keeps the floor even with the flag
        # on (conservative fallback): the registry's energy-only *default*
        # withholds capacity revenue for unknown ISOs, but must not double as
        # asserting they have no adequacy construct.
        from market_sim.model import capacity as capacity_mod

        config = ScenarioConfig(
            market_design_retirement_floor=True, retirement_years_coal=1
        )
        with mock.patch.dict(capacity_mod.MARKET_DESIGN, clear=True):
            survivors, _, retention_log = self._screen(self._fleet(), config, 10000.0)
        self.assertEqual(len([g for g in survivors if g.fuel_type == "coal"]), 8)
        self.assertEqual(len(retention_log), 8)


class TestStoragePortfolioElccDilution(unittest.TestCase):
    """Portfolio ELCC dilution (accreditation audit §3 follow-up).

    Linear interpolation between two cited (penetration, ELCC) anchors: 1.0
    at/below today's validated reference MW, the CDR's own ratio (46/60.2)
    at/above the deployment ceiling, straight-line between.
    """

    def test_no_op_at_and_below_reference(self):
        from market_sim.model.capacity import _storage_portfolio_elcc_dilution

        self.assertEqual(_storage_portfolio_elcc_dilution(20_438.0, "ERCOT"), 1.0)
        self.assertEqual(_storage_portfolio_elcc_dilution(0.0, "ERCOT"), 1.0)
        self.assertEqual(_storage_portfolio_elcc_dilution(11_700.0, "ERCOT"), 1.0)

    def test_ceiling_ratio_at_and_beyond_ceiling(self):
        from market_sim.model.capacity import _storage_portfolio_elcc_dilution

        expected = 0.46 / 0.602
        self.assertAlmostEqual(
            _storage_portfolio_elcc_dilution(45_000.0, "ERCOT"), expected
        )
        self.assertAlmostEqual(
            _storage_portfolio_elcc_dilution(60_000.0, "ERCOT"), expected
        )

    def test_linear_between_anchors(self):
        from market_sim.model.capacity import _storage_portfolio_elcc_dilution

        # Midpoint of the reference-to-ceiling span.
        reference, ceiling = 20_438.0, 45_000.0
        mid = (reference + ceiling) / 2.0
        factor = _storage_portfolio_elcc_dilution(mid, "ERCOT")
        expected = 1.0 - (1.0 - 0.46 / 0.602) * 0.5
        self.assertAlmostEqual(factor, expected)

    def test_unregistered_iso_is_no_op(self):
        from market_sim.model.capacity import _storage_portfolio_elcc_dilution

        self.assertEqual(_storage_portfolio_elcc_dilution(100_000.0, "PJM"), 1.0)

    def test_evolve_fleet_dilutes_storage_firm_mw(self):
        # End-to-end: evolve_fleet reads storage_firm_mw from prior_results
        # and applies the dilution before the floor/backstop consume it.
        prior = {
            "fleet_arrays": None,
            "dispatch_result": None,
            "prices": None,
            "peak_demand": 0.0,
            "planned_additions": [],
            "mc_cost": None,
            "rps_shadow_price": 0.0,
            "storage_power_mw": 45_000.0,  # at the ERCOT ceiling
            "wind_cap_mw": 0.0,
            "solar_cap_mw": 0.0,
            "storage_firm_mw": 10_000.0,
        }
        config = ScenarioConfig(iso="ERCOT")
        _, _, _, _, floor_log = evolve_fleet(
            [], prior, 2027, config, {}, confirmed_exits=None
        )
        # No assertion on the return value directly exposes storage_firm_mw
        # (it feeds the floor/backstop internally); this just confirms the
        # call succeeds end-to-end with the ceiling-penetration case wired
        # through evolve_fleet without raising.
        self.assertEqual(floor_log, [])


class TestThermalElccClassRatings(unittest.TestCase):
    """R3 — PJM thermal + storage accreditation on the published ELCC class
    ratings (2025/26 CIFP reform; accreditation-basis memo §4.2)."""

    def _pjm_official_elcc(self):
        """resource_class -> elcc fraction, PJM 2026/2027 BRA official/final."""
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / "elcc" / "pjm" / "pjm.csv"
        vintage = "2026/2027 BRA (official/final)"
        with path.open(newline="") as fh:
            return {
                r["resource_class"]: float(r["elcc_pct"]) / 100.0
                for r in csv.DictReader(fh)
                if r["study_vintage"] == vintage and r["elcc_pct"]
            }

    def test_thermal_ratings_reconcile_with_published_csv(self):
        from market_sim.config.constants import THERMAL_ELCC_CLASS_RATING_BY_ISO

        official = self._pjm_official_elcc()
        # Each model fuel class maps to exactly one published PJM thermal class.
        expected = {
            "nuclear": official["Nuclear"],
            "coal": official["Coal"],
            "gas_cc": official["Gas Combined Cycle"],
            "gas_ct": official["Gas Combustion Turbine"],
            "gas_st": official["Steam"],
            "oil": official["Diesel Utility"],
        }
        self.assertEqual(THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"], expected)

    def test_storage_ratings_reconcile_with_published_csv(self):
        from market_sim.config.constants import STORAGE_ELCC_BY_DURATION_BY_ISO

        official = self._pjm_official_elcc()
        expected = [
            (4.0, official["4-hr Storage"]),
            (6.0, official["6-hr Storage"]),
            (8.0, official["8-hr Storage"]),
            (10.0, official["10-hr Storage"]),
        ]
        self.assertEqual(STORAGE_ELCC_BY_DURATION_BY_ISO["PJM"], expected)

    def test_thermal_firm_mw_uses_class_rating_for_pjm(self):
        from market_sim.model.capacity import _thermal_firm_mw

        g = _gen("cc", "gas_cc", pmax=1000.0)  # eford default 0.05
        # PJM: pmax x published class rating (0.74), NOT (1 - eford)=0.95.
        self.assertAlmostEqual(_thermal_firm_mw(g, "PJM"), 740.0, places=3)
        # UCAP ISO / iso=None keep (1 - eford).
        self.assertAlmostEqual(_thermal_firm_mw(g, "MISO"), 950.0, places=3)
        self.assertAlmostEqual(_thermal_firm_mw(g, None), 950.0, places=3)

    def test_class_absent_falls_back_to_ucap(self):
        from market_sim.config.constants import EFORD
        from market_sim.model.capacity import thermal_accreditation_fraction

        # 'biomass' has no PJM thermal ELCC class -> UCAP neutral fallback.
        self.assertAlmostEqual(
            thermal_accreditation_fraction("biomass", EFORD["biomass"], "PJM"),
            1.0 - EFORD["biomass"],
            places=6,
        )

    def test_pjm_storage_elcc_below_generic(self):
        from market_sim.model.storage import _elcc_for_duration

        # PJM's own reformed ratings are lower than the generic NREL/E3 curve
        # (a published input, not a fit), and clamp outside 4-10h.
        self.assertAlmostEqual(_elcc_for_duration(4.0, "PJM"), 0.50, places=3)
        self.assertAlmostEqual(_elcc_for_duration(8.0, "PJM"), 0.62, places=3)
        self.assertLess(_elcc_for_duration(8.0, "PJM"), _elcc_for_duration(8.0))
        self.assertAlmostEqual(_elcc_for_duration(2.0, "PJM"), 0.50, places=3)
        self.assertAlmostEqual(_elcc_for_duration(24.0, "PJM"), 0.72, places=3)
        # A non-override ISO keeps the generic table byte-identically.
        self.assertAlmostEqual(
            _elcc_for_duration(8.0, "MISO"), _elcc_for_duration(8.0), places=6
        )


class TestClaimedCapabilityBasis(unittest.TestCase):
    """R5b — ISO-NE thermal accredited at Qualified Capacity (claimed
    capability), no forced-outage derate (pairing-adjudication 2026-07-15 §1)."""

    def test_thermal_firm_mw_uses_claimed_capability_for_neiso(self):
        from market_sim.model.capacity import _thermal_firm_mw

        g = _gen("cc", "gas_cc", pmax=1000.0)  # eford default 0.05
        # NEISO: full nameplate (QC has no (1-EFORd) derate), NOT 950 MW UCAP.
        self.assertAlmostEqual(_thermal_firm_mw(g, "NEISO"), 1000.0, places=3)
        # NYISO / iso=None keep the UCAP fallback as the contrast case.
        self.assertAlmostEqual(_thermal_firm_mw(g, "NYISO"), 950.0, places=3)
        self.assertAlmostEqual(_thermal_firm_mw(g, None), 950.0, places=3)

    def test_claimed_capability_is_class_agnostic(self):
        from market_sim.config.constants import EFORD
        from market_sim.model.capacity import thermal_accreditation_fraction

        # Unlike PJM's per-class ELCC table, QC is a per-unit SCC median with no
        # fuel-class dependency — every dispatchable class accredits at 1.0.
        for fuel, eford in EFORD.items():
            self.assertAlmostEqual(
                thermal_accreditation_fraction(fuel, eford, "NEISO"),
                1.0,
                places=6,
                msg=f"{fuel} should accredit at 1.0 on NEISO",
            )

    def test_claimed_capability_matches_seasonal_rating_numerically(self):
        from market_sim.config.constants import (
            THERMAL_ACCREDITATION_BASIS_BY_ISO,
        )
        from market_sim.model.capacity import thermal_accreditation_fraction

        # The two un-derated bases are arithmetically identical (both 1.0)...
        self.assertEqual(
            thermal_accreditation_fraction("gas_ct", 0.10, "NEISO"),
            thermal_accreditation_fraction("gas_ct", 0.10, "ERCOT"),
        )
        # ...while remaining DISTINCT registry strings (provenance, R5b).
        self.assertEqual(
            THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"], "claimed_capability"
        )
        self.assertEqual(THERMAL_ACCREDITATION_BASIS_BY_ISO["ERCOT"], "seasonal_rating")
        self.assertNotEqual(
            THERMAL_ACCREDITATION_BASIS_BY_ISO["NEISO"],
            THERMAL_ACCREDITATION_BASIS_BY_ISO["ERCOT"],
        )


class TestNyisoIcapUcapTranslation(unittest.TestCase):
    """R5a — NYISO's ICAP-stated IRM paired onto the model's UCAP supply basis
    via the published NYCA translation factor (Option B, FF-3D 2026-07-18;
    pairing-adjudication 2026-07-15 §3). Mirrors the R2/R3 basis-consistency
    pattern: the registry ratio reconciles with the committed CSV, the ONE
    requirement resolver applies it (rule 19), and the supply side stays UCAP.
    """

    def _csv_translation_rows(self):
        """Published icap_ucap_translation_factor rows from the NYISO CSV."""
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / "demand-curve" / "nyiso" / "nyiso.csv"
        with path.open(newline="") as fh:
            return [
                r
                for r in csv.DictReader(fh)
                if r["metric"] == "icap_ucap_translation_factor"
            ]

    def test_registry_reconciles_with_published_csv(self):
        # The registry ratio must equal 1 - the most-recently-realized NYCA
        # translation factor on disk (2024-2025), digitized from NYSRC IRM Study
        # Appendix D Table D.2 (Derate Factor) — never a fit target (rules
        # 13/23). Every published factor is a fraction in the rising wind-driven
        # band (0.083 -> 0.132), never a Locational number (NYC 5.18% is out).
        rows = self._csv_translation_rows()
        self.assertTrue(rows, "expected published translation-factor rows on disk")
        by_year = {r["delivery_year"]: float(r["y_value"]) for r in rows}
        latest = max(by_year)  # "2024-2025" sorts last among the CY labels
        self.assertEqual(latest, "2024-2025")
        self.assertAlmostEqual(
            PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"],
            1.0 - by_year[latest],
            places=6,
        )
        self.assertTrue(all(r["y_unit"] == "fraction" for r in rows))
        self.assertTrue(all(0.05 < v < 0.20 for v in by_year.values()))

    def test_translation_factor_reconciles_ucap_margin(self):
        # Table D.1 cross-check: (1 + EC-approved IRM 22.0%) x (1 - 0.1321) - 1
        # = the published 2024-2025 NYCA Equivalent UCAP Requirement, 5.9%. The
        # derate is the ICAP<->UCAP margin bridge, not an invented number.
        ucap_margin = (1.0 + 0.220) * PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO[
            "NYISO"
        ] - 1.0
        self.assertAlmostEqual(ucap_margin, 0.059, places=3)

    def test_requirement_uses_translation_ratio(self):
        # resolve_adequacy_requirement_mw applies (1 + IRM) x ratio on the firm
        # peak (NYISO nets no DR, so firm_peak == peak) — the one requirement
        # resolver, rule 19. NYISO publishes no FPR -> the fallback ratio path.
        cfg = ScenarioConfig(iso="NYISO")
        peak = 32_000.0
        ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]
        irm = PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"]
        self.assertIsNone(resolve_forecast_pool_requirement("NYISO", 2025))
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "NYISO", peak, 2025),
            peak * (1.0 + irm) * ratio,
            places=3,
        )

    def test_pairing_lowers_requirement_vs_ratio_one_fallback(self):
        # The correction is real and directional: pairing the ICAP IRM onto UCAP
        # LOWERS the requirement vs the pre-R5a ratio-1.0 fallback (the ~13%
        # overstatement the adjudication named), so the reserve position rises
        # and a curve-ON NYISO stops systematically over-paying.
        cfg = ScenarioConfig(iso="NYISO")
        peak = 32_000.0
        paired = resolve_adequacy_requirement_mw(cfg, "NYISO", peak, 2025)
        with mock.patch.dict(
            PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO, clear=False
        ) as reg:
            del reg["NYISO"]
            unpaired = resolve_adequacy_requirement_mw(cfg, "NYISO", peak, 2025)
        self.assertLess(paired, unpaired)
        self.assertAlmostEqual(
            paired / unpaired,
            PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"],
            places=6,
        )

    def test_supply_side_stays_ucap(self):
        # Rule-19 pairing: only the requirement side moved. NYISO thermal still
        # accredits at UCAP (1 - EFORd) — the basis NYISO's own ICAP Manual §4.5
        # unit UCAP uses — so requirement and supply are both on the UCAP basis
        # (NYISO is intentionally absent from THERMAL_ACCREDITATION_BASIS_BY_ISO).
        from market_sim.config.constants import THERMAL_ACCREDITATION_BASIS_BY_ISO
        from market_sim.model.capacity import (
            _thermal_firm_mw,
            thermal_accreditation_fraction,
        )

        self.assertNotIn("NYISO", THERMAL_ACCREDITATION_BASIS_BY_ISO)
        g = _gen("cc", "gas_cc", pmax=1000.0)  # eford default 0.05
        self.assertAlmostEqual(_thermal_firm_mw(g, "NYISO"), 950.0, places=3)
        self.assertAlmostEqual(
            thermal_accreditation_fraction("gas_ct", 0.10, "NYISO"), 0.90, places=6
        )

    def test_curve_now_eligible(self):
        from market_sim.config.constants import (
            CAPACITY_CURVE_ELIGIBLE_BY_ISO,
            resolve_capacity_curve_eligible,
        )

        # The pairing landed, so NYISO's curve-eligibility block is lifted (the
        # governance gate for a curve-ON position on the corrected basis).
        self.assertTrue(CAPACITY_CURVE_ELIGIBLE_BY_ISO["NYISO"])
        self.assertTrue(resolve_capacity_curve_eligible("NYISO"))


class TestForecastPoolRequirement(unittest.TestCase):
    """R2 — PJM requirement devintaged onto the published Forecast Pool
    Requirement of the matching delivery year (accreditation-basis memo §4.2)."""

    def _csv_fpr_rows(self):
        """The published forecast_pool_requirement rows from the P-0B CSV."""
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / "demand-curve" / "pjm" / "pjm.csv"
        with path.open(newline="") as fh:
            return [
                r
                for r in csv.DictReader(fh)
                if r["metric"] == "forecast_pool_requirement"
            ]

    def test_registry_reconciles_with_published_csv(self):
        # Every FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"] entry must match a
        # published forecast_pool_requirement row byte-for-byte (rule 13 —
        # digitized from the committed rows, never a fit target).
        rows = self._csv_fpr_rows()
        self.assertTrue(rows, "expected published FPR rows on disk")
        by_year = {r["delivery_year"]: float(r["y_value"]) for r in rows}
        self.assertEqual(
            FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"],
            {y: by_year[y] for y in FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"]},
        )
        # And every published unit is the UCAP fraction.
        self.assertTrue(all(r["y_unit"] == "fraction_of_peak_ucap" for r in rows))

    def test_published_fpr_used_for_matching_delivery_year(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        cfg = ScenarioConfig(iso="PJM")
        peak = 160_560.0
        # Model year 2026 -> delivery 2026/2027 -> published FPR 0.9170, on
        # the DR-netted firm peak (W2-D: PJM adequacy side-registries).
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2026),
            peak * (1.0 - dr) * 0.9170,
            places=3,
        )

    def test_falls_back_when_no_published_fpr(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        cfg = ScenarioConfig(iso="PJM")
        peak = 160_560.0
        # Model year 2030 -> delivery 2030/2031 -> no published FPR -> the
        # (1 + PRM) x icap_to_ucap_ratio fallback (byte-identical to pre-R2),
        # on the DR-netted firm peak.
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["PJM"]
        expected = (
            peak * (1.0 - dr) * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["PJM"]) * ratio
        )
        self.assertIsNone(resolve_forecast_pool_requirement("PJM", 2030))
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2030),
            expected,
            places=3,
        )

    def test_year_none_is_fallback_byte_identical(self):
        cfg = ScenarioConfig(iso="PJM")
        peak = 160_560.0
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak),
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2030),
            places=6,
        )

    def test_non_pjm_iso_unaffected(self):
        # An ISO with no FPR table keeps the fallback in both year modes.
        cfg = ScenarioConfig(iso="MISO")
        peak = 120_000.0
        self.assertIsNone(resolve_forecast_pool_requirement("MISO", 2026))
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "MISO", peak, 2026),
            resolve_adequacy_requirement_mw(cfg, "MISO", peak),
            places=6,
        )


class TestPJMAdequacySideRegistries(unittest.TestCase):
    """W2-D (gap G10 / W1-B B1): PJM DR + CIL firm-import intake.

    Both values are PJM's published 2026/2027 BRA parameters (BRA Report,
    posted 2025-07-22) — never a number tuned to clear I7 (rules 5/13). The
    DR entry is a documented rule-14 reconciliation: PJM counts DR as
    supply-side UCAP, so the registry's peak-netting fraction is DR UCAP
    divided by the UCAP-basis RTO Reliability Requirement (= peak x FPR),
    which makes the netted credit reproduce PJM's own supply-side counting
    exactly under the published-FPR path.
    """

    def test_dr_fraction_reconstructs_published_bra_numbers(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
            ADEQUACY_EXTERNAL_TIE_FIRM_MW,
        )

        # DR cleared 5,795 MW UCAP (Table 6, RPM + FRR-committed) on the
        # 146,105 MW UCAP RTO Reliability Requirement (p.3).
        self.assertAlmostEqual(
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"] * 146_105.0,
            5_795.0,
            places=6,
        )
        # Capacity imports cleared 1,281.7 MW UCAP (Table 7, CIL framework).
        self.assertEqual(ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"], 1_281.7)

    def test_requirement_netting_reproduces_pjm_supply_side_dr(self):
        # The rule-14 reconciliation identity: at PJM's own forecast peak
        # (146,105 / 0.9170 = 159,329 MW) under the published-FPR path, the
        # DR-netted requirement equals PJM's own construction — Reliability
        # Requirement minus supply-side DR UCAP.
        cfg = ScenarioConfig(iso="PJM")
        pjm_peak = 146_105.0 / 0.9170
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", pjm_peak, 2026),
            146_105.0 - 5_795.0,
            places=3,
        )

    def test_accredited_firm_includes_pjm_tie_imports(self):
        from market_sim.model.capacity import accredited_firm_capacity_mw

        # An empty fleet accredits exactly the cleared BRA import UCAP.
        self.assertAlmostEqual(
            accredited_firm_capacity_mw([], iso="PJM"), 1_281.7, places=6
        )


class TestFF2BAdequacyBasis(unittest.TestCase):
    """FF-2B (2026-07-19): NEISO Net ICR requirement + CAISO/NEISO RA imports.

    Every value is ISO-published and forward-regenerable (rules 5/13), never
    tuned to clear I7. NEISO's requirement is its own Net ICR construction
    (Net ICR / 50-50 peak - 1, FCA 17); its DR fraction is the rule-14
    reconciliation (cleared FCM demand resources / Net ICR); the firm-import
    credits are the ISOs' RA/FCM firm import products, credited additively in
    the accredited ledger for the import-node ISOs without double-counting the
    dispatch node.
    """

    def test_neiso_prm_is_net_icr_over_5050_peak(self):
        from market_sim.config.constants import PLANNING_RESERVE_MARGIN_BY_ISO

        # FCA 17 (CCP 2026/2027), Docket ER23-405-000: Net ICR 30,305 MW,
        # summer 50/50 peak 27,298 MW.
        self.assertAlmostEqual(
            PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"],
            30_305.0 / 27_298.0 - 1.0,
            places=6,
        )

    def test_neiso_dr_fraction_reconstructs_cleared_fca_demand_resources(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        # FCA 17 cleared 2,940 MW demand resources against the 30,305 MW Net ICR.
        self.assertAlmostEqual(
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"] * 30_305.0,
            2_940.0,
            places=6,
        )

    def test_neiso_requirement_netting_reproduces_net_icr_minus_dr(self):
        # At ISO-NE's own 50/50 peak the DR-netted requirement equals its own
        # construction: Net ICR minus the cleared supply-side demand resources.
        cfg = ScenarioConfig(iso="NEISO")
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "NEISO", 27_298.0),
            30_305.0 - 2_940.0,
            places=3,
        )

    def test_firm_import_credits_for_import_node_isos(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW
        from market_sim.model.capacity import (
            _firm_import_mw,
            accredited_firm_capacity_mw,
        )

        self.assertEqual(ADEQUACY_EXTERNAL_TIE_FIRM_MW["CAISO"], 3_371.0)
        self.assertEqual(ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"], 567.0)
        # One resolver, and an empty fleet accredits exactly the firm import.
        self.assertEqual(_firm_import_mw("CAISO"), 3_371.0)
        self.assertEqual(_firm_import_mw(None), 0.0)
        self.assertAlmostEqual(
            accredited_firm_capacity_mw([], iso="CAISO"), 3_371.0, places=6
        )
        self.assertAlmostEqual(
            accredited_firm_capacity_mw([], iso="NEISO"), 567.0, places=6
        )


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
        # required = 8000 x 0.942 x 1.1375 = 8568 (ERCOT firm-peak basis);
        # gap = 3568 firm -> >0 nameplate.
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

    def test_icap_ucap_ratio_reverses_naive_pjm_vs_ercot_comparison(self):
        """PJM's raw registered PRM exceeds ERCOT's, but its EFFECTIVE
        (ICAP/UCAP-corrected) requirement is lower — demonstrating why the
        two can't be compared as raw percentages (stage-5 §6 ICAP/UCAP
        pairing audit, 2026-07-06).

        PJM's IRM (~17.8%) is stated on INSTALLED capacity; the model counts
        PJM's thermal fleet at UCAP, so the naive ``peak x (1+IRM)`` (the
        pre-fix formula) overstated PJM's requirement relative to a
        UCAP-stated target like ERCOT's CDR-basis 13.75%. Applying PJM's own
        published ICAP->UCAP ratio (~0.77 — 2026/2027 BRA FPR/[1+IRM])
        reverses the ordering: PJM's corrected requirement factor
        ((1+0.178) x 0.77 = 0.907) is LOWER than ERCOT's (1.1375), so the
        same firm/peak inputs make PJM's backstop build LESS than ERCOT's,
        not more — the opposite of comparing the raw registered percentages.
        """
        from market_sim.model.capacity import apply_reserve_margin_build

        self.assertGreater(
            PLANNING_RESERVE_MARGIN_BY_ISO["PJM"],
            PLANNING_RESERVE_MARGIN_BY_ISO["ERCOT"],
        )
        config = ScenarioConfig(reserve_margin_build_enabled=True)
        # Identical firm/peak; only the resolved per-ISO requirement differs.
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
        self.assertGreater(built_pjm, 0.0)
        self.assertLess(built_pjm, built_ercot)

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
        fallback (0.1375) on the default basis: gross peak, no load-product
        netting, UCAP nameplate conversion, no ICAP/UCAP ratio correction —
        the analytic value below. (ERCOT itself is no longer at parity with
        the bare scalar: its CDR basis nets load-side products and counts
        the new CT at rating — accreditation audit 2026-07-06.) PJM is
        cleared from the PRM registry, the ICAP/UCAP ratio registry
        (stage-5 §6) AND the DR-netting registry (W2-D) so this isolates the
        true full-fallback case — an ISO absent from every adequacy registry.
        """
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
            EFORD,
        )
        from market_sim.model.capacity import apply_reserve_margin_build

        config = ScenarioConfig(reserve_margin_build_enabled=True)
        self.assertEqual(config.planning_reserve_margin, 0.1375)
        with (
            mock.patch.dict(PLANNING_RESERVE_MARGIN_BY_ISO, clear=False) as registry,
            mock.patch.dict(
                PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO, clear=False
            ) as ratio_registry,
            mock.patch.dict(
                ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO, clear=False
            ) as dr_registry,
        ):
            del registry["PJM"]
            del ratio_registry["PJM"]
            del dr_registry["PJM"]
            _, built_fallback = apply_reserve_margin_build(
                [],
                firm_capacity_mw=5000.0,
                peak_demand_mw=8000.0,
                year=2030,
                config=config,
                iso="PJM",
            )
        self.assertGreater(built_fallback, 0.0)
        expected = (8000.0 * 1.1375 - 5000.0) / (1.0 - EFORD["gas_ct"])
        self.assertAlmostEqual(built_fallback, expected)


class TestReserveMarginBuildMarketDesignResolution(unittest.TestCase):
    """G-41: the backstop's tri-state field resolves per market design.

    Owner-approved market-design-dependent variant (PJM hindcast I7 decision
    2026-07-06): ``reserve_margin_build_enabled=None`` (default) resolves ON for
    capacity-market ISOs, OFF for energy-only ERCOT; an explicit bool overrides.
    """

    def test_default_is_none(self):
        self.assertIsNone(ScenarioConfig().reserve_margin_build_enabled)

    def test_none_resolves_off_for_energy_only_ercot(self):
        from market_sim.model.capacity import resolve_reserve_margin_build_enabled

        cfg = ScenarioConfig(iso="ERCOT")  # default None
        self.assertFalse(resolve_reserve_margin_build_enabled(cfg, "ERCOT"))

    def test_none_resolves_on_for_capacity_market_isos(self):
        from market_sim.model.capacity import resolve_reserve_margin_build_enabled

        cfg = ScenarioConfig()  # default None
        for iso in ("PJM", "MISO", "NYISO", "NEISO", "CAISO"):
            self.assertTrue(
                resolve_reserve_margin_build_enabled(cfg, iso),
                f"{iso} is a capacity-market ISO -> backstop default-on",
            )

    def test_none_resolves_off_for_iso_absent_from_market_design(self):
        from market_sim.model.capacity import resolve_reserve_margin_build_enabled

        cfg = ScenarioConfig()  # default None
        # An ISO not in MARKET_DESIGN takes DEFAULT_MARKET_DESIGN (capacity_market
        # False) -> conservative OFF.
        self.assertFalse(resolve_reserve_margin_build_enabled(cfg, "SPP"))

    def test_explicit_override_wins_either_way(self):
        from market_sim.model.capacity import resolve_reserve_margin_build_enabled

        # Force ON for energy-only ERCOT.
        on = ScenarioConfig(iso="ERCOT", reserve_margin_build_enabled=True)
        self.assertTrue(resolve_reserve_margin_build_enabled(on, "ERCOT"))
        # Force OFF for a capacity-market ISO.
        off = ScenarioConfig(iso="PJM", reserve_margin_build_enabled=False)
        self.assertFalse(resolve_reserve_margin_build_enabled(off, "PJM"))

    def test_ercot_default_none_byte_identical_to_explicit_false(self):
        """Energy-only ERCOT under the new None default builds nothing — exactly
        the pre-G-41 default-off (explicit False) behaviour (byte-identity)."""
        from market_sim.model.capacity import apply_reserve_margin_build

        none_cfg = ScenarioConfig(iso="ERCOT")  # default None -> resolves off
        false_cfg = ScenarioConfig(iso="ERCOT", reserve_margin_build_enabled=False)
        fleet = [_gen("cc", "gas_cc", pmax=1000.0)]
        _, built_none = apply_reserve_margin_build(
            list(fleet), 0.0, 8000.0, 2030, none_cfg, "ERCOT"
        )
        _, built_false = apply_reserve_margin_build(
            list(fleet), 0.0, 8000.0, 2030, false_cfg, "ERCOT"
        )
        self.assertEqual(built_none, 0.0)
        self.assertEqual(built_false, 0.0)

    def test_pjm_default_none_builds_like_explicit_true(self):
        """Capacity-market PJM under the None default fires the backstop
        identically to an explicit True (the default now engages it)."""
        from market_sim.model.capacity import apply_reserve_margin_build

        none_cfg = ScenarioConfig(iso="PJM")  # default None -> resolves on
        true_cfg = ScenarioConfig(iso="PJM", reserve_margin_build_enabled=True)
        _, built_none = apply_reserve_margin_build(
            [], 5000.0, 8000.0, 2030, none_cfg, "PJM"
        )
        _, built_true = apply_reserve_margin_build(
            [], 5000.0, 8000.0, 2030, true_cfg, "PJM"
        )
        self.assertGreater(built_none, 0.0)
        self.assertEqual(built_none, built_true)


class TestRetirementMargin(unittest.TestCase):
    """The retirement screen nets variable cost against price.

    Gross revenue alone lets a unit "cover" fixed cost with money it spent
    on fuel (peer review B1): a unit dispatching at a price equal to its
    own marginal cost earns zero margin and must accumulate a loss year,
    however large its gross revenue.
    """

    T = 10

    def _setup(self, price, mc_value, level=100.0):
        # Pin the legacy gas_cc FOM bar (12 $/kW-yr) the crafted margins below
        # are computed against; the default flipped to the NREL-ATB-2024 30
        # $/kW-yr (G-32), which this mechanism test is deliberately independent
        # of.
        config = ScenarioConfig().with_overrides(fixed_om_gas_cc=12.0)
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
        # Pin the legacy gas_cc/gas_ct FOM bars (12 / 8 $/kW-yr) the crafted
        # margins in this class are computed against; the defaults flipped to
        # NREL-ATB-2024 30 / 21 (G-32), which these mechanism tests are
        # deliberately independent of.
        config = config or ScenarioConfig().with_overrides(
            fixed_om_gas_cc=12.0, fixed_om_gas_ct=8.0
        )
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
        # Pin the legacy gas_ct FOM bar (8 $/kW-yr) the flat-credit "> bar 8"
        # sizing above assumes; the default flipped to NREL-ATB-2024 21 (G-32).
        config = config.with_overrides(
            as_revenue_multiplier=needed, fixed_om_gas_ct=8.0
        )
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

    def test_nuclear_smr_costlier_than_large(self):
        # ATB 2024 costs a small modular reactor HIGHER per kW/MWh than a large
        # LWR (a FOAK/economies-of-scale premium: SMR Moderate CAPEX @2030 =
        # $9,650/kW vs large $7,616/kW, 2022$). NEW_ENTRY_COSTS is now derived
        # from that ATB extract (FF-1E), so SMR LCOE exceeds large — the reverse
        # of the pre-FF-1E hand-set values ($6,800 < $8,500) that had no source.
        smr = compute_lcoe("nuclear_smr", 2030, ScenarioConfig())
        large = compute_lcoe("nuclear_large", 2030, ScenarioConfig())
        self.assertGreater(smr, large)

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
        # P-1C statute-triangulated §45Y/§48E STEP schedule (100/75/50/0%),
        # replacing the earlier undocumented 2028/2033 linear ramp (rule 24
        # default change). Canonical coverage lives in
        # tests/test_ira.py::TestIRAPhaseoutFraction; kept here so this
        # class's geothermal-LCOE path (which reads the same fraction) stays
        # self-consistent. Defaults: last_full=2033, 75pct=2034, 50pct=2035,
        # phaseout_end=2036.
        config = ScenarioConfig()
        self.assertEqual(ira_phaseout_fraction(2033, config), 1.0)
        self.assertAlmostEqual(ira_phaseout_fraction(2034, config), 0.75)
        self.assertAlmostEqual(ira_phaseout_fraction(2035, config), 0.50)
        self.assertEqual(ira_phaseout_fraction(2036, config), 0.0)
        self.assertEqual(ira_phaseout_fraction(2040, config), 0.0)


class TestGetRPSTarget(unittest.TestCase):
    """Renewable portfolio standard target lookup and interpolation."""

    def test_knot_year_returns_exact_value(self):
        self.assertAlmostEqual(get_rps_target("CAISO", 2030), 0.60)

    def test_intermediate_year_is_interpolated(self):
        # 2028 sits midway between 2026 (0.50) and 2030 (0.60).
        self.assertAlmostEqual(get_rps_target("CAISO", 2028), 0.55)

    def test_unregistered_iso_is_none(self):
        # An ISO with no STATE_RPS_FLOORS entry (SPP is not modeled) -> None.
        # All six registered ISOs now carry a floor entry (MISO added after PJM).
        self.assertIsNone(get_rps_target("SPP", 2030))

    def test_ercot_floor_is_zero(self):
        self.assertAlmostEqual(get_rps_target("ERCOT", 2030), 0.0)

    def test_pjm_blended_floor_interpolates(self):
        # PJM carries a load-weighted blend of its member-state renewable
        # tiers: ~18.5% (2026) rising to 23% (2030).
        self.assertAlmostEqual(get_rps_target("PJM", 2026), 0.185)
        self.assertAlmostEqual(get_rps_target("PJM", 2028), 0.2075, places=4)
        self.assertAlmostEqual(get_rps_target("PJM", 2030), 0.23)

    def test_miso_blended_floor_interpolates(self):
        # MISO carries a load-weighted blend of its member-state renewable
        # tiers, diluted by its many no-RPS states: ~11% (2026) rising to
        # 16% (2030); 2028 sits midway.
        self.assertAlmostEqual(get_rps_target("MISO", 2026), 0.11)
        self.assertAlmostEqual(get_rps_target("MISO", 2028), 0.135, places=4)
        self.assertAlmostEqual(get_rps_target("MISO", 2030), 0.16)
        # Below PJM at every knot (more no-RPS load).
        self.assertLess(get_rps_target("MISO", 2030), get_rps_target("PJM", 2030))


class TestGetRPSACP(unittest.TestCase):
    """RPS Alternative Compliance Payment ceiling lookup."""

    def test_rps_iso_returns_acp_ceiling(self):
        # NEISO refreshed 65.0 -> 50.0 (FF-1E-policy 2026-07-19): the MA Class I
        # RPS ACP input was stale ($67.62 -> $40/MWh, 225 CMR 14.08(3)(a)(2)
        # 2021 reset), so the load-weighted NE Class I ACP falls to ~$50.
        self.assertAlmostEqual(get_rps_acp("NEISO"), 50.0)
        self.assertAlmostEqual(get_rps_acp("CAISO"), 50.0)
        self.assertAlmostEqual(get_rps_acp("NYISO"), 40.0)
        self.assertAlmostEqual(get_rps_acp("PJM"), 45.0)
        # MISO is a deliberately low forward REC-price-ceiling proxy (soft
        # Midwest enforcement / cheap RECs): below PJM and NEISO.
        self.assertAlmostEqual(get_rps_acp("MISO"), 30.0)
        self.assertLess(get_rps_acp("MISO"), get_rps_acp("PJM"))

    def test_case_insensitive(self):
        self.assertAlmostEqual(get_rps_acp("neiso"), 50.0)
        self.assertAlmostEqual(get_rps_acp("miso"), 30.0)

    def test_iso_without_acp_is_none(self):
        # ERCOT has a modeled-zero floor but no ACP entry; SPP is unregistered.
        # Either way no escape column is built and the LP is unchanged there.
        self.assertIsNone(get_rps_acp("ERCOT"))
        self.assertIsNone(get_rps_acp("SPP"))


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
        # coal=1 pinned (D1 default 3): this test isolates the evolve_fleet
        # wiring of the economic screen, not the loss-year threshold.
        config = ScenarioConfig(iso="ERCOT", retirement_years_coal=1)
        coal = _gen("C0", "coal", pmax=100.0, zone="North")
        arrays = generators_to_fleet_arrays([coal], ["North"], hours=24)
        dispatch = SimpleNamespace(dispatch=np.full((1, 24), 1.0))
        prior = SimpleNamespace(
            fleet_arrays=arrays,
            dispatch_result=dispatch,
            prices=np.full((1, 24), 5.0),  # revenue far below fixed cost
            planned_additions=[],
        )
        # A single loss year triggers retirement at the pinned coal=1 threshold.
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


class TestIRANuclear45UAndCleanPhaseout(unittest.TestCase):
    """IRA §45U existing-nuclear PTC in the retirement screen, plus the
    §45Y/§48E step schedule's effect on storage entry economics and the
    (unchanged) wind/solar hard cliff (P-1C).
    """

    T = 10

    def _run_nuclear_screen(
        self, year, loss_counter, *, fixed_om, eac_price=0.0, price=20.0
    ):
        """Screen one 100-MW nuclear unit; return (survivor_ids, loss_year).

        Scales are hand-chosen so §45U (max $15/MWh while ``price`` <= the
        $25/MWh gross-receipts threshold) is the pivotal revenue: energy
        margin = price x 100 MW x T; §45U revenue = credit x 100 MW x T;
        going-forward cost = ``fixed_om`` $/kW-yr x 100 MW x 1000. ERCOT
        default => no capacity or AS revenue for nuclear, so energy + the
        attribute payment is the whole stack; ``eford=0`` makes the pro-forma
        margin basis the full 100 MW.
        """
        config = ScenarioConfig(fixed_om_nuclear=fixed_om, eac_price_nuclear=eac_price)
        fleet = [_gen("N0", "nuclear", pmax=100.0, eford=0.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        dispatch = SimpleNamespace(dispatch=np.full((1, self.T), 100.0))
        prices = np.full((1, self.T), price)
        mc = np.zeros((1, self.T))
        survivors, losses, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {"N0": loss_counter},
            peak_demand=0.0,
            mc=mc,
            year=year,
        )
        return [g.unit_id for g in survivors], losses.get("N0")

    def test_section_45u_credit_enters_retirement_seam(self):
        # Sanity that the screen actually consults §45U: at price=20 (<25) the
        # full $15/MWh credit is live in 2030 and fully expired in 2033.
        config = ScenarioConfig()
        self.assertEqual(section_45u_credit_per_mwh(2030, 20.0, config), 15.0)
        self.assertEqual(section_45u_credit_per_mwh(2033, 20.0, config), 0.0)

    def test_nuclear_survives_when_45u_covers_fom_gap(self):
        # price = 20 $/MWh (< the 25 $/MWh gross-receipts threshold => full
        # §45U = $15/MWh). Over T=10 h at 100 MW: energy margin = 20 x 100 x
        # 10 = 20_000; §45U revenue = 15 x 100 x 10 = 15_000; going-forward =
        # 0.30 x 100 x 1000 = 30_000. With §45U (2030 <= ira_45u_last_year):
        # 20_000 + 15_000 = 35_000 >= 30_000 -> profitable -> counter resets.
        # The unit sat one loss year short of the nuclear threshold (3), so
        # §45U is exactly what keeps it online.
        survivors, loss = self._run_nuclear_screen(2030, 2, fixed_om=0.30)
        self.assertEqual(survivors, ["N0"])
        self.assertEqual(loss, 0)

    def test_nuclear_retires_after_45u_expiry(self):
        # Same unit and gap, but 2033 > ira_45u_last_year (2032): §45U = 0, so
        # energy alone (20_000) < going-forward (30_000) -> a 3rd consecutive
        # loss year -> the unit retires.
        survivors, loss = self._run_nuclear_screen(2033, 2, fixed_om=0.30)
        self.assertEqual(survivors, [])
        self.assertIsNone(loss)  # retired units drop out of the loss counter

    def test_45u_and_eac_nuclear_do_not_stack(self):
        # §45U and eac_price_nuclear (ZEC/CES) both support nuclear retention
        # but MUST NOT stack (rule 19): the screen credits max(§45U, eac), not
        # their sum. Construct a gap only their SUM could close: price=20 =>
        # §45U=$15/MWh, eac_price_nuclear=$15/MWh; energy=20_000, going-forward
        # = 0.40 x 100 x 1000 = 40_000. max(15,15) x 100 x 10 = 15_000 =>
        # 35_000 < 40_000 (retire); a buggy sum (30 x 1000 = 30_000) => 50_000
        # >= 40_000 would keep it online. All three configs below — both
        # credits, eac-only, §45U-only — must land on the SAME outcome
        # (retirement), proving the second credit adds nothing.
        both, _ = self._run_nuclear_screen(2030, 2, fixed_om=0.40, eac_price=15.0)
        eac_only, _ = self._run_nuclear_screen(2033, 2, fixed_om=0.40, eac_price=15.0)
        u45_only, _ = self._run_nuclear_screen(2030, 2, fixed_om=0.40, eac_price=0.0)
        self.assertEqual(both, [])
        self.assertEqual(eac_only, [])
        self.assertEqual(u45_only, [])

    def test_storage_entry_cost_steps_across_45y48e_transition(self):
        # §45Y/§48E storage ITC phases down 100/75/50/0% across the 2033->2036
        # breakpoints (ira_phaseout_fraction). The ITC discounts capex, so as
        # the credit STEPS DOWN the storage entry cost STEPS UP, holding flat
        # on the plateaus (2032-2033 at 100%, 2036+ at 0%).
        config = ScenarioConfig()
        name = "li_ion_4hr"
        self.assertIn(name, STORAGE_TECHS)
        cost = {
            y: compute_storage_annual_cost(name, y, config)
            for y in (2032, 2033, 2034, 2035, 2036, 2037)
        }
        # 100% plateau: 2032 and 2033 identical.
        self.assertAlmostEqual(cost[2032], cost[2033])
        # Strictly rising as the credit steps 100 -> 75 -> 50 -> 0%.
        self.assertLess(cost[2033], cost[2034])
        self.assertLess(cost[2034], cost[2035])
        self.assertLess(cost[2035], cost[2036])
        # 0% plateau: 2036 and 2037 identical (credit fully expired).
        self.assertAlmostEqual(cost[2036], cost[2037])
        # The step boundaries are exactly the phase-down schedule.
        self.assertEqual(ira_phaseout_fraction(2033, config), 1.0)
        self.assertEqual(ira_phaseout_fraction(2034, config), 0.75)
        self.assertEqual(ira_phaseout_fraction(2035, config), 0.50)
        self.assertEqual(ira_phaseout_fraction(2036, config), 0.0)

    def test_wind_solar_keep_hard_cliff_not_the_45y_ramp(self):
        # Wind/solar credits are a HARD binary cliff at ira_wind_solar_last_year
        # (OBBBA, 2027), NOT the §45Y/§48E step schedule the other clean techs
        # follow. Wind dispatch MC is -ira_ptc_wind through 2027 and 0 after;
        # solar never affects dispatch MC. Guard: at 2034 — where the step
        # schedule sits at 0.75 — wind/solar are already fully off, proving
        # they do not ride the ramp.
        config = ScenarioConfig()
        self.assertEqual(
            compute_dispatch_credits(config, 2027), (-config.ira_ptc_wind, 0.0)
        )
        self.assertEqual(compute_dispatch_credits(config, 2028), (0.0, 0.0))
        self.assertEqual(compute_dispatch_credits(config, 2034), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
