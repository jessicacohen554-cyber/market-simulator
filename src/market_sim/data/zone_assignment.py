"""Geographic zone assignment using eGRID 2023 plant-level data.

Maps each generator's ORIS plant code to a model zone using latitude,
longitude, and FIPS county codes from the EPA eGRID database. This
replaces the count-proportional zone allocation that mis-distributes
capacity when the generator list order doesn't match zone geography.

Source: EPA eGRID 2023 (rev 2), PLNT23 sheet.

Note: if the eGRID file is updated, delete the cached binned-fleet
parquets (``data/raw/_processed-legacy/*_fleet_binned.parquet``) so they are
regenerated with zone assignments derived from the new data.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import (
    CAISO_FSNO_SUBZONE_CSV,
    CAISO_HUB_MEMBERSHIP_CSV,
    CAMPD_BINS_CSV,
    EIA_860_DIR,
    FLEET_DIR,
)
from market_sim.data.egrid_sheets import read_egrid_sheet
from market_sim.data.local_capacity import (
    BOUNDARY_LAT_MAX as _LA_BASIN_BOUNDARY_LAT_MAX,
)
from market_sim.data.local_capacity import (
    BOUNDARY_LON_MAX as _LA_BASIN_BOUNDARY_LON_MAX,
)

logger = logging.getLogger(__name__)


def _use_clean() -> bool:
    """Whether to read curated clean parquet instead of the raw inputs.

    Gated by the ``MARKET_SIM_USE_CLEAN`` environment variable, **default OFF**.
    When unset or falsey the module reads raw inputs exactly as before; when
    truthy the reference crosswalks are read through the frozen clean seam
    (:func:`scripts.lib.clean_io.read_clean`). The flag only chooses the data
    *source* — the clean table is curated from the same raw file, so the
    resolved lookup is identical either way (see ``tests/test_consume_reference``).
    """
    return os.environ.get("MARKET_SIM_USE_CLEAN", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


# eGRID 2023 plant-level workbook (from the central path registry).
_EGRID_PATH: Path = FLEET_DIR / "egrid2023_data_rev2.xlsx"

# EIA-860 plant file — current plant coordinates and balancing-authority
# codes. Used to zone plants too new for the eGRID 2023 vintage.
_EIA860_PLANT_PATH: Path = EIA_860_DIR / "eia860_plant.parquet"

# Model ISO name → eGRID balancing-authority code (BACODE column).
_ISO_TO_BA_CODE: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "MISO": "MISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
    # SPP = balancing authority SWPP (EIA-860 ``Balancing Authority Code`` and
    # eGRID BACODE alike); 715 plants / 1,646 operable generators / 103,330.8
    # MW at the EIA-860 2025 Early Release (docs/multi-iso/spp-data-audit.md
    # §2.2). Registered 2026-09-06 by lane SPP-20.
    "SPP": "SWPP",
}

# NWPP (registered 2026-09-14, lane NWPP-20; owner rulings N1 + N5). NWPP is
# a POOL of seventeen balancing authorities, so it has NO entry in the scalar
# map above — its zones are WHOLE-BA GROUPS keyed on the EIA-860 / eGRID
# balancing-authority code, NEVER on state or coordinates: a state here holds
# several BAs (Washington: BPAT, PSEI, SCL, TPWR, CHPD, DOPD, GCPD, AVRN) and
# a BA holds several states (PACE: UT, WY, ID; BPAT: WA, OR, ID, MT, NV). There
# is no EIA-930 sub-BA product for any of the 17, so a zone may not split a
# BA (plan §7 gate G18); the state-keyed ``_SPP_STATE_ZONES`` is the WRONG
# shape and is deliberately not copied. Five ruled zones (plan §3 card N5,
# 2024 Adjusted load shares in docs/multi-iso/nwpp-data-audit.md §9.2):
#   NWPP-NW     BPAT PSEI SCL TPWR CHPD DOPD GCPD  + AVRN generation (37.4 %)
#   NWPP-OR     PGE PACW                           + GRID generation (15.1 %)
#   NWPP-INLAND IPCO AVA NWMT WAUW                                   (15.3 %)
#   NWPP-EAST   PACE                                                 (18.1 %)
#   NWPP-SNV    NEVP                                                 (14.1 %)
# AVRN and GRID serve zero load in every hour of 2023-2025 (NWPP-10 §2 item
# 4) and are placed by geography: AVRN's Columbia-Gorge wind/solar (Klondike,
# Leaning Juniper, Montague, Klamath) and GRID's Hermiston Power sit on the
# NW/OR boundary, the one boundary WECC rates no path for. Declared open,
# not hidden (card N5): GCPD's placement is disputed by load correlation (0.90
# with IPCO, 0.08-0.16 with its own zone) and stays, because load correlation
# is not a transmission constraint. The membership set equals
# ``market_sim.data.fleet.models.NWPP_BAS`` (pinned by test).
_NWPP_BA_ZONES: dict[str, str] = {
    "BPAT": "NWPP-NW",
    "PSEI": "NWPP-NW",
    "SCL": "NWPP-NW",
    "TPWR": "NWPP-NW",
    "CHPD": "NWPP-NW",
    "DOPD": "NWPP-NW",
    "GCPD": "NWPP-NW",
    "AVRN": "NWPP-NW",
    "PGE": "NWPP-OR",
    "PACW": "NWPP-OR",
    "GRID": "NWPP-OR",
    "IPCO": "NWPP-INLAND",
    "AVA": "NWPP-INLAND",
    "NWMT": "NWPP-INLAND",
    "WAUW": "NWPP-INLAND",
    "PACE": "NWPP-EAST",
    "NEVP": "NWPP-SNV",
}

# NWPP footprint admission predicate (audit §2.8(a); registry form in
# ``fleet.models.ISO_NERC_REGION_ADMISSION``): a plant carrying a footprint BA
# code is admitted only when its NERC region is WECC — the Western
# Interconnection and ERCOT are asynchronously separated, so a Washington PUD
# (DOPD) cannot balance Pine Forest Solar I (68906, Hopkins County TX, TRE).
_NWPP_NERC_REGION: str = "WECC"


def _iso_ba_codes(iso: str) -> tuple[str, ...]:
    """Return every balancing-authority code ``iso`` comprises (``()`` if none).

    The 1:1 regions read their scalar ``_ISO_TO_BA_CODE`` entry (so ``isin``
    over the one-element tuple selects exactly the rows ``==`` selected); NWPP
    returns its seventeen members. A pool region must never be reduced to one
    arbitrary code (NWPP-10 §3).
    """
    if iso == "NWPP":
        return tuple(_NWPP_BA_ZONES)
    code = _ISO_TO_BA_CODE.get(iso)
    return (code,) if code is not None else ()


def _nwpp_admitted(ba: pd.Series, nerc: pd.Series | None) -> pd.Series:
    """Boolean mask of rows admitted to the NWPP footprint (BA ∈ map AND WECC)."""
    mask = ba.isin(_NWPP_BA_ZONES)
    if nerc is not None:
        mask &= nerc.astype(str).str.strip() == _NWPP_NERC_REGION
    return mask


# ISOs modeled as a single zone, with that zone's name. Every current ISO now
# has a multi-zone topology, so this is empty; the mechanism stays in place for
# any future single-zone ISO.
_SINGLE_ZONE: dict[str, str] = {}

# Largest-load-share zone per multi-zone ISO, used as the defensive
# fallback when a plant's ORIS code is not present in the eGRID lookup. CAISO
# is pinned to SP15_rest, NOT its largest-load-share zone: post-split, SP15
# is three sub-zones (LA_BASIN 0.374, SDGE 0.091, SP15_rest 0.0735 — SP15_rest
# is the smallest of the three), but SP15_rest is the south gateway that
# Path 26 and Path 46/WOR both feed, so it's where unlocated West-of-River /
# Palo Verde imports physically land before flowing on into the LA_BASIN/
# SDGE pockets over the import-limited internal links (see
# docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md). PJM
# falls back to PJM_West: the western
# AEP/ComEd belt is the largest-load-share zone (0.504) and is where the
# unlocated MISO/PJM-seam plants geographically sit. NYISO falls back to
# Upstate-West, its largest-load-share zone (0.365).
_LARGEST_ZONE: dict[str, str] = {
    "ERCOT": "North",
    "PJM": "PJM_AEP_Ohio",
    "CAISO": "SP15_rest",
    # MISO is pinned to MISO-Illinois, NOT its largest-load-share zone: at six
    # zones the largest share flips to MISO-South (0.2711), an unacceptable
    # default for the overwhelmingly Midwest unlocated cohort. Illinois is the
    # central wheel-through zone adjacent to every Midwest neighbor, so a
    # mis-defaulted plant distorts the topology least (scope doc §3).
    "MISO": "MISO-Illinois",
    "NYISO": "Upstate_West",
    # Central (WCMA/SEMA/RI) is ISO-NE's largest-load-share zone (0.30) and
    # holds central/coastal Massachusetts, so unlocated NEISO plants land there.
    "NEISO": "Central",
    # SPP-North is SPP's largest-load-share zone (0.5125 vs 0.4875 — the
    # measured 2023-2025 sub-BA energy split, iso_configs._spp_config) and
    # holds the KS/NE/MO plurality of the footprint's plant count, so an
    # unlocated SPP plant lands there (SPP-20, 2026-09-06).
    "SPP": "SPP-North",
    # NWPP: NWPP-NW is the largest-load-share zone (0.3769) and holds the
    # plurality of the footprint's plants (BPAT alone: 130 of 939). Reached
    # only by ``assign_zone`` for an ORIS absent from BOTH eGRID and the
    # EIA-860 plant file — i.e. a plant with no balancing-authority record at
    # all; every real footprint plant resolves through _NWPP_BA_ZONES.
    "NWPP": "NWPP-NW",
}

# FIPS state code for Texas; Houston-metro counties are matched within it.
_TEXAS_FIPS: int = 48

# Houston-metro county FIPS codes (within FIPS state 48). The metro
# boundary doesn't follow clean lat/lon lines, so county codes give the
# Houston zone the precision lat/lon alone can't.
HOUSTON_COUNTIES: frozenset[int] = frozenset(
    {
        201,  # Harris
        157,  # Fort Bend
        39,  # Brazoria
        167,  # Galveston
        339,  # Montgomery
        291,  # Liberty
        71,  # Chambers
        245,  # Jefferson
        361,  # Orange
        473,  # Waller
        321,  # Matagorda
        481,  # Wharton
    }
)

# CAISO north–south zone boundaries by latitude. The dominant axis of
# CAISO congestion is the Path 15 / Path 26 north–south split, so latitude
# carries the assignment; FIPS county handles the coastal cases where
# latitude alone would misplace a plant. Path 15 (Los Banos–Gates) sits at
# ~lat 36.5; Path 26 (Midway–Vincent) at ~lat 35.0.
_CAISO_PATH15_LAT: float = 36.5
_CAISO_PATH26_LAT: float = 35.0

# FIPS state codes for the out-of-state CISO resources. Arizona and Nevada
# plants sit in the CAISO balancing authority but outside California's
# Path 15 / Path 26 geography, so they are routed by the intertie their
# output lands on rather than by latitude band.
_CALIFORNIA_FIPS: int = 6
_ARIZONA_FIPS: int = 4
_NEVADA_FIPS: int = 32

# Latitude above which a Nevada CISO plant ties to the north (NP15) rather
# than the southern Eldorado/Marketplace hub (SP15).
_NEVADA_NORTH_LAT: float = 38.0

# Central-coast California counties (FIPS state 6) that fall in the ZP26
# latitude band but belong to NP15: they sit on PG&E's coastal system north
# of Path 26, not in the inland San Joaquin Valley that defines ZP26.
# (Diablo Canyon in San Luis Obispo is the canonical case.) This mirrors the
# Houston-county FIPS rule: county codes give precision lat/lon alone can't.
CAISO_CENTRAL_COAST_NP15_COUNTIES: frozenset[int] = frozenset(
    {
        79,  # San Luis Obispo (Diablo Canyon)
        53,  # Monterey (Moss Landing)
        69,  # San Benito
    }
)

# FSNO pocket county FIPS codes (state 6 = California) — the caiso-223 §B
# county tier of the FSNO sub-zonal partition (caiso-224, gated on
# ScenarioConfig caiso_fsno_subzonal_topology via config.topology_variant):
# a CAISO plant with NO measured sub-zone row whose eGRID county sits in the
# San Joaquin Valley pocket re-cuts from its NP15/ZP26 lat-band estimate to
# FSNO (Helms PS in Fresno county is the canonical case). Mirrors
# scripts/probes/_caiso223_subzonal_scope.py FSNO_COUNTIES.
CAISO_FSNO_COUNTIES: frozenset[int] = frozenset(
    {
        19,  # Fresno (Helms, Kerckhoff, the Westlands solar belt)
        31,  # Kings (Mustang, American Kings, Henrietta)
        39,  # Madera
        47,  # Merced
    }
)

# LA-basin / SDG&E LCR-pocket county FIPS codes (state 6 = California),
# matching the county names in local_capacity.COUNTY_AREA_CAISO — the same
# LCT membership geography that parameterizes the SP15 sub-zone split
# (docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md).
CAISO_LA_BASIN_COUNTIES: frozenset[int] = frozenset(
    {
        37,  # Los Angeles
        59,  # Orange
    }
)
CAISO_SDGE_COUNTIES: frozenset[int] = frozenset(
    {
        73,  # San Diego
        25,  # Imperial
    }
)
# Counties the LA Basin LCR boundary bisects (Devers/Mira Loma IN; Lugo/Red
# Bluff OUT), resolved geographically like local_capacity.caiso_area_of:
# south of the San Gabriel/Cajon rim AND west of the Red Bluff/Eagle
# Mountain desert. The lat/lon thresholds are local_capacity's own
# BOUNDARY_LAT_MAX / BOUNDARY_LON_MAX, reused (not re-derived) for
# consistency with the LCR membership rule.
CAISO_LA_BASIN_BOUNDARY_COUNTIES: frozenset[int] = frozenset(
    {
        65,  # Riverside
        71,  # San Bernardino
    }
)

# Coords-only (no FIPS county) fallback split of the south-of-Path-26 band
# into SDGE vs LA_BASIN: San Diego/Imperial sit south of ~lat 33.4, the
# LA-basin core north of that up to the LCR boundary latitude. Used by the
# EIA-860 greenfield cohort (_eia860_ba_zones), which has no county code.
_CAISO_SDGE_MAX_LAT: float = 33.4

# PJM model zone by FIPS state code, for the states that fall cleanly inside
# one of the eight zones. Ohio, Pennsylvania, Maryland and West Virginia
# straddle zones and are split by latitude/longitude/county in ``_pjm_zone``
# below, so they are deliberately absent here.
#   - IL is ComEd; IN/MI/KY are the AEP/Duke/EKPC western coal belt (AEP_Ohio);
#   - NJ/DE are the EMAAC eastern load pocket; DC is SWMAAC (PEPCO);
#   - VA/NC are Dominion; TN is the AEP/EKPC edge.
_PJM_STATE_ZONES: dict[int, str] = {
    17: "PJM_ComEd",  # IL  (ComEd)
    18: "PJM_AEP_Ohio",  # IN  (AEP / Duke / OVEC Clifty Creek)
    26: "PJM_AEP_Ohio",  # MI  (AEP)
    21: "PJM_AEP_Ohio",  # KY  (EKPC / Duke KY / AEP KY)
    34: "PJM_EMAAC",  # NJ  (PSEG / JCPL / AECO / RECO)
    10: "PJM_EMAAC",  # DE  (DPL)
    11: "PJM_SWMAAC",  # DC  (PEPCO)
    51: "PJM_Dominion",  # VA  (DOM)
    37: "PJM_Dominion",  # NC  (DOM)
    47: "PJM_AEP_Ohio",  # TN  (AEP / EKPC edge)
}

# FIPS state codes for the PJM states that straddle model zones.
_PENNSYLVANIA_FIPS: int = 42
_MARYLAND_FIPS: int = 24
_OHIO_FIPS: int = 39
_WEST_VIRGINIA_FIPS: int = 54

# Ohio: FirstEnergy's northern-Ohio territory (ATSI — Cleveland / Akron /
# Toledo / Youngstown) sits above ~lat 40.9; the rest of the state (AEP
# Columbus, Dayton, Duke/DEOK Cincinnati) is the AEP_Ohio coal belt.
_PJM_OH_ATSI_LAT: float = 40.9

# West Virginia: the northern half (Mon Power / Potomac Edison — APS:
# Harrison, Fort Martin, Pleasants) ties West_APS; the southern half (AEP
# Appalachian Power — Mountaineer, John Amos, Mitchell) is the AEP_Ohio belt.
_PJM_WV_NORTH_LAT: float = 39.0

# Pennsylvania splits four ways. The Philadelphia metro (PECO) is the EMAAC
# load pocket; western PA (Duquesne / West Penn / APS, west of ~-79.0) is
# West_APS; the remaining central/north-eastern PPL/METED/PENELEC corridor is
# Central_PA. The Philadelphia-metro county codes give the precision longitude
# alone can't, mirroring the Houston rule.
PJM_PHILLY_COUNTIES: frozenset[int] = frozenset(
    {
        101,  # Philadelphia
        45,  # Delaware
        91,  # Montgomery
        17,  # Bucks
        29,  # Chester
    }
)
_PJM_PA_WEST_LON: float = -79.0

# Maryland: the western panhandle (Garrett / Allegany — APS / Potomac Edison,
# west of ~-78.5) ties West_APS; the rest of the state (BGE / PEPCO Baltimore-
# DC, plus the eastern-shore DPL) is SWMAAC.
_PJM_MD_WEST_LON: float = -78.5

# Coords-only PJM fallback: a caller holding latitude/longitude but no eGRID
# FIPS codes. Before this rule EVERY such row fell through
# ``_PJM_STATE_ZONES.get(None, ...)`` into the largest-load-share zone — all
# 371 EIA-860 PJM proposed rows (PA 93, IL 78, VA 42, KY 37, OH 37, WV 21,
# NJ 21, IN 15, DE 11, MD 10, NC 4, DC 1, MI 1) landed in PJM_AEP_Ohio.
#
# PJM's footprint spans those 13 states with jagged, non-rectangular borders,
# so unlike the 1-to-6-state ISOs above it cannot be expressed as a lat/lon
# box ladder. Rather than invent boundary constants, a coords-only query
# borrows the FIPS state/county of the NEAREST eGRID PJM plant and re-enters
# the cited state/county/lat-lon rules — eGRID's own authoritative geography,
# with no hand-drawn line added (rule 14 [R-ACCURATE]: prefer the measured
# datum over an estimate). Measured leave-one-out over the 1,727 eGRID PJM
# plants (hold a plant out, zone it from its nearest neighbour's FIPS):
# 1,697/1,727 = 98.3 % agreement, against 12.0 % for the PJM_AEP_Ohio
# fallback it replaces.
#
# Search cap in degrees, so a coordinate outside the footprint cannot silently
# borrow a distant plant's state. Measured nearest-neighbour spacing in that
# same eGRID cohort: p50 0.028°, p90 0.129°, p99 0.329° — 1.0° (~111 km
# north-south, ~85 km east-west at 40°N) clears p99 threefold while still
# refusing an out-of-region point, which keeps the old fallback.
_PJM_COORDS_NEIGHBOR_MAX_DEG: float = 1.0

# MISO model zone by FIPS state code. The six model zones are drawn as whole
# EIA-930 sub-BA (LRZ) unions so the fleet and load partitions share identical
# boundaries (see eia_loader._MISO_SUBBA_ZONE_GROUPS): West = LRZ 1
# (MN/ND/SD/MT), Plains = LRZ 3+5 (IA/MO), Illinois = LRZ 4 (IL), Indiana =
# LRZ 6 (IN/KY), East = LRZ 2+7 (WI/MI), South = LRZ 8+9+10 (the Entergy
# footprint AR/LA/MS/East TX). Every zone is an exact union of whole states,
# and eGRID carries a FIPS state for every MISO plant, so the state map is
# authoritative; the latitude fallback below only handles the rare coords-only
# caller. See docs/multi-iso/miso-zonal-refinement-scope.md §3.
_MISO_STATE_ZONES: dict[int, str] = {
    27: "MISO-West",  # MN (LRZ 1)
    38: "MISO-West",  # ND (LRZ 1)
    46: "MISO-West",  # SD (LRZ 1)
    30: "MISO-West",  # MT (LRZ 1)
    19: "MISO-Plains",  # IA (LRZ 3, bundled with MO in sub-BA 0035)
    29: "MISO-Plains",  # MO (LRZ 5)
    17: "MISO-Illinois",  # IL (LRZ 4, Ameren)
    18: "MISO-Indiana",  # IN (LRZ 6)
    21: "MISO-Indiana",  # KY (LRZ 6)
    55: "MISO-East",  # WI (LRZ 2, bundled with MI in sub-BA 0027)
    26: "MISO-East",  # MI (LRZ 7)
    5: "MISO-South",  # AR
    22: "MISO-South",  # LA
    28: "MISO-South",  # MS
    48: "MISO-South",  # TX (MISO East Texas / Entergy, not ERCOT)
}

# Latitude threshold for the coords-only MISO fallback (no FIPS state). The
# Entergy South footprint sits below ~lat 36 (AR/LA/MS/East TX). At six
# Midwest-split zones a latitude band can no longer resolve the zone (the
# W↔E boundaries are longitudinal), so the fallback degrades to South vs a
# single pinned Midwest default (MISO-Illinois — the central wheel-through
# zone, see _LARGEST_ZONE). FIPS state is strongly preferred; this only
# triggers when a caller supplies coordinates without a state code.
_MISO_SOUTH_LAT: float = 36.0

# SPP model zone by FIPS state code (owner ruling P1, SPP desk r#2, 2026-09-06;
# docs/multi-iso/spp-data-audit.md §5 rows 4/5 and §6.3 option A). The two
# zones are exact unions of whole states: the North/South seam runs along the
# KS/OK and MO/AR state lines, and the EIA-860 census puts no SWPP plant in a
# state that crosses it, so the state map is authoritative and needs no
# county rule. Wyoming is deliberately ABSENT — zero EIA-860 plants carry
# balancing authority SWPP there (Laramie River files under WAUW, a WECC BA);
# Colorado IS present (eight small solar sites, 19.5 MW, all North).
_SPP_STATE_ZONES: dict[int, str] = {
    38: "SPP-North",  # ND
    46: "SPP-North",  # SD
    31: "SPP-North",  # NE
    27: "SPP-North",  # MN
    30: "SPP-North",  # MT
    19: "SPP-North",  # IA
    20: "SPP-North",  # KS
    29: "SPP-North",  # MO
    8: "SPP-North",  # CO (19.5 MW of solar; no CEMS unit)
    40: "SPP-South",  # OK
    48: "SPP-South",  # TX (SPS Panhandle + AEP/Golden Spread east Texas)
    35: "SPP-South",  # NM
    5: "SPP-South",  # AR
    22: "SPP-South",  # LA
}

# Latitude of the SPP North/South seam for the coords-only fallback (no FIPS
# state): the KS/OK state line is 37.0 N and the MO/AR line 36.5 N, so a plant
# south of 37.0 N is in the South tier. FIPS state is strongly preferred; this
# only triggers when a caller supplies coordinates without a state code.
_SPP_SEAM_LAT: float = 37.0

# FIPS state code for New York. NYISO's eleven load zones (A–K) follow
# county lines closely enough that county FIPS carries the assignment, with
# a lat/lon fallback for out-of-state merchant resources (the NJ HVDC/VFT
# cables that inject downstate) and any plant lacking a NY county code.
_NEW_YORK_FIPS: int = 36

# NYC (zone J) — the five boroughs.
NYISO_NYC_COUNTIES: frozenset[int] = frozenset(
    {
        5,  # Bronx
        47,  # Kings (Brooklyn)
        61,  # New York (Manhattan)
        81,  # Queens
        85,  # Richmond (Staten Island)
    }
)

# Long Island (zone K).
NYISO_LONG_ISLAND_COUNTIES: frozenset[int] = frozenset(
    {
        59,  # Nassau
        103,  # Suffolk
    }
)

# Lower-Hudson (zones H Millwood + I Dunwoodie) — the Westchester/Putnam
# pocket north of NYC and south of the UPNY-SENY interface.
NYISO_LOWER_HUDSON_COUNTIES: frozenset[int] = frozenset(
    {
        119,  # Westchester (Con Ed — zones H and I)
        79,  # Putnam
    }
)

# Capital/Hudson (zones F Capital + G Hudson Valley) — the eastern-NY
# corridor between the Central-East and UPNY-SENY interfaces. Every other
# NY county falls through to Upstate-West (zones A–E), which keeps the
# Niagara (zone A) and St. Lawrence (zone D) hydro upstate.
NYISO_CAPITAL_HUDSON_COUNTIES: frozenset[int] = frozenset(
    {
        1,  # Albany (F)
        21,  # Columbia (F)
        39,  # Greene (F)
        83,  # Rensselaer (F)
        91,  # Saratoga (F)
        93,  # Schenectady (F)
        95,  # Schoharie (F)
        113,  # Warren (F)
        115,  # Washington (F)
        27,  # Dutchess (G)
        71,  # Orange (G)
        87,  # Rockland (G)
        105,  # Sullivan (G)
        111,  # Ulster (G)
    }
)

# NYISO downstate lat/lon fallback boundaries, used only when a plant carries
# no NY county code (the NJ merchant-cable resources) or for the coordinate
# API. The precise assignment is county-based; these bands are the backstop.
# West of the Hudson corridor, or north of the Capital region (the North
# Country, zone D), is upstate; the eastern band splits by latitude into
# Capital/Hudson then Lower-Hudson, then by longitude into NYC and Long
# Island. Albany sits at ~lat 42.6; Westchester at ~lat 41.0–41.3; NYC at
# ~lat 40.7; Long Island runs east of NYC past ~lon -73.5.
_NYISO_UPSTATE_LON: float = -75.0
_NYISO_NORTH_LAT: float = 43.3
_NYISO_CAPITAL_LAT: float = 41.4
_NYISO_LOWER_HUDSON_LAT: float = 41.0
_NYISO_LONG_ISLAND_LON: float = -73.5

# NEISO model zone by FIPS state code. ISO-NE's aggregated zones follow state
# lines except Massachusetts, which splits across three load zones and is
# handled by county below: ME/NH/VT → North, CT → Connecticut, RI → Central
# (the WCMA/SEMA/RI aggregate). eGRID carries a FIPS state for every ISNE
# plant, so the state map is authoritative; the lat/lon fallback only handles
# the rare coords-only caller and out-of-footprint (e.g. NY-FIPS) attributions.
_NEISO_STATE_ZONES: dict[int, str] = {
    23: "North",  # ME
    33: "North",  # NH
    50: "North",  # VT
    9: "Connecticut",  # CT
    44: "Central",  # RI (part of the WCMA/SEMA/RI aggregate)
}

# FIPS state code for Massachusetts; its three ISO-NE load zones (NEMA/Boston,
# WCMA, SEMA) are split by county below.
_MASSACHUSETTS_FIPS: int = 25

# Massachusetts counties (FIPS within state 25) in the NEMA/Boston load zone.
# The NEMA/Boston pocket is the Boston-metro counties; every other MA county
# belongs to the WCMA (western/central) or SEMA (southeast) load zones, both
# of which fold into the Central aggregate. This mirrors the ERCOT/CAISO rule
# where county codes give the precision lat/lon alone can't.
NEMA_BOSTON_COUNTIES: frozenset[int] = frozenset(
    {
        25,  # Suffolk (Boston)
        17,  # Middlesex (Mystic / Lowell)
        9,  # Essex (Salem Harbor)
        21,  # Norfolk (Fore River / Boston south suburbs)
    }
)

# Latitude/longitude bands for the coords-only NEISO fallback (no FIPS state).
# Northern New England (ME/NH/VT) sits above ~lat 42.8; Connecticut is the
# southwest corner (below ~lat 42.05 and west of ~lon -71.8); the Boston/NEMA
# coast is eastern Massachusetts (east of ~lon -71.3, at/above ~lat 42.1);
# everything else (western/central MA, SE Mass, RI) is Central. This is coarse
# — FIPS state+county is preferred — and only triggers for a coords-only caller
# or an out-of-footprint attribution that misses the state map.
_NEISO_NORTH_LAT: float = 42.8
_NEISO_CT_LAT: float = 42.05
_NEISO_CT_LON: float = -71.8
_NEISO_BOSTON_LAT: float = 42.1
_NEISO_BOSTON_LON: float = -71.3

# Cached parsed eGRID DataFrame and derived ORIS→location lookup, so the
# 21 MB workbook is read at most once per process.
_PLNT23_CACHE: pd.DataFrame | None = None
_ORIS_TO_LOCATION: (
    dict[int, tuple[float | None, float | None, int | None, int | None]] | None
) = None

# Cached (lat, lon, fips_state, fips_county) arrays for eGRID's PJM plants,
# backing the coords-only PJM nearest-plant rule (_PJM_COORDS_NEIGHBOR_MAX_DEG).
_PJM_EGRID_GEOGRAPHY: tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None = (
    None
)


def _to_float(value: object) -> float | None:
    """Coerce ``value`` to a float, returning ``None`` for blanks or NaN."""
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return result


def _to_int(value: object) -> int | None:
    """Coerce ``value`` to an int, returning ``None`` for blanks or NaN."""
    if value is None:
        return None
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if result != result:  # NaN
        return None
    return int(result)


# Clean ``egrid`` datatype column -> the legacy eGRID short-code name this
# module's callers (_oris_to_location, build_zone_lookup) read by.
_EGRID_CLEAN_TO_SHORT: dict[str, str] = {
    "plant_id": "ORISPL",
    "lat": "LAT",
    "lon": "LON",
    "fips_state": "FIPSST",
    "fips_county": "FIPSCNTY",
    "ba_code": "BACODE",
}

# eGRID vintage this module pins zone assignment to (matches _EGRID_PATH).
_EGRID_VINTAGE: int = 2023


def _plnt23() -> pd.DataFrame:
    """Return the eGRID PLNT23 sheet, parsing and caching it on first call.

    The PLNT23 sheet's first row holds long descriptive headers; ``skiprows=1``
    drops it so the short-code header row (ORISPL, LAT, LON, ...) becomes the
    column index.

    When ``MARKET_SIM_USE_CLEAN`` is set (default OFF) and the curated
    ``data/clean/egrid`` partition for vintage 2023 exists (written by
    ``scripts/data/curate_egrid.py``), the sheet is read from there instead of the
    21 MB workbook, with columns renamed back to the legacy eGRID short codes
    this module's lookups key on; otherwise it falls back to the raw parse.

    That raw parse goes through
    :func:`market_sim.data.egrid_sheets.read_egrid_sheet`, which serves the sheet
    from a content-addressed parquet mirror beside the workbook after the first
    miss — same frame, without openpyxl on the solve path (wall-clock item A-2).
    """
    global _PLNT23_CACHE
    if _PLNT23_CACHE is None:
        if _use_clean():
            from scripts.lib.clean_io import clean_exists, read_clean

            if clean_exists("egrid", year=_EGRID_VINTAGE):
                df = read_clean(
                    "egrid",
                    year=_EGRID_VINTAGE,
                    columns=list(_EGRID_CLEAN_TO_SHORT),
                )
                _PLNT23_CACHE = df.rename(columns=_EGRID_CLEAN_TO_SHORT)
        if _PLNT23_CACHE is None:
            _PLNT23_CACHE = read_egrid_sheet(
                _EGRID_PATH,
                "PLNT23",
                ["ORISPL", "LAT", "LON", "FIPSST", "FIPSCNTY", "BACODE"],
            )
    return _PLNT23_CACHE


def _oris_to_location() -> dict[
    int, tuple[float | None, float | None, int | None, int | None]
]:
    """Return the ``{oris: (lat, lon, fips_state, fips_county)}`` lookup."""
    global _ORIS_TO_LOCATION
    if _ORIS_TO_LOCATION is None:
        lookup: dict[
            int, tuple[float | None, float | None, int | None, int | None]
        ] = {}
        for row in _plnt23().itertuples(index=False):
            oris = _to_int(row.ORISPL)
            if oris is None:
                continue
            lookup[oris] = (
                _to_float(row.LAT),
                _to_float(row.LON),
                _to_int(row.FIPSST),
                _to_int(row.FIPSCNTY),
            )
        _ORIS_TO_LOCATION = lookup
    return _ORIS_TO_LOCATION


def _ercot_zone(
    lat: float | None,
    lon: float | None,
    fips_state: int | None,
    fips_county: int | None,
) -> str:
    """Return the ERCOT model zone for a plant location.

    Zones are bounded by ERCOT's real congestion interfaces. Houston-metro
    counties are checked first; the remaining zones follow lat/lon
    boundaries — Panhandle and West behind the West Texas Export interface,
    North and Houston as the load centers, South_Central (Austin/San
    Antonio) and South (the coast and Rio Grande Valley) — with North as the
    catch-all.
    """
    if fips_state == _TEXAS_FIPS and fips_county in HOUSTON_COUNTIES:
        return "Houston"
    # Northeast Texas (the EAST weather zone): the generation-rich East-Texas
    # lobe -- Martin Lake / Welsh / Tenaska Gateway / Wilkes etc. -- east of
    # the North zone behind ERCOT's East Texas GTC (EASTEX) export limit
    # (Tyler / Longview / Texarkana / Paris / Lufkin; ercot-234 card Z-A —
    # this window formerly cited NE_LOB under the repaired name misreading).
    # Checked before the North band/catch-all; the North
    # band's eastern edge is lon -95.5, so this -95.55..-93.0 window does not
    # overlap the DFW / central-Texas North plants.
    if (
        lat is not None
        and lon is not None
        and 31.3 <= lat <= 34.0
        and -95.55 <= lon <= -93.0
    ):
        return "Northeast"
    if lon is not None and lon < -99.5:
        # West Texas Export interface: the Panhandle wind belt sits north of
        # the CREZ belt / Permian behind its own stability-limited GTC.
        if lat is not None and lat >= 33.5:
            return "Panhandle"
        return "West"
    if lat is not None and lon is not None and lat >= 31.0 and -99.5 <= lon < -95.5:
        return "North"
    # Houston-area fallback for east-coast plants without a FIPS county match.
    if lat is not None and lon is not None and lon >= -96.0 and lat < 31.0:
        return "Houston"
    if (
        lat is not None
        and lon is not None
        and 29.0 <= lat < 31.0
        and -99.0 <= lon < -95.5
    ):
        return "South_Central"
    if lat is not None and lat < 29.0:
        return "South"
    return "North"


def _caiso_zone(
    lat: float | None,
    lon: float | None,
    fips_state: int | None,
    fips_county: int | None,
) -> str:
    """Return the CAISO model zone for a plant location.

    Zones follow CAISO's north–south split plus the SP15 local-capacity-area
    split: NP15 (north of Path 15), ZP26 (between Path 15 and Path 26),
    LA_BASIN / SDGE (the two LCR pockets south of Path 26), and SP15_rest
    (the remaining south gateway that feeds them — see
    docs/handoffs/caiso-sp15-split-implementation-scope-2026-07-09.md).
    Out-of-state CISO resources are routed first — Arizona (Palo Verde /
    West-of-River) and Nevada south of the NP15 cutoff land in SP15_rest,
    the zone Path 46/WOR and the WECC_DSW corridor now terminate on; Nevada
    north of the cutoff ties to NP15. Coastal PG&E counties that fall in the
    ZP26 latitude band are lifted to NP15. Los Angeles/Orange (+ the
    LCR-boundary counties Riverside/San Bernardino, resolved geographically)
    route to LA_BASIN; San Diego/Imperial route to SDGE — the LCT membership
    geography reused from local_capacity.COUNTY_AREA_CAISO /
    caiso_area_of. Latitude then carries the remaining (inland California)
    plants south of Path 26 into LA_BASIN vs SDGE by a coords-only lat cut,
    else SP15_rest; with no latitude the largest-load-share zone
    (SP15_rest) is the fallback.
    """
    if fips_state == _ARIZONA_FIPS:
        return "SP15_rest"
    if fips_state == _NEVADA_FIPS:
        if lat is not None and lat >= _NEVADA_NORTH_LAT:
            return "NP15"
        return "SP15_rest"
    if fips_state == _CALIFORNIA_FIPS:
        if fips_county in CAISO_CENTRAL_COAST_NP15_COUNTIES:
            return "NP15"
        if fips_county in CAISO_LA_BASIN_COUNTIES:
            return "LA_BASIN"
        if fips_county in CAISO_SDGE_COUNTIES:
            return "SDGE"
        if fips_county in CAISO_LA_BASIN_BOUNDARY_COUNTIES:
            if (
                lat is not None
                and lon is not None
                and lat < _LA_BASIN_BOUNDARY_LAT_MAX
                and lon < _LA_BASIN_BOUNDARY_LON_MAX
            ):
                return "LA_BASIN"
    if lat is not None:
        if lat >= _CAISO_PATH15_LAT:
            return "NP15"
        if lat >= _CAISO_PATH26_LAT:
            return "ZP26"
        # South of Path 26: no county to resolve the LCR pocket, so split
        # LA_BASIN vs SDGE by latitude alone (San Diego/Imperial sit south
        # of ~lat 33.4); everything else in the south gateway is SP15_rest.
        if lat < _CAISO_SDGE_MAX_LAT:
            return "SDGE"
        if lat < _LA_BASIN_BOUNDARY_LAT_MAX and (
            lon is None or lon < _LA_BASIN_BOUNDARY_LON_MAX
        ):
            return "LA_BASIN"
        return "SP15_rest"
    return _LARGEST_ZONE["CAISO"]


def _nyiso_zone(
    lat: float | None,
    lon: float | None,
    fips_state: int | None,
    fips_county: int | None,
) -> str:
    """Return the NYISO model zone for a plant location.

    NYISO's eleven load zones (A–K) follow New York county lines closely, so
    county FIPS carries the assignment: the five boroughs -> NYC (J),
    Nassau/Suffolk -> Long Island (K), Westchester/Putnam -> Lower-Hudson
    (H–I), the Capital and Hudson-Valley counties -> Capital/Hudson (F–G),
    and every other NY county -> Upstate-West (A–E) — which keeps the Niagara
    (zone A) and St. Lawrence (zone D) hydro upstate. Out-of-state merchant
    resources that inject through the downstate HVDC/VFT cables (the NJ
    plants) carry no NY county code and are routed by lat/lon onto the
    downstate pocket they feed.
    """
    if fips_state == _NEW_YORK_FIPS and fips_county is not None:
        if fips_county in NYISO_NYC_COUNTIES:
            return "NYC"
        if fips_county in NYISO_LONG_ISLAND_COUNTIES:
            return "Long_Island"
        if fips_county in NYISO_LOWER_HUDSON_COUNTIES:
            return "Lower_Hudson"
        if fips_county in NYISO_CAPITAL_HUDSON_COUNTIES:
            return "Capital_Hudson"
        return "Upstate_West"
    return _nyiso_zone_from_latlon(lat, lon)


def _nyiso_zone_from_latlon(lat: float | None, lon: float | None) -> str:
    """Return the NYISO zone for a plant with no NY county code, by lat/lon.

    Coarse backstop for out-of-state merchant resources and missing FIPS:
    west of the Hudson corridor or north of the Capital region is
    Upstate-West; the eastern band splits by latitude into Capital/Hudson and
    Lower-Hudson, then by longitude into NYC and Long Island downstate. With
    no coordinates the largest-load-share zone (Upstate-West) is the fallback.
    """
    if lat is None or lon is None:
        return _LARGEST_ZONE["NYISO"]
    if lon < _NYISO_UPSTATE_LON or lat >= _NYISO_NORTH_LAT:
        return "Upstate_West"
    if lat >= _NYISO_CAPITAL_LAT:
        return "Capital_Hudson"
    if lat >= _NYISO_LOWER_HUDSON_LAT:
        return "Lower_Hudson"
    if lon >= _NYISO_LONG_ISLAND_LON:
        return "Long_Island"
    return "NYC"


def _pjm_egrid_geography() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(lat, lon, fips_state, fips_county)`` arrays for eGRID's PJM plants.

    Parsed from the same PLNT23 sheet every other lookup in this module reads
    and cached process-wide (the module's ``_PLNT23_CACHE`` idiom). Rows with
    no usable coordinate or no FIPS state are dropped — they cannot serve as a
    geographic reference. Counties are carried as ``-1`` where absent, so the
    array stays integral; :func:`_pjm_fips_from_coords` maps that back to
    ``None``.
    """
    global _PJM_EGRID_GEOGRAPHY
    if _PJM_EGRID_GEOGRAPHY is None:
        df = _plnt23()
        ba = df["BACODE"].astype(str).str.strip()
        subset = df[ba == _ISO_TO_BA_CODE["PJM"]]

        lats: list[float] = []
        lons: list[float] = []
        states: list[int] = []
        counties: list[int] = []
        for row in subset.itertuples(index=False):
            lat = _to_float(row.LAT)
            lon = _to_float(row.LON)
            state = _to_int(row.FIPSST)
            if lat is None or lon is None or state is None:
                continue
            county = _to_int(row.FIPSCNTY)
            lats.append(lat)
            lons.append(lon)
            states.append(state)
            counties.append(-1 if county is None else county)

        _PJM_EGRID_GEOGRAPHY = (
            np.asarray(lats, dtype=float),
            np.asarray(lons, dtype=float),
            np.asarray(states, dtype=int),
            np.asarray(counties, dtype=int),
        )
    return _PJM_EGRID_GEOGRAPHY


