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
``scripts/data/derive_miso_hub_lmp.py`` reduces these to the zonal validation
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
    python scripts/data/fetch_miso_hub_lmp.py --years 2023 2024 2025
    python scripts/data/fetch_miso_hub_lmp.py --years 2024 --markets rt
    MISO_PRICING_API_KEY=... python scripts/data/fetch_miso_hub_lmp.py --years 2022
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import re
import sys
import threading
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from market_sim.config.paths import RAW_DIR

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.lib.env_keys import get_api_key  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_miso_hub_lmp")

OUT_DIR = RAW_DIR / "lmp-data" / "MISO"

_URL = "https://docs.misoenergy.org/marketreports/{ymd}_{report}.csv"
_REPORT = {"da": "da_expost_lmp", "rt": "rt_lmp_final"}

_API_BASE = "https://apim.misoenergy.org/pricing/v1"
_API_MARKET_PATH = {"da": "day-ahead", "rt": "real-time"}
_API_CALLS_PER_MINUTE = 90  # MISO Data Exchange quota is 100/min; leave margin

# --- pre-2023 route: the MONTHLY Daily/Real-Time Pricing Report zips ---------
# MISO changed report FAMILIES in 2023; it did not delete its history. The
# daily all-node reports above (``_URL``) start 2023-01-01 and 404 below it;
# these monthly zips of per-day ``.xls`` pricing reports run from at least 2015
# and 404 from 2023-01 -- the two families are exact mirror images, so between
# them the public record is unbroken. Measured 2026-09-13: ``{ym}_da_pr_xls``
# returns 200 for 201501/201801/201901/202001/202006/202012/202101/202106/
# 202112/202201/202206/202212 and 404 for 202306/202406.
#
# Provenance, and why this is the SAME measurement and not a substitute: over
# the one month both families cover on disk (2022-06), the monthly route
# reproduces the committed API-sourced staging EXACTLY on day-ahead -- 5,760 of
# 5,760 hub-hours, max abs diff $0.0000 -- and on real-time reproduces 5,721 of
# 5,760 (99.32%), the 39 exceptions being five (date, hour) slots the monthly
# report publishes as 0.0 across ALL EIGHT hubs at once (missing data, handled
# below), not restated prices.
#
# Found via the source-URL table of Zenodo deposit 10.5281/zenodo.17676746
# ("Electricity Price Data by System Operator", CC-BY-4.0), whose MISO series
# was downloaded from this family in November 2020. Three prior route audits
# (miso-252, miso-254, miso-256) swept the DAILY and annual ``*_HIST`` naming
# spaces only and concluded the pre-2023 record was unrecoverable; it was not.
_MONTHLY_URL = "https://docs.misoenergy.org/marketreports/{ym}_{report}.zip"
_MONTHLY_REPORT = {"da": "da_pr_xls", "rt": "rt_pr_xls"}

# The report labels its hub columns with display names, not the node ids the
# daily all-node file uses. MISO System is the 9th column and is deliberately
# NOT staged: it is a system average, not one of the eight named hubs (D6).
_MONTHLY_HUB_COLUMNS = {
    "Arkansas Hub": "ARKANSAS.HUB",
    "Illinois Hub": "ILLINOIS.HUB",
    "Indiana Hub": "INDIANA.HUB",
    "Louisiana Hub": "LOUISIANA.HUB",
    "Michigan Hub": "MICHIGAN.HUB",
    "Minnesota Hub": "MINN.HUB",
    "MS.HUB": "MS.HUB",
    "Texas Hub": "TEXAS.HUB",
}

# Each sheet states its own market date. This is load-bearing rather than
# cosmetic: the DA member is named for its market date (20210615_da_pr.xls ->
# 06/15/2021) but the RT member is named for its PUBLISH date and carries the
# PRIOR day's market (20220615_rt_pr.xls -> 06/14/2022). Keying on the filename
# mis-dates every real-time row by one day; keying on this header is correct for
# both families and needs no per-market special case.
_MONTHLY_MARKET_DATE_RE = re.compile(r"Market Date:\s*(\d{2})/(\d{2})/(\d{4})")

# The hourly block is found by its own header row (the one whose second cell
# reads "MISO System") rather than a fixed offset -- DA puts it at row 14 and
# RT at row 11, and the preamble has varied across years.
_MONTHLY_HEADER_CELL = "MISO System"

_monthly_cache: dict[tuple[int, int, str], dict[date, list[list[str]]]] = {}
_monthly_lock = threading.Lock()


