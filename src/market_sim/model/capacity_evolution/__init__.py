"""Capacity evolution: retirements, new entry, adequacy backstop, CCS retrofits.

Package split of the former ``model/capacity.py`` god-module (W-D4,
2026-07-21; refactor-consolidation plan §5 item 4):

- :mod:`.retirements` — confirmed exits (step 0), announced retirements
  (step 1), the economic-retirement screen (step 3) with the reliability
  floor / ``floor_retention_log`` attribution, and the shared
  capacity-market / accreditation / adequacy-requirement helpers
  (``capacity_revenue_per_mw_yr``, ``thermal_accreditation_fraction``,
  ``resolve_adequacy_requirement_mw``, deliverability headroom).
- :mod:`.new_entry` — the economic new-entry screen (step 5): candidate
  techs, Wright's-Law learning curves, LCOE, expected revenue,
  :class:`CumulativeDeployment`, and the shared new-unit factory.
- :mod:`.adequacy` — the accredited-firm-capacity ledger, CR-1 reserve
  position, and the reserve-margin build backstop (step 6).
- :mod:`.ccs` — the gas-CC CCS retrofit screen (step 2, W2-C joint
  retrofit-or-retire).
- :mod:`.evolve` — :func:`evolve_fleet`, the one-pass year step chaining
  steps 0→7 EXACTLY as spec §5.1 orders them.

Compatibility contract: ``market_sim.model.capacity`` (the historical import
path used by src, scripts, and the tests) is a facade that aliases itself to
THIS package via ``sys.modules``, so ``from market_sim.model import
capacity`` returns this module object. This ``__init__`` therefore re-exports
the ENTIRE pre-split module surface — public functions, test/script-imported
privates, and the config/data/policy re-imports that lived in the old module
namespace — and the package internals resolve the historically monkeypatched
names (the six ``evolve_fleet`` step functions and
``estimate_expected_revenue``) through this namespace at call time, so every
existing ``mock.patch("market_sim.model.capacity.<name>")``,
``mock.patch.dict("market_sim.model.capacity.MARKET_DESIGN", ...)`` and
probe-style ``capacity.<name> = wrapped`` keeps intercepting them. The
re-export surface is pinned by ``tests/test_capacity_evolution_facade.py``.
"""

from __future__ import annotations

