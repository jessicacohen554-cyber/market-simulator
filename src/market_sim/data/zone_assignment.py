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
from pathlib import Path

import pandas as pd

from market_sim.config.paths import CAMPD_BINS_CSV, EIA_860_DIR, FLEET_DIR
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
_EGRID_PATH: Path = FLEET_DIR / "egrid2023_data_rev2 2.xlsx"

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
}

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
    ``scripts/curate_egrid.py``), the sheet is read from there instead of the
    21 MB workbook, with columns renamed back to the legacy eGRID short codes
    this module's lookups key on; otherwise it falls back to the raw parse.
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
            _PLNT23_CACHE = pd.read_excel(
                _EGRID_PATH,
                sheet_name="PLNT23",
                skiprows=1,
                usecols=["ORISPL", "LAT", "LON", "FIPSST", "FIPSCNTY", "BACODE"],
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
    # Northeast Texas (the EAST weather zone): the generation-rich NE_LOB lobe
    # -- Martin Lake / Welsh / Tenaska Gateway / Wilkes etc. -- east of the North
    # zone behind the ~1,300 MW NE_LOB export limit (Tyler / Longview / Texarkana
    # / Paris / Lufkin). Checked before the North band/catch-all; the North
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
    boundaries (Tier 3 — verify against a PJM zone-county crosswalk). A plant
    with no usable location falls back to the largest-load-share zone
    (``PJM_AEP_Ohio``).
    """
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

    Every current ISO (ERCOT, CAISO, MISO, NYISO, NEISO, PJM) has a multi-zone
    topology, so the plant is located via the eGRID ORIS→location table; an
    ORIS code missing from eGRID falls back to the ISO's largest-load-share
    zone with a warning.
    """
    iso = iso.upper()
    if iso in _SINGLE_ZONE:
        return _SINGLE_ZONE[iso]

    oris = _to_int(oris_code)
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
    return _zone_from_location(iso, lat, lon, fips_state, fips_county)


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
# resolves most of them, see docs/multi-iso/miso-zonal-refinement-scope.md §3).
_EIA860_SUPPLEMENT_ISOS: frozenset[str] = frozenset(
    {"ERCOT", "CAISO", "NYISO", "NEISO", "MISO"}
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
    df = df[ba == _ISO_TO_BA_CODE[iso]]

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
    ba_code = _ISO_TO_BA_CODE.get(iso)
    if ba_code is None or not _EIA860_PLANT_PATH.exists():
        return {}
    df = pd.read_parquet(
        _EIA860_PLANT_PATH,
        columns=["Plant Code", "State", "Balancing Authority Code"],
    )
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    df = df[ba == ba_code]

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


def build_zone_lookup(iso: str) -> dict[int, str]:
    """Return ``{oris: zone_name}`` for every plant in the ISO.

    Zones come from eGRID 2023 plant coordinates. For the ISOs in
    :data:`_EIA860_SUPPLEMENT_ISOS` the lookup is then supplemented from the
    current EIA-860 plant file, which covers plants too new for the eGRID
    vintage; eGRID stays authoritative where it has the plant, as it also
    carries the FIPS county the county-level zone rules need.

    Returns an empty dict for ISOs without geographic zone rules, letting
    callers fall back to a non-geographic assignment.
    """
    iso = iso.upper()
    ba_code = _ISO_TO_BA_CODE.get(iso)
    if ba_code is None:
        return {}

    df = _plnt23()
    ba = df["BACODE"].astype(str).str.strip()
    subset = df[ba == ba_code]

    lookup: dict[int, str] = {}
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

    if iso in _EIA860_SUPPLEMENT_ISOS:
        for oris, zone in _eia860_ba_zones(iso).items():
            lookup.setdefault(oris, zone)

    # Clean-backed reference crosswalk supplement (default OFF, gated by
    # MARKET_SIM_USE_CLEAN). When enabled, the curated ERCOT bin-assignments
    # plant->zone map fills any ORIS the eGRID/EIA-860 geography missed. eGRID
    # stays authoritative (``setdefault``), and with the flag off this block is
    # skipped, so the default raw path — and the ERCOT/PJM byte-identical
    # regression guard — is unchanged.
    if _use_clean():
        for oris, zone in load_reference_zone_crosswalk(iso).items():
            lookup.setdefault(oris, zone)
    return lookup
