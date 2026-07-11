"""Tests for the carbon-auction-results intake on a tiny synthetic fixture.

Writes a minimal RGGI+CARB auction-results CSV into a tmp raw tree, runs
``curate``, and asserts the written Parquet is schema-valid and correctly
shaped. CLEAN_DIR is redirected to a tmp dir so it never touches the real
tree. Also covers the skip-empty path and the holdout-year quarantine guard
(rule 22).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_carbon_auction_results as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_HEADER = (
    "program,year,quarter,auction_date,auction_number,clearing_price,"
    "price_unit,allowances_sold,allowances_offered,source_doc,source_page\n"
)
_CSV = _HEADER + (
    "RGGI,2025,4,2025-12-03,70,26.73,usd_per_short_ton,15230235,15230235,"
    "RGGI Inc,https://www.rggi.org/auctions/auction-results/prices-volumes\n"
    "CARB,2025,2,2025-05-29,43,25.87,usd_per_tonne,,,"
    "CARB press release,https://ww2.arb.ca.gov/news/43rd\n"
    "CARB,2024,2,,,37.02,usd_per_tonne,,,"
    "EIA Today in Energy,https://www.eia.gov/todayinenergy/detail.php?id=62644\n"
)


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateCarbonAuctionResults(unittest.TestCase):
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
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "carbon-auction-results")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 3)

        rggi = df[df["program"] == "RGGI"]
        self.assertEqual(rggi["clearing_price"].iloc[0], 26.73)
        self.assertEqual(rggi["allowances_sold"].iloc[0], 15230235.0)

        carb_no_number = df[(df["program"] == "CARB") & (df["year"] == 2024)]
        self.assertTrue(pd.isna(carb_no_number["auction_number"].iloc[0]))

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_quarantined_year_rejected(self) -> None:
        bad = _CSV + ("RGGI,2026,1,2026-03-11,71,24.99,usd_per_short_ton,,,doc,url\n")
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_unknown_program_rejected(self) -> None:
        bad = _HEADER
        bad += "WCI,2024,1,,,20.0,usd_per_tonne,,,doc,url\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_invalid_quarter_rejected(self) -> None:
        bad = _HEADER
        bad += "RGGI,2024,5,,,20.0,usd_per_short_ton,,,doc,url\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)
