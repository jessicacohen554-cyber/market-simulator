"""Historic generator-outage overlay for ERCOT calibration backcasts.

Reads the committed ERCOT outage extract (``data/raw/ercot-outages.csv``)
and turns sustained coal / combined-cycle outages into per-plant hourly
availability masks on the model's fixed 8760-hour clock. The masks are applied
by :func:`market_sim.data.fleet.generators_to_fleet_arrays` only when a
backcast config sets ``outage_source == "historic"``; forward/forecast runs
keep the statistical WEFOR/POF availability model.

Filter (user directive): only outages at COAL or COMBINED-CYCLE plants
(``Plant_Group`` in :data:`QUALIFYING_PLANT_GROUPS`) whose start->stop span is
at least :data:`MIN_OUTAGE_SPAN_HOURS` (2 days) are overlaid. The detector
(scripts/derive_campd_outages.py) defines an outage as a sustained CF < 5%
gap of >= 2 days, so a unit idling at low output (5-10% CF, e.g. J K Spruce)
is *not* outaged, while genuine multi-day full-off gaps are. The CSV's
``duration_hours`` column is unreliable and is NOT used to measure outage
length; the span is ``outage_stop - outage_start``.
"""

from __future__ import annotations

import calendar
import logging
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import CALIBRATION_DIR, CAMPD_BINS_CSV, RAW_DATA_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Clean-data read seam (MARKET_SIM_USE_CLEAN, default OFF)
# ---------------------------------------------------------------------------
# When this env flag is set, the facility-outage overlay sources its windows
# from the curated clean tree (data/clean/outages, written by
# scripts/curate_outages.py through the frozen scripts/lib/clean_io.py seam)
# instead of re-deriving them from raw here. The raw/derive path below stays the
# default and is left fully intact; the flag is a migration gate, not a switch
# we flip in code. See data/README.md and data/dictionary/schema/outages.schema.yaml.
_USE_CLEAN_ENV = "MARKET_SIM_USE_CLEAN"
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _use_clean() -> bool:
    """Whether to read outages from the clean tree (MARKET_SIM_USE_CLEAN)."""
    return os.environ.get(_USE_CLEAN_ENV, "").strip().lower() in _TRUTHY


def _clean_io():
    """Import the frozen clean-data read seam (``scripts/lib/clean_io.py``).

    The model package does not put the repo root — where the ``scripts``
    package lives — on ``sys.path``, so add it before importing. This module is
    the contract; we only ever read through it (never edit it).
    """
    try:
        import scripts.lib.clean_io as clean_io
    except ModuleNotFoundError:
        import sys

        from market_sim.config import paths

        repo = str(paths.REPO_ROOT)
        if repo not in sys.path:
            sys.path.insert(0, repo)
        import scripts.lib.clean_io as clean_io
    return clean_io


def read_clean_outages(
    year: int, *, columns: list[str] | None = None, validate: bool = True
) -> pd.DataFrame:
    """Load per-unit hourly availability for ``year`` from the clean tree.

    The clean-backed read seam (gated by :func:`_use_clean`). Returns the
    per-``(plant_id, unit_id)`` hourly outage / availability rows curated by
    ``scripts/curate_outages.py`` and validated against
    ``data/dictionary/schema/outages.schema.yaml`` — ``outage_mw`` is the
    capacity offline during the interval and ``available_mw`` the capacity
    available (plant nameplate minus that). Facility-grain rows carry
    ``unit_id == "ALL"``.

    Reads through :func:`scripts.lib.clean_io.read_clean`, which raises
    :class:`FileNotFoundError` (with a regenerate hint) when the partition is
    absent. The clean tree is gitignored, so regenerate it from raw with
    ``python scripts/regenerate_clean.py outages`` first.
    """
    clean_io = _clean_io()
    return clean_io.read_clean(
        "outages", year=int(year), columns=columns, validate=validate
    )


# Default ERCOT historic-outage extract, resolved relative to the repository
# root (this file lives at src/market_sim/data/outages.py). One row per
# outage event: oris_code, plant_name, unit, outage_start, outage_stop,
# duration_hours.
#
# Default source is the CAMPD-derived window set (scripts/derive_campd_outages.py):
# every coal/CC plant the CEMS extract covers, with a "real run" = sustained
# CF > 10% so brief test blips don't end an outage. This replaces the sparse
# hand-maintained ercot-outages.csv (kept in the repo for reference), which
# only covered a handful of plants and missed e.g. San Miguel's spring/fall
# blocks. The > 10-day span filter (MIN_OUTAGE_SPAN_HOURS) still selects only
# sustained maintenance from these windows.
OUTAGES_CSV: Path = RAW_DATA_DIR / "campd-outages.csv"

# Default CAMPD bin-assignment CSV, the plant_code -> Plant_Group source used
# to decide which plants are coal/CC. Matches ScenarioConfig.campd_bins_path.
BINS_CSV_DEFAULT: str = str(CAMPD_BINS_CSV)

# Per-ISO historic-outage extract. ERCOT keeps the original file name (so the
# ERCOT backcast is unchanged); other ISOs use ``campd-outages-{ISO}.csv``,
# written by ``scripts/derive_campd_outages.py --iso <ISO>`` from that ISO's
# CAMPD CEMS state extracts. Those per-ISO files already contain only coal/CC/
# gas-steam plants (the derivation's GROUPS filter), so the overlay trusts
# them without re-intersecting against an ISO-specific bin CSV.
_OUTAGES_DIR: Path = RAW_DATA_DIR


def default_outages_path(iso: str | None) -> Path:
    """Return the historic-outage CSV path for an ISO (ERCOT = the legacy file)."""
    if iso is None or iso.upper() == "ERCOT":
        return OUTAGES_CSV
    return _OUTAGES_DIR / f"campd-outages-{iso.upper()}.csv"


# Plant groups whose sustained outages are overlaid: coal and combined cycle
# (regular and CHP). A plant qualifies if it has any bin in this set; the
# per-bin group filter at overlay time then restricts the zeroing to those
# coal/CC bins (e.g. Barney M Davis carries both a CC and an ST_GAS bin —
# only the CC bin is outaged).
QUALIFYING_PLANT_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "CC_CHP", "CT_CHP", "ST_GAS", "ST_CHP"}
)

# Peaker-class ST_GAS plants: patchy / spiky run rate (run only when called),
# so they get NO outage overlay (and no reliability min-gen floor in
# fleet.generators_to_fleet_arrays) — they dispatch purely economically. The
# remaining ST_GAS units run sustained idling / drag patterns and DO get the
# outage + reliability treatment. Excluded from the overlay below.
ST_GAS_PEAKER_PLANTS: frozenset[int] = frozenset(
    {
        # ERCOT
        3504,  # Stryker Creek
        3453,  # Mountain Creek
        3490,  # Graham
        3507,  # Trinidad (TX)
        3576,  # Ray Olinger
        4266,  # Spencer
        # CAISO — the last once-through-cooling steamers, kept on OTC compliance
        # extensions as RMR-style reliability units. CAMPD 2024-25 shows them
        # online only 0.4-2.5% of hours (spiky, run-when-called), so the
        # event-based outage rule would flood them with economic-idleness
        # windows; they dispatch purely economically instead.
        315,  # AES Alamitos LLC units 3-5 (legacy boilers; the colocated
        #   CCGT reports under this ORIS too but is remapped to EIA
        #   62115 — campd.CAMPD_UNIT_PLANT_REMAP)
        335,  # AES Huntington Beach LLC unit 2 (CCGT remapped to 62116)
        350,  # Ormond Beach units 1-2
    }
)

