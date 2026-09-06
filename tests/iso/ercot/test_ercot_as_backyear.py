"""Unit tests for ``scripts/data/build_ercot_as_backyear.py`` (synthetic frames).

The back-year load-resource RRS builder reads the 60-Day DAM Load Resource
Data awards; these tests exercise its pure functions on tiny synthetic
inputs so they need none of the raw parquets: the RRS-split continuity
(``RRS Awarded`` before 2022-10-15, the three components after), the
CPT->CST clock placement, and the uncovered-window reconstruction rule.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd
from tests.helpers import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.data import build_ercot_as_backyear as backyear  # noqa: E402


def _hourly(date: str, **cols: float) -> pd.DataFrame:
    """One delivery day of ``(date, he)``-indexed award sums."""
    idx = pd.MultiIndex.from_arrays(
        [[pd.Timestamp(date)] * 24, list(range(1, 25))], names=["date", "Hour Ending"]
    )
    frame = pd.DataFrame(index=idx)
    for name in backyear._RRS_COLS:
        frame[name] = cols.get(name, 0.0)
    return frame


def test_split_day_rrs_total_is_continuous():
    """Pre-split ``RRS Awarded`` and post-split components sum to one series."""
    pre = _hourly("2022-10-14", **{"RRS Awarded": 1000.0})
    post = _hourly(
        "2022-10-15",
        **{"RRSPFR Awarded": 40.0, "RRSFFR Awarded": 0.0, "RRSUFR Awarded": 960.0},
    )
    both = pd.concat([pre, post])
    both["lr_rrs"] = both[list(backyear._RRS_COLS)].sum(axis=1)
    arr = backyear.to_clock_keep_gaps(backyear.awards_to_rows(both, "lr_rrs"), 2022)
    covered = arr[~np.isnan(arr)]
    assert len(covered) == 48
    assert np.allclose(covered, 1000.0)


def test_clock_placement_summer_is_one_hour_earlier_than_naive():
    """June HE 1 (CDT) lands on CST 23:00 of the previous day."""
    day = _hourly("2022-06-10", **{"RRS Awarded": 500.0})
    day["lr_rrs"] = day[list(backyear._RRS_COLS)].sum(axis=1)
    arr = backyear.to_clock_keep_gaps(backyear.awards_to_rows(day, "lr_rrs"), 2022)
    # Jan..May = 151 days; Jun 9 is day index 159; 159*24 + 23 = 3839.
    assert arr[3839] == 500.0
    assert np.isnan(arr[3838])
    assert arr[3862] == 500.0 and np.isnan(arr[3863])


def test_build_rrsufr_measured_hours_pass_through_and_gap_reconstructed():
    """Covered hours are returned verbatim; uncovered hours = plan - gen - offset."""
    T = backyear.HOURS_PER_YEAR
    lr = np.full(T, 900.0)
    lr[7000:] = np.nan  # uncovered tail
    gen = np.full(T, 1000.0)
    plan = np.full(T, 2650.0)  # plan - gen = 1650 -> offset = 750 on covered hours
    plan[7000:] = 2800.0  # tail residual 1800 -> reconstructed 1050
    out, meta = backyear.build_rrsufr(lr, gen, plan, 2022)
    assert np.allclose(out[:7000], 900.0)
    assert np.allclose(out[7000:], 1050.0)
    assert meta["rrsufr_covered_hours"] == "7000"
    assert meta["rrsufr_reconstructed_hours"] == str(T - 7000)
    assert "offset" in meta["rrsufr_reconstruction"]
    assert "= 750.0 MW" in meta["rrsufr_reconstruction"]


def test_build_rrsufr_no_plan_zero_fills_gap_and_says_so():
    """Without an ASPLAN file the uncovered hours are zero, never fabricated."""
    T = backyear.HOURS_PER_YEAR
    lr = np.full(T, 600.0)
    lr[:100] = np.nan
    out, meta = backyear.build_rrsufr(lr, np.full(T, 1000.0), None, 2020)
    assert np.all(out[:100] == 0.0) and np.allclose(out[100:], 600.0)
    assert meta["rrsufr_reconstructed_hours"] == "100"
    assert meta["rrsufr_reconstruction"].startswith("ZERO-FILLED")


def test_build_rrsufr_full_coverage_is_identity():
    """A fully covered year is returned unchanged with no reconstruction."""
    T = backyear.HOURS_PER_YEAR
    lr = np.linspace(400.0, 1200.0, T)
    out, meta = backyear.build_rrsufr(lr, np.zeros(T), None, 2021)
    assert np.array_equal(out, lr)
    assert meta["rrsufr_reconstructed_hours"] == "0"
    assert "rrsufr_reconstruction" not in meta
