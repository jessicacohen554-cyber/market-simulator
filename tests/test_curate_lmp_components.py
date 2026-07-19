"""Tests for the lmp-components intake on a tiny synthetic fixture.

Writes a minimal MISO D6-style hub staging (verbatim layout: one row per
(date, node, component) with he01..he24 columns) into a tmp raw tree, runs
``curate``, and asserts the written Parquet is schema-valid and the parse
(EST->UTC fixed offset, component pivot, blank-cell nulls, MEC identity)
is correct. NOT a full-data run: CLEAN_DIR is redirected to a tmp dir (as
in tests/test_curate_transfer_constraint_binding.py) so it never touches
the real tree.
"""

import unittest
from gzip import open as gzopen
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_lmp_components as curate_lc
from scripts.lib import clean_io
from scripts.lib import lmp_components as lc
from scripts.lib.clean_io import validate_clean

# Staged-layout header (fetch_miso_hub_lmp.py): date,node,type,value,he01..he24.
_HEADER = "date,node,type,value," + ",".join(f"he{h:02d}" for h in range(1, 25))


def _row(date: str, node: str, value: str, base: float, step: float = 0.0) -> str:
    """One staged row with he01..he24 = base + step*(he-1)."""
    cells = ",".join(f"{base + step * h:.2f}" for h in range(24))
    return f"{date},{node},Hub,{value},{cells}"


# Two hubs, one day. MEC identity holds by construction: for every hour,
# LMP - MCC - MLC is the same 20.00 for both hubs (INDIANA carries the
# congestion/loss premium in its components, not in the implied MEC).
_DA_2023_ROWS = [
    _row("2023-01-01", "INDIANA.HUB", "LMP", 25.00, 1.0),
    _row("2023-01-01", "INDIANA.HUB", "MCC", 3.00, 1.0),
    _row("2023-01-01", "INDIANA.HUB", "MLC", 2.00),
    _row("2023-01-01", "ILLINOIS.HUB", "LMP", 21.50, 1.0),
    _row("2023-01-01", "ILLINOIS.HUB", "MCC", 0.50, 1.0),
    _row("2023-01-01", "ILLINOIS.HUB", "MLC", 1.00),
]

# RT staging with one blank cell (he02 of the MCC row) — must become null,
# never imputed.
_RT_BLANK = "2023-01-01,INDIANA.HUB,Hub,MCC,1.00,," + ",".join(
    "1.00" for _ in range(22)
)
_RT_2023_ROWS = [
    _row("2023-01-01", "INDIANA.HUB", "LMP", 30.00),
    _RT_BLANK,
    _row("2023-01-01", "INDIANA.HUB", "MLC", 2.00),
]


def _write_fixture(raw_root: Path) -> None:
    d = raw_root / "lmp-data" / "MISO"
    d.mkdir(parents=True, exist_ok=True)
    for name, rows in (
        ("miso_hub_lmp_2023_da.csv.gz", _DA_2023_ROWS),
        ("miso_hub_lmp_2023_rt.csv.gz", _RT_2023_ROWS),
    ):
        with gzopen(d / name, "wt") as fh:
            fh.write(_HEADER + "\n")
            for r in rows:
                fh.write(r + "\n")


class TestCurateLmpComponents(unittest.TestCase):
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

    def _curate(self) -> dict[str, pd.DataFrame]:
        _write_fixture(self.raw_root)
        written = curate_lc.curate(raw_root=self.raw_root, isos=["MISO"], years=[2023])
        self.assertEqual(len(written), 2, "expected da+rt 2023 partitions")
        out = {}
        for path in written:
            schema = validate_clean(path)
            self.assertEqual(schema.datatype, lc.DATATYPE)
            df = pd.read_parquet(path)
            out[df["market"].iloc[0]] = df
        return out

    def test_pivot_timestamps_and_values(self) -> None:
        da = self._curate()["da"]
        # 2 hubs x 24 hours, components pivoted wide.
        self.assertEqual(len(da), 48)
        self.assertEqual(list(da.columns), list(lc.CANONICAL_COLUMNS))
        ind = da[da["node"] == "INDIANA.HUB"].sort_values("interval_start_utc")
        # HE1 EST (hour-beginning 2023-01-01 00:00 EST) -> 05:00 UTC.
        self.assertEqual(
            ind["interval_start_utc"].iloc[0],
            pd.Timestamp("2023-01-01 05:00:00", tz="UTC"),
        )
        self.assertEqual(
            ind["interval_start_est"].iloc[0], pd.Timestamp("2023-01-01 00:00:00")
        )
        # he01 = base (step*0): LMP 25.00, MCC 3.00, MLC 2.00.
        self.assertAlmostEqual(ind["lmp_usd_per_mwh"].iloc[0], 25.00)
        self.assertAlmostEqual(ind["mcc_usd_per_mwh"].iloc[0], 3.00)
        self.assertAlmostEqual(ind["mlc_usd_per_mwh"].iloc[0], 2.00)
        # he24 of the stepped rows: 25 + 23 = 48 (LMP), 3 + 23 = 26 (MCC).
        self.assertAlmostEqual(ind["lmp_usd_per_mwh"].iloc[23], 48.00)
        self.assertAlmostEqual(ind["mcc_usd_per_mwh"].iloc[23], 26.00)

    def test_mec_identity_on_fixture(self) -> None:
        da = self._curate()["da"]
        spread = lc.mec_identity_spread(da)
        self.assertEqual(len(spread), 24)
        self.assertLessEqual(float(spread.max()), lc.MEC_IDENTITY_TOLERANCE_USD_MWH)
        # And the implied MEC really is the constructed 20.00 everywhere.
        mec = da["lmp_usd_per_mwh"] - da["mcc_usd_per_mwh"] - da["mlc_usd_per_mwh"]
        self.assertTrue((mec.round(2) == 20.00).all())

    def test_blank_cell_stays_null(self) -> None:
        rt = self._curate()["rt"]
        ind = rt[rt["node"] == "INDIANA.HUB"].sort_values("interval_start_utc")
        # he02 blank MCC -> null; LMP/MLC of that hour still present.
        self.assertTrue(pd.isna(ind["mcc_usd_per_mwh"].iloc[1]))
        self.assertAlmostEqual(ind["lmp_usd_per_mwh"].iloc[1], 30.00)
        self.assertAlmostEqual(ind["mlc_usd_per_mwh"].iloc[1], 2.00)

    def test_out_of_train_year_refused(self) -> None:
        _write_fixture(self.raw_root)
        with self.assertRaises(SystemExit):
            curate_lc.curate(raw_root=self.raw_root, isos=["MISO"], years=[2022])

    def test_absent_year_skipped(self) -> None:
        _write_fixture(self.raw_root)
        written = curate_lc.curate(raw_root=self.raw_root, isos=["MISO"], years=[2024])
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
