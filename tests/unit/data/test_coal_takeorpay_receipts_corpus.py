"""Guard the ``--from-receipts-corpus`` source of the coal take-or-pay deriver.

Lane NWPP-43 (2026-09-20) found ``coal_takeorpay_NWPP.csv`` absent while the file
exists for all seven other ISOs, which made ``coal_takeorpay_from_data`` and
``coal_committed_takeorpay_regulated`` silently INERT for NWPP — the NWPP-41
defect class (an underived artifact making a real mechanism do nothing). It could
not be derived because ``scripts/data/derive_coal_takeorpay.py`` reads the
``f923_*.zip`` releases, which are NOT committed to the repo, while the same EIA-923
Page 5 lives in the COMMITTED ``data/raw/coal-receipts/`` corpus.

These tests pin the two properties that make the new source safe:

1. it is **column-for-column equivalent** to the zip source — the same ``_RENAME``
   map, so ``_takeorpay_table`` cannot tell them apart; and
2. it is **opt-in**, so every other ISO's derive path is byte-identical and no
   committed table moves (rule 23 ``[R-FROZEN-DERIVE]``: a table re-derives only
   when its SOURCE data changes).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.data import derive_coal_takeorpay as dct  # noqa: E402
from scripts.data.process_f923_fuel_costs import _RENAME  # noqa: E402

CORPUS = REPO / "data" / "raw" / "coal-receipts"


class ReceiptsCorpusSourceTest(unittest.TestCase):
    """The committed corpus is a drop-in for the uncommitted zips."""

    def setUp(self) -> None:
        if not sorted(CORPUS.glob("coal_receipts_*.csv")):
            self.skipTest("coal-receipts corpus not hydrated in this checkout")

    def test_corpus_frames_carry_the_canonical_receipt_columns(self) -> None:
        """Every column ``_takeorpay_table`` reads is present and canonically named."""
        frames = dct._load_receipts_corpus(REPO / "data" / "raw", None)
        self.assertTrue(frames, "corpus produced no frames")
        for frame in frames:
            for col in ("plant_id", "quantity", "fuel_group", "purchase_type"):
                self.assertIn(col, frame.columns)
            # No raw Page-5 header survives un-renamed.
            self.assertFalse(
                set(frame.columns) & set(_RENAME),
                "a raw EIA-923 header leaked through the rename",
            )

    def test_year_filter_selects_release_years(self) -> None:
        """``--year`` narrows the corpus exactly as it narrows the zip list."""
        all_frames = dct._load_receipts_corpus(REPO / "data" / "raw", None)
        one = dct._load_receipts_corpus(REPO / "data" / "raw", [2024])
        self.assertEqual(len(one), 1)
        self.assertLess(len(one), len(all_frames))
        self.assertEqual(set(one[0]["year"].unique()), {2024})

    def test_missing_release_year_is_a_hard_error_not_an_empty_table(self) -> None:
        """A year the corpus does not hold STOPS, rather than writing 0 plants."""
        with self.assertRaises(SystemExit):
            dct._load_receipts_corpus(REPO / "data" / "raw", [1990])

    def test_absent_corpus_is_a_hard_error_naming_the_remedy(self) -> None:
        """Pointing at a root with no corpus explains both ways forward."""
        with self.assertRaises(SystemExit) as ctx:
            dct._load_receipts_corpus(Path("/nonexistent-raw-root"), None)
        msg = str(ctx.exception)
        self.assertIn("fetch_eia923_coal_receipts.py", msg)
        self.assertIn("--from-receipts-corpus", msg)

    def test_source_is_opt_in(self) -> None:
        """``from_receipts_corpus`` defaults False, so no existing table moves."""
        import inspect

        sig = inspect.signature(dct._takeorpay_table)
        self.assertIs(sig.parameters["from_receipts_corpus"].default, False)


class NwppTableTest(unittest.TestCase):
    """The NWPP table this lane derived, pinned to its measured values."""

    TABLE = REPO / "data" / "raw" / "_processed-legacy" / "coal_takeorpay_NWPP.csv"

    def setUp(self) -> None:
        if not self.TABLE.exists():
            self.skipTest("coal_takeorpay_NWPP.csv not present in this checkout")
        self.df = pd.read_csv(self.TABLE)

    def test_schema_matches_the_other_isos(self) -> None:
        other = REPO / "data" / "raw" / "_processed-legacy" / "coal_takeorpay_PJM.csv"
        if not other.exists():
            self.skipTest("no sibling table to compare against")
        self.assertEqual(list(self.df.columns), list(pd.read_csv(other).columns))

    def test_shares_are_proper_fractions_that_sum_to_one(self) -> None:
        self.assertTrue(
            ((self.df.contract_share >= 0) & (self.df.contract_share <= 1)).all()
        )
        for c, s in zip(self.df.contract_share, self.df.spot_share):
            self.assertAlmostEqual(c + s, 1.0, places=4)

    def test_nwpp_coal_is_overwhelmingly_contracted(self) -> None:
        """The measured finding: NWPP coal is 98-100 % contract at most plants.

        This is what makes the regulated committed band a live question — the
        model bids that fuel at full spot SRMC today.
        """
        self.assertGreaterEqual(len(self.df), 13)
        self.assertAlmostEqual(
            float(self.df.loc[self.df.plant_code == 6165, "contract_share"].iloc[0]),
            0.9816,
            places=4,
        )
        self.assertAlmostEqual(
            float(self.df.loc[self.df.plant_code == 8069, "contract_share"].iloc[0]),
            0.9888,
            places=4,
        )
        # North Valmy is the spot-heavy counter-example that keeps the arm two-sided.
        self.assertAlmostEqual(
            float(self.df.loc[self.df.plant_code == 8224, "contract_share"].iloc[0]),
            0.5611,
            places=4,
        )


if __name__ == "__main__":
    unittest.main()
