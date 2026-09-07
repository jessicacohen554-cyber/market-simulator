#!/usr/bin/env python3
"""Fetch CAISO OASIS *GroupZip* all-node LMP bulk archives and fold them in place.

WHY THIS EXISTS (caiso-261, 2026-09-06). The per-node OASIS API
(``SingleZip?queryname=PRC_LMP`` / ``PRC_INTVL_LMP``) has a moving ~39-month
retention window that aged past 2022 during 2026 (``fetch_caiso_oasis.py``
docstring). The **GroupZip** all-node bulk endpoint does NOT share that limit:
measured 2026-09-06, ``GroupZip?groupid=DAM_LMP_GRP&startdatetime=20220601T07:00-0000
&version=12`` returns the full 2022-06-01 archive (12.3 MB, four component
files LMP/MCE/MCC/MCL, every node), and a re-download of the 2023-01-01 DAM
archive reproduces the byte-pinned file in ``data/raw/lmp-data/CAISO/
SHA256SUMS.txt`` **sha256-identical** (``6523fedd...``). That makes GroupZip the
primary-publisher route to the 2022 hub / DLAP / intertie prices the 2022
validation touchpoint needs (rule 22; charter
``docs/handoffs/caiso-2022-price-archive-intake-charter-2026-09.md``), with
rule-14 alignment exact: same reports, nodes, components and downstream chain as
2023-2025.

WHAT IT DOES. For each trade date in ``[--start, --end]``:

1. ``GET GroupZip`` for the market's group, with the request instant expressed
   in UTC — the request a browser download makes, and what reproduced the
   pinned bytes.

   * **DAM** (``DAM_LMP_GRP`` version 12): ONE request per trade date, at the
     trade date's LOCAL midnight (08:00 PST / 07:00 PDT).
   * **RTM** (``RTM_LMP_GRP`` version 3): OASIS serves this report **one
     OPERATING HOUR per request** — measured 2026-09-07 on 2022-06-01
     (caiso-262 §2.2): 24 requests returned 24 distinct archives, group index
     ``01``…``24`` tracking ``OPR_HR`` exactly, each 8.3–9.1 MB with the hour's
     12 five-minute intervals over ~16.6k nodes. (The claim in the intake
     charter and ``data/raw/lmp-data/CAISO/README.md`` that ``version=3`` was
     "7 groups/day" was a miscount of how many hours had been hand-downloaded
     on some January-2023 dates; the tracked ``SHA256SUMS.txt`` carries group
     indices ``01``…``24``. Corrected here by measurement.) So the crawl walks
     the trade date's LOCAL HOURS **as instants** — local midnight to the next
     local midnight, stepping one hour — which is what makes the DST days come
     out right on their own: 2022-03-13 issues 23 requests and 2022-11-06
     issues 25, where a fixed ``range(24)`` would silently drop or duplicate an
     hour.

2. Saves each zip under its ``Content-Disposition`` filename in
   ``data/raw/lmp-data/CAISO/`` (gitignored there by pattern), so
   :mod:`scripts.data.fold_caiso_oasis_grp_zips` recognises it.
3. Folds the trade date ONCE, after every one of its groups is on disk
   (``fold_caiso_oasis_grp_zips.fold``), into the per-day node window CSV
   ``{market}_grp_{Ymd}_{Ymd}.csv`` (hubs + DLAPs + the WECC intertie nodes
   only), then DELETES the zips — extract-and-discard, so a full year costs a
   few hundred MB of disk rather than 4.4 GB (DAM) / 77 GB (RTM). Folding
   per-zip would be WRONG for a multi-group market: ``fold`` skips a window
   whose CSV already exists, so the day would be written from its first hour
   alone and hours 02-24 dropped silently.

Resumable at both grains: a date whose window CSV already exists is skipped,
and within a date an hour whose zip is already on disk is not re-fetched (so an
interrupted day resumes rather than re-downloading). Rate limit: ``--sleep``
seconds **between request starts** (an interval floor, not idle time added
after each response — the OASIS acceptable-use throttle is a request-RATE
limit, ~1 request / 5 s, and returns HTTP 200 with an HTML "Acceptable Use
Policy Violation" body when exceeded, detected here by the missing zip magic
and backed off). Exponential back-off on any failure, at most ``--retries``
attempts per request, then the group is recorded MISSING in the summary and the
crawl continues.

Downstream (run by hand, in this order, after the crawl):
``postprocess_oasis_downloads.py --stage-dir <scratch>`` folds the windows into
``CAISO_dam_hourly_<year>.csv`` (then restrict the new year to the same node
set the other years carry — the aggregates hold the 3 hubs + 4 DLAPs; the
intertie nodes go to the intertie parquet instead), and
``fetch_caiso_intertie_lmp.py --from-grp-windows`` builds the MALIN / PALOVRDE
delivered-LMP rows for ``wecc_intertie_lmp_hourly_CAISO.parquet``.

Usage::

    PYTHONPATH=.:src uv run python scripts/data/fetch_caiso_oasis_grp.py \
        --market dam --start 2022-01-01 --end 2022-12-31 --sleep 6
    PYTHONPATH=.:src uv run python scripts/data/fetch_caiso_oasis_grp.py \
        --market rtm --start 2022-01-01 --end 2022-12-31 --sleep 7
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.fetch_caiso_oasis import _oasis_error  # noqa: E402
from scripts.data.fold_caiso_oasis_grp_zips import LMP_DIR, fold  # noqa: E402

BASE = "https://oasis.caiso.com/oasisapi/GroupZip"
CAISO_TZ = ZoneInfo("America/Los_Angeles")
#: OASIS group ids and report versions per market — the versions the tracked
#: corpus was built with (``README.md``: DAM ``v12``, RTM ``v3``). ``hourly``
#: says the report is served one OPERATING HOUR per request, so a trade date
#: costs one request per local hour rather than one request (module docstring
#: step 1, measured caiso-262 §2.2).
MARKETS = {
    "dam": {"groupid": "DAM_LMP_GRP", "version": "12", "hourly": False},
    "rtm": {"groupid": "RTM_LMP_GRP", "version": "3", "hourly": True},
}
_CD_NAME = re.compile(r'filename="?([^";]+)"?')
REQUEST_TIMEOUT_S = 300


def _start_utc(day: dt.date) -> str:
    """The trade date's local midnight as an OASIS ``startdatetime`` (UTC)."""
    local = dt.datetime(day.year, day.month, day.day, tzinfo=CAISO_TZ)
    return local.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H:%M-0000")


