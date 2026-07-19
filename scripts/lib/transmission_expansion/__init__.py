"""Shared contract for the ``transmission-expansion`` clean datatype.

Each ISO's committed transmission-expansion projects (ERCOT PUCT-approved
Permian/765 kV work, MISO board-approved LRTP tranches, PJM RTEP designations,
CAISO TPP board approvals, NYISO public-policy selections and Tier 4 contracts,
ISO-NE state-contracted HVDC) are curated onto ONE tidy frame declared in
``data/dictionary/schema/transmission-expansion.schema.yaml``.

The per-ISO logic lives in sibling modules (``ercot.py``, ``miso.py``, ...),
each of which registers an :class:`IsoSpec` via :func:`register`. Shared code
never branches on the ISO name — it looks the spec up in :data:`REGISTRY`,
mirroring ``scripts/lib/confirmed_retirements`` (the binding-instrument
registry this package clones; hand-rolled rather than
``scripts.lib.datatype_registry.make_registry`` because the canonical frame
carries datetime/bool/nullable-int columns and a single per-ISO CSV, neither of
which the factory's finalize/raw resolver covers).

Retrieval sessions produce one hand-curated CSV per ISO at
``data/raw/transmission-expansion/<iso>.csv`` with exactly the canonical
columns (sources are planning PDFs / regulator dockets, so curation is
human-in-the-loop by design; the provenance + mapping_note columns are what
keep it reproducible per CLAUDE.md rules 13/14). :func:`parse_unified_csv` is
the generic reader every ISO uses unless its spec supplies a custom ``parse``
hook.

This datatype is **forecast-forward only**: it feeds the forward TTC channel
(``market_sim.data.transmission_expansion`` → the per-year link/interface
uplift in ``runner.run_scenario_iso``). Backcast-year transmission stays with
the measured overlays (``NYISO_INTERFACE_TTC_BY_YEAR``, measured GTC/interface
series); nothing here is a backcast device.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

DATATYPE = "transmission-expansion"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "row_id",
    "project_id",
    "project_name",
    "sponsor",
    "status_tier",
    "instrument",
    "instrument_id",
    "instrument_date",
    "in_service_year",
    "in_service_month",
    "target_kind",
    "from_zone",
    "to_zone",
    "interface_name",
    "delta_mw",
    "delta_mw_reverse",
    "capacity_basis",
    "mapping_confidence",
    "mapping_note",
    "superseded",
    "superseding_instrument",
    "superseding_instrument_date",
    "source_url",
    "source_doc",
    "accessed",
    "notes",
)

# Closed status vocabulary. ``roadmap``/``planned``/``recommended`` is
# deliberately NOT a member: an unapproved plan is not an instrument, so it
# stays a README watchlist entry (the confirmed-retirements announced-exclusion
# convention, rule 13).
STATUS_TIER_VOCAB: frozenset[str] = frozenset(
    {"energized", "under_construction", "approved_funded"}
)

# What kind of model element a row's delta targets. ``link``/``interface``
# rows are the apply set; ``import_tranche``/``intra_zonal`` are recorded but
# dispatch-inert in V1 (the import-fleet per-year seam is a named follow-up).
TARGET_KIND_VOCAB: frozenset[str] = frozenset(
    {"link", "interface", "import_tranche", "intra_zonal"}
)

# What the published MW measures (rule 14: a line thermal rating is NOT an
# interface-TTC uplift; a thermal_rating row must reconcile in mapping_note).
CAPACITY_BASIS_VOCAB: frozenset[str] = frozenset(
    {"thermal_rating", "interface_uplift", "converter_rating"}
)

MAPPING_CONFIDENCE_VOCAB: frozenset[str] = frozenset(
    {"exact", "reconciled", "ambiguous"}
)

_STRING_COLS = (
    "iso",
    "row_id",
    "project_id",
    "project_name",
    "sponsor",
    "status_tier",
    "instrument",
    "instrument_id",
    "target_kind",
    "from_zone",
    "to_zone",
    "interface_name",
    "capacity_basis",
    "mapping_confidence",
    "mapping_note",
    "superseding_instrument",
    "source_url",
    "source_doc",
    "notes",
)
_INT_COLS = ("in_service_year", "in_service_month")
_FLOAT_COLS = ("delta_mw", "delta_mw_reverse")
_DATETIME_COLS = ("instrument_date", "accessed", "superseding_instrument_date")
_BOOL_COLS = ("superseded",)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's transmission-expansion source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (``"ERCOT"``, ``"CAISO"``, ``"PJM"``, ``"MISO"``, ``"NYISO"``,
        ``"NEISO"``).
    source_note:
        One-line description of the ISO's committed-project source, for
        reviewers (documentation only).
    parse:
        Optional custom reader ``(csv_path: Path, spec: IsoSpec) -> DataFrame``
        for a native (non-unified-CSV) source. Defaults to
        :func:`parse_unified_csv`.
    """

    iso: str
    source_note: str = ""
    parse: Callable[["Path", "IsoSpec"], pd.DataFrame] | None = field(default=None)


