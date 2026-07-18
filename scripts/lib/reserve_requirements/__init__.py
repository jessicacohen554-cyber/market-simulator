"""Shared contract for the ``reserve-requirements`` clean datatype.

Measured as-enforced hourly reserve requirements per (ISO, reserve location,
product) — the condition-varying requirement channel for the in-LP
energy+reserve co-optimization (see
``data/dictionary/schema/reserve-requirements.schema.yaml``).

Per-ISO parsing lives in sibling modules (``neiso.py``, ...), each of which
registers an :class:`IsoSpec` via :func:`register`; shared code never branches
on the ISO name (``docs/adding-new-data-types.md``). A spec's ``parse`` hook
returns ONE calendar year's tidy schema-shaped frame from the ISO's raw drop
zone; the dispatcher (``scripts/data/curate_reserve_requirements.py``) writes each
(ISO, year) partition through the frozen ``clean_io`` seam.

Canonical product vocabulary (every ISO's native names normalize to these):

* ``10min_spin``  — 10-minute spinning/synchronized reserve
* ``10min_total`` — 10-minute total reserve (spin + non-spin)
* ``30min_total`` — 30-minute total operating reserve
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "reserve-requirements"

#: Canonical tidy column order (matches the schema).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "location",
    "location_id",
    "product",
    "interval_start_utc",
    "interval_start_local",
    "requirement_mw",
)

#: Canonical reserve-product vocabulary.
PRODUCT_VOCAB: frozenset[str] = frozenset({"10min_spin", "10min_total", "30min_total"})


@dataclass(frozen=True)
class IsoSpec:
    """One ISO's registration in the reserve-requirements registry.

    Attributes:
        iso: Canonical ISO name (e.g. ``NEISO``).
        raw_dir: Raw drop zone relative to the raw root (e.g.
            ``NEISO-AS/requirements``).
        parse: ``parse(raw_root, year) -> DataFrame`` returning one calendar
            year's schema-shaped tidy frame (empty frame when the year's raw
            files have not landed).
        years: ``years(raw_root) -> list[int]`` discovering which calendar
            years the ISO's raw drop zone currently covers.
    """

    iso: str
    raw_dir: str
    parse: Callable[[Path, int], pd.DataFrame]
    years: Callable[[Path], list[int]]


REGISTRY: dict[str, IsoSpec] = {}

#: Sibling modules imported by :func:`load_registry`; adding an ISO appends
#: one name here and drops one module next to this file.
_ISO_MODULES: tuple[str, ...] = ("neiso",)


def register(spec: IsoSpec) -> None:
    """Register one ISO's spec (called from its module at import time)."""
    REGISTRY[spec.iso.upper()] = spec


def load_registry() -> dict[str, IsoSpec]:
    """Import every per-ISO module and return the populated registry."""
    for name in _ISO_MODULES:
        importlib.import_module(f"{__name__}.{name}")
    return REGISTRY


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Absolute raw drop zone for ``iso`` under ``raw_root``."""
    return Path(raw_root) / REGISTRY[iso.upper()].raw_dir


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Order/validate a parser's frame into the canonical tidy shape.

    Enforces the canonical column set, the product vocabulary, non-negative
    finite requirement values, and a unique (iso, location, product,
    interval_start_utc) key; sorts by the key. Raises ``ValueError`` on any
    violation so a parser bug never reaches ``write_clean``.
    """
    missing = set(CANONICAL_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"parser frame missing column(s) {sorted(missing)}")
    df = df.loc[:, list(CANONICAL_COLUMNS)].copy()

    bad_products = set(df["product"].unique()) - PRODUCT_VOCAB
    if bad_products:
        raise ValueError(
            f"non-canonical product(s) {sorted(bad_products)}; "
            f"vocabulary is {sorted(PRODUCT_VOCAB)}"
        )
    vals = pd.to_numeric(df["requirement_mw"], errors="raise")
    if not (vals.ge(0).all() and vals.notna().all()):
        raise ValueError("requirement_mw contains negative or missing values")

    key = ["iso", "location", "product", "interval_start_utc"]
    dup = df.duplicated(subset=key)
    if dup.any():
        raise ValueError(
            f"{int(dup.sum())} duplicate key row(s), e.g. "
            f"{df.loc[dup, key].iloc[0].to_dict()}"
        )
    return df.sort_values(key).reset_index(drop=True)
