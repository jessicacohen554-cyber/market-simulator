"""The slim window (``uc_slim_window``, ``model/uc/slim.py``; lane UC-SLIM).

The fast-tier half of the equivalence gate: on tiny hand-built LPs every
reduction fixes, tightens, drops or merges exactly what it claims and stands
down on a contradiction; a slim column vector round-trips through
``restrict`` / ``expand`` with the fixed values reinserted and the merged
members split within their bounds; HiGHS's objective and gap carry the
offset; on the toy windows (no-load decommit, carried min-down, storage
boundary, relaxation) the slim and the full model give an identical
objective and an identical ``u``, the expanded solution satisfies every
full-model bound, and the stage's rolling schedule is the same with the
slim on and off.
"""

from __future__ import annotations

import numpy as np
import pytest
import scipy.sparse as sp

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.uc import slim as ucslim
from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import (
    UcWindowInfeasible,
    UcWindowModel,
    WindowState,
    slice_window_inputs,
)

from .conftest import toy_inputs

T = 24
OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)
INF = np.inf


def _lp(rows, cl, cu, rl, ru, cost=None, is_int=None):
    A = sp.csr_matrix(np.asarray(rows, dtype=float))
    n = A.shape[1]
    cost = np.zeros(n) if cost is None else np.asarray(cost, dtype=float)
    return ucslim.reduce_lp(
        A,
        cost,
        np.asarray(cl, float),
        np.asarray(cu, float),
        np.asarray(rl, float),
        np.asarray(ru, float),
        None if is_int is None else np.asarray(is_int, bool),
    )


# ------------------------------------------------------------- reductions
def test_fixed_column_leaves_with_its_cost_and_shifts_the_row():
    # x0 fixed at 2 (cost 3), x1 free in [0, 5], x2 in [0, 9] (cost 2);
    # rows: x0 + x1 >= 3 (a singleton on x1 once x0 is gone: x1 >= 1, dropped),
    # x0 + x1 + x2 <= 10 (kept: it can bind; shifted by the fixed 2)
    red = _lp(
        [[1, 1, 0], [1, 1, 1]],
        [2, 0, 0],
        [2, 5, 9],
        [3, -INF],
        [INF, 10],
        cost=[3, 1, 2],
    )
    assert red is not None
    assert red.fixed_cols.tolist() == [0] and red.fixed_values.tolist() == [2.0]
    assert red.n_slim_cols == 2 and red.n_slim_rows == 1
    assert red.kept_rows.tolist() == [1]
    assert red.row_lower.tolist() == [-INF] and red.row_upper.tolist() == [8.0]
    assert red.col_lower.tolist() == [1.0, 0.0]
    assert red.offset == 6.0
    assert red.counts["cols_fixed_by_bounds"] == 1
    assert red.counts["rows_dropped_singleton"] == 1


def test_forcing_row_fixes_every_column_at_the_attaining_bound():
    # x0, x1 in [0, 1]; row: x0 + x1 >= 2 -> both at 1; row then redundant
    red = _lp([[1, 1]], [0, 0], [1, 1], [2], [INF])
    assert red is not None
    assert red.fixed_cols.tolist() == [0, 1] and red.fixed_values.tolist() == [1, 1]
    assert red.counts["cols_fixed_by_forcing"] == 2
    assert red.n_slim_rows == 0 and red.n_slim_cols == 0


def test_forcing_row_at_the_minimum_fixes_negatives_at_their_upper_bound():
    # x0 in [0, 1], x1 in [0, 1]; row: x0 - x1 <= -1 -> x0 = 0, x1 = 1
    red = _lp([[1, -1]], [0, 0], [1, 1], [-INF], [-1])
    assert red is not None
    assert red.fixed_values.tolist() == [0.0, 1.0]


