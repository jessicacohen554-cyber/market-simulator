"""Tests for the dispatch variable layout and cost-vector assembly."""

import time
import unittest

import highspy
import numpy as np
import scipy.sparse as sp

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import (
    VariableLayout,
    _build_zone_gen_map,
    build_constraints,
    build_cost_vector,
    build_variable_bounds,
    solve_dispatch,
)
from market_sim.model.storage import StorageUnit, storage_units_to_arrays
from market_sim.model.transmission import build_incidence_matrix, get_ttc_array


def _make_fleet(zones_of_gens, zone_names, hours, pmax=100.0, pmin=10.0, eford=0.05):
    """Build ``FleetArrays`` with one generator per entry of ``zones_of_gens``."""
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=pmin,
            eford=eford,
        )
        for i, z in enumerate(zones_of_gens)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=hours)


class TestVariableLayout(unittest.TestCase):
    """Tests for column-index bookkeeping in ``VariableLayout``."""

    def test_total_columns_minimal(self):
        # 2 thermal gens, 1 zone, no storage, no links.
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=24)
        # vars_per_hour = 2 + 4*1 + 3*0 + 0 = 6
        self.assertEqual(layout.vars_per_hour, 6)
        self.assertEqual(layout.total_columns, 6 * 24)

    def test_vars_per_hour_with_storage_and_links(self):
        layout = VariableLayout(n_gen=3, n_zones=2, n_storage=4, n_links=2, T=10)
        # 3 + 4*2 + 3*4 + 2 = 25
        self.assertEqual(layout.vars_per_hour, 25)
        self.assertEqual(layout.total_columns, 25 * 10)

    def test_block_offsets_are_ordered_and_contiguous(self):
        layout = VariableLayout(n_gen=3, n_zones=2, n_storage=4, n_links=2, T=10)
        self.assertEqual(layout._p_off, 0)
        self.assertEqual(layout._w_off, 3)
        self.assertEqual(layout._s_off, 5)
        self.assertEqual(layout._chg_off, 7)
        self.assertEqual(layout._dis_off, 11)
        self.assertEqual(layout._soc_off, 15)
        self.assertEqual(layout._flow_off, 19)
        self.assertEqual(layout._slack_off, 21)
        self.assertEqual(layout._dump_off, 23)

    def test_columns_unique_within_an_hour(self):
        layout = VariableLayout(n_gen=2, n_zones=2, n_storage=1, n_links=1, T=5)
        # t=2 -- arbitrary interior hour.
        cols = []
        for g in range(2):  # g: thermal generator index
            cols.append(layout.p_col(g, 2))
        for z in range(2):  # z: zone index
            cols.append(layout.w_col(z, 2))
            cols.append(layout.s_col(z, 2))
            cols.append(layout.slack_col(z, 2))
            cols.append(layout.dump_col(z, 2))
        for s in range(1):  # s: storage unit index
            cols.append(layout.chg_col(s, 2))
            cols.append(layout.dis_col(s, 2))
            cols.append(layout.soc_col(s, 2))
        cols.append(layout.flow_col(0, 2))  # transmission link 0
        self.assertEqual(len(cols), len(set(cols)))
        self.assertEqual(len(cols), layout.vars_per_hour)

    def test_columns_advance_by_vars_per_hour(self):
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=8)
        self.assertEqual(
            layout.p_col(1, 3) - layout.p_col(1, 2), layout.vars_per_hour
        )

    def test_p_cols_gen_selects_all_hours(self):
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=6)
        sl = layout.p_cols_gen(1)  # g=1: second thermal generator
        selected = np.arange(layout.total_columns)[sl]
        expected = [layout.p_col(1, t) for t in range(layout.T)]
        np.testing.assert_array_equal(selected, expected)


