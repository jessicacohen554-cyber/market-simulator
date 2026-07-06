"""Tests for load intake, aggregation, growth, and LMP intake/reconciliation."""

import numpy as np
import pandas as pd
import pytest

from lce_portfolio.config import (
    HOURS_PER_YEAR,
    LMP_KIND_ANNUAL_AVERAGE_FLAT,
    LMP_KIND_HOURLY,
    PortfolioConfig,
)
from lce_portfolio.intake import (
    aggregate_by_hour_iso,
    apply_load_growth,
    collapse_zonal_lmp,
    lmp_intake,
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
    lmp, lmp_kind = prepare_lmp(path, "A")
    assert lmp.shape == (HOURS_PER_YEAR,)
    assert np.allclose(lmp, df.sort_values("hour")["lmp"].to_numpy())
    assert lmp_kind == LMP_KIND_HOURLY


def test_lmp_round_trip_parquet(tmp_path) -> None:
    """A written-then-read Parquet LMP file returns the exact series for the ISO."""
    df = _lmp_df()
    path = tmp_path / "lmp.parquet"
    df.to_parquet(path, index=False)
    lmp, lmp_kind = prepare_lmp(path, "A")
    assert lmp.shape == (HOURS_PER_YEAR,)
    assert np.allclose(lmp, df.sort_values("hour")["lmp"].to_numpy())
    assert lmp_kind == LMP_KIND_HOURLY


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


# --- intake validation hardening (audit findings IO-2/IO-3/IO-5/IO-6) --------


def _full_lmp_df(**overrides) -> pd.DataFrame:
    """One ISO, full 8760 calendar, constant price unless overridden."""
    df = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR),
            "iso": "A",
            "lmp": np.full(HOURS_PER_YEAR, 30.0),
        }
    )
    for col, val in overrides.items():
        df.loc[0, col] = val
    return df


def test_nan_lmp_rejected(tmp_path) -> None:
    """A NaN price must not flow into the LP objective (IO-2)."""
    path = tmp_path / "lmp.csv"
    _full_lmp_df(lmp=np.nan).to_csv(path, index=False)
    with pytest.raises(ValueError, match="non-finite lmp"):
        prepare_lmp(path, "A")


# --- annual-average LMP intake (HP-01, data/templates/README.md §2b) --------


def _annual_avg_lmp_df(**overrides) -> pd.DataFrame:
    """Two ISOs, one annual-average row each, unless overridden."""
    df = pd.DataFrame({"iso": ["A", "B"], "annual_avg_lmp": [30.0, 45.0]})
    for col, val in overrides.items():
        df.loc[0, col] = val
    return df


def test_lmp_intake_detects_hourly_schema(tmp_path) -> None:
    """A (hour, iso, lmp) file is detected as the hourly schema."""
    path = tmp_path / "lmp.csv"
    _lmp_df().to_csv(path, index=False)
    df, lmp_kind = lmp_intake(path)
    assert lmp_kind == LMP_KIND_HOURLY
    assert "hour" in df.columns


def test_lmp_intake_detects_annual_average_schema(tmp_path) -> None:
    """An (iso, annual_avg_lmp) file with no hour column is detected as
    annual-average (HP-01)."""
    path = tmp_path / "lmp.csv"
    _annual_avg_lmp_df().to_csv(path, index=False)
    df, lmp_kind = lmp_intake(path)
    assert lmp_kind == LMP_KIND_ANNUAL_AVERAGE_FLAT
    assert "hour" not in df.columns


def test_prepare_lmp_expands_annual_average_to_flat_8760(tmp_path) -> None:
    """Every hour of the expanded vector equals the file's annual average."""
    path = tmp_path / "lmp.csv"
    _annual_avg_lmp_df().to_csv(path, index=False)
    lmp, lmp_kind = prepare_lmp(path, "A")
    assert lmp_kind == LMP_KIND_ANNUAL_AVERAGE_FLAT
    assert lmp.shape == (HOURS_PER_YEAR,)
    assert np.all(lmp == 30.0)

    lmp_b, _ = prepare_lmp(path, "B")
    assert np.all(lmp_b == 45.0)


def test_annual_average_lmp_duplicate_iso_errors(tmp_path) -> None:
    """A repeated iso row in the annual-average file is a hard error naming
    an example (mirrors the hourly path's duplicate-row idiom)."""
    df = pd.concat([_annual_avg_lmp_df(), _annual_avg_lmp_df().iloc[[0]]])
    path = tmp_path / "lmp.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="duplicate"):
        prepare_lmp(path, "A")


def test_annual_average_lmp_rejects_non_finite(tmp_path) -> None:
    """A NaN annual-average value is a hard error, not a silent pass-through."""
    path = tmp_path / "lmp.csv"
    _annual_avg_lmp_df(annual_avg_lmp=np.nan).to_csv(path, index=False)
    with pytest.raises(ValueError, match="non-finite annual_avg_lmp"):
        prepare_lmp(path, "A")


