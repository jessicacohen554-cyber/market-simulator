"""PJM measured generation-outage availability (Data Miner 2 gen_outages_by_type).

The PJM analogue of the ERCOT 60-Day DAM disclosure thermal-availability overlay
(:func:`market_sim.data.outages.ercot_thermal_dam_availability_series`), and the
aggregate-coverage intake replacement for the CAMPD unit-outage fallback in a PJM
backcast. PJM publishes, daily at 06:00 EPT, the active/approved MW on outage for
the operating day and the next six days, split by outage type (forced /
maintenance / planned) and by region (Mid Atlantic - Dominion, Western, PJM RTO).
This is a forward-looking, operator-published capacity-availability quantity that
regenerates for a future day and responds to conditions (CLAUDE.md rule 13
admissible) — a measured/forecast INPUT, never a fitted answer pinned to actuals.

Source pull: ``scripts/data/fetch_pjm_outages.py``; processed by
``scripts/data/derive_pjm_dam_availability.py``. Provenance and the
committed-CSV / local-parquet split: ``data/raw/pjm-outages/README.md`` and
``data/dictionary/schema/pjm-outages.schema.yaml``.

Gated by ``ScenarioConfig.pjm_dam_availability`` (default off, backcast only) —
see the wiring in ``docs/handoffs/pjm-dam-availability-wiring-2026-07.md`` (the
flag + the ``data.fleet`` application share the ERCOT water-fill).

FROZEN AGAINST RESIDUALS (rule 23): the covered classes, outage-type default, and
region are cited defaults, not tuned values; re-derive only when the raw PJM
source is re-pulled.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import RAW_DATA_DIR

# Efficient columnar artifact (all years/lead days) the loader prefers when
# present. Gitignored — the repo's API-only push path cannot commit a binary
# blob — and regenerated locally by the derive script from the committed CSVs.
PJM_DAM_AVAILABILITY_PARQUET: Path = RAW_DATA_DIR / "pjm-dam-availability.parquet"

# Committed, portable per-year CSV fallback (current-day actuals, lead_days == 0).
# The loader falls back to ``pjm-outages/by-year/gen_outages_by_type_<year>.csv``
# on a fresh clone. Both sources carry the identical tidy schema
# (data/dictionary/schema/pjm-outages.schema.yaml).
PJM_OUTAGE_BYYEAR_DIR: Path = RAW_DATA_DIR / "pjm-outages" / "by-year"

# Region whose outage total drives the fleet-wide availability. "PJM RTO" is the
# whole footprint (== the two sub-regions summed); the sub-regional totals
# ("Mid Atlantic - Dominion", "Western") are retained for a future zone-resolved
# refinement but are not used by the default (uniform) transform.
PJM_OUTAGE_DEFAULT_REGION: str = "PJM RTO"

# Outage types summed into the unavailability MW. Default = the UNPLANNED
# components (forced + maintenance), the measured analogue of the statistical
# forced-outage (EFOR) rate the model's availability model estimates; "planned"
# is excluded because it is dominated by scheduled nuclear refuel + fossil
# maintenance the model already carries via the nuclear availability overlay and
# the statistical maintenance schedule (avoids double-counting nuclear refuels
# against the fossil fleet). A cited default, not a tuned value.
PJM_OUTAGE_DEFAULT_TYPES: tuple[str, ...] = ("forced", "maintenance")

#: EVERY published outage subtotal. The basis the ``pjm_measured_outage_event
#: _cap`` overlay compares on (pjm-161): the model's incumbent CAMPD envelope
#: carries planned outages too, so a like-for-like comparison must include
#: them. Using the UNPLANNED default against that envelope is a definitional
#: mismatch that mechanically makes the measured target look LESS derated than
#: the model on almost every day — which is what produced pjm-145's
#: restore-on-364-of-365-days and, through it, its refusal.
PJM_OUTAGE_ALL_TYPES: tuple[str, ...] = ("forced", "maintenance", "planned")

# PJM fossil-thermal model classes the uniform availability derate covers. The
# capacity denominator is the model fleet's nameplate in these groups; nuclear /
# hydro / renewables / storage are excluded (own availability treatment).
PJM_OUTAGE_COVERED_GROUPS: frozenset[str] = frozenset(
    # Artifact class vocabulary (the extract / capacity-map keys): coal is its
    # family token; a fleet unit is matched through artifact_class (COAL-SUB).
    {
        COAL_ARTIFACT_FAMILY,
        "CC_REGULAR",
        "CT_PEAKER",
        "ST_GAS",
        "CC_CHP",
        "CT_CHP",
        "ST_CHP",
    }
)

_PJM_TYPE_COLUMN: dict[str, str] = {
    "total": "total_outages_mw",
    "planned": "planned_outages_mw",
    "maintenance": "maintenance_outages_mw",
    "forced": "forced_outages_mw",
}

_PJM_OUTAGE_COLUMNS = [
    "forecast_date",
    "lead_days",
    "region",
    *_PJM_TYPE_COLUMN.values(),
]


def _load_pjm_outage_source(year: int) -> pd.DataFrame | None:
    """Return the tidy PJM outage rows for ``year``, or ``None`` when absent.

    Prefers the (gitignored, local) columnar parquet
    :data:`PJM_DAM_AVAILABILITY_PARQUET` when present — read once and filtered to
    ``year`` — and otherwise falls back to the committed per-year CSV
    ``pjm-outages/by-year/gen_outages_by_type_<year>.csv``
    (:data:`PJM_OUTAGE_BYYEAR_DIR`). Both carry the identical tidy columns, so the
    downstream reshaping is source-agnostic. The per-year CSV is partitioned by
    execution-date year; the current-day (``lead_days == 0``) rows the loader uses
    have ``forecast_date == execution_date``, so the year semantics match.
    """
    if PJM_DAM_AVAILABILITY_PARQUET.exists():
        df = pd.read_parquet(PJM_DAM_AVAILABILITY_PARQUET, columns=_PJM_OUTAGE_COLUMNS)
        yr = pd.to_datetime(df["forecast_date"]).dt.year
        return df[yr == int(year)]
    csv = PJM_OUTAGE_BYYEAR_DIR / f"gen_outages_by_type_{int(year)}.csv"
    if csv.exists():
        return pd.read_csv(csv, usecols=_PJM_OUTAGE_COLUMNS)
    return None


@lru_cache(maxsize=None)
def pjm_outage_mw_series(
    year: int,
    hours: int = HOURS_PER_YEAR,
    region: str = PJM_OUTAGE_DEFAULT_REGION,
    outage_types: tuple[str, ...] = PJM_OUTAGE_DEFAULT_TYPES,
) -> np.ndarray:
    """Return the measured PJM outage MW for ``year`` on the fixed 8760 clock.

    Reads the current-day *actual* outage (``lead_days == 0``) for ``region``
    from the PJM outage source (:func:`_load_pjm_outage_source` — the local
    parquet if present, else the committed per-year CSV), sums the requested
    ``outage_types`` (a subset of ``forced`` / ``maintenance`` / ``planned`` /
    ``total``), and broadcasts each delivery day's MW to a flat 24-hour block on
    the model's non-leap clock (a leap year's Feb 29 row is dropped, the archive
    convention). Uncovered days stay ``NaN`` so the caller can fall back to its
    statistical estimate there. Returns an all-``NaN`` array when no source is
    present or the year has no rows. This is the raw, allocation-free measured
    quantity; the per-class availability transform is
    :func:`pjm_dam_availability_series`.
    """
    from market_sim.data.outages import _hour_of_year

    df = _load_pjm_outage_source(int(year))
    if df is None:
        return np.full(hours, np.nan)
    df = df[(df["lead_days"] == 0) & (df["region"] == region)]
    dts = pd.to_datetime(df["forecast_date"])
    df = df[dts.dt.year == int(year)]
    if df.empty:
        return np.full(hours, np.nan)
    dts = pd.to_datetime(df["forecast_date"])
    mw_cols = [_PJM_TYPE_COLUMN[t] for t in outage_types]
    day_mw = df[mw_cols].sum(axis=1).clip(lower=0.0).to_numpy(dtype=float)
    months = dts.dt.month.to_numpy()
    days = dts.dt.day.to_numpy()
    out = np.full(hours, np.nan)
    for mo, dy, val in zip(months, days, day_mw):
        if mo == 2 and dy == 29:
            continue  # non-leap model clock
        lo = _hour_of_year(int(mo), int(dy), 0)
        hi = min(lo + 24, hours)
        out[lo:hi] = val
    return out


@lru_cache(maxsize=None)
def pjm_dam_availability_series(
    year: int,
    hours: int = HOURS_PER_YEAR,
    iso: str = "PJM",
    region: str = PJM_OUTAGE_DEFAULT_REGION,
    outage_types: tuple[str, ...] = PJM_OUTAGE_DEFAULT_TYPES,
) -> dict[str, np.ndarray]:
    """Return ``{plant_group: (hours,) measured class availability}`` for PJM.

    The PJM analogue of
    :func:`market_sim.data.outages.ercot_thermal_dam_availability_series`, gated
    by ``ScenarioConfig.pjm_dam_availability`` (backcast only). PJM publishes
    outages only at the RTO/sub-region aggregate — never per fuel class — so the
    measured unplanned-outage MW (:func:`pjm_outage_mw_series`) is converted to a
    single fleet-wide availability fraction

        avail(day) = 1 - outage_mw(day) / fossil_thermal_capacity_mw

    against the model's own PJM fossil-thermal nameplate
    (:func:`market_sim.data.outages._iso_plant_capacity` summed over
    :data:`PJM_OUTAGE_COVERED_GROUPS`), and returned for every covered class —
    i.e. a UNIFORM derate across the fossil-thermal fleet. This is the honest
    first-order transform the public aggregate data supports; a zone/class-
    resolved allocation is left to a future refinement (the parquet keeps the
    sub-regional detail). Uncovered days are ``NaN`` (the caller keeps its
    statistical availability there); the value is clipped to [0, 1]. Returns an
    empty dict when no source is present or the year has no rows, so callers
    degrade to the statistical model unchanged.
    """
    from market_sim.data.outages import _iso_plant_capacity

    mw = pjm_outage_mw_series(year, hours, region, outage_types)
    if not np.isfinite(mw).any():
        return {}
    cap = _iso_plant_capacity((iso or "PJM").upper())
    fossil_cap = sum(m for (_, g), m in cap.items() if g in PJM_OUTAGE_COVERED_GROUPS)
    if fossil_cap <= 0.0:
        return {}
    with np.errstate(invalid="ignore"):
        avail = np.clip(1.0 - mw / fossil_cap, 0.0, 1.0)
    # NaN in mw (uncovered days) propagates to NaN so the caller falls back to the
    # statistical availability on those days.
    avail = np.where(np.isfinite(mw), avail, np.nan)
    return {g: avail.copy() for g in sorted(PJM_OUTAGE_COVERED_GROUPS)}
