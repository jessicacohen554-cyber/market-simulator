"""Shared contract for the ``gas-ofo-events`` clean datatype.

An Operational Flow Order (OFO) is a gas utility's tariff instrument for
forcing shippers' daily deliveries into balance with their burn when the
pipeline/storage system cannot absorb the imbalance. Each declaration is a
**physical gas-system availability event** on one gas day, carrying a published
escalation stage and a published imbalance tolerance band. The LOW side
(under-delivery penalized) is the winter gas-*deliverability* instrument that
binds when a cold snap strands gas-fired generation; the HIGH side is the
converse linepack-surplus instrument.

Every declaring utility's event ledger is reconciled onto ONE tidy frame
declared in ``data/dictionary/schema/gas-ofo-events.schema.yaml``, at
``(iso, utility, gas_day, side)`` grain.

Per-ISO logic lives in sibling modules (``caiso.py``, ...), each registering an
:class:`IsoSpec` via :func:`register`; shared code never branches on the ISO
name. A spec declares its :class:`OfoSource` list — one entry per (utility,
side, snapshot file) — and each source names the ``reader`` that parses its
publisher's format. Adding a second utility to an ISO is one more
:class:`OfoSource`; adding an ISO is one more module. See
``docs/adding-new-data-types.md``.

Rule 13 ``[R-MEASURED]``: this is an admissible measured *input* (a published
physical event with a forward analogue), never a fit target. The adjudication
is ``results/calibration/FINDING-caiso226-ofo-intake-2026-08-31.md`` §4–§5.
"""

from __future__ import annotations

import datetime as _dt
import html as _html
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "gas-ofo-events"

# Canonical tidy column order (matches the schema's key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "utility",
    "gas_day",
    "side",
    "stage",
    "tolerance_pct",
    "waived",
    "source_doc",
)

#: The two sides an order can be declared on. ``low`` penalizes under-delivery
#: (tolerance published negative) and is the gas-deliverability instrument;
#: ``high`` penalizes over-delivery (tolerance published positive).
SIDE_VOCAB: frozenset[str] = frozenset({"low", "high"})

#: Published escalation stages, as printed. ``EFO`` is an Emergency Flow Order
#: — a distinct instrument the utility prints in the same ledger, NOT an OFO
#: stage — and is deliberately left unranked (no numeric severity is assigned
#: to it here; a consuming mechanism decides how to treat it).
STAGE_VOCAB: frozenset[str] = frozenset(
    {"1", "2", "3", "3.1", "3.2", "3.3", "4", "5", "EFO"}
)

_STRING_COLS = ("iso", "utility", "side", "stage", "source_doc")
_FLOAT_COLS = ("tolerance_pct",)


@dataclass(frozen=True)
class OfoSource:
    """One raw snapshot to parse: a (utility, side) ledger and its reader.

    Attributes:
        utility: declaring gas utility / balancing entity (e.g. ``SOCALGAS``).
        side: ``low`` or ``high`` — which ledger this snapshot is.
        filename: the snapshot's name under the ISO's raw directory.
        url: the public endpoint the snapshot was retrieved from (provenance).
        reader: name of the parser in :data:`READERS` that reads this
            publisher's format. Defaults to the SoCalGas ENVOY table reader.
    """

    utility: str
    side: str
    filename: str
    url: str
    reader: str = "envoy_year_column_table"


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
    sort_by=("utility", "gas_day", "side"),
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
raw_dir_for = _R.raw_dir_for
_finalize_base = _R.finalize

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

# ENVOY ledger cell: "<Month> <day>, <Stage token>, <tolerance>%" with the
# stage segment absent on the pre-2018 high-OFO vintage and an optional
# "(WAIVED)" suffix. Examples:
#   "January 3, Stage 3.1, -5%"      "January 6, 5%"
#   "November 1, Stage 1, -5% (WAIVED)"        "December 29, EFO, 0%"
_CELL_RE = re.compile(
    r"^(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2})\s*,\s*"
    r"(?:(?P<stage>Stage\s+[\d.]+|EFO)\s*,\s*)?"
    r"(?P<tol>[-+]?\d+(?:\.\d+)?)\s*%"
    r"(?P<waived>\s*\(\s*WAIVED\s*\))?$",
    re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_HEADER_YEAR_RE = re.compile(r"<th[^>]*>\s*(\d{4})\s*</th>", re.IGNORECASE)
_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_CELL_TAG_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.IGNORECASE | re.DOTALL)


def _cell_text(raw: str) -> str:
    """Strip tags/entities from one ledger cell and normalize its whitespace."""
    text = _html.unescape(_TAG_RE.sub("", raw)).replace("\xa0", " ")
    return " ".join(text.split()).strip()


