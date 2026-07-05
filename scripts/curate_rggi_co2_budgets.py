"""Curate the ``rggi-co2-budgets`` clean datatype.

Lands the RGGI regional and per-member-state annual CO2 allowance budgets and
the price-control-band trigger-price schedule (Cost Containment Reserve,
Emissions Containment Reserve, minimum reserve/floor) onto the tidy schema in
``data/dictionary/schema/rggi-co2-budgets.schema.yaml`` and writes one Parquet
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Single hand-curated source: ``data/raw/policy/rggi-co2-budgets/
rggi-co2-budgets.csv`` (regional/per-state, cited to RGGI, Inc. filings). The
budget year is a *column* (one file spans many years), so the whole datatype
writes one partition ``data/clean/rggi-co2-budgets/rggi-co2-budgets.parquet``
(``year=None``). Reads only ``data/raw``; idempotent; skips cleanly when the CSV
has not landed yet (the optional power-sector mass-cap row stays inert until
then; see ``docs/handoffs/emissions-mass-cap-plan-2026-07.md`` §7).

HOLDOUT QUARANTINE (CLAUDE.md rule 22): rows for 2022 or 2026 are rejected —
those years are under full quarantine (no data intake) until the holdout is
released. Run ``python scripts/curate_rggi_co2_budgets.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "rggi-co2-budgets"

# Allowed vocabularies (schema-enforced downstream; guarded here for a clear
# error at curation time rather than a dtype/round-trip failure).
_METRICS = {
    "allowance_budget",
    "ccr_trigger_price",
    "ecr_trigger_price",
    "minimum_reserve_price",
}
_UNITS = {"short_tons", "usd_per_short_ton"}
# Years under full holdout quarantine — never intaken (CLAUDE.md rule 22).
_QUARANTINED_YEARS = frozenset({2022, 2026})

_COLUMNS = [
    "state",
    "budget_year",
    "metric",
    "value",
    "unit",
    "source_doc",
    "source_page",
]


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
    """Read and schema-shape the raw RGGI budget CSV (empty if it has not landed).

    Coerces dtypes to the canonical schema, upper-cases the state code, and
    enforces the metric/unit vocabulary and the holdout-year quarantine.
    """
    csv = raw_csv_path(raw_root)
    if not csv.exists():
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.read_csv(csv)
    missing = set(_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_rel(csv)}: missing columns {sorted(missing)}")
    df = df[_COLUMNS].copy()

    df["state"] = df["state"].astype("string").str.strip().str.upper()
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
    """Curate and write the RGGI CO2 budget partition; returns paths written.

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
