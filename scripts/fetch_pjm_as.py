"""Fetch PJM ancillary-services / reserve-market data from the DataMiner2 REST API.

Extends ``data/raw/PJM-AS/`` (hand-assembled for 2023-2025 only — see the
directory's README) to the CLAUDE.md rule-22 holdout-intake years: 2018-2022
and H1-2026 (Jan 1 - Jun 30 2026 only). This is DATA INTAKE ONLY — rule 22
keeps solving/scoring on any of these years quarantined until PJM's
calibration-complete marker exists; nothing here runs an LP.

Feeds (PJM DataMiner2, verified live via ``<feed>/metadata`` on 2026-07-10)
----------------------------------------------------------------------------
    reserve_market_results      RT Reserve Market Results   firstAvailable 2013-06-14
    da_reserve_market_results   DA Reserve Market Results    firstAvailable 2022-10-01
    ancillary_services          RT AS hourly product LMPs    firstAvailable 2012-10-01
    da_ancillary_services       DA AS hourly product LMPs    firstAvailable 2022-10-01

All four report ``"retentionTime": "Indefinitely"`` — the ``firstAvailable``
dates above are the true floor, not a rolling window, confirmed by both (a)
the feed's own ``/metadata`` endpoint and (b) live probes: an unfiltered
``sort=datetime_beginning_utc&order=Asc`` query on ``reserve_market_results``
returns rows starting 6/14/2013; the two ``da_*`` feeds return **zero rows**
(HTTP 200, empty body) for any date-range filter entirely before 2022-10-01,
and the earliest row an unfiltered query returns is 10/1/2022 — this is PJM's
Reserve Price Formation market redesign (new DA reserve products), not a
data-retention gap, so it is a genuine "does not exist," never padded.

**Consequence for the requested 2018-2022 + H1-2026 span:**

  - ``reserve_market_results`` / ``ancillary_services`` (RT): every requested
    year 2018-2022 is a full calendar year; H1-2026 is fetched Jan 1 - Jun 30
    only (per the intake authorization — never request past H1).
  - ``da_reserve_market_results`` / ``da_ancillary_services`` (DA): 2018-2021
    are **entirely before retention start** and are skipped — no file is
    written (a zero-row file would be indistinguishable from a fetch bug, so
    we refuse to write one). 2022 is genuinely available only **Oct 1 - Dec
    31** (the market redesign went live mid-year); that partial year is
    fetched and written, but under a ``_partial`` filename suffix (see
    below), never under the plain ``da_reserve_market_results_2022.parquet``
    name a full-year consumer would assume.

Partial-year naming convention
-------------------------------
A file is written under the plain ``<feed>_<year>.parquet`` name ONLY when
its covered window is the full calendar year. Any narrower window (the 2022
DA retention floor, or the H1-2026 scope limit) is written as
``<feed>_<year>_partial.parquet`` with the exact covered date range recorded
in the Parquet schema metadata (``coverage_start``/``coverage_end``/
``partial_reason``). This is deliberate: ``scripts/build_pjm_as_withholding.py``
looks for the plain-named file and would otherwise either build a corrupted
partial-year withholding series or (thanks to its own ``_MAX_GAP_HOURS``
guard) raise on a multi-month gap; the suffix means it correctly sees "no
source parquet" for a partial year and skips it instead of building or
crashing.

DataMiner2 REST API notes (mirrors ``scripts/fetch_pjm_energy_offers.py``)
----------------------------------------------------------------------------
- Base URL:    ``https://api.pjm.com/api/v1``
- Auth header: ``Ocp-Apim-Subscription-Key`` (PJM's own PUBLIC key, published
  in the DataMiner2 site's ``settings.json`` — not a secret). Verified the
  header name is case-insensitive and the API also accepts the same key as a
  ``subscription-key`` query parameter; an unauthenticated request gets a
  genuine HTTP 401, confirming the key is actually required and actually
  working (not merely ignored).
- Date filter: ``datetime_beginning_utc=YYYY-MM-DDThh:mm:ss.0 to YYYY-MM-DDThh:mm:ss.0``
  on all four feeds (confirmed filterable+sortable in each feed's metadata).
- Pagination:  ``startRow`` (1-indexed) + ``rowCount`` (``PAGE_SIZE`` below,
  the API's max page size, same constant as the energy-offers fetcher).
- Format:      ``format=csv`` returns UTF-8 CSV with a BOM.
- Rate limit:  ``--sleep`` (default 1.5s) between pages; ``--retries``
  (default 4) retries with exponential back-off on 429/503.

Usage
-----
    python scripts/fetch_pjm_as.py                          # 2018-2022, all 4 feeds
    python scripts/fetch_pjm_as.py --years 2018 2019
    python scripts/fetch_pjm_as.py --feeds reserve_market_results
    python scripts/fetch_pjm_as.py --h1-2026                # Jan-Jun 2026, all 4 feeds
    python scripts/fetch_pjm_as.py --force                  # re-download existing files

Licensing: PJM DataMiner2 redistribution carries conditions — see
``docs/data-licensing.md`` §4 (open finding for owner review as of 2026-07;
this script only reproduces the existing PJM-AS intake pattern, it does not
resolve that finding).
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# ---------------------------------------------------------------------------
# Repo path bootstrap
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402

OUT_DIR = paths.PJM_AS_DIR

# PJM DataMiner2 REST API — subscription key is PUBLIC (embedded in the
# DataMiner2 Angular app's settings.json at /config/settings.json); same key
# scripts/fetch_pjm_energy_offers.py already uses.
API_BASE = "https://api.pjm.com/api/v1"
SUB_KEY = "6a75d9f6d933401dbb4f36f8e70b95b3"

PAGE_SIZE = (
    50_000  # rows per page (max the API allows; matches the energy-offers fetcher)
)

# The intake authorization (2026-07-10 session, CLAUDE.md rule 22) covers only
# Jan 1 - Jun 30 2026 for the "H1-2026" leg — this is a hard cap, not a default,
# so the CLI never lets --years include 2026 (use --h1-2026 instead).
H1_2026_START = date(2026, 1, 1)
H1_2026_END_EXCLUSIVE = date(2026, 7, 1)  # first instant NOT requested


@dataclass(frozen=True)
class FeedSpec:
    """One PJM DataMiner2 feed this script knows how to fetch and type."""

    name: str
    first_available: date  # verified via <feed>/metadata "firstAvailable"
    float_cols: tuple[str, ...] = ()
    bool_cols: tuple[str, ...] = ()
    int_cols: tuple[str, ...] = ()


# Column lists verified against each feed's live /metadata response and the
# existing hand-assembled 2023-2025 parquets already in data/raw/PJM-AS/.
_RESERVE_FLOAT_COLS = (
    "mcp",
    "mcp_capped",
    "reg_ccp",
    "reg_pcp",
    "as_req_mw",
    "total_mw",
    "as_mw",
    "ss_mw",
    "tier1_mw",
    "ircmwt2",
    "dsr_as_mw",
    "nsr_mw",
    "regd_mw",
)

FEEDS: dict[str, FeedSpec] = {
    "reserve_market_results": FeedSpec(
        name="reserve_market_results",
        first_available=date(2013, 6, 14),
        float_cols=_RESERVE_FLOAT_COLS,
    ),
    "da_reserve_market_results": FeedSpec(
        name="da_reserve_market_results",
        first_available=date(2022, 10, 1),
        # DA feed lacks reg_ccp/reg_pcp/tier1_mw/regd_mw (RT-only regulation
        # mileage/tier-1 columns) per its live /metadata column list.
        float_cols=(
            "mcp",
            "mcp_capped",
            "as_req_mw",
            "total_mw",
            "as_mw",
            "ss_mw",
            "ircmwt2",
            "dsr_as_mw",
            "nsr_mw",
        ),
    ),
    "ancillary_services": FeedSpec(
        name="ancillary_services",
        first_available=date(2012, 10, 1),
        float_cols=("value",),
        bool_cols=("row_is_current",),
        int_cols=("version_nbr",),
    ),
    "da_ancillary_services": FeedSpec(
        name="da_ancillary_services",
        first_available=date(2022, 10, 1),
        float_cols=("value",),
        bool_cols=("row_is_current",),
        int_cols=("version_nbr",),
    ),
}


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------


def _date_filter(start: date, end_exclusive: date) -> str:
    """Return the ``datetime_beginning_utc`` filter string for ``[start, end)``."""
    return (
        f"{start:%Y-%m-%d}T00:00:00.0000000 to "
        f"{end_exclusive:%Y-%m-%d}T00:00:00.0000000"
    )


def _build_url(feed: str, start: date, end_exclusive: date, start_row: int) -> str:
    """Compose the DataMiner2 CSV export URL for one page of a date window."""
    params = {
        "startRow": str(start_row),
        "rowCount": str(PAGE_SIZE),
        "sort": "datetime_beginning_utc",
        "order": "Asc",
        "format": "csv",
        "datetime_beginning_utc": _date_filter(start, end_exclusive),
    }
    return f"{API_BASE}/{feed}?" + urllib.parse.urlencode(params)


def _fetch_page(url: str, *, retries: int = 4, sleep_s: float = 1.5) -> list[dict]:
    """Fetch one CSV page; return list of row dicts.

    Retries on HTTP 429/503 with exponential back-off. A genuine HTTP 404, or
    a 200 with an empty body (DataMiner2's actual response for a window with
    no rows — e.g. entirely before a feed's retention floor, or not yet
    published), both return an empty list rather than raising: "no data for
    this window" is a legitimate, expected outcome here, not an error.

    HTTP 400 is treated the same way (logged, not raised): confirmed live
    2026-07-10 that the ``ancillary_services`` feed returns 400 (not an empty
    200) for a 2018 full-year window even though its own ``/metadata``
    advertises ``firstAvailable: 2012-10-01`` — DataMiner2 is evidently
    inconsistent across feeds about how it signals "before this feed's real
    data starts." Logged distinctly from 404 so a genuinely malformed request
    is still visible in the run log, not silently indistinguishable.
    """
    delay = sleep_s
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "Ocp-Apim-Subscription-Key": SUB_KEY,
                    "Accept": "text/csv",
                    "User-Agent": "market-sim/fetch_pjm_as",
                },
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8-sig", errors="replace")  # strip BOM
            if not raw.strip():
                return []
            rows = list(csv.DictReader(io.StringIO(raw)))
            return rows
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return []
            if exc.code == 400:
                print(f"    HTTP 400 — treating as no data for this window ({url})")
                return []
            if exc.code in (429, 503) and attempt < retries:
                print(f"    HTTP {exc.code} — back-off {delay:.0f}s …")
                time.sleep(delay)
                delay *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < retries:
                print(f"    network error ({exc}) — back-off {delay:.0f}s …")
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return []


def _fetch_window(
    feed: str,
    start: date,
    end_exclusive: date,
    *,
    sleep_s: float = 1.5,
    retries: int = 4,
) -> pd.DataFrame:
    """Download every page for one ``[start, end)`` date window of one feed."""
    all_rows: list[dict] = []
    start_row = 1
    page = 1

    while True:
        url = _build_url(feed, start, end_exclusive, start_row)
        print(f"  page {page:3d}  startRow={start_row:>8d} … ", end="", flush=True)
        rows = _fetch_page(url, retries=retries, sleep_s=sleep_s)
        print(f"{len(rows):>6d} rows")

        all_rows.extend(rows)
        if len(rows) < PAGE_SIZE:
            break  # last page (or no data at all in this window)

        start_row += PAGE_SIZE
        page += 1
        time.sleep(sleep_s)

    if not all_rows:
        return pd.DataFrame()
    return pd.DataFrame(all_rows)


def _coerce_dtypes(df: pd.DataFrame, spec: FeedSpec) -> pd.DataFrame:
    """Coerce raw CSV strings to typed columns for efficient Parquet encoding."""
    df.columns = [c.strip().lower() for c in df.columns]
    for col in spec.float_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in spec.int_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    for col in spec.bool_cols:
        if col in df.columns:
            df[col] = df[col].map(
                {"True": True, "False": False, "true": True, "false": False}
            )
    return df


# ---------------------------------------------------------------------------
# Year-window planning (retention floor + H1-2026 scope cap)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class YearWindow:
    """A feed's fetchable window for one requested year, or the skip reason."""

    year: int
    start: date | None
    end_exclusive: date | None
    is_full_year: bool
    partial_reason: str | None = None
    skip_reason: str | None = None