class TestBuildCostVector(unittest.TestCase):
    """Tests for ``build_cost_vector`` objective assembly."""

    def setUp(self):
        self.layout = VariableLayout(
            n_gen=2, n_zones=1, n_storage=1, n_links=0, T=4
        )
        self.mc = np.array(
            [[10.0, 11.0, 12.0, 13.0], [20.0, 21.0, 22.0, 23.0]]
        )
        self.voll = 9000.0
        self.cost = build_cost_vector(
            self.layout, self.mc, self.voll, storage_epsilon=0.001
        )

    def test_length(self):
        self.assertEqual(len(self.cost), self.layout.total_columns)

    def test_thermal_costs_in_correct_positions(self):
        for g in range(2):  # g: thermal generator index
            for t in range(self.layout.T):  # t: hour index
                self.assertEqual(
                    self.cost[self.layout.p_col(g, t)], self.mc[g, t]
                )

    def test_renewables_are_zero_cost(self):
        for t in range(self.layout.T):  # t: hour index
            self.assertEqual(self.cost[self.layout.w_col(0, t)], 0.0)
            self.assertEqual(self.cost[self.layout.s_col(0, t)], 0.0)

    def test_storage_charge_discharge_carry_epsilon(self):
        for t in range(self.layout.T):  # t: hour index
            self.assertEqual(self.cost[self.layout.chg_col(0, t)], 0.001)
            self.assertEqual(self.cost[self.layout.dis_col(0, t)], 0.001)

    def test_soc_is_zero_cost(self):
        for t in range(self.layout.T):  # t: hour index
            self.assertEqual(self.cost[self.layout.soc_col(0, t)], 0.0)

    def test_slack_equals_voll(self):
        for t in range(self.layout.T):  # t: hour index
            self.assertEqual(self.cost[self.layout.slack_col(0, t)], self.voll)

    def test_round_trip_cost_matches_mc(self):
        for g in range(2):  # g: thermal generator index
            for t in range(self.layout.T):  # t: hour index
                self.assertEqual(
                    self.cost[self.layout.p_col(g, t)], self.mc[g, t]
                )

    def test_flow_is_zero_cost(self):
        layout = VariableLayout(
            n_gen=1, n_zones=1, n_storage=0, n_links=2, T=3
        )
        mc = np.full((1, 3), 5.0)
        cost = build_cost_vector(layout, mc, voll=1000.0)
        for ln in range(2):  # ln: transmission link index
            for t in range(layout.T):  # t: hour index
                self.assertEqual(cost[layout.flow_col(ln, t)], 0.0)


class TestBuildZoneGenMap(unittest.TestCase):
    """Tests for the sparse zone-membership matrix."""

    def test_membership_entries(self):
        fleet = _make_fleet(["Z0", "Z1", "Z1"], ["Z0", "Z1"], hours=4)
        zone_gen = _build_zone_gen_map(fleet, n_zones=2)
        self.assertEqual(zone_gen.shape, (2, 3))
        np.testing.assert_array_equal(
            zone_gen.toarray(), [[1.0, 0.0, 0.0], [0.0, 1.0, 1.0]]
        )


