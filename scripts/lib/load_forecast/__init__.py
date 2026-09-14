"""Shared contract for the ``load-forecast`` clean datatype.

Each ISO's PUBLISHED long-term load forecast — ERCOT's LTLF, the CEC's
California Energy Demand forms, PJM's Load Forecast Report, the NYISO Gold
Book, the ISO-NE CELT and MISO's LTLF — reconciled onto ONE tidy frame declared
in ``data/dictionary/schema/load-forecast.schema.yaml``.

The per-ISO logic lives in sibling modules (``ercot.py``, ``caiso.py``, ...),
each registering an :class:`IsoSpec` via :func:`register`. Shared code never
branches on the ISO name — it looks the spec up in :data:`REGISTRY` — so a new
ISO or a new vintage is additive and parallel intake sessions never touch a
shared file (``docs/adding-new-data-types.md``).

**Two intake routes, and a spec may use both.** Where the publisher issues a
machine-readable workbook the spec supplies a ``parse`` hook that opens it with
``openpyxl`` (a project dependency), so a vintage refresh is *drop in the new
workbook and re-run*. Where the publisher issues only a PDF or a slide deck the
tables are transcribed once into ``data/raw/load-forecast/<iso>/<iso>.csv`` with
the canonical columns, and :func:`parse_unified_csv` reads it — the repo's
existing convention for publication PDFs, and what keeps a PDF/``.xlsb`` parser
out of ``pyproject.toml``. :func:`parse_iso` concatenates whichever of the two
an ISO has.

Rule 13 ``[R-MEASURED]`` posture: every row is a **forward-looking published
input** that regenerates from the next vintage and responds to changed
conditions — never a measured outcome, and never a target a model output is
pinned to. The historical rows a publication prints beside its forecast are
carried only so a CAGR can be anchored on the publication's own base year, and
they are labelled ``scenario="actual"``.

The registry scaffolding (``IsoSpec``, ``REGISTRY``, ``register``,
``load_registry``, ``raw_dir_for``) is built by the shared
:func:`scripts.lib.datatype_registry.make_registry` factory.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "load-forecast"

# Canonical tidy column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "edition",
    "vintage",
    "scenario",
    "published_case",
    "area",
    "area_type",
    "component",
    "metric",
    "year",
    "value",
    "unit",
    "basis",
    "source_doc",
    "source_page",
)

# Canonical scenario axis — the model's demand_growth_path / datacenter_load_path
# / electrification_path labels, plus "actual" for the historical rows a
# publication prints beside its forecast (carried so a CAGR can be anchored on
# the publication's own base year; never a scoring target, rule 13).
SCENARIOS: frozenset[str] = frozenset({"low", "mid", "high", "actual"})

# Areas are in the PUBLISHER's vocabulary; crosswalking onto model zones is the
# consumer's job (config/iso_configs.py owns those maps), never this datatype's.
AREA_TYPES: frozenset[str] = frozenset(
    {"iso", "source_zone", "state", "agency", "region", "planning_area"}
)

COMPONENTS: frozenset[str] = frozenset(
    {
        "total",
        "base_economic",
        # `data_center` ONLY where the publisher itself isolates data centres
        # (the CEC's Form 1.1c). A publisher reporting the wider category uses
        # `large_load`, and the DC share of it stays the consumer's declared
        # assumption rather than being folded in here.
        "data_center",
        "large_load",
        "ev",
        "heat_pump",
        "building_electrification",
        "solar_pv",
    }
)

# metric -> the unit it must carry. Peak metrics keep the PUBLISHER's own peak
# definition (coincident vs non-coincident, 50/50 vs 1-in-2); those are not
# interchangeable across publishers, which is why the raw README states each.
METRIC_UNITS: dict[str, str] = {
    "energy_gwh": "gwh",
    "summer_peak_mw": "mw",
    "winter_peak_mw": "mw",
    "annual_peak_mw": "mw",
    "stock_count": "count",
}

# `basis` is part of the KEY: ISO-NE's CELT publishes a Gross and a Net row for
# every energy and peak series, and they are different quantities. "unspecified"
# is the honest label for a publisher that does not draw the distinction —
# never a silent default onto "net".
BASES: frozenset[str] = frozenset({"net", "gross", "unspecified"})

_STRING_COLS = (
    "iso",
    "edition",
    "scenario",
    "published_case",
    "area",
    "area_type",
    "component",
    "metric",
    "unit",
    "basis",
    "source_doc",
    "source_page",
)
_FLOAT_COLS = ("value",)
_INT_COLS = ("vintage", "year")


def _check_spec(spec) -> None:
    """Reject a spec whose declared basis is outside the vocabulary."""
    if spec.default_basis is not None and spec.default_basis not in BASES:
        raise ValueError(
            f"{spec.iso}: default_basis {spec.default_basis!r} not in {sorted(BASES)}"
        )


_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("edition", str),
        ("vintage", int),
        ("default_basis", "str | None", None),
        ("parse", "Callable[[Path, 'IsoSpec'], pd.DataFrame] | None", None),
    ],
    package=__name__,
    iso_modules=(
        "ercot",
        "caiso",
        "pjm",
        "miso",
        "nyiso",
        "neiso",
        "spp",
        "nwpp",
        "soco",
    ),
    raw_subpath=(DATATYPE,),
    string_cols=_STRING_COLS,
    float_cols=_FLOAT_COLS,
    int_cols=_INT_COLS,
    sort_by=("scenario", "area", "component", "metric", "basis", "year"),
    register_check=_check_spec,
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to canonical dtypes/order, then restore the two integer columns.

    The shared factory's finalizer coerces every numeric column to ``float64``;
    ``vintage`` and ``year`` are declared ``int64`` in the schema and are always
    populated, so they are cast back here rather than shipped as floats.
    """
    out = _R.finalize(df)
    for col in _INT_COLS:
        if not out.empty:
            out[col] = out[col].astype("int64")
    return out