# Minimum outage span to overlay, in hours (>= 2 days). The CAMPD detector
# (scripts/derive_campd_outages.py) already defines an outage as a sustained
# CF < 5% gap of at least this length, so the overlay applies every window it
# emits; this guards against any shorter stray windows.
MIN_OUTAGE_SPAN_HOURS: int = 48

# Days before each 1-based month in a NON-leap year, so _DAYS_BEFORE_MONTH[m]
# is the 0-based day-of-year of month m's first day ([1]=0 for Jan 1, [2]=31
# for Feb 1, ..., [12]=334 for Dec 1). Index 0 is unused. The model runs on a
# fixed 8760-hour clock keyed to ERCOT-local date with Feb 29 dropped (see
# eia_loader._ercot_hourly_frame), so outage timestamps map onto a non-leap
# calendar.
_DAYS_BEFORE_MONTH: list[int] = [0] * 13
for _m in range(2, 13):
    _DAYS_BEFORE_MONTH[_m] = (
        _DAYS_BEFORE_MONTH[_m - 1] + calendar.monthrange(2023, _m - 1)[1]
    )


def _hour_of_year(month: int, day: int, hour: int) -> int:
    """Map an ERCOT-local (month, day, hour) to a 0-based hour on the clock.

    Uses a non-leap calendar (Feb has 28 days) to match the model's fixed
    8760-hour year. Feb 29 — dropped from the clock in leap years — maps to
    the Mar 1 00:00 boundary (the next hour that exists on the clock); no
    qualifying outage window begins or ends exactly on Feb 29.
    """
    if month == 2 and day >= 29:
        return _DAYS_BEFORE_MONTH[3] * 24  # Mar 1 00:00
    return (_DAYS_BEFORE_MONTH[month] + (day - 1)) * 24 + hour


def outage_hour_mask(
    start: object, stop: object, year: int, hours: int = HOURS_PER_YEAR
) -> np.ndarray:
    """Return a length-``hours`` bool mask of hours covered by ``[start, stop)``.

    ``start`` / ``stop`` are ERCOT-local timestamps (anything pandas can
    coerce). The window is clipped to calendar ``year`` on the model's fixed
    clock: a window that begins in a prior year is covered from hour 0, and
    one that ends in a later year is covered through hour ``hours`` (so a
    year-straddling window such as 2024-12-16 -> 2025-01-03 splits cleanly
    across the two run years). ``stop`` is the return-to-service hour, so the
    interval is half-open and the stop hour itself is not masked. Returns an
    all-False mask when the window does not overlap ``year``.
    """
    mask = np.zeros(hours, dtype=bool)
    start = pd.Timestamp(start)
    stop = pd.Timestamp(stop)
    if stop <= start or start.year > year or stop.year < year:
        return mask
    lo = 0 if start.year < year else _hour_of_year(start.month, start.day, start.hour)
    hi = hours if stop.year > year else _hour_of_year(stop.month, stop.day, stop.hour)
    lo = max(0, min(lo, hours))
    hi = max(0, min(hi, hours))
    if hi > lo:
        mask[lo:hi] = True
    return mask


@lru_cache(maxsize=4)
def _qualifying_plant_codes(bins_path: str) -> frozenset[int]:
    """Return EIA plant codes that have at least one coal/CC operational bin.

    Read from the CAMPD bin-assignment CSV (one row per plant). A plant
    qualifies if any of its bins is in :data:`QUALIFYING_PLANT_GROUPS`.

    When ``MARKET_SIM_USE_CLEAN`` is set and ``bins_path`` is the default
    ERCOT bin-assignment CSV (:data:`BINS_CSV_DEFAULT`), reads the curated
    ``reference/bin-assignments`` clean table instead (the same source CSV,
    curated by ``scripts/curate_reference.py``); any other ``bins_path``
    (e.g. a test fixture) always reads raw.
    """
    if _use_clean() and bins_path == BINS_CSV_DEFAULT:
        clean_io = _clean_io()
        if clean_io.clean_exists("reference", market="bin-assignments"):
            detail = clean_io.read_clean(
                "reference",
                market="bin-assignments",
                columns=["plant_id", "plant_group"],
            )
            coal_cc = detail[detail["plant_group"].isin(QUALIFYING_PLANT_GROUPS)]
            codes = {int(c) for c in coal_cc["plant_id"].unique()}
            return frozenset(codes - ST_GAS_PEAKER_PLANTS)
    detail = pd.read_csv(bins_path)
    coal_cc = detail[detail["Plant_Group"].isin(QUALIFYING_PLANT_GROUPS)]
    codes = {int(c) for c in coal_cc["Plant_Code"].unique()}
    return frozenset(codes - ST_GAS_PEAKER_PLANTS)


@lru_cache(maxsize=4)
def _build_outage_masks(
    outages_path: str, bins_path: str, hours: int
) -> dict[int, dict[int, np.ndarray]]:
    """Build ``{plant_code: {year: bool mask}}`` for qualifying outages.

    Filters the outage extract to coal/CC plants (per ``bins_path``) whose
    start->stop span exceeds :data:`MIN_OUTAGE_SPAN_HOURS`, then ORs each
    window's per-year clipped mask into the result. Cached on the input
    paths and horizon; the returned arrays are shared (read-only callers).

    An empty ``bins_path`` skips the coal/CC intersection entirely — used for
    the per-ISO ``campd-outages-{ISO}.csv`` extracts, which are already
    coal/CC/gas-steam only by construction (the derivation's GROUPS filter).
    """
    df = pd.read_csv(outages_path, parse_dates=["outage_start", "outage_stop"])
    if bins_path:
        df = df[df["oris_code"].isin(_qualifying_plant_codes(bins_path))]

    masks: dict[int, dict[int, np.ndarray]] = {}
    for row in df.itertuples(index=False):
        start = pd.Timestamp(row.outage_start)
        stop = pd.Timestamp(row.outage_stop)
        span_hours = (stop - start).total_seconds() / 3600.0
        if span_hours < MIN_OUTAGE_SPAN_HOURS:
            continue
        code = int(row.oris_code)
        for year in range(start.year, stop.year + 1):
            window = outage_hour_mask(start, stop, year, hours)
            if not window.any():
                continue
            by_year = masks.setdefault(code, {})
            if year in by_year:
                by_year[year] |= window
            else:
                by_year[year] = window
    return masks


