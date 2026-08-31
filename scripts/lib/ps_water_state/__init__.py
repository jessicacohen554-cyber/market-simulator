"""Shared contract for the ``ps-water-state`` clean datatype.

Measured hourly pumped-storage plant operations — generation and pumping
energy, generation/pumping water flow, and upper/lower reservoir elevation and
storage — from the operator's own published plant records. This is the public
breach of the CAISO "hourly PS water-state" wall (FINDING-caiso141 §A/§B): the
Helms Pumped Storage Project (FERC P-2735) published its PG&E HEC-DSS hourly
operations record, 2001-01-01 .. 2022-09-30, as the PUBLIC Final License
Application Appendix B1 (Hydrology) xlsx on FERC eLibrary (accession
20240418-5301).

Every plant's record is reconciled onto ONE tidy frame declared in
``data/dictionary/schema/ps-water-state.schema.yaml``, at
``(iso, plant, interval_end_local)`` hourly grain.

Per-ISO logic lives in sibling modules (``caiso.py``, ...), each registering an
:class:`IsoSpec` via :func:`register`; shared code never branches on the ISO
name. A spec declares its :class:`PsSource` list — one entry per (plant,
snapshot file) — and each source names the ``reader`` that parses its
publisher's format. Adding a plant is one more :class:`PsSource`; adding an
ISO is one more module. See ``docs/adding-new-data-types.md``.

Rule 13 ``[R-MEASURED]``: an admissible measured *input* (a physical plant
operations record produced outside the electricity market), never a fit
target. Span limitation stated honestly: the Helms record ends 2022-09-30 and
does not cover the 2023–2025 training years; what it grounds is measured
multi-year hourly conduct. Adjudication:
``results/calibration/FINDING-caiso227-c3a-rootcause-ps-intake-2026-08-31.md``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "ps-water-state"

# Canonical tidy column order (matches the schema's key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "plant",
    "interval_end_local",
    "generation_mwh",
    "pumping_mwh",
    "flow_generation_cfs",
    "flow_pumping_cfs",
    "upper_elevation_ft",
    "upper_storage_af",
    "lower_elevation_ft",
    "lower_storage_af",
    "source_doc",
)

_STRING_COLS = ("iso", "plant", "source_doc")
_FLOAT_COLS = (
    "generation_mwh",
    "pumping_mwh",
    "flow_generation_cfs",
    "flow_pumping_cfs",
    "upper_elevation_ft",
    "upper_storage_af",
    "lower_elevation_ft",
    "lower_storage_af",
)

#: HEC-DSS missing-value sentinels as they appear in the published workbook:
#: -901 ("missing") and -902 ("no record"). Exact match only — any OTHER
#: negative value in a non-flow physical column is a format change and fails
#: loudly. FLOW columns keep the publisher's signed values: the Helms record
#: carries 276 negative ``flow_pumping_cfs`` hours (-795 .. -0.03, reverse-flow
#: metering during mode changeover), which are data, not sentinels.
HECDSS_SENTINELS: frozenset[float] = frozenset({-901.0, -902.0})

#: Columns whose published values may legitimately be negative (signed flows).
SIGNED_COLUMNS: frozenset[str] = frozenset({"flow_generation_cfs", "flow_pumping_cfs"})


@dataclass(frozen=True)
class PsSource:
    """One raw snapshot to parse: a plant's operations record and its reader.

    Attributes:
        plant: plant key, upper-case (e.g. ``HELMS``).
        filename: the snapshot's name under the ISO's raw directory.
        url: the public endpoint the snapshot was retrieved from (provenance).
        accession: FERC eLibrary accession number (or other docket citation)
            identifying the public filing the snapshot is part of.
        reader: name of the parser in :data:`READERS` that reads this
            publisher's format.
    """

    plant: str
    filename: str
    url: str
    accession: str = ""
    reader: str = "helms_fla_appb1_hourly"


_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("sources", tuple, field(default_factory=tuple)),
    ],
    package=__name__,
    iso_modules=("caiso",),
    raw_subpath=(DATATYPE,),
    string_cols=_STRING_COLS,
    float_cols=_FLOAT_COLS,
    sort_by=("plant", "interval_end_local"),
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for
_finalize_base = _R.finalize

# The Appendix B1 hourly sheet's fixed layout: sheet name, the pathname header
# rows above the data, and the (B Part, C Part) -> canonical column mapping.
# Column order in the sheet is asserted at parse time — a layout change in a
# future re-publication must fail loudly, not silently mis-map series.
_B1_SHEET = "Hourly PG&E Data"
_B1_SERIES: tuple[tuple[str, str, str], ...] = (
    # (B Part substring, C Part, canonical column)
    ("COURTRIGHT_RES", "ELEVATION", "upper_elevation_ft"),
    ("COURTRIGHT_RES", "STORAGE", "upper_storage_af"),
    ("WISHON_RES", "ELEVATION", "lower_elevation_ft"),
    ("WISHON_RES", "STORAGE", "lower_storage_af"),
    ("HELMS_PH", "FLOW-GENERATION", "flow_generation_cfs"),
    ("HELMS_PH", "GENERATION", "generation_mwh"),
    ("HELMS_PH", "FLOW-PUMPING", "flow_pumping_cfs"),
    ("HELMS_PH", "PUMPING", "pumping_mwh"),
)


def _clean_sentinels(series: pd.Series, name: str, path: Path) -> pd.Series:
    """Null the HEC-DSS sentinels; refuse other negatives outside signed cols."""
    out = pd.to_numeric(series, errors="coerce")
    out = out.mask(out.isin(list(HECDSS_SENTINELS)))
    if name not in SIGNED_COLUMNS:
        bad = out[out < 0]
        if len(bad):
            raise ValueError(
                f"{path.name}: {len(bad)} negative non-sentinel value(s) in "
                f"{name!r}, e.g. {bad.head(3).tolist()!r} — format change?"
            )
    return out


def parse_helms_fla_appb1_hourly(path: Path, source: PsSource) -> pd.DataFrame:
    """Parse the Helms FLA Appendix B1 hourly sheet into tidy rows.

    The sheet is a HEC-DSS export: rows 1–6 are the pathname parts (Part A–F),
    rows 7–11 the span/units/data-type block, and data rows follow with the
    hour-ending timestamp in column 1 and the eight series in columns 2–9. The
    series identity is asserted against :data:`_B1_SERIES` by the (B Part,
    C Part) header cells — positional trust only after that check passes.

    Timestamps carry sub-second float drift in later vintages (HEC-DSS time
    arithmetic, e.g. ``04:59:59.97`` for HE05); they are rounded to the nearest
    hour, and the resulting clock is asserted GAP-FREE hourly (the published
    record is a fixed-offset local standard clock with no DST events).

    Args:
        path: the immutable xlsx snapshot to read.
        source: the :class:`PsSource` describing the plant.

    Returns:
        A frame with the canonical columns except ``iso`` (stamped by the
        caller), one row per hour of the published span.

    Raises:
        ValueError: if the sheet layout, series headers, units, sentinel
            discipline, or clock continuity differ from the published form.
    """
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True)
    if _B1_SHEET not in wb.sheetnames:
        raise ValueError(f"{path.name}: sheet {_B1_SHEET!r} not found")
    ws = wb[_B1_SHEET]
    rows = ws.iter_rows(values_only=True)
    header: dict[str, tuple] = {}
    data: list[tuple] = []
    for row in rows:
        label = str(row[0]).strip() if row[0] is not None else ""
        if label.endswith(":") or label in ("Units", "Data Type"):
            header[label.rstrip(":").strip()] = row[1:9]
            continue
        if row[0] is not None:
            data.append(row[:9])
    for part in ("Part B", "Part C"):
        if part not in header:
            raise ValueError(f"{path.name}: header row {part!r} not found")
    for idx, (b_sub, c_val, column) in enumerate(_B1_SERIES):
        b_cell = str(header["Part B"][idx] or "")
        c_cell = str(header["Part C"][idx] or "").strip()
        if b_sub not in b_cell or c_cell != c_val:
            raise ValueError(
                f"{path.name}: column {idx + 2} is ({b_cell!r}, {c_cell!r}), "
                f"expected ({b_sub!r}*, {c_val!r}) for {column!r}"
            )

    frame = pd.DataFrame(
        data, columns=["interval_end_local", *(c for _, _, c in _B1_SERIES)]
    )
    stamps = pd.to_datetime(frame["interval_end_local"]).dt.round("h")
    step = stamps.diff().dropna()
    if not (step == pd.Timedelta(hours=1)).all():
        gaps = step[step != pd.Timedelta(hours=1)]
        raise ValueError(
            f"{path.name}: clock not gap-free hourly — {len(gaps)} "
            f"irregular step(s), first at {stamps[gaps.index[0]]}"
        )
    out = pd.DataFrame({"interval_end_local": stamps})
    for _, _, column in _B1_SERIES:
        out[column] = _clean_sentinels(frame[column], column, path)
    out["plant"] = source.plant
    out["source_doc"] = source.filename
    return out


#: Publisher-format readers, looked up by :attr:`PsSource.reader`. A plant
#: publishing a different layout registers its own reader here rather than
#: adding a branch to the shared parse path.
READERS: dict[str, object] = {
    "helms_fla_appb1_hourly": parse_helms_fla_appb1_hourly,
}


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to canonical dtypes/order (timestamp aware).

    Wraps the registry factory's generic finalizer (strings + floats) to also
    land ``interval_end_local`` as tz-naive ``datetime64[ns]`` — the one dtype
    this datatype's schema declares beyond the generic pair.
    """
    out = _finalize_base(df)
    out["interval_end_local"] = pd.to_datetime(out["interval_end_local"]).astype(
        "datetime64[ns]"
    )
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check the value-level rules the schema cannot express.

    Complements :func:`scripts.lib.clean_io.validate_df` with: no negative
    values outside the signed flow columns (sentinels must be nulled at parse
    time; flows keep the publisher's sign — see :data:`SIGNED_COLUMNS`), and
    uniqueness of the ``(iso, plant, interval_end_local)`` key. An hour may
    carry BOTH generation and pumping (mode changeover within the hour — 1,921
    such hours on the Helms record), so no exclusivity is asserted. Raises
    :class:`ValueError` on any violation; returns ``df`` on success.
    """
    problems: list[str] = []
    for column in _FLOAT_COLS:
        if column in SIGNED_COLUMNS:
            continue
        negative = df[df[column] < 0]
        if len(negative):
            problems.append(f"{len(negative)} negative value(s) in {column}")
    key = ["iso", "plant", "interval_end_local"]
    dupes = df.duplicated(subset=key).sum()
    if dupes:
        problems.append(f"{int(dupes)} duplicate row(s) on key {key}")
    if problems:
        raise ValueError(
            "ps-water-state tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw snapshots into a validated tidy frame.

    Walks the ISO spec's :class:`PsSource` list, reads each snapshot with the
    reader its source names, stamps the ISO, and concatenates. A source whose
    snapshot has not landed yet is skipped, so an ISO can be registered before
    all of its plants are retrieved.
    """
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/ps_water_state/{iso.lower()}.py present?)"
        )
    raw_dir = raw_dir_for(spec.iso, raw_root)
    frames: list[pd.DataFrame] = []
    for source in spec.sources:
        path = raw_dir / source.filename
        if not path.is_file():
            continue
        reader = READERS.get(source.reader)
        if reader is None:
            raise ValueError(
                f"{spec.iso}: unknown reader {source.reader!r}; "
                f"registered: {sorted(READERS)}"
            )
        frames.append(reader(path, source))
    if not frames:
        return finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))
    df = pd.concat(frames, ignore_index=True)
    df["iso"] = spec.iso
    return validate_tidy(finalize(df))
