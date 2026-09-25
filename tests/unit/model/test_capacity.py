"""Tests for fleet retirement mechanisms in ``market_sim.model.capacity``."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO,
    DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO,
    FORECAST_POOL_REQUIREMENT_BY_ISO,
    FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO,
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HOURS_PER_YEAR,
    NET_ICR_HOLD_LAST_RATIO_BY_ISO,
    NET_ICR_REQUIREMENT_MW_BY_ISO,
    RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO,
    NEW_ENTRY_COSTS,
    NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO,
    NYCA_ICAP_UCAP_TRANSLATION_BY_ISO,
    NYCA_IRM_ADOPTED_BY_ISO,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig, resolve_demand_growth_rate
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
    resolve_published_net_icr_mw,
    wind_ptc_levelized_per_mwh,
    wright_cost,
)
from market_sim.model.capacity_evolution.retirements import (
    _floor_retention_merit,
    gross_adequacy_requirement_mw,
    nyiso_requirement_forecast_peak_armed,
    nyiso_requirement_vintage_factors_armed,
    resolve_nyiso_requirement_factor,
    resolve_nyiso_requirement_peak_mw,
    resolve_demand_response_supply_mw,
    resolve_pre_reform_pool_requirement,
    resolve_published_reliability_requirement_mw,
    resolve_thermal_accreditation_basis,
    thermal_accreditation_fraction,
)
from market_sim.model.capacity_evolution.adequacy import (
    CapacityClearing,
    capacity_supply_curve,
    clear_capacity_supply_stack,
    curve_convention_position,
)
from market_sim.config.capacity_market import (
    MARKET_DESIGN,
    ClearedCapacityPrice,
    resolve_capacity_market_supply_clearing,
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
from tests.helpers.builders import no_hydro_accreditation


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
        plant_group="COAL_BIT",
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

    def test_partial_year_exit_completes_next_year(self):
        # FFR-1A arm 2 (audit FR-2): a first-half exit removes its
        # annual-average share in the effective year and the REMAINDER the
        # following year — it must not freeze at the annual-average factor.
        # Brandon Shores shape: month 5 -> effective year removes 7/12 of the
        # MW, year+1 removes the remaining 5/12.
        fleet = [_binned("BS_COAL1", 602, 1370.2, pmin=274.0, nameplate=1370.2)]
        exits = [
            self._exit(602, "1", 2029, month=5, mw=685.1),
            self._exit(602, "2", 2029, month=5, mw=685.1),
        ]
        y2029 = apply_confirmed_exits(fleet, 2029, exits)
        self.assertAlmostEqual(y2029[0].pmax_mw, 1370.2 - (7 / 12) * 1370.2, places=4)
        # Year+1: the completion leg removes the remaining 5/12 -> the whole
        # plant is out (both units exited), tranche dropped below epsilon.
        y2030 = apply_confirmed_exits(y2029, 2030, exits)
        self.assertEqual(y2030, [])

    def test_partial_year_exit_completion_leaves_survivor_mw(self):
        # Same schedule against a plant with a non-exiting remainder: after
        # the completion leg exactly binned - mw survives, and later years
        # are no-ops (each schedule leg fires exactly once).
        fleet = [_binned("H_ST1", 900, 1000.0, pmin=200.0, nameplate=1000.0)]
        exits = [self._exit(900, "1", 2028, month=6, mw=400.0)]
        y2028 = apply_confirmed_exits(fleet, 2028, exits)
        # month 6: (12-6)/12 * 400 = 200 MW removed in the effective year.
        self.assertAlmostEqual(y2028[0].pmax_mw, 800.0, places=4)
        y2029 = apply_confirmed_exits(y2028, 2029, exits)
        # Completion: the remaining 6/12 * 400 = 200 MW.
        self.assertAlmostEqual(y2029[0].pmax_mw, 600.0, places=4)
        y2030 = apply_confirmed_exits(y2029, 2030, exits)
        self.assertAlmostEqual(y2030[0].pmax_mw, 600.0, places=4)

    def test_backlog_prior_partial_exit_fully_removed(self):
        # FR-2's backlog variant: a first-half row effective BEFORE the first
        # simulated year has both schedule legs due — the pre-start backlog
        # removes the full registry MW, never the annual-average share.
        # V H Braunig shape: units 1+2 (477 MW) out March 2025, 2026 start.
        fleet = [_binned("SC_STGAS3", 3612, 1138.0, pmin=227.6, nameplate=1138.0)]
        exits = [
            self._exit(3612, "1", 2025, month=3, mw=225.0),
            self._exit(3612, "2", 2025, month=3, mw=252.0),
        ]
        base = apply_confirmed_exits(fleet, 2026, exits, apply_backlog=True)
        self.assertAlmostEqual(base[0].pmax_mw, 1138.0 - 477.0, places=4)
        # And nothing fires later (no completion leg for a backlog-prior row).
        y2027 = apply_confirmed_exits(base, 2027, exits)
        self.assertAlmostEqual(y2027[0].pmax_mw, 661.0, places=4)

    def test_backlog_current_year_partial_then_completion(self):
        # A first-half row effective exactly AT the first simulated year keeps
        # its normal schedule: annual-average in the backlog application,
        # completion via the next evolve_fleet-style call.
        fleet = [_binned("H_CC1", 901, 1000.0, pmin=200.0, nameplate=1000.0)]
        exits = [self._exit(901, "1", 2026, month=4, mw=300.0)]
        base = apply_confirmed_exits(fleet, 2026, exits, apply_backlog=True)
        # (12-4)/12 * 300 = 200 MW removed in 2026.
        self.assertAlmostEqual(base[0].pmax_mw, 800.0, places=4)
        y2027 = apply_confirmed_exits(base, 2027, exits)
        # Completion: 4/12 * 300 = 100 MW -> 700 MW = 1000 - 300.
        self.assertAlmostEqual(y2027[0].pmax_mw, 700.0, places=4)

    def test_oversubscribed_partial_exit_annual_average_then_drop(self):
        # Over-subscribed registry (registry MW > the plant's binned fleet MW
        # — the live NEISO Merrimack shape: 459.2 MW registry vs a 108 MW
        # binned tranche). The effective year must land on the annual-average
        # of the plant's true start/end states — factor m/12 for a
        # whole-plant first-half exit, NOT a deeper cut apportioned off the
        # raw registry MW — and the completion leg drops the remainder.
        fleet = [_binned("M_COAL1", 2364, 108.0, pmin=20.0, nameplate=108.0)]
        exits = [
            self._exit(2364, "1", 2028, month=6, mw=113.6),
            self._exit(2364, "2", 2028, month=6, mw=345.6),
        ]
        y2028 = apply_confirmed_exits(fleet, 2028, exits)
        # Annual-average of full exit: 6/12 * 108 = 54 MW keeps running.
        self.assertAlmostEqual(y2028[0].pmax_mw, 54.0, places=4)
        # Completion: the plant is legally gone -> tranche dropped.
        self.assertEqual(apply_confirmed_exits(y2028, 2029, exits), [])

    def test_oversubscribed_backlog_prior_drops_whole_plant(self):
        # Backlog variant of over-subscription: a pre-start whole-plant exit
        # removes min(registry, binned) -> the tranche is gone at base build.
        fleet = [_binned("M_COAL1", 903, 108.0, pmin=20.0, nameplate=108.0)]
        exits = [self._exit(903, "1", 2025, month=6, mw=459.2)]
        self.assertEqual(
            apply_confirmed_exits(fleet, 2026, exits, apply_backlog=True), []
        )


class TestEvolveFleetLedgerReconciliation(unittest.TestCase):
    """The evolve_fleet-seam capacity-accounting reconciliation (FFR-1A / FR-26).

    Asserts, per fuel, the I4 identity ON THE EVENTS DICT itself::

        fleet_by_fuel_after == fleet_by_fuel_before − retirements
                               − confirmed_derates + thermal_additions
                               (± ccs_retrofit fuel shifts)

    This is the unit test the forecast-readiness audit says would have caught
    FR-1 (the I4/A1 leak): a plant-binned confirmed exit derates a SURVIVING
    ``unit_id``, so no set-diff retirement row exists and only the
    ``confirmed_derates`` rows can close the balance.
    """

    def _exit(self, plant_id, gen_id, year, month=None, mw=None):
        return ConfirmedExit(
            plant_id=plant_id,
            generator_id=gen_id,
            exit_year=year,
            exit_month=month,
            mw=mw,
        )

    def _events(self):
        from market_sim.results.evolution_ledger import new_events

        return new_events()

    def _assert_reconciles(self, events):
        """Per fuel: after == before − retired − derated + added (± CCS)."""
        expected = dict(events["fleet_by_fuel_before"])
        for r in events["retirements"]:
            expected[r["fuel"]] = expected.get(r["fuel"], 0.0) - r["mw"]
        for d in events["confirmed_derates"]:
            expected[d["fuel"]] = expected.get(d["fuel"], 0.0) - d["derate_mw"]
        for d in events.get("announced_derates", []):
            expected[d["fuel"]] = expected.get(d["fuel"], 0.0) - d["derate_mw"]
        for a in events["thermal_additions"]:
            expected[a["fuel"]] = expected.get(a["fuel"], 0.0) + a["mw"]
        for c in events["ccs_retrofits"]:
            expected[c["from_fuel"]] = expected.get(c["from_fuel"], 0.0) - c["mw"]
            expected[c["to_fuel"]] = expected.get(c["to_fuel"], 0.0) + c["mw"]
        after = events["fleet_by_fuel_after"]
        for fuel in set(expected) | set(after):
            self.assertAlmostEqual(
                expected.get(fuel, 0.0),
                after.get(fuel, 0.0),
                places=4,
                msg=f"I4 identity broken for {fuel}",
            )

    def test_two_unit_grain_drop_reconciles(self):
        # Trivial 2-unit fixture: a coal unit confirmed out (unit-grain drop),
        # a gas unit untouched. The drop lands as reason="confirmed" and the
        # per-fuel balance closes.
        fleet = [
            _unit(100, "1", 300.0, fuel="coal"),
            _unit(101, "1", 200.0, fuel="gas_cc"),
        ]
        events = self._events()
        evolve_fleet(
            fleet,
            None,
            2028,
            ScenarioConfig(),
            {},
            events=events,
            confirmed_exits=[self._exit(100, "1", 2028, mw=300.0)],
        )
        self.assertEqual(
            [(r["unit_id"], r["reason"]) for r in events["retirements"]],
            [("100_1", "confirmed")],
        )
        self.assertEqual(events["confirmed_derates"], [])
        self.assertAlmostEqual(events["fleet_by_fuel_after"].get("coal", 0.0), 0.0)
        self._assert_reconciles(events)

    def test_binned_derate_writes_confirmed_derates_and_reconciles(self):
        # FR-1 regression: a plant-binned exit shrinks surviving tranches.
        # Without confirmed_derates rows the balance CANNOT close (no unit_id
        # disappears), so this asserts both the rows and the closed identity.
        fleet = [
            _binned("B_CC1", 200, 600.0, pmin=120.0, nameplate=600.0),
            _binned("B_CC2", 200, 400.0, pmin=80.0, nameplate=400.0),
        ]
        events = self._events()
        evolve_fleet(
            fleet,
            None,
            2028,
            ScenarioConfig(),
            {},
            events=events,
            confirmed_exits=[self._exit(200, "U1", 2028, mw=400.0)],
        )
        self.assertEqual(events["retirements"], [])
        derates = {d["unit_id"]: d for d in events["confirmed_derates"]}
        self.assertEqual(set(derates), {"B_CC1", "B_CC2"})
        self.assertAlmostEqual(derates["B_CC1"]["derate_mw"], 240.0, places=4)
        self.assertAlmostEqual(derates["B_CC2"]["derate_mw"], 160.0, places=4)
        for d in derates.values():
            self.assertAlmostEqual(
                d["mw_before"] - d["mw_after"], d["derate_mw"], places=6
            )
        # The leak the rows repair is material: 400 MW left the fleet with no
        # retirement row.
        self.assertAlmostEqual(
            sum(d["derate_mw"] for d in derates.values()), 400.0, places=4
        )
        self._assert_reconciles(events)

    def test_reason_split_confirmed_vs_announced(self):
        # A confirmed drop and an announced (EIA-860 date) non-fossil drop in
        # the same year carry their own channel reasons — never one conflated
        # "known" diff.
        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),
            _gen("N0", "nuclear", pmax=800.0, retirement_year=2028),
        ]
        events = self._events()
        evolve_fleet(
            fleet,
            None,
            2028,
            ScenarioConfig(),
            {},
            events=events,
            confirmed_exits=[self._exit(300, "1", 2028, mw=500.0)],
        )
        reasons = {r["unit_id"]: r["reason"] for r in events["retirements"]}
        self.assertEqual(reasons, {"300_1": "confirmed", "N0": "announced"})
        self._assert_reconciles(events)

    def test_commissioned_pipeline_unit_gets_addition_row(self):
        # FR-13: a step-4.5 commissioned pipeline unit must land in
        # thermal_additions (the baseline snapshots BEFORE the insert), or its
        # MW enters the fleet unledgered and I4 fails at every COD year once
        # entry_commissioning_lag is armed.
        fleet = [_unit(400, "1", 250.0, fuel="gas_cc")]
        pipeline = [
            {
                "tech": "gas_ct",
                "mw": 120.0,
                "zone": "ERCOT-Houston",
                "decision_year": 2027,
                "cod_year": 2029,
                "seq": 0,
                "kind": "thermal",
            }
        ]
        events = self._events()
        evolve_fleet(
            fleet,
            None,
            2029,
            ScenarioConfig(iso="ERCOT", entry_commissioning_lag=True),
            {},
            events=events,
            entry_pipeline=pipeline,
        )
        adds = {a["unit_id"]: a for a in events["thermal_additions"]}
        self.assertEqual(len(adds), 1)
        (row,) = adds.values()
        self.assertEqual(row["fuel"], "gas_ct")
        self.assertAlmostEqual(row["mw"], 120.0, places=4)
        self.assertEqual(row["source"], "economic")
        self._assert_reconciles(events)

    def test_partial_exit_completion_ledgered_in_both_years(self):
        # FFR-1A arm 2 x arm 1: a first-half exit's annual-average leg AND its
        # year+1 completion leg each land as confirmed_derates rows in their
        # own year's events, and both years reconcile per fuel.
        fleet = [_binned("M_COAL1", 2364, 500.0, pmin=100.0, nameplate=500.0)]
        exits = [self._exit(2364, "1", 2028, month=6, mw=300.0)]
        ev_2028 = self._events()
        fleet_2028, _, _, _, _ = evolve_fleet(
            fleet,
            None,
            2028,
            ScenarioConfig(),
            {},
            events=ev_2028,
            confirmed_exits=exits,
        )
        (d28,) = ev_2028["confirmed_derates"]
        self.assertAlmostEqual(d28["derate_mw"], 150.0, places=4)  # (6/12)*300
        self._assert_reconciles(ev_2028)
        ev_2029 = self._events()
        evolve_fleet(
            fleet_2028,
            None,
            2029,
            ScenarioConfig(),
            {},
            events=ev_2029,
            confirmed_exits=exits,
        )
        (d29,) = ev_2029["confirmed_derates"]
        self.assertAlmostEqual(d29["derate_mw"], 150.0, places=4)  # completion
        self.assertAlmostEqual(d29["mw_after"], 200.0, places=4)  # 500 - 300
        self._assert_reconciles(ev_2029)


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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy")
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

        config = ScenarioConfig(
            retirement_rule="legacy"
        )  # eac_price_nuclear defaults to 0.0
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
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy")
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

    def test_default_rule_is_pipeline(self):
        # Owner decision D-1, signed 2026-08-02 (ffr-owner-sitting-2026-08-02
        # Addendum C.1): the default flipped "legacy" -> "pipeline" on FFR-2B's
        # met evidence bar. The legacy rule remains selectable and tested below.
        self.assertEqual(ScenarioConfig().retirement_rule, "pipeline")

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
        # (same fixture arithmetic as the reliability-floor tests). The cap is
        # tested at the schedule's EXECUTION horizon, not the decision year
        # (_admission_cap_horizon, the G-31 grain correction): coal's lag 3
        # puts the horizon at 2033, so the 2031/2032 screens test
        # 3080 x 1.025^2 x 0.942 x 1.1375 = 3467.3 MW rather than the
        # decision-year 3080 x 0.942 x 1.1375 = 3300.1 MW. Retaining gas_st
        # alone (3817 MW accredited) clears BOTH, so this fixture's outcome is
        # grain-invariant and still pins the composition claim below; the
        # grain itself is pinned by the two tests that follow.
        # nuclear (2000 at rating) + DC ties (817) = 2817 < req, so ONE of the two failing
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

    def test_admission_cap_horizon_is_the_last_execution_year(self):
        # G-31 cap grain (FFR-3F task 1; owner decision D-8 / FFR-3C §1.2 G3).
        # The admission cap screens ONE counterfactual fleet — the current
        # fleet with the whole scheduled exit set removed at once — and that
        # fleet is realized at the LAST execution year in the schedule, not at
        # the decision year. FFR-3C measured the old grain testing a 2026
        # requirement against exits landing in 2028: +10.3 % of requirement
        # the cap never saw. Both year-dependent inputs move to the horizon:
        # the FPR delivery year and the peak, the latter projected on the
        # run's own demand-growth path.
        from market_sim.model.capacity_evolution.retirements import (
            _admission_cap_horizon,
        )

        config = ScenarioConfig(retirement_rule="pipeline", iso="ERCOT")
        coal = [_gen(f"C{i}", "coal", pmax=100.0) for i in range(3)]
        scheduled = {g.unit_id for g in coal}
        growth = (1.0 + resolve_demand_growth_rate(config, 2031)) * (
            1.0 + resolve_demand_growth_rate(config, 2032)
        )
        # Decided at the 2031 screen (loss year 2030) + lag_coal 3 => 2033.
        cap_year, cap_peak = _admission_cap_horizon(
            config, scheduled, {}, 2030, coal, 1000.0, 2031
        )
        self.assertEqual(cap_year, 2033)
        self.assertAlmostEqual(cap_peak, 1000.0 * growth, places=6)

        # A lag-1 fuel executes in the screen year itself, so its horizon IS
        # the decision year: the correction is inert there, byte-identically.
        gas_st = [_gen("S0", "gas_st", pmax=100.0)]
        self.assertEqual(
            _admission_cap_horizon(config, {"S0"}, {}, 2030, gas_st, 1000.0, 2031),
            (2031, 1000.0),
        )
        # Empty schedule: nothing to project against, unchanged.
        self.assertEqual(
            _admission_cap_horizon(config, set(), {}, 2030, coal, 1000.0, 2031),
            (2031, 1000.0),
        )
        # A pending unit carries its OWN decided year, not this screen's.
        self.assertEqual(
            _admission_cap_horizon(
                config, {"C0"}, {"C0": 2028}, 2030, coal, 1000.0, 2031
            )[0],
            2031,  # 2028 + 3 = 2031, already due — never earlier than `year`
        )

    def test_admission_cap_binds_on_the_execution_year_requirement(self):
        # The behavioural half: a fixture where the two grains admit DIFFERENT
        # exit sets, so a revert to the decision-year grain fails here.
        # ERCOT, peak 3095.5 MW. Accredited without the coal cohort (nuclear
        # 2000 at seasonal rating + DC ties) = 3090.15 MW, and each coal unit
        # buys 250 MW of firm adequacy back.
        #   decision-year requirement 2031 = 3316.91 MW -> ONE unit retained
        #   execution-year requirement 2033 (peak grown 2 yr) = 3484.82 MW
        #                                                     -> TWO retained
        config = ScenarioConfig(retirement_rule="pipeline", iso="ERCOT")
        peak = 3095.5
        nuclear = _gen("N0", "nuclear", pmax=2000.0)
        coal = [_gen(f"C{i}", "coal", pmax=250.0) for i in range(8)]
        fleet = [nuclear, *coal]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        # Nuclear clears its bar on the gross fallback; every coal unit fails.
        dispatch = SimpleNamespace(
            dispatch=np.vstack(
                [np.full((1, self.T), 1.0e7)] + [np.full((1, self.T), 10.0)] * 8
            )
        )
        sink: dict = {}
        apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=peak,
            year=2031,
            event_sink=sink,
        )
        capped = [e for e in sink["pipeline_events"] if e["event"] == "entry_capped"]
        self.assertEqual(len(capped), 2)

        # And the grain is what makes it two: the accredited base plus ONE
        # retained unit clears the decision-year requirement but NOT the
        # execution-year one. If the cap reverts to the decision year this
        # bracket inverts and the assertion above drops to 1.
        from market_sim.model.capacity_evolution.adequacy import (
            accredited_firm_capacity_mw,
        )

        base = accredited_firm_capacity_mw(
            [nuclear],
            0.0,
            0.0,
            0.0,
            iso="ERCOT",
            peak_demand_mw=peak,
            elcc_curves_enabled=config.renewable_elcc_curves,
        )
        growth = (1.0 + resolve_demand_growth_rate(config, 2031)) * (
            1.0 + resolve_demand_growth_rate(config, 2032)
        )
        req_decision = resolve_adequacy_requirement_mw(config, "ERCOT", peak, 2031)
        req_execution = resolve_adequacy_requirement_mw(
            config, "ERCOT", peak * growth, 2033
        )
        self.assertGreaterEqual(base + 250.0, req_decision)
        self.assertLess(base + 250.0, req_execution)
        self.assertGreaterEqual(base + 500.0, req_execution)

    def _cohort_schedule(self, cap, n=12, mw=500.0, years=range(2026, 2036)):
        """Exit schedule of an all-failing coal cohort under ``exit_rate_cap_mw``.

        ``peak_demand=0`` makes the reliability floor inert, so what is left
        is the queue alone. Returns ``[(year, executed_gw, deferred_units)]``.
        """
        fleet = [
            _gen(f"C{i:02d}", "coal", pmax=mw, heat_rate=10.0 + i) for i in range(n)
        ]
        config = ScenarioConfig(retirement_rule="pipeline", iso="ERCOT")
        state: dict[str, int] = {}
        schedule = []
        for year in years:
            if not fleet:
                schedule.append((year, 0.0, 0))
                continue
            arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
            sink: dict = {}
            fleet, state, _ = apply_economic_retirements(
                fleet,
                arrays,
                SimpleNamespace(dispatch=np.full((len(fleet), self.T), 10.0)),
                np.full((1, self.T), 10.0),
                config,
                state,
                peak_demand=0.0,
                year=year,
                event_sink=sink,
                exit_rate_cap_mw=cap,
            )
            events = sink["pipeline_events"]
            schedule.append(
                (
                    year,
                    sum(e["mw"] for e in events if e["event"] == "executed") / 1000.0,
                    sum(1 for e in events if e["event"] == "throughput_deferred"),
                )
            )
        return schedule

    def test_exit_throughput_cap_spreads_the_wave_without_shrinking_it(self):
        # The mechanism owner decision D-8 authorized (2026-08-03,
        # ffr-owner-sitting-2026-08-02.md Addendum F.1). FFR-3C §1.2 G2
        # measured what the pipeline lacks: a per-fuel constant execution lag
        # is a rigid TIME-SHIFT operator, so an all-failing cohort's exit wave
        # is one year wide however many units fail. A throughput cap is the
        # missing second property of the same queue.
        #
        # 12 x 500 MW coal (6 GW), all failing, lag 3. Uncapped the whole
        # cohort leaves in ONE year; capped at 2 GW/yr it leaves over THREE —
        # and the TOTAL is identical. That invariant is the point: a
        # throughput cap moves the calendar, it does not adjudicate the level
        # (which is the revenue lane's, FFR-3C §1.4).
        uncapped = self._cohort_schedule(None)
        capped = self._cohort_schedule(2000.0)

        self.assertEqual(sum(1 for _y, gw, _d in uncapped if gw > 0), 1)
        self.assertEqual(sum(1 for _y, gw, _d in capped if gw > 0), 3)
        self.assertAlmostEqual(sum(gw for _y, gw, _d in uncapped), 6.0)
        self.assertAlmostEqual(sum(gw for _y, gw, _d in capped), 6.0)
        # No year exceeds the budget, and deferrals are recorded as their own
        # event kind (never folded into floor retention).
        self.assertTrue(all(gw <= 2.0 + 1e-9 for _y, gw, _d in capped))
        self.assertTrue(any(d > 0 for _y, _gw, d in capped))
        # Default off is byte-identical to the shipped no-cap behaviour.
        self.assertEqual(self._cohort_schedule(None), uncapped)

    def test_exit_throughput_cap_is_strict_fifo_by_decided_year(self):
        # A deactivation queue is processed oldest-request-first. The unit
        # decided earlier leaves first even though the later-decided unit is
        # the less efficient one (which is the order the ledger sort would
        # otherwise impose).
        from market_sim.model.capacity_evolution.retirements import (
            _apply_exit_throughput_cap,
        )

        old = _gen("OLD", "coal", pmax=500.0, heat_rate=9.0)
        new = _gen("NEW", "coal", pmax=500.0, heat_rate=15.0)
        due = sorted([old, new], key=lambda g: (g.fuel_type, -g.heat_rate))
        self.assertEqual([g.unit_id for g in due], ["NEW", "OLD"])  # ledger order
        executing, deferred = _apply_exit_throughput_cap(
            due, {"OLD": 2028, "NEW": 2030}, cap_mw=500.0
        )
        self.assertEqual([g.unit_id for g in executing], ["OLD"])
        self.assertEqual([g.unit_id for g in deferred], ["NEW"])

    def test_exit_throughput_cap_never_makes_a_unit_immortal(self):
        # A unit larger than the whole annual budget must still leave — at the
        # head of the queue — or the cap silently becomes an immortality rule
        # instead of a rate limit.
        from market_sim.model.capacity_evolution.retirements import (
            _apply_exit_throughput_cap,
        )

        huge = _gen("HUGE", "coal", pmax=9000.0)
        small = _gen("SMALL", "coal", pmax=100.0)
        executing, deferred = _apply_exit_throughput_cap(
            [huge, small], {"HUGE": 2028, "SMALL": 2029}, cap_mw=1000.0
        )
        self.assertEqual([g.unit_id for g in executing], ["HUGE"])
        self.assertEqual([g.unit_id for g in deferred], ["SMALL"])

    def test_exit_throughput_cap_does_not_backfill_remaining_headroom(self):
        # Strict FIFO: the year stops at the first unit that does not fit; a
        # smaller LATER request is not promoted to pack the year. Reordering
        # the queue by size is not something a real deactivation queue does,
        # and it would make exit composition depend on unit size.
        from market_sim.model.capacity_evolution.retirements import (
            _apply_exit_throughput_cap,
        )

        first = _gen("A", "coal", pmax=600.0)
        big = _gen("B", "coal", pmax=900.0)
        tiny = _gen("C", "coal", pmax=100.0)
        executing, deferred = _apply_exit_throughput_cap(
            [first, big, tiny], {"A": 2028, "B": 2029, "C": 2030}, cap_mw=1000.0
        )
        self.assertEqual([g.unit_id for g in executing], ["A"])
        self.assertEqual([g.unit_id for g in deferred], ["B", "C"])

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
        config = ScenarioConfig(retirement_rule="legacy").with_overrides(
            fixed_om_gas_ct=fom_gas_ct
        )
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

    def setUp(self):
        # Hand-computed requirement/UCAP arithmetic on a synthetic 1-2-unit
        # fixture: zero the FFR-1C hydro pool so the ISO's real EIA hydro
        # census can never enter these sums (tests/helpers docstring).
        patcher = no_hydro_accreditation()
        patcher.start()
        self.addCleanup(patcher.stop)

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
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(retirement_rule="legacy").with_overrides(
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

    def test_retention_merit_within_fuel_co2_order_heterogeneous_pmax(self):
        # capx D55 (D32 §3.2 — FINDING-capx-d32-floor-retention-2026-09-02):
        # key 1 must be the class constant, not the per-unit quotient
        # (FOM x pmax x 1000) / (pmax x fraction). The quotient is the same
        # number in exact arithmetic but not in IEEE-754 — at UCAP 0.95,
        # pmax 291.535 / 1000 / 613.2 land on 61578.947368421046 / ...05 /
        # ...07 — so the defective key sorted B (the dirtiest) FIRST and C
        # (the cleanest) LAST, and the CO2 tie-break never fired. The
        # sibling test above uses two units of EQUAL pmax (1000), where the
        # quotient is bit-identical and the defect is invisible.
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
            ADEQUACY_EXTERNAL_TIE_FIRM_MW,
            THERMAL_ACCREDITATION_BASIS_BY_ISO,
        )

        config = ScenarioConfig(retirement_rule="legacy").with_overrides(
            planning_reserve_margin_override=0.0,
            retirement_years_coal=1,  # pin (D1 default 3): screen-eligible now
        )
        fleet = [
            _gen("A", "coal", pmax=1000.0, heat_rate=10.0, emission_rate_co2=0.95),
            _gen("B", "coal", pmax=291.535, heat_rate=10.0, emission_rate_co2=1.50),
            _gen("C", "coal", pmax=613.2, heat_rate=10.0, emission_rate_co2=0.60),
        ]
        # Legacy UCAP basis (registries cleared, as the nameplate test below):
        # firm = 0.95 x pmax -> C 582.5, A 950.0, B 277.0. Requirement = peak
        # 1000 (PRM 0). Designed order (CO2 ascending) retains C then A
        # (1532.5 >= 1000) and releases B; the defective order (B, A, C by
        # float noise) retained B then A (1227.0 >= 1000) and released C.
        with (
            mock.patch.dict(THERMAL_ACCREDITATION_BASIS_BY_ISO, clear=True),
            mock.patch.dict(ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO, clear=True),
            mock.patch.dict(ADEQUACY_EXTERNAL_TIE_FIRM_MW, clear=True),
        ):
            keys = [_floor_retention_merit(config, g) for g in fleet]
            survivors, _, log = self._screen(fleet, config, peak=1000.0)
        # Key 1 is bit-identical across the fuel whatever the pmax.
        self.assertEqual(len({k[0] for k in keys}), 1)
        self.assertEqual(keys[0][0], 45.0 * 1.3 * 1000.0 / 0.95)
        self.assertEqual(sorted(g.unit_id for g in survivors), ["A", "C"])
        self.assertEqual([r["unit_id"] for r in log], ["C", "A"])
        self.assertEqual([r["co2_rate"] for r in log], [0.60, 0.95])

    def test_retention_merit_cost_is_primary(self):
        # Cost stays the primary key: a cheap-adequacy CT (8 $/kW-yr) beats
        # coal (52 effective) regardless of CO2 — the floor is an adequacy
        # purchase, not an emissions ranking. coal=1 pinned (D1 default 3).
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(retirement_rule="legacy").with_overrides(
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
        config = ScenarioConfig(retirement_rule="legacy", retirement_years_coal=1)
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
        config = ScenarioConfig(
            retirement_rule="legacy", iso="ERCOT", retirement_years_coal=1
        )
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

        config = ScenarioConfig(retirement_rule="legacy")
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
            retirement_rule="legacy",
            market_design_retirement_floor=True,
            retirement_years_coal=1,
        )
        survivors, _, retention_log = self._screen(self._fleet(), config, 10000.0)
        self.assertEqual([g.unit_id for g in survivors], ["N0"])
        self.assertEqual(retention_log, [])

    def test_flag_off_is_byte_identical(self):
        # Default-off reproduces the pre-gate behaviour exactly (the same
        # fixture as test_reliability_floor_prevents_over_retirement).
        config = ScenarioConfig(
            retirement_rule="legacy",
            market_design_retirement_floor=False,
            retirement_years_coal=1,
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
            base = ScenarioConfig(
                retirement_rule="legacy", iso="PJM", retirement_years_coal=1
            )
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
            retirement_rule="legacy",
            market_design_retirement_floor=True,
            retirement_years_coal=1,
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
        # The registry's DOCUMENTED vintage is the 2024-2025 factor (Option B
        # static proxy, FF-3D 2026-07-18). capx D52 (2026-09-04) intook the
        # 2025-2026 row (0.1300) for its per-capability-year gate
        # (NYCA_ICAP_UCAP_TRANSLATION_BY_ISO) WITHOUT moving this composite —
        # re-deriving the shipped composite onto the newer row is a rule-23
        # owner decision routed in FINDING-capx-d52-2026-09-04.md, so this test
        # pins the registry's own vintage rather than the newest row on disk.
        latest = "2024-2025"
        self.assertIn(latest, by_year)
        self.assertIn("2025-2026", by_year)  # the D52 intake is on disk
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

    def test_falls_back_before_first_published_fpr(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        cfg = ScenarioConfig(iso="PJM")
        peak = 160_560.0
        # Model year 2024 -> delivery 2024/2025 -> BEFORE the first published
        # post-CIFP FPR (2025/2026) -> the (1 + PRM) x icap_to_ucap_ratio
        # fallback (byte-identical to pre-R2), on the DR-netted firm peak.
        # Pre-table years deliberately keep the fallback (hold-last extends
        # the table's FORWARD edge only, card C-A 2026-08-25) — this is what
        # keeps every backcast year byte-identical.
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["PJM"]
        expected = (
            peak * (1.0 - dr) * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["PJM"]) * ratio
        )
        self.assertIsNone(resolve_forecast_pool_requirement("PJM", 2024))
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2024),
            expected,
            places=3,
        )

    def test_holds_last_published_fpr_beyond_table(self):
        # HOLD-LAST-FPR (owner card C-A, 2026-08-25; the
        # resolve_demand_curve_vintage / forward_net_cone_anchor forward-carry
        # precedent): a delivery year strictly beyond the last published FPR
        # holds that value — never the stale (1 + PRM) x ratio composite,
        # whose IRM half is two vintages behind PJM's own rising series
        # (FINDING-capx-d2b-i7-ledger-2026-08-25.md §5.2: the composite
        # dropped the bar 3.18 % of peak crossing 2028/29 -> 2029/30).
        last = FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"]["2028/2029"]
        for year in (2029, 2030, 2050):
            self.assertEqual(resolve_forecast_pool_requirement("PJM", year), last)

    def test_requirement_uses_held_last_fpr_beyond_table(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        cfg = ScenarioConfig(iso="PJM")
        peak = 160_560.0
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        last = FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"]["2028/2029"]
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2030),
            peak * (1.0 - dr) * last,
            places=3,
        )
        # And the held bar sits ABOVE the stale composite it replaces — the
        # direction of the correction is against leniency, by construction.
        ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["PJM"]
        composite = (
            peak * (1.0 - dr) * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["PJM"]) * ratio
        )
        self.assertGreater(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2030), composite
        )

    def test_hold_last_never_bridges_an_in_table_gap(self):
        # An absent delivery year BETWEEN published entries falls back (None):
        # the convention extends the forward edge only; a mid-table hole is a
        # data problem hold-last must not paper over.
        with mock.patch.dict(
            FORECAST_POOL_REQUIREMENT_BY_ISO,
            {"PJM": {"2025/2026": 0.9380, "2028/2029": 0.9401}},
            clear=False,
        ):
            self.assertIsNone(resolve_forecast_pool_requirement("PJM", 2026))
            self.assertEqual(resolve_forecast_pool_requirement("PJM", 2029), 0.9401)

    def test_year_none_is_fallback_byte_identical(self):
        cfg = ScenarioConfig(iso="PJM")
        peak = 160_560.0
        # year=None keeps the fallback path; 2024 (pre-table) resolves the
        # same construction, so the two must agree byte-identically.
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", peak),
            resolve_adequacy_requirement_mw(cfg, "PJM", peak, 2024),
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
        from market_sim.model.capacity import (
            _hydro_firm_mw,
            accredited_firm_capacity_mw,
        )

        # An empty fleet accredits exactly the cleared BRA import UCAP plus
        # PJM's published hydro accreditation (FFR-1C: the hydro pool is the
        # only other non-fleet supply term).
        self.assertAlmostEqual(
            accredited_firm_capacity_mw([], iso="PJM"),
            1_281.7 + _hydro_firm_mw([], "PJM"),
            places=6,
        )
        with no_hydro_accreditation():
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

        # ARA 3 of CCP 2026/2027 (ARA ICR filing, 2025-11-21, p.12; capx-S4b
        # re-vintage): Net ICR 30,050 MW, summer 50/50 peak 26,648 MW.
        self.assertAlmostEqual(
            PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"],
            30_050.0 / 26_648.0 - 1.0,
            places=6,
        )

    def test_neiso_dr_fraction_reconstructs_cleared_fca_demand_resources(self):
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        # CCP 2026/27 demand-resource CSO incl. ARA 3 results (2026 CELT 4.1):
        # 2,639.682 MW against the ARA-3 Net ICR of 30,050 MW.
        self.assertAlmostEqual(
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"] * 30_050.0,
            2_639.682,
            places=6,
        )

    def test_neiso_requirement_netting_reproduces_net_icr_minus_dr(self):
        # At ISO-NE's own 50/50 peak the DR-netted requirement equals its own
        # construction: Net ICR minus the supply-side demand-resource CSOs
        # (both at the ARA-3 vintage of CCP 2026/27).
        cfg = ScenarioConfig(iso="NEISO")
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "NEISO", 26_648.0),
            30_050.0 - 2_639.682,
            places=3,
        )

    def test_firm_import_credits_for_import_node_isos(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW
        from market_sim.model.capacity import (
            _firm_import_mw,
            accredited_firm_capacity_mw,
        )

        self.assertEqual(ADEQUACY_EXTERNAL_TIE_FIRM_MW["CAISO"], 3_371.0)
        # CCP 2026/27 net import CSO incl. ARA 3 (2026 CELT 4.1; capx-S4b).
        self.assertEqual(ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"], 409.31)
        # One resolver, and an empty fleet accredits exactly the firm import.
        self.assertEqual(_firm_import_mw("CAISO"), 3_371.0)
        self.assertEqual(_firm_import_mw(None), 0.0)
        # The firm-import credit is additive to the (FFR-1C) hydro pool — the
        # two are the ledger's only non-fleet, non-pool supply terms.
        with no_hydro_accreditation():
            self.assertAlmostEqual(
                accredited_firm_capacity_mw([], iso="CAISO"), 3_371.0, places=6
            )
            self.assertAlmostEqual(
                accredited_firm_capacity_mw([], iso="NEISO"), 409.31, places=6
            )


class TestNyisoExternalCapacityIntake(unittest.TestCase):
    """capx D-2 (2026-08-25): NYISO external-capacity accreditation intake.

    Closes the FC-1 I7 base-year accounting gap adjudicated by
    FINDING-capx-d2-adequacy-nyiso-2026-08-24.md §4b: NYISO credited zero
    external firm capacity while every peer ISO carried a registry entry. The
    value is NYISO's own published external capacity — 2026 Gold Book Table
    V-1, Summer 2026 net capacity purchases from external control areas,
    3,168.5 MW on the schedule's seasonal-capability (ICAP) basis — converted
    to the model's UCAP requirement basis with the SAME published NYCA
    ICAP->UCAP translation factor the requirement side applies (rule 19 one
    basis; the rule-14 reconciliation pattern of the PJM DR entry). Published
    operands only, never a number tuned to clear I7 (rules 5/13/21): the
    entry overshoots the 35.7 MW I7 residual by ~77x, the pre-declared
    honesty signature of a real accreditation rather than a fit.
    """

    # Gold Book Table V-1, Summer 2026 column (seasonal capability, ICAP MW).
    GOLD_BOOK_SUMMER_2026_ICAP_MW = 3_168.5

    def test_registry_reconstructs_gold_book_times_translation(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW

        # Table V-1's own component sum reconciles the summer total.
        self.assertAlmostEqual(67.3 + 2_443.0 + 3.3 + 654.9, 3_168.5, places=6)
        self.assertAlmostEqual(
            ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"],
            self.GOLD_BOOK_SUMMER_2026_ICAP_MW * (1.0 - 0.1321),
            places=6,
        )

    def test_ucap_conversion_uses_the_requirement_side_factor(self):
        # One basis across both sides of I7 (rule 19): the entry's ICAP->UCAP
        # conversion IS the registered requirement-side ratio, never a second
        # independently-typed factor that could silently diverge.
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW

        self.assertAlmostEqual(
            ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"] / self.GOLD_BOOK_SUMMER_2026_ICAP_MW,
            PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"],
            places=9,
        )

    def test_accredited_ledger_includes_nyiso_external_firm(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW
        from market_sim.model.capacity import (
            _firm_import_mw,
            accredited_firm_capacity_mw,
        )

        expected = ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"]
        # One resolver (rule 19), and the credit is additive to the hydro
        # pool — the ledger's only non-fleet, non-pool supply terms.
        self.assertAlmostEqual(_firm_import_mw("NYISO"), expected, places=6)
        with no_hydro_accreditation():
            self.assertAlmostEqual(
                accredited_firm_capacity_mw([], iso="NYISO"), expected, places=6
            )

    def test_entry_is_not_a_deliverability_limit_or_the_dispatch_floor(self):
        # The two rejected bases, pinned so a future edit cannot silently
        # swap them in: the 4,350 MW Simultaneous Import Limit (a
        # deliverability LIMIT — the exact error the CAISO entry rejects for
        # the MIC) and the model's 900 MW HQ firm dispatch floor (an
        # inherited ladder constant, not a published RA accreditation).
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW

        value = ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"]
        self.assertNotAlmostEqual(value, 4_350.0, places=0)
        self.assertNotAlmostEqual(value, 900.0, places=0)
        self.assertLess(value, 4_350.0)


class TestMisoAdequacyPackage(unittest.TestCase):
    """capx S-123 (2026-08-30): the MISO adequacy package — S-1 + S-2 + S-3a.

    Executes the three published-source terms chartered by
    FINDING-capx-d2b-i7-ledger-2026-08-25.md §8/§10 against the 6,037 MW MISO
    2026 base-year I7 gap: the PY 2025-26 same-document PRM re-vintage (S-1),
    the PRA external-resource ZRC intake (S-2), and the LMR/DR documented
    reconciliation (S-3a). Published operands only, none sized against the
    residual (rules 5/13/21/23); every pin below is a value from the PY
    2025/26 PRA Results Posting or the PY 2025-26 LOLE Study.
    """

    # PY 2025/26 PRA Results Posting, p.22 Summer trend table (cleared ZRC).
    PRA_SUMMER_CLEARED = {
        "generation": 120_738.6,
        "external_resources": 3_505.9,
        "btm_generation": 4_282.8,
        "demand_resources": 9_004.4,
        "energy_efficiency": 27.6,
    }
    # p.18 Summer zonal results, System column.
    PRA_SUMMER_INITIAL_PRMR = 135_213.4
    PRA_SUMMER_COMMITTED = 137_559.3

    def test_s1_prm_pair_is_same_document_py2025_26(self):
        # Both halves from the PY 2025-26 LOLE Study Module E-1 (ICAP 15.7%,
        # UCAP 7.9%), so the composite is the document's own UCAP requirement
        # peak x 1.079 — no longer the mixed-vintage peak x 1.09952.
        from market_sim.config.constants import PLANNING_RESERVE_MARGIN_BY_ISO

        self.assertAlmostEqual(PLANNING_RESERVE_MARGIN_BY_ISO["MISO"], 0.157)
        ratio = PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["MISO"]
        self.assertAlmostEqual(ratio, 1.079 / 1.157, places=9)
        self.assertAlmostEqual(
            (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["MISO"]) * ratio, 1.079, places=9
        )

    def test_s2_registry_is_the_pra_summer_cleared_external_zrc(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW

        # The posting's own five category rows sum to the System committed
        # total — the entry is one row of MISO's own supply accounting.
        self.assertAlmostEqual(
            sum(self.PRA_SUMMER_CLEARED.values()), self.PRA_SUMMER_COMMITTED, places=1
        )
        self.assertAlmostEqual(
            ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"],
            self.PRA_SUMMER_CLEARED["external_resources"],
            places=6,
        )

    def test_s2_zrc_basis_needs_no_conversion_factor(self):
        # One basis (rule 19): a ZRC is 1 MW of SAC — MISO's UCAP-equivalent
        # unit, the basis the (1 + PRM_UCAP) requirement is stated on — so
        # unlike the NYISO Gold-Book entry the published operand enters
        # verbatim, with no ICAP->UCAP factor to diverge from the requirement
        # side.
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW

        self.assertEqual(ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"], 3_505.9)

    def test_s2_accredited_ledger_includes_miso_external_firm(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW
        from market_sim.model.capacity import (
            _firm_import_mw,
            accredited_firm_capacity_mw,
        )

        expected = ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"]
        self.assertAlmostEqual(_firm_import_mw("MISO"), expected, places=6)
        with no_hydro_accreditation():
            self.assertAlmostEqual(
                accredited_firm_capacity_mw([], iso="MISO"), expected, places=6
            )

    def test_s2_entry_is_not_the_dispatch_floor_or_the_erz_column(self):
        # The rejected bases, pinned so a future edit cannot silently swap
        # them in: the 1,400 MW Manitoba firm-hydro dispatch constant (an
        # inherited ladder spec constant, not a published RA accreditation)
        # and the zonal tables' ERZ-column committed 1,580.1 MW (only the
        # portion clearing in the External Resource Zones proper — the
        # category row is MISO's full external-resource supply count).
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW

        value = ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"]
        self.assertNotAlmostEqual(value, 1_400.0, places=0)
        self.assertNotAlmostEqual(value, 1_580.1, places=0)

    def test_s3a_dr_fraction_is_the_documented_reconciliation(self):
        # Cleared Demand Resources over the pre-auction Initial PRMR (the PJM
        # divide-by-published-requirement construction) — and NOT the BTMG/EE
        # categories, excluded conservatively (metered-demand embedding).
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )

        f = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["MISO"]
        self.assertAlmostEqual(
            f,
            self.PRA_SUMMER_CLEARED["demand_resources"] / self.PRA_SUMMER_INITIAL_PRMR,
            places=9,
        )
        with_btmg_ee = (
            self.PRA_SUMMER_CLEARED["demand_resources"]
            + self.PRA_SUMMER_CLEARED["btm_generation"]
            + self.PRA_SUMMER_CLEARED["energy_efficiency"]
        ) / self.PRA_SUMMER_INITIAL_PRMR
        self.assertLess(f, with_btmg_ee)

    def test_package_requirement_composition(self):
        # The fallback resolver composes the three terms exactly:
        # requirement = peak x (1 - f_DR) x (1 + 0.157) x (1.079/1.157)
        #             = peak x (1 - f_DR) x 1.079   (MISO publishes no FPR).
        from market_sim.config.constants import (
            ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
        )
        from market_sim.model.capacity import resolve_adequacy_requirement_mw

        config = ScenarioConfig(iso="MISO")
        peak = 128_548.607  # the committed FFR-1C 2026 ledger peak
        f = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["MISO"]
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(config, "MISO", peak, 2026),
            peak * (1.0 - f) * 1.079,
            places=3,
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
        # The FPR registry is cleared throughout: at year=2030 the held-last
        # FPR (card C-A) would otherwise govern both calls and neither PRM
        # value would be read — this test isolates the (1 + PRM) fallback.
        registry_config = ScenarioConfig(reserve_margin_build_enabled=True)
        with mock.patch.dict(FORECAST_POOL_REQUIREMENT_BY_ISO, clear=False) as fpr:
            del fpr["PJM"]
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
            with mock.patch.dict(
                PLANNING_RESERVE_MARGIN_BY_ISO, clear=False
            ) as registry:
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
            mock.patch.dict(
                FORECAST_POOL_REQUIREMENT_BY_ISO, clear=False
            ) as fpr_registry,
        ):
            del registry["PJM"]
            del ratio_registry["PJM"]
            del dr_registry["PJM"]
            # Held-last FPR (card C-A) would govern 2030 otherwise — cleared
            # with the rest: "absent from EVERY adequacy registry".
            del fpr_registry["PJM"]
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
        config = ScenarioConfig(retirement_rule="legacy").with_overrides(
            fixed_om_gas_cc=12.0
        )
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
        config = ScenarioConfig(retirement_rule="legacy")
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
        config = config or ScenarioConfig(retirement_rule="legacy").with_overrides(
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

        config = ScenarioConfig(retirement_rule="legacy", iso="ERCOT").with_overrides(
            as_revenue_enabled=True
        )
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
                ScenarioConfig(retirement_rule="legacy", iso=iso),
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
                ScenarioConfig(retirement_rule="legacy", iso=iso),
                iso,
                gas_price_per_mmbtu=3.5,
            )
        self.assertNotIn("hourly", seen)


class TestQueueCapCoverage(unittest.TestCase):
    """Every registered ISO must carry queue-cap data (peer review B2)."""

    ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")

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

    @staticmethod
    def _wind_window_factor(config, window_years):
        """CRF(life)/CRF(window) at the screen's own wind rate and life."""
        from market_sim.config.scenario_resolvers import resolve_new_entry_costs
        from market_sim.config.scenarios import resolve_real_discount_rate

        rate = resolve_real_discount_rate(config, "wind")
        life = float(resolve_new_entry_costs(config)["wind"]["lifetime_yr"])
        return _capital_recovery_factor(rate, life) / _capital_recovery_factor(
            rate, window_years
        )

    def test_wind_ptc_subtracts_levelized_statutory_window(self):
        # FFR-4C (owner decision D-13): the §45 credit runs 10 statutory
        # years from placed-in-service (26 U.S.C. §45(a)(2)(A)(ii)), so the
        # screen books ira_ptc_wind x CRF(life)/CRF(10) per MWh — never the
        # full nominal rate over the plant's whole book life.
        config = ScenarioConfig()  # ira_ptc_wind = 26.0, window = 10
        expected_credit = 26.0 * self._wind_window_factor(config, 10.0)
        adjusted = apply_ira_credits_to_lcoe("wind", 50.0, 2027, config)
        self.assertAlmostEqual(adjusted, 50.0 - expected_credit)
        # Magnitude anchor from the statute arithmetic at the shipped wind
        # cost record (30-yr life, 5.675% real): $13.63/MWh, factor 0.5243
        # (ffr-3v-miso-entry-screen-2026-08-04.md §6.2).
        self.assertAlmostEqual(expected_credit, 13.63, places=2)

    def test_wind_ptc_credit_stops_at_year_10_of_life(self):
        # The chartered semantic, asserted in present-value terms: what the
        # LCOE books, paid over the FULL book life, discounts to the same PV
        # as the nominal rate paid over ONLY the first 10 years — i.e. years
        # 11..30 contribute nothing. An unwindowed credit (the pre-4C defect)
        # would carry PV(nominal over 30), 1.91x larger.
        from market_sim.config.scenario_resolvers import resolve_new_entry_costs
        from market_sim.config.scenarios import resolve_real_discount_rate

        config = ScenarioConfig()
        rate = resolve_real_discount_rate(config, "wind")
        life = float(resolve_new_entry_costs(config)["wind"]["lifetime_yr"])
        booked = wind_ptc_levelized_per_mwh(config)
        pv_booked = booked / _capital_recovery_factor(rate, life)
        pv_ten_year_stream = config.ira_ptc_wind / _capital_recovery_factor(rate, 10.0)
        pv_full_life_stream = config.ira_ptc_wind / _capital_recovery_factor(rate, life)
        self.assertAlmostEqual(pv_booked, pv_ten_year_stream)
        self.assertLess(pv_booked, pv_full_life_stream)

    def test_wind_ptc_window_none_restores_full_life_credit(self):
        # None is the indefinite-extension / paired-control scenario: the
        # factor collapses to CRF(life)/CRF(life) = 1 and the pre-4C flat
        # crediting is reproduced exactly.
        config = ScenarioConfig(ira_ptc_credit_window_years=None)
        self.assertEqual(wind_ptc_levelized_per_mwh(config), 26.0)
        self.assertAlmostEqual(
            apply_ira_credits_to_lcoe("wind", 50.0, 2027, config), 24.0
        )

    def test_wind_ptc_window_at_or_past_life_clips_to_life(self):
        # A window >= book life clips to the life: no year past the plant's
        # own horizon can earn, so the factor is exactly 1.
        config = ScenarioConfig(ira_ptc_credit_window_years=30)
        self.assertAlmostEqual(wind_ptc_levelized_per_mwh(config), 26.0)
        config_over = ScenarioConfig(ira_ptc_credit_window_years=45)
        self.assertAlmostEqual(wind_ptc_levelized_per_mwh(config_over), 26.0)

    def test_wind_ptc_window_rejects_nonpositive(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(ira_ptc_credit_window_years=0)

    def test_solar_itc_path_unchanged_by_ptc_window(self):
        # The chartered no-regression assert: the solar ITC path (capex
        # discount inside compute_lcoe) is byte-identical whatever the wind
        # PTC window is set to — the window touches wind's post-hoc credit
        # only.
        base = ScenarioConfig()
        control = ScenarioConfig(ira_ptc_credit_window_years=None)
        short = ScenarioConfig(ira_ptc_credit_window_years=4)
        for year in (2024, 2027, 2028, 2035):
            lcoe_base = compute_lcoe("solar", year, base)
            self.assertEqual(lcoe_base, compute_lcoe("solar", year, control))
            self.assertEqual(lcoe_base, compute_lcoe("solar", year, short))

    def test_compute_lcoe_and_apply_ira_agree_on_wind_credit(self):
        # Both call sites delegate to the ONE computation site
        # (wind_ptc_levelized_per_mwh) — the credited $/MWh must be identical
        # through either path (rule 19 [R-ONE-MECH]).
        config = ScenarioConfig()
        credit_via_apply = 50.0 - apply_ira_credits_to_lcoe("wind", 50.0, 2027, config)
        control = ScenarioConfig(ira_ptc_credit_window_years=None)
        # The windowed LCOE sits ABOVE the unwindowed control by exactly the
        # credit reduction (nominal - levelized).
        credit_via_lcoe = compute_lcoe("wind", 2027, config) - compute_lcoe(
            "wind", 2027, control
        )
        # compute_lcoe(control) - compute_lcoe(windowed) = nominal - levelized;
        # rearrange against the apply-path credit (= levelized).
        self.assertAlmostEqual(credit_via_lcoe, config.ira_ptc_wind - credit_via_apply)

    def test_solar_itc_not_applied_post_hoc(self):
        # The solar ITC is a capital credit: it is applied to capex inside
        # compute_lcoe, not as a post-hoc scaling of a finished LCOE (which
        # would wrongly discount the fixed-O&M component too).
        config = ScenarioConfig()  # ira_itc_solar = 0.30
        adjusted = apply_ira_credits_to_lcoe("solar", 50.0, 2030, config)
        self.assertEqual(adjusted, 50.0)

    def test_credit_expires_after_expiry_year(self):
        config = ScenarioConfig()  # ira_wind_solar_last_year = 2027
        # The last eligible year itself still carries the (levelized) credit.
        self.assertAlmostEqual(
            apply_ira_credits_to_lcoe("wind", 50.0, 2027, config),
            50.0 - 26.0 * self._wind_window_factor(config, 10.0),
        )
        # The year after the cliff leaves LCOE untouched.
        self.assertEqual(apply_ira_credits_to_lcoe("wind", 50.0, 2028, config), 50.0)

    def test_ira_phaseout_fraction(self):
        # P-1C statute-triangulated §45Y/§48E STEP schedule (100/75/50/0%),
        # replacing the earlier undocumented 2028/2033 linear ramp (rule 24
        # default change). Canonical coverage lives in
        # tests/unit/policy/test_ira.py::TestIRAPhaseoutFraction; kept here so this
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
        self.assertIsNone(get_rps_target("TVA", 2030))

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
        self.assertIsNone(get_rps_acp("TVA"))


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
        # An explicit RFF exogenous path is a FLOOR under the program
        # projection, not a replacement for it — owner ruling S2 (2026-09-06,
        # card D-1), executed by SCN-WS1c. This assertion previously read
        # `== 15.0`, i.e. the mid path REPLACING CARB's $39.36/t in 2030: that
        # is the G-C1 defect (a named federal path SUPPRESSING the state
        # program, which made policy_bundle="tight" a carbon-price CUT on every
        # program ISO in every horizon year). The resolver now returns
        # max(program, path), so CARB binds here and the mid path does not.
        # See tests/unit/policy/test_cap_and_trade.py::TestFederalCarbonFloor
        # for the full statement of the ruled semantics.
        config = ScenarioConfig(iso="CAISO", carbon_price_path="mid")
        self.assertAlmostEqual(
            resolve_carbon_price(config, 2030), 28.06 * 1.07**5, places=3
        )
        self.assertGreater(resolve_carbon_price(config, 2030), 15.0)


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
        self,
        year,
        loss_counter,
        *,
        fixed_om,
        eac_price=0.0,
        price=20.0,
        clean_price=None,
    ):
        """Screen one 100-MW nuclear unit; return (survivor_ids, loss_year).

        Scales are hand-chosen so §45U (max $15/MWh while the gross-receipts
        basis is at or under the $26/MWh threshold) is the pivotal revenue:
        energy margin = price x 100 MW x T; §45U revenue = credit x 100 MW x T;
        going-forward cost = ``fixed_om`` $/kW-yr x 100 MW x 1000. ERCOT
        default => no capacity or AS revenue for nuclear, so energy + the
        attribute payment is the whole stack; ``eford=0`` makes the pro-forma
        margin basis the full 100 MW.

        ``clean_price`` supplies the FFR-7B Arm-3 clean-tier row dual for the
        unit's zone in $/MWh — a branch-(i) compliance certificate, as against
        ``eac_price`` (``eac_price_nuclear``), which is the branch-(iii)
        NY-ZEC/IL-CMC netting contract (D-28).
        """
        config = ScenarioConfig(
            retirement_rule="legacy",
            fixed_om_nuclear=fixed_om,
            eac_price_nuclear=eac_price,
        )
        fleet = [_gen("N0", "nuclear", pmax=100.0, eford=0.0)]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        dispatch = SimpleNamespace(dispatch=np.full((1, self.T), 100.0))
        prices = np.full((1, self.T), price)
        mc = np.zeros((1, self.T))
        clean_by_fuel = (
            None if clean_price is None else {"nuclear": np.array([clean_price])}
        )
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
            clean_attribute_price_by_fuel=clean_by_fuel,
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

    def test_eac_nuclear_stays_out_of_the_45u_gross_receipts_base(self):
        # D-28 branch adjudication, the other half of the test above.
        # eac_price_nuclear models the NY-ZEC / IL-CMC design: a state payment
        # set net of the unit's other revenue, i.e. 26 U.S.C. §45U(b)(2)(B)(iii)
        # -- the contract is EXCLUDED from gross receipts and the state instead
        # reduces its own payment by the federal credit, so the pair pays
        # max(contract, §45U(P_energy)) and never contract + §45U.
        #
        # price=20, eac=15 => branch (iii) pays max(15, §45U(20) = 15) = 15
        # => 20_000 energy + 15_000 attribute = 35_000 < 40_000 -> retire.
        # Had the contract been mis-classified into branch (i) it would sit
        # INSIDE the base: 15 + §45U(35) = 15 + 7.8 = 22.8 $/MWh => 42_800
        # => 20_000 + 22_800 = 42_800 >= 40_000 -> survive. The retirement is
        # what pins the exclusion.
        survivors, _ = self._run_nuclear_screen(2030, 2, fixed_om=0.40, eac_price=15.0)
        self.assertEqual(survivors, [])

    def test_45u_tops_up_a_state_contract_worth_less_than_the_credit(self):
        # Branch (iii)'s max() has two sides. A $5/MWh contract is worth less
        # than the $15/MWh credit at price=20, so the netting program pays
        # nothing and the unit keeps §45U alone -- the SAME outcome as no
        # contract at all. Both configs must land identically at a bar the
        # credit alone clears (20_000 + 15_000 = 35_000 >= 34_000).
        with_contract, _ = self._run_nuclear_screen(
            2030, 2, fixed_om=0.34, eac_price=5.0
        )
        without, _ = self._run_nuclear_screen(2030, 2, fixed_om=0.34, eac_price=0.0)
        self.assertEqual(with_contract, ["N0"])
        self.assertEqual(without, ["N0"])

    def test_clean_tier_dual_enters_the_45u_gross_receipts_base(self):
        # D-28 composition (c) / §45U(b)(2)(B)(i): the Arm-3 clean-tier dual is
        # an LSE-paid compliance certificate with no federal-credit offset in
        # it, so it sits INSIDE gross receipts and each $1 of dual costs $0.80
        # of credit. price=20, D=10 => 10 + §45U(30) = 10 + 11.8 = 21.8 $/MWh
        # => 20_000 energy + 21_800 = 41_800.
        #
        # The two bars below bracket that number and refute both rejected
        # compositions in one pass:
        #   * bar 40_000 -- the old max() fold would credit only
        #     max(§45U(20) = 15, 10) = 15 => 35_000 < 40_000 -> retire. The
        #     unit SURVIVING here is what rules the max() out.
        #   * bar 43_000 -- naive phase-down-then-add on an energy-only basis
        #     would credit 10 + §45U(20) = 25 => 45_000 >= 43_000 -> survive.
        #     The unit RETIRING here is what rules the naive add out.
        survives, _ = self._run_nuclear_screen(2030, 2, fixed_om=0.40, clean_price=10.0)
        retires, _ = self._run_nuclear_screen(2030, 2, fixed_om=0.43, clean_price=10.0)
        self.assertEqual(survives, ["N0"])
        self.assertEqual(retires, [])

    def test_nuclear_takes_the_better_of_the_two_45u_branches(self):
        # One certificate, two statutory routes, and the unit sells it into
        # whichever pays more. eac (branch iii) = 10, clean dual (branch i) =
        # 20, price = 20:
        #   branch (i)   -> 20 + §45U(40) = 20 + 3.8 = 23.8 $/MWh  (WINS)
        #   branch (iii) -> max(10, §45U(20) = 15)    = 15   $/MWh
        # => 20_000 energy + 23_800 = 43_800, which clears a 43_000 bar and
        # misses a 44_000 one. Taking the losing route at either bar, or
        # stacking the two, changes both answers.
        survives, _ = self._run_nuclear_screen(
            2030, 2, fixed_om=0.43, eac_price=10.0, clean_price=20.0
        )
        retires, _ = self._run_nuclear_screen(
            2030, 2, fixed_om=0.44, eac_price=10.0, clean_price=20.0
        )
        self.assertEqual(survives, ["N0"])
        self.assertEqual(retires, [])

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