def _pjm_fips_from_coords(lat: float, lon: float) -> tuple[int, int | None] | None:
    """Return the nearest eGRID PJM plant's ``(fips_state, fips_county)``.

    The coords-only PJM rule (see :data:`_PJM_COORDS_NEIGHBOR_MAX_DEG`).
    Distance is equirectangular with the longitude degree cos-corrected at the
    query latitude — exact enough for a nearest-neighbour argmin over a
    ~10°-wide footprint, and it avoids a haversine per query. Returns ``None``
    when eGRID is unavailable, holds no PJM row, or the nearest plant is
    farther than the cap, so the caller keeps its existing fallback.
    """
    lats, lons, states, counties = _pjm_egrid_geography()
    if lats.size == 0:
        return None

    coslat = np.cos(np.radians(lat))
    d2 = (lats - lat) ** 2 + ((lons - lon) * coslat) ** 2
    idx = int(np.argmin(d2))
    if float(d2[idx]) > _PJM_COORDS_NEIGHBOR_MAX_DEG**2:
        return None

    county = int(counties[idx])
    return int(states[idx]), (None if county < 0 else county)


def _pjm_zone(
    lat: float | None,
    lon: float | None,
    fips_state: int | None,
    fips_county: int | None,
) -> str:
    """Return the PJM model zone (one of eight) for a plant location.

    Most states map cleanly via ``_PJM_STATE_ZONES``. Four states straddle
    zones and split by latitude/longitude/county:

    - **Ohio** — northern OH (FirstEnergy ATSI) above ~lat 40.9 is ``PJM_ATSI``;
      the rest (AEP/Dayton/Duke) is ``PJM_AEP_Ohio``.
    - **West Virginia** — northern WV (APS) at/above ~lat 39.0 is
      ``PJM_West_APS``; southern WV (AEP) is ``PJM_AEP_Ohio``.
    - **Pennsylvania** — Philadelphia metro (PECO counties) is ``PJM_EMAAC``;
      western PA (west of ~-79.0) is ``PJM_West_APS``; the rest (PPL/METED/
      PENELEC) is ``PJM_Central_PA``.
    - **Maryland** — the western panhandle (west of ~-78.5, APS) is
      ``PJM_West_APS``; the rest (BGE/PEPCO) is ``PJM_SWMAAC``.

    These lat/lon/county cuts approximate the real utility-territory
    boundaries (Tier 3 — verify against a PJM zone-county crosswalk).

    A **coords-only** caller (latitude/longitude, no FIPS — the forecast-only
    EIA-860 planned/procured-additions limbs) borrows the FIPS state/county of
    the nearest eGRID PJM plant and re-enters these same rules; see
    :data:`_PJM_COORDS_NEIGHBOR_MAX_DEG` for the rationale and the measured
    98.3 % leave-one-out agreement. A plant with no usable location at all —
    and a coordinate with no eGRID PJM plant inside the cap — still falls back
    to the largest-load-share zone (``PJM_AEP_Ohio``).
    """
    if fips_state is None and lat is not None and lon is not None:
        nearest = _pjm_fips_from_coords(lat, lon)
        if nearest is not None:
            # One level only: ``nearest[0]`` is never None, so the re-entry
            # cannot take this branch again.
            return _pjm_zone(lat, lon, nearest[0], nearest[1])
    if fips_state == _OHIO_FIPS:
        if lat is not None and lat >= _PJM_OH_ATSI_LAT:
            return "PJM_ATSI"
        return "PJM_AEP_Ohio"
    if fips_state == _WEST_VIRGINIA_FIPS:
        if lat is not None and lat >= _PJM_WV_NORTH_LAT:
            return "PJM_West_APS"
        return "PJM_AEP_Ohio"
    if fips_state == _PENNSYLVANIA_FIPS:
        if fips_county in PJM_PHILLY_COUNTIES:
            return "PJM_EMAAC"
        if lon is not None and lon <= _PJM_PA_WEST_LON:
            return "PJM_West_APS"
        return "PJM_Central_PA"
    if fips_state == _MARYLAND_FIPS:
        if lon is not None and lon <= _PJM_MD_WEST_LON:
            return "PJM_West_APS"
        return "PJM_SWMAAC"
    return _PJM_STATE_ZONES.get(fips_state, _LARGEST_ZONE["PJM"])


