"""EIA-860 / eGRID fleet loaders, EIA-923 class scoring, and per-plant registries.

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd
import re

from functools import lru_cache
from market_sim.config.constants import (
    CO2_RATES,
    EFORD,
    FUEL_CO2_FACTOR_PER_MMBTU,
    HEAT_RATE_BINS,
    NOX_RATES,
    VOM,
)
from market_sim.config.iso_configs import (
    ISOConfig,
    get_iso_config,
)
from market_sim.config.paths import (
    PROCESSED_DIR,
    active_eia860_dir,
)
from market_sim.config.plant_taxonomy import (
    BIOMASS_ENERGY_SOURCES,
    OIL_ENERGY_SOURCES,
    classify_plant,
)
from market_sim.data.coal import _coal_class_for
from pathlib import Path
from market_sim.data.fleet.models import (
    BA_CODE_TO_ISO,
    BINNED_FLEET_COLUMNS,
    EIA860_OPERABLE_VINTAGE,
    EIA_860_MULTIFUEL_PARQUET_NAME,
    EIA_860_PARQUET_NAME,
    EIA_860_RETIRED_WINDOW_PARQUET_NAME,
    Generator,
    ISO_TO_BA_CODE,
    MIXED_FACILITY_STEAM_HR,
    _clean_fleet_year,
    _read_clean,
    _use_clean,
)
from market_sim.data.fleet.models import _pkg_ns

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")

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


# Tolerance above which a plant's fleet-loaded merchant-CC pmax sum is treated
# as an EIA-860 summer-capacity double-filing (component + block-total rows both
# counted, or a plant-total filed on one row with the loader nameplate-filling
# the NaN component rows). EIA-860's own schema defines summer capability <=
# nameplate, so a summed pmax above the summed nameplate is impossible for a
# clean record. 0.1% headroom absorbs benign rounding in the source sheet.
_CC_NAMEPLATE_GUARD_TOL = 1.001


@lru_cache(maxsize=None)
def _cc_demonstrated_peaks(iso: str) -> dict[int, float]:
    """Per-plant CAMPD demonstrated p999 peak (MW) from the ISO reconcile table.

    Reads ``campd_p999_mw`` out of ``cc_capacity_reconcile_<ISO>.csv`` (the
    measured artifact ``scripts/data/derive_cc_capacity_reconcile.py`` writes; rule
    13 — re-derives only on CAMPD vintage change, rule 23). Keyed by plant code.
    A missing table returns ``{}``. Every ISO reads only its own table (rule
    24). CT-only / incomplete-CEMS plants are excluded from the table by the
    derive, so a plant present here has a *complete* CEMS record and its peak is
    a trustworthy capability bound. Cached: the guard runs on every fleet build.
    """
    from market_sim.config.paths import cc_capacity_reconcile_path

    path = cc_capacity_reconcile_path(iso)
    if not path.exists():
        return {}
    table = pd.read_csv(path)
    if "campd_p999_mw" not in table.columns or "plant_code" not in table.columns:
        return {}
    peaks = pd.to_numeric(table["campd_p999_mw"], errors="coerce")
    codes = pd.to_numeric(table["plant_code"], errors="coerce")
    return {
        int(c): float(p)
        for c, p in zip(codes, peaks)
        if pd.notna(c) and pd.notna(p) and p > 0.0
    }


def _reconcile_cc_pmax_to_nameplate(
    records: list[dict], cc_nameplate_sum: dict[int, float], iso: str
) -> None:
    """Clip merchant-CC plants whose fleet pmax sum exceeds their trusted bound.

    Enforces the EIA-860 schema invariant *summer capability <= nameplate* on
    the **fleet-loaded** plant pmax sum, but never below a plant's *measured*
    capability. The trusted upper bound per CC_REGULAR plant is
    ``max(nameplate_sum, demonstrated_peak)`` where ``demonstrated_peak`` is the
    plant's CAMPD p999 from its ISO reconcile table (:func:`_cc_demonstrated_peaks`;
    absent for CT-only / no-clean-CEMS plants, so those clip to nameplate). Where
    a plant's summed ``pmax_mw`` (net-summer, or the loader's nameplate-fill of
    NaN component rows) exceeds that bound by more than
    :data:`_CC_NAMEPLATE_GUARD_TOL`, the excess is component/total double-filing;
    every one of the plant's CC_REGULAR ``pmax_mw`` values is scaled by
    ``bound / pmax_sum`` so the plant sum reconciles to the bound. Scaling is
    proportional, so the intensive base heat rate (a capacity-weighted mean) is
    preserved.

    Using ``max(nameplate, demonstrated_peak)`` fixes the rule-13 inversion the
    plain-nameplate clip caused: a plant whose real cold-weather CEMS peak sits
    *above* nameplate (New Covert 55297: nameplate 1176 MW, demonstrated 1192.4
    MW) was clipped to 1176, discarding 16 MW of measured capability that the
    reconcile table already records. The guard now keeps it — the demonstrated
    peak, where a *complete* CEMS record exists, is the authority; the nameplate
    is the fallback where it is not. CT-only plants (demonstrated peak
    understated, excluded from the table) still clip to nameplate: their peak is
    absent, so the bound is nameplate.

    Acts on the FLEET-LOADED sum, not the raw EIA-860 summer sum: the
    plant-total-on-one-row pattern (Keys 60302, Camden 10751) hides behind NaN
    component rows the loader nameplate-fills, so a raw summer-sum audit misses
    it — only the fleet pmax sum exposes every instance (diagnosis
    ``docs/DIAGNOSIS-pjm-july-cc-overrun-2026-07.md`` §3b, probe block 3 of
    ``scripts/probes/_pjm_cc_netgross_bases.py``). ISO-agnostic in mechanism
    (the corruption lives in the shared EIA-860 loader; each ISO reads only its
    own peak table — rule 24). Mutates ``records`` in place; logs one warning per
    reconciled plant naming it and the MW removed.

    This is a data-integrity validator (an EIA-860 schema bound that never
    discards measured capability), not a tunable market feature — deliberately
    always-on and ISO-agnostic, so it is ungated. See A.4.3 of
    ``docs/handoffs/pjm-cc-capacity-reconcile-2026-07.md``.

    Rule-14/15 basis: the clipped figure regenerates for any forward EIA-860
    vintage and CAMPD peak and responds to re-rates — a reproducible physical
    bound, not a residual-tuned value.
    """
    demonstrated_peak = _pkg_ns()._cc_demonstrated_peaks(iso)
    cc_pmax: dict[int, float] = {}
    for rec in records:
        if rec["plant_group"] == "CC_REGULAR":
            code = int(rec["plant_code"])
            cc_pmax[code] = cc_pmax.get(code, 0.0) + float(rec["pmax_mw"])
    for code, pmax_sum in cc_pmax.items():
        nameplate_sum = cc_nameplate_sum.get(code, 0.0)
        if nameplate_sum <= 0.0:
            continue
        # Never clip below the plant's demonstrated CAMPD capability (rule 13):
        # the trusted bound is max(nameplate, demonstrated_peak). Only plants
        # over-rated beyond this — genuine double-file phantom — are clipped.
        bound = max(nameplate_sum, demonstrated_peak.get(code, 0.0))
        if pmax_sum <= bound * _CC_NAMEPLATE_GUARD_TOL:
            continue
        scale = bound / pmax_sum
        for rec in records:
            if rec["plant_group"] == "CC_REGULAR" and int(rec["plant_code"]) == code:
                rec["pmax_mw"] = float(rec["pmax_mw"]) * scale
        bound_kind = (
            "demonstrated peak" if bound > nameplate_sum + 1e-6 else "nameplate"
        )
        logger.warning(
            "%s: CC plant %d fleet pmax sum %.1f MW exceeds trusted bound "
            "%.1f MW (%s; corrupt summer-capacity rows) — reconciled "
            "(%.1f MW removed)",
            iso,
            code,
            pmax_sum,
            bound,
            bound_kind,
            pmax_sum - bound,
        )


def _rows_to_generators(
    df: pd.DataFrame,
    iso: str,
    iso_config: ISOConfig | None,
    apply_cc_summer_guard: bool = True,
) -> list[Generator]:
    """Convert a normalized generator DataFrame into :class:`Generator` objects.

    Rows are filtered to operating units, mapped to a model fuel type
    (skipping wind/solar/hydro), assigned an efficiency bin by vintage, and
    given heat rate, emission, VOM and outage parameters from
    ``config/constants.py``.

    ``apply_cc_summer_guard`` gates the always-on merchant-CC summer-capacity
    guard (:func:`_reconcile_cc_pmax_to_nameplate`). It is True everywhere in
    the model; the CC demonstrated-peak derive
    (:func:`scripts.data.derive_cc_capacity_reconcile._model_cc_capacity`) passes
    False so it measures the *raw* fleet capacity the guard clips — the guard
    reads the derive's own table, so guarding the derive's input would make the
    demonstrated-peak table self-referential (a plant restored to its peak would
    then read as "at capacity" and drop from the next re-derive).
    """
    if "status" in df.columns:
        status = df["status"].astype(str).str.strip().str.upper()
        df = df[status == "OP"]

    records: list[dict] = []
    # Per-plant EIA-860 nameplate sum over merchant-CC generators, for the
    # summer-capacity consistency guard applied after the row loop.
    cc_nameplate_sum: dict[int, float] = {}
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

        record = {
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
        records.append(record)
        # Accumulate the per-plant EIA-860 nameplate sum for the merchant-CC
        # consistency guard below. Keyed on plant_code, summed over the same
        # CC_REGULAR generators whose fleet-loaded pmax the guard reconciles.
        if group == "CC_REGULAR":
            nameplate = _to_float(data.get("nameplate_capacity_mw")) or 0.0
            cc_nameplate_sum[plant_code] = (
                cc_nameplate_sum.get(plant_code, 0.0) + nameplate
            )

    if apply_cc_summer_guard:
        _reconcile_cc_pmax_to_nameplate(records, cc_nameplate_sum, iso)
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
    _correct_chp_steam_credit_hr,
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
    apply_cc_summer_guard: bool = True,
) -> list[Generator] | None:
    """Load an ISO's fleet from the committed EIA-860 generator parquet.

    The parquet holds real generators for all seven wholesale markets; rows
    are filtered to the ISO via their ``balancing_authority_code``. Returns
    ``None`` when the parquet is missing or yields no thermal generators.
    ``apply_cc_summer_guard`` is forwarded to :func:`_rows_to_generators`.
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

    generators = _rows_to_generators(
        df, iso, iso_config, apply_cc_summer_guard=apply_cc_summer_guard
    )
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
    apply_cc_summer_guard: bool = True,
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
    generators = _rows_to_generators(
        normalized, iso, iso_config, apply_cc_summer_guard=apply_cc_summer_guard
    )
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
    apply_cc_summer_guard: bool = True,
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
        apply_cc_summer_guard: When False, skip the merchant-CC summer-capacity
            guard (:func:`_reconcile_cc_pmax_to_nameplate`). The model always
            leaves this True; only the CC demonstrated-peak derive passes False
            (it must see the raw, un-guarded fleet capacity — see
            :func:`_rows_to_generators`).

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
        generators = _rows_to_generators(
            df, iso, iso_config, apply_cc_summer_guard=apply_cc_summer_guard
        )
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
        from_clean = _load_fleet_from_clean(
            iso, iso_config, data_dir, year, apply_cc_summer_guard=apply_cc_summer_guard
        )
        if from_clean is None:
            raise FileNotFoundError(
                f"No clean fleet generators for {iso} "
                f"(vintage {_clean_fleet_year(data_dir)}); regenerate with "
                "`python scripts/regenerate_clean.py fleet`"
            )
        return from_clean
    else:
        parquet_path = data_dir / EIA_860_PARQUET_NAME
        from_parquet = _load_fleet_from_parquet(
            parquet_path,
            iso,
            iso_config,
            year,
            apply_cc_summer_guard=apply_cc_summer_guard,
        )
        if from_parquet is None:
            raise FileNotFoundError(
                f"No EIA-860 data for {iso}: expected a per-ISO override "
                f"CSV at {csv_path} or the generator parquet at "
                f"{parquet_path}"
            )
        generators = from_parquet
        source = parquet_path

    _correct_mixed_facility_steam_hr(generators)
    _correct_chp_steam_credit_hr(generators, iso)
    _pkg_ns()._cache_binned_fleet(iso, generators, source)
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