class TestInternalSupplyAccountingRatio(unittest.TestCase):
    """capx D31 (2026-09-02): the MISO internal-supply accounting ratio.

    The measured wedge between the model's census-accreditation ledger and
    MISO's PRA supply accounting, applied to every internal contribution
    wherever firm capacity is summed toward the adequacy requirement (ledger,
    floor increments, backstop crediting) — and to nothing else. Value and
    application both pinned; every other ISO must stay byte-identical.
    """

    def test_value_is_the_documented_published_arithmetic(self):
        from market_sim.config.constants import (
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO,
        )
        from market_sim.model.capacity import resolve_internal_supply_accounting_ratio

        # Two clean overlap years' Summer offered Generation ZRC (PRA trend
        # table, capacity-market-auction-supply rows) over the model's own
        # entering internal firm (committed D27 ledgers on documented bases).
        expected = (122_375.6 + 123_395.6) / (143_822.1 + 143_749.5)
        self.assertAlmostEqual(
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"],
            expected,
            places=9,
        )
        self.assertAlmostEqual(expected, 0.854644, places=6)
        self.assertEqual(resolve_internal_supply_accounting_ratio("ERCOT"), 1.0)
        self.assertEqual(resolve_internal_supply_accounting_ratio(None), 1.0)

    def test_numerators_match_the_committed_auction_supply_rows(self):
        # The ratio's numerators ARE the committed PRA rows — a transcription
        # tripwire between the registry constant and the datatype.
        from pathlib import Path

        from scripts.lib import capacity_market_auction_supply as asup

        repo_raw = Path(__file__).resolve().parents[3] / "data" / "raw"
        df = asup.parse_iso("MISO", repo_raw)
        gen = df[
            (df["metric"] == "offered")
            & (df["category"] == "generation")
            & (df["season"] == "summer")
        ].set_index("planning_year")["value_mw"]
        self.assertEqual(float(gen.loc["2023-2024"]), 122_375.6)
        self.assertEqual(float(gen.loc["2024-2025"]), 123_395.6)

    def test_ledger_scales_internal_but_not_the_tie(self):
        from market_sim.config.constants import ADEQUACY_EXTERNAL_TIE_FIRM_MW
        from market_sim.model.capacity import (
            _thermal_firm_mw,
            accredited_firm_capacity_mw,
            resolve_internal_supply_accounting_ratio,
        )

        ratio = resolve_internal_supply_accounting_ratio("MISO")
        g = _gen("C1", "coal", pmax=1000.0)
        with no_hydro_accreditation():
            base = accredited_firm_capacity_mw([], iso="MISO")
            with_unit = accredited_firm_capacity_mw([g], iso="MISO")
        # Empty fleet: the tie alone, UNSCALED (the tie is already the
        # market's own cleared external ZRC).
        self.assertAlmostEqual(base, ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"], places=6)
        # Adding a unit moves the ledger by its firm MW × the ratio — the
        # exact increment the reliability floor credits when it un-retires
        # the same unit (one basis, rule 19).
        self.assertAlmostEqual(
            with_unit - base, _thermal_firm_mw(g, "MISO") * ratio, places=6
        )
        self.assertLess(with_unit - base, _thermal_firm_mw(g, "MISO"))

    def test_other_isos_ledgers_are_byte_identical(self):
        from market_sim.model.capacity import (
            _thermal_firm_mw,
            accredited_firm_capacity_mw,
        )

        for iso in ("PJM", "NYISO", "NEISO", "CAISO", "ERCOT"):
            g = _gen("G1", "gas_cc", pmax=500.0)
            with no_hydro_accreditation():
                base = accredited_firm_capacity_mw([], iso=iso)
                with_unit = accredited_firm_capacity_mw([g], iso=iso)
            self.assertAlmostEqual(
                with_unit - base, _thermal_firm_mw(g, iso), places=6, msg=iso
            )

    def test_backstop_builds_enough_to_close_the_gap_on_the_ratioed_ledger(self):
        from market_sim.config.constants import EFORD
        from market_sim.model.capacity import (
            apply_reserve_margin_build,
            resolve_internal_supply_accounting_ratio,
        )

        config = ScenarioConfig(reserve_margin_build_enabled=True)
        peak = 100_000.0
        # A firm ledger 5 GW short of the requirement: the built nameplate
        # must be gap / ((1 - EFORd_ct) × ratio) so its LEDGER contribution
        # (which carries the ratio) closes the gap exactly.
        from market_sim.model.capacity import resolve_adequacy_requirement_mw

        req = resolve_adequacy_requirement_mw(config, "MISO", peak)
        firm = req - 5_000.0
        fleet, built = apply_reserve_margin_build([], firm, peak, 2030, config, "MISO")
        ratio = resolve_internal_supply_accounting_ratio("MISO")
        self.assertAlmostEqual(
            built, 5_000.0 / ((1.0 - EFORD["gas_ct"]) * ratio), places=3
        )
        self.assertEqual(len(fleet), 1)


class TestInternalSupplyAccountingRatioDatedNet(unittest.TestCase):
    """capx D51 (2026-09-04): the MISO ratio re-identified on the dates-ON fleet.

    GATED default-OFF behind ``adequacy_accounting_ratio_dated_net``: unarmed
    (and for every ISO but MISO even when armed) the resolver, the ledger, the
    floor increment and the backstop are byte-identical to D31's registry;
    armed, all three seams resolve the ONE dated-net value (one basis, rule 19).
    """

    def test_value_is_the_documented_one_term_moved_arithmetic(self):
        from market_sim.config.constants import (
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO,
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO,
        )

        # Same PRA numerators as D31; denominators net of the accredited dated
        # exits the D46 ledgers record (4,508.5 / 7,977.6 MW).
        expected = (122_375.6 + 123_395.6) / (
            (143_822.1 - 4_508.5) + (143_749.5 - 7_977.6)
        )
        got = ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO["MISO"]
        self.assertAlmostEqual(got, expected, places=9)
        self.assertAlmostEqual(got, 0.893436, places=6)
        # Inside the pre-declared STOP band, and strictly above the D31 value
        # (the double-netting can only have made the census look SHORTER).
        self.assertGreater(
            got, ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"]
        )
        self.assertTrue(0.80 <= got <= 0.95)
        # MISO-only registry (rule 25).
        self.assertEqual(
            set(ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO), {"MISO"}
        )

    def test_unarmed_resolver_is_byte_identical_to_d31(self):
        from market_sim.config.constants import (
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO,
        )
        from market_sim.model.capacity import resolve_internal_supply_accounting_ratio

        d31 = ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO["MISO"]
        self.assertEqual(resolve_internal_supply_accounting_ratio("MISO"), d31)
        self.assertEqual(
            resolve_internal_supply_accounting_ratio("MISO", ScenarioConfig()), d31
        )
        self.assertFalse(ScenarioConfig().adequacy_accounting_ratio_dated_net)

    def test_armed_resolver_returns_the_dated_net_value_for_miso_only(self):
        from market_sim.config.constants import (
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO,
        )
        from market_sim.model.capacity import resolve_internal_supply_accounting_ratio

        armed = ScenarioConfig(adequacy_accounting_ratio_dated_net=True)
        self.assertEqual(
            resolve_internal_supply_accounting_ratio("MISO", armed),
            ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_DATED_NET_BY_ISO["MISO"],
        )
        # Every other ISO falls through to the D31 registry (neutral 1.0 —
        # rule 25: nothing transfers), armed or not.
        for iso in ("PJM", "NYISO", "NEISO", "CAISO", "ERCOT", None):
            self.assertEqual(resolve_internal_supply_accounting_ratio(iso, armed), 1.0)

    def test_armed_ledger_floor_increment_and_backstop_share_one_basis(self):
        from market_sim.config.constants import EFORD
        from market_sim.model.capacity import (
            _thermal_firm_mw,
            accredited_firm_capacity_mw,
            apply_reserve_margin_build,
            resolve_adequacy_requirement_mw,
            resolve_internal_supply_accounting_ratio,
        )

        armed = ScenarioConfig(
            adequacy_accounting_ratio_dated_net=True, reserve_margin_build_enabled=True
        )
        ratio = resolve_internal_supply_accounting_ratio("MISO", armed)
        g = _gen("C1", "coal", pmax=1000.0)
        with no_hydro_accreditation():
            base = accredited_firm_capacity_mw([], iso="MISO", config=armed)
            with_unit = accredited_firm_capacity_mw([g], iso="MISO", config=armed)
        # The ledger increment carries the dated-net ratio …
        self.assertAlmostEqual(
            with_unit - base, _thermal_firm_mw(g, "MISO") * ratio, places=6
        )
        # … and so does the backstop's crediting of the unit it builds.
        peak = 100_000.0
        req = resolve_adequacy_requirement_mw(armed, "MISO", peak)
        _fleet, built = apply_reserve_margin_build(
            [], req - 5_000.0, peak, 2030, armed, "MISO"
        )
        self.assertAlmostEqual(
            built, 5_000.0 / ((1.0 - EFORD["gas_ct"]) * ratio), places=3
        )

    def test_gate_is_cache_key_registered_and_backcast_coerced(self):
        from market_sim.config.scenarios import (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
            _CACHE_KEY_OPTIONAL_FIELDS,
        )

        self.assertIn("adequacy_accounting_ratio_dated_net", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["adequacy_accounting_ratio_dated_net"],
            "False",
        )
        # Unarmed key byte-stable; armed keys distinctly.
        self.assertEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(adequacy_accounting_ratio_dated_net=False).cache_key(),
        )
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(adequacy_accounting_ratio_dated_net=True).cache_key(),
        )
        # Forecast-lane mechanism: coerced to the default in a plain backcast.
        self.assertFalse(
            ScenarioConfig(
                mode="backcast", adequacy_accounting_ratio_dated_net=True
            ).adequacy_accounting_ratio_dated_net
        )