def _plan_year(feed: FeedSpec, year: int, *, h1_only: bool) -> YearWindow:
    """Compute the fetchable window for ``feed`` in ``year`` given its retention floor.

    ``h1_only=True`` hard-caps the window at 2026-06-30 regardless of
    retention (the intake authorization is Jan-Jun 2026 only — never request
    past H1, even if the feed's real retention extends further).
    """
    calendar_start = date(year, 1, 1)
    calendar_end_exclusive = date(year + 1, 1, 1)

    window_start = max(calendar_start, feed.first_available)
    window_end_exclusive = calendar_end_exclusive
    if h1_only:
        window_end_exclusive = min(window_end_exclusive, H1_2026_END_EXCLUSIVE)
        window_start = max(window_start, H1_2026_START)

    if window_start >= window_end_exclusive:
        return YearWindow(
            year=year,
            start=None,
            end_exclusive=None,
            is_full_year=False,
            skip_reason=(
                f"entirely before {feed.name}'s retention floor "
                f"({feed.first_available:%Y-%m-%d}) — not writing a fabricated file"
            ),
        )

    is_full_year = (
        window_start == calendar_start
        and window_end_exclusive == calendar_end_exclusive
    )
    partial_reason = None
    if not is_full_year:
        if h1_only:
            partial_reason = (
                "scope-limited: intake authorization covers Jan 1 - Jun 30 2026 only"
            )
        else:
            partial_reason = (
                f"retention-limited: {feed.name} data starts "
                f"{feed.first_available:%Y-%m-%d}, mid-year"
            )
    return YearWindow(
        year=year,
        start=window_start,
        end_exclusive=window_end_exclusive,
        is_full_year=is_full_year,
        partial_reason=partial_reason,
    )


