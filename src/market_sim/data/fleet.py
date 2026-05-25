"""Generation fleet inventory and attributes.

Provides the :class:`Generator` model, its vectorized :class:`FleetArrays`
form, and loaders that build a per-ISO thermal fleet from EIA-860 / eGRID
CSV extracts.
"""

from __future__ import annotations

import calendar
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel

from market_sim.config.constants import (
    CO2_RATES,
    EFORD,
    FUEL_CO2_FACTOR_PER_MMBTU,
    HEAT_RATE_BINS,
    NOX_RATES,
    NUCLEAR_MONTHLY_CF,
    NUCLEAR_MONTHLY_CF_BY_YEAR,
    THERMAL_AVAILABILITY,
    VOM,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.outages import (
    QUALIFYING_PLANT_GROUPS,
    ST_GAS_PEAKER_PLANTS,
    outage_masks_for_year,
    partial_outage_derate_factors,
    unit_outage_derate_factors,
)

logger = logging.getLogger(__name__)

# Location of the EIA-860 / eGRID CSV extracts, resolved relative to the
# repository root (this file lives at src/market_sim/data/fleet.py).
EIA_860_DIR: Path = Path(__file__).parents[3] / "inputs" / "raw-data" / "eia-860"

# Committed parquet of real EIA-860 generators for the seven wholesale
# markets, produced by ``scripts/process_eia860.py`` from the raw release.
EIA_860_PARQUET_NAME: str = "eia860_generators.parquet"

# Directory for derived, inspectable fleet outputs (the binned-fleet cache).
PROCESSED_DIR: Path = Path(__file__).parents[3] / "inputs" / "processed"

# Columns of the cached plant-level binned-fleet parquet, one row per
# physical generator with its loader-assigned efficiency bin and attributes.
BINNED_FLEET_COLUMNS: list[str] = [
    "plant_id", "plant_name", "fuel_type", "efficiency_bin", "zone",
    "pmax_mw", "pmin_mw", "heat_rate", "vom", "emission_rate_co2",
    "nox_rate", "eford", "online_year", "retirement_year",
]

# Canonical column order of the EIA-860 generator extract consumed by the
# fleet loader, produced by ``scripts/process_eia860.py``.
EIA_860_CSV_COLUMNS: list[str] = [
    "plant_id", "generator_id", "plant_name", "state",
    "balancing_authority_code", "technology", "energy_source", "prime_mover",
    "nameplate_capacity_mw", "net_summer_capacity_mw", "operating_year",
    "planned_retirement_year", "status", "heat_rate",
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
    "SWPP": "SPP",
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
    "hydrogen_ct": 8,     # simple-cycle H2 turbine (peaker)
    "hydrogen_ccgt": 9,   # combined-cycle H2 turbine (mid-merit/baseload)
    "gas_cc_ccs": 10,     # gas CCGT with 90% post-combustion carbon capture
    "oil": 11,            # oil-fired peaker/steam (distillate + residual fuel oil)
    "geothermal": 12,     # enhanced geothermal systems (EGS)
    "offshore_wind": 13,  # offshore wind (fixed-bottom and floating)
    "gas_st": 14,         # legacy natural-gas steam boiler (conventional ST)
    "biomass": 15,        # biomass / wood / MSW / landfill-gas thermal steam
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
    is_must_run: bool = False

    # CAMPD operational-bin attributes. Set only for generators built by
    # :func:`bins_to_fleet`; left at defaults for the legacy fleet. These
    # carry the per-bin commitment parameters and must-run accounting that
    # used to live in lookup-table constants.
    is_campd_bin: bool = False
    plant_group: str = ""           # CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS, ST_CHP
    bin_label: str = ""             # human-readable bin id, e.g. H_CC1
    min_run_hours: int = 0          # minimum committed run length
    min_down_hours: int = 0         # minimum downtime between runs
    startup_cost_per_mw: float = 0.0  # $/MW per start, for the bid markup
    must_run_pct: float = 0.0       # MR% of the bin's nameplate (CHP steam)
    bin_nameplate_mw: float = 0.0   # bin total nameplate, for MR reconstruction
    coal_supply: str = ""           # "lignite" (mine-mouth) or "prb" (rail);
    #                                 drives plant-specific coal fuel pricing
    plant_code: int = 0             # EIA plant code, when the tranche maps
    #                                 to a single physical plant; drives the
    #                                 F923 monthly fuel-cost lookup.
    chp_grid_pmin_mw: float = 0.0   # grid-delivered steam-following floor (MW)
    #                                 forced on flat via FleetArrays.min_gen for
    #                                 CC_CHP cogens (config.chp_steam_following).


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

# Months (1-based) over which the legacy gas-steam (ST_GAS) reliability
# must-run floor and its seasonal startup-cost amortization apply: May through
# September, ERCOT's high-load season when these old units are dragged online.
_GAS_ST_SUMMER_MONTHS: frozenset[int] = frozenset({5, 6, 7, 8, 9})

# Fraction of a unit's WEFOR (forced-outage rate) that applies during the
# summer peak; the remaining (1 - share) is redistributed into the shoulder
# months. Winter keeps the flat WEFOR.
_SUMMER_WEFOR_SHARE: float = 0.30

# Additional summer (Jun-Sep) capacity derate by plant group, modeling the
# ambient-temperature output loss gas turbines suffer in the heat (worse for
# simple-cycle CTs than combined-cycle). Applied on top of the age-based
# availability for these classes only; coal and gas steam are unaffected.
_SUMMER_CLASS_DERATE: dict[str, float] = {
    "CC_REGULAR": 0.10, "CC_CHP": 0.10,
    "CT_PEAKER": 0.125, "CT_CHP": 0.125,
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

# Per-plant coal maximum capacity-factor ceilings (fraction of capacity_mw):
# the sustained output each unit cannot exceed even running hard (derates,
# heat-rate / boiler limits), capping the dispatch so coal does not over-run.
# Applied as an availability ceiling year-round.
COAL_MAX_CF_BY_PLANT: dict[int, float] = {
    6180: 0.90,  # Oak Grove
    298:  0.80,  # Limestone
    6178: 0.99,  # Coleto Creek
    6183: 0.90,  # San Miguel
    6179: 0.89,  # Fayette (Sam Seymour)
    7097: 0.80,  # J K Spruce
}
# Year-specific ceiling overrides (e.g. confirmed unit-outage years).
COAL_MAX_CF_OVERRIDE: dict[tuple[int, int], float] = {
    (6179, 2025): 0.78,  # Fayette unit issues held it to ~78% in 2025
}
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
    pof, w_base, w_rate, w_onset, d_base, d_rate, d_onset = (
        THERMAL_AVAILABILITY[category]
    )
    wefor = w_base + max(0.0, age - w_onset) * w_rate
    derate = d_base + max(0.0, age - d_onset) * d_rate
    return pof, wefor, derate


def generators_to_fleet_arrays(
    generators: list[Generator],
    zone_names: list[str],
    hours: int = 8760,
    iso: str | None = None,
    config: ScenarioConfig | None = None,
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
    availability = np.broadcast_to(
        (1.0 - eford)[:, np.newaxis], (n_gen, hours)
    ).copy()

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
    if config is not None and shoulder_hours > 0:
        run_year = config.weather_year
        summer_to_shoulder = summer_hours / shoulder_hours
        drop_coal_pof = getattr(config, "coal_drop_pof", False)
        for g_idx, gen in enumerate(generators):
            if gen.plant_group not in THERMAL_AVAILABILITY:
                continue
            pof, wefor, derate = _thermal_outage(
                gen.plant_group, run_year - gen.online_year
            )
            # Lighten (or raise) the forced-outage magnitude while keeping the
            # seasonal shape — applied before the summer/shoulder/winter split.
            wefor *= config.wefor_multiplier
            if drop_coal_pof and gen.fuel_type == "coal":
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
                    wefor
                    + (1.0 - _SUMMER_WEFOR_SHARE) * wefor * summer_to_shoulder
                )
                # Drop the shoulder POF for the historic-overlay classes (CC /
                # ST + their CHP) so it does not double-count the actual planned
                # outages from the overlay + unit derate; CTs keep POF.
                pof_eff = (
                    0.0 if drop_coal_pof and gen.plant_group in _POF_DROP_GROUPS
                    else pof
                )
                # Default (winter): flat WEFOR, no POF. Then override summer
                # and shoulder.
                availability[g_idx, :] = 1.0 - wefor - derate
                availability[g_idx, summer] = 1.0 - summer_wefor - derate
                availability[g_idx, shoulder] = (
                    1.0 - shoulder_wefor - derate - pof_eff
                )
            # Per-bin forced derates for confirmed unit losses (e.g. a
            # multi-unit plant losing one boiler to a fire). Applied as a
            # flat multiplier on top of the age-based availability.
            forced = BIN_FORCED_DERATE_BY_YEAR.get(gen.bin_label, {}).get(
                run_year
            )
            if forced is not None:
                availability[g_idx, :] *= forced
            # Summer ambient-temperature derate for CC / CT classes.
            summer_derate = _SUMMER_CLASS_DERATE.get(gen.plant_group)
            if summer_derate:
                availability[g_idx, summer] *= 1.0 - summer_derate
            # Per-plant coal max-CF ceilings: cap availability so the unit
            # cannot dispatch above its sustained operating limit.
            if gen.plant_group == "COAL":
                _pc = int(gen.plant_code)
                cap = COAL_MAX_CF_OVERRIDE.get(
                    (_pc, run_year), COAL_MAX_CF_BY_PLANT.get(_pc)
                )
                if cap is not None:
                    np.minimum(availability[g_idx, :], cap,
                               out=availability[g_idx, :])
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
    if config is not None and getattr(
        config, "outage_source", "statistical"
    ) == "historic":
        masks = outage_masks_for_year(
            config.weather_year,
            hours,
            bins_path=getattr(
                config, "campd_bins_path", "inputs/custom-bin-assignments.csv"
            ),
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
                "historic outage overlay (%d): zeroed %d coal/CC bin-tranches "
                "across %d plant(s)",
                config.weather_year, applied, len(masks),
            )
        # Unit-level outage derate (backcast): partial availability cut per
        # unit outage >= 5 days, sized by the unit's share of its model bin
        # capacity (CTs excluded; split plants routed to the right asset
        # class). Multiplies the availability already set above.
        ufac = unit_outage_derate_factors(
            config.weather_year, hours,
            getattr(config, "campd_bins_path",
                    "inputs/custom-bin-assignments.csv"),
        )
        if ufac:
            applied_u = 0
            for g_idx, gen in enumerate(generators):
                f = ufac.get((int(gen.plant_code), gen.plant_group))
                if f is not None:
                    availability[g_idx, :] *= f
                    applied_u += 1
            logger.info(
                "unit-outage derate (%d): %d bin-tranches derated",
                config.weather_year, applied_u,
            )
        # Partial-outage derate (CAMPD CF-ceiling plateaus): approximate
        # half-units-out events for baseload coal + a confirmed CC allowlist
        # where no unit data exists. Multiplies availability over the window.
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
                config.weather_year, applied_p,
            )

    # Seasonal ST_GAS reliability must-run floor: a hard minimum-generation
    # bound on the legacy gas-steam fleet in the summer months, modeling units
    # held online at min load for grid reliability ("reliability dragging").
    # Applied to the base (non-peak) ST_GAS tranches so the peak slice stays
    # economic; capped by availability.
    min_gen = None
    st_mr_frac = (
        getattr(config, "gas_st_summer_mustrun", 0.0) if config is not None
        else 0.0
    )
    st_off_frac = (
        getattr(config, "gas_st_offsummer_mustrun", 0.0) if config is not None
        else 0.0
    )
    chp_pmin_any = any(
        getattr(g, "chp_grid_pmin_mw", 0.0) > 0.0 for g in generators
    )
    if st_mr_frac > 0.0 or st_off_frac > 0.0 or chp_pmin_any:
        min_gen = np.zeros((n_gen, hours), dtype=float)
        if st_mr_frac > 0.0 or st_off_frac > 0.0:
            summer_mask = np.isin(_hour_to_month_index(hours) + 1,
                                  list(_GAS_ST_SUMMER_MONTHS))
            # Reliability (non-peaker) ST_GAS held at the summer / off-summer
            # floor; peaker-class ST_GAS run purely economically (no floor).
            for g_idx, gen in enumerate(generators):
                if (gen.plant_group == "ST_GAS"
                        and not gen.unit_id.endswith("_peak")
                        and gen.plant_code not in ST_GAS_PEAKER_PLANTS):
                    min_gen[g_idx, summer_mask] = st_mr_frac * pmax[g_idx]
                    min_gen[g_idx, ~summer_mask] = st_off_frac * pmax[g_idx]
        # CHP grid-delivered steam-following floor: the cogen's steady export
        # is forced on flat all year (the dispatchable surplus rides above it
        # via the load-following tranches).
        for g_idx, gen in enumerate(generators):
            pmin_mw = getattr(gen, "chp_grid_pmin_mw", 0.0)
            if pmin_mw > 0.0:
                min_gen[g_idx, :] = pmin_mw
        # Never demand more than the (outage/derate-adjusted) availability.
        np.minimum(min_gen, pmax[:, np.newaxis] * availability, out=min_gen)

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
        efficiency_bin=np.array(
            [g.efficiency_bin for g in generators], dtype=str
        ),
        plant_code=np.array(
            [int(g.plant_code) for g in generators], dtype=int
        ),
        min_gen=min_gen,
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
                )
            )
    else:
        for key in sorted(groups):
            fuel_type, zone = key
            for rep in aggregate_fleet_by_efficiency(
                groups[key], fuel_type, n_bins
            ):
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
    and ``nox_price`` may be scalars or ``(T,)`` hourly arrays. Each ``adders``
    keyword value is a ``(generator_rate_array, hourly_price_array)`` pair,
    allowing extra cost terms (e.g. SO2) without changing the signature.
    """
    heat_rate = fleet.heat_rate[:, np.newaxis]
    mc = heat_rate * np.asarray(fuel_prices, dtype=float)
    mc = mc + fleet.vom[:, np.newaxis]
    mc = mc + fleet.emission_rate[:, np.newaxis] * np.asarray(carbon_price, dtype=float)
    mc = mc + fleet.nox_rate[:, np.newaxis] * np.asarray(nox_price, dtype=float)

    for rate_array, price_array in adders.values():
        rate = np.asarray(rate_array, dtype=float)[:, np.newaxis]
        mc = mc + rate * np.asarray(price_array, dtype=float)

    return mc


def _coal_tranches(config: ScenarioConfig) -> list[tuple[float, float]]:
    """Return the coal take-or-pay tranches as ``(cap_frac, fuel_frac)`` pairs.

    Mirrors :data:`~market_sim.config.constants.COAL_TRANCHES`, reading the
    per-tranche capacity fraction and fuel-cost passthrough from the scenario
    config so calibration can override the defaults.
    """
    return [
        (config.coal_tranche_1_frac, config.coal_tranche_1_fuel_passthrough),
        (config.coal_tranche_2_frac, config.coal_tranche_2_fuel_passthrough),
        (config.coal_tranche_3_frac, config.coal_tranche_3_fuel_passthrough),
    ]


def split_coal_tranches(
    generators: list[Generator], config: ScenarioConfig
) -> tuple[list[Generator], list[float]]:
    """Split each coal generator into take-or-pay supply-curve tranches.

    Coal plants hold take-or-pay fuel contracts: the contracted volume bids
    at VOM only (its fuel is sunk) while volume above the contract bids at
    progressively more of full fuel cost. Each coal :class:`Generator` is
    therefore replaced by three sub-generators — one per tranche — that
    together reproduce its capacity but expose a stepped supply curve to the
    dispatch LP. Tranches carry ``pmin_mw = 0``: coal's baseload behavior
    emerges from tranche 1's near-zero (VOM-only) bid, not a hard minimum.

    Non-coal generators pass through unchanged.

    Args:
        generators: The fleet to expand.
        config: Scenario configuration supplying the ``coal_tranche_*`` fields.

    Returns:
        A tuple ``(expanded_fleet, fuel_fracs)`` where ``fuel_fracs[g]`` is the
        fraction of fuel cost passed through to generator ``g``'s marginal
        cost. Non-coal generators have ``fuel_frac = 1.0``.
    """
    tranches = _coal_tranches(config)
    expanded: list[Generator] = []
    fuel_fracs: list[float] = []
    for gen in generators:
        if gen.fuel_type != "coal":
            expanded.append(gen)
            fuel_fracs.append(1.0)
            continue
        for ti, (cap_frac, fuel_frac) in enumerate(tranches):
            expanded.append(
                Generator(
                    unit_id=f"{gen.unit_id}_t{ti + 1}",
                    name=gen.name,
                    zone=gen.zone,
                    fuel_type="coal",
                    efficiency_bin=gen.efficiency_bin,
                    pmax_mw=gen.pmax_mw * cap_frac,
                    pmin_mw=0.0,
                    heat_rate=gen.heat_rate,
                    vom=gen.vom,
                    emission_rate_co2=gen.emission_rate_co2,
                    nox_rate=gen.nox_rate,
                    so2_rate=gen.so2_rate,
                    eford=gen.eford,
                    online_year=gen.online_year,
                    retirement_year=gen.retirement_year,
                    plant_code=gen.plant_code,
                )
            )
            fuel_fracs.append(fuel_frac)
    return expanded, fuel_fracs


def campd_tranche_fuel_frac(
    gen: Generator, coal_prb_passthrough: "float | np.ndarray" = 1.0
) -> "float | np.ndarray":
    """Return the fuel-cost passthrough for one CAMPD tranche generator.

    ``coal_prb_passthrough`` may be a scalar (flat) or an ``(T,)`` array (the
    gas-keyed sigmoid); whichever is given is returned for PRB above-must-run
    tranches and applied by :func:`apply_coal_tranches`.

    Must-run tranches (any fuel) pass ``0.0`` — their fuel is sunk under
    take-or-pay coal contracts, CHP host-steam obligations or ERCOT RUC, so
    they bid VOM + carbon + NOx only. Every PRB coal tranche *above* must-run
    (committed, economic and peaking) passes ``coal_prb_passthrough`` < 1.0
    to price-take: an already-online PRB unit (rail take-or-pay) bids to
    clear rather than on full marginal cost. Mine-mouth lignite and all
    other tranches pass full fuel cost (``1.0``).
    """
    if gen.unit_id.endswith("_mustrun"):
        return 0.0
    if gen.fuel_type == "coal" and getattr(gen, "coal_supply", "") == "prb":
        return coal_prb_passthrough
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
        "plant_id", "plantid", "plant_code", "plantcode", "oris", "orispl",
        "plant_id_eia", "plantid_eia",
    },
    "generator_id": {
        "generator_id", "generatorid", "gen_id", "genid", "unit_id", "unitid",
    },
    "plant_name": {"plant_name", "plantname", "pname", "name"},
    "state": {"state", "plant_state", "plantstate", "pstatabb", "plstatabb"},
    "balancing_authority_code": {
        "balancing_authority_code", "balancingauthoritycode", "bacode",
        "ba_code", "balancing_authority", "ba",
    },
    "technology": {
        "technology", "technology_description", "technologydescription", "tech",
    },
    "energy_source": {
        "energy_source", "energy_source_code", "energy_source_code_1",
        "energysourcecode", "fuel", "plprmfl", "plfuelct", "fuel_type",
    },
    "prime_mover": {
        "prime_mover", "prime_mover_code", "primemover", "primemovercode",
    },
    "nameplate_capacity_mw": {
        "nameplate_capacity_mw", "nameplate_capacity", "nameplatecapacity",
        "namepcap", "capacity_mw", "capacity",
    },
    "net_summer_capacity_mw": {
        "net_summer_capacity_mw", "net_summer_capacity", "netsummercapacity",
        "summer_capacity_mw", "summercapacity",
    },
    "operating_year": {
        "operating_year", "operatingyear", "opyr", "operating_date",
        "operatingdate",
    },
    "planned_retirement_year": {
        "planned_retirement_year", "plannedretirementyear",
        "planned_retirement_date", "plannedretirement", "retirement_year",
        "retirementyear",
    },
    "status": {"status", "statusdescription", "status_description"},
    "heat_rate": {
        "heat_rate", "heatrate", "plhtrt", "heat_rate_mmbtu_mwh",
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
# Energy-source codes that indicate oil-based fuel: distillate (DFO), residual
# (RFO), petroleum coke (PC), jet fuel (JF), kerosene (KER) and waste oil (WO).
# These map to the dedicated ``oil`` fuel type (oil peakers/steam).
_OIL_ENERGY_SOURCES = {"DFO", "RFO", "PC", "JF", "KER", "WO"}
# Energy-source codes that indicate biomass/refuse fuel: wood & wood waste
# solids (WDS), agricultural byproducts (AB), municipal solid waste (MSW),
# landfill gas (LFG), and other common biogenic streams. Map to ``biomass``.
_BIOMASS_ENERGY_SOURCES = {"WDS", "AB", "MSW", "LFG", "BLQ", "OBG", "OBL", "OBS", "WDL", "SLW", "DG"}
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


def _zone_for_index(
    index: int, n: int, zone_shares: list[tuple[str, float]]
) -> str:
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
    # largest-load-share zone.
    if iso_config is not None and iso_config.zones:
        fallback_zone = max(
            iso_config.zones, key=lambda z: z.load_share
        ).name
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

    non_nuclear = [
        i for i, rec in enumerate(records) if rec["fuel_type"] != "nuclear"
    ]
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

        records.append(
            {
                "plant_id": plant_id,
                "unit_id": f"{plant_id}_{generator_id}",
                "name": plant_name,
                "fuel_type": fuel_type,
                "efficiency_bin": ebin,
                "pmax_mw": pmax,
                "pmin_mw": pmin,
                "heat_rate": heat_rate,
                "vom": VOM.get(fuel_type, 0.0),
                "emission_rate_co2": CO2_RATES.get(fuel_type, {}).get(ebin, 0.0),
                "nox_rate": NOX_RATES.get(fuel_type, 0.0),
                "eford": EFORD.get(fuel_type, 0.05),
                "online_year": operating_year,
                "retirement_year": _to_year(data.get("planned_retirement_year")),
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


def _load_fleet_from_parquet(
    parquet_path: Path, iso: str, iso_config: ISOConfig | None
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
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce").astype(
        "Int64"
    )
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

    Reads ``inputs/processed/{iso}_fleet_binned.parquet`` written by
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
) -> list[Generator]:
    """Load an ISO's thermal generation fleet.

    Resolves the fleet from the first available source:

    1. ``generators_{iso}.csv`` in the EIA-860 directory (per-ISO override);
    2. the committed real EIA-860 generator parquet
       (:data:`EIA_860_PARQUET_NAME`), filtered to the ISO.

    Wind, solar and hydro are skipped (handled by ``renewables.py``).

    As a side output, the plant-level binned fleet is cached to
    ``inputs/processed/{iso}_fleet_binned.parquet`` for later inspection
    (see :func:`load_binned_fleet`); it is not consumed by dispatch.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        iso_config: Topology configuration supplying zone load shares. If
            ``None``, it is fetched via :func:`get_iso_config` when the ISO
            is known; ISOs without a config get a single ISO-named zone.
        data_dir: Directory holding the EIA-860 data. Defaults to
            ``inputs/raw-data/eia-860``.

    Returns:
        The ISO's thermal fleet as a list of :class:`Generator` objects.

    Raises:
        FileNotFoundError: If neither the per-ISO CSV override nor the
            EIA-860 generator parquet yields a fleet for the ISO.
    """
    iso = iso.upper()
    if data_dir is None:
        data_dir = EIA_860_DIR
    data_dir = Path(data_dir)
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    csv_path = data_dir / f"generators_{iso.lower()}.csv"
    source: Path | None
    if csv_path.exists():
        df = _normalize_columns(pd.read_csv(csv_path))
        generators = _rows_to_generators(df, iso, iso_config)
        source = csv_path
        logger.info(
            "Loaded %s fleet from EIA-860 CSV (%d generators)",
            iso,
            len(generators),
        )
    else:
        parquet_path = data_dir / EIA_860_PARQUET_NAME
        from_parquet = _load_fleet_from_parquet(parquet_path, iso, iso_config)
        if from_parquet is None:
            raise FileNotFoundError(
                f"No EIA-860 data for {iso}: expected a per-ISO override "
                f"CSV at {csv_path} or the generator parquet at "
                f"{parquet_path}"
            )
        generators = from_parquet
        source = parquet_path

    _cache_binned_fleet(iso, generators, source)
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

# ERCOT coal fuel-supply type by EIA plant code. Mine-mouth lignite plants
# ("lignite") bid into SCED at the marginal extraction cost — fixed mine
# costs are sunk on a dispatch-hour basis. PRB-by-rail plants ("prb") bid
# at the delivered contract price (mine-gate plus rail freight). The two
# differ by ~$13/MWh in fuel cost, enough to swing merit order against gas
# CC when gas is cheap. Drives fuel.apply_coal_supply_pricing.
COAL_PLANT_SUPPLY: dict[int, str] = {
    6180: "lignite",   # Oak Grove — Kosse mine
    298: "prb",        # Limestone — now PRB by rail (switched off local lignite)
    6146: "prb",       # Martin Lake — now PRB by rail (was East Texas lignite)
    6183: "lignite",   # San Miguel — adjacent lignite mine
    7030: "lignite",   # Major Oak Power
    6178: "prb",       # Coleto Creek — PRB by rail
    6179: "prb",       # Fayette / Sam Seymour — PRB by rail
    7097: "prb",       # J K Spruce — PRB by rail
    56611: "prb",      # Sandy Creek — PRB by rail (EIA-923 plant id 56611)
    3470: "prb",       # W A Parish (coal units 5-8, subbituminous) — PRB by rail
}

# ERCOT coal-unit commission year by EIA plant code — the in-service year
# of the plant's coal units (not its older gas-era units, which differ at
# mixed plants like W A Parish). Drives the age-based coal availability
# model in :func:`generators_to_fleet_arrays`.
COAL_PLANT_COMMISSION_YEAR: dict[int, int] = {
    298: 1985,    # Limestone
    3470: 1977,   # W A Parish (coal units 5-8)
    6146: 1977,   # Martin Lake
    6178: 1980,   # Coleto Creek
    6179: 1979,   # Fayette / Sam Seymour
    6180: 2010,   # Oak Grove
    6183: 1982,   # San Miguel
    7030: 1990,   # Major Oak Power
    7097: 1992,   # J K Spruce
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
    6180: 45.0,   # Oak Grove (lignite) — 12d planned block, otherwise baseload
    7030: 45.0,   # Major Oak (lignite) — 99.2% online, EAF only
    6183: 55.0,   # San Miguel (lignite) — large spring + fall blocks, ~38% off
    298: 20.0,    # Limestone (PRB) — recurring Feb winter + variable spring
    6146: 20.0,   # Martin Lake (PRB) — no systematic pattern, EAF
    6178: 30.0,   # Coleto Creek (PRB) — large spring block (shortening)
    6179: 30.0,   # Fayette (PRB) — zero outage events across 3 years
    7097: 12.0,   # J K Spruce (PRB) — scattered short shoulder events
    3470: 15.0,   # W A Parish (PRB) — mixed facility, coal outages undetectable
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
    7325: "merchant", 10154: "industrial", 10243: "industrial",
    10261: "industrial", 10298: "industrial", 10418: "industrial",
    10436: "industrial", 10554: "industrial", 10692: "industrial",
    10790: "industrial", 50026: "industrial", 50043: "industrial",
    50054: "commercial", 50118: "commercial", 50150: "industrial",
    50229: "industrial", 50475: "industrial", 50815: "merchant",
    52088: "merchant", 52120: "industrial", 52132: "industrial",
    52176: "merchant", 54330: "industrial", 54520: "commercial",
    54676: "merchant", 55015: "merchant", 55047: "merchant",
    55154: "merchant", 55187: "merchant", 55206: "merchant",
    55299: "merchant", 55311: "industrial", 55313: "industrial",
    55327: "merchant", 55464: "merchant", 55470: "industrial",
    56152: "industrial", 56374: "merchant", 57322: "industrial",
    57504: "commercial", 58151: "commercial", 58378: "merchant",
    59145: "industrial", 59381: "commercial", 62762: "merchant",
    66992: "merchant",
}
CHP_BTM_PCT_BY_SECTOR: dict[str, float] = {
    "merchant": 40.0, "industrial": 60.0, "commercial": 60.0,
}
CHP_ST_BTM_PCT: float = 90.0  # ST_CHP group (tiny chemical host-steam): near-full BTM

# Per-plant total must-run floor: the p2 CAMPD gross CF (non-outage, pooled
# 2023-2025). The grid-delivered steam-following floor applied as min-gen is
# this minus the plant's BTM share (computed at build time). Only plants with
# CAMPD coverage have a value (Baytown ~28%, ~the 27% target); absent => no
# floor, dispatched purely economically.
CHP_PMIN_CF_BY_PLANT: dict[int, float] = {
    7325: 34.6, 10298: 65.3, 50815: 36.7, 52088: 26.0, 52176: 0.0,
    55015: 49.7, 55047: 25.0, 55154: 0.0, 55187: 64.2, 55206: 25.8,
    55299: 33.1, 55327: 28.2, 55464: 33.8, 55470: 20.9, 58378: 88.8,
}


# Per-plant CC_REGULAR committed-tranche % (minimum stable load once started),
# keyed by EIA plant code. Derived from EPA CAMPD/CEMS TX 2023 hourly gross
# output over Jan-July (the window inputs/tx-jan-aug23-unit-outages.csv covers,
# so available capacity is known): the P5 of each plant's net capacity factor
# over its committed (online) hours, normalized by the unit-outage-adjusted
# available capacity. See scripts/derive_cc_committed_pct.py and
# inputs/processed/cc_committed_pct.csv for the full percentile distribution.
# Replaces the coarse assumed CSV Pct_Committed (clustered at 20/25/45/55) when
# config.cc_committed_per_plant is set; the economic tranche absorbs the
# difference so each plant's tranche split still sums to 100%. Plants without
# CAMPD coverage (7512, 50127, 55545, 56233) keep the CSV value.
CC_REGULAR_COMMITTED_PCT_BY_PLANT: dict[int, float] = {
    3441: 11.5,   # Nueces Bay (online 0.41)
    3443: 44.7,   # Victoria (online 0.28)
    3469: 8.4,    # T H Wharton (online 0.22)
    3631: 8.1,    # Sam Rayburn (online 0.39)
    4937: 33.3,   # Thomas C Ferguson (online 0.89)
    4939: 7.7,    # Barney M Davis [CC] (online 0.46)
    7900: 17.9,   # Sand Hill (online 0.87)
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


# Per-plant CC_REGULAR peaking-tranche % (top slice of nameplate priced at the
# duct-burner peak multiplier), keyed by EIA plant code. Used in place of the
# offer curve's ``pct_peaking`` when config.cc_peaking_per_plant is set, so the
# expensive peak band starts earlier on the CF axis (15% => peaking starts at
# 85% of nameplate). Applies to the four F-class(late) 2x1 CCs the model
# over-runs in the 80-90% CF range; the economic tranche absorbs the change.
CC_REGULAR_PEAKING_PCT_BY_PLANT: dict[int, float] = {
    58001: 15.0,  # Temple Power Station
    58005: 15.0,  # Rayburn Energy Station LLC
    59812: 15.0,  # Wolf Hollow II
    60122: 15.0,  # Colorado Bend II
}


def chp_btm_pct(plant_code: int, group: str) -> float:
    """Behind-the-meter pull-out share (% of nameplate) for a CHP plant."""
    if group == "ST_CHP":
        return CHP_ST_BTM_PCT
    return CHP_BTM_PCT_BY_SECTOR[
        CHP_SECTOR_CLASS_BY_PLANT.get(int(plant_code), "merchant")
    ]

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

# Fallback heat rate (MMBtu/MWh) by plant group, used when a bin's
# Bin_Zone_Weighted_Avg_HR is blank in the CSV (e.g. tiny unmetered CTs).
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
    "Plant_Group", "ERCOT_Zone", "Bin_Number", "Bin_Label",
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


# Default location of the CAMPD-derived per-plant emission-rate artifact
# (scripts/derive_plant_emissions.py), resolved relative to the repo root.
PLANT_EMISSION_RATES_PATH: Path = (
    Path(__file__).parents[3] / "inputs" / "processed"
    / "plant_emission_rates.parquet"
)

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
    "CC_CHP":     {"mr": 1.05, "mc": 1.05, "econ": 1.00, "peak": 1.45},
    "CC_REGULAR": {"mr": 1.10, "mc": 1.08, "econ": 1.00, "peak": 1.55},
    "CT_CHP":     {"mr": 1.05, "mc": 1.10, "econ": 1.00, "peak": 1.15},
    "CT_PEAKER":  {"mr": 1.05, "mc": 1.12, "econ": 1.00, "peak": 1.10},
    "ST_GAS":     {"mr": 1.10, "mc": 1.15, "econ": 1.00, "peak": 1.10},
    "ST_CHP":     {"mr": 1.05, "mc": 1.10, "econ": 1.00, "peak": 1.10},
    "COAL":       {"mr": 1.00, "mc": 1.15, "econ": 1.00, "peak": 1.05},
}


def load_campd_bins(csv_path: str | Path) -> pd.DataFrame:
    """Load the CAMPD bin assignments, one row per plant.

    The detail CSV has one row per plant; this normalises it into the
    one-bin-per-plant LP fleet schema. Every plant becomes its own
    operational bin: tranche percentages, commitment hours and the
    per-tranche HR multipliers come directly from the plant's CSV row,
    and per-tranche heat rates are derived from the plant's own
    ``Plant_Avg_HR_MMBtu_MWh`` rather than a zone-weighted average.

    Per-plant binning is the model spine for plant-specific monthly
    EIA-923 fuel costs and asset-level financial reporting — each LP bin
    is one EIA plant code, so dispatch and downstream P&L disaggregation
    share the same row identity.

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

    # Each plant's tranche HR = Plant_Avg_HR × HR_Mult_<tranche>. We fill
    # missing plant heat rates with the per-group default and missing
    # multipliers with the group-typical value so the tranche arithmetic
    # is well-defined; tranches whose capacity is zero are skipped by
    # ``bins_to_fleet`` regardless of the resulting HR.
    plant_hr = [
        _fill_plant_hr(hr, grp)
        for hr, grp in zip(
            detail["Plant_Avg_HR_MMBtu_MWh"], detail["Plant_Group"]
        )
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
    bins = pd.DataFrame({
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
    })
    for short, col in mult_columns.items():
        bins[f"hr_{short}"] = [
            hr * _fill_hr_multiplier(mult, defaults[short])
            for hr, mult, defaults in zip(
                plant_hr, detail[col], defaults_by_idx
            )
        ]
    bins["plant_count"] = 1
    bins["plant_codes"] = [[int(c)] for c in detail["Plant_Code"]]
    bins["fuel"] = fuel_series.values

    bad = bins["pct_mr"] + bins["pct_mc"] + bins["pct_econ"] + bins["pct_peak"]
    if not (bad == 100).all():
        offending = bins.loc[bad != 100, "Plant_Name"].tolist()
        raise ValueError(
            f"CAMPD bin tranches must sum to 100%; offending plants: {offending}"
        )

    logger.info(
        "Loaded %d per-plant CAMPD bins from %s (%.1f GW)",
        len(bins), csv_path, bins["capacity_mw"].sum() / 1000.0,
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
    "f": 2.25,         # F-class incl. E/F
    "older": 2.00,     # E-class, legacy
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


def _offer_curve_for_group(
    group: str, plant_code: int, config: ScenarioConfig
) -> dict[str, float] | None:
    """Return the offer-curve band multipliers for a group, or ``None``.

    Reads ``config.offer_curve_by_group[group]`` (see :class:`ScenarioConfig`).
    Returns ``None`` — the legacy override / CSV path — when no curve is
    configured for the group or for an ST_GAS peaker plant (those keep their
    CSV heat rates, matching the ``gas_st_*_hr_override`` scope). COAL plants
    resolve to a supply-specific ``COAL_LIGNITE`` / ``COAL_PRB`` entry when
    present, else the generic ``COAL`` entry.
    """
    curves = getattr(config, "offer_curve_by_group", None) or {}
    if group == "COAL":
        supply = COAL_PLANT_SUPPLY.get(int(plant_code), "")
        key = ("COAL_LIGNITE" if supply == "lignite"
               else "COAL_PRB" if supply == "prb" else None)
        return (curves.get(key) if key and curves.get(key)
                else curves.get("COAL")) or None
    if group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS:
        return None
    return curves.get(group) or None


def _econ_split_for_group(
    group: str, plant_code: int, config: ScenarioConfig
) -> tuple[float, float, float] | None:
    """Return ``(split_frac, lo_hr_mult, hi_hr_mult)`` for the econ split, or ``None``.

    Reads ``config.econ_split_by_group[group] = [split_frac, lo_hr_mult,
    hi_hr_mult]`` (see :class:`ScenarioConfig`). Returns ``None`` — a single
    economic tranche, the default behavior — when no split is configured for
    the group or for an ST_GAS peaker plant (those dispatch on CSV heat rates,
    matching the ``gas_st_*_hr_override`` scope). ``split_frac`` is clamped to
    ``[0, 1]``.
    """
    spec_map = getattr(config, "econ_split_by_group", None) or {}
    spec = spec_map.get(group)
    if not spec:
        return None
    if group == "ST_GAS" and plant_code in ST_GAS_PEAKER_PLANTS:
        return None
    frac, lo_mult, hi_mult = float(spec[0]), float(spec[1]), float(spec[2])
    return max(0.0, min(1.0, frac)), lo_mult, hi_mult


# Numeric columns of the per-plant tranche-config override sheet
# (scripts/export_tranche_config.py). The five ``Pct_*`` are tranche shares of
# nameplate (must-run + committed + econ-low + econ-high + peaking = 100); the
# five ``HR_Mult_*`` are per-tranche multipliers on the plant's base HR. Other
# columns in the sheet (names, group, config, turbine class …) are reference
# only and ignored by the loader.
PLANT_TRANCHE_OVERRIDE_FIELDS: dict[str, str] = {
    "pct_mr": "Pct_Must_Run", "pct_mc": "Pct_Committed",
    "pct_lo": "Pct_Econ_Low", "pct_hi": "Pct_Econ_High",
    "pct_pk": "Pct_Peaking",
    "hr_mr": "HR_Mult_Must_Run", "hr_mc": "HR_Mult_Committed",
    "hr_lo": "HR_Mult_Econ_Low", "hr_hi": "HR_Mult_Econ_High",
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
    missing = [c for c in PLANT_TRANCHE_OVERRIDE_FIELDS.values()
               if c not in df.columns]
    if "Plant_Code" not in df.columns or missing:
        raise ValueError(
            f"tranche-config sheet {path} missing columns: "
            f"{(['Plant_Code'] if 'Plant_Code' not in df.columns else []) + missing}"
        )
    out: dict[int, dict[str, float]] = {}
    for _, row in df.iterrows():
        try:
            rec = {key: float(row[col])
                   for key, col in PLANT_TRANCHE_OVERRIDE_FIELDS.items()}
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

    for _, b in bins.iterrows():
        pct_mr = float(b["pct_mr"])
        nameplate = float(b["capacity_mw"])
        fuel = BIN_GROUP_TO_FUEL[b["Plant_Group"]]
        ov = tranche_ov.get(int(b["Plant_Code"]))
        # Coal must-run override (calibration): per-plant CAMPD-derived floor
        # (config.coal_mustrun_per_plant) takes precedence; otherwise the
        # uniform lignite/PRB supply override (sweep). The grid tranches
        # rescale via `denom`.
        if fuel == "coal":
            _pc = int(b["Plant_Code"])
            _supply = COAL_PLANT_SUPPLY.get(_pc, "")
            if (config.coal_mustrun_per_plant
                    and _pc in COAL_MUSTRUN_BY_PLANT):
                pct_mr = COAL_MUSTRUN_BY_PLANT[_pc]
            elif (_supply == "lignite"
                    and config.coal_lignite_mustrun_override is not None):
                pct_mr = config.coal_lignite_mustrun_override
            elif (_supply == "prb"
                    and config.coal_prb_mustrun_override is not None):
                pct_mr = config.coal_prb_mustrun_override
        # Steam-following cogen treatment: a CC_CHP bin's behind-the-meter host
        # self-supply (removed from the grid, added back in the report) is
        # chp_btm_floor_pct of nameplate, not the CSV Pct_Must_Run merchant
        # split. Overriding pct_mr here shrinks the removed share and grows the
        # grid-facing capacity, which the steam floor + expensive load-following
        # below then shape into base + dispatchable rather than a flat slab.
        chp_following = (
            str(b["Plant_Group"]) in ("CC_CHP", "CT_CHP", "ST_CHP")
            and getattr(config, "chp_steam_following", False)
        )
        if chp_following:
            pct_mr = chp_btm_pct(int(b["Plant_Code"]), str(b["Plant_Group"]))
        if ov is not None:
            pct_mr = ov["pct_mr"]
        # Coal must-run capacity stays IN the LP as a ``_mustrun`` tranche
        # (its fuel is sunk under take-or-pay; bids at VOM + carbon + NOx
        # only via the runner). Non-coal bins' must-run share is host
        # steam cogen and is removed from LP capacity; its generation and
        # emissions are added back by post-processing.
        if fuel == "coal":
            mustrun_cap = nameplate * pct_mr / 100.0
            grid_cap = nameplate - mustrun_cap
        else:
            mustrun_cap = 0.0
            grid_cap = nameplate * (1.0 - pct_mr / 100.0)
        if grid_cap + mustrun_cap <= 0.0:
            continue

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
        if (group == "CC_REGULAR"
                and getattr(config, "cc_committed_per_plant", False)
                and plant_code in CC_REGULAR_COMMITTED_PCT_BY_PLANT):
            pct_mc = CC_REGULAR_COMMITTED_PCT_BY_PLANT[plant_code]
        # Peaking %: the offer curve may override the CSV value before the
        # residual is split into the two economic steps (residual = 100 -
        # must_run - committed - peaking).
        pct_peak = float(b["pct_peak"])
        if offer is not None and "pct_peaking" in offer:
            pct_peak = float(offer["pct_peaking"])
        if (group == "CC_REGULAR"
                and getattr(config, "cc_peaking_per_plant", False)
                and plant_code in CC_REGULAR_PEAKING_PCT_BY_PLANT):
            pct_peak = CC_REGULAR_PEAKING_PCT_BY_PLANT[plant_code]
        if ov is not None:
            pct_mc, pct_peak = ov["pct_mc"], ov["pct_pk"]
        denom = 100.0 - pct_mr
        committed_cap = grid_cap * pct_mc / denom if denom > 0.0 else 0.0
        peak_cap = grid_cap * pct_peak / denom if denom > 0.0 else 0.0
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
            coal_supply = COAL_PLANT_SUPPLY.get(plant_code, "")
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
            # below). CC peaking uses the per-plant duct-burner multiplier
            # (turbine class); other groups use the curve's "peak". VOM is held
            # constant across bands (the peak band's VOM markup is dropped).
            committed_hr = base_hr * float(offer["committed"])
            if group in ("CC_REGULAR", "CC_CHP"):
                peak_hr = base_hr * cc_duct_burner_peak_mult(
                    b.get("Turbine_Class")
                )
            else:
                peak_hr = base_hr * float(offer["peak"])
        else:
            # Legacy per-class supply-curve overrides (relative to base HR),
            # used when no offer curve covers the group: CC committed/econ/peak,
            # reliability ST_GAS (peakers keep CSV heat rates), and CT_CHP.
            cc_mc = getattr(config, "cc_committed_hr_override", None)
            if group in ("CC_REGULAR", "CC_CHP") and cc_mc is not None:
                committed_hr = base_hr * cc_mc
                econ_hr = base_hr * float(
                    getattr(config, "cc_econ_hr_override", 1.2)
                )
                peak_hr = base_hr * float(
                    getattr(config, "cc_peak_hr_override", 1.8)
                )
            st_mc = getattr(config, "gas_st_committed_hr_override", None)
            if (group == "ST_GAS" and plant_code not in ST_GAS_PEAKER_PLANTS
                    and st_mc is not None):
                committed_hr = base_hr * st_mc
                econ_hr = base_hr * float(
                    getattr(config, "gas_st_econ_hr_override", 1.0)
                )
                peak_hr = base_hr * float(
                    getattr(config, "gas_st_peak_hr_override", 1.5)
                )
            ct_mc = getattr(config, "ct_committed_hr_override", None)
            if group == "CT_CHP" and ct_mc is not None:
                committed_hr = base_hr * ct_mc
                econ_hr = base_hr * float(
                    getattr(config, "ct_econ_hr_override", 1.1)
                )
                peak_hr = base_hr * float(
                    getattr(config, "ct_peak_hr_override", 1.3)
                )
        if ov is not None:
            # Per-plant sheet wins: all band heat rates are base_HR x the sheet's
            # multipliers (econ-low/-high set in the econ split below).
            mustrun_hr = base_hr * ov["hr_mr"]
            committed_hr = base_hr * ov["hr_mc"]
            peak_hr = base_hr * ov["hr_pk"]
        # CHP steam-following grid floor pinned onto the econ tranche: the
        # plant's total must-run (p2 CAMPD gross CF) minus its BTM share, i.e.
        # the steady export delivered to the grid above host self-supply. Only
        # CAMPD-covered plants have a floor; the rest export surplus only.
        chp_pmin_mw = 0.0
        if chp_following:
            pmin_cf = CHP_PMIN_CF_BY_PLANT.get(plant_code)
            if pmin_cf is not None:
                grid_mr_cf = max(0.0, pmin_cf - pct_mr)
                chp_pmin_mw = min(grid_mr_cf / 100.0 * nameplate, econ_cap)

        # Economic tranche(s). One tranche at econ_hr by default; the offer
        # curve (or the standalone econ split) replaces it with two stepped
        # tranches — a rising heat rate (base_HR x lo/hi multiplier) across the
        # economic block, the lower step holding the configured share of the
        # economic capacity. The first econ step carries any CHP
        # steam-following floor.
        if ov is not None:
            # Per-plant sheet: the two econ steps take their capacity straight
            # from the sheet's econ-low/-high shares of nameplate and their heat
            # rates from the sheet's multipliers.
            econ_steps = [
                ("econlo", nameplate * ov["pct_lo"] / 100.0,
                 base_hr * ov["hr_lo"], 1.0, 0, 0, 0.0),
                ("econhi", nameplate * ov["pct_hi"] / 100.0,
                 base_hr * ov["hr_hi"], 1.0, 0, 0, 0.0),
            ]
        elif offer is not None:
            share = float(offer["econ_low_share"])
            econ_steps = [
                ("econlo", econ_cap * share, base_hr * float(offer["econ_low"]),
                 1.0, 0, 0, 0.0),
                ("econhi", econ_cap * (1.0 - share),
                 base_hr * float(offer["econ_high"]), 1.0, 0, 0, 0.0),
            ]
        elif (split := _econ_split_for_group(group, plant_code, config)) is not None:
            split_frac, lo_mult, hi_mult = split
            econ_steps = [
                ("econlo", econ_cap * split_frac, base_hr * lo_mult,
                 1.0, 0, 0, 0.0),
                ("econhi", econ_cap * (1.0 - split_frac), base_hr * hi_mult,
                 1.0, 0, 0, 0.0),
            ]
        else:
            econ_steps = [("econ", econ_cap, econ_hr, 1.0, 0, 0, 0.0)]
        first_econ_suffix = econ_steps[0][0]

        # Stepped tranches: (suffix, capacity, heat rate, VOM multiplier,
        # min-run, min-down, start cost). Only the Committed tranche is
        # screened and carries the start cost; Must-Run, Economic and Peaking
        # are incremental output of an already-running plant. No tranche
        # carries a Pmin floor — the Must-Run tranche is forced on by bidding
        # at VOM only (fuel_fracs in the runner).
        # Peak-band VOM multiplier: the offer curve holds VOM constant across
        # bands (band MC = VOM + (AHR x fuel) x mult); the legacy path keeps
        # the 1.5x peak VOM markup.
        peak_vom_mult = 1.0 if offer is not None else 1.5
        tranches = [
            ("mustrun", mustrun_cap, mustrun_hr, 1.0, 0, 0, 0.0),
            ("committed", committed_cap, committed_hr, 1.0,
             int(b["min_run"]), int(b["min_down"]), startup),
            *econ_steps,
            ("peak", peak_cap, peak_hr, peak_vom_mult, 0, 0, 0.0),
        ]
        for suffix, cap, tr_hr, vom_mult, min_run, min_down, tr_startup in (
            tranches
        ):
            if cap <= 0.5:
                continue
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
                    emission_rate_co2=get_emission_rate(fuel, tr_hr),
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
                    bin_nameplate_mw=(
                        nameplate if suffix == "committed" else 0.0
                    ),
                    coal_supply=coal_supply,
                    plant_code=plant_code,
                    chp_grid_pmin_mw=(
                        chp_pmin_mw if suffix == first_econ_suffix else 0.0
                    ),
                )
            )

    fleet_arrays = generators_to_fleet_arrays(
        fleet, zone_names, hours=config.hours, iso=config.iso, config=config
    )
    return fleet, fleet_arrays


def _bands_from_shares(
    raw: list[tuple[str, float, float, bool]], is_coal: bool
) -> list[dict]:
    """Stack ``(name, pct_of_nameplate, hr_mult, vom)`` tranches into CF bands.

    Bands accumulate from CF 0 in dispatch fill order, dropping empty ones. The
    non-coal must-run share is host steam removed from the grid, so it is not
    shown and does not shift the grid bands (committed still starts at CF 0);
    the coal must-run band is the in-LP VOM-only floor and is shown from 0.
    """
    bands: list[dict] = []
    cursor = 0.0
    for name, pct, mult, vom in raw:
        if name == "must-run" and not is_coal:
            continue
        lo, hi = cursor, cursor + pct
        cursor = hi
        if pct <= 0.5:
            continue
        bands.append({"name": name, "cf_lo": round(lo, 1),
                      "cf_hi": round(hi, 1), "mult": round(mult, 3),
                      "vom": vom})
    return bands


def plant_tranche_bands(
    b: "pd.Series | dict", config: ScenarioConfig
) -> list[dict]:
    """Return one plant's offer-curve tranche bands on the capacity-factor axis.

    Mirrors the tranche capacity and per-band heat-rate resolution in
    :func:`bins_to_fleet` (same offer-curve lookup, per-plant committed %,
    peaking override, econ split and CC duct-burner peak) and converts the
    cumulative tranche capacities into capacity-factor edges (percent of
    nameplate). The bands stack in dispatch fill order — must-run, committed,
    econ-lo, econ-hi, peak — so the dashboard can mark where each band engages
    on the CF axis and label the heat-rate multiplier priced there.

    Args:
        b: One row of the :func:`load_campd_bins` frame (or an equivalent
            mapping) for a single plant.
        config: The run's scenario configuration (offer curves, per-plant
            committed flag, mustrun overrides).

    Returns:
        A list of ``{"name", "cf_lo", "cf_hi", "mult", "vom"}`` dicts — one per
        non-empty band, in increasing CF order. ``mult`` is the band heat rate
        over the plant's base HR; ``vom`` flags the must-run band, which bids
        VOM-only (its fuel is sunk) rather than at a heat-rate multiplier.
        Empty when the plant has no nameplate.
    """
    group = str(b["Plant_Group"])
    plant_code = int(b["Plant_Code"])
    nameplate = float(b["capacity_mw"])
    if nameplate <= 0.0:
        return []
    fuel = BIN_GROUP_TO_FUEL[group]

    # Per-plant tranche-config sheet wins (same precedence as bins_to_fleet):
    # build the bands straight from the sheet's shares + multipliers so the
    # dashboard markers track what the user edited.
    _ov_path = getattr(config, "plant_tranche_config_path", None)
    if _ov_path:
        ov = load_plant_tranche_config(_ov_path).get(plant_code)
        if ov is not None:
            return _bands_from_shares(
                [("must-run", ov["pct_mr"], ov["hr_mr"], True),
                 ("committed", ov["pct_mc"], ov["hr_mc"], False),
                 ("econ-lo", ov["pct_lo"], ov["hr_lo"], False),
                 ("econ-hi", ov["pct_hi"], ov["hr_hi"], False),
                 ("peak", ov["pct_pk"], ov["hr_pk"], False)],
                is_coal=(fuel == "coal"),
            )

    offer = _offer_curve_for_group(group, plant_code, config)

    # Resolve must-run / committed / peaking percentages exactly as
    # bins_to_fleet does (coal overrides, CHP host-steam, per-plant committed,
    # offer peaking override).
    pct_mr = float(b["pct_mr"])
    if fuel == "coal":
        _supply = COAL_PLANT_SUPPLY.get(plant_code, "")
        if config.coal_mustrun_per_plant and plant_code in COAL_MUSTRUN_BY_PLANT:
            pct_mr = COAL_MUSTRUN_BY_PLANT[plant_code]
        elif (_supply == "lignite"
                and config.coal_lignite_mustrun_override is not None):
            pct_mr = config.coal_lignite_mustrun_override
        elif (_supply == "prb"
                and config.coal_prb_mustrun_override is not None):
            pct_mr = config.coal_prb_mustrun_override
    if (group in ("CC_CHP", "CT_CHP", "ST_CHP")
            and getattr(config, "chp_steam_following", False)):
        pct_mr = chp_btm_pct(plant_code, group)
    pct_mc = float(b["pct_mc"])
    if (group == "CC_REGULAR"
            and getattr(config, "cc_committed_per_plant", False)
            and plant_code in CC_REGULAR_COMMITTED_PCT_BY_PLANT):
        pct_mc = CC_REGULAR_COMMITTED_PCT_BY_PLANT[plant_code]
    pct_peak = float(b["pct_peak"])
    if offer is not None and "pct_peaking" in offer:
        pct_peak = float(offer["pct_peaking"])
    if (group == "CC_REGULAR"
            and getattr(config, "cc_peaking_per_plant", False)
            and plant_code in CC_REGULAR_PEAKING_PCT_BY_PLANT):
        pct_peak = CC_REGULAR_PEAKING_PCT_BY_PLANT[plant_code]

    if fuel == "coal":
        mustrun_cap = nameplate * pct_mr / 100.0
        grid_cap = nameplate - mustrun_cap
    else:
        mustrun_cap = 0.0
        grid_cap = nameplate * (1.0 - pct_mr / 100.0)
    denom = 100.0 - pct_mr
    committed_cap = grid_cap * pct_mc / denom if denom > 0.0 else 0.0
    peak_cap = grid_cap * pct_peak / denom if denom > 0.0 else 0.0
    econ_cap = max(grid_cap - committed_cap - peak_cap, 0.0)

    # Per-band heat rates, mirroring bins_to_fleet (offer-curve multipliers,
    # CC duct-burner peak, or the legacy per-class overrides / CSV columns).
    base_hr = float(b["hr_weighted"])
    mustrun_hr = float(b["hr_mr"])
    committed_hr = float(b["hr_mc"])
    econ_hr = float(b["hr_econ"])
    peak_hr = float(b["hr_peak"])
    if offer is not None:
        committed_hr = base_hr * float(offer["committed"])
        if group in ("CC_REGULAR", "CC_CHP"):
            peak_hr = base_hr * cc_duct_burner_peak_mult(b.get("Turbine_Class"))
        else:
            peak_hr = base_hr * float(offer["peak"])
    else:
        cc_mc = getattr(config, "cc_committed_hr_override", None)
        if group in ("CC_REGULAR", "CC_CHP") and cc_mc is not None:
            committed_hr = base_hr * cc_mc
            econ_hr = base_hr * float(getattr(config, "cc_econ_hr_override", 1.2))
            peak_hr = base_hr * float(getattr(config, "cc_peak_hr_override", 1.8))
        st_mc = getattr(config, "gas_st_committed_hr_override", None)
        if (group == "ST_GAS" and plant_code not in ST_GAS_PEAKER_PLANTS
                and st_mc is not None):
            committed_hr = base_hr * st_mc
            econ_hr = base_hr * float(
                getattr(config, "gas_st_econ_hr_override", 1.0))
            peak_hr = base_hr * float(
                getattr(config, "gas_st_peak_hr_override", 1.5))
        ct_mc = getattr(config, "ct_committed_hr_override", None)
        if group == "CT_CHP" and ct_mc is not None:
            committed_hr = base_hr * ct_mc
            econ_hr = base_hr * float(getattr(config, "ct_econ_hr_override", 1.1))
            peak_hr = base_hr * float(getattr(config, "ct_peak_hr_override", 1.3))

    if offer is not None:
        share = float(offer["econ_low_share"])
        econ_steps = [
            ("econ-lo", econ_cap * share, base_hr * float(offer["econ_low"])),
            ("econ-hi", econ_cap * (1.0 - share),
             base_hr * float(offer["econ_high"])),
        ]
    elif (split := _econ_split_for_group(group, plant_code, config)) is not None:
        split_frac, lo_mult, hi_mult = split
        econ_steps = [
            ("econ-lo", econ_cap * split_frac, base_hr * lo_mult),
            ("econ-hi", econ_cap * (1.0 - split_frac), base_hr * hi_mult),
        ]
    else:
        econ_steps = [("econ", econ_cap, econ_hr)]

    raw = [
        ("must-run", mustrun_cap, mustrun_hr, True),
        ("committed", committed_cap, committed_hr, False),
        *[(name, cap, hr, False) for name, cap, hr in econ_steps],
        ("peak", peak_cap, peak_hr, False),
    ]
    bands: list[dict] = []
    cursor = 0.0
    for name, cap, hr, vom_only in raw:
        lo, hi = cursor, cursor + cap
        cursor = hi
        if cap <= 0.5:  # dropped from the LP in bins_to_fleet
            continue
        bands.append({
            "name": name,
            "cf_lo": round(lo / nameplate * 100.0, 1),
            "cf_hi": round(hi / nameplate * 100.0, 1),
            "mult": round(hr / base_hr, 3) if base_hr > 0.0 else None,
            "vom": vom_only,
        })
    return bands
