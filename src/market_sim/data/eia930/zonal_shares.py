"""Measured hourly zonal load shares for :mod:`market_sim.data.eia930`.

The per-ISO zone-group crosswalks (real load zone -> model transmission zone),
the hour-of-year share-matrix builders shared with
``scripts/data/curate_zonal_shares.py``, and ``load_zonal_shares`` (clean
Parquet primary, raw-file fallback). Split out of ``data/eia_loader.py`` as
pure code motion (W-D2, 2026-07-20).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import CAISO_TAC_ZONE_WEIGHTS, HOURS_PER_YEAR
from market_sim.config.paths import ZONE_DEMAND_DIR

from .frames import (
    _MONTH_START_HOUR,
    _eia_hourly_frame_filled,
    _read_clean_seam,
    logger,
)


# PJM (metered, 20 transmission zones) and ERCOT (NP3-565-CD native load, 8
# weather zones) both publish per-zone hourly load here, one file per year.
# Used to give each model zone its *own* hourly load shape (zones peak at
# different times) instead of a single system shape scaled by a static share.
_ZONAL_LOAD_DIR: Path = ZONE_DEMAND_DIR
# Back-compat alias (PJM-specific name) for any external importer.
_PJM_ZONAL_LOAD_DIR: Path = _ZONAL_LOAD_DIR

# ERCOT weather-zone column (in ERCOT_Native_Load_<year>.xlsx) -> model
# transmission zone (the seven-zone topology in iso_configs._ercot_config).
# ERCOT has no Panhandle weather zone, so the Panhandle model zone receives no
# load here (its share stays 0.0, matching the static config); the small Lubbock
# load it would hold sits inside the WEST weather zone and lands in the West
# model zone. The EAST weather zone is its own Northeast model zone (behind the
# NE_LOB export limit). The ERCOT system-total column is dropped. Mirrors the
# aggregation in scripts/data/derive_load_shares.py that seeded the load_share values.
_ERCOT_LOAD_ZONE_GROUPS: dict[str, str] = {
    "COAST": "Houston",
    "EAST": "Northeast",
    "NORTH": "North",
    "NCENT": "North",
    "SCENT": "South_Central",
    "SOUTH": "South",
    "FWEST": "West",
    "WEST": "West",
}

# CAISO TAC-area actual hourly load (upload U4: OASIS SLD_FCST with
# market_run_id=ACTUAL, monthly pulls) -> model zone weights. The "CA ISO-TAC"
# system-total rows are dropped and shares are normalized over the component
# TACs. Weights themselves now live in constants.CAISO_TAC_ZONE_WEIGHTS.
_CAISO_TAC_ZONE_WEIGHTS: dict[str, dict[str, float]] = CAISO_TAC_ZONE_WEIGHTS

# NYISO settlement zone (OASIS "pal" actual-load zone names) -> model
# transmission zone. Maps the eleven NYISO load zones (A–K) onto the five
# model zones that aggregate them along the binding downstate-import interfaces
# (Central-East / Total-East cutset, UPNY-SENY, Dunwoodie-South, Long Island
# import). Both the single-letter form (A–K) and the OASIS PTID-name form are
# accepted so the parser handles whichever column the upload carries.
#
# Aggregation: A+B+C+D+E → Upstate_West  (cheap upstate generation belt)
#              F+G        → Capital_Hudson (Capital District + Hudson Valley)
#              H+I        → Lower_Hudson   (Millwood + Dunwoodie pocket)
#              J          → NYC            (New York City)
#              K          → Long_Island    (Long Island / LIPA territory)
_NYISO_LOAD_ZONE_GROUPS: dict[str, str] = {
    # Zone A — West (Niagara frontier)
    "A": "Upstate_West",
    "WEST": "Upstate_West",
    # Zone B — Genesee
    "B": "Upstate_West",
    "GENESE": "Upstate_West",
    # Zone C — Central
    "C": "Upstate_West",
    "CENTRL": "Upstate_West",
    # Zone D — North
    "D": "Upstate_West",
    "NORTH": "Upstate_West",
    # Zone E — Mohawk Valley
    "E": "Upstate_West",
    "MHK VL": "Upstate_West",
    # Zone F — Capital District
    "F": "Capital_Hudson",
    "CAPITL": "Capital_Hudson",
    # Zone G — Hudson Valley
    "G": "Capital_Hudson",
    "HUD VL": "Capital_Hudson",
    # Zone H — Millwood (Lower Hudson)
    "H": "Lower_Hudson",
    "MILLWD": "Lower_Hudson",
    # Zone I — Dunwoodie (Lower Hudson)
    "I": "Lower_Hudson",
    "DUNWOD": "Lower_Hudson",
    # Zone J — New York City
    "J": "NYC",
    "N.Y.C.": "NYC",
    # Zone K — Long Island
    "K": "Long_Island",
    "LONGIL": "Long_Island",
}

# Directory for NYISO zonal actual-load CSVs (upload U3). Absent until the
# user uploads NYISO OASIS "pal" actual-load files.
_NYISO_ZONAL_LOAD_DIR: Path = _ZONAL_LOAD_DIR / "NYISO"

# ISO-NE SMD load zone -> model transmission zone. Maps the eight ISO-NE load
# zones onto the four model zones (North = ME+NH+VT, Central = WCMASS+SEMASS+RI,
# Boston = NEMA, Connecticut = CT). The ``.H.<zone>`` hub-prefixed column
# variants the SMD downloads sometimes carry are accepted alongside the bare
# names. ``HQ_import`` is a priced node, not a load zone, so it is absent here.
_NEISO_LOAD_ZONE_GROUPS: dict[str, str] = {
    "ME": "North",
    "NH": "North",
    "VT": "North",
    "NEMA": "Boston",
    ".H.NEMA": "Boston",
    "SEMASS": "Central",
    ".H.SEMASS": "Central",
    "WCMASS": "Central",
    ".H.WCMASS": "Central",
    "RI": "Central",
    "CT": "Connecticut",
}

# Minimum measured TAC hours to derive CAISO zonal shapes from a partial-year
# upload (U4 lands month by month); below this, fall back to static shares.
_CAISO_TAC_MIN_HOURS: int = 28 * 24


# Real PJM transmission zone -> model zone (the eight-zone aggregation in
# iso_configs._pjm_config). ``RTO`` is the system total and is dropped.
_PJM_LOAD_ZONE_GROUPS: dict[str, str] = {
    "CE": "PJM_ComEd",
    "AEP": "PJM_AEP_Ohio",
    "DAY": "PJM_AEP_Ohio",
    "DEOK": "PJM_AEP_Ohio",
    "OVEC": "PJM_AEP_Ohio",
    "ATSI": "PJM_ATSI",
    "AP": "PJM_West_APS",
    "DUQ": "PJM_West_APS",
    "PL": "PJM_Central_PA",
    "PN": "PJM_Central_PA",
    "ME": "PJM_Central_PA",
    "EKPC": "PJM_Central_PA",
    "DOM": "PJM_Dominion",
    "PS": "PJM_EMAAC",
    "JC": "PJM_EMAAC",
    "PE": "PJM_EMAAC",
    "DPL": "PJM_EMAAC",
    "AE": "PJM_EMAAC",
    "RECO": "PJM_EMAAC",
    "BC": "PJM_SWMAAC",
    "PEP": "PJM_SWMAAC",
}


def _hours_of_year(ts: pd.Series) -> np.ndarray:
    """Map naive timestamps to an hour-of-year index on the non-leap clock.

    Feb 29 must already be removed by the caller; this returns indices into
    ``[0, HOURS_PER_YEAR)`` using the fixed non-leap month lengths.
    """
    return (
        np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )


def _hourly_shares_from_groups(
    mzone: pd.Series, hoy: np.ndarray, mw: pd.Series, zone_names: list[str]
) -> np.ndarray:
    """Build a ``(n_zones, HOURS_PER_YEAR)`` hourly load-share matrix.

    Sums ``mw`` into a (model zone, hour-of-year) grid, back-fills any all-zero
    hour (e.g. a DST spring-forward gap) from the previous hour, and normalizes
    each hour to fractions summing to 1.0 across zones. Zones absent from the
    data (such as ERCOT's Panhandle) keep an all-zero row.
    """
    zone_idx = {z: i for i, z in enumerate(zone_names)}
    grid = np.zeros((len(zone_names), HOURS_PER_YEAR), dtype=float)
    grp = (
        pd.DataFrame({"mzone": mzone.to_numpy(), "hoy": hoy, "mw": mw.to_numpy()})
        .groupby(["mzone", "hoy"], observed=True)["mw"]
        .sum()
    )
    for (mz, h), v in grp.items():
        if mz in zone_idx and 0 <= h < HOURS_PER_YEAR:
            grid[zone_idx[mz], int(h)] = v
    col_tot = grid.sum(axis=0)
    for h in np.nonzero(col_tot == 0.0)[0]:
        grid[:, h] = grid[:, h - 1] if h > 0 else grid[:, h + 1]
        col_tot[h] = grid[:, h].sum()
    return grid / col_tot[None, :]


def _validate_zonal_shares(
    iso: str, year: int, zone_names: list[str], shares: np.ndarray, origin: str
) -> np.ndarray:
    """Reject an all-zero row for any zone that carries static load.

    A zone that legitimately carries no load (ERCOT Panhandle, CAISO/NEISO
    import nodes) has static ``load_share == 0``; any zone with a positive
    static share must have a live measured column. An all-zero row there is a
    stale-parquet / bad-mapping bug (the exact hazard of the MISO 3→6-zone
    rename), never a silent degradation, so it is a hard error.
    """
    from market_sim.config.iso_configs import get_iso_config

    static_share = {z.name: z.load_share for z in get_iso_config(iso).zones}
    dead = [
        z
        for i, z in enumerate(zone_names)
        if static_share.get(z, 0.0) > 0.0 and not np.any(shares[i])
    ]
    if dead:
        raise ValueError(
            f"zonal-shares ({origin}) for {iso} {year} has all-zero shares for "
            f"load-carrying zone(s) {dead} — stale parquet under old zone names "
            "or a broken raw mapping? Re-run scripts/data/curate_zonal_shares.py."
        )
    return shares


def _zonal_shares_from_raw(
    iso: str, year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Build measured hourly zonal shares straight from the raw demand file.

    Falls back to the per-ISO parsers in ``scripts.data.curate_zonal_shares`` (the
    single source of the raw-file parsing the clean curation also uses, so the
    raw and clean paths are byte-identical) when the clean Parquet has not been
    materialised. ``data/clean`` is derived and gitignored, so in a fresh clone
    the curated parquet is absent; without this fallback the LP would silently
    drop to the static Gold-Book ``load_share`` and lose every zone's measured
    diurnal/seasonal shape — the downstate-pocket peaking that G-20c depends on.
    Returns ``None`` when the raw file is absent (caller then uses the static
    share) or the scripts package is off ``sys.path``.
    """
    try:
        from scripts.data.curate_zonal_shares import _PARSE_FUNCS
    except Exception:  # pragma: no cover - only when scripts/ is off sys.path
        logger.debug("scripts.data.curate_zonal_shares unavailable; static shares")
        return None
    parse_fn = _PARSE_FUNCS.get(iso)
    if parse_fn is None:
        return None
    try:
        shares = parse_fn(year, zone_names)
    except Exception as exc:
        logger.warning("raw zonal-shares parse failed for %s %d: %s", iso, year, exc)
        return None
    if shares is None:
        return None
    return _validate_zonal_shares(iso, year, zone_names, shares, "raw")


def load_zonal_shares(iso: str, year: int, zone_names: list[str]) -> np.ndarray | None:
    """Load measured hourly zonal load-share fractions.

    Returns a ``(n_zones, HOURS_PER_YEAR)`` array of hourly fractional load
    shares (each column sums to 1.0 across zones), so each model zone gets its
    own measured diurnal/seasonal shape instead of a single static fraction
    broadcast flat across the year. Prefers the curated ``zonal-shares`` clean
    Parquet (``scripts/data/curate_zonal_shares.py``); when that has not been
    materialised — ``data/clean`` is derived and gitignored, so it is absent in
    a fresh clone — it falls back to parsing the raw
    ``data/raw/zone-specific-demand`` file directly (:func:`_zonal_shares_from_raw`).
    Both paths share the same parsing, so the fallback is byte-identical to the
    clean parquet. Returns ``None`` only when neither the parquet nor a raw file
    exists, in which case the caller uses the static per-zone ``load_share``.

    Args:
        iso: ISO code (e.g. ``"ERCOT"``).
        year: Calendar year.
        zone_names: Model zone names in the order the caller expects (must
            match the zones written by the curation script).

    Returns:
        ``(n_zones, HOURS_PER_YEAR)`` float64 array, or ``None`` if no measured
        source (clean parquet or raw file) is available for this ISO-year.
    """
    seam = _read_clean_seam()
    if seam is not None:
        read_clean, clean_exists = seam
        if clean_exists("zonal-shares", iso=iso, year=year):
            try:
                df = read_clean("zonal-shares", iso=iso, year=year, validate=False)
            except Exception as exc:
                logger.warning("zonal-shares read failed for %s %d: %s", iso, year, exc)
            else:
                pivot = df.pivot(index="hour", columns="zone", values="share")
                pivot = pivot.reindex(columns=zone_names, fill_value=0.0)
                shares = pivot.to_numpy(dtype=float).T
                return _validate_zonal_shares(iso, year, zone_names, shares, "clean")
    # Clean parquet absent (or read failed / seam off): use the measured raw file.
    return _zonal_shares_from_raw(iso, year, zone_names)


# EIA-930 MISO sub-BA -> model zone. EIA-930 reports MISO sub-BA hourly demand
# at exactly six LRZ-group partitions, and the six model zones are drawn as
# exactly those groups — a 1:1 map, the finest partition with fully measured
# hourly load (docs/multi-iso/miso-zonal-refinement-scope.md §1). The fleet
# partition (zone_assignment._MISO_STATE_ZONES) shares identical whole-state
# sub-BA-union boundaries. Source: EIA-930 region-sub-ba-data, parent=MISO;
# crosswalk per docs/multi-iso/miso-data-audit.md Item 2.
_MISO_SUBBA_ZONE_GROUPS: dict[str, str] = {
    "0001": "MISO-West",  # LRZ 1: MN, ND, SD, MT (wind belt)
    "0035": "MISO-Plains",  # LRZ 3+5: IA, MO (Iowa wind-export corridor)
    "0004": "MISO-Illinois",  # LRZ 4: IL (Ameren wheel-through zone)
    "0006": "MISO-Indiana",  # LRZ 6: IN, KY (load-east anchor)
    "0027": "MISO-East",  # LRZ 2+7: WI, MI (Michigan import pocket + WUMS)
    "8910": "MISO-South",  # LRZ 8+9+10: AR, LA, MS, E. TX (RDT-separated)
}


def _miso_utc_to_local_hoy(period_utc: pd.Series, year: int) -> pd.Series | None:
    """Map UTC timestamps to MISO local hour-of-year on the renewable clock.

    The MISO sub-BA demand CSV stamps its ``period`` in UTC, but the renewable
    CF and system demand the zonal shares are multiplied into live on MISO local
    wall-clock time (the EIA-930 ``MISO hourly`` extract's ``Local time``). To
    keep all three on one clock, each UTC period is mapped through the hourly
    frame's *own* ``UTC time`` -> row-index correspondence: frame row k is local
    hour-of-year k (Feb 29 already dropped, DST handled by the extract), so the
    returned index lands the share at the same wall-clock hour the renewables
    use. This derives the offset from the clock itself — no IANA-zone or
    fixed-offset assumption — and stays valid for any forward year that ships a
    frame. Periods outside the local-year UTC window map to NaN (the caller
    drops them). Returns ``None`` when the MISO frame is unavailable.
    """
    frame = _eia_hourly_frame_filled("MISO", year)
    if frame is None:
        return None
    # frame row k == model local hour-of-year k; invert UTC time -> k.
    utc_index = pd.DatetimeIndex(frame["UTC time"])
    hoy_of_utc = pd.Series(np.arange(len(frame), dtype=float), index=utc_index)
    hoy_of_utc = hoy_of_utc[~hoy_of_utc.index.duplicated(keep="first")]
    return period_utc.map(hoy_of_utc)
