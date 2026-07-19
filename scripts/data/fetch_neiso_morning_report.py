"""Download ISO-NE's public Morning Report (Operable Capacity Analysis).

The measured daily generation-outage / operable-capacity series for NEISO — the
ISO-NE analogue of the ERCOT 60-Day DAM measured class-day thermal availability
(``data/raw/ercot-thermal-dam-availability.csv``,
``derive_ercot_thermal_dam_availability.py``). ISO-NE publishes, each morning, a
peak-hour "Operable Capacity Analysis" whose Section 3 reports, in MW, the day's

    * Generation Outages and Reductions (Planned + Forced)   -- outages
    * Capacity Supply Obligation (CSO) + EcoMax-above-CSO     -- operable base
    * Total Available Capacity                                -- available fleet

i.e. exactly the "outages and capacity availability" the ERCOT DAM disclosure
gives per class, but at ISO-NE fleet grain (ISO-NE does not publish per-unit or
per-fuel availability — masked-asset offer data only). Source report:
ISO Express > Operations Reports > "Morning Report"
(https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/morning-report),
whose public CSV export endpoint is

    https://www.iso-ne.com/transform/csv/morningreport?start=YYYYMMDD

(one operating day per file, ~2.5 kB). This is a rule-13-admissible measured
availability INPUT: a physical generator-outage / operable-capacity quantity
(planned maintenance + forced outages) that regenerates for a forward year from
forward drivers and responds to changed conditions — never a price and never an
outcome fitted to a residual (CLAUDE.md rules 13/14; the ERCOT DAM-availability
admissibility argument, applied at fleet grain). The measured PRICES ISO-NE
publishes are the validation target and are never fetched here.

Coverage: the archive begins 2018-07-01 (2018 H1 returns an empty placeholder)
and runs to the present. The full requested span is therefore 2018-07-01 →
today. Out-of-training years (< 2023, > 2025) are downloaded only under the
explicit session-logged owner authorization required by CLAUDE.md rule 22; the
intake is data-only (no LP solve, no scoring).

Layout produced (daily CSVs are gitignored -- the NEISO/NYISO-archive
push-limit precedent; this committed downloader regenerates them, and
``build_neiso_operable_capacity.py`` parses them into the committed parquet):

    data/raw/neiso-operable-capacity/daily/morning_report_<YYYYMMDD>.csv

The endpoint 403s without an ``isox_token`` session cookie; the script
bootstraps one by fetching a public ISO Express report page first (the same
bootstrap ``fetch_neiso_reserve_requirements.py`` /
``fetch_neiso_da_energy_offers.py`` use).

Usage:
    python scripts/data/fetch_neiso_morning_report.py                 # full archive
    python scripts/data/fetch_neiso_morning_report.py --years 2024 2025
    python scripts/data/fetch_neiso_morning_report.py --start 2018-07-01 --end 2026-07-19
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
RAW_DIR = REPO_ROOT / "data" / "raw" / "neiso-operable-capacity" / "daily"

#: Any ISO Express report page mints an isox_token; use the ancillary tree the
#: sibling ISO-NE downloaders bootstrap from (stable, small).
REPORT_PAGE = (
    "https://www.iso-ne.com/isoexpress/web/reports/operations/-/tree/"
    "ancillary-hourly-rr"
)
CSV_ENDPOINT = "https://www.iso-ne.com/transform/csv/morningreport"

#: First operating day the archive publishes a populated report (2018 H1 is an
#: empty placeholder). Verified 2026-07-19 by a month-by-month coverage sweep.
ARCHIVE_START = dt.date(2018, 7, 1)

#: Below this the response is the ~161-byte empty placeholder, not a report.
_MIN_REPORT_BYTES = 500

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
            "ISO Express session bootstrap failed: no isox_token cookie from "
            f"{REPORT_PAGE}"
        )
    return opener


def fetch_day(opener: urllib.request.OpenerDirector, day: dt.date) -> bytes | None:
    """Fetch one day's Morning Report CSV bytes.

    Returns ``None`` for days the archive has no populated report (the empty
    placeholder), and validates the report preamble otherwise so a silent HTML
    error page never lands on disk as a CSV.
    """
    url = f"{CSV_ENDPOINT}?start={day:%Y%m%d}"
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    with opener.open(req, timeout=120) as resp:
        body = resp.read()
    if len(body) < _MIN_REPORT_BYTES:
        return None
    # Validate on the Section-3 header we actually parse, not the report title:
    # ISO-NE renamed the title "Morning Report" -> "Operational Capacity Update
    # Report" at the mid-2025 format change, but "Operable Capacity Analysis" is
    # the stable marker across both epochs (and confirms the file is parseable).
    if b"Operable Capacity Analysis" not in body:
        raise RuntimeError(
            f"unexpected response (not the operable-capacity CSV) from {url}"
        )
    return body


def _daterange(start: dt.date, end: dt.date):
    day = start
    while day <= end:
        yield day
        day += dt.timedelta(days=1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=None,
        help="calendar years to download (default: full archive from 2018-07-01)",
    )
    parser.add_argument("--start", type=str, default=None, help="YYYY-MM-DD start")
    parser.add_argument("--end", type=str, default=None, help="YYYY-MM-DD end")
    parser.add_argument(
        "--force", action="store_true", help="re-download existing days"
    )
    args = parser.parse_args(argv)

    if args.years:
        start = dt.date(min(args.years), 1, 1)
        end = dt.date(max(args.years), 12, 31)
    else:
        start = dt.date.fromisoformat(args.start) if args.start else ARCHIVE_START
        end = dt.date.fromisoformat(args.end) if args.end else dt.date.today()
    start = max(start, ARCHIVE_START)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    opener = _opener()
    n_new = n_skip = n_empty = n_err = 0
    for i, day in enumerate(_daterange(start, end)):
        dest = RAW_DIR / f"morning_report_{day:%Y%m%d}.csv"
        if dest.exists() and not args.force:
            n_skip += 1
            continue
        try:
            body = fetch_day(opener, day)
        except Exception as e:  # transient endpoint hiccups: log, refresh, go on
            print(f"ERROR {day}: {e}", flush=True)
            n_err += 1
            time.sleep(3.0)
            opener = _opener()  # refresh the session
            continue
        if body is None:
            n_empty += 1
        else:
            dest.write_bytes(body)
            n_new += 1
        if i % 200 == 0 and i:
            print(
                f"  ... {day} (new={n_new} skip={n_skip} empty={n_empty} err={n_err})",
                flush=True,
            )
            opener = _opener()  # periodic session refresh over a long pull
        time.sleep(0.15)
    print(
        f"done: {n_new} downloaded, {n_skip} skipped, {n_empty} empty-days, "
        f"{n_err} errors -> {RAW_DIR}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