def _miso_zone(lat: float | None, fips_state: int | None) -> str:
    """Return the MISO model zone for a plant location.

    FIPS state carries the assignment — the six model zones are exact unions
    of whole states (see :data:`_MISO_STATE_ZONES`) and eGRID has a state for
    every plant. A plant whose state is outside the MISO map (a stray
    cross-seam attribution) falls back to South vs the pinned Midwest default
    when coordinates are available (latitude cannot resolve the six-zone
    Midwest split), and otherwise to the pinned Midwest default
    (MISO-Illinois).
    """
    if fips_state in _MISO_STATE_ZONES:
        return _MISO_STATE_ZONES[fips_state]
    if lat is not None and lat < _MISO_SOUTH_LAT:
        return "MISO-South"
    return _LARGEST_ZONE["MISO"]


def _neiso_zone(
    lat: float | None,
    lon: float | None,
    fips_state: int | None,
    fips_county: int | None,
) -> str:
    """Return the NEISO model zone for a plant location.

    FIPS state carries the assignment — North (ME/NH/VT), Connecticut (CT),
    Central (RI) — except Massachusetts, which is split by county: the
    NEMA/Boston metro counties land in Boston and every other MA county folds
    into the Central (WCMA/SEMA/RI) aggregate. A plant outside the ISO-NE state
    map (e.g. a NY-FIPS cross-seam attribution) or a coords-only caller falls
    back to a coarse lat/lon band, and otherwise to the largest-load-share zone
    (Central).
    """
    if fips_state == _MASSACHUSETTS_FIPS:
        if fips_county in NEMA_BOSTON_COUNTIES:
            return "Boston"
        return "Central"
    if fips_state in _NEISO_STATE_ZONES:
        return _NEISO_STATE_ZONES[fips_state]
    if lat is not None and lon is not None:
        if lat >= _NEISO_NORTH_LAT:
            return "North"
        if lat < _NEISO_CT_LAT and lon < _NEISO_CT_LON:
            return "Connecticut"
        if lat >= _NEISO_BOSTON_LAT and lon >= _NEISO_BOSTON_LON:
            return "Boston"
        return "Central"
    return _LARGEST_ZONE["NEISO"]


