"""Tests for the CT-only CEMS bench flag (render_calibration_html Leg B).

A plant whose EIA-923 annual NET generation exceeds 1.1x its CAMPD annual
GROSS is submitting an incomplete CEMS record (gross >= net for any complete
record) — the 2x1 combined-cycle signature where only the combustion-turbine
block reports. Those plants must be flagged so their per-plant capture scores
on the EIA-923 monthly row, not the understated CAMPD series
(docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md §3a, §6 Leg B).
"""

import importlib.util
import unittest
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[1]


def _load(mod_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        mod_name, str(_REPO / "scripts" / filename)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rch = _load("rch_ctonly", "render_calibration_html.py")


class TestFlagCtOnlyReporters(unittest.TestCase):
    """``_flag_ct_only_reporters`` marks 923-net > 1.1x CAMPD-gross plants."""

    def setUp(self):
        # Hermetic: a fixed net/gross factor (2.7% parasitic) for every plant,
        # so CAMPD gross = c_ann / 0.973 regardless of the committed artifact.
        rch._parasitic_factors.cache_clear()
        self._orig = rch._parasitic_factors
        rch._parasitic_factors = lambda: {}

    def tearDown(self):
        rch._parasitic_factors = self._orig
        rch._parasitic_factors.cache_clear()

    def _bench(self):
        # Ironwood-like CT-only reporter (923 net ~1.5x CAMPD gross), a clean CC
        # (923 net ~ CAMPD net), and a no-CAMPD plant.
        return {
            "55337": {
                "name": "Ironwood",
                "group": "CC_REGULAR",
                "c_ann": 3.34,
                "e_ann": 4.90,
            },  # 923/gross ~ 1.43
            "999": {
                "name": "Clean CC",
                "group": "CC_REGULAR",
                "c_ann": 5.00,
                "e_ann": 4.90,
            },  # ~0.95, not flagged
            "888": {
                "name": "NoData",
                "group": "CC_REGULAR",
                "c_ann": 0.0,
                "e_ann": 2.00,
            },  # nodata, skipped
        }

    def test_flags_only_the_ct_only_plant(self):
        bp = self._bench()
        flagged = rch._flag_ct_only_reporters(bp)
        self.assertEqual([r["code"] for r in flagged], [55337])
        self.assertTrue(bp["55337"]["ct_only"])
        # Ratio is 923-net / CAMPD-gross = 4.90 / (3.34 / 0.973).
        self.assertAlmostEqual(bp["55337"]["ct_ratio"], 4.90 / (3.34 / 0.973), places=2)
        self.assertNotIn("ct_only", bp["999"])
        self.assertNotIn("ct_only", bp["888"])

    def test_nodata_plant_never_flagged(self):
        bp = {"1": {"name": "x", "group": "CC_REGULAR", "c_ann": 0.0, "e_ann": 9.0}}
        self.assertEqual(rch._flag_ct_only_reporters(bp), [])
        self.assertNotIn("ct_only", bp["1"])

    def test_just_below_threshold_untouched(self):
        # 923 net exactly at 1.1x CAMPD gross is NOT flagged (strict >).
        gross = 5.0 / 0.973
        bp = {
            "7": {
                "name": "edge",
                "group": "CC_REGULAR",
                "c_ann": 5.0,
                "e_ann": round(1.10 * gross, 4),
            }
        }
        self.assertEqual(rch._flag_ct_only_reporters(bp), [])


class TestCaptureOn923(unittest.TestCase):
    """``_capture_on_923`` scores a plant on its EIA-923 monthly row."""

    def test_perfect_monthly_match_high_capture(self):
        # Model whose monthly GWh equals the 923 monthly row → r=1, dev=0.
        e_mon = np.array([50.0, 45, 48, 40, 42, 55, 60, 58, 47, 44, 46, 52])
        # Build an hourly series whose monthly GWh sums to e_mon.
        rch_mod = rch
        cum = rch_mod._CUM
        mw = np.zeros(8760)
        for m in range(12):
            hrs = slice(cum[m], cum[m + 1])
            n = cum[m + 1] - cum[m]
            mw[hrs] = e_mon[m] * 1e3 / n  # GWh -> MWh -> per-hour MW
        m_ann = float(mw.sum()) / 1e6
        e_ann = float(e_mon.sum()) / 1e3
        r, nr, cap = rch_mod._capture_on_923(mw, e_mon, m_ann, e_ann)
        self.assertAlmostEqual(r, 1.0, places=2)
        self.assertGreater(cap, 95.0)

    def test_flat_model_returns_none(self):
        r, nr, cap = rch._capture_on_923(
            np.zeros(8760), np.array([10.0] * 12), 0.0, 0.12
        )
        self.assertEqual((r, nr, cap), (None, None, None))


if __name__ == "__main__":
    unittest.main()
