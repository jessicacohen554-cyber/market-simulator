"""uc-1.6: reserve headroom on an integer cluster is its COMMITTED capacity.

1 cluster / 1 zone / 24 h (FINDING-ucmilp-fix6-reserve-headroom-2026-10-14).
The toy CC (2 x 100 MW, min-stable 0.5) is the one integer cluster; the night
load (40 MW) is below its min-load, so with no reserve need a positive
no-load decommits it. A reserve requirement the CC alone may carry then
forces the minimum commitment the requirement implies: at R = 80 MW one unit
(100 MW online, >= 50 MW min-load) carries at most 50 MW, so both units are
online every hour (200 MW online, P >= 100, headroom <= 100 >= 80). An
offline cluster (u = 0) carries no reserve. With no reserve co-optimization
the window is the uc-1.5 window (no coefficient, no right-hand-side edit).
"""

from __future__ import annotations

import numpy as np

from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import (
    UcWindowModel,
    WindowState,
    _lp_matrix_csc,
    reserve_headroom_u_terms,
    slice_window_inputs,
)

from .conftest import toy_inputs

T = 24
OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)
#: Shortfall penalty far above any energy cost: the requirement is met when it can be.
PENALTY = 1000.0


def _reserve_kwargs(dk: dict, req_mw: float, eligible: list[bool], hard: bool = False):
    kw = dict(dk)
    kw["reserve_requirement"] = np.full(T, req_mw)
    kw["reserve_eligible"] = np.asarray(eligible, dtype=bool)
    if not hard:
        kw["ordc_penalties"] = np.array([PENALTY])
        kw["ordc_step_widths"] = np.array([req_mw])
    return kw


def _window(fa, demand, mc, dk, params, *, u_prev=0.0, fix_off=None, noload=200.0):
    inputs = slice_window_inputs(fa, demand, dk, 0, T)
    n_int = int(params.integer_clusters.size)
    state = WindowState(
        u_prev=np.full(n_int, float(u_prev)),
        v_hist=np.zeros((n_int, 0)),
        w_hist=np.zeros((n_int, 0)),
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    return UcWindowModel(
        inputs,
        params,
        mc,
        np.full((n_int, T), noload),
        state,
        fix_off=fix_off,
    )


def _reserve_mw(window: UcWindowModel, res) -> np.ndarray:
    lay = window.layout
    block = res.col_value[: window.n_lp].reshape(T, lay.vars_per_hour)
    return block[:, lay._reserve_off : lay._reserve_off + lay.n_reserve].sum(axis=1)


def test_no_reserve_requirement_adds_nothing(uc_params_frame):
    """G-OFF at the window: no co-opt -> no u coefficient, no RHS edit."""
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p)
    assert w.n_reserve_gated_rows == 0
    A = _lp_matrix_csc(w.h)
    n_lp_rows = int(w.h.getNumRow()) - int(w._n_uc_rows)
    # The u/v/w columns hold entries in the UC rows only, none in the LP's.
    uvw = A[:, w.U0 :].tocoo()
    assert uvw.nnz and np.all(uvw.row >= n_lp_rows)
    res = solve_window(w, OPTS)
    assert (res.u[0, :7] == 0).all()  # the uc-1.5 night decommit


def test_requirement_forces_min_commit(uc_params_frame):
    """R = 80 MW on the CC alone: both units online every hour."""
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    kw = _reserve_kwargs(dk, 80.0, [True, False, False])
    w = _window(fa, demand, mc, kw, p)
    assert w.n_reserve_gated_rows == T
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.u[0, :] == 2).all()
    r = _reserve_mw(w, res)
    np.testing.assert_allclose(r, 80.0, atol=1e-6)
    cc = res.dispatch[0]
    assert np.all(cc >= 100.0 - 1e-6) and np.all(200.0 - cc >= r - 1e-6)


def test_offline_cluster_carries_no_reserve(uc_params_frame):
    """u fixed at 0: the cluster provides 0 MW; the whole requirement is short."""
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    kw = _reserve_kwargs(dk, 80.0, [True, False, False])
    w = _window(
        fa, demand, mc, kw, p, fix_off=np.ones(p.integer_clusters.size, dtype=bool)
    )
    res = solve_window(w, OPTS)
    assert (res.u == 0).all()
    np.testing.assert_allclose(_reserve_mw(w, res), 0.0, atol=1e-6)


def test_one_unit_bound_is_committed_capacity(uc_params_frame):
    """R = 30 MW: one unit suffices (100 online - 50 min-load >= 30) at night."""
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    kw = _reserve_kwargs(dk, 30.0, [True, False, False], hard=True)
    w = _window(fa, demand, mc, kw, p)
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.u[0, :7] == 1).all()
    r = _reserve_mw(w, res)
    # Every hour: reserve <= committed capacity - CC output.
    cap_on = 100.0 * res.u[0]
    assert np.all(r <= cap_on - res.dispatch[0] + 1e-6)


def test_fast_start_member_keeps_offline_credit(uc_params_frame):
    """A non-integer (fast-start CT) member keeps pmax*a: no commitment forced."""
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    kw = _reserve_kwargs(dk, 80.0, [True, False, True])
    w = _window(fa, demand, mc, kw, p)
    res = solve_window(w, OPTS)
    assert (res.u[0, :7] == 0).all()  # the CT's offline 150 MW covers 80 MW
    np.testing.assert_allclose(_reserve_mw(w, res), 80.0, atol=1e-6)


def test_u_terms_pergen_pools(uc_params_frame):
    """Per-generator joint rows: the same -pmax*a/n entries, one per pool-hour."""
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    kw = dict(dk)
    kw["reserve_requirement"] = np.full(T, 80.0)
    kw["reserve_pergen_gen_idx"] = np.array([0])
    kw["reserve_pergen_ramp10"] = np.array([200.0])
    kw["ordc_penalties"] = np.array([PENALTY])
    kw["ordc_step_widths"] = np.array([80.0])
    w = _window(fa, demand, mc, kw, p)
    rows, u_local, vals, _, cut = reserve_headroom_u_terms(
        w.model, p, slice_window_inputs(fa, demand, kw, 0, T).kwargs, 0
    )
    assert rows.size == T  # one CC pool row per hour
    np.testing.assert_allclose(vals, -100.0)  # 200 MW / 2 units
    np.testing.assert_allclose(cut, 200.0)
    res = solve_window(w, OPTS)
    assert (res.u[0, :] == 2).all()