@lru_cache(maxsize=4)
def _clean_outage_masks_for_year(
    year: int, hours: int, bins_path: str
) -> dict[int, np.ndarray]:
    """Build ``{plant_code: bool mask}`` from the clean tree's facility rows.

    The clean-backed equivalent of :func:`_build_outage_masks` for the
    facility-summed layer: every ``unit_id == "ALL"`` row marks the whole plant
    offline for its interval. Rows are mapped from their ERCOT-local wall-clock
    stamp (``interval_start_local``) onto the model's fixed 8760-hour clock with
    the same :func:`_hour_of_year` mapping the raw path uses, and restricted to
    the qualifying coal/CC (non-peaker) plants via ``bins_path`` so the result
    matches the raw derive within tolerance.

    The clean datatype is partitioned by **UTC** year, while the model clock is
    keyed to the ERCOT-local calendar year. A window's local hours straddle the
    UTC-year boundary by the fixed 6-hour offset, so we read ``year`` and
    ``year + 1`` and keep the rows whose local stamp falls in ``year`` — exactly
    the local calendar year the raw path clips each window to. No explicit span
    filter is needed: the facility ``"ALL"`` rows come from ``campd-outages.csv``
    (>10-day windows), so every contiguous run already exceeds
    :data:`MIN_OUTAGE_SPAN_HOURS`. Cached read-only like the raw builder.
    """
    clean_io = _clean_io()
    cols = ["interval_start_local", "plant_id", "unit_id"]
    frames = [
        read_clean_outages(y, columns=cols, validate=False)
        for y in (year, year + 1)
        if clean_io.clean_exists("outages", year=y)
    ]
    if not frames:
        return {}
    df = pd.concat(frames, ignore_index=True) if len(frames) > 1 else frames[0]

    fac = df[df["unit_id"] == "ALL"]
    local = pd.to_datetime(fac["interval_start_local"])
    in_year = local.dt.year == year
    fac, local = fac[in_year], local[in_year]
    if bins_path:
        codes = _qualifying_plant_codes(bins_path)
        keep = fac["plant_id"].astype("int64").isin(codes)
        fac, local = fac[keep], local[keep]

    masks: dict[int, np.ndarray] = {}
    plant_codes = fac["plant_id"].astype("int64")
    for code, idx in plant_codes.groupby(plant_codes).groups.items():
        mask = np.zeros(hours, dtype=bool)
        for ts in local.loc[idx]:
            h = _hour_of_year(ts.month, ts.day, ts.hour)
            if 0 <= h < hours:
                mask[h] = True
        if mask.any():
            masks[int(code)] = mask
    return masks


def outage_masks_for_year(
    year: int,
    hours: int = HOURS_PER_YEAR,
    outages_path: str | Path = OUTAGES_CSV,
    bins_path: str | Path | None = BINS_CSV_DEFAULT,
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: bool mask}`` of qualifying outage hours in ``year``.

    Only coal/CC plants with a sustained (> :data:`MIN_OUTAGE_SPAN_HOURS`)
    outage overlapping ``year`` appear; the masks are on the model's fixed
    8760-hour ERCOT-local clock. Returns an empty dict when the outage
    extract is missing, so a backcast degrades gracefully to the statistical
    availability model.

    ``bins_path`` is the coal/CC bin CSV used to restrict the extract (ERCOT).
    Pass ``None``/empty for a per-ISO extract that is already coal/CC only.

    When ``MARKET_SIM_USE_CLEAN`` is set (default OFF), the ERCOT overlay sources
    these windows from the curated clean tree via :func:`read_clean_outages`
    instead of re-deriving them from ``outages_path``; it falls back to the raw
    derive when no clean partition exists. The clean tree is ERCOT-only, so the
    clean path is taken only for the default ERCOT extract — other ISOs always
    use the raw per-ISO ``campd-outages-{ISO}.csv``.
    """
    outages_path = Path(outages_path)
    if _use_clean() and outages_path == Path(OUTAGES_CSV):
        clean_io = _clean_io()
        if clean_io.clean_exists("outages", year=int(year)):
            return dict(
                _clean_outage_masks_for_year(
                    int(year), int(hours), str(bins_path) if bins_path else ""
                )
            )
        logger.warning(
            "%s set but no clean outages for %d; falling back to raw derive at %s",
            _USE_CLEAN_ENV,
            year,
            outages_path,
        )
    if not outages_path.exists():
        logger.warning(
            "historic outage extract not found at %s; "
            "falling back to statistical availability",
            outages_path,
        )
        return {}
    all_masks = _build_outage_masks(
        str(outages_path), str(bins_path) if bins_path else "", hours
    )
    return {
        code: by_year[year] for code, by_year in all_masks.items() if year in by_year
    }


# Unit-level outage derate. Each unit outage of at least this many days
# derates its model bin's availability by the unit's share of that bin's
# capacity over the window.
#
# Default source is the CAMPD-derived unit-outage extract
# (scripts/derive_campd_unit_outages.py): outages detected on each *unit's*
# own CAMPD gross output for the full year, both 2023 and 2024. This replaces
# the hand-maintained data/raw/reference/tx-jan-aug23-unit-outages.csv (kept in the repo
# for reference), which covered only Jan-Aug 2023. The unit-level layer's
# unique job is to catch single-unit outages the facility-summed overlay
# hides: a coal-unit outage at a mixed coal/gas facility (W A Parish 5-8), or
# one unit out at a multi-unit baseload plant. The derivation flags coal
# (baseload) units when their output gaps below ~5% CF, and load-following
# CC/gas-steam units only when they go genuinely dead (event-based), so an
# economically idle CC turbine is not mistaken for an outage. Rows carry full
# (year, start, end) windows; outage_hour_mask clips each to the run year.
UNIT_OUTAGE_CSV: Path = RAW_DATA_DIR / "campd-unit-outages.csv"
UNIT_OUTAGE_MIN_DAYS: int = 5
# W A Parish (3470) coal units; the rest of its units are gas steam, modeled
# under the split code 34702. Combustion turbines (CT_PEAKER / CT_CHP) are
# excluded from the derate entirely, per the unit-availability convention.
_WAP_COAL_UNITS: frozenset[str] = frozenset({"WAP5", "WAP6", "WAP7", "WAP8"})


def _unit_outage_target(
    facility_id: int, unit_id: object, group: object
) -> tuple[int, str] | None:
    """Map a unit-outage row to a model ``(plant_code, plant_group)`` bin.

    Returns ``None`` to skip the row: combustion turbines are excluded, and
    the split plants (W A Parish, Barney M Davis) route each unit to the right
    asset-class bin (coal vs the gas-steam split code 34702 / 49392). A blank
    or ``OTHER`` group is treated as gas steam.
    """
    g = (
        ""
        if group is None or (isinstance(group, float) and np.isnan(group))
        else str(group)
    )
    if g in ("CT_PEAKER", "CT_CHP"):
        return None
    if facility_id == 3470:  # W A Parish: coal units vs gas-steam (code 34702)
        return (3470, "COAL") if str(unit_id) in _WAP_COAL_UNITS else (34702, "ST_GAS")
    if facility_id == 4939:  # Barney M Davis: steam unit 1 (49392) vs CC
        return (49392, "ST_GAS") if str(unit_id) == "1" else (4939, "CC_REGULAR")
    if g in ("CC_REGULAR", "CC_CHP", "COAL"):
        return (facility_id, g)
    return (facility_id, "ST_GAS")


# Mixed CC/ST facilities whose CAMPD unit-outage rows are tagged with a different
# asset class than the model's bin. Ravenswood (2500) is combined-cycle dominant,
# so CAMPD tags every unit CC_REGULAR, but our NYISO fleet carries plant 2500 as a
# single ST_GAS bin (with an HR correction, fleet.MIXED_FACILITY_STEAM_HR). Without
# this override its outage rows route to a (2500, CC_REGULAR) bin that does not
# exist, so the ST_GAS bin reads near-fully-available and over-runs (and the steam
# reliability floor, frac x pmax x availability, over-forces it). Route the plant's
# outages to its ST_GAS bin so the model availability reflects the real downtime.
_FLEET_GROUP_OVERRIDE: dict[int, str] = {2500: "ST_GAS"}


def _generic_unit_outage_target(
    facility_id: int, unit_id: object, group: object
) -> tuple[int, str] | None:
    """Map a non-ERCOT unit-outage row to its ``(plant_code, plant_group)``.

    Non-ERCOT ISOs run a per-plant fleet with no split facilities, so each
    unit routes straight to its plant's model group. Combustion turbines are
    excluded from the derate (they dispatch economically), matching the
    ERCOT convention. A handful of mixed CC/ST facilities whose CAMPD class tag
    disagrees with the model bin are remapped via :data:`_FLEET_GROUP_OVERRIDE`.
    """
    g = (
        ""
        if group is None or (isinstance(group, float) and np.isnan(group))
        else str(group)
    )
    if g in ("CT_PEAKER", "CT_CHP"):
        return None
    if facility_id in _FLEET_GROUP_OVERRIDE:
        return (facility_id, _FLEET_GROUP_OVERRIDE[facility_id])
    if not g or g == "OTHER":
        return None
    return (facility_id, g)


def unit_outage_csv_for_iso(iso: str | None) -> Path:
    """Return the CAMPD unit-outage CSV path for an ISO.

    ERCOT uses the canonical ``campd-unit-outages.csv``; every other ISO uses
    ``campd-unit-outages-<ISO>.csv``, both written by
    ``scripts/derive_campd_unit_outages.py --iso <ISO>``.
    """
    if iso is None or iso.upper() == "ERCOT":
        return UNIT_OUTAGE_CSV
    return UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-{iso.upper()}.csv")


def unit_outage_short_csv_for_iso(iso: str | None) -> Path:
    """Return the SHORT (< 5-day) unit-outage CSV path for an ISO.

    Written by ``scripts/derive_campd_unit_outages.py --short-windows``:
    baseload-coal full stops of 1-5 days that the standard >= 5-day floor
    excludes, kept only when they survive the derive script's identification
    guards (coal-only detector, unit annual CF >= 0.55, revealed-availability
    in-merit filter). Consumed by :func:`unit_outage_short_derate_factors`
    under ``ScenarioConfig.unit_outage_short_windows``.
    """
    if iso is None or iso.upper() == "ERCOT":
        return UNIT_OUTAGE_CSV.with_name("campd-unit-outages-short.csv")
    return UNIT_OUTAGE_CSV.with_name(f"campd-unit-outages-short-{iso.upper()}.csv")


# Columns unit_outage_derate_factors reads (event-grain; the same columns the
# raw CAMPD unit-outage CSV and the clean unit-outage-events table both carry).
_UNIT_OUTAGE_EVENT_COLUMNS: tuple[str, ...] = (
    "facility_id",
    "unit_id",
    "plant_group",
    "outage_start",
    "outage_end",
    "duration_days",
    "unit_capacity_mw",
)


def _load_unit_outage_events(csv_path: Path, iso: str) -> pd.DataFrame | None:
    """Return the ISO's unit-outage events, or ``None`` when no source exists.

    Reads the curated ``unit-outage-events`` clean table (written by
    ``scripts/curate_unit_outage_events.py``) when :func:`_use_clean` is set and
    the ISO's partition exists; otherwise reads ``csv_path`` (the raw CAMPD
    unit-outage CSV) directly, returning ``None`` when neither is available.
    """
    if _use_clean():
        clean_io = _clean_io()
        if clean_io.clean_exists("unit-outage-events", iso=iso):
            df = clean_io.read_clean(
                "unit-outage-events",
                iso=iso,
                columns=["plant_id", *_UNIT_OUTAGE_EVENT_COLUMNS[1:]],
            )
            return df.rename(columns={"plant_id": "facility_id"})
    if not csv_path.exists():
        return None
    return pd.read_csv(csv_path)


@lru_cache(maxsize=None)
def _iso_plant_capacity(iso: str) -> dict[tuple[int, str], float]:
    """Return ``{(plant_code, plant_group): nameplate_mw}`` for a non-ERCOT ISO.

    Non-ERCOT ISOs run a per-plant EIA-860 fleet (no CAMPD bin sheet), so the
    derate denominator — the plant's capacity in its model group — comes from
    the fleet's nameplate summed per ``(plant_code, plant_group)``.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import (
        load_fleet_from_csv,
        load_retired_within_window,
    )

    iso_config = get_iso_config(iso)
    # Within-window plant exits dispatch in the backcast fleet, so their
    # capacity must be in the derate denominator — else their unit-outage rows
    # route to a (plant_code, plant_group) absent from this map and are skipped,
    # leaving the injected retiree (e.g. Mystic) un-capped.
    fleet = load_fleet_from_csv(iso, iso_config) + load_retired_within_window(
        iso, iso_config
    )
    cap: dict[tuple[int, str], float] = {}
    for g in fleet:
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        cap[(code, g.plant_group)] = cap.get((code, g.plant_group), 0.0) + float(
            g.pmax_mw
        )
    return cap


