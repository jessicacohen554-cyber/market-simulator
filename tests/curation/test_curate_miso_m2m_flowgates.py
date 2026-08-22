"""Tests for the miso-m2m-flowgates intake on a tiny synthetic fixture.

Writes a four-row raw ``M2M_Settlement_srw_2025.csv.gz`` covering the source's
combos (MISO-monitored vs PJM, PJM-monitored, SWPP-monitored, "NO RTO" with
NaNs; hour-ending labels 1 and "24:00:00") into a tmp raw tree, runs
``curate``, and asserts the written partition is schema-valid, the HE→EST→UTC
conversion is exact, and ``seam_rto`` derives the non-MISO RTO of every pair.
CLEAN_DIR is redirected to a tmp dir so the real tree is never touched.
"""

import gzip
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_miso_m2m_flowgates as curate_m2m
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_CSV = """HOUR_ENDING,FLOWGATE_ID,MONITORING_RTO,CP_RTO,FLOWGATE_NAME,MISO_SHADOW_PRICE,MISO_MKT_FLOW,MISO_FFE,CP_SHADOW_PRICE,CP_MKT_FLOW,CP_FFE,MISO_CREDIT,CP_CREDIT
2025-01-01 1:00:00,25833,MISO,SWPP,SplitRock_TR11_FLO_SplitRock_TR10,0,138,237,0,-11,111,0,0
2025-01-01 24:00:00,30639,SWPP,MISO,TMP484_PIRKEY_345_138kV,12.5,-183,195,8.1,0,0,-42.0,0
2025-07-15 18:00:00,556,PJM,MISO,StLine_Roxanna138_flo_WiltonCenter,101.0,56,214.5,250.0,0,0,1500.25,0
2025-07-15 19:00:00,53,NO RTO,PJM,AEP_DOM_flo_Pruntytown_MtStorm500kV,0,81,,,,,0,0
"""


def _write_fixture(raw_root: Path, year: int = 2025, body: str = _CSV) -> Path:
    out_dir = raw_root / "miso-m2m-flowgates"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"M2M_Settlement_srw_{year}.csv.gz"
    with gzip.open(path, "wt") as f:
        f.write(body)
    return path


class TestCurateMisoM2mFlowgates(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self.csv = _write_fixture(self.raw_root)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_hour_ending_to_est_and_utc(self) -> None:
        """HE k EST maps to hour-beginning EST = date+(k-1)h; UTC = +5h."""
        df = curate_m2m.build_year_frame(self.csv, 2025)
        by_fg = df.set_index("flowgate_id")
        # HE 1 on Jan 1 -> EST 2025-01-01 00:00, UTC 05:00.
        self.assertEqual(
            by_fg.loc[25833, "interval_start_est"], pd.Timestamp("2025-01-01 00:00")
        )
        self.assertEqual(
            by_fg.loc[25833, "interval_start_utc"],
            pd.Timestamp("2025-01-01 05:00", tz="UTC"),
        )
        # HE 24 ("24:00:00") on Jan 1 -> EST 23:00, UTC next-day 04:00.
        self.assertEqual(
            by_fg.loc[30639, "interval_start_est"], pd.Timestamp("2025-01-01 23:00")
        )
        self.assertEqual(
            by_fg.loc[30639, "interval_start_utc"],
            pd.Timestamp("2025-01-02 04:00", tz="UTC"),
        )

    def test_seam_rto_is_the_non_miso_party(self) -> None:
        """seam_rto = counterparty unless MISO, else the monitoring RTO."""
        df = curate_m2m.build_year_frame(self.csv, 2025)
        seam = df.set_index("flowgate_id")["seam_rto"]
        self.assertEqual(seam.loc[25833], "SWPP")  # MISO-monitored vs SWPP
        self.assertEqual(seam.loc[30639], "SWPP")  # SWPP-monitored
        self.assertEqual(seam.loc[556], "PJM")  # PJM-monitored
        self.assertEqual(seam.loc[53], "PJM")  # NO RTO vs PJM

    def test_curate_writes_valid_partition(self) -> None:
        """The per-year partition writes through the seam and re-validates."""
        written = curate_m2m.curate(raw_root=self.raw_root, years=[2025])
        self.assertEqual(len(written), 1)
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "miso-m2m-flowgates")
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 4)
        self.assertEqual(str(df["interval_start_utc"].dt.tz), "UTC")
        # Answer-class numerics round-trip; NO-RTO NaNs survive as nulls.
        self.assertAlmostEqual(
            df.loc[df.flowgate_id == 556, "miso_credit_usd"].item(), 1500.25
        )
        self.assertTrue(
            df.loc[df.flowgate_id == 53, "cp_shadow_price_usd_mwh"].isna().all()
        )

    def test_rejects_rows_dated_outside_year(self) -> None:
        """A mirror carrying rows outside its labelled year fails loudly."""
        bad = _CSV + "2024-12-31 5:00:00,999,MISO,PJM,X,0,1,2,0,3,4,0,0\n"
        csv = _write_fixture(self.raw_root, body=bad)
        with self.assertRaises(ValueError):
            curate_m2m.build_year_frame(csv, 2025)

    def test_rejects_duplicate_flowgate_hours(self) -> None:
        """Duplicate (flowgate, hour) rows fail loudly."""
        dup = _CSV + "2025-01-01 1:00:00,25833,MISO,SWPP,SplitRock,0,1,2,0,3,4,0,0\n"
        csv = _write_fixture(self.raw_root, body=dup)
        with self.assertRaises(ValueError):
            curate_m2m.build_year_frame(csv, 2025)

    def test_missing_mirror_is_skipped(self) -> None:
        """A year with no mirror is skipped, not an error."""
        written = curate_m2m.curate(raw_root=self.raw_root, years=[2023, 2025])
        self.assertEqual(len(written), 1)


if __name__ == "__main__":
    unittest.main()
