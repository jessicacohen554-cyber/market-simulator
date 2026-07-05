"""Shared contract for the ``capacity-deliverability`` clean datatype.

Each ISO's locational resource-adequacy parameters (PJM CETO/CETL, MISO
LRR/LCR/CIL/CEL/ZIA, NYISO LCR/TSL, ISO-NE LSR/MCL, CAISO LCR/MIC) are
reconciled onto ONE tidy frame declared in
``data/dictionary/schema/capacity-deliverability.schema.yaml``.

The per-ISO logic lives in sibling modules (``pjm.py``, ``miso.py``, ...), each
of which registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`. This keeps
new ISOs additive (drop a module, register a spec) and lets parallel intake
sessions work without touching a shared file, per ``docs/adding-new-data-types.md``.

Retrieval sessions produce one *unified CSV* per ISO under
``data/raw/capacity-deliverability/<iso>/<iso>.csv`` with exactly the canonical
columns; :func:`parse_unified_csv` is the generic reader every ISO uses unless
its spec supplies a custom ``parse`` hook for a native (non-CSV) source.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "capacity-deliverability"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "area",
    "area_type",
    "delivery_year",
    "season",
    "metric",
    "value_mw",
    "value_pu",
    "source_doc",
    "source_page",
)

# Canonical metric vocabulary. requirement is the CETO analog; import_limit is
# the CETL analog. See the schema header for each ISO's native -> canonical map.
METRIC_VOCAB: frozenset[str] = frozenset(
    {
        "requirement",
        "local_clearing_requirement",
        "import_limit",
        "export_limit",
        "import_ability",
        "system_requirement",
        # Published area peak-demand forecast from the SAME study table family
        # as the area's requirement (CAISO LCT "Load+Losses+Pumps" area rows /
        # Table 3.2-1 zonal rows): pairs with `requirement` so
        # import_cap = peak_load - requirement is computed on one consistent
        # boundary (market_sim.data.local_capacity).
        "peak_load",
    }
)

AREA_TYPES: frozenset[str] = frozenset(
    {
        "lda",
        "lrz",
        "locality",
        "capacity_zone",
        "local_area",
        "branch_group",
        "rto",
        # Model/transmission-zone aggregate rows (CAISO SP26 zonal peak_load,
        # the denominator of the local-capacity area load share).
        "zone",
    }
)

SEASONS: frozenset[str] = frozenset({"annual", "summer", "fall", "winter", "spring"})

# String columns that must be text; numeric columns coerced to float64.
_STRING_COLS = (
    "iso",
    "area",
    "area_type",
    "delivery_year",
    "season",
    "metric",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("value_mw", "value_pu")


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's capacity-deliverability source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (e.g. ``"PJM"``, ``"MISO"``, ``"NYISO"``, ``"ISONE"``, ``"CAISO"``).
    default_area_type:
        Area type stamped on rows whose CSV leaves ``area_type`` blank.
    metric_aliases:
        Map of native metric label (lower-cased, e.g. ``"ceto"``) -> canonical
        metric, so a retrieval CSV may carry either the native or canonical name.
    delivery_year_kind:
        ``"planning"`` (label like ``"2025/2026"``) or ``"calendar"`` (``"2025"``);
        documentation only, used by the parser to sanity-check the label shape.
    parse:
        Optional custom reader ``(raw_dir: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    default_area_type: str
    metric_aliases: dict[str, str] = field(default_factory=dict)
    delivery_year_kind: str = "planning"
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = None


# The registry every ISO module populates at import time.
REGISTRY: dict[str, IsoSpec] = {}

# ISO submodules to import so their register() calls run. Missing modules (an
# ISO not yet implemented) are skipped, so intake waves land independently.
_ISO_MODULES: tuple[str, ...] = ("pjm", "miso", "nyiso", "isone", "caiso")
_loaded = False


def register(spec: IsoSpec) -> IsoSpec:
    """Register an :class:`IsoSpec` under its ISO label. Returns the spec."""
    if spec.default_area_type not in AREA_TYPES:
        raise ValueError(
            f"{spec.iso}: default_area_type {spec.default_area_type!r} not in {sorted(AREA_TYPES)}"
        )
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


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw capacity-deliverability inputs."""
    return raw_root / DATATYPE / iso.lower()


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order.

    Missing optional columns (``value_mw`` / ``value_pu`` / source locators) are
    filled with nulls so a source that carries only one value form still yields
    a schema-shaped frame.
    """
    out = df.copy()
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in _STRING_COLS:
        out[col] = out[col].astype("string")
    for col in _FLOAT_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(["delivery_year", "season", "area", "metric"]).reset_index(
        drop=True
    )
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary columns before the frame reaches write_clean.

    Complements :func:`scripts.lib.clean_io.validate_df` (which checks dtypes,
    nulls and naming) with the value-level rules the schema can't express:
    metric / area_type / season vocabularies and at-least-one-value per row.
    Raises :class:`ValueError` on any violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_metric = sorted(set(df["metric"].dropna()) - METRIC_VOCAB)
    if bad_metric:
        problems.append(f"metric(s) not in vocab: {bad_metric}")
    bad_area_type = sorted(set(df["area_type"].dropna()) - AREA_TYPES)
    if bad_area_type:
        problems.append(f"area_type(s) not in vocab: {bad_area_type}")
    bad_season = sorted(set(df["season"].dropna()) - SEASONS)
    if bad_season:
        problems.append(f"season(s) not in vocab: {bad_season}")
    both_null = df["value_mw"].isna() & df["value_pu"].isna()
    if bool(both_null.any()):
        problems.append(
            f"{int(both_null.sum())} row(s) have neither value_mw nor value_pu"
        )
    if problems:
        raise ValueError(
            "capacity-deliverability tidy checks failed:\n  - "
            + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns (as produced by
    the retrieval prompts). Native metric labels are mapped through
    ``spec.metric_aliases``; a blank ``area_type`` is filled from
    ``spec.default_area_type``; a blank ``season`` defaults to ``"annual"``.
    Rows with neither a MW nor a p.u. value (the retrieval prompts leave a cell
    blank rather than guess an unpublished value) carry no information and are
    dropped. Returns an empty (but correctly-shaped) frame when the CSV is
    absent so :func:`curate` can skip an ISO whose data has not landed yet.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str)
    raw.columns = [c.strip().lower() for c in raw.columns]
    if "metric" in raw.columns and spec.metric_aliases:
        raw["metric"] = (
            raw["metric"]
            .str.strip()
            .str.lower()
            .map(lambda m: spec.metric_aliases.get(m, m))
        )
    raw["iso"] = spec.iso
    if "area_type" in raw.columns:
        raw["area_type"] = (
            raw["area_type"]
            .fillna(spec.default_area_type)
            .replace({"": spec.default_area_type})
        )
    else:
        raw["area_type"] = spec.default_area_type
    if "season" in raw.columns:
        raw["season"] = raw["season"].fillna("annual").replace({"": "annual"})
    else:
        raw["season"] = "annual"
    df = finalize(raw)
    both_null = df["value_mw"].isna() & df["value_pu"].isna()
    return df[~both_null].reset_index(drop=True)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/capacity_deliverability/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
