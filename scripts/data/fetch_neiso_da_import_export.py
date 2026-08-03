"""Download ISO-NE's public Day-Ahead SUBMITTED import-offer / export-bid book.

The external-transaction analogue of ``fetch_neiso_da_energy_offers.py``.
ISO Express publishes, per operating day, every DA import offer and export
bid submitted at an external interface (masked customer / masked origin and
destination location, direction, transaction type, price, MW).  Source: ISO
Express *Real-Time and Day-Ahead Import Offer and Export Bid Data*, the
static historical-report tree

    https://www.iso-ne.com/static-transform/csv/histRpts/da-import-export/hbdayaheadimpexp_<YYYYMMDD>.csv

(one operating day per file, ~0.35 MB; published on the first day of the
fourth month following the operating month, per the FERC-ordered lag).

WHY THIS CORPUS EXISTS (neiso-79).  ISO-NE publishes **no** day-ahead cleared
external-transaction or day-ahead net-interchange series anywhere on ISO
Express — every interchange report on the Grid tree is real-time/actual
scheduled interchange, and the only day-ahead external data the ISO makes
public is this SUBMITTED book.  That absence is what this corpus answers: the
neiso-76 §D stack traversal needed "cleared demand net of scheduled imports",
and with the priced import book in hand the import depth is *cleared
endogenously by the crossing itself* instead of being assumed at a flat 3 GW
(the neiso-76 depth sensitivity).  A priced supply book is a strictly better
input here than a cleared quantity would have been.

Row semantics, identified from the file (not assumed):

===============  ==========================================================
Direction        ``IMPORT`` (supply into the control area) / ``EXPORT``
                 (demand leaving it)
Transaction Type ``DISPATCHABLE`` — priced, clears against the LMP;
                 ``FIXED`` — self-scheduled, price-insensitive, blank Price
Price / Bid MW   the (price, MW) offer or bid; one row per hour per
                 transaction, MW are per-hour block widths
===============  ==========================================================

Layout produced (daily CSVs are gitignored -- the NYISO-archive push-limit
precedent; this committed downloader regenerates them):

    data/raw/NEISO-AS/da-import-export/hbdayaheadimpexp_<YYYYMMDD>.csv

Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22).

Rule 13: these are a measured *market input* on the offer/bid side and are
read only by probes.  Nothing derived from them is armed in any solve, and no
``data/`` loader or derive reads this directory.

Usage:
    python scripts/data/fetch_neiso_da_import_export.py            # 2023-2025
    python scripts/data/fetch_neiso_da_import_export.py --years 2025
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import NEISO_AS_DIR  # noqa: E402

from scripts.data.fetch_neiso_da_energy_offers import _opener  # noqa: E402

RAW_DIR = NEISO_AS_DIR / "da-import-export"

REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/pricing/-/tree/import-export-data"
)
CSV_BASE = (
    "https://www.iso-ne.com/static-transform/csv/histRpts/da-import-export/"
    "hbdayaheadimpexp_%s.csv"
)

#: Train years only (CLAUDE.md rule 22).
DEFAULT_YEARS = (2023, 2024, 2025)

#: The endpoint answers a missing/unpublished operating day either with a stub
#: body (~31 bytes) or with a bare 404 -- the same publication-gap pattern the
#: sibling ``da-energy-offers`` and ``da-demand-bids`` READMEs document.  A 404
#: here is an ABSENT DAY, not a transport failure: it is recorded and skipped
#: without the session refresh a real error triggers.
MIN_REAL_BYTES = 5_000


class DayNotPublished(Exception):
    """The operating day is absent from the static historical-report tree."""


def fetch_day(opener: urllib.request.OpenerDirector, day: dt.date) -> bytes:
    """Fetch one operating day's import/export CSV, validating the preamble.

    Raises:
        DayNotPublished: the report tree has no file for this operating day.
    """
    url = CSV_BASE % f"{day:%Y%m%d}"
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    try:
        with opener.open(req, timeout=180) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise DayNotPublished(f"{day:%Y-%m-%d}") from None
        raise
    if len(body) >= MIN_REAL_BYTES and b"Import and Export" not in body[:200]:
        raise RuntimeError(f"unexpected response (not the impexp CSV) from {url}")
    return body


def main(argv: list[str] | None = None) -> int:
    """Download the DA import-offer/export-bid corpus for the requested years."""
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
    args = parser.parse_args(argv)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    n_new = n_skip = n_err = n_empty = n_absent = 0
    for year in args.years:
        day = dt.date(year, 1, 1)
        while day.year == year:
            dest = RAW_DIR / f"hbdayaheadimpexp_{day:%Y%m%d}.csv"
            if dest.exists() and not args.force:
                n_skip += 1
            else:
                try:
                    body = fetch_day(opener, day)
                except DayNotPublished:  # a source gap, not a failure
                    n_absent += 1
                    day += dt.timedelta(days=1)
                    continue
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
        f"done: {n_new} fetched ({n_empty} empty postings), {n_skip} present, "
        f"{n_absent} not published (404), {n_err} errors -> {RAW_DIR}"
    )
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
