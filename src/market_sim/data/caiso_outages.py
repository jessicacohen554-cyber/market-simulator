"""CAISO measured generator availability from the DAM curtailment reports.

Third stage of the owner-directed CAISO DAM-outage intake (caiso-104; fetch:
:mod:`scripts.data.fetch_caiso_dam_outages`, consolidation:
:mod:`scripts.data.curate_caiso_dam_outages`). Turns the measured
Curtailed-and-Non-Operational-Generator outage episodes
(``data/raw/caiso-dam-outages/caiso-dam-outage-windows.parquet``) into a
per-plant hourly availability multiplier keyed exactly like
:func:`market_sim.data.outages.unit_outage_derate_factors` — so it drops into
the same fleet overlay with **DAM-before-CAMPD precedence**: the published
outage schedule replaces the CAMPD emissions-gap inference for the CAISO
thermal plants it covers, and the CAMPD windows remain the fallback everywhere
else (uncovered plants, and years before CAISO's 2021-06-18 series).

Each covered CAISO resource is mapped to its model ``(plant_code, plant_group)``
via the reviewed crosswalk
(``data/raw/reference/caiso-resource-eia-crosswalk.csv``,
:mod:`scripts.data.build_caiso_resource_crosswalk`); only ``accepted`` rows are
used, so an unreviewed guess never enters a solve.

Admissibility (CLAUDE.md rule 14 prefer-measured; rule 13 forward analogue):
a measured *physical availability event* (an outage window with a curtailed-MW
level and a real FORCED/PLANNED label), grounded in reported operation, whose
forecast analogue is the statistical WEFOR/POF draw — not an outcome fitted to
a residual.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.plant_taxonomy import COAL_ARTIFACT_FAMILY
from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import RAW_DATA_DIR, REFERENCE_DIR
from market_sim.data.outages import _iso_plant_capacity, outage_hour_mask

# First CAISO prior-trade-date publication; no DAM availability before this.
CAISO_DAM_FIRST_DATE = pd.Timestamp("2021-06-18")

CROSSWALK_CSV: Path = REFERENCE_DIR / "caiso-resource-eia-crosswalk.csv"
DAM_OUTAGE_WINDOWS_PARQUET: Path = (
    RAW_DATA_DIR / "caiso-dam-outages" / "caiso-dam-outage-windows.parquet"
)

# Model asset classes the availability overlay applies to (renewables are LP
# decision variables bounded by CF, storage/CTs dispatch economically) — the
# thermal set routed by outages._generic_unit_outage_target.
_OVERLAY_GROUPS: frozenset[str] = frozenset(
    # Artifact class vocabulary (the extract / capacity-map keys): coal is its
    # family token; a fleet unit is matched through artifact_class (COAL-SUB).
    {COAL_ARTIFACT_FAMILY, "CC_REGULAR", "CC_CHP", "ST_GAS", "ST_CHP"}
)


@lru_cache(maxsize=1)
def load_crosswalk() -> dict[str, tuple[int, str]]:
    """Return ``{resource_id: (plant_code, plant_group)}`` from accepted rows.

    Reads the reviewed CAISO-resource -> EIA-plant crosswalk. Only rows flagged
    ``accepted`` (truthy) with a valid ``plant_code``/``plant_group`` are used;
    everything else is left to the CAMPD fallback.
    """
    if not CROSSWALK_CSV.is_file():
        return {}
    df = pd.read_csv(CROSSWALK_CSV)
    if "accepted" in df.columns:
        acc = df["accepted"].astype(str).str.strip().str.lower()
        df = df[acc.isin({"1", "true", "yes", "y"})]
    out: dict[str, tuple[int, str]] = {}
    for _, r in df.iterrows():
        code, group, rid = (
            r.get("plant_code"),
            r.get("plant_group"),
            r.get("resource_id"),
        )
        if pd.isna(code) or pd.isna(group) or pd.isna(rid):
            continue
        out[str(rid).strip()] = (int(code), str(group).strip())
    return out


def _load_windows() -> pd.DataFrame | None:
    """Load the consolidated DAM outage episodes (or None if absent)."""
    if not DAM_OUTAGE_WINDOWS_PARQUET.is_file():
        return None
    return pd.read_parquet(
        DAM_OUTAGE_WINDOWS_PARQUET,
        columns=["resource_id", "start", "end", "curtailment_mw"],
    )


@lru_cache(maxsize=None)
def caiso_dam_outage_derate_factors(
    year: int,
    hours: int = HOURS_PER_YEAR,
    iso: str = "CAISO",
) -> dict[tuple[int, str], np.ndarray]:
    """Return ``{(plant_code, plant_group): (hours,) availability multiplier}``.

    Built from the measured CAISO DAM outage episodes: each mapped episode
    removes ``curtailment_mw`` from its plant over ``[start, end)`` (clipped to
    ``year`` on the model clock; concurrent episodes sum), and the plant's
    availability multiplier is ``1 - offline_mw / plant_capacity`` clipped to
    ``[0, 1]``. ``plant_capacity`` is the model group's EIA-860 nameplate
    (:func:`market_sim.data.outages._iso_plant_capacity`). Returns an empty dict
    for ISOs other than CAISO, or when the windows/crosswalk are absent.
    """
    if (iso or "CAISO").upper() != "CAISO":
        return {}
    windows = _load_windows()
    if windows is None or windows.empty:
        return {}
    crosswalk = load_crosswalk()
    if not crosswalk:
        return {}
    cap = _iso_plant_capacity("CAISO")

    start = pd.to_datetime(windows["start"], errors="coerce")
    end = pd.to_datetime(windows["end"], errors="coerce")
    mw = pd.to_numeric(windows["curtailment_mw"], errors="coerce").fillna(0.0)
    rid = windows["resource_id"].astype("string")

    offline: dict[tuple[int, str], np.ndarray] = {}
    for i in range(len(windows)):
        key = crosswalk.get(str(rid.iloc[i]))
        if key is None or key not in cap:
            continue
        s, e, m = start.iloc[i], end.iloc[i], float(mw.iloc[i])
        if m <= 0 or pd.isna(s) or pd.isna(e) or e <= s:
            continue
        if s.year > year or e.year < year:
            continue
        mask = outage_hour_mask(s, e, year, hours)
        if not mask.any():
            continue
        arr = offline.get(key)
        if arr is None:
            arr = np.zeros(hours, dtype=float)
            offline[key] = arr
        arr[mask] += m

    factors: dict[tuple[int, str], np.ndarray] = {}
    for key, off in offline.items():
        denom = cap.get(key, 0.0)
        if denom > 0:
            factors[key] = np.clip(1.0 - off / denom, 0.0, 1.0)
    return factors


def has_dam_coverage(year: int) -> bool:
    """True when CAISO's DAM curtailment feed covers any of ``year``."""
    return year >= CAISO_DAM_FIRST_DATE.year
