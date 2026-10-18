"""Shared contract for the ``counterparty-interchange`` clean datatype.

Every measured hourly leg of an ISO balancing authority's interchange, as the
BA itself reports it (``reporter = "own"``) and as each counterparty reports
it (``reporter = "counterparty"``), on one export-positive sign from the
ISO's BA (``data/dictionary/schema/counterparty-interchange.schema.yaml``).
Intake lane UC-SPP-DATAFIX (owner ruling R22, UC-DESK r20): when SWPP's own
submission is frozen or absent, the counterparty-reported legs are the
measured replacement for its ``Total interchange``.

Per-ISO parsing lives in sibling modules (``spp.py``) that register an
:class:`IsoSpec`; shared code never branches on the ISO name. Partitions are
the ISO-local calendar year of each hour's START.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "counterparty-interchange"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "ba",
    "counterparty",
    "reporter",
    "interval_end_utc",
    "export_mw",
)

KEY_COLUMNS: tuple[str, ...] = ("iso", "counterparty", "reporter", "interval_end_utc")

#: The two reporting sides of a leg.
REPORTERS: frozenset[str] = frozenset({"own", "counterparty"})

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("ba", str),
        ("raw_subdir", str),
        ("tz", str),
        ("parse", "Callable[[Path, 'IsoSpec'], pd.DataFrame]"),
        ("description", str, ""),
    ],
    package=__name__,
    iso_modules=("spp",),
    raw_subpath=(),
    string_cols=("iso", "ba", "counterparty", "reporter"),
    float_cols=("export_mw",),
    sort_by=KEY_COLUMNS,
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
_finalize_base = _R.finalize


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw interchange files (the spec's ``raw_subdir``)."""
    return Path(raw_root) / load_registry()[iso.upper()].raw_subdir


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to the canonical dtypes / column order and sort on the key."""
    out = _finalize_base(df)
    out["interval_end_utc"] = out["interval_end_utc"].astype("datetime64[ns, UTC]")
    return out


def validate_tidy(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` on a duplicate key, an unknown reporter or a null value."""
    dup = df.duplicated(list(KEY_COLUMNS))
    if dup.any():
        raise ValueError(f"{DATATYPE}: {int(dup.sum())} duplicate key rows")
    bad = set(df["reporter"].unique()) - REPORTERS
    if bad:
        raise ValueError(f"{DATATYPE}: unknown reporter(s) {sorted(bad)}")
    if df["export_mw"].isna().any():
        raise ValueError(f"{DATATYPE}: null export_mw")


def split_local_years(df: pd.DataFrame, tz: str) -> dict[int, pd.DataFrame]:
    """``{local year: rows}`` keyed by the local calendar year of each hour's START."""
    start_local = (df["interval_end_utc"] - pd.Timedelta(hours=1)).dt.tz_convert(tz)
    years = start_local.dt.year
    return {
        int(y): df[years == y].reset_index(drop=True) for y in sorted(years.unique())
    }


def parse_iso(iso: str, raw_root: Path) -> dict[int, pd.DataFrame]:
    """``{local year: tidy frame}`` for one ISO via its registered parser."""
    spec = load_registry().get(iso.upper())
    if spec is None:
        raise KeyError(f"{DATATYPE}: no registered spec for {iso}")
    df = finalize(spec.parse(raw_dir_for(iso, raw_root), spec))
    validate_tidy(df)
    return split_local_years(df, spec.tz)
