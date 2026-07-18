"""Tests for the reserve-requirements intake on tiny synthetic fixtures.

Writes minimal ISO-NE "Hourly Reserve Requirements" window CSVs (normal,
spring-forward and fall-back days) into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid, the positional HE->UTC mapping
lands each local day on its true UTC hours (23/24/25 rows), and the model
loader (``market_sim.data.neiso_reserve_requirements``) returns the mapped
family series and hard-errors when the clean partition is absent. NOT a
full-data run: CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_capacity_deliverability.py) so it never touches the real
tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_reserve_requirements as curate_rr
from scripts.lib import clean_io
from scripts.lib import reserve_requirements as rr
from scripts.lib.clean_io import validate_clean
from scripts.lib.reserve_requirements import neiso


def _window_csv(days: dict[str, list[str]]) -> str:
    """Build a report CSV: date -> ordered HE labels, all four locations.

    System (7000) rows carry distinguishable values (spin=300+h, 10min=1200+h,
    total=2000+h for HE index h); local rows carry zeros except a fixed
    30-minute total.
    """
    lines = [
        "C,Hourly Reserve Requirements",
        "C,Filename: requirements_test.csv",
        "C,Time period: test fixture",
        "C,Report generated 2026-01-01 00:00:00 EST",
        "H,,,Location ID,Ten-Minute Spinning,Ten-Minute,TOTAL",
        "H,Date,Hour Ending,Label,MW,MW,MW",
    ]
    for date, hes in days.items():
        for h, he in enumerate(hes):
            lines.append(f"D,{date},{he},7000,{300 + h},{1200 + h},{2000 + h}")
            for loc, total in ((7001, 280.0), (7002, 878.0), (7003, 1600.0)):
                lines.append(f"D,{date},{he},{loc},0,0,{total}")
    n = sum(len(v) for v in days.values()) * 4
    lines.append(f"T,{n} lines")
    return "\n".join(lines) + "\n"


_HE_NORMAL = [f"{h:02d}" for h in range(1, 25)]
_HE_SPRING = [he for he in _HE_NORMAL if he != "03"]  # 23 rows, no HE 03
_HE_FALL = _HE_NORMAL[:2] + ["02X"] + _HE_NORMAL[2:]  # 25 rows, 02 repeated


def _write_fixture(raw_root: Path) -> None:
    dest = raw_root / "NEISO-AS" / "requirements"
    dest.mkdir(parents=True)
    (dest / "requirements_20230101_20230101.csv").write_text(
        _window_csv({"2023-01-01": _HE_NORMAL})
    )
    (dest / "requirements_20230312_20230312.csv").write_text(
        _window_csv({"2023-03-12": _HE_SPRING})
    )
    (dest / "requirements_20231105_20231105.csv").write_text(
        _window_csv({"2023-11-05": _HE_FALL})
    )


class TestCurateReserveRequirements(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.raw = self.tmp / "raw"
        _write_fixture(self.raw)
        self._old_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = self.tmp / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._old_clean
        self._tmp.cleanup()

    def test_parse_maps_local_days_to_true_utc_hours(self):
        df = neiso.parse(self.raw, 2023)
        # 24 + 23 + 25 = 72 hours x 4 locations x 3 products
        self.assertEqual(len(df), 72 * 4 * 3)
        sys30 = df[(df["location"] == "ROS") & (df["product"] == "30min_total")]
        self.assertEqual(len(sys30), 72)
        # UTC key is unique and hourly-contiguous within each day.
        self.assertTrue(sys30["interval_start_utc"].is_unique)
        jan1 = sys30[sys30["interval_start_local"].dt.date.astype(str) == "2023-01-01"]
        self.assertEqual(list(jan1["requirement_mw"]), [2000.0 + h for h in range(24)])
        # Jan 1 HE 01 is local midnight EST = 05:00 UTC.
        self.assertEqual(
            jan1["interval_start_utc"].iloc[0], pd.Timestamp("2023-01-01 05:00Z")
        )
        # DST days carry their true UTC hour counts.
        by_day = sys30.groupby(
            sys30["interval_start_utc"].dt.tz_convert("America/New_York").dt.date
        ).size()
        self.assertEqual(by_day[pd.Timestamp("2023-03-12").date()], 23)
        self.assertEqual(by_day[pd.Timestamp("2023-11-05").date()], 25)

    def test_parse_step_fills_source_holes(self):
        dest = self.raw / "NEISO-AS" / "requirements"
        # HE 15 missing (the real 2023-03-14 publication hole pattern).
        (dest / "requirements_20230601_20230601.csv").write_text(
            _window_csv({"2023-06-01": [he for he in _HE_NORMAL if he != "15"]})
        )
        df = neiso.parse(self.raw, 2023)
        sys30 = df[
            (df["location"] == "ROS")
            & (df["product"] == "30min_total")
            & (df["interval_start_local"].dt.date.astype(str) == "2023-06-01")
        ].sort_values("interval_start_utc")
        self.assertEqual(len(sys30), 24)  # the hole comes back, step-filled
        vals = list(sys30["requirement_mw"])
        # HE 15 = local hour-beginning 14 (index 14): held from HE 14's value.
        self.assertEqual(vals[14], vals[13])

    def test_parse_rejects_row_outside_day_sequence(self):
        dest = self.raw / "NEISO-AS" / "requirements"
        csv_text = _window_csv({"2023-06-02": _HE_NORMAL})
        # Duplicate a non-fall-back hour: cannot fit the day's sequence.
        csv_text += "D,2023-06-02,13,7000,1,2,3\n"
        (dest / "requirements_20230602_20230602.csv").write_text(csv_text)
        with self.assertRaises(ValueError):
            neiso.parse(self.raw, 2023)

    def test_parse_rejects_gap_budget_overrun(self):
        dest = self.raw / "NEISO-AS" / "requirements"
        # Four days with only HE 01 published: 4 x 23 = 92 holes > 72 budget.
        (dest / "requirements_20230701_20230704.csv").write_text(
            _window_csv({f"2023-07-{d:02d}": ["01"] for d in range(1, 5)})
        )
        with self.assertRaises(ValueError):
            neiso.parse(self.raw, 2023)

    def test_curate_writes_schema_valid_partition(self):
        written = curate_rr.curate(raw_root=self.raw, isos=["NEISO"], years=[2023])
        self.assertEqual(len(written), 1)
        validate_clean(written[0])
        df = clean_io.read_clean(rr.DATATYPE, iso="NEISO", year=2023)
        self.assertEqual(len(df), 72 * 4 * 3)
        spin = df[(df["location"] == "ROS") & (df["product"] == "10min_spin")]
        self.assertEqual(spin["requirement_mw"].iloc[0], 300.0)

    def test_loader_returns_family_series_and_hard_errors_when_absent(self):
        from market_sim.data.neiso_reserve_requirements import (
            load_neiso_reserve_requirements,
        )

        with self.assertRaises(FileNotFoundError):
            load_neiso_reserve_requirements(2023, 24)

        curate_rr.curate(raw_root=self.raw, isos=["NEISO"], years=[2023])
        fam = load_neiso_reserve_requirements(2023, 24)
        self.assertEqual(
            set(fam), {"ne_30min_total", "ne_10min_total", "ne_10min_spin"}
        )
        self.assertEqual(fam["ne_30min_total"][0], 2000.0)
        self.assertEqual(fam["ne_10min_spin"][23], 300.0 + 23)
        # Fixture covers 72 hours; a longer horizon must hard-error.
        with self.assertRaises(ValueError):
            load_neiso_reserve_requirements(2023, 8760)


if __name__ == "__main__":
    unittest.main()
