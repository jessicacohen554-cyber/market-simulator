"""Tests for EIA-930 demand loading, including the T&D loss gross-up."""

import numpy as np

from market_sim.data.eia_loader import load_demand

_TEST_YEAR = 2023


def test_loss_factor_applied():
    """Demand with td_loss_factor > 0 is scaled up by (1 + factor)."""
    # CAISO's load_demand is a pure load-share split, so the gross-up is a
    # clean proportional scaling. ERCOT additionally nets DC-tie
    # interchange, a transmission flow that is not loss-grossed.
    base = load_demand("CAISO", _TEST_YEAR)
    grossed = load_demand("CAISO", _TEST_YEAR, td_loss_factor=0.058)
    np.testing.assert_allclose(grossed, base * 1.058)


def test_loss_factor_zero_is_noop():
    """A zero loss factor leaves demand unchanged."""
    base = load_demand("ERCOT", _TEST_YEAR)
    same = load_demand("ERCOT", _TEST_YEAR, td_loss_factor=0.0)
    np.testing.assert_array_equal(base, same)
