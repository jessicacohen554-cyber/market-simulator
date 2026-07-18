"""Tests for the MISO per-hub LMP reduction (scope decision D6).

Builds a tiny staged fixture (one hub, three days straddling Feb 29 of a leap
year) and checks the hour-of-year mapping onto the model's chronological
non-leap 8760-hour calendar — fixed Central STANDARD time, a constant -1 h
from the reports' fixed-EST labels in every season (the 2026-07-15
scoring-clock fix; previously the mapping was Central *prevailing*, which
paired CST-month hours one real hour off) — plus the hub -> model-zone map
against the real staged files' vocabulary.
"""

import gzip
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.data import derive_miso_hub_lmp as dml


def _stage_fixture(stage_dir: Path, year: int, market: str, days: list[str]) -> None:
    """Write a one-hub staged gz CSV whose HE values encode day-index * 100 + HE."""
    header = "date,node,type,value," + ",".join(f"he{h:02d}" for h in range(1, 25))
    lines = [header]
    for d_i, day in enumerate(days):
        vals = ",".join(str(d_i * 100 + he) for he in range(1, 25))
        lines.append(f"{day},MINN.HUB,Hub,LMP,{vals}")
        # MCC rows must be ignored by the reduction.
        lines.append(f"{day},MINN.HUB,Hub,MCC,{vals}")
    path = stage_dir / f"miso_hub_lmp_{year}_{market}.csv.gz"
    with gzip.open(path, "wt") as f:
        f.write("\n".join(lines) + "\n")


class TestDeriveMisoHubLmp(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig_stage = dml.STAGE_DIR
        dml.STAGE_DIR = Path(self._tmp.name)

    def tearDown(self) -> None:
        dml.STAGE_DIR = self._orig_stage
        self._tmp.cleanup()

    def test_leap_day_dropped_and_winter_hours_shift_to_cst(self) -> None:
        # February is CST (UTC-6) while the reports are EST (UTC-5), so each
        # hour-ending shifts back one local hour: HE 2 of a date is that
        # date's local midnight. 2024 is a leap year: local Feb 29 must vanish
        # and Mar 1 must land at the non-leap hour-of-year (31+28)*24.
        _stage_fixture(
            dml.STAGE_DIR, 2024, "rt", ["2024-02-28", "2024-02-29", "2024-03-01"]
        )
        frame = dml._market_frame(2024, "rt")
        by_hour = frame.set_index("hour")["price"]
        feb28_local_midnight = (31 + 27) * 24
        mar01_local_midnight = (31 + 28) * 24
        self.assertEqual(by_hour[feb28_local_midnight], 2.0)  # Feb 28 HE 2
        self.assertEqual(by_hour[mar01_local_midnight], 202.0)  # Mar 1 HE 2
        # Feb 29 HE 1 = Feb 28 23:00 CST -> the last kept hour of Feb 28.
        self.assertEqual(by_hour[feb28_local_midnight + 23], 101.0)
        # Local Feb 29 (Feb 29 HE 2..24 + Mar 1 HE 1) contributes no rows.
        self.assertFalse(by_hour.isin(list(range(102, 125)) + [201]).any())
        self.assertEqual(len(frame), 2 * 24)
        self.assertTrue((frame["year"] == 2024).all())

    def test_summer_hours_shift_to_cst_like_winter(self) -> None:
        # The calendar is fixed CST year-round, so July shifts exactly like
        # February: HE 2 (01:00 EST = 00:00 CST) is the date's slot midnight.
        # HE 1 (00:00 EST = 23:00 CST of the prior day) lands one slot before.
        _stage_fixture(dml.STAGE_DIR, 2024, "rt", ["2024-07-01"])
        frame = dml._market_frame(2024, "rt")
        by_hour = frame.set_index("hour")["price"]
        jul01_slot_midnight = sum((31, 28, 31, 30, 31, 30)) * 24
        self.assertEqual(by_hour[jul01_slot_midnight], 2.0)  # HE 2
        self.assertEqual(by_hour[jul01_slot_midnight - 1], 1.0)  # HE 1
        self.assertEqual(by_hour[jul01_slot_midnight + 22], 24.0)  # HE 24

    def test_jan1_first_hour_spills_into_prior_year(self) -> None:
        # Jan 1 HE 1 EST = Dec 31 23:00 CST -> local year - 1, hour 8759.
        _stage_fixture(dml.STAGE_DIR, 2024, "rt", ["2024-01-01"])
        frame = dml._market_frame(2024, "rt")
        spill = frame[frame["year"] == 2023]
        self.assertEqual(len(spill), 1)
        self.assertEqual(int(spill["hour"].iloc[0]), 8759)
        self.assertEqual(float(spill["price"].iloc[0]), 1.0)

    def test_hub_zone_map_covers_all_hubs(self) -> None:
        # Every fetched hub maps to a model zone, South carries the four
        # southern hubs, and Plains (no hub) is only ever a documented proxy.
        from scripts.data.fetch_miso_hub_lmp import HUBS

        self.assertEqual(set(dml.HUB_TO_ZONE), set(HUBS))
        south = {h for h, z in dml.HUB_TO_ZONE.items() if z == "MISO-South"}
        self.assertEqual(
            south, {"ARKANSAS.HUB", "LOUISIANA.HUB", "TEXAS.HUB", "MS.HUB"}
        )
        self.assertNotIn("MISO-Plains", dml.HUB_TO_ZONE.values())


if __name__ == "__main__":
    unittest.main()
