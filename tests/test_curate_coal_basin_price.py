"""Tests for scripts/curate_coal_basin_price.py.

Drives the curation on a tiny synthetic raw fixture (not the real EIA pull):
one market-sales-price row and one price-by-rank row -> curate -> assert the
written clean file is schema-valid and the two EIA routes tidy onto one
`metric`-keyed frame correctly (the ALL sentinel on the dimension the other
route doesn't carry).

CLEAN_DIR is redirected to a tmp dir (mirroring tests/test_clean_io.py) so the
curation never writes the real data/clean tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_coal_basin_price
from scripts.lib import clean_io
from scripts.lib.clean_io import read_clean_metadata, validate_clean


class TestCurateCoalBasinPrice(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.raw_dir = Path(self._tmp.name) / "raw" / "coal-prices"
        self.raw_dir.mkdir(parents=True)

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"

        (self.raw_dir / "eia_coal_market_sales_price.csv").write_text(
            "year,region_id,region_name,market_type_id,market_type_name,"
            "price_usd_per_ton,sales_short_tons\n"
            "2023,PRB,Powder River Basin,TOT,Total,14.68,234000000.0\n"
        )
        (self.raw_dir / "eia_coal_price_by_rank.csv").write_text(
            "year,region_id,region_name,coal_rank_id,coal_rank_name,price_usd_per_ton\n"
            "2023,PRB,Powder River Basin,SUB,Subbituminous,14.68\n"
        )

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid_file(self):
        out = curate_coal_basin_price.curate(raw_dir=self.raw_dir)
        self.assertTrue(out.exists())
        self.assertEqual(out.name, "coal-basin-price.parquet")
        schema = validate_clean(out)
        self.assertEqual(schema.datatype, "coal-basin-price")

    def test_reconciliation_is_correct(self):
        out = curate_coal_basin_price.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(out).sort_values("metric").reset_index(drop=True)

        self.assertEqual(len(df), 2)
        market = df[df["metric"] == "market_sales_price"].iloc[0]
        self.assertEqual(market["market_type_id"], "TOT")
        self.assertEqual(market["coal_rank_id"], "ALL")  # sentinel, not null
        self.assertEqual(market["price_usd_per_ton"], 14.68)
        self.assertEqual(market["sales_short_tons"], 234000000.0)

        rank = df[df["metric"] == "price_by_rank"].iloc[0]
        self.assertEqual(rank["coal_rank_id"], "SUB")
        self.assertEqual(rank["market_type_id"], "ALL")  # sentinel, not null
        self.assertTrue(pd.isna(rank["sales_short_tons"]))

    def test_source_provenance_embedded(self):
        out = curate_coal_basin_price.curate(raw_dir=self.raw_dir)
        meta = read_clean_metadata(out)
        self.assertEqual(meta["datatype"], "coal-basin-price")
        self.assertIn("eia_coal_market_sales_price.csv", meta["source"])
        self.assertIn("eia_coal_price_by_rank.csv", meta["source"])

    def test_idempotent_rerun(self):
        first = curate_coal_basin_price.curate(raw_dir=self.raw_dir)
        df1 = pd.read_parquet(first)
        second = curate_coal_basin_price.curate(raw_dir=self.raw_dir)
        df2 = pd.read_parquet(second)
        self.assertEqual(first, second)
        pd.testing.assert_frame_equal(df1, df2)

    def test_missing_raw_raises(self):
        empty = Path(self._tmp.name) / "raw" / "empty"
        empty.mkdir(parents=True)
        with self.assertRaises(FileNotFoundError):
            curate_coal_basin_price.curate(raw_dir=empty)


if __name__ == "__main__":
    unittest.main()
