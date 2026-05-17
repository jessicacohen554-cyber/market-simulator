"""Generation fleet inventory and attributes.

Provides the :class:`Generator` model, its vectorized :class:`FleetArrays`
form, and loaders that build a per-ISO thermal fleet from EIA-860 / eGRID
CSV extracts.
"""

from __future__ import annotations

import logging
import random
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel

from market_sim.config.constants import (
    CO2_RATES,
    EFORD,
    HEAT_RATE_BINS,
    NOX_RATES,
    VOM,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config

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
    "planned_retirement_year", "status",
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
# Code 11 is intentionally reserved (left as a gap) for a future fuel type.
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
    "geothermal": 12,     # enhanced geothermal systems (EGS)
    "offshore_wind": 13,  # offshore wind (fixed-bottom and floating)
}

# Inverse of FUEL_TYPE_MAP: fuel type name indexed by its integer code.
# Sized to the largest code so a gap in the code space (e.g. the reserved
# code 11) yields an empty string rather than a misaligned name.
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
    eford: float = 0.05
    online_year: int = 2000
    retirement_year: int | None = None
    is_must_run: bool = False


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
    zone_idx: np.ndarray
    fuel_type_idx: np.ndarray
    availability: np.ndarray
    unit_ids: list[str]
    efficiency_bin: np.ndarray

    @property
    def n_gen(self) -> int:
        """Return the number of generators in the fleet."""
        return len(self.unit_ids)


def generators_to_fleet_arrays(
    generators: list[Generator],
    zone_names: list[str],
    hours: int = 8760,
) -> FleetArrays:
    """Convert a list of generators into vectorized ``FleetArrays``.

    Availability is set to ``1 - eford`` for every hour; seasonal and
    maintenance derate factors are applied later in the pipeline.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}

    n_gen = len(generators)
    pmax = np.array([g.pmax_mw for g in generators], dtype=float)
    pmin = np.array([g.pmin_mw for g in generators], dtype=float)
    heat_rate = np.array([g.heat_rate for g in generators], dtype=float)
    vom = np.array([g.vom for g in generators], dtype=float)
    emission_rate = np.array([g.emission_rate_co2 for g in generators], dtype=float)
    nox_rate = np.array([g.nox_rate for g in generators], dtype=float)
    zone_idx = np.array([zone_to_idx[g.zone] for g in generators], dtype=int)
    fuel_type_idx = np.array(
        [FUEL_TYPE_MAP[g.fuel_type] for g in generators], dtype=int
    )

    eford = np.array([g.eford for g in generators], dtype=float)
    availability = np.broadcast_to(
        (1.0 - eford)[:, np.newaxis], (n_gen, hours)
    ).copy()

    return FleetArrays(
        pmax=pmax,
        pmin=pmin,
        heat_rate=heat_rate,
        vom=vom,
        emission_rate=emission_rate,
        nox_rate=nox_rate,
        zone_idx=zone_idx,
        fuel_type_idx=fuel_type_idx,
        availability=availability,
        unit_ids=[g.unit_id for g in generators],
        efficiency_bin=np.array(
            [g.efficiency_bin for g in generators], dtype=str
        ),
    )


# Fuel types collapsed into efficiency-bin representative units. Everything
# else -- nuclear, hydro, import (few in number, distinct characteristics)
# and wind/solar (not part of the thermal fleet) -- passes through unchanged.
_AGGREGATABLE_FUELS: frozenset[str] = frozenset({"gas_cc", "gas_ct", "coal"})


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
    generators: list[Generator], n_bins: int | None = None
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

    Nuclear, hydro and import units pass through unchanged -- they are few
    in number and have distinct characteristics. Wind and solar are not part
    of the thermal fleet handled here, so they are unaffected. A thermal unit
    carrying a scheduled ``retirement_year`` also passes through, so the
    known-retirement mechanism keeps its per-unit retirement dates.

    Args:
        generators: The individual-unit fleet.
        n_bins: Number of equal-width efficiency bins per ``(fuel_type, zone)``
            group. ``None`` uses the predefined vintage bins.

    Returns:
        A new fleet list: pass-through units in their original order,
        followed by one representative unit per thermal group.
    """
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
    "diablo canyon": "CAISO_main",
}

# Energy-source codes (EIA-860 / eGRID PLPRMFL) that indicate coal steam.
_COAL_ENERGY_SOURCES = {"SUB", "BIT", "LIG", "ANT", "RC", "WC"}
# Energy-source codes that indicate oil / distillate fuel (dual-fuel CTs).
_OIL_ENERGY_SOURCES = {"DFO", "RFO", "JF", "KER", "WO"}
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

    Returns one of ``gas_cc``, ``gas_ct``, ``coal`` or ``nuclear``, or
    ``None`` for wind, solar, hydro and other non-thermal resources, which
    are handled elsewhere.
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
        # Oil / dual-fuel units (mainly NEISO) are modeled as gas CTs.
        return "gas_ct"
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
