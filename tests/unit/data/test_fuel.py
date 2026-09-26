"""Tests for fuel price resolution against AEO Henry Hub trajectories."""

import numpy as np
import pytest

from market_sim.config.constants import (
    BIOMASS_PRICE_PER_MMBTU,
    CAISO_CITYGATE_TRANSPORT_ADDER,
    COAL_PRICE_BASE,
    COAL_PRICE_TRAJECTORIES,
    GAS_BASIS_DIFFERENTIAL,
    HENRY_HUB_TRAJECTORIES,
    NUCLEAR_FUEL_PRICE_HISTORICAL,
    OIL_PRICE_PER_MMBTU,
    START_YEAR,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    assemble_mc,
    generators_to_fleet_arrays,
    get_emission_rate,
)
from market_sim.data.fuel import (
    COAL_PRICE_LIGNITE_BY_YEAR,
    COAL_PRICE_PRB_BY_YEAR,
    _prb_monthly_actuals,
    apply_caiso_zonal_gas_basis,
    apply_coal_supply_pricing,
    apply_hub_basis_overlay,
    apply_miso_winter_citygate_daily,
    apply_miso_zonal_gas_basis,
    apply_nyiso_downstate_ct_gas_basis,
    apply_nyiso_zonal_gas_basis,
    apply_pjm_zonal_gas_basis,
    ercot_west_oversupply_collapse_freq,
    iso_hub_monthly_gas_prices,
    iso_monthly_gas_prices,
    load_winter_gas_basis,
    caiso_zonal_gas_basis_by_zone,
    miso_zonal_gas_basis_by_zone,
    nyiso_downstate_ct_gas_premium,
    nyiso_zonal_gas_offsets,
    pjm_zonal_gas_basis_by_zone,
    resolve_annual_coal_price,
    resolve_annual_gas_price,
    resolve_annual_oil_price,
    resolve_fuel_prices,
    resolve_nox_price,
    resolve_nuclear_fuel_price,
)
from market_sim.data import fuel
from market_sim.model.dispatch import solve_dispatch
from market_sim.policy.carbon import resolve_carbon_price

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
    jan_avg = prices[gas_idx, 0:744].mean()  # hours 0-743 = January
    may_avg = prices[gas_idx, 2880:3624].mean()  # hours 2880-3623 = May
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
    """Wind generators get zero fuel price; nuclear pays its derived fuel cost."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, 2030)
    wind_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["wind"]
    assert np.all(prices[wind_mask] == 0.0)


def test_nuclear_units_get_derived_fuel_price():
    """Nuclear generators pay the EIA-uranium-marketing-derived fuel cost."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, 2030)
    nuclear_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["nuclear"]
    expected = resolve_nuclear_fuel_price(_config(), 2030)
    assert expected > 0.0
    np.testing.assert_allclose(prices[nuclear_mask], expected)


def test_nuclear_fuel_price_holds_flat_beyond_2024():
    """Forecast years beyond 2024 hold the last real-dollar value flat."""
    last_year = max(NUCLEAR_FUEL_PRICE_HISTORICAL)
    expected = NUCLEAR_FUEL_PRICE_HISTORICAL[last_year]
    assert resolve_nuclear_fuel_price(_config(), 2050) == pytest.approx(expected)


def test_nuclear_fuel_price_override():
    """An explicit override bypasses the derived series entirely."""
    config = _config(nuclear_fuel_price_override=1.23)
    assert resolve_nuclear_fuel_price(config, 2030) == pytest.approx(1.23)


def test_coal_price_escalated_to_year():
    """Forecast-mode coal price tracks the AEO2025 real-growth ratio applied
    to the ISO's own COAL_PRICE_BASE anchor (P-1D — replaces the flat 1%/yr)."""
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(), fleet, 2030)
    coal_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["coal"]
    expected = resolve_annual_coal_price(_config(), 2030)
    np.testing.assert_allclose(prices[coal_mask], expected)


def test_coal_price_forecast_tracks_aeo_growth_ratio():
    """Forecast coal price ratio between two years matches the AEO trajectory
    ratio, not the retired flat 1%/yr escalation."""
    config = _config()
    fleet = _coal_fleet()
    prices_2026 = resolve_fuel_prices(config, fleet, 2026)
    prices_2036 = resolve_fuel_prices(config, fleet, 2036)
    trajectory = COAL_PRICE_TRAJECTORIES["mid"]
    expected_ratio = trajectory[2036] / trajectory[2026]
    actual_ratio = prices_2036[0, 0] / prices_2026[0, 0]
    assert abs(actual_ratio - expected_ratio) < 1e-4


def test_coal_price_backcast_still_uses_flat_escalation():
    """Backcast mode keeps the prior flat 1%/yr fallback byte-identical."""
    config = _config(mode="backcast")
    fleet = _coal_fleet()
    prices = resolve_fuel_prices(config, fleet, 2025)
    expected = COAL_PRICE_BASE["ERCOT"] * 1.01 ** (2025 - START_YEAR)
    np.testing.assert_allclose(prices[0, 0], expected)


def test_fuel_price_shape_is_n_gen_by_hours():
    """The resolved fuel price array is shaped ``(n_gen, T)``."""
    fleet = _sample_fleet(hours=24)
    prices = resolve_fuel_prices(_config(hours=24), fleet, 2030)
    assert prices.shape == (fleet.n_gen, 24)


def test_annual_gas_price_extrapolates_beyond_trajectory():
    """Years past the trajectory hold the last real value flat — no
    compounding tail (P-1D, replaces the retired last-YoY-ratio extrapolation)."""
    config = _config(gas_price_path="mid")
    traj = HENRY_HUB_TRAJECTORIES["mid"]
    expected = traj[2050] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    assert abs(resolve_annual_gas_price(config, 2051) - expected) < 1e-9
    assert abs(resolve_annual_gas_price(config, 2075) - expected) < 1e-9


def test_capacity_gas_lcoe_uses_trajectory():
    """The annual gas price feeding capacity LCOE matches the dispatch trajectory.

    The runner passes ``resolve_annual_gas_price`` into ``evolve_fleet`` so
    capacity new-entry LCOE screening charges gas units the same delivered
    price that hourly dispatch sees (seasonality aside).
    """
    config = _config(gas_price_path="mid")
    year = 2035
    expected_gas = HENRY_HUB_TRAJECTORIES["mid"][year] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    assert resolve_annual_gas_price(config, year) == expected_gas

    # Dispatch with seasonality off resolves to the same annual price.
    fleet = _sample_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, year)
    np.testing.assert_allclose(prices[0], expected_gas)


def test_gas_price_factor_monotonic():
    """Raising gas_price_factor monotonically raises the delivered price."""
    year = 2035
    prices = [
        resolve_annual_gas_price(
            _config(gas_price_path="mid", gas_price_factor=f), year
        )
        for f in (0.8, 1.0, 1.2)
    ]
    assert prices == sorted(prices)
    assert prices[0] < prices[1] < prices[2]


def test_gas_price_factor_scales_trajectory():
    """gas_price_factor multiplies the trajectory value before the basis adder."""
    config = _config(gas_price_path="mid", gas_price_factor=1.2)
    year = 2035
    expected = (
        HENRY_HUB_TRAJECTORIES["mid"][year] * 1.2 + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    )
    assert abs(resolve_annual_gas_price(config, year) - expected) < 1e-9


def test_gas_price_factor_neutral_default_matches_unscaled():
    """The neutral 1.0 default reproduces today's trajectory exactly."""
    config = _config(gas_price_path="mid")
    assert config.gas_price_factor == 1.0
    year = 2035
    expected = HENRY_HUB_TRAJECTORIES["mid"][year] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    assert resolve_annual_gas_price(config, year) == expected


def test_gas_price_factor_does_not_apply_to_override():
    """The measured gas_price_override is never scaled by gas_price_factor."""
    config = _config(
        gas_price_path="mid", gas_price_override=2.54, gas_price_factor=1.5
    )
    expected = 2.54 + GAS_BASIS_DIFFERENTIAL["ERCOT"]
    assert resolve_annual_gas_price(config, 2030) == expected


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
        unit_id=f"COAL_{supply or 'none'}",
        name="Coal",
        zone="north",
        fuel_type="coal",
        pmax_mw=500.0,
        heat_rate=10.0,
        coal_supply=supply,
    )


def test_coal_supply_pricing_uses_year_trajectory():
    """Lignite stays on the per-year curve; PRB takes the measured monthly
    reporter series in historical years (annual trajectory otherwise)."""
    config = ScenarioConfig()
    gens = [_coal_gen("lignite"), _coal_gen("prb"), _coal_gen("")]
    fuel_prices = np.full((3, 24), 2.0)
    apply_coal_supply_pricing(fuel_prices, gens, config, 2024)
    assert np.allclose(fuel_prices[0], COAL_PRICE_LIGNITE_BY_YEAR[2024])
    # 2024 is historical: PRB prices at the measured EIA-923 PRB reporter
    # series (January, for a 24-hour horizon), take-or-pay discounted. With
    # no F923 parquet shipped the flat annual trajectory is the fallback.
    monthly = _prb_monthly_actuals().get(2024)
    expected_prb = monthly[0] if monthly is not None else COAL_PRICE_PRB_BY_YEAR[2024]
    assert np.allclose(
        fuel_prices[1],
        expected_prb * config.coal_prb_contract_passthrough,
    )
    # Untagged coal keeps the generic price already in the array.
    assert np.allclose(fuel_prices[2], 2.0)


def test_coal_supply_pricing_forward_year_uses_trajectory():
    """A forward year with no F923 reports prices PRB at the annual curve.

    2027 is the first year with no F923 receipts on disk — the 2022/H1-2026
    holdout intake landed measured receipts through Apr 2026, so 2026 now
    resolves from measured data rather than the trajectory.
    """
    config = ScenarioConfig()
    gens = [_coal_gen("prb")]
    fp = np.full((1, 24), 2.0)
    apply_coal_supply_pricing(fp, gens, config, 2027)
    assert np.allclose(
        fp[0],
        COAL_PRICE_PRB_BY_YEAR[2027] * config.coal_prb_contract_passthrough,
    )


def test_lignite_flat_then_escalates():
    """Lignite is $1.45 flat 2023-2025, then escalates at inflation."""
    assert COAL_PRICE_LIGNITE_BY_YEAR[2023] == 1.45
    assert COAL_PRICE_LIGNITE_BY_YEAR[2025] == 1.45
    assert COAL_PRICE_LIGNITE_BY_YEAR[2026] > 1.45
    assert COAL_PRICE_LIGNITE_BY_YEAR[2050] > COAL_PRICE_LIGNITE_BY_YEAR[2030]


def test_prb_forward_commodity_decline_after_2030():
    """PRB forward: the curve rises to 2030, then commodity decline bends it."""
    # Calibration anchors.
    assert COAL_PRICE_PRB_BY_YEAR[2023] == 2.15
    assert COAL_PRICE_PRB_BY_YEAR[2024] == 2.00
    # Commodity holds flat through 2030, so the curve climbs on rail inflation.
    assert COAL_PRICE_PRB_BY_YEAR[2030] > COAL_PRICE_PRB_BY_YEAR[2026]
    # From 2031 the commodity component declines 1.5%/yr — the year-over-year
    # rise slows versus the pre-2031 (rail-inflation-only) step.
    pre = COAL_PRICE_PRB_BY_YEAR[2030] - COAL_PRICE_PRB_BY_YEAR[2029]
    post = COAL_PRICE_PRB_BY_YEAR[2032] - COAL_PRICE_PRB_BY_YEAR[2031]
    assert post < pre


def test_coal_supply_pricing_year_outside_trajectory():
    """A run year before the coal trajectory leaves the generic price."""
    config = ScenarioConfig()
    gens = [_coal_gen("prb")]
    fp = np.full((1, 4), 2.0)
    apply_coal_supply_pricing(fp, gens, config, 2010)
    assert np.allclose(fp[0], 2.0)


# --- Oil and biomass fuel pricing & dispatch ------------------------------


def _oil_biomass_fleet(hours: int = 24):
    """Return a fleet with gas CC, an oil peaker and a biomass unit."""
    generators = [
        Generator(
            unit_id="GAS_CC",
            name="CC",
            zone="north",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            heat_rate=7.0,
            vom=2.0,
            eford=0.0,
        ),
        Generator(
            unit_id="OIL",
            name="Oil Peaker",
            zone="north",
            fuel_type="oil",
            pmax_mw=100.0,
            heat_rate=13.5,
            vom=4.5,
            emission_rate_co2=1.0,
            eford=0.0,
        ),
        Generator(
            unit_id="BIO",
            name="Biomass",
            zone="south",
            fuel_type="biomass",
            pmax_mw=80.0,
            heat_rate=13.5,
            vom=5.0,
            emission_rate_co2=0.0,
            eford=0.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _ZONE_NAMES, hours=hours)


def test_oil_units_get_oil_price():
    """Forecast-mode oil generators price at the AEO2025 oil trajectory."""
    fleet = _oil_biomass_fleet()
    config = _config(gas_seasonality=False)
    prices = resolve_fuel_prices(config, fleet, 2030)
    oil_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["oil"]
    expected = resolve_annual_oil_price(config, 2030)
    np.testing.assert_allclose(prices[oil_mask], expected)


def test_oil_units_backcast_uses_flat_fallback():
    """Backcast mode keeps the flat OIL_PRICE_PER_MMBTU fallback byte-identical."""
    fleet = _oil_biomass_fleet()
    config = _config(mode="backcast", gas_seasonality=False)
    prices = resolve_fuel_prices(config, fleet, 2024)
    oil_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["oil"]
    np.testing.assert_allclose(prices[oil_mask], OIL_PRICE_PER_MMBTU)


def test_biomass_units_get_biomass_price():
    """Biomass generators are priced at the delivered biomass fuel cost."""
    fleet = _oil_biomass_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, 2030)
    bio_mask = fleet.fuel_type_idx == FUEL_TYPE_MAP["biomass"]
    np.testing.assert_allclose(prices[bio_mask], BIOMASS_PRICE_PER_MMBTU)


def test_oil_priced_above_gas_and_biomass():
    """Oil is the dearest fuel; biomass sits near cheap fuel parity."""
    fleet = _oil_biomass_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, 2030)
    gas_idx = np.where(fleet.fuel_type_idx == FUEL_TYPE_MAP["gas_cc"])[0][0]
    oil_idx = np.where(fleet.fuel_type_idx == FUEL_TYPE_MAP["oil"])[0][0]
    bio_idx = np.where(fleet.fuel_type_idx == FUEL_TYPE_MAP["biomass"])[0][0]
    assert prices[oil_idx, 0] > prices[gas_idx, 0]
    assert prices[oil_idx, 0] > prices[bio_idx, 0]


# --- Dual-fuel switching (doc 03 Pack G) -----------------------------------

_DF_PLANT = 1234  # dual-fuel capable plant (monkeypatched lookup)
_PLAIN_PLANT = 5678  # gas-only plant


