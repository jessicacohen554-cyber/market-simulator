"""Tests for the nyiso-interface-flows intake on a tiny synthetic fixture.

Writes a two-interface, two-hour raw hourly CSV.GZ into a tmp raw tree, runs
``curate``, and asserts the written partition is schema-valid, the +/-9999 MW
"unbounded" sentinel limits are nulled, and real limits round-trip. CLEAN_DIR
is redirected to a tmp dir so the real tree is never touched.
"""

import gzip
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_nyiso_interface_flows as curate_if
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_HOURLY_CSV = """interface,point_id,interval_start_utc,interval_start_local,flow_mw,positive_limit_mw,negative_limit_mw,n_intervals
CENTRAL EAST - VC,23330,2024-01-01 05:00:00+00:00,2024-01-01 00:00:00,1184.2,2855,-9999,12
CENTRAL EAST - VC,23330,2024-01-01 06:00:00+00:00,2024-01-01 01:00:00,1211.77,2855,-9999,12
SCH - HQ - NY,23324,2024-01-01 05:00:00+00:00,2024-01-01 00:00:00,-789.0,1500,-800,12
SCH - HQ - NY,23324,2024-01-01 06:00:00+00:00,2024-01-01 01:00:00,-777.0,1500,-800,12
"""


def _write_fixture(raw_root: Path) -> None:
    out_dir = raw_root / "NYISO" / "interface-flows"
    out_dir.mkdir(parents=True)
    with gzip.open(out_dir / "NYISO_interface_flows_hourly_2024.csv.gz", "wt") as f:
        f.write(_HOURLY_CSV)


class TestCurateNyisoInterfaceFlows(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        _write_fixture(self.raw_root)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_sentinel_limits_nulled(self) -> None:
        """+/-9999 sentinels become null; real limits survive."""
        csv = (
            self.raw_root
            / "NYISO"
            / "interface-flows"
            / "NYISO_interface_flows_hourly_2024.csv.gz"
        )
        df = curate_if.build_year_frame(csv)
        ce = df[df["interface"] == "CENTRAL EAST - VC"]
        self.assertTrue(ce["negative_limit_mw"].isna().all())
        self.assertTrue((ce["positive_limit_mw"] == 2855.0).all())
        hq = df[df["interface"] == "SCH - HQ - NY"]
        self.assertTrue((hq["negative_limit_mw"] == -800.0).all())

    def test_curate_writes_valid_partition(self) -> None:
        """The per-year partition writes through the seam and re-validates."""
        written = curate_if.curate(raw_root=self.raw_root, years=[2024])
        self.assertEqual(len(written), 1)
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "nyiso-interface-flows")
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 4)
        self.assertEqual(
            df["interval_start_utc"].dt.tz.zone
            if hasattr(df["interval_start_utc"].dt.tz, "zone")
            else str(df["interval_start_utc"].dt.tz),
            "UTC",
        )


if __name__ == "__main__":
    unittest.main()
