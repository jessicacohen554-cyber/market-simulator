"""Curate the ``fleet`` clean datatype from EIA-860, eGRID and the registry.

The generator fleet registry — one row per ``(plant_id, unit_id)`` — reconciled
across the three raw generator-registry sources into the canonical
``data/dictionary/schema/fleet.schema.yaml`` columns and written through the
shared :func:`scripts.lib.clean_io.write_clean` seam.

Sources and their roles
-----------------------
* **EIA-860** (``data/raw/eia-860``) is the authoritative *unit-grain* spine.
  ``eia860_generator_operable.parquet`` carries the spaced/parenthesized headers
  the schema reconciles — ``"Plant Code"`` -> ``plant_id``, ``"Generator ID"`` ->
  ``unit_id``, ``"Nameplate Capacity (MW)"`` -> ``nameplate_capacity_mw``,
  ``"Nameplate Energy Capacity (MWh)"`` -> ``energy_capacity_mwh`` (the last from
  the companion ``eia860_energy_storage_operable.parquet``, joined on the unit
  key). Energy source + prime mover + CHP flag are mapped onto the canonical
  fuel vocabulary (the repo's :data:`EIA930_FUELS`) via the single-source-of-
  truth :func:`classify_plant`.
* **eGRID** (``data/raw/fleet-egrid/*.xlsx``) and the **master plant registry**
  (``data/raw/reference/master-plant-registry.csv``) are reconciled in as the
  ``iso`` enrichment layer: a plant_id -> ISO map is built from eGRID's plant
  sheet balancing-authority code (``BACODE``) and the registry's ``ba_code``,
  using the canonical ISO<->BA crosswalk. eGRID's plant sheet has a two-row
  header (a descriptive row above the short-code row); :func:`load_egrid_iso_map`
  locates the real header row by its code tokens rather than assuming a position.

Vintage handling
----------------
The schema is vintage-agnostic. EIA-860 ships several vintages under
``data/raw/eia-860``: the top-level directory (the 2025 Early Release snapshot,
operating years through 2025) plus ``vintage_<year>/`` subdirectories. Each
vintage is curated independently and **partitioned by year** through
``write_clean(df, "fleet", year=<vintage>)`` -> ``data/clean/fleet/fleet_<year>
.parquet``. ``zone`` is left null (model-zone assignment from geography is out of
scope for the registry); the schema marks it nullable.

Idempotent and re-runnable: reads only ``data/raw`` and overwrites the clean
parquet in place.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))  # so ``scripts.lib.clean_io`` resolves as a script

from market_sim.config import paths  # noqa: E402
from market_sim.config.plant_taxonomy import (  # noqa: E402
    EIA930_FUELS,  # noqa: F401  re-exported for tests asserting the fuel vocab
    classify_plant,
    fuel930_of,
)
from market_sim.data.zone_assignment import _ISO_TO_BA_CODE  # noqa: E402
from scripts.lib import clean_io  # noqa: E402

logger = logging.getLogger("curate_fleet")

# The 2025 Early Release snapshot lives at the top of the EIA-860 tree (operating
# years through 2025); year-matched vintages live in vintage_<year>/ subdirs.
TOP_LEVEL_VINTAGE_YEAR = 2025

# Raw EIA-860 file names (constant across vintages).
GENERATOR_OPERABLE = "eia860_generator_operable.parquet"
ENERGY_STORAGE_OPERABLE = "eia860_energy_storage_operable.parquet"

# The canonical schema columns, in order, that every emitted frame carries.
FLEET_COLUMNS = [
    "plant_id",
    "unit_id",
    "iso",
    "zone",
    "plant_name",
    "fuel",
    "prime_mover",
    "technology",
    "nameplate_capacity_mw",
    "summer_capacity_mw",
    "winter_capacity_mw",
    "energy_capacity_mwh",
    "operating_year",
]

# EIA-860 spaced/parenthesized headers -> canonical snake_case + unit suffixes.
# The energy-source / CHP columns are read for fuel mapping but not emitted.
_EIA860_RENAME = {
    "Plant Code": "plant_id",
    "Generator ID": "unit_id",
    "Plant Name": "plant_name",
    "Technology": "technology",
    "Prime Mover": "prime_mover",
    "Nameplate Capacity (MW)": "nameplate_capacity_mw",
    "Summer Capacity (MW)": "summer_capacity_mw",
    "Winter Capacity (MW)": "winter_capacity_mw",
    "Operating Year": "operating_year",
}

# BA code -> ISO, inverted from the canonical ISO->BA crosswalk so curation and
# the model never drift on which balancing authority is which ISO.
_BA_TO_ISO = {ba: iso for iso, ba in _ISO_TO_BA_CODE.items()}

# Storage energy-source / prime-mover codes that bucket a unit as "storage"
# rather than letting MWH fall through classify_plant's residual OTHER bucket.
_STORAGE_SOURCES = {"MWH"}
_STORAGE_PRIME_MOVERS = {"BA", "FW"}


def canonical_fuel(
    energy_source: object,
    prime_mover: object,
    technology: object,
    chp_flag: object,
    plant_id: object,
) -> str:
    """Map a unit's raw EIA codes onto the canonical fuel vocabulary.

    Returns one of :data:`EIA930_FUELS` (``coal``/``gas``/``nuclear``/``hydro``/
    ``wind``/``solar``/``oil``/``storage``/``other``). Storage is detected first
    (EIA's ``MWH`` energy source / battery / flywheel prime movers), then the
    unit is run through the canonical :func:`classify_plant` and its model class
    rolled up to the reporting bucket with :func:`fuel930_of`.
    """
    src = str(energy_source or "").strip().upper()
    pm = str(prime_mover or "").strip().upper()
    tech = str(technology or "").strip().lower()
    if src in _STORAGE_SOURCES or pm in _STORAGE_PRIME_MOVERS or "batter" in tech:
        return "storage"
    chp = str(chp_flag or "").strip().upper() == "Y"
    try:
        pid = int(float(plant_id))
    except (TypeError, ValueError):
        pid = 0
    return fuel930_of(classify_plant(src, pm, chp, pid))


def _egrid_plant_sheet(xl: pd.ExcelFile) -> str | None:
    """Return the plant-level sheet name (``PLNT<yy>``) of an eGRID workbook."""
    for name in xl.sheet_names:
        if str(name).upper().startswith("PLNT"):
            return name
    return None


def _find_header_row(raw: pd.DataFrame, tokens: set[str]) -> int | None:
    """Index of the first row whose cells contain all ``tokens`` (eGRID codes).

    eGRID sheets carry a descriptive header row above the short-code row, so a
    naive read yields ``Unnamed:`` columns; this locates the real (code) header
    by content instead of by a hard-coded position.
    """
    for i in range(min(len(raw), 10)):
        cells = {str(v).strip().upper() for v in raw.iloc[i].tolist()}
        if tokens <= cells:
            return i
    return None


def load_egrid_iso_map(egrid_path: Path) -> dict[int, str]:
    """Build a ``plant_id -> iso`` map from an eGRID workbook's plant sheet.

    Reads the ``ORISPL`` (plant code) and ``BACODE`` (balancing authority)
    columns and maps each BA to its ISO via :data:`_BA_TO_ISO`. Plants whose BA
    is not an ISO/RTO are omitted. Returns an empty map if the file or the
    expected columns are absent.
    """
    if not Path(egrid_path).is_file():
        return {}
    xl = pd.ExcelFile(egrid_path)
    sheet = _egrid_plant_sheet(xl)
    if sheet is None:
        return {}
    probe = pd.read_excel(egrid_path, sheet_name=sheet, header=None, nrows=10)
    header = _find_header_row(probe, {"ORISPL", "BACODE"})
    if header is None:
        return {}
    df = pd.read_excel(egrid_path, sheet_name=sheet, header=header)
    df = df[["ORISPL", "BACODE"]].dropna(subset=["ORISPL"])
    out: dict[int, str] = {}
    for plant, ba in zip(df["ORISPL"], df["BACODE"]):
        iso = _BA_TO_ISO.get(str(ba).strip())
        if iso is not None:
            try:
                out[int(plant)] = iso
            except (TypeError, ValueError):
                continue
    return out


def load_registry_iso_map(registry_csv: Path) -> dict[int, str]:
    """Build a ``plant_id -> iso`` map from the master plant registry.

    Uses the registry's ``plantid`` and ``ba_code`` columns (mapped to ISO via
    :data:`_BA_TO_ISO`). Returns an empty map if the file is absent.
    """
    if not Path(registry_csv).is_file():
        return {}
    df = pd.read_csv(registry_csv, usecols=["plantid", "ba_code"])
    out: dict[int, str] = {}
    for plant, ba in zip(df["plantid"], df["ba_code"]):
        iso = _BA_TO_ISO.get(str(ba).strip())
        if iso is not None:
            try:
                out[int(plant)] = iso
            except (TypeError, ValueError):
                continue
    return out


def build_fleet_frame(
    gen_df: pd.DataFrame,
    storage_df: pd.DataFrame | None = None,
    iso_map: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Reconcile EIA-860 generator + storage frames into the fleet schema.

    Renames the spaced/parenthesized EIA-860 headers to canonical snake_case,
    maps fuel onto the canonical vocabulary, joins storage energy capacity on the
    unit key, attaches ISO from ``iso_map`` (when given) and returns exactly the
    canonical :data:`FLEET_COLUMNS` with schema-correct dtypes, one row per
    ``(plant_id, unit_id)``.
    """
    iso_map = iso_map or {}
    df = gen_df.rename(columns=_EIA860_RENAME)

    # Drop rows missing a key or the non-nullable nameplate capacity (trailing
    # summary / blank rows in the raw extracts).
    df = df.copy()
    df["plant_id"] = pd.to_numeric(df["plant_id"], errors="coerce")
    df["nameplate_capacity_mw"] = pd.to_numeric(
        df["nameplate_capacity_mw"], errors="coerce"
    )
    df = df.dropna(subset=["plant_id", "unit_id", "nameplate_capacity_mw"])

    df["plant_id"] = df["plant_id"].astype("int64")
    df["unit_id"] = df["unit_id"].astype("string").str.strip()
    df = df.drop_duplicates(subset=["plant_id", "unit_id"], keep="first")

    # Fuel from energy source + prime mover + CHP flag (columns not emitted).
    energy_source = df.get("Energy Source 1")
    chp = df.get("Associated with Combined Heat and Power System")
    df["fuel"] = [
        canonical_fuel(es, pm, tech, ch, pid)
        for es, pm, tech, ch, pid in zip(
            energy_source if energy_source is not None else [None] * len(df),
            df["prime_mover"],
            df["technology"],
            chp if chp is not None else [None] * len(df),
            df["plant_id"],
        )
    ]

    # Numeric coercions for the optional capacity / year columns.
    for col in ("summer_capacity_mw", "winter_capacity_mw"):
        df[col] = pd.to_numeric(df.get(col), errors="coerce").astype("float64")
    df["nameplate_capacity_mw"] = df["nameplate_capacity_mw"].astype("float64")
    df["operating_year"] = pd.to_numeric(
        df.get("operating_year"), errors="coerce"
    ).astype("Int64")

    # Storage energy capacity joined on the unit key.
    df["energy_capacity_mwh"] = pd.Series(float("nan"), index=df.index, dtype="float64")
    if storage_df is not None and len(storage_df):
        s = storage_df.rename(
            columns={
                "Plant Code": "plant_id",
                "Generator ID": "unit_id",
                "Nameplate Energy Capacity (MWh)": "energy_capacity_mwh",
            }
        )
        s = s[["plant_id", "unit_id", "energy_capacity_mwh"]].copy()
        s["plant_id"] = pd.to_numeric(s["plant_id"], errors="coerce")
        s = s.dropna(subset=["plant_id", "unit_id"])
        s["plant_id"] = s["plant_id"].astype("int64")
        s["unit_id"] = s["unit_id"].astype("string").str.strip()
        s["energy_capacity_mwh"] = pd.to_numeric(
            s["energy_capacity_mwh"], errors="coerce"
        ).astype("float64")
        s = s.drop_duplicates(subset=["plant_id", "unit_id"], keep="first")
        df = df.merge(s, on=["plant_id", "unit_id"], how="left", suffixes=("", "_s"))
        df["energy_capacity_mwh"] = df["energy_capacity_mwh_s"].astype("float64")
        df = df.drop(columns=["energy_capacity_mwh_s"])

    # ISO enrichment; zone left null (model-zone geography is out of scope here).
    df["iso"] = (
        df["plant_id"].map(iso_map).astype("string")
        if iso_map
        else pd.Series(pd.NA, index=df.index, dtype="string")
    )
    df["zone"] = pd.Series(pd.NA, index=df.index, dtype="string")

    # String columns to the nullable string dtype.
    for col in ("plant_name", "fuel", "prime_mover", "technology"):
        df[col] = df[col].astype("string")

    return df[FLEET_COLUMNS].reset_index(drop=True)


