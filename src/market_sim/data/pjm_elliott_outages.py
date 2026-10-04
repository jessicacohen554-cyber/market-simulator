"""PJM Winter Storm Elliott hourly measured forced outage (backcast-only overlay input).

Source: PJM, *Winter Storm Elliott Event Analysis and Recommendation Report*
(2023-07-17), Figure 30 — GADS forced outages and derates by fuel, 23-25 Dec 2022,
digitised by ``scripts/data/digitise_pjm_elliott_forced_outages.py`` into
``data/raw/pjm-elliott-forced-outages/figure30_digitised.csv`` (README there: URL,
sha256, digitisation uncertainty). Admissible as a windowed, measured, backcast-only
outage overlay by owner ruling R-64 (2026-10-04; rule 13 [R-MEASURED]).

The figure prints even hours (plus 24 Dec 07:00); :func:`build_hourly_frame` puts the
bars on the model's 8760 clock (EIA-930 local prevailing, hour-beginning hh on 23 Dec
2022 = row 356*24 + hh; DST nets to zero by December), interpolates the odd hours
linearly and holds 25 Dec 23:00 at 22:00. That frame is the clean datatype
``pjm-elliott-forced-outages`` (``scripts/data/curate_pjm_elliott_forced_outages.py``);
:func:`elliott_forced_outage_mw` reads the clean partition when present and otherwise
builds the identical frame from the committed raw CSV (the
``data.pjm_outages`` committed-CSV fallback pattern), so a solve never depends on
``data/clean`` having been regenerated.

Consumer: ``data/fleet/arrays.py::_apply_outage_overlays`` under
``ScenarioConfig.pjm_elliott_measured_outage_overlay``.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HOURS_PER_YEAR
from market_sim.config.paths import RAW_DATA_DIR

logger = logging.getLogger(__name__)

DATATYPE = "pjm-elliott-forced-outages"
RAW_CSV: Path = RAW_DATA_DIR / "pjm-elliott-forced-outages" / "figure30_digitised.csv"
EVENT_YEAR = 2022
EVENT_START = pd.Timestamp("2022-12-23 00:00")
EVENT_HOURS = 72  # 23 Dec 00:00 .. 25 Dec 23:00 EPT, hour-beginning (Figure 30 span)
# Figure 30's own pre-front bars (23 Dec 00:00-04:00): the same-source baseline the
# overlay measures the event rise from (PRECOMMIT-closeout-pjm-elliott-2026-10-04 §2).
BASELINE_HOURS = 5
# Figure-30 fuel -> model ``Generator.fuel_type`` set. Hydro and "other" (< 0.6 GW in
# every bar) have no thermal availability row to derate and are not covered.
FUEL_GROUPS: dict[str, tuple[str, ...]] = {
    "gas": ("gas_cc", "gas_ct", "gas_st"),
    "coal": ("coal",),
    "oil": ("oil",),
    "nuclear": ("nuclear",),
}


def _event_start_row() -> int:
    """Model-clock row of 23 Dec 2022 00:00 EPT (hour-beginning)."""
    return int((EVENT_START - pd.Timestamp(f"{EVENT_YEAR}-01-01")) / pd.Timedelta("1h"))


def build_hourly_frame(raw_csv: Path | None = None) -> pd.DataFrame:
    """Return the tidy hourly frame (one row per event hour x fuel) from the raw CSV.

    Columns: ``iso``, ``year``, ``hour_of_year``, ``hour_beginning_ept``, ``fuel``,
    ``forced_outage_mw``, ``digitised`` (False for an interpolated or held hour).
    """
    raw = pd.read_csv(RAW_CSV if raw_csv is None else raw_csv)
    t0 = _event_start_row()
    hours = pd.date_range(EVENT_START, periods=EVENT_HOURS, freq="h")
    frames = []
    for fuel in sorted(raw.fuel.unique()):
        f = raw[raw.fuel == fuel]
        s = pd.Series(
            f.forced_outage_mw.to_numpy(float),
            index=pd.to_datetime(f.hour_beginning_ept),
        ).reindex(hours)
        read = s.notna().to_numpy()
        s = s.interpolate(limit_area="inside").ffill()
        frames.append(
            pd.DataFrame(
                {
                    "iso": "PJM",
                    "year": EVENT_YEAR,
                    "hour_of_year": np.arange(t0, t0 + EVENT_HOURS, dtype=np.int64),
                    "hour_beginning_ept": hours.astype("datetime64[ns]"),
                    "fuel": fuel,
                    "forced_outage_mw": s.to_numpy(float),
                    "digitised": read,
                }
            )
        )
    return pd.concat(frames, ignore_index=True)


@lru_cache(maxsize=1)
def _frame() -> pd.DataFrame | None:
    """Clean partition when present, else the identical frame from the raw CSV."""
    try:
        from scripts.lib.clean_io import read_clean

        return read_clean(DATATYPE, iso="PJM", year=EVENT_YEAR)
    except (ModuleNotFoundError, FileNotFoundError):
        pass
    if RAW_CSV.exists():
        return build_hourly_frame(RAW_CSV)
    logger.warning("pjm-elliott-forced-outages: neither clean nor raw source present")
    return None


def elliott_forced_outage_mw(
    year: int, hours: int = HOURS_PER_YEAR
) -> dict[str, np.ndarray] | None:
    """Measured GADS forced outage MW per covered fuel on the 8760 clock, or ``None``.

    Returns ``{fuel: (hours,) array}`` for the keys of :data:`FUEL_GROUPS`, NaN outside
    the 72 event hours. ``None`` for any year other than 2022 or when no source is
    present, so every other year is untouched by construction.
    """
    if int(year) != EVENT_YEAR:
        return None
    df = _frame()
    if df is None or df.empty:
        return None
    out: dict[str, np.ndarray] = {}
    for fuel in FUEL_GROUPS:
        arr = np.full(hours, np.nan)
        f = df[df.fuel == fuel]
        rows = f.hour_of_year.to_numpy(np.int64)
        keep = rows < hours
        arr[rows[keep]] = f.forced_outage_mw.to_numpy(float)[keep]
        out[fuel] = arr
    return out
