"""Tests for build_capacity_actuals.py — the capacity-hindcast scoring target.

Two things are covered:

* the **RD-5 actuals-coverage gap-fix** (the curated override for plants the
  current EIA-860 release has dropped or un-retired), and
* the **FFR-7A physical-exit dating rule** (owner decision D-21(b)) that dates
  a retirement at the status transition to OS/RE rather than at the reported
  paper date, and gates units already out of service at the fleet vintage.

Trivial case first: the exit-dating rule is exercised as a pure function on
hand-written status series, then on a tiny fixture EIA-860 *release tree*
(three releases, four generators, one pathology each), redirecting the
module's EIA_860_DIR/RETIRED_SHEET_GAP_FIX constants to a tmp dir so the real
repo data is never touched. Then smoke tests against the committed artifacts:
the gap-fix file (Indian Point 3 / Palisades) and the regenerated ERCOT/NEISO
targets (J T Deely out, V H Braunig and Sandy Creek in, Potter Station out).
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


class TestPhysicalExitYear(unittest.TestCase):
    """The FFR-7A dating rule, on hand-written status series (trivial first)."""

    def test_still_operating_is_not_an_exit(self) -> None:
        self.assertIsNone(
            bca.physical_exit_year({2020: "OP", 2021: "OP", 2022: "OP"}, None)
        )

    def test_standby_and_returning_are_not_exits(self) -> None:
        # SB and OA are available capacity by EIA's own definition.
        self.assertIsNone(bca.physical_exit_year({2020: "OP", 2021: "SB"}, None))
        self.assertIsNone(bca.physical_exit_year({2020: "OP", 2021: "OA"}, None))

    def test_clean_retirement_takes_the_reported_year(self) -> None:
        # The normal case: the release that reports RE is published for a year
        # at or after the retirement, so the reported date wins.
        self.assertEqual(
            bca.physical_exit_year({2022: "OP", 2025: "RE"}, 2023),
            2023,
        )

    def test_paper_date_is_corrected_down_to_the_status_run(self) -> None:
        # J T Deely: OS from 2018 on, EIA Retirement Year 2023.
        deely = {y: "OS" for y in range(2018, 2023)} | {2025: "RE"}
        self.assertEqual(bca.physical_exit_year(deely, 2023), 2018)

    def test_mothball_without_a_reported_date_dates_at_the_transition(self) -> None:
        # V H Braunig / Sandy Creek: OP through 2024, OS in the 2025 release,
        # never moved to the retired sheet, so no reported year exists at all.
        braunig = {y: "OP" for y in range(2018, 2025)} | {2025: "OS"}
        self.assertEqual(bca.physical_exit_year(braunig, None), 2025)

    def test_return_to_service_resets_the_run(self) -> None:
        # Out, back, out again: the exit is the FINAL run's start, not the first.
        self.assertEqual(
            bca.physical_exit_year(
                {2018: "OS", 2019: "OS", 2020: "OP", 2021: "OP", 2022: "OS"}, None
            ),
            2022,
        )

    def test_reversed_retirement_is_not_an_exit(self) -> None:
        # Palisades: RE in an older release, back on the operable sheet since.
        self.assertIsNone(
            bca.physical_exit_year({2021: "OP", 2022: "RE", 2025: "OP"}, 2022)
        )

    def test_no_status_history_falls_back_to_the_reported_year(self) -> None:
        self.assertEqual(bca.physical_exit_year({}, 2024), 2024)


def _write_release_tree(eia_dir: Path) -> None:
    """A 3-release fixture tree (2020, 2021, current) with one unit per case.

    * ``500_A`` — clean retirement: OP, OP, then RE dated 2023.
    * ``500_B`` — J T Deely shape: OS from 2020, papered RE 2023.
    * ``500_C`` — V H Braunig shape: OP, OP, OS in the current release.
    * ``500_D`` — vintage-gate shape: OS at 2020, back OP in 2021, OS again.
    """

    def gens(rows: list[tuple[str, str, int]], cod: int = 1990) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "plant_id": [500] * len(rows),
                "generator_id": [r[0] for r in rows],
                "plant_name": ["Fixture"] * len(rows),
                "state": ["ZZ"] * len(rows),
                "balancing_authority_code": ["TEST"] * len(rows),
                "technology": ["Conventional Steam Coal"] * len(rows),
                "energy_source": ["BIT"] * len(rows),
                "prime_mover": ["ST"] * len(rows),
                "nameplate_capacity_mw": [float(r[2]) for r in rows],
                "operating_year": [cod] * len(rows),
                "status": [r[1] for r in rows],
            }
        )

    def retired(rows: list[tuple[str, int, int]]) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Plant Code": [500] * len(rows),
                "Plant Name": ["Fixture"] * len(rows),
                "Generator ID": [r[0] for r in rows],
                "Technology": ["Conventional Steam Coal"] * len(rows),
                "Energy Source 1": ["BIT"] * len(rows),
                "Prime Mover": ["ST"] * len(rows),
                "Nameplate Capacity (MW)": [float(r[2]) for r in rows],
                "Status": ["RE"] * len(rows),
                "Retirement Month": [1] * len(rows),
                "Retirement Year": [r[1] for r in rows],
                "State": ["ZZ"] * len(rows),
            }
        )

    plant = pd.DataFrame({"Plant Code": [500], "Balancing Authority Code": ["TEST"]})
    for name, operable, retired_rows, cod in (
        (
            "vintage_2020",
            [("A", "OP", 100), ("B", "OS", 200), ("C", "OP", 300), ("D", "OS", 400)],
            [],
            1990,
        ),
        (
            "vintage_2021",
            [("A", "OP", 100), ("B", "OS", 200), ("C", "OP", 300), ("D", "OP", 400)],
            [],
            1990,
        ),
        (
            "",  # the current release — its reporting year is read from the COD
            [("C", "OS", 300), ("D", "OS", 400)],
            [("A", 2023, 100), ("B", 2023, 200)],
            2025,
        ),
    ):
        d = eia_dir / name if name else eia_dir
        d.mkdir(parents=True, exist_ok=True)
        plant.to_parquet(d / "eia860_plant.parquet")
        gens(operable, cod=cod).to_parquet(d / "eia860_generators.parquet")
        if retired_rows or not name:
            retired(retired_rows).to_parquet(
                d / "eia860_generator_retired_and_canceled.parquet"
            )


class TestPhysicalExitDatingOnFixtureTree(unittest.TestCase):
    """The dating rule + vintage gate end-to-end on a 3-release fixture tree."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_eia_dir = bca.EIA_860_DIR
        self._orig_gap_fix = bca.RETIRED_SHEET_GAP_FIX
        bca.EIA_860_DIR = Path(self._tmp.name) / "eia-860"
        bca.RETIRED_SHEET_GAP_FIX = bca.EIA_860_DIR / "absent.csv"
        _write_release_tree(bca.EIA_860_DIR)

    def tearDown(self) -> None:
        bca.EIA_860_DIR = self._orig_eia_dir
        bca.RETIRED_SHEET_GAP_FIX = self._orig_gap_fix
        self._tmp.cleanup()

    def test_release_series_is_ordered_and_dates_the_current_release(self) -> None:
        self.assertEqual([y for y, _ in bca.release_series()], [2020, 2021, 2025])

    def test_clean_retirement_survives_at_its_reported_year(self) -> None:
        df = bca.build_retirements({"TEST"}).set_index("unit_id")
        self.assertEqual(int(df.loc["500_A", "year"]), 2023)
        self.assertEqual(float(df.loc["500_A", "mw"]), 100.0)
        self.assertEqual(df.loc["500_A", "fuel"], "coal")

    def test_paper_dated_unit_leaves_the_target(self) -> None:
        # Out of service from the fleet vintage on: dated 2020, outside WINDOW.
        df = bca.build_retirements({"TEST"})
        self.assertNotIn("500_B", set(df["unit_id"]))

    def test_mothballed_unit_enters_the_target(self) -> None:
        df = bca.build_retirements({"TEST"}).set_index("unit_id")
        self.assertEqual(int(df.loc["500_C", "year"]), 2025)

    def test_vintage_gate_drops_a_unit_dead_at_the_fleet_vintage(self) -> None:
        audit: dict = {}
        df = bca.build_retirements({"TEST"}, audit=audit)
        self.assertNotIn("500_D", set(df["unit_id"]))
        excluded = {r["unit_id"]: r for r in audit["excluded"]}
        self.assertIn("500_D", excluded)
        self.assertIn("OS", excluded["500_D"]["reason"])

    def test_ungated_build_keeps_the_vintage_dead_unit(self) -> None:
        df = bca.build_retirements({"TEST"}, fleet_vintage=None).set_index("unit_id")
        self.assertEqual(int(df.loc["500_D", "year"]), 2025)

    def test_no_pathology_means_no_change(self) -> None:
        """An ISO with only clean RE rows is byte-identical to the old rule.

        The old builder emitted the current retired sheet's in-window rows
        verbatim. Restricted to the units that carry no OS history and no
        paper-date mismatch (here: ``500_A``), the new builder must produce
        exactly the same CSV body — the fix is inert where there is nothing to
        fix, which is what keeps it from silently re-writing clean rows.
        """
        legacy = pd.DataFrame(
            [
                {
                    "kind": "retirement",
                    "unit_id": "500_A",
                    "plant_id": 500,
                    "fuel": "coal",
                    "mw": 100.0,
                    "year": 2023,
                    "state": "ZZ",
                }
            ]
        )
        rebuilt = bca.build_retirements({"TEST"})
        rebuilt = rebuilt[rebuilt["unit_id"] == "500_A"].reset_index(drop=True)
        self.assertEqual(rebuilt.to_csv(index=False), legacy.to_csv(index=False))


