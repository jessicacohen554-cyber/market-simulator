"""In-place P1-native floor re-solve (``refloor_thermal_inplace``).

The P1-native commitment-bridge hooks (CAISO RA must-offer, ERCOT gas bridge)
inject a ``min_gen`` floor for the P1 clearing solve. Historically that forced a
cold rebuild of the whole LP; ``lp.inplace_floor.refloor_thermal_inplace``
instead mutates the thermal P-block column bounds on the live P0 model and
warm-solves from the P0 basis (refactor-consolidation plan §7 H-1, the analogue
of the shipped ``changeColsCost`` P0->P1 re-cost).

The floor is only a P-block column-bound change, so on a *tie-free* LP (unique
optimum) the in-place warm P1 must be byte-identical to a cold rebuild on the
floored fleet — the same neutrality standard as the shipped warm starts. These
tests assert that identity on trivial 3-gen / 1-zone / 24-hour LPs, plus the
gate that declines the in-place edit when a floored ``availability`` would also
move an availability-dependent row (ramp / co-opt reserve).
"""

from __future__ import annotations

import dataclasses
import os

import numpy as np
import pytest

from market_sim.data.fleet import FleetArrays, generators_to_fleet_arrays
from market_sim.model.lp import DispatchModel, solve_dispatch
from market_sim.model.lp.inplace_floor import (
    availability_feeds_rows,
    refloor_thermal_inplace,
)
from market_sim.pipeline.solve import run_energy_solve
from tests.helpers.builders import base_scenario, make_gen

T = 24
ZONES = ["Z0"]
DEMAND = np.full((1, T), 150.0)


def _gens():
    # pmin 0 so the only lower bound is the injected floor; distinct fuels are
    # irrelevant (mc is passed explicitly), gas_cc keeps markup trivial.
    return [
        make_gen(unit_id=f"G{i}", zone="Z0", pmax_mw=100.0, pmin_mw=0.0)
        for i in range(3)
    ]


def _fleet(avail: float = 0.95):
    fa = generators_to_fleet_arrays(_gens(), ZONES, hours=T)
    return dataclasses.replace(fa, availability=np.full((3, T), avail))


def _mc(base):
    """Distinct per-gen, per-hour costs => unique optimum (no marginal ties)."""
    return np.stack([c + 0.01 * np.arange(T) for c in base])


def _floor(fa: FleetArrays, gen: int, val: float, hours) -> FleetArrays:
    mg = np.zeros((fa.n_gen, T))
    mg[gen, hours] = val
    return dataclasses.replace(
        fa, min_gen=mg, min_gen_mechanism=np.zeros((fa.n_gen, T), np.int8)
    )


def _raise_avail_to_floor(fa: FleetArrays) -> FleetArrays:
    """Emulate ``_bridge_floored_fleet``'s feasibility guard on the floored fleet."""
    need = np.clip(fa.min_gen / np.maximum(fa.pmax, 1.0)[:, None], 0.0, 1.0)
    av = np.where(fa.min_gen > 0.0, np.maximum(fa.availability, need), fa.availability)
    return dataclasses.replace(fa, availability=av)


_BASE_KW = dict(
    wind_cf=np.zeros((1, T)),
    wind_cap=np.zeros(1),
    solar_cf=np.zeros((1, T)),
    solar_cap=np.zeros(1),
    T=T,
)


def _assert_identical(a, b):
    assert np.array_equal(a.dispatch, b.dispatch), np.abs(a.dispatch - b.dispatch).max()
    assert np.array_equal(a.prices, b.prices), np.abs(a.prices - b.prices).max()


@pytest.mark.parametrize("guard", [False, True])
def test_inplace_matches_cold_noncoopt(guard):
    """min_gen-only and availability-guard-fires floors (no co-opt) are exact."""
    fa = _fleet(0.95)
    if guard:
        # gen2 availability below the floor fraction => the guard raises it; with
        # no availability-dependent row this is still a pure P-block edit.
        av = fa.availability.copy()
        av[2, 0:6] = 0.30
        fa = dataclasses.replace(fa, availability=av)
    floored = _floor(fa, 2, 40.0, np.arange(0, 6))
    if guard:
        floored = _raise_avail_to_floor(floored)

    mc_base = _mc([10.0, 20.0, 30.0])
    mc_bid = _mc([12.0, 23.0, 34.0])

    model = DispatchModel(fa, DEMAND, **_BASE_KW)
    model.solve(mc=mc_base)
    assert (
        refloor_thermal_inplace(model, floored, availability_feeds_rows(model, False))
        is True
    )
    inplace = model.solve(mc=mc_bid)

    cold = solve_dispatch(floored, DEMAND, mc=mc_bid, **_BASE_KW)
    _assert_identical(inplace, cold)
    # The floor actually bound: gen2 runs at 40 in the floored hours.
    assert np.allclose(inplace.dispatch[2, 0:6], 40.0)


