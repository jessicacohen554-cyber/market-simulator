"""Tests for the dispatch variable layout and cost-vector assembly."""

import time
import unittest

import highspy
import numpy as np
import pytest
import scipy.sparse as sp

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import TransferLink, get_iso_config
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

    def test_reserve_coopt_columns_off_by_default(self):
        """n_reserve/n_ordc_steps default to 0 -> byte-identical layout."""
        base = VariableLayout(n_gen=3, n_zones=2, n_storage=4, n_links=2, T=10)
        coopt0 = VariableLayout(
            n_gen=3,
            n_zones=2,
            n_storage=4,
            n_links=2,
            T=10,
            n_reserve=0,
            n_ordc_steps=0,
        )
        self.assertEqual(base.vars_per_hour, coopt0.vars_per_hour)
        self.assertEqual(base.total_columns, coopt0.total_columns)
        self.assertEqual(base._dump_off, coopt0._dump_off)

    def test_reserve_coopt_columns_when_enabled(self):
        """Reserve/ORDC blocks append after dump; indices stay unique."""
        layout = VariableLayout(
            n_gen=3,
            n_zones=2,
            n_storage=1,
            n_links=1,
            T=5,
            n_reserve=3,
            n_ordc_steps=2,
        )
        # vars_per_hour = 3 + 4*2 + 3*1 + 1 + 3 + 2 = 20
        self.assertEqual(layout.vars_per_hour, 20)
        # Reserve block sits right after the dump block (dump = n_zones wide).
        self.assertEqual(layout._reserve_off, layout._dump_off + layout.n_zones)
        self.assertEqual(layout._ordc_off, layout._reserve_off + 3)
        cols = []
        for g in range(3):
            cols.append(layout.p_col(g, 2))
            cols.append(layout.r_col(g, 2))
        for z in range(2):
            cols += [
                layout.w_col(z, 2),
                layout.s_col(z, 2),
                layout.slack_col(z, 2),
                layout.dump_col(z, 2),
            ]
        for s in range(1):
            cols += [layout.chg_col(s, 2), layout.dis_col(s, 2), layout.soc_col(s, 2)]
        cols.append(layout.flow_col(0, 2))
        for k in range(2):
            cols.append(layout.ordc_col(k, 2))
        self.assertEqual(len(cols), len(set(cols)))
        self.assertEqual(len(cols), layout.vars_per_hour)
        # All within hour t=2's contiguous block.
        lo = 2 * layout.vars_per_hour
        self.assertTrue(all(lo <= c < lo + layout.vars_per_hour for c in cols))

    def test_columns_advance_by_vars_per_hour(self):
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=8)
        self.assertEqual(layout.p_col(1, 3) - layout.p_col(1, 2), layout.vars_per_hour)

    def test_p_cols_gen_selects_all_hours(self):
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=6)
        sl = layout.p_cols_gen(1)  # g=1: second thermal generator
        selected = np.arange(layout.total_columns)[sl]
        expected = [layout.p_col(1, t) for t in range(layout.T)]
        np.testing.assert_array_equal(selected, expected)


