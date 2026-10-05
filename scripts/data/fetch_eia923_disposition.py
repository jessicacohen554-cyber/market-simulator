#!/usr/bin/env python3
"""Fetch EIA-923 Schedules 6/7 (non-utility source and disposition) into a compact table.

closeout-CAISO-w6 intake (2026-10-05). EIA Form 923 Schedules 6 and 7, "Annual
Source and Disposition of Electricity for Non-Utility Generators", report per
plant-year the owner's own electricity balance: gross generation and incoming
electricity on the source side; station use, direct (facility) use, retail
sales, sales for resale, tolling agreements and outgoing electricity on the
disposition side. Own generation consumed on site is

    on_site_mwh = (gross - station use) - sales for resale - retail sales
                  - tolling - outgoing

which equals direct use minus incoming, so the two sides agree. It is the
measured behind-the-meter share of a self-generator or cogeneration plant
(``scripts/data/derive_caiso_chp_btm_share.py``).

Source (public domain, EIA): ``https://www.eia.gov/electricity/data/eia923/xls/
f923_<year>.zip`` (falls back to ``.../archive/xls/f923_<year>.zip``), workbook
``EIA923_Schedules_6_7_NU_SourceNDisposition_<year>_Final*.xlsx``, first sheet,
header row 5. Every US plant is kept (the table is ISO-neutral).

Output: ``config.paths.EIA_923_DISPOSITION_PATH`` with columns
``year, plant_id, plant_name, plant_state, sector_code, chp, gross_mwh,
incoming_mwh, station_use_mwh, direct_use_mwh, retail_sales_mwh,
sales_for_resale_mwh, tolling_mwh, outgoing_mwh``.

Usage:
    python3 scripts/data/fetch_eia923_disposition.py
    python3 scripts/data/fetch_eia923_disposition.py --zip-dir <dir with f923_<year>.zip>
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import EIA_923_DISPOSITION_PATH  # noqa: E402

YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
URLS: tuple[str, ...] = (
    "https://www.eia.gov/electricity/data/eia923/xls/f923_{y}.zip",
    "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_{y}.zip",
)
#: Schedules 6/7 header row (0-based) in every 2019-2025 release.
HEADER_ROW: int = 4
COLUMNS: dict[str, str] = {
    "Plant Code": "plant_id",
    "Plant Name": "plant_name",
    "Plant State": "plant_state",
    "Sector Code": "sector_code",
    "CHP Plant": "chp",
    "Gross Generation": "gross_mwh",
    "Incoming Electricity": "incoming_mwh",
    "Station_Use": "station_use_mwh",
    "Direct_Use": "direct_use_mwh",
    "Retail Sales": "retail_sales_mwh",
    "Sales for Resale": "sales_for_resale_mwh",
    "Tolling Agreements": "tolling_mwh",
    "Outgoing Electricity": "outgoing_mwh",
}
NUMERIC: tuple[str, ...] = tuple(v for v in COLUMNS.values() if v.endswith("_mwh"))


def _zip_bytes(year: int, zip_dir: Path | None) -> bytes:
    """Return the release ZIP for ``year`` from ``zip_dir`` or EIA."""
    if zip_dir is not None:
        return (zip_dir / f"f923_{year}.zip").read_bytes()
    last: Exception | None = None
    for url in URLS:
        try:
            req = Request(url.format(y=year), headers={"User-Agent": "market-sim"})
            with urlopen(req, timeout=300) as resp:
                data = resp.read()
            if data[:2] == b"PK":
                return data
        except Exception as exc:  # noqa: BLE001 - try the next mirror
            last = exc
    raise RuntimeError(f"f923_{year}.zip unavailable: {last}")


def read_year(year: int, zip_dir: Path | None = None) -> pd.DataFrame:
    """Return one year's Schedules 6/7 table, normalized to :data:`COLUMNS`."""
    with zipfile.ZipFile(io.BytesIO(_zip_bytes(year, zip_dir))) as zf:
        name = next(n for n in zf.namelist() if "6_7" in n and n.endswith(".xlsx"))
        raw = pd.read_excel(io.BytesIO(zf.read(name)), sheet_name=0, header=HEADER_ROW)
    raw.columns = [" ".join(str(c).split()) for c in raw.columns]
    frame = raw[list(COLUMNS)].rename(columns=COLUMNS)
    frame = frame[pd.to_numeric(frame["plant_id"], errors="coerce").notna()].copy()
    frame["plant_id"] = frame["plant_id"].astype(int)
    for col in NUMERIC:
        frame[col] = pd.to_numeric(frame[col], errors="coerce").fillna(0.0)
    frame.insert(0, "year", int(year))
    return frame


def main() -> None:
    """Fetch every release year and write the compact table."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip-dir", type=Path, default=None)
    args = ap.parse_args()
    out = pd.concat([read_year(y, args.zip_dir) for y in YEARS], ignore_index=True)
    out = out.sort_values(["year", "plant_id"]).reset_index(drop=True)
    EIA_923_DISPOSITION_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(EIA_923_DISPOSITION_PATH, index=False)
    print(f"wrote {EIA_923_DISPOSITION_PATH} ({len(out)} rows)")


if __name__ == "__main__":
    main()
