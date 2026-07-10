"""Download ISO-NE's public Day-Ahead Energy Market historical offer data.

The measured OFFER surface for the NEISO winter scarcity charter Limb B
(scarcity-anticipating DA offer formation at healthy reserves — the ERCOT
G-22 analogue): ISO-NE publishes, per operating day and masked asset, every
DA supply offer (up to 10 price/MW blocks, startup/no-load, economic
min/max, must-take) with a ~4-month publication lag. Source: ISO Express
"Day-Ahead Energy Market Historical Offer Report", CSV endpoint

    https://www.iso-ne.com/transform/csv/hbdayaheadenergyoffer?start=YYYYMMDD

(one operating day per file, ~1.3 MB). Masked Lead Participant ID / Masked
Asset ID only — no unit identity. This is a rule-13-admissible measured
market input when used to derive an offer distribution conditioned on a
FORWARD-REPRODUCIBLE tightness driver; it must never be fitted to the price
residual (CLAUDE.md rules 1/13; G-22 §5.1 discipline).

Layout produced (daily CSVs are gitignored — the NYISO-archive push-limit
precedent; this committed downloader regenerates them):

    data/raw/NEISO-AS/da-energy-offers/hbdayaheadenergyoffer_<YYYYMMDD>.csv

Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22).

The endpoint 403s without an ``isox_token`` session cookie; the script
bootstraps one from the public report page.

Usage:
    python scripts/fetch_neiso_da_energy_offers.py            # 2023-2025
    python scripts/fetch_neiso_da_energy_offers.py --years 2025
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import time
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = REPO_ROOT / "data" / "raw" / "NEISO-AS" / "da-energy-offers"

#: Any ISO Express report page works for the isox_token bootstrap; use the
#: DA hourly-offers tree (the report this endpoint backs).
REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/pricing/-/tree/"
    "day-ahead-energy-offer-data"
)
CSV_ENDPOINT = "https://www.iso-ne.com/transform/csv/hbdayaheadenergyoffer"

#: Train years only (CLAUDE.md rule 22).
DEFAULT_YEARS = (2023, 2024, 2025)

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def _opener() -> urllib.request.OpenerDirector:
    """Build a cookie-carrying opener and bootstrap the isox_token session."""
    jar = CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    opener.addheaders = [("User-Agent", _UA)]
    with opener.open(REPORT_PAGE, timeout=60) as resp:
        resp.read()
    if not any(c.name == "isox_token" for c in jar):
        raise RuntimeError(
            f"ISO Express session bootstrap failed: no isox_token from {REPORT_PAGE}"
        )
    return opener


def fetch_day(opener: urllib.request.OpenerDirector, day: dt.date) -> bytes:
    """Fetch one operating day's offer CSV, validating the report preamble."""
    url = f"{CSV_ENDPOINT}?start={day:%Y%m%d}"
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    with opener.open(req, timeout=180) as resp:
        body = resp.read()
    if b"Day-Ahead Energy Market Historical Offer Report" not in body[:200]:
        raise RuntimeError(f"unexpected response (not the offer CSV) from {url}")
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
        "--force", action="store_true", help="re-download existing days"
    )
    args = parser.parse_args(argv)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    n_new = n_skip = n_err = 0
    for year in args.years:
        day = dt.date(year, 1, 1)
        while day.year == year:
            dest = RAW_DIR / f"hbdayaheadenergyoffer_{day:%Y%m%d}.csv"
            if dest.exists() and not args.force:
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
                if n_new % 50 == 0:
                    print(f"fetched {n_new} days (at {day})", flush=True)
                time.sleep(0.5)  # be polite to the public endpoint
            day += dt.timedelta(days=1)
    print(f"done: {n_new} fetched, {n_skip} present, {n_err} errors -> {RAW_DIR}")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