@lru_cache(maxsize=None)
def unit_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
) -> dict[tuple[int, str], np.ndarray]:
    """Return ``{(plant_code, plant_group): (hours,) availability multiplier}``.

    Built from the ISO's unit-level outage extract (ERCOT's
    :data:`UNIT_OUTAGE_CSV` ``campd-unit-outages.csv``, or
    ``campd-unit-outages-<ISO>.csv`` for other ISOs — see
    :func:`unit_outage_csv_for_iso`): every unit outage of at least
    :data:`UNIT_OUTAGE_MIN_DAYS` days whose window overlaps ``year`` derates
    its plant's availability by ``unit_capacity_mw / plant_capacity_mw`` over
    the outage window (concurrent units sum, clipped at full derate). Each
    row's ``(outage_start, outage_end)`` is clipped to ``year`` on the model
    clock, so a single multi-year file feeds every backcast year. Combustion
    turbines are excluded and rows without a matching plant or capacity are
    skipped. Years the file does not cover get an empty dict.

    The plant-capacity denominator and the unit->plant routing differ by ISO:
    ERCOT reads capacities from its CAMPD bin sheet and routes its split
    facilities (W A Parish, Barney M Davis) to the right asset class; other
    ISOs read per-plant nameplate from the EIA-860 fleet
    (:func:`_iso_plant_capacity`) and route each unit straight to its
    ``(plant_code, plant_group)`` (no split plants, CTs still excluded).
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_outage_csv_for_iso(iso)
    df = _load_unit_outage_events(csv_path, iso)
    if df is None:
        return {}
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    return _unit_outage_factors_from_events(df, year, hours, bins_path, iso)


def _unit_outage_factors_from_events(
    df: pd.DataFrame,
    year: int,
    hours: int,
    bins_path: str | Path,
    iso: str,
) -> dict[tuple[int, str], np.ndarray]:
    """Accumulate unit-outage event rows into per-bin availability factors.

    Shared core of :func:`unit_outage_derate_factors` (>= 5-day full stops),
    :func:`unit_outage_short_derate_factors` (< 5-day baseload-coal full stops)
    and :func:`unit_partial_outage_derate_factors` (unit-grain partial-derate
    plateaus): each row derates its plant's ``(plant_code, plant_group)`` bin by
    its removed-capacity share ``removed_mw / plant_capacity_mw`` over the window
    clipped to ``year`` on the model clock; concurrent units sum, clipped at
    full derate.

    A full-stop row removes the unit's whole ``unit_capacity_mw``. A partial
    row carries a ``derate_factor`` column (the measured availability fraction
    the unit ran at during the plateau) and removes only
    ``(1 - derate_factor) x unit_capacity_mw`` — so a plant with two units each
    at half capability derates to half, exactly like two full stops of half the
    plant. The two paths share this accumulator so the partial derate uses the
    identical unit-capacity-share / concurrent-sum / clip-at-full aggregation
    as the >= 5-day overlay.
    """
    if iso == "ERCOT":
        from market_sim.data.fleet import load_campd_bins

        bins = load_campd_bins(str(bins_path))
        cap = {
            (int(c), str(g)): float(m)
            for c, g, m in zip(
                bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
            )
            if m and m > 0
        }
        target_fn = _unit_outage_target
    else:
        cap = _iso_plant_capacity(iso)
        target_fn = _generic_unit_outage_target
    has_derate = "derate_factor" in df.columns
    sums: dict[tuple[int, str], np.ndarray] = {}
    for r in df.itertuples(index=False):
        tgt = target_fn(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt not in cap:
            continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        # Fraction of the unit's capacity removed over the window: a full stop
        # removes all of it; a partial plateau removes (1 - derate_factor).
        removed_frac = 1.0
        if has_derate:
            dfac = r.derate_factor
            if pd.isna(dfac):
                continue
            removed_frac = min(max(1.0 - float(dfac), 0.0), 1.0)
            if removed_frac <= 0.0:
                continue
        mask = outage_hour_mask(
            r.outage_start,
            pd.Timestamp(r.outage_end) + pd.Timedelta(days=1),
            year,
            hours,
        )
        if not mask.any():
            continue
        arr = sums.setdefault(tgt, np.zeros(hours))
        arr[mask] += removed_frac * float(ucap) / cap[tgt]
    return {k: np.clip(1.0 - v, 0.0, 1.0) for k, v in sums.items()}


@lru_cache(maxsize=None)
def unit_outage_short_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
) -> dict[tuple[int, str], np.ndarray]:
    """Return short-window (< 5-day) unit-outage availability multipliers.

    The sub-floor companion of :func:`unit_outage_derate_factors`, gated by
    ``ScenarioConfig.unit_outage_short_windows``: baseload-coal full stops of
    1-5 days from ``campd-unit-outages-short-<ISO>.csv`` (built by
    ``scripts/derive_campd_unit_outages.py --short-windows``, which enforces
    the identification guards — coal-only detector, unit annual CF >= 0.55,
    revealed-availability in-merit filter — so economic idling never enters).
    Defensively re-filters to ``plant_group == "COAL"`` and
    ``duration_days < UNIT_OUTAGE_MIN_DAYS`` so the two overlays stay disjoint
    (a window >= the floor belongs to the standard overlay and is dropped
    here). ISOs without the file get an empty dict (no effect).
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_outage_short_csv_for_iso(iso)
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    df = df[
        (df["duration_days"] < UNIT_OUTAGE_MIN_DAYS) & (df["plant_group"] == "COAL")
    ]
    return _unit_outage_factors_from_events(df, year, hours, bins_path, iso)


