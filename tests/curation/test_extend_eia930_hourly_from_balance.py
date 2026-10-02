"""Tests for ``scripts/data/extend_eia930_hourly_from_balance.py`` (the extend path).

Pins the I-SOCO (2026-09-24) repair: a fuel column the BALANCE taxonomy lacks
arrives all-NA, and the extend must cast it to the extract's own dtype so the
already-committed rows stay byte-identical (the concat used to upcast those
columns float32 -> float64 across the whole file).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from scripts.data import extend_eia930_hourly_from_balance as ext

_BA = "TEST"


def _existing_extract() -> pd.DataFrame:
    """Two committed hours of a wide extract carrying a new-taxonomy-only column."""
    utc = pd.to_datetime(["2023-01-01 06:00", "2023-01-01 07:00"]).astype(
        "datetime64[us]"
    )
    frame = pd.DataFrame(
        {
            "UTC time": utc,
            "Local date": pd.to_datetime(["2023-01-01"] * 2).astype("datetime64[us]"),
            "Hour": np.array([1, 2], dtype="int64"),
            "Local time": (utc - pd.Timedelta(hours=6)).astype("datetime64[us]"),
            "Demand": np.array([100.0, 110.0], dtype="float32"),
            "NG: COL": np.array([10.0, 11.0], dtype="float32"),
            "NG: BAT": np.array([np.nan, 1.0], dtype="float32"),
        }
    )
    return frame


def _new_rows(fuel_cols, years, halves, ba=_BA, target=None):
    """Stand-in ``build_new_rows``: one earlier hour, ``NG: BAT`` all-``pd.NA``."""
    utc = pd.to_datetime(["2022-12-31 06:00"]).astype("datetime64[us]")
    return pd.DataFrame(
        {
            "UTC time": utc,
            "Local date": pd.to_datetime(["2022-12-31"]).astype("datetime64[us]"),
            "Hour": np.array([1], dtype="int64"),
            "Local time": (utc - pd.Timedelta(hours=6)).astype("datetime64[us]"),
            "Demand": np.array([90.0], dtype="float32"),
            "NG: COL": np.array([9.0], dtype="float32"),
            "NG: BAT": pd.Series([pd.NA], dtype=object),
        }
    )


@pytest.fixture
def extract_dir(tmp_path, monkeypatch):
    """Point the module's output dir at a temp extract and stub the BALANCE read."""
    _existing_extract().to_parquet(tmp_path / f"{_BA} hourly.parquet", index=False)
    monkeypatch.setattr(ext, "OUT_DIR", tmp_path)
    monkeypatch.setattr(
        ext,
        "build_new_rows",
        lambda ba, fuel_cols, years, halves: _new_rows(fuel_cols, years, halves),
    )
    return tmp_path


def test_extend_keeps_committed_rows_and_schema_byte_identical(extract_dir):
    """The committed rows and every column dtype survive a prepend unchanged."""
    before = _existing_extract()
    ext.extend_ba(_BA, False, (2022,), ("Jul_Dec",))
    after = pd.read_parquet(extract_dir / f"{_BA} hourly.parquet")
    assert dict(after.dtypes) == dict(before.dtypes)
    assert len(after) == 3
    kept = after[after["UTC time"].isin(before["UTC time"])].reset_index(drop=True)
    assert_frame_equal(kept, before, check_exact=True)
    assert after["NG: BAT"].iloc[0] != after["NG: BAT"].iloc[0]  # NaN, not 0


def _balance_rows(ba: str, utc: list[str], demand: list[float]) -> pd.DataFrame:
    """Legacy-taxonomy BALANCE rows for one FLA member BA."""
    n = len(utc)
    frame = pd.DataFrame(
        {
            "Balancing Authority": [ba] * n,
            "Region": ["FLA"] * n,
            "UTC Time at End of Hour": utc,
            "Demand Forecast (MW)": demand,
            "Demand (MW)": [d * 1000 for d in demand],  # raw spike, never read
            "Demand (MW) (Adjusted)": demand,
            "Net Generation (MW) (Adjusted)": demand,
            "Total Interchange (MW) (Adjusted)": [0.0] * n,
        }
    )
    for col in (*ext._LEGACY_FUEL_MAP, *ext._LEGACY_OTHER_COLS):
        frame[col] = np.nan
    frame["Net Generation (MW) from Natural Gas"] = demand
    return frame


def test_region_rows_sum_members_per_hour(tmp_path, monkeypatch):
    """A region hour is the Adjusted sum of the BAs filing that hour.

    A BA absent from an hour (NSB after folding into FMPP) is not a member
    there; a member filing NaN makes the demand family NaN (a partial sum is
    not the region) while fuel sums stay ``min_count=1``.
    """
    hours = ["2020-01-01 06:00", "2020-01-01 07:00", "2020-01-01 08:00"]
    balance = pd.concat(
        [
            _balance_rows("AAA", hours, [100.0, 100.0, 100.0]),
            _balance_rows("BBB", hours, [10.0, np.nan, 10.0]),
            _balance_rows("NSB", hours[:1], [1.0]),
        ],
        ignore_index=True,
    )
    balance.to_parquet(tmp_path / "EIA930_BALANCE_2020_Jan_Jun.parquet")
    monkeypatch.setattr(ext, "BALANCE_DIR", tmp_path)

    out = ext.build_region_rows("FLA", ["NG: NG", "NG: COL"], (2020,), ("Jan_Jun",))

    assert out["Demand"].tolist()[0] == 111.0
    assert np.isnan(out["Demand"].iloc[1])
    assert out["Demand"].iloc[2] == 110.0
    assert out["NG: NG"].tolist() == [111.0, 100.0, 110.0]
    assert out["NG: COL"].isna().all()  # no member reports it: NaN, not 0
    assert out["Local time"].iloc[0] == pd.Timestamp("2020-01-01 01:00")  # US/Eastern
    assert out["Local date"].iloc[0] == pd.Timestamp("2020-01-01")
