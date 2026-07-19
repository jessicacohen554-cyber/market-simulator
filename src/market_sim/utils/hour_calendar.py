"""The model's fixed non-leap 8760-hour dispatch calendar, in one place.

Every ISO-year the model solves runs on a **fixed non-leap clock**: 8760 hours
(``HOURS_PER_YEAR``), the twelve months always at their common-year lengths
(``DAYS_IN_MONTH_NOLEAP``), Feb 29 dropped in leap years. Hour ``k`` is the
k-th chronological hour after local **standard**-time midnight on Jan 1 — a
fixed-offset (UTC-N, no daylight-saving) clock. This is the same calendar
``data.eia_loader._eia_hourly_frame`` builds (rows sorted by UTC from local
standard midnight), so every hourly series — demand, generation, fuel prices,
LMP actuals — must be laid on it the same way for the hour slots to line up.

Why a *standard*-time (chronological) clock and not the prevailing (DST) wall
clock the source reports label their hours with: pairing a model hour against
an actual on the prevailing clock shifts every hour mid-March→early-November by
one slot, which shows up as a spurious ~+1h evening-band residual in scoring.
That was diagnosed as an all-ISO scoring artifact and fixed by re-laying the
actuals on this chronological calendar; see
``docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md`` and
the ``2026-07-14`` / ``2026-07-15`` calibration-log entries (ALL-ISO
scoring-clock fix). The audit counted this calendar re-implemented across ~44
files; this module is the single home the duplications collapse onto.

Two hour-of-year forms are offered because two conventions coexist in the tree:

* :func:`hour_of_year` takes ``(month, day, hour)`` arrays; a leap year's
  Feb 29 maps to ``-1`` for the caller to drop.
* :func:`hour_index` takes a timestamp Series and is the same map, Feb 29 -> -1.
* :func:`std_hour_index` first converts tz-aware instants to a fixed
  standard-time zone, then maps them (used when the source carries real UTC
  instants rather than pre-localised wall-clock stamps).

``HOURS_PER_YEAR`` is imported from :mod:`market_sim.config.constants` — the one
canonical definition — and re-exported here for convenience.
"""

from __future__ import annotations

import calendar

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR

__all__ = [
    "HOURS_PER_YEAR",
    "DAYS_IN_MONTH_NOLEAP",
    "MONTH_START_HOUR",
    "hour_of_year",
    "month_of_hour",
    "hour_index",
    "std_hour_index",
    "to_model_hour",
    "by_month",
]

# Common-year month lengths (days). Feb has 28: the model's clock drops Feb 29,
# so these boundaries align in every year, leap or not.
DAYS_IN_MONTH_NOLEAP: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

# Cumulative hours before the first of each 1-based month (``[0]`` = Jan 1 hour
# 0, ``[1]`` = 744 = Feb 1, ... ``[11]`` = 8016 = Dec 1). Twelve entries.
MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum(DAYS_IN_MONTH_NOLEAP[:m]) * 24) for m in range(12)
)

# Thirteen month boundaries [0, 744, ..., 8760] for a searchsorted month lookup
# (the trailing 8760 closes December). Private: callers use :func:`month_of_hour`.
_MONTH_START_HOUR_BOUNDS: np.ndarray = np.cumsum(
    [0] + [d * 24 for d in DAYS_IN_MONTH_NOLEAP]
)


def hour_of_year(month, day, hour) -> np.ndarray:
    """Map ``(month, day, hour)`` to a non-leap hour-of-year index.

    Returns an int array in ``[0, 8760)``; Feb 29 maps to ``-1`` so callers can
    drop it, keeping the clock aligned with the model's fixed 8760-hour year.
    Inputs may be scalars or arrays.
    """
    month = np.asarray(month, dtype=int)
    day = np.asarray(day, dtype=int)
    hour = np.asarray(hour, dtype=int)
    base = np.array(MONTH_START_HOUR, dtype=int)[month - 1]
    idx = base + (day - 1) * 24 + hour
    leap_day = (month == 2) & (day == 29)
    idx = np.where(leap_day, -1, idx)
    return idx