def load_mothballed_but_operating(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
    year: int | None = None,
) -> list[Generator]:
    """Re-carry OA (mothballed) units that were OP in the year-matched vintage.

    The Cottonwood lane (``docs/handoffs/miso-cc-vintage-undercarry-plan-
    2026-07.md`` §5/§7). The canonical operable snapshot is a single recent
    vintage; :func:`_rows_to_generators` keeps ``status == "OP"`` only, so a
    unit that snapshot marks OA (out of service — a mothball, not a
    retirement) is absent from *every* modeled year, even years it
    demonstrably ran. The within-window retiree channel
    (:func:`load_retired_within_window`) cannot catch this either: an OA unit
    never appears on the Retired-and-Canceled sheet, and that channel emits
    whole-plant exits only, while a mothball can be partial (Cottonwood
    55358: 4 of 8 units OA in the 2025ER snapshot, 576 MW, with CAMPD showing
    the OA CTs running 88-91% of 2023 hours).

    The re-carry trigger is the **vintage-status oracle** — the unit is
    injected for backcast solve ``year`` iff it is OP in the year-matched
    EIA-860 vintage (``vintage_<year>/``). That is EIA's own contemporaneous
    status: a unit truly idle in the solve year is OA in its own vintage too
    and stays dropped, so OA status alone never re-carries capacity (the
    rule-13 admissibility hinge — charter §4). Zero fitted parameters. The
    qualifying units are built **from the vintage rows** (year-matched
    net-summer capacity and attributes — the same record the oracle reads),
    per-unit, so a partial mothball leaves the surviving OP units (already
    loaded from the snapshot) untouched and no unit is double-carried.

    **Backcast-mode only**, gated on ``ScenarioConfig.carry_operating_
    mothballs`` (default off) at the call site. Solve years with no committed
    ``vintage_<year>/`` (2025 — the canonical snapshot IS the 2025 Early
    Release) carry nothing: the accepted 2025 under-carry (charter §10 owner
    default, 2026-07-16). Forward story (rule 12): a unit OP in its most
    recent vintage is physically available and would be carried forward
    until a real exit (economic screen / confirmed-retirement registry)
    removes it; per the same owner default the forecast path is deliberately
    NOT wired — a forecast keeps the canonical snapshot's contemporaneous OA
    judgment.

    Under an active ``eia860_vintage_year`` switch this channel self-
    neutralizes: the snapshot read here IS the vintage file, whose OA units
    are OA in the oracle file too, so nothing qualifies (no double-count —
    the vintage fleet already carries its own OP units natively).

    Returns an empty list when ``year`` is ``None``, either parquet is
    absent, or nothing qualifies.
    """
    iso = iso.upper()
    if year is None:
        return []
    data_dir = active_eia860_dir() if data_dir is None else Path(data_dir)
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    snap_path = data_dir / EIA_860_PARQUET_NAME
    vintage_path = _pkg_ns().EIA_860_DIR / f"vintage_{int(year)}" / EIA_860_PARQUET_NAME
    if not snap_path.exists() or not vintage_path.exists():
        return []

    snap = _normalize_columns(pd.read_parquet(snap_path))
    if "status" not in snap.columns:
        return []
    ba_code = ISO_TO_BA_CODE.get(iso)
    if ba_code is not None and "balancing_authority_code" in snap.columns:
        ba = snap["balancing_authority_code"].astype(str).str.strip()
        snap = snap[ba == ba_code]
    status = snap["status"].astype(str).str.strip().str.upper()
    # OA only (out of service, expected to return — the mothball status the
    # charter scopes this channel to). OS/SB/retired statuses are deliberately
    # out of scope: extending the channel needs its own probe.
    oa = snap[status == "OA"]
    if oa.empty:
        return []

    def _unit_keys(df: pd.DataFrame) -> list[tuple[int, str]]:
        codes = pd.to_numeric(df["plant_id"], errors="coerce").fillna(0)
        gids = df["generator_id"].astype(str).str.strip()
        return [(int(c), g) for c, g in zip(codes, gids)]

    vint = _normalize_columns(pd.read_parquet(vintage_path))
    if "status" not in vint.columns:
        return []
    if ba_code is not None and "balancing_authority_code" in vint.columns:
        ba = vint["balancing_authority_code"].astype(str).str.strip()
        vint = vint[ba == ba_code]
    vstatus = vint["status"].astype(str).str.strip().str.upper()
    vint = vint[vstatus == "OP"]

    oa_keys = set(_unit_keys(oa))
    carried = vint[[k in oa_keys for k in _unit_keys(vint)]]
    if carried.empty:
        return []

    carried = carried.copy()
    # Plant-level CHP flag, exactly as the operable/retiree loaders join it
    # (that year's EIA-860 designation when the per-year lookup exists).
    carried["chp"] = carried["plant_id"].map(_chp_by_plant(data_dir, year)).fillna("N")
    generators = _rows_to_generators(carried, iso, iso_config)
    if generators:
        logger.info(
            "re-carried %d mothballed-but-operating units for %s %d "
            "(%.0f MW; OA in the snapshot, OP in vintage_%d; plants %s)",
            len(generators),
            iso,
            year,
            sum(g.pmax_mw for g in generators),
            year,
            sorted({int(g.plant_code) for g in generators}),
        )
    return generators


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
    mixed = _pkg_ns().mixed_fossil_plants(year)
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
# available capacity. See scripts/data/derive_cc_committed_pct.py and
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


