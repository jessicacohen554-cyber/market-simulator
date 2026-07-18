"""Curate the ``nrel-atb`` clean datatype.

Lands the NREL ATB 2024 generation/storage technology CAPEX/Fixed O&M
trajectories (2022-2050) onto the tidy schema in
``data/dictionary/schema/nrel-atb.schema.yaml`` and writes one Parquet
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Single source: ``data/raw/nrel-atb/atb_2024_electricity_filtered.csv`` -- a
technology-filtered, crpyears-deduplicated extract of NREL's public
``ATBe.csv`` (the full file is ~572k rows / 94MB; see
``data/raw/nrel-atb/README.md`` for the exact filter and how to regenerate it
from the original). ``year`` is a *column* (one file spans 2022-2050), so the
whole datatype writes one partition
``data/clean/nrel-atb/nrel-atb.parquet`` (``year=None``). Reads only
``data/raw``; idempotent; skips cleanly when the CSV has not landed yet.

Run ``python scripts/data/curate_nrel_atb.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "nrel-atb"

# ATB's raw column name -> this datatype's schema column name. ``crpyears``
# is not listed: scripts/data/fetch_nrel_atb.py already drops it from the raw
# extract (verified value-invariant across every crpyears option).
_RENAME = {
    "atb_year": "atb_edition_year",
    "core_metric_parameter": "parameter",
    "core_metric_case": "financial_case",
    "scenario": "cost_case",
    "default": "is_default_class",
    "core_metric_variable": "year",
}

_RAW_COLUMNS = [
    "atb_year",
    "technology",
    "techdetail",
    "display_name",
    "core_metric_parameter",
    "core_metric_case",
    "tax_credit_case",
    "scenario",
    "default",
    "core_metric_variable",
    "value",
]

# ATB glossary/documentation unit convention by parameter -- the raw file's
# own `units` column ships empty for every row (verified during intake), so
# this mapping is applied here, not read from the source. ATB 2024's dollar
# year is 2022 (atb.nrel.gov/electricity/2024/index -- domain proxy-blocked
# in this environment; see README for the verification caveat).
_UNIT_BY_PARAMETER = {
    "CAPEX": "2022 $/kW",
    "Fixed O&M": "2022 $/kW-yr",
}

_SOURCE_DOC = "NREL ATB 2024 v3.0.0 electricity, OEDI data lake"
_SOURCE_KEY = "ATB/electricity/csv/2024/v3.0.0/ATBe.csv"


def raw_csv_path(raw_root: Path) -> Path:
    """Return the expected raw CSV path beneath ``raw_root``."""
    return raw_root / "nrel-atb" / "atb_2024_electricity_filtered.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _read_raw_csv(raw_root: Path) -> pd.DataFrame | None:
    """Read the single CSV if present, else concat ``.part*.csv`` files.

    This repo's GitHub-API push path caps individual file-content size, so
    this filtered extract lands as numbered, header-repeating parts
    (``atb_2024_electricity_filtered.part00.csv``, ...) instead of one file
    -- the same convention ``curate_coal_basin_price.py`` uses. Either
    layout is byte-identical once concatenated. Returns ``None`` if neither
    is present (not yet fetched).
    """
    single = raw_csv_path(raw_root)
    if single.is_file():
        return pd.read_csv(single, low_memory=False)
    parts = sorted(single.parent.glob(f"{single.stem}.part*.csv"))
    if not parts:
        return None
    return pd.concat(
        [pd.read_csv(p, low_memory=False) for p in parts], ignore_index=True
    )


def _source_repr(raw_root: Path) -> str:
    """Provenance string: the single CSV, or ``;``-joined part files."""
    single = raw_csv_path(raw_root)
    if single.is_file():
        return _rel(single)
    parts = sorted(single.parent.glob(f"{single.stem}.part*.csv"))
    return ";".join(_rel(p) for p in parts) or _rel(single)


def parse(raw_root: Path) -> pd.DataFrame:
    """Read and schema-shape the raw ATB extract (empty if not landed).

    Renames ATB's native column names to the schema's, maps parameter ->
    unit, converts the 0/1 default flag to bool, and attaches fixed source
    provenance.
    """
    df = _read_raw_csv(raw_root)
    if df is None:
        return pd.DataFrame()

    missing = set(_RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_source_repr(raw_root)}: missing columns {sorted(missing)}")
    df = df[_RAW_COLUMNS].rename(columns=_RENAME).copy()

    df["atb_edition_year"] = df["atb_edition_year"].astype("int64")
    df["technology"] = df["technology"].astype("string").str.strip()
    df["techdetail"] = df["techdetail"].astype("string").str.strip()
    df["display_name"] = df["display_name"].astype("string")
    df["parameter"] = df["parameter"].astype("string").str.strip()
    df["financial_case"] = df["financial_case"].astype("string").str.strip()
    df["tax_credit_case"] = df["tax_credit_case"].astype("string")
    df["cost_case"] = df["cost_case"].astype("string").str.strip()
    df["is_default_class"] = df["is_default_class"].astype("int64").astype("bool")
    df["year"] = df["year"].astype("int64")
    df["value"] = df["value"].astype("float64")

    bad_params = set(df["parameter"]) - set(_UNIT_BY_PARAMETER)
    if bad_params:
        raise ValueError(
            f"{_source_repr(raw_root)}: unmapped parameter(s) {sorted(bad_params)}"
        )
    df["unit"] = df["parameter"].map(_UNIT_BY_PARAMETER)

    bad_financial = set(df["financial_case"]) - {"Market"}
    if bad_financial:
        raise ValueError(
            f"{_source_repr(raw_root)}: unexpected financial_case(s) "
            f"{sorted(bad_financial)} -- this datatype only lands the Market case"
        )

    df["source_doc"] = _SOURCE_DOC
    df["source_page"] = _SOURCE_KEY

    key = [
        "technology",
        "techdetail",
        "parameter",
        "financial_case",
        "tax_credit_case",
        "cost_case",
        "year",
    ]
    dupes = df[df.duplicated(key, keep=False)]
    if not dupes.empty:
        raise ValueError(
            f"{_source_repr(raw_root)}: duplicate key rows:\n{dupes[key].to_string()}"
        )

    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the ATB partition; returns paths written.

    Reads only ``data/raw``; safe to re-run. Returns an empty list (and skips
    the write) when the raw CSV has not landed yet.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    df = parse(raw_root)
    if df.empty:
        print(f"[skip] {DATATYPE}: no raw CSV at {_rel(raw_csv_path(raw_root))}")
        return []
    source = _source_repr(raw_root)
    path = clean_io.write_clean(df, DATATYPE, year=None, source=source)
    clean_io.validate_clean(path)
    print(f"wrote {path}  ({len(df)} rows)")
    return [path]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--raw-root",
        default=None,
        help="root of the raw tree (default: data/raw)",
    )
    args = parser.parse_args(argv)
    curate(raw_root=args.raw_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
