"""Download ISO-NE's public Day-Ahead SUBMITTED demand-bid book (full corpus).

The demand-side companion to ``fetch_neiso_da_energy_offers.py``.  ISO Express
publishes, per operating day, every DA demand bid and virtual transaction
submitted (masked participant / masked location, Bid Type, up to 50
(price, MW) segments).  Source: ISO Express *Day-Ahead Energy Market Demand
Historical Demand Bid Report*

    https://www.iso-ne.com/transform/csv/hbdayaheaddemandbid?start=YYYYMMDD

(one operating day per file, ~2.3 MB).

=============  ==============================================  ===========
Bid Type       what it is                                      price axis
=============  ==============================================  ===========
``FIXED``      price-insensitive physical demand               none
``PRICE``      price-sensitive physical demand                 yes
``DEC``        virtual load (decrement bid)                    yes
``INC``        virtual supply (increment offer)                yes
=============  ==============================================  ===========

WHY A FULL-CORPUS FETCHER EXISTS (neiso-79).  neiso-76 pulled this book at a
41-day Phase-0 sample (the 15th of every month 2023-2025 plus the five 2025
C3c event days) via ``scripts/probes/_neiso76_demand_limb.py --fetch``, which
was right for a per-hour λ0 error statistic.  The neiso-79 crossing-quantity
reconciliation instead needs an hour-of-day MEAN per year, and 13-14 sample
days a year leaves ~13 observations per (year, hour-of-day) cell -- too thin
to put an hod *range* beside neiso-76 §D's full-corpus traversal anchor.  The
sample is therefore widened deliberately to every published operating day,
which is a ~26x increase and removes sampling as a confound (neiso-79 prereg
§3).  The 41-day probe path still works and is unchanged.

Layout produced (daily CSVs are gitignored -- the NYISO-archive push-limit
precedent; this committed downloader regenerates them):

    data/raw/NEISO-AS/da-demand-bids/hbdayaheaddemandbid_<YYYYMMDD>.csv

Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22).

Rule 13: the bid side is a measured *market input* and the cleared side is the
validation target; both are read only by probes.  Nothing derived from them is
armed in any solve, and no ``data/`` loader or derive reads this directory.

Usage:
    python scripts/data/fetch_neiso_da_demand_bids.py            # 2023-2025
    python scripts/data/fetch_neiso_da_demand_bids.py --years 2025
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import NEISO_AS_DIR  # noqa: E402

from scripts.data.fetch_neiso_da_energy_offers import _opener  # noqa: E402

RAW_DIR = NEISO_AS_DIR / "da-demand-bids"

REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/pricing/-/tree/dmd-bid-data"
)
CSV_ENDPOINT = "https://www.iso-ne.com/transform/csv/hbdayaheaddemandbid"

#: The companion CLEARED series -- *Day-Ahead Energy Market Hourly Demand
#: Report*, one column (``Day-Ahead Cleared Demand``, MWh).  A bare ``?start=``
#: 500s, so it is pulled a calendar month at a time.
CLEARED_ENDPOINT = "https://www.iso-ne.com/transform/csv/hourlydayaheaddemand"

#: Train years only (CLAUDE.md rule 22).
DEFAULT_YEARS = (2023, 2024, 2025)

#: The endpoint answers an unpublished operating day with a header-only body
#: rather than a 404 -- the documented publication-gap pattern shared with the
#: sibling ``da-energy-offers`` and ``da-import-export`` corpora.
MIN_REAL_BYTES = 5_000


def fetch_day(opener: urllib.request.OpenerDirector, day: dt.date) -> bytes:
    """Fetch one operating day's demand-bid CSV, validating the preamble."""
    url = f"{CSV_ENDPOINT}?start={day:%Y%m%d}"
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    with opener.open(req, timeout=300) as resp:
        body = resp.read()
    if len(body) >= MIN_REAL_BYTES and b"Demand Bid" not in body[:200]:
        raise RuntimeError(f"unexpected response (not the demand-bid CSV) from {url}")
    return body


def fetch_cleared(opener: urllib.request.OpenerDirector, years: list[int]) -> int:
    """Download the published DA cleared-demand series, one file per month.

    Returns the number of month files written.  This is the *validation
    target* side of the corpus (rule 13) and the vertical quantity line any
    crossing of the submitted books is read against.
    """
    n = 0
    for year in years:
        for month in range(1, 13):
            start = dt.date(year, month, 1)
            end = (
                dt.date(year + 1, 1, 1) if month == 12 else dt.date(year, month + 1, 1)
            ) - dt.timedelta(days=1)
            dest = RAW_DIR / f"cleared_{start:%Y%m%d}_{end:%Y%m%d}.csv"
            if dest.exists() and dest.stat().st_size > 1_000:
                continue
            url = f"{CLEARED_ENDPOINT}?start={start:%Y%m%d}&end={end:%Y%m%d}"
            req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
            with opener.open(req, timeout=300) as resp:
                dest.write_bytes(resp.read())
            print(
                f"  cleared {year}-{month:02d}: {dest.stat().st_size:,} bytes",
                flush=True,
            )
            n += 1
            time.sleep(0.3)
    return n


def main(argv: list[str] | None = None) -> int:
    """Download the DA submitted demand-bid corpus for the requested years."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=list(DEFAULT_YEARS),
        help="calendar years to download (default: 2023 2024 2025)",
    )
    parser.add_argument(
        "--force", action="store_true", help="re-download existing days"
    )
    parser.add_argument(
        "--cleared-only",
        action="store_true",
        help="fetch only the published cleared-demand month files",
    )
    args = parser.parse_args(argv)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    n_cleared = fetch_cleared(opener, args.years)
    if args.cleared_only:
        print(f"done: {n_cleared} cleared-demand month files -> {RAW_DIR}")
        return 0
    n_new = n_skip = n_err = n_empty = 0
    for year in args.years:
        day = dt.date(year, 1, 1)
        while day.year == year:
            dest = RAW_DIR / f"hbdayaheaddemandbid_{day:%Y%m%d}.csv"
            if (
                dest.exists()
                and dest.stat().st_size > MIN_REAL_BYTES
                and not args.force
            ):
                n_skip += 1
            else:
                try:
                    body = fetch_day(opener, day)
                except Exception as e:  # transient endpoint hiccups: log, go on
                    print(f"ERROR {day}: {e}", flush=True)
                    n_err += 1
                    time.sleep(5.0)
                    opener = _opener()  # refresh the session
                    day += dt.timedelta(days=1)
                    continue
                dest.write_bytes(body)
                n_new += 1
                if len(body) < MIN_REAL_BYTES:
                    n_empty += 1
                if n_new % 50 == 0:
                    print(f"fetched {n_new} days (at {day})", flush=True)
                time.sleep(0.3)  # be polite to the public endpoint
            day += dt.timedelta(days=1)
    print(
        f"done: {n_new} fetched ({n_empty} empty postings), "
        f"{n_skip} present, {n_err} errors -> {RAW_DIR}"
    )
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