@lru_cache(maxsize=1)
def _eia860_plant_sector() -> dict[int, int]:
    """Return ``{plant_code: EIA-860 Sector number}`` from the plant table."""
    path = active_eia860_dir() / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Sector"])
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


@lru_cache(maxsize=1)
def eia860_regulated_plants() -> frozenset[int]:
    """Return the plant codes whose EIA-860 ``Regulatory Status`` is ``RE``.

    The EIA-860 plant table carries a two-value ``Regulatory Status`` flag —
    ``RE`` (the operator's rates are regulated / cost-of-service recovered)
    vs ``NR`` (non-regulated merchant/IPP). This is the measured
    regulated-vs-merchant conduct split the MISO SOM Table 7 reports its
    coal self-commitment statistics on (``coal_committed_takeorpay_regulated``);
    plants absent from the table (or with a null flag) are conservatively
    treated as non-regulated (no committed-band discount).
    """
    path = active_eia860_dir() / "eia860_plant.parquet"
    if not path.exists():
        return frozenset()
    df = pd.read_parquet(path, columns=["Plant Code", "Regulatory Status"])
    df = df.dropna(subset=["Plant Code", "Regulatory Status"])
    return frozenset(
        int(c)
        for c, s in zip(df["Plant Code"], df["Regulatory Status"])
        if str(s).strip().upper() == "RE"
    )


