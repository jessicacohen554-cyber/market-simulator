"""Tests for fuel price resolution against AEO Henry Hub trajectories."""

import numpy as np

from market_sim.config.constants import (
    COAL_DIESEL_INDEX_BASE_YEAR,
    COAL_PRICE_BASE,
    GAS_BASIS_DIFFERENTIAL,
    HENRY_HUB_TRAJECTORIES,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, Generator, generators_to_fleet_arrays
from market_sim.data.fuel import (
    apply_coal_supply_pricing,
    resolve_annual_gas_price,
    resolve_fuel_prices,
    resolve_nox_price,
)

_HOURS = 8760
_ZONE_NAMES = ["north", "south"]


def _sample_fleet(hours: int = _HOURS):
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
    return generators_to_fleet_arrays(generators, _ZONE_NAMES, hours=hours)


def _coal_fleet(hours: int = _HOURS):
    """Return a coal-only fleet (one coal steam generator)."""
    generators = [
        Generator(
            unit_id="COAL",
            name="Coal Steam",
            zone="north",
            fuel_type="coal",
            pmax_mw=600.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _ZONE_NAMES, hours=hours)


def _config(**overrides) -> ScenarioConfig:
    """Return an ERCOT scenario config spanning a full weather year."""
    base = ScenarioConfig(iso="ERCOT", gas_price_path="mid", hours=_HOURS)
    return base.with_overrides(**overrides) if overrides else base


def test_mid_gas_price_2026():
    """Mid-path gas price for 2026 averages the AEO reference delivered price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, year=2026)
    gas_idx = fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"]
    expected_annual = (
        HENRY_HUB_TRAJECTORIES["mid"][2026] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    )
    # With seasonality on, the annual average is budget-neutral.
    actual_avg = prices[gas_idx].mean()
    assert abs(actual_avg - expected_annual) < 0.05, (
        f"Average gas price {actual_avg:.2f} != expected {expected_annual:.2f}"
    )


def test_gas_price_trajectory_increases():
    """Mid-path gas price increases from 2026 to 2050."""
    config = _config(gas_seasonality=False)
    fleet = _sample_fleet()
    p2026 = resolve_fuel_prices(config, fleet, 2026)
    p2050 = resolve_fuel_prices(config, fleet, 2050)
    gas_idx = fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"]
    assert p2050[gas_idx].mean() > p2026[gas_idx].mean()


def test_low_path_below_mid():
    """Low gas price path < mid path for all years."""
    config_low = _config(gas_price_path="low", gas_seasonality=False)
    config_mid = _config(gas_price_path="mid", gas_seasonality=False)
    fleet = _sample_fleet()
    for year in (2026, 2035, 2050):
        p_low = resolve_fuel_prices(config_low, fleet, year)
        p_mid = resolve_fuel_prices(config_mid, fleet, year)
        gas_idx = fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"]
        assert p_low[gas_idx].mean() < p_mid[gas_idx].mean(), f"low >= mid in {year}"


def test_caiso_basis_premium():
    """CAISO delivered gas price > ERCOT delivered gas price (same path/year)."""
    fleet = _sample_fleet()
    config_e = ScenarioConfig(
        iso="ERCOT", gas_price_path="mid", gas_seasonality=False, hours=_HOURS
    )
    config_c = ScenarioConfig(
        iso="CAISO", gas_price_path="mid", gas_seasonality=False, hours=_HOURS
    )
    pe = resolve_fuel_prices(config_e, fleet, 2030)
    pc = resolve_fuel_prices(config_c, fleet, 2030)
    gas_idx = fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"]
    assert pc[gas_idx].mean() > pe[gas_idx].mean()


def test_seasonality_winter_premium():
    """With seasonality on, January gas price > May gas price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=True), fleet, 2030)
    gas_idx = np.where(fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"])[0][0]
    jan_avg = prices[gas_idx, 0:744].mean()       # hours 0-743 = January
    may_avg = prices[gas_idx, 2880:3624].mean()   # hours 2880-3623 = May
    assert jan_avg > may_avg


def test_seasonality_off_flat():
    """With seasonality off, all hours have the same gas price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, 2030)
    gas_idx = np.where(fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"])[0][0]
    assert np.all(prices[gas_idx] == prices[gas_idx, 0])


def test_both_gas_types_get_gas_price():
    """gas_cc and gas_ct units both receive the delivered gas price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, 2030)
    expected = resolve_annual_gas_price(_config(), 2030)
    np.testing.assert_allclose(prices[0], expected)
    np.testing.assert_allclose(prices[1], expected)


def test_non_gas_zero_fuel():
    """Nuclear and wind generators get zero fuel price."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, 2030)
    nuclear_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["nuclear"]
    wind_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["wind"]
    assert np.all(prices[nuclear_mask] == 0.0)
    assert np.all(prices[wind_mask] == 0.0)


def test_coal_price_escalated_to_year():
    """Coal generators get COAL_PRICE_BASE escalated to the resolved year."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, 2030)
    coal_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["coal"]
    expected = COAL_PRICE_BASE["ERCOT"] * 1.01 ** (2030 - START_YEAR)
    np.testing.assert_allclose(prices[coal_mask], expected)


