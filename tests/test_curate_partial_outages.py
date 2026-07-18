"""Round-trip tests for partial-outages curation
(scripts/data/curate_partial_outages.py).

Builds a tiny synthetic ``campd-partial-outages.csv`` fixture, runs
``curate``, and asserts the written Parquet is schema-valid, ``iso`` is
stamped, and the derate-window rows match the source CSV.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_partial_outages as cpo
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _write_partial_outages(path: Path) -> None:
    pd.DataFrame(
        [
            {
                "oris_code": 298,
                "plant_name": "Limestone",
                "plant_group": "COAL",
                "year": 2023,
                "outage_start": "2023-01-21",
                "outage_stop": "2023-03-21",
                "derate_factor": 0.36,
            },
            {
                "oris_code": 298,
                "plant_name": "Limestone",
                "plant_group": "COAL",
                "year": 2024,
                "outage_start": "2024-02-01",
                "outage_stop": "2024-02-15",
                "derate_factor": 0.5,
            },
        ]
    ).to_csv(path, index=False)


class TestCuratePartialOutages(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_dir = root / "raw"
        self.raw_dir.mkdir(parents=True)

        _write_partial_outages(self.raw_dir / "campd-partial-outages.csv")

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid(self):
        written = cpo.curate(raw_dir=self.raw_dir)
        self.assertEqual(set(written), {"ERCOT"})
        path = written["ERCOT"]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "partial-outages")
        self.assertIn("ERCOT", path.parts)

    def test_rows_match_source(self):
        written = cpo.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(written["ERCOT"])

        self.assertEqual(len(df), 2)
        self.assertTrue((df["iso"] == "ERCOT").all())
        self.assertTrue((df["plant_id"] == 298).all())

        row_2023 = df[df["year"] == 2023].iloc[0]
        self.assertAlmostEqual(row_2023["derate_factor"], 0.36)
        self.assertEqual(
            pd.Timestamp(row_2023["outage_start"]), pd.Timestamp("2023-01-21")
        )
        self.assertEqual(
            pd.Timestamp(row_2023["outage_stop"]), pd.Timestamp("2023-03-21")
        )

    def test_idempotent_rerun(self):
        first = cpo.curate(raw_dir=self.raw_dir)
        second = cpo.curate(raw_dir=self.raw_dir)
        pd.testing.assert_frame_equal(
            pd.read_parquet(first["ERCOT"]), pd.read_parquet(second["ERCOT"])
        )


if __name__ == "__main__":
    unittest.main()
