#!/usr/bin/env python3
"""Harvest NYISO-hub daily gas prints from the EIA NG Weekly Update narrative.

Companion to ``fetch_transco_daily_spot.py`` (which reads the structured
"New York" row of the archive pages' compact Spot Prices table) and the exact
NYISO analogue of ``fetch_algonquin_daily_spot.py``: every weekly page's prose
carries two hard-dated spot prints per hub — the report Wednesday
("yesterday") and the prior Wednesday ("last Wednesday") — plus, in volatile
(winter) weeks, a named-weekday weekly high and/or low, e.g.::

    "At the Transcontinental Pipeline Zone 6 trading point for New York City,
     the price went up $1.51 from $3.34/MMBtu last Wednesday to $4.85/MMBtu
     yesterday, after reaching a weekly high of $9.10/MMBtu on Monday."

Two harvests from the same pages:

* **Transco Z6 NY** ("New York" narrative): merged into
  ``data/raw/gas-prices/transco_z6_ny_daily.csv`` (union with the table-scrape
  rows; a table row wins on a duplicate date — it is the same NGI print without
  narrative rounding). The narrative reaches weeks whose table scrape is
  missing (holiday-week archive gaps — the Dec-2024 late-month hole that
  under-reads the month) and adds the true-dated weekly-high/low spike prints.
* **Iroquois** (opportunistic): any narrative print naming the Iroquois
  pipeline's trading points, written to
  ``data/raw/gas-prices/iroquois_z2_daily.csv`` with the location tagged
  (``zone2`` / ``waddington`` / ``unknown``). Only ``zone2`` rows are consumed
  by the model (``fuel._iroquois_z2_daily``); the others are provenance. EIA's
  free compact table has no Iroquois row, so the narrative is the only free
  source — coverage is expected to be sparse and winter-concentrated, which is
  exactly where it matters.

After merging, the NYISO monthly hub files are **recomputed from the completed
daily series** for months whose print coverage changed:
``transco_z6_iroquois_monthly.csv`` (Transco monthly mean of daily quotes +
the unchanged SOM annual Iroquois-Transco spread) and the NYISO rows of
``gas_basis_by_iso_month.csv`` (Iroquois monthly − Henry Hub monthly). This is
the same "monthly mean of daily quotes" construction those files already
document — just with the recovered prints included, so an under-sampled month
(Dec-2024: 12 early-month prints, none after the 18th) stops under-reading its
own measured series.

Usage:
    uv run python scripts/data/fetch_nyiso_gas_narrative.py
    uv run python scripts/data/fetch_nyiso_gas_narrative.py --start-year 2023 --end-year 2025
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parent.parent.parent
GAS_DIR = REPO / "data" / "raw" / "gas-prices"
TRANSCO_PATH = GAS_DIR / "transco_z6_ny_daily.csv"
IROQUOIS_PATH = GAS_DIR / "iroquois_z2_daily.csv"
MONTHLY_HUB_PATH = GAS_DIR / "transco_z6_iroquois_monthly.csv"
HH_MONTHLY_PATH = GAS_DIR / "henry_hub_monthly.csv"
BASIS_PATH = REPO / "data" / "raw" / "gas_basis_by_iso_month.csv"

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

# Hub anchors in the narrative. The NY hub is named several ways across
# vintages; all resolve to Transco Z6 NY (the NGI "New York" location).
_HUB_ANCHORS: dict[str, re.Pattern[str]] = {
    "transco": re.compile(
        r"(?:Transco(?:ntinental)?(?:\s+Pipeline)?\s+Zone\s*6"
        r"(?:\s+trading\s+point)?(?:\s+for\s+New\s+York(?:\s+City)?)?"
        r"|Zone\s*6\s+trading\s+point\s+for\s+New\s+York)",
        flags=re.I,
    ),
    "iroquois": re.compile(r"Iroquois[\w\s,]*?(?:Zone\s*2|Waddington)?", flags=re.I),
}
# Within a hub's sentence window: the two dated Wednesday prints.
_MAIN = re.compile(
    r"\$([0-9]+\.?[0-9]*)/MMBtu\s+last\s+Wednesday\s+to\s+"
    r"\$([0-9]+\.?[0-9]*)/MMBtu\s+yesterday",
    flags=re.S | re.I,
)
# Within the same window: named-weekday weekly high/low prints.
_HILO = re.compile(
    r"weekly\s+(high|low)\s+of\s+\$([0-9]+\.?[0-9]*)/MMBtu\s+on\s+(\w+day)",
    flags=re.S | re.I,
)
# How far past the anchor one hub's prose can run before the next hub's
# paragraph starts; NGWU hub paragraphs are 1-3 sentences (~450 chars).
_WINDOW = 500


def _fetch(url: str, timeout: int = 60) -> str:
    """GET a URL with a browser-ish UA, returning decoded text. Raises on error."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-sim data fetch)"})
    with urlopen(req, timeout=timeout) as fh:
        return fh.read().decode("utf-8", errors="replace")


