"""Curation tests: ``iso-area-load``, ``counterparty-interchange``, ``iso-genmix`` (SPP).

Lane UC-SPP-DATAFIX (owner rulings R22 / R23). Tiny raw fixtures under a
temp root; ``paths.CLEAN_DIR`` redirected by :class:`RawFixtureTestCase`.
"""

from __future__ import annotations

import zipfile

import numpy as np
import pandas as pd

from scripts.data.curate_counterparty_interchange import curate as curate_ix
from scripts.data.curate_iso_area_load import curate as curate_load
from scripts.data.curate_iso_genmix import curate as curate_mix
from tests.helpers.base import RawFixtureTestCase
from tests.helpers.clean_asserts import assert_clean_valid, read_clean_or_fail

_HDR = "MarketHour, CSWS, EDE"


class TestIsoAreaLoad(RawFixtureTestCase):
    """SPP HOURLY_LOAD wide monthlies -> tidy area-load partitions."""

    def setUp(self) -> None:
        super().setUp()
        self.dir = self.tmp_path / "raw" / "spp-hourly-load"
        self.dir.mkdir(parents=True)

    def test_trivial_one_hour(self):
        (self.dir / "HOURLY_LOAD-202501.csv").write_text(
            f"{_HDR}\n01/01/2025 07:00:00,4000.5,500\n"
        )
        [path] = curate_load(raw_root=self.tmp_path / "raw", isos=["SPP"])
        assert_clean_valid("iso-area-load", iso="SPP", year=2025)
        df = read_clean_or_fail("iso-area-load", iso="SPP", year=2025)
        self.assertEqual(sorted(df["area"]), ["CSWS", "EDE"])
        self.assertEqual(
            df["interval_end_utc"].iloc[0], pd.Timestamp("2025-01-01 07:00", tz="UTC")
        )
        self.assertAlmostEqual(df.loc[df["area"] == "CSWS", "load_mw"].iloc[0], 4000.5)

    def test_year_zip_wins_over_extracted_csv_and_blank_dropped(self):
        with zipfile.ZipFile(self.dir / "hourly-load-2024.zip", "w") as z:
            z.writestr(
                "2024/HOURLY_LOAD-202401.csv", f"{_HDR}\n01/01/2024 07:00:00,1,\n"
            )
            z.writestr("2024/DAILY_HOURLY_LOAD-20240101.csv", "ignored")
        # Same month extracted: must NOT be double counted.
        (self.dir / "HOURLY_LOAD-202401.csv").write_text(
            f"{_HDR}\n01/01/2024 07:00:00,99,99\n"
        )
        curate_load(raw_root=self.tmp_path / "raw", isos=["SPP"])
        df = read_clean_or_fail("iso-area-load", iso="SPP", year=2024)
        self.assertEqual(len(df), 1)  # EDE blank dropped
        self.assertEqual(df["load_mw"].iloc[0], 1.0)

    def test_partition_is_the_local_year_of_the_hour_start(self):
        # 2025-01-01 06:00Z ends local HE24 of 2024-12-31 (CST).
        (self.dir / "HOURLY_LOAD-202412.csv").write_text(
            f"{_HDR}\n01/01/2025 06:00:00,7,7\n01/01/2025 07:00:00,8,8\n"
        )
        paths = curate_load(raw_root=self.tmp_path / "raw", isos=["SPP"])
        self.assertEqual(
            sorted(p.stem for p in paths), ["iso-area-load_2024", "iso-area-load_2025"]
        )