class TestCommittedTargetStatusHygiene(unittest.TestCase):
    """Smoke tests on the regenerated committed targets (FFR-7A §2)."""

    @staticmethod
    def _target(iso: str) -> pd.DataFrame:
        df = pd.read_csv(bca.OUT_DIR / f"capacity_actuals_{iso}.csv", comment="#")
        return df[df["kind"] == "retirement"].set_index("unit_id")

    def test_deely_left_the_ercot_target(self) -> None:
        # Plant 6181, 932 MW coal, EIA status OS from 2018 on, papered 2023.
        ercot = self._target("ercot")
        self.assertNotIn("6181_1", ercot.index)
        self.assertNotIn("6181_2", ercot.index)

    def test_braunig_entered_the_ercot_target(self) -> None:
        # Plant 3612 units 1+2, 477 MW, OP through 2024 then OS in RY2025.
        ercot = self._target("ercot")
        for uid, mw in (("3612_1", 225.0), ("3612_2", 252.0)):
            self.assertIn(uid, ercot.index)
            self.assertEqual(int(ercot.loc[uid, "year"]), 2025)
            self.assertEqual(float(ercot.loc[uid, "mw"]), mw)

    def test_sandy_creek_entered_the_ercot_target(self) -> None:
        # Plant 56611, 1008 MW coal, same OS-in-RY2025 transition.
        ercot = self._target("ercot")
        self.assertIn("56611_S01", ercot.index)
        self.assertEqual(int(ercot.loc["56611_S01", "year"]), 2025)

    def test_potter_station_left_the_neiso_target(self) -> None:
        # Plant 1660 CC2/CC3: OS from 2020, papered 2024 — the Deely shape.
        neiso = self._target("neiso")
        self.assertNotIn("1660_CC2", neiso.index)
        self.assertNotIn("1660_CC3", neiso.index)

    def test_reversed_retirement_is_still_carried_by_the_gap_fix(self) -> None:
        # Palisades restarted, so the status rule declines to call it an exit;
        # the curated RD-5 override keeps it for RC-0B to adjudicate.
        self.assertIn("1715_1", self._target("miso").index)

    def test_no_target_carries_an_out_of_window_year(self) -> None:
        for iso in ("ercot", "pjm", "miso", "nyiso", "neiso"):
            years = set(self._target(iso)["year"].astype(int))
            self.assertTrue(
                years <= set(bca.WINDOW), f"{iso} has out-of-window years {years}"
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