def _local_hours(day: dt.date) -> list[dt.datetime]:
    """Every operating-hour start of a trade date, as aware local instants.

    Walks local midnight to the NEXT local midnight one hour at a time, so the
    count is the day's true operating-hour count without a DST special case:
    23 on the spring-forward date, 25 on the fall-back date, 24 otherwise.
    Arithmetic is done in UTC and converted back, because adding a timedelta to
    a zone-aware local datetime keeps the old UTC offset across a transition.
    """
    start = dt.datetime(day.year, day.month, day.day, tzinfo=CAISO_TZ)
    nxt = day + dt.timedelta(days=1)
    end = dt.datetime(nxt.year, nxt.month, nxt.day, tzinfo=CAISO_TZ)
    hours: list[dt.datetime] = []
    cur = start.astimezone(dt.timezone.utc)
    stop = end.astimezone(dt.timezone.utc)
    while cur < stop:
        hours.append(cur.astimezone(CAISO_TZ))
        cur += dt.timedelta(hours=1)
    return hours


def _is_error_zip(payload: bytes) -> bool:
    """True when the zip is an OASIS error envelope (an XML member, no CSV)."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            names = [n.lower() for n in zf.namelist()]
    except zipfile.BadZipFile:
        return True
    return not any(n.endswith(".csv") for n in names)


def _fetch_zip(url: str, retries: int, sleep_s: float) -> tuple[bytes, str] | None:
    """Download one GroupZip; returns ``(payload, filename)`` or ``None``."""
    delay = max(sleep_s, 5.0)
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_S) as resp:
                payload = resp.read()
                cd = resp.headers.get("Content-Disposition", "") or ""
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(
                f"    attempt {attempt}/{retries} failed: {exc}",
                file=sys.stderr,
                flush=True,
            )
            payload, cd = b"", ""
        if payload[:2] == b"PK":
            if _is_error_zip(payload):
                err = _oasis_error(payload)
                print(f"    OASIS error: {err}", file=sys.stderr, flush=True)
                return None  # a definitive "no data" — do not retry
            m = _CD_NAME.search(cd)
            return payload, (m.group(1) if m else "")
        if payload:
            head = payload[:200].decode("utf-8", "replace").replace("\n", " ")
            print(
                f"    non-zip body (AUP throttle?): {head[:120]}",
                file=sys.stderr,
                flush=True,
            )
        if attempt < retries:
            time.sleep(delay)
            delay = min(delay * 2, 600.0)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--market", choices=sorted(MARKETS), default="dam")
    ap.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2022, 1, 1))
    ap.add_argument("--end", type=dt.date.fromisoformat, default=dt.date(2022, 12, 31))
    ap.add_argument("--sleep", type=float, default=6.0, help="seconds between requests")
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument(
        "--keep-zips",
        action="store_true",
        help="leave the bulk zips on disk after folding",
    )
    ap.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="JSON summary path (fetched / skipped / missing dates)",
    )
    args = ap.parse_args()
    spec = MARKETS[args.market]
    LMP_DIR.mkdir(parents=True, exist_ok=True)

    fetched: list[str] = []
    skipped: list[str] = []
    missing: list[str] = []
    partial: dict[str, list[str]] = {}  # trade date -> the groups it never got
    total_bytes = 0
    day = args.start
    t0 = time.monotonic()
    # Interval floor between request STARTS (see the module docstring): the AUP
    # limit is a request rate, so pacing start-to-start honours it exactly
    # while sleeping the FULL --sleep after each response would idle ~6 s on
    # top of a ~6 s download and roughly double an 8,760-request crawl.
    next_start = 0.0

    def _paced_fetch(url: str) -> tuple[bytes, str] | None:
        nonlocal next_start
        wait = next_start - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        next_start = time.monotonic() + args.sleep
        return _fetch_zip(url, args.retries, args.sleep)

    while day <= args.end:
        ymd = day.strftime("%Y%m%d")
        window = LMP_DIR / f"{args.market}_grp_{ymd}_{ymd}.csv"
        if window.exists():
            skipped.append(ymd)
            day += dt.timedelta(days=1)
            continue
        # One request per operating hour for an hourly-served group, else one
        # for the whole trade date. Every group is on disk BEFORE the fold, so
        # the day's window carries all of its hours (see docstring step 3).
        starts = (
            [
                h.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H:%M-0000")
                for h in _local_hours(day)
            ]
            if spec["hourly"]
            else [_start_utc(day)]
        )
        print(
            f"{ymd}: GET {spec['groupid']} v{spec['version']} ({len(starts)} group(s))",
            flush=True,
        )
        zpaths: list[Path] = []
        lost: list[str] = []
        day_bytes = 0
        for idx, start in enumerate(starts, start=1):
            probe = LMP_DIR / (
                f"{ymd}_{ymd}_{spec['groupid']}_{idx:02d}_N_v{spec['version']}_csv.zip"
            )
            if probe.exists():  # resumed day — this group is already on disk
                zpaths.append(probe)
                continue
            url = (
                f"{BASE}?groupid={spec['groupid']}&startdatetime={start}"
                f"&version={spec['version']}&resultformat=6"
            )
            got = _paced_fetch(url)
            if got is None:
                lost.append(f"{idx:02d}")
                print(f"{ymd} grp {idx:02d}: MISSING", flush=True)
                continue
            payload, name = got
            if not name:
                suffix = f"{idx:02d}" if spec["hourly"] else "N"
                name = (
                    f"{ymd}_{ymd}_{spec['groupid']}_{suffix}_N"
                    f"_v{spec['version']}_csv.zip"
                )
            zpath = LMP_DIR / name
            zpath.write_bytes(payload)
            zpaths.append(zpath)
            day_bytes += len(payload)
        total_bytes += day_bytes
        if not zpaths:
            missing.append(ymd)
            print(f"{ymd}: MISSING (no group returned)", flush=True)
            day += dt.timedelta(days=1)
            continue
        written = fold((args.market,))
        if not args.keep_zips:
            for zpath in zpaths:
                zpath.unlink(missing_ok=True)
        ok = window.exists()
        if lost:
            partial[ymd] = lost
        print(
            f"{ymd}: {len(zpaths)}/{len(starts)} group(s), "
            f"{day_bytes / 1e6:.1f} MB -> "
            f"{'window ' + window.name if ok else 'NO WINDOW'} "
            f"({len(written)} written; {time.monotonic() - t0:.0f}s elapsed)",
            flush=True,
        )
        (fetched if ok else missing).append(ymd)
        day += dt.timedelta(days=1)

    summary = {
        "market": args.market,
        "groupid": spec["groupid"],
        "version": spec["version"],
        "hourly_groups": spec["hourly"],
        "start": args.start.isoformat(),
        "end": args.end.isoformat(),
        "fetched": len(fetched),
        "skipped_existing": len(skipped),
        "missing": missing,
        "partial_dates": partial,
        "transferred_gb": round(total_bytes / 1e9, 3),
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    print(json.dumps(summary, indent=1), flush=True)
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
