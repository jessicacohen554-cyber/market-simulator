"""Curate the ``nrel-atb`` clean datatype.

Lands the NREL ATB 2024 generation/storage technology CAPEX/Fixed O&M
trajectories (2022-2050) onto the tidy schema in
``data/dictionary/schema/nrel-atb.schema.yaml`` and writes one Parquet
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Sources: one technology-filtered, crpyears-deduplicated extract of NREL's
public ``ATBe.csv`` per committed ATB *version* -- today
``atb_2024_electricity_filtered.csv`` (2024 v3.0.0) and
``atb_2024v4_electricity_filtered.csv`` (2024 v4.0.0). The full source file
is ~572-586k rows / ~94-103MB; see ``data/raw/nrel-atb/README.md`` for the
exact filter and how to regenerate either from the original.

NREL re-releases an ATB *edition* under successive point *versions* when it
corrects it, so edition-year alone does not identify a vintage --
``atb_version`` is therefore part of the schema key, every landed version is
curated into the one partition, and :func:`parse` defaults to the single
version this repo's cost constants were derived from
(:data:`DERIVATION_PINNED_VERSION`) so its derive-script callers are
unaffected when a newer version lands.

``year`` is a *column* (one file spans 2022-2050), so the whole datatype
writes one partition ``data/clean/nrel-atb/nrel-atb.parquet``
(``year=None``). Reads only ``data/raw``; idempotent; skips cleanly when no
extract has landed yet.

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

# The ATB versions committed under data/raw/nrel-atb, newest last. An ATB
# *edition* (2024) is re-released by NREL under successive point *versions*
# when it is corrected, so edition-year alone does not identify a vintage --
# hence `atb_version` is part of this datatype's key and each version lands
# its own raw extract under its own filename stem. Adding a version here (and
# committing its extract) is the whole intake step for a new ATB release.
#
# stem -> (edition_year, version, OEDI object key)
_VERSIONS: dict[str, tuple[int, str, str]] = {
    "atb_2024_electricity_filtered": (
        2024,
        "v3.0.0",
        "ATB/electricity/csv/2024/v3.0.0/ATBe.csv",
    ),
    "atb_2024v4_electricity_filtered": (
        2024,
        "v4.0.0",
        "ATB/electricity/csv/2024/v4.0.0/ATBe.csv",
    ),
}

# The version this repo's committed constants were derived from. `parse`
# defaults to it so the derive scripts and their rule-23 consistency tests
# (tests/test_atb_entry_cost_consistency.py,
# tests/test_cost_benchmark_envelope.py) keep reading exactly the bytes they
# were built against when a newer version lands alongside. `curate` ignores
# this and writes EVERY committed version to the clean partition, so a
# re-derivation session can select the newer one explicitly. Moving this pin
# is a deliberate re-derivation act (FFR-SC), never a side effect of intake.
#
# MOVED v3.0.0 -> v4.0.0 by FFR-SC (2026-08-03), on the DATA VINTAGE CHANGE and
# nothing else (rule 23 [R-FROZEN-DERIVE]): OEDI mirrored ATB 2024 v4.0.0 on
# 2026-07-28 and FFR-PB landed its extract (audit FR-20). No residual moved and
# none was consulted. The re-derivation is a measured NO-OP on every committed
# constant: over the whole committed slice (3,858 rows, identical key index)
# only 56 rows differ materially, ALL of them Geothermal/DeepEGSFlash Moderate
# (CAPEX +1.50..+6.14 %, Fixed O&M +0.13..+2.00 %) -- a technology no derive
# script reads; the other 16 differing rows are float round-trip noise at
# ~1e-14 relative. derive_entry_costs_from_atb (NEW_ENTRY_COSTS,
# TECH_COST_MULTIPLIERS) and derive_cost_benchmark_envelope (envelope table,
# envelope multipliers, STORAGE_TECHS li-ion, OFFSHORE_WIND_PARAMS) return
# byte-identical dicts under both versions, so constants.py is unchanged and
# the two rule-23 consistency tests still pass against the newer bytes.
DERIVATION_PINNED_VERSION = "v4.0.0"

_STEM_BY_VERSION = {v: stem for stem, (_, v, _) in _VERSIONS.items()}


def raw_csv_path(raw_root: Path, version: str = DERIVATION_PINNED_VERSION) -> Path:
    """Return the expected raw CSV path for one ATB version beneath ``raw_root``."""
    try:
        stem = _STEM_BY_VERSION[version]
    except KeyError:
        raise ValueError(
            f"unknown ATB version {version!r}; known: {sorted(_STEM_BY_VERSION)}"
        ) from None
    return raw_root / "nrel-atb" / f"{stem}.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def available_versions(raw_root: Path) -> list[str]:
    """Return the ATB versions whose raw extract has landed under ``raw_root``.

    Ordered as :data:`_VERSIONS` declares them (oldest first). A version with
    neither its single CSV nor any ``.part*.csv`` piece present is skipped,
    so this reports what is actually on disk rather than what is known.
    """
    found = []
    for version in _STEM_BY_VERSION:
        single = raw_csv_path(raw_root, version)
        if single.is_file() or sorted(single.parent.glob(f"{single.stem}.part*.csv")):
            found.append(version)
    return found


def _read_raw_csv(raw_root: Path, version: str) -> pd.DataFrame | None:
    """Read the single CSV if present, else concat ``.part*.csv`` files.

    This repo's GitHub-API push path caps individual file-content size, so
    this filtered extract lands as numbered, header-repeating parts
    (``atb_2024_electricity_filtered.part00.csv``, ...) instead of one file
    -- the same convention ``curate_coal_basin_price.py`` uses. Either
    layout is byte-identical once concatenated. Returns ``None`` if neither
    is present (not yet fetched).
    """
    single = raw_csv_path(raw_root, version)
    if single.is_file():
        return pd.read_csv(single, low_memory=False)
    parts = sorted(single.parent.glob(f"{single.stem}.part*.csv"))
    if not parts:
        return None
    return pd.concat(
        [pd.read_csv(p, low_memory=False) for p in parts], ignore_index=True
    )


def _source_repr(raw_root: Path, version: str) -> str:
    """Provenance string: the single CSV, or ``;``-joined part files."""
    single = raw_csv_path(raw_root, version)
    if single.is_file():
        return _rel(single)
    parts = sorted(single.parent.glob(f"{single.stem}.part*.csv"))
    return ";".join(_rel(p) for p in parts) or _rel(single)


def parse(raw_root: Path, version: str = DERIVATION_PINNED_VERSION) -> pd.DataFrame:
    """Read and schema-shape one ATB version's raw extract (empty if not landed).

    Renames ATB's native column names to the schema's, maps parameter ->
    unit, converts the 0/1 default flag to bool, and attaches the version's
    own source provenance.

    ``version`` defaults to :data:`DERIVATION_PINNED_VERSION` -- the vintage
    this repo's committed cost constants were derived from -- so the derive
    scripts that call this keep seeing exactly one row per key, unchanged,
    when a newer ATB version lands alongside. Pass an explicit version to
    read a different one.
    """
    df = _read_raw_csv(raw_root, version)
    if df is None:
        return pd.DataFrame()
    edition_year, _, source_key = _VERSIONS[_STEM_BY_VERSION[version]]

    missing = set(_RAW_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(
            f"{_source_repr(raw_root, version)}: missing columns {sorted(missing)}"
        )
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
            f"{_source_repr(raw_root, version)}: unmapped parameter(s) {sorted(bad_params)}"
        )
    df["unit"] = df["parameter"].map(_UNIT_BY_PARAMETER)

    bad_financial = set(df["financial_case"]) - {"Market"}
    if bad_financial:
        raise ValueError(
            f"{_source_repr(raw_root, version)}: unexpected financial_case(s) "
            f"{sorted(bad_financial)} -- this datatype only lands the Market case"
        )

    if set(df["atb_edition_year"]) != {edition_year}:
        raise ValueError(
            f"{_source_repr(raw_root, version)}: expected atb_year "
            f"{edition_year} for {version}, found "
            f"{sorted(set(df['atb_edition_year']))}"
        )
    df["atb_version"] = version
    df["source_doc"] = f"NREL ATB {edition_year} {version} electricity, OEDI data lake"
    df["source_page"] = source_key

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
            f"{_source_repr(raw_root, version)}: duplicate key rows:\n{dupes[key].to_string()}"
        )

    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the ATB partition; returns paths written.

    Writes EVERY ATB version whose extract has landed (``atb_version`` is
    part of the key, so successive versions of one edition stack in the
    single partition rather than colliding) -- unlike :func:`parse`, which
    defaults to the one pinned vintage its callers derive from.

    Reads only ``data/raw``; safe to re-run. Returns an empty list (and skips
    the write) when no raw extract has landed yet.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    versions = available_versions(raw_root)
    if not versions:
        print(
            f"[skip] {DATATYPE}: no raw CSV at "
            f"{_rel(raw_csv_path(raw_root).parent)} for any known version "
            f"{sorted(_STEM_BY_VERSION)}"
        )
        return []

    frames = [parse(raw_root, version) for version in versions]
    df = pd.concat(frames, ignore_index=True)
    source = ";".join(_source_repr(raw_root, version) for version in versions)
    path = clean_io.write_clean(df, DATATYPE, year=None, source=source)
    clean_io.validate_clean(path)
    print(f"wrote {path}  ({len(df)} rows, versions {', '.join(versions)})")
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
