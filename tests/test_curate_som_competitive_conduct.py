"""Tests for scripts/data/curate_som_competitive_conduct.py.

Trivial fixture first (one ISO, two rows) with a redirected ``CLEAN_DIR``,
then the committed transcription itself: schema validation plus a
provenance-freeze check on the MISO SOM values the coal offer redesign is
grounded on (docs/handoffs/miso-coal-offer-som-redesign-2026-07.md) — the
2023/2024 price-cost mark-up and the coal must-run (self-commitment) start
shares. Those numbers re-derive only when their source data (a new SOM)
updates (CLAUDE.md rule 23), so a silent edit fails here.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.data import curate_som_competitive_conduct as mod  # noqa: E402
from scripts.lib import clean_io  # noqa: E402


class CurateSomCompetitiveConductTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp()
        self._old_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = Path(self._tmp) / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._old_clean
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_trivial_fixture_roundtrip(self) -> None:
        """1 ISO / 2 rows: curate writes a validating partition."""
        raw = Path(self._tmp) / "raw"
        (raw / mod.DATATYPE).mkdir(parents=True)
        (raw / mod.DATATYPE / "som_competitive_conduct.csv").write_text(
            "iso,year,period,fleet_segment,metric,value,unit,"
            "source_doc,source_page,note\n"
            "TESTISO,2024,annual,system,price_cost_markup,-0.025,fraction,"
            "t.pdf,1,\n"
            "TESTISO,2024,annual,coal_regulated,starts,10,count,t.pdf,2,x\n"
        )
        written = mod.curate(raw_root=raw)
        self.assertEqual(len(written), 1)
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 2)
        self.assertEqual(set(df["iso"]), {"TESTISO"})

    def test_committed_transcription_validates(self) -> None:
        """The real raw CSV curates cleanly for MISO."""
        written = mod.curate(isos=["MISO"])
        self.assertEqual(len(written), 1)
        df = pd.read_parquet(written[0])
        # Quarantine (rule 22): train-window years only.
        self.assertTrue(df["year"].between(2023, 2025).all())
        # Key uniqueness on the schema key.
        key = ["iso", "year", "period", "fleet_segment", "metric"]
        self.assertFalse(df.duplicated(subset=key).any())

    def test_miso_grounding_values_frozen(self) -> None:
        """The SOM values the MISO coal offer redesign cites are pinned.

        Source: 2023/2024 MISO SOM Table 7 + Competitive Assessment
        (source_doc/source_page on each row). Re-derive only on a new SOM.
        """
        df = mod.build_frame(clean_io.paths.RAW_DIR)
        miso = df[df["iso"] == "MISO"].set_index(
            ["year", "period", "fleet_segment", "metric"]
        )["value"]

        def v(year: int, seg: str, metric: str) -> float:
            return float(miso.loc[(year, "annual", seg, metric)])

        # Price-cost mark-up ~ 0: the near-cost offer anchor.
        self.assertAlmostEqual(v(2023, "system", "price_cost_markup"), 0.030)
        self.assertAlmostEqual(v(2024, "system", "price_cost_markup"), -0.025)
        # Output gap de minimis (no economic withholding to model).
        self.assertLessEqual(v(2023, "system", "output_gap_share_of_load"), 0.001)
        self.assertLessEqual(v(2024, "system", "output_gap_share_of_load"), 0.001)
        # Self-commitment: must-run share of regulated coal starts
        # (profitable + unprofitable) = 56% (2023) / 53% (2024).
        for year, mr_share in ((2023, 0.56), (2024, 0.53)):
            got = v(year, "coal_regulated", "starts_mustrun_profitable_share") + v(
                year, "coal_regulated", "starts_mustrun_unprofitable_share"
            )
            self.assertAlmostEqual(got, mr_share, places=6)
        # Merchants offer overwhelmingly economically (93% / 74%).
        self.assertAlmostEqual(
            v(2023, "coal_merchant", "starts_econ_offered_share"), 0.93
        )
        self.assertAlmostEqual(
            v(2024, "coal_merchant", "starts_econ_offered_share"), 0.74
        )


if __name__ == "__main__":
    unittest.main()
