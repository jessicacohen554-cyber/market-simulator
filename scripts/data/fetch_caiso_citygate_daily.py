#!/usr/bin/env python3
"""Scrape the **daily** California Composite Average citygate natural-gas spot
price from the EIA Natural Gas Weekly Update archive, for the CAISO daily
hub-basis overlay.

The model's CAISO gas path has the measured *monthly* SoCal/PG&E citygate
basis (``apply_hub_basis_overlay`` + ``data/raw/gas_basis_by_iso_month.csv``,
EIA N3050CA3 citygate proxy), but a flat monthly mean smears within-month
cold-snap spikes across the mild days — Jan-2023 held a measured $28/MMBtu
citygate print early in the month while the monthly average (~$28 basis over
Henry Hub) is applied flat to all 744 hours, over-pricing the mild back half
of the month. The daily series this script builds lets
:func:`market_sim.data.fuel.iso_hub_daily_gas_prices` resolve the real
day-to-day swing, mean-preserving at the monthly hub level, so the annual gas
burn and fuel mix are unchanged while the cold-day blowout (and its decay)
reaches the merit order on its true calendar days.

Source: the EIA Natural Gas Weekly Update **archive** pages
``https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/YYYY/MM_DD/`` (one per
publication Thursday) — the same pages ``fetch_transco_daily_spot.py`` reads
for NYISO. Each page carries a server-rendered compact "Spot Prices
($/MMBtu)" table whose **"Cal. Comp. Avg"** row is EIA's California Composite
Average (PG&E Citygate / SoCal Citygate / SoCal Border blend, NGI Daily GPI
compiled by Bloomberg) — the same free daily print the existing Transco/
Algonquin daily scripts already draw their hub rows from. The five daily
columns (Thu/Fri/Mon/Tue/Wed) of each page are the trading days of the week
ending the Wednesday before publication.

Output: ``data/raw/gas-prices/caiso_citygate_daily.csv``
  columns ``date, ca_composite_usd_mmbtu, henry_hub_usd_mmbtu`` (same minimal
  convention as ``transco_z6_ny_daily.csv``).

Usage:
    uv run python scripts/data/fetch_caiso_citygate_daily.py
    uv run python scripts/data/fetch_caiso_citygate_daily.py --start-year 2023 --end-year 2025
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent.parent
OUT_PATH = REPO / "data" / "raw" / "gas-prices" / "caiso_citygate_daily.csv"

ARCHIVE_INDEX = "https://www.eia.gov/naturalgas/weekly/includes/archive.php"
PAGE_TMPL = "https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/{y}/{m:02d}_{d:02d}/"

_MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def _fetch(url: str, timeout: int = 60) -> str:
    """GET a URL with a browser-ish UA, returning decoded text. Raises on error."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-sim data fetch)"})
    with urlopen(req, timeout=timeout) as fh:
        return fh.read().decode("utf-8", errors="replace")


def archive_pages(start_year: int, end_year: int) -> list[tuple[int, int, int]]:
    """Return sorted ``(year, month, day)`` publication dates of archive pages.

    A page published in month M reports the prior week, so its daily quotes can
    fall in M or the prior month/year. To capture every day in
    ``[start_year, end_year]`` we keep pages published from ``start_year`` through
    the first weeks of ``end_year + 1`` (a late-December week is published the
    following January).
    """
    html = _fetch(ARCHIVE_INDEX)
    seen = sorted(set(re.findall(r"archivenew_ngwu/(\d{4})/(\d{2})_(\d{2})", html)))
    out = []
    for y, m, d in seen:
        yi = int(y)
        if start_year <= yi <= end_year + 1:
            out.append((yi, int(m), int(d)))
    return out


def _resolve_year(month: int, page_year: int, page_month: int) -> int:
    """Year of a column whose month is ``month`` on a page published in
    ``page_year``/``page_month`` (handle the Dec/Jan boundary the week straddles)."""
    if month == 12 and page_month == 1:
        return page_year - 1
    if month == 1 and page_month == 12:
        return page_year + 1
    return page_year


