"""Tests for the PJM DA virtual-bid layer (market_sim.data.virtual_bids).

The mechanism is a single per-hour symmetric NET virtual curve
(``net(λ) = Σ DEC≥λ − Σ INC≤λ``): the ``net > 0`` region rendered as
DEC-form withdrawal rungs and the ``net < 0`` region as INC-form net-supply
rungs (pjm-105; docs/FINDING-pjm-midmerit-level-2026-07.md §6 item 1). The
tests exercise the symmetric compression (trivial hand-built curve first,
then round-trip properties) and the DEC/INC bound and price appliers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.virtual_bids import (  # noqa: E402
    VIRTUAL_DEC_GROUP,
    VIRTUAL_INC_GROUP,
    _hourly_net_rungs,
    apply_virtual_bid_prices,
    apply_virtual_profiles,
)


def _bids_frame() -> pd.DataFrame:
    """Two hours of synthetic INC/DEC curves (long by price point)."""
    rows = []
    # hour 0: DEC 100 MW @ $200, 100 MW @ $50; INC 80 MW @ $10, 80 MW @ $90.
    # Net: 200 (λ<10) -> 120 (10-50) -> 20 (50-90) -> -60 (>90: net supply).
    rows += [
        {"t": 0, "price": 200.0, "inc": 0.0, "dec": 100.0},
        {"t": 0, "price": 50.0, "inc": 0.0, "dec": 100.0},
        {"t": 0, "price": 10.0, "inc": 80.0, "dec": 0.0},
        {"t": 0, "price": 90.0, "inc": 80.0, "dec": 0.0},
    ]
    # hour 1: empty DEC; INC 10 MW @ -$5 (net supply everywhere).
    rows += [{"t": 1, "price": -5.0, "inc": 10.0, "dec": 0.0}]
    return pd.DataFrame(rows)


def _dec_cleared(mw: np.ndarray, price: np.ndarray, t: int, lam: float) -> float:
    """Cleared DEC-form withdrawal at dual ``lam`` (blocks with price > lam)."""
    return float(mw[price[:, t] > lam, t].sum())


def _inc_cleared(mw: np.ndarray, price: np.ndarray, t: int, lam: float) -> float:
    """Cleared INC-form net supply at dual ``lam`` (blocks with price < lam)."""
    return float(mw[price[:, t] < lam, t].sum())


def test_trivial_three_point_curve_round_trip():
    """Trivial case first: 1 hour, a hand-built 3-point curve, both sides.

    DEC 60 MW @ $40; INC 25 MW @ $20 and 50 MW @ $80. The monotone net
    curve: +60 (λ<20) -> +35 (20-40) -> -25 (40-80) -> -75 (>80). The
    crossing λ0 = $40 (net demand exhausts inside the $40 block). The DEC
    side must carry exactly 60 MW at prices ≤ $40; the INC side exactly 75
    MW at prices ≥ $40.
    """
    rows = [
        {"t": 0, "price": 40.0, "inc": 0.0, "dec": 60.0},
        {"t": 0, "price": 20.0, "inc": 25.0, "dec": 0.0},
        {"t": 0, "price": 80.0, "inc": 50.0, "dec": 0.0},
    ]
    dec_mw, dec_price, inc_mw, inc_price = _hourly_net_rungs(
        pd.DataFrame(rows), hours=1, n_rungs=4
    )
    assert dec_mw[:, 0].sum() == pytest.approx(60.0)  # net-demand region
    assert inc_mw[:, 0].sum() == pytest.approx(75.0)  # net-supply region
    # Region split at the crossing: DEC prices ≤ λ0 ≤ INC prices.
    assert dec_price[:, 0].max() <= 40.0 + 1e-9
    assert inc_price[:, 0].min() >= 40.0 - 1e-9
    # Round-trip the net curve at duals between the submitted points:
    # net(λ) = cleared DEC − cleared INC must match the analytic steps at
    # the region endpoints (quantile smoothing only moves interior levels).
    net_lo = _dec_cleared(dec_mw, dec_price, 0, 5.0) - _inc_cleared(
        inc_mw, inc_price, 0, 5.0
    )
    assert net_lo == pytest.approx(60.0)  # below every price point
    net_hi = _dec_cleared(dec_mw, dec_price, 0, 100.0) - _inc_cleared(
        inc_mw, inc_price, 0, 100.0
    )
    assert net_hi == pytest.approx(-75.0)  # above every price point


def test_net_rungs_equal_mw_and_totals():
    """Equal-MW rungs; DEC mass = Σ dec, INC mass = Σ inc, per hour."""
    dec_mw, _, inc_mw, _ = _hourly_net_rungs(_bids_frame(), hours=3, n_rungs=4)
    # hour 0: total DEC = 200 -> four 50 MW rungs; total INC = 160 -> 40 MW.
    assert dec_mw[:, 0] == pytest.approx([50.0, 50.0, 50.0, 50.0])
    assert inc_mw[:, 0] == pytest.approx([40.0, 40.0, 40.0, 40.0])
    # hour 1: supply-only (10 MW INC, no DEC) — the symmetric form renders
    # the INC side where the old clamp dropped the hour entirely.
    assert dec_mw[:, 1] == pytest.approx(np.zeros(4))
    assert inc_mw[:, 1].sum() == pytest.approx(10.0)
    # hour 2 absent from the frame.
    assert dec_mw[:, 2] == pytest.approx(np.zeros(4))
    assert inc_mw[:, 2] == pytest.approx(np.zeros(4))


def test_net_rungs_prices_ascending_and_sides_ordered():
    """Rung prices are non-decreasing per side and split at the crossing."""
    dec_mw, dec_price, inc_mw, inc_price = _hourly_net_rungs(
        _bids_frame(), hours=3, n_rungs=4
    )
    assert np.all(np.diff(dec_price[:, 0]) >= -1e-9)
    assert np.all(np.diff(inc_price[:, 0]) >= -1e-9)
    # hour 0 crossing is inside the $90 block: DEC ≤ $90 ≤ INC, and the DEC
    # side never prices below the cheapest submitted point.
    assert dec_price[:, 0].max() <= 90.0 + 1e-6
    assert dec_price[:, 0].min() >= 10.0 - 1e-6
    assert inc_price[:, 0].min() >= 90.0 - 1e-6
    assert dec_price[:, 0].max() <= inc_price[:, 0].min() + 1e-6


def test_net_rungs_survival_monotone_net_curve():
    """Cleared net (DEC − INC) is non-increasing in the dual over both regions.

    Below the cheapest bid the whole net demand clears; above the highest
    offer the whole net supply clears — a valid monotone net curve spanning
    [+Σdec, −Σinc]. Intermediate levels are the MW-weighted-quantile
    smoothing of the step curve.
    """
    dec_mw, dec_price, inc_mw, inc_price = _hourly_net_rungs(
        _bids_frame(), hours=1, n_rungs=40
    )
    lams = np.linspace(-10.0, 250.0, 120)
    net = np.array(
        [
            _dec_cleared(dec_mw, dec_price, 0, lam)
            - _inc_cleared(inc_mw, inc_price, 0, lam)
            for lam in lams
        ]
    )
    assert net[0] == pytest.approx(200.0)  # all net demand
    assert net[-1] == pytest.approx(-160.0)  # all net supply
    assert np.all(np.diff(net) <= 1e-9)  # monotone non-increasing


def test_net_rungs_inc_dominated_hour_bounded_by_net():
    """An INC-heavy hour renders both regions, each bounded by its own mass.

    Supply >> demand still yields at most Σdec MW of withdrawal and exactly
    Σinc MW of net-supply capacity — the symmetric mirror of the old
    no-supply clamp test (the INC side is the measured NET position's
    negative region, never the gross INC curves of the condemned pjm-101
    form).
    """
    rows = [
        {"t": 0, "price": 20.0, "inc": 500.0, "dec": 30.0},
        {"t": 0, "price": 60.0, "inc": 400.0, "dec": 20.0},
    ]
    dec_mw, dec_price, inc_mw, inc_price = _hourly_net_rungs(
        pd.DataFrame(rows), hours=1, n_rungs=8
    )
    assert dec_mw[:, 0].sum() == pytest.approx(50.0)  # total DEC only
    assert inc_mw[:, 0].sum() == pytest.approx(900.0)  # total INC
    # Crossing λ0 = $20 (net demand exhausts inside the first block).
    assert dec_price[:, 0].max() <= 20.0 + 1e-9
    assert inc_price[:, 0].min() >= 20.0 - 1e-9


class _FakeFleet:
    """Minimal FleetArrays stand-in for the bound/price appliers."""

    def __init__(self, unit_ids, pmax, pmin, hours):
        self.unit_ids = np.asarray(unit_ids, dtype=object)
        self.pmax = np.asarray(pmax, dtype=float)
        self.pmin = np.asarray(pmin, dtype=float)
        self.availability = np.ones((len(unit_ids), hours))
        self.min_gen = None


def test_apply_virtual_profiles_dec_bounds():
    """Net-demand (DEC) MW rides a min_gen lower bound; others keep their seed."""
    hours = 4
    fleet = _FakeFleet(
        ["thermal_1", "Z1_vNET_R00", "Z1_vNET_R01"],
        pmax=[500.0, 0.0, 0.0],
        pmin=[0.0, -300.0, -150.0],
        hours=hours,
    )
    r00 = np.array([300.0, 0.0, 150.0, 75.0])
    r01 = np.array([100.0, 50.0, 0.0, 25.0])
    n = apply_virtual_profiles(fleet, {"Z1_vNET_R00": r00, "Z1_vNET_R01": r01})
    assert n == 2
    assert fleet.min_gen is not None
    assert fleet.min_gen[1] == pytest.approx(-r00)
    assert fleet.min_gen[2] == pytest.approx(-r01)
    # Real thermal unit keeps its pmin seed and untouched availability.
    assert fleet.min_gen[0] == pytest.approx(np.zeros(hours))
    assert fleet.availability[0] == pytest.approx(np.ones(hours))


def test_apply_virtual_profiles_mixed_dec_and_inc():
    """DEC rows ride min_gen, INC rows ride availability, in one profile set."""
    hours = 3
    fleet = _FakeFleet(
        ["thermal_1", "Z1_vNET_R00", "Z1_vINC_R00"],
        pmax=[500.0, 0.0, 120.0],
        pmin=[0.0, -200.0, 0.0],
        hours=hours,
    )
    dec = np.array([200.0, 0.0, 90.0])
    inc = np.array([0.0, 120.0, 60.0])
    n = apply_virtual_profiles(fleet, {"Z1_vNET_R00": dec, "Z1_vINC_R00": inc})
    assert n == 2
    assert fleet.min_gen[1] == pytest.approx(-dec)
    # INC upper bound: pmax × availability reproduces the hourly MW profile.
    assert fleet.pmax[2] * fleet.availability[2] == pytest.approx(inc)
    # INC rows never receive a floor of any kind.
    assert fleet.min_gen[2] == pytest.approx(np.zeros(hours))


def test_apply_virtual_bid_prices_writes_rows():
    """Price rows land on the units' fuel_prices rows; others untouched."""
    fleet = _FakeFleet(
        ["thermal_1", "Z1_vNET_R00"], pmax=[500.0, 0.0], pmin=[0.0, -100.0], hours=3
    )
    fuel = np.full((2, 3), 3.5)
    n = apply_virtual_bid_prices(
        fuel, fleet, {"Z1_vNET_R00": np.array([120.0, 80.0, -10.0])}
    )
    assert n == 1
    assert fuel[1] == pytest.approx([120.0, 80.0, -10.0])
    assert fuel[0] == pytest.approx(np.full(3, 3.5))


def test_virtual_group_constants():
    """Both sides carry non-physical groups (reserve-ineligible, no bench)."""
    assert VIRTUAL_DEC_GROUP == "VIRTUAL_DEC"
    assert VIRTUAL_INC_GROUP == "VIRTUAL_INC"
