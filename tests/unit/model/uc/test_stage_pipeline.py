"""The UC stage through ``run_energy_solve``: off-gate byte-identity, G-EMPTY, injection.

* gate off: the result is the same objects / arrays as before the hunk and the
  stage module is never imported;
* gate on with an empty integer set: identical to gate off (the markup is the
  same object, the hook returns the upstream result);
* gate on with one integer cluster: the P1 fleet carries ceiling
  ``availability * u / n`` and floor ``mlf * pbar * u`` under MECH 28, the
  markup is zeroed on the cluster's rows and the artifacts are written.
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.floor_mechanisms import MECH_UC_SCHEDULE
from market_sim.pipeline.solve import run_energy_solve
from market_sim.pipeline.uc import take_uc_artifacts as puc_take
from market_sim.pipeline.uc import write_uc_artifacts

from .conftest import toy_inputs, toy_uc_params

T = 48


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(iso="NEISO", hours=T, **kw)


def _same(a, b) -> bool:
    return np.array_equal(np.asarray(a), np.asarray(b))


@pytest.fixture(autouse=True)
def _warm_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")


def test_gate_off_is_byte_identical_and_never_imports_the_stage(uc_params_frame):
    gens, fa, demand, mc, dk = toy_inputs(T)
    sys.modules.pop("market_sim.pipeline.uc", None)
    off = run_energy_solve(gens, fa, demand, mc, dk, _cfg(unit_commitment_milp=False))
    assert "market_sim.pipeline.uc" not in sys.modules
    assert off.p1_fleet_arrays is fa
    again = run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    assert _same(off.p1.dispatch, again.p1.dispatch)
    assert _same(off.p1.prices, again.p1.prices)
    assert _same(off.mc_bid, again.mc_bid)
    assert off.p1.objective_value == again.p1.objective_value


def test_gate_on_with_empty_integer_set_equals_gate_off(
    uc_params_frame, uc_results_root
):
    gens, fa, demand, mc, dk = toy_inputs(T, with_baseload=False)
    # Make the CC fast-start by physics (dt 1 h, start below $30/MW cannot be
    # expressed through uc-params; instead drop the CC row so the cluster takes
    # the class tables, and shrink the fleet to the CT alone for the empty set).
    gens = [g for g in gens if g.unit_id == "CT1"]
    from market_sim.data.fleet import generators_to_fleet_arrays

    fa = generators_to_fleet_arrays(gens, ["Z0"], hours=T)
    mc = mc[-1:, :]
    demand = np.minimum(demand, 140.0)
    uc_params_frame(toy_uc_params().iloc[0:0])
    off = run_energy_solve(gens, fa, demand, mc, dk, _cfg())
    on = run_energy_solve(gens, fa, demand, mc, dk, _cfg(unit_commitment_milp=True))
    assert on.p1_fleet_arrays is fa
    assert _same(off.markup, on.markup) and _same(off.mc_bid, on.mc_bid)
    assert _same(off.p1.dispatch, on.p1.dispatch) and _same(off.p1.prices, on.p1.prices)
    assert puc_take() == []


def test_gate_on_injects_ceiling_floor_and_zeroes_markup(
    uc_params_frame, uc_results_root
):
    gens, fa, demand, mc, dk = toy_inputs(T, day_mw=190.0)
    cfg = _cfg(unit_commitment_milp=True, uc_window_hours=24, uc_lookahead_hours=12)
    res = run_energy_solve(gens, fa, demand, mc, dk, cfg)
    import market_sim.pipeline.uc as puc

    stage = puc.take_uc_stages()[-1]
    u = stage.schedule.u[0].astype(float)
    assert stage.schedule.is_complete()
    assert (u[7:24] == 2).all() and (u[:7] == 0).all()
    p1f = res.p1_fleet_arrays
    assert p1f is not fa
    # ceiling = availability * u / n ; floor = mlf * pbar * u (one member, so all of it)
    np.testing.assert_allclose(p1f.availability[0], fa.availability[0] * u / 2.0)
    np.testing.assert_allclose(p1f.min_gen[0], 0.5 * 100.0 * u)
    assert set(np.unique(p1f.min_gen_mechanism[0][u > 0]).tolist()) == {
        MECH_UC_SCHEDULE
    }
    assert (p1f.min_gen_mechanism[0][u == 0] == 0).all()
    # other rows untouched
    np.testing.assert_array_equal(p1f.availability[1:], fa.availability[1:])
    # markup zeroed on the cluster's row only
    assert res.markup[0].max() == 0.0
    # the scored P1 respects the bounds
    assert (res.p1.dispatch[0] <= fa.pmax[0] * p1f.availability[0] + 1e-6).all()
    assert (res.p1.dispatch[0] >= p1f.min_gen[0] - 1e-6).all()
    # artifacts: drained by the orchestrator and written INTO the bundle
    arts = [stage.artifacts(res.p1)]
    bundle = uc_results_root / "bundle"
    paths = write_uc_artifacts(bundle, stage.year, arts)
    assert {p.name for p in paths} == {
        f"uc_schedule_{stage.year}.parquet",
        f"uc_uplift_{stage.year}.parquet",
        f"uc_solve_log_{stage.year}.json",
    }
    sched = pd.read_parquet(bundle / "hourly" / f"uc_schedule_{stage.year}.parquet")
    assert len(sched) == T and set(sched.columns) >= {
        "u",
        "v",
        "w",
        "online_mw",
        "floor_mw",
    }
    up = pd.read_parquet(bundle / "hourly" / f"uc_uplift_{stage.year}.parquet")
    assert len(up) == 2 and (up["uplift_usd"] >= 0).all()
    log = json.loads((bundle / f"uc_solve_log_{stage.year}.json").read_text())
    assert log["summary"]["n_windows"] == 2 and log["engine"]["integer_set_size"] == 1
    assert all(w["status"] == "Optimal" for w in log["windows"])
    # no artifact anywhere outside the bundle (the old results/uc path is gone)
    assert (
        not list((uc_results_root / "uc").glob("**/*"))
        if (uc_results_root / "uc").exists()
        else True
    )


def test_min_up_carries_across_the_window_boundary(uc_params_frame, uc_results_root):
    """UC-DESK review point 1: a start at hour 22 of window 0 (ut = 8) stays on
    through hour 5 of window 1 even though the no-load would stop it at hour 24."""
    from .conftest import toy_uc_params

    uc_params_frame(toy_uc_params(ut_h=8, dt_h=4, noload_mmbtu_h=100.0))
    gens, fa, demand, mc, dk = toy_inputs(T, night_mw=40.0, day_mw=40.0)
    demand[0, 22:24] = 300.0  # baseload 60 + CT 150 < 300: the CC must start at 22
    cfg = _cfg(unit_commitment_milp=True, uc_window_hours=24, uc_lookahead_hours=12)
    run_energy_solve(gens, fa, demand, mc, dk, cfg)
    import market_sim.pipeline.uc as puc

    stage = puc.take_uc_stages()[-1]
    u = stage.schedule.u[0]
    assert (u[22:24] >= 1).all(), u
    assert (u[24:30] >= 1).all(), u  # hours 0..5 of window 1: the carried start holds
    assert u[30:].max() == 0, u  # free to stop once the min-up is served
    assert stage.schedule.v[0, 22] >= 1


def test_stack_refused_at_validation():
    with pytest.raises(ValueError, match="REPLACES"):
        _cfg(unit_commitment_milp=True, nyiso_gas_commitment_bridge=True)
    with pytest.raises(ValueError, match="REPLACES"):
        ScenarioConfig(
            iso="SPP", hours=T, unit_commitment_milp=True, spp_commitment_posture=True
        )
    # D-5 hard cases and "replace" recommendations are NOT refused by the engine.
    ScenarioConfig(
        iso="PJM", mode="backcast", unit_commitment_milp=True, cc_mustrun_per_plant=True
    )
