"""Tests for the transfer-constraint-binding intake on a tiny synthetic fixture.

Writes a minimal MISO pbc consolidated file (verbatim source layout, trailing
comma and all) into a tmp raw tree, runs ``curate``, and asserts the written
Parquet is schema-valid and the parse (EST->UTC fixed offset, direction
normalization, curve/override columns, key dedupe) is correct. NOT a
full-data run: CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_outages.py) so it never touches the real tree.
"""

import unittest
from gzip import open as gzopen
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_transfer_constraint_binding as curate_tcb
from scripts.lib import clean_io
from scripts.lib import transfer_constraint_binding as tcb
from scripts.lib.clean_io import validate_clean

# Verbatim source layout (trailing comma = the posted 15th empty field). One
# duplicate row (must dedupe), both directions, one override row with the
# 2023-04-16 emergency $3,000 curve variant, one DA-style 999999 sentinel.
_HEADER = (
    "MARKET_HOUR_EST, CONSTRAINT_NAME, PRELIMINARY_SHADOW_PRICE, CURVETYPE,"
    " BP1, PC1, BP2, PC2, BP3, PC3, BP4, PC4, OVERRIDE, REASON"
)
_RT_2023_ROWS = [
    "07/14/2023 05:25:00,RDT_SO_MW (South_North),-7.56,PERCENT,100,40,102,500,200,500,,,0,,",
    "07/14/2023 05:25:00,RDT_SO_MW (South_North),-7.56,PERCENT,100,40,102,500,200,500,,,0,,",
    "04/16/2023 04:05:00,RDT_MW_SO (North_South),-4.47,PERCENT,100,40,102,3000,200,3000,,,1,System conditions require override to effectively manage within target,",
]
_DA_2023_ROWS = [
    "07/16/2023 16:00:00,RDT_SO_MW (South_North),-40,PERCENT,100,40,102,500,200,500,999999,,0,,",
]


def _write_fixture(raw_root: Path) -> None:
    d = raw_root / tcb.DATATYPE / "MISO"
    d.mkdir(parents=True, exist_ok=True)
    for name, rows in (
        ("miso_pbc_rt_2023.csv.gz", _RT_2023_ROWS),
        ("miso_pbc_da_2023.csv.gz", _DA_2023_ROWS),
    ):
        with gzopen(d / name, "wt") as fh:
            fh.write(_HEADER + "\n")
            for r in rows:
                fh.write(r + "\n")


class TestCurateTransferConstraintBinding(unittest.TestCase):
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
        written = curate_tcb.curate(raw_root=self.raw_root, isos=["MISO"], years=[2023])
        self.assertEqual(len(written), 2, "expected da+rt 2023 partitions")
        out = {}
        for path in written:
            schema = validate_clean(path)
            self.assertEqual(schema.datatype, tcb.DATATYPE)
            df = pd.read_parquet(path)
            out[df["market"].iloc[0]] = df
        return out

    def test_parse_dedupe_directions_and_timestamps(self) -> None:
        frames = self._curate()
        rt = frames["rt"]
        # Duplicate verbatim row collapses on the schema key.
        self.assertEqual(len(rt), 2)
        self.assertEqual(list(rt.columns), list(tcb.CANONICAL_COLUMNS))
        self.assertEqual(set(rt["direction"]), {"S_to_N", "N_to_S"})
        s2n = rt[rt["direction"] == "S_to_N"].iloc[0]
        # EST (UTC-5 fixed, year-round) -> UTC.
        self.assertEqual(
            s2n["interval_start_utc"],
            pd.Timestamp("2023-07-14 10:25:00", tz="UTC"),
        )
        self.assertEqual(s2n["interval_start_est"], pd.Timestamp("2023-07-14 05:25:00"))
        self.assertAlmostEqual(s2n["shadow_price_usd_mwh"], -7.56)
        self.assertFalse(bool(s2n["override"]))

    def test_override_and_emergency_curve_variant(self) -> None:
        rt = self._curate()["rt"]
        n2s = rt[rt["direction"] == "N_to_S"].iloc[0]
        self.assertTrue(bool(n2s["override"]))
        self.assertIn("override", n2s["override_reason"])
        self.assertAlmostEqual(n2s["pc2_usd_mwh"], 3000.0)
        self.assertAlmostEqual(n2s["bp1_pct"], 100.0)

    def test_da_sentinel_and_step_plateau(self) -> None:
        da = self._curate()["da"]
        self.assertEqual(len(da), 1)
        row = da.iloc[0]
        # -40 = the first TCDC step's plateau (flow in real violation).
        self.assertAlmostEqual(row["shadow_price_usd_mwh"], -40.0)
        self.assertAlmostEqual(row["bp4_pct"], 999999.0)
        self.assertTrue(pd.isna(row["pc4_usd_mwh"]))

    def test_absent_year_skipped(self) -> None:
        _write_fixture(self.raw_root)
        written = curate_tcb.curate(raw_root=self.raw_root, isos=["MISO"], years=[2024])
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
