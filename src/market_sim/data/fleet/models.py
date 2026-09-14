"""Leaf of the :mod:`market_sim.data.fleet` package (absorbs 3E ``fleet_models``).

Physically holds the pre-split module-level constants and clean-seam helpers
every submodule shares (fuel-type codes, EIA-860 artifact names, BA/ISO maps,
the clean-read gate, the non-leap month index), so submodules can import them
WITHOUT a module-level edge back to the package (`the ``data/fuel``
``_shared`` pattern; tests/test_persisted_identity.py
``test_no_module_level_import_cycles``).

:class:`Generator` and :class:`FleetArrays` are NOT defined here: the
committed ``p2_state`` pickles resolve both classes by
``__module__ == "market_sim.data.fleet"`` (pinned by
``tests/test_persisted_identity.py``), so they are defined physically in the
package ``__init__`` and this leaf resolves them lazily via PEP-562
``__getattr__`` — a from-import of either name through this module works at
call/import time with no import-time cycle. :func:`_pkg_ns` is the call-time
package-namespace resolver that keeps historical monkeypatch / ``mock.patch``
targets on ``market_sim.data.fleet`` intercepting package internals.
"""

from __future__ import annotations

import calendar
import os
from pathlib import Path

import numpy as np


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


def operable_vintage_year(data_dir: "Path | None" = None) -> int:
    """Return the operable-snapshot vintage year of an EIA-860 directory.

    The vintage-aware replacement for reading :data:`EIA860_OPERABLE_VINTAGE`
    directly (FH-1, ``docs/hindcast-forward-plan-2026-07.md`` §4 row 2): a
    ``vintage_<year>/`` directory IS the ``<year>`` operable snapshot, so every
    consumer that bounds itself by "the snapshot vintage" — the
    planned-additions ``Effective Year`` filter, the renewables
    proposed-capacity augmentation, the announced-retirement data horizon —
    must bound by the ACTIVE vintage, not the canonical-snapshot constant.
    (The hardcoded constant silently discarded essentially every unit of a
    2020/2021/2023 vintage's own proposed sheet: ``eff_year > 2025`` against a
    sheet whose pipeline lives in 2021-2025.)

    Args:
        data_dir: EIA-860 directory to resolve. ``None`` resolves the active
            dir (:func:`market_sim.config.paths.active_eia860_dir`, which
            honors a ``ScenarioConfig.eia860_vintage_year`` switch).

    Returns:
        The ``<year>`` of a ``vintage_<year>/`` directory, else
        :data:`EIA860_OPERABLE_VINTAGE` (the canonical top-level snapshot) —
        so every non-vintage run is byte-identical to the pre-FH-1 constant.
    """
    if data_dir is None:
        from market_sim.config.paths import active_eia860_dir

        data_dir = active_eia860_dir()
    name = Path(data_dir).name
    if name.startswith("vintage_"):
        try:
            return int(name.split("_", 1)[1])
        except ValueError:
            pass
    return EIA860_OPERABLE_VINTAGE


def _clean_fleet_year(data_dir: Path) -> int:
    """Map an active EIA-860 vintage directory to its clean ``fleet`` partition.

    The clean ``fleet`` datatype is partitioned by EIA-860 vintage year
    (``data/clean/fleet/fleet_<year>.parquet``): a ``vintage_<year>/`` directory
    curates to ``year`` and the top-level snapshot curates to
    :data:`EIA860_OPERABLE_VINTAGE`. Resolving the active dir
    (:func:`paths.active_eia860_dir`, which honors a
    ``ScenarioConfig.eia860_vintage_year`` switch) to that year is what lets the
    clean fleet read preserve the EIA-860 vintage behavior of the raw loaders —
    selecting ``vintage_2023`` routes the clean read to ``fleet_2023``. Same
    dir→year mapping as :func:`operable_vintage_year` (the shared FH-1
    pattern), kept as its own name for the clean-partition semantics.
    """
    return operable_vintage_year(Path(data_dir))