class TestBuildConstraints(unittest.TestCase):
    """Tests for energy-balance and storage-SOC constraint assembly."""

    def test_energy_balance_only_shape(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=24)
        fleet = _make_fleet(["Z0"], ["Z0"], hours=24)
        demand = np.arange(24, dtype=float).reshape(1, 24)
        A, row_lower, row_upper = build_constraints(layout, fleet, demand)
        # vars_per_hour = 1 + 4*1 + 3*0 + 0 = 5.
        self.assertEqual(layout.vars_per_hour, 5)
        self.assertEqual(A.shape, (24, 24 * layout.vars_per_hour))
        self.assertEqual(A.format, "csr")

    def test_energy_balance_row_entries(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=24)
        fleet = _make_fleet(["Z0"], ["Z0"], hours=24)
        demand = np.zeros((1, 24))
        A, _, _ = build_constraints(layout, fleet, demand)
        dense = A.toarray()
        for t in range(layout.T):  # t: hour index
            self.assertEqual(dense[t, layout.p_col(0, t)], 1.0)
            self.assertEqual(dense[t, layout.w_col(0, t)], 1.0)
            self.assertEqual(dense[t, layout.s_col(0, t)], 1.0)
            self.assertEqual(dense[t, layout.slack_col(0, t)], 1.0)
            self.assertEqual(dense[t, layout.dump_col(0, t)], -1.0)
            # The balance row touches exactly those five columns.
            self.assertEqual(int((dense[t] != 0).sum()), 5)

    def test_multizone_balance_places_gens_in_their_zone(self):
        layout = VariableLayout(n_gen=2, n_zones=2, n_storage=0, n_links=0, T=3)
        fleet = _make_fleet(["Z0", "Z1"], ["Z0", "Z1"], hours=3)
        demand = np.zeros((2, 3))
        A, _, _ = build_constraints(layout, fleet, demand)
        dense = A.toarray()
        for t in range(layout.T):  # t: hour index
            # Row for zone 0 holds gen 0; row for zone 1 holds gen 1.
            self.assertEqual(dense[t * 2 + 0, layout.p_col(0, t)], 1.0)
            self.assertEqual(dense[t * 2 + 0, layout.p_col(1, t)], 0.0)
            self.assertEqual(dense[t * 2 + 1, layout.p_col(1, t)], 1.0)
            self.assertEqual(dense[t * 2 + 1, layout.p_col(0, t)], 0.0)

    def test_demand_appears_in_row_bounds(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=24)
        fleet = _make_fleet(["Z0"], ["Z0"], hours=24)
        demand = np.arange(100.0, 124.0).reshape(1, 24)
        _, row_lower, row_upper = build_constraints(layout, fleet, demand)
        # Equality rows: lower == upper == demand, in hour order.
        np.testing.assert_array_equal(row_lower, demand.ravel())
        np.testing.assert_array_equal(row_upper, demand.ravel())

    def test_storage_soc_rows_link_adjacent_hours(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=1, n_links=0, T=4)
        fleet = _make_fleet(["Z0"], ["Z0"], hours=4)
        demand = np.array([[10.0, 20.0, 30.0, 40.0]])
        A, row_lower, row_upper = build_constraints(
            layout, fleet, demand, storage_zone_idx=[0], eta_chg=0.9, eta_dis=0.8
        )
        # 4 energy-balance rows + 4 SOC rows (one per hour).
        self.assertEqual(A.shape, (8, layout.total_columns))
        dense = A.toarray()

        # Dynamics row for hour 2 sits at global row 4 + 2.
        r = 4 + 2
        self.assertEqual(dense[r, layout.soc_col(0, 2)], 1.0)
        self.assertEqual(dense[r, layout.soc_col(0, 1)], -1.0)
        self.assertEqual(dense[r, layout.chg_col(0, 2)], -0.9)
        self.assertAlmostEqual(dense[r, layout.dis_col(0, 2)], 1.0 / 0.8)

        # Hour-0 row is a full dynamics row that wraps around from hour T-1,
        # so it also carries hour 0's own charge and discharge terms.
        self.assertEqual(dense[4, layout.soc_col(0, 0)], 1.0)
        self.assertEqual(dense[4, layout.soc_col(0, 3)], -1.0)
        self.assertEqual(dense[4, layout.chg_col(0, 0)], -0.9)
        self.assertAlmostEqual(dense[4, layout.dis_col(0, 0)], 1.0 / 0.8)

        # SOC rows are equalities with a zero RHS.
        np.testing.assert_array_equal(row_lower[4:8], np.zeros(4))
        np.testing.assert_array_equal(row_upper[4:8], np.zeros(4))

    def test_incidence_enters_flow_columns(self):
        layout = VariableLayout(n_gen=1, n_zones=2, n_storage=0, n_links=1, T=2)
        fleet = _make_fleet(["Z0"], ["Z0", "Z1"], hours=2)
        demand = np.zeros((2, 2))
        incidence = np.array([[1.0], [-1.0]])  # link injects to Z0, withdraws Z1
        A, _, _ = build_constraints(layout, fleet, demand, incidence=incidence)
        dense = A.toarray()
        for t in range(layout.T):  # t: hour index
            self.assertEqual(dense[t * 2 + 0, layout.flow_col(0, t)], 1.0)
            self.assertEqual(dense[t * 2 + 1, layout.flow_col(0, t)], -1.0)


class TestBuildVariableBounds(unittest.TestCase):
    """Tests for decision-variable bound assembly."""

    def test_generator_upper_is_pmax_times_availability(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=24)
        fleet = _make_fleet(["Z0"], ["Z0"], hours=24, pmax=100.0, pmin=10.0, eford=0.05)
        col_lower, col_upper = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.full((1, 24), 0.3),
            wind_cap=np.array([200.0]),
            solar_cf=np.full((1, 24), 0.2),
            solar_cap=np.array([150.0]),
        )
        for t in range(layout.T):  # t: hour index
            self.assertAlmostEqual(col_upper[layout.p_col(0, t)], 100.0 * 0.95)
            self.assertEqual(col_lower[layout.p_col(0, t)], 10.0)

    def test_wind_and_solar_upper_are_cf_times_cap(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=24)
        fleet = _make_fleet(["Z0"], ["Z0"], hours=24)
        col_lower, col_upper = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.full((1, 24), 0.3),
            wind_cap=np.array([200.0]),
            solar_cf=np.full((1, 24), 0.2),
            solar_cap=np.array([150.0]),
        )
        for t in range(layout.T):  # t: hour index
            self.assertAlmostEqual(col_upper[layout.w_col(0, t)], 0.3 * 200.0)
            self.assertEqual(col_lower[layout.w_col(0, t)], 0.0)
            self.assertAlmostEqual(col_upper[layout.s_col(0, t)], 0.2 * 150.0)
            self.assertEqual(col_lower[layout.s_col(0, t)], 0.0)

    def test_storage_and_flow_and_slack_bounds(self):
        layout = VariableLayout(n_gen=1, n_zones=2, n_storage=1, n_links=1, T=5)
        fleet = _make_fleet(["Z0"], ["Z0", "Z1"], hours=5)
        col_lower, col_upper = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.full((2, 5), 0.4),
            wind_cap=np.array([10.0, 20.0]),
            solar_cf=np.full((2, 5), 0.1),
            solar_cap=np.array([30.0, 40.0]),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            ttc=np.array([300.0]),
        )
        for t in range(layout.T):  # t: hour index
            self.assertEqual(col_upper[layout.chg_col(0, t)], 50.0)
            self.assertEqual(col_upper[layout.dis_col(0, t)], 50.0)
            self.assertEqual(col_lower[layout.chg_col(0, t)], 0.0)
            self.assertEqual(col_upper[layout.soc_col(0, t)], 200.0)
            self.assertEqual(col_lower[layout.flow_col(0, t)], -300.0)
            self.assertEqual(col_upper[layout.flow_col(0, t)], 300.0)
            for z in range(2):  # z: zone index
                self.assertEqual(col_lower[layout.slack_col(z, t)], 0.0)
                self.assertTrue(np.isinf(col_upper[layout.slack_col(z, t)]))