class TestBuildCostVector(unittest.TestCase):
    """Tests for ``build_cost_vector`` objective assembly."""

    def setUp(self):
        self.layout = VariableLayout(n_gen=2, n_zones=1, n_storage=1, n_links=0, T=4)
        self.mc = np.array([[10.0, 11.0, 12.0, 13.0], [20.0, 21.0, 22.0, 23.0]])
        self.voll = 9000.0
        self.cost = build_cost_vector(
            self.layout, self.mc, self.voll, storage_epsilon=0.001
        )

    def test_length(self):
        self.assertEqual(len(self.cost), self.layout.total_columns)

    def test_thermal_costs_in_correct_positions(self):
        for g in range(2):  # g: thermal generator index
            for t in range(self.layout.T):  # t: hour index
                self.assertEqual(self.cost[self.layout.p_col(g, t)], self.mc[g, t])

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
                self.assertEqual(self.cost[self.layout.p_col(g, t)], self.mc[g, t])

    def test_flow_is_zero_cost(self):
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=2, T=3)
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

    def test_per_hour_ttc_sets_seasonal_flow_bounds(self):
        # A 2-D ttc (T, n_links) sets a distinct flow limit each hour, so an
        # interface can follow a seasonal envelope (NYISO Central-East monthly
        # TTC) instead of one static value.
        layout = VariableLayout(n_gen=1, n_zones=2, n_storage=0, n_links=1, T=3)
        fleet = _make_fleet(["Z0"], ["Z0", "Z1"], hours=3)
        ttc_per_hour = np.array([[100.0], [250.0], [400.0]])  # (T, n_links)
        col_lower, col_upper = build_variable_bounds(
            layout,
            fleet,
            wind_cf=np.zeros((2, 3)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, 3)),
            solar_cap=np.zeros(2),
            ttc=ttc_per_hour,
        )
        for t, limit in enumerate([100.0, 250.0, 400.0]):  # t: hour index
            self.assertEqual(col_upper[layout.flow_col(0, t)], limit)
            self.assertEqual(col_lower[layout.flow_col(0, t)], -limit)

    def test_one_d_and_two_d_ttc_agree_when_constant(self):
        # A 1-D ttc and a constant 2-D ttc must produce identical bounds — the
        # static path stays byte-identical.
        layout = VariableLayout(n_gen=1, n_zones=2, n_storage=0, n_links=1, T=4)
        fleet = _make_fleet(["Z0"], ["Z0", "Z1"], hours=4)
        kwargs = dict(
            wind_cf=np.zeros((2, 4)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, 4)),
            solar_cap=np.zeros(2),
        )
        lo1, up1 = build_variable_bounds(layout, fleet, ttc=np.array([300.0]), **kwargs)
        lo2, up2 = build_variable_bounds(
            layout, fleet, ttc=np.full((4, 1), 300.0), **kwargs
        )
        np.testing.assert_array_equal(lo1, lo2)
        np.testing.assert_array_equal(up1, up2)


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
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
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
        demand = 0.7 * peak + 0.3 * peak * np.sin(2 * np.pi * hours / T)
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
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)  # thermal at $50
        demand = np.full((1, self.T), 80.0)
        # Wind capacity exceeds demand — wind is marginal
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
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
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
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
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=1000.0, pmin=800.0, eford=0.0
        )
        mc = np.full((1, self.T), 5.0)
        demand = np.full((1, self.T), 500.0)
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        self.assertEqual(result.status, "Optimal")
        np.testing.assert_allclose(result.dispatch[0], 800.0, atol=1.0)
        np.testing.assert_allclose(result.dump[0], 300.0, atol=1.0)
        self.assertTrue(np.all(result.prices < 0))

    def test_no_dump_when_balanced(self):
        """Normal operation: dump is zero."""
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        np.testing.assert_allclose(result.dump, 0.0, atol=1e-6)

    def test_energy_balance_with_dump(self):
        """Supply - dump + slack = demand for every hour."""
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=1000.0, pmin=800.0, eford=0.0
        )
        mc = np.full((1, self.T), 5.0)
        demand = np.full((1, self.T), 500.0)
        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
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
                unit_id="N0",
                name="N0",
                zone="Z0",
                fuel_type="nuclear",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
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
            fleet,
            demand,
            mc=mc,
            T=self.T,
            rps_target=None,
            **self._no_renewables(1),
        )
        np.testing.assert_allclose(with_none.prices, baseline.prices)
        np.testing.assert_allclose(with_none.dispatch, baseline.dispatch)
        self.assertIsNone(baseline.rps_shadow_price)
        self.assertIsNone(with_none.rps_shadow_price)

    def test_rps_nuclear_present_does_not_satisfy_target(self):
        # CX-6a: an RPS is a *renewable* standard, so nuclear does not count
        # toward it even though it is clean. A nuclear + gas fleet has clean
        # capacity available (100 MW nuclear) but NO renewable capacity, so a
        # 50% RPS is infeasible -- nuclear's presence cannot satisfy it. Under
        # the pre-fix semantics (nuclear counted) this solve was Optimal with
        # nuclear covering the target; now it raises.
        fleet = self._nuclear_gas_fleet()
        mc = np.vstack([np.full(self.T, 0.0), np.full(self.T, 20.0)])
        demand = np.full((1, self.T), 80.0)

        with self.assertRaises(RuntimeError):
            solve_dispatch(
                fleet,
                demand,
                mc=mc,
                T=self.T,
                rps_target=0.5,
                **self._no_renewables(1),
            )

    def test_rps_dual_reflects_renewable_premium_not_nuclear(self):
        # CX-6a: with nuclear excluded, the RPS must be met by wind/solar, so
        # the REC dual reflects the *renewable* premium, not nuclear's. A fleet
        # of cheap nuclear (MC 0) + gas (MC 20) plus expensive wind (MC 100)
        # and a 50% target: absent the RPS, cheap nuclear serves all load and
        # no wind runs. The RPS forces 50% of demand onto wind, displacing
        # nuclear, so the dual is the wind-over-nuclear premium (100). If
        # nuclear still counted (pre-fix), its output alone would satisfy the
        # target and the dual would be 0 -- excluding nuclear makes it rise.
        fleet = self._nuclear_gas_fleet()
        # Row 0 nuclear (cheapest), row 1 gas.
        mc = np.vstack([np.full(self.T, 0.0), np.full(self.T, 20.0)])
        demand = np.full((1, self.T), 80.0)

        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            rps_target=0.5,
            wind_cf=np.full((1, self.T), 0.5),
            wind_cap=np.array([100.0]),  # 50 MW available vs 40 MW target
            wind_mc=100.0,  # expensive renewable, idle absent the RPS
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        self.assertEqual(result.status, "Optimal")
        self.assertIsNotNone(result.rps_shadow_price)
        # The dual is the wind premium over the displaced nuclear (100 - 0),
        # NOT zero (which nuclear-counting semantics would give).
        self.assertGreater(result.rps_shadow_price, 0.0)
        self.assertAlmostEqual(result.rps_shadow_price, 100.0, delta=0.5)
        # Renewables (wind), not nuclear, carry the target: total wind output
        # reaches at least the 50% floor.
        self.assertGreaterEqual(result.wind_dispatched.sum(), 0.5 * demand.sum() - 1.0)

    def test_rps_non_binding_with_enough_wind(self):
        # Cheap wind already supplies more than the RPS floor, so the
        # constraint is slack and its dual is zero.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)

        result = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            rps_target=0.5,
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
                fleet,
                demand,
                mc=mc,
                T=self.T,
                rps_target=1.0,
                **self._no_renewables(1),
            )


