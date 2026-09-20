"""Generation fleet inventory and attributes (package).

Provides the :class:`Generator` model, its vectorized :class:`FleetArrays`
form, and loaders that build a per-ISO thermal fleet from EIA-860 / eGRID
CSV extracts.

Package split of the former ``data/fleet.py`` god-module (11,199 ln;
refactor-consolidation plan §5 item 8, 2026-07-23):

- :mod:`.models` — types leaf (absorbs 3E ``data/fleet_models.py``) and the
  :func:`~.models._pkg_ns` call-time patch-namespace resolver.
- :mod:`.withholding` — measured AS reserve withholding + ERCOT DAM overlays.
- :mod:`.eia860` — EIA-860/eGRID fleet loaders, EIA-923 class scoring,
  per-plant registries.
- :mod:`.campd_bins` — CAMPD per-plant binning, ramp groups, emission rates,
  thermal-tranche tables.
- :mod:`.arrays` — ``generators_to_fleet_arrays`` vectorization.
- :mod:`.floors` — net-load reliability / drag floors, cold-snap derates.
- :mod:`.offer_surfaces` — measured offer-surface markups/markdowns.
- :mod:`.legacy_bins` — legacy equal-width heat-rate bin aggregation +
  ``assemble_mc``.
- :mod:`.assembly` — ``bins_to_fleet`` / ``build_base_fleet`` /
  ``build_dispatch_fleet``.

Compatibility contract (the ``data/fuel`` package pattern): the package holds
the EXACT import path of the pre-split module, so ``from
market_sim.data.fleet import <name>``, ``monkeypatch.setattr /
mock.patch("market_sim.data.fleet.<name>", ...)`` and ``fleet.<name> = ...``
writes all land on THIS namespace, which re-exports the entire pre-split
surface (public names, script/test-imported privates, and the config/data
re-imports that lived in the old module namespace). Package internals resolve
the historically patched names through :func:`~.models._pkg_ns` at call time.
The re-export surface is pinned by ``tests/test_fleet_facade.py``.

Pickle identity (plan §1): the committed ``p2_state`` pickles resolve
:class:`Generator` and :class:`FleetArrays` by ``__module__ ==
"market_sim.data.fleet"``, so both classes are defined PHYSICALLY in this
``__init__`` — never re-exported from a submodule — asserted by
``tests/test_persisted_identity.py`` and ``tests/test_p2_state_smoke.py``.
"""

from __future__ import annotations

import calendar
import json
import logging
import os
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel

