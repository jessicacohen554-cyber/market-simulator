"""Curate the ``nyiso-renewable-curtailment`` / ``-monthly`` clean datatypes.

Reads the hand-transcribed source CSVs under
``data/raw/nyiso-renewable-curtailment/`` (see that directory's README for the
primary-source NYCA Renewables presentation decks and documented year gaps),
shapes them onto the two schemas in
``data/dictionary/schema/nyiso-renewable-curtailment{,-monthly}.schema.yaml``,
and writes each through the frozen :func:`scripts.lib.clean_io.write_clean`
seam. Both datatypes span every transcribed year in one file (``year=None``);
the year is a column, not a partition, since row counts are small.

Run ``python scripts/data/curate_nyiso_renewable_curtailment.py``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.lib import clean_io
from scripts.lib.clean_io import paths

ANNUAL_DATATYPE = "nyiso-renewable-curtailment"
MONTHLY_DATATYPE = "nyiso-renewable-curtailment-monthly"

_ANNUAL_CSV = "nyiso_curtailment_annual.csv"
_MONTHLY_CSV = "nyiso_curtailment_monthly.csv"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _raw_dir(raw_root: Path) -> Path:
    return raw_root / "nyiso-renewable-curtailment"


def build_annual_frame(raw_root: Path) -> pd.DataFrame:
    """Read and dtype-shape the annual curtailment CSV onto its schema."""
    df = pd.read_csv(_raw_dir(raw_root) / _ANNUAL_CSV)
    df["year"] = df["year"].astype("int64")
    df["curtailed_energy_gwh"] = df["curtailed_energy_gwh"].astype("float64")
    df["curtailed_pct"] = df["curtailed_pct"].astype("float64")
    df["source_page"] = df["source_page"].astype("string").astype(object)
    df["notes"] = df["notes"].where(df["notes"].notna(), None)
    return df


def build_monthly_frame(raw_root: Path) -> pd.DataFrame:
    """Read and dtype-shape the monthly curtailment CSV onto its schema."""
    df = pd.read_csv(_raw_dir(raw_root) / _MONTHLY_CSV)
    df["year"] = df["year"].astype("int64")
    df["month"] = df["month"].astype("int64")
    df["curtailed_energy_gwh"] = df["curtailed_energy_gwh"].astype("float64")
    df["curtailed_pct"] = df["curtailed_pct"].astype("float64")
    df["source_page"] = df["source_page"].astype("string").astype(object)
    return df


def curate(raw_root: Path | None = None) -> list[Path]:
    """Curate and write both NYISO renewable-curtailment partitions.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    source = (
        f"{_rel(_raw_dir(raw_root) / _ANNUAL_CSV)} / "
        f"{_rel(_raw_dir(raw_root) / _MONTHLY_CSV)} "
        "(hand-transcribed from NYISO NYCA Renewables presentation decks; "
        "see raw README for source URLs and documented gaps)"
    )

    written: list[Path] = []

    annual = build_annual_frame(raw_root)
    path = clean_io.write_clean(annual, ANNUAL_DATATYPE, iso="NYISO", source=source)
    clean_io.validate_clean(path)
    written.append(path)
    print(f"wrote {path}  ({len(annual)} rows)")

    monthly = build_monthly_frame(raw_root)
    path = clean_io.write_clean(monthly, MONTHLY_DATATYPE, iso="NYISO", source=source)
    clean_io.validate_clean(path)
    written.append(path)
    print(f"wrote {path}  ({len(monthly)} rows)")

    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args(argv)
    del args
    written = curate()
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
