"""Tests for the plant-group hourly ramp-envelope rows (``ramp_limits``).

Design: docs/ramp-locational-design-2026-07.md §1 / §7 (T1-T3, T6). Trivial
cases first (1 gen, 1 zone, 24 hours), per the repo testing pattern.
"""

import inspect
import time
import unittest

import numpy as np

from market_sim.model.dispatch import (
    VariableLayout,
    _build_local_capacity_rows,
    _build_ramp_rows,
    build_constraints,
    solve_dispatch,
)
from tests.test_dispatch import _make_fleet

T24 = 24


def _no_renewables(n_zones, T):
    """Zero wind/solar kwargs for ``solve_dispatch``."""
    return dict(
        wind_cf=np.zeros((n_zones, T)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, T)),
        solar_cap=np.zeros(n_zones),
    )


def _step_demand(T=T24, lo=50.0, hi=150.0, step_at=12):
    """Flat ``lo`` demand stepping to ``hi`` at hour ``step_at`` (1 zone)."""
    demand = np.full((1, T), lo)
    demand[0, step_at:] = hi
    return demand


class TestRampRowsT1(unittest.TestCase):
    """T1: slow gen + fast peaker over a demand step (the merit mechanism)."""

    def _solve(self, with_ramp):
        # Gen 0: slow (pmax 100, MC 30, RU=RD=20). Gen 1: peaker (pmax 200,
        # MC 100). Demand steps 50 -> 150 at hour 12.
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0
        )
        fleet.pmax[1] = 200.0
        mc = np.vstack([np.full(T24, 30.0), np.full(T24, 100.0)])
        kwargs = dict(_no_renewables(1, T24))
        if with_ramp:
            kwargs.update(
                ramp_gen_idx=np.array([0]),
                ramp_group_col=np.array([0]),
                ramp_up_mw=np.array([20.0]),
                ramp_dn_mw=np.array([20.0]),
            )
        return solve_dispatch(fleet, _step_demand(), mc=mc, T=T24, **kwargs)

    def test_slow_gen_delta_bounded_and_peaker_fills_step(self):
        result = self._solve(with_ramp=True)
        slow = result.dispatch[0]
        deltas = np.diff(slow)
        self.assertLessEqual(deltas.max(), 20.0 + 1e-6)
        self.assertGreaterEqual(deltas.min(), -20.0 - 1e-6)
        # The step hour outruns the slow gen's envelope: the peaker fills it.
        self.assertGreater(result.dispatch[1, 12], 1e-6)
        # No load shed anywhere.
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)

    def test_step_hour_price_is_peaker_mc(self):
        # The merit mechanism itself: in the ramp-bound step hour the fast
        # resource is marginal, so the LMP rises to the peaker's MC.
        result = self._solve(with_ramp=True)
        self.assertAlmostEqual(float(result.prices[0, 12]), 100.0, places=4)

    def test_without_ramp_slow_gen_jumps_freely(self):
        # Control arm: no envelope -> the slow gen takes the whole step in
        # one hour and the peaker never runs at the step.
        result = self._solve(with_ramp=False)
        self.assertAlmostEqual(float(result.dispatch[0, 12]), 100.0, places=4)
        self.assertGreater(float(np.diff(result.dispatch[0]).max()), 20.0)


class TestRampRowsT2Availability(unittest.TestCase):
    """T2: an outage edge widens the bounds — the LP stays feasible."""

    def test_outage_onset_and_return_stay_feasible(self):
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0
        )
        fleet.pmax[1] = 200.0
        # Slow gen forced off hours 8-15: onset forces dP = -P[7], return
        # restores 100 MW in one hour — both wider than RU=RD=20 and only
        # feasible through the availability-edge widening.
        fleet.availability[0, 8:16] = 0.0
        mc = np.vstack([np.full(T24, 30.0), np.full(T24, 100.0)])
        result = solve_dispatch(
            fleet,
            _step_demand(),
            mc=mc,
            T=T24,
            ramp_gen_idx=np.array([0]),
            ramp_group_col=np.array([0]),
            ramp_up_mw=np.array([20.0]),
            ramp_dn_mw=np.array([20.0]),
            **_no_renewables(1, T24),
        )
        # Peaker (200 MW) covers the outage window alone: no slack at all.
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)
        np.testing.assert_allclose(result.dispatch[0, 8:16], 0.0, atol=1e-6)


