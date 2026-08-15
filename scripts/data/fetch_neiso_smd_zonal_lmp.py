"""Download ISO-NE hourly DA / RT-final LMP for the nine SMD pricing locations.

WHY THIS EXISTS (neiso-96, 2026-08-15).  ``scripts/data/derive_actual_lmp.py``
sources NEISO from the ISO-NE SMD hourly workbooks
(``data/raw/lmp-data/NEISO/<year>_smd_hourly.xlsx``), which are **hand
downloaded**: the ISO Express *Zonal Information* page serves them only behind
a CAPTCHA-gated "Download Selected Files" form, so no committed script can
refresh them and no unattended session can obtain a year the repo does not
already hold.  The repo holds 2018-2025.  H1-2026 -- the half of NEISO's
``final`` locked test that is blocked by MISSING DATA rather than by a finding
-- was therefore unreachable through the workbook route.

ISO-NE publishes **the same hourly prices** through a second, ungated channel:
the static historical-report tree, one operating day per file, no CAPTCHA and
no credentials.

    https://www.iso-ne.com/static-transform/csv/histRpts/da-lmp/WW_DALMP_ISO_<YYYYMMDD>.csv
    https://www.iso-ne.com/static-transform/csv/histRpts/rt-lmp/lmp_rt_final_<YYYYMMDD>.csv

Both are the *Hourly LMP Report* for their market -- the DA market's hourly
clearing prices and the real-time market's **final** (settlement) hourly
prices -- at every ISO-NE location.  This script keeps only the nine the SMD
workbook's per-zone sheets carry and reduces ~4.9 MB/day of all-node report to
~14 KB/day of zonal series, so a half-year lands as one small committed CSV
instead of 362 multi-megabyte files.

    location id  location name        SMD sheet
    ===========  ===================  ==========
    4000         .H.INTERNAL_HUB      ISO NE CA   (the system hub)
    4001         .Z.MAINE             ME
    4002         .Z.NEWHAMPSHIRE      NH
    4003         .Z.VERMONT           VT
    4004         .Z.CONNECTICUT       CT
    4005         .Z.RHODEISLAND       RI
    4006         .Z.SEMASS            SEMA
    4007         .Z.WCMASS            WCMA
    4008         .Z.NEMASSBOST        NEMA

THIS IS THE SAME SERIES, NOT A PROXY, AND THE CLAIM IS MEASURED RATHER THAN
ASSERTED.  ``scripts/probes/neiso96_smd_route_equivalence.py`` runs sampled
operating days from the committed years through this reducer and compares them
to the workbook-derived values the committed parquet is built from; they agree
to the last published cent.  That is what lets 2026 be carried on this route
without year-gating the *input*: the two routes are one input (CLAUDE.md rule
22 as amended 2026-08-06).

Hour labelling is identical to the workbook's, which is what makes the
positional clock in ``derive_actual_lmp._neiso_sheet_series`` transfer
unchanged: ``Hour Ending`` runs "01".."24", the fall-back day carries 25 rows
with "02X" marking the repeated hour, and the spring-forward day carries 23.
Verified 2026-08-15 on 2025-11-02 (25 rows) and 2026-03-08 (23 rows).  This
script records the within-day row position (``seq``) explicitly so downstream
never has to re-derive it from a label.

Layout produced (committed -- small, and it is the durable record of a window
whose per-day source files are not kept):

    data/raw/lmp-data/NEISO/smd-zonal-lmp/NEISO_smd_zonal_lmp_<year>.csv

Rule 22: this is DATA INTAKE.  What is held out is the SCORE, never the DATA
-- an intake needs no marker and no authorization, and this script neither
solves, scores nor registers anything.

Usage:
    uv run python scripts/data/fetch_neiso_smd_zonal_lmp.py --start 2026-01-01 --end 2026-06-30
    uv run python scripts/data/fetch_neiso_smd_zonal_lmp.py --days 2019-01-21 2020-03-08
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import sys
import threading
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

from scripts.data.fetch_neiso_da_energy_offers import _opener  # noqa: E402

RAW_DIR = RAW_DATA_DIR / "lmp-data" / "NEISO" / "smd-zonal-lmp"

REPORT_PAGE = "https://www.iso-ne.com/isoexpress/web/reports/pricing/-/tree/lmp-hourly"
DA_URL = (
    "https://www.iso-ne.com/static-transform/csv/histRpts/da-lmp/"
    "WW_DALMP_ISO_%s.csv"
)
RT_URL = (
    "https://www.iso-ne.com/static-transform/csv/histRpts/rt-lmp/"
    "lmp_rt_final_%s.csv"
)

#: The nine SMD pricing locations, by ISO-NE location id -> SMD sheet name.
#: Keyed on the numeric id rather than the name because the id is the stable
#: identifier in the report; the name is carried through for readability.
SMD_LOCATIONS: dict[str, str] = {
    "4000": "ISO NE CA",
    "4001": "ME",
    "4002": "NH",
    "4003": "VT",
    "4004": "CT",
    "4005": "RI",
    "4006": "SEMA",
    "4007": "WCMA",
    "4008": "NEMA",
}

#: Output column order.  ``seq`` is the 0-based position of the hour within the
#: operating day AS PUBLISHED -- the quantity the chronological clock needs
#: (row k begins exactly k real hours after that day's local midnight), kept
#: explicit so no reader has to re-derive it from the DST-irregular label.
COLUMNS = ("date", "hour_ending", "seq", "location_id", "location", "da_lmp", "rt_lmp")

#: A real all-node hourly report is ~2.4 MB; an unpublished day comes back as a
#: short stub with HTTP 200, the publication-gap pattern the sibling ISO-NE
#: downloaders document.
MIN_REAL_BYTES = 100_000

#: Concurrent workers -- the modest pool size the sibling ISO-NE downloaders
#: settled on (``fetch_neiso_da_energy_offers``: latency-bound per connection,
#: saturates the pipe well before it stresses the endpoint).
DEFAULT_WORKERS = 5


class TransientMiss(Exception):
    """A 404 from the static report tree for an operating day.

    Treated as a retryable serving failure rather than an absent day, per the
    measured behaviour documented in ``fetch_neiso_da_import_export``: the day
    is counted and left unwritten so a re-run picks it up.
    """


def _fetch(opener: urllib.request.OpenerDirector, url: str) -> bytes:
    """Fetch one report CSV, raising :class:`TransientMiss` on a 404."""
    req = urllib.request.Request(url, headers={"Referer": REPORT_PAGE})
    try:
        with opener.open(req, timeout=180) as resp:
            body = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise TransientMiss(url) from None
        raise
    if len(body) < MIN_REAL_BYTES:
        raise RuntimeError(f"short body ({len(body)} B) -- unpublished day? {url}")
    return body


def reduce_report(body: bytes) -> dict[tuple[int, str], tuple[str, float]]:
    """Reduce one daily all-node hourly LMP report to the nine SMD locations.

    Returns ``{(seq, location_id): (hour_ending, lmp)}`` where ``seq`` is the
    0-based position of the hour within the operating day, counted per location
    in publication order. Keying on position rather than on the ``Hour Ending``
    label is what makes the DST days (23 rows in spring, 25 in autumn) carry
    through without a special case.
    """
    out: dict[tuple[int, str], tuple[str, float]] = {}
    seen: dict[str, int] = {}
    for row in csv.reader(io.TextIOWrapper(io.BytesIO(body), encoding="utf-8-sig")):
        if len(row) < 7 or row[0] != "D":
            continue
        loc = row[3]
        if loc not in SMD_LOCATIONS:
            continue
        seq = seen.get(loc, 0)
        seen[loc] = seq + 1
        out[(seq, loc)] = (row[2], float(row[6]))
    missing = set(SMD_LOCATIONS) - {loc for _, loc in out}
    if missing:
        raise RuntimeError(f"report is missing SMD locations {sorted(missing)}")
    return out


def day_rows(opener: urllib.request.OpenerDirector, day: dt.date) -> list[dict]:
    """Fetch and join one operating day's DA and RT-final hourly zonal prices.

    The two markets publish separate reports with the same per-day hour
    sequence; they are joined on ``(seq, location_id)`` and the ``Hour Ending``
    labels are cross-checked, so a silent misalignment between the two files
    fails loudly instead of pairing prices one hour apart.
    """
    stamp = f"{day:%Y%m%d}"
    da = reduce_report(_fetch(opener, DA_URL % stamp))
    rt = reduce_report(_fetch(opener, RT_URL % stamp))
    if da.keys() != rt.keys():
        raise RuntimeError(f"{day}: DA/RT hour grids differ")
    rows = []
    for (seq, loc), (he, da_lmp) in sorted(da.items()):
        rt_he, rt_lmp = rt[(seq, loc)]
        if rt_he != he:
            raise RuntimeError(f"{day} seq {seq} {loc}: DA HE {he} vs RT HE {rt_he}")
        rows.append(
            {
                "date": f"{day:%Y-%m-%d}",
                "hour_ending": he,
                "seq": seq,
                "location_id": loc,
                "location": SMD_LOCATIONS[loc],
                "da_lmp": da_lmp,
                "rt_lmp": rt_lmp,
            }
        )
    return rows


def fetch_days(days: list[dt.date], *, workers: int = DEFAULT_WORKERS) -> list[dict]:
    """Fetch ``days`` through a small pool of independent ISO Express sessions.

    Each worker keeps its own cookie-carrying opener (the endpoint is
    session-scoped) and rebuilds it after an error. Returns every day's rows
    concatenated in chronological order; a day that 404s is reported and
    omitted rather than silently zero-filled.
    """
    local = threading.local()
    lock = threading.Lock()
    got: dict[dt.date, list[dict]] = {}
    missed: list[dt.date] = []
    failed: list[tuple[dt.date, str]] = []

    def one(day: dt.date) -> None:
        if getattr(local, "opener", None) is None:
            local.opener = _opener()
        try:
            rows = day_rows(local.opener, day)
        except TransientMiss:
            with lock:
                missed.append(day)
            return
        except Exception as e:  # transient endpoint hiccups: log and go on
            local.opener = None  # force a fresh session for this worker
            with lock:
                failed.append((day, str(e)))
            return
        with lock:
            got[day] = rows
            if len(got) % 25 == 0:
                print(f"  fetched {len(got)}/{len(days)} days", flush=True)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(one, days))

    for day, err in sorted(failed):
        print(f"ERROR {day}: {err}", flush=True)
    if missed:
        print(f"404 (retryable, re-run to fill): {len(missed)} days", flush=True)
    return [r for day in sorted(got) for r in got[day]]


def write_year_csv(rows: list[dict], year: int, dest_dir: Path | None = None) -> Path:
    """Write one year's reduced zonal series, merging with any existing file.

    Merging on ``(date, location_id)`` makes the script idempotent and lets a
    window be filled in several passes; rows are re-sorted chronologically so
    the file is byte-deterministic regardless of fetch order.
    """
    dest_dir = RAW_DIR if dest_dir is None else dest_dir
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / f"NEISO_smd_zonal_lmp_{year}.csv"
    merged: dict[tuple[str, int, str], dict] = {}
    if path.exists():
        with path.open(newline="") as f:
            for r in csv.DictReader(f):
                r["seq"] = int(r["seq"])
                r["da_lmp"] = float(r["da_lmp"])
                r["rt_lmp"] = float(r["rt_lmp"])
                merged[(r["date"], r["seq"], r["location_id"])] = r
    for r in rows:
        merged[(r["date"], r["seq"], r["location_id"])] = r
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(COLUMNS))
        w.writeheader()
        for key in sorted(merged):
            w.writerow(merged[key])
    return path


def _parse_day(s: str) -> dt.date:
    """Parse a ``YYYY-MM-DD`` command-line date."""
    return dt.date.fromisoformat(s)


def main(argv: list[str] | None = None) -> int:
    """Download and reduce the requested operating days."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=_parse_day, help="first operating day (YYYY-MM-DD)")
    p.add_argument("--end", type=_parse_day, help="last operating day, inclusive")
    p.add_argument(
        "--days", nargs="*", type=_parse_day, default=[], help="explicit day list"
    )
    p.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="destination directory (default: the committed raw home)",
    )
    args = p.parse_args(argv)

    days = list(args.days)
    if args.start or args.end:
        if not (args.start and args.end):
            p.error("--start and --end must be given together")
        if args.end < args.start:
            p.error("--end precedes --start")
        d = args.start
        while d <= args.end:
            days.append(d)
            d += dt.timedelta(days=1)
    if not days:
        p.error("nothing to do: pass --start/--end or --days")
    days = sorted(set(days))

    print(f"fetching {len(days)} operating day(s) x 2 markets", flush=True)
    rows = fetch_days(days, workers=args.workers)
    if not rows:
        print("no rows fetched")
        return 1
    by_year: dict[int, list[dict]] = {}
    for r in rows:
        by_year.setdefault(int(r["date"][:4]), []).append(r)
    for year, yr_rows in sorted(by_year.items()):
        path = write_year_csv(yr_rows, year, dest_dir=args.out_dir)
        days_in = len({r["date"] for r in yr_rows})
        print(f"wrote {path} (+{len(yr_rows)} rows over {days_in} days)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
