"""Tests for the PJM DA virtual-bid layer (market_sim.data.virtual_bids).

The mechanism is a single per-hour NET virtual-demand curve
(``Σ DEC≥λ − Σ INC≤λ``) rendered entirely as DEC-form withdrawal blocks —
no INC supply is ever injected (docs/FINDING-pjm-da-depth-midcurve-2026-07.md
§5). The tests exercise the net-curve compression and the DEC-form bound /
price appliers.
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
    _hourly_net_rungs,
    apply_virtual_bid_prices,
    apply_virtual_profiles,
)


def _bids_frame() -> pd.DataFrame:
    """Two hours of synthetic INC/DEC curves (long by price point)."""
    rows = []
    # hour 0: DEC 100 MW @ $200, 100 MW @ $50; INC 80 MW @ $10, 80 MW @ $90.
    # Net demand: 200 (λ<10) -> 120 (10-50) -> 20 (50-90) -> -60 (>90, clamped).
    rows += [
        {"t": 0, "price": 200.0, "inc": 0.0, "dec": 100.0},
        {"t": 0, "price": 50.0, "inc": 0.0, "dec": 100.0},
        {"t": 0, "price": 10.0, "inc": 80.0, "dec": 0.0},
        {"t": 0, "price": 90.0, "inc": 80.0, "dec": 0.0},
    ]
    # hour 1: empty DEC; INC 10 MW @ -$5 (net supply everywhere -> no demand).
    rows += [{"t": 1, "price": -5.0, "inc": 10.0, "dec": 0.0}]
    return pd.DataFrame(rows)


def _survival(mw: np.ndarray, price: np.ndarray, t: int, lam: float) -> float:
    """Cleared DEC-form withdrawal at dual ``lam`` (blocks with price > lam)."""
    return float(mw[price[:, t] > lam, t].sum())


def test_net_rungs_equal_mw_and_total_is_dec():
    """Every rung is equal-MW; the kept mass equals total submitted DEC."""
    mw, price = _hourly_net_rungs(_bids_frame(), hours=3, n_rungs=4)
    # hour 0: total DEC = 200 -> four 50 MW rungs.
    assert mw[:, 0] == pytest.approx([50.0, 50.0, 50.0, 50.0])
    assert mw[:, 0].sum() == pytest.approx(200.0)
    # hour 1 has no DEC (net supply only): clamped to zero, no withdrawal.
    assert mw[:, 1] == pytest.approx(np.zeros(4))
    # hour 2 absent from the frame.
    assert mw[:, 2] == pytest.approx(np.zeros(4))


def test_net_rungs_prices_ascending_and_bounded():
    """Rung prices rise with the willingness-to-pay curve, within bid range."""
    _, price = _hourly_net_rungs(_bids_frame(), hours=3, n_rungs=4)
    assert np.all(np.diff(price[:, 0]) >= -1e-9)  # non-decreasing
    # No rung is priced above the highest kept bid ($90 — the net crossing).
    assert price[:, 0].max() <= 90.0 + 1e-6
    assert price[:, 0].min() >= 10.0 - 1e-6


def test_net_rungs_survival_endpoints_and_monotone():
    """Cleared withdrawal spans [0, total_dec] and decreases with the dual.

    Below the cheapest kept bid the whole net demand clears; above the net
    crossing ($90) nothing clears (the net-negative tail is gone); and cleared
    MW is non-increasing in the dual (a valid downward-sloping demand curve).
    The intermediate levels are the MW-weighted-quantile smoothing of the step
    curve — the same np.interp discretization the per-side rungs used — so they
    are bounded by, not equal to, the analytic steps.
    """
    mw, price = _hourly_net_rungs(_bids_frame(), hours=1, n_rungs=40)
    assert _survival(mw, price, 0, -1.0) == pytest.approx(200.0)  # all net demand
    assert _survival(mw, price, 0, 90.0) == pytest.approx(0.0)  # past the crossing
    lams = np.linspace(-5.0, 100.0, 50)
    surv = np.array([_survival(mw, price, 0, lam) for lam in lams])
    assert np.all(np.diff(surv) <= 1e-9)  # non-increasing
    assert surv.max() <= 200.0 + 1e-9  # never exceeds total submitted DEC


def test_net_rungs_no_supply_side():
    """The net curve never injects supply: kept mass is bounded by total DEC.

    An INC-heavy hour (supply >> demand) still yields at most total-DEC MW of
    withdrawal — the net-negative tail is clamped, not turned into generation.
    """
    rows = [
        {"t": 0, "price": 20.0, "inc": 500.0, "dec": 30.0},
        {"t": 0, "price": 60.0, "inc": 400.0, "dec": 20.0},
    ]
    mw, _ = _hourly_net_rungs(pd.DataFrame(rows), hours=1, n_rungs=8)
    assert mw[:, 0].sum() == pytest.approx(50.0)  # total DEC only, no INC MW


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


def test_apply_virtual_profiles_positive_pmax_branch_uses_availability():
    """A positive-pmax profile rides availability and skips the min_gen matrix."""
    fleet = _FakeFleet(["Z1_vSUP_R00"], pmax=[100.0], pmin=[0.0], hours=2)
    apply_virtual_profiles(fleet, {"Z1_vSUP_R00": np.array([10.0, 20.0])})
    assert fleet.min_gen is None
    assert fleet.pmax[0] * fleet.availability[0] == pytest.approx([10.0, 20.0])


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


def test_virtual_dec_group_constant():
    """The pseudo-units carry the DEC withdrawal group (reserve-ineligible)."""
    assert VIRTUAL_DEC_GROUP == "VIRTUAL_DEC"
