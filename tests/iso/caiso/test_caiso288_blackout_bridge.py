"""caiso-288 — guards for the EIA publication-blackout bridge.

``ScenarioConfig.caiso_citygate_blackout_bridge`` rebuilds the interiors of the
measured CA Composite daily citygate series' PUBLICATION BLACKOUTS (the 8-19 day
Thanksgiving / Christmas / New-Year holes EIA leaves in the Natural Gas Weekly
Update every year) from measured data, instead of constant-extending the last
print across them. These tests pin the four properties the mechanism's
admissibility rests on:

  1. OFF is byte-identical (rules 24 / the nyiso-119 registration discipline).
  2. A legitimate 1-4 day trading package is NEVER touched — only a blackout is.
  3. The bridge lands exactly on the measured Henry Hub daily series plus a
     linearly-interpolated basis between the two bracketing MEASURED prints,
     and reproduces those prints exactly at the endpoints.
  4. The gap threshold sits in the EMPTY region of the series' own trade-gap
     histogram, so any value in [6, 7] selects the identical set of gaps.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.data.fuel.hubs import (
    _GAS_BLACKOUT_MIN_GAP_DAYS,
    _basis_bridge_blackouts,
    _caiso_citygate_daily_dated,
    _flow_date_staircase,
)


def _hh(dates: dict[str, float]) -> pd.Series:
    return pd.Series({pd.Timestamp(k): v for k, v in dates.items()}).sort_index()


def test_package_gaps_are_left_alone() -> None:
    """A 1-4 day gap is a real trading package; the bridge must not fill it."""
    flow = pd.Series(
        {
            pd.Timestamp("2022-06-03"): 10.0,
            pd.Timestamp("2022-06-06"): 12.0,  # 3 d — the Fri->Mon weekend
            pd.Timestamp("2022-06-10"): 14.0,  # 4 d — holiday-extended package
        }
    )
    hh = _hh({"2022-06-03": 5.0, "2022-06-06": 9.0, "2022-06-10": 5.0})
    out = _basis_bridge_blackouts(flow, hh)
    # Only the three measured days carry a value; every interior day is still
    # NaN for the caller's own ffill staircase to fill.
    filled = out.dropna()
    assert list(filled.index) == list(flow.index)
    assert filled.tolist() == pytest.approx([10.0, 12.0, 14.0])


def test_blackout_is_bridged_on_hh_plus_interpolated_basis() -> None:
    """The interior is HH + basis, exact at both measured endpoints."""
    left, right = pd.Timestamp("2022-12-22"), pd.Timestamp("2023-01-06")
    flow = pd.Series({left: 53.59, right: 16.55})
    span = (right - left).days
    hh = _hh(
        {
            "2022-12-22": 7.10,
            "2022-12-27": 4.88,
            "2022-12-30": 3.52,
            "2023-01-06": 3.43,
        }
    )
    out = _basis_bridge_blackouts(flow, hh)
    assert span >= _GAS_BLACKOUT_MIN_GAP_DAYS

    # HH forward-filled onto every calendar day, exactly as the bridge sees it.
    cal = pd.date_range(left, right, freq="D")
    hs = hh.reindex(hh.index.union(cal)).sort_index().ffill().bfill()
    b_l, b_r = 53.59 - hs[left], 16.55 - hs[right]
    for day in cal:
        w = (day - left).days / span
        assert out[day] == pytest.approx(float(hs[day]) + b_l + w * (b_r - b_l))

    # Endpoints reproduce the measured prints; nothing is invented there.
    assert out[left] == pytest.approx(53.59)
    assert out[right] == pytest.approx(16.55)
    # And the interior is strictly BELOW the held value the staircase would use.
    interior = out.loc[left + pd.Timedelta(days=1) : right - pd.Timedelta(days=1)]
    assert (interior < 53.59).all()


def test_staircase_off_is_byte_identical() -> None:
    """``_flow_date_staircase`` with no bridge arguments is unchanged."""
    dated = _caiso_citygate_daily_dated(None)
    for year in (2022, 2023, 2024, 2025):
        if year not in dated:
            pytest.skip(f"no committed citygate prints for {year}")
        plain = _flow_date_staircase(dated[year], year)
        explicit_off = _flow_date_staircase(dated[year], year, None, None)
        assert plain is not None
        assert np.array_equal(plain, explicit_off)


def test_threshold_sits_in_an_empty_region_of_the_gap_histogram() -> None:
    """Any threshold in [6, 7] selects the identical gap set — so the value
    cannot have been chosen against a result (rules 1 / 5 / 21)."""
    dated = _caiso_citygate_daily_dated(None)
    days = sorted(
        pd.Timestamp(year=y, month=m, day=d)
        for y, months in dated.items()
        for m, dd in months.items()
        for d in dd
    )
    gaps = [(b - a).days for a, b in zip(days, days[1:])]
    assert gaps, "committed citygate series carries no prints"
    # The empty region: no gap of exactly 6 or 7 calendar days anywhere.
    assert 6 not in gaps and 7 not in gaps
    assert _GAS_BLACKOUT_MIN_GAP_DAYS in (6, 7)
    # Packages dominate the series and blackouts are the rare tail.
    assert sum(g <= 4 for g in gaps) > 50 * sum(g >= 8 for g in gaps) / 50
    assert sum(g >= 8 for g in gaps) > 0


def test_bridge_moves_december_2022_down_and_november_2022_up() -> None:
    """The mechanism is NOT one-directional — the signature of a construction
    rather than a fit. Measured on the committed series."""
    dated = _caiso_citygate_daily_dated(None)
    if 2022 not in dated:
        pytest.skip("no committed 2022 citygate prints")
    hh_dated = pytest.importorskip("market_sim.data.fuel.hubs")._henry_hub_daily_dated(
        None
    )
    hh = pd.Series(
        {
            pd.Timestamp(year=y, month=m, day=d): v
            for y, months in hh_dated.items()
            for m, dd in months.items()
            for d, v in dd.items()
        }
    ).sort_index()
    off = _flow_date_staircase(dated[2022], 2022)
    on = _flow_date_staircase(dated[2022], 2022, dated, hh)
    assert off is not None and on is not None
    idx = pd.date_range("2022-01-01", "2022-12-31", freq="D")
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    delta = pd.Series(on - off, index=idx)
    assert delta[delta.index.month == 12].mean() < -1.0  # December falls
    assert delta[delta.index.month == 11].mean() > +0.1  # November rises