def discover_vintages(eia860_root: Path) -> dict[int, Path]:
    """Map vintage year -> EIA-860 directory (top level + ``vintage_<year>/``)."""
    vintages: dict[int, Path] = {}
    if (eia860_root / GENERATOR_OPERABLE).is_file():
        vintages[TOP_LEVEL_VINTAGE_YEAR] = eia860_root
    for sub in sorted(eia860_root.glob("vintage_*")):
        if not sub.is_dir():
            continue
        try:
            year = int(sub.name.split("_", 1)[1])
        except (IndexError, ValueError):
            continue
        if (sub / GENERATOR_OPERABLE).is_file():
            vintages[year] = sub
    return vintages


def _egrid_for_year(egrid_dir: Path, year: int) -> Path | None:
    """Pick the eGRID workbook for a vintage year (year-matched, else latest)."""
    if not Path(egrid_dir).is_dir():
        return None
    books = sorted(Path(egrid_dir).glob("egrid*.xlsx"))
    if not books:
        return None
    for book in books:
        if str(year) in book.name:
            return book
    return books[-1]  # latest available as a fallback


def curate_vintage(
    year: int,
    eia860_dir: Path,
    *,
    egrid_dir: Path = paths.FLEET_DIR,
    registry_csv: Path = paths.PLANT_REGISTRY_CSV,
    write: bool = True,
) -> tuple[pd.DataFrame, Path | None]:
    """Curate one EIA-860 vintage into a fleet frame (and optionally write it)."""
    gen_df = pd.read_parquet(eia860_dir / GENERATOR_OPERABLE)
    storage_path = eia860_dir / ENERGY_STORAGE_OPERABLE
    storage_df = pd.read_parquet(storage_path) if storage_path.is_file() else None

    iso_map = load_registry_iso_map(registry_csv)
    egrid_path = _egrid_for_year(egrid_dir, year)
    if egrid_path is not None:
        # eGRID's national coverage takes precedence over the ERCOT-only registry.
        iso_map = {**iso_map, **load_egrid_iso_map(egrid_path)}

    df = build_fleet_frame(gen_df, storage_df, iso_map)

    sources = [str(eia860_dir / GENERATOR_OPERABLE)]
    if storage_df is not None:
        sources.append(str(storage_path))
    if egrid_path is not None:
        sources.append(str(egrid_path))
    sources.append(str(registry_csv))

    out: Path | None = None
    if write:
        out = clean_io.write_clean(df, "fleet", year=year, source=", ".join(sources))
        clean_io.validate_clean(out)
        logger.info("wrote %s rows -> %s", len(df), out)
    return df, out