def month_of_hour(hours) -> np.ndarray:
    """Map non-leap hour-of-year indices to months ``1-12``.

    ``hours`` may be a scalar or an int array; the result clips to ``[1, 12]``.
    """
    return np.searchsorted(_MONTH_START_HOUR_BOUNDS, hours, side="right").clip(1, 12)


def hour_index(ts: pd.Series) -> np.ndarray:
    """Map tz-naive local timestamps to the fixed non-leap hour-of-year.

    Feb 29 maps to ``-1``. ``ts`` is anything with a ``.dt`` accessor
    (month/day/hour). Callers that pre-drop Feb 29 get the same result as if
    it were never present (the ``-1`` branch simply never fires).
    """
    month = ts.dt.month.to_numpy()
    day = ts.dt.day.to_numpy()
    hour = ts.dt.hour.to_numpy()
    idx = np.array(MONTH_START_HOUR)[month - 1] + (day - 1) * 24 + hour
    return np.where((month == 2) & (day == 29), -1, idx)


def std_hour_index(ts: pd.DatetimeIndex, year: int, std_tz: str) -> np.ndarray:
    """Chronological hour-of-year for tz-aware instants; out-of-scope -> ``-1``.

    Converts real instants to a fixed standard-time zone (``std_tz``, e.g.
    ``"Etc/GMT+6"`` == UTC-6/CST) and maps ``(month, day, hour)`` onto the
    non-leap 8760 calendar — row ``k`` is the k-th UTC hour after local standard
    midnight Jan 1. Rows outside ``year`` (a boundary spill from a
    prevailing-year source file) and the local standard-time Feb 29 map to
    ``-1`` for the caller to drop.
    """
    std = ts.tz_convert(std_tz)
    month = np.asarray(std.month)
    day = np.asarray(std.day)
    idx = (
        np.asarray([MONTH_START_HOUR[m - 1] for m in month])
        + (day - 1) * 24
        + np.asarray(std.hour)
    )
    ok = (np.asarray(std.year) == year) & ~((month == 2) & (day == 29))
    return np.where(ok, idx, -1)


def to_model_hour(dates: pd.Series, hour_end: pd.Series, year: int) -> np.ndarray:
    """Map ``(date, HE 1-24)`` rows onto the fixed non-leap 8760 clock.

    Returns the hour-of-year index per row; a leap year's Feb 29 rows map to
    ``-1`` (dropped), and days after Feb 29 shift back one slot on the non-leap
    clock. ``hour_end`` is 1-based hour-ending (HE 1 == hour index 0).
    """
    ts = pd.to_datetime(dates)
    doy = ts.dt.dayofyear.to_numpy(dtype=int)
    if calendar.isleap(year):
        feb29 = (ts.dt.month == 2) & (ts.dt.day == 29)
        # Days after Feb 29 shift back one slot on the non-leap clock.
        doy = np.where(ts.dt.dayofyear.to_numpy() > 60, doy - 1, doy)
        doy = np.where(feb29.to_numpy(), 0, doy)  # sentinel, dropped below
    idx = (doy - 1) * 24 + (hour_end.to_numpy(dtype=int) - 1)
    if calendar.isleap(year):
        idx = np.where(feb29.to_numpy(), -1, idx)
    return idx


def by_month(values, months) -> list:
    """Twelve monthly means (rounded to 2 dp) from a value series by month label.

    ``months`` is a 1-12 month label per row; empty months come back ``None``.
    """
    out: list = [None] * 12
    g = pd.Series(list(values)).groupby(list(months)).mean()
    for m, v in g.items():
        if pd.notna(m) and 1 <= int(m) <= 12 and pd.notna(v):
            out[int(m) - 1] = round(float(v), 2)
    return out
