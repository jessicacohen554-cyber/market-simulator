#!/usr/bin/env python3
"""Curate the ``coal-mining-ppi`` clean datatype.

Reads ONLY ``data/raw/coal-prices`` and writes one schema-validated Parquet
through the frozen :func:`scripts.lib.clean_io.write_clean` seam, from the raw
BLS PPI CSV (``bls_coal_ppi.csv`` — see ``scripts/data/fetch_bls_coal_ppi.py``).

Idempotent and re-runnable.

Usage:
    python scripts/data/curate_coal_mining_ppi.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

_DATATYPE = "coal-mining-ppi"


def _repo_rel(path: Path) -> str:
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def build_clean(csv_path: Path) -> pd.DataFrame:
    """Reconcile bls_coal_ppi.csv onto the coal-mining-ppi schema."""
    raw = pd.read_csv(csv_path)
    required = {"series_id", "series_name", "year", "month", "index_value"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"{csv_path}: missing columns {sorted(missing)}")
    df = pd.DataFrame(
        {
            "series_id": raw["series_id"].astype("string"),
            "series_name": raw["series_name"].astype("string"),
            "year": raw["year"].astype("int64"),
            "month": raw["month"].astype("int64"),
            "index_value": raw["index_value"].astype("float64"),
        }
    )
    return df.sort_values(["series_id", "year", "month"]).reset_index(drop=True)


def curate(raw_dir: Path | None = None) -> Path:
    """Curate coal-mining-ppi; return the path written."""
    raw_dir = raw_dir or paths.COAL_PRICES_DIR
    csv_path = raw_dir / "bls_coal_ppi.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(f"{csv_path} not found")
    df = build_clean(csv_path)
    out = write_clean(df, _DATATYPE, source=_repo_rel(csv_path))
    validate_clean(out)
    return out


def main() -> None:
    out = curate()
    print(f"coal-mining-ppi -> {out}")


if __name__ == "__main__":
    main()
