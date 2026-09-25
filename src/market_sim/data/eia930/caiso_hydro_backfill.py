"""Repair EIA-930's missing CISO hydro cell from CAISO's own measured fuel mix.

EIA-930 files CISO ``NG: WAT`` (conventional hydro) as MISSING — NaN, not zero —
from 2019-10-01 through 2020-08-24, and EIA's own ``(Adjusted)`` / ``(Imputed)``
columns of the bulk BALANCE files are empty over the same window. Because
``Net generation`` is the sum of the reported fuel cells, it omits hydro in those
hours too, while the independently-filed ``Demand`` does not: the
``Demand − (Net generation − Total interchange)`` residual jumps from its normal
+0.5–0.9 TWh/month to +1.7–2.6 TWh/month exactly in the gap months. Every reader
of the frame inherits the hole — the measured hydro budget pins those months to
~0 (:func:`market_sim.data.eia930.envelopes.measured_monthly_hydro`), and the
CAISO supply-consistent demand (``Net generation − NG + CEMS − TI``) would lose
~2 GW of load for eleven months.

The measured source is CAISO's "Today's Outlook" historical fuel mix
(``https://www.caiso.com/outlook/history/<YYYYMMDD>/fuelsource.csv``, 5-minute,
committed raw under ``data/raw/caiso-outlook-fuelsource/`` by
``scripts/data/fetch_caiso_outlook_fuelsource.py``) — the ISO-native series the
EIA-930 CISO cells are reported from. ``large_hydro + small_hydro`` is the
``NG: WAT`` object: over the 6,557 hours of 2019 where both are present the
EIA-930 cell is 0.9965 × the Outlook sum (monthly within ±0.5 % in every month,
Jan–Sep), mean |Δ| 87 MW on a ~3–4 GW series, hourly r = 0.94. The CLOCK is
measured, not assumed: grouping the 5-minute rows by their UTC hour-beginning
aligns the Outlook series to the EIA-930 row stamp at lag 0 for solar
(r 0.970), natural gas (0.986) and nuclear (1.000) — every other lag is worse —
so the hydro fill rides the same alignment.

The repair (:func:`repair_measured_gaps`) touches ONLY FILED hours (``Net
generation`` present) whose ``NG: WAT`` is NaN and for which the Outlook series
has a value; it fills the cell and, where
``Net generation`` is present and demonstrably excludes hydro (it sits closer to
the sum of the other reported fuel cells than to that sum plus the fill — a
parameter-free test of the filing identity, which holds to ≤ 3 MW rounding in
every hour of 2019–2021), adds the same MW to ``Net generation``. Nothing else
moves. A BA with no registered source, or a year with no committed source file,
is returned unchanged (the same object), which is what keeps every 2022–2025
frame byte-identical. Admissibility (rule 13 ``[R-MEASURED]``): a measured
physical input that regenerates for any year from the same public source, used
to repair a missing measurement — never a fitted answer. Rule 14
``[R-ACCURATE]``: it replaces an implicit zero with the measured value.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.paths import CAISO_OUTLOOK_FUELSOURCE_DIR

logger = logging.getLogger("market_sim.data.eia_loader")

# The Outlook series' wall clock (prevailing Pacific time, DST-following).
_OUTLOOK_TZ = "America/Los_Angeles"
# Outlook columns whose sum is the EIA-930 ``NG: WAT`` object.
_OUTLOOK_HYDRO_COLUMNS: tuple[str, ...] = ("large_hydro", "small_hydro")


@lru_cache(maxsize=8)
def outlook_hourly_hydro(year: int) -> pd.Series | None:
    """CAISO Outlook ``large_hydro + small_hydro`` (MW) by UTC hour-beginning.

    Indexed by tz-naive UTC hour-beginning — the EIA-930 frames' ``UTC time``
    clock at the measured lag-0 alignment (module docstring). 5-minute rows
    average within their hour. The repeated fall-back hour is ambiguous on the
    source's wall clock and is dropped rather than guessed; a NaN source value
    stays out of the mean. Returns ``None`` when no committed file covers
    ``year``.
    """
    path = CAISO_OUTLOOK_FUELSOURCE_DIR / f"fuelsource_{int(year)}.csv.gz"
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype=str)
    hydro = sum(pd.to_numeric(df[c], errors="coerce") for c in _OUTLOOK_HYDRO_COLUMNS)
    local = pd.to_datetime(df["date"] + " " + df["time"], format="%Y-%m-%d %H:%M")
    utc = local.dt.tz_localize(
        _OUTLOOK_TZ, ambiguous="NaT", nonexistent="shift_forward"
    ).dt.tz_convert("UTC")
    keep = utc.notna() & hydro.notna()
    hb = utc[keep].dt.floor("h").dt.tz_localize(None)
    return (
        pd.Series(hydro[keep].to_numpy(float), index=hb.to_numpy())
        .groupby(level=0)
        .mean()
    )


#: BA -> ``{frame column: per-year hourly source}``. A registry rather than an
#: ``if ba == ...`` branch, so another BA's measured gap source is one entry.
MEASURED_GAP_SOURCES: dict[str, dict[str, Callable[[int], pd.Series | None]]] = {
    "CISO": {"NG: WAT": outlook_hourly_hydro},
}


def repair_measured_gaps(
    frame: pd.DataFrame | None, ba_code: str, year: int
) -> pd.DataFrame | None:
    """Fill a BA frame's missing fuel cells from its registered measured source.

    See the module docstring. Returns ``frame`` itself (unchanged) when there is
    nothing to repair, else a repaired copy.
    """
    if frame is None or ba_code not in MEASURED_GAP_SOURCES:
        return frame
    out = None
    for col, loader in MEASURED_GAP_SOURCES[ba_code].items():
        if col not in frame.columns or not frame[col].isna().any():
            continue
        src = loader(int(year))
        if src is None:
            continue
        stamps = pd.DatetimeIndex(frame["UTC time"])
        if stamps.tz is not None:
            stamps = stamps.tz_convert("UTC").tz_localize(None)
        fill = src.reindex(stamps).to_numpy(float)
        base = frame if out is None else out
        cell = pd.to_numeric(base[col], errors="coerce").to_numpy(float)
        hit = np.isnan(cell) & np.isfinite(fill)
        if "Net generation" in base.columns:
            # Only hours the BA FILED (Net generation present) with the cell
            # missing — the defect being repaired. A wholly-absent hour is a
            # gap row the loader inserted, and bridging it stays the readers'
            # own business (this keeps CISO 2021, whose only NaN WAT hours are
            # five such rows, and the 2021-2025 hydro climatology untouched).
            filed = np.isfinite(
                pd.to_numeric(base["Net generation"], errors="coerce").to_numpy(float)
            )
            hit &= filed
        if not hit.any():
            continue
        if out is None:
            out = frame.copy()
        out[col] = np.where(hit, fill, cell)
        if "Net generation" in out.columns:
            others = [c for c in out.columns if c.startswith("NG: ") and c != col]
            rest = (
                out[others]
                .apply(pd.to_numeric, errors="coerce")
                .sum(axis=1, min_count=1)
            )
            ng = pd.to_numeric(out["Net generation"], errors="coerce").to_numpy(float)
            excl = np.abs(ng - rest.to_numpy(float)) < np.abs(
                ng - (rest.to_numpy(float) + fill)
            )
            add = hit & np.isfinite(ng) & excl
            out["Net generation"] = np.where(add, ng + fill, ng)
        else:
            add = np.zeros_like(hit)
        logger.info(
            "%s %d: %s missing in %d h — filled from the measured CAISO Outlook "
            "series (%.3f TWh); Net generation restored in %d h",
            ba_code,
            year,
            col,
            int(hit.sum()),
            float(np.nansum(np.where(hit, fill, 0.0))) / 1e6,
            int(add.sum()),
        )
    return frame if out is None else out