# Vintage year of the CANONICAL operable EIA-860 snapshot behind the committed
# generators parquet: units online through this year are in the operable
# schedule. Proposed rows whose Effective Year is at or before it are
# stale (slipped projects with a past-dated COD), so the planned-additions
# loader and the renewables proposed-capacity augmentation both skip them
# rather than trust an effective date the snapshot has already overtaken.
# Bump this whenever process_eia860.py regenerates the parquets from a
# newer release. Source: EIA-860 2025 Early Release (eia8602025ER.zip,
# operating years through 2025).
# CONSUMERS: never read this constant directly where a vintage-seeded run
# (``ScenarioConfig.eia860_vintage_year``) can be active — resolve the ACTIVE
# snapshot's vintage via :func:`operable_vintage_year` instead (FH-1 leak fix:
# a ``vintage_<year>/`` dir's own proposed sheet was filtered against this
# 2025 constant and silently zeroed). This constant remains the top-level
# snapshot's vintage and the fallback for non-vintage runs.
EIA860_OPERABLE_VINTAGE: int = 2025


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

# EIA-930 balancing-authority code → model region name. Seven regions are one
# balancing authority each (the wholesale markets with EIA-930 demand data);
# NWPP is a POOL of seventeen balancing authorities under one key — the first
# many-to-one entry in this map (registered 2026-09-14, lane NWPP-20; owner
# ruling N1, docs/multi-iso/nwpp-addition-plan-2026-09.md §3). The map stays
# many-to-one safe everywhere it is read (``.map`` / ``.isin`` / membership);
# the ISO -> BA direction is ``ISO_TO_BA_CODES`` below, NOT a scalar inverse.
# EIA-930 balancing-authority code → registry name, for the eight registered
# regions that have EIA-930 demand data (seven wholesale markets plus the
# SOCO balancing authority).
BA_CODE_TO_ISO: dict[str, str] = {
    "ERCO": "ERCOT",
    "CISO": "CAISO",
    "PJM": "PJM",
    "MISO": "MISO",
    "NYIS": "NYISO",
    "ISNE": "NEISO",
    # SPP = balancing authority SWPP (registered 2026-09-06, lane SPP-20;
    # docs/multi-iso/00-iso-addition-protocol.md Stage B).
    "SWPP": "SPP",
    # NWPP = the seventeen EIA-860 / EIA-930 balancing authorities of the
    # Northwest Power Pool footprint (owner ruling N1, 2026-09-13): the
    # Hermiston provenance is the illustration — plant 54761 (Hermiston
    # Generating) files under PACW and plant 55328 (Hermiston Power
    # Partnership) under GRID, two BAs one fence apart. AVRN and GRID are
    # generation-only members (no demand in any hour); Canada (BCHA, AESO)
    # is OUT — inside the real pool, outside EIA-930. Census at registration:
    # 939 plants / 1,930 operable generators / 98,238.1 MW after the NERC
    # admission predicate (ISO_NERC_REGION_ADMISSION) — docs/multi-iso/
    # nwpp-data-audit.md §2.1, §2.8(a).
    "BPAT": "NWPP",
    "PACE": "NWPP",
    "PACW": "NWPP",
    "PGE": "NWPP",
    "PSEI": "NWPP",
    "AVA": "NWPP",
    "IPCO": "NWPP",
    "NWMT": "NWPP",
    "CHPD": "NWPP",
    "DOPD": "NWPP",
    "GCPD": "NWPP",
    "SCL": "NWPP",
    "TPWR": "NWPP",
    "AVRN": "NWPP",
    "GRID": "NWPP",
    "WAUW": "NWPP",
    "NEVP": "NWPP",
    # SOCO = the Southern Company balancing authority itself (Southern
    # Company Services, Inc. - Trans; NERC SERC) — the one region here that is
    # NOT an ISO, so the BA code and the registry key are the same string.
    # 335 plants / 786 operable generators / 70,665.7 MW after the audit's
    # §2.6(a) MA rejection (docs/multi-iso/soco-data-audit.md §2.2).
    # Registered 2026-09-14 by lane SOCO-20.
    "SOCO": "SOCO",
}

