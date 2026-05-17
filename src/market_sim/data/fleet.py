"""Generation fleet inventory and attributes.

Provides the :class:`Generator` model, its vectorized :class:`FleetArrays`
form, and loaders that build a per-ISO thermal fleet either from EIA-860 /
eGRID CSV extracts or from a deterministic synthetic fleet fallback.
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
FUEL_TYPE_MAP: dict[str, int] = {
    "gas_cc": 0,
    "gas_ct": 1,
    "coal": 2,
    "nuclear": 3,
    "wind": 4,
    "solar": 5,
    "hydro": 6,
    "import": 7,
}

# Inverse of FUEL_TYPE_MAP: fuel type name indexed by its integer code.
FUEL_TYPE_NAMES: list[str] = [
    name for name, _ in sorted(FUEL_TYPE_MAP.items(), key=lambda item: item[1])
]


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
    )


# Fuel types collapsed into efficiency-bin representative units. Everything
# else -- nuclear, hydro, import (few in number, distinct characteristics)
# and wind/solar (not part of the thermal fleet) -- passes through unchanged.
_AGGREGATABLE_FUELS: frozenset[str] = frozenset({"gas_cc", "gas_ct", "coal"})


def aggregate_fleet(generators: list[Generator]) -> list[Generator]:
    """Collapse individual generators into representative units.

    Thermal generators are grouped by ``(fuel_type, efficiency_bin, zone)``;
    each group becomes a single :class:`Generator` whose capacity is the
    group total and whose per-MWh attributes are capacity-weighted averages
    of the group. This shrinks the LP from one column per physical unit
    (200+) to one column per thermal bin (~36), the dominant solve-time win.

    Nuclear, hydro and import units pass through unchanged -- they are few
    in number and have distinct characteristics. Wind and solar are not part
    of the thermal fleet handled here, so they are unaffected. A thermal unit
    carrying a scheduled ``retirement_year`` also passes through, so the
    known-retirement mechanism keeps its per-unit retirement dates.

    Args:
        generators: The individual-unit fleet.

    Returns:
        A new fleet list: pass-through units in their original order,
        followed by one representative unit per thermal group, ordered by
        ``(fuel_type, efficiency_bin, zone)``.
    """
    passthrough: list[Generator] = []
    groups: dict[tuple[str, str, str], list[Generator]] = {}
    for g in generators:
        if g.fuel_type not in _AGGREGATABLE_FUELS or g.retirement_year is not None:
            passthrough.append(g)
            continue
        key = (g.fuel_type, g.efficiency_bin, g.zone)
        groups.setdefault(key, []).append(g)

    representatives: list[Generator] = []
    for key in sorted(groups):
        fuel_type, efficiency_bin, zone = key
        units = groups[key]
        total_cap = sum(u.pmax_mw for u in units)

        def _weighted(attr: str) -> float:
            """Return the capacity-weighted average of ``attr`` over the group."""
            if total_cap > 0.0:
                return (
                    sum(getattr(u, attr) * u.pmax_mw for u in units) / total_cap
                )
            return sum(getattr(u, attr) for u in units) / len(units)

        unit_id = f"{fuel_type}_{efficiency_bin}_{zone}"
        representatives.append(
            Generator(
                unit_id=unit_id,
                name=unit_id,
                zone=zone,
                fuel_type=fuel_type,
                efficiency_bin=efficiency_bin,
                pmax_mw=total_cap,
                pmin_mw=sum(u.pmin_mw for u in units),
                heat_rate=_weighted("heat_rate"),
                vom=_weighted("vom"),
                emission_rate_co2=_weighted("emission_rate_co2"),
                nox_rate=_weighted("nox_rate"),
                eford=_weighted("eford"),
            )
        )

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
# Fleet loading from EIA-860 / eGRID CSVs (with synthetic fallback)
# ---------------------------------------------------------------------------

# Maps many possible source column names (lower-cased, spaces → underscores)
# to the canonical names the loader works with. Covers the EIA-860 API,
# eGRID plant/unit files, and the synthetic fleet CSV.
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

    Handles the differing column names of the EIA-860 API, eGRID extracts
    and the synthetic fleet CSV. Unknown columns are left untouched;
    duplicate canonical columns keep the first occurrence.

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
    """Assign each generator record a zone.

    Non-nuclear units are spread across the ISO's load zones in proportion
    to each zone's ``load_share``; zones with zero load share (such as
    CAISO's ``WECC_import`` import node) never receive a thermal generator.
    Nuclear units use an explicit zone where the plant is known, otherwise
    the largest-load-share zone. If no ``iso_config`` is available, every
    generator is placed in a single zone named after the ISO.
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
        Generator(zone=zone, **rec) for rec, zone in zip(records, zones)
    ]


