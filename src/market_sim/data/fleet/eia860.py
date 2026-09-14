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
    EGRID_CC_HR_PHYSICAL_CEILING,
    EGRID_COLOCATION_RADIUS_KM,
    EGRID_CT_HR_PHYSICAL_FLOOR,
    EGRID_UNIT_VINTAGE_TOL_YEARS,
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
    CC_STEAM_PART_PRIME_MOVER,
    CC_STEAM_PART_RECLASS_ISOS,
    CC_STEAM_PART_REPAIR_ISOS,
    OIL_ENERGY_SOURCES,
    classify_plant,
)
from market_sim.data.coal import _coal_class_for
from market_sim.data.disk_memo import memoized_mapping
from market_sim.data.egrid_sheets import read_egrid_sheet
from pathlib import Path
from market_sim.data.fleet.models import (
    BA_CODE_TO_ISO,
    BINNED_FLEET_COLUMNS,
    EIA_860_MULTIFUEL_PARQUET_NAME,
    EIA_860_PARQUET_NAME,
    EIA_860_RETIRED_WINDOW_PARQUET_NAME,
    Generator,
    MIXED_FACILITY_STEAM_HR,
    ba_codes,
    _clean_fleet_year,
    _read_clean,
    _use_clean,
    egrid_prime_mover_family,
    operable_vintage_year,
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

    Returns one of ``gas_cc``, ``gas_ct``, ``gas_st``, ``coal``, ``nuclear``,
    ``oil`` or ``biomass``, or ``None`` for wind, solar, hydro and other
    non-thermal resources, which are handled elsewhere.

    Compressed-air energy storage (EIA-860 technology ``Natural Gas with
    Compressed Air Storage``, prime mover ``CE``) deliberately falls through
    the ``NG`` branch to ``gas_ct``: it burns gas on discharge and the model
    has no CAES class. The one such unit in the registered footprints is
    McIntosh unit 1 (SOCO, EIA plant 7063; 110.0 MW nameplate but a **25 MW
    summer/winter rating**, a 77 % derate the source itself states), and the
    loader's ``pmax = net summer capacity`` rule therefore carries it at
    25 MW — owner card S7 (SOCO desk r#3, 2026-09-13: "map to a gas CT at the
    25 MW rating"). Its energy-storage-schedule twin is skipped by
    ``model.storage.load_eia860_storage`` so the unit is represented once.
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
        # Legacy natural-gas steam boilers: EIA-860 prime mover ``ST``
        # (Schedule 3 "Prime Mover" code, steam turbine) — the dedicated
        # ``gas_st`` fuel the CAMPD bin path already carries
        # (BIN_GROUP_TO_FUEL), not a combustion turbine. The string branch
        # mirrors the combined-cycle line above for rows that carry only the
        # EIA-860 "Technology" description. Taxonomy fix D-25 (sitting
        # Addendum Y.4, 2026-08-06; seam: FFR-7A §4.1).
        if "steam turbine" in tech or mover == "ST":
            return "gas_st"
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


def _egrid_boundary_hr_repairs() -> dict[int, float]:
    """Boundary-reconciled plant heat rates (MMBtu/MWh) for eGRID double-counts.

    eGRID keys its plant sheet (PLNT23) on ORISPL, but CEMS reports co-located
    plants sharing a stack under ONE facilityId. Where that happens the plant
    row's heat input ``PLHTIAN`` covers the whole CEMS facility while its net
    generation ``PLNGENAN`` covers only the one EIA plant, so ``PLHTRT`` is a
    ratio of two different boundaries and the co-located sibling's fuel is
    double-counted. **Riverside Energy Center (55641)** is the live instance:
    ``PLHTIAN`` = 53,017,211 MMBtu is byte-identical to the sum of ``heatInput``
    over all four units of CEMS facility 55641 (both the 2004 Riverside block
    and the 2020 West Riverside block, EIA plant 64020, 454 m away), while
    ``PLNGENAN`` = 3,543,044 MWh is the 674.9 MW Riverside plant alone. The
    published 14,963.7 Btu/kWh is ~2x any combined cycle, pricing the plant near
    $45/MWh against ~$20/MWh for its class — above most MISO coal — so the LP
    never commits it (model CF 0.01 against an actual 0.60).

    Returns ``{plant_id: reconciled_heat_rate}``, empty when the eGRID workbook
    is absent. A plant is repaired only when ALL FOUR hold:

    1. ``PLHTRT`` exceeds :data:`EGRID_CC_HR_PHYSICAL_CEILING` — a combined cycle
       raises steam from its own topping turbine's exhaust, so it cannot be less
       efficient than a bare simple-cycle GT of the same era. A physics bound off
       an existing cited constant, not a fitted multiple of the class mean.
    2. A co-located sibling plant (within :data:`EGRID_COLOCATION_RADIUS_KM`)
       independently reports its own ``PLHTIAN`` > 0, so excluding the duplicated
       units loses no fuel from the system.
    3. The plant carries UNT23 units whose commissioning vintage is within
       :data:`EGRID_UNIT_VINTAGE_TOL_YEARS` of a *sibling* EIA-860 generator
       vintage and of NONE of its own — eGRID dates 55641's CT-03/CT-04 to 2019
       while all three of its EIA-860 generators are 2004. Excluding them must
       leave at least one unit with positive heat input.
    4. The recomputed rate lands at or below the same ceiling. Self-validating:
       the repair is accepted only because it resolves an impossibility.

    Condition 4 is what makes this safe. Without it the detector also fires on
    Devon 544 (876.6 -> 340.1 MMBtu/MWh, garbage either way and already dropped
    by the curation script's 3,000-30,000 Btu/kWh window) and King City 10294
    (7.855 -> 8.998, a *degradation* of an already-plausible value). Both are
    correctly rejected — Devon by condition 4, King City by condition 1. Across
    the six ISOs of 2026-07 the accepted set was exactly ``{55641: 6.880}``;
    NWPP's registration (2026-09-14, lane NWPP-20) put a second provable
    instance in scan range, **Coyote Springs (7350)**: CEMS facility 7350
    stacks the co-located Coyote Springs II (7931, BPAT, 6 m away, its own
    ``PLHTIAN`` > 0), the published 13,795.8 Btu/kWh is the whole-facility heat
    input over the PGE plant's generation alone, and the reconciled 6.918 sits
    beside the sibling's own 6.894. The accepted set is now
    ``{7350: 6.918, 55641: 6.880}`` (pinned by the curation test).

    A *general* form of this repair — drop every UNT23 unit whose vintage matches
    no EIA-860 generator at its plant — was sized and refused: it touches 47
    plants and destroys 25 (French Island -> 0.011, Ivanpah 3 -> 0.873), because
    EIA-860's operable snapshot omits retired units CEMS still reports, so
    removing their heat input guts the numerator while ``PLNGENAN`` stays the
    whole-plant total.

    Rule posture: rule 11's named exception — measured data drawn on a different
    boundary than our representation, reconciled rather than replaced by a guess.
    Zero free parameters (the value is arithmetic on eGRID's own fields, never
    chosen) and no appeal to any model output, so rules 1/10 are not engaged.
    Rule 13/23 forward story: recomputed from whichever eGRID vintage is on disk,
    so a later release that fixes the 55641 attribution makes condition 1 stop
    firing and this a silent no-op.

    Thin resolver over :func:`_egrid_boundary_hr_repairs_for`, which carries the
    cache keyed on the two resolved source paths — so an ``eia860_vintage_year``
    switch (which repoints :func:`active_eia860_dir`) recomputes against that
    vintage's own generator table instead of serving a stale set.
    """
    from market_sim.config.paths import FLEET_DIR

    egrid_path = FLEET_DIR / "egrid2023_data_rev2.xlsx"
    eia_path = active_eia860_dir() / EIA_860_PARQUET_NAME
    if not egrid_path.exists() or not eia_path.exists():
        return {}
    return _egrid_boundary_hr_repairs_for(egrid_path, eia_path)


@lru_cache(maxsize=4)
def _egrid_boundary_hr_repairs_for(
    egrid_path: Path, eia_path: Path
) -> dict[int, float]:
    """Return the accepted repair set for one (eGRID, EIA-860) source pair.

    Cache-bearing resolver for :func:`_egrid_boundary_hr_repairs`; see that
    function for the four acceptance conditions and the rule posture. Keyed on
    the resolved paths so each EIA-860 vintage gets its own entry.

    Two caches, at two lifetimes. The ``lru_cache`` here holds the set for the
    life of the process; :func:`market_sim.data.disk_memo.memoized_mapping`
    holds it *across* processes, in a JSON memo named by a sha256 over both
    source files' bytes. The derivation below is a pure function of exactly
    those bytes and costs seconds of CPU (the per-plant ``operating_year``
    reduction and the co-location scan), paid afresh by every invocation in
    whichever year first loads a fleet — which is the year-1 ``data_prep``
    premium wall-clock item A-4 measures. A re-released eGRID workbook or a
    different EIA-860 vintage hashes differently, so the memo is
    self-invalidating and no flag arms it.

    The accepted set is logged here rather than only inside the derivation, so
    a boundary-reconciled plant is named on the memo-hit path too — the
    detailed per-plant justification is emitted by
    :func:`_egrid_boundary_hr_repairs_compute` on the miss that built the memo.
    """
    repairs = memoized_mapping(
        "egrid_boundary_hr_repairs",
        [egrid_path, eia_path],
        lambda: _egrid_boundary_hr_repairs_compute(egrid_path, eia_path),
        float,
    )
    if repairs:
        logger.warning(
            "eGRID boundary heat-rate reconciliation active for %d plant(s): %s",
            len(repairs),
            ", ".join(f"{code}->{hr:.3f}" for code, hr in sorted(repairs.items())),
        )
    return repairs


def _egrid_boundary_hr_repairs_compute(
    egrid_path: Path, eia_path: Path
) -> dict[int, float]:
    """Compute the accepted repair set for one (eGRID, EIA-860) source pair.

    The derivation itself, with no cache of its own — both caches live on
    :func:`_egrid_boundary_hr_repairs_for`, which is the only caller. Returns
    ``{}`` when either workbook/parquet does not carry the expected columns.

    The two eGRID sheets come through
    :func:`market_sim.data.egrid_sheets.read_egrid_sheet`, which serves them from
    a content-addressed parquet mirror beside the workbook after the first miss —
    the same frames, without openpyxl on the solve path (wall-clock item A-2).
    """
    try:
        plants = read_egrid_sheet(
            egrid_path,
            "PLNT23",
            ["ORISPL", "LAT", "LON", "PLHTIAN", "PLNGENAN", "PLHTRT"],
        )
        units = read_egrid_sheet(
            egrid_path,
            "UNT23",
            ["ORISPL", "HTIAN", "UNTYRONL"],
        )
        gens = pd.read_parquet(
            eia_path, columns=["plant_id", "technology", "operating_year", "status"]
        )
    except (ValueError, KeyError, OSError):  # unexpected workbook/parquet schema
        logger.warning(
            "eGRID boundary heat-rate reconciliation skipped: unreadable source"
        )
        return {}

    gens = gens[gens["status"].astype(str).str.strip().str.upper() == "OP"]
    vintages: dict[int, set[int]] = {
        int(code): {int(y) for y in grp.dropna()}
        for code, grp in gens.groupby("plant_id")["operating_year"]
        if pd.notna(code)
    }
    # Scoped to gas_cc, the one class with an airtight physical ceiling.
    cc_codes = {
        int(c)
        for c in gens.loc[
            gens["technology"].astype(str) == "Natural Gas Fired Combined Cycle",
            "plant_id",
        ].dropna()
    }
    plants = plants.dropna(subset=["ORISPL", "LAT", "LON"]).drop_duplicates("ORISPL")
    lat = plants["LAT"].to_numpy(dtype=float)
    lon = plants["LON"].to_numpy(dtype=float)
    oris = plants["ORISPL"].to_numpy(dtype="int64")
    htian = pd.to_numeric(plants["PLHTIAN"], errors="coerce").to_numpy(dtype=float)
    ngen = pd.to_numeric(plants["PLNGENAN"], errors="coerce").to_numpy(dtype=float)
    # eGRID publishes PLHTRT in Btu/kWh; the model works in MMBtu/MWh.
    phtrt = pd.to_numeric(plants["PLHTRT"], errors="coerce").to_numpy(dtype=float) / 1e3
    units = units.dropna(subset=["ORISPL"])
    units_by_plant = {int(c): grp for c, grp in units.groupby("ORISPL")}

    repairs: dict[int, float] = {}
    for i, code in enumerate(oris):
        code = int(code)
        own_vint = vintages.get(code)
        # (1) impossible for a combined cycle
        if (
            code not in cc_codes
            or not own_vint
            or not np.isfinite(phtrt[i])
            or phtrt[i] <= EGRID_CC_HR_PHYSICAL_CEILING
            or not np.isfinite(ngen[i])
            or ngen[i] <= 0.0
        ):
            continue
        own_units = units_by_plant.get(code)
        if own_units is None or own_units.empty:
            continue
        # Equirectangular separation is exact enough at 1 km / mid-latitudes.
        km = np.hypot(
            (lat - lat[i]) * 111.0,
            (lon - lon[i]) * 111.0 * np.cos(np.radians(lat[i])),
        )
        for j in np.nonzero(km < EGRID_COLOCATION_RADIUS_KM)[0]:
            sib = int(oris[j])
            sib_vint = vintages.get(sib)
            # (2) a co-located sibling that reports its own heat input
            if (
                sib == code
                or not sib_vint
                or not np.isfinite(htian[j])
                or htian[j] <= 0.0
            ):
                continue

            def _is_siblings(year: object) -> bool:
                if pd.isna(year):
                    return False
                y = int(year)  # type: ignore[arg-type]
                tol = EGRID_UNIT_VINTAGE_TOL_YEARS
                return any(abs(y - v) <= tol for v in sib_vint) and not any(
                    abs(y - v) <= tol for v in own_vint
                )

            dup = own_units["UNTYRONL"].map(_is_siblings)
            # (3) the plant carries units that are demonstrably the sibling's
            if not dup.any() or bool(dup.all()):
                continue
            kept = (
                pd.to_numeric(own_units.loc[~dup, "HTIAN"], errors="coerce")
                .fillna(0.0)
                .sum()
            )
            if kept <= 0.0:
                continue
            reconciled = float(kept) / float(ngen[i])
            # (4) the repair must resolve the impossibility
            if reconciled <= 0.0 or reconciled > EGRID_CC_HR_PHYSICAL_CEILING:
                continue
            repairs[code] = reconciled
            logger.warning(
                "eGRID plant %d heat rate %.3f MMBtu/MWh exceeds the combined-cycle "
                "physical ceiling %.3f (PLHTIAN spans co-located plant %d, %.0f m "
                "away, whose %d unit(s) eGRID double-counts) — reconciled to %.3f",
                code,
                phtrt[i],
                EGRID_CC_HR_PHYSICAL_CEILING,
                sib,
                km[j] * 1000.0,
                int(dup.sum()),
                reconciled,
            )
            break
    return repairs


def _apply_egrid_boundary_hr_repairs(df: pd.DataFrame) -> pd.DataFrame:
    """Overwrite ``heat_rate`` for plants with a boundary-reconciled eGRID rate.

    Applied to the normalized generator frame before it becomes
    :class:`Generator` objects, so every read path — the canonical snapshot, the
    per-year vintages and the mothball re-carry — picks the correction up from
    the one seam. A frame with no ``heat_rate``/``plant_id`` column, or no
    repaired plant in it, is returned unchanged. See
    :func:`_egrid_boundary_hr_repairs` for the four acceptance conditions.
    """
    if "heat_rate" not in df.columns or "plant_id" not in df.columns:
        return df
    repairs = _egrid_boundary_hr_repairs()
    if not repairs:
        return df
    codes = pd.to_numeric(df["plant_id"], errors="coerce")
    hit = codes.isin(repairs)
    if not hit.any():
        return df
    df = df.copy()
    df.loc[hit, "heat_rate"] = codes[hit].map(repairs).astype(float)
    return df


#: EIA-860 prime movers with no steam cycle: a simple-cycle gas turbine (``GT``)
#: and a reciprocating engine (``IC``). A plant whose operating rows are all of
#: these has no heat recovery anywhere on site, so its annual net heat rate
#: cannot sit below a bare turbine's — the predicate of
#: :func:`_apply_simple_cycle_hr_floor`. A combined-cycle part (``CT`` / ``CA``
#: / ``CS``) or a steam turbine (``ST``) anywhere at the plant makes it MIXED
#: and out of scope (its plant-blend rate is the ``egrid_family_heat_rates``
#: object, rule 19).
_SIMPLE_CYCLE_PRIME_MOVERS: frozenset[str] = frozenset({"GT", "IC"})


def _apply_simple_cycle_hr_floor(df: pd.DataFrame) -> pd.DataFrame:
    """Clamp a simple-cycle-only plant's eGRID heat rate to the physical floor.

    The mirror of :func:`_apply_egrid_boundary_hr_repairs` on the other side of
    the physics (SPP-46 R-2; owner ruling P19, 2026-09-08, repo-wide;
    ``docs/handoffs/PRECOMMIT-spp-49-2026-09-08.md`` §1.1 / §2.2). eGRID's
    plant-grain ``PLHTRT`` is ``PLHTIAN / PLNGENAN``; a plant whose every
    operating row is a simple-cycle prime mover (:data:`_SIMPLE_CYCLE_PRIME_MOVERS`)
    cannot convert fuel to net electricity at better than the best bare
    turbine, :data:`EGRID_CT_HR_PHYSICAL_FLOOR` (``HEAT_RATE_BINS["gas_ct"]["aero"]``,
    EIA Table 8). A rate below it is arithmetic on mismatched boundaries —
    Pioneer 57881 reads **3.43 MMBtu/MWh** on three GTs and twelve engines with
    EIA-923 net generation ~3x its CEMS gross load, and priced 763 MW of SPP
    peakers at ~$12/MWh (+5.0 TWh of 2024 CT over-run on one plant, FINDING-spp-46
    §0.1) — not measured efficiency.

    The reconciled value is the floor itself, ``max(heat_rate, floor)`` on the
    plant's rows: the smallest repair that resolves the impossibility (the CC
    ceiling's condition 4, applied at the bound). Treating the value as absent
    and falling to the vintage bin was considered and refused — it discards the
    measured information that the plant is efficient (a plausible 8.2 would
    become 10.5).

    A CONSTRUCTION, not a gate: the raw value has no reading under which it is
    the plant's efficiency, so no run wants it; the precedent form is the CC
    ceiling. Frame-level and unconditional, at the same seam as the boundary
    repair, so every fleet read path picks it up and every measured mechanism
    downstream keeps its precedence — ``egrid_family_heat_rates`` (frame, next),
    ``measured_ct_heat_rates`` (row loop) and the CHP measured rates still win
    over the clamped value where armed. A frame without ``heat_rate`` /
    ``plant_id`` / ``prime_mover`` columns, or with no flagged plant, is
    returned unchanged; the input is never mutated.

    **CHP plants are OUT of scope** (the one narrowing made after the
    PRECOMMIT, before any number was cited — FINDING-spp-49 §5): eGRID's
    ``PLHTRT`` at a combined-heat-and-power plant is STEAM-CREDITED (the useful
    thermal output's heat input is netted out of ``PLHTIAN``), so a sub-floor
    value there is not an impossibility but the published power-only
    convention, and the model already owns it — ``_correct_chp_steam_credit_hr``
    (the CAISO / PJM topping factor, which fires below 8.0) and
    ``measured_chp_heat_rates`` (``CHPCHTI`` added back). Clamping a CHP plant to
    9.0 first would pre-empt that chain (measured on the CAISO keeper: 81 CT_CHP
    rows / 631 MW landing at 9.9 instead of their 10.3–13.5 topping-corrected
    rates) — two mechanisms on one row, rule 19 [R-ONE-MECH]. A plant with any
    row flagged ``chp`` = ``Y`` is therefore left to that chain; a frame with no
    ``chp`` column (the raw parquet outside the loader) treats every plant as
    non-CHP, which every loader read path never does — each stamps ``chp``
    from ``_chp_by_plant`` before reaching this seam.

    Rule posture: rule 14's misalignment exception (measured data on a different
    boundary than our representation, reconciled rather than replaced by a
    guess); zero free parameters (an alias of an existing cited constant; no
    appeal to any model output, so rules 1 / 13 are not engaged); rule 23
    forward story: re-evaluated on whichever eGRID join and EIA-860 vintage the
    frame carries, so a later eGRID release that repairs the boundary makes this
    a silent no-op.
    """
    needed = {"heat_rate", "plant_id", "prime_mover"}
    if not needed.issubset(df.columns):
        return df
    hr = pd.to_numeric(df["heat_rate"], errors="coerce")
    codes = pd.to_numeric(df["plant_id"], errors="coerce")
    pm = df["prime_mover"].astype(str).str.strip().str.upper()
    simple = pm.isin(_SIMPLE_CYCLE_PRIME_MOVERS)
    # A plant is simple-cycle-only iff EVERY row of it in the frame is.
    all_simple = simple.groupby(codes).transform("all")
    if "chp" in df.columns:
        is_chp = df["chp"].astype(str).str.strip().str.upper().str.startswith("Y")
        any_chp = is_chp.groupby(codes).transform("any")
    else:
        any_chp = pd.Series(False, index=df.index)
    hit = (
        all_simple
        & ~any_chp
        & codes.notna()
        & hr.notna()
        & (hr < EGRID_CT_HR_PHYSICAL_FLOOR)
    )
    if not hit.any():
        return df
    df = df.copy()
    for code, grp in df.loc[hit].groupby(codes[hit]):
        logger.warning(
            "eGRID plant %d heat rate %.3f MMBtu/MWh is below the simple-cycle "
            "physical floor %.3f on a plant whose %d operating row(s) are all "
            "GT/IC — clamped to the floor (SPP-49)",
            int(code),
            float(hr[grp.index].iloc[0]),
            EGRID_CT_HR_PHYSICAL_FLOOR,
            int(len(grp)),
        )
    df.loc[hit, "heat_rate"] = EGRID_CT_HR_PHYSICAL_FLOOR
    return df


#: Plants whose carried pmax the CC guard CLIPPED off the published net-summer
#: basis onto ``max(nameplate, demonstrated_peak)``, per ISO — rewritten on
#: every fleet load by :func:`_reconcile_cc_pmax_to_nameplate`.
#:
#: Read by ``config.summer_derate_basis_aware`` (miso-148) to decide, per plant,
#: whether the flat ambient haircut may be suppressed. It must be the LOADER'S
#: OWN determination rather than a re-derivation from the raw sheet: the
#: plant-total-on-one-row pattern hides behind NaN component rows the loader
#: nameplate-fills, so a raw summer-sum audit MISSES corrupt plants (the
#: hazard :func:`_reconcile_cc_pmax_to_nameplate` documents, and which a
#: re-derived predicate walked straight into during miso-148).
_CC_PMAX_RECONCILED_PLANTS: dict[str, frozenset[int]] = {}


def cc_pmax_reconciled_plants(iso: str) -> frozenset[int]:
    """Plants the CC guard clipped off the net-summer basis for ``iso``.

    Empty before the ISO's fleet has been loaded in this process.
    """
    return _CC_PMAX_RECONCILED_PLANTS.get(iso.upper(), frozenset())


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
    reconciled: set[int] = set()
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
        reconciled.add(int(code))
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
    # Record the loader's OWN clip decision for this ISO (see
    # _CC_PMAX_RECONCILED_PLANTS): these plants are no longer carried on the
    # published net-summer basis, so a basis-aware consumer must keep the flat
    # ambient derate for them.
    _CC_PMAX_RECONCILED_PLANTS[iso.upper()] = frozenset(reconciled)


#: Plants whose eGRID prime-mover-FAMILY heat rates were applied on the last
#: fleet load of each ISO (``ScenarioConfig.egrid_family_heat_rates``). Read
#: by :func:`load_fleet_from_csv` so the hand-number channel
#: (:func:`_correct_mixed_facility_steam_hr`) skips them — one mechanism per
#: plant, never a stack (rule 19). Empty for every ISO while the flag is off.
_EGRID_FAMILY_COVERED_PLANTS: dict[str, frozenset[int]] = {}


def egrid_family_heat_rates_for(iso: str) -> dict[tuple[int, str], float]:
    """Load the committed eGRID prime-mover-family heat-rate artifact.

    ``{(plant_id, family): heat_rate}`` over the ``flag == "ok"`` rows of
    ``data/raw/_processed-legacy/egrid_family_heat_rates_<ISO>.csv``
    (``scripts/data/derive_egrid_family_heat_rates.py``): for a plant hosting
    two or more prime-mover families (a 1960s steam station beside a 2003
    combined cycle), each family's own Σ ``UNT.HTIAN`` ÷ Σ ``GEN.GENNTAN``
    from the SAME eGRID vintage the plant-grain join reads, so the family
    rate replaces the plant blend on the identical net-annual boundary.
    Families are :data:`~market_sim.data.fleet.models.EGRID_PRIME_MOVER_FAMILIES`.
    Empty when the ISO has no committed artifact — a no-op there by
    construction (rule 25: each ISO's lane derives its own).
    """
    from market_sim.config.paths import PROCESSED_DIR

    path = PROCESSED_DIR / f"egrid_family_heat_rates_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    need = {"plant_id", "family", "heat_rate_mmbtu_mwh", "flag"}
    if df.empty or not need.issubset(df.columns):
        return {}
    df = df[df["flag"].astype(str) == "ok"]
    return {
        (int(r.plant_id), str(r.family)): float(r.heat_rate_mmbtu_mwh)
        for r in df.itertuples()
        if float(r.heat_rate_mmbtu_mwh) > 0.0
    }


def _apply_egrid_family_heat_rates(
    df: pd.DataFrame, iso: str
) -> tuple[pd.DataFrame, frozenset[int]]:
    """Overwrite ``heat_rate`` with the family rate at covered plants (frame level).

    Applied at the eGRID-input seam of :func:`_rows_to_generators` — right
    after :func:`_apply_egrid_boundary_hr_repairs` — so it is a better read of
    the SAME source the plant-grain join used, and every class-specific
    measured mechanism downstream (``measured_ct_heat_rates`` in the row
    loop, ``measured_chp_heat_rates`` / ``egrid_identity_heat_rates`` after
    load) keeps exactly the precedence it has today. A row is keyed by its
    own ``prime_mover``'s family; rows with no family (hydro, wind, storage,
    fuel cells) and nuclear rows are never touched. Returns the frame and the
    set of plants any row of which was repriced.

    The nyiso-184 replacement for :data:`MIXED_FACILITY_STEAM_HR`'s hand
    number at the plants the artifact covers (PREREG-nyiso184 §1, §3 R1):
    zero free parameters, regenerates from whichever eGRID vintage the join
    reads, responds to changed conditions (rule 13), no per-plant carve
    (rule 24).
    """
    if "heat_rate" not in df.columns or "plant_id" not in df.columns:
        return df, frozenset()
    if "prime_mover" not in df.columns:
        return df, frozenset()
    rates = egrid_family_heat_rates_for(iso)
    if not rates:
        return df, frozenset()
    codes = pd.to_numeric(df["plant_id"], errors="coerce")
    families = df["prime_mover"].map(egrid_prime_mover_family)
    nuclear = (
        df["energy_source"].astype(str).str.strip().str.upper() == "NUC"
        if "energy_source" in df.columns
        else pd.Series(False, index=df.index)
    )
    keys = list(zip(codes.fillna(-1).astype(int), families.fillna("")))
    new = pd.Series([rates.get(k) for k in keys], index=df.index, dtype="float64")
    hit = new.notna() & ~nuclear
    if not hit.any():
        return df, frozenset()
    df = df.copy()
    df.loc[hit, "heat_rate"] = new[hit]
    covered = frozenset(int(c) for c in codes[hit].dropna().unique())
    logger.info(
        "%s: eGRID prime-mover-family heat rates applied to %d generator row(s) "
        "across %d plant(s)",
        iso,
        int(hit.sum()),
        len(covered),
    )
    return df, covered


def _rows_to_generators(
    df: pd.DataFrame,
    iso: str,
    iso_config: ISOConfig | None,
    apply_cc_summer_guard: bool = True,
    measured_ct_heat_rates: bool = False,
    cc_steam_part_capacity: bool = False,
    cc_steam_part_reclass: bool = False,
    egrid_family_heat_rates: bool = False,
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

    ``measured_ct_heat_rates`` (``ScenarioConfig.measured_ct_heat_rates``)
    swaps the eGRID plant-average annual heat rate for the CAMPD-measured
    LOADED rate on CT_PEAKER rows the artifact covers — see the row loop below
    and :func:`market_sim.data.fleet.campd_bins.measured_ct_heat_rates`.

    ``cc_steam_part_capacity`` (``ScenarioConfig.cc_steam_part_capacity``)
    restores the combined-cycle STEAM parts the fuel-type map drops. EIA-860's
    ``Energy Source 1`` on a ``CA`` row is the block's supplementary / duct
    fuel, so a duct-fired steam part reports ``BFG`` / ``OG`` / ``DFO``,
    :func:`_map_fuel_type` returns ``None`` and the row never reaches the LP —
    even though its primary energy input is its own block's turbine exhaust.
    Gated on :data:`~market_sim.config.plant_taxonomy.CC_STEAM_PART_REPAIR_ISOS`
    (rule 25 ``[R-ISO-SCOPE]``) and resolved by
    :func:`cc_steam_part_generators`. Default off and byte-identical off.

    ``cc_steam_part_reclass`` (``ScenarioConfig.cc_steam_part_reclass``) covers
    the SAME predicate's other half: the steam parts the fuel-type map CARRIES
    under the non-gas fuel their own ``Energy Source 1`` names (``DFO`` →
    ``oil``) rather than dropping. Total capacity is unchanged; the row's class,
    fuel, VOM, CO2 rate and EFORd move onto the gas combined-cycle block it is
    half of. Gated on its own
    :data:`~market_sim.config.plant_taxonomy.CC_STEAM_PART_RECLASS_ISOS` — never
    the repair's set, because the repair's ``fuel_type is None`` gate is
    load-bearing (it is what keeps MISO 1004 Edwardsport's real 555 MW IGCC
    machine in ``COAL``; miso-125 §6). Default off and byte-identical off.
    """
    if "status" in df.columns:
        status = df["status"].astype(str).str.strip().str.upper()
        df = df[status == "OP"]

    # Boundary-reconcile eGRID plant heat rates double-counted across co-located
    # CEMS facilities (Riverside 55641). Single seam: every fleet read path — the
    # canonical snapshot, the per-year vintages, the mothball re-carry — lands here.
    df = _apply_egrid_boundary_hr_repairs(df)

    # Simple-cycle physical FLOOR (SPP-49, owner ruling P19): the mirror of the
    # boundary repair above — a plant whose operating rows are all GT / IC and
    # whose plant-grain eGRID rate sits below HEAT_RATE_BINS["gas_ct"]["aero"]
    # is clamped to that floor. Same seam, unconditional, so every read path and
    # every measured mechanism below keep their precedence.
    df = _apply_simple_cycle_hr_floor(df)

    # eGRID prime-mover-FAMILY heat rates (config.egrid_family_heat_rates,
    # default off, byte-identical off): at a plant hosting two or more
    # prime-mover families the plant-grain PLHTRT is a blend of both, so each
    # family takes its own HTIAN/GENNTAN rate from the same vintage. Same seam
    # as the boundary repair above, so every class-scoped measured mechanism
    # below keeps its precedence. Covered plants are recorded per ISO so the
    # hand-number channel (_correct_mixed_facility_steam_hr) skips them.
    if egrid_family_heat_rates:
        df, covered = _apply_egrid_family_heat_rates(df, iso)
        _EGRID_FAMILY_COVERED_PLANTS[iso.upper()] = covered
    else:
        _EGRID_FAMILY_COVERED_PLANTS[iso.upper()] = frozenset()

    # Measured CT loaded heat rates (config.measured_ct_heat_rates). Resolved
    # once here rather than in the row loop; empty when the flag is off or the
    # ISO has no committed artifact, in which case every row keeps its eGRID
    # rate. Applied INSIDE the loop (not as a frame-level repair like the
    # boundary fix above) because it is class-scoped: only a row that resolves
    # to CT_PEAKER may take it, so a mixed steam/CT facility's boilers keep the
    # eGRID plant average while its turbines take their own measured rate.
    ct_heat_rates: dict[int, float] = (
        _pkg_ns().measured_ct_heat_rates(iso) if measured_ct_heat_rates else {}
    )

    # Combined-cycle steam parts to restore (config.cc_steam_part_capacity).
    # Resolved once here, ISO-gated, and empty in every ISO that has not
    # verified the repair on its own data — so the flag is a strict no-op
    # outside CC_STEAM_PART_REPAIR_ISOS as well as when it is off.
    steam_parts: frozenset[tuple[int, str]] = (
        cc_steam_part_generators()
        if cc_steam_part_capacity and iso.upper() in CC_STEAM_PART_REPAIR_ISOS
        else frozenset()
    )

    # Combined-cycle steam parts to RE-CLASS (config.cc_steam_part_reclass).
    # Same predicate, disjoint population and opposite object: these are the
    # rows the fuel map CARRIES under a non-gas fuel taken from the steam
    # part's own (duct / legacy) Energy Source 1, not the rows it drops. Its
    # own ISO registry, never CC_STEAM_PART_REPAIR_ISOS — the two gates are
    # deliberately separate (see CC_STEAM_PART_RECLASS_ISOS).
    reclass_parts: frozenset[tuple[int, str]] = (
        cc_steam_part_generators()
        if cc_steam_part_reclass and iso.upper() in CC_STEAM_PART_RECLASS_ISOS
        else frozenset()
    )

    records: list[dict] = []
    # Per-plant EIA-860 nameplate sum over merchant-CC generators, for the
    # summer-capacity consistency guard applied after the row loop.
    cc_nameplate_sum: dict[int, float] = {}
    for row in df.itertuples(index=False):
        data = row._asdict()
        # Is this row a combined-cycle steam part the fuel map would drop? The
        # key is (plant, generator) because a plant can host both a genuine
        # steam part and an unrelated process-gas machine.
        is_steam_part = (
            bool(steam_parts)
            and (
                int(_to_float(data.get("plant_id")) or 0),
                str(data.get("generator_id") or "").strip(),
            )
            in steam_parts
        )
        fuel_type = _map_fuel_type(
            data.get("technology"),
            data.get("energy_source"),
            data.get("prime_mover"),
        )
        # The repair only ever RESTORES a row the fuel map drops; it never
        # reclassifies one that already resolves. MISO 1004 Edwardsport matches
        # the steam-part predicate (its `ST` row is CA / SGC sharing unit code
        # "1" with two NG CT siblings) but its technology string carries "coal",
        # so `_map_fuel_type` resolves it to coal and it is ALREADY in the fleet
        # as COAL 555.0 MW. Gating on `fuel_type is None` keeps it there: a
        # represented machine must not be re-bucketed by a capacity repair
        # (miso-125 §6 — the 555 MW false positive the presence test caught).
        # Is this row a carried-but-mis-fuelled steam part the re-class covers?
        # Disjoint from `is_steam_part` in practice (that branch only fires when
        # the fuel map DROPS the row), and gated on its own flag + ISO set.
        is_reclass_part = (
            bool(reclass_parts)
            and (
                int(_to_float(data.get("plant_id")) or 0),
                str(data.get("generator_id") or "").strip(),
            )
            in reclass_parts
        )
        rescued_steam_part = False
        if fuel_type is None:
            if not is_steam_part:
                continue
            # The block's primary energy input is its CT siblings' exhaust, so
            # the steam part is gas combined cycle whatever its duct fuel says.
            fuel_type = "gas_cc"
            rescued_steam_part = True
        elif is_reclass_part and fuel_type != "gas_cc":
            # Carried, but under the fuel its own Energy Source 1 names. A
            # combined-cycle steam turbine has no combustion path — it is driven
            # by its CT siblings' exhaust, reports no CEMS stack of its own, and
            # every MMBtu the block burns is already metered at those siblings.
            # So that code is a duct / legacy label, and dispatching the row as
            # a standalone unit of that fuel burns a fuel the machine does not
            # have. Re-class it onto the block it is half of. Capacity is
            # UNCHANGED (contrast the restore branch above); what moves is the
            # class, fuel, VOM, CO2 rate and EFORd. NEISO 6081 Stony Brook
            # `CA1`: 96.0 MW carried as `oil` at $4.50 VOM / 1.0 t-CO2/MWh
            # against three `CC_REGULAR` `CT` siblings that share its plant heat
            # rate (rule 25 [R-ISO-SCOPE]: NEISO's whole population is that row).
            fuel_type = "gas_cc"
            rescued_steam_part = True

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
        elif fuel_type in ("gas_cc", "gas_cc_ccs", "gas_ct", "gas_st"):
            group = classify_plant(
                data.get("energy_source"),
                data.get("prime_mover"),
                chp_flag,
                plant_code,
                cc_steam_part=rescued_steam_part,
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

        # The measured loaded heat rate wins over the eGRID plant-average
        # annual rate assigned above (rule 14 [R-ACCURATE]): eGRID's figure is
        # an annual average, so it blends start / part-load / shutdown fuel
        # into the number that sets a peaker's offer, and it is published
        # per-PLANT, so at a mixed facility it is not even the right
        # technology's rate. Gated on ``group`` — resolved just above — so a
        # mixed plant's steam and CC rows are untouched.
        if ct_heat_rates and group == "CT_PEAKER":
            measured_hr = ct_heat_rates.get(plant_code)
            if measured_hr is not None:
                heat_rate = measured_hr

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
    apply_measured_chp_heat_rates as _apply_measured_chp_heat_rates,
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
def _cc_steam_part_generators(eia860_dir: Path) -> frozenset[tuple[int, str]]:
    """Cached ``(plant_code, generator_id)`` keys of dropped CC steam parts.

    ``ScenarioConfig.cc_steam_part_capacity``. Reads the raw EIA-860 operable
    generator sheet — the same bridge :func:`_chp_by_plant` uses for the CHP
    flag, and for the same reason: the processed generator parquet the fleet
    loads does **not** carry ``Unit Code``, and the predicate needs a plant's
    whole generator roster.

    A row is the steam part of a gas-fired combined-cycle block iff ALL of:

    * prime mover is :data:`~market_sim.config.plant_taxonomy.CC_STEAM_PART_PRIME_MOVER`
      (``CA``, EIA's code for the combined-cycle steam part);
    * its own ``Energy Source 1`` is not ``NG`` — an ``NG``-coded ``CA`` row
      already classes correctly and needs no repair;
    * its ``Unit Code`` is non-empty, and at least one sibling at the SAME plant
      carries the SAME ``Unit Code`` with prime mover ``CT`` and
      ``Energy Source 1`` ``NG``. The shared unit code is EIA-860's own
      machine-level statement that the rows are one block, and it is what
      separates a genuine steam part from a landfill-gas or oil standalone;
    * the steam part is **not older** than the oldest of those ``NG`` ``CT``
      siblings. A heat-recovery steam generator is commissioned with or after
      the gas turbines whose exhaust drives it, so a "steam part" predating
      every turbine that supposedly drives it is a plant-wide steam header
      sharing a unit-code label, not a combined cycle (measured at MISO 50973
      Motiva: ``CA`` rows of 1957/1962/1978 against ``NG`` ``CT`` siblings of
      1983 and 2011). KNOWN CONSERVATIVE LIMITATION: a *repowered* block — an
      existing steam turbine fitted with new gas turbines and an HRSG — also
      has an older ``CA`` row and is excluded here. That direction is safe: the
      model drops 100 % of these rows today, so this clause can only ever
      restore fewer of them, never more.

    Returns an empty set when the sheet is absent, so a fleet without the raw
    EIA-860 extract is unchanged.
    """
    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return frozenset()
    cols = [
        "Plant Code",
        "Generator ID",
        "Prime Mover",
        "Energy Source 1",
        "Unit Code",
        "Operating Year",
    ]
    try:
        raw = pd.read_parquet(path, columns=cols)
    except Exception:
        logger.warning(
            "EIA-860 operable sheet at %s is unreadable — no CC steam parts resolved",
            path,
        )
        return frozenset()

    raw = raw.copy()
    raw.columns = [str(c).strip() for c in raw.columns]
    pm = raw["Prime Mover"].astype(str).str.strip().str.upper()
    es = raw["Energy Source 1"].astype(str).str.strip().str.upper()
    uc = raw["Unit Code"].astype(str).str.strip()
    # "nan" is what a null Unit Code stringifies to; a standalone machine
    # carries no block and can never be a steam part.
    has_uc = (uc != "") & (uc.str.lower() != "nan")
    year = pd.to_numeric(raw["Operating Year"], errors="coerce")

    # Oldest NG CT sibling per (plant, unit code) — the block's first turbine.
    sib = raw[(pm == "CT") & (es == "NG") & has_uc]
    if sib.empty:
        return frozenset()
    sib_year = (
        pd.to_numeric(sib["Operating Year"], errors="coerce")
        .groupby([sib["Plant Code"], uc.loc[sib.index]])
        .min()
    )

    cand = raw[(pm == CC_STEAM_PART_PRIME_MOVER) & (es != "NG") & has_uc]
    out: set[tuple[int, str]] = set()
    for idx, row in cand.iterrows():
        key = (row["Plant Code"], uc.at[idx])
        first_turbine = sib_year.get(key)
        if first_turbine is None or pd.isna(first_turbine):
            continue  # no NG CT sibling in this block
        ca_year = year.at[idx]
        if pd.isna(ca_year) or float(ca_year) < float(first_turbine):
            continue  # predates its own turbines — a steam header, not a block
        try:
            plant_code = int(row["Plant Code"])
        except (TypeError, ValueError):
            continue
        out.add((plant_code, str(row["Generator ID"]).strip()))
    logger.info(
        "EIA-860: %d combined-cycle steam part(s) resolved for the "
        "cc_steam_part_capacity repair",
        len(out),
    )
    return frozenset(out)


def cc_steam_part_generators(
    eia860_dir: Path | None = None,
) -> frozenset[tuple[int, str]]:
    """Return ``(plant_code, generator_id)`` keys of dropped CC steam parts.

    Resolves the EIA-860 directory through :func:`paths.active_eia860_dir` when
    not given (so a year-matched vintage switch is honored) and defers to the
    directory-keyed cache above.
    """
    return _cc_steam_part_generators(
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


@lru_cache(maxsize=8)
def _operating_month_by_unit(eia860_dir) -> dict[tuple[int, str], int]:
    """Return ``{(plant_code, generator_id): Operating Month}`` from the operable sheet.

    Read from ``<eia860_dir>/eia860_generator_operable.parquet`` — the same
    raw sheet :func:`_chp_by_plant` bridges the CHP flag from and
    ``cod_ramp._load_cod_map`` reduces the plant COD from — so a fleet built
    from a year-matched ``vintage_<year>/`` directory takes that vintage's own
    months. Keys mirror the processed parquet's ``(plant_id, generator_id)``
    (the id stripped, as ``_rows_to_generators`` strips it). Rows with no
    month are omitted so the caller's January default applies. Empty when the
    sheet is absent.
    """
    path = Path(eia860_dir) / "eia860_generator_operable.parquet"
    if not path.exists():
        return {}
    raw = pd.read_parquet(
        path, columns=["Plant Code", "Generator ID", "Operating Month"]
    )
    raw.columns = [str(c).strip() for c in raw.columns]
    pc = pd.to_numeric(raw["Plant Code"], errors="coerce")
    om = pd.to_numeric(raw["Operating Month"], errors="coerce")
    gid = raw["Generator ID"].astype(str).str.strip()
    out: dict[tuple[int, str], int] = {}
    for code, month, gen_id in zip(pc, om, gid):
        if pd.isna(code) or pd.isna(month) or not (1 <= int(month) <= 12):
            continue
        out[(int(code), gen_id)] = int(month)
    return out


def _load_fleet_from_parquet(
    parquet_path: Path,
    iso: str,
    iso_config: ISOConfig | None,
    year: int | None = None,
    apply_cc_summer_guard: bool = True,
    measured_ct_heat_rates: bool = False,
    cc_steam_part_capacity: bool = False,
    cc_steam_part_reclass: bool = False,
    egrid_family_heat_rates: bool = False,
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
    # Membership over every BA the region comprises (a pool region such as
    # NWPP has 17; the 1:1 regions select exactly the rows ``== code`` did).
    codes = ba_codes(iso)
    if codes and "balancing_authority_code" in df.columns:
        ba = df["balancing_authority_code"].astype(str).str.strip()
        df = df[ba.isin(codes)]

    # Join the plant-level CHP flag (dropped from the processed generators
    # parquet) from the raw EIA-860 operable sheet, so gas cogens are grouped
    # CC_CHP / CT_CHP / ST_CHP. A plant is CHP if any of its units is flagged.
    # ``year`` selects that vintage's CHP designation when the per-year lookup
    # is available (else the latest committed snapshot).
    df = df.copy()
    df["chp"] = df["plant_id"].map(_chp_by_plant(parquet_path.parent, year)).fillna("N")
    # Join each unit's own month-precise ``Operating Month`` from the SAME
    # directory's raw operable sheet (the processed generators parquet carries
    # ``operating_year`` only). This is what makes ``Generator.online_month`` a
    # unit's own measured EIA-860 record, which ``cod_ramp.effective_cod`` now
    # prefers over the plant-collapsed COD for the online date (SOCO-15, owner
    # card S12, rule 14 [R-ACCURATE]); a unit the sheet does not carry keeps
    # the January default exactly as before. Never overrides a month the
    # parquet already carries (the retiree-channel schema has one).
    if "operating_month" not in df.columns or df["operating_month"].isna().all():
        months = _operating_month_by_unit(parquet_path.parent)
        if months:
            keys = list(
                zip(
                    pd.to_numeric(df["plant_id"], errors="coerce"),
                    df["generator_id"].astype(str).str.strip(),
                )
            )
            df["operating_month"] = [months.get(k) for k in keys]

    generators = _rows_to_generators(
        df,
        iso,
        iso_config,
        apply_cc_summer_guard=apply_cc_summer_guard,
        measured_ct_heat_rates=measured_ct_heat_rates,
        cc_steam_part_capacity=cc_steam_part_capacity,
        cc_steam_part_reclass=cc_steam_part_reclass,
        egrid_family_heat_rates=egrid_family_heat_rates,
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
    measured_ct_heat_rates: bool = False,
    cc_steam_part_capacity: bool = False,
    cc_steam_part_reclass: bool = False,
    egrid_family_heat_rates: bool = False,
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
        normalized,
        iso,
        iso_config,
        apply_cc_summer_guard=apply_cc_summer_guard,
        measured_ct_heat_rates=measured_ct_heat_rates,
        cc_steam_part_capacity=cc_steam_part_capacity,
        cc_steam_part_reclass=cc_steam_part_reclass,
        egrid_family_heat_rates=egrid_family_heat_rates,
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


def egrid_identity_heat_rates_for(iso: str) -> dict[int, float]:
    """Load the committed eGRID identity-reconciled heat-rate artifact.

    ``{plant_id: pooled_heat_rate}`` from
    ``data/raw/_processed-legacy/egrid_identity_heat_rates_<ISO>.csv``
    (``scripts/data/derive_egrid_identity_heat_rates.py`` — the threshold-free
    two-registry identity discovery rule; see the ScenarioConfig
    ``egrid_identity_heat_rates`` docstring and
    ``FINDING-nyiso150-allegany-hr-identity-2026-08-22.md``). Empty when the
    ISO has no committed artifact — the mechanism is a no-op there by
    construction (rule 25: each ISO's lane derives its own artifact).
    """
    from market_sim.config.paths import PROCESSED_DIR

    path = PROCESSED_DIR / f"egrid_identity_heat_rates_{iso}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if df.empty or not {"plant_id", "heat_rate_mmbtu_mwh"}.issubset(df.columns):
        return {}
    return {
        int(r.plant_id): float(r.heat_rate_mmbtu_mwh)
        for r in df.itertuples()
        if float(r.heat_rate_mmbtu_mwh) > 0.0
    }


def apply_egrid_identity_heat_rates(generators: list, iso: str) -> frozenset[int]:
    """Swap in the identity-reconciled measured heat rate where it covers.

    In-place, gated by ``ScenarioConfig.egrid_identity_heat_rates`` at the
    call site; every unit of a covered plant takes the plant's pooled
    measured rate (the plants are single-block small CCs whose class default
    was the only rate they carried). Returns the ``id()`` set of repriced
    generators, mirroring :func:`market_sim.data.chp.apply_measured_chp_heat_rates`.
    """
    rates = egrid_identity_heat_rates_for(iso)
    if not rates:
        return frozenset()
    touched: set[int] = set()
    for gen in generators:
        rate = rates.get(int(getattr(gen, "plant_code", 0) or 0))
        if rate is not None:
            gen.heat_rate = rate
            touched.add(id(gen))
    logger.info(
        "%s: eGRID identity-reconciled heat rates applied to %d generator(s) "
        "across %d plant(s)",
        iso,
        len(touched),
        len(rates),
    )
    return frozenset(touched)


def egrid_steam_collapse_heat_rates_for(iso: str) -> dict[int, float]:
    """Load the committed eGRID steam-collapse identity heat-rate artifact.

    ``{plant_id: identity_heat_rate}`` for the plants whose APPLIED-vintage
    row is ADMITTED in
    ``data/raw/_processed-legacy/egrid_steam_collapse_heat_rates_<ISO>.csv``
    (``scripts/data/derive_egrid_steam_collapse_heat_rates.py`` — the
    population rule over every combined cycle of the ISO with a filed steam
    generator; see the ScenarioConfig ``egrid_steam_collapse_heat_rates``
    docstring and ``PREREG-nyiso189-steam-collapse-identity-ab.md``). Empty
    when the ISO has no committed artifact — the mechanism is a no-op there
    by construction (rule 25: each ISO's lane derives its own artifact).
    """
    from market_sim.config.paths import PROCESSED_DIR

    path = PROCESSED_DIR / f"egrid_steam_collapse_heat_rates_{iso}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    need = {"plant_id", "identity_hr", "applied", "admitted"}
    if df.empty or not need.issubset(df.columns):
        return {}
    live = df[df["applied"].astype(bool) & df["admitted"].astype(bool)]
    return {
        int(r.plant_id): float(r.identity_hr)
        for r in live.itertuples()
        if pd.notna(r.identity_hr) and float(r.identity_hr) > 0.0
    }


def apply_egrid_steam_collapse_heat_rates(
    generators: list, iso: str, skip_ids: frozenset[int] = frozenset()
) -> frozenset[int]:
    """Swap in the CT-heat identity rate where the steam-generator filing
    collapsed in the applied eGRID vintage.

    In-place, gated by ``ScenarioConfig.egrid_steam_collapse_heat_rates`` at
    the call site; every unit of an admitted plant takes the plant's identity
    rate EXCEPT generators in ``skip_ids`` (already on a measured rate from
    ``measured_chp_heat_rates`` / ``egrid_identity_heat_rates`` on this load
    — rule 19, one measured rate per plant). Returns the ``id()`` set of
    repriced generators, mirroring :func:`apply_egrid_identity_heat_rates`.
    """
    rates = egrid_steam_collapse_heat_rates_for(iso)
    if not rates:
        return frozenset()
    touched: set[int] = set()
    for gen in generators:
        if id(gen) in skip_ids:
            continue
        rate = rates.get(int(getattr(gen, "plant_code", 0) or 0))
        if rate is not None:
            gen.heat_rate = rate
            touched.add(id(gen))
    logger.info(
        "%s: eGRID steam-collapse identity heat rates applied to %d generator(s) "
        "across %d plant(s)",
        iso,
        len(touched),
        len(rates),
    )
    return frozenset(touched)


def load_fleet_from_csv(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
    year: int | None = None,
    apply_cc_summer_guard: bool = True,
    measured_ct_heat_rates: bool = False,
    measured_chp_heat_rates: bool = False,
    egrid_identity_heat_rates: bool = False,
    apply_chp_steam_credit_correction: bool = True,
    cc_steam_part_capacity: bool = False,
    cc_steam_part_reclass: bool = False,
    egrid_family_heat_rates: bool = False,
    egrid_steam_collapse_heat_rates: bool = False,
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
        measured_ct_heat_rates: When True (``ScenarioConfig.
            measured_ct_heat_rates``), CT_PEAKER generators at plants the
            committed CAMPD artifact covers take their measured LOADED heat
            rate instead of the eGRID plant-average annual rate. Only the
            peaker rows of a mixed facility are affected.
        measured_chp_heat_rates: When True (``ScenarioConfig.
            measured_chp_heat_rates``), topping-cycle CHP generators
            (``CC_CHP`` / ``CT_CHP``) at plants the committed artifact covers
            take their measured POWER-ONLY heat rate instead of eGRID's
            steam-credited one, and are exempted from the legacy hand-factor
            correction. Default off and byte-identical off.
        apply_chp_steam_credit_correction: When False, the legacy hand-factor
            CHP correction (:func:`~market_sim.data.chp._correct_chp_steam_credit_hr`)
            is skipped and the binned-fleet side cache is left untouched. The
            model ALWAYS leaves this True; only
            ``scripts/data/derive_chp_power_only_heat_rates.py`` passes False,
            to read each plant's incumbent heat rate **at the seam where the
            measured rate would replace it** — i.e. after the eGRID join and
            the boundary repairs but before the hand factor. Its basis check
            ("is the incumbent this eGRID row, or a repair/bin fallback?")
            is otherwise blinded in the two hand-factor ISOs, where every
            corrected plant reads as a mismatch (caiso-147).
        cc_steam_part_capacity: When True (``ScenarioConfig.
            cc_steam_part_capacity``), the combined-cycle STEAM parts
            :func:`_map_fuel_type` drops — ``CA``-prime-mover rows whose own
            ``Energy Source 1`` is the block's duct fuel rather than ``NG`` —
            are restored to the fleet as gas combined cycle. ISO-gated on
            :data:`~market_sim.config.plant_taxonomy.CC_STEAM_PART_REPAIR_ISOS`
            (rule 25 ``[R-ISO-SCOPE]``). Default off and byte-identical off.
        cc_steam_part_reclass: When True (``ScenarioConfig.
            cc_steam_part_reclass``), the combined-cycle STEAM parts
            :func:`_map_fuel_type` CARRIES under a non-gas fuel taken from the
            row's own duct / legacy ``Energy Source 1`` are re-classed to gas
            combined cycle. Capacity is unchanged — the fuel, class, VOM, CO2
            rate and EFORd move. ISO-gated on
            :data:`~market_sim.config.plant_taxonomy.CC_STEAM_PART_RECLASS_ISOS`
            (rule 25 ``[R-ISO-SCOPE]``). Default off and byte-identical off.
        egrid_family_heat_rates: When True (``ScenarioConfig.
            egrid_family_heat_rates``), every generator at a plant the
            committed per-ISO artifact covers — a plant hosting two or more
            prime-mover families — takes its own family's eGRID
            ``HTIAN``/``GENNTAN`` rate instead of the plant-grain blend, and
            :data:`MIXED_FACILITY_STEAM_HR`'s hand number is skipped there
            (rule 19). See :func:`_apply_egrid_family_heat_rates`. Default
            off and byte-identical off.
        egrid_steam_collapse_heat_rates: When True (``ScenarioConfig.
            egrid_steam_collapse_heat_rates``), every generator of a
            combined cycle whose eGRID steam-generator filing collapsed in
            the applied vintage (the committed per-ISO artifact's admitted
            rows) takes the CT-heat identity rate in place of the inflated
            plant-grain ``PLHTRT``, skipping generators the measured-CHP /
            identity mechanisms already repriced and plants the family
            construction covers (rule 19). See
            :func:`apply_egrid_steam_collapse_heat_rates`. Default off and
            byte-identical off.

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
            df,
            iso,
            iso_config,
            apply_cc_summer_guard=apply_cc_summer_guard,
            measured_ct_heat_rates=measured_ct_heat_rates,
            cc_steam_part_capacity=cc_steam_part_capacity,
            cc_steam_part_reclass=cc_steam_part_reclass,
            egrid_family_heat_rates=egrid_family_heat_rates,
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
            iso,
            iso_config,
            data_dir,
            year,
            apply_cc_summer_guard=apply_cc_summer_guard,
            measured_ct_heat_rates=measured_ct_heat_rates,
            cc_steam_part_capacity=cc_steam_part_capacity,
            cc_steam_part_reclass=cc_steam_part_reclass,
            egrid_family_heat_rates=egrid_family_heat_rates,
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
            measured_ct_heat_rates=measured_ct_heat_rates,
            cc_steam_part_capacity=cc_steam_part_capacity,
            cc_steam_part_reclass=cc_steam_part_reclass,
            egrid_family_heat_rates=egrid_family_heat_rates,
        )
        if from_parquet is None:
            raise FileNotFoundError(
                f"No EIA-860 data for {iso}: expected a per-ISO override "
                f"CSV at {csv_path} or the generator parquet at "
                f"{parquet_path}"
            )
        generators = from_parquet
        source = parquet_path

    # The hand-number channel skips every plant the eGRID family construction
    # repriced on this load (empty while egrid_family_heat_rates is off).
    _correct_mixed_facility_steam_hr(
        generators, _EGRID_FAMILY_COVERED_PLANTS.get(iso, frozenset())
    )
    # Measured power-only CHP heat rates FIRST (config.measured_chp_heat_rates,
    # default off): where the committed artifact covers a (plant, class) the
    # plant takes its own measured rate, and the legacy hand-factor correction
    # below skips it (rule 19 [R-ONE-MECH]). Off, ``measured`` is empty and the
    # call below is byte-identical to what it always was.
    measured = (
        _apply_measured_chp_heat_rates(generators, iso)
        if measured_chp_heat_rates
        else frozenset()
    )
    # eGRID identity-reconciled heat rates (config.egrid_identity_heat_rates,
    # default off): a plant whose measured eGRID history lives under a
    # DIFFERENT ORISPL (the proven two-registry identity splits of the
    # committed per-ISO artifact) takes its pooled measured rate instead of
    # the HEAT_RATE_BINS vintage class default. Off, the artifact is not read
    # and the fleet is byte-identical.
    identity_touched = (
        apply_egrid_identity_heat_rates(generators, iso)
        if egrid_identity_heat_rates
        else frozenset()
    )
    # eGRID steam-collapse identity heat rates (config.
    # egrid_steam_collapse_heat_rates, default off): a combined cycle whose
    # steam generator's EIA-923 filing collapsed in the applied vintage takes
    # the CT-heat identity rate in place of the inflated plant-grain PLHTRT.
    # Same seam class as the identity swap above; never stacked on a plant
    # another measured mechanism already repriced (rule 19). Off, the
    # artifact is not read and the fleet is byte-identical.
    if egrid_steam_collapse_heat_rates:
        family_covered = _EGRID_FAMILY_COVERED_PLANTS.get(iso, frozenset())
        skip = set(measured) | set(identity_touched)
        skip |= {
            id(g)
            for g in generators
            if int(getattr(g, "plant_code", 0) or 0) in family_covered
        }
        apply_egrid_steam_collapse_heat_rates(generators, iso, frozenset(skip))
    if not apply_chp_steam_credit_correction:
        # Basis-inspection read only (the CHP derive). Return before the hand
        # factor AND before the cache write, so the committed side cache always
        # reflects the fleet the model actually prices with.
        return generators
    _correct_chp_steam_credit_hr(generators, iso, skip_ids=measured)
    _pkg_ns()._cache_binned_fleet(iso, generators, source)
    return generators


def _correct_mixed_facility_steam_hr(
    generators: list[Generator], skip_plants: frozenset[int] = frozenset()
) -> None:
    """Reassign the steam-unit heat rate at mixed CC+ST facilities (in place).

    See :data:`MIXED_FACILITY_STEAM_HR`: at a combined CC+ST plant the single
    plant-level EIA-923 heat rate blends the efficient CC with the legacy steam
    turbine, so the steam units inherit a too-low (CC-influenced) heat rate. This
    lifts only the steam (``ST_GAS``) units of a listed plant to the steam-class
    value, and only when their current heat rate is *below* it (so a correctly
    metered steam unit is never lowered). The CC rows keep their measured blend.

    ``skip_plants`` — the plants the eGRID prime-mover-family construction
    (``ScenarioConfig.egrid_family_heat_rates``) already repriced from
    measured unit-grain data — are left alone: the family rate supersedes the
    hand number there rather than stacking on it (rule 19 ``[R-ONE-MECH]``).
    Empty while that flag is off, so this runs exactly as it always has.
    """
    for gen in generators:
        code = int(gen.plant_code)
        if code in skip_plants:
            continue
        target = MIXED_FACILITY_STEAM_HR.get(code)
        if (
            target is not None
            and gen.plant_group == "ST_GAS"
            and gen.heat_rate < target
        ):
            gen.heat_rate = target


@lru_cache(maxsize=None)
def _committed_vintage_years_for(base: Path) -> tuple[int, ...]:
    """Return the committed ``vintage_<year>/`` snapshot years under ``base``.

    Support for the retiree vintage-status oracle (miso-188,
    ``ScenarioConfig.retiree_vintage_status_scope``). Scans once per base
    path; a repo with no vintage dirs yields an empty tuple (the oracle
    then fails open — nothing is ever dropped).
    """
    years: list[int] = []
    if base.exists():
        for p in base.iterdir():
            name = p.name
            if p.is_dir() and name.startswith("vintage_"):
                try:
                    years.append(int(name.removeprefix("vintage_")))
                except ValueError:
                    continue
    return tuple(sorted(years))


@lru_cache(maxsize=None)
def _vintage_status_index_for(
    base: Path, vintage_year: int
) -> dict[tuple[int, str], str] | None:
    """Return ``{(plant_id, GENERATOR_ID): STATUS}`` from one committed
    ``vintage_<vintage_year>/`` operable snapshot under ``base``, or
    ``None`` when absent.

    Support for the retiree vintage-status oracle (miso-188): the SAME
    year-matched vintage record :func:`load_mothballed_but_operating`
    already reads as its status oracle, indexed per unit. Ids are
    normalized ``strip().upper()``.
    """
    path = base / f"vintage_{int(vintage_year)}" / EIA_860_PARQUET_NAME
    if not path.exists():
        return None
    try:
        df = _normalize_columns(pd.read_parquet(path))
    except Exception:  # pragma: no cover - schema drift falls open
        logger.warning("vintage-status index unavailable (%s); oracle open", path)
        return None
    if "status" not in df.columns:
        return None
    codes = pd.to_numeric(df["plant_id"], errors="coerce")
    out: dict[tuple[int, str], str] = {}
    for code, gid, st in zip(codes, df["generator_id"], df["status"]):
        if pd.isna(code):
            continue
        out[(int(code), str(gid).strip().upper())] = str(st).strip().upper()
    return out


def _retiree_vintage_status(plant_id: int, generator_id: str, year: int) -> str | None:
    """Latest committed vintage ≤ ``year`` status for one retiree unit.

    The miso-188 oracle lookup: walk the committed vintages at or before the
    backcast solve year, newest first, and return the first status that
    lists ``(plant_id, generator_id)`` on its operable sheet — EIA's own
    contemporaneous judgment of the unit closest to (and never after) the
    solve year. ``None`` when no committed vintage lists the unit (the
    caller fails OPEN and keeps it).
    """
    gid = str(generator_id).strip().upper()
    base = _pkg_ns().EIA_860_DIR
    for v in reversed(_committed_vintage_years_for(base)):
        if v > int(year):
            continue
        idx = _vintage_status_index_for(base, v)
        if idx is None:
            continue
        st = idx.get((int(plant_id), gid))
        if st is not None:
            return st
    return None


# Raw EIA-860 "Retired and Canceled" sheet parquet + plant sheet, read only by
# the gated partial-plant exit carry (miso-190). Column map mirrors
# scripts/data/process_eia860.py::_GENERATOR_COLUMN_MAP (the raw headers carry
# parentheses that _normalize_columns' snake_case aliases do not match).
_RETIRED_CANCELED_PARQUET_NAME = "eia860_generator_retired_and_canceled.parquet"
_PLANT_PARQUET_NAME = "eia860_plant.parquet"
# Mirrors process_eia860.RETIREMENT_WINDOW_START (the backcast window start):
# a unit retired in or after this year operated during the window.
#
# ercot-261: MOVED 2023 -> 2019 to restore that mirror. The whole-plant half was
# widened to 2019 by the fleet-vintage charter (process_eia860, charter task 2)
# and this constant -- which its own comment says mirrors it -- was left at 2023,
# so a plant's whole-plant exits reached back to 2019 while its UNIT-GRAIN exits
# stayed stranded at 2023. Measured consequence for ERCOT: Decker Creek (plant
# 3548), a 405 MW gas ST retired 2022, is 98% of ERCOT's 2021-2022 affected
# capacity and is invisible to BOTH halves -- the whole-plant filter refuses it
# by design (four 51.5 MW CTs survive in the operable snapshot, so the
# plant-keyed COD map would hold the whole plant online and double-count), and
# this window then hid it from the one channel that can carry it at unit grain.
# The two halves must move together or the split is incoherent.
# (docs/ADDENDUM-ercot261-partial-plant-scope-2026-09-09.md)
_PARTIAL_EXIT_WINDOW_START = 2019
_PARTIAL_EXIT_COLUMN_MAP: dict[str, str] = {
    "Plant Code": "plant_id",
    "Generator ID": "generator_id",
    "Plant Name": "plant_name",
    "State": "state",
    "Technology": "technology",
    "Energy Source 1": "energy_source",
    "Prime Mover": "prime_mover",
    "Nameplate Capacity (MW)": "nameplate_capacity_mw",
    "Summer Capacity (MW)": "net_summer_capacity_mw",
    "Operating Year": "operating_year",
    "Operating Month": "operating_month",
    "Retirement Year": "planned_retirement_year",
    "Retirement Month": "planned_retirement_month",
}


def _partial_plant_exit_rows(
    data_dir: Path, codes: tuple[str, ...]
) -> "pd.DataFrame | None":
    """Partial-plant mid-window exits in the canonical retiree-channel schema.

    The gated complement of ``build_within_window_retirees``' whole-plant
    filter (miso-190, ``ScenarioConfig.partial_plant_exit_carry``,
    PREREG-miso190-partial-plant-exit-carry-2026-08-30): units on the
    committed raw "Retired and Canceled" sheet with an ACTUAL retirement in
    or after :data:`_PARTIAL_EXIT_WINDOW_START` whose plant IS still present
    in the operable snapshot. The builder drops exactly these rows because
    the plant-keyed COD map cannot time out a single unit — but
    ``cod_ramp.effective_cod`` prefers a generator's OWN per-unit retirement
    over the plant-collapsed date (the Homer City seam), so a row built here
    with its actual retirement in ``planned_retirement_*`` ages out at unit
    grain while its plant siblings keep running (Sherco-2, 682 MW, ret
    2023-12, in a surviving three-unit plant).

    Rows come back in the canonical channel schema with ``status`` forced to
    ``OP`` (the unit operated during the window; the COD ramp owns the
    exit), exactly as the whole-plant builder emits. Zero overlap with the
    whole-plant parquet by construction (a plant cannot be both present in
    and absent from the operable snapshot). Returns ``None`` when any of the
    three source parquets is absent (a year-matched native vintage dir
    ships none of them — the channel self-neutralizes there exactly as the
    whole-plant path does).
    """
    ret_path = data_dir / _RETIRED_CANCELED_PARQUET_NAME
    op_path = data_dir / EIA_860_PARQUET_NAME
    plant_path = data_dir / _PLANT_PARQUET_NAME
    if not (ret_path.exists() and op_path.exists() and plant_path.exists()):
        return None

    raw = pd.read_parquet(ret_path)
    cols = [c for c in _PARTIAL_EXIT_COLUMN_MAP if c in raw.columns]
    df = raw[cols].rename(columns=_PARTIAL_EXIT_COLUMN_MAP)
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df = df[df["plant_id"].notna()].copy()
    df["plant_id"] = df["plant_id"].astype("int64")

    plant = pd.read_parquet(plant_path)
    ba_by_plant = (
        plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
        .drop_duplicates("Plant Code")
        .set_index("Plant Code")["Balancing Authority Code"]
    )
    ba_by_plant.index = pd.to_numeric(ba_by_plant.index, errors="coerce").astype(
        "int64"
    )
    df["balancing_authority_code"] = (
        df["plant_id"].map(ba_by_plant).astype("string").str.strip()
    )
    if codes:
        # Membership over every BA the region comprises (NWPP is seventeen).
        df = df[df["balancing_authority_code"].isin(codes)]

    df["planned_retirement_year"] = pd.to_numeric(
        df["planned_retirement_year"], errors="coerce"
    )
    df = df[df["planned_retirement_year"] >= _PARTIAL_EXIT_WINDOW_START]

    # The canonical fleet snapshot (snake_case schema) — the same membership
    # the dispatch fleet actually reads: a plant with any surviving row is
    # "present", exactly the builder's whole-plant test.
    op = pd.read_parquet(op_path, columns=["plant_id"])
    op_ids = set(pd.to_numeric(op["plant_id"], errors="coerce").dropna().astype(int))
    df = df[df["plant_id"].isin(op_ids)]
    if df.empty:
        return df

    df = df.copy()
    # The unit operated during the window; OP keeps it through
    # _rows_to_generators' status filter — the COD ramp owns the exit.
    df["status"] = "OP"
    return df


def _register_partial_exit_coal_supply(df: pd.DataFrame) -> None:
    """Register injected coal units' supply classes from their own codes.

    The reporting seam of the partial-plant exit carry (miso-190): a coal
    plant unresolved by ``coal.coal_supply_class`` lands its dispatch in a
    bare ``COAL`` class the EIA-923 benchmark never has. Each injected coal
    unit carries its own committed ``Energy Source 1`` code, mapped through
    the canonical ``COAL_CODE_TO_SUPPLY`` — the identical fallback the
    whole-plant channel applies at build time (``_join_egrid_heat_rate``'s
    sibling) and the benchmark applies at class time. Registered into the
    flag-gated registry (``coal.register_partial_exit_coal_supply``), which
    is consulted LAST (after the curated map, the receipt-derived map and
    the whole-plant retiree fallback) so it can never override an existing
    resolution; empty (and every path byte-identical) while the flag is off.
    """
    from market_sim.config.plant_taxonomy import COAL_CODE_TO_SUPPLY
    from market_sim.data.coal import register_partial_exit_coal_supply

    mapping: dict[int, str] = {}
    for pid, src in zip(df["plant_id"], df.get("energy_source", df["plant_id"] * 0)):
        supply = COAL_CODE_TO_SUPPLY.get(str(src).strip().upper())
        if supply:
            mapping.setdefault(int(pid), supply)
    if mapping:
        register_partial_exit_coal_supply(mapping)


def load_retired_within_window(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
    year: int | None = None,
    vintage_status_scope: bool = False,
    partial_plant_exit_carry: bool = False,
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

    ``vintage_status_scope`` (GATED default-off; miso-188,
    ``ScenarioConfig.retiree_vintage_status_scope``,
    PREREG-miso188-retiree-vintage-status-scope-2026-08-30): the channel
    carries each unit to its FORMAL retirement month, but several plants
    were deactivated years before their paper date and EIA's own
    contemporaneous vintage record says so (Grand Tower 862: OS in
    vintage_2023, CAMPD 0.0 GWh 2022–2024, yet carried in-merit Jan–Apr
    2024). When True and ``year`` is given, a unit is dropped iff its
    status in the latest committed vintage ≤ ``year`` whose operable sheet
    lists it (:func:`_retiree_vintage_status`) is non-``OP``; unlisted
    units fail OPEN (kept), so a retiree the record never marks non-OP
    (Rush Island 6155 — OP, ran through Oct-2024) keeps its window.
    Measured, zero fitted scalars, byte-inert while off.

    ``partial_plant_exit_carry`` (GATED default-off; miso-190,
    ``ScenarioConfig.partial_plant_exit_carry``,
    PREREG-miso190-partial-plant-exit-carry-2026-08-30): widens the
    channel's MEMBERSHIP with the builder's deliberate complement — units
    on the committed raw "Retired and Canceled" sheet with an actual
    retirement in the window whose plant SURVIVES in the operable snapshot
    (:func:`_partial_plant_exit_rows`; Sherco-2 682 MW, ret 2023-12, in a
    surviving three-unit plant). Each carries its own actual retirement in
    ``planned_retirement_*``, which ``cod_ramp.effective_cod`` prefers over
    the plant-collapsed date, so it ages out at unit grain while its plant
    siblings keep running. The union happens BEFORE the vintage-status
    oracle above, so an armed ``vintage_status_scope`` scopes both
    memberships uniformly (Dallman-3, OS in vintage_2023 and CAMPD-dark,
    stays out). Measured, zero fitted scalars, byte-inert while off.
    """
    iso = iso.upper()
    data_dir = active_eia860_dir() if data_dir is None else Path(data_dir)
    if iso_config is None:
        try:
            iso_config = get_iso_config(iso)
        except ValueError:
            iso_config = None

    path = data_dir / EIA_860_RETIRED_WINDOW_PARQUET_NAME
    codes = ba_codes(iso)

    frames: list[pd.DataFrame] = []
    if path.exists():
        whole = _normalize_columns(pd.read_parquet(path))
        if codes and "balancing_authority_code" in whole.columns:
            whole = whole[
                whole["balancing_authority_code"].astype(str).str.strip().isin(codes)
            ]
        if not whole.empty:
            frames.append(whole)

    partial_frame: pd.DataFrame | None = None
    if partial_plant_exit_carry:
        partial = _partial_plant_exit_rows(data_dir, codes)
        if partial is not None and not partial.empty:
            partial_frame = partial
            _register_partial_exit_coal_supply(partial)
            logger.info(
                "partial-plant exit carry (%s): injecting %d unit(s), %.0f MW "
                "— plants %s",
                iso,
                len(partial),
                pd.to_numeric(partial["net_summer_capacity_mw"], errors="coerce")
                .fillna(0.0)
                .sum(),
                sorted(set(partial["plant_id"].astype(int))),
            )
            frames.append(partial)

    if not frames:
        return []
    df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]

    df = df.copy()
    if vintage_status_scope and year is not None:
        codes = pd.to_numeric(df["plant_id"], errors="coerce")
        keep_mask = []
        dropped: list[tuple[int, str, str, float]] = []
        for code, gid, cap in zip(
            codes, df["generator_id"], df.get("net_summer_capacity_mw", codes * 0)
        ):
            if pd.isna(code):
                keep_mask.append(True)
                continue
            st = _retiree_vintage_status(int(code), str(gid), int(year))
            drop = st is not None and st != "OP"
            keep_mask.append(not drop)
            if drop:
                dropped.append((int(code), str(gid).strip(), st, float(cap or 0.0)))
        if dropped:
            logger.info(
                "retiree vintage-status scope (%s %d): dropped %d unit(s), "
                "%.0f MW — %s",
                iso,
                int(year),
                len(dropped),
                sum(d[3] for d in dropped),
                sorted({(d[0], d[1], d[2]) for d in dropped}),
            )
            df = df[pd.Series(keep_mask, index=df.index)]
            if df.empty:
                return []
    df["chp"] = df["plant_id"].map(_chp_by_plant(path.parent, year)).fillna("N")
    generators = _rows_to_generators(df, iso, iso_config)
    if partial_frame is not None:
        # Provenance stamp for the binning-aware exit-cohort routing
        # (miso-191, PREREG-miso191 §1-§2): mark exactly the leg-1
        # partial-exit units, keyed the same way _rows_to_generators keys a
        # unit (plant_code + stripped generator id), so fleet_to_bins can
        # give them their own date-scoped bins. The whole-plant channel and
        # everything else stays unstamped — cohort routing must not touch
        # plants that keep their plant-collapsed COD timing.
        _partial_keys = {
            (int(p), str(g).strip())
            for p, g in zip(partial_frame["plant_id"], partial_frame["generator_id"])
        }
        for g in generators:
            _gid = g.unit_id.split("_", 1)[1].strip() if "_" in g.unit_id else ""
            if (int(g.plant_code), _gid) in _partial_keys:
                g.partial_exit_unit = True
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
    partial_plant_exit_carry: bool = False,
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

    ``partial_plant_exit_carry`` (GATED default-off; miso-190,
    ``ScenarioConfig.partial_plant_exit_carry``,
    PREREG-miso190-partial-plant-exit-carry-2026-08-30) widens the snapshot
    status set from ``{OA}`` to ``{OA, OS, SB}`` — the extension the
    OA-only comment below deliberately reserved for its own probe, which
    that PREREG is. Same vintage-OP oracle, same per-unit vintage-row
    build, same no-``vintage_2025``-carries-nothing owner default. The
    adjudicated case: Big Cajun 2-1 (6055, 517 MW coal) — OS in the
    canonical snapshot so the OP filter drops it from every year, yet OP
    in vintage_2023 AND vintage_2024 with measured 2023/2024 generation;
    Warrick-2 (6705, 126 MW) OP in vintage_2023 only (OA in
    vintage_2024, so 2023-only). Byte-inert while off.

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
    codes = ba_codes(iso)
    if codes and "balancing_authority_code" in snap.columns:
        ba = snap["balancing_authority_code"].astype(str).str.strip()
        snap = snap[ba.isin(codes)]
    status = snap["status"].astype(str).str.strip().str.upper()
    # OA only by default (out of service, expected to return — the mothball
    # status the Cottonwood charter scopes this channel to); OS/SB join the
    # set only under the gated partial-plant exit carry (miso-190), the
    # "own probe" the original boundary comment reserved. Retired statuses
    # never qualify (retired units leave the operable sheet entirely and are
    # the retiree channel's domain).
    scope = {"OA", "OS", "SB"} if partial_plant_exit_carry else {"OA"}
    oa = snap[status.isin(scope)]
    if oa.empty:
        return []

    def _unit_keys(df: pd.DataFrame) -> list[tuple[int, str]]:
        codes = pd.to_numeric(df["plant_id"], errors="coerce").fillna(0)
        gids = df["generator_id"].astype(str).str.strip()
        return [(int(c), g) for c, g in zip(codes, gids)]

    vint = _normalize_columns(pd.read_parquet(vintage_path))
    if "status" not in vint.columns:
        return []
    if codes and "balancing_authority_code" in vint.columns:
        ba = vint["balancing_authority_code"].astype(str).str.strip()
        vint = vint[ba.isin(codes)]
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
    # Stale-COD bound measured from the ACTIVE snapshot's own vintage, not the
    # canonical-2025 constant (FH-1 leak fix, hindcast-forward plan §4 row 2):
    # a vintage_<year> proposed sheet's pipeline lives in <year>+1..<year>+5,
    # so filtering it against the 2025 constant silently zeroed the whole
    # planned-additions channel for every vintage-seeded run. Top-level
    # snapshot resolves to the constant — byte-identical for non-vintage runs.
    df = df[eff_year > operable_vintage_year(data_dir)]
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


def load_procured_vre_additions(
    iso: str,
    iso_config: ISOConfig | None = None,
    data_dir: Path | None = None,
) -> list[dict]:
    """Load EIA-860 construction-committed proposed WIND / SOLAR rows for an ISO.

    The VRE limb of the step-4 known-additions channel (FFR-5E; design
    ``docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md`` §§2-3),
    GATED on ``ScenarioConfig.vre_procurement_additions_enabled`` (default
    OFF) and applied by :func:`evolve_fleet` step 4. The exact sibling of
    :func:`load_planned_additions`, which skips wind and solar because
    ``_map_fuel_type`` returns ``None`` for them: same sheet, same
    :data:`_PLANNED_FIRM_STATUSES`, same BA crosswalk, same vintage gate,
    same lat/lon zone assignment. Wind/solar rows become zonal pool MW
    rather than :class:`Generator` objects, so this returns plain dicts.

    **Rule 13 [R-MEASURED] boundary.** Only ``eia860_generator_proposed.parquet``
    is read — a forward statement of intent, filed *before* the outcome. The
    operable sheet (*the outcome*) is never opened here, for any purpose
    including cross-checks, because deciding what to build from an observed
    ``Operating Year`` would be pasting the answer key in (design §3.1).

    **Three gates, none of them a parameter.**

    * *Instrument* — a row exists only with a construction-committed status
      (:data:`_PLANNED_FIRM_STATUSES`, ``U``/``V``/``TS``), whose instrument
      is the utility's own Form 860 filing. ``P`` (planned, approvals not
      initiated) is announcement-grade and stays excluded, exactly as the
      thermal limb excludes it; the frozenset is *shared*, not copied, so
      the two limbs cannot drift apart.
    * *Information* — only the run's own active vintage directory is read,
      and only rows with ``Effective Year > operable_vintage_year(data_dir)``
      qualify. A run pinned to vintage 2020 can never open the 2021 sheet.
    * *Horizon* — none is imposed here. The pipeline is simply empty past
      roughly ``V+4``, so the channel falls silent and hands the whole job
      back to the economic screen. **The pipeline is never extrapolated
      forward**: an assumed repeat of the last cohort would be a free
      parameter wearing a data costume (design §3.3).

    Technology mapping reuses :data:`market_sim.data.renewables._TECHNOLOGY_TO_FUEL`
    — the repo's already-adjudicated map for *this same sheet* — rather than
    minting a second vocabulary. It covers ``Solar Photovoltaic`` and
    ``Onshore Wind Turbine``; offshore wind and solar thermal are therefore
    out of scope for this limb, which makes it build *less* (the safe
    direction, and the same posture as the U/V/TS status choice). Extending
    the map is a separate decision with its own evidence, not a widening this
    lane may take.

    Args:
        iso: ISO identifier, e.g. ``"MISO"``.
        iso_config: Topology configuration; fetched via
            :func:`get_iso_config` when ``None``.
        data_dir: Directory holding the processed EIA-860 parquets.
            Defaults to the active (vintage-aware) snapshot directory.

    Returns:
        One dict per qualifying row, sorted by ``(online_year, plant_id,
        generator_id)``, with keys ``zone``, ``tech`` (``"wind"``/``"solar"``),
        ``online_year``, ``mw``, ``plant_id`` and ``generator_id``. Empty when
        the proposed or plant parquet is missing (logged), or nothing
        qualifies -- including every year past the data horizon, which is
        correct behaviour rather than a fault.
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
            "procured VRE additions unavailable for %s: missing %s",
            iso,
            proposed_path.name if not proposed_path.exists() else plant_path.name,
        )
        return []

    # The adjudicated proposed-sheet technology map, imported rather than
    # duplicated so a future edit cannot leave the two readers disagreeing
    # about what "solar" means on the same file.
    from market_sim.data.renewables import _TECHNOLOGY_TO_FUEL, get_renewable_zone

    df = pd.read_parquet(proposed_path)
    plants = pd.read_parquet(plant_path)[
        ["Plant Code", "Balancing Authority Code", "Latitude", "Longitude"]
    ].drop_duplicates("Plant Code")
    df = df.merge(plants, on="Plant Code", how="left")

    ba_iso = df["Balancing Authority Code"].map(BA_CODE_TO_ISO)
    df = df[ba_iso == iso]
    tech = df["Technology"].map(_TECHNOLOGY_TO_FUEL)
    df = df[tech.notna()]
    if df.empty:
        return []
    status = df["Status"].astype(str).str.strip().str.upper()
    df = df[status.isin(_PLANNED_FIRM_STATUSES)]
    eff_year = pd.to_numeric(df["Effective Year"], errors="coerce")
    # The information gate, measured from the ACTIVE snapshot's own vintage
    # (never the canonical-2025 constant) — the same FH-1 leak fix the thermal
    # limb carries, for the same reason.
    df = df[eff_year > operable_vintage_year(data_dir)]
    if df.empty:
        return []

    from market_sim.data.zone_assignment import assign_zone_by_coords

    rows: list[dict] = []
    _cols = [
        "Plant Code",
        "Generator ID",
        "Technology",
        "Nameplate Capacity (MW)",
        "Effective Year",
        "Latitude",
        "Longitude",
    ]
    # Positional itertuples (name=None): the EIA-860 headers carry spaces and
    # parentheses, which named tuples would mangle — the same convention the
    # renewables loader uses on this file.
    for code_v, gid_v, tech_v, cap_v, year_v, lat_v, lon_v in df[_cols].itertuples(
        index=False, name=None
    ):
        mw = _to_float(cap_v)
        online_year = _to_float(year_v)
        fuel = _TECHNOLOGY_TO_FUEL.get(str(tech_v).strip())
        if mw is None or mw <= 0.0 or online_year is None or fuel is None:
            continue
        lat = _to_float(lat_v)
        lon = _to_float(lon_v)
        # Sited from the plant's own coordinates — procured MW lands in the
        # zone it is actually being built in, NOT the single
        # RENEWABLE_ZONE_ALLOCATION bucket the economic screen forces every MW
        # into (design §2.2; FFR-3V §4.4). That bucket remains the fallback for
        # a row with no usable coordinates, so the MW is never dropped.
        zone = None
        if lat is not None and lon is not None:
            try:
                zone = assign_zone_by_coords(lat, lon, iso)
            except Exception:  # zone rules missing for the ISO: fall back
                zone = None
        if zone is None:
            try:
                zone = get_renewable_zone(iso, fuel)
            except KeyError:  # no allocation entry for this ISO/fuel
                continue
        code = _to_float(code_v)
        rows.append(
            {
                "zone": zone,
                "tech": fuel,
                "online_year": int(online_year),
                "mw": float(mw),
                "plant_id": int(code) if code is not None else None,
                "generator_id": str(gid_v).strip(),
            }
        )

    if not rows:
        return []
    rows.sort(key=lambda r: (r["online_year"], r["plant_id"] or 0, r["generator_id"]))
    logger.info(
        "%s procured VRE additions: %d rows, %.0f MW (wind %.0f / solar %.0f), %d-%d",
        iso,
        len(rows),
        sum(r["mw"] for r in rows),
        sum(r["mw"] for r in rows if r["tech"] == "wind"),
        sum(r["mw"] for r in rows if r["tech"] == "solar"),
        min(r["online_year"] for r in rows),
        max(r["online_year"] for r in rows),
    )
    return rows


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


def _eia860_plant_sector() -> dict[int, int]:
    """Return ``{plant_code: EIA-860 Sector number}`` from the plant table.

    Vintage-keyed shim over :func:`_eia860_plant_sector_cached` (SPP-38): the
    active EIA-860 directory enters the cache key so a span run that moves the
    vintage between years cannot serve year 1's table to years 2+ (rule 14
    ``[R-ACCURATE]``).
    """
    return _eia860_plant_sector_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _eia860_plant_sector_cached(eia860_dir: str) -> dict[int, int]:
    """Directory-keyed cache behind :func:`_eia860_plant_sector`.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key.
    """
    path = Path(eia860_dir) / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Sector"])
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


def eia860_plant_states() -> dict[int, str]:
    """Vintage-keyed shim over :func:`_eia860_plant_states_cached` (SPP-38).

    See that function for the contract. The active EIA-860 directory enters the
    cache key here so the docstring's own promise — "a vintage switch is
    honoured" — holds across a span run as well as a single-year one (rule 14
    ``[R-ACCURATE]``).
    """
    return _eia860_plant_states_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _eia860_plant_states_cached(eia860_dir: str) -> dict[int, str]:
    """Return ``{plant_code: USPS state}`` from the EIA-860 plant table.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the :func:`eia860_plant_states` shim,
    which supplies the active vintage.

    The measured plant-location source for ``Generator.state`` on the
    CAMPD-bin / plant-level fleet path (``ScenarioConfig.fleet_state_from_eia860``,
    caiso-243): ``bins_to_fleet`` built every generator without a state, so
    the F923 fallback's state-first donor tier was unreachable on every
    plant-level fleet. Plants absent from the table (or with a null state)
    are omitted and keep the empty string, i.e. the zonal tier as before.
    Resolves through :func:`paths.active_eia860_dir` like the sibling
    plant-table readers, so a vintage switch is honoured.
    """
    path = Path(eia860_dir) / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "State"])
    df = df.dropna(subset=["Plant Code", "State"])
    return {
        int(c): str(s).strip().upper()
        for c, s in zip(df["Plant Code"], df["State"])
        if str(s).strip()
    }


def eia860_plant_sectors(eia860_dir: Path | None = None) -> dict[int, int]:
    """Return ``{plant_code: EIA-860 Sector}`` from the plant table at a vintage.

    The per-plant ownership-sector attribute the retirement-screen sector gate
    partitions on (capx D53, ``ScenarioConfig.retirement_sector_gate``;
    ``docs/handoffs/DESIGN-capx-d53-sector-gate-2026-09-05.md`` §1.2, §1.10):
    Form EIA-860 Schedule 2 ``Sector`` — 1 Electric Utility, 2 IPP Non-CHP,
    3 IPP CHP, 4 Commercial Non-CHP, 5 Commercial CHP, 6 Industrial Non-CHP,
    7 Industrial CHP. Resolves through :func:`paths.active_eia860_dir` when
    ``eia860_dir`` is not given, so a hindcast reads the vintage it initialised
    from (the information gate: a post-vintage sale that re-sectors a plant is
    not visible in a vintage-pinned run — the same gate step 0 applies to
    ``instrument_date``), and defers to the directory-keyed cache below —
    unlike the sibling :func:`_eia860_plant_sector` (``maxsize=1``, no
    directory key, kept unchanged for its own consumer ``data.coal``), a
    vintage switch after first use is honoured here. Plants absent from the
    table (or with a null sector) are omitted; the gate treats them as
    unknown and fails OPEN to the screen.
    """
    return _eia860_plant_sectors(
        Path(eia860_dir) if eia860_dir is not None else active_eia860_dir()
    )


@lru_cache(maxsize=4)
def _eia860_plant_sectors(eia860_dir: Path) -> dict[int, int]:
    """Directory-keyed cache behind :func:`eia860_plant_sectors`."""
    path = Path(eia860_dir) / "eia860_plant.parquet"
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["Plant Code", "Sector"])
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


def eia860_regulated_plants() -> frozenset[int]:
    """Vintage-keyed shim over :func:`_eia860_regulated_plants_cached` (SPP-38).

    See that function for the contract; the active EIA-860 directory enters the
    cache key so a span run that moves the vintage between years cannot serve
    year 1's table to years 2+ (rule 14 ``[R-ACCURATE]``).
    """
    return _eia860_regulated_plants_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _eia860_regulated_plants_cached(eia860_dir: str) -> frozenset[int]:
    """Return the plant codes whose EIA-860 ``Regulatory Status`` is ``RE``.

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the :func:`eia860_regulated_plants` shim,
    which supplies the active vintage.

    The EIA-860 plant table carries a two-value ``Regulatory Status`` flag —
    ``RE`` (the operator's rates are regulated / cost-of-service recovered)
    vs ``NR`` (non-regulated merchant/IPP). This is the measured
    regulated-vs-merchant conduct split the MISO SOM Table 7 reports its
    coal self-commitment statistics on (``coal_committed_takeorpay_regulated``);
    plants absent from the table (or with a null flag) are conservatively
    treated as non-regulated (no committed-band discount).
    """
    path = Path(eia860_dir) / "eia860_plant.parquet"
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


def eia860_costofservice_majority_plants() -> frozenset[int]:
    """Vintage-keyed shim over :func:`_eia860_costofservice_majority_plants_cached`.

    SPP-38. See that function for the contract; the active EIA-860 directory
    enters the cache key so a span run that moves the vintage between years
    cannot serve year 1's Schedule-4 ownership to years 2+ (rule 14
    ``[R-ACCURATE]``).
    """
    return _eia860_costofservice_majority_plants_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _eia860_costofservice_majority_plants_cached(eia860_dir: str) -> frozenset[int]:
    """Plant codes majority-owned by cost-of-service entities (Schedule 4).

    ``eia860_dir`` is BOTH the cache key and the directory read, so a stale
    global can never desync from the key. Call through the
    :func:`eia860_costofservice_majority_plants` shim.

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
    d = Path(eia860_dir)
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


def eia860_selfcommit_scope_plants() -> frozenset[int]:
    """Vintage-keyed shim over :func:`_eia860_selfcommit_scope_plants_cached`.

    SPP-38. Both legs of the union are themselves vintage-dependent, so this
    composition has to carry the directory in its key as well — otherwise it
    would pin year 1's union even with repaired inputs. (The SPP-37 census read
    this row "stable" across SPP's three vintages; that is a property of the
    data, not of the construction, and the repair does not rest on it.)
    """
    return _eia860_selfcommit_scope_plants_cached(str(active_eia860_dir()))


@lru_cache(maxsize=4)
def _eia860_selfcommit_scope_plants_cached(eia860_dir: str) -> frozenset[int]:
    """The ``coal_committed_takeorpay_regulated`` scope set.

    ``eia860_dir`` is a **cache key only** — both legs below resolve the active
    vintage themselves. Call through the :func:`eia860_selfcommit_scope_plants`
    shim.

    Union of the two measured cost-of-service legs: EIA-860 ``Regulatory
    Status`` RE operators (:func:`eia860_regulated_plants`) and plants
    majority-owned by cost-of-service entities
    (:func:`eia860_costofservice_majority_plants`). See
    docs/handoffs/miso-coal-conduct-design-2026-07.md §4 (the pre-declared
    V1b refinement, engaged when the RE-only probe broke the 2023 COAL_BIT
    band on the Prairie State reversion).
    """
    del eia860_dir  # cache-key only; both legs resolve the vintage themselves
    return eia860_regulated_plants() | eia860_costofservice_majority_plants()


# Per-bin forced availability derates by year, for confirmed unit losses
# that the age-based THERMAL_AVAILABILITY model cannot anticipate (turbine
# fires, boiler explosions, etc.). Keyed by ``Bin_Label`` and SOLVE year, the
# value is a flat multiplier on the bin's availability for the whole year.
#
# BACKCAST-ONLY (FR-8, rule 13 [R-MEASURED]): every read site is gated on
# ``mode == "backcast"`` (arrays.py ``_availability_matrix``; the DAM-overlay
# ceiling reads sit inside the already-mode-gated
# ``ercot_thermal_dam_availability`` block). A measured single-event derate
# has no forward analogue, so it must never reach a forecast or crossover
# year — pre-gate, the T1-X harness's pinned ``weather_year=2025`` re-applied
# the Martin Lake fire to every crossover solve year.
#
# RULE 24 [R-REGISTRY] STATUS: this dict is an off-registry per-plant tuning
# channel and is being retired entry by entry as each event finds its proper
# measured or registry home. Two are already gone (see below). Do NOT add to
# it -- route new events to the measured outage overlay
# (data/raw/campd-unit-outages.csv) or the confirmed-retirement registry.
BIN_FORCED_DERATE_BY_YEAR: dict[str, dict[int, float]] = {
    # Martin Lake -- turbine fire and boiler explosion took unit 1 out of
    # commission for 2025 (1 of 3 units, ~33% nameplate loss).
    #
    # RETAINED, and checked rather than assumed (ercot132 follow-up): the
    # measured overlay does NOT carry this event. campd-unit-outages.csv has
    # 2025 rows for Martin Lake units 2 and 3 only (five short maintenance
    # outages, 5.0-18.2 days); there is no unit-1 row at all, because a unit
    # destroyed before the year starts never produces the run/stop transition
    # the outage derive detects. Deleting this entry would hand the 2025 fleet
    # back ~793 MW of capacity that physically did not exist.
    # TO RETIRE IT: give the outage derive a way to represent a unit absent for
    # a whole vintage (or add the event to a registry), then delete this line.
    "N_COAL4": {2025: 0.67},
    # V H Braunig -- CPS Energy retired ST units 1 (225 MW) and 2 (252 MW)
    # in early 2025 (March). Handled via confirmed-exit registry injection
    # (data/raw/confirmed-retirements/ercot.csv, plant 3612) with
    # month-level precision: (3/12 * 1.0) + (9/12 * 661/1138) = 0.686.
    # Removed from hardcode 2026-07-06 per rule 24 (no off-registry tuning).
    #
    # Sandy Creek (56611, SC_COAL3) -- REMOVED 2026-07-28 (owner decision, the
    # ercot132 D2/D3 resolution). The entry set availability to 0.0 for all
    # 8,760 hours of 2025 while its own justifying comment cited EIA-923
    # showing 0.72 TWh GENERATED -- self-refuting, and the sole cause of the
    # ERCOT-130 §6 finding (model 0.000 TWh against CAMPD 1,300 running hours /
    # 0.697 TWh / 895 MW peak). The measured overlay already carries the event
    # correctly and needs no hardcode: campd-unit-outages.csv has Sandy Creek
    # S01 out 2025-01-22..01-29 and 2025-02-28..12-31 (306 days), leaving 1,246
    # available hours against the 1,300 hours CAMPD observed it running.
    # Deleting the line is what lets that measured signal through (rules 14/24).
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
