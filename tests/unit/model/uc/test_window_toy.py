"""Ladder rung L0: the toy UC window (GATESPEC section 3; DESIGN section 6).

1 cluster / 1 zone / 24 h: a positive no-load decommits the cluster through
the night (the LP relaxation cannot), min-up / min-down hold, a warm start
from the window's own solution is accepted, and an empty integer set solves
the sliced LP exactly.
"""

from __future__ import annotations

import numpy as np

from market_sim.model.dispatch import solve_dispatch
from market_sim.model.uc.params import build_uc_cluster_params, units_online_profile
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs

from .conftest import toy_inputs, toy_uc_params

T = 24
OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)


def _window(
    fa,
    demand,
    mc,
    dk,
    params,
    u_prev,
    noload_usd_h,
    t0=0,
    t1=T,
    v_hist=None,
    w_hist=None,
):
    inputs = slice_window_inputs(fa, demand, dk, t0, t1)
    n_int = int(params.integer_clusters.size)
    state = WindowState(
        u_prev=np.full(n_int, float(u_prev)),
        v_hist=np.zeros((n_int, 0)) if v_hist is None else v_hist,
        w_hist=np.zeros((n_int, 0)) if w_hist is None else w_hist,
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    noload = np.full((n_int, t1 - t0), noload_usd_h)
    return UcWindowModel(inputs, params, mc[:, t0:t1], noload, state)


def test_cluster_params_from_toy(uc_params_frame):
    _, fa, _, _, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    # CC (integer: NREL f-class min-down 6 h, $48.6/MW) and CT (fast-start) are
    # clusters; the nuclear row is outside the candidate set.
    assert p.n_clusters == 2
    assert list(p.family) == ["cc", "ct"]
    assert p.integer.tolist() == [True, False]
    assert p.n_units[0] == 2 and p.pbar_mw[0] == 100.0 and p.mlf[0] == 0.5
    assert p.ut_h[0] == 6 and p.dt_h[0] == 4
    assert p.noload_mmbtu_h[0] == 50.0  # 100 MMBtu/h plant / 2 units
    assert p.src_noload[0] == "uc-params" and p.src_mlf[1].startswith("MIN_STABLE")


def test_noload_decommit_and_relaxation_fraction(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p, u_prev=0, noload_usd_h=200.0)
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.u[0, :7] == 0).all()  # off through the night
    assert (res.u[0, 7:] == 2).all()  # 130 MW of CC needs both units
    # The relaxation: u = P / pbar = 1.3 in the day, 0 at night.
    w2 = _window(fa, demand, mc, dk, p, u_prev=0, noload_usd_h=200.0)
    rel = solve_window(w2, OPTS, relax=True)
    x = rel.col_value[w2.U0 : w2.V0].reshape(T, 1)[:, 0]
    assert np.all(x[7:] < 2.0 - 1e-6) and np.all(x[7:] > 1.0 + 1e-6)
    assert rel.objective <= res.objective + 1e-6


def test_min_up_holds_a_two_hour_spike(uc_params_frame):
    """A 2-hour spike that needs the CC: with ut = 6 the unit, once started,
    stays on for at least six hours (or the spike is served otherwise)."""
    _, fa, demand, mc, dk = toy_inputs(
        T, with_baseload=True, night_mw=40.0, day_mw=40.0
    )
    demand[0, 10:12] = 300.0  # baseload 60 + CT 150 < 300: the CC must run
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p, u_prev=0, noload_usd_h=50.0)
    res = solve_window(w, OPTS)
    u = res.u[0]
    assert u[10] >= 1 and u[11] >= 1
    on = np.flatnonzero(u > 0)
    assert on.size >= 6, u
    assert res.v[0].sum() >= 1


def test_min_down_holds_after_a_stop(uc_params_frame):
    """Carried stops: a unit stopped 1 h before t0 cannot restart until dt = 4."""
    _, fa, demand, mc, dk = toy_inputs(T, night_mw=250.0, day_mw=250.0)
    p = build_uc_cluster_params(fa, "NEISO")
    n_int = 1
    w_hist = np.zeros((n_int, 3))
    w_hist[0, -1] = 2.0  # both units stopped in hour t0-1
    w = _window(
        fa,
        demand,
        mc,
        dk,
        p,
        u_prev=0,
        noload_usd_h=10.0,
        v_hist=np.zeros((n_int, 3)),
        w_hist=w_hist,
    )
    res = solve_window(w, OPTS)
    # hours 0..2 (dt - 1 = 3 hours after the stop) cannot carry a unit...
    assert (res.u[0, :3] == 0).all(), res.u
    # ...and the demand there is served by the CT + baseload, with slack only
    # if physically needed (250 - 60 - 150 = 40 MW of slack: priced at VOLL).
    assert res.u[0, 3:].max() >= 1


def test_warm_start_from_own_solution_is_accepted_at_the_root(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p, u_prev=0, noload_usd_h=200.0)
    first = solve_window(w, OPTS)
    w2 = _window(fa, demand, mc, dk, p, u_prev=0, noload_usd_h=200.0)
    second = solve_window(w2, OPTS, warm_values=first.col_value)
    assert second.warm_accepted
    # HiGHS counts the root as one node; a warm-started integral root needs no branching.
    assert second.nodes <= 1
    np.testing.assert_array_equal(second.u, first.u)
    assert abs(second.objective - first.objective) <= 1e-6 * max(
        1.0, abs(first.objective)
    )


def test_integer_empty_equals_the_sliced_lp(uc_params_frame):
    """Every cluster failing E1 (a CT-only fleet): the window objective and
    dispatch equal the plain sliced LP's."""
    _, fa, demand, mc, dk = toy_inputs(T)
    frame = toy_uc_params()
    frame.loc[0, "plant_code"] = 999  # the CC plant has no measured row ...
    uc_params_frame(frame)
    p = build_uc_cluster_params(fa, "NEISO")
    p = type(p)(**{**p.__dict__, "integer": np.zeros(p.n_clusters, dtype=bool)})
    assert p.integer_clusters.size == 0
    w = _window(fa, demand, mc, dk, p, u_prev=0, noload_usd_h=0.0)
    res = solve_window(w, OPTS)
    assert res.integers == 0 and res.columns == w.n_lp
    lp = solve_dispatch(fa, demand, mc=mc, **dk)
    assert abs(res.objective - lp.objective_value) <= 1e-6 * max(
        1.0, abs(lp.objective_value)
    )
    np.testing.assert_allclose(res.dispatch, lp.dispatch, atol=1e-6)


def test_units_online_profile_rounds_up(uc_params_frame):
    _, fa, _, _, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    d = np.zeros((fa.n_gen, 4))
    d[0, :] = [0.0, 1.0, 100.0, 150.0]
    u = units_online_profile(p, d)
    assert u[0].tolist() == [0, 1, 1, 2]