def _spp_zone(lat: float | None, fips_state: int | None) -> str:
    """Return the SPP model zone for a plant location.

    FIPS state carries the assignment — the two model zones are exact unions
    of whole states (see :data:`_SPP_STATE_ZONES`) and eGRID / EIA-860 carry a
    state for every SWPP plant. A plant whose state is outside the SPP map (a
    stray cross-seam attribution) falls back to the seam latitude when
    coordinates are available (South below 37.0 N, the KS/OK line), and
    otherwise to the largest-load-share zone (SPP-North).
    """
    if fips_state in _SPP_STATE_ZONES:
        return _SPP_STATE_ZONES[fips_state]
    if lat is not None:
        return "SPP-South" if lat < _SPP_SEAM_LAT else "SPP-North"
    return _LARGEST_ZONE["SPP"]


def _zone_from_location(
    iso: str,
    lat: float | None,
    lon: float | None,
    fips_state: int | None,
    fips_county: int | None,
) -> str:
    """Return the model zone for a plant location in the given ISO."""
    if iso in _SINGLE_ZONE:
        return _SINGLE_ZONE[iso]
    if iso == "ERCOT":
        return _ercot_zone(lat, lon, fips_state, fips_county)
    if iso == "CAISO":
        return _caiso_zone(lat, lon, fips_state, fips_county)
    if iso == "MISO":
        return _miso_zone(lat, fips_state)
    if iso == "NYISO":
        return _nyiso_zone(lat, lon, fips_state, fips_county)
    if iso == "NEISO":
        return _neiso_zone(lat, lon, fips_state, fips_county)
    if iso == "PJM":
        return _pjm_zone(lat, lon, fips_state, fips_county)
    if iso == "SPP":
        return _spp_zone(lat, fips_state)
    if iso == "NWPP":
        # NWPP zones are whole-BA groups (gate G18): no coordinate, state or
        # county rule can place a plant, because a state holds several BAs.
        # Callers resolve through the BA-keyed lookups (build_zone_lookup /
        # _eia860_ba_zones); this raise is what keeps a coordinate fallback
        # from silently splitting a BA.
        raise ValueError(
            "NWPP zones are whole-BA groups keyed on the balancing-authority "
            "code; no geographic zone rule exists (use build_zone_lookup)"
        )
    raise ValueError(f"No geographic zone rules for ISO '{iso}'")


