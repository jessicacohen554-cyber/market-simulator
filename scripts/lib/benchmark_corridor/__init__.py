"""Shared contract for the ``benchmark-corridor`` clean datatype.

External forecast-corridor anchors — 2030/2035/2040 capacity mix, generation
(energy) mix, and power-sector CO2 by ISO/region — reconciled from every
external outlook (EIA AEO2025 regional electricity tables, NREL Standard
Scenarios, ISO planning documents) onto ONE tidy frame declared in
``data/dictionary/schema/benchmark-corridor.schema.yaml``.

These are the FC-5 external-corridor evidence base of the forecast determination
rubric (``docs/forecast-determination-rubric.md`` §2 FC-5 / §6). **Context,
never a fit target** (CLAUDE.md rule 13): nothing in the model is ever tuned
toward a value curated here.

Per-source logic lives in sibling modules — :mod:`aeo` (the one fetchable
source, with a custom API parser), :mod:`stdscen` and :mod:`iso_planning` (the
manual-download sources, which share the generic unified-CSV reader). Each
module registers a :class:`SourceSpec` via :func:`register`; shared code never
branches on the source name — it looks the spec up in :data:`REGISTRY`. This
keeps new sources additive (drop a module / add a ``register`` call) and lets
parallel intake sessions add sources without touching a shared file, per
``docs/adding-new-data-types.md``.

A manual-download source produces one *unified CSV* under
``data/raw/benchmark-corridor/<raw_subdir>/<raw_subdir>.csv`` with exactly the
:data:`CANONICAL_COLUMNS`; :func:`parse_unified_csv` is the generic reader every
such source uses unless its spec supplies a custom ``parse`` hook (AEO does).
A source whose raw file has not landed yet parses to an empty frame and is
reported as a *missing source*, never a placeholder value (rule 5).
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from scripts.lib.clean_io import paths

DATATYPE = "benchmark-corridor"

# Canonical tidy column order (matches the schema key + value + provenance
# columns in benchmark-corridor.schema.yaml).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "source",
    "iso",
    "region",
    "vintage",
    "scenario",
    "target_year",
    "quantity",
    "tech",
    "value",
    "unit",
    "source_doc",
    "source_page",
    "note",
)

# The FC-5 "metric" axis.
QUANTITY_VOCAB: frozenset[str] = frozenset({"capacity", "generation", "co2"})

# Canonical technology / fuel vocabulary (a UNION covering AEO's granularity and
# the ISO-document / model granularity). `renewables` is a source's renewable
# aggregate; `total` is a capacity/generation grand total or the system CO2
# total.
TECH_VOCAB: frozenset[str] = frozenset(
    {
        "coal",
        "gas",
        "gas_cc",
        "gas_ct",
        "gas_st",
        "oil",
        "nuclear",
        "hydro",
        "wind",
        "offshore_wind",
        "solar",
        "solar_thermal",
        "geothermal",
        "biomass",
        "municipal_waste",
        "storage",
        "pumped_storage",
        "hydrogen",
        "fuel_cells",
        "distributed_gen",
        "renewables",
        "other",
        "total",
    }
)

# ISO/region label an intake row may map onto. "national" is the US/system grain.
ISO_VOCAB: frozenset[str] = frozenset(
    {"ERCOT", "PJM", "MISO", "NYISO", "NEISO", "CAISO", "national"}
)

# Per-ISO source modules registered on import. Add a source: create the module,
# call register() in it, and add its name here (the ONLY shared-file edit).
_SOURCE_MODULES: tuple[str, ...] = ("aeo", "stdscen", "iso_planning")


@dataclass(frozen=True)
class SourceSpec:
    """One external benchmark source's intake declaration.

    ``parse`` maps this source's raw directory to a canonical-schema frame
    (defaulting to :func:`parse_unified_csv`, which reads a committed unified
    CSV). ``fetchable`` records whether the raw lands by an in-repo fetch
    (AEO) or a manual download (everything else) — surfaced in the raw README
    and the FF-0F deliverable, never a guess.
    """

    source: str
    raw_subdir: str
    isos: tuple[str, ...]
    vintage: str
    description: str
    fetchable: bool = False
    parse: Callable[[Path], pd.DataFrame] | None = None
    citation: str = ""


REGISTRY: dict[str, SourceSpec] = {}


def register(spec: SourceSpec) -> SourceSpec:
    """Register a source spec under its ``source`` id (idempotent per import)."""
    REGISTRY[spec.source] = spec
    return spec


def load_registry() -> dict[str, SourceSpec]:
    """Import every per-source module so it registers, then return the registry."""
    for name in _SOURCE_MODULES:
        importlib.import_module(f"{__name__}.{name}")
    return REGISTRY


def raw_dir_for(source: str, raw_root: Path | None = None) -> Path:
    """Directory holding one source's raw file(s): ``<raw>/benchmark-corridor/<sub>``."""
    load_registry()
    spec = REGISTRY[source]
    root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    return root / DATATYPE / spec.raw_subdir


