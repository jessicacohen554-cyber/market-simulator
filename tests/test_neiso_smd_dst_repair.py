"""Tests for the NEISO SMD DST-naive workbook-vintage repair (neiso-97, audit row O8).

The 2018-2023 SMD workbook vintage publishes a FLAT 24 rows on every calendar
day. Measured against the market's own daily hourly-LMP reports
(``scripts/probes/neiso97_smd_dst_defect_quantify.py``, 0 mismatches over all
truth days x 9 sheets x both markets):

* spring-forward (23 real hours): positional row 1 is a FABRICATED entry for
  the nonexistent hour (the mean of its neighbours); the true values sit one
  row late from there.
* fall-back (25 real hours): positional row 1 is the repeated hour's two
  instances COLLAPSED TO THEIR MEAN; the true values for positions 3..24 sit
  at rows 2..23, and the two instances exist only in the daily-report route.

These tests pin the repaired placement in BOTH workbook readers —
``derive_actual_lmp._neiso_sheet_series`` (+ the day-scoped daily-report
overlay in ``neiso_zone_hourly``) and ``curate_lmp._neiso_flat24_repair`` —
and pin that true-shape (2024+) days pass through untouched. Nothing here
touches the network or the committed data.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import openpyxl
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import curate_lmp  # noqa: E402
from scripts.data import derive_actual_lmp as dal  # noqa: E402
from scripts.data import fetch_neiso_smd_zonal_lmp as f  # noqa: E402

SPRING = "2023-03-12"  # 23 real hours
FALL = "2023-11-05"  # 25 real hours


def _write_workbook(path: Path, days: dict[str, int]) -> None:
    """A synthetic hub-sheet SMD workbook: ``{date: n_rows}``, values 100+k / 200+k.

    Column layout mirrors the real sheets: Date at 0, Hr_End at 1, DA_LMP at
    ``dal.NEISO_DA_COL`` (4), RT_LMP at ``dal.NEISO_RT_COL`` (8).
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = dal.NEISO_HUB_SHEET
    header = ["Date", "Hr_End", "", "", "DA_LMP", "", "", "", "RT_LMP"]
    ws.append(header)
    for date, n in days.items():
        for k in range(n):
            row = [
                date,
                f"{k + 1:02d}",
                None,
                None,
                100.0 + k,
                None,
                None,
                None,
                200.0 + k,
            ]
            ws.append(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _sheet_series(days: dict[str, int]) -> dict[str, pd.Series]:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "wb.xlsx"
        _write_workbook(p, days)
        wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
        try:
            return dal._neiso_sheet_series(wb, dal.NEISO_HUB_SHEET)
        finally:
            wb.close()


def _instants(date: str, positions) -> list[pd.Timestamp]:
    start = pd.Timestamp(date).tz_localize(dal._EASTERN_TZ).tz_convert("UTC")
    return [start + pd.Timedelta(hours=p) for p in positions]


class SheetSeriesVintageTest(unittest.TestCase):
    """The positional clock is vintage-aware in ``_neiso_sheet_series``."""

    def test_flat24_spring_drops_phantom_and_replaces(self) -> None:
        ser = _sheet_series({SPRING: 24})["da"]
        self.assertEqual(len(ser), 23)
        self.assertEqual(list(ser.index), _instants(SPRING, range(23)))
        # Position 0 keeps row 0; positions 1..22 take rows 2..23 (row 1, the
        # fabricated neighbour-mean phantom, is dropped).
        self.assertEqual(ser.iloc[0], 100.0)
        for p in range(1, 23):
            self.assertEqual(ser.iloc[p], 100.0 + p + 1)

    def test_flat24_fall_drops_pair_mean_and_replaces(self) -> None:
        ser = _sheet_series({FALL: 24})["rt"]
        # Positions 1-2 (the repeated hour's two instances) are absent here;
        # the daily-report overlay supplies them.
        self.assertEqual(list(ser.index), _instants(FALL, [0, *range(3, 25)]))
        self.assertEqual(ser.iloc[0], 200.0)
        for i, p in enumerate(range(3, 25)):
            self.assertEqual(ser[_instants(FALL, [p])[0]], 200.0 + i + 2)

    def test_true_shape_days_pass_through_positionally(self) -> None:
        for date, n in ((SPRING, 23), (FALL, 25), ("2023-07-04", 24)):
            ser = _sheet_series({date: n})["da"]
            self.assertEqual(list(ser.index), _instants(date, range(n)), date)
            self.assertEqual(list(ser), [100.0 + k for k in range(n)], date)


class ReportOverlayTest(unittest.TestCase):
    """A day the workbook cannot represent is taken from the daily report."""

    def test_defective_day_overlaid_normal_day_kept(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _write_workbook(
                d / "NEISO" / "2023_smd_hourly.xlsx", {"2023-11-04": 24, FALL: 24}
            )
            hours = ["01", "02", "02X"] + [f"{h:02d}" for h in range(3, 25)]
            rows = [
                {
                    "date": FALL,
                    "hour_ending": he,
                    "seq": s,
                    "location_id": "4000",
                    "location": f.SMD_LOCATIONS["4000"],
                    "da_lmp": 300.0 + s,
                    "rt_lmp": 400.0 + s,
                }
                for s, he in enumerate(hours)
            ]
            f.write_year_csv(rows, 2023, dest_dir=d / "report")
            orig_lmp, orig_rep = dal.LMP_DIR, dal.NEISO_REPORT_DIR
            dal.LMP_DIR, dal.NEISO_REPORT_DIR = d, d / "report"
            try:
                fr = dal.neiso_zone_hourly(2023, "da")
            finally:
                dal.LMP_DIR, dal.NEISO_REPORT_DIR = orig_lmp, orig_rep
            self.assertIsNotNone(fr)
            hub = fr["hub"]
            # The defective fall day carries all 25 hours from the REPORT,
            # repeated-hour pair included.
            for p in range(25):
                self.assertEqual(hub[_instants(FALL, [p])[0]], 300.0 + p)
            # The normal day is untouched workbook data at every hour.
            for p in range(24):
                self.assertEqual(hub[_instants("2023-11-04", [p])[0]], 100.0 + p)


class CurateFlat24RepairTest(unittest.TestCase):
    """``curate_lmp._neiso_flat24_repair`` fixes the label clock's two defects.

    ``Hr_End`` is built as int64, matching what ``pd.read_excel`` yields for
    the all-numeric flat-24 vintage sheets — the only vintage that reaches the
    relabel. A str-typed frame here let the original str relabel pass tests
    while the real corpus raised under pandas 3 (golden-data-tier run
    31999181985, first cron firing).
    """

    def _day(self, date: str, n: int) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Date": [date] * n,
                "Hr_End": pd.array([k + 1 for k in range(n)], dtype="int64"),
                "DA_LMP": [100.0 + k for k in range(n)],
            }
        )

    def test_spring_phantom_dropped_and_true_he02_relabeled(self) -> None:
        out = curate_lmp._neiso_flat24_repair(self._day(SPRING, 24))
        self.assertEqual(len(out), 23)
        self.assertNotIn(101.0, set(out["DA_LMP"]))  # the phantom value
        self.assertEqual(out.iloc[1]["Hr_End"], 2)  # true HE02, relabeled
        self.assertEqual(out.iloc[1]["DA_LMP"], 102.0)
        self.assertEqual(list(out.iloc[2:]["Hr_End"]), list(range(4, 25)))
        self.assertEqual(out["Hr_End"].dtype, "int64")  # no silent upcast

    def test_fall_pair_mean_dropped(self) -> None:
        out = curate_lmp._neiso_flat24_repair(self._day(FALL, 24))
        self.assertEqual(len(out), 23)
        self.assertNotIn(101.0, set(out["DA_LMP"]))  # the collapsed mean
        self.assertEqual(out.iloc[1]["Hr_End"], 3)

    def test_true_shape_days_untouched(self) -> None:
        for date, n in ((SPRING, 23), (FALL, 25), ("2023-07-04", 24)):
            frame = self._day(date, n)
            out = curate_lmp._neiso_flat24_repair(frame)
            pd.testing.assert_frame_equal(out, frame)


if __name__ == "__main__":
    unittest.main()
