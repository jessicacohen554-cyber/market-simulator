"""Shared contract for the ``capacity-market-elcc`` clean datatype.

Each capacity-market ISO's published Effective Load Carrying Capability (or
equivalent capacity-accreditation) study is reconciled onto ONE tidy frame
declared in ``data/dictionary/schema/capacity-market-elcc.schema.yaml``. This
is the CR-3.1 input (docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §3.4.1) — the
penetration-indexed curves that will eventually replace the model's flat
``RENEWABLE_CAPACITY_CREDIT`` wind/solar constants.

The per-ISO logic lives in sibling modules (``pjm.py``, ``nyiso.py``, ...),
each of which registers an :class:`IsoSpec` via :func:`register`. Shared code
never branches on the ISO name — it looks the spec up in :data:`REGISTRY`.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "capacity-market-elcc"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "resource_class",
    "study_vintage",
    "penetration_pct",
    "penetration_unit",
    "elcc_pct",
    "elcc_type",
    "source_doc",
    "source_page",
)

RESOURCE_CLASSES: frozenset[str] = frozenset(
    {
        "wind",
        "solar",
        "wind_offshore",
        "hybrid_solar_storage",
        "storage_2hr",
        "storage_4hr",
        "storage_6hr",
        "storage_8hr",
        "storage_10hr",
        "storage_ldes",
        "other",
    }
)
PENETRATION_UNITS: frozenset[str] = frozenset(
    {"pct_of_peak_load", "pct_of_installed_capacity", "installed_mw"}
)
ELCC_TYPES: frozenset[str] = frozenset({"class_average", "marginal", "incremental"})

_STRING_COLS = (
    "iso",
    "resource_class",
    "study_vintage",
    "penetration_unit",
    "elcc_type",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("penetration_pct", "elcc_pct")


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's capacity-market-elcc source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition.
    resource_class_aliases:
        Map of native resource-class label (lower-cased) -> canonical
        resource_class, so a retrieval CSV may carry either form.
    parse:
        Optional custom reader ``(raw_dir: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    resource_class_aliases: dict[str, str] = field(default_factory=dict)
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = None


REGISTRY: dict[str, IsoSpec] = {}

_ISO_MODULES: tuple[str, ...] = ("pjm", "nyiso", "isone", "miso", "caiso")
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
                continue
        _loaded = True
    return REGISTRY


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw capacity-market-elcc inputs."""
    return raw_root / "capacity-market" / "elcc" / iso.lower()


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order."""
    out = df.copy()
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in _STRING_COLS:
        out[col] = out[col].astype("string")
    for col in _FLOAT_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(
        ["resource_class", "study_vintage", "penetration_pct"], na_position="first"
    ).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary columns before the frame reaches write_clean.

    Complements :func:`scripts.lib.clean_io.validate_df` with the value-level
    rules the schema can't express: resource_class/penetration_unit/elcc_type
    vocabularies and every row carrying an elcc_pct. Raises :class:`ValueError`
    on any violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_class = sorted(set(df["resource_class"].dropna()) - RESOURCE_CLASSES)
    if bad_class:
        problems.append(f"resource_class(es) not in vocab: {bad_class}")
    bad_unit = sorted(set(df["penetration_unit"].dropna()) - PENETRATION_UNITS)
    if bad_unit:
        problems.append(f"penetration_unit(s) not in vocab: {bad_unit}")
    bad_type = sorted(set(df["elcc_type"].dropna()) - ELCC_TYPES)
    if bad_type:
        problems.append(f"elcc_type(s) not in vocab: {bad_type}")
    no_value = df["elcc_pct"].isna()
    if bool(no_value.any()):
        problems.append(f"{int(no_value.sum())} row(s) have no elcc_pct")
    if problems:
        raise ValueError(
            "capacity-market-elcc tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns. Native
    resource-class labels are mapped through ``spec.resource_class_aliases``.
    Rows with no ``elcc_pct`` carry no information and are dropped. Returns an
    empty (but correctly-shaped) frame when the CSV is absent so
    :func:`curate` can skip an ISO whose data has not landed yet.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str)
    raw.columns = [c.strip().lower() for c in raw.columns]
    if "resource_class" in raw.columns and spec.resource_class_aliases:
        raw["resource_class"] = (
            raw["resource_class"]
            .str.strip()
            .str.lower()
            .map(lambda c: spec.resource_class_aliases.get(c, c))
        )
    raw["iso"] = spec.iso
    df = finalize(raw)
    return df[df["elcc_pct"].notna()].reset_index(drop=True)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/capacity_market_elcc/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
