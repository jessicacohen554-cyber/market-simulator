"""Shared contract for the ``capacity-market-auction-price`` clean datatype.

Each capacity-market ISO's published auction/spot clearing-price history (PJM
BRA, NYISO spot, ISO-NE FCA, MISO PRA) is reconciled onto ONE tidy frame
declared in ``data/dictionary/schema/capacity-market-auction-price.schema.yaml``.
This is a VALIDATION OBSERVABLE (CR-2 / T3.1) — compared against the model's
implemented demand-curve mechanism, never pinned or fit to (CLAUDE.md rules
1/13).

Per the intake plan (docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §3-4), only delivery
years <= 2026/27 are admitted at intake: later delivery years have not
cleared yet (PJM's 2026/2027 BRA is the most recent held at time of writing)
and admitting them here would risk a future accidental leak of actual
auction-clearing outcomes into a holdout-year comparison. :func:`validate_tidy`
enforces the cutoff and raises rather than silently dropping, so a source
that publishes a later delivery year is caught at curation time, not
discovered downstream.

The per-ISO logic lives in sibling modules (``pjm.py``, ``nyiso.py``, ...),
each of which registers an :class:`IsoSpec` via :func:`register`. Shared code
never branches on the ISO name — it looks the spec up in :data:`REGISTRY`.
"""

from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "capacity-market-auction-price"

# No auction-clearing outcome for a delivery year starting after this may be
# admitted (docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
# §4: "delivery years <= 2026/27 only").
MAX_DELIVERY_YEAR_START: int = 2026

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "delivery_year",
    "season",
    "area",
    "area_type",
    "auction_round",
    "clearing_price",
    "price_unit",
    "cleared_mw",
    "source_doc",
    "source_page",
)

SEASONS: frozenset[str] = frozenset({"annual", "summer", "fall", "winter", "spring"})
# "resource" covers CAISO's CPM backstop, which designates and clears at
# individual-resource granularity rather than a zone/area (no locality curve
# of its own — see scripts/lib/capacity_market_auction_price/caiso.py).
# "import_interface" covers an external tie that clears its own price
# alongside the internal zones (e.g. ISO-NE's New Brunswick interface in FCA
# results).
AREA_TYPES: frozenset[str] = frozenset(
    {"lda", "lrz", "locality", "capacity_zone", "rto", "resource", "import_interface"}
)
AUCTION_ROUNDS: frozenset[str] = frozenset(
    {
        "base_residual_auction",
        "incremental_auction",
        "spot",
        "forward_capacity_auction",
        "planning_resource_auction",
        "cpm_backstop",
    }
)
PRICE_UNITS: frozenset[str] = frozenset(
    {"usd_per_mw_day", "usd_per_kw_month", "usd_per_kw_yr", "usd_per_mw_yr"}
)

