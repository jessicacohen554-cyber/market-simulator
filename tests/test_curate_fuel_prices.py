"""Tests for scripts/curate_fuel_prices.py.

Drives the curation end-to-end on a *tiny synthetic* raw fixture (not the real
data tree): a synthetic ``henry_hub_daily.csv`` -> curate -> assert the written
clean file is schema-valid and that the reconciliation is correct (price column
renamed verbatim, fuel/hub set, daily date -> 00:00 UTC tz-aware interval, naive
local wall-clock carried, one row per (fuel, hub, interval_start_utc)).

CLEAN_DIR is redirected to a tmp dir (mirroring tests/test_clean_io.py) so the
curation never writes the real ``data/clean`` tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_fuel_prices
from scripts.lib import clean_io
from scripts.lib.clean_io import read_clean_metadata, validate_clean


class TestCurateFuelPrices(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # Redirect the clean tree so writes never touch the repo (see test_clean_io).
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.root / "clean"

        # Tiny synthetic raw fixture: a 3-row Henry Hub daily series. One date is
        # a first-of-month (collision-prone with a monthly series) to exercise
        # that we curate the daily granularity cleanly.
        self.gas_dir = self.root / "raw" / "gas-prices"
        self.gas_dir.mkdir(parents=True)
        (self.gas_dir / "henry_hub_daily.csv").write_text(
            "date,price_usd_mmbtu\n2024-01-01,2.50\n2024-01-02,2.75\n2024-01-03,3.1\n"
        )

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid_file(self):
        out = curate_fuel_prices.curate(gas_dir=self.gas_dir)
        self.assertTrue(out.exists())
        # Single combined file under the fuel-prices datatype dir.
        self.assertEqual(out.name, "fuel-prices.parquet")
        # Round-trips against the embedded schema.
        schema = validate_clean(out)
        self.assertEqual(schema.datatype, "fuel-prices")

    def test_reconciliation_is_correct(self):
        out = curate_fuel_prices.curate(gas_dir=self.gas_dir)
        df = (
            pd.read_parquet(out)
            .sort_values("interval_start_utc")
            .reset_index(drop=True)
        )

        # One row per (fuel, hub, interval_start_utc); all three synthetic dates.
        self.assertEqual(len(df), 3)
        self.assertEqual(set(df["fuel"]), {"gas"})
        self.assertEqual(set(df["hub"]), {"henry_hub"})

        # Price column carried verbatim from the raw price_usd_mmbtu values.
        self.assertEqual(list(df["price_usd_per_mmbtu"]), [2.50, 2.75, 3.1])

        # Daily date -> 00:00 UTC, tz-aware.
        ts0 = df["interval_start_utc"].iloc[0]
        self.assertEqual(str(ts0.tz), "UTC")
        self.assertEqual(ts0, pd.Timestamp("2024-01-01 00:00:00", tz="UTC"))

        # Local wall-clock carried as tz-naive midnight of the same date.
        local0 = df["interval_start_local"].iloc[0]
        self.assertIsNone(local0.tz)
        self.assertEqual(local0, pd.Timestamp("2024-01-01 00:00:00"))

    def test_source_provenance_embedded(self):
        out = curate_fuel_prices.curate(gas_dir=self.gas_dir)
        meta = read_clean_metadata(out)
        self.assertEqual(meta["datatype"], "fuel-prices")
        self.assertIn("henry_hub_daily.csv", meta["source"])

    def test_idempotent_rerun(self):
        first = curate_fuel_prices.curate(gas_dir=self.gas_dir)
        df1 = pd.read_parquet(first)
        second = curate_fuel_prices.curate(gas_dir=self.gas_dir)
        df2 = pd.read_parquet(second)
        self.assertEqual(first, second)
        pd.testing.assert_frame_equal(df1, df2)

    def test_missing_benchmarks_raises(self):
        empty = self.root / "raw" / "empty"
        empty.mkdir(parents=True)
        with self.assertRaises(FileNotFoundError):
            curate_fuel_prices.curate(gas_dir=empty)

    def test_caiso_citygate_benchmark_reconciled(self):
        (self.gas_dir / "caiso_citygate_daily.csv").write_text(
            "date,ca_composite_usd_mmbtu,henry_hub_usd_mmbtu\n"
            "2023-01-12,24.29,3.55\n2023-01-26,7.80,2.71\n"
        )
        out = curate_fuel_prices.curate(gas_dir=self.gas_dir)
        df = pd.read_parquet(out)
        ca = df[df["hub"] == "ca_composite"].sort_values("interval_start_utc")
        self.assertEqual(list(ca["fuel"]), ["gas", "gas"])
        self.assertEqual(list(ca["price_usd_per_mmbtu"]), [24.29, 7.80])
        self.assertEqual(
            ca["interval_start_utc"].iloc[0],
            pd.Timestamp("2023-01-12 00:00:00", tz="UTC"),
        )


if __name__ == "__main__":
    unittest.main()
