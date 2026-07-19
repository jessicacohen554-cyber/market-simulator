"""Curate the ``egrid`` clean datatype: plant-level eGRID extract per vintage.

Reads each eGRID vintage's plant sheet (``PLNT<YY>``, first row of long
descriptive headers skipped) from ``data/raw/fleet-egrid/`` and writes one
clean Parquet per vintage year through :func:`scripts.lib.clean_io.write_clean`.

The sheet feeds two different consumers, each historically reading its own
disjoint column subset directly from the 21 MB workbook:

* :mod:`market_sim.data.zone_assignment` — ``ORISPL, LAT, LON, FIPSST,
  FIPSCNTY, BACODE`` (geographic zone assignment).
* :mod:`market_sim.data.egrid` — ``ORISPL, PLFUELCT, PLNGENAN, PLCO2AN``
  (fleet-wide fossil CO2 emission rate).

This script reads the union of both column sets in one pass and writes the
unfiltered plant list (every plant in the sheet, fossil or not), so both
consumers can read one curated table and apply their own filtering downstream.

Idempotent and re-runnable; reads only ``data/raw``.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import pandas as pd

from market_sim.config.paths import FLEET_DIR  # noqa: E402
from scripts.lib.clean_io import validate_clean, write_clean  # noqa: E402

# eGRID plant-sheet workbooks by vintage year (mirrors market_sim.data.egrid).
EGRID_FILES: dict[int, str] = {
    2022: "egrid2022_data.xlsx",  # epa.gov eGRID2022 (retrieved 2026-07-04)
    2023: "egrid2023_data_rev2.xlsx",
    2024: "egrid2024_data.xlsx",
}

# eGRID plant-sheet short-code columns -> our snake_case schema columns.
_COLUMN_MAP: dict[str, str] = {
    "ORISPL": "plant_id",
    "LAT": "lat",
    "LON": "lon",
    "FIPSST": "fips_state",
    "FIPSCNTY": "fips_county",
    "BACODE": "ba_code",
    "PLFUELCT": "fuel_cat",
    "PLNGENAN": "net_mwh",
    "PLCO2AN": "co2_tons",
}

SCHEMA_COLUMNS: list[str] = list(_COLUMN_MAP.values())


def _rel(path: Path) -> str:
    """Repo-relative path string for embedded provenance (``source=``)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_egrid_plant_sheet(vintage: int, fleet_dir: Path = FLEET_DIR) -> pd.DataFrame:
    """Read one eGRID vintage's plant sheet into the unfiltered clean frame.

    Every plant in the sheet is kept (fossil or not, zero-generation or not);
    only the row's ``plant_id`` (eGRID ``ORISPL``) must be present — a plant
    with no ORIS code carries no usable key and is dropped.
    """
    path = fleet_dir / EGRID_FILES[vintage]
    sheet = f"PLNT{vintage % 100:02d}"
    raw = pd.read_excel(path, sheet_name=sheet, skiprows=1, usecols=list(_COLUMN_MAP))
    df = raw.rename(columns=_COLUMN_MAP)

    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df = df.dropna(subset=["plant_id"]).copy()
    df["plant_id"] = df["plant_id"].astype("int64")

    for col in ("lat", "lon", "fips_state", "fips_county", "net_mwh", "co2_tons"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
    df["ba_code"] = df["ba_code"].astype("string")
    df["fuel_cat"] = df["fuel_cat"].astype("string")

    return df[SCHEMA_COLUMNS].reset_index(drop=True)


def curate(
    vintages: list[int] | tuple[int, ...] | None = None,
    fleet_dir: Path = FLEET_DIR,
    *,
    write: bool = True,
) -> list[Path]:
    """Curate one or more eGRID vintages and return the written paths.

    ``vintages`` defaults to every vintage in :data:`EGRID_FILES` whose
    workbook is present on disk.
    """
    if vintages is None:
        vintages = [
            v for v, name in EGRID_FILES.items() if (fleet_dir / name).is_file()
        ]

    written: list[Path] = []
    for vintage in vintages:
        df = load_egrid_plant_sheet(vintage, fleet_dir)
        if not write or df.empty:
            continue
        source = _rel(fleet_dir / EGRID_FILES[vintage])
        path = write_clean(df, "egrid", year=vintage, source=source)
        validate_clean(path)
        written.append(path)
    return written


def main() -> None:
    written = curate()
    if not written:
        print("no egrid vintages curated (no source workbooks found)")
        return
    for path in written:
        n = len(pd.read_parquet(path))
        print(f"wrote {n:>6,} rows  ->  {path}")


if __name__ == "__main__":
    main()
