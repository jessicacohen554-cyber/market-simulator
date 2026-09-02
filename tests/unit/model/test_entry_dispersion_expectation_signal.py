"""Tests for the dispersion-carrying capacity-screen entry signal (capx D43).

The D39 object (``docs/handoffs/FINDING-capx-d39-entry-underbuild-2026-09-02.md``
§0/§3.1): the zone-flat tail-free stack re-price discards the energy leg's
DISPERSION. The construction under test replaces it with each zone's OWN
realized price-duration curve indexed by the entering year's headroom rank on
the current year's headroom distribution —
``signal[z,t] = quantile_{1 - u[t]}(econ_prices[z,:])``,
``u = mid-rank CDF of headroom_next on headroom_curr``.
Trivial-first per CLAUDE.md: hand-computed 2-zone / 4-8-hour surfaces; the
config seam (requires-reprice refusal, mutual exclusions, backcast coercion,
cache-key registration) is tested at the ScenarioConfig grain.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.runner import _dispersion_expectation_signal, _headroom_rank


class TestHeadroomRank(unittest.TestCase):
    """The rank is a mid-rank empirical CDF: ties split, ends clamp."""

    def test_distinct_values_rank_at_midpoints(self):
        curr = np.array([10.0, 30.0, 20.0, 40.0])
        # Each current value ranks at its own (i + 0.5) / T position.
        np.testing.assert_allclose(
            _headroom_rank(curr, curr), [0.125, 0.625, 0.375, 0.875]
        )

    def test_ties_and_out_of_range(self):
        curr = np.array([10.0, 20.0, 20.0, 40.0])
        # 20 ties two current hours: left=1, right=3 -> (1+3)/8 = 0.5.
        # 5 is tighter than every current hour -> 0.0; 99 looser -> 1.0.
        np.testing.assert_allclose(
            _headroom_rank(np.array([20.0, 5.0, 99.0]), curr), [0.5, 0.0, 1.0]
        )

    def test_monotone_in_headroom(self):
        rng = np.random.default_rng(7)
        curr = rng.normal(size=500)
        probe = np.sort(rng.normal(size=200))
        u = _headroom_rank(probe, curr)
        self.assertTrue(np.all(np.diff(u) >= 0.0))


class TestDispersionCompose(unittest.TestCase):
    """Hand-computed fixed points and the one-sided moves."""

    def test_unchanged_headroom_is_an_exact_permutation_per_zone(self):
        # Two zones, four hours; headroom identical between the years.
        econ = np.array([[10.0, 30.0, 50.0, 20.0], [12.0, 28.0, 55.0, -3.0]])
        headroom = np.array([900.0, 300.0, 100.0, 600.0])  # tight hour = h2
        out = _dispersion_expectation_signal(econ, headroom, headroom)
        # Tightest hour (h2, rank 0.125 -> q 0.875 = grid[3]) earns each
        # zone's MAX; loosest (h0) its MIN; the multiset is reproduced.
        np.testing.assert_allclose(out[0], [10.0, 30.0, 50.0, 20.0])
        np.testing.assert_allclose(out[1], [-3.0, 28.0, 55.0, 12.0])
        for z in range(2):
            np.testing.assert_allclose(np.sort(out[z]), np.sort(econ[z]))
        # Zone 0's duals are already monotone in headroom -> hour by hour.
        np.testing.assert_allclose(out[0], econ[0])

    def test_uniform_tightening_moves_up_the_duration_curve(self):
        econ = np.array([[10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]])
        curr = np.array([800.0, 700.0, 600.0, 500.0, 400.0, 300.0, 200.0, 100.0])
        same = _dispersion_expectation_signal(econ, curr, curr)
        tighter = _dispersion_expectation_signal(econ, curr - 150.0, curr)
        np.testing.assert_allclose(same, econ)
        # Every hour ranks tighter, so no hour prices lower and the mean
        # rises; the tightest hours clamp at the realized MAX (the ceiling
        # is the dual surface, never a pro-forma tail).
        self.assertTrue(np.all(tighter >= same - 1e-12))
        self.assertGreater(tighter.mean(), same.mean())
        self.assertLessEqual(tighter.max(), econ.max())
        # And looser the other way, floored at the realized MIN.
        looser = _dispersion_expectation_signal(econ, curr + 150.0, curr)
        self.assertTrue(np.all(looser <= same + 1e-12))
        self.assertGreaterEqual(looser.min(), econ.min())

    def test_entering_year_may_have_more_tight_hours(self):
        # A year whose headroom duration has MORE tight hours draws more
        # hours from the top of the duration curve: the hours >= $100 count
        # rises even though no realized price above $100 is invented.
        econ = np.array([[5.0, 20.0, 40.0, 60.0, 90.0, 120.0, 150.0, 400.0]])
        curr = np.array([80.0, 70.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0]) * 100
        nxt = np.array([80.0, 70.0, 60.0, 15.0, 12.0, 10.0, 10.0, 10.0]) * 100
        out = _dispersion_expectation_signal(econ, nxt, curr)
        self.assertGreater((out >= 100.0).sum(), (econ >= 100.0).sum())
        self.assertLessEqual(out.max(), 400.0)

    def test_new_array_inputs_untouched_and_shapes(self):
        econ = np.array([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])
        econ_copy = econ.copy()
        h = np.array([3.0, 2.0, 1.0])
        out = _dispersion_expectation_signal(econ, np.array([2.5, 1.5, 0.5, 9.0]), h)
        self.assertEqual(out.shape, (2, 4))
        self.assertIsNot(out, econ)
        np.testing.assert_allclose(econ, econ_copy)


class TestConfigSeam(unittest.TestCase):
    """Gate contract: requires the reprice; exclusive; backcast off; cache key."""

    def test_armed_without_reprice_is_refused(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="CAISO",
                mode="forecast",
                entry_lookahead_reprice=False,
                entry_dispersion_expectation_signal=True,
            )

    def test_mutually_exclusive_with_the_hour_aligned_composition(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="CAISO",
                mode="forecast",
                entry_forward_expectation_signal=True,
                entry_dispersion_expectation_signal=True,
            )

    def test_refused_with_the_exhaustion_walk(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="CAISO",
                mode="forecast",
                entry_margin_exhaustion=True,
                entry_dispersion_expectation_signal=True,
            )

    def test_backcast_coerces_off_with_the_reprice(self):
        cfg = ScenarioConfig(
            iso="CAISO",
            mode="backcast",
            entry_dispersion_expectation_signal=True,
        )
        self.assertFalse(cfg.entry_lookahead_reprice)
        self.assertFalse(cfg.entry_dispersion_expectation_signal)

    def test_default_off_keeps_cache_key_and_armed_moves_it(self):
        base = ScenarioConfig(iso="CAISO", mode="forecast")
        explicit_off = ScenarioConfig(
            iso="CAISO",
            mode="forecast",
            entry_dispersion_expectation_signal=False,
        )
        armed = ScenarioConfig(
            iso="CAISO",
            mode="forecast",
            entry_dispersion_expectation_signal=True,
        )
        self.assertEqual(base.cache_key(), explicit_off.cache_key())
        self.assertNotEqual(base.cache_key(), armed.cache_key())


if __name__ == "__main__":
    unittest.main()
