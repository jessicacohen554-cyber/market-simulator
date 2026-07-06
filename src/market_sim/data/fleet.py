"""Generation fleet inventory and attributes.

Provides the :class:`Generator` model, its vectorized :class:`FleetArrays`
form, and loaders that build a per-ISO thermal fleet from EIA-860 / eGRID
CSV extracts.
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
    CC_REGULAR_PEAKING_PCT_BY_PLANT,
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
    MECH_CHP_STEAM,
    MECH_COAL_MUSTRUN,
    MECH_CT_DEPLOYMENT_OVERLAY,
    MECH_CT_MUSTRUN_PER_PLANT,
    MECH_CT_NETLOAD_DRAG,
    MECH_NUCLEAR,
    MECH_RELIABILITY_DEPLOYMENT_OVERLAY,
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
    QUALIFYING_PLANT_GROUPS,
    ST_GAS_PEAKER_PLANTS,
    ct_deployment_floor_for_year,
    default_outages_path,
    outage_masks_for_year,
    partial_outage_derate_factors,
    reliability_deployment_floor_for_year,
    retiree_availability_caps,
    unit_outage_derate_factors,
)

logger = logging.getLogger(__name__)


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
# markets, produced by ``scripts/process_eia860.py`` from the raw release.
EIA_860_PARQUET_NAME: str = "eia860_generators.parquet"

# Committed parquet of within-window plant exits (whole plants that retired
# mid-backcast and so are absent from the single recent operable vintage —
# e.g. Mystic, plant 1588, a ~1.4 GW CC retired mid-2024). Built by
# ``scripts/process_eia860.py --retired-window-from`` in the canonical fleet
# schema (plus month-precise online/retirement columns), with ``status`` = OP
# and the actual retirement carried in ``planned_retirement_*``. Injected into
# the BACKCAST fleet so the COD ramp can dispatch each through its real
# retirement month — the mirror of :func:`load_planned_additions` (forecast).
EIA_860_RETIRED_WINDOW_PARQUET_NAME: str = (
    "eia860_generator_retired_within_window.parquet"
)

# Committed parquet of the EIA-860 Multifuel schedule (operable units),
# produced by ``scripts/process_eia860.py``. Carries the multiple-energy-
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
# fleet loader, produced by ``scripts/process_eia860.py``.
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
    fast_start_run_hours: float = 0.0  # CAMPD-measured median start-to-stop run
    #                                 length (h) for fast-start CT tranches under
    #                                 config.tranche_startup_measured_runs (v3):
    #                                 compute_monthly_markup caps the startup-
    #                                 amortization horizon at this measured value
    #                                 (P0 runs may only shorten it). 0 = v2
    #                                 behaviour (P0 run lengths only).


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


# Spring/autumn shoulder months (1-based) when thermal plants concentrate
# planned maintenance — the lull between the winter and summer demand peaks.
# Used to size each unit's annual planned-outage (POF) budget.
_CC_SHOULDER_MONTHS: frozenset[int] = frozenset({3, 4, 5, 10, 11})

# ERCOT summer peak months (1-based). Thermal units carry reduced outage
# here — planned outages are removed entirely and only a fraction of the
# forced-outage rate applies — so firm capacity is available for the load
# peak. The displaced outage energy is redistributed into the shoulder months
# only (not winter, which has its own peak), leaving each unit's
# annual-average availability unchanged. See generators_to_fleet_arrays.
_SUMMER_MONTHS: frozenset[int] = frozenset({6, 7, 8, 9})

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


# CAISO Kern-County enhanced-oil-recovery (EOR) topping cogens: a gas turbine
# whose exhaust raises injection steam for thermal EOR, electricity a byproduct.
# EIA-923 reports an artificially EFFICIENT plant heat rate (Kern River 5.80,
# Sycamore 5.99, Midway Sunset 5.09 MMBtu/MWh — BELOW an efficient combined
# cycle ~7) because the steam fuel is credited out of the electrical heat rate.
# The model then prices these as cheap baseload and runs the three at ~88% CF
# (3.7 TWh combined in 2024) versus their measured ~0.8 TWh (EIA-923 CF 0.05-
# 0.14, and DECLINING as CA EOR winds down) — a real CT_CHP over-dispatch. The
# physically-correct dispatch basis is the POWER-ONLY heat rate: charge ALL the
# fuel to electricity (no steam credit), which for a topping cycle is the
# simple-cycle gas-turbine heat rate ~1.8x the steam-credited blend — landing
# these units at ~9-11 MMBtu/MWh, the CT_PEAKER simple-cycle band where their
# power island physically sits. CAISO_EOR_TOPPING_FACTOR is the steam-credit
# ratio (forward-derivable turbine physics, responds to changed gas/steam
# conditions — admissible under CLAUDE.md #11/#12, the same measured-physics HR
# correction as MIXED_FACILITY_STEAM_HR, NOT a residual fit). Applied to the
# CT_CHP rows of these plants only, and only when it RAISES the heat rate.
CAISO_EOR_TOPPING_PLANTS: frozenset[int] = frozenset({10496, 50134, 52169})
CAISO_EOR_TOPPING_FACTOR: float = 1.8

# Generalized steam-credit HR correction for ALL CAISO CHP gas turbines, not
# just the three big EOR plants.  Every CHP simple-cycle CT reports a steam-
# credited EIA-923/CAMPD heat rate because total fuel includes steam-host
# thermal energy.  No simple-cycle GT achieves HR < 8.0 MMBtu/MWh on a
# power-only basis — the sub-8 values are artifacts of the CHP accounting.
# The same 1.8× topping factor used for EOR applies: all CT_CHP plants are
# physically simple-cycle turbines with similar thermodynamics; the correction
# lands them at 9–11 MMBtu/MWh regardless of the steam host type (oilfield,
# refinery, hospital, campus).  Applied only when it RAISES the heat rate.
CAISO_CHP_CT_STEAM_CREDIT_HR_THRESHOLD: float = 8.0

# CC_CHP plants also carry a steam credit, but smaller because the combined-
# cycle steam turbine is part of the power conversion — only ADDITIONAL process-
# steam extraction inflates efficiency.  A CC_CHP with reported HR < 6.0 is
# below even the most efficient gas-CC class (h_class = 6.3), confirming steam
# credit.  A 1.15× factor brings these into the 6.3–6.9 range (h_class to
# f_class); a floor of 6.3 prevents under-correction of heavily credited units.
CAISO_CHP_CC_STEAM_CREDIT_HR_THRESHOLD: float = 6.0
CAISO_CHP_CC_STEAM_CREDIT_FACTOR: float = 1.15
CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR: float = 6.3

# Fraction of a unit's WEFOR (forced-outage rate) that applies during the
# summer peak; the remaining (1 - share) is redistributed into the shoulder
# months. Winter keeps the flat WEFOR.
_SUMMER_WEFOR_SHARE: float = 0.30

# Additional summer (Jun-Sep) capacity derate by plant group, modeling the
# ambient-temperature output loss gas turbines suffer in the heat (worse for
# simple-cycle CTs than combined-cycle). Applied on top of the age-based
# availability for these classes only; coal and gas steam are unaffected.
_SUMMER_CLASS_DERATE: dict[str, float] = {
    "CC_REGULAR": 0.10,
    "CC_CHP": 0.10,
    "CT_PEAKER": 0.125,
    "CT_CHP": 0.125,
}

# Non-coal thermal classes whose statistical planned-outage factor (POF) is
# dropped in the historic backcast (gated on config.coal_drop_pof): their
# planned outages now come from the CAMPD overlay + the unit-level derate, so
# the shoulder-month POF would double-count. Combustion turbines (CT_PEAKER /
# CT_CHP) keep POF — they have no historic overlay coverage and are excluded
# from the unit derate.
_POF_DROP_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
)

# Per-plant coal sustained-output ceilings now live in
# constants.COAL_MAX_CF_BY_PLANT (re-derived from CAMPD outage-adjusted
# availability physics, not observed output — see
# scripts/derive_coal_max_cf.py). The year-specific (6179, 2025) override that
# used to sit here was deleted outright: a single confirmed-unit-outage year
# has no forward analogue, and the historic-outage overlay already zeros the
# actual outage hours for backcast runs.
# Summer-only (Jun-Sep) ceilings: an ambient/derate cap that only binds in the
# heat (the unit runs higher the rest of the year).
COAL_SUMMER_MAX_CF: dict[int, float] = {
    7030: 0.87,  # Major Oak — ~13% summer derate
}


def _thermal_outage(category: str, age: float) -> tuple[float, float, float]:
    """Return ``(POF, WEFOR, derate)`` for a thermal unit's age.

    ``category`` is the plant group (e.g. ``CC_REGULAR``, ``ST_GAS``,
    ``COAL``). POF is flat; WEFOR and the weather/performance derate are a
    base plus a linear escalation per year of age past an onset year. The
    three are additive — availability is ``1 - WEFOR - derate`` flat
    year-round, less ``POF`` in the shoulder months.
    """
    pof, w_base, w_rate, w_onset, d_base, d_rate, d_onset = THERMAL_AVAILABILITY[
        category
    ]
    wefor = w_base + max(0.0, age - w_onset) * w_rate
    derate = d_base + max(0.0, age - d_onset) * d_rate
    return pof, wefor, derate


# Dispatchable thermal plant groups that clear upward ancillary service and
# can therefore withhold energy when they do (gas CC/CT/ST + coal, incl. their
# CHP variants). Storage, renewables, nuclear and hydro are excluded from the
# AS-reserve-withholding pool.
_AS_THERMAL_GROUPS: frozenset[str] = frozenset(
    {
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
        "COAL",
    }
)

# AS-withholding pool: gas thermal only. Baseload coal is self-committed and
# runs flat for energy, carrying little upward AS in ERCOT (reserve sits on
# part-loaded gas headroom, peakers and — increasingly — storage/load), so it
# is excluded from the withdrawal so the probe does not strand baseload.
_AS_GAS_GROUPS: frozenset[str] = _AS_THERMAL_GROUPS - {"COAL"}

# PJM AS-withholding pool: gas thermal + flexible oil (steam/CT). PJM's Primary
# Reserve sits on synchronized, part-loaded thermal headroom; the flexible oil
# steam/CT fleet carries the same quick-start reserve as gas. Coal and nuclear
# (baseload, self-committed, run flat) hold little upward reserve and are
# excluded, mirroring the ERCOT gas-only pool.
_AS_PJM_GROUPS: frozenset[str] = _AS_GAS_GROUPS | {"oil"}

# Per-ISO reserve-withholding configuration: (raw-data dir, file prefix,
# withdrawal pool of plant_groups). The measured system-wide hourly reserve
# held out of energy sits in ``<dir>/<prefix>_<year>_as_up_mw.parquet`` on the
# non-leap 8760-hour clock; built by scripts/build_{ercot,pjm}_as_withholding.
_AS_WITHHOLDING: dict[str, tuple[Path, str, frozenset[str]]] = {
    "ERCOT": (RAW_DATA_DIR / "ercot-AS", "ercot", _AS_GAS_GROUPS),
    "PJM": (RAW_DATA_DIR / "PJM-AS", "pjm", _AS_PJM_GROUPS),
}

# Back-compat alias (ERCOT default location; used by the per-type loader).
_AS_WITHHOLDING_DIR = _AS_WITHHOLDING["ERCOT"][0]

# Map each per-resource-type AS column (from the 60-Day DAM Gen Resource Data,
# aggregated by ERCOT Resource Type) to the fleet plant_groups that share it.
# Storage and load AS are not here: they do not withhold *thermal* energy.
_AS_RESTYPE_TO_GROUPS: dict[str, frozenset[str]] = {
    "gas_cc": frozenset({"CC_REGULAR", "CC_CHP"}),
    "gas_ct": frozenset({"CT_PEAKER", "CT_CHP"}),
    "gas_st": frozenset({"ST_GAS", "ST_CHP"}),
    "coal": frozenset({"COAL"}),
}

# CAISO formula-based upward operating-reserve requirement (used by the
# default-off ``as_reserve_formula`` scaffold until OASIS cleared-AS data
# (AS_REQ/AS_RESULTS) can be pulled — outbound network is blocked in the remote
# env). R(t) = max(MSSC, MORC_LOAD_FRAC*load) + REG_UP_LOAD_FRAC*load, a
# published-standard WECC requirement carrying no fitted constants:
#   - contingency reserve = WECC MORC: the greater of the most-severe single
#     contingency (the largest single online unit nameplate) or 5% of
#     hydro-served + 7% of thermal-served load (~6.7% of load for CA's mix);
#   - regulation-up ~= 1% of load (CAISO Reg ~300-500 MW on 25-40 GW).
# Reg-Down is a downward product (it withholds no upward energy offer), excluded.
_CAISO_MORC_LOAD_FRAC = 0.067
_CAISO_REG_UP_LOAD_FRAC = 0.01

# The WECC most-severe single contingency (MSSC) is the largest single
# synchronous unit (for CAISO a Diablo Canyon unit, ~1.1 GW). Imports are
# aggregate tranches and wind/solar are many small inverters, so neither is a
# credible single-unit contingency; both are excluded when sizing the MSSC.
_CAISO_MSSC_EXCLUDE_FUELS: frozenset[str] = frozenset({"import", "wind", "solar"})


# Clean ``ancillary-services`` cleared-MW columns that make up the *upward*
# reserve held out of energy (Reg-Down is a downward product — it removes no
# upward energy offer — and is excluded, exactly as the raw withholding builders
# do). Their sum reproduces the raw ``as_up_mw`` series for ERCOT.
_CLEAN_AS_UP_MW_COLS: tuple[str, ...] = (
    "reg_up_mw",
    "spin_mw",
    "nonspin_mw",
    "supp_30min_mw",
)

# The fixed non-leap 8760-hour model calendar (representative year 2023), shared
# with :mod:`scripts.build_ercot_as_withholding`. Clean AS rows (UTC, with a
# wall-clock ``interval_start_local``) are folded onto this (month, day, hour)
# grid so the reconstructed series lands on the same clock as the fleet.
_AS_MODEL_CALENDAR = pd.date_range("2023-01-01", periods=8760, freq="h")
_AS_MODEL_INDEX = pd.MultiIndex.from_arrays(
    [_AS_MODEL_CALENDAR.month, _AS_MODEL_CALENDAR.day, _AS_MODEL_CALENDAR.hour],
    names=["month", "day", "hour"],
)
# Largest hole (hours) interpolated when placing a series on the 8760-hour clock
# (the DST spring-forward gap is 1h); bigger holes are partial-year coverage and
# are zero-filled rather than interpolated. Mirrors build_ercot_as_withholding.
_AS_MAX_GAP_HOURS = 24


def _clean_as_reserve_withholding_mw(
    year: int, hours: int, iso: str, market: str = "DAM"
) -> np.ndarray | None:
    """Reconstruct ``iso``'s hourly upward-AS withholding MW from data/clean.

    Reads the curated AS clearing table
    (``read_clean("ancillary-services", iso=iso, market=market, year=year)``),
    sums the system-wide (``zone == "SYSTEM"``) upward cleared-MW products
    (:data:`_CLEAN_AS_UP_MW_COLS`) and folds them onto the fleet's non-leap
    8760-hour clock by the local wall-clock ``(month, day, hour)`` — the same
    reduction :mod:`scripts.build_ercot_as_withholding` applies to the raw
    cleared-DAM-AS reports, so for ERCOT this reproduces the raw ``as_up_mw``
    series exactly (see ``tests/test_consume_fleet.py``). Returns ``None`` when
    the clean partition is absent or carries no cleared MW (the feature then
    no-ops, matching the raw "missing parquet -> None" behavior).

    NOTE: this is faithful for ERCOT (its raw withholding *is* the cleared DAM
    up-AS). PJM's raw withholding is a different quantity (the RT Primary Reserve
    requirement, which the clean AS schema intentionally does not carry), so the
    clean reconstruction is not a like-for-like substitute there — surfacing the
    PJM Primary Reserve through the clean seam would need an AS-schema contract
    change (raise one rather than editing the frozen YAML).
    """
    try:
        df = _read_clean("ancillary-services", iso=iso, market=market, year=year)
    except FileNotFoundError:
        logger.warning(
            "as_reserve_withholding(clean) on but no clean AS partition for "
            "%s %s %d; withholding skipped",
            iso,
            market,
            year,
        )
        return None
    if "zone" in df.columns:
        df = df[df["zone"].astype("string").str.strip() == "SYSTEM"]
    present = [c for c in _CLEAN_AS_UP_MW_COLS if c in df.columns]
    if df.empty or not present:
        return None
    up = df[present].sum(axis=1, min_count=1)
    covered = df.loc[df[present].notna().any(axis=1)].copy()
    if covered.empty:
        return None

    local = pd.to_datetime(covered["interval_start_local"])
    work = pd.DataFrame({"ts": local, "mw": up.loc[covered.index].to_numpy(float)})
    keep = (work["ts"].dt.year == year) & ~(
        (work["ts"].dt.month == 2) & (work["ts"].dt.day == 29)
    )
    work = work[keep]
    if work.empty:
        return None
    grouped = work.groupby(
        [work["ts"].dt.month, work["ts"].dt.day, work["ts"].dt.hour]
    )["mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    aligned = grouped.reindex(_AS_MODEL_INDEX)
    missing = int(aligned.isna().sum())
    if 0 < missing <= _AS_MAX_GAP_HOURS:
        aligned = aligned.interpolate(limit_direction="both")
    # A larger hole is partial-year coverage; leave it as 0 (no fabricated
    # reserve) so callers using the covered hours still get exact values.
    series = aligned.fillna(0.0).to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(hours - len(series))])
    return series[:hours]


@lru_cache(maxsize=8)
def load_as_reserve_withholding_mw(
    year: int, hours: int, iso: str = "ERCOT"
) -> np.ndarray | None:
    """Load ``iso``'s hourly system-wide reserve-withholding MW for ``year``.

    Returns the ``(hours,)`` reserve-held-out-of-energy MW series written by
    :mod:`scripts.build_ercot_as_withholding` (ERCOT: cleared DAM up-AS) or
    :mod:`scripts.build_pjm_as_withholding` (PJM: the RT Primary Reserve
    requirement), or ``None`` when the parquet is absent (the feature then
    silently no-ops, like a backcast year with no outage windows). The file
    sits on the same non-leap 8760-hour clock as the fleet, so it is returned
    as-is when ``hours == 8760``; other horizons take the leading ``hours``
    values.

    When the clean seam is on (:func:`_use_clean`), the series is instead
    reconstructed from the curated ``ancillary-services`` clearing table
    (:func:`_clean_as_reserve_withholding_mw`) — for ERCOT this matches the raw
    ``as_up_mw`` series exactly.
    """
    if _use_clean():
        return _clean_as_reserve_withholding_mw(year, hours, (iso or "ERCOT").upper())
    spec = _AS_WITHHOLDING.get((iso or "ERCOT").upper())
    if spec is None:
        return None
    as_dir, prefix, _ = spec
    path = as_dir / f"{prefix}_{year}_as_up_mw.parquet"
    if not path.exists():
        logger.warning(
            "as_reserve_withholding on but %s is missing; AS withholding "
            "skipped for %d",
            path,
            year,
        )
        return None
    series = pd.read_parquet(path)["as_up_mw"].to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(hours - len(series))])
    return series[:hours]


def load_as_thermal_withholding(year: int, hours: int) -> dict[str, np.ndarray] | None:
    """Load ERCOT's measured per-thermal-class hourly AS-up MW for ``year``.

    Reads ``ercot_<year>_as_by_restype_hourly.parquet`` — the per-resource
    60-Day DAM AS awards aggregated by ERCOT Resource Type (RegUp + RRS +
    ECRS; offline Non-Spin and the storage/load share are excluded, as those
    do not withhold *thermal* energy). Returns ``{restype_col: (hours,) MW}``
    for the thermal columns present (``gas_cc``/``gas_ct``/``gas_st``/
    ``coal``), or ``None`` when the file is absent (caller then falls back to
    the system-total upper bound). Same non-leap 8760-hour clock as the fleet.
    """
    path = _AS_WITHHOLDING_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    out: dict[str, np.ndarray] = {}
    for col in _AS_RESTYPE_TO_GROUPS:
        if col not in df.columns:
            continue
        series = df[col].to_numpy(dtype=float)
        if len(series) < hours:
            series = np.concatenate([series, np.zeros(hours - len(series))])
        out[col] = series[:hours]
    return out or None


def caiso_operating_reserve_mw(
    load_shape: np.ndarray, mssc_mw: float, hours: int
) -> np.ndarray:
    """Formula-based CAISO upward operating-reserve requirement (MW/hour).

    ``R(t) = max(MSSC, 0.067*load(t)) + 0.01*load(t)`` — a published-standard
    WECC requirement carrying no fitted constants:

    * **Contingency reserve** is the WECC Minimum Operating Reliability Criterion
      (MORC): the greater of the most-severe single contingency (``mssc_mw``, the
      largest single online unit nameplate — ~1,150 MW for a Diablo Canyon unit)
      or 5% of hydro-served + 7% of thermal-served load (~6.7% of load for
      California's generation mix; :data:`_CAISO_MORC_LOAD_FRAC`).
    * **Regulation-up** is ~1% of load (CAISO Reg ~300-500 MW on 25-40 GW of
      load; :data:`_CAISO_REG_UP_LOAD_FRAC`).

    Reg-Down is a downward product — it withholds no upward energy offer — and is
    excluded. ``load_shape`` is the hourly system load (MW) on the fleet's clock;
    a shorter series is zero-padded and a longer one truncated to ``hours``. This
    is the default-off scaffold to be replaced by measured OASIS AS_REQ/
    AS_RESULTS MW once the remote-env outbound-network block is lifted.
    """
    load = np.asarray(load_shape, dtype=float)
    if load.shape[0] < hours:
        load = np.concatenate([load, np.zeros(hours - load.shape[0])])
    load = load[:hours]
    contingency = np.maximum(float(mssc_mw), _CAISO_MORC_LOAD_FRAC * load)
    regulation = _CAISO_REG_UP_LOAD_FRAC * load
    return contingency + regulation


def _withdraw_top_of_merit(
    availability: np.ndarray,
    pmax: np.ndarray,
    heat_rate: np.ndarray,
    pool: np.ndarray,
    as_series: np.ndarray,
) -> tuple[float, float]:
    """Withdraw ``as_series`` MW/hour from ``pool``'s top-of-merit headroom.

    Removes the hourly reserve from the highest-heat-rate (most expensive,
    most peaking) available tranches in ``pool`` first, cascading down — the
    headroom that physically carries the AS award. Mutates ``availability`` in
    place and returns ``(GWh-equiv withdrawn, GWh-equiv unmet)`` for logging.
    """
    if pool.size == 0:
        return 0.0, 0.0
    order = pool[np.argsort(-heat_rate[pool], kind="stable")]
    caps = pmax[order, np.newaxis] * availability[order, :]  # (k, hours)
    cum_above = np.cumsum(caps, axis=0) - caps  # MW ranked above each tranche
    removed = np.clip(as_series[np.newaxis, :] - cum_above, 0.0, caps)
    with np.errstate(divide="ignore", invalid="ignore"):
        availability[order, :] = np.where(
            pmax[order, np.newaxis] > 0.0,
            (caps - removed) / pmax[order, np.newaxis],
            0.0,
        )
    unmet = float(np.maximum(as_series - caps.sum(axis=0), 0.0).sum())
    return float(removed.sum()), unmet


# Fraction of nameplate a unit can ramp within the 10-minute reserve window,
# by plant group — the cap on the upward operating reserve a synchronized unit
# can deliver (``FleetArrays.ramp10 = frac * pmax``; rebuild step 3b,
# docs/multi-iso/pjm-reserve-ordc.md Phase 2). Class ramp rates (% of capacity
# per minute, x10 min) from NREL "Western Wind and Solar Integration Study"
# Phase 2 (NREL/TP-5500-55588, App. H) and EIA generator ramp-rate ranges:
# subcritical/supercritical coal steam ~1.5 %/min, gas combined cycle ~4 %/min,
# simple-cycle CT / oil peakers fast-start (full output reachable in <10 min),
# legacy gas steam ~2 %/min. Nuclear runs baseload (no upward reserve). Keyed by
# the model plant group; the per-fuel fallback covers non-binned fleets. These
# depend only on capacity and class, so ramp10 regenerates for a forecast year.
RAMP10_FRAC_BY_GROUP: dict[str, float] = {
    "COAL": 0.15,  # steam, ~1.5 %/min
    "CC_REGULAR": 0.40,  # combined cycle, ~4 %/min
    "CC_CHP": 0.40,
    "CT_PEAKER": 1.00,  # simple-cycle fast-start, full in <10 min
    "CT_CHP": 1.00,
    "ST_GAS": 0.20,  # legacy gas steam, ~2 %/min
    "ST_CHP": 0.20,
}
# Per-fuel fallback (legacy aggregated fleets without a plant group). Nuclear and
# the renewables/hydro/storage classes carry no thermal upward reserve here.
RAMP10_FRAC_BY_FUEL: dict[str, float] = {
    "coal": 0.15,
    "gas_cc": 0.40,
    "gas_cc_ccs": 0.40,
    "gas_ct": 1.00,
    "gas_st": 0.20,
    "oil": 1.00,
}


def _ramp10_capability(
    generators: list[Generator],
    pmax: np.ndarray,
    measured: dict | None = None,
) -> np.ndarray:
    """Return the ``(n_gen,)`` 10-minute ramp capability (MW) for a fleet.

    ``RAMP10_FRAC_BY_GROUP[plant_group]`` (preferred, the per-plant CAMPD-bin
    fleets) or :data:`RAMP10_FRAC_BY_FUEL` (legacy aggregated fleets) times the
    unit's capacity. Generators in neither map (nuclear, hydro, wind, solar,
    storage, imports) get 0.0 — they provide no thermal upward operating
    reserve. See :attr:`FleetArrays.ramp10`.

    When ``measured`` is given (``ScenarioConfig.measured_ramp_capability`` —
    the ``ramp-capability`` clean datatype, plant_code →
    :class:`~market_sim.data.ramp_capability.PlantRampCapability`), each
    covered plant's class fraction is reconciled against its MEASURED EIA-860
    fast-start capacity (floor) and CAMPD CEMS hourly ramp envelope (ceiling)
    via :func:`market_sim.data.ramp_capability.measured_ramp10_frac`; uncovered
    plants keep the class estimate (rule 14: measured preferred, estimate only
    as fallback).
    """
    from market_sim.data.ramp_capability import measured_ramp10_frac

    fracs = np.zeros(len(generators), dtype=float)
    for g_idx, gen in enumerate(generators):
        frac = RAMP10_FRAC_BY_GROUP.get(getattr(gen, "plant_group", "") or "")
        if frac is None:
            frac = RAMP10_FRAC_BY_FUEL.get(gen.fuel_type, 0.0)
        if measured and frac > 0.0:
            cap = measured.get(int(getattr(gen, "plant_code", 0) or 0))
            if cap is not None:
                frac = measured_ramp10_frac(frac, cap)
        fracs[g_idx] = frac
    return fracs * pmax


# Coal synchronization online%-scaled forcing (step-3a): a plant whose measured
# online_frac is at or above this threshold is treated as synchronized ~all year
# and held at its min-load floor every hour (the always-online supercriticals);
# below it the floor is placed only in the top-online_frac fraction of hours by
# system load (a two-shifting cycler). 0.99 keeps the supercriticals on the
# force-all path (rounding to 8760) while letting the cyclers shed their cheap
# overnight hours. See generators_to_fleet_arrays / bins_to_fleet.
_COAL_SYNC_FORCE_ALL: float = 0.99


def generators_to_fleet_arrays(
    generators: list[Generator],
    zone_names: list[str],
    hours: int = 8760,
    iso: str | None = None,
    config: ScenarioConfig | None = None,
    load_shape: np.ndarray | None = None,
    ct_campd_shape: dict[int, np.ndarray] | None = None,
    year: int | None = None,
) -> FleetArrays:
    """Convert a list of generators into vectorized ``FleetArrays``.

    Availability is set to ``1 - eford`` for every hour. When ``iso`` is
    given and has :data:`NUCLEAR_MONTHLY_CF` factors, nuclear generators get
    a month-varying availability instead, capturing refueling outages and
    planned maintenance. Other seasonal derates are applied later.

    Coal carries no Pmin floor: each coal bin is split into take-or-pay
    tranches (see :func:`split_coal_tranches`), each with ``pmin_mw = 0``,
    so coal's baseload behavior emerges from tranche economics rather than a
    hard minimum.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}

    n_gen = len(generators)
    pmax = np.array([g.pmax_mw for g in generators], dtype=float)
    pmin = np.array([g.pmin_mw for g in generators], dtype=float)
    heat_rate = np.array([g.heat_rate for g in generators], dtype=float)
    vom = np.array([g.vom for g in generators], dtype=float)
    emission_rate = np.array([g.emission_rate_co2 for g in generators], dtype=float)
    nox_rate = np.array([g.nox_rate for g in generators], dtype=float)
    so2_rate = np.array([g.so2_rate for g in generators], dtype=float)
    zone_idx = np.array([zone_to_idx[g.zone] for g in generators], dtype=int)
    fuel_type_idx = np.array(
        [FUEL_TYPE_MAP[g.fuel_type] for g in generators], dtype=int
    )

    eford = np.array([g.eford for g in generators], dtype=float)
    availability = np.broadcast_to((1.0 - eford)[:, np.newaxis], (n_gen, hours)).copy()

    # Apply nuclear monthly availability factors (refueling outages, planned
    # maintenance). NUCLEAR_MONTHLY_CF holds 12 monthly capacity-factor caps
    # from NRC PRIS data; they multiply the EFORD derate to give the final
    # hourly availability. Non-nuclear units keep the flat 1 - eford derate.
    # Prefer the per-year 923-derived refueling pattern for the backcast;
    # fall back to the fixed seasonal average for forecast years.
    _iso = iso.upper() if iso else None
    _yr = getattr(config, "weather_year", None) if config is not None else None
    monthly_cf = NUCLEAR_MONTHLY_CF_BY_YEAR.get(_iso, {}).get(_yr) if _iso else None
    # The 923-derived per-year CF is realized availability (it already embeds
    # refueling + forced outages + derate), so it is used directly. The static
    # forecast pattern is a planned-outage cap, so the EFORD forced-outage
    # derate is layered on top of it.
    from_actual = monthly_cf is not None
    if monthly_cf is None and _iso:
        monthly_cf = NUCLEAR_MONTHLY_CF.get(_iso)
    if monthly_cf is not None:
        monthly_factors = np.array(monthly_cf, dtype=float)
        month_idx = _hour_to_month_index(hours)
        for g_idx, gen in enumerate(generators):
            if gen.fuel_type == "nuclear":
                base = monthly_factors[month_idx]
                availability[g_idx, :] = (
                    base if from_actual else (1.0 - gen.eford) * base
                )
    # Dormant nuclear (EIA-860 lists OP but the unit is physically offline,
    # e.g. the Crane/TMI-1 restart): zero it in backcast years before its
    # return-to-service year. Forecast runs keep the unit — in backcast mode
    # weather_year is the calendar year; in forecast it is only a weather
    # shape, so the comparison would be meaningless there.
    if _yr is not None and getattr(config, "mode", "forecast") == "backcast":
        for g_idx, gen in enumerate(generators):
            if gen.fuel_type == "nuclear" and _yr < NUCLEAR_DORMANT_UNTIL.get(
                int(gen.plant_code), 0
            ):
                availability[g_idx, :] = 0.0

    # Summer peak, spring/autumn shoulder, and winter — a 3-way partition of
    # the year. The shoulder absorbs the outage shifted out of summer; winter
    # is left at base availability so the winter peak is not derated.
    month = _hour_to_month_index(hours) + 1
    summer = np.isin(month, list(_SUMMER_MONTHS))
    shoulder = np.isin(month, list(_CC_SHOULDER_MONTHS))
    summer_hours = int(summer.sum())
    shoulder_hours = int(shoulder.sum())

    # Thermal availability: an age-based model keyed to the plant-group
    # category (THERMAL_AVAILABILITY). Each unit's annual outage energy is
    # conserved but concentrated away from the summer and winter demand peaks:
    #   * WEFOR (forced outages): only _SUMMER_WEFOR_SHARE applies in summer;
    #     the remaining (1 - share) is redistributed into the shoulder months
    #     only. Winter keeps the flat WEFOR.
    #   * POF (planned outages): applies in the shoulder months only — none in
    #     summer or winter, where load peaks.
    #   * The weather/performance derate stays flat year-round.
    # The annual-average availability of each unit is unchanged — only the
    # seasonal shape moves. Non-thermal units (nuclear, hydro, ...) keep the
    # 1 - EFORD derate. Age is the run year minus the unit's commission year.
    #
    # Per-plant CT_PEAKER reliability must-run floor (config.ct_mustrun_per_plant,
    # backcast only). The observed EIA-923 net generation is forced on these
    # peakers as a minimum below; because that floor already nets out every real
    # outage, WEFOR and the planned-outage (maintenance) derate must NOT apply to
    # the floor units (they would double-count and clip it). The table is keyed
    # by plant code; an empty table (flag off, or forecast/missing 923) leaves
    # every code path byte-identical.
    ct_floor_mwh: dict[int, np.ndarray] = {}
    ct_floor_frac = 0.0
    if (
        config is not None
        and getattr(config, "ct_mustrun_per_plant", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        ct_floor_frac = float(getattr(config, "ct_mustrun_floor_frac", 1.0) or 0.0)
        if ct_floor_frac > 0.0:
            ct_floor_mwh = ct_mustrun_floor_mwh_by_plant(int(_yr))
    ct_floor_plants = set(ct_floor_mwh)
    # Per-plant CT_PEAKER AS/RUC-deployment hourly floor (config
    # .ct_deployment_overlay, backcast only): the measured out-of-merit CEMS
    # energy, applied below as a sparse per-hour min-gen bound. Unlike the
    # must-run floor above, the deployment units keep the statistical WEFOR/POF
    # model (the floor is well below pmax in its hours), so they are NOT added
    # to ct_floor_plants — only availability-capped where they coincide.
    ct_deploy_floor: dict[int, np.ndarray] = {}
    ct_deploy_frac = 0.0
    if (
        config is not None
        and getattr(config, "ct_deployment_overlay", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        ct_deploy_frac = float(getattr(config, "ct_deployment_floor_frac", 1.0) or 0.0)
        if ct_deploy_frac > 0.0:
            ct_deploy_floor = ct_deployment_floor_for_year(
                int(_yr), hours, _iso or "ERCOT"
            )
    ct_deploy_plants = set(ct_deploy_floor)
    # Spatial reliability-deployment hourly floor (config
    # .reliability_deployment_overlay, backcast only): the load-pocket thermal
    # fleet's measured congestion-subset CEMS energy (CC_REGULAR/COAL/ST_GAS/
    # CC_CHP in South_Central/West/Northeast). Applied below as a sparse per-hour
    # min-gen bound keyed by plant code, distributed cheapest-first over the
    # plant's tranches. Like the CT deployment floor, these units keep the
    # statistical WEFOR/POF model (the floor is sparse and below pmax), so they
    # are only availability-capped where they coincide.
    rd_deploy_floor: dict[int, np.ndarray] = {}
    rd_deploy_frac = 0.0
    if (
        config is not None
        and getattr(config, "reliability_deployment_overlay", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and _yr is not None
    ):
        rd_deploy_frac = float(
            getattr(config, "reliability_deployment_floor_frac", 1.0) or 0.0
        )
        if rd_deploy_frac > 0.0:
            rd_deploy_floor = reliability_deployment_floor_for_year(
                int(_yr), hours, _iso or "ERCOT"
            )
    rd_deploy_plants = set(rd_deploy_floor)
    if config is not None and shoulder_hours > 0:
        run_year = config.weather_year
        summer_to_shoulder = summer_hours / shoulder_hours
        drop_coal_pof = getattr(config, "coal_drop_pof", False)
        # Historic-backcast WEFOR residual: the CAMPD overlay + unit-level
        # derate already carry every >= 5-day outage for the covered classes
        # (coal + _POF_DROP_GROUPS), so their full statistical WEFOR would
        # double-count those events. Cap it at the short-outage residual the
        # overlay's detector floor leaves uncovered. CTs have no overlay
        # coverage and keep the full statistical model.
        wefor_res = (
            getattr(config, "wefor_residual", None)
            if getattr(config, "outage_source", "statistical") == "historic"
            else None
        )
        # CC nameplate + per-plant summer derate (config.cc_nameplate_summer_
        # derate): CC plants carry full nameplate capacity (raised in
        # fleet_to_bins) and are derated to their measured net-summer rating in
        # summer only. In a historic backcast the statistical WEFOR/POF/age
        # derate are also dropped for CC — the CAMPD outage overlay already
        # carries every real outage, so the statistical model double-counts.
        cc_np_derate = getattr(config, "cc_nameplate_summer_derate", False)
        cc_np_derate_backcast = (
            cc_np_derate
            and getattr(config, "outage_source", "statistical") == "historic"
        )
        # FORECAST-mode monthly planned-maintenance shape (spec 1.7). When
        # enabled, the flat shoulder-POF block (POF subtracted uniformly across
        # _CC_SHOULDER_MONTHS) is replaced by the historically-derived
        # MAINTENANCE_MONTHLY_SHAPE — a per-group 12-month curve whose
        # month-length-weighted mean is 1, so the group's annual POF budget
        # (POF * shoulder_hours) is conserved exactly while its seasonal
        # distribution is sharpened (peaks Apr/Oct-Nov, ~0 at the Jul/Aug
        # summer peak). Backcast runs keep the legacy flat block. _maint_derate
        # returns the per-hour planned-maintenance derate for a unit's group.
        _mode = getattr(config, "mode", "forecast")
        use_maint_shape = _mode == "forecast" and getattr(
            config, "maintenance_monthly_shape", True
        )
        month0 = month - 1  # 0-based calendar month per hour, for shape lookup
        shoulder_frac = shoulder_hours / hours
        _maint_pooled = MAINTENANCE_MONTHLY_SHAPE.get("_POOLED")

        def _maint_derate(
            group: str, pof_value: float, pof_eff_legacy: float
        ) -> np.ndarray:
            """Per-hour planned-maintenance derate for ``group``.

            Forecast (shape on): ``POF * shoulder_frac * w[group][month]`` — the
            monthly curve, annual budget conserved. Otherwise (backcast, or shape
            off): the legacy flat block, ``pof_eff_legacy`` in the shoulder
            months and zero elsewhere (byte-identical to the prior model).
            """
            if use_maint_shape:
                w = np.asarray(
                    MAINTENANCE_MONTHLY_SHAPE.get(group, _maint_pooled), dtype=float
                )
                return pof_value * shoulder_frac * w[month0]
            out = np.zeros(hours, dtype=float)
            out[shoulder] = pof_eff_legacy
            return out

        for g_idx, gen in enumerate(generators):
            if gen.plant_group not in THERMAL_AVAILABILITY:
                continue
            is_cc_np = cc_np_derate and gen.plant_group in ("CC_REGULAR", "CC_CHP")
            pof, wefor, derate = _thermal_outage(
                gen.plant_group, run_year - gen.online_year
            )
            # ISO-gated gas-steam forced-outage base override. The global ST_GAS
            # WEFOR base (0.21) is fitted to ERCOT's once-through steamers and is
            # >2x every other thermal class — an implicit availability crush that
            # holds intermediate-duty steam off on top of the EIA-860 net-summer
            # rating already applied. When configured, replace the base with a
            # realistic NERC-GADS gas-steam EFOR, keeping the age escalation.
            _st_wefor_base = getattr(config, "gas_st_wefor_base_override", None)
            if _st_wefor_base is not None and gen.plant_group in ("ST_GAS", "ST_CHP"):
                _, _w_base, _w_rate, _w_onset, *_ = THERMAL_AVAILABILITY[
                    gen.plant_group
                ]
                _age = run_year - gen.online_year
                wefor = _st_wefor_base + max(0.0, _age - _w_onset) * _w_rate
            # Lighten (or raise) the forced-outage magnitude while keeping the
            # seasonal shape — applied before the summer/shoulder/winter split.
            wefor *= config.wefor_multiplier
            # WEFOR residual cap (historic-backcast double-count relief). By
            # default it applies to every CAMPD-covered class (coal +
            # _POF_DROP_GROUPS), whose sustained outages the overlay/unit/
            # partial derates already carry. ``wefor_residual_groups`` narrows
            # it to a chosen subset — the measured per-class evidence shows
            # the relief is only warranted where the class was actually
            # availability-capped (ST_GAS 2024) and is harmful where the
            # class is already over (CC) or displaces an un-relieved class
            # (CT keeps the full statistical model — no CAMPD coverage).
            _relief_groups = getattr(config, "wefor_residual_groups", None)
            _covered = (
                gen.plant_group in _relief_groups
                if _relief_groups
                else (gen.fuel_type == "coal" or gen.plant_group in _POF_DROP_GROUPS)
            )
            if wefor_res is not None and _covered:
                wefor = min(wefor, wefor_res)
            if is_cc_np and cc_np_derate_backcast:
                # CC nameplate, historic backcast: the CAMPD outage overlay below
                # carries every SUSTAINED outage, so the statistical POF and the
                # age/performance derate are dropped (the net-summer rating
                # already captures performance). Only the short-outage forced
                # residual remains — wefor is already capped to
                # ``wefor_residual`` above for this overlay-covered class, the
                # brief forced events below the overlay's multi-day detector
                # floor — so the unit starts at ``1 - wefor_residual`` at
                # nameplate; the per-plant summer derate is applied below.
                availability[g_idx, :] = 1.0 - wefor
            elif is_cc_np:
                # CC nameplate, statistical/forward run: keep WEFOR/POF (no
                # overlay) but the seasonal cap comes from the per-plant summer
                # derate below, not the flat class derate.
                summer_wefor = _SUMMER_WEFOR_SHARE * wefor
                shoulder_wefor = (
                    wefor + (1.0 - _SUMMER_WEFOR_SHARE) * wefor * summer_to_shoulder
                )
                pof_eff = 0.0 if drop_coal_pof else pof
                maint_h = _maint_derate(gen.plant_group, pof, pof_eff)
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - summer_wefor - derate
                availability[g_idx, shoulder] = 1.0 - shoulder_wefor - derate
                availability[g_idx, :] -= maint_h
            elif (
                gen.plant_group == "CT_PEAKER"
                and int(gen.plant_code) in ct_floor_plants
            ):
                # Reliability must-run floor unit: WEFOR and the planned-outage
                # (maintenance) derate do not apply — the floor injected below is
                # observed EIA-923 generation, which already embeds every real
                # outage, so the statistical outage model would double-count and
                # clip it. Keep only the flat performance derate (the summer
                # ambient derate still multiplies in below).
                availability[g_idx, :] = 1.0 - derate
            elif getattr(gen, "coal_sync_pmin_mw", 0.0) > 0.0:
                # Coal synchronization floor tranche (_mustrun / _sync): held at
                # the measured online Pmin via min_gen below. The STATISTICAL
                # WEFOR and planned-maintenance derate must NOT erode this floor
                # — a synced baseload coal unit physically holds min load in
                # every hour it is online, and the min_gen floor is clipped to
                # pmax x availability (line ~1682), so a statistical derate here
                # would silently pull the floor below its measured cap (the
                # MISO/Merom under-run bug). Genuine availability still relaxes
                # it: the historic facility outage overlay and the unit-level
                # outage derate apply AFTER this on the same array and still
                # zero/derate the floor during real outages, and the online%-
                # scaled top-k forcing already drops the floor in the bottom
                # (1 - online_frac) load hours the cycler genuinely shuts.
                # Mirrors the CT_PEAKER reliability-floor treatment above.
                availability[g_idx, :] = 1.0
            elif drop_coal_pof and gen.fuel_type == "coal":
                # Planned maintenance now comes from the historic outage
                # overlay, so drop the statistical POF (and its summer->shoulder
                # WEFOR redistribution) to avoid double-counting. Keep WEFOR in
                # the non-summer months and the derate all year; summer runs at
                # 1 - derate (WEFOR off for the peak).
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - derate
            else:
                summer_wefor = _SUMMER_WEFOR_SHARE * wefor
                shoulder_wefor = (
                    wefor + (1.0 - _SUMMER_WEFOR_SHARE) * wefor * summer_to_shoulder
                )
                # Drop the shoulder POF for the historic-overlay classes (CC /
                # ST + their CHP) so it does not double-count the actual planned
                # outages from the overlay + unit derate; CTs keep POF.
                pof_eff = (
                    0.0
                    if drop_coal_pof and gen.plant_group in _POF_DROP_GROUPS
                    else pof
                )
                maint_h = _maint_derate(gen.plant_group, pof, pof_eff)
                # Default (winter): flat WEFOR. Then override summer and
                # shoulder for the WEFOR seasonal split, and subtract the
                # planned-maintenance derate across all months (forecast: the
                # monthly shape; backcast/legacy: pof_eff in the shoulder only).
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - summer_wefor - derate
                availability[g_idx, shoulder] = 1.0 - shoulder_wefor - derate
                availability[g_idx, :] -= maint_h
            # Per-bin forced derates for confirmed unit losses (e.g. a
            # multi-unit plant losing one boiler to a fire). Applied as a
            # flat multiplier on top of the age-based availability.
            forced = BIN_FORCED_DERATE_BY_YEAR.get(gen.bin_label, {}).get(run_year)
            if forced is not None:
                availability[g_idx, :] *= forced
            # Summer ambient-temperature derate. CC plants under
            # cc_nameplate_summer_derate use their per-plant MEASURED summer
            # derate (net_summer / nameplate) — the capacity was raised to
            # nameplate in fleet_to_bins, so this brings the summer months back
            # to the real net-summer rating. Every other class keeps the flat
            # ``_SUMMER_CLASS_DERATE``.
            if is_cc_np:
                ratio = cc_summer_derate_ratio(int(gen.plant_code))
                if ratio is not None and ratio < 1.0:
                    availability[g_idx, summer] *= ratio
            else:
                summer_derate = _SUMMER_CLASS_DERATE.get(gen.plant_group)
                if summer_derate:
                    availability[g_idx, summer] *= 1.0 - summer_derate
            # Per-plant coal max-CF ceilings: cap availability so the unit
            # cannot dispatch above its sustained operating limit.
            if gen.plant_group == "COAL":
                _pc = int(gen.plant_code)
                cap = COAL_MAX_CF_BY_PLANT.get(_pc)
                if cap is not None:
                    np.minimum(availability[g_idx, :], cap, out=availability[g_idx, :])
                scap = COAL_SUMMER_MAX_CF.get(_pc)
                if scap is not None:
                    availability[g_idx, summer] = np.minimum(
                        availability[g_idx, summer], scap
                    )
        np.clip(availability, 0.0, 1.0, out=availability)

    # Historic-outage overlay (backcast only). When config.outage_source is
    # "historic", zero availability for coal/CC plants during their actual
    # sustained (> 10-day) outage windows, a hard override of the statistical
    # WEFOR/POF model in those hours. Forward/forecast runs leave outages
    # statistical (outage_source == "statistical", the default). The per-bin
    # group filter restricts zeroing to the plant's coal/CC bins, so a plant
    # carrying both a CC and a non-CC bin only has its CC bin outaged.
    if (
        config is not None
        and getattr(config, "outage_source", "statistical") == "historic"
    ):
        # ERCOT reads the legacy campd-outages.csv intersected with its bin
        # CSV; every other ISO reads its own campd-outages-{ISO}.csv (already
        # coal/CC only, so no bin intersection). The per-bin gen.plant_group
        # filter below still restricts zeroing to coal/CC tranches.
        is_ercot = _iso == "ERCOT" or _iso is None
        # The facility-summed overlay is the primary outage layer only where the
        # unit-level derate is supplemental (ERCOT). ISOs whose unit-level file
        # is the complete CAMPD-derived source disable it (config flag) so the
        # two layers don't double-count.
        masks = (
            outage_masks_for_year(
                config.weather_year,
                hours,
                outages_path=default_outages_path(_iso),
                bins_path=(
                    getattr(
                        config,
                        "campd_bins_path",
                        str(CAMPD_BINS_CSV),
                    )
                    if is_ercot
                    else None
                ),
            )
            if getattr(config, "historic_outage_overlay", True)
            else {}
        )
        if masks:
            applied = 0
            for g_idx, gen in enumerate(generators):
                if gen.plant_group not in QUALIFYING_PLANT_GROUPS:
                    continue
                mask = masks.get(int(gen.plant_code))
                if mask is None:
                    continue
                availability[g_idx, mask] = 0.0
                applied += 1
            logger.info(
                "historic outage overlay (%s %d): zeroed %d coal/CC "
                "bin-tranches across %d plant(s)",
                _iso or "ERCOT",
                config.weather_year,
                applied,
                len(masks),
            )
        # Unit-level outage derate (backcast): partial availability cut per
        # unit outage >= 5 days, sized by the unit's share of its plant's
        # capacity (CTs excluded; ERCOT split plants routed to the right asset
        # class). Catches single-unit outages the facility-summed overlay above
        # hides — e.g. the W A Parish coal units, masked in CEMS by the gas
        # units that keep running. Built per ISO by
        # scripts/derive_campd_unit_outages.py --iso <ISO>; ISOs with no
        # unit-outage file get an empty derate (no effect). Multiplies the
        # availability already set above.
        ufac = unit_outage_derate_factors(
            config.weather_year,
            hours,
            getattr(config, "campd_bins_path", str(CAMPD_BINS_CSV)),
            iso=_iso or "ERCOT",
        )
        if ufac:
            # NEISO temperature-reliability-floor exemption (CLAUDE.md #11). The
            # lone Merrimack-class COAL unit and lone ST_GAS unit are winter
            # cold-snap RELIABILITY runners whose commitment is governed by
            # transmission.inject_reliability_floor, with coefficients
            # regressed from each unit's own measured CAMPD capacity factor. That
            # regression already nets out the unit's real maintenance downtime, so
            # re-applying the CF-gap unit-outage derate on top double-counts it.
            # Worse, for a unit that runs only on cold snaps (sub-10% annual CF)
            # the detector's "sustained CF < 5%" rule reads the unit's *economic
            # idleness* as a forced outage, and the derate's unit_capacity_mw /
            # plant_capacity_mw fraction is taken against the 108 MW model bin
            # while the CSV's unit capacities are the real ~460 MW plant, so a
            # single coal-unit "outage" over-derates the bin to zero -- collapsing
            # availability (0 of 8760 h in 2024) and structurally capping the
            # floor (frac x available) at ~0. The floor is the correct,
            # forward-faithful availability/commitment model for these units, so
            # exempt them here exactly as the ct_mustrun_per_plant floor exempts
            # its units from WEFOR/planned outage. Scoped to NEISO + the two floor
            # classes + floor-on, so non-floor runs stay byte-identical.
            neiso_floor_exempt = _iso == "NEISO" and getattr(
                config, "reliability_floor", False
            )
            exempt_groups = {"COAL", "ST_GAS"}
            applied_u = 0
            exempted_u = 0
            for g_idx, gen in enumerate(generators):
                if neiso_floor_exempt and gen.plant_group in exempt_groups:
                    exempted_u += 1
                    continue
                f = ufac.get((int(gen.plant_code), gen.plant_group))
                if f is not None:
                    availability[g_idx, :] *= f
                    applied_u += 1
            logger.info(
                "unit-outage derate (%s %d): %d plant-tranches derated%s",
                _iso or "ERCOT",
                config.weather_year,
                applied_u,
                (
                    f"; {exempted_u} NEISO floor-class tranche(s) exempted "
                    "(temp-reliability floor governs availability)"
                    if exempted_u
                    else ""
                ),
            )
        # Within-window retiree measured-availability cap (CAMPD unit-level):
        # a unit winding down to retirement is held at its coal must-run floor
        # by the cost-based LP while reality barely ran it (out-of-market
        # retirement economics the merit order cannot see, and the per-plant
        # binning collapses the per-unit COD before the ramp). Cap each retiree
        # plant's availability to its measured monthly CEMS envelope. Applied
        # before min_gen is built so the must-run floor (clamped to availability)
        # scales down with it. Plant-keyed (reaches every binned tranche),
        # scoped to the within-window retirees; the bulk fleet keeps its
        # cost-based dispatch. Gated to the validated ISO (config flag).
        if getattr(config, "retiree_cems_cap", False):
            rcaps = retiree_availability_caps(
                _iso or "ERCOT", config.weather_year, hours
            )
            if rcaps:
                applied_r = 0
                for g_idx, gen in enumerate(generators):
                    cap = rcaps.get(int(gen.plant_code))
                    if cap is not None:
                        np.minimum(
                            availability[g_idx, :], cap, out=availability[g_idx, :]
                        )
                        applied_r += 1
                logger.info(
                    "retiree CEMS availability cap (%s %d): %d tranche(s) across "
                    "%d retiree plant(s) capped to measured envelope",
                    _iso or "ERCOT",
                    config.weather_year,
                    applied_r,
                    len(rcaps),
                )
        if not masks and not ufac:
            # A backcast year with no measured windows in either layer (e.g.
            # CAISO 2023: no CA unit-level CEMS extract until upload U1 lands)
            # silently degrades to the statistical WEFOR/POF model; say so,
            # and record it in the run's model_changes_note.
            logger.warning(
                "outage_source='historic' but no outage windows cover %s %d; "
                "availability is statistical-only for this year",
                _iso or "ERCOT",
                config.weather_year,
            )
        # The partial-outage derate below is an ERCOT-only extract (CAMPD
        # CF-ceiling plateaus keyed to ERCOT plant codes); other ISOs carry no
        # such file, so it stays scoped to ERCOT.
        if is_ercot:
            # Partial-outage derate (CAMPD CF-ceiling plateaus): approximate
            # half-units-out events for baseload coal + a confirmed CC
            # allowlist where no unit data exists. Multiplies availability
            # over the window.
            pfac = partial_outage_derate_factors(config.weather_year, hours)
            if pfac:
                applied_p = 0
                for g_idx, gen in enumerate(generators):
                    f = pfac.get(int(gen.plant_code))
                    if f is not None:
                        availability[g_idx, :] *= f
                        applied_p += 1
                logger.info(
                    "partial-outage derate (%d): %d bin-tranches derated",
                    config.weather_year,
                    applied_p,
                )

    # NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay
    # (config.nysdec_peaker_rule_availability, NYISO): units whose curated
    # compliance-schedule row is an ozone-season shutdown / reliability-only
    # restriction are unavailable to the energy market inside their effective
    # May 1 - Sep 30 windows. An exogenous regulatory availability event
    # (rule #12 class of the CAMPD outage windows) — availability only, never
    # an offer/price change — so it applies regardless of outage_source and in
    # any mode (the schedule is the regulation's, forward-valid). ``oil``
    # scope zeroes the plant's raw oil units (matched per generator id when
    # the row names units); ``gas_ct`` scope derates the plant's CT-class
    # tranches by restricted_mw / class capacity (full zero when the row
    # restricts the whole class).
    if config is not None and getattr(config, "nysdec_peaker_rule_availability", False):
        from market_sim.data.outages import nysdec_peaker_restrictions

        applied_dec = 0
        for r in nysdec_peaker_restrictions(config.weather_year, hours):
            code, scope = r["plant_code"], r["scope"]
            h_lo, h_hi = r["h_lo"], r["h_hi"]
            if scope == "oil":
                for g_idx, gen in enumerate(generators):
                    if int(gen.plant_code) != code or gen.fuel_type != "oil":
                        continue
                    if r["unit_ids"] and not any(
                        str(gen.unit_id).endswith(f"_{u}") for u in r["unit_ids"]
                    ):
                        continue
                    availability[g_idx, h_lo:h_hi] = 0.0
                    applied_dec += 1
            else:  # gas_ct: the plant's simple-cycle CT-class tranches
                idxs = [
                    g_idx
                    for g_idx, gen in enumerate(generators)
                    if int(gen.plant_code) == code
                    and gen.plant_group in ("CT_PEAKER", "CT_CHP")
                ]
                if not idxs:
                    continue
                class_mw = float(sum(pmax[i] for i in idxs))
                mw = r["restricted_mw"]
                frac = 1.0 if mw is None else min(1.0, mw / max(class_mw, 1e-9))
                for g_idx in idxs:
                    availability[g_idx, h_lo:h_hi] *= 1.0 - frac
                applied_dec += len(idxs)
        if applied_dec:
            logger.info(
                "NYSDEC 227-3 peaker-rule overlay (%s %d): %d unit/tranche "
                "availability window(s) restricted",
                _iso or "?",
                config.weather_year,
                applied_dec,
            )

    # Reallocate each CC_REGULAR plant's outage derate from pro-rata to
    # top-of-stack (config.cc_outage_derate_from_top): the plant's hourly
    # available MW is unchanged, but it now fills the tranches bottom-up in
    # heat-rate order, so a partial outage truncates the expensive duct-fire /
    # high-econ end of the offer curve while the cheap committed floor keeps
    # its level — matching how a multi-train CC sheds its least-efficient
    # increments first and runs the surviving train near full load.
    if config is not None and getattr(config, "cc_outage_derate_from_top", False):
        cc_by_plant: dict[int, list[int]] = {}
        for g_idx, gen in enumerate(generators):
            if gen.plant_group == "CC_REGULAR" and int(gen.plant_code) > 0:
                cc_by_plant.setdefault(int(gen.plant_code), []).append(g_idx)
        realloc_plants = 0
        for idxs in cc_by_plant.values():
            if len(idxs) < 2:
                continue  # single-tranche plant: nothing to reallocate
            # Merit order within the plant: tranches share one fuel price, so
            # heat rate ranks them (committed < econ slices < peak).
            order = sorted(idxs, key=lambda i: heat_rate[i])
            caps = pmax[order]  # (n_tranches,)
            avail_mw = availability[order, :].T @ caps  # (T,) plant total
            cum_below = np.concatenate(([0.0], np.cumsum(caps[:-1])))
            bounds = np.clip(
                avail_mw[np.newaxis, :] - cum_below[:, np.newaxis],
                0.0,
                caps[:, np.newaxis],
            )
            availability[order, :] = bounds / caps[:, np.newaxis]
            realloc_plants += 1
        if realloc_plants:
            logger.info(
                "CC_REGULAR outage derate reallocated top-of-stack for %d plant(s)",
                realloc_plants,
            )

    # Hard minimum-generation bounds composed below: CHP grid-steam floors,
    # coal synchronization Pmin, nuclear flat must-run, and the per-plant
    # CT/reliability deployment overlays. Temperature-driven ST_GAS commitment is
    # now handled by the generic reliability-floor engine
    # (transmission.inject_reliability_floor), not a calendar-month seasonal floor.
    min_gen = None
    min_gen_mech = None
    chp_pmin_any = any(getattr(g, "chp_grid_pmin_mw", 0.0) > 0.0 for g in generators)
    coal_sync_any = any(getattr(g, "coal_sync_pmin_mw", 0.0) > 0.0 for g in generators)
    # Nuclear runs flat as must-run baseload — it physically cannot load-follow
    # on price, so it must not back down to a part-load pmin in CAISO's many
    # negative/near-zero midday hours (the ~1 TWh Diablo Canyon under-run). Pin
    # it at its hourly availability cap (the refuel-schedule-driven monthly CF
    # already set in ``availability``), which is a forward-derivable physical
    # input, not a price/volume fit. Backcast only (forecast keeps the cap as a
    # planned-outage ceiling, not a floor).
    nuclear_flat = (
        config is not None
        and getattr(config, "mode", "forecast") == "backcast"
        and any(g.fuel_type == "nuclear" for g in generators)
    )
    if (
        chp_pmin_any
        or ct_floor_plants
        or ct_deploy_plants
        or rd_deploy_plants
        or nuclear_flat
        or coal_sync_any
    ):
        min_gen = np.zeros((n_gen, hours), dtype=float)
        # Parallel mechanism-id array (D-2 forced-energy attribution): each
        # block below tags the unit-hours whose binding floor it supplied.
        min_gen_mech = np.zeros((n_gen, hours), dtype=np.int8)
        # min_gen replaces pmin as the LP lower bound for EVERY generator
        # (build_variable_bounds), so export sinks (pmin < 0, absorption
        # modeled as negative generation) must keep their range — a zero
        # floor would pin them off whenever any CHP/ST_GAS floor is active.
        neg_pmin = pmin < 0.0
        if neg_pmin.any():
            min_gen[neg_pmin, :] = pmin[neg_pmin, np.newaxis]
        if nuclear_flat:
            # Flat must-run: floor == availability cap, so nuclear holds its
            # available output through the solar-glut belly instead of cycling
            # to a 0.9*pmax part-load when the midday price falls below its VOM.
            for g_idx, gen in enumerate(generators):
                if gen.fuel_type == "nuclear":
                    min_gen[g_idx, :] = availability[g_idx, :] * pmax[g_idx]
                    min_gen_mech[g_idx, min_gen[g_idx, :] > 0.0] = MECH_NUCLEAR
        # CHP grid-delivered steam-following floor: the cogen's steady export
        # is forced on flat all year (the dispatchable surplus rides above it
        # via the load-following tranches).
        for g_idx, gen in enumerate(generators):
            pmin_mw = getattr(gen, "chp_grid_pmin_mw", 0.0)
            if pmin_mw > 0.0:
                min_gen[g_idx, :] = pmin_mw
                min_gen_mech[g_idx, :] = MECH_CHP_STEAM
        # Coal synchronization floor (rebuild step 3a,
        # config.coal_sync_srmc_tranche): the _mustrun (contracted, fuel-free)
        # and _sync (spot, SRMC) coal min-load tranches are held on at the
        # measured online Pmin so the unit stays synchronized instead of
        # price-following to zero. The forcing is **online%-scaled** (step-3a
        # full fix): a plant synchronized ~all year (online_frac >=
        # _COAL_SYNC_FORCE_ALL, the supercriticals) is held every hour; a
        # two-shifting cycler is held only in the top-online_frac fraction of
        # hours by *system load* — mirroring the CT must-run load-shaping, so the
        # floor lands where the cycler actually runs (the load peaks) and relaxes
        # in the cheap overnight hours it would real-world shut for. The floor is
        # the tranche capacity; min_gen is clipped to pmax*availability below, so
        # an outage hour relaxes it. np.maximum composes with any floor already
        # placed.
        if coal_sync_any:
            sys_load = (
                np.asarray(load_shape, dtype=float)
                if load_shape is not None and len(load_shape) == hours
                else None
            )
            # Hours ranked peak-load first; the top-k carry a cycler's floor.
            load_rank = (
                np.argsort(-sys_load, kind="stable") if sys_load is not None else None
            )
            for g_idx, gen in enumerate(generators):
                pmin_mw = getattr(gen, "coal_sync_pmin_mw", 0.0)
                if pmin_mw <= 0.0:
                    continue
                frac = float(getattr(gen, "coal_sync_online_frac", 1.0))
                if frac >= _COAL_SYNC_FORCE_ALL or load_rank is None:
                    raised = min_gen[g_idx, :] < pmin_mw
                    np.maximum(min_gen[g_idx, :], pmin_mw, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_COAL_MUSTRUN
                else:
                    k = int(round(frac * hours))
                    if k <= 0:
                        continue
                    hrs = load_rank[:k]
                    # Fancy indexing returns a copy, so out= cannot target it;
                    # compute the max then assign back via the fancy index.
                    raised = hrs[min_gen[g_idx, hrs] < pmin_mw]
                    min_gen[g_idx, hrs] = np.maximum(min_gen[g_idx, hrs], pmin_mw)
                    min_gen_mech[g_idx, raised] = MECH_COAL_MUSTRUN
        # Per-plant CT_PEAKER reliability must-run floor: spread each plant's
        # observed monthly net generation (frac-scaled) across that month's
        # hours, *shaped by system load* — the energy is placed in the
        # above-median-load hours (where simple-cycle peakers actually run) and
        # left at zero whenever the peaker was actually offline, so it genuinely
        # starts and stops (it is not held on at a flat baseload level) and
        # displaces marginal gas/imports at the peak rather than coal baseload.
        # The hourly *shape* comes from the plant's CAMPD/CEMS hourly record
        # (zero in every hour the unit did not report load — real start/stop);
        # where a plant has no CAMPD coverage it falls back to the system-load
        # shape (energy placed in the above-median-load hours). Within each hour
        # the floor is distributed over the plant's tranches cheapest-first
        # (committed -> econ -> peak), each capped at its available capacity. The
        # floor units' availability already excludes WEFOR/POF (set above), so
        # the observed energy fits under the cap.
        if ct_floor_plants:
            month_idx = _hour_to_month_index(hours)
            sys_load = (
                np.asarray(load_shape, dtype=float)
                if load_shape is not None and len(load_shape) == hours
                else None
            )
            ct_tranches: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                if (
                    gen.plant_group == "CT_PEAKER"
                    and int(gen.plant_code) in ct_floor_plants
                ):
                    ct_tranches.setdefault(int(gen.plant_code), []).append(g_idx)
            # System-load fallback weights (per month, summing to 1.0):
            # max(load - median, 0) concentrates energy in the peak hours.
            load_weights: dict[int, np.ndarray] = {}
            for m in range(12):
                hmask = month_idx == m
                n_h = int(hmask.sum())
                if n_h == 0:
                    continue
                if sys_load is not None:
                    lm = sys_load[hmask]
                    w = np.maximum(lm - np.median(lm), 0.0)
                    if w.sum() <= 0.0:
                        w = np.ones(n_h, dtype=float)
                else:
                    w = np.ones(n_h, dtype=float)
                load_weights[m] = w / w.sum()
            for pc, idxs in ct_tranches.items():
                # Cheapest tranche first so the floor lands on the committed band.
                idxs.sort(key=lambda i: heat_rate[i])
                mwh12 = ct_floor_mwh[pc]
                campd_shape = (
                    ct_campd_shape.get(pc) if ct_campd_shape is not None else None
                )
                for m in range(12):
                    if m not in load_weights:
                        continue
                    energy = ct_floor_frac * float(mwh12[m])
                    if energy <= 0.0:
                        continue
                    hmask = month_idx == m
                    # Prefer the plant's CAMPD on/off shape (zero hours = offline,
                    # so the floor starts/stops); fall back to the load shape.
                    w = None
                    if campd_shape is not None and len(campd_shape) == hours:
                        # NaN hours = unit not reporting = offline -> zero weight,
                        # so the floor genuinely stops there.
                        cs = np.nan_to_num(
                            np.asarray(campd_shape, dtype=float)[hmask],
                            nan=0.0,
                            posinf=0.0,
                            neginf=0.0,
                        )
                        cs = np.maximum(cs, 0.0)
                        if cs.sum() > 0.0:
                            w = cs / cs.sum()
                    if w is None:
                        w = load_weights[m]
                    # Per-hour floor (MW) summing to ``energy`` MWh over the month.
                    remaining = energy * w
                    for g_idx in idxs:
                        if not remaining.any():
                            break
                        # Flat availability within a calendar month for these
                        # units, so the cap is a scalar.
                        cap_mw = float((pmax[g_idx] * availability[g_idx, hmask]).min())
                        take = np.minimum(remaining, cap_mw)
                        min_gen[g_idx, hmask] = take
                        mech_row = min_gen_mech[g_idx, hmask]
                        mech_row[take > 0.0] = MECH_CT_MUSTRUN_PER_PLANT
                        min_gen_mech[g_idx, hmask] = mech_row
                        remaining = remaining - take
        # Per-plant CT_PEAKER AS/RUC-deployment hourly floor: in each plant's
        # measured out-of-merit hours, force its observed net output as a
        # minimum, distributed over the plant's tranches cheapest-first
        # (committed -> econ -> peak) and each capped at the tranche's available
        # MW that hour. The floor is sparse (zero outside deployment hours), so
        # the in-merit hours dispatch economically as before; ``np.maximum``
        # composes it with any reliability must-run floor already placed above
        # rather than clobbering it.
        if ct_deploy_plants:
            ct_d_tranches: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                if (
                    gen.plant_group == "CT_PEAKER"
                    and int(gen.plant_code) in ct_deploy_plants
                ):
                    ct_d_tranches.setdefault(int(gen.plant_code), []).append(g_idx)
            deploy_mwh = 0.0
            for pc, idxs in ct_d_tranches.items():
                idxs.sort(key=lambda i: heat_rate[i])
                remaining = ct_deploy_frac * ct_deploy_floor[pc]  # (hours,)
                deploy_mwh += float(remaining.sum())
                for g_idx in idxs:
                    cap = pmax[g_idx] * availability[g_idx, :]
                    take = np.minimum(remaining, cap)
                    raised = min_gen[g_idx, :] < take
                    np.maximum(min_gen[g_idx, :], take, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_CT_DEPLOYMENT_OVERLAY
                    remaining = remaining - take
            logger.info(
                "CT deployment overlay (%s %s): floored %d peaker(s), "
                "%.2f TWh of out-of-merit energy (frac %.2f)",
                _iso or "ERCOT",
                _yr,
                len(ct_d_tranches),
                deploy_mwh / 1e6,
                ct_deploy_frac,
            )
        # Per-plant spatial reliability-deployment hourly floor: in each
        # load-pocket plant's measured congestion-subset hours (economic at its
        # local load-zone price, out of merit at the system hub), force its
        # observed net output as a minimum, distributed over the plant's
        # tranches cheapest-first and each capped at that tranche's available MW.
        # Keyed by plant code (any thermal class), so a split plant's tranches
        # are gathered together. The floor is sparse (zero outside the
        # congestion hours), so in-merit hours dispatch economically as before;
        # ``np.maximum`` composes it with any floor already placed above.
        if rd_deploy_plants:
            rd_tranches: dict[int, list[int]] = {}
            for g_idx, gen in enumerate(generators):
                pc = int(gen.plant_code)
                if pc in rd_deploy_plants:
                    rd_tranches.setdefault(pc, []).append(g_idx)
            rd_mwh = 0.0
            for pc, idxs in rd_tranches.items():
                idxs.sort(key=lambda i: heat_rate[i])
                remaining = rd_deploy_frac * rd_deploy_floor[pc]  # (hours,)
                rd_mwh += float(remaining.sum())
                for g_idx in idxs:
                    cap = pmax[g_idx] * availability[g_idx, :]
                    take = np.minimum(remaining, cap)
                    raised = min_gen[g_idx, :] < take
                    np.maximum(min_gen[g_idx, :], take, out=min_gen[g_idx, :])
                    min_gen_mech[g_idx, raised] = MECH_RELIABILITY_DEPLOYMENT_OVERLAY
                    remaining = remaining - take
            logger.info(
                "reliability deployment overlay (%s %s): floored %d "
                "pocket plant(s), %.2f TWh of congestion energy (frac %.2f)",
                _iso or "ERCOT",
                _yr,
                len(rd_tranches),
                rd_mwh / 1e6,
                rd_deploy_frac,
            )
        # Never demand more than the (outage/derate-adjusted) availability.
        np.minimum(min_gen, pmax[:, np.newaxis] * availability, out=min_gen)
        # An outage hour that collapsed the floor is no longer forced.
        clear_where_unfloored(min_gen_mech, min_gen)

    # Ancillary-service reserve withholding (backcast). Capacity the market
    # holds out of energy as upward reserve is withdrawn from the gas/flexible-
    # thermal top-of-merit headroom (most expensive/peaking headroom first —
    # the part-loaded capacity that physically carries the reserve), so the
    # energy supply curve clears without it and the afternoon-peak price lifts.
    # ERCOT: the cleared DAM up-AS (Reg-Up/RRS/ECRS); when the per-resource-type
    # series is available each thermal class withholds *its own measured* hourly
    # AS MW from its top-of-merit headroom (the physically-grounded split;
    # storage/load AS, which carry the bulk in ERCOT, are excluded as they do
    # not withhold thermal energy), else the system-total upper bound on the gas
    # pool. PJM: the measured RT Primary Reserve requirement (the binding
    # upward 10-min product that nests Synchronized, Manual 11 sec 4.4.1) on the
    # gas + flexible-oil pool (coal/nuclear baseload excluded). The withdrawn
    # pool is consistent with scarcity.pjm_online_reserve, which measures
    # plant-level online reserve over the same thermal fleet. Applied last,
    # after every outage/derate; floored back up to any must-run min_gen.
    # Down-AS (Reg-Down) is excluded upstream — it removes no upward offer.
    if (
        config is not None
        and getattr(config, "as_reserve_withholding", False)
        and _iso in _AS_WITHHOLDING
    ):
        _yr_as = getattr(config, "weather_year", 0)
        pool_groups = _AS_WITHHOLDING[_iso][2]
        withdrawn = unmet = 0.0
        # Per-resource-type split is ERCOT-only (no PJM per-type AS file);
        # every other ISO uses the system-total measured series on its pool.
        by_class = (
            load_as_thermal_withholding(_yr_as, hours) if _iso == "ERCOT" else None
        )
        if by_class is not None:
            for col, series in by_class.items():
                pool = np.array(
                    [
                        i
                        for i, g in enumerate(generators)
                        if g.plant_group in _AS_RESTYPE_TO_GROUPS[col]
                    ],
                    dtype=int,
                )
                w, u = _withdraw_top_of_merit(
                    availability, pmax, heat_rate, pool, series
                )
                withdrawn += w
                unmet += u
            source = "measured per-type"
        else:
            as_mw = load_as_reserve_withholding_mw(_yr_as, hours, iso=_iso)
            pool = np.array(
                [i for i, g in enumerate(generators) if g.plant_group in pool_groups],
                dtype=int,
            )
            if as_mw is not None:
                withdrawn, unmet = _withdraw_top_of_merit(
                    availability, pmax, heat_rate, pool, as_mw
                )
            source = (
                "measured PR requirement"
                if _iso == "PJM"
                else "system-total upper bound"
            )
        if min_gen is not None:
            floor_frac = np.zeros_like(availability)
            np.divide(
                min_gen,
                pmax[:, np.newaxis],
                out=floor_frac,
                where=pmax[:, np.newaxis] > 0.0,
            )
            np.maximum(availability, floor_frac, out=availability)
        np.clip(availability, 0.0, 1.0, out=availability)
        logger.info(
            "AS reserve withholding (%s %s, %s): withdrew %.1f GWh-equiv "
            "from thermal top-of-merit (%.1f GWh unmet by headroom)",
            _iso,
            _yr_as,
            source,
            withdrawn / 1e3,
            unmet / 1e3,
        )

    # CAISO formula-based operating-reserve withholding (default off; the
    # measured-OASIS path is unavailable until the remote-env outbound-network
    # block is lifted). Computes R(t) = max(MSSC, 0.067*load) + 0.01*load from
    # the load shape and the fleet's largest single-unit nameplate (the WECC
    # MSSC), then withdraws it from the gas top-of-merit headroom exactly like
    # the measured ERCOT/PJM path above — lifting the tight-hour / evening-tail
    # price. Coal/nuclear baseload is left out of the pool, and the midday floor
    # (a separate longness/marginal-offer problem) is untouched.
    if (
        config is not None
        and getattr(config, "as_reserve_formula", False)
        and _iso == "CAISO"
        and load_shape is not None
    ):
        mssc_mw = float(
            max(
                (
                    pmax[i]
                    for i, g in enumerate(generators)
                    if g.fuel_type not in _CAISO_MSSC_EXCLUDE_FUELS
                ),
                default=0.0,
            )
        )
        r_mw = caiso_operating_reserve_mw(load_shape, mssc_mw, hours)
        pool = np.array(
            [i for i, g in enumerate(generators) if g.plant_group in _AS_GAS_GROUPS],
            dtype=int,
        )
        withdrawn, unmet = _withdraw_top_of_merit(
            availability, pmax, heat_rate, pool, r_mw
        )
        if min_gen is not None:
            floor_frac = np.zeros_like(availability)
            np.divide(
                min_gen,
                pmax[:, np.newaxis],
                out=floor_frac,
                where=pmax[:, np.newaxis] > 0.0,
            )
            np.maximum(availability, floor_frac, out=availability)
        np.clip(availability, 0.0, 1.0, out=availability)
        logger.info(
            "CAISO operating-reserve withholding (formula, %s): MSSC %.0f MW, "
            "R(t) mean %.0f / max %.0f MW; withdrew %.1f GWh-equiv from gas "
            "top-of-merit (%.1f GWh unmet by headroom)",
            getattr(config, "weather_year", 0),
            mssc_mw,
            float(r_mw.mean()),
            float(r_mw.max()),
            withdrawn / 1e3,
            unmet / 1e3,
        )

    # Commercial-operation-date (COD) vintage ramp — the single COD mechanism
    # for the whole fleet (data.cod_ramp). A unit that came online or retired
    # part-way through the solved year is available only in the months it
    # actually operated, instead of the all-year-or-nothing annual screen: the
    # thermal/nuclear/oil analogue of the renewable/storage vintage ramps. The
    # month-precise COD comes from the EIA-860 plant-code map (data.cod_ramp
    # .load_cod_map) — which is what gives the ERCOT CAMPD bins (carrying no
    # build date of their own) their COD — with each generator's own
    # online_year/month as the fall-back. Applied last (after every outage/
    # derate/withholding) so nothing re-raises an offline month; min_gen (the
    # hard must-run floor) is zeroed in offline months too, else the LP lower
    # bound would force a not-yet-built/retired unit to run. Default-on for
    # backcasts (config.cod_ramp_enabled); forecast runs pass an explicit
    # calendar ``year`` to engage it.
    _cod_year = year if year is not None else getattr(config, "weather_year", None)
    if (
        config is not None
        and getattr(config, "cod_ramp_enabled", True)
        and getattr(config, "mode", "forecast") == "backcast"
        and _cod_year is not None
    ):
        cod_map = load_cod_map()
        online_mask = np.ones((n_gen, 12), dtype=float)
        cod_class_labels: list[str] = []
        cod_online_years: list[int | None] = []
        for g_idx, gen in enumerate(generators):
            oy, om, ry, rm = effective_cod(
                int(gen.plant_code),
                gen.online_year,
                gen.online_month,
                gen.retirement_year,
                gen.retirement_month,
                cod_map,
            )
            online_mask[g_idx] = monthly_online_mask(oy, om, ry, rm, _cod_year)
            # Per-class COD coverage guardrail: a class whose units all resolve
            # to a known EIA-860 COD is month-precision ramped; a class with no
            # COD dates silently bypasses the vintage ramp (data.cod_ramp
            # .log_class_cod_coverage WARNs so a future vintage cannot drop a
            # class unnoticed). Synthetic, non-physical units (plant_code <= 0 —
            # the WECC import-node tranches) carry no EIA-860 COD by design and
            # are excluded; the audit covers only real EIA-860 plants.
            if int(gen.plant_code) > 0:
                cod_class_labels.append(gen.plant_group or gen.fuel_type)
                cod_online_years.append(oy)
        log_class_cod_coverage(
            class_cod_coverage(cod_class_labels, cod_online_years), _iso, _cod_year
        )
        if (online_mask < 1.0).any():
            month_idx = _hour_to_month_index(hours)
            ramp = online_mask[:, month_idx]  # (n_gen, hours) 0/1
            availability *= ramp
            if min_gen is not None:
                min_gen *= ramp
                # Offline months carry no floor, hence no forcing mechanism.
                clear_where_unfloored(min_gen_mech, min_gen)
            dropped = int((online_mask.max(axis=1) < 1.0).sum())
            offline = int((online_mask < 1.0).sum())
            logger.info(
                "COD ramp (%s %s): %d unit-months masked offline "
                "(mid-year COD / retirement), %d unit(s) fully not-yet-built/"
                "retired",
                _iso,
                _cod_year,
                offline,
                dropped,
            )

    # Measured ramp/fast-start capability (GATED config.measured_ramp_capability,
    # default off): reconcile the class 10-minute fractions against the
    # ramp-capability clean datatype (EIA-860 "10M" fast-start floor + CAMPD
    # CEMS hourly-envelope ceiling, data/ramp_capability.py). Class fractions
    # remain the uncovered-plant fallback.
    _measured_ramp: dict | None = None
    if (
        config is not None
        and getattr(config, "measured_ramp_capability", False)
        and iso is not None
    ):
        from market_sim.data.ramp_capability import load_measured_ramp_capability

        _measured_ramp = load_measured_ramp_capability(iso)

    return FleetArrays(
        pmax=pmax,
        pmin=pmin,
        heat_rate=heat_rate,
        vom=vom,
        emission_rate=emission_rate,
        nox_rate=nox_rate,
        so2_rate=so2_rate,
        zone_idx=zone_idx,
        fuel_type_idx=fuel_type_idx,
        availability=availability,
        unit_ids=[g.unit_id for g in generators],
        efficiency_bin=np.array([g.efficiency_bin for g in generators], dtype=str),
        plant_code=np.array([int(g.plant_code) for g in generators], dtype=int),
        state=np.array([g.state for g in generators], dtype=object),
        plant_group=np.array([g.plant_group for g in generators], dtype=object),
        min_gen=min_gen,
        min_gen_mechanism=min_gen_mech,
        ramp10=_ramp10_capability(generators, pmax, measured=_measured_ramp),
    )


# Fuel types collapsed into efficiency-bin representative units. Everything
# else -- nuclear, hydro, import (few in number, distinct characteristics)
# and wind/solar (not part of the thermal fleet) -- passes through unchanged.
# Oil and biomass are aggregatable thermal blocks too; including them here
# also means ERCOT's CAMPD-bin path (which sources non-aggregatable fuels
# from EIA-860) excludes the handful of ERCOT oil/biomass units exactly as it
# already excluded their gas_ct-classified predecessors, keeping ERCOT
# dispatch unchanged.
_AGGREGATABLE_FUELS: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "coal", "oil", "biomass"}
)


def apply_netload_reliability_floor(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    net_load_mw: np.ndarray,
    *,
    plant_group: str,
    slope: float,
    intercept: float,
    cap: float,
    ramp_window: tuple[int, int] | None = None,
    exclude_plant_codes: frozenset[int] = frozenset(),
    mech_id: int = MECH_CT_NETLOAD_DRAG,
) -> bool:
    """Impose a net-load-indexed reliability-commitment min-gen floor on a class.

    The shared engine behind the per-class ERCOT reliability-drag floors
    (:func:`apply_gas_st_netload_drag_floor`, :func:`apply_ct_netload_drag_floor`)
    — the endogenous, weather-driven replacement for a fixed seasonal must-run
    fraction or an actuals pin. ERCOT commits these out-of-merit thermal units
    at minimum load for local/system reliability (RUC/RMR); the held fraction is
    not a calendar season but rises with system **net-load** (``load - wind -
    solar``), the operational proxy for the reserve tightness RUC keys off. Each
    non-``_peak`` tranche of ``plant_group`` (the economic ``_peak`` scarcity
    band runs purely on price) whose plant is not in ``exclude_plant_codes`` gets
    a per-hour minimum-generation floor of
    ``clip(slope*netload_GW + intercept, 0, cap) x pmax``, capped at available
    capacity and composed with any existing floor via ``maximum``; the LP
    dispatches economically *above* it.

    ``ramp_window=(start, end)`` gates the floor to the local-standard
    hour-of-day window ``[start, end)`` (``hour t -> t % 24`` on the model's
    8760 clock), zeroing it elsewhere — used for resources that serve
    reliability only in a diurnal window (CT peakers in the afternoon-evening
    net-load ramp), where ``None`` applies the floor every hour (the all-hours
    gas-steam boiler). Because both the trigger (net-load) and the magnitude
    (physical min-gen) are forward-derivable and condition-responsive, the
    mechanism is admissible in both backcast and forecast (CLAUDE.md #10/#11).

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when the class has no reliability units.
    """
    rows = [
        g
        for g, gen in enumerate(generators)
        if gen.plant_group == plant_group
        # exclude every peak-band rung ("peak", "peak2".. under a ladder) —
        # the scarcity band is never commitment scaffolding
        and not gen.unit_id.rpartition("_")[2].startswith("peak")
        and gen.plant_code not in exclude_plant_codes
    ]
    if not rows:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    net_load_gw = np.asarray(net_load_mw, dtype=float)[:hours] / 1000.0
    floor_frac = np.clip(slope * net_load_gw + intercept, 0.0, cap)  # (T,)
    if ramp_window is not None:
        # Gate to the diurnal reliability window; zero outside it. Hour of day on
        # the model's local-standard 8760 clock is t % 24.
        start, end = ramp_window
        hod = np.arange(hours) % 24
        floor_frac = np.where((hod >= start) & (hod < end), floor_frac, 0.0)

    if fleet_arrays.min_gen is None:
        # min_gen replaces pmin as the LP lower bound for EVERY generator, so a
        # fresh floor must preserve export-sink rows (pmin < 0) by seeding from
        # pmin rather than zeroing them (mirrors generators_to_fleet_arrays).
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()

    mech = ensure_mechanism(fleet_arrays)
    pmax = fleet_arrays.pmax
    avail = fleet_arrays.availability
    for g in rows:
        # Never floor above the hour's available capacity, so the LP stays
        # feasible (the drag can never manufacture unmet demand).
        target = np.minimum(floor_frac * pmax[g], avail[g, :] * pmax[g])
        raised = fleet_arrays.min_gen[g, :] < target
        fleet_arrays.min_gen[g, :] = np.maximum(fleet_arrays.min_gen[g, :], target)
        mech[g, raised] = mech_id
    return True


def apply_gas_st_netload_drag_floor(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> bool:
    """Impose the net-load-indexed ST_GAS reliability-drag min-gen floor.

    The endogenous, weather-driven net-load drag floor (a forward-native
    replacement for a fixed seasonal calendar fraction). ERCOT holds legacy
    gas-steam
    units committed at minimum load for local/system reliability (RUC); the
    held fraction is not a fixed season but rises with system **net-load**
    (``load - wind - solar``), the operational proxy for reserve tightness RUC
    keys off. Each non-peaker ST_GAS tranche (peaker-class units in
    :data:`ST_GAS_PEAKER_PLANTS` and the economic ``_peak`` tranche are
    excluded — they run purely on price) gets a per-hour minimum-generation
    floor of ``clip(slope*netload_GW + intercept, 0, cap) x pmax``, capped at
    available capacity and composed with any existing floor via ``maximum``.
    The LP dispatches economically *above* the floor, so the floor only binds
    in the low-price (overnight / shoulder) hours where an energy-only merit
    order would leave these out-of-merit boilers off — exactly the
    reliability-drag energy the dispatch was missing.

    The default curve coefficients (``config.gas_st_drag_slope_per_gw`` /
    ``_intercept`` / ``_cap``) are the CAMPD overnight (low-price) ST_GAS
    capacity factor regressed on contemporaneous system net-load, 2023-2025
    (``docs/ercot-st-gas-netload-drag-2026-06.md``); the relationship is
    year-stable, so the same curve regenerates for a forward year (which has a
    load forecast and a wind/solar build, hence a net-load) and responds to
    changed conditions (more VRE lowers net-load and so the drag). That
    forward-derivability and condition-response is what makes it admissible in
    both backcast and forecast (CLAUDE.md #10), unlike a fixed seasonal fraction
    or an offer markdown tuned to the ST_GAS residual.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when the flag is off or the fleet has no
    reliability ST_GAS units.

    Args:
        fleet_arrays: The vectorized fleet (``min_gen`` is set in place).
        generators: The dispatch fleet, aligned row-for-row with ``fleet_arrays``.
        net_load_mw: System net-load per hour (``load - wind - solar``), the same
            LP-served (net-of-must-run) net-load convention the runner uses
            elsewhere, shape ``(T,)``.
        config: Scenario config supplying the enable flag and curve coefficients.
    """
    if not getattr(config, "gas_st_netload_drag", False):
        return False
    # All-hours boiler floor (no ramp window); peaker-class ST_GAS plants run on
    # price and are excluded.
    return apply_netload_reliability_floor(
        fleet_arrays,
        generators,
        net_load_mw,
        plant_group="ST_GAS",
        slope=config.gas_st_drag_slope_per_gw,
        intercept=config.gas_st_drag_intercept,
        cap=config.gas_st_drag_cap,
        ramp_window=None,
        exclude_plant_codes=ST_GAS_PEAKER_PLANTS,
        mech_id=MECH_ST_NETLOAD_DRAG,
    )


def apply_ct_netload_drag_floor(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> bool:
    """Impose the net-load-indexed CT_PEAKER reliability-drag min-gen floor.

    The simple-cycle analog of :func:`apply_gas_st_netload_drag_floor`, and the
    forward-native replacement for the ``ct_mustrun_per_plant`` actuals pin.
    ERCOT commits fast-start gas peakers for summer-peak + evening
    net-load-ramp local reliability (RUC / RMR); the hourly energy-only LP,
    seeing their top-of-merit offer, never makes that commitment, so the
    backcast under-runs CT_PEAKER and the freed energy spills onto cheaper CC.

    Unlike the all-hours ST_GAS boiler, CT peakers serve reliability only in the
    afternoon-evening ramp (solar collapse): the CAMPD overnight CF is ~0 even
    at high net-load, while the evening (15-22h local-standard) CF rises cleanly
    with net-load (Spearman rho ~0.7, 2023-2025). So the floor is the same
    clipped net-load line ``clip(slope*netload_GW + intercept, 0, cap)`` but
    **gated to the ramp window** ``[ct_drag_ramp_start, ct_drag_ramp_end)`` —
    zero outside it. The window is on the model's local-standard hour-of-year
    clock (hour t → t % 24), the same clock the CAMPD fit used. Each non-``_peak``
    CT_PEAKER tranche (the duct-firing ``_peak`` scarcity band runs purely on
    price) gets the floor, capped at available capacity and composed with any
    existing floor via ``maximum``; the LP dispatches economically above it.

    The defaults (``config.ct_drag_slope_per_gw`` / ``_intercept`` / ``_cap``)
    are the CAMPD CT_PEAKER evening capacity factor regressed on contemporaneous
    net-load, 2023-2025 (``docs/ercot-ct-netload-drag-2026-06.md``); both the
    trigger (net-load) and the magnitude (physical min-gen) are forward-derivable
    and condition-responsive, so the mechanism is admissible in both backcast and
    forecast (CLAUDE.md #10/#11), unlike an offer markdown or actuals pin.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when the flag is off or the fleet has no
    reliability CT_PEAKER units.

    Args:
        fleet_arrays: The vectorized fleet (``min_gen`` is set in place).
        generators: The dispatch fleet, aligned row-for-row with ``fleet_arrays``.
        net_load_mw: System net-load per hour (``load - wind - solar``), the same
            LP-served convention the runner uses elsewhere, shape ``(T,)``.
        config: Scenario config supplying the enable flag, curve coefficients and
            ramp window.
    """
    if not getattr(config, "ct_netload_drag", False):
        return False
    # Evening-ramp-gated floor (peakers serve reliability in the afternoon-
    # evening net-load ramp, not overnight).
    return apply_netload_reliability_floor(
        fleet_arrays,
        generators,
        net_load_mw,
        plant_group="CT_PEAKER",
        slope=config.ct_drag_slope_per_gw,
        intercept=config.ct_drag_intercept,
        cap=config.ct_drag_cap,
        ramp_window=(config.ct_drag_ramp_start, config.ct_drag_ramp_end),
        mech_id=MECH_CT_NETLOAD_DRAG,
    )


@lru_cache(maxsize=1)
def _load_ct_offer_surface() -> tuple[tuple[float, float, float], ...]:
    """Load the frozen measured CT/peaker offer-surface regimes.

    Reads ``data/raw/_validation-source/ercot_ct_offer_surface.json`` (produced by
    ``scripts/derive_ct_offer_surface.py`` from the 60-Day DAM disclosure) and
    returns its regimes as ``(q_lo, q_hi, offer_level)`` triples. Cached — the
    surface is frozen against residuals (rule 20); a re-derive is a data-update
    commit, not a solve-time knob.
    """
    from market_sim.config import paths

    path = paths.CALIBRATION_DIR / "ercot_ct_offer_surface.json"
    payload = json.loads(path.read_text())
    return tuple(
        (float(lo), float(hi), float(level)) for lo, hi, level in payload["regimes"]
    )


def apply_ercot_ct_offer_surface(
    mc_base: np.ndarray,
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> bool:
    """Raise ERCOT CT/peaker econ+peak offers to the measured self-withholding level.

    The G-22 condition-responsive offer surface (filed structural conclusion #1
    of ``docs/FINDING-ercot-priceshape-2026-07.md`` §6; design note
    ``docs/handoffs/ercot-g22-offer-surface-2026-07.md``). In the missed tail
    hours the P1 LP offers every online CT/peaker economic+peak tranche at its
    flat marginal cost ``heat_rate x gas + VOM`` (~$50-150/MWh) — the "phantom
    sub-$200 spare" that caps the energy dual below the scarcity level the real
    market cleared. The real fleet's peakers had already offered themselves to
    the ERCOT cap band (~$1,500/MWh) by those hours: the 60-Day DAM disclosure
    shows the CT/peaker offer at 90% of HSL is cap-band, not heat-rate x gas
    (``scripts/derive_ct_offer_surface.py``).

    This posts the **measured** self-withholding offer level on the CT/peaker
    ``econ*``/``peak*`` tranches (the phantom-spare bands; the ``mustrun``/
    ``sync``/``committed`` min-gen scaffolding is untouched), keyed on a
    **net-load percentile** driver. The low regime is inert (level 0), so the LP
    applies ``max(mc, 0) = mc`` and every sub-hinge hour is byte-identical; only
    above the measured hinge — the net-load percentile at which even the peaker
    fleet's lower quartile has crossed to cap-band — is the offer raised. Unlike
    the REJECTED ercot33 static wall this is condition-responsive (inert in the
    ~90% of hours below the hinge, so no broad elevation) and touches only the
    CT/peaker class (no CC/ST peak-band repricing, the channel that moved measured
    volumes through the P0->P1 startup-amortization coupling). Both the trigger
    (net-load) and the level (measured offer) are forward-derivable and respond to
    changed conditions, so the mechanism is admissible in backcast and forecast
    (CLAUDE.md #10/#13); every parameter is measured and frozen (rules 20/26).

    Vectorised (no hour loop, rule 2). Modifies ``mc_base`` in place. Returns
    ``True`` when the surface was applied, ``False`` (byte-identical) when the
    flag is off, the ISO is not ERCOT, or the fleet has no CT/peaker econ/peak
    tranches.

    Args:
        mc_base: The P1 bid-cost matrix ``(n_gen, T)``, mutated in place.
        generators: The dispatch fleet, aligned row-for-row with ``mc_base``.
        net_load_mw: System net-load per hour (``load - wind - solar``), shape
            ``(T,)`` — the same LP-served convention the drag floors use.
        config: Scenario config supplying the enable flag and ISO.
    """
    if not getattr(config, "ercot_ct_offer_surface", False):
        return False
    if config.iso != "ERCOT":
        return False
    # The phantom-spare bands: CT_PEAKER economic (``econ``/``econc00``..) and
    # peak (``peak``/``peak2``..) tranches. The min-gen scaffolding
    # (``mustrun``/``sync``/``committed``) is commitment structure, never repriced.
    rows = [
        g
        for g, gen in enumerate(generators)
        if gen.plant_group == "CT_PEAKER"
        and (
            gen.unit_id.rpartition("_")[2].startswith("econ")
            or gen.unit_id.rpartition("_")[2].startswith("peak")
        )
    ]
    if not rows:
        return False

    regimes = _load_ct_offer_surface()
    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    # Per-hour measured offer level from the net-load-percentile regimes. A
    # percentile hinge maps to a net-load quantile threshold on this year's own
    # net-load distribution (forward-native: the same construction regenerates
    # from a forecast load+VRE net-load), so the surface tracks the year's
    # scarcity structure rather than an absolute MW line.
    level_series = np.zeros(hours)
    for q_lo, q_hi, level in regimes:
        if level <= 0.0:
            continue
        lo_mw = np.quantile(net_load, q_lo)
        if q_hi >= 1.0:
            mask = net_load >= lo_mw
        else:
            mask = (net_load >= lo_mw) & (net_load < np.quantile(net_load, q_hi))
        level_series[mask] = level

    row_idx = np.asarray(rows)
    mc_base[row_idx, :] = np.maximum(mc_base[row_idx, :], level_series[np.newaxis, :])
    hinge = min((lo for lo, _hi, lv in regimes if lv > 0.0), default=1.0)
    logger.info(
        "ERCOT CT/peaker offer surface applied: %d econ/peak tranche rows raised "
        "to the measured self-withholding level above the %.0fth net-load "
        "percentile (%d/%d hours)",
        len(rows),
        hinge * 100.0,
        int((level_series > 0.0).sum()),
        hours,
    )
    return True


def apply_netload_drag_floors(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    demand: np.ndarray,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    config: ScenarioConfig,
    iso: str,
    year: int,
) -> None:
    """Apply the net-load-indexed reliability-drag min-gen floors (both classes).

    The single shared gate-and-log wrapper over
    :func:`apply_gas_st_netload_drag_floor` (legacy gas-steam boilers) and
    :func:`apply_ct_netload_drag_floor` (CT_PEAKER simple-cycle, evening-ramp
    gated), called by BOTH orchestrators (orchestrator-unification Stage 6 --
    the ~40-line wrapper was previously duplicated verbatim in ``runner.py``
    and ``scripts/run_calibration.py``). Each floors a tranche's per-hour
    minimum generation by a curve rising with system net-load
    (``load - wind - solar``, the LP-served convention) -- the operational
    proxy for the reserve tightness RUC keys off -- over which the LP
    dispatches economically. Both appliers gate internally on their own
    config flag and modify ``fleet_arrays.min_gen`` in place; with both flags
    off this returns without computing anything (byte-identical).
    """
    if not (
        getattr(config, "gas_st_netload_drag", False)
        or getattr(config, "ct_netload_drag", False)
    ):
        return
    # t: hour. Net-load = load - wind - solar, LP-served convention.
    net_load = (
        demand.sum(axis=0)
        - (solar_cap[:, None] * solar_cf).sum(axis=0)
        - (wind_cap[:, None] * wind_cf).sum(axis=0)
    )
    if apply_gas_st_netload_drag_floor(fleet_arrays, generators, net_load, config):
        logger.info(
            "%s %d: ST_GAS net-load reliability-drag floor applied "
            "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f); net-load mean %.0f / "
            "max %.0f MW)",
            iso,
            year,
            config.gas_st_drag_slope_per_gw,
            config.gas_st_drag_intercept,
            config.gas_st_drag_cap,
            float(net_load.mean()),
            float(net_load.max()),
        )
    if apply_ct_netload_drag_floor(fleet_arrays, generators, net_load, config):
        logger.info(
            "%s %d: CT_PEAKER net-load reliability-drag floor applied "
            "(frac = clip(%.5f*netGW %+0.4f, 0, %.2f) in ramp %dh-%dh)",
            iso,
            year,
            config.ct_drag_slope_per_gw,
            config.ct_drag_intercept,
            config.ct_drag_cap,
            config.ct_drag_ramp_start,
            config.ct_drag_ramp_end,
        )


def apply_neiso_coldsnap_derate(
    fleet_arrays: "FleetArrays",
    config: ScenarioConfig,
    iso: str,
    year: int,
) -> None:
    """Apply the NEISO winter gas-availability cold-snap derate (gated).

    The shared gate-and-log wrapper over
    :func:`market_sim.model.transmission.inject_neiso_gas_coldsnap_derate`
    (temperature-dependent forced outage, TDFOR): on cold snaps the
    gas-electric constraint makes non-dual-fuel gas-CC/CT capacity physically
    UNAVAILABLE, so the fleet goes reserve-short and the RCPF co-opt prices
    the >$300 scarcity tail (and widens the storage spread). Must run before
    the reserve-co-opt inputs are built so the shared-headroom RHS sees the
    derated availability. Dual-fuel units are excluded (they switch to oil,
    not vanish).

    Called by BOTH orchestrators (orchestrator-unification Stage 6 -- the
    mechanism was previously wired only in ``scripts/run_calibration.py``,
    the §2.2 accidental-drift row this stage closes). Gated on
    ``config.neiso_gas_coldsnap_derate`` (default off, byte-identical); the
    curve coefficients are plain ``ScenarioConfig`` fields (NERC
    cold-weather-anchored defaults -- see the field citations), no longer
    getattr fallback literals (CLAUDE.md #24).
    """
    if not getattr(config, "neiso_gas_coldsnap_derate", False):
        return
    # Local import: transmission imports from data.fleet at module level.
    from market_sim.model.transmission import inject_neiso_gas_coldsnap_derate

    if inject_neiso_gas_coldsnap_derate(
        fleet_arrays,
        iso,
        year,
        float(config.neiso_gas_derate_t0_c),
        float(config.neiso_gas_derate_slope_per_c),
        float(config.neiso_gas_derate_cap),
    ):
        logger.info(
            "%s %d: winter gas-availability derate — non-dual-fuel gas-CC/CT "
            "availability cut by clip(slope*(t0-TMIN),0,cap) over the cold-snap "
            "window (TDFOR, NERC cold-weather anchored)",
            iso,
            year,
        )


def _capacity_weighted(units: list[Generator], attr: str) -> float:
    """Return the capacity-weighted average of ``attr`` over ``units``.

    Falls back to a plain mean when the group has no positive capacity.
    """
    total_cap = sum(u.pmax_mw for u in units)
    if total_cap > 0.0:
        return sum(getattr(u, attr) * u.pmax_mw for u in units) / total_cap
    return sum(getattr(u, attr) for u in units) / len(units)


def _aggregate_with_predefined_bins(
    generators: list[Generator], fuel_type: str
) -> list[Generator]:
    """Aggregate one fuel type's generators by their predefined efficiency bins.

    Generators are grouped by ``(efficiency_bin, zone)`` -- the loader-assigned
    vintage bins from :data:`HEAT_RATE_BINS` -- and each group collapses into a
    single capacity-weighted representative. This is the backward-compatible
    aggregation used when no explicit bin count is requested.
    """
    groups: dict[tuple[str, str], list[Generator]] = {}
    for g in generators:
        groups.setdefault((g.efficiency_bin, g.zone), []).append(g)

    result: list[Generator] = []
    for efficiency_bin, zone in sorted(groups):
        units = groups[(efficiency_bin, zone)]
        unit_id = f"{fuel_type}_{efficiency_bin}_{zone}"
        result.append(
            Generator(
                unit_id=unit_id,
                name=unit_id,
                zone=zone,
                fuel_type=fuel_type,
                efficiency_bin=efficiency_bin,
                pmax_mw=sum(u.pmax_mw for u in units),
                pmin_mw=sum(u.pmin_mw for u in units),
                heat_rate=_capacity_weighted(units, "heat_rate"),
                vom=_capacity_weighted(units, "vom"),
                emission_rate_co2=_capacity_weighted(units, "emission_rate_co2"),
                nox_rate=_capacity_weighted(units, "nox_rate"),
                eford=_capacity_weighted(units, "eford"),
                # Preserve the bin's vintage (see aggregate_fleet) so the
                # CCS-retrofit remaining-life screen and learning
                # attribution survive re-aggregation.
                online_year=int(round(_capacity_weighted(units, "online_year"))),
            )
        )
    return result


def aggregate_fleet_by_efficiency(
    generators: list[Generator],
    fuel_type: str,
    n_bins: int | None = None,
) -> list[Generator]:
    """Aggregate generators of one fuel type into efficiency bins.

    If ``n_bins`` is ``None``, use the predefined :data:`HEAT_RATE_BINS`
    vintage bins for this fuel type (backward-compatible default behavior).

    If ``n_bins`` is an integer, ignore :data:`HEAT_RATE_BINS` and instead
    create ``n_bins`` equal-width bins spanning the heat rate range of the
    input generators. Each bin gets:

    * ``heat_rate`` -- capacity-weighted average of generators in the bin,
    * ``pmax_mw`` -- sum of generator capacities in the bin,
    * ``emission_rate_co2`` / ``vom`` / ``nox_rate`` / ``eford`` --
      capacity-weighted averages,
    * ``efficiency_bin`` -- ``f"bin_{i+1}_of_{n_bins}"``.

    This allows fine-grained sensitivity analysis without changing any
    constants -- just set ``config.heat_rate_bin_count``. Note that 10+ bins
    add LP columns and may increase solve time; profile if using 20+ bins.

    Args:
        generators: All generators of this fuel type (assumed one zone).
        fuel_type: Fuel type string (e.g. ``"gas_cc"``).
        n_bins: Number of efficiency bins. ``None`` uses the defaults.

    Returns:
        List of aggregated :class:`Generator` objects, one per non-empty bin.
    """
    if n_bins is None:
        return _aggregate_with_predefined_bins(generators, fuel_type)

    if len(generators) == 0:
        return []

    sorted_gens = sorted(generators, key=lambda g: g.heat_rate)
    hr_min = sorted_gens[0].heat_rate
    hr_max = sorted_gens[-1].heat_rate

    # All generators essentially the same heat rate -- collapse to one bin.
    if hr_max - hr_min < 0.01:
        n_bins = 1

    bin_width = (hr_max - hr_min) / n_bins if n_bins > 1 else 1.0
    bins: list[list[Generator]] = [[] for _ in range(n_bins)]
    for g in sorted_gens:
        if n_bins == 1:
            idx = 0
        else:
            idx = min(int((g.heat_rate - hr_min) / bin_width), n_bins - 1)
        bins[idx].append(g)

    result: list[Generator] = []
    for i, bin_gens in enumerate(bins):
        if not bin_gens:
            continue
        unit_id = f"{fuel_type}_bin{i + 1}of{n_bins}"
        result.append(
            Generator(
                unit_id=unit_id,
                name=unit_id,
                zone=bin_gens[0].zone,
                fuel_type=fuel_type,
                efficiency_bin=f"bin_{i + 1}_of_{n_bins}",
                pmax_mw=sum(g.pmax_mw for g in bin_gens),
                pmin_mw=sum(g.pmin_mw for g in bin_gens),
                heat_rate=_capacity_weighted(bin_gens, "heat_rate"),
                vom=_capacity_weighted(bin_gens, "vom"),
                emission_rate_co2=_capacity_weighted(bin_gens, "emission_rate_co2"),
                nox_rate=_capacity_weighted(bin_gens, "nox_rate"),
                eford=_capacity_weighted(bin_gens, "eford"),
                # Preserve the bin's vintage: dropping it to the Generator
                # default (2000) makes every aggregated CC look near
                # end-of-life, silently disqualifying the whole bin from
                # the CCS-retrofit screen and from learning attribution.
                online_year=int(round(_capacity_weighted(bin_gens, "online_year"))),
            )
        )
    return result


def aggregate_fleet(
    generators: list[Generator], n_bins: int | str | None = None
) -> list[Generator]:
    """Collapse individual generators into representative units.

    With ``n_bins=None`` thermal generators are grouped by
    ``(fuel_type, efficiency_bin, zone)``; each group becomes a single
    :class:`Generator` whose capacity is the group total and whose per-MWh
    attributes are capacity-weighted averages of the group. This shrinks the
    LP from one column per physical unit (200+) to one column per thermal bin
    (~36), the dominant solve-time win.

    With an integer ``n_bins`` the thermal generators of each
    ``(fuel_type, zone)`` group are instead split into ``n_bins`` equal-width
    heat-rate bins (see :func:`aggregate_fleet_by_efficiency`), giving finer
    resolution for carbon-pricing and CCS sensitivity analysis at the cost of
    more LP columns.

    With ``n_bins=0`` or ``n_bins="unit"`` no aggregation is performed: the
    fleet is returned unchanged, one LP column per physical unit. This gives
    full plant-level granularity for calibration and financial analysis.

    Nuclear, hydro and import units pass through unchanged -- they are few
    in number and have distinct characteristics. Wind and solar are not part
    of the thermal fleet handled here, so they are unaffected. A thermal unit
    carrying a scheduled ``retirement_year`` also passes through, so the
    known-retirement mechanism keeps its per-unit retirement dates.

    Args:
        generators: The individual-unit fleet.
        n_bins: Number of equal-width efficiency bins per ``(fuel_type, zone)``
            group. ``None`` uses the predefined vintage bins; ``0`` or
            ``"unit"`` disables aggregation entirely.

    Returns:
        A new fleet list: pass-through units in their original order,
        followed by one representative unit per thermal group.
    """
    # n_bins == 0 / "unit": full unit granularity, no aggregation.
    if n_bins == 0 or n_bins == "unit":
        return list(generators)

    passthrough: list[Generator] = []
    groups: dict[tuple, list[Generator]] = {}
    for g in generators:
        if g.fuel_type not in _AGGREGATABLE_FUELS or g.retirement_year is not None:
            passthrough.append(g)
            continue
        key = (
            (g.fuel_type, g.zone)
            if n_bins is not None
            else (g.fuel_type, g.efficiency_bin, g.zone)
        )
        groups.setdefault(key, []).append(g)

    representatives: list[Generator] = []
    if n_bins is None:
        for key in sorted(groups):
            fuel_type, efficiency_bin, zone = key
            units = groups[key]
            unit_id = f"{fuel_type}_{efficiency_bin}_{zone}"
            representatives.append(
                Generator(
                    unit_id=unit_id,
                    name=unit_id,
                    zone=zone,
                    fuel_type=fuel_type,
                    efficiency_bin=efficiency_bin,
                    pmax_mw=sum(u.pmax_mw for u in units),
                    pmin_mw=sum(u.pmin_mw for u in units),
                    heat_rate=_capacity_weighted(units, "heat_rate"),
                    vom=_capacity_weighted(units, "vom"),
                    emission_rate_co2=_capacity_weighted(units, "emission_rate_co2"),
                    nox_rate=_capacity_weighted(units, "nox_rate"),
                    eford=_capacity_weighted(units, "eford"),
                    # Preserve the bin's vintage (see the per-efficiency
                    # aggregator) so retrofit screens and learning
                    # attribution survive re-aggregation.
                    online_year=int(round(_capacity_weighted(units, "online_year"))),
                )
            )
    else:
        for key in sorted(groups):
            fuel_type, zone = key
            for rep in aggregate_fleet_by_efficiency(groups[key], fuel_type, n_bins):
                # The per-efficiency aggregator names bins within one zone;
                # qualify the id with the zone so cross-zone bins stay unique.
                rep.unit_id = f"{rep.unit_id}_{zone}"
                rep.name = rep.unit_id
                representatives.append(rep)

    return passthrough + representatives


def assemble_mc(
    fleet: FleetArrays,
    fuel_prices: np.ndarray,
    carbon_price: np.ndarray | float,
    nox_price: np.ndarray | float = 0.0,
    **adders: tuple[np.ndarray, np.ndarray],
) -> np.ndarray:
    """Return the ``(n_gen, T)`` marginal cost array for the fleet.

    The marginal cost of each generator in each hour is::

        mc = heat_rate * fuel_price + vom
             + emission_rate * carbon_price
             + nox_rate * nox_price
             + sum(rate * price for each adder)

    ``fuel_prices`` is ``(n_gen, T)`` or broadcastable to it. ``carbon_price``
    and ``nox_price`` may be scalars or ``(T,)`` hourly arrays. ``carbon_price``
    may additionally be a **per-generator** membership-weighted allowance adder
    (``m_zone[zone_idx] * price``, shape ``(n_gen,)`` or ``(n_gen, 1)``) so a
    cap-and-trade program with fractional/partial footprint membership charges
    each generator only its member share (a uniform ``m_zone == 1`` reproduces
    the scalar path bit-for-bit). A bare ``(n_gen,)`` vector is reshaped to a
    column; in this model ``n_gen`` (hundreds) is never equal to ``T`` (8760),
    so the per-generator vs per-hour shapes never collide. Each ``adders``
    keyword value is a ``(generator_rate_array, hourly_price_array)`` pair,
    allowing extra cost terms (e.g. SO2) without changing the signature.
    """
    heat_rate = fleet.heat_rate[:, np.newaxis]
    mc = heat_rate * np.asarray(fuel_prices, dtype=float)
    mc = mc + fleet.vom[:, np.newaxis]
    carbon = np.asarray(carbon_price, dtype=float)
    # A per-generator membership-weighted adder arrives as a length-n_gen
    # vector; reshape to a column so it broadcasts down the T axis (a scalar or
    # (T,) hourly price is left as-is).
    if carbon.ndim == 1 and carbon.shape[0] == fleet.n_gen:
        carbon = carbon[:, np.newaxis]
    mc = mc + fleet.emission_rate[:, np.newaxis] * carbon
    mc = mc + fleet.nox_rate[:, np.newaxis] * np.asarray(nox_price, dtype=float)

    for rate_array, price_array in adders.values():
        rate = np.asarray(rate_array, dtype=float)[:, np.newaxis]
        mc = mc + rate * np.asarray(price_array, dtype=float)

    return mc


from market_sim.data.offer_curves import (  # noqa: E402
    _econ_curve_steps,
    _econ_split_for_group,
    _hr_override,
    _offer_curve_for_group,
    split_coal_tranches,
    split_gas_tranches,
)


def campd_tranche_fuel_frac(
    gen: Generator,
    passthrough_by_supply: "dict[str, float | np.ndarray] | None" = None,
    takeorpay_by_plant: "dict[int, float] | None" = None,
    econ_srmc_bound: bool = False,
) -> "float | np.ndarray":
    """Return the fuel-cost passthrough for one CAMPD tranche generator.

    ``passthrough_by_supply`` maps a coal supply tag (the
    :func:`coal_supply_class` vocabulary — "prb" / "subbituminous" /
    "bituminous" / "lignite" / "waste") to that supply chain's passthrough:
    a scalar (flat) or an ``(T,)`` array (its gas-keyed sigmoid,
    ``fuel.coal_passthrough_by_supply``). Each coal tranche above must-run
    looks up its own tag, so each supply's curve — tuned to its basin, rank
    and delivery economics per ISO — applies only to its own plants. Tags
    without an entry (e.g. unclassified "") pass full fuel cost
    (``1.0``); :func:`apply_coal_tranches` applies the result.

    Must-run tranches (any fuel) pass ``0.0`` by default — their fuel is sunk
    under take-or-pay coal contracts, CHP host-steam obligations or ERCOT RUC,
    so they bid VOM + carbon + NOx only. A passthrough < 1.0 price-takes (an
    already-online unit bids to clear rather than on full marginal cost);
    > 1.0 marks the bid up to suppress over-dispatch.

    ``takeorpay_by_plant`` (set when ``ScenarioConfig.coal_takeorpay_from_data``
    is on) maps ``plant_code → measured contract share`` (EIA-923 Schedule-5
    Purchase Type, :func:`coal_takeorpay_share`). When given, a **coal** must-run
    tranche passes ``1 - share`` of its fuel instead of ``0.0``: only the
    contracted (take-or-pay) fraction is sunk, and the spot remainder bids full
    delivered fuel. ``share = 1.0`` (fully contracted) reproduces the default
    0.0; a plant absent from the map keeps the default 100%-sunk behaviour.

    ``econ_srmc_bound`` (``ScenarioConfig.coal_econ_srmc_bound``): when set,
    a **marginal** coal tranche (unit id ending ``_peak`` or containing
    ``_econ``) has its passthrough clamped to ``>= 1.0`` — its fuel is bought
    at market, so the offer never drops below the plant's full measured
    delivered fuel cost. Committed/must-run bands keep their contracted
    discount; markups above 1.0 are untouched.

    The ``_sync`` synchronization tranche (rebuild step 3a,
    ``ScenarioConfig.coal_sync_srmc_tranche``) bids its **full SRMC** — full
    delivered fuel + VOM + reagents — so it passes ``1.0`` (no discount). It is
    the spot (avoidable-fuel) share of the forced-on coal min-load; the
    contracted share is carried by the fuel-free ``_mustrun`` band beside it,
    sized in :func:`bins_to_fleet` from the same measured contract share (so
    ``takeorpay_by_plant`` is *not* re-applied to ``_mustrun`` in sync mode —
    the runner passes ``None`` there and the default 0.0 fuel-free bid stands).
    """
    if gen.unit_id.endswith("_sync"):
        return 1.0
    if gen.unit_id.endswith("_mustrun"):
        if takeorpay_by_plant is not None and gen.fuel_type == "coal":
            share = takeorpay_by_plant.get(int(gen.plant_code))
            if share is not None:
                return float(1.0 - share)
        return 0.0
    if gen.fuel_type == "coal" and passthrough_by_supply:
        pt = passthrough_by_supply.get(getattr(gen, "coal_supply", ""), 1.0)
        # ScenarioConfig.coal_econ_srmc_bound: a MARGINAL coal tranche
        # (econ*/peak — above the contracted committed band) buys its fuel
        # at market, so its offer may never drop below full measured
        # delivered fuel cost: clamp the supply chain's passthrough to
        # >= 1.0 (markups > 1.0 pass through unchanged). The committed
        # band keeps the take-or-pay/stay-online discount.
        uid = gen.unit_id
        if econ_srmc_bound and (uid.endswith("_peak") or "_econ" in uid):
            if isinstance(pt, np.ndarray):
                return np.maximum(pt, 1.0)
            return max(float(pt), 1.0)
        return pt
    return 1.0


def apply_coal_tranches(
    mc: np.ndarray,
    generators: list[Generator],
    fleet_arrays: FleetArrays,
    fuel_fracs: list[float],
    fuel_prices: np.ndarray,
) -> None:
    """Reduce coal-tranche marginal cost by the sunk (unpassed) fuel fraction.

    For each coal tranche ``g``, the take-or-pay contract makes
    ``1 - fuel_fracs[g]`` of the physical fuel cost (``heat_rate ×
    fuel_price``) sunk, so it is removed from the bid::

        mc[g, t] -= (1 - fuel_fracs[g]) × heat_rate[g] × fuel_price[g, t]

    Tranche 1 (``fuel_frac = 0``) is left bidding at VOM (plus carbon/NOx);
    tranche 3 (``fuel_frac = 1``) is unchanged. VOM, carbon and NOx are never
    discounted — they are incurred per MWh dispatched regardless of the fuel
    contract. ``mc`` is modified in place.

    Args:
        mc: The ``(n_gen, T)`` marginal-cost array, modified in place.
        generators: The generator list aligned row-for-row with ``mc``.
        fleet_arrays: The vectorized fleet, for per-generator heat rate.
        fuel_fracs: Per-generator fuel-cost passthrough from
            :func:`split_coal_tranches`.
        fuel_prices: The ``(n_gen, T)`` delivered fuel price array used to
            assemble ``mc``.
    """
    fuel_prices = np.asarray(fuel_prices, dtype=float)
    for g, gen in enumerate(generators):
        # Discount the fuel term for any generator with a take-or-pay
        # contract or host-steam obligation that sinks part of its fuel
        # cost (coal tranches; CAMPD must-run tranches across all fuels).
        # fuel_fracs[g] is a scalar, or an (T,) array for a gas-keyed PRB
        # passthrough — an hourly-varying frac applies elementwise (and a
        # value > 1.0 marks the bid up).
        ff = fuel_fracs[g]
        if np.isscalar(ff) and ff >= 1.0:
            continue
        fuel_cost = fleet_arrays.heat_rate[g] * fuel_prices[g, :]
        mc[g, :] -= (1.0 - np.asarray(ff, dtype=float)) * fuel_cost


# ---------------------------------------------------------------------------
# Fleet loading from EIA-860 / eGRID CSVs
# ---------------------------------------------------------------------------

# Maps many possible source column names (lower-cased, spaces → underscores)
# to the canonical names the loader works with. Covers the EIA-860 API and
# eGRID plant/unit files.
_COLUMN_ALIASES: dict[str, set[str]] = {
    "plant_id": {
        "plant_id",
        "plantid",
        "plant_code",
        "plantcode",
        "oris",
        "orispl",
        "plant_id_eia",
        "plantid_eia",
    },
    "generator_id": {
        "generator_id",
        "generatorid",
        "gen_id",
        "genid",
        "unit_id",
        "unitid",
    },
    "plant_name": {"plant_name", "plantname", "pname", "name"},
    "state": {"state", "plant_state", "plantstate", "pstatabb", "plstatabb"},
    "balancing_authority_code": {
        "balancing_authority_code",
        "balancingauthoritycode",
        "bacode",
        "ba_code",
        "balancing_authority",
        "ba",
    },
    "technology": {
        "technology",
        "technology_description",
        "technologydescription",
        "tech",
    },
    "energy_source": {
        "energy_source",
        "energy_source_code",
        "energy_source_code_1",
        "energysourcecode",
        "fuel",
        "plprmfl",
        "plfuelct",
        "fuel_type",
    },
    "prime_mover": {
        "prime_mover",
        "prime_mover_code",
        "primemover",
        "primemovercode",
    },
    "nameplate_capacity_mw": {
        "nameplate_capacity_mw",
        "nameplate_capacity",
        "nameplatecapacity",
        "namepcap",
        "capacity_mw",
        "capacity",
    },
    "net_summer_capacity_mw": {
        "net_summer_capacity_mw",
        "net_summer_capacity",
        "netsummercapacity",
        "summer_capacity_mw",
        "summercapacity",
    },
    "operating_year": {
        "operating_year",
        "operatingyear",
        "opyr",
        "operating_date",
        "operatingdate",
    },
    "operating_month": {
        "operating_month",
        "operatingmonth",
        "opmonth",
    },
    "planned_retirement_year": {
        "planned_retirement_year",
        "plannedretirementyear",
        "planned_retirement_date",
        "plannedretirement",
        "retirement_year",
        "retirementyear",
    },
    "planned_retirement_month": {
        "planned_retirement_month",
        "plannedretirementmonth",
        "retirement_month",
        "retirementmonth",
    },
    "status": {"status", "statusdescription", "status_description"},
    "heat_rate": {
        "heat_rate",
        "heatrate",
        "plhtrt",
        "heat_rate_mmbtu_mwh",
        "unit_heat_rate",
    },
}

# Nuclear plants whose ISO zone is known explicitly. Keyed by a lower-cased
# substring of the plant name.
_NUCLEAR_ZONE_OVERRIDES: dict[str, str] = {
    "comanche peak": "North",
    "south texas": "South",
    "diablo canyon": "NP15",  # San Luis Obispo, NP15 coast (north of Path 26)
}

# Energy-source codes (EIA-860 / eGRID PLPRMFL) that indicate coal steam.
_COAL_ENERGY_SOURCES = {"SUB", "BIT", "LIG", "ANT", "RC", "WC"}
# Oil and biomass energy-source codes come from the canonical taxonomy so the
# model fleet and the EIA-923 benchmark bucket a plant identically. Petroleum
# coke (PC) is excluded from oil there (it falls to the residual OTHER bucket).
_OIL_ENERGY_SOURCES = OIL_ENERGY_SOURCES
_BIOMASS_ENERGY_SOURCES = BIOMASS_ENERGY_SOURCES
# Prime-mover codes that indicate a combined-cycle configuration.
_CC_PRIME_MOVERS = {"CC", "CA", "CT", "CS"}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Rename a generator DataFrame's columns to canonical loader names.

    Handles the differing column names of the EIA-860 API and eGRID
    extracts. Unknown columns are left untouched; duplicate canonical
    columns keep the first occurrence.

    Args:
        df: A raw generator DataFrame.

    Returns:
        The DataFrame with recognized columns renamed.
    """
    alias_to_canon: dict[str, str] = {}
    for canon, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            alias_to_canon[alias] = canon

    rename: dict[str, str] = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        if key in alias_to_canon:
            rename[col] = alias_to_canon[key]

    df = df.rename(columns=rename)
    return df.loc[:, ~df.columns.duplicated()]


def _to_float(value: object) -> float | None:
    """Coerce ``value`` to a float, returning ``None`` for blanks or NaN."""
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def _to_year(value: object) -> int | None:
    """Extract a four-digit year from an int, float or date-like string."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value != value:  # NaN
            return None
        year = int(value)
        return year if year > 0 else None
    text = str(value).strip()
    match = re.search(r"(?:19|20)\d{2}", text)
    return int(match.group(0)) if match else None


def _to_month(value: object) -> int | None:
    """Extract a calendar month (1-12) from an int, float or string.

    Returns ``None`` when the value is missing or out of range, letting the
    caller fall back to its default (January for online, December for retire).
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        if value != value:  # NaN
            return None
        month = int(value)
        return month if 1 <= month <= 12 else None
    text = str(value).strip()
    if not text:
        return None
    try:
        month = int(float(text))
    except ValueError:
        return None
    return month if 1 <= month <= 12 else None


# Model fuel type -> historic-outage plant group, for EIA-860 fleets (every
# non-ERCOT ISO). Mirrors the coal/CC/gas-steam classes the overlay's
# QUALIFYING_PLANT_GROUPS filters on; gas CTs map to CT_PEAKER, which the
# overlay deliberately excludes (peakers run economically, not on a
# sustained-outage schedule), and oil/biomass/nuclear carry no group so they
# keep the statistical availability model. ERCOT is unaffected: its fleet
# comes from bins_to_fleet, which sets plant_group directly.
_EIA860_PLANT_GROUP_BY_FUEL: dict[str, str] = {
    "coal": "COAL",
    "gas_cc": "CC_REGULAR",
    "gas_cc_ccs": "CC_REGULAR",
    "gas_ct": "CT_PEAKER",
    "gas_st": "ST_GAS",
}

# Gas group -> its combined-heat-and-power variant, applied when EIA-860 flags
# the plant as CHP. CHP cogens run must-run on host steam, so they bid/dispatch
# differently than the merchant variants.
_CHP_GROUP_FOR: dict[str, str] = {
    "CC_REGULAR": "CC_CHP",
    "CT_PEAKER": "CT_CHP",
    "ST_GAS": "ST_CHP",
}

# The six gas dispatch classes the canonical classifier may return for a gas
# unit; a result outside this set (OTHER) falls back to the fuel-type group.
_EIA860_GAS_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"}
)


def _map_fuel_type(
    technology: object, energy_source: object, prime_mover: object
) -> str | None:
    """Map raw technology / fuel / prime-mover codes to a model fuel type.

    Returns one of ``gas_cc``, ``gas_ct``, ``coal``, ``nuclear``, ``oil`` or
    ``biomass``, or ``None`` for wind, solar, hydro and other non-thermal
    resources, which are handled elsewhere.
    """
    tech = str(technology or "").strip().lower()
    source = str(energy_source or "").strip().upper()
    mover = str(prime_mover or "").strip().upper()

    if source == "NUC" or "nuclear" in tech:
        return "nuclear"
    if source in _COAL_ENERGY_SOURCES or "coal" in tech:
        return "coal"
    if source == "NG" or "natural gas" in tech:
        if "combined cycle" in tech or mover in _CC_PRIME_MOVERS:
            return "gas_cc"
        return "gas_ct"
    if source in _OIL_ENERGY_SOURCES or "petroleum" in tech:
        # Oil / distillate / residual units — peakers (mainly NYISO/ISO-NE)
        # and legacy oil steam — priced off the distillate/residual curve.
        return "oil"
    if (
        source in _BIOMASS_ENERGY_SOURCES
        or "biomass" in tech
        or "wood" in tech
        or "landfill" in tech
        or "municipal" in tech
    ):
        return "biomass"
    return None


def _efficiency_bin(fuel_type: str, operating_year: int) -> str:
    """Return the efficiency bin for a unit given its fuel and vintage."""
    if fuel_type == "gas_cc":
        if operating_year >= 2015:
            return "h_class"
        if operating_year >= 2005:
            return "f_class"
        return "older"
    if fuel_type == "gas_ct":
        if operating_year >= 2010:
            return "aero"
        if operating_year >= 2000:
            return "frame"
        return "older"
    if fuel_type == "coal":
        if operating_year >= 2000:
            return "supercritical"
        if operating_year >= 1985:
            return "subcritical"
        return "older"
    return "default"


def _nuclear_zone_override(plant_name: str) -> str | None:
    """Return an explicit zone for a known nuclear plant, else ``None``."""
    name = plant_name.lower()
    for substring, zone in _NUCLEAR_ZONE_OVERRIDES.items():
        if substring in name:
            return zone
    return None


def _zone_for_index(index: int, n: int, zone_shares: list[tuple[str, float]]) -> str:
    """Pick a zone for generator ``index`` of ``n`` by cumulative load share."""
    pos = (index + 0.5) / n
    cumulative = 0.0
    for name, share in zone_shares:
        cumulative += share
        if pos <= cumulative:
            return name
    return zone_shares[-1][0]


def _assign_zones(
    records: list[dict], iso: str, iso_config: ISOConfig | None
) -> list[str]:
    """Assign each generator record a zone using eGRID plant geography.

    Uses lat/lon and FIPS county from eGRID 2023 to place each plant in
    the correct model zone. Falls back to proportional allocation if the
    eGRID data is unavailable.
    """
    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        logger.warning(
            "eGRID zone lookup failed for %s — using proportional fallback",
            iso,
        )
        return _assign_zones_proportional(records, iso, iso_config)

    if not zone_lookup:
        return _assign_zones_proportional(records, iso, iso_config)

    # Defensive fallback for plants whose ORIS code is absent from eGRID
    # (e.g. units commissioned after the eGRID 2023 vintage): the ISO's
    # pinned default zone (zone_assignment._LARGEST_ZONE — for MISO the
    # pinned Midwest default, NOT the literal largest share, which flipped
    # to MISO-South at the six-zone refinement), falling back to the
    # largest-load-share zone for ISOs without a pin.
    from market_sim.data.zone_assignment import _LARGEST_ZONE

    if iso in _LARGEST_ZONE:
        fallback_zone = _LARGEST_ZONE[iso]
    elif iso_config is not None and iso_config.zones:
        fallback_zone = max(iso_config.zones, key=lambda z: z.load_share).name
    else:
        fallback_zone = iso

    zones: list[str] = []
    missing = 0
    for rec in records:
        oris = _record_oris(rec)
        zone = zone_lookup.get(oris) if oris is not None else None
        if zone is None:
            zone = fallback_zone
            missing += 1
        zones.append(zone)

    if missing:
        logger.warning(
            "%d of %d %s generators not in eGRID lookup — assigned fallback zone",
            missing,
            len(records),
            iso,
        )
    return zones


def _record_oris(rec: dict) -> int | None:
    """Return the integer ORIS plant code carried by a generator record."""
    raw = rec.get("plant_id", rec.get("oris"))
    try:
        return int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _assign_zones_proportional(
    records: list[dict], iso: str, iso_config: ISOConfig | None
) -> list[str]:
    """Assign each generator record a zone by proportional allocation.

    Non-nuclear units are spread across the ISO's load zones in proportion
    to each zone's ``load_share``; zones with zero load share (such as
    CAISO's ``WECC_import`` import node) never receive a thermal generator.
    Nuclear units use an explicit zone where the plant is known, otherwise
    the largest-load-share zone. If no ``iso_config`` is available, every
    generator is placed in a single zone named after the ISO.

    This is the fallback used when eGRID geographic data is unavailable.
    """
    if iso_config is None:
        return [iso] * len(records)

    zone_shares = [
        (z.name, z.load_share) for z in iso_config.zones if z.load_share > 0.0
    ]
    if not zone_shares:
        return [iso_config.zones[0].name] * len(records)

    total = sum(share for _, share in zone_shares)
    zone_shares = [(name, share / total) for name, share in zone_shares]
    valid_zones = {name for name, _ in zone_shares}
    largest_zone = max(zone_shares, key=lambda item: item[1])[0]

    non_nuclear = [i for i, rec in enumerate(records) if rec["fuel_type"] != "nuclear"]
    zones: list[str | None] = [None] * len(records)
    for position, idx in enumerate(non_nuclear):
        zones[idx] = _zone_for_index(position, len(non_nuclear), zone_shares)

    for idx, rec in enumerate(records):
        if rec["fuel_type"] != "nuclear":
            continue
        override = _nuclear_zone_override(rec["name"])
        zones[idx] = override if override in valid_zones else largest_zone

    return [zone for zone in zones if zone is not None]


def _rows_to_generators(
    df: pd.DataFrame, iso: str, iso_config: ISOConfig | None
) -> list[Generator]:
    """Convert a normalized generator DataFrame into :class:`Generator` objects.

    Rows are filtered to operating units, mapped to a model fuel type
    (skipping wind/solar/hydro), assigned an efficiency bin by vintage, and
    given heat rate, emission, VOM and outage parameters from
    ``config/constants.py``.
    """
    if "status" in df.columns:
        status = df["status"].astype(str).str.strip().str.upper()
        df = df[status == "OP"]

    records: list[dict] = []
    for row in df.itertuples(index=False):
        data = row._asdict()
        fuel_type = _map_fuel_type(
            data.get("technology"),
            data.get("energy_source"),
            data.get("prime_mover"),
        )
        if fuel_type is None:
            continue

        pmax = _to_float(data.get("net_summer_capacity_mw"))
        if pmax is None or pmax <= 0.0:
            pmax = _to_float(data.get("nameplate_capacity_mw"))
        if pmax is None or pmax <= 0.0:
            continue

        operating_year = _to_year(data.get("operating_year")) or 2000
        operating_month = _to_month(data.get("operating_month")) or 1
        retirement_month = _to_month(data.get("planned_retirement_month"))
        ebin = _efficiency_bin(fuel_type, operating_year)

        # Prefer a unit-level heat rate (e.g. from eGRID) when present.
        heat_rate = _to_float(data.get("heat_rate"))
        if heat_rate is None or heat_rate <= 0.0:
            heat_rate = HEAT_RATE_BINS.get(fuel_type, {}).get(ebin, 0.0)

        if fuel_type == "nuclear":
            pmin = 0.9 * pmax
        elif fuel_type == "coal":
            pmin = 0.4 * pmax
        else:
            pmin = 0.0

        plant_id = data.get("plant_id")
        generator_id = data.get("generator_id")
        plant_name = str(data.get("plant_name") or f"{iso} unit")

        # plant_code keys the EIA-923 monthly fuel-cost lookup, and
        # plant_group keys the historic-outage overlay's coal/CC filter;
        # both are unset on the EIA-860 fleet until here, so an ISO loaded
        # this way (every non-ERCOT ISO) saw neither its plant-specific
        # fuel cost nor its measured outages. state feeds the resolver's
        # state-level "nearby plant" fuel-cost fallback.
        plant_code = int(_to_float(plant_id) or 0)
        state = str(data.get("state") or "").strip().upper()

        # Plant group (dispatch class). Gas units are classed by the SAME
        # canonical classifier the EIA-923 benchmark uses
        # (:func:`market_sim.config.plant_taxonomy.classify_plant`), so an NG
        # unit's class — CC / CT / steam, merchant vs CHP — is identical by
        # construction across the model fleet and the benchmark. Combined-heat-
        # and-power cogens (EIA-860 "Associated with Combined Heat and Power
        # System" = Y) take the cogen variant; gas steam boilers resolve to
        # ST_GAS rather than being folded into CT_PEAKER. Coal keeps the bare
        # ``COAL`` group (its supply rank is split downstream from
        # :func:`coal_supply_class`); nuclear / oil / biomass carry no group and
        # keep the statistical availability model.
        chp_flag = str(data.get("chp") or "").strip().upper().startswith("Y")
        if fuel_type == "coal":
            group = "COAL"
        elif fuel_type in ("gas_cc", "gas_cc_ccs", "gas_ct"):
            group = classify_plant(
                data.get("energy_source"),
                data.get("prime_mover"),
                chp_flag,
                plant_code,
            )
            if group not in _EIA860_GAS_GROUPS:
                # Non-NG gas code (e.g. blast-furnace / other gas) the canonical
                # classifier returns OTHER for: fall back to the fuel-type group
                # so the unit still classes as gas rather than dropping out.
                group = _EIA860_PLANT_GROUP_BY_FUEL.get(fuel_type, "")
                if chp_flag:
                    group = _CHP_GROUP_FOR.get(group, group)
        else:
            group = ""

        records.append(
            {
                "plant_id": plant_id,
                "plant_code": plant_code,
                "unit_id": f"{plant_id}_{generator_id}",
                "name": plant_name,
                "fuel_type": fuel_type,
                "plant_group": group,
                "state": state,
                "efficiency_bin": ebin,
                "pmax_mw": pmax,
                "pmin_mw": pmin,
                "heat_rate": heat_rate,
                "vom": VOM.get(fuel_type, 0.0),
                "emission_rate_co2": CO2_RATES.get(fuel_type, {}).get(ebin, 0.0),
                "nox_rate": NOX_RATES.get(fuel_type, 0.0),
                "eford": EFORD.get(fuel_type, 0.05),
                "online_year": operating_year,
                "online_month": operating_month,
                "retirement_year": _to_year(data.get("planned_retirement_year")),
                "retirement_month": retirement_month,
                "is_must_run": fuel_type == "nuclear",
            }
        )

    zones = _assign_zones(records, iso, iso_config)
    return [
        Generator(
            zone=zone,
            **{k: v for k, v in rec.items() if k != "plant_id"},
        )
        for rec, zone in zip(records, zones)
    ]


from market_sim.data.chp import (  # noqa: E402
    _chp_by_plant,
    _correct_caiso_chp_steam_credit_hr,
    chp_btm_pct,
    chp_class_netgen_mwh,
    chp_pmin_cf,
)


def dual_fuel_plant_groups(
    eia860_dir: Path | None = None,
) -> frozenset[tuple[int, str]]:
    """Return ``(plant_code, plant_group)`` pairs of oil/gas dual-fuel units.

    Resolves the EIA-860 directory through :func:`paths.active_eia860_dir` when
    not given (so a year-matched vintage switch is honored) and defers to the
    directory-keyed cache below.
    """
    return _dual_fuel_plant_groups(
        Path(eia860_dir) if eia860_dir is not None else active_eia860_dir()
    )


@lru_cache(maxsize=4)
def _dual_fuel_plant_groups(
    eia860_dir: Path,
) -> frozenset[tuple[int, str]]:
    """Cached ``(plant_code, plant_group)`` dual-fuel pairs for one directory.

    Reads the EIA-860 Multifuel schedule (:data:`EIA_860_MULTIFUEL_PARQUET_NAME`)
    and flags every operable gas-primary unit ("Energy Source 1" = ``NG``)
    whose "Switch Between Oil and Natural Gas?" field is ``Y`` — the units
    that physically carry oil backup (typically "Energy Source 2" = ``DFO`` /
    ``RFO``) and can switch when gas spikes past oil parity. Each flagged
    unit is classed with the same canonical gas classifier the fleet loaders
    use (:func:`~market_sim.config.plant_taxonomy.classify_plant`), so the
    returned keys line up with both the raw EIA-860 per-unit fleet and the
    per-plant tranche fleet (:func:`fleet_to_bins` / :func:`bins_to_fleet`),
    whose generators carry ``plant_code`` + ``plant_group``.

    Oil-primary switchers are excluded: they are already modeled as ``oil``
    units paying the oil price. Returns an empty set when the multifuel
    parquet is absent, so fleets without the EIA-860 extract are unchanged.
    """
    path = Path(eia860_dir) / EIA_860_MULTIFUEL_PARQUET_NAME
    if not path.exists():
        return frozenset()
    try:
        raw = pd.read_parquet(
            path,
            columns=[
                "Plant Code",
                "Energy Source 1",
                "Prime Mover",
                "Switch Between Oil and Natural Gas?",
            ],
        )
    except Exception:
        logger.warning(
            "EIA-860 multifuel parquet at %s is unreadable — "
            "no dual-fuel units flagged",
            path,
        )
        return frozenset()

    chp = _chp_by_plant(Path(eia860_dir))
    pairs: set[tuple[int, str]] = set()
    for row in raw.itertuples(index=False):
        source = str(row[1] or "").strip().upper()
        switch = str(row[3] or "").strip().upper()
        if source != "NG" or not switch.startswith("Y"):
            continue
        try:
            plant_code = int(row[0])
        except (TypeError, ValueError):
            continue
        chp_flag = str(chp.get(plant_code, "N")).startswith("Y")
        group = classify_plant(source, row[2], chp_flag, plant_code)
        if group not in _EIA860_GAS_GROUPS:
            # Mirror _rows_to_generators: an exotic prime mover the canonical
            # classifier returns OTHER for falls back to the fuel-type group
            # (+ CHP variant), so the key matches the fleet's grouping.
            fuel_type = _map_fuel_type(None, source, row[2])
            group = _EIA860_PLANT_GROUP_BY_FUEL.get(fuel_type or "", "")
            if chp_flag:
                group = _CHP_GROUP_FOR.get(group, group)
        if group:
            pairs.add((plant_code, group))
    logger.info(
        "EIA-860 multifuel: %d (plant, group) dual-fuel gas keys flagged",
        len(pairs),
    )
    return frozenset(pairs)


def _load_fleet_from_parquet(
    parquet_path: Path,
    iso: str,
    iso_config: ISOConfig | None,
    year: int | None = None,
) -> list[Generator] | None:
    """Load an ISO's fleet from the committed EIA-860 generator parquet.

    The parquet holds real generators for all seven wholesale markets; rows
    are filtered to the ISO via their ``balancing_authority_code``. Returns
    ``None`` when the parquet is missing or yields no thermal generators.
    """
    if not parquet_path.exists():
        return None

    df = _normalize_columns(pd.read_parquet(parquet_path))
    ba_code = ISO_TO_BA_CODE.get(iso)
    if ba_code is not None and "balancing_authority_code" in df.columns:
        ba = df["balancing_authority_code"].astype(str).str.strip()
        df = df[ba == ba_code]

    # Join the plant-level CHP flag (dropped from the processed generators
    # parquet) from the raw EIA-860 operable sheet, so gas cogens are grouped
    # CC_CHP / CT_CHP / ST_CHP. A plant is CHP if any of its units is flagged.
    # ``year`` selects that vintage's CHP designation when the per-year lookup
    # is available (else the latest committed snapshot).
    df = df.copy()
    df["chp"] = df["plant_id"].map(_chp_by_plant(parquet_path.parent, year)).fillna("N")

    generators = _rows_to_generators(df, iso, iso_config)
    if not generators:
        logger.warning("EIA-860 parquet has no generators for %s", iso)
        return None

    logger.info(
        "Loaded %s fleet from EIA-860 parquet (%d generators)",
        iso,
        len(generators),
    )
    return generators


# The clean ``fleet`` schema folds the raw EIA-860 energy-source code into the
# canonical ``fuel`` bucket (coal/gas/nuclear/oil/biomass/hydro/wind/solar/...).
# :func:`_map_fuel_type` and :func:`classify_plant` still want an energy-source
# *code* to split NG into CC/CT/ST and to confirm coal/nuclear/oil/biomass, so we
# round-trip the bucket back to a representative code. The exact sub-code does
# not matter: it only has to land each unit in the right model class (coal rank,
# for instance, is re-derived downstream from the plant code, not this proxy).
# NOTE: the dropped energy-source code is one of several attributes the frozen
# clean fleet schema does not carry (alongside the CHP flag, operating *month*,
# planned retirement, state and unit heat rate). The CHP flag is bridged from the
# raw EIA-860 operable sheet below exactly as the raw parquet loader does; the
# rest fall back to model defaults. Recovering them through the clean seam would
# need a fleet-schema contract change (raise one — do not edit the frozen YAML).
_CLEAN_FUEL_TO_ENERGY_SOURCE: dict[str, str] = {
    "gas": "NG",
    "coal": "BIT",
    "nuclear": "NUC",
    "oil": "DFO",
    "biomass": "WDS",
    "hydro": "WAT",
    "wind": "WND",
    "solar": "SUN",
}


def _clean_fleet_to_normalized(
    df_clean: pd.DataFrame, eia860_dir: Path, year: int | None
) -> pd.DataFrame:
    """Adapt a clean ``fleet`` frame to the raw loader's normalized columns.

    Maps the canonical schema columns (``unit_id`` -> ``generator_id``,
    ``summer_capacity_mw`` -> ``net_summer_capacity_mw``, ``fuel`` ->
    a representative ``energy_source`` code) onto exactly the columns
    :func:`_rows_to_generators` consumes, so the clean and raw paths share the
    *same* Generator-construction logic (and therefore agree by construction —
    see ``tests/test_consume_fleet.py``). The clean fleet is operable-only, so
    ``status`` is synthesized as ``"OP"``; the plant-level CHP flag (not in the
    clean schema) is joined from the raw EIA-860 operable sheet via
    :func:`_chp_by_plant`, matching the raw parquet loader.
    """
    df = pd.DataFrame(
        {
            "plant_id": df_clean["plant_id"],
            "generator_id": df_clean["unit_id"].astype("string"),
            "plant_name": df_clean["plant_name"],
            "technology": df_clean["technology"],
            "prime_mover": df_clean["prime_mover"],
            "energy_source": df_clean["fuel"].map(_CLEAN_FUEL_TO_ENERGY_SOURCE),
            "nameplate_capacity_mw": df_clean["nameplate_capacity_mw"],
            "net_summer_capacity_mw": df_clean["summer_capacity_mw"],
            "operating_year": df_clean["operating_year"],
            "status": "OP",
        }
    )
    df["chp"] = df["plant_id"].map(_chp_by_plant(eia860_dir, year)).fillna("N")
    return df


def _load_fleet_from_clean(
    iso: str,
    iso_config: ISOConfig | None,
    data_dir: Path,
    year: int | None = None,
) -> list[Generator] | None:
    """Load an ISO's fleet from the curated clean ``fleet`` registry.

    The clean counterpart of :func:`_load_fleet_from_parquet`: reads
    ``clean_io.read_clean("fleet", year=<vintage>)`` for the vintage the active
    EIA-860 directory selects (:func:`_clean_fleet_year`), filters to the ISO via
    the curated ``iso`` column, adapts the canonical columns to the loader's
    normalized frame and runs the shared :func:`_rows_to_generators`. Returns
    ``None`` when the slice yields no thermal generators. Raises
    ``FileNotFoundError`` (with a regenerate hint) if the clean partition is
    absent — regenerate it with ``scripts/regenerate_clean.py fleet``.
    """
    partition_year = _clean_fleet_year(data_dir)
    df = _read_clean("fleet", year=partition_year)
    if "iso" in df.columns:
        df = df[df["iso"].astype("string").str.strip() == iso]
    if df.empty:
        logger.warning("clean fleet (year %d) has no rows for %s", partition_year, iso)
        return None

    normalized = _clean_fleet_to_normalized(df.copy(), data_dir, year)
    generators = _rows_to_generators(normalized, iso, iso_config)
    if not generators:
        logger.warning(
            "clean fleet (year %d) has no generators for %s", partition_year, iso
        )
        return None

    logger.info(
        "Loaded %s fleet from clean fleet registry, vintage %d (%d generators)",
        iso,
        partition_year,
        len(generators),
    )
    return generators


def _binned_fleet_frame(generators: list[Generator]) -> pd.DataFrame:
    """Return the plant-level binned fleet as a DataFrame.

    One row per physical generator, exposing the efficiency bin and the
    cost/outage attributes the loader assigned from its fuel and vintage.
    The ``plant_id`` is recovered from each unit's ``plant_id_generatorid``
    identifier.
    """
    rows = [
        {
            "plant_id": g.unit_id.split("_", 1)[0],
            "plant_name": g.name,
            "fuel_type": g.fuel_type,
            "efficiency_bin": g.efficiency_bin,
            "zone": g.zone,
            "pmax_mw": g.pmax_mw,
            "pmin_mw": g.pmin_mw,
            "heat_rate": g.heat_rate,
            "vom": g.vom,
            "emission_rate_co2": g.emission_rate_co2,
            "nox_rate": g.nox_rate,
            "eford": g.eford,
            "online_year": g.online_year,
            "retirement_year": g.retirement_year,
        }
        for g in generators
    ]
    df = pd.DataFrame(rows, columns=BINNED_FLEET_COLUMNS)
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce").astype("Int64")
    df["retirement_year"] = df["retirement_year"].astype("Int64")
    return df


def _cache_binned_fleet(
    iso: str, generators: list[Generator], source: Path | None
) -> None:
    """Write the binned-fleet parquet for ``iso``, skipping a current cache.

    The parquet is regenerated only when no cache exists or its source file
    is newer than the cached copy. It is a side output for inspection and
    traceability -- never an input to dispatch.
    """
    cache_path = PROCESSED_DIR / f"{iso.lower()}_fleet_binned.parquet"
    if (
        cache_path.exists()
        and source is not None
        and cache_path.stat().st_mtime >= source.stat().st_mtime
    ):
        logger.info(
            "Binned fleet cache for %s is up to date — loaded from %s",
            iso,
            cache_path.name,
        )
        return

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    _binned_fleet_frame(generators).to_parquet(cache_path, index=False)
    logger.info(
        "Rebuilt binned fleet cache for %s — %d plants → %s",
        iso,
        len(generators),
        cache_path.name,
    )


def load_binned_fleet(iso: str) -> pd.DataFrame:
    """Return the cached plant-level binned fleet for an ISO.

    Reads ``data/raw/_processed-legacy/{iso}_fleet_binned.parquet`` written by
    :func:`load_fleet_from_csv`, exposing the efficiency-bin assignment of
    every physical generator for analysis without re-parsing the raw
    EIA-860 data.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.

    Returns:
        The binned fleet as a DataFrame with :data:`BINNED_FLEET_COLUMNS`.

    Raises:
        FileNotFoundError: If the cache has not been built yet (call
            :func:`load_fleet_from_csv` for the ISO first).
    """
    cache_path = PROCESSED_DIR / f"{iso.lower()}_fleet_binned.parquet"
    if not cache_path.exists():
        raise FileNotFoundError(
            f"No binned fleet cache for {iso}; run load_fleet_from_csv first"
        )
    return pd.read_parquet(cache_path)


def load_fleet_from_csv(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
    year: int | None = None,
) -> list[Generator]:
    """Load an ISO's thermal generation fleet.

    Resolves the fleet from the first available source:

    1. ``generators_{iso}.csv`` in the EIA-860 directory (per-ISO override);
    2. the committed real EIA-860 generator parquet
       (:data:`EIA_860_PARQUET_NAME`), filtered to the ISO.

    Wind, solar and hydro are skipped (handled by ``renewables.py``).

    As a side output, the plant-level binned fleet is cached to
    ``data/raw/_processed-legacy/{iso}_fleet_binned.parquet`` for later inspection
    (see :func:`load_binned_fleet`); it is not consumed by dispatch.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        iso_config: Topology configuration supplying zone load shares. If
            ``None``, it is fetched via :func:`get_iso_config` when the ISO
            is known; ISOs without a config get a single ISO-named zone.
        data_dir: Directory holding the EIA-860 data. Defaults to
            ``data/raw/eia-860``.
        year: Optional backcast year. When set and the per-year CHP lookup is
            present, gas cogens are bucketed with THAT year's EIA-860 CHP
            designation rather than the latest committed snapshot's (see
            :func:`_chp_by_plant`). ``None`` keeps the snapshot vintage.

    Returns:
        The ISO's thermal fleet as a list of :class:`Generator` objects.

    Raises:
        FileNotFoundError: If neither the per-ISO CSV override nor the
            EIA-860 generator parquet yields a fleet for the ISO.
    """
    iso = iso.upper()
    if data_dir is None:
        data_dir = active_eia860_dir()
    data_dir = Path(data_dir)
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    csv_path = data_dir / f"generators_{iso.lower()}.csv"
    source: Path | None
    if csv_path.exists():
        # Per-ISO override CSV always wins (an explicit manual escape hatch),
        # regardless of the clean seam.
        df = _normalize_columns(pd.read_csv(csv_path))
        generators = _rows_to_generators(df, iso, iso_config)
        source = csv_path
        logger.info(
            "Loaded %s fleet from EIA-860 CSV (%d generators)",
            iso,
            len(generators),
        )
    elif _use_clean():
        # Opt-in clean seam: source fleet attributes from data/clean instead of
        # the raw generator parquet. ``source`` is left None so the
        # data/raw/_processed-legacy binned-fleet side cache is NOT written here
        # (the clean path must not mutate data/raw).
        from_clean = _load_fleet_from_clean(iso, iso_config, data_dir, year)
        if from_clean is None:
            raise FileNotFoundError(
                f"No clean fleet generators for {iso} "
                f"(vintage {_clean_fleet_year(data_dir)}); regenerate with "
                "`python scripts/regenerate_clean.py fleet`"
            )
        return from_clean
    else:
        parquet_path = data_dir / EIA_860_PARQUET_NAME
        from_parquet = _load_fleet_from_parquet(parquet_path, iso, iso_config, year)
        if from_parquet is None:
            raise FileNotFoundError(
                f"No EIA-860 data for {iso}: expected a per-ISO override "
                f"CSV at {csv_path} or the generator parquet at "
                f"{parquet_path}"
            )
        generators = from_parquet
        source = parquet_path

    _correct_mixed_facility_steam_hr(generators)
    _correct_caiso_chp_steam_credit_hr(generators, iso)
    _cache_binned_fleet(iso, generators, source)
    return generators


def _correct_mixed_facility_steam_hr(generators: list[Generator]) -> None:
    """Reassign the steam-unit heat rate at mixed CC+ST facilities (in place).

    See :data:`MIXED_FACILITY_STEAM_HR`: at a combined CC+ST plant the single
    plant-level EIA-923 heat rate blends the efficient CC with the legacy steam
    turbine, so the steam units inherit a too-low (CC-influenced) heat rate. This
    lifts only the steam (``ST_GAS``) units of a listed plant to the steam-class
    value, and only when their current heat rate is *below* it (so a correctly
    metered steam unit is never lowered). The CC rows keep their measured blend.
    """
    for gen in generators:
        target = MIXED_FACILITY_STEAM_HR.get(int(gen.plant_code))
        if (
            target is not None
            and gen.plant_group == "ST_GAS"
            and gen.heat_rate < target
        ):
            gen.heat_rate = target


def load_retired_within_window(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
    year: int | None = None,
) -> list[Generator]:
    """Load whole-plant exits that retired mid-backcast for an ISO.

    The committed operable EIA-860 snapshot is a single recent vintage, so a
    plant that ran through part of the backcast window and retired before that
    vintage (e.g. Mystic, plant 1588 — a ~1.4 GW CC active through 2023 that
    retired mid-2024) is absent from *every* modeled year. The COD ramp can
    only age out a unit it is given, so this injects those units into the
    fleet; the ramp (keyed on the same plant code via
    :func:`market_sim.data.cod_ramp.load_cod_map`, which unions the same
    retiree record) then dispatches each through its real retirement month and
    zeros it after.

    Reads :data:`EIA_860_RETIRED_WINDOW_PARQUET_NAME` (canonical fleet schema,
    ``status`` = OP), filters to the ISO's balancing authority, and builds
    :class:`Generator` objects exactly as the operable fleet loader does (zones
    from eGRID geography, CHP flag joined from the operable sheet). Returns an
    empty list when the parquet is absent.

    **Backcast-mode only** — the mirror of :func:`load_planned_additions`
    (forecast). A forecast solves a forward year whose snapshot must not carry
    a unit that has already retired, so callers gate this on
    ``config.mode == "backcast"``.

    Resolves the EIA-860 directory through :func:`paths.active_eia860_dir`
    (honoring a ``ScenarioConfig.eia860_vintage_year`` switch). A year-matched
    native vintage carries its within-window exits in its own operable file and
    ships no retiree parquet, so this returns an empty list there — the operable
    fleet already has them, and injecting again would double-count.
    """
    iso = iso.upper()
    data_dir = active_eia860_dir() if data_dir is None else Path(data_dir)
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    path = data_dir / EIA_860_RETIRED_WINDOW_PARQUET_NAME
    if not path.exists():
        return []

    df = _normalize_columns(pd.read_parquet(path))
    ba_code = ISO_TO_BA_CODE.get(iso)
    if ba_code is not None and "balancing_authority_code" in df.columns:
        df = df[df["balancing_authority_code"].astype(str).str.strip() == ba_code]
    if df.empty:
        return []

    df = df.copy()
    df["chp"] = df["plant_id"].map(_chp_by_plant(path.parent, year)).fillna("N")
    generators = _rows_to_generators(df, iso, iso_config)
    if generators:
        logger.info(
            "loaded %d within-window retiree units for %s (%.0f MW, plants %s)",
            len(generators),
            iso,
            sum(g.pmax_mw for g in generators),
            sorted({int(g.plant_code) for g in generators}),
        )
    return generators


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

# EIA-860 proposed-generator statuses treated as construction-committed for
# the deterministic known-additions pipeline: U / V are under construction
# (<50% / >50% complete), TS is in test-mode pre-commercial. ``P``
# (planned-with-permits) is deliberately excluded here — appropriate for
# the renewables capacity-ramp aggregation, too speculative to enter the
# dispatch fleet as a firm thermal unit.
_PLANNED_FIRM_STATUSES: frozenset[str] = frozenset({"U", "V", "TS"})


def load_planned_additions(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
) -> list[Generator]:
    """Load EIA-860 planned/under-construction thermal units for an ISO.

    The deterministic "known additions" pipeline (methodology spec §5.4):
    proposed-generator rows with a construction-committed status (``U`` /
    ``V`` / ``TS``) whose plant's balancing authority maps to ``iso`` and
    whose ``Effective Year`` falls *after* the operable-snapshot vintage
    become :class:`Generator` objects with ``online_year`` set to that
    effective year. The runner injects each unit into the fleet when the
    simulation reaches its online year; beyond the EIA-860 data horizon the
    economic new-entry screen owns all additions.

    Wind, solar, hydro and storage rows are skipped (``_map_fuel_type``
    returns ``None`` for them): renewable capacity growth is handled by the
    zonal ``wind_cap`` / ``solar_cap`` pools and storage by its own entry
    screen, so adding them here would double-count. **Forecast-mode only**
    -- a backcast solves a historical year whose fleet snapshot already
    reflects what was actually built.

    Zones are assigned from each plant's EIA-860 lat/lon (proposed plants
    are usually absent from the eGRID vintage the operable loader keys on),
    falling back to the standard eGRID/largest-zone path.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        iso_config: Topology configuration; fetched via
            :func:`get_iso_config` when ``None``.
        data_dir: Directory holding the processed EIA-860 parquets.
            Defaults to :data:`EIA_860_DIR`.

    Returns:
        Planned thermal :class:`Generator` objects (``unit_id`` prefixed
        ``planned_``), sorted by online year. Empty when the proposed or
        plant parquet is missing (logged), or nothing qualifies.
    """
    iso = iso.upper()
    if data_dir is None:
        data_dir = active_eia860_dir()
    data_dir = Path(data_dir)
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    proposed_path = data_dir / "eia860_generator_proposed.parquet"
    plant_path = data_dir / "eia860_plant.parquet"
    if not proposed_path.exists() or not plant_path.exists():
        logger.warning(
            "planned additions unavailable for %s: missing %s",
            iso,
            proposed_path.name if not proposed_path.exists() else plant_path.name,
        )
        return []

    df = pd.read_parquet(proposed_path)
    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Balancing Authority Code", "Latitude", "Longitude"]
    ].drop_duplicates("Plant Code")
    df = df.merge(plants, on="Plant Code", how="left")

    ba_iso = df["Balancing Authority Code"].map(BA_CODE_TO_ISO)
    df = df[ba_iso == iso]
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status.isin(_PLANNED_FIRM_STATUSES)]
    eff_year = pd.to_numeric(df["Effective Year"], errors="coerce")
    df = df[eff_year > EIA860_OPERABLE_VINTAGE]
    if df.empty:
        return []

    norm = pd.DataFrame(
        {
            # Integer plant codes: the raw column arrives as float and
            # would otherwise render as "66335.0" inside unit ids.
            "plant_id": pd.to_numeric(df["Plant Code"], errors="coerce").astype(
                "Int64"
            ),
            "generator_id": df["Generator ID"],
            "plant_name": df["Plant Name"],
            "state": df["State"],
            "technology": df["Technology"],
            "energy_source": df["Energy Source 1"],
            "prime_mover": df["Prime Mover"],
            "nameplate_capacity_mw": df["Nameplate Capacity (MW)"],
            "net_summer_capacity_mw": df["Summer Capacity (MW)"],
            "operating_year": pd.to_numeric(df["Effective Year"], errors="coerce"),
            "chp": df["Associated with Combined Heat and Power System"],
        }
    )
    generators = _rows_to_generators(norm, iso, iso_config)

    # Re-place each unit from its plant's EIA-860 coordinates: proposed
    # plants mostly post-date the eGRID vintage behind _assign_zones, which
    # would otherwise dump them all in the fallback zone.
    from market_sim.data.zone_assignment import assign_zone_by_coords

    coords: dict[int, tuple[float, float]] = {}
    for row in df[["Plant Code", "Latitude", "Longitude"]].itertuples(index=False):
        code = _to_float(row[0])
        lat = _to_float(row[1])
        lon = _to_float(row[2])
        if code is not None and lat is not None and lon is not None:
            coords[int(code)] = (lat, lon)
    for g in generators:
        latlon = coords.get(g.plant_code)
        if latlon is not None:
            try:
                g.zone = assign_zone_by_coords(latlon[0], latlon[1], iso)
            except Exception:  # zone rules missing for the ISO: keep fallback
                pass
        g.unit_id = f"planned_{g.unit_id}"
        g.name = f"planned {g.name}"

    # The ISO's proposed rows may all be non-thermal (wind/solar/storage,
    # handled elsewhere), leaving nothing after fuel mapping.
    if not generators:
        return []
    generators.sort(key=lambda g: (g.online_year, g.unit_id))
    logger.info(
        "%s planned additions: %d units, %.0f MW, %d-%d",
        iso,
        len(generators),
        sum(g.pmax_mw for g in generators),
        min(g.online_year for g in generators),
        max(g.online_year for g in generators),
    )
    return generators


# ---------------------------------------------------------------------------
# CAMPD operational binning
#
# A unified, data-derived replacement for equal-width heat-rate binning. Each
# plant in custom-bin-assignments.csv is assigned to an operational bin; bins
# carry a 4-tranche capacity structure (Must Run / Committed / Economic /
# Peaking) that maps directly to LP dispatch behavior. See
# docs/binning-methodology.md.
# ---------------------------------------------------------------------------

# CAMPD plant-group → model fuel type. The two steam groups both map to
# the dedicated ``gas_st`` fuel: ST_GAS is the legacy utility natural-gas
# steam boiler fleet; ST_CHP is industrial steam cogeneration (a host steam
# load makes part of its capacity must-run).
BIN_GROUP_TO_FUEL: dict[str, str] = {
    "CC_CHP": "gas_cc",
    "CC_REGULAR": "gas_cc",
    "CT_CHP": "gas_ct",
    "CT_PEAKER": "gas_ct",
    "ST_GAS": "gas_st",
    "ST_CHP": "gas_st",
    "COAL": "coal",
}

# Startup cost ($/MW per start) by CAMPD plant group, used to amortize
# cycling cost into the monthly bid markup and to set the commitment IRR
# hurdle. Coal carries the highest cost: a coal start is a slow, fuel- and
# wear-intensive boiler warm-up, so its 36-hour minimum run rarely pays off.
# Source: NREL/SR-5500-55433 (Kumar et al. 2012), consistent with the legacy
# CC_STARTUP_PARAMS / CT_STARTUP_PARAMS midpoints.
BIN_STARTUP_COST_PER_MW: dict[str, float] = {
    "CC_CHP": 50.0,
    "CC_REGULAR": 50.0,
    "CT_CHP": 20.0,
    "CT_PEAKER": 20.0,
    "ST_GAS": 35.0,
    "ST_CHP": 35.0,
    "COAL": 100.0,
}

# Coal boiler minimum run / minimum downtime for the P2 commitment screen. A
# coal start is a slow, fuel- and wear-intensive boiler warm-up, so once
# committed a unit stays on ~1.5 days and, once down, stays down ~16 h before a
# restart pays off (NREL SR-5500-55433 baseload class; the same 36/16 ERCOT
# carries per-plant in custom-bin-assignments.csv). Other CAMPD-binning ISOs
# (MISO/PJM/CAISO/…) have no Min_Run column in their bin sheet, so coal there
# falls back to these physical defaults instead of the 0/0 that would let it
# cycle with peaker agility. Inert unless commitment screening runs with coal
# screened (P1-only keepers never touch min_run_hours).
COAL_BIN_MIN_RUN_HOURS: int = 36
COAL_BIN_MIN_DOWN_HOURS: int = 16
# The gas dispatch classes the EIA-923 override may assign to an ERCOT bin.
# Coal bins keep their bare ``COAL`` group (the supply rank is split downstream
# from :func:`coal_supply_class`), so the override only ever moves a plant among
# the gas classes — never into or out of coal.
_GAS_BIN_GROUPS: frozenset[str] = frozenset(
    {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"}
)


@lru_cache(maxsize=8)
def _eia923_plant_class_totals(year: int) -> dict[int, dict[str, float]]:
    """Return ``{plant_code: {model class: annual net-gen MWh}}`` from EIA-923.

    Classifies every ``(plant, prime_mover, fuel, chp)`` EIA-923 Page-1
    generation row through the canonical :func:`classify_plant` and sums net
    generation per (plant, class). The shared basis for both the per-plant
    dominant class and the genuinely-mixed-plant detection. Empty when EIA-923
    has no data for ``year``.
    """
    from market_sim.data.eia923 import load_monthly_generation

    try:
        gen = load_monthly_generation()
    except FileNotFoundError:
        return {}
    df = gen[gen["year"] == year]
    if df.empty:
        return {}

    totals: dict[int, dict[str, float]] = {}
    for pid, pm, fuel, chp, mwh in zip(
        df["plant_id"],
        df["prime_mover"],
        df["fuel_type"],
        df["chp"],
        df["netgen_annual_mwh"],
    ):
        klass = classify_plant(
            fuel,
            pm,
            str(chp).strip().upper().startswith("Y"),
            int(pid),
            coal_class_resolver=_coal_class_for,
        )
        totals.setdefault(int(pid), {})
        totals[int(pid)][klass] = totals[int(pid)].get(klass, 0.0) + float(mwh)
    return totals


def eia923_dominant_class_by_plant(year: int) -> dict[int, str]:
    """Return ``{plant_code: dominant model class}`` from EIA-923 Page-1 netgen.

    Classifies every ``(plant, prime_mover, fuel, chp)`` EIA-923 generation row
    through the canonical :func:`classify_plant` and, per plant, picks the class
    with the most net generation. This is the single source of truth for a
    plant's class: the ERCOT bin override (:func:`load_campd_bins`) reads it so
    a curated bin can't drift from what the plant actually burned.

    Returns an empty mapping when EIA-923 has no data for ``year`` (forward /
    scenario years, or a missing parquet), so callers fall back cleanly to the
    curated (ERCOT) or EIA-860-derived class.
    """
    out: dict[int, str] = {}
    for pid, by in _eia923_plant_class_totals(year).items():
        out[pid] = max(by.items(), key=lambda kv: kv[1])[0]
    return out


# Gas-thermal scoring classes a single plant can mix (steam vs combustion-turbine
# units), and the dominant-share floor below which the plant is treated as
# genuinely mixed — no single class earns the bin, so collapsing it to one class
# is a coin-flip that can flip year-to-year (e.g. Dansby 50/50 ST/CT).
_GAS_THERMAL_SCORING_CLASSES: frozenset[str] = frozenset(
    {
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
    }
)
OTHER_FOSSIL_CLASS: str = "OTHER_FOSSIL"
OTHER_FOSSIL_MIN_DOMINANT_FRAC: float = 0.60


@lru_cache(maxsize=8)
def mixed_fossil_plants(year: int) -> frozenset[int]:
    """Return the EIA plant codes that are genuinely mixed gas-thermal plants.

    A plant qualifies when no single gas-thermal class holds at least
    :data:`OTHER_FOSSIL_MIN_DOMINANT_FRAC` (60%) of its EIA-923 net generation
    and its two largest classes are both gas-thermal — i.e. a steam + combustion-
    turbine mix we cannot cleanly assign to CC / CT / ST from the plant-summed
    data. These are scored in an ``OTHER_FOSSIL`` bucket (on both the model and
    the actual side) by :func:`apply_other_fossil_scoring`, so the coin-flip does
    not distort the clean-class scores. Dispatch is unaffected — the bin keeps
    its dominant-class offer curve. Empty when EIA-923 has no data for ``year``.
    """
    out: set[int] = set()
    for pid, by in _eia923_plant_class_totals(year).items():
        total = sum(by.values())
        if total <= 0.0:
            continue
        ranked = sorted(by.items(), key=lambda kv: kv[1], reverse=True)
        (top_cls, top_mwh) = ranked[0]
        second_cls = ranked[1][0] if len(ranked) > 1 else None
        if (
            top_mwh / total < OTHER_FOSSIL_MIN_DOMINANT_FRAC
            and top_cls in _GAS_THERMAL_SCORING_CLASSES
            and second_cls in _GAS_THERMAL_SCORING_CLASSES
        ):
            out.add(pid)
    return frozenset(out)


def apply_other_fossil_scoring(
    df: pd.DataFrame,
    year: int,
    plant_col: str = "plant_code",
    class_col: str = "klass",
) -> pd.DataFrame:
    """Re-bucket genuinely-mixed plants' gas-thermal rows into ``OTHER_FOSSIL``.

    A reporting/benchmark transform (NOT a dispatch change): for every row whose
    ``plant_col`` is a :func:`mixed_fossil_plants` plant and whose ``class_col``
    is a gas-thermal class, the class is relabelled ``OTHER_FOSSIL``. Applied
    symmetrically to the model dispatch frame and the EIA-923 actuals frame so a
    mixed plant's generation lands in the same bucket on both sides. Returns the
    frame unchanged (a copy is made only when something is relabelled) when the
    year has no mixed plants or the columns are absent.
    """
    mixed = mixed_fossil_plants(year)
    if not mixed or plant_col not in df.columns or class_col not in df.columns:
        return df
    codes = pd.to_numeric(df[plant_col], errors="coerce")
    mask = codes.isin(mixed) & df[class_col].isin(_GAS_THERMAL_SCORING_CLASSES)
    if not bool(mask.any()):
        return df
    out = df.copy()
    # The class column is often a pandas Categorical (from parquet); register the
    # new bucket as a category before assigning, else the setitem raises.
    if isinstance(out[class_col].dtype, pd.CategoricalDtype):
        if OTHER_FOSSIL_CLASS not in out[class_col].cat.categories:
            out[class_col] = out[class_col].cat.add_categories([OTHER_FOSSIL_CLASS])
    out.loc[mask, class_col] = OTHER_FOSSIL_CLASS
    return out


def ct_mustrun_floor_mwh_by_plant(year: int) -> dict[int, np.ndarray]:
    """Return ``{plant_code: array(12) monthly CT_PEAKER net-gen MWh}``.

    Sums every EIA-923 Page-1 monthly net-generation row that classifies
    (:func:`classify_plant`) as ``CT_PEAKER``, per plant, in calendar-month
    order. This is the source of the per-plant simple-cycle reliability
    must-run floor (``config.ct_mustrun_per_plant``): the energy-only LP prices
    peakers out almost entirely while the actuals show a low (~4% CF) reserve/
    reliability run, so the observed monthly energy is injected as a
    minimum-generation floor.

    Returns an empty mapping when EIA-923 has no data for ``year`` (forward /
    scenario years, or a missing parquet), so callers fall back to no floor.
    """
    from market_sim.data.eia923 import (
        load_monthly_generation,
        monthly_netgen_columns,
    )

    try:
        gen = load_monthly_generation()
    except FileNotFoundError:
        return {}
    df = gen[gen["year"] == year]
    if df.empty:
        return {}
    is_ct = [
        classify_plant(
            fuel,
            pm,
            str(chp).strip().upper().startswith("Y"),
            int(pid),
            coal_class_resolver=_coal_class_for,
        )
        == "CT_PEAKER"
        for pm, fuel, chp, pid in zip(
            df["prime_mover"],
            df["fuel_type"],
            df["chp"],
            df["plant_id"],
        )
    ]
    sub = df[pd.Series(is_ct, index=df.index)]
    if sub.empty:
        return {}
    cols = monthly_netgen_columns()
    grouped = sub.groupby("plant_id")[cols].sum()
    return {int(pid): row.to_numpy(dtype=float) for pid, row in grouped.iterrows()}


# ERCOT coal-unit commission year by EIA plant code — the in-service year
# of the plant's coal units (not its older gas-era units, which differ at
# mixed plants like W A Parish). Drives the age-based coal availability
# model in :func:`generators_to_fleet_arrays`.
COAL_PLANT_COMMISSION_YEAR: dict[int, int] = {
    298: 1985,  # Limestone
    3470: 1977,  # W A Parish (coal units 5-8)
    6146: 1977,  # Martin Lake
    6178: 1980,  # Coleto Creek
    6179: 1979,  # Fayette / Sam Seymour
    6180: 2010,  # Oak Grove
    6183: 1982,  # San Miguel
    7030: 1990,  # Major Oak Power
    7097: 1992,  # J K Spruce
    56257: 2013,  # Sandy Creek
}

# Per-plant coal must-run percentage, keyed by EIA plant code. Derived from
# EPA CAMPD/CEMS TX 2023-2025 minimum-load behaviour and observed seasonal
# outage structure (an outage = plant gross < 2% of nameplate for >= 2
# consecutive days). Replaces the uniform lignite/PRB must-run overrides when
# config.coal_mustrun_per_plant is set; the historic outage overlay still
# zeros these plants during their actual maintenance windows. Lignite mine-
# mouth units carry high floors (take-or-pay, baseload); PRB rail units that
# cycle hard (J K Spruce, W A Parish) carry low floors.
COAL_MUSTRUN_BY_PLANT: dict[int, float] = {
    6180: 45.0,  # Oak Grove (lignite) — 12d planned block, otherwise baseload
    7030: 45.0,  # Major Oak (lignite) — 99.2% online, EAF only
    6183: 55.0,  # San Miguel (lignite) — large spring + fall blocks, ~38% off
    298: 20.0,  # Limestone (PRB) — recurring Feb winter + variable spring
    6146: 20.0,  # Martin Lake (PRB) — no systematic pattern, EAF
    6178: 30.0,  # Coleto Creek (PRB) — large spring block (shortening)
    6179: 30.0,  # Fayette (PRB) — zero outage events across 3 years
    7097: 12.0,  # J K Spruce (PRB) — scattered short shoulder events
    3470: 15.0,  # W A Parish (PRB) — mixed facility, coal outages undetectable
    56611: 40.0,  # Sandy Creek (PRB) — annual spring block, length varies
}

# Sector-based behind-the-meter (BTM) treatment for CHP cogens. EIA-923 Page 1
# classifies each plant by sector: industrial / commercial cogens serve a host
# behind the meter and export only surplus, while merchant (IPP / NAICS-22)
# cogens sell to the grid. CHP_SECTOR_CLASS_BY_PLANT maps plant code to
# {"merchant","industrial","commercial"}; CHP_BTM_PCT_BY_SECTOR is the share of
# nameplate pulled out of the grid LP as host self-supply. The pulled-out BTM
# is added back in the report data-driven (EIA-923 net minus grid dispatch), so
# this only sizes how much grid-facing capacity the LP can dispatch.
CHP_SECTOR_CLASS_BY_PLANT: dict[int, str] = {
    10154: "industrial",
    10243: "industrial",
    10261: "industrial",
    10298: "industrial",
    10418: "industrial",
    10436: "industrial",
    10554: "industrial",
    10692: "industrial",
    10790: "industrial",
    50026: "industrial",
    50043: "industrial",
    50054: "commercial",
    50118: "commercial",
    50150: "industrial",
    50229: "industrial",
    50475: "industrial",
    50815: "merchant",
    52088: "merchant",
    52120: "industrial",
    52132: "industrial",
    52176: "merchant",
    54330: "industrial",
    54520: "commercial",
    54676: "merchant",
    55015: "merchant",
    55047: "merchant",
    55187: "merchant",
    55206: "merchant",
    55299: "merchant",
    55311: "industrial",
    55313: "industrial",
    55327: "merchant",
    55464: "merchant",
    55470: "industrial",
    56152: "industrial",
    56374: "merchant",
    57322: "industrial",
    57504: "commercial",
    58151: "commercial",
    58378: "merchant",
    59145: "industrial",
    59381: "commercial",
    62762: "merchant",
    66992: "merchant",
}
# CHP_BTM_PCT_BY_SECTOR and CHP_ST_BTM_PCT now live in constants.py (re-derived
# from EIA-923 Schedule-8 CHP sector data rather than the Run-61..65 residual
# — see the citation there).

# Per-plant total must-run floor: the p2 CAMPD gross CF (non-outage, pooled
# 2023-2025). The grid-delivered steam-following floor applied as min-gen is
# this minus the plant's BTM share (computed at build time). Only plants with
# CAMPD coverage have a value (Baytown ~28%, ~the 27% target); absent => no
# floor, dispatched purely economically.
CHP_PMIN_CF_BY_PLANT: dict[int, float] = {
    10298: 65.3,
    50815: 36.7,
    52088: 26.0,
    52176: 0.0,
    55015: 49.7,
    55047: 25.0,
    55187: 64.2,
    55206: 25.8,
    55299: 33.1,
    55327: 28.2,
    55464: 33.8,
    55470: 20.9,
    58378: 88.8,
}

# Petra Nova carbon-capture cogen (EIA 58378): classified on its own, outside
# the CT_CHP offer curve. The 45Q tax credit pays per ton captured, so the
# plant runs flat-out whenever the capture train is up regardless of energy
# price — CAMPD shows pure on/off behaviour (out Jan-Aug 2023, roughly half of
# 2024/2025) at a ~95% when-on capacity factor, never price-following. Modeled
# as a single tranche forced to PETRA_NOVA_MIN_CF of its net capacity whenever
# available; the historic facility outage overlay (campd-outages.csv carries
# its windows) supplies the on/off shape. PETRA_NOVA_PARASITIC_PCT is the
# capture train's parasitic load — the gap between CAMPD generator output and
# EIA-923 net delivered (2023: 1-109.0/181.2 = 39.8%; 2024: 1-200.8/339.5 =
# 40.9%) — replacing the generic merchant-sector BTM share.
PETRA_NOVA_PLANT_CODE: int = 58378
PETRA_NOVA_PARASITIC_PCT: float = 40.0
PETRA_NOVA_MIN_CF: float = 0.92


# Per-plant CC_REGULAR committed-tranche % (minimum stable load once started),
# keyed by EIA plant code. Derived from EPA CAMPD/CEMS TX 2023 hourly gross
# output over Jan-July (the window data/raw/reference/tx-jan-aug23-unit-outages.csv covers,
# so available capacity is known): the P5 of each plant's net capacity factor
# over its committed (online) hours, normalized by the unit-outage-adjusted
# available capacity. See scripts/derive_cc_committed_pct.py and
# data/raw/_processed-legacy/cc_committed_pct.csv for the full percentile distribution.
# Replaces the coarse assumed CSV Pct_Committed (clustered at 20/25/45/55) when
# config.cc_committed_per_plant is set; the economic tranche absorbs the
# difference so each plant's tranche split still sums to 100%. Plants without
# CAMPD coverage (7512, 50127, 55545, 56233) keep the CSV value.
CC_REGULAR_COMMITTED_PCT_BY_PLANT: dict[int, float] = {
    3441: 11.5,  # Nueces Bay (online 0.41)
    3443: 44.7,  # Victoria (online 0.28)
    3469: 8.4,  # T H Wharton (online 0.22)
    3631: 8.1,  # Sam Rayburn (online 0.39)
    4937: 33.3,  # Thomas C Ferguson (online 0.89)
    4939: 7.7,  # Barney M Davis [CC] (online 0.46)
    7900: 17.9,  # Sand Hill (online 0.87)
    50109: 28.8,  # Paris Energy Center (online 0.47)
    54817: 36.7,  # Johnson County (online 0.54)
    55062: 25.7,  # Tenaska Frontier (online 0.86)
    55086: 21.0,  # Gregory Power Plant (online 0.15)
    55091: 12.1,  # Midlothian Energy Facility (online 0.59)
    55097: 31.2,  # Lamar Power Project (online 0.80)
    55098: 40.3,  # Frontera Energy Center (online 0.32)
    55123: 27.9,  # Magic Valley (online 0.61)
    55132: 15.2,  # Tenaska Gateway (online 0.45)
    55137: 37.8,  # Rio Nogales Power Project (online 0.68)
    55139: 38.6,  # Wolf Hollow I LP (online 0.60)
    55144: 23.3,  # Hays Energy Project (online 0.75)
    55153: 44.1,  # Guadalupe Generating Station (online 0.95)
    55168: 32.4,  # Bastrop Energy Center (online 0.73)
    55172: 37.3,  # Thad Hill Energy Center (online 0.89)
    55215: 26.4,  # Odessa-Ector Power Plant (online 0.89)
    55223: 42.5,  # Ennis Power Company LLC (online 0.54)
    55226: 40.9,  # Freestone Energy Center (online 1.00)
    55230: 18.1,  # Jack County (online 0.89)
    55320: 25.3,  # Wise County Power LLC (online 0.61)
    55480: 30.2,  # Forney Energy Center (online 0.85)
    56349: 22.7,  # Quail Run Energy Center (online 0.64)
    56350: 27.3,  # Colorado Bend Energy Center (online 0.75)
    56806: 20.9,  # Cedar Bayou 4 (online 0.63)
    58001: 30.5,  # Temple Power Station (online 0.96)
    58005: 36.2,  # Rayburn Energy Station LLC (online 0.62)
    59812: 32.3,  # Wolf Hollow II (online 0.85)
    60122: 36.6,  # Colorado Bend II (online 0.91)
}


# CC_REGULAR_PEAKING_PCT_BY_PLANT now lives in constants.py (residual-
# identified, forecast-risk — see the citation there).


@lru_cache(maxsize=1)
def _eia860_plant_sector() -> dict[int, int]:
    """Return ``{plant_code: EIA-860 Sector number}`` from the plant table."""
    path = active_eia860_dir() / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Sector"])
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


# Per-bin forced availability derates by year, for confirmed unit losses
# that the age-based THERMAL_AVAILABILITY model cannot anticipate (turbine
# fires, boiler explosions, etc.). Keyed by ``Bin_Label`` and run year, the
# value is a flat multiplier on the bin's availability for the whole year.
BIN_FORCED_DERATE_BY_YEAR: dict[str, dict[int, float]] = {
    # Martin Lake -- turbine fire and boiler explosion took unit 1 out of
    # commission for 2025 (1 of 3 units, ~33% nameplate loss).
    "N_COAL4": {2025: 0.67},
    # V H Braunig -- CPS Energy retired ST units 1 (225 MW) and 2 (252 MW)
    # in early 2025 (March), leaving ST unit 3 (417 MW) and four 61 MW
    # CTs (units 5-8) in the bin. The retiring 477 MW is 42% of the bin's
    # 1138 MW nameplate; the annual-average derate for 2025 is
    # (3/12 * 1.0) + (9/12 * 661/1138) = 0.686. 2026+ would be 0.581
    # (units 1+2 retired full year); add when those calibration years
    # come into scope.
    "SC_STGAS3": {2025: 0.686},
    # Sandy Creek -- removed from availability in 2025 (mostly offline; EIA-923
    # shows 0.72 TWh vs ~3.0-3.3 TWh in 2023-2024).
    "SC_COAL3": {2025: 0.0},
}

# Fallback heat rate (MMBtu/MWh) by plant group, used when a plant's
# Plant_Avg_HR_MMBtu_MWh is blank in the CSV (e.g. tiny unmetered CTs).
BIN_GROUP_HR_DEFAULT: dict[str, float] = {
    "CC_CHP": 7.5,
    "CC_REGULAR": 7.0,
    "CT_CHP": 9.0,
    "CT_PEAKER": 13.0,
    "ST_GAS": 11.0,
    "ST_CHP": 7.0,
    "COAL": 9.5,
}

# The composite key that uniquely identifies one CAMPD bin. Bin_Label alone
# is NOT unique — labels such as "S_CC1" or "CT1 (8-9)" recur across zones —
# so the group, zone and bin number are all part of the key.
_BIN_KEY_COLUMNS: list[str] = [
    "Plant_Group",
    "ERCOT_Zone",
    "Bin_Number",
    "Bin_Label",
]


def get_vom(fuel: str) -> float:
    """Return the variable O&M ($/MWh) for a model fuel type."""
    return VOM.get(fuel, 0.0)


def get_emission_rate(fuel: str, heat_rate: float) -> float:
    """Return the CO2 emission rate (tCO2/MWh) for a fuel at a heat rate.

    Derived as ``heat_rate × FUEL_CO2_FACTOR_PER_MMBTU[fuel]`` so a
    CAMPD bin's CEMS-measured heat rate yields its emission rate directly,
    without a vintage-bin lookup.
    """
    return float(heat_rate) * FUEL_CO2_FACTOR_PER_MMBTU.get(fuel, 0.0)


def get_nox_rate(fuel: str) -> float:
    """Return the NOx emission rate (tons NOx/MWh) for a model fuel type."""
    return NOX_RATES.get(fuel, 0.0)


def get_eford(fuel: str) -> float:
    """Return the equivalent forced outage rate for a model fuel type."""
    return EFORD.get(fuel, 0.05)


def load_plant_registry(csv_path: str | Path) -> pd.DataFrame:
    """Load the master plant registry CSV.

    The registry has one row per ERCOT thermal plant with EIA-860 / CAMPD
    attributes. It is not consumed by dispatch directly — the dispatch fleet
    comes from :func:`load_campd_bins` — but it is the reference for plant
    metadata and the "OTHER" (non-dispatchable) plant set.

    Args:
        csv_path: Path to ``master-plant-registry.csv``.

    Returns:
        The registry as a DataFrame.
    """
    return pd.read_csv(csv_path)


# EIA-860 "Technology" string that marks an oil/distillate-fired unit. The
# energy-source codes that back it (distillate / residual fuel oil) — used to
# keep the match robust if the technology label is blank but the fuel code is
# present.
_OIL_PRIMARY_TECHNOLOGY: str = "petroleum liquids"
_OIL_PRIMARY_FUEL_CODES: frozenset[str] = frozenset({"DFO", "RFO"})


@lru_cache(maxsize=4)
def _oil_primary_bin_plants(registry_path: str) -> frozenset[int]:
    """Cached oil-primary plant-code set from one registry CSV path."""
    reg = pd.read_csv(
        registry_path, usecols=lambda c: c in ("plantid", "fuel_type", "technology")
    )
    tech = reg["technology"].astype(str).str.strip().str.lower()
    fuel = reg["fuel_type"].astype(str).str.strip().str.upper()
    is_oil = tech.eq(_OIL_PRIMARY_TECHNOLOGY) | fuel.isin(_OIL_PRIMARY_FUEL_CODES)
    return frozenset(int(p) for p in reg.loc[is_oil, "plantid"])


def oil_primary_bin_plants(registry_path: str | Path) -> frozenset[int]:
    """Return EIA plant codes whose EIA-860 primary fuel is oil/distillate.

    A plant is oil-primary when its master-registry row (EIA-860 derived)
    is technology ``Petroleum Liquids`` or its primary energy source
    (``fuel_type``) is a distillate / residual fuel-oil code
    (:data:`_OIL_PRIMARY_FUEL_CODES`). These are the combustion-turbine /
    reciprocating peakers the CAMPD bin sheet routes through the gas
    ``CT_PEAKER`` class even though they physically burn distillate — e.g.
    Morgan Creek (3492). :func:`bins_to_fleet` reprices the gas-CT tranches
    of these plants on oil when ``config.oil_primary_bin_fuel`` is set, the
    structural counterpart of the oil-primary exclusion in
    :func:`dual_fuel_plant_groups`.

    The signal is a measured EIA-860 attribute that regenerates for any
    forward year, so the correction is forward-defensible rather than a
    fitted per-unit adder.
    """
    return _oil_primary_bin_plants(str(registry_path))


# Generator-level EIA-860 energy-source codes that mark an oil/kerosene-primary
# unit (Energy Source 1). Adds kerosene / jet fuel to the plant-registry DFO/RFO
# codes — the LI/NYC legacy frames are KER-listed at the generator level.
_OIL_PRIMARY_UNIT_FUEL_CODES: frozenset[str] = frozenset({"DFO", "RFO", "KER", "JF"})

# Simple-cycle prime movers for the generator-level oil-primary screen (GT/IC;
# EIA "CT" is a combined-cycle turbine part, never a simple-cycle peaker).
_OIL_PRIMARY_PRIME_MOVERS: frozenset[str] = frozenset({"GT", "IC"})


@lru_cache(maxsize=8)
def oil_primary_ct_plants_from_eia860(iso: str) -> frozenset[int]:
    """Return plant codes whose *generator-level* EIA-860 CT fleet is oil-primary.

    The generator-level companion to :func:`oil_primary_bin_plants`, which keys
    on the (ERCOT-only) master plant registry's PLANT primary fuel and so
    catches zero plants for the per-plant non-ERCOT ISOs. This reads the raw
    EIA-860 operable generator sheet directly: a plant is oil-primary when the
    majority (by nameplate capacity) of its operating simple-cycle units
    (GT/IC) carry an oil / kerosene Energy Source 1
    (:data:`_OIL_PRIMARY_UNIT_FUEL_CODES`), restricted to the ISO's balancing
    authority. Same measured-attribute admissibility as the registry screen
    (rule #12): the EIA-860 field regenerates for any forward vintage.

    Verification note (NYISO, 2026-07-04 session): the per-plant non-ERCOT
    fleet path already maps each unit's own EIA-860 energy source
    (:func:`_map_fuel_type`), so KER/DFO-primary units (Holtsville, Wading
    River, Glenwood 2514, Shoreham 2518, ...) load as raw ``oil`` units and
    never enter a gas CT bin — every NYISO gas-CT bin was confirmed
    NG-primary at the generator level. This screen therefore catches plants
    only where a minority NG unit creates a gas bin at a majority-oil plant,
    and its NYISO yield is empty; it is kept because it grounds the flag's
    semantics in the generator-level record for every ISO.
    """
    path = EIA_860_DIR / "eia860_generator_operable.parquet"
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Prime Mover",
            "Energy Source 1",
            "Nameplate Capacity (MW)",
            "Status",
        ],
    )
    ba_map = pd.read_parquet(
        EIA_860_DIR / "eia860_generators.parquet",
        columns=["plant_id", "balancing_authority_code"],
    ).drop_duplicates("plant_id")
    ba_code = ISO_TO_BA_CODE.get(iso.upper())
    if ba_code:
        keep = set(
            ba_map.loc[
                ba_map["balancing_authority_code"].astype(str).str.strip() == ba_code,
                "plant_id",
            ].astype(int)
        )
        df = df[df["Plant Code"].astype("Int64").isin(keep)]
    df = df[
        (df["Status"].astype(str).str.strip().str.upper() == "OP")
        & df["Prime Mover"].astype(str).str.strip().isin(_OIL_PRIMARY_PRIME_MOVERS)
    ]
    if df.empty:
        return frozenset()
    df = df.assign(
        _oil=df["Energy Source 1"]
        .astype(str)
        .str.strip()
        .str.upper()
        .isin(_OIL_PRIMARY_UNIT_FUEL_CODES),
        _mw=pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce").fillna(0.0),
    )
    by_plant = df.groupby(df["Plant Code"].astype(int)).apply(
        lambda g: float(g.loc[g["_oil"], "_mw"].sum()) > 0.5 * float(g["_mw"].sum()),
        include_groups=False,
    )
    return frozenset(int(p) for p, is_oil in by_plant.items() if is_oil)


@lru_cache(maxsize=8)
def campd_ct_run_lengths(iso: str) -> dict[int, float]:
    """Return ``{plant_code: median CT run hours}`` for an ISO, ``0`` = fallback.

    Reads the committed CAMPD-measured simple-cycle CT run-length artifact
    (``scripts/derive_campd_ct_run_lengths.py`` →
    ``data/raw/_processed-legacy/campd_ct_run_lengths_<ISO>.csv``): per-plant
    median start-to-stop run lengths pooled 2023-2025, with the ISO-class
    pooled median under key ``0`` for CT plants without CEMS coverage. Empty
    dict when the ISO has no artifact (the v3 amortization then leaves every
    tranche on the v2 P0 basis — never a silent hand number, rule #23).
    """
    path = PROCESSED_DIR / f"campd_ct_run_lengths_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path, usecols=["plant_code", "median_run_hours"])
    return {
        int(r.plant_code): float(r.median_run_hours)
        for r in df.itertuples(index=False)
        if float(r.median_run_hours) > 0.0
    }


# Model plant_group -> CAMPD ramp-envelope family bucket. Mirrors the derive
# script's unitType bucketing (scripts/derive_campd_ramp_envelopes.py) so a
# mixed facility (CC block + standalone peakers) is enveloped per family.
_RAMP_BUCKET_BY_GROUP: dict[str, str] = {
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "ST_GAS": "ST",
    "ST_CHP": "ST",
    "COAL": "ST",
    "CT_PEAKER": "CT",
    "CT_CHP": "CT",
}


@lru_cache(maxsize=8)
def load_campd_ramp_envelopes(iso: str) -> "pd.DataFrame | None":
    """Return the ISO's CAMPD plant-level hourly ramp-envelope table, or None.

    Reads the committed measured artifact
    (``scripts/derive_campd_ramp_envelopes.py`` →
    ``data/raw/_processed-legacy/campd_ramp_envelopes_<ISO>.csv``): per
    (plant, CC/CT/ST bucket) max observed 1-h up/down gross-load deltas
    pooled 2023-2025 (``basis == "plant"``), sparse-coverage rows
    (``basis == "sparse"``, informational only) and the capacity-weighted
    class-median envelope FRACTIONS under ``plant_code == 0``
    (``basis == "class_fraction"``). ``None`` when the ISO has no artifact —
    the ramp rows are then simply absent (never a silent hand number,
    rule #23). Cached per ISO; treat the returned frame as read-only.
    """
    path = PROCESSED_DIR / f"campd_ramp_envelopes_{iso.upper()}.csv"
    if not path.exists():
        return None
    return pd.read_csv(path)


def build_ramp_groups(
    fleet: FleetArrays, iso: str
) -> "tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None":
    """Group thermal columns into ramp-enveloped plant groups for the LP.

    Members are grouped by ``(plant_code, family bucket)`` where the bucket
    collapses the model plant groups onto the CAMPD envelope families
    (CC_REGULAR/CC_CHP → CC; ST_GAS/ST_CHP/COAL → ST; CT_PEAKER/CT_CHP →
    CT) — the envelope is a plant property, tranche switching inside a plant
    stays free (design doc §1.2). Each group's envelope resolves from its
    measured ``basis == "plant"`` row (MW, used directly); groups without one
    fall back to the CC/ST class-median fraction × group pmax. CT groups get
    NO fallback — a CT without a well-observed CEMS trace simply has no row
    (bang-bang is the measured norm for the class).

    Pruning (rule 18 — physics by parameters, not class names): a group
    whose envelope can never bind (``RU >= cap`` AND ``RD >= cap``, with
    ``cap`` the group's summed pmax) gets no row — bang-bang CTs drop out
    naturally, as do import pseudo-generators (``plant_code == 0``, never
    grouped).

    Args:
        fleet: Vectorized fleet arrays (needs ``plant_code``, ``plant_group``
            and ``pmax``).
        iso: ISO identifier keying the committed envelope artifact.

    Returns:
        ``(gen_idx, group_col, ramp_up_mw, ramp_dn_mw)`` for
        :func:`market_sim.model.dispatch.build_constraints` — member thermal
        column indices, each member's group index, and the per-group
        envelopes — or ``None`` when the artifact is absent, the fleet
        carries no plant groups, or every group pruned out.
    """
    env = load_campd_ramp_envelopes(iso)
    if env is None or fleet.plant_group is None:
        return None
    plant_code = np.asarray(fleet.plant_code, dtype=int)
    pmax = np.asarray(fleet.pmax, dtype=float)
    buckets = np.array(
        [
            _RAMP_BUCKET_BY_GROUP.get(str(g), "")
            for g in np.asarray(fleet.plant_group, dtype=object)
        ],
        dtype=object,
    )

    measured = {
        (int(r.plant_code), str(r.bucket)): (
            float(r.ramp_up_mw),
            float(r.ramp_dn_mw),
        )
        for r in env[env.basis == "plant"].itertuples(index=False)
    }
    class_frac = {
        str(r.bucket): (float(r.ramp_up_mw), float(r.ramp_dn_mw))
        for r in env[env.basis == "class_fraction"].itertuples(index=False)
        # CT gets NO class fallback: only a measured plant row can envelope it.
        if str(r.bucket) in ("CC", "ST")
    }

    # Group member columns by (plant, bucket); insertion order is stable.
    members: dict[tuple[int, str], list[int]] = {}
    for i in np.flatnonzero((plant_code > 0) & (buckets != "")):
        members.setdefault((int(plant_code[i]), str(buckets[i])), []).append(int(i))

    gen_idx: list[int] = []
    group_col: list[int] = []
    ramp_up: list[float] = []
    ramp_dn: list[float] = []
    for (pk, bucket), m in members.items():
        cap = float(pmax[m].sum())
        if (pk, bucket) in measured:
            ru, rd = measured[(pk, bucket)]
        elif bucket in class_frac:
            fu, fd = class_frac[bucket]
            ru, rd = fu * cap, fd * cap
        else:
            continue
        if ru >= cap and rd >= cap:
            continue  # envelope can never bind (bang-bang) — prune, no row
        g = len(ramp_up)
        gen_idx.extend(m)
        group_col.extend([g] * len(m))
        ramp_up.append(ru)
        ramp_dn.append(rd)
    if not ramp_up:
        return None
    return (
        np.asarray(gen_idx, dtype=int),
        np.asarray(group_col, dtype=int),
        np.asarray(ramp_up, dtype=float),
        np.asarray(ramp_dn, dtype=float),
    )


# Default location of the CAMPD-derived per-plant emission-rate artifact
# (scripts/derive_plant_emissions.py), resolved relative to the repo root.
PLANT_EMISSION_RATES_PATH: Path = PROCESSED_DIR / "plant_emission_rates.parquet"

# kg -> metric tonnes, the model's internal emission-rate mass unit.
_KG_PER_TONNE: float = 1000.0


@lru_cache(maxsize=4)
def _plant_emission_rate_map(
    path: str,
) -> dict[int, tuple[float, float, float]]:
    """Return ``{plant_id: (co2, nox, so2)}`` rates in tonnes/MWh net.

    Reads the pooled (``year == 0``) rows of the CAMPD emission-rate
    artifact and converts the per-MWh-net kg figures to the model's
    tonnes/MWh unit. Plants flagged ``mixed`` (coal and gas units sharing one
    facility CEMS record) are omitted — a single facility rate cannot be
    assigned to their separate coal and gas dispatch bins, so those bins keep
    fuel-class defaults. Cached by path so repeated yearly fleet builds in one
    run parse the parquet once.
    """
    df = pd.read_parquet(path)
    pooled = df[df["year"] == 0]
    if "mixed" in pooled.columns:
        pooled = pooled[~pooled["mixed"].astype(bool)]
    out: dict[int, tuple[float, float, float]] = {}
    for _, r in pooled.iterrows():
        out[int(r["plant_id"])] = (
            float(r["co2_kg_per_mwh_net"]) / _KG_PER_TONNE,
            float(r["nox_kg_per_mwh_net"]) / _KG_PER_TONNE,
            float(r["so2_kg_per_mwh_net"]) / _KG_PER_TONNE,
        )
    return out


@lru_cache(maxsize=8)
def _measured_plant_rate_map_v2(
    path: str, iso: str, year: int, mode: str
) -> dict[tuple[int, str], tuple[float, float, float]]:
    """Cache the mode-aware ``{(plant_id, fuel_class): (tCO2, tNOx, tSO2)/MWh}`` map.

    All three pollutants share the identical mode/window/composition-mask policy
    (:func:`market_sim.data.emission_rates.measured_plant_rates`); NOx/SO2 simply
    read their own mass column (plan §5 R7). A plant/class missing a pollutant's
    measured mass gets 0.0 for that pollutant, so the caller can preserve the
    fuel-class default (CO2/NOx) rather than overwrite it with a spurious zero.
    """
    from market_sim.data.emission_rates import measured_plant_rates

    df = pd.read_parquet(path)
    co2 = measured_plant_rates(df, iso, year, mode, pollutant="co2")
    nox = measured_plant_rates(df, iso, year, mode, pollutant="nox")
    so2 = measured_plant_rates(df, iso, year, mode, pollutant="so2")
    keys = set(co2) | set(nox) | set(so2)
    return {k: (co2.get(k, 0.0), nox.get(k, 0.0), so2.get(k, 0.0)) for k in keys}


def _apply_forward_control_retrofits(
    rates: dict[tuple[int, str], tuple[float, float, float]],
    config: object,
    year: int,
) -> dict[tuple[int, str], tuple[float, float, float]]:
    """Step measured ``(co2, nox, so2)`` rates for announced EIA-860 controls.

    The forward control-retrofit channel
    (``docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md``):
    splits the triple map into per-pollutant float maps, applies
    :func:`market_sim.data.emission_rates.apply_control_retrofits` to each with
    the forecast-year announced-control schedule (a control online by ``year``
    steps the covered plant's rate down), and recombines. Returns the input map
    unchanged when no control is announced. Forecast-only; the caller gates on
    the mode and the ``control_retrofit_forward`` flag.
    """
    from market_sim.config import constants
    from market_sim.data.emission_rates import (
        apply_control_retrofits,
        load_announced_controls,
    )

    controls = load_announced_controls(
        getattr(config, "control_retrofit_path", ""),
        min_install_year=constants.CONTROL_RETROFIT_HISTORY_END_YEAR + 1,
    )
    if not controls:
        return rates
    # One stepped float map per pollutant (index 0=co2, 1=nox, 2=so2), then zip
    # back into triples. Fresh dicts throughout — the cached input is untouched.
    stepped = [
        apply_control_retrofits(
            {k: v[i] for k, v in rates.items()}, controls, year, pollutant
        )
        for i, pollutant in enumerate(("co2", "nox", "so2"))
    ]
    return {k: (stepped[0][k], stepped[1][k], stepped[2][k]) for k in rates}


def apply_plant_emission_rates_v2(
    generators: list[Generator],
    path: str | Path,
    *,
    iso: str,
    year: int,
    mode: str,
    config: object | None = None,
) -> int:
    """Override per-generator CO2 rates from the v2 artifact (mode-aware).

    Uses :func:`market_sim.data.emission_rates.measured_plant_rates`: a backcast
    year books each plant's own measured rate, a forecast year books the
    gen-weighted trailing-average estimator base. Rates are matched to each
    generator by ``(plant_code, coarse fuel class)`` — the composition mask — so
    a Parish-style coal+gas facility's coal and gas bins get separate measured
    rates (this replaces the old ``mixed`` exclusion). Returns the override count.

    CO2, NOx and SO2 are all booked at the plant's measured tonnes/MWh-net rate
    (plan §5 R7 full-wiring wave). CO2/NOx are overridden only when the measured
    rate is positive (a zero means "no measured mass" — keep the fuel default);
    SO2 is always set, mirroring :func:`apply_plant_emission_rates`, because zero
    is a legitimate SO2 value for gas units. NOx/SO2 are secondary: this changes
    no CO2 rate and no merit order.

    When ``config.control_retrofit_forward`` is set and this is a **forecast**
    year, each pollutant's measured map is stepped by any announced EIA-860
    control online by ``year`` (SCR/SNCR → NOx, FGD/DSI → SO2, from the
    committed-install pipeline; CO2 carries no default control — carbon capture
    is owned by the CCS retrofit screen, rule 15), via
    :func:`_apply_forward_control_retrofits`. OFF or backcast leaves the maps
    byte-identical.
    docs/handoffs/emission-control-retrofit-forward-channel-2026-07.md
    """
    from market_sim.data.emission_rates import fuel_class

    resolved = Path(path)
    if not resolved.exists():
        return 0
    rates = _measured_plant_rate_map_v2(str(resolved), str(iso), int(year), str(mode))
    if (
        str(mode).lower() != "backcast"
        and config is not None
        and getattr(config, "control_retrofit_forward", False)
    ):
        rates = _apply_forward_control_retrofits(rates, config, int(year))
    n = 0
    for gen in generators:
        triple = rates.get((int(gen.plant_code), fuel_class(gen.fuel_type)))
        if triple is None:
            continue
        co2, nox, so2 = triple
        touched = False
        if co2 > 0.0:
            gen.emission_rate_co2 = co2
            touched = True
        if nox > 0.0:
            gen.nox_rate = nox
            touched = True
        gen.so2_rate = so2
        if touched or so2 > 0.0:
            n += 1
    return n


def apply_plant_emission_rates(
    generators: list[Generator],
    path: str | Path | None = None,
) -> int:
    """Override per-generator CO2/NOx/SO2 rates with CAMPD plant-specific ones.

    Each generator pinned to a single physical plant (``plant_code > 0``)
    that the CAMPD emission-rate artifact covers takes that plant's measured
    intensity per MWh **net** generation, so carbon / NOx / SO2 prices in the
    dispatch LP bite at the real plant rather than a fuel-class average.
    Generators without a plant code, or whose plant is absent from the
    artifact (multi-plant peaker bins, the legacy aggregated fleet), keep
    their fuel-default rates. CO2 and NOx are overridden only when the
    measured rate is positive; SO2 is always set (zero is a valid value for
    gas units, and the default is zero anyway).

    Args:
        generators: The fleet to mutate in place.
        path: Override for the artifact location; ``None`` uses
            :data:`PLANT_EMISSION_RATES_PATH`.

    Returns:
        The number of generators whose rates were overridden.
    """
    resolved = Path(path) if path is not None else PLANT_EMISSION_RATES_PATH
    if not resolved.exists():
        return 0
    rates = _plant_emission_rate_map(str(resolved))
    n = 0
    for gen in generators:
        plant_rate = rates.get(int(gen.plant_code))
        if plant_rate is None:
            continue
        co2, nox, so2 = plant_rate
        if co2 > 0.0:
            gen.emission_rate_co2 = co2
        if nox > 0.0:
            gen.nox_rate = nox
        gen.so2_rate = so2
        n += 1
    return n


def _fill_plant_hr(hr: float | None, plant_group: str) -> float:
    """Return a plant's heat rate, falling back to the plant-group default.

    Plants without a measured ``Plant_Avg_HR_MMBtu_MWh`` (typically tiny
    unmetered backup CTs in CT_unassigned) inherit the per-group default
    so the LP never sees a NaN heat rate.
    """
    if hr is not None and hr == hr and hr > 0.0:
        return float(hr)
    return BIN_GROUP_HR_DEFAULT.get(plant_group, 10.0)


def _fill_hr_multiplier(value: float | None, default: float) -> float:
    """Return a tranche HR multiplier, falling back to ``default`` if blank.

    Plants whose tranche capacity is zero leave the corresponding
    ``HR_Mult_<tranche>`` column blank; the per-fuel default keeps the
    arithmetic well-defined even when the resulting tranche is skipped.
    """
    if value is not None and value == value and value > 0.0:
        return float(value)
    return float(default)


# Per-plant-group default tranche HR multipliers, used when the CSV's
# ``HR_Mult_<tranche>`` cell is blank (a tranche with zero capacity for
# that plant). The values match the typical multipliers seen in the CSV
# for each group so a sensitivity run that turns on a zero-share tranche
# still produces a reasonable heat rate.
_DEFAULT_HR_MULT_BY_GROUP: dict[str, dict[str, float]] = {
    "CC_CHP": {"mr": 1.05, "mc": 1.05, "econ": 1.00, "peak": 1.45},
    "CC_REGULAR": {"mr": 1.10, "mc": 1.08, "econ": 1.00, "peak": 1.55},
    "CT_CHP": {"mr": 1.05, "mc": 1.10, "econ": 1.00, "peak": 1.15},
    "CT_PEAKER": {"mr": 1.05, "mc": 1.12, "econ": 1.00, "peak": 1.10},
    "ST_GAS": {"mr": 1.10, "mc": 1.15, "econ": 1.00, "peak": 1.10},
    "ST_CHP": {"mr": 1.05, "mc": 1.10, "econ": 1.00, "peak": 1.10},
    "COAL": {"mr": 1.00, "mc": 1.15, "econ": 1.00, "peak": 1.05},
}


def _override_bin_class_from_eia923(bins: pd.DataFrame, year: int) -> pd.DataFrame:
    """Override each gas bin's ``Plant_Group`` with its EIA-923 dominant class.

    For every bin whose curated class is one of the gas classes, replace it with
    the EIA-923 dominant class for that plant code when EIA-923 covers the year
    and resolves to a (different) gas class. The bin's ``fuel`` is re-derived
    from the new class; all other columns are preserved. Coal bins and plants
    EIA-923 doesn't cover keep their curated class — the durable single source
    of truth for ERCOT class assignment.
    """
    dominant = eia923_dominant_class_by_plant(year)
    if not dominant:
        return bins

    new_groups = bins["Plant_Group"].astype(str).tolist()
    changed: list[tuple[str, str, str]] = []
    for i, (code, curated) in enumerate(zip(bins["Plant_Code"], new_groups)):
        if curated not in _GAS_BIN_GROUPS:
            continue  # coal (and any non-gas bin) keeps its curated class
        derived = dominant.get(int(code))
        if derived and derived in _GAS_BIN_GROUPS and derived != curated:
            new_groups[i] = derived
            changed.append((str(bins["Plant_Name"].iloc[i]), curated, derived))

    if not changed:
        return bins

    bins = bins.copy()
    bins["Plant_Group"] = new_groups
    bins["fuel"] = bins["Plant_Group"].map(BIN_GROUP_TO_FUEL)
    for name, was, now in changed:
        logger.info(
            "EIA-923 %d: reclassified %s  %s -> %s (curated bin drifted)",
            year,
            name,
            was,
            now,
        )
    return bins


def _reconcile_cc_capacity(
    bins: pd.DataFrame, reconcile_path: str | Path
) -> pd.DataFrame:
    """Reconcile listed CC plants' ``capacity_mw`` to their demonstrated value.

    Reads the per-plant reconciliation table
    (``scripts/derive_cc_capacity_reconcile.py``) and applies each row per its
    ``mode`` column:

    * ``raise`` (or no ``mode`` column — the original ERCOT table, unchanged
      behaviour): lift ``capacity_mw`` to ``reconciled_mw`` where it exceeds
      the current value — the demonstrated CAMPD peak above nameplate (the
      cold-weather over-rating). A reconciled value at or below the current
      capacity is ignored, so a raise row can never shrink a plant.
    * ``cap``: lower ``capacity_mw`` to ``reconciled_mw`` where the current
      value exceeds it — the demonstrated-peak CAP for plants whose model
      nameplate exceeds anything the plant ever sustained in the CEMS record
      (measured capability, CLAUDE.md #13: the plant should not carry LP
      headroom above what it has ever delivered). A cap row at or above the
      current capacity is ignored, so a cap row can never grow a plant.

    A missing file is a no-op (the flag is on but the artifact was not
    generated). See :attr:`ScenarioConfig.cc_capacity_reconcile`.
    """
    path = Path(reconcile_path)
    if not path.exists():
        logger.warning(
            "cc_capacity_reconcile on but %s missing — no capacity change", path
        )
        return bins
    table = pd.read_csv(path)
    mode = (
        table["mode"].astype(str)
        if "mode" in table.columns
        else pd.Series("raise", index=table.index)
    )
    codes = table["plant_code"].astype(int)
    mw = table["reconciled_mw"].astype(float)
    recon_raise = dict(zip(codes[mode != "cap"], mw[mode != "cap"]))
    recon_cap = dict(zip(codes[mode == "cap"], mw[mode == "cap"]))
    old_cap = bins["capacity_mw"].astype(float).to_numpy()
    new_cap = np.array(
        [
            min(
                max(float(cur), recon_raise.get(int(code), 0.0)),
                recon_cap.get(int(code), np.inf),
            )
            for code, cur in zip(bins["Plant_Code"].astype(int), old_cap)
        ]
    )
    raised = int((new_cap > old_cap + 1e-6).sum())
    capped = int((new_cap < old_cap - 1e-6).sum())
    bins = bins.copy()
    bins["capacity_mw"] = new_cap
    logger.info(
        "CC capacity reconcile: raised %d / capped %d plant(s) to demonstrated "
        "peak (%+.0f MW total) from %s",
        raised,
        capped,
        float((new_cap - old_cap).sum()),
        path.name,
    )
    return bins


def load_campd_bins(
    csv_path: str | Path,
    year: int | None = None,
    capacity_reconcile_path: str | Path | None = None,
) -> pd.DataFrame:
    """Load the CAMPD bin assignments, one row per plant.

    The detail CSV has one row per plant; this normalises it into the
    one-bin-per-plant LP fleet schema. Every plant becomes its own
    operational bin: tranche percentages, commitment hours and the
    per-tranche HR multipliers come directly from the plant's CSV row,
    and per-tranche heat rates are derived from the plant's own
    ``Plant_Avg_HR_MMBtu_MWh`` rather than a zone-weighted average.

    When ``year`` is given, each bin's gas class (``Plant_Group``) is
    overridden with the EIA-923 dominant class for that plant code
    (:func:`eia923_dominant_class_by_plant`), so the curated bin can't drift
    from what the plant actually burned — e.g. a CC_CHP bin whose EIA-923
    netgen is dominated by merchant CC output is corrected to CC_REGULAR. Only
    the class (and the fuel it implies) changes; every other curated column
    (tranche %, HR multipliers, turbine class, config) is preserved, and the
    override only moves a plant among the gas classes. Plants EIA-923 doesn't
    cover for the year (or coal bins) keep their curated class. ``year=None``
    (the default, for tooling and forward scenarios) applies no override.

    Per-plant binning is the model spine for plant-specific monthly
    EIA-923 fuel costs and asset-level financial reporting — each LP bin
    is one EIA plant code, so dispatch and downstream P&L disaggregation
    share the same row identity.

    The ``Bin_Label`` / ``Bin_Number`` columns are a human-readable
    grouping only — they do NOT collapse plants into a shared LP generator
    and no bin-weighted heat rate is ever used in dispatch (each plant
    dispatches on its own ``Plant_Avg_HR_MMBtu_MWh``). Two CSV columns are
    read here but then commonly *overridden* downstream, so do not treat
    them as the dispatched values:

    * ``Pct_Committed`` / ``Pct_Peaking`` — replaced per-plant by the
      CAMPD-derived ``CC_REGULAR_COMMITTED_PCT_BY_PLANT`` /
      ``CC_REGULAR_PEAKING_PCT_BY_PLANT`` when
      ``config.cc_committed_per_plant`` / ``cc_peaking_per_plant`` is set
      (the ERCOT calibration default).
    * ``HR_Mult_Committed`` / ``HR_Mult_Economic`` / ``HR_Mult_Peaking`` —
      used only when no ``offer_curve_by_group`` covers the group. With an
      offer curve configured (the ERCOT default) the committed band uses
      ``base_hr × offer["committed"]``, the economic band is rendered as an
      N-slice rising ramp (``_econ_curve_steps``), and the CC peak band uses
      the turbine-class duct-burner multiplier — so the CSV ``HR_Mult_*``
      values are not the dispatched band heat rates. See ``bins_to_fleet``
      and ``docs/binning-methodology.md``.

    Args:
        csv_path: Path to ``custom-bin-assignments.csv``.

    Returns:
        One row per plant with columns: the original bin key columns,
        ``Plant_Code``, ``Plant_Name``, ``capacity_mw``, ``hr_weighted``
        (the plant's own HR), ``hr_mr`` / ``hr_mc`` / ``hr_econ`` /
        ``hr_peak`` (= ``Plant_Avg_HR × HR_Mult_<tranche>``),
        ``pct_mr`` / ``pct_mc`` / ``pct_econ`` / ``pct_peak``,
        ``min_run``, ``min_down``, ``plant_count`` (always 1),
        ``plant_codes`` (a one-element list with the plant code),
        ``fuel``.
    """
    detail = pd.read_csv(csv_path)
    fuel_series = detail["Plant_Group"].map(BIN_GROUP_TO_FUEL)
    unmapped = detail[fuel_series.isna()]
    if not unmapped.empty:
        groups = sorted(unmapped["Plant_Group"].unique())
        raise ValueError(
            f"CAMPD bins reference unknown plant groups: {groups}. "
            f"Add them to BIN_GROUP_TO_FUEL."
        )

    # Multi-tech CT correction: at mixed-facility plants (CC+CT, COAL+CT)
    # the plant-average HR is dominated by the efficient dominant technology,
    # making the CT bin 25-40% cheaper than a standalone CT. Clip multi-tech
    # CT heat rates to the standalone CT median for the ISO.
    if "Mixed_Facility" in detail.columns:
        ct_mask = detail["Plant_Group"] == "CT_PEAKER"
        mixed_mask = detail["Mixed_Facility"].notna() & (
            detail["Mixed_Facility"].astype(str).str.strip() != ""
        )
        multi_ct = ct_mask & mixed_mask
        if multi_ct.any():
            standalone_ct = ct_mask & ~mixed_mask
            median_ct_hr = (
                float(detail.loc[standalone_ct, "Plant_Avg_HR_MMBtu_MWh"].median())
                if standalone_ct.any()
                else 11.5
            )
            before = detail.loc[multi_ct, "Plant_Avg_HR_MMBtu_MWh"].copy()
            detail.loc[multi_ct, "Plant_Avg_HR_MMBtu_MWh"] = detail.loc[
                multi_ct, "Plant_Avg_HR_MMBtu_MWh"
            ].clip(lower=median_ct_hr)
            raised = (
                detail.loc[multi_ct, "Plant_Avg_HR_MMBtu_MWh"] > before + 1e-6
            ).sum()
            if raised:
                logger.info(
                    "Multi-tech CT HR correction: raised %d/%d CT(s) to "
                    "standalone median %.2f MMBtu/MWh",
                    int(raised),
                    int(multi_ct.sum()),
                    median_ct_hr,
                )

    # Each plant's tranche HR = Plant_Avg_HR × HR_Mult_<tranche>. We fill
    # missing plant heat rates with the per-group default and missing
    # multipliers with the group-typical value so the tranche arithmetic
    # is well-defined; tranches whose capacity is zero are skipped by
    # ``bins_to_fleet`` regardless of the resulting HR.
    plant_hr = [
        _fill_plant_hr(hr, grp)
        for hr, grp in zip(detail["Plant_Avg_HR_MMBtu_MWh"], detail["Plant_Group"])
    ]
    defaults_by_idx = [
        _DEFAULT_HR_MULT_BY_GROUP.get(grp, _DEFAULT_HR_MULT_BY_GROUP["CC_REGULAR"])
        for grp in detail["Plant_Group"]
    ]
    mult_columns = {
        "mr": "HR_Mult_Must_Run",
        "mc": "HR_Mult_Committed",
        "econ": "HR_Mult_Economic",
        "peak": "HR_Mult_Peaking",
    }
    bins = pd.DataFrame(
        {
            "Plant_Group": detail["Plant_Group"].astype(str),
            "ERCOT_Zone": detail["ERCOT_Zone"].astype(str),
            "Bin_Number": detail["Bin_Number"].astype(int),
            "Bin_Label": detail["Bin_Label"].astype(str),
            "Plant_Code": detail["Plant_Code"].astype(int),
            "Plant_Name": detail["Plant_Name"].astype(str),
            "Turbine_Class": detail["Turbine_Class"].astype(str),
            "capacity_mw": detail["Nameplate_MW"].astype(float),
            "hr_weighted": plant_hr,
            "pct_mr": detail["Pct_Must_Run"].astype(float),
            "pct_mc": detail["Pct_Committed"].astype(float),
            "pct_econ": detail["Pct_Economic"].astype(float),
            "pct_peak": detail["Pct_Peaking"].astype(float),
            "min_run": detail["Min_Run_Hours"].astype(int),
            "min_down": detail["Min_Down_Hours"].astype(int),
        }
    )
    for short, col in mult_columns.items():
        bins[f"hr_{short}"] = [
            hr * _fill_hr_multiplier(mult, defaults[short])
            for hr, mult, defaults in zip(plant_hr, detail[col], defaults_by_idx)
        ]
    bins["plant_count"] = 1
    bins["plant_codes"] = [[int(c)] for c in detail["Plant_Code"]]
    bins["fuel"] = fuel_series.values

    if year is not None:
        bins = _override_bin_class_from_eia923(bins, year)

    if capacity_reconcile_path is not None:
        bins = _reconcile_cc_capacity(bins, capacity_reconcile_path)

    bad = bins["pct_mr"] + bins["pct_mc"] + bins["pct_econ"] + bins["pct_peak"]
    if not (bad == 100).all():
        offending = bins.loc[bad != 100, "Plant_Name"].tolist()
        raise ValueError(
            f"CAMPD bin tranches must sum to 100%; offending plants: {offending}"
        )

    logger.info(
        "Loaded %d per-plant CAMPD bins from %s (%.1f GW)",
        len(bins),
        csv_path,
        bins["capacity_mw"].sum() / 1000.0,
    )
    return bins


# Default tranche split (% of nameplate) per group for the synthetic per-plant
# bins an ISO builds when it has no CAMPD bin sheet (see
# :func:`fleet_to_bins`): used only for plants absent from the CAMPD-derived
# thermal-tranche artifact (rarely-online units with no reliable observed
# floor). ``(must_run, committed, peaking)``; the economic band is the
# residual. Peakers carry no committed band; coal carries a baseload floor.
_DEFAULT_TRANCHE_PCT_BY_GROUP: dict[str, tuple[float, float, float]] = {
    "CC_REGULAR": (0.0, 45.0, 8.0),
    "CC_CHP": (0.0, 45.0, 8.0),  # must-run set to host steam in bins_to_fleet
    "CT_PEAKER": (0.0, 0.0, 7.0),
    "CT_CHP": (0.0, 30.0, 7.0),
    "ST_GAS": (0.0, 30.0, 15.0),
    "ST_CHP": (0.0, 30.0, 15.0),
    "COAL": (45.0, 5.0, 2.0),
}


@lru_cache(maxsize=16)
def thermal_tranche_overrides(
    iso: str,
    coal_online_pmin: bool = False,
) -> dict[tuple[int, str], tuple[float, float]]:
    """Return ``{(plant_code, group): (committed_pct, mustrun_pct)}`` for an ISO.

    Loads the per-plant CAMPD-derived committed and must-run tranche shares
    from ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (written by
    ``scripts/derive_thermal_tranches.py``). Empty when the ISO has no
    artifact, so the caller falls back to the group default. This is the
    general, ISO-agnostic replacement for the hardcoded ERCOT
    ``CC_REGULAR_COMMITTED_PCT_BY_PLANT`` / ``COAL_MUSTRUN_BY_PLANT`` maps.

    When ``coal_online_pmin`` is set (``ScenarioConfig.coal_mustrun_online_pmin``,
    rebuild step 2) a **coal** row's must-run is taken from the artifact's
    ``mustrun_online_pct`` column — the measured online-net-MW synchronization
    Pmin (~20-30% of nameplate) — instead of the all-hours available-CF
    ``mustrun_pct`` (which reads ~2x high for an always-online unit). Coal rows
    in an artifact that predates the column (or with a blank/NaN value) keep
    ``mustrun_pct``; non-coal rows are unaffected.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    has_online = "mustrun_online_pct" in df.columns
    out: dict[tuple[int, str], tuple[float, float]] = {}
    for r in df.itertuples(index=False):
        if str(getattr(r, "status", "ok")) != "ok":
            continue
        mustrun = float(r.mustrun_pct)
        if coal_online_pmin and has_online and str(r.plant_group) == "COAL":
            online_v = getattr(r, "mustrun_online_pct", float("nan"))
            if online_v == online_v:  # not NaN
                mustrun = float(online_v)
        out[(int(r.plant_code), str(r.plant_group))] = (
            float(r.committed_pct),
            mustrun,
        )
    return out


@lru_cache(maxsize=8)
def thermal_tranche_peaking(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, group): peaking_pct}`` for an ISO's CC plants.

    The CAMPD-derived duct-firing / scarcity share from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (``peaking_pct``, written
    by ``scripts/derive_thermal_tranches.py`` for CC_REGULAR / CC_CHP): the
    share of the plant's demonstrated sustained maximum it clears in fewer
    than 5% of its online hours. Empty when the ISO has no artifact or it
    predates the column. Applied per plant in :func:`bins_to_fleet` under
    ``config.cc_peaking_per_plant`` — the per-ISO measured analogue of the
    hand-set ERCOT :data:`CC_REGULAR_PEAKING_PCT_BY_PLANT` — superseding the
    offer curve's class-wide ``pct_peaking``.
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "peaking_pct" not in df.columns:
        return {}
    out: dict[tuple[int, str], float] = {}
    for r in df.itertuples(index=False):
        if str(getattr(r, "status", "ok")) != "ok" or pd.isna(r.peaking_pct):
            continue
        out[(int(r.plant_code), str(r.plant_group))] = float(r.peaking_pct)
    return out


from market_sim.data.coal import (  # noqa: E402
    _COAL_CHP_FLOOR_CAP_PCT,
    _COAL_CHP_FLOOR_FACTOR,
    COAL_PLANT_SUPPLY,
    _coal_class_for,
    coal_chp_overrides,
    coal_supply_class,
    coal_sync_online_frac,
    coal_takeorpay_share,
)


@lru_cache(maxsize=1)
def cc_duct_peaking_pct() -> dict[int, float]:
    """Return ``{plant_code: peaking_pct}`` for every EIA-860 CC plant.

    Built from the raw EIA-860 Generator_Y Operable sheet parquet
    (``eia860_generator_operable.parquet``): a plant is duct-fired when any
    of its combined-cycle generators carries the "Duct Burners" = Y flag
    (reported on the steam/CA rows). Duct-fired plants get the
    nameplate-vs-net-summer capability gap as their peaking share,
    ``100 x max(0, nameplate - net_summer) / nameplate`` summed over the
    plant's CC generators; non-duct CC plants get 0.0 — they have no
    duct-firing increment, so a class-uniform peak band hands them phantom
    scarcity capacity. (The EIA-860 release carries no separate duct-burner
    MW increment, so the capability gap is the proxy; for non-duct plants
    that same gap is ambient derate, already modeled by
    ``_SUMMER_CLASS_DERATE``.) Applied per plant under
    ``config.cc_duct_peaking``, superseding the offer curve's class-wide
    ``pct_peaking``. Plants absent from the sheet are absent from the map
    (callers keep their class default).
    """
    path = active_eia860_dir() / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Technology",
            "Duct Burners",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    if cc.empty:
        return {}
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["np"] = pd.to_numeric(cc["Nameplate Capacity (MW)"], errors="coerce")
    cc["ns"] = pd.to_numeric(cc["Summer Capacity (MW)"], errors="coerce")
    out: dict[int, float] = {}
    for code, grp in cc.groupby("plant_code"):
        np_sum = float(grp["np"].sum())
        if np_sum <= 0.0:
            continue
        if (grp["Duct Burners"].astype(str).str.strip() == "Y").any():
            ns_sum = float(grp["ns"].sum())
            out[int(code)] = round(100.0 * max(0.0, np_sum - ns_sum) / np_sum, 1)
        else:
            out[int(code)] = 0.0
    return out


@lru_cache(maxsize=1)
def cc_summer_capacity() -> dict[int, tuple[float, float]]:
    """Return ``{plant_code: (nameplate_mw, net_summer_mw)}`` for every CC plant.

    Summed over each plant's combined-cycle generators from the EIA-860
    Generator_Y Operable sheet. Consumed under
    ``config.cc_nameplate_summer_derate`` to (a) raise a CC plant's LP capacity
    from its net-summer rating to full nameplate and (b) derive the per-plant
    MEASURED summer derate ``net_summer / nameplate`` applied in the summer
    months — the correct seasonal capacity shape (full nameplate in winter,
    ambient-derated to net-summer in summer). Plants absent from the sheet are
    absent from the map (callers keep net-summer / the flat class derate).
    """
    path = active_eia860_dir() / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(
        path,
        columns=[
            "Plant Code",
            "Technology",
            "Nameplate Capacity (MW)",
            "Summer Capacity (MW)",
        ],
    )
    df = df[pd.to_numeric(df["Plant Code"], errors="coerce").notna()]
    cc = df[df["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    if cc.empty:
        return {}
    cc["plant_code"] = cc["Plant Code"].astype(float).astype(int)
    cc["np"] = pd.to_numeric(cc["Nameplate Capacity (MW)"], errors="coerce")
    cc["ns"] = pd.to_numeric(cc["Summer Capacity (MW)"], errors="coerce")
    out: dict[int, tuple[float, float]] = {}
    for code, grp in cc.groupby("plant_code"):
        np_sum = float(grp["np"].sum())
        ns_sum = float(grp["ns"].sum())
        if np_sum > 0.0 and ns_sum > 0.0:
            out[int(code)] = (np_sum, ns_sum)
    return out


def cc_summer_derate_ratio(plant_code: int) -> float | None:
    """Return a CC plant's measured summer availability multiplier.

    ``net_summer / nameplate`` from :func:`cc_summer_capacity`, clamped to
    ``(0, 1]`` (a plant whose summer rating meets or exceeds nameplate gets no
    derate). ``None`` when the plant is absent from the EIA-860 CC sheet.
    """
    cap = cc_summer_capacity().get(int(plant_code))
    if cap is None:
        return None
    nameplate, net_summer = cap
    if nameplate <= 0.0:
        return None
    return min(1.0, net_summer / nameplate)


def fleet_to_bins(
    generators: list[Generator], iso: str, config: ScenarioConfig
) -> pd.DataFrame:
    """Build a per-plant CAMPD-style bins frame from an ISO's EIA-860 fleet.

    The non-ERCOT analogue of the CAMPD bin sheet: each thermal
    ``(plant_code, plant_group)`` becomes one bin row in the schema
    :func:`bins_to_fleet` consumes, so a per-plant ISO (PJM, MISO, ...) gets
    the *same* smoothed rising offer curve and per-plant committed / must-run
    tranches ERCOT gets from its bins. Committed % and (coal) must-run % come
    from the CAMPD-derived artifact (:func:`thermal_tranche_overrides`; under
    ``config.coal_mustrun_online_pmin`` the coal must-run uses the artifact's
    online-Pmin floor, rebuild step 2); plants absent from it fall back to
    :data:`_DEFAULT_TRANCHE_PCT_BY_GROUP`. Per-band
    heat rates are the plant's capacity-weighted heat rate times the group
    default multipliers (the offer curve overrides these in ``bins_to_fleet``).
    Non-thermal generators (nuclear, oil, biomass, ...) are not binned — the
    caller keeps them as raw LP units.

    Returns one row per thermal ``(plant_code, plant_group)``; empty frame when
    the fleet has no thermal plants.
    """
    overrides = thermal_tranche_overrides(
        iso, getattr(config, "coal_mustrun_online_pmin", False)
    )
    peaking = thermal_tranche_peaking(iso)
    # Aggregate the per-generator fleet to one row per (plant, group): capacity
    # sums, heat rate is capacity-weighted.
    agg: dict[tuple[int, str], dict] = {}
    for g in generators:
        if g.plant_group not in BIN_GROUP_TO_FUEL:
            continue  # non-thermal (nuclear / oil / biomass) stays a raw unit
        code = int(g.plant_code)
        if code <= 0:
            continue
        key = (code, g.plant_group)
        a = agg.setdefault(
            key,
            {
                "cap": 0.0,
                "hr_cap": 0.0,
                "name": g.name,
                "zone": g.zone,
            },
        )
        a["cap"] += float(g.pmax_mw)
        a["hr_cap"] += float(g.pmax_mw) * float(g.heat_rate)

    rows: list[dict] = []
    for (code, group), a in agg.items():
        cap = a["cap"]
        if cap <= 0.0:
            continue
        # CC nameplate capacity (config.cc_nameplate_summer_derate): the fleet
        # carries each unit's net-summer rating, so a CC plant's summed cap is
        # net-summer. Rescale it up to full nameplate (cap / (net_summer /
        # nameplate)); the availability builder reapplies the per-plant summer
        # derate seasonally. Robust to fleet-vs-EIA membership differences (uses
        # the ratio, not the absolute nameplate). ERCOT/other groups unchanged.
        if group in ("CC_REGULAR", "CC_CHP") and getattr(
            config, "cc_nameplate_summer_derate", False
        ):
            _ratio = cc_summer_derate_ratio(code)
            if _ratio is not None and _ratio > 0.0:
                cap = cap / _ratio
        base_hr = a["hr_cap"] / cap if cap > 0 else _fill_plant_hr(None, group)
        d_mr, d_mc, d_peak = _DEFAULT_TRANCHE_PCT_BY_GROUP.get(group, (0.0, 30.0, 8.0))
        committed, mustrun = overrides.get((code, group), (d_mc, d_mr))
        pct_mc = committed
        pct_mr = mustrun if group == "COAL" else d_mr
        pct_peak = peaking.get((code, group), d_peak)
        # Keep the split feasible: clip committed + peaking to leave room for an
        # economic band above the must-run floor.
        room = max(0.0, 100.0 - pct_mr)
        if pct_mc + pct_peak > room:
            pct_mc = max(0.0, min(pct_mc, room - pct_peak))
        pct_econ = max(0.0, 100.0 - pct_mr - pct_mc - pct_peak)
        mults = _DEFAULT_HR_MULT_BY_GROUP.get(
            group, _DEFAULT_HR_MULT_BY_GROUP["CC_REGULAR"]
        )
        rows.append(
            {
                "Plant_Group": group,
                "ERCOT_Zone": a["zone"],
                "Bin_Number": 1,
                "Bin_Label": a["name"],
                "Plant_Code": code,
                "Plant_Name": a["name"],
                "Turbine_Class": "",
                "capacity_mw": cap,
                "hr_weighted": base_hr,
                "pct_mr": pct_mr,
                "pct_mc": pct_mc,
                "pct_econ": pct_econ,
                "pct_peak": pct_peak,
                "min_run": 0,
                "min_down": 0,
                "hr_mr": base_hr * mults["mr"],
                "hr_mc": base_hr * mults["mc"],
                "hr_econ": base_hr * mults["econ"],
                "hr_peak": base_hr * mults["peak"],
                "plant_count": 1,
                "plant_codes": [code],
                "fuel": BIN_GROUP_TO_FUEL[group],
            }
        )
    bins = pd.DataFrame(
        rows,
        columns=[
            "Plant_Group",
            "ERCOT_Zone",
            "Bin_Number",
            "Bin_Label",
            "Plant_Code",
            "Plant_Name",
            "Turbine_Class",
            "capacity_mw",
            "hr_weighted",
            "pct_mr",
            "pct_mc",
            "pct_econ",
            "pct_peak",
            "min_run",
            "min_down",
            "hr_mr",
            "hr_mc",
            "hr_econ",
            "hr_peak",
            "plant_count",
            "plant_codes",
            "fuel",
        ],
    )
    # Per-plant CC capacity reconciliation (ScenarioConfig.cc_capacity_reconcile)
    # for the synthesized-bins ISOs — the same hook the ERCOT curated-CSV path
    # gets via load_campd_bins. Applied after the summer-derate nameplate
    # rescale above, so a demonstrated-peak CAP row (mode="cap",
    # scripts/derive_cc_capacity_reconcile.py --mode cap) bounds the final LP
    # capacity at the plant's measured CAMPD sustained maximum.
    if not bins.empty and getattr(config, "cc_capacity_reconcile", False):
        bins = _reconcile_cc_capacity(
            bins, getattr(config, "cc_capacity_reconcile_path", "")
        )
    return bins


# Combined-cycle duct-burner (peaking) heat-rate multiplier by turbine class,
# on (AHR x fuel_price). Operator ranges: advanced G/H-class 2.3-2.5, F-class
# 2.0-2.3, older E-class / legacy 1.8-2.0 — a lower base AHR makes the
# duct-fire/base ratio steeper, so the most efficient classes carry the highest
# multiplier. Set 0.1 below the range midpoints per the operator's CC peaking
# tune.
CC_DUCT_BURNER_PEAK_MULT: dict[str, float] = {
    "advanced": 2.50,  # G/H-class
    "f": 2.25,  # F-class incl. E/F
    "older": 2.00,  # E-class, legacy
}


def cc_duct_burner_peak_mult(turbine_class: object) -> float:
    """Return the CC duct-burner peaking HR multiplier for a turbine class.

    Maps the CSV ``Turbine_Class`` string onto the operator's three duct-burner
    buckets (see :data:`CC_DUCT_BURNER_PEAK_MULT`). Unknown / blank classes
    fall back to the F-class midpoint (the modal CC class).
    """
    s = str(turbine_class)
    if "G-class" in s or "H-class" in s:
        return CC_DUCT_BURNER_PEAK_MULT["advanced"]
    if "F-class" in s:  # also catches "E/F-class"
        return CC_DUCT_BURNER_PEAK_MULT["f"]
    if "E-class" in s or "Legacy" in s:
        return CC_DUCT_BURNER_PEAK_MULT["older"]
    return CC_DUCT_BURNER_PEAK_MULT["f"]


# Coal supply class -> offer_curve_by_group key (COAL_LIGNITE / COAL_PRB /
# COAL_BIT / COAL_WC; sub-bituminous routes to COAL_PRB), from the canonical
# taxonomy; unclassified coal uses the generic COAL curve. Kept under the
# local name for back-compat.
_COAL_SUPPLY_TO_CURVE = COAL_SUPPLY_TO_CLASS


@lru_cache(maxsize=8)
def ct_intermediate_plants(iso: str, threshold: float) -> frozenset[int]:
    """EIA plant codes of intermediate-duty ``CT_PEAKER`` units for an ISO.

    A simple-cycle combustion turbine whose measured CAMPD median capacity
    factor (``thermal_tranches_<ISO>.csv`` ``median_cf``) is at or above
    ``threshold`` runs intermediate / near-baseload duty, not as a true
    peaker. EIA-860 confirms these are genuine GT / IC simple-cycle units (not
    mislabeled combined cycle or cogen), so their prime-mover *classification*
    is correct — what differs is their *duty cycle*. The single steep
    ``CT_PEAKER`` offer curve (a committed-band start-cost hurdle that holds
    true peakers idle) mis-prices these always-on units above the CC fleet, so
    they never clear and CC over-runs. The cohort is routed to the flatter
    ``CT_INTERMEDIATE`` offer curve instead.

    The median CF is a durable, forward-reproducible duty-role signal — it
    regenerates per unit and year from CAMPD and responds to changed
    conditions (a unit that stops running intermediate falls out of the
    cohort) — and assigns an offer *shape*, never pins measured output, so it
    is admissible under CLAUDE.md #11/#12 on the same basis as
    :data:`market_sim.data.outages.ST_GAS_PEAKER_PLANTS`. Returns an empty set
    when the ISO has no tranche file (e.g. ERCOT's hand-set bins).
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path)
    if "median_cf" not in df.columns or "plant_group" not in df.columns:
        return frozenset()
    ct = df[(df["plant_group"] == "CT_PEAKER") & (df["median_cf"] >= threshold)]
    codes = set(int(c) for c in ct["plant_code"].dropna())

    # Exclude CTs at multi-technology sites (COAL+CT, CC+CT, etc.): the CT
    # at such a plant is a supplemental peaker, not an intermediate-duty
    # unit, so it keeps the steep CT_PEAKER curve.
    bin_path = PROCESSED_DIR / f"bin_assignments_{iso.upper()}.csv"
    if bin_path.exists() and codes:
        bins_df = pd.read_csv(
            bin_path, usecols=["Plant_Code", "Plant_Group", "Mixed_Facility"]
        )
        ct_bins = bins_df[bins_df["Plant_Group"] == "CT_PEAKER"]
        mixed = set(
            int(c)
            for c in ct_bins.loc[
                ct_bins["Mixed_Facility"].notna()
                & (ct_bins["Mixed_Facility"].astype(str).str.strip() != ""),
                "Plant_Code",
            ].dropna()
        )
        codes -= mixed

    return frozenset(codes)


def st_gas_intermediate_plants(iso: str, threshold: float) -> frozenset[int]:
    """EIA plant codes of intermediate-duty ``ST_GAS`` units for an ISO.

    The gas-steam analogue of :func:`ct_intermediate_plants`. A legacy gas-steam
    plant whose measured CAMPD median capacity factor
    (``thermal_tranches_<ISO>.csv`` ``median_cf``) is at or above ``threshold``
    runs intermediate / near-baseload duty (MISO's Harding Street, Ames, Nine
    Mile Point, Lewis Creek, Sabine, ...), not as a peaker. The ERCOT-fitted
    ST_GAS offer curve (steep econ_high ramp + a 15% peaking band) prices most of
    each such unit above the CC fleet, so it never clears and the model
    under-runs it (the Moselle / Lewis Creek under-run). The cohort is routed to
    the flatter ``ST_GAS_INTERMEDIATE`` offer curve instead.

    The median CF is a durable, forward-reproducible duty-role signal — it
    regenerates per unit and year from CAMPD and responds to changed conditions
    — and assigns an offer *shape*, never pins measured output, so it is
    admissible under CLAUDE.md #11/#12 on the same basis as
    :func:`ct_intermediate_plants` and :data:`outages.ST_GAS_PEAKER_PLANTS`.
    Returns an empty set when the ISO has no tranche file (e.g. ERCOT's hand-set
    bins).
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path)
    if "median_cf" not in df.columns or "plant_group" not in df.columns:
        return frozenset()
    st = df[(df["plant_group"] == "ST_GAS") & (df["median_cf"] >= threshold)]
    return frozenset(int(c) for c in st["plant_code"].dropna())


def cc_intermediate_plants(iso: str, threshold: float) -> frozenset[int]:
    """EIA plant codes of intermediate-duty ``CC_REGULAR`` units for an ISO.

    The combined-cycle analogue of :func:`ct_intermediate_plants` /
    :func:`st_gas_intermediate_plants`. A combined-cycle plant whose measured
    CAMPD median capacity factor (``thermal_tranches_<ISO>.csv`` ``median_cf``)
    is at or above ``threshold`` runs intermediate / baseload duty, not as a
    flexible mid-merit peaker. The ``CC_REGULAR`` offer curve was fit to ERCOT's
    duct-fire-heavy 2x1 CCs (Colorado Bend II / Wolf Hollow II): a rising econ
    ramp (start-cost-amortized) topped by a duct-burner peak band. For a fleet of
    already-committed, high-CF baseload CCs (MISO's entire CC fleet measures a
    median CF of 50-150 %, mean ~90 %) that rising ramp over-prices the upper
    operating range — the incremental energy of a committed CC is near its
    full-load heat rate (~0.93x its own average), flat across load, not a
    start-cost-amortized peaker bid — so the upper econ tranches sit above the
    clearing price and the model under-runs the CC fleet (the MISO gas under-run).
    The cohort is routed to the flatter ``CC_INTERMEDIATE`` offer curve, which
    flattens the econ ramp to the measured near-baseload incremental cost while
    **keeping** the physically-real duct-burner peak band (the duct-fire reach is
    still priced at its true ~2.25x heat rate — only the operating-range ramp is
    corrected, never the peak).

    The median CF is a durable, forward-reproducible duty-role signal — it
    regenerates per unit and year from CAMPD and responds to changed conditions
    (a CC that stops running baseload falls out of the cohort) — and assigns an
    offer *shape*, never pins measured output, so it is admissible under
    CLAUDE.md #11/#12 on the same basis as :func:`ct_intermediate_plants` and
    :func:`st_gas_intermediate_plants`. Returns an empty set when the ISO has no
    tranche file (e.g. ERCOT's hand-set bins).
    """
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return frozenset()
    df = pd.read_csv(path)
    if "median_cf" not in df.columns or "plant_group" not in df.columns:
        return frozenset()
    cc = df[(df["plant_group"] == "CC_REGULAR") & (df["median_cf"] >= threshold)]
    return frozenset(int(c) for c in cc["plant_code"].dropna())


# five ``HR_Mult_*`` are per-tranche multipliers on the plant's base HR. Other
# columns in the sheet (names, group, config, turbine class …) are reference
# only and ignored by the loader.
PLANT_TRANCHE_OVERRIDE_FIELDS: dict[str, str] = {
    "pct_mr": "Pct_Must_Run",
    "pct_mc": "Pct_Committed",
    "pct_lo": "Pct_Econ_Low",
    "pct_hi": "Pct_Econ_High",
    "pct_pk": "Pct_Peaking",
    "hr_mr": "HR_Mult_Must_Run",
    "hr_mc": "HR_Mult_Committed",
    "hr_lo": "HR_Mult_Econ_Low",
    "hr_hi": "HR_Mult_Econ_High",
    "hr_pk": "HR_Mult_Peaking",
}


@lru_cache(maxsize=8)
def load_plant_tranche_config(path: str | Path) -> dict[int, dict[str, float]]:
    """Load the per-plant tranche-config override sheet, keyed by plant code.

    Each row gives one plant's five tranche shares of nameplate and five
    per-tranche heat-rate multipliers (see :data:`PLANT_TRANCHE_OVERRIDE_FIELDS`).
    Returned as ``{plant_code: {pct_mr, pct_mc, pct_lo, pct_hi, pct_pk, hr_mr,
    hr_mc, hr_lo, hr_hi, hr_pk}}`` for :func:`bins_to_fleet` to apply in place of
    the offer curve / per-plant dicts. Rows with a blank or non-numeric value in
    any required column are skipped (so a partially edited sheet still loads).
    """
    df = pd.read_csv(path)
    missing = [c for c in PLANT_TRANCHE_OVERRIDE_FIELDS.values() if c not in df.columns]
    if "Plant_Code" not in df.columns or missing:
        raise ValueError(
            f"tranche-config sheet {path} missing columns: "
            f"{(['Plant_Code'] if 'Plant_Code' not in df.columns else []) + missing}"
        )
    out: dict[int, dict[str, float]] = {}
    for _, row in df.iterrows():
        try:
            rec = {
                key: float(row[col])
                for key, col in PLANT_TRANCHE_OVERRIDE_FIELDS.items()
            }
            code = int(row["Plant_Code"])
        except (TypeError, ValueError):
            continue
        if any(v != v for v in rec.values()):  # NaN in a required cell
            continue
        out[code] = rec
    return out


def bins_to_fleet(
    bins: pd.DataFrame,
    zone_names: list[str],
    config: ScenarioConfig,
) -> tuple[list[Generator], FleetArrays]:
    """Convert per-plant CAMPD bins into LP generators -- stepped tranches.

    Each input row is one EIA plant ("one bin per plant"); its
    grid-facing capacity is split into LP-dispatchable tranches keyed to
    the CSV percentages and per-tranche heat rates. A bin only gets
    tranches whose capacity is non-zero:

      - ``_mustrun`` -- COAL ONLY. The unit's minimum operating floor:
        mine-mouth take-or-pay, start/stop and cycling damage avoidance,
        environmental minimum-gen / CEMS compliance and ERCOT RUC. Bids
        at VOM + carbon + NOx only (the fuel cost is sunk) via fuel_fracs
        in the runner, so it is always in merit without a Pmin floor.
        Non-coal bins' must-run share is host-steam (CHP) cogen and is
        removed from LP capacity -- it serves industrial process steam,
        not the grid; its generation and emissions are added back by
        post-processing (see
        :func:`market_sim.results.emissions.compute_must_run_emissions`).
      - ``_committed`` -- the part-load range when started. Carries the
        bin's start cost and min-run window -- starting this tranche is
        starting the plant.
      - ``_econ`` -- incremental dispatch above the part-load range, the
        most efficient slice of the unit.
      - ``_peak`` -- duct-firing / overfire tranche, heat rate scaled by
        the CSV's ``HR_Mult_Peaking`` so scarcity output bids highest.

    Per-tranche heat rates are the plant's own ``Plant_Avg_HR`` scaled by
    the CSV ``HR_Mult_<tranche>`` columns — assembled in
    :func:`load_campd_bins` — so each plant brings its measured heat rate
    and OEM-typical part-load / peaking penalties into the LP. No tranche
    carries a Pmin floor; the Committed and Economic tranches are the
    same physical unit, so the P2 commitment screen starts and stops them
    together (see
    :func:`market_sim.model.commitment.apply_commitment_with_coal_pin`).
    Economic and Peaking are incremental loading of a running unit, so
    they carry neither a start cost nor a min-run window.

    Args:
        bins: The per-plant frame from :func:`load_campd_bins` (one row
            per plant).
        zone_names: The ISO's ordered zone names.
        config: Scenario configuration (unknown-zone default, registry
            path, horizon length).

    Returns:
        A tuple ``(generators, fleet_arrays)``: the bin-derived generator
        list and its vectorized form.
    """
    valid_zones = set(zone_names)
    fleet: list[Generator] = []

    # Per-plant commission years drive the age-based thermal availability
    # model. Coal uses the curated COAL_PLANT_COMMISSION_YEAR (accurate
    # coal-unit years); every other plant takes its EIA-860 ``year_built``
    # from the master plant registry. Plants absent from the registry fall
    # back to 2010 — a recent-but-not-modern vintage.
    registry = load_plant_registry(config.plant_registry_path)
    _reg_year = dict(zip(registry["plantid"], registry["year_built"]))

    # Oil-primary fuel correction: EIA-860 Petroleum-Liquids combustion-turbine
    # peakers (e.g. Morgan Creek 3492) sit in the gas CT_PEAKER class on the bin
    # sheet but physically burn distillate, so the LP otherwise prices them on
    # cheap Waha gas and floats them baseload. When enabled, their gas-CT fuel
    # is overridden to ``oil`` (priced at OIL_PRICE_PER_MMBTU) — a measured
    # EIA-860 correction, not a residual adder. Restricted to gas_ct so legacy
    # gas steam/CC bins are never reclassified. See oil_primary_bin_plants.
    # Two measured EIA-860 layers: ERCOT keeps its curated master-registry
    # plant-primary screen exactly (its keepers were solved on it — a silent
    # set change here would break their reproducibility, the 0c6c833 failure
    # mode); the per-plant non-ERCOT ISOs, which the registry cannot cover,
    # use the generator-level Energy-Source-1 majority screen
    # (oil_primary_ct_plants_from_eia860) instead.
    _oil_primary_iso = getattr(config, "iso", "ERCOT") or "ERCOT"
    _oil_primary = (
        (
            oil_primary_bin_plants(config.plant_registry_path)
            if _oil_primary_iso == "ERCOT"
            else oil_primary_ct_plants_from_eia860(_oil_primary_iso)
        )
        if getattr(config, "oil_primary_bin_fuel", False)
        else frozenset()
    )

    # Fast-start amortization v3 (tranche_startup_measured_runs): per-plant
    # CAMPD-measured median CT start-to-stop run lengths, the measured
    # amortization-horizon ceiling for the fast-start CT tranches. Empty when
    # the flag is off or the ISO has no committed artifact (v2 P0 basis).
    _fsp_run_lengths: dict[int, float] = (
        campd_ct_run_lengths(getattr(config, "iso", "ERCOT"))
        if (
            getattr(config, "tranche_startup_amortization", False)
            and getattr(config, "tranche_startup_measured_runs", False)
        )
        else {}
    )

    # Optional per-plant tranche-config override sheet: when set, each listed
    # plant's tranche shares + per-band HR multipliers come straight from the
    # sheet, bypassing the offer curve and the per-plant committed/peaking dicts.
    tranche_ov: dict[int, dict[str, float]] = {}
    _ov_path = getattr(config, "plant_tranche_config_path", None)
    if _ov_path:
        tranche_ov = load_plant_tranche_config(_ov_path)

    def _commission_year(plant_code: int) -> int:
        """Return the EIA-860 commission year for ``plant_code``."""
        year = _reg_year.get(plant_code)
        if year and not pd.isna(year):
            return int(year)
        return 2010

    # Coal cogens (PJM): a coal plant whose EIA-860 sector is a CHP host follows
    # its host steam contract, not the LMP, so its coal bin is routed through the
    # same behind-the-meter / steam-following holdout as the gas cogens — host
    # self-supply removed from the LP, the grid remainder a must-run floor —
    # rather than dispatched as an economic COAL_BIT/WC tranche. Keyed by plant
    # code -> (measured min-month avg MW floor, sector class). Empty unless the
    # CHP machinery is on and the ISO is PJM.
    coal_chp = (
        coal_chp_overrides(
            getattr(config, "iso", "ERCOT"),
            int(getattr(config, "weather_year", 0) or 0),
        )
        if getattr(config, "chp_steam_following", False)
        else {}
    )

    # Measured steam-following export level (backcast overlay,
    # config.chp_export_floor_measured): the year's per-(plant, class) EIA-923
    # net generation, which replaces the pooled CAMPD p2 minimum as the CHP
    # total must-run CF below — see the ScenarioConfig field for the physics
    # and the rule-#13 admissibility argument. Empty (no override) in forecast
    # mode or when the flag is off.
    chp_measured_netgen: dict[tuple[int, str], float] = {}
    if (
        getattr(config, "chp_steam_following", False)
        and getattr(config, "chp_export_floor_measured", False)
        and getattr(config, "mode", "forecast") == "backcast"
        and int(getattr(config, "weather_year", 0) or 0) > 0
    ):
        chp_measured_netgen = chp_class_netgen_mwh(
            int(getattr(config, "weather_year", 0) or 0)
        )

    for _, b in bins.iterrows():
        pct_mr = float(b["pct_mr"])
        nameplate = float(b["capacity_mw"])
        fuel = BIN_GROUP_TO_FUEL[b["Plant_Group"]]
        # Reprice EIA-860 oil-primary combustion-turbine peakers on distillate
        # (only gas_ct bins, so gas steam/CC are untouched and coal can never
        # flip). plant_group stays CT_PEAKER, so reserve/offer-curve logic is
        # unchanged — only the burned fuel changes.
        if fuel == "gas_ct" and int(b["Plant_Code"]) in _oil_primary:
            fuel = "oil"
        ov = tranche_ov.get(int(b["Plant_Code"]))
        # Coal must-run override (calibration): per-plant CAMPD-derived floor
        # (config.coal_mustrun_per_plant) takes precedence; otherwise the
        # uniform lignite/PRB supply override (sweep). The grid tranches
        # rescale via `denom`.
        if fuel == "coal":
            _pc = int(b["Plant_Code"])
            _supply = COAL_PLANT_SUPPLY.get(_pc, "")
            if config.coal_mustrun_per_plant and _pc in COAL_MUSTRUN_BY_PLANT:
                pct_mr = COAL_MUSTRUN_BY_PLANT[_pc]
            elif (
                _supply == "lignite"
                and config.coal_lignite_mustrun_override is not None
            ):
                pct_mr = config.coal_lignite_mustrun_override
            elif _supply == "prb" and config.coal_prb_mustrun_override is not None:
                pct_mr = config.coal_prb_mustrun_override
            # PJM bituminous spot-coal: NOT mine-mouth take-or-pay, so it is the
            # marginal/price-responsive swing fuel rather than held-flat
            # baseload. Zeroing its must-run floor moves all of its capacity into
            # the rising offer-curve tranches (committed/econ/peak, Pmin=0),
            # which bid full delivered cost (coal_bit_passthrough_floor=1.0) and
            # back down when gas undercuts them. Faithful to the contract physics
            # (CLAUDE.md #1/#11), not tuned to a coal-MWh residual; PRB/lignite/
            # waste keep their take-or-pay floors above.
            if (
                getattr(config, "coal_bit_dispatchable", False)
                and coal_supply_class(_pc) == "bituminous"
            ):
                pct_mr = 0.0
        # Coal cogen: a coal bin at a CHP-host plant (Eastman, St Nicholas, John
        # B Rich, ...) is held out at its sector behind-the-meter share and
        # carries a measured steam-following grid floor instead of staying in the
        # LP as economic coal. ``coal_chp_floor_mw`` (measured min-month avg MW)
        # sizes the floor below; the merchant CFB / culm fleet (sector 1/2) is
        # absent from ``coal_chp`` and keeps its in-LP coal must-run tranche.
        coal_chp_floor_mw: float | None = None
        coal_chp_sector: str | None = None
        if fuel == "coal" and int(b["Plant_Code"]) in coal_chp:
            coal_chp_floor_mw, coal_chp_sector = coal_chp[int(b["Plant_Code"])]
            pct_mr = CHP_BTM_PCT_BY_SECTOR.get(
                coal_chp_sector, CHP_BTM_PCT_BY_SECTOR["merchant"]
            )
        # Steam-following cogen treatment: a CC_CHP bin's behind-the-meter host
        # self-supply (removed from the grid, added back in the report) is
        # chp_btm_floor_pct of nameplate, not the CSV Pct_Must_Run merchant
        # split. Overriding pct_mr here shrinks the removed share and grows the
        # grid-facing capacity, which the steam floor + expensive load-following
        # below then shape into base + dispatchable rather than a flat slab.
        chp_following = str(b["Plant_Group"]) in (
            "CC_CHP",
            "CT_CHP",
            "ST_CHP",
        ) and getattr(config, "chp_steam_following", False)
        if chp_following:
            pct_mr = chp_btm_pct(
                int(b["Plant_Code"]),
                str(b["Plant_Group"]),
                iso=getattr(config, "iso", "ERCOT"),
            )
        # Petra Nova runs on its own classification (see PETRA_NOVA_* above):
        # one tranche at the capture train's net capacity, forced to
        # PETRA_NOVA_MIN_CF whenever the outage overlay says it is up. No
        # offer-curve bands — the 45Q credit makes it insensitive to price.
        if chp_following and int(b["Plant_Code"]) == PETRA_NOVA_PLANT_CODE:
            _pn_zone = str(b["ERCOT_Zone"])
            if _pn_zone == "Unknown" or _pn_zone not in valid_zones:
                _pn_zone = config.unknown_zone_default
            _pn_cap = nameplate * (1.0 - PETRA_NOVA_PARASITIC_PCT / 100.0)
            _pn_hr = float(b["hr_weighted"])
            fleet.append(
                Generator(
                    unit_id=f"CT_CHP_{_pn_zone}_p{PETRA_NOVA_PLANT_CODE}_ccs",
                    name=f"{b.get('Plant_Name', 'Petra Nova')} ccs",
                    zone=_pn_zone,
                    fuel_type=BIN_GROUP_TO_FUEL["CT_CHP"],
                    efficiency_bin="CT_CHP",
                    pmax_mw=_pn_cap,
                    pmin_mw=0.0,
                    heat_rate=_pn_hr,
                    vom=get_vom(BIN_GROUP_TO_FUEL["CT_CHP"]),
                    emission_rate_co2=get_emission_rate(
                        BIN_GROUP_TO_FUEL["CT_CHP"], _pn_hr
                    ),
                    nox_rate=get_nox_rate(BIN_GROUP_TO_FUEL["CT_CHP"]),
                    eford=get_eford(BIN_GROUP_TO_FUEL["CT_CHP"]),
                    online_year=_commission_year(PETRA_NOVA_PLANT_CODE),
                    is_campd_bin=True,
                    plant_group="CT_CHP",
                    bin_label=str(b["Bin_Label"]),
                    plant_code=PETRA_NOVA_PLANT_CODE,
                    chp_grid_pmin_mw=PETRA_NOVA_MIN_CF * _pn_cap,
                )
            )
            continue
        if ov is not None:
            pct_mr = ov["pct_mr"]
        # Coal must-run capacity stays IN the LP as a ``_mustrun`` tranche
        # (its fuel is sunk under take-or-pay; bids at VOM + carbon + NOx
        # only via the runner). Non-coal bins' must-run share — and a coal
        # cogen's host self-supply — is removed from LP capacity; its generation
        # and emissions are added back by post-processing (the coal cogen via
        # _btm_frame, the gas CHP via compute_must_run_emissions).
        if fuel == "coal" and coal_chp_sector is None:
            mustrun_cap = nameplate * pct_mr / 100.0
            grid_cap = nameplate - mustrun_cap
        else:
            mustrun_cap = 0.0
            grid_cap = nameplate * (1.0 - pct_mr / 100.0)
        if grid_cap + mustrun_cap <= 0.0:
            continue

        # SRMC-priced synchronization split (rebuild step 3a,
        # config.coal_sync_srmc_tranche). The coal min-load band (sized to the
        # measured online Pmin under coal_mustrun_online_pmin) is split by the
        # measured contract share into a fuel-free contracted floor (_mustrun)
        # and a spot remainder priced at full SRMC (_sync). BOTH are forced on
        # below (coal_sync_pmin_mw -> min_gen) so the unit holds synchronized at
        # min-load instead of price-following to zero, while the dispatchable
        # tranches above still back down in cheap hours. The split preserves the
        # total min-load (mr + sync = original mustrun_cap), so grid_cap and the
        # tranches above are unchanged. Plants absent from the take-or-pay map
        # are treated as fully contracted (share=1.0): all min-load fuel-free,
        # no _sync band — the step-2 sizing, now forced on.
        coal_sync = (
            fuel == "coal"
            and coal_chp_sector is None
            and mustrun_cap > 0.0
            and getattr(config, "coal_sync_srmc_tranche", False)
            and getattr(config, "coal_mustrun_online_pmin", False)
        )
        sync_cap = 0.0
        sync_online_frac = 1.0
        if coal_sync:
            _share = coal_takeorpay_share(int(b["Plant_Code"]))
            _share = 1.0 if _share is None else min(1.0, max(0.0, float(_share)))
            sync_cap = mustrun_cap * (1.0 - _share)  # spot, full SRMC
            mustrun_cap = mustrun_cap * _share  # contracted, fuel-free
            # Online%-scaled forcing: the measured share of the year the plant is
            # synchronized. ~1.0 (supercritical) -> floor held all 8760 h; a
            # cycler -> floor held only in its top-load online hours. Plants
            # absent from the artifact keep the force-all default (1.0).
            sync_online_frac = coal_sync_online_frac(
                getattr(config, "iso", "ERCOT") or "ERCOT"
            ).get(int(b["Plant_Code"]), 1.0)

        group = str(b["Plant_Group"])
        plant_code = int(b["Plant_Code"])
        offer = _offer_curve_for_group(group, plant_code, config)
        # Committed-tranche % (minimum stable load once started). The CSV
        # Pct_Committed is a coarse assumed value; for CC_REGULAR plants with
        # CAMPD-observed minimum stable load it is replaced by the per-plant
        # grounded value (CC_REGULAR_COMMITTED_PCT_BY_PLANT) — the economic
        # tranche below absorbs the difference. Off unless the calibration
        # config sets cc_committed_per_plant.
        pct_mc = float(b["pct_mc"])
        if offer is not None and "pct_committed" in offer:
            pct_mc = float(offer["pct_committed"])
        if (
            group == "CC_REGULAR"
            and getattr(config, "cc_committed_per_plant", False)
            and plant_code in CC_REGULAR_COMMITTED_PCT_BY_PLANT
        ):
            pct_mc = CC_REGULAR_COMMITTED_PCT_BY_PLANT[plant_code]
        # Peaking %: the offer curve may override the CSV value before the
        # residual is split into the two economic steps (residual = 100 -
        # must_run - committed - peaking).
        pct_peak = float(b["pct_peak"])
        if offer is not None and "pct_peaking" in offer:
            pct_peak = float(offer["pct_peaking"])
        if group in ("CC_REGULAR", "CC_CHP") and getattr(
            config, "cc_peaking_per_plant", False
        ):
            # Per-plant CAMPD-derived duct-firing share from the ISO's
            # thermal-tranche artifact (thermal_tranche_peaking), superseding
            # the offer curve's class-wide pct_peaking; the hand-set ERCOT
            # map below stays the final word for its four plants.
            _pk = thermal_tranche_peaking(
                (getattr(config, "iso", "ERCOT") or "ERCOT")
            ).get((plant_code, group))
            if _pk is not None:
                pct_peak = _pk
        if group in ("CC_REGULAR", "CC_CHP") and getattr(
            config, "cc_duct_peaking", False
        ):
            # Per-plant EIA-860 duct-burner peaking share: duct-fired plants
            # get their capability gap, non-duct CCs get 0 (no phantom
            # scarcity band). Supersedes the class-wide pct_peaking and the
            # tranche artifact above; the ERCOT hand-set map below stays the
            # final word for its plants.
            _dpk = cc_duct_peaking_pct().get(plant_code)
            if _dpk is not None:
                # Cap the band at the F-class supplementary-firing physical
                # maximum: the raw nameplate-vs-net-summer gap folds the ambient
                # summer derate into the duct band, oversizing it for high-gap
                # plants and dropping the price wall below the real duct point.
                _cap = getattr(config, "cc_duct_peaking_cap_pct", None)
                pct_peak = min(_dpk, float(_cap)) if _cap is not None else _dpk
        if (
            group == "CC_REGULAR"
            and getattr(config, "cc_peaking_per_plant", False)
            and plant_code in CC_REGULAR_PEAKING_PCT_BY_PLANT
        ):
            pct_peak = CC_REGULAR_PEAKING_PCT_BY_PLANT[plant_code]
        if ov is not None:
            pct_mc, pct_peak = ov["pct_mc"], ov["pct_pk"]
        denom = 100.0 - pct_mr
        committed_cap = grid_cap * pct_mc / denom if denom > 0.0 else 0.0
        peak_cap = grid_cap * pct_peak / denom if denom > 0.0 else 0.0
        # The steam-following BTM substitution above can leave committed +
        # peaking exceeding the grid share (a cogen whose measured committed
        # floor is ~70% of nameplate against a 35% BTM pull-out, e.g. Elk
        # Hills / Marcus Hook); clamp into grid_cap — committed keeps its
        # measured level, the scarcity peak gives way — so the LP never
        # carries more capacity than the grid-facing share.
        if committed_cap + peak_cap > grid_cap:
            committed_cap = min(committed_cap, grid_cap)
            peak_cap = max(0.0, min(peak_cap, grid_cap - committed_cap))
        econ_cap = max(grid_cap - committed_cap - peak_cap, 0.0)

        zone = str(b["ERCOT_Zone"])
        if zone == "Unknown" or zone not in valid_zones:
            zone = config.unknown_zone_default

        label = str(b["Bin_Label"])
        plant_name = str(b.get("Plant_Name") or label)
        # One bin = one plant, so the unit id is anchored on the plant
        # code; the tranche suffix keeps the four sub-generators distinct.
        bin_id = f"{group}_{zone}_p{plant_code}"

        coal_supply = ""
        if fuel == "coal":
            coal_supply = coal_supply_class(plant_code)
            commission_year = COAL_PLANT_COMMISSION_YEAR.get(
                plant_code, _commission_year(plant_code)
            )
        else:
            commission_year = _commission_year(plant_code)
        startup = BIN_STARTUP_COST_PER_MW.get(group, 0.0)

        base_hr = float(b["hr_weighted"])
        mustrun_hr = float(b["hr_mr"])
        committed_hr = float(b["hr_mc"])
        econ_hr = float(b["hr_econ"])
        peak_hr = float(b["hr_peak"])
        if offer is not None:
            # Unified offer curve: committed and peaking band heat rates from
            # the multipliers (econ_low / econ_high are set in the econ split
            # below). The peak band is a separate flat tranche; its height is
            # the curve's "peak" multiplier when given, else (CC only) the
            # per-plant duct-burner multiplier by turbine class. VOM is held
            # constant across bands (the peak band's VOM markup is dropped).
            committed_hr = base_hr * float(offer["committed"])
            if "peak" in offer:
                peak_hr = base_hr * float(offer["peak"])
            elif group in ("CC_REGULAR", "CC_CHP"):
                peak_hr = base_hr * cc_duct_burner_peak_mult(b.get("Turbine_Class"))
            else:
                peak_hr = base_hr * float(offer["peak"])
        else:
            # Legacy per-class supply-curve overrides (relative to base HR),
            # used when no offer curve covers the group: CC committed/econ/peak,
            # reliability ST_GAS (peakers keep CSV heat rates), and CT_CHP.
            cc_mc = config.cc_committed_hr_override
            if group in ("CC_REGULAR", "CC_CHP") and cc_mc is not None:
                committed_hr = base_hr * cc_mc
                econ_hr = base_hr * _hr_override(
                    config.cc_econ_hr_override, CC_ECON_HR_OVERRIDE_DEFAULT
                )
                peak_hr = base_hr * _hr_override(
                    config.cc_peak_hr_override, CC_PEAK_HR_OVERRIDE_DEFAULT
                )
            st_mc = config.gas_st_committed_hr_override
            if (
                group == "ST_GAS"
                and plant_code not in ST_GAS_PEAKER_PLANTS
                and st_mc is not None
            ):
                committed_hr = base_hr * st_mc
                econ_hr = base_hr * _hr_override(
                    config.gas_st_econ_hr_override, GAS_ST_ECON_HR_OVERRIDE_DEFAULT
                )
                peak_hr = base_hr * _hr_override(
                    config.gas_st_peak_hr_override, GAS_ST_PEAK_HR_OVERRIDE_DEFAULT
                )
            ct_mc = config.ct_committed_hr_override
            if group == "CT_CHP" and ct_mc is not None:
                committed_hr = base_hr * ct_mc
                econ_hr = base_hr * _hr_override(
                    config.ct_econ_hr_override, CT_ECON_HR_OVERRIDE_DEFAULT
                )
                peak_hr = base_hr * _hr_override(
                    config.ct_peak_hr_override, CT_PEAK_HR_OVERRIDE_DEFAULT
                )
        if ov is not None:
            # Per-plant sheet wins: all band heat rates are base_HR x the sheet's
            # multipliers (econ-low/-high set in the econ split below).
            mustrun_hr = base_hr * ov["hr_mr"]
            committed_hr = base_hr * ov["hr_mc"]
            peak_hr = base_hr * ov["hr_pk"]
        # CHP steam-following grid floor pinned onto the econ tranche: the
        # plant's total must-run (p2 CAMPD gross CF) net of its BTM share, i.e.
        # the steady export delivered to the grid above host self-supply. The
        # BTM share is a fraction of the plant's *generation* (host self-supply
        # scales with output, same basis the report add-back uses), so the
        # grid-delivered floor is pmin_cf * (1 - btm). Subtracting the BTM as
        # raw nameplate-percentage points zeroed the floor whenever a plant's
        # observed must-run ran below its BTM share (e.g. San Jacinto: pmin
        # 34.6 < BTM 40), leaving inefficient CT_CHP cogens to idle instead of
        # delivering their steady steam-following export. The floor comes from
        # the ISO's derived artifact (CAMPD p2, EIA-923 CF fallback) with the
        # hardcoded ERCOT CAMPD map behind it; plants with neither export
        # surplus only.
        chp_pmin_mw = 0.0
        pmin_cf = None
        if chp_following:
            pmin_cf = chp_pmin_cf(plant_code, iso=getattr(config, "iso", "ERCOT"))
            # Measured steam-following level (chp_export_floor_measured): the
            # plant's EIA-923 class CF for the solved year supersedes the
            # pooled CAMPD p2 minimum — the host-driven operating level the
            # steam contract sustains, not the never-below floor. The grid
            # floor formula below is unchanged (x (1 - btm share)), so the
            # forced export is exactly the measured total times the measured
            # sector grid-delivery share. Plants missing from the year's
            # 923 vintage keep the p2/artifact floor from above.
            _mtot = chp_measured_netgen.get((plant_code, group))
            if _mtot is not None and nameplate > 0.0:
                pmin_cf = min(100.0, 100.0 * _mtot / (nameplate * HOURS_PER_YEAR))
        elif coal_chp_sector is not None and coal_chp_floor_mw and nameplate > 0.0:
            # Coal cogen: the measured min-month average MW as a % of the coal
            # bin nameplate, scaled and capped the same way derive_thermal_tranches
            # sizes a CEMS-invisible cogen's EIA-923-CF floor.
            pmin_cf = min(
                _COAL_CHP_FLOOR_CAP_PCT,
                coal_chp_floor_mw / nameplate * 100.0 * _COAL_CHP_FLOOR_FACTOR,
            )
        if pmin_cf is not None:
            grid_mr_cf = max(0.0, pmin_cf * (1.0 - pct_mr / 100.0))
            floor_mw = grid_mr_cf / 100.0 * nameplate
            # The floor is carried by the econ slices, so it can be no
            # larger than the econ band. When the committed tranche leaves
            # too little econ room (CAMPD-grounded committed shares run
            # 45-65% on cogens), shift the shortfall from committed into
            # econ — total grid capacity is unchanged, and the always-on
            # steam base takes priority over how the dispatchable
            # remainder is banded.
            shift = min(max(0.0, floor_mw - econ_cap), committed_cap)
            committed_cap -= shift
            econ_cap += shift
            chp_pmin_mw = min(floor_mw, econ_cap)

        # Economic tranche(s). By default one tranche at econ_hr; the offer
        # curve (or the standalone econ split) replaces it with a rising
        # marginal-cost curve that spans ``econ_low -> econ_high`` only. When
        # ``offer_curve_smoothing_n`` is positive the curve is rendered as an
        # N-slice rising ramp (``_econ_curve_steps``) so the LP fills it
        # gradually as hourly price crosses MC, rather than snapping between two
        # wide flat blocks; when it is zero the curve stays two flat steps
        # (econ-low / econ-high). Every group spans econ-low to econ-high and
        # keeps the duct-firing / scarcity peak as a separate flat tranche
        # above the ramp. The first econ step carries any CHP steam-following
        # floor.
        n_curve = int(getattr(config, "offer_curve_smoothing_n", 0) or 0)
        curve_exp = float(getattr(config, "offer_curve_smoothing_exp", 1.0))
        _mid = getattr(config, "offer_curve_smoothing_mid", None)
        curve_mid = float(_mid) if _mid is not None else None
        if ov is not None:
            # Per-plant sheet: the econ ramp spans econ-low to econ-high; the
            # sheet's peaking band stays a separate tranche below.
            lo_m, pk_m = ov["hr_lo"], ov["hr_hi"]
            curve_pct = ov["pct_lo"] + ov["pct_hi"]
            if n_curve > 0 and curve_pct > 0.0 and pk_m > lo_m:
                econ_steps = _econ_curve_steps(
                    base_hr,
                    lo_m,
                    pk_m,
                    nameplate * curve_pct / 100.0,
                    n_curve,
                    curve_exp,
                    curve_mid,
                )
            else:
                econ_steps = [
                    (
                        "econlo",
                        nameplate * ov["pct_lo"] / 100.0,
                        base_hr * ov["hr_lo"],
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                    (
                        "econhi",
                        nameplate * ov["pct_hi"] / 100.0,
                        base_hr * ov["hr_hi"],
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                ]
        elif offer is not None:
            lo_m = float(offer["econ_low"])
            pk_m = float(offer["econ_high"])
            if n_curve > 0 and econ_cap > 0.0 and pk_m > lo_m:
                econ_steps = _econ_curve_steps(
                    base_hr,
                    lo_m,
                    pk_m,
                    econ_cap,
                    n_curve,
                    curve_exp,
                    curve_mid,
                )
            else:
                share = float(offer["econ_low_share"])
                econ_steps = [
                    ("econlo", econ_cap * share, base_hr * lo_m, 1.0, 0, 0, 0.0),
                    (
                        "econhi",
                        econ_cap * (1.0 - share),
                        base_hr * float(offer["econ_high"]),
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                ]
        elif (split := _econ_split_for_group(group, plant_code, config)) is not None:
            split_frac, lo_mult, hi_mult = split
            if n_curve > 0 and econ_cap > 0.0 and hi_mult > lo_mult:
                econ_steps = _econ_curve_steps(
                    base_hr,
                    lo_mult,
                    hi_mult,
                    econ_cap,
                    n_curve,
                    curve_exp,
                    curve_mid,
                )
            else:
                econ_steps = [
                    (
                        "econlo",
                        econ_cap * split_frac,
                        base_hr * lo_mult,
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                    (
                        "econhi",
                        econ_cap * (1.0 - split_frac),
                        base_hr * hi_mult,
                        1.0,
                        0,
                        0,
                        0.0,
                    ),
                ]
        else:
            econ_steps = [("econ", econ_cap, econ_hr, 1.0, 0, 0, 0.0)]
        # Spread the CHP steam-following grid floor across the econ slices in
        # fill order. Pinning it all on the first slice clips the floor to
        # that slice's capacity in generators_to_fleet_arrays (min_gen <=
        # pmax x availability): with the n=6 smoothing ramp a 185 MW floor
        # (Sweeny) collapsed to one ~57 MW slice, idling the steady steam-host
        # export the floor exists to force.
        chp_floor_by_suffix: dict[str, float] = {}
        _floor_rem = chp_pmin_mw
        for _suffix, _cap, *_rest in econ_steps:
            if _floor_rem <= 0.0:
                break
            _take = min(_floor_rem, _cap)
            chp_floor_by_suffix[_suffix] = _take
            _floor_rem -= _take

        # Stepped tranches: (suffix, capacity, heat rate, VOM multiplier,
        # min-run, min-down, start cost). Only the Committed tranche is
        # screened and carries the start cost; Must-Run, Economic and Peaking
        # are incremental output of an already-running plant. No tranche
        # carries a Pmin floor — the Must-Run tranche is forced on by bidding
        # at VOM only (fuel_fracs in the runner).
        # Peak-band VOM multiplier: the offer curve holds VOM constant across
        # bands (band MC = VOM + (AHR x fuel) x mult); the legacy path keeps
        # the 1.5x peak VOM markup. The peak is always a separate flat tranche
        # that jumps up above the econ-low -> econ-high ramp.
        peak_vom_mult = 1.0 if offer is not None else 1.5
        # Committed band: a single flat block by default. With
        # ``committed_ramp_spread`` > 0 it is rendered as an n-slice rising
        # ramp spanning committed_mult x (1 +/- spread), so the plant clears
        # its committed capacity progressively as price rises rather than
        # snapping from 0 to the full committed share in one step (the
        # bimodal-dispatch / under-populated mid-CF-band artifact). The mean
        # bid is unchanged, so class volume is ~preserved; only the operating
        # -level distribution smooths. The first slice stays the screened
        # anchor — it carries the min-run / min-down / start cost and (below)
        # the must_run_pct / bin_nameplate tags — so commitment coupling and
        # the BTM add-back are unaffected.
        # Min-run / min-down for the commitment screen: the bin's measured value
        # when present (ERCOT carries 36/16 per-plant), else the physical coal-
        # boiler default for coal on ISOs whose bin sheet has no Min_Run column.
        # Non-coal keeps the bin value (0 when absent → screened on start cost
        # alone, no duration hysteresis). Only the first committed slice carries
        # it (the screened anchor).
        _bm = b["min_run"]
        _bd = b["min_down"]
        bin_min_run = 0 if pd.isna(_bm) else int(_bm)
        bin_min_down = 0 if pd.isna(_bd) else int(_bd)
        if fuel == "coal":
            if bin_min_run <= 0:
                bin_min_run = COAL_BIN_MIN_RUN_HOURS
            if bin_min_down <= 0:
                bin_min_down = COAL_BIN_MIN_DOWN_HOURS
        cr_spread = float(getattr(config, "committed_ramp_spread", 0.0) or 0.0)
        if cr_spread > 0.0 and committed_cap > 0.5 and n_curve > 0 and base_hr > 0.0:
            cmt_mult = committed_hr / base_hr
            cmt_steps = _econ_curve_steps(
                base_hr,
                cmt_mult * (1.0 - cr_spread),
                cmt_mult * (1.0 + cr_spread),
                committed_cap,
                n_curve,
                curve_exp,
                curve_mid,
            )
            committed_tranches = [
                (
                    ("committed" if i == 0 else f"committed{i:02d}"),
                    _cap,
                    _hr,
                    1.0,
                    bin_min_run if i == 0 else 0,
                    bin_min_down if i == 0 else 0,
                    startup if i == 0 else 0.0,
                )
                for i, (_s, _cap, _hr, *_r) in enumerate(cmt_steps)
            ]
        else:
            committed_tranches = [
                (
                    "committed",
                    committed_cap,
                    committed_hr,
                    1.0,
                    bin_min_run,
                    bin_min_down,
                    startup,
                ),
            ]
        # The _sync (synchronization) tranche bids full SRMC (fuel_frac=1.0 in
        # campd_tranche_fuel_frac), so it carries no fuel discount; it shares the
        # min-load heat rate with _mustrun. Only present in step-3a sync mode and
        # only for plants with a spot (non-contracted) share.
        sync_tranches = (
            [("sync", sync_cap, mustrun_hr, 1.0, 0, 0, 0.0)] if sync_cap > 0.5 else []
        )
        # Fast-start tranche pricing (Order 825 analogue,
        # ScenarioConfig.tranche_startup_amortization): the FAST-START-capable
        # tranches carry the same NREL start cost as the committed anchor, so
        # compute_monthly_markup amortizes each tranche's own P0 run lengths
        # into its P1 bid — the fuel-price-invariant commitment-cost component
        # of the real offer stack. Scope follows ISO-NE's fast-start pricing
        # eligibility (start + notification <= ~30 min): simple-cycle CT
        # tranches (a peaker's econ blocks ARE additional quick-start units)
        # and the CC duct-burner/quick-response PEAK band. A big CC's econ
        # blocks are deliberately EXCLUDED — block-loading a committed CC is
        # not a fast start, and its start costs settle as NCPC uplift, not in
        # the LMP (v1 of this lever marked up CC econ slices and inflated the
        # mild-winter bulk price ~$4 the actual does not show). Min-run /
        # min-down stay 0 (bid markup only, no new UC coupling).
        _fsp_on = getattr(config, "tranche_startup_amortization", False)
        _fsp_econ = startup if (_fsp_on and group in ("CT_PEAKER", "CT_CHP")) else 0.0
        _fsp_peak = (
            startup
            if (_fsp_on and group in ("CT_PEAKER", "CT_CHP", "CC_REGULAR", "CC_CHP"))
            else 0.0
        )
        if _fsp_econ > 0.0:
            econ_steps = [
                (sfx, cap_, hr_, vm_, mr_, md_, _fsp_econ)
                for sfx, cap_, hr_, vm_, mr_, md_, _su in econ_steps
            ]
        # v3 measured-run-length basis (tranche_startup_measured_runs): the
        # simple-cycle CT tranches carry the plant's CAMPD-measured median
        # start-to-stop run length (ISO-class fallback under key 0), which
        # compute_monthly_markup uses as the amortization-horizon ceiling —
        # P0 runs may only shorten it. CC peak (duct) bands keep the v2 P0
        # basis: a duct burner's run is not a CEMS start-to-stop block.
        _fsp_measured_h = (
            _fsp_run_lengths.get(plant_code, _fsp_run_lengths.get(0, 0.0))
            if (_fsp_econ > 0.0 and _fsp_run_lengths)
            else 0.0
        )
        # Peak band: one flat tranche at the offer curve's "peak" multiplier by
        # default. When the offer carries a measured ``peak_ladder``
        # (``[[capacity_share, multiplier], ...]``, derive_dam_offer_hrmults
        # --peak-ladder), the band is split into equal-capacity rungs at the
        # capacity-weighted quantiles of the per-resource top-of-curve offer
        # distribution — representing the measured across-resource dispersion
        # (the upper rungs are the real market's always-posted scarcity wall)
        # instead of collapsing it to the class median
        # (docs/FINDING-ercot-priceshape-2026-07.md §4). Suffixes beyond the
        # first are ``peak2..peakN`` — every consumer that scopes by tranche
        # matches the ``peak`` prefix, not the exact suffix.
        # The per-plant tranche sheet (``ov``) wins over the class ladder, as it
        # does for every other band height.
        ladder = (
            offer.get("peak_ladder") if (offer is not None and ov is None) else None
        )
        if ladder:
            peak_tranches = [
                (
                    ("peak" if i == 0 else f"peak{i + 1}"),
                    peak_cap * float(share),
                    base_hr * float(mult),
                    peak_vom_mult,
                    0,
                    0,
                    _fsp_peak,
                )
                for i, (share, mult) in enumerate(ladder)
            ]
        else:
            peak_tranches = [
                ("peak", peak_cap, peak_hr, peak_vom_mult, 0, 0, _fsp_peak)
            ]
        tranches = [
            ("mustrun", mustrun_cap, mustrun_hr, 1.0, 0, 0, 0.0),
            *sync_tranches,
            *committed_tranches,
            *econ_steps,
            *peak_tranches,
        ]
        for suffix, cap, tr_hr, vom_mult, min_run, min_down, tr_startup in tranches:
            if cap <= 0.5:
                continue
            # Step-3a synchronization forcing: the _mustrun (contracted, fuel-
            # free) and _sync (spot, SRMC) coal min-load tranches are held on at
            # their full capacity via min_gen, so the unit stays synchronized at
            # the measured online Pmin. Other tranches (and non-sync runs) keep
            # the Pmin=0 economic behaviour.
            sync_floor = cap if (coal_sync and suffix in ("mustrun", "sync")) else 0.0
            fleet.append(
                Generator(
                    unit_id=f"{bin_id}_{suffix}",
                    name=f"{plant_name} {suffix}",
                    zone=zone,
                    fuel_type=fuel,
                    efficiency_bin=group,
                    pmax_mw=cap,
                    pmin_mw=0.0,
                    heat_rate=tr_hr,
                    vom=get_vom(fuel) * vom_mult,
                    # R2/EM-4: book CO2 at the plant's PHYSICAL heat rate
                    # (``base_hr``), never the bid-tranche heat rate ``tr_hr``.
                    # ``tr_hr`` carries the offer-curve pricing multipliers
                    # (peak ×2.0-2.5, committed ×0.92 — docs/binning-methodology.md
                    # §pricing) that shape the bid stack; a plant's CO2/MWh does
                    # not change because a block is offered at a scarcity price.
                    # CEMS-covered plants get their measured rate later via
                    # apply_plant_emission_rates; this base_hr value is the
                    # physical default for uncovered plants and entrants.
                    emission_rate_co2=get_emission_rate(fuel, base_hr),
                    nox_rate=get_nox_rate(fuel),
                    eford=get_eford(fuel),
                    online_year=commission_year,
                    is_campd_bin=True,
                    plant_group=group,
                    bin_label=label,
                    min_run_hours=min_run,
                    min_down_hours=min_down,
                    startup_cost_per_mw=tr_startup,
                    must_run_pct=pct_mr if suffix == "committed" else 0.0,
                    bin_nameplate_mw=(nameplate if suffix == "committed" else 0.0),
                    coal_supply=coal_supply,
                    plant_code=plant_code,
                    chp_grid_pmin_mw=chp_floor_by_suffix.get(suffix, 0.0),
                    coal_sync_pmin_mw=sync_floor,
                    coal_sync_online_frac=(
                        sync_online_frac if sync_floor > 0.0 else 1.0
                    ),
                    # Measured amortization horizon only on the fast-start CT
                    # tranches that carry the fsp startup cost (econ + peak of
                    # CT groups); the committed anchor keeps the P0 basis.
                    fast_start_run_hours=(
                        _fsp_measured_h
                        if (tr_startup > 0.0 and suffix.startswith(("econ", "peak")))
                        else 0.0
                    ),
                )
            )

    # v2 measured plant CO2/NOx/SO2 rates on the CAMPD-bins path (G-39 §9.6
    # backcast-reachability fix, 2026-07-06): `apply_plant_emission_rates_v2`
    # was previously called only from `build_dispatch_fleet` (the forecast/
    # runner path), so `use_plant_emission_rates_v2=True` in a backcast
    # run_config was silently unreachable for every CAMPD-binned ISO — proven
    # byte-identical by the nyiso-53 v2-on/off twin pair before this call was
    # added (the same production-wiring-gap class as gap-register G-29).
    # Applying here — before the array conversion, on the same (plant_code,
    # coarse fuel class) match the dispatch-fleet path uses — makes the flag's
    # recorded state true on both paths. Default off: byte-identical unless a
    # config explicitly opts in.
    if getattr(config, "use_plant_emission_rates_v2", False):
        apply_plant_emission_rates_v2(
            fleet,
            config.plant_emission_rates_v2_path,
            iso=config.iso,
            year=int(config.weather_year),
            mode=str(getattr(config, "mode", "forecast")),
            config=config,
        )

    fleet_arrays = generators_to_fleet_arrays(
        fleet,
        zone_names,
        hours=config.hours,
        iso=config.iso,
        config=config,
        year=config.weather_year,
    )
    return fleet, fleet_arrays


def load_or_synthesize_bins(
    config: ScenarioConfig,
    iso: str,
    iso_config: ISOConfig,
    retired_within_window: list[Generator],
) -> pd.DataFrame | None:
    """Resolve the per-plant bin frame driving the offer-curve fleet path.

    ERCOT reads its curated per-plant bin sheet (``config.campd_bins_path``)
    directly via :func:`load_campd_bins`. Every other ISO in
    :data:`~market_sim.config.constants.CAMPD_BINNING_ISOS` synthesizes the
    same per-plant bin schema from its EIA-860 fleet plus the CAMPD-derived
    thermal-tranche artifact via :func:`fleet_to_bins`. Returns ``None`` --
    the signal to fall back to the legacy :func:`aggregate_fleet` path --
    when ``use_campd_bins`` is off, the ISO has no CAMPD artifact, the
    curated CSV is missing, or the synthesis yields no thermal bins.
    """
    if not (config.use_campd_bins and iso in CAMPD_BINNING_ISOS):
        return None
    if iso == "ERCOT":
        if not Path(config.campd_bins_path).exists():
            logger.info(
                "%s: use_campd_bins=True but %s does not exist; falling back "
                "to the legacy aggregate_fleet path",
                iso,
                config.campd_bins_path,
            )
            return None
        return load_campd_bins(
            config.campd_bins_path,
            year=START_YEAR,
            capacity_reconcile_path=(
                config.cc_capacity_reconcile_path
                if config.cc_capacity_reconcile
                else None
            ),
        )
    bins = fleet_to_bins(
        load_fleet_from_csv(iso, iso_config) + retired_within_window,
        iso,
        config,
    )
    if bins.empty:
        logger.info(
            "%s: use_campd_bins=True but fleet_to_bins synthesized no "
            "thermal bins (no CAMPD-derived thermal_tranches artifact); "
            "falling back to the legacy aggregate_fleet path",
            iso,
        )
        return None
    return bins


def build_base_fleet(
    campd_bins: pd.DataFrame | None,
    iso: str,
    iso_config: ISOConfig,
    zone_names: list[str],
    config: ScenarioConfig,
    retired_within_window: list[Generator],
    planned_additions: list[Generator],
    year: int,
    confirmed_exits: list | None = None,
    *,
    vintage_year: int | None = None,
    nonthermal_exclude: frozenset[str] | None = None,
    legacy_n_bins: int | None = None,
) -> list[Generator]:
    """Build the first simulated year's persistent generation fleet.

    Takes the per-plant bin choice already resolved by
    :func:`load_or_synthesize_bins`: per-plant tranche generators
    (:func:`bins_to_fleet`) when bins were found, else the legacy
    equal-width heat-rate-bin aggregation (:func:`aggregate_fleet`). Either
    way the collapse happens once, here, before the per-year dispatch loop.
    Planned EIA-860 additions already due by ``year`` are appended; later
    years instead evolve this fleet via
    :func:`~market_sim.model.capacity.evolve_fleet`.

    Confirmed (binding-instrument) exits already effective by ``year`` are
    applied last (:func:`~market_sim.model.capacity.apply_confirmed_exits`,
    ``apply_backlog=True``), so a unit confirmed to close in the first
    simulated year is not mis-carried for a full year — the "a 2026 exit can
    never happen in 2026" hole the economic screen (which needs prior-year
    dispatch) cannot close. ``apply_backlog=True`` collapses every exit with
    ``effective_year <= year`` (the pre-start backlog) into a single
    application here; :func:`~market_sim.model.capacity.evolve_fleet` then
    only ever selects a row newly effective in its own year, so no row is
    ever applied twice. GATED on ``config.confirmed_exits_enabled``; a no-op
    when off or ``confirmed_exits`` is empty.

    Backcast parameterization (orchestrator-unification Stage 6 -- the
    backcast rebuilds this base fleet every solved year instead of evolving
    a persistent one):

    - ``vintage_year``: EIA-860 vintage passed to
      :func:`load_fleet_from_csv` (the backcast's year-matched snapshot);
      ``None`` keeps the runner's default vintage resolution.
    - ``nonthermal_exclude``: the fuel set removed from the raw EIA-860
      units on the ERCOT curated-bins branch; ``None`` uses
      :data:`_AGGREGATABLE_FUELS`. The backcast passes a set WITHOUT
      ``oil`` (its ERCOT oil units stay raw LP scarcity peakers, while the
      forecast path drops them) -- a pre-existing divergence preserved
      through the migration, not a new choice; reconciling it is an open
      root-cause item (CLAUDE.md #14), not a refactor decision.
    - ``legacy_n_bins``: heat-rate bin count on the no-bins fallback path;
      ``None`` reads ``config.heat_rate_bin_count``. The backcast passes 0
      (per-plant, identity-preserving) when ``plant_level_fleet`` is set.
    """
    if campd_bins is not None:
        campd_fleet, _ = bins_to_fleet(campd_bins, zone_names, config)
        all_gens = (
            load_fleet_from_csv(iso, iso_config, year=vintage_year)
            + retired_within_window
        )
        if iso == "ERCOT":
            # ERCOT's curated sheet covers the full gas/coal thermal fleet;
            # nuclear (and any other non-aggregatable unit) still comes from
            # EIA-860 so it stays in the dispatch LP.
            _exclude = (
                _AGGREGATABLE_FUELS
                if nonthermal_exclude is None
                else nonthermal_exclude
            )
            non_thermal = [g for g in all_gens if g.fuel_type not in _exclude]
        else:
            # The synthesized bins cover exactly the thermal (plant_code,
            # plant_group) pairs in ``campd_bins``; every other unit
            # (nuclear, oil, biomass, and any thermal plant the synthesis
            # didn't bin) stays a raw LP unit. Filtering on the exact binned
            # set -- rather than a fuel allow-list -- avoids dropping or
            # double-counting any plant (the bin groups include gas_st,
            # which is not an aggregatable fuel).
            binned = set(
                zip(
                    campd_bins["Plant_Code"].astype(int),
                    campd_bins["Plant_Group"],
                )
            )
            non_thermal = [
                g for g in all_gens if (int(g.plant_code), g.plant_group) not in binned
            ]
        fleet = non_thermal + campd_fleet
    else:
        fleet = aggregate_fleet(
            load_fleet_from_csv(iso, iso_config, year=vintage_year)
            + retired_within_window,
            n_bins=(
                config.heat_rate_bin_count if legacy_n_bins is None else legacy_n_bins
            ),
        )
    # Planned units already due by the first simulated year (their EIA-860
    # effective year falls after the operable snapshot but at or before
    # ``year``) join the base fleet now; evolve_fleet only runs from the
    # second year on.
    due = [g for g in planned_additions if g.online_year <= year]
    if due:
        logger.info(
            "year %d: %d planned additions already due (%.0f MW)",
            year,
            len(due),
            sum(g.pmax_mw for g in due),
        )
        fleet = fleet + due

    # Confirmed exits already effective by the first simulated year (their
    # instrument date is at or before ``year``): a unit confirmed to close now is
    # excluded up front, since the economic screen (needing prior-year dispatch)
    # cannot retire it in the first year. Local import avoids the fleet<->capacity
    # import cycle; a no-op unless the confirmed channel is enabled.
    if getattr(config, "confirmed_exits_enabled", False) and confirmed_exits:
        from market_sim.model.capacity import apply_confirmed_exits

        before = len(fleet)
        fleet = apply_confirmed_exits(fleet, year, confirmed_exits, apply_backlog=True)
        if len(fleet) != before:
            logger.info(
                "year %d: confirmed exits removed/derated %d base-fleet unit(s)",
                year,
                before - len(fleet),
            )
    return fleet


def _drop_biomass_units(
    fleet: list[Generator], fuel_fracs: list
) -> tuple[list[Generator], list]:
    """Remove biomass LP units (and their parallel fuel fractions) from a fleet.

    Used when biomass is injected as a measured EIA-923 must-run profile (the
    caller nets it out of demand and re-adds it as a fixed pseudo-unit), so the
    raw biomass generators must not also clear the merit order -- else biomass
    is served twice. Returns the filtered ``(fleet, fuel_fracs)`` pair (order-
    and length-preserving). A no-op for a fleet with no biomass units (e.g.
    ERCOT, whose CAMPD path already excludes them). Moved verbatim from
    ``scripts/run_calibration.py`` (orchestrator-unification Stage 6).
    """
    kept = [(g, ff) for g, ff in zip(fleet, fuel_fracs) if g.fuel_type != "biomass"]
    return [g for g, _ in kept], [ff for _, ff in kept]


def build_dispatch_fleet(
    fleet: list[Generator],
    campd_bins: pd.DataFrame | None,
    import_generators: list[Generator],
    iso: str,
    year: int,
    zone_names: list[str],
    config: ScenarioConfig,
    *,
    hydro_backfill_year: int | None = None,
    hydro_eia930_monthly: bool = False,
    hydro_forecast_budget: bool = True,
    hydro_year: str | None = None,
    drop_biomass_units: bool = False,
    imports_after_hydro: bool = False,
    apply_emission_overrides: bool = True,
) -> tuple[list[Generator], list[float], np.ndarray | None, np.ndarray | None]:
    """Assemble this year's LP-ready dispatch fleet from the persistent fleet.

    Splits coal (and optionally gas) into take-or-pay / SRMC tranches --
    CAMPD per-plant fuel fractions (:func:`campd_tranche_fuel_frac`) when
    ``campd_bins`` is active, else the legacy :func:`split_coal_tranches` /
    :func:`split_gas_tranches` -- then appends energy-limited hydro plants
    and overrides plant-specific CAMPD emission rates. Both branches start
    from the same ``fleet`` and end at the same shape: a list of
    :class:`Generator` ready for :func:`generators_to_fleet_arrays`.

    THE shared per-year fleet-assembly body for both orchestrators
    (orchestrator-unification Stage 6): the forecast runner calls it with the
    keyword defaults; the backcast orchestrator passes its measured hydro
    budgets, biomass-injection drop, import placement, and the emission-
    override seam explicitly. The coal-passthrough machinery (per-supply
    gas-keyed sigmoids, tiered PRB follower) is resolved here from ``config``
    for both callers, so a supply curve a config enables is reachable from
    either path -- flat full-cost passthrough at the field defaults.

    Args:
        hydro_backfill_year / hydro_eia930_monthly / hydro_forecast_budget:
            threaded to :func:`market_sim.data.hydro.build_hydro_fleet`. The
            defaults (no backfill, climatology forecast budget) reproduce the
            runner's historical call; a backcast passes its measured
            monthly-budget switches.
        hydro_year: water-year selector; ``None`` reads ``config.hydro_year``.
        drop_biomass_units: drop raw biomass LP units (and their parallel
            fuel fractions) after the tranche split -- set by the backcast
            when biomass is injected as a measured must-run profile
            (``inject_biomass_mustrun``) so biomass is never served twice.
        imports_after_hydro: append ``import_generators`` after the hydro
            block (the backcast's historical LP column order) instead of
            merging them into the tranche split (the runner's). Both orders
            price imports identically (fuel fraction 1.0 either way); the
            switch exists purely to preserve each orchestrator's established
            column order across the Stage-6 migration (golden byte-identity,
            output-frame stability), not because the orders differ
            economically.
        apply_emission_overrides: run the plant-specific CAMPD emission-rate
            override block (v2 mode-aware artifact, else the v1 parquet when
            ``config.use_plant_emission_rates``). The backcast passes False:
            its per-plant rates enter via the bin artifacts and the v2 hook
            inside :func:`bins_to_fleet` (G-39 §9.6), and it has never
            applied the v1 overwrite -- folding v1 in would move keeper
            emission costs (an open reconciliation item, not a refactor
            decision).

    Returns:
        ``(dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy)``.
        ``hydro_gen_idx`` / ``hydro_monthly_energy`` are ``None`` when the
        ISO has no hydro plants.
    """
    # Local import: data.fuel imports from data.fleet at module level, so the
    # passthrough helpers must be imported lazily here (same pattern as the
    # hydro builder below).
    from market_sim.data.fuel import (
        coal_passthrough_by_supply,
        prb_follower_passthrough_series,
    )

    inline_imports = [] if imports_after_hydro else import_generators
    if campd_bins is not None:
        dispatch_fleet = fleet + inline_imports
        # Must-run tranches bid at VOM + carbon + NOx only -- the fuel is
        # sunk under take-or-pay coal contracts, CHP host steam obligations
        # or ERCOT RUC. In step-3a sync mode the contract share is consumed
        # in bins_to_fleet to SIZE the fuel-free _mustrun band vs the SRMC
        # _sync band, so it must NOT be re-applied here (that would
        # double-discount).
        takeorpay = None
        if getattr(config, "coal_takeorpay_from_data", False) and not getattr(
            config, "coal_sync_srmc_tranche", False
        ):
            takeorpay = {
                int(g.plant_code): coal_takeorpay_share(int(g.plant_code))
                for g in dispatch_fleet
                if g.fuel_type == "coal"
                and coal_takeorpay_share(int(g.plant_code)) is not None
            }
        # Above must-run, each coal tranche passes its own supply chain's
        # passthrough -- flat scalar, or a (T,) gas-keyed sigmoid resolved
        # per (ISO, supply) -- so baseloaded coal clears the merit order
        # instead of being priced out by cheap gas. At the field defaults
        # (all sigmoid toggles off, coal_prb_passthrough = 1.0) every supply
        # passes full fuel cost, value-identical to the pre-Stage-6 inline
        # {"prb": p, "subbituminous": p} dict this replaces (a missing tag
        # and a 1.0 tag both mean full cost). The one semantic tightening:
        # with sigmoids off, a non-default coal_prb_passthrough now discounts
        # only prb-tagged coal (subbituminous keeps full cost unless its own
        # curve is enabled) -- the backcast's calibrated per-supply routing,
        # which no forecast config relied on (nothing in src/ sets the field).
        pt_by_supply = coal_passthrough_by_supply(config, year, config.hours)
        if config.coal_prb_passthrough_sigmoid and config.coal_prb_passthrough_tiered:
            # Tiered PRB: low-must-run "prb" load-followers swap the baseload
            # prb curve for the follower-tier one. The tier split is specific
            # to the curated ERCOT prb supply; ISOs without a characterized
            # follower curve fall back to the baseload prb series
            # (value-identical routing).
            foll = {
                **pt_by_supply,
                "prb": prb_follower_passthrough_series(config, year, config.hours),
            }
            thr = config.coal_prb_follower_mustrun_max

            def _pt_for(g: Generator):
                if (
                    g.fuel_type == "coal"
                    and getattr(g, "coal_supply", "") == "prb"
                    and COAL_MUSTRUN_BY_PLANT.get(g.plant_code, 100.0) <= thr
                ):
                    return foll
                return pt_by_supply

        else:

            def _pt_for(g: Generator):
                return pt_by_supply

        fuel_fracs = [
            campd_tranche_fuel_frac(
                g,
                _pt_for(g),
                takeorpay,
                econ_srmc_bound=getattr(config, "coal_econ_srmc_bound", False),
            )
            for g in dispatch_fleet
        ]
    else:
        # Non-CAMPD-binned ISOs split coal into take-or-pay tranches here.
        # With coal_takeorpay_from_data the sunk first tranche uses each
        # plant's MEASURED EIA-923 Schedule-5 contracted share (CLAUDE.md
        # #11/#12) instead of the uniform 100%-sunk assumption.
        split_takeorpay = None
        if getattr(config, "coal_takeorpay_from_data", False):
            split_takeorpay = {
                int(g.plant_code): coal_takeorpay_share(int(g.plant_code))
                for g in fleet
                if g.fuel_type == "coal"
                and coal_takeorpay_share(int(g.plant_code)) is not None
            }
        dispatch_fleet, fuel_fracs = split_coal_tranches(
            fleet + inline_imports, config, split_takeorpay
        )
        if getattr(config, "gas_offer_curve", False):
            dispatch_fleet, fuel_fracs = split_gas_tranches(
                dispatch_fleet, fuel_fracs, config
            )

    # Biomass injected as a measured EIA-923 must-run profile (the caller nets
    # it out of demand and re-adds it as a fixed pseudo-unit), so drop the raw
    # biomass LP units to avoid double-serving -- and to make biomass output
    # the fuel/contract-limited, price-insensitive quantity it is in reality
    # instead of a dispatchable unit the LP runs to max when gas rises.
    # Backcast-only today (inject_biomass_mustrun); default off, so callers
    # that do NOT inject biomass keep it as an LP unit and never lose it.
    if drop_biomass_units:
        dispatch_fleet, fuel_fracs = _drop_biomass_units(dispatch_fleet, fuel_fracs)

    # Energy-limited conventional hydro (every ISO with hydro plants): one LP
    # unit per EIA-923-reporting hydro plant, capped per hour by its EIA-860
    # nameplate and per month by its energy budget via the dispatch LP's
    # hydro budget rows. Appended after the coal/gas split so it flows
    # through assemble_mc and the dispatch like any other generator.
    from market_sim.data.hydro import build_hydro_fleet

    hydro_units, hydro_monthly_energy = build_hydro_fleet(
        iso,
        year,
        zone_names,
        backfill_year=hydro_backfill_year,
        eia930_monthly=hydro_eia930_monthly,
        forecast_budget=hydro_forecast_budget,
        hydro_year=config.hydro_year if hydro_year is None else hydro_year,
    )
    hydro_gen_idx = None
    if hydro_units:
        hydro_gen_idx = np.arange(
            len(dispatch_fleet),
            len(dispatch_fleet) + len(hydro_units),
            dtype=int,
        )
        dispatch_fleet = dispatch_fleet + hydro_units
        fuel_fracs = list(fuel_fracs) + [1.0] * len(hydro_units)
        logger.info(
            "%s %d: %d hydro plants in LP (%.0f MW, %.2f TWh monthly budget)",
            iso,
            year,
            len(hydro_units),
            sum(g.pmax_mw for g in hydro_units),
            hydro_monthly_energy.sum() / 1e6,
        )

    # Backcast import placement: the priced import/export node's tranches join
    # the LP after hydro (the backcast's historical column order -- see the
    # imports_after_hydro docstring note).
    if imports_after_hydro and import_generators:
        dispatch_fleet = dispatch_fleet + import_generators
        fuel_fracs = list(fuel_fracs) + [1.0] * len(import_generators)
        logger.info(
            "%s %d: priced import/export node — %d import tranches "
            "(%.0f MW), %d export sinks (%.0f MW)",
            iso,
            year,
            sum(1 for g in import_generators if g.pmax_mw > 0),
            sum(g.pmax_mw for g in import_generators),
            sum(1 for g in import_generators if g.pmin_mw < 0),
            -sum(g.pmin_mw for g in import_generators),
        )

    # Override fuel-class CO2/NOx/SO2 rates with CAMPD plant-specific ones
    # for generators pinned to a single plant, so emission prices bite at
    # each plant's measured per-MWh-net intensity. Gated off by the backcast
    # (see the apply_emission_overrides docstring note).
    if apply_emission_overrides:
        if getattr(config, "use_plant_emission_rates_v2", False):
            # Mode-aware v2 source: backcast books the target year's measured
            # rate, forecast the estimator base; composition mask splits
            # Parish coal/gas.
            apply_plant_emission_rates_v2(
                dispatch_fleet,
                config.plant_emission_rates_v2_path,
                iso=iso,
                year=int(year),
                mode=str(getattr(config, "mode", "forecast")),
                config=config,
            )
        elif config.use_plant_emission_rates:
            apply_plant_emission_rates(dispatch_fleet, config.plant_emission_rates_path)

    return dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy
