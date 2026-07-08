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


def _read_raw_csv(raw_dir: Path, stem: str) -> pd.DataFrame:
    """Read ``<stem>.csv`` if present, else concat ``<stem>.part*.csv``.

    The raw EIA pulls are large single CSVs; some repo-push paths in this
    environment cap individual file-content size, so a fetch may land as
    numbered, header-repeating parts instead of one file. Either layout is
    byte-identical once concatenated — this is a read-time convenience, not
    a change to the raw data itself.
    """
    single = raw_dir / f"{stem}.csv"
    if single.is_file():
        return pd.read_csv(single)
    parts = sorted(raw_dir.glob(f"{stem}.part*.csv"))
    if not parts:
        raise FileNotFoundError(f"{single} not found (and no {stem}.part*.csv)")
    return pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)


def _build_market_sales_rows(raw: pd.DataFrame) -> pd.DataFrame:
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
        raise ValueError(f"market-sales-price raw: missing columns {sorted(missing)}")
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


def _build_price_by_rank_rows(raw: pd.DataFrame) -> pd.DataFrame:
    required = {"year", "region_id", "region_name", "coal_rank_id", "price_usd_per_ton"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"price-by-rank raw: missing columns {sorted(missing)}")
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
    market_raw = _read_raw_csv(raw_dir, "eia_coal_market_sales_price")
    rank_raw = _read_raw_csv(raw_dir, "eia_coal_price_by_rank")
    df = pd.concat(
        [_build_market_sales_rows(market_raw), _build_price_by_rank_rows(rank_raw)],
        ignore_index=True,
    )
    df["sales_short_tons"] = df["sales_short_tons"].astype("float64")
    return df.sort_values(
        ["metric", "region_id", "market_type_id", "coal_rank_id", "year"]
    ).reset_index(drop=True)


def _source_repr(raw_dir: Path, stem: str) -> str:
    single = raw_dir / f"{stem}.csv"
    if single.is_file():
        return _repo_rel(single)
    parts = sorted(raw_dir.glob(f"{stem}.part*.csv"))
    return ";".join(_repo_rel(p) for p in parts) or _repo_rel(single)


def curate(raw_dir: Path | None = None) -> Path:
    """Curate coal-basin-price; return the path written."""
    raw_dir = raw_dir or paths.COAL_PRICES_DIR
    df = build_clean(raw_dir)
    source = (
        f"{_source_repr(raw_dir, 'eia_coal_market_sales_price')};"
        f"{_source_repr(raw_dir, 'eia_coal_price_by_rank')}"
    )
    out = write_clean(df, _DATATYPE, source=source)
    validate_clean(out)
    return out


def main() -> None:
    out = curate()
    print(f"coal-basin-price -> {out}")


if __name__ == "__main__":
    main()