def _load_fleet_from_parquet(
    parquet_path: Path, iso: str, iso_config: ISOConfig | None
) -> list[Generator] | None:
    """Load an ISO's fleet from the committed EIA-860 generator parquet.

    The parquet holds real generators for all seven wholesale markets; rows
    are filtered to the ISO via their ``balancing_authority_code``. Returns
    ``None`` when the parquet is missing or yields no thermal generators,
    so the caller can fall through to the synthetic fleet.
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


def load_fleet_from_csv(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
) -> list[Generator]:
    """Load an ISO's thermal generation fleet.

    Resolves the fleet from the first available source:

    1. ``generators_{iso}.csv`` in the EIA-860 directory (per-ISO override);
    2. the committed real EIA-860 generator parquet
       (:data:`EIA_860_PARQUET_NAME`), filtered to the ISO;
    3. a deterministic synthetic fleet, as a last-resort fallback.

    Wind, solar and hydro are skipped (handled by ``renewables.py``).

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        iso_config: Topology configuration supplying zone load shares. If
            ``None``, it is fetched via :func:`get_iso_config` when the ISO
            is known; ISOs without a config get a single ISO-named zone.
        data_dir: Directory holding the EIA-860 data. Defaults to
            ``inputs/raw-data/eia-860``.

    Returns:
        The ISO's thermal fleet as a list of :class:`Generator` objects.
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
    if csv_path.exists():
        df = _normalize_columns(pd.read_csv(csv_path))
        generators = _rows_to_generators(df, iso, iso_config)
        logger.info(
            "Loaded %s fleet from EIA-860 CSV (%d generators)",
            iso,
            len(generators),
        )
        return generators

    from_parquet = _load_fleet_from_parquet(
        data_dir / EIA_860_PARQUET_NAME, iso, iso_config
    )
    if from_parquet is not None:
        return from_parquet

    logger.warning("EIA-860 not found — using synthetic fleet for %s", iso)
    return build_synthetic_fleet(iso, iso_config)


# ---------------------------------------------------------------------------
# Synthetic fleet generation (guaranteed fallback)
# ---------------------------------------------------------------------------

# Fixed RNG seed so the synthetic fleet is identical on every run.
_SYNTHETIC_SEED = 20260516

# ISO ordering used to derive a per-ISO RNG seed offset.
_ISO_ORDER = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP"]

# Per-ISO plant_id base, spaced 1000 apart to avoid cross-ISO collisions.
_PLANT_ID_BASE: dict[str, int] = {
    "ERCOT": 60000,
    "CAISO": 61000,
    "PJM": 62000,
    "MISO": 63000,
    "NYISO": 64000,
    "NEISO": 65000,
    "SPP": 66000,
}

# Operating-year ranges per (vintage kind, vintage label), chosen so the
# fleet loader bins each unit into the intended efficiency class.
_VINTAGE_YEARS: dict[tuple[str, str], tuple[int, int]] = {
    ("gas_cc", "new"): (2015, 2024),
    ("gas_cc", "mid"): (2005, 2014),
    ("gas_cc", "old"): (1990, 2004),
    ("gas_ct", "new"): (2010, 2023),
    ("gas_ct", "mid"): (2000, 2009),
    ("gas_ct", "old"): (1975, 1999),
    ("coal", "new"): (2000, 2012),
    ("coal", "mid"): (1985, 1999),
    ("coal", "old"): (1965, 1984),
}

# Category → (vintage kind, technology, energy source, prime mover).
_CATEGORY_DEFAULTS: dict[str, tuple[str, str, str, str]] = {
    "gas_cc": ("gas_cc", "Natural Gas Fired Combined Cycle", "NG", "CC"),
    "gas_ct": ("gas_ct", "Natural Gas Fired Combustion Turbine", "NG", "GT"),
    "coal": ("coal", "Conventional Steam Coal", "SUB", "ST"),
    "oil_ct": ("gas_ct", "Petroleum Liquids", "DFO", "GT"),
}

# Default vintage splits when a block does not specify its own.
_GAS_CC_SPLIT = {"new": 0.35, "mid": 0.45, "old": 0.20}
_GAS_CT_SPLIT = {"new": 0.25, "mid": 0.45, "old": 0.30}
_COAL_SPLIT = {"new": 0.25, "mid": 0.50, "old": 0.25}
_OIL_SPLIT = {"old": 1.0}
_DEFAULT_SPLITS = {
    "gas_cc": _GAS_CC_SPLIT,
    "gas_ct": _GAS_CT_SPLIT,
    "coal": _COAL_SPLIT,
    "oil_ct": _OIL_SPLIT,
}

