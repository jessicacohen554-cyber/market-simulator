"""Fetch CAISO OASIS data for the backcast uploads (U2 hub LMPs, U4 TAC load).

The remote Claude environment cannot reach ``oasis.caiso.com`` (egress
allowlist), and hand-tapping hundreds of OASIS links is impractical, so this
script is meant to be run by the user from an unrestricted machine:

    python scripts/fetch_caiso_oasis.py                 # everything, 2023-2025
    python scripts/fetch_caiso_oasis.py --datasets dam load
    python scripts/fetch_caiso_oasis.py --years 2024

It downloads, per backcast year:

* ``dam``  -- PRC_LMP (DAM, version 12), one query per trading hub
  (TH_NP15/TH_SP15/TH_ZP26 ``_GEN-APND``) per window
  -> ``inputs/raw-data/lmp-data/CAISO/``
* ``rtm``  -- PRC_INTVL_LMP (RTM 5-minute, version 2), same hubs
  -> ``inputs/raw-data/lmp-data/CAISO/``
* ``load`` -- SLD_FCST (market_run_id=ACTUAL, version 1), all TAC areas
  -> ``inputs/raw-data/zone-specific-demand/CAISO/``

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
REPO = Path(__file__).resolve().parent.parent

HUBS = ("TH_NP15_GEN-APND", "TH_SP15_GEN-APND", "TH_ZP26_GEN-APND")

# dataset key -> (query params, output dir, per-node?)
DATASETS: dict[str, dict] = {
    "dam": {
        "params": {"queryname": "PRC_LMP", "market_run_id": "DAM", "version": "12"},
        "out_dir": REPO / "inputs" / "raw-data" / "lmp-data" / "CAISO",
        "per_node": True,
    },
    "rtm": {
        "params": {"queryname": "PRC_INTVL_LMP", "market_run_id": "RTM", "version": "2"},
        "out_dir": REPO / "inputs" / "raw-data" / "lmp-data" / "CAISO",
        "per_node": True,
    },
    "load": {
        "params": {"queryname": "SLD_FCST", "market_run_id": "ACTUAL", "version": "1"},
        "out_dir": REPO / "inputs" / "raw-data" / "zone-specific-demand" / "CAISO",
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
    parts = {"resultformat": "6", **params,
             "startdatetime": _stamp(start), "enddatetime": _stamp(end)}
    if node:
        parts["node"] = node
    return BASE + "?" + "&".join(f"{k}={v}" for k, v in parts.items())


def _fetch(url: str, retries: int = 3, sleep_s: float = 5.0) -> bytes:
    """Download ``url`` with simple exponential-backoff retries."""
    delay = sleep_s
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - network errors of any shape
            if attempt == retries - 1:
                raise
            print(f"    retry after error: {exc}", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


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


def _windows(start: dt.date, end: dt.date, days: int):
    cur = start
    while cur < end:
        nxt = min(cur + dt.timedelta(days=days), end)
        yield cur, nxt
        cur = nxt


def fetch_dataset(key: str, years: list[int], window: int, sleep_s: float) -> None:
    """Fetch one dataset for the given years with adaptive window sizing."""
    spec = DATASETS[key]
    out_dir: Path = spec["out_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes = HUBS if spec["per_node"] else (None,)
    start = dt.date(min(years), 1, 1)
    end = dt.date(max(years) + 1, 1, 1)
    today = dt.date.today()
    end = min(end, today)  # OASIS has no future actuals

    for node in nodes:
        cur = start
        size = window
        while cur < end:
            win_end = min(cur + dt.timedelta(days=size), end)
            tag = f"{key}_{node or 'ALL'}_{cur:%Y%m%d}_{win_end:%Y%m%d}"
            target = out_dir / f"{tag}.csv"
            if target.exists():
                cur = win_end
                continue
            url = _url(spec["params"], cur, win_end, node)
            print(f"  {tag} ...", flush=True)
            payload = _fetch(url, sleep_s=sleep_s)
            time.sleep(sleep_s)
            result = _extract_csv(payload)
            got = _covered_days(result[1]) if result else set()
            need = _expected_days(cur, win_end)
            if result and need <= got:
                target.write_bytes(result[1])
                cur = win_end
                size = window  # reset after success
            elif size > 1:
                size = max(1, size // 2)
                print(f"    incomplete ({len(got)}/{len(need)} days) — "
                      f"halving window to {size}d", flush=True)
            else:
                # single-day window still failing: record and move on
                print(f"    FAILED single-day window {cur} — skipping",
                      file=sys.stderr, flush=True)
                cur = win_end


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--datasets", nargs="+", default=["dam", "rtm", "load"],
                        choices=list(DATASETS))
    parser.add_argument("--years", nargs="+", type=int,
                        default=[2023, 2024, 2025])
    parser.add_argument("--window", type=int, default=25,
                        help="initial window size in days (adaptively halved)")
    parser.add_argument("--sleep", type=float, default=5.0,
                        help="seconds between OASIS requests")
    args = parser.parse_args()

    for key in args.datasets:
        print(f"=== {key} ({DATASETS[key]['params']['queryname']}) ===")
        fetch_dataset(key, args.years, args.window, args.sleep)
    print("done. Commit the new files under inputs/raw-data/ when finished.")


if __name__ == "__main__":
    main()
