#!/usr/bin/env python3
"""Stage EIA-930 sub-balancing-area hourly demand from the key-free Grid Monitor.

The committed per-year ``data/raw/zone-specific-demand/<ISO>/<iso>_subba_demand_
<year>.csv`` files were pulled from EIA API v2 ``electricity/rto/region-sub-ba-
data`` with the project ``EIA_API_KEY``. That route needs a credential, and the
API's own coverage of this product starts 2019-01-01 — which is why MISO's 2018
partition was recorded as unobtainable (``zone-specific-demand/MISO/SOURCES.md``).

EIA also publishes the SAME sub-BA demand, without registration, in the Hourly
Electric Grid Monitor's six-month bulk extracts::

    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_<YEAR>_<Jan_Jun|Jul_Dec>.csv
    columns: Balancing Authority, Data Date, Hour Number, Sub-Region,
             Demand (MW), Local Time at End of Hour, UTC Time at End of Hour

and those extracts reach back to **2018-07-01** (``2018_Jan_Jun`` is a 404 page:
sub-BA reporting began mid-2018). This script reads them and re-emits the exact
committed schema, so a back year the API cannot serve still lands in the same
shape as its siblings.

**Clock.** The API's ``period`` for this product is the **UTC hour-ending**
stamp, verified against the 2019-H1 overlap: joining the committed
``miso_subba_demand_2019.csv`` to the Grid Monitor extract on ``UTC Time at End
of Hour`` reproduces **4,343/4,343 values exactly** (every other offset from -8
to +8 h matches essentially nothing), so ``period`` is written from the UTC
column verbatim. The Grid Monitor's own "Local Time" column is NOT used: for
MISO it is stamped at a fixed UTC-5 regardless of season, which is neither the
API's convention nor Central time.

Output matches the committed files byte-convention for byte-convention: CRLF
line endings, period-DESCENDING with sub-BA ascending inside each hour,
zero-padded 4-character sub-BA codes, and ``value-units = megawatthours``.
Existing rows are never rewritten — a target file that already exists is only
extended with periods it does not carry (MERGE, never replace; rule 22).

Usage:
    python scripts/data/fetch_eia930_subba_demand.py --iso MISO --years 2018
    python scripts/data/fetch_eia930_subba_demand.py --iso MISO --years 2018 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import ZONE_DEMAND_DIR  # noqa: E402

SIX_MONTH_URL = (
    "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"
    "EIA930_SUBREGION_{year}_{half}.csv"
)
_HALVES = ("Jan_Jun", "Jul_Dec")

# Sub-BA display names, per ISO, in the vintage the committed pre-2023 files use
# (EIA renamed these in 2026 — the 2026 file drops the " - MISO" suffix; a back
# year is written in the naming of its own era, i.e. the 2019-2022 form).
SUBBA_NAMES: dict[str, dict[str, str]] = {
    "MISO": {
        "0001": "Zone 1 - MISO",
        "0004": "Zone 4 - MISO",
        "0006": "Zone 6 - MISO",
        "0027": "Zones 2 and 7 - MISO",
        "0035": "Zones 3 and 5 - MISO",
        "8910": "Zones 8, 9 and 10 - MISO",
    },
}

HEADER = ["period", "subba", "subba-name", "parent", "value", "value-units"]


def _fetch(url: str) -> str | None:
    """GET a six-month extract, or None when EIA has no file for that half."""
    req = Request(url, headers={"User-Agent": "Mozilla/5.0 (market-sim data fetch)"})
    try:
        with urlopen(req, timeout=600) as fh:
            body = fh.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    # EIA serves a 200 HTML "page not found" for a half it never published
    # (2018_Jan_Jun) rather than a 404 — detect it by shape, not status.
    if body.lstrip()[:15].lower().startswith("<!doctype html"):
        return None
    return body


def rows_for_year(iso: str, year: int) -> list[dict[str, str]]:
    """Every published sub-BA hour of ``year`` for ``iso``, newest period first."""
    names = SUBBA_NAMES[iso]
    out: list[dict[str, str]] = []
    for half in _HALVES:
        url = SIX_MONTH_URL.format(year=year, half=half)
        body = _fetch(url)
        if body is None:
            print(f"  {year} {half}: not published by EIA — skipped")
            continue
        n = 0
        for rec in csv.DictReader(io.StringIO(body)):
            if (rec.get("Balancing Authority") or "").strip() != iso:
                continue
            code = (rec.get("Sub-Region") or "").strip().zfill(4)
            if code not in names:
                continue
            demand = (rec.get("Demand (MW)") or "").strip()
            if not demand:
                continue
            # "07/01/2018 6:00:00 AM" -> "2018-07-01T06" (UTC hour-ending, the
            # committed period convention — see the module docstring).
            stamp = (rec.get("UTC Time at End of Hour") or "").strip()
            date_s, time_s, ampm = stamp.split(" ")
            mo, dy, yr = date_s.split("/")
            hour = int(time_s.split(":")[0]) % 12 + (12 if ampm.upper() == "PM" else 0)
            if int(yr) != year:
                # A half-year extract spills a few hours into the neighbouring
                # UTC year (Dec-31 local evening stamps as Jan-1 UTC). The
                # committed files are partitioned by PERIOD year — those hours
                # belong to, and already sit in, the neighbour's file; keeping
                # them here would duplicate them across two partitions.
                continue
            out.append(
                {
                    "period": f"{yr}-{mo}-{dy}T{hour:02d}",
                    "subba": code,
                    "subba-name": names[code],
                    "parent": iso,
                    "value": str(int(round(float(demand)))),
                    "value-units": "megawatthours",
                }
            )
            n += 1
        print(f"  {year} {half}: {n:,} {iso} sub-BA rows")
    out.sort(key=lambda r: (r["period"], r["subba"]), reverse=False)
    out.sort(key=lambda r: r["period"], reverse=True)
    # Stable double sort: period descending, sub-BA ascending within an hour.
    by_period: dict[str, list[dict[str, str]]] = {}
    for r in out:
        by_period.setdefault(r["period"], []).append(r)
    ordered: list[dict[str, str]] = []
    for period in sorted(by_period, reverse=True):
        ordered.extend(sorted(by_period[period], key=lambda r: r["subba"]))
    return ordered


def write_year(iso: str, year: int, rows: list[dict[str, str]], dry_run: bool) -> int:
    """Write/extend ``<iso>_subba_demand_<year>.csv``; return the rows added."""
    path = ZONE_DEMAND_DIR / iso / f"{iso.lower()}_subba_demand_{year}.csv"
    have: set[tuple[str, str]] = set()
    existing: list[dict[str, str]] = []
    if path.exists():
        with path.open(newline="") as fh:
            existing = list(csv.DictReader(fh))
        have = {(r["period"], r["subba"]) for r in existing}
    new = [r for r in rows if (r["period"], r["subba"]) not in have]
    if not new:
        print(f"  {path.name}: nothing new ({len(existing):,} rows on disk)")
        return 0
    merged = existing + new
    by_period: dict[str, list[dict[str, str]]] = {}
    for r in merged:
        by_period.setdefault(r["period"], []).append(r)
    ordered: list[dict[str, str]] = []
    for period in sorted(by_period, reverse=True):
        ordered.extend(sorted(by_period[period], key=lambda r: r["subba"]))
    if dry_run:
        print(
            f"  {path.name}: DRY RUN — would write {len(ordered):,} rows (+{len(new):,})"
        )
        return len(new)
    path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=HEADER, lineterminator="\r\n")
    w.writeheader()
    w.writerows(ordered)
    path.write_bytes(buf.getvalue().encode())
    print(f"  wrote {path} — {len(ordered):,} rows (+{len(new):,} new)")
    return len(new)


def main() -> None:
    """CLI: stage the requested ISO/years from the Grid Monitor bulk extracts."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", default="MISO", choices=sorted(SUBBA_NAMES))
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    for year in args.years:
        rows = rows_for_year(args.iso, year)
        if not rows:
            print(f"  {year}: no published sub-BA rows — nothing written")
            continue
        write_year(args.iso, year, rows, args.dry_run)


if __name__ == "__main__":
    main()