def test_singleton_row_tightens_the_column_and_is_dropped():
    # x0 in [0, 10]; rows: 2 x0 <= 6  (-> x0 <= 3), x0 + x1 >= 1 (kept);
    # distinct costs so the two are not parallel
    red = _lp([[2, 0], [1, 1]], [0, 0], [10, 10], [-INF, 1], [6, INF], cost=[1, 2])
    assert red is not None
    assert red.n_slim_rows == 1 and red.kept_rows.tolist() == [1]
    assert red.col_upper[0] == 3.0 and red.counts["rows_dropped_singleton"] == 1


def test_singleton_row_that_would_cross_the_bounds_is_left_in_place():
    # x0 in [4, 10]; row: x0 <= 3 contradicts the bound -> the row stays, no None
    red = _lp([[1, 0], [1, 1]], [4, 0], [10, 10], [-INF, 1], [3, INF])
    assert red is None  # mn > ru on row 0: the propagation names the contradiction


def test_redundant_row_is_dropped_and_contradiction_stands_down():
    red = _lp([[1, 1]], [0, 0], [1, 1], [-1], [5])
    assert red is not None and red.n_slim_rows == 0
    assert red.counts["rows_dropped_redundant"] == 1
    assert _lp([[1, 1]], [0, 0], [1, 1], [3], [INF]) is None
    assert _lp([[1, 1]], [2, 0], [1, 1], [0], [INF]) is None  # lower > upper


def test_explicit_zero_entries_are_not_columns_of_the_row():
    # the coupling rows write -pbar*a*u with a = 0: an explicit zero
    A = sp.csr_matrix(
        (np.array([1.0, 0.0]), np.array([0, 1]), np.array([0, 2])), shape=(1, 2)
    )
    red = ucslim.reduce_lp(
        A,
        np.array([0.0, 1.0]),
        np.array([0.0, 0.0]),
        np.array([5.0, 5.0]),
        np.array([2.0]),
        np.array([INF]),
    )
    assert red is not None
    # singleton on x0: x0 >= 2, row dropped; x1 untouched
    assert red.col_lower.tolist() == [2.0, 0.0] and red.n_slim_rows == 0


def test_parallel_continuous_columns_merge_and_integers_never_do():
    # x0, x1 parallel (same column, same cost); x2 same column but another
    # cost; x3 integer parallel to x0 -> not merged
    rows = [[1, 1, 1, 1], [2, 2, 2, 2]]
    red = _lp(
        rows,
        [0, 1, 0, 0],
        [2, 3, 4, 1],
        [-INF, -INF],
        [10, 20],
        cost=[5, 5, 6, 5],
        is_int=[0, 0, 0, 1],
    )
    assert red is not None
    assert red.col_map.tolist() == [0, 0, 1, 2]
    assert red.n_slim_cols == 3 and red.counts["cols_merged_parallel"] == 1
    assert red.col_lower[0] == 1.0 and red.col_upper[0] == 5.0
    assert red.col_cost.tolist() == [5.0, 6.0, 5.0]


def test_restrict_and_expand_round_trip_with_fixed_and_merged_columns():
    rows = [[1, 1, 1, 1, 1]]
    red = _lp(
        rows, [0, 1, 7, 0, 0], [2, 3, 7, 4, 1], [-INF], [100], cost=[5, 5, 1, 6, 4]
    )
    assert red is not None
    assert red.fixed_cols.tolist() == [2]
    assert red.col_map.tolist() == [0, 0, -1, 1, 2]
    x_full = np.array([1.5, 2.0, 7.0, 0.5, 1.0])
    x_slim = red.restrict(x_full)
    assert x_slim.tolist() == [3.5, 0.5, 1.0]
    back = red.expand(x_slim)
    # fixed value reinserted, singles copied, the merged pair split in index
    # order: x0 takes its lower bound 0 + min(cap 2, resid 2.5) = 2, x1 = 1 + 0.5
    assert back.tolist() == [2.0, 1.5, 7.0, 0.5, 1.0]
    assert red.restrict(back).tolist() == x_slim.tolist()
    # a full-model feasibility check of the split
    A = sp.csr_matrix(np.asarray(rows, float))
    assert (A @ back)[0] == pytest.approx((A @ x_full)[0])
    assert np.all(back >= [0, 1, 7, 0, 0]) and np.all(back <= [2, 3, 7, 4, 1])


