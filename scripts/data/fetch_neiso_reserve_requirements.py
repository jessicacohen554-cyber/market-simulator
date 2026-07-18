"""Download ISO-NE's public Hourly Reserve Requirements report (ISO Express).

The measured as-enforced reserve-requirement series for the NEISO winter
scarcity charter (Limb A): ISO-NE publishes, per hour and reserve location,
the Ten-Minute Spinning / Ten-Minute (total) / TOTAL (30-minute) reserve
requirement MW actually enforced in real time — the exact ISO-NE analogue of
the NYISO issue-#1344 Ask-B intake. Source report: ISO Express > Operations
Reports > "Hourly Reserve Requirements"
(https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/ancillary-hourly-rr),
whose CSV export endpoint is

    https://www.iso-ne.com/transform/csv/hourlyrequirements?start=YYYYMMDD&end=YYYYMMDD

This is a rule-13-admissible measured market-design INPUT (the requirement
ISO-NE schedules from its published criteria — largest contingency, cold
weather / gas contingencies — which regenerates for a forward year from
forward states and responds to changed conditions). Measured reserve PRICES
are the validation target and are never fetched here.

Layout produced (window CSVs are gitignored — the NYISO-archive push-limit
precedent; this committed downloader regenerates them):

    data/raw/NEISO-AS/requirements/requirements_<start>_<end>.csv

Windowing is fixed and year-scoped so regeneration is reproducible: within
each calendar year, consecutive 15-day windows starting Jan 1, the last
truncated at Dec 31 (25 windows/year; 75 files for 2023-2025).

The endpoint 403s without an ``isox_token`` session cookie; the script
bootstraps one by fetching the public report page first.

Usage:
    python scripts/data/fetch_neiso_reserve_requirements.py            # 2023-2025
    python scripts/data/fetch_neiso_reserve_requirements.py --years 2024
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "NEISO-AS" / "requirements"

REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/"
    "ancillary-hourly-rr"
)
CSV_ENDPOINT = "https://www.iso-ne.com/transform/csv/hourlyrequirements"

#: Fixed window length (days). 15-day year-scoped windows keep each file
#: comfortably under the endpoint's response limits and make the on-disk
#: layout reproducible (25 windows per calendar year).
WINDOW_DAYS = 15

#: Train years only (CLAUDE.md rule 22): no out-of-training intake without
#: explicit owner authorization.
DEFAULT_YEARS = (2023, 2024, 2025)

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def year_windows(year: int) -> list[tuple[dt.date, dt.date]]:
    """Return the fixed (start, end) 15-day windows covering ``year``."""
    windows = []
    start = dt.date(year, 1, 1)
    year_end = dt.date(year, 12, 31)
    while start <= year_end:
        end = min(start + dt.timedelta(days=WINDOW_DAYS - 1), year_end)
        windows.append((start, end))
        start = end + dt.timedelta(days=1)
    return windows


def _opener() -> urllib.request.OpenerDirector:
    """Build a cookie-carrying opener and bootstrap the isox_token session."""
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", _UA)]
    with opener.open(REPORT_PAGE, timeout=60) as resp:
        resp.read()
    if not any(c.name == "isox_token" for c in jar):
        raise RuntimeError(
            "ISO Express session bootstrap failed: no isox_token cookie from "
            f"{REPORT_PAGE}"
        )
    return opener


def fetch_window(
    opener: urllib.request.OpenerDirector, start: dt.date, end: dt.date
) -> bytes:
    """Fetch one window's CSV bytes, validating the report preamble."""
    url = f"{CSV_ENDPOINT}?start={start:%Y%m%d}&end={end:%Y%m%d}"
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    with opener.open(req, timeout=120) as resp:
        body = resp.read()
    if not body.startswith(b"C,Hourly Reserve Requirements"):
        raise RuntimeError(f"unexpected response (not the report CSV) from {url}")
    return body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=list(DEFAULT_YEARS),
        help="calendar years to download (default: 2023 2024 2025)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-download windows whose file already exists",
    )
    args = parser.parse_args(argv)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    n_new = n_skip = 0
    for year in args.years:
        for start, end in year_windows(year):
            dest = RAW_DIR / f"requirements_{start:%Y%m%d}_{end:%Y%m%d}.csv"
            if dest.exists() and not args.force:
                n_skip += 1
                continue
            body = fetch_window(opener, start, end)
            dest.write_bytes(body)
            n_new += 1
            print(f"fetched {dest.name} ({len(body)} bytes)")
            time.sleep(1.0)  # be polite to the public endpoint
    print(f"done: {n_new} fetched, {n_skip} already present -> {RAW_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
