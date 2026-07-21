"""Fuel price and NOx price resolution.

Resolves per-generator delivered fuel prices ($/MMBtu) and the scenario
NOx price into the forms consumed by marginal-cost assembly
(see :func:`market_sim.data.fleet.assemble_mc`). Carbon-price resolution
lives in :mod:`market_sim.policy.carbon`.

Package split of the former ``data/fuel.py`` god-module (W-D3, 2026-07-21;
refactor-consolidation plan §5 item 3):

- :mod:`._shared` — cross-cutting leaf: fuel-type codes, month calendar,
  clean-data gate, and the :func:`~._shared._pkg_ns` call-time resolver.
- :mod:`.trajectories` — annual gas/coal/oil/nuclear/NOx resolvers, seasonal
  shapes, and the gas-keyed coal passthrough sigmoids.
- :mod:`.hubs` — measured hub series (Henry Hub / Transco / Algonquin /
  Iroquois / CA-composite / Chicago), staircases, daily shape factors, the
  hub-month reconstruction and the hub-basis overlay
  (``load_winter_gas_basis`` / ``apply_hub_basis_overlay`` family).
- :mod:`.basis` — the per-ISO zonal gas-basis appliers
  (``basis/{nyiso,ercot,pjm,miso,caiso}.py``) behind the
  :data:`~.basis.ZONAL_BASIS_APPLIERS` registry consumed by :mod:`.resolve`.
- :mod:`.plant_prices` — EIA-923 plant/ISO-month delivered costs (F923).
- :mod:`.dual_fuel` — oil/gas switch-capable pricing and the switch mask.
- :mod:`.coal` — CAMPD coal supply-class (lignite / PRB-by-rail) pricing.
- :mod:`.resolve` — :func:`resolve_fuel_prices`, the orchestrator.

Compatibility contract: the package holds the EXACT import path of the
pre-split module (``market_sim.data.fuel``), so no ``sys.modules`` alias is
needed (that construction exists for renamed paths like
``eia_loader`` -> ``eia930``): ``from market_sim.data.fuel import <name>``,
``monkeypatch.setattr("market_sim.data.fuel.<name>", ...)``,
``mock.patch.object(fuel, ...)`` and direct ``fuel.<name> = ...`` attribute
writes all land on THIS namespace, which re-exports the entire pre-split
surface — public functions, script/test-imported privates, and the
config/data re-imports that lived in the old module namespace. Package
internals resolve the historically patched names through this namespace at
call time (:func:`._shared._pkg_ns`), so every existing patch keeps
intercepting them. The re-export surface is pinned by
``tests/test_fuel_facade.py``.

**Gas** generators all pay the same delivered price for a year — the AEO
Henry Hub trajectory (:data:`HENRY_HUB_TRAJECTORIES`) plus the ISO basis
differential (:data:`GAS_BASIS_DIFFERENTIAL`), optionally seasonally
shaped. Per-plant EIA-923 monthly gas costs are **off by default**
(``gas_plant_monthly_fuel_pricing``): merchant CCs in a hub all buy gas in
the same market, and EIA-923 Schedule-5 gas reporting is too sparse (~12%
of ERCOT CC MW) to split same-zone units without introducing a spurious
price asymmetry. For pipeline-constrained ISOs whose marginal gas cost is
set by a blown-out trading hub rather than plant receipts (NEISO /
Algonquin Citygate), the measured hub-month basis overlay
(``gas_hub_basis_overlay``, :func:`apply_hub_basis_overlay`) replaces the
gas price with measured Henry Hub monthly + measured hub basis in covered
months.

**Coal** generators in backcast runs (and the capacity hindcast) still pay
their own measured EIA-923 Schedule 5 monthly delivered cost where
reported (lignite mine-mouth vs railed PRB are genuinely different costs),
falling back to the per-year coal supply-class trajectories otherwise. The
same resolver path serves both backcast and forward, so calibration and
projection share one model — but the F923 plant-monthly overlay itself is
MODE-GATED to backcast (:func:`apply_plant_monthly_fuel_prices`): a
forecast run never prices a plant from measured receipts, even for a year
the parquet covers (rule 22 / spec §1.7; G11 / W2-E).
"""

