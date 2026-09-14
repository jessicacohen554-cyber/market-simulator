"""Shared contract for the ``confirmed-retirements`` clean datatype.

Each ISO's binding retirement instruments (PJM deactivation acceptances, MISO
Attachment Y approvals, NYISO deactivation notices, ISO-NE cleared de-list bids,
CAISO SWRCB/CPUC orders, ERCOT NSO acceptances, plus cross-ISO federal consent
decrees and state statutes) are curated onto ONE tidy frame declared in
``data/dictionary/schema/confirmed-retirements.schema.yaml``.

The per-ISO logic lives in sibling modules (``pjm.py``, ``ercot.py``, ...), each
of which registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`. This keeps
new ISOs additive (drop a module, register a spec) and lets parallel intake
sessions work without touching a shared file, mirroring
``scripts/lib/capacity_deliverability``.

Retrieval sessions produce one hand-curated CSV per ISO at
``data/raw/confirmed-retirements/<iso>.csv`` with exactly the canonical columns
(the sources are PDFs / web postings, so curation is human-in-the-loop by
design; the provenance columns are what keep it reproducible per rule 13).
:func:`parse_unified_csv` is the generic reader every ISO uses unless its spec
supplies a custom ``parse`` hook.

This datatype is **forecast-forward only**: it feeds the confirmed-exit injector
(``market_sim.data.confirmed_retirements`` → ``model.capacity.apply_confirmed_exits``).
Historical exits stay with the EIA-860 vintage snapshot + within-window retiree
build; nothing here is a backcast device.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "confirmed-retirements"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "plant_id",
    "generator_id",
    "unit_name",
    "capacity_mw",
    "exit_year",
    "exit_month",
    "confirmation_class",
    "instrument_id",
    "instrument",
    "instrument_date",
    "superseded",
    "superseding_instrument",
    "superseding_instrument_date",
    "source_url",
    "source_doc",
    "accessed",
    "notes",
)

# Closed confirmation-class vocabulary. ``announced``/``intended`` is
# deliberately NOT a member: an EIA-860 planned date is not an instrument, so it
# stays with the economic-retirement screen (plan §2.3, rule 13).
CONFIRMATION_CLASS_VOCAB: frozenset[str] = frozenset(
    {
        "rto_deactivation",
        "consent_decree",
        "statute",
        "regulatory_order",
        "rmr_end",
    }
)

_STRING_COLS = (
    "iso",
    "generator_id",
    "unit_name",
    "confirmation_class",
    "instrument_id",
    "instrument",
    "superseding_instrument",
    "source_url",
    "source_doc",
    "notes",
)
_INT_COLS = ("plant_id", "exit_year", "exit_month")
_FLOAT_COLS = ("capacity_mw",)
_DATETIME_COLS = ("instrument_date", "accessed", "superseding_instrument_date")
_BOOL_COLS = ("superseded",)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's confirmed-retirement source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (e.g. ``"PJM"``, ``"ERCOT"``, ``"MISO"``, ``"NYISO"``, ``"NEISO"``,
        ``"CAISO"``).
    class_aliases:
        Map of native confirmation-class label (lower-cased) -> canonical class,
        so a retrieval CSV may carry either the native or canonical name.
    source_note:
        One-line description of the ISO's binding-instrument source, for
        reviewers (documentation only).
    parse:
        Optional custom reader ``(csv_path: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    class_aliases: dict[str, str] = field(default_factory=dict)
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
    """Path of an ISO's raw confirmed-retirements CSV extract."""
    return raw_root / DATATYPE / f"{iso.lower()}.csv"


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order.

    Missing optional columns are filled with nulls so a source that omits an
    optional field still yields a schema-shaped frame. Integer columns that
    allow nulls (``exit_month``) become pandas nullable ``Int64``; the
    non-nullable ``plant_id`` / ``exit_year`` are checked downstream by
    :func:`scripts.lib.clean_io.validate_df`.
    """
    out = df.copy()
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in _STRING_COLS:
        out[col] = out[col].astype("string").str.strip()
    for col in _INT_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("Int64")
    for col in _FLOAT_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    for col in _DATETIME_COLS:
        out[col] = pd.to_datetime(out[col], errors="coerce")
    for col in _BOOL_COLS:
        # Blank/absent supersession defaults to False (a live row).
        out[col] = (
            out[col].map(_coerce_bool).astype("boolean").fillna(False).astype(bool)
        )
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(
        ["iso", "plant_id", "generator_id", "instrument_id"]
    ).reset_index(drop=True)
    return out


def _coerce_bool(value: object) -> object:
    """Coerce a CSV cell to a bool, leaving unknown/blank as ``pd.NA``."""
    if value is None or (isinstance(value, float) and value != value):
        return pd.NA
    s = str(value).strip().lower()
    if s in ("", "na", "nan", "none"):
        return pd.NA
    if s in ("true", "t", "yes", "y", "1"):
        return True
    if s in ("false", "f", "no", "n", "0"):
        return False
    return pd.NA


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary / value rules before the frame is written.

    Complements :func:`scripts.lib.clean_io.validate_df` (dtypes, nulls, naming)
    with the value-level rules the schema cannot express: the closed
    confirmation-class vocabulary, a valid month range, and that a superseded
    row cites its counter-instrument. Raises :class:`ValueError` on any
    violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_class = sorted(
        set(df["confirmation_class"].dropna()) - CONFIRMATION_CLASS_VOCAB
    )
    if bad_class:
        problems.append(f"confirmation_class not in vocab: {bad_class}")
    months = pd.to_numeric(df["exit_month"], errors="coerce").dropna()
    if not months.between(1, 12).all():
        problems.append("exit_month has value(s) outside 1-12")
    superseded_no_cite = df["superseded"].astype(bool) & (
        df["superseding_instrument"].isna()
        | (df["superseding_instrument"].astype("string").str.len() == 0)
    )
    if bool(superseded_no_cite.any()):
        problems.append(
            f"{int(superseded_no_cite.sum())} superseded row(s) miss "
            "superseding_instrument"
        )
    dup = df.duplicated(
        subset=["iso", "plant_id", "generator_id", "instrument_id"], keep=False
    )
    if bool(dup.any()):
        problems.append(f"{int(dup.sum())} duplicate (unit, instrument) key row(s)")
    if problems:
        raise ValueError(
            "confirmed-retirements tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(csv_path: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw>/confirmed-retirements/<iso>.csv`` with the canonical columns
    (as produced by the retrieval prompts). Native confirmation-class labels are
    mapped through ``spec.class_aliases``. Returns an empty (but correctly-shaped)
    frame when the CSV is absent or has no data rows, so :func:`curate` can skip
    an ISO whose registry has not landed yet (DATA NEEDED).
    """
    if not csv_path.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv_path, dtype=str, comment="#")
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw = raw.dropna(how="all")
    if raw.empty:
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    if "confirmation_class" in raw.columns and spec.class_aliases:
        raw["confirmation_class"] = (
            raw["confirmation_class"]
            .str.strip()
            .str.lower()
            .map(lambda c: spec.class_aliases.get(c, c))
        )
    raw["iso"] = spec.iso
    return finalize(raw)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw CSV into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/confirmed_retirements/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_csv_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
