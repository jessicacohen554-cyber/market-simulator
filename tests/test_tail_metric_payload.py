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


class SettlementScoringTests(unittest.TestCase):
    """C3c scores the settlement tail (``.overlay``) when the render derived one,
    else the energy-only ``.model`` — G-20a (2026-07-07, owner-approved)."""

    def _with_tail(self, iso, year, da_gt, rt_gt):
        cv._TAIL_CACHE = {
            iso: {str(year): {"da_gt": da_gt, "rt_gt": rt_gt, "da_coverage": 1.0}}
        }
        self.addCleanup(setattr, cv, "_TAIL_CACHE", None)

    def test_overlay_is_scored_when_present(self):
        # Energy-only tail collapsed (model=0) but the settlement tail (overlay)
        # lands in band -> C3c PASSES on the settlement count, not the raw dual.
        self._with_tail("ERCOT", 2024, da_gt=100, rt_gt=100)
        ypay = {"ordc": {"hoursGt200": {"model": 0, "overlay": 90, "actual": 100}}}
        rows = cv.score_price_tail(2024, ypay, "ERCOT")
        self.assertEqual(rows[0]["status"], cv.PASS)
        self.assertEqual(rows[0]["model"], 90.0)  # scored value = overlay count
        self.assertIn("settlement", rows[0]["magnitude"])
        self.assertIn("energy-only 0h", rows[0]["magnitude"])

    def test_overlay_can_fail_when_still_collapsed(self):
        # The overlay is inert (capacity-market keeper) -> settlement tail still 0
        # -> C3c FAILS, exactly as the honest expectation: plumbing does not
        # manufacture a tail where the LP is not tight.
        self._with_tail("PJM", 2024, da_gt=100, rt_gt=100)
        ypay = {"ordc": {"hoursGt200": {"model": 0, "overlay": 0, "actual": 100}}}
        rows = cv.score_price_tail(2024, ypay, "PJM")
        self.assertEqual(rows[0]["status"], cv.FAIL)
        self.assertEqual(rows[0]["model"], 0.0)

    def test_energy_only_scored_when_no_overlay(self):
        # No overlay key (a co-opt / no-sidecar run) -> falls back to the
        # energy-only model count, byte-identical to the pre-G-20a behaviour.
        self._with_tail("MISO", 2024, da_gt=100, rt_gt=100)
        ypay = {"ordc": {"hoursGt200": {"model": 80, "actual": 100}}}
        rows = cv.score_price_tail(2024, ypay, "MISO")
        self.assertEqual(rows[0]["status"], cv.PASS)
        self.assertEqual(rows[0]["model"], 80.0)
        self.assertNotIn("settlement", rows[0]["magnitude"])

    def test_overlay_none_falls_back_to_model(self):
        # An explicit ``overlay: None`` (ISO with no actuals/adder) is treated as
        # absent -> energy-only model is scored.
        self._with_tail("MISO", 2024, da_gt=100, rt_gt=100)
        ypay = {"ordc": {"hoursGt200": {"model": 80, "overlay": None, "actual": 100}}}
        rows = cv.score_price_tail(2024, ypay, "MISO")
        self.assertEqual(rows[0]["model"], 80.0)


