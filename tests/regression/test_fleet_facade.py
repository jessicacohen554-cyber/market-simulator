"""Facade re-export tests for the ``data/fleet.py`` -> ``data/fleet`` package split.

The 11,199-line ``data/fleet.py`` was split into the ``data/fleet/`` package
(models / withholding / eia860 / campd_bins / arrays / floors / offer_surfaces
/ legacy_bins / assembly) on 2026-07-23 (refactor-consolidation plan §5 item
8). The package holds the EXACT import path of the pre-split module (the
``data/fuel`` pattern — no ``sys.modules`` alias needed), so its ``__init__``
must re-export the entire pre-split surface.

Pinned contracts:

* **Historical surface** — the frozen inventory below is the complete
  pre-split module namespace (AST + runtime census 2026-07-23: 316 top-level
  names, superset of the 116 distinct names src/scripts/tests importers pull
  from ``market_sim.data.fleet``). Extend, never prune.
* **Home identity** — each moved name resolves via the package to the very
  object defined in its new home submodule.
* **Pickle identity** — ``Generator`` and ``FleetArrays`` are defined
  PHYSICALLY in the package ``__init__`` so ``__module__`` stays
  ``market_sim.data.fleet`` (plan §1: the committed ``p2_state`` pickles
  resolve both classes by that path). tests/regression/test_persisted_identity.py owns
  the primary assertion; this pins it against facade regressions.
* **Patch transparency** — ``mock.patch("market_sim.data.fleet.X")``
  intercepts package internals that resolve historically-patched names at
  call time via :func:`market_sim.data.fleet.models._pkg_ns` (census union in
  that docstring).
"""

from __future__ import annotations

import importlib
from unittest import mock

