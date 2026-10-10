"""The look-ahead guard sees the floors the next window will hold (engine uc-1.2).

FINDING-ucmilp-fix2-floor-mindown-2026-10-10 (UC-1-FIX-2): with MISO's coal
yard budget armed (``coal_fuel_inventory_plant_grain``) every yard row is a
dropped budget family inside a window, pinned to its P0 dispatch through its
``availability`` (``P0 / pmax``) and ``min_gen`` (``P0``). The window's row (a)
then needs every unit online wherever the pinned output is positive, but the
look-ahead guard read its floor needs on the UNPINNED year fleet (and divided
by ``pbar`` alone, not the ``pbar * a`` row (a) carries), saw none, and let a
window stop units a later window's pin needed inside their min-down
(``UcWindowInfeasible`` mid-year, MISO 2020-2025). Trivial cases first (one
cluster, a few hours), then the stage over a toy horizon.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.uc.params import (
    build_uc_cluster_params,
    demote_budget_pinned,
    units_needed_for_floor,
)
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import (
    UcWindowInfeasible,
    UcWindowModel,
    WindowState,
    slice_window_inputs,
    window_fleet,
)
from market_sim.pipeline.uc import UcStage

from .conftest import toy_generators, toy_inputs, toy_uc_params

OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)

#: The budget key the toy pins the CC plant (fleet row 0) with: MISO's yard family.
PIN = {"coal_plant_gen_idx": np.array([0])}


# --------------------------------------------------------------------------- #
# The unit need: row (a)'s own count, on the pinned fleet                     #
# --------------------------------------------------------------------------- #
def test_pinned_row_needs_every_unit_the_unpinned_fleet_does_not(uc_params_frame):
    """A row pinned to P0 = 150 MW on a 2 x 100 MW plant has availability 0.75;
    row (a) then carries 75 MW per unit and needs both units (and at 50 MW,
    25 MW per unit: still both). The unpinned year fleet has no floor at all,
    which is what the uc-1.1 guard read."""
    T = 4
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    p0 = np.zeros((fa.n_gen, T))
    p0[0, :] = [0.0, 150.0, 50.0, 200.0]
    fleet_w, pinned = window_fleet(fa, {**dk, **PIN}, 0, T, p0)
    assert pinned.tolist() == [0]
    assert units_needed_for_floor(p, fleet_w, 0, T)[0].tolist() == [0, 2, 2, 2]
    assert units_needed_for_floor(p, fa, 0, T)[0].tolist() == [0, 0, 0, 0]


def test_window_fleet_is_hour_local(uc_params_frame):
    """The guard's slice and the next window's slice agree hour by hour: the
    fleet of ``[h0, h1)`` is the same rows of any window that covers them."""
    T = 12
    _, fa, demand, mc, dk = toy_inputs(T)
    p0 = np.zeros((fa.n_gen, T))
    p0[0, :] = np.linspace(0.0, 200.0, T)
    wide, _ = window_fleet(fa, {**dk, **PIN}, 2, 10, p0)
    narrow, _ = window_fleet(fa, {**dk, **PIN}, 5, 8, p0)
    assert np.array_equal(wide.availability[:, 3:6], narrow.availability)
    assert np.array_equal(wide.min_gen[:, 3:6], narrow.min_gen)
    inputs = slice_window_inputs(fa, demand, {**dk, **PIN}, 5, 8, p0)
    assert np.array_equal(inputs.fleet.availability, narrow.availability)


def test_window_bound_matches_row_a_under_a_pin(uc_params_frame):
    """One window, one cluster, the pin at 50 MW: the ``u`` lower bound is 2
    (row (a)'s count), and a carried min-down holding one unit off makes the
    window infeasible with the plant, its pinned rows and the hours NAMED in
    the exception text (the MISO lane could not name plants)."""
    T_w = 4
    _, fa, demand, mc, dk = toy_inputs(T_w, night_mw=110.0, day_mw=110.0)
    p = build_uc_cluster_params(fa, "NEISO")
    p0 = np.zeros((fa.n_gen, T_w))
    p0[0, :] = 50.0
    inputs = slice_window_inputs(fa, demand, {**dk, **PIN}, 0, T_w, p0)
    dt = int(p.dt_h[0])
    w_hist = np.zeros((1, dt - 1))
    w_hist[0, -1] = 1.0  # one unit stopped at t0 - 1, inside its min-down
    state = WindowState(
        u_prev=np.ones(1),
        v_hist=np.zeros((1, dt - 1)),
        w_hist=w_hist,
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    w = UcWindowModel(inputs, p, mc, np.full((1, T_w), 10.0), state)
    assert w.u_lower[0].tolist() == [2.0] * T_w
    with pytest.raises(UcWindowInfeasible) as exc:
        solve_window(w, OPTS, window_index=3, t0=72, t1=76)
    rows = exc.value.diagnosis["clusters_floor_above_min_down"]
    assert rows and rows[0]["plant_code"] == 1 and rows[0]["pinned_members"] == 1
    assert "plant 1 cc (n=2" in str(exc.value) and "pinned 1/1" in str(exc.value)


# --------------------------------------------------------------------------- #
# The stage                                                                   #
# --------------------------------------------------------------------------- #
class _P0:
    """A synthetic P0 result (the stage reads dispatch / prices / SOC / flows)."""

    def __init__(self, dispatch: np.ndarray, n_zones: int) -> None:
        self.dispatch = dispatch
        self.prices = np.full((n_zones, dispatch.shape[1]), 30.0)
        self.storage_soc = None
        self.flows = None


T_STAGE, W_STAGE, L_STAGE = 72, 24, 2


def _stage(tmp_path, fa, demand, mc, dk, p0):
    cfg = ScenarioConfig(
        iso="NEISO",
        hours=T_STAGE,
        unit_commitment_milp=True,
        uc_window_hours=W_STAGE,
        uc_lookahead_hours=L_STAGE,
    )
    return UcStage(
        cfg,
        fa,
        demand,
        dk,
        mc,
        _P0(p0, demand.shape[0]),
        None,
        lambda: mc,
        checkpoint_root=tmp_path,
    )


def _p0_off_then_on(fa, on_mw_after: float) -> np.ndarray:
    """The CC plant runs both units to hour 21, idles to window 0's horizon, runs again after."""
    p0 = np.zeros((fa.n_gen, T_STAGE))
    p0[0, 0:22] = 200.0
    p0[0, W_STAGE + L_STAGE :] = on_mw_after
    p0[0, T_STAGE - 1] = 200.0  # the cyclic first state: both units on
    p0[1, :] = 60.0
    return p0


def test_all_pinned_cluster_carries_no_integer(uc_params_frame, tmp_path):
    """UC-DESK ruling (option (a)): a cluster whose members are ALL budget-pinned
    has its commitment fixed by the identity (P0), so it carries no ``u``. The
    stage drops its integer, logs the plant, and runs the year with no integer
    clusters (the uc-1.1 engine raised here: window 1 inherited a pin inside
    the min-down of stops window 0 kept)."""
    uc_params_frame(toy_uc_params(ut_h=4, noload_mmbtu_h=100.0))
    gens, fa, demand, mc, dk = toy_inputs(T_STAGE, night_mw=40.0, day_mw=40.0)
    p = build_uc_cluster_params(fa, "NEISO")
    assert demote_budget_pinned(p, np.array([], dtype=int))[1].size == 0
    p_dem, demoted = demote_budget_pinned(p, PIN["coal_plant_gen_idx"])
    assert demoted.tolist() == [0] and not p_dem.integer.any()
    p0 = _p0_off_then_on(fa, 50.0)
    demand[0, :] = p0[0, :] + 60.0
    stage = _stage(tmp_path, fa, demand, mc, {**dk, **PIN}, p0)
    assert stage.int_idx.size == 0 and stage.integer_gate_size == 1
    sched = stage.run(fa, mc, write=False)
    assert sched.kept_until == T_STAGE
    eng = stage.log["engine"]
    assert eng["integer_demoted_budget_pinned"] == [1]
    assert eng["integer_set_size"] == 0 and eng["integer_gate_size"] == 1
    # no integer cluster: P1's markup is not zeroed on the pinned rows either
    markup = np.ones((fa.n_gen, T_STAGE))
    assert stage.zero_markup(markup) is markup


def test_partially_pinned_cluster_keeps_its_integer(uc_params_frame):
    """One unpinned member is enough for the window to decide the commitment."""
    gens = toy_generators()
    gens.insert(1, gens[0].model_copy(update={"unit_id": "CC1b", "pmax_mw": 100.0}))
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=4)
    p = build_uc_cluster_params(fa, "NEISO")
    assert p.integer.any()
    c = int(p.cluster_of_gen[0])
    assert int(p.cluster_of_gen[1]) == c, "both CC rows are one plant cluster"
    _, demoted = demote_budget_pinned(p, np.array([0]))
    assert demoted.size == 0
    _, demoted = demote_budget_pinned(p, np.array([0, 1]))
    assert demoted.tolist() == [c]


