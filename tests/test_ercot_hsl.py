"""Tests for the ERCOT HSL (uncurtailed potential) data path.

Covers the per-year HSL parquet loaders in ``market_sim.data.renewables``
and the NP6 report ingestion in ``scripts/data/build_ercot_hsl.py`` that extends
HSL coverage beyond the 2023 UMass dataset.
"""

import sys
from pathlib import Path
from unittest import mock

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

from scripts.data import build_ercot_hsl as hsl_script  # noqa: E402


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


def test_hsl_potential_reconciles_2023_coverage():
    """ERCOT 2023 wind potential is reconciled to the EIA-930 footprint.

    The UMass-derived 2023 series undercounts the system footprint (its
    delivered GEN sums below the EIA-930 delivered total), so the potential is
    scaled up to the EIA-930 level *preserving the dataset's own delivered/HSL
    curtailment ratio* — never a tune to model output. The reconciled total is
    EIA-930 delivered / (GEN/HSL), and the curtailment ratio is unchanged.
    """
    df = renewables.load_hsl_hourly("ERCOT", 2023)
    src_gen = float(df["wind_gen_mw"].sum())
    src_hsl = float(df["wind_hsl_mw"].sum())
    delivered = renewables._eia930_delivered_mwh("ERCOT", 2023, "wind")

    pot = hsl_potential_mw("ERCOT", 2023, "wind")
    assert pot is not None
    assert pot.shape == (HOURS_PER_YEAR,)
    # Reconciled to the EIA-930 footprint at the dataset's own curtailment ratio.
    np.testing.assert_allclose(pot.sum(), delivered / (src_gen / src_hsl), rtol=1e-9)
    # Curtailment ratio (delivered/HSL) preserved by the level-only scaling.
    np.testing.assert_allclose(delivered / pot.sum(), src_gen / src_hsl, rtol=1e-9)


def test_hsl_potential_unmapped_iso_returns_none():
    """An ISO with no HSL-style dataset mapping yields None."""
    assert hsl_potential_mw("PJM", 2023, "wind") is None


def test_hsl_cf_profile_covers_new_year(tmp_path, monkeypatch):
    """A newly built per-year parquet (e.g. 2024 NP6) feeds the CF path.

    A full-footprint source needs no coverage reconciliation, so with the
    EIA-930 reference absent the CF profile must round-trip exactly to the raw
    HSL MW series through the online capacity.
    """
    year = 2024
    series = _write_synthetic_hsl(tmp_path, year)
    monkeypatch.setattr(renewables, "_ERCOT_HSL_DIR", tmp_path)
    # No EIA-930 footprint reference -> series consumed as-is (the published
    # full-footprint case); exercises the no-reconciliation round-trip.
    monkeypatch.setattr(renewables, "_eia930_delivered_mwh", lambda *a, **k: None)

    # Two zones, online all year, comfortably above the peak HSL so the CF
    # clip at 1.0 never engages and the round-trip is exact.
    monthly_capacity = np.tile(np.array([[7000.0], [5000.0]]), (1, 12))
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
    """Return an NP4-732-style hourly report frame for the given CPT hours."""
    return pd.DataFrame(
        {
            "DELIVERY_DATE": dates.strftime("%m/%d/%Y"),
            "HOUR_ENDING": [f"{h + 1}:00" for h in dates.hour],
            "DSTFLAG": "N",
            "ACTUAL_SYSTEM_WIDE": 5000.0 + np.arange(len(dates)) % 100,
            "ACTUAL_SYSTEM_WIDE_HSL": 6000.0 + np.arange(len(dates)) % 100,
            "COP_HSL_SYSTEM_WIDE": 9999.0,  # must NOT be picked over the actual
            "STWPF_SYSTEM_WIDE": 5500.0,
        }
    )