# Every top-level name the pre-split fleet.py namespace carried (module logger
# included), captured at the split commit. This is the package's minimum
# contractual surface.
#
# ``_name`` / ``_code`` are deliberately NOT pinned: they were the leaked loop
# temporaries of the module-level ``for _name, _code in FUEL_TYPE_MAP.items()``
# that fills FUEL_TYPE_NAMES, never API, and nothing in src/scripts/tests
# imports them. That loop now runs in the ``.models`` leaf, so the temporaries
# leak there instead of here (the F811 de-duplication, 2026-07-30).
HISTORICAL_SURFACE = (
    "BA_CODE_TO_ISO",
    "BINNED_FLEET_COLUMNS",
    "BIN_FORCED_DERATE_BY_YEAR",
    "BIN_GROUP_HR_DEFAULT",
    "BIN_GROUP_TO_FUEL",
    "BIN_STARTUP_COST_PER_MW",
    "BIOMASS_ENERGY_SOURCES",
    "BaseModel",
    "CAISO_CHP_CC_STEAM_CREDIT_FACTOR",
    "CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR",
    "CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD",
    "CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD",
    "CAISO_EOR_TOPPING_FACTOR",
    "CAISO_EOR_TOPPING_PLANTS",
    "CAMPD_BINNING_ISOS",
    "CAMPD_BINS_CSV",
    "CC_DUCT_BURNER_PEAK_MULT",
    "CC_ECON_HR_OVERRIDE_DEFAULT",
    "CC_PEAK_HR_OVERRIDE_DEFAULT",
    "CC_REGULAR_COMMITTED_PCT_BY_PLANT",
    "CHP_BTM_PCT_BY_SECTOR",
    "CHP_PMIN_CF_BY_PLANT",
    "CHP_SECTOR_CLASS_BY_PLANT",
    "CHP_STEAM_CREDIT_HR_CORRECTION_ISOS",
    "CHP_ST_BTM_PCT",
    "CO2_RATES",
    "COAL_BIN_MIN_DOWN_HOURS",
    "COAL_BIN_MIN_RUN_HOURS",
    "COAL_MAX_CF_BY_PLANT",
    "COAL_MUSTRUN_BY_PLANT",
    "COAL_PLANT_COMMISSION_YEAR",
    "COAL_PLANT_SUPPLY",
    "COAL_SUMMER_MAX_CF",
    "COAL_SUPPLY_TO_CLASS",
    "CONDITIONAL_SURFACE_GROUPS",
    "EFORD",
    "EIA860_OPERABLE_VINTAGE",
    "EIA_860_CSV_COLUMNS",
    "EIA_860_DIR",
    "EIA_860_MULTIFUEL_PARQUET_NAME",
    "EIA_860_PARQUET_NAME",
    "EIA_860_RETIRED_WINDOW_PARQUET_NAME",
    "FUEL_CO2_FACTOR_PER_MMBTU",
    "FUEL_TYPE_MAP",
    "FUEL_TYPE_NAMES",
    "FleetArrays",
    "GAS_ST_ECON_HR_OVERRIDE_DEFAULT",
    "GAS_ST_PEAK_HR_OVERRIDE_DEFAULT",
    "Generator",
    "HEAT_RATE_BINS",
    "HOURS_PER_YEAR",
    "ISOConfig",
    "ISO_TO_BA_CODE",
    "MAINTENANCE_MONTHLY_SHAPE",
    "MECH_CC_MUSTRUN_PER_PLANT",
    "MECH_CHP_STEAM",
    "MECH_COAL_MUSTRUN",
    "MECH_CT_DEPLOYMENT_OVERLAY",
    "MECH_CT_MUSTRUN_PER_PLANT",
    "MECH_CT_NETLOAD_DRAG",
    "MECH_NUCLEAR",
    "MECH_RELIABILITY_DEPLOYMENT_OVERLAY",
    "MECH_ST_GAS_MUSTRUN_PER_PLANT",
    "MECH_ST_NETLOAD_DRAG",
    "MIXED_FACILITY_STEAM_HR",
    "NOX_RATES",
    "NUCLEAR_DORMANT_UNTIL",
    "NUCLEAR_MONTHLY_CF",
    "NUCLEAR_MONTHLY_CF_BY_YEAR",
    "OIL_ENERGY_SOURCES",
    "OTHER_FOSSIL_CLASS",
    "OTHER_FOSSIL_MIN_DOMINANT_FRAC",
    "PETRA_NOVA_MIN_CF",
    "PETRA_NOVA_PARASITIC_PCT",
    "PETRA_NOVA_PLANT_CODE",
    "PLANT_EMISSION_RATES_PATH",
    "PLANT_TRANCHE_OVERRIDE_FIELDS",
    "PROCESSED_DIR",
    "Path",
    "RAMP10_FRAC_BY_FUEL",
    "RAMP10_FRAC_BY_GROUP",
    "RAW_DATA_DIR",
    "START_YEAR",
    "ST_GAS_PEAKER_PLANTS",
    "ScenarioConfig",
    "THERMAL_AVAILABILITY",
    "USE_CLEAN_ENV",
    "VOM",
    "_AGGREGATABLE_FUELS",
    "_AS_GAS_GROUPS",
    "_AS_MAX_GAP_HOURS",
    "_AS_MODEL_CALENDAR",
    "_AS_MODEL_INDEX",
    "_AS_PJM_GROUPS",
    "_AS_RESTYPE_TO_GROUPS",
    "_AS_THERMAL_GROUPS",
    "_AS_WITHHOLDING",
    "_AS_WITHHOLDING_DIR",
    "_BIN_KEY_COLUMNS",
    "_BIOMASS_ENERGY_SOURCES",
    "_CAISO_MORC_LOAD_FRAC",
    "_CAISO_MSSC_EXCLUDE_FUELS",
    "_CAISO_REG_UP_LOAD_FRAC",
    "_CAMPD_BINS_CACHE",
    "_CC_NAMEPLATE_GUARD_TOL",
    "_CC_PRIME_MOVERS",
    "_CC_SHOULDER_MONTHS",
    "_CHP_GROUP_FOR",
    "_CLEAN_AS_UP_MW_COLS",
    "_CLEAN_FUEL_TO_ENERGY_SOURCE",
    "_COAL_CHP_FLOOR_CAP_PCT",
    "_COAL_CHP_FLOOR_FACTOR",
    "_COAL_ENERGY_SOURCES",
    "_COAL_SUMMER_TECH",
    "_COAL_SUPPLY_TO_CURVE",
    "_COAL_SYNC_FORCE_ALL",
    "_COLUMN_ALIASES",
    "_COST_OF_SERVICE_ENTITY_TYPES",
    "_DEFAULT_HR_MULT_BY_GROUP",
    "_DEFAULT_TRANCHE_PCT_BY_GROUP",
    "_EIA860_GAS_GROUPS",
    "_EIA860_PLANT_GROUP_BY_FUEL",
    "_ERCOT_CLEARED_SHARE_CLASS_OF",
    "_ERCOT_CLEARED_SHARE_STEAM_CLASS_OF",
    "_ERCOT_MIDCURVE_CLASS_OF",
    "_GAS_BIN_GROUPS",
    "_GAS_THERMAL_SCORING_CLASSES",
    "_KG_PER_TONNE",
    "_LOWCURVE_ECON_SUFFIXES",
    "_NUCLEAR_ZONE_OVERRIDES",
    "_OIL_ENERGY_SOURCES",
    "_OIL_PRIMARY_FUEL_CODES",
    "_OIL_PRIMARY_PRIME_MOVERS",
    "_OIL_PRIMARY_TECHNOLOGY",
    "_OIL_PRIMARY_UNIT_FUEL_CODES",
    "_PJM_MIDCURVE_SEGMENT_OF",
    "_PLANNED_FIRM_STATUSES",
    "_POF_DROP_GROUPS",
    "_RAMP_BUCKET_BY_GROUP",
    "_SUMMER_CLASS_DERATE",
    "_SUMMER_MONTHS",
    "_SUMMER_WEFOR_SHARE",
    "_USE_CLEAN_TRUTHY",
    "_aggregate_with_predefined_bins",
    "_apply_forward_control_retrofits",
    "_assign_zones",
    "_assign_zones_proportional",
    "_binned_fleet_frame",
    "_cache_binned_fleet",
    "_capacity_weighted",
    "_cc_demonstrated_peaks",
    "_chp_by_plant",
    "_clean_as_reserve_withholding_mw",
    "_clean_fleet_to_normalized",
    "_clean_fleet_year",
    "_coal_class_for",
    "_conditional_surface_markup",
    "_correct_chp_steam_credit_hr",
    "_correct_mixed_facility_steam_hr",
    "_dam_waterfill",
    "_drop_biomass_units",
    "_dual_fuel_plant_groups",
    "_econ_curve_steps",
    "_econ_split_for_group",
    "_efficiency_bin",
    "_eia860_plant_sector",
    "_eia923_plant_class_totals",
    "_ercot_dam_plant_hourly_apply",
    "_fill_hr_multiplier",
    "_fill_plant_hr",
    "_hour_to_month_index",
    "_hr_override",
    "_load_condbinned_surface",
    "_load_ct_offer_surface",
    "_load_ercot_online_span_tables",
    "_load_ercot_stgas_seasonal_drag",
    "_load_fleet_from_clean",
    "_load_fleet_from_parquet",
    "_load_plant_registry_cached",
    "_lowcurve_row_family",
    "_map_fuel_type",
    "_measured_plant_rate_map_v2",
    "_normalize_columns",
    "_nuclear_zone_override",
    "_offer_curve_for_group",
    "_oil_primary_bin_plants",
    "_override_bin_class_from_eia923",
    "_plant_emission_rate_map",
    "_ramp10_capability",
    "_read_clean",
    "_reconcile_cc_capacity",
    "_reconcile_cc_pmax_to_nameplate",
    "_record_oris",
    "_rows_to_generators",
    "_thermal_outage",
    "_to_float",
    "_to_month",
    "_to_year",
    "_use_clean",
    "_withdraw_top_of_merit",
    "_zone_for_index",
    "active_eia860_dir",
    "aggregate_fleet",
    "aggregate_fleet_by_efficiency",
    "annotations",
    "apply_coal_tranches",
    "apply_ct_netload_drag_floor",
    "apply_ercot_ct_offer_surface",
    "apply_gas_st_netload_drag_floor",
    "apply_neiso_coldsnap_derate",
    "apply_netload_drag_floors",
    "apply_netload_reliability_floor",
    "apply_other_fossil_scoring",
    "apply_plant_emission_rates",
    "apply_plant_emission_rates_v2",
    "assemble_mc",
    "bins_to_fleet",
    "build_base_fleet",
    "build_caiso_offer_surface_conditional_markup",
    "build_dispatch_fleet",
    "build_ercot_faststart_pool_markup",
    "build_ercot_offer_midcurve_conditional_markup",
    "build_ercot_offer_surface_cleared_share_markup",
    "build_ercot_offer_surface_conditional_markup",
    "build_ercot_offer_surface_lowcurve_floorscoped_markdown",
    "build_ercot_offer_surface_lowcurve_markdown",
    "build_neiso_offer_surface_conditional_markup",
    "build_pjm_offer_midcurve_conditional_markup",
    "build_pjm_offer_surface_conditional_markup",
    "build_ramp_groups",
    "caiso_operating_reserve_mw",
    "calendar",
    "campd_ct_run_band_ratios",
    "campd_ct_run_lengths",
    "campd_tranche_fuel_frac",
    "cc_duct_burner_peak_mult",
    "cc_duct_peaking_pct",
    "cc_intermediate_plants",
    "cc_summer_capacity",
    "cc_summer_derate_ratio",
    "chp_btm_pct",
    "chp_class_netgen_mwh",
    "chp_pmin_cf",
    "class_cod_coverage",
    "classify_plant",
    "clear_where_unfloored",
    "coal_chp_overrides",
    "coal_summer_capacity",
    "coal_summer_derate_ratio",
    "coal_supply_class",
    "coal_sync_online_frac",
    "coal_takeorpay_share",
    "ct_deployment_floor_for_year",
    "ct_intermediate_plants",
    "ct_mustrun_floor_mwh_by_plant",
    "dataclass",
    "dual_fuel_plant_groups",
    "effective_cod",
    "eia860_costofservice_majority_plants",
    "eia860_regulated_plants",
    "eia860_selfcommit_scope_plants",
    "eia923_dominant_class_by_plant",
    "ensure_mechanism",
    "ercot_noncampd_availability_caps",
    "fleet_to_bins",
    "generators_to_fleet_arrays",
    "get_eford",
    "get_emission_rate",
    "get_iso_config",
    "get_nox_rate",
    "get_vom",
    "json",
    "load_as_reserve_withholding_mw",
    "load_as_thermal_withholding",
    "load_binned_fleet",
    "load_campd_bins",
    "load_campd_ramp_envelopes",
    "load_cod_map",
    "load_fleet_from_csv",
    "load_mothballed_but_operating",
    "load_or_synthesize_bins",
    "load_planned_additions",
    "load_plant_registry",
    "load_plant_tranche_config",
    "load_retired_within_window",
    "log_class_cod_coverage",
    "logger",
    "logging",
    "lru_cache",
    "mixed_fossil_plants",
    "monthly_online_mask",
    "np",
    "oil_primary_bin_plants",
    "oil_primary_ct_plants_from_eia860",
    "os",
    "partial_outage_derate_factors",
    "pd",
    "re",
    "reliability_deployment_floor_for_year",
    "retiree_availability_caps",
    "split_gas_tranches",
    "st_gas_intermediate_plants",
    "thermal_tranche_chp_steam_level",
    "thermal_tranche_online_frac",
    "thermal_tranche_overrides",
    "thermal_tranche_p25_level",
    "thermal_tranche_peaking",
    "unit_outage_derate_factors",
    "unit_outage_maxgen_derate_factors",
    "unit_outage_short_derate_factors",
    "unit_partial_outage_derate_factors",
)

