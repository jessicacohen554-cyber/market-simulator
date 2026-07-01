"""Tests for load intake, aggregation, growth, and LMP intake/reconciliation."""

import numpy as np
import pandas as pd
import pytest

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.intake import (
    aggregate_by_hour_iso,
    apply_load_growth,
    collapse_zonal_lmp,
    prepare_lmp,
    prepare_load,
)


def _long_df() -> pd.DataFrame:
    """Two facilities in one ISO plus a second ISO, a few hours each."""
    rows = []
    for h in range(HOURS_PER_YEAR):
        rows.append({"hour": h, "iso": "A", "facility": "f1", "load_mwh": 10.0})
        rows.append({"hour": h, "iso": "A", "facility": "f2", "load_mwh": 5.0})
        rows.append({"hour": h, "iso": "B", "facility": "g1", "load_mwh": 7.0})
    return pd.DataFrame(rows)


def test_aggregate_sums_facilities_per_iso() -> None:
    """Facilities within an (iso, hour) are summed; ISOs kept separate."""
    agg = aggregate_by_hour_iso(_long_df())
    assert set(agg) == {"A", "B"}
    assert agg["A"].shape == (HOURS_PER_YEAR,)
    assert np.allclose(agg["A"], 15.0)  # 10 + 5
    assert np.allclose(agg["B"], 7.0)


def test_growth_compounds() -> None:
    """Growth applies a compound multiplier, shape-preserving."""
    load = np.ones(HOURS_PER_YEAR)
    grown = apply_load_growth(load, 0.02, 5)
    assert np.allclose(grown, 1.02**5)


def test_growth_rate_must_exceed_negative_one() -> None:
    """A rate <= -1 (load vanishing or reversing sign) is rejected."""
    load = np.ones(HOURS_PER_YEAR)
    with pytest.raises(ValueError, match="load_growth_rate"):
        apply_load_growth(load, -1.0, 1)


def test_prepare_load_end_to_end(tmp_path) -> None:
    """prepare_load reads, aggregates, and grows for one ISO."""
    path = tmp_path / "load.csv"
    _long_df().to_csv(path, index=False)
    cfg = PortfolioConfig(iso="A", load_growth_rate=0.1, load_growth_years=1)
    load = prepare_load(path, "A", cfg)
    assert load.shape == (HOURS_PER_YEAR,)
    assert np.allclose(load, 15.0 * 1.1)


def test_missing_hours_error_names_iso_and_count() -> None:
    """Dropping trailing hours for one ISO raises, naming the ISO and the count."""
    df = _long_df()
    df = df[~((df["iso"] == "A") & (df["hour"] >= HOURS_PER_YEAR - 3))]
    with pytest.raises(ValueError) as exc_info:
        aggregate_by_hour_iso(df)
    message = str(exc_info.value)
    assert "'A'" in message
    assert "3" in message
    assert str(HOURS_PER_YEAR - 3) in message  # first missing hour named as example


def test_duplicate_facility_hour_rows_error() -> None:
    """A repeated (facility, hour) row within an ISO is a data error, not a sum."""
    df = _long_df()
    dup_row = df[(df["iso"] == "A") & (df["facility"] == "f1") & (df["hour"] == 0)]
    df = pd.concat([df, dup_row], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate"):
        aggregate_by_hour_iso(df)


def _lmp_df() -> pd.DataFrame:
    """One ISO, 8760 hours, a simple deterministic LMP series."""
    hours = np.arange(HOURS_PER_YEAR)
    return pd.DataFrame({"hour": hours, "iso": "A", "lmp": 20.0 + 0.001 * hours})


def test_lmp_round_trip_csv(tmp_path) -> None:
    """A written-then-read CSV LMP file returns the exact series for the ISO."""
    df = _lmp_df()
    path = tmp_path / "lmp.csv"
    df.to_csv(path, index=False)
    lmp = prepare_lmp(path, "A")
    assert lmp.shape == (HOURS_PER_YEAR,)
    assert np.allclose(lmp, df.sort_values("hour")["lmp"].to_numpy())


def test_lmp_round_trip_parquet(tmp_path) -> None:
    """A written-then-read Parquet LMP file returns the exact series for the ISO."""
    df = _lmp_df()
    path = tmp_path / "lmp.parquet"
    df.to_parquet(path, index=False)
    lmp = prepare_lmp(path, "A")
    assert lmp.shape == (HOURS_PER_YEAR,)
    assert np.allclose(lmp, df.sort_values("hour")["lmp"].to_numpy())


def test_lmp_wrong_length_errors(tmp_path) -> None:
    """An LMP file missing hours for the requested ISO raises."""
    df = _lmp_df().iloc[:-10]  # drop the last 10 hours
    path = tmp_path / "lmp.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing"):
        prepare_lmp(path, "A")


def test_lmp_duplicate_hour_errors(tmp_path) -> None:
    """A duplicated (iso, hour) row in the LMP file raises."""
    df = pd.concat([_lmp_df(), _lmp_df().iloc[[0]]], ignore_index=True)
    path = tmp_path / "lmp.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        prepare_lmp(path, "A")


def test_collapse_zonal_lmp_load_weighted_with_zero_load_hour() -> None:
    """Load-weighted average across 2 zones; a zero-load hour falls back to the mean."""
    zonal_lmp = pd.DataFrame(
        {
            "hour": [0, 0, 1, 1],
            "iso": ["A", "A", "A", "A"],
            "zone": ["z1", "z2", "z1", "z2"],
            "lmp": [10.0, 50.0, 20.0, 40.0],
        }
    )
    zonal_load = pd.DataFrame(
        {
            "hour": [0, 0, 1, 1],
            "iso": ["A", "A", "A", "A"],
            "zone": ["z1", "z2", "z1", "z2"],
            "load_mwh": [100.0, 300.0, 0.0, 0.0],
        }
    )
    collapsed = collapse_zonal_lmp(zonal_lmp, zonal_load)
    collapsed = collapsed.set_index("hour")
    # hour 0: (100*10 + 300*50) / 400 = 40.0
    assert collapsed.loc[0, "lmp"] == pytest.approx(40.0)
    # hour 1: zero total load -> simple mean of 20 and 40
    assert collapsed.loc[1, "lmp"] == pytest.approx(30.0)
