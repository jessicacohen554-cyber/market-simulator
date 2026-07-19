"""Tests for the PJM measured generation-outage availability intake.

Covers the derive-script invariants, the two loaders
(:func:`pjm_outages.pjm_outage_mw_series`, :func:`pjm_outages.pjm_dam_availability_series`),
and a loader-resolvability check against the committed per-year CSVs. No LP solve
is run — the committed-artifact checks are the no-LP validation the holdout policy
permits for out-of-training data.
"""

import importlib
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.data import outages, pjm_outages

REPO = Path(__file__).parents[1]
DERIVE = importlib.import_module("scripts.data.derive_pjm_dam_availability")


def _raw_fixture() -> pd.DataFrame:
    """A tiny 2-lead-day, 3-region raw fixture with the invariants exercised."""
    rows = []
    for ex, fc, lead in [
        ("2023-01-01T00:00:00", "2023-01-01T00:00:00", 0),
        ("2023-01-01T00:00:00", "2023-01-02T00:00:00", 1),
    ]:
        for region, tot, pl, mn, fr in [
            # (region, total, planned, maintenance, forced); total == sum, and a
            # negative maintenance (PJM reconciliation artifact) on one row.
            ("Mid Atlantic - Dominion", 1000, 200, -50, 850),
            ("Western", 1500, 300, 100, 1100),
            ("PJM RTO", 2500, 500, 50, 1950),
        ]:
            rows.append(
                {
                    "forecast_execution_date_ept": ex,
                    "forecast_date": fc,
                    "region": region,
                    "total_outages_mw": tot,
                    "planned_outages_mw": pl,
                    "maintenance_outages_mw": mn,
                    "forced_outages_mw": fr,
                }
            )
    return pd.DataFrame(rows)


class DeriveInvariantsTest(unittest.TestCase):
    """The derive build() enforces the structural invariants."""

    def test_build_shapes_and_invariants(self):
        df = DERIVE.build_from_frame(_raw_fixture())
        self.assertEqual(
            set(df["region"]), {"Mid Atlantic - Dominion", "Western", "PJM RTO"}
        )
        self.assertEqual(sorted(df["lead_days"].unique()), [0, 1])
        # Negative maintenance preserved verbatim (not clamped).
        self.assertIn(-50.0, df["maintenance_outages_mw"].tolist())

    def test_rejects_broken_total(self):
        bad = _raw_fixture()
        bad.loc[0, "total_outages_mw"] = 9999  # breaks components == total
        with self.assertRaises(ValueError):
            DERIVE.build_from_frame(bad)


