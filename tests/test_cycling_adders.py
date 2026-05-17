"""Tests for thermal cycling cost adders applied to the marginal-cost array."""

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.cycling import apply_cycling_adders
from market_sim.data.fleet import Generator, generators_to_fleet_arrays

_T = 4

# All nine cycling adders, set to 0.0 — used to disable the feature.
_ZERO_ADDERS = {
    "cc_cycling_adder_h_class": 0.0,
    "cc_cycling_adder_f_class": 0.0,
    "cc_cycling_adder_older": 0.0,
    "coal_cycling_adder_supercritical": 0.0,
    "coal_cycling_adder_subcritical": 0.0,
    "coal_cycling_adder_older": 0.0,
    "ct_cycling_adder_aero": 0.0,
    "ct_cycling_adder_frame": 0.0,
    "ct_cycling_adder_older": 0.0,
}


def _gen(unit_id: str, fuel_type: str, retirement_year: int | None = None) -> Generator:
    """Build a minimal generator for cycling-adder tests."""
    return Generator(
        unit_id=unit_id,
        name=unit_id,
        zone="North",
        fuel_type=fuel_type,
        pmax_mw=100.0,
        retirement_year=retirement_year,
    )


def _apply(generators: list[Generator], config: ScenarioConfig) -> np.ndarray:
    """Apply cycling adders to a zero marginal-cost array for ``generators``."""
    fleet = generators_to_fleet_arrays(generators, ["North"], hours=_T)
    mc = np.zeros((len(generators), _T), dtype=float)
    return apply_cycling_adders(mc, generators, fleet, config)


def test_cycling_adders_applied():
    """Each fuel type's bins get the correct adder from config."""
    generators = [
        _gen("gas_cc_h_class_North", "gas_cc"),
        _gen("gas_cc_f_class_North", "gas_cc"),
        _gen("gas_cc_older_North", "gas_cc"),
        _gen("coal_supercritical_North", "coal"),
        _gen("coal_subcritical_North", "coal"),
        _gen("coal_older_North", "coal"),
        _gen("gas_ct_aero_North", "gas_ct"),
        _gen("gas_ct_frame_North", "gas_ct"),
        _gen("gas_ct_older_North", "gas_ct"),
    ]
    config = ScenarioConfig()
    mc = _apply(generators, config)

    expected = [
        config.cc_cycling_adder_h_class,
        config.cc_cycling_adder_f_class,
        config.cc_cycling_adder_older,
        config.coal_cycling_adder_supercritical,
        config.coal_cycling_adder_subcritical,
        config.coal_cycling_adder_older,
        config.ct_cycling_adder_aero,
        config.ct_cycling_adder_frame,
        config.ct_cycling_adder_older,
    ]
    for i, adder in enumerate(expected):
        np.testing.assert_allclose(mc[i], adder)


def test_passthrough_units_get_default():
    """Units without bin names (retirement_year set) get the 'older' default."""
    config = ScenarioConfig()
    # Pass-through units keep a plantid_generatorid unit_id with no bin name.
    generators = [
        _gen("3470_1", "gas_cc", retirement_year=2030),
        _gen("6648_2", "coal", retirement_year=2028),
        _gen("55097_GT1", "gas_ct", retirement_year=2032),
    ]
    mc = _apply(generators, config)

    np.testing.assert_allclose(mc[0], config.cc_cycling_adder_older)
    np.testing.assert_allclose(mc[1], config.coal_cycling_adder_older)
    np.testing.assert_allclose(mc[2], config.ct_cycling_adder_older)


def test_non_thermal_units_get_no_adder():
    """Wind, solar and nuclear units are never charged a cycling adder."""
    config = ScenarioConfig()
    generators = [
        _gen("wind_West", "wind"),
        _gen("solar_South", "solar"),
        _gen("12345_1", "nuclear"),
    ]
    mc = _apply(generators, config)
    np.testing.assert_allclose(mc, 0.0)


def test_cycling_adders_zero_when_disabled():
    """Setting all adders to 0.0 in config produces unchanged MC."""
    config = ScenarioConfig().with_overrides(**_ZERO_ADDERS)
    generators = [
        _gen("gas_cc_h_class_North", "gas_cc"),
        _gen("coal_supercritical_North", "coal"),
        _gen("gas_ct_frame_North", "gas_ct"),
    ]
    fleet = generators_to_fleet_arrays(generators, ["North"], hours=_T)
    mc_in = np.full((len(generators), _T), 25.0, dtype=float)
    mc_out = apply_cycling_adders(mc_in, generators, fleet, config)
    np.testing.assert_allclose(mc_out, mc_in)
