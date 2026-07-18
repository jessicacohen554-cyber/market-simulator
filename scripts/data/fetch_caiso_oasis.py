"""Fetch CAISO OASIS data for the backcast uploads (U2 hub LMPs, U4 TAC load).

``oasis.caiso.com`` IS reachable from the remote Claude environment (verified
2026-06-22: PRC_LMP/PRC_INTVL_LMP SingleZip queries return data; the bare
endpoint 403s only because it needs query params). The practical limits are
OASIS's strict rate limiting (HTTP 429/403 under bursts — keep ``--sleep`` high
and back off) and its ~39-month retention: as of mid-2026 DAM/RTM before
~2023-03-10 is aged out (ERR 1000), so 2023 is only fetchable Mar-Dec. Run:

    python scripts/data/fetch_caiso_oasis.py                 # everything, 2023-2025
    python scripts/data/fetch_caiso_oasis.py --datasets dam load
    python scripts/data/fetch_caiso_oasis.py --years 2024

It downloads, per backcast year:

* ``dam``  -- PRC_LMP (DAM, version 12), one query per trading hub
  (TH_NP15/TH_SP15/TH_ZP26 ``_GEN-APND``) per window
  -> ``data/raw/lmp-data/CAISO/``
* ``rtm``  -- PRC_INTVL_LMP (RTM 5-minute, version 2), same hubs
  -> ``data/raw/lmp-data/CAISO/``
* ``load`` -- SLD_FCST (market_run_id=ACTUAL, version 1), all TAC areas
  -> ``data/raw/zone-specific-demand/CAISO/``

OASIS quirks this script works around (observed 2026-06-11):

* Multi-node LMP queries are silently truncated to the last ~2 trade dates
  (CAISO's own FAQ examples for multi-node queries span a single day), so
  every LMP query here is **single-node**.
* A 31-day multi-node window returned ``ERR_CODE 1000`` outright. Window
  sizing is therefore **adaptive**: start at ``--window`` days (default 25)
  and halve on truncation/error until the response covers the request.
* Rate limit: ``--sleep`` seconds between requests (default 5).
* Responses are zips; an error response is a small zip holding an XML with
  ``<m:ERROR>``. Extracted CSVs are written next to each other; existing
  target CSVs make the window be skipped, so reruns resume where they left
  off.

Requires only the Python standard library.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import re
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://oasis.caiso.com/oasisapi/SingleZip"
REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402  (resolves the data root)

# Paths resolve through config/paths.py — the W1 relocation collapsed the legacy
# inputs/raw-data tree into data/raw.
_LMP_DIR = paths.RAW_DATA_DIR / "lmp-data" / "CAISO"
_LOAD_DIR = paths.RAW_DATA_DIR / "zone-specific-demand" / "CAISO"

HUBS = ("TH_NP15_GEN-APND", "TH_SP15_GEN-APND", "TH_ZP26_GEN-APND")

# dataset key -> (query params, output dir, per-node?)
DATASETS: dict[str, dict] = {
    "dam": {
        "params": {"queryname": "PRC_LMP", "market_run_id": "DAM", "version": "12"},
        "out_dir": _LMP_DIR,
        "per_node": True,
    },
    "rtm": {
        "params": {
            "queryname": "PRC_INTVL_LMP",
            "market_run_id": "RTM",
            "version": "2",
        },
        "out_dir": _LMP_DIR,
        "per_node": True,
    },
    "load": {
        "params": {"queryname": "SLD_FCST", "market_run_id": "ACTUAL", "version": "1"},
        "out_dir": _LOAD_DIR,
        "per_node": False,
    },
    # DAM ancillary-service regional requirements (AS_REQ): hourly MW minimum/
    # maximum per AS region (AS_CAISO/AS_SP26/AS_NP26 + _EXP variants) and
    # product (SR/NR/RU/RD). The regional MINIMUM is the locational
    # must-procure-in-region floor — the measured driver for the CAISO
    # sub-regional reserve families (caiso-70 FINDING probe-#2 redirect).
    # Verified reachable for Jan-2023 (2026-07-10), so AS_REQ retention
    # reaches further back than the DAM/RTM LMP ~39-month ageout noted above.
    "asreq": {
        "params": {
            "queryname": "AS_REQ",
            "market_run_id": "DAM",
            "version": "1",
            "anc_type": "ALL",
            "anc_region": "ALL",
        },
        "out_dir": paths.RAW_DATA_DIR / "CAISO-AS",
        "per_node": False,
    },
    # DAM ancillary-service market results (AS_RESULTS): hourly procured MW per
    # AS region and product — RESULT_TYPE AS_MW (total = market + self),
    # AS_BUY_MW (market-procured), AS_SELF_MW (self-provided), AS_COST.
    # XML_DATA_ITEM {SP,NS,RU,RD,RMU,RMD}_{TOT,SPROC,PROC}_MW. The measured
    # TOTAL-procurement denominator (all resource types): the battery-held
    # award itself comes from the Daily Energy Storage Report intake
    # (data/raw/storage-as-awards, caiso_storage_as_reservation), so this
    # dataset is a cross-check / battery-share denominator and the eventual
    # measured replacement for the as_reserve_formula scaffold. Verified
    # reachable and complete-format for Jul-2024 (2026-07-11); not yet
    # fetched in bulk.
    "asresults": {
        "params": {
            "queryname": "AS_RESULTS",
            "market_run_id": "DAM",
            "version": "1",
            "anc_type": "ALL",
            "anc_region": "ALL",
        },
        "out_dir": paths.RAW_DATA_DIR / "CAISO-AS",
        "per_node": False,
    },
}

# OASIS datetimes are UTC; 08:00 UTC == midnight PST, so windows tile the
# PST calendar without gaps.
UTC_OFFSET_HOURS = 8


def _stamp(day: dt.date) -> str:
    """Return the OASIS UTC datetime string for PST-midnight of ``day``."""
    return f"{day:%Y%m%d}T{UTC_OFFSET_HOURS:02d}:00-0000"


def _url(params: dict, start: dt.date, end: dt.date, node: str | None) -> str:
    parts = {
        "resultformat": "6",
        **params,
        "startdatetime": _stamp(start),
        "enddatetime": _stamp(end),
    }
    if node:
        parts["node"] = node
    return BASE + "?" + "&".join(f"{k}={v}" for k, v in parts.items())


def _fetch(url: str, retries: int = 3, sleep_s: float = 5.0) -> bytes | None:
    """Download ``url`` with exponential-backoff retries.

    Returns ``None`` instead of raising when every attempt fails (e.g. OASIS
    hangs on a too-large window — observed on 25-day PRC_LMP queries), so the
    caller can shrink the window and continue rather than abort a multi-hour
    crawl.
    """
    delay = sleep_s
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - network errors of any shape
            print(
                f"    attempt {attempt + 1}/{retries} failed: {exc}",
                file=sys.stderr,
                flush=True,
            )
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
    return None


def _oasis_error(payload: bytes) -> str:
    """Return the ERR_DESC from an OASIS XML error payload, if any."""
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as zf:
            for name in zf.namelist():
                if name.lower().endswith(".xml"):
                    m = re.search(rb"<m:ERR_DESC>([^<]*)</m:ERR_DESC>", zf.read(name))
                    if m:
                        return m.group(1).decode(errors="replace")
    except Exception:  # noqa: BLE001 - diagnostic only
        pass
    return "unknown"


def _extract_csv(payload: bytes) -> tuple[str, bytes] | None:
    """Return ``(name, data)`` for the CSV inside an OASIS zip.

    Returns ``None`` when the zip holds an OASIS XML error response
    (``ERR_CODE`` / "No data returned") instead of data.
    """
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        names = zf.namelist()
        csvs = [n for n in names if n.lower().endswith(".csv")]
        if not csvs:
            return None  # XML error payload
        name = csvs[0]
        return name, zf.read(name)


def _covered_days(csv_data: bytes) -> set[str]:
    """Return the set of OPR_DT values present in an OASIS CSV.

    OPR_DT is a bare comma-delimited date column; the interval timestamps
    (``2023-02-27T11:00:00-00:00``) don't match the comma-bounded pattern.
    """
    return {m.decode() for m in re.findall(rb",(\d{4}-\d{2}-\d{2}),", csv_data)}


def _expected_days(start: dt.date, end: dt.date) -> set[str]:
    return {str(start + dt.timedelta(days=i)) for i in range((end - start).days)}


def _aggregate_covered_days(out_dir: Path, key: str, node: str | None) -> set[str]:
    """Return days already covered by this dataset's hourly aggregate files.

    ``scripts/data/postprocess_oasis_downloads.py`` folds raw window CSVs into
    per-year hourly aggregates (``CAISO_{key}_hourly_{year}.csv``) and stages
    the raws out of the repo, so on a fresh checkout the aggregates are the
    only record of what was already fetched. A day counts as covered when the
    reference series (the requested node, or ``CA ISO-TAC`` for the load
    report) has at least 23 hourly rows (DST-short days have 23).
    """
    ref = node or "CA ISO-TAC"
    counts: dict[dt.date, int] = {}
    stamp = re.compile(rb"(\d{4})-(\d{2})-(\d{2})[ T](\d{2})")
    for path in sorted(out_dir.glob(f"CAISO_{key}_hourly_*.csv")):
        with open(path, "rb") as fh:
            for line in fh:
                if ref.encode() not in line:
                    continue
                m = stamp.search(line)
                if not m:
                    continue
                y, mo, d, h = (int(g) for g in m.groups())
                # Aggregate timestamps are GMT; shift back to the PST trade
                # date the fetch windows are expressed in.
                trade = (
                    dt.datetime(y, mo, d, h) - dt.timedelta(hours=UTC_OFFSET_HOURS)
                ).date()
                counts[trade] = counts.get(trade, 0) + 1
    return {str(day) for day, n in counts.items() if n >= 23}


def _windows(start: dt.date, end: dt.date, days: int):
    cur = start
    while cur < end:
        nxt = min(cur + dt.timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def fetch_dataset(
    key: str,
    years: list[int],
    window: int,
    sleep_s: float,
    deadline: float | None = None,
) -> None:
    """Fetch one dataset for the given years with adaptive window sizing.

    Stops cleanly (returns) when ``deadline`` (a ``time.monotonic`` value)
    passes, so a CI job can leave time for post-processing and commit.
    """
    spec = DATASETS[key]
    out_dir: Path = spec["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes = HUBS if spec["per_node"] else (None,)
    start = dt.date(min(years), 1, 1)
    end = dt.date(max(years) + 1, 1, 1)
    today = dt.date.today()
    end = min(end, today)  # OASIS has no future actuals

    for node in nodes:
        done_days = _aggregate_covered_days(out_dir, key, node)
        cur = start
        size = window
        while cur < end:
            if deadline is not None and time.monotonic() > deadline:
                print(f"  deadline reached — stopping {key} cleanly", flush=True)
                return
            win_end = min(cur + dt.timedelta(days=size), end)
            tag = f"{key}_{node or 'ALL'}_{cur:%Y%m%d}_{win_end:%Y%m%d}"
            target = out_dir / f"{tag}.csv"
            need = _expected_days(cur, win_end)
            if target.exists() or need <= done_days:
                cur = win_end
                continue
            url = _url(spec["params"], cur, win_end, node)
            print(f"  {tag} ...", flush=True)
            payload = _fetch(url, sleep_s=sleep_s)
            time.sleep(sleep_s)
            result = _extract_csv(payload) if payload is not None else None
            got = _covered_days(result[1]) if result else set()
            if result and need <= got:
                target.write_bytes(result[1])
                cur = win_end
                # AIMD window sizing: grow gently after success instead of
                # resetting to the maximum — OASIS hangs on windows past its
                # per-report limit, and reprobing the max on every success
                # would waste ~5 requests per window.
                size = min(window, size * 2)
            elif size > 1:
                size = max(1, size // 2)
                reason = (
                    "no response"
                    if payload is None
                    else f"OASIS: {_oasis_error(payload)}"
                    if result is None
                    else f"{len(got)}/{len(need)} days"
                )
                print(
                    f"    incomplete ({reason}) — halving window to {size}d", flush=True
                )
            else:
                # Single-day window still failing: skip the day. Persistent
                # runs of these at the start of the range usually mean the
                # data has aged out of OASIS retention (~39 months).
                reason = (
                    "no response"
                    if payload is None
                    else f"OASIS: {_oasis_error(payload)}"
                    if result is None
                    else "wrong days returned"
                )
                print(
                    f"    FAILED single-day window {cur} ({reason}) — skipping",
                    file=sys.stderr,
                    flush=True,
                )
                cur = win_end


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--datasets", nargs="+", default=["dam", "rtm", "load"], choices=list(DATASETS)
    )
    parser.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    parser.add_argument(
        "--window",
        type=int,
        default=25,
        help="initial window size in days (adaptively halved)",
    )
    parser.add_argument(
        "--sleep", type=float, default=5.0, help="seconds between OASIS requests"
    )
    parser.add_argument(
        "--deadline-minutes",
        type=float,
        default=None,
        help="stop fetching cleanly after this many minutes "
        "(for CI jobs with a hard timeout)",
    )
    args = parser.parse_args()

    deadline = (
        time.monotonic() + args.deadline_minutes * 60.0
        if args.deadline_minutes
        else None
    )
    for key in args.datasets:
        print(f"=== {key} ({DATASETS[key]['params']['queryname']}) ===")
        fetch_dataset(key, args.years, args.window, args.sleep, deadline)
    print("done. Commit the new files under data/raw/ when finished.")


if __name__ == "__main__":
    main()
