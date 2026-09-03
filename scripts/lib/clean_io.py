"""Shared clean-data writer and validator for all curation scripts.

Every parallel curation session writes its cleaned datatype through ONE seam —
:func:`write_clean` — so the ``data/clean`` tree is uniform regardless of which
session produced it. The writer validates a DataFrame against the datatype's
canonical schema (``data/dictionary/schema/<datatype>.schema.yaml``) before it
touches disk: column presence, dtypes, units, tz-aware UTC timestamps and
lower_snake_case naming. It then writes Parquet to the path resolved by
:func:`market_sim.config.paths.clean_path` and embeds the schema version and
source provenance in the Parquet key-value metadata. :func:`validate_clean`
reads a written file back and re-checks it against its embedded schema (a
round-trip guard for curation pipelines and tests).

This module is the contract referenced by the data dictionary; it deliberately
has no dependency on the model package beyond ``config.paths`` so curation
scripts can import it cheaply.

See ``data/dictionary/data-dictionary.md`` for the per-datatype overview.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
import subprocess
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.fs as pafs
import pyarrow.parquet as pq
import yaml

from market_sim.config import paths

# Directory holding the per-datatype canonical schemas.
SCHEMA_DIR: Path = paths.DICTIONARY_DIR / "schema"

# Parquet metadata keys (bytes once written) carrying our contract + provenance.
_META_PREFIX = "market_sim."

# lower_snake_case: starts with a lowercase letter, then lowercase / digit / _.
_SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class SchemaError(ValueError):
    """Raised when a DataFrame (or written file) violates its datatype schema."""


@dataclass(frozen=True)
class ColumnSpec:
    """One canonical column declaration from a schema YAML."""

    name: str
    dtype: str
    unit: str
    nullable: bool
    description: str = ""


@dataclass(frozen=True)
class Schema:
    """A loaded, parsed datatype schema."""

    datatype: str
    schema_version: int
    title: str
    description: str
    key_columns: tuple[str, ...]
    allow_additional_columns: bool
    columns: tuple[ColumnSpec, ...]

    @property
    def column_map(self) -> dict[str, ColumnSpec]:
        return {c.name: c for c in self.columns}

    def units(self) -> dict[str, str]:
        """Map of column name -> declared unit (for parquet metadata)."""
        return {c.name: c.unit for c in self.columns}


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------
def schema_path(datatype: str) -> Path:
    """Return the on-disk path of a datatype's schema YAML."""
    return SCHEMA_DIR / f"{datatype}.schema.yaml"


def load_schema(datatype: str) -> Schema:
    """Load and parse the canonical schema for ``datatype``.

    Raises :class:`SchemaError` if the schema file is missing or malformed.
    """
    path = schema_path(datatype)
    if not path.is_file():
        available = sorted(p.name for p in SCHEMA_DIR.glob("*.schema.yaml"))
        raise SchemaError(
            f"no schema for datatype {datatype!r} at {path} "
            f"(available: {', '.join(available) or 'none'})"
        )
    raw = yaml.safe_load(path.read_text())
    if not isinstance(raw, dict):
        raise SchemaError(f"schema {path} is not a mapping")
    try:
        columns = tuple(
            ColumnSpec(
                name=c["name"],
                dtype=c["dtype"],
                unit=c.get("unit", "none"),
                nullable=bool(c.get("nullable", True)),
                description=c.get("description", ""),
            )
            for c in raw["columns"]
        )
        schema = Schema(
            datatype=raw["datatype"],
            schema_version=int(raw["schema_version"]),
            title=raw.get("title", raw["datatype"]),
            description=raw.get("description", ""),
            key_columns=tuple(raw.get("key_columns", ())),
            allow_additional_columns=bool(raw.get("allow_additional_columns", False)),
            columns=columns,
        )
    except (KeyError, TypeError) as exc:
        raise SchemaError(f"malformed schema {path}: {exc}") from exc

    if schema.datatype != datatype:
        raise SchemaError(
            f"schema {path} declares datatype {schema.datatype!r}, expected {datatype!r}"
        )
    return schema


