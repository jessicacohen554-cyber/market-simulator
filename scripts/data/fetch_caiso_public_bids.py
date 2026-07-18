"""Download CAISO OASIS DAM Public Bid Data (PUB_BID, ``PUB_DAM_GRP``).

The measured OFFER surface for the CAISO C1 CC-over/CT-under charter (the
Panoche bid wedge and the CT_PEAKER econ rungs — see
``docs/DIAGNOSIS-caiso-evening-merit-c1-c3c-2026-07.md`` §3-4 and
``results/calibration/FINDING-caiso91b-ct-committed-conduct-refuted-2026-07-16.md``):
CAISO publishes, per trade date and masked resource, every DAM bid — the
full piecewise energy bid curve (MW/price breakpoints), self-schedule MW,
and AS product bids — with a 90-day publication lag. Source: CAISO OASIS
GroupZip API, one trade date per request:

    https://oasis.caiso.com/oasisapi/GroupZip
        ?groupid=PUB_DAM_GRP&startdatetime=<YYYYMMDD>T08:00-0000
        &version=3&resultformat=6

(resultformat=6 → CSV inside the zip, ~0.3-0.8 MB compressed per day).
Masked ``SCHEDULINGCOORDINATOR_SEQ`` / ``RESOURCEBID_SEQ`` only — no unit
identity; the masked resource seq is PERSISTENT across days and years
(verified 2026-07-16: 1,160 of 1,278 Jan-10-2024 generator seqs recur on
Jul-10-2024 with median max-MW drift 0.24 MW). This is a rule-13-admissible
measured market input when used to derive an offer distribution normalized
by forward-reproducible drivers (fuel price, carbon price); it must never
be fitted to the price residual (CLAUDE.md rules 1/13/23).

Layout produced (daily zips are gitignored — the pjm-energy-offers
size/precedent; this committed downloader regenerates them):

    data/raw/caiso-public-bids/zips/<YYYYMMDD>_PUB_BID_DAM_v3_csv.zip

Coverage policy: train years 2023-2025 only (CLAUDE.md rule 22).

OASIS rate limit: concurrent/rapid requests return an HTTP-200 HTML page
("CAISO Acceptable Use Policy Violation. Please retry your request after
5 seconds.") instead of a zip — the fetcher sleeps ``--sleep`` (default 6 s)
between requests, detects non-zip bodies by magic bytes, and retries with
exponential backoff.

Usage:
    python scripts/data/fetch_caiso_public_bids.py            # 2023-2025
    python scripts/data/fetch_caiso_public_bids.py --years 2025
    python scripts/data/fetch_caiso_public_bids.py --start 2024-01-01 --end 2024-03-31
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw" / "caiso-public-bids" / "zips"

GROUPZIP_ENDPOINT = "https://oasis.caiso.com/oasisapi/GroupZip"

#: Train years only (CLAUDE.md rule 22).
DEFAULT_YEARS = (2023, 2024, 2025)

#: OASIS acceptable-use policy asks for >=5 s between requests; errors come
#: back as HTTP-200 HTML pages, so politeness is the only reliable throttle.
DEFAULT_SLEEP_S = 6.0

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)


def _day_url(day: dt.date) -> str:
    """GroupZip URL for one DAM trade date (CSV result format)."""
    stamp = day.strftime("%Y%m%d")
    return (
        f"{GROUPZIP_ENDPOINT}?groupid=PUB_DAM_GRP"
        f"&startdatetime={stamp}T08:00-0000&version=3&resultformat=6"
    )


def _out_path(day: dt.date) -> Path:
    return RAW_DIR / f"{day.strftime('%Y%m%d')}_PUB_BID_DAM_v3_csv.zip"


def _is_no_data_report(body: bytes) -> bool:
    """True when a small valid zip wraps the OASIS 'No data returned' XML.

    Isolated trade dates are missing from the OASIS PUB_BID archive on every
    report version (e.g. 2023-06-01; neighbours fine) — the API answers with
    an ERR_CODE 1000 XML report inside a valid zip instead of the CSV.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            name = zf.namelist()[0]
            payload = zf.read(name)
    except (zipfile.BadZipFile, IndexError, KeyError):
        return False
    return b"No data returned for the specified selection" in payload


def _fetch_day(day: dt.date, retries: int = 5, timeout: int = 180) -> bytes | None:
    """Download one trade date's zip, retrying through rate-limit HTML pages.

    Returns the zip bytes, or ``None`` for a genuine no-data archive hole;
    raises ``RuntimeError`` after ``retries`` failures.
    """
    url = _day_url(day)
    delay = 30.0
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
        except Exception as exc:  # noqa: BLE001 — network layer, retry all
            print(f"  {day} attempt {attempt}: {exc!r}", flush=True)
            body = b""
        if body[:2] == b"PK" and len(body) > 10_000:
            return body
        if body[:2] == b"PK" and _is_no_data_report(body):
            print(f"  {day}: NO DATA in the OASIS archive — skipped", flush=True)
            return None
        snippet = body[:120].decode("utf-8", "replace")
        print(
            f"  {day} attempt {attempt}: non-zip body ({len(body)} B): {snippet!r}",
            flush=True,
        )
        time.sleep(delay)
        delay = min(delay * 2, 300.0)
    raise RuntimeError(f"failed to fetch {day} after {retries} attempts")


def fetch_range(
    start: dt.date,
    end: dt.date,
    *,
    sleep_s: float = DEFAULT_SLEEP_S,
    force: bool = False,
) -> list[Path]:
    """Fetch every trade date in [start, end], skipping existing valid zips."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    day = start
    while day <= end:
        out = _out_path(day)
        if out.exists() and out.stat().st_size > 10_000 and not force:
            day += dt.timedelta(days=1)
            continue
        body = _fetch_day(day)
        if body is not None:
            out.write_bytes(body)
            written.append(out)
            print(f"  wrote {out.name} ({len(body):,} B)", flush=True)
        day += dt.timedelta(days=1)
        time.sleep(sleep_s)
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(DEFAULT_YEARS),
        help="calendar years to fetch (default: 2023 2024 2025)",
    )
    ap.add_argument("--start", type=dt.date.fromisoformat, default=None)
    ap.add_argument("--end", type=dt.date.fromisoformat, default=None)
    ap.add_argument("--sleep", type=float, default=DEFAULT_SLEEP_S)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    if (args.start is None) != (args.end is None):
        ap.error("--start and --end must be given together")

    if args.start is not None:
        spans = [(args.start, args.end)]
    else:
        for year in args.years:
            if year not in DEFAULT_YEARS:
                ap.error(
                    f"year {year} is outside the train window "
                    f"{DEFAULT_YEARS} (CLAUDE.md rule 22)"
                )
        spans = [(dt.date(year, 1, 1), dt.date(year, 12, 31)) for year in args.years]

    total = 0
    for span_start, span_end in spans:
        print(f"fetching {span_start} .. {span_end}", flush=True)
        total += len(
            fetch_range(span_start, span_end, sleep_s=args.sleep, force=args.force)
        )
    print(f"done: {total} new files in {RAW_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
