#!/usr/bin/env python3
"""Scrape the **daily** Chicago Citygate natural-gas spot price from the EIA
Natural Gas Weekly Update archive, for the MISO winter fuel-security daily
hub-basis overlay.

MISO's marginal winter gas unit in the North/Central footprint prices off the
Chicago Citygate — the dominant Midwest trading hub — whose spot blows out well
above Henry Hub on the coldest days (gas-for-heating crowds gas-for-power off
the Chicago-area pipes). The model already has the measured *monthly* Chicago
basis (``apply_hub_basis_overlay`` + ``data/raw/gas_basis_by_iso_month.csv``,
MISO Chicago rows), but a flat monthly plateau smears within-month cold-snap
spikes across the mild days — the Jan-2024 Winter Storm Heather week held a
measured **$25.82/MMBtu** Chicago Citygate print on 2024-01-12 (the Friday that
priced storm-weekend delivery) while the monthly average basis (~+$1.82 over
Henry Hub) is applied flat to all 744 January hours, so the cold-day blowout
that sets the MISO winter LMP tail never reaches the merit order on its true
calendar days. The daily series this script builds lets
:func:`market_sim.data.fuel.iso_hub_daily_gas_prices` resolve the real
day-to-day swing, mean-preserving at the monthly hub level, so the annual gas
burn and fuel mix are unchanged while the cold-day spike (and its decay) lands
on the days it actually occurred.

The real daily Chicago Citygate / MichCon spot indices are an ICE/NGI product
(paywalled), but **EIA quotes the Chicago Citygate daily print for free** in the
server-rendered compact "Spot Prices ($/MMBtu)" table of every Weekly Update,
in the **"Chicago"** row — the same free daily table the existing CAISO
(``fetch_caiso_citygate_daily.py``, "Cal. Comp. Avg" row) and NYISO
(``fetch_transco_daily_spot.py``, "New York" row) daily scripts already draw
from. The five daily columns (Thu/Fri/Mon/Tue/Wed) of each page are the trading
days of the week ending the Wednesday before publication; a market holiday
column (e.g. MLK Day) is quoted N/A and skipped.

**MichCon is NOT free.** The compact EIA table carries no MichCon/Michigan row
(verified across the archive) and the narrative never quotes a MichCon daily
print, so lower-Michigan's citygate daily remains the paywalled ICE
manual-download item (``docs/multi-iso/miso-data-audit.md`` Item 4). Chicago
Citygate is the representative MISO North/Central winter gas hub for the
mechanism; this script lands Chicago only and documents the MichCon gap.

**Licensing.** The Chicago spot print is NGI's Daily Gas Price Index compiled by
Bloomberg that EIA merely *displays* — the same proprietary-index provenance
flagged for the sibling AGT/CA/NY daily files in
``data/raw/gas-prices/README.md`` and ``docs/data-licensing.md`` §5. This script
does not resolve that finding; it carries it forward (see
``SOURCES_miso_citygate.md``).

Source: the EIA Natural Gas Weekly Update **archive** pages
``https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/YYYY/MM_DD/`` (one per
publication Thursday).

Output: ``data/raw/gas-prices/miso_citygate_daily.csv``
  columns ``date, chicago_citygate_usd_mmbtu, henry_hub_usd_mmbtu, source``
  where ``source`` is the narrative/table anchor the print came from
  (``eia_ngwu_spot_table`` for the structured daily row). Later pages win on a
  duplicate date (revisions).

``--merge`` seeds from the committed CSV and adds ONLY newly scraped dates,
asserting every pre-existing row survives byte-identical — so a holdout year can
be densified later (e.g. ``--start-year 2022 --end-year 2022 --merge``) while
the in-sample 2023-2025 rows stay frozen (rule 22 / the algonquin precedent).
The default (no ``--merge``) REPLACES the file, for a full 2023-2025 rebuild.

Usage:
    uv run python scripts/fetch_miso_citygate_daily.py
    uv run python scripts/fetch_miso_citygate_daily.py --start-year 2023 --end-year 2025
    uv run python scripts/fetch_miso_citygate_daily.py --start-year 2022 --end-year 2022 --merge
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "raw" / "gas-prices" / "miso_citygate_daily.csv"

ARCHIVE_INDEX = "https://www.eia.gov/naturalgas/weekly/includes/archive.php"
PAGE_TMPL = "https://www.eia.gov/naturalgas/weekly/archivenew_ngwu/{y}/{m:02d}_{d:02d}/"

_SOURCE = "eia_ngwu_spot_table"

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
    """Return ``[{date, chicago, henry_hub}]`` for one weekly page, or ``[]``.

    Locates the active (non-commented) "Spot Prices ($/MMBtu)" table inside the
    ``tabs-prices-2`` block, reads the five daily column dates from the header,
    and the Henry Hub + "Chicago" (Chicago Citygate) rows. Robust to the page's
    whitespace/``<br />`` noise inside each cell and to the header's date
    separator varying between a hyphen (``12-Jan``) and a space (``12 Jan``) on
    the first column of some pages. A market-holiday column is quoted N/A and
    returned as ``None`` (skipped downstream). Mirrors
    ``fetch_caiso_citygate_daily.py``.
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

    # Column dates from the header: "Fri, 12-Jan" or "Fri, 12 Jan" (both seen).
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

    # The Chicago Citygate row is bolded simply "Chicago" in the compact table
    # (verified 2023-2025); the narrative calls it "the Chicago Citygate". It is
    # the only row label starting "Chicago", so the loose anchor is unambiguous.
    chi = _row_values(r"Chicago")
    hh = _row_values(r"Henry\s*Hub")
    rows = []
    for i, date in enumerate(dates):
        c = chi[i] if i < len(chi) else None
        h = hh[i] if i < len(hh) else None
        if c is None:
            continue
        rows.append({"date": date, "chicago": c, "henry_hub": h})
    return rows