def _dual_fuel_fleet(hours: int = 24):
    """Return a fleet with a dual-fuel CT, a gas-only CT and an oil unit."""
    generators = [
        Generator(
            unit_id="CT_DUAL",
            name="Dual-Fuel CT",
            zone="north",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            heat_rate=11.0,
            eford=0.0,
            plant_code=_DF_PLANT,
            plant_group="CT_PEAKER",
        ),
        Generator(
            unit_id="CT_PLAIN",
            name="Gas-Only CT",
            zone="north",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            heat_rate=11.0,
            eford=0.0,
            plant_code=_PLAIN_PLANT,
            plant_group="CT_PEAKER",
        ),
        Generator(
            unit_id="OIL",
            name="Oil Peaker",
            zone="south",
            fuel_type="oil",
            pmax_mw=50.0,
            heat_rate=13.5,
            eford=0.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _ZONE_NAMES, hours=hours)


def _patch_dual_fuel_capability(monkeypatch):
    """Pin the EIA-860 dual-fuel lookup to the synthetic test plant."""
    monkeypatch.setattr(
        "market_sim.data.fuel.dual_fuel_plant_groups",
        lambda: frozenset({(_DF_PLANT, "CT_PEAKER")}),
    )


def test_dual_fuel_switches_to_oil_above_parity(monkeypatch):
    """A dual-fuel unit pays the oil price when gas exceeds oil parity."""
    _patch_dual_fuel_capability(monkeypatch)
    fleet = _dual_fuel_fleet()
    # Delivered gas = 25 + PJM basis, far above the forecast-year oil price
    # (no F923 petroleum data, so oil parity is the AEO2025 trajectory).
    config = ScenarioConfig(
        iso="PJM",
        hours=24,
        gas_seasonality=False,
        gas_price_override=25.0,
        dual_fuel_switching=True,
    )
    prices = resolve_fuel_prices(config, fleet, 2030)
    delivered_gas = resolve_annual_gas_price(config, 2030)
    oil_price = resolve_annual_oil_price(config, 2030)
    assert delivered_gas > oil_price
    np.testing.assert_allclose(prices[0], oil_price)  # switched
    np.testing.assert_allclose(prices[1], delivered_gas)  # gas-only
    np.testing.assert_allclose(prices[2], oil_price)  # oil unit


def test_dual_fuel_switch_mask_marks_only_switched_capable_units(monkeypatch):
    """The mask flags the dual-fuel unit's switched hours, nothing else."""
    from market_sim.data.fuel import dual_fuel_switch_mask

    _patch_dual_fuel_capability(monkeypatch)
    fleet = _dual_fuel_fleet(hours=24)
    config = ScenarioConfig(
        iso="PJM",
        hours=24,
        gas_seasonality=False,
        gas_price_override=25.0,
        dual_fuel_switching=True,
    )
    # Pre-min gas price array (what run_year passes before the dual-fuel cap).
    gas_prices = resolve_fuel_prices(config, fleet, 2030, apply_monthly=False)
    mask = dual_fuel_switch_mask(gas_prices, fleet, config, 2030)
    # Row 0 is the dual-fuel CT (gas $25 > oil $18 → switched every hour);
    # row 1 the gas-only CT and row 2 the oil unit are never re-attributed.
    assert mask[0].all()
    assert not mask[1].any()
    assert not mask[2].any()

    # Below parity: nothing switches.
    cheap = config.with_overrides(gas_price_override=2.0)
    gas_cheap = resolve_fuel_prices(cheap, fleet, 2030, apply_monthly=False)
    assert not dual_fuel_switch_mask(gas_cheap, fleet, cheap, 2030).any()

    # Flag off: empty mask regardless of price.
    off = config.with_overrides(dual_fuel_switching=False)
    assert not dual_fuel_switch_mask(gas_prices, fleet, off, 2030).any()


def test_dual_fuel_no_switch_below_parity(monkeypatch):
    """Cheap gas leaves a dual-fuel unit on its gas price (min is gas)."""
    _patch_dual_fuel_capability(monkeypatch)
    fleet = _dual_fuel_fleet()
    config = ScenarioConfig(
        iso="PJM",
        hours=24,
        gas_seasonality=False,
        gas_price_override=2.0,
        dual_fuel_switching=True,
    )
    prices = resolve_fuel_prices(config, fleet, 2030)
    delivered_gas = resolve_annual_gas_price(config, 2030)
    assert delivered_gas < OIL_PRICE_PER_MMBTU
    np.testing.assert_allclose(prices[0], delivered_gas)
    np.testing.assert_allclose(prices[1], delivered_gas)


def test_dual_fuel_off_by_default_ercot_unchanged(monkeypatch):
    """With the flag off (the default — ERCOT), prices are byte-identical."""
    _patch_dual_fuel_capability(monkeypatch)
    fleet = _dual_fuel_fleet()
    base = ScenarioConfig(
        iso="ERCOT",
        hours=24,
        gas_seasonality=False,
        gas_price_override=25.0,
    )
    assert base.dual_fuel_switching is False
    prices = resolve_fuel_prices(base, fleet, 2030)
    delivered_gas = resolve_annual_gas_price(base, 2030)
    np.testing.assert_allclose(prices[0], delivered_gas)
    np.testing.assert_allclose(prices[1], delivered_gas)


def test_dual_fuel_caps_only_above_parity_hours(monkeypatch):
    """The per-hour min caps spike hours and leaves cheap-gas hours alone."""
    from market_sim.data.fuel import apply_dual_fuel_pricing

    _patch_dual_fuel_capability(monkeypatch)
    fleet = _dual_fuel_fleet(hours=4)
    config = ScenarioConfig(
        iso="PJM",
        hours=4,
        dual_fuel_switching=True,
    )
    oil_price = resolve_annual_oil_price(config, 2030)
    # The middle hour's gas (10.0) sits clearly below the delivered oil price so
    # it stays a cheap-gas hour the cap must leave alone -- robust to the oil
    # trajectory level (AEO2026 mid 2030 oil is ~$17.8/MMBtu, FF-G2 vintage).
    gas = np.array([3.0, 30.0, 10.0, 50.0])
    fuel_prices = np.vstack([gas, gas, np.full(4, oil_price)])
    apply_dual_fuel_pricing(fuel_prices, fleet, config, 2030)
    np.testing.assert_allclose(fuel_prices[0], [3.0, oil_price, 10.0, oil_price])
    np.testing.assert_allclose(fuel_prices[1], gas)  # gas-only untouched


def test_dual_fuel_nyiso_switches_on_parity(monkeypatch):
    """NYISO dual-fuel units cap at oil when winter gas crosses parity (P13).

    Mirrors the PJM parity test for the NYISO instantiation (doc-07 design
    decision 3): with the gas leg spiked past distillate parity, the flagged
    NYISO dual-fuel CT prices off oil while the gas-only CT keeps its gas
    price.
    """
    _patch_dual_fuel_capability(monkeypatch)
    fleet = _dual_fuel_fleet()
    config = ScenarioConfig(
        iso="NYISO",
        hours=24,
        gas_seasonality=False,
        gas_price_override=25.0,
        dual_fuel_switching=True,
    )
    prices = resolve_fuel_prices(config, fleet, 2030)
    delivered_gas = resolve_annual_gas_price(config, 2030)
    oil_price = resolve_annual_oil_price(config, 2030)
    assert delivered_gas > oil_price
    np.testing.assert_allclose(prices[0], oil_price)  # switched to oil
    np.testing.assert_allclose(prices[1], delivered_gas)  # gas-only
    np.testing.assert_allclose(prices[2], oil_price)  # pure-oil unit


def test_calibration_config_dual_fuel_gating():
    """The backcast config activates dual-fuel for the NE/NY/PJM cluster only.

    Test req #4 / doc-07 P13: NYISO and NEISO switch on (NE/NY winter
    switching), PJM stays on (unchanged), and ERCOT/CAISO/MISO stay off
    (byte-identical). Guards the ERCOT/PJM/CAISO regression.
    """
    from scripts.run_calibration import _calibration_config

    on = {"NYISO", "NEISO", "PJM"}
    for iso in ("NYISO", "NEISO", "PJM", "ERCOT", "CAISO", "MISO"):
        cfg = _calibration_config(2023, iso, 24, 3.0)
        assert cfg.dual_fuel_switching is (iso in on), iso


def test_oil_peaker_dispatches_only_at_high_prices():
    """An oil peaker stays idle until demand exceeds cheaper capacity.

    With a 300 MW gas CC (MC ~$23/MWh) and a 100 MW oil unit (MC ~$248/MWh)
    in one zone, an 80 MW hour is served entirely by gas (oil idle, low
    price), while a 350 MW hour exhausts gas and forces the oil peaker on,
    setting a much higher clearing price.
    """
    hours = 2
    generators = [
        Generator(
            unit_id="GAS_CC",
            name="CC",
            zone="north",
            fuel_type="gas_cc",
            pmax_mw=300.0,
            heat_rate=7.0,
            vom=2.0,
            eford=0.0,
        ),
        Generator(
            unit_id="OIL",
            name="Oil Peaker",
            zone="north",
            fuel_type="oil",
            pmax_mw=100.0,
            heat_rate=13.5,
            vom=4.5,
            emission_rate_co2=1.0,
            eford=0.0,
        ),
    ]
    fleet = generators_to_fleet_arrays(generators, ["north"], hours=hours)
    config = _config(gas_seasonality=False, hours=hours)
    fuel_prices = resolve_fuel_prices(config, fleet, 2030)
    mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)

    demand = np.array([[80.0, 350.0]])  # low-demand then high-demand hour
    result = solve_dispatch(
        fleet,
        demand,
        mc=mc,
        T=hours,
        wind_cf=np.zeros((1, hours)),
        wind_cap=np.zeros(1),
        solar_cf=np.zeros((1, hours)),
        solar_cap=np.zeros(1),
    )
    oil_idx = np.where(fleet.fuel_type_idx == FUEL_TYPE_MAP["oil"])[0][0]
    # Idle in the cheap hour, dispatched in the scarce hour.
    assert result.dispatch[oil_idx, 0] < 1e-6
    assert result.dispatch[oil_idx, 1] > 1.0
    # The clearing price is far higher when the oil peaker is marginal.
    assert result.prices[0, 1] > result.prices[0, 0]


# --- CA cap-and-trade in CAISO marginal cost (CARB allowance pricing) ------


def _cc_fleet(heat_rate: float = 7.0, hours: int = 24):
    """Return a single gas-CC fleet at the given heat rate.

    ``emission_rate_co2`` is set the way the fleet loaders set it —
    ``get_emission_rate(fuel, heat_rate)`` — so the carbon term in
    ``assemble_mc`` is exercised exactly as in a real fleet.
    """
    generators = [
        Generator(
            unit_id="GAS_CC",
            name="CC",
            zone="north",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            heat_rate=heat_rate,
            vom=2.0,
            eford=0.0,
            emission_rate_co2=get_emission_rate("gas_cc", heat_rate),
        ),
    ]
    return generators_to_fleet_arrays(generators, ["north"], hours=hours)


def test_caiso_backcast_gas_mc_includes_carbon():
    """CAISO 2024 gas MC carries the CARB allowance cost; off elsewhere."""
    hours = 24
    fleet = _cc_fleet(hours=hours)
    caiso = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
    )
    fuel_prices = resolve_fuel_prices(caiso, fleet, 2024)
    carbon = resolve_carbon_price(caiso, 2024)
    assert carbon == 35.23  # 2024 CARB quarterly-auction settlement average
    mc_with = assemble_mc(fleet, fuel_prices, carbon_price=carbon)
    mc_without = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
    uplift = mc_with - mc_without
    expected = get_emission_rate("gas_cc", 7.0) * carbon
    np.testing.assert_allclose(uplift, expected)
    assert expected > 10.0  # the carbon wedge is first-order, ~$14/MWh

    # ERCOT and PJM backcasts resolve to a zero carbon price: identical MC.
    for iso in ("ERCOT", "PJM"):
        other = ScenarioConfig(
            iso=iso,
            mode="backcast",
            weather_year=2024,
            gas_seasonality=False,
            hours=hours,
        )
        assert resolve_carbon_price(other, 2024) == 0.0


def test_cc_7000_hr_at_35_per_ton_uplift_near_13_per_mwh():
    """A 7.0 HR gas CC at $35/t shows the expected ~$13-14/MWh uplift."""
    fleet = _cc_fleet(heat_rate=7.0, hours=24)
    fuel_prices = np.zeros((fleet.n_gen, 24))  # isolate the carbon term
    uplift = assemble_mc(fleet, fuel_prices, carbon_price=35.0) - assemble_mc(
        fleet, fuel_prices, carbon_price=0.0
    )
    # 7.0 MMBtu/MWh x 0.057 tCO2/MMBtu (model gas CO2 factor) x $35/t.
    np.testing.assert_allclose(uplift, 7.0 * 0.057 * 35.0)
    assert 12.0 < uplift[0, 0] < 15.0


def test_nyiso_backcast_years_pay_rggi_allowance_price():
    """NYISO 2023-2025 carbon resolves to the RGGI auction-average price."""
    config = ScenarioConfig(iso="NYISO", mode="backcast", weather_year=2023)
    # Simple mean of the four quarterly RGGI clearing prices each year
    # (constants.STATE_CARBON_PRICE_BY_ISO citation).
    assert resolve_carbon_price(config, 2023) == 13.49
    assert resolve_carbon_price(config, 2024) == 20.71
    assert resolve_carbon_price(config, 2025) == 22.09
    # RGGI rose 2023->2025; the price level moves with it.
    assert resolve_carbon_price(config, 2023) < resolve_carbon_price(config, 2025)


def test_nyiso_rggi_off_with_state_carbon_pricing_flag():
    """The state_carbon_pricing toggle disables RGGI for NYISO."""
    config = ScenarioConfig(
        iso="NYISO",
        mode="backcast",
        weather_year=2024,
        state_carbon_pricing=False,
    )
    assert resolve_carbon_price(config, 2024) == 0.0


def test_nyiso_backcast_gas_mc_includes_rggi():
    """NYISO gas MC carries the RGGI allowance cost; unchanged elsewhere."""
    hours = 24
    fleet = _cc_fleet(hours=hours)
    nyiso = ScenarioConfig(
        iso="NYISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
    )
    fuel_prices = resolve_fuel_prices(nyiso, fleet, 2024)
    carbon = resolve_carbon_price(nyiso, 2024)
    assert carbon == 20.71  # 2024 RGGI auction average
    mc_with = assemble_mc(fleet, fuel_prices, carbon_price=carbon)
    mc_without = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
    uplift = mc_with - mc_without
    expected = get_emission_rate("gas_cc", 7.0) * carbon
    np.testing.assert_allclose(uplift, expected)

    # ERCOT/PJM stay carbon-free, and CAISO keeps its own CARB price — the
    # NYISO addition leaves every other ISO's resolved carbon price unchanged.
    for iso in ("ERCOT", "PJM"):
        other = ScenarioConfig(
            iso=iso,
            mode="backcast",
            weather_year=2024,
            gas_seasonality=False,
            hours=hours,
        )
        assert resolve_carbon_price(other, 2024) == 0.0
    caiso = ScenarioConfig(iso="CAISO", mode="backcast", weather_year=2024)
    assert resolve_carbon_price(caiso, 2023) == 33.03
    assert resolve_carbon_price(caiso, 2024) == 35.23
    assert resolve_carbon_price(caiso, 2025) == 28.06


def test_neiso_backcast_gas_mc_includes_rggi():
    """NEISO 2023-25 gas MC carries the RGGI allowance cost; off elsewhere.

    The constants entry is the per-year average of the four RGGI quarterly
    auction clearing prices, converted from $/short ton (as RGGI clears) to
    the model's $/metric tonne. A 7.0-HR CC at the 2023 average (~$14.9/t)
    shows the doc-08 "~$5-7/MWh on a CC" uplift.
    """
    hours = 24
    fleet = _cc_fleet(hours=hours)
    expected_by_year = {2023: 14.87, 2024: 22.83, 2025: 24.35}
    for year, expected in expected_by_year.items():
        neiso = ScenarioConfig(
            iso="NEISO",
            mode="backcast",
            weather_year=year,
            gas_seasonality=False,
            hours=hours,
        )
        carbon = resolve_carbon_price(neiso, year)
        assert carbon == expected
        zero_fuel = np.zeros((fleet.n_gen, hours))  # isolate the carbon term
        uplift = assemble_mc(fleet, zero_fuel, carbon_price=carbon) - assemble_mc(
            fleet, zero_fuel, carbon_price=0.0
        )
        np.testing.assert_allclose(uplift, get_emission_rate("gas_cc", 7.0) * carbon)
        # First-order but below the CAISO CARB wedge: $5-11/MWh on a CC.
        assert 5.0 < uplift[0, 0] < 11.0
    # 2023 specifically lands in the doc-08 $5-7/MWh band.
    uplift_2023 = get_emission_rate("gas_cc", 7.0) * expected_by_year[2023]
    assert 5.0 < uplift_2023 < 7.0

    # Forward years carry the PROJECTED RGGI program price (EM-6 seam fix):
    # the last measured clearing price (2025, $24.35/t) escalated at the RGGI
    # CCR-band rate (7%/yr). No longer zero — forecast carbon now flows through
    # the same channel as backcast. Source: cap_and_trade.projected_price.
    forward = ScenarioConfig(iso="NEISO", gas_seasonality=False, hours=hours)
    assert resolve_carbon_price(forward, 2026) == pytest.approx(24.35 * 1.07)
    assert resolve_carbon_price(forward, 2026) > resolve_carbon_price(forward, 2025)

    # ERCOT/PJM stay at zero; the CAISO CARB series is untouched.
    for iso in ("ERCOT", "PJM"):
        other = ScenarioConfig(
            iso=iso,
            mode="backcast",
            weather_year=2024,
            gas_seasonality=False,
            hours=hours,
        )
        assert resolve_carbon_price(other, 2024) == 0.0
    caiso = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
    )
    assert resolve_carbon_price(caiso, 2024) == 35.23


def test_carbon_price_delta_is_additive_on_every_precedence_path():
    """carbon_price_delta rides ON TOP of whatever the precedence chain resolves.

    The D26 FC-6 P1 arm construction (repairing the D23 premise inversion):
    on a program ISO the delta shifts the projected trajectory uniformly, so a
    +25 arm is a strictly positive increase in EVERY horizon year instead of a
    replacement that CUT an escalating base. Default 0.0 is an exact no-op.
    """
    # Path (2): program adder (NEISO projected RGGI escalator, forecast).
    base = ScenarioConfig(iso="NEISO", gas_seasonality=False, hours=24)
    arm = ScenarioConfig(
        iso="NEISO", gas_seasonality=False, hours=24, carbon_price_delta=25.0
    )
    for year in (2026, 2030, 2040, 2050):
        b = resolve_carbon_price(base, year)
        assert b > 0.0  # premise: the base trajectory is armed, not zero
        assert resolve_carbon_price(arm, year) == pytest.approx(b + 25.0)

    # Path (1): a nonzero carbon_price override still wins the chain; the
    # delta adds to it rather than being swallowed by the replacement.
    over = ScenarioConfig(
        iso="ERCOT", carbon_price=25.0, carbon_price_delta=10.0, hours=24
    )
    assert resolve_carbon_price(over, 2030) == pytest.approx(35.0)

    # Path (3)/zero fallthrough: a no-program ISO at the "zero" path resolves
    # exactly the delta.
    ercot = ScenarioConfig(iso="ERCOT", hours=24, carbon_price_delta=25.0)
    assert resolve_carbon_price(ercot, 2030) == pytest.approx(25.0)

    # Default is an exact no-op (bit-equal, not merely approx).
    assert resolve_carbon_price(base, 2030) == resolve_carbon_price(
        ScenarioConfig(iso="NEISO", gas_seasonality=False, hours=24), 2030
    )


