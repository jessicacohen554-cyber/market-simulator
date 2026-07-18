#!/usr/bin/env python3
"""Scrape weekly **PG&E Citygate** and **SoCal Citygate** Wednesday spot prints
from the EIA Natural Gas Weekly Update archive, for the CAISO zonal gas basis.

The model's CAISO gas path prices every zone off ONE blended series — the EIA
California Composite Average citygate (``fetch_caiso_citygate_daily.py`` daily +
the N3050CA3 monthly basis) — so NP15/ZP26 and SP15 gas fleets are equally
cheap and the LP develops no systematic north-south dispatch gradient: the
model's NP15 and ZP26 clear byte-identical prices (Path 15 never binds) and its
north-south LMP basis carries the wrong sign vs the measured hub LMPs (model
SP15 $2-4.5 ABOVE NP15; actual NP15 $6-8 ABOVE SP15 in 2024-25). In reality the
two halves of CAISO buy gas at different hubs — the north at **PG&E Citygate**,
the south at **SoCal Citygate** — and the persistent PG&E-vs-SoCal spot spread
is the marginal-cost gradient that pushes south-to-north flows until Paths
15/26 bind and the zonal LMPs separate.

Unlike the Cal.-Comp.-Avg blend, the two hubs have no row in the archive pages'
compact spot table — but the **narrative bullets** of nearly every weekly issue
quote both hubs' Wednesday prints, in the fixed EIA construction::

    The price at PG&E Citygate in Northern California rose 19 cents from
    $1.86/MMBtu last Wednesday to $2.05/MMBtu yesterday.

Each sentence carries TWO dated prints (last Wednesday and "yesterday", the
Wednesday before the Thursday publication), so a full crawl yields roughly
weekly coverage per hub with a same-print overlap between consecutive issues
that cross-validates the parse. Parsing is scoped to the text between one
"price at" mention and the next so a week that quotes only one hub can never
attribute the other hub's number to it. This is the same free published print
the committed ERCOT ``Waha`` basis rows cite ("NGI/EIA NG Weekly"), applied at
weekly rather than annual resolution (CLAUDE.md rule 14 — measured data over
estimates, with the source citable per print).

Output: ``data/raw/gas-prices/pge_socal_citygate_weekly.csv``
  columns ``date, pge_citygate_usd_mmbtu, socal_citygate_usd_mmbtu`` — one row
  per quoted Wednesday; a hub not quoted that week is empty.

Usage:
    python scripts/data/fetch_pge_socal_citygate_daily.py
    python scripts/data/fetch_pge_socal_citygate_daily.py --start-year 2023 --end-year 2025
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

OUT_PATH = REPO / "data" / "raw" / "gas-prices" / "pge_socal_citygate_weekly.csv"

# One narrative price sentence: "The price at <hub> ... [from $A/MMBtu last
# Wednesday] to/at $B/MMBtu yesterday." Windows are cut at the NEXT "price at"
# (or "The price of") so a hub's window can never swallow another hub's quote.
_PRICE_AT = re.compile(r"[Tt]he price (?:at|of)\b")
_HUB_PATS = {
    "pge": re.compile(r"PG&(?:amp;)?E\s*Citygate"),
    "socal": re.compile(r"SoCal\s*Citygate"),
}
_FROM_TO = re.compile(
    r"from\s*\$(\d+\.\d+)/MMBtu\s*last\s*Wednesday\s*"
    r".{0,80}?\$(\d+\.\d+)/MMBtu\s*yesterday",
    re.S,
)
_TO_ONLY = re.compile(r"\$(\d+\.\d+)/MMBtu\s*yesterday")


def parse_weekly_prints(html: str, pub: date) -> dict[str, dict[str, float]]:
    """Extract the two hubs' dated Wednesday prints from one issue's narrative.

    Returns ``{iso_date: {hub: price}}`` where ``iso_date`` is the Wednesday the
    print quotes: "yesterday" = publication Thursday − 1 day, "last Wednesday" =
    publication Thursday − 8 days. Only sentences opening with EIA's "The price
    at/of …" construction are read, and each sentence window ends at the next
    such opener, so at most one hub's quotes are in scope per window.
    """
    out: dict[str, dict[str, float]] = {}
    yesterday = (pub - timedelta(days=1)).isoformat()
    last_wed = (pub - timedelta(days=8)).isoformat()
    starts = [m.start() for m in _PRICE_AT.finditer(html)]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else min(s + 800, len(html))
        win = html[s:end]
        for hub, hub_pat in _HUB_PATS.items():
            hm = hub_pat.search(win[:120])  # hub named right after "price at"
            if not hm:
                continue
            ft = _FROM_TO.search(win)
            if ft:
                out.setdefault(last_wed, {})[hub] = float(ft.group(1))
                out.setdefault(yesterday, {})[hub] = float(ft.group(2))
            else:
                to = _TO_ONLY.search(win)
                if to:
                    out.setdefault(yesterday, {})[hub] = float(to.group(1))
    return out


def main() -> None:
    """CLI: crawl the weekly archive and write the two-hub Wednesday-print CSV."""
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

    by_date: dict[str, dict[str, float]] = {}
    conflicts = 0
    fetched = failed = 0
    for y, m, d in pages:
        url = PAGE_TMPL.format(y=y, m=m, d=d)
        try:
            html = _fetch(url)
        except (HTTPError, URLError) as exc:
            print(f"  {y}-{m:02d}-{d:02d}: FETCH FAIL — {exc}", file=sys.stderr)
            failed += 1
            continue
        prints = parse_weekly_prints(html, date(y, m, d))
        for dt, hubs in prints.items():
            if not (args.start_year <= int(dt[:4]) <= args.end_year):
                continue
            slot = by_date.setdefault(dt, {})
            for hub, price in hubs.items():
                # Consecutive issues overlap on one Wednesday (this week's "last
                # Wednesday" = prior week's "yesterday"); a disagreement means a
                # mis-parse, so flag it loudly and keep the first-seen value.
                if hub in slot and abs(slot[hub] - price) > 0.005:
                    conflicts += 1
                    print(
                        f"  CONFLICT {dt} {hub}: {slot[hub]} vs {price} "
                        f"(page {y}-{m:02d}-{d:02d})",
                        file=sys.stderr,
                    )
                    continue
                slot[hub] = price
        fetched += 1
        time.sleep(args.sleep)

    out_rows = sorted(by_date)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["date", "pge_citygate_usd_mmbtu", "socal_citygate_usd_mmbtu"])
        for dt in out_rows:
            hubs = by_date[dt]
            w.writerow(
                [
                    dt,
                    f"{hubs['pge']:.2f}" if "pge" in hubs else "",
                    f"{hubs['socal']:.2f}" if "socal" in hubs else "",
                ]
            )
    n_pge = sum(1 for d_ in by_date.values() if "pge" in d_)
    n_soc = sum(1 for d_ in by_date.values() if "socal" in d_)
    n_both = sum(1 for d_ in by_date.values() if "pge" in d_ and "socal" in d_)
    print(
        f"fetched {fetched} pages ({failed} failed, {conflicts} conflicts); "
        f"{len(out_rows)} dated Wednesdays -> {args.out}\n"
        f"coverage: PG&E {n_pge}, SoCal {n_soc}, both {n_both}"
    )


if __name__ == "__main__":
    main()