def test_parse_report_hourly_layout_prefers_actual_hsl():
    """DELIVERY_DATE/HOUR_ENDING parse; actual HSL wins over COP HSL.

    June labels are Central *Prevailing* (CDT), so the CST model-clock stamp
    is one hour earlier than the naive label.
    """
    dates = pd.date_range("2024-06-01", periods=48, freq="h")
    parsed = hsl_script._parse_report("wind.csv", _hourly_report_frame(dates))
    assert len(parsed) == 48
    assert (parsed["hsl_mw"] < 9999.0).all()  # actual column, not COP
    assert parsed["ts"].iloc[0] == pd.Timestamp("2024-05-31 23:00")
    assert parsed["ts"].iloc[-1] == pd.Timestamp("2024-06-02 22:00")


def test_parse_report_cpt_to_cst_winter_identity():
    """Winter (CST) labels are already standard time: no shift."""
    dates = pd.date_range("2024-01-05", periods=24, freq="h")
    parsed = hsl_script._parse_report("wind.csv", _hourly_report_frame(dates))
    assert parsed["ts"].iloc[0] == pd.Timestamp("2024-01-05 00:00")
    assert parsed["ts"].iloc[-1] == pd.Timestamp("2024-01-05 23:00")


def test_parse_report_cpt_dst_transitions_cover_cst_clock():
    """Spring-forward (HE 3 absent) and fall-back (HE 2 repeated, DSTFLAG=Y)
    prevailing labels convert to a gapless, duplicate-free CST hour sequence."""
    # 2024-03-10: spring forward. Real reports carry HE 1,2,4..24 (23 rows).
    he = [1, 2] + list(range(4, 25))
    spring = pd.DataFrame(
        {
            "DELIVERY_DATE": "03/10/2024",
            "HOUR_ENDING": [f"{h}:00" for h in he],
            "DSTFLAG": "N",
            "ACTUAL_SYSTEM_WIDE": 100.0,
            "ACTUAL_SYSTEM_WIDE_HSL": 120.0,
        }
    )
    parsed = hsl_script._parse_report("wind.csv", spring)
    got = parsed["ts"].dt.strftime("%m-%d %H").tolist()
    # HE1,2 are CST hours 0,1; HE4..24 are CDT -> CST hours 2..22. Gapless.
    assert got == [f"03-10 {h:02d}" for h in range(23)]

    # 2024-11-03: fall back. HE 2 occurs twice; DSTFLAG=Y marks the repeat.
    rows = [(1, "N"), (2, "N"), (2, "Y")] + [(h, "N") for h in range(3, 25)]
    fall = pd.DataFrame(
        {
            "DELIVERY_DATE": "11/03/2024",
            "HOUR_ENDING": [f"{h}:00" for h, _ in rows],
            "DSTFLAG": [f for _, f in rows],
            "ACTUAL_SYSTEM_WIDE": 100.0,
            "ACTUAL_SYSTEM_WIDE_HSL": 120.0,
        }
    )
    parsed = hsl_script._parse_report("wind.csv", fall)
    got = parsed["ts"].dt.strftime("%m-%d %H").tolist()
    # HE1 (00:00 CDT) -> 11-02 23:00 CST; HE2 N/Y -> 00:00/01:00; HE3..24 -> 02..23.
    assert got == ["11-02 23"] + [f"11-03 {h:02d}" for h in range(24)]


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
    df = pd.DataFrame(
        {
            "SCED_TIMESTAMP": ts.strftime("%m/%d/%Y %H:%M:%S"),
            "SYSTEM_WIDE": 100.0,
            "SYSTEM_WIDE_HSL": 120.0,
        }
    )
    parsed = hsl_script._parse_report("solar.csv", df)
    # Intervals ending 00:05..01:00 cover CPT hour 0; 01:05..02:00 CPT hour 1
    # — June CPT is CDT, one hour ahead of the CST model clock.
    assert (parsed["ts"].iloc[:12] == pd.Timestamp("2024-05-31 23:00")).all()
    assert (parsed["ts"].iloc[12:] == pd.Timestamp("2024-06-01 00:00")).all()


