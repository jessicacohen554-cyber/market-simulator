"""Trivial-case tests for the fast-start pool derive's wall-clock prep.

Covers ``scripts/data/derive_ercot_faststart_pool._prep_clock_gas`` — the
CPT -> fixed-CST -> non-leap hour-of-year + gas-day join every pool/live frame
passes through (``derive_year`` and ``derive_year_continuous`` both call it).

The regression these pin is the ERCOT-187 leap-day defect (surfaced, and
deliberately left unfixed, at ERCOT-183): the Feb-29 mask is computed on the
PRE-filter frame, so any derived column re-read off the POST-filter frame and
indexed with that mask raises ``IndexError`` the moment the year's basis
actually carries Feb-29 rows. The path is unreachable on a non-leap corpus —
which is every basis the committed artifacts were derived from — so it sat
latent until the ERCOT-183 leap-year (delivery-2024) corpus intake made it
reachable. Both halves are asserted: the leap-year frame must survive AND
stay row-aligned, and the non-leap frame must be unchanged (the no-op that
makes every committed block byte-identical across the fix).

Hermetic: synthetic frames only, no corpus, no ``data/raw`` read.
"""

import numpy as np
import pandas as pd

from scripts.data import derive_ercot_faststart_pool as pool
from scripts.data.derive_ercot_dam_cleared_share import _MONTH_START_HOUR


def _frame(stamps: list[str], status: str = "OFFQS") -> pd.DataFrame:
    """Minimal SCED frame at the columns ``_prep_clock_gas`` touches."""
    return pd.DataFrame(
        {
            "SCED Time Stamp": pd.to_datetime(stamps),
            "Telemetered Resource Status": [status] * len(stamps),
            "HSL": [100.0] * len(stamps),
        }
    )


def _gas_day(start: str, end: str, price: float = 3.0) -> pd.Series:
    """Flat delivered-gas day series over an inclusive date range."""
    idx = pd.DatetimeIndex(pd.date_range(start, end, freq="D"))
    return pd.Series([price] * len(idx), index=idx)


def _hoy(month: int, day: int, hour: int) -> int:
    """The non-leap hour-of-year the derive's own map assigns."""
    return int(_MONTH_START_HOUR[month - 1] + (day - 1) * 24 + hour)


def test_leap_year_frame_drops_feb29_and_stays_row_aligned():
    """A Feb-29-carrying basis prepped without IndexError, columns aligned.

    Feb-29 rows sit in the MIDDLE of the frame, so a prep that merely
    truncated to the surviving row count (rather than masking) would land the
    wrong timestamps on the wrong rows and fail on ``_ts``/``_date``, not just
    on the row count.
    """
    stamps = [
        "02/28/2024 12:00:00",
        "02/29/2024 03:00:00",
        "02/29/2024 21:00:00",
        "03/01/2024 12:00:00",
        "12/31/2024 23:00:00",
    ]
    out = pool._prep_clock_gas(_frame(stamps), _gas_day("2024-01-01", "2024-12-31"))

    survivors = ["2024-02-28 12:00", "2024-03-01 12:00", "2024-12-31 23:00"]
    assert len(out) == 3
    assert list(pd.to_datetime(out["_ts"])) == list(pd.to_datetime(survivors))
    assert list(pd.to_datetime(out["_date"])) == list(
        pd.to_datetime(["2024-02-28", "2024-03-01", "2024-12-31"])
    )
    # Non-leap hour-of-year: Mar-1 of a leap year maps onto the non-leap map,
    # and the last hour stays inside the 8760 the artifact is keyed on.
    assert list(out["hoy"]) == [_hoy(2, 28, 12), _hoy(3, 1, 12), _hoy(12, 31, 23)]
    assert out["hoy"].max() < pool.HOURS
    assert set(out["stat"]) == {"OFFQS"}
    assert (out["gas_day"] > 0).all()


def test_non_leap_year_frame_is_untouched_by_the_feb29_mask():
    """No Feb-29 row => every row survives with its own clock values.

    This is the no-op guarantee behind the ERCOT-187 fix being artifact-inert:
    on a basis with zero Feb-29 rows the mask is all-True, so the fixed and
    pre-fix expressions are the same array.
    """
    stamps = ["02/28/2023 12:00:00", "03/01/2023 12:00:00", "07/04/2023 17:00:00"]
    out = pool._prep_clock_gas(_frame(stamps), _gas_day("2023-01-01", "2023-12-31"))

    assert len(out) == 3
    assert list(pd.to_datetime(out["_ts"])) == list(pd.to_datetime(stamps))
    # ``hoy`` is on the FIXED standard-time clock, so the July stamp (posted in
    # CDT) lands an hour earlier than its wall-clock hour; the winter stamps do
    # not move. ``_ts`` keeps the posted CPT stamp either way.
    assert list(out["hoy"]) == [_hoy(2, 28, 12), _hoy(3, 1, 12), _hoy(7, 4, 16)]


def test_gasless_days_are_dropped_after_the_leap_filter():
    """Rows whose gas day is missing/zero leave, independently of Feb-29."""
    stamps = ["02/29/2024 12:00:00", "03/01/2024 12:00:00", "03/02/2024 12:00:00"]
    gas = _gas_day("2024-03-01", "2024-03-01")  # only Mar-1 has a gas day
    out = pool._prep_clock_gas(_frame(stamps), gas)

    assert len(out) == 1
    assert pd.to_datetime(out["_ts"].iloc[0]) == pd.Timestamp("2024-03-01 12:00")
    assert np.isclose(out["gas_day"].iloc[0], 3.0)