# Every top-level name each new submodule defines (module loggers excluded);
# the package __init__ must resolve each to the submodule's own object.
MOVED_SURFACE: dict[str, tuple[str, ...]] = {
    "market_sim.data.fleet.models": ("_pkg_ns",),
    "market_sim.data.fleet.withholding": (
        "RAMP10_FRAC_BY_FUEL",
        "RAMP10_FRAC_BY_GROUP",
        "_AS_GAS_GROUPS",
        "_AS_MAX_GAP_HOURS",
        "_AS_MODEL_CALENDAR",
        "_AS_MODEL_INDEX",
        "_AS_PJM_GROUPS",
        "_AS_RESTYPE_TO_GROUPS",
        "_AS_THERMAL_GROUPS",
        "_AS_WITHHOLDING",
        "_AS_WITHHOLDING_DIR",
        "_CAISO_MORC_LOAD_FRAC",
        "_CAISO_MSSC_EXCLUDE_FUELS",
        "_CAISO_REG_UP_LOAD_FRAC",
        "_CLEAN_AS_UP_MW_COLS",
        "_COAL_SYNC_FORCE_ALL",
        "_clean_as_reserve_withholding_mw",
        "_dam_waterfill",
        "_ercot_dam_plant_hourly_apply",
        "_ramp10_capability",
        "_withdraw_top_of_merit",
        "caiso_operating_reserve_mw",
        "load_as_reserve_withholding_mw",
        "load_as_thermal_withholding",
    ),
    "market_sim.data.fleet.eia860": (
        "BIN_FORCED_DERATE_BY_YEAR",
        "BIN_GROUP_HR_DEFAULT",
        "BIN_GROUP_TO_FUEL",
        "BIN_STARTUP_COST_PER_MW",
        "CC_REGULAR_COMMITTED_PCT_BY_PLANT",
        "CHP_PMIN_CF_BY_PLANT",
        "CHP_SECTOR_CLASS_BY_PLANT",
        "COAL_BIN_MIN_DOWN_HOURS",
        "COAL_BIN_MIN_RUN_HOURS",
        "COAL_MUSTRUN_BY_PLANT",
        "COAL_PLANT_COMMISSION_YEAR",
        "OTHER_FOSSIL_CLASS",
        "OTHER_FOSSIL_MIN_DOMINANT_FRAC",
        "PETRA_NOVA_MIN_CF",
        "PETRA_NOVA_PARASITIC_PCT",
        "PETRA_NOVA_PLANT_CODE",
        "_BIN_KEY_COLUMNS",
        "_BIOMASS_ENERGY_SOURCES",
        "_CC_NAMEPLATE_GUARD_TOL",
        "_CC_PRIME_MOVERS",
        "_CHP_GROUP_FOR",
        "_CLEAN_FUEL_TO_ENERGY_SOURCE",
        "_COAL_ENERGY_SOURCES",
        "_COLUMN_ALIASES",
        "_COST_OF_SERVICE_ENTITY_TYPES",
        "_EIA860_GAS_GROUPS",
        "_EIA860_PLANT_GROUP_BY_FUEL",
        "_GAS_BIN_GROUPS",
        "_GAS_THERMAL_SCORING_CLASSES",
        "_NUCLEAR_ZONE_OVERRIDES",
        "_OIL_ENERGY_SOURCES",
        "_PLANNED_FIRM_STATUSES",
        "_assign_zones",
        "_assign_zones_proportional",
        "_binned_fleet_frame",
        "_cache_binned_fleet",
        "_cc_demonstrated_peaks",
        "_clean_fleet_to_normalized",
        "_correct_mixed_facility_steam_hr",
        "_dual_fuel_plant_groups",
        "_efficiency_bin",
        "_eia860_plant_sector",
        "_eia923_plant_class_totals",
        "_load_fleet_from_clean",
        "_load_fleet_from_parquet",
        "_map_fuel_type",
        "_normalize_columns",
        "_nuclear_zone_override",
        "_reconcile_cc_pmax_to_nameplate",
        "_record_oris",
        "_rows_to_generators",
        "_to_float",
        "_to_month",
        "_to_year",
        "_zone_for_index",
        "apply_other_fossil_scoring",
        "ct_mustrun_floor_mwh_by_plant",
        "dual_fuel_plant_groups",
        "eia860_costofservice_majority_plants",
        "eia860_regulated_plants",
        "eia860_selfcommit_scope_plants",
        "eia923_dominant_class_by_plant",
        "get_eford",
        "get_emission_rate",
        "get_nox_rate",
        "get_vom",
        "load_binned_fleet",
        "load_fleet_from_csv",
        "load_mothballed_but_operating",
        "load_planned_additions",
        "load_retired_within_window",
        "mixed_fossil_plants",
    ),
    "market_sim.data.fleet.campd_bins": (
        "CC_DUCT_BURNER_PEAK_MULT",
        "PLANT_EMISSION_RATES_PATH",
        "PLANT_TRANCHE_OVERRIDE_FIELDS",
        "_CAMPD_BINS_CACHE",
        "_COAL_SUMMER_TECH",
        "_COAL_SUPPLY_TO_CURVE",
        "_DEFAULT_HR_MULT_BY_GROUP",
        "_DEFAULT_TRANCHE_PCT_BY_GROUP",
        "_KG_PER_TONNE",
        "_OIL_PRIMARY_FUEL_CODES",
        "_OIL_PRIMARY_PRIME_MOVERS",
        "_OIL_PRIMARY_TECHNOLOGY",
        "_OIL_PRIMARY_UNIT_FUEL_CODES",
        "_RAMP_BUCKET_BY_GROUP",
        "_apply_forward_control_retrofits",
        "_fill_hr_multiplier",
        "_fill_plant_hr",
        "_load_plant_registry_cached",
        "_measured_plant_rate_map_v2",
        "_oil_primary_bin_plants",
        "_override_bin_class_from_eia923",
        "_plant_emission_rate_map",
        "_reconcile_cc_capacity",
        "apply_plant_emission_rates",
        "apply_plant_emission_rates_v2",
        "build_ramp_groups",
        "campd_ct_run_band_ratios",
        "campd_ct_run_lengths",
        "cc_duct_burner_peak_mult",
        "cc_duct_peaking_pct",
        "cc_intermediate_plants",
        "cc_summer_capacity",
        "cc_summer_derate_ratio",
        "coal_summer_capacity",
        "coal_summer_derate_ratio",
        "ct_intermediate_plants",
        "fleet_to_bins",
        "load_campd_bins",
        "load_campd_ramp_envelopes",
        "load_plant_registry",
        "load_plant_tranche_config",
        "oil_primary_bin_plants",
        "oil_primary_ct_plants_from_eia860",
        "st_gas_intermediate_plants",
        "thermal_tranche_chp_steam_level",
        "thermal_tranche_online_frac",
        "thermal_tranche_overrides",
        "thermal_tranche_p25_level",
        "thermal_tranche_peaking",
    ),
    "market_sim.data.fleet.arrays": (
        "CAISO_CHP_CC_STEAM_CREDIT_FACTOR",
        "CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR",
        "CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD",
        "CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD",
        "CAISO_EOR_TOPPING_FACTOR",
        "CAISO_EOR_TOPPING_PLANTS",
        "CHP_STEAM_CREDIT_HR_CORRECTION_ISOS",
        "COAL_SUMMER_MAX_CF",
        "_CC_SHOULDER_MONTHS",
        "_POF_DROP_GROUPS",
        "_SUMMER_CLASS_DERATE",
        "_SUMMER_MONTHS",
        "_SUMMER_WEFOR_SHARE",
        "_apply_outage_overlays",
        "_availability_matrix",
        "_compose_min_gen_floors",
        "_nuclear_monthly",
        "_thermal_outage",
        "generators_to_fleet_arrays",
    ),
    "market_sim.data.fleet.floors": (
        "_load_ercot_stgas_seasonal_drag",
        "apply_ct_netload_drag_floor",
        "apply_gas_st_netload_drag_floor",
        "apply_neiso_coldsnap_derate",
        "apply_netload_drag_floors",
        "apply_netload_reliability_floor",
    ),
    "market_sim.data.fleet.offer_surfaces": (
        "_CONDITIONAL_SURFACE_SPECS",
        "_CondSurfaceSpec",
        "_ERCOT_CLEARED_SHARE_CLASS_OF",
        "_ERCOT_CLEARED_SHARE_STEAM_CLASS_OF",
        "_ERCOT_MIDCURVE_CLASS_OF",
        "_LOWCURVE_ECON_SUFFIXES",
        "_PJM_MIDCURVE_SEGMENT_OF",
        "_conditional_surface_markup",
        "_load_condbinned_surface",
        "_load_ct_offer_surface",
        "_load_ercot_online_span_tables",
        "_lowcurve_row_family",
        "apply_ercot_ct_offer_surface",
        "build_caiso_offer_surface_conditional_markup",
        "build_ercot_faststart_pool_markup",
        "build_ercot_offer_midcurve_conditional_markup",
        "build_ercot_offer_surface_cleared_share_markup",
        "build_ercot_offer_surface_conditional_markup",
        "build_ercot_offer_surface_lowcurve_floorscoped_markdown",
        "build_ercot_offer_surface_lowcurve_markdown",
        "build_neiso_offer_surface_conditional_markup",
        "build_offer_surface_conditional_markup",
        "build_pjm_offer_midcurve_conditional_markup",
        "build_pjm_offer_surface_conditional_markup",
    ),
    "market_sim.data.fleet.legacy_bins": (
        "_AGGREGATABLE_FUELS",
        "_aggregate_with_predefined_bins",
        "_capacity_weighted",
        "aggregate_fleet",
        "aggregate_fleet_by_efficiency",
        "apply_coal_tranches",
        "assemble_mc",
        "campd_tranche_fuel_frac",
    ),
    "market_sim.data.fleet.assembly": (
        "_drop_biomass_units",
        "bins_to_fleet",
        "build_base_fleet",
        "build_dispatch_fleet",
        "load_or_synthesize_bins",
    ),
}

