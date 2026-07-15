"""Tests for the unit-outage deriver's WHEN-OPERABLE baseload guard and the
unit-grain partial-plateau mode.

The short/partial baseload guard (:data:`SHORT_BASELOAD_CF` = 0.55) is measured
on the hours a unit is OPERABLE — outside its own >= 5-day standard outage
windows — not on raw annual hours. A unit with a documented multi-month outage
plus a short event-coincident stop is baseload by its running capability and
must pass the guard; the same unit cycling economically (low CF throughout, no
documented outage) must fail. This is the identification correction of
docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7, cited to that measurement, not
to any price residual. Trivial synthetic cases only (no on-disk CEMS read).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.derive_campd_unit_outages import (  # noqa: E402
    SHORT_BASELOAD_CF,
    _operable_mask,
    _partial_plateau_windows,
    _when_operable_cf,
)

HOURS = 8760
YEAR = 2025
CAP = 100.0  # detect nameplate MW


def _base_gross(run_cf: float) -> np.ndarray:
    """A unit running flat at ``run_cf`` x CAP for the whole year."""
    return np.full(HOURS, run_cf * CAP, dtype=float)


class WhenOperableGuardTest(unittest.TestCase):
    """The when-operable baseload guard (the LEG A identification correction)."""

    # A 180-day documented outage the standard >= 5-day extract carries: the
    # unit is 0 MW here. Feb-Jul (day 40 .. 220).
    LONG_START = pd.Timestamp("2025-02-10")
    LONG_END = pd.Timestamp("2025-08-08")  # inclusive last day, ~180 days

    def _standard_windows(self) -> dict:
        return {
            (99, "1", YEAR): [(self.LONG_START, self.LONG_END)],
        }

    def _baseload_with_outage_and_short_stop(self) -> np.ndarray:
        """Runs at 0.65 CF, zeroed across the 180-day outage AND a 2-day stop."""
        g = _base_gross(0.65)
        base = pd.Timestamp(f"{YEAR}-01-01")
        lo = int((self.LONG_START - base).total_seconds() // 3600)
        hi = int((self.LONG_END + pd.Timedelta(days=1) - base).total_seconds() // 3600)
        g[lo:hi] = 0.0
        # A 2-day event-coincident full stop OUTSIDE the documented window
        # (late August), the short-window phenomenon itself.
        s2 = int((pd.Timestamp("2025-08-20") - base).total_seconds() // 3600)
        g[s2 : s2 + 48] = 0.0
        return g

    def test_operable_mask_removes_only_the_standard_window(self):
        mask = _operable_mask(self._standard_windows(), 99, "1", YEAR, HOURS)
        base = pd.Timestamp(f"{YEAR}-01-01")
        lo = int((self.LONG_START - base).total_seconds() // 3600)
        hi = int((self.LONG_END + pd.Timedelta(days=1) - base).total_seconds() // 3600)
        self.assertFalse(mask[lo:hi].any())  # window hours are not operable
        self.assertTrue(mask[:lo].all())  # everything else operable
        self.assertTrue(mask[hi:].all())

    def test_baseload_unit_with_long_outage_passes_when_operable(self):
        g = self._baseload_with_outage_and_short_stop()
        # Raw-annual basis (no standard windows) is dragged below 0.55 by the
        # 180-day outage and SPURIOUSLY fails the guard...
        raw_cf = _when_operable_cf(g, CAP, {}, 99, "1", YEAR)
        self.assertLess(raw_cf, SHORT_BASELOAD_CF)
        # ...but the when-operable basis (excluding the documented window) sees
        # the unit's true running capability and PASSES.
        oper_cf = _when_operable_cf(g, CAP, self._standard_windows(), 99, "1", YEAR)
        self.assertGreaterEqual(oper_cf, SHORT_BASELOAD_CF)

    def test_economically_cycling_unit_fails_the_guard(self):
        # Same unit, no documented outage, just cycling at 0.40 CF all year:
        # when-operable CF == raw-annual CF == 0.40, below the baseload guard,
        # so an economic cycler is never admitted (either basis).
        g = _base_gross(0.40)
        self.assertLess(_when_operable_cf(g, CAP, {}, 99, "1", YEAR), SHORT_BASELOAD_CF)
        self.assertLess(
            _when_operable_cf(g, CAP, self._standard_windows(), 99, "1", YEAR),
            SHORT_BASELOAD_CF,
        )

    def test_no_windows_reduces_to_raw_annual(self):
        g = _base_gross(0.70)
        self.assertAlmostEqual(
            _when_operable_cf(g, CAP, {}, 99, "1", YEAR), 0.70, places=6
        )


class PartialPlateauModeTest(unittest.TestCase):
    """The unit-grain partial-plateau detector wrapper (LEG B)."""

    def test_sustained_half_capacity_plateau_is_detected(self):
        # Unit runs near ceiling (0.9 CF) except for a 20-day plateau at ~0.45
        # CF (half its units out) — a partial derate the >= 5-day plateau rule
        # must catch, with a derate_factor around 0.5.
        g = _base_gross(0.9)
        base = pd.Timestamp(f"{YEAR}-01-01")
        lo = int((pd.Timestamp("2025-07-10") - base).total_seconds() // 3600)
        g[lo : lo + 20 * 24] = 0.45 * CAP
        windows, factors = _partial_plateau_windows(g, CAP)
        self.assertTrue(windows, "expected at least one plateau window")
        # A window overlapping the depressed span with a derate_factor < 1.
        hit = [w for w in windows if w[0] <= lo < w[1]]
        self.assertTrue(hit)
        self.assertLess(factors[hit[0]], 1.0)
        self.assertGreater(factors[hit[0]], 0.0)

    def test_flat_baseload_unit_has_no_plateau(self):
        # A unit that never drops its ceiling yields no partial window.
        windows, factors = _partial_plateau_windows(_base_gross(0.9), CAP)
        self.assertEqual(windows, [])
        self.assertEqual(factors, {})


if __name__ == "__main__":
    unittest.main()
