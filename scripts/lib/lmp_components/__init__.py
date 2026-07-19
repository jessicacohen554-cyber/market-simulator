"""Shared contract for the ``lmp-components`` clean datatype.

Verbatim per-node hourly LMP component record (total LMP + published
congestion MCC / loss MLC components) per
``data/dictionary/schema/lmp-components.schema.yaml``. First ISO: MISO's
daily ex-post market reports, staged per scope decision D6 (see
``data/raw/lmp-components/README.md``). Primary consumer: the miso-76
marginal delivery-factor (loss) surface derive
(``scripts/data/derive_miso_loss_surface.py``; charter
``docs/handoffs/miso-nc-price-separation-design-2026-07.md`` §4).

The per-ISO logic lives in sibling modules (``miso.py``, ...), each of
which registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`, so new
ISOs are additive (drop a module, register a spec) per
``docs/adding-new-data-types.md``.

An ISO spec supplies a ``parse`` hook
``(raw_dir: Path, market: str, year: int) -> DataFrame`` returning a frame
with exactly :data:`CANONICAL_COLUMNS`; the curation script partitions and
writes it through ``clean_io.write_clean``. Unlike most datatypes, an ISO's
``raw_subdir`` here is **RAW_DIR-relative** (not datatype-dir-relative) so a
spec may point at a shared staging — MISO's component rows live inside the
committed D6 hub holding ``data/raw/lmp-data/MISO`` rather than being
duplicated under ``data/raw/lmp-components`` (see that README's rationale).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "lmp-components"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "market",
    "node",
    "node_type",
    "interval_start_utc",
    "interval_start_est",
    "lmp_usd_per_mwh",
    "mcc_usd_per_mwh",
    "mlc_usd_per_mwh",
)

# Market runs every ISO module may emit.
MARKETS: tuple[str, ...] = ("da", "rt")

# Cross-node MEC-identity tolerance (USD/MWh): components are published to
# 2 decimals, so LMP - MCC - MLC may differ across nodes by accumulated
# rounding of the three addends (±0.005 each) — beyond ~3 cents indicates a
# corrupted staging row, not rounding.
MEC_IDENTITY_TOLERANCE_USD_MWH: float = 0.03


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's LMP-component source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and clean partition.
    raw_subdir:
        Subdirectory of ``data/raw`` (RAW_DIR-relative — module docstring)
        holding the ISO's staged raw files.
    parse:
        Reader ``(raw_dir: Path, market: str, year: int) -> DataFrame``
        returning exactly :data:`CANONICAL_COLUMNS`; must return an empty
        frame (same columns) when the (market, year) staging is absent.
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


def mec_identity_spread(df: pd.DataFrame) -> pd.Series:
    """Per-interval cross-node spread of the implied MEC (LMP - MCC - MLC).

    The system marginal energy component is common to every node within one
    (market, interval); its cross-node max-min spread should stay within
    :data:`MEC_IDENTITY_TOLERANCE_USD_MWH` (2-decimal publication rounding).
    Returns the spread indexed by ``interval_start_utc`` (intervals whose
    rows are all-null are dropped) for the caller to threshold/report —
    curation warns loudly on violations rather than silently accepting a
    corrupted staging row.
    """
    mec = df["lmp_usd_per_mwh"] - df["mcc_usd_per_mwh"] - df["mlc_usd_per_mwh"]
    frame = pd.DataFrame(
        {"interval_start_utc": df["interval_start_utc"], "mec": mec}
    ).dropna(subset=["mec"])
    grouped = frame.groupby("interval_start_utc")["mec"]
    return grouped.max() - grouped.min()
