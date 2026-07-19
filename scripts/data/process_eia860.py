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
    python scripts/data/process_eia860.py --zip PATH [--out-dir DIR]

Defaults:
    --zip      data/raw/eia-860/eia8602024.zip
    --out-dir  data/raw/eia-860
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
    "Planned Retirement Month": "planned_retirement_month",
    "Status": "status",
}

# First backcast year the within-window retiree snapshot supports: a unit that
# retired in or after this calendar year operated for part of the backcast
# window and so belongs in the historical fleet snapshot (the COD ramp times it
# out by its retirement month). Units retired before it are gone for the whole
# window and are deliberately omitted. Bump only if the supported window moves.
RETIREMENT_WINDOW_START: int = 2023

# Output parquet of within-window retirees (mid-window plant exits the latest
# operable EIA-860 vintage no longer carries). Same canonical schema as the
# operable fleet plus the month-precise ``operating_month`` /
# ``planned_retirement_month`` the COD ramp reads — its actual retirement
# month/year is written into the ``planned_retirement_*`` columns so the single
# COD mechanism (data.cod_ramp) ages it out exactly as it does a planned exit.
RETIRED_WITHIN_WINDOW_PARQUET = "eia860_generator_retired_within_window.parquet"


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


# Column names that mark the real header row of an EIA-860 data sheet.
_HEADER_ANCHORS: frozenset[str] = frozenset({"Utility ID", "Plant Code"})


def _read_sheet(data: bytes, sheet: str) -> pd.DataFrame:
    """Read one EIA-860 sheet, locating the header row by its anchor columns.

    The final annual release carries a one-line title above the header; the
    Early Release adds a disclaimer paragraph as a second preamble row, so the
    header row is found by scanning for the first row containing a known
    anchor column ("Utility ID" / "Plant Code") rather than hardcoding it.
    """
    probe = pd.read_excel(io.BytesIO(data), sheet_name=sheet, header=None, nrows=6)
    header_row = 1  # final-release default: one title line
    for i in range(len(probe)):
        cells = {str(c).strip() for c in probe.iloc[i].tolist()}
        if cells & _HEADER_ANCHORS:
            header_row = i
            break
    return pd.read_excel(io.BytesIO(data), sheet_name=sheet, header=header_row)


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

    ba_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
        "Balancing Authority Code"
    ]

    df = generator[list(_GENERATOR_COLUMN_MAP)].rename(columns=_GENERATOR_COLUMN_MAP)
    df["balancing_authority_code"] = (
        df["plant_id"].map(ba_by_plant).astype("string").str.strip()
    )
    df = df[df["balancing_authority_code"].isin(BA_CODE_TO_ISO)]

    df["plant_id"] = df["plant_id"].astype("int64")
    df["generator_id"] = df["generator_id"].map(_stringify)
    for col in (
        "operating_year",
        "planned_retirement_year",
        "planned_retirement_month",
    ):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["status"] = df["status"].astype("string").str.strip()

    _join_egrid_heat_rate(df)

    return df[EIA_860_CSV_COLUMNS].reset_index(drop=True)


def _join_egrid_heat_rate(df: pd.DataFrame) -> None:
    """Add a plant-level ``heat_rate`` column (MMBtu/MWh) from eGRID PLNT23.

    The EIA-860 Generator_Y sheets carry no heat-rate column, so eGRID PLHTRT
    -- derived from CEMS fuel consumption -- is the source. It is plant-level,
    so every generator at a plant inherits the same value. Mutates ``df`` in
    place (keyed on its ``plant_id`` column); where the join misses, the fleet
    loader falls back to the vintage bin centers in HEAT_RATE_BINS.
    """
    from market_sim.config.paths import FLEET_DIR

    egrid_path = FLEET_DIR / "egrid2023_data_rev2.xlsx"
    if not egrid_path.exists():
        logger.warning(
            "eGRID workbook not found at %s; heat_rate left blank", egrid_path
        )
        df["heat_rate"] = pd.NA
        return
    egrid = pd.read_excel(
        egrid_path, sheet_name="PLNT23", skiprows=1, usecols=["ORISPL", "PLHTRT"]
    )
    hr = pd.to_numeric(egrid["PLHTRT"], errors="coerce")
    # Drop physically implausible plant heat rates -- negative or absurdly
    # large values appear for plants with near-zero net generation.
    egrid["PLHTRT"] = hr.where((hr >= 3_000) & (hr <= 30_000))
    egrid_hr = (
        egrid.dropna(subset=["ORISPL", "PLHTRT"])
        .drop_duplicates("ORISPL")
        .set_index("ORISPL")["PLHTRT"]
    )
    # Convert BTU/kWh -> MMBtu/MWh (divide by 1000).
    df["heat_rate"] = df["plant_id"].map(egrid_hr) / 1000.0
    matched = int(df["heat_rate"].notna().sum())
    logger.info(
        "  joined eGRID heat rates: %d of %d generators matched", matched, len(df)
    )


