"""The reliability-commitment (RUC) pass of the UC stage (uc-1.9, owner ruling R12).

Trivial case: one zone, 48 h, the toy fleet (CC cluster 2 x 100 MW with mlf
0.5, a 60 MW nuclear row, a 150 MW CT). Actual day load 350 MW; the day-ahead
forecast is injected 200 MW low on day hours, so the DA windows commit one CC
unit and P1a (nuclear 60 + one CC unit 100 + CT 150 = 310 MW) is 40 MW short
every day hour. The RUC re-commits those days on actual load and adds the
second unit; P1b serves the load. DESIGN-ucmilp-ruc-stage-2026-10-16.md.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.solve import run_energy_solve

from .conftest import toy_inputs

T = 48
DAY_HOURS = np.r_[7:24, 31:48]


@pytest.fixture(autouse=True)
def _warm_env(monkeypatch):
    monkeypatch.setenv("MARKET_SIM_WARMSTART", "1")
    monkeypatch.setenv("MARKET_SIM_WARMSTART_XYEAR", "0")
    monkeypatch.setenv("MARKET_SIM_P1_BASIS_SEED", "0")


def _cfg(**kw) -> ScenarioConfig:
    base = dict(
        iso="NEISO",
        mode="backcast",
        weather_year=2023,
        hours=T,
        unit_commitment_milp=True,
        uc_window_hours=24,
        uc_lookahead_hours=12,
        uc_commitment_demand_source="da_forecast",
    )
    base.update(kw)
    return ScenarioConfig(**base)


def _inject_increment(monkeypatch, day_mw: float) -> None:
    """The DA forecast minus actual: ``day_mw`` on the day hours, 0 at night."""
    import market_sim.data.commitment_demand as cd

    inc = np.zeros((1, 8760))
    inc[0, DAY_HOURS] = day_mw
    monkeypatch.setattr(
        cd, "backcast_commitment_increment", lambda *a, **k: (inc.copy(), 0)
    )


def _solve(cfg, day_mw: float = 350.0):
    import market_sim.pipeline.uc as puc

    gens, fa, demand, mc, dk = toy_inputs(T, day_mw=day_mw)
    puc._LAST_SOLVED.clear()
    res = run_energy_solve(gens, fa, demand, mc, dk, cfg, zone_names=["North"])
    return res, puc.take_uc_stages()[-1], demand


def test_ruc_closes_the_shortfall_add_only(
    uc_params_frame, uc_results_root, monkeypatch
):
    """The DA commitment (one CC unit) leaves P1a short; the RUC adds the
    second unit on the triggered days only, never removes a DA unit, and P1b
    serves the actual load."""
    _inject_increment(monkeypatch, -200.0)
    off, st_off, demand = _solve(_cfg())
    on, st_on, _ = _solve(_cfg(uc_reliability_commitment=True))

    # The arm without RUC: one CC unit by day, P1 short 40 MW each day hour.
    assert (st_off.schedule.u[0, DAY_HOURS] == 1).all()
    np.testing.assert_allclose(off.p1.slack[0, DAY_HOURS], 40.0, atol=1e-6)

    ruc = st_on.log["ruc"]
    assert ruc["trigger_hours"] == DAY_HOURS.size
    assert ruc["trigger_days"] == [0, 1]
    assert ruc["add_only"] is True and ruc["added_floor_mwh_outside_swept"] == 0.0
    # The DA schedule is kept and equals the arm without RUC (same DA problem).
    assert np.array_equal(st_on.schedule_da.u, st_off.schedule.u)
    assert st_on.log["engine"]["input_digest"] == st_off.log["engine"]["input_digest"]
    # Add-only everywhere; the second unit on every short hour.
    assert (st_on.schedule.u >= st_on.schedule_da.u).all()
    assert (st_on.schedule.u[0, DAY_HOURS] == 2).all()
    assert ruc["added_unit_hours"] == int(
        (st_on.schedule.u - st_on.schedule_da.u).sum()
    )
    # P1b (the scored P1) serves the actual load.
    assert float(on.p1.slack.sum()) <= 1e-6
    np.testing.assert_allclose(
        on.p1.dispatch.sum(axis=0) + on.p1.slack.sum(axis=0), demand[0], atol=1e-6
    )
    # The second unit's floor (2 x 50 MW) holds in P1b.
    assert (on.p1.dispatch[0, DAY_HOURS] >= 100.0 - 1e-6).all()

    # Uplift sidecar: the RUC make-whole columns, apart from the DA one.
    from market_sim.pipeline.uc import take_uc_artifacts, _STAGES

    _STAGES.append(st_on)
    art = take_uc_artifacts(on.p1)[-1]
    up = art.uplift
    assert {"ruc_added_units", "ruc_start_usd", "ruc_noload_usd"} <= set(up.columns)
    assert up["ruc_added_units"].sum() == ruc["added_unit_hours"]
    assert (up["ruc_noload_usd"] >= 0.0).all() and up["ruc_noload_usd"].sum() > 0.0
    assert art.log["ruc"]["n_windows"] >= 2


def test_zero_trigger_year_is_identical_to_the_arm_without_ruc(
    uc_params_frame, uc_results_root, monkeypatch
):
    """No P1a shortfall: the RUC runs no window, P1a is final, and every
    scored array and the schedule equal the arm without RUC bit for bit."""
    _inject_increment(monkeypatch, 0.0)
    a, st_a, _ = _solve(_cfg(), day_mw=150.0)
    b, st_b, _ = _solve(_cfg(uc_reliability_commitment=True), day_mw=150.0)
    assert st_b.log["ruc"]["trigger_hours"] == 0
    assert st_b.log["ruc"]["n_windows"] == 0
    assert st_b.schedule_da is None
    assert np.array_equal(st_a.schedule.u, st_b.schedule.u)
    assert np.array_equal(st_a.schedule.v, st_b.schedule.v)
    for name in ("dispatch", "prices", "slack", "dump"):
        assert np.array_equal(getattr(a.p1, name), getattr(b.p1, name)), name
    assert a.p1.objective_value == b.p1.objective_value
    assert b.p1_fleet_arrays is not None
    assert np.array_equal(a.p1_fleet_arrays.min_gen, b.p1_fleet_arrays.min_gen)
    assert np.array_equal(
        a.p1_fleet_arrays.availability, b.p1_fleet_arrays.availability
    )


def test_gate_off_runs_no_ruc(uc_params_frame, uc_results_root, monkeypatch):
    """Default (off): no RUC block, no DA copy, no RUC uplift columns."""
    _inject_increment(monkeypatch, -200.0)
    res, st, _ = _solve(_cfg())
    assert "ruc" not in st.log
    assert st.schedule_da is None and st.ruc_armed is False
    from market_sim.pipeline.uc import take_uc_artifacts, _STAGES

    _STAGES.append(st)
    up = take_uc_artifacts(res.p1)[-1].uplift
    assert "ruc_added_units" not in up.columns


def test_no_offline_capacity_adds_nothing(
    uc_params_frame, uc_results_root, monkeypatch
):
    """Both CC units already committed by the DA pass and P1a still short:
    the RUC window has nothing to add (add-only, never infeasible) and P1b
    equals P1a's commitment."""
    _inject_increment(monkeypatch, 0.0)
    res, st, demand = _solve(_cfg(uc_reliability_commitment=True), day_mw=500.0)
    assert st.log["ruc"]["trigger_hours"] > 0
    assert st.log["ruc"]["added_unit_hours"] == 0
    assert np.array_equal(st.schedule.u, st.schedule_da.u)
    # 60 + 200 + 150 = 410 MW against 500 MW: the shortfall is real.
    np.testing.assert_allclose(res.p1.slack[0, DAY_HOURS], 90.0, atol=1e-6)