def unit_partial_outage_csv_for_iso(iso: str | None) -> Path:
    """Return the UNIT-GRAIN partial-derate plateau CSV path for an ISO.

    Distinct from the ERCOT PLANT-grain :data:`PARTIAL_OUTAGE_CSV`
    (``campd-partial-outages.csv``): this is the unit-grain partial-plateau
    extract (``campd-partial-outages-<ISO>.csv``, written by
    ``scripts/derive_campd_unit_outages.py --partial-windows``), consumed by
    :func:`unit_partial_outage_derate_factors` under
    ``ScenarioConfig.unit_partial_outage_windows``. Always ISO-suffixed —
    ERCOT keeps the plant-grain path and has no unit-grain partial file, so
    ``ERCOT`` resolves to a name that does not collide with the plant-grain
    file and simply does not exist (empty derate).
    """
    return UNIT_OUTAGE_CSV.with_name(
        f"campd-partial-outages-{(iso or 'ERCOT').upper()}.csv"
    )


@lru_cache(maxsize=None)
def unit_partial_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
    iso: str = "ERCOT",
) -> dict[tuple[int, str], np.ndarray]:
    """Return unit-grain partial-derate plateau availability multipliers.

    The partial-derate companion of :func:`unit_outage_short_derate_factors`,
    gated by ``ScenarioConfig.unit_partial_outage_windows``: sustained
    CF-ceiling plateaus (a unit running at a depressed ceiling — half its
    capability out — which never reaches zero, so no full-stop window can
    represent it) from ``campd-partial-outages-<ISO>.csv`` (built by
    ``scripts/derive_campd_unit_outages.py --partial-windows``, which enforces
    the same identification guards as the short windows — coal-only detector,
    the when-operable baseload CF >= 0.55 screen, the revealed-availability
    in-merit filter — plus the plant-level partial detector's frozen plateau
    constants). Each row carries a ``derate_factor`` (the measured availability
    fraction during the plateau); the shared accumulator removes
    ``(1 - derate_factor) x unit_capacity`` from the plant bin, aggregated by
    unit-capacity share with concurrent units summed and clipped at full derate
    — identical to the >= 5-day overlay. Returns ``{(plant_code, plant_group):
    (hours,) multiplier}``. ISOs without the file get an empty dict (no effect).

    Keyed and applied per ``(plant_code, plant_group)`` like the unit-outage
    derate, NOT per ``plant_code`` like the ERCOT-only plant-grain
    :func:`partial_outage_derate_factors` — the plant-grain path over-fires on
    a cycling fleet and stays ERCOT-scoped in ``fleet.py``.
    """
    iso = (iso or "ERCOT").upper()
    csv_path = unit_partial_outage_csv_for_iso(iso)
    if not csv_path.exists():
        return {}
    df = pd.read_csv(csv_path)
    return _unit_outage_factors_from_events(df, year, hours, bins_path, iso)


# Partial (unit-level) outage derates approximated from CAMPD CF-ceiling
# plateaus (scripts/derive_partial_outages.py). A multiplicative availability
# factor per plant: 1.0 outside detected windows, derate_factor within.
PARTIAL_OUTAGE_CSV: Path = RAW_DATA_DIR / "campd-partial-outages.csv"


