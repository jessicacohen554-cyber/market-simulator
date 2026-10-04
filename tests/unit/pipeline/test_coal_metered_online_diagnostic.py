"""The DIAGNOSTIC metered coal online floor (closeout-SOCO-w3; rule 13: never promotable)."""

import ast
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.floor_mechanisms import MECH_DIAG_COAL_METERED_ONLINE
from market_sim.pipeline import commitment as pc

REPO = Path(__file__).resolve().parents[3]


def _fleet(avail_mustrun=1.0):
    """One coal plant (code 7) with a mustrun and a committed row, plus a CC row."""
    T = 3
    return SimpleNamespace(
        unit_ids=["COAL_Z_p7_committed", "COAL_Z_p7_mustrun", "CC_Z_p9_econ"],
        plant_code=np.array([7, 7, 9]),
        plant_group=np.array(["COAL_BIT", "COAL_BIT", "CC_REGULAR"]),
        pmax=np.array([100.0, 50.0, 200.0]),
        pmin=np.zeros(3),
        availability=np.array([[1.0] * T, [avail_mustrun] * T, [1.0] * T]),
        min_gen=None,
        min_gen_mechanism=None,
    )


def test_floor_fills_mustrun_first_then_committed():
    fa = _fleet()
    floor = pc._coal_metered_online_floor(fa, {7: np.array([30.0, 120.0, 0.0])})
    np.testing.assert_allclose(floor[1], [30.0, 50.0, 0.0])  # mustrun first
    np.testing.assert_allclose(floor[0], [0.0, 70.0, 0.0])  # remainder to committed
    np.testing.assert_allclose(floor[2], [0.0, 0.0, 0.0])  # never touches CC


def test_floor_clipped_to_available_capacity():
    fa = _fleet(avail_mustrun=0.0)
    floor = pc._coal_metered_online_floor(fa, {7: np.array([500.0, 500.0, 500.0])})
    np.testing.assert_allclose(floor[1], 0.0)  # outage relaxes the floor
    np.testing.assert_allclose(floor[0], 100.0)  # capped at committed pmax


def test_no_matching_plant_is_none():
    assert pc._coal_metered_online_floor(_fleet(), {99: np.ones(3)}) is None


def test_wrapper_off_returns_base_unchanged():
    base = object()
    cfg = SimpleNamespace(diagnostic_coal_metered_online_floor=False)
    assert (
        pc.wrap_coal_metered_online_diagnostic_prep(cfg, "SOCO", 2019, _fleet(), base)
        is base
    )


def test_wrapper_without_artifact_is_inert(monkeypatch):
    import market_sim.data.coal_metered_online as cmo

    monkeypatch.setattr(cmo, "load_coal_metered_online_floor", lambda *a: {})
    cfg = SimpleNamespace(diagnostic_coal_metered_online_floor=True)
    assert (
        pc.wrap_coal_metered_online_diagnostic_prep(cfg, "SOCO", 2019, _fleet(), None)
        is None
    )


def test_wrapper_composes_with_its_own_mechanism(monkeypatch):
    import market_sim.data.coal_metered_online as cmo

    monkeypatch.setattr(
        cmo,
        "load_coal_metered_online_floor",
        lambda *a: {7: np.array([30.0, 30.0, 30.0])},
    )
    seen = {}

    def fake_bridge(fa, floor, mech, **kw):
        seen["mech"], seen["floor"] = mech, floor
        return "floored"

    monkeypatch.setattr(pc, "_bridge_floored_fleet", fake_bridge)
    cfg = SimpleNamespace(diagnostic_coal_metered_online_floor=True)
    prep = pc.wrap_coal_metered_online_diagnostic_prep(
        cfg, "SOCO", 2019, _fleet(), None
    )
    assert prep(SimpleNamespace()) == "floored"
    assert seen["mech"] == MECH_DIAG_COAL_METERED_ONLINE
    np.testing.assert_allclose(seen["floor"][1], 30.0)


def test_forecast_mode_refuses_the_diagnostic():
    with pytest.raises(ValueError):
        ScenarioConfig(
            iso="SOCO", mode="forecast", diagnostic_coal_metered_online_floor=True
        )


@pytest.mark.parametrize(
    "rel",
    [
        "src/market_sim/pipeline/year.py",
        "src/market_sim/runner.py",
        "scripts/run_calibration.py",
    ],
)
def test_every_orchestrator_calls_the_wrapper(rel):
    tree = ast.parse((REPO / rel).read_text())
    called = {
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    }
    assert "wrap_coal_metered_online_diagnostic_prep" in called
