"""Curate the ``unit-outage-events`` clean datatype: per-unit outage windows.

Reads the CAMPD unit-outage detector's per-ISO CSVs (the committed output of
``scripts/data/derive_campd_unit_outages.py``) from ``data/raw`` and writes one
clean Parquet per ISO through :func:`scripts.lib.clean_io.write_clean`,
preserving the event grain (one row per detected outage window) rather than
expanding to hourly rows — the grain
:func:`market_sim.data.outages.unit_outage_derate_factors` consumes.

Sources (data/raw)
-------------------
- ``campd-unit-outages.csv`` — ERCOT.
- ``campd-unit-outages-<ISO>.csv`` — CAISO / MISO / NEISO / NYISO / PJM.

Both layouts share one header (``facility_name, facility_id, unit_id,
unit_capacity_mw, plant_capacity_mw, unit_pct_of_plant, plant_group,
capacity_source, outage_start, outage_end, duration_days, peer_units_online,
total_units_at_plant``); ``iso`` is stamped at curation time (the raw files
carry no iso column).

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

# ISOs with a CAMPD unit-outage extract, and the raw CSV filename for each.
_ISO_CSV: dict[str, str] = {
    "ERCOT": "campd-unit-outages.csv",
    "CAISO": "campd-unit-outages-CAISO.csv",
    "MISO": "campd-unit-outages-MISO.csv",
    "NEISO": "campd-unit-outages-NEISO.csv",
    "NYISO": "campd-unit-outages-NYISO.csv",
    "PJM": "campd-unit-outages-PJM.csv",
}

SCHEMA_COLUMNS: list[str] = [
    "iso",
    "plant_id",
    "unit_id",
    "facility_name",
    "unit_capacity_mw",
    "plant_capacity_mw",
    "unit_pct_of_plant",
    "plant_group",
    "capacity_source",
    "outage_start",
    "outage_end",
    "duration_days",
    "peer_units_online",
    "total_units_at_plant",
]


def _rel(path: Path) -> str:
    """Repo-relative path string for embedded provenance (``source=``)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_iso_events(csv_path: Path, iso: str) -> pd.DataFrame:
    """Read one ISO's unit-outage CSV into the canonical event-grain frame."""
    raw = pd.read_csv(csv_path, parse_dates=["outage_start", "outage_end"])
    df = pd.DataFrame(
        {
            "iso": pd.array([iso] * len(raw), dtype="string"),
            "plant_id": raw["facility_id"].astype("int64"),
            "unit_id": raw["unit_id"].astype("string"),
            "facility_name": raw["facility_name"].astype("string"),
            "unit_capacity_mw": pd.to_numeric(
                raw["unit_capacity_mw"], errors="coerce"
            ).astype("float64"),
            "plant_capacity_mw": pd.to_numeric(
                raw["plant_capacity_mw"], errors="coerce"
            ).astype("float64"),
            "unit_pct_of_plant": pd.to_numeric(
                raw["unit_pct_of_plant"], errors="coerce"
            ).astype("float64"),
            "plant_group": raw["plant_group"].astype("string"),
            "capacity_source": raw["capacity_source"].astype("string"),
            "outage_start": raw["outage_start"].astype("datetime64[ns]"),
            "outage_end": raw["outage_end"].astype("datetime64[ns]"),
            "duration_days": pd.to_numeric(
                raw["duration_days"], errors="coerce"
            ).astype("float64"),
            "peer_units_online": pd.to_numeric(
                raw["peer_units_online"], errors="coerce"
            ).astype("float64"),
            "total_units_at_plant": pd.to_numeric(
                raw["total_units_at_plant"], errors="coerce"
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
    """Curate every available ISO's unit-outage events; return ``{iso: path}``."""
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
        path = write_clean(df, "unit-outage-events", iso=iso, source=_rel(csv_path))
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
        print("no unit-outage-events curated (no source CSVs found)")
        return
    for iso, path in written.items():
        n = len(pd.read_parquet(path))
        print(f"wrote {iso:>6} {n:>6,} rows  ->  {path}")


if __name__ == "__main__":
    main()