_STRING_COLS = (
    "iso",
    "delivery_year",
    "season",
    "area",
    "area_type",
    "auction_round",
    "price_unit",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("clearing_price", "cleared_mw")

_LEADING_YEAR_RE = re.compile(r"(\d{4})")


def delivery_year_start(label: str) -> int | None:
    """Extract the leading 4-digit year from a delivery-year label, or None."""
    m = _LEADING_YEAR_RE.search(str(label))
    return int(m.group(1)) if m else None


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's capacity-market-auction-price source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition.
    default_area_type:
        Area type stamped on rows whose CSV leaves ``area_type`` blank.
    default_auction_round:
        Auction/product-type label stamped on rows whose CSV leaves
        ``auction_round`` blank (each ISO runs essentially one round type).
    parse:
        Optional custom reader ``(raw_dir: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    default_area_type: str
    default_auction_round: str
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = None


REGISTRY: dict[str, IsoSpec] = {}

_ISO_MODULES: tuple[str, ...] = ("pjm", "nyiso", "isone", "miso", "caiso")
_loaded = False


def register(spec: IsoSpec) -> IsoSpec:
    """Register an :class:`IsoSpec` under its ISO label. Returns the spec."""
    if spec.default_area_type not in AREA_TYPES:
        raise ValueError(
            f"{spec.iso}: default_area_type {spec.default_area_type!r} not in {sorted(AREA_TYPES)}"
        )
    if spec.default_auction_round not in AUCTION_ROUNDS:
        raise ValueError(
            f"{spec.iso}: default_auction_round {spec.default_auction_round!r} "
            f"not in {sorted(AUCTION_ROUNDS)}"
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
                continue
        _loaded = True
    return REGISTRY


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw capacity-market-auction-price inputs."""
    return raw_root / "capacity-market" / "auction-price" / iso.lower()


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
    out = out.sort_values(["delivery_year", "season", "area"]).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary columns and the delivery-year cutoff.

    Complements :func:`scripts.lib.clean_io.validate_df` with the value-level
    rules the schema can't express: season/area_type/auction_round
    vocabularies, at-least-one-value per row, and the delivery-year quarantine
    cutoff (:data:`MAX_DELIVERY_YEAR_START`). Raises :class:`ValueError` on any
    violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_season = sorted(set(df["season"].dropna()) - SEASONS)
    if bad_season:
        problems.append(f"season(s) not in vocab: {bad_season}")
    bad_area_type = sorted(set(df["area_type"].dropna()) - AREA_TYPES)
    if bad_area_type:
        problems.append(f"area_type(s) not in vocab: {bad_area_type}")
    bad_round = sorted(set(df["auction_round"].dropna()) - AUCTION_ROUNDS)
    if bad_round:
        problems.append(f"auction_round(s) not in vocab: {bad_round}")
    bad_price_unit = sorted(set(df["price_unit"].dropna()) - PRICE_UNITS)
    if bad_price_unit:
        problems.append(f"price_unit(s) not in vocab: {bad_price_unit}")
    both_null = df["clearing_price"].isna() & df["cleared_mw"].isna()
    if bool(both_null.any()):
        problems.append(
            f"{int(both_null.sum())} row(s) have neither clearing_price nor cleared_mw"
        )
    years = df["delivery_year"].map(delivery_year_start)
    too_late = years.notna() & (years > MAX_DELIVERY_YEAR_START)
    if bool(too_late.any()):
        offending = sorted(set(df.loc[too_late, "delivery_year"]))
        problems.append(
            f"delivery_year(s) beyond the {MAX_DELIVERY_YEAR_START}/{MAX_DELIVERY_YEAR_START + 1} "
            f"quarantine cutoff: {offending}"
        )
    if problems:
        raise ValueError(
            "capacity-market-auction-price tidy checks failed:\n  - "
            + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns. A blank
    ``season``/``area_type``/``auction_round`` cell defaults from the spec.
    Rows with neither a clearing price nor a cleared-MW value carry no
    information and are dropped. Returns an empty (but correctly-shaped) frame
    when the CSV is absent so :func:`curate` can skip an ISO whose data has
    not landed yet.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["iso"] = spec.iso
    if "season" in raw.columns:
        raw["season"] = raw["season"].fillna("annual").replace({"": "annual"})
    else:
        raw["season"] = "annual"
    if "area_type" in raw.columns:
        raw["area_type"] = (
            raw["area_type"]
            .fillna(spec.default_area_type)
            .replace({"": spec.default_area_type})
        )
    else:
        raw["area_type"] = spec.default_area_type
    if "auction_round" in raw.columns:
        raw["auction_round"] = (
            raw["auction_round"]
            .fillna(spec.default_auction_round)
            .replace({"": spec.default_auction_round})
        )
    else:
        raw["auction_round"] = spec.default_auction_round
    df = finalize(raw)
    both_null = df["clearing_price"].isna() & df["cleared_mw"].isna()
    return df[~both_null].reset_index(drop=True)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/capacity_market_auction_price/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