def _pricing_api_key() -> str | None:
    """Return ``MISO_PRICING_API_KEY`` from the environment or ``.env`` fallback."""
    return get_api_key("MISO_PRICING_API_KEY", required=False)


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


def _parse_monthly_zip(body: bytes, market: str) -> dict[date, list[list[str]]]:
    """Parse one monthly pricing-report zip into staged rows keyed by MARKET date.

    Each zip member is a legacy BIFF ``.xls`` holding one market day: a short
    preamble, then an ``HE 01``-``HE 24`` block whose columns are MISO System
    plus the eight named hubs. Returns ``{market_date: [[date, node, "Hub",
    "LMP", he01..he24], ...]}`` -- the same record shape the daily and API
    routes produce, so every downstream reader is untouched.

    **LMP only.** This family publishes the settled hub price without the
    MCC/MLC decomposition the daily all-node file carries, so the MCC and MLC
    rows the other two routes stage are simply absent here. That is complete
    for every consumer in this repo: ``derive_miso_hub_lmp`` selects
    ``value == "LMP"`` and nothing reads the other two.

    An hour the report publishes as exactly ``0.0`` at ALL EIGHT hubs at once is
    staged BLANK (missing), not as a zero price. Eight hubs settling at exactly
    $0.00 in the same hour does not occur in a real market -- congestion and
    losses separate them -- so it is the report's missing-data marker, and
    writing it through as a price would put a false zero into the validation
    reference. Blank is the staged convention for an absent hour, and the
    coverage machinery downstream already records partial months.
    """
    import xlrd  # local: tooling-only dependency, never imported by the model

    out: dict[date, list[list[str]]] = {}
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        for name in sorted(zf.namelist()):
            if not name.lower().endswith(".xls"):
                continue
            sheet = xlrd.open_workbook(file_contents=zf.read(name)).sheet_by_index(0)
            market_date = None
            for r in range(min(8, sheet.nrows)):
                m = _MONTHLY_MARKET_DATE_RE.search(str(sheet.cell_value(r, 0)))
                if m:
                    market_date = date(int(m[3]), int(m[1]), int(m[2]))
                    break
            header = next(
                (
                    r
                    for r in range(sheet.nrows)
                    if str(sheet.cell_value(r, 1)).strip() == _MONTHLY_HEADER_CELL
                ),
                None,
            )
            if market_date is None or header is None:
                log.warning("%s %s: no market date / hour block, skipped", name, market)
                continue
            col = {
                _MONTHLY_HUB_COLUMNS[label]: c
                for c in range(sheet.ncols)
                if (label := str(sheet.cell_value(header, c)).strip())
                in _MONTHLY_HUB_COLUMNS
            }
            missing_hubs = sorted(set(_MONTHLY_HUB_COLUMNS.values()) - set(col))
            if missing_hubs:
                log.warning("%s %s: hub columns absent: %s", name, market, missing_hubs)
            # hour -> {hub: text}; blanked below where the whole hour is 0.0.
            by_hour: dict[int, dict[str, str]] = {}
            for r in range(header + 1, min(header + 1 + _N_HOURS, sheet.nrows)):
                label = str(sheet.cell_value(r, 0)).strip()
                if not label.startswith("Hour"):
                    continue
                values = {}
                for hub, c in col.items():
                    raw = sheet.cell_value(r, c)
                    values[hub] = "" if raw in ("", None) else f"{float(raw):.2f}"
                if col and all(v == "0.00" for v in values.values()):
                    values = dict.fromkeys(values, "")
                by_hour[int(label.split()[-1])] = values
            if len(by_hour) != _N_HOURS:
                log.warning(
                    "%s %s: expected %d hours, got %d",
                    name,
                    market,
                    _N_HOURS,
                    len(by_hour),
                )
            iso = market_date.isoformat()
            out[market_date] = [
                [
                    iso,
                    hub,
                    "Hub",
                    "LMP",
                    *[by_hour.get(h, {}).get(hub, "") for h in range(1, _N_HOURS + 1)],
                ]
                for hub in sorted(col)
            ]
    return out


