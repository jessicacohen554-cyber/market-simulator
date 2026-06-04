"""Tests for EIA-930 demand loading, including the T&D loss gross-up."""

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.data.eia_loader import (
    load_demand,
    pjm_net_interchange,
    pjm_zonal_load_shares,
)

_TEST_YEAR = 2023


def test_pjm_net_interchange_is_export_positive():
    """PJM's measured interchange loads as a large positive net export."""
    ix = pjm_net_interchange(_TEST_YEAR)
    assert ix is not None
    assert ix.shape == (8760,)
    assert not np.isnan(ix).any()
    # PJM exported ~40 TWh (≈ +4,564 MW avg) in 2023 — export-positive.
    assert 3000.0 < ix.mean() < 6000.0


def test_pjm_demand_includes_net_export():
    """PJM demand carries internal load *plus* the measured net export.

    The fleet must generate the ~40 TWh PJM actually exported, so total demand
    exceeds the internal-load-only allocation by the net interchange.
    """
    pjm = get_iso_config("PJM")
    demand = load_demand("PJM", _TEST_YEAR, pjm).sum(axis=0)
    ix = pjm_net_interchange(_TEST_YEAR)
    # Total served ≈ internal load + net export; the export is a real uplift.
    assert demand.mean() > 90_000.0  # ~94 GW incl. export vs ~89 GW load-only
    np.testing.assert_allclose(demand.mean(), 89_400 + ix.mean(), rtol=0.03)


def test_pjm_zonal_shares_sum_to_one_each_hour():
    """The per-zone hourly load shares partition system load every hour."""
    pjm = get_iso_config("PJM")
    shares = pjm_zonal_load_shares(_TEST_YEAR, pjm.zone_names)
    assert shares.shape == (pjm.n_zones, 8760)
    np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)


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
