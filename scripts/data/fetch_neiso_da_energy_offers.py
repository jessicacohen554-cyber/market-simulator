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
    python scripts/data/fetch_neiso_da_energy_offers.py            # 2023-2025
    python scripts/data/fetch_neiso_da_energy_offers.py --years 2025
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import NEISO_AS_DIR  # noqa: E402

RAW_DIR = NEISO_AS_DIR / "da-energy-offers"

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


#: Concurrent workers.  The ISO Express endpoint is per-connection
#: LATENCY-bound, not bandwidth-bound: measured 2026-08-03 on fresh
#: (uncached) operating days, one worker sustains ~6.7 files/min while five
#: sustain ~80 files/min at ~2 MB/s, and eight adds nothing over four -- so the
#: pool saturates the pipe well before it stresses the endpoint.  Kept modest
#: for exactly that reason.
DEFAULT_WORKERS = 5


def fetch_days_concurrent(
    days: list[dt.date],
    dest_for,
    fetch_one,
    *,
    workers: int = DEFAULT_WORKERS,
    min_real_bytes: int = 5_000,
    label: str = "days",
) -> tuple[int, int, int]:
    """Download ``days`` through a small pool of independent ISO Express sessions.

    Shared by the three NEISO day-ahead corpus fetchers.  Each worker holds its
    own cookie-bootstrapped opener (the sessions are not thread-safe to share),
    and a failure on one day is logged and skipped rather than aborting the
    run.

    Args:
        days: operating days to fetch.
        dest_for: ``day -> Path`` for the file to write.
        fetch_one: ``(opener, day) -> bytes``; may raise to signal a source gap.
        workers: size of the session pool.
        min_real_bytes: bodies below this are counted as empty postings.
        label: noun used in progress lines.

    Returns:
        ``(n_written, n_empty, n_error)``.
    """
    import concurrent.futures as cf
    import threading

    local = threading.local()
    lock = threading.Lock()
    state = {"done": 0, "empty": 0, "err": 0}

    def worker(day: dt.date) -> None:
        if getattr(local, "opener", None) is None:
            local.opener = _opener()
        try:
            body = fetch_one(local.opener, day)
        except Exception as e:
            with lock:
                state["err"] += 1
                print(f"ERROR {day}: {e}", flush=True)
            local.opener = None  # force a fresh session for this worker
            return
        dest_for(day).write_bytes(body)
        with lock:
            state["done"] += 1
            if len(body) < min_real_bytes:
                state["empty"] += 1
            if state["done"] % 50 == 0:
                print(f"fetched {state['done']} {label} (at {day})", flush=True)

    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(worker, days))
    return state["done"], state["empty"], state["err"]


def fetch_day(opener: urllib.request.OpenerDirector, day: dt.date) -> bytes:
    """Fetch one operating day's offer CSV, validating the report preamble."""
    url = f"{CSV_ENDPOINT}?start={day:%Y%m%d}"
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    with opener.open(req, timeout=180) as resp:
        body = resp.read()
    if b"Day-Ahead Energy Market Historical Offer Report" not in body[:200]:
        raise RuntimeError(f"unexpected response (not the offer CSV) from {url}")
    return body


def _dest_for(day: dt.date) -> Path:
    """Destination path for one operating day's offer CSV."""
    return RAW_DIR / f"hbdayaheadenergyoffer_{day:%Y%m%d}.csv"


def main(argv: list[str] | None = None) -> int:
    """Download the DA energy-offer corpus for the requested years."""
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
        "--workers",
        type=int,
        default=DEFAULT_WORKERS,
        help=f"concurrent ISO Express sessions (default: {DEFAULT_WORKERS})",
    )
    args = parser.parse_args(argv)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    todo, n_skip = [], 0
    for year in args.years:
        day = dt.date(year, 1, 1)
        while day.year == year:
            if _dest_for(day).exists() and not args.force:
                n_skip += 1
            else:
                todo.append(day)
            day += dt.timedelta(days=1)

    n_new, _, n_err = fetch_days_concurrent(
        todo, _dest_for, fetch_day, workers=args.workers
    )
    print(f"done: {n_new} fetched, {n_skip} present, {n_err} errors -> {RAW_DIR}")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