def _monthly_month(year: int, month: int, market: str) -> dict[date, list[list[str]]]:
    """Return one month's staged rows, fetching and parsing the zip at most once.

    ``stage_year`` fans out over DAYS, so without this cache each of a month's
    ~30 days would re-download and re-parse the same ~120 KB archive.
    """
    key = (year, month, market)
    with _monthly_lock:
        if key in _monthly_cache:
            return _monthly_cache[key]
    url = _MONTHLY_URL.format(ym=f"{year}{month:02d}", report=_MONTHLY_REPORT[market])
    try:
        parsed = _parse_monthly_zip(_fetch(url), market)
    except _NotFound:
        parsed = {}
    with _monthly_lock:
        _monthly_cache.setdefault(key, parsed)
        return _monthly_cache[key]


def _hub_rows_monthly(day: date, market: str) -> list[list[str]] | None:
    """Return ``day``'s hub rows from the monthly pricing-report zip, else ``None``.

    Searches the day's own month and then the FOLLOWING month. The second look
    is what the real-time family needs and is not an edge case: its members are
    named for the PUBLISH date, so the last market day of any month is published
    on the 1st of the next and ships in the NEXT month's archive. Without it
    every month-end real-time day is missing -- measured as exactly 12 of 365
    days in 2021, one per month. Expressed as "day's month, then the next"
    rather than as a per-market rule so a day-ahead member that ever shifts the
    same way is picked up too; a month already parsed is served from cache, so
    the second look is free.

    ``None`` means this route genuinely has nothing for the day -- both months
    404 (2023 onward) -- and the caller falls through to the credentialed API.
    """
    for probe in (day, day + timedelta(days=1)):
        rows = _monthly_month(probe.year, probe.month, market).get(day)
        if rows:
            return rows
    return None


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
        # Below 2023-01-01 the daily family 404s. Try the monthly pricing-report
        # zips FIRST: they cover exactly those years, need no credential, and
        # reproduce the API byte-for-byte on day-ahead where both are available
        # (_MONTHLY_URL's note). The API stays as the last resort.
        monthly = _hub_rows_monthly(day, market)
        if monthly:
            return monthly
        if api_key is None:
            raise RuntimeError(
                f"{day} {market}: static report not found (retention rolled "
                "off), the monthly pricing-report zip has no row for this day, "
                "and no MISO_PRICING_API_KEY is set for the API fallback"
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


def stage_year(
    year: int, market: str, api_key: str | None, through: date | None = None
) -> list[Path]:
    """Fetch every day of ``year`` for ``market`` and write ~7-day staged plain CSVs.

    ``through`` (optional) stops the day list at that date instead of running to
    Dec 31 -- the half-year staging the holdout intake channel needs (CLAUDE.md
    rule 22 authorizes intake for a *named window*, e.g. "H1-2026", so staging
    days past that window would land data nobody authorized even though the
    source publishes them).

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
    while d.year == year and (through is None or d <= through):
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
    # A year in which EVERY day failed is a source/credential problem, not a
    # staging: writing its chunk files anyway leaves ~53 header-only CSVs whose
    # names are indistinguishable from a real staging, and the derive step reads
    # them without complaint. Refuse to write instead. The usual cause is a
    # pre-2023 year (``docs.misoenergy.org`` serves no daily report before
    # 2023-01-01 -- re-verified 2026-09-12) with no ``MISO_PRICING_API_KEY`` set
    # for the documented Data Exchange fallback.
    if len(failed_days) == len(days):
        raise RuntimeError(
            f"{year} {market}: 0/{len(days)} days staged -- nothing written. "
            "Every day failed: the static daily reports 404 before 2023-01-01, "
            "the monthly pricing-report zips returned nothing for this year, "
            "and the Data Exchange fallback needs MISO_PRICING_API_KEY "
            "(see data/raw/lmp-data/MISO/README.md)."
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
        chunk = [
            rows for dd, rows in zip(days, per_day) if dd in window and rows is not None
        ]
        if not chunk:
            # No day in this window staged: skip the file rather than leave a
            # header-only CSV standing in for a week nobody has. The 2022
            # staging already records a short tail as ABSENT chunks (p01..p49,
            # not 53 with four empty ones) -- this keeps that convention true.
            continue
        out = OUT_DIR / f"miso_hub_lmp_{year}_{market}_p{i + 1:02d}.csv"
        with open(out, "wt", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            for rows in chunk:
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
    ap.add_argument(
        "--through",
        type=date.fromisoformat,
        default=None,
        help="last day to stage (YYYY-MM-DD), for half-year windows like H1-2026",
    )
    args = ap.parse_args()
    api_key = _pricing_api_key()
    for year in args.years:
        for market in args.markets:
            stage_year(year, market, api_key, through=args.through)


if __name__ == "__main__":
    main()