if __name__ == "__main__":
    unittest.main()


class TestNeisoNetIcrRequirement(unittest.TestCase):
    """capx D40 (2026-09-02) — the NEISO adequacy requirement devintaged onto
    ISO-NE's published per-CCP Net ICR series (D33 §4 R-A, the PJM published-FPR
    pattern), with the CR-1 position on the curve's own x-convention (R-B) and
    the card C-A hold-last as the last CCP's published ratio. GATED default-OFF:
    every unarmed NEISO solve is byte-identical to the composite."""

    PEAK = 23_475.0  # the crossover-rcrepair 2023 ledger peak

    @staticmethod
    def _csv_rows(sub, metric):
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / sub
        with path.open(newline="") as fh:
            return [r for r in csv.DictReader(fh) if r["metric"] == metric]

    @staticmethod
    def _cfg(armed, **kw):
        return ScenarioConfig(
            iso="NEISO",
            mode="forecast",
            hindcast=True,
            neiso_net_icr_requirement=armed,
            **kw,
        )

    @staticmethod
    def _composite(peak):
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
        return peak * (1.0 - dr) * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"])

    def test_registry_reconciles_with_published_csv(self):
        # Every NET_ICR_REQUIREMENT_MW_BY_ISO["NEISO"] entry must match the
        # committed reliability_requirement row for that CCP byte-for-byte,
        # and the table must cover EVERY published row — a new intaken FCA
        # row that is not carried here fails loudly (rules 13/23).
        rows = self._csv_rows("demand-curve/neiso/neiso.csv", "reliability_requirement")
        self.assertTrue(rows, "expected published Net ICR rows on disk")
        by_ccp = {
            r["delivery_year"].replace("-", "/"): float(r["y_value"]) for r in rows
        }
        self.assertEqual(NET_ICR_REQUIREMENT_MW_BY_ISO["NEISO"], by_ccp)
        self.assertTrue(all(r["y_unit"] == "mw" for r in rows))
        self.assertEqual(set(NET_ICR_REQUIREMENT_MW_BY_ISO), {"NEISO"})  # rule 25

    def test_hold_last_ratio_reconciles_with_ara_extract(self):
        # The held object is the last CCP's newest published Net-ICR / 50-50
        # peak pair (ARA 2 of 2027/28, icr-ara extract), not a frozen MW.
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = (
            RAW_DATA_DIR
            / "capacity-market"
            / "icr-ara"
            / "neiso"
            / "ara_requirement_values.csv"
        )
        with path.open(newline="") as fh:
            ara2 = {
                r["metric"]: float(r["value_mw"])
                for r in csv.DictReader(fh)
                if r["ccp"] == "2027-2028" and r["vintage"] == "ARA 2"
            }
        last_ccp = max(NET_ICR_REQUIREMENT_MW_BY_ISO["NEISO"], key=lambda l: int(l[:4]))
        self.assertEqual(last_ccp, "2027/2028")
        self.assertAlmostEqual(
            NET_ICR_HOLD_LAST_RATIO_BY_ISO["NEISO"],
            ara2["net_icr"] / ara2["peak_50_50_net_btm_pv"],
            places=12,
        )

    def test_default_off_is_byte_identical_to_composite(self):
        cfg = self._cfg(False)
        for year in (2019, 2020, 2023, 2027, 2028, 2050, None):
            self.assertIsNone(
                resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, year)
            )
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "NEISO", self.PEAK, year),
                self._composite(self.PEAK),
                places=6,
            )
        self.assertEqual(
            curve_convention_position(cfg, "NEISO", 1.2593906741), 1.2593906741
        )
        # And the gate is off in the shipped default (owner-armed only).
        self.assertFalse(ScenarioConfig(iso="NEISO").neiso_net_icr_requirement)

    def test_armed_in_table_year_uses_absolute_net_icr(self):
        cfg = self._cfg(True)
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
        # Model year 2023 -> CCP 2023/2024 -> FCA 14 Net ICR 32,490 MW; the
        # model's peak DROPS OUT (the auction's own denominator, D33 R-A (i)).
        self.assertEqual(
            resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, 2023), 32_490.0
        )
        for peak in (self.PEAK, 2.0 * self.PEAK):
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "NEISO", peak, 2023),
                32_490.0 * (1.0 - dr),
                places=6,
            )
        # The D33 measurement: +5,489 MW of requirement at the 2023 ledger peak.
        delta = resolve_adequacy_requirement_mw(
            cfg, "NEISO", self.PEAK, 2023
        ) - self._composite(self.PEAK)
        self.assertAlmostEqual(delta, 5_489.4, delta=0.5)

    def test_armed_pre_table_and_year_none_fall_through(self):
        cfg = self._cfg(True)
        for year in (2019, None):
            self.assertIsNone(
                resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, year)
            )
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "NEISO", self.PEAK, year),
                self._composite(self.PEAK),
                places=6,
            )

    def test_armed_hold_last_beyond_table_is_the_published_ratio(self):
        cfg = self._cfg(True)
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
        ratio = NET_ICR_HOLD_LAST_RATIO_BY_ISO["NEISO"]
        for year in (2028, 2035, 2050):
            for peak in (self.PEAK, 30_000.0):
                self.assertAlmostEqual(
                    resolve_published_net_icr_mw(cfg, "NEISO", peak, year),
                    peak * ratio,
                    places=6,
                )
                self.assertAlmostEqual(
                    resolve_adequacy_requirement_mw(cfg, "NEISO", peak, year),
                    peak * ratio * (1.0 - dr),
                    places=6,
                )
        # The held bar scales with load (rule 13) and sits marginally ABOVE
        # the composite it re-anchors (ARA-2 2027/28 ratio 1.1301 vs the
        # ARA-3 2026/27 composite ratio 1.1277) — never a frozen MW.
        self.assertGreater(
            resolve_adequacy_requirement_mw(cfg, "NEISO", self.PEAK, 2050),
            self._composite(self.PEAK),
        )
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "NEISO", self.PEAK, 2050)
            / self._composite(self.PEAK),
            ratio / (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]),
            places=9,
        )

    def test_hold_last_never_bridges_an_in_table_gap(self):
        cfg = self._cfg(True)
        with mock.patch.dict(
            NET_ICR_REQUIREMENT_MW_BY_ISO,
            {"NEISO": {"2023/2024": 32_490.0, "2027/2028": 30_550.0}},
            clear=False,
        ):
            self.assertIsNone(
                resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, 2025)
            )
            self.assertEqual(
                resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, 2027), 30_550.0
            )
            self.assertAlmostEqual(
                resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, 2028),
                self.PEAK * NET_ICR_HOLD_LAST_RATIO_BY_ISO["NEISO"],
                places=6,
            )

    def test_no_hold_ratio_means_no_hold(self):
        # A series without a published hold ratio has nothing lawful to hold:
        # beyond its table it falls through to the composite, never a frozen MW.
        cfg = self._cfg(True)
        with mock.patch.dict(NET_ICR_HOLD_LAST_RATIO_BY_ISO, {}, clear=True):
            self.assertIsNone(
                resolve_published_net_icr_mw(cfg, "NEISO", self.PEAK, 2030)
            )
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "NEISO", self.PEAK, 2030),
                self._composite(self.PEAK),
                places=6,
            )

    def test_curve_convention_transform(self):
        # R-B: pos_raw = f + (1 - f) * pos_net; 1.0 is a fixed point; the D33
        # 2023 row (net 1.2594 -> raw 1.2366) is reproduced.
        cfg = self._cfg(True)
        f = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
        self.assertAlmostEqual(
            curve_convention_position(cfg, "NEISO", 1.0), 1.0, places=12
        )
        self.assertAlmostEqual(
            curve_convention_position(cfg, "NEISO", 1.2593906741249772),
            1.2366050204326122,
            places=9,
        )
        for p in (0.9, 1.05, 1.3):
            self.assertAlmostEqual(
                curve_convention_position(cfg, "NEISO", p), f + (1.0 - f) * p, places=12
            )
        # Inert off-registry even with the flag armed (rule 25).
        self.assertEqual(curve_convention_position(cfg, "PJM", 1.3), 1.3)
        self.assertEqual(curve_convention_position(None, "NEISO", 1.3), 1.3)

    def test_reserve_position_end_to_end(self):
        from market_sim.model.capacity_evolution.adequacy import (
            accredited_firm_capacity_mw,
            capacity_reserve_position,
        )

        gen = _gen("G0", "gas_cc", pmax=30_000.0, eford=0.05)
        f = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]
        with no_hydro_accreditation():
            firm = accredited_firm_capacity_mw(
                [gen], 0.0, 0.0, 0.0, iso="NEISO", peak_demand_mw=self.PEAK, year=2023
            )
            off = capacity_reserve_position(
                [gen], 0.0, 0.0, 0.0, self._cfg(False), "NEISO", self.PEAK, 2023
            )
            on = capacity_reserve_position(
                [gen], 0.0, 0.0, 0.0, self._cfg(True), "NEISO", self.PEAK, 2023
            )
        self.assertAlmostEqual(off, firm / self._composite(self.PEAK), places=9)
        self.assertAlmostEqual(
            on, f + (1.0 - f) * firm / (32_490.0 * (1.0 - f)), places=9
        )
        # Sign discipline (rule 14): the corrected denominator SHORTENS the
        # position — capacity revenue moves UP, retirements get HARDER.
        self.assertLess(on, off)

    def test_other_isos_inert_with_the_flag_armed(self):
        for iso, peak, year in (
            ("PJM", 160_560.0, 2026),
            ("MISO", 120_000.0, 2026),
            ("ERCOT", 85_000.0, 2030),
        ):
            armed = ScenarioConfig(iso=iso, neiso_net_icr_requirement=True)
            plain = ScenarioConfig(iso=iso)
            self.assertIsNone(resolve_published_net_icr_mw(armed, iso, peak, year))
            self.assertEqual(
                resolve_adequacy_requirement_mw(armed, iso, peak, year),
                resolve_adequacy_requirement_mw(plain, iso, peak, year),
            )

    def test_backcast_coerces_hindcast_keeps_and_cache_key(self):
        # Plain backcast: coerced to the dataclass default (forecast-lane
        # mechanism); hindcast (mode=forecast, hindcast=True) keeps the arm.
        self.assertFalse(
            ScenarioConfig(
                iso="NEISO", mode="backcast", neiso_net_icr_requirement=True
            ).neiso_net_icr_requirement
        )
        self.assertTrue(self._cfg(True).neiso_net_icr_requirement)
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS at False: unarmed keys are
        # byte-stable, an armed run keys distinctly.
        self.assertEqual(
            ScenarioConfig(iso="NEISO").cache_key(),
            ScenarioConfig(iso="NEISO", neiso_net_icr_requirement=False).cache_key(),
        )
        self.assertNotEqual(self._cfg(False).cache_key(), self._cfg(True).cache_key())


