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

    if not frames:
        raise SystemExit(
            f"no EIA-860 release zips found under {EIA_860_DIR}; "
            "expected eia860<year>*.zip"
        )

    out = pd.concat(frames, ignore_index=True)
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
