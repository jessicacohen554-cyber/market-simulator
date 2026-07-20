"""Loaders for EIA-930 hourly demand and generation series.

Package split of the former ``data/eia_loader.py`` god-module (W-D2,
2026-07-20; refactor-consolidation plan §5 item 2):

- :mod:`.frames` — path constants, the non-leap hour calendar anchor, the
  clean-data consumption seam, and the per-BA ``<BA> hourly`` frame loaders.
- :mod:`.demand` — the six per-ISO hourly-demand readers, the
  :data:`DEMAND_LOADERS` registry (replacing the if/elif ladder), and the
  public ``load_demand`` / ``load_demand_meta``.
- :mod:`.zonal_shares` — zone-group crosswalks + measured hourly zonal shares.
- :mod:`.envelopes` — measured hydro / interchange / corridor / seam
  envelopes, hub prices, and net-interchange schedules.
- :mod:`.weather` — the unified daily-weather loader and hourly broadcasts.
- :mod:`.actuals` — the EIA-930 per-fuel benchmark actuals.

Compatibility contract: ``market_sim.data.eia_loader`` (the historical import
path used by src, ~45 scripts, and the tests) is a facade that aliases itself
to THIS package via ``sys.modules``, so ``from market_sim.data import
eia_loader`` returns this module object. This ``__init__`` therefore re-exports
the ENTIRE pre-split module surface — public functions, test/script-imported
privates, and the config re-imports that lived in the old module namespace —
and the package internals resolve the historically monkeypatched names
(``load_zonal_shares``, the per-ISO demand loaders, ``CALIBRATION_DIR``,
``EIA_HOURLY_DIR``) through this namespace at call time, so every existing
``mock.patch("market_sim.data.eia_loader.<name>")`` keeps intercepting them.
The re-export surface is pinned by ``tests/test_eia930_facade.py``.
"""

from __future__ import annotations

# Config names that were part of the old ``eia_loader`` module namespace
# (from-imports create module globals; tests patch CALIBRATION_DIR /
# EIA_HOURLY_DIR here and scripts read several of the others).
from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS, HOURS_PER_YEAR
from market_sim.config.interchange_config import CAISO_IMPORT_TRANCHE_HUB
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.paths import (
    CALIBRATION_DIR,
    EIA_930_DIR,
    EIA_HOURLY_DIR,
    ISO_TRANSMISSION_DIR,
    RAW_DIR,
    ZONE_DEMAND_DIR,
)

