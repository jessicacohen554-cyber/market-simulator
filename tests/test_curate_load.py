"""Tests for the ``load`` curation pipeline (scripts/data/curate_load.py).

Builds a tiny synthetic raw fixture (one CAISO TAC area + a DAM forecast row,
one NYISO zone, one EIA-930 BA with wind/solar), runs the real curation, and
asserts the clean output is schema-valid and reconciled correctly:

  * CAISO actual ``mw`` -> ``load_mw``; SLD DAM ``MW`` -> ``load_forecast_mw``.
  * NYISO local Eastern wall-clock -> tz-aware UTC, carrying ``interval_start_local``.
  * EIA Demand -> ``load_mw``; net load = Demand - wind - solar only where both
    are co-available (null otherwise).

This is a fixture-scale run, NOT a full-data curation. CLEAN_DIR and the raw
input dirs are redirected to temp dirs so it never touches the real data tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_load
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _write_caiso(caiso_dir: Path) -> None:
    caiso_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "interval_start_gmt": [
                "2023-06-01 08:00:00+00:00",
                "2023-06-01 09:00:00+00:00",
            ],
            "tac_area": ["CA ISO-TAC", "CA ISO-TAC"],
            "mw": [100, 110],
        }
    ).to_csv(caiso_dir / "CAISO_tac_load_hourly_2023.csv", index=False)

    # SLD_FCST_ACTUAL: one DAM forecast row (kept) + one ACTUAL row (dropped).
    pd.DataFrame(
        {
            "INTERVALSTARTTIME_GMT": [
                "2023-06-01T08:00:00-00:00",
                "2023-06-01T08:00:00-00:00",
            ],
            "MARKET_RUN_ID": ["DAM", "ACTUAL"],
            "TAC_AREA_NAME": ["CA ISO-TAC", "CA ISO-TAC"],
            "MW": [105, 999],
        }
    ).to_csv(caiso_dir / "20230601_20230701_SLD_FCST_ACTUAL_test_v1.csv", index=False)


def _write_nyiso(nyiso_dir: Path) -> None:
    nyiso_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "Time Stamp": ["2023-01-01 00:00:00", "2023-01-01 01:00:00"],
            "Name": ["CAPITL", "CAPITL"],
            "Load": [1000.0, 1010.0],
        }
    ).to_csv(nyiso_dir / "NYISO_load_actuals_2023.csv", index=False)


def _write_eia(eia_dir: Path) -> None:
    eia_dir.mkdir(parents=True, exist_ok=True)
    # h0: wind+solar present -> net computable; h1: solar missing; h2: wind missing.
    pd.DataFrame(
        {
            "UTC time": pd.to_datetime(
                ["2024-03-01 00:00", "2024-03-01 01:00", "2024-03-01 02:00"]
            ),
            "Demand": [500.0, 600.0, 700.0],
            "Demand forecast": [510.0, 610.0, 710.0],
            "NG: WND": [50.0, 60.0, None],
            "NG: SUN": [20.0, None, 10.0],
        }
    ).to_parquet(eia_dir / "ERCO hourly.parquet", index=False)


class TestCurateLoad(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)

        # Redirect the clean output tree (mirrors tests/test_clean_io.py).
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

        # Redirect the raw input dirs the curation script reads.
        self._orig_dirs = (
            curate_load.CAISO_DIR,
            curate_load.NYISO_DIR,
            curate_load.EIA_DIR,
        )
        curate_load.CAISO_DIR = root / "raw" / "CAISO"
        curate_load.NYISO_DIR = root / "raw" / "NYISO"
        curate_load.EIA_DIR = root / "raw" / "eia"

        _write_caiso(curate_load.CAISO_DIR)
        _write_nyiso(curate_load.NYISO_DIR)
        _write_eia(curate_load.EIA_DIR)

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        (curate_load.CAISO_DIR, curate_load.NYISO_DIR, curate_load.EIA_DIR) = (
            self._orig_dirs
        )
        self._tmp.cleanup()

    def _clean(self, iso: str, year: int) -> pd.DataFrame:
        path = clean_io.paths.clean_path("load", iso=iso, year=year)
        validate_clean(path)  # round-trip schema check
        return pd.read_parquet(path)

    def test_curate_all_writes_expected_partitions(self):
        written = curate_load.curate_all()
        names = {(p.parts[-2], p.name) for p in written}
        self.assertIn(("CAISO", "load_2023.parquet"), names)
        self.assertIn(("NYISO", "load_2023.parquet"), names)
        self.assertIn(("ERCOT", "load_2024.parquet"), names)

    def test_caiso_actual_and_dam_forecast(self):
        curate_load.curate_all()
        df = self._clean("CAISO", 2023).sort_values("interval_start_utc")
        self.assertEqual(list(df["zone"].unique()), ["CA ISO-TAC"])
        self.assertEqual(df["load_mw"].tolist(), [100.0, 110.0])
        # The 08:00 hour gets the DAM forecast (105); the 09:00 hour has none.
        fc = df.set_index("interval_start_utc")["load_forecast_mw"]
        self.assertEqual(fc.loc["2023-06-01 08:00:00+00:00"], 105.0)
        self.assertTrue(pd.isna(fc.loc["2023-06-01 09:00:00+00:00"]))
        # No co-available renewables in the CAISO feed.
        self.assertTrue(df["net_load_mw"].isna().all())

    def test_nyiso_local_to_utc(self):
        curate_load.curate_all()
        df = self._clean("NYISO", 2023).sort_values("interval_start_utc")
        self.assertEqual(list(df["zone"].unique()), ["CAPITL"])
        # January is EST (UTC = local + 5h); local wall-clock is carried.
        self.assertEqual(
            str(df["interval_start_utc"].iloc[0]), "2023-01-01 05:00:00+00:00"
        )
        self.assertEqual(str(df["interval_start_local"].iloc[0]), "2023-01-01 00:00:00")
        self.assertEqual(str(df["interval_start_utc"].dt.tz), "UTC")
        self.assertEqual(df["load_mw"].tolist(), [1000.0, 1010.0])

    def test_eia_net_load_only_when_wind_and_solar_coavailable(self):
        curate_load.curate_all()
        df = self._clean("ERCOT", 2024).sort_values("interval_start_utc")
        self.assertEqual(list(df["zone"].unique()), ["ERCO"])
        self.assertEqual(df["load_mw"].tolist(), [500.0, 600.0, 700.0])
        self.assertEqual(df["load_forecast_mw"].tolist(), [510.0, 610.0, 710.0])
        net = df["net_load_mw"].tolist()
        self.assertEqual(net[0], 500.0 - 50.0 - 20.0)  # both present
        self.assertTrue(pd.isna(net[1]))  # solar missing
        self.assertTrue(pd.isna(net[2]))  # wind missing


if __name__ == "__main__":
    unittest.main()
