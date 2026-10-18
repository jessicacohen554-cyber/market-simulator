"""Shared contract for the ``iso-area-load`` clean datatype.

An ISO's OWN published hourly metered load by load area, one row per (area,
hour), declared in ``data/dictionary/schema/iso-area-load.schema.yaml``.
Intake lane UC-SPP-DATAFIX (owner ruling R22, UC-DESK r20): SPP's HOURLY_LOAD
is the measured replacement for the EIA-930 frozen-snapshot hours in the SPP
demand leg and zonal weights.

Per-ISO parsing lives in sibling modules (``spp.py``) that register an
:class:`IsoSpec`; shared code never branches on the ISO name. Each spec names
its raw directory under ``data/raw`` and its market clock; partitions are the
ISO-local calendar year of each hour's START.

The registry scaffolding comes from
:func:`scripts.lib.datatype_registry.make_registry`; only the columns,
``validate_tidy``, ``split_local_years`` and ``parse_iso`` are datatype-specific.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "iso-area-load"

CANONICAL_COLUMNS: tuple[str, ...] = ("iso", "area", "interval_end_utc", "load_mw")

KEY_COLUMNS: tuple[str, ...] = ("iso", "area", "interval_end_utc")

_R = make_registry(
    DATATYPE,
    CANONICAL_COLUMNS,
    [
        ("iso", str),
        ("raw_subdir", str),
        ("tz", str),
        ("parse", "Callable[[Path, 'IsoSpec'], pd.DataFrame]"),
        ("description", str, ""),
    ],
    package=__name__,
    iso_modules=("spp",),
    raw_subpath=(),
    string_cols=("iso", "area"),
    float_cols=("load_mw",),
    sort_by=KEY_COLUMNS,
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
_finalize_base = _R.finalize


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw area-load files (the spec's ``raw_subdir``)."""
    return Path(raw_root) / load_registry()[iso.upper()].raw_subdir


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to the canonical dtypes / column order and sort on the key."""
    out = _finalize_base(df)
    out["interval_end_utc"] = out["interval_end_utc"].astype("datetime64[ns, UTC]")
    return out


def validate_tidy(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` on a duplicate key or a null / negative load."""
    dup = df.duplicated(list(KEY_COLUMNS))
    if dup.any():
        raise ValueError(f"{DATATYPE}: {int(dup.sum())} duplicate key rows")
    if df["load_mw"].isna().any():
        raise ValueError(f"{DATATYPE}: null load_mw")
    if (df["load_mw"] < 0).any():
        raise ValueError(f"{DATATYPE}: negative load_mw")


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