class OverlaySidecarIntegrationTests(unittest.TestCase):
    """End-to-end: a derived scarcity.parquet in a bundle -> the render loads it
    for ANY ISO (ERCOT gate removed), builds the ordc block the same way
    build_payload does, and score_price_tail scores the settlement tail."""

    def _bundle(self, tmp, iso, thr):
        # A tiny 5-hour sidecar: energy-only lmp under the threshold everywhere,
        # a published adder that lifts two hours above it -> settlement tail = 2,
        # energy-only tail = 0. This is exactly a run where the LP is not tight
        # but the reserve/scarcity adder fires.
        lmp = np.array([50.0, 60.0, thr - 10, thr - 5, 40.0])
        adder = np.array([0.0, 0.0, 20.0, 20.0, 0.0])
        pd.DataFrame(
            {
                "year": 2024,
                "hour": np.arange(5),
                "scarcity_adder": adder,
                "lmp": lmp,
                "lmp_scarcity": lmp + adder,
            }
        ).to_parquet(tmp / "scarcity.parquet")
        return lmp, adder

    def _ordc_block(self, scar, iso, hours):
        # Mirror build_payload's ISO-agnostic ordc-block construction.
        thr = cv.TAIL_THRESHOLD.get(iso, 200.0)
        lam, lam_s = scar["lmp"], scar["lmp_scarcity"]
        return {
            "hoursGt200": {
                "actual": None,
                "model": rch._gt_count(lam, thr),
                "overlay": rch._gt_count(lam_s, thr),
            }
        }

    def test_pjm_sidecar_scores_settlement_tail(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            thr = cv.TAIL_THRESHOLD["PJM"]  # $200
            self._bundle(tmp, "PJM", thr)
            # The ERCOT-gate removal: the loader returns the overlay for PJM.
            scar = rch._load_scarcity_overlay(tmp, 2024, 5)
            self.assertIsNotNone(scar)
            block = self._ordc_block(scar, "PJM", 5)
            self.assertEqual(block["hoursGt200"]["model"], 0)  # energy-only: no tail
            self.assertEqual(block["hoursGt200"]["overlay"], 2)  # settlement: 2 h
            cv._TAIL_CACHE = {
                "PJM": {"2024": {"da_gt": 2, "rt_gt": 2, "da_coverage": 1.0}}
            }
            self.addCleanup(setattr, cv, "_TAIL_CACHE", None)
            rows = cv.score_price_tail(2024, {"ordc": block}, "PJM")
            self.assertEqual(rows[0]["model"], 2.0)  # scored the settlement count
            self.assertEqual(rows[0]["status"], cv.PASS)

    def test_nyiso_uses_300_threshold(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            thr = cv.TAIL_THRESHOLD["NYISO"]  # $300
            self._bundle(tmp, "NYISO", thr)
            scar = rch._load_scarcity_overlay(tmp, 2024, 5)
            block = self._ordc_block(scar, "NYISO", 5)
            # The $250-ish energy-only hours stay under $300; adder lifts 2 over.
            self.assertEqual(block["hoursGt200"]["model"], 0)
            self.assertEqual(block["hoursGt200"]["overlay"], 2)


class GtCountTests(unittest.TestCase):
    def test_none_series_is_none(self):
        self.assertIsNone(rch._gt_count(None, 200.0))

    def test_counts_strictly_above_and_ignores_nan(self):
        s = np.array([100.0, 250.0, np.nan, 300.0, 200.0])
        self.assertEqual(rch._gt_count(s, 200.0), 2)  # 250, 300 (200 not strict)


class ActualRtPaddedTests(unittest.TestCase):
    def _write(self, tmp, iso, frame):
        frame.to_parquet(tmp / f"actual_lmp_hourly_{iso}.parquet")

    def _patched(self, tmp):
        rch._actual_rt_padded.cache_clear()
        return mock.patch("market_sim.config.paths.CALIBRATION_DIR", tmp)

    def test_none_when_missing(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            with self._patched(Path(d)):
                self.assertIsNone(rch._actual_rt_padded("NOPE", 2024, 8760))

    def test_scatters_by_hour_into_padded_array(self):
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            # Sparse, out-of-order hours -> scattered to a fixed-length NaN array.
            self._write(
                tmp,
                "TEST",
                pd.DataFrame(
                    {
                        "year": [2024, 2024],
                        "hour": [3, 1],
                        "rt": [500.0, np.nan],
                        "da": [1.0, 250.0],
                    }
                ),
            )
            with self._patched(tmp):
                got = rch._actual_rt_padded("TEST", 2024, 5)
            self.assertEqual(len(got), 5)
            np.testing.assert_allclose(got[3], 500.0)
            np.testing.assert_allclose(got[1], 250.0)  # da fallback where rt NaN
            self.assertTrue(np.isnan(got[0]) and np.isnan(got[2]) and np.isnan(got[4]))
            # Tail count via _gt_count uses the padded array directly.
            self.assertEqual(rch._gt_count(got, 300.0), 1)


if __name__ == "__main__":
    unittest.main()
