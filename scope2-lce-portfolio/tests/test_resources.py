"""Tests for the resource catalog and cost resolution."""

import numpy as np

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.resources import load_resource_arrays


def test_minimal_set_and_storage_mask() -> None:
    """Default config selects the three active_minimal resources."""
    res = load_resource_arrays(PortfolioConfig())
    assert res.names == ["solar_pv", "onshore_wind", "battery_4h"]
    assert res.n_res == 3
    # only the battery is storage
    assert res.is_storage.tolist() == [False, False, True]
    assert res.storage_idx.tolist() == [2]


def test_lcoe_to_fixed_conversion() -> None:
    """Generation fixed cost = lcoe * cf_assumed * 8760 (pay-for-capacity)."""
    res = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="mid"))
    solar = res.names.index("solar_pv")
    expected = 30.0 * 0.26 * HOURS_PER_YEAR  # mid LCOE * cf_assumed * hours
    assert np.isclose(res.fixed_mwyr[solar], expected)


def test_sensitivity_monotone() -> None:
    """low <= mid <= high fixed cost for a generation resource."""
    lo = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="low"))
    mid = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="mid"))
    hi = load_resource_arrays(PortfolioConfig(lcoe_sensitivity="high"))
    i = lo.names.index("onshore_wind")
    assert lo.fixed_mwyr[i] <= mid.fixed_mwyr[i] <= hi.fixed_mwyr[i]


def test_cap_and_floor_override() -> None:
    """Config caps/floors override the table defaults."""
    cfg = PortfolioConfig(
        resource_caps_mw={"solar_pv": 250.0},
        resource_floors_mw={"onshore_wind": 40.0},
    )
    res = load_resource_arrays(cfg)
    assert res.cap_max_mw[res.names.index("solar_pv")] == 250.0
    assert res.cap_min_mw[res.names.index("onshore_wind")] == 40.0


def test_active_resources_selection() -> None:
    """Explicit active_resources selects exactly those rows."""
    res = load_resource_arrays(PortfolioConfig(active_resources=("nuclear_new",)))
    assert res.names == ["nuclear_new"]
