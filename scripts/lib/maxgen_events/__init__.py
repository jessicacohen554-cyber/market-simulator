"""Shared contract for the ``maxgen-events`` clean datatype.

Declared capacity-emergency event windows — one row per (ISO, declaration,
region) at or above the lowest capacity-ladder rung (for MISO the pre-2026
ladder Capacity Advisory -> Maximum Generation Alert -> Warning -> Event
Steps 1-5). The M-1 datatype of the MISO price-formation lane
(``docs/handoffs/miso-price-formation-design-2026-07.md`` §3/M-1): a rule-13
availability-event registry in the same admissibility family as the CAMPD
outage windows (backcast/calibration overlay by construction; a forecast year
carries the class outage-rate machinery instead).

F4 discipline (pre-declared, absolute): a window with no primary document does
NOT enter the registry — windows are never reconstructed from price spikes or
from a model residual. Rows record exactly what the primary document declares.

Per-ISO facts (ladder vocabulary, region scopes, operating-time UTC offset)
live in sibling modules (``miso.py``, ...), each of which registers an
:class:`IsoSpec` via :func:`register`. Shared code never branches on the ISO
name — it looks the spec up in :data:`REGISTRY`, keeping new ISOs additive per
``docs/adding-new-data-types.md``.

Raw layout: ``data/raw/maxgen-events/<iso>/<iso>.csv`` with the canonical
columns except that window endpoints are ``start_local``/``end_local`` in the
ISO's *operating time* (hand-curation transcribes the primary document
verbatim); :func:`parse_unified_csv` converts to UTC via the spec's
``utc_offset_hours``.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATATYPE = "maxgen-events"

# Canonical column order (matches the schema).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "region",
    "level",
    "start_utc",
    "end_utc",
    "declared_precision",
    "source_url",
    "source_doc",
    "accessed",
    "notes",
)

# Closed ladder vocabulary (pre-2026 MISO capacity ladder; other ISOs extend
# via their own spec's level_vocab). Conservative Operations, transmission
# instruments and weather alerts are deliberately NOT members — they sit
# outside the capacity ladder (see the raw README).
LEVEL_VOCAB: frozenset[str] = frozenset(
    {
        "capacity_advisory",
        "maxgen_alert",
        "maxgen_warning",
        "maxgen_event_step1",
        "maxgen_event_step2",
        "maxgen_event_step3",
        "maxgen_event_step4",
        "maxgen_event_step5",
    }
)

PRECISION_VOCAB: frozenset[str] = frozenset({"hour", "day"})

_STRING_COLS = (
    "iso",
    "region",
    "level",
    "declared_precision",
    "source_url",
    "source_doc",
    "notes",
)


@dataclass(frozen=True)
class IsoSpec:
    """Declarative description of one ISO's declared-event source.

    Attributes
    ----------
    iso:
        Canonical ISO label used in the ``iso`` column and the clean partition
        (e.g. ``"MISO"``).
    regions:
        Closed vocabulary of declared-scope labels this ISO's documents use
        (canonical lowercase, e.g. ``{"footprint", "midwest", "south"}``).
    utc_offset_hours:
        Hours to ADD to the ISO's operating time to reach UTC (MISO market
        operations run on EST = UTC-5 year-round, so 5).
    level_vocab:
        Ladder vocabulary for this ISO (defaults to the shared
        :data:`LEVEL_VOCAB`).
    """

    iso: str
    regions: frozenset[str]
    utc_offset_hours: int
    level_vocab: frozenset[str] = field(default=LEVEL_VOCAB)


# The registry every ISO module populates at import time.
REGISTRY: dict[str, IsoSpec] = {}

# ISO submodules to import so their register() calls run. Missing modules (an
# ISO not yet implemented) are skipped, so intake waves land independently.
_ISO_MODULES: tuple[str, ...] = ("miso",)
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
    """Directory holding an ISO's raw maxgen-events inputs."""
    return raw_root / DATATYPE / iso.lower()


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to the canonical dtypes + column order."""
    out = df.copy()
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = pd.NA
    for col in _STRING_COLS:
        out[col] = out[col].astype("string")
    out["start_utc"] = pd.to_datetime(out["start_utc"], utc=True)
    out["end_utc"] = pd.to_datetime(out["end_utc"], utc=True)
    out["accessed"] = pd.to_datetime(out["accessed"])
    out = out[list(CANONICAL_COLUMNS)]
    out = out.sort_values(["iso", "start_utc", "level"]).reset_index(drop=True)
    return out


def validate_tidy(df: pd.DataFrame, spec: IsoSpec) -> pd.DataFrame:
    """Check the value-level rules the schema can't express.

    Complements :func:`scripts.lib.clean_io.validate_df` (dtypes/nulls/naming)
    with: level and region vocabularies, precision vocabulary, and
    window sanity (``end_utc`` strictly after ``start_utc``). Raises
    :class:`ValueError` on any violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_level = sorted(set(df["level"].dropna()) - spec.level_vocab)
    if bad_level:
        problems.append(f"level(s) not in vocab: {bad_level}")
    bad_region = sorted(set(df["region"].dropna()) - spec.regions)
    if bad_region:
        problems.append(f"region(s) not in vocab: {bad_region}")
    bad_precision = sorted(set(df["declared_precision"].dropna()) - PRECISION_VOCAB)
    if bad_precision:
        problems.append(f"declared_precision(s) not in vocab: {bad_precision}")
    inverted = df["end_utc"] <= df["start_utc"]
    if bool(inverted.any()):
        problems.append(f"{int(inverted.sum())} row(s) have end_utc <= start_utc")
    if problems:
        raise ValueError(
            "maxgen-events tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's unified CSV (the only parser) into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns except that the
    window endpoints are ``start_local``/``end_local`` in the ISO's operating
    time, transcribed verbatim from the primary document; they are converted
    to UTC by ADDING ``spec.utc_offset_hours``. Returns an empty (but
    correctly-shaped) frame when the CSV is absent so curation can skip an ISO
    whose data has not landed yet.
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    raw = pd.read_csv(csv, dtype=str)
    offset = pd.Timedelta(hours=spec.utc_offset_hours)
    raw["start_utc"] = (pd.to_datetime(raw.pop("start_local")) + offset).dt.tz_localize(
        "UTC"
    )
    raw["end_utc"] = (pd.to_datetime(raw.pop("end_local")) + offset).dt.tz_localize(
        "UTC"
    )
    return finalize(raw)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse and tidy-validate one ISO's registry from the raw tree."""
    spec = load_registry()[iso.upper()]
    df = parse_unified_csv(raw_dir_for(iso, raw_root), spec)
    if not df.empty:
        validate_tidy(df, spec)
    return df
