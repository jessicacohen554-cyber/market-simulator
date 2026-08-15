"""Tests for the ISO-NE daily-report LMP reducer (neiso-96 intake).

Covers the parts of ``scripts/data/fetch_neiso_smd_zonal_lmp.py`` that are pure
functions of a report body, plus the seam that hands the reduced CSV to
``derive_actual_lmp.neiso_zone_hourly``. Nothing here touches the network.

The DST cases are the point of the file: the reducer's whole correctness claim
is that it keys hours on the as-published within-day POSITION rather than on the
``Hour Ending`` label, so the 23-hour spring-forward day and the 25-hour
fall-back day need no special case. Both are asserted directly.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data import derive_actual_lmp as dal  # noqa: E402
from scripts.data import fetch_neiso_smd_zonal_lmp as f  # noqa: E402

PREAMBLE = (
    '"C","Day-Ahead Energy Market Hourly LMP Report"\n'
    '"C","Report for: 01/15/2026 - 01/15/2026"\n'
    '"H","Date","Hour Ending","Location ID","Location Name","Location Type",'
    '"Locational Marginal Price","Energy Component","Congestion Component",'
    '"Marginal Loss Component"\n'
)


def _body(date: str, hours: list[str], base: float = 50.0) -> bytes:
    """Build a synthetic all-node report: the nine SMD rows plus a decoy node.

    The decoy is a NETWORK NODE, which the reducer must drop; if it were kept it
    would shift every subsequent ``seq`` and the DST assertions would fail.
    """
    out = [PREAMBLE]
    for i, he in enumerate(hours):
        out.append(
            f'"D","{date}","{he}","321","UN.DECOY13.8","NETWORK NODE",'
            f"{base + i},0,0,0\n"
        )
        for loc in sorted(f.SMD_LOCATIONS):
            price = base + i + int(loc) - 4000
            out.append(
                f'"D","{date}","{he}","{loc}","{f.SMD_LOCATIONS[loc]}",'
                f'"{"HUB" if loc == "4000" else "LOAD ZONE"}",{price},0,0,0\n'
            )
    # Pad past the short-body guard so the fixture looks like a real report.
    out.append('"C","' + "x" * f.MIN_REAL_BYTES + '"\n')
    return "".join(out).encode()


class ReduceReportTest(unittest.TestCase):
    """The all-node report reduces to exactly the nine SMD locations."""

    def test_keeps_only_smd_locations_and_counts_position(self) -> None:
        hours = [f"{h:02d}" for h in range(1, 25)]
        red = f.reduce_report(_body("01/15/2026", hours))
        self.assertEqual(len(red), 24 * 9)
        self.assertEqual({loc for _, loc in red}, set(f.SMD_LOCATIONS))
        # seq is 0-based and per location, in publication order.
        self.assertEqual(red[(0, "4000")], ("01", 50.0))
        self.assertEqual(red[(23, "4000")], ("24", 73.0))

    def test_missing_smd_location_is_an_error(self) -> None:
        body = _body("01/15/2026", ["01"]).replace(b'"4004"', b'"9999"')
        with self.assertRaises(RuntimeError):
            f.reduce_report(body)

    def test_spring_forward_day_has_23_positions(self) -> None:
        hours = ["01", "02"] + [f"{h:02d}" for h in range(4, 25)]
        red = f.reduce_report(_body("03/08/2026", hours))
        self.assertEqual(len(red), 23 * 9)
        # The label gap is preserved but position stays contiguous.
        self.assertEqual(red[(2, "4000")][0], "04")

    def test_fall_back_day_has_25_positions_including_02X(self) -> None:
        hours = ["01", "02", "02X"] + [f"{h:02d}" for h in range(3, 25)]
        red = f.reduce_report(_body("11/01/2026", hours))
        self.assertEqual(len(red), 25 * 9)
        self.assertEqual(red[(2, "4000")][0], "02X")
        self.assertEqual(red[(3, "4000")][0], "03")


class WriteYearCsvTest(unittest.TestCase):
    """The committed CSV is deterministic, idempotent and mergeable."""

    def _rows(self, date: str, n: int) -> list[dict]:
        return [
            {
                "date": date,
                "hour_ending": f"{s + 1:02d}",
                "seq": s,
                "location_id": loc,
                "location": f.SMD_LOCATIONS[loc],
                "da_lmp": 10.0 + s,
                "rt_lmp": 20.0 + s,
            }
            for s in range(n)
            for loc in sorted(f.SMD_LOCATIONS)
        ]

    def test_rewrite_is_byte_identical_and_merge_adds_days(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            p = f.write_year_csv(self._rows("2026-01-01", 24), 2026, dest_dir=d)
            first = p.read_bytes()
            # Idempotent: the same rows again produce the same bytes.
            f.write_year_csv(self._rows("2026-01-01", 24), 2026, dest_dir=d)
            self.assertEqual(p.read_bytes(), first)
            # Mergeable: a second day is added, not replaced.
            f.write_year_csv(self._rows("2026-01-02", 24), 2026, dest_dir=d)
            text = p.read_text()
            self.assertIn("2026-01-01", text)
            self.assertIn("2026-01-02", text)
            self.assertEqual(len(text.strip().splitlines()), 1 + 2 * 24 * 9)


class DeriveSeamTest(unittest.TestCase):
    """``neiso_zone_hourly`` reads the reduced CSV when no workbook exists."""

    def test_reads_report_csv_and_folds_model_zones(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            rows = [
                {
                    "date": "2026-01-01",
                    "hour_ending": f"{s + 1:02d}",
                    "seq": s,
                    "location_id": loc,
                    "location": f.SMD_LOCATIONS[loc],
                    "da_lmp": 10.0,
                    "rt_lmp": 20.0,
                }
                for s in range(24)
                for loc in sorted(f.SMD_LOCATIONS)
            ]
            f.write_year_csv(rows, 2026, dest_dir=d)
            orig = dal.NEISO_REPORT_DIR
            dal.NEISO_REPORT_DIR = d
            try:
                # A year with no workbook on disk falls to the report route.
                frame = dal.neiso_zone_hourly(1999, "rt")
                self.assertIsNone(frame)
                frame = dal.neiso_zone_hourly(2026, "rt")
            finally:
                dal.NEISO_REPORT_DIR = orig
            self.assertIsNotNone(frame)
            self.assertEqual(len(frame), 24)
            self.assertEqual(
                set(frame.columns), {*dal.NEISO_ZONE_MAP, "hub"}
            )
            self.assertTrue((frame["hub"] == 20.0).all())
            # Hour 0 is local midnight EST -> 05:00 UTC, and the day is
            # contiguous from there.
            self.assertEqual(str(frame.index[0]), "2026-01-01 05:00:00+00:00")
            self.assertEqual(str(frame.index[23]), "2026-01-02 04:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