class TestSolveDispatch(unittest.TestCase):
    """End-to-end tests for ``solve_dispatch`` (all use T=24)."""

    T = 24

    def _no_renewables(self, n_zones):
        """Return zero-capacity wind/solar kwargs for ``n_zones`` zones."""
        return dict(
            wind_cf=np.zeros((n_zones, self.T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, self.T)),
            solar_cap=np.zeros(n_zones),
        )

    def test_single_marginal_generator_sets_price(self):
        # 1 gen, MC=50, pmax=100; flat demand 80 -> price 50, dispatch 80.
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0)
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, **self._no_renewables(1)
        )
        np.testing.assert_allclose(result.prices, 50.0)
        np.testing.assert_allclose(result.dispatch, 80.0)

    def test_cheap_generator_sets_price_below_capacity(self):
        # 2 gens (MC=30/pmax=50, MC=60/pmax=50); demand 40 -> price 30.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=50.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 30.0), np.full(self.T, 60.0)])
        demand = np.full((1, self.T), 40.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, **self._no_renewables(1)
        )
        np.testing.assert_allclose(result.prices, 30.0)

    def test_expensive_generator_sets_price_at_the_margin(self):
        # Demand 70 -> cheap gen full at 50, expensive at 20, price 60.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=50.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 30.0), np.full(self.T, 60.0)])
        demand = np.full((1, self.T), 70.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, **self._no_renewables(1)
        )
        np.testing.assert_allclose(result.prices, 60.0)
        np.testing.assert_allclose(result.dispatch[0], 50.0)
        np.testing.assert_allclose(result.dispatch[1], 20.0)

    def test_unserved_load_prices_at_voll(self):
        # Demand 200 exceeds the 100 MW fleet -> slack > 0, price = VOLL.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=50.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 30.0), np.full(self.T, 60.0)])
        demand = np.full((1, self.T), 200.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, voll=5000.0, T=self.T, **self._no_renewables(1)
        )
        self.assertTrue(np.all(result.slack > 0.0))
        np.testing.assert_allclose(result.prices, 5000.0)

    def test_energy_balance_holds_every_hour(self):
        # Generation + wind + solar + slack must equal demand each hour.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=50.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 30.0), np.full(self.T, 60.0)])
        demand = np.full((1, self.T), 75.0)
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            wind_cf=np.full((1, self.T), 0.5),
            wind_cap=np.array([20.0]),
            solar_cf=np.full((1, self.T), 0.3),
            solar_cap=np.array([10.0]),
        )
        supply = (
            result.dispatch.sum(axis=0)
            + result.wind_dispatched[0]
            + result.solar_dispatched[0]
            + result.slack[0]
        )
        np.testing.assert_allclose(supply, demand[0])


