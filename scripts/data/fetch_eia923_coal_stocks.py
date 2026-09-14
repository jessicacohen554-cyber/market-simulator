#!/usr/bin/env python3
"""Fetch EIA-923 plant-level monthly ending coal stocks into ``data/raw/coal-stocks``.

Downloads the free, **keyless** EIA-923 annual bulk ZIP for each requested year,
extracts the ``Page 2 Coal Stocks Data`` worksheet from the
``EIA923_Schedules_2_3_4_5_M_*`` workbook, and writes it out VERBATIM (every
column, no transformation beyond dropping EIA's four banner rows) as one CSV per
year. The bulky source workbooks are NOT retained — the CSV plus this script's
recorded source URL and the workbook sha256 are the reproduction record, which
is the corpus discipline ``docs/bloat-removal-plan-2026-08.md`` §4 sets for
large upstream payloads.

**Why this route matters.** ``docs/FINDING-miso256-2022-passthrough-inversion-
2026-09-13.md`` §5 recorded MISO-footprint coal stocks as "not on disk", with an
``EIA_API_KEY`` named as the unblocker and the EIA API v2 blocked from the
session. The API is indeed key-gated (HTTP 403 without one), but the same
quantity ships in this bulk workbook, which needs no credential at all — the
same "exhaustive audit of an incomplete search space" that §0 of that document
records for the MISO LMP families.

Source (public domain, US Government work):
    https://www.eia.gov/electricity/data/eia923/          (landing page)
    .../xls/f923_<YEAR>.zip                               (recent years)
    .../archive/xls/f923_<YEAR>.zip                       (older years)

Usage:
    python scripts/data/fetch_eia923_coal_stocks.py --years 2018 2019 2020
    python scripts/data/fetch_eia923_coal_stocks.py            # default span
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402

#: The worksheet carrying plant-level monthly ending coal stocks.
SHEET_NAME = "Page 2 Coal Stocks Data"

#: EIA prepends five banner rows (agency, title, sources, blank, and a merged
#: "Total Month Ending Stocks" super-header) above the real header row.
_BANNER_ROWS = 6

#: Both URL shapes EIA serves the annual bulk ZIP under; recent years live at
#: the first, older years are moved to the archive path.
_URL_TEMPLATES = (
    "https://www.eia.gov/electricity/data/eia923/xls/f923_{year}.zip",
    "https://www.eia.gov/electricity/data/eia923/archive/xls/f923_{year}.zip",
)

#: Default span: the earliest year the current fleet/receipts artifacts cover
#: (eia923_monthly_fuel_costs.parquet starts 2018) through the latest final.
DEFAULT_YEARS: tuple[int, ...] = (2018, 2019, 2020, 2021, 2022, 2023, 2024)


def raw_dir() -> Path:
    """Return the ``coal-stocks`` raw directory, created if absent."""
    d = paths.RAW_DATA_DIR / "coal-stocks"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _download(year: int) -> tuple[bytes, str]:
    """Return ``(zip_bytes, source_url)`` for ``year``, trying both URL shapes."""
    last: Exception | None = None
    for tmpl in _URL_TEMPLATES:
        url = tmpl.format(year=year)
        try:
            with urllib.request.urlopen(url, timeout=300) as resp:  # noqa: S310
                blob = resp.read()
            zipfile.ZipFile(io.BytesIO(blob)).testzip()
            return blob, url
        except Exception as exc:  # pragma: no cover - network shape
            last = exc
    raise RuntimeError(f"no reachable EIA-923 bulk ZIP for {year}: {last}")


def _extract_sheet(blob: bytes) -> tuple[list[list[object]], str, str]:
    """Return ``(rows, workbook_name, workbook_sha256)`` for the stocks sheet.

    ``rows[0]`` is the header row; EIA's banner rows are dropped. Values come
    back exactly as the workbook stores them — this is an extraction, never a
    transformation.
    """
    import openpyxl

    zf = zipfile.ZipFile(io.BytesIO(blob))
    names = [n for n in zf.namelist() if "Schedules_2_3_4_5" in n]
    if not names:
        raise RuntimeError("bulk ZIP carries no Schedules_2_3_4_5 workbook")
    name = names[0]
    payload = zf.read(name)
    sha = hashlib.sha256(payload).hexdigest()
    with tempfile.NamedTemporaryFile(suffix=".xlsx") as tmp:
        tmp.write(payload)
        tmp.flush()
        wb = openpyxl.load_workbook(tmp.name, read_only=True, data_only=True)
        if SHEET_NAME not in wb.sheetnames:
            wb.close()
            raise RuntimeError(f"workbook has no {SHEET_NAME!r} sheet")
        ws = wb[SHEET_NAME]
        rows = [list(r) for r in ws.iter_rows(min_row=_BANNER_ROWS, values_only=True)]
        wb.close()
    return rows, name, sha


def fetch_year(year: int, out_dir: Path | None = None) -> tuple[Path, str, str]:
    """Fetch one year; return ``(csv_path, source_url, workbook_sha256)``."""
    out_dir = out_dir or raw_dir()
    blob, url = _download(year)
    rows, workbook, sha = _extract_sheet(blob)
    header = [" ".join(str(c).split()) if c is not None else "" for c in rows[0]]
    path = out_dir / f"coal_stocks_{year}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in rows[1:]:
            if all(c is None or str(c).strip() == "" for c in r):
                continue
            w.writerow(["" if c is None else c for c in r])
    print(f"  {year}: {len(rows) - 1:>5} rows -> {path.name}  ({workbook})")
    return path, url, sha


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", type=int, nargs="*", default=list(DEFAULT_YEARS))
    args = ap.parse_args()
    out = raw_dir()
    sums: list[str] = []
    for year in args.years:
        try:
            _, url, sha = fetch_year(year, out)
            sums.append(f"{sha}  f923_{year}.zip::Schedules_2_3_4_5  {url}")
        except Exception as exc:
            print(f"  {year}: SKIPPED — {exc}")
    if sums:
        (out / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
