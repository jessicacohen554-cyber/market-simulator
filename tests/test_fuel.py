"""Tests for fuel price and carbon price resolution."""

import numpy as np

from market_sim.config.constants import (
    COAL_PRICE_BASE,
    GAS_PRICE_BASE,
    GAS_PRICE_ESCALATION,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fuel import resolve_fuel_prices, resolve_nox_price

_TEST_HOURS = 12
_ZONE_NAMES = ["north", "south"]


def _sample_fleet():
    """Return a fleet spanning gas, coal and non-fuel-burning generators."""
    generators = [
        Generator(
            unit_id="GAS_CC",
            name="Combined Cycle",
            zone="north",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_CT",
            name="Combustion Turbine",
            zone="south",
            fuel_type="gas_ct",
            pmax_mw=100.0,
        ),
        Generator(
            unit_id="COAL",
            name="Coal Steam",
            zone="north",
            fuel_type="coal",
            pmax_mw=600.0,
        ),
        Generator(
            unit_id="NUKE",
            name="Nuclear",
            zone="north",
            fuel_type="nuclear",
            pmax_mw=1200.0,
        ),
        Generator(
            unit_id="WIND",
            name="Wind Farm",
            zone="south",
            fuel_type="wind",
            pmax_mw=300.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _ZONE_NAMES, hours=_TEST_HOURS)


def _config(**overrides) -> ScenarioConfig:
    """Return an ERCOT scenario config with the test hour count."""
    base = ScenarioConfig(iso="ERCOT", gas_price_path="mid", hours=_TEST_HOURS)
    return base.with_overrides(**overrides) if overrides else base


def test_mid_gas_start_year_equals_base():
    """ERCOT 'mid' gas in the start year carries no escalation."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, START_YEAR)

    expected = GAS_PRICE_BASE["ERCOT"]["mid"]
    # Generator 0 is the gas_cc unit.
    np.testing.assert_allclose(prices[0], expected)


def test_gas_price_escalates_over_time():
    """A later year yields a higher gas price than the start year."""
    fleet = _sample_fleet()
    config = _config()
    price_2026 = resolve_fuel_prices(config, fleet, 2026)[0, 0]
    price_2030 = resolve_fuel_prices(config, fleet, 2030)[0, 0]

    assert price_2030 > price_2026
    expected_2030 = GAS_PRICE_BASE["ERCOT"]["mid"] * (
        1.0 + GAS_PRICE_ESCALATION
    ) ** (2030 - START_YEAR)
    assert price_2030 == expected_2030


def test_non_fuel_generators_get_zero_price():
    """Nuclear and wind generators carry no commodity fuel price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, START_YEAR)

    # Generators 3 and 4 are nuclear and wind.
    np.testing.assert_array_equal(prices[3], np.zeros(_TEST_HOURS))
    np.testing.assert_array_equal(prices[4], np.zeros(_TEST_HOURS))


def test_coal_generators_get_coal_price():
    """Coal generators are priced at the ISO's COAL_PRICE_BASE."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, 2040)

    # Generator 2 is the coal unit; coal price does not escalate.
    np.testing.assert_allclose(prices[2], COAL_PRICE_BASE["ERCOT"])


def test_fuel_price_shape_is_n_gen_by_hours():
    """The resolved fuel price array is shaped ``(n_gen, T)``."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, START_YEAR)

    assert prices.shape == (fleet.n_gen, _TEST_HOURS)


def test_both_gas_types_get_gas_price():
    """gas_cc and gas_ct units both receive the escalated gas price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, START_YEAR)

    expected = GAS_PRICE_BASE["ERCOT"]["mid"]
    np.testing.assert_allclose(prices[0], expected)
    np.testing.assert_allclose(prices[1], expected)


def test_nox_price_passes_through_from_config():
    """The NOx price is the scalar carried on the config."""
    config = _config(nox_price=7.5)
    assert resolve_nox_price(config) == 7.5
