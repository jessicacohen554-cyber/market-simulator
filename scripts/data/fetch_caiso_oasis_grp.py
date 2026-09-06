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

1. ``GET GroupZip`` for the market's group (``DAM_LMP_GRP`` version 12, one
   request per trade date; ``RTM_LMP_GRP`` version 3, which OASIS serves as
   several hour-group zips per day — see ``--rtm-groups``), with the trade
   date's LOCAL midnight expressed in UTC (08:00 PST / 07:00 PDT), which is the
   request a browser download makes and what reproduced the pinned bytes.
2. Saves the zip under its ``Content-Disposition`` filename in
   ``data/raw/lmp-data/CAISO/`` (gitignored there by pattern), so
   :mod:`scripts.data.fold_caiso_oasis_grp_zips` recognises it.
3. Folds it immediately (``fold_caiso_oasis_grp_zips.fold``) into the per-day
   node window CSV ``{market}_grp_{Ymd}_{Ymd}.csv`` (hubs + DLAPs + the WECC
   intertie nodes only), then DELETES the zip — extract-and-discard, so a
   full year costs a few MB of disk rather than 4.4 GB.

Resumable: a date whose window CSV already exists is skipped. Rate limit:
``--sleep`` seconds between requests (OASIS's acceptable-use throttle returns
HTTP 200 with an HTML "Acceptable Use Policy Violation" body when polled
faster than ~1 request / 5 s — detected by the missing zip magic and backed
off), exponential back-off on any failure, at most ``--retries`` attempts per
request, then the date is recorded as MISSING in the summary and the crawl
continues.

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
#: corpus was built with (``README.md``: DAM ``v12``, RTM ``v3``).
MARKETS = {
    "dam": {"groupid": "DAM_LMP_GRP", "version": "12"},
    "rtm": {"groupid": "RTM_LMP_GRP", "version": "3"},
}
_CD_NAME = re.compile(r'filename="?([^";]+)"?')
REQUEST_TIMEOUT_S = 300


def _start_utc(day: dt.date) -> str:
    """The trade date's local midnight as an OASIS ``startdatetime`` (UTC)."""
    local = dt.datetime(day.year, day.month, day.day, tzinfo=CAISO_TZ)
    return local.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H:%M-0000")


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
    day = args.start
    t0 = time.monotonic()
    while day <= args.end:
        ymd = day.strftime("%Y%m%d")
        window = LMP_DIR / f"{args.market}_grp_{ymd}_{ymd}.csv"
        if window.exists():
            skipped.append(ymd)
            day += dt.timedelta(days=1)
            continue
        url = (
            f"{BASE}?groupid={spec['groupid']}&startdatetime={_start_utc(day)}"
            f"&version={spec['version']}&resultformat=6"
        )
        print(f"{ymd}: GET {spec['groupid']} v{spec['version']}", flush=True)
        got = _fetch_zip(url, args.retries, args.sleep)
        if got is None:
            missing.append(ymd)
            print(f"{ymd}: MISSING", flush=True)
        else:
            payload, name = got
            if not name:
                name = f"{ymd}_{ymd}_{spec['groupid']}_N_N_v{spec['version']}_csv.zip"
            zpath = LMP_DIR / name
            zpath.write_bytes(payload)
            written = fold((args.market,))
            if not args.keep_zips:
                zpath.unlink(missing_ok=True)
            ok = window.exists()
            print(
                f"{ymd}: {len(payload) / 1e6:.1f} MB -> "
                f"{'window ' + window.name if ok else 'NO WINDOW'} "
                f"({len(written)} written; {time.monotonic() - t0:.0f}s elapsed)",
                flush=True,
            )
            (fetched if ok else missing).append(ymd)
        day += dt.timedelta(days=1)
        time.sleep(args.sleep)

    summary = {
        "market": args.market,
        "groupid": spec["groupid"],
        "version": spec["version"],
        "start": args.start.isoformat(),
        "end": args.end.isoformat(),
        "fetched": len(fetched),
        "skipped_existing": len(skipped),
        "missing": missing,
        "elapsed_s": round(time.monotonic() - t0, 1),
    }
    print(json.dumps(summary, indent=1), flush=True)
    if args.summary:
        args.summary.write_text(json.dumps(summary, indent=1) + "\n")


if __name__ == "__main__":
    main()
