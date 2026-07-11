"""Curate the ``uranium-marketing-price`` clean datatype.

Lands the EIA Uranium Marketing Annual Report's weighted-average uranium
(U3O8e) and enrichment-services (SWU) purchase price/quantity series onto the
tidy schema in ``data/dictionary/schema/uranium-marketing-price.schema.yaml``
and writes one Parquet partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Single hand-transcribed source: ``data/raw/uranium-marketing/
eia_umar_uranium_price.csv`` (EIA's Uranium Marketing Annual Report is
PDF-only -- no EIA Open Data API v2 route exists for uranium, verified
during intake -- so this is a documented table transcription, per-row cited
to its exact source table, not a fetch-script output). ``delivery_year`` is a
*column* (one file spans 2002-2024), so the whole datatype writes one
partition ``data/clean/uranium-marketing-price/uranium-marketing-price.parquet``
(``year=None``). Reads only ``data/raw``; idempotent; skips cleanly when the
CSV has not landed yet.

Run ``python scripts/curate_uranium_marketing_price.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "uranium-marketing-price"

_METRICS = {
    "total_purchased_quantity",
    "total_purchased_price",
    "enrichment_services_price",
}
_UNITS = {"million_lb_u3o8e", "usd_per_lb_u3o8e", "usd_per_swu"}

_COLUMNS = ["metric", "delivery_year", "value", "unit", "source_doc", "source_page"]


def raw_csv_path(raw_root: Path) -> Path:
    """Return the expected raw CSV path beneath ``raw_root``."""
    return raw_root / "uranium-marketing" / "eia_umar_uranium_price.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def parse(raw_root: Path) -> pd.DataFrame:
    """Read and schema-shape the raw uranium-price CSV (empty if not landed).

    Coerces dtypes to the canonical schema and enforces the metric/unit
    vocabulary.
    """
    csv = raw_csv_path(raw_root)
    if not csv.exists():
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.read_csv(csv)
    missing = set(_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_rel(csv)}: missing columns {sorted(missing)}")
    df = df[_COLUMNS].copy()

    df["metric"] = df["metric"].astype("string").str.strip()
    df["delivery_year"] = df["delivery_year"].astype("int64")
    df["value"] = df["value"].astype("float64")
    df["unit"] = df["unit"].astype("string").str.strip()
    df["source_doc"] = df["source_doc"].astype("string")
    df["source_page"] = df["source_page"].astype("string")

    bad_metric = set(df["metric"]) - _METRICS
    if bad_metric:
        raise ValueError(f"{_rel(csv)}: unknown metric(s) {sorted(bad_metric)}")
    bad_unit = set(df["unit"]) - _UNITS
    if bad_unit:
        raise ValueError(f"{_rel(csv)}: unknown unit(s) {sorted(bad_unit)}")

    dupes = df[df.duplicated(["metric", "delivery_year"], keep=False)]
    if not dupes.empty:
        raise ValueError(f"{_rel(csv)}: duplicate key rows:\n{dupes}")

    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the uranium-price partition; returns paths written.

    Reads only ``data/raw``; safe to re-run. Returns an empty list (and skips
    the write) when the raw CSV has not landed yet.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    df = parse(raw_root)
    if df.empty:
        print(f"[skip] {DATATYPE}: no raw CSV at {_rel(raw_csv_path(raw_root))}")
        return []
    source = _rel(raw_csv_path(raw_root))
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