# Defined PHYSICALLY in the package __init__ (pickle identity, plan §1).
PHYSICAL_INIT_NAMES = ("Generator", "FleetArrays")
FROZEN_MODULE_PATH = "market_sim.data.fleet"

# Names owned by the frozen ``market_sim.data.fleet`` path (constants + clean
# seam + the two pickle-borne classes). Only Generator/FleetArrays are defined
# PHYSICALLY in the ``__init__`` (pickle identity, asserted separately via
# PHYSICAL_INIT_NAMES); the constants and clean-seam helpers live in the
# ``.models`` leaf and are re-imported into this namespace, so what is asserted
# below is namespace presence on the frozen path, not the defining module.
INIT_DEFINED = (
    "BA_CODE_TO_ISO",
    "BINNED_FLEET_COLUMNS",
    "EIA860_OPERABLE_VINTAGE",
    "EIA_860_CSV_COLUMNS",
    "EIA_860_MULTIFUEL_PARQUET_NAME",
    "EIA_860_PARQUET_NAME",
    "EIA_860_RETIRED_WINDOW_PARQUET_NAME",
    "FUEL_TYPE_MAP",
    "FUEL_TYPE_NAMES",
    "FleetArrays",
    "Generator",
    "ISO_TO_BA_CODE",
    "MIXED_FACILITY_STEAM_HR",
    "USE_CLEAN_ENV",
    "_USE_CLEAN_TRUTHY",
    "_clean_fleet_year",
    "_hour_to_month_index",
    "_read_clean",
    "_use_clean",
    "logger",
)

