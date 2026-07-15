"""Shared contract for the ``capacity-market-avoidable-cost-rate`` clean datatype.

Published default/generic Avoidable Cost Rate (going-forward-cost) benchmarks
by technology class — PJM's own Manual 18 / Tariff default gross ACR table
(``source_type=pjm_manual18_default``) and Monitoring Analytics' independent
State of the Market avoidable-cost benchmark tables
(``source_type=monitoring_analytics_som``) — reconciled onto ONE tidy frame
declared in
``data/dictionary/schema/capacity-market-avoidable-cost-rate.schema.yaml``.

The per-ISO logic lives in sibling modules (``pjm.py``, ...), each of which
registers an :class:`IsoSpec` via :func:`register`. Shared code never branches
on the ISO name — it looks the spec up in :data:`REGISTRY`. Mirrors
``scripts/lib/capacity_market_demand_curve`` exactly, per
``docs/adding-new-data-types.md``.

Retrieval sessions produce one *unified CSV* per ISO under
``data/raw/capacity-market/avoidable-cost-rate/<iso>/<iso>.csv`` with exactly
the canonical columns; :func:`parse_unified_csv` is the generic reader every
ISO uses unless its spec supplies a custom ``parse`` hook.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "capacity-market-avoidable-cost-rate"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "source_type",
    "technology_class",
    "capacity_bin",
    "cost_component",
    "value",
    "unit",
    "vintage",
    "source_doc",
    "source_page",
)

SOURCE_TYPE_VOCAB: frozenset[str] = frozenset(
    {"pjm_manual18_default", "monitoring_analytics_som"}
)
COST_COMPONENT_VOCAB: frozenset[str] = frozenset(
    {
        "gross_acr",
        "avoidable_capital_recovery",
        "avoidable_fixed_om",
        "avoidable_variable_om",
        "net_acr",
    }
)
UNIT_VOCAB: frozenset[str] = frozenset(
    {"usd_per_mw_yr", "usd_per_kw_month", "usd_per_mw_day", "usd_per_kw_yr"}
)

_STRING_COLS = (
    "iso",
    "source_type",
    "technology_class",
    "capacity_bin",
    "cost_component",
    "unit",
    "vintage",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("value",)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's avoidable-cost-rate source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean
        partition (e.g. ``"PJM"``).
    parse:
        Optional custom reader ``(raw_dir: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = None


REGISTRY: dict[str, IsoSpec] = {}

_ISO_MODULES: tuple[str, ...] = ("pjm",)
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
                continue  # ISO not implemented yet -- additive by design.
        _loaded = True
    return REGISTRY


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw avoidable-cost-rate inputs."""
    return raw_root / "capacity-market" / "avoidable-cost-rate" / iso.lower()


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
        ["source_type", "technology_class", "cost_component", "vintage"],
        na_position="first",
    ).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary columns before the frame reaches write_clean.

    Complements :func:`scripts.lib.clean_io.validate_df` with the value-level
    rules the schema can't express: source_type/cost_component/unit
    vocabularies and every row carrying a value. Raises :class:`ValueError` on
    any violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_source_type = sorted(set(df["source_type"].dropna()) - SOURCE_TYPE_VOCAB)
    if bad_source_type:
        problems.append(f"source_type(s) not in vocab: {bad_source_type}")
    bad_component = sorted(set(df["cost_component"].dropna()) - COST_COMPONENT_VOCAB)
    if bad_component:
        problems.append(f"cost_component(s) not in vocab: {bad_component}")
    bad_unit = sorted(set(df["unit"].dropna()) - UNIT_VOCAB)
    if bad_unit:
        problems.append(f"unit(s) not in vocab: {bad_unit}")
    no_value = df["value"].isna()
    if bool(no_value.any()):
        problems.append(f"{int(no_value.sum())} row(s) have no value")
    if problems:
        raise ValueError(
            "capacity-market-avoidable-cost-rate tidy checks failed:\n  - "
            + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns. A row with no
    ``value`` carries no information and is dropped rather than guessed.
    Returns an empty (but correctly-shaped) frame when the CSV is absent so
    :func:`curate` can skip an ISO whose data has not landed yet.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["iso"] = spec.iso
    df = finalize(raw)
    return df[df["value"].notna()].reset_index(drop=True)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/capacity_market_avoidable_cost_rate/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