# Within-window retiree schema: the canonical fleet columns (which now carry
# ``planned_retirement_month``) plus ``operating_month`` — the two month-precise
# fields the COD ramp reads (the loader only requires them when present).
_RETIRED_COLUMNS: list[str] = EIA_860_CSV_COLUMNS + ["operating_month"]


def build_within_window_retirees(
    zip_paths: list[Path],
    operable_parquet: Path,
    cutoff_year: int = RETIREMENT_WINDOW_START,
) -> pd.DataFrame:
    """Return mid-window plant exits missing from the latest operable vintage.

    The committed operable EIA-860 vintage is a single recent snapshot, so a
    plant that retired *during* the backcast window (e.g. Mystic, plant 1588,
    a ~1.4 GW CC that ran through 2023 and retired mid-2024) is absent from
    every modeled year -- the COD ramp can only age out a unit that is in the
    snapshot. This reads the "Retired and Canceled" sheet of each *final*
    EIA-860 vintage in ``zip_paths``, keeps units that retired in or after
    ``cutoff_year`` (the window start), and returns them in the canonical fleet
    schema with their **actual** retirement month/year written into the
    ``planned_retirement_*`` columns and ``status`` forced to ``OP`` -- so the
    fleet loader keeps them and the single COD mechanism (:mod:`cod_ramp`) times
    each out by its real retirement month, exactly as it does a planned exit.

    Only *whole-plant* exits are emitted: any plant still present in
    ``operable_parquet`` is dropped (a partially-retired plant keeps its
    surviving units in the operable snapshot, and the plant-keyed COD map would
    hold the whole plant online -- so its retired units stay out to avoid an
    un-maskable over-count). Units are de-duplicated across vintages by
    ``(plant_id, generator_id)``, keeping the latest vintage's record.
    """
    operable_plant_ids: set[int] = set()
    if operable_parquet.exists():
        op = pd.read_parquet(operable_parquet, columns=["Plant Code"])
        operable_plant_ids = set(
            pd.to_numeric(op["Plant Code"], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )

    frames: list[pd.DataFrame] = []
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path) as zf:
            plant_name = next(n for n in zf.namelist() if "Plant_Y" in n)
            gen_name = next(n for n in zf.namelist() if "Generator_Y" in n)
            plant = _read_sheet(zf.read(plant_name), "Plant")
            retired = _read_sheet(zf.read(gen_name), "Retired and Canceled")

        retired = retired[pd.to_numeric(retired["Plant Code"], errors="coerce").notna()]
        plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()]
        ba_by_plant = plant.drop_duplicates("Plant Code").set_index("Plant Code")[
            "Balancing Authority Code"
        ]

        # The retired sheet carries ACTUAL "Retirement Year/Month" rather than
        # the operable sheet's "Planned Retirement Year" -- map every shared
        # column, then fill the planned_retirement_* fields from the actuals.
        shared = {
            k: v
            for k, v in _GENERATOR_COLUMN_MAP.items()
            if k in retired.columns and k != "Planned Retirement Year"
        }
        df = retired[list(shared)].rename(columns=shared)
        # Carry the real retirement into the planned_retirement_* columns the
        # COD ramp reads.
        df["operating_month"] = pd.to_numeric(
            retired["Operating Month"], errors="coerce"
        )
        df["planned_retirement_year"] = pd.to_numeric(
            retired["Retirement Year"], errors="coerce"
        )
        df["planned_retirement_month"] = pd.to_numeric(
            retired["Retirement Month"], errors="coerce"
        )
        df["balancing_authority_code"] = (
            df["plant_id"].map(ba_by_plant).astype("string").str.strip()
        )
        df = df[df["balancing_authority_code"].isin(BA_CODE_TO_ISO)]
        # Within-window exits only.
        df = df[df["planned_retirement_year"] >= cutoff_year]
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=_RETIRED_COLUMNS)

    df = pd.concat(frames, ignore_index=True)
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce").astype("int64")
    df["generator_id"] = df["generator_id"].map(_stringify)
    for col in ("operating_year", "planned_retirement_year"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("operating_month", "planned_retirement_month"):
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in ("nameplate_capacity_mw", "net_summer_capacity_mw"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Whole-plant exits only: drop any plant still carried by the operable
    # snapshot (its surviving units are already dispatched there).
    df = df[~df["plant_id"].isin(operable_plant_ids)]
    # Keep the latest vintage's record per unit (frames are vintage-ordered).
    df = df.drop_duplicates(subset=["plant_id", "generator_id"], keep="last")

    # The within-window retiree operated during the window; mark it OP so the
    # fleet loader keeps it -- the COD ramp owns the actual exit timing.
    df["status"] = "OP"
    _join_egrid_heat_rate(df)
    return df[_RETIRED_COLUMNS].reset_index(drop=True)


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
    parser.add_argument(
        "--retired-window-from",
        type=Path,
        nargs="+",
        default=None,
        metavar="ZIP",
        help="One or more FINAL EIA-860 annual zips whose 'Retired and "
        "Canceled' sheets supply within-window plant exits (e.g. Mystic) "
        "the latest operable vintage no longer carries. Writes "
        f"{RETIRED_WITHIN_WINDOW_PARQUET}.",
    )
    parser.add_argument(
        "--retired-only",
        action="store_true",
        help="Only (re)build the within-window retiree parquet from "
        "--retired-window-from; leave the operable parquets untouched.",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    if args.retired_only:
        if not args.retired_window_from:
            raise SystemExit("--retired-only requires --retired-window-from")
        _build_retired_window(args.retired_window_from, args.out_dir)
        return

    if not args.zip.exists():
        raise SystemExit(f"EIA-860 zip not found: {args.zip}")

    logger.info("Extracting all EIA-860 workbooks…")
    count = extract_all_workbooks(args.zip, args.out_dir)
    logger.info("Wrote %d raw parquet sheets", count)

    fleet = build_generator_table(args.zip)
    fleet_path = args.out_dir / "eia860_generators.parquet"
    fleet.to_parquet(fleet_path, index=False)

    if args.retired_window_from:
        _build_retired_window(args.retired_window_from, args.out_dir)

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


def _build_retired_window(zip_paths: list[Path], out_dir: Path) -> None:
    """Build and write the within-window retiree parquet, logging a summary."""
    for zp in zip_paths:
        if not zp.exists():
            raise SystemExit(f"EIA-860 zip not found: {zp}")
    operable_parquet = out_dir / "eia860_generator_operable.parquet"
    retired = build_within_window_retirees(zip_paths, operable_parquet)
    out_path = out_dir / RETIRED_WITHIN_WINDOW_PARQUET
    retired.to_parquet(out_path, index=False)
    logger.info(
        "Wrote %d within-window retiree units (%.1f GW, %d plants) to %s",
        len(retired),
        retired["nameplate_capacity_mw"].sum() / 1e3,
        retired["plant_id"].nunique(),
        out_path.name,
    )
    by_iso = (
        retired.assign(iso=retired["balancing_authority_code"].map(BA_CODE_TO_ISO))
        .groupby("iso")
        .agg(
            units=("generator_id", "size"),
            plants=("plant_id", "nunique"),
            nameplate_gw=("nameplate_capacity_mw", lambda s: round(s.sum() / 1e3, 2)),
        )
    )
    for iso, row in by_iso.iterrows():
        logger.info(
            "  %-6s %4d units / %3d plants  %6.2f GW",
            iso,
            int(row["units"]),
            int(row["plants"]),
            row["nameplate_gw"],
        )


if __name__ == "__main__":
    main()
