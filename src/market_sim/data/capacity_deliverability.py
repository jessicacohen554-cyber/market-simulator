"""Read the curated ``capacity-deliverability`` clean datatype into plain dicts.

The model's *consumption seam* for each ISO's locational resource-adequacy
parameters (PJM CETO/CETL, MISO LRR/LCR/CIL, NYISO LCR/TSL, ISO-NE LSR/MCL,
CAISO LCR/MIC), reconciled onto one tidy frame by the intake pipeline
(``scripts/lib/capacity_deliverability`` → ``data/clean/capacity-deliverability``).

Everything here returns **plain Python dicts / floats** keyed by the ISO's own
capacity *area* label (an LDA, LRZ, locality, capacity zone, local area or
intertie/branch group). Mapping those areas onto the model's *zones* is the job
of :mod:`market_sim.config.capacity_area_crosswalk`; this module never touches
the topology, and no Pydantic objects cross into the LP.

Only the reader lives here. The clean tree is derived/gitignored, so a missing
partition (an ISO whose intake has not landed, or ERCOT, which is energy-only
and has no analog) yields an empty dict with a warning rather than an error —
callers gate on ``ScenarioConfig.capacity_deliverability_limits`` and degrade to
their prior behaviour when the data is absent.
"""

from __future__ import annotations

import logging

import pandas as pd

logger = logging.getLogger(__name__)

DATATYPE = "capacity-deliverability"

# The model calls ISO New England "NEISO"; the clean partition (and every other
# ISO's source filings) label it "ISONE". Translate at the seam so callers pass
# their model ISO name and never learn the storage label.
_CLEAN_ISO_ALIAS: dict[str, str] = {"NEISO": "ISONE"}

# ISOs that publish these locational parameters. ERCOT is energy-only (no
# capacity market / LDAs), so it has no clean partition and reads as empty.
_SUPPORTED_ISOS: frozenset[str] = frozenset({"PJM", "MISO", "NYISO", "ISONE", "CAISO"})

# ISOs whose delivery_year is a planning-year label ("2024/2025"); the rest use
# a bare calendar study year ("2024", CAISO). Used to resolve a model calendar
# year to the ISO's delivery_year label.
_PLANNING_YEAR_ISOS: frozenset[str] = frozenset({"PJM", "MISO", "NYISO", "ISONE"})

# MISO publishes every metric per season (summer/fall/winter/spring) since
# PY2023-24; every other ISO publishes a single "annual" value. Resource
# adequacy binds at the seasonal peak, so the MISO default is the summer row.
_DEFAULT_SEASON_BY_ISO: dict[str, str] = {"MISO": "summer"}


def _clean_iso(iso: str) -> str:
    """Return the clean-partition ISO label for a model ISO name."""
    up = iso.upper()
    return _CLEAN_ISO_ALIAS.get(up, up)


def resolve_season(iso: str, season: str | None = None) -> str:
    """Return the season label to read for ``iso``.

    ``season`` overrides when given; otherwise MISO defaults to ``"summer"``
    (its binding RA season) and every other ISO to ``"annual"``.
    """
    if season is not None:
        return season
    return _DEFAULT_SEASON_BY_ISO.get(iso.upper(), "annual")


def resolve_delivery_year(iso: str, year: int) -> str:
    """Return the ISO's ``delivery_year`` label for a model calendar ``year``.

    Planning-year ISOs (PJM/MISO/NYISO/ISO-NE) label the period that *begins*
    in ``year`` as ``"{year}/{year+1}"``; CAISO uses the bare calendar study
    year ``"{year}"``. This is a pure label construction — whether that label
    is actually present in the clean file is checked by the reader, which falls
    back to the latest available year when the exact label is missing.
    """
    if iso.upper() in _PLANNING_YEAR_ISOS:
        return f"{year}/{year + 1}"
    return str(year)


def _read(iso: str) -> pd.DataFrame | None:
    """Return the clean frame for ``iso``, or ``None`` when unavailable.

    A missing partition (intake not landed, or an unsupported ISO such as
    ERCOT) is logged at INFO and returns ``None`` so callers degrade gracefully.
    """
    clean_iso = _clean_iso(iso)
    if clean_iso not in _SUPPORTED_ISOS:
        logger.info(
            "capacity-deliverability: no partition for ISO %s (energy-only / "
            "no locational RA construct)",
            iso,
        )
        return None
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError:
        logger.warning(
            "capacity-deliverability: scripts.lib.clean_io unavailable; "
            "returning no limits for %s",
            clean_iso,
        )
        return None
    try:
        return read_clean(DATATYPE, iso=clean_iso)
    except FileNotFoundError:
        logger.warning(
            "capacity-deliverability: clean partition for %s absent; run "
            "scripts/curate_capacity_deliverability.py. Returning no limits.",
            clean_iso,
        )
        return None


def available_delivery_years(iso: str) -> set[str]:
    """Return the ``delivery_year`` labels present in the ISO's clean partition.

    Lets callers that need an *exact* year (e.g. the MISO seasonal interface
    caps, whose backcast months straddle two planning years) decide their own
    fallback instead of inheriting :func:`_select_year`'s latest-year fallback.
    Empty when the partition is unavailable.
    """
    df = _read(iso)
    if df is None or df.empty:
        return set()
    return {str(y) for y in df["delivery_year"].dropna().unique()}