def test_annual_average_lmp_rejects_negative(tmp_path) -> None:
    """A negative annual-average value is a hard error."""
    path = tmp_path / "lmp.csv"
    _annual_avg_lmp_df(annual_avg_lmp=-5.0).to_csv(path, index=False)
    with pytest.raises(ValueError, match="negative annual_avg_lmp"):
        prepare_lmp(path, "A")


def test_annual_average_lmp_missing_iso_matches_hourly_error_shape(tmp_path) -> None:
    """A requested ISO absent from an annual-average file raises the same
    KeyError shape as the hourly path."""
    path = tmp_path / "lmp.csv"
    _annual_avg_lmp_df().to_csv(path, index=False)
    with pytest.raises(KeyError, match="not present in LMP file"):
        prepare_lmp(path, "C")


def test_lmp_intake_bad_schema_keeps_missing_columns_error(tmp_path) -> None:
    """A file matching neither schema keeps the clear missing-columns error."""
    path = tmp_path / "lmp.csv"
    pd.DataFrame({"iso": ["A"], "price": [10.0]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="missing columns"):
        lmp_intake(path)


def test_nan_emission_rate_rejected(tmp_path) -> None:
    """NaN passes a `< 0` sign check, so finiteness is checked first (IO-2)."""
    from lce_portfolio.intake import prepare_emission_rate

    df = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR),
            "iso": "A",
            "fossil_avg_co2_rate": np.full(HOURS_PER_YEAR, 0.4),
        }
    )
    df.loc[10, "fossil_avg_co2_rate"] = np.nan
    path = tmp_path / "rates.csv"
    df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="non-finite fossil_avg_co2_rate"):
        prepare_emission_rate(path, "A")


def test_nan_and_negative_load_rejected(tmp_path) -> None:
    """A NaN load hour was silently summed to 0 MWh; negatives accepted (IO-3)."""
    base = _long_df()
    cfg = PortfolioConfig()

    nan_df = base.copy()
    nan_df.loc[0, "load_mwh"] = np.nan
    path = tmp_path / "load_nan.csv"
    nan_df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="non-finite load_mwh"):
        prepare_load(path, "A", cfg)

    neg_df = base.copy()
    neg_df.loc[0, "load_mwh"] = -50.0
    path = tmp_path / "load_neg.csv"
    neg_df.to_csv(path, index=False)
    with pytest.raises(ValueError, match="negative load_mwh"):
        prepare_load(path, "A", cfg)


def test_float_hour_column_consistent_across_intakes(tmp_path) -> None:
    """Integer-valued float hours load identically in load and LMP paths (IO-5).

    Regression: a float64 hour column raised a raw IndexError in the load
    aggregation while the LMP path accepted the same file.
    """
    float_load = _long_df()
    float_load["hour"] = float_load["hour"].astype(float)
    agg = aggregate_by_hour_iso(float_load)
    assert np.allclose(agg["A"], 15.0)

    frac = _long_df()
    frac["hour"] = frac["hour"].astype(float)
    frac.loc[0, "hour"] = 0.5
    with pytest.raises(ValueError, match=r"integers in \[0, 8759\]"):
        aggregate_by_hour_iso(frac)


def test_leap_length_file_clean_error_in_direct_api() -> None:
    """An 8784-hour frame errors cleanly in aggregate_by_hour_iso (IO-6).

    Regression: hours 8760..8783 passed the missing-hour check (0..8759 all
    present) and overflowed the 8760 vector with a raw IndexError.
    """
    df = pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR + 24),
            "iso": "A",
            "load_mwh": 1.0,
        }
    )
    with pytest.raises(ValueError, match=r"integers in \[0, 8759\]"):
        aggregate_by_hour_iso(df)


def test_collapse_zonal_lmp_rejects_nan_price_and_negative_weight() -> None:
    """NaN zonal prices and negative load weights are errors (IO-2/IO-4).

    Regression: pandas' skipna sum dropped a NaN price from the weighted
    numerator while its load stayed in the denominator, biasing the collapsed
    price toward zero with no warning.
    """
    lmp = pd.DataFrame(
        {
            "hour": [0, 0],
            "iso": ["A", "A"],
            "zone": ["z1", "z2"],
            "lmp": [np.nan, 100.0],
        }
    )
    load = pd.DataFrame(
        {
            "hour": [0, 0],
            "iso": ["A", "A"],
            "zone": ["z1", "z2"],
            "load_mwh": [50.0, 50.0],
        }
    )
    with pytest.raises(ValueError, match="non-finite lmp"):
        collapse_zonal_lmp(lmp, load)

    lmp["lmp"] = [10.0, 100.0]
    load["load_mwh"] = [300.0, -200.0]
    with pytest.raises(ValueError, match="negative load_mwh weight"):
        collapse_zonal_lmp(lmp, load)