# Real-world fleet composition per ISO. Capacities are approximate; non-LP
# ISOs (PJM/MISO/NYISO/NEISO/SPP) only need the fuel mix roughly right.
_FLEET_SPECS: dict[str, dict] = {
    "ERCOT": {
        "ba": "ERCO",
        "states": ["TX"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 58000, "n": 30,
             "splits": {"new": 0.40, "mid": 0.40, "old": 0.20}},
            {"category": "gas_ct", "total_mw": 22000, "n": 30,
             "splits": {"new": 0.30, "mid": 0.40, "old": 0.30}},
            {"category": "coal", "total_mw": 14000, "n": 10,
             "splits": {"new": 0.20, "mid": 0.50, "old": 0.30},
             "retire": (2028, 2035)},
        ],
        "nuclear": [
            {"name": "Comanche Peak", "states": ["TX"], "units": 2,
             "unit_mw": 1200, "online": 1990},
            {"name": "South Texas Project", "states": ["TX"], "units": 2,
             "unit_mw": 1350, "online": 1988},
        ],
    },
    "CAISO": {
        "ba": "CISO",
        "states": ["CA"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 24000, "n": 20},
            {"category": "gas_ct", "total_mw": 11000, "n": 15},
        ],
        "nuclear": [
            {"name": "Diablo Canyon", "states": ["CA"], "units": 2,
             "unit_mw": 1150, "online": 1985},
        ],
    },
    "PJM": {
        "ba": "PJM",
        "states": ["PA", "NJ", "MD", "VA", "OH", "WV", "IL", "IN", "DE"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 75000, "n": 40},
            {"category": "gas_ct", "total_mw": 35000, "n": 40},
            {"category": "coal", "total_mw": 40000, "n": 25,
             "retire": (2028, 2038)},
        ],
        "nuclear": [
            {"name": "PJM Nuclear", "states": ["PA", "NJ", "IL", "MD", "VA"],
             "units": 18, "unit_mw": 1833, "online": 1980},
        ],
    },
    "MISO": {
        "ba": "MISO",
        "states": ["IL", "MN", "MI", "WI", "IN", "MO", "IA", "AR", "LA",
                   "MS", "ND", "SD"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 55000, "n": 30},
            {"category": "gas_ct", "total_mw": 30000, "n": 35},
            {"category": "coal", "total_mw": 45000, "n": 30,
             "retire": (2028, 2040)},
        ],
        "nuclear": [
            {"name": "MISO Nuclear", "states": ["IL", "MN", "MI", "WI"],
             "units": 10, "unit_mw": 1300, "online": 1980},
        ],
    },
    "NYISO": {
        "ba": "NYIS",
        "states": ["NY"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 15000, "n": 12},
            {"category": "gas_ct", "total_mw": 10000, "n": 15},
            {"category": "coal", "total_mw": 800, "n": 2,
             "splits": {"old": 1.0}, "retire": (2028, 2030)},
        ],
        "nuclear": [
            {"name": "NYISO Nuclear", "states": ["NY"], "units": 3,
             "unit_mw": 1800, "online": 1985},
        ],
    },
    "NEISO": {
        "ba": "ISNE",
        "states": ["CT", "MA", "ME", "NH", "RI", "VT"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 14000, "n": 10},
            {"category": "gas_ct", "total_mw": 5000, "n": 10},
            {"category": "oil_ct", "total_mw": 5000, "n": 10},
            {"category": "coal", "total_mw": 1000, "n": 2,
             "splits": {"old": 1.0}, "retire": (2028, 2030)},
        ],
        "nuclear": [
            {"name": "Millstone", "states": ["CT"], "units": 2,
             "unit_mw": 1100, "online": 1986},
            {"name": "Seabrook", "states": ["NH"], "units": 1,
             "unit_mw": 1200, "online": 1990},
        ],
    },
    "SPP": {
        "ba": "SWPP",
        "states": ["KS", "OK", "NE", "SD", "ND", "MO", "AR", "NM", "MN"],
        "thermal": [
            {"category": "gas_cc", "total_mw": 30000, "n": 20},
            {"category": "gas_ct", "total_mw": 20000, "n": 25},
            {"category": "coal", "total_mw": 20000, "n": 15,
             "retire": (2030, 2040)},
        ],
        "nuclear": [
            {"name": "Wolf Creek", "states": ["KS"], "units": 1,
             "unit_mw": 1200, "online": 1985},
            {"name": "Grand Gulf", "states": ["MS"], "units": 1,
             "unit_mw": 1200, "online": 1985},
        ],
    },
}

# Canonical CSV column order for synthetic fleet files.
SYNTHETIC_CSV_COLUMNS = [
    "plant_id", "generator_id", "plant_name", "state",
    "balancing_authority_code", "technology", "energy_source", "prime_mover",
    "nameplate_capacity_mw", "net_summer_capacity_mw", "operating_year",
    "planned_retirement_year", "status",
]