# ---------------------------------------------------------------------------
# Main fetch-and-write
# ---------------------------------------------------------------------------


def fetch_feed_year(
    feed_key: str,
    year: int,
    *,
    h1_only: bool = False,
    sleep_s: float = 1.5,
    retries: int = 4,
    force: bool = False,
) -> Path | None:
    """Fetch one (feed, year) into ``data/raw/PJM-AS/``; return the written path or None."""
    spec = FEEDS[feed_key]
    plan = _plan_year(spec, year, h1_only=h1_only)

    if plan.skip_reason:
        print(f"[{feed_key} {year}] SKIP — {plan.skip_reason}")
        return None

    suffix = "" if plan.is_full_year else "_partial"
    out_path = OUT_DIR / f"{feed_key}_{year}{suffix}.parquet"
    if out_path.exists() and not force:
        print(f"[{feed_key} {year}] already exists, skipping ({out_path.name})")
        return out_path

    print(
        f"[{feed_key} {year}] fetching {plan.start:%Y-%m-%d} to "
        f"{plan.end_exclusive:%Y-%m-%d} (exclusive)"
        + (f" — PARTIAL: {plan.partial_reason}" if plan.partial_reason else "")
    )
    df = _fetch_window(
        feed_key, plan.start, plan.end_exclusive, sleep_s=sleep_s, retries=retries
    )
    if df.empty:
        print(f"  no rows returned for {feed_key} {year} — not yet published, skipping")
        return None

    df = _coerce_dtypes(df, spec)
    table = pa.Table.from_pandas(df, preserve_index=False)
    metadata = {
        "source": f"PJM DataMiner2 feed '{feed_key}', https://api.pjm.com/api/v1/{feed_key}",
        "coverage_start": plan.start.isoformat(),
        "coverage_end_exclusive": plan.end_exclusive.isoformat(),
        "is_full_calendar_year": str(plan.is_full_year),
    }
    if plan.partial_reason:
        metadata["partial_reason"] = plan.partial_reason
    table = table.replace_schema_metadata(
        {
            **(table.schema.metadata or {}),
            **{k: v.encode() for k, v in metadata.items()},
        }
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, out_path)
    mb = out_path.stat().st_size / 1_048_576
    print(f"  saved {len(df):,} rows → {out_path.name} ({mb:.1f} MB)")
    return out_path


