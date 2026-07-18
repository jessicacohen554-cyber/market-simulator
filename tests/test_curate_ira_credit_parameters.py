"""Tests for the ira-credit-parameters intake on a tiny synthetic fixture.

Writes a minimal 45U/45Y/48E-shaped CSV into a tmp raw tree, runs ``curate``,
and asserts the written Parquet is schema-valid and correctly shaped.
CLEAN_DIR is redirected to a tmp dir so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_ira_credit_parameters as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_CSV = """statute_section,parameter,value,value_type,unit,notes,source_doc,source_page
45U,base_credit_rate,0.3,numeric,cents_per_kwh,,26 USC 45U,45U(a)
45U,credit_end_date,2032-12-31,date,date,,26 USC 45U,45U(e)
48E,storage_wind_solar_exemption,true,boolean,boolean,,OBBBA,wind/solar termination
"""


def _write_fixture(raw_root: Path, csv: str = _CSV) -> None:
    d = curate_mod.raw_csv_path(raw_root).parent
    d.mkdir(parents=True, exist_ok=True)
    curate_mod.raw_csv_path(raw_root).write_text(csv)


class TestCurateIraCreditParameters(unittest.TestCase):
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
        self.assertEqual(schema.datatype, "ira-credit-parameters")
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 3)

        rate = df[
            (df["statute_section"] == "45U") & (df["parameter"] == "base_credit_rate")
        ]
        self.assertEqual(rate["value"].iloc[0], "0.3")
        self.assertEqual(rate["value_type"].iloc[0], "numeric")

        boolean_row = df[df["parameter"] == "storage_wind_solar_exemption"]
        self.assertEqual(boolean_row["value"].iloc[0], "true")
        self.assertEqual(boolean_row["value_type"].iloc[0], "boolean")

    def test_skips_when_no_raw_csv(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_unknown_section_rejected(self) -> None:
        bad = "statute_section,parameter,value,value_type,unit,notes,source_doc,source_page\n"
        bad += "48,itc_rate,30,numeric,percent,,doc,p\n"
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)

    def test_duplicate_key_rejected(self) -> None:
        bad = (
            _CSV
            + "45U,base_credit_rate,0.35,numeric,cents_per_kwh,,26 USC 45U,45U(a)\n"
        )
        _write_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_mod.curate(raw_root=self.raw_root)
