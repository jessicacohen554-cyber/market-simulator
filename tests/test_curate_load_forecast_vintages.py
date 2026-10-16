"""Tests for the ``load-forecast-vintages`` intake (SPP MTLF) and its lead selector."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pandas as pd

from scripts.data.curate_load_forecast_vintages import curate
from scripts.lib.load_forecast_vintages import spp
from market_sim.data.load_forecast_vintages import forecast_at_lead, select_at_lead
from tests.helpers.base import RawFixtureTestCase
from tests.helpers.clean_asserts import assert_clean_valid, read_clean_or_fail

HOUR = pd.Timedelta(hours=1)


def _mtlf_csv(issue_utc: pd.Timestamp, base_mw: float, with_baa: bool = False) -> bytes:
    """A synthetic OP-MTLF file: 24 past rows with actuals + 169 forward rows."""
    lines = [
        "Interval,GMTIntervalEnd,MTLF,Averaged Actual" + (",BAA" if with_baa else "")
    ]
    for lead in range(spp.MTLF_HORIZON_HOURS, -25, -1):
        end = issue_utc + lead * HOUR
        local = end.tz_convert(spp.SPP_TZ).tz_localize(None)
        act = "" if lead > 1 else f"{base_mw - 5:.0f}"
        row = (
            f"{local:%m/%d/%Y %H:%M:%S},{end.tz_localize(None):%m/%d/%Y %H:%M:%S},"
            f"{base_mw + lead:.0f},{act}"
        )
        lines.append(row + (",SPP" if with_baa else ""))
    return ("\n".join(lines) + "\n").encode()


def _member(issue_utc: pd.Timestamp, suffix: str = "") -> str:
    """Archive member path for a vintage (stamp in Central prevailing time)."""
    loc = issue_utc.tz_convert(spp.SPP_TZ)
    return f"{loc:%Y/%m/%d}/OP-MTLF-{loc:%Y%m%d%H}00{suffix}.csv"


def _write_zip(path: Path, members: dict[str, bytes]) -> None:
    """Write a year zip with the archive's member layout."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as z:
        for name, data in members.items():
            z.writestr(name, data)


class TestSppParse(RawFixtureTestCase):
    """Parsing one SPP year zip into the tidy vintage frame."""

    def setUp(self) -> None:
        super().setUp()
        self.raw = self.tmp_path / "raw"
        self.issue_a = pd.Timestamp("2024-07-15 05:00", tz="UTC")  # 00:00 CDT
        self.issue_b = self.issue_a + 4 * HOUR
        _write_zip(
            self.raw / "load-forecast-vintages" / "spp" / "2024.zip",
            {
                _member(self.issue_a): _mtlf_csv(self.issue_a, 30000.0),
                _member(self.issue_b): _mtlf_csv(self.issue_b, 31000.0, with_baa=True),
            },
        )

    def test_curate_writes_valid_partition(self) -> None:
        """One partition, both vintages, 193 rows each, issue times from the horizon."""
        written = curate(raw_root=self.raw, isos=["SPP"])
        self.assertEqual(len(written), 1)
        assert_clean_valid("load-forecast-vintages", iso="SPP", year=2024)
        df = read_clean_or_fail("load-forecast-vintages", iso="SPP", year=2024)
        self.assertEqual(
            sorted(df["issue_time_utc"].unique()), [self.issue_a, self.issue_b]
        )
        self.assertEqual(len(df), 2 * 193)
        self.assertEqual(set(df["area"]), {"SPP"})
        self.assertEqual(int(df["lead_hours"].min()), -24)
        self.assertEqual(int(df["lead_hours"].max()), 168)
        fwd = df[df["lead_hours"] > 1]
        self.assertTrue(fwd["actual_mw"].isna().all())

    def test_select_at_lead_picks_latest_qualifying_vintage(self) -> None:
        """Lead L: latest vintage issued at or before the hour's start less L."""
        curate(raw_root=self.raw, isos=["SPP"])
        df = read_clean_or_fail("load-forecast-vintages", iso="SPP", year=2024)
        hour_end = self.issue_b + 6 * HOUR  # starts 5 h after issue_b
        at4 = select_at_lead(df, 4).loc[hour_end]
        self.assertEqual(at4["issue_time_utc"], self.issue_b)
        self.assertEqual(int(at4["lead_hours"]), 5)
        self.assertEqual(at4["forecast_mw"], 31000.0 + 6)
        at6 = select_at_lead(df, 6).loc[hour_end]
        self.assertEqual(at6["issue_time_utc"], self.issue_a)
        self.assertEqual(at6["forecast_mw"], 30000.0 + 10)

    def test_forecast_at_lead_reads_the_year(self) -> None:
        """The year reader returns hours ending in that UTC year only."""
        curate(raw_root=self.raw, isos=["SPP"])
        out = forecast_at_lead("SPP", 2024, 1)
        self.assertTrue((out.index.year == 2024).all())
        self.assertGreater(len(out), 160)


class TestSppDstStamps(RawFixtureTestCase):
    """SPP's fall-back relabelling (``...0200d.csv``) parses from the horizon."""

    def test_fall_back_pair(self) -> None:
        """The 07 UTC "0200" and 08 UTC "0200d" vintages are distinct issues."""
        first = pd.Timestamp("2024-11-03 07:00", tz="UTC")
        second = first + HOUR
        members = {
            "2024/11/03/OP-MTLF-202411030200.csv": _mtlf_csv(first, 25000.0),
            "2024/11/03/OP-MTLF-202411030200d.csv": _mtlf_csv(second, 25100.0),
        }
        df = spp.parse_members(members)
        self.assertEqual(sorted(df["issue_time_utc"].unique()), [first, second])

    def test_bad_stamp_raises(self) -> None:
        """A stamp far from its horizon (no DST nearby) is a malformed file."""
        issue = pd.Timestamp("2024-07-15 05:00", tz="UTC")
        members = {"2024/07/15/OP-MTLF-202407150300.csv": _mtlf_csv(issue, 30000.0)}
        with self.assertRaises(ValueError):
            spp.parse_members(members)
