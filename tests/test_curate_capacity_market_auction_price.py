"""Tests for the capacity-market-auction-price intake on a tiny synthetic fixture.

Writes a minimal unified PJM CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid, defaults (season/area_type/
auction_round) apply correctly, and the delivery-year <= 2026/27 quarantine
cutoff is enforced. CLEAN_DIR is redirected to a tmp dir.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_capacity_market_auction_price as curate_ap
from scripts.lib import capacity_market_auction_price as ap
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# RTO + one LDA row across two delivery years, season/area_type left blank to
# test defaults. The last row is a future 2027/2028 delivery year that must
# never reach a real curate() call (tested separately via validate_tidy).
_PJM_CSV = """iso,delivery_year,season,area,area_type,auction_round,clearing_price,price_unit,cleared_mw,source_doc,source_page
PJM,2025/2026,,RTO,rto,,269.92,usd_per_mw_day,140000,bra-report-2025-2026.pdf,Table 1
PJM,2025/2026,,MAAC,,,300.00,usd_per_mw_day,9000,bra-report-2025-2026.pdf,Table 2
PJM,2026/2027,,RTO,rto,,329.17,usd_per_mw_day,,bra-report-2026-2027.pdf,Table 1
"""


def _write_pjm_fixture(raw_root: Path) -> None:
    d = ap.raw_dir_for("PJM", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "pjm.csv").write_text(_PJM_CSV)


class TestCurateCapacityMarketAuctionPrice(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_pjm(self) -> pd.DataFrame:
        _write_pjm_fixture(self.raw_root)
        written = curate_ap.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1, "expected one PJM partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-market-auction-price")
        return pd.read_parquet(path)

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(set(df["iso"]), {"PJM"})
        self.assertEqual(list(df.columns), list(ap.CANONICAL_COLUMNS))

    def test_defaults_applied(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(set(df["season"]), {"annual"})
        self.assertEqual(set(df["auction_round"]), {"base_residual_auction"})
        maac = df[df["area"] == "MAAC"]
        self.assertEqual(list(maac["area_type"]), ["lda"])

    def test_values(self) -> None:
        df = self._curate_pjm()
        rto = df[(df["area"] == "RTO") & (df["delivery_year"] == "2025/2026")]
        self.assertEqual(rto["clearing_price"].iloc[0], 269.92)
        self.assertEqual(rto["cleared_mw"].iloc[0], 140000.0)

    def test_delivery_year_beyond_cutoff_rejected(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "delivery_year": ["2027/2028"],
                "season": ["annual"],
                "area": ["RTO"],
                "area_type": ["rto"],
                "auction_round": ["base_residual_auction"],
                "clearing_price": [300.0],
                "price_unit": ["usd_per_mw_day"],
                "cleared_mw": [pd.NA],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            ap.validate_tidy(ap.finalize(bad))

    def test_delivery_year_start_helper(self) -> None:
        self.assertEqual(ap.delivery_year_start("2026/2027"), 2026)
        self.assertEqual(ap.delivery_year_start("2025"), 2025)
        self.assertIsNone(ap.delivery_year_start(""))

    def test_both_null_row_rejected(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "delivery_year": ["2026/2027"],
                "season": ["annual"],
                "area": ["RTO"],
                "area_type": ["rto"],
                "auction_round": ["base_residual_auction"],
                "clearing_price": [pd.NA],
                "price_unit": [pd.NA],
                "cleared_mw": [pd.NA],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            ap.validate_tidy(ap.finalize(bad))

    def test_empty_iso_is_skipped(self) -> None:
        written = curate_ap.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(written, [])

    def test_unregistered_iso_raises(self) -> None:
        with self.assertRaises(ValueError):
            curate_ap.curate(raw_root=self.raw_root, isos=["NOTANISO"])

    def test_pjm_registered(self) -> None:
        registry = ap.load_registry()
        self.assertIn("PJM", registry)
        self.assertEqual(registry["PJM"].default_area_type, "lda")


if __name__ == "__main__":
    unittest.main()
