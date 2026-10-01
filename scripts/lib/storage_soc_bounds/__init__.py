"""Shared contract for the ``storage-soc-bounds`` clean datatype.

Participant-submitted storage end-of-hour state-of-charge bid bounds, one row
per (masked resource, bid hour), reconciled onto the tidy schema in
``data/dictionary/schema/storage-soc-bounds.schema.yaml``. REPORT-ONLY: the
bound is a conduct parameter with no forward driver, so it is never a solve
input (rule 13; R-CAISO-28 FINDING section 1 point 4).

Per-ISO logic lives in sibling modules (``caiso.py``, ...), each registering an
:class:`IsoSpec` via :func:`register`; shared code never branches on the ISO
name, per ``docs/adding-new-data-types.md``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "storage-soc-bounds"

#: Canonical tidy column order (matches the schema).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "market",
    "resource_id",
    "sc_id",
    "min_eoh_soc_mwh",
    "max_eoh_soc_mwh",
    "en_min_mw",
    "en_max_mw",
    "is_storage_s1",
)


@dataclass(frozen=True)
class IsoSpec:
    """One ISO's storage-SOC-bound intake registration.

    Attributes
    ----------
    iso:
        Canonical ISO code (e.g. ``"CAISO"``).
    parse:
        ``parse(raw_root, year) -> pd.DataFrame`` returning the canonical tidy
        frame for one local trade-date year (empty when the raw is absent).
    years:
        ``years(raw_root) -> list[int]`` — the years the raw drop covers.
    source:
        Free-text provenance embedded in the clean parquet metadata.
    """

    iso: str
    parse: Callable[[Path, int], pd.DataFrame]
    years: Callable[[Path], list[int]]
    source: str


REGISTRY: dict[str, IsoSpec] = {}

#: Sibling modules that self-register on import.
_ISO_MODULES: tuple[str, ...] = ("caiso",)


def register(spec: IsoSpec) -> None:
    """Register one ISO's intake spec (called by the sibling ISO modules)."""
    REGISTRY[spec.iso.upper()] = spec


def load_registry() -> dict[str, IsoSpec]:
    """Import every ISO module so its spec lands in :data:`REGISTRY`."""
    for mod in _ISO_MODULES:
        importlib.import_module(f"{__name__}.{mod}")
    return REGISTRY
