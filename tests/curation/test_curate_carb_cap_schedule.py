"""Tests for the carb-cap-schedule intake on a tiny synthetic fixture.

Writes a minimal CARB schedule CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and correctly shaped. CLEAN_DIR is
redirected to a tmp dir so it never touches the real tree. Also covers the
skip-empty path and the holdout-year quarantine guard (rule 22).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_carb_cap_schedule as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# Budget + floor-price rows across a backcast and a forward year. Illustrative
# values (a fixture, not the authoritative schedule).
_CSV = """budget_year,metric,value,unit,source_doc,source_page
2023,allowance_budget,307.7,mmt_co2e,CARB Reg 17 CCR 95841,95841
2023,auction_reserve_price,22.21,usd_per_tonne,CARB Auction Reserve Notice,1
2027,auction_reserve_price,29.40,usd_per_tonne,CARB Reg 17 CCR 95911,95911(c)
"""


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateCarbCapSchedule(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_schema_valid_and_values_round_trip(self) -> None:
        _write_fixture(self.raw_root)
        written = curate_mod.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "carb-cap-schedule")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 3)
        floor = df[
            (df["budget_year"] == 2023) & (df["metric"] == "auction_reserve_price")
        ]
        self.assertEqual(floor["value"].iloc[0], 22.21)
        self.assertEqual(floor["unit"].iloc[0], "usd_per_tonne")

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_quarantined_year_rejected(self) -> None:
        bad = _CSV + "2022,allowance_budget,320.0,mmt_co2e,doc,p\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_unknown_unit_rejected(self) -> None:
        bad = "budget_year,metric,value,unit,source_doc,source_page\n"
        bad += "2024,auction_reserve_price,25.0,usd_per_short_ton,doc,p\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)


if __name__ == "__main__":
    unittest.main()
