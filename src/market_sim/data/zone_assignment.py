"""Geographic zone assignment using eGRID 2023 plant-level data.

Maps each generator's ORIS plant code to a model zone using latitude,
longitude, and FIPS county codes from the EPA eGRID database. This
replaces the count-proportional zone allocation that mis-distributes
capacity when the generator list order doesn't match zone geography.

Source: EPA eGRID 2023 (rev 2), PLNT23 sheet.

Note: if the eGRID file is updated, delete the cached binned-fleet
parquets (``inputs/processed/*_fleet_binned.parquet``) so they are
regenerated with zone assignments derived from the new data.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# eGRID 2023 plant-level workbook, resolved relative to the repo root
# (this file lives at src/market_sim/data/zone_assignment.py).
_EGRID_PATH: Path = (
    Path(__file__).parents[3] / "data" / "fleet" / "egrid2023_data_rev2 2.xlsx"
)

# EIA-860 plant file — current plant coordinates and balancing-authority
# codes. Used to zone plants too new for the eGRID 2023 vintage.
_EIA860_PLANT_PATH: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "eia-860"
    / "eia860_plant.parquet"
)

# Model ISO name → eGRID balancing-authority code (BACODE column).
_ISO_TO_BA_CODE: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "MISO": "MISO",
    "SPP": "SWPP",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
}

# ISOs modeled as a single zone, with that zone's name. Every current ISO now
# has a multi-zone topology, so this is empty; the mechanism stays in place for
# any future single-zone ISO.
_SINGLE_ZONE: dict[str, str] = {}

# Largest-load-share zone per multi-zone ISO, used as the defensive
# fallback when a plant's ORIS code is not present in the eGRID lookup.
# CAISO falls back to SP15: the SCE+SDG&E south is the largest-load-share
# zone (0.50) and is where unlocated imports physically land via the
# West-of-River / Palo Verde ties. PJM falls back to PJM_West: the western
# AEP/ComEd belt is the largest-load-share zone (0.504) and is where the
# unlocated MISO/PJM-seam plants geographically sit. NYISO falls back to
# Upstate-West, its largest-load-share zone (0.365).
_LARGEST_ZONE: dict[str, str] = {
    "ERCOT": "North",
    "PJM": "PJM_West",
    "CAISO": "SP15",
    # MISO-Central is the largest-load-share zone (0.46) and holds the
    # lower-Midwest load centers, so unlocated MISO plants land there.
    "MISO": "MISO-Central",
    "NYISO": "Upstate_West",
    # Central (WCMA/SEMA/RI) is ISO-NE's largest-load-share zone (0.30) and
    # holds central/coastal Massachusetts, so unlocated NEISO plants land there.
    "NEISO": "Central",
    # SPP-North is the largest-load-share zone (0.52) — the Kansas/Nebraska
    # core plus the Kansas-City metro — so unlocated SPP plants land there.
    "SPP": "SPP-North",
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
        39,   # Brazoria
        167,  # Galveston
        339,  # Montgomery
        291,  # Liberty
        71,   # Chambers
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

# PJM model zone by FIPS state code, for the states that fall cleanly inside
# one zone. Pennsylvania and Maryland straddle zones and are split by
# longitude/county in ``_pjm_zone`` below, so they are deliberately absent
# here. West rolls up the AEP/ComEd/APS/DAY/ATSI belt (+ DEOK/DUQ/EKPC); East
# is the PSEG/JCPL/PECO/BGE/PEPCO Mid-Atlantic pocket (+ DPL/AECO/RECO); South
# is Dominion (DOM).
_PJM_STATE_ZONES: dict[int, str] = {
    17: "PJM_West",      # IL  (ComEd)
    18: "PJM_West",      # IN  (AEP)
    39: "PJM_West",      # OH  (AEP / ATSI / DAY / DEOK / Duke OH)
    26: "PJM_West",      # MI  (AEP)
    21: "PJM_West",      # KY  (EKPC / Duke KY / AEP KY)
    54: "PJM_West",      # WV  (AEP / APS)
    34: "PJM_East",      # NJ  (PSEG / JCPL / AECO / RECO)
    10: "PJM_East",      # DE  (DPL)
    11: "PJM_East",      # DC  (PEPCO)
    51: "PJM_South",     # VA  (DOM)
    37: "PJM_South",     # NC  (DOM)
    47: "PJM_South",     # TN  (edge of EKPC)
}

# FIPS state codes for the two PJM states that straddle model zones.
_PENNSYLVANIA_FIPS: int = 42
_MARYLAND_FIPS: int = 24

# Pennsylvania splits three ways. The Philadelphia metro (PECO) is the East
# load pocket; the rest divides by longitude — SW/NW PA (APS / Penn Power /
# Duquesne / West Penn, west of ~-78.0) ties West, and the central/north-
# eastern PPL/METED/PENELEC corridor is Central. The Philadelphia-metro county
# codes give the precision longitude alone can't, mirroring the Houston rule.
PJM_PHILLY_COUNTIES: frozenset[int] = frozenset(
    {
        101,  # Philadelphia
        45,   # Delaware
        91,   # Montgomery
        17,   # Bucks
        29,   # Chester
    }
)
_PJM_PA_WEST_LON: float = -78.0

# Maryland: the western panhandle (Garrett / Allegany — APS / Potomac Edison,
# west of ~-78.5) ties West; the rest of the state (BGE / PEPCO / DPL eastern
# shore) is the Mid-Atlantic East.
_PJM_MD_WEST_LON: float = -78.5

# MISO model region by FIPS state code. MISO's defining split is the three
# sub-regions, which follow state lines: the wind-rich upper-Midwest North,
# the lower-Midwest Central load centers, and the Entergy South. eGRID
# carries a FIPS state for every MISO plant, so the state map is authoritative;
# the latitude fallback below only handles the rare coords-only caller.
_MISO_STATE_ZONES: dict[int, str] = {
    27: "MISO-North",     # MN
    19: "MISO-North",     # IA
    55: "MISO-North",     # WI
    38: "MISO-North",     # ND
    46: "MISO-North",     # SD
    30: "MISO-North",     # MT
    17: "MISO-Central",   # IL
    18: "MISO-Central",   # IN
    26: "MISO-Central",   # MI
    29: "MISO-Central",   # MO
    21: "MISO-Central",   # KY
    5: "MISO-South",      # AR
    22: "MISO-South",     # LA
    28: "MISO-South",     # MS
    48: "MISO-South",     # TX (MISO East Texas / Entergy, not ERCOT)
}

# Latitude bands for the coords-only MISO fallback (no FIPS state). The
# Entergy South footprint sits below ~lat 36 (AR/LA/MS/East TX); the upper-
# Midwest North sits above ~lat 43 (MN/ND/SD/WI); the lower-Midwest Central
# load centers fall between. This is coarse — FIPS state is preferred — and
# only triggers when a caller supplies coordinates without a state code.
_MISO_SOUTH_LAT: float = 36.0
_MISO_NORTH_LAT: float = 43.0

# FIPS state code for New York. NYISO's eleven load zones (A–K) follow
# county lines closely enough that county FIPS carries the assignment, with
# a lat/lon fallback for out-of-state merchant resources (the NJ HVDC/VFT
# cables that inject downstate) and any plant lacking a NY county code.
_NEW_YORK_FIPS: int = 36

# NYC (zone J) — the five boroughs.
NYISO_NYC_COUNTIES: frozenset[int] = frozenset(
    {
        5,    # Bronx
        47,   # Kings (Brooklyn)
        61,   # New York (Manhattan)
        81,   # Queens
        85,   # Richmond (Staten Island)
    }
)

# Long Island (zone K).
NYISO_LONG_ISLAND_COUNTIES: frozenset[int] = frozenset(
    {
        59,   # Nassau
        103,  # Suffolk
    }
)

# Lower-Hudson (zones H Millwood + I Dunwoodie) — the Westchester/Putnam
# pocket north of NYC and south of the UPNY-SENY interface.
NYISO_LOWER_HUDSON_COUNTIES: frozenset[int] = frozenset(
    {
        119,  # Westchester (Con Ed — zones H and I)
        79,   # Putnam
    }
)

# Capital/Hudson (zones F Capital + G Hudson Valley) — the eastern-NY
# corridor between the Central-East and UPNY-SENY interfaces. Every other
# NY county falls through to Upstate-West (zones A–E), which keeps the
# Niagara (zone A) and St. Lawrence (zone D) hydro upstate.
NYISO_CAPITAL_HUDSON_COUNTIES: frozenset[int] = frozenset(
    {
        1,    # Albany (F)
        21,   # Columbia (F)
        39,   # Greene (F)
        83,   # Rensselaer (F)
        91,   # Saratoga (F)
        93,   # Schenectady (F)
        95,   # Schoharie (F)
        113,  # Warren (F)
        115,  # Washington (F)
        27,   # Dutchess (G)
        71,   # Orange (G)
        87,   # Rockland (G)
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
    23: "North",        # ME
    33: "North",        # NH
    50: "North",        # VT
    9: "Connecticut",   # CT
    44: "Central",      # RI (part of the WCMA/SEMA/RI aggregate)
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
        9,   # Essex (Salem Harbor)
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

# SPP model region by FIPS state code. SPP's two zones split the footprint
# north/south: the Kansas/Nebraska core and the upper-Plains states (the
# Dakotas, Minnesota, Iowa, eastern Colorado and far-eastern Montana) sit in
# SPP-North; the Oklahoma core, the Xcel SPS Texas-panhandle / eastern-New-
# Mexico footprint, and the SWEPCO northwest-Louisiana / Arkansas footprint
# sit in SPP-South. Missouri straddles the divide (Kansas-City metro north,
# Empire District southwest-Missouri south) and is split by latitude below.
# eGRID carries a FIPS state for every SWPP plant, so the state map is
# authoritative; the latitude fallback only handles the rare coords-only caller.
_SPP_STATE_ZONES: dict[int, str] = {
    20: "SPP-North",   # KS
    31: "SPP-North",   # NE
    19: "SPP-North",   # IA
    27: "SPP-North",   # MN
    46: "SPP-North",   # SD
    38: "SPP-North",   # ND
    30: "SPP-North",   # MT (far-eastern Montana: Basin Electric / WAPA UGP)
    8: "SPP-North",    # CO (Denver-metro & southeastern-Colorado SPP load)
    40: "SPP-South",   # OK
    48: "SPP-South",   # TX (panhandle: Xcel SPS / Southwestern Public Service)
    35: "SPP-South",   # NM (eastern New Mexico: Xcel SPS)
    22: "SPP-South",   # LA (northwest Louisiana: SWEPCO)
    5: "SPP-South",    # AR (Arkansas SPP: SWEPCO / AECC)
}

# Missouri straddles the SPP north–south divide. The Kansas-City metro
# (Evergy / KCP&L, ~lat 39) sits in SPP-North; the Empire District /
# City-Utilities-of-Springfield southwest-Missouri load (~lat 37) sits in
# SPP-South. The 38th parallel separates the two clusters in the eGRID data.
_SPP_MISSOURI_FIPS: int = 29
_SPP_MISSOURI_NORTH_LAT: float = 38.0

# Latitude band for the coords-only SPP fallback (no FIPS state). The KS/OK
# border — the 37th parallel — is the canonical SPP north/south geographic
# divide: Kansas and north sit in SPP-North, Oklahoma and south in SPP-South.
# Coarse; FIPS state is preferred and this only triggers when a caller supplies
# coordinates without a state code.
_SPP_NORTH_LAT: float = 37.0

# Cached parsed eGRID DataFrame and derived ORIS→location lookup, so the
# 21 MB workbook is read at most once per process.
_PLNT23_CACHE: pd.DataFrame | None = None
_ORIS_TO_LOCATION: dict[int, tuple[float | None, float | None, int | None, int | None]] | None = None


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


def _plnt23() -> pd.DataFrame:
    """Return the eGRID PLNT23 sheet, parsing and caching it on first call.

    The PLNT23 sheet's first row holds long descriptive headers; ``skiprows=1``
    drops it so the short-code header row (ORISPL, LAT, LON, ...) becomes the
    column index.
    """
    global _PLNT23_CACHE
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
    if lon is not None and lon < -99.5:
        # West Texas Export interface: the Panhandle wind belt sits north of
        # the CREZ belt / Permian behind its own stability-limited GTC.
        if lat is not None and lat >= 33.5:
            return "Panhandle"
        return "West"
    if (
        lat is not None
        and lon is not None
        and lat >= 31.0
        and -99.5 <= lon < -95.5
    ):
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

    Zones follow CAISO's north–south split: NP15 (north of Path 15), ZP26
    (between Path 15 and Path 26), SP15 (south of Path 26). Out-of-state CISO
    resources are routed first — Arizona (Palo Verde / West-of-River) lands
    in SP15, Nevada ties to NP15 in the far north and SP15 otherwise. Coastal
    PG&E counties that fall in the ZP26 latitude band are lifted to NP15.
    Latitude then carries the remaining (inland California) plants; with no
    latitude the largest-load-share zone (SP15) is the fallback.
    """
    if fips_state == _ARIZONA_FIPS:
        return "SP15"
    if fips_state == _NEVADA_FIPS:
        if lat is not None and lat >= _NEVADA_NORTH_LAT:
            return "NP15"
        return "SP15"
    if (
        fips_state == _CALIFORNIA_FIPS
        and fips_county in CAISO_CENTRAL_COAST_NP15_COUNTIES
    ):
        return "NP15"
    if lat is not None:
        if lat >= _CAISO_PATH15_LAT:
            return "NP15"
        if lat >= _CAISO_PATH26_LAT:
            return "ZP26"
        return "SP15"
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
    """Return the PJM model zone for a plant location.

    Most states map cleanly to one zone via ``_PJM_STATE_ZONES``. Pennsylvania
    and Maryland straddle zones: the Philadelphia metro (PECO counties) is
    East, western PA/MD ties West by longitude, and the rest of PA is the
    Central PPL/METED/PENELEC corridor. A plant whose state is unknown (or a PA
    plant with no longitude to place it west) falls back to the Central PA
    default; a plant with no usable location at all falls back to the
    largest-load-share zone (PJM_West).
    """
    if fips_state == _PENNSYLVANIA_FIPS:
        if fips_county in PJM_PHILLY_COUNTIES:
            return "PJM_East"
        if lon is not None and lon <= _PJM_PA_WEST_LON:
            return "PJM_West"
        return "PJM_Central"
    if fips_state == _MARYLAND_FIPS:
        if lon is not None and lon <= _PJM_MD_WEST_LON:
            return "PJM_West"
        return "PJM_East"
    return _PJM_STATE_ZONES.get(fips_state, _LARGEST_ZONE["PJM"])