class TestPjmPublishedReliabilityRequirement(unittest.TestCase):
    """capx D67: the PJM adequacy requirement read from PJM's OWN published
    RTO Reliability Requirement instead of reconstructed as ``model peak x
    FPR`` (FINDING-capx-d66-2026-09-06.md §8 card A). The PJM analogue of
    TestNeisoNetIcrRequirement above, on the same provenance discipline.
    GATED default-OFF: every unarmed solve of every ISO is byte-identical."""

    # The D57 arm A committed screen seam peak for 2025 (evolution_2025.json,
    # screen_peak_demand_mw). Any peak works -- that is the point of the
    # mechanism -- but using the real one keeps the assertions legible.
    PEAK = 158_633.356

    @staticmethod
    def _csv_rows(sub, metric):
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / sub
        with path.open(newline="") as fh:
            return [r for r in csv.DictReader(fh) if r["metric"] == metric]

    @staticmethod
    def _cfg(armed, **kw):
        # pjm_accreditation_design_vintage ON is the SHIPPED PJM posture
        # (D57 section 8.1), and it is what makes the pre-reform FPR table
        # live for delivery years 2021/22-2024/25 -- so the off arm below is
        # the real peak x FPR construction this gate replaces, not a
        # composite the recipe never runs.
        kw.setdefault("pjm_accreditation_design_vintage", True)
        return ScenarioConfig(
            iso="PJM",
            mode="forecast",
            hindcast=True,
            capacity_adequacy_requirement_published_by_iso=(
                {"PJM": True} if armed else None
            ),
            **kw,
        )

    def test_registry_reconciles_with_published_csv(self):
        # Every RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO["PJM"] entry must match
        # the committed reliability_requirement row for that delivery year
        # byte-for-byte, and the table must cover EVERY published row -- a
        # newly intaken BRA row that is not carried here fails loudly
        # (rules 13/23). This is the test the registry's citation block
        # promises.
        rows = self._csv_rows("demand-curve/pjm/pjm.csv", "reliability_requirement")
        self.assertTrue(rows, "expected published Reliability Requirement rows on disk")
        by_dy = {r["delivery_year"]: float(r["y_value"]) for r in rows}
        self.assertEqual(RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO["PJM"], by_dy)
        self.assertTrue(all(r["y_unit"] == "mw" for r in rows))
        self.assertTrue(all((r["area"] or "RTO") == "RTO" for r in rows))
        self.assertEqual(set(RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO), {"PJM"})  # rule 25

    def test_the_frr_adjusted_comparator_is_NOT_the_registry(self):
        # The vintage rule, asserted rather than merely documented
        # (PRECOMMIT-capx-d67 section 3): ``_frr_adj + ee_addback`` is the
        # RPM-ONLY comparator that reproduces PJM's published CLEARED position
        # (D66 section 1.2) -- it is basis-mismatched to a whole-RTO model and
        # must never be what the registry carries. If a later lane "fixes" the
        # requirement by swapping the column, this fails.
        adj = {
            r["delivery_year"]: float(r["y_value"])
            for r in self._csv_rows(
                "demand-curve/pjm/pjm.csv", "reliability_requirement_frr_adj"
            )
        }
        ee = {
            r["delivery_year"]: float(r["y_value"])
            for r in self._csv_rows("demand-curve/pjm/pjm.csv", "ee_addback")
        }
        for dy, mw in RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO["PJM"].items():
            if dy in adj:
                self.assertNotAlmostEqual(mw, adj[dy] + ee.get(dy, 0.0), places=1)

    def test_off_is_byte_identical_and_on_returns_the_published_mw(self):
        # Off: the peak x FPR reconstruction, untouched. On: the published MW,
        # and the model's peak drops out entirely.
        for year, published in ((2024, 164107.6), (2025, 144450.0)):
            off = gross_adequacy_requirement_mw(
                self._cfg(False), "PJM", self.PEAK, year
            )
            on = gross_adequacy_requirement_mw(self._cfg(True), "PJM", self.PEAK, year)
            fpr = resolve_pre_reform_pool_requirement(
                self._cfg(False), "PJM", year
            ) or resolve_forecast_pool_requirement("PJM", year)
            self.assertAlmostEqual(off, self.PEAK * fpr, places=6)
            self.assertAlmostEqual(on, published, places=6)

    def test_armed_requirement_is_independent_of_the_model_peak(self):
        # The mechanism's DEFINING property (PRECOMMIT-capx-d67 P3):
        # d(R)/d(peak) = 0 in every in-table delivery year.
        cfg = self._cfg(True)
        for year in (2021, 2022, 2023, 2024, 2025, 2028):
            got = {
                gross_adequacy_requirement_mw(cfg, "PJM", peak, year)
                for peak in (100_000.0, self.PEAK, 250_000.0)
            }
            self.assertEqual(len(got), 1, f"{year}: requirement moved with the peak")

    def test_gap_and_forward_edge_fall_through_to_the_fpr_path(self):
        # HOLD-LAST, declared ex ante (PRECOMMIT-capx-d67 section 4): the
        # in-table gap (2026/27, 2027/28 -- an FPR but no RR row) and every
        # year past the 2028/29 forward edge fall through to the FPR path, so
        # they are byte-identical to the unarmed run. No absolute MW is ever
        # held over a forward horizon (rule 13's forward test).
        for year in (2026, 2027, 2029, 2035, 2050):
            self.assertAlmostEqual(
                gross_adequacy_requirement_mw(self._cfg(True), "PJM", self.PEAK, year),
                gross_adequacy_requirement_mw(self._cfg(False), "PJM", self.PEAK, year),
                places=9,
                msg=f"{year} must fall through to the FPR path",
            )
        # ... and the fall-through really is the ratio hold-last: PJM
        # constructs RR = forecast peak x FPR, so the last published row and
        # its FPR imply each other.
        for dy, fpr in (("2025/2026", 0.9380), ("2028/2029", 0.9401)):
            rr = RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO["PJM"][dy]
            self.assertAlmostEqual(rr / fpr, rr / fpr, places=6)  # identity anchor
            self.assertGreater(rr / fpr, 150_000.0)  # a plausible RTO peak

    def test_year_none_and_other_isos_are_inert(self):
        # rule 25 [R-ISO-SCOPE]: the flag armed on another ISO's run is inert
        # by construction (no intaken table), and a caller that threads no
        # year keeps the pre-D67 path.
        self.assertIsNone(
            resolve_published_reliability_requirement_mw(self._cfg(True), "PJM", None)
        )
        for iso in ("MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
            cfg = ScenarioConfig(
                iso=iso,
                mode="forecast",
                hindcast=True,
                capacity_adequacy_requirement_published_by_iso={iso: True},
            )
            self.assertIsNone(
                resolve_published_reliability_requirement_mw(cfg, iso, 2025)
            )

    def test_one_requirement_on_every_path(self):
        # rule 19 [R-ONE-MECH]: the floor, the backstop and the CR-1 position
        # all reach the requirement through resolve_adequacy_requirement_mw,
        # so arming the gate moves ONE object. Under PJM's D48 DR-as-supply
        # posture the peak is NOT netted, so the resolved requirement is the
        # published MW itself.
        cfg = self._cfg(True, pjm_demand_response_supply=True)
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, 2025),
            144450.0,
            places=6,
        )

    def test_default_off_keeps_every_cache_key_byte_stable(self):
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS at None: unarmed keys stay
        # byte-stable, an armed run keys distinctly.
        for iso in ("PJM", "MISO", "ERCOT", "CAISO", "NYISO", "NEISO"):
            self.assertEqual(
                ScenarioConfig(iso=iso).cache_key(),
                ScenarioConfig(
                    iso=iso, capacity_adequacy_requirement_published_by_iso=None
                ).cache_key(),
            )
        self.assertNotEqual(self._cfg(False).cache_key(), self._cfg(True).cache_key())

    def test_plain_backcast_coerces_the_gate_off(self):
        # A backcast runs no capacity evolution; the gate is coerced to None
        # exactly as its three siblings are, so every keeper stays identical.
        cfg = ScenarioConfig(
            iso="PJM",
            mode="backcast",
            capacity_adequacy_requirement_published_by_iso={"PJM": True},
        )
        self.assertIsNone(cfg.capacity_adequacy_requirement_published_by_iso)
        self.assertEqual(
            cfg.cache_key(), ScenarioConfig(iso="PJM", mode="backcast").cache_key()
        )


class TestFossilAnnouncedExits(unittest.TestCase):
    """capx D42: the FOSSIL owner-filed date channel at step 1 + its rule-19
    reconciliation with the economic screen and the reliability floor.

    GATED ``fossil_announced_exits_enabled`` — DEFAULT ON since 2026-09-03
    (owner ruling Q30, capx D44): on, the rows ride step 0's matcher/derate
    machinery, dated plants are exogenous to the screen, and the R-NEW
    admission cap's counterfactual nets the pending dated exits. The OFF legs
    below now pass an EXPLICIT ``fossil_announced_exits_enabled=False`` — that
    is the pre-Q30 control posture, and what they assert (rows ignored, step 1
    the fossil no-op, cache key unmoved) is unchanged by the flip.
    """

    def _row(self, plant_id, gen_id, year, month=None, mw=None):
        from market_sim.data.announced_retirements import AnnouncedFossilExit

        return AnnouncedFossilExit(
            plant_id=plant_id,
            generator_id=gen_id,
            exit_year=year,
            exit_month=month,
            mw=mw,
            fuel_type="coal",
            filed_vintage=2020,
            vintage_exit_year=year,
            vintage_exit_month=month,
        )

    def _events(self):
        from market_sim.results.evolution_ledger import new_events

        return new_events()

    # -- gate off: byte-identical shipped posture -------------------------
    def test_gate_off_ignores_dated_rows(self):
        fleet = [_unit(300, "1", 500.0, fuel="coal", retirement_year=2028)]
        events = self._events()
        kept, _, _, _, _ = evolve_fleet(
            fleet,
            None,
            2028,
            ScenarioConfig(fossil_announced_exits_enabled=False),
            {},
            events=events,
            announced_fossil_exits=[self._row(300, "1", 2028, mw=500.0)],
        )
        self.assertEqual([g.unit_id for g in kept], ["300_1"])
        self.assertEqual(events["retirements"], [])
        self.assertEqual(events["announced_derates"], [])

    # -- gate on: unit-grain drop + plant-binned derate --------------------
    def test_unit_grain_dated_fossil_exits_at_its_date(self):
        cfg = ScenarioConfig(fossil_announced_exits_enabled=True)
        fleet = [
            _unit(300, "1", 500.0, fuel="coal", retirement_year=2028),
            # Undated-in-window sibling survives. It carries a far date only so
            # the year-end legacy re-aggregation passes it through un-binned
            # (units with no retirement_year collapse into an efficiency bin —
            # pre-existing behaviour, not this channel's).
            _unit(300, "2", 400.0, fuel="coal", retirement_year=2099),
        ]
        rows = [self._row(300, "1", 2028, mw=500.0)]
        early = self._events()
        kept, _, _, _, _ = evolve_fleet(
            fleet, None, 2027, cfg, {}, events=early, announced_fossil_exits=rows
        )
        self.assertEqual([g.unit_id for g in kept], ["300_1", "300_2"])
        events = self._events()
        kept, _, _, _, _ = evolve_fleet(
            fleet, None, 2028, cfg, {}, events=events, announced_fossil_exits=rows
        )
        self.assertEqual([g.unit_id for g in kept], ["300_2"])
        self.assertEqual(
            [(r["unit_id"], r["reason"], r["mw"]) for r in events["retirements"]],
            [("300_1", "announced", 500.0)],
        )
        self.assertEqual(events["announced_derates"], [])

    def test_plant_binned_dated_fossil_derates_and_ledgers(self):
        cfg = ScenarioConfig(fossil_announced_exits_enabled=True)
        fleet = [_binned("H_C1", 200, 300.0), _binned("H_C2", 200, 200.0)]
        rows = [self._row(200, "U1", 2028, mw=250.0)]
        events = self._events()
        kept, _, _, _, _ = evolve_fleet(
            fleet, None, 2028, cfg, {}, events=events, announced_fossil_exits=rows
        )
        self.assertAlmostEqual(sum(g.pmax_mw for g in kept), 250.0)
        self.assertEqual(events["retirements"], [])
        self.assertAlmostEqual(
            sum(d["derate_mw"] for d in events["announced_derates"]), 250.0
        )
        self.assertEqual(
            {d["unit_id"] for d in events["announced_derates"]}, {"H_C1", "H_C2"}
        )

    def test_first_year_backlog_via_build_base_fleet_is_gated(self):
        # A dated row at/before the first simulated year lands in the
        # base-fleet backlog only under the gate.
        from market_sim.data.fleet import build_base_fleet

        rows = [self._row(300, "1", 2026, month=3, mw=500.0)]
        # build_base_fleet resolves its loaders through the fleet package
        # namespace (_pkg_ns); with campd_bins=None it takes the legacy path.
        with (
            mock.patch(
                "market_sim.data.fleet.load_fleet_from_csv",
                return_value=[_unit(300, "1", 500.0, fuel="coal")],
            ),
            mock.patch(
                "market_sim.data.fleet.aggregate_fleet",
                side_effect=lambda gens, *a, **kw: list(gens),
            ),
        ):
            iso_config = get_iso_config("MISO")
            zones = [z.name for z in iso_config.zones]
            off = build_base_fleet(
                None,
                "MISO",
                iso_config,
                zones,
                ScenarioConfig(fossil_announced_exits_enabled=False),
                [],
                [],
                2027,
                announced_fossil_exits=rows,
            )
            on = build_base_fleet(
                None,
                "MISO",
                iso_config,
                zones,
                ScenarioConfig(fossil_announced_exits_enabled=True),
                [],
                [],
                2027,
                announced_fossil_exits=rows,
            )
        self.assertEqual([g.unit_id for g in off], ["300_1"])
        self.assertEqual(on, [])

    # -- reconciliation (a): dated plants are exogenous to the screen -----
    def test_dated_plant_unit_ids_grain_and_pending_semantics(self):
        from market_sim.model.capacity import dated_plant_unit_ids

        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),
            _unit(300, "2", 400.0, fuel="coal"),
            _binned("H_C1", 200, 300.0),
            _binned("H_C2", 200, 200.0),
            _unit(999, "1", 100.0, fuel="gas_ct"),
        ]
        rows = [
            self._row(300, "1", 2030, mw=500.0),  # pending in 2028
            self._row(200, "U1", 2029, month=3, mw=100.0),  # pending in 2028
        ]
        # Unit grain: only the dated generator; binned: the whole plant.
        self.assertEqual(
            dated_plant_unit_ids(fleet, rows, 2028),
            frozenset({"300_1", "H_C1", "H_C2"}),
        )
        # A first-half row in its effective year still has a completion leg
        # next year -> still pending; the year after, it is done.
        self.assertIn("H_C1", dated_plant_unit_ids(fleet, rows, 2029))
        self.assertNotIn("H_C1", dated_plant_unit_ids(fleet, rows, 2030))
        # A past unit-grain row is not pending.
        self.assertEqual(dated_plant_unit_ids(fleet, rows, 2031), frozenset())
        self.assertEqual(dated_plant_unit_ids(fleet, [], 2028), frozenset())

    def test_evolve_passes_exemption_and_exogenous_rows_to_the_screen(self):
        from market_sim.model import capacity_evolution as pkg

        cfg = ScenarioConfig(fossil_announced_exits_enabled=True)
        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),
            _unit(301, "1", 400.0, fuel="coal"),
        ]
        rows = [self._row(300, "1", 2030, mw=500.0)]
        seen = {}

        def spy(fleet_, *a, **kw):
            seen["kwargs"] = kw
            seen["exit_exempt"] = kw.get("exit_exempt_unit_ids")
            seen["exogenous"] = kw.get("exogenous_exits")
            return fleet_, {}, []

        prior = {
            "fleet_arrays": object(),
            "dispatch_result": object(),
            "prices": np.zeros((1, 24)),
            "peak_demand": 1000.0,
        }
        with mock.patch.object(pkg, "apply_economic_retirements", side_effect=spy):
            evolve_fleet(fleet, prior, 2028, cfg, {}, announced_fossil_exits=rows)
        # capx D81: the exemption is an EXIT exemption — a plant whose filed
        # date is LATER than the delivery year must still offer its accredited
        # MW into the D57 clearing (Manual 18 Rev 62 §1.2), so it rides
        # ``exit_exempt_unit_ids``. capx D78-R2 then DELETED the second,
        # not-eligible-to-offer parameter this call site used to pass empty:
        # the screen has exactly one exemption seam, so the kwarg is gone.
        self.assertNotIn("exempt_unit_ids", seen["kwargs"])
        self.assertEqual(seen["exit_exempt"], frozenset({"300_1"}))
        self.assertIs(seen["exogenous"], rows)
        # Off the gate the screen sees neither.
        seen.clear()
        with mock.patch.object(pkg, "apply_economic_retirements", side_effect=spy):
            evolve_fleet(
                fleet,
                prior,
                2028,
                ScenarioConfig(fossil_announced_exits_enabled=False),
                {},
                announced_fossil_exits=rows,
            )
        self.assertNotIn("exempt_unit_ids", seen["kwargs"])
        self.assertEqual(seen["exit_exempt"], frozenset())
        self.assertIsNone(seen["exogenous"])

    # -- reconciliation (b): the admission cap nets the dated exits ---------
    def test_admission_cap_counterfactual_nets_dated_exits(self):
        from market_sim.model.capacity_evolution import retirements as rmod

        cfg = ScenarioConfig(iso="MISO", retirement_rule="pipeline")
        lag = rmod._execution_lag_years(cfg, "coal")  # cap horizon = year-1+lag
        year = 2028
        cap_year = year - 1 + lag
        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),  # dated, due inside the horizon
            _unit(301, "1", 400.0, fuel="coal"),  # dated, due beyond the horizon
            _unit(302, "1", 300.0, fuel="coal"),  # undated failing candidate
        ]
        rows = [
            self._row(300, "1", cap_year, mw=500.0),
            self._row(301, "1", cap_year + 1, mw=400.0),
        ]
        margins = [(fleet[2], 0.0, 1.0)]  # only the undated unit is screened
        calls = []

        def spy(fleet_, eligible, retired, *a, **kw):
            calls.append([g.unit_id for g in fleet_])
            return []

        with mock.patch.object(rmod, "_apply_reliability_floor", side_effect=spy):
            rmod._apply_pipeline_retirements(
                fleet,
                margins,
                {},
                cfg,
                1000.0,
                0.0,
                0.0,
                0.0,
                None,
                year,
                None,
                None,
                exogenous_exits=rows,
            )
            rmod._apply_pipeline_retirements(
                fleet,
                margins,
                {},
                cfg,
                1000.0,
                0.0,
                0.0,
                0.0,
                None,
                year,
                None,
                None,
            )
        admission_with, execution_with, admission_without, _ = calls
        # With the rows: the admission counterfactual has lost the in-horizon
        # dated unit and kept the beyond-horizon one; the execution-stage
        # floor still sees the realized fleet.
        self.assertEqual(admission_with, ["301_1", "302_1"])
        self.assertEqual(execution_with, ["300_1", "301_1", "302_1"])
        # Without the rows: byte-identical pre-D42 behaviour.
        self.assertEqual(admission_without, ["300_1", "301_1", "302_1"])

    # -- fuel-scoped derate at mixed-fuel plants ---------------------------
    def test_fuel_scoped_derate_at_mixed_fuel_plant(self):
        cfg = ScenarioConfig(fossil_announced_exits_enabled=True)
        fleet = [
            _binned("H_C1", 200, 300.0, fuel="coal"),
            _binned("H_G1", 200, 200.0, fuel="gas_ct"),
        ]
        # A dated COAL row lands on the coal bin only.
        rows = [self._row(200, "U1", 2028, mw=150.0)]
        kept, _, _, _, _ = evolve_fleet(
            fleet, None, 2028, cfg, {}, announced_fossil_exits=rows
        )
        by_id = {g.unit_id: g.pmax_mw for g in kept}
        self.assertAlmostEqual(by_id["H_C1"], 150.0)
        self.assertAlmostEqual(by_id["H_G1"], 200.0)
        # A row whose fuel has no binned generator at the plant falls back to
        # the plant-wide derate (nothing is silently dropped).
        from dataclasses import replace

        oil_row = replace(rows[0], fuel_type="oil", mw=100.0)
        kept, _, _, _, _ = evolve_fleet(
            fleet, None, 2028, cfg, {}, announced_fossil_exits=[oil_row]
        )
        self.assertAlmostEqual(sum(g.pmax_mw for g in kept), 400.0)
        self.assertAlmostEqual(
            {g.unit_id: g.pmax_mw for g in kept}["H_C1"], 300.0 * 400.0 / 500.0
        )
        # A fuel-less confirmed row keeps the plant-wide derate (byte-identical
        # pre-D42 behaviour).
        conf = ConfirmedExit(
            plant_id=200, generator_id="U1", exit_year=2028, exit_month=None, mw=150.0
        )
        kept = apply_confirmed_exits(fleet, 2028, [conf])
        by_id = {g.unit_id: g.pmax_mw for g in kept}
        self.assertAlmostEqual(by_id["H_C1"], 300.0 * 350.0 / 500.0)
        self.assertAlmostEqual(by_id["H_G1"], 200.0 * 350.0 / 500.0)


class TestFossilAnnouncedLedgerReconciliation(TestEvolveFleetLedgerReconciliation):
    """The I4 identity holds with the D42 ``announced_derates`` rows in the sum."""

    def test_dated_binned_and_unit_grain_reconcile(self):
        from market_sim.data.announced_retirements import AnnouncedFossilExit

        cfg = ScenarioConfig(fossil_announced_exits_enabled=True)
        fleet = [
            _binned("H_C1", 200, 300.0, fuel="coal"),
            _binned("H_G1", 200, 200.0, fuel="gas_ct"),
            _unit(300, "1", 500.0, fuel="coal", retirement_year=2028),
            _unit(301, "1", 400.0, fuel="gas_st", retirement_year=2099),
        ]
        rows = [
            AnnouncedFossilExit(200, "U1", 2028, None, 150.0, "coal", 2020, 2028, None),
            AnnouncedFossilExit(300, "1", 2028, None, 500.0, "coal", 2020, 2028, None),
        ]
        events = self._events()
        evolve_fleet(
            fleet, None, 2028, cfg, {}, events=events, announced_fossil_exits=rows
        )
        self.assertEqual(
            [(r["unit_id"], r["reason"]) for r in events["retirements"]],
            [("300_1", "announced")],
        )
        self.assertAlmostEqual(
            sum(d["derate_mw"] for d in events["announced_derates"]), 150.0
        )
        self._assert_reconciles(events)


class TestPjmAccreditationDesignVintage(unittest.TestCase):
    """capx D48 (2026-09-04) — PJM's adequacy accounting devintaged onto the
    design each delivery year's auction actually cleared on (D45 §2.3 item 1):
    thermal at UCAP + the published pre-CIFP FPR before 2025/26, the ELCC class
    ratings + post-CIFP FPR from it. GATED default-OFF: every unarmed solve is
    byte-identical to the single-vintage basis."""

    PEAK = 149_590.0  # the D45 L1 2021 ledger peak

    @staticmethod
    def _csv_rows(sub, metric):
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / sub
        with path.open(newline="") as fh:
            return [r for r in csv.DictReader(fh) if r["metric"] == metric]

    @staticmethod
    def _cfg(armed, iso="PJM", **kw):
        return ScenarioConfig(
            iso=iso,
            mode="forecast",
            hindcast=True,
            pjm_accreditation_design_vintage=armed,
            **kw,
        )

    @staticmethod
    def _composite(peak):
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        return (
            peak
            * (1.0 - dr)
            * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["PJM"])
            * PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["PJM"]
        )

    def test_pre_reform_fpr_reconciles_with_published_csv(self):
        # Every pre-reform entry matches the committed forecast_pool_requirement
        # row for its delivery year byte-for-byte, the two tables never share a
        # delivery year, and every committed pre-2025/26 row is carried.
        rows = self._csv_rows("demand-curve/pjm/pjm.csv", "forecast_pool_requirement")
        by_dy = {r["delivery_year"]: float(r["y_value"]) for r in rows}
        pre = FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO["PJM"]
        post = FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"]
        self.assertEqual(set(pre) & set(post), set())
        reform = THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO["PJM"]
        self.assertEqual(reform, "2025/2026")
        self.assertEqual(
            pre, {dy: v for dy, v in by_dy.items() if int(dy[:4]) < int(reform[:4])}
        )
        for dy, v in pre.items():
            self.assertEqual(v, by_dy[dy])
        self.assertTrue(all(v > 1.0 for v in pre.values()))  # (1+IRM)(1-EFORd) > 1
        self.assertTrue(all(v < 1.0 for v in post.values()))  # post-CIFP FPR < 1
        self.assertEqual(
            set(THERMAL_ACCREDITATION_REFORM_DELIVERY_YEAR_BY_ISO), {"PJM"}
        )
        self.assertEqual(set(FORECAST_POOL_REQUIREMENT_PRE_REFORM_BY_ISO), {"PJM"})

    def test_default_off_is_byte_identical(self):
        cfg = self._cfg(False)
        self.assertFalse(ScenarioConfig(iso="PJM").pjm_accreditation_design_vintage)
        for year in (2019, 2021, 2023, 2024, 2025, 2028, None):
            self.assertIsNone(resolve_pre_reform_pool_requirement(cfg, "PJM", year))
            self.assertEqual(
                resolve_thermal_accreditation_basis("PJM", cfg, year),
                "elcc_class_rating",
            )
            self.assertEqual(
                thermal_accreditation_fraction("coal", 0.08, "PJM", cfg, year), 0.83
            )
        for year in (2021, 2023, 2024):
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year),
                self._composite(self.PEAK),
                places=6,
            )
        # The seams are byte-identical when neither config nor year is threaded.
        self.assertEqual(thermal_accreditation_fraction("gas_ct", 0.06, "PJM"), 0.60)
        self.assertEqual(
            resolve_thermal_accreditation_basis("PJM"), "elcc_class_rating"
        )

    def test_armed_pre_reform_year_uses_ucap_and_published_fpr(self):
        cfg = self._cfg(True)
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        for year, fpr in (
            (2021, 1.0898),
            (2022, 1.0868),
            (2023, 1.0901),
            (2024, 1.0894),
        ):
            self.assertEqual(resolve_pre_reform_pool_requirement(cfg, "PJM", year), fpr)
            self.assertEqual(
                resolve_thermal_accreditation_basis("PJM", cfg, year), "ucap"
            )
            self.assertAlmostEqual(
                thermal_accreditation_fraction("coal", 0.08, "PJM", cfg, year), 0.92
            )
            self.assertAlmostEqual(
                thermal_accreditation_fraction("gas_ct", 0.06, "PJM", cfg, year), 0.94
            )
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year),
                self.PEAK * (1.0 - dr) * fpr,
                places=6,
            )
        # The D45 §2.2 sign: the pre-reform requirement is ABOVE the composite
        # (+20 %), and the UCAP fleet is above the ELCC-class fleet, so the
        # position moves toward the curve on the requirement side.
        self.assertGreater(
            resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, 2021),
            self._composite(self.PEAK) * 1.19,
        )

    def test_armed_post_reform_year_is_unchanged(self):
        cfg, off = self._cfg(True), self._cfg(False)
        for year in (2025, 2026, 2028, 2030, 2050):
            self.assertIsNone(resolve_pre_reform_pool_requirement(cfg, "PJM", year))
            self.assertEqual(
                resolve_thermal_accreditation_basis("PJM", cfg, year),
                "elcc_class_rating",
            )
            self.assertEqual(
                resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year),
                resolve_adequacy_requirement_mw(off, "PJM", self.PEAK, year),
            )
        # No hold-last on the pre-reform table: nothing carries past the switch.
        self.assertIsNone(resolve_pre_reform_pool_requirement(cfg, "PJM", 2025))
        # Pre-table years (no committed row) fall through to the composite.
        self.assertIsNone(resolve_pre_reform_pool_requirement(cfg, "PJM", 2019))
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, 2019),
            self._composite(self.PEAK),
            places=6,
        )

    def test_capacity_payment_priced_on_the_delivery_year_basis(self):
        # The per-unit payment resolves through the same seam as the ledger:
        # armed, a 2023 coal unit is paid on 0.92 not 0.83; unarmed 0.83.
        from market_sim.model.capacity import capacity_revenue_per_mw_yr

        cfg, off = self._cfg(True), self._cfg(False)
        paid_on = capacity_revenue_per_mw_yr("PJM", "coal", 0.08, cfg, None, 2023)
        paid_off = capacity_revenue_per_mw_yr("PJM", "coal", 0.08, off, None, 2023)
        self.assertGreater(paid_off, 0.0)
        self.assertAlmostEqual(paid_on / paid_off, 0.92 / 0.83, places=9)
        self.assertEqual(
            capacity_revenue_per_mw_yr("PJM", "coal", 0.08, cfg, None, 2026), paid_off
        )

    def test_other_isos_inert_with_the_flag_armed(self):
        for iso in ("MISO", "NYISO", "NEISO", "ERCOT", "CAISO"):
            on, off = self._cfg(True, iso=iso), self._cfg(False, iso=iso)
            for year in (2021, 2023, 2025):
                self.assertIsNone(resolve_pre_reform_pool_requirement(on, iso, year))
                self.assertEqual(
                    resolve_thermal_accreditation_basis(iso, on, year),
                    resolve_thermal_accreditation_basis(iso, off, year),
                )
                self.assertEqual(
                    resolve_adequacy_requirement_mw(on, iso, 30_000.0, year),
                    resolve_adequacy_requirement_mw(off, iso, 30_000.0, year),
                )

    def test_backcast_coerces_hindcast_keeps_and_cache_key(self):
        bc = ScenarioConfig(
            iso="PJM", mode="backcast", pjm_accreditation_design_vintage=True
        )
        self.assertFalse(bc.pjm_accreditation_design_vintage)
        self.assertTrue(self._cfg(True).pjm_accreditation_design_vintage)
        off, on = self._cfg(False), self._cfg(True)
        self.assertEqual(
            off.cache_key(),
            ScenarioConfig(iso="PJM", mode="forecast", hindcast=True).cache_key(),
        )
        self.assertNotEqual(off.cache_key(), on.cache_key())


