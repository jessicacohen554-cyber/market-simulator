#!/usr/bin/env python3
"""Scrape the **daily** Algonquin Citygate (AGT) natural-gas spot price from the
EIA Natural Gas Weekly Update archive narrative, for the ISO-NE daily hub-basis
overlay.

ISO-NE's marginal gas unit prices off Algonquin Citygate, the pipeline-constrained
New England trading hub whose winter spot blows out to many multiples of Henry Hub
on the coldest days (gas-for-heating crowds gas-for-power off the Algonquin pipe).
The model has the measured *monthly* AGT basis (``gas_basis_by_iso_month.csv``,
EIA MA-citygate family) - the right level - but a flat monthly plateau never
reaches distillate parity, so the dual-fuel gas->oil switch and the winter LMP
tail are understated. The real daily AGT spot is an ICE/Platts product (paywalled),
but **EIA quotes it for free in the prose of every Weekly Update**, e.g.:

    "At the Algonquin Citygate, which serves Boston-area consumers, the price
     went up $9.31 from $4.04/MMBtu last Wednesday to $13.35/MMBtu yesterday,
     after reaching a weekly high of $17.27/MMBtu on Tuesday."

Each weekly page therefore carries two hard-dated AGT spot prints - the report
Wednesday ("yesterday") and the prior Wednesday ("last Wednesday") - plus, in
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

The 2022-era Weekly Updates phrase the main sentence with an intervening change
figure ("the price went up $3.73 from $18.96/MMBtu last Wednesday to
$22.69/MMBtu yesterday") and often state the cold-week peak/trough by an
absolute calendar date rather than a weekday ("a weekly high of $22.81/MMBtu on
February 3", "a monthly low of $0.74/MMBtu on November 4"). The main regex
therefore spans the change figure, and ``_AGT_CALDATE`` recovers the
calendar-dated extremes (``high_caldate``/``low_caldate``); a high/low with no
dateable anchor ("in advance of the holiday weekend") is left out rather than
guessed (rule 14). The compact EIA "Spot Prices" table carries no Algonquin row
in the 2022 pages either (verified), so the narrative remains the only source.

Output: ``data/raw/gas-prices/algonquin_citygate_daily.csv``
  columns ``date, algonquin_citygate_usd_mmbtu, source`` where ``source`` is the
  narrative anchor the print came from (``wednesday``/``last_wednesday``/
  ``weekly_high``/``weekly_low``/``high_caldate``/``low_caldate``) for
  provenance. Later pages win on a duplicate date (revisions).

``--merge`` seeds from the committed CSV and adds ONLY newly scraped dates,
asserting every pre-existing row survives byte-identical - so a holdout year can
be densified (e.g. ``--start-year 2022 --end-year 2022 --merge``) while the
in-sample 2023-2025 rows stay frozen. The default (no ``--merge``) REPLACES the
file, the original behaviour for a full 2023-2025 rebuild.

Usage:
    uv run python scripts/data/fetch_algonquin_daily_spot.py
    uv run python scripts/data/fetch_algonquin_daily_spot.py --start-year 2023 --end-year 2025
    uv run python scripts/data/fetch_algonquin_daily_spot.py --start-year 2022 --end-year 2022 --merge
"""

from __future__ import annotations

import argparse
import csv
import io
import datetime as dt
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent.parent
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

