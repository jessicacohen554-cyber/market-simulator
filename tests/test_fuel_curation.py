"""Round-trip tests: synthetic raw CSV → curate → read_clean → fuel.py parity.

Each test class covers one new datatype added in the fuel-prices Parquet routing:

  - ``fuel-hub-monthly`` (Henry Hub EIA monthly)
  - ``fuel-basis`` (winter gas basis by ISO/month)
  - ``fuel-zonal-hub`` (ERCOT per-zone annual hub prices/basis)
  - ``fuel-takeorpay`` (ERCOT per-plant gas spot share)

Tests use tiny synthetic raw fixtures so the real ``data/raw`` tree is never
required.  ``CLEAN_DIR`` is redirected to a tmp directory (same pattern as
``tests/test_curate_fuel_prices.py``) so the real ``data/clean`` tree is
never written.
"""

import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_fuel_prices
from scripts.lib import clean_io
from scripts.lib.clean_io import read_clean_metadata, validate_clean


class _CleanDirBase(unittest.TestCase):
    """Redirect CLEAN_DIR to a tmp dir; restore on teardown."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    @staticmethod
    def _setenv(key: str, value: str | None):
        """Set or unset an env var; return the previous value (or None)."""
        prev = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
        return prev

    def _with_clean_flag(self, flag_key: str):
        """Context: set USE_CLEAN env flag and restore it on exit."""

        class _CM:
            def __init__(self_, key):
                self_._key = key
                self_._prev = None

            def __enter__(self_):
                self_._prev = os.environ.get(self_._key)
                os.environ[self_._key] = "1"

            def __exit__(self_, *_):
                if self_._prev is None:
                    os.environ.pop(self_._key, None)
                else:
                    os.environ[self_._key] = self_._prev

        return _CM(flag_key)


class TestHubMonthlyRoundTrip(_CleanDirBase):
    """fuel-hub-monthly: monthly CSV → curate → Parquet valid → fuel.py parity."""

    def setUp(self):
        super().setUp()
        self.gas_dir = self.root / "raw" / "gas-prices"
        self.gas_dir.mkdir(parents=True)
        (self.gas_dir / "henry_hub_monthly.csv").write_text(
            "year,month,price_usd_mmbtu\n"
            "2023,1,3.45\n"
            "2023,2,2.90\n"
            "2024,1,2.50\n"
            "2024,2,1.90\n"
        )

    def _curate(self):
        return curate_fuel_prices.curate_hub_monthly(gas_dir=self.gas_dir)

    def test_writes_schema_valid_parquet(self):
        out = self._curate()
        self.assertTrue(out.exists())
        schema = validate_clean(out)
        self.assertEqual(schema.datatype, "fuel-hub-monthly")

    def test_values_and_keys_correct(self):
        out = self._curate()
        df = pd.read_parquet(out)
        self.assertEqual(len(df), 4)
        self.assertTrue((df["fuel"] == "gas").all())
        self.assertTrue((df["hub"] == "henry_hub").all())
        self.assertEqual(df["year"].dtype, "int64")
        self.assertEqual(df["month"].dtype, "int64")
        self.assertAlmostEqual(
            float(df[df["month"] == 1]["price_usd_per_mmbtu"].iloc[0]), 3.45
        )

    def test_source_provenance(self):
        out = self._curate()
        meta = read_clean_metadata(out)
        self.assertEqual(meta["datatype"], "fuel-hub-monthly")
        self.assertIn("henry_hub_monthly.csv", meta["source"])

    def test_clean_path_matches_raw_path(self):
        """_henry_hub_monthly(None) with MARKET_SIM_USE_CLEAN returns same dict."""
        from market_sim.data import fuel

        self._curate()
        raw_out = fuel._henry_hub_monthly(self.gas_dir / "henry_hub_monthly.csv")

        fuel._HH_MONTHLY_CLEAN_CACHE.clear()
        with self._with_clean_flag(fuel._USE_CLEAN_ENV):
            fuel._HH_MONTHLY_CLEAN_CACHE.clear()
            clean_out = fuel._henry_hub_monthly(None)
        fuel._HH_MONTHLY_CLEAN_CACHE.clear()

        self.assertEqual(clean_out, raw_out)


class TestBasisRoundTrip(_CleanDirBase):
    """fuel-basis: winter-basis CSV → curate → Parquet valid → fuel.py parity."""

    def setUp(self):
        super().setUp()
        self.raw_dir = self.root / "raw"
        self.raw_dir.mkdir(parents=True)
        (self.raw_dir / "gas_basis_by_iso_month.csv").write_text(
            "iso,year,month,hub,basis_usd_mmbtu,source\n"
            "NEISO,2023,1,Algonquin,4.50,EIA\n"
            "NEISO,2023,2,Algonquin,3.80,EIA\n"
            "NEISO,2024,1,Algonquin,2.10,EIA\n"
        )

    def _curate(self):
        return curate_fuel_prices.curate_basis(raw_dir=self.raw_dir)

    def test_writes_schema_valid_parquet(self):
        out = self._curate()
        self.assertTrue(out.exists())
        schema = validate_clean(out)
        self.assertEqual(schema.datatype, "fuel-basis")

    def test_source_column_stripped(self):
        out = self._curate()
        df = pd.read_parquet(out)
        self.assertNotIn("source", df.columns)
        self.assertIn("basis_usd_mmbtu", df.columns)
        self.assertEqual(len(df), 3)

    def test_clean_path_loads_frame(self):
        """_load_winter_basis_frame(None) with clean flag returns the curated frame."""
        from market_sim.data import fuel

        self._curate()
        fuel._WINTER_BASIS_CLEAN_CACHE.clear()
        fuel._WINTER_BASIS_CACHE.clear()

        with self._with_clean_flag(fuel._USE_CLEAN_ENV):
            fuel._WINTER_BASIS_CLEAN_CACHE.clear()
            frame = fuel._load_winter_basis_frame(None)
        fuel._WINTER_BASIS_CLEAN_CACHE.clear()

        self.assertIsNotNone(frame)
        self.assertIn("basis_usd_mmbtu", frame.columns)
        self.assertIn("iso", frame.columns)
        self.assertEqual(len(frame), 3)

    def test_idempotent(self):
        p1 = self._curate()
        df1 = pd.read_parquet(p1)
        p2 = self._curate()
        df2 = pd.read_parquet(p2)
        pd.testing.assert_frame_equal(df1, df2)


class TestZonalHubRoundTrip(_CleanDirBase):
    """fuel-zonal-hub: ERCOT zonal CSV → curate → Parquet valid → fuel.py parity."""

    def setUp(self):
        super().setUp()
        self.raw_dir = self.root / "raw"
        self.raw_dir.mkdir(parents=True)
        # Three rows: West (2 years) + North (1 year).  neg_day_freq only for West.
        (self.raw_dir / "ercot_zonal_gas_hub.csv").write_text(
            "zone,year,hub,basis_vs_hh_usd_mmbtu,neg_day_freq,source\n"
            "West,2023,Waha,-0.80,0.42,NGI\n"
            "North,2023,N-TX Citygate,0.10,,NGI\n"
            "West,2024,Waha,-0.70,0.38,NGI\n"
        )

    def _curate(self):
        return curate_fuel_prices.curate_zonal_hub(raw_dir=self.raw_dir)

    def test_writes_schema_valid_parquet(self):
        paths_written = self._curate()
        self.assertGreaterEqual(len(paths_written), 1)
        for p in paths_written:
            schema = validate_clean(p)
            self.assertEqual(schema.datatype, "fuel-zonal-hub")

    def test_iso_column_added_and_extras_present(self):
        self._curate()
        ercot_path = (
            clean_io.paths.CLEAN_DIR
            / "fuel-zonal-hub"
            / "ERCOT"
            / "fuel-zonal-hub.parquet"
        )
        df = pd.read_parquet(ercot_path)
        self.assertTrue((df["iso"] == "ERCOT").all())
        self.assertIn("basis_vs_hh_usd_mmbtu", df.columns)
        self.assertIn("neg_day_freq", df.columns)
        # West rows carry neg_day_freq; North row is NaN.
        west = df[df["zone"] == "West"]
        self.assertFalse(west["neg_day_freq"].isna().all())

    def test_clean_path_matches_raw_loader(self):
        """_load_ercot_zonal_gas_hub(None) with clean flag matches raw loader."""
        from market_sim.data import fuel

        self._curate()
        raw_path = self.raw_dir / "ercot_zonal_gas_hub.csv"
        raw_frame = fuel._load_ercot_zonal_gas_hub(raw_path)

        fuel._ERCOT_ZONAL_HUB_CLEAN_CACHE.clear()
        fuel._ERCOT_ZONAL_HUB_CACHE.clear()

        with self._with_clean_flag(fuel._USE_CLEAN_ENV):
            fuel._ERCOT_ZONAL_HUB_CLEAN_CACHE.clear()
            clean_frame = fuel._load_ercot_zonal_gas_hub(None)
        fuel._ERCOT_ZONAL_HUB_CLEAN_CACHE.clear()

        self.assertIsNotNone(clean_frame)
        self.assertEqual(
            set(clean_frame["zone"].tolist()), set(raw_frame["zone"].tolist())
        )
        west_raw = float(
            raw_frame[raw_frame["zone"] == "West"]["basis_vs_hh_usd_mmbtu"].iloc[0]
        )
        west_clean = float(
            clean_frame[clean_frame["zone"] == "West"]["basis_vs_hh_usd_mmbtu"].iloc[0]
        )
        self.assertAlmostEqual(west_clean, west_raw)


class TestTakeorpayRoundTrip(_CleanDirBase):
    """fuel-takeorpay: spot-share CSV → curate → Parquet valid → fuel.py parity."""

    def setUp(self):
        super().setUp()
        self.processed_dir = self.root / "processed"
        self.processed_dir.mkdir(parents=True)
        (self.processed_dir / "gas_takeorpay_ERCOT.csv").write_text(
            "plant_code,spot_share,contract_share,total_mmbtu,n_receipts,source,breakdown\n"
            "3404,0.80,0.20,1234567.0,12,EIA-923,spot|contract\n"
            "3481,0.25,0.75,987654.0,8,EIA-923,spot|contract\n"
            "3490,1.00,0.00,555000.0,5,EIA-923,spot\n"
        )

    def _curate(self):
        return curate_fuel_prices.curate_takeorpay(processed_dir=self.processed_dir)

    def test_writes_schema_valid_parquet(self):
        out = self._curate()
        self.assertTrue(out.exists())
        schema = validate_clean(out)
        self.assertEqual(schema.datatype, "fuel-takeorpay")

    def test_extra_columns_stripped(self):
        out = self._curate()
        df = pd.read_parquet(out)
        self.assertEqual(set(df.columns), {"plant_code", "spot_share", "total_mmbtu"})
        self.assertEqual(len(df), 3)

    def test_values_correct(self):
        out = self._curate()
        df = pd.read_parquet(out).sort_values("plant_code").reset_index(drop=True)
        self.assertEqual(list(df["plant_code"]), [3404, 3481, 3490])
        self.assertAlmostEqual(df.loc[0, "spot_share"], 0.80)
        self.assertAlmostEqual(df.loc[1, "spot_share"], 0.25)
        self.assertAlmostEqual(df.loc[2, "total_mmbtu"], 555000.0)

    def test_clean_path_matches_raw_loader(self):
        """ercot_gas_spot_share_by_plant() with clean flag matches raw loader."""
        from market_sim.data import fuel

        self._curate()
        raw_path = self.processed_dir / "gas_takeorpay_ERCOT.csv"
        raw_dict = fuel.ercot_gas_spot_share_by_plant(takeorpay_path=raw_path)

        fuel._ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE.clear()
        fuel._ERCOT_GAS_SPOT_PLANT_CACHE.clear()

        with self._with_clean_flag(fuel._USE_CLEAN_ENV):
            fuel._ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE.clear()
            clean_dict = fuel.ercot_gas_spot_share_by_plant(takeorpay_path=None)
        fuel._ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE.clear()

        self.assertIsNotNone(clean_dict)
        self.assertEqual(set(clean_dict.keys()), set(raw_dict.keys()))
        for pc, share in raw_dict.items():
            self.assertAlmostEqual(clean_dict[pc], share, places=10)


if __name__ == "__main__":
    unittest.main()
