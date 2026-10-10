"""UC defect 6: the P1 floor fills a cluster's members in merit order; uplift at ``mc_base``; pass-2 reuse.

FINDING-ucmilp-fix4-floor-merit-2026-10-10. A CAMPD-binned plant's members are
offer tranches of the same units, so the cluster floor ``mlf * pbar * u`` is
produced by the cheapest tranche first, each up to its ceiling, never split
pro rata into the peak tranches. Trivial cases first (1 cluster, 3 tranches,
24 h), then the stage through ``run_energy_solve``.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import MECH_UC_SCHEDULE
from market_sim.pipeline.solve import run_energy_solve
from market_sim.pipeline.uc import merit_floor_allocation

T = 24


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    import market_sim.pipeline.uc as puc

    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")
    puc._LAST_SOLVED.clear()
    puc.take_uc_stages()
    yield
    puc._LAST_SOLVED.clear()
    puc.take_uc_stages()


# --------------------------------------------------------------- pure allocator
def _one_cluster(floor: float, mc=(30.0, 20.0, 2821.0), cap=(50.0, 30.0, 20.0)):
    k = np.zeros(3, dtype=int)
    g = np.array([10, 11, 12])
    F = np.full((1, T), floor)
    caps = np.repeat(np.asarray(cap, dtype=float)[:, None], T, axis=1)
    mcs = np.repeat(np.asarray(mc, dtype=float)[:, None], T, axis=1)
    return merit_floor_allocation(k, g, F, caps, mcs)


def test_floor_fills_the_cheapest_tranche_first():
    out = _one_cluster(50.0)
    # mc order: member 1 ($20, cap 30) -> member 0 ($30, cap 50) -> member 2 ($2,821)
    np.testing.assert_array_equal(out[:, 0], [20.0, 30.0, 0.0])
    assert (out[2] == 0.0).all()


def test_each_member_capped_and_the_remainder_carried():
    np.testing.assert_array_equal(_one_cluster(90.0)[:, 0], [50.0, 30.0, 10.0])
    # above the summed ceiling: every member at its cap, the rest dropped
    np.testing.assert_array_equal(_one_cluster(500.0)[:, 0], [50.0, 30.0, 20.0])


def test_u_zero_gives_an_exactly_zero_floor():
    out = _one_cluster(0.0, cap=(0.0, 0.0, 0.0))
    assert (out == 0.0).all()
    out = _one_cluster(0.0)
    assert (out == 0.0).all()


def test_ties_break_by_fleet_row():
    out = _one_cluster(40.0, mc=(25.0, 25.0, 25.0))
    np.testing.assert_array_equal(out[:, 0], [40.0, 0.0, 0.0])


def test_merit_order_is_per_hour():
    k = np.zeros(2, dtype=int)
    g = np.array([0, 1])
    F = np.full((1, T), 30.0)
    caps = np.full((2, T), 40.0)
    mc = np.zeros((2, T))
    mc[0, :12], mc[1, :12] = 10.0, 50.0
    mc[0, 12:], mc[1, 12:] = 50.0, 10.0
    out = merit_floor_allocation(k, g, F, caps, mc)
    assert (out[0, :12] == 30.0).all() and (out[1, :12] == 0.0).all()
    assert (out[0, 12:] == 0.0).all() and (out[1, 12:] == 30.0).all()


def test_clusters_fill_independently():
    # cluster 0: one member; cluster 1: three members, listed out of order
    k = np.array([1, 0, 1, 1])
    g = np.array([5, 6, 7, 8])
    F = np.vstack([np.full(T, 15.0), np.full(T, 45.0)])
    caps = np.repeat(np.array([20.0, 10.0, 30.0, 40.0])[:, None], T, axis=1)
    mc = np.repeat(np.array([90.0, 1.0, 10.0, 50.0])[:, None], T, axis=1)
    out = merit_floor_allocation(k, g, F, caps, mc)
    np.testing.assert_array_equal(out[:, 0], [0.0, 10.0, 30.0, 15.0])


# ------------------------------------------------------- the stage, 3 tranches
def _tranche_fleet():
    """One CC plant (2 x 100 MW units) as three offer tranches, plus a CT."""
    rows = [("CC1_committed", 100.0), ("CC1_econ", 60.0), ("CC1_peak", 40.0)]
    gens = [
        Generator(
            unit_id=uid,
            name="cc",
            zone="Z0",
            fuel_type="gas_cc",
            pmax_mw=cap,
            pmin_mw=0.0,
            heat_rate=7.0,
            vom=2.0,
            eford=0.0,
            plant_code=1,
            plant_group="CC_REGULAR",
        )
        for uid, cap in rows
    ]
    gens.append(
        Generator(
            unit_id="CT1",
            name="ct",
            zone="Z0",
            fuel_type="gas_ct",
            pmax_mw=300.0,
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=5.0,
            eford=0.0,
            plant_code=2,
            plant_group="CT_PEAKER",
        )
    )
    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=T)
    demand = np.full((1, T), 150.0)
    demand[0, :7] = 40.0
    # committed $30, econ $20 (cheapest), peak $2,821; CT $60
    mc_base = np.vstack(
        [np.full(T, 30.0), np.full(T, 20.0), np.full(T, 2821.0), np.full(T, 60.0)]
    )
    dk = dict(
        wind_cf=np.zeros((1, T)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, T)),
        solar_cap=np.zeros(1),
        voll=5000.0,
    )
    return gens, fa, demand, mc_base, dk


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso="NEISO",
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=12,
        uc_lookahead_hours=6,
        **kw,
    )


def test_stage_floors_the_cheap_tranches_and_never_the_peak(
    uc_params_frame, uc_results_root
):
    gens, fa, demand, mc, dk = _tranche_fleet()
    res = run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    import market_sim.pipeline.uc as puc

    stage = puc.take_uc_stages()[-1]
    assert stage.params.n_clusters >= 1 and stage.int_idx.size == 1
    u = stage.schedule.u[0].astype(float)
    assert (u > 0).any()
    floor = res.p1_fleet_arrays.min_gen[:3]
    # cluster floor mlf * pbar * u = 0.5 * 100 * u: econ (cap 30u) then committed (20u)
    np.testing.assert_allclose(floor[1], 30.0 * u)
    np.testing.assert_allclose(floor[0], 20.0 * u)
    assert (floor[2] == 0.0).all()
    np.testing.assert_allclose(floor.sum(axis=0), 50.0 * u)
    mech = res.p1_fleet_arrays.min_gen_mechanism
    assert set(np.unique(mech[0][u > 0]).tolist()) == {MECH_UC_SCHEDULE}
    assert (mech[2] == 0).all()
    # the scored P1 never runs the peak tranche to meet a commitment floor
    assert res.p1.dispatch[2].max() <= 1e-6


def test_uplift_is_priced_at_mc_base_not_the_p1_bid(uc_params_frame, uc_results_root):
    gens, fa, demand, mc, dk = _tranche_fleet()
    adjust = np.zeros_like(mc)
    adjust[:3, :] = 500.0  # a P1-only bid adjustment on the integer rows
    res = run_energy_solve(gens, fa, demand, mc, dk, _cfg(), mc_bid_adjust=adjust)
    import market_sim.pipeline.uc as puc

    stage = puc.take_uc_stages()[-1]
    assert not np.array_equal(res.mc_bid[:3], mc[:3])
    up = stage.artifacts(res.p1).uplift
    P = np.asarray(res.p1.dispatch)[:3]
    assert up["energy_cost_usd"].sum() == pytest.approx(float((mc[:3] * P).sum()))
    assert up["energy_mwh"].sum() == pytest.approx(float(P.sum()))


def test_pass_two_with_identical_inputs_reuses_the_schedule(
    uc_params_frame, uc_results_root
):
    gens, fa, demand, mc, dk = _tranche_fleet()
    first = run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    second = run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    import market_sim.pipeline.uc as puc

    s1, s2 = puc.take_uc_stages()[-2:]
    assert s1.log["engine"]["reused_schedule"] is None
    reuse = s2.log["engine"]["reused_schedule"]
    assert reuse is not None
    assert reuse["input_digest"] == s1.log["engine"]["input_digest"]
    assert s2.schedule is s1.schedule
    assert s2.log["summary"]["n_windows"] == s1.log["summary"]["n_windows"]
    assert s1.log["engine"]["input_digest_opaque_types"] == []
    np.testing.assert_array_equal(
        first.p1_fleet_arrays.min_gen, second.p1_fleet_arrays.min_gen
    )
    np.testing.assert_array_equal(first.p1.dispatch, second.p1.dispatch)
    np.testing.assert_array_equal(first.p1.prices, second.p1.prices)


def test_changed_inputs_resolve_the_windows(uc_params_frame, uc_results_root):
    gens, fa, demand, mc, dk = _tranche_fleet()
    run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    run_energy_solve(gens, fa, demand + 1.0, mc, dk, _cfg())
    import market_sim.pipeline.uc as puc

    s1, s2 = puc.take_uc_stages()[-2:]
    assert s2.log["engine"]["reused_schedule"] is None
    assert s2.schedule is not s1.schedule
    assert s2.log["engine"]["input_digest"] != s1.log["engine"]["input_digest"]