from .frames import (
    DATA_DIR,
    _CLEAN_FLAG_TRUE as _CLEAN_FLAG_TRUE,
    _DEMAND_META_FILE as _DEMAND_META_FILE,
    _DEMAND_PROFILES_FILE as _DEMAND_PROFILES_FILE,
    _EIA930_LONG_REGION_COLUMNS as _EIA930_LONG_REGION_COLUMNS,
    _ERCO_HOURLY_FILE as _ERCO_HOURLY_FILE,
    _GENERATION_PROFILES_FILE as _GENERATION_PROFILES_FILE,
    _HOURLY_FRAME_MAX_GAP as _HOURLY_FRAME_MAX_GAP,
    _ISO_LOCAL_TZ as _ISO_LOCAL_TZ,
    _ISO_TO_HOURLY_BA as _ISO_TO_HOURLY_BA,
    _META_FIELDS as _META_FIELDS,
    _MONTH_START_HOUR as _MONTH_START_HOUR,
    _clean_local_year_rows as _clean_local_year_rows,
    _eia_hourly_frame as _eia_hourly_frame,
    _eia_hourly_frame_filled as _eia_hourly_frame_filled,
    _eia_hourly_path as _eia_hourly_path,
    _ercot_hourly_frame as _ercot_hourly_frame,
    _fill_hourly_frame_from_long as _fill_hourly_frame_from_long,
    _filter_iso_year as _filter_iso_year,
    _read_clean_iso_year as _read_clean_iso_year,
    _read_clean_seam as _read_clean_seam,
    _use_clean as _use_clean,
    logger,
)
from .weather import (
    _DOWNSTATE_RAW as _DOWNSTATE_RAW,
    _LW_RAW as _LW_RAW,
    _broadcast_daily_to_hourly as _broadcast_daily_to_hourly,
    _load_weather_from_raw as _load_weather_from_raw,
    iso_zone_tmax,
    load_weather,
    neiso_load_weighted_temp,
)
from .zonal_shares import (
    _CAISO_TAC_MIN_HOURS as _CAISO_TAC_MIN_HOURS,
    _CAISO_TAC_ZONE_WEIGHTS as _CAISO_TAC_ZONE_WEIGHTS,
    _ERCOT_LOAD_ZONE_GROUPS as _ERCOT_LOAD_ZONE_GROUPS,
    _MISO_SUBBA_ZONE_GROUPS as _MISO_SUBBA_ZONE_GROUPS,
    _NEISO_LOAD_ZONE_GROUPS as _NEISO_LOAD_ZONE_GROUPS,
    _NYISO_LOAD_ZONE_GROUPS as _NYISO_LOAD_ZONE_GROUPS,
    _NYISO_ZONAL_LOAD_DIR as _NYISO_ZONAL_LOAD_DIR,
    _PJM_LOAD_ZONE_GROUPS as _PJM_LOAD_ZONE_GROUPS,
    _PJM_ZONAL_LOAD_DIR as _PJM_ZONAL_LOAD_DIR,
    _ZONAL_LOAD_DIR as _ZONAL_LOAD_DIR,
    _hourly_shares_from_groups as _hourly_shares_from_groups,
    _hours_of_year as _hours_of_year,
    _miso_utc_to_local_hoy as _miso_utc_to_local_hoy,
    _validate_zonal_shares as _validate_zonal_shares,
    _zonal_shares_from_raw as _zonal_shares_from_raw,
    load_zonal_shares,
)
from .envelopes import (
    _CAISO_IMPORT_TRANCHE_HUB as _CAISO_IMPORT_TRANCHE_HUB,
    _CAISO_INTERCHANGE_LAG_DST_H as _CAISO_INTERCHANGE_LAG_DST_H,
    _CAISO_INTERCHANGE_LAG_STD_H as _CAISO_INTERCHANGE_LAG_STD_H,
    _PJM_INTERCHANGE_DIR as _PJM_INTERCHANGE_DIR,
    _PJM_TIE_ZONE as _PJM_TIE_ZONE,
    _PJM_TIE_ZONE_DEFAULT as _PJM_TIE_ZONE_DEFAULT,
    _SCALAR_INTERCHANGE_ISOS as _SCALAR_INTERCHANGE_ISOS,
    _caiso_interchange_model_clock as _caiso_interchange_model_clock,
    _eia930_net_interchange as _eia930_net_interchange,
    _hydro_wat_month_hod as _hydro_wat_month_hod,
    caiso_solar_fraction,
    climatological_monthly_hydro,
    measured_corridor_flow_envelope,
    measured_firm_import_shape,
    measured_gas_floor_profile,
    measured_hydro_hourly_envelope,
    measured_import_hub_prices,
    measured_interchange_envelope,
    measured_intertie_hub_price_raw,
    measured_miso_pjm_border_prices,
    measured_monthly_hydro,
    measured_seam_import_envelope,
    neiso_net_interchange,
    nyiso_forward_net_import_monthly,
    nyiso_net_interchange,
    pjm_net_interchange,
    pjm_zonal_interchange,
    pjm_zonal_interchange_envelope,
)
from .actuals import (
    _CLEAN_GEN_FUEL_TO_BENCHMARK as _CLEAN_GEN_FUEL_TO_BENCHMARK,
    _EIA930_BENCHMARK_COLUMNS as _EIA930_BENCHMARK_COLUMNS,
    _STORAGE_BENCHMARK_SERIES as _STORAGE_BENCHMARK_SERIES,
    _STORAGE_MIN_COVERAGE_FRAC as _STORAGE_MIN_COVERAGE_FRAC,
    _clean_generation_by_fuel as _clean_generation_by_fuel,
    _pad_to_year as _pad_to_year,
    load_eia_hourly_benchmark,
    load_eia_hourly_renewable_gen,
    load_ercot_battery_gen,
    load_ercot_fossil_gen,
    load_ercot_nuclear_gen,
    load_ercot_other_gen,
    load_ercot_renewable_gen,
    load_generation_profiles,
)
from .demand import (
    DEMAND_LOADERS,
    DemandProfileNotRepairedError,
    _CAISO_DEMAND_CLOCK_LAG_H as _CAISO_DEMAND_CLOCK_LAG_H,
    _CAISO_DEMAND_CLOCK_REALIGN_END as _CAISO_DEMAND_CLOCK_REALIGN_END,
    _CLEAN_DEMAND_ISOS as _CLEAN_DEMAND_ISOS,
    _REGEN_DEMAND_PROFILE_CMD as _REGEN_DEMAND_PROFILE_CMD,
    _clean_system_demand as _clean_system_demand,
    _demand_profile_clean as _demand_profile_clean,
    _demand_profile_raw_pairs as _demand_profile_raw_pairs,
    _load_caiso_hourly_demand as _load_caiso_hourly_demand,
    _load_caiso_supply_consistent_demand as _load_caiso_supply_consistent_demand,
    _load_ercot_hourly as _load_ercot_hourly,
    _load_miso_hourly_demand as _load_miso_hourly_demand,
    _load_neiso_hourly_demand as _load_neiso_hourly_demand,
    _load_nyiso_hourly_demand as _load_nyiso_hourly_demand,
    _load_pjm_hourly_demand as _load_pjm_hourly_demand,
    load_demand,
    load_demand_meta,
)

