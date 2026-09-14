#!/usr/bin/env python3
"""Curate the ``coal-stocks`` clean datatype.

Reads ONLY ``data/raw/coal-stocks/coal_stocks_<year>.csv`` (verbatim extracts of
EIA-923 "Page 2 Coal Stocks Data" — see
``scripts/data/fetch_eia923_coal_stocks.py``) and writes one schema-validated
Parquet per year through the frozen :func:`scripts.lib.clean_io.write_clean`
seam. The raw sheet is WIDE (twelve ``Quantity <Month>`` columns); this melts it
to the tidy long grain the schema declares — one row per plant x coal rank x
month.

National grain by design: the burning ISO is resolved at read time from the
plant registry (:mod:`market_sim.data.coal_stocks`), never partitioned here, so
one curation serves every coal ISO without a per-ISO branch.

Idempotent and re-runnable: everything derives from raw and the clean output is
overwritten in place.

Usage:
    python scripts/data/curate_coal_stocks.py
    python scripts/data/curate_coal_stocks.py --years 2020 2021 2022
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

_DATATYPE = "coal-stocks"

#: EIA files a synthetic plant, id 999999 "State-Fuel Level Increment", holding
#: its IMPUTED residual for plants below the reporting threshold, broken out per
#: state x sector x fuel. It is not a plant: it carries no location, no unit and
#: no capacity, and it is the sole reason a naive (plant, fuel) key looks
#: massively duplicated (141-172 rows/yr against 0 genuine duplicate pairs in
#: five of the seven published years). It is EXCLUDED, because this datatype's
#: grain is a real plant that the fleet can join to — a state residual summed
#: into it would be a fictitious stockpile no modelled unit can burn.
_SYNTHETIC_PLANT_ID_FLOOR = 999000

#: Raw wide month column -> calendar month number.
_MONTHS: dict[str, int] = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

#: Raw column -> clean column, for the columns carried through unmelted. These
#: are present in every published vintage; a missing one is a hard error.
_PASSTHROUGH: dict[str, str] = {
    "Plant Id": "plant_id",
    "Reported Fuel Type Code": "energy_source",
    "Plant Name": "plant_name",
    "Plant State": "plant_state",
    "NERC Region": "nerc_region",
    "EIA Sector Number": "eia_sector_number",
    "Physical Unit Label": "physical_unit_label",
}

#: Columns EIA added part-way through the published record. Absent in the 2018
#: vintage, present from 2019. Nullable in the schema and provenance-only (ISO
#: membership comes from the plant registry), so an older vintage curates
#: cleanly with the column left null rather than failing the whole year.
_OPTIONAL_PASSTHROUGH: dict[str, str] = {
    "Balancing Authority Code": "balancing_authority_code",
}


def raw_dir(raw_root: Path | None = None) -> Path:
    """Return the ``coal-stocks`` raw directory under ``raw_root``."""
    return (raw_root or paths.RAW_DATA_DIR) / "coal-stocks"


def _repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _numeric(series: pd.Series) -> pd.Series:
    """Coerce an EIA quantity column to float, treating '.'/'W'/'' as absent.

    EIA writes withheld or not-applicable cells as ``.`` or ``W``; neither is a
    zero stock and neither may be read as one, so both become NaN and the row is
    dropped for that month rather than silently entering as an empty stockpile.
    """
    return pd.to_numeric(
        series.astype("string").str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )


def _tidy_year(path: Path, year: int) -> pd.DataFrame:
    """Melt one raw year CSV onto the schema's long grain."""
    raw = pd.read_csv(path, dtype="string")
    raw.columns = [" ".join(str(c).split()) for c in raw.columns]

    missing = [c for c in _PASSTHROUGH if c not in raw.columns]
    if missing:
        raise ValueError(f"{path.name}: missing expected column(s) {missing}")

    frames: list[pd.DataFrame] = []
    for label, month in _MONTHS.items():
        col = f"Quantity {label}"
        if col not in raw.columns:
            raise ValueError(f"{path.name}: missing {col!r}")
        block = raw[list(_PASSTHROUGH)].rename(columns=_PASSTHROUGH)
        for src, dst in _OPTIONAL_PASSTHROUGH.items():
            block[dst] = raw[src] if src in raw.columns else pd.NA
        block["ending_stock_tons"] = _numeric(raw[col])
        block["month"] = month
        frames.append(block)

    df = pd.concat(frames, ignore_index=True)
    df["year"] = year
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df["eia_sector_number"] = pd.to_numeric(df["eia_sector_number"], errors="coerce")
    df = df.dropna(subset=["plant_id", "energy_source", "ending_stock_tons"])
    df = df[df["plant_id"] < _SYNTHETIC_PLANT_ID_FLOOR]
    df["plant_id"] = df["plant_id"].astype("int64")
    df["eia_sector_number"] = df["eia_sector_number"].astype("Int64")
    df["month"] = df["month"].astype("int64")
    df["year"] = df["year"].astype("int64")
    df["ending_stock_tons"] = df["ending_stock_tons"].astype("float64")
    for col in (
        "energy_source",
        "plant_name",
        "plant_state",
        "balancing_authority_code",
        "nerc_region",
        "physical_unit_label",
    ):
        df[col] = df[col].astype("string").str.strip()

    key = ["plant_id", "energy_source", "year", "month"]
    dupes = int(df.duplicated(subset=key).sum())
    if dupes:
        # With the synthetic state-increment rows excluded above, a genuine
        # duplicate is rare (0 pairs in 2018/2020/2021/2022/2023; 2 in 2019, 1
        # in 2024) and is a re-stated filing for one plant's rank. Sum is the
        # only defensible reconciliation for a stock held at one plant, and it
        # is announced rather than applied silently.
        print(f"  {year}: reconciled {dupes} duplicate key row(s) by sum")
        df = df.groupby(key, as_index=False).agg(
            ending_stock_tons=("ending_stock_tons", "sum"),
            plant_name=("plant_name", "first"),
            plant_state=("plant_state", "first"),
            balancing_authority_code=("balancing_authority_code", "first"),
            nerc_region=("nerc_region", "first"),
            eia_sector_number=("eia_sector_number", "first"),
            physical_unit_label=("physical_unit_label", "first"),
        )
    return df.sort_values(key).reset_index(drop=True)


def curate(raw_root: Path | None = None, years: list[int] | None = None) -> list[Path]:
    """Curate each available raw year; return the written clean paths."""
    rdir = raw_dir(raw_root)
    if not rdir.is_dir():
        raise FileNotFoundError(
            f"{_repo_rel(rdir)} not found — run "
            "scripts/data/fetch_eia923_coal_stocks.py first"
        )
    written: list[Path] = []
    for csv_path in sorted(rdir.glob("coal_stocks_*.csv")):
        year = int(csv_path.stem.rsplit("_", 1)[1])
        if years and year not in years:
            continue
        df = _tidy_year(csv_path, year)
        out = write_clean(
            df,
            _DATATYPE,
            year=year,
            source=f"EIA-923 Page 2 Coal Stocks Data via {_repo_rel(csv_path)}",
        )
        validate_clean(out)
        print(
            f"  {year}: {len(df):>6} rows, "
            f"{df.plant_id.nunique():>4} plants -> {_repo_rel(out)}"
        )
        written.append(out)
    if not written:
        raise FileNotFoundError(f"no coal_stocks_*.csv under {_repo_rel(rdir)}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=None)
    args = ap.parse_args()
    curate(years=args.years)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
