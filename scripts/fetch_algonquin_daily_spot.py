#!/usr/bin/env python3
"""Scrape the **daily** Algonquin Citygate (AGT) natural-gas spot price from the
EIA Natural Gas Weekly Update archive narrative, for the ISO-NE daily hub-basis
overlay.

ISO-NE's marginal gas unit prices off Algonquin Citygate, the pipeline-constrained
New England trading hub whose winter spot blows out to many multiples of Henry Hub
on the coldest days (gas-for-heating crowds gas-for-power off the Algonquin pipe).
The model has the measured *monthly* AGT basis (``gas_basis_by_iso_month.csv``,
EIA MA-citygate family) — the right level — but a flat monthly plateau never
reaches distillate parity, so the dual-fuel gas->oil switch and the winter LMP
tail are understated. The real daily AGT spot is an ICE/Platts product (paywalled),
but **EIA quotes it for free in the prose of every Weekly Update**, e.g.:

    "At the Algonquin Citygate, which serves Boston-area consumers, the price
     went up $9.31 from $4.04/MMBtu last Wednesday to $13.35/MMBtu yesterday,
     after reaching a weekly high of $17.27/MMBtu on Tuesday."

Each weekly page therefore carries two hard-dated AGT spot prints — the report
Wednesday ("yesterday") and the prior Wednesday ("last Wednesday") — plus, in
volatile (winter) weeks, a named-weekday weekly high and/or low. These are real
measured AGT quotes, densest exactly in the cold weeks that set the price tail.
This is the AGT analogue of ``fetch_transco_daily_spot.py`` (which reads the
structured "New York"/Transco Z6 NY row of the same pages); the compact EIA spot
table has no Algonquin row, so AGT is recovered from the narrative instead.

Source: ``https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/YYYY/MM_DD/`` (one
per publication Thursday). The five daily column dates in the page's "Spot Prices"
table header pin the calendar: the last (Wednesday) column is the narrative's
"yesterday", and "last Wednesday" is seven days earlier; weekly high/low weekday
names map onto the five column dates of the report week.

Output: ``data/raw/gas-prices/algonquin_citygate_daily.csv``
  columns ``date, algonquin_citygate_usd_mmbtu, source`` where ``source`` is the
  narrative anchor the print came from (``wednesday``/``last_wednesday``/
  ``weekly_high``/``weekly_low``) for provenance. Later pages win on a duplicate
  date (revisions).

Usage:
    uv run python scripts/fetch_algonquin_daily_spot.py
    uv run python scripts/fetch_algonquin_daily_spot.py --start-year 2023 --end-year 2025
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "raw" / "gas-prices" / "algonquin_citygate_daily.csv"

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
_WEEKDAY = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

# Main AGT sentence: two dated Wednesday prints. The ``[^$]*?`` spans the
# "which serves Boston-area consumers, the price went up/rose/fell ..." clause
# (verb varies week to week) up to the first dollar figure.
_AGT_MAIN = re.compile(
    r"Algonquin Citygate[^$]*?\$([0-9]+\.?[0-9]*)/MMBtu\s+last Wednesday\s+to\s+"
    r"\$([0-9]+\.?[0-9]*)/MMBtu\s+yesterday",
    flags=re.S | re.I,
)
_AGT_HIGH = re.compile(
    r"Algonquin Citygate[^.]*?weekly high of\s+\$([0-9]+\.?[0-9]*)/MMBtu\s+on\s+(\w+day)",
    flags=re.S | re.I,
)
_AGT_LOW = re.compile(
    r"Algonquin Citygate[^.]*?weekly low of\s+\$([0-9]+\.?[0-9]*)/MMBtu\s+on\s+(\w+day)",
    flags=re.S | re.I,
)
# A standalone "reaching a weekly high of $X/MMBtu on Day" can follow the main
# sentence (its subject is still Algonquin); capture that shape too.
_HILO_TAIL = re.compile(
    r"weekly (high|low) of\s+\$([0-9]+\.?[0-9]*)/MMBtu\s+on\s+(\w+day)",
    flags=re.S | re.I,
)


def _fetch(url: str, timeout: int = 60) -> str:
    """GET a URL with a browser-ish UA, returning decoded text. Raises on error."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-sim data fetch)"})
    with urlopen(req, timeout=timeout) as fh:
        return fh.read().decode("utf-8", errors="replace")