# ---------------------------------------------------------------------------
# dtype compatibility
# ---------------------------------------------------------------------------
def _dtype_ok(series: pd.Series, declared: str) -> tuple[bool, str]:
    """Check a pandas Series against a declared schema dtype.

    Returns ``(ok, detail)``; ``detail`` explains a failure. The check is
    deliberately lenient on width (float32 satisfies float64) but strict on
    kind, and enforces tz-aware UTC for ``datetime64[ns, UTC]``.
    """
    dtype = series.dtype
    declared = declared.strip()

    if declared == "datetime64[ns, UTC]":
        if not isinstance(dtype, pd.DatetimeTZDtype):
            return False, f"expected tz-aware UTC datetime, got {dtype}"
        if str(dtype.tz) != "UTC":
            return False, f"expected UTC tz, got {dtype.tz}"
        return True, ""

    if declared == "datetime64[ns]":
        # naive local wall-clock; tz-aware is NOT acceptable here.
        if isinstance(dtype, pd.DatetimeTZDtype):
            return False, f"expected tz-naive datetime, got tz-aware {dtype}"
        if not pd.api.types.is_datetime64_any_dtype(dtype):
            return False, f"expected datetime64[ns], got {dtype}"
        return True, ""

    if declared == "float64":
        if pd.api.types.is_float_dtype(dtype):
            return True, ""
        return False, f"expected float, got {dtype}"

    if declared == "int64":
        # Integer columns that allow nulls arrive as float (NaN) or nullable
        # Int64; accept both alongside plain ints.
        if pd.api.types.is_integer_dtype(dtype):
            return True, ""
        if pd.api.types.is_float_dtype(dtype):
            return True, ""  # nullable integer stored as float
        return False, f"expected integer, got {dtype}"

    if declared == "bool":
        if pd.api.types.is_bool_dtype(dtype):
            return True, ""
        # nullable boolean / object of bools
        if isinstance(dtype, pd.BooleanDtype) or pd.api.types.is_object_dtype(dtype):
            return True, ""
        return False, f"expected bool, got {dtype}"

    if declared == "string":
        if pd.api.types.is_string_dtype(dtype) or pd.api.types.is_object_dtype(dtype):
            return True, ""
        return False, f"expected string, got {dtype}"

    return False, f"unknown declared dtype {declared!r}"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate_df(
    df: pd.DataFrame, datatype: str, *, schema: Schema | None = None
) -> Schema:
    """Validate ``df`` against the canonical schema for ``datatype``.

    Checks, in order: column naming (lower_snake_case), no unexpected columns
    (unless the schema allows them), all key + non-nullable columns present,
    per-column dtype compatibility, non-nullable columns free of nulls, and
    tz-aware UTC on UTC timestamp columns. Raises :class:`SchemaError` with all
    problems collected, and returns the resolved :class:`Schema` on success.
    """
    schema = schema or load_schema(datatype)
    cols = schema.column_map
    problems: list[str] = []

    # 1. Naming convention on every column actually present.
    for name in df.columns:
        if not _SNAKE_RE.match(str(name)):
            problems.append(f"column {name!r} is not lower_snake_case")

    # 2. Unexpected columns (only when the schema is closed).
    if not schema.allow_additional_columns:
        extra = [c for c in df.columns if c not in cols]
        if extra:
            problems.append(f"unexpected columns not in schema: {sorted(extra)}")

    # 3. Required columns present: keys plus any non-nullable declared column.
    required = set(schema.key_columns) | {
        c.name for c in schema.columns if not c.nullable
    }
    missing = [c for c in sorted(required) if c not in df.columns]
    if missing:
        problems.append(f"missing required columns: {missing}")

    # 4. Per-column dtype + nullability for declared columns that are present.
    for name in df.columns:
        spec = cols.get(name)
        if spec is None:
            continue  # additional column on an open schema; nothing to check
        ok, detail = _dtype_ok(df[name], spec.dtype)
        if not ok:
            problems.append(f"column {name!r}: {detail}")
        if not spec.nullable and name in df.columns and df[name].isna().any():
            n = int(df[name].isna().sum())
            problems.append(f"non-nullable column {name!r} has {n} null value(s)")

    if problems:
        raise SchemaError(
            f"DataFrame failed {datatype} schema (v{schema.schema_version}):\n  - "
            + "\n  - ".join(problems)
        )
    return schema


