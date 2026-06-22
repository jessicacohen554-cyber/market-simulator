"""Calibration-page fossil CO2 metric: payload helper and C5a verdict wiring.

The render payload carries a ``co2`` block on both the benchmark side
(``bench[year].co2.egrid``) and the model side (``run.years[year].co2.model``),
keyed exactly as ``calibration_verdict.score_co2`` (C5a) reads them. These tests
pin the TWh x tonnes/MWh -> Mt unit contract of ``_fossil_co2`` and confirm the
verdict activates off that payload shape (it was SKIPPED for want of an actual).
"""

import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch_co2", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)

from scripts import calibration_verdict as cv  # noqa: E402


class FossilCo2HelperTests(unittest.TestCase):
    def test_twh_times_intensity_is_mt(self):
        # 100 TWh coal @ 1.0 t/MWh = 100 Mt; 50 TWh CC @ 0.4 = 20 Mt.
        total, by = rch._fossil_co2(
            {"COAL_BIT": 100.0, "CC_REGULAR": 50.0},
            {"COAL_BIT": 1.0, "CC_REGULAR": 0.4},
        )
        self.assertAlmostEqual(total, 120.0)
        self.assertEqual(by, {"COAL_BIT": 100.0, "CC_REGULAR": 20.0})

    def test_classes_without_intensity_dropped(self):
        # A non-fossil class (no intensity) contributes nothing.
        total, by = rch._fossil_co2({"COAL_BIT": 10.0, "wind": 99.0}, {"COAL_BIT": 1.0})
        self.assertAlmostEqual(total, 10.0)
        self.assertNotIn("wind", by)


class Co2VerdictWiringTests(unittest.TestCase):
    def test_c5a_activates_off_payload(self):
        ypay = {"co2": {"model": 172.0}}
        ybench = {"co2": {"egrid": 174.0}}
        r = cv.score_co2(2024, ypay, ybench)
        self.assertEqual(r["status"], cv.PASS)

    def test_c5a_fails_outside_band(self):
        r = cv.score_co2(2024, {"co2": {"model": 210.0}}, {"co2": {"egrid": 174.0}})
        self.assertEqual(r["status"], cv.FAIL)

    def test_c5a_skips_without_actual(self):
        r = cv.score_co2(2024, {"co2": {"model": 172.0}}, {})
        self.assertEqual(r["status"], cv.SKIPPED)


if __name__ == "__main__":
    unittest.main()
