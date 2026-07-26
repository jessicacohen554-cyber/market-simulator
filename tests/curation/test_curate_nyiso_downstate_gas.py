"""Tests for the nyiso-downstate-gas intake on a tiny synthetic fixture.

Writes minimal raw gas-price fixtures (a few Transco Z6 NY daily prints, a few
Henry Hub daily prints, one month's per-LDC non-firm transport rate for both
downstate LDCs) into a tmp raw tree, runs ``curate``, and asserts the written
Parquet is schema-valid and each zone's delivered gas reconciles to
``transco_z6_ny_daily + ldc_transport_adder_month``. CLEAN_DIR is redirected to a
tmp dir so it never touches the real tree. Trivial case first (one month, sparse
prints, interpolation, two zones), then the schema round-trip.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_nyiso_downstate_gas as curate_dg
from scripts.lib import clean_io
from scripts.lib import nyiso_downstate_gas as dg
from scripts.lib.clean_io import validate_clean

# Sparse trading-day Transco prints in Jan 2024 with a cold-snap spike on the
# 16th; the 1st and 31st anchor the interpolation edges. Henry Hub is provenance
# only. The monthly per-LDC transport adder is a flat $1.50 (KEDLI / Long_Island)
# and $2.50 (KEDNY / NYC) for Jan.
_TRANSCO_CSV = """date,transco_z6_ny_usd_mmbtu,henry_hub_usd_mmbtu
2024-01-01,3.00,2.50
2024-01-16,20.00,3.00
2024-01-31,4.00,2.60
"""
_HH_CSV = """date,price_usd_mmbtu
2024-01-01,2.50
2024-01-16,3.00
2024-01-31,2.60
"""
_TRANSPORT_CSV = """ldc,zone,year,month,rate_usd_per_therm,rate_usd_per_mmbtu,source_statement
KEDLI,Long_Island,2024,1,0.15000,1.50,fixture
KEDNY,NYC,2024,1,0.25000,2.50,fixture
"""


def _write_fixture(raw_root: Path) -> None:
    gp = raw_root / "gas-prices"
    gp.mkdir(parents=True, exist_ok=True)
    (gp / "transco_z6_ny_daily.csv").write_text(_TRANSCO_CSV)
    (gp / "henry_hub_daily.csv").write_text(_HH_CSV)
    (gp / "nyiso_downstate_ldc_transport_monthly.csv").write_text(_TRANSPORT_CSV)


class TestCurateNyisoDownstateGas(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        _write_fixture(self.raw_root)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_builder_reconciliation(self) -> None:
        """Per zone: delivered_gas == interpolated transco daily + monthly adder."""
        df = dg.build_daily_frame("NYISO", 2024, self.raw_root)
        # Two downstate zones x a full leap-year calendar of daily rows.
        self.assertEqual(len(df), 366 * 2)
        self.assertEqual(list(df.columns), list(dg.CANONICAL_COLUMNS))
        self.assertEqual(set(df["zone"]), {"NYC", "Long_Island"})

        for zone, adder in (("Long_Island", 1.50), ("NYC", 2.50)):
            jan = df[(df["zone"] == zone) & (df["date"].dt.month == 1)].reset_index(
                drop=True
            )
            self.assertAlmostEqual(
                jan.loc[0, "transco_z6_ny_usd_per_mmbtu"], 3.00, places=3
            )
            self.assertAlmostEqual(
                jan.loc[0, "delivered_gas_usd_per_mmbtu"], 3.00 + adder, places=3
            )
            # The cold-snap spike lands on the 16th (index 15), not smeared away.
            self.assertAlmostEqual(
                jan.loc[15, "transco_z6_ny_usd_per_mmbtu"], 20.00, places=3
            )
            self.assertAlmostEqual(
                jan.loc[15, "delivered_gas_usd_per_mmbtu"], 20.00 + adder, places=3
            )
            # Every day: delivered == transco + adder (adder flat in Jan).
            self.assertTrue(
                (
                    (
                        jan["delivered_gas_usd_per_mmbtu"]
                        - jan["transco_z6_ny_usd_per_mmbtu"]
                        - adder
                    ).abs()
                    < 1e-6
                ).all()
            )
            # A non-trading day (the 2nd) interpolates between the 1st and 16th.
            self.assertGreater(jan.loc[1, "transco_z6_ny_usd_per_mmbtu"], 3.00)
            self.assertLess(jan.loc[1, "transco_z6_ny_usd_per_mmbtu"], 20.00)

    def test_curate_writes_valid_partition(self) -> None:
        """curate() writes a schema-valid Parquet per year through write_clean."""
        written = curate_dg.curate(raw_root=self.raw_root, isos=["NYISO"], years=[2024])
        self.assertEqual(len(written), 1)
        path = written[0]
        validate_clean(path)  # raises on any schema mismatch
        got = pd.read_parquet(path)
        self.assertEqual(len(got), 366 * 2)
        self.assertEqual((got["iso"] == "NYISO").all(), True)


if __name__ == "__main__":
    unittest.main()
