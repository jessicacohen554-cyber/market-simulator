"""Read adapter for ERCOT's RTC+B-era NP3-965 SCED Gen Resource disclosure.

**Authority.** ``docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md``
card **D**, signature **D1** (owner, 2026-08-11): *"authorize, scoped to a READ
ADAPTER"* — map the RTC+B member onto the existing schema; **no mechanism, no
re-derive of frozen artifacts, no keeper movement**. Nothing in this module
writes a ``ScenarioConfig`` field, touches a solve path, mints a clean datatype
or consults a residual.

**What broke.** ERCOT's Real-Time Co-optimization + Batteries (RTC+B) go-live
changed the NP3-965 Gen Resource member format at publications **2026-02-02
onward**, i.e. deliveries **2025-12-05..31** (27 parts, 8.66M rows). Measured
against a pre-RTC+B shard (188 columns), the RTC+B parts carry 193 or 195:

===========================  =====================================================
change                       columns
===========================  =====================================================
**REMOVED, no successor**    ``HASL``, ``LASL``
**RENAMED (lossless)**       ``Telemetered Net Output `` -> ``Telemetered Net Output``
                             (the trailing space is dropped; same telemetered
                             quantity — the equivalence ``ercot123.NETOUT_COLS``
                             already coalesces)
**SUPERSEDED (redefined)**   the six ``Ancillary Service <svc>`` responsibility
                             columns -> ``AS Awards <svc>`` + ``AS Capability
                             <svc>``, with ``RRS`` disaggregated into
                             ``RRSPFR``/``RRSUFR``/``RRSFFR`` and ``NSRS``
                             renamed ``NSPIN``
**ADDED**                    ``Ramp Rate Up``/``Ramp Rate Down``; the ``AS
                             Awards``/``AS Capability`` blocks (the 195-column
                             variant adds ``AS Capability RRSPF``/``RRSFF``)
===========================  =====================================================

``HASL`` is a required read column of **every** corpus consumer
(``derive_ercot_sced_offer_wall`` / ``derive_ercot_faststart_pool`` /
``sced_corpus_instruments`` / ``derive_coal_perplant_offer``), so these parts
crash the derives outright — the ercot-95/97 defect class. They are quarantined
at ``data/raw/ercot/SCED/rtcb-format-2026/``, **invisible to those consumers'
non-recursive globs**, bytes intact (see the corpus README).

**THE BOUNDARY — why the quarantine directory is load-bearing.** RTC+B rows are
delivery **2025**-12-05..31, so they sit *inside* delivery year 2025 and the
existing lanes' row filter cannot see them:
``derive_ercot_sced_offer_wall._sced_source_files(2025)`` selects publications
(2025-02 .. 2026-03) — which **includes** 2026-02 and 2026-03 — and
``_delivery_year_rows(df, 2025)`` **keeps** a 2025-12-31 stamp. The *only* thing
holding the line is that the parts live in a subdirectory the non-recursive
globs never reach. This module therefore never registers the quarantine
directory as a corpus root, and offers :func:`assert_pre_rtcb_files` /
:func:`assert_no_rtcb_rows` so a lane can assert the line positively.

**Every existing SCED-corpus lane stops at delivery 2025-12-04**
(:data:`PRE_RTCB_LAST_DELIVERY`). Reading past it is this adapter's job and
this adapter's only job.

**The two contract promises.**

1. **Removed columns are explicitly absent, never silently NaN-filled.** The
   returned frame has no ``HASL``/``LASL`` column at all, and asking for one
   raises :class:`ScedFormatBreakError` naming the break. A NaN-filled ``HASL``
   would be an invented telemetered quantity flowing into an identification —
   rule 13 ``[R-MEASURED]``. Same for the ``Ancillary Service *`` block: an AS
   *award* under RTC+B is a differently-defined quantity from the legacy
   *responsibility* (different null convention — legacy is dense ``0``, RTC+B is
   sparse ``''``) and ``RRS`` has no 1:1 successor at all, so the adapter refuses
   to serve them under the legacy names rather than guess an aggregation.
2. **Every row carries a format flag** (:data:`SCED_FORMAT_COLUMN`), so a frame
   that has been through this adapter is self-identifying downstream.

The frame contract is otherwise exactly what the existing readers get from
``pd.read_parquet``: the verbatim all-string CSV copy, unused curve steps as
EMPTY STRINGS, ``MM/DD/YYYY HH:MM:SS`` Central Prevailing Time stamps. Numeric
coercion and the CPT->CST conversion stay with the consumer, unchanged.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

REPO = Path(__file__).resolve().parents[2]

#: The NP3-965 publication-month corpus root. Pre-RTC+B parts live here at the
#: top level and are read by the existing consumers' non-recursive globs.
SCED_CORPUS_DIR: Path = REPO / "data" / "raw" / "ercot" / "SCED"

#: The RTC+B-format quarantine. A SUBDIRECTORY on purpose: it is what makes the
#: 27 parts invisible to every ``*.parquet`` / ``YYYY-MM.part*.parquet`` glob in
#: ``scripts/data`` and ``scripts/lib``. Never add this to a corpus-root tuple.
RTCB_DIR: Path = SCED_CORPUS_DIR / "rtcb-format-2026"

#: Last delivery date carried in the pre-RTC+B format (publication 2026-02-01).
#: Every existing SCED-corpus lane stops here.
PRE_RTCB_LAST_DELIVERY: date = date(2025, 12, 4)

#: First delivery date carried in the RTC+B format (publication 2026-02-02).
RTCB_FIRST_DELIVERY: date = date(2025, 12, 5)

#: Column stamped on every row this adapter returns (contract promise 2).
SCED_FORMAT_COLUMN: str = "sced_format"

#: Flag value for the pre-RTC+B (188-column) disclosure format.
FORMAT_PRE_RTCB: str = "pre-rtcb"

#: Flag value for the RTC+B-era (193/195-column) disclosure format.
FORMAT_RTCB: str = "rtcb-2026"

#: The disclosure timestamp format, identical across the break (CPT).
SCED_TIMESTAMP_FORMAT: str = "%m/%d/%Y %H:%M:%S"

#: RTC+B spelling -> canonical (pre-RTC+B) spelling, for the changes that are
#: LOSSLESS renames of the same quantity. Only one qualifies: the net-output
#: trailing space. ``ercot123.NETOUT_COLS`` already treats the two spellings as
#: one quantity and coalesces them, so serving the canonical name here keeps the
#: frame contract identical rather than asserting anything new.
RENAMED_COLUMNS: dict[str, str] = {
    "Telemetered Net Output": "Telemetered Net Output ",
}

#: Canonical column -> why it cannot be served. REMOVED outright by RTC+B: the
#: quantity is not published in any form, so there is nothing to map.
REMOVED_COLUMNS: dict[str, str] = {
    "HASL": (
        "High Ancillary Service Limit is REMOVED by the RTC+B disclosure "
        "format and has no successor column — under RTC+B the AS reservation "
        "is not netted into a telemetered limit. It is not recoverable from "
        "this member."
    ),
    "LASL": (
        "Low Ancillary Service Limit is REMOVED by the RTC+B disclosure "
        "format and has no successor column (the down-direction counterpart "
        "of HASL)."
    ),
}

#: Canonical column -> the RTC+B columns that carry the information instead.
#: These are NOT served under the legacy name: an AS *award* is a differently
#: defined quantity from the legacy *responsibility* (legacy is dense, carrying
#: an explicit ``0``; the RTC+B award block is sparse, carrying ``''`` for "no
#: award"), and ``Ancillary Service RRS`` has no 1:1 successor at all — RTC+B
#: disaggregates RRS into PFR/UFR/FFR, so reconstituting it would be an
#: unverified aggregation, i.e. a construction rather than a read. Out of the
#: card-D read-adapter scope; the RTC+B-native columns are served under their
#: own names for a future authorized session to work from.
SUPERSEDED_COLUMNS: dict[str, tuple[str, ...]] = {
    "Ancillary Service REGUP": ("AS Awards REGUP", "AS Capability REGUP"),
    "Ancillary Service REGDN": ("AS Awards REGDN", "AS Capability REGDN"),
    "Ancillary Service RRS": (
        "AS Awards RRSPFR",
        "AS Awards RRSUFR",
        "AS Awards RRSFFR",
    ),
    "Ancillary Service RRSFFR": ("AS Awards RRSFFR",),
    "Ancillary Service NSRS": ("AS Awards NSPIN", "AS Capability NSPIN"),
    "Ancillary Service ECRS": ("AS Awards ECRS", "AS Capability ECRS"),
}


class ScedFormatBreakError(KeyError):
    """A pre-RTC+B column was requested from an RTC+B-format part.

    Raised instead of returning a NaN-filled column, so a removed telemetered
    quantity can never enter an identification path as an invented value
    (rule 13 ``[R-MEASURED]``).
    """

    def __str__(self) -> str:  # KeyError repr()s its arg; keep the message plain
        return self.args[0] if self.args else ""


class ScedQuarantineLeakError(RuntimeError):
    """RTC+B-format data reached a lane that stops at the pre-RTC+B boundary."""


def rtcb_part_files(root: Path | None = None) -> list[Path]:
    """The quarantined RTC+B-format parts, sorted by name.

    Args:
        root: Quarantine directory. Defaults to :data:`RTCB_DIR`.

    Returns:
        Sorted ``YYYY-MM.partNNNN.parquet`` paths (publication-month keyed, as
        everywhere in this corpus — delivery is ~2 months earlier).
    """
    d = RTCB_DIR if root is None else Path(root)
    return sorted(d.glob("[0-9][0-9][0-9][0-9]-[0-1][0-9].part*.parquet"))


def _file_columns(path: Path) -> list[str]:
    """Physical column names of a parquet part, in file order."""
    import pyarrow.parquet as pq

    return list(pq.ParquetFile(path).schema_arrow.names)


def canonical_columns(path: Path) -> list[str]:
    """Canonical column names an RTC+B part can serve, in file order.

    RTC+B-native columns keep their own names; the :data:`RENAMED_COLUMNS`
    entries are reported under their canonical (pre-RTC+B) spelling. Columns in
    :data:`REMOVED_COLUMNS` / :data:`SUPERSEDED_COLUMNS` never appear.
    """
    return [RENAMED_COLUMNS.get(c, c) for c in _file_columns(path)]


def _resolve_requested(
    requested: Sequence[str], available: list[str], path: Path
) -> list[str]:
    """Canonical requested names -> physical names, or raise on a broken column.

    Raises:
        ScedFormatBreakError: A requested column was removed or superseded by
            the RTC+B format break, or is simply absent from the part. Never
            NaN-filled.
    """
    to_physical = {RENAMED_COLUMNS.get(c, c): c for c in available}
    physical: list[str] = []
    for name in requested:
        if name in to_physical:
            physical.append(to_physical[name])
            continue
        if name in REMOVED_COLUMNS:
            raise ScedFormatBreakError(
                f"{name!r} is not available from {path.name}: "
                f"{REMOVED_COLUMNS[name]} "
                "It is NOT NaN-filled — read a pre-RTC+B part (delivery on or "
                f"before {PRE_RTCB_LAST_DELIVERY:%Y-%m-%d}) if you need it."
            )
        if name in SUPERSEDED_COLUMNS:
            succ = ", ".join(repr(s) for s in SUPERSEDED_COLUMNS[name])
            raise ScedFormatBreakError(
                f"{name!r} is not available from {path.name}: the RTC+B format "
                f"replaces it with {succ}, which is a differently-defined "
                "quantity (award/capability vs responsibility, and RRS is "
                "disaggregated into PFR/UFR/FFR). Mapping it onto the legacy "
                "name is a construction, not a read, and is outside the card-D "
                "read-adapter scope — request the successor column(s) directly."
            )
        raise ScedFormatBreakError(
            f"{name!r} is absent from {path.name} and is not a known RTC+B "
            "format change; it is not NaN-filled. Available names: "
            f"{sorted(set(RENAMED_COLUMNS.get(c, c) for c in available))}"
        )
    return physical


def read_rtcb_part(path: Path, columns: Sequence[str] | None = None) -> pd.DataFrame:
    """Read one RTC+B-format part into the canonical SCED frame contract.

    The frame is the verbatim all-string parquet copy the existing readers get
    from ``pd.read_parquet`` — unused curve steps are EMPTY STRINGS, timestamps
    are ``MM/DD/YYYY HH:MM:SS`` CPT — with two differences, both deliberate:
    :data:`RENAMED_COLUMNS` are served under their canonical pre-RTC+B spelling,
    and every row carries :data:`SCED_FORMAT_COLUMN` = :data:`FORMAT_RTCB`.
    Numeric coercion and the CPT->CST conversion stay with the consumer.

    Args:
        path: An RTC+B-format part (193- or 195-column variant).
        columns: Canonical column names to read. ``None`` reads every column
            the part carries.

    Returns:
        The frame, with removed/superseded columns absent rather than NaN-filled.

    Raises:
        ScedFormatBreakError: A requested column was removed or superseded by
            the format break, or is absent from the part.
    """
    path = Path(path)
    available = _file_columns(path)
    if columns is None:
        physical = available
    else:
        physical = _resolve_requested(list(columns), available, path)
    df = pd.read_parquet(path, columns=physical)
    df = df.rename(
        columns={c: RENAMED_COLUMNS[c] for c in physical if c in RENAMED_COLUMNS}
    )
    df[SCED_FORMAT_COLUMN] = FORMAT_RTCB
    return df


def read_rtcb(
    paths: Iterable[Path] | None = None, columns: Sequence[str] | None = None
) -> pd.DataFrame:
    """Read the quarantined RTC+B parts into one canonical frame.

    Args:
        paths: Parts to read. Defaults to every part in :data:`RTCB_DIR`.
        columns: Canonical column names; ``None`` reads the per-part
            intersection, matching the corpus convention that the column
            inventory drifts at ERCOT's edge (the 193- vs 195-column variants).

    Returns:
        The concatenated frame, every row flagged :data:`FORMAT_RTCB`.

    Raises:
        FileNotFoundError: No RTC+B part was found.
        ScedFormatBreakError: A requested column was removed or superseded.
    """
    files = list(paths) if paths is not None else rtcb_part_files()
    if not files:
        raise FileNotFoundError(f"no RTC+B-format parts under {RTCB_DIR}")
    if columns is None:
        shared = set(canonical_columns(files[0]))
        for f in files[1:]:
            shared &= set(canonical_columns(f))
        # Preserve first-file order; the intersection is order-insensitive.
        columns = [c for c in canonical_columns(files[0]) if c in shared]
    frames = [read_rtcb_part(f, columns=columns) for f in files]
    return pd.concat(frames, ignore_index=True)


def delivery_timestamps(df: pd.DataFrame) -> pd.Series:
    """Parse ``SCED Time Stamp`` (CPT, as disclosed) to datetimes.

    The disclosure clock, not the model clock: no CPT->CST conversion is applied
    here, exactly as the existing readers leave it until they choose to convert.
    """
    return pd.to_datetime(df["SCED Time Stamp"], format=SCED_TIMESTAMP_FORMAT)


def assert_pre_rtcb_files(files: Iterable[Path]) -> None:
    """Refuse a file list that reaches into the RTC+B quarantine.

    The positive form of the invisibility the quarantine subdirectory gives the
    consumers' non-recursive globs: a lane that selects its own shards can call
    this to assert the line rather than rely on the glob shape.

    Raises:
        ScedQuarantineLeakError: Any path lies inside :data:`RTCB_DIR`.
    """
    leaked = [Path(f) for f in files if Path(f).resolve().parent.name == RTCB_DIR.name]
    if leaked:
        raise ScedQuarantineLeakError(
            f"{len(leaked)} RTC+B-format part(s) reached a pre-RTC+B lane "
            f"(first: {leaked[0].name}). Every existing SCED-corpus lane stops "
            f"at delivery {PRE_RTCB_LAST_DELIVERY:%Y-%m-%d}; RTC+B parts are "
            "readable only through scripts.lib.sced_rtcb_adapter (card D / D1)."
        )


def assert_no_rtcb_rows(df: pd.DataFrame, where: str = "frame") -> None:
    """Refuse rows delivered on or after :data:`RTCB_FIRST_DELIVERY`.

    The row-level counterpart of :func:`assert_pre_rtcb_files`, and the check
    that matters most: RTC+B deliveries fall inside calendar year **2025**, so
    the lanes' ``_delivery_year_rows(df, 2025)`` filter does **not** exclude
    them. Only the delivery DATE separates the two formats.

    Args:
        df: A frame carrying ``SCED Time Stamp``.
        where: Label used in the error message.

    Raises:
        ScedQuarantineLeakError: Any row is delivered on/after the boundary.
    """
    if df.empty:
        return
    bad = delivery_timestamps(df).dt.date >= RTCB_FIRST_DELIVERY
    if bool(bad.any()):
        raise ScedQuarantineLeakError(
            f"{int(bad.sum())} of {len(df)} rows in {where} are delivered on or "
            f"after {RTCB_FIRST_DELIVERY:%Y-%m-%d}, the RTC+B format break. "
            f"Pre-RTC+B lanes stop at {PRE_RTCB_LAST_DELIVERY:%Y-%m-%d}; the "
            "delivery-year filter cannot catch this because both sides are "
            "delivery-2025."
        )