def test_inplace_matches_cold_coopt_min_gen_only():
    """A co-opt model accepts a min_gen-only floor (availability unchanged)."""
    fa = _fleet(0.95)
    floored = _floor(fa, 2, 40.0, np.arange(0, 6))  # 0.95*100 >= 40 => no guard
    kw = dict(
        _BASE_KW,
        reserve_requirement=np.full(T, 20.0),
        reserve_eligible=np.ones(3, bool),
    )
    mc_base = _mc([10.0, 20.0, 30.0])
    mc_bid = _mc([12.0, 23.0, 34.0])

    model = DispatchModel(fa, DEMAND, **kw)
    model.solve(mc=mc_base)
    assert (
        refloor_thermal_inplace(model, floored, availability_feeds_rows(model, False))
        is True
    )
    inplace = model.solve(mc=mc_bid)

    cold = solve_dispatch(floored, DEMAND, mc=mc_bid, **kw)
    _assert_identical(inplace, cold)


def test_inplace_declines_coopt_availability_change():
    """Co-opt + changed availability => decline (avail feeds the reserve rows)."""
    fa = _fleet(0.95)
    av = fa.availability.copy()
    av[2, 0:6] = 0.30
    floored = _raise_avail_to_floor(
        dataclasses.replace(_floor(fa, 2, 40.0, np.arange(0, 6)), availability=av)
    )
    kw = dict(
        _BASE_KW,
        reserve_requirement=np.full(T, 20.0),
        reserve_eligible=np.ones(3, bool),
    )
    mc_base = _mc([10.0, 20.0, 30.0])
    mc_bid = _mc([12.0, 23.0, 34.0])

    model = DispatchModel(fa, DEMAND, **kw)
    model.solve(mc=mc_base)
    assert (
        refloor_thermal_inplace(model, floored, availability_feeds_rows(model, False))
        is False
    )
    # Model left untouched: re-solving reproduces the UNfloored optimum.
    after_decline = model.solve(mc=mc_bid)
    unfloored = solve_dispatch(fa, DEMAND, mc=mc_bid, **kw)
    _assert_identical(after_decline, unfloored)


def test_inplace_declines_on_gen_count_mismatch():
    fa = _fleet(0.95)
    model = DispatchModel(fa, DEMAND, **_BASE_KW)
    model.solve(mc=_mc([10.0, 20.0, 30.0]))
    smaller = generators_to_fleet_arrays(_gens()[:2], ZONES, hours=T)
    assert (
        refloor_thermal_inplace(model, smaller, availability_feeds_rows(model, False))
        is False
    )


def _run_solve(flag_value, floored):
    """Drive run_energy_solve with the env toggle set, returning the P1 result."""
    fleet = _gens()
    fa = _fleet(0.95)
    cfg = base_scenario(mode="backcast", iso="CAISO", hours=T)
    mc_base = _mc([10.0, 20.0, 30.0])
    kw = dict(_BASE_KW)
    prev = os.environ.get("MARKET_SIM_P1_FLOOR_INPLACE")
    if flag_value is None:
        os.environ.pop("MARKET_SIM_P1_FLOOR_INPLACE", None)
    else:
        os.environ["MARKET_SIM_P1_FLOOR_INPLACE"] = flag_value
    try:
        res = run_energy_solve(
            fleet, fa, DEMAND, mc_base, kw, cfg, p1_fleet_prep=lambda r0: floored
        )
    finally:
        if prev is None:
            os.environ.pop("MARKET_SIM_P1_FLOOR_INPLACE", None)
        else:
            os.environ["MARKET_SIM_P1_FLOOR_INPLACE"] = prev
    return res


def test_run_energy_solve_inplace_matches_cold_path():
    """run_energy_solve: the in-place P1 (flag=1) matches the cold P1 (flag=0)."""
    floored = _floor(_fleet(0.95), 2, 40.0, np.arange(0, 6))
    on = _run_solve("1", floored)
    off = _run_solve("0", floored)
    _assert_identical(on.p1, off.p1)
    # Both persisted the floored fleet the scored P1 saw.
    assert on.p1_fleet_arrays is floored and off.p1_fleet_arrays is floored
    # The floor bound in both.
    assert np.allclose(on.p1.dispatch[2, 0:6], 40.0)


def test_run_energy_solve_default_is_cold_path():
    """Unset toggle keeps the pre-2026-07 cold rebuild (byte-identical to flag=0)."""
    floored = _floor(_fleet(0.95), 2, 40.0, np.arange(0, 6))
    default = _run_solve(None, floored)
    cold = _run_solve("0", floored)
    _assert_identical(default.p1, cold.p1)


def test_availability_feeds_rows_gate():
    """The gate keys off co-opt / posture (model state) and ramp (passed)."""
    fa = _fleet(0.95)
    energy_only = DispatchModel(fa, DEMAND, **_BASE_KW)
    energy_only.solve(mc=_mc([10.0, 20.0, 30.0]))
    assert availability_feeds_rows(energy_only, ramp_present=False) is False
    # A caller that reports ramp constraints flips the gate on an energy-only LP.
    assert availability_feeds_rows(energy_only, ramp_present=True) is True

    coopt = DispatchModel(
        fa,
        DEMAND,
        **dict(
            _BASE_KW,
            reserve_requirement=np.full(T, 20.0),
            reserve_eligible=np.ones(3, bool),
        ),
    )
    coopt.solve(mc=_mc([10.0, 20.0, 30.0]))
    assert availability_feeds_rows(coopt, ramp_present=False) is True