def empty_frame() -> pd.DataFrame:
    """An empty, correctly-shaped canonical frame (an ISO whose data has not landed)."""
    return _R.finalize(pd.DataFrame(columns=list(CANONICAL_COLUMNS)))


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check controlled vocabularies and metric/unit agreement before ``write_clean``.

    Complements :func:`scripts.lib.clean_io.validate_df` (dtypes, nulls, naming)
    with the value-level rules the schema cannot express: the scenario /
    area_type / component / metric / basis vocabularies, that ``unit`` agrees
    with ``metric``, that no (iso, edition, scenario, area, component, metric,
    year) key repeats, and that the frame carries no null value.

    Args:
        df: canonical tidy frame.

    Returns:
        ``df`` unchanged on success.

    Raises:
        ValueError: on any vocabulary, unit, duplicate-key or null violation.
    """
    problems: list[str] = []
    for col, vocab in (
        ("scenario", SCENARIOS),
        ("area_type", AREA_TYPES),
        ("component", COMPONENTS),
        ("metric", frozenset(METRIC_UNITS)),
    ):
        bad = sorted(set(df[col].dropna()) - vocab)
        if bad:
            problems.append(f"{col}(s) not in vocab: {bad}")
    bad_basis = sorted(set(df["basis"].dropna()) - BASES)
    if bad_basis:
        problems.append(f"basis(es) not in vocab: {bad_basis}")
    if bool(df["basis"].isna().any()):
        problems.append(
            f"{int(df['basis'].isna().sum())} row(s) have a null basis (a key column)"
        )

    known = df["metric"].isin(METRIC_UNITS)
    expected = df.loc[known, "metric"].map(METRIC_UNITS)
    mismatch = df.loc[known & (df["unit"] != expected.reindex(df.index))]
    if not mismatch.empty:
        pairs = sorted({(m, u) for m, u in zip(mismatch["metric"], mismatch["unit"])})
        problems.append(f"metric/unit disagreement: {pairs}")

    if bool(df["value"].isna().any()):
        problems.append(f"{int(df['value'].isna().sum())} row(s) have a null value")

    key = ["iso", "edition", "scenario", "area", "component", "metric", "basis", "year"]
    dupes = df.duplicated(subset=key, keep=False)
    if bool(dupes.any()):
        sample = df.loc[dupes, key].drop_duplicates().head(5).to_dict("records")
        problems.append(f"{int(dupes.sum())} duplicate key row(s), e.g. {sample}")

    if problems:
        raise ValueError(
            "load-forecast tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_unified_csv(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """Read an ISO's transcription CSV into a canonical frame.

    Expects ``<raw_dir>/<iso>.csv`` with the canonical columns, as produced when
    a publisher issues only a PDF or a slide deck. ``iso`` / ``edition`` /
    ``vintage`` are stamped from the spec when the CSV leaves them blank, and a
    blank ``basis`` falls back to ``spec.default_basis``. Returns an empty (but
    correctly-shaped) frame when the CSV is absent, so an ISO with only a native
    workbook — or one whose data has not landed — is skipped rather than raising.

    Args:
        raw_dir: the ISO's directory under ``data/raw/load-forecast``.
        spec: the ISO's registered spec.

    Returns:
        Canonical tidy frame (possibly empty).
    """
    csv = raw_dir / f"{spec.iso.lower()}.csv"
    if not csv.is_file():
        return empty_frame()
    # An ASSEMBLED transcription (NWPP-12's nwpp.csv, built from participant
    # IRPs) opens with a ``#`` provenance preamble ahead of the header row.
    # Skip exactly the leading comment lines — never ``comment="#"``, which
    # would also truncate any value carrying a ``#`` (a source_doc URL
    # fragment). Every other ISO's CSV has zero such lines and reads as before.
    preamble = 0
    with csv.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.startswith("#"):
                break
            preamble += 1
    raw = pd.read_csv(csv, dtype=str, skiprows=preamble)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw["iso"] = spec.iso
    for col, val in (("edition", spec.edition), ("vintage", spec.vintage)):
        if col not in raw.columns:
            raw[col] = val
        else:
            raw[col] = raw[col].fillna(val).replace({"": val})
    if spec.default_basis is not None:
        if "basis" not in raw.columns:
            raw["basis"] = spec.default_basis
        else:
            raw["basis"] = (
                raw["basis"]
                .fillna(spec.default_basis)
                .replace({"": spec.default_basis})
            )
    return finalize(raw)


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw inputs into a validated canonical frame.

    Concatenates the ISO's native-workbook rows (``spec.parse``, when the spec
    declares one) with its transcription-CSV rows (:func:`parse_unified_csv`),
    so a publisher that issues both — ERCOT — needs no special case anywhere.

    Args:
        iso: ISO label (case-insensitive).
        raw_root: root of the raw tree (``data/raw`` in production).

    Returns:
        Validated canonical tidy frame (possibly empty).

    Raises:
        ValueError: if the ISO is not registered, or the frame fails
            :func:`validate_tidy`.
    """
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/load_forecast/{iso.lower()}.py present?)"
        )
    raw_dir = raw_dir_for(spec.iso, raw_root)
    frames = [parse_unified_csv(raw_dir, spec)]
    if spec.parse is not None:
        frames.append(spec.parse(raw_dir, spec))
    df = (
        finalize(pd.concat([f for f in frames if not f.empty], ignore_index=True))
        if any(not f.empty for f in frames)
        else empty_frame()
    )
    if not df.empty:
        validate_tidy(df)
    return df
