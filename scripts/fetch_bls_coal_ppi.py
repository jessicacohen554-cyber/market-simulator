#!/usr/bin/env python3
"""Fetch BLS Producer Price Index series for coal, as a slope/elasticity
cross-check on the EIA Annual Coal Report region prices (see
``fetch_eia_coal_prices.py``).

Two national monthly PPI series, both free/public-domain (U.S. Government
Work), both from the BLS Public Data API v2 (no registration key required for
the free tier — https://www.bls.gov/developers/):

  * ``WPU051`` — PPI commodity "Coal" (all coal, national). ``WPU0513`` (a
    narrower BLS code under the same commodity group) returns byte-identical
    values over 2015-2024 on inspection, so only ``WPU051`` is kept.
  * ``PCU2121--2121--`` — PPI industry "Coal Mining" (NAICS 2121, national
    output price index — a distinct index from the commodity series, useful
    as an independent cross-check).

BLS does **not** publish a coal PPI broken out by producing region/basin —
the commodity and industry PPI programs are national-only (confirmed by
probing candidate regional/rank BLS series ids; none resolve). This is
recorded as a known gap in the intake memo; the region-level ask is served by
the EIA ACR f.o.b.-mine prices instead (``fetch_eia_coal_prices.py``).

The free (unregistered) BLS API caps a single request to a 10-year span, so
this fetches overlapping 10-year windows and de-duplicates by (year, month).

Output (raw, immutable, never hand-edited):
  data/raw/coal-prices/bls_coal_ppi.csv
    columns: series_id, series_name, year, month, index_value

BLS API docs: https://www.bls.gov/developers/api_signature_v2.htm

Usage:
    python scripts/fetch_bls_coal_ppi.py
    python scripts/fetch_bls_coal_ppi.py --start-year 2015 --end-year 2026
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parent.parent
OUT_PATH = REPO / "data" / "raw" / "coal-prices" / "bls_coal_ppi.csv"

BASE = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

SERIES: dict[str, str] = {
    "WPU051": "PPI commodity: Coal (all coal, national)",
    "PCU2121--2121--": "PPI industry: Coal Mining (NAICS 2121, national)",
}

# Unregistered BLS API allows at most a 10-year span per request.
_WINDOW_YEARS = 10


def _fetch_window(series_ids: list[str], start_year: int, end_year: int) -> dict:
    body = json.dumps(
        {"seriesid": series_ids, "startyear": str(start_year), "endyear": str(end_year)}
    ).encode()
    req = Request(BASE, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=30) as fh:
            return json.loads(fh.read().decode())
    except (HTTPError, URLError) as exc:
        raise RuntimeError(
            f"BLS request failed ({start_year}-{end_year}): {exc}"
        ) from exc


def fetch_series(series_ids: list[str], start_year: int, end_year: int) -> list[dict]:
    """Return ``[{series_id, series_name, year, month, index_value}]`` across
    ``[start_year, end_year]``, fetched in overlapping <=10-year windows and
    de-duplicated on (series_id, year, month)."""
    by_key: dict[tuple[str, int, int], dict] = {}
    window_start = start_year
    while window_start <= end_year:
        window_end = min(window_start + _WINDOW_YEARS - 1, end_year)
        payload = _fetch_window(series_ids, window_start, window_end)
        if payload.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(f"BLS request failed: {payload.get('message')}")
        for s in payload["Results"]["series"]:
            sid = s["seriesID"]
            for d in s["data"]:
                period = d["period"]
                if not period.startswith("M") or period == "M13":
                    continue  # skip annual-average pseudo-period M13
                year, month = int(d["year"]), int(period[1:])
                by_key[(sid, year, month)] = {
                    "series_id": sid,
                    "series_name": SERIES.get(sid, sid),
                    "year": year,
                    "month": month,
                    "index_value": float(d["value"]),
                }
        window_start = window_end + 1
    rows = sorted(
        by_key.values(), key=lambda r: (r["series_id"], r["year"], r["month"])
    )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start-year", type=int, default=2010)
    ap.add_argument("--end-year", type=int, default=2026)
    args = ap.parse_args()

    rows = fetch_series(list(SERIES), args.start_year, args.end_year)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(
            fh, fieldnames=["series_id", "series_name", "year", "month", "index_value"]
        )
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
