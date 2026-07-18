"""Tests for the CAISO capacity-deliverability intake on the real raw CSV.

Unlike the PJM fixture test (``tests/test_curate_capacity_deliverability.py``),
this copies the actual canonical
``data/raw/capacity-deliverability/caiso/caiso.csv`` into a tmp raw tree (the
retrieval CSV already carries canonical column values, so no synthetic
fixture is needed) and runs ``curate`` against it. CLEAN_DIR is redirected to
a tmp dir so the run never touches the real clean tree. Asserts the written
Parquet is schema-valid, mixed ``area_type`` survives the parse (LCR rows
``local_area``, MIC rows ``branch_group``, the PRM row ``rto``), and
``delivery_year`` is a calendar year.
"""

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_deliverability as curate_cd
from scripts.lib import capacity_deliverability as cd
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean, paths as clean_paths

_REAL_CSV = clean_paths.RAW_DIR / "capacity-deliverability" / "caiso" / "caiso.csv"


class TestCurateCapacityDeliverabilityCaiso(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        d = cd.raw_dir_for("CAISO", self.raw_root)
        d.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_REAL_CSV, d / "caiso.csv")
        # Redirect CLEAN_DIR so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_caiso(self) -> pd.DataFrame:
        written = curate_cd.curate(raw_root=self.raw_root, isos=["CAISO"])
        self.assertEqual(len(written), 1, "expected one CAISO partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-deliverability")
        return pd.read_parquet(path)

    def test_schema_valid_and_partitioned_by_iso(self) -> None:
        df = self._curate_caiso()
        self.assertEqual(set(df["iso"]), {"CAISO"})
        self.assertEqual(list(df.columns), list(cd.CANONICAL_COLUMNS))
        # 138 original rows + 9 peak_load rows (LA Basin / San Diego-IV /
        # SP26 zonal x 2023-2025, the local-capacity constraint inputs).
        self.assertEqual(len(df), 147)

    def test_mixed_area_type_survives(self) -> None:
        df = self._curate_caiso()
        # LCR rows: local_area requirement.
        lcr = df[(df["area"] == "Humboldt") & (df["metric"] == "requirement")]
        self.assertFalse(lcr.empty)
        self.assertEqual(set(lcr["area_type"]), {"local_area"})
        # MIC rows: branch_group import_limit.
        mic = df[(df["area"] == "IPP-DC") & (df["metric"] == "import_limit")]
        self.assertFalse(mic.empty)
        self.assertEqual(set(mic["area_type"]), {"branch_group"})
        # PRM row: rto system_requirement.
        prm = df[(df["area"] == "CAISO") & (df["metric"] == "system_requirement")]
        self.assertFalse(prm.empty)
        self.assertEqual(set(prm["area_type"]), {"rto"})
        # peak_load rows: local_area for the two LCR pockets, zone for the
        # SP26 share denominator (local-capacity constraint inputs).
        pl = df[df["metric"] == "peak_load"]
        self.assertFalse(pl.empty)
        self.assertEqual(set(pl["area_type"]), {"local_area", "zone"})
        self.assertEqual(set(pl[pl["area_type"] == "zone"]["area"]), {"SP26"})
        self.assertEqual(
            set(df["area_type"]), {"local_area", "branch_group", "rto", "zone"}
        )

    def test_calendar_delivery_year(self) -> None:
        df = self._curate_caiso()
        years = set(df["delivery_year"])
        self.assertTrue(years)
        for year in years:
            self.assertRegex(year, r"^\d{4}$")

    def test_prm_row_carries_value_pu_not_value_mw(self) -> None:
        df = self._curate_caiso()
        prm = df[(df["area"] == "CAISO") & (df["metric"] == "system_requirement")]
        self.assertTrue(prm["value_pu"].notna().all())
        self.assertTrue(prm["value_mw"].isna().all())

    def test_caiso_registered(self) -> None:
        registry = cd.load_registry()
        self.assertIn("CAISO", registry)
        self.assertEqual(registry["CAISO"].default_area_type, "local_area")


if __name__ == "__main__":
    unittest.main()
