"""Tests for the ERCOT HSL (uncurtailed potential) data path.

Covers the per-year HSL parquet loaders in ``market_sim.data.renewables``
and the NP6 report ingestion in ``scripts/build_ercot_hsl.py`` that extends
HSL coverage beyond the 2023 UMass dataset.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data import renewables
from market_sim.data.renewables import (
    _hsl_cf_profile,
    hsl_potential_mw,
    load_ercot_hsl_hourly,
)

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts import build_ercot_hsl as hsl_script  # noqa: E402


def _write_synthetic_hsl(directory: Path, year: int) -> dict[str, np.ndarray]:
    """Write a synthetic per-year HSL parquet; return its series."""
    rng = np.random.default_rng(7)
    wind_hsl = 8000.0 + 2000.0 * rng.random(HOURS_PER_YEAR)
    solar_hsl = 4000.0 * rng.random(HOURS_PER_YEAR)
    series = {
        "wind_hsl_mw": wind_hsl,
        "wind_gen_mw": wind_hsl * 0.95,
        "solar_hsl_mw": solar_hsl,
        "solar_gen_mw": solar_hsl * 0.98,
    }
    df = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR), **series})
    directory.mkdir(parents=True, exist_ok=True)
    df.to_parquet(directory / f"ercot_{year}_hsl_hourly.parquet")
    return series


# ---------------------------------------------------------------------------
# renewables.py loaders
# ---------------------------------------------------------------------------


def test_load_ercot_hsl_2023_uncurtailed_at_least_delivered():
    """The shipped 2023 parquet loads and HSL >= GEN everywhere."""
    df = load_ercot_hsl_hourly(2023)
    assert df is not None
    assert len(df) == HOURS_PER_YEAR
    assert list(df["hour"]) == list(range(HOURS_PER_YEAR))
    for fuel in ("wind", "solar"):
        assert (df[f"{fuel}_hsl_mw"] >= df[f"{fuel}_gen_mw"]).all()


def test_load_ercot_hsl_missing_year_returns_none():
    """A year with no built parquet yields None, not an exception."""
    assert load_ercot_hsl_hourly(2199) is None


def test_hsl_potential_applies_2023_rescale():
    """ERCOT 2023 wind potential is rescaled to the 110 TWh target."""
    pot = hsl_potential_mw("ERCOT", 2023, "wind")
    assert pot is not None
    assert pot.shape == (HOURS_PER_YEAR,)
    np.testing.assert_allclose(pot.sum() / 1e6, 110.0, rtol=1e-9)


def test_hsl_potential_unmapped_iso_returns_none():
    """An ISO with no HSL-style dataset mapping yields None."""
    assert hsl_potential_mw("PJM", 2023, "wind") is None


def test_hsl_cf_profile_covers_new_year(tmp_path, monkeypatch):
    """A newly built per-year parquet (e.g. 2024 NP6) feeds the CF path.

    No rescale entry exists for the synthetic year, so the CF profile must
    round-trip exactly to the raw HSL MW series through the online capacity.
    """
    year = 2024
    series = _write_synthetic_hsl(tmp_path, year)
    monkeypatch.setattr(renewables, "_ERCOT_HSL_DIR", tmp_path)

    # Two zones, online all year, comfortably above the peak HSL so the CF
    # clip at 1.0 never engages and the round-trip is exact.
    monthly_capacity = np.tile(
        np.array([[7000.0], [5000.0]]), (1, 12)
    )
    cf = _hsl_cf_profile("ERCOT", year, "wind", monthly_capacity)
    assert cf is not None
    np.testing.assert_allclose(cf * 12000.0, series["wind_hsl_mw"])

    # The same year without a parquet (different fuel column intact) still
    # resolves; a year with no file does not.
    assert _hsl_cf_profile("ERCOT", year, "solar", monthly_capacity) is not None
    assert _hsl_cf_profile("ERCOT", 2199, "wind", monthly_capacity) is None


# ---------------------------------------------------------------------------
# build_ercot_hsl.py NP6 ingestion
# ---------------------------------------------------------------------------


def _hourly_report_frame(dates: pd.DatetimeIndex) -> pd.DataFrame:
    """Return an NP4-732-style hourly report frame for the given local hours."""
    return pd.DataFrame({
        "DELIVERY_DATE": dates.strftime("%m/%d/%Y"),
        "HOUR_ENDING": [f"{h + 1}:00" for h in dates.hour],
        "ACTUAL_SYSTEM_WIDE": 5000.0 + np.arange(len(dates)) % 100,
        "ACTUAL_SYSTEM_WIDE_HSL": 6000.0 + np.arange(len(dates)) % 100,
        "COP_HSL_SYSTEM_WIDE": 9999.0,  # must NOT be picked over the actual
        "STWPF_SYSTEM_WIDE": 5500.0,
    })


def test_parse_report_hourly_layout_prefers_actual_hsl():
    """DELIVERY_DATE/HOUR_ENDING parse; actual HSL wins over COP HSL."""
    dates = pd.date_range("2024-06-01", periods=48, freq="h")
    parsed = hsl_script._parse_report("wind.csv", _hourly_report_frame(dates))
    assert len(parsed) == 48
    assert (parsed["hsl_mw"] < 9999.0).all()  # actual column, not COP
    assert parsed["ts"].iloc[0] == pd.Timestamp("2024-06-01 00:00")
    assert parsed["ts"].iloc[-1] == pd.Timestamp("2024-06-02 23:00")


def test_parse_report_drops_forecast_only_rows():
    """Rows with no actuals (the rolling forecast window) are dropped."""
    dates = pd.date_range("2024-06-01", periods=24, freq="h")
    df = _hourly_report_frame(dates)
    df.loc[12:, "ACTUAL_SYSTEM_WIDE"] = np.nan
    parsed = hsl_script._parse_report("wind.csv", df)
    assert len(parsed) == 12


def test_parse_report_five_minute_interval_ending():
    """5-minute interval-ending stamps land in the hour they cover."""
    ts = pd.date_range("2024-06-01 00:05", periods=24, freq="5min")
    df = pd.DataFrame({
        "SCED_TIMESTAMP": ts.strftime("%m/%d/%Y %H:%M:%S"),
        "SYSTEM_WIDE": 100.0,
        "SYSTEM_WIDE_HSL": 120.0,
    })
    parsed = hsl_script._parse_report("solar.csv", df)
    # Intervals ending 00:05..01:00 cover hour 0; 01:05..02:00 cover hour 1.
    assert (parsed["ts"].iloc[:12] == pd.Timestamp("2024-06-01 00:00")).all()
    assert (parsed["ts"].iloc[12:] == pd.Timestamp("2024-06-01 01:00")).all()


def test_fuel_identification():
    """Fuel resolves from filename first, then column signature."""
    assert hsl_script._fuel_of("ercot_wind_2024.zip", []) == "wind"
    assert hsl_script._fuel_of("solar-actuals.csv", []) == "solar"
    assert hsl_script._fuel_of("report.csv", ["STWPF_SYSTEM_WIDE"]) == "wind"
    assert hsl_script._fuel_of("report.csv", ["PVGRPP_SYSTEM_WIDE"]) == "solar"
    assert hsl_script._fuel_of("report.csv", ["FOO"]) is None


def test_to_model_clock_drops_leap_day_and_fills_dst_gap():
    """A leap-year series lands on the fixed 8760 clock, Feb 29 dropped."""
    ts = pd.date_range("2024-01-01", "2024-12-31 23:00", freq="h")
    assert len(ts) == 8784  # leap year
    rows = pd.DataFrame({
        "ts": ts,
        "gen_mw": np.full(len(ts), 100.0),
        "hsl_mw": np.full(len(ts), 150.0),
    })
    # Mark Feb 29 with a sentinel that must not survive, and knock out the
    # DST spring-forward hour (2024-03-10 02:00) to exercise interpolation.
    feb29 = (ts.month == 2) & (ts.day == 29)
    rows.loc[feb29.nonzero()[0], "gen_mw"] = 1.0e9
    rows = rows[rows["ts"] != pd.Timestamp("2024-03-10 02:00")]

    out = hsl_script._to_model_clock(rows, 2024)
    assert len(out) == HOURS_PER_YEAR
    assert not out["gen_mw"].isna().any()
    assert out["gen_mw"].max() == 100.0  # Feb 29 sentinel gone, gap filled
    np.testing.assert_allclose(out["hsl_mw"], 150.0)


def test_to_model_clock_rejects_incomplete_upload():
    """A series missing more than a day of hours is rejected loudly."""
    ts = pd.date_range("2024-01-01", periods=4000, freq="h")
    rows = pd.DataFrame({"ts": ts, "gen_mw": 1.0, "hsl_mw": 2.0})
    with pytest.raises(ValueError, match="incomplete"):
        hsl_script._to_model_clock(rows, 2024)


def test_aggregate_np6_hourly_end_to_end(tmp_path, monkeypatch):
    """Wind+solar CSV uploads aggregate to the 8760 output frame."""
    year = 2025
    ts = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    for fuel, sig in (("wind", "STWPF"), ("solar", "STPPF")):
        pd.DataFrame({
            "DELIVERY_DATE": ts.strftime("%m/%d/%Y"),
            "HOUR_ENDING": [f"{h + 1}:00" for h in ts.hour],
            "ACTUAL_SYSTEM_WIDE": 1000.0,
            # GEN a shade above HSL in one column tests the HSL >= GEN floor.
            "ACTUAL_SYSTEM_WIDE_HSL": 990.0 if fuel == "wind" else 1200.0,
            f"{sig}_SYSTEM_WIDE": 1100.0,
        }).to_csv(tmp_path / f"{fuel}_{year}.csv", index=False)
    monkeypatch.setattr(hsl_script, "NP6_DIR", tmp_path)

    df = hsl_script.aggregate_np6_hourly(year)
    assert df is not None
    assert len(df) == HOURS_PER_YEAR
    for fuel in ("wind", "solar"):
        assert (df[f"{fuel}_hsl_mw"] >= df[f"{fuel}_gen_mw"]).all()
    # The wind HSL was floored up to GEN; solar kept its reported headroom.
    np.testing.assert_allclose(df["wind_hsl_mw"], 1000.0)
    np.testing.assert_allclose(df["solar_hsl_mw"], 1200.0)


def test_aggregate_np6_hourly_missing_uploads_returns_none(tmp_path,
                                                           monkeypatch,
                                                           capsys):
    """No uploads -> None with a data-needed message, never fabricated."""
    monkeypatch.setattr(hsl_script, "NP6_DIR", tmp_path / "absent")
    assert hsl_script.aggregate_np6_hourly(2024) is None
    out = capsys.readouterr().out
    assert "no NP6" in out
    assert "never" in out  # "Curtailment is never fabricated..."