class TestDispatchPerformance(unittest.TestCase):
    """Full-scale (8760-hour) timing and energy-balance checks."""

    def test_full_year_200_generator_fleet(self):
        T = HOURS_PER_YEAR  # 8760 hours
        n_gen = 200
        pmax = 100.0  # MW per unit
        total_cap = n_gen * pmax  # 20_000 MW installed thermal capacity

        # 1 zone, no storage, no transmission -- the simplest full-scale case.
        fleet = _make_fleet(
            ["Z0"] * n_gen, ["Z0"], hours=T, pmax=pmax, pmin=0.0, eford=0.0
        )

        # Marginal costs spanning 20-80 $/MWh, flat across the year.
        mc = np.tile(np.linspace(20.0, 80.0, n_gen)[:, np.newaxis], (1, T))

        # Sinusoidal demand peaking at 80% of total installed capacity.
        peak = 0.8 * total_cap  # 16_000 MW
        hours = np.arange(T)
        demand = (0.7 * peak + 0.3 * peak * np.sin(2 * np.pi * hours / T))
        demand = demand.reshape(1, T)

        # Flat wind; solar follows a daily bell curve (0 at night, 0.6 midday).
        wind_cf = np.full((1, T), 0.35)
        hour_of_day = hours % 24
        solar_shape = np.clip(np.sin(np.pi * (hour_of_day - 6) / 12), 0.0, None)
        solar_cf = (0.6 * solar_shape).reshape(1, T)

        wind_cap = np.array([0.10 * total_cap])  # 10% of thermal capacity
        solar_cap = np.array([0.10 * total_cap])

        result = solve_dispatch(
            fleet,
            demand,
            wind_cf=wind_cf,
            wind_cap=wind_cap,
            solar_cf=solar_cf,
            solar_cap=solar_cap,
            mc=mc,
            T=T,
        )

        print(
            f"\n[dispatch perf] 200 gens x {T} hours -- "
            f"build: {result.build_time:.3f}s, solve: {result.solve_time:.3f}s"
        )

        # Energy balance must hold in every one of the 8760 hours.
        supply = (
            result.dispatch.sum(axis=0)
            + result.wind_dispatched[0]
            + result.solar_dispatched[0]
            + result.slack[0]
        )
        self.assertTrue(np.allclose(supply, demand[0]))

        self.assertLess(result.build_time, 3.0)
        self.assertLess(result.solve_time, 15.0)


class TestNegativePricing(unittest.TestCase):
    """Tests that production credits drive prices below zero."""

    T = 24

    def test_ptc_wind_creates_negative_prices(self):
        """Wind with PTC at -26 $/MWh sets price negative when at margin."""
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0)
        mc = np.full((1, self.T), 50.0)  # thermal at $50
        demand = np.full((1, self.T), 80.0)
        # Wind capacity exceeds demand — wind is marginal
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T,
            wind_cf=np.full((1, self.T), 1.0),
            wind_cap=np.array([200.0]),  # 200 MW available, only 80 needed
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
            wind_mc=-26.0,  # PTC
        )
        # Wind is marginal and has MC=-26, so price should be -26
        np.testing.assert_allclose(result.prices, -26.0, atol=0.1)
        # Thermal gen should be off (wind is cheaper)
        np.testing.assert_allclose(result.dispatch, 0.0, atol=0.1)

    def test_zero_mc_wind_without_ptc(self):
        """Without PTC, wind at margin gives price=0 (backward compatible)."""
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0)
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T,
            wind_cf=np.full((1, self.T), 1.0),
            wind_cap=np.array([200.0]),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
            # wind_mc defaults to 0.0 — no PTC
        )
        np.testing.assert_allclose(result.prices, 0.0, atol=0.1)

    def test_ptc_expired_no_negative_prices(self):
        """After IRA expiry, wind reverts to MC=0."""
        from market_sim.policy.ira import compute_dispatch_credits
        from market_sim.config.scenarios import ScenarioConfig
        config = ScenarioConfig(ira_ptc_wind=26.0, ira_wind_solar_last_year=2035)
        w_mc, s_mc = compute_dispatch_credits(config, year=2036)
        self.assertEqual(w_mc, 0.0)
        self.assertEqual(s_mc, 0.0)
        w_mc, s_mc = compute_dispatch_credits(config, year=2030)
        self.assertEqual(w_mc, -26.0)

    def test_wind_solar_cliff_2027(self):
        """Wind/solar dispatch credits vanish after the OBBBA 2027 cliff."""
        from market_sim.policy.ira import compute_dispatch_credits
        from market_sim.config.scenarios import ScenarioConfig
        config = ScenarioConfig()
        w_mc, _ = compute_dispatch_credits(config, 2027)
        self.assertEqual(w_mc, -26.0)
        w_mc, _ = compute_dispatch_credits(config, 2028)
        self.assertEqual(w_mc, 0.0)


class TestOvergeneration(unittest.TestCase):
    """Tests that must-run overgeneration is absorbed by the dump variable."""

    T = 24

    def test_must_run_exceeds_demand_uses_dump(self):
        """Nuclear pmin=800 MW, demand=500 MW — dump absorbs 300 MW."""
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T,
                            pmax=1000.0, pmin=800.0, eford=0.0)
        mc = np.full((1, self.T), 5.0)
        demand = np.full((1, self.T), 500.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T,
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1))
        self.assertEqual(result.status, "Optimal")
        np.testing.assert_allclose(result.dispatch[0], 800.0, atol=1.0)
        np.testing.assert_allclose(result.dump[0], 300.0, atol=1.0)
        self.assertTrue(np.all(result.prices < 0))

    def test_no_dump_when_balanced(self):
        """Normal operation: dump is zero."""
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T,
                            pmax=200.0, pmin=0.0, eford=0.0)
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T,
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1))
        np.testing.assert_allclose(result.dump, 0.0, atol=1e-6)

    def test_energy_balance_with_dump(self):
        """Supply - dump + slack = demand for every hour."""
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T,
                            pmax=1000.0, pmin=800.0, eford=0.0)
        mc = np.full((1, self.T), 5.0)
        demand = np.full((1, self.T), 500.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T,
            wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)), solar_cap=np.zeros(1))
        supply = result.dispatch.sum(axis=0) + result.slack[0] - result.dump[0]
        np.testing.assert_allclose(supply, demand[0], atol=1e-4)