def test_carbon_price_delta_is_forecast_only_rule13():
    """A nonzero delta in backcast mode raises — never a residual channel."""
    with pytest.raises(ValueError, match="carbon_price_delta"):
        ScenarioConfig(
            iso="NEISO",
            mode="backcast",
            weather_year=2024,
            hours=24,
            carbon_price_delta=5.0,
        )


def test_cc_7000_hr_at_18_per_ton_uplift_5_to_7_per_mwh():
    """A 7.0 HR gas CC at ~$18/t RGGI shows the doc-07 ~$5-7/MWh uplift."""
    fleet = _cc_fleet(heat_rate=7.0, hours=24)
    fuel_prices = np.zeros((fleet.n_gen, 24))  # isolate the carbon term
    uplift = assemble_mc(fleet, fuel_prices, carbon_price=18.0) - assemble_mc(
        fleet, fuel_prices, carbon_price=0.0
    )
    # 7.0 MMBtu/MWh x 0.057 tCO2/MMBtu x $18/t = $7.18/MWh.
    np.testing.assert_allclose(uplift, 7.0 * 0.057 * 18.0)
    assert 5.0 <= uplift[0, 0] <= 7.5
    # The measured RGGI years (2023 $13.49 -> 2025 $22.09) bracket the doc-07
    # design-decision-4 band of ~$5-9/MWh for a ~0.4 t/MWh CC.
    er = get_emission_rate("gas_cc", 7.0)
    assert 5.0 <= er * 13.49 <= 9.0
    assert 5.0 <= er * 22.09 <= 9.0


def test_winter_gas_basis_absent_falls_back_to_923(tmp_path):
    """Forward years (no measured basis row) resolve to None (fall back)."""
    config = ScenarioConfig(iso="NYISO", mode="backcast", weather_year=2023)
    # The in-repo CSV now carries every ISO's measured EIA citygate basis for
    # the backcast years (2015-2026), so a forward year is the genuine "absent"
    # case: no basis row -> None -> the gas path falls back to the measured
    # ISO-month 923 series.
    assert load_winter_gas_basis(config, 2035) is None
    # An absent path is likewise None (a tree with no basis CSV at all).
    missing = tmp_path / "nope.csv"
    assert load_winter_gas_basis(config, 2023, path=missing) is None


def test_winter_gas_basis_loads_when_present(tmp_path):
    """When U4 lands, the per-ISO monthly hub basis is read by month."""
    csv = tmp_path / "gas_basis_by_iso_month.csv"
    csv.write_text(
        "iso,year,month,hub,basis_usd_mmbtu,source\n"
        "NYISO,2023,1,Transco Z6 NY,6.50,ICE\n"
        "NYISO,2023,2,Transco Z6 NY,4.20,ICE\n"
        "NYISO,2023,7,Transco Z6 NY,-0.30,ICE\n"
        "PJM,2023,1,TETCO M3,2.00,ICE\n"
    )
    config = ScenarioConfig(iso="NYISO", mode="backcast", weather_year=2023)
    basis = load_winter_gas_basis(config, 2023, path=csv)
    assert basis is not None
    assert basis[0] == 6.50  # January winter spike
    assert basis[1] == 4.20  # February
    assert basis[6] == -0.30  # July shoulder discount
    assert np.isnan(basis[3])  # April unreported -> NaN (caller fills from 923)
    # A year with no rows for this ISO falls back to None.
    assert load_winter_gas_basis(config, 2024, path=csv) is None


# --- Algonquin hub-month basis overlay (NEISO winter gas blowout) -----------


def test_hub_basis_overlay_replaces_covered_months(tmp_path):
    """Covered months are repriced at HH-month + basis; others untouched.

    A synthetic basis CSV with a single January 2024 row (+$10 over the
    measured Jan-2024 Henry Hub of $3.1762) must reprice every gas unit's
    January hours to $13.1762 while February (no row) and the coal row keep
    their prior prices. With the flag off the overlay is a strict no-op.
    """
    basis_csv = tmp_path / "basis.csv"
    basis_csv.write_text(
        "iso,year,month,hub,basis_usd_mmbtu,source\nNEISO,2024,1,AGT,10.0,test\n"
    )
    hours = 31 * 24 + 28 * 24  # January + February 2024
    fleet = _sample_fleet(hours=hours)
    config = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
        gas_hub_basis_overlay=True,
    )
    fuel_prices = np.full((fleet.n_gen, hours), 4.0)
    before = fuel_prices.copy()
    apply_hub_basis_overlay(fuel_prices, fleet, config, 2024, basis_path=basis_csv)

    gas_rows = np.isin(
        fleet.fuel_type_idx,
        (
            FUEL_TYPE_MAP["gas_cc"],
            FUEL_TYPE_MAP["gas_ct"],
        ),
    )
    jan = slice(0, 31 * 24)
    feb = slice(31 * 24, hours)
    np.testing.assert_allclose(fuel_prices[gas_rows, jan], 3.1762 + 10.0)
    np.testing.assert_allclose(fuel_prices[gas_rows, feb], 4.0)
    # Non-gas generators never see the hub price.
    np.testing.assert_allclose(fuel_prices[~gas_rows], before[~gas_rows])

    # Flag off: byte-identical no-op.
    off = before.copy()
    apply_hub_basis_overlay(
        off,
        fleet,
        config.with_overrides(gas_hub_basis_overlay=False),
        2024,
        basis_path=basis_csv,
    )
    np.testing.assert_array_equal(off, before)


def test_neiso_hub_basis_overlay_winter_blowout_real_data():
    """A January AGT-spike hour prices gas far above the annual average.

    Uses the committed gas_basis_by_iso_month.csv (ISO-NE MA gas index /
    Algonquin Citygate, isonewswire.com): Jan-2025 measured $16.92/MMBtu
    (basis +$12.79 over HH) against a ~$4.6 annual mean, so winter gas MC
    blows out well above plant-average levels — the ISO-NE price driver.
    """
    config = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        weather_year=2025,
        gas_price_override=3.53,
        hours=_HOURS,
        gas_hub_basis_overlay=True,
    )
    monthly = iso_hub_monthly_gas_prices(config, 2025)
    if monthly is None:
        import pytest

        pytest.skip("gas_basis_by_iso_month.csv has no NEISO rows")
    # Jan/Feb/Dec 2025 reconstruct the measured ISO-NE index blowout.
    assert monthly[0] > 15.0  # Jan-25: 4.13 HH + 12.79 basis = 16.92
    assert monthly[1] > 13.0  # Feb-25: 14.62
    assert monthly[11] > 13.0  # Dec-25: 14.90
    # The 2025 ISO-NE index is now complete (the Jul/Sep gap was interpolated
    # from the bracketing months), so every month carries a measured hub level.
    assert not np.isnan(monthly).any()
    assert monthly[7] < 3.5  # Aug-25 is a cheap shoulder month (no scarcity)
    assert np.nanmin(monthly) < 3.0  # shoulder months stay cheap

    fleet = _cc_fleet(hours=_HOURS)
    prices = resolve_fuel_prices(config, fleet, 2025)
    mc = assemble_mc(fleet, prices, carbon_price=0.0)
    jan_mc = mc[0, : 31 * 24].mean()
    annual_mc = mc[0].mean()
    assert jan_mc > 2.0 * annual_mc, (
        f"January gas MC {jan_mc:.1f} should blow out far above the "
        f"annual average {annual_mc:.1f}"
    )


def test_neiso_hub_overlay_drives_dual_fuel_switch(monkeypatch):
    """P13: the AGT hub-basis overlay is what trips the dual-fuel switch.

    The end-to-end NEISO winter mechanism (doc-08 decisions 1-2): the
    measured Algonquin Citygate spot (``apply_hub_basis_overlay``) blows the
    gas price out past distillate parity in the cold month, and because the
    overlay runs *before* :func:`apply_dual_fuel_pricing` in
    :func:`resolve_fuel_prices`, the dual-fuel unit then caps that blown-out
    hub price at oil — it *consumes* the overlay. A gas-only unit eats the
    full hub spike; a cheap month leaves both on gas. Driven through the real
    resolver with the hub series monkeypatched to a Jan blowout so the test
    does not depend on a specific calendar year's committed basis.
    """
    _patch_dual_fuel_capability(monkeypatch)
    # Jan AGT spot far above distillate parity ($18); July cheap. The overlay
    # replaces the gas price outright in covered months (it is the measured
    # constrained-hub spot, not a basis adder).
    hub = np.full(12, 2.0)
    hub[0] = 30.0
    monkeypatch.setattr(
        "market_sim.data.fuel.iso_hub_monthly_gas_prices",
        lambda config, year, basis_path=None: hub,
    )
    hours = 31 * 24 + 28 * 24 + 31 * 24  # Jan-Mar, enough to span the spike
    fleet = _dual_fuel_fleet(hours=hours)
    config = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        weather_year=2030,
        hours=hours,
        gas_seasonality=False,
        gas_hub_basis_overlay=True,
        dual_fuel_switching=True,
    )
    # 2030: no F923 petroleum data, so oil parity is the flat default.
    prices = resolve_fuel_prices(config, fleet, 2030)
    jan = slice(0, 31 * 24)
    feb = slice(31 * 24, 31 * 24 + 28 * 24)
    # Dual-fuel unit: switched to oil in the AGT-spike month, on (cheap) gas
    # in the shoulder month.
    np.testing.assert_allclose(prices[0, jan], OIL_PRICE_PER_MMBTU)
    np.testing.assert_allclose(prices[0, feb], 2.0)
    # Gas-only unit eats the full hub spike — no oil backup to switch to.
    np.testing.assert_allclose(prices[1, jan], 30.0)
    np.testing.assert_allclose(prices[1, feb], 2.0)
    # The pure-oil steam unit always prices off oil.
    np.testing.assert_allclose(prices[2, jan], OIL_PRICE_PER_MMBTU)


def test_neiso_monthly_agt_basis_stays_below_distillate_parity():
    """Doc-08 P13 limitation: monthly AGT averages do not cross oil parity.

    The committed gas_basis_by_iso_month.csv carries *monthly* Algonquin
    Citygate prices, which smooth over the daily cold-snap spot blowouts that
    actually drive the dual-fuel switch in real time. Across 2023-2025 every
    monthly AGT value stays below distillate parity (~$18/MMBtu), so the
    dual-fuel CT/ST switch is correctly wired (see
    :func:`test_neiso_hub_overlay_drives_dual_fuel_switch`) but rarely binds
    on monthly granularity — modeled winter oil comes predominantly from the
    oil-primary steam fleet (Canal/Wyman/New Haven/Montville/Newington, ~5 GW)
    dispatching at scarcity, not the CT switch. Daily AGT (a finer U4 upload)
    is what would make the CT switch bind. This guards the documented finding
    against a silent change to the basis CSV.
    """
    for year in (2023, 2024, 2025):
        config = ScenarioConfig(
            iso="NEISO",
            mode="backcast",
            weather_year=year,
            hours=_HOURS,
            gas_price_override=3.0,
            gas_hub_basis_overlay=True,
        )
        monthly = iso_hub_monthly_gas_prices(config, year)
        if monthly is None:
            import pytest

            pytest.skip("gas_basis_by_iso_month.csv has no NEISO rows")
        # Winter months blow out well above the shoulder, but the monthly
        # average never reaches distillate parity.
        assert np.nanmax(monthly) < OIL_PRICE_PER_MMBTU, (
            f"{year}: monthly AGT max {np.nanmax(monthly):.1f} unexpectedly "
            "crossed distillate parity — revisit the P13 monthly-granularity "
            "limitation note"
        )


def test_hub_basis_daily_is_mean_preserving_and_spikes(tmp_path, monkeypatch):
    """The daily overlay keeps the monthly mean but injects the real AGT spike.

    With ``gas_hub_basis_daily`` on, January's gas price is no longer the flat
    monthly hub ($3.1762 HH + $10 basis = $13.1762) but a daily series anchored to
    the real Algonquin Citygate daily spot prints (here synthetic: a cold-day
    print of $25 on day 15) interpolated on their calendar days. Its mean over the
    month still equals $13.1762 (so the annual gas burn is unchanged) while the
    cold day carrying the high AGT print is repriced well above it — the blowout a
    flat plateau can never produce. No demand/oil-tuned proxy is involved.
    """
    basis_csv = tmp_path / "basis.csv"
    basis_csv.write_text(
        "iso,year,month,hub,basis_usd_mmbtu,source\nNEISO,2024,1,AGT,10.0,test\n"
    )
    hours = 31 * 24  # January 2024 only
    # Flat monthly Henry Hub, no within-month HH shape (so the basis leg drives
    # the daily structure): day_hh == hh_m everywhere.
    monkeypatch.setattr(
        "market_sim.data.fuel._henry_hub_monthly", lambda path: {(2024, 1): 3.1762}
    )
    monkeypatch.setattr("market_sim.data.fuel._henry_hub_daily", lambda path: {})
    # Real AGT prints: mild shoulders with one cold-day spike on day 15 (>=2 prints
    # selects the real-AGT-print branch).
    monkeypatch.setattr(
        "market_sim.data.fuel._algonquin_daily",
        lambda path: {2024: {1: {5: 11.0, 15: 25.0, 25: 11.0}}},
    )
    fleet = _sample_fleet(hours=hours)
    config = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
        gas_hub_basis_overlay=True,
        gas_hub_basis_daily=True,
    )
    fuel_prices = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(fuel_prices, fleet, config, 2024, basis_path=basis_csv)

    gas_rows = np.isin(
        fleet.fuel_type_idx,
        (
            FUEL_TYPE_MAP["gas_cc"],
            FUEL_TYPE_MAP["gas_ct"],
        ),
    )
    gas_jan = fuel_prices[gas_rows]  # (n_gas, 744)
    # Mean over the month is exactly the flat monthly hub (mean-preserving).
    np.testing.assert_allclose(gas_jan.mean(axis=1), 3.1762 + 10.0, rtol=1e-6)
    # Daily resolution: the series is not flat, and the cold day (day 15, the high
    # AGT print) is repriced above the monthly mean.
    daily = gas_jan[0].reshape(31, 24).mean(axis=1)
    assert daily.std() > 0.5
    assert daily[14] == daily.max()
    assert daily[14] > 13.1762

    # No AGT prints and no Transco shape -> falls back to the flat monthly overlay.
    monkeypatch.setattr("market_sim.data.fuel._algonquin_daily", lambda path: {})
    monkeypatch.setattr("market_sim.data.fuel._transco_z6_daily", lambda path: {})
    flat = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(flat, fleet, config, 2024, basis_path=basis_csv)
    np.testing.assert_allclose(flat[gas_rows], 3.1762 + 10.0)


