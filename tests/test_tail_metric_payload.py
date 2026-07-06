"""Calibration-page scarcity-tail (C3c) metric: payload helpers + verdict wiring.

The render payload carries the scarcity tail under ``run.years[year].ordc`` as
``{"hoursGt200": {"model": M, "actual": A}}`` — the count of hours whose zonal
LMP exceeds the ISO's threshold (rubric §5: $200, $300 for NYISO/NEISO), stored
under the legacy ``hoursGt200`` key the scorer reads regardless of threshold. For
non-ERCOT ISOs this block was never emitted, so C3c was permanently SKIPPED;
these tests pin the two render helpers (``_tail_hours`` + the actual hourly-LMP
loader) on synthetic frames and confirm ``calibration_verdict.score_price_tail``
(C3c) activates off the emitted payload shape. The ERCOT ORDC path is untouched
and not exercised here (it has its own byte-identity guard).
"""

import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch_tail", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)

from scripts import calibration_verdict as cv  # noqa: E402


class TailHoursTests(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(rch._tail_hours({}, 200.0), 0)

    def test_counts_hours_above_threshold(self):
        # 2 of 4 hours strictly exceed $200.
        z = {"Z": np.array([100.0, 250.0, 200.0, 9999.0])}
        self.assertEqual(rch._tail_hours(z, 200.0), 2)

    def test_max_across_zones_counts_once(self):
        # An hour counts if ANY zone is in scarcity (max across zones), and is
        # counted once even when several zones spike together.
        z = {
            "A": np.array([300.0, 10.0, 10.0]),
            "B": np.array([10.0, 400.0, 500.0]),
        }
        self.assertEqual(rch._tail_hours(z, 200.0), 3)

    def test_threshold_is_per_iso(self):
        # The $300 NYISO/NEISO threshold excludes a $250 spike a $200 ISO counts.
        z = {"Z": np.array([250.0, 350.0])}
        self.assertEqual(rch._tail_hours(z, 200.0), 2)
        self.assertEqual(rch._tail_hours(z, 300.0), 1)

    def test_nans_are_ignored(self):
        # Unpadded/missing hours (NaN) never register as scarcity.
        z = {"Z": np.array([np.nan, 250.0, np.nan])}
        self.assertEqual(rch._tail_hours(z, 200.0), 1)


class ActualHourlyLmpTests(unittest.TestCase):
    def _write(self, tmp, iso, frame):
        frame.to_parquet(tmp / f"actual_lmp_hourly_{iso}.parquet")

    def _patched(self, tmp):
        # Patch CALIBRATION_DIR (the loader imports it at call time) and clear the
        # loader's lru_cache so each case reads the freshly-written temp parquet.
        rch._actual_lmp_hourly.cache_clear()
        return mock.patch("market_sim.config.paths.CALIBRATION_DIR", tmp)

    def test_none_when_file_missing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            with self._patched(tmp):
                self.assertIsNone(rch._actual_lmp_hourly("NOPE", 2024))

    def test_none_when_year_absent(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(
                tmp,
                "TEST",
                pd.DataFrame({"year": [2023], "hour": [0], "rt": [50.0], "da": [40.0]}),
            )
            with self._patched(tmp):
                self.assertIsNone(rch._actual_lmp_hourly("TEST", 2024))

    def test_prefers_rt_sorted_by_hour(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            # Rows out of hour order; rt is preferred over da.
            self._write(
                tmp,
                "TEST",
                pd.DataFrame(
                    {
                        "year": [2024, 2024, 2024],
                        "hour": [2, 0, 1],
                        "rt": [300.0, 10.0, 20.0],
                        "da": [1.0, 2.0, 3.0],
                    }
                ),
            )
            with self._patched(tmp):
                got = rch._actual_lmp_hourly("TEST", 2024)
            np.testing.assert_allclose(got, [10.0, 20.0, 300.0])

    def test_falls_back_to_da_where_rt_nan(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self._write(
                tmp,
                "TEST",
                pd.DataFrame(
                    {
                        "year": [2024, 2024],
                        "hour": [0, 1],
                        "rt": [np.nan, 25.0],
                        "da": [400.0, 5.0],
                    }
                ),
            )
            with self._patched(tmp):
                got = rch._actual_lmp_hourly("TEST", 2024)
            np.testing.assert_allclose(got, [400.0, 25.0])
            # The da-filled scarcity hour is then counted by the tail proxy.
            self.assertEqual(rch._tail_hours({"hub": got}, 300.0), 1)


class TailVerdictWiringTests(unittest.TestCase):
    """C3c activates off the non-ERCOT payload shape build_payload now emits.

    Rubric v2: the gate reads the model count from the payload but the actual
    from the committed DA-expressible tail part (``tail/actual_tail.json``) —
    injected here via ``cv._TAIL_CACHE`` so the tests stay hermetic.
    """

    def _with_tail(self, iso, year, da_gt, rt_gt):
        cv._TAIL_CACHE = {
            iso: {str(year): {"da_gt": da_gt, "rt_gt": rt_gt, "da_coverage": 1.0}}
        }
        self.addCleanup(setattr, cv, "_TAIL_CACHE", None)

    def test_within_band_passes(self):
        self._with_tail("NEISO", 2024, da_gt=100, rt_gt=100)
        ypay = {"ordc": {"hoursGt200": {"model": 80, "actual": 100}}}
        rows = cv.score_price_tail(2024, ypay, "NEISO")
        self.assertEqual(rows[0]["status"], cv.PASS)

    def test_collapsed_tail_fails(self):
        # Model tail collapsed to 0 where the market had scarcity -> FAIL (the
        # expected, truthful energy-only outcome — not to be tuned away).
        self._with_tail("PJM", 2024, da_gt=100, rt_gt=100)
        ypay = {"ordc": {"hoursGt200": {"model": 0, "actual": 100}}}
        rows = cv.score_price_tail(2024, ypay, "PJM")
        self.assertEqual(rows[0]["status"], cv.FAIL)

    def test_skipped_without_ordc(self):
        # No actual file for the ISO-year -> ordc unset -> SKIPPED, never a pass.
        rows = cv.score_price_tail(2024, {"lmp": {}}, "CAISO")
        self.assertEqual(rows[0]["status"], cv.SKIPPED)


if __name__ == "__main__":
    unittest.main()
