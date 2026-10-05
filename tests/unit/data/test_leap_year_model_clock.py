"""Leap-year alignment of the model's fixed non-leap 8760-hour clock.

Every hourly input (demand via ``eia930.frames._eia_hourly_frame``, CAMPD,
reserve requirements, ...) is laid on a clock that DROPS a leap year's Feb 29,
so model hour 1416 is Mar 1 00:00 in every year. ``_hour_to_month_index`` (a
365-day table) is therefore correct; the leap-year bug class is the opposite
one — reading a calendar field off ``pd.date_range(f"{year}-01-01",
periods=hours)``, which keeps Feb 29 and labels every hour from Mar 1 on one
day early. ``hour_calendar.model_clock`` is the one correct inverse.
"""

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data.fleet import _hour_to_month_index
from market_sim.utils.hour_calendar import hour_index, model_clock, month_of_hour


def test_model_clock_2020_02_28_last_hour_precedes_mar_1() -> None:
    clock = model_clock(2020, 24 * 60)
    assert clock[58 * 24 + 23] == pd.Timestamp("2020-02-28 23:00")
    assert clock[59 * 24] == pd.Timestamp("2020-03-01 00:00")


def test_model_clock_never_contains_feb_29() -> None:
    clock = model_clock(2020)
    assert not ((clock.month == 2) & (clock.day == 29)).any()


def test_model_clock_2020_03_01_is_hour_1416() -> None:
    assert model_clock(2020)[1416] == pd.Timestamp("2020-03-01 00:00")
    assert _hour_to_month_index(1417)[1416] == 2  # March, 0-based


@pytest.mark.parametrize("year", [2020, 2024])
def test_model_clock_leap_year_ends_on_dec_31(year: int) -> None:
    clock = model_clock(year)
    assert len(clock) == HOURS_PER_YEAR
    assert clock[-1] == pd.Timestamp(f"{year}-12-31 23:00")
    assert _hour_to_month_index(HOURS_PER_YEAR)[-1] == 11


@pytest.mark.parametrize("year", [2019, 2023, 2025])
def test_model_clock_common_year_equals_date_range(year: int) -> None:
    ref = pd.date_range(f"{year}-01-01", periods=HOURS_PER_YEAR, freq="h")
    assert model_clock(year).equals(ref)


@pytest.mark.parametrize("year", [2019, 2020, 2023, 2024])
def test_model_clock_month_matches_hour_to_month_index(year: int) -> None:
    months = model_clock(year).month.to_numpy() - 1
    np.testing.assert_array_equal(months, _hour_to_month_index(HOURS_PER_YEAR))
    np.testing.assert_array_equal(months + 1, month_of_hour(np.arange(HOURS_PER_YEAR)))


@pytest.mark.parametrize("year", [2020, 2024])
def test_model_clock_round_trips_through_hour_index(year: int) -> None:
    clock = model_clock(year)
    np.testing.assert_array_equal(
        hour_index(pd.Series(clock)), np.arange(HOURS_PER_YEAR)
    )


def test_model_clock_weekday_2024_mar_1_is_friday() -> None:
    # pd.date_range(2024, periods=8760) would label this slot Thu Feb 29.
    assert model_clock(2024)[1416].dayofweek == 4


def test_no_leap_naive_date_range_clock_in_src() -> None:
    """``pd.date_range(f"{year}-01-01", periods=...)`` keeps Feb 29; use model_clock."""
    from pathlib import Path
    import re

    root = Path(__file__).resolve().parents[3]
    pat = re.compile(r'date_range\(\s*f"\{\w+\}-01-01",\s*periods=')
    offenders = []
    for path in [
        *(root / "src").rglob("*.py"),
        root / "scripts/run_calibration_full.py",
    ]:
        for i, line in enumerate(path.read_text().splitlines(), 1):
            if pat.search(line):
                nxt = path.read_text().splitlines()[i : i + 1]
                if not any("day == 29" in n for n in nxt):
                    offenders.append(f"{path.relative_to(root)}:{i}")
    assert offenders == []
