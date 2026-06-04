"""Historic generator-outage overlay for ERCOT calibration backcasts.

Reads the committed ERCOT outage extract (``inputs/raw-data/ercot-outages.csv``)
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
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR

logger = logging.getLogger(__name__)

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
OUTAGES_CSV: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "campd-outages.csv"
)

# Default CAMPD bin-assignment CSV, the plant_code -> Plant_Group source used
# to decide which plants are coal/CC. Matches ScenarioConfig.campd_bins_path.
BINS_CSV_DEFAULT: str = "inputs/custom-bin-assignments.csv"

# Per-ISO historic-outage extract. ERCOT keeps the original file name (so the
# ERCOT backcast is unchanged); other ISOs use ``campd-outages-{ISO}.csv``,
# written by ``scripts/derive_campd_outages.py --iso <ISO>`` from that ISO's
# CAMPD CEMS state extracts. Those per-ISO files already contain only coal/CC/
# gas-steam plants (the derivation's GROUPS filter), so the overlay trusts
# them without re-intersecting against an ISO-specific bin CSV.
_OUTAGES_DIR: Path = Path(__file__).parents[3] / "inputs" / "raw-data"


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
ST_GAS_PEAKER_PLANTS: frozenset[int] = frozenset({
    3504,   # Stryker Creek
    3453,   # Mountain Creek
    3490,   # Graham
    3507,   # Trinidad (TX)
    3576,   # Ray Olinger
    4266,   # Spencer
})

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
    lo = (
        0 if start.year < year
        else _hour_of_year(start.month, start.day, start.hour)
    )
    hi = (
        hours if stop.year > year
        else _hour_of_year(stop.month, stop.day, stop.hour)
    )
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
    """
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
    df = pd.read_csv(
        outages_path, parse_dates=["outage_start", "outage_stop"]
    )
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
    """
    outages_path = Path(outages_path)
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
        code: by_year[year]
        for code, by_year in all_masks.items()
        if year in by_year
    }


# Unit-level outage derate. Each unit outage of at least this many days
# derates its model bin's availability by the unit's share of that bin's
# capacity over the window.
#
# Default source is the CAMPD-derived unit-outage extract
# (scripts/derive_campd_unit_outages.py): outages detected on each *unit's*
# own CAMPD gross output for the full year, both 2023 and 2024. This replaces
# the hand-maintained inputs/tx-jan-aug23-unit-outages.csv (kept in the repo
# for reference), which covered only Jan-Aug 2023. The unit-level layer's
# unique job is to catch single-unit outages the facility-summed overlay
# hides: a coal-unit outage at a mixed coal/gas facility (W A Parish 5-8), or
# one unit out at a multi-unit baseload plant. The derivation flags coal
# (baseload) units when their output gaps below ~5% CF, and load-following
# CC/gas-steam units only when they go genuinely dead (event-based), so an
# economically idle CC turbine is not mistaken for an outage. Rows carry full
# (year, start, end) windows; outage_hour_mask clips each to the run year.
UNIT_OUTAGE_CSV: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "campd-unit-outages.csv"
)
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
    g = "" if group is None or (isinstance(group, float) and np.isnan(group)) else str(group)
    if g in ("CT_PEAKER", "CT_CHP"):
        return None
    if facility_id == 3470:  # W A Parish: coal units vs gas-steam (code 34702)
        return (3470, "COAL") if str(unit_id) in _WAP_COAL_UNITS else (34702, "ST_GAS")
    if facility_id == 4939:  # Barney M Davis: steam unit 1 (49392) vs CC
        return (49392, "ST_GAS") if str(unit_id) == "1" else (4939, "CC_REGULAR")
    if g in ("CC_REGULAR", "CC_CHP", "COAL"):
        return (facility_id, g)
    return (facility_id, "ST_GAS")


@lru_cache(maxsize=None)
def unit_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    bins_path: str | Path = BINS_CSV_DEFAULT,
) -> dict[tuple[int, str], np.ndarray]:
    """Return ``{(plant_code, plant_group): (hours,) availability multiplier}``.

    Built from the unit-level outage extract (:data:`UNIT_OUTAGE_CSV`, the
    CAMPD-derived ``campd-unit-outages.csv`` covering full 2023 and 2024):
    every unit outage of at least :data:`UNIT_OUTAGE_MIN_DAYS` days whose
    window overlaps ``year`` derates its model bin's availability by
    ``unit_capacity_mw / bin_capacity_mw`` over the outage window (concurrent
    units sum, clipped at full derate). Each row's ``(outage_start,
    outage_end)`` is clipped to ``year`` on the model clock, so a single
    multi-year file feeds every backcast year. Combustion turbines are
    excluded and rows without a matching model bin or capacity are skipped.
    Years the file does not cover get an empty dict (every window misses the
    clock).
    """
    if not UNIT_OUTAGE_CSV.exists():
        return {}
    from market_sim.data.fleet import load_campd_bins

    bins = load_campd_bins(str(bins_path))
    cap = {
        (int(c), str(g)): float(m)
        for c, g, m in zip(
            bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
        )
        if m and m > 0
    }
    df = pd.read_csv(UNIT_OUTAGE_CSV)
    df = df[df["duration_days"] >= UNIT_OUTAGE_MIN_DAYS]
    sums: dict[tuple[int, str], np.ndarray] = {}
    for r in df.itertuples(index=False):
        tgt = _unit_outage_target(int(r.facility_id), r.unit_id, r.plant_group)
        if tgt is None or tgt not in cap:
            continue
        ucap = r.unit_capacity_mw
        if pd.isna(ucap) or float(ucap) <= 0.0:
            continue
        mask = outage_hour_mask(
            r.outage_start,
            pd.Timestamp(r.outage_end) + pd.Timedelta(days=1),
            year, hours,
        )
        if not mask.any():
            continue
        arr = sums.setdefault(tgt, np.zeros(hours))
        arr[mask] += float(ucap) / cap[tgt]
    return {k: np.clip(1.0 - v, 0.0, 1.0) for k, v in sums.items()}


# Partial (unit-level) outage derates approximated from CAMPD CF-ceiling
# plateaus (scripts/derive_partial_outages.py). A multiplicative availability
# factor per plant: 1.0 outside detected windows, derate_factor within.
PARTIAL_OUTAGE_CSV: Path = (
    Path(__file__).parents[3] / "inputs" / "raw-data" / "campd-partial-outages.csv"
)


@lru_cache(maxsize=None)
def partial_outage_derate_factors(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: (hours,) availability multiplier}`` from the
    CAMPD-derived partial-outage windows. 1.0 outside detected ceiling plateaus,
    the window's derate factor within (deepest wins where they overlap)."""
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