class TestRPSConstraint(unittest.TestCase):
    """The annual RPS constraint row and its REC-price dual."""

    T = 24

    def _no_renewables(self, n_zones):
        """Return zero-capacity wind/solar kwargs for ``n_zones`` zones."""
        return dict(
            wind_cf=np.zeros((n_zones, self.T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, self.T)),
            solar_cap=np.zeros(n_zones),
        )

    def _nuclear_gas_fleet(self):
        """A two-unit fleet: one nuclear unit, one gas unit, both in Z0."""
        generators = [
            Generator(
                unit_id="N0", name="N0", zone="Z0", fuel_type="nuclear",
                pmax_mw=100.0, pmin_mw=0.0, eford=0.0,
            ),
            Generator(
                unit_id="G0", name="G0", zone="Z0", fuel_type="gas_cc",
                pmax_mw=100.0, pmin_mw=0.0, eford=0.0,
            ),
        ]
        return generators_to_fleet_arrays(generators, ["Z0"], hours=self.T)

    def test_rps_none_matches_unconstrained_dispatch(self):
        # rps_target=None adds no constraint row: the solve is identical to
        # one that never mentions an RPS, and rps_shadow_price stays None.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)

        baseline = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, **self._no_renewables(1)
        )
        with_none = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, rps_target=None,
            **self._no_renewables(1),
        )
        np.testing.assert_allclose(with_none.prices, baseline.prices)
        np.testing.assert_allclose(with_none.dispatch, baseline.dispatch)
        self.assertIsNone(baseline.rps_shadow_price)
        self.assertIsNone(with_none.rps_shadow_price)

    def test_rps_binds_with_thermal_only_fleet(self):
        # A nuclear + gas fleet with cheap gas and expensive nuclear: the
        # RPS forces expensive nuclear up to cover half of demand, so the
        # constraint binds and its dual (the RPS shadow price) is positive.
        fleet = self._nuclear_gas_fleet()
        # Row 0 is nuclear (expensive), row 1 is gas (cheap).
        mc = np.vstack(
            [np.full(self.T, 100.0), np.full(self.T, 20.0)]
        )
        demand = np.full((1, self.T), 80.0)

        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, rps_target=0.5,
            **self._no_renewables(1),
        )
        self.assertEqual(result.status, "Optimal")
        self.assertIsNotNone(result.rps_shadow_price)
        self.assertGreater(result.rps_shadow_price, 0.0)
        # The RPS shadow price equals the cost premium of nuclear over gas:
        # an extra MWh of clean swaps 1 MWh gas (20) for nuclear (100).
        self.assertAlmostEqual(result.rps_shadow_price, 80.0, delta=0.5)
        # Nuclear is pushed up to supply at least half of total demand.
        self.assertGreaterEqual(
            result.dispatch[0].sum(), 0.5 * demand.sum() - 1.0
        )

    def test_rps_non_binding_with_enough_wind(self):
        # Cheap wind already supplies more than the RPS floor, so the
        # constraint is slack and its dual is zero.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)

        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, rps_target=0.5,
            wind_cf=np.full((1, self.T), 0.5),
            wind_cap=np.array([100.0]),  # 50 MW available vs 80 MW demand
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        self.assertEqual(result.status, "Optimal")
        self.assertIsNotNone(result.rps_shadow_price)
        # Wind covers 62.5% of demand, comfortably above the 50% floor.
        self.assertAlmostEqual(result.rps_shadow_price, 0.0, places=3)

    def test_rps_infeasible_with_no_clean_capacity(self):
        # A gas-only fleet can produce no clean energy at all, so a 100%
        # RPS has no feasible solution and the solve raises.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)

        with self.assertRaises(RuntimeError):
            solve_dispatch(
                fleet, demand, mc=mc, T=self.T, rps_target=1.0,
                **self._no_renewables(1),
            )