# ---------------------------------------------------------------------------
# Provenance metadata
# ---------------------------------------------------------------------------
def _git_commit() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=paths.REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if out.returncode == 0:
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _build_metadata(
    schema: Schema,
    *,
    iso: str | None,
    year: int | None,
    market: str | None,
    source: str | None,
    extra: dict[str, Any] | None,
) -> dict[bytes, bytes]:
    """Assemble the parquet key-value metadata (schema version + provenance)."""
    meta: dict[str, str] = {
        "datatype": schema.datatype,
        "schema_version": str(schema.schema_version),
        "units": json.dumps(schema.units(), sort_keys=True),
        "key_columns": json.dumps(list(schema.key_columns)),
        "created_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
    }
    if iso is not None:
        meta["iso"] = str(iso)
    if year is not None:
        meta["year"] = str(year)
    if market is not None:
        meta["market"] = str(market)
    if source is not None:
        meta["source"] = str(source)
    commit = _git_commit()
    if commit is not None:
        meta["git_commit"] = commit
    if extra:
        for k, v in extra.items():
            meta[str(k)] = json.dumps(v) if not isinstance(v, str) else v
    return {f"{_META_PREFIX}{k}".encode(): str(v).encode() for k, v in meta.items()}


# ---------------------------------------------------------------------------
# Public writer + round-trip validator
# ---------------------------------------------------------------------------
def write_clean(
    df: pd.DataFrame,
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
    *,
    source: str | None = None,
    extra_provenance: dict[str, Any] | None = None,
) -> Path:
    """Validate ``df`` against the ``datatype`` schema and write clean Parquet.

    The single writer every curation script uses. It validates the frame (see
    :func:`validate_df`), resolves the destination via
    :func:`market_sim.config.paths.clean_path` (``iso`` / ``year`` / ``market``
    partition the path), and writes Parquet with the schema version, declared
    units and source provenance embedded in the file's key-value metadata.

    Parameters
    ----------
    df:
        The cleaned frame, already conforming to the canonical schema.
    datatype:
        One of the schemas under ``data/dictionary/schema``.
    iso, year, market:
        Optional partition keys passed straight to :func:`clean_path`.
    source:
        Free-text provenance (raw input path(s) / generating script) embedded
        in parquet metadata so a clean file traces back to its raw origin.
    extra_provenance:
        Additional key/value provenance to embed (JSON-encoded if non-string).

    Returns
    -------
    Path
        The path written.
    """
    schema = validate_df(df, datatype)
    out = paths.clean_path(datatype, iso=iso, year=year, market=market)
    out.parent.mkdir(parents=True, exist_ok=True)

    table = pa.Table.from_pandas(df, preserve_index=False)
    kv = _build_metadata(
        schema, iso=iso, year=year, market=market, source=source, extra=extra_provenance
    )
    # Preserve pandas/arrow metadata already on the table, then layer ours on.
    existing = table.schema.metadata or {}
    merged = {**existing, **kv}
    table = table.replace_schema_metadata(merged)
    pq.write_table(table, out)
    return out


#: Default parquet row-group size (rows). Matches the pyarrow default that
#: :func:`write_clean`'s single-shot ``pq.write_table`` applies, so the
#: streaming writer below lays out identical row groups.
_ROW_GROUP_ROWS = 1024 * 1024