from __future__ import annotations

# Config/data names that were part of the old ``fuel.py`` module namespace
# (from-imports create module globals; scripts/tests may read or patch them
# here — e.g. ``dual_fuel_plant_groups`` is monkeypatched on this namespace
# and read back through ``_pkg_ns()`` by ``dual_fuel.py``).
from market_sim.config.constants import (
    BIOMASS_PRICE_PER_MMBTU,
    CAISO_CITYGATE_TRANSPORT_ADDER,
    COAL_PRICE_BASE,
    COAL_PRICE_ESCALATION,
    COAL_PRICE_TRAJECTORIES,
    END_YEAR,
    GAS_BASIS_DIFFERENTIAL,
    GAS_MONTHLY_SEASONALITY,
    HENRY_HUB_TRAJECTORIES,
    HOURS_PER_YEAR,
    INFLATION_RATE,
    LIGNITE_PRICE_2023_25,
    NUCLEAR_FUEL_PRICE_HISTORICAL,
    OIL_PRICE_PER_MMBTU,
    OIL_PRICE_TRAJECTORIES,
    PRB_COMMODITY_DECLINE,
    PRB_COMMODITY_FLAT_THROUGH,
    PRB_COMMODITY_SHARE,
    PRB_PRICE_BY_YEAR,
    PRB_RAIL_DIESEL_SHARE,
    PRB_RAIL_NONDIESEL_SHARE,
    START_YEAR,
)
from market_sim.config.paths import GAS_PRICES_DIR, RAW_DATA_DIR
from market_sim.config.scenarios import COAL_SIGMOID_DEFAULTS, ScenarioConfig
from market_sim.data.eia923 import (
    EIA923_MONTHLY_COSTS_PATH,
    available_years,
    load_monthly_fuel_costs,
    plant_month_price_grid,
    state_month_price_grid,
)
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    FleetArrays,
    dual_fuel_plant_groups,
)
from market_sim.data.hydrogen import compute_h2_fuel_cost