def _solve_with_highs_options(
    highs_options,
    *,
    fleet,
    demand,
    wind_cf,
    wind_cap,
    solar_cf,
    solar_cap,
    mc,
    T,
    voll=5000.0,
    incidence=None,
    ttc=None,
    storage_power_cap=None,
    storage_energy_cap=None,
    storage_zone_idx=None,
    eta_chg=None,
    eta_dis=None,
):
    """Build and solve the dispatch LP inline, applying extra HiGHS options.

    This duplicates the HiGHS setup/solve portion of ``solve_dispatch`` so the
    benchmark can vary solver options without changing the production API.
    ``highs_options`` is a dict of option name -> value applied *after* the
    standard options (``output_flag`` off, ``presolve`` off).

    Returns ``(build_time, solve_time, objective_value)``.
    """
    build_start = time.perf_counter()

    demand = np.asarray(demand, dtype=float)
    n_zones = demand.shape[0]
    n_gen = fleet.n_gen
    n_storage = 0 if storage_power_cap is None else len(storage_power_cap)
    n_links = 0 if incidence is None else sp.csr_matrix(incidence).shape[1]

    layout = VariableLayout(
        n_gen=n_gen, n_zones=n_zones, n_storage=n_storage, n_links=n_links, T=T
    )

    cost = build_cost_vector(layout, np.asarray(mc, dtype=float), voll)
    A, row_lower, row_upper = build_constraints(
        layout,
        fleet,
        demand,
        incidence=incidence,
        storage_zone_idx=storage_zone_idx,
        eta_chg=eta_chg,
        eta_dis=eta_dis,
    )
    col_lower, col_upper = build_variable_bounds(
        layout,
        fleet,
        wind_cf,
        wind_cap,
        solar_cf,
        solar_cap,
        storage_power_cap=storage_power_cap,
        storage_energy_cap=storage_energy_cap,
        ttc=ttc,
    )

    starts = A.indptr[:-1].astype(np.int32)
    indices = A.indices.astype(np.int32)
    values = A.data.astype(np.float64)

    inf = highspy.kHighsInf
    col_upper = np.where(np.isinf(col_upper), inf, col_upper)
    col_lower = np.where(np.isinf(col_lower), -inf, col_lower)
    row_upper = np.where(np.isinf(row_upper), inf, row_upper)
    row_lower = np.where(np.isinf(row_lower), -inf, row_lower)

    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    # Match the production default: presolve adds pure overhead on these LPs.
    h.setOptionValue("presolve", "off")
    for key, val in highs_options.items():
        h.setOptionValue(key, val)
    h.addCols(
        layout.total_columns,
        cost,
        col_lower,
        col_upper,
        0,
        np.zeros(layout.total_columns, dtype=np.int32),
        np.array([], dtype=np.int32),
        np.array([], dtype=np.float64),
    )
    h.addRows(
        A.shape[0], row_lower, row_upper, A.nnz, starts, indices, values
    )
    build_time = time.perf_counter() - build_start

    solve_start = time.perf_counter()
    h.run()
    solve_time = time.perf_counter() - solve_start

    _, primal_status = h.getInfoValue("primal_solution_status")
    if primal_status != 2:
        status = h.modelStatusToString(h.getModelStatus())
        raise RuntimeError(f"benchmark LP infeasible (status: {status})")

    return build_time, solve_time, float(h.getObjectiveValue())


def _make_200gen_1zone_problem():
    """200-gen, 1-zone, 8760h problem from ``test_full_year_200_generator_fleet``."""
    T = HOURS_PER_YEAR  # 8760 hours
    n_gen = 200
    pmax = 100.0
    total_cap = n_gen * pmax

    fleet = _make_fleet(
        ["Z0"] * n_gen, ["Z0"], hours=T, pmax=pmax, pmin=0.0, eford=0.0
    )
    mc = np.tile(np.linspace(20.0, 80.0, n_gen)[:, np.newaxis], (1, T))

    peak = 0.8 * total_cap
    hours = np.arange(T)
    demand = (0.7 * peak + 0.3 * peak * np.sin(2 * np.pi * hours / T)).reshape(
        1, T
    )

    wind_cf = np.full((1, T), 0.35)
    hour_of_day = hours % 24
    solar_shape = np.clip(np.sin(np.pi * (hour_of_day - 6) / 12), 0.0, None)
    solar_cf = (0.6 * solar_shape).reshape(1, T)
    wind_cap = np.array([0.10 * total_cap])
    solar_cap = np.array([0.10 * total_cap])

    return dict(
        fleet=fleet,
        demand=demand,
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        mc=mc,
        T=T,
    )


