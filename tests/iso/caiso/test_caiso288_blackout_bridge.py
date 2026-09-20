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

caiso-289 (2026-09-20) added three more, after caiso-288 recovered the 85
published prints the fetcher had been discarding
(``docs/FINDING-caiso289-the-bridge-flag-carries-two-mechanisms-2026-09-20.md``):

  5. The Dec-2022 blackout that MOTIVATED the mechanism is measured now, so the
     bridge cannot touch it. This REPLACES the old
     ``test_bridge_moves_december_2022_down_and_november_2022_up``, which
     asserted a footprint the armed flag no longer has and failed on main.
  6. Over the repaired series the bridge is INERT in 2022 and 2023 and reaches
     only the two G-DUP-refused Thanksgiving weeks in 2024/2025.
  7. The flag carries a SECOND, undeclared channel — the year-start left-edge
     convention — which is its entire effect in 2022/2023. Pinned so it cannot
     be mistaken for a bridge regression and silently "fixed".
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


def _committed_hh() -> pd.Series:
    hh_dated = pytest.importorskip("market_sim.data.fuel.hubs")._henry_hub_daily_dated(
        None
    )
    return pd.Series(
        {
            pd.Timestamp(year=y, month=m, day=d): v
            for y, months in hh_dated.items()
            for m, dd in months.items()
            for d, v in dd.items()
        }
    ).sort_index()


def _blackout_interior_days(dated: dict) -> set[pd.Timestamp]:
    """Flow days strictly inside a >= threshold gap — the bridge's real reach."""
    flow = pd.Series(
        {
            pd.Timestamp(year=y, month=m, day=d) + pd.Timedelta(days=1): v
            for y, months in sorted(dated.items())
            for m, dd in sorted(months.items())
            for d, v in sorted(dd.items())
        }
    ).sort_index()
    out: set[pd.Timestamp] = set()
    for a, b in zip(flow.index, flow.index[1:]):
        if (b - a).days >= _GAS_BLACKOUT_MIN_GAP_DAYS:
            out.update(
                pd.date_range(a + pd.Timedelta(days=1), b - pd.Timedelta(days=1))
            )
    return out


def test_december_2022_is_measured_not_bridged() -> None:
    """caiso-289: the Dec-2022 blackout that MOTIVATED this mechanism no longer
    exists — caiso-288 recovered its prints, so the bridge cannot touch it.

    This test replaces ``test_bridge_moves_december_2022_down_and_november_2022
    _up``, which asserted a December fall of >$1/MMBtu and a November rise. Both
    were measured on the UNREPAIRED series and both are now 0.0 by construction:
    the days are measurements. Restoring that assertion would be re-pinning the
    bridge to a footprint it does not have (see
    docs/FINDING-caiso289-the-bridge-flag-carries-two-mechanisms-2026-09-20.md).
    """
    dated = _caiso_citygate_daily_dated(None)
    if 2022 not in dated:
        pytest.skip("no committed 2022 citygate prints")
    off = _flow_date_staircase(dated[2022], 2022)
    on = _flow_date_staircase(dated[2022], 2022, dated, _committed_hh())
    assert off is not None and on is not None
    idx = pd.date_range("2022-01-01", "2022-12-31", freq="D")
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    delta = pd.Series(on - off, index=idx)
    # The prints EIA published across 2022-12-21 -> 2023-01-05 are committed, so
    # November and December 2022 carry no blackout interior at all.
    assert (delta[delta.index.month == 12] == 0.0).all()
    assert (delta[delta.index.month == 11] == 0.0).all()


def test_the_flag_also_switches_the_year_start_left_edge() -> None:
    """caiso-289: arming the bridge changes a SECOND thing that is not the
    bridge — the year-start left-edge convention — and in 2022/2023 that second
    channel is its ENTIRE effect.

    Unbridged, flow days before a year's first print ``.bfill()`` from that
    year's first JANUARY trade; bridged, they ``.ffill()`` from the previous
    DECEMBER's last trade, because the reindex spans all years. This test pins
    the confound so it cannot be silently "fixed" as a bridge regression: the
    days that move in 2022 and 2023 are OUTSIDE every blackout interior.
    """
    dated = _caiso_citygate_daily_dated(None)
    hh = _committed_hh()
    interior = _blackout_interior_days(dated)
    for year in (2022, 2023):
        if year not in dated:
            pytest.skip(f"no committed {year} citygate prints")
        off = _flow_date_staircase(dated[year], year)
        on = _flow_date_staircase(dated[year], year, dated, hh)
        assert off is not None and on is not None
        idx = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        idx = idx[~((idx.month == 2) & (idx.day == 29))]
        moved = idx[~np.isclose(on - off, 0.0, atol=1e-12)]
        assert len(moved), f"{year} should move at the left edge"
        # Not one of them is a blackout interior day: this is not the bridge.
        assert not (set(moved) & interior)
        # And they are all at the very start of the year.
        assert (moved.month == 1).all() and (moved.day <= 5).all()


def test_bridge_is_inert_in_2022_and_2023_over_the_repaired_series() -> None:
    """caiso-289 G-FOOT289: the mechanism's own reach in the scored years.

    Post-repair the bridge touches ZERO days in 2022 and 2023, and only the two
    G-DUP-refused Thanksgiving weeks in 2024/2025. Anything else means the
    committed citygate series moved and the audit must be re-run.
    """
    dated = _caiso_citygate_daily_dated(None)
    hh = _committed_hh()
    interior = _blackout_interior_days(dated)
    expected = {2022: 0, 2023: 0, 2024: 11, 2025: 11}
    for year, n_expected in expected.items():
        if year not in dated:
            pytest.skip(f"no committed {year} citygate prints")
        off = _flow_date_staircase(dated[year], year)
        on = _flow_date_staircase(dated[year], year, dated, hh)
        assert off is not None and on is not None
        idx = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
        idx = idx[~((idx.month == 2) & (idx.day == 29))]
        moved = idx[~np.isclose(on - off, 0.0, atol=1e-12)]
        assert len(set(moved) & interior) == n_expected, (
            f"{year}: bridge-interior days moved != {n_expected}"
        )
