"""Shared contract for the ``nuclear-license-status`` clean datatype.

Each ISO's nuclear fleet forward-lifetime rows (NRC operating-license expiries,
Subsequent License Renewal status, announced power uprates, restart pathways, and
confirmed-retirement cross-references) are curated onto ONE tidy frame declared in
``data/dictionary/schema/nuclear-license-status.schema.yaml``.

The per-ISO logic lives in sibling modules (``pjm.py``, ``miso.py``, ...), each of
which registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`, so new ISOs
stay additive (drop a module, register a spec) and parallel intake sessions never
touch a shared file. This mirrors ``scripts/lib/confirmed_retirements`` and
``scripts/lib/capacity_deliverability``.

Retrieval sessions produce one hand-curated CSV per ISO at
``data/raw/nuclear-license-status/<iso>.csv`` with exactly the canonical columns.
The sources are NRC web pages / licensee filings / state dockets, so curation is
human-in-the-loop by design; the provenance columns (``source_url``,
``*_instrument``, ``accessed``) are what keep it reproducible per rule 13.
:func:`parse_unified_csv` is the generic reader every ISO uses.

This datatype is a **DATA registry only**. Nothing in the solve path consumes it
yet — the forward-channel design (how a license expiry / SLR / restart / uprate
should enter the forecast) is
``docs/handoffs/ff-g5-nuclear-registry-2026-07.md``. A read-only loader stub lives
at ``src/market_sim/data/nuclear_license.py`` for tests / future wiring.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "nuclear-license-status"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "plant_name",
    "unit",
    "eia_plant_id",
    "capacity_mw",
    "nrc_docket",
    "license_issued_date",
    "current_license_expiry",
    "license_stage",
    "license_instrument",
    "slr_status",
    "slr_docket",
    "slr_instrument",
    "slr_instrument_date",
    "announced_uprate_mw",
    "uprate_status",
    "uprate_instrument",
    "restart_status",
    "restart_target_year",
    "restart_instrument",
    "retirement_announcement",
    "confirmed_retirement_ref",
    "source_url",
    "source_doc",
    "accessed",
    "notes",
)

# Closed controlled vocabularies. A value outside these fails curation
# (validate_tidy) rather than silently entering the registry.
LICENSE_STAGE_VOCAB: frozenset[str] = frozenset(
    {"original", "renewed_60", "slr_granted_80"}
)
SLR_STATUS_VOCAB: frozenset[str] = frozenset(
    {"granted", "under_review", "announced_intent", "none"}
)
UPRATE_STATUS_VOCAB: frozenset[str] = frozenset(
    {"approved", "under_review", "announced_intent", "none"}
)
RESTART_STATUS_VOCAB: frozenset[str] = frozenset(
    {"returned", "in_progress", "planned", "none"}
)

_STRING_COLS = (
    "iso",
    "plant_name",
    "unit",
    "nrc_docket",
    "license_stage",
    "license_instrument",
    "slr_status",
    "slr_docket",
    "slr_instrument",
    "uprate_status",
    "uprate_instrument",
    "restart_status",
    "restart_instrument",
    "retirement_announcement",
    "confirmed_retirement_ref",
    "source_url",
    "source_doc",
    "notes",
)
_INT_COLS = ("eia_plant_id", "restart_target_year")
_FLOAT_COLS = ("capacity_mw", "announced_uprate_mw")
_DATETIME_COLS = (
    "license_issued_date",
    "current_license_expiry",
    "slr_instrument_date",
    "accessed",
)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's nuclear-license-status source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (``"PJM"``, ``"ERCOT"``, ``"MISO"``, ``"NYISO"``, ``"NEISO"``,
        ``"CAISO"``).
    source_note:
        One-line description of the ISO's nuclear-fleet source, for reviewers
        (documentation only).
    parse:
        Optional custom reader ``(csv_path: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    source_note: str = ""
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = None


# The registry every ISO module populates at import time.
REGISTRY: dict[str, IsoSpec] = {}

# ISO submodules to import so their register() calls run. Missing modules (an
# ISO not yet implemented) are skipped, so intake waves land independently.
_ISO_MODULES: tuple[str, ...] = (
    "ercot",
    "pjm",
    "miso",
    "nyiso",
    "neiso",
    "caiso",
    "spp",  # registered 2026-09-06 (lane SPP-20)
    "nwpp",  # registered 2026-09-14 (lane NWPP-20)
)
_loaded = False


def register(spec: IsoSpec) -> IsoSpec:
    """Register an :class:`IsoSpec` under its ISO label. Returns the spec."""
    REGISTRY[spec.iso.upper()] = spec
    return spec


def load_registry() -> dict[str, IsoSpec]:
    """Import every available ISO module (idempotent) and return the registry."""
    global _loaded
    if not _loaded:
        for name in _ISO_MODULES:
            try:
                importlib.import_module(f"{__name__}.{name}")
            except ModuleNotFoundError:
                continue  # ISO not implemented yet — additive by design.
        _loaded = True
    return REGISTRY


def raw_csv_for(iso: str, raw_root: Path) -> Path:
    """Path of an ISO's raw nuclear-license-status CSV extract."""
    return raw_root / DATATYPE / f"{iso.lower()}.csv"


