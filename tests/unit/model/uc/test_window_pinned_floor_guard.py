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

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.uc.params import build_uc_cluster_params, units_needed_for_floor
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import (
    UcWindowInfeasible,
    UcWindowModel,
    WindowState,
    slice_window_inputs,
    window_fleet,
)
from market_sim.pipeline.uc import UcStage

from .conftest import toy_inputs, toy_uc_params

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
# The stage: a pin past window 0's horizon, inside the min-down               #
# --------------------------------------------------------------------------- #
class _P0:
    """A synthetic P0 result (the stage reads dispatch / prices / SOC / flows)."""

    def __init__(self, dispatch: np.ndarray, n_zones: int) -> None:
        self.dispatch = dispatch
        self.prices = np.full((n_zones, dispatch.shape[1]), 30.0)
        self.storage_soc = None
        self.flows = None


def _pinned_stage(tmp_path, pin_mw_after: float):
    T, W, L = 72, 24, 2
    gens, fa, demand, mc, dk = toy_inputs(T, night_mw=40.0, day_mw=40.0)
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(p.dt_h[0])
    assert dt >= L + 2, "the collision needs a min-down longer than the look-ahead"
    p0 = np.zeros((fa.n_gen, T))
    p0[0, 0:22] = 200.0  # both units through hour 21
    p0[0, 22 : W + L] = 0.0  # the pinned plant idles to window 0's horizon ...
    p0[0, W + L :] = pin_mw_after  # ... and runs again one hour past it
    p0[0, T - 1] = 200.0  # the cyclic first state: both units on
    p0[1, :] = 60.0
    demand[0, :] = p0[0, :] + 60.0
    cfg = ScenarioConfig(
        iso="NEISO",
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=W,
        uc_lookahead_hours=L,
    )
    stage = UcStage(
        cfg,
        fa,
        demand,
        {**dk, **PIN},
        mc,
        _P0(p0, demand.shape[0]),
        None,
        lambda: mc,
        checkpoint_root=tmp_path,
    )
    return stage, fa, mc, dt, W + L


@pytest.mark.parametrize("pin_mw_after", [150.0, 50.0])
def test_guard_keeps_units_a_later_pin_needs(uc_params_frame, tmp_path, pin_mw_after):
    """Window 0 sees the pinned plant idle over hours 22-25 and nothing after;
    window 1 pins it at ``pin_mw_after`` from hour 26, which row (a) carries
    only with both units. uc-1.1 stopped both at hour 22 (its guard read the
    unpinned fleet: no floor) and window 1 raised ``UcWindowInfeasible``; at
    50 MW even a pinned-fleet guard dividing by ``pbar`` alone asked for one
    unit. uc-1.2's guard reads row (a)'s count on the pinned fleet: no stop
    inside the min-down of hour 26, every window Optimal."""
    uc_params_frame(toy_uc_params(ut_h=4, noload_mmbtu_h=100.0))
    stage, fa, mc, dt, h_pin = _pinned_stage(tmp_path, pin_mw_after)
    sched = stage.run(fa, mc, write=False)
    assert sched.is_complete()
    u, w = sched.u[0].astype(int), sched.w[0].astype(int)
    assert (u[h_pin:] == 2).all(), u
    assert w[h_pin - dt + 1 : h_pin + 1].sum() == 0, (u, w)
    assert all(win["status"] == "Optimal" for win in stage.log["windows"])
    assert stage.log["windows"][0]["guard_rows"] >= 1
    assert stage.log["engine"]["version"] == "uc-1.2"