__all__ = [
    # config re-imports (old module namespace parity)
    "CAISO_TAC_ZONE_WEIGHTS",
    "HOURS_PER_YEAR",
    "CAISO_IMPORT_TRANCHE_HUB",
    "ISOConfig",
    "get_iso_config",
    "CALIBRATION_DIR",
    "EIA_930_DIR",
    "EIA_HOURLY_DIR",
    "ISO_TRANSMISSION_DIR",
    "RAW_DIR",
    "ZONE_DEMAND_DIR",
    "logger",
    # frames
    "DATA_DIR",
    # weather
    "load_weather",
    "iso_zone_tmax",
    "neiso_load_weighted_temp",
    # zonal shares
    "load_zonal_shares",
    # envelopes
    "measured_monthly_hydro",
    "climatological_monthly_hydro",
    "measured_hydro_hourly_envelope",
    "measured_interchange_envelope",
    "measured_gas_floor_profile",
    "measured_import_hub_prices",
    "measured_intertie_hub_price_raw",
    "measured_miso_pjm_border_prices",
    "measured_corridor_flow_envelope",
    "measured_firm_import_shape",
    "caiso_solar_fraction",
    "measured_seam_import_envelope",
    "pjm_net_interchange",
    "pjm_zonal_interchange",
    "pjm_zonal_interchange_envelope",
    "nyiso_net_interchange",
    "nyiso_forward_net_import_monthly",
    "neiso_net_interchange",
    # actuals
    "load_ercot_renewable_gen",
    "load_eia_hourly_benchmark",
    "load_eia_hourly_renewable_gen",
    "load_ercot_fossil_gen",
    "load_ercot_nuclear_gen",
    "load_ercot_other_gen",
    "load_ercot_battery_gen",
    "load_generation_profiles",
    # demand
    "DEMAND_LOADERS",
    "DemandProfileNotRepairedError",
    "load_demand",
    "load_demand_meta",
]
