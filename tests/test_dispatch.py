"""Tests for the dispatch variable layout and cost-vector assembly."""

import unittest

import numpy as np

from market_sim.model.dispatch import VariableLayout, build_cost_vector


class TestVariableLayout(unittest.TestCase):
    """Tests for column-index bookkeeping in ``VariableLayout``."""

    def test_total_columns_minimal(self):
        # 2 thermal gens, 1 zone, no storage, no links.
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=24)
        # vars_per_hour = 2 + 2*1 + 3*0 + 0 + 1 = 5
        self.assertEqual(layout.vars_per_hour, 5)
        self.assertEqual(layout.total_columns, 5 * 24)

    def test_vars_per_hour_with_storage_and_links(self):
        layout = VariableLayout(n_gen=3, n_zones=2, n_storage=4, n_links=2, T=10)
        # 3 + 2*2 + 3*4 + 2 + 2 = 23
        self.assertEqual(layout.vars_per_hour, 23)
        self.assertEqual(layout.total_columns, 23 * 10)

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
        for l in range(2):  # l: transmission link index
            for t in range(layout.T):  # t: hour index
                self.assertEqual(cost[layout.flow_col(l, t)], 0.0)


if __name__ == "__main__":
    unittest.main()