def test_parse_report_2025_schema_prefers_system_wide_hsl_over_cop():
    """The 2025 NP6 rename (SYSTEM_WIDE_GEN/SYSTEM_WIDE_HSL replacing
    ACTUAL_SYSTEM_WIDE/COP_HSL_SYSTEM_WIDE) must still resolve the actual
    HSL, not fall back to the legacy COP HSL column that happens to sort
    earlier."""
    dates = pd.date_range("2025-06-01", periods=24, freq="h")
    df = pd.DataFrame(
        {
            "DELIVERY_DATE": dates.strftime("%m/%d/%Y"),
            "HOUR_ENDING": [f"{h + 1}:00" for h in dates.hour],
            "SYSTEM_WIDE_GEN": 5000.0,
            "COP_HSL_SYSTEM_WIDE": 9999.0,  # legacy column; must NOT be picked
            "STPPF_SYSTEM_WIDE": 5200.0,
            "SYSTEM_WIDE_HSL": 5500.0,
        }
    )
    parsed = hsl_script._parse_report("solar.csv", df)
    assert (parsed["gen_mw"] == 5000.0).all()
    assert (parsed["hsl_mw"] == 5500.0).all()


def test_read_csvs_recurses_nested_zips(tmp_path):
    """ERCOT's real NP6 download is a zip of per-posting zips, each holding
    one CSV; the reader must recurse to any depth to find them."""
    import zipfile

    inner_csv = tmp_path / "inner.csv"
    inner_csv.write_text("a,b\n1,2\n")
    inner_zip = tmp_path / "posting.zip"
    with zipfile.ZipFile(inner_zip, "w") as zf:
        zf.write(inner_csv, arcname="posting/data.csv")
    outer_zip = tmp_path / "month.zip"
    with zipfile.ZipFile(outer_zip, "w") as zf:
        zf.write(inner_zip, arcname="posting.zip")

    results = hsl_script._read_csvs(outer_zip)
    assert len(results) == 1
    name, frame = results[0]
    assert "posting.zip" in name and "data.csv" in name
    assert frame.to_dict("records") == [{"a": 1, "b": 2}]


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
    rows = pd.DataFrame(
        {
            "ts": ts,
            "gen_mw": np.full(len(ts), 100.0),
            "hsl_mw": np.full(len(ts), 150.0),
        }
    )
    # Mark Feb 29 with a sentinel that must not survive, and knock out the
    # DST spring-forward hour (2024-03-10 02:00) to exercise interpolation.
    feb29 = (ts.month == 2) & (ts.day == 29)
    rows.loc[feb29.nonzero()[0], "gen_mw"] = 1.0e9
    rows = rows[rows["ts"] != pd.Timestamp("2024-03-10 02:00")]

    # 2024 carries a cited known-bad window, which is filled from the
    # measured EIA-930 series (patched here so the unit test stays
    # self-contained); inside the window HSL = GEN by construction.
    with mock.patch.object(
        hsl_script,
        "load_eia_hourly_renewable_gen",
        return_value={"wind": np.full(HOURS_PER_YEAR, 100.0)},
    ):
        out = hsl_script._to_model_clock(rows, 2024, "wind")
    assert len(out) == HOURS_PER_YEAR
    assert not out["gen_mw"].isna().any()
    assert out["gen_mw"].max() == 100.0  # Feb 29 sentinel gone, gap filled
    known_bad = hsl_script._known_bad_mask(
        pd.MultiIndex.from_arrays(
            [
                pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h").month,
                pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h").day,
                pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h").hour,
            ],
            names=["month", "day", "hour"],
        ),
        2024,
    )
    np.testing.assert_allclose(out["hsl_mw"][~known_bad], 150.0)
    np.testing.assert_allclose(out["hsl_mw"][known_bad], 100.0)  # HSL = GEN fill