def _expand_vintages(splits: dict[str, float], n: int) -> list[str]:
    """Return a list of ``n`` vintage labels matching the given fractions."""
    labels: list[str] = []
    for label, fraction in splits.items():
        labels.extend([label] * round(fraction * n))
    dominant = max(splits, key=splits.get)
    while len(labels) < n:
        labels.append(dominant)
    return labels[:n]


def _gen_thermal_block(
    block: dict, ba: str, states: list[str], plant_id: int, rng: random.Random
) -> tuple[list[dict], int]:
    """Generate the raw CSV rows for one thermal block.

    Returns the rows and the next free plant_id.
    """
    kind, technology, energy_source, prime_mover = _CATEGORY_DEFAULTS[
        block["category"]
    ]
    n = block["n"]
    total_mw = block["total_mw"]
    splits = block.get("splits", _DEFAULT_SPLITS[block["category"]])
    retire = block.get("retire")

    # Vary unit sizes, then rescale so the block hits its total capacity.
    weights = [rng.uniform(0.65, 1.35) for _ in range(n)]
    weight_sum = sum(weights)
    caps = [total_mw * w / weight_sum for w in weights]

    labels = _expand_vintages(splits, n)
    rng.shuffle(labels)
    old_positions = [i for i, label in enumerate(labels) if label == "old"]

    rows: list[dict] = []
    for i in range(n):
        label = labels[i]
        year_lo, year_hi = _VINTAGE_YEARS[(kind, label)]
        operating_year = rng.randint(year_lo, year_hi)

        retirement = ""
        if retire is not None and label == "old":
            r_lo, r_hi = retire
            k = old_positions.index(i)
            span = max(len(old_positions) - 1, 1)
            retirement = round(r_lo + (r_hi - r_lo) * k / span)

        nameplate = round(caps[i], 1)
        rows.append(
            {
                "plant_id": plant_id,
                "generator_id": "1",
                "plant_name": f"{ba} {block['category']} {i + 1}",
                "state": rng.choice(states),
                "balancing_authority_code": ba,
                "technology": technology,
                "energy_source": energy_source,
                "prime_mover": prime_mover,
                "nameplate_capacity_mw": nameplate,
                "net_summer_capacity_mw": round(nameplate * 0.95, 1),
                "operating_year": operating_year,
                "planned_retirement_year": retirement,
                "status": "OP",
            }
        )
        plant_id += 1
    return rows, plant_id


def build_synthetic_fleet_rows(iso: str) -> list[dict]:
    """Return deterministic raw CSV rows for an ISO's synthetic fleet.

    The rows use the same column schema as a real EIA-860 extract, so they
    can be written to a CSV or passed straight to the fleet loader.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.

    Returns:
        A list of row dicts with the columns in :data:`SYNTHETIC_CSV_COLUMNS`.
    """
    iso = iso.upper()
    spec = _FLEET_SPECS[iso]
    rng = random.Random(_SYNTHETIC_SEED + _ISO_ORDER.index(iso))

    ba = spec["ba"]
    states = spec["states"]
    plant_id = _PLANT_ID_BASE[iso]

    rows: list[dict] = []
    for block in spec["thermal"]:
        block_rows, plant_id = _gen_thermal_block(
            block, ba, states, plant_id, rng
        )
        rows.extend(block_rows)

    for plant in spec.get("nuclear", []):
        for unit in range(plant["units"]):
            rows.append(
                {
                    "plant_id": plant_id,
                    "generator_id": str(unit + 1),
                    "plant_name": plant["name"],
                    "state": rng.choice(plant["states"]),
                    "balancing_authority_code": ba,
                    "technology": "Nuclear",
                    "energy_source": "NUC",
                    "prime_mover": "ST",
                    "nameplate_capacity_mw": plant["unit_mw"],
                    "net_summer_capacity_mw": round(plant["unit_mw"] * 0.98, 1),
                    "operating_year": plant["online"],
                    "planned_retirement_year": "",
                    "status": "OP",
                }
            )
        plant_id += 1

    return rows


def build_synthetic_fleet(
    iso: str, iso_config: ISOConfig | None = None
) -> list[Generator]:
    """Build an ISO's thermal fleet from the deterministic synthetic spec.

    Used as the fallback when no EIA-860 CSV is available.

    Args:
        iso: ISO identifier, e.g. ``"ERCOT"``.
        iso_config: Topology configuration for zone assignment. If ``None``,
            it is fetched via :func:`get_iso_config` when the ISO is known.

    Returns:
        The synthetic thermal fleet as a list of :class:`Generator` objects.
    """
    iso = iso.upper()
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    df = _normalize_columns(pd.DataFrame(build_synthetic_fleet_rows(iso)))
    generators = _rows_to_generators(df, iso, iso_config)
    logger.warning(
        "Using synthetic fleet for %s (%d generators)", iso, len(generators)
    )
    return generators