@lru_cache(maxsize=None)
def partial_outage_derate_factors(
    year: int, hours: int = HOURS_PER_YEAR, iso: str = "ERCOT"
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) availability multiplier}`` from the
    CAMPD-derived partial-outage windows. 1.0 outside detected ceiling plateaus,
    the window's derate factor within (deepest wins where they overlap).

    When ``MARKET_SIM_USE_CLEAN`` is set and the ISO's curated
    ``partial-outages`` clean partition exists (written by
    ``scripts/curate_partial_outages.py``), reads from there; otherwise reads
    :data:`PARTIAL_OUTAGE_CSV` (ERCOT-only) directly.
    """
    iso = (iso or "ERCOT").upper()
    df = None
    if _use_clean():
        clean_io = _clean_io()
        if clean_io.clean_exists("partial-outages", iso=iso):
            df = clean_io.read_clean(
                "partial-outages",
                iso=iso,
                columns=[
                    "plant_id",
                    "year",
                    "outage_start",
                    "outage_stop",
                    "derate_factor",
                ],
            ).rename(columns={"plant_id": "oris_code"})
    if df is None:
        if not PARTIAL_OUTAGE_CSV.exists():
            return {}
        df = pd.read_csv(PARTIAL_OUTAGE_CSV)
    df = df[df["year"] == year]
    out: dict[int, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mask = outage_hour_mask(r.outage_start, r.outage_stop, year, hours)
        if not mask.any():
            continue
        arr = out.setdefault(int(r.oris_code), np.ones(hours))
        arr[mask] = np.minimum(arr[mask], float(r.derate_factor))
    return out


# ERCOT per-reactor DAILY nuclear availability (60-Day DAM disclosure NUC
# Resource Status, monthly energy reconciled to the EIA-923 anchor) — the
# window-grain replacement for the NUCLEAR_MONTHLY_CF_BY_YEAR fleet-month
# smear, gated by ScenarioConfig.ercot_nuclear_unit_availability. Derived by
# scripts/derive_ercot_nuclear_availability.py (provenance + admissibility in
# its docstring); a refuel window is a physical availability event, the
# nuclear analogue of the CAMPD fossil outage windows above.
ERCOT_NUCLEAR_AVAILABILITY_CSV: Path = RAW_DATA_DIR / "ercot-nuclear-availability.csv"


@lru_cache(maxsize=None)
def ercot_nuclear_unit_availability_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[tuple[int, int], np.ndarray]:
    """Return ``{(plant_code, unit_no): (hours,) availability}`` for ``year``.

    Each covered delivery date contributes a flat 24-hour block of its daily
    ``avail`` fraction on the model's fixed non-leap clock (real-calendar
    month/day mapped through :func:`_hour_of_year`; a leap year's Feb 29 row
    is dropped, matching the archive convention). Hours the disclosure does
    not cover are ``NaN`` — the caller keeps its existing (monthly-smear)
    availability there. Returns an empty dict when the CSV is absent or the
    year has no rows, so callers degrade to the smear unchanged.
    """
    if not ERCOT_NUCLEAR_AVAILABILITY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_NUCLEAR_AVAILABILITY_CSV)
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    if df.empty:
        return {}
    out: dict[tuple[int, int], np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        arr = out.setdefault(
            (int(r.plant_code), int(r.unit_no)), np.full(hours, np.nan)
        )
        arr[lo:hi] = float(r.avail)
    return out


# ERCOT measured CLASS-day thermal availability (60-Day DAM disclosure
# Gen_Resource HSL + Resource Status, config-collapsed to physical CC trains)
# — the measured replacement for the statistical WEFOR/EFOR estimate of the
# same quantity on the covered gas classes, gated by
# ScenarioConfig.ercot_thermal_dam_availability. Derived by
# scripts/derive_ercot_thermal_dam_availability.py (provenance, class scope and
# admissibility in its docstring); the June/Sep-2023 scarcity-formation
# forensics measured the statistical stack 13-22 % derated at the summer
# reserve margin where this disclosure shows the same fleet at its ratings.
ERCOT_THERMAL_DAM_AVAILABILITY_CSV: Path = (
    RAW_DATA_DIR / "ercot-thermal-dam-availability.csv"
)


@lru_cache(maxsize=None)
def ercot_thermal_dam_availability_series(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[str, np.ndarray]:
    """Return ``{plant_group: (hours,) measured class availability}`` for ``year``.

    Each covered delivery date contributes a flat 24-hour block of the class's
    measured day availability fraction (live config-collapsed HSL / site
    ratings) on the model's fixed non-leap clock (:func:`_hour_of_year`; a leap
    year's Feb 29 row dropped, the archive convention). Hours the disclosure
    does not cover — the Oct-2023 publication hole, Nov-Dec 2025 until the 2026
    files land — are ``NaN``: the caller keeps the statistical availability
    there. Returns an empty dict when the CSV is absent or the year has no
    rows, so callers degrade to the statistical model unchanged.
    """
    if not ERCOT_THERMAL_DAM_AVAILABILITY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_THERMAL_DAM_AVAILABILITY_CSV)
    # "class" is a Python keyword — itertuples would positionalize it.
    df = df.rename(columns={"class": "klass"})
    df["date"] = pd.to_datetime(df["date"])
    df = df[df["date"].dt.year == int(year)]
    if df.empty:
        return {}
    out: dict[str, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mo, dy = int(r.date.month), int(r.date.day)
        if mo == 2 and dy == 29:
            continue  # non-leap model clock (ERCOT-54 convention)
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        arr = out.setdefault(str(r.klass), np.full(hours, np.nan))
        arr[lo:hi] = float(r.avail)
    return out


# ERCOT CAMPD-blind per-plant availability (EIA-923 zero-month outage windows;
# scripts/derive_ercot_noncampd_availability.py). Restores measured
# availability for the ERCOT gas plants ABSENT from the TX CAMPD extract
# (Kiamichi 55501, Hidalgo 55545, Arthur Von Rosenberg 7512, EG178 56233 — the
# ERCOT-70 phantom-CC blind spot: the model dispatches them on flat statistical
# availability while EIA-923 shows a real full-plant outage month). The
# CAMPD-derived outage overlay cannot see them (no CEMS rows -> no windows).
# Backcast-only, gated by ScenarioConfig.ercot_noncampd_plant_availability;
# forecast keeps the statistical stack (the mode-aware seam).
ERCOT_NONCAMPD_AVAILABILITY_CSV: Path = RAW_DATA_DIR / "ercot-noncampd-availability.csv"


@lru_cache(maxsize=None)
def ercot_noncampd_availability_caps(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) availability cap}`` for the CAMPD-blind
    ERCOT gas plants, from the EIA-923 zero-month outage windows.

    Each window ``[outage_start, outage_end)`` (a full-plant EIA-923 zero
    month; ``outage_end`` is the exclusive return-to-service instant) zeroes
    the plant's availability over its hours on the model's fixed non-leap clock
    (:func:`outage_hour_mask`); every other hour stays at 1.0, so the cap only
    ever REMOVES the plant in its measured-offline months and leaves the
    statistical availability untouched elsewhere (a zero-month availability
    event, never a monthly-level pin — rule 14). Plant-keyed so the fleet
    builder applies each cap to every dispatch tranche of the (possibly binned)
    plant, exactly like :func:`retiree_availability_caps`. Empty when the CSV is
    absent or the year has no windows, so callers degrade to the statistical
    model unchanged.
    """
    if not ERCOT_NONCAMPD_AVAILABILITY_CSV.exists():
        return {}
    df = pd.read_csv(ERCOT_NONCAMPD_AVAILABILITY_CSV)
    df = df[df["year"] == int(year)]
    if df.empty:
        return {}
    caps: dict[int, np.ndarray] = {}
    for r in df.itertuples(index=False):
        mask = outage_hour_mask(r.outage_start, r.outage_end, int(year), hours)
        if not mask.any():
            continue
        cap = caps.setdefault(int(r.plant_code), np.ones(hours))
        # MIN-combine so the most-conservative measured availability wins where
        # windows overlap (a daily DAM row and an EIA-923 zero-month backstop).
        cap[mask] = np.minimum(cap[mask], float(r.avail))
    return caps


# Within-window retiree measured-availability cap (CAMPD unit-level CEMS).
# A within-window retiree (fleet.load_retired_within_window) is a whole-plant
# exit the COD ramp ages out on its EIA-860 planned retirement date. But a unit
# winding down to retirement runs at LOW capacity factor — or stops generating
# months before its official date — for retirement-logistics / out-of-market
# (RMR-type) reasons a cost-based merit order cannot see: the LP keeps it
# dispatched at its coal must-run floor as baseload while reality barely ran it.
# Homer City (plant 3122) is the type case: model ~4.1 TWh vs CEMS 1.2 TWh in
# 2023 (its three coal units stopping generation Mar/May 2023 though officially
# retiring 2023-07 / 2023-08 / 2024-04, the middle unit never running at all),
# and ~2.8 TWh modeled in 2024 against zero actual. The per-plant binning
# (fleet.fleet_to_bins) merges the units before the COD ramp, so per-unit
# planned-date aging cannot resolve it; the measured envelope can.
#
# This caps each retiree plant's availability to its MEASURED monthly CEMS
# envelope — the peak hourly plant-total gross load the plant actually
# demonstrated that month, as a fraction of its nameplate, and zero in months it
# did not run. It is an AVAILABILITY measurement (the LP still chooses dispatch,
# and the must-run floor, clamped to availability, scales with it), not an
# energy target, and is plant-keyed so it reaches every dispatch tranche of the
# binned plant. Scoped to the within-window retiree plants — capping the bulk
# operable fleet to CEMS would be circular (it would reproduce EIA-930).
# Backcast-only, mirroring the measured CAMPD outage overlay; the forecast path
# ages retirees out on planned dates instead.
CAMPD_UNIT_LEVEL_DIR: Path = RAW_DATA_DIR / "campd-unit-level"