def _make_4zone_storage_problem():
    """4-zone + storage + transmission 8760h problem from the integration suite.

    Mirrors ``test_integration.TestFullYearPerformance.test_full_year``.
    """
    T = 8760
    iso = get_iso_config("ERCOT")
    zone_names = iso.zone_names

    zones_cycle = zone_names * 50
    gens = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=zones_cycle[i],
            fuel_type="gas_cc",
            pmax_mw=100.0,
            pmin_mw=0.0,
            heat_rate=0.0,
            vom=15 + 75 * i / 200,
            eford=0.0,
        )
        for i in range(200)
    ]
    fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
    mc = np.array([[g.vom] * T for g in gens], dtype=float)

    eta = 0.85**0.5
    units = [
        StorageUnit(
            unit_id=f"STO{i}",
            zone=zone_names[i % 4],
            tech_name="li_ion_4hr",
            power_cap_mw=100.0,
            energy_cap_mwh=400.0,
            eta_charge=eta,
            eta_discharge=eta,
        )
        for i in range(5)
    ]
    sa = storage_units_to_arrays(units, zone_names)

    incidence = build_incidence_matrix(iso.links, zone_names)
    ttc = get_ttc_array(iso.links)

    hours = np.arange(T)
    hod = hours % 24
    daily = 0.6 + 0.4 * np.sin(np.pi * (hod - 6) / 12)
    total = 12000 * daily
    demand = np.array([z.load_share for z in iso.zones])[:, None] * total[None, :]

    wind_cf = np.zeros((4, T))
    wind_cf[2] = 0.35
    wind_cap = np.array([0, 0, 2000, 0])

    solar_cf = np.zeros((4, T))
    solar_cf[1] = np.clip(0.6 * np.sin(np.pi * (hod - 6) / 12), 0, 1)
    solar_cap = np.array([0, 1500, 0, 0])

    return dict(
        fleet=fleet,
        demand=demand,
        wind_cf=wind_cf,
        wind_cap=wind_cap,
        solar_cf=solar_cf,
        solar_cap=solar_cap,
        mc=mc,
        T=T,
        incidence=incidence,
        ttc=ttc,
        storage_power_cap=sa.power_cap,
        storage_energy_cap=sa.energy_cap,
        storage_zone_idx=sa.zone_idx,
        eta_chg=sa.eta_chg,
        eta_dis=sa.eta_dis,
    )


class TestSolverBenchmark(unittest.TestCase):
    """Benchmarks HiGHS solver configurations on the full-year dispatch LP.

    This is a benchmark only -- ``dispatch.py`` is intentionally left
    unchanged. The test compares three HiGHS configurations (all keep the
    production ``presolve=off`` setting):

      * ``default``  -- current production setup, no solver method set
      * ``ipm``      -- interior-point method (``solver=ipm``)
      * ``parallel`` -- simplex with parallelism (``parallel=on``)

    on both the simple 200-gen/1-zone model and the more complex
    4-zone + storage + transmission model.

    FOLLOW-UP: no single configuration wins across both models, so
    ``dispatch.py`` should be left on the ``default`` dual simplex. Measured
    on this machine:

      * 1-zone model:  parallel ~4.3s < ipm ~5.3s < default ~5.9s
      * 4-zone model:  default ~17.2s < parallel ~20.7s < ipm ~23.0s

    ``parallel=on`` is fastest on the simple 1-zone LP but ~20% slower than
    the default on the 4-zone storage/transmission model, where the SOC
    dynamics rows make the dual simplex's warm-started pivoting pay off.
    ``ipm`` is never the fastest. Since the production model is the complex
    multi-zone one, the current ``default`` remains the right choice -- no
    change to ``dispatch.py`` is warranted from this benchmark.
    """

    # Solver methods are at most this much slower/different in objective.
    OBJECTIVE_REL_TOL = 1e-4  # 0.01%

    def _run_benchmark(self, problem):
        configs = {
            "default": {},
            "ipm": {"solver": "ipm"},
            "parallel": {"parallel": "on"},
        }
        results = {}
        for name, opts in configs.items():
            results[name] = _solve_with_highs_options(opts, **problem)

        ref_obj = results["default"][2]
        for name, (build_time, solve_time, obj) in results.items():
            print(
                f"[solver bench] {name + ':':<10}"
                f" build={build_time:.2f}s solve={solve_time:.2f}s"
                f" total={build_time + solve_time:.2f}s obj={obj:.0f}"
            )

        # Every solver method must reach the same optimum within 0.01%.
        for name, (_, _, obj) in results.items():
            self.assertAlmostEqual(
                obj,
                ref_obj,
                delta=abs(ref_obj) * self.OBJECTIVE_REL_TOL,
                msg=f"{name} objective diverged from default",
            )

    def test_solver_method_benchmark(self):
        print(
            "\n[solver bench] 200 gens x 8760h -- 1 zone, no storage/transmission"
        )
        self._run_benchmark(_make_200gen_1zone_problem())

        print(
            "[solver bench] 200 gens x 8760h -- 4 zones + storage + transmission"
        )
        self._run_benchmark(_make_4zone_storage_problem())


if __name__ == "__main__":
    unittest.main()