def _load_existing(path: Path) -> dict[str, dict]:
    """Read a committed MISO citygate CSV into ``{date: row}`` for merging."""
    out: dict[str, dict] = {}
    with path.open(newline="") as fh:
        r = csv.DictReader(fh)
        for row in r:
            if row.get("date"):
                out[row["date"]] = {
                    "date": row["date"],
                    "chicago": float(row["chicago_citygate_usd_mmbtu"]),
                    "henry_hub": (
                        float(row["henry_hub_usd_mmbtu"])
                        if row.get("henry_hub_usd_mmbtu")
                        else None
                    ),
                }
    return out


def _render(by_date: dict[str, dict]) -> bytes:
    """Render the CSV bytes from ``{date: row}`` (sorted, 4-dp prices)."""
    buf = io.StringIO(newline="")
    w = csv.writer(buf)
    w.writerow(["date", "chicago_citygate_usd_mmbtu", "henry_hub_usd_mmbtu", "source"])
    for date in sorted(by_date):
        r = by_date[date]
        hh = "" if r["henry_hub"] is None else f"{r['henry_hub']:.4f}"
        w.writerow([date, f"{r['chicago']:.4f}", hh, _SOURCE])
    return buf.getvalue().encode()


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
    by_date: dict[str, dict] = {}
    if args.merge and args.out.exists():
        by_date = _load_existing(args.out)
        raw = args.out.read_bytes().split(b"\r\n")
        frozen_lines = {ln for ln in raw[1:] if ln}  # data lines, sans header
        print(f"merge: seeded {len(by_date)} committed Chicago prints (frozen)")
    seeded_dates = set(by_date)

    try:
        pages = archive_pages(args.start_year, args.end_year)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: archive index fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"archive: {len(pages)} weekly pages {args.start_year}..{args.end_year + 1}")

    fetched = failed = no_row = added = 0
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
            no_row += 1
            print(f"  {y}-{m:02d}-{d:02d}: no Chicago spot row parsed", file=sys.stderr)
        for r in rows:
            yr = int(r["date"][:4])
            if not (args.start_year <= yr <= args.end_year):
                continue
            if args.merge and r["date"] in seeded_dates:
                continue  # committed in-sample date is frozen: never touch it
            if r["date"] not in by_date:
                added += 1
            by_date[r["date"]] = r  # later page wins on duplicate (revisions)
        fetched += 1
        time.sleep(args.sleep)

    out_bytes = _render(by_date)

    if args.merge:
        # Byte-freeze proof: every committed data line must reappear verbatim.
        new_lines = set(out_bytes.split(b"\r\n"))
        dropped = [ln for ln in frozen_lines if ln not in new_lines]
        if dropped:
            raise SystemExit(
                f"MERGE ABORTED: {len(dropped)} committed rows would change, e.g. "
                f"{dropped[0][:60]!r} — refusing to write"
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(out_bytes)
    if args.merge:
        print(
            f"fetched {fetched} pages ({failed} failed, {no_row} without a Chicago "
            f"row); merged +{added} new prints, {len(frozen_lines)} committed rows "
            f"frozen -> {args.out} ({len(by_date)} total)"
        )
    else:
        print(
            f"fetched {fetched} pages ({failed} failed, {no_row} without a Chicago "
            f"row); wrote {len(by_date)} daily Chicago prints -> {args.out}"
        )


if __name__ == "__main__":
    main()
