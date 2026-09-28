"""R-CAISO-13 ``caiso_eia930_clock_repair``: the CISO late-stamp frame repair.

Synthetic extracts only (1 BA, a few hours), per the repo's trivial-case-first
testing pattern. Checks: the unarmed and non-CISO paths return the SAME object;
inside a registered window the value stamped ``s`` lands on ``s - 1 h``; the
seam hour takes its neighbours' mean; the column families are respected; the
switch clears the frame caches; and the supply-consistent demand transform
moves only the EIA-930 term.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config import constants
from market_sim.data.eia930 import demand as D
from market_sim.data.eia930 import frames as F


@pytest.fixture(autouse=True)
def _disarm():
    """Leave the process switch off after every test."""
    F.set_caiso_eia930_clock_repair(False)
    yield
    F.set_caiso_eia930_clock_repair(False)


def _extract(n: int = 8) -> pd.DataFrame:
    """An 8-row hourly CISO-like extract with distinct values per column."""
    utc = pd.date_range("2024-01-01 00:00", periods=n, freq="h")
    k = np.arange(n, dtype=float)
    return pd.DataFrame(
        {
            "UTC time": utc,
            "Demand": 100.0 + k,
            "Demand forecast": 500.0 + k,
            "Net generation": 200.0 + k,
            "Total interchange": 300.0 + k,
            "NG: SUN": 400.0 + k,
        }
    )


def _windows(monkeypatch, gen, dem):
    monkeypatch.setattr(
        constants,
        "EIA930_CISO_CLOCK_LATE_WINDOWS_UTC",
        {"generation": gen, "demand": dem},
    )


def test_unarmed_returns_same_object():
    """Off by default: the input object comes back untouched."""
    df = _extract()
    assert F._repair_clock_late_windows(df, "CISO") is df


def test_other_ba_returns_same_object():
    """Armed, but a non-CISO BA is never touched."""
    F.set_caiso_eia930_clock_repair(True)
    df = _extract()
    assert F._repair_clock_late_windows(df, "ERCO") is df


def test_window_pulls_back_one_hour_with_mean_seam(monkeypatch):
    """Stamps 02..05 are late: row s-1 takes s; the last row takes the mean."""
    _windows(
        monkeypatch,
        ("2024-01-01 02:00", "2024-01-01 05:00"),
        ("2024-01-01 02:00", "2024-01-01 05:00"),
    )
    F.set_caiso_eia930_clock_repair(True)
    df = _extract()
    out = F._repair_clock_late_windows(df, "CISO")
    assert out is not df
    # Rows 1..4 take the values published at 2..5; row 5 (the seam) takes
    # mean(published 5, published 6); rows 0, 6, 7 are untouched.
    exp = np.array([0, 2, 3, 4, 5, 5.5, 6, 7], dtype=float)
    for col, base in (
        ("Demand", 100.0),
        ("Net generation", 200.0),
        ("Total interchange", 300.0),
        ("NG: SUN", 400.0),
    ):
        np.testing.assert_allclose(out[col].to_numpy(), base + exp)
    # Not in any family: never moved.
    np.testing.assert_allclose(out["Demand forecast"], df["Demand forecast"])
    # The raw input is never edited in place.
    np.testing.assert_allclose(df["Demand"], 100.0 + np.arange(8))


def test_families_have_independent_windows(monkeypatch):
    """Generation window empty of rows: only Demand moves."""
    _windows(
        monkeypatch,
        ("2030-01-01 00:00", "2030-01-02 00:00"),
        ("2024-01-01 03:00", "2024-01-01 04:00"),
    )
    F.set_caiso_eia930_clock_repair(True)
    out = F._repair_clock_late_windows(_extract(), "CISO")
    np.testing.assert_allclose(out["NG: SUN"], 400.0 + np.arange(8))
    np.testing.assert_allclose(
        out["Demand"], 100.0 + np.array([0, 1, 3, 4, 4.5, 5, 6, 7])
    )


def test_switch_clears_frame_caches(monkeypatch):
    """Changing the switch empties every cached frame."""
    calls = []
    for name in (
        "_eia_hourly_frame",
        "_eia_hourly_frame_filled",
        "_pool_hourly_frame",
        "_ercot_hourly_frame",
    ):
        fn = getattr(F, name)
        monkeypatch.setattr(fn, "cache_clear", lambda n=name: calls.append(n))
    F.set_caiso_eia930_clock_repair(True)
    assert len(calls) == 4
    F.set_caiso_eia930_clock_repair(True)  # idempotent: no second clear
    assert len(calls) == 4


def test_supply_consistent_moves_only_eia930_term(monkeypatch):
    """The CEMS/flat remainder is invariant; the 930 term shifts one row."""
    g = np.arange(D.HOURS_PER_YEAR, dtype=float)
    rest = np.full(D.HOURS_PER_YEAR, 1000.0)
    monkeypatch.setattr(
        D, "_supply_consistent_eia930_term", lambda y: g if y == 2024 else None
    )
    stamps = D._model_row_starts_utc(2024) + pd.Timedelta(hours=1)
    first, last = stamps[10], stamps[20]
    monkeypatch.setattr(
        constants,
        "EIA930_CISO_CLOCK_LATE_WINDOWS_UTC",
        {"generation": (str(first), str(last)), "demand": (str(first), str(last))},
    )
    out = D._repair_supply_consistent_clock(2024, g + rest)
    moved = out - rest
    np.testing.assert_allclose(moved[:9], g[:9])
    np.testing.assert_allclose(moved[9:20], g[10:21])
    assert moved[20] == pytest.approx(0.5 * (g[20] + g[21]))
    np.testing.assert_allclose(moved[21:], g[21:])


def test_model_row_starts_skip_leap_day():
    """The 8760 model clock drops Feb 29 and starts at PST midnight."""
    idx = D._model_row_starts_utc(2024)
    assert len(idx) == D.HOURS_PER_YEAR
    assert idx[0] == pd.Timestamp("2024-01-01 08:00")
    pst = idx - pd.Timedelta(hours=8)
    assert not ((pst.month == 2) & (pst.day == 29)).any()