# The registry every ISO module populates at import time.
REGISTRY: dict[str, IsoSpec] = {}

# ISO submodules to import so their register() calls run. Missing modules (an
# ISO not yet implemented) are skipped, so intake waves land independently.
_ISO_MODULES: tuple[str, ...] = ("ercot", "pjm", "miso", "nyiso", "neiso", "caiso")
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
    """Path of an ISO's raw transmission-expansion CSV extract."""
    return raw_root / DATATYPE / f"{iso.lower()}.csv"


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order.

    Missing optional columns are filled with nulls so a source that omits an
    optional field still yields a schema-shaped frame. Integer columns that
    allow nulls (``in_service_month``) become pandas nullable ``Int64``; the
    non-nullable ``in_service_year`` is checked downstream by
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
    out = out.sort_values(["iso", "in_service_year", "row_id"]).reset_index(drop=True)
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

    Complements :func:`scripts.lib.clean_io.validate_df` (dtypes, nulls,
    naming) with the value-level rules the schema cannot express: the closed
    status/kind/basis/confidence vocabularies, per-kind column requirements
    (a ``link`` row names both zones, an ``interface`` row its limit, an
    ``import_tranche`` row its receiving zone), the ``intra_zonal`` zero-delta
    rule, non-negative deltas, non-empty mapping notes, a valid month range,
    and that a superseded row cites its counter-instrument. Raises
    :class:`ValueError` on any violation; returns ``df`` on success.

    Zone/link *resolvability* against the live topology is checked in
    ``scripts/data/curate_transmission_expansion.py`` (it needs the model's
    :func:`~market_sim.config.iso_configs.get_iso_config`), not here.
    """
    problems: list[str] = []

    def _bad_vocab(col: str, vocab: frozenset[str]) -> None:
        bad = sorted(set(df[col].dropna()) - vocab)
        if bad:
            problems.append(f"{col} not in vocab: {bad}")

    _bad_vocab("status_tier", STATUS_TIER_VOCAB)
    _bad_vocab("target_kind", TARGET_KIND_VOCAB)
    _bad_vocab("capacity_basis", CAPACITY_BASIS_VOCAB)
    _bad_vocab("mapping_confidence", MAPPING_CONFIDENCE_VOCAB)

    months = pd.to_numeric(df["in_service_month"], errors="coerce").dropna()
    if not months.between(1, 12).all():
        problems.append("in_service_month has value(s) outside 1-12")

    delta = pd.to_numeric(df["delta_mw"], errors="coerce")
    if bool((delta < 0).any()) or bool(delta.isna().any()):
        problems.append("delta_mw must be present and >= 0 on every row")
    rev = pd.to_numeric(df["delta_mw_reverse"], errors="coerce")
    if bool((rev.dropna() < 0).any()):
        problems.append("delta_mw_reverse must be >= 0 where present")

    kind = df["target_kind"].astype("string")
    intra = kind == "intra_zonal"
    if bool((delta[intra] != 0.0).any()):
        problems.append(
            "intra_zonal row(s) with delta_mw != 0 (research rows are "
            "dispatch-inert by schema; map to a link/interface instead)"
        )
    link = kind == "link"
    if bool((df.loc[link, "from_zone"].isna() | df.loc[link, "to_zone"].isna()).any()):
        problems.append("link row(s) missing from_zone/to_zone")
    iface = kind == "interface"
    if bool(df.loc[iface, "interface_name"].isna().any()):
        problems.append("interface row(s) missing interface_name")
    tranche = kind == "import_tranche"
    if bool(df.loc[tranche, "to_zone"].isna().any()):
        problems.append("import_tranche row(s) missing to_zone (receiving zone)")

    note = df["mapping_note"].astype("string")
    if bool((note.isna() | (note.str.len() == 0)).any()):
        problems.append("mapping_note is required on every row (rule 14)")

    superseded_no_cite = df["superseded"].astype(bool) & (
        df["superseding_instrument"].isna()
        | (df["superseding_instrument"].astype("string").str.len() == 0)
    )
    if bool(superseded_no_cite.any()):
        problems.append(
            f"{int(superseded_no_cite.sum())} superseded row(s) miss "
            "superseding_instrument"
        )

    dup = df.duplicated(subset=["iso", "row_id"], keep=False)
    if bool(dup.any()):
        problems.append(f"{int(dup.sum())} duplicate (iso, row_id) key row(s)")

    if problems:
        raise ValueError(
            "transmission-expansion tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(csv_path: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the default parser) into a canonical frame.

    Expects ``<raw>/transmission-expansion/<iso>.csv`` with the canonical
    columns (as produced by the retrieval/grounding sessions). Returns an empty
    (but correctly-shaped) frame when the CSV is absent or has no data rows, so
    ``curate`` can skip an ISO whose registry has not landed yet (DATA NEEDED).
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
            f"(is scripts/lib/transmission_expansion/{iso.lower()}.py present?)"
        )
    reader = spec.parse or parse_unified_csv
    df = reader(raw_csv_for(spec.iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df)
    return df