def test_trigger_screen_reads_slack_and_the_largest_reserve_family():
    from market_sim.pipeline.uc import lp_feasibility_tolerance, ruc_trigger_hours

    tol = lp_feasibility_tolerance()
    assert 0.0 < tol < 1e-3
    slack = np.zeros((2, 5))
    slack[1, 1] = 5.0
    slack[0, 4] = tol / 2.0  # round-off, not a shortfall
    fam = np.zeros((5, 2))
    fam[3, 0] = 12.0
    fam[3, 1] = 4.0
    trig, s, r = ruc_trigger_hours(
        SimpleNamespace(slack=slack, reserve_shortfall_by_family=fam), tol
    )
    assert trig.tolist() == [False, True, False, True, False]
    assert r[3] == 12.0  # nested families are not summed
    trig2, _, _ = ruc_trigger_hours(
        SimpleNamespace(slack=slack, reserve_shortfall_by_family=None), tol
    )
    assert trig2.tolist() == [False, True, False, False, False]


def test_da_schedule_reuse_from_a_committed_bundle(
    uc_params_frame, uc_results_root, monkeypatch, tmp_path
):
    """R15: a run whose UC input digest equals a committed leg's reads that
    leg's DA schedule instead of re-solving, and solves the same P1; a
    different DA problem raises instead of silently re-solving."""
    from market_sim.pipeline.uc import _STAGES, take_uc_artifacts, write_uc_artifacts

    _inject_increment(monkeypatch, -200.0)
    leg, st_leg, _ = _solve(_cfg(uc_reliability_commitment=True))
    _STAGES.append(st_leg)
    bundle = tmp_path / "bundle"
    # The committed leg's schedule sidecar is its FINAL schedule; the reuse
    # needs the DA one, so write the arm-without-RUC leg (the same DA problem).
    base, st_base, _ = _solve(_cfg())
    _STAGES.clear()
    _STAGES.append(st_base)
    write_uc_artifacts(bundle, 2023, take_uc_artifacts(base.p1))

    re, st_re, _ = _solve(
        _cfg(uc_reliability_commitment=True, uc_da_schedule_reuse_bundle=str(bundle))
    )
    src = st_re.log["engine"]["reused_schedule"]
    assert src["source"] == "committed_bundle" and src["bundle"] == str(bundle)
    assert st_re.log["engine"]["input_digest"] == st_base.log["engine"]["input_digest"]
    assert np.array_equal(st_re.schedule_da.u, st_leg.schedule_da.u)
    assert np.array_equal(st_re.schedule.u, st_leg.schedule.u)
    assert np.array_equal(re.p1.dispatch, leg.p1.dispatch)
    assert np.array_equal(re.p1.prices, leg.p1.prices)

    # A different DA problem (another forecast) cannot take that schedule.
    _inject_increment(monkeypatch, -150.0)
    with pytest.raises(ValueError, match="digest"):
        _solve(
            _cfg(
                uc_reliability_commitment=True,
                uc_da_schedule_reuse_bundle=str(bundle),
            )
        )
    # A bundle without the year raises too.
    with pytest.raises(FileNotFoundError):
        _solve(_cfg(uc_da_schedule_reuse_bundle=str(tmp_path / "empty")))