def test_hub_basis_daily_transco_fallback_caps_at_agt_ceiling(tmp_path, monkeypatch):
    """A sparse-print month borrows the Transco shape but caps at AGT's ceiling.

    When a covered month has <2 real AGT prints it borrows the measured Transco
    Z6 NY daily-basis within-month shape. On the most extreme days NY is more
    pipeline-constrained than Boston (Transco hit $97.9 in the Jan-2025 vortex
    while AGT spot never exceeds ~$30), so the borrowed basis is capped at AGT's
    own measured price ceiling — before the mean-preserving shift, so the monthly
    mean stays exact. Here the ceiling is $28 (a print in another month) and a
    synthetic $50 Transco spike must not propagate to a $50 AGT day.
    """
    basis_csv = tmp_path / "basis.csv"
    basis_csv.write_text(
        "iso,year,month,hub,basis_usd_mmbtu,source\nNEISO,2024,1,AGT,5.0,test\n"
    )
    hours = 31 * 24
    monkeypatch.setattr(
        "market_sim.data.fuel._henry_hub_monthly", lambda path: {(2024, 1): 3.0}
    )
    monkeypatch.setattr("market_sim.data.fuel._henry_hub_daily", lambda path: {})
    # One print this month (<2 -> Transco branch); a $28 print elsewhere sets the
    # dataset-wide AGT price ceiling.
    monkeypatch.setattr(
        "market_sim.data.fuel._algonquin_daily",
        lambda path: {2024: {1: {10: 8.0}}, 2023: {2: {2: 28.0}}},
    )
    spike = [2.0] * 31
    spike[14] = 50.0  # extreme Transco day, far above AGT's ceiling
    monkeypatch.setattr(
        "market_sim.data.fuel._transco_z6_daily", lambda path: {2024: {1: spike}}
    )
    fleet = _sample_fleet(hours=hours)
    config = ScenarioConfig(
        iso="NEISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
        gas_hub_basis_overlay=True,
        gas_hub_basis_daily=True,
    )
    fuel_prices = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(fuel_prices, fleet, config, 2024, basis_path=basis_csv)
    gas_rows = np.isin(
        fleet.fuel_type_idx, (FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"])
    )
    gas_jan = fuel_prices[gas_rows]
    # Mean-preserving even with the cap (cap applied before the shift).
    np.testing.assert_allclose(gas_jan.mean(axis=1), 3.0 + 5.0, rtol=1e-6)
    daily = gas_jan[0].reshape(31, 24).mean(axis=1)
    # The $50 Transco spike is capped near AGT's $28 ceiling (+ the mean shift),
    # nowhere near the uncapped ~$53 it would otherwise hit.
    assert daily[14] == daily.max()
    assert daily.max() < 35.0


def test_nyiso_hub_basis_daily_uses_real_transco_shape(tmp_path, monkeypatch):
    """NYISO's daily overlay takes its within-month shape from the measured
    Transco Z6 NY daily spot, mean-preserving on the monthly Iroquois hub.

    Unlike the NEISO leg (a demand-convexity proxy), the NYISO leg
    (``_nyiso_hub_daily_gas_prices``) is driven by the real daily series: the
    flat monthly hub (HH $3 + basis $10 = $13) is replaced by a daily series
    whose mean over the month is still exactly $13 (annual burn unchanged) while
    the cold day carrying the high Transco quote is repriced above it — the
    cold-snap spike a monthly mean smears flat (the Jan-2025 case in the doc).
    """
    basis_csv = tmp_path / "basis.csv"
    basis_csv.write_text(
        "iso,year,month,hub,basis_usd_mmbtu,source\nNYISO,2024,1,Transco,10.0,test\n"
    )
    hours = 31 * 24  # January 2024 only
    monkeypatch.setattr(
        "market_sim.data.fuel._henry_hub_monthly", lambda path: {(2024, 1): 3.0}
    )
    # Synthetic daily Transco: flat $2 with one cold-day spike to $8 on day 15
    # (true-date keyed: quotes carry their actual calendar day).
    daily_quotes = {d: 2.0 for d in range(1, 32)}
    daily_quotes[15] = 8.0
    monkeypatch.setattr(
        "market_sim.data.fuel._transco_z6_daily_dated",
        lambda path: {2024: {1: daily_quotes}},
    )
    fleet = _sample_fleet(hours=hours)
    config = ScenarioConfig(
        iso="NYISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
        gas_hub_basis_overlay=True,
        gas_hub_basis_daily=True,
    )
    fuel_prices = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(fuel_prices, fleet, config, 2024, basis_path=basis_csv)

    gas_rows = np.isin(
        fleet.fuel_type_idx,
        (FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]),
    )
    gas_jan = fuel_prices[gas_rows]
    # Mean over the month is exactly the flat monthly hub (mean-preserving).
    np.testing.assert_allclose(gas_jan.mean(axis=1), 3.0 + 10.0, rtol=1e-6)
    # Daily resolution: not flat, and the cold day (day 15, the Transco spike)
    # is the most expensive day, repriced above the $13 monthly mean.
    daily = gas_jan[0].reshape(31, 24).mean(axis=1)
    assert daily.std() > 0.5
    assert daily[14] == daily.max()
    assert daily[14] > 13.0

    # No daily Transco quotes -> the month keeps the flat monthly hub level.
    monkeypatch.setattr("market_sim.data.fuel._transco_z6_daily_dated", lambda path: {})
    flat = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(flat, fleet, config, 2024, basis_path=basis_csv)
    np.testing.assert_allclose(flat[gas_rows], 13.0)


def test_caiso_hub_basis_daily_uses_real_citygate_shape(tmp_path, monkeypatch):
    """CAISO's daily overlay takes its within-month shape from the measured
    California Composite Average citygate daily spot, mean-preserving on the
    monthly SoCal/PG&E citygate hub.

    Mirrors ``test_nyiso_hub_basis_daily_uses_real_transco_shape``: the flat
    monthly hub (HH $3 + basis $10 = $13, + the citygate transport adder) is
    replaced by a daily series whose mean over the month is still exactly $13
    (annual burn unchanged) while the cold day carrying the high citygate quote
    is repriced above it. Guards against the (would-be) NEISO-narrative AGT
    branch ever firing for CAISO — a real bug this daily leg replaces.
    """
    basis_csv = tmp_path / "basis.csv"
    basis_csv.write_text(
        "iso,year,month,hub,basis_usd_mmbtu,source\n"
        "CAISO,2024,1,SoCal/PG&E Citygate,10.0,test\n"
    )
    hours = 31 * 24  # January 2024 only
    monkeypatch.setattr(
        "market_sim.data.fuel._henry_hub_monthly", lambda path: {(2024, 1): 3.0}
    )
    # Synthetic daily CA Composite: flat $2 with one cold-day spike to $8 on day
    # 15 (true-date keyed: quotes carry their actual calendar day).
    daily_quotes = {d: 2.0 for d in range(1, 32)}
    daily_quotes[15] = 8.0
    monkeypatch.setattr(
        "market_sim.data.fuel._caiso_citygate_daily_dated",
        lambda path: {2024: {1: daily_quotes}},
    )
    fleet = _sample_fleet(hours=hours)
    config = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        weather_year=2024,
        gas_seasonality=False,
        hours=hours,
        gas_hub_basis_overlay=True,
        gas_hub_basis_daily=True,
    )
    fuel_prices = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(fuel_prices, fleet, config, 2024, basis_path=basis_csv)

    gas_rows = np.isin(
        fleet.fuel_type_idx,
        (FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]),
    )
    gas_jan = fuel_prices[gas_rows]
    adder = CAISO_CITYGATE_TRANSPORT_ADDER
    # Mean over the month is exactly the flat monthly hub + transport adder.
    np.testing.assert_allclose(gas_jan.mean(axis=1), 3.0 + 10.0 + adder, rtol=1e-6)
    # Daily resolution: not flat, and the cold day (day 15, the citygate spike)
    # is the most expensive day, repriced above the $13(+adder) monthly mean.
    daily = gas_jan[0].reshape(31, 24).mean(axis=1)
    assert daily.std() > 0.5
    assert daily[14] == daily.max()
    assert daily[14] > 13.0 + adder

    # No daily citygate quotes -> the month keeps the flat monthly hub level.
    monkeypatch.setattr(
        "market_sim.data.fuel._caiso_citygate_daily_dated", lambda path: {}
    )
    flat = np.full((fleet.n_gen, hours), 4.0)
    apply_hub_basis_overlay(flat, fleet, config, 2024, basis_path=basis_csv)
    np.testing.assert_allclose(flat[gas_rows], 13.0 + adder)


def test_hub_basis_overlay_off_by_default_for_other_isos():
    """The hub-basis overlay never touches a default ERCOT/PJM/CAISO run.

    The committed basis CSV now carries every ISO's measured EIA citygate basis
    (the NYISO/citygate rebuild backfilled all seven ISOs, not just NEISO), so
    the overlay is no longer NEISO-only. The keeper-safety invariant is that it
    stays *off by default*: a default resolve is byte-identical to one with the
    flag explicitly off, and only gas rows ever move when it is turned on. With
    the flag on, gas is repriced to that ISO's measured citygate (HH + basis),
    so it is no longer a no-op — that is the intended measured-data behaviour,
    not a leak from the NEISO leg.
    """
    fleet = _sample_fleet(hours=24)
    gas_rows = np.isin(
        fleet.fuel_type_idx,
        (FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]),
    )
    for iso in ("ERCOT", "PJM", "CAISO"):
        base = ScenarioConfig(
            iso=iso,
            mode="backcast",
            weather_year=2024,
            gas_seasonality=False,
            hours=24,
        )
        default = resolve_fuel_prices(base, fleet, 2024)
        explicit_off = resolve_fuel_prices(
            base.with_overrides(gas_hub_basis_overlay=False), fleet, 2024
        )
        # Off by default: the flag changes nothing for a keeper run.
        np.testing.assert_array_equal(default, explicit_off)

        forced = resolve_fuel_prices(
            base.with_overrides(gas_hub_basis_overlay=True), fleet, 2024
        )
        # Flag on reprices the gas units to the measured citygate (not a no-op)
        # but never touches non-gas rows.
        assert not np.array_equal(default[gas_rows], forced[gas_rows])
        np.testing.assert_array_equal(default[~gas_rows], forced[~gas_rows])


def test_caiso_gas_monthly_actuals_uses_measured_iso_month_series():
    """gas_monthly_actuals prices CAISO gas at the measured EIA-923 series.

    The measured ISO-month volume-weighted delivered cost replaces the
    Henry Hub + (+1.20 basis seed) x seasonality shape month by month. The
    2023 series must carry the Dec-22/Jan-23 western gas crisis (January
    delivered gas far above any shaped trajectory value).
    """
    measured = iso_monthly_gas_prices(
        ScenarioConfig(iso="CAISO", mode="backcast", weather_year=2023), 2023
    )
    if measured is None:
        import pytest

        pytest.skip("EIA-923 monthly fuel cost parquet not available")
    assert measured.shape == (12,)
    assert np.isfinite(measured).all()  # every month has gas receipts
    # Jan-2023: measured ~$38.7/MMBtu vs trajectory + basis ~ $4-5.
    assert measured[0] > 20.0

    hours = 8760
    fleet = _cc_fleet(hours=hours)
    base = ScenarioConfig(
        iso="CAISO",
        mode="backcast",
        weather_year=2023,
        gas_price_override=2.54,
        hours=hours,
    )
    shaped = resolve_fuel_prices(base, fleet, 2023)
    actuals = resolve_fuel_prices(
        base.with_overrides(gas_monthly_actuals=True), fleet, 2023
    )
    # January hours pay the measured price, not the shaped trajectory.
    np.testing.assert_allclose(actuals[0, :744], measured[0])
    assert actuals[0, 0] > shaped[0, 0]


_NYISO_ZONES = [
    "Upstate_West",
    "Capital_Hudson",
    "Lower_Hudson",
    "NYC",
    "Long_Island",
]


def _nyiso_gas_fleet(hours: int = 48):
    """Two identical gas CCs, one upstate (cheap hub) and one in the east."""
    generators = [
        Generator(
            unit_id="GAS_UP",
            name="Upstate CC",
            zone="Upstate_West",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_CAP",
            name="Capital CC",
            zone="Capital_Hudson",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _NYISO_ZONES, hours=hours)


def test_nyiso_zonal_gas_offsets_west_below_east():
    """Upstate and NYC carry a negative gas basis vs the east reference (0)."""
    off = nyiso_zonal_gas_offsets(2023)
    assert off is not None
    assert off["Capital_Hudson"] == 0.0  # reference zone anchors at zero
    assert off["Upstate_West"] < -1.0  # Tenn Z4 200L well below Iroquois Z2
    assert off["NYC"] < 0.0  # Transco Z6 NY below Iroquois Z2
    assert off["Long_Island"] == 0.0  # Iroquois Z2, same as the reference


def test_nyiso_zonal_gas_basis_shifts_only_when_enabled():
    """The overlay lowers upstate gas only for NYISO with the flag on."""
    hours = 48
    fleet = _nyiso_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 4.0)
    config = ScenarioConfig(iso="NYISO", hours=hours)

    off_prices = base.copy()
    apply_nyiso_zonal_gas_basis(off_prices, fleet, config, 2023)
    np.testing.assert_array_equal(off_prices, base)  # flag off -> no-op

    on_prices = base.copy()
    apply_nyiso_zonal_gas_basis(
        on_prices, fleet, config.with_overrides(nyiso_zonal_gas_basis=True), 2023
    )
    up = fleet.unit_ids.index("GAS_UP")
    cap = fleet.unit_ids.index("GAS_CAP")
    assert on_prices[up, 0] < base[up, 0]  # upstate cheaper
    assert on_prices[cap, 0] == base[cap, 0]  # east reference unchanged
    assert on_prices[up, 0] == 4.0 + nyiso_zonal_gas_offsets(2023)["Upstate_West"]


def test_nyiso_zonal_gas_basis_skips_other_isos():
    """A non-NYISO ISO is untouched even with the flag set."""
    hours = 48
    fleet = _nyiso_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 4.0)
    config = ScenarioConfig(iso="PJM", hours=hours, nyiso_zonal_gas_basis=True)
    prices = base.copy()
    apply_nyiso_zonal_gas_basis(prices, fleet, config, 2023)
    np.testing.assert_array_equal(prices, base)


def _nyiso_ct_fleet(hours: int = 8760):
    """Downstate + upstate CT_PEAKERs and a downstate CC, for the CT basis test."""
    generators = [
        Generator(
            unit_id="CT_NYC",
            name="NYC peaker",
            zone="NYC",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            plant_group="CT_PEAKER",
        ),
        Generator(
            unit_id="CT_LI",
            name="LI peaker",
            zone="Long_Island",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            plant_group="CT_PEAKER",
        ),
        Generator(
            unit_id="CT_UP",
            name="Upstate peaker",
            zone="Upstate_West",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            plant_group="CT_PEAKER",
        ),
        Generator(
            unit_id="CC_NYC",
            name="NYC combined cycle",
            zone="NYC",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            plant_group="CC_REGULAR",
        ),
    ]
    return generators_to_fleet_arrays(generators, _NYISO_ZONES, hours=hours)


def test_nyiso_downstate_ct_gas_premium_positive_year_round():
    """The measured premium is positive year-round and summer-peaked."""
    prem = nyiso_downstate_ct_gas_premium(2023)
    assert prem is not None
    assert prem.shape == (12,)
    assert (prem >= 0.0).all()  # floored at 0
    assert prem.min() > 0.5  # 2023: city-gate above the hub in every month
    assert prem[6] > 3.0  # July: downstate interruptible-gas scarcity peak
    assert prem[6] == prem.max()
    # 2024 Jan floors to 0 (the arctic pipeline-hub spike exceeds the city gate)
    prem24 = nyiso_downstate_ct_gas_premium(2024)
    assert prem24[0] == 0.0


def test_nyiso_downstate_ct_gas_basis_lifts_only_downstate_peakers():
    """Only NYISO downstate CT_PEAKERs are lifted, and only with the flag on."""
    hours = 8760
    fleet = _nyiso_ct_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="NYISO", hours=hours)

    off = base.copy()
    apply_nyiso_downstate_ct_gas_basis(off, fleet, config, 2024)
    np.testing.assert_array_equal(off, base)  # flag off -> no-op

    on = base.copy()
    apply_nyiso_downstate_ct_gas_basis(
        on, fleet, config.with_overrides(nyiso_downstate_ct_gas_basis=True), 2024
    )
    prem = nyiso_downstate_ct_gas_premium(2024)
    july = 24 * 181 + 5  # an hour inside July (month index 6)
    nyc = fleet.unit_ids.index("CT_NYC")
    li = fleet.unit_ids.index("CT_LI")
    up = fleet.unit_ids.index("CT_UP")
    cc = fleet.unit_ids.index("CC_NYC")
    # downstate CT peakers lifted by the July premium
    assert on[nyc, july] == 3.0 + prem[6]
    assert on[li, july] == 3.0 + prem[6]
    # upstate CT peaker and downstate CC untouched
    assert on[up, july] == 3.0
    assert on[cc, july] == 3.0
    # January premium is zero -> no lift even downstate
    assert on[nyc, 5] == 3.0


def test_nyiso_downstate_ct_gas_daily_per_zone():
    """The daily re-grounding sets each downstate CT peaker to its zone's index.

    NYC peakers take the KEDNY (SC-22) delivered index, Long Island peakers the
    KEDLI (SC-19) one — different per-zone levels — while upstate CT and the
    downstate CC are untouched. Uses the committed 2024 raw series via the
    reader's raw fallback.
    """
    from market_sim.data.fuel import (
        _downstate_delivered_gas_hourly_by_zone,
        apply_nyiso_downstate_ct_gas_daily,
    )

    hours = 8760
    fleet = _nyiso_ct_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="NYISO", hours=hours)

    off = base.copy()
    apply_nyiso_downstate_ct_gas_daily(off, fleet, config, 2024)
    np.testing.assert_array_equal(off, base)  # flag off -> no-op

    by_zone = _downstate_delivered_gas_hourly_by_zone("NYISO", 2024, hours)
    assert by_zone is not None and {"NYC", "Long_Island"} <= set(by_zone)

    on = base.copy()
    apply_nyiso_downstate_ct_gas_daily(
        on, fleet, config.with_overrides(nyiso_downstate_ct_gas_daily=True), 2024
    )
    nyc = fleet.unit_ids.index("CT_NYC")
    li = fleet.unit_ids.index("CT_LI")
    up = fleet.unit_ids.index("CT_UP")
    cc = fleet.unit_ids.index("CC_NYC")
    # Each downstate peaker is SET to its own zone's measured delivered index
    # (all >> the gas-price floor, so the floor is a no-op here).
    np.testing.assert_allclose(on[nyc], by_zone["NYC"])
    np.testing.assert_allclose(on[li], by_zone["Long_Island"])
    # Per-zone: NYC (KEDNY transport) is dearer than Long Island (KEDLI).
    assert on[nyc].mean() > on[li].mean()
    # Upstate CT peaker and downstate CC untouched.
    np.testing.assert_array_equal(on[up], base[up])
    np.testing.assert_array_equal(on[cc], base[cc])


def test_nyiso_downstate_ct_gas_basis_skips_other_isos():
    """A non-NYISO ISO is untouched even with the flag set."""
    hours = 8760
    fleet = _nyiso_ct_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="NEISO", hours=hours, nyiso_downstate_ct_gas_basis=True)
    prices = base.copy()
    apply_nyiso_downstate_ct_gas_basis(prices, fleet, config, 2024)
    np.testing.assert_array_equal(prices, base)