# Hour-of-year (0-based) -> calendar month (1-12) on the fixed non-leap 8760
# clock, so a per-month envelope broadcasts to hours without per-call calendar
# work.
_MONTH_OF_HOUR: np.ndarray = np.empty(HOURS_PER_YEAR, dtype=np.int64)
for _mm in range(1, 13):
    _lo_h = _DAYS_BEFORE_MONTH[_mm] * 24
    _hi_h = (_DAYS_BEFORE_MONTH[_mm] + calendar.monthrange(2023, _mm)[1]) * 24
    _MONTH_OF_HOUR[_lo_h:_hi_h] = _mm


def _plant_cems_envelope(
    state: str, year: int, plant_code: int, nameplate_mw: float, hours: int
) -> np.ndarray | None:
    """Monthly CEMS availability envelope for one retiree plant, or ``None``.

    Reads ``campd-unit-level/{STATE}_{YEAR}.parquet``, sums the plant's units to
    an hourly plant-total gross load, and returns a length-``hours`` cap in
    [0, 1] = each month's peak plant-total hour / ``nameplate_mw`` (clipped to
    1), zero in months with no generation. ``None`` when the state extract or
    the plant is absent (no measurement -> the COD ramp's planned-date aging
    stands). Gross load over net nameplate clips to 1 in full-output months, so
    the cap only bites where the plant's demonstrated peak has fallen — i.e.
    where it is winding down.

    A within-window retiree absent from an extract that *exists* did not run that
    year at all (it had retired / was decommissioned), so it is capped to zero
    rather than skipped — the binned plant's planned retirement (e.g. Homer City
    held online through 2024-04 by the collapsed plant date) is then overridden
    by the measured "did not run" fact. Only a missing state extract returns
    ``None`` (a genuine data gap).
    """
    if nameplate_mw <= 0.0:
        return None
    path = CAMPD_UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path, columns=["facilityId", "date", "hour", "grossLoad"])
    sub = df[df["facilityId"].astype(str) == str(int(plant_code))]
    if sub.empty:
        return np.zeros(hours)
    sub = sub.copy()
    sub["grossLoad"] = pd.to_numeric(sub["grossLoad"], errors="coerce").fillna(0.0)
    # Plant-total per hour (units summed), then the peak hour within each month.
    plant_hourly = sub.groupby(["date", "hour"], as_index=False)["grossLoad"].sum()
    plant_hourly["month"] = pd.to_datetime(plant_hourly["date"]).dt.month
    monthly_peak = plant_hourly.groupby("month")["grossLoad"].max()
    frac = np.zeros(13)  # 1-indexed; index 0 unused
    for m in range(1, 13):
        peak = monthly_peak.get(m, 0.0)
        if pd.isna(peak):
            peak = 0.0
        frac[m] = min(1.0, max(0.0, float(peak) / nameplate_mw))
    idx = np.arange(hours) % HOURS_PER_YEAR
    return frac[_MONTH_OF_HOUR[idx]]


@lru_cache(maxsize=None)
def retiree_availability_caps(
    iso: str, year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) availability cap}`` for within-window
    retiree plants, from the CAMPD unit-level CEMS envelope.

    Plant-keyed so the fleet builder applies each cap to every dispatch tranche
    of the (possibly binned) plant. The denominator is the plant's nameplate
    summed over its retiree units. Plants with no CEMS extract, or whose
    envelope never falls below full capacity, are omitted. Empty for an ISO with
    no within-window retiree parquet.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_retired_within_window

    try:
        iso_config = get_iso_config(iso)
    except ValueError:
        iso_config = None
    plants: dict[int, list] = {}
    for g in load_retired_within_window(iso, iso_config):
        pc = int(g.plant_code)
        if pc <= 0 or not g.state:
            continue
        rec = plants.setdefault(pc, [g.state, 0.0])
        rec[1] += float(g.pmax_mw)
    caps: dict[int, np.ndarray] = {}
    for pc, (state, nameplate) in plants.items():
        cap = _plant_cems_envelope(state, year, pc, nameplate, hours)
        if cap is not None and (cap < 1.0).any():
            caps[pc] = cap
    return caps


# CT_PEAKER AS/RUC-deployment energy floor (scripts/derive_ct_deployment.py).
# A per-plant *hourly* minimum-generation floor on the model's 8760-hour clock:
# in the out-of-merit hours where CEMS shows a simple-cycle peaker generating
# below its marginal energy cost (the IMM-documented ancillary-service /
# reliability-unit-commitment deployment + reserve-adequacy wedge), the floor is
# the plant's *measured* net output; zero everywhere else. Applied as a min-gen
# bound by fleet.generators_to_fleet_arrays when ScenarioConfig
# .ct_deployment_overlay is set (backcast only, any ISO — the artifact is keyed
# per ISO via ct_deployment_csv) so the LP reproduces the out-of-merit CT energy
# an energy-only merit order omits,
# WITHOUT flooring CT to its full CEMS output (the in-merit hours stay
# economic). Unlike the CT reliability must-run floor (which covers all hours
# and so exempts its units from WEFOR/POF), this floor is sparse and well below
# pmax in its hours, so the units keep the statistical availability model and
# the floor is simply availability-capped where they ever coincide.
_CT_DEPLOYMENT_DIR: Path = CALIBRATION_DIR


def ct_deployment_csv(iso: str = "ERCOT") -> Path:
    """Return the per-ISO CT deployment-floor artifact path.

    ``scripts/derive_ct_deployment.py`` writes one parquet per ISO
    (``ct_deployment_floor_<ISO>.parquet``); the overlay reads the file for
    the ISO it is dispatching so every ISO's out-of-merit wedge is sourced
    from its own CEMS + LMP measurement.
    """
    return _CT_DEPLOYMENT_DIR / f"ct_deployment_floor_{iso.upper()}.parquet"


# Backward-compatible alias: the default ERCOT artifact path.
CT_DEPLOYMENT_CSV: Path = ct_deployment_csv("ERCOT")


