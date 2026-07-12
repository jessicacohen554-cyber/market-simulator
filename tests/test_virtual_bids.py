"""Tests for the PJM DA virtual-bid layer (market_sim.data.virtual_bids)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.virtual_bids import (  # noqa: E402
    INC_PRICE_FLOOR_USD,
    VIRTUAL_DEC_GROUP,
    VIRTUAL_INC_GROUP,
    _hourly_rungs,
    apply_virtual_bid_prices,
    apply_virtual_profiles,
)


def _bids_frame() -> pd.DataFrame:
    """Two hours of synthetic INC/DEC curves (long by price point)."""
    rows = []
    # hour 0: DEC 100 MW @ $200, 100 MW @ $50; INC 80 MW @ $10, 80 MW @ $90.
    rows += [
        {"t": 0, "price": 200.0, "inc": 0.0, "dec": 100.0},
        {"t": 0, "price": 50.0, "inc": 0.0, "dec": 100.0},
        {"t": 0, "price": 10.0, "inc": 80.0, "dec": 0.0},
        {"t": 0, "price": 90.0, "inc": 80.0, "dec": 0.0},
    ]
    # hour 1: empty DEC; INC 10 MW @ -$5 (negative offer).
    rows += [{"t": 1, "price": -5.0, "inc": 10.0, "dec": 0.0}]
    return pd.DataFrame(rows)


def test_hourly_rungs_dec_descending_and_equal_mw():
    """DEC rungs read the curve in willingness-to-pay order, equal-MW split."""
    mw, price = _hourly_rungs(_bids_frame(), "dec", True, hours=3, n_rungs=2)
    # hour 0: 200 MW total -> two 100 MW rungs, top rung at the $200 block.
    assert mw[:, 0] == pytest.approx([100.0, 100.0])
    assert price[0, 0] > price[1, 0]
    assert price[0, 0] == pytest.approx(200.0, abs=40.0)
    assert price[1, 0] == pytest.approx(50.0, abs=40.0)
    # hour 1 has no DEC bids; hour 2 absent from the frame.
    assert mw[:, 1] == pytest.approx([0.0, 0.0])
    assert mw[:, 2] == pytest.approx([0.0, 0.0])


def test_hourly_rungs_inc_ascending():
    """INC rungs read the curve cheapest-first (offer order)."""
    mw, price = _hourly_rungs(_bids_frame(), "inc", False, hours=2, n_rungs=2)
    assert mw[:, 0] == pytest.approx([80.0, 80.0])
    assert price[0, 0] < price[1, 0]
    # hour 1: a single 10 MW negative-priced INC block.
    assert mw[:, 1] == pytest.approx([5.0, 5.0])
    assert price[0, 1] == pytest.approx(-5.0)


class _FakeFleet:
    """Minimal FleetArrays stand-in for the bound/price appliers."""

    def __init__(self, unit_ids, pmax, pmin, hours):
        self.unit_ids = np.asarray(unit_ids, dtype=object)
        self.pmax = np.asarray(pmax, dtype=float)
        self.pmin = np.asarray(pmin, dtype=float)
        self.availability = np.ones((len(unit_ids), hours))
        self.min_gen = None


def test_apply_virtual_profiles_inc_and_dec_bounds():
    """INC MW rides availability; DEC MW rides a min_gen lower bound."""
    hours = 4
    fleet = _FakeFleet(
        ["thermal_1", "Z1_vINC_R00", "Z1_vDEC_R00"],
        pmax=[500.0, 200.0, 0.0],
        pmin=[0.0, 0.0, -300.0],
        hours=hours,
    )
    inc_mw = np.array([200.0, 100.0, 0.0, 50.0])
    dec_mw = np.array([300.0, 0.0, 150.0, 75.0])
    n = apply_virtual_profiles(fleet, {"Z1_vINC_R00": inc_mw, "Z1_vDEC_R00": dec_mw})
    assert n == 2
    # INC upper bound = pmax x availability reproduces the hourly MW.
    assert fleet.pmax[1] * fleet.availability[1] == pytest.approx(inc_mw)
    # DEC lower bound is -MW(t); other units keep their pmin seed.
    assert fleet.min_gen is not None
    assert fleet.min_gen[2] == pytest.approx(-dec_mw)
    assert fleet.min_gen[0] == pytest.approx(np.zeros(hours))
    # Thermal availability untouched.
    assert fleet.availability[0] == pytest.approx(np.ones(hours))


def test_apply_virtual_profiles_inc_only_skips_min_gen():
    """An INC-only profile set must not materialize the min_gen matrix."""
    fleet = _FakeFleet(["Z1_vINC_R00"], pmax=[100.0], pmin=[0.0], hours=2)
    apply_virtual_profiles(fleet, {"Z1_vINC_R00": np.array([10.0, 20.0])})
    assert fleet.min_gen is None


def test_apply_virtual_bid_prices_writes_rows():
    """Price rows land on the units' fuel_prices rows; others untouched."""
    fleet = _FakeFleet(
        ["thermal_1", "Z1_vDEC_R00"], pmax=[500.0, 0.0], pmin=[0.0, -100.0], hours=3
    )
    fuel = np.full((2, 3), 3.5)
    n = apply_virtual_bid_prices(
        fuel, fleet, {"Z1_vDEC_R00": np.array([120.0, 80.0, -10.0])}
    )
    assert n == 1
    assert fuel[1] == pytest.approx([120.0, 80.0, -10.0])
    assert fuel[0] == pytest.approx(np.full(3, 3.5))


def test_inc_price_floor_constant_positive():
    """The INC clamp floor must stay non-negative (dump-guard safety)."""
    assert INC_PRICE_FLOOR_USD >= 0.0
    assert VIRTUAL_INC_GROUP != VIRTUAL_DEC_GROUP