_PJM_ZONES = [
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
]


def _pjm_gas_fleet(hours: int = 48):
    """Three identical gas CCs: a western (cheap), a Dominion and an SWMAAC."""
    generators = [
        Generator(
            unit_id="GAS_WEST",
            name="West CC",
            zone="PJM_West_APS",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_DOM",
            name="Dominion CC",
            zone="PJM_Dominion",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_SWMAAC",
            name="SWMAAC CC",
            zone="PJM_SWMAAC",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _PJM_ZONES, hours=hours)


def test_pjm_zonal_gas_basis_west_below_east():
    """The western coal belt sits below the dear east (Dominion/SWMAAC)."""
    basis = pjm_zonal_gas_basis_by_zone(2024)
    assert basis is not None
    # Western Marcellus/Appalachian zones cheap; eastern pockets dear.
    assert basis["PJM_West_APS"] < basis["PJM_Dominion"]
    assert basis["PJM_Central_PA"] < basis["PJM_SWMAAC"]
    assert basis["PJM_SWMAAC"] > 0.0  # Transco Z6 premium


def test_pjm_zonal_gas_basis_mean_zero_preserves_level():
    """With the flag on the cap-weighted mean shift is zero (level preserved)."""
    hours = 48
    fleet = _pjm_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="PJM", hours=hours)

    off_prices = base.copy()
    apply_pjm_zonal_gas_basis(off_prices, fleet, config, 2024)
    np.testing.assert_array_equal(off_prices, base)  # flag off -> no-op

    on_prices = base.copy()
    apply_pjm_zonal_gas_basis(
        on_prices, fleet, config.with_overrides(pjm_zonal_gas_basis=True), 2024
    )
    west = fleet.unit_ids.index("GAS_WEST")
    dom = fleet.unit_ids.index("GAS_DOM")
    swmaac = fleet.unit_ids.index("GAS_SWMAAC")
    # West cheaper than Dominion and SWMAAC after the shift.
    assert on_prices[west, 0] < on_prices[dom, 0]
    assert on_prices[west, 0] < on_prices[swmaac, 0]
    # Equal pmax -> the (unweighted) mean of the three shifts equals the base,
    # i.e. the capacity-weighted-zero anchor preserves the aggregate level.
    np.testing.assert_allclose(
        np.mean([on_prices[west, 0], on_prices[dom, 0], on_prices[swmaac, 0]]),
        3.0,
        atol=1e-9,
    )


def test_pjm_zonal_gas_basis_skips_other_isos():
    """A non-PJM ISO is untouched even with the flag set."""
    hours = 48
    fleet = _pjm_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="MISO", hours=hours, pjm_zonal_gas_basis=True)
    prices = base.copy()
    apply_pjm_zonal_gas_basis(prices, fleet, config, 2024)
    np.testing.assert_array_equal(prices, base)


# Must mirror the real six-zone config order: _apply_meanzero_zonal_gas_basis
# maps zone basis through get_iso_config("MISO").zone_names positions.
_MISO_ZONES = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]


def _miso_gas_fleet(hours: int = 48):
    """Three identical gas CCs, one per hub region (West, Illinois, South)."""
    generators = [
        Generator(
            unit_id="GAS_WEST",
            name="West CC",
            zone="MISO-West",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_ILLINOIS",
            name="Illinois CC",
            zone="MISO-Illinois",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_SOUTH",
            name="South CC",
            zone="MISO-South",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _MISO_ZONES, hours=hours)


def test_miso_zonal_gas_basis_south_premium():
    """MISO-South (Gulf Coast) carries a premium over Illinois (Chicago) in 2024."""
    basis = miso_zonal_gas_basis_by_zone(2024)
    assert basis is not None
    assert set(basis) == {
        "MISO-West",
        "MISO-Plains",
        "MISO-Illinois",
        "MISO-Indiana",
        "MISO-East",
        "MISO-South",
    }
    assert basis["MISO-South"] > basis["MISO-Illinois"]


def test_miso_zonal_gas_basis_mean_zero_preserves_level():
    """With the flag on the cap-weighted mean shift is zero (level preserved)."""
    hours = 48
    fleet = _miso_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="MISO", hours=hours)

    off_prices = base.copy()
    apply_miso_zonal_gas_basis(off_prices, fleet, config, 2024)
    np.testing.assert_array_equal(off_prices, base)  # flag off -> no-op

    on_prices = base.copy()
    apply_miso_zonal_gas_basis(
        on_prices, fleet, config.with_overrides(miso_zonal_gas_basis=True), 2024
    )
    west = fleet.unit_ids.index("GAS_WEST")
    illinois = fleet.unit_ids.index("GAS_ILLINOIS")
    south = fleet.unit_ids.index("GAS_SOUTH")
    # South dearer than Illinois after the shift (Gulf Coast premium, 2024).
    assert on_prices[south, 0] > on_prices[illinois, 0]
    # Equal pmax -> the (unweighted) mean of the three shifts equals the base,
    # i.e. the capacity-weighted-zero anchor preserves the aggregate level.
    np.testing.assert_allclose(
        np.mean([on_prices[west, 0], on_prices[illinois, 0], on_prices[south, 0]]),
        3.0,
        atol=1e-9,
    )


def test_miso_zonal_gas_basis_skips_other_isos():
    """A non-MISO ISO is untouched even with the flag set."""
    hours = 48
    fleet = _miso_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="PJM", hours=hours, miso_zonal_gas_basis=True)
    prices = base.copy()
    apply_miso_zonal_gas_basis(prices, fleet, config, 2024)
    np.testing.assert_array_equal(prices, base)


# --- §3.7 national HH daily shape: true-date staircase (all-ISO fix) ---------


def _hh_dated(monkeypatch, jan: dict[int, float]):
    """Patch the dated HH loader with synthetic Jan-2024 quotes only."""
    monkeypatch.setattr(
        "market_sim.data.fuel._henry_hub_daily_dated",
        lambda path=None: {2024: {1: jan}},
    )


def test_gas_daily_shape_spike_lands_on_true_date(monkeypatch):
    """A convex single-day spike prices its own trade date, not an interp slot.

    Trivial case (rule: 1-gen/1-zone/24-h analogue): weekday quotes at $3 with a
    single $30 Friday print on Jan-12 bracketed by a weekend+holiday gap
    (no quotes Jan-13/14/15). The pre-fix even-spread ``np.interp`` relocated
    the spike off its date (Jan-12 -> ~Jan-13); the true-date staircase pins it
    to Jan-12.
    """
    jan = {d: 3.0 for d in (2, 3, 4, 5, 8, 9, 10, 11, 16, 17, 18, 19, 22, 23)}
    jan[12] = 30.0
    _hh_dated(monkeypatch, jan)
    hours = 31 * 24
    f = fuel.gas_daily_shape_factors(2024, hours)
    daily = f[::24]  # one factor per January day
    # The spike day itself carries the month's maximum factor...
    assert daily[11] == daily.max()
    # ...and the day BEFORE the spike is a plain $3 day (no backward leak —
    # the even-spread interp raised Jan-11 toward the spike).
    np.testing.assert_allclose(daily[10], daily[7], atol=1e-9)


def test_gas_daily_shape_holiday_gap_staircase(monkeypatch):
    """The Friday quote covers Sat/Sun/Mon-holiday flat — staircase, no interp.

    Non-trading days carry the LAST trade date's value: Jan-13/14/15 (weekend +
    MLK Monday, no quotes) must equal Jan-12's factor exactly, then Jan-16 steps
    down to its own quote. A linear interpolation across the gap would instead
    decay monotonically from $30 toward $3.
    """
    jan = {d: 3.0 for d in (2, 3, 4, 5, 8, 9, 10, 11, 16, 17, 18, 19, 22, 23)}
    jan[12] = 30.0
    _hh_dated(monkeypatch, jan)
    hours = 31 * 24
    daily = fuel.gas_daily_shape_factors(2024, hours)[::24]
    for d in (13, 14, 15):
        np.testing.assert_allclose(daily[d - 1], daily[11], atol=1e-9)
    # Jan-16 steps down to its own $3 quote (same factor as any plain $3 day).
    np.testing.assert_allclose(daily[15], daily[7], atol=1e-9)
    # Mean preservation holds exactly (by construction, not renormalization).
    np.testing.assert_allclose(daily.mean(), 1.0, atol=1e-9)


def test_gas_daily_shape_gapless_month_unchanged(monkeypatch):
    """A month quoted every calendar day reproduces quote/mean exactly.

    With no trading gaps the staircase is the quotes themselves, so the factors
    equal each day's quote over the month mean — identical to the pre-fix
    even-spread output for a gap-free month (the fix only moves months WITH
    gaps).
    """
    quotes = {d: 3.0 + 0.1 * d for d in range(1, 32)}
    _hh_dated(monkeypatch, quotes)
    hours = 31 * 24
    daily = fuel.gas_daily_shape_factors(2024, hours)[::24]
    vals = np.array([quotes[d] for d in range(1, 32)])
    np.testing.assert_allclose(daily, vals / vals.mean(), atol=1e-12)


def test_gas_daily_shape_months_without_quotes_are_ones(monkeypatch):
    """Months with no quotes stay all-ones (no shape), as before the fix."""
    _hh_dated(monkeypatch, {12: 30.0, 15: 3.0})  # January-only quotes
    f = fuel.gas_daily_shape_factors(2024, 8760)
    assert np.any(f[: 31 * 24] != 1.0)
    np.testing.assert_array_equal(f[31 * 24 :], np.ones(8760 - 31 * 24))


def test_gas_daily_shape_off_is_byte_inert(monkeypatch):
    """gas_daily_shape=False never touches the daily HH series (byte-inert).

    The fixed loader/staircase must be unreachable when the flag is off: with
    the dated loader booby-trapped, resolve_fuel_prices with
    ``gas_daily_shape=False`` still returns, byte-identical to a run with no
    daily data at all.
    """

    def _boom(path=None):
        raise AssertionError("gas_daily_shape=False must not read the daily HH series")

    fleet = _sample_fleet()
    config = _config(gas_seasonality=False)
    assert config.gas_daily_shape is False
    baseline = resolve_fuel_prices(config, fleet, year=2026)
    monkeypatch.setattr("market_sim.data.fuel._henry_hub_daily_dated", _boom)
    monkeypatch.setattr("market_sim.data.fuel._trade_date_staircase", _boom)
    off = resolve_fuel_prices(config, fleet, year=2026)
    np.testing.assert_array_equal(off, baseline)


# --- miso-72 winter fuel-security citygate daily overlay ---------------------

_MISO_WINTER_HOURS = 8760


def _miso_winter_base(fleet, level: float = 4.5):
    """Base gas price = flat level × national HH daily shape (what line 3564 sets)."""
    national = fuel.gas_daily_shape_factors(2024, _MISO_WINTER_HOURS)
    return np.full((fleet.n_gen, _MISO_WINTER_HOURS), level) * national[np.newaxis, :]


def _jan_hour(day: int) -> int:
    return (day - 1) * 24


def test_miso_chicago_daily_shape_is_mean_preserving():
    """The Chicago daily shape factors average to exactly 1.0 within each month."""
    chi = fuel.miso_chicago_daily_shape_factors(2024, _MISO_WINTER_HOURS)
    # January (the Heather month) mean is exactly 1.0 -> level unchanged.
    np.testing.assert_allclose(chi[:744].mean(), 1.0, atol=1e-9)
    # Every month averages ~1.0 (mean-preserving construction).
    hour = 0
    for n_days in fuel._DAYS_IN_MONTH:
        seg = chi[hour : hour + n_days * 24]
        np.testing.assert_allclose(seg.mean(), 1.0, atol=1e-9)
        hour += n_days * 24


def test_miso_chicago_daily_shape_flow_date_placement():
    """The Jan-12 Friday spike prices the weekend+MLK flow days Jan-13..16, not Jan-12."""
    chi = fuel.miso_chicago_daily_shape_factors(2024, _MISO_WINTER_HOURS)
    # Flow-date: gas bought Friday Jan-12 ($25.82) flows Jan-13/14/15/16 (MLK Mon
    # is a no-trade holiday; the record-peak Tuesday burns Friday's gas). Jan-12
    # itself carries the low Thursday-trade flow.
    for d in (13, 14, 15, 16):
        assert chi[_jan_hour(d)] > 3.0, f"Jan-{d} should carry the broadcast spike"
    assert chi[_jan_hour(12)] < 1.0, "Jan-12 (pre-storm) should be below average"
    assert chi[_jan_hour(17)] < 1.0, "Jan-17 (thaw) should be below average"


def test_miso_winter_citygate_daily_off_is_byte_identical():
    """Flag off -> exact no-op (off-state byte identity)."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = _miso_winter_base(fleet)
    prices = base.copy()
    config = ScenarioConfig(
        iso="MISO", mode="backcast", hours=_MISO_WINTER_HOURS, gas_daily_shape=True
    )
    apply_miso_winter_citygate_daily(prices, fleet, config, 2024)
    np.testing.assert_array_equal(prices, base)


def test_miso_winter_citygate_daily_lifts_coldsnap_mean_preserving():
    """Chicago-hub gas: cold-snap flow days lifted, monthly level unchanged."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = _miso_winter_base(fleet)
    on = base.copy()
    config = ScenarioConfig(
        iso="MISO",
        # Measured Chicago Citygate daily prints — a backcast-only overlay, so
        # the config must say so (FFR-1D rule-13 guard, audit FR-11).
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        gas_daily_shape=True,
        miso_winter_citygate_daily=True,
    )
    apply_miso_winter_citygate_daily(on, fleet, config, 2024)
    il = list(fleet.unit_ids).index("GAS_ILLINOIS")
    # The true tail days Jan-15/16 (record-peak Tuesday) are lifted well above
    # the flat level by the Chicago flow-date shape (the whole point of the
    # mechanism). Since the §3.7 fix the national HH shape also carries the
    # Jan-12 Friday print across the Jan-13-15 gap (trade-date staircase), so
    # Jan-15's base is no longer the mislocated ~0.9× trough: the Chicago
    # overlay still reprices it (4.67× vs the national 3.3×), and on Jan-16
    # (where the national shape steps down to its own Tuesday quote but the
    # Friday flow package still prices Chicago gas) the lift stays >3× base.
    for d in (15, 16):
        assert on[il, _jan_hour(d)] > base[il, _jan_hour(d)]
        assert on[il, _jan_hour(d)] > 15.0  # ~$21 gas -> prices the winter tail
    assert on[il, _jan_hour(16)] > 3.0 * base[il, _jan_hour(16)]
    # January monthly mean unchanged (mean-preserving: the level does not move).
    np.testing.assert_allclose(on[il, :744].mean(), base[il, :744].mean(), atol=1e-9)


def test_miso_winter_citygate_daily_supersedes_national_shape():
    """On a lifted cell the price is level×chicago, NOT level×national×chicago (rule 19)."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    level = 4.5
    base = _miso_winter_base(fleet, level=level)
    on = base.copy()
    config = ScenarioConfig(
        iso="MISO",
        # Measured Chicago Citygate daily prints — a backcast-only overlay, so
        # the config must say so (FFR-1D rule-13 guard, audit FR-11).
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        gas_daily_shape=True,
        miso_winter_citygate_daily=True,
    )
    apply_miso_winter_citygate_daily(on, fleet, config, 2024)
    il = list(fleet.unit_ids).index("GAS_ILLINOIS")
    chi = fuel.miso_chicago_daily_shape_factors(2024, _MISO_WINTER_HOURS)
    h = _jan_hour(16)
    np.testing.assert_allclose(on[il, h], level * chi[h], atol=1e-9)


def test_miso_winter_citygate_daily_zone_and_season_scoped():
    """Only Chicago-hub zones in winter months move; West/South and summer untouched."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = _miso_winter_base(fleet)
    on = base.copy()
    config = ScenarioConfig(
        iso="MISO",
        # Measured Chicago Citygate daily prints — a backcast-only overlay, so
        # the config must say so (FFR-1D rule-13 guard, audit FR-11).
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        gas_daily_shape=True,
        miso_winter_citygate_daily=True,
    )
    apply_miso_winter_citygate_daily(on, fleet, config, 2024)
    west = list(fleet.unit_ids).index("GAS_WEST")
    south = list(fleet.unit_ids).index("GAS_SOUTH")
    il = list(fleet.unit_ids).index("GAS_ILLINOIS")
    # West (MidCon) and South (Gulf) are not Chicago-hub -> untouched everywhere.
    np.testing.assert_array_equal(on[west], base[west])
    np.testing.assert_array_equal(on[south], base[south])
    # July (a non-winter month) is untouched even for the Chicago-hub Illinois unit.
    jul0 = sum(fuel._DAYS_IN_MONTH[:6]) * 24
    jul1 = sum(fuel._DAYS_IN_MONTH[:7]) * 24
    np.testing.assert_array_equal(on[il, jul0:jul1], base[il, jul0:jul1])


