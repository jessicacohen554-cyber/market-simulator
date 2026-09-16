#!/usr/bin/env python3
"""Fetch EIA-923 plant-level monthly coal receipts into ``data/raw/coal-receipts``.

The DELIVERY half of the coal fuel-inventory state, and the sibling of
``fetch_eia923_coal_stocks.py``: same free, keyless annual bulk ZIP, different
worksheet (``Page 5 Fuel Receipts and Costs`` instead of ``Page 2 Coal Stocks
Data``). The download / extract plumbing is imported from that script rather
than duplicated, so both intakes read one workbook through one extractor.

**Why this intake exists at all.**
``data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet`` already carries
a ``quantity`` column from this same form, and it is an INCOMPLETE extract:
measured 2026-09-14 it matches only 50 of the 67 MISO model coal plants and
understates MISO coal receipts by 17-21 % (2020: 99.10 Mt against the true
120.42 Mt; nationally in 2018, 436 Mt against ~637 Mt actually received). A
coal-delivery budget built on it flips two MISO years from inert to marginal,
which would have produced a false G-FOOTPRINT failure. It is superseded for
coal receipts by this datatype.

**Scope.** Page 5 is an all-fuel sheet; this datatype is coal receipts, so the
extract keeps only ``FUEL_GROUP == "Coal"`` rows — every column of them,
verbatim. The filter is the datatype's own definition rather than a
transformation of what it covers, and it is applied here at fetch so the
committed raw corpus stays ~1.6 MB/yr rather than ~7 MB/yr.

**Rule 13 ``[R-MEASURED]``.** These are measured deliveries-to-tank OUTCOMES.
The NEISO oil precedent rejected exactly this quantity as a budget input for
the year it is reported in; see the schema header and
``src/market_sim/data/coal_receipts.py``. The admissible read is a rate over
years ``<= Y-1``.

Source (public domain, US Government work):
    https://www.eia.gov/electricity/data/eia923/          (landing page)
    .../xls/f923_<YEAR>.zip                               (recent years)
    .../archive/xls/f923_<YEAR>.zip                       (older years)

Usage:
    python scripts/data/fetch_eia923_coal_receipts.py --years 2018 2019 2020
    python scripts/data/fetch_eia923_coal_receipts.py            # default span
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from market_sim.config import paths  # noqa: E402
from scripts.data.fetch_eia923_coal_stocks import (  # noqa: E402
    DEFAULT_YEARS,
    _download,
    _extract_sheet,
)

#: The worksheet carrying plant-level monthly fuel receipts (all fuels).
SHEET_NAME = "Page 5 Fuel Receipts and Costs"

#: Page 5 prepends four banner rows (agency, title, sources, blank) above the
#: real header — one fewer than Page 2 Coal Stocks Data, which also carries a
#: merged "Total Month Ending Stocks" super-header.
_BANNER_ROWS = 5

#: EIA's own fuel-group label for coal on this sheet. The extract keeps these
#: rows and drops every other fuel: this datatype is coal receipts, and the
#: all-fuel sheet is ~4x the size.
_COAL_FUEL_GROUP = "Coal"


def raw_dir() -> Path:
    """Return the ``coal-receipts`` raw directory, created if absent."""
    d = paths.RAW_DATA_DIR / "coal-receipts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _coal_rows(rows: list[list[object]]) -> tuple[list[str], list[list[object]]]:
    """Return ``(header, coal_rows)`` from the raw Page 5 rows.

    Raises when the fuel-group column is absent, rather than silently writing
    an all-fuel file that would later be summed as if it were coal.
    """
    header = [" ".join(str(c).split()) if c is not None else "" for c in rows[0]]
    if "FUEL_GROUP" not in header:
        raise RuntimeError(f"{SHEET_NAME!r} has no FUEL_GROUP column: {header[:12]}")
    gi = header.index("FUEL_GROUP")
    keep = [
        r
        for r in rows[1:]
        if r[gi] is not None and str(r[gi]).strip() == _COAL_FUEL_GROUP
    ]
    return header, keep


def fetch_year(year: int, out_dir: Path | None = None) -> tuple[Path, str, str]:
    """Fetch one year; return ``(csv_path, source_url, workbook_sha256)``."""
    out_dir = out_dir or raw_dir()
    blob, url = _download(year)
    rows, workbook, sha = _extract_sheet(blob, SHEET_NAME, _BANNER_ROWS)
    header, coal = _coal_rows(rows)
    path = out_dir / f"coal_receipts_{year}.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        for r in coal:
            w.writerow(["" if c is None else c for c in r])
    print(
        f"  {year}: {len(coal):>6} coal rows of {len(rows) - 1:>6} "
        f"-> {path.name}  ({workbook})"
    )
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