def test_guard_keeps_units_a_later_derated_floor_needs(uc_params_frame, tmp_path):
    """No pin: a structural floor of 50 MW past window 0's horizon on a plant at
    availability 0.25 (25 MW per unit) needs BOTH units by row (a). uc-1.1's
    guard counted ``ceil(50 / 100) = 1``, let window 0 stop one unit at hour 22,
    and window 1 raised on the contradicted ceiling. uc-1.2's guard counts
    ``ceil(50 / (100 * 0.25)) = 2``: no stop inside the floor hour's min-down."""
    uc_params_frame(toy_uc_params(ut_h=4, noload_mmbtu_h=100.0))
    gens, fa, demand, mc, dk = toy_inputs(T_STAGE, night_mw=40.0, day_mw=40.0)
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(p.dt_h[0])
    assert dt >= L_STAGE + 2, (
        "the collision needs a min-down longer than the look-ahead"
    )
    h = W_STAGE + L_STAGE  # the first hour window 0 cannot see
    mg = np.zeros((fa.n_gen, T_STAGE))
    mg[0, h] = 50.0
    av = np.array(fa.availability, dtype=float, copy=True)
    av[0, h] = 0.25
    mech = np.zeros((fa.n_gen, T_STAGE), dtype=np.int8)
    mech[0, h] = 1
    fa = dataclasses.replace(fa, min_gen=mg, availability=av, min_gen_mechanism=mech)
    p0 = _p0_off_then_on(fa, 0.0)
    p0[0, h] = 50.0
    demand[0, :] = p0[0, :] + 60.0
    stage = _stage(tmp_path, fa, demand, mc, dk, p0)
    sched = stage.run(fa, mc, write=False)
    assert sched.is_complete()
    u, w = sched.u[0].astype(int), sched.w[0].astype(int)
    assert u[h] == 2, u
    assert w[h - dt + 1 : h + 1].sum() == 0, (u, w)
    assert all(win["status"] == "Optimal" for win in stage.log["windows"])
    assert stage.log["windows"][0]["guard_rows"] >= 1
    assert stage.log["engine"]["version"] == "uc-1.2"
