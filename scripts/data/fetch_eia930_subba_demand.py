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
zero-padded 4-character sub-BA codes (MISO's codes are numeric; SWPP's are
alphabetic utility mnemonics and are NOT padded — see ``SUBBA_NAMES``), and
``value-units = megawatthours``. Existing rows are never rewritten — a target
file that already exists is only extended with periods it does not carry
(MERGE, never replace; rule 22).

``--combine`` writes ONE ``<iso>_subba_demand_<first>-<last>.csv`` spanning the
requested years instead of one file per year, which is the shape the committed
``miso_subba_demand_2023-2025.csv`` uses for the calibration window. The byte
convention is the one above in both cases (the combined MISO file predates this
script and is period-ASCENDING/LF, an API-era artifact; nothing downstream reads
these files in order — ``curate_zonal_shares.py`` pivots on ``period``).

Usage:
    python scripts/data/fetch_eia930_subba_demand.py --iso MISO --years 2018
    python scripts/data/fetch_eia930_subba_demand.py --iso MISO --years 2018 --dry-run
    python scripts/data/fetch_eia930_subba_demand.py --iso SPP \
        --years 2023 2024 2025 --combine
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

# The Grid Monitor's own BA code for each model ISO. The six-month extract keys
# its rows on this code, and it is what the API writes into the ``parent``
# column, so it is used for both. MISO's ISO name and BA code coincide; SPP's
# do not (BA code ``SWPP``).
PARENT_BA: dict[str, str] = {"MISO": "MISO", "SPP": "SWPP"}

