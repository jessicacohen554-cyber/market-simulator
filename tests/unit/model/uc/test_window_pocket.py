"""The VLR load-pocket commitment rows (``vlr_pocket_commitment``; lane UC-MISO-VLR).

Trivial cases first (one integer cluster, one zone, 24 h):

* the requirement builder maps source units onto ``(plant_code, family)``
  clusters, merges groups on the same cluster set (requirements add, capped at
  the set's units), records groups with no cluster, and refuses overlapping
  sets;
* in the window, a positive no-load decommits the CC at night without the row
  and holds one unit on with it; the row relaxes inside a carried min-down
  (never infeasible); no row is built for a set without an integer cluster;
* through the stage: gate off builds no requirement; gate on holds the set in
  every scheduled hour and logs it; config validation refuses the row without
  the UC and beside the ST_GAS per-plant floor.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.pocket import build_pocket_requirement
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs

from .conftest import toy_inputs

T = 24
OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)


def _groups(rows) -> pd.DataFrame:
    """A ``vlr-pocket-groups`` frame from ``(pocket, group, plant, unit, family)``."""
    return pd.DataFrame(
        rows, columns=["pocket", "group_id", "plant_code", "unit_id", "uc_family"]
    )


def _window(fa, demand, mc, dk, params, pocket=None, w_hist=None, noload=200.0):
    inputs = slice_window_inputs(fa, demand, dk, 0, T)
    n_int = int(params.integer_clusters.size)
    state = WindowState(
        u_prev=np.zeros(n_int),
        v_hist=np.zeros((n_int, 0 if w_hist is None else w_hist.shape[1])),
        w_hist=np.zeros((n_int, 0)) if w_hist is None else w_hist,
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    return UcWindowModel(
        inputs, params, mc, np.full((n_int, T), noload), state, pocket=pocket
    )


# --------------------------------------------------------------- builder
def test_builder_one_group_one_cluster(uc_params_frame):
    _, fa, _, _, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    req = build_pocket_requirement(p, _groups([("P", "A", 1, "1", "cc")]), 1)
    assert req.n_sets == 1 and req.n_req.tolist() == [1]
    assert req.clusters_of(0).tolist() == [0]  # the CC cluster
    assert req.labels == ("P:A",) and req.unmatched == ()


def test_builder_merges_same_set_caps_at_units_and_records_unmatched(uc_params_frame):
    _, fa, _, _, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    frame = _groups(
        [
            ("P", "A", 1, "1", "cc"),
            ("P", "B", 1, "2", "cc"),
            ("P", "C", 1, "3", "cc"),  # third group on the same 2-unit cluster
            ("Q", "D", 99, "1", "st_gas"),  # no cluster in the fleet
        ]
    )
    req = build_pocket_requirement(p, frame, 1)
    assert req.n_sets == 1
    assert req.n_req.tolist() == [2]  # 1 + 1 + 1, capped at n_units = 2
    assert req.labels == ("P:A+P:B+P:C",)
    assert req.unmatched == ("Q:D",)


def test_builder_refuses_overlapping_sets(uc_params_frame):
    _, fa, _, _, _ = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    frame = _groups(
        [("P", "A", 1, "1", "cc"), ("P", "A", 2, "1", "ct"), ("P", "B", 1, "2", "cc")]
    )
    with pytest.raises(ValueError, match="share clusters"):
        build_pocket_requirement(p, frame, 1)


# ---------------------------------------------------------------- window
def test_row_holds_one_unit_through_the_night(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    p = build_uc_cluster_params(fa, "NEISO")
    base = solve_window(_window(fa, demand, mc, dk, p), OPTS)
    assert (base.u[0, :7] == 0).all()  # no-load decommits the CC at night
    req = build_pocket_requirement(p, _groups([("P", "A", 1, "1", "cc")]), 1)
    w = _window(fa, demand, mc, dk, p, pocket=req)
    assert w._n_pocket_rows == T
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.u[0] >= 1).all()
    assert (res.u[0, 7:] == 2).all()  # the day still needs both units
    assert res.objective >= base.objective - 1e-6


def test_row_relaxes_inside_a_carried_min_down(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T, night_mw=40.0, day_mw=40.0)
    p = build_uc_cluster_params(fa, "NEISO")
    dt = int(p.dt_h[0])
    w_hist = np.zeros((1, dt - 1))
    w_hist[0, -1] = 2.0  # both units stopped at t0 - 1
    req = build_pocket_requirement(p, _groups([("P", "A", 1, "1", "cc")]), 1)
    res = solve_window(_window(fa, demand, mc, dk, p, pocket=req, w_hist=w_hist), OPTS)
    assert res.status == "Optimal"
    assert (res.u[0, : dt - 1] == 0).all()  # no unit can be on: the row relaxes
    assert (res.u[0, dt - 1 :] >= 1).all()  # and binds once the min-down expires


def test_no_row_for_a_set_without_an_integer_cluster(uc_params_frame):
    _, fa, demand, mc, dk = toy_inputs(T)
    p = build_uc_cluster_params(fa, "NEISO")
    req = build_pocket_requirement(p, _groups([("P", "A", 2, "1", "ct")]), 1)
    w = _window(fa, demand, mc, dk, p, pocket=req)  # the CT is fast-start
    assert w._n_pocket_rows == 0 and w.pocket_sets_skipped == 1


# ---------------------------------------------------------------- stage / config
@pytest.fixture
def _warm_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")


def test_stage_gate_on_holds_the_set_and_logs_it(
    uc_params_frame, uc_results_root, monkeypatch, _warm_env
):
    import market_sim.pipeline.uc as puc
    from market_sim.pipeline.solve import run_energy_solve

    monkeypatch.setattr(
        puc,
        "load_vlr_pocket_groups",
        lambda iso: _groups([("P", "A", 1, "1", "cc"), ("Q", "Z", 99, "1", "st_gas")]),
    )
    hours = 48
    gens, fa, demand, mc, dk = toy_inputs(hours, day_mw=190.0)
    base = dict(
        iso="NEISO",
        hours=hours,
        unit_commitment_milp=True,
        uc_window_hours=24,
        uc_lookahead_hours=12,
    )
    run_energy_solve(gens, fa, demand, mc, dk, ScenarioConfig(**base))
    off = puc.take_uc_stages()[-1]
    assert off.pocket is None
    assert off.log["engine"]["vlr_pocket"] is None
    assert off.log["engine"]["fields"]["vlr_pocket_commitment"] is False
    assert (off.schedule.u[0, :7] == 0).all()
    run_energy_solve(
        gens, fa, demand, mc, dk, ScenarioConfig(**base, vlr_pocket_commitment=True)
    )
    on = puc.take_uc_stages()[-1]
    assert (on.schedule.u[0] >= 1).all()
    log = on.log["engine"]["vlr_pocket"]
    assert log["min_units_per_group"] == 1
    assert log["unmatched_groups"] == ["Q:Z"]
    assert log["sets"][0]["label"] == "P:A"
    assert all(w["pocket_rows"] > 0 for w in on.log["windows"])
    assert on.log["engine"]["input_digest"] != off.log["engine"]["input_digest"]


def test_config_refusals_and_cache_key():
    with pytest.raises(ValueError, match="needs unit_commitment_milp"):
        ScenarioConfig(vlr_pocket_commitment=True)
    with pytest.raises(ValueError, match="REPLACES st_gas_mustrun_per_plant"):
        ScenarioConfig(
            mode="backcast",
            unit_commitment_milp=True,
            vlr_pocket_commitment=True,
            st_gas_mustrun_per_plant=True,
        )
    assert ScenarioConfig().vlr_pocket_commitment is False
    assert (
        ScenarioConfig().cache_key()
        == ScenarioConfig(vlr_pocket_commitment=False).cache_key()
    )
    on = ScenarioConfig(unit_commitment_milp=True, vlr_pocket_commitment=True)
    assert on.cache_key() != ScenarioConfig(unit_commitment_milp=True).cache_key()
