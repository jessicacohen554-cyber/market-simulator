"""Tests for the nrel-atb intake on a tiny synthetic fixture.

Writes a minimal ATB-shaped CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and correctly shaped. CLEAN_DIR is
redirected to a tmp dir so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_nrel_atb as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_HEADER = (
    "atb_year,technology,techdetail,display_name,core_metric_parameter,"
    "core_metric_case,tax_credit_case,scenario,default,"
    "core_metric_variable,value\n"
)
_CSV = _HEADER + (
    "2024,LandbasedWind,Class4,Land-Based Wind - Class 4,CAPEX,Market,PTC,"
    "Moderate,1,2030,1407.953224\n"
    "2024,LandbasedWind,Class4,Land-Based Wind - Class 4,Fixed O&M,Market,"
    "PTC,Moderate,1,2030,28.5\n"
    "2024,Nuclear,Nuclear - Small,Nuclear - Small,CAPEX,Market,ITC,Moderate,"
    "0,2030,9650.000677\n"
)


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateNrelAtb(unittest.TestCase):
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
        self.assertEqual(schema.datatype, "nrel-atb")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 3)

        capex = df[(df["technology"] == "LandbasedWind") & (df["parameter"] == "CAPEX")]
        self.assertEqual(capex["value"].iloc[0], 1407.953224)
        self.assertEqual(capex["unit"].iloc[0], "2022 $/kW")
        self.assertEqual(capex["cost_case"].iloc[0], "Moderate")
        self.assertTrue(bool(capex["is_default_class"].iloc[0]))

        smr = df[df["techdetail"] == "Nuclear - Small"]
        self.assertFalse(bool(smr["is_default_class"].iloc[0]))

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_unmapped_parameter_rejected(self) -> None:
        bad = _HEADER
        bad += (
            "2024,LandbasedWind,Class4,Land-Based Wind - Class 4,WACC Real,"
            "Market,PTC,Moderate,1,2030,0.05\n"
        )
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_rd_financial_case_rejected(self) -> None:
        bad = _HEADER
        bad += (
            "2024,LandbasedWind,Class4,Land-Based Wind - Class 4,CAPEX,R&D,"
            "PTC,Moderate,1,2030,1400.0\n"
        )
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)


if __name__ == "__main__":
    unittest.main()