def test_to_model_clock_rejects_incomplete_upload():
    """A series missing more than a day of hours is rejected loudly."""
    ts = pd.date_range("2024-01-01", periods=4000, freq="h")
    rows = pd.DataFrame({"ts": ts, "gen_mw": 1.0, "hsl_mw": 2.0})
    with pytest.raises(ValueError, match="incomplete"):
        hsl_script._to_model_clock(rows, 2024, "wind")


def test_to_model_clock_fills_cited_known_bad_window_from_eia930():
    """The cited 2024-08-20..23 ERCOT telemetry defect is filled from EIA-930.

    Even though it carries valid-looking values, the window is a cited
    known-bad ERCOT source defect (``_KNOWN_BAD_NP6_WINDOWS``): it must be
    excluded and replaced with the measured EIA-930 hourly series (HSL =
    GEN inside the window — no fabricated curtailment headroom), NOT
    linearly interpolated (a night-bounded multi-day hole interpolates
    solar to identically zero), and doing so must not trip the >24h
    incomplete-upload guard (the general guard stays exactly as strict for
    anything outside the cited window).
    """
    ts = pd.date_range("2024-01-01", "2024-12-31 23:00", freq="h")
    assert len(ts) == 8784  # leap year
    rows = pd.DataFrame({"ts": ts, "gen_mw": 100.0, "hsl_mw": 150.0})
    # A physically-impossible spike, identical to the cited ERCOT defect.
    bad = (ts >= pd.Timestamp("2024-08-20")) & (ts < pd.Timestamp("2024-08-24"))
    rows.loc[bad, "gen_mw"] = 310_736.69
    rows.loc[bad, "hsl_mw"] = 302_119.3

    eia = {"solar": np.full(HOURS_PER_YEAR, 77.0)}
    with mock.patch.object(
        hsl_script, "load_eia_hourly_renewable_gen", return_value=eia
    ):
        out = hsl_script._to_model_clock(rows, 2024, "solar")
    assert len(out) == HOURS_PER_YEAR
    assert not out["gen_mw"].isna().any()
    # The spike is gone; the window carries the measured EIA-930 fill.
    assert out["gen_mw"].max() < 200.0
    calendar = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    known_bad = hsl_script._known_bad_mask(
        pd.MultiIndex.from_arrays(
            [calendar.month, calendar.day, calendar.hour],
            names=["month", "day", "hour"],
        ),
        2024,
    )
    np.testing.assert_allclose(out["gen_mw"][known_bad], 77.0)
    np.testing.assert_allclose(out["hsl_mw"][known_bad], 77.0)  # HSL = GEN
    np.testing.assert_allclose(out["gen_mw"][~known_bad], 100.0)
    np.testing.assert_allclose(out["hsl_mw"][~known_bad], 150.0)


def test_to_model_clock_known_bad_fill_requires_eia930():
    """A cited known-bad window with no EIA-930 series to fill it raises —
    the corrupt source hours are never silently interpolated or ingested."""
    ts = pd.date_range("2024-01-01", "2024-12-31 23:00", freq="h")
    rows = pd.DataFrame({"ts": ts, "gen_mw": 100.0, "hsl_mw": 150.0})
    with mock.patch.object(
        hsl_script, "load_eia_hourly_renewable_gen", return_value=None
    ):
        with pytest.raises(ValueError, match="EIA-930"):
            hsl_script._to_model_clock(rows, 2024, "solar")


def test_to_model_clock_known_bad_window_does_not_mask_other_gaps():
    """A genuinely incomplete upload still raises even in a year with a
    cited known-bad window — the exception is narrow, not a blanket cap
    increase."""
    ts = pd.date_range("2024-01-01", periods=4000, freq="h")
    rows = pd.DataFrame({"ts": ts, "gen_mw": 1.0, "hsl_mw": 2.0})
    with pytest.raises(ValueError, match="incomplete"):
        hsl_script._to_model_clock(rows, 2024, "wind")