def unified_csv_path(source: str, raw_root: Path | None = None) -> Path:
    """Canonical unified-CSV path for a manual-download source."""
    spec = REGISTRY[source] if source in REGISTRY else load_registry()[source]
    return raw_dir_for(source, raw_root) / f"{spec.raw_subdir}.csv"


# ---------------------------------------------------------------------------
# Generic parsing helpers
# ---------------------------------------------------------------------------
def _coerce(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce raw string columns to the schema dtypes (target_year int, value float)."""
    df = df.copy()
    df["target_year"] = pd.to_numeric(df["target_year"], errors="raise").astype("int64")
    df["value"] = pd.to_numeric(df["value"], errors="raise").astype("float64")
    for c in (
        "source",
        "iso",
        "region",
        "vintage",
        "scenario",
        "quantity",
        "tech",
        "unit",
    ):
        df[c] = df[c].astype("string").str.strip()
    for c in ("source_doc", "source_page", "note"):
        if c in df.columns:
            df[c] = df[c].astype("string")
        else:
            df[c] = pd.Series([pd.NA] * len(df), dtype="string")
    return df


def finalize(df: pd.DataFrame, *, source: str | None = None) -> pd.DataFrame:
    """Order columns, coerce dtypes, and validate the controlled vocabularies.

    Returns the frame with exactly :data:`CANONICAL_COLUMNS` in order. Raises
    ``ValueError`` on an out-of-vocabulary quantity/tech/iso or a null key — the
    fail-loud guard that keeps every source's rows uniform.
    """
    if df.empty:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    missing = [
        c
        for c in CANONICAL_COLUMNS
        if c not in df.columns and c not in ("source_doc", "source_page", "note")
    ]
    if missing:
        raise ValueError(f"benchmark-corridor rows missing columns: {missing}")
    df = _coerce(df)
    bad_q = sorted(set(df["quantity"]) - QUANTITY_VOCAB)
    if bad_q:
        raise ValueError(
            f"unknown quantity value(s) {bad_q}; vocab={sorted(QUANTITY_VOCAB)}"
        )
    bad_t = sorted(set(df["tech"]) - TECH_VOCAB)
    if bad_t:
        raise ValueError(f"unknown tech value(s) {bad_t}; vocab={sorted(TECH_VOCAB)}")
    bad_i = sorted(set(df["iso"]) - ISO_VOCAB)
    if bad_i:
        raise ValueError(f"unknown iso value(s) {bad_i}; vocab={sorted(ISO_VOCAB)}")
    key = ["source", "iso", "region", "scenario", "target_year", "quantity", "tech"]
    if df[key].isna().any().any():
        raise ValueError("benchmark-corridor key columns contain nulls")
    dups = df.duplicated(subset=key, keep=False)
    if dups.any():
        raise ValueError(
            f"duplicate benchmark-corridor keys ({int(dups.sum())} rows), e.g.\n"
            f"{df.loc[dups, key].head(6).to_string(index=False)}"
        )
    out = df[list(CANONICAL_COLUMNS)].sort_values(key).reset_index(drop=True)
    return out


def parse_unified_csv(path: Path) -> pd.DataFrame:
    """Read a manual-download source's unified CSV (canonical columns).

    Returns an empty frame if the file is absent (the source is "missing", not
    an error). Otherwise reads every row and hands it through :func:`finalize`.
    """
    path = Path(path)
    if not path.is_file():
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    raw = pd.read_csv(path, dtype=str, keep_default_na=False)
    raw = raw.replace("", pd.NA)
    # Drop fully blank rows / comment rows (a leading '#' in `source`).
    if "source" in raw.columns:
        raw = raw[~raw["source"].astype("string").str.startswith("#", na=False)]
    raw = raw.dropna(how="all")
    if raw.empty:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    return finalize(raw)


def parse_source(source: str, raw_root: Path | None = None) -> pd.DataFrame:
    """Parse one registered source's raw directory into canonical rows."""
    load_registry()
    if source not in REGISTRY:
        raise KeyError(
            f"unknown benchmark-corridor source {source!r}; registered: {sorted(REGISTRY)}"
        )
    spec = REGISTRY[source]
    raw_dir = raw_dir_for(source, raw_root)
    parse = spec.parse or (
        lambda _d: parse_unified_csv(unified_csv_path(source, raw_root))
    )
    df = parse(raw_dir)
    if df is None or df.empty:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    return finalize(df, source=source)