@pytest.mark.parametrize(
    "kw, match",
    [
        (
            dict(unit_commitment_milp=False, uc_commitment_demand_source="actual"),
            "needs unit_commitment_milp",
        ),
        (dict(uc_commitment_demand_source="actual"), "da_forecast"),
    ],
)
def test_ruc_refusals(kw, match):
    with pytest.raises(ValueError, match=match):
        _cfg(uc_reliability_commitment=True, **kw)


def test_basis_and_reuse_refusals():
    with pytest.raises(ValueError, match="must be one of"):
        _cfg(uc_reliability_commitment=True, uc_ruc_load_basis="forecast_of_choice")
    # The measured intraday basis is SPP's MTLF vintages: other ISOs and
    # forecast mode are refused at construction (UC-DA-BASIS).
    with pytest.raises(ValueError, match="backcast only, ISOs"):
        _cfg(uc_reliability_commitment=True, uc_ruc_load_basis="iso_intraday_forecast")
    with pytest.raises(ValueError, match="backcast only, ISOs"):
        _cfg(
            iso="SPP",
            mode="forecast",
            uc_reliability_commitment=True,
            uc_ruc_load_basis="iso_intraday_forecast",
        )
    ok = _cfg(
        iso="SPP",
        uc_reliability_commitment=True,
        uc_ruc_load_basis="iso_intraday_forecast",
    )
    assert ok.uc_ruc_load_basis == "iso_intraday_forecast"
    with pytest.raises(ValueError, match="read only by the UC stage"):
        ScenarioConfig(iso="SPP", uc_da_schedule_reuse_bundle="results/x")