def archive_pages(start_year: int, end_year: int) -> list[tuple[int, int, int]]:
    """Return sorted ``(year, month, day)`` publication dates of archive pages."""
    html = _fetch(ARCHIVE_INDEX)
    seen = sorted(set(re.findall(r"archivenew_ngwu/(\d{4})/(\d{2})_(\d{2})", html)))
    out = []
    for y, m, d in seen:
        yi = int(y)
        if start_year <= yi <= end_year + 1:
            out.append((yi, int(m), int(d)))
    return out


def _resolve_year(month: int, page_year: int, page_month: int) -> int:
    """Year of a column dated ``month`` on a page published ``page_year/month``."""
    if month == 12 and page_month == 1:
        return page_year - 1
    if month == 1 and page_month == 12:
        return page_year + 1
    return page_year


def column_dates(html: str, page_year: int, page_month: int) -> list[dt.date]:
    """Return the five (Thu..Wed) report-week dates of the Spot Prices table."""
    idx = html.find('id="tabs-prices-2"')
    seg = html[idx : idx + 24000] if idx >= 0 else html[:24000]
    seg = re.sub(r"<!--.*?-->", "", seg, flags=re.S)
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


def parse_hub(
    text: str, cols: list[dt.date], anchor: re.Pattern[str]
) -> list[tuple[dt.date, float, str, str]]:
    """Return ``[(date, price, source, context)]`` prints for one hub.

    ``text`` is the tag-stripped page prose; ``cols`` the report-week dates.
    Every anchor occurrence opens a bounded sentence window; the Wednesday-pair
    and weekly-high/low patterns are matched only inside that window, so one
    hub's high/low can never be attributed to another hub (the global-findall
    leak the Algonquin scraper tolerates).
    """
    if not cols:
        return []
    wednesdays = [d for d in cols if d.weekday() == _WEEKDAY["Wednesday"]]
    yesterday = wednesdays[-1] if wednesdays else cols[-1]
    last_wed = yesterday - dt.timedelta(days=7)
    col_by_wd = {d.weekday(): d for d in cols}
    by_date: dict[dt.date, tuple[float, str, str]] = {}
    for m in anchor.finditer(text):
        window = text[m.start() : m.start() + _WINDOW]
        context = m.group(0).strip()
        main = _MAIN.search(window)
        if main:
            by_date[last_wed] = (float(main.group(1)), "last_wednesday", context)
            by_date[yesterday] = (float(main.group(2)), "wednesday", context)
        for kind, price_s, wd_s in _HILO.findall(window):
            wd = _WEEKDAY.get(wd_s.capitalize())
            if wd is None or wd not in col_by_wd:
                continue
            d = col_by_wd[wd]
            src = f"weekly_{kind.lower()}"
            if d not in by_date or by_date[d][1].startswith("weekly"):
                by_date[d] = (float(price_s), src, context)
    return [(d, p, s, c) for d, (p, s, c) in sorted(by_date.items())]


def _iroquois_location(context: str) -> str:
    low = context.lower()
    if "zone 2" in low or "zone2" in low:
        return "zone2"
    if "waddington" in low:
        return "waddington"
    return "unknown"


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as fh:
        return list(csv.DictReader(fh))


