"""Tests for the MISO capacity-deliverability intake against the real fixture.

Copies the committed ``data/raw/capacity-deliverability/miso/miso.csv`` into a
tmp raw tree (CLEAN_DIR redirected, as in ``test_curate_capacity_deliverability.py``)
and runs ``curate`` end to end. This proves the normalized CSV — area labels
"LRZ 1".."LRZ 10", area_type lrz/rto, lowercase season, "2023/2024"-style
delivery_year, canonical metric names — is actually in-vocab and round-trips
through ``validate_clean``, not just eyeballed.
"""

import shutil
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_capacity_deliverability as curate_cd
from scripts.lib import capacity_deliverability as cd
from scripts.lib.clean_io import paths, validate_clean

_REAL_MISO_CSV = paths.REPO_ROOT / "data/raw/capacity-deliverability/miso/miso.csv"


class TestCapacityDeliverabilityMiso(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = paths.CLEAN_DIR
        paths.CLEAN_DIR = root / "clean"

        d = cd.raw_dir_for("MISO", self.raw_root)
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy(_REAL_MISO_CSV, d / "miso.csv")

    def tearDown(self) -> None:
        paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_miso(self) -> pd.DataFrame:
        written = curate_cd.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(len(written), 1, "expected one MISO partition")
        path = written[0]
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-deliverability")
        return pd.read_parquet(path)

    def test_validate_clean_passes(self) -> None:
        # Proves area_type/season/metric are all in-vocab post-normalization
        # (validate_tidy runs inside parse_iso; validate_clean re-checks on disk).
        self._curate_miso()

    def test_all_four_seasons_present(self) -> None:
        df = self._curate_miso()
        self.assertEqual(set(df["season"]), {"summer", "fall", "winter", "spring"})

    def test_requirement_row_carries_value_pu(self) -> None:
        df = self._curate_miso()
        requirement = df[df["metric"] == "requirement"]
        self.assertFalse(requirement.empty)
        self.assertTrue((requirement["value_pu"].notna()).all())

    def test_rto_system_row_exists(self) -> None:
        df = self._curate_miso()
        rto_rows = df[df["area_type"] == "rto"]
        self.assertFalse(rto_rows.empty)
        self.assertEqual(set(rto_rows["area"]), {"RTO", "North", "South"})

    def test_miso_registered(self) -> None:
        registry = cd.load_registry()
        self.assertIn("MISO", registry)
        self.assertEqual(registry["MISO"].default_area_type, "lrz")


if __name__ == "__main__":
    unittest.main()