def assign_zone_by_coords(lat: float, lon: float, iso: str) -> str:
    """Return the model zone for a plant given its latitude and longitude."""
    iso = iso.upper()
    return _zone_from_location(iso, lat, lon, None, None)


def assign_zone_by_fips(
    fips_state: str | int | None, fips_county: str | int | None, iso: str
) -> str:
    """Return the model zone for a plant given its FIPS state/county codes."""
    iso = iso.upper()
    return _zone_from_location(
        iso, None, None, _to_int(fips_state), _to_int(fips_county)
    )


def assign_zone(oris_code: int, iso: str) -> str:
    """Return the model zone for a plant's ORIS code.

    Every current ISO (ERCOT, CAISO, MISO, NYISO, NEISO, PJM, SPP) has a
    multi-zone topology, so the plant is located via the eGRID ORIS→location table; an
    ORIS code missing from eGRID falls back to the ISO's largest-load-share
    zone with a warning. For CAISO the measured hub-membership crosswalk is
    the first check, consistent with :func:`build_zone_lookup`: where CAISO's
    own generator-hub membership is joined, it overrides the geographic
    estimate (caiso-217, ``[R-ACCURATE]``).
    """
    iso = iso.upper()
    if iso in _SINGLE_ZONE:
        return _SINGLE_ZONE[iso]

    oris = _to_int(oris_code)
    if iso == "NWPP":
        # BA-keyed (gate G18): the eGRID BACODE / EIA-860 plant-file lookup is
        # the only admissible placement; a coordinate read cannot place an
        # NWPP plant. The fallback fires only for an ORIS in neither source.
        zone = build_zone_lookup(iso).get(oris) if oris is not None else None
        if zone is not None:
            return zone
        logger.warning(
            "ORIS %s not in the eGRID/EIA-860 BA lookup for NWPP — assigning "
            "fallback zone %s",
            oris_code,
            _LARGEST_ZONE["NWPP"],
        )
        return _LARGEST_ZONE["NWPP"]
    location = _oris_to_location().get(oris) if oris is not None else None
    if location is None:
        fallback = _LARGEST_ZONE.get(iso)
        if fallback is None:
            raise ValueError(f"No geographic zone rules for ISO '{iso}'")
        logger.warning(
            "ORIS %s not in eGRID lookup for %s — assigning fallback zone %s",
            oris_code,
            iso,
            fallback,
        )
        return fallback

    lat, lon, fips_state, fips_county = location
    geo_zone = _zone_from_location(iso, lat, lon, fips_state, fips_county)
    if iso == "CAISO" and oris is not None:
        hub = load_caiso_hub_membership().get(oris)
        if hub is not None:
            return _caiso_zone_from_hub(hub, geo_zone)
    return geo_zone