from market_sim.config.constants import (
    CAMPD_BINNING_ISOS,
    CC_ECON_HR_OVERRIDE_DEFAULT,
    CC_PEAK_HR_OVERRIDE_DEFAULT,
    CHP_BTM_PCT_BY_SECTOR,
    CHP_ST_BTM_PCT,  # noqa: F401 — re-exported; market_sim.data.chp imports from fleet
    CO2_RATES,
    COAL_MAX_CF_BY_PLANT,
    EFORD,
    FUEL_CO2_FACTOR_PER_MMBTU,
    GAS_ST_ECON_HR_OVERRIDE_DEFAULT,
    GAS_ST_PEAK_HR_OVERRIDE_DEFAULT,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    MAINTENANCE_MONTHLY_SHAPE,
    NOX_RATES,
    NUCLEAR_DORMANT_UNTIL,
    NUCLEAR_MONTHLY_CF,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
    START_YEAR,
    THERMAL_AVAILABILITY,
    VOM,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.paths import (
    CAMPD_BINS_CSV,
    EIA_860_DIR,  # noqa: F401 — re-exported; many modules import from fleet
    PROCESSED_DIR,
    RAW_DATA_DIR,
    active_eia860_dir,
)
from market_sim.config.plant_taxonomy import (
    BIOMASS_ENERGY_SOURCES,
    COAL_SUPPLY_TO_CLASS,
    OIL_ENERGY_SOURCES,
    classify_plant,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.floor_mechanisms import (
    MECH_CC_MUSTRUN_PER_PLANT,
    MECH_CHP_STEAM,
    MECH_COAL_MUSTRUN,
    MECH_CT_DEPLOYMENT_OVERLAY,
    MECH_CT_MUSTRUN_PER_PLANT,
    MECH_CT_NETLOAD_DRAG,
    MECH_NUCLEAR,
    MECH_RELIABILITY_DEPLOYMENT_OVERLAY,
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
    MECH_ST_NETLOAD_DRAG,
    clear_where_unfloored,
    ensure_mechanism,
)
from market_sim.data.cod_ramp import (
    class_cod_coverage,
    effective_cod,
    generator_online_mask,
    load_cod_map,
    load_unit_cod_map,
    log_class_cod_coverage,
    monthly_online_mask,
)
from market_sim.data.outages import (
    ST_GAS_PEAKER_PLANTS,
    ct_deployment_floor_for_year,
    ercot_noncampd_availability_caps,
    partial_outage_derate_factors,
    reliability_deployment_floor_for_year,
    retiree_availability_caps,
    unit_outage_derate_factors,
    unit_outage_maxgen_derate_factors,
    unit_outage_short_derate_factors,
    unit_partial_outage_derate_factors,
)

logger = logging.getLogger(__name__)
# Data-model leaf (models.py): the pre-split module-level constants and
# clean-seam helpers live in the package leaf so submodules import them
# without a module-level cycle; they remain part of THIS namespace (the
# pre-split surface).
from market_sim.data.fleet.models import (  # noqa: F401  (historical namespace re-export)
    BA_CODE_TO_ISO,
    BINNED_FLEET_COLUMNS,
    EIA860_OPERABLE_VINTAGE,
    EIA_860_CSV_COLUMNS,
    EIA_860_MULTIFUEL_PARQUET_NAME,
    EIA_860_PARQUET_NAME,
    EIA_860_RETIRED_WINDOW_PARQUET_NAME,
    FUEL_TYPE_MAP,
    FUEL_TYPE_NAMES,
    ISO_NERC_REGION_ADMISSION,
    ISO_TO_BA_CODE,
    ISO_TO_BA_CODES,
    MIXED_FACILITY_STEAM_HR,
    NWPP_BAS,
    USE_CLEAN_ENV,
    _USE_CLEAN_TRUTHY,
    _clean_fleet_year,
    _hour_to_month_index,
    _read_clean,
    _use_clean,
    ba_codes,
    footprint_plant_mask,
    operable_vintage_year,
)


class Generator(BaseModel):
    """Attributes of a single generating unit."""

    unit_id: str
    name: str
    zone: str
    fuel_type: str
    efficiency_bin: str = "default"
    pmax_mw: float
    pmin_mw: float = 0.0
    heat_rate: float = 0.0
    vom: float = 0.0
    emission_rate_co2: float = 0.0
    # Fraction of this unit's stack CO2 that its capture island removes: 0.0 on
    # every unabated unit (the default, so nothing that does not set it moves),
    # ``config.ccs_retrofit_capture_rate`` on a unit converted by the CCS
    # retrofit screen (``capacity_evolution/ccs.py::apply_ccs_retrofit``), and
    # ``config.ccs_capture_rate`` on a CCS unit built by the entry screen
    # (``capacity_evolution/new_entry.py``). It is a PHYSICAL property of the
    # unit, not a tunable (rule 24 [R-REGISTRY]): its value is always one of
    # those two already-registered ScenarioConfig fields, no residual can be
    # closed by it, and it adds no free parameter (rule 21 [R-DOF]).
    #
    # WHY IT EXISTS (capx D77). ``emission_rate_co2`` is written twice per
    # forecast year on a converted unit: ``ccs.py`` applies the capture at the
    # retrofit, and then ``campd_bins.apply_plant_emission_rates*`` -- which
    # runs EVERY year, downstream of evolution, from ``build_dispatch_fleet``
    # -- re-books the host plant's MEASURED CAMPD rate over it. The measured
    # rate is keyed on ``(plant_code, coarse fuel class)`` and
    # ``fuel_class("gas_cc_ccs") == "gas"``, so a converted unit still matched
    # its own uncaptured host rate and was silently restored to it, in the
    # dispatch fleet AND (the campd path concatenates rather than copies) in
    # the persistent fleet. This field is what lets the restoration book the
    # measured host rate and the capture TOGETHER -- one mechanism at one
    # composition point (rule 19 [R-ONE-MECH]) -- instead of the two writes
    # racing. Measured defect and repair:
    # docs/handoffs/FINDING-capx-d77-2026-09-06.md.
    ccs_capture_fraction: float = 0.0
    nox_rate: float = 0.0
    so2_rate: float = 0.0
    eford: float = 0.05
    online_year: int = 2000
    retirement_year: int | None = None
    # Commercial-operation / retirement *month* (1-12) within the online/
    # retirement year, from EIA-860 Operating Month / Planned Retirement Month.
    # Default 1 (online) / None (retire end-of-year) reproduce the all-year
    # annual screen; consumed by the COD ramp (config.cod_ramp_enabled) as the
    # fall-back when a generator's plant is absent from cod_ramp.load_cod_map.
    online_month: int = 1
    retirement_month: int | None = None
    is_must_run: bool = False
    # Provenance: True only on units injected by the leg-1 partial-plant exit
    # channel (eia860._partial_plant_exit_rows, stamped by
    # load_retired_within_window under ScenarioConfig.partial_plant_exit_carry;
    # miso-191, PREREG-miso191-binning-aware-exit-2026-08-30 §1-§2). Read by
    # exactly one consumer — fleet_to_bins' exit-cohort routing, which gives
    # these units their own date-scoped bins so the per-unit retirement
    # survives plant binning and the existing effective_cod seam times each
    # out at unit grain. Loader-stamped plumbing, not a config tunable (rule
    # 24): no residual can be closed by it and nothing else reads it.
    partial_exit_unit: bool = False
    # Provenance: True only on units injected by the mid-vintage-year
    # whole-plant exit channel (eia860._mid_vintage_exit_rows, stamped by
    # load_retired_within_window under ScenarioConfig.mid_vintage_exit_carry;
    # SPP-48). The exact sibling of partial_exit_unit above and read by the
    # exact same single consumer — fleet_to_bins' exit-cohort routing — for
    # the same reason: without a date-scoped bin, a plant-binned LP discards
    # the unit's own EIA-860 retirement and runs the plant past its real
    # death. Measured before this stamp existed: Oklaunion (plant 127, EIA
    # retirement 9/2020) came back online in ALL TWELVE months of 2020, three
    # of them after it had retired, which is a rule 17 [R-FLOOR-WINDOW]
    # violation by construction. Loader-stamped plumbing, not a config
    # tunable (rule 24 [R-REGISTRY]).
    mid_vintage_exit_unit: bool = False

    # CAMPD operational-bin attributes. Set only for generators built by
    # :func:`bins_to_fleet`; left at defaults for the legacy fleet. These
    # carry the per-bin commitment parameters and must-run accounting that
    # used to live in lookup-table constants.
    is_campd_bin: bool = False
    plant_group: str = ""  # CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP
    bin_label: str = ""  # human-readable bin id, e.g. H_CC1
    min_run_hours: int = 0  # minimum committed run length
    min_down_hours: int = 0  # minimum downtime between runs
    # The PLANT's unit physics, stamped by assembly on EVERY tranche row
    # (ercot-186, rule 18 [R-PHYSICS] grain repair). The two fields above are
    # the UC-COUPLING anchor tags and are carried by the committed anchor slice
    # ALONE — deliberately, so a bid tranche acquires no commitment coupling
    # ("min-run / min-down stay 0 (bid markup only, no new UC coupling)",
    # assembly.py) — which left every econ*/peak* row reading 0 and made any
    # rule-18 physics gate at bid-row grain VACUOUS in both directions. These
    # two carry the SAME assembled values at PLANT grain so a licensing gate on
    # a bid row can read the physics that row's plant actually has. They are
    # read-only provenance: no LP column, no FleetArrays field, no commitment
    # consumer. 0 on fleets whose bin sheet records no physics.
    plant_min_run_hours: int = 0  # the plant's min-run, on every tranche row
    plant_min_down_hours: int = 0  # the plant's min-down, on every tranche row
    startup_cost_per_mw: float = 0.0  # $/MW per start, for the bid markup
    must_run_pct: float = 0.0  # MR% of the bin's nameplate (CHP steam)
    bin_nameplate_mw: float = 0.0  # bin total nameplate, for MR reconstruction
    coal_supply: str = ""  # "lignite" (mine-mouth) or "prb" (rail);
    #                                 drives plant-specific coal fuel pricing
    plant_code: int = 0  # EIA plant code, when the tranche maps
    #                                 to a single physical plant; drives the
    #                                 F923 monthly fuel-cost lookup.
    state: str = ""  # USPS state code (EIA-860). Drives the
    #                                 fuel-cost resolver's state-level
    #                                 "nearby plant" fallback; "" for fleets
    #                                 (e.g. ERCOT bins) that do not set it.
    chp_grid_pmin_mw: float = 0.0  # grid-delivered steam-following floor (MW)
    #                                 forced on flat via FleetArrays.min_gen for
    #                                 CC_CHP cogens (config.chp_steam_following).
    chp_grid_pmin_on_frac: float = 1.0  # measured share of AVAILABLE hours the
    #                                 plant has a unit online (CEMS; the exact
    #                                 identity steam_level_cf / median_cf over
    #                                 the thermal-tranche artifact's own two
    #                                 committed columns). 1.0 — the default and
    #                                 the value every unit carries unless
    #                                 config.chp_steam_duty_window is armed —
    #                                 holds the floor all 8760 h, which is the
    #                                 pre-caiso-293 behaviour exactly. Below 1.0
    #                                 the floor is confined to the top
    #                                 on_frac x live-hours by the SHARED
    #                                 commitment-floor window series, the same
    #                                 construction coal_sync_online_frac and
    #                                 cc_mustrun_online_frac already use (rule
    #                                 17 [R-FLOOR-WINDOW]; caiso-293).
    coal_sync_pmin_mw: float = 0.0  # coal synchronization floor (MW) forced on
    #                                 flat via FleetArrays.min_gen for the
    #                                 _mustrun / _sync min-load tranches under
    #                                 config.coal_sync_srmc_tranche (step 3a).
    coal_sync_online_frac: float = 1.0  # measured share of the year the plant is
    #                                 synchronized (CEMS online_frac). Scales the
    #                                 step-3a forcing: ~1.0 (supercritical) holds
    #                                 the floor all 8760 h; a cycler is forced
    #                                 only in its top online_frac fraction of
    #                                 hours by system load (the rest stay Pmin=0).
    coal_min_config_pmin_mw: float = 0.0  # coal MINIMUM ONLINE CONFIGURATION
    #                                 floor (MW) forced on via FleetArrays.min_gen
    #                                 under config.ercot_coal_min_config_floor:
    #                                 the least MW the plant can hold with at
    #                                 least one unit synchronised, min_u
    #                                 MinLoad_u from EIA-860 (ercot128). Spread
    #                                 across the plant's tranches in fill order
    #                                 by assembly, so the clip to
    #                                 pmax x availability cannot collapse it onto
    #                                 one slice. Distinct from coal_sync_pmin_mw
    #                                 (step-3a synchronization): different
    #                                 driver, different level, separate
    #                                 mechanism id (rule 19).
    cc_mustrun_pmin_mw: float = 0.0  # gas local-reliability commitment floor
    #                                 (MW) forced on via FleetArrays.min_gen for
    #                                 a CC_REGULAR / CT_PEAKER committed tranche
    #                                 under config.cc_mustrun_per_plant — the
    #                                 tranche's own capacity (CEMS committed %).
    cc_mustrun_online_frac: float = 0.0  # measured share of the year the plant
    #                                 is synchronized (CEMS online_frac, gas
    #                                 rows of thermal_tranches_<ISO>.csv). The
    #                                 floor above binds only in the plant's top
    #                                 online_frac fraction of hours ranked by
    #                                 system load (its measured committed
    #                                 window); 0 disables the floor.
    hydro_min_flow_monthly_mw: tuple[float, ...] | None = None
    #                                 Conventional-hydro minimum-flow floor (MW)
    #                                 per calendar month (12 entries, index 0 =
    #                                 January), forced on via FleetArrays.min_gen
    #                                 under config.hydro_min_flow_floor: the
    #                                 plant's pro-rata share of the fleet's
    #                                 measured monthly Q95 sustained level
    #                                 (run-of-river inflow + FERC-licence minimum
    #                                 releases, which the energy-budget LP cannot
    #                                 represent). Month-constant BY DESIGN — a
    #                                 diurnal floor would pin the measured shape.
    #                                 None = no floor (data.hydro.
    #                                 build_hydro_fleet stamps it).
    hydro_ror_flat_monthly_mw: tuple[float, ...] | None = None
    #                                 Run-of-river flat dispatch level (MW) per
    #                                 calendar month (12 entries, index 0 =
    #                                 January) under config.hydro_ror_split: the
    #                                 plant's own measured monthly water spread
    #                                 flat, budget[g,m]/hours[m]. Applied as BOTH
    #                                 the availability cap and the min_gen floor
    #                                 (mechanism id MECH_HYDRO_ROR_FLAT), so the
    #                                 plant's dispatch is fixed — an RoR/canal
    #                                 plant's output follows inflow and cannot
    #                                 chase price. None = shapeable (data.hydro.
    #                                 build_hydro_fleet stamps it from the
    #                                 hydro-plant-modes classifier).
    fast_start_run_hours: float = 0.0  # CAMPD-measured median start-to-stop run
    #                                 length (h) for fast-start CT tranches under
    #                                 config.tranche_startup_measured_runs (v3):
    #                                 compute_monthly_markup caps the startup-
    #                                 amortization horizon at this measured value
    #                                 (P0 runs may only shorten it). 0 = v2
    #                                 behaviour (P0 run lengths only).
    offer_markup_hr: float = 0.0  # markup heat rate (MMBtu/MWh) ABOVE the
    #                                 tranche's measured physical basis —
    #                                 base_HR × max(0, band_mult − phys_mult),
    #                                 set by bins_to_fleet when
    #                                 config.gas_offer_net_revenue_margin is
    #                                 armed and the resolved offer band carries
    #                                 phys_* keys. Consumed by
    #                                 data.offer_curves.apply_gas_offer_margin
    #                                 (markup → fuel-invariant $/MWh margin at
    #                                 the ISO anchor). 0 = outside the
    #                                 mechanism (flag off / neutral band /
    #                                 non-gas tranche).
    offer_margin_anchor: float | None = None  # per-tranche margin anchor
    #                                 ($/MMBtu) overriding the ISO window
    #                                 anchor in apply_gas_offer_margin — set
    #                                 from the offer band's ``margin_anchor``
    #                                 key (ERCOT-118 EP rebasis: the year's
    #                                 EP-anchored delivered mean the rebased
    #                                 per-year multiplier was identified at).
    #                                 None = the config window anchor.


@dataclass
class FleetArrays:
    """Vectorized fleet attributes for dispatch computation.

    Per-generator scalar attributes are stored as ``(n_gen,)`` arrays;
    availability is stored as ``(n_gen, T)`` to allow hour-varying derates.
    """

    pmax: np.ndarray
    pmin: np.ndarray
    heat_rate: np.ndarray
    vom: np.ndarray
    emission_rate: np.ndarray
    nox_rate: np.ndarray
    so2_rate: np.ndarray
    zone_idx: np.ndarray
    fuel_type_idx: np.ndarray
    availability: np.ndarray
    unit_ids: list[str]
    efficiency_bin: np.ndarray
    # EIA plant code per generator (0 when the tranche is not pinned to
    # a single physical plant — e.g. the legacy aggregated fleet, WECC
    # imports, or a multi-plant CT_PEAKER bin). Used by the F923 monthly
    # fuel-cost resolver to look up plant-specific delivered prices.
    plant_code: np.ndarray

    # Optional ``(n_gen, T)`` hour-varying minimum generation (a hard dispatch
    # floor). When set, it replaces the scalar ``pmin`` lower bound in the
    # dispatch LP — used for the seasonal ST_GAS reliability must-run. ``None``
    # falls back to ``pmin`` broadcast across all hours.
    min_gen: np.ndarray | None = None

    # Optional ``(n_gen, T)`` int8 mechanism-id array parallel to ``min_gen``
    # (see data.floor_mechanisms): which injector supplied the *binding*
    # floor at each unit-hour, maximum-composition (the largest floor keeps
    # its id). Diagnostic metadata for the D-2 forced-energy attribution
    # (scripts/legitimacy_diagnostics.py); never read by the LP build.
    min_gen_mechanism: np.ndarray | None = None

    # Optional ``(n_gen,)`` object array of USPS state codes per generator,
    # for the fuel-cost resolver's state-level "nearby plant" fallback.
    # ``None`` (or empty strings) disables the state tier, leaving the zonal
    # fallback and per-fuel trajectory.
    state: np.ndarray | None = None

    # Optional ``(n_gen,)`` object array of model plant groups (COAL, CC_REGULAR,
    # CC_CHP, CT_PEAKER, CT_CHP, ST_GAS, ST_CHP). Set for the EIA-860 per-plant
    # fleets (non-ERCOT) so the dispatch frame can class each unit by its real
    # group (CHP vs merchant) rather than collapsing by fuel. ``None`` for
    # fleets that don't set it.
    plant_group: np.ndarray | None = None

    # Optional ``(n_gen,)`` 10-minute deliverable ramp capability (MW) per
    # generator — the upper bound on the upward operating reserve a unit can
    # provide (``R[g] <= ramp10[g]``) in the energy+reserve co-optimization
    # (rebuild step 3b; docs/multi-iso/pjm-reserve-ordc.md Phase 2). Derived
    # forward-reproducibly from the unit's class ramp rate
    # (:data:`RAMP10_FRAC_BY_GROUP`) times its capacity, so it regenerates for a
    # forecast year and responds to fleet changes. ``None`` for fleets/runs that
    # do not co-optimize reserves.
    ramp10: np.ndarray | None = None

    @property
    def n_gen(self) -> int:
        """Return the number of generators in the fleet."""
        return len(self.unit_ids)


# ---------------------------------------------------------------------------
# Submodule re-exports: the entire pre-split module surface (public names AND
# script/test-imported privates), in dependency order. Import order matters:
# everything above (constants, Generator, FleetArrays) must exist before the
# first submodule executes, because submodules import it back from this
# partially-initialized package.
# ---------------------------------------------------------------------------
from market_sim.data.fleet.withholding import (  # noqa: F401
    RAMP10_FRAC_BY_FUEL,
    RAMP10_FRAC_BY_GROUP,
    _AS_GAS_GROUPS,
    _AS_MAX_GAP_HOURS,
    _AS_MODEL_CALENDAR,
    _AS_MODEL_INDEX,
    _AS_PJM_GROUPS,
    _AS_RESTYPE_TO_GROUPS,
    _AS_THERMAL_GROUPS,
    _AS_WITHHOLDING,
    _AS_WITHHOLDING_DIR,
    _CAISO_MORC_LOAD_FRAC,
    _CAISO_MSSC_EXCLUDE_FUELS,
    _CAISO_REG_UP_LOAD_FRAC,
    _CLEAN_AS_UP_MW_COLS,
    _COAL_SYNC_FORCE_ALL,
    _clean_as_reserve_withholding_mw,
    _dam_waterfill,
    _ercot_dam_plant_hourly_apply,
    _ramp10_capability,
    _withdraw_top_of_merit,
    caiso_operating_reserve_mw,
    load_as_reserve_withholding_mw,
    load_as_thermal_withholding,
)
from market_sim.data.fleet.eia860 import (  # noqa: F401
    BIN_FORCED_DERATE_BY_YEAR,
    BIN_GROUP_HR_DEFAULT,
    BIN_GROUP_TO_FUEL,
    BIN_STARTUP_COST_PER_MW,
    CC_REGULAR_COMMITTED_PCT_BY_PLANT,
    CHP_PMIN_CF_BY_PLANT,
    CHP_SECTOR_CLASS_BY_PLANT,
    COAL_BIN_MIN_DOWN_HOURS,
    COAL_BIN_MIN_RUN_HOURS,
    COAL_MUSTRUN_BY_PLANT,
    COAL_PLANT_COMMISSION_YEAR,
    OTHER_FOSSIL_CLASS,
    OTHER_FOSSIL_MIN_DOMINANT_FRAC,
    PETRA_NOVA_MIN_CF,
    PETRA_NOVA_PARASITIC_PCT,
    PETRA_NOVA_PLANT_CODE,
    _BIN_KEY_COLUMNS,
    _BIOMASS_ENERGY_SOURCES,
    _CC_NAMEPLATE_GUARD_TOL,
    _CC_PRIME_MOVERS,
    _CHP_GROUP_FOR,
    _CLEAN_FUEL_TO_ENERGY_SOURCE,
    _COAL_ENERGY_SOURCES,
    _COLUMN_ALIASES,
    _COST_OF_SERVICE_ENTITY_TYPES,
    _EIA860_GAS_GROUPS,
    _EIA860_PLANT_GROUP_BY_FUEL,
    _GAS_BIN_GROUPS,
    _GAS_THERMAL_SCORING_CLASSES,
    _NUCLEAR_ZONE_OVERRIDES,
    _OIL_ENERGY_SOURCES,
    _PLANNED_FIRM_STATUSES,
    _assign_zones,
    _assign_zones_proportional,
    _binned_fleet_frame,
    _cache_binned_fleet,
    _cc_demonstrated_peaks,
    _clean_fleet_to_normalized,
    _correct_mixed_facility_steam_hr,
    _cc_steam_part_generators,
    _dual_fuel_plant_groups,
    _efficiency_bin,
    _eia860_plant_sector,
    _eia923_plant_class_totals,
    _load_fleet_from_clean,
    _load_fleet_from_parquet,
    _map_fuel_type,
    _normalize_columns,
    _nuclear_zone_override,
    _reconcile_cc_pmax_to_nameplate,
    _record_oris,
    _rows_to_generators,
    _to_float,
    _to_month,
    _to_year,
    _zone_for_index,
    apply_other_fossil_scoring,
    ct_mustrun_floor_mwh_by_plant,
    cc_steam_part_generators,
    dual_fuel_plant_groups,
    eia860_costofservice_majority_plants,
    eia860_plant_sectors,
    eia860_plant_states,
    eia860_regulated_plants,
    eia860_selfcommit_scope_plants,
    eia923_dominant_class_by_plant,
    get_eford,
    get_emission_rate,
    get_nox_rate,
    get_vom,
    load_binned_fleet,
    load_fleet_from_csv,
    load_mothballed_but_operating,
    load_planned_additions,
    load_procured_vre_additions,
    load_retired_within_window,
    mixed_fossil_plants,
)
from market_sim.data.fleet.campd_bins import (  # noqa: F401
    CC_DUCT_BURNER_PEAK_MULT,
    PLANT_EMISSION_RATES_PATH,
    PLANT_TRANCHE_OVERRIDE_FIELDS,
    _CAMPD_BINS_CACHE,
    _COAL_SUMMER_TECH,
    _COAL_SUPPLY_TO_CURVE,
    _DEFAULT_HR_MULT_BY_GROUP,
    _DEFAULT_TRANCHE_PCT_BY_GROUP,
    _KG_PER_TONNE,
    _OIL_PRIMARY_FUEL_CODES,
    _OIL_PRIMARY_PRIME_MOVERS,
    _OIL_PRIMARY_TECHNOLOGY,
    _OIL_PRIMARY_UNIT_FUEL_CODES,
    _RAMP_BUCKET_BY_GROUP,
    _apply_forward_control_retrofits,
    _fill_hr_multiplier,
    _fill_plant_hr,
    _load_plant_registry_cached,
    _measured_plant_rate_map_v2,
    _oil_primary_bin_plants,
    _override_bin_class_from_eia923,
    _plant_emission_rate_map,
    _reconcile_cc_capacity,
    _CHP_GROUPS,
    _chp_duty_curve,
    _chp_layup_cohort,
    _reserve_duty_cohort,
    apply_plant_emission_rates,
    apply_plant_emission_rates_v2,
    assert_thermal_tranche_coverage,
    build_ramp_groups,
    campd_ct_run_band_ratios,
    campd_ct_run_lengths,
    cc_duct_burner_peak_mult,
    cc_duct_peaking_pct,
    cc_intermediate_plants,
    cc_seasonal_capability_ratios,
    cc_summer_capacity,
    cc_summer_derate_ratio,
    cc_winter_capacity,
    summer_basis_measured_plants,
    coal_min_config,
    coal_summer_capacity,
    coal_summer_derate_ratio,
    ct_intermediate_plants,
    fleet_to_bins,
    load_campd_bins,
    load_campd_ramp_envelopes,
    load_plant_registry,
    load_plant_tranche_config,
    measured_chp_heat_rates,
    measured_coal_heat_rates,
    measured_st_heat_rates,
    measured_ct_heat_rates,
    oil_primary_bin_plants,
    oil_primary_ct_plants_from_eia860,
    st_gas_intermediate_plants,
    thermal_tranche_chp_steam_level,
    thermal_tranche_online_frac,
    thermal_tranche_oom_level,
    thermal_tranche_online_frac_by_year,
    thermal_tranche_overrides,
    thermal_tranche_p25_level,
    thermal_tranche_p25_measured_level,
    thermal_tranche_peaking,
)
from market_sim.data.fleet.arrays import (  # noqa: F401
    CAISO_CHP_CC_STEAM_CREDIT_FACTOR,
    _apply_outage_overlays,
    _availability_matrix,
    _compose_min_gen_floors,
    _nuclear_monthly,
    CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR,
    CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD,
    CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD,
    CAISO_EOR_TOPPING_FACTOR,
    CAISO_EOR_TOPPING_PLANTS,
    CHP_STEAM_CREDIT_HR_CORRECTION_ISOS,
    COAL_SUMMER_MAX_CF,
    _CC_SHOULDER_MONTHS,
    _POF_DROP_GROUPS,
    _SUMMER_CLASS_DERATE,
    _SUMMER_MONTHS,
    _SUMMER_WEFOR_SHARE,
    _thermal_outage,
    generators_to_fleet_arrays,
)
from market_sim.data.fleet.floors import (  # noqa: F401
    _load_ercot_stgas_seasonal_drag,
    apply_ct_netload_drag_floor,
    apply_gas_st_netload_drag_floor,
    apply_neiso_coldsnap_derate,
    apply_netload_drag_floors,
    apply_netload_reliability_floor,
)
from market_sim.data.fleet.offer_surfaces import (  # noqa: F401
    _CONDITIONAL_SURFACE_SPECS,
    _CondSurfaceSpec,
    _ERCOT_CLEARED_SHARE_CLASS_OF,
    build_offer_surface_conditional_markup,
    _ERCOT_CLEARED_SHARE_STEAM_CLASS_OF,
    _ERCOT_MIDCURVE_CLASS_OF,
    _LOWCURVE_ECON_SUFFIXES,
    _PJM_MIDCURVE_SEGMENT_OF,
    _conditional_surface_markup,
    _load_condbinned_surface,
    _load_ct_offer_surface,
    _load_ercot_online_span_tables,
    _lowcurve_row_family,
    apply_ercot_ct_offer_surface,
    build_caiso_offer_surface_conditional_markup,
    build_ercot_faststart_pool_markup,
    build_ercot_offer_midcurve_conditional_markup,
    build_ercot_offer_surface_cleared_share_markup,
    build_ercot_offer_surface_conditional_markup,
    build_ercot_offer_surface_lowcurve_floorscoped_markdown,
    build_ercot_offer_surface_lowcurve_markdown,
    build_ercot_offline_commit_target,
    build_neiso_offer_surface_conditional_markup,
    build_pjm_ct_measured_max_target,
    build_pjm_offer_midcurve_conditional_markup,
    build_pjm_offer_surface_conditional_markup,
)
from market_sim.data.fleet.legacy_bins import (  # noqa: F401
    _AGGREGATABLE_FUELS,
    _aggregate_with_predefined_bins,
    _capacity_weighted,
    aggregate_fleet,
    aggregate_fleet_by_efficiency,
    apply_coal_tranches,
    assemble_mc,
    campd_tranche_fuel_frac,
)
from market_sim.data.fleet.assembly import (  # noqa: F401
    _drop_biomass_units,
    bins_to_fleet,
    build_base_fleet,
    build_dispatch_fleet,
    load_or_synthesize_bins,
)

# Historical namespace passthroughs: the monolith bound these via its three
# mid-file imports (offer_curves / chp / coal — placed mid-file for the
# import-cycle ordering); scripts/tests import them FROM fleet, so the package
# keeps them on this namespace, now from their canonical homes.
from market_sim.data.chp import (  # noqa: F401  (historical namespace re-export)
    _chp_by_plant,
    _correct_chp_steam_credit_hr,
    chp_btm_pct,
    chp_class_netgen_mwh,
    chp_pmin_cf,
)
from market_sim.data.coal import (  # noqa: F401  (historical namespace re-export)
    _COAL_CHP_FLOOR_CAP_PCT,
    _COAL_CHP_FLOOR_FACTOR,
    COAL_PLANT_SUPPLY,
    _coal_class_for,
    coal_chp_overrides,
    coal_supply_class,
    coal_sync_online_frac,
    coal_takeorpay_share,
)
from market_sim.data.offer_curves import (  # noqa: F401  (historical namespace re-export)
    CONDITIONAL_SURFACE_GROUPS,
    _econ_curve_steps,
    _econ_split_for_group,
    _hr_override,
    _offer_curve_for_group,
    split_gas_tranches,
)
from market_sim.data.fleet import models as models  # noqa: F401
