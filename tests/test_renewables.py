"""Tests for wind and solar capacity-factor profile derivation."""

import numpy as np

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.renewables import (
    derive_cf_profile,
    load_renewable_profiles,
)

_TEST_YEAR = 2024


def test_derive_cf_profile_known_values():
    """CF equals generation value times avg CF times the hour count."""
    values = np.array([1.0e-4, 2.0e-4, 1.5e-4])
    avg_cf = 0.35
    result = derive_cf_profile(values, avg_cf)
    expected = values * avg_cf * HOURS_PER_YEAR
    np.testing.assert_allclose(result, expected)


def test_derive_cf_profile_clipped_to_unit_interval():
    """High generation values clip to 1.0 and all CFs stay in [0, 1]."""
    values = np.array([0.0, 1.0e-4, 0.5])
    result = derive_cf_profile(values, 0.35)
    assert result.min() >= 0.0
    assert result.max() <= 1.0
    # 0.5 * 0.35 * 8760 far exceeds 1.0 and must clip to the CF ceiling.
    assert result[-1] == 1.0


def test_renewable_cf_adjustment_scales_cfs():
    """A 1.1 CF adjustment scales the (unclipped) wind CFs by 10%."""
    iso_config = get_iso_config("ERCOT")
    base = ScenarioConfig(weather_year=_TEST_YEAR, iso="ERCOT")
    adjusted = base.with_overrides(renewable_cf_adjustment=1.1)

    wind_cf_base, _, _, _ = load_renewable_profiles(
        "ERCOT", _TEST_YEAR, iso_config, base
    )
    wind_cf_adj, _, _, _ = load_renewable_profiles(
        "ERCOT", _TEST_YEAR, iso_config, adjusted
    )
    np.testing.assert_allclose(wind_cf_adj, wind_cf_base * 1.1)


def test_ercot_wind_allocated_to_west_zone():
    """ERCOT wind CF fills the West zone and zeros every other zone."""
    iso_config = get_iso_config("ERCOT")
    config = ScenarioConfig(weather_year=_TEST_YEAR, iso="ERCOT")
    wind_cf, wind_cap, _, _ = load_renewable_profiles(
        "ERCOT", _TEST_YEAR, iso_config, config
    )
    assert wind_cf.shape == (4, HOURS_PER_YEAR)

    west = iso_config.zone_names.index("West")
    assert wind_cf[west].sum() > 0.0
    assert wind_cap[west] > 0.0
    for idx in range(iso_config.n_zones):
        if idx != west:
            assert np.all(wind_cf[idx] == 0.0)
            assert wind_cap[idx] == 0.0


def test_caiso_solar_allocated_to_main_zone_not_import():
    """CAISO solar CF fills CAISO_main and leaves WECC_import at zero."""
    iso_config = get_iso_config("CAISO")
    config = ScenarioConfig(weather_year=_TEST_YEAR, iso="CAISO")
    _, _, solar_cf, solar_cap = load_renewable_profiles(
        "CAISO", _TEST_YEAR, iso_config, config
    )
    main = iso_config.zone_names.index("CAISO_main")
    wecc = iso_config.zone_names.index("WECC_import")

    assert solar_cf[main].sum() > 0.0
    assert solar_cap[main] > 0.0
    assert np.all(solar_cf[wecc] == 0.0)
    assert solar_cap[wecc] == 0.0
