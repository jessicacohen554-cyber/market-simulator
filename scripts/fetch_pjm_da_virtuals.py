"""Fetch PJM Day-Ahead virtual bid curves + demand bids from DataMiner2.

Downloads the two DA demand-side bid feeds behind the G-22 lever-B
DA-procurement-depth mechanism (docs/FINDING-pjm-offer-surface-noop-2026-07.md
§Re-scoped levers):

* ``hrl_da_incs_decs`` — hourly INCrement offer (virtual supply) and
  DECrement bid (virtual demand) curves, RTO-aggregated by price point.
  These are SUBMITTED ex-ante bid curves — participant inputs like
  generator energy offers, never cleared outcomes — so clearing stays
  endogenous to the LP (CLAUDE.md rule 13).
* ``hrl_dmd_bids`` — hourly total day-ahead demand bid MW by area
  (PJM_RTO / MID_ATLANTIC_REGION / WESTERN_REGION), used as a cross-check
  of the physical demand-bid base.

One compressed Parquet per feed per calendar month is written to
``data/raw/pjm-da-virtuals/`` (gitignored; PJM DataMiner2 non-member
redistribution restriction — see docs/data-licensing.md §4 and the
pjm-energy-offers precedent).

Usage
-----
    python scripts/fetch_pjm_da_virtuals.py                # 2023-2025, all months
    python scripts/fetch_pjm_da_virtuals.py --years 2024
    python scripts/fetch_pjm_da_virtuals.py --feeds hrl_da_incs_decs
    python scripts/fetch_pjm_da_virtuals.py --force        # re-download existing

API notes are shared with ``scripts/fetch_pjm_energy_offers.py`` (same
DataMiner2 REST API, public subscription key, pagination and back-off).
``hrl_da_incs_decs`` filters on ``bid_datetime_beginning_ept``;
``hrl_dmd_bids`` filters on ``datetime_beginning_ept``.
"""

from __future__ import annotations

import argparse
import calendar
import csv
import io
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402

OUT_DIR = paths.PJM_DA_VIRTUALS_DIR

API_BASE = "https://api.pjm.com/api/v1"
# Public key embedded in DataMiner2's own settings.json (see
# fetch_pjm_energy_offers.py).
SUB_KEY = "6a75d9f6d933401dbb4f36f8e70b95b3"
PAGE_SIZE = 50_000

#: feed name -> (datetime filter/sort field, float columns)
FEEDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "hrl_da_incs_decs": (
        "bid_datetime_beginning_ept",
        ("price_point", "inc_mw", "dec_mw"),
    ),
    "hrl_dmd_bids": ("datetime_beginning_ept", ("hrly_da_demand_bid",)),
}


def _date_filter(year: int, month: int) -> str:
    """EPT month-window filter string (ISO-8601, DataMiner2 convention)."""
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01T00:00:00.0000000"
    end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59.0000000"
    return f"{start} to {end}"


def _build_url(feed: str, ts_field: str, year: int, month: int, start_row: int) -> str:
    """Compose the DataMiner2 CSV export URL for one page of one month."""
    params = {
        "startRow": str(start_row),
        "rowCount": str(PAGE_SIZE),
        "isActiveMetadata": "true",
        "sort": ts_field,
        "order": "Asc",
        "format": "csv",
        ts_field: _date_filter(year, month),
    }
    return f"{API_BASE}/{feed}?" + urllib.parse.urlencode(params)


def _fetch_page(url: str, *, retries: int = 4, sleep_s: float = 1.5) -> list[dict]:
    """Fetch one CSV page with 429/503 exponential back-off."""
    delay = sleep_s
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Ocp-Apim-Subscription-Key": SUB_KEY,
                    "Accept": "text/csv",
                    "User-Agent": "market-sim/fetch_pjm_da_virtuals",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8-sig", errors="replace")
            return list(csv.DictReader(io.StringIO(raw)))
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 503) and attempt < retries:
                print(f"    HTTP {exc.code} — back-off {delay:.0f}s …")
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < retries:
                print(f"    network error ({exc}) — back-off {delay:.0f}s …")
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return []


def _fetch_month(
    feed: str, ts_field: str, year: int, month: int, *, sleep_s: float = 1.5
) -> pd.DataFrame:
    """Download all pages for one feed-month; return a concatenated frame."""
    all_rows: list[dict] = []
    start_row, page = 1, 1
    while True:
        url = _build_url(feed, ts_field, year, month, start_row)
        print(f"  page {page:3d}  startRow={start_row:>8d} … ", end="", flush=True)
        rows = _fetch_page(url, sleep_s=sleep_s)
        print(f"{len(rows):>6d} rows")
        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break
        start_row += PAGE_SIZE
        page += 1
        time.sleep(sleep_s)
    return pd.DataFrame(all_rows)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--months", nargs="*", type=int, default=list(range(1, 13)))
    ap.add_argument("--feeds", nargs="*", choices=sorted(FEEDS), default=sorted(FEEDS))
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    ap.add_argument("--sleep", type=float, default=1.5)
    args = ap.parse_args(argv)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for feed in args.feeds:
        ts_field, float_cols = FEEDS[feed]
        for year in args.years:
            for month in args.months:
                out = OUT_DIR / f"{feed}_{year:04d}_{month:02d}.parquet"
                if out.exists() and not args.force:
                    print(f"[skip] {out.name} exists")
                    continue
                print(f"[{feed} {year}-{month:02d}]")
                df = _fetch_month(feed, ts_field, year, month, sleep_s=args.sleep)
                if df.empty:
                    print(f"  !! no rows for {year}-{month:02d}; not writing")
                    continue
                for c in float_cols:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce")
                df.to_parquet(out, compression="zstd", index=False)
                print(f"  wrote {out.name} ({len(df)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
