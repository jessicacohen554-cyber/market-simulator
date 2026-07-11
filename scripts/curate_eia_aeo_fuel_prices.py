"""Curate the ``eia-aeo-fuel-prices`` clean datatype.

Lands the EIA AEO2025 gas/coal/oil price trajectories (Reference / High Oil
and Gas Supply / Low Oil and Gas Supply cases, 2024-2050) onto the tidy
schema in ``data/dictionary/schema/eia-aeo-fuel-prices.schema.yaml`` and
writes one Parquet partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Single fetched source: ``data/raw/eia-aeo/eia_aeo2025_fuel_prices.csv``,
produced by ``scripts/fetch_eia_aeo.py`` against the EIA Open Data API v2.
``year`` is a *column* (one file spans 2024-2050), so the whole datatype
writes one partition ``data/clean/eia-aeo-fuel-prices/
eia-aeo-fuel-prices.parquet`` (``year=None``). Reads only ``data/raw``;
idempotent; skips cleanly when the CSV has not been fetched yet.

This is a forward-projection dataset (2024-2050), not a measured actual for a
solve/scoring year, so it carries no CLAUDE.md rule-22 holdout-quarantine
restriction (unlike rggi-co2-budgets/carb-cap-schedule, which do quarantine
2022/2026 rows). Run ``python scripts/curate_eia_aeo_fuel_prices.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "eia-aeo-fuel-prices"

_FUELS = {"gas", "coal", "oil"}
_METRICS = {
    "henry_hub_spot",
    "wti_spot_crude",
    "electric_power_distillate",
    "electric_power_residual",
    "delivered_electric_power",
    "minemouth_average",
    "minemouth_by_region",
}
_SCENARIOS = {"ref2025", "highogs", "lowogs"}

_COLUMNS = [
    "fuel",
    "metric",
    "region",
    "scenario",
    "scenario_name",
    "year",
    "value",
    "unit",
    "series_id",
    "table_id",
    "table_name",
]


def raw_csv_path(raw_root: Path) -> Path:
    """Return the expected raw CSV path beneath ``raw_root``."""
    return raw_root / "eia-aeo" / "eia_aeo2025_fuel_prices.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _read_raw_csv(raw_root: Path) -> pd.DataFrame | None:
    """Read the single CSV if present, else concat ``.part*.csv`` files.

    This repo's GitHub-API push path caps individual file-content size, so
    this fetch lands as numbered, header-repeating parts
    (``eia_aeo2025_fuel_prices.part00.csv``, ...) instead of one file -- the
    same convention ``curate_coal_basin_price.py`` uses. Either layout is
    byte-identical once concatenated. Returns ``None`` if neither is present
    (not yet fetched).
    """
    single = raw_csv_path(raw_root)
    if single.is_file():
        return pd.read_csv(single)
    parts = sorted(single.parent.glob(f"{single.stem}.part*.csv"))
    if not parts:
        return None
    return pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)


def _source_repr(raw_root: Path) -> str:
    """Provenance string: the single CSV, or ``;``-joined part files."""
    single = raw_csv_path(raw_root)
    if single.is_file():
        return _rel(single)
    parts = sorted(single.parent.glob(f"{single.stem}.part*.csv"))
    return ";".join(_rel(p) for p in parts) or _rel(single)


def parse(raw_root: Path) -> pd.DataFrame:
    """Read and schema-shape the raw AEO CSV (empty if it has not landed).

    Coerces dtypes to the canonical schema and enforces the fuel/metric/
    scenario vocabulary.
    """
    df = _read_raw_csv(raw_root)
    if df is None:
        return pd.DataFrame(columns=_COLUMNS)

    missing = set(_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_source_repr(raw_root)}: missing columns {sorted(missing)}")
    df = df[_COLUMNS].copy()

    df["fuel"] = df["fuel"].astype("string").str.strip()
    df["metric"] = df["metric"].astype("string").str.strip()
    df["region"] = df["region"].astype("string").str.strip()
    df["scenario"] = df["scenario"].astype("string").str.strip()
    df["scenario_name"] = df["scenario_name"].astype("string")
    df["year"] = df["year"].astype("int64")
    df["value"] = df["value"].astype("float64")
    df["unit"] = df["unit"].astype("string")
    df["series_id"] = df["series_id"].astype("string")
    df["table_id"] = df["table_id"].astype("string")
    df["table_name"] = df["table_name"].astype("string")

    bad_fuel = set(df["fuel"]) - _FUELS
    if bad_fuel:
        raise ValueError(
            f"{_source_repr(raw_root)}: unknown fuel(s) {sorted(bad_fuel)}"
        )
    bad_metric = set(df["metric"]) - _METRICS
    if bad_metric:
        raise ValueError(
            f"{_source_repr(raw_root)}: unknown metric(s) {sorted(bad_metric)}"
        )
    bad_scenario = set(df["scenario"]) - _SCENARIOS
    if bad_scenario:
        raise ValueError(
            f"{_source_repr(raw_root)}: unknown scenario(s) {sorted(bad_scenario)}"
        )

    dupe_key = ["fuel", "metric", "region", "scenario", "year"]
    dupes = df[df.duplicated(dupe_key, keep=False)]
    if not dupes.empty:
        raise ValueError(f"{_source_repr(raw_root)}: duplicate key rows:\n{dupes}")

    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the AEO fuel-price partition; returns paths written.

    Reads only ``data/raw``; safe to re-run. Returns an empty list (and skips
    the write) when the raw CSV has not been fetched yet.
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
