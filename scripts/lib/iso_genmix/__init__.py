"""Shared contract for the ``iso-genmix`` clean datatype.

An ISO's OWN published generation by fuel, aggregated to the hour
(``data/dictionary/schema/iso-genmix.schema.yaml``). Intake lane
UC-SPP-DATAFIX (owner ruling R23, UC-DESK r20): SPP's 5-minute GenMix is the
measured replacement for EIA-930's frozen ``NG: WND`` / ``NG: SUN`` hours.

Per-ISO parsing lives in sibling modules (``spp.py``) that register an
:class:`IsoSpec`; shared code never branches on the ISO name. Partitions are
the ISO-local calendar year of each hour's START.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.datatype_registry import make_registry

DATATYPE = "iso-genmix"

CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "area",
    "fuel",
    "interval_end_utc",
    "generation_mw",
    "n_intervals",
)

KEY_COLUMNS: tuple[str, ...] = ("iso", "area", "fuel", "interval_end_utc")

#: Canonical fuel families.
FUEL_VOCAB: frozenset[str] = frozenset(
    {
        "coal",
        "oil",
        "hydro",
        "gas",
        "nuclear",
        "solar",
        "wind",
        "waste",
        "waste_heat",
        "other",
    }
)

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
    string_cols=("iso", "area", "fuel"),
    float_cols=("generation_mw",),
    sort_by=KEY_COLUMNS,
)
IsoSpec = _R.IsoSpec
REGISTRY: dict[str, "IsoSpec"] = _R.REGISTRY
register = _R.register
load_registry = _R.load_registry
_finalize_base = _R.finalize


def raw_dir_for(iso: str, raw_root: Path) -> Path:
    """Directory holding an ISO's raw generation-mix files (the spec's ``raw_subdir``)."""
    return Path(raw_root) / load_registry()[iso.upper()].raw_subdir


def finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce to the canonical dtypes / column order and sort on the key."""
    out = _finalize_base(df)
    out["interval_end_utc"] = out["interval_end_utc"].astype("datetime64[ns, UTC]")
    out["n_intervals"] = out["n_intervals"].astype("int64")
    return out


def validate_tidy(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` on a duplicate key, an unknown fuel or a null value."""
    dup = df.duplicated(list(KEY_COLUMNS))
    if dup.any():
        raise ValueError(f"{DATATYPE}: {int(dup.sum())} duplicate key rows")
    bad = set(df["fuel"].unique()) - FUEL_VOCAB
    if bad:
        raise ValueError(f"{DATATYPE}: unknown fuel(s) {sorted(bad)}")
    if df["generation_mw"].isna().any():
        raise ValueError(f"{DATATYPE}: null generation_mw")
    if (df["n_intervals"] < 1).any():
        raise ValueError(f"{DATATYPE}: n_intervals < 1")


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