@lru_cache(maxsize=None)
def ct_deployment_floor_for_year(
    year: int, hours: int = HOURS_PER_YEAR, iso: str = "ERCOT"
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) deployment floor MW}`` for ``year``.

    Reads the per-plant out-of-merit deployment-hour floors written by
    ``scripts/derive_ct_deployment.py`` (long: ``year, plant_code, hour,
    floor_mw``) for ``iso`` and rebuilds each plant's dense 8760-hour floor
    (zero outside its deployment hours). Returns an empty dict when the
    artifact is missing (the overlay then degrades to the unmodified
    energy-only dispatch) or when the year is absent. The arrays are shared
    read-only via the cache.
    """
    path = ct_deployment_csv(iso)
    if not path.exists():
        logger.warning(
            "CT deployment-floor artifact not found at %s; "
            "the CT deployment overlay is a no-op for %s %d",
            path,
            iso.upper(),
            year,
        )
        return {}
    df = pd.read_parquet(path)
    df = df[df["year"] == year]
    out: dict[int, np.ndarray] = {}
    for code, sub in df.groupby("plant_code", observed=True):
        arr = np.zeros(hours, dtype=float)
        hoy = sub["hour"].to_numpy()
        valid = (hoy >= 0) & (hoy < hours)
        arr[hoy[valid]] = sub["floor_mw"].to_numpy(dtype=float)[valid]
        out[int(code)] = arr
    return out


# Spatial reliability-deployment energy floor (scripts/derive_reliability_
# deployment.py). The generalization of the CT deployment overlay to the
# load-pocket thermal fleet (CC_REGULAR, COAL, ST_GAS, CC_CHP) in the
# under-running zones (South_Central, West, Northeast). Same per-plant *hourly*
# floor artifact and dense format as the CT overlay, but scoped on the load-zone
# congestion subset: the measured CEMS net in hours where the plant was economic
# at its LOCAL load-zone price yet out of merit at the system hub — the
# intra-zonal congestion energy a single-system-price LP cannot dispatch.
# Applied as a sparse min-gen bound by fleet.generators_to_fleet_arrays when
# ScenarioConfig.reliability_deployment_overlay is set (ERCOT backcast only).
def reliability_deployment_csv(iso: str = "ERCOT") -> Path:
    """Return the per-ISO reliability-deployment-floor artifact path."""
    return _CT_DEPLOYMENT_DIR / f"reliability_deployment_floor_{iso.upper()}.parquet"


@lru_cache(maxsize=None)
def reliability_deployment_floor_for_year(
    year: int, hours: int = HOURS_PER_YEAR, iso: str = "ERCOT"
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) deployment floor MW}`` for ``year``.

    Reads the per-plant out-of-merit-at-hub-but-economic-locally floors written
    by ``scripts/derive_reliability_deployment.py`` (long: ``year, plant_code,
    hour, floor_mw``) for ``iso`` and rebuilds each plant's dense 8760-hour
    floor (zero outside its deployment hours). Returns an empty dict when the
    artifact is missing (the overlay then degrades to the unmodified
    energy-only dispatch) or when the year is absent. Mirrors
    :func:`ct_deployment_floor_for_year`; the arrays are shared read-only via
    the cache.
    """
    path = reliability_deployment_csv(iso)
    if not path.exists():
        logger.warning(
            "reliability deployment-floor artifact not found at %s; "
            "the reliability deployment overlay is a no-op for %s %d",
            path,
            iso.upper(),
            year,
        )
        return {}
    df = pd.read_parquet(path)
    df = df[df["year"] == year]
    out: dict[int, np.ndarray] = {}
    for code, sub in df.groupby("plant_code", observed=True):
        arr = np.zeros(hours, dtype=float)
        hoy = sub["hour"].to_numpy()
        valid = (hoy >= 0) & (hoy < hours)
        arr[hoy[valid]] = sub["floor_mw"].to_numpy(dtype=float)[valid]
        out[int(code)] = arr
    return out


# ---------------------------------------------------------------------------
# NYSDEC 6 NYCRR Subpart 227-3 "peaker rule" availability overlay (NYISO)
# ---------------------------------------------------------------------------
# The regulation caps ozone-season (May 1 - Sep 30) NOx from simple-cycle
# turbines in two phases (2023-05-01 / 2025-05-01). Units whose compliance
# plan is ozone-season shutdown or reliability-only operation are unavailable
# to the energy market inside the window — an exogenous regulatory
# availability event in the same rule-#12 admissibility class as the CAMPD
# unit-outage windows (availability only, never an offer/price change; the
# schedule regenerates from the regulation, not from observed CF). Curated
# unit schedule: data/raw/reference/nysdec-227-3-peaker-compliance.csv
# (NYISO Gold Book Tables IV-3..IV-6, 2023/2024/2025 vintages; per-unit
# citations in the CSV rows).
NYSDEC_PEAKER_CSV: Path = (
    RAW_DATA_DIR / "reference" / "nysdec-227-3-peaker-compliance.csv"
)

# Ozone-season bounds on the model's fixed non-leap 8760 clock: May 1 00:00 is
# hour 2880, Sep 30 24:00 is hour 6552 (same span as the ST_GAS seasonal
# amortization window in model/commitment.py).
OZONE_SEASON_HOURS: tuple[int, int] = (2880, 6552)

# Restriction kinds the overlay APPLIES. Designated / record-only kinds
# (ozone_season_oos_star_designated, statutory_phaseout_2030, retired,
# none_documented) are carried in the CSV for the audit record but never
# restrict availability: the STAR designation kept the Gowanus/Narrows barges
# in operation, retirements are the fleet vintage's job, and the NYPA statute
# binds after 2030.
_NYSDEC_APPLIED_KINDS: frozenset[str] = frozenset({"ozone_season_oos"})


@lru_cache(maxsize=8)
def _nysdec_peaker_rows(csv_path: str) -> tuple:
    """Parse the curated 227-3 schedule into applicable restriction rows."""
    path = Path(csv_path)
    if not path.exists():
        return ()
    df = pd.read_csv(path)
    rows = []
    for r in df.itertuples(index=False):
        if str(r.restriction).strip() not in _NYSDEC_APPLIED_KINDS:
            continue
        eff = pd.to_datetime(r.effective_date)
        end = pd.to_datetime(r.end_date) if pd.notna(r.end_date) else None
        unit_ids = (
            tuple(u.strip() for u in str(r.unit_ids).split(";") if u.strip())
            if pd.notna(r.unit_ids)
            else ()
        )
        mw = float(r.restricted_mw) if pd.notna(r.restricted_mw) else None
        rows.append(
            (
                int(r.plant_code),
                str(r.scope).strip(),
                unit_ids,
                eff,
                end,
                mw,
            )
        )
    return tuple(rows)


def nysdec_peaker_restrictions(
    year: int, hours: int, csv_path: Path | None = None
) -> list[dict]:
    """Return the 227-3 restrictions active in ``year`` as hour windows.

    Each item: ``{"plant_code", "scope", "unit_ids", "restricted_mw",
    "h_lo", "h_hi"}`` — the ozone-window slice of the model year during which
    the row's units are out of the energy market. A row whose effective date
    falls inside the year's ozone window starts there (the 227-3 compliance
    dates are May 1, which is the window start); one that ends mid-window
    (e.g. a retirement) stops there.
    """
    o_lo, o_hi = OZONE_SEASON_HOURS
    o_hi = min(o_hi, hours)

    def _doy_nonleap(ts: pd.Timestamp) -> int:
        """Day-of-year on the model's fixed non-leap 8760 clock (Feb 29 -> 28)."""
        day = min(ts.day, 28) if ts.month == 2 else ts.day
        return int(pd.Timestamp(2023, ts.month, day).dayofyear)

    out: list[dict] = []
    for code, scope, unit_ids, eff, end, mw in _nysdec_peaker_rows(
        str(csv_path or NYSDEC_PEAKER_CSV)
    ):
        if eff.year > year:
            continue
        if end is not None and end.year < year:
            continue
        h_lo = o_lo
        if eff.year == year:
            h_lo = max(o_lo, min((_doy_nonleap(eff) - 1) * 24, hours))
        h_hi = o_hi
        if end is not None and end.year == year:
            h_hi = min(o_hi, max((_doy_nonleap(end) - 1) * 24, 0))
        if h_hi <= h_lo:
            continue
        out.append(
            {
                "plant_code": code,
                "scope": scope,
                "unit_ids": unit_ids,
                "restricted_mw": mw,
                "h_lo": h_lo,
                "h_hi": h_hi,
            }
        )
    return out