# Config/data/policy names that were part of the old ``model/capacity.py``
# module namespace (from-imports create module globals; scripts and tests
# resolve several of them through this namespace — e.g. the
# ``mock.patch.dict("market_sim.model.capacity.MARKET_DESIGN", ...)`` target).
from market_sim.config.constants import (
    ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO,
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    CCUS_PARAMS,
    CO2_RATES,
    DEFAULT_MARKET_DESIGN,
    EFORD,
    FORECAST_POOL_REQUIREMENT_BY_ISO,
    GEOTHERMAL_PARAMS,
    GLOBAL_ANNUAL_DEPLOYMENT_GW,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    HYDROGEN_TURBINE_PARAMS,
    MARKET_DESIGN,
    NEW_ENTRY_COSTS,
    NONFOSSIL_ANNOUNCED_HORIZON_YEARS,
    NOX_RATES,
    OFFSHORE_WIND_PARAMS,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_CAPACITY_CREDIT_BY_ISO,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO,
    STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO,
    THERMAL_ACCREDITATION_BASIS_BY_ISO,
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    VOM,
    WRIGHT_REFERENCE_GW,
    evaluate_renewable_elcc_curve,
)
from market_sim.config.capacity_area_crosswalk import aggregate_by_zone
from market_sim.config.entry_config import (
    ENTRY_COD_LAG_DEFAULT_YEARS,
    ENTRY_COD_LAG_YEARS,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.reserve_config import (
    QUICK_START_FUEL_TYPES,
    RESERVE_FUEL_TYPES,
)
from market_sim.config.scenarios import (
    ScenarioConfig,
    resolve_new_entry_costs,
    resolve_real_discount_rate,
)
from market_sim.data import capacity_deliverability as capdel
from market_sim.model.ancillary import as_revenue_per_mw_yr
from market_sim.data.confirmed_retirements import ConfirmedExit
from market_sim.data.fleet import (
    EIA860_OPERABLE_VINTAGE,
    FleetArrays,
    Generator,
    aggregate_fleet,
)
from market_sim.data.hydrogen import compute_h2_fuel_cost
from market_sim.data.renewables import get_renewable_zone
from market_sim.model.dispatch import DispatchResult
from market_sim.policy.federal_ces import (
    effective_eac_price_for_tech,
    effective_eac_price_for_unit,
)
from market_sim.policy.ira import (
    apply_ira_credits_to_lcoe,
    ccus_45q_credit_per_mwh,
    h2_45v_credit_per_mmbtu,
    section_45u_credit_per_mwh,
)

from .retirements import (
    _CLEAN_FUELS as _CLEAN_FUELS,
    _CONFIRMED_EXIT_MW_EPS as _CONFIRMED_EXIT_MW_EPS,
    _DELIVERABILITY_LONG_BAND as _DELIVERABILITY_LONG_BAND,
    _FIRM_CLEAN_FUELS as _FIRM_CLEAN_FUELS,
    _FOM_MULTIPLIER as _FOM_MULTIPLIER,
    _FOSSIL_FUELS as _FOSSIL_FUELS,
    _NEW_ENTRY_DEFAULT_ZONE as _NEW_ENTRY_DEFAULT_ZONE,
    _RETIREMENT_EXECUTION_LAG as _RETIREMENT_EXECUTION_LAG,
    _RETIREMENT_YEARS as _RETIREMENT_YEARS,
    _RPS_ELIGIBLE_FUELS as _RPS_ELIGIBLE_FUELS,
    _THERMAL_FOM as _THERMAL_FOM,
    _THERMAL_PLANT_LIFE_YEARS as _THERMAL_PLANT_LIFE_YEARS,
    _apply_pipeline_retirements as _apply_pipeline_retirements,
    _apply_reliability_floor as _apply_reliability_floor,
    _confirmed_effective_year as _confirmed_effective_year,
    _default_build_zone as _default_build_zone,
    _derate_generator as _derate_generator,
    _dispatch_rows as _dispatch_rows,
    _execution_lag_years as _execution_lag_years,
    _floor_retention_merit as _floor_retention_merit,
    _is_confirmed_binned as _is_confirmed_binned,
    _renewable_credit as _renewable_credit,
    _storage_portfolio_elcc_dilution as _storage_portfolio_elcc_dilution,
    _thermal_firm_mw as _thermal_firm_mw,
    _unit_generator_id as _unit_generator_id,
    _zone_is_long as _zone_is_long,
    apply_announced_retirements,
    apply_confirmed_exits,
    apply_economic_retirements,
    capacity_revenue_per_mw_yr,
    compute_attribute_revenue,
    compute_clean_share,
    deliverability_headroom_by_zone,
    logger,
    resolve_adequacy_requirement_mw,
    resolve_forecast_pool_requirement,
    resolve_planning_reserve_margin,
    resolve_renewable_capacity_credit,
    thermal_accreditation_fraction,
)
from .new_entry import (
    CumulativeDeployment,
    _EMERGING_AVAILABLE_YEAR as _EMERGING_AVAILABLE_YEAR,
    _EMERGING_SCREEN_CF as _EMERGING_SCREEN_CF,
    _NEW_ENTRY_TECHS as _NEW_ENTRY_TECHS,
    _QUEUE_CAP_GROUP as _QUEUE_CAP_GROUP,
    _RENEWABLE_NEW_FUELS as _RENEWABLE_NEW_FUELS,
    _capital_recovery_factor as _capital_recovery_factor,
    _emerging_lcoe as _emerging_lcoe,
    _emerging_screen_cf as _emerging_screen_cf,
    _make_new_generator as _make_new_generator,
    _merge_renewable_additions as _merge_renewable_additions,
    _new_entry_candidates as _new_entry_candidates,
    _offshore_wind_params as _offshore_wind_params,
    apply_economic_new_entry,
    compute_lcoe,
    estimate_expected_revenue,
    wright_cost,
)
from .ccs import (
    _adjust_retrofit_capex as _adjust_retrofit_capex,
    _ccs_45q_window_years as _ccs_45q_window_years,
    _ccs_retrofit_payback_years as _ccs_retrofit_payback_years,
    _retrofit_price_row as _retrofit_price_row,
    apply_ccs_retrofit,
)
from .adequacy import (
    _firm_import_mw as _firm_import_mw,
    _renewable_nameplate_by_fuel as _renewable_nameplate_by_fuel,
    accredited_firm_capacity_mw,
    apply_reserve_margin_build,
    capacity_reserve_position,
    renewable_credits_applied,
    resolve_reserve_margin_build_enabled,
)
from .evolve import (
    _prior_attr as _prior_attr,
    evolve_fleet,
)

__all__ = [
    # config/data/policy re-imports (old module namespace parity)
    "ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO",
    "ADEQUACY_EXTERNAL_TIE_FIRM_MW",
    "CCUS_PARAMS",
    "CO2_RATES",
    "DEFAULT_MARKET_DESIGN",
    "EFORD",
    "FORECAST_POOL_REQUIREMENT_BY_ISO",
    "GEOTHERMAL_PARAMS",
    "GLOBAL_ANNUAL_DEPLOYMENT_GW",
    "HEAT_RATE_BINS",
    "HOURS_PER_YEAR",
    "HYDROGEN_TURBINE_PARAMS",
    "MARKET_DESIGN",
    "NEW_ENTRY_COSTS",
    "NONFOSSIL_ANNOUNCED_HORIZON_YEARS",
    "NOX_RATES",
    "OFFSHORE_WIND_PARAMS",
    "PLANNING_RESERVE_MARGIN_BY_ISO",
    "PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO",
    "QUEUE_CAP_GW",
    "QUEUE_CAP_PER_TECH_GW",
    "RENEWABLE_CAPACITY_CREDIT",
    "RENEWABLE_CAPACITY_CREDIT_BY_ISO",
    "RENEWABLE_ELCC_CURVES_BY_ISO",
    "STORAGE_DEPLOYMENT_CEILING_MW",
    "STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO",
    "STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO",
    "THERMAL_ACCREDITATION_BASIS_BY_ISO",
    "THERMAL_ELCC_CLASS_RATING_BY_ISO",
    "VOM",
    "WRIGHT_REFERENCE_GW",
    "evaluate_renewable_elcc_curve",
    "aggregate_by_zone",
    "ENTRY_COD_LAG_DEFAULT_YEARS",
    "ENTRY_COD_LAG_YEARS",
    "get_iso_config",
    "QUICK_START_FUEL_TYPES",
    "RESERVE_FUEL_TYPES",
    "ScenarioConfig",
    "resolve_new_entry_costs",
    "resolve_real_discount_rate",
    "capdel",
    "as_revenue_per_mw_yr",
    "ConfirmedExit",
    "EIA860_OPERABLE_VINTAGE",
    "FleetArrays",
    "Generator",
    "aggregate_fleet",
    "compute_h2_fuel_cost",
    "get_renewable_zone",
    "DispatchResult",
    "effective_eac_price_for_tech",
    "effective_eac_price_for_unit",
    "apply_ira_credits_to_lcoe",
    "ccus_45q_credit_per_mwh",
    "h2_45v_credit_per_mmbtu",
    "section_45u_credit_per_mwh",
    # retirements
    "logger",
    "apply_confirmed_exits",
    "apply_announced_retirements",
    "apply_economic_retirements",
    "compute_attribute_revenue",
    "compute_clean_share",
    "capacity_revenue_per_mw_yr",
    "deliverability_headroom_by_zone",
    "resolve_planning_reserve_margin",
    "resolve_forecast_pool_requirement",
    "resolve_adequacy_requirement_mw",
    "resolve_renewable_capacity_credit",
    "thermal_accreditation_fraction",
    # new entry
    "CumulativeDeployment",
    "apply_economic_new_entry",
    "compute_lcoe",
    "estimate_expected_revenue",
    "wright_cost",
    # ccs
    "apply_ccs_retrofit",
    # adequacy
    "accredited_firm_capacity_mw",
    "apply_reserve_margin_build",
    "capacity_reserve_position",
    "renewable_credits_applied",
    "resolve_reserve_margin_build_enabled",
    # evolve
    "evolve_fleet",
]
