#!/usr/bin/env python3
"""Curate the ``coal-basin-price`` clean datatype.

Reads ONLY ``data/raw/coal-prices`` and writes one schema-validated Parquet
through the frozen :func:`scripts.lib.clean_io.write_clean` seam. Tidies the
two raw EIA Open Data API CSVs (``eia_coal_market_sales_price.csv``,
``eia_coal_price_by_rank.csv`` — see ``scripts/fetch_eia_coal_prices.py``)
onto one long ``metric``-keyed frame per ``data/dictionary/schema/
coal-basin-price.schema.yaml``.

Idempotent and re-runnable: everything is derived from raw and the clean
output is overwritten in place.

Usage:
    python scripts/curate_coal_basin_price.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

_DATATYPE = "coal-basin-price"


def _repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _build_market_sales_rows(csv_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(csv_path)
    required = {
        "year",
        "region_id",
        "region_name",
        "market_type_id",
        "market_type_name",
        "price_usd_per_ton",
        "sales_short_tons",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{csv_path}: missing columns {sorted(missing)}")
    return pd.DataFrame(
        {
            "metric": pd.array(["market_sales_price"] * len(raw), dtype="string"),
            "region_id": raw["region_id"].astype("string"),
            "region_name": raw["region_name"].astype("string"),
            "market_type_id": raw["market_type_id"].astype("string"),
            "coal_rank_id": pd.array(["ALL"] * len(raw), dtype="string"),
            "year": raw["year"].astype("int64"),
            "price_usd_per_ton": raw["price_usd_per_ton"].astype("float64"),
            "sales_short_tons": raw["sales_short_tons"].astype("float64"),
        }
    )


def _build_price_by_rank_rows(csv_path: Path) -> pd.DataFrame:
    raw = pd.read_csv(csv_path)
    required = {"year", "region_id", "region_name", "coal_rank_id", "price_usd_per_ton"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{csv_path}: missing columns {sorted(missing)}")
    return pd.DataFrame(
        {
            "metric": pd.array(["price_by_rank"] * len(raw), dtype="string"),
            "region_id": raw["region_id"].astype("string"),
            "region_name": raw["region_name"].astype("string"),
            "market_type_id": pd.array(["ALL"] * len(raw), dtype="string"),
            "coal_rank_id": raw["coal_rank_id"].astype("string"),
            "year": raw["year"].astype("int64"),
            "price_usd_per_ton": raw["price_usd_per_ton"].astype("float64"),
            "sales_short_tons": pd.array([pd.NA] * len(raw), dtype="Float64"),
        }
    )


def build_clean(raw_dir: Path) -> pd.DataFrame:
    """Return the tidied coal-basin-price frame from the two raw CSVs."""
    market_csv = raw_dir / "eia_coal_market_sales_price.csv"
    rank_csv = raw_dir / "eia_coal_price_by_rank.csv"
    if not market_csv.is_file():
        raise FileNotFoundError(f"{market_csv} not found")
    if not rank_csv.is_file():
        raise FileNotFoundError(f"{rank_csv} not found")
    df = pd.concat(
        [_build_market_sales_rows(market_csv), _build_price_by_rank_rows(rank_csv)],
        ignore_index=True,
    )
    df["sales_short_tons"] = df["sales_short_tons"].astype("float64")
    return df.sort_values(
        ["metric", "region_id", "market_type_id", "coal_rank_id", "year"]
    ).reset_index(drop=True)


def curate(raw_dir: Path | None = None) -> Path:
    """Curate coal-basin-price; return the path written."""
    raw_dir = raw_dir or paths.COAL_PRICES_DIR
    df = build_clean(raw_dir)
    source = (
        f"{_repo_rel(raw_dir / 'eia_coal_market_sales_price.csv')};"
        f"{_repo_rel(raw_dir / 'eia_coal_price_by_rank.csv')}"
    )
    out = write_clean(df, _DATATYPE, source=source)
    validate_clean(out)
    return out


def main() -> None:
    out = curate()
    print(f"coal-basin-price -> {out}")


if __name__ == "__main__":
    main()