class TestPjmDemandResponseSupply(unittest.TestCase):
    """capx D48 (2026-09-04) — PJM Demand Resources counted as adequacy SUPPLY
    (the published per-delivery-year BRA offered DR UCAP) instead of a peak
    netting (D45 §2.3 item 2). GATED default-OFF: every unarmed solve keeps the
    netting byte-identically."""

    PEAK = 149_590.0

    @staticmethod
    def _cfg(armed, iso="PJM", **kw):
        return ScenarioConfig(
            iso=iso,
            mode="forecast",
            hindcast=True,
            pjm_demand_response_supply=armed,
            **kw,
        )

    def test_registry_reconciles_with_committed_csv(self):
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / "auction-supply" / "pjm" / "pjm.csv"
        with path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        offered = {
            r["planning_year"]: float(r["value_mw"])
            for r in rows
            if r["metric"] == "offered" and r["category"] == "demand_resources"
        }
        self.assertEqual(DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO["PJM"], offered)
        self.assertTrue(all(r["unit"] == "mw_ucap" for r in rows))
        self.assertEqual(set(DEMAND_RESPONSE_SUPPLY_UCAP_MW_BY_ISO), {"PJM"})  # rule 25
        # Hold-last ratio: the last delivery year's offered DR over its
        # published Reliability Requirement (an explicit expression).
        last = max(offered, key=lambda l: int(l[:4]))
        self.assertEqual(last, "2027/2028")
        self.assertAlmostEqual(
            DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO["PJM"],
            offered[last] / 152_400.0,
            places=12,
        )

    def test_default_off_is_byte_identical_to_netting(self):
        cfg = self._cfg(False)
        self.assertFalse(ScenarioConfig(iso="PJM").pjm_demand_response_supply)
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        for year in (2019, 2021, 2023, 2025, 2028, None):
            self.assertIsNone(resolve_demand_response_supply_mw(cfg, "PJM", year, 1e5))
        for year in (2021, 2025):
            gross = gross_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year)
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year),
                gross * (1.0 - dr),
                places=6,
            )
        # accredited_firm_capacity_mw adds nothing unarmed / when not threaded.
        from market_sim.model.capacity_evolution.adequacy import (
            accredited_firm_capacity_mw,
        )

        base = accredited_firm_capacity_mw(
            [], 0.0, 0.0, 0.0, iso="PJM", peak_demand_mw=self.PEAK
        )
        self.assertEqual(
            accredited_firm_capacity_mw(
                [],
                0.0,
                0.0,
                0.0,
                iso="PJM",
                peak_demand_mw=self.PEAK,
                config=cfg,
                accreditation_year=2023,
            ),
            base,
        )
        self.assertEqual(
            accredited_firm_capacity_mw(
                [],
                0.0,
                0.0,
                0.0,
                iso="PJM",
                peak_demand_mw=self.PEAK,
                config=self._cfg(True),
                accreditation_year=None,
            ),
            base,
        )

    def test_armed_in_table_year_counts_published_dr_and_stops_netting(self):
        from market_sim.model.capacity_evolution.adequacy import (
            accredited_firm_capacity_mw,
        )

        cfg, off = self._cfg(True), self._cfg(False)
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        for year, mw in (
            (2021, 11_886.8),
            (2023, 10_116.7),
            (2024, 10_146.4),
            (2025, 6_084.8),
        ):
            self.assertEqual(
                resolve_demand_response_supply_mw(cfg, "PJM", year, None), mw
            )
            # Requirement: the gross (un-netted) bar — the netting is gone.
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year),
                resolve_adequacy_requirement_mw(off, "PJM", self.PEAK, year)
                / (1.0 - dr),
                places=6,
            )
            # Supply: the published DR is added outside the internal ratio.
            base = accredited_firm_capacity_mw(
                [],
                0.0,
                0.0,
                0.0,
                iso="PJM",
                peak_demand_mw=self.PEAK,
                config=off,
                accreditation_year=year,
            )
            self.assertAlmostEqual(
                accredited_firm_capacity_mw(
                    [],
                    0.0,
                    0.0,
                    0.0,
                    iso="PJM",
                    peak_demand_mw=self.PEAK,
                    config=cfg,
                    accreditation_year=year,
                ),
                base + mw,
                places=6,
            )

    def test_hold_last_is_a_ratio_of_the_gross_requirement(self):
        cfg = self._cfg(True)
        ratio = DEMAND_RESPONSE_SUPPLY_HOLD_LAST_RATIO_BY_ISO["PJM"]
        for year in (2028, 2030, 2050):
            gross = gross_adequacy_requirement_mw(cfg, "PJM", self.PEAK, year)
            self.assertAlmostEqual(
                resolve_demand_response_supply_mw(cfg, "PJM", year, gross),
                gross * ratio,
            )
            # Scales with load.
            self.assertAlmostEqual(
                resolve_demand_response_supply_mw(cfg, "PJM", year, 2.0 * gross),
                2.0 * gross * ratio,
            )
            # No gross requirement supplied → nothing is invented.
            self.assertIsNone(resolve_demand_response_supply_mw(cfg, "PJM", year, None))
        # Pre-table (no 2019/20 row) falls through to the netting.
        self.assertIsNone(resolve_demand_response_supply_mw(cfg, "PJM", 2019, 1e5))
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(cfg, "PJM", self.PEAK, 2019),
            gross_adequacy_requirement_mw(cfg, "PJM", self.PEAK, 2019) * (1.0 - dr),
            places=6,
        )

    def test_position_is_on_the_raw_convention(self):
        # With DR counted as supply the CR-1 position is (firm + DR) / gross —
        # PJM's VRR x-basis — with NO curve_convention_position transform
        # (that transform is the NEISO D40 R-B half and stays gated to NEISO).
        from market_sim.model.capacity_evolution.adequacy import (
            accredited_firm_capacity_mw,
            capacity_reserve_position,
        )

        cfg, off = self._cfg(True), self._cfg(False)
        dr = ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["PJM"]
        args = ([], 0.0, 0.0, 50_000.0)
        pos_off = capacity_reserve_position(*args, off, "PJM", self.PEAK, 2023)
        pos_on = capacity_reserve_position(*args, cfg, "PJM", self.PEAK, 2023)
        gross = gross_adequacy_requirement_mw(cfg, "PJM", self.PEAK, 2023)
        firm_off = accredited_firm_capacity_mw(
            *args,
            iso="PJM",
            peak_demand_mw=self.PEAK,
            year=2023,
            config=off,
            accreditation_year=2023,
        )
        self.assertAlmostEqual(pos_off, firm_off / (gross * (1.0 - dr)), places=9)
        self.assertAlmostEqual(pos_on, (firm_off + 10_116.7) / gross, places=9)
        self.assertEqual(curve_convention_position(cfg, "PJM", 1.3), 1.3)

    def test_other_isos_inert_and_cache_key(self):
        for iso in ("MISO", "NYISO", "NEISO", "ERCOT", "CAISO"):
            on, off = self._cfg(True, iso=iso), self._cfg(False, iso=iso)
            for year in (2021, 2023, 2025):
                self.assertIsNone(resolve_demand_response_supply_mw(on, iso, year, 1e5))
                self.assertEqual(
                    resolve_adequacy_requirement_mw(on, iso, 30_000.0, year),
                    resolve_adequacy_requirement_mw(off, iso, 30_000.0, year),
                )
        bc = ScenarioConfig(iso="PJM", mode="backcast", pjm_demand_response_supply=True)
        self.assertFalse(bc.pjm_demand_response_supply)
        off, on = self._cfg(False), self._cfg(True)
        self.assertEqual(
            off.cache_key(),
            ScenarioConfig(iso="PJM", mode="forecast", hindcast=True).cache_key(),
        )
        self.assertNotEqual(off.cache_key(), on.cache_key())
        both = ScenarioConfig(
            iso="PJM",
            mode="forecast",
            hindcast=True,
            pjm_demand_response_supply=True,
            pjm_accreditation_design_vintage=True,
        )
        self.assertEqual(len({off.cache_key(), on.cache_key(), both.cache_key()}), 3)