def test_ruc_load_basis_seam_reads_the_intraday_forecast(monkeypatch):
    """ "actual" hands back the stage's P1 demand (the same object);
    "iso_intraday_forecast" reads the data layer with the stage's config,
    P1 demand and runtime zones."""
    import market_sim.pipeline.uc as puc

    demand = np.full((2, 4), 100.0)
    seen = {}

    def fake(config, d, zones):
        seen.update(config=config, d=d, zones=zones)
        return d + 7.0

    monkeypatch.setattr(puc, "intraday_commitment_demand", fake)
    stage = SimpleNamespace(
        config=SimpleNamespace(uc_ruc_load_basis="actual"),
        demand=demand,
        zone_names=["A", "B"],
    )
    assert puc.ruc_load_basis_demand(stage) is demand
    stage.config = SimpleNamespace(uc_ruc_load_basis="iso_intraday_forecast")
    np.testing.assert_array_equal(puc.ruc_load_basis_demand(stage), demand + 7.0)
    assert seen["zones"] == ["A", "B"] and seen["config"] is stage.config
    stage.config = SimpleNamespace(uc_ruc_load_basis="other")
    with pytest.raises(ValueError, match="has no loader"):
        puc.ruc_load_basis_demand(stage)


def test_defaults_leave_the_cache_key_unmoved():
    a = ScenarioConfig(iso="SPP")
    b = ScenarioConfig(
        iso="SPP",
        uc_reliability_commitment=False,
        uc_ruc_load_basis="actual",
        uc_da_schedule_reuse_bundle="",
    )
    assert a.cache_key() == b.cache_key()


def test_sweep_carries_a_ruc_unit_through_its_min_up(
    uc_params_frame, uc_results_root, monkeypatch
):
    """Only day 0 is short, but the unit the RUC starts there owes a 30 h
    min-up: the sweep re-solves day 1 too (an untriggered window) and keeps
    the unit on through the night, add-only, until the state rejoins."""
    import market_sim.data.commitment_demand as cd

    from .conftest import toy_uc_params

    uc_params_frame(toy_uc_params(ut_h=30))
    inc = np.zeros((1, 8760))
    inc[0, 7:24] = -200.0
    monkeypatch.setattr(
        cd, "backcast_commitment_increment", lambda *a, **k: (inc.copy(), 0)
    )
    res, st, _ = _solve(_cfg(uc_reliability_commitment=True))
    ruc = st.log["ruc"]
    assert ruc["trigger_days"] == [0]
    flags = [w["triggered"] for w in ruc["windows"]]
    assert flags[0] is True and False in flags  # a sweep window ran
    assert (st.schedule.u >= st.schedule_da.u).all()
    # The min-up row (Rajan-Takriti, clustered units are interchangeable):
    # every unit started in the last 30 h is still online, so the unit the
    # RUC started on day 0 keeps one unit on through the day-1 night, where
    # the DA schedule had none.
    u, v = st.schedule.u[0].astype(int), st.schedule.v[0].astype(int)
    csum = np.concatenate([[0], np.cumsum(v)])
    recent = csum[1:] - csum[np.maximum(np.arange(T) + 1 - 30, 0)]
    assert (u >= recent).all()
    night = slice(24, 31)
    assert (st.schedule.u[0, night] > st.schedule_da.u[0, night]).all()
    assert ruc["added_floor_mwh_outside_swept"] == 0.0
    assert float(res.p1.slack[:, 7:24].sum()) <= 1e-6
