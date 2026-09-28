"""Tests for the same-year measured pile receipts (NWPP-NEXT-9,
coal_monthly_pile_measured_receipts).

Trivial-first: a measured row replaces the ratable m/12 profile on both sides of
the cumulative pile, a NaN row keeps it, ``None`` is byte-identical to NEXT-8,
the clips still bind, the builder reads the year's own Page 5 lots by month and
purchase type, and the gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data import coal_fuel_inventory as cfi  # noqa: E402
from scripts.run_calibration import resolve_coal_measured_receipts  # noqa: E402
from tests.unit.data.test_coal_fuel_inventory import _coal_fleet  # noqa: E402

_YEAR = 8760


def _pile(measured=None, n=1, parts=None):
    fleet = _coal_fleet(list(range(1, n + 1)), pmax=1e6, hours=_YEAR)
    return cfi.build_coal_monthly_pile(
        fleet,
        np.arange(n),
        np.arange(n),
        np.full(n, 10.0),
        np.full((n, 1), 2_400.0),  # stock 1,200 + ratable receipts 1,200
        (1_200.0,) * n,
        {i: (1_200.0, -600.0) for i in range(n)} if parts is None else parts,
        _YEAR,
        measured=measured,
    )


def test_none_is_the_ratable_pile():
    c0, f0, _m0, _p0 = _pile()
    c1, f1, _m1, _p1 = _pile(measured=None)
    assert np.array_equal(c0, c1) and np.array_equal(f0, f1)


def test_measured_row_replaces_ratable_on_both_sides():
    # A shortfall year: nothing arrives until July, then 200 a month.
    r = np.cumsum([0.0] * 6 + [200.0] * 6)[None, :]
    c = np.cumsum([0.0] * 6 + [100.0] * 6)[None, :]
    ceiling, floor, _mi, _p = _pile(measured=(r, c))
    assert ceiling[0].tolist() == pytest.approx((1_200.0 + r[0]).tolist())
    assert floor[0].tolist() == pytest.approx(np.maximum(-600.0 + c[0], 0).tolist())
    assert ceiling[0, 0] == pytest.approx(1_200.0)  # no Jan inflow: stock only


def test_nan_row_keeps_ratable():
    r = np.vstack([np.full(12, np.nan), np.cumsum(np.full(12, 50.0))])
    c = np.vstack([np.full(12, np.nan), np.zeros(12)])
    ceiling, floor, _mi, _p = _pile(measured=(r, c), n=2)
    ratable, rfloor, _m, _q = _pile(n=2)
    assert np.array_equal(ceiling[0], ratable[0])
    assert np.array_equal(floor[0], rfloor[0])
    assert ceiling[1, -1] == pytest.approx(1_800.0)
    assert np.all(floor[1] == 0.0)  # (S_dec - S_max) < 0 and no contract lots


def test_floor_still_clipped_to_the_measured_ceiling():
    r = np.zeros((1, 12))
    c = np.cumsum(np.full(12, 500.0))[None, :]
    ceiling, floor, _mi, prov = _pile(measured=(r, c), parts={0: (0.0, 0.0)})
    assert np.all(floor <= ceiling + 1e-9)
    assert prov.floor_clipped_to_ceiling > 0


def test_shape_mismatch_raises():
    with pytest.raises(ValueError, match="measured receipts"):
        _pile(measured=(np.zeros((2, 12)), np.zeros((2, 12))))


def test_builder_reads_same_year_lots_by_month_and_purchase_type(monkeypatch):
    rec = pd.DataFrame(
        {
            "plant_id": [1, 1, 1, 2],
            "year": [2023] * 4,
            "month": [1, 1, 3, 2],
            "purchase_type": ["C", "S", "NC", "C"],
            "quantity_tons": [10.0, 5.0, 2.0, 1.0],
            "heat_content_mmbtu_per_ton": [20.0, 18.0, 20.0, 17.0],
        }
    )
    import market_sim.data.coal_receipts as cr

    monkeypatch.setattr(cr, "load_coal_receipts", lambda years: rec)
    monkeypatch.setattr(cfi, "coal_yard_groups", lambda f, reference_dir=None: {1: {1}, 3: {3}})
    fleet = _coal_fleet([1], hours=24)
    cum_r, cum_c, prov = cfi.build_coal_measured_receipts(fleet, 2023, (1, 3))
    assert cum_r[0, :3].tolist() == pytest.approx([290.0, 290.0, 330.0])
    assert cum_c[0, :3].tolist() == pytest.approx([200.0, 200.0, 240.0])
    assert np.isnan(cum_r[1]).all()  # yard 3 has no same-year row: ratable
    assert prov.n_measured == 1 and prov.n_ratable == 1
    assert prov.receipts_mmbtu == pytest.approx(330.0)


def test_builder_none_without_a_year_file(monkeypatch):
    import market_sim.data.coal_receipts as cr

    monkeypatch.setattr(cr, "load_coal_receipts", lambda years: pd.DataFrame())
    assert cfi.build_coal_measured_receipts(_coal_fleet([1], hours=24), 2025, (1,)) is None


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast").with_overrides(**kw)


def test_gate_default_off():
    assert resolve_coal_measured_receipts(_cfg(), "NWPP", True) is False


def test_gate_arms_for_nwpp_with_the_pile():
    assert resolve_coal_measured_receipts(
        _cfg(coal_monthly_pile_measured_receipts=True), "NWPP", True
    )


def test_gate_requires_the_pile():
    with pytest.raises(ValueError, match="requires coal_fuel_inventory_monthly_pile"):
        resolve_coal_measured_receipts(
            _cfg(coal_monthly_pile_measured_receipts=True), "NWPP", False
        )


def test_gate_refuses_other_isos():
    with pytest.raises(ValueError, match="R-ISO-SCOPE"):
        resolve_coal_measured_receipts(
            _cfg(coal_monthly_pile_measured_receipts=True), "MISO", True
        )


def test_cache_key_unchanged_off_and_distinct_armed():
    base = ScenarioConfig()
    assert (
        base.cache_key()
        == ScenarioConfig(coal_monthly_pile_measured_receipts=False).cache_key()
    )
    assert (
        base.cache_key()
        != ScenarioConfig(coal_monthly_pile_measured_receipts=True).cache_key()
    )
