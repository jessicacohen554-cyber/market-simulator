"""Shared contract for the ``transfer-constraint-binding`` clean datatype.

Measured binding record (posted shadow prices + the live demand-curve
breakpoints in force) for an ISO's published inter-regional transfer
constraints, per ``data/dictionary/schema/transfer-constraint-binding.schema.yaml``.
First ISO: MISO's Regional Directional Transfer (RDT) from the public
``{da,rt}_pbc`` market reports. This is a backcast VALIDATION series, never
an LP input (rule 13: when a constraint binds is a dispatch outcome).

The per-ISO logic lives in sibling modules (``miso.py``, ...), each of which
registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`, so new
ISOs are additive (drop a module, register a spec) per
``docs/adding-new-data-types.md``.

An ISO spec supplies a ``parse`` hook
``(raw_dir: Path, market: str, year: int) -> DataFrame`` returning a frame
with exactly :data:`CANONICAL_COLUMNS`; the curation script partitions and
writes it through ``clean_io.write_clean``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "transfer-constraint-binding"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "market",
    "constraint",
    "direction",
    "interval_start_utc",
    "interval_start_est",
    "shadow_price_usd_mwh",
    "curvetype",
    "bp1_pct",
    "pc1_usd_mwh",
    "bp2_pct",
    "pc2_usd_mwh",
    "bp3_pct",
    "pc3_usd_mwh",
    "bp4_pct",
    "pc4_usd_mwh",
    "override",
    "override_reason",
)

# Market runs every ISO module may emit.
MARKETS: tuple[str, ...] = ("da", "rt")


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's binding-record source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and clean partition.
    raw_subdir:
        Subdirectory of ``data/raw/transfer-constraint-binding`` holding the
        ISO's consolidated raw files.
    parse:
        Reader ``(raw_dir: Path, market: str, year: int) -> DataFrame``
        returning exactly :data:`CANONICAL_COLUMNS`; must return an empty
        frame (same columns) when the (market, year) raw file is absent.
    """

    iso: str
    raw_subdir: str
    parse: Callable[[Path, str, int], pd.DataFrame]


# The registry every ISO module populates at import time.
REGISTRY: dict[str, IsoSpec] = {}

# ISO submodules to import so their register() calls run. Missing modules
# (an ISO not yet implemented) are skipped, so intake waves land
# independently.
_ISO_MODULES: tuple[str, ...] = ("miso",)
_loaded = False


def register(spec: IsoSpec) -> IsoSpec:
    """Register an :class:`IsoSpec` under its ISO label. Returns the spec."""
    REGISTRY[spec.iso.upper()] = spec
    return spec


def load_specs() -> dict[str, IsoSpec]:
    """Import every ISO submodule once and return the populated registry."""
    global _loaded
    if not _loaded:
        for mod in _ISO_MODULES:
            try:
                importlib.import_module(f"{__name__}.{mod}")
            except ImportError:
                continue
        _loaded = True
    return REGISTRY
