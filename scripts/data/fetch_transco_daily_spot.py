#!/usr/bin/env python3
"""Scrape the **daily** Transco Z6 NY natural-gas spot price from the EIA Natural
Gas Weekly Update archive, for the NYISO daily hub-basis overlay.

The model's NYISO gas path can price the marginal gas unit at the measured
trading-hub *monthly* spot (``apply_hub_basis_overlay`` +
``data/raw/gas-prices/transco_z6_iroquois_monthly.csv``), but a monthly mean
smears within-month cold spikes across the mild days (Jan-2025 Transco $12.7
applied flat to all 744 hours over-prices the ~25 mild days). The daily series
this script builds lets ``iso_hub_daily_gas_prices`` resolve the real day-to-day
swing, mean-preserving at the monthly hub level, so the annual gas burn and fuel
mix are unchanged while the cold-day blowout reaches the merit order.

Source: the EIA Natural Gas Weekly Update **archive** pages
``https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/YYYY/MM_DD/`` (one per
publication Thursday). Each page carries a server-rendered compact "Spot Prices
($/MMBtu)" table whose **"New York"** row is the Transcontinental Pipeline Zone 6
NY trading point (NGI Daily GPI, compiled by Bloomberg). The five daily columns
(Thu/Fri/Mon/Tue/Wed) of each page are the trading days of the week ending the
Wednesday before publication. The same source the existing *monthly*
``transco_z6_iroquois_monthly.csv`` was built from — this just keeps the daily
resolution instead of folding to a monthly mean.

EIA's free table carries Henry Hub, "New York" (Transco Z6 NY), Chicago and a
California composite — but **not** Iroquois Z2 (NGI hub pages are 405-blocked).
The Henry Hub daily column is captured too as a cross-check against the existing
``henry_hub_daily.csv``; the Iroquois-priced NYISO zones inherit the Transco
daily *shape* in the overlay (a real daily Iroquois series is the open data ask).

Output: ``data/raw/gas-prices/transco_z6_ny_daily.csv``
  columns ``date, transco_z6_ny_usd_mmbtu, henry_hub_usd_mmbtu`` (provenance is
  this script + the loader docstring, matching the minimal ``henry_hub_daily.csv``
  convention — no per-row source string).

Usage:
    uv run python scripts/data/fetch_transco_daily_spot.py
    uv run python scripts/data/fetch_transco_daily_spot.py --start-year 2023 --end-year 2025
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
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import GAS_PRICES_DIR  # noqa: E402

OUT_PATH = GAS_PRICES_DIR / "transco_z6_ny_daily.csv"

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
    """Return ``[{date, transco, henry_hub}]`` for EVERY live weekly table on a page.

    Reads the "Spot Prices ($/MMBtu)" tables inside the ``tabs-prices-2`` block,
    taking the five daily column dates from each header and the Henry Hub + New
    York rows. Robust to the page's whitespace/``<br />`` noise inside each cell.

    **A page can carry MORE THAN ONE live table, and the extra ones are the only
    published record of the weeks EIA skips.** EIA publishes no Natural Gas
    Weekly Update during the Christmas/New Year weeks (and around other federal
    holidays); when it resumes it carries the missed weeks as ADDITIONAL live
    tables in the catch-up page. Measured on the 2023-01-12 page: three live
    tables — Jan 5-11 (the current week), Dec 29-Jan 4, and **Dec 22-28, which
    is the only published source for Winter Storm Elliott** (New York $32.12 on
    Dec 22 and $35.61 on Dec 23). The same three-table shape repeats in the
    2024-01-11 and 2025-01-10 catch-up pages.

    This function previously took ``re.search`` — the FIRST table only — so every
    catch-up week was silently dropped, leaving a 14-15 day hole across every
    year-end in ``transco_z6_ny_daily.csv`` and a flat interpolated fill across
    the largest gas event in Northeast history
    (``docs/FINDING-nyiso234-tail-gas-is-unobserved-2026-09-14.md``). Rule 23
    ``[R-FROZEN-DERIVE]``: this re-derivation is cited to that source-coverage
    defect, never to a residual.

    **Alignment is GUARDED, not assumed.** A header may separate day and month
    with either a hyphen or a space (both ``"Thu, 04-Jan"`` and ``"Thu, 5 Jan"``
    occur, sometimes in the same table), and the old hyphen-only pattern silently
    dropped the spaced date — leaving four dates against five values, so every
    value in that week landed on the FOLLOWING trading day. Measured on the
    2023-01-12 page: the committed series carried Jan 6 = 3.17 where EIA
    published 3.50, and so on for Jan 9/10/11, with Jan 5 missing entirely. Both
    separators are now accepted and a table whose dates and values do not line up
    exactly is SKIPPED with a warning rather than emitted misaligned — a silent
    one-day shift in the delivered gas price is worse than a gap, because a gap
    is visible.
    """
    idx = html.find('id="tabs-prices-2"')
    if idx < 0:
        return []
    # Window is generous: some weeks leave a stale commented-out "Table option 1"
    # template (with old dates) ahead of the active table, pushing it down-page.
    seg = html[idx : idx + 24000]
    seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)  # drop the commented template(s)
    rows: list[dict] = []
    for m in re.finditer(r"<table.*?</table>", seg, flags=re.S):
        rows.extend(_parse_one_table(m.group(0), page_year, page_month))
    return rows


def _parse_one_table(table: str, page_year: int, page_month: int) -> list[dict]:
    """Return ``[{date, transco, henry_hub}]`` for ONE weekly spot table.

    Split out of :func:`parse_spot_table` so a page's several live tables (see
    that docstring) each parse independently and one malformed table cannot
    discard the others. Returns ``[]`` for a table that is not a spot table, or
    whose header dates and value cells do not align.
    """
    # Column dates from the header: "Thu, 19-Jan" or "Thu, 5 Jan" — BOTH occur,
    # so the separator is [- ] and not the hyphen the original pattern assumed.
    head = table[: table.find("</thead>") + 8] if "</thead>" in table else table
    date_tokens = re.findall(r"(\d{1,2})[-\s]([A-Z][a-z]{2})\b", head)
    dates: list[str] = []
    for day_s, mon_s in date_tokens:
        mon = _MONTHS.get(mon_s)
        if mon is None:
            continue
        yr = _resolve_year(mon, page_year, page_month)
        dates.append(f"{yr:04d}-{mon:02d}-{int(day_s):02d}")
    if not dates:
        return []

    def _row_values(label: str) -> list[float | None]:
        # Match the <tr> whose first <td> bolds exactly this label.
        pat = re.compile(
            r"<tr>\s*<td[^>]*>\s*<strong>\s*"
            + re.escape(label)
            + r"\s*</strong>.*?</tr>",
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

    ny = _row_values("New York")
    hh = _row_values("Henry Hub")
    if not any(v is not None for v in ny):
        return []  # not a spot table (or no New York row) — not an error

    # ALIGNMENT GUARD. Column i of the value row must be column i of the header,
    # so a table is emitted only when the two line up exactly. A mismatch means
    # the header lost a date (the spaced-separator class above) or a value row
    # bled into its neighbour; either way the dates and prices would be off by
    # one and a silently shifted delivered gas price is worse than a gap.
    if len(ny) != len(dates) or (hh and len(hh) != len(dates)):
        print(
            f"  WARN: spot table skipped — {len(dates)} header date(s) vs "
            f"{len(ny)} New York value(s) (dates {dates[:1]}..{dates[-1:]})",
            file=sys.stderr,
        )
        return []

    rows = []
    for i, date in enumerate(dates):
        t = ny[i]
        h = hh[i] if i < len(hh) else None
        if t is None:
            continue  # "Holiday"/"Closed" — no trade that day, so no row
        rows.append({"date": date, "transco": t, "henry_hub": h})
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
        w.writerow(["date", "transco_z6_ny_usd_mmbtu", "henry_hub_usd_mmbtu"])
        for r in out_rows:
            hh = "" if r["henry_hub"] is None else f"{r['henry_hub']:.4f}"
            w.writerow([r["date"], f"{r['transco']:.4f}", hh])
    print(
        f"fetched {fetched} pages ({failed} failed); "
        f"wrote {len(out_rows)} daily rows -> {args.out}"
    )


if __name__ == "__main__":
    main()
