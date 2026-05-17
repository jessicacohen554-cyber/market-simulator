"""Process the raw EIA-860 release into parquet.

Two outputs are produced from the official EIA-860 annual zip:

1. A faithful parquet of every data sheet in every workbook
   (``eia860_<workbook>[_<sheet>].parquet``) -- utilities, plants,
   generators, wind, solar, storage, multifuel, ownership and the
   environmental schedules.
2. ``eia860_generators.parquet`` -- operable generators for the seven
   wholesale markets, joined to their plant's balancing authority and
   reduced to the loader's canonical schema. This is the file consumed by
   :func:`market_sim.data.fleet.load_fleet_from_csv`.

Usage:
    python scripts/process_eia860.py --zip PATH [--out-dir DIR]

Defaults:
    --zip      inputs/raw-data/eia-860/eia8602024.zip
    --out-dir  inputs/raw-data/eia-860
"""

from __future__ import annotations

import argparse
import io
import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.data.fleet import BA_CODE_TO_ISO, EIA_860_CSV_COLUMNS, EIA_860_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("process_eia860")

# Filename marker (workbook) → short slug used in the output parquet name.
_WORKBOOK_SLUGS: dict[str, str] = {
    "Utility_Y": "utility",
    "Plant_Y": "plant",
    "Generator_Y": "generator",
    "Wind_Y": "wind",
    "Solar_Y": "solar",
    "Energy_Storage_Y": "energy_storage",
    "Multifuel_Y": "multifuel",
    "Owner_Y": "owner",
    "EnviroAssoc_Y": "enviro_assoc",
    "EnviroEquip_Y": "enviro_equip",
}

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


def _slug(text: str) -> str:
    """Return a lower-case underscore slug for a sheet or workbook name."""
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", text.lower())).strip("_")


def _stringify(value: object) -> object:
    """Coerce an object-column cell to a clean string (or ``None``)."""
    if value is None:
        return None
    if isinstance(value, float):
        if value != value:  # NaN
            return None
        return str(int(value)) if value.is_integer() else str(value)
    return str(value).strip()


def _clean_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Drop blank rows and make object columns parquet-safe."""
    df = df.dropna(how="all").reset_index(drop=True)
    df.columns = [str(c).strip() for c in df.columns]
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].map(_stringify)
    return df


def _read_sheet(data: bytes, sheet: str) -> pd.DataFrame:
    """Read one EIA-860 sheet (the workbook carries a one-line title)."""
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet, header=1)


def extract_all_workbooks(zip_path: Path, out_dir: Path) -> int:
    """Write every data sheet of every EIA-860 workbook to a parquet.

    Returns the number of parquet files written.
    """
    written = 0
    with zipfile.ZipFile(zip_path) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".xlsx"):
                continue
            slug = next(
                (s for marker, s in _WORKBOOK_SLUGS.items() if marker in name),
                None,
            )
            if slug is None:  # blank form, layout key, etc.
                continue
            data = zf.read(name)
            sheets = pd.ExcelFile(io.BytesIO(data)).sheet_names
            for sheet in sheets:
                df = _clean_sheet(_read_sheet(data, sheet))
                stem = slug if len(sheets) == 1 else f"{slug}_{_slug(sheet)}"
                path = out_dir / f"eia860_{stem}.parquet"
                df.to_parquet(path, index=False)
                logger.info(
                    "  %-46s %6d rows x %2d cols", path.name, len(df), df.shape[1]
                )
                written += 1
    return written


def build_generator_table(zip_path: Path) -> pd.DataFrame:
    """Return the canonical-schema generator table for the seven markets."""
    with zipfile.ZipFile(zip_path) as zf:
        plant_name = next(n for n in zf.namelist() if "Plant_Y" in n)
        gen_name = next(n for n in zf.namelist() if "Generator_Y" in n)
        plant = _read_sheet(zf.read(plant_name), "Plant")
        generator = _read_sheet(zf.read(gen_name), "Operable")

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
    df["generator_id"] = df["generator_id"].map(_stringify)
    for col in ("operating_year", "planned_retirement_year"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip()

    return df[EIA_860_CSV_COLUMNS].reset_index(drop=True)


def main() -> None:
    """Extract the full EIA-860 release and build the fleet loader parquet."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--zip",
        type=Path,
        default=EIA_860_DIR / "eia8602024.zip",
        help="Path to the raw EIA-860 annual zip.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=EIA_860_DIR,
        help="Directory for the parquet outputs.",
    )
    args = parser.parse_args()

    if not args.zip.exists():
        raise SystemExit(f"EIA-860 zip not found: {args.zip}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting all EIA-860 workbooks…")
    count = extract_all_workbooks(args.zip, args.out_dir)
    logger.info("Wrote %d raw parquet sheets", count)

    fleet = build_generator_table(args.zip)
    fleet_path = args.out_dir / "eia860_generators.parquet"
    fleet.to_parquet(fleet_path, index=False)

    by_iso = (
        fleet.assign(iso=fleet["balancing_authority_code"].map(BA_CODE_TO_ISO))
        .groupby("iso")
        .agg(
            generators=("generator_id", "size"),
            nameplate_gw=("nameplate_capacity_mw", lambda s: round(s.sum() / 1e3, 1)),
        )
    )
    logger.info("Wrote %d market generators to %s", len(fleet), fleet_path.name)
    for iso, row in by_iso.iterrows():
        logger.info(
            "  %-6s %5d generators  %7.1f GW nameplate",
            iso,
            int(row["generators"]),
            row["nameplate_gw"],
        )


if __name__ == "__main__":
    main()