class TestRampRowsT3PlantGrouping(unittest.TestCase):
    """T3: the envelope binds the plant SUM; tranche switching stays free."""

    def test_group_sum_bounded_not_tranches(self):
        # One plant, two tranches (gens 0+1, one ramp group) + a peaker.
        fleet = _make_fleet(
            ["Z0", "Z0", "Z0"], ["Z0"], hours=T24, pmax=60.0, pmin=0.0, eford=0.0
        )
        fleet.pmax[2] = 200.0
        mc = np.vstack([np.full(T24, 30.0), np.full(T24, 35.0), np.full(T24, 100.0)])
        result = solve_dispatch(
            fleet,
            _step_demand(),
            mc=mc,
            T=T24,
            ramp_gen_idx=np.array([0, 1]),
            ramp_group_col=np.array([0, 0]),
            ramp_up_mw=np.array([20.0]),
            ramp_dn_mw=np.array([20.0]),
            **_no_renewables(1, T24),
        )
        plant = result.dispatch[0] + result.dispatch[1]
        deltas = np.diff(plant)
        self.assertLessEqual(deltas.max(), 20.0 + 1e-6)
        self.assertGreaterEqual(deltas.min(), -20.0 - 1e-6)
        np.testing.assert_allclose(result.slack, 0.0, atol=1e-6)


class TestRampFlagOffByteIdentity(unittest.TestCase):
    """Flag off -> zero rows -> byte-identical constraint matrix."""

    def test_none_inputs_add_no_rows(self):
        fleet = _make_fleet(
            ["Z0", "Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0
        )
        demand = _step_demand()
        layout = VariableLayout(n_gen=2, n_zones=1, n_storage=0, n_links=0, T=T24)
        a0, lo0, up0 = build_constraints(layout, fleet, demand)
        a1, lo1, up1 = build_constraints(
            layout,
            fleet,
            demand,
            ramp_gen_idx=None,
            ramp_group_col=None,
            ramp_up_mw=None,
            ramp_dn_mw=None,
            local_capacity_specs=None,
        )
        self.assertEqual(a0.shape, a1.shape)
        self.assertEqual((a0 != a1).nnz, 0)
        np.testing.assert_array_equal(lo0, lo1)
        np.testing.assert_array_equal(up0, up1)

    def test_empty_gen_idx_adds_no_rows(self):
        fleet = _make_fleet(["Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0)
        demand = np.full((1, T24), 50.0)
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=T24)
        a0, _, _ = build_constraints(layout, fleet, demand)
        a1, _, _ = build_constraints(
            layout,
            fleet,
            demand,
            ramp_gen_idx=np.zeros(0, dtype=int),
            ramp_group_col=np.zeros(0, dtype=int),
            ramp_up_mw=np.zeros(0),
            ramp_dn_mw=np.zeros(0),
        )
        self.assertEqual(a0.shape, a1.shape)
        self.assertEqual((a0 != a1).nnz, 0)


class TestRampBoundsWidening(unittest.TestCase):
    """The availability-delta arithmetic lands in the right rows."""

    def test_bounds_widen_exactly_at_the_capacity_edge(self):
        fleet = _make_fleet(["Z0"], ["Z0"], hours=T24, pmax=100.0, pmin=0.0, eford=0.0)
        fleet.availability[0, 10] = 0.0  # one-hour outage
        layout = VariableLayout(n_gen=1, n_zones=1, n_storage=0, n_links=0, T=T24)
        block, lower, upper = _build_ramp_rows(
            layout,
            fleet,
            np.array([0]),
            np.array([0]),
            np.array([20.0]),
            np.array([20.0]),
        )
        self.assertEqual(block.shape[0], T24 - 1)
        # Row (t-1) covers the t-1 -> t transition (single group).
        # Transition 9->10 loses 100 MW: RD widens; 10->11 regains: RU widens.
        np.testing.assert_allclose(upper[[9, 10]], [20.0, 120.0])
        np.testing.assert_allclose(lower[[9, 10]], [-120.0, -20.0])
        # Everywhere else the measured envelope holds unwidened.
        mask = np.ones(T24 - 1, dtype=bool)
        mask[[9, 10]] = False
        np.testing.assert_allclose(upper[mask], 20.0)
        np.testing.assert_allclose(lower[mask], -20.0)


class TestRampVectorizationT6(unittest.TestCase):
    """T6: no hour loop in the new builders; 8760-h construction is fast."""

    def test_no_python_loop_over_hours(self):
        for fn in (_build_ramp_rows, _build_local_capacity_rows):
            src = inspect.getsource(fn)
            self.assertNotIn("for t in range(", src)

    def test_full_year_construction_time(self):
        T = 8760
        n_groups, members_per = 60, 4
        n_gen = n_groups * members_per
        fleet = _make_fleet(
            ["Z0"] * n_gen, ["Z0"], hours=T, pmax=100.0, pmin=0.0, eford=0.0
        )
        layout = VariableLayout(n_gen=n_gen, n_zones=1, n_storage=0, n_links=0, T=T)
        gen_idx = np.arange(n_gen)
        group_col = np.repeat(np.arange(n_groups), members_per)
        start = time.perf_counter()
        block, lower, upper = _build_ramp_rows(
            layout,
            fleet,
            gen_idx,
            group_col,
            np.full(n_groups, 50.0),
            np.full(n_groups, 50.0),
        )
        elapsed = time.perf_counter() - start
        self.assertEqual(block.shape[0], n_groups * (T - 1))
        self.assertLess(elapsed, 5.0)


if __name__ == "__main__":
    unittest.main()