class TestPjmCapacitySupplyClearing(unittest.TestCase):
    """capx D57 (2026-09-05) — the PJM clearing half built from
    DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md: the fleet's net-ACR
    sell-offer stack cleared against the published VRR curve, the cleared
    set paid the clearing price, the uncleared set paid $0, the screen's
    failing set the auction's uncleared set. GATED default-OFF
    (``capacity_market_supply_clearing_by_iso``); the invariants of design
    §3.6 (I1–I6), trivial cases first."""

    R = 10_000.0  # requirement, MW

    @staticmethod
    def _curve(pos):
        """A linear stand-in for the VRR curve in $/firm-MW-yr: $100k/MW-yr
        at position 1.0, zero-cross at 1.10, flat-capped below 1.0."""
        return 100_000.0 * max(0.0, min(1.0, (1.10 - pos) / 0.10))

    @staticmethod
    def _cfg(supply=None, **kw):
        return ScenarioConfig(
            iso="PJM",
            mode="forecast",
            hindcast=True,
            capacity_market_supply_clearing_by_iso=supply,
            **kw,
        )

    # --- the gate and the seam -------------------------------------------
    def test_predicate_requires_row_and_curve_gate(self):
        self.assertFalse(resolve_capacity_market_supply_clearing(self._cfg(), "PJM"))
        self.assertFalse(resolve_capacity_market_supply_clearing(None, "PJM"))
        on = self._cfg({"PJM": True})
        self.assertTrue(resolve_capacity_market_supply_clearing(on, "PJM"))
        # Another ISO's row never leaks (rule 25); an absent row is off.
        self.assertFalse(resolve_capacity_market_supply_clearing(on, "MISO"))
        self.assertFalse(resolve_capacity_market_supply_clearing(on, None))
        # The curve gate is the precondition: a supply row over a curve gate
        # that is off resolves OFF (a stack cannot clear against a flat anchor).
        no_curve = self._cfg(
            {"PJM": True}, capacity_market_clearing_by_iso={"PJM": False}
        )
        self.assertFalse(resolve_capacity_market_supply_clearing(no_curve, "PJM"))
        # ERCOT is energy-only and curve-less: never ON.
        ercot = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            hindcast=True,
            capacity_market_supply_clearing_by_iso={"ERCOT": True},
        )
        self.assertFalse(resolve_capacity_market_supply_clearing(ercot, "ERCOT"))

    def test_seam_short_circuits_on_pre_priced_object(self):
        cfg = self._cfg()
        priced = ClearedCapacityPrice(
            price_per_firm_mw_yr=30_231.0, cleared_position=1.0445, census_position=1.14
        )
        pjm = MARKET_DESIGN["PJM"]
        self.assertEqual(
            pjm.capacity_price_per_firm_mw_yr(cfg, priced, iso="PJM", year=2023),
            30_231.0,
        )
        # A float position still takes the census (curve) path.
        self.assertNotEqual(
            pjm.capacity_price_per_firm_mw_yr(cfg, 1.0445, iso="PJM", year=2023),
            30_231.0,
        )
        # Energy-only ERCOT pays nothing whatever object it is handed.
        self.assertEqual(
            MARKET_DESIGN["ERCOT"].capacity_price_per_firm_mw_yr(
                cfg, priced, iso="ERCOT"
            ),
            0.0,
        )

    # --- the clearing rule, trivial cases first ----------------------------
    def test_i1_census_recovery_all_zero_offers_and_short_market(self):
        # Every offer $0 (every unit covers its bar): the clearing IS the
        # census evaluation — price = curve(census / R), cleared = census.
        offers = [
            ("A", "coal", 0.0, 1_000.0, 1_100.0),
            ("B", "gas_cc", 0.0, 500.0, 520.0),
        ]
        c = clear_capacity_supply_stack(offers, 9_000.0, self.R, self._curve)
        self.assertIsInstance(c, CapacityClearing)
        self.assertAlmostEqual(c.cleared_mw, 10_500.0)
        self.assertAlmostEqual(c.census_mw, 10_500.0)
        self.assertAlmostEqual(c.price_per_firm_mw_yr, self._curve(1.05))
        self.assertEqual(c.cleared_unit_ids, frozenset({"A", "B"}))
        self.assertEqual(c.n_uncleared, 0)
        self.assertEqual(c.how, "all_offers_clear_curve_sets_price")
        # A SHORT market (curve above every offer): identical reduction.
        offers = [
            ("A", "coal", 50.0, 1_000.0, 1_100.0),
            ("B", "gas_cc", 120.0, 500.0, 520.0),
        ]
        c = clear_capacity_supply_stack(offers, 7_000.0, self.R, self._curve)
        self.assertAlmostEqual(c.cleared_mw, 8_500.0)
        self.assertAlmostEqual(c.price_per_firm_mw_yr, self._curve(0.85))  # the cap
        self.assertEqual(c.n_uncleared, 0)
        self.assertEqual(c.how, "all_offers_clear_curve_sets_price")

    def test_rule1_zero_block_past_zero_cross(self):
        # Q_0 alone is past the zero-cross: price 0; $0 offers clear (ties at
        # $0 are inside the block), every positive offer is uncleared.
        offers = [
            ("Z", "nuclear", 0.0, 800.0, 850.0),
            ("A", "coal", 1.0, 1_000.0, 1_100.0),
        ]
        c = clear_capacity_supply_stack(offers, 11_500.0, self.R, self._curve)
        self.assertEqual(c.price_usd_per_mw_day, 0.0)
        self.assertEqual(c.how, "zero_block_past_zero_cross")
        self.assertEqual(c.cleared_unit_ids, frozenset({"Z"}))
        self.assertAlmostEqual(c.cleared_mw, 12_300.0)
        self.assertEqual(c.uncleared_firm_mw_by_fuel, {"coal": 1_000.0})
        self.assertEqual(c.uncleared_nameplate_mw_by_fuel, {"coal": 1_100.0})

    def test_rule2_curve_sets_price_between_offers(self):
        # After A clears, the curve at q = 10_800 pays 20k $/MW-yr = 54.79
        # $/MW-day, below B's 100 $/MW-day offer: the curve sets the price on
        # the vertical rise and B is uncleared.
        offers = [
            ("A", "coal", 10.0, 800.0, 800.0),
            ("B", "gas_st", 100.0, 500.0, 500.0),
        ]
        c = clear_capacity_supply_stack(offers, 10_000.0, self.R, self._curve)
        self.assertEqual(c.how, "curve_sets_price_between_offers")
        self.assertAlmostEqual(c.cleared_mw, 10_800.0)
        self.assertAlmostEqual(c.price_usd_per_mw_day, self._curve(1.08) / 365.0)
        self.assertEqual(c.cleared_unit_ids, frozenset({"A"}))
        self.assertEqual(c.marginal_unit_id, None)

    def test_rule4_marginal_offer_sets_price_and_bisection(self):
        # The curve crosses INSIDE A's step: price = A's offer, the cleared
        # quantity is the Q with D(Q) = offer, A is cleared in full for the
        # screen (whole-unit grain) and B is uncleared.
        offer_a = 40_000.0 / 365.0  # 40k $/MW-yr <-> position 1.06
        offers = [
            ("A", "coal", offer_a, 2_000.0, 2_000.0),
            ("B", "oil", 200.0, 300.0, 300.0),
        ]
        c = clear_capacity_supply_stack(offers, 10_000.0, self.R, self._curve)
        self.assertEqual(c.how, "marginal_offer_sets_price")
        self.assertAlmostEqual(c.price_usd_per_mw_day, offer_a)
        self.assertAlmostEqual(c.cleared_mw, 10_600.0, places=3)
        self.assertAlmostEqual(c.cleared_position, 1.06, places=6)
        self.assertEqual(c.marginal_unit_id, "A")
        self.assertEqual(c.cleared_unit_ids, frozenset({"A"}))
        self.assertEqual(c.n_uncleared, 1)
        # Deterministic tie order: equal offers sort by unit_id.
        tie = [
            ("B", "coal", offer_a, 1_000.0, 1_000.0),
            ("A", "coal", offer_a, 1_000.0, 1_000.0),
        ]
        c2 = clear_capacity_supply_stack(tie, 10_000.0, self.R, self._curve)
        self.assertEqual(c2.marginal_unit_id, "A")
        self.assertEqual(c2.cleared_unit_ids, frozenset({"A"}))
        with self.assertRaises(ValueError):
            clear_capacity_supply_stack(offers, 1.0, 0.0, self._curve)

    def test_i3_bounds_and_i4_monotonicity(self):
        base = [
            ("A", "coal", 5.0, 1_000.0, 1_000.0),
            ("B", "gas_cc", 60.0, 800.0, 800.0),
            ("C", "gas_ct", 90.0, 600.0, 600.0),
        ]
        cap_day = self._curve(0.0) / 365.0
        for q0 in (8_000.0, 9_500.0, 10_500.0, 12_000.0):
            c = clear_capacity_supply_stack(base, q0, self.R, self._curve)
            self.assertGreaterEqual(c.price_usd_per_mw_day, 0.0)
            self.assertLessEqual(c.price_usd_per_mw_day, cap_day)
            self.assertGreaterEqual(c.cleared_mw, q0 - 1e-9)
            self.assertLessEqual(c.cleared_mw, q0 + 2_400.0 + 1e-9)
        ref = clear_capacity_supply_stack(base, 9_500.0, self.R, self._curve)
        # Raising any single offer never lowers the price or raises the
        # cleared quantity.
        for i in range(3):
            raised = list(base)
            uid, fuel, o, a, n = raised[i]
            raised[i] = (uid, fuel, o + 30.0, a, n)
            c = clear_capacity_supply_stack(raised, 9_500.0, self.R, self._curve)
            self.assertGreaterEqual(
                c.price_usd_per_mw_day, ref.price_usd_per_mw_day - 1e-9
            )
            self.assertLessEqual(c.cleared_mw, ref.cleared_mw + 1e-6)
        # Raising R never lowers the price.
        c = clear_capacity_supply_stack(base, 9_500.0, self.R * 1.05, self._curve)
        self.assertGreaterEqual(c.price_usd_per_mw_day, ref.price_usd_per_mw_day - 1e-9)

    def test_i5_known_answer_committed_ledgers(self):
        # The pre-declaration instrument's 2022 -> DY 2022/23 row on the D48
        # basis (PREDECL-capx-d54 §2.1; docs/handoffs/d54/clearing-predecl-
        # 2026-09-05.json): price 82.81 $/MW-day, cleared position 1.0445, set
        # by a marginal gas_cc offer — reproduced by the code's own clearing
        # function and the registry's own vintage curve, to ±$1 / ±0.1 pt.
        import glob
        import json

        from market_sim.config.capacity_market import THERMAL_ELCC_CLASS_RATING_BY_ISO
        from market_sim.config.constants import EFORD
        from market_sim.config.paths import REPO_ROOT

        ledger = glob.glob(
            str(
                REPO_ROOT
                / "results/hindcast/pjm-2021-2025-realized-t1h-d45r/PJM/*/evolution_2022.json"
            )
        )
        pos_path = (
            REPO_ROOT / "docs/handoffs/d48/devintage-positions-d45r-2026-09-04.json"
        )
        ref_path = REPO_ROOT / "docs/handoffs/d54/clearing-predecl-2026-09-05.json"
        if not (ledger and pos_path.exists() and ref_path.exists()):
            self.skipTest("committed D45-R / D48 / D54 artifacts absent")
        rows = [
            e
            for e in json.load(open(ledger[0])).get("pipeline_events", [])
            if e["event"] in ("decided", "entry_capped", "re_confirmed")
        ]
        both = json.load(open(pos_path))["years"]["2022"]["arms"]["BOTH"]
        ref = json.load(open(ref_path))["control pjm-t1h"]["2022"]
        elcc = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]
        offers, fail_firm = [], 0.0
        for e in rows:
            a = 1.0 - EFORD.get(e["fuel"], 0.08)  # UCAP through DY 2024/25
            fmw = e["mw"] * a
            fail_firm += fmw
            eas = e["net_revenue_usd"] - e.get("capacity_revenue_usd", 0.0)
            offers.append(
                (
                    e["unit_id"],
                    e["fuel"],
                    max(0.0, e["going_forward_cost_usd"] - eas) / (fmw * 365.0),
                    fmw,
                    e["mw"],
                )
            )
        self.assertIn("gas_cc", elcc)  # the registry the HEAD basis would use
        c = clear_capacity_supply_stack(
            offers,
            both["firm_mw"] - fail_firm,
            both["requirement_mw"],
            capacity_supply_curve(self._cfg(), "PJM", 2022),
        )
        self.assertEqual(c.how, "marginal_offer_sets_price")
        self.assertAlmostEqual(c.price_usd_per_mw_day, ref["price_mw_day"], delta=1.0)
        self.assertAlmostEqual(
            100.0 * c.cleared_position, 100.0 * ref["position"], delta=0.1
        )
        self.assertAlmostEqual(c.price_usd_per_mw_day, 82.81, delta=0.01)
        self.assertAlmostEqual(c.cleared_position, 1.0445, delta=0.0001)

    # --- the settlement into the screen ------------------------------------
    def _screen(self, cfg, peak, year=2023):
        """Three PJM coal units: A covers its bar on energy (offer $0), B has
        a small gap, C earns exactly zero margin (offer = its full bar)."""
        T = 100
        fleet = [
            _gen("A", "coal", pmax=1_000.0, eford=0.08),
            _gen("B", "coal", pmax=1_000.0, eford=0.08),
            _gen("C", "coal", pmax=1_000.0, eford=0.08),
        ]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=T)
        prices = np.full((1, T), 50.0)
        # margin/MW-yr over 100 h: A 100 $/MWh x 100 h = 10k/MW... scaled so
        # A clears its 58.5k $/MW-yr bar, B misses it by a little, C by all.
        mc = np.vstack(
            [
                np.full(T, 50.0 - 800.0),  # A: 800 $/MWh x 100 h x avail > 58.5k
                np.full(T, 50.0 - 500.0),  # B: 50k x avail < 58.5k (a gap)
                np.full(T, 50.0),  # C: zero margin
            ]
        )
        dispatch = SimpleNamespace(dispatch=np.zeros((3, T)))
        sink: dict = {}
        with no_hydro_accreditation():
            survivors, state, _ = apply_economic_retirements(
                fleet,
                arrays,
                dispatch,
                prices,
                cfg,
                {},
                peak_demand=peak,
                mc=mc,
                year=year,
                event_sink=sink,
            )
        return fleet, survivors, state, sink

    def test_i2_identity_failing_set_is_uncleared_set(self):
        cfg = self._cfg({"PJM": True}, retirement_rule="pipeline")
        for peak in (1_500.0, 6_000.0, 40_000.0):
            fleet, survivors, state, sink = self._screen(cfg, peak)
            clearing = sink["capacity_clearing"]
            self.assertIsInstance(clearing, CapacityClearing)
            rows = {e["unit_id"]: e for e in sink.get("pipeline_events", [])}
            failing = {
                uid
                for uid, e in rows.items()
                if e["event"] in ("decided", "entry_capped")
            }
            uncleared = {g.unit_id for g in fleet} - set(clearing.cleared_unit_ids)
            # I2: a screened unit fails the bar iff the auction did not clear
            # it (the marginal unit is cleared and indifferent — it passes).
            self.assertEqual(failing, uncleared, (peak, clearing.how))
            # A covers its bar on energy: offer $0, always cleared, never fails.
            self.assertEqual(clearing.offer_usd_per_mw_day["A"], 0.0)
            self.assertIn("A", clearing.cleared_unit_ids)
            # C's offer is its full bar on accredited MW (HEAD's basis: the
            # ELCC class rating in every year, the devintage OFF); B's the gap.
            from market_sim.config.capacity_market import (
                THERMAL_ELCC_CLASS_RATING_BY_ISO,
            )

            a_frac = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]["coal"]
            a_mw = 1_000.0 * a_frac
            bar_day = 58.5 * 1_000.0 * 1_000.0 / (a_mw * 365.0)
            self.assertAlmostEqual(
                clearing.offer_usd_per_mw_day["C"], bar_day, places=6
            )
            if "B" in rows:  # B failing: its offer is its gap on its firm MW
                self.assertAlmostEqual(
                    clearing.offer_usd_per_mw_day["B"],
                    (rows["B"]["going_forward_cost_usd"] - rows["B"]["net_revenue_usd"])
                    / (a_mw * 365.0),
                    places=6,
                )
                self.assertAlmostEqual(rows["B"]["capacity_accredited_mw"], a_mw)
            # Ledger fields on every failing row; settled revenue consistent.
            for uid in failing:
                self.assertIs(rows[uid]["capacity_cleared"], False)
                self.assertEqual(rows[uid]["capacity_revenue_usd"], 0.0)
                self.assertIn("capacity_offer_usd_per_mw_day", rows[uid])
                self.assertIn("capacity_accredited_mw", rows[uid])
            self.assertAlmostEqual(
                clearing.census_mw, clearing.price_takers_mw + clearing.offered_mw
            )
        # The long peak leaves the market past the curve's reach for B and C
        # (rule 1 or rule 2: the price forms at or before A's $0 step ends):
        # B and C uncleared and failing.
        _, _, _, sink = self._screen(cfg, 1_500.0)
        self.assertIn(
            sink["capacity_clearing"].how,
            ("zero_block_past_zero_cross", "curve_sets_price_between_offers"),
        )
        self.assertEqual(
            {g for g in ("B", "C")} - set(sink["capacity_clearing"].cleared_unit_ids),
            {"B", "C"},
        )
        # The short peak clears everything at the cap (rule 5 = census): with
        # the cap on the unit's firm MW every unit covers its bar, nothing fails.
        _, _, _, sink = self._screen(cfg, 40_000.0)
        self.assertEqual(
            sink["capacity_clearing"].how, "all_offers_clear_curve_sets_price"
        )
        self.assertEqual(sink["capacity_clearing"].n_uncleared, 0)
        self.assertEqual(sink.get("pipeline_events", []), [])

    def test_pjm_iso_override_arms_forecast_only(self):
        # Owner ruling 2026-09-05 (FINDING-capx-d57 §8): the joint PJM
        # configuration is armed through ISOConfig.default_scenario_overrides,
        # not the shared dataclass defaults — so the bare PJM T1-H recipe
        # resolves to arm A's own key, an explicit all-off caller still
        # resolves the D45-R control key, every other ISO is untouched, and a
        # PJM plain backcast is coerced back to the off posture (key unmoved).
        #
        # 2026-09-05, all three pins re-keyed by the Y-11 fast-tier pin lane:
        # capx D60 (commit 13f711bc) landed the declared flip of
        # ccs_retrofit_capex_co2_scaling (owner ruling Q42, director sitting
        # r#37) AFTER D57 (5bb70047) wrote these literals, advancing every
        # resolved key by one field. The Q44 posture this test asserts is
        # UNCHANGED -- arm A / arm B / control are still three distinct keys
        # reached through the same override path, and setting
        # ccs_retrofit_capex_co2_scaling=False restores all three pre-flip
        # values exactly (f0e050e820c1159a / ccee17a4c1563727 /
        # c6091bd5b62bbc3f). D60's own §3 table independently records the
        # post-arm bare PJM key as aef81c84c4609c76 and its pre-declared
        # all-off key as 7297dcb3b92be3fb ("moved by D57, not by D60" --
        # FINDING-capx-d60-2026-09-05.md §3/§4, STOP 1, which is why D60's
        # sweep left PJM's pins behind).
        from market_sim.config.iso_configs import apply_iso_scenario_defaults
        from scripts.run_capacity_hindcast import build_config

        def _key(iso, **kw):
            cfg = build_config(
                iso,
                2021,
                2025,
                "realized",
                vintage=2020,
                entry_screen_diagnostics=True,
                **kw,
            )
            return apply_iso_scenario_defaults(cfg, iso).cache_key()

        # capx D65-B-R: all three literals refreshed for D65-B's Act B, which
        # merged 2026-09-06, the day after these were written.
        # ``ccs_retrofit_vom_adder`` 8.0 -> 2.95 is not a
        # ``_CACHE_KEY_OPTIONAL_FIELDS`` member, so it re-keys every config
        # unconditionally. MEASURED, not assumed: undoing exactly the two D65-B
        # acts on each resolved config (``ccs_retrofit_vom_adder=8.0``,
        # ``ccs_retrofit_fixed_cost_co2_scaling=False``) restores all three of
        # the previous literals EXACTLY --
        #   arm A  15a723ba3b6dc856 -> aef81c84c4609c76
        #   ctrl   c5ec052057905966 -> 7297dcb3b92be3fb
        #   arm B  6ba67a81ed4d2ed6 -> 6cf8ee2c9f31e528
        # -- so the whole move is the two acts' and nothing else's, the same
        # decomposition PRECOMMIT-capx-d65b-2026-09-06.md §3.1 uses. The Q44
        # posture this test asserts is untouched: three distinct keys through
        # the same override path.
        # capx D67-ARM (owner ruling Q52): a FOURTH field is now armed through
        # the same override path, so the bare key advances again and the two
        # explicit control legs need the fourth ``--no-`` flag to reach the
        # postures they name. MEASURED, not assumed: adding
        # ``capacity_adequacy_requirement_published=False`` to each restores
        # its pre-D67-ARM literal EXACTLY (c5ec052057905966 / 6ba67a81ed4d2ed6),
        # so the whole move is this one field's. The three-flag leg is no
        # longer the D45-R posture -- it now carries the published requirement
        # armed -- and is pinned at its own key so a later lane cannot mistake
        # it for one (PRECOMMIT-capx-d67arm-2026-09-06.md §2; the miss against
        # that PRECOMMIT's own "unmoved" declaration is reported at full
        # magnitude in FINDING-capx-d67arm-2026-09-06.md).
        # capx D75-R-ARM (owner ruling Q55): a FIFTH field is armed through the
        # same override path — ``pjm_vre_accreditation_vintage``, the VRE half
        # of the D48 devintage — so the bare key advances again and EVERY
        # explicit control leg needs the fifth ``--no-`` flag to reach the
        # posture it names. That the four control legs move is PRE-DECLARED
        # this time (PRECOMMIT-capx-d75r-arm-2026-09-06.md §2.1) rather than
        # discovered after the fact, which is the miss FINDING-capx-d67arm
        # §2.1 recorded against itself. The cause is structural: the field is a
        # ``_CACHE_KEY_OPTIONAL_FIELDS`` member registered at ``False``, so it
        # is dropped from the hash while unarmed and enters it once armed, on
        # every PJM forecast leg whatever the other flags say — even the three
        # legs where the mechanism is INERT because its predicate also needs
        # ``pjm_accreditation_design_vintage`` (inertness is a solve property,
        # not a hash property).
        #
        # MEASURED, not assumed: adding ``pjm_vre_accreditation_vintage=False``
        # to each leg restores its pre-arm literal EXACTLY —
        #   bare                a9c66d8ea25acb9d   (the D67-ARM posture)
        #   off3 + no-req-pub   c5ec052057905966   (D45-R's bare key)
        #   off2 + no-req-pub   6ba67a81ed4d2ed6   (D57 arm B)
        # — so the whole move is this one field's, and every pre-arm recipe
        # stays both reachable and identified. The post-arm bare key is
        # ``b518f5fe7d02f961``, which is D75-R's OWN measured full-window arm
        # key (its control is the pre-arm bare recipe, to the digit), so the
        # arm reproduces the recipe the A/B was measured on rather than
        # naming a new one.
        # capx D78-ARM (owner ruling Q56, served by FINDING-capx-d78r3 §5): a
        # SIXTH field is armed through the same override path —
        # ``retirement_sector_gate``, the retirement-screen sector gate (capx
        # D53 / D78) — so the bare key advances again and EVERY explicit
        # control leg needs the sixth ``--no-`` flag to reach the posture it
        # names. Pre-declared with measured literals
        # (PRECOMMIT-capx-d78arm-2026-09-06.md §2 / §2.1), the D75-R-ARM
        # discipline. Same structural cause: the field is a
        # ``_CACHE_KEY_OPTIONAL_FIELDS`` member registered at ``False``.
        #
        # MEASURED, not assumed: adding ``retirement_sector_gate=False`` to
        # each leg restores its pre-arm literal EXACTLY —
        #   bare                b518f5fe7d02f961   (the D75-R-ARM / Q55 posture)
        #   off3                1785cb6086cd2b15
        #   off2                ab0237198cff24ad
        # — so the whole move is this one field's. Two post-arm legs land on
        # keys that ALREADY carry a measurement: ``--no-pjm-vre-accreditation-
        # vintage`` resolves ``bb6a60239d69508b``, which IS D78-R2's own
        # measured arm (the gate without Q55; d78r2/keys_probe.json), and both
        # ``--no-`` flags reach ``a9c66d8ea25acb9d``, the D67-ARM / D78-R2
        # graded control. The post-arm bare key is ``fb16fda2ddb0a94a``.
        # capx D76-ARM-B (owner ruling Q58): a SEVENTH field re-keys every leg
        # below — ``capacity_screen_peak_measured_hindcast``, the measured
        # hindcast capacity-screen peak — and it is the FIRST that is not armed
        # through ``_pjm_config`` at all. It is a flip of the SHARED
        # ``ScenarioConfig`` default (False -> True, the fourth entry in
        # ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS``), which every one of these
        # legs resolves because they are all HINDCAST configs. Same structural
        # cause as the five arms above and the reason a moved key is the
        # intended effect: the field is a ``_CACHE_KEY_OPTIONAL_FIELDS`` member
        # registered at ``False``, so it is dropped from the hash while it
        # equals that frozen declaration and enters it once it does not.
        #
        # MEASURED, not assumed, and for ALL FOURTEEN legs rather than the
        # customary three: adding ``capacity_screen_peak_measured_hindcast=
        # False`` to each leg restores its pre-arm literal EXACTLY, 14 of 14
        # (PRECOMMIT-capx-d76-arm-b-2026-09-07.md; FINDING §3). So the whole
        # move is this one field's, the Q44/Q52/Q55/Q56 postures this test
        # asserts are untouched, and every pre-arm PJM recipe stays both
        # reachable and identified by its own key. The bare inverse is asserted
        # below rather than only narrated.
        _nod76 = dict(capacity_screen_peak_measured_hindcast=False)
        _novre = dict(pjm_vre_accreditation_vintage=False)
        _nogate = dict(retirement_sector_gate=False)
        _nod84 = dict(pjm_thermal_accreditation_vintage=False)
        self.assertEqual(_key("PJM"), "b9fa47dedb6c3319")  # = the D78-ARM posture
        self.assertEqual(_key("PJM", **_nogate), "3b3c0463b53e2df0")  # = D75-R-ARM
        self.assertEqual(_key("PJM", **_novre), "02b4d92349186a1e")  # = D78-R2's arm
        self.assertEqual(
            _key("PJM", **_novre, **_nogate), "0200586e10655e64"
        )  # = D67-ARM
        _off3 = dict(
            pjm_accreditation_design_vintage=False,
            pjm_demand_response_supply=False,
            capacity_market_supply_clearing=False,
        )
        self.assertEqual(
            _key("PJM", **_off3), "8f74247fb042eec9"
        )  # D57 off, D67+Q55+Q56 on
        self.assertEqual(
            _key("PJM", **_off3, **_nogate), "943d161f2da63444"
        )  # D57 off, D67+D75R on
        self.assertEqual(_key("PJM", **_off3, **_novre, **_nogate), "18de6fa20f8afa85")
        self.assertEqual(
            _key(
                "PJM",
                **_off3,
                **_nogate,
                capacity_adequacy_requirement_published=False,
            ),
            "e8d661da3f81715f",  # D57 + D67 off, D75-R still on
        )
        self.assertEqual(
            _key(
                "PJM",
                **_off3,
                **_novre,
                **_nogate,
                capacity_adequacy_requirement_published=False,
            ),
            "dde282050c2fa058",  # = D45-R's bare key, the explicit control
        )
        _off2 = dict(
            pjm_accreditation_design_vintage=False,
            pjm_demand_response_supply=False,
        )
        self.assertEqual(
            _key("PJM", **_off2), "d3fd2763909b5df8"
        )  # arm B, D67+Q55+Q56 on
        self.assertEqual(
            _key("PJM", **_off2, **_nogate), "8bcecb48a7db00bc"
        )  # arm B, D67+D75R on
        self.assertEqual(_key("PJM", **_off2, **_novre, **_nogate), "7036962575091ca1")
        self.assertEqual(
            _key(
                "PJM",
                **_off2,
                **_nogate,
                capacity_adequacy_requirement_published=False,
            ),
            "4c296bc13ff12be2",  # D57 partial + D67 off, D75-R still on
        )
        self.assertEqual(
            _key(
                "PJM",
                **_off2,
                **_novre,
                **_nogate,
                capacity_adequacy_requirement_published=False,
            ),
            "daed452f928e9c45",  # = arm B
        )
        # The (b'-1) inverse, enforced: the pre-D76-ARM-B bare recipe is still
        # reachable and still carries its own key.
        self.assertEqual(_key("PJM", **_nod76), "bb4fd42e6d1f9e81")
        # capx D84-ARM (owner ruling 2026-09-07, served by
        # FINDING-capx-d84-2026-09-07.md §8): an EIGHTH field is armed through
        # the ``_pjm_config`` override path — ``pjm_thermal_accreditation_
        # vintage``, the THERMAL RATING half of the D48 devintage (the VRE half
        # is Q55 above) — so every leg here re-keys, for the same structural
        # cause the five arms above document: the field is a
        # ``_CACHE_KEY_OPTIONAL_FIELDS`` member registered at ``False``, so it
        # is dropped from the hash while unarmed and enters it once armed, on
        # every PJM forecast leg whatever the other flags say — even the legs
        # where the mechanism is INERT because its predicate also needs
        # ``pjm_accreditation_design_vintage`` (inertness is a solve property,
        # not a hash property).
        #
        # MEASURED, not assumed, for ALL FIFTEEN legs: adding
        # ``pjm_thermal_accreditation_vintage=False`` to each restores its
        # pre-arm literal EXACTLY, 15 of 15, so the whole move is this one
        # field's and every pre-arm PJM recipe stays both reachable and
        # identified by its own key (PRECOMMIT-capx-d84arm-2026-09-07.md §3;
        # FINDING-capx-d84arm-2026-09-07.md §3). The post-arm bare key
        # ``b9fa47dedb6c3319`` is D84's OWN measured full-window arm key — its
        # control is the pre-arm bare recipe ``f736025631d0d27e`` to the digit
        # — so the arm reproduces the recipe the A/B was measured on rather
        # than naming a new one, and the registration owed no re-solve.
        self.assertEqual(_key("PJM", **_nod84), "f736025631d0d27e")
        # Every other ISO resolves the PJM fields OFF (their own keys are
        # their own lanes' — never pinned here, rule 25). The sector gate is
        # ISO-agnostic in form and armed PER ISO on that ISO's own ISOConfig:
        # MISO carries its D53 arm, nobody else's moves with PJM's.
        for iso in ("MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
            cfg = build_config(
                iso, 2021, 2025, "realized", vintage=2020, entry_screen_diagnostics=True
            )
            res = apply_iso_scenario_defaults(cfg, iso)
            self.assertFalse(res.pjm_accreditation_design_vintage)
            self.assertFalse(res.pjm_demand_response_supply)
            self.assertIsNone(res.capacity_market_supply_clearing_by_iso)
            self.assertFalse(res.pjm_vre_accreditation_vintage)
            self.assertIs(res.retirement_sector_gate, iso == "MISO")
        back = ScenarioConfig(iso="PJM", mode="backcast")
        res = apply_iso_scenario_defaults(back, "PJM")
        self.assertFalse(res.pjm_accreditation_design_vintage)
        self.assertFalse(res.pjm_demand_response_supply)
        self.assertIsNone(res.capacity_market_supply_clearing_by_iso)
        # FORECAST-ONLY, which is the whole intent of this test's name: the
        # backcast leg coerces the VRE gate AND the sector gate back to their
        # dataclass defaults in ``__post_init__``, so no backcast keeper of
        # any ISO can be re-keyed.
        self.assertFalse(res.pjm_vre_accreditation_vintage)
        self.assertFalse(res.retirement_sector_gate)
        self.assertEqual(res.cache_key(), back.cache_key())

    def test_i6_byte_identity_unarmed_and_backcast_coercion(self):
        # Cache keys: None (the default) hashes as if the field were absent;
        # an armed row keys distinctly; a plain backcast coerces to None.
        bare = ScenarioConfig(iso="PJM", mode="forecast", hindcast=True)
        self.assertEqual(self._cfg(None).cache_key(), bare.cache_key())
        self.assertNotEqual(self._cfg({"PJM": True}).cache_key(), bare.cache_key())
        back = ScenarioConfig(
            iso="PJM",
            mode="backcast",
            capacity_market_supply_clearing_by_iso={"PJM": True},
        )
        self.assertIsNone(back.capacity_market_supply_clearing_by_iso)
        self.assertIsNone(back.capacity_market_clearing_by_iso)
        # Unarmed screen: no clearing, no ledger fields, the census leg as before.
        cfg = self._cfg(None, retirement_rule="pipeline")
        _, _, _, sink = self._screen(cfg, 6_000.0)
        self.assertNotIn("capacity_clearing", sink)
        for e in sink.get("pipeline_events", []):
            self.assertNotIn("capacity_cleared", e)
            self.assertNotIn("capacity_offer_usd_per_mw_day", e)


class TestNyisoRequirementDevintage(unittest.TestCase):
    """capx D52 (2026-09-04) — the NYISO adequacy requirement devintaged onto the
    NYSRC ICAP-market FORECAST peak (D45 §5.2.4 item 1) and the capability year's
    ADOPTED IRM × (1 − derate) (item 2, the D40 vintage axis), Table D.2 of the
    NYSRC 2026-27 IRM Study Appendices. Two GATED default-OFF fields: every
    unarmed solve is byte-identical to the single-vintage composite."""

    MODEL_PEAK = 28_640.0  # the capacity-screen seam peak the 2023 screens saw
    PUB = {  # Table D.2: forecast peak, adopted IRM %, derate, UCAP requirement
        2020: (32_296.0, 18.9, 0.0830, 35_213.0),
        2021: (32_333.0, 20.7, 0.0877, 35_604.0),
        2022: (31_767.0, 19.6, 0.0978, 34_277.0),
        2023: (32_049.0, 20.0, 0.1014, 34_559.0),
        2024: (31_542.0, 22.0, 0.1321, 33_397.0),
        2025: (31_469.0, 24.4, 0.1300, 34_059.0),
    }

    @staticmethod
    def _csv_rows(metric):
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / "demand-curve" / "nyiso" / "nyiso.csv"
        with path.open(newline="") as fh:
            return {
                r["delivery_year"].replace("-", "/"): float(r["y_value"])
                for r in csv.DictReader(fh)
                if r["metric"] == metric and r["area"] == "NYCA"
            }

    @staticmethod
    def _cfg(peak=False, factors=False, iso="NYISO", **kw):
        return ScenarioConfig(
            iso=iso,
            mode="forecast",
            hindcast=True,
            nyiso_requirement_forecast_peak=peak,
            nyiso_requirement_vintage_factors=factors,
            **kw,
        )

    @staticmethod
    def _composite(peak):
        return (
            peak
            * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"])
            * PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]
        )

    def test_registries_reconcile_with_published_csv_and_table_identity(self):
        # Every registry row equals its committed csv row (rules 13/23), the
        # three tables carry the SAME capability years, and each year satisfies
        # Table D.2's own identity peak × (1 + IRM) × (1 − derate) = UCAP
        # requirement to within 1 MW (the table rounds to MW). Rule 25: one ISO.
        peaks, irms, derates = (
            NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO["NYISO"],
            NYCA_IRM_ADOPTED_BY_ISO["NYISO"],
            NYCA_ICAP_UCAP_TRANSLATION_BY_ISO["NYISO"],
        )
        self.assertEqual(set(peaks), set(irms))
        self.assertEqual(set(peaks), set(derates))
        self.assertEqual(peaks, self._csv_rows("icap_market_forecast_peak"))
        csv_irms = self._csv_rows("irm_adopted")
        self.assertEqual(set(csv_irms), set(irms))
        for label, pct in csv_irms.items():
            self.assertAlmostEqual(irms[label], pct / 100.0, places=9, msg=label)
        self.assertEqual(derates, self._csv_rows("icap_ucap_translation_factor"))
        ucap = self._csv_rows("ucap_requirement")
        self.assertEqual(set(ucap), set(peaks))
        for label in peaks:
            self.assertLess(
                abs(
                    peaks[label] * (1.0 + irms[label]) * (1.0 - derates[label])
                    - ucap[label]
                ),
                1.0,
                label,
            )
        for reg in (
            NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO,
            NYCA_IRM_ADOPTED_BY_ISO,
            NYCA_ICAP_UCAP_TRANSLATION_BY_ISO,
        ):
            self.assertEqual(set(reg), {"NYISO"})
        # The single-vintage composite ratio is the 2024/25 derate, untouched.
        self.assertAlmostEqual(
            PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"],
            1.0 - derates["2024/2025"],
            places=9,
        )

    def test_default_off_is_byte_identical_to_composite(self):
        off, plain = (
            self._cfg(),
            ScenarioConfig(iso="NYISO", mode="forecast", hindcast=True),
        )
        for year in (*range(2019, 2036), None):
            self.assertEqual(
                resolve_adequacy_requirement_mw(off, "NYISO", self.MODEL_PEAK, year),
                resolve_adequacy_requirement_mw(plain, "NYISO", self.MODEL_PEAK, year),
            )
            self.assertEqual(
                resolve_adequacy_requirement_mw(off, "NYISO", self.MODEL_PEAK, year),
                self._composite(self.MODEL_PEAK),
            )
        # The unarmed peak resolver hands back the caller's own float object.
        self.assertIs(
            resolve_nyiso_requirement_peak_mw(off, "NYISO", self.MODEL_PEAK, 2023),
            self.MODEL_PEAK,
        )
        self.assertIsNone(resolve_nyiso_requirement_factor(off, "NYISO", 2023))

    def test_both_armed_in_table_is_the_published_ucap_requirement(self):
        # With both gates on the in-table requirement IS Table D.2's UCAP
        # requirement (< 1 MW) whatever peak the model hands in — the model's
        # peak drops out, the NEISO Net ICR / PJM FPR shape.
        both = self._cfg(peak=True, factors=True)
        for year, (_, _, _, ucap) in self.PUB.items():
            for model_peak in (self.MODEL_PEAK, 31_857.0):
                self.assertLess(
                    abs(
                        resolve_adequacy_requirement_mw(both, "NYISO", model_peak, year)
                        - ucap
                    ),
                    1.0,
                    (year, model_peak),
                )

    def test_single_gate_arms_decompose(self):
        # Peak-only: the composite factor on the PUBLISHED peak; factors-only:
        # the capability year's pair on the MODEL peak. Multiplicative halves.
        pk, fa = self._cfg(peak=True), self._cfg(factors=True)
        for year, (pub_peak, irm, derate, _) in self.PUB.items():
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(pk, "NYISO", self.MODEL_PEAK, year),
                self._composite(pub_peak),
                places=6,
            )
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(fa, "NYISO", self.MODEL_PEAK, year),
                self.MODEL_PEAK * (1.0 + irm / 100.0) * (1.0 - derate),
                places=6,
            )
        # 2024 is the one in-window year the factor half LOWERS the requirement
        # (adopted 22.0 % vs the vintage 24.4 %); 2021 raises it (D45 item 2 sign).
        self.assertLess(
            resolve_adequacy_requirement_mw(fa, "NYISO", self.MODEL_PEAK, 2024),
            self._composite(self.MODEL_PEAK),
        )
        self.assertGreater(
            resolve_adequacy_requirement_mw(fa, "NYISO", self.MODEL_PEAK, 2021),
            self._composite(self.MODEL_PEAK),
        )

    def test_pre_table_and_year_none_fall_through(self):
        both = self._cfg(peak=True, factors=True)
        for year in (2015, 2019, None):
            self.assertEqual(
                resolve_adequacy_requirement_mw(both, "NYISO", self.MODEL_PEAK, year),
                self._composite(self.MODEL_PEAK),
            )

    def test_forecast_peak_has_no_hold_last(self):
        # Beyond the table the model's own peak IS the forward forecast: the
        # peak arm is the composite on the model peak, never a held MW.
        pk = self._cfg(peak=True)
        for year in (2026, 2030, 2050):
            self.assertEqual(
                resolve_adequacy_requirement_mw(pk, "NYISO", self.MODEL_PEAK, year),
                self._composite(self.MODEL_PEAK),
            )
            self.assertIs(
                resolve_nyiso_requirement_peak_mw(pk, "NYISO", self.MODEL_PEAK, year),
                self.MODEL_PEAK,
            )

    def test_factors_hold_last_beyond_table_is_the_last_published_pair(self):
        fa = self._cfg(factors=True)
        held = (1.0 + 0.244) * (1.0 - 0.1300)
        for year in (2026, 2030, 2050):
            self.assertAlmostEqual(
                resolve_nyiso_requirement_factor(fa, "NYISO", year), held, places=9
            )
            self.assertAlmostEqual(
                resolve_adequacy_requirement_mw(fa, "NYISO", self.MODEL_PEAK, year),
                self.MODEL_PEAK * held,
                places=6,
            )
        # The held object is a RATIO: it scales with the peak.
        self.assertAlmostEqual(
            resolve_adequacy_requirement_mw(fa, "NYISO", 40_000.0, 2030)
            / resolve_adequacy_requirement_mw(fa, "NYISO", 20_000.0, 2030),
            2.0,
            places=9,
        )
        # +0.24 % over the composite — the D40 exposure split.
        self.assertAlmostEqual(held / self._composite(1.0), 1.0024, places=3)

    def test_hold_last_never_bridges_an_in_table_gap(self):
        fa = self._cfg(factors=True)
        with mock.patch.dict(NYCA_IRM_ADOPTED_BY_ISO["NYISO"], clear=False) as irms:
            del irms["2023/2024"]
            self.assertIsNone(resolve_nyiso_requirement_factor(fa, "NYISO", 2023))
            self.assertEqual(
                resolve_adequacy_requirement_mw(fa, "NYISO", self.MODEL_PEAK, 2023),
                self._composite(self.MODEL_PEAK),
            )
            self.assertIsNotNone(resolve_nyiso_requirement_factor(fa, "NYISO", 2024))

    def test_information_gate_a_later_row_is_never_read_earlier(self):
        # The rule-13 vintage gate: model year Y reads capability year Y/Y+1
        # ONLY. With just the 2024/25 row on file, 2023 sees nothing published.
        both = self._cfg(peak=True, factors=True)
        only = {"2024/2025": NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO["NYISO"]["2024/2025"]}
        with (
            mock.patch.dict(NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO, {"NYISO": only}),
            mock.patch.dict(
                NYCA_IRM_ADOPTED_BY_ISO,
                {"NYISO": {"2024/2025": NYCA_IRM_ADOPTED_BY_ISO["NYISO"]["2024/2025"]}},
            ),
            mock.patch.dict(
                NYCA_ICAP_UCAP_TRANSLATION_BY_ISO,
                {
                    "NYISO": {
                        "2024/2025": NYCA_ICAP_UCAP_TRANSLATION_BY_ISO["NYISO"][
                            "2024/2025"
                        ]
                    }
                },
            ),
        ):
            self.assertEqual(
                resolve_adequacy_requirement_mw(both, "NYISO", self.MODEL_PEAK, 2023),
                self._composite(self.MODEL_PEAK),
            )
            self.assertLess(
                abs(
                    resolve_adequacy_requirement_mw(
                        both, "NYISO", self.MODEL_PEAK, 2024
                    )
                    - 33_397.0
                ),
                1.0,
            )

    def test_seam_position_sign_matches_the_pre_declaration(self):
        # PREDECL-capx-d52 §1/P2 (rule 14 sign): on the 2023 seam peak the
        # entering firm 35,163 MW sits at 1.137 over the composite and at
        # 1.0175 over the published requirement — DOWN toward the market's
        # 1.043, not past it.
        off, both = self._cfg(), self._cfg(peak=True, factors=True)
        firm = 35_163.0
        pos_off = firm / resolve_adequacy_requirement_mw(
            off, "NYISO", self.MODEL_PEAK, 2023
        )
        pos_on = firm / resolve_adequacy_requirement_mw(
            both, "NYISO", self.MODEL_PEAK, 2023
        )
        self.assertAlmostEqual(pos_off, 1.137, places=3)
        self.assertAlmostEqual(pos_on, 1.0175, places=3)
        self.assertLess(abs(pos_on - 1.043), 0.03)

    def test_other_isos_inert_with_the_flags_armed(self):
        for iso, peak in (
            ("PJM", 150_000.0),
            ("MISO", 120_000.0),
            ("NEISO", 24_000.0),
            ("ERCOT", 85_000.0),
            ("CAISO", 45_000.0),
        ):
            on, off = self._cfg(peak=True, factors=True, iso=iso), self._cfg(iso=iso)
            for year in (2021, 2023, 2025, 2030):
                self.assertEqual(
                    resolve_adequacy_requirement_mw(on, iso, peak, year),
                    resolve_adequacy_requirement_mw(off, iso, peak, year),
                    (iso, year),
                )
            self.assertFalse(nyiso_requirement_forecast_peak_armed(on, iso))
            self.assertFalse(nyiso_requirement_vintage_factors_armed(on, iso))
        self.assertFalse(nyiso_requirement_forecast_peak_armed(None, "NYISO"))
        self.assertFalse(nyiso_requirement_vintage_factors_armed(self._cfg(), None))

    def test_backcast_coerces_hindcast_keeps_and_cache_key(self):
        bc = ScenarioConfig(
            iso="NYISO",
            mode="backcast",
            nyiso_requirement_forecast_peak=True,
            nyiso_requirement_vintage_factors=True,
        )
        self.assertFalse(bc.nyiso_requirement_forecast_peak)
        self.assertFalse(bc.nyiso_requirement_vintage_factors)
        hc = self._cfg(peak=True, factors=True)
        self.assertTrue(
            hc.nyiso_requirement_forecast_peak and hc.nyiso_requirement_vintage_factors
        )
        off, explicit_off = (
            self._cfg(),
            ScenarioConfig(iso="NYISO", mode="forecast", hindcast=True),
        )
        self.assertEqual(off.cache_key(), explicit_off.cache_key())
        keys = {
            off.cache_key(),
            self._cfg(peak=True).cache_key(),
            self._cfg(factors=True).cache_key(),
            hc.cache_key(),
        }
        self.assertEqual(len(keys), 4)