# ISOs whose eGRID zone lookup is supplemented from the current EIA-860
# plant file (plants too new for the eGRID 2023 vintage). Gated per ISO so
# opting one ISO in cannot move another ISO's derived outputs (the ERCOT/PJM
# byte-identical regression guard): ERCOT was first (2024+ wind/solar/
# storage), CAISO second (2024-2025 greenfield solar, ~4.8 GW absent from
# eGRID 2023), NYISO third (2024+ downstate battery fleet), NEISO fourth
# (2022-2024 MA batteries: 29 plants / ~44 MW absent from eGRID 2023, rising
# to 346 MW with the 2025 Cranberry Point and Cross Town BESS additions),
# MISO fifth (post-eGRID-2023 plants — 28 of 1,975 at the six-zone refinement
# — previously landed in the fallback zone; the EIA-860 lat/lon supplement
# resolves most of them, see docs/multi-iso/miso-zonal-refinement-scope.md §3),
# SPP sixth at registration (2026-09-06, lane SPP-20: the SPP fleet is read
# from the EIA-860 2025 Early Release, whose 2024-2025 wind/solar/storage
# additions post-date eGRID 2023; with a whole-state zone map the lat/lon
# supplement resolves them exactly, so no SWPP plant is dropped to the
# fallback — the Stage-B "every plant resolves" check).
_EIA860_SUPPLEMENT_ISOS: frozenset[str] = frozenset(
    # NWPP seventh at registration (2026-09-14, lane NWPP-20): the footprint
    # fleet is read from the EIA-860 2025 Early Release, whose 2024-2025
    # additions post-date eGRID 2023, and the plant file's BA code is the ONLY
    # placement key a whole-BA zoning can use — so the supplement is not a
    # refinement here, it is the primary source for every post-eGRID plant.
    {"ERCOT", "CAISO", "NYISO", "NEISO", "MISO", "SPP", "NWPP"}
)