def test_miso_winter_citygate_daily_skips_other_isos():
    """A non-MISO ISO is untouched even with the flag set."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = _miso_winter_base(fleet)
    prices = base.copy()
    config = ScenarioConfig(
        iso="PJM",
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        gas_daily_shape=True,
        miso_winter_citygate_daily=True,
    )
    apply_miso_winter_citygate_daily(prices, fleet, config, 2024)
    np.testing.assert_array_equal(prices, base)


def test_miso_winter_citygate_daily_synthetic_coldsnap(monkeypatch):
    """Controlled synthetic cold snap: a single mid-Jan spike lifts its flow days only."""
    # One elevated Jan-15 print among mild days; mild elsewhere. Trade day 15 ->
    # flow day 16 (forward-filled). Everything else ~ $3.
    jan = {d: 3.0 for d in range(2, 28, 2)}
    jan[15] = 30.0
    monkeypatch.setattr(
        "market_sim.data.fuel._miso_citygate_daily_dated",
        lambda path=None: {2024: {1: jan}},
    )
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = np.full((fleet.n_gen, _MISO_WINTER_HOURS), 5.0)  # flat, gas_daily_shape off
    on = base.copy()
    config = ScenarioConfig(
        iso="MISO",
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        gas_daily_shape=False,
        miso_winter_citygate_daily=True,
    )
    apply_miso_winter_citygate_daily(on, fleet, config, 2024)
    il = list(fleet.unit_ids).index("GAS_ILLINOIS")
    # Flow day (Jan-16, trade+1 of the Jan-15 spike) is lifted above the $5 base.
    assert on[il, _jan_hour(16)] > 5.0
    # Mean-preserving: January average unchanged at the $5 flat level.
    np.testing.assert_allclose(on[il, :744].mean(), 5.0, atol=1e-9)


# Must mirror the real CAISO config zone order: _apply_meanzero_zonal_gas_basis
# maps zone basis through get_iso_config("CAISO").zone_names positions.
# SP15 split into LA_BASIN/SDGE/SP15_rest (2026-07-09); SP15_rest stands in as
# the southern (SoCal Citygate) zone for this two-zone fixture.
_CAISO_ZONES = ["NP15", "ZP26", "SP15_rest", "WECC_import"]


def _caiso_gas_fleet(hours: int = 48):
    """Two identical gas CCs: a northern (PG&E Citygate) and a southern (SoCal)."""
    generators = [
        Generator(
            unit_id="GAS_NORTH",
            name="North CC",
            zone="NP15",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
        Generator(
            unit_id="GAS_SOUTH",
            name="South CC",
            zone="SP15_rest",
            fuel_type="gas_cc",
            pmax_mw=400.0,
        ),
    ]
    return generators_to_fleet_arrays(generators, _CAISO_ZONES, hours=hours)


def test_caiso_zonal_gas_basis_measured_sign_by_year():
    """The measured PG&E-vs-SoCal spread flips sign across years (data, not knob)."""
    b24 = caiso_zonal_gas_basis_by_zone(2024)
    b23 = caiso_zonal_gas_basis_by_zone(2023)
    assert b24 is not None and b23 is not None
    assert set(b24) == {"NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"}
    # ZP26 shares the PG&E backbone with NP15.
    assert b24["NP15"] == b24["ZP26"]
    # 2024: PG&E premium (north-dear); 2023: SoCal premium (south-dear).
    assert b24["NP15"] > b24["SP15_rest"]
    assert b23["NP15"] < b23["SP15_rest"]


def test_caiso_zonal_gas_basis_mean_zero_preserves_level():
    """With the flag on the cap-weighted mean shift is zero (level preserved)."""
    hours = 48
    fleet = _caiso_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="CAISO", hours=hours)

    off_prices = base.copy()
    apply_caiso_zonal_gas_basis(off_prices, fleet, config, 2024)
    np.testing.assert_array_equal(off_prices, base)  # flag off -> no-op

    on_prices = base.copy()
    apply_caiso_zonal_gas_basis(
        on_prices, fleet, config.with_overrides(caiso_zonal_gas_basis=True), 2024
    )
    north = fleet.unit_ids.index("GAS_NORTH")
    south = fleet.unit_ids.index("GAS_SOUTH")
    # 2024: PG&E Citygate premium -> north dearer than south after the shift.
    assert on_prices[north, 0] > on_prices[south, 0]
    # Equal pmax -> the (unweighted) mean of the two shifts equals the base,
    # i.e. the capacity-weighted-zero anchor preserves the aggregate level.
    np.testing.assert_allclose(
        np.mean([on_prices[north, 0], on_prices[south, 0]]), 3.0, atol=1e-9
    )


def test_caiso_zonal_gas_basis_skips_other_isos():
    """A non-CAISO ISO is untouched even with the flag set."""
    hours = 48
    fleet = _caiso_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.0)
    config = ScenarioConfig(iso="PJM", hours=hours, caiso_zonal_gas_basis=True)
    prices = base.copy()
    apply_caiso_zonal_gas_basis(prices, fleet, config, 2024)
    np.testing.assert_array_equal(prices, base)


_ERCOT_ZONES = ["West", "Panhandle", "North", "Northeast", "Houston"]


def _ercot_gas_fleet(hours: int = 48):
    """Two identical gas CTs, one in the West (Waha) zone and one in North."""
    generators = [
        Generator(
            unit_id="GAS_WEST",
            name="Permian CT",
            zone="West",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=3494,  # Permian Basin (real EIA code, for per-plant haircut)
        ),
        Generator(
            unit_id="GAS_NORTH",
            name="DFW CT",
            zone="North",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=3456,
        ),
    ]
    return generators_to_fleet_arrays(generators, _ERCOT_ZONES, hours=hours)


def test_ercot_gas_delivered_floor_lifts_west_only():
    """The delivered floor truncates the deep-negative West Waha tail only.

    The raw West basis is a Waha *hub* basis (deeply negative); a power plant pays
    *delivered* gas, so its discount cannot exceed the cited measured Waha
    delivered basis. With the floor on, the West unit's delivered price rises (the
    -2.19 hub spread is truncated at -0.50) while the North unit — already above
    the floor — is byte-identical to the unfloored zonal result.
    """
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 2.19)  # ~2024 Henry Hub
    west = fleet.unit_ids.index("GAS_WEST")
    north = fleet.unit_ids.index("GAS_NORTH")

    cfg_on = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)
    unfloored = base.copy()
    apply_ercot_zonal_gas_basis(unfloored, fleet, cfg_on, 2024)

    floored = base.copy()
    apply_ercot_zonal_gas_basis(
        floored,
        fleet,
        cfg_on.with_overrides(ercot_gas_delivered_floor_basis=-0.50),
        2024,
    )

    # West delivered price is lifted by the floor; North is untouched.
    assert floored[west, 0] > unfloored[west, 0]
    np.testing.assert_allclose(floored[north, 0], unfloored[north, 0])
    # West is no longer near zero — it offers above a transport-grounded floor.
    assert floored[west, 0] > 1.0


def test_ercot_gas_delivered_floor_noop_without_zonal_gas():
    """The floor is inert unless the zonal-gas overlay itself is enabled."""
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 2.19)
    cfg = ScenarioConfig(
        iso="ERCOT", hours=hours, ercot_gas_delivered_floor_basis=-0.50
    )
    prices = base.copy()
    apply_ercot_zonal_gas_basis(prices, fleet, cfg, 2024)
    np.testing.assert_array_equal(prices, base)  # zonal-gas flag off -> no-op


def test_ercot_gas_spot_share_aggregates_to_zones(tmp_path):
    """Per-plant gas spot share rolls up MMBtu-weighted to model zones."""
    import pandas as pd

    from market_sim.data.fuel import ercot_gas_spot_share_by_zone

    top = tmp_path / "gas_takeorpay_ERCOT.csv"
    binp = tmp_path / "bins.csv"
    pd.DataFrame(
        {
            "plant_code": [3492, 3494, 55091],
            "spot_share": [0.8, 0.6, 0.3],
            "total_mmbtu": [100.0, 100.0, 200.0],
        }
    ).to_csv(top, index=False)
    pd.DataFrame(
        {"Plant_Code": [3492, 3494, 55091], "ERCOT_Zone": ["West", "West", "North"]}
    ).to_csv(binp, index=False)
    shares = ercot_gas_spot_share_by_zone(top, binp)
    assert shares == {"West": 0.7, "North": 0.3}  # MMBtu-weighted
    # Missing file -> None (caller falls back to the scalar floor, no haircut).
    assert ercot_gas_spot_share_by_zone(tmp_path / "absent.csv", binp) is None


def test_ercot_gas_spot_share_by_plant_keys_on_plant_code(tmp_path):
    """The per-plant loader returns each plant's own share, untouched by zone."""
    import pandas as pd

    from market_sim.data.fuel import ercot_gas_spot_share_by_plant

    top = tmp_path / "gas_takeorpay_ERCOT.csv"
    pd.DataFrame(
        {
            "plant_code": [3494, 58471],
            "spot_share": [1.0, 0.0],  # Permian Basin 100% spot; Ector 100% contract
            "total_mmbtu": [100.0, 100.0],
        }
    ).to_csv(top, index=False)
    assert ercot_gas_spot_share_by_plant(top) == {3494: 1.0, 58471: 0.0}
    assert ercot_gas_spot_share_by_plant(tmp_path / "absent.csv") is None


def test_ercot_gas_haircut_differentiates_same_zone_plants():
    """Two West units: a 100%-spot plant keeps the full Waha discount; a
    100%-contract plant in the same zone loses it. The zone average could not
    express this — it is exactly what per-plant buys us.
    """
    import market_sim.data.fuel as fuelmod
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fleet import (  # noqa: F401  (re-export guard)
        generators_to_fleet_arrays,
    )
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    gens = [
        Generator(
            unit_id="WEST_SPOT",
            name="Permian Basin",
            zone="West",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=3494,
        ),
        Generator(
            unit_id="WEST_CONTRACT",
            name="Ector County",
            zone="West",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=58471,
        ),
    ]
    fleet = generators_to_fleet_arrays(gens, _ERCOT_ZONES, hours=hours)
    base = np.full((fleet.n_gen, hours), 2.19)
    spot = fleet.unit_ids.index("WEST_SPOT")
    contract = fleet.unit_ids.index("WEST_CONTRACT")

    cfg = ScenarioConfig(
        iso="ERCOT",
        hours=hours,
        ercot_zonal_gas_basis=True,
        ercot_gas_contract_haircut=True,
    )
    orig = fuelmod.ercot_gas_spot_share_by_plant
    fuelmod.ercot_gas_spot_share_by_plant = lambda *a, **k: {3494: 1.0, 58471: 0.0}
    try:
        prices = base.copy()
        apply_ercot_zonal_gas_basis(prices, fleet, cfg, 2024)
    finally:
        fuelmod.ercot_gas_spot_share_by_plant = orig

    # The contracted unit (no Waha discount) is more expensive than the 100%-spot
    # unit (full discount), despite sharing the West zone.
    assert prices[contract, 0] > prices[spot, 0]


def test_ercot_gas_contract_haircut_shrinks_west_discount():
    """The measured per-PLANT spot-share haircut makes the West discount shallower.

    With the haircut on and a 50% spot share on the West plant, only half the Waha
    hub discount reaches the merit order, so the West delivered price sits above the
    unhaircut zonal price. The haircut keys on the unit's own EIA plant code, so we
    monkeypatch the per-plant loader to return that share for plant 3494.
    """
    import market_sim.data.fuel as fuelmod
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 2.19)
    west = fleet.unit_ids.index("GAS_WEST")

    cfg_on = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)
    unhaircut = base.copy()
    apply_ercot_zonal_gas_basis(unhaircut, fleet, cfg_on, 2024)

    orig = fuelmod.ercot_gas_spot_share_by_plant
    fuelmod.ercot_gas_spot_share_by_plant = lambda *a, **k: {3494: 0.5}
    try:
        haircut = base.copy()
        apply_ercot_zonal_gas_basis(
            haircut,
            fleet,
            cfg_on.with_overrides(ercot_gas_contract_haircut=True),
            2024,
        )
    finally:
        fuelmod.ercot_gas_spot_share_by_plant = orig

    # Halving the West plant's hub discount lifts its delivered gas above the raw
    # zonal price (less discount reaches the burner tip).
    assert haircut[west, 0] > unhaircut[west, 0]


def test_nyiso_monthly_ttc_expands_to_seasonal_envelope():
    """The Central-East TTC follows the measured monthly envelope per hour.

    Structure-first (claude.md rule #1): NYISO's day-ahead Central-East limit
    steps up when the AC Transmission upgrade energizes (Dec 2023) and derates
    each shoulder season; _apply_iso_monthly_ttc must expand the scalar TTC to a
    (hours, n_links) matrix whose Central-East column tracks
    NYISO_INTERFACE_TTC_BY_MONTH, leap-year safe.
    """
    from scripts.run_calibration import _apply_iso_monthly_ttc
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.constants import NYISO_INTERFACE_TTC_BY_MONTH

    cfg = get_iso_config("NYISO")
    ttc = np.array([link.ttc_mw for link in cfg.links], dtype=float)
    hours = 8760
    out = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2023, hours)

    assert out.ndim == 2 and out.shape == (hours, len(cfg.links))
    profile = NYISO_INTERFACE_TTC_BY_MONTH[2023][("Upstate_West", "Capital_Hudson")]
    ce = next(
        i
        for i, link in enumerate(cfg.links)
        if (link.from_zone, link.to_zone) == ("Upstate_West", "Capital_Hudson")
    )
    assert out[0, ce] == profile[0]  # Jan hour 0 -> Jan limit
    assert out[hours - 1, ce] == profile[11]  # Dec last hour -> Dec limit
    assert out[31 * 24, ce] == profile[1]  # first Feb hour -> Feb limit
    # The Dec post-upgrade limit is well above the shoulder-season floor.
    assert profile[11] > profile[3]


def test_nyiso_monthly_ttc_leap_year_hours():
    """2024 has 8784 hours; the month map must stay aligned through Feb 29."""
    from scripts.run_calibration import _apply_iso_monthly_ttc
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.constants import NYISO_INTERFACE_TTC_BY_MONTH

    cfg = get_iso_config("NYISO")
    ttc = np.array([link.ttc_mw for link in cfg.links], dtype=float)
    out = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2024, 8784)
    ce = next(
        i
        for i, link in enumerate(cfg.links)
        if (link.from_zone, link.to_zone) == ("Upstate_West", "Capital_Hudson")
    )
    profile = NYISO_INTERFACE_TTC_BY_MONTH[2024][("Upstate_West", "Capital_Hudson")]
    assert out.shape == (8784, len(cfg.links))
    assert out[8784 - 1, ce] == profile[11]  # last hour is still December


def test_monthly_ttc_noop_for_other_isos_and_untabulated_years():
    """No monthly table -> the scalar TTC array is returned unchanged (1-D)."""
    from scripts.run_calibration import _apply_iso_monthly_ttc
    from market_sim.config.iso_configs import get_iso_config

    cfg = get_iso_config("NYISO")
    ttc = np.array([link.ttc_mw for link in cfg.links], dtype=float)
    # Non-NYISO ISO.
    out_pjm = _apply_iso_monthly_ttc(ttc, cfg, "PJM", 2023, 8760)
    assert np.asarray(out_pjm).ndim == 1
    np.testing.assert_array_equal(out_pjm, ttc)
    # NYISO year BEYOND the table -> forward edge, still a silent no-op. There
    # the static value is the correct one (it is this series' own measured
    # post-upgrade annual mean; the forward level channel is the
    # transmission-expansion registry on top of it).
    out_fwd = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2099, 8760)
    assert np.asarray(out_fwd).ndim == 1
    np.testing.assert_array_equal(out_fwd, ttc)


def test_ttc_refuses_untabulated_historical_nyiso_year():
    """A NYISO year at/below the table's span with no entry RAISES (nyiso-134 D-2).

    The appliers used to no-op silently, which left the link on the STATIC
    post-upgrade 2,850 MW Central-East limit — transmission that did not exist
    before Dec-2023. 2022 solved that way would have run +56 % on the annual
    mean and 3.9x in Nov-2022, relieving exactly the upstate->downstate
    congestion that forms the downstate scarcity C3c measures.
    """
    import pytest

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.pipeline.ttc import apply_iso_monthly_ttc, apply_iso_year_ttc

    cfg = get_iso_config("NYISO")
    ttc = np.array([link.ttc_mw for link in cfg.links], dtype=float)
    for call in (
        lambda: apply_iso_year_ttc(cfg, "NYISO", 2016),
        lambda: apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2016, 8760),
    ):
        with pytest.raises(ValueError, match="no NYISO_INTERFACE_TTC"):
            call()
    # Non-NYISO is untouched by the guard (early return before it).
    caiso = get_iso_config("CAISO")
    assert apply_iso_year_ttc(caiso, "CAISO", 2016) is caiso


def test_west_oversupply_collapse_freq_counts_oversupply_hours():
    """Endogenous collapse freq = fraction of hours West VRE > local load + export."""
    # 10 hours; export limit 5 MW. Oversupply when vre > load + 5.
    vre = np.array([0, 10, 20, 4, 6, 16, 15, 30, 1, 11], dtype=float)
    load = np.array([10, 10, 10, 0, 0, 10, 10, 10, 5, 5], dtype=float)
    # headroom = load + 5 -> [15,15,15,5,5,15,15,15,10,10]
    # vre > headroom -> idx 2,4,5,7,9 True (strict >) = 5/10
    freq = ercot_west_oversupply_collapse_freq(vre, load, 5.0)
    assert freq == pytest.approx(0.5)