class TestCounterpartyInterchange(RawFixtureTestCase):
    """Both reporting sides onto SWPP's export-positive sign."""

    def setUp(self) -> None:
        super().setUp()
        self.dir = self.tmp_path / "raw" / "eia-930-interchange"
        self.dir.mkdir(parents=True)

    def _cp(self, rows):
        pd.DataFrame(rows, columns=["ba", "mw", "utc_time"]).astype(
            {"utc_time": "datetime64[us]", "mw": "float32"}
        ).to_parquet(self.dir / "SWPP counterparty interchange hourly.parquet")

    def test_counterparty_leg_is_negated(self):
        self._cp([("MISO", 250.0, "2025-07-01 06:00")])
        curate_ix(raw_root=self.tmp_path / "raw", isos=["SPP"])
        df = read_clean_or_fail("counterparty-interchange", iso="SPP", year=2025)
        self.assertEqual(df["reporter"].tolist(), ["counterparty"])
        self.assertEqual(df["export_mw"].iloc[0], -250.0)  # MISO exports INTO SWPP

    def test_own_leg_fall_back_hour_localized_in_order(self):
        self._cp([("MISO", 1.0, "2025-11-02 06:00")])
        own = pd.DataFrame(
            {
                "diba": ["SPC", "SPC", "SPC"],
                "mw": np.array([10.0, 20.0, 30.0], dtype="float32"),
                "local_time": pd.to_datetime(
                    ["2025-11-02 01:00", "2025-11-02 01:00", "2025-11-02 02:00"]
                ).astype("datetime64[us]"),
            }
        )
        own.to_parquet(self.dir / "SWPP interchange hourly.parquet")
        curate_ix(raw_root=self.tmp_path / "raw", isos=["SPP"])
        df = read_clean_or_fail("counterparty-interchange", iso="SPP", year=2025)
        spc = df[df["counterparty"] == "SPC"].sort_values("interval_end_utc")
        self.assertEqual(
            spc["interval_end_utc"].dt.strftime("%H").tolist(), ["06", "07", "08"]
        )

    def test_missing_counterparty_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            curate_ix(raw_root=self.tmp_path / "raw", isos=["SPP"])


class TestIsoGenmix(RawFixtureTestCase):
    """SPP 5-minute GenMix -> hourly means by fuel."""

    COLS = (
        "Coal Market, Coal Self, Diesel Fuel Oil Market, Diesel Fuel Oil Self, Hydro Market,"
        " Hydro Self, Natural Gas Market, Gas Self, Nuclear Market, Nuclear Self, Solar Market,"
        " Solar Self, Waste Disposal Services Market, Waste Disposal Services Self, Wind Market,"
        " Wind Self, Waste Heat Market, Waste Heat Self, Other Market, Other Self, Load"
    )

    def _write(self, year, stamps, wind):
        d = self.tmp_path / "raw" / "spp-genmix"
        d.mkdir(parents=True, exist_ok=True)
        lines = [f"GMT MKT Interval, {self.COLS}"]
        for t, w in zip(stamps, wind):
            vals = ["0"] * 21
            if w is None:
                vals = [""] * 21
            else:
                vals[14], vals[15] = f"{w}", "1"
            lines.append(f"{t}," + ",".join(vals))
        (d / f"GenMix_{year}.csv").write_text("\n".join(lines) + "\n")

    def test_hour_mean_of_interval_end_stamps(self):
        start = pd.Timestamp("2025-01-01 06:05", tz="UTC")
        stamps = [
            (start + pd.Timedelta(minutes=5 * i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            for i in range(24)
        ]
        self._write(2025, stamps, list(range(24)))
        curate_mix(raw_root=self.tmp_path / "raw", isos=["SPP"])
        df = read_clean_or_fail("iso-genmix", iso="SPP", year=2025)
        wind = df[df["fuel"] == "wind"].set_index("interval_end_utc")
        # 06:05..07:00 -> hour ending 07:00: mean(0..11) + 1 (Self).
        self.assertAlmostEqual(
            wind.loc[pd.Timestamp("2025-01-01 07:00", tz="UTC"), "generation_mw"], 6.5
        )
        self.assertEqual(int(wind["n_intervals"].iloc[0]), 12)
        self.assertEqual(len(wind), 2)

    def test_blank_rows_dropped_and_prior_year_interval_excluded(self):
        stamps = [
            "2019-01-01T06:00:00Z",
            "2019-01-01T06:05:00Z",
            "2019-01-01T06:10:00Z",
        ]
        self._write(2019, stamps, [5, 7, None])
        paths = curate_mix(raw_root=self.tmp_path / "raw", isos=["SPP"])
        self.assertEqual([p.stem for p in paths], ["iso-genmix_2019"])
        df = read_clean_or_fail("iso-genmix", iso="SPP", year=2019)
        wind = df[df["fuel"] == "wind"]
        self.assertEqual(int(wind["n_intervals"].iloc[0]), 1)
        self.assertAlmostEqual(wind["generation_mw"].iloc[0], 8.0)
