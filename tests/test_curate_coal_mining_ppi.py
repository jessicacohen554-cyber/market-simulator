"""Tests for scripts/data/curate_coal_mining_ppi.py.

Drives the curation on a tiny synthetic raw fixture (not the real BLS pull):
two rows across the two series ids -> curate -> assert the written clean file
is schema-valid and the reconciliation is correct.

CLEAN_DIR is redirected to a tmp dir (mirroring tests/test_clean_io.py) so the
curation never writes the real data/clean tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_coal_mining_ppi
from scripts.lib import clean_io
from scripts.lib.clean_io import read_clean_metadata, validate_clean


class TestCurateCoalMiningPpi(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.raw_dir = Path(self._tmp.name) / "raw" / "coal-prices"
        self.raw_dir.mkdir(parents=True)

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp.name) / "clean"

        (self.raw_dir / "bls_coal_ppi.csv").write_text(
            "series_id,series_name,year,month,index_value\n"
            'WPU051,"PPI commodity: Coal (all coal, national)",2023,1,262.588\n'
            'PCU2121--2121--,"PPI industry: Coal Mining (NAICS 2121, national)",2023,1,270.011\n'
        )

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid_file(self):
        out = curate_coal_mining_ppi.curate(raw_dir=self.raw_dir)
        self.assertTrue(out.exists())
        self.assertEqual(out.name, "coal-mining-ppi.parquet")
        schema = validate_clean(out)
        self.assertEqual(schema.datatype, "coal-mining-ppi")

    def test_reconciliation_is_correct(self):
        out = curate_coal_mining_ppi.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(out).sort_values("series_id").reset_index(drop=True)

        self.assertEqual(len(df), 2)
        self.assertEqual(set(df["series_id"]), {"WPU051", "PCU2121--2121--"})
        wpu = df[df["series_id"] == "WPU051"].iloc[0]
        self.assertEqual(wpu["year"], 2023)
        self.assertEqual(wpu["month"], 1)
        self.assertEqual(wpu["index_value"], 262.588)

    def test_source_provenance_embedded(self):
        out = curate_coal_mining_ppi.curate(raw_dir=self.raw_dir)
        meta = read_clean_metadata(out)
        self.assertEqual(meta["datatype"], "coal-mining-ppi")
        self.assertIn("bls_coal_ppi.csv", meta["source"])

    def test_idempotent_rerun(self):
        first = curate_coal_mining_ppi.curate(raw_dir=self.raw_dir)
        df1 = pd.read_parquet(first)
        second = curate_coal_mining_ppi.curate(raw_dir=self.raw_dir)
        df2 = pd.read_parquet(second)
        self.assertEqual(first, second)
        pd.testing.assert_frame_equal(df1, df2)

    def test_missing_raw_raises(self):
        empty = Path(self._tmp.name) / "raw" / "empty"
        empty.mkdir(parents=True)
        with self.assertRaises(FileNotFoundError):
            curate_coal_mining_ppi.curate(raw_dir=empty)


if __name__ == "__main__":
    unittest.main()