# Sub-BA display names, per ISO, in the vintage the committed pre-2023 files use
# (EIA renamed these in 2026 — the 2026 file drops the " - MISO" suffix; a back
# year is written in the naming of its own era, i.e. the 2019-2022 form).
#
# SPP: the 17 SWPP sub-BAs, names taken verbatim from EIA's own key-free
# EIA-930 reference table ``https://www.eia.gov/electricity/930-api/sub_bas/data``
# (``DESCRIPTION`` of every row whose ``PARENT_BA_ID`` is ``SWPP``), pulled
# 2026-09-06. The six-month extract carries only the code, so the names cannot
# be read off it; this is the table the Grid Monitor itself renders them from.
# There is no committed SPP file whose naming vintage a back year would have to
# match, so this current vintage is used for every year and recorded in
# ``data/raw/zone-specific-demand/SPP/SOURCES.md``.
SUBBA_NAMES: dict[str, dict[str, str]] = {
    "MISO": {
        "0001": "Zone 1 - MISO",
        "0004": "Zone 4 - MISO",
        "0006": "Zone 6 - MISO",
        "0027": "Zones 2 and 7 - MISO",
        "0035": "Zones 3 and 5 - MISO",
        "8910": "Zones 8, 9 and 10 - MISO",
    },
    "SPP": {
        "CSWS": "AEPW American Electric Power West",
        "EDE": "Empire District Electric Company",
        "GRDA": "Grand River Dam Authority",
        "INDN": "Independence Power & Light",
        "KACY": "Kansas City Board of Public Utilities",
        "KCPL": "Kansas City Power & Light",
        "LES": "Lincoln Electric System",
        "MPS": "KCP&L Greater Missouri Operations",
        "NPPD": "Nebraska Public Power District",
        "OKGE": "Oklahoma Gas and Electric Co.",
        "OPPD": "Omaha Public Power District",
        "SECI": "Sunflower Electric",
        "SPRM": "City of Springfield",
        "SPS": "Southwestern Public Service Company",
        "WAUE": "Western Area Power Upper Great Plains East",
        "WFEC": "Western Farmers Electric Cooperative",
        "WR": "Westar Energy",
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


def _code(raw: str) -> str:
    """Normalise a ``Sub-Region`` cell to the committed ``subba`` convention.

    MISO's sub-BA ids are numeric and the committed files zero-pad them to four
    characters ("1" -> "0001"). SWPP's are alphabetic utility mnemonics of two
    to four characters (``WR``, ``EDE``, ``CSWS``) which must pass through
    unpadded — padding them would invent codes ("00WR") that EIA never
    publishes.
    """
    code = raw.strip()
    return code.zfill(4) if code.isdigit() else code


def rows_for_year(
    iso: str, year: int, keep_years: frozenset[int] | None = None
) -> list[dict[str, str]]:
    """Every published sub-BA hour of ``year`` for ``iso``, newest period first.

    ``keep_years`` widens the period-year filter below from ``{year}`` to the
    whole span a ``--combine`` run is landing in one file. A half-year extract
    spills the first few UTC hours of January into the *previous* year's
    ``Jul_Dec`` file (SWPP is UTC-6, so 7 hour-ending stamps), and those hours
    are inside a multi-year file's own span — dropping them would leave a
    self-inflicted hole at every interior year boundary.
    """
    names = SUBBA_NAMES[iso]
    parent = PARENT_BA[iso]
    wanted = keep_years if keep_years is not None else frozenset({year})
    out: list[dict[str, str]] = []
    for half in _HALVES:
        url = SIX_MONTH_URL.format(year=year, half=half)
        body = _fetch(url)
        if body is None:
            print(f"  {year} {half}: not published by EIA — skipped")
            continue
        n = 0
        for rec in csv.DictReader(io.StringIO(body)):
            if (rec.get("Balancing Authority") or "").strip() != parent:
                continue
            code = _code(rec.get("Sub-Region") or "")
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
            if int(yr) not in wanted:
                # A half-year extract spills a few hours into the neighbouring
                # UTC year (Dec-31 local evening stamps as Jan-1 UTC). The
                # committed files are partitioned by PERIOD year — those hours
                # belong to, and already sit in, the neighbour's file; keeping
                # them here would duplicate them across two partitions. (Under
                # --combine ``wanted`` is the whole span, so an INTERIOR
                # boundary's hours are kept — they are that file's own.)
                continue
            out.append(
                {
                    "period": f"{yr}-{mo}-{dy}T{hour:02d}",
                    "subba": code,
                    "subba-name": names[code],
                    "parent": parent,
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


def write_year(
    iso: str,
    year: int,
    rows: list[dict[str, str]],
    dry_run: bool,
    path: Path | None = None,
) -> int:
    """Write/extend ``<iso>_subba_demand_<year>.csv``; return the rows added.

    ``path`` overrides the per-year target (used by ``--combine``, which lands
    every requested year in one ``<iso>_subba_demand_<first>-<last>.csv``); the
    MERGE-never-replace semantics and the byte convention are the same either
    way.
    """
    path = path or ZONE_DEMAND_DIR / iso / f"{iso.lower()}_subba_demand_{year}.csv"
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
    ap.add_argument(
        "--combine",
        action="store_true",
        help="write ONE <iso>_subba_demand_<first>-<last>.csv spanning the "
        "requested years instead of one file per year (the shape the committed "
        "miso_subba_demand_2023-2025.csv uses for the calibration window)",
    )
    args = ap.parse_args()
    years = sorted(args.years)
    combined: list[dict[str, str]] = []
    span_years = frozenset(years) if args.combine else None
    for year in years:
        rows = rows_for_year(args.iso, year, span_years)
        if not rows:
            print(f"  {year}: no published sub-BA rows — nothing written")
            continue
        if args.combine:
            combined.extend(rows)
        else:
            write_year(args.iso, year, rows, args.dry_run)
    if args.combine and combined:
        span = f"{years[0]}-{years[-1]}" if len(years) > 1 else str(years[0])
        path = (
            ZONE_DEMAND_DIR / args.iso / f"{args.iso.lower()}_subba_demand_{span}.csv"
        )
        write_year(args.iso, years[-1], combined, args.dry_run, path=path)


if __name__ == "__main__":
    main()
