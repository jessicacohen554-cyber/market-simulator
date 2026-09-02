"""Tests for the capacity-market-auction-supply intake on a tiny synthetic fixture.

Writes a minimal unified MISO CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and the tidy vocabulary /
metric-category pairing rules hold. CLEAN_DIR is redirected to a tmp dir (as
in tests/curation/test_curate_capacity_market_demand_curve.py) so it never
touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_market_auction_supply as curate_asup
from scripts.lib import capacity_market_auction_supply as asup
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# Trivial case first (one season, one category pair + two ledger rows), per
# docs/testing.md.
_MISO_CSV = """iso,planning_year,season,area,metric,category,value_mw,unit,vintage,source_doc,source_page
MISO,2025-2026,summer,System,offered,generation,121015.6,mw_zrc,PY2025-26 posting,doc.pdf,p.22
MISO,2025-2026,summer,System,cleared,generation,120738.6,mw_zrc,PY2025-26 posting,doc.pdf,p.22
MISO,2025-2026,summer,System,initial_prmr,,135213.4,mw_sac,PY2025-26 posting,doc.pdf,p.18
MISO,2025-2026,summer,North/Central,initial_prmr,,99770.5,mw_sac,PY2025-26 posting,doc.pdf,p.18
"""


def _write_miso_fixture(raw_root: Path, text: str = _MISO_CSV) -> None:
    d = asup.raw_dir_for("MISO", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "miso.csv").write_text(text)


class TestCurateCapacityMarketAuctionSupply(unittest.TestCase):
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

    def test_curate_writes_schema_valid_partition(self) -> None:
        _write_miso_fixture(self.raw_root)
        written = curate_asup.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(len(written), 1, "expected one MISO partition")
        path = written[0]
        self.assertTrue(path.exists())
        validate_clean(path)
        df = pd.read_parquet(path)
        self.assertEqual(len(df), 4)
        self.assertEqual(set(df["iso"]), {"MISO"})
        gen = df[(df["metric"] == "cleared") & (df["category"] == "generation")]
        self.assertEqual(float(gen["value_mw"].iloc[0]), 120_738.6)
        sub = df[(df["area"] == "North/Central") & (df["metric"] == "initial_prmr")]
        self.assertEqual(float(sub["value_mw"].iloc[0]), 99_770.5)
        self.assertTrue(df.loc[df["metric"] == "initial_prmr", "category"].isna().all())

    def test_missing_csv_skips_iso(self) -> None:
        written = curate_asup.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(written, [])

    def test_vocab_violation_raises(self) -> None:
        bad = _MISO_CSV + (
            "MISO,2025-2026,summer,System,offered,not_a_category,1.0,mw_zrc,v,doc,p\n"
        )
        _write_miso_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_asup.curate(raw_root=self.raw_root, isos=["MISO"])

    def test_ledger_row_with_category_raises(self) -> None:
        bad = _MISO_CSV + (
            "MISO,2025-2026,summer,System,frap,generation,1.0,mw_sac,v,doc,p\n"
        )
        _write_miso_fixture(self.raw_root, bad)
        with self.assertRaises(ValueError):
            curate_asup.curate(raw_root=self.raw_root, isos=["MISO"])

    def test_real_committed_csv_curates_and_reconciles(self) -> None:
        # The committed raw file itself curates cleanly, and the category sums
        # reproduce the published totals (a transcription tripwire).
        repo_raw = Path(__file__).resolve().parents[2] / "data" / "raw"
        df = asup.parse_iso("MISO", repo_raw)
        self.assertGreater(len(df), 150)
        cats = df[
            (df["metric"].isin(["offered", "cleared"])) & (df["category"] != "total")
        ]
        tots = df[
            (df["metric"].isin(["offered", "cleared"])) & (df["category"] == "total")
        ]
        got = cats.groupby(["planning_year", "season", "metric"])["value_mw"].sum()
        for (py, season, metric), total in tots.set_index(
            ["planning_year", "season", "metric"]
        )["value_mw"].items():
            self.assertAlmostEqual(
                float(got.loc[(py, season, metric)]),
                float(total),
                delta=0.35,
                msg=f"{py} {season} {metric}",
            )
        # The S-123 registry operands live in this file (their full series).
        s25 = df[
            (df["planning_year"] == "2025-2026")
            & (df["season"] == "summer")
            & (df["metric"] == "cleared")
        ].set_index("category")["value_mw"]
        self.assertEqual(float(s25.loc["external_resources"]), 3_505.9)
        self.assertEqual(float(s25.loc["demand_resources"]), 9_004.4)
