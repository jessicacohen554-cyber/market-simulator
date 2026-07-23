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
    CT_ECON_HR_OVERRIDE_DEFAULT,
    CT_PEAK_HR_OVERRIDE_DEFAULT,
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
    load_cod_map,
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
    ISO_TO_BA_CODE,
    MIXED_FACILITY_STEAM_HR,
    USE_CLEAN_ENV,
    _USE_CLEAN_TRUTHY,
    _clean_fleet_year,
    _hour_to_month_index,
    _read_clean,
    _use_clean,
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

    # CAMPD operational-bin attributes. Set only for generators built by
    # :func:`bins_to_fleet`; left at defaults for the legacy fleet. These
    # carry the per-bin commitment parameters and must-run accounting that
    # used to live in lookup-table constants.
    is_campd_bin: bool = False
    plant_group: str = ""  # CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP
    bin_label: str = ""  # human-readable bin id, e.g. H_CC1
    min_run_hours: int = 0  # minimum committed run length
    min_down_hours: int = 0  # minimum downtime between runs
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
# data/clean consumption seam (opt-in)
# ---------------------------------------------------------------------------
# Opt-in switch that routes the fleet + AS-withholding reads through the curated
# ``data/clean`` tree (the frozen ``scripts.lib.clean_io.read_clean`` seam)
# instead of ``data/raw``. Default OFF: with the variable unset the model reads
# raw byte-for-byte as before. The clean tree is gitignored/derived, so
# regenerate it first:
#   python scripts/regenerate_clean.py fleet ancillary-services
# This is a parity/migration seam, not a behavior change — see
# ``tests/test_consume_fleet.py`` for the raw<->clean parity checks.
USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"
_USE_CLEAN_TRUTHY: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether reads should be sourced from ``data/clean`` (opt-in).

    Controlled by the :data:`USE_CLEAN_ENV` environment variable; any of
    ``1/true/yes/on`` (case-insensitive) turns the clean seam on. Unset/anything
    else keeps the default raw read path.
    """
    return os.environ.get(USE_CLEAN_ENV, "").strip().lower() in _USE_CLEAN_TRUTHY


def _read_clean(*args, **kwargs):
    """Lazy proxy to :func:`scripts.lib.clean_io.read_clean`.

    Imported lazily (and only on the opt-in clean path) because ``scripts`` is a
    repo-root package, not part of the installed ``market_sim`` distribution, so
    it must not be required for a normal raw-path import.
    """
    from scripts.lib import clean_io

    return clean_io.read_clean(*args, **kwargs)


def _clean_fleet_year(data_dir: Path) -> int:
    """Map an active EIA-860 vintage directory to its clean ``fleet`` partition.

    The clean ``fleet`` datatype is partitioned by EIA-860 vintage year
    (``data/clean/fleet/fleet_<year>.parquet``): a ``vintage_<year>/`` directory
    curates to ``year`` and the top-level snapshot curates to
    :data:`EIA860_OPERABLE_VINTAGE`. Resolving the active dir
    (:func:`paths.active_eia860_dir`, which honors a
    ``ScenarioConfig.eia860_vintage_year`` switch) to that year is what lets the
    clean fleet read preserve the EIA-860 vintage behavior of the raw loaders —
    selecting ``vintage_2023`` routes the clean read to ``fleet_2023``.
    """
    name = Path(data_dir).name
    if name.startswith("vintage_"):
        try:
            return int(name.split("_", 1)[1])
        except ValueError:
            pass
    return EIA860_OPERABLE_VINTAGE


# Location of the EIA-860 / eGRID CSV extracts. Re-exported from the central
# path registry (other data modules import EIA_860_DIR from fleet).

# Committed parquet of real EIA-860 generators for the seven wholesale
# markets, produced by ``scripts/data/process_eia860.py`` from the raw release.
EIA_860_PARQUET_NAME: str = "eia860_generators.parquet"

# Committed parquet of within-window plant exits (whole plants that retired
# mid-backcast and so are absent from the single recent operable vintage —
# e.g. Mystic, plant 1588, a ~1.4 GW CC retired mid-2024). Built by
# ``scripts/data/process_eia860.py --retired-window-from`` in the canonical fleet
# schema (plus month-precise online/retirement columns), with ``status`` = OP
# and the actual retirement carried in ``planned_retirement_*``. Injected into
# the BACKCAST fleet so the COD ramp can dispatch each through its real
# retirement month — the mirror of :func:`load_planned_additions` (forecast).
EIA_860_RETIRED_WINDOW_PARQUET_NAME: str = (
    "eia860_generator_retired_within_window.parquet"
)

# Committed parquet of the EIA-860 Multifuel schedule (operable units),
# produced by ``scripts/data/process_eia860.py``. Carries the multiple-energy-
# source fields ("Energy Source 2", "Multiple Fuels?", "Switch Between Oil
# and Natural Gas?", oil/gas capacity splits) that flag dual-fuel units.
EIA_860_MULTIFUEL_PARQUET_NAME: str = "eia860_multifuel_operable.parquet"

# Directory for derived, inspectable fleet outputs (the binned-fleet cache).
# Re-exported from the central path registry.

# Columns of the cached plant-level binned-fleet parquet, one row per
# physical generator with its loader-assigned efficiency bin and attributes.
BINNED_FLEET_COLUMNS: list[str] = [
    "plant_id",
    "plant_name",
    "fuel_type",
    "efficiency_bin",
    "zone",
    "pmax_mw",
    "pmin_mw",
    "heat_rate",
    "vom",
    "emission_rate_co2",
    "nox_rate",
    "eford",
    "online_year",
    "retirement_year",
]

# Canonical column order of the EIA-860 generator extract consumed by the
# fleet loader, produced by ``scripts/data/process_eia860.py``.
EIA_860_CSV_COLUMNS: list[str] = [
    "plant_id",
    "generator_id",
    "plant_name",
    "state",
    "balancing_authority_code",
    "technology",
    "energy_source",
    "prime_mover",
    "nameplate_capacity_mw",
    "net_summer_capacity_mw",
    "operating_year",
    "planned_retirement_year",
    "planned_retirement_month",
    "status",
    "heat_rate",
]

# EIA-930 balancing-authority code → ISO name, for the seven wholesale
# markets that have EIA-930 demand data.
BA_CODE_TO_ISO: dict[str, str] = {
    "ERCO": "ERCOT",
    "CISO": "CAISO",
    "PJM": "PJM",
    "MISO": "MISO",
    "NYIS": "NYISO",
    "ISNE": "NEISO",
}

# Inverse of BA_CODE_TO_ISO: EIA balancing-authority code keyed by ISO name.
ISO_TO_BA_CODE: dict[str, str] = {iso: ba for ba, iso in BA_CODE_TO_ISO.items()}

# Integer codes for fuel types, used to index into fuel-keyed arrays.
# Code 11 (previously reserved as a gap) is now oil; biomass takes the next
# free integer (15) after the prior maximum (gas_st = 14).
FUEL_TYPE_MAP: dict[str, int] = {
    "gas_cc": 0,
    "gas_ct": 1,
    "coal": 2,
    "nuclear": 3,
    "wind": 4,
    "solar": 5,
    "hydro": 6,
    "import": 7,
    "hydrogen_ct": 8,  # simple-cycle H2 turbine (peaker)
    "hydrogen_ccgt": 9,  # combined-cycle H2 turbine (mid-merit/baseload)
    "gas_cc_ccs": 10,  # gas CCGT with 90% post-combustion carbon capture
    "oil": 11,  # oil-fired peaker/steam (distillate + residual fuel oil)
    "geothermal": 12,  # enhanced geothermal systems (EGS)
    "offshore_wind": 13,  # offshore wind (fixed-bottom and floating)
    "gas_st": 14,  # legacy natural-gas steam boiler (conventional ST)
    "biomass": 15,  # biomass / wood / MSW / landfill-gas thermal steam
    "demand_response": 16,  # price-responsive DR supply block (NYISO SCR/EDRP):
    # a pseudo-generator that clears the energy balance at its strike price with
    # heat_rate=0 / emission_rate=0, so it carries no fuel/emission cost and is
    # excluded from generation-mix scoring (it is avoided load, not generation —
    # see results.export). Falls outside every reserve/AS/renewable/RPS fuel set,
    # so it is dispatch-only and never evolves. data.nyiso_demand_response.
}

# Inverse of FUEL_TYPE_MAP: fuel type name indexed by its integer code.
# Sized to the largest code so any gap in the code space yields an empty
# string rather than a misaligned name.
FUEL_TYPE_NAMES: list[str] = [""] * (max(FUEL_TYPE_MAP.values()) + 1)
for _name, _code in FUEL_TYPE_MAP.items():
    FUEL_TYPE_NAMES[_code] = _name


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

    # CAMPD operational-bin attributes. Set only for generators built by
    # :func:`bins_to_fleet`; left at defaults for the legacy fleet. These
    # carry the per-bin commitment parameters and must-run accounting that
    # used to live in lookup-table constants.
    is_campd_bin: bool = False
    plant_group: str = ""  # CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP
    bin_label: str = ""  # human-readable bin id, e.g. H_CC1
    min_run_hours: int = 0  # minimum committed run length
    min_down_hours: int = 0  # minimum downtime between runs
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


def _hour_to_month_index(hours: int) -> np.ndarray:
    """Return an ``(hours,)`` array mapping each hour to a 0-based month.

    Uses a representative non-leap year (2023) so the 8760-hour horizon
    maps cleanly onto the twelve calendar months.
    """
    month_hours: list[int] = []
    for month in range(1, 13):
        days = calendar.monthrange(2023, month)[1]
        month_hours.extend([month - 1] * (days * 24))
    return np.array(month_hours[:hours], dtype=int)


# Mixed CC+ST facility steam heat-rate corrections (MMBtu/MWh), keyed by EIA
# plant code. A facility that runs BOTH an efficient combined cycle and a legacy
# steam turbine reports ONE plant-level EIA-923 heat rate (fuel / net-gen
# blended across both prime movers); applied uniformly to every unit, that blend
# hands the inefficient steam units the CC's efficiency. Ravenswood (plant 2500,
# NYC, "CC+ST") is the material NYISO case: its ~1.7 GW steam units inherited the
# 8.8 plant blend, so 0.97x8.8 = 8.5 eff HR put the big NYC steam unit BELOW the
# top of an efficient CC's economic ramp (1.12x7.76 = 8.7) and it cleared AHEAD
# of idle NYC combined cycle on merit (the 2023 CC_REGULAR -4 TWh / ST_GAS
# +3.5 TWh merit inversion; nyiso 25).
#
# The corrected value (9.5) is the steam units' OWN heat rate recovered from the
# plant blend, not a free parameter: the 8.8 plant figure is generation-weighted
# across the efficient combined cycle (~7.5) and the steam turbine, so backing the
# CC out at plausible 2023 capacity factors (CC ~0.6, steam ~0.15) leaves the steam
# at ~9.5 MMBtu/MWh — modestly above the blend (steam is less efficient than the
# CC) yet below the smaller, older NYC peers (Arthur Kill 11.27, Astoria 11.95),
# as fits Ravenswood Unit 30 being a large, relatively efficient unit. 0.97x9.5 =
# 9.2 eff HR also clears the top of CC's economic ramp (8.7), so the merit order
# is restored (CC ahead of steam). A measured-data correction (CLAUDE.md rule #11
# — the plant blend was silently masking the inversion), forward-reproducible (it
# reflects unit physics, not a calendar/residual fit) and applied to the steam
# (ST_GAS) units ONLY, leaving the CC rows on their measured blend.
# CAISO AES Southland coastal once-through-cooling (OTC) steamers carry the SAME
# pathology via a different path: a colocated CCGT reports under the steam plant's
# ORIS code, so the EIA-923 plant-level heat rate blends the efficient CC into the
# legacy boiler even though CAMPD remaps the CCGT to its own EIA code (315 -> 62115,
# 335 -> 62116; see ST_GAS_PEAKER_PLANTS / campd.CAMPD_UNIT_PLANT_REMAP). The blend
# hands the steam units CC-like heat rates (Alamitos 315 -> 8.49, Huntington Beach
# 335 -> 7.33, both BELOW the CT_PEAKER fleet median ~10.07), so the model clears
# ~1.3 GW of OTC steam ahead of CA's simple-cycle peakers (the model ST_GAS over /
# CT_PEAKER under merit inversion). The recovered value is the measured heat rate of
# the IDENTICAL pure-steam sister plant Ormond Beach (350: 11.85 MMBtu/MWh, same AES
# Southland 1958-73 OTC boiler fleet, no colocated CC so its 923 blend is clean) —
# a measured physical analog (CLAUDE.md rule #11), not a residual fit. _correct_
# mixed_facility_steam_hr lifts ST_GAS units only and never lowers a clean unit, so
# Ormond itself is untouched. With HR ~11.85 these boilers sit above the peakers and
# clear only at scarcity, matching their ~0.2-0.6 TWh measured 2023 dispatch.
MIXED_FACILITY_STEAM_HR: dict[int, float] = {2500: 9.5, 315: 11.85, 335: 11.85}


# Vintage year of the operable EIA-860 snapshot behind the committed
# generators parquet: units online through this year are in the operable
# schedule. Proposed rows whose Effective Year is at or before it are
# stale (slipped projects with a past-dated COD), so the planned-additions
# loader and the renewables proposed-capacity augmentation both skip them
# rather than trust an effective date the snapshot has already overtaken.
# Bump this whenever process_eia860.py regenerates the parquets from a
# newer release. Source: EIA-860 2025 Early Release (eia8602025ER.zip,
# operating years through 2025).
EIA860_OPERABLE_VINTAGE: int = 2025


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
    dual_fuel_plant_groups,
    eia860_costofservice_majority_plants,
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
    apply_plant_emission_rates,
    apply_plant_emission_rates_v2,
    build_ramp_groups,
    campd_ct_run_band_ratios,
    campd_ct_run_lengths,
    cc_duct_burner_peak_mult,
    cc_duct_peaking_pct,
    cc_intermediate_plants,
    cc_summer_capacity,
    cc_summer_derate_ratio,
    coal_summer_capacity,
    coal_summer_derate_ratio,
    ct_intermediate_plants,
    fleet_to_bins,
    load_campd_bins,
    load_campd_ramp_envelopes,
    load_plant_registry,
    load_plant_tranche_config,
    oil_primary_bin_plants,
    oil_primary_ct_plants_from_eia860,
    st_gas_intermediate_plants,
    thermal_tranche_chp_steam_level,
    thermal_tranche_online_frac,
    thermal_tranche_overrides,
    thermal_tranche_p25_level,
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
    build_neiso_offer_surface_conditional_markup,
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
    split_coal_tranches,
    split_gas_tranches,
)
from market_sim.data.fleet import models as models  # noqa: F401
