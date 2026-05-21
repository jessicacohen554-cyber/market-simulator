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

# Plant groups whose sustained outages are overlaid: coal and combined cycle
# (regular and CHP). A plant qualifies if it has any bin in this set; the
# per-bin group filter at overlay time then restricts the zeroing to those
# coal/CC bins (e.g. Barney M Davis carries both a CC and an ST_GAS bin —
# only the CC bin is outaged).
QUALIFYING_PLANT_GROUPS: frozenset[str] = frozenset(
    {"COAL", "CC_REGULAR", "CC_CHP", "ST_GAS"}
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
    """
    codes = _qualifying_plant_codes(bins_path)
    df = pd.read_csv(
        outages_path, parse_dates=["outage_start", "outage_stop"]
    )
    df = df[df["oris_code"].isin(codes)]

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
    bins_path: str | Path = BINS_CSV_DEFAULT,
) -> dict[int, np.ndarray]:
    """Return ``{plant_code: bool mask}`` of qualifying outage hours in ``year``.

    Only coal/CC plants with a sustained (> :data:`MIN_OUTAGE_SPAN_HOURS`)
    outage overlapping ``year`` appear; the masks are on the model's fixed
    8760-hour ERCOT-local clock. Returns an empty dict when the outage
    extract is missing, so a backcast degrades gracefully to the statistical
    availability model.
    """
    outages_path = Path(outages_path)
    if not outages_path.exists():
        logger.warning(
            "historic outage extract not found at %s; "
            "falling back to statistical availability",
            outages_path,
        )
        return {}
    all_masks = _build_outage_masks(str(outages_path), str(bins_path), hours)
    return {
        code: by_year[year]
        for code, by_year in all_masks.items()
        if year in by_year
    }
