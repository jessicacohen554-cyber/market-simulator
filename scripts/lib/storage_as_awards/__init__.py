"""Shared contract for the ``storage-as-awards`` clean datatype.

The measured ancillary-service award MW held by the storage fleet — the
resource-type-resolved counterpart of ``ancillary-services`` (system
requirement / total procurement). Each ISO's published award layout is
reconciled onto ONE tidy frame declared in
``data/dictionary/schema/storage-as-awards.schema.yaml``.

Per-ISO logic lives in sibling modules (``caiso.py``, ...), each of which
registers an :class:`IsoSpec` via :func:`register`. Shared code never branches
on the ISO name — it looks the spec up in :data:`REGISTRY`; new ISOs are
additive (drop a module, register a spec), per ``docs/adding-new-data-types.md``.

Product vocabulary is the same reconciled taxonomy as ``ancillary-services``:
``reg_up`` / ``reg_down`` / ``spin`` / ``nonspin``. Resource classes:
``battery`` (standalone + co-located storage) and ``hybrid``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "storage-as-awards"

#: Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "interval_start_utc",
    "interval_start_local",
    "iso",
    "resource_class",
    "market",
    "product",
    "award_mw",
)

#: Canonical AS product vocabulary (shared with `ancillary-services`).
PRODUCT_VOCAB: frozenset[str] = frozenset({"reg_up", "reg_down", "spin", "nonspin"})

#: Canonical storage resource-class vocabulary.
RESOURCE_CLASS_VOCAB: frozenset[str] = frozenset({"battery", "hybrid"})


@dataclass(frozen=True)
class IsoSpec:
    """One ISO's storage-AS-award intake registration.

    Attributes
    ----------
    iso:
        Canonical ISO code (e.g. ``"CAISO"``).
    parse:
        ``parse(raw_root) -> pd.DataFrame`` returning the canonical tidy frame
        for every year the ISO's raw drop covers (empty frame when the raw
        files have not landed).
    years:
        ``years(raw_root) -> list[int]`` — the calendar years the raw drop
        covers, used to partition ``write_clean(..., year=…)`` per year.
    source:
        Free-text provenance embedded in the clean parquet metadata.
    """

    iso: str
    parse: Callable[[Path], pd.DataFrame]
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
