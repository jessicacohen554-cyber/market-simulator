"""Shared contract for the ``capacity-market-auction-supply`` clean datatype.

The supply half of the capacity-auction record (companion to
``capacity-market-auction-price``, which carries the cleared PRICES): each
capacity auction's published QUANTITY accounting — offered and cleared MW by
planning-resource category plus the requirement/commitment ledger rows the
same postings publish — reconciled onto ONE tidy frame declared in
``data/dictionary/schema/capacity-market-auction-supply.schema.yaml``.

First populated for MISO (capx D31, 2026-09-02) from the PRA Results
Postings: the "Seasonal Supply Offered and Cleared Comparison Trend" category
tables (ZRC) and the seasonal "PRA Results by Zone" System/subregion ledger
rows (MW SAC). Rule-13 posture (stated in the schema header): the market's
own supply-accounting basis is an admissible published input; the cleared
quantities are validation observables — never a target to pin a model's
position or cleared MW to.

The per-ISO logic lives in sibling modules (``miso.py``, ...), each of which
registers an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY`. The
registry scaffolding is built by
:func:`scripts.lib.datatype_registry.make_registry`; only the columns,
vocabularies, ``validate_tidy`` and ``parse_unified_csv`` are
datatype-specific and live here.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "capacity-market-auction-supply"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "planning_year",
    "season",
    "area",
    "metric",
    "category",
    "value_mw",
    "unit",
    "vintage",
    "source_doc",
    "source_page",
)

SEASONS: frozenset[str] = frozenset({"summer", "fall", "winter", "spring"})
# offered/cleared pair with a category; the ledger metrics carry category null.
CATEGORY_METRICS: frozenset[str] = frozenset({"offered", "cleared"})
LEDGER_METRICS: frozenset[str] = frozenset(
    {
        "prmr",
        "initial_prmr",
        "final_prmr",
        "offer_submitted",
        "frap",
        "self_scheduled",
        "non_ss_offer_cleared",
        "committed",
    }
)
METRIC_VOCAB: frozenset[str] = CATEGORY_METRICS | LEDGER_METRICS
CATEGORY_VOCAB: frozenset[str] = frozenset(
    {
        "generation",
        "external_resources",
        "behind_meter_generation",
        "demand_resources",
        "energy_efficiency",
        "total",
    }
)
# mw_zrc / mw_sac: MISO's ZRC and SAC labels; mw_ucap: PJM's Unforced
# Capacity basis (the BRA reports state DR/EE and generation offers in UCAP).
UNIT_VOCAB: frozenset[str] = frozenset({"mw_zrc", "mw_sac", "mw_ucap"})

_STRING_COLS = (
    "iso",
    "planning_year",
    "season",
    "area",
    "metric",
    "category",
    "unit",
    "vintage",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("value_mw",)


_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
    ],
    package=__name__,
    iso_modules=("miso", "pjm"),
    raw_subpath=("capacity-market", "auction-supply"),
    string_cols=_STRING_COLS,
    float_cols=_FLOAT_COLS,
    sort_by=("planning_year", "season", "area", "metric", "category"),
    na_position="first",
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for
finalize = _R.finalize


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary columns before the frame reaches write_clean.

    Complements :func:`scripts.lib.clean_io.validate_df` with the value-level
    rules the schema can't express: metric/category/unit/season vocabularies,
    the metric-category pairing (offered/cleared rows carry a category, ledger
    rows don't), and positive quantities. Raises :class:`ValueError` on any
    violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_metric = sorted(set(df["metric"].dropna()) - METRIC_VOCAB)
    if bad_metric:
        problems.append(f"metric(s) not in vocab: {bad_metric}")
    bad_cat = sorted(set(df["category"].dropna()) - CATEGORY_VOCAB)
    if bad_cat:
        problems.append(f"category(s) not in vocab: {bad_cat}")
    bad_unit = sorted(set(df["unit"].dropna()) - UNIT_VOCAB)
    if bad_unit:
        problems.append(f"unit(s) not in vocab: {bad_unit}")
    bad_season = sorted(set(df["season"].dropna()) - SEASONS)
    if bad_season:
        problems.append(f"season(s) not in vocab: {bad_season}")
    cat_rows = df["metric"].isin(sorted(CATEGORY_METRICS))
    missing_cat = cat_rows & df["category"].isna()
    if bool(missing_cat.any()):
        problems.append(
            f"{int(missing_cat.sum())} offered/cleared row(s) missing category"
        )
    stray_cat = ~cat_rows & df["category"].notna()
    if bool(stray_cat.any()):
        problems.append(
            f"{int(stray_cat.sum())} ledger row(s) carry a category (must be null)"
        )
    bad_value = df["value_mw"].isna() | (df["value_mw"] < 0.0)
    if bool(bad_value.any()):
        problems.append(f"{int(bad_value.sum())} row(s) with missing/negative value_mw")
    if problems:
        raise ValueError(
            "capacity-market-auction-supply tidy checks failed:\n  - "
            + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns. Returns an
    empty (but correctly-shaped) frame when the CSV is absent so
    :func:`curate` can skip an ISO whose data has not landed yet.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["iso"] = spec.iso
    return finalize(raw)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/capacity_market_auction_supply/{iso.lower()}.py present?)"
        )
    reader = spec.parse if getattr(spec, "parse", None) else parse_unified_csv
    df = reader(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
