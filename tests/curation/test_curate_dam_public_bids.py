"""Tests for the dam-public-bids intake on a tiny synthetic fixture.

Writes a minimal CAISO ``PUB_DAM_GRP`` daily zip (three resources: one
piecewise curve, one self-schedule, one AS bid, plus a run-length-encoded
3-hour curve and a 2-hour self-schedule) into a tmp raw tree, runs
``curate``, and asserts the written Parquet is schema-valid and the
reconciliation (segment vs self-schedule row split, GMT hour selection,
RLE expansion to the declared per-hour grain, ascending-MW step_idx) is
correct. CLEAN_DIR is redirected to a tmp dir (as in
tests/curation/test_curate_outages.py) so it never touches the real tree.
"""

import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_dam_public_bids as curate_dpb
from scripts.lib import clean_io

_HEADER = (
    "STARTTIME,STOPTIME,STARTTIME_GMT,STOPTIME_GMT,STARTDATE,MARKET_RUN_ID,"
    "RESOURCE_TYPE,SCHEDULINGCOORDINATOR_SEQ,RESOURCEBID_SEQ,"
    "TIMEINTERVALSTART,TIMEINTERVALEND,TIMEINTERVALSTART_GMT,"
    "TIMEINTERVALEND_GMT,PRODUCTBID_DESC,PRODUCTBID_MRID,MARKETPRODUCT_DESC,"
    "MARKETPRODUCTTYPE,SELFSCHEDMW,SCH_BID_TIMEINTERVALSTART,"
    "SCH_BID_TIMEINTERVALSTOP,SCH_BID_TIMEINTERVALSTART_GMT,"
    "SCH_BID_TIMEINTERVALSTOP_GMT,SCH_BID_XAXISDATA,SCH_BID_Y1AXISDATA,"
    "SCH_BID_Y2AXISDATA,SCH_BID_CURVETYPE,MINEOHSTATEOFCHARGE,"
    "MAXEOHSTATEOFCHARGE"
)

# Resource 111: 3-point EN curve for hour 08:00 UTC, deliberately out of MW
# order in the file (80 MW row before 40 MW row) to exercise the step_idx
# sort. Resource 222: EN self-schedule at hour 09:00 UTC + one SR curve row.
_ROWS = [
    # curve rows (hour in SCH_BID_TIMEINTERVALSTART_GMT)
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9001,111,,,,,,,,EN,,"
    "2024-01-10T00:00:00,2024-01-10T01:00:00,2024-01-10T08:00:00-00:00,"
    "2024-01-10T09:00:00-00:00,80.0,55.5,,BIDPRICE,,",
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9001,111,,,,,,,,EN,,"
    "2024-01-10T00:00:00,2024-01-10T01:00:00,2024-01-10T08:00:00-00:00,"
    "2024-01-10T09:00:00-00:00,40.0,30.25,,BIDPRICE,,",
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9001,111,,,,,,,,EN,,"
    "2024-01-10T00:00:00,2024-01-10T01:00:00,2024-01-10T08:00:00-00:00,"
    "2024-01-10T09:00:00-00:00,100.0,999.99,,BIDPRICE,,",
    # self-schedule row (hour in TIMEINTERVALSTART_GMT, no curve)
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9002,222,"
    "2024-01-10T01:00:00,2024-01-10T02:00:00,2024-01-10T09:00:00-00:00,"
    "2024-01-10T10:00:00-00:00,,,,EN,17.5,,,,,,,,,",
    # AS (SR) curve row for resource 222
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9002,222,,,,,,,,SR,,"
    "2024-01-10T01:00:00,2024-01-10T02:00:00,2024-01-10T09:00:00-00:00,"
    "2024-01-10T10:00:00-00:00,12.0,4.0,,BIDPRICE,,",
    # Resource 333: run-length-encoded 2-point EN curve held for THREE hours
    # (12:00-15:00 UTC) — one raw row per breakpoint, six clean rows.
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9003,333,,,,,,,,EN,,"
    "2024-01-10T04:00:00,2024-01-10T07:00:00,2024-01-10T12:00:00-00:00,"
    "2024-01-10T15:00:00-00:00,25.0,18.0,,BIDPRICE,,",
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9003,333,,,,,,,,EN,,"
    "2024-01-10T04:00:00,2024-01-10T07:00:00,2024-01-10T12:00:00-00:00,"
    "2024-01-10T15:00:00-00:00,10.0,7.0,,BIDPRICE,,",
    # Resource 333: run-length-encoded self-schedule held for TWO hours.
    ",,,,2024-01-10 00:00:00.0,DAM,GENERATOR,9003,333,"
    "2024-01-10T08:00:00,2024-01-10T10:00:00,2024-01-10T16:00:00-00:00,"
    "2024-01-10T18:00:00-00:00,,,,EN,9.5,,,,,,,,,",
]