def parse_spot_table(html: str, page_year: int, page_month: int) -> list[dict]:
    """Return ``[{date, ca_comp, henry_hub}]`` for one weekly page, or ``[]``.

    Locates the active (non-commented) "Spot Prices ($/MMBtu)" table inside the
    ``tabs-prices-2`` block, reads the five daily column dates from the header,
    and the Henry Hub + "Cal. Comp. Avg" rows. Robust to the page's
    whitespace/``<br />`` noise inside each cell and to the header's date
    separator varying between a hyphen (``6-Jan``) and a space/line-break
    (``5 Jan``) on the first column of some pages.
    """
    idx = html.find('id="tabs-prices-2"')
    if idx < 0:
        return []
    # Window is generous: some weeks leave a stale commented-out "Table option 1"
    # template (with old dates) ahead of the active table, pushing it down-page.
    seg = html[idx : idx + 24000]
    seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)  # drop the commented template(s)
    m = re.search(r"<table.*?</table>", seg, flags=re.S)
    if not m:
        return []
    table = m.group(0)

    # Column dates from the header: "Thu, 6-Jan" or "Thu, 5 Jan" (both seen).
    head = table[: table.find("</thead>") + 8] if "</thead>" in table else table
    date_tokens = re.findall(r"(\d{1,2})[-\s]+([A-Z][a-z]{2})", head)
    dates: list[str] = []
    for day_s, mon_s in date_tokens:
        mon = _MONTHS.get(mon_s)
        if mon is None:
            continue
        yr = _resolve_year(mon, page_year, page_month)
        dates.append(f"{yr:04d}-{mon:02d}-{int(day_s):02d}")
    if not dates:
        return []

    def _row_values(label_pat: str) -> list[float | None]:
        # Match the <tr> whose first <td> bolds a label matching label_pat.
        pat = re.compile(
            r"<tr>\s*<td[^>]*>\s*<strong>\s*" + label_pat + r".{0,3}</strong>.*?</tr>",
            flags=re.S,
        )
        rm = pat.search(table)
        if not rm:
            return [None] * len(dates)
        # Value cells appear in two layouts across weeks: <td><div align=...>V</div>
        # and <td width=.. align="right">V</td>; tolerate attributes and inner tags.
        cells = re.findall(r"<td[^>]*>(.*?)</td>", rm.group(0), flags=re.S)[1:]
        vals: list[float | None] = []
        for c in cells:
            txt = re.sub(r"<[^>]+>", " ", c)
            if "N/A" in txt or "NA" in txt.replace("N/A", ""):
                vals.append(None)
                continue
            nums = re.findall(r"-?\d+\.?\d*", txt)
            vals.append(float(nums[0]) if nums else None)
        return vals

    ca = _row_values(r"Cal\.\s*Comp\.\s*Avg")
    hh = _row_values(r"Henry\s*Hub")
    rows = []
    for i, date in enumerate(dates):
        c = ca[i] if i < len(ca) else None
        h = hh[i] if i < len(hh) else None
        if c is None:
            continue
        rows.append({"date": date, "ca_comp": c, "henry_hub": h})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start-year", type=int, default=2023)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    try:
        pages = archive_pages(args.start_year, args.end_year)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: archive index fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"archive: {len(pages)} weekly pages {args.start_year}..{args.end_year + 1}")

    by_date: dict[str, dict] = {}
    fetched = failed = 0
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL — {exc}", file=sys.stderr)
            failed += 1
            continue
        rows = parse_spot_table(html, y, m)
        if not rows:
            print(f"  {y}-{m:02d}-{d:02d}: no spot table parsed", file=sys.stderr)
        for r in rows:
            yr = int(r["date"][:4])
            if args.start_year <= yr <= args.end_year:
                by_date[r["date"]] = r  # later page wins on duplicate (revisions)
        fetched += 1
        time.sleep(args.sleep)

    out_rows = [by_date[k] for k in sorted(by_date)]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "ca_composite_usd_mmbtu", "henry_hub_usd_mmbtu"])
        for r in out_rows:
            hh = "" if r["henry_hub"] is None else f"{r['henry_hub']:.4f}"
            w.writerow([r["date"], f"{r['ca_comp']:.4f}", hh])
    print(
        f"fetched {fetched} pages ({failed} failed); "
        f"wrote {len(out_rows)} daily rows -> {args.out}"
    )


if __name__ == "__main__":
    main()
