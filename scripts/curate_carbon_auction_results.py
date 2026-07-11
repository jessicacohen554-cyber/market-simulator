"""Curate the ``carbon-auction-results`` clean datatype.

Lands the RGGI and CARB/Quebec joint cap-and-trade per-auction clearing-price
history onto the tidy schema in
``data/dictionary/schema/carbon-auction-results.schema.yaml`` and writes one
Parquet partition through the frozen :func:`scripts.lib.clean_io.write_clean`
seam.

Single hand-curated source: ``data/raw/policy/carbon-auction-results/
carbon-auction-results.csv`` (RGGI's own published auction-results table for
every row; CARB rows collected from individual press releases/secondary
reporting since ww2.arb.ca.gov blocks automated fetches -- see the raw
README). ``year``/``quarter`` are *columns* (one file spans multiple years),
so the whole datatype writes one partition
``data/clean/carbon-auction-results/carbon-auction-results.parquet``
(``year=None``). Reads only ``data/raw``; idempotent; skips cleanly when the
CSV has not landed yet.

HOLDOUT QUARANTINE (CLAUDE.md rule 22): rows for 2022 or any 2026 auction are
rejected -- same restriction the sibling rggi-co2-budgets/carb-cap-schedule
datatypes enforce. Run ``python scripts/curate_carbon_auction_results.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "carbon-auction-results"

_PROGRAMS = {"RGGI", "CARB"}
_PRICE_UNITS = {"usd_per_short_ton", "usd_per_tonne"}
# Years under full holdout quarantine -- never intaken (CLAUDE.md rule 22).
_QUARANTINED_YEARS = frozenset({2022, 2026})

_COLUMNS = [
    "program",
    "year",
    "quarter",
    "auction_date",
    "auction_number",
    "clearing_price",
    "price_unit",
    "allowances_sold",
    "allowances_offered",
    "source_doc",
    "source_page",
]


def raw_csv_path(raw_root: Path) -> Path:
    """Return the expected raw CSV path beneath ``raw_root``."""
    return raw_root / "policy" / "carbon-auction-results" / f"{DATATYPE}.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def parse(raw_root: Path) -> pd.DataFrame:
    """Read and schema-shape the raw auction-results CSV (empty if not landed).

    Coerces dtypes to the canonical schema, enforces the program/unit
    vocabulary, and the holdout-year quarantine.
    """
    csv = raw_csv_path(raw_root)
    if not csv.exists():
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.read_csv(csv)
    missing = set(_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_rel(csv)}: missing columns {sorted(missing)}")
    df = df[_COLUMNS].copy()

    df["program"] = df["program"].astype("string").str.strip()
    df["year"] = df["year"].astype("int64")
    df["quarter"] = df["quarter"].astype("int64")
    df["auction_date"] = df["auction_date"].astype("string")
    df["auction_number"] = df["auction_number"].astype("string")
    df["clearing_price"] = df["clearing_price"].astype("float64")
    df["price_unit"] = df["price_unit"].astype("string").str.strip()
    df["allowances_sold"] = df["allowances_sold"].astype("float64")
    df["allowances_offered"] = df["allowances_offered"].astype("float64")
    df["source_doc"] = df["source_doc"].astype("string")
    df["source_page"] = df["source_page"].astype("string")

    bad_program = set(df["program"]) - _PROGRAMS
    if bad_program:
        raise ValueError(f"{_rel(csv)}: unknown program(s) {sorted(bad_program)}")
    bad_unit = set(df["price_unit"]) - _PRICE_UNITS
    if bad_unit:
        raise ValueError(f"{_rel(csv)}: unknown price_unit(s) {sorted(bad_unit)}")
    bad_quarter = set(df["quarter"]) - {1, 2, 3, 4}
    if bad_quarter:
        raise ValueError(f"{_rel(csv)}: invalid quarter(s) {sorted(bad_quarter)}")
    hit = _QUARANTINED_YEARS & set(df["year"].tolist())
    if hit:
        raise ValueError(
            f"{_rel(csv)}: holdout-quarantined year(s) {sorted(hit)} -- "
            "2022/2026 must not be intaken (CLAUDE.md rule 22)"
        )

    dupes = df[df.duplicated(["program", "year", "quarter"], keep=False)]
    if not dupes.empty:
        raise ValueError(f"{_rel(csv)}: duplicate key rows:\n{dupes}")

    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the auction-results partition; returns paths written.

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
