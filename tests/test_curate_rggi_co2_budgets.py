"""Tests for the rggi-co2-budgets intake on a tiny synthetic fixture.

Writes a minimal RGGI budget CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and correctly shaped. CLEAN_DIR is
redirected to a tmp dir so it never touches the real tree. Also covers the
skip-empty path and the holdout-year quarantine guard (rule 22).
"""

import unittest
from pathlib import Path

import pandas as pd

from scripts.data import curate_rggi_co2_budgets as curate_mod
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import CleanDirTestCase

# Regional + per-state budget and a floor-price row; deliberately mixed years
# and metrics. Illustrative values (a fixture, not the authoritative schedule).
_CSV = """state,budget_year,metric,value,unit,source_doc,source_page
RGGI,2023,allowance_budget,88400000,short_tons,RGGI Allowance Distribution,Table 1
NY,2023,allowance_budget,44100000,short_tons,RGGI Allowance Distribution,Table 1
RGGI,2027,ccr_trigger_price,16.53,usd_per_short_ton,RGGI 2017 Model Rule,5.3
RGGI,2027,minimum_reserve_price,3.09,usd_per_short_ton,RGGI 2017 Model Rule,5.3
"""


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateRggiCo2Budgets(CleanDirTestCase):
    def setUp(self) -> None:
        super().setUp()  # redirects paths.CLEAN_DIR to self.clean_dir
        self.raw_root = self.tmp_path / "raw"
        self.raw_root.mkdir(parents=True)

    def test_schema_valid_and_values_round_trip(self) -> None:
        _write_fixture(self.raw_root)
        written = curate_mod.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "rggi-co2-budgets")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 4)
        # State upper-cased, key columns present, a known value survives.
        budget = df[(df["state"] == "NY") & (df["metric"] == "allowance_budget")]
        self.assertEqual(budget["value"].iloc[0], 44100000.0)
        self.assertEqual(budget["unit"].iloc[0], "short_tons")

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_quarantined_year_rejected(self) -> None:
        bad = _CSV + ("RGGI,2026,allowance_budget,80000000,short_tons,doc,p\n")
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_unknown_metric_rejected(self) -> None:
        bad = "state,budget_year,metric,value,unit,source_doc,source_page\n"
        bad += "NY,2024,bogus_metric,1.0,short_tons,doc,p\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)


if __name__ == "__main__":
    unittest.main()