# Names fleet.py historically re-exported from its own module-level imports
# (facade passthroughs) -> their canonical defining homes.
PASSTHROUGHS: dict[str, tuple[str, ...]] = {
    "market_sim.data.chp": (
        "_chp_by_plant",
        "_correct_chp_steam_credit_hr",
        "chp_btm_pct",
        "chp_class_netgen_mwh",
        "chp_pmin_cf",
    ),
    "market_sim.data.coal": (
        "COAL_PLANT_SUPPLY",
        "_COAL_CHP_FLOOR_CAP_PCT",
        "_COAL_CHP_FLOOR_FACTOR",
        "_coal_class_for",
        "coal_chp_overrides",
        "coal_supply_class",
        "coal_sync_online_frac",
        "coal_takeorpay_share",
    ),
    "market_sim.data.offer_curves": (
        "CONDITIONAL_SURFACE_GROUPS",
        "_econ_curve_steps",
        "_econ_split_for_group",
        "_hr_override",
        "_offer_curve_for_group",
        "split_gas_tranches",
    ),
    "market_sim.config.constants": (
        "CAMPD_BINNING_ISOS",
        "CC_ECON_HR_OVERRIDE_DEFAULT",
        "CC_PEAK_HR_OVERRIDE_DEFAULT",
        "CHP_BTM_PCT_BY_SECTOR",
        "CHP_ST_BTM_PCT",
        "CO2_RATES",
        "COAL_MAX_CF_BY_PLANT",
        "EFORD",
        "FUEL_CO2_FACTOR_PER_MMBTU",
        "GAS_ST_ECON_HR_OVERRIDE_DEFAULT",
        "GAS_ST_PEAK_HR_OVERRIDE_DEFAULT",
        "HEAT_RATE_BINS",
        "HOURS_PER_YEAR",
        "MAINTENANCE_MONTHLY_SHAPE",
        "NOX_RATES",
        "NUCLEAR_DORMANT_UNTIL",
        "NUCLEAR_MONTHLY_CF",
        "NUCLEAR_MONTHLY_CF_BY_YEAR",
        "START_YEAR",
        "THERMAL_AVAILABILITY",
        "VOM",
    ),
    "market_sim.config.iso_configs": (
        "ISOConfig",
        "get_iso_config",
    ),
    "market_sim.config.paths": (
        "CAMPD_BINS_CSV",
        "EIA_860_DIR",
        "PROCESSED_DIR",
        "RAW_DATA_DIR",
        "active_eia860_dir",
    ),
    "market_sim.config.plant_taxonomy": (
        "BIOMASS_ENERGY_SOURCES",
        "COAL_SUPPLY_TO_CLASS",
        "OIL_ENERGY_SOURCES",
        "classify_plant",
    ),
    "market_sim.config.scenarios": ("ScenarioConfig",),
    "market_sim.data.cod_ramp": (
        "class_cod_coverage",
        "effective_cod",
        "load_cod_map",
        "log_class_cod_coverage",
        "monthly_online_mask",
    ),
    "market_sim.data.floor_mechanisms": (
        "MECH_CC_MUSTRUN_PER_PLANT",
        "MECH_CHP_STEAM",
        "MECH_COAL_MUSTRUN",
        "MECH_CT_DEPLOYMENT_OVERLAY",
        "MECH_CT_MUSTRUN_PER_PLANT",
        "MECH_CT_NETLOAD_DRAG",
        "MECH_NUCLEAR",
        "MECH_RELIABILITY_DEPLOYMENT_OVERLAY",
        "MECH_ST_GAS_MUSTRUN_PER_PLANT",
        "MECH_ST_NETLOAD_DRAG",
        "clear_where_unfloored",
        "ensure_mechanism",
    ),
    "market_sim.data.outages": (
        "ST_GAS_PEAKER_PLANTS",
        "ct_deployment_floor_for_year",
        "ercot_noncampd_availability_caps",
        "partial_outage_derate_factors",
        "reliability_deployment_floor_for_year",
        "retiree_availability_caps",
        "unit_outage_derate_factors",
        "unit_outage_maxgen_derate_factors",
        "unit_outage_short_derate_factors",
        "unit_partial_outage_derate_factors",
    ),
}


