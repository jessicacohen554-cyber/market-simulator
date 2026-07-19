"""Fetch PJM energy market generation offers from the DataMiner2 REST API.

Downloads the ``energy_market_offers`` feed from PJM's public REST API
(https://api.pjm.com/api/v1) for each requested year (default 2023–2025)
and saves one compressed Parquet file per calendar month to
``data/raw/pjm-energy-offers/pjm_energy_offers_YYYY_MM.parquet``.

The raw files are gitignored (3-year corpus ≈ 1–2 GB compressed at
~29 000 rows/day × 365 days); they are the immutable source inputs for
``scripts/data/curate_energy_offers.py``, which produces the schema-validated
``data/clean/energy-offers/PJM/`` long-format tree.

Usage
-----
    python scripts/data/fetch_pjm_energy_offers.py               # 2023–2025, all months
    python scripts/data/fetch_pjm_energy_offers.py --years 2024
    python scripts/data/fetch_pjm_energy_offers.py --years 2023 2024 --months 1 2 3
    python scripts/data/fetch_pjm_energy_offers.py --force        # re-download existing files

DataMiner2 REST API notes
--------------------------
- Base URL:     ``https://api.pjm.com/api/v1``
- Auth header:  ``Ocp-Apim-Subscription-Key`` (public key in the site's
  settings.json — ``6a75d9f6d933401dbb4f36f8e70b95b3``).
- Date filter:  ``bid_datetime_beginning_ept=YYYY-MM-DDThh:mm:ss.0 to YYYY-MM-DDThh:mm:ss.0``
  (EPT local time, ISO-8601 with millisecond precision).
- Pagination:   ``startRow`` (1-indexed) + ``rowCount`` rows per page.
  The JSON response includes ``totalRows``; the CSV response stops when
  fewer than ``rowCount`` rows arrive.
- Format:       ``format=csv`` returns UTF-8 CSV with a BOM.
- Rate limit:   ``--sleep`` (default 1.5 s) between pages; ``--retry``
  (default 4) retries with exponential back-off on 429/503.
- Data delay:   results are posted monthly, four months in arrears.
  2023–2025 data is fully available as of mid-2026.
- Retention:    indefinite (available from 2017-11-01 onward).

Wide raw format (as stored on disk)
--------------------------------------
One row per (unit_code × operating-hour).  Columns:

  bid_datetime_beginning_utc, bid_datetime_beginning_ept, unit_code,
  bid_slope_flag, mw1..mw20, bid1..bid20,
  no_load_cost, cold_start_cost, inter_start_cost, hot_start_cost,
  max_daily_starts, min_runtime,
  max_ecomax, min_ecomax, avg_ecomax, max_ecomin, min_ecomin, avg_ecomin

The curate script pivots these to long (step) format.
"""

from __future__ import annotations

import argparse
import calendar
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Repo path bootstrap
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402
from scripts.lib import pjm_dataminer  # noqa: E402

OUT_DIR = paths.PJM_ENERGY_OFFERS_DIR

# The DataMiner2 feed and this fetcher's User-Agent; the API base / public
# subscription key / page size live in scripts.lib.pjm_dataminer.
FEED = "energy_market_offers"
USER_AGENT = "market-sim/fetch_pjm_energy_offers"


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _date_filter(year: int, month: int) -> str:
    """Return the ``bid_datetime_beginning_ept`` filter string for one calendar month.

    DataMiner2 expects ISO-8601 with 7 decimal places:
    ``YYYY-MM-DDThh:mm:ss.0000000 to YYYY-MM-DDThh:mm:ss.0000000``
    using EPT (Eastern Prevailing Time) local timestamps.
    """
    last_day = calendar.monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01T00:00:00.0000000"
    end = f"{year:04d}-{month:02d}-{last_day:02d}T23:59:59.0000000"
    return f"{start} to {end}"


def _fetch_month(
    year: int, month: int, *, sleep_s: float = 1.5, retries: int = 4
) -> pd.DataFrame:
    """Download all pages for one calendar month; return a concatenated DataFrame."""
    params = {
        "isActiveMetadata": "true",
        "sort": "bid_datetime_beginning_ept",
        "order": "Asc",
        "format": "csv",
        "bid_datetime_beginning_ept": _date_filter(year, month),
    }
    rows = pjm_dataminer.fetch_feed(
        FEED, params, user_agent=USER_AGENT, sleep_s=sleep_s, retries=retries
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ---------------------------------------------------------------------------
# Minimal type coercions for efficient Parquet storage
# ---------------------------------------------------------------------------

_FLOAT_COLS = (
    "mw1",
    "mw2",
    "mw3",
    "mw4",
    "mw5",
    "mw6",
    "mw7",
    "mw8",
    "mw9",
    "mw10",
    "mw11",
    "mw12",
    "mw13",
    "mw14",
    "mw15",
    "mw16",
    "mw17",
    "mw18",
    "mw19",
    "mw20",
    "bid1",
    "bid2",
    "bid3",
    "bid4",
    "bid5",
    "bid6",
    "bid7",
    "bid8",
    "bid9",
    "bid10",
    "bid11",
    "bid12",
    "bid13",
    "bid14",
    "bid15",
    "bid16",
    "bid17",
    "bid18",
    "bid19",
    "bid20",
    "no_load_cost",
    "cold_start_cost",
    "inter_start_cost",
    "hot_start_cost",
    "max_daily_starts",
    "min_runtime",
    "max_ecomax",
    "min_ecomax",
    "avg_ecomax",
    "max_ecomin",
    "min_ecomin",
    "avg_ecomin",
)


def _coerce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce raw CSV strings to typed columns for efficient Parquet encoding."""
    # Lowercase column names (API is case-inconsistent across versions).
    df.columns = [c.strip().lower() for c in df.columns]

    for col in _FLOAT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "bid_slope_flag" in df.columns:
        df["bid_slope_flag"] = df["bid_slope_flag"].map(
            {"True": True, "False": False, "true": True, "false": False}
        )

    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Parse arguments, iterate year × month, fetch and save raw Parquet."""
    ap = argparse.ArgumentParser(
        description="Fetch PJM energy market offers from DataMiner2 REST API"
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="Calendar years to fetch (default: 2023 2024 2025)",
    )
    ap.add_argument(
        "--months",
        nargs="+",
        type=int,
        default=list(range(1, 13)),
        help="Months to fetch (1–12, default all)",
    )
    ap.add_argument(
        "--sleep",
        type=float,
        default=1.5,
        help="Seconds to sleep between API pages (default 1.5)",
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=4,
        help="Retries on HTTP 429/503 (default 4, exponential back-off)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Re-download and overwrite files that already exist",
    )
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for year in sorted(args.years):
        for month in sorted(args.months):
            out_path = OUT_DIR / f"pjm_energy_offers_{year:04d}_{month:02d}.parquet"

            if out_path.exists() and not args.force:
                print(
                    f"[{year}-{month:02d}] already exists, skipping ({out_path.name})"
                )
                continue

            print(f"[{year}-{month:02d}] fetching …")
            try:
                df = _fetch_month(year, month, sleep_s=args.sleep, retries=args.retries)
            except Exception as exc:
                print(f"  ERROR: {exc}")
                continue

            if df.empty:
                print(f"  no data returned for {year}-{month:02d}")
                continue

            df = _coerce_dtypes(df)
            df.to_parquet(out_path, index=False, compression="snappy")
            mb = out_path.stat().st_size / 1_048_576
            print(f"  saved {len(df):,} rows → {out_path.name} ({mb:.1f} MB)")


if __name__ == "__main__":
    main()
