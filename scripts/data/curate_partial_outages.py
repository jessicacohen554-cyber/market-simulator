"""Curate the ``partial-outages`` clean datatype: per-plant derate windows.

Reads ``campd-partial-outages.csv`` (CAMPD CF-ceiling plateau windows, the
committed output of ``scripts/data/derive_partial_outages.py``) from ``data/raw``
and writes one clean Parquet per ISO through
:func:`scripts.lib.clean_io.write_clean`. The source is ERCOT-only today;
``iso`` is stamped at curation time (the raw file carries no iso column).

Feeds :func:`market_sim.data.outages.partial_outage_derate_factors`.

Idempotent and re-runnable; reads only ``data/raw``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

# ISOs with a CAMPD partial-outage extract, and the raw CSV filename for each.
_ISO_CSV: dict[str, str] = {
    "ERCOT": "campd-partial-outages.csv",
}

SCHEMA_COLUMNS: list[str] = [
    "iso",
    "plant_id",
    "plant_name",
    "plant_group",
    "year",
    "outage_start",
    "outage_stop",
    "derate_factor",
]


def _rel(path: Path) -> str:
    """Repo-relative path string for embedded provenance (``source=``)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_iso_events(csv_path: Path, iso: str) -> pd.DataFrame:
    """Read one ISO's partial-outage CSV into the canonical frame."""
    raw = pd.read_csv(csv_path, parse_dates=["outage_start", "outage_stop"])
    df = pd.DataFrame(
        {
            "iso": pd.array([iso] * len(raw), dtype="string"),
            "plant_id": raw["oris_code"].astype("int64"),
            "plant_name": raw["plant_name"].astype("string"),
            "plant_group": raw["plant_group"].astype("string"),
            "year": raw["year"].astype("int64"),
            "outage_start": raw["outage_start"].astype("datetime64[ns]"),
            "outage_stop": raw["outage_stop"].astype("datetime64[ns]"),
            "derate_factor": pd.to_numeric(
                raw["derate_factor"], errors="coerce"
            ).astype("float64"),
        }
    )
    return df[SCHEMA_COLUMNS]


def curate(
    raw_dir: Path | None = None,
    isos: list[str] | None = None,
    *,
    write: bool = True,
) -> dict[str, Path]:
    """Curate every available ISO's partial-outage windows; return ``{iso: path}``."""
    raw_dir = Path(raw_dir) if raw_dir is not None else RAW_DATA_DIR
    isos = isos or list(_ISO_CSV)

    written: dict[str, Path] = {}
    for iso in isos:
        csv_path = raw_dir / _ISO_CSV[iso]
        if not csv_path.is_file():
            continue
        df = load_iso_events(csv_path, iso)
        if not write or df.empty:
            continue
        path = write_clean(df, "partial-outages", iso=iso, source=_rel(csv_path))
        validate_clean(path)
        written[iso] = path
    return written


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--raw-dir", default=None, help="Override the data/raw root (for testing)."
    )
    ap.add_argument(
        "--iso",
        nargs="+",
        choices=sorted(_ISO_CSV),
        default=None,
        help="ISO(s) to curate (default: all available).",
    )
    args = ap.parse_args()
    written = curate(raw_dir=args.raw_dir, isos=args.iso)
    if not written:
        print("no partial-outages curated (no source CSVs found)")
        return
    for iso, path in written.items():
        n = len(pd.read_parquet(path))
        print(f"wrote {iso:>6} {n:>6,} rows  ->  {path}")


if __name__ == "__main__":
    main()