# Model region -> tuple of EVERY balancing-authority code it comprises, in
# BA_CODE_TO_ISO insertion order. THIS is the ISO -> BA direction every
# consumer filters on (``.isin(ba_codes(iso))``), because a scalar inverse of
# a many-to-one map keeps whichever code was inserted last and silently
# returns 1/17 of a pool (NWPP-10 §3: thirteen ``==`` call sites failed
# silently that way before this table existed).
ISO_TO_BA_CODES: dict[str, tuple[str, ...]] = {}
for _ba, _iso in BA_CODE_TO_ISO.items():
    ISO_TO_BA_CODES[_iso] = ISO_TO_BA_CODES.get(_iso, ()) + (_ba,)
del _ba, _iso

# Scalar inverse of BA_CODE_TO_ISO for the 1:1 regions ONLY. A pool region
# (NWPP) deliberately has NO entry here, so ``ISO_TO_BA_CODE.get("NWPP")``
# is ``None`` rather than an arbitrary member — a consumer that still keys on
# this table reads "no single BA" instead of one seventeenth of the fleet.
# Solve-path consumers read ``ba_codes`` / ``ISO_TO_BA_CODES``; this table
# survives for the historical probes and the 1:1 fast paths.
ISO_TO_BA_CODE: dict[str, str] = {
    iso: codes[0] for iso, codes in ISO_TO_BA_CODES.items() if len(codes) == 1
}

# The NWPP footprint as a tuple, for callers that need the pool's member set
# by name (the EIA-930 pool frame, the zone map, the tests).
NWPP_BAS: tuple[str, ...] = ISO_TO_BA_CODES["NWPP"]

# Footprint ADMISSION PREDICATE by NERC region, per region. A plant whose
# EIA-860 ``Balancing Authority Code`` maps to the region is admitted only when
# its ``NERC Region`` equals the listed value; regions absent here admit on the
# BA code alone (the seven 1:1 regions, byte-identical to before). NWPP needs
# it because the BA-code field is respondent-entered: plant 68906 (Pine Forest
# Solar I, Hopkins County TX, NERC TRE, 500.0 MW) files under DOPD, a
# Washington PUD that cannot balance a resource in ERCOT — the Western
# Interconnection and ERCOT are asynchronously separated, so the key is
# dispositive on physics (NWPP-10 §1.2 / audit §2.8(a)). It is a REGISTRY
# predicate, never a per-plant exclusion (rule 24 [R-REGISTRY]). It also does
# real work for WAUW, which straddles the Eastern/Western seam through eastern
# Montana (Sand Creek Wind, 60595, NERC MRO — canceled, inert today).
ISO_NERC_REGION_ADMISSION: dict[str, str] = {"NWPP": "WECC"}


def ba_codes(iso: str) -> tuple[str, ...]:
    """Return every EIA balancing-authority code the region ``iso`` comprises.

    ``()`` for a region with no EIA-930 balancing authority registered, so a
    caller filtering with ``.isin(ba_codes(iso))`` selects nothing rather than
    everything. Case-insensitive on ``iso``.
    """
    return ISO_TO_BA_CODES.get(iso.upper(), ())