def test_slim_index_maps_u_columns_and_names_fixed_ones():
    red = _lp([[1, 1, 1]], [0, 3, 0], [1, 3, 1], [-INF], [10], cost=[1, 2, 3])
    assert red is not None
    assert red.slim_index(np.array([0, 1, 2])).tolist() == [0, -1, 1]


def test_highs_reports_the_offset_in_objective_and_gap():
    """HiGHS 1.14 includes ``offset_`` in ``objective_function_value`` and in
    the MIP bounds the gap is measured on (the slim model's objective is the
    full window's)."""
    import highspy

    inf = highspy.kHighsInf

    def model(fixed_col: bool):
        h = highspy.Highs()
        h.setOptionValue("output_flag", False)
        n = 3 + int(fixed_col)
        lo = [0.0, 0.0, 0.0] + ([1.5] if fixed_col else [])
        up = [2.0, 2.0, 5.0] + ([1.5] if fixed_col else [])
        h.addVars(n, np.array(lo), np.array(up))
        h.changeColsCost(
            n,
            np.arange(n, dtype=np.int32),
            np.array([3.0, 2.0, 5.0] + ([7.0] if fixed_col else [])),
        )
        h.addRow(
            4.5 + (1.5 if fixed_col else 0.0),
            inf,
            n,
            np.arange(n, dtype=np.int32),
            np.ones(n),
        )
        h.changeColsIntegrality(
            2, np.array([0, 1], dtype=np.int32), [highspy.HighsVarType.kInteger] * 2
        )
        if not fixed_col:
            h.changeObjectiveOffset(10.5)
        return h

    full, slim = model(True), model(False)
    full.run()
    slim.run()
    assert slim.getInfo().objective_function_value == pytest.approx(
        full.getInfo().objective_function_value
    )
    assert slim.getInfo().mip_dual_bound == pytest.approx(full.getInfo().mip_dual_bound)
    assert slim.getLp().offset_ == 10.5


# ---------------------------------------------------------------- windows
def _state(n_int, u_prev=0.0, v_hist=None, w_hist=None, soc_prev=None):
    return WindowState(
        u_prev=np.full(n_int, float(u_prev)),
        v_hist=np.zeros((n_int, 0)) if v_hist is None else v_hist,
        w_hist=np.zeros((n_int, 0)) if w_hist is None else w_hist,
        soc_prev=soc_prev,
        p_prev=None,
        avail_prev=None,
    )


def _pair(fa, demand, mc, dk, params, noload_usd_h, state, **kw):
    """The same window built full and slim."""
    inputs = slice_window_inputs(fa, demand, dk, 0, T)
    n_int = int(params.integer_clusters.size)
    noload = np.full((n_int, T), noload_usd_h)
    full = UcWindowModel(inputs, params, mc, noload, state, slim=False, **kw)
    slim = UcWindowModel(inputs, params, mc, noload, state, slim=True, **kw)
    return full, slim


def _assert_equivalent(full_w, slim_w, warm=None, relax=False):
    a = solve_window(full_w, OPTS, warm, relax=relax)
    b = solve_window(slim_w, OPTS, warm, relax=relax)
    assert a.status == "Optimal" and b.status == "Optimal"
    assert abs(a.objective - b.objective) <= 1e-9 * max(1.0, abs(a.objective))
    if not relax:
        np.testing.assert_array_equal(a.u, b.u)
        np.testing.assert_array_equal(a.v, b.v)
        np.testing.assert_array_equal(a.w, b.w)
    assert b.col_value.shape == a.col_value.shape
    # reinsertion: the expanded slim solution satisfies every full-model bound
    col_v, row_v = ucslim.full_row_residuals(slim_w.h, b.col_value)
    assert col_v.max() <= 1e-6 and row_v.max() <= 1e-6
    # and prices nothing differently: the slim model is smaller or equal
    assert b.slim_columns <= a.columns and b.slim_rows <= a.rows
    assert b.slim_counts is not None and a.slim_counts is None
    return a, b