# EIA-860 utility Entity Type codes whose generation ownership is recovered
# at cost of service (rate base or member/public rates): Investor-owned,
# Municipal, Cooperative, Political subdivision, State, Federal. Q (IPP) and
# the IND/COM self-suppliers are excluded — their offtake is not
# rate-recovered, so the SOM's merchant conduct (economic offers) applies.
_COST_OF_SERVICE_ENTITY_TYPES: frozenset[str] = frozenset(
    {"I", "M", "C", "P", "S", "F"}
)


@lru_cache(maxsize=1)
def eia860_costofservice_majority_plants() -> frozenset[int]:
    """Plant codes majority-owned by cost-of-service entities (Schedule 4).

    The ``Regulatory Status`` flag classifies the OPERATOR, so a plant whose
    output is take-or-pay committed to municipal/cooperative/IOU owners reads
    ``NR`` when a project company operates it (Prairie State: ~95% owned by
    eight municipal JAAs/co-ops, EIA-860 Schedule 4). Conduct-wise those
    owners recover the plant at cost and self-commit it like regulated fleet
    (the 2024 SOM Table 7 merchant rows themselves show 25% of "merchant"
    starts flagged must-run). This helper measures that leg: per plant, the
    summed ``Percent Owned`` of Schedule-4 owners whose EIA-860 utility
    ``Entity Type`` is cost-of-service (I/M/C/P/S/F); plants absent from
    Schedule 4 are 100% operator-owned and use the operator's entity type.
    Returns plants whose cost-of-service share exceeds 0.5.
    """
    d = active_eia860_dir()
    own_path = d / "eia860_owner.parquet"
    util_path = d / "eia860_utility.parquet"
    plant_path = d / "eia860_plant.parquet"
    if not (own_path.exists() and util_path.exists() and plant_path.exists()):
        return frozenset()
    util = pd.read_parquet(util_path, columns=["Utility ID", "Entity Type"])
    etype = {
        int(u): str(e).strip().upper()
        for u, e in zip(util["Utility ID"], util["Entity Type"])
        if pd.notna(u) and pd.notna(e)
    }

    own = pd.read_parquet(
        own_path,
        columns=["Plant Code", "Generator ID", "Ownership ID", "Percent Owned"],
    ).dropna(subset=["Plant Code", "Ownership ID"])
    own["pct"] = pd.to_numeric(own["Percent Owned"], errors="coerce")
    own = own.dropna(subset=["pct"])
    # Per (plant, owner): mean across that plant's generators (joint-owned
    # coal plants list identical shares per unit), then sum the
    # cost-of-service owners' shares per plant.
    per_owner = own.groupby(["Plant Code", "Ownership ID"])["pct"].mean().reset_index()
    per_owner["cos"] = per_owner["Ownership ID"].map(
        lambda u: etype.get(int(u), "") in _COST_OF_SERVICE_ENTITY_TYPES
    )
    cos_share = per_owner[per_owner["cos"]].groupby("Plant Code")["pct"].sum()
    majority = {int(p) for p, s in cos_share.items() if float(s) > 0.5}

    # Plants absent from Schedule 4: 100% operator-owned (ownership.py's
    # sparse-schedule rule) — classify by the operator's entity type.
    plants = pd.read_parquet(plant_path, columns=["Plant Code", "Utility ID"]).dropna()
    sched4 = set(int(p) for p in own["Plant Code"].unique())
    for p, u in zip(plants["Plant Code"], plants["Utility ID"]):
        p = int(p)
        if p in sched4:
            continue
        if etype.get(int(u), "") in _COST_OF_SERVICE_ENTITY_TYPES:
            majority.add(p)
    return frozenset(majority)


