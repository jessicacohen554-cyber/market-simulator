#!/usr/bin/env python3
"""Scrape the daily Algonquin Citygate spot price from EIA's New England Dashboard archive.

``data/raw/gas-prices/algonquin_citygate_daily.csv`` (``fetch_algonquin_daily_spot.py``)
holds only the prints EIA's Natural Gas Weekly Update NARRATIVE names — mostly
Wednesdays — so the daily hub-basis overlay interpolates across exactly the cold-snap
days that set New England's winter price: the series has nothing between 2022-12-21
($6.51) and 2023-01-04 because EIA skipped the 2022-12-29 and 2023-01-05 Weekly
Updates, and Winter Storm Elliott sits in that hole (closeout-NEISO research shard §4;
``FINDING-neiso110`` §3: model delivered gas $12.5-15 on Dec 24-27 2022).

EIA's **New England Dashboard** publishes a daily PDF snapshot (≈ 10:00 ET) whose
"Spot natural gas price (Algonquin Citygate)" tile prints the price as text::

    30.16 $/MMBtu ... Spot natural gas price (Algonquin Citygate) 12/23/22

Archive URL (one PDF per calendar day; weekends/holidays print ``--``; a few days 404)::

    https://www.eia.gov/dashboard/new-england-energy-api/archives/YYYYMM/YYYYMMDD_new_england_dashboard.pdf

The dashboard's notes page names **S&P Global Market Intelligence** as the price
source — like the NGI index the Weekly Update quotes, a proprietary third-party
assessment EIA displays; ``docs/data-licensing.md`` §5's finding for the NGI series
applies here unchanged. The archive begins in 2018 (2018-01 returns 404; 2019-01-31
is served).

Each row keeps BOTH dates because they differ in meaning: ``snapshot_date`` is the
archive day, ``label_date`` the date the tile prints beside the price. The label is
not defined by EIA; matched against dated sources it behaves as the **flow (gas) day**
(dashboard 12/22/22 6.54 and 12/23/22 30.16 vs ISO-NE IMM's gas-day step $6.66 →
$30.05 at HE 11 Dec 23; NGWU trade-day prints line up one day earlier — closeout-NEISO
wave-1 intake record). It is a 10:00 "most recent" figure, not a settled index, and on
at least one extreme day it disagrees with the final assessment (flow 2023-02-03:
dashboard 26.06 vs NGWU/NGI 71.42 traded Feb 2 and the ISO-NE composite 76.42); the
consumer's precedence rule is declared in the closeout-NEISO scarcity-physics PRECOMMIT,
not here. ``last_daily_update`` (the snapshot's own update stamp) is kept for that audit.

Needs ``pdftotext`` (poppler-utils) on PATH. PDFs (~3.5 MB each) are streamed to a
temp file, parsed and deleted; nothing but the CSV is written.

Output: ``data/raw/gas-prices/algonquin_citygate_daily_eia_ne_dashboard.csv``
  ``snapshot_date, label_date, algonquin_citygate_usd_mmbtu, last_daily_update, url``;
  one row per snapshot that prints a value; snapshots printing ``--`` and 404 days are
  counted in the summary, not written.

Usage:
    uv run python scripts/data/fetch_eia_ne_dashboard_agt_daily.py --start 2019-01-01 --end 2025-12-31
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import csv
import datetime as dt
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

URL = (
    "https://www.eia.gov/dashboard/new-england-energy-api/archives/"
    "{d:%Y%m}/{d:%Y%m%d}_new_england_dashboard.pdf"
)
OUT_PATH: Path = (
    RAW_DATA_DIR / "gas-prices" / "algonquin_citygate_daily_eia_ne_dashboard.csv"
)
#: Archive days whose snapshot is defective at the source (verified 2026-10-02): a
#: truncated PDF with no text layer (2020-02-08, 36 KB; 2025-06-07, 28 KB — both
#: Saturdays, no-print days anyway) or a snapshot that omits the price tile and carries
#: only the notes page (2020-05-12). Counted, never failed on; any OTHER unparsed day
#: fails the run.
KNOWN_SOURCE_DEFECTS: frozenset[str] = frozenset(
    {"2020-02-08", "2020-05-12", "2025-06-07"}
)
COLUMNS = (
    "snapshot_date",
    "label_date",
    "algonquin_citygate_usd_mmbtu",
    "last_daily_update",
    "url",
)

# The tile, in every layout seen 2019-2025: a "<value|--> $/MMBtu" figure on the
# nearest line above the "Spot natural gas price" caption that carries one (the
# rightmost figure when several tiles share a row), and the m/d/yy label that ENDS a
# line within four lines after the caption's "Citygate)" (searched from the caption
# on; the 2020 layout wraps "(Algonquin / Citygate)" across two lines; the price tile
# is the rightmost column, so its date ends the line).
# The notes page that only DESCRIBES the indicator ("This indicator ...") is skipped.
_VALUE = re.compile(r"(-?[\d.]+|--) \$/MMBtu")
_LABEL = re.compile(r"Citygate\)[^\n]*\n(?:.*\n){0,3}?.*?(\d+/\d+/\d+)[ \t]*$", re.M)
#: How far above the caption the value line may sit (the 2025-07 layout: 6 lines).
_VALUE_LOOKBACK_LINES = 8
_UPDATE = re.compile(r"Last daily update: (.*?) Next")


def parse_snapshot(text: str) -> tuple[str | None, str | None, str | None]:
    """Return ``(value, label_date_iso, last_daily_update)`` from a snapshot's text.

    ``value`` is ``"--"`` on a no-print day and ``None`` when the tile is not found
    (a layout change — the caller counts these and the run fails loudly).
    """
    update = _UPDATE.search(text)
    stamp = " ".join(update.group(1).split()) if update else None
    for page in text.split("\f"):
        if "Spot natural gas price" not in page or "This indicator" in page:
            continue
        lines = page.splitlines()
        cap = next(i for i, ln in enumerate(lines) if "Spot natural gas price" in ln)
        value = None
        for ln in reversed(lines[max(0, cap - _VALUE_LOOKBACK_LINES) : cap]):
            found = _VALUE.findall(ln)
            if found:
                value = found[-1]
                break
        if value is None:
            continue
        ml = _LABEL.search("\n".join(lines[cap:]))
        label = (
            dt.datetime.strptime(ml.group(1), "%m/%d/%y").date().isoformat()
            if ml
            else None
        )
        return value, label, stamp
    return None, None, stamp


def fetch_day(day: dt.date, session: requests.Session) -> dict:
    """Fetch and parse one archive day; returns a status dict."""
    url = URL.format(d=day)
    for attempt in range(4):
        try:
            resp = session.get(url, timeout=120)
            break
        except requests.RequestException:
            time.sleep(2 ** (attempt + 1))
    else:
        return {"day": day, "status": "error", "url": url}
    if resp.status_code == 404:
        return {"day": day, "status": "404", "url": url}
    resp.raise_for_status()
    with tempfile.NamedTemporaryFile(suffix=".pdf") as fh:
        fh.write(resp.content)
        fh.flush()
        text = subprocess.run(
            ["pdftotext", "-layout", fh.name, "-"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    value, label, update = parse_snapshot(text)
    if value is None or (value != "--" and label is None):
        return {"day": day, "status": "unparsed", "url": url}
    if value == "--":
        return {"day": day, "status": "no_print", "url": url}
    return {
        "day": day,
        "status": "ok",
        "url": url,
        "label": label,
        "value": value,
        "update": update,
    }


def main() -> int:
    """CLI: scrape a date range into the output CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2019, 1, 1))
    ap.add_argument("--end", type=dt.date.fromisoformat, default=dt.date(2025, 12, 31))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args()

    days = [
        args.start + dt.timedelta(n) for n in range((args.end - args.start).days + 1)
    ]
    session = requests.Session()
    results: list[dict] = []
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, res in enumerate(pool.map(lambda d: fetch_day(d, session), days), 1):
            results.append(res)
            if i % 100 == 0:
                print(f"  {i}/{len(days)} days", flush=True)

    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    rows = [r for r in results if r["status"] == "ok"]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(COLUMNS)
        for r in sorted(rows, key=lambda r: r["day"]):
            w.writerow(
                [
                    r["day"].isoformat(),
                    r["label"] or "",
                    r["value"],
                    r["update"] or "",
                    r["url"],
                ]
            )
    print(f"wrote {args.out}: {len(rows)} priced snapshots; status counts {counts}")
    bad = [
        r["day"].isoformat()
        for r in results
        if r["status"] in ("unparsed", "error")
        and r["day"].isoformat() not in KNOWN_SOURCE_DEFECTS
    ]
    if bad:
        print(
            f"UNPARSED/ERROR days ({len(bad)}): {bad[:20]}{' ...' if len(bad) > 20 else ''}"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
