"""The Sector-1 ST_GAS self-commitment rows (``spp_selfcommit_sector1_st_gas``).

Lane UC-SPP-SELFCOMMIT (owner ruling R24). Trivial cases first (one zone,
24-72 h, a one-unit gas steamer beside the toy CC / CT / baseload fleet):

* the builder selects integer ``st_gas`` clusters of EIA-860 Sector-1 plants
  with a measured ``online_frac`` and records every other one with a reason;
  it places the window as whole operating days ranked by mean system load;
* in the window, the priced-out steamer stays off without the row and holds
  one unit online in exactly its required hours with it, at or above its
  measured min-load and free above it;
* rule 17: an outage hour builds no row (the unit is not forced on), a
  derated hour still holds the unit online at the derated min-load;
* rule 18: a carried min-down relaxes the row, and the unit's own min-up
  (not the requirement) decides how long it stays on;
* through the stage: gate off builds nothing; gate on holds the window and
  logs it; config validation refuses the row without the UC, outside SPP and
  beside the per-plant ST_GAS floor.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.uc.params import build_uc_cluster_params
from market_sim.model.uc.selfcommit import (
    SelfCommitRequirement,
    build_selfcommit_requirement,
)
from market_sim.model.uc.solve import UcSolveOptions, solve_window
from market_sim.model.uc.window import UcWindowModel, WindowState, slice_window_inputs

from .conftest import toy_generators, toy_uc_params

T = 24
OPTS = UcSolveOptions(mip_rel_gap=1e-6, time_limit_s=60.0)
ST_PLANT = 3
ST_MW = 100.0
ST_MLF = 0.3


def _st_params_frame(ut_h: int = 2, dt_h: int = 4) -> pd.DataFrame:
    """The toy CC row plus a one-unit gas steamer (plant 3)."""
    st = dict(
        plant_code=ST_PLANT,
        uc_class="st_gas",
        n_units=1,
        hsl_mw=ST_MW,
        lsl_mw=ST_MW * ST_MLF,
        mlf=ST_MLF,
        ut_h=ut_h,
        dt_h=dt_h,
        noload_mmbtu_h=150.0,
        noload_units_fitted=1,
        noload_r2_median=0.99,
        online_frac=0.6,
        n_runs=50,
        years="2023-2025",
        source="toy",
    )
    return pd.concat([toy_uc_params(), pd.DataFrame([st])], ignore_index=True)


def _st_inputs(hours: int, demand_mw: float = 100.0):
    """Toy fleet + the steamer; the steamer is the dearest energy and has no-load."""
    gens = toy_generators() + [
        Generator(
            unit_id="ST1",
            name="st",
            zone="Z0",
            fuel_type="gas_st",
            pmax_mw=ST_MW,
            pmin_mw=0.0,
            heat_rate=11.0,
            vom=3.0,
            eford=0.0,
            plant_code=ST_PLANT,
            plant_group="ST_GAS",
        )
    ]
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=hours)
    demand = np.full((1, hours), demand_mw)
    mc = np.vstack(
        [
            np.full(hours, 25.0),  # CC
            np.full(hours, 5.0),  # baseload
            np.full(hours, 60.0),  # CT
            np.full(hours, 70.0),  # ST: priced out
        ]
    )
    dk = dict(
        wind_cf=np.zeros((1, hours)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, hours)),
        solar_cap=np.zeros(1),
        voll=5000.0,
    )
    return gens, fa, demand, mc, dk


@pytest.fixture
def st_params(uc_params_frame):
    """Inject the CC + steamer ``uc-params`` frame; returns a setter."""
    uc_params_frame(_st_params_frame())
    return uc_params_frame


def _st_cluster(p) -> int:
    return int(np.flatnonzero(np.asarray(p.family) == "st_gas")[0])


def _req(p, mask: np.ndarray) -> SelfCommitRequirement:
    c = _st_cluster(p)
    return SelfCommitRequirement(
        clusters=np.array([c]),
        plant_code=np.array([ST_PLANT]),
        online_frac=np.array([float(mask.mean())]),
        required=np.asarray(mask, dtype=bool)[None, :],
        min_units=1,
        skipped=(),
    )


def _window(fa, demand, mc, dk, params, selfcommit=None, w_hist=None):
    inputs = slice_window_inputs(fa, demand, dk, 0, demand.shape[1])
    n_int = int(params.integer_clusters.size)
    T_w = demand.shape[1]
    state = WindowState(
        u_prev=np.zeros(n_int),
        v_hist=np.zeros((n_int, 0 if w_hist is None else w_hist.shape[1])),
        w_hist=np.zeros((n_int, 0)) if w_hist is None else w_hist,
        soc_prev=None,
        p_prev=None,
        avail_prev=None,
    )
    return UcWindowModel(
        inputs,
        params,
        mc,
        np.full((n_int, T_w), 200.0),
        state,
        selfcommit=selfcommit,
    )


def _local(p, c: int) -> int:
    return int(np.flatnonzero(p.integer_clusters == c)[0])


# --------------------------------------------------------------- builder
def test_builder_selects_sector1_st_gas_with_a_measured_share(st_params):
    _, fa, demand, _, _ = _st_inputs(T)
    p = build_uc_cluster_params(fa, "SPP")
    req = build_selfcommit_requirement(
        p, {ST_PLANT: 1}, {(ST_PLANT, "ST_GAS"): 0.5}, demand[0], (1,), 1
    )
    assert req.n_sel == 1 and req.clusters.tolist() == [_st_cluster(p)]
    assert req.plant_code.tolist() == [ST_PLANT] and req.min_units == 1
    assert req.required.shape == (1, T)


@pytest.mark.parametrize(
    "sectors, frac, reason",
    [
        ({ST_PLANT: 2}, 0.5, "EIA-860 sector 2"),
        ({}, 0.5, "EIA-860 sector None"),
        ({ST_PLANT: 1}, 0.0, "no measured online_frac"),
    ],
)
def test_builder_skips_with_a_reason(st_params, sectors, frac, reason):
    _, fa, demand, _, _ = _st_inputs(T)
    p = build_uc_cluster_params(fa, "SPP")
    req = build_selfcommit_requirement(
        p, sectors, {(ST_PLANT, "ST_GAS"): frac}, demand[0], (1,), 1
    )
    assert req.n_sel == 0
    assert req.skipped == (f"{ST_PLANT}:{reason}",)


def test_builder_places_whole_days_by_mean_system_load(st_params):
    hours = 72
    _, fa, demand, _, _ = _st_inputs(hours)
    p = build_uc_cluster_params(fa, "SPP")
    load = np.concatenate([np.full(24, 100.0), np.full(24, 300.0), np.full(24, 200.0)])
    load[5] = 1_000.0  # one hot hour does not outrank a hot day's mean
    one_day = build_selfcommit_requirement(
        p, {ST_PLANT: 1}, {(ST_PLANT, "ST_GAS"): 1.0 / 3.0}, load, (1,), 1
    )
    assert np.flatnonzero(one_day.required[0]).tolist() == list(range(24, 48))
    two_days = build_selfcommit_requirement(
        p, {ST_PLANT: 1}, {(ST_PLANT, "ST_GAS"): 2.0 / 3.0}, load, (1,), 1
    )
    assert np.flatnonzero(two_days.required[0]).tolist() == list(range(24, 72))
    every = build_selfcommit_requirement(
        p, {ST_PLANT: 1}, {(ST_PLANT, "ST_GAS"): 1.0}, load, (1,), 1
    )
    assert every.required.all()


# ---------------------------------------------------------------- window
def test_trivial_one_unit_24h_holds_exactly_the_required_hours(st_params):
    _, fa, demand, mc, dk = _st_inputs(T)
    p = build_uc_cluster_params(fa, "SPP")
    k = _local(p, _st_cluster(p))
    base = solve_window(_window(fa, demand, mc, dk, p), OPTS)
    assert base.status == "Optimal"
    assert (base.u[k] == 0).all()  # priced out: never committed on its own
    mask = np.zeros(T, dtype=bool)
    mask[8:20] = True
    w = _window(fa, demand, mc, dk, p, selfcommit=_req(p, mask))
    assert w._n_selfcommit_rows == 12 and w.selfcommit_relaxed_hours == 0
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.u[k, 8:20] == 1).all()
    assert (res.u[k, :8] == 0).all() and (res.u[k, 20:] == 0).all()
    assert res.objective >= base.objective - 1e-6


def test_online_unit_sits_at_its_measured_min_load_not_a_p_floor(st_params):
    _, fa, demand, mc, dk = _st_inputs(T)
    p = build_uc_cluster_params(fa, "SPP")
    k = _local(p, _st_cluster(p))
    w = _window(fa, demand, mc, dk, p, selfcommit=_req(p, np.ones(T, dtype=bool)))
    res = solve_window(w, OPTS)
    assert res.status == "Optimal" and (res.u[k] == 1).all()
    # Coupling row (b): output >= mlf * pbar * a * u, and it is the dearest
    # energy, so it sits exactly at its measured min-load — no P floor above.
    st_mw = res.dispatch[int(p.member_gen[p.member_cluster == _st_cluster(p)][0])]
    assert np.allclose(st_mw, ST_MLF * ST_MW, atol=1e-6)


def test_rule17_outage_hours_build_no_row_derate_still_commits(st_params):
    _, fa, demand, mc, dk = _st_inputs(T)
    p = build_uc_cluster_params(fa, "SPP")
    c = _st_cluster(p)
    k = _local(p, c)
    g = int(p.member_gen[p.member_cluster == c][0])
    fa.availability[g, 10:14] = 0.0  # forced outage
    fa.availability[g, 16:18] = 0.5  # derate: still available, half capacity
    # Required ONLY in the outage hours: no row, nothing forces the unit on.
    outage = np.zeros(T, dtype=bool)
    outage[10:14] = True
    w = _window(fa, demand, mc, dk, p, selfcommit=_req(p, outage))
    assert w.selfcommit_relaxed_hours == 4 and w._n_selfcommit_rows == 0
    res = solve_window(w, OPTS)
    assert res.status == "Optimal" and (res.u[k] == 0).all()
    # Required across both: the outage hours relax, the derated hours bind.
    mask = np.zeros(T, dtype=bool)
    mask[8:20] = True
    w = _window(fa, demand, mc, dk, p, selfcommit=_req(p, mask))
    assert w.selfcommit_relaxed_hours == 4 and w._n_selfcommit_rows == 8
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.dispatch[g, 10:14] == 0.0).all()  # no output through the outage
    assert (res.u[k, 16:18] == 1).all()  # derated, still self-committed
    assert np.allclose(res.dispatch[g, 16:18], ST_MLF * ST_MW * 0.5, atol=1e-6)


def test_rule18_carried_min_down_relaxes_and_min_up_is_physics(uc_params_frame):
    uc_params_frame(_st_params_frame(ut_h=6, dt_h=4))
    _, fa, demand, mc, dk = _st_inputs(T)
    p = build_uc_cluster_params(fa, "SPP")
    c = _st_cluster(p)
    k = _local(p, c)
    n_int = int(p.integer_clusters.size)
    dt = int(p.dt_h[c])
    w_hist = np.zeros((n_int, dt - 1))
    w_hist[k, -1] = 1.0  # the unit stopped at t0 - 1
    mask = np.zeros(T, dtype=bool)
    mask[0:2] = True  # required inside the carried min-down
    mask[12:14] = True  # a two-hour required block, shorter than min-up
    w = _window(fa, demand, mc, dk, p, selfcommit=_req(p, mask), w_hist=w_hist)
    assert w.selfcommit_relaxed_hours == 2
    res = solve_window(w, OPTS)
    assert res.status == "Optimal"
    assert (res.u[k, :2] == 0).all()  # min-down wins over the requirement
    on = np.flatnonzero(res.u[k] > 0)
    assert {12, 13} <= set(on.tolist())
    assert on.size >= int(p.ut_h[c])  # the unit's own min-up holds it on


# ---------------------------------------------------------------- stage / config
@pytest.fixture
def _warm_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")


def test_stage_gate_on_holds_the_window_and_logs_it(
    st_params, uc_results_root, monkeypatch, _warm_env
):
    import market_sim.data.fleet.campd_bins as cb
    import market_sim.data.fleet.eia860 as e860
    import market_sim.pipeline.uc as puc
    from market_sim.pipeline.solve import run_energy_solve

    monkeypatch.setattr(e860, "eia860_plant_sectors", lambda *a, **k: {ST_PLANT: 1})
    monkeypatch.setattr(
        cb, "thermal_tranche_online_frac", lambda *a, **k: {(ST_PLANT, "ST_GAS"): 0.5}
    )
    hours = 48
    gens, fa, demand, mc, dk = _st_inputs(hours)
    demand[0, 24:] = 120.0  # day 2 carries the higher mean load
    base = dict(
        iso="SPP",
        hours=hours,
        unit_commitment_milp=True,
        uc_window_hours=24,
        uc_lookahead_hours=12,
    )
    run_energy_solve(gens, fa, demand, mc, dk, ScenarioConfig(**base))
    off = puc.take_uc_stages()[-1]
    assert off.selfcommit is None
    assert off.log["engine"]["selfcommit"] is None
    assert off.log["engine"]["fields"]["spp_selfcommit_sector1_st_gas"] is False
    k = _local(off.params, _st_cluster(off.params))
    assert (off.schedule.u[k] == 0).all()
    run_energy_solve(
        gens,
        fa,
        demand,
        mc,
        dk,
        ScenarioConfig(**base, spp_selfcommit_sector1_st_gas=True),
    )
    on = puc.take_uc_stages()[-1]
    assert (on.schedule.u[k, 24:] >= 1).all()  # the measured window: day 2
    log = on.log["engine"]["selfcommit"]
    assert log["eligible_sectors"] == [1] and log["min_units_online"] == 1
    assert log["clusters"][0]["plant_code"] == ST_PLANT
    assert log["clusters"][0]["required_hours"] == 24
    assert any(w["selfcommit_rows"] > 0 for w in on.log["windows"])
    assert on.log["engine"]["input_digest"] != off.log["engine"]["input_digest"]


def test_config_refusals_and_cache_key():
    with pytest.raises(ValueError, match="needs unit_commitment_milp"):
        ScenarioConfig(iso="SPP", spp_selfcommit_sector1_st_gas=True)
    with pytest.raises(ValueError, match="scoped to"):
        ScenarioConfig(
            iso="MISO", unit_commitment_milp=True, spp_selfcommit_sector1_st_gas=True
        )
    with pytest.raises(ValueError, match="REPLACES the per-plant ST_GAS floor"):
        ScenarioConfig(
            iso="SPP",
            mode="backcast",
            unit_commitment_milp=True,
            spp_selfcommit_sector1_st_gas=True,
            st_gas_mustrun_per_plant=True,
        )
    assert ScenarioConfig().spp_selfcommit_sector1_st_gas is False
    assert (
        ScenarioConfig().cache_key()
        == ScenarioConfig(spp_selfcommit_sector1_st_gas=False).cache_key()
    )
    on = ScenarioConfig(
        iso="SPP", unit_commitment_milp=True, spp_selfcommit_sector1_st_gas=True
    )
    assert (
        on.cache_key()
        != ScenarioConfig(iso="SPP", unit_commitment_milp=True).cache_key()
    )
