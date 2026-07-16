"""Tests for the maxgen-events intake on a tiny synthetic fixture.

Writes a minimal unified MISO CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and the reconciliation (EST->UTC
endpoint conversion, dtype coercion, sort order) is correct. NOT a full-data
run: CLEAN_DIR is redirected to a tmp dir (as in tests/test_curate_outages.py)
so it never touches the real tree. Also covers the vocabulary guards, the
inverted-window guard and the skip-empty path — trivial case (1 row) first,
then the committed 2023-2025 registry is smoke-parsed from the real raw tree
(read-only) so the hand-curated rows always conform.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_maxgen_events as curate_mge
from scripts.lib import clean_io
from scripts.lib import maxgen_events as mge
from scripts.lib.clean_io import paths, validate_clean

# One hour-precision row exercising the EST->UTC conversion (14:00 EST =
# 19:00 UTC) plus one day-precision row.
_MISO_CSV = """iso,region,level,start_local,end_local,declared_precision,source_url,source_doc,accessed,notes
MISO,footprint,maxgen_alert,2025-07-28 14:00,2025-07-28 22:00,hour,https://example.test/q.pdf,"IMM quarterly p.23",2026-07-16,stated hours
MISO,midwest,maxgen_event_step1,2025-06-23 00:00,2025-06-23 23:59,day,https://example.test/som.pdf,"SOM p.14",2026-07-16,
"""


def _write_miso_fixture(raw_root: Path, csv: str = _MISO_CSV) -> None:
    d = mge.raw_dir_for("MISO", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "miso.csv").write_text(csv)


class TestCurateMaxgenEvents(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        # Redirect CLEAN_DIR so writes never touch the repo.
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_trivial_roundtrip_and_est_to_utc(self) -> None:
        """1-ISO fixture: written partition validates; EST+5h = UTC."""
        _write_miso_fixture(self.raw_root)
        written = curate_mge.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(len(written), 1, "expected one MISO partition")
        validate_clean(written[0])
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 2)
        # Sorted by start_utc: the June day-row first, then the July hour-row.
        self.assertEqual(list(df["level"]), ["maxgen_event_step1", "maxgen_alert"])
        alert = df[df["level"] == "maxgen_alert"].iloc[0]
        self.assertEqual(alert["start_utc"], pd.Timestamp("2025-07-28 19:00", tz="UTC"))
        self.assertEqual(alert["end_utc"], pd.Timestamp("2025-07-29 03:00", tz="UTC"))
        self.assertEqual(alert["declared_precision"], "hour")

    def test_vocab_guards(self) -> None:
        """Unknown level / region / precision and inverted windows all raise."""
        bad_rows = [
            _MISO_CSV.replace("maxgen_alert", "conservative_operations"),
            _MISO_CSV.replace("footprint", "narnia"),
            _MISO_CSV.replace(",hour,", ",minute,"),
            _MISO_CSV.replace("2025-07-28 22:00", "2025-07-28 13:00"),
        ]
        for csv in bad_rows:
            _write_miso_fixture(self.raw_root, csv)
            with self.assertRaises(ValueError):
                curate_mge.curate(raw_root=self.raw_root, isos=["MISO"])

    def test_missing_csv_skips(self) -> None:
        """An ISO whose raw CSV has not landed yields no partition, no error."""
        written = curate_mge.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(written, [])

    def test_committed_registry_parses(self) -> None:
        """The real hand-curated MISO registry conforms (read-only smoke)."""
        real_raw = paths.RAW_DIR
        if not (mge.raw_dir_for("MISO", real_raw) / "miso.csv").is_file():
            self.skipTest("committed MISO registry not present")
        df = mge.parse_iso("MISO", real_raw)
        self.assertGreaterEqual(len(df), 9)
        # Every committed row cites a primary document (F4 discipline).
        self.assertFalse(df["source_url"].isna().any())
        self.assertFalse(df["source_doc"].isna().any())
        # The registry window is 2023-2025 (rule 22: no out-of-training rows).
        years = df["start_utc"].dt.year
        self.assertTrue(years.between(2023, 2025).all())


if __name__ == "__main__":
    unittest.main()