def test_toy_window_slim_equals_full_and_removes_something(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    full, slim = _pair(fa, demand, mc, dk, p, 200.0, _state(1))
    assert slim.slim is not None and slim.h_solve is not slim.h
    a, b = _assert_equivalent(full, slim)
    assert (b.u[0, :7] == 0).all() and (b.u[0, 7:] == 2).all()
    # zero-CF wind / solar columns are bound-fixed in the toy (cap 0)
    assert b.slim_counts["cols_fixed_by_bounds"] >= 2 * T
    assert b.slim_columns < a.columns


def test_toy_window_relaxation_agrees_on_the_slim_model(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    full, slim = _pair(fa, demand, mc, dk, p, 200.0, _state(1))
    _assert_equivalent(full, slim, relax=True)
    # integrality restored after the relaxation on the solving handle
    assert (
        slim.h_solve.getColIntegrality(int(slim.u_cols_solve()[0]))[1]
        == __import__("highspy").HighsVarType.kInteger
    )


def test_carried_min_down_history_pins_u_and_the_slim_honours_it(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, night_mw=250.0, day_mw=250.0)
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(p.dt_h[0])
    w_hist = np.zeros((1, dt - 1))
    w_hist[0, -1] = 2.0
    state = _state(1, v_hist=np.zeros((1, dt - 1)), w_hist=w_hist)
    full, slim = _pair(fa, demand, mc, dk, p, 10.0, state)
    a, b = _assert_equivalent(full, slim)
    assert (b.u[0, : dt - 1] == 0).all()
    # the pinned u (ub = n - hist_w = 0) left the slim model with its v / w
    assert (
        b.slim_counts["cols_fixed_by_bounds"]
        + b.slim_counts["cols_fixed_by_forcing"]
        + b.slim_counts["cols_fixed_by_singleton"]
        >= dt - 1
    )


def test_warm_start_restricts_to_the_slim_space_and_is_accepted(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    full, _ = _pair(fa, demand, mc, dk, p, 200.0, _state(1))
    first = solve_window(full, OPTS)
    _, slim = _pair(fa, demand, mc, dk, p, 200.0, _state(1))
    second = solve_window(slim, OPTS, warm_values=first.col_value)
    assert second.warm_accepted and second.nodes <= 1
    np.testing.assert_array_equal(second.u, first.u)
    assert abs(second.objective - first.objective) <= 1e-6 * max(
        1.0, abs(first.objective)
    )


def test_storage_boundary_survives_the_slim(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    dk = dict(
        dk,
        storage_power_cap=np.array([50.0]),
        storage_energy_cap=np.array([200.0]),
        storage_zone_idx=np.array([0]),
        eta_chg=np.array([0.95]),
        eta_dis=np.array([0.95]),
    )
    p = build_uc_cluster_params(fa, "NEISO")
    full, slim = _pair(
        fa,
        demand,
        mc,
        dk,
        p,
        200.0,
        _state(1, soc_prev=np.array([120.0])),
        soc_terminal=np.array([150.0]),
    )
    a, b = _assert_equivalent(full, slim)
    soc = b.storage_soc[0]
    chg = b.col_value[slim.layout.chg_col(0, 0)]
    dis = b.col_value[slim.layout.dis_col(0, 0)]
    assert abs(soc[0] - (120.0 + 0.95 * chg - dis / 0.95)) < 1e-6
    assert soc[T - 1] >= 150.0 - 1e-6
    # the SOC path itself is degenerate (an equal-cost charge can sit in
    # either of two hours), so only the boundary and the objective are held
    assert a.storage_soc[0, T - 1] >= 150.0 - 1e-6


def test_infeasible_window_is_diagnosed_on_the_full_model(uc_params_frame):
    """A contradiction stands the reduction down: the window solves on the
    full handle and the existing report (relaxation status, zero-LP
    diagnosis) is what fires."""
    _, fa, demand, mc, dk = toy_inputs(T, night_mw=250.0, day_mw=250.0)
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(p.dt_h[0])
    w_hist = np.zeros((1, dt - 1))
    w_hist[0, -1] = 2.0
    state = WindowState(
        u_prev=np.array(
            [2.0]
        ),  # both units on at t0-1 while both stopped: a logic contradiction
        v_hist=np.zeros((1, dt - 1)),
        w_hist=w_hist,
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    inputs = slice_window_inputs(fa, demand, dk, 0, T)
    fa_floor = inputs.fleet
    # a min_gen floor on the CC that the stopped units cannot carry
    min_gen = np.zeros((fa.n_gen, T))
    min_gen[0, :] = 150.0
    import dataclasses

    inputs = dataclasses.replace(
        inputs, fleet=dataclasses.replace(fa_floor, min_gen=min_gen)
    )
    w = UcWindowModel(inputs, p, mc, np.full((1, T), 10.0), state, slim=True)
    with pytest.raises(UcWindowInfeasible) as exc:
        solve_window(w, OPTS, window_index=3, t0=0, t1=T)
    assert exc.value.window_index == 3
    assert exc.value.diagnosis is not None and exc.value.relaxation_status


def test_stage_schedule_is_the_same_with_the_slim_on_and_off(
    uc_params_frame, uc_results_root
):
    from market_sim.pipeline.solve import run_energy_solve
    from market_sim.pipeline.uc import take_uc_stages

    T2 = 72
    gens, fa, demand, mc, dk = toy_inputs(T2, day_mw=190.0)
    logs = {}
    for slim in (False, True):
        cfg = ScenarioConfig(
            iso="NEISO",
            hours=T2,
            unit_commitment_milp=True,
            uc_window_hours=24,
            uc_lookahead_hours=12,
            uc_mip_rel_gap=1e-6,
            uc_slim_window=slim,
        )
        res = run_energy_solve(gens, fa, demand, mc, dk, cfg)
        stage = take_uc_stages()[-1]
        logs[slim] = (stage.schedule.u.copy(), stage.log, res)
    u_off, log_off, r_off = logs[False]
    u_on, log_on, r_on = logs[True]
    np.testing.assert_array_equal(u_on, u_off)
    for w_on, w_off in zip(log_on["windows"], log_off["windows"]):
        assert abs(w_on["objective"] - w_off["objective"]) <= 1e-6 * max(
            1.0, abs(w_off["objective"])
        )
        assert w_on["slim"]["reduced"] and not w_off["slim"]["reduced"]
        assert w_on["slim"]["columns"] < w_off["slim"]["columns"] == w_off["columns"]
    assert log_on["engine"]["fields"]["uc_slim_window"] is True
    assert log_on["summary"]["slim_sums"]["windows_reduced"] == len(log_on["windows"])
    assert "slim_s" in log_on["summary"]["phase_sums"]
    # P1 is scored on the same bounds: identical dispatch
    np.testing.assert_allclose(r_on.p1.dispatch, r_off.p1.dispatch, atol=1e-6)


def test_slim_field_is_registered_at_its_default():
    from market_sim.config import scenarios as sc

    assert "uc_slim_window" in sc._CACHE_KEY_OPTIONAL_FIELDS
    assert sc._CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["uc_slim_window"] == "True"
    assert ScenarioConfig().uc_slim_window is True
    on = ScenarioConfig(unit_commitment_milp=True)
    off = ScenarioConfig(unit_commitment_milp=True, uc_slim_window=False)
    assert on.cache_key() != off.cache_key()
    assert (
        ScenarioConfig().cache_key() == ScenarioConfig(uc_slim_window=True).cache_key()
    )