def _write_fixture_zip(raw_dir: Path) -> Path:
    raw_dir.mkdir(parents=True, exist_ok=True)
    csv = "\n".join([_HEADER, *_ROWS]) + "\n"
    out = raw_dir / "20240110_PUB_BID_DAM_v3_csv.zip"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("20240110_20240110_PUB_BID_DAM_v3.csv", csv)
    out.write_bytes(buf.getvalue())
    return out


class TestCurateDamPublicBids(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        _write_fixture_zip(self.raw_root)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_roundtrip(self) -> None:
        written = curate_dpb.curate(
            raw_root=self.raw_root, isos=["CAISO"], years=[2024]
        )
        self.assertEqual(len(written), 1)
        clean_io.validate_clean(written[0])
        df = pd.read_parquet(written[0])
        # 5 single-hour rows + 2 breakpoints x 3 hours + 1 self-sched x 2 hours.
        self.assertEqual(len(df), 13)

        # Curve rows: step_idx follows ascending MW despite file order.
        en111 = df[(df.resource_seq == 111) & (df["product"] == "EN")].sort_values(
            "step_idx"
        )
        self.assertEqual(list(en111.segment_mw), [40.0, 80.0, 100.0])
        self.assertEqual(list(en111.step_idx), [1, 2, 3])
        self.assertEqual(list(en111.row_kind.unique()), ["segment"])
        self.assertEqual(
            str(en111.interval_start_utc.iloc[0]), "2024-01-10 08:00:00+00:00"
        )

        # Self-schedule row: hour from TIMEINTERVALSTART_GMT, MW carried.
        ss = df[(df.row_kind == "self_sched") & (df.resource_seq == 222)]
        self.assertEqual(len(ss), 1)
        self.assertEqual(ss.self_sched_mw.iloc[0], 17.5)
        self.assertTrue(pd.isna(ss.segment_mw.iloc[0]))
        self.assertEqual(
            str(ss.interval_start_utc.iloc[0]), "2024-01-10 09:00:00+00:00"
        )

        # AS product retained.
        self.assertEqual((df["product"] == "SR").sum(), 1)

        # RLE curve: one raw row per breakpoint held 12:00-15:00 UTC becomes
        # a complete 2-step curve in EACH of the three hours, and step_idx
        # restarts per hour in ascending-MW order (caiso-152).
        en333 = df[(df.resource_seq == 333) & (df.row_kind == "segment")].sort_values(
            ["interval_start_utc", "step_idx"]
        )
        self.assertEqual(len(en333), 6)
        self.assertEqual(
            [str(t) for t in en333.interval_start_utc.unique()],
            [
                "2024-01-10 12:00:00+00:00",
                "2024-01-10 13:00:00+00:00",
                "2024-01-10 14:00:00+00:00",
            ],
        )
        self.assertEqual(list(en333.step_idx), [1, 2, 1, 2, 1, 2])
        self.assertEqual(list(en333.segment_mw), [10.0, 25.0] * 3)
        self.assertEqual(list(en333.segment_price_usd_per_mwh), [7.0, 18.0] * 3)

        # RLE self-schedule: the quantity repeats in every hour of its range,
        # it is never summed or spread across them.
        ss333 = df[
            (df.resource_seq == 333) & (df.row_kind == "self_sched")
        ].sort_values("interval_start_utc")
        self.assertEqual(len(ss333), 2)
        self.assertEqual(list(ss333.self_sched_mw), [9.5, 9.5])
        self.assertEqual(
            [str(t) for t in ss333.interval_start_utc],
            ["2024-01-10 16:00:00+00:00", "2024-01-10 17:00:00+00:00"],
        )
        self.assertEqual(list(ss333.step_idx), [1, 1])

        # Idempotent re-run.
        again = curate_dpb.curate(raw_root=self.raw_root, isos=["CAISO"], years=[2024])
        self.assertEqual(len(again), 1)
        clean_io.validate_clean(again[0])


if __name__ == "__main__":
    unittest.main()
