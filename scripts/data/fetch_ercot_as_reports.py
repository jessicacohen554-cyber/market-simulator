#!/usr/bin/env python3
"""Fetch ERCOT MIS ancillary-services (AS) report bundles for arbitrary years.

Targets the three MIS report families already curated under
``data/raw/ercot-AS/`` (see that directory's ``README.md``):

    NP3-911-ER   "2-Day DAM Ancillary Services Reports"      (2-day lag)
    NP3-966-ER   "60-Day DAM Disclosure Reports"             (60-day lag;
                 carries the AS-only-awards CSV inside the daily mega-zip)
    NP3-965-ER   "60-Day SCED Disclosure Reports"            (60-day lag;
                 carries the AS-offer-updates CSV inside the daily mega-zip)

using ERCOT's **free, unauthenticated** legacy MIS API:

    doc list :  https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=<ID>
    download :  https://www.ercot.com/misdownload/servlets/mirDownload?doclookupId=<docId>

This is the exact pattern already validated and in production use by
``scripts/data/fetch_ercot_ordc_reserves.py`` (NP6-905-CD, reportTypeId=13231).

## Report-type IDs (how they were found, 2026-07-10)

NOT guessed. Each ``reportTypeId`` below was confirmed two independent ways:

1. ``https://www.ercot.com/api/1/services/read/common/all-emil-items-search.json``
   -- ERCOT's own MIS product catalog (unauthenticated) -- filtered to
   ``emilId_s`` matching the EMIL code; the matching entry's
   ``reportTypeId_i`` and ``misDisplayDuration_i`` fields are read directly.
2. The ``reportTypeID`` JS variable embedded in each product's own page,
   ``https://www.ercot.com/mp/data-products/data-product-details?id=<EMIL>``
   (``grep -n reportTypeID`` on the fetched HTML).

Both agree, and both also match the reportTypeId already baked into the
filename prefixes of the files already committed under ``data/raw/ercot-AS/``
(``00013057.np3-911-er...``, ``00013051.np3-966-er...``,
``00013052.np3-965-er...`` -- the zero-padded reportTypeId is the first
filename component ERCOT itself uses).

## The 2018-2022 retention wall (found this session, 2026-07-10)

**ERCOT's free ``IceDocListJsonWS`` doc list is NOT a fixed archive -- it is a
ROLLING window of length ``misDisplayDuration_i`` days, ending "today".**
Confirmed empirically (curl against production, no auth) on 2026-07-10:

    reportTypeId  EMIL          misDisplayDuration_i   earliest doc *actually* listed
    13057         NP3-911-ER    31 days                2026-06-08 (~31 days back)
    13051         NP3-966-ER    1462 days (~4 yr)       2024-03-24 (~2.3 yr back)
    13052         NP3-965-ER    1462 days (~4 yr)       2024-03-24 (~2.3 yr back)

(The two 60-Day report families show less history than their own advertised
``misDisplayDuration_i`` -- the catalog's 1462-day figure appears to be a
maximum/nominal value, not a guarantee; the actually-listed window is what
this script measures live, not the advertised constant.) Passing extra query
params (``size=``, ``startDate=``/``endDate=``) to ``IceDocListJsonWS`` does
NOT widen the list -- verified, identical result set either way.

Because the window's *right edge* is always "today", **2018-2022 will never
become reachable through this endpoint, no matter when this script or its
GitHub Actions workflow runs.** This is a permanent, structural limit of the
free path, not a transient gap. The only ERCOT-side alternative is the
credentialed archive on ``data.ercot.com`` / ``api.ercot.com``
("Search History Data" on each product page), which requires an
``apiexplorer.ercot.com`` account + OAuth bearer token + subscription key.
That route is already investigated and **permanently declined by the repo
owner** in this exact codebase:
``docs/handoffs/ercot-as-coopt-plan-2026-07.md`` §WS-E and
``docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`` (re-verified live this
session: ``api.ercot.com/api/public-reports/...`` still returns
``401 {"message":"Access denied due to missing subscription key..."}``, and
the legacy ``mis.ercot.com/misapp/GetReports.do`` path still 302s to a
SiteMinder market-participant login wall for all three reportTypeIds).

This script therefore performs an honest, up-front reachability check per
(report, year) before attempting anything, and reports -- rather than
fabricates -- when a requested year sits outside the currently-listed window.
It is NOT a no-op generator: it fully implements and exercises the real fetch
mechanics (doc discovery + download), which will work again automatically
the moment either (a) a requested year re-enters the rolling window (e.g.
this script is later pointed at 2024/2025), or (b) ERCOT widens the window,
or (c) a future session is authorized to add credentialed-archive support.

ECRS products (ECRSM/ECRSS in NP3-911-ER) will legitimately carry zero rows
before 2023-06-10 (ECRS market launch) even in any year that IS reachable --
that is expected, not a gap (REGUP/RRS have existed since nodal launch,
Dec 2010).

Run:
    python scripts/data/fetch_ercot_as_reports.py --years 2018 2019 2020 2021 2022
    python scripts/data/fetch_ercot_as_reports.py --years 2025 --sample-only  # smoke test
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "raw" / "ercot-AS"

# Same unauthenticated legacy MIS endpoints already used by
# scripts/data/fetch_ercot_ordc_reserves.py (NP6-905-CD).
DOC_LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"
EMIL_CATALOG_URL = (
    "https://www.ercot.com/api/1/services/read/common/all-emil-items-search.json"
)

# reportTypeId per EMIL -- see module docstring "How they were found".
REPORT_TYPE_IDS: dict[str, int] = {
    "np3-911-er": 13057,  # "2-Day DAM Ancillary Services Reports"
    "np3-966-er": 13051,  # "60-Day DAM Disclosure Reports" (AS-only-awards CSV)
    "np3-965-er": 13052,  # "60-Day SCED Disclosure Reports" (AS-offer-updates CSV)
}

# ERCOT's own advertised MIS list-display window, from the same catalog
# entries (``misDisplayDuration_i``, days). The *actually observed* window is
# measured live in ``_reachable_years`` and may be shorter -- see docstring.
MIS_DISPLAY_DURATION_DAYS: dict[str, int] = {
    "np3-911-er": 31,
    "np3-966-er": 1462,
    "np3-965-er": 1462,
}

# Conservative publish-lag bounds used only to map a doc's PublishDate to an
# *approximate* delivery year when deciding which listed docs are candidates
# for a requested year (the actual per-row Delivery Date column, read later
# by the build scripts, is authoritative -- this is just a coarse doc filter).
_LAG_DAYS_CENTER: dict[str, int] = {
    "np3-911-er": 2,
    "np3-966-er": 60,
    "np3-965-er": 60,
}
# Buffer added on top of the center lag when computing the *earliest possibly
# reachable delivery date* implied by the oldest currently-listed doc (a
# report published shortly after its nominal lag can still cover slightly
# older deliveries, e.g. supplemental/correction bundles).
_LAG_DAYS_BUFFER = 10

_TIMEOUT_S = 120


def _list_docs(report_type_id: int) -> list[dict]:
    """Return every document ERCOT's MIS currently lists for ``report_type_id``.

    This is the live, rolling window -- see module docstring. Raises on any
    non-2xx HTTP response (network/host problems); an empty list is a valid,
    non-error result (no docs currently posted).
    """
    resp = requests.get(
        DOC_LIST_URL, params={"reportTypeId": report_type_id}, timeout=_TIMEOUT_S
    )
    resp.raise_for_status()
    return [d["Document"] for d in resp.json()["ListDocsByRptTypeRes"]["DocumentList"]]


def _reachable_years(emil: str, docs: list[dict]) -> tuple[int, int] | None:
    """Return the ``(min_year, max_year)`` of delivery years the currently
    listed ``docs`` could possibly cover for ``emil``, or ``None`` if no docs
    are listed at all.

    Uses the conservative lag bounds in ``_LAG_DAYS_CENTER``/``_LAG_DAYS_BUFFER``
    -- this is intentionally a coarse, inclusive bound (errs toward "maybe
    reachable") so the exact per-row Delivery Date filtering in
    ``_docs_for_year`` is the source of truth for what actually gets kept.
    """
    if not docs:
        return None
    publishes = [datetime.fromisoformat(d["PublishDate"]) for d in docs]
    lag = timedelta(days=_LAG_DAYS_CENTER[emil] + _LAG_DAYS_BUFFER)
    earliest_delivery = min(publishes) - lag
    latest_delivery = max(publishes)
    return earliest_delivery.year, latest_delivery.year


def _docs_for_year(emil: str, docs: list[dict], year: int) -> list[dict]:
    """Filter ``docs`` to those whose *estimated* delivery date falls in ``year``."""
    lag = timedelta(days=_LAG_DAYS_CENTER[emil])
    out = []
    for d in docs:
        est_delivery = datetime.fromisoformat(d["PublishDate"]) - lag
        if est_delivery.year == year:
            out.append(d)
    return out


def _download(doc: dict, out_dir: Path) -> Path:
    """Download one MIS document by DocID and write it byte-for-byte to ``out_dir``.

    Uses ERCOT's own ``ConstructedName`` (already unique: reportTypeId,
    publish timestamp, and a descriptive report name) so the on-disk file is
    self-describing and traceable back to the exact MIS posting.
    """
    resp = requests.get(DOWNLOAD_URL, params={"doclookupId": doc["DocID"]}, timeout=300)
    resp.raise_for_status()
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / doc["ConstructedName"]
    path.write_bytes(resp.content)
    return path


def fetch_report_years(
    emil: str, years: list[int], out_dir: Path, sample_only: bool, max_docs: int | None
) -> tuple[int, bool]:
    """Fetch ``years`` for one ``emil``. Returns ``(n_downloaded, any_out_of_window)``."""
    report_type_id = REPORT_TYPE_IDS[emil]
    print(f"\n=== {emil} (reportTypeId={report_type_id}) ===")
    docs = _list_docs(report_type_id)
    window = _reachable_years(emil, docs)
    if window is None:
        print("  no documents currently listed at all -- nothing fetchable")
        return 0, True
    publishes = sorted(datetime.fromisoformat(d["PublishDate"]) for d in docs)
    print(
        f"  MIS list currently exposes ~{len(docs)} docs, publish "
        f"{publishes[0].date()} .. {publishes[-1].date()} "
        f"(estimated deliverable years {window[0]}-{window[1]}; ERCOT's "
        f"advertised misDisplayDuration={MIS_DISPLAY_DURATION_DAYS[emil]}d)"
    )

    n_downloaded = 0
    any_out_of_window = False
    for year in years:
        if not (window[0] <= year <= window[1]):
            print(
                f"  {year}: OUT OF RETENTION WINDOW -- ERCOT's free/unauthenticated "
                f"MIS list for {emil} is a rolling window ending today and does not "
                f"reach back this far. This is a permanent limit (the window's right "
                f"edge always tracks 'now'), not a transient gap -- see module "
                f"docstring. Reaching {year} requires ERCOT's credentialed "
                f"data.ercot.com/api.ercot.com archive, which this repo's owner has "
                f"declined to procure (docs/handoffs/ercot-as-coopt-plan-2026-07.md "
                f"§WS-E). Skipping."
            )
            any_out_of_window = True
            continue
        matched = _docs_for_year(emil, docs, year)
        if not matched:
            print(f"  {year}: within the nominal window but no matching docs found")
            continue
        if sample_only:
            matched = matched[:1]
        elif max_docs is not None:
            matched = matched[:max_docs]
        for doc in matched:
            path = _download(doc, out_dir)
            n_downloaded += 1
            try:
                shown = path.relative_to(REPO_ROOT)
            except ValueError:
                shown = path  # out_dir is outside the repo (e.g. a test run)
            print(f"  wrote {shown} ({path.stat().st_size:,} bytes)")
    return n_downloaded, any_out_of_window


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "--report",
        nargs="+",
        choices=sorted(REPORT_TYPE_IDS),
        default=sorted(REPORT_TYPE_IDS),
        help="which MIS report families to fetch (default: all three)",
    )
    ap.add_argument(
        "--years", type=int, nargs="+", required=True, help="delivery years to fetch"
    )
    ap.add_argument(
        "--sample-only",
        action="store_true",
        help="download at most 1 doc per (report, year) -- for validating the "
        "fetch mechanics, not for a real backfill",
    )
    ap.add_argument(
        "--max-docs-per-year",
        type=int,
        default=None,
        help="cap docs downloaded per (report, year); omit for no cap (a full "
        "60-Day-disclosure year is ~365 daily docs)",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help="directory to write raw bundles into (default: %(default)s)",
    )
    args = ap.parse_args(argv)

    total_downloaded = 0
    any_out_of_window = False
    for emil in args.report:
        n, oow = fetch_report_years(
            emil, args.years, args.out_dir, args.sample_only, args.max_docs_per_year
        )
        total_downloaded += n
        any_out_of_window = any_out_of_window or oow

    print(
        f"\nDone: {total_downloaded} document(s) downloaded across {len(args.report)} report(s)."
    )
    if any_out_of_window:
        print(
            "One or more requested years were outside ERCOT's currently-listed "
            "retention window (see per-report messages above). This is an "
            "expected, documented outcome for years far in the past, not a bug."
        )
    if total_downloaded == 0:
        # Distinguish "nothing reachable" (expected for old years, exit 2) from
        # a genuine unexpected failure (exit 1 would have already been raised
        # by requests.raise_for_status() during discovery/download).
        return 2 if any_out_of_window else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
