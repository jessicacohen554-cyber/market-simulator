"""MISO-native published generation-outage / capacity-availability overlay.

The MISO analog of ERCOT's measured DAM capacity-availability record
(:func:`market_sim.data.outages.ercot_thermal_dam_availability_series`, from the
60-Day DAM disclosure). Where ERCOT publishes a unit-resolved DAM capability, the
only MISO-public outage record is **aggregate**: MISO's daily Multiday Operating
Margin Forecast Report (``docs.misoenergy.org/marketreports/YYYYMMDD_mom.xlsx``,
``OUTAGE`` sheet) tabulates capacity offline in MW by operating **region**
(North / Central / South; ``MISO`` = the system total = North+Central+South) and
by **cause type** (Derated / Forced / Planned / Unplanned) — with **no unit or
fuel-class identity**. So this overlay enters the model as a region availability
*envelope*, not the per-unit derate the CAMPD extract produces.

Built by ``scripts/data/fetch_miso_outages.py`` into
``data/raw/miso-generation-outages/`` (see the ``_SOURCE.md`` sidecar for the
citation + MISO disclaimer). Coverage begins 2023-01-01 (MISO does not publish
this report earlier). The committed in-repo form is a compact **wide CSV**, one
file per year (``miso_outages_estimated_<year>.csv``) — this repo's web-session
push path is API-only (text) and cannot carry a binary parquet blob, so the
efficient parquet the fetch script also writes is a local (gitignored) artifact
and the CSV is the portable source of truth. :func:`_load_estimated` prefers the
parquet when present and falls back to the CSVs.

**Rule-13 admissibility.** The offline-MW record is a MISO-published, measured
physical/market availability quantity (never a price, never an outcome fed back
to force a fit). Its forward analogue is the statistical outage-rate model, so
it is a **backcast/calibration overlay only**; a forecast year keeps the
statistical stack. Because the report gives a regional/system total rather than
a unit identity, the derate this module builds (:func:`miso_native_outage_derate_factors`)
distributes the measured offline MW across the region's thermal fleet as a
uniform availability envelope — an aggregate approximation whose exact
composition (cause-type selection, denominator, replace-vs-multiply against the
statistical availability) is a calibration decision to be made and validated in
a future MISO calibration session. The unambiguous measured outputs
(:func:`miso_outage_mw_series`) carry no such modelling choice and are the
primary intake.

Solve-path wiring — the ``ScenarioConfig.miso_native_outage_source`` gate that
selects this overlay over the CAMPD unit-outage derate, plus the one-branch
seam in :func:`market_sim.data.fleet.generators_to_fleet_arrays` — is a
paste-ready follow-up in
``docs/handoffs/miso-native-outage-wiring-2026-07.md`` (default off; a
solve-affecting change deferred to the calibration session that validates it).
This module is usable standalone today.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.outages import _hour_of_year

logger = logging.getLogger(__name__)

# Resolves through the config/paths.py registry root (RAW_DATA_DIR), per the
# repo's path convention (never Path(__file__).parents[...]). Kept here rather
# than as a named export in paths.py so this intake lands as new files only.
MISO_OUTAGES_DIR = RAW_DATA_DIR / "miso-generation-outages"

# The four cause-type buckets the OUTAGE sheet tabulates (mutually exclusive;
# their sum is total capacity offline). Region "MISO" is the system total.
CAUSE_TYPES: tuple[str, ...] = ("Derated", "Forced", "Planned", "Unplanned")
REGIONS: tuple[str, ...] = ("North", "Central", "South", "MISO")

# Cause types the AVAILABILITY DERATE sums (miso-85 composition decision; the
# open question left by docs/handoffs/miso-native-outage-wiring-2026-07.md
# "Composition to settle in calibration"). The UNPLANNED components only —
# "Planned" is excluded, exactly as the sibling PJM instrument excludes its
# "planned" bucket (data.pjm_outages.PJM_OUTAGE_DEFAULT_TYPES = forced +
# maintenance), for two independent reasons:
#
#   1. Double count. The model already carries a planned-outage layer for the
#      covered classes (the statistical POF / CAMPD maintenance windows, plus
#      the separate nuclear refuel-availability overlay), so re-applying the
#      report's Planned MW on top counts the same maintenance twice.
#   2. Non-thermal contamination + provable infeasibility. The report's MW is a
#      WHOLE-REGISTERED-FLEET total (no fuel identity), while this derate applies
#      it to the fossil-thermal bins against a fossil-thermal denominator. The
#      Planned bucket is where the non-thermal scheduled work lives (nuclear
#      refuel, hydro/renewable maintenance) and it dominates the total (2023-25
#      annual mean 17.6-20.6 GW of a 41.8-48.7 GW total, peaking at 36.4 GW in
#      April vs 7.9 GW in July). Summing all four leaves LESS available thermal
#      capacity than MISO's own metered thermal output: measured EIA-930 daily-max
#      coal+gas generation exceeds the all-cause envelope's available capacity on
#      12 / 15 / 61 days of 2023 / 2024 / 2025 (worst excess 12.7 GW), and July
#      2025 mean headroom is 0.3 GW on a 118 GW fleet — before reserves. The
#      unplanned-only set is feasible on every day but one (2025-05, 1.6 GW).
#
# The retained buckets are the measured analogue of the model's forced-outage /
# derate layer: "Forced" and "Unplanned" are flat year-round (no shoulder peak),
# and "Derated" peaks in JULY-AUGUST (10.5 GW vs 6.0 GW in March) — the ambient
# summer capability derate GADS EFORd counts, not scheduled work. The resulting
# fleet-average availability (0.816 / 0.795 / 0.763) is within a few points of
# the independent CAMPD per-unit measured derate it replaces (0.763 / 0.768 /
# 0.782), so the swap is level-neutral and changes the availability *shape*, not
# its magnitude — the point of the overlay (the CAMPD detector reads economic
# idleness as outage; see results/calibration/FINDING-ercot79-phantom-outage-2026-07.md).
UNPLANNED_CAUSE_TYPES: tuple[str, ...] = ("Derated", "Forced", "Unplanned")

# Committed in-repo form: compact wide CSV, one file per calendar year
# (``miso_outages_estimated_<year>.csv``: an ``interval_date`` column + one
# ``<Region>_<CauseType>`` column per region×cause, integer MW). CSV rather than
# parquet because this repo's web-session push path is API-only (text) and cannot
# carry a binary parquet blob (see the module docstring / _SOURCE.md); the fetch
# script also writes the efficient parquet locally (gitignored). The wide layout
# keeps each year ~34 KB.
ESTIMATED_CSV_GLOB = "miso_outages_estimated_*.csv"
# Local-only efficient artifacts the fetch script writes (gitignored; preferred
# when present because they carry the un-rounded MW + publish_date provenance).
ESTIMATED_PARQUET = MISO_OUTAGES_DIR / "miso_generation_outages_estimated.parquet"

# Fossil-thermal plant groups the aggregate envelope is applied to. Nuclear is
# excluded (it carries its own measured refuel-availability overlay, and folding
# the report's nuclear outages in here would double-count); renewables/hydro are
# excluded because a wind/solar "outage" is not a dispatchable-capacity derate.
# The report's regional total still includes those fuels' outages, which this
# thermal-only application cannot net out — an inherent aggregate approximation
# documented in the module docstring.
_THERMAL_GROUPS: frozenset[str] = frozenset(
    # Artifact class vocabulary (the extract / capacity-map keys): coal is its
    # family token; a fleet unit is matched through artifact_class (COAL-SUB).
    {
        COAL_ARTIFACT_FAMILY,
        "CC_REGULAR",
        "CC_CHP",
        "ST_GAS",
        "ST_CHP",
        "CT_PEAKER",
        "CT_CHP",
    }
)


def _melt_wide(w: pd.DataFrame) -> pd.DataFrame:
    """Reshape one wide outage frame (``interval_date`` + ``<Region>_<Type>``
    columns) into long ``(interval_date, region, cause_type, outage_mw)`` rows.
    """
    m = w.melt(id_vars="interval_date", var_name="col", value_name="outage_mw")
    m = m.dropna(subset=["outage_mw"])
    # Region/type split on the LAST underscore ("North_Central" is not a region,
    # but the fixed vocab has no underscored region; rsplit keeps it robust).
    parts = m["col"].str.rsplit("_", n=1, expand=True)
    m["region"] = parts[0]
    m["cause_type"] = parts[1]
    return m[["interval_date", "region", "cause_type", "outage_mw"]]


@lru_cache(maxsize=None)
def _load_estimated() -> pd.DataFrame | None:
    """Load the settled estimated (actual) outage series, or ``None`` if absent.

    Prefers the local efficient parquet (:data:`ESTIMATED_PARQUET`, un-rounded MW
    + ``publish_date`` provenance) when the fetch script has written it; otherwise
    reads the committed per-year wide CSVs (:data:`ESTIMATED_CSV_GLOB`) and melts
    them to long. Returns a frame with columns ``interval_date`` (datetime),
    ``region``, ``cause_type``, ``outage_mw`` (float), or ``None`` when neither
    source is present. Cached read-only.
    """
    if ESTIMATED_PARQUET.exists():
        df = pd.read_parquet(ESTIMATED_PARQUET)
        df["interval_date"] = pd.to_datetime(df["interval_date"])
        df["region"] = df["region"].astype(str)
        df["cause_type"] = df["cause_type"].astype(str)
        return df
    csvs = sorted(MISO_OUTAGES_DIR.glob(ESTIMATED_CSV_GLOB))
    if not csvs:
        return None
    frames = [_melt_wide(pd.read_csv(p)) for p in csvs]
    df = pd.concat(frames, ignore_index=True)
    df["interval_date"] = pd.to_datetime(df["interval_date"])
    df["region"] = df["region"].astype(str)
    df["cause_type"] = df["cause_type"].astype(str)
    df["outage_mw"] = df["outage_mw"].astype(float)
    return df


def _daily_to_hours(
    daily: dict[tuple[int, int], float], year: int, hours: int
) -> np.ndarray:
    """Broadcast a ``{(month, day): value}`` daily series onto the 8760 clock.

    Each covered calendar day fills its 24-hour block on the model's fixed
    non-leap clock (:func:`~market_sim.data.outages._hour_of_year`; a leap
    year's Feb 29 is dropped). Uncovered days stay 0.0.
    """
    arr = np.zeros(hours, dtype=float)
    for (mo, dy), val in daily.items():
        if mo == 2 and dy == 29:
            continue  # non-leap model clock
        lo = _hour_of_year(mo, dy, 0)
        hi = min(lo + 24, hours)
        if hi > lo:
            arr[lo:hi] = val
    return arr


@lru_cache(maxsize=None)
def miso_outage_mw_series(
    year: int,
    region: str = "MISO",
    cause_types: tuple[str, ...] = CAUSE_TYPES,
    hours: int = HOURS_PER_YEAR,
) -> np.ndarray:
    """Return the measured hourly offline-MW series for ``year`` and ``region``.

    Sums the requested ``cause_types`` (default all four) for ``region`` on each
    covered day and broadcasts the daily total onto the model's fixed non-leap
    8760-hour clock. This is the unambiguous measured quantity — no modelling
    choice — and the primary intake. Returns an all-zero array when the parquet
    is absent or the year/region has no rows.
    """
    df = _load_estimated()
    if df is None:
        return np.zeros(hours, dtype=float)
    want_types = {t for t in cause_types if t in CAUSE_TYPES}
    sub = df[
        (df["interval_date"].dt.year == int(year))
        & (df["region"] == region)
        & (df["cause_type"].isin(want_types))
    ]
    if sub.empty:
        return np.zeros(hours, dtype=float)
    by_day = sub.groupby([sub["interval_date"].dt.month, sub["interval_date"].dt.day])[
        "outage_mw"
    ].sum()
    daily = {(int(m), int(d)): float(v) for (m, d), v in by_day.items()}
    return _daily_to_hours(daily, int(year), hours)


def miso_outage_available_years() -> list[int]:
    """Return the calendar years present in the estimated outage record."""
    df = _load_estimated()
    if df is None:
        return []
    return sorted({int(y) for y in df["interval_date"].dt.year.unique()})


@lru_cache(maxsize=None)
def _miso_thermal_capacity_mw() -> float:
    """Total MISO fossil-thermal nameplate (the envelope denominator).

    Summed over :data:`_THERMAL_GROUPS` from the model's own MISO fleet, so the
    derate is self-consistent with the capacity the LP dispatches. Reuses the
    per-``(plant_code, plant_group)`` capacity map the CAMPD overlay builds.
    """
    from market_sim.data.outages import _iso_plant_capacity

    cap = _iso_plant_capacity("MISO")
    return float(sum(mw for (code, grp), mw in cap.items() if grp in _THERMAL_GROUPS))


@lru_cache(maxsize=None)
def miso_native_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    iso: str = "MISO",
    cause_types: tuple[str, ...] = UNPLANNED_CAUSE_TYPES,
) -> dict[tuple[int, str], np.ndarray]:
    """Return ``{(plant_code, plant_group): (hours,) availability multiplier}``.

    The MISO-native substitute for
    :func:`~market_sim.data.outages.unit_outage_derate_factors`, matching its
    interface so the fleet builder applies it identically. Because the MISO
    report gives only a regional/system offline-MW total (no unit identity),
    this distributes that measured total across the region's thermal fleet as a
    **uniform** availability envelope:

        avail(t) = 1 - system_offline_MW(t) / MISO_thermal_capacity_MW

    applied to every fossil-thermal ``(plant_code, plant_group)`` bin
    (:data:`_THERMAL_GROUPS`). ``system_offline_MW`` is the ``MISO`` system-total
    of the requested ``cause_types`` — default :data:`UNPLANNED_CAUSE_TYPES`, the
    unplanned components (Derated + Forced + Unplanned), NOT all four: see that
    constant for the miso-85 composition decision (Planned is the model's own
    layer, is where the report's non-thermal scheduled work lives, and summing it
    here is refuted by MISO's own metered thermal output) — from
    :func:`miso_outage_mw_series`. The denominator is the model's own MISO
    fossil-thermal nameplate, so the derate is self-consistent with the
    dispatched fleet.

    Aggregate approximation (module docstring): the report's total includes
    nuclear/renewable outages this thermal-only application cannot net out, and
    the uniform split removes a proportional slice from every thermal bin rather
    than the units that were actually out. Intended to be selected by the
    ``ScenarioConfig.miso_native_outage_source`` gate (default off; wiring in
    ``docs/handoffs/miso-native-outage-wiring-2026-07.md``); the composition is a
    calibration decision. Returns ``{}`` when the record or the fleet capacity is
    unavailable (a clean no-op).
    """
    if (iso or "MISO").upper() != "MISO":
        return {}
    offline = miso_outage_mw_series(year, "MISO", tuple(cause_types), hours)
    if not offline.any():
        return {}
    denom = _miso_thermal_capacity_mw()
    if denom <= 0.0:
        logger.warning(
            "MISO thermal capacity is 0; miso_native_outage_derate_factors is a no-op"
        )
        return {}
    avail = np.clip(1.0 - offline / denom, 0.0, 1.0)
    if (avail >= 1.0).all():
        return {}
    from market_sim.data.outages import _iso_plant_capacity

    cap = _iso_plant_capacity("MISO")
    factors: dict[tuple[int, str], np.ndarray] = {}
    for code, grp in cap:
        if grp in _THERMAL_GROUPS:
            factors[(int(code), grp)] = avail
    logger.info(
        "MISO native outage envelope (%d): peak %.0f MW offline / %.0f MW thermal "
        "= min avail %.3f, applied to %d thermal bins",
        int(year),
        float(offline.max()),
        denom,
        float(avail.min()),
        len(factors),
    )
    return factors
