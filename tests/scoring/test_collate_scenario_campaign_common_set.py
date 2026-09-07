"""The system-scope delta is computed on the COMMON ISO set (lane SCN-FIX1).

The defect these tests pin, routed by SCN-WS5A-LOAD
(``docs/handoffs/STATUS-scn-ws5a-load-2026-09-06.md``, "Routed defect"):
``collate_scenario_campaign.build_delta_table`` computed the
``six-ISO modeled system`` delta as *(sum over the case's ISOs)* minus *(sum
over the reference case's ISOs)* with nothing restricting the two to the same
system. A case with a legitimately degenerate arm — PJM and NEISO ship
``LOAD-HI == LOAD-HI-ORGANIC`` byte-for-byte, so their ORGANIC arm is correctly
never solved — therefore differenced against a wider reference by exactly the
missing ISOs' levels.

Two layers, trivial first per CLAUDE.md's testing pattern:

  1. :class:`TestCommonSetOnFixtures` — a fabricated three-ISO campaign whose
     case arm covers two, with every number hand-computed.
  2. :class:`TestScnCampaignLoadRegression` — the measured numbers from the
     STATUS doc, reproduced from the committed
     ``results/scn-campaign-load-2026-09-06/`` artifacts. No LP, no solve.
"""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from scripts import collate_scenario_campaign as C

YEARS = (2026, 2027)

# A three-ISO REF against a two-ISO case, shaped like the real defect: the
# naive difference is +5.0 and the common-set answer is +15.0, the error being
# exactly NEISO's REF level.
LEVELS: dict[str, dict[str, dict[int, float]]] = {
    "REF": {
        "ERCOT": {2026: 100.0, 2027: 105.0},
        "NYISO": {2026: 20.0, 2027: 21.0},
        "NEISO": {2026: 10.0, 2027: 11.0},
    },
    "CASE": {
        "ERCOT": {2026: 110.0, 2027: 118.0},
        "NYISO": {2026: 25.0, 2027: 27.0},
    },
}
COMMON = ("ERCOT", "NYISO")


def _write_campaign(root: Path, levels: dict[str, dict[str, dict[int, float]]]) -> None:
    """Write a ``<root>/<iso>/<case>/full_horizon_summary.json`` tree."""
    for case, by_iso in levels.items():
        for iso, by_year in by_iso.items():
            case_dir = root / iso.lower() / case
            case_dir.mkdir(parents=True)
            (case_dir / "full_horizon_summary.json").write_text(
                json.dumps(
                    {
                        "iso": iso,
                        "cache_key": f"{iso.lower()}_{case}",
                        "run_dir": None,
                        "trajectory": [
                            {"year": y, "co2_mt": mt} for y, mt in by_year.items()
                        ],
                    }
                )
            )


def _deltas(root: Path, reference_case: str = "REF") -> pd.DataFrame:
    """Run the collation in-process and return the delta table."""
    summaries = C.discover_summaries(root)
    iso_frame = C.build_iso_frame(summaries)
    system_frame = C.build_system_frame(iso_frame)
    return C.build_delta_table(iso_frame, system_frame, reference_case)


