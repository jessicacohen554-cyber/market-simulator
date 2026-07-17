"""Tests for the measured MISO reserve-requirement loader
(``data.miso_reserve_requirements``).

Covers the miso-71 Midwest leg (``MISO-Midwest`` = cleared reg+spin+supp over
{North, Central}), the nesting identity (Midwest + South == market), STR
exclusion, and the non-leap 8760 HE-1..24 clock conventions. Trivial synthetic
parquets first (rule "1 gen, 1 zone, 24 h"), then one integration check
against the committed 2025 ASM parquet.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.miso_reserve_requirements import (
    MIDWEST_REGIONS,
    MIDWEST_ZONE,
    SOUTH_ZONE,
    _to_model_hour,
    load_miso_reserve_requirements,
)


def _write_parquet(rows, tmpdir, year=2023):
    df = pd.DataFrame(
        rows, columns=["date", "hour_end_est", "region", "product", "cleared_mw"]
    )
    p = Path(tmpdir) / f"asm_rt_cleared_mw_{year}.parquet"
    df.to_parquet(p)
    return p


class TestMidwestLeg(unittest.TestCase):
    """The Midwest key sums North+Central over the OR products only."""

    #: reg/spin/supp/str MW per region for a single hour-ending. STR (999/888/
    #: 777) must NOT enter any OR sum.
    _VALS = {
        ("North", "reg"): 100, ("North", "spin"): 50,
        ("North", "supp"): 25, ("North", "str"): 999,
        ("Central", "reg"): 80, ("Central", "spin"): 40,
        ("Central", "supp"): 20, ("Central", "str"): 888,
        ("South", "reg"): 30, ("South", "spin"): 15,
        ("South", "supp"): 5, ("South", "str"): 777,
    }  # fmt: skip

    def _rows(self):
        rows = []
        for he in (1, 2):
            for (region, product), mw in self._VALS.items():
                rows.append(["2023-01-01", he, region, product, float(mw)])
        return rows

    def _load(self, td):
        return load_miso_reserve_requirements(
            2023, 2, path=_write_parquet(self._rows(), td)
        )

    def test_midwest_key_present_and_sums_north_central(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._load(td)
        self.assertIn(MIDWEST_ZONE, out)
        # Midwest OR = (100+50+25) + (80+40+20) = 315; STR excluded.
        np.testing.assert_allclose(out[MIDWEST_ZONE], [315.0, 315.0])

    def test_south_leg(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._load(td)
        # South OR = 30+15+5 = 50.
        np.testing.assert_allclose(out[SOUTH_ZONE], [50.0, 50.0])

    def test_nesting_identity_midwest_plus_south_equals_market(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._load(td)
        np.testing.assert_allclose(out[MIDWEST_ZONE] + out[SOUTH_ZONE], out["market"])
        # market OR = 315 + 50 = 365 (all three regions, STR excluded).
        np.testing.assert_allclose(out["market"], [365.0, 365.0])

    def test_str_product_excluded(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._load(td)
        # If STR (999/888) were summed, Midwest would exceed 2,000 MW.
        self.assertTrue(np.all(out[MIDWEST_ZONE] < 400.0))

    def test_midwest_regions_constant(self):
        self.assertEqual(tuple(MIDWEST_REGIONS), ("North", "Central"))


class TestClockConventions(unittest.TestCase):
    """The loader's HE-1..24 EST → non-leap 8760 mapping (shared with the
    market and South legs — the Midwest leg inherits it unchanged)."""

    def test_he_maps_to_hour_of_year(self):
        # HE1 Jan-1 -> 0; HE24 Jan-1 -> 23; HE1 Jan-2 -> 24 (non-leap).
        idx = _to_model_hour(
            pd.Series(["2023-01-01", "2023-01-01", "2023-01-02"]),
            pd.Series([1, 24, 1]),
            2023,
        )
        np.testing.assert_array_equal(idx, [0, 23, 24])

    def test_leap_feb29_dropped_and_march_shifts_back(self):
        idx = _to_model_hour(
            pd.Series(["2024-02-29", "2024-03-01"]), pd.Series([1, 1]), 2024
        )
        self.assertEqual(int(idx[0]), -1)  # Feb 29 sentinel (dropped downstream)
        # Mar-1 sits at non-leap day-of-year 60 (0-indexed 59) -> hour 59*24.
        self.assertEqual(int(idx[1]), 59 * 24)


class TestRealParquetIntegration(unittest.TestCase):
    """Integration against the committed 2025 ASM parquet (design §2b)."""

    def test_2025_midwest_annual_mean_and_nesting(self):
        try:
            out = load_miso_reserve_requirements(2025, 8760)
        except FileNotFoundError:
            self.skipTest("2025 ASM parquet not present")
        # Design §2b: Midwest (N+C) 2025 annual mean = 2,165 MW.
        self.assertAlmostEqual(float(out[MIDWEST_ZONE].mean()), 2165.0, delta=1.0)
        # Nesting identity holds in every fully-covered hour.
        np.testing.assert_allclose(
            out[MIDWEST_ZONE] + out[SOUTH_ZONE], out["market"], atol=1e-6
        )


if __name__ == "__main__":
    unittest.main()