# Main AGT sentence: two dated Wednesday prints. The bounded ``.{0,220}?`` spans
# the "which serves Boston-area consumers, the price went up/rose/fell ..."
# clause (verb varies week to week) up to the "$X/MMBtu last Wednesday to
# $Y/MMBtu yesterday" pair. It must be able to CROSS an intervening change
# figure: the 2022-era pages phrase it "the price went up $3.73 from
# $18.96/MMBtu last Wednesday to $22.69/MMBtu yesterday" - a ``$``- AND
# ``.``-bearing delta the old ``[^$]*?`` / a ``[^.]*?`` both choke on. The
# bound keeps the (non-greedy) span inside the Algonquin sentence so it cannot
# latch onto a different hub's "last Wednesday ... yesterday" pair.
_AGT_MAIN = re.compile(
    r"Algonquin Citygate.{0,220}?\$([0-9]+\.?[0-9]*)/MMBtu\s+last Wednesday\s+to\s+"
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

# Explicit-calendar-date weekly/monthly high/low, the dominant 2022-era shape:
# "Algonquin Citygate price reached a weekly high of $22.81/MMBtu on February 3"
# / "monthly low of $0.74/MMBtu on November 4". Unlike ``_HILO_TAIL`` (which
# pins a weekday name onto a report-week column), this carries an absolute
# ``Month Day`` that dates the print directly - so it recovers the cold-week
# extremes on the many 2022 pages that state the peak/trough by calendar date
# rather than by weekday. Anchored to "Algonquin Citygate" within the sentence
# (``[^.]*?``) so it cannot borrow a neighbouring hub's extreme.
_MONTHS_FULL = {
    m: i
    for i, m in enumerate(
        [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ],
        start=1,
    )
}
_AGT_CALDATE = re.compile(
    r"Algonquin Citygate[^.]*?(?:weekly|monthly)\s+(high|low)\s+of\s+"
    r"\$([0-9]+\.?[0-9]*)/MMBtu\s+on\s+(" + "|".join(_MONTHS_FULL) + r")\s+(\d{1,2})",
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


def parse_agt(
    html: str, cols: list[dt.date], page_year: int, page_month: int
) -> list[tuple[dt.date, float, str]]:
    """Return ``[(date, price, source)]`` AGT prints from one weekly narrative.

    ``cols`` are the report-week column dates; the Wednesday among them is the
    narrative "yesterday" and anchors the two main Wednesday prints. Weekday
    high/lows map onto ``cols``; explicit ``Month Day`` extremes are dated
    directly (``page_year``/``page_month`` resolve the Dec/Jan boundary the
    report week straddles). Returns ``[]`` when the column dates are absent.
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

    # Explicit-calendar-date weekly/monthly high/low (the dominant 2022 shape).
    for kind, price_s, mon_s, day_s in _AGT_CALDATE.findall(text):
        mon = _MONTHS_FULL[mon_s.capitalize()]
        try:
            d = dt.date(_resolve_year(mon, page_year, page_month), mon, int(day_s))
        except ValueError:
            continue
        src = f"{kind.lower()}_caldate"
        # Never overwrite a primary Wednesday print; a dated extreme is a more
        # precise anchor than a weekday-mapped high/low, so it may replace one.
        if d not in by_date or by_date[d][1] not in ("wednesday", "last_wednesday"):
            by_date[d] = (float(price_s), src)

    return [(d, p, s) for d, (p, s) in sorted(by_date.items())]


def _load_existing(path: Path) -> dict[dt.date, tuple[float, str]]:
    """Read a committed AGT CSV into ``{date: (price, source)}`` for merging."""
    out: dict[dt.date, tuple[float, str]] = {}
    with path.open(newline="") as fh:
        r = csv.reader(fh)
        next(r, None)  # header
        for row in r:
            if len(row) >= 3 and row[0]:
                out[dt.date.fromisoformat(row[0])] = (float(row[1]), row[2])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start-year", type=int, default=2023)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--sleep", type=float, default=0.5)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    ap.add_argument(
        "--merge",
        action="store_true",
        help="MERGE into the committed CSV instead of REPLACING it: seed from "
        "the existing file, add ONLY newly scraped dates, and assert every "
        "pre-existing row survives byte-identical. Use with a holdout-year "
        "window (e.g. --start-year 2022 --end-year 2022) to densify one year "
        "while the in-sample 2023-2025 rows stay frozen.",
    )
    args = ap.parse_args()

    # Freeze anchor: the committed data lines that must survive a merge verbatim.
    frozen_lines: set[bytes] = set()
    by_date: dict[dt.date, tuple[float, str]] = {}
    if args.merge and args.out.exists():
        by_date = _load_existing(args.out)
        raw = args.out.read_bytes().split(b"\r\n")
        frozen_lines = {ln for ln in raw[1:] if ln}  # data lines, sans header
        print(f"merge: seeded {len(by_date)} committed AGT prints (frozen)")
    seeded_dates = set(by_date)

    try:
        pages = archive_pages(args.start_year, args.end_year)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: archive index fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"archive: {len(pages)} weekly pages {args.start_year}..{args.end_year + 1}")

    fetched = failed = no_agt = added = 0
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL - {exc}", file=sys.stderr)
            failed += 1
            continue
        cols = column_dates(html, y, m)
        prints = parse_agt(html, cols, y, m)
        if not prints:
            no_agt += 1
        for date, price, src in prints:
            if not (args.start_year <= date.year <= args.end_year):
                continue
            # In merge mode a committed (in-sample) date is frozen: never touch it.
            if args.merge and date in seeded_dates:
                continue
            if date not in by_date:
                added += 1
            by_date[date] = (price, src)  # later page wins (revisions)
        fetched += 1
        time.sleep(args.sleep)

    # Render the merged CSV in memory first so a failed freeze-check can never
    # leave a corrupted committed file behind.
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["date", "algonquin_citygate_usd_mmbtu", "source"])
    for date in sorted(by_date):
        price, src = by_date[date]
        w.writerow([date.isoformat(), f"{price:.4f}", src])
    out_bytes = buf.getvalue().encode()

    if args.merge:
        # Byte-freeze proof: every committed data line must reappear verbatim.
        new_lines = set(out_bytes.split(b"\r\n"))
        dropped = [ln for ln in frozen_lines if ln not in new_lines]
        if dropped:
            raise SystemExit(
                f"MERGE ABORTED: {len(dropped)} committed rows would change, e.g. "
                f"{dropped[0][:60]!r} - refusing to write"
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out_bytes)
    if args.merge:
        print(
            f"fetched {fetched} pages ({failed} failed, {no_agt} without an AGT "
            f"print); merged +{added} new AGT prints, {len(frozen_lines)} committed "
            f"rows frozen -> {args.out} ({len(by_date)} total)"
        )
    else:
        print(
            f"fetched {fetched} pages ({failed} failed, {no_agt} without an AGT "
            f"print); wrote {len(by_date)} daily AGT prints -> {args.out}"
        )


if __name__ == "__main__":
    main()
