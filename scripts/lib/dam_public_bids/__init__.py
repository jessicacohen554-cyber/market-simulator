"""Shared contract for the ``dam-public-bids`` clean datatype.

Each ISO's public day-ahead-market bid disclosure (CAISO OASIS Public Bid
Data today; other ISOs additive later) is reconciled onto ONE tidy frame
declared in ``data/dictionary/schema/dam-public-bids.schema.yaml``: one row
per masked resource x operating hour x market product x bid-curve breakpoint
(or self-schedule quantity).

The per-ISO logic lives in sibling modules (``caiso.py``, ...), each of
which registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`. This
keeps new ISOs additive (drop a module, register a spec) per
``docs/adding-new-data-types.md``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import pandas as pd

DATATYPE = "dam-public-bids"

# Canonical tidy column order (matches the schema declaration).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "trade_date",
    "interval_start_utc",
    "resource_type",
    "sc_seq",
    "resource_seq",
    "product",
    "row_kind",
    "step_idx",
    "self_sched_mw",
    "segment_mw",
    "segment_price_usd_per_mwh",
    "curve_type",
)

ROW_KINDS: frozenset[str] = frozenset({"segment", "self_sched"})

#: ISO modules to import on load so their specs self-register.
_ISO_MODULES: tuple[str, ...] = ("caiso",)


def expand_rle(
    frame: pd.DataFrame,
    stop_utc,
    *,
    hour_col: str = "interval_start_utc",
) -> pd.DataFrame:
    """Expand run-length-encoded ``[start, stop)`` rows to one row per hour.

    ISO DAM bid disclosures publish a bid that is unchanged across several
    operating hours as ONE row carrying a start stamp and a stop stamp, not
    as one row per hour: a resource that holds the same curve all day emits
    a single 24-hour row. The datatype's declared grain is one row per
    masked resource x **operating hour** x product x breakpoint, so a parser
    that keys on the start stamp alone silently drops every hour of every
    multi-hour range and biases the surviving population toward
    frequently-rebidding resource-hours (caiso-152; the defect filed at
    caiso-150 §E1). Measured on CAISO GENERATOR EN curves, 2023-01-02:
    18,520 raw rows carry 50,972 real curve-hours.

    Every ISO's disclosure is run-length-encoded this way, so the expansion
    is shared here rather than repeated per ISO module (each parser passes
    its own STOP column).

    Parameters
    ----------
    frame:
        Rows keyed by their RANGE START in ``hour_col`` (tz-aware UTC).
    stop_utc:
        Matching exclusive range end per row, positionally aligned with
        ``frame``. Parsed to tz-aware UTC; a null or non-positive span is
        treated as a single hour (never dropped).
    hour_col:
        Column holding the range start, rewritten in place to the expanded
        per-hour stamp.

    Returns
    -------
    pandas.DataFrame
        ``frame`` with each row repeated once per hour in its range, the
        index reset. Row order is preserved: a range's hours stay adjacent
        and in ascending order.
    """
    if frame.empty:
        return frame.reset_index(drop=True)

    start = pd.DatetimeIndex(
        pd.to_datetime(pd.Series(frame[hour_col]).to_numpy(), utc=True)
    )
    stop = pd.DatetimeIndex(
        pd.to_datetime(pd.Series(stop_utc).to_numpy(), utc=True, format="mixed")
    )
    hours = (stop - start).total_seconds().to_numpy() / 3600.0
    # A missing/degenerate stop stamp means "this hour only" — never a drop.
    span = np.where(np.isfinite(hours), hours, 1.0).astype("int64")
    np.clip(span, 1, None, out=span)
    if not (span > 1).any():
        out = frame.reset_index(drop=True)
        out[hour_col] = start
        return out

    rep = np.repeat(np.arange(len(frame)), span)
    # Offset of each expanded row within its own range: 0, 1, ... span-1.
    ends = np.cumsum(span)
    offs = np.arange(ends[-1]) - np.repeat(ends - span, span)
    out = frame.iloc[rep].reset_index(drop=True)
    out[hour_col] = start[rep] + pd.to_timedelta(offs, unit="h")
    return out


@dataclass(frozen=True)
class IsoSpec:
    """One ISO's raw layout + parser for the dam-public-bids datatype.

    Attributes
    ----------
    iso:
        Canonical ISO name (upper case, e.g. ``"CAISO"``).
    market:
        Market run the disclosure covers (``"DAM"``).
    raw_dir:
        Directory holding the ISO's raw daily files.
    file_glob:
        Glob (relative to ``raw_dir``) matching one raw file per trade date.
    parse_day:
        Callable mapping one raw daily file to a schema-shaped DataFrame
        (canonical columns, one trade date).
    """

    iso: str
    market: str
    raw_dir: Path
    file_glob: str
    parse_day: Callable[[Path], pd.DataFrame]


REGISTRY: dict[str, IsoSpec] = {}


def register(spec: IsoSpec) -> None:
    """Register an ISO spec (called by each ISO module at import time)."""
    REGISTRY[spec.iso] = spec


def load_specs(isos: Iterable[str] | None = None) -> list[IsoSpec]:
    """Import ISO modules and return registered specs (optionally filtered)."""
    for mod in _ISO_MODULES:
        importlib.import_module(f"{__name__}.{mod}")
    if isos is None:
        return list(REGISTRY.values())
    missing = sorted(set(i.upper() for i in isos) - REGISTRY.keys())
    if missing:
        raise KeyError(
            f"no dam-public-bids spec registered for {missing}; "
            f"known: {sorted(REGISTRY)}"
        )
    return [REGISTRY[i.upper()] for i in isos]