def test_west_oversupply_collapse_freq_rises_with_more_vre():
    """More West VRE -> more oversupply hours -> higher collapse frequency."""
    load = np.full(100, 50.0)
    base_vre = np.linspace(0.0, 100.0, 100)
    export = 10.0
    low = ercot_west_oversupply_collapse_freq(base_vre, load, export)
    high = ercot_west_oversupply_collapse_freq(base_vre * 1.5, load, export)
    assert high > low


def test_west_oversupply_collapse_freq_falls_with_more_export():
    """More takeaway (export TTC) -> fewer oversupply hours -> lower frequency."""
    load = np.full(100, 50.0)
    vre = np.linspace(0.0, 200.0, 100)
    tight = ercot_west_oversupply_collapse_freq(vre, load, 10.0)
    loose = ercot_west_oversupply_collapse_freq(vre, load, 80.0)
    assert loose < tight


def test_west_oversupply_collapse_freq_degenerate_returns_none():
    """Empty or mismatched-length series -> None (caller falls back)."""
    assert ercot_west_oversupply_collapse_freq(np.array([]), np.array([]), 5.0) is None
    assert (
        ercot_west_oversupply_collapse_freq(np.array([1.0, 2.0]), np.array([1.0]), 5.0)
        is None
    )


def test_west_netload_shape_uses_endogenous_freq_when_flag_on():
    """With the endogenous flag on, the split uses west_oversupply_freq, not measured.

    A 0.10 oversupply freq sends the lowest 10% of net-load hours to the deep
    collapse regime; the firm regime (one distinct price) is the rest. The 2024
    measured neg_day_freq is 0.42, so a 0.10 collapse fraction proves the
    endogenous value was used, not the measured one.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
    from market_sim.data.fuel import apply_ercot_west_netload_gas_shape

    cfg = get_iso_config("ERCOT")
    zone_names = cfg.zone_names
    west_idx = zone_names.index("West")
    hours = 100

    # One West gas unit. apply_ercot_west_netload_gas_shape only reads
    # fuel_type_idx and zone_idx, but FleetArrays requires the full field set.
    fa = FleetArrays(
        pmax=np.array([100.0]),
        pmin=np.array([0.0]),
        heat_rate=np.array([7.0]),
        vom=np.array([2.0]),
        emission_rate=np.array([0.05]),
        nox_rate=np.array([0.0]),
        so2_rate=np.array([0.0]),
        zone_idx=np.array([west_idx]),
        fuel_type_idx=np.array([FUEL_TYPE_MAP["gas_cc"]]),
        availability=np.ones((1, hours)),
        unit_ids=["W1"],
        efficiency_bin=np.array([0]),
        plant_code=np.array([0]),
    )

    config = ScenarioConfig(
        iso="ERCOT",
        ercot_zonal_gas_basis=True,
        ercot_west_netload_gas_shape=True,
        ercot_west_gas_endogenous_collapse=True,
    )

    fuel_prices = np.full((1, hours), 2.0)
    # Net-load: a clean ramp so quantiles are well-defined.
    net_load = np.linspace(1000.0, 5000.0, hours)

    apply_ercot_west_netload_gas_shape(
        fuel_prices,
        fa,
        config,
        2024,
        net_load,
        west_oversupply_freq=0.10,
    )
    # Net-load is a monotonic ramp, so the lowest 10% of hours (the collapse
    # regime) are the first 10 — all sharing the single deep price; the rest share
    # the single firm price. Count the collapse-priced hours; it must match the
    # endogenous 0.10, not the measured 0.42.
    row = fuel_prices[0]
    deep = row[0]  # lowest net-load hour -> deep collapse price
    firm = row[-1]  # highest net-load hour -> firm price
    assert not np.isclose(deep, firm)  # two distinct regimes
    collapse_frac = float(np.isclose(row, deep).mean())
    assert collapse_frac == pytest.approx(0.10, abs=0.02)


class TestGasHhMonthlyShape:
    """Measured HH monthly gas shape (gas_hh_monthly_shape, level-preserving)."""

    def _cfg(self, on: bool):
        from types import SimpleNamespace

        return SimpleNamespace(gas_hh_monthly_shape=on)

    def test_off_is_generic(self):
        import numpy as np

        from market_sim.data.fuel import _seasonal_factors, gas_seasonal_shape

        np.testing.assert_array_equal(
            gas_seasonal_shape(self._cfg(False), 2024, 8760),
            _seasonal_factors(8760),
        )

    def test_measured_year_level_preserved(self):

        from market_sim.data.fuel import gas_seasonal_shape

        f = gas_seasonal_shape(self._cfg(True), 2024, 8760)
        assert abs(float(f.mean()) - 1.0) < 1e-9  # hour-weighted mean exactly 1
        # Feb-2024 (post-Heather collapse) must sit well below the generic 1.10
        feb = f[31 * 24 + 12]
        assert feb < 0.9

    def test_forward_year_falls_back(self):
        import numpy as np

        from market_sim.data.fuel import _seasonal_factors, gas_seasonal_shape

        np.testing.assert_array_equal(
            gas_seasonal_shape(self._cfg(True), 2035, 8760),
            _seasonal_factors(8760),
        )


class TestOilDailyParity:
    """``dual_fuel_oil_daily_parity`` — the daily-resolution oil-parity cap.

    The measured EIA-923 Petroleum receipt is MONTHLY, so the dual-fuel cap is
    a flat plateau across the month, while the gas side of the same ``min()``
    is already daily. These cover the granularity fix: the shape is exactly
    mean-preserving per month (the delivered level stays the receipt), the
    flag is byte-identical when off, and an absent series degrades to no-shape
    rather than erroring.
    """

    @staticmethod
    def _cfg(daily: bool):
        from market_sim.config.scenarios import ScenarioConfig

        return ScenarioConfig(
            iso="NYISO",
            mode="backcast",
            hours=8760,
            dual_fuel_switching=True,
            dual_fuel_oil_daily_parity=daily,
        )

    def test_factors_mean_exactly_one_per_month(self):
        from market_sim.data.fuel import oil_daily_shape_factors
        from market_sim.data.fuel._shared import _month_index

        month = _month_index(8760)
        for year in (2023, 2024, 2025):
            factors = oil_daily_shape_factors(year, 8760)
            for m in range(12):
                assert abs(float(factors[month == m].mean()) - 1.0) < 1e-12, (year, m)

    def test_default_off_is_byte_identical(self):
        import numpy as np

        from market_sim.data.fuel import dual_fuel_oil_price_series

        for year in (2023, 2024, 2025):
            np.testing.assert_array_equal(
                dual_fuel_oil_price_series(self._cfg(False), year),
                dual_fuel_oil_price_series(self._cfg(False), year),
            )
        # And the flag is what makes the two differ at all.
        assert not np.array_equal(
            dual_fuel_oil_price_series(self._cfg(False), 2025),
            dual_fuel_oil_price_series(self._cfg(True), 2025),
        )

    def test_monthly_delivered_level_is_preserved(self):
        """Only the within-month profile moves; every month's mean is fixed."""
        import numpy as np

        from market_sim.data.fuel import dual_fuel_oil_price_series
        from market_sim.data.fuel._shared import _month_index

        month = _month_index(8760)
        for year in (2023, 2024, 2025):
            flat = dual_fuel_oil_price_series(self._cfg(False), year)
            daily = dual_fuel_oil_price_series(self._cfg(True), year)
            for m in range(12):
                np.testing.assert_allclose(
                    daily[month == m].mean(), flat[month == m].mean(), rtol=1e-12
                )
            # The point of the fix: a real intra-month spread now exists.
            assert daily.std() > flat.std()

    def test_absent_series_resolves_to_no_shape(self, tmp_path):
        import numpy as np

        from market_sim.data.fuel import oil_daily_shape_factors

        np.testing.assert_array_equal(
            oil_daily_shape_factors(2025, 8760, path=tmp_path / "missing.csv"),
            np.ones(8760),
        )

    def test_cold_snap_lifts_the_cap_above_the_month(self):
        """Jan-2025's polar-vortex days must price above the monthly plateau."""
        from market_sim.data.fuel import dual_fuel_oil_price_series

        flat = dual_fuel_oil_price_series(self._cfg(False), 2025)
        daily = dual_fuel_oil_price_series(self._cfg(True), 2025)
        # 2025-01-17 (the Transco Z6 NY $97.9/MMBtu gas day) — hour 0 of day 17
        # on the model's non-leap clock.
        h = (17 - 1) * 24
        assert daily[h] > flat[h]
        # ... and a mild early-January day must price below it (mean-preserving
        # means the lift is paid for, not added).
        assert daily[(6 - 1) * 24] < flat[(6 - 1) * 24]


# ---------------------------------------------------------------------------
# miso-224: gas at marginal commodity (measured daily hub spot per zone)
# ---------------------------------------------------------------------------


def test_miso_gas_marginal_commodity_off_is_byte_identical():
    """Flag off -> exact no-op and ``None`` (off-state byte identity)."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = _miso_winter_base(fleet)
    prices = base.copy()
    config = ScenarioConfig(iso="MISO", mode="backcast", hours=_MISO_WINTER_HOURS)
    assert fuel.apply_miso_gas_marginal_commodity(prices, fleet, config, 2024) is None
    np.testing.assert_array_equal(prices, base)


def test_miso_gas_marginal_commodity_prices_each_zone_at_its_hub():
    """Chicago-hub and MidCon zones take the Chicago daily; South takes Henry Hub."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    prices = _miso_winter_base(fleet)
    config = ScenarioConfig(
        iso="MISO",
        mode="backcast",  # measured daily hub prints: a backcast-only overlay
        hours=_MISO_WINTER_HOURS,
        miso_gas_marginal_commodity_pricing=True,
    )
    written = fuel.apply_miso_gas_marginal_commodity(prices, fleet, config, 2024)
    assert written is not None and written.all()
    chi = np.repeat(
        fuel._flow_date_staircase(fuel._miso_citygate_daily_dated(None)[2024], 2024), 24
    )
    hh = np.repeat(
        fuel._trade_date_staircase(fuel._henry_hub_daily_dated(None)[2024], 2024), 24
    )
    il = list(fleet.unit_ids).index("GAS_ILLINOIS")
    west = list(fleet.unit_ids).index("GAS_WEST")
    south = list(fleet.unit_ids).index("GAS_SOUTH")
    np.testing.assert_allclose(prices[il], np.maximum(chi, fuel._GAS_PRICE_FLOOR))
    np.testing.assert_allclose(prices[west], np.maximum(chi, fuel._GAS_PRICE_FLOOR))
    np.testing.assert_allclose(prices[south], np.maximum(hh, fuel._GAS_PRICE_FLOOR))
    # The level moved to the hub: Feb-2024 Chicago averaged ~$1.56 vs the $4.5 base.
    feb = slice(31 * 24, 59 * 24)
    assert prices[il, feb].mean() < 2.0
    # Idempotent.
    again = prices.copy()
    fuel.apply_miso_gas_marginal_commodity(again, fleet, config, 2024)
    np.testing.assert_array_equal(again, prices)


def test_miso_gas_marginal_commodity_is_miso_scoped():
    """Arming on another ISO is a hard error, never a silent no-op (rule 25)."""
    fleet = _miso_gas_fleet(48)
    prices = np.full((fleet.n_gen, 48), 3.0)
    config = ScenarioConfig(
        iso="PJM", mode="backcast", hours=48, miso_gas_marginal_commodity_pricing=True
    )
    with pytest.raises(ValueError, match="MISO-scoped"):
        fuel.apply_miso_gas_marginal_commodity(prices, fleet, config, 2024)


# ---------------------------------------------------------------------------
# miso-225: the owner-ruled form — marginal commodity PLUS variable transport
# ---------------------------------------------------------------------------


def test_miso_gas_variable_transport_off_is_byte_identical():
    """Transport off -> the arm is exactly the miso-224 bare-hub form."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    bare = _miso_winter_base(fleet)
    config = ScenarioConfig(
        iso="MISO",
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        miso_gas_marginal_commodity_pricing=True,
    )
    fuel.apply_miso_gas_marginal_commodity(bare, fleet, config, 2024)
    again = _miso_winter_base(fleet)
    fuel.apply_miso_gas_marginal_commodity(
        again, fleet, config.with_overrides(miso_gas_variable_transport=False), 2024
    )
    np.testing.assert_array_equal(again, bare)


def test_miso_gas_variable_transport_requires_the_hub_repricing():
    """Rule 19: a transport adder on top of the AVERAGE print double-counts.

    Enforced AT THE POINT OF USE, which is the layer that actually fails closed:
    the applier runs on every backcast path, so an armed-alone transport flag can
    never reach a price. A ``__post_init__`` check was tried and REMOVED (miso-225
    Addendum A) — a config is assembled by long chains of ``with_overrides`` in
    which a pair is legitimately split, so validating there rejected a correct run
    after its LP had already finished.
    """
    fleet = _miso_gas_fleet(48)
    prices = np.full((fleet.n_gen, 48), 3.0)
    config = ScenarioConfig(
        iso="MISO", mode="backcast", hours=48, miso_gas_variable_transport=True
    )
    with pytest.raises(
        ValueError, match="requires miso_gas_marginal_commodity_pricing"
    ):
        fuel.apply_miso_gas_marginal_commodity(prices, fleet, config, 2024)


def test_miso_gas_variable_transport_lifts_every_row_above_the_bare_hub():
    """Armed, each gas row sits at its hub PLUS its own measured, non-zero adder."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    config = ScenarioConfig(
        iso="MISO",
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        miso_gas_marginal_commodity_pricing=True,
    )
    bare = _miso_winter_base(fleet)
    fuel.apply_miso_gas_marginal_commodity(bare, fleet, config, 2024)
    with_transport = _miso_winter_base(fleet)
    written = fuel.apply_miso_gas_marginal_commodity(
        with_transport,
        fleet,
        config.with_overrides(miso_gas_variable_transport=True),
        2024,
    )
    assert written is not None and written.all()
    # The fixture's units carry no plant_code, so every row resolves down the
    # declared ladder to its zone|group (or group) rung -- which is the point of
    # the ladder: 30 % of MISO gas nameplate has no EIA-923 receipt at all.
    delta = with_transport - bare
    # A constant-in-time adder per row (the transport is a $/MMBtu level, the
    # hub carries all the shape).
    for row in range(fleet.n_gen):
        assert np.ptp(delta[row]) == pytest.approx(0.0, abs=1e-9)
    assert np.abs(delta).max() > 0.0


def test_miso_gas_variable_transport_table_is_measured_and_nonempty():
    """The frozen derive's table exists, and its own-plant rung dominates it."""
    from market_sim.data.fuel.basis import miso as fuel_basis_miso

    by_plant, _by_zone_group, by_group, miso_wide = (
        fuel_basis_miso._load_miso_gas_variable_transport()
    )
    assert len(by_plant) > 50, "the derived per-plant transport table is missing"
    assert by_group, "the declared class fallback rung is missing"
    assert miso_wide != 0.0
    # Measured, not chosen: the table carries both signs (MidCon plants priced
    # off the Chicago proxy really do buy under the index) and is never clipped.
    values = list(by_plant.values())
    assert min(values) < 0.0 < max(values)


# ---------------------------------------------------------------------------
# miso-276: WINTER daily DELIVERED gas (owner ruling D1, "Chicago proxy")
# ---------------------------------------------------------------------------


def _miso_winter_delivered_config(**kw):
    return ScenarioConfig(
        iso="MISO",
        mode="backcast",
        hours=_MISO_WINTER_HOURS,
        miso_winter_gas_daily_delivered=True,
        **kw,
    )


def test_miso_winter_gas_daily_delivered_off_is_byte_identical():
    """Off -> returns None and touches no price."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    prices = _miso_winter_base(fleet)
    base = prices.copy()
    config = ScenarioConfig(iso="MISO", mode="backcast", hours=_MISO_WINTER_HOURS)
    assert fuel.apply_miso_winter_gas_daily_delivered(prices, fleet, config, 2024) is None
    np.testing.assert_array_equal(prices, base)


def test_miso_winter_gas_daily_delivered_writes_winter_only_at_hub_plus_transport():
    """Dec/Jan/Feb cells equal hub + the row's transport; every other cell untouched."""
    fleet = _miso_gas_fleet(_MISO_WINTER_HOURS)
    base = _miso_winter_base(fleet)
    prices = base.copy()
    written = fuel.apply_miso_winter_gas_daily_delivered(
        prices, fleet, _miso_winter_delivered_config(), 2024
    )
    month0 = fuel._month_index(_MISO_WINTER_HOURS)
    winter = np.isin(month0, [11, 0, 1])
    assert written is not None
    assert written[:, winter].all() and not written[:, ~winter].any()
    np.testing.assert_array_equal(prices[:, ~winter], base[:, ~winter])
    # Winter cells are exactly the marginal-commodity-plus-transport form.
    ref = _miso_winter_base(fleet)
    fuel.apply_miso_gas_marginal_commodity(
        ref,
        fleet,
        ScenarioConfig(
            iso="MISO",
            mode="backcast",
            hours=_MISO_WINTER_HOURS,
            miso_gas_marginal_commodity_pricing=True,
            miso_gas_variable_transport=True,
        ),
        2024,
    )
    np.testing.assert_allclose(prices[:, winter], ref[:, winter])
    again = prices.copy()
    fuel.apply_miso_winter_gas_daily_delivered(
        again, fleet, _miso_winter_delivered_config(), 2024
    )
    np.testing.assert_array_equal(again, prices)