from ._shared import (
    _BIOMASS_FUEL_IDX as _BIOMASS_FUEL_IDX,
    _COAL_FUEL_IDX as _COAL_FUEL_IDX,
    _DAYS_IN_MONTH as _DAYS_IN_MONTH,
    _FUEL_BASIS_DATATYPE as _FUEL_BASIS_DATATYPE,
    _FUEL_ERCOT_EP_GAS_DATATYPE as _FUEL_ERCOT_EP_GAS_DATATYPE,
    _FUEL_HUB_MONTHLY_DATATYPE as _FUEL_HUB_MONTHLY_DATATYPE,
    _FUEL_PRICES_DATATYPE as _FUEL_PRICES_DATATYPE,
    _FUEL_TAKEORPAY_DATATYPE as _FUEL_TAKEORPAY_DATATYPE,
    _FUEL_ZONAL_HUB_DATATYPE as _FUEL_ZONAL_HUB_DATATYPE,
    _GAS_FUEL_IDX as _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR as _GAS_PRICE_FLOOR,
    _HENRY_HUB_CLEAN_KEY as _HENRY_HUB_CLEAN_KEY,
    _HYDROGEN_FUEL_IDX as _HYDROGEN_FUEL_IDX,
    _NUCLEAR_FUEL_IDX as _NUCLEAR_FUEL_IDX,
    _OIL_FUEL_IDX as _OIL_FUEL_IDX,
    _USE_CLEAN_ENV as _USE_CLEAN_ENV,
    _USE_CLEAN_TRUTHY as _USE_CLEAN_TRUTHY,
    _ZERO_FUEL_PRICE as _ZERO_FUEL_PRICE,
    _clean_zonal_hub_frame as _clean_zonal_hub_frame,
    _expand_monthly_to_hourly as _expand_monthly_to_hourly,
    _month_index as _month_index,
    _use_clean_data as _use_clean_data,
    logger,
)
from .trajectories import (
    _COAL_SIGMOID_FIELD_STEM as _COAL_SIGMOID_FIELD_STEM,
    _COAL_SIGMOID_PARAMS as _COAL_SIGMOID_PARAMS,
    _gas_series as _gas_series,
    _hold_flat_extrapolate as _hold_flat_extrapolate,
    _seasonal_factors as _seasonal_factors,
    _sigmoid_passthrough as _sigmoid_passthrough,
    coal_passthrough_by_supply,
    coal_passthrough_series,
    coal_sigmoid_params,
    gas_seasonal_shape,
    prb_follower_passthrough_series,
    resolve_annual_coal_price,
    resolve_annual_gas_price,
    resolve_annual_oil_price,
    resolve_nox_price,
    resolve_nuclear_fuel_price,
)
from .hubs import (
    ALGONQUIN_DAILY_PATH,
    CAISO_CITYGATE_DAILY_PATH,
    HENRY_HUB_DAILY_PATH,
    HENRY_HUB_MONTHLY_PATH,
    IROQUOIS_Z2_DAILY_PATH,
    MISO_CITYGATE_DAILY_PATH,
    PGE_SOCAL_CITYGATE_WEEKLY_PATH,
    TRANSCO_Z6_NY_DAILY_PATH,
    WINTER_GAS_BASIS_PATH,
    _ALGONQUIN_DAILY_CACHE as _ALGONQUIN_DAILY_CACHE,
    _ALGONQUIN_DAILY_CLEAN_CACHE as _ALGONQUIN_DAILY_CLEAN_CACHE,
    _CAISO_CITYGATE_DAILY_CACHE as _CAISO_CITYGATE_DAILY_CACHE,
    _CAISO_CITYGATE_DAILY_CLEAN_CACHE as _CAISO_CITYGATE_DAILY_CLEAN_CACHE,
    _HH_DAILY_CACHE as _HH_DAILY_CACHE,
    _HH_DAILY_CLEAN_CACHE as _HH_DAILY_CLEAN_CACHE,
    _HH_DAILY_DATED_CACHE as _HH_DAILY_DATED_CACHE,
    _HH_DAILY_DATED_CLEAN_CACHE as _HH_DAILY_DATED_CLEAN_CACHE,
    _HH_MONTHLY_CACHE as _HH_MONTHLY_CACHE,
    _HH_MONTHLY_CLEAN_CACHE as _HH_MONTHLY_CLEAN_CACHE,
    _IROQUOIS_DAILY_CACHE as _IROQUOIS_DAILY_CACHE,
    _MISO_CITYGATE_DAILY_CACHE as _MISO_CITYGATE_DAILY_CACHE,
    _TRANSCO_DAILY_CACHE as _TRANSCO_DAILY_CACHE,
    _TRANSCO_DAILY_DATED_CACHE as _TRANSCO_DAILY_DATED_CACHE,
    _WINTER_BASIS_CACHE as _WINTER_BASIS_CACHE,
    _WINTER_BASIS_CLEAN_CACHE as _WINTER_BASIS_CLEAN_CACHE,
    _algonquin_daily as _algonquin_daily,
    _caiso_citygate_daily_dated as _caiso_citygate_daily_dated,
    _caiso_hub_daily_gas_prices as _caiso_hub_daily_gas_prices,
    _clean_algonquin_daily as _clean_algonquin_daily,
    _clean_caiso_citygate_daily as _clean_caiso_citygate_daily,
    _clean_fuel_price_daily as _clean_fuel_price_daily,
    _clean_fuel_price_daily_dated as _clean_fuel_price_daily_dated,
    _clean_hub_monthly as _clean_hub_monthly,
    _flow_date_staircase as _flow_date_staircase,
    _henry_hub_daily as _henry_hub_daily,
    _henry_hub_daily_dated as _henry_hub_daily_dated,
    _henry_hub_monthly as _henry_hub_monthly,
    _hub_overlay_series as _hub_overlay_series,
    _iroquois_z2_daily as _iroquois_z2_daily,
    _load_winter_basis_frame as _load_winter_basis_frame,
    _miso_citygate_daily_dated as _miso_citygate_daily_dated,
    _nyiso_hub_daily_gas_prices as _nyiso_hub_daily_gas_prices,
    _trade_date_staircase as _trade_date_staircase,
    _transco_z6_daily as _transco_z6_daily,
    _transco_z6_daily_dated as _transco_z6_daily_dated,
    apply_hub_basis_overlay,
    gas_daily_shape_factors,
    iso_hub_daily_gas_prices,
    iso_hub_monthly_gas_prices,
    load_winter_gas_basis,
    socal_citygate_weekly_hourly,
)
from .basis import (
    ZONAL_BASIS_APPLIERS,
    ZONAL_BASIS_ORDER,
    apply_caiso_zonal_gas_basis,
    apply_ercot_west_netload_gas_shape,
    apply_ercot_zonal_gas_basis,
    apply_miso_winter_citygate_daily,
    apply_miso_zonal_gas_basis,
    apply_nyiso_downstate_ct_gas_basis,
    apply_nyiso_downstate_ct_gas_daily,
    apply_nyiso_zonal_gas_basis,
    apply_pjm_zonal_gas_basis,
    caiso_zonal_gas_basis_by_zone,
    ercot_electric_power_gas_basis,
    ercot_gas_spot_share_by_plant,
    ercot_gas_spot_share_by_zone,
    ercot_waha_collapse_freq,
    ercot_west_oversupply_collapse_freq,
    ercot_zonal_gas_basis_by_zone,
    miso_chicago_daily_shape_factors,
    miso_zonal_gas_basis_by_zone,
    nyiso_downstate_ct_gas_premium,
    nyiso_reconciled_reference_monthly,
    nyiso_zonal_gas_offsets,
    nyiso_zonal_gas_ratios_monthly,
    pjm_zonal_gas_basis_by_zone,
)
from .basis.ercot import (
    ERCOT_BIN_ASSIGNMENTS_PATH,
    ERCOT_ELECTRIC_POWER_GAS_PATH,
    ERCOT_GAS_TAKEORPAY_PATH,
    ERCOT_ZONAL_GAS_HUB_PATH,
    _ERCOT_EP_GAS_CACHE as _ERCOT_EP_GAS_CACHE,
    _ERCOT_EP_GAS_CLEAN_CACHE as _ERCOT_EP_GAS_CLEAN_CACHE,
    _ERCOT_GAS_SPOT_CACHE as _ERCOT_GAS_SPOT_CACHE,
    _ERCOT_GAS_SPOT_PLANT_CACHE as _ERCOT_GAS_SPOT_PLANT_CACHE,
    _ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE as _ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE,
    _ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE as _ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE,
    _ERCOT_WAHA_ZONES as _ERCOT_WAHA_ZONES,
    _ERCOT_ZONAL_HUB_CACHE as _ERCOT_ZONAL_HUB_CACHE,
    _ERCOT_ZONAL_HUB_CLEAN_CACHE as _ERCOT_ZONAL_HUB_CLEAN_CACHE,
    _MCF_TO_MMBTU as _MCF_TO_MMBTU,
    _WEST_GAS_COLLAPSE_FREQ_DEFAULT as _WEST_GAS_COLLAPSE_FREQ_DEFAULT,
    _clean_ercot_ep_gas_frame as _clean_ercot_ep_gas_frame,
    _clean_takeorpay_plant_dict as _clean_takeorpay_plant_dict,
    _load_ercot_electric_power_gas as _load_ercot_electric_power_gas,
    _load_ercot_zonal_gas_hub as _load_ercot_zonal_gas_hub,
)
from .basis.meanzero import (
    CAISO_ZONAL_GAS_HUB_PATH,
    MISO_ZONAL_GAS_HUB_PATH,
    PJM_ZONAL_GAS_HUB_PATH,
    _ZONAL_HUB_CACHE as _ZONAL_HUB_CACHE,
    _ZONAL_HUB_ISO_CLEAN_CACHE as _ZONAL_HUB_ISO_CLEAN_CACHE,
    _apply_meanzero_zonal_gas_basis as _apply_meanzero_zonal_gas_basis,
    _load_zonal_gas_hub as _load_zonal_gas_hub,
    _zonal_gas_basis_by_zone as _zonal_gas_basis_by_zone,
)
from .basis.miso import (
    _MISO_WINTER_MONTHS as _MISO_WINTER_MONTHS,
    _miso_chicago_hub_zones as _miso_chicago_hub_zones,
)
from .basis.nyiso import (
    NYISO_DOWNSTATE_CT_GAS_BASIS_PATH,
    NYISO_DOWNSTATE_CT_ZONES,
    NYISO_GAS_HUB_REFERENCE_ZONE,
    NYISO_ZONAL_GAS_HUB_PATH,
    TRANSCO_IROQUOIS_MONTHLY_PATH,
    _NYISO_DOWNSTATE_CT_BASIS_CACHE as _NYISO_DOWNSTATE_CT_BASIS_CACHE,
    _NYISO_ZONAL_HUB_CACHE as _NYISO_ZONAL_HUB_CACHE,
    _NYISO_ZONAL_HUB_CLEAN_CACHE as _NYISO_ZONAL_HUB_CLEAN_CACHE,
    _downstate_delivered_gas_hourly_by_zone as _downstate_delivered_gas_hourly_by_zone,
    _load_nyiso_zonal_gas_hub as _load_nyiso_zonal_gas_hub,
    _zone_delivered_hourly as _zone_delivered_hourly,
)
from .plant_prices import (
    _F923_FUEL_GROUP_BY_FUEL as _F923_FUEL_GROUP_BY_FUEL,
    _PLANT_MONTHLY_CACHE as _PLANT_MONTHLY_CACHE,
    _NearbyFuelPrices as _NearbyFuelPrices,
    _fuel_name as _fuel_name,
    _iso_monthly_fuel_prices as _iso_monthly_fuel_prices,
    _load_monthly_cache as _load_monthly_cache,
    apply_plant_monthly_fuel_prices,
    iso_monthly_gas_prices,
    iso_monthly_oil_prices,
    load_oil_burn_budget,
)
from .dual_fuel import (
    apply_dual_fuel_pricing,
    dual_fuel_oil_price_series,
    dual_fuel_switch_mask,
)
from .coal import (
    COAL_PRICE_LIGNITE_BY_YEAR,
    COAL_PRICE_PRB_BY_YEAR,
    _build_coal_price_trajectories as _build_coal_price_trajectories,
    _prb_monthly_actuals as _prb_monthly_actuals,
    apply_coal_supply_pricing,
)
from .resolve import resolve_fuel_prices