def _coerce_int_series(series: pd.Series) -> pd.Series:
    """Numeric -> pandas nullable Int64 (blank/NA preserved)."""
    return pd.to_numeric(series, errors="coerce").astype("Int64")


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order.

    Missing optional columns are filled with nulls so a source that omits an
    optional field still yields a schema-shaped frame. Integer columns that
    allow nulls (``restart_target_year``) become pandas nullable ``Int64``; the
    non-nullable ``eia_plant_id`` is checked downstream by
    :func:`scripts.lib.clean_io.validate_df`.
    """
    out = df.copy()
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in _STRING_COLS:
        out[col] = out[col].astype("string").str.strip()
    for col in _INT_COLS:
        out[col] = _coerce_int_series(out[col])
    for col in _FLOAT_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    for col in _DATETIME_COLS:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(["iso", "eia_plant_id", "unit"]).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary / value rules before the frame is written.

    Complements :func:`scripts.lib.clean_io.validate_df` (dtypes, nulls, naming)
    with the value-level rules the schema cannot express: the four closed
    controlled vocabularies (license_stage, slr_status, uprate_status,
    restart_status), the (unit, plant) key uniqueness, and the internal
    consistency that a ``granted`` SLR implies the ``slr_granted_80`` stage.
    Raises :class:`ValueError` on any violation; returns ``df`` on success.
    """
    problems: list[str] = []

    def _bad(col: str, vocab: frozenset[str], *, drop_none: bool = False) -> None:
        vals = df[col].dropna()
        vals = vals[vals.astype(str).str.strip() != ""]
        seen = set(vals.astype(str).str.strip())
        if drop_none:
            seen -= {"none"}
        bad = sorted(seen - vocab)
        if bad:
            problems.append(f"{col} not in vocab: {bad}")

    _bad("license_stage", LICENSE_STAGE_VOCAB)
    _bad("slr_status", SLR_STATUS_VOCAB)
    _bad("uprate_status", UPRATE_STATUS_VOCAB)
    _bad("restart_status", RESTART_STATUS_VOCAB)

    # A granted SLR must be reflected in the license stage (one fact, two
    # columns — keep them consistent so a downstream consumer can trust either).
    granted = df["slr_status"].astype("string").str.strip() == "granted"
    stage = df["license_stage"].astype("string").str.strip()
    mismatch = granted & (stage != "slr_granted_80")
    if bool(mismatch.any()):
        problems.append(
            f"{int(mismatch.sum())} row(s) with slr_status=granted but "
            "license_stage != slr_granted_80"
        )

    months = pd.to_numeric(df["restart_target_year"], errors="coerce").dropna()
    if not months.empty and not (months.between(2000, 2100)).all():
        problems.append("restart_target_year has value(s) outside 2000-2100")

    dup = df.duplicated(subset=["iso", "eia_plant_id", "unit"], keep=False)
    if bool(dup.any()):
        problems.append(f"{int(dup.sum())} duplicate (iso, plant, unit) key row(s)")

    if problems:
        raise ValueError(
            "nuclear-license-status tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(csv_path: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw>/nuclear-license-status/<iso>.csv`` with the canonical columns
    (as produced by the retrieval prompts). Returns an empty (but correctly-
    shaped) frame when the CSV is absent or has no data rows, so :func:`curate`
    can skip an ISO whose registry has not landed yet (DATA NEEDED).
    """
    if not csv_path.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv_path, dtype=str, comment="#")
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw = raw.dropna(how="all")
    if raw.empty:
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw["iso"] = spec.iso
    return finalize(raw)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw CSV into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/nuclear_license_status/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_csv_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