def _recompute_monthlies(start_year: int, end_year: int) -> None:
    """Recompute the NYISO monthly hub files from the completed daily series.

    Same construction the files document ("monthly mean of daily quotes" +
    the SOM annual Iroquois-Transco spread; basis = Iroquois − Henry Hub) —
    only the print coverage changed. Only rows in [start_year, end_year] move.
    """
    daily = _read_csv(TRANSCO_PATH)
    by_month: dict[str, list[float]] = {}
    for r in daily:
        ym = r["date"][:7]
        try:
            by_month.setdefault(ym, []).append(float(r["transco_z6_ny_usd_mmbtu"]))
        except (KeyError, ValueError):
            continue

    monthly = _read_csv(MONTHLY_HUB_PATH)
    spread_by_year: dict[int, float] = {}
    for r in monthly:
        y = int(r["date"][:4])
        spread = float(r["iroquois_z2_usd_mmbtu"]) - float(r["transco_z6_ny_usd_mmbtu"])
        spread_by_year.setdefault(y, spread)  # SOM annual spread, constant per year

    changed = []
    for r in monthly:
        ym, y = r["date"], int(r["date"][:4])
        if not (start_year <= y <= end_year) or ym not in by_month:
            continue
        new_tz = round(sum(by_month[ym]) / len(by_month[ym]), 4)
        old_tz = float(r["transco_z6_ny_usd_mmbtu"])
        if abs(new_tz - old_tz) < 5e-5:
            continue
        r["transco_z6_ny_usd_mmbtu"] = f"{new_tz}"
        r["iroquois_z2_usd_mmbtu"] = f"{round(new_tz + spread_by_year[y], 4)}"
        changed.append((ym, old_tz, new_tz))
    if changed:
        with MONTHLY_HUB_PATH.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(monthly[0].keys()))
            w.writeheader()
            w.writerows(monthly)
        for ym, old, new in changed:
            print(f"  monthly {ym}: transco {old} -> {new}")

    # Basis rows: NYISO basis = Iroquois monthly − Henry Hub monthly.
    hh = {
        (int(r["year"]), int(r["month"])): float(r["price_usd_mmbtu"])
        for r in _read_csv(HH_MONTHLY_PATH)
    }
    iq = {
        r["date"]: float(r["iroquois_z2_usd_mmbtu"])
        for r in _read_csv(MONTHLY_HUB_PATH)
    }
    basis = _read_csv(BASIS_PATH)
    n_basis = 0
    for r in basis:
        y, m = int(r["year"]), int(r["month"])
        ym = f"{y}-{m:02d}"
        if r["iso"] != "NYISO" or not (start_year <= y <= end_year) or ym not in iq:
            continue
        if (y, m) not in hh:
            continue
        new_b = round(iq[ym] - hh[(y, m)], 4)
        if abs(new_b - float(r["basis_usd_mmbtu"])) >= 5e-5:
            r["basis_usd_mmbtu"] = f"{new_b}"
            n_basis += 1
    if n_basis:
        with BASIS_PATH.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(basis[0].keys()))
            w.writeheader()
            w.writerows(basis)
        print(f"  basis: {n_basis} NYISO rows recomputed")


def _parse_ngpf_table_row(
    html: str, cols: list["dt.date"], row_re: re.Pattern[str]
) -> list[tuple["dt.date", float]]:
    """Return ``[(date, price)]`` from a printer-friendly full spot-table row.

    The archive's printer version (``ngpf.asp``) historically carries the FULL
    NGI spot table (many hubs, incl. Iroquois Zone 2) instead of the compact
    4-row table. Each row is ``<td>Hub name</td>`` followed by five daily
    price cells matching the report-week column dates.
    """
    if not cols:
        return []
    # Work row-wise: split on <tr>, strip tags per row.
    out: list[tuple[dt.date, float]] = []
    for row_html in re.split(r"<tr[^>]*>", html):
        cells = [
            re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c)).strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.S)
        ]
        if not cells or not row_re.search(cells[0]):
            continue
        prices = []
        for c in cells[1:]:
            m = re.match(r"^\$?([0-9]+\.[0-9]+)$", c.replace(",", ""))
            prices.append(float(m.group(1)) if m else None)
        # Align the trailing price cells onto the report-week dates.
        vals = [p for p in prices if p is not None]
        if len(vals) == len(cols):
            out.extend((d, v) for d, v in zip(cols, vals))
        break
    return out


def harvest_ngpf_iroquois(
    pages: list[tuple[int, int, int]],
    start_year: int,
    end_year: int,
    sleep: float,
) -> dict["dt.date", float]:
    """Harvest daily Iroquois Zone 2 prints from the printer-friendly pages.

    Probes the first few pages for an Iroquois row; if the modern printer
    version carries only the compact table (no Iroquois anywhere), bails out
    after the probe window so the run stays fast. Returns ``{date: price}``.
    """
    row_re = re.compile(r"Iroquois", flags=re.I)
    found: dict[dt.date, float] = {}
    probed = hits = 0
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d) + "ngpf.asp"
        try:
            html = _fetch(url)
        except (HTTPError, URLError):
            probed += 1
            if probed >= 6 and hits == 0:
                break
            continue
        cols = column_dates(html, y, m)
        prints = _parse_ngpf_table_row(html, cols, row_re)
        probed += 1
        if prints:
            hits += 1
            for date, price in prints:
                if start_year <= date.year <= end_year:
                    found[date] = price
        if probed >= 6 and hits == 0:
            print("ngpf.asp probe: no Iroquois row in the modern printer table")
            break
        time.sleep(sleep)
    if hits:
        print(f"ngpf.asp: Iroquois row found on {hits}/{probed} pages")
    return found


