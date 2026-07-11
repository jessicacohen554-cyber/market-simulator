"""Tests for the eia-aeo-fuel-prices intake on a tiny synthetic fixture.

Writes a minimal AEO fuel-price CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and correctly shaped. CLEAN_DIR is
redirected to a tmp dir so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_eia_aeo_fuel_prices as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_CSV = (
    "fuel,metric,region,scenario,scenario_name,year,value,unit,series_id,"
    "table_id,table_name\n"
    "gas,henry_hub_spot,usa,ref2025,Reference case,2026,2.737246,"
    "2024 $/MMBtu,prce_hhp_NA_NA_ng_NA_usa_y13dlrpmmbtu,13,"
    '"Table 13.  Natural Gas Supply, Disposition, and Prices"\n'
    "gas,henry_hub_spot,usa,highogs,High Oil and Gas Supply,2026,2.108019,"
    "2024 $/MMBtu,prce_hhp_NA_NA_ng_NA_usa_y13dlrpmmbtu,13,"
    '"Table 13.  Natural Gas Supply, Disposition, and Prices"\n'
    "coal,minemouth_by_region,appalachia,ref2025,Reference case,2026,45.12,"
    "2024 $/st,prce_NA_NA_NA_cl_mnmth_aplch_y13dlrptn,94,"
    '"Table 65.  Coal Production and Minemouth Prices by Region"\n'
)


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateEiaAeoFuelPrices(unittest.TestCase):
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
        self.assertEqual(schema.datatype, "eia-aeo-fuel-prices")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 3)
        hh = df[(df["metric"] == "henry_hub_spot") & (df["scenario"] == "ref2025")]
        self.assertEqual(hh["value"].iloc[0], 2.737246)
        self.assertEqual(hh["unit"].iloc[0], "2024 $/MMBtu")

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_unknown_fuel_rejected(self) -> None:
        bad = _CSV.splitlines()[0] + "\n"
        bad += (
            "nuclear,henry_hub_spot,usa,ref2025,Reference case,2026,1.0,"
            "2024 $/MMBtu,bogus,13,bogus table\n"
        )
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_duplicate_key_rejected(self) -> None:
        bad = _CSV + (
            "gas,henry_hub_spot,usa,ref2025,Reference case,2026,9.99,"
            "2024 $/MMBtu,prce_hhp_NA_NA_ng_NA_usa_y13dlrpmmbtu,13,"
            "Table 13.  Natural Gas Supply, Disposition, and Prices\n"
        )
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)


if __name__ == "__main__":
    unittest.main()
