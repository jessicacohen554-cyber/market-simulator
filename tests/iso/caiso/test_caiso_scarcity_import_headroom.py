"""Tests for the caiso-85 scarcity-overlay import-headroom reserve measure.

``caiso_scarcity_import_headroom`` (FINDING-caiso-winter-gas-level-2026-07-15 §3)
adds the hourly unloaded must-offer import capability to the CAISO scarcity
overlay's LOLP reserve measure, so the overlay stops pricing scarcity while the
LP still holds unloaded sub-VOLL import supply. The change is a post-solve
overlay only:

  * ``import_headroom=None`` (default) is byte-identical to the pre-caiso-85
    overlay;
  * a positive import headroom raises the reserve measure and therefore lowers
    (never raises) the scarcity adder.
"""

import types
import unittest

import numpy as np

from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.results import scarcity as sc

_T = 24


def _fleet() -> types.SimpleNamespace:
    # One thermal (gas_cc) running near cap (little native reserve) + one import
    # tranche so the fleet carries import capability the overlay can credit.
    return types.SimpleNamespace(
        fuel_type_idx=np.array(
            [FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["import"]], dtype=int
        ),
        pmax=np.array([1000.0, 2000.0]),
        availability=np.ones((2, _T)),
    )


class TestCaisoScarcityImportHeadroom(unittest.TestCase):
    def _dispatch(self) -> np.ndarray:
        d = np.zeros((2, _T))
        d[0] = 990.0  # thermal near cap -> ~10 MW native reserve
        d[1] = 500.0  # import 500 of 2000 MW
        return d

    def test_none_is_byte_identical(self) -> None:
        fa = _fleet()
        d = self._dispatch()
        lam = np.full(_T, 50.0)
        a_default = sc.caiso_scarcity_overlay(fa, d, np.zeros(0), None, None, None, lam)
        a_none = sc.caiso_scarcity_overlay(
            fa, d, np.zeros(0), None, None, None, lam, import_headroom=None
        )
        np.testing.assert_array_equal(a_default, a_none)

    def test_import_headroom_lowers_adder(self) -> None:
        fa = _fleet()
        d = self._dispatch()
        lam = np.full(_T, 50.0)
        a_off = sc.caiso_scarcity_overlay(fa, d, np.zeros(0), None, None, None, lam)
        imp_hr = np.full(_T, 1500.0)  # 2000 - 500 unloaded import
        a_on = sc.caiso_scarcity_overlay(
            fa, d, np.zeros(0), None, None, None, lam, import_headroom=imp_hr
        )
        # More reserve -> lower LOLP -> lower (never higher) scarcity adder.
        self.assertTrue(np.all(a_on <= a_off + 1e-9))
        self.assertLess(float(a_on.mean()), float(a_off.mean()))

    def test_zero_headroom_matches_none(self) -> None:
        fa = _fleet()
        d = self._dispatch()
        lam = np.full(_T, 50.0)
        a_none = sc.caiso_scarcity_overlay(fa, d, np.zeros(0), None, None, None, lam)
        a_zero = sc.caiso_scarcity_overlay(
            fa, d, np.zeros(0), None, None, None, lam, import_headroom=np.zeros(_T)
        )
        np.testing.assert_allclose(a_zero, a_none)


if __name__ == "__main__":
    unittest.main()