def test_coal_price_escalates():
    """Coal price escalates 1%/yr, compounding from the start year."""
    config = _config()
    fleet = _coal_fleet()
    prices_2026 = resolve_fuel_prices(config, fleet, 2026)
    prices_2036 = resolve_fuel_prices(config, fleet, 2036)
    expected_ratio = (1.01) ** 10
    actual_ratio = prices_2036[0, 0] / prices_2026[0, 0]
    assert abs(actual_ratio - expected_ratio) < 1e-4


def test_fuel_price_shape_is_n_gen_by_hours():
    """The resolved fuel price array is shaped ``(n_gen, T)``."""
    fleet = _sample_fleet(hours=24)
    prices = resolve_fuel_prices(_config(hours=24), fleet, 2030)
    assert prices.shape == (fleet.n_gen, 24)


def test_annual_gas_price_extrapolates_beyond_trajectory():
    """Years past the trajectory extrapolate from the final growth rate."""
    config = _config(gas_price_path="mid")
    traj = HENRY_HUB_TRAJECTORIES["mid"]
    growth = traj[2050] / traj[2049]
    expected = traj[2050] * growth + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    assert abs(resolve_annual_gas_price(config, 2051) - expected) < 1e-9


def test_capacity_gas_lcoe_uses_trajectory():
    """The annual gas price feeding capacity LCOE matches the dispatch trajectory.

    The runner passes ``resolve_annual_gas_price`` into ``evolve_fleet`` so
    capacity new-entry LCOE screening charges gas units the same delivered
    price that hourly dispatch sees (seasonality aside).
    """
    config = _config(gas_price_path="mid")
    year = 2035
    expected_gas = (
        HENRY_HUB_TRAJECTORIES["mid"][year] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    )
    assert resolve_annual_gas_price(config, year) == expected_gas

    # Dispatch with seasonality off resolves to the same annual price.
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, year)
    np.testing.assert_allclose(prices[0], expected_gas)


def test_gas_price_override_bypasses_trajectory():
    """A gas_price_override pins the delivered price, ignoring the trajectory.

    The override is the measured Henry Hub price; ``resolve_annual_gas_price``
    adds only the ISO basis differential and never consults the AEO
    trajectory, so every year resolves to the same delivered price.
    """
    config = _config(gas_price_path="mid", gas_price_override=2.54)
    expected = 2.54 + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    for year in (2023, 2030, 2050):
        assert resolve_annual_gas_price(config, year) == expected

    # The override differs from the trajectory it replaces for the same year.
    trajectory_config = _config(gas_price_path="mid")
    assert resolve_annual_gas_price(
        trajectory_config, 2030
    ) != resolve_annual_gas_price(config, 2030)


def test_nox_price_passes_through_from_config():
    """The NOx price is the scalar carried on the config."""
    config = _config(nox_price=7.5)
    assert resolve_nox_price(config) == 7.5


def _coal_gen(supply: str) -> Generator:
    """Return a coal generator tagged with a fuel-supply type."""
    return Generator(
        unit_id=f"COAL_{supply or 'none'}", name="Coal", zone="north",
        fuel_type="coal", pmax_mw=500.0, heat_rate=10.0, coal_supply=supply,
    )


def test_coal_supply_pricing_base_year():
    """At the diesel base year, lignite and PRB get their base prices."""
    config = ScenarioConfig()
    gens = [_coal_gen("lignite"), _coal_gen("prb"), _coal_gen("")]
    fuel_prices = np.full((3, 24), 2.0)
    apply_coal_supply_pricing(
        fuel_prices, gens, config, COAL_DIESEL_INDEX_BASE_YEAR
    )
    assert np.allclose(fuel_prices[0], config.coal_price_lignite)
    assert np.allclose(
        fuel_prices[1],
        config.coal_price_prb * config.coal_prb_contract_passthrough,
    )
    # Untagged coal keeps the generic price already in the array.
    assert np.allclose(fuel_prices[2], 2.0)


def test_coal_supply_pricing_diesel_indexed():
    """Lignite scales with the diesel index; PRB is held flat."""
    config = ScenarioConfig()
    gens = [_coal_gen("lignite"), _coal_gen("prb")]
    fp_2023, fp_2024 = np.zeros((2, 4)), np.zeros((2, 4))
    apply_coal_supply_pricing(fp_2023, gens, config, 2023)
    apply_coal_supply_pricing(fp_2024, gens, config, 2024)
    # 2023 diesel was higher, so lignite is pricier in 2023 than 2024.
    assert fp_2023[0, 0] > fp_2024[0, 0]
    # PRB is the measured delivered cost (take-or-pay discounted), not
    # diesel-indexed — flat across years.
    assert fp_2023[1, 0] == fp_2024[1, 0] == (
        config.coal_price_prb * config.coal_prb_contract_passthrough
    )