def _package():
    return importlib.import_module("market_sim.data.fleet")


class TestHistoricalSurface:
    def test_full_pre_split_namespace_resolves(self):
        pkg = _package()
        missing = [n for n in HISTORICAL_SURFACE if not hasattr(pkg, n)]
        assert not missing, (
            "fleet package lost historically-available names (breaking "
            f"src/scripts/tests importers): {missing}"
        )

    def test_init_defined_names_present(self):
        pkg = _package()
        missing = [n for n in INIT_DEFINED if not hasattr(pkg, n)]
        assert not missing, missing


class TestMovedSurface:
    def test_every_moved_name_is_the_home_object(self):
        pkg = _package()
        bad = []
        for home_path, names in MOVED_SURFACE.items():
            home = importlib.import_module(home_path)
            for n in names:
                if n == "_pkg_ns":
                    continue  # models-only helper, not re-exported
                if not hasattr(pkg, n):
                    bad.append(f"{n} missing from package")
                elif getattr(pkg, n) is not getattr(home, n):
                    bad.append(f"{n} is not {home_path}.{n}")
        assert not bad, "\n".join(bad)

    def test_passthroughs_are_the_canonical_objects(self):
        pkg = _package()
        bad = []
        for home_path, names in PASSTHROUGHS.items():
            home = importlib.import_module(home_path)
            for n in names:
                if not hasattr(pkg, n):
                    bad.append(f"{n} missing from package")
                elif getattr(pkg, n) is not getattr(home, n):
                    bad.append(f"{n} is not {home_path}.{n}")
        assert not bad, "\n".join(bad)