def probe_ne_dashboard() -> None:
    """Reconnaissance: dump any JSON/CSV data endpoints behind the EIA New
    England natural-gas dashboard that mention Iroquois, for a future harvest.
    Prints findings to the workflow log; writes nothing."""
    try:
        html = _fetch("https://www.eia.gov/dashboard/newengland/naturalgas")
    except (HTTPError, URLError) as exc:
        print(f"NE dashboard probe: fetch failed ({exc})")
        return
    candidates = sorted(
        set(
            re.findall(
                r'["\'](/(?:dashboard|api|opendata)[^"\']*?(?:json|csv|data)[^"\']*)["\']',
                html,
            )
        )
    )[:12]
    print(f"NE dashboard probe: {len(candidates)} candidate data URLs")
    for c in candidates:
        url = "https://www.eia.gov" + c
        try:
            body = _fetch(url)[:4000]
        except (HTTPError, URLError) as exc:
            print(f"  {c}: fetch failed ({exc})")
            continue
        has_iq = "iroquois" in body.lower()
        print(
            f"  {c}: {'IROQUOIS PRESENT' if has_iq else 'no iroquois'} "
            f"(first bytes: {body[:120]!r})"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start-year", type=int, default=2023)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    try:
        pages = archive_pages(args.start_year, args.end_year)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: archive index fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"archive: {len(pages)} weekly pages {args.start_year}..{args.end_year + 1}")

    tz_prints: dict[dt.date, tuple[float, str]] = {}
    iq_prints: dict[dt.date, tuple[float, str, str]] = {}
    fetched = failed = 0
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL — {exc}", file=sys.stderr)
            failed += 1
            continue
        cols = column_dates(html, y, m)
        text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
        for date, price, src, _ctx in parse_hub(text, cols, _HUB_ANCHORS["transco"]):
            if args.start_year <= date.year <= args.end_year:
                tz_prints[date] = (price, src)
        for date, price, src, ctx in parse_hub(text, cols, _HUB_ANCHORS["iroquois"]):
            if args.start_year <= date.year <= args.end_year:
                iq_prints[date] = (price, src, _iroquois_location(ctx))
        fetched += 1
        time.sleep(args.sleep)
    print(
        f"fetched {fetched} pages ({failed} failed): "
        f"{len(tz_prints)} Transco narrative prints, {len(iq_prints)} Iroquois prints"
    )

    # Merge Transco narrative prints into the table-scrape file. A table row
    # wins on a duplicate date (same NGI print, no narrative rounding).
    existing = {r["date"]: r for r in _read_csv(TRANSCO_PATH)}
    added = 0
    for date, (price, _src) in sorted(tz_prints.items()):
        key = date.isoformat()
        if key in existing:
            continue
        existing[key] = {
            "date": key,
            "transco_z6_ny_usd_mmbtu": f"{price}",
            "henry_hub_usd_mmbtu": "",
        }
        added += 1
    if added:
        with TRANSCO_PATH.open("w", newline="") as fh:
            w = csv.DictWriter(
                fh,
                fieldnames=["date", "transco_z6_ny_usd_mmbtu", "henry_hub_usd_mmbtu"],
            )
            w.writeheader()
            w.writerows([existing[k] for k in sorted(existing)])
    print(f"transco: +{added} narrative rows -> {len(existing)} total")

    # Printer-friendly full spot table (structured, dense where present):
    # a table print wins over a narrative print on the same date.
    for date, price in harvest_ngpf_iroquois(
        pages, args.start_year, args.end_year, args.sleep
    ).items():
        iq_prints[date] = (price, "ngpf_table", "zone2")
    probe_ne_dashboard()

    if iq_prints:
        with IROQUOIS_PATH.open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["date", "iroquois_z2_usd_mmbtu", "source", "location"])
            for date, (price, src, loc) in sorted(iq_prints.items()):
                w.writerow([date.isoformat(), price, src, loc])
        print(f"iroquois: {len(iq_prints)} prints written")

    print("recomputing NYISO monthly hub levels from the completed daily series:")
    _recompute_monthlies(args.start_year, args.end_year)


if __name__ == "__main__":
    main()
