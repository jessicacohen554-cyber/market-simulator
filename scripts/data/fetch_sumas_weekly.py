#!/usr/bin/env python3
"""Scrape weekly **Northwest Sumas** Wednesday spot prints from the EIA Natural
Gas Weekly Update archive, for the CAISO north-corridor (Malin-side) gas floor.

The caiso-87 south-corridor surplus-clean trigger keys on the Palo Verde hub
sitting below its own remote gas-CCGT floor, evaluated at the measured SoCal
citygate weekly print (``interchange_config`` depth block). The NORTH-corridor
analogue (COI/Path-66, proxy hub MALIN) needs a *Malin-side* gas series — the
2026-07-16 caiso-87 session showed the north depth is not year-stable under the
(misaligned) SoCal-gas trigger, and the handoff chartered a Malin-appropriate
intake before the north lane may be re-derived.

Malin itself has no row in the archive pages' compact "Spot Prices ($/MMBtu)"
table (Henry Hub / New York / Chicago / Cal. Comp. Avg. only — verified
2026-07-16) and no narrative quote; **Northwest Sumas** is the series EIA does
publish weekly, in the fixed narrative construction the PG&E/SoCal scraper
(``fetch_pge_socal_citygate_daily.py``, the template for this script) already
parses. EIA's own words: "Northwest Sumas on the Canada-Washington border, the
main pricing point for natural gas in the Pacific Northwest". Sumas prices the
gas the Pacific-NW CCGT fleet burns — the fleet whose floor the Malin trigger
needs — so it is the *aligned* measured series for the north corridor
(rule 14: Malin spot itself is unpublished here; Sumas is the reconciled real
print, not a guess; PG&E Citygate would be the misaligned fallback — it prices
gas SOUTH of Malin including California LDC transport).

Three narrative constructions are seen across 2023-2025, all quoting dated
Wednesday prints:

    The price at [Northwest] Sumas ... rose 44 cents from $1.03/MMBtu last
    Wednesday to $1.47/MMBtu yesterday.

    At Northwest Sumas ..., the price increased 68 cents from $3.17/MMBtu
    last Wednesday to $3.85/MMBtu yesterday.

    The price at Northwest Sumas ... increased $2.32 week over week, reaching
    $2.46/MMBtu on Wednesday after beginning the week at $0.14/MMBtu ...

Each sentence carries TWO dated prints (last Wednesday and "yesterday"/"on
Wednesday", the Wednesday before the Thursday publication), so a full crawl
yields roughly weekly coverage with a same-print overlap between consecutive
issues that cross-validates the parse (disagreements are flagged, first-seen
kept — the template's convention).

STALE-REPUBLISH GUARD (not in the template): the 2024-03-07 issue republished
the 2024-02-29 issue's West narrative verbatim, which would mis-date the prior
week's prints one week forward (2024-03-06 would read $1.49 where the genuine
2024-03-14 issue's overlap print says $1.87). A page whose matched Sumas
sentence is character-identical to the immediately preceding issue's sentence
is treated as stale and contributes no prints.

Output: ``data/raw/gas-prices/sumas_weekly.csv``
  columns ``date, sumas_usd_mmbtu`` — one row per quoted Wednesday.

Usage:
    python scripts/data/fetch_sumas_weekly.py
    python scripts/data/fetch_sumas_weekly.py --start-year 2023 --end-year 2025
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))

from scripts.data.fetch_caiso_citygate_daily import (  # noqa: E402
    PAGE_TMPL,
    _fetch,
    archive_pages,
)

OUT_PATH = REPO / "data" / "raw" / "gas-prices" / "sumas_weekly.csv"

# Sentence openers that scope a hub quote: "The price at <hub>" and the
# alternate "At <hub> ..., the price ..." construction. Windows are cut at the
# NEXT opener so another hub's numbers can never be attributed to Sumas.
_OPENER = re.compile(r"[Tt]he price (?:at|of)\b|\bAt\s+(?=[A-Z])")
_SUMAS = re.compile(r"(?:Northwest\s+)?Sumas\b")
_FROM_TO = re.compile(
    r"from\s*\$(-?\d+\.\d+)/MMBtu\s*last\s*Wednesday\s*"
    r".{0,80}?\$(-?\d+\.\d+)/MMBtu\s*(?:yesterday|on\s*Wednesday)",
    re.S,
)
# 2025 variant: "... reaching $B/MMBtu on Wednesday after beginning the week
# at $A/MMBtu" (B = yesterday's Wednesday, A = last Wednesday).
_REACHING = re.compile(
    r"reaching\s*\$(-?\d+\.\d+)/MMBtu\s*on\s*Wednesday\s*"
    r".{0,80}?beginning\s+the\s+week\s+at\s*\$(-?\d+\.\d+)/MMBtu",
    re.S,
)
_TO_ONLY = re.compile(r"\$(-?\d+\.\d+)/MMBtu\s*(?:yesterday|on\s*Wednesday)")


def parse_weekly_prints(html: str, pub: date) -> tuple[dict[str, float], str]:
    """Extract Sumas' dated Wednesday prints from one issue's narrative.

    Returns ``({iso_date: price}, window_text)`` where ``iso_date`` is the
    Wednesday the print quotes: "yesterday"/"on Wednesday" = publication
    Thursday − 1 day, "last Wednesday"/"beginning the week" = publication
    Thursday − 8 days; ``window_text`` is the matched sentence window (used by
    the caller's stale-republish guard). Only sentence windows opening with an
    EIA hub-quote construction and naming Sumas right at the opener are read.
    """
    text = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    out: dict[str, float] = {}
    matched_win = ""
    yesterday = (pub - timedelta(days=1)).isoformat()
    last_wed = (pub - timedelta(days=8)).isoformat()
    starts = [m.start() for m in _OPENER.finditer(text)]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else min(s + 800, len(text))
        win = text[s:end]
        if not _SUMAS.search(win[:60]):  # hub named right at the opener
            continue
        ft = _FROM_TO.search(win)
        if ft:
            out[last_wed] = float(ft.group(1))
            out[yesterday] = float(ft.group(2))
            matched_win = win
            continue
        rc = _REACHING.search(win)
        if rc:
            out[yesterday] = float(rc.group(1))
            out[last_wed] = float(rc.group(2))
            matched_win = win
            continue
        to = _TO_ONLY.search(win)
        if to:
            out[yesterday] = float(to.group(1))
            matched_win = win
    return out, matched_win


def main() -> None:
    """CLI: crawl the weekly archive and write the Sumas Wednesday-print CSV."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start-year", type=int, default=2023)
    ap.add_argument("--end-year", type=int, default=2025)
    ap.add_argument("--sleep", type=float, default=0.4)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    try:
        pages = archive_pages(args.start_year, args.end_year)
    except (HTTPError, URLError) as exc:
        print(f"ERROR: archive index fetch failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"archive: {len(pages)} weekly pages {args.start_year}..{args.end_year + 1}")

    by_date: dict[str, float] = {}
    conflicts = stale = 0
    fetched = failed = 0
    prev_win = ""
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL — {exc}", file=sys.stderr)
            failed += 1
            continue
        prints, win = parse_weekly_prints(html, date(y, m, d))
        if win and win == prev_win:
            stale += 1
            print(
                f"  {y}-{m:02d}-{d:02d}: STALE republish of prior issue's "
                "Sumas sentence — skipped",
                file=sys.stderr,
            )
            fetched += 1
            time.sleep(args.sleep)
            continue
        prev_win = win or prev_win
        for dt, price in prints.items():
            if not (args.start_year <= int(dt[:4]) <= args.end_year):
                continue
            # Consecutive issues overlap on one Wednesday (this week's "last
            # Wednesday" = prior week's "yesterday"); a disagreement means a
            # mis-parse, so flag it loudly and keep the first-seen value.
            if dt in by_date and abs(by_date[dt] - price) > 0.005:
                conflicts += 1
                print(
                    f"  CONFLICT {dt}: {by_date[dt]} vs {price} "
                    f"(page {y}-{m:02d}-{d:02d})",
                    file=sys.stderr,
                )
                continue
            by_date[dt] = price
        fetched += 1
        time.sleep(args.sleep)

    out_rows = sorted(by_date)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "sumas_usd_mmbtu"])
        for dt in out_rows:
            w.writerow([dt, f"{by_date[dt]:.2f}"])
    print(
        f"fetched {fetched} pages ({failed} failed, {conflicts} conflicts, "
        f"{stale} stale republishes); "
        f"{len(out_rows)} dated Wednesdays -> {args.out}"
    )


if __name__ == "__main__":
    main()
