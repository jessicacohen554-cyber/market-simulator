"""Tests for fuel price resolution against AEO Henry Hub trajectories."""

import numpy as np
import pytest

from market_sim.config.constants import (
    BIOMASS_PRICE_PER_MMBTU,
    CAISO_CITYGATE_TRANSPORT_ADDER,
    COAL_PRICE_BASE,
    GAS_BASIS_DIFFERENTIAL,
    HENRY_HUB_TRAJECTORIES,
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
    apply_coal_supply_pricing,
    apply_hub_basis_overlay,
    apply_miso_zonal_gas_basis,
    apply_nyiso_zonal_gas_basis,
    apply_pjm_zonal_gas_basis,
    ercot_west_oversupply_collapse_freq,
    iso_hub_monthly_gas_prices,
    iso_monthly_gas_prices,
    load_winter_gas_basis,
    miso_zonal_gas_basis_by_zone,
    nyiso_zonal_gas_offsets,
    pjm_zonal_gas_basis_by_zone,
    resolve_annual_gas_price,
    resolve_fuel_prices,
    resolve_nox_price,
)
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
    expected_gas = HENRY_HUB_TRAJECTORIES["mid"][year] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
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
    """Oil generators are priced at the flat delivered oil cost."""
    fleet = _oil_biomass_fleet()
    prices = resolve_fuel_prices(_config(gas_seasonality=False), fleet, 2030)
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
    # Delivered gas = 25 + PJM basis, far above the flat oil price (forward
    # year: no F923 petroleum data, so oil parity is OIL_PRICE_PER_MMBTU).
    config = ScenarioConfig(
        iso="PJM",
        hours=24,
        gas_seasonality=False,
        gas_price_override=25.0,
        dual_fuel_switching=True,
    )
    prices = resolve_fuel_prices(config, fleet, 2030)
    delivered_gas = resolve_annual_gas_price(config, 2030)
    assert delivered_gas > OIL_PRICE_PER_MMBTU
    np.testing.assert_allclose(prices[0], OIL_PRICE_PER_MMBTU)  # switched
    np.testing.assert_allclose(prices[1], delivered_gas)  # gas-only
    np.testing.assert_allclose(prices[2], OIL_PRICE_PER_MMBTU)  # oil unit


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
    gas = np.array([3.0, 30.0, 17.9, 50.0])
    fuel_prices = np.vstack([gas, gas, np.full(4, OIL_PRICE_PER_MMBTU)])
    apply_dual_fuel_pricing(fuel_prices, fleet, config, 2030)
    np.testing.assert_allclose(
        fuel_prices[0], [3.0, OIL_PRICE_PER_MMBTU, 17.9, OIL_PRICE_PER_MMBTU]
    )
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
    assert delivered_gas > OIL_PRICE_PER_MMBTU
    np.testing.assert_allclose(prices[0], OIL_PRICE_PER_MMBTU)  # switched to oil
    np.testing.assert_allclose(prices[1], delivered_gas)  # gas-only
    np.testing.assert_allclose(prices[2], OIL_PRICE_PER_MMBTU)  # pure-oil unit


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
    # NYISO year with no table entry.
    out_old = _apply_iso_monthly_ttc(ttc, cfg, "NYISO", 2099, 8760)
    assert np.asarray(out_old).ndim == 1
    np.testing.assert_array_equal(out_old, ttc)


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
