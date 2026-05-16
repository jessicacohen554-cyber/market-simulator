"""Tests for emissions accounting from dispatch results."""

import unittest

import numpy as np

from market_sim.results.emissions import compute_emissions, compute_nox


class TestComputeEmissions(unittest.TestCase):
    """``compute_emissions`` weights dispatch by per-generator CO2 rates."""

    def test_matches_manual_calculation(self):
        dispatch = np.array([[10.0, 20.0, 30.0], [5.0, 0.0, 15.0]])
        rates = np.array([0.4, 1.0])

        result = compute_emissions(dispatch, rates)

        manual = dispatch[0] * 0.4 + dispatch[1] * 1.0
        np.testing.assert_allclose(result, manual)
        self.assertEqual(result.shape, (3,))

    def test_equals_sum_of_dispatch_times_rates(self):
        rng = np.random.default_rng(0)
        dispatch = rng.uniform(0.0, 100.0, size=(7, 24))
        rates = rng.uniform(0.0, 1.0, size=7)

        np.testing.assert_allclose(
            compute_emissions(dispatch, rates),
            (dispatch * rates[:, None]).sum(axis=0),
        )

    def test_zero_rates_produce_zero_emissions(self):
        dispatch = np.full((4, 12), 50.0)

        result = compute_emissions(dispatch, np.zeros(4))

        np.testing.assert_array_equal(result, np.zeros(12))


class TestComputeNox(unittest.TestCase):
    """``compute_nox`` follows the same pattern with NOx rates."""

    def test_matches_manual_calculation(self):
        dispatch = np.array([[100.0, 200.0], [50.0, 25.0]])
        rates = np.array([0.0015, 0.0003])

        result = compute_nox(dispatch, rates)

        manual = dispatch[0] * 0.0015 + dispatch[1] * 0.0003
        np.testing.assert_allclose(result, manual)
        self.assertEqual(result.shape, (2,))


if __name__ == "__main__":
    unittest.main()
