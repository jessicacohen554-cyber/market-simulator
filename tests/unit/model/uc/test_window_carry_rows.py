"""The rolling-horizon carry: history inside the Rajan–Takriti rows, the look-ahead guard.

FINDING-ucmilp-1-fix-window-infeasibility-2026-10-04 (UC-1-FIX): with the
carried min-up / min-down history enforced as a separate ``u`` column bound,
a window could stop a unit still inside its min-up whenever another unit's
earlier start satisfied the bound alone; the kept history then held more
starts within one min-up than the plant has units and a later window raised
``UcWindowInfeasible`` (SPP 2020, every year of the keeper span). Trivial
cases first (one cluster, one zone, a few hours), then the stage over a toy
horizon that reproduces the SPP chain and the look-ahead floor collision.
"""

from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.floor_mechanisms import MECH_UC_SCHEDULE
from market_sim.model.uc.params import build_uc_cluster_params, units_needed_for_floor
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import (
    UcWindowInfeasible,
    UcWindowModel,
    WindowState,
    slice_window_inputs,
)
from market_sim.pipeline.solve import run_energy_solve

from .conftest import toy_inputs, toy_uc_params

OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)


def _window(
    fa, demand, mc, dk, params, u_prev, noload_usd_h, v_hist=None, w_hist=None, **kw
):
    T_w = demand.shape[1]
    inputs = slice_window_inputs(fa, demand, dk, 0, T_w)
    n_int = int(params.integer_clusters.size)
    state = WindowState(
        u_prev=np.full(n_int, float(u_prev)),
        v_hist=np.zeros((n_int, 0)) if v_hist is None else v_hist,
        w_hist=np.zeros((n_int, 0)) if w_hist is None else w_hist,
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    noload = np.full((n_int, T_w), noload_usd_h)
    return UcWindowModel(inputs, params, mc, noload, state, **kw)


def _joint_physics(u, v, w, n, ut, dt):
    """Violations of min-up / min-down over the FULL history of a stitched schedule."""
    tt = np.arange(u.size)
    cv = np.concatenate([[0], np.cumsum(v)])
    cw = np.concatenate([[0], np.cumsum(w)])
    starts = cv[tt + 1] - cv[np.maximum(tt + 1 - ut, 0)]
    stops = cw[tt + 1] - cw[np.maximum(tt + 1 - dt, 0)]
    return int((starts > u).sum()), int((stops > n - u).sum())


# --------------------------------------------------------------------------- #
# One window, carried history                                                 #
# --------------------------------------------------------------------------- #
def test_min_up_history_and_window_start_are_summed(uc_params_frame):
    """Unit A started at t0-1 (history), unit B starts at hour 1: BOTH stay on.

    With ut = 6 the history alone bounds u >= 1 until hour 4 and the window's
    own start bounds u >= 1 until hour 6; the row sums them, so u = 2 holds
    through hour 4 even though one unit would do from hour 3 on.
    """
    uc_params_frame(toy_uc_params(ut_h=6, dt_h=4, noload_mmbtu_h=100.0))
    T_w = 12
    _, fa, demand, mc, dk = toy_inputs(T_w, night_mw=160.0, day_mw=160.0)
    demand[0, 1:3] = 260.0  # baseload 60 + both CC units
    p = build_uc_cluster_params(fa, "NEISO")
    v_hist = np.zeros((1, 5))
    v_hist[0, -1] = 1.0  # A started in hour t0-1
    w = _window(
        fa,
        demand,
        mc,
        dk,
        p,
        u_prev=1,
        noload_usd_h=300.0,
        v_hist=v_hist,
        w_hist=np.zeros((1, 5)),
    )
    res = solve_window(w, OPTS)
    u = res.u[0]
    assert (u[1:5] == 2).all(), (
        u
    )  # A (until hour 4) and B (until hour 6) both inside min-up
    assert (u[5:7] >= 1).all(), u
    assert u[7:].max() == 1, u  # one unit serves 160 MW once both min-ups are served


def test_min_down_history_and_window_stop_are_summed(uc_params_frame):
    """A unit stopped at t0-1 (history) and a unit the window stops cannot both
    be online again before their min-down — the illegal restart the separate
    bound allowed is refused, so the spike is served by the CT and slack."""
    uc_params_frame(toy_uc_params(ut_h=1, noload_mmbtu_h=100.0))
    T_w = 8
    _, fa, demand, mc, dk = toy_inputs(T_w, night_mw=40.0, day_mw=40.0)
    demand[0, 2] = 400.0  # baseload 60 + CT 150 < 400: a CC unit would be worth a lot
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(
        p.dt_h[0]
    )  # the PUBLISHED class min-down (6 h for the toy CC), never uc-params'
    assert dt >= 4
    w_hist = np.zeros((1, dt - 1))
    w_hist[0, -1] = 1.0  # B stopped in hour t0-1
    # The no-load is large enough that stopping A for two hours beats its
    # start cost, so the window WANTS "stop at 0, restart at 2" — illegal for
    # both units (A off 2 h, B off 3 h, min-down 4 h).
    w = _window(
        fa,
        demand,
        mc,
        dk,
        p,
        u_prev=1,
        noload_usd_h=5000.0,
        v_hist=np.zeros((1, 3)),
        w_hist=w_hist,
    )
    res = solve_window(w, OPTS)
    u, v, ww = res.u[0], res.v[0], res.w[0]
    # the joint min-down holds against the full history in every hour
    hist_stop_hour = -1
    for tau in range(T_w):
        recent = ww[max(0, tau - 3) : tau + 1].sum() + (
            1 if tau - hist_stop_hour < 4 else 0
        )
        assert recent + u[tau] <= 2, (tau, u, ww)
    # and since a restart at hour 2 is impossible, A stays on to serve the spike
    assert u[2] == 1 and v[2] == 0, (u, v)


def test_units_needed_for_floor_uses_the_lp_effective_floor(uc_params_frame):
    """A floor above the available capacity is clipped exactly as the LP clips
    the P lower bound: the UC never asks for a unit the LP's own floor does not."""
    T_w = 6
    _, fa, demand, mc, dk = toy_inputs(T_w, night_mw=100.0, day_mw=100.0)
    p = build_uc_cluster_params(fa, "NEISO")
    mg = np.zeros((fa.n_gen, T_w))
    mg[0, :] = 150.0  # 1.5 units of floor on a 2 x 100 MW plant
    av = np.array(fa.availability, copy=True)
    av[0, 2:4] = 0.25  # only 50 MW available in hours 2-3
    fa2 = dataclasses.replace(fa, min_gen=mg, availability=av)
    need = units_needed_for_floor(p, fa2, 0, T_w)[0]
    assert need.tolist() == [2, 2, 1, 1, 2, 2]


def test_infeasible_window_names_itself_and_dumps(uc_params_frame, tmp_path):
    """An impossible carried state (u_prev above n) raises with the window
    index, the LP-relaxation status, the a-priori diagnosis and the dump."""
    T_w = 6
    _, fa, demand, mc, dk = toy_inputs(T_w)
    p = build_uc_cluster_params(fa, "NEISO")
    w = _window(fa, demand, mc, dk, p, u_prev=5, noload_usd_h=10.0)
    opts = dataclasses.replace(OPTS, debug_dump_dir=tmp_path / "dump")
    with pytest.raises(UcWindowInfeasible) as exc:
        solve_window(w, opts, window_index=7, t0=168, t1=174)
    e = exc.value
    assert e.window_index == 7 and e.t0 == 168 and e.t1 == 174
    assert "window 7 [168, 174)" in str(e)
    assert e.relaxation_status == "Infeasible"
    assert e.diagnosis["contradictory_rows"]["logic"]["count"] >= 1
    files = {f.name for f in (tmp_path / "dump").iterdir()}
    assert files == {"window_7.mps", "window_7_state.npz", "window_7_diagnosis.json"}
    rep = json.loads((tmp_path / "dump" / "window_7_diagnosis.json").read_text())
    assert (
        rep["contradictory_rows"]["logic"]["count"]
        == e.diagnosis["contradictory_rows"]["logic"]["count"]
    )


# --------------------------------------------------------------------------- #
# The stage over a toy horizon                                                #
# --------------------------------------------------------------------------- #
def _stage_schedule(res):
    import market_sim.pipeline.uc as puc

    stage = puc.take_uc_stages()[-1]
    return stage, stage.schedule


def test_spp_pattern_three_starts_within_one_min_up(uc_params_frame, uc_results_root):
    """The SPP 2020 chain in miniature (plants 2965 / 2817: two units, a long
    measured min-up, three starts carried within one min-up, a later window
    bounded above n). ut = 16, W = 6, L = 3: A starts at hour 4, B at hour 6;
    the old engine stopped one at hour 7 (both inside min-up), re-started it
    at hour 12 under its own history bound and raised at window 3 with a
    carried lower bound of 3 on a 2-unit plant. The fixed engine completes
    and the stitched schedule obeys min-up / min-down against its full history.
    """
    uc_params_frame(toy_uc_params(ut_h=16, noload_mmbtu_h=100.0))
    T = 48
    gens, fa, demand, mc, dk = toy_inputs(T, night_mw=160.0, day_mw=160.0)
    demand[0, 0:4] = 40.0
    demand[0, 6] = 420.0  # baseload 60 + CT 150 < 420: B must start
    demand[0, 44:48] = (
        40.0  # P0 has the plant off at hour T-1: the first state is u = 0
    )
    cfg = ScenarioConfig(
        iso="NEISO",
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=6,
        uc_lookahead_hours=3,
    )
    res = run_energy_solve(gens, fa, demand, mc, dk, cfg)
    stage, sched = _stage_schedule(res)
    assert sched.is_complete()
    u, v, w = sched.u[0].astype(int), sched.v[0].astype(int), sched.w[0].astype(int)
    assert u.max() <= 2 and (u >= 0).all()
    assert _joint_physics(u, v, w, 2, 16, 4) == (0, 0), (u, v, w)
    assert u[6] == 2 and (u[6:14] == 2).all(), (
        u
    )  # A (4..19) and B (6..21) both inside min-up
    assert all(win["status"] == "Optimal" for win in stage.log["windows"])
    # the P1 fleet carries the schedule as bounds under MECH 28
    p1f = res.p1_fleet_arrays
    assert set(np.unique(p1f.min_gen_mechanism[0][u > 0]).tolist()) == {
        MECH_UC_SCHEDULE
    }


def test_floor_beyond_the_horizon_is_guarded_against_min_down(
    uc_params_frame, uc_results_root
):
    """A structural floor that turns on just past window 0's horizon needs both
    units of a plant that ran to hour 21 and would stop at 22; its min-down
    (the published 6 h) reaches the floor hour. The old engine stopped them,
    then window 1 inherited a floor its min-down could not honour. The guard
    row keeps them on, so the floor is met with the physics intact."""
    uc_params_frame(toy_uc_params(ut_h=4, noload_mmbtu_h=100.0))
    T = 72
    W, L = 24, 2
    gens, fa, demand, mc, dk = toy_inputs(T, night_mw=40.0, day_mw=40.0)
    demand[0, 0:22] = 420.0  # both units needed through hour 21
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(p.dt_h[0])
    assert dt >= L + 2, "the collision needs a min-down longer than the look-ahead"
    h_floor = W + L  # the first hour window 0 cannot see
    mg = np.zeros((fa.n_gen, T))
    mg[0, h_floor] = 200.0  # one-hour floor on the whole plant
    mech = np.zeros((fa.n_gen, T), dtype=np.int8)
    mech[0, h_floor] = 1
    fa = dataclasses.replace(fa, min_gen=mg, min_gen_mechanism=mech)
    cfg = ScenarioConfig(
        iso="NEISO",
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=W,
        uc_lookahead_hours=L,
    )
    res = run_energy_solve(gens, fa, demand, mc, dk, cfg)
    stage, sched = _stage_schedule(res)
    assert sched.is_complete()
    u, v, w = sched.u[0].astype(int), sched.v[0].astype(int), sched.w[0].astype(int)
    assert u[h_floor] == 2, u
    assert _joint_physics(u, v, w, 2, 4, dt) == (0, 0), (u, v, w)
    assert (u[h_floor - dt + 1 : h_floor + 1] == 2).all(), (
        u
    )  # no stop inside the floor hour's min-down
    assert stage.log["windows"][0]["guard_rows"] >= 1
    assert res.p1.dispatch[0, h_floor] >= 200.0 - 1e-6


def test_floor_above_availability_solves_gate_off_and_on(
    uc_params_frame, uc_results_root
):
    """A floor the available capacity cannot carry in some hours: P0 clips the
    P lower bound to pmax * availability; gate off and gate on both solve and
    the gate-on schedule respects the clipped floor (all units on, the
    plant's output at the clipped level)."""
    uc_params_frame(toy_uc_params(ut_h=4, noload_mmbtu_h=100.0))
    T = 48
    gens, fa, demand, mc, dk = toy_inputs(T, night_mw=100.0, day_mw=100.0)
    mg = np.zeros((fa.n_gen, T))
    mg[0, 8:20] = 200.0  # the whole plant
    av = np.array(fa.availability, copy=True)
    av[0, 12:16] = 0.5  # 100 MW available: the 200 MW floor exceeds it
    mech = np.zeros((fa.n_gen, T), dtype=np.int8)
    mech[0, 8:20] = 1
    fa = dataclasses.replace(fa, min_gen=mg, min_gen_mechanism=mech, availability=av)
    off = run_energy_solve(
        gens, fa, demand, mc, dk, ScenarioConfig(iso="NEISO", hours=T)
    )
    assert off.p1.dispatch[0, 12:16].min() >= 100.0 - 1e-6
    cfg = ScenarioConfig(
        iso="NEISO",
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=24,
        uc_lookahead_hours=12,
    )
    on = run_energy_solve(gens, fa, demand, mc, dk, cfg)
    stage, sched = _stage_schedule(on)
    assert sched.is_complete()
    u = sched.u[0].astype(int)
    assert (u[8:20] == 2).all(), u
    p1f = on.p1_fleet_arrays
    # the clipped floor rides into P1: 200 MW where available, 100 MW where not
    assert np.allclose(on.p1.dispatch[0, 8:12], 200.0, atol=1e-6)
    assert np.allclose(on.p1.dispatch[0, 12:16], 100.0, atol=1e-6)
    assert (
        p1f.min_gen[0, 8:20] <= p1f.pmax[0] * p1f.availability[0, 8:20] + 1e-9
    ).all()