def curate(
    *,
    eia860_root: Path = paths.EIA_860_DIR,
    egrid_dir: Path = paths.FLEET_DIR,
    registry_csv: Path = paths.PLANT_REGISTRY_CSV,
    write: bool = True,
) -> list[Path]:
    """Curate every EIA-860 vintage found under ``eia860_root``."""
    vintages = discover_vintages(eia860_root)
    if not vintages:
        raise FileNotFoundError(f"no {GENERATOR_OPERABLE} found under {eia860_root}")
    written: list[Path] = []
    for year in sorted(vintages):
        _, out = curate_vintage(
            year,
            vintages[year],
            egrid_dir=egrid_dir,
            registry_csv=registry_csv,
            write=write,
        )
        if out is not None:
            written.append(out)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--eia860-root",
        type=Path,
        default=paths.EIA_860_DIR,
        help="EIA-860 root directory (default: the canonical data/raw/eia-860).",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Build the frames but do not write parquet (dry run).",
    )
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    written = curate(eia860_root=args.eia860_root, write=not args.no_write)
    if args.no_write:
        logger.info(
            "dry run: %d vintage(s) built, nothing written",
            len(discover_vintages(args.eia860_root)),
        )
    else:
        logger.info("curated %d fleet vintage(s)", len(written))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
