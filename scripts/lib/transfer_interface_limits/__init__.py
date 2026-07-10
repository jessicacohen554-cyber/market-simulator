"""Shared contract for the ``transfer-interface-limits`` clean datatype.

Measured hourly transmission-interface transfer limits (and the measured
actual transfers, kept for crosswalk diagnostics only) reconciled onto the
fixed non-leap 8760-hour ISO-local model clock, per the schema in
``data/dictionary/schema/transfer-interface-limits.schema.yaml``.

The per-ISO logic lives in sibling modules (``pjm.py``, ...), each of which
registers an :class:`IsoSpec` via :func:`register`. Shared code never branches
on the ISO name — it looks the spec up in :data:`REGISTRY`, so new ISOs are
additive (drop a module, register a spec) per ``docs/adding-new-data-types.md``.

An ISO spec supplies (a) how to find its raw files under ``data/raw`` and
(b) a ``parse`` hook returning a tidy frame with columns
``[interface, ts_utc, limit_mw, transfer_mw]`` (``ts_utc`` tz-aware UTC).
The shared :func:`to_model_clock` then does the clock reconciliation every ISO
shares: convert to the ISO's local wall clock, drop Feb 29, merge the DST
fall-back repeat by clock-hour group-by, and densify to all 8760 hours by
filling the single spring-forward hour from its neighbours
(``n_source_rows = 0`` flags the fill).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

DATATYPE = "transfer-interface-limits"

# Hours on the fixed non-leap model dispatch clock.
HOURS_PER_YEAR = 8760

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "interface",
    "hour",
    "interval_start_local",
    "limit_mw",
    "transfer_mw",
    "n_source_rows",
)

# Columns a spec's parse hook must return (ts_utc tz-aware UTC).
PARSED_COLUMNS: tuple[str, ...] = ("interface", "ts_utc", "limit_mw", "transfer_mw")


@dataclass(frozen=True)
class IsoSpec:
    """One ISO's raw layout + parser for this datatype.

    Attributes
    ----------
    iso:
        ISO/RTO code (upper case, e.g. ``"PJM"``).
    tz:
        IANA timezone of the ISO's local clock (e.g. ``"America/New_York"``
        for PJM's EPT).
    raw_subdir:
        Directory under ``data/raw`` holding the raw files.
    raw_glob:
        Glob (within ``raw_subdir``) matching this ISO's raw files.
    parse:
        Hook ``(path) -> DataFrame`` returning the tidy parsed columns
        (:data:`PARSED_COLUMNS`) for one raw file.
    """

    iso: str
    tz: str
    raw_subdir: str
    raw_glob: str
    parse: Callable[[Path], pd.DataFrame]


REGISTRY: dict[str, IsoSpec] = {}

# Sibling modules auto-imported by load_specs(); each registers its spec.
_ISO_MODULES: tuple[str, ...] = ("pjm",)


def register(spec: IsoSpec) -> IsoSpec:
    """Register an ISO spec (called at import time by the per-ISO modules)."""
    REGISTRY[spec.iso.upper()] = spec
    return spec


def load_specs() -> dict[str, IsoSpec]:
    """Import every per-ISO module and return the populated registry."""
    for mod in _ISO_MODULES:
        importlib.import_module(f"{__name__}.{mod}")
    return REGISTRY


def to_model_clock(parsed: pd.DataFrame, spec: IsoSpec, year: int) -> pd.DataFrame:
    """Reconcile one year's parsed UTC rows onto the non-leap model clock.

    Converts ``ts_utc`` to the ISO's local wall clock, keeps only ``year``,
    drops Feb 29, group-by-means each ``(interface, month, day, hour)`` (which
    merges the DST fall-back repeat), maps onto the 0-8759 fixed non-leap
    hour index, and densifies: the spring-forward wall-clock hour that never
    occurs locally is filled per interface from its neighbouring hours
    (``limit_mw`` interpolated, ``transfer_mw`` left null,
    ``n_source_rows = 0``). Returns a schema-shaped frame sorted by
    ``(interface, hour)``.
    """
    local = parsed["ts_utc"].dt.tz_convert(spec.tz)
    df = parsed.assign(
        yr=local.dt.year, month=local.dt.month, day=local.dt.day, hr=local.dt.hour
    )
    df = df[(df["yr"] == year) & ~((df["month"] == 2) & (df["day"] == 29))]
    if df.empty:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))

    grouped = (
        df.groupby(["interface", "month", "day", "hr"])
        .agg(
            limit_mw=("limit_mw", "mean"),
            transfer_mw=("transfer_mw", "mean"),
            n_source_rows=("ts_utc", "nunique"),
        )
        .reset_index()
    )

    # Map (month, day, hour) onto the 0-8759 non-leap clock (2023 is any
    # non-leap template year — only month/day/hour structure is used).
    calendar = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    pos = pd.Series(
        np.arange(HOURS_PER_YEAR, dtype="int64"),
        index=pd.MultiIndex.from_arrays(
            [calendar.month, calendar.day, calendar.hour],
            names=["month", "day", "hr"],
        ),
    )
    key = pd.MultiIndex.from_frame(grouped[["month", "day", "hr"]])
    grouped["hour"] = pos.reindex(key).to_numpy()

    # Densify per interface: every hour 0-8759 gets a row; the (at most one)
    # missing spring-forward hour is filled by linear interpolation of
    # limit_mw between its neighbours, flagged n_source_rows = 0.
    full_index = pd.MultiIndex.from_product(
        [grouped["interface"].unique(), np.arange(HOURS_PER_YEAR, dtype="int64")],
        names=["interface", "hour"],
    )
    dense = (
        grouped.set_index(["interface", "hour"])
        .reindex(full_index)
        .reset_index()
        .sort_values(["interface", "hour"], ignore_index=True)
    )
    dense["n_source_rows"] = dense["n_source_rows"].fillna(0).astype("int64")
    dense["limit_mw"] = (
        dense.groupby("interface")["limit_mw"]
        .transform(lambda s: s.interpolate(limit_direction="both"))
        .astype("float64")
    )

    dense["iso"] = spec.iso.upper()
    hr = dense["hour"].to_numpy()
    dense["interval_start_local"] = pd.to_datetime(
        {
            "year": year,
            "month": calendar.month.to_numpy()[hr],
            "day": calendar.day.to_numpy()[hr],
            "hour": calendar.hour.to_numpy()[hr],
        }
    )
    return dense[list(CANONICAL_COLUMNS)]