class LoaderTest(unittest.TestCase):
    """The two loaders reshape onto the 8760 clock and fall back cleanly."""

    def setUp(self):
        self._orig = pjm_outages.PJM_DAM_AVAILABILITY_PARQUET
        self._orig_byyear = pjm_outages.PJM_OUTAGE_BYYEAR_DIR
        self._orig_cap = outages._iso_plant_capacity
        pjm_outages.pjm_outage_mw_series.cache_clear()
        pjm_outages.pjm_dam_availability_series.cache_clear()

    def tearDown(self):
        pjm_outages.PJM_DAM_AVAILABILITY_PARQUET = self._orig
        pjm_outages.PJM_OUTAGE_BYYEAR_DIR = self._orig_byyear
        outages._iso_plant_capacity = self._orig_cap
        pjm_outages.pjm_outage_mw_series.cache_clear()
        pjm_outages.pjm_dam_availability_series.cache_clear()

    def _point_at_parquet(self, tmp: Path) -> None:
        out = tmp / "pjm-dam-availability.parquet"
        DERIVE.build_from_frame(_raw_fixture()).to_parquet(out, index=False)
        pjm_outages.PJM_DAM_AVAILABILITY_PARQUET = out
        pjm_outages.PJM_OUTAGE_BYYEAR_DIR = tmp / "nonexistent-byyear"
        pjm_outages.pjm_outage_mw_series.cache_clear()
        pjm_outages.pjm_dam_availability_series.cache_clear()

    def _point_at_csv(self, tmp: Path) -> None:
        DERIVE.write_byyear_csvs(DERIVE.build_from_frame(_raw_fixture()), tmp)
        pjm_outages.PJM_DAM_AVAILABILITY_PARQUET = tmp / "nonexistent.parquet"
        pjm_outages.PJM_OUTAGE_BYYEAR_DIR = tmp
        pjm_outages.pjm_outage_mw_series.cache_clear()
        pjm_outages.pjm_dam_availability_series.cache_clear()

    def test_missing_source_returns_nan(self):
        pjm_outages.PJM_DAM_AVAILABILITY_PARQUET = Path("/nonexistent/x.parquet")
        pjm_outages.PJM_OUTAGE_BYYEAR_DIR = Path("/nonexistent/byyear")
        pjm_outages.pjm_outage_mw_series.cache_clear()
        pjm_outages.pjm_dam_availability_series.cache_clear()
        mw = pjm_outages.pjm_outage_mw_series(2023)
        self.assertTrue(np.isnan(mw).all())
        self.assertEqual(pjm_outages.pjm_dam_availability_series(2023), {})

    def _assert_mw_series(self):
        # forced+maintenance for PJM RTO on Jan 1 (lead 0) = 1950 + 50 = 2000.
        mw = pjm_outages.pjm_outage_mw_series(2023)
        self.assertAlmostEqual(mw[0], 2000.0)  # Jan 1 hour 0
        self.assertAlmostEqual(mw[12], 2000.0)  # still Jan 1
        self.assertTrue(np.isnan(mw[24 * 5]))  # uncovered day -> NaN fallback
        # total type = 2500; forced-only = 1950.
        self.assertAlmostEqual(
            pjm_outages.pjm_outage_mw_series(2023, outage_types=("total",))[0], 2500.0
        )
        self.assertAlmostEqual(
            pjm_outages.pjm_outage_mw_series(2023, outage_types=("forced",))[0], 1950.0
        )

    def test_current_day_actual_from_parquet(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            self._point_at_parquet(Path(d))
            self._assert_mw_series()

    def test_current_day_actual_from_csv_fallback(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            self._point_at_csv(Path(d))
            self._assert_mw_series()

    def test_availability_fraction_and_covered_classes(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            self._point_at_parquet(Path(d))
            # 10,000 MW fossil-thermal capacity across two covered groups; patched
            # on the `outages` module where the loader imports it at call time.
            outages._iso_plant_capacity = lambda iso: {
                (1, "COAL"): 6000.0,
                (2, "CC_REGULAR"): 4000.0,
            }
            pjm_outages.pjm_dam_availability_series.cache_clear()
            av = pjm_outages.pjm_dam_availability_series(2023)
            self.assertEqual(set(av), pjm_outages.PJM_OUTAGE_COVERED_GROUPS)
            # 1 - 2000/10000 = 0.80 on the covered Jan-1 hours.
            self.assertAlmostEqual(av["COAL"][0], 0.80, places=4)
            self.assertTrue(np.isnan(av["COAL"][24 * 5]))  # uncovered -> NaN


class CommittedArtifactTest(unittest.TestCase):
    """Loader-resolvability against the shipped per-year CSVs (no LP solve)."""

    def setUp(self):
        self._orig = pjm_outages.PJM_DAM_AVAILABILITY_PARQUET
        pjm_outages.pjm_outage_mw_series.cache_clear()

    def tearDown(self):
        pjm_outages.PJM_DAM_AVAILABILITY_PARQUET = self._orig
        pjm_outages.pjm_outage_mw_series.cache_clear()

    def test_shipped_csv_resolves(self):
        csv = pjm_outages.PJM_OUTAGE_BYYEAR_DIR / "gen_outages_by_type_2023.csv"
        if not csv.exists():
            self.skipTest("committed per-year CSV not present")
        # Force the CSV path (parquet may exist locally but is gitignored).
        pjm_outages.PJM_DAM_AVAILABILITY_PARQUET = Path("/nonexistent.parquet")
        pjm_outages.pjm_outage_mw_series.cache_clear()
        # 2023 is an in-training year; this only reshapes data, no dispatch.
        mw = pjm_outages.pjm_outage_mw_series(2023)
        self.assertGreater(int(np.isfinite(mw).sum()), 8000)
        self.assertTrue((mw[np.isfinite(mw)] >= 0).all())
        self.assertEqual(len(mw), HOURS_PER_YEAR)


if __name__ == "__main__":
    unittest.main()