def test_aggregate_np6_hourly_end_to_end(tmp_path, monkeypatch):
    """Wind+solar CSV uploads aggregate to the 8760 output frame."""
    year = 2025
    ts = pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    for fuel, sig in (("wind", "STWPF"), ("solar", "STPPF")):
        pd.DataFrame(
            {
                "DELIVERY_DATE": ts.strftime("%m/%d/%Y"),
                "HOUR_ENDING": [f"{h + 1}:00" for h in ts.hour],
                "ACTUAL_SYSTEM_WIDE": 1000.0,
                # GEN a shade above HSL in one column tests the HSL >= GEN floor.
                "ACTUAL_SYSTEM_WIDE_HSL": 990.0 if fuel == "wind" else 1200.0,
                f"{sig}_SYSTEM_WIDE": 1100.0,
            }
        ).to_csv(tmp_path / f"{fuel}_{year}.csv", index=False)
    monkeypatch.setattr(hsl_script, "NP6_DIR", tmp_path)

    df = hsl_script.aggregate_np6_hourly(year)
    assert df is not None
    assert len(df) == HOURS_PER_YEAR
    for fuel in ("wind", "solar"):
        assert (df[f"{fuel}_hsl_mw"] >= df[f"{fuel}_gen_mw"]).all()
    # The wind HSL was floored up to GEN; solar kept its reported headroom.
    np.testing.assert_allclose(df["wind_hsl_mw"], 1000.0)
    np.testing.assert_allclose(df["solar_hsl_mw"], 1200.0)


def test_aggregate_np6_hourly_missing_uploads_returns_none(
    tmp_path, monkeypatch, capsys
):
    """No uploads -> None with a data-needed message, never fabricated."""
    monkeypatch.setattr(hsl_script, "NP6_DIR", tmp_path / "absent")
    assert hsl_script.aggregate_np6_hourly(2024) is None
    out = capsys.readouterr().out
    assert "no NP6" in out
    assert "never" in out  # "Curtailment is never fabricated..."


# ---------------------------------------------------------------------------
# run_calibration_full.py shared curtailment table
# ---------------------------------------------------------------------------


def _flat_dispatch_frame(mw: float) -> pd.DataFrame:
    """Return a minimal bundle dispatch frame with flat wind/solar output."""
    hours = np.arange(HOURS_PER_YEAR, dtype=np.int32)
    return pd.concat(
        [
            pd.DataFrame({"fuel": fuel, "hour": hours, "mw": float(mw)})
            for fuel in ("wind", "solar")
        ],
        ignore_index=True,
    )


def test_curtailment_table_uses_consumed_potential(capsys):
    """The model side measures against the reconciled (consumed) potential.

    ERCOT 2023's wind HSL is reconciled 104 -> 113.28 TWh (the EIA-930
    footprint at the dataset's curtailment ratio) before the dispatch consumes
    it; measuring model curtailment against the raw HSL would understate it by
    the whole reconciliation margin (reading ~0 for a run that delivered more
    than the raw series).
    """
    from scripts.run_calibration_full import _print_curtailment_vs_reported

    _print_curtailment_vs_reported(2023, "ERCOT", _flat_dispatch_frame(0.0), label="3e")
    out = capsys.readouterr().out
    assert "[3e] Renewable curtailment" in out
    wind_row = next(
        line for line in out.splitlines() if line.strip().startswith("wind")
    )
    # The potential column reads the reconciled 113.28 TWh, not the raw 104.05.
    assert "113.28" in wind_row


def test_curtailment_table_data_needed_note(capsys):
    """Missing HSL years: note for HSL-capable ISOs, silence otherwise."""
    from scripts.run_calibration_full import _print_curtailment_vs_reported

    _print_curtailment_vs_reported(2199, "ERCOT", _flat_dispatch_frame(0.0))
    assert "no ERCOT HSL parquet" in capsys.readouterr().out

    _print_curtailment_vs_reported(2199, "PJM", _flat_dispatch_frame(0.0))
    assert capsys.readouterr().out == ""