class TestPickleIdentity:
    def test_physical_init_names_pin_the_frozen_module_path(self):
        pkg = _package()
        bad = []
        for n in PHYSICAL_INIT_NAMES:
            obj = getattr(pkg, n)
            if obj.__module__ != FROZEN_MODULE_PATH:
                bad.append(f"{n}.__module__ == {obj.__module__!r}")
        assert not bad, (
            f"pickle-identity pins broken (expected {FROZEN_MODULE_PATH!r}): "
            + "; ".join(bad)
        )

    def test_unpickle_path_round_trips(self):
        pkg = _package()
        for n in PHYSICAL_INIT_NAMES:
            cls = getattr(pkg, n)
            again = getattr(importlib.import_module(cls.__module__), cls.__qualname__)
            assert again is cls, f"{n} does not round-trip via __module__"


class TestPatchTransparency:
    def test_string_patch_reaches_pkg_ns_resolver(self):
        """A mock.patch through the historical dotted path must be what
        package internals see through the call-time resolver (the census'd
        ``models._pkg_ns`` route: load_fleet_from_csv & co.)."""
        from market_sim.data.fleet.models import _pkg_ns

        with mock.patch("market_sim.data.fleet.load_fleet_from_csv") as spy:
            assert _pkg_ns().load_fleet_from_csv is spy
        restored = _package().load_fleet_from_csv
        home = importlib.import_module("market_sim.data.fleet.eia860")
        assert restored is home.load_fleet_from_csv

    def test_models_leaf_resolves_types_lazily(self):
        """The 3E leaf absorption: models.Generator/FleetArrays resolve to the
        package-defined (pickle-pinned) classes."""
        models = importlib.import_module("market_sim.data.fleet.models")
        pkg = _package()
        assert models.Generator is pkg.Generator
        assert models.FleetArrays is pkg.FleetArrays
