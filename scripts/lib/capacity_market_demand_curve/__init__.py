"""Shared contract for the ``capacity-market-demand-curve`` clean datatype.

Each capacity-market ISO's published demand-curve parameters (PJM VRR points +
Net CONE + IRM, NYISO ICAP demand curves, ISO-NE FCA/MRI parameters, MISO PRA
seasonal reliability-based curve + seasonal CONE, CAISO's CPM/CPUC-RA fixed
proxy) are reconciled onto ONE tidy frame declared in
``data/dictionary/schema/capacity-market-demand-curve.schema.yaml``.

The per-ISO logic lives in sibling modules (``pjm.py``, ``nyiso.py``, ...),
each of which registers an :class:`IsoSpec` via :func:`register`. Shared code
never branches on the ISO name — it looks the spec up in :data:`REGISTRY`.
This keeps new ISOs additive and lets parallel intake sessions work without
touching a shared file, per ``docs/adding-new-data-types.md``.

Retrieval sessions produce one *unified CSV* per ISO under
``data/raw/capacity-market/demand-curve/<iso>/<iso>.csv`` with exactly the
canonical columns; :func:`parse_unified_csv` is the generic reader every ISO
uses unless its spec supplies a custom ``parse`` hook.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "capacity-market-demand-curve"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "delivery_year",
    "area",
    "season",
    "metric",
    "point_index",
    "x_value",
    "x_unit",
    "y_value",
    "y_unit",
    "vintage",
    "source_doc",
    "source_page",
)

# Canonical metric vocabulary. See the schema header for each ISO's native
# parameter -> canonical metric map. gross_cone is the pre-inframarginal-rent
# Cost of New Entry (MISO publishes both a per-LRZ gross CONE and a
# two-subregion Net CONE — genuinely different quantities, not a duplicate).
# forecast_pool_requirement is PJM's published FPR — the reliability
# requirement stated in UCAP terms as a fraction of forecast peak load
# (post-CIFP FPR = (1+IRM) x Reference-Resource Accredited-UCAP factor);
# it devintages the requirement onto the ISO's own published basis (R2,
# accreditation-basis memo 2026-07-12 §4.2), carried in fraction_of_peak_ucap.
METRIC_VOCAB: frozenset[str] = frozenset(
    {
        "net_cone",
        "gross_cone",
        "irm",
        "forecast_pool_requirement",
        "price_cap",
        "price_floor",
        "curve_point",
        "soft_offer_cap",
        "ra_report_price",
    }
)

X_UNIT_VOCAB: frozenset[str] = frozenset({"pct_of_requirement", "mw", "pct_of_irm"})
Y_UNIT_VOCAB: frozenset[str] = frozenset(
    {
        "usd_per_mw_day",
        "usd_per_mw_day_icap",
        "usd_per_mw_yr",
        "usd_per_kw_month",
        "usd_per_kw_yr",
        "pct",
        "multiple_of_net_cone",
        "fraction_of_peak_ucap",
    }
)
SEASONS: frozenset[str] = frozenset({"summer", "fall", "winter", "spring"})

_STRING_COLS = (
    "iso",
    "delivery_year",
    "area",
    "season",
    "metric",
    "x_unit",
    "y_unit",
    "vintage",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("x_value", "y_value")
_INT_COLS = ("point_index",)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's capacity-market-demand-curve source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (e.g. ``"PJM"``, ``"NYISO"``, ``"ISONE"``, ``"MISO"``, ``"CAISO"``).
    metric_aliases:
        Map of native metric label (lower-cased) -> canonical metric, so a
        retrieval CSV may carry either the native or canonical name.
    delivery_year_kind:
        ``"planning"`` (label like ``"2025/2026"``) or ``"calendar"``
        (``"2025"``); documentation only.
    parse:
        Optional custom reader ``(raw_dir: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    metric_aliases: dict[str, str] = field(default_factory=dict)
    delivery_year_kind: str = "planning"
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
                continue  # ISO not implemented yet — additive by design.
        _loaded = True
    return REGISTRY


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw capacity-market-demand-curve inputs."""
    return raw_root / "capacity-market" / "demand-curve" / iso.lower()


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
    for col in _INT_COLS:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(
        ["delivery_year", "metric", "point_index"], na_position="first"
    ).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled-vocabulary columns before the frame reaches write_clean.

    Complements :func:`scripts.lib.clean_io.validate_df` with the value-level
    rules the schema can't express: metric/x_unit/y_unit/season vocabularies,
    curve_point rows carrying a point_index, and every row carrying a value.
    Raises :class:`ValueError` on any violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_metric = sorted(set(df["metric"].dropna()) - METRIC_VOCAB)
    if bad_metric:
        problems.append(f"metric(s) not in vocab: {bad_metric}")
    bad_x_unit = sorted(set(df["x_unit"].dropna()) - X_UNIT_VOCAB)
    if bad_x_unit:
        problems.append(f"x_unit(s) not in vocab: {bad_x_unit}")
    bad_y_unit = sorted(set(df["y_unit"].dropna()) - Y_UNIT_VOCAB)
    if bad_y_unit:
        problems.append(f"y_unit(s) not in vocab: {bad_y_unit}")
    bad_season = sorted(set(df["season"].dropna()) - SEASONS)
    if bad_season:
        problems.append(f"season(s) not in vocab: {bad_season}")
    curve_rows = df["metric"] == "curve_point"
    missing_point_index = curve_rows & df["point_index"].isna()
    if bool(missing_point_index.any()):
        problems.append(
            f"{int(missing_point_index.sum())} curve_point row(s) missing point_index"
        )
    # A curve_point's x-position is meaningful on its own: some ISOs (e.g.
    # PJM's Manual 18 formula points) publish the curve as a formula whose
    # price at a point is not itself a standalone published number, only the
    # point's x-position is. Scalar metrics (net_cone, irm, ...) always need
    # a y_value; curve_point rows need at least one of x_value/y_value.
    no_value = (~curve_rows & df["y_value"].isna()) | (
        curve_rows & df["x_value"].isna() & df["y_value"].isna()
    )
    if bool(no_value.any()):
        problems.append(f"{int(no_value.sum())} row(s) have no x_value/y_value")
    if problems:
        raise ValueError(
            "capacity-market-demand-curve tidy checks failed:\n  - "
            + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns. Native metric
    labels are mapped through ``spec.metric_aliases``. A scalar-metric row
    with no ``y_value`` (a source publishes only a bound like ">X", or a cell
    is unpublished) carries no information and is dropped rather than
    guessed; a ``curve_point`` row is kept as long as it carries an
    ``x_value`` even if its ``y_value`` is formula-defined rather than a
    published number (see :func:`validate_tidy`). Returns an empty (but
    correctly-shaped) frame when the CSV is absent so :func:`curate` can skip
    an ISO whose data has not landed yet.
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
    df = finalize(raw)
    has_value = df["y_value"].notna() | (
        (df["metric"] == "curve_point") & df["x_value"].notna()
    )
    return df[has_value].reset_index(drop=True)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/capacity_market_demand_curve/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_dir_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
