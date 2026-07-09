"""Fetch MISO daily market-report LMP files and stage the eight named trading hubs.

Scope decision D6 (docs/multi-iso/miso-zonal-refinement-scope.md §7/§8): the
zonal-spread gate needs measured per-hub RT and DA hourly LMPs. MISO publishes
them only as one-file-per-day all-node market reports (no annual archives):

    DA ex-post: https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv
    RT final:   https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv

Each file carries every node's LMP/MCC/MLC per hour-ending 1-24, Eastern
Standard Time year-round (no DST -- the header says so explicitly). Committing
~2,200 all-node daily files (~1 MB each) is not viable, so this script stages
the *verbatim rows for the eight named trading hubs only* (ARKANSAS.HUB,
ILLINOIS.HUB, INDIANA.HUB, LOUISIANA.HUB, MICHIGAN.HUB, MINN.HUB, MS.HUB,
TEXAS.HUB -- all three Value rows: LMP, MCC, MLC) into compact plain-text CSVs
under ``data/raw/lmp-data/MISO/``, one per (year, market, ~7-day window):

    miso_hub_lmp_<year>_<da|rt>_p<NN>.csv   (NN = 01.. , 7 days/chunk, last short)
    columns: date,node,type,value,he01..he24   (values verbatim from the source)

(2023-2025 predate the chunk split and ship as one gzip ``miso_hub_lmp_<year>_
<da|rt>.csv.gz`` per year instead -- ``derive_miso_hub_lmp.py`` reads either
layout. The split to ~7-day chunks (2026-07-09) exists solely so each file is
small enough to read and inline whole into a single ``push_files`` call --
this repo's git-push rule requires committing over the GitHub API, whose
``content`` field is written verbatim as the file's bytes with no encoding
option; gzip binary can't survive that (and base64-encoding the gzip bytes
first doesn't help -- the base64 *text* just gets committed as the file's
literal content, corrupting it, as discovered 2026-07-09 on p01-p13). Plain,
uncompressed CSV is valid UTF-8 and survives ``content`` unmodified, so 2022+
chunks ship uncompressed; a first pass at ~10-day windows (~40KB/chunk)
still overran the Read tool's per-file token cap as plain text (denser than
the old base64-gzip encoding), so the window narrowed to ~7 days (~25-29KB,
~169 lines) to leave comfortable headroom under both the Read-tool
truncation cap and push_files' practical size limit.)

The only transformation is filtering to the hub rows and prepending the
file's date (which the source carries in its header line, not per row) -- the
same source-subset pattern as the ERCOT ``DAMLZHBSPP_*.zip`` holdings (LZ/HB/
SPP settlement points only). Downstream,
``scripts/derive_miso_hub_lmp.py`` reduces these to the zonal validation
parquet ``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``.

``docs.misoenergy.org`` only retains a rolling ~3.5-year window of these daily
files (verified 2026-07-09: 2022-12-31 -> 404, 2023-01-01 -> 200, for both
reports). For a year that has aged off, this script falls back to the MISO
Data Exchange Pricing API (``https://apim.misoenergy.org/pricing/v1``,
subscription-key auth via ``MISO_PRICING_API_KEY``) -- same underlying LMP
Ex-Post reports, verified byte-identical against the static CSV on an
overlapping day (2023-01-03 DA, ARKANSAS.HUB, all three LMP/MCC/MLC rows).
The API's ``node`` filter takes one node per call, so the fallback costs 8
calls/day/market (one per hub) against the API's 100-call/minute quota.

Usage:
    python scripts/fetch_miso_hub_lmp.py --years 2023 2024 2025
    python scripts/fetch_miso_hub_lmp.py --years 2024 --markets rt
    MISO_PRICING_API_KEY=... python scripts/fetch_miso_hub_lmp.py --years 2022
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from market_sim.config.paths import RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_miso_hub_lmp")

OUT_DIR = RAW_DIR / "lmp-data" / "MISO"

_URL = "https://docs.misoenergy.org/marketreports/{ymd}_{report}.csv"
_REPORT = {"da": "da_expost_lmp", "rt": "rt_lmp_final"}

_API_BASE = "https://apim.misoenergy.org/pricing/v1"
_API_MARKET_PATH = {"da": "day-ahead", "rt": "real-time"}
_API_CALLS_PER_MINUTE = 90  # MISO Data Exchange quota is 100/min; leave margin


def _pricing_api_key() -> str | None:
    """Return ``MISO_PRICING_API_KEY`` from the environment or ``.env`` fallback."""
    key = os.environ.get("MISO_PRICING_API_KEY")
    if key:
        return key
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            if line.startswith("MISO_PRICING_API_KEY="):
                return line.split("=", 1)[1].strip()
    return None


class _RateLimiter:
    """Sliding-window limiter shared across threads to stay under the API quota."""

    def __init__(self, max_per_minute: int) -> None:
        self._max = max_per_minute
        self._lock = threading.Lock()
        self._calls: list[float] = []

    def wait(self) -> None:
        """Block until another call is allowed under the per-minute cap."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._calls = [t for t in self._calls if now - t < 60]
                if len(self._calls) < self._max:
                    self._calls.append(now)
                    return
                sleep_for = 60 - (now - self._calls[0]) + 0.05
            time.sleep(sleep_for)