__all__ = [
    # config/data re-imports (old module namespace parity)
    "BIOMASS_PRICE_PER_MMBTU",
    "CAISO_CITYGATE_TRANSPORT_ADDER",
    "COAL_PRICE_BASE",
    "COAL_PRICE_ESCALATION",
    "COAL_PRICE_TRAJECTORIES",
    "COAL_SIGMOID_DEFAULTS",
    "EIA923_MONTHLY_COSTS_PATH",
    "END_YEAR",
    "FUEL_TYPE_MAP",
    "FleetArrays",
    "GAS_BASIS_DIFFERENTIAL",
    "GAS_MONTHLY_SEASONALITY",
    "GAS_PRICES_DIR",
    "HENRY_HUB_TRAJECTORIES",
    "HOURS_PER_YEAR",
    "INFLATION_RATE",
    "LIGNITE_PRICE_2023_25",
    "NUCLEAR_FUEL_PRICE_HISTORICAL",
    "OIL_PRICE_PER_MMBTU",
    "OIL_PRICE_TRAJECTORIES",
    "PRB_COMMODITY_DECLINE",
    "PRB_COMMODITY_FLAT_THROUGH",
    "PRB_COMMODITY_SHARE",
    "PRB_PRICE_BY_YEAR",
    "PRB_RAIL_DIESEL_SHARE",
    "PRB_RAIL_NONDIESEL_SHARE",
    "RAW_DATA_DIR",
    "START_YEAR",
    "ScenarioConfig",
    "available_years",
    "compute_h2_fuel_cost",
    "dual_fuel_plant_groups",
    "load_monthly_fuel_costs",
    "plant_month_price_grid",
    "state_month_price_grid",
    "logger",
    # trajectories
    "coal_passthrough_by_supply",
    "coal_passthrough_series",
    "coal_sigmoid_params",
    "gas_seasonal_shape",
    "prb_follower_passthrough_series",
    "resolve_annual_coal_price",
    "resolve_annual_gas_price",
    "resolve_annual_oil_price",
    "resolve_nox_price",
    "resolve_nuclear_fuel_price",
    # hubs
    "ALGONQUIN_DAILY_PATH",
    "CAISO_CITYGATE_DAILY_PATH",
    "HENRY_HUB_DAILY_PATH",
    "HENRY_HUB_MONTHLY_PATH",
    "IROQUOIS_Z2_DAILY_PATH",
    "MISO_CITYGATE_DAILY_PATH",
    "PGE_SOCAL_CITYGATE_WEEKLY_PATH",
    "TRANSCO_Z6_NY_DAILY_PATH",
    "WINTER_GAS_BASIS_PATH",
    "apply_hub_basis_overlay",
    "gas_daily_shape_factors",
    "iso_hub_daily_gas_prices",
    "iso_hub_monthly_gas_prices",
    "load_winter_gas_basis",
    "socal_citygate_weekly_hourly",
    # basis (registry + per-ISO)
    "ZONAL_BASIS_APPLIERS",
    "ZONAL_BASIS_ORDER",
    "CAISO_ZONAL_GAS_HUB_PATH",
    "ERCOT_BIN_ASSIGNMENTS_PATH",
    "ERCOT_ELECTRIC_POWER_GAS_PATH",
    "ERCOT_GAS_TAKEORPAY_PATH",
    "ERCOT_ZONAL_GAS_HUB_PATH",
    "MISO_ZONAL_GAS_HUB_PATH",
    "NYISO_DOWNSTATE_CT_GAS_BASIS_PATH",
    "NYISO_DOWNSTATE_CT_ZONES",
    "NYISO_GAS_HUB_REFERENCE_ZONE",
    "NYISO_ZONAL_GAS_HUB_PATH",
    "PJM_ZONAL_GAS_HUB_PATH",
    "TRANSCO_IROQUOIS_MONTHLY_PATH",
    "apply_caiso_zonal_gas_basis",
    "apply_ercot_west_netload_gas_shape",
    "apply_ercot_zonal_gas_basis",
    "apply_miso_winter_citygate_daily",
    "apply_miso_zonal_gas_basis",
    "apply_nyiso_downstate_ct_gas_basis",
    "apply_nyiso_downstate_ct_gas_daily",
    "apply_nyiso_zonal_gas_basis",
    "apply_pjm_zonal_gas_basis",
    "caiso_zonal_gas_basis_by_zone",
    "ercot_electric_power_gas_basis",
    "ercot_gas_spot_share_by_plant",
    "ercot_gas_spot_share_by_zone",
    "ercot_waha_collapse_freq",
    "ercot_west_oversupply_collapse_freq",
    "ercot_zonal_gas_basis_by_zone",
    "miso_chicago_daily_shape_factors",
    "miso_zonal_gas_basis_by_zone",
    "nyiso_downstate_ct_gas_premium",
    "nyiso_reconciled_reference_monthly",
    "nyiso_zonal_gas_offsets",
    "nyiso_zonal_gas_ratios_monthly",
    "pjm_zonal_gas_basis_by_zone",
    # plant_prices
    "apply_plant_monthly_fuel_prices",
    "iso_monthly_gas_prices",
    "iso_monthly_oil_prices",
    "load_oil_burn_budget",
    # dual_fuel
    "apply_dual_fuel_pricing",
    "dual_fuel_oil_price_series",
    "dual_fuel_switch_mask",
    # coal
    "COAL_PRICE_LIGNITE_BY_YEAR",
    "COAL_PRICE_PRB_BY_YEAR",
    "apply_coal_supply_pricing",
    # resolve
    "resolve_fuel_prices",
]
