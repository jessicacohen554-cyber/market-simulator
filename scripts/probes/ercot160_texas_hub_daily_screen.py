#!/usr/bin/env python3
"""ERCOT-160 — screen the FREE paths for a daily Texas gas hub series.

ERCOT-147 §4 part (2) asks for a Waha + HSC/Katy **daily** series, the same
intake the `winter_citygate_daily` ERCOT cell has been waiting on, and says
"licensing must be checked before promising it". This probe performs that
check against the two free paths the repo already knows how to read, and
records the answer so it is not re-litigated from memory.

It measures, it does not assume:

1. **EIA's Natural Gas Weekly Update** compact "Spot Prices ($/MMBtu)" table
   — the page `scripts/data/fetch_{miso,caiso,transco,algonquin}_*` already
   scrape. The probe fetches a real archive page and reports which hub rows
   the table carries, and whether any Texas hub appears anywhere on it.
   (`docs/data-licensing.md` §5 names the table's columns as Henry Hub /
   New York / Chicago / California Composite Average; this re-measures it.)
2. **ERCOT's own MIS product catalog** (`all-emil-items-search.json`, the
   unauthenticated feed `scripts/data/fetch_ercot_as_reports.py` verifies
   report-type IDs against) — searched for any product that publishes a fuel
   *price* series. ERCOT's settlement Fuel Index Price would be the ideal
   public Texas daily gas number if it were posted as a data product.

A hit on either path is a fetchable intake. A miss on both means the series
exists only behind NGI / Platts / Argus, which is an OWNER LICENSING DECISION
(compounded by the unresolved `docs/data-licensing.md` §5 finding on the NGI
series the repo already carries) — a MANUAL/BLOCKED line, never an inferred
zero and never a substituted Henry Hub.

Run:
    python scripts/probes/ercot160_texas_hub_daily_screen.py
    python scripts/probes/ercot160_texas_hub_daily_screen.py --out results/calibration/ercot160_texas_hub_screen.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parents[2]
NGWU_FETCHER = REPO / "scripts/data/fetch_miso_citygate_daily.py"
EMIL_CATALOG = (
    "https://www.ercot.com/api/1/services/read/common/all-emil-items-search.json"
)
# Texas trading points a CT conduct-vs-fuel-basis identification would need.
TEXAS_HUBS = ("Waha", "Houston Ship", "Katy", "Permian", "Agua Dulce", "Carthage")
# Hub rows the repo already sources off the same free EIA table.
KNOWN_ROWS = ("Henry Hub", "New York", "Chicago", "Cal. comp", "Algonquin")
_TIMEOUT_S = 120


def _load_ngwu_fetcher():
    """Import the committed NGWU scraper so this screen reads the same page."""
    spec = importlib.util.spec_from_file_location("ngwu", NGWU_FETCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def screen_eia_ngwu() -> dict:
    """Report which hub rows EIA's free weekly spot table actually carries."""
    ngwu = _load_ngwu_fetcher()
    pages = ngwu.archive_pages(2025, 2025)
    if not pages:
        return {"reachable": False, "reason": "no archive page discovered"}
    year, month, day = pages[len(pages) // 2]
    html = ngwu._fetch(ngwu.PAGE_TMPL.format(y=year, m=month, d=day))
    parsed = ngwu.parse_spot_table(html, year, month)
    return {
        "reachable": True,
        "page": f"{year}-{month:02d}-{day:02d}",
        "parsed_spot_rows": len(parsed),
        "spot_table_columns": sorted({k for row in parsed for k in row if k != "date"}),
        "known_row_mentions": {
            name: len(re.findall(re.escape(name), html, re.I)) for name in KNOWN_ROWS
        },
        "texas_hub_mentions": {
            hub: len(re.findall(re.escape(hub), html, re.I)) for hub in TEXAS_HUBS
        },
    }


def screen_ercot_catalog() -> dict:
    """Report whether ERCOT publishes any fuel PRICE series as a data product."""
    items = requests.get(EMIL_CATALOG, timeout=_TIMEOUT_S).json()
    fuel_items = [i for i in items if "fuel" in json.dumps(i).lower()]
    named = []
    for item in fuel_items:
        named.append(
            {
                "emilId": item.get("emilId_s"),
                "productName": item.get("productName_s"),
                "reportTypeId": item.get("reportTypeId_i"),
            }
        )
    price_like = [
        n
        for n in named
        if n["productName"]
        and re.search(r"index price|price index|fuel price", n["productName"], re.I)
    ]
    return {
        "catalog_items": len(items),
        "items_mentioning_fuel": len(fuel_items),
        "fuel_products": sorted(named, key=lambda n: str(n["emilId"])),
        "fuel_price_series_products": price_like,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=None, help="write the screen JSON here")
    args = ap.parse_args()

    eia = screen_eia_ngwu()
    ercot = screen_ercot_catalog()

    eia_hit = eia.get("reachable") and any(
        # a Texas hub is only a HIT if the parsed spot TABLE carries it, not
        # if the narrative prose merely mentions it in passing.
        hub.lower().replace(" ", "_") in {c.lower() for c in eia["spot_table_columns"]}
        for hub in TEXAS_HUBS
    )
    ercot_hit = bool(ercot["fuel_price_series_products"])
    verdict = {
        "eia_ngwu_carries_texas_hub_daily": bool(eia_hit),
        "ercot_mis_publishes_fuel_price_series": ercot_hit,
        "free_path_available": bool(eia_hit or ercot_hit),
        "conclusion": (
            "FETCHABLE"
            if (eia_hit or ercot_hit)
            else "BLOCKED — licensed source only (NGI/Platts/Argus); owner decision"
        ),
    }

    out = {"eia_ngwu": eia, "ercot_catalog": ercot, "verdict": verdict}
    print(json.dumps(out, indent=2))
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(out, indent=2) + "\n")
        print(f"\nwrote {path}")


if __name__ == "__main__":
    main()