def parse_envoy_year_column_table(path: Path, source: OfoSource) -> pd.DataFrame:
    """Parse a SoCalGas ENVOY event-history ledger snapshot into tidy rows.

    ENVOY publishes both OFO histories as ONE table whose ``<th>`` header cells
    are years (newest first) and whose body cells hold one event each, as free
    text — ``"January 3, Stage 3.1, -5%"``. A cell's *column position* supplies
    the year, so the row is only reconstructable from (header year, cell text)
    together. Blank cells pad the shorter years and are skipped.

    The tolerance is taken **with its published sign** (negative on the low
    side, positive on the high side); the stage segment is absent on the
    pre-2018 high-OFO vintage and yields a null ``stage``.

    Args:
        path: the immutable HTML snapshot to read.
        source: the :class:`OfoSource` describing which ledger this is.

    Returns:
        A frame with the canonical columns except ``iso`` (stamped by the
        caller), one row per declared gas day.

    Raises:
        ValueError: if the snapshot has no year header row, or any non-blank
            cell does not match the published cell grammar (a format change
            must fail loudly rather than silently drop events).
    """
    text = path.read_text(encoding="latin-1")
    years = _HEADER_YEAR_RE.findall(text)
    if not years:
        raise ValueError(f"{path.name}: no <th> year header cells found")

    body_start = text.lower().find("<tbody")
    body_end = text.lower().find("</tbody>")
    body = text[body_start:body_end] if body_start >= 0 < body_end else text

    records: list[dict] = []
    unparsed: list[str] = []
    for row_html in _ROW_RE.findall(body):
        cells = _CELL_TAG_RE.findall(row_html)
        for index, cell_html in enumerate(cells):
            cell = _cell_text(cell_html)
            if not cell or index >= len(years):
                continue
            match = _CELL_RE.match(cell)
            if match is None:
                unparsed.append(cell)
                continue
            month = _MONTHS.get(match.group("month").lower())
            if month is None:
                unparsed.append(cell)
                continue
            stage_raw = match.group("stage")
            stage = (
                None
                if stage_raw is None
                else re.sub(r"^stage\s+", "", stage_raw.strip(), flags=re.IGNORECASE)
            )
            records.append(
                {
                    "utility": source.utility,
                    "gas_day": _dt.datetime(
                        int(years[index]), month, int(match.group("day"))
                    ),
                    "side": source.side,
                    "stage": stage.upper() if stage else None,
                    "tolerance_pct": float(match.group("tol")),
                    "waived": match.group("waived") is not None,
                    "source_doc": source.filename,
                }
            )
    if unparsed:
        raise ValueError(
            f"{path.name}: {len(unparsed)} ledger cell(s) did not match the "
            f"published grammar, e.g. {unparsed[:3]!r}"
        )
    return pd.DataFrame.from_records(records, columns=list(CANONICAL_COLUMNS[1:]))


#: Publisher-format readers, looked up by :attr:`OfoSource.reader`. A utility
#: publishing a different layout registers its own reader here rather than
#: adding a branch to the shared parse path.
READERS: dict[str, object] = {
    "envoy_year_column_table": parse_envoy_year_column_table,
}


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce a parsed frame to canonical dtypes/order (bool + date aware).

    Wraps the registry factory's generic finalizer, which only knows string and
    float columns, to also land ``waived`` as a real ``bool`` and ``gas_day``
    as tz-naive ``datetime64[ns]`` — the two dtypes this datatype's schema
    declares beyond the generic pair.
    """
    out = _finalize_base(df)
    out["waived"] = out["waived"].fillna(False).astype(bool)
    out["gas_day"] = pd.to_datetime(out["gas_day"]).astype("datetime64[ns]")
    return out


def validate_tidy(df: pd.DataFrame) -> pd.DataFrame:
    """Check the value-level rules the schema cannot express.

    Complements :func:`scripts.lib.clean_io.validate_df` with: the side and
    stage controlled vocabularies, the published tolerance sign convention
    (low negative-or-zero, high positive-or-zero), and uniqueness of the
    ``(iso, utility, gas_day, side)`` key. Raises :class:`ValueError` on any
    violation; returns ``df`` on success.
    """
    problems: list[str] = []
    bad_side = sorted(set(df["side"].dropna()) - SIDE_VOCAB)
    if bad_side:
        problems.append(f"side(s) not in vocab: {bad_side}")
    bad_stage = sorted(set(df["stage"].dropna()) - STAGE_VOCAB)
    if bad_stage:
        problems.append(f"stage(s) not in vocab: {bad_stage}")
    # Sign convention is the publisher's, not ours: a low order tightens
    # deliveries (negative band) and a high order loosens them (positive). A
    # flipped sign means the side was mis-assigned at parse time.
    wrong_low = df[(df["side"] == "low") & (df["tolerance_pct"] > 0)]
    if len(wrong_low):
        problems.append(f"{len(wrong_low)} low-side row(s) with positive tolerance")
    wrong_high = df[(df["side"] == "high") & (df["tolerance_pct"] < 0)]
    if len(wrong_high):
        problems.append(f"{len(wrong_high)} high-side row(s) with negative tolerance")
    key = ["iso", "utility", "gas_day", "side"]
    dupes = df.duplicated(subset=key).sum()
    if dupes:
        problems.append(f"{int(dupes)} duplicate row(s) on key {key}")
    if problems:
        raise ValueError(
            "gas-ofo-events tidy checks failed:\n  - " + "\n  - ".join(problems)
        )
    return df


def parse_iso(iso: str, raw_root: Path) -> pd.DataFrame:
    """Parse one registered ISO's raw snapshots into a validated tidy frame.

    Walks the ISO spec's :class:`OfoSource` list, reads each snapshot with the
    reader its source names, stamps the ISO, and concatenates. A source whose
    snapshot has not landed yet is skipped, so an ISO can be registered before
    all of its utilities are retrieved.
    """
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise ValueError(
            f"unknown ISO {iso!r}; registered: {sorted(REGISTRY)} "
            f"(is scripts/lib/gas_ofo_events/{iso.lower()}.py present?)"
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
