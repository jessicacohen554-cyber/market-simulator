"""The UC window commits against the commitment demand; P1 clears on actual (uc-1.7).

Owner ruling UC-DESK r13 (lane UC-1-FIX-7): ``uc_commitment_demand_source``
"da_forecast" makes the window balance against the measured day-ahead
forecast while P1 still clears on actual load (rule 4). Trivial case: one
zone, the toy CC cluster (2 x 100 MW, mlf 0.5), 48 h. The backcast increment
is injected (the measured EIA-930 read is covered by
``tests/unit/data/test_commitment_demand.py``).
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.solve import run_energy_solve

from .conftest import toy_inputs

T = 48
DAY = slice(7, 24)


@pytest.fixture(autouse=True)
def _warm_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        weather_year=2023,
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=24,
        uc_lookahead_hours=12,
        **kw,
    )


def _inject_increment(monkeypatch, mw: float) -> None:
    import market_sim.data.commitment_demand as cd

    monkeypatch.setattr(
        cd,
        "backcast_commitment_increment",
        lambda *a, **k: (np.full((1, 8760), mw), 0),
    )


def _solve(cfg, day_mw: float = 150.0):
    import market_sim.pipeline.uc as puc

    gens, fa, demand, mc, dk = toy_inputs(T, day_mw=day_mw)
    puc._LAST_SOLVED.clear()
    res = run_energy_solve(gens, fa, demand, mc, dk, cfg, zone_names=["North"])
    return res, puc.take_uc_stages()[-1], demand


def test_forecast_above_actual_commits_a_second_unit(
    uc_params_frame, uc_results_root, monkeypatch
):
    """Actual 150 MW: nuclear 60 + one CC unit (<= 100 MW) serve it, so the
    window commits one unit. A forecast 60 MW above actual (210 MW) needs both
    CC units online; P1 then clears the ACTUAL 150 MW against that commitment
    (the CC floor 2 x 50 MW holds, nuclear backs down and sets the price)."""
    _inject_increment(monkeypatch, 60.0)
    act, st_act, demand = _solve(_cfg())
    fc, st_fc, _ = _solve(_cfg(uc_commitment_demand_source="da_forecast"))

    assert (st_act.schedule.u[0, DAY] == 1).all()
    assert (st_fc.schedule.u[0, DAY] == 2).all()
    np.testing.assert_allclose(st_fc.commit.demand, demand + 60.0)
    assert st_fc.log["engine"]["commitment_demand"]["basis"] == "eia930_da_forecast"
    assert st_fc.log["engine"]["commitment_demand"]["increment_mean_mw"] == 60.0

    # P1 clears on actual load: generation == actual in every actual-arm hour
    # and every forecast-arm day hour. (At night the forecast, 100 MW, commits
    # one unit whose 50 MW floor exceeds the actual 40 MW: P1 dumps the
    # excess -- the over-commitment cost the forecast error carries; P1 has no
    # real-time decommitment.)
    np.testing.assert_allclose(act.p1.dispatch.sum(axis=0), demand[0], atol=1e-6)
    np.testing.assert_allclose(
        fc.p1.dispatch[:, DAY].sum(axis=0), demand[0, DAY], atol=1e-6
    )
    # Forecast arm: the second unit's floor holds, so CC runs at >= 100 MW and
    # the price is the nuclear unit's offer (it is the one backing down).
    assert (fc.p1.dispatch[0, DAY] >= 100.0 - 1e-6).all()
    np.testing.assert_allclose(fc.p1.prices[0, DAY], fc.mc_bid[1, DAY])
    # Actual arm: one CC unit at part load is marginal.
    np.testing.assert_allclose(act.p1.prices[0, DAY], act.mc_bid[0, DAY])


def test_actual_source_is_the_p1_demand_object(uc_params_frame, uc_results_root):
    """G-OFF: at "actual" the windows balance against the P1 demand itself
    (the same object), and the run equals the default config's bit for bit."""
    a, st_a, demand = _solve(_cfg())
    b, st_b, _ = _solve(_cfg(uc_commitment_demand_source="actual"))
    assert st_a.commit.demand is st_a.demand
    assert st_a.log["engine"]["commitment_demand"]["increment_max_mw"] == 0.0
    assert np.array_equal(st_a.schedule.u, st_b.schedule.u)
    assert np.array_equal(a.p1.dispatch, b.p1.dispatch)
    assert np.array_equal(a.p1.prices, b.p1.prices)
    assert a.p1.objective_value == b.p1.objective_value


def test_source_needs_the_uc_gate():
    with pytest.raises(ValueError, match="arm unit_commitment_milp"):
        ScenarioConfig(iso="NEISO", uc_commitment_demand_source="da_forecast")
    with pytest.raises(ValueError, match="must be one of"):
        _cfg(uc_commitment_demand_source="perfect")
