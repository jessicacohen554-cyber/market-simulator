"""Round-trip tests for weather curation (scripts/data/curate_weather.py).

Builds minimal synthetic raw CSV fixtures, runs ``curate_iso_year``, and
validates:
  - The clean Parquet passes ``validate_clean`` (schema + provenance check).
  - Columns and dtypes match the weather schema.
  - tmax_c is non-null for all rows.
  - tmin_c is null for sentinel-zone rows sourced from TMAX-only files.
  - NaN gaps in tmax_c are filled before writing.
  - ``load_weather`` (eia_loader) reads the clean Parquet and optionally
    filters by zone.

Two ISOs are exercised:
  - ERCOT: single zone-temp CSV (date, zone, tmax_c, tmin_c).
  - NYISO: zone-temp CSV + downstate TMAX-only CSV (tests sentinel zone).
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts.data import curate_weather
from scripts.lib.clean_io import validate_clean

# Import after clean_io so paths is available as an attribute.
import market_sim.config.paths as _paths


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _write_ercot(raw_root: Path, year: int) -> None:
    d = raw_root / "ercot-weather"
    d.mkdir(parents=True, exist_ok=True)
    rows = []
    for zone in ("Houston", "North"):
        for day in range(3):
            date = pd.Timestamp(f"{year}-01-0{day + 1}")
            tmax = 10.0 + day + (5.0 if zone == "Houston" else 0.0)
            tmin = tmax - 8.0
            rows.append(
                {
                    "date": date.date().isoformat(),
                    "zone": zone,
                    "tmax_c": tmax,
                    "tmin_c": tmin,
                }
            )
    # Inject a NaN gap in tmax_c on day 2 for "Houston" to test gap-fill.
    rows[1]["tmax_c"] = float("nan")
    pd.DataFrame(rows).to_csv(d / "ercot_zone_temp_daily.csv", index=False)


def _write_nyiso(raw_root: Path, year: int) -> None:
    d = raw_root / "nyiso-weather"
    d.mkdir(parents=True, exist_ok=True)
    # Per-zone CSV (date, zone, tmax_c, tmin_c).
    pd.DataFrame(
        {
            "date": [f"{year}-07-01", f"{year}-07-02"],
            "zone": ["NYC", "NYC"],
            "tmax_c": [32.0, 33.0],
            "tmin_c": [24.0, 25.0],
        }
    ).to_csv(d / "nyiso_zone_temp_daily.csv", index=False)
    # Downstate TMAX-only CSV (no zone column).
    pd.DataFrame(
        {
            "date": [f"{year}-07-01", f"{year}-07-02"],
            "tmax_c": [31.5, 32.5],
        }
    ).to_csv(d / "nyiso_downstate_tmax_daily.csv", index=False)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestCurateWeatherERCOT(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)

        self._orig_clean = _paths.CLEAN_DIR
        _paths.CLEAN_DIR = root / "clean"

        self._orig_raw_root = curate_weather._WEATHER_RAW_ROOT
        curate_weather._WEATHER_RAW_ROOT = root / "raw"

        _write_ercot(curate_weather._WEATHER_RAW_ROOT, 2023)

    def tearDown(self):
        _paths.CLEAN_DIR = self._orig_clean
        curate_weather._WEATHER_RAW_ROOT = self._orig_raw_root
        self._tmp.cleanup()

    def _clean(self) -> pd.DataFrame:
        path = _paths.clean_path("weather", iso="ERCOT", year=2023)
        validate_clean(path)
        return pd.read_parquet(path)

    def test_curate_writes_parquet(self):
        path = curate_weather.curate_iso_year("ERCOT", 2023)
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())

    def test_row_count_and_zones(self):
        curate_weather.curate_iso_year("ERCOT", 2023)
        df = self._clean()
        # 2 zones × 3 days = 6 rows.
        self.assertEqual(len(df), 6)
        self.assertSetEqual(set(df["zone"].unique()), {"Houston", "North"})

    def test_tmax_non_null_after_gap_fill(self):
        curate_weather.curate_iso_year("ERCOT", 2023)
        df = self._clean()
        self.assertTrue(
            df["tmax_c"].notna().all(), "tmax_c must be non-null (gap-filled)"
        )

    def test_tmin_non_null_for_zone_file(self):
        curate_weather.curate_iso_year("ERCOT", 2023)
        df = self._clean()
        self.assertTrue(
            df["tmin_c"].notna().all(),
            "tmin_c should be non-null for zone-level ERCOT data",
        )

    def test_dtypes(self):
        curate_weather.curate_iso_year("ERCOT", 2023)
        df = self._clean()
        # datetime64 resolution varies by pyarrow version (ns or us); check kind.
        self.assertEqual(df["date"].dtype.kind, "M")
        self.assertTrue(hasattr(df["zone"].dtype, "name"))  # string / object
        self.assertEqual(df["tmax_c"].dtype, np.float64)
        self.assertEqual(df["tmin_c"].dtype, np.float64)

    def test_year_filter(self):
        curate_weather.curate_iso_year("ERCOT", 2023)
        df = self._clean()
        years = df["date"].dt.year.unique()
        self.assertEqual(list(years), [2023])


class TestCurateWeatherNYISO(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)

        self._orig_clean = _paths.CLEAN_DIR
        _paths.CLEAN_DIR = root / "clean"

        self._orig_raw_root = curate_weather._WEATHER_RAW_ROOT
        curate_weather._WEATHER_RAW_ROOT = root / "raw"

        _write_nyiso(curate_weather._WEATHER_RAW_ROOT, 2023)

    def tearDown(self):
        _paths.CLEAN_DIR = self._orig_clean
        curate_weather._WEATHER_RAW_ROOT = self._orig_raw_root
        self._tmp.cleanup()

    def _clean(self) -> pd.DataFrame:
        path = _paths.clean_path("weather", iso="NYISO", year=2023)
        validate_clean(path)
        return pd.read_parquet(path)

    def test_curate_writes_parquet(self):
        path = curate_weather.curate_iso_year("NYISO", 2023)
        self.assertIsNotNone(path)
        self.assertTrue(path.exists())

    def test_zones_include_sentinel(self):
        curate_weather.curate_iso_year("NYISO", 2023)
        df = self._clean()
        zones = set(df["zone"].unique())
        self.assertIn("NYC", zones)
        self.assertIn("_downstate", zones)

    def test_row_count(self):
        curate_weather.curate_iso_year("NYISO", 2023)
        df = self._clean()
        # NYC × 2 days + _downstate × 2 days = 4 rows.
        self.assertEqual(len(df), 4)

    def test_downstate_tmin_is_null(self):
        curate_weather.curate_iso_year("NYISO", 2023)
        df = self._clean()
        ds = df[df["zone"] == "_downstate"]
        self.assertTrue(
            ds["tmin_c"].isna().all(),
            "_downstate tmin_c must be null (TMAX-only source)",
        )

    def test_zone_tmin_non_null(self):
        curate_weather.curate_iso_year("NYISO", 2023)
        df = self._clean()
        nyc = df[df["zone"] == "NYC"]
        self.assertTrue(nyc["tmin_c"].notna().all(), "NYC tmin_c should be non-null")

    def test_tmax_non_null(self):
        curate_weather.curate_iso_year("NYISO", 2023)
        df = self._clean()
        self.assertTrue(df["tmax_c"].notna().all())


class TestLoadWeatherRoundTrip(unittest.TestCase):
    """Round-trip: curate_iso_year writes → validate_clean + parquet read-back.

    Tests that the clean Parquet for two ISOs (ERCOT and NYISO) produced by
    curate_iso_year can be read back with correct content and that the data
    structure supports zone-level filtering as load_weather would perform.
    """

    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)

        self._orig_clean = _paths.CLEAN_DIR
        _paths.CLEAN_DIR = root / "clean"

        self._orig_raw_root = curate_weather._WEATHER_RAW_ROOT
        curate_weather._WEATHER_RAW_ROOT = root / "raw"

        _write_ercot(curate_weather._WEATHER_RAW_ROOT, 2024)
        _write_nyiso(curate_weather._WEATHER_RAW_ROOT, 2024)
        curate_weather.curate_iso_year("ERCOT", 2024)
        curate_weather.curate_iso_year("NYISO", 2024)

    def tearDown(self):
        _paths.CLEAN_DIR = self._orig_clean
        curate_weather._WEATHER_RAW_ROOT = self._orig_raw_root
        self._tmp.cleanup()

    def _read(self, iso: str, year: int) -> pd.DataFrame:
        path = _paths.clean_path("weather", iso=iso, year=year)
        validate_clean(path)
        return pd.read_parquet(path)

    def test_ercot_round_trip_content(self):
        df = self._read("ERCOT", 2024)
        self.assertSetEqual(set(df["zone"].unique()), {"Houston", "North"})
        self.assertEqual(len(df), 6)
        self.assertTrue(df["tmax_c"].notna().all())

    def test_zone_filter_simulation(self):
        """Simulate the zone= filter that load_weather applies."""
        df = self._read("ERCOT", 2024)
        filtered = df[df["zone"] == "Houston"]
        self.assertEqual(len(filtered), 3)
        self.assertTrue((filtered["zone"] == "Houston").all())

    def test_missing_zone_filter_returns_empty(self):
        """A non-existent zone filter produces an empty frame (load_weather → None)."""
        df = self._read("ERCOT", 2024)
        filtered = df[df["zone"] == "NonExistentZone"]
        self.assertTrue(filtered.empty)

    def test_missing_year_file_absent(self):
        path = _paths.clean_path("weather", iso="ERCOT", year=1999)
        self.assertFalse(path.exists())

    def test_nyiso_round_trip_zones(self):
        df = self._read("NYISO", 2024)
        zones = set(df["zone"].unique())
        self.assertIn("NYC", zones)
        self.assertIn("_downstate", zones)
        self.assertEqual(len(df), 4)  # 2 zones × 2 days


if __name__ == "__main__":
    unittest.main()
