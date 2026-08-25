"""Fetch CAISO OASIS data for the backcast uploads (U2 hub LMPs, U4 TAC load).

``oasis.caiso.com`` IS reachable from the remote Claude environment (verified
2026-06-22: PRC_LMP/PRC_INTVL_LMP SingleZip queries return data; the bare
endpoint 403s only because it needs query params). The practical limits are
OASIS's strict rate limiting (HTTP 429/403 under bursts — keep ``--sleep`` high
and back off) and its ~39-month retention.

**The LMP retention boundary moves forward with the calendar** — it is not a
fixed date, and it aged past the whole 2018-2022 holdout window during 2026.
Binary-searched 2026-07-31: the earliest DAM trade date PRC_LMP served was
**2023-04-19**. **Re-binary-searched 2026-08-04 (caiso-165): it has moved to
2023-04-22** — three trade dates lost in four calendar days, which is the
retention window sliding in real time. The boundary is a property of the
*report*, not of the node: ``TH_SP15_GEN-APND`` and ``DLAP_SCE-APND`` both
return ERR_CODE 1000 "No data returned" at 2023-04-19 and both return data at
2023-04-22. Do NOT hardcode a boundary date and trust it — re-measure it, and
use ``--start-date`` to skip the aged-out head of the range rather than
burning ~3 failed requests per day walking into it.

A back-year LMP intake is therefore NOT a fetch task at all — the API cannot
serve it, and the only route to aged-out history is a hand-downloaded GRP bulk
zip (``fold_caiso_oasis_grp_zips.py``). ``AS_REQ`` carries NO such limit: 2018,
2020, 2022 and 2026 all return full data (re-verified 2026-07-31), so the
ancillary-requirement history is fetchable for every year. Run:

    python scripts/data/fetch_caiso_oasis.py                 # everything, 2023-2025
    python scripts/data/fetch_caiso_oasis.py --datasets dam load
    python scripts/data/fetch_caiso_oasis.py --years 2024
    # the caiso-165 DLAP intake (load aggregation points, not the GEN hubs):
    python scripts/data/fetch_caiso_oasis.py --datasets dam --nodes dlaps \
        --start-date 2023-04-22

It downloads, per backcast year:

* ``dam``  -- PRC_LMP (DAM, version 12), one query per node
  (default: the TH_NP15/TH_SP15/TH_ZP26 ``_GEN-APND`` trading hubs; the four
  ``DLAP_*-APND`` load aggregation points via ``--nodes dlaps``) per window
  -> ``data/raw/lmp-data/CAISO/``
* ``rtm``  -- PRC_INTVL_LMP (RTM 5-minute, version 2), same nodes
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
import signal
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

#: The three CAISO trading hubs. These are GENERATION aggregation points: each
#: is a generation-weighted average over the pnodes of its congestion zone, so
#: it prices where power is INJECTED, not where load is served.
HUBS = ("TH_NP15_GEN-APND", "TH_SP15_GEN-APND", "TH_ZP26_GEN-APND")

#: The four CAISO Default Load Aggregation Points. A DLAP is the LOAD-weighted
#: aggregate over the pnodes serving one utility's service territory, so it
#: prices where load is WITHDRAWN — which is what a model load zone represents.
#: ``DLAP_SCE`` is the SCE territory (the LA-basin load pocket), ``DLAP_SDGE``
#: the post-SONGS San Diego pocket behind Path 44, ``DLAP_PGAE`` the PG&E
#: territory (which straddles NP15 and ZP26), ``DLAP_VEA`` the small Valley
#: Electric (NV) member. Present in the committed nodal ``DAM_LMP_GRP`` zips
#: and served by PRC_LMP for every in-retention trade date (caiso-165).
DLAPS = (
    "DLAP_PGAE-APND",
    "DLAP_SCE-APND",
    "DLAP_SDGE-APND",
    "DLAP_VEA-APND",
)

#: ``--nodes`` shorthands. Anything not a shorthand is taken as a literal node.
NODE_SETS: dict[str, tuple[str, ...]] = {
    "hubs": HUBS,
    "dlaps": DLAPS,
    "all": HUBS + DLAPS,
}


def _resolve_nodes(tokens: list[str] | None) -> tuple[str, ...]:
    """Expand ``--nodes`` tokens into a de-duplicated node tuple.

    Each token is either a shorthand from :data:`NODE_SETS` or a literal OASIS
    node id. ``None`` keeps the historical default (the three trading hubs).
    """
    if not tokens:
        return HUBS
    out: list[str] = []
    for tok in tokens:
        for node in NODE_SETS.get(tok, (tok,)):
            if node not in out:
                out.append(node)
    return tuple(out)


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
    # DAM ancillary-service clearing prices (PRC_AS): hourly $/MW marginal
    # price per AS region (AS_CAISO/AS_NP26/AS_SP26 + _EXP variants) and
    # product (SR/NR/RU/RD; RMU/RMD on the EXP region), XML_DATA_ITEM
    # {SP,NS,RU,RD,RMU,RMD}_CLR_PRC with the price in the MW column (OASIS
    # reuses the numeric column name). The measured price leg for the CAISO
    # storage AS-revenue identification (D-9 value-stack lane): battery award
    # MW (data/raw/storage-as-awards) × these prices = measured battery AS
    # revenue. Verified reachable for Jan-2023 (2026-08-25), same retention
    # depth as AS_REQ.
    "asprc": {
        "params": {
            "queryname": "PRC_AS",
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


#: Read timeout per OASIS request. Was 60 s, which is NOT enough: measured
#: 2026-08-04 (caiso-165), a 25-day single-node PRC_LMP window returns in ~4 s
#: in the middle of the retention range but ~21 s within a few weeks of the
#: aged-out boundary, and OASIS additionally *hangs* rather than 429s when it
#: throttles a burst. A 60 s ceiling turned those two effects into spurious
#: "too-large window" verdicts, so the adaptive sizer halved a window that was
#: never too large. Give a slow response room to land; genuine hangs are still
#: bounded by ``retries`` and by :data:`REQUEST_WALL_CLOCK_S`.
REQUEST_TIMEOUT_S = 180

#: Hard wall-clock bound per request, enforced with ``SIGALRM``.
#:
#: ``urlopen(timeout=...)`` is a **per-socket-operation** timeout, not a total
#: one, so a throttled OASIS that trickles bytes indefinitely never trips it:
#: measured 2026-08-04 (caiso-165), a throttled ``resp.read()`` sat for over
#: ten minutes inside a call with ``timeout=180`` and printed no failure,
#: stalling the crawl with no forward progress and no diagnostic. This bound is
#: what makes a throttled request FAIL rather than HANG, so the retry/backoff
#: path can actually run.
REQUEST_WALL_CLOCK_S = 240


class _RequestTimeout(Exception):
    """Raised by the SIGALRM handler when a request exceeds its wall clock."""


def _alarm(_signum, _frame):  # noqa: ANN001 - signal handler signature
    """SIGALRM handler: turn a trickling read into a catchable failure."""
    raise _RequestTimeout(
        f"exceeded {REQUEST_WALL_CLOCK_S}s wall clock (OASIS throttle trickle)"
    )


def _fetch(url: str, retries: int = 3, sleep_s: float = 5.0) -> bytes | None:
    """Download ``url`` with exponential-backoff retries.

    Returns ``None`` instead of raising when every attempt fails (e.g. OASIS
    hangs on a too-large window — observed on 25-day PRC_LMP queries), so the
    caller can shrink the window and continue rather than abort a multi-hour
    crawl.
    """
    delay = sleep_s
    for attempt in range(retries):
        prev = signal.signal(signal.SIGALRM, _alarm)
        signal.alarm(REQUEST_WALL_CLOCK_S)
        try:
            with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_S) as resp:
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
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, prev)
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
    end_date: dt.date | None = None,
    start_date: dt.date | None = None,
    nodes: tuple[str, ...] = HUBS,
    force: bool = False,
) -> None:
    """Fetch one dataset for the given years with adaptive window sizing.

    Stops cleanly (returns) when ``deadline`` (a ``time.monotonic`` value)
    passes, so a CI job can leave time for post-processing and commit.

    ``end_date`` is an exclusive upper bound on the trade dates fetched, so a
    partial year can be pinned to an exact window (e.g. ``2026-07-01`` for the
    H1-2026 holdout edge) instead of running to today's date.

    ``start_date`` is the inclusive lower bound. Its purpose is the moving
    PRC_LMP retention boundary documented in the module docstring: without it a
    fetch whose range starts before the boundary spends ~3 failed requests per
    aged-out day walking the window down to 1 day and back up again.

    ``nodes`` is the node list for per-node datasets (see :func:`_resolve_nodes`).

    ``force`` re-fetches windows the aggregates already cover. The coverage
    check is keyed on ONE reference series (``CA ISO-TAC`` for the load
    report), so once an aggregate exists it reports every day covered even for
    a series that was never kept — which makes back-filling a NEWLY kept series
    impossible without it. That is exactly how ``MWD-TAC`` stayed missing from
    ``CAISO_tac_load_hourly_<year>.csv`` after it was added to
    ``postprocess_oasis_downloads.CAISO_TACS`` (caiso-175). Use it when the
    KEPT SET widens, not to re-pull data already on disk.
    """
    spec = DATASETS[key]
    out_dir: Path = spec["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes = nodes if spec["per_node"] else (None,)
    start = dt.date(min(years), 1, 1)
    end = dt.date(max(years) + 1, 1, 1)
    today = dt.date.today()
    end = min(end, today)  # OASIS has no future actuals
    if end_date is not None:
        end = min(end, end_date)
    if start_date is not None:
        start = max(start, start_date)

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
            if target.exists() or (not force and need <= done_days):
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
    parser.add_argument(
        "--end-date",
        type=dt.date.fromisoformat,
        default=None,
        help="exclusive upper bound on trade dates (YYYY-MM-DD); pins a "
        "partial year to an exact window, e.g. 2026-07-01 for H1-2026",
    )
    parser.add_argument(
        "--start-date",
        type=dt.date.fromisoformat,
        default=None,
        help="inclusive lower bound on trade dates (YYYY-MM-DD); use it to "
        "skip the aged-out head of the PRC_LMP retention window "
        "(2023-04-22 as re-measured 2026-08-04 — it MOVES, so re-check)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="re-fetch windows the hourly aggregates already cover. Needed "
        "only when the KEPT SERIES SET widens (the coverage check reads one "
        "reference series, so a newly kept series can never be back-filled "
        "without it) — not for re-pulling data already on disk",
    )
    parser.add_argument(
        "--nodes",
        nargs="+",
        default=None,
        help="nodes for per-node datasets: the shorthands "
        f"{sorted(NODE_SETS)} or literal OASIS node ids (default: hubs)",
    )
    args = parser.parse_args()
    nodes = _resolve_nodes(args.nodes)

    deadline = (
        time.monotonic() + args.deadline_minutes * 60.0
        if args.deadline_minutes
        else None
    )
    for key in args.datasets:
        print(f"=== {key} ({DATASETS[key]['params']['queryname']}) ===")
        if DATASETS[key]["per_node"]:
            print(f"    nodes: {', '.join(nodes)}")
        fetch_dataset(
            key,
            args.years,
            args.window,
            args.sleep,
            deadline,
            args.end_date,
            args.start_date,
            nodes,
            args.force,
        )
    print("done. Commit the new files under data/raw/ when finished.")


if __name__ == "__main__":
    main()
