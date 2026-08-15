"""Build the per-year EIA-860 plant-level CHP flag lookup.

The model fleet's combined-heat-and-power classification (CC_CHP / CT_CHP /
ST_CHP vs the merchant variants) is read off EIA-860's generator-level
``Associated with Combined Heat and Power System`` field. The committed
processed snapshot (``eia860_generator_operable.parquet``) carries only the
latest vintage, so a 3-year backcast classified every year with the most recent
year's CHP flags — an anachronism for plants whose cogen status changed or that
retired before the snapshot vintage.

This script extracts the plant-level CHP flag from EVERY available EIA-860
annual release (``eia860<year>*.zip`` under ``data/raw/eia-860``) and
writes a small per-year lookup so each backcast year is bucketed with its own
vintage's CHP designation:

    data/raw/_processed-legacy/eia860_chp_by_year.parquet  ->  columns (year, plant_id, chp)

A plant is marked ``Y`` when ANY of its operable units is flagged CHP in that
year's release (mirroring :func:`market_sim.data.fleet._chp_by_plant`).

Run:
    python scripts/data/build_eia860_chp_by_year.py
"""

from __future__ import annotations

import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

from market_sim.config.paths import EIA_860_DIR, PROCESSED_DIR
from scripts.data.process_eia860 import _read_sheet

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("build_eia860_chp_by_year")

_CHP_COL = "Associated with Combined Heat and Power System"
_OUT_PATH = PROCESSED_DIR / "eia860_chp_by_year.parquet"


def _chp_from_generator_sheet(gen: pd.DataFrame) -> pd.DataFrame:
    """Return ``(plant_id, chp)`` from one EIA-860 Operable generator sheet.

    A plant is ``Y`` when any of its operable units is flagged CHP.
    """
    code = pd.to_numeric(gen["Plant Code"], errors="coerce")
    gen = gen[code.notna()].copy()
    gen["plant_id"] = code[code.notna()].astype(int)
    is_y = gen[_CHP_COL].astype(str).str.strip().str.upper().str.startswith("Y")
    by_plant = is_y.groupby(gen["plant_id"]).any()
    return pd.DataFrame(
        {
            "plant_id": by_plant.index.astype(int),
            "chp": by_plant.map({True: "Y", False: "N"}).to_numpy(),
        }
    )


def _year_from_zip_name(name: str) -> int | None:
    """Parse the 4-digit release year from an ``eia860<year>...zip`` filename."""
    m = re.search(r"eia860(\d{4})", name)
    return int(m.group(1)) if m else None


def _chp_from_vintage_dirs() -> list[pd.DataFrame]:
    """Return per-year CHP frames from the extracted ``vintage_<year>/`` dirs.

    The release zips are not committed in every clone (they are large and the
    processed parquets supersede them), but ``data/raw/eia-860/vintage_<year>/
    eia860_generator_operable.parquet`` is the SAME Operable generator sheet
    already extracted, carrying the same ``Associated with Combined Heat and
    Power System`` column. Reading it applies the identical per-plant "any
    unit flagged CHP" rule as the zip path, so the two sources are
    interchangeable — verified over the committed 2023/2024 rows (neiso-93,
    2026-08-14). Used to fill any year the zips do not supply.
    """
    frames: list[pd.DataFrame] = []
    for vdir in sorted(EIA_860_DIR.glob("vintage_*")):
        m = re.search(r"vintage_(\d{4})", vdir.name)
        gen_path = vdir / "eia860_generator_operable.parquet"
        if m is None or not gen_path.exists():
            continue
        gen = pd.read_parquet(gen_path)
        if _CHP_COL not in gen.columns:
            logger.warning("%s: no CHP column in operable parquet", vdir.name)
            continue
        frame = _chp_from_generator_sheet(gen)
        frame.insert(0, "year", int(m.group(1)))
        frames.append(frame)
        logger.info(
            "%s -> year %s: %d plants (%d CHP)",
            vdir.name,
            m.group(1),
            len(frame),
            int((frame["chp"] == "Y").sum()),
        )
    return frames


def build() -> Path:
    """Write the per-year EIA-860 CHP lookup parquet; return its path."""
    frames: list[pd.DataFrame] = []
    for zip_path in sorted(EIA_860_DIR.glob("eia860*.zip")):
        year = _year_from_zip_name(zip_path.name)
        if year is None:
            continue
        with zipfile.ZipFile(zip_path) as zf:
            gen_name = next((n for n in zf.namelist() if "Generator_Y" in n), None)
            if gen_name is None:
                logger.warning("no Generator workbook in %s", zip_path.name)
                continue
            gen = _read_sheet(zf.read(gen_name), "Operable")
        if _CHP_COL not in gen.columns:
            logger.warning("%s: no CHP column in Operable sheet", zip_path.name)
            continue
        frame = _chp_from_generator_sheet(gen)
        frame.insert(0, "year", year)
        frames.append(frame)
        logger.info(
            "%s -> year %d: %d plants (%d CHP)",
            zip_path.name,
            year,
            len(frame),
            int((frame["chp"] == "Y").sum()),
        )

    # Fill any year the zips did not supply from the extracted vintage dirs.
    # Zip-derived years win, so a clone that carries both is unaffected.
    have = {int(f["year"].iloc[0]) for f in frames}
    frames.extend(
        f for f in _chp_from_vintage_dirs() if int(f["year"].iloc[0]) not in have
    )

    # A year already committed to the output is never recomputed: this builder
    # rewrites the whole file, and the committed 2025 row comes from an early
    # release whose zip/vintage dir no clone carries. Preserving it keeps the
    # extension additive (rule 22: applying a measured input to more years must
    # not move the years it already covers).
    if _OUT_PATH.exists():
        prior = pd.read_parquet(_OUT_PATH)
        fresh = {int(f["year"].iloc[0]) for f in frames}
        keep = prior[~prior["year"].isin(fresh)]
        if not keep.empty:
            logger.info(
                "preserving committed years %s (no source on disk)",
                sorted(keep["year"].unique()),
            )
            frames.append(keep)

    if not frames:
        raise SystemExit(
            f"no EIA-860 release zips or vintage_<year>/ dirs found under "
            f"{EIA_860_DIR}; expected eia860<year>*.zip or vintage_<year>/"
            "eia860_generator_operable.parquet"
        )

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["year", "plant_id"], kind="stable").reset_index(drop=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out.to_parquet(_OUT_PATH, index=False)
    logger.info(
        "wrote %s (%d rows, years %s)",
        _OUT_PATH,
        len(out),
        sorted(out["year"].unique()),
    )
    return _OUT_PATH


if __name__ == "__main__":
    build()
