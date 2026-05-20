"""Process EIA-923 Schedule 5 monthly fuel receipts into a per-plant cost table.

The official EIA-923 release ships one Excel workbook per year. Sheet
"Page 5 Fuel Receipts and Costs" contains one row per fuel receipt, with
the delivered ``FUEL_COST`` in cents/MMBtu (0.1-cent precision). This
script aggregates receipts to one row per ``(year, month, plant_id,
fuel_group)`` weighted by ``QUANTITY``, converts cents/MMBtu to dollars,
filters to the ERCOT balancing authority and writes the result to
``inputs/processed/eia923_monthly_fuel_costs.parquet`` for the dispatch
fuel-price resolver to consume.

EIA suppresses delivered cost for many records (``FUEL_COST = '.'``);
those receipts are dropped before the quantity-weighted aggregation, so
a plant with no reported cost in a month is simply absent from the
output and the dispatch resolver's fallback (AEO Henry Hub + basis,
COAL_PRICE_*_BY_YEAR) takes over.

Usage:
    python scripts/process_f923_fuel_costs.py [--out-dir DIR] [--ba ERCO]

Defaults to processing every ``f923_*.zip`` in
``inputs/raw-data/`` and writing the ERCO-only parquet.
"""

from __future__ import annotations

import argparse
import io
import logging
import re
import zipfile
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("process_f923")

# Page 5 (Fuel Receipts and Costs) header sits a few rows down past the
# EIA boilerplate. The exact row varies by release vintage (row 4 for
# final releases, row 3 for the early-cycle 2025 file), so we scan the
# first eight rows for the YEAR header rather than hard-coding it.
_PAGE_5_HEADER_SCAN_ROWS: int = 8
_PAGE_5_SHEET: str = "Page 5 Fuel Receipts and Costs"

# Columns we keep from the raw receipts sheet, normalised to short names.
# A column may appear under several spellings across release vintages
# (e.g. ``Balancing\nAuthority Code`` in the final releases, ``BA_CODE`` in
# the preliminary 2025 file), so multiple source names can map to one
# canonical name.
_RENAME: dict[str, str] = {
    "YEAR": "year",
    "MONTH": "month",
    "Plant Id": "plant_id",
    "Plant State": "state",
    "ENERGY_SOURCE": "energy_source",
    "FUEL_GROUP": "fuel_group",
    "QUANTITY": "quantity",
    "FUEL_COST": "fuel_cost_cents_per_mmbtu",
    "Balancing\nAuthority Code": "ba_code",
    "BA_CODE": "ba_code",
}

# EIA-923 reports FUEL_COST in cents per MMBtu with one-decimal precision,
# i.e. the column value is the dollar price scaled by 100. Dividing by
# this converts the column to delivered $/MMBtu.
_CENTS_PER_DOLLAR: float = 100.0

# Fuel-group strings we keep. Everything else (waste fuels, biomass) is
# outside the gas/coal/oil cost trajectories the dispatch model uses.
_FUEL_GROUP_KEEP: frozenset[str] = frozenset(
    {"Natural Gas", "Coal", "Petroleum", "Petroleum Coke"}
)


def _find_zips(raw_dir: Path) -> list[Path]:
    """Return every ``f923_*.zip`` under ``raw_dir`` in year order."""
    zips = sorted(raw_dir.glob("f923_*.zip"))
    if not zips:
        raise FileNotFoundError(f"No f923_*.zip found in {raw_dir}")
    return zips


def _extract_schedules_xlsx(zip_path: Path) -> bytes:
    """Return the bytes of the Schedules 2-3-4-5 workbook in ``zip_path``."""
    with zipfile.ZipFile(zip_path) as zf:
        members = [
            name for name in zf.namelist()
            if re.search(r"Schedules_2_3_4_5", name)
            and name.lower().endswith(".xlsx")
        ]
        if not members:
            raise FileNotFoundError(
                f"No Schedules 2-3-4-5 workbook in {zip_path.name}"
            )
        return zf.read(members[0])