_api_limiter = _RateLimiter(_API_CALLS_PER_MINUTE)

# The eight named MISO trading hubs (scope decision D6). Everything else in
# the daily files (load zones, gennodes, interfaces, the *.AZ accounting hubs)
# is dropped at stage time.
HUBS: frozenset[str] = frozenset(
    {
        "ARKANSAS.HUB",
        "ILLINOIS.HUB",
        "INDIANA.HUB",
        "LOUISIANA.HUB",
        "MICHIGAN.HUB",
        "MINN.HUB",
        "MS.HUB",
        "TEXAS.HUB",
    }
)

_N_HOURS = 24  # HE 1-24, EST year-round (no DST hour in these reports)
_FETCH_WORKERS = 8
_RETRIES = 3
_TIMEOUT_S = 60


class _NotFound(Exception):
    """The static daily report 404s -- the URL has aged off MISO's retention window."""


def _fetch(url: str) -> bytes:
    """Return the response body for ``url``, retrying transient failures.

    A 404 is treated as permanent (retrying won't produce the file) and
    raised immediately as ``_NotFound`` so the caller can fall back to the API.
    """
    last: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise _NotFound(url) from exc
            last = exc
            log.warning("retry %d/%d %s (%s)", attempt + 1, _RETRIES, url, exc)
        except Exception as exc:  # noqa: BLE001 - retry then re-raise
            last = exc
            log.warning("retry %d/%d %s (%s)", attempt + 1, _RETRIES, url, exc)
    raise RuntimeError(f"failed after {_RETRIES} attempts: {url}") from last


_API_RETRIES = 8
_API_BACKOFF_BASE_S = 2.0  # exponential: 2, 4, 8, 16, 32, 64, 128s


def _fetch_json_api(url: str, api_key: str) -> dict:
    """GET ``url`` with the Data Exchange subscription key, retrying transient failures.

    Uses exponential backoff (not just the rate limiter's spacing): observed
    MISO-side 500/503 bursts lasting longer than 3 near-immediate retries.
    """
    req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": api_key})
    last: Exception | None = None
    for attempt in range(_API_RETRIES):
        _api_limiter.wait()
        try:
            with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
                return json.loads(resp.read())
        except Exception as exc:  # noqa: BLE001 - retry then re-raise
            last = exc
            log.warning("retry %d/%d %s (%s)", attempt + 1, _API_RETRIES, url, exc)
            if attempt < _API_RETRIES - 1:
                time.sleep(_API_BACKOFF_BASE_S * (2**attempt))
    raise RuntimeError(f"failed after {_API_RETRIES} attempts: {url}") from last


def _hub_rows_api(day: date, market: str, api_key: str) -> list[list[str]]:
    """Fetch one day's hub rows from the MISO Data Exchange Pricing API.

    Fallback for years the static daily CSV has aged off (module docstring).
    The API's ``node`` query param accepts one node per call, so this makes
    8 calls (one per hub), each returning that hub's 24 hourly LMP/MCC/MLC
    records -- reshaped into the same ``[date, node, type, value, he01..he24]``
    rows the static path produces (node type is always "Hub" for this set).
    """
    iso = day.isoformat()
    url = f"{_API_BASE}/{_API_MARKET_PATH[market]}/{iso}/lmp-expost"
    rows: list[list[str]] = []
    for hub in sorted(HUBS):
        payload = _fetch_json_api(f"{url}?node={hub}", api_key)
        records = payload["data"]
        records.sort(key=lambda r: int(r.get("interval") or r["timeInterval"]["value"]))
        if len(records) != _N_HOURS:
            log.warning(
                "%s %s %s: expected %d hourly records, got %d",
                iso,
                market,
                hub,
                _N_HOURS,
                len(records),
            )
        for metric, label in (("lmp", "LMP"), ("mcc", "MCC"), ("mlc", "MLC")):
            values = [f"{r[metric]:.2f}" for r in records]
            rows.append([iso, hub, "Hub", label, *values])
    return rows