@lru_cache(maxsize=1)
def eia860_selfcommit_scope_plants() -> frozenset[int]:
    """The ``coal_committed_takeorpay_regulated`` scope set.

    Union of the two measured cost-of-service legs: EIA-860 ``Regulatory
    Status`` RE operators (:func:`eia860_regulated_plants`) and plants
    majority-owned by cost-of-service entities
    (:func:`eia860_costofservice_majority_plants`). See
    docs/handoffs/miso-coal-conduct-design-2026-07.md §4 (the pre-declared
    V1b refinement, engaged when the RE-only probe broke the 2023 COAL_BIT
    band on the Prairie State reversion).
    """
    return eia860_regulated_plants() | eia860_costofservice_majority_plants()


# Per-bin forced availability derates by year, for confirmed unit losses
# that the age-based THERMAL_AVAILABILITY model cannot anticipate (turbine
# fires, boiler explosions, etc.). Keyed by ``Bin_Label`` and run year, the
# value is a flat multiplier on the bin's availability for the whole year.
BIN_FORCED_DERATE_BY_YEAR: dict[str, dict[int, float]] = {
    # Martin Lake -- turbine fire and boiler explosion took unit 1 out of
    # commission for 2025 (1 of 3 units, ~33% nameplate loss).
    "N_COAL4": {2025: 0.67},
    # V H Braunig -- CPS Energy retired ST units 1 (225 MW) and 2 (252 MW)
    # in early 2025 (March). Handled via confirmed-exit registry injection
    # (data/raw/confirmed-retirements/ercot.csv, plant 3612) with
    # month-level precision: (3/12 * 1.0) + (9/12 * 661/1138) = 0.686.
    # Removed from hardcode 2026-07-06 per rule 24 (no off-registry tuning).
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
