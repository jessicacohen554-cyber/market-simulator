#!/usr/bin/env python3
"""Curate the ``stb-coal-loadings`` clean datatype (STB EP 724 Category 9).

Reads ONLY the newest ``data/raw/stb-ep724/EP724_Consolidated_Data_through_*.xlsx`` and writes one
schema-validated Parquet through :func:`scripts.lib.clean_io.write_clean`. The workbook is wide (one
column per reporting week); this script keeps Category 9 ("Coal Unit Train Loadings or Carloadings by
Coal Production Region") and melts it into the schema's long grain
``(carrier, region, measure, week, value)``.

National grain, no ISO partition (rule 25). A blank cell is a week the carrier did not file and is
dropped, never read as zero loadings. Idempotent: the clean output is overwritten in place.

Usage:
    python scripts/data/curate_stb_coal_loadings.py
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

_DATATYPE = "stb-coal-loadings"
_RAW_GLOB = "EP724_Consolidated_Data_through_*.xlsx"
#: EP 724 metric number of the coal-loadings-by-region series.
_CATEGORY = "9"
#: Sub-Variable label -> clean ``measure``.
_MEASURES = {"Loadings Plan": "plan", "Loadings Average": "actual"}
_ID_COLS = ["carrier", "category", "sub_category", "metric", "region", "sub_variable"]


def raw_dir(raw_root: Path | None = None) -> Path:
    """Return the ``stb-ep724`` raw directory under ``raw_root``."""
    return (raw_root or paths.RAW_DATA_DIR) / "stb-ep724"


def newest_workbook(raw_root: Path | None = None) -> Path:
    """Return the newest consolidated workbook (names sort by their through-date)."""
    found = sorted(raw_dir(raw_root).glob(_RAW_GLOB))
    if not found:
        raise FileNotFoundError(f"no {_RAW_GLOB} under {raw_dir(raw_root)}")
    return found[-1]


def tidy(raw: pd.DataFrame) -> pd.DataFrame:
    """Melt the wide EP 724 sheet (header row included) to the schema's long Category-9 frame."""
    header = list(raw.iloc[0])
    body = raw.iloc[1:].copy()
    body.columns = _ID_COLS + header[len(_ID_COLS) :]
    body = body[body.category.astype(str).str.strip() == _CATEGORY]
    body = body[body.sub_variable.isin(_MEASURES) & body.region.notna()]
    weeks = [c for c in body.columns[len(_ID_COLS) :] if pd.notna(pd.to_datetime(c, errors="coerce"))]
    long = body.melt(id_vars=["carrier", "region", "sub_variable"], value_vars=weeks, var_name="week")
    long["value"] = pd.to_numeric(long.value, errors="coerce")
    long = long.dropna(subset=["value"])
    out = pd.DataFrame(
        {
            "carrier": long.carrier.astype(str).str.strip().astype("string"),
            "region": long.region.astype(str).str.strip().str.title().astype("string"),
            "measure": long.sub_variable.map(_MEASURES).astype("string"),
            "week": pd.to_datetime(long.week).astype("datetime64[ns]"),
            "value": long.value.astype("float64"),
        }
    )
    return out.sort_values(["carrier", "region", "measure", "week"]).reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate the newest workbook and return the written clean path(s)."""
    src = newest_workbook(raw_root)
    df = tidy(pd.read_excel(src, header=None))
    try:
        source = str(src.relative_to(paths.REPO_ROOT))
    except ValueError:
        source = str(src)
    path = write_clean(df, _DATATYPE, source=source)
    validate_clean(path)
    return [path]


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args(argv)
    for p in curate():
        print(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
