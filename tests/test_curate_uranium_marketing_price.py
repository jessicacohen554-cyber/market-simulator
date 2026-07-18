"""Tests for the uranium-marketing-price intake on a tiny synthetic fixture.

Writes a minimal EIA UMAR-shaped CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and correctly shaped. CLEAN_DIR is
redirected to a tmp dir so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_uranium_marketing_price as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_CSV = """metric,delivery_year,value,unit,source_doc,source_page
total_purchased_quantity,2024,55.9,million_lb_u3o8e,EIA 2024 Uranium Marketing Annual Report,Table S1a
total_purchased_price,2024,52.71,usd_per_lb_u3o8e,EIA 2024 Uranium Marketing Annual Report,Table S1b
enrichment_services_price,2024,97.66,usd_per_swu,EIA 2024 Uranium Marketing Annual Report,Table S2
"""


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateUraniumMarketingPrice(unittest.TestCase):
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
        self.assertEqual(schema.datatype, "uranium-marketing-price")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 3)
        price = df[df["metric"] == "total_purchased_price"]
        self.assertEqual(price["value"].iloc[0], 52.71)
        self.assertEqual(price["unit"].iloc[0], "usd_per_lb_u3o8e")

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_unknown_metric_rejected(self) -> None:
        bad = "metric,delivery_year,value,unit,source_doc,source_page\n"
        bad += "bogus_metric,2024,1.0,usd_per_lb_u3o8e,doc,p\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_duplicate_key_rejected(self) -> None:
        bad = _CSV + (
            "total_purchased_price,2024,99.0,usd_per_lb_u3o8e,"
            "EIA 2024 Uranium Marketing Annual Report,Table S1b\n"
        )
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)