class TestMassCapConstraint(unittest.TestCase):
    """The emissions mass-cap row, its endogenous dual, and membership."""

    T = 24

    def _no_renewables(self, n_zones):
        return dict(
            wind_cf=np.zeros((n_zones, self.T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, self.T)),
            solar_cap=np.zeros(n_zones),
        )

    def test_no_hour_loop_in_builder(self):
        # Rule 2: the row builder must not loop over hours.
        import inspect

        from market_sim.model.dispatch import _build_mass_cap_rows

        src = inspect.getsource(_build_mass_cap_rows)
        self.assertNotIn("for t in", src)
        self.assertNotIn("for hour", src)

    def test_none_matches_unconstrained_dispatch(self):
        # mass_cap_coeffs=None adds no row: identical solve, co2_cap_price None.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=200.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        baseline = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, **self._no_renewables(1)
        )
        with_none = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            mass_cap_coeffs=None,
            **self._no_renewables(1),
        )
        np.testing.assert_allclose(with_none.prices, baseline.prices)
        np.testing.assert_allclose(with_none.dispatch, baseline.dispatch)
        self.assertIsNone(baseline.co2_cap_price)
        self.assertIsNone(with_none.co2_cap_price)

    def _dirty_clean_fleet(self):
        # Two units in one zone: cheap-dirty (mc 20, 1.0 t/MWh) vs
        # expensive-clean (mc 50, 0.2 t/MWh). MC is passed explicitly.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 20.0), np.full(self.T, 50.0)])
        return fleet, mc

    def test_binding_cap_dual_equals_switching_price(self):
        # Plan §9.1: a cap set between all-dirty and all-clean emissions binds,
        # and its dual equals the analytic switching price
        # (mc_clean - mc_dirty) / (rate_dirty - rate_clean).
        fleet, mc = self._dirty_clean_fleet()
        demand = np.full((1, self.T), 100.0)
        rate_dirty, rate_clean = 1.0, 0.2
        coeffs = np.array([[rate_dirty, rate_clean]])
        # All-dirty = 100*1.0*24 = 2400 t; all-clean = 480 t. Cap in between.
        cap = 1200.0
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            mass_cap_coeffs=coeffs,
            mass_cap_rhs=np.array([cap]),
            **self._no_renewables(1),
        )
        self.assertEqual(res.status, "Optimal")
        # Cap binds: total weighted emissions equal the budget.
        emissions = (coeffs[0][:, None] * res.dispatch).sum()
        self.assertAlmostEqual(emissions, cap, delta=1.0)
        # Endogenous allowance price = analytic switching price.
        expected = (50.0 - 20.0) / (rate_dirty - rate_clean)  # = 37.5
        self.assertIsNotNone(res.co2_cap_price)
        self.assertAlmostEqual(res.co2_cap_price[0], expected, delta=0.1)
        # Member dispatch shifts to a mean of 37.5 MW dirty. With flat hourly MC
        # and a single annual cap the per-hour split is degenerate (0/100), but
        # the annual dirty energy is pinned at 37.5*24 MWh.
        self.assertAlmostEqual(res.dispatch[0].sum(), 37.5 * self.T, delta=self.T)

    def test_dual_nonnegative_monotonic_and_reorders_merit(self):
        # Dual sign + monotonicity invariant (task deliverable 3): as the cap
        # tightens from slack to tight, the endogenous allowance price is always
        # >= 0 and non-decreasing, and the merit order re-orders cheap-dirty
        # coal -> pricier-clean gas (coal energy falls, gas energy rises).
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        # Row 0: coal — cheap ($18) and dirty (1.0 t/MWh).
        # Row 1: gas_cc — pricier ($32) and cleaner (0.40 t/MWh).
        mc = np.vstack([np.full(self.T, 18.0), np.full(self.T, 32.0)])
        demand = np.full((1, self.T), 100.0)
        coeffs = np.array([[1.0, 0.40]])
        # All-coal emissions = 100*1.0*24 = 2400 t; all-gas = 960 t.
        caps = [1.0e6, 2000.0, 1500.0, 1100.0]  # slack -> progressively tighter
        duals, coal_energy, gas_energy = [], [], []
        for cap in caps:
            res = solve_dispatch(
                fleet,
                demand,
                mc=mc,
                T=self.T,
                mass_cap_coeffs=coeffs,
                mass_cap_rhs=np.array([cap]),
                **self._no_renewables(1),
            )
            self.assertEqual(res.status, "Optimal")
            duals.append(res.co2_cap_price[0])
            coal_energy.append(res.dispatch[0].sum())
            gas_energy.append(res.dispatch[1].sum())
        # Sign: every dual is non-negative.
        for d in duals:
            self.assertGreaterEqual(d, -1e-6)
        # Slack cap prices at ~0; the analytic switching price once binding is
        # (32-18)/(1.0-0.40) = 23.333...
        self.assertAlmostEqual(duals[0], 0.0, places=3)
        # Monotone non-decreasing as the cap tightens.
        for lo, hi in zip(duals, duals[1:]):
            self.assertGreaterEqual(hi + 1e-6, lo)
        # A binding cap prices at the coal->gas switching price.
        self.assertAlmostEqual(duals[-1], (32.0 - 18.0) / (1.0 - 0.40), delta=0.1)
        # Merit re-orders: tighter caps push energy off coal onto gas.
        for lo, hi in zip(coal_energy, coal_energy[1:]):
            self.assertLessEqual(hi, lo + 1e-6)
        for lo, hi in zip(gas_energy, gas_energy[1:]):
            self.assertGreaterEqual(hi, lo - 1e-6)

    def test_loose_cap_has_zero_dual(self):
        # A cap above the all-dirty emissions never binds: dual is 0.
        fleet, mc = self._dirty_clean_fleet()
        demand = np.full((1, self.T), 100.0)
        coeffs = np.array([[1.0, 0.2]])
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            mass_cap_coeffs=coeffs,
            mass_cap_rhs=np.array([1.0e6]),
            **self._no_renewables(1),
        )
        self.assertAlmostEqual(res.co2_cap_price[0], 0.0, places=3)
        # All-dirty dispatch (cheapest) — the cap is slack.
        np.testing.assert_allclose(res.dispatch[0], 100.0, atol=1e-6)

    def test_membership_charges_only_member_zone(self):
        # Plan §9.4/§9.6: with membership [1, 0] the cap coefficient is zero on
        # zone-1's generator, so zone-1 emissions are uncapped. Cheap-dirty in
        # each zone; cap forces zone-0 to its clean unit but leaves zone-1 alone.
        generators = [
            Generator(
                unit_id="D0",
                name="D0",
                zone="Z0",
                fuel_type="coal",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="C0",
                name="C0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="D1",
                name="D1",
                zone="Z1",
                fuel_type="coal",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(generators, ["Z0", "Z1"], hours=self.T)
        # Rows: D0 (dirty, mc20), C0 (clean, mc50), D1 (dirty, mc20).
        mc = np.vstack(
            [
                np.full(self.T, 20.0),
                np.full(self.T, 50.0),
                np.full(self.T, 20.0),
            ]
        )
        demand = np.full((2, self.T), 100.0)
        # Copperplate link so zones can share, but each has local supply.
        emission = np.array([1.0, 0.2, 1.0])
        membership = np.array([1.0, 0.0])  # zone-0 member, zone-1 not
        coeffs = (membership[fleet.zone_idx] * emission)[None, :]
        # Coefficient on the zone-1 dirty unit (index 2) must be zero.
        self.assertEqual(coeffs[0][2], 0.0)
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            mass_cap_coeffs=coeffs,
            mass_cap_rhs=np.array([600.0]),  # binds only on zone-0's emissions
            **self._no_renewables(2),
        )
        self.assertEqual(res.status, "Optimal")
        # Zone-1's dirty unit runs full-out (uncapped) every hour.
        np.testing.assert_allclose(res.dispatch[2], 100.0, atol=1e-6)

    def test_simultaneous_rps_reserve_and_masscap_duals(self):
        # Plan §9.5: RPS + reserve co-opt + mass-cap all active at once. Each
        # end-anchored dual must land on its own row. Wind (RPS-eligible) +
        # dirty gas + idle nuclear: the RPS floors renewable output (CX-6a --
        # nuclear does NOT count), the mass cap bounds gas emissions, reserve
        # co-opt prices headroom. Cross-check each dual against a single-
        # constraint solve.
        generators = [
            Generator(
                unit_id="N0",
                name="N0",
                zone="Z0",
                fuel_type="nuclear",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=100.0,
                pmin_mw=0.0,
                eford=0.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(generators, ["Z0"], hours=self.T)
        mc = np.vstack([np.full(self.T, 100.0), np.full(self.T, 20.0)])
        demand = np.full((1, self.T), 80.0)
        coeffs = np.array([[0.0, 0.5]])  # only gas emits
        common = dict(
            mc=mc,
            T=self.T,
            reserve_requirement=np.full(self.T, 30.0),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([1000.0]),
            ordc_step_widths=np.array([1000.0]),
            # Wind is the only RPS-eligible resource: expensive enough (MC 60 >
            # gas 20) to stay idle absent the RPS, so it forces the dual up.
            wind_cf=np.full((1, self.T), 0.5),
            wind_cap=np.array([100.0]),  # 50 MW available vs 40 MW target
            wind_mc=60.0,
            solar_cf=np.zeros((1, self.T)),
            solar_cap=np.zeros(1),
        )
        res = solve_dispatch(
            fleet,
            demand,
            rps_target=0.5,
            mass_cap_coeffs=coeffs,
            mass_cap_rhs=np.array([700.0]),
            **common,
        )
        self.assertEqual(res.status, "Optimal")
        # All three duals recovered and distinct on their own rows.
        self.assertIsNotNone(res.rps_shadow_price)
        self.assertIsNotNone(res.co2_cap_price)
        self.assertIsNotNone(res.reserve_price)
        self.assertGreater(res.rps_shadow_price, 0.0)
        self.assertGreaterEqual(res.co2_cap_price[0], 0.0)
        # The mass-cap dual is recovered from the correct row: re-solve with a
        # cap loose enough to never bind and confirm it drops to ~0 while RPS
        # stays put — proving the cap dual is not aliasing the RPS row.
        loose = solve_dispatch(
            fleet,
            demand,
            rps_target=0.5,
            mass_cap_coeffs=coeffs,
            mass_cap_rhs=np.array([1.0e6]),
            **common,
        )
        self.assertAlmostEqual(loose.co2_cap_price[0], 0.0, places=2)
        self.assertAlmostEqual(loose.rps_shadow_price, res.rps_shadow_price, delta=1e-3)


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
    h.addRows(A.shape[0], row_lower, row_upper, A.nnz, starts, indices, values)
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

    fleet = _make_fleet(["Z0"] * n_gen, ["Z0"], hours=T, pmax=pmax, pmin=0.0, eford=0.0)
    mc = np.tile(np.linspace(20.0, 80.0, n_gen)[:, np.newaxis], (1, T))

    peak = 0.8 * total_cap
    hours = np.arange(T)
    demand = (0.7 * peak + 0.3 * peak * np.sin(2 * np.pi * hours / T)).reshape(1, T)

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

    n_zones = len(zone_names)
    west = zone_names.index("West")
    south_central = zone_names.index("South_Central")

    wind_cf = np.zeros((n_zones, T))
    wind_cf[west] = 0.35
    wind_cap = np.zeros(n_zones)
    wind_cap[west] = 2000.0

    solar_cf = np.zeros((n_zones, T))
    solar_cf[south_central] = np.clip(0.6 * np.sin(np.pi * (hod - 6) / 12), 0, 1)
    solar_cap = np.zeros(n_zones)
    solar_cap[south_central] = 1500.0

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


@pytest.mark.slow  # benchmark-only: 6 full-year LP solves comparing solver configs
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
        print("\n[solver bench] 200 gens x 8760h -- 1 zone, no storage/transmission")
        self._run_benchmark(_make_200gen_1zone_problem())

        print("[solver bench] 200 gens x 8760h -- 4 zones + storage + transmission")
        self._run_benchmark(_make_4zone_storage_problem())


if __name__ == "__main__":
    unittest.main()


class TestReserveCoOptimization(unittest.TestCase):
    """Trivial-case tests for in-LP energy+reserve co-optimization.

    Reserve is tracked per zone (``reserve_dispatch`` is ``(n_zones, T)``);
    these single-zone cases make the zone aggregate equal to the fleet total.
    """

    T = 4

    def _no_renewables(self, n_zones):
        return dict(
            wind_cf=np.zeros((n_zones, self.T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, self.T)),
            solar_cap=np.zeros(n_zones),
        )

    def test_reserve_met_from_free_headroom_no_price_lift(self):
        # 1 gen 100 MW @ $20, demand 80 -> 20 MW free headroom. Reserve req 10
        # < 20: met for free, reserve price 0, energy LMP stays $20.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 20.0)
        demand = np.full((1, self.T), 80.0)
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            reserve_requirement=np.full(self.T, 10.0),
            reserve_eligible=np.array([True]),
            ordc_penalties=np.array([1000.0]),
            ordc_step_widths=np.array([1000.0]),
            **self._no_renewables(1),
        )
        np.testing.assert_allclose(res.dispatch, 80.0)
        self.assertTrue((res.reserve_dispatch >= 10.0 - 1e-6).all())
        np.testing.assert_allclose(res.reserve_price, 0.0, atol=1e-6)
        np.testing.assert_allclose(res.prices, 20.0, atol=1e-6)

    def test_reserve_scarcity_lifts_energy_lmp(self):
        # Same gen, reserve req 30 > 20 free headroom: 10 MW short, priced at
        # the $1000 ORDC step. The shared-headroom constraint binds (P+R=100),
        # transferring the reserve price into the energy LMP: $20 + $1000.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 20.0)
        demand = np.full((1, self.T), 80.0)
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            reserve_requirement=np.full(self.T, 30.0),
            reserve_eligible=np.array([True]),
            ordc_penalties=np.array([1000.0]),
            ordc_step_widths=np.array([1000.0]),
            **self._no_renewables(1),
        )
        np.testing.assert_allclose(res.dispatch, 80.0)
        # Reserve capped by headroom at 20 MW (P + R <= 100).
        np.testing.assert_allclose(res.reserve_dispatch, 20.0, atol=1e-6)
        np.testing.assert_allclose(res.reserve_price, 1000.0, atol=1e-6)
        np.testing.assert_allclose(res.prices, 1020.0, atol=1e-6)

    def test_idle_unit_supplies_reserve_without_lifting_price(self):
        # Cheap 100 MW @ $20 + idle 100 MW @ $90, both in one zone. Demand 80,
        # reserve req 50. Cheap serves the 80 energy; the zone has 120 MW of
        # headroom (200 cap - 80 dispatched), far above the 50 MW requirement,
        # so reserve clears free -> reserve price 0, LMP stays $20.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 20.0), np.full(self.T, 90.0)])
        demand = np.full((1, self.T), 80.0)
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            reserve_requirement=np.full(self.T, 50.0),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([1000.0]),
            ordc_step_widths=np.array([1000.0]),
            **self._no_renewables(1),
        )
        # Requirement met (reserve beyond it is free, so the exact level is
        # indeterminate); the point is the price does not lift.
        total_reserve = res.reserve_dispatch.sum(axis=0)
        self.assertTrue((total_reserve >= 50.0 - 1e-6).all())
        np.testing.assert_allclose(res.reserve_price, 0.0, atol=1e-6)
        np.testing.assert_allclose(res.prices, 20.0, atol=1e-6)

    def test_storage_backs_reserve_when_enabled(self):
        # One 100 MW @ $20 thermal serving 90 MW load -> 10 MW thermal headroom.
        # Reserve req 30: 20 MW short on thermal alone. A 40 MW storage unit
        # (idle) supplies the rest only when reserve_storage=True, so the
        # requirement clears and the reserve price stays at 0; without it, the
        # 20 MW shortfall would price at the $1000 ORDC step.
        fleet = _make_fleet(
            ["Z0"], ["Z0"], hours=self.T, pmax=100.0, pmin=0.0, eford=0.0
        )
        mc = np.full((1, self.T), 20.0)
        demand = np.full((1, self.T), 90.0)
        kw = dict(
            reserve_requirement=np.full(self.T, 30.0),
            reserve_eligible=np.array([True]),
            ordc_penalties=np.array([1000.0]),
            ordc_step_widths=np.array([1000.0]),
            storage_power_cap=np.array([40.0]),
            storage_energy_cap=np.array([160.0]),
            storage_zone_idx=np.array([0]),
            **self._no_renewables(1),
        )
        without = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, reserve_storage=False, **kw
        )
        with_stor = solve_dispatch(
            fleet, demand, mc=mc, T=self.T, reserve_storage=True, **kw
        )
        # Thermal-only: 10 MW headroom < 30 req -> 20 MW priced at $1000.
        self.assertTrue((without.reserve_price > 100.0).all())
        # Storage room covers the gap -> requirement met free, no price lift.
        np.testing.assert_allclose(with_stor.reserve_price, 0.0, atol=1e-6)
        np.testing.assert_allclose(with_stor.prices, 20.0, atol=1e-6)

    def test_off_path_matches_energy_only(self):
        # No reserve_requirement -> co-opt columns absent; identical result.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=self.T, pmax=60.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(self.T, 25.0), np.full(self.T, 55.0)])
        demand = np.full((1, self.T), 70.0)
        base = solve_dispatch(fleet, demand, mc=mc, T=self.T, **self._no_renewables(1))
        coopt_off = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=self.T,
            reserve_requirement=None,
            **self._no_renewables(1),
        )
        np.testing.assert_allclose(base.dispatch, coopt_off.dispatch)
        np.testing.assert_allclose(base.prices, coopt_off.prices)
        self.assertIsNone(coopt_off.reserve_price)


