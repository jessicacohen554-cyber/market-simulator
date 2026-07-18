"""Curate the ``ira-credit-parameters`` clean datatype.

Lands the post-OBBBA §45U/§45Y/§48E statute parameters onto the tidy schema
in ``data/dictionary/schema/ira-credit-parameters.schema.yaml`` and writes
one Parquet partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Single hand-curated source: ``data/raw/policy/ira-credit-parameters/
ira-credit-parameters.csv`` (statute text cited per-row; see the raw
README for the full citation table and a flagged confidence caveat on the
45Y/48E non-wind/solar phase-down schedule). ``statute_section`` +
``parameter`` is the whole key (no year partitioning -- these are enacted
statute parameters, not a time series), so the whole datatype writes one
partition ``data/clean/ira-credit-parameters/ira-credit-parameters.parquet``
(``year=None``). Reads only ``data/raw``; idempotent; skips cleanly when the
CSV has not landed yet.

Run ``python scripts/data/curate_ira_credit_parameters.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

DATATYPE = "ira-credit-parameters"

_SECTIONS = {"45U", "45Y", "48E"}
_VALUE_TYPES = {"numeric", "date", "boolean"}

_COLUMNS = [
    "statute_section",
    "parameter",
    "value",
    "value_type",
    "unit",
    "notes",
    "source_doc",
    "source_page",
]


def raw_csv_path(raw_root: Path) -> Path:
    """Return the expected raw CSV path beneath ``raw_root``."""
    return raw_root / "policy" / "ira-credit-parameters" / f"{DATATYPE}.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def parse(raw_root: Path) -> pd.DataFrame:
    """Read and schema-shape the raw statute-parameters CSV (empty if not landed).

    Coerces dtypes to the canonical schema and enforces the
    statute_section/value_type vocabulary.
    """
    csv = raw_csv_path(raw_root)
    if not csv.exists():
        return pd.DataFrame(columns=_COLUMNS)

    df = pd.read_csv(csv, keep_default_na=False, na_values=[""])
    missing = set(_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"{_rel(csv)}: missing columns {sorted(missing)}")
    df = df[_COLUMNS].copy()

    df["statute_section"] = df["statute_section"].astype("string").str.strip()
    df["parameter"] = df["parameter"].astype("string").str.strip()
    df["value"] = df["value"].astype("string")
    df["value_type"] = df["value_type"].astype("string").str.strip()
    df["unit"] = df["unit"].astype("string").str.strip()
    df["notes"] = df["notes"].astype("string")
    df["source_doc"] = df["source_doc"].astype("string")
    df["source_page"] = df["source_page"].astype("string")

    bad_section = set(df["statute_section"]) - _SECTIONS
    if bad_section:
        raise ValueError(
            f"{_rel(csv)}: unknown statute_section(s) {sorted(bad_section)}"
        )
    bad_type = set(df["value_type"]) - _VALUE_TYPES
    if bad_type:
        raise ValueError(f"{_rel(csv)}: unknown value_type(s) {sorted(bad_type)}")

    dupes = df[df.duplicated(["statute_section", "parameter"], keep=False)]
    if not dupes.empty:
        raise ValueError(f"{_rel(csv)}: duplicate key rows:\n{dupes}")

    return df.reset_index(drop=True)


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write the statute-parameters partition; returns paths written.

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