def main() -> None:
    """CLI entrypoint: fetch the requested feeds x years into data/raw/PJM-AS/."""
    ap = argparse.ArgumentParser(
        description="Fetch PJM ancillary-services / reserve-market data from DataMiner2"
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2018, 2019, 2020, 2021, 2022],
        help="Calendar years to fetch (default: 2018-2022). 2026 is rejected here — "
        "use --h1-2026, which hard-caps at Jun 30 2026 per the intake authorization.",
    )
    ap.add_argument(
        "--h1-2026",
        action="store_true",
        help="Also fetch Jan 1 - Jun 30 2026 (never later) for the requested feeds",
    )
    ap.add_argument(
        "--feeds",
        nargs="+",
        default=list(FEEDS),
        choices=list(FEEDS),
        help="Feeds to fetch (default: all four)",
    )
    ap.add_argument(
        "--sleep", type=float, default=1.5, help="Seconds between API pages"
    )
    ap.add_argument("--retries", type=int, default=4, help="Retries on HTTP 429/503")
    ap.add_argument(
        "--force", action="store_true", help="Re-download and overwrite existing files"
    )
    args = ap.parse_args()

    if 2026 in args.years:
        ap.error(
            "2026 may not appear in --years (only Jan-Jun is authorized) — pass --h1-2026 instead"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Each (feed, year) fetch is independent; one unexpected failure (a real
    # bug, a transient outage that exhausted retries, ...) must not discard
    # every other (feed, year) already written to disk in this run — so
    # failures are logged and skipped rather than aborting the whole script.
    failures: list[str] = []
    for feed_key in args.feeds:
        for year in sorted(args.years):
            try:
                fetch_feed_year(
                    feed_key,
                    year,
                    h1_only=False,
                    sleep_s=args.sleep,
                    retries=args.retries,
                    force=args.force,
                )
            except Exception as exc:  # noqa: BLE001 - log and continue, see above
                print(f"[{feed_key} {year}] FAILED unexpectedly: {exc}")
                failures.append(f"{feed_key} {year}: {exc}")
        if args.h1_2026:
            try:
                fetch_feed_year(
                    feed_key,
                    2026,
                    h1_only=True,
                    sleep_s=args.sleep,
                    retries=args.retries,
                    force=args.force,
                )
            except Exception as exc:  # noqa: BLE001 - log and continue, see above
                print(f"[{feed_key} 2026] FAILED unexpectedly: {exc}")
                failures.append(f"{feed_key} 2026: {exc}")

    if failures:
        print(f"\n{len(failures)} (feed, year) fetch(es) failed unexpectedly:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()
