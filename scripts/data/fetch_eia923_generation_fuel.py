#!/usr/bin/env python3
"""Fetch EIA-923 Page 1 "Generation and Fuel Data" into a compact annual table.

R-CAISO-3 intake (2026-09-25). EIA Form 923 Schedules 2-5, Page 1, reports per
plant x reported prime mover x reported fuel the owner's **total fuel
consumption** and **electric fuel consumption** (MMBtu, HHV) and **net
generation** (MWh). It is the plant's own fuel filing and is independent of the
EPA CAMPD CEMS heat input, which is why it is the measured comparator for a
plant whose CEMS record the CC heat-rate derive refuses
(``scripts/data/derive_campd_cc_heat_rates.py``: EIA-923 fuel / EIA-923 net,
numerator and denominator from one filing and one boundary).

Source (public domain, EIA): ``https://www.eia.gov/electricity/data/eia923/xls/
f923_<year>.zip`` (falls back to ``.../archive/xls/f923_<year>.zip``), workbook
``EIA923_Schedules_2_3_4_5_M_12_<year>_Final*.xlsx``, first sheet ("Page 1
Generation and Fuel Data"), header row 6. Every US plant is kept (the table is
ISO-neutral); only the annual totals are kept.

Output: ``config.paths.EIA_923_GENERATION_FUEL_PATH`` with columns
``year, plant_id, plant_state, prime_mover, fuel_type, total_fuel_mmbtu,
elec_fuel_mmbtu, net_generation_mwh``.

Usage:
    python3 scripts/data/fetch_eia923_generation_fuel.py
    python3 scripts/data/fetch_eia923_generation_fuel.py --zip-dir <dir with f923_<year>.zip>
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

from market_sim.config.paths import EIA_923_GENERATION_FUEL_PATH  # noqa: E402

YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
URLS: tuple[str, ...] = (
    "https://www.eia.gov/electricity/data/eia923/xls/f923_{y}.zip",
    "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_{y}.zip",
)
#: Page 1 header row (0-based) in every 2019-2025 release.
HEADER_ROW: int = 5
COLUMNS: dict[str, str] = {
    "Plant Id": "plant_id",
    "Plant State": "plant_state",
    "Reported Prime Mover": "prime_mover",
    "Reported Fuel Type Code": "fuel_type",
    "Total Fuel Consumption MMBtu": "total_fuel_mmbtu",
    "Elec Fuel Consumption MMBtu": "elec_fuel_mmbtu",
    "Net Generation (Megawatthours)": "net_generation_mwh",
}


def _zip_bytes(year: int, zip_dir: Path | None) -> bytes:
    """Return the release ZIP for ``year`` from ``zip_dir`` or EIA."""
    if zip_dir is not None:
        local = zip_dir / f"f923_{year}.zip"
        if local.exists():
            return local.read_bytes()
    for url in URLS:
        req = Request(
            url.format(y=year), headers={"User-Agent": "market-sim data fetch"}
        )
        with urlopen(req, timeout=600) as fh:
            data = fh.read()
        if data[:2] == b"PK":
            return data
    raise SystemExit(f"EIA-923 {year}: no ZIP reachable")


def page1_frame(year: int, raw: bytes) -> pd.DataFrame:
    """Parse one release's Page 1 into the compact annual table."""
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = next(
            n for n in zf.namelist() if "Schedules_2_3_4_5" in n and n.endswith(".xlsx")
        )
        frame = pd.read_excel(zf.open(name), sheet_name=0, header=HEADER_ROW)
    frame.columns = [" ".join(str(c).split()) for c in frame.columns]
    missing = [c for c in COLUMNS if c not in frame.columns]
    if missing:
        raise SystemExit(f"EIA-923 {year}: Page 1 lacks {missing}")
    out = frame[list(COLUMNS)].rename(columns=COLUMNS)
    out = out[pd.to_numeric(out["plant_id"], errors="coerce").notna()].copy()
    out["plant_id"] = out["plant_id"].astype(int)
    for col in ("total_fuel_mmbtu", "elec_fuel_mmbtu", "net_generation_mwh"):
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)
    out.insert(0, "year", year)
    return out


def main(argv: list[str] | None = None) -> int:
    """Fetch every year and write the committed CSV."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip-dir", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=EIA_923_GENERATION_FUEL_PATH)
    args = parser.parse_args(argv)
    frames = [page1_frame(y, _zip_bytes(y, args.zip_dir)) for y in YEARS]
    table = pd.concat(frames, ignore_index=True).sort_values(
        ["year", "plant_id", "prime_mover", "fuel_type"], kind="stable"
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)
    print(f"wrote {args.out} ({len(table):,} rows, years {YEARS[0]}-{YEARS[-1]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