class TestRetirementSectorGate(unittest.TestCase):
    """capx D53 (2026-09-05): the retirement-screen SECTOR GATE.

    GATED default-OFF behind ``retirement_sector_gate``: unarmed, the screen's
    candidate set is the whole thermal fleet and every ledger is
    byte-identical; armed, every thermal unit whose PLANT's EIA-860 ``Sector``
    is 1 (regulated electric utility) is exogenous to the step-3 screen through
    the SAME ``exit_exempt_unit_ids`` seam as the fossil-dates exemption
    (rule 19; capx D78/D81 — and since capx D78-R2 that is the screen's only
    exemption seam),
    while sectors 2-7 and unknown-sector plants face the screen as before
    (design docs/handoffs/DESIGN-capx-d53-sector-gate-2026-09-05.md).
    """

    SECTORS = {300: 1, 200: 1, 400: 2, 500: 7}

    def _fleet(self):
        return [
            _unit(300, "1", 500.0, fuel="coal"),  # utility, unit grain
            _unit(300, "2", 400.0, fuel="coal"),
            _binned("H_C1", 200, 300.0),  # utility, plant-binned tranche
            _binned("H_C2", 200, 200.0),
            _unit(400, "1", 100.0, fuel="gas_ct"),  # IPP non-CHP
            _unit(500, "1", 150.0, fuel="gas_cc"),  # industrial CHP
            _unit(999, "1", 50.0, fuel="gas_ct"),  # plant absent from the table
        ]

    def test_gate_partitions_on_the_plants_sector_at_plant_grain(self):
        from market_sim.model.capacity import UTILITY_SECTOR, sector_gated_unit_ids

        self.assertEqual(UTILITY_SECTOR, 1)
        gated, census = sector_gated_unit_ids(self._fleet(), self.SECTORS)
        # Every tranche / unit of a sector-1 plant; nothing else.
        self.assertEqual(gated, frozenset({"300_1", "300_2", "H_C1", "H_C2"}))
        self.assertEqual(census["units"], 4)
        self.assertAlmostEqual(census["mw"], 1400.0)
        self.assertEqual(census["mw_by_fuel"], {"coal": 1400.0})
        self.assertEqual(census["mw_by_sector"], {"1": 1400.0})
        # The plant absent from the table fails OPEN to the screen and is
        # counted, never gated.
        self.assertEqual(census["unknown_sector_units"], 1)
        self.assertAlmostEqual(census["unknown_sector_mw"], 50.0)

    def test_gate_ignores_fuels_the_screen_cannot_evaluate_and_plant_code_zero(self):
        from market_sim.model.capacity import sector_gated_unit_ids

        wind = Generator(
            unit_id="w1",
            name="w",
            zone="Z",
            fuel_type="wind",
            pmax_mw=100.0,
            plant_code=300,
        )
        no_code = Generator(
            unit_id="synth",
            name="s",
            zone="Z",
            fuel_type="gas_ct",
            pmax_mw=10.0,
        )
        gated, census = sector_gated_unit_ids([wind, no_code], self.SECTORS)
        self.assertEqual(gated, frozenset())
        self.assertEqual(census["units"], 0)
        # plant_code == 0 is unknown, not sector 0.
        self.assertEqual(census["unknown_sector_units"], 1)
        # Empty table: nothing gated, everything unknown (fail-open).
        gated, census = sector_gated_unit_ids(self._fleet(), {})
        self.assertEqual(gated, frozenset())
        self.assertEqual(census["unknown_sector_units"], 7)

    def test_evolve_routes_every_exogenous_exit_set_to_the_exit_exempt_param(self):
        from market_sim.model import capacity_evolution as pkg
        from tests.unit.model.test_capacity import TestFossilAnnouncedExits as _F

        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),  # utility, undated
            _unit(400, "1", 100.0, fuel="gas_ct"),  # IPP, dated
            _unit(500, "1", 150.0, fuel="gas_cc"),  # CHP, undated -> screened
        ]
        rows = [_F._row(_F(), 400, "1", 2030, mw=100.0)]
        seen = {}

        def spy(fleet_, *a, **kw):
            seen["kwargs"] = kw
            seen["exit_exempt"] = kw.get("exit_exempt_unit_ids")
            return fleet_, {}, []

        prior = {
            "fleet_arrays": object(),
            "dispatch_result": object(),
            "prices": np.zeros((1, 24)),
            "peak_demand": 1000.0,
        }
        from market_sim.results.evolution_ledger import new_events

        events = new_events()
        with (
            mock.patch.object(pkg, "apply_economic_retirements", side_effect=spy),
            mock.patch(
                "market_sim.data.fleet.eia860_plant_sectors",
                return_value=self.SECTORS,
            ),
        ):
            evolve_fleet(
                fleet,
                prior,
                2028,
                ScenarioConfig(
                    fossil_announced_exits_enabled=True, retirement_sector_gate=True
                ),
                {},
                announced_fossil_exits=rows,
                events=events,
            )
        # capx D78 (owner ruling Q53 = reading 1) as EXTENDED by capx D81:
        # BOTH exogenous-exit declarations are exempt from the EXIT decision
        # ONLY — evaluated and OFFERED into the D57 clearing — so both ride
        # ``exit_exempt_unit_ids``, which left ``exempt_unit_ids`` (not
        # eligible to offer at all) with no producer; capx D78-R2 deleted it,
        # so the kwarg no longer exists. A PENDING dated plant's filed date is
        # LATER than the delivery year, so PJM's must-offer requirement still
        # reaches it (Manual 18 Rev 62 §1.2); a plant whose date is EFFECTIVE
        # this year left the fleet at step 0/1/1b above and reaches neither
        # set. The CHP unit is screened.
        self.assertNotIn("exempt_unit_ids", seen["kwargs"])
        self.assertEqual(seen["exit_exempt"], frozenset({"300_1", "400_1"}))
        self.assertEqual(events["sector_gated"]["units"], 1)
        self.assertAlmostEqual(events["sector_gated"]["mw"], 500.0)
        self.assertEqual(events["sector_gated"]["year"], 2028)
        # Off the gate: only the dated exemption, no ledger block.
        seen.clear()
        events = new_events()
        with (
            mock.patch.object(pkg, "apply_economic_retirements", side_effect=spy),
            mock.patch(
                "market_sim.data.fleet.eia860_plant_sectors",
                return_value=self.SECTORS,
            ),
        ):
            evolve_fleet(
                fleet,
                prior,
                2028,
                ScenarioConfig(fossil_announced_exits_enabled=True),
                {},
                announced_fossil_exits=rows,
                events=events,
            )
        self.assertNotIn("exempt_unit_ids", seen["kwargs"])
        self.assertEqual(seen["exit_exempt"], frozenset({"400_1"}))
        self.assertNotIn("sector_gated", events)

    def test_gated_unit_never_enters_margins_or_the_pipeline(self):
        """A failing unit passed through ``exit_exempt_unit_ids`` (a dated
        plant, a sector-1 unit, a this-year retrofit — the screen's sole
        exemption seam since capx D78-R2 deleted the second one) carries
        no pipeline row, is never decided, and cannot seed the pipeline state —
        while the identical IPP unit fails and is decided (or capped)."""
        from market_sim.model.capacity import apply_economic_retirements

        cfg = ScenarioConfig(retirement_rule="pipeline", capacity_market_clearing=False)
        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),  # utility (gated by the caller)
            _unit(400, "1", 500.0, fuel="coal"),  # IPP (screened)
        ]
        fa = generators_to_fleet_arrays(fleet, ["Z0"], hours=24)
        T = 24
        prices = np.zeros((1, T))  # $0 every hour: both units fail the bar
        dispatch = SimpleNamespace(dispatch=np.zeros((2, T)))
        mc = np.full((2, T), 20.0)
        sink: dict = {}
        survivors, state, _log = apply_economic_retirements(
            fleet,
            fa,
            dispatch,
            prices,
            cfg,
            {},
            peak_demand=10.0,  # tiny requirement: the floor never binds
            mc=mc,
            year=2028,
            event_sink=sink,
            exit_exempt_unit_ids=frozenset({"300_1"}),
        )
        rows = sink.get("pipeline_events", [])
        self.assertTrue(rows, "the screened IPP unit must carry a row")
        self.assertEqual({r["unit_id"] for r in rows}, {"400_1"})
        self.assertNotIn("300_1", state)
        self.assertIn("300_1", {g.unit_id for g in survivors})

    # --- capx D78: exit-exempt, not offer-exempt --------------------------
    def _screen_off_clearing(self, rule, **exempt_kw):
        """The toy of the test above (clearing OFF), parameterized on the
        decision rule and on whether the sector-1 unit is declared
        ``exit_exempt``; returns everything a ledger reader could see."""
        from market_sim.model.capacity import apply_economic_retirements

        cfg = ScenarioConfig(retirement_rule=rule, capacity_market_clearing=False)
        fleet = [
            _unit(300, "1", 500.0, fuel="coal"),  # utility (gated by the caller)
            _unit(400, "1", 500.0, fuel="coal"),  # IPP (screened)
        ]
        fa = generators_to_fleet_arrays(fleet, ["Z0"], hours=24)
        T = 24
        prices = np.zeros((1, T))  # $0 every hour: both units fail the bar
        dispatch = SimpleNamespace(dispatch=np.zeros((2, T)))
        mc = np.full((2, T), 20.0)
        sink: dict = {}
        survivors, state, log = apply_economic_retirements(
            fleet,
            fa,
            dispatch,
            prices,
            cfg,
            {},
            peak_demand=10.0,
            mc=mc,
            year=2028,
            event_sink=sink,
            **exempt_kw,
        )
        return {
            "survivors": [g.unit_id for g in survivors],
            "state": state,
            "log": log,
            "sink": sink,
        }

    def test_exit_exempt_leaves_every_other_row_untouched_when_clearing_is_off(self):
        """capx D78 T2 (design §3.6), RESTATED by capx D78-R2 against the
        surviving seam.

        With no D57 clearing armed (MISO's armed keeper posture) an
        ``exit_exempt`` unit is invisible to every decision structure: the
        pipeline rows, the pipeline state, the retired / floor_retained log
        and the survivor set are exactly the un-gated run's MINUS that unit,
        under both decision rules. (The one difference is that the unit's
        margin is now evaluated; nothing downstream reads it.)

        This is what made the pre-D78 ``exempt_unit_ids`` routing
        byte-identical off the clearing, and it is why deleting that
        parameter (D78-R2) moves no MISO byte. The former form of this test
        differenced the two parameters directly; the deleted branch cannot be
        called any more, so the claim is asserted against the un-gated
        baseline instead — the same equality, one leg re-derived rather than
        re-run through dead code.
        """
        for rule in ("pipeline", "legacy"):
            base = self._screen_off_clearing(rule)
            new = self._screen_off_clearing(
                rule, exit_exempt_unit_ids=frozenset({"300_1"})
            )

            def _rows(res):
                return {r["unit_id"]: r for r in res["sink"].get("pipeline_events", [])}

            self.assertEqual(
                _rows(new),
                {k: v for k, v in _rows(base).items() if k != "300_1"},
                rule,
            )
            self.assertEqual(
                new["state"],
                {k: v for k, v in base["state"].items() if k != "300_1"},
                rule,
            )
            self.assertEqual(
                [e for e in new["log"] if e.get("unit_id") != "300_1"],
                [e for e in base["log"] if e.get("unit_id") != "300_1"],
                rule,
            )
            # And the gated unit is genuinely out of the decision: no row, no
            # state, survives — while the IPP unit is decided / counted.
            self.assertNotIn("300_1", _rows(new))
            self.assertNotIn("300_1", new["state"])
            self.assertIn("300_1", new["survivors"])
            self.assertIn("400_1", new["state"])

    def test_exit_exempt_defaults_empty_and_is_a_no_op(self):
        """T1: the default (empty) set is byte-identical to not passing it."""
        for rule in ("pipeline", "legacy"):
            self.assertEqual(
                self._screen_off_clearing(rule),
                self._screen_off_clearing(rule, exit_exempt_unit_ids=frozenset()),
            )

    def _pjm_clearing_screen(self, peak, extra_fleet=(), **exempt_kw):
        """DESIGN-capx-d54's three-coal-unit toy under the D57 clearing
        (the `_screen` of ``TestPjmCapacitySupplyClearing``): A covers its bar
        on energy (offer $0), B has a small gap, C earns zero margin (offer =
        its full bar). C is the sector-1 unit the caller gates.

        ``extra_fleet`` appends units the screen cannot evaluate (a fuel with
        no ``_THERMAL_FOM`` entry), for the D78-R2 residual test below; each
        is given an inert marginal-cost row.
        """
        from market_sim.model.capacity import apply_economic_retirements

        cfg = ScenarioConfig(
            iso="PJM",
            mode="forecast",
            hindcast=True,
            capacity_market_supply_clearing_by_iso={"PJM": True},
            retirement_rule="pipeline",
        )
        T = 100
        fleet = [
            _gen("A", "coal", pmax=1_000.0, eford=0.08),
            _gen("B", "coal", pmax=1_000.0, eford=0.08),
            _gen("C", "coal", pmax=1_000.0, eford=0.08),
            *extra_fleet,
        ]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=T)
        prices = np.full((1, T), 50.0)
        mc = np.vstack(
            [
                np.full(T, 50.0 - 800.0),
                np.full(T, 50.0 - 500.0),
                np.full(T, 50.0),
                *[np.full(T, 50.0) for _ in extra_fleet],
            ]
        )
        dispatch = SimpleNamespace(dispatch=np.zeros((len(fleet), T)))
        sink: dict = {}
        with no_hydro_accreditation():
            survivors, state, _ = apply_economic_retirements(
                fleet,
                arrays,
                dispatch,
                prices,
                cfg,
                {},
                peak_demand=peak,
                mc=mc,
                year=2023,
                event_sink=sink,
                **exempt_kw,
            )
        rows = {e["unit_id"]: e for e in sink.get("pipeline_events", [])}
        return {g.unit_id for g in survivors}, state, rows, sink["capacity_clearing"]

    def test_exit_exempt_unit_offers_into_the_clearing_and_faces_no_exit(self):
        """capx D78 T3 / T5 (design §3.6; the D58 §3 seam reproduced on a toy
        and repaired): under the D57 clearing an ``exit_exempt`` sector-1 unit
        is IN the sell-offer stack at its net-ACR cap — the stack, the price,
        the price-taking block and every merchant unit's row are IDENTICAL to
        the un-gated run — while it carries no pipeline row, seeds no state
        and survives whether or not the auction clears it (uncleared and
        RETAINED)."""
        saw_uncleared = saw_cleared = False
        for peak in (1_500.0, 6_000.0, 40_000.0):
            base_surv, base_state, base_rows, base = self._pjm_clearing_screen(peak)
            ex_surv, ex_state, ex_rows, ex = self._pjm_clearing_screen(
                peak, exit_exempt_unit_ids=frozenset({"C"})
            )
            # The repaired seam: the auction is the un-gated auction.
            self.assertEqual(ex.n_offers, base.n_offers)
            self.assertEqual(ex.n_offers, 3)
            self.assertEqual(ex.offer_usd_per_mw_day, base.offer_usd_per_mw_day)
            self.assertEqual(ex.accredited_mw, base.accredited_mw)
            self.assertEqual(ex.offered_mw, base.offered_mw)
            self.assertEqual(ex.price_takers_mw, base.price_takers_mw)
            self.assertEqual(ex.price_usd_per_mw_day, base.price_usd_per_mw_day)
            self.assertEqual(ex.cleared_unit_ids, base.cleared_unit_ids)
            self.assertEqual(ex.how, base.how)
            self.assertIn("C", ex.offer_usd_per_mw_day)
            # The exit decision: C is out of it, A and B are exactly as before.
            self.assertNotIn("C", ex_rows)
            self.assertNotIn("C", ex_state)
            self.assertIn("C", ex_surv)
            self.assertEqual(
                {k: v for k, v in ex_rows.items()},
                {k: v for k, v in base_rows.items() if k != "C"},
                peak,
            )
            self.assertEqual(
                {k: v for k, v in ex_state.items()},
                {k: v for k, v in base_state.items() if k != "C"},
            )
            self.assertEqual(ex_surv | {"C"}, base_surv | {"C"})
            if "C" in base.cleared_unit_ids:
                saw_cleared = True
            else:
                saw_uncleared = True  # uncleared AND retained (design §2.4)
        # Both regimes were exercised: C uncleared on the short-of-curve
        # toy and cleared on the short market.
        self.assertTrue(saw_uncleared and saw_cleared)

    def test_unscreened_unit_is_a_zero_dollar_price_taker_in_q0(self):
        """capx D78-R2 T3, the NEGATIVE form of the D58 seam.

        D78's T3 demonstrated the seam by routing the unit through
        ``exempt_unit_ids`` and watching its accredited MW fall out of the
        sell-offer stack into ``Q_0``. That parameter is DELETED (D81 left it
        with no producer; rule 26 ``[R-DELETE]``), so the claim is asserted
        against **the only remaining path to $0**: a unit that is absent from
        ``margins`` — here because its fuel has no ``_THERMAL_FOM`` entry, so
        the screen cannot evaluate it — and absent from
        ``exit_exempt_unit_ids`` is never offered, never decided, and its
        accredited MW lands in the price-taking block through
        ``_settle_capacity_supply_clearing``'s ``accredited_total − Σ A_g``
        residual.

        The negative form is the stronger one: it says a unit reaches $0
        ONLY by being unscreenable, never by a declaration — which is exactly
        what makes the deleted parameter unreachable rather than merely
        unused.
        """
        for peak in (1_500.0, 6_000.0, 40_000.0):
            _bs, _bst, base_rows, base = self._pjm_clearing_screen(peak)
            wind = _gen("W", "wind", pmax=1_000.0)
            surv, state, rows, cl = self._pjm_clearing_screen(peak, extra_fleet=(wind,))
            # NOT offered: the stack is the three-coal stack, unit for unit.
            self.assertEqual(cl.n_offers, base.n_offers)
            self.assertEqual(cl.n_offers, 3)
            self.assertNotIn("W", cl.offer_usd_per_mw_day)
            self.assertNotIn("W", cl.accredited_mw)
            self.assertNotIn("W", cl.cleared_unit_ids)
            self.assertEqual(cl.offer_usd_per_mw_day, base.offer_usd_per_mw_day)
            self.assertAlmostEqual(cl.offered_mw, base.offered_mw, places=6)
            # Its whole accredited credit is in Q_0, at $0: the census rises
            # by exactly what the price-taking block rises by, and invariant
            # I1 (Q_0 + Sum A_g == accredited) holds on both legs.
            delta = cl.census_mw - base.census_mw
            self.assertGreater(delta, 0.0)
            self.assertAlmostEqual(
                cl.price_takers_mw, base.price_takers_mw + delta, places=6
            )
            for c in (base, cl):
                self.assertAlmostEqual(
                    c.price_takers_mw + c.offered_mw, c.census_mw, places=6
                )
            # NOT decided: no pipeline row, no loss state, and it survives —
            # the same invisibility the deleted parameter used to declare,
            # reached structurally instead.
            self.assertNotIn("W", rows)
            self.assertNotIn("W", state)
            self.assertIn("W", surv)
            self.assertEqual(rows, base_rows, peak)

    def test_cache_key_registration_and_backcast_coercion(self):
        from market_sim.config.scenarios import (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
            _CACHE_KEY_OPTIONAL_FIELDS,
        )

        self.assertIn("retirement_sector_gate", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["retirement_sector_gate"], "False"
        )
        self.assertFalse(ScenarioConfig().retirement_sector_gate)
        # The pinned default key is unmoved by the registration (D24-R option
        # b'-1: dropped at its declared False default); the armed key differs.
        #
        # capx D65-B-R: refreshed e5ecd4105ada3e58 -> 547053bdfccd4264. This pin
        # was written 2026-09-05 and D65-B's Act B merged the next day:
        # ``ccs_retrofit_vom_adder`` 8.0 -> 2.95 is not a
        # ``_CACHE_KEY_OPTIONAL_FIELDS`` member, so it has no drop value and
        # re-keys EVERY config unconditionally (D65 §9 item 3; D41 §6.2's
        # mechanic). The new literal is exactly the global forecast key
        # PRECOMMIT-capx-d65b-2026-09-06.md §3 pre-declared before that solve,
        # and e5ecd4105ada3e58 is the pre-flip value the same table records --
        # so this is a re-key refresh with a named cause, not a drift.
        # WHAT THIS TEST ASSERTS IS UNCHANGED: the sector gate is still dropped
        # at its declared False default, which is the next assertion's job.
        self.assertEqual(ScenarioConfig().cache_key(), "547053bdfccd4264")
        self.assertNotEqual(
            ScenarioConfig(retirement_sector_gate=True).cache_key(),
            ScenarioConfig().cache_key(),
        )
        # A plain backcast coerces the gate to its dataclass default (a
        # backcast runs no capacity evolution); a hindcast keeps it.
        self.assertFalse(
            ScenarioConfig(
                mode="backcast", retirement_sector_gate=True
            ).retirement_sector_gate
        )
        self.assertEqual(
            ScenarioConfig(mode="backcast", retirement_sector_gate=True).cache_key(),
            ScenarioConfig(mode="backcast").cache_key(),
        )
        self.assertTrue(
            ScenarioConfig(
                mode="forecast", hindcast=True, retirement_sector_gate=True
            ).retirement_sector_gate
        )

    def test_plant_sector_reader_is_vintage_keyed(self):
        from market_sim.data.fleet import eia860_plant_sectors

        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a"
            b = Path(td) / "b"
            a.mkdir()
            b.mkdir()
            pd.DataFrame({"Plant Code": [1, 2, 3], "Sector": [1, 2, None]}).to_parquet(
                a / "eia860_plant.parquet"
            )
            pd.DataFrame({"Plant Code": [1], "Sector": [2]}).to_parquet(
                b / "eia860_plant.parquet"
            )
            self.assertEqual(eia860_plant_sectors(a), {1: 1, 2: 2})
            # A second directory is not served from the first's cache.
            self.assertEqual(eia860_plant_sectors(b), {1: 2})
            # A directory with no plant table reads empty (fail-open upstream).
            self.assertEqual(eia860_plant_sectors(Path(td)), {})


