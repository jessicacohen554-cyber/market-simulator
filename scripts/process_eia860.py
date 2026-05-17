"""Process the raw EIA-860 release into a generator inventory parquet.

Reads the official EIA-860 annual zip (the workbooks ``2___Plant`` and
``3_1_Generator``), joins each operable generator to its plant's balancing
authority, restricts to the seven wholesale markets the simulator models,
and writes a single parquet in the loader's canonical column schema.

The parquet is the committed raw input consumed by
:func:`market_sim.data.fleet.load_fleet_from_csv`; it replaces the
synthetic fleet that was previously used as the only data source.

Usage:
    python scripts/process_eia860.py [--zip PATH] [--out PATH]

Defaults:
    --zip  inputs/raw-data/eia-860/eia8602024.zip
    --out  inputs/raw-data/eia-860/eia860_generators.parquet
"""

from __future__ import annotations

import argparse
import io
import logging
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.data.fleet import BA_CODE_TO_ISO, EIA_860_DIR, SYNTHETIC_CSV_COLUMNS

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("process_eia860")

# Substrings identifying the relevant workbooks inside the EIA-860 zip.
_PLANT_WORKBOOK = "Plant_Y"
_GENERATOR_WORKBOOK = "Generator_Y"

# EIA-860 generator-sheet column → canonical loader column.
_GENERATOR_COLUMN_MAP: dict[str, str] = {
    "Plant Code": "plant_id",
    "Generator ID": "generator_id",
    "Plant Name": "plant_name",
    "State": "state",
    "Technology": "technology",
    "Energy Source 1": "energy_source",
    "Prime Mover": "prime_mover",
    "Nameplate Capacity (MW)": "nameplate_capacity_mw",
    "Summer Capacity (MW)": "net_summer_capacity_mw",
    "Operating Year": "operating_year",
    "Planned Retirement Year": "planned_retirement_year",
    "Status": "status",
}


def _read_workbook(zf: zipfile.ZipFile, marker: str, sheet: str) -> pd.DataFrame:
    """Read a sheet from the EIA-860 workbook whose name contains ``marker``."""
    names = [n for n in zf.namelist() if marker in n and n.endswith(".xlsx")]
    if not names:
        raise FileNotFoundError(f"No workbook matching '{marker}' in the zip")
    with zf.open(names[0]) as handle:
        data = io.BytesIO(handle.read())
    # EIA-860 workbooks carry a one-line title above the header row.
    return pd.read_excel(data, sheet_name=sheet, header=1)


def _coerce_generator_id(value: object) -> str:
    """Return a clean string generator ID (Excel may read ``"1"`` as ``1.0``)."""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def build_generator_table(zip_path: Path) -> pd.DataFrame:
    """Return the canonical-schema generator table for the seven markets."""
    with zipfile.ZipFile(zip_path) as zf:
        plant = _read_workbook(zf, _PLANT_WORKBOOK, "Plant")
        generator = _read_workbook(zf, _GENERATOR_WORKBOOK, "Operable")

    # Drop trailing footer/blank rows (Plant Code is non-numeric there).
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
    generator = generator[
        pd.to_numeric(generator["Plant Code"], errors="coerce").notna()
    ]

    ba_by_plant = (
        plant.drop_duplicates("Plant Code")
        .set_index("Plant Code")["Balancing Authority Code"]
    )

    df = generator[list(_GENERATOR_COLUMN_MAP)].rename(
        columns=_GENERATOR_COLUMN_MAP
    )
    df["balancing_authority_code"] = (
        df["plant_id"].map(ba_by_plant).astype("string").str.strip()
    )
    df = df[df["balancing_authority_code"].isin(BA_CODE_TO_ISO)]

    df["plant_id"] = df["plant_id"].astype("int64")
    df["generator_id"] = df["generator_id"].map(_coerce_generator_id)
    for col in ("operating_year", "planned_retirement_year"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip()

    return df[SYNTHETIC_CSV_COLUMNS].reset_index(drop=True)


def main() -> None:
    """Process the EIA-860 zip into the committed generator parquet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip",
        type=Path,
        default=EIA_860_DIR / "eia8602024.zip",
        help="Path to the raw EIA-860 annual zip.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=EIA_860_DIR / "eia860_generators.parquet",
        help="Destination parquet path.",
    )
    args = parser.parse_args()

    if not args.zip.exists():
        raise SystemExit(f"EIA-860 zip not found: {args.zip}")

    df = build_generator_table(args.zip)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(args.out, index=False)

    by_iso = (
        df.assign(iso=df["balancing_authority_code"].map(BA_CODE_TO_ISO))
        .groupby("iso")
        .agg(
            generators=("generator_id", "size"),
            nameplate_gw=("nameplate_capacity_mw", lambda s: round(s.sum() / 1e3, 1)),
        )
    )
    logger.info("Wrote %d generators to %s", len(df), args.out)
    for iso, row in by_iso.iterrows():
        logger.info(
            "  %-6s %5d generators  %7.1f GW nameplate",
            iso,
            int(row["generators"]),
            row["nameplate_gw"],
        )


if __name__ == "__main__":
    main()
