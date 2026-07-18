#!/usr/bin/env python3
"""Fetch EIA Annual Coal Report region/rank f.o.b.-mine coal prices.

The coal-vs-gas passthrough sigmoids (``fuel.coal_sigmoid_params`` /
``config.scenarios.COAL_SIGMOID_DEFAULTS``) key the coal offer curve off the
delivered *gas* price, but the coal side of that curve — where the offer
should sit as a fraction of full cost — has never had a real coal commodity
price to check the ``floor``/``ceil``/``gas_mid`` asymptotes against; every
per-(ISO, supply) entry today is a hand-tuned literal (issue #1347, G-26).
The daily basin spot indices that would be the tightest source (PRB 8800,
Illinois Basin, NAPP, CAPP, Uinta) are S&P Global/Argus/McCloskey-licensed —
even EIA's own current "Coal Markets" weekly report is licensed FROM S&P
Global ("With permission, S&P Global"; historical data "are proprietary" and
"cannot be released by EIA" — https://www.eia.gov/coal/markets/) — so this
script pulls the free public-domain substitute instead: the EIA Annual Coal
Report's own **f.o.b.-mine average sales price**, by producing region and by
coal rank, from the EIA Open Data API v2 (public domain, no license
restriction, https://www.eia.gov/opendata/).

Two ACR tables, both annual, both national/regional (not ISO-specific — the
coal PRODUCING region, not the burning ISO; see
``scripts/data/derive_coal_region_crosswalk.py`` for the region -> ISO-plant
crosswalk):

  * ``coal/market-sales-price`` — average price ($/short ton) and sales
    (short tons) by producing region/state and market type (captive / open
    market / total), all ranks combined. 52 regions incl. Appalachia
    Central/Northern/Southern, Illinois Basin, Powder River Basin, Uinta
    Basin, and per-state rows (TX, ND, LA, MS, ... for lignite; WV split into
    Northern/Southern; KY split into East/West).
  * ``coal/price-by-rank`` — average price ($/short ton) by the same regions,
    broken out by coal rank (bituminous / subbituminous / lignite /
    anthracite / all).

Both regenerate every ACR publication year (annual, ~8-month lag) and respond
to changed conditions (a regional price shift moves next year's release) —
rule-13 admissible as a forward-regenerating commodity input.

Output (raw, immutable, never hand-edited):
  data/raw/coal-prices/eia_coal_market_sales_price.csv
    columns: year, region_id, region_name, market_type_id, market_type_name,
             price_usd_per_ton, sales_short_tons
  data/raw/coal-prices/eia_coal_price_by_rank.csv
    columns: year, region_id, region_name, coal_rank_id, coal_rank_name,
             price_usd_per_ton

EIA API v2 docs: https://www.eia.gov/opendata/documentation.php
Free key: https://www.eia.gov/opendata/register.php

Usage:
    EIA_API_KEY=... python scripts/data/fetch_eia_coal_prices.py
    EIA_API_KEY=... python scripts/data/fetch_eia_coal_prices.py --start-year 2015
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

REPO = Path(__file__).resolve().parent.parent.parent
OUT_DIR = REPO / "data" / "raw" / "coal-prices"
MARKET_SALES_OUT = OUT_DIR / "eia_coal_market_sales_price.csv"
PRICE_BY_RANK_OUT = OUT_DIR / "eia_coal_price_by_rank.csv"

BASE = "https://api.eia.gov/v2"
MARKET_SALES_ROUTE = "coal/market-sales-price"
PRICE_BY_RANK_ROUTE = "coal/price-by-rank"

# EIA suppresses cells that would disclose a single respondent's price ("w" =
# withheld). Kept out of the numeric output; the raw row count still records
# how many region/year cells exist so a withheld cell is visibly absent, not
# silently zero.
_WITHHELD = {"w", "W", "", None}


def _get_all(route: str, params: dict, key: str, sleep_s: float) -> list[dict]:
    """Page through an EIA v2 data route, returning all rows. Raises on failure."""
    rows: list[dict] = []
    offset = 0
    page = 5000
    while True:
        q = {"api_key": key, "length": page, "offset": offset, **params}
        url = f"{BASE}/{route}/data/?{urlencode(q, doseq=True)}"
        try:
            with urlopen(url, timeout=60) as fh:
                payload = json.loads(fh.read().decode())
        except (HTTPError, URLError) as exc:
            raise RuntimeError(f"EIA request failed ({route}): {exc}") from exc
        chunk = payload.get("response", {}).get("data", [])
        rows.extend(chunk)
        if len(chunk) < page:
            break
        offset += page
        time.sleep(sleep_s)
    return rows


def fetch_market_sales_price(key: str, start_year: int, sleep_s: float) -> list[dict]:
    """Return ``[{year, region_id, region_name, market_type_id,
    market_type_name, price_usd_per_ton, sales_short_tons}]`` for every
    producing region and market type (captive/open-market/total) from
    ``start_year`` on."""
    data = _get_all(
        MARKET_SALES_ROUTE,
        {
            "frequency": "annual",
            "data[0]": "price",
            "data[1]": "sales",
            "start": str(start_year),
        },
        key,
        sleep_s,
    )
    rows = []
    for r in data:
        price = r.get("price")
        if price in _WITHHELD:
            continue
        rows.append(
            {
                "year": int(r["period"]),
                "region_id": r["stateRegionId"],
                "region_name": r["stateRegionDescription"],
                "market_type_id": r["marketTypeId"],
                "market_type_name": r["marketTypeDescription"],
                "price_usd_per_ton": round(float(price), 4),
                "sales_short_tons": (
                    None if r.get("sales") in _WITHHELD else round(float(r["sales"]), 1)
                ),
            }
        )
    rows.sort(key=lambda r: (r["year"], r["region_id"], r["market_type_id"]))
    return rows


def fetch_price_by_rank(key: str, start_year: int, sleep_s: float) -> list[dict]:
    """Return ``[{year, region_id, region_name, coal_rank_id,
    coal_rank_name, price_usd_per_ton}]`` for every producing region and coal
    rank (bituminous/subbituminous/lignite/anthracite/all) from
    ``start_year`` on."""
    data = _get_all(
        PRICE_BY_RANK_ROUTE,
        {"frequency": "annual", "data[0]": "price", "start": str(start_year)},
        key,
        sleep_s,
    )
    rows = []
    for r in data:
        price = r.get("price")
        if price in _WITHHELD:
            continue
        rows.append(
            {
                "year": int(r["period"]),
                "region_id": r["stateRegionId"],
                "region_name": r["stateRegionDescription"],
                "coal_rank_id": r["coalRankId"],
                "coal_rank_name": r["coalRankDescription"],
                "price_usd_per_ton": round(float(price), 4),
            }
        )
    rows.sort(key=lambda r: (r["year"], r["region_id"], r["coal_rank_id"]))
    return rows


def _write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--start-year",
        type=int,
        default=2001,
        help="earliest ACR year to pull (API coverage starts 2001)",
    )
    ap.add_argument("--sleep", type=float, default=0.5)
    args = ap.parse_args()

    key = os.environ.get("EIA_API_KEY")
    if not key and (REPO / ".env").exists():
        for line in (REPO / ".env").read_text().splitlines():
            if line.startswith("EIA_API_KEY="):
                key = line.split("=", 1)[1].strip()
    if not key:
        print(
            "ERROR: set EIA_API_KEY (free: https://www.eia.gov/opendata/register.php)",
            file=sys.stderr,
        )
        sys.exit(1)

    print("=== coal/market-sales-price (region x market-type, all ranks) ===")
    market_rows = fetch_market_sales_price(key, args.start_year, args.sleep)
    _write_csv(
        MARKET_SALES_OUT,
        [
            "year",
            "region_id",
            "region_name",
            "market_type_id",
            "market_type_name",
            "price_usd_per_ton",
            "sales_short_tons",
        ],
        market_rows,
    )
    print(f"  wrote {len(market_rows)} rows -> {MARKET_SALES_OUT}")

    print("=== coal/price-by-rank (region x coal rank) ===")
    rank_rows = fetch_price_by_rank(key, args.start_year, args.sleep)
    _write_csv(
        PRICE_BY_RANK_OUT,
        [
            "year",
            "region_id",
            "region_name",
            "coal_rank_id",
            "coal_rank_name",
            "price_usd_per_ton",
        ],
        rank_rows,
    )
    print(f"  wrote {len(rank_rows)} rows -> {PRICE_BY_RANK_OUT}")


if __name__ == "__main__":
    main()