class TestSignedInterfaceGroup(unittest.TestCase):
    """Signed-member interface groups (MISO per-zone CIL/CEL), trivial cases.

    Trivial-first per CLAUDE.md: 2 zones, short horizons. Covers the 5-tuple
    ``(link_idx, cap, two_way, lower_cap, signs)`` group format — a net
    corridor cap over an opposing one-way link pair (the RDT shape) — and an
    hourly cap vector (the seasonal CIL expansion).
    """

    def _two_zone(self, T: int):
        """Cheap Z0 / expensive Z1 with an RDT-style opposing one-way pair."""
        zone_names = ["Z0", "Z1"]
        fleet = _make_fleet(
            ["Z0", "Z1"], zone_names, hours=T, pmax=10000.0, pmin=0.0, eford=0.0
        )
        mc = np.vstack([np.full(T, 10.0), np.full(T, 90.0)])
        demand = np.array([np.zeros(T), np.full(T, 5000.0)])
        links = [
            TransferLink(
                from_zone="Z0", to_zone="Z1", ttc_mw=6000.0, is_bidirectional=False
            ),
            TransferLink(
                from_zone="Z1", to_zone="Z0", ttc_mw=6000.0, is_bidirectional=False
            ),
        ]
        incidence = build_incidence_matrix(links, zone_names)
        ttc = get_ttc_array(links)
        kwargs = dict(
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
        )
        return fleet, mc, demand, incidence, ttc, kwargs

    def test_signed_net_flow_cap_binds_on_one_way_pair(self):
        # Net import into Z1 = flow(Z0->Z1) - flow(Z1->Z0), capped at 3000 MW
        # even though each one-way link's own TTC (6000) is slack.
        T = 4
        fleet, mc, demand, incidence, ttc, kwargs = self._two_zone(T)
        groups = [(np.array([0, 1]), 3000.0, False, None, np.array([1.0, -1.0]))]
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            interface_groups=groups,
            **kwargs,
        )
        net_import = res.flows[0] - res.flows[1]
        np.testing.assert_allclose(net_import, np.full(T, 3000.0), atol=1e-6)

    def test_hourly_cap_vector_tracks_seasonal_envelope(self):
        # 24-hour horizon with a per-hour cap that steps 2000 -> 4000 at noon
        # (the seasonal CIL expansion shape): the bound must track hour by hour.
        T = 24
        fleet, mc, demand, incidence, ttc, kwargs = self._two_zone(T)
        cap = np.where(np.arange(T) < 12, 2000.0, 4000.0)
        groups = [(np.array([0, 1]), cap, False, None, np.array([1.0, -1.0]))]
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            interface_groups=groups,
            **kwargs,
        )
        net_import = res.flows[0] - res.flows[1]
        np.testing.assert_allclose(net_import, cap, atol=1e-6)

    def test_asymmetric_export_floor_with_signs(self):
        # CEL side: cheap Z1 wants to export back to Z0; the signed group's
        # lower bound (-CEL = -1500) must floor the net flow while the import
        # cap stays slack.
        T = 4
        fleet, _, _, incidence, ttc, kwargs = self._two_zone(T)
        mc = np.vstack([np.full(T, 90.0), np.full(T, 10.0)])
        demand = np.array([np.full(T, 5000.0), np.zeros(T)])
        groups = [(np.array([0, 1]), 6000.0, False, 1500.0, np.array([1.0, -1.0]))]
        res = solve_dispatch(
            fleet,
            demand,
            mc=mc,
            T=T,
            incidence=incidence,
            ttc=ttc,
            interface_groups=groups,
            **kwargs,
        )
        net_import_z1 = res.flows[0] - res.flows[1]
        np.testing.assert_allclose(net_import_z1, np.full(T, -1500.0), atol=1e-6)