def write_clean_iter(
    frames: Iterable[pd.DataFrame],
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
    *,
    source: str | None = None,
    extra_provenance: dict[str, Any] | None = None,
    row_group_rows: int = _ROW_GROUP_ROWS,
) -> Path:
    """Streaming sibling of :func:`write_clean` for datasets too big to concat.

    Same contract, same validation, same embedded metadata — but the caller
    hands over an *iterable* of schema-conforming chunks instead of one frame,
    and peak memory is bounded by ``row_group_rows`` rather than by the whole
    dataset. :func:`write_clean` materialises the full frame *and* a full
    ``pa.Table.from_pandas`` copy of it, which is what puts a 365-day CAISO
    ``dam-public-bids`` year (~32 M rows) past a 15 GB ceiling.

    The output is laid out to be **data-byte identical** to what
    :func:`write_clean` would have written for the concatenation of ``frames``:
    each chunk is cast to the first chunk's Arrow schema, buffered to exactly
    ``row_group_rows`` rows, and ``combine_chunks``-ed before the row group is
    flushed — so both writers produce the same row groups from the same
    contiguous column data. Only the provenance metadata differs, and only in
    the fields that are timestamps by construction (``created_utc``).

    Every chunk is validated with :func:`validate_df`, so a schema violation in
    a late chunk still fails the write (the file is removed before raising).

    Parameters
    ----------
    frames:
        Iterable of chunks, each conforming to the ``datatype`` schema and each
        carrying the same columns/dtypes. Consumed lazily — pass a generator.
    row_group_rows:
        Rows buffered before a row group is flushed. Bounds peak memory.

    Returns
    -------
    Path
        The path written.

    Raises
    ------
    SchemaError
        If any chunk violates the schema, or if ``frames`` is empty.
    """
    out = paths.clean_path(datatype, iso=iso, year=year, market=market)
    out.parent.mkdir(parents=True, exist_ok=True)

    schema = load_schema(datatype)
    writer: pq.ParquetWriter | None = None
    arrow_schema: pa.Schema | None = None
    buf: list[pa.Table] = []
    buffered = 0

    def _flush(n_rows: int) -> None:
        """Write exactly ``n_rows`` rows off the front of ``buf``."""
        nonlocal buf, buffered
        table = pa.concat_tables(buf)
        head = table.slice(0, n_rows).combine_chunks()
        assert writer is not None
        writer.write_table(head, row_group_size=n_rows)
        rest = table.slice(n_rows)
        buf = [rest] if rest.num_rows else []
        buffered = rest.num_rows

    try:
        for chunk in frames:
            if chunk is None or chunk.empty:
                continue
            validate_df(chunk, datatype, schema=schema)
            table = pa.Table.from_pandas(chunk, preserve_index=False)
            if writer is None:
                kv = _build_metadata(
                    schema,
                    iso=iso,
                    year=year,
                    market=market,
                    source=source,
                    extra=extra_provenance,
                )
                existing = table.schema.metadata or {}
                arrow_schema = table.schema.with_metadata({**existing, **kv})
                writer = pq.ParquetWriter(out, arrow_schema)
            else:
                table = table.cast(arrow_schema.remove_metadata())
            buf.append(table)
            buffered += table.num_rows
            while buffered >= row_group_rows:
                _flush(row_group_rows)
        if writer is None:
            raise SchemaError(
                f"write_clean_iter({datatype!r}): no non-empty chunks to write"
            )
        if buffered:
            _flush(buffered)
    except BaseException:
        if writer is not None:
            writer.close()
        out.unlink(missing_ok=True)
        raise
    writer.close()
    return out


def read_clean_metadata(path: str | Path) -> dict[str, str]:
    """Return the ``market_sim.*`` provenance metadata embedded in a clean file."""
    md = pq.read_metadata(str(path)).metadata or {}
    out: dict[str, str] = {}
    for k, v in md.items():
        key = k.decode() if isinstance(k, bytes) else str(k)
        if key.startswith(_META_PREFIX):
            out[key[len(_META_PREFIX) :]] = (
                v.decode() if isinstance(v, bytes) else str(v)
            )
    return out