def test_miso_winter_gas_daily_delivered_refuses_the_all_month_form():
    """Rule 19: stacking on the all-month marginal repricing is a hard error."""
    fleet = _miso_gas_fleet(48)
    prices = np.full((fleet.n_gen, 48), 3.0)
    config = ScenarioConfig(
        iso="MISO",
        mode="backcast",
        hours=48,
        miso_winter_gas_daily_delivered=True,
        miso_gas_marginal_commodity_pricing=True,
    )
    with pytest.raises(ValueError, match="mutually exclusive"):
        fuel.apply_miso_winter_gas_daily_delivered(prices, fleet, config, 2024)


def test_miso_winter_gas_daily_delivered_is_miso_scoped():
    """Arming on another ISO is a hard error (rule 25)."""
    fleet = _miso_gas_fleet(48)
    prices = np.full((fleet.n_gen, 48), 3.0)
    config = ScenarioConfig(
        iso="PJM", mode="backcast", hours=48, miso_winter_gas_daily_delivered=True
    )
    with pytest.raises(ValueError, match="MISO-scoped"):
        fuel.apply_miso_winter_gas_daily_delivered(prices, fleet, config, 2024)


# ---------------------------------------------------------------------------
# ercot-254: MONTHLY resolution of the ERCOT delivered-gas LEVEL anchor
# ---------------------------------------------------------------------------


def test_ercot_ep_gas_basis_monthly_mean_equals_the_annual_form():
    """The repair relocates a measured level; it never re-levels the year.

    ``mean(EP[m] - HH[m]) == mean(EP) - mean(HH)`` because the mean is linear,
    so the monthly basis carries exactly the annual form's value and the whole
    change is a within-year redistribution back to the months the series was
    measured in. Checked on every year the committed series covers, so a future
    intake that broke the identity would fail here.
    """
    from market_sim.data.fuel import (
        ercot_electric_power_gas_basis,
        ercot_electric_power_gas_basis_monthly,
    )

    checked = 0
    for year in range(2019, 2026):
        monthly = ercot_electric_power_gas_basis_monthly(year)
        if monthly is None:
            continue
        assert monthly.shape == (12,)
        annual = ercot_electric_power_gas_basis(year)
        assert annual is not None
        np.testing.assert_allclose(float(monthly.mean()), annual, atol=1e-12)
        checked += 1
    assert checked >= 5


def test_ercot_ep_gas_basis_monthly_is_none_for_a_forward_year():
    """A year with no measured rows returns None under BOTH forms.

    That is what keeps every forecast solve byte-identical: the caller degrades
    to the same mean-zero spread it always did.
    """
    from market_sim.data.fuel import (
        ercot_electric_power_gas_basis,
        ercot_electric_power_gas_basis_monthly,
    )

    assert ercot_electric_power_gas_basis(2035) is None
    assert ercot_electric_power_gas_basis_monthly(2035) is None


def test_ercot_ep_gas_basis_monthly_gate_is_byte_identical_when_off():
    """Default-off is byte-identical to the pre-repair annual branch."""
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 8760
    fleet = _ercot_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)
    assert cfg.ercot_ep_gas_basis_monthly is False

    annual = base.copy()
    apply_ercot_zonal_gas_basis(annual, fleet, cfg, 2021)
    explicit_off = base.copy()
    apply_ercot_zonal_gas_basis(
        explicit_off, fleet, cfg.with_overrides(ercot_ep_gas_basis_monthly=False), 2021
    )
    np.testing.assert_array_equal(annual, explicit_off)


def test_ercot_ep_gas_basis_monthly_moves_uri_cost_back_into_february():
    """The 2021 defect and its repair, on the applier itself.

    The annual form smears February 2021's $61.88/Mcf print over all 8,760
    hours: every ordinary hour is lifted and February is left too cheap. The
    monthly form puts that cost back in February. Both must hold at once, and
    the hour-weighted annual mean must barely move (only month lengths separate
    the two, since the month-mean identity is exact).
    """
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 8760
    fleet = _ercot_gas_fleet(hours)
    north = fleet.unit_ids.index("GAS_NORTH")
    base = np.full((fleet.n_gen, hours), 3.72)  # 2021 Henry Hub
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)

    annual = base.copy()
    apply_ercot_zonal_gas_basis(annual, fleet, cfg, 2021)
    monthly = base.copy()
    apply_ercot_zonal_gas_basis(
        monthly, fleet, cfg.with_overrides(ercot_ep_gas_basis_monthly=True), 2021
    )

    feb = slice(31 * 24, (31 + 28) * 24)
    july = slice(
        (31 + 28 + 31 + 30 + 31 + 30) * 24, (31 + 28 + 31 + 30 + 31 + 30 + 31) * 24
    )

    # February: the measured Uri cost lands where it was measured.
    assert monthly[north, feb].mean() > annual[north, feb].mean() + 40.0
    # An ordinary month: the smeared lift is removed.
    assert monthly[north, july].mean() < annual[north, july].mean() - 4.0
    # The annual level barely moves — this is a redistribution, not a re-level.
    # The residual is pure month-length weighting: the month-mean identity is
    # exact (see the identity test above), but February carries 28/365 of the
    # hours rather than 1/12, so down-weighting a +54.88 $/MMBtu February lowers
    # the HOUR-weighted 2021 level by 0.350 $/MMBtu. That is the entire level
    # effect of the repair in the worst year in the record.
    assert abs(monthly[north].mean() - annual[north].mean()) < 0.40


def test_ercot_ep_gas_basis_monthly_is_near_inert_in_the_training_window():
    """In 2023-2025 the same repair is a sub-$0.3/MMBtu redistribution.

    The defect is a property of 2021's extreme within-year distribution, not of
    the construction firing hard everywhere: the training years' monthly prints
    are tame, so the repair moves each hour by well under a dollar and moves the
    annual level essentially not at all.
    """
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 8760
    fleet = _ercot_gas_fleet(hours)
    north = fleet.unit_ids.index("GAS_NORTH")
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)

    for year, hub in ((2023, 2.54), (2024, 2.19), (2025, 3.52)):
        base = np.full((fleet.n_gen, hours), hub)
        annual = base.copy()
        apply_ercot_zonal_gas_basis(annual, fleet, cfg, year)
        monthly = base.copy()
        apply_ercot_zonal_gas_basis(
            monthly, fleet, cfg.with_overrides(ercot_ep_gas_basis_monthly=True), year
        )
        delta = np.abs(monthly[north] - annual[north])
        assert delta.max() < 1.5, f"{year}: max hourly move {delta.max()}"
        assert delta.mean() < 0.30, f"{year}: mean hourly move {delta.mean()}"
        assert abs(monthly[north].mean() - annual[north].mean()) < 0.05


def test_ercot_ep_gas_basis_monthly_leaves_other_isos_alone():
    """Rule 25 [R-ISO-SCOPE]: the gate cannot reach a non-ERCOT solve."""
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_gas_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(
        iso="PJM",
        hours=hours,
        ercot_zonal_gas_basis=True,
        ercot_ep_gas_basis_monthly=True,
    )
    out = base.copy()
    apply_ercot_zonal_gas_basis(out, fleet, cfg, 2021)
    np.testing.assert_array_equal(out, base)


# ---------------------------------------------------------------------------
# ercot-255: EP REFERENCE for the F923-sourced rows of the ERCOT zonal SPREAD
# ---------------------------------------------------------------------------


def _ercot_mixed_provenance_fleet(hours: int = 24):
    """One 400 MW gas CT in each of three zones spanning both provenance groups.

    ``North`` and ``South_Central`` carry EIA-923 Schedule-5 measured rows;
    ``Houston`` carries the cited hub-vs-hub convention. West is deliberately
    excluded so the applier's own seam is measured without
    ``apply_ercot_west_netload_gas_shape`` in the way.
    """
    generators = [
        Generator(
            unit_id="GAS_NORTH",
            name="DFW CT",
            zone="North",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=3456,
        ),
        Generator(
            unit_id="GAS_SC",
            name="South TX CT",
            zone="South_Central",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=3548,
        ),
        Generator(
            unit_id="GAS_HOUSTON",
            name="HSC CT",
            zone="Houston",
            fuel_type="gas_ct",
            pmax_mw=400.0,
            plant_code=3469,
        ),
    ]
    # The applier indexes its per-zone basis vector by ``get_iso_config("ERCOT")
    # .zone_names``, so the fleet's zone order must be the ISO's own, in full.
    from market_sim.config.iso_configs import get_iso_config

    return generators_to_fleet_arrays(
        generators, list(get_iso_config("ERCOT").zone_names), hours=hours
    )


def test_ercot_zonal_basis_source_group_reads_the_tables_own_provenance():
    """The F923/convention partition comes from the data, not a zone list.

    North / Northeast / South_Central / South are EIA-923 Schedule-5 measured
    delivered prices; Houston is a cited hub-vs-hub constant and West/Panhandle
    a Waha hub basis. Checked on every year the committed table covers, so a
    re-derivation that changed a zone's provenance would re-classify it here.
    """
    from market_sim.data.fuel import ercot_zonal_gas_basis_source_group

    checked = 0
    for year in range(2019, 2026):
        groups = ercot_zonal_gas_basis_source_group(year)
        if groups is None:
            continue
        for zone in ("North", "South_Central", "South"):
            assert groups[zone] == "f923", (year, zone)
        if "Northeast" in groups:
            assert groups["Northeast"] == "f923", year
        assert groups["Houston"] == "convention", year
        for zone in ("West", "Panhandle"):
            if zone in groups:
                assert groups[zone] == "convention", (year, zone)
        checked += 1
    assert checked >= 5


def test_ercot_zonal_basis_source_group_is_none_for_a_forward_year():
    """No rows -> None, so the caller keeps the unreferenced construction."""
    from market_sim.data.fuel import ercot_zonal_gas_basis_source_group

    assert ercot_zonal_gas_basis_source_group(2035) is None


def test_ercot_zonal_spread_ep_referenced_gate_is_byte_identical_when_off():
    """Default-off is byte-identical to the pre-repair branch."""
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_mixed_provenance_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)
    assert cfg.ercot_zonal_spread_ep_referenced is False

    default = base.copy()
    apply_ercot_zonal_gas_basis(default, fleet, cfg, 2021)
    explicit_off = base.copy()
    apply_ercot_zonal_gas_basis(
        explicit_off,
        fleet,
        cfg.with_overrides(ercot_zonal_spread_ep_referenced=False),
        2021,
    )
    np.testing.assert_array_equal(default, explicit_off)


def test_ercot_zonal_spread_ep_referenced_shifts_only_the_f923_group():
    """Each zone's delta is ONE exact constant, and the two groups split it.

    The F923 rows move by ``-ep_basis * (1 - w923)`` and the convention rows by
    ``+ep_basis * w923``, where w923 is the F923 zones' gas-capacity share --
    the arithmetic of shifting one group before a capacity-weighted mean-zero
    recentring. On this fixture w923 = 2/3.
    """
    from market_sim.data.fuel import (
        apply_ercot_zonal_gas_basis,
        ercot_electric_power_gas_basis,
    )

    hours = 24
    fleet = _ercot_mixed_provenance_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)
    ep = ercot_electric_power_gas_basis(2021)
    assert ep is not None

    control = base.copy()
    apply_ercot_zonal_gas_basis(control, fleet, cfg, 2021)
    arm = base.copy()
    apply_ercot_zonal_gas_basis(
        arm, fleet, cfg.with_overrides(ercot_zonal_spread_ep_referenced=True), 2021
    )
    delta = arm - control

    w923 = 2.0 / 3.0  # North + South_Central of three equal-pmax units
    for row, zone in enumerate(("North", "South_Central", "Houston")):
        expected = -ep * (1.0 - w923) if zone != "Houston" else ep * w923
        assert np.ptp(delta[row]) == pytest.approx(0.0, abs=1e-12), zone
        assert delta[row, 0] == pytest.approx(expected, abs=1e-9), zone
    # 2021 is the year the defect bites: the F923 rows fall and Houston rises.
    assert delta[0, 0] < -1.0 and delta[2, 0] > 1.0


def test_ercot_zonal_spread_ep_referenced_is_exactly_level_neutral():
    """The mechanism is a pure redistribution: the fleet level does not move.

    This is the defining property. The capacity-weighted mean delivered gas
    price must be unchanged to machine precision in EVERY year the table
    covers -- if it moves, the mechanism is re-levelling, which is a different
    (and forbidden) thing.
    """
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_mixed_provenance_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)
    weights = fleet.pmax

    checked = 0
    for year in range(2019, 2026):
        control = base.copy()
        apply_ercot_zonal_gas_basis(control, fleet, cfg, year)
        arm = base.copy()
        apply_ercot_zonal_gas_basis(
            arm, fleet, cfg.with_overrides(ercot_zonal_spread_ep_referenced=True), year
        )
        delta = (arm - control).mean(axis=1)
        level = float((delta * weights).sum() / weights.sum())
        assert level == pytest.approx(0.0, abs=1e-9), year
        checked += 1
    assert checked >= 6


def test_ercot_zonal_spread_ep_referenced_preserves_within_group_differentials():
    """Referencing shifts the F923 group bodily; it never reshapes it.

    Two F923 zones keep exactly their measured price difference, which is the
    locational content the spread is supposed to carry.
    """
    from market_sim.data.fuel import apply_ercot_zonal_gas_basis

    hours = 24
    fleet = _ercot_mixed_provenance_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(iso="ERCOT", hours=hours, ercot_zonal_gas_basis=True)

    control = base.copy()
    apply_ercot_zonal_gas_basis(control, fleet, cfg, 2021)
    arm = base.copy()
    apply_ercot_zonal_gas_basis(
        arm, fleet, cfg.with_overrides(ercot_zonal_spread_ep_referenced=True), 2021
    )
    # rows 0 and 1 are North and South_Central, both F923.
    assert (arm[0, 0] - arm[1, 0]) == pytest.approx(
        control[0, 0] - control[1, 0], abs=1e-12
    )


def test_ercot_zonal_spread_ep_referenced_is_inert_for_a_forward_year():
    """No EP row -> no reference -> byte-identical, so forecasts never move."""
    from market_sim.data.fuel import (
        apply_ercot_zonal_gas_basis,
        ercot_electric_power_gas_basis,
    )

    assert ercot_electric_power_gas_basis(2035) is None
    hours = 24
    fleet = _ercot_mixed_provenance_fleet(hours)
    base = np.full((fleet.n_gen, hours), 3.72)
    cfg = ScenarioConfig(
        iso="ERCOT",
        hours=hours,
        ercot_zonal_gas_basis=True,
        ercot_zonal_spread_ep_referenced=True,
    )
    out = base.copy()
    apply_ercot_zonal_gas_basis(out, fleet, cfg, 2035)
    np.testing.assert_array_equal(out, base)


def test_nyiso_total_east_cutset_ttc_replaces_central_east():
    """nyiso-224: armed, the link takes the TOTAL EAST cutset envelope, not CENT EAST.

    Rule 19 [R-ONE-MECH] in test form — the two tables never stack: the armed
    column equals NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH exactly, and the unarmed
    column stays byte-identical to the incumbent CENT EAST path, so every
    registered keeper is unmoved.
    """
    from scripts.run_calibration import _apply_iso_monthly_ttc
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.config.constants import (
        NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH,
        NYISO_INTERFACE_TTC_BY_MONTH,
    )

    cfg = get_iso_config("NYISO")
    ttc = np.array([link.ttc_mw for link in cfg.links], dtype=float)
    hours = 8760
    link_key = ("Upstate_West", "Capital_Hudson")
    ce = next(
        i
        for i, link in enumerate(cfg.links)
        if (link.from_zone, link.to_zone) == link_key
    )

    class _Armed:
        nyiso_total_east_cutset_ttc = True

    class _Off:
        nyiso_total_east_cutset_ttc = False

    base = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2022, hours)
    off = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2022, hours, config=_Off())
    arm = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2022, hours, config=_Armed())

    # Unarmed (and the no-config legacy call) is byte-identical to the incumbent.
    incumbent = NYISO_INTERFACE_TTC_BY_MONTH[2022][link_key]
    assert np.array_equal(base, off)
    assert off[0, ce] == incumbent[0]
    assert off[hours - 1, ce] == incumbent[11]

    # Armed selects the cutset envelope, month by month.
    envelope = NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH[2022][link_key]
    assert arm[0, ce] == envelope[0]
    assert arm[31 * 24, ce] == envelope[1]
    assert arm[hours - 1, ce] == envelope[11]

    # Every other link is untouched by either path.
    others = [i for i in range(len(cfg.links)) if i != ce]
    assert np.array_equal(arm[:, others], off[:, others])

    # The cutset the link represents is strictly wider than its nested
    # sub-cutset in every month of 2022 — the misalignment this arm repairs.
    assert all(e > c for e, c in zip(envelope, incumbent))