def _hub_rows(day: date, market: str, api_key: str | None) -> list[list[str]]:
    """Fetch one daily report and return the hub rows as staged-CSV records.

    Each record is ``[date, node, type, value, he01..he24]`` with the 24
    hourly strings passed through verbatim (blank stays blank). Falls back to
    the Data Exchange API when the static file has aged off retention.
    """
    ymd = day.strftime("%Y%m%d")
    try:
        body = _fetch(_URL.format(ymd=ymd, report=_REPORT[market]))
    except _NotFound:
        if api_key is None:
            raise RuntimeError(
                f"{day} {market}: static report not found (retention rolled "
                "off) and no MISO_PRICING_API_KEY set for the API fallback"
            ) from None
        return _hub_rows_api(day, market, api_key)
    rows: list[list[str]] = []
    reader = csv.reader(io.StringIO(body.decode("utf-8", errors="replace")))
    for rec in reader:
        if len(rec) < 3 + _N_HOURS or rec[0] not in HUBS:
            continue
        rows.append([day.isoformat(), rec[0], rec[1], rec[2], *rec[3 : 3 + _N_HOURS]])
    if len(rows) != len(HUBS) * 3:  # 8 hubs x LMP/MCC/MLC
        log.warning(
            "%s %s: expected %d hub rows, got %d",
            ymd,
            market,
            len(HUBS) * 3,
            len(rows),
        )
    return rows


def _hub_rows_or_none(
    day: date, market: str, api_key: str | None
) -> list[list[str]] | None:
    """Wrap ``_hub_rows`` so one persistently-failing day can't sink the whole year."""
    try:
        return _hub_rows(day, market, api_key)
    except Exception:
        log.exception("%s %s: giving up on this day after retries", day, market)
        return None


_CHUNK_DAYS = 7  # ~25-29KB plain-text/chunk (module docstring) -- stays under a single push_files call


def stage_year(year: int, market: str, api_key: str | None) -> list[Path]:
    """Fetch every day of ``year`` for ``market`` and write ~7-day staged plain CSVs.

    A day that fails all its retries is dropped (logged loudly) rather than
    aborting the whole year -- the API path costs ~8 calls/day, so losing one
    day's rows is cheap to re-fetch but re-running the whole year is not.
    Chunked by ``_CHUNK_DAYS`` (not one file per year) so each file is small
    enough to inline whole into a single ``push_files`` call (module docstring).

    Written as **plain, uncompressed CSV** (not gzip): this repo's git-push
    rule requires committing binary-safe content through
    ``mcp__github__push_files``' ``content`` string field, which is written
    verbatim as the file's bytes -- there is no way to hand it real gzip
    binary without an encoding step, and base64-encoding the gzip bytes and
    passing *that* string as ``content`` does not decode back to binary, it
    commits the base64 text itself as the file's literal content (discovered
    2026-07-09 when p01-p13 were found corrupted on disk). Plain CSV text is
    valid UTF-8 and survives ``content`` unmodified, so it is the only format
    this push path can carry correctly; the ~7-day chunk size (~169 lines)
    keeps each file comfortably under both the Read-tool truncation cap and
    push_files' practical size limit (a ~10-day/~40KB first pass still
    overran the Read cap as plain text).
    """
    days = []
    d = date(year, 1, 1)
    while d.year == year:
        days.append(d)
        d += timedelta(days=1)
    with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as pool:
        per_day = list(
            pool.map(lambda dd: _hub_rows_or_none(dd, market, api_key), days)
        )

    failed_days = [dd for dd, rows in zip(days, per_day) if rows is None]
    if failed_days:
        log.error(
            "%s %s: %d/%d days FAILED after retries: %s",
            year,
            market,
            len(failed_days),
            len(days),
            ", ".join(dd.isoformat() for dd in failed_days),
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = ["date", "node", "type", "value"] + [
        f"he{h:02d}" for h in range(1, _N_HOURS + 1)
    ]
    out_paths: list[Path] = []
    n = 0
    n_chunks = -(-len(days) // _CHUNK_DAYS)  # ceil
    for i in range(n_chunks):
        window = days[i * _CHUNK_DAYS : (i + 1) * _CHUNK_DAYS]
        out = OUT_DIR / f"miso_hub_lmp_{year}_{market}_p{i + 1:02d}.csv"
        with open(out, "wt", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for dd, rows in zip(days, per_day):
                if dd in window and rows is not None:
                    w.writerows(rows)
                    n += len(rows)
        out_paths.append(out)
    log.info(
        "wrote %d chunk files for %s %s (%d rows, %d/%d days)",
        len(out_paths),
        year,
        market,
        n,
        len(days) - len(failed_days),
        len(days),
    )
    return out_paths


def main() -> None:
    """CLI: stage the requested years/markets."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--markets", nargs="+", choices=sorted(_REPORT), default=sorted(_REPORT)
    )
    args = ap.parse_args()
    api_key = _pricing_api_key()
    for year in args.years:
        for market in args.markets:
            stage_year(year, market, api_key)


if __name__ == "__main__":
    main()
