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

# Model ISO name → eGRID balancing-authority code (BACODE column).
_ISO_TO_BA_CODE: dict[str, str] = {
    "ERCOT": "ERCO",
    "CAISO": "CISO",
    "PJM": "PJM",
    "NYISO": "NYIS",
    "NEISO": "ISNE",
}

# ISOs modeled as a single zone, with that zone's name.
_SINGLE_ZONE: dict[str, str] = {
    "CAISO": "CAISO_main",
    "NYISO": "NYISO_main",
    "NEISO": "NEISO_main",
}

# Largest-load-share zone per multi-zone ISO, used as the defensive
# fallback when a plant's ORIS code is not present in the eGRID lookup.
_LARGEST_ZONE: dict[str, str] = {
    "ERCOT": "North",
    "PJM": "PJM_West",
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

# PJM model zone by FIPS state code. Captures the major transmission
# interfaces (West→East, AP South→Mid-Atlantic) without LDA granularity.
_PJM_STATE_ZONES: dict[int, str] = {
    17: "PJM_West",      # IL
    18: "PJM_West",      # IN
    39: "PJM_West",      # OH
    26: "PJM_West",      # MI
    42: "PJM_Central",   # PA
    54: "PJM_Central",   # WV
    21: "PJM_Central",   # KY
    34: "PJM_East",      # NJ
    10: "PJM_East",      # DE
    24: "PJM_East",      # MD
    11: "PJM_East",      # DC
    51: "PJM_South",     # VA
    37: "PJM_South",     # NC
    47: "PJM_South",     # TN
}

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


def _pjm_zone(fips_state: int | None) -> str:
    """Return the PJM model zone for a plant's FIPS state code."""
    return _PJM_STATE_ZONES.get(fips_state, _LARGEST_ZONE["PJM"])


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
    if iso == "PJM":
        return _pjm_zone(fips_state)
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

    For single-zone ISOs (CAISO, NYISO, NEISO) the main zone is returned
    without a lookup. For multi-zone ISOs the plant is located via the
    eGRID ORIS→location table; an ORIS code missing from eGRID falls back
    to the ISO's largest-load-share zone with a warning.
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


def build_zone_lookup(iso: str) -> dict[int, str]:
    """Return ``{oris: zone_name}`` for every eGRID plant in the ISO.

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
    return lookup