class TestCommonSetOnFixtures(unittest.TestCase):
    """Hand-computed: REF covers three ISOs, CASE covers two."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "campaign"
        _write_campaign(self.root, LEVELS)
        self.deltas = _deltas(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _system(self, case: str, year: int) -> pd.Series:
        rows = self.deltas[
            (self.deltas["scope"] == C.SYSTEM_LABEL)
            & (self.deltas["case"] == case)
            & (self.deltas["year"] == year)
        ]
        self.assertEqual(len(rows), 1)
        return rows.iloc[0]

    def test_the_delta_is_the_hand_computed_common_set_answer(self):
        row = self._system("CASE", 2026)
        case_common = sum(LEVELS["CASE"][i][2026] for i in COMMON)  # 135.0
        ref_common = sum(LEVELS["REF"][i][2026] for i in COMMON)  # 120.0
        self.assertAlmostEqual(row["emissions_mt_delta"], 15.0, places=6)
        self.assertAlmostEqual(row["emissions_mt_delta"], case_common - ref_common)

    def test_the_naive_cross_system_difference_is_NOT_emitted(self):
        # What the pre-repair table produced: the case's own total minus the
        # reference's own total, over different systems.
        naive = sum(LEVELS["CASE"][i][2026] for i in LEVELS["CASE"]) - sum(
            LEVELS["REF"][i][2026] for i in LEVELS["REF"]
        )
        self.assertAlmostEqual(naive, 5.0, places=6)
        row = self._system("CASE", 2026)
        self.assertNotAlmostEqual(row["emissions_mt_delta"], naive, places=6)
        # The error the naive form carries is exactly the dropped ISO's level.
        self.assertAlmostEqual(
            row["emissions_mt_delta"] - naive, LEVELS["REF"]["NEISO"][2026], places=6
        )

    def test_the_row_is_labelled_with_the_intersection(self):
        row = self._system("CASE", 2026)
        self.assertEqual(row["delta_isos"], "ERCOT+NYISO")
        self.assertEqual(row["delta_n_isos"], 2)

    def test_a_strict_subset_says_so_in_its_own_column(self):
        row = self._system("CASE", 2026)
        self.assertNotEqual(row["delta_coverage"], C.COVERAGE_FULL)
        self.assertIn("COMMON-SET ONLY", row["delta_coverage"])
        self.assertIn("NEISO", row["delta_coverage"])
        self.assertIn("REF", row["delta_coverage"])

    def test_full_coverage_reads_full_and_differences_to_zero(self):
        row = self._system("REF", 2026)
        self.assertEqual(row["delta_coverage"], C.COVERAGE_FULL)
        self.assertEqual(row["delta_n_isos"], 3)
        self.assertAlmostEqual(row["emissions_mt_delta"], 0.0, places=6)

    def test_the_row_arithmetic_closes_within_the_row(self):
        # A reader who subtracts the two level columns must land on the delta.
        for _, row in self.deltas.iterrows():
            if math.isnan(row["emissions_mt_delta"]):
                continue
            self.assertAlmostEqual(
                row["emissions_mt"] - row["emissions_mt_ref"],
                row["emissions_mt_delta"],
                places=6,
                msg=f"{row['scope']} / {row['case']} / {row['year']}",
            )

    def test_the_system_delta_is_the_sum_of_the_common_isos_deltas(self):
        for year in YEARS:
            per_iso = self.deltas[
                (self.deltas["scope"].isin(COMMON))
                & (self.deltas["case"] == "CASE")
                & (self.deltas["year"] == year)
            ]["emissions_mt_delta"].sum()
            self.assertAlmostEqual(
                self._system("CASE", year)["emissions_mt_delta"], per_iso, places=6
            )

    def test_cumulative_runs_over_the_common_set_too(self):
        expected = sum(
            sum(LEVELS["CASE"][i][y] for i in COMMON)
            - sum(LEVELS["REF"][i][y] for i in COMMON)
            for y in YEARS
        )
        self.assertAlmostEqual(
            self._system("CASE", YEARS[-1])["cumulative_emissions_mt_delta"],
            expected,
            places=6,
        )

    def test_per_iso_rows_are_unaffected_and_carry_the_columns(self):
        ercot = self.deltas[
            (self.deltas["scope"] == "ERCOT")
            & (self.deltas["case"] == "CASE")
            & (self.deltas["year"] == 2026)
        ].iloc[0]
        self.assertAlmostEqual(ercot["emissions_mt_delta"], 10.0, places=6)
        self.assertEqual(ercot["delta_isos"], "ERCOT")
        self.assertEqual(ercot["delta_n_isos"], 1)
        self.assertEqual(ercot["delta_coverage"], C.COVERAGE_FULL)

    def test_an_iso_the_reference_lacks_gets_no_delta(self):
        neiso = self.deltas[self.deltas["scope"] == "NEISO"]
        # NEISO exists only in REF here, so it differences to zero against
        # itself and never against a case that does not carry it.
        self.assertEqual(set(neiso["case"]), {"REF"})

    def test_the_markdown_surfaces_the_coverage_columns(self):
        out_dir = self.root.parent / "rollup"
        C.main(
            [
                "--root",
                str(self.root),
                "--reference-case",
                "REF",
                "--out-dir",
                str(out_dir),
            ]
        )
        md = (out_dir / "campaign_report.md").read_text()
        self.assertIn("delta_isos", md)
        self.assertIn("delta_coverage", md)
        self.assertIn("COMMON-SET ONLY", md)


class TestNoCommonIso(unittest.TestCase):
    """No shared ISO at all must yield NaN, never a computable-looking zero."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "campaign"
        _write_campaign(
            self.root,
            {
                "REF": {"ERCOT": {2026: 100.0}},
                "CASE": {"MISO": {2026: 300.0}},
            },
        )
        self.deltas = _deltas(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_disjoint_coverage_emits_nan_and_says_why(self):
        row = self.deltas[
            (self.deltas["scope"] == C.SYSTEM_LABEL) & (self.deltas["case"] == "CASE")
        ].iloc[0]
        self.assertTrue(math.isnan(row["emissions_mt_delta"]))
        self.assertTrue(math.isnan(row["emissions_mt"]))
        self.assertEqual(row["delta_n_isos"], 0)
        self.assertIn("NO DELTA", row["delta_coverage"])


CAMPAIGN = (
    Path(__file__).resolve().parents[2] / "results" / "scn-campaign-load-2026-09-06"
)

# STATUS-scn-ws5a-load-2026-09-06.md, "Routed defect", measured on the three
# ISOs complete when it was written: the reported system-scope LOAD-HI-ORGANIC
# 2030 delta, the correct common-set answer, and the error between them.
STATUS_REPORTED_MT = 5.4620
STATUS_COMMON_SET_MT = 18.8300
STATUS_ERROR_MT = -13.368  # exactly NEISO's REF 2030 level
STATUS_ISOS = ("ERCOT", "NEISO", "NYISO")


# The class below reads the per-case ``full_horizon_summary.json`` files, which
# is what ``discover_summaries`` walks -- NOT the campaign directory as a whole.
# The guard used to test ``CAMPAIGN.is_dir()``, which stayed true after session
# SCN-WS5A-RESOLVE-{CAISO,MISO,ERCOT} deleted every per-case summary from the
# tree as "pre-fix slim artifacts" (commit c29f6107, 2026-09-07; the same lane
# deleted CAISO's at 7964a50f/0b5f38fb/cf279436 and MISO's at 7200af05). With the
# directory present and the summaries gone, ``discover_summaries`` returned zero
# rows and the five regression tests raised KeyError/IndexError on an empty
# frame instead of skipping -- a stale guard, not a defect in the repair it
# pins. The guard now names the artifact the class actually reads.
#
# SPP-38 did NOT re-point the class at the surviving committed rollup
# (``_rollup/campaign_emissions_by_iso.csv``, which is byte-for-byte the shape
# ``build_iso_frame`` returns and does still reproduce all three STATUS numbers
# -- 18.830 / 5.462 / 13.368): that rollup was last written 2026-09-06 16:35 UTC,
# BEFORE the RESOLVE lane's re-solves, so it is a superseded vintage, and
# ``test_the_repair_holds_over_the_whole_committed_tree`` no longer holds against
# it (CAISO and MISO ORGANIC legs landed after the STATUS doc, moving the
# whole-tree common-set delta 18.830 -> 101.967). Restoring the summaries or
# re-rolling ``_rollup`` is the SCN desk's call, not a test repair
# (docs/handoffs/FINDING-spp-38-2026-09-07.md §4).
_SUMMARIES = (
    sorted(CAMPAIGN.rglob("full_horizon_summary.json")) if CAMPAIGN.is_dir() else []
)


@unittest.skipUnless(
    _SUMMARIES,
    "campaign per-case full_horizon_summary.json artifacts not on disk "
    "(deleted by SCN-WS5A-RESOLVE at c29f6107; see the note above)",
)
class TestScnCampaignLoadRegression(unittest.TestCase):
    """Reproduce the routed defect's measured numbers from committed artifacts."""

    @classmethod
    def setUpClass(cls):
        cls.summaries = C.discover_summaries(CAMPAIGN)
        cls.iso_frame = C.build_iso_frame(cls.summaries)

    def _tables(self, isos: tuple[str, ...] | None = None):
        frame = self.iso_frame
        if isos is not None:
            frame = frame[frame["iso"].isin(isos)].reset_index(drop=True)
        system = C.build_system_frame(frame)
        return frame, system, C.build_delta_table(frame, system, "REF")

    def _organic_2030(self, deltas: pd.DataFrame) -> pd.Series:
        rows = deltas[
            (deltas["scope"] == C.SYSTEM_LABEL)
            & (deltas["case"] == "LOAD-HI-ORGANIC")
            & (deltas["year"] == 2030)
        ]
        self.assertEqual(len(rows), 1)
        return rows.iloc[0]

    def test_the_status_docs_broken_number_is_reproduced_from_the_levels(self):
        # The pre-repair arithmetic, recomputed here from campaign_emissions_system
        # so the "before" in the FINDING is a measurement and not a memory.
        _, system, _ = self._tables(STATUS_ISOS)

        def level(case: str) -> float:
            row = system[(system["case"] == case) & (system["year"] == 2030)].iloc[0]
            return float(row["emissions_mt"])

        self.assertAlmostEqual(
            level("LOAD-HI-ORGANIC") - level("REF"), STATUS_REPORTED_MT, 3
        )

    def test_the_repair_emits_the_status_docs_common_set_number(self):
        _, _, deltas = self._tables(STATUS_ISOS)
        row = self._organic_2030(deltas)
        self.assertAlmostEqual(row["emissions_mt_delta"], STATUS_COMMON_SET_MT, 3)
        self.assertEqual(row["delta_isos"], "ERCOT+NYISO")
        self.assertIn("NEISO", row["delta_coverage"])

    def test_the_error_the_repair_removes_is_neisos_ref_level(self):
        frame, _, deltas = self._tables(STATUS_ISOS)
        neiso_ref_2030 = float(
            frame[
                (frame["iso"] == "NEISO")
                & (frame["case"] == "REF")
                & (frame["year"] == 2030)
            ].iloc[0]["emissions_mt"]
        )
        self.assertAlmostEqual(
            STATUS_REPORTED_MT - STATUS_COMMON_SET_MT, -neiso_ref_2030, 3
        )
        self.assertAlmostEqual(-neiso_ref_2030, STATUS_ERROR_MT, 3)
        # And the repaired table no longer carries it.
        self.assertAlmostEqual(
            self._organic_2030(deltas)["emissions_mt_delta"], STATUS_COMMON_SET_MT, 3
        )

    def test_the_repair_holds_over_the_whole_committed_tree(self):
        # More ISOs have landed since the STATUS doc, so the naive error grows;
        # the common-set answer for ORGANIC is unchanged because its ISO set is.
        _, system, deltas = self._tables()
        row = self._organic_2030(deltas)
        self.assertAlmostEqual(row["emissions_mt_delta"], STATUS_COMMON_SET_MT, 3)
        naive = float(
            system[
                (system["case"] == "LOAD-HI-ORGANIC") & (system["year"] == 2030)
            ].iloc[0]["emissions_mt"]
        ) - float(
            system[(system["case"] == "REF") & (system["year"] == 2030)].iloc[0][
                "emissions_mt"
            ]
        )
        self.assertLess(naive, 0.0)  # the sign itself flips under the defect
        self.assertNotAlmostEqual(naive, STATUS_COMMON_SET_MT, 3)

    def test_every_row_of_the_committed_tree_names_its_iso_set(self):
        _, _, deltas = self._tables()
        self.assertTrue((deltas["delta_n_isos"] >= 0).all())
        system = deltas[deltas["scope"] == C.SYSTEM_LABEL]
        for _, row in system.iterrows():
            if row["delta_coverage"] == C.COVERAGE_FULL:
                continue
            self.assertIn("COMMON-SET ONLY", row["delta_coverage"])
            self.assertTrue(row["delta_isos"])


if __name__ == "__main__":
    unittest.main()