def _eia860_ba_zones(iso: str) -> dict[int, str]:
    """Return ``{oris: zone}`` for the ISO's plants from the EIA-860 plant file.

    The EIA-860 plant file carries current latitude/longitude and
    balancing-authority codes, so it covers plants too new for the eGRID
    2023 vintage (notably 2024+ wind, solar and storage). Plants in the
    ISO's balancing authority are zoned from their coordinates alone; the
    county-FIPS refinements (ERCOT's Houston rule, CAISO's central-coast
    NP15 lift) cannot apply without eGRID's FIPS codes — an accepted
    compromise for the small post-eGRID cohort.

    Returns an empty dict when the EIA-860 plant file is unavailable.
    """
    if not _EIA860_PLANT_PATH.exists():
        return {}
    df = pd.read_parquet(_EIA860_PLANT_PATH)
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    if iso == "NWPP":
        # Whole-BA zoning (gate G18) under the footprint admission predicate
        # (BA ∈ map AND NERC == WECC, audit §2.8(a)): the zone IS the BA's
        # group, coordinates are not read, and a plant with no coordinates is
        # still placed — there is nothing for a coordinate rule to refine.
        nerc = df["NERC Region"] if "NERC Region" in df.columns else None
        df = df[_nwpp_admitted(ba, nerc)]
        out_nwpp: dict[int, str] = {}
        for code, ba_code in zip(df["Plant Code"], df["Balancing Authority Code"]):
            oris = _to_int(code)
            if oris is None:
                continue
            out_nwpp[oris] = _NWPP_BA_ZONES[str(ba_code).strip()]
        return out_nwpp
    df = df[ba.isin(_iso_ba_codes(iso))]

    codes = df["Plant Code"].to_numpy()
    lats = pd.to_numeric(df["Latitude"], errors="coerce").to_numpy()
    lons = pd.to_numeric(df["Longitude"], errors="coerce").to_numpy()

    out: dict[int, str] = {}
    for code, lat, lon in zip(codes, lats, lons):
        oris = _to_int(code)
        if oris is None or lat != lat or lon != lon:  # None / NaN coords
            continue
        out[oris] = _zone_from_location(iso, float(lat), float(lon), None, None)
    return out


def plant_state_lookup(iso: str) -> dict[int, str]:
    """Return ``{plant_code: state}`` (2-letter postal code) for the ISO's plants.

    The EIA-860 plant file already carries the plant's ``State`` directly (no
    FIPS/lat-lon decoding needed, unlike zone assignment) — this is the raw
    fact a per-generator program-membership test (e.g. RGGI) resolves exactly
    against, for any generator whose ``plant_code`` names a real physical
    plant (see ``policy.cap_and_trade.per_generator_membership``). Filters to
    the current EIA-860 snapshot's balancing-authority column, mirroring
    :func:`_eia860_ba_zones`. Returns an empty dict when the plant file is
    unavailable or the ISO has no balancing-authority code registered.
    """
    iso = iso.upper()
    codes = _iso_ba_codes(iso)
    if not codes or not _EIA860_PLANT_PATH.exists():
        return {}
    df = pd.read_parquet(
        _EIA860_PLANT_PATH,
        columns=["Plant Code", "State", "Balancing Authority Code", "NERC Region"],
    )
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    if iso == "NWPP":
        df = df[_nwpp_admitted(ba, df["NERC Region"])]
    else:
        df = df[ba.isin(codes)]

    out: dict[int, str] = {}
    for code, state in zip(df["Plant Code"], df["State"]):
        oris = _to_int(code)
        if oris is None or state is None or state != state:  # None / NaN state
            continue
        out[oris] = str(state).strip().upper()
    return out


# Reference crosswalk: the curated ERCOT plant -> model-zone map. Its raw
# source is ``data/raw/reference/custom-bin-assignments.csv`` (``Plant_Code`` /
# ``ERCOT_Zone``), curated to ``data/clean/reference/bin-assignments`` through
# the clean seam. The table is ERCOT-only, so the crosswalk is empty for every
# other ISO.
def load_reference_zone_crosswalk(iso: str = "ERCOT") -> dict[int, str]:
    """Return ``{plant_id: zone}`` from the bin-assignments reference table.

    Reads the curated clean parquet when ``MARKET_SIM_USE_CLEAN`` is set
    (``read_clean("reference", market="bin-assignments")``) and the raw
    ``custom-bin-assignments.csv`` otherwise; both backends yield the same
    plant->zone map (the clean table is curated from that CSV). Returns an
    empty dict for non-ERCOT ISOs — the table only covers ERCOT — or when the
    backing source is absent.
    """
    iso = iso.upper()
    if iso != "ERCOT":
        return {}

    if _use_clean():
        from scripts.lib.clean_io import read_clean

        df = read_clean(
            "reference", market="bin-assignments", columns=["plant_id", "zone"]
        )
        pairs = zip(df["plant_id"], df["zone"])
    else:
        if not CAMPD_BINS_CSV.exists():
            return {}
        raw = pd.read_csv(CAMPD_BINS_CSV, usecols=["Plant_Code", "ERCOT_Zone"])
        pairs = zip(raw["Plant_Code"], raw["ERCOT_Zone"])

    out: dict[int, str] = {}
    for code, zone in pairs:
        oris = _to_int(code)
        if oris is None or zone is None or zone != zone:  # None / NaN zone
            continue
        out[oris] = str(zone)
    return out


# Measured CAISO generator->trading-hub membership (caiso-217, chartered by
# FINDING-caiso216-belly-lever-plan-2026-08-23.md §F.1g). CAISO's own
# ATL_PNODE_MAP puts several GW of capacity on the other side of the
# Path 15 / Path 26 cuts from the lat/county estimate above (canonical
# witnesses: Diablo Canyon -> TH_ZP26 where the county lift says NP15;
# Alta/Tehachapi -> TH_SP15 where the lat band says ZP26; Mustang/Westlands
# -> TH_NP15 where the lat cut says ZP26 — the error is two-directional, so
# the fix is this membership crosswalk, not a boundary re-tune [R-FROZEN-DERIVE]).
# Derived by scripts/data/derive_caiso_plant_hub_membership.py; the join
# method and witness pnode for every row live in the CSV [R-ACCURATE].
_CAISO_HUB_TO_ZONE: dict[str, str] = {"TH_NP15": "NP15", "TH_ZP26": "ZP26"}
_CAISO_SOUTH_OF_PATH26: frozenset[str] = frozenset({"LA_BASIN", "SDGE", "SP15_rest"})


def load_caiso_hub_membership() -> dict[int, str]:
    """Return ``{plant_code: hub}`` from the measured membership crosswalk.

    Reads the curated clean parquet when ``MARKET_SIM_USE_CLEAN`` is set
    (``read_clean("reference", market="caiso-hub-membership")``) and the raw
    ``caiso-plant-hub-membership.csv`` otherwise; both backends yield the same
    map. Hubs are ``TH_NP15`` / ``TH_ZP26`` / ``TH_SP15``. Returns an empty
    dict when the backing source is absent (the geographic rule then stands
    alone). Memoized on the flag like the zone lookup itself; callers get a
    fresh shallow copy per call.
    """
    return dict(_load_caiso_hub_membership_cached(_use_clean()))


@lru_cache(maxsize=2)
def _load_caiso_hub_membership_cached(use_clean: bool) -> dict[int, str]:
    """Cache-bearing core of :func:`load_caiso_hub_membership`."""
    if use_clean:
        from scripts.lib.clean_io import read_clean

        try:
            df = read_clean(
                "reference",
                market="caiso-hub-membership",
                columns=["plant_id", "hub"],
            )
        except FileNotFoundError:
            return {}
        pairs = zip(df["plant_id"], df["hub"])
    else:
        if not CAISO_HUB_MEMBERSHIP_CSV.exists():
            return {}
        raw = pd.read_csv(CAISO_HUB_MEMBERSHIP_CSV, usecols=["plant_code", "hub"])
        pairs = zip(raw["plant_code"], raw["hub"])

    out: dict[int, str] = {}
    for code, hub in pairs:
        oris = _to_int(code)
        if oris is None or hub is None or hub != hub:  # None / NaN hub
            continue
        out[oris] = str(hub)
    return out


