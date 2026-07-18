"""Tests for the RD-5 actuals-coverage gap-fix in build_capacity_actuals.py.

Trivial case first: a tiny fixture EIA-860 tree (1 plant/generator) plus a
tiny gap-fix CSV, redirecting the module's EIA_860_DIR/RETIRED_SHEET_GAP_FIX
constants to a tmp dir so the real repo data is never touched. Then a
loader-resolvability smoke test against the actual committed gap-fix file
(Indian Point 3 / Palisades).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import build_capacity_actuals as bca


def _write_plant_and_retired(eia_dir: Path) -> None:
    """One plant (BA=TEST) NOT in the gap-fix set, retired 2023."""
    eia_dir.mkdir(parents=True, exist_ok=True)
    plant = pd.DataFrame(
        {
            "Plant Code": [111],
            "Balancing Authority Code": ["TEST"],
        }
    )
    plant.to_parquet(eia_dir / "eia860_plant.parquet")
    retired = pd.DataFrame(
        {
            "Plant Code": [111],
            "Plant Name": ["Test Plant"],
            "Generator ID": ["1"],
            "Technology": ["Natural Gas Fired Combustion Turbine"],
            "Energy Source 1": ["NG"],
            "Prime Mover": ["GT"],
            "Nameplate Capacity (MW)": [50.0],
            "Retirement Month": ["6"],
            "Retirement Year": ["2023"],
            "State": ["TX"],
        }
    )
    retired.to_parquet(eia_dir / "eia860_generator_retired_and_canceled.parquet")
    empty_gens = pd.DataFrame(columns=["plant_id", "operating_year"])
    empty_gens.to_parquet(eia_dir / "eia860_generators.parquet")


def _write_gap_fix(path: Path, *, extra_row: bool = False) -> None:
    rows = (
        "plant_code,plant_name,generator_id,technology,energy_source_1,prime_mover,"
        "nameplate_capacity_mw,retirement_month,retirement_year,state,ba_code,source_vintage\n"
        "9001,Gap Plant,1,Nuclear,NUC,ST,900.0,4,2022,ZZ,TEST,vintage_2022/fixture\n"
    )
    if extra_row:
        # Outside the 2021-2025 WINDOW -- must be dropped.
        rows += (
            "9002,Old Plant,1,Coal,BIT,ST,300.0,1,2015,ZZ,TEST,vintage_2015/fixture\n"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# header comment line\n{rows}")


class TestActualsCoverageGapFix(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_eia_dir = bca.EIA_860_DIR
        self._orig_gap_fix = bca.RETIRED_SHEET_GAP_FIX
        bca.EIA_860_DIR = self.root / "eia-860"
        bca.RETIRED_SHEET_GAP_FIX = bca.EIA_860_DIR / "retired_sheet_coverage_gaps.csv"
        _write_plant_and_retired(bca.EIA_860_DIR)

    def tearDown(self) -> None:
        bca.EIA_860_DIR = self._orig_eia_dir
        bca.RETIRED_SHEET_GAP_FIX = self._orig_gap_fix
        self._tmp.cleanup()

    def test_gap_fix_absent_yields_empty_frame(self) -> None:
        self.assertTrue(bca.load_retired_sheet_gap_fix({"TEST"}).empty)

    def test_gap_fix_unioned_into_retirements(self) -> None:
        _write_gap_fix(bca.RETIRED_SHEET_GAP_FIX)
        df = bca.build_retirements({"TEST"})
        self.assertEqual(len(df), 2, "main-sheet row + gap-fix row")
        gap_row = df[df["plant_id"] == 9001].iloc[0]
        self.assertEqual(gap_row["fuel"], "nuclear")
        self.assertEqual(gap_row["mw"], 900.0)
        self.assertEqual(gap_row["year"], 2022)
        self.assertEqual(gap_row["unit_id"], "9001_1")

    def test_gap_fix_filtered_by_ba(self) -> None:
        _write_gap_fix(bca.RETIRED_SHEET_GAP_FIX)
        df = bca.build_retirements({"OTHER_BA"})
        self.assertTrue(df.empty, "gap-fix row's BA is TEST, not OTHER_BA")

    def test_gap_fix_filtered_by_window(self) -> None:
        _write_gap_fix(bca.RETIRED_SHEET_GAP_FIX, extra_row=True)
        df = bca.build_retirements({"TEST"})
        self.assertNotIn(
            9002, set(df["plant_id"]), "2015 retirement is outside the window"
        )

    def test_gap_fix_does_not_duplicate_existing_row(self) -> None:
        # Same plant/generator as the main sheet's own row (111_1) -- must not
        # be double-counted if a future gap-fix row happens to overlap.
        _write_gap_fix(bca.RETIRED_SHEET_GAP_FIX)
        (bca.RETIRED_SHEET_GAP_FIX).write_text(
            "# header\n"
            "plant_code,plant_name,generator_id,technology,energy_source_1,prime_mover,"
            "nameplate_capacity_mw,retirement_month,retirement_year,state,ba_code,source_vintage\n"
            "111,Test Plant,1,Natural Gas Fired Combustion Turbine,NG,GT,50.0,6,2023,TX,TEST,dup\n"
        )
        df = bca.build_retirements({"TEST"})
        self.assertEqual(
            len(df), 1, "duplicate (plant_id, unit_id) must not double-count"
        )


class TestCommittedGapFixFileResolvability(unittest.TestCase):
    """Loader-resolvability smoke test against the real committed gap-fix file."""

    def test_committed_file_loads_and_covers_expected_plants(self) -> None:
        self.assertTrue(
            bca.RETIRED_SHEET_GAP_FIX.is_file(),
            f"expected {bca.RETIRED_SHEET_GAP_FIX} to exist",
        )
        df = bca.load_retired_sheet_gap_fix({"NYIS", "MISO"})
        self.assertEqual(set(df["plant_id"]), {8907, 1715})
        ip3 = df[df["plant_id"] == 8907].iloc[0]
        self.assertEqual(ip3["fuel"], "nuclear")
        self.assertEqual(ip3["year"], 2021)
        palisades = df[df["plant_id"] == 1715].iloc[0]
        self.assertEqual(palisades["fuel"], "nuclear")
        self.assertEqual(palisades["year"], 2022)

    def test_committed_file_scoped_by_ba(self) -> None:
        df = bca.load_retired_sheet_gap_fix({"NYIS"})
        self.assertEqual(set(df["plant_id"]), {8907})


if __name__ == "__main__":
    unittest.main()
