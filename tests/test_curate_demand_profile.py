"""Tests for the ``demand-profile`` curation pipeline (scripts/curate_demand_profile.py).

Covers the physical-bounds screen + interpolation repair on a tiny synthetic
fixture (one spike hour, one zero-gap run), the schema-valid clean output, and
that a non-modeled ISO (SPP) is screened/reported but not written. CLEAN_DIR and
the raw fixture path are redirected to temp locations so the suite never
touches the real data tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from scripts import curate_demand_profile as cdp
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _series(base: float, n: int) -> np.ndarray:
    """A gently-varying, always-positive demand series of length n."""
    return base + 5.0 * np.sin(np.linspace(0, 3.0, n))


def _write_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []

    # PJM: 10 clean hours plus one order-of-magnitude spike at hour 5.
    pjm = _series(1000.0, 10)
    pjm[5] = 5.0e8
    for h, mw in enumerate(pjm):
        rows.append(("PJM", 2021, h, float(mw)))

    # CAISO: 10 clean hours plus a 2-hour zero-value gap (missing-data sentinel).
    caiso = _series(500.0, 10)
    caiso[3] = 0.0
    caiso[4] = 0.0
    for h, mw in enumerate(caiso):
        rows.append(("CAISO", 2022, h, float(mw)))

    # SPP: not a modeled ISO — one spike, should be screened but not written.
    spp = _series(300.0, 10)
    spp[0] = 9.0e7
    for h, mw in enumerate(spp):
        rows.append(("SPP", 2023, h, float(mw)))

    df = pd.DataFrame(rows, columns=["iso", "year", "hour", "raw_mw"])
    df["normalized"] = df.groupby(["iso", "year"])["raw_mw"].transform(
        lambda s: s / s.sum()
    )
    df.to_parquet(path, index=False)


class TestScreenAndRepair(unittest.TestCase):
    def test_screen_flags_spike_and_zero(self):
        mw = _series(1000.0, 10)
        mw[2] = 0.0
        mw[7] = 1.0e7
        bad = cdp.screen_physical_bounds(mw)
        self.assertTrue(bad[2])
        self.assertTrue(bad[7])
        self.assertEqual(int(bad.sum()), 2)
        # Untouched hours stay unflagged.
        self.assertFalse(bad[0])
        self.assertFalse(bad[5])

    def test_screen_ignores_normal_seasonal_swing(self):
        # Realistic peak/trough ratio (~2x) must never be flagged.
        mw = np.array([50_000.0, 100_000.0, 60_000.0, 90_000.0])
        bad = cdp.screen_physical_bounds(mw)
        self.assertFalse(bad.any())

    def test_repair_interpolates_interior_gap(self):
        mw = np.array([100.0, 200.0, 0.0, 0.0, 500.0])
        bad = np.array([False, False, True, True, False])
        out = cdp.repair_by_interpolation(mw, bad)
        # Linear interpolation between 200 (idx1) and 500 (idx4).
        self.assertAlmostEqual(out[2], 300.0)
        self.assertAlmostEqual(out[3], 400.0)
        self.assertEqual(out[0], 100.0)
        self.assertEqual(out[4], 500.0)

    def test_repair_no_bad_hours_is_a_no_op(self):
        mw = np.array([1.0, 2.0, 3.0])
        bad = np.zeros(3, dtype=bool)
        out = cdp.repair_by_interpolation(mw, bad)
        np.testing.assert_array_equal(out, mw)


class TestCurateAll(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

        self._orig_raw = cdp._RAW_FILE
        cdp._RAW_FILE = root / "raw" / "eia_demand_profiles.parquet"
        _write_fixture(cdp._RAW_FILE)

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        cdp._RAW_FILE = self._orig_raw
        self._tmp.cleanup()

    def _clean(self, iso: str, year: int) -> pd.DataFrame:
        path = clean_io.paths.clean_path("demand-profile", iso=iso, year=year)
        validate_clean(path)
        return pd.read_parquet(path).sort_values("hour").reset_index(drop=True)

    def test_writes_only_modeled_isos(self):
        written = cdp.curate_all()
        names = {(p.parts[-2], p.name) for p in written}
        self.assertIn(("PJM", "demand-profile_2021.parquet"), names)
        self.assertIn(("CAISO", "demand-profile_2022.parquet"), names)
        self.assertFalse(
            clean_io.paths.clean_path("demand-profile", iso="SPP", year=2023).exists()
        )

    def test_pjm_spike_repaired_and_flagged(self):
        cdp.curate_all()
        df = self._clean("PJM", 2021)
        self.assertTrue(df.loc[5, "repaired"])
        self.assertLess(df.loc[5, "raw_mw"], 2000.0)  # no longer the 5e8 spike
        self.assertEqual(int(df["repaired"].sum()), 1)
        # normalized recomputed from the repaired series, still sums to ~1.
        self.assertAlmostEqual(df["normalized"].sum(), 1.0, places=6)

    def test_caiso_zero_gap_repaired_and_flagged(self):
        cdp.curate_all()
        df = self._clean("CAISO", 2022)
        self.assertTrue(df.loc[3, "repaired"])
        self.assertTrue(df.loc[4, "repaired"])
        self.assertGreater(df.loc[3, "raw_mw"], 0.0)
        self.assertGreater(df.loc[4, "raw_mw"], 0.0)
        self.assertEqual(int(df["repaired"].sum()), 2)

    def test_untouched_hours_not_flagged(self):
        cdp.curate_all()
        df = self._clean("PJM", 2021)
        self.assertFalse(df.loc[0, "repaired"])
        self.assertFalse(df["repaired"].drop(index=5).any())


if __name__ == "__main__":
    unittest.main()