def load_caiso_fsno_subzone_membership() -> dict[int, str]:
    """Return ``{plant_code: subzone}`` for the FSNO sub-zonal partition.

    The caiso-223 §B measured membership recut promoted to
    ``data/raw/reference/caiso-fsno-subzone-membership.csv`` (subzone ∈
    {FSNO, NP15, ZP26}; SP15-side rows are hub-unchanged by construction and
    deliberately absent). Consumed by the CAISO carve in
    :func:`_build_zone_lookup_cached` ONLY when the FSNO partition is armed
    (caiso-224; PRECOMMIT-caiso224-fsno-arm-2026-08-30.md §1). Reads the raw
    CSV on both the raw and clean paths — it is the same measured input
    either way (the caiso-217 hub first-check precedent); returns an empty
    dict when the file is absent.
    """
    return dict(_load_caiso_fsno_subzone_cached())


@lru_cache(maxsize=1)
def _load_caiso_fsno_subzone_cached() -> dict[int, str]:
    """Cache-bearing core of :func:`load_caiso_fsno_subzone_membership`."""
    if not CAISO_FSNO_SUBZONE_CSV.exists():
        return {}
    raw = pd.read_csv(CAISO_FSNO_SUBZONE_CSV, usecols=["plant_code", "subzone"])
    out: dict[int, str] = {}
    for code, subzone in zip(raw["plant_code"], raw["subzone"]):
        oris = _to_int(code)
        if oris is None or subzone is None or subzone != subzone:
            continue
        out[oris] = str(subzone)
    return out


def _caiso_zone_from_hub(hub: str, geo_zone: str | None) -> str:
    """Resolve a measured hub membership onto the CAISO model zones.

    ``TH_NP15`` / ``TH_ZP26`` map directly. ``TH_SP15`` covers everything
    south of Path 26 in CAISO's three-hub world, while the model splits that
    region into the two LCR pockets plus the gateway (LA_BASIN / SDGE /
    SP15_rest) — a finer resolution than the hub carries — so the geographic
    rule keeps the sub-zone when it already lands south of Path 26, and a
    plant the geography had placed north of the cut lands in the SP15_rest
    gateway (the zone Path 26 feeds).
    """
    direct = _CAISO_HUB_TO_ZONE.get(hub)
    if direct is not None:
        return direct
    if geo_zone in _CAISO_SOUTH_OF_PATH26:
        return geo_zone
    return "SP15_rest"


def build_zone_lookup(iso: str) -> dict[int, str]:
    """Return ``{oris: zone_name}`` for every plant in the ISO.

    Zones come from eGRID 2023 plant coordinates. For the ISOs in
    :data:`_EIA860_SUPPLEMENT_ISOS` the lookup is then supplemented from the
    current EIA-860 plant file, which covers plants too new for the eGRID
    vintage; eGRID stays authoritative where it has the plant, as it also
    carries the FIPS county the county-level zone rules need.

    Returns an empty dict for ISOs without geographic zone rules, letting
    callers fall back to a non-geographic assignment.

    Memoized (PERF-B, perf-recheck §2.4): the per-row ``_zone_from_location``
    walk over the ISO's eGRID subset is a pure function of two static on-disk
    sources (the eGRID workbook via :func:`_plnt23`, the EIA-860 plant file)
    plus the ``MARKET_SIM_USE_CLEAN`` flag, and data_prep calls it ~8× per
    solved year. The cache is keyed ``(iso, use_clean)`` and the public
    function returns a fresh shallow copy per call, so a caller mutating its
    dict can never poison another's.

    The cache key also carries the CAISO FSNO-partition state
    (``config.topology_variant``), so an in-process variant toggle (tests;
    the arm/control pair share nothing in-process) can never serve a lookup
    built under the other topology.
    """
    from market_sim.config.topology_variant import caiso_fsno_partition_active

    iso_u = iso.upper()
    fsno = caiso_fsno_partition_active() if iso_u == "CAISO" else False
    return dict(_build_zone_lookup_cached(iso_u, _use_clean(), fsno))


@lru_cache(maxsize=16)
def _build_zone_lookup_cached(
    iso: str, use_clean: bool, caiso_fsno: bool = False
) -> dict[int, str]:
    """Cache-bearing core of :func:`build_zone_lookup` (already-uppercased ISO)."""
    codes = _iso_ba_codes(iso)
    if not codes:
        return {}

    df = _plnt23()
    ba = df["BACODE"].astype(str).str.strip()
    if iso == "NWPP":
        # Whole-BA zoning (gate G18): the eGRID BACODE decides the zone
        # outright, under the same NERC admission predicate the EIA-860
        # supplement applies (eGRID's ``NERC`` column).
        nerc = df["NERC"] if "NERC" in df.columns else None
        subset = df[_nwpp_admitted(ba, nerc)]
        lookup_nwpp: dict[int, str] = {}
        for oris_v, ba_v in zip(subset["ORISPL"], subset["BACODE"]):
            oris = _to_int(oris_v)
            if oris is None:
                continue
            lookup_nwpp[oris] = _NWPP_BA_ZONES[str(ba_v).strip()]
        for oris, zone in _eia860_ba_zones(iso).items():
            lookup_nwpp.setdefault(oris, zone)
        if use_clean:
            for oris, zone in load_reference_zone_crosswalk(iso).items():
                lookup_nwpp.setdefault(oris, zone)
        return lookup_nwpp
    subset = df[ba.isin(codes)]

    lookup: dict[int, str] = {}
    # eGRID county per plant, kept only for the CAISO FSNO county tier below
    # (state FIPS, county FIPS); the base zone rule consumes county inline.
    counties: dict[int, tuple[int | None, int | None]] = {}
    for row in subset.itertuples(index=False):
        oris = _to_int(row.ORISPL)
        if oris is None:
            continue
        lookup[oris] = _zone_from_location(
            iso,
            _to_float(row.LAT),
            _to_float(row.LON),
            _to_int(row.FIPSST),
            _to_int(row.FIPSCNTY),
        )
        if caiso_fsno:
            counties[oris] = (_to_int(row.FIPSST), _to_int(row.FIPSCNTY))

    if iso in _EIA860_SUPPLEMENT_ISOS:
        for oris, zone in _eia860_ba_zones(iso).items():
            lookup.setdefault(oris, zone)

    # CAISO measured hub-membership first-check (caiso-217): where CAISO's
    # own generator-hub membership is joined, it OVERRIDES the geographic
    # estimate above — measured settlement geography beats the lat/county
    # proxy [R-ACCURATE]. Unjoined plants keep the geographic assignment,
    # and a crosswalk row can only re-zone a plant already in the ISO's
    # population (never widen it). Applied on both the raw and clean paths —
    # it is the same measured input either way.
    if iso == "CAISO":
        for oris, hub in load_caiso_hub_membership().items():
            geo_zone = lookup.get(oris)
            if geo_zone is not None:
                lookup[oris] = _caiso_zone_from_hub(hub, geo_zone)

    # CAISO FSNO sub-zonal carve (caiso-224, armed via config.topology_variant
    # from ScenarioConfig caiso_fsno_subzonal_topology; the caiso-223 §B
    # measured membership applied verbatim). Two tiers, mirroring caiso-223:
    # (1) the measured sub-zone recut of the crosswalk pool overrides the hub
    #     first-check above (it IS that first-check at sub-zonal grain —
    #     including honest non-moves like Henrietta-D staying ZP26);
    # (2) an unjoined plant whose eGRID county sits in the FSNO pocket and
    #     whose geographic estimate is NP15/ZP26 re-cuts to FSNO (the county
    #     tier — Helms PS is the canonical case). The guard never pulls
    #     SP15-side or out-of-state plants north. EIA-860-supplement plants
    #     without an eGRID county keep their estimate (the caiso-223
    #     enumeration's own base was the eGRID CISO cohort).
    if iso == "CAISO" and caiso_fsno:
        subzone_map = load_caiso_fsno_subzone_membership()
        for oris, zone in lookup.items():
            measured = subzone_map.get(oris)
            if measured is not None:
                lookup[oris] = measured
                continue
            fips_state, fips_county = counties.get(oris, (None, None))
            if (
                fips_state == _CALIFORNIA_FIPS
                and fips_county in CAISO_FSNO_COUNTIES
                and zone in ("NP15", "ZP26")
            ):
                lookup[oris] = "FSNO"

    # Clean-backed reference crosswalk supplement (default OFF, gated by
    # MARKET_SIM_USE_CLEAN). When enabled, the curated ERCOT bin-assignments
    # plant->zone map fills any ORIS the eGRID/EIA-860 geography missed. eGRID
    # stays authoritative (``setdefault``), and with the flag off this block is
    # skipped, so the default raw path — and the ERCOT/PJM byte-identical
    # regression guard — is unchanged. Read via the cache key's ``use_clean``
    # (not a fresh ``_use_clean()`` call), so the cached entry and the flag
    # value it was built under can never disagree.
    if use_clean:
        for oris, zone in load_reference_zone_crosswalk(iso).items():
            lookup.setdefault(oris, zone)
    return lookup
