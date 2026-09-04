"""Tests for the ra-import-allocations intake on a tiny synthetic fixture.

Writes minimal CAISO "Holders of Import Capability" workbooks into a tmp raw
tree — one with text-stamped windows (the 2023/2025 layout), one with Excel
datetimes (the 2024 layout) — runs ``curate``, and asserts the written Parquet
is schema-valid, per-year partitioned, and that the tidy checks refuse a
duplicate holding and a non-positive MW. ``CLEAN_DIR`` is redirected to a tmp
dir by :class:`tests.helpers.base.CleanDirTestCase`. Trivial case first (one
row), then the two-layout fixture.
"""

from __future__ import annotations

import unittest

import pandas as pd

from scripts.data import curate_ra_import_allocations as curate_ria
from scripts.lib import ra_import_allocations as ria
from scripts.lib.ra_import_allocations import caiso as ria_caiso
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import CleanDirTestCase


def _holders(rows, text_dates: bool) -> pd.DataFrame:
    df = pd.DataFrame(
        rows, columns=["LSE", "BRANCHGROUP", "ALLOCATION", "START_DT", "END_DT"]
    )
    if not text_dates:
        df["START_DT"] = pd.to_datetime(df["START_DT"], format="%m/%d/%Y %H:%M:%S")
        df["END_DT"] = pd.to_datetime(df["END_DT"], format="%m/%d/%Y %H:%M:%S")
    return df


class TestCurateRaImportAllocations(CleanDirTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.raw_root = self.tmp_path / "raw"
        self.drop = self.raw_root / ria_caiso.RAW_SUBDIR
        self.drop.mkdir(parents=True)

    def test_trivial_one_row(self) -> None:
        _holders(
            [
                (
                    "LPGE",
                    "PALOVRDE_ITC",
                    100.0,
                    "01/01/2023 00:00:00",
                    "12/31/2023 23:59:59",
                )
            ],
            text_dates=True,
        ).to_excel(self.drop / "2023-holders-of-import-capability.xlsx", index=False)
        written = curate_ria.curate(raw_root=self.raw_root, isos=["CAISO"])
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 1)
        self.assertEqual(df.loc[0, "delivery_year"], "2023")
        self.assertEqual(df.loc[0, "allocation_mw"], 100.0)
        self.assertEqual(
            pd.Timestamp(df.loc[0, "start_date"]), pd.Timestamp("2023-01-01")
        )

    def test_two_layouts_two_partitions(self) -> None:
        _holders(
            [
                (
                    "LPGE",
                    "MALIN500_ISL",
                    500.0,
                    "01/01/2023 00:00:00",
                    "12/31/2023 23:59:59",
                ),
                (
                    "LSCE",
                    "PALOVRDE_ITC",
                    700.5,
                    "01/01/2023 00:00:00",
                    "12/31/2023 23:59:59",
                ),
            ],
            text_dates=True,
        ).to_excel(self.drop / "2023-holders-of-import-capability.xlsx", index=False)
        _holders(
            [("LSCE", "NOB_ITC", 300.0, "01/01/2024 00:00:00", "12/31/2024 23:59:59")],
            text_dates=False,
        ).to_excel(self.drop / "2024-holders-of-import-capability.xlsx", index=False)
        # An unrelated companion workbook must be ignored by the glob.
        pd.DataFrame(
            {"MONTH": [5], "SCID/BG": ["LPGE"], "USED_ALL_CAPABILITY": ["Yes"]}
        ).to_excel(
            self.drop
            / "2023-import-capability-used-on-annual-resource-adequacy-plans.xlsx",
            index=False,
        )
        written = curate_ria.curate(raw_root=self.raw_root, isos=["CAISO"])
        self.assertEqual(len(written), 2)
        frames = [pd.read_parquet(p) for p in written]
        for p in written:
            validate_clean(p)
        years = sorted(f["delivery_year"].iloc[0] for f in frames)
        self.assertEqual(years, ["2023", "2024"])
        y23 = next(f for f in frames if f["delivery_year"].iloc[0] == "2023")
        self.assertAlmostEqual(y23["allocation_mw"].sum(), 1200.5)
        self.assertEqual(ria_caiso.years(self.raw_root), [2023, 2024])

    def test_tidy_checks_refuse_duplicate_and_nonpositive(self) -> None:
        dup = _holders(
            [
                ("LPGE", "NOB_ITC", 10.0, "01/01/2023 00:00:00", "12/31/2023 23:59:59"),
                ("LPGE", "NOB_ITC", 10.0, "01/01/2023 00:00:00", "12/31/2023 23:59:59"),
            ],
            text_dates=True,
        )
        dup.to_excel(self.drop / "2023-holders-of-import-capability.xlsx", index=False)
        with self.assertRaises(ValueError):
            ria.parse_iso("CAISO", self.raw_root)
        _holders(
            [("LPGE", "NOB_ITC", 0.0, "01/01/2023 00:00:00", "12/31/2023 23:59:59")],
            text_dates=True,
        ).to_excel(self.drop / "2023-holders-of-import-capability.xlsx", index=False)
        with self.assertRaises(ValueError):
            ria.parse_iso("CAISO", self.raw_root)


if __name__ == "__main__":
    unittest.main()
