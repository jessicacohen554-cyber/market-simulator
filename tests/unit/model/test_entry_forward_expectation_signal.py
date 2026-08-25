"""Tests for the forward-expectation capacity-screen entry signal.

ENTRY-SIGNAL lane, the rung named by
``docs/FINDING-entry-signal-disarm-2026-08.md`` §6: the screens' price object
becomes the run's own prior-year hourly ZONAL LP dual surface re-leveled hour
by hour by the lookahead stack instrument's own forward delta —
``signal[z,t] = econ_prices[z,t] + (S_entering[t] - S_current[t])``.
Trivial-first per CLAUDE.md: hand-computed 2-zone / 4-hour surfaces; the
config seam (requires-reprice refusal, backcast coercion, cache-key
registration) is tested at the ScenarioConfig grain.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.runner import _forward_expectation_signal


class TestForwardExpectationCompose(unittest.TestCase):
    """The composition is exact arithmetic on a hand-computed surface."""

    def test_hand_computed_composition(self):
        econ = np.array([[10.0, 30.0, 50.0, 20.0], [12.0, 28.0, 55.0, 22.0]])
        sig_next = np.array([20.0, 25.0, 60.0, 30.0])
        sig_curr = np.array([15.0, 25.0, 40.0, 35.0])
        out = _forward_expectation_signal(econ, sig_next, sig_curr)
        # delta = [+5, 0, +20, -5], applied zone-uniformly per hour.
        np.testing.assert_allclose(
            out,
            [[15.0, 30.0, 70.0, 15.0], [17.0, 28.0, 75.0, 17.0]],
        )
        # The duals' cross-zone structure survives the re-level EXACTLY: the
        # locational content is the duals', the level move is the stack's.
        np.testing.assert_allclose(out[1] - out[0], econ[1] - econ[0])

    def test_zero_delta_is_identity_and_input_never_mutated(self):
        econ = np.array([[10.0, 30.0], [12.0, 28.0]])
        econ_copy = econ.copy()
        flat = np.array([40.0, 45.0])
        out = _forward_expectation_signal(econ, flat, flat)
        # S_entering == S_current (nothing changes between the years) ==>
        # the signal IS the dual surface — the disarm's object, recovered as
        # the fixed point of the forward view.
        np.testing.assert_allclose(out, econ_copy)
        self.assertIsNot(out, econ)  # a NEW array
        np.testing.assert_allclose(econ, econ_copy)  # duals untouched

    def test_negative_hours_are_allowed(self):
        # A renewable-oversupply trough (low dual) plus a falling stack
        # (negative delta) may price below zero — real markets do; the
        # screens' max(p - vc, 0) semantics handle it. The composition must
        # not clip.
        econ = np.array([[2.0, 5.0]])
        out = _forward_expectation_signal(
            econ, np.array([10.0, 10.0]), np.array([18.0, 10.0])
        )
        np.testing.assert_allclose(out, [[-6.0, 5.0]])


class TestConfigSeam(unittest.TestCase):
    """Gate contract: requires the reprice; backcast coerces off; cache key."""

    def test_armed_without_reprice_is_refused(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="ERCOT",
                mode="forecast",
                entry_lookahead_reprice=False,
                entry_forward_expectation_signal=True,
            )

    def test_backcast_coerces_off_with_the_reprice(self):
        cfg = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            entry_forward_expectation_signal=True,
        )
        self.assertFalse(cfg.entry_lookahead_reprice)
        self.assertFalse(cfg.entry_forward_expectation_signal)

    def test_default_off_keeps_cache_key_and_armed_moves_it(self):
        base = ScenarioConfig(iso="ERCOT", mode="forecast")
        explicit_off = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            entry_forward_expectation_signal=False,
        )
        armed = ScenarioConfig(
            iso="ERCOT",
            mode="forecast",
            entry_forward_expectation_signal=True,
        )
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS: the default is dropped
        # from the hash, so every pre-existing key is byte-stable...
        self.assertEqual(base.cache_key(), explicit_off.cache_key())
        # ...and an armed run is a distinct scenario.
        self.assertNotEqual(base.cache_key(), armed.cache_key())


if __name__ == "__main__":
    unittest.main()