def available_seasons(iso: str, delivery_year: str) -> set[str]:
    """Return the ``season`` labels present for one ISO ``delivery_year``.

    Lets callers detect a pre-seasonal MISO planning year (PY2022-23 and
    earlier publish one ``"annual"`` CIL/CEL/LRR set; PY2023-24 onward carry
    the four seasons) and read the annual row instead of a season that does
    not exist — the exact-season filter in :func:`_metric_by_area` would
    otherwise fall back to the *latest* delivery year via :func:`_select_year`,
    silently substituting the wrong planning year. Empty when the partition or
    the delivery year is unavailable.
    """
    df = _read(iso)
    if df is None or df.empty:
        return set()
    sub = df[df["delivery_year"] == delivery_year]
    return {str(s) for s in sub["season"].dropna().unique()}


def _select_year(df: pd.DataFrame, iso: str, delivery_year: str) -> pd.DataFrame:
    """Return the rows for ``delivery_year``, or the latest year when absent.

    Delivery-year labels sort lexically in chronological order for both the
    planning-year ("2024/2025") and calendar ("2024") conventions, so the
    fallback simply takes the max label present.
    """
    years = set(df["delivery_year"].dropna().unique())
    if delivery_year in years:
        return df[df["delivery_year"] == delivery_year]
    if not years:
        return df.iloc[0:0]
    latest = max(years)
    logger.info(
        "capacity-deliverability %s: delivery_year %s absent; using latest %s",
        iso,
        delivery_year,
        latest,
    )
    return df[df["delivery_year"] == latest]


def _metric_by_area(
    iso: str,
    metric: str,
    delivery_year: str,
    season: str,
) -> dict[str, float]:
    """Return ``{area: value_mw}`` for one metric / delivery year / season.

    Rows whose ``value_mw`` is null (a metric the ISO published only as a
    ratio, or an unpublished cell) are dropped. Returns an empty dict when the
    partition is absent so callers can no-op.
    """
    df = _read(iso)
    if df is None or df.empty:
        return {}
    sub = df[(df["metric"] == metric) & (df["season"] == season)]
    sub = _select_year(sub, iso, delivery_year)
    sub = sub[sub["value_mw"].notna()]
    return {str(a): float(v) for a, v in zip(sub["area"], sub["value_mw"])}


def requirement_by_area(
    iso: str,
    delivery_year: str,
    season: str = "annual",
) -> dict[str, float]:
    """Return ``{area: requirement_mw}`` — the locational capacity requirement.

    ``requirement`` is the CETO analog: the MW of accredited capacity an area
    must hold or be able to serve. Keyed by the ISO's native area label (LDA /
    LRZ / locality / capacity zone / local area).

    Args:
        iso: Model ISO name (``NEISO`` is translated to the ``ISONE`` partition).
        delivery_year: The ISO's ``delivery_year`` label (see
            :func:`resolve_delivery_year`); falls back to the latest present.
        season: ``"annual"`` for every ISO except MISO, which is seasonal
            (pass ``"summer"`` for the binding RA season).

    Returns:
        A plain ``{area: MW}`` dict; empty when the partition is unavailable.
    """
    return _metric_by_area(iso, "requirement", delivery_year, season)


def import_limit_by_area(
    iso: str,
    delivery_year: str,
    season: str = "annual",
) -> dict[str, float]:
    """Return ``{area: import_limit_mw}`` — the area transfer/import limit.

    ``import_limit`` is the CETL analog: for PJM/MISO/NYISO/ISO-NE it is the
    per-area capacity-emergency transfer limit (how much can be imported into
    the area); for CAISO the rows are branch-group Maximum Import Capability
    (MIC) — a *seam* import limit into the WECC boundary, not an internal-zone
    transfer (see the crosswalk for how each is routed to a model zone).

    Args, Returns: as :func:`requirement_by_area`.
    """
    return _metric_by_area(iso, "import_limit", delivery_year, season)


def area_types_by_area(
    iso: str,
    delivery_year: str,
    season: str = "annual",
    metric: str | None = None,
) -> dict[str, str]:
    """Return ``{area: area_type}`` for one delivery year / season.

    Needed to route CAISO areas correctly (branch-group MIC vs local-area LCR)
    when crosswalking to zones. Optionally filtered to one ``metric``. Returns
    an empty dict when the partition is unavailable.
    """
    df = _read(iso)
    if df is None or df.empty:
        return {}
    sub = df[df["season"] == season]
    sub = _select_year(sub, iso, delivery_year)
    if metric is not None:
        sub = sub[sub["metric"] == metric]
    return {str(a): str(t) for a, t in zip(sub["area"], sub["area_type"])}


def export_limit_by_area(
    iso: str,
    delivery_year: str,
    season: str = "annual",
) -> dict[str, float]:
    """Return ``{area: export_limit_mw}`` — the area export transfer limit.

    ``export_limit`` is the MCL analog (MISO CEL / ISO-NE MCL): the MW of
    surplus generation an export-constrained area may send out. Only MISO and
    ISO-NE publish it; other ISOs return an empty dict.

    Args, Returns: as :func:`requirement_by_area`.
    """
    return _metric_by_area(iso, "export_limit", delivery_year, season)