def _miso_zone(lat: float | None, fips_state: int | None) -> str:
    """Return the MISO model region for a plant location.

    FIPS state carries the assignment — North (upper Midwest), Central
    (lower-Midwest load centers), South (Entergy) — since MISO's three
    sub-regions follow state lines and eGRID has a state for every plant.
    A plant whose state is outside the MISO map (a stray cross-seam
    attribution) falls back to a coarse latitude band when coordinates are
    available, and otherwise to the largest-load-share zone (Central).
    """
    if fips_state in _MISO_STATE_ZONES:
        return _MISO_STATE_ZONES[fips_state]
    if lat is not None:
        if lat < _MISO_SOUTH_LAT:
            return "MISO-South"
        if lat >= _MISO_NORTH_LAT:
            return "MISO-North"
        return "MISO-Central"
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
    """Return the SPP model region for a plant location.

    FIPS state carries the assignment — SPP-North (the Kansas/Nebraska core
    and the upper-Plains states) or SPP-South (Oklahoma, the Xcel SPS
    panhandle / eastern New Mexico, and SWEPCO Louisiana/Arkansas) — since
    SPP's two zones follow state lines and eGRID has a state for every SWPP
    plant. Missouri straddles the divide and is split by latitude (Kansas-City
    metro north, Empire District southwest-Missouri south). A plant whose
    state is outside the SPP map falls back to a coarse latitude band (the
    37th-parallel KS/OK divide) when coordinates are available, and otherwise
    to the largest-load-share zone (North).
    """
    if fips_state == _SPP_MISSOURI_FIPS:
        if lat is not None:
            if lat >= _SPP_MISSOURI_NORTH_LAT:
                return "SPP-North"
            return "SPP-South"
        return _LARGEST_ZONE["SPP"]
    if fips_state in _SPP_STATE_ZONES:
        return _SPP_STATE_ZONES[fips_state]
    if lat is not None:
        if lat >= _SPP_NORTH_LAT:
            return "SPP-North"
        return "SPP-South"
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
    if iso == "SPP":
        return _spp_zone(lat, fips_state)
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