def footprint_plant_mask(iso: str, ba_code, nerc_region=None):
    """Return the boolean mask of plants admitted to ``iso``'s footprint.

    ``ba_code`` is a pandas Series of EIA balancing-authority codes and
    ``nerc_region`` the matching Series of EIA-860 ``NERC Region`` values (or
    ``None`` when the frame carries none). A plant is admitted when its BA code
    is one of :func:`ba_codes` AND, where :data:`ISO_NERC_REGION_ADMISSION`
    names a region for ``iso`` and the NERC column is available, its NERC
    region equals it. For the 1:1 regions the second key never applies, so the
    mask is exactly the pre-existing ``== code`` selection.
    """
    mask = ba_code.astype(str).str.strip().isin(ba_codes(iso))
    required = ISO_NERC_REGION_ADMISSION.get(iso.upper())
    if required is not None and nerc_region is not None:
        mask &= nerc_region.astype(str).str.strip() == required
    return mask


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

# Prime-mover FAMILIES for the eGRID family heat-rate construction (nyiso-184,
# ``ScenarioConfig.egrid_family_heat_rates``). eGRID keys its per-unit heat
# input (``UNT<yy>.HTIAN``) and per-generator net generation
# (``GEN<yy>.GENNTAN``) on the same ``PRMVR`` codes EIA-860 carries as
# ``prime_mover``, so one map serves both sides of the join. A combined cycle
# is one family whatever half of it a row is (the CT burns the fuel, the CA
# makes power from its exhaust); simple-cycle turbines and reciprocating
# engines are one family (a single combustion path each); steam is its own.
# The construction is the measured replacement for MIXED_FACILITY_STEAM_HR's
# hand number at the plants it covers (PREREG-nyiso184 §1, §3 R1).
EGRID_PRIME_MOVER_FAMILIES: dict[str, frozenset[str]] = {
    "ST": frozenset({"ST"}),
    "CC": frozenset({"CT", "CA", "CS", "CC"}),
    "GT": frozenset({"GT", "IC"}),
}


def egrid_prime_mover_family(prime_mover: object) -> str | None:
    """Return the :data:`EGRID_PRIME_MOVER_FAMILIES` key for a prime-mover code.

    ``None`` for a code no family claims (hydro, wind, PV, storage, fuel
    cells, ...), so those rows never enter a family sum.

    Args:
        prime_mover: An eGRID ``PRMVR`` or EIA-860 ``prime_mover`` code.

    Returns:
        ``"ST"``, ``"CC"``, ``"GT"`` or ``None``.
    """
    code = str(prime_mover or "").strip().upper()
    for family, codes in EGRID_PRIME_MOVER_FAMILIES.items():
        if code in codes:
            return family
    return None


def _pkg_ns():
    """Return the package namespace (:mod:`market_sim.data.fleet`) at call time.

    The package holds the exact import path of the pre-split module, so every
    historical ``monkeypatch.setattr("market_sim.data.fleet.<name>", ...)``,
    ``mock.patch("market_sim.data.fleet.<name>")`` and direct
    ``fleet.<name> = ...`` attribute write lands on the package namespace.
    Package internals resolve the historically patched names through it AT
    CALL TIME so those patches keep intercepting the lookups — the pre-split
    module-global semantics. Routed names (2026-07 census union):
    ``load_cod_map``, ``mixed_fossil_plants``, ``cc_summer_derate_ratio``,
    ``coal_summer_derate_ratio``, ``thermal_tranche_p25_level``,
    ``thermal_tranche_online_frac``, ``load_campd_bins``,
    ``load_fleet_from_csv``, ``fleet_to_bins``, ``bins_to_fleet``,
    ``aggregate_fleet``, ``campd_tranche_fuel_frac``,
    ``apply_plant_emission_rates``, ``_cache_binned_fleet``, ``EIA_860_DIR``,
    ``_cc_demonstrated_peaks``, ``COAL_MUSTRUN_BY_PLANT``,
    ``apply_plant_emission_rates_v2``.
    """
    import market_sim.data.fleet as fleet

    return fleet


def __getattr__(name: str):
    """PEP 562 lazy re-export of the package-defined data-model types."""
    if name in ("Generator", "FleetArrays"):
        return getattr(_pkg_ns(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
