"""Curate the ``carb-cap-schedule`` clean datatype.

Lands the California cap-and-trade annual allowance budget (MMT CO2e) and the
Auction Reserve (floor) price schedule ($/tonne) onto the tidy schema in
``data/dictionary/schema/carb-cap-schedule.schema.yaml`` and writes one Parquet
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Single hand-curated source: ``data/raw/policy/carb-cap-schedule/
carb-cap-schedule.csv`` (cited to CARB Cap-and-Trade Regulation §95841/§95911
and the annual auction-reserve-price notice). The budget year is a *column*, so
the whole datatype writes one partition
``data/clean/carb-cap-schedule/carb-cap-schedule.parquet`` (``year=None``).
Reads only ``data/raw``; idempotent; skips cleanly when the CSV has not landed
yet (the optional power-sector mass-cap row stays inert until then; see
``docs/handoffs/emissions-mass-cap-plan-2026-07.md`` §7).

HOLDOUT QUARANTINE (CLAUDE.md rule 22): rows for 2022 or 2026 are rejected —
those years are under full quarantine (no data intake) until the holdout is
released. Run ``python scripts/data/curate_carb_cap_schedule.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "carb-cap-schedule"

_METRICS = {"allowance_budget", "auction_reserve_price"}
_UNITS = {"mmt_co2e", "usd_per_tonne"}
# Years under full holdout quarantine — never intaken (CLAUDE.md rule 22).
_QUARANTINED_YEARS = frozenset({2022, 2026})

_COLUMNS = ["budget_year", "metric", "value", "unit", "source_doc", "source_page"]


def raw_csv_path(raw_root: Path) -> Path:
    """Return the expected raw CSV path beneath ``raw_root``."""
    return raw_root / "policy" / DATATYPE / f"{DATATYPE}.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def parse(raw_root: Path) -> pd.DataFrame:
    """Read and schema-shape the raw CARB schedule CSV (empty if not landed).

    Coerces dtypes to the canonical schema and enforces the metric/unit
    vocabulary and the holdout-year quarantine.
    """
    csv = raw_csv_path(raw_root)
    if not csv.exists():
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.read_csv(csv)
    missing = set(_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_rel(csv)}: missing columns {sorted(missing)}")
    df = df[_COLUMNS].copy()

    df["budget_year"] = df["budget_year"].astype("int64")
    df["metric"] = df["metric"].astype("string").str.strip()
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
    hit = _QUARANTINED_YEARS & set(df["budget_year"].tolist())
    if hit:
        raise ValueError(
            f"{_rel(csv)}: holdout-quarantined budget_year(s) {sorted(hit)} — "
            "2022/2026 must not be intaken (CLAUDE.md rule 22)"
        )
    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the CARB schedule partition; returns paths written.

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