def _eia860_ercot_zones() -> dict[int, str]:
    """Return ``{oris: zone}`` for ERCOT plants from the EIA-860 plant file.

    The EIA-860 plant file carries current latitude/longitude and
    balancing-authority codes, so it covers plants too new for the eGRID
    2023 vintage (notably 2024+ wind, solar and storage). Plants in the
    ERCO balancing authority are zoned from their coordinates.

    Returns an empty dict when the EIA-860 plant file is unavailable.
    """
    if not _EIA860_PLANT_PATH.exists():
        return {}
    df = pd.read_parquet(_EIA860_PLANT_PATH)
    ba = df["Balancing Authority Code"].astype(str).str.strip()
    df = df[ba == _ISO_TO_BA_CODE["ERCOT"]]

    codes = df["Plant Code"].to_numpy()
    lats = pd.to_numeric(df["Latitude"], errors="coerce").to_numpy()
    lons = pd.to_numeric(df["Longitude"], errors="coerce").to_numpy()

    out: dict[int, str] = {}
    for code, lat, lon in zip(codes, lats, lons):
        oris = _to_int(code)
        if oris is None or lat != lat or lon != lon:  # None / NaN coords
            continue
        out[oris] = _ercot_zone(float(lat), float(lon), None, None)
    return out


def build_zone_lookup(iso: str) -> dict[int, str]:
    """Return ``{oris: zone_name}`` for every plant in the ISO.

    Zones come from eGRID 2023 plant coordinates. For ERCOT the lookup is
    then supplemented from the current EIA-860 plant file, which covers
    plants too new for the eGRID vintage; eGRID stays authoritative where
    it has the plant, as it also carries the FIPS county the Houston-zone
    rule needs.

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

    if iso == "ERCOT":
        for oris, zone in _eia860_ercot_zones().items():
            lookup.setdefault(oris, zone)
    return lookup