def validate_clean(path: str | Path) -> Schema:
    """Round-trip check: read a written clean file and re-validate it.

    Reads the embedded ``datatype`` / ``schema_version`` metadata, loads the
    matching schema, and re-runs :func:`validate_df` on the round-tripped frame.
    Raises :class:`SchemaError` on any mismatch (missing metadata, unknown
    datatype, version drift, or content that no longer conforms). Returns the
    resolved :class:`Schema` on success.
    """
    path = Path(path)
    meta = read_clean_metadata(path)
    datatype = meta.get("datatype")
    if not datatype:
        raise SchemaError(f"{path} has no embedded market_sim.datatype metadata")

    schema = load_schema(datatype)
    embedded_version = meta.get("schema_version")
    if embedded_version is not None and int(embedded_version) != schema.schema_version:
        raise SchemaError(
            f"{path} embeds schema_version {embedded_version} but current "
            f"{datatype} schema is v{schema.schema_version}"
        )

    # Read through Arrow's own LocalFileSystem with prefetch + reader threads
    # OFF. A bare ``pd.read_parquet(path)`` has pandas open the file itself and
    # hand Arrow a Python file object (pandas/io/parquet.py ``get_handle``
    # branch), so Arrow's IO-pool prefetch threads read through the GIL and can
    # still hold Python buffers when a short curation script reaches
    # interpreter finalization — CPython then force-unwinds that worker,
    # which aborts with ``terminate called without an active exception``
    # (exit -6) AFTER every partition was written and validated. This is
    # every curation script's LAST parquet read, so it is the trigger that
    # fired non-deterministically on ancillary-services (caiso160 §5.1),
    # ira-credit-parameters (ffr-3p) and confirmed-retirements (golden tier
    # run #8, 2026-09-03; docs/FINDING-golden-tier-repair-2026-09.md §7).
    # Upstream: apache/arrow #34314 / #36980 (unfixed; ``use_threads=False``
    # is the documented mitigation). The frame is byte-identical, dtypes
    # included (asserted 2026-09-03 on 27M-row emissions: +0.8 s), so the
    # round-trip validation is unchanged — only the IO path is.
    df = pd.read_parquet(
        path, filesystem=pafs.LocalFileSystem(), use_threads=False, pre_buffer=False
    )
    validate_df(df, datatype, schema=schema)
    return schema


# ---------------------------------------------------------------------------
# Public reader (the consumption seam for the model)
# ---------------------------------------------------------------------------
def clean_exists(
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
) -> bool:
    """Whether the clean Parquet for these partition keys exists on disk.

    The clean tree is gitignored (derived/disposable), so consumers should
    check this and regenerate from raw — via ``scripts/regenerate_clean.py`` or
    the datatype's ``scripts/data/curate_<datatype>.py`` — when it is absent.
    """
    return paths.clean_path(datatype, iso=iso, year=year, market=market).is_file()


def read_clean(
    datatype: str,
    iso: str | None = None,
    year: int | None = None,
    market: str | None = None,
    *,
    validate: bool = True,
    columns: list[str] | None = None,
) -> pd.DataFrame:
    """Read a curated clean dataset — the single consumption seam for the model.

    Mirror image of :func:`write_clean`: resolves the path via
    :func:`market_sim.config.paths.clean_path` and returns the Parquet as a
    DataFrame. By default the frame is re-validated against the embedded
    schema (a guard against stale clean files written under an older contract);
    pass ``validate=False`` to skip for hot paths, or ``columns`` to project.

    Raises :class:`FileNotFoundError` (with a regenerate hint) if the partition
    is absent, and :class:`SchemaError` if a present file no longer conforms.
    """
    path = paths.clean_path(datatype, iso=iso, year=year, market=market)
    if not path.is_file():
        raise FileNotFoundError(
            f"no clean {datatype} at {path} — regenerate from raw with "
            f"`python scripts/data/curate_{datatype.replace('-', '_')}.py` "
            f"(or scripts/regenerate_clean.py)"
        )
    if validate:
        # Full round-trip validation (reads the file once); return that frame.
        validate_clean(path)
    return pd.read_parquet(path, columns=columns)
