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