class TestInterfaceGroupLimit(unittest.TestCase):
    """Tests for the aggregate interface-limit rows (CAISO simultaneous import)."""

    def setUp(self):
        # 3 zones: an import node Z0 with cheap supply, two load zones Z1/Z2,
        # each fed by a generous link from the import node. The aggregate cap
        # over the two links is tighter than their TTC sum, so it must bind.
        self.T = 4
        self.zone_names = ["Z0", "Z1", "Z2"]
        # One cheap generator at the import node, one expensive local unit in
        # each load zone (so the LP imports up to the cap, then runs local gas).
        self.fleet = _make_fleet(
            ["Z0", "Z1", "Z2"],
            self.zone_names,
            hours=self.T,
            pmax=10000.0,
            pmin=0.0,
            eford=0.0,
        )
        self.mc = np.vstack(
            [
                np.full(self.T, 10.0),  # import node: cheap
                np.full(self.T, 90.0),  # Z1 local: expensive
                np.full(self.T, 90.0),  # Z2 local: expensive
            ]
        )
        # Demand only in the two load zones; import node carries none.
        self.demand = np.array(
            [
                np.zeros(self.T),
                np.full(self.T, 3000.0),
                np.full(self.T, 3000.0),
            ]
        )
        # Links Z0->Z1 and Z0->Z2 built with the production incidence
        # convention (positive flow = power from the import node into a load
        # zone = an import).
        links = [
            TransferLink(from_zone="Z0", to_zone="Z1", ttc_mw=6000.0),
            TransferLink(from_zone="Z0", to_zone="Z2", ttc_mw=6000.0),
        ]
        self.incidence = build_incidence_matrix(links, self.zone_names)
        self.ttc = get_ttc_array(links)  # each link loose at 6000

    def _kwargs(self):
        return dict(
            wind_cf=np.zeros((3, self.T)),
            wind_cap=np.zeros(3),
            solar_cf=np.zeros((3, self.T)),
            solar_cap=np.zeros(3),
        )

    def test_aggregate_cap_binds_below_ttc_sum(self):
        # Without the cap the LP imports the full 6000 MW (3000 each link).
        uncapped = solve_dispatch(
            self.fleet,
            self.demand,
            mc=self.mc,
            T=self.T,
            incidence=self.incidence,
            ttc=self.ttc,
            **self._kwargs(),
        )
        total_import = uncapped.flows.sum(axis=0)  # link 0 + link 1, per hour
        np.testing.assert_allclose(total_import, np.full(self.T, 6000.0), atol=1e-6)

        # With an aggregate cap of 4000 MW the simultaneous import is bound,
        # even though each link's own TTC (6000) is slack.
        groups = [(np.array([0, 1]), 4000.0, True)]
        capped = solve_dispatch(
            self.fleet,
            self.demand,
            mc=self.mc,
            T=self.T,
            incidence=self.incidence,
            ttc=self.ttc,
            interface_groups=groups,
            **self._kwargs(),
        )
        total_import = capped.flows.sum(axis=0)
        self.assertTrue(np.all(total_import <= 4000.0 + 1e-6))
        np.testing.assert_allclose(total_import, np.full(self.T, 4000.0), atol=1e-6)

    def test_asymmetric_group_caps_export_direction(self):
        # 4-tuple group (link_idx, import_cap, two_way=False, export_cap): the
        # reverse (export, negative-flow) direction is floored at -export_cap
        # while the import direction keeps import_cap. Make the import node
        # expensive and a load zone's local gen cheap, so the LP wants to export
        # cheap local power up the link (negative flow) — and verify the export
        # floor binds while the import cap stays slack.
        mc = np.vstack(
            [
                np.full(self.T, 90.0),  # import node: expensive
                np.full(self.T, 10.0),  # Z1 local: cheap (wants to export)
                np.full(self.T, 90.0),  # Z2 local: expensive
            ]
        )
        demand = np.array(
            [
                np.full(self.T, 2000.0),  # import node now has load to serve
                np.zeros(self.T),
                np.full(self.T, 1000.0),
            ]
        )
        # Export floor of 500 MW on link 0 (Z0->Z1); import cap loose at 6000.
        groups = [(np.array([0]), 6000.0, False, 500.0)]
        res = solve_dispatch(
            self.fleet,
            demand,
            mc=mc,
            T=self.T,
            incidence=self.incidence,
            ttc=self.ttc,
            interface_groups=groups,
            **self._kwargs(),
        )
        # Flow on link 0 is bounded below by -500 (export from Z1 to Z0 capped).
        self.assertTrue(np.all(res.flows[0] >= -500.0 - 1e-6))
        np.testing.assert_allclose(res.flows[0], np.full(self.T, -500.0), atol=1e-6)

    def test_no_groups_is_identical(self):
        base = solve_dispatch(
            self.fleet,
            self.demand,
            mc=self.mc,
            T=self.T,
            incidence=self.incidence,
            ttc=self.ttc,
            **self._kwargs(),
        )
        none_groups = solve_dispatch(
            self.fleet,
            self.demand,
            mc=self.mc,
            T=self.T,
            incidence=self.incidence,
            ttc=self.ttc,
            interface_groups=None,
            **self._kwargs(),
        )
        np.testing.assert_allclose(base.flows, none_groups.flows)
        np.testing.assert_allclose(base.prices, none_groups.prices)