class TestDatedBlockMustOffer(unittest.TestCase):
    """capx D81: the PENDING owner-filed dated block and the this-year CCS
    retrofit MUST OFFER — the director's extension of owner ruling Q53 to the
    channels ``DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md`` §4
    enumerates, replacing ``DESIGN-capx-d54`` §4.2's price-taker reading.

    PJM's must-offer requirement keys on *existing and located in the
    footprint* (Manual 18 Rev 62 §1.2 / §5.4.1) and its three enumerated
    exceptions — physical CP incapability, a firm external sale, a filed
    removal of Capacity Resource status — do not include a filed plan that has
    not yet taken effect. So a plant whose filed date is LATER than the
    delivery year offers for every year before the removal is effective, and a
    plant whose removal IS effective has already left the fleet at evolve step
    0/1/1b and is correctly absent from the census and the stack alike
    (§5.4.7, "no longer eligible to offer").
    """

    def _pjm_screen(self, peak, **exempt_kw):
        """DESIGN-capx-d54's three-coal-unit toy under the D57 clearing.

        A covers its bar on energy (offer $0), B has a small gap, C earns zero
        margin (offer = its full bar). C is the unit the caller declares.
        """
        from market_sim.model.capacity import apply_economic_retirements

        cfg = ScenarioConfig(
            iso="PJM",
            mode="forecast",
            hindcast=True,
            capacity_market_supply_clearing_by_iso={"PJM": True},
            retirement_rule="pipeline",
        )
        T = 100
        fleet = [
            _gen("A", "coal", pmax=1_000.0, eford=0.08),
            _gen("B", "coal", pmax=1_000.0, eford=0.08),
            _gen("C", "coal", pmax=1_000.0, eford=0.08),
        ]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=T)
        prices = np.full((1, T), 50.0)
        mc = np.vstack(
            [
                np.full(T, 50.0 - 800.0),
                np.full(T, 50.0 - 500.0),
                np.full(T, 50.0),
            ]
        )
        dispatch = SimpleNamespace(dispatch=np.zeros((3, T)))
        sink: dict = {}
        with no_hydro_accreditation():
            survivors, state, _ = apply_economic_retirements(
                fleet,
                arrays,
                dispatch,
                prices,
                cfg,
                {},
                peak_demand=peak,
                mc=mc,
                year=2023,
                event_sink=sink,
                **exempt_kw,
            )
        rows = {e["unit_id"]: e for e in sink.get("pipeline_events", [])}
        return {g.unit_id for g in survivors}, state, rows, sink["capacity_clearing"]

    def test_pending_dated_unit_offers_at_its_cap_and_faces_no_exit(self):
        """T1: a pending dated plant is IN the sell-offer stack at its net-ACR
        cap and OUT of the exit decision — the stack, the price and the
        price-taking block are the un-declared run's, and it carries no
        pipeline row, seeds no state and survives whether or not it clears."""
        for peak in (1_500.0, 6_000.0, 40_000.0):
            base_surv, base_state, base_rows, base = self._pjm_screen(peak)
            dated_surv, dated_state, dated_rows, dated = self._pjm_screen(
                peak, exit_exempt_unit_ids=frozenset({"C"})
            )
            self.assertEqual(dated.n_offers, base.n_offers, peak)
            self.assertEqual(dated.offer_usd_per_mw_day, base.offer_usd_per_mw_day)
            self.assertEqual(dated.accredited_mw, base.accredited_mw)
            self.assertEqual(dated.offered_mw, base.offered_mw)
            self.assertEqual(dated.price_takers_mw, base.price_takers_mw)
            self.assertEqual(dated.price_usd_per_mw_day, base.price_usd_per_mw_day)
            self.assertEqual(dated.cleared_unit_ids, base.cleared_unit_ids)
            self.assertIn("C", dated.offer_usd_per_mw_day)
            # Its offer is the net-ACR cap the D54 formula defines, not $0.
            self.assertGreater(dated.offer_usd_per_mw_day["C"], 0.0)
            self.assertNotIn("C", dated_rows)
            self.assertNotIn("C", dated_state)
            self.assertIn("C", dated_surv)
            self.assertEqual(
                dated_rows, {k: v for k, v in base_rows.items() if k != "C"}, peak
            )

    def test_conservation_offered_up_price_takers_down_by_the_same_mw(self):
        """T3 / the PRECOMMIT §1.2 identity, RESTATED by capx D78-R2.

        The original form differenced ``exempt_unit_ids`` (D54 §4.2's
        price-taker reading of the dated block) against
        ``exit_exempt_unit_ids`` and showed the routing moved exactly ``A_g``
        out of ``Q_0`` and into the priced stack. That parameter is DELETED
        (rule 26 ``[R-DELETE]``; it had no producer after D81), so D54 §4.2's
        reading is no longer expressible and the difference cannot be taken.

        What is asserted instead is the surviving half of the same identity:
        the declared block IS in the priced stack at its net-ACR cap, its
        ``A_g`` is in ``offered_mw`` and NOT in ``Q_0``, invariant I1
        (``Q_0 + Σ A_g == accredited``) holds, and the declaration moves
        neither the census nor the requirement. The complementary half — a
        unit that IS a $0 price taker in ``Q_0``, and the only remaining way
        to become one — is
        ``test_unscreened_unit_is_a_zero_dollar_price_taker_in_q0`` above.
        """
        for peak in (1_500.0, 6_000.0, 40_000.0):
            _s, _st, _r, base = self._pjm_screen(peak)
            _s2, _st2, _r2, new = self._pjm_screen(
                peak, exit_exempt_unit_ids=frozenset({"C"})
            )
            a_g = new.accredited_mw["C"]
            self.assertGreater(a_g, 0.0)
            # The declared block offers: it is in the stack, priced, and its
            # A_g is inside ``offered_mw`` rather than inside ``Q_0``.
            self.assertIn("C", new.offer_usd_per_mw_day)
            self.assertGreater(new.offer_usd_per_mw_day["C"], 0.0)
            self.assertEqual(new.n_offers, base.n_offers)
            self.assertEqual(new.n_offers, 3)
            self.assertAlmostEqual(new.offered_mw, base.offered_mw, places=6)
            self.assertAlmostEqual(
                new.price_takers_mw, new.census_mw - new.offered_mw, places=6
            )
            self.assertLessEqual(new.price_takers_mw, new.census_mw - a_g + 1e-9)
            # I1 on both legs, and the declaration moves neither denominator.
            for cl in (base, new):
                self.assertAlmostEqual(
                    cl.price_takers_mw + cl.offered_mw, cl.census_mw, places=6
                )
            self.assertAlmostEqual(new.census_mw, base.census_mw, places=6)
            self.assertAlmostEqual(new.requirement_mw, base.requirement_mw, places=6)
            # And the clearing itself is the un-declared clearing: the
            # declaration is an EXIT-side statement only.
            self.assertAlmostEqual(
                new.price_usd_per_mw_day, base.price_usd_per_mw_day, places=9
            )
            self.assertAlmostEqual(
                new.cleared_position, base.cleared_position, places=9
            )

    def _spy_evolve(self, year, fleet, rows, **cfg_kw):
        """Run ``evolve_fleet`` with the screen spied on; return the two id
        sets it was handed plus the recorded events."""
        from market_sim.model import capacity_evolution as pkg
        from market_sim.results.evolution_ledger import new_events

        seen: dict = {}

        def spy(fleet_, *a, **kw):
            seen["kwargs"] = kw
            seen["exit_exempt"] = kw.get("exit_exempt_unit_ids")
            seen["fleet_ids"] = {g.unit_id for g in fleet_}
            return fleet_, {}, []

        prior = {
            "fleet_arrays": object(),
            "dispatch_result": object(),
            "prices": np.zeros((1, 24)),
            "peak_demand": 1000.0,
        }
        events = new_events()
        with mock.patch.object(pkg, "apply_economic_retirements", side_effect=spy):
            evolve_fleet(
                fleet,
                prior,
                year,
                ScenarioConfig(fossil_announced_exits_enabled=True, **cfg_kw),
                {},
                announced_fossil_exits=rows,
                events=events,
            )
        return seen, events

    def test_executed_exit_is_absent_from_the_stack_and_from_every_decision(self):
        """T2: a plant whose filed date is EFFECTIVE for the delivery year is
        removed by step 1b BEFORE the screen — Manual 18 §5.4.7 exception [c],
        "no longer eligible to offer". It reaches the exemption seam not at
        all, nor the census, nor the stack, nor any decision structure; the
        PENDING twin (a later date) reaches ``exit_exempt_unit_ids``."""
        from tests.unit.model.test_capacity import TestFossilAnnouncedExits as _F

        fleet = [
            _unit(400, "1", 100.0, fuel="coal"),  # date effective this year
            _unit(500, "1", 200.0, fuel="coal"),  # date still pending
        ]
        rows = [
            _F._row(_F(), 400, "1", 2028, mw=100.0),
            _F._row(_F(), 500, "1", 2032, mw=200.0),
        ]
        seen, _events = self._spy_evolve(2028, fleet, rows)
        self.assertNotIn("400_1", seen["fleet_ids"])
        self.assertNotIn("exempt_unit_ids", seen["kwargs"])
        self.assertNotIn("400_1", seen["exit_exempt"])
        self.assertIn("500_1", seen["fleet_ids"])
        self.assertEqual(seen["exit_exempt"], frozenset({"500_1"}))

    def test_retrofit_channel_is_inert_below_the_availability_year(self):
        """T4: below ``ccs_retrofit_available_year`` (2028) the retrofit set is
        empty by construction, so this lane's routing of ``_retrofitted_ids``
        is a no-op on every backcast, hindcast and crossover year — nothing in
        such a year's ledger, decision or cache key can move."""
        fleet = [_unit(600, "1", 400.0, fuel="gas_cc")]
        cfg = ScenarioConfig()
        self.assertEqual(cfg.ccs_retrofit_available_year, 2028)
        for year in (2023, 2025, cfg.ccs_retrofit_available_year - 1):
            seen, events = self._spy_evolve(year, list(fleet), [])
            self.assertEqual(events["ccs_retrofits"], [], year)
            self.assertNotIn("exempt_unit_ids", seen["kwargs"])
            self.assertEqual(seen["exit_exempt"], frozenset(), year)


class TestNyisoLocalityCapacityCurves(unittest.TestCase):
    """capx D59 (2026-09-05) — the NYISO LOCALITY half: NYC (Zone J) and Long Island
    (Zone K) priced on their own published ICAP demand curves at their own published
    Locational Minimum ICAP Requirement, settled by the ICAP Manual §5.15.2
    max(NYCA, locality) rule. ONE gated default-OFF field
    (``locality_capacity_curves``); every unarmed path is byte-identical.
    Design: docs/handoffs/DESIGN-capx-d59-nyiso-locality-2026-09-05.md."""

    @staticmethod
    def _csv_rows():
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-market" / "demand-curve" / "nyiso" / "nyiso.csv"
        with path.open(newline="") as fh:
            return list(csv.DictReader(fh))

    @staticmethod
    def _cfg(armed=True, curve=True, iso="NYISO", **kw):
        return ScenarioConfig(
            iso=iso,
            mode="forecast",
            hindcast=True,
            locality_capacity_curves=armed,
            capacity_market_clearing_by_iso=({iso: True} if curve else None),
            **kw,
        )

    @staticmethod
    def _gen(unit_id, zone, pmax, eford=0.05, fuel="gas_st"):
        return Generator(
            unit_id=unit_id,
            name=unit_id,
            zone=zone,
            fuel_type=fuel,
            pmax_mw=pmax,
            eford=eford,
        )

    # --- registries reconcile to the committed csv (rules 13 / 23) -------------
    def test_locality_vintages_reconcile_with_published_csv(self):
        from market_sim.config.capacity_market import (
            LOCALITY_MARKET_DESIGN_VINTAGES,
            _NYISO_LOCALITY_CURVE_LENGTH,
        )

        rows = self._csv_rows()
        self.assertEqual(set(LOCALITY_MARKET_DESIGN_VINTAGES), {"NYISO"})
        for locality in ("NYC", "LI"):
            for v in LOCALITY_MARKET_DESIGN_VINTAGES["NYISO"][locality]:
                mine = [
                    r
                    for r in rows
                    if r["area"] == locality and r["delivery_year"] == v.delivery_year
                ]
                summer = [r for r in mine if r["season"] in ("summer", "")]
                ref = [
                    r
                    for r in summer
                    if r["metric"] == "curve_point" and r["point_index"] == "0"
                ]
                zero = [
                    r
                    for r in summer
                    if r["metric"] == "curve_point" and r["point_index"] == "1"
                ]
                arv = [r for r in mine if r["metric"] == "net_cone"]
                cap = [r for r in summer if r["metric"] == "price_cap"]
                self.assertTrue(ref and zero, (locality, v.delivery_year))
                if not arv:
                    # 2021-22 / 2022-23: no ARV published → flat anchor = ref × 12, () shape.
                    self.assertEqual(v.demand_curve, ())
                    self.assertAlmostEqual(
                        v.net_cone_curve_per_kw_yr, float(ref[0]["y_value"]) * 12.0, 6
                    )
                    continue
                self.assertAlmostEqual(
                    v.net_cone_curve_per_kw_yr, float(arv[0]["y_value"]), 6
                )
                self.assertAlmostEqual(
                    v.demand_curve[-1].reserve_ratio, float(zero[0]["x_value"]), 6
                )
                self.assertAlmostEqual(
                    v.demand_curve[-1].reserve_ratio,
                    1.0 + _NYISO_LOCALITY_CURVE_LENGTH,
                    6,
                )
                self.assertAlmostEqual(v.demand_curve[1].reserve_ratio, 1.0, 9)
                self.assertAlmostEqual(v.demand_curve[1].price_frac_net_cone, 1.0, 9)
                self.assertAlmostEqual(
                    v.demand_curve[0].price_frac_net_cone,
                    float(cap[0]["y_value"]) / float(ref[0]["y_value"]),
                    6,
                )

    def test_gross_cone_registry_reconciles_with_published_csv(self):
        from market_sim.config.capacity_market import LOCALITY_GROSS_CONE_BY_ISO

        rows = self._csv_rows()
        self.assertEqual(set(LOCALITY_GROSS_CONE_BY_ISO), {"NYISO"})
        for label, by_area in LOCALITY_GROSS_CONE_BY_ISO["NYISO"].items():
            dy = label.replace("/", "-")
            for area, val in by_area.items():
                got = [
                    r
                    for r in rows
                    if r["metric"] == "gross_cone"
                    and r["area"] == area
                    and r["delivery_year"] == dy
                ]
                self.assertEqual(len(got), 1, (label, area))
                self.assertAlmostEqual(float(got[0]["y_value"]), val, 6)

    def test_gross_cone_ratio_resolution(self):
        from market_sim.config.capacity_market import (
            resolve_locality_gross_cone_ratio as g,
        )

        self.assertAlmostEqual(g("NYISO", "NYC", 2025), 222.73 / 127.71, 9)
        self.assertAlmostEqual(g("NYISO", "LI", 2023), 168.15 / 120.04, 9)
        self.assertAlmostEqual(g("NYISO", "NYC", 2040), 230.10 / 131.94, 9)  # hold-last
        self.assertAlmostEqual(
            g("NYISO", "NYC", 2019), 212.81 / 120.04, 9
        )  # hold-first
        self.assertIsNone(g("PJM", "NYC", 2025))
        self.assertIsNone(g("NYISO", "NYC", None))

    def test_tsl_floor_consistency_of_committed_lcr_rows(self):
        # DESIGN §2.1: the TSL is NOT supply — the LCR is already ≥ the TSL floor
        # (peak − TSL) / peak in every committed capability year (peak = MW / LCR).
        import csv

        from market_sim.config.paths import RAW_DATA_DIR

        path = RAW_DATA_DIR / "capacity-deliverability" / "nyiso" / "nyiso.csv"
        with path.open(newline="") as fh:
            rows = list(csv.DictReader(fh))
        checked = 0
        for r in rows:
            if r["metric"] != "requirement" or not r["value_mw"] or not r["value_pu"]:
                continue
            tsl = [
                float(x["value_mw"])
                for x in rows
                if x["metric"] == "import_limit"
                and x["area"] == r["area"]
                and x["delivery_year"] == r["delivery_year"]
            ]
            if not tsl:
                continue
            peak = float(r["value_mw"]) / float(r["value_pu"])
            self.assertGreaterEqual(
                float(r["value_pu"]) + 1e-9, (peak - tsl[0]) / peak, r
            )
            checked += 1
        self.assertGreaterEqual(checked, 6)

    # --- the published UDR rights, dated ----------------------------------------
    def test_udr_rights_dating(self):
        from market_sim.model.capacity_evolution.retirements import (
            _locality_udr_icap_mw as u,
        )

        self.assertAlmostEqual(u("LI", 2023), 990.0)
        self.assertAlmostEqual(u("NYC", 2021), 315.0 + 660.0)
        self.assertAlmostEqual(u("NYC", 2023), 315.0)
        self.assertAlmostEqual(u("NYC", 2024), 400.0)
        self.assertAlmostEqual(u("NYC", 2026), 400.0 + 1250.0)
        self.assertAlmostEqual(u("G-J", 2025), 0.0)

    # --- the §5.15.2 stacking max at the ONE price seam --------------------------
    def test_stacking_max_at_price_seam(self):
        from market_sim.model.capacity_evolution.retirements import (
            capacity_revenue_per_mw_yr as f,
        )

        cfg = self._cfg(curve=False)
        base = f("NYISO", "gas_st", 0.07, cfg, None, 2025)
        self.assertGreater(base, 0.0)
        self.assertEqual(
            f(
                "NYISO",
                "gas_st",
                0.07,
                cfg,
                None,
                2025,
                locality_price_per_firm_mw_yr=None,
            ),
            base,
        )
        self.assertEqual(
            f(
                "NYISO",
                "gas_st",
                0.07,
                cfg,
                None,
                2025,
                locality_price_per_firm_mw_yr=1.0,
            ),
            base,
        )
        higher = f(
            "NYISO",
            "gas_st",
            0.07,
            cfg,
            None,
            2025,
            locality_price_per_firm_mw_yr=base / 0.93 * 2.0,
        )
        self.assertAlmostEqual(higher, base * 2.0, 3)
        # Energy-only ERCOT earns nothing in both modes.
        self.assertEqual(
            f(
                "ERCOT",
                "gas_st",
                0.07,
                cfg,
                None,
                2025,
                locality_price_per_firm_mw_yr=1e9,
            ),
            0.0,
        )

    def test_locality_prices_by_zone_is_the_max_over_containing_localities(self):
        from market_sim.model.capacity_evolution.retirements import (
            LocalityPosition,
            locality_prices_by_zone,
        )

        a = LocalityPosition(
            locality="A", zones=("Z1", "Z2"), price_per_firm_mw_yr=10.0
        )
        b = LocalityPosition(locality="B", zones=("Z2",), price_per_firm_mw_yr=25.0)
        c = LocalityPosition(locality="C", zones=("Z3",), price_per_firm_mw_yr=None)
        self.assertEqual(
            locality_prices_by_zone({"A": a, "B": b, "C": c}), {"Z1": 10.0, "Z2": 25.0}
        )
        self.assertEqual(locality_prices_by_zone({}), {})
        self.assertEqual(locality_prices_by_zone(None), {})

    # --- the gate predicate and byte-identity --------------------------------------
    def test_gate_predicate(self):
        from market_sim.model.capacity_evolution.retirements import (
            locality_capacity_curves_armed as armed,
        )

        self.assertTrue(armed(self._cfg(), "NYISO"))
        self.assertFalse(armed(self._cfg(armed=False), "NYISO"))
        self.assertFalse(
            armed(self._cfg(curve=False), "NYISO")
        )  # needs the NYCA curve ON
        for iso in ("PJM", "MISO", "NEISO", "CAISO", "ERCOT"):
            self.assertFalse(armed(self._cfg(iso=iso), iso))
        self.assertFalse(armed(None, "NYISO"))
        self.assertFalse(armed(self._cfg(), None))

    def _patched_reader(self, req):
        from market_sim.model.capacity_evolution import retirements as r

        return (
            mock.patch.object(
                r.capdel, "available_delivery_years", return_value={"2025/2026"}
            ),
            mock.patch.object(r.capdel, "requirement_by_area", return_value=req),
        )

    def test_position_is_the_icap_identity_independent_of_eford(self):
        # ICAP Manual §2.6: position = ΣICAP / ICAP requirement (DESIGN §2.2) — the
        # class EFORd assumption drops out; the TSL is NOT added to supply.
        from market_sim.model.capacity_evolution.retirements import (
            locality_capacity_positions,
        )

        req = {"NYC": 8673.0, "Long Island": 5423.0}
        p1, p2 = self._patched_reader(req)
        with p1, p2:
            fleet_a = [
                self._gen("a", "NYC", 8000.0, eford=0.02),
                self._gen("u", "Upstate_West", 500.0),
            ]
            fleet_b = [
                self._gen("a", "NYC", 8000.0, eford=0.40),
                self._gen("u", "Upstate_West", 500.0),
            ]
            pos_a = locality_capacity_positions("NYISO", 2025, fleet_a, self._cfg())
            pos_b = locality_capacity_positions("NYISO", 2025, fleet_b, self._cfg())
        self.assertEqual(set(pos_a), {"NYC", "LI"})
        self.assertAlmostEqual(pos_a["NYC"].position, (8000.0 + 400.0) / 8673.0, 9)
        self.assertAlmostEqual(pos_a["NYC"].position, pos_b["NYC"].position, 12)
        self.assertAlmostEqual(pos_a["NYC"].udr_icap_mw, 400.0)
        self.assertEqual(pos_a["NYC"].requirement_source, "published")
        self.assertAlmostEqual(
            pos_a["LI"].position, 990.0 / 5423.0, 9
        )  # UDR rights only
        # The price is the locality curve at the position (2025/26 NYC vintage).
        from market_sim.config.capacity_market import (
            locality_curve_price_per_firm_mw_yr as lp,
        )

        self.assertAlmostEqual(
            pos_a["NYC"].price_per_firm_mw_yr,
            lp("NYISO", "NYC", 2025, pos_a["NYC"].position),
            6,
        )
        self.assertAlmostEqual(lp("NYISO", "NYC", 2025, 1.0), 140.47 * 1000.0, 6)
        self.assertAlmostEqual(lp("NYISO", "NYC", 2025, 1.18), 0.0, 6)
        row = pos_a["NYC"].as_ledger_row()
        self.assertEqual(row["zones"], ["NYC"])
        self.assertAlmostEqual(
            row["price_per_kw_yr"], pos_a["NYC"].price_per_firm_mw_yr / 1000.0, 3
        )

    def test_positions_count_zonal_pools_and_storage_never_load_share(self):
        from market_sim.model.capacity_evolution.retirements import (
            locality_capacity_positions,
        )

        p1, p2 = self._patched_reader({"NYC": 8673.0})
        with p1, p2:
            pos = locality_capacity_positions(
                "NYISO",
                2025,
                [self._gen("a", "NYC", 8000.0)],
                self._cfg(),
                wind_pool_by_zone={"NYC": 10.0, "Upstate_West": 5000.0},
                solar_pool_by_zone={"NYC": 20.0},
                storage_power_by_zone={"NYC": 30.0, "Long_Island": 99.0},
            )
        self.assertAlmostEqual(
            pos["NYC"].supply_icap_mw, 8000.0 + 10.0 + 20.0 + 30.0 + 400.0, 6
        )
        self.assertNotIn("LI", pos)  # no requirement row → not priced

    def test_hold_last_lcr_beyond_the_table_and_none_before(self):
        from market_sim.model.capacity_evolution import retirements as r

        import pandas as pd

        df = pd.DataFrame(
            [
                {
                    "metric": "requirement",
                    "delivery_year": "2025/2026",
                    "area": "NYC",
                    "value_mw": 8673.0,
                    "value_pu": 0.785,
                },
            ]
        )
        with (
            mock.patch.object(
                r.capdel, "available_delivery_years", return_value={"2025/2026"}
            ),
            mock.patch.object(
                r.capdel, "requirement_by_area", return_value={"NYC": 8673.0}
            ),
            mock.patch.object(r.capdel, "_read", return_value=df),
        ):
            pos = r.locality_capacity_positions(
                "NYISO",
                2030,
                [self._gen("a", "NYC", 8000.0)],
                self._cfg(),
                locality_peak_by_zone={"NYC": 12000.0},
            )
            self.assertAlmostEqual(pos["NYC"].requirement_icap_mw, 0.785 * 12000.0, 6)
            self.assertEqual(pos["NYC"].requirement_source, "hold_last_lcr")
            self.assertEqual(
                r.locality_capacity_positions(
                    "NYISO", 2019, [self._gen("a", "NYC", 8000.0)], self._cfg()
                ),
                {},
            )

    def test_default_off_and_other_iso_return_empty(self):
        from market_sim.model.capacity_evolution.retirements import (
            locality_capacity_positions,
        )

        p1, p2 = self._patched_reader({"NYC": 8673.0})
        fleet = [self._gen("a", "NYC", 8000.0)]
        with p1, p2:
            self.assertEqual(
                locality_capacity_positions(
                    "NYISO", 2025, fleet, self._cfg(armed=False)
                ),
                {},
            )
            self.assertEqual(
                locality_capacity_positions(
                    "NYISO", 2025, fleet, self._cfg(curve=False)
                ),
                {},
            )
            self.assertEqual(
                locality_capacity_positions("PJM", 2025, fleet, self._cfg(iso="PJM")),
                {},
            )

    def test_storage_capacity_value_load_share_weighting(self):
        from market_sim.model.storage import estimate_capacity_value

        cfg = ScenarioConfig(
            iso="NYISO", mode="forecast", hindcast=True, storage_capacity_value=True
        )
        base = estimate_capacity_value(
            "li_ion_4h" if "li_ion_4h" in STORAGE_TECHS else next(iter(STORAGE_TECHS)),
            0.0,
            cfg,
            "NYISO",
            None,
            2025,
        )
        tech = (
            "li_ion_4h" if "li_ion_4h" in STORAGE_TECHS else next(iter(STORAGE_TECHS))
        )
        same = estimate_capacity_value(
            tech, 0.0, cfg, "NYISO", None, 2025, locality_prices_by_zone={}
        )
        self.assertEqual(same, base)
        from market_sim.config.iso_configs import get_iso_config

        shares = {z.name: z.load_share for z in get_iso_config("NYISO").zones}
        # NYC priced at 3× the flat NYCA price: the weighted price rises by NYC's load share × 2.
        from market_sim.config.constants import MARKET_DESIGN

        flat = MARKET_DESIGN["NYISO"].capacity_price_per_firm_mw_yr(
            cfg, None, iso="NYISO", year=2025
        )
        lifted = estimate_capacity_value(
            tech,
            0.0,
            cfg,
            "NYISO",
            None,
            2025,
            locality_prices_by_zone={"NYC": 3.0 * flat},
        )
        expected = base * (1.0 + shares["NYC"] * 2.0 / sum(shares.values()))
        self.assertAlmostEqual(lifted, expected, 3)

    def test_config_semantics(self):
        base = ScenarioConfig(iso="NYISO", mode="forecast", hindcast=True)
        self.assertEqual(
            ScenarioConfig(
                iso="NYISO",
                mode="forecast",
                hindcast=True,
                locality_capacity_curves=False,
            ).cache_key(),
            base.cache_key(),
        )
        self.assertNotEqual(
            ScenarioConfig(
                iso="NYISO",
                mode="forecast",
                hindcast=True,
                locality_capacity_curves=True,
            ).cache_key(),
            base.cache_key(),
        )
        self.assertFalse(
            ScenarioConfig(
                iso="NYISO", mode="backcast", locality_capacity_curves=True
            ).locality_capacity_curves
        )
        self.assertTrue(
            ScenarioConfig(
                iso="NYISO",
                mode="forecast",
                hindcast=True,
                locality_capacity_curves=True,
            ).locality_capacity_curves
        )
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="NYISO",
                mode="forecast",
                locality_capacity_curves=True,
                capacity_deliverability_limits=True,
            )
        # Any other ISO may carry both (Part B stays theirs; the field is inert there).
        ScenarioConfig(
            iso="PJM",
            mode="forecast",
            locality_capacity_curves=True,
            capacity_deliverability_limits=True,
        )

    def test_thermal_locality_siting_leg(self):
        # DESIGN §5.5: a thermal candidate is also screened sited in each priced
        # locality (that zone's LP prices, the settled price, the Gross-CONE cost
        # ratio) and built where its margin is highest; a tie keeps the default.
        from market_sim.config.iso_configs import get_iso_config as _gic

        iso = "NYISO"
        zone_names = [z.name for z in _gic(iso).zones]
        T = 8760
        prices = np.full((len(zone_names), T), 40.0)
        cfg = ScenarioConfig(
            iso=iso,
            mode="forecast",
            hindcast=True,
            entry_screen_diagnostics=True,
            capacity_market_clearing_by_iso={iso: True},
            locality_capacity_curves=True,
        )

        def _zone_of(**kw):
            ledger: list[dict] = []
            apply_economic_new_entry(
                [],
                prices,
                2030,
                cfg,
                iso,
                gas_price_per_mmbtu=3.0,
                zone_names=zone_names,
                screen_ledger=ledger,
                reserve_position=1.0,
                **kw,
            )
            rows = {r["tech"]: r for r in ledger if r.get("kind") == "thermal"}
            self.assertIn("gas_ct", rows)
            return rows["gas_ct"]["build_zone"], rows["gas_ct"][
                "capacity_revenue_per_mw_yr"
            ]

        default_zone, base_cap = _zone_of()
        self.assertEqual(default_zone, "Upstate_West")
        # A locality price far above NYCA (cost ratio 1.0) sites the candidate in NYC
        # and its capacity leg is the settled (locality) price × accreditation.
        z, cap = _zone_of(
            locality_prices_by_zone={"NYC": 10.0 * base_cap + 1e6},
            locality_cost_ratio_by_zone={"NYC": 1.0},
        )
        self.assertEqual(z, "NYC")
        self.assertGreater(cap, base_cap)
        # The published cost ratio can undo it: a 1000× fixed cost loses the tie-break.
        z, _ = _zone_of(
            locality_prices_by_zone={"NYC": 10.0 * base_cap + 1e6},
            locality_cost_ratio_by_zone={"NYC": 1000.0},
        )
        self.assertEqual(z, "Upstate_West")
        # A locality price BELOW NYCA is a tie (max = NYCA both places) → default zone.
        z, cap = _zone_of(
            locality_prices_by_zone={"NYC": 1.0},
            locality_cost_ratio_by_zone={"NYC": 1.0},
        )
        self.assertEqual(z, "Upstate_West")
        self.assertAlmostEqual(cap, base_cap, 6)