def _find_header_row(xlsx_bytes: bytes) -> int:
    """Return the zero-based header row for Page 5 in the given workbook."""
    probe = pd.read_excel(
        io.BytesIO(xlsx_bytes),
        sheet_name=_PAGE_5_SHEET,
        header=None,
        nrows=_PAGE_5_HEADER_SCAN_ROWS,
    )
    for idx, value in enumerate(probe.iloc[:, 0]):
        if isinstance(value, str) and value.strip().upper() == "YEAR":
            return idx
    raise ValueError(
        "Could not locate YEAR header row on Page 5 of the workbook"
    )


def _load_receipts(zip_path: Path) -> pd.DataFrame:
    """Read Page 5 from ``zip_path``'s schedules workbook, renaming columns."""
    logger.info("reading %s", zip_path.name)
    xlsx_bytes = _extract_schedules_xlsx(zip_path)
    header = _find_header_row(xlsx_bytes)
    raw = pd.read_excel(
        io.BytesIO(xlsx_bytes),
        sheet_name=_PAGE_5_SHEET,
        header=header,
    )
    keep = [c for c in _RENAME if c in raw.columns]
    return raw[keep].rename(columns=_RENAME)


def aggregate_monthly_fuel_costs(
    zip_paths: list[Path], ba_code: str | None = None
) -> pd.DataFrame:
    """Return a quantity-weighted monthly fuel-cost table from EIA-923 zips.

    Receipts whose ``FUEL_COST`` is the EIA-suppressed sentinel ``.`` are
    dropped before aggregation; a plant-month with no reported cost is
    therefore absent from the result (the dispatch resolver's per-fuel
    fallback covers it).

    Args:
        zip_paths: One ``f923_*.zip`` per calendar year.
        ba_code: When given, keep only receipts at plants in this
            balancing authority (e.g. ``"ERCO"``); ``None`` keeps every BA.

    Returns:
        ``(year, month, plant_id, fuel_group, price_per_mmbtu, quantity)``
        with one row per plant-month-fuel.
    """
    frames = [_load_receipts(path) for path in zip_paths]
    df = pd.concat(frames, ignore_index=True)

    df["fuel_cost_cents_per_mmbtu"] = pd.to_numeric(
        df["fuel_cost_cents_per_mmbtu"], errors="coerce"
    )
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df = df.dropna(subset=["fuel_cost_cents_per_mmbtu", "quantity"])
    df = df[df["quantity"] > 0]
    df = df[df["fuel_group"].isin(_FUEL_GROUP_KEEP)]

    if ba_code is not None:
        df = df[df["ba_code"] == ba_code]

    df["weighted"] = df["fuel_cost_cents_per_mmbtu"] * df["quantity"]

    key = ["year", "month", "plant_id", "fuel_group"]
    grouped = (
        df.groupby(key, sort=True)
        .agg(weighted=("weighted", "sum"), quantity=("quantity", "sum"))
        .reset_index()
    )
    grouped["price_per_mmbtu"] = (
        grouped["weighted"] / grouped["quantity"] / _CENTS_PER_DOLLAR
    )
    grouped["plant_id"] = grouped["plant_id"].astype(int)
    grouped["year"] = grouped["year"].astype(int)
    grouped["month"] = grouped["month"].astype(int)
    return grouped[[
        "year", "month", "plant_id", "fuel_group",
        "price_per_mmbtu", "quantity",
    ]]


def main() -> None:
    """Process every ``f923_*.zip`` under inputs/raw-data and write parquet."""
    parser = argparse.ArgumentParser(
        description="Process EIA-923 fuel receipts into a monthly cost table."
    )
    parser.add_argument(
        "--raw-dir",
        default="inputs/raw-data",
        help="Directory holding the f923_*.zip releases.",
    )
    parser.add_argument(
        "--out-dir",
        default="inputs/processed",
        help="Directory for the output parquet.",
    )
    parser.add_argument(
        "--ba", default="ERCO",
        help="Balancing-authority filter (default ERCO); blank to keep all.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    zips = _find_zips(raw_dir)
    ba = args.ba or None
    table = aggregate_monthly_fuel_costs(zips, ba_code=ba)

    out_path = out_dir / "eia923_monthly_fuel_costs.parquet"
    table.to_parquet(out_path, index=False)
    logger.info(
        "wrote %s (%d plant-months across %d years, BA filter=%s)",
        out_path, len(table), table["year"].nunique(), ba or "ALL",
    )


if __name__ == "__main__":
    main()