def archive_pages(start_year: int, end_year: int) -> list[tuple[int, int, int]]:
    """Return sorted ``(year, month, day)`` publication dates of archive pages.

    A page published in month M reports the prior week, so a late-December week is
    published the following January; we keep pages through the first weeks of
    ``end_year + 1`` to capture every day in ``[start_year, end_year]``.
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


def column_dates(html: str, page_year: int, page_month: int) -> list[dt.date]:
    """Return the five ``date`` objects (Thu..Wed) of the page's Spot Prices table.

    These pin the narrative calendar: the last/Wednesday column is "yesterday",
    "last Wednesday" is seven days earlier, and weekly high/low weekday names map
    onto these five report-week days. Mirrors the header parse in
    ``fetch_transco_daily_spot.py``.
    """
    idx = html.find('id="tabs-prices-2"')
    seg = html[idx : idx + 24000] if idx >= 0 else html[:24000]
    seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)  # drop commented templates
    head = seg[: seg.find("</thead>") + 8] if "</thead>" in seg else seg
    out: list[dt.date] = []
    for day_s, mon_s in re.findall(r"(\d{1,2})-([A-Z][a-z]{2})", head):
        mon = _MONTHS.get(mon_s)
        if mon is None:
            continue
        yr = _resolve_year(mon, page_year, page_month)
        try:
            out.append(dt.date(yr, mon, int(day_s)))
        except ValueError:
            continue
    return sorted(set(out))


def parse_agt(html: str, cols: list[dt.date]) -> list[tuple[dt.date, float, str]]:
    """Return ``[(date, price, source)]`` AGT prints from one weekly narrative.

    ``cols`` are the report-week column dates; the Wednesday among them is the
    narrative "yesterday" and anchors the two main Wednesday prints. Returns
    ``[]`` when neither the column dates nor the main sentence are found.
    """
    if not cols:
        return []
    text = re.sub(r"<[^>]+>", " ", html)  # strip tags/links inside the prose
    text = re.sub(r"\s+", " ", text)
    wednesdays = [d for d in cols if d.weekday() == _WEEKDAY["Wednesday"]]
    yesterday = wednesdays[-1] if wednesdays else cols[-1]
    last_wed = yesterday - dt.timedelta(days=7)
    by_date: dict[dt.date, tuple[float, str]] = {}

    m = _AGT_MAIN.search(text)
    if m:
        by_date[last_wed] = (float(m.group(1)), "last_wednesday")
        by_date[yesterday] = (float(m.group(2)), "wednesday")

    # Weekly high/low on a named weekday within the report week (cols).
    col_by_wd = {d.weekday(): d for d in cols}
    for kind, price_s, wd_s in _HILO_TAIL.findall(text):
        wd = _WEEKDAY.get(wd_s.capitalize())
        if wd is None or wd not in col_by_wd:
            continue
        d = col_by_wd[wd]
        src = f"weekly_{kind.lower()}"
        # Don't let a high/low overwrite a primary Wednesday print.
        if d not in by_date or by_date[d][1].startswith("weekly"):
            by_date[d] = (float(price_s), src)

    return [(d, p, s) for d, (p, s) in sorted(by_date.items())]


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

    by_date: dict[dt.date, tuple[float, str]] = {}
    fetched = failed = no_agt = 0
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL — {exc}", file=sys.stderr)
            failed += 1
            continue
        cols = column_dates(html, y, m)
        prints = parse_agt(html, cols)
        if not prints:
            no_agt += 1
        for date, price, src in prints:
            if args.start_year <= date.year <= args.end_year:
                by_date[date] = (price, src)  # later page wins (revisions)
        fetched += 1
        time.sleep(args.sleep)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "algonquin_citygate_usd_mmbtu", "source"])
        for date in sorted(by_date):
            price, src = by_date[date]
            w.writerow([date.isoformat(), f"{price:.4f}", src])
    print(
        f"fetched {fetched} pages ({failed} failed, {no_agt} without an AGT print); "
        f"wrote {len(by_date)} daily AGT prints -> {args.out}"
    )


if __name__ == "__main__":
    main()
