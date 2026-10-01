"""Fetch CAISO OASIS ``TRNS_USAGE`` (DAM) intertie transmission ratings + usage.

``TRNS_USAGE`` publishes, per intertie scheduling constraint (``TI_ID``, the
ITC/ISL names CAISO schedules imports/exports against) and direction
(``I`` import / ``E`` export), hourly DAM values for thirteen items:

====================  ============================================
``TTC_MW``            Seasonal TTC (path rating)
``OTC_MW``            Hourly TTC (the operating transfer capability)
``TRM_MW``            Total TRM (= UF + FTO + SPI components below)
``TRM_UF_MW``         TRM — unscheduled flow
``TRM_FTO_MW``        TRM — forced topology outages
``TRM_SPI_MW``        TRM — simultaneous path interaction
``CBM_MW``            CBM
``MKT_XFER_CAP_MW``   Market transfer capability (what IFM enforces)
``CONSTRAINT_MW``     Constraint
``ENE_IMPORT_MW``     Scheduled net energy from imports/exports
``AS_IMPORT_MW``      AS from imports
``USEAGE_MW``         Hourly unscheduled TR capacity
``ATC_MW``            ATC
====================  ============================================

``99999`` is OASIS's "unlimited" sentinel (the CISO_NET_* aggregate ITCs)
and is kept verbatim here; the curation layer decides how to treat it.

**Retention rolls.** OASIS serves ~39 months. Measured 2026-10-01 (R-CAISO-30):
the earliest DAM trade date served was **2023-06-19** (2023-06-17 and 2023-06-18 returned
ERR_CODE 1000 "No data returned"); every earlier day is gone from the API and
the boundary advances one day per calendar day. This is why the fold below is
COMMITTED: once a month ages out, the committed parquet is the only copy.

**Windows sit on Pacific-day boundaries** — local midnight in
America/Los_Angeles, i.e. 07Z in PDT months and 08Z in PST months. An 08Z
start in a PDT month returns an empty zip (R-CAISO-29 tip). Each window's
start AND end are converted from local midnight, so a window may straddle a
DST change.

Two stages, both idempotent:

* fetch -- one ``SingleZip`` per ``--window``-day window (default 11, ~2 MB
  zip / ~55 MB CSV) -> a lossless WIDE parquet per window under
  ``data/raw/caiso-trns-usage/windows/`` (gitignored staging; an existing
  window file is skipped, so reruns resume).
* ``--fold`` -- concatenates the window files into one committed parquet per
  operating year, ``data/raw/caiso-trns-usage/caiso_trns_usage_dam_<year>.parquet``,
  and rewrites ``SHA256SUMS.txt``.

The WIDE reshape is lossless for the source's information content: key
(``interval_start_utc``, ``ti_id``, ``ti_constraint_id``, ``direction``) plus
one float column per ``XML_DATA_ITEM``. The dropped CSV columns are either
derivable (``OPR_DT``/``OPR_HR``/``INTERVALENDTIME_GMT`` from the UTC start),
constant for this query (``MARKET_RUN_ID``=DAM, ``OPR_INTERVAL``=0),
a serial row-block counter (``GROUP``: one value per ITC x direction x item x
operating day) or a pure function of ``XML_DATA_ITEM`` (``TR_TYPE``, ``LABEL``,
``POS``); the fetch asserts those invariants per window and stops if one
breaks rather than silently dropping information.

Run::

    python scripts/data/fetch_caiso_trns_usage.py --start 2023-06-19 --end 2026-01-01
    python scripts/data/fetch_caiso_trns_usage.py --fold
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402

BASE = "https://oasis.caiso.com/oasisapi/SingleZip"
QUERY = "TRNS_USAGE"
MARKET_RUN_ID = "DAM"
# OASIS report version for TRNS_USAGE (v1 is the only published version).
VERSION = 1
# resultformat=6 -> CSV inside the zip (OASIS API spec).
RESULT_FORMAT = 6
PACIFIC = ZoneInfo("America/Los_Angeles")

RAW_DIR = paths.RAW_DIR / "caiso-trns-usage"
WINDOW_DIR = RAW_DIR / "windows"

KEY = ["interval_start_utc", "ti_id", "ti_constraint_id", "direction"]
# The thirteen items the report carries (verified 2025-07-01 and 2023-06-19).
ITEMS: tuple[str, ...] = (
    "TTC_MW",
    "OTC_MW",
    "TRM_MW",
    "TRM_UF_MW",
    "TRM_FTO_MW",
    "TRM_SPI_MW",
    "CBM_MW",
    "MKT_XFER_CAP_MW",
    "CONSTRAINT_MW",
    "ENE_IMPORT_MW",
    "AS_IMPORT_MW",
    "USEAGE_MW",
    "ATC_MW",
)


def _utc_stamp(day: dt.date) -> str:
    """OASIS timestamp for local (Pacific) midnight of ``day``, in UTC."""
    local = dt.datetime(day.year, day.month, day.day, tzinfo=PACIFIC)
    return local.astimezone(dt.timezone.utc).strftime("%Y%m%dT%H:%M-0000")


def _url(start: dt.date, end: dt.date) -> str:
    """SingleZip URL for the Pacific-day window [start, end)."""
    return (
        f"{BASE}?queryname={QUERY}&market_run_id={MARKET_RUN_ID}"
        f"&startdatetime={_utc_stamp(start)}&enddatetime={_utc_stamp(end)}"
        f"&version={VERSION}&resultformat={RESULT_FORMAT}"
    )


def _get(url: str, retries: int, sleep_s: float) -> bytes:
    """GET with linear back-off on 429/5xx/network errors."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=300) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            time.sleep(sleep_s * (attempt + 2))
    raise RuntimeError(f"giving up on {url}: {last}")


def _to_wide(csv_bytes: bytes) -> pd.DataFrame:
    """Reshape one TRNS_USAGE CSV to the lossless wide frame (asserts invariants)."""
    d = pd.read_csv(io.BytesIO(csv_bytes))
    if not (d["MARKET_RUN_ID"] == MARKET_RUN_ID).all():
        raise ValueError("non-DAM rows in a DAM query")
    for col in ("OPR_INTERVAL",):
        if d[col].nunique() != 1:
            raise ValueError(f"{col} not constant: {d[col].unique()[:5]}")
    if (
        (d.groupby("XML_DATA_ITEM")[["TR_TYPE", "LABEL", "POS"]].nunique() > 1)
        .any()
        .any()
    ):
        raise ValueError("TR_TYPE/LABEL/POS not a function of XML_DATA_ITEM")
    unknown = set(d["XML_DATA_ITEM"]) - set(ITEMS)
    if unknown:
        raise ValueError(f"unknown XML_DATA_ITEM(s): {sorted(unknown)}")
    d = d.rename(
        columns={
            "INTERVALSTARTTIME_GMT": "interval_start_utc",
            "TI_ID": "ti_id",
            "TI_CONSTRAINT_ID": "ti_constraint_id",
            "TI_DIRECTION": "direction",
        }
    )
    if d.duplicated(KEY + ["XML_DATA_ITEM"]).any():
        raise ValueError("duplicate (key, item) rows")
    w = d.pivot(index=KEY, columns="XML_DATA_ITEM", values="MW").reset_index()
    w.columns.name = None
    for item in ITEMS:
        if item not in w:
            w[item] = float("nan")
    w["interval_start_utc"] = pd.to_datetime(w["interval_start_utc"], utc=True)
    for c in ("ti_id", "ti_constraint_id", "direction"):
        w[c] = w[c].astype("string")
    w[list(ITEMS)] = w[list(ITEMS)].astype("float64")
    return w[KEY + list(ITEMS)].sort_values(KEY, ignore_index=True)


def fetch(
    start: dt.date, end: dt.date, window: int, sleep_s: float, retries: int
) -> None:
    """Fetch every Pacific-day window in [start, end) not already staged."""
    WINDOW_DIR.mkdir(parents=True, exist_ok=True)
    day = start
    while day < end:
        stop = min(day + dt.timedelta(days=window), end)
        out = WINDOW_DIR / f"trns_usage_dam_{day:%Y%m%d}_{stop:%Y%m%d}.parquet"
        if out.exists():
            day = stop
            continue
        payload = _get(_url(day, stop), retries, sleep_s)
        zf = zipfile.ZipFile(io.BytesIO(payload))
        names = [n for n in zf.namelist() if n.endswith(".csv")]
        if not names:
            err = zf.read(zf.namelist()[0]).decode("utf-8", "replace")
            code = (
                err.split("<m:ERR_CODE>")[-1].split("<")[0]
                if "ERR_CODE" in err
                else "?"
            )
            print(f"{day}..{stop}: NO DATA (ERR_CODE {code})", flush=True)
        else:
            w = _to_wide(zf.read(names[0]))
            local_days = (
                w["interval_start_utc"].dt.tz_convert(PACIFIC).dt.date.nunique()
            )
            w.to_parquet(out, compression="zstd", index=False)
            print(
                f"{day}..{stop}: {len(w)} rows, {w['ti_id'].nunique()} ITCs, "
                f"{local_days}/{(stop - day).days} local days -> {out.name}",
                flush=True,
            )
        day = stop
        time.sleep(sleep_s)


def fold() -> list[Path]:
    """Fold staged windows into one committed parquet per Pacific operating year."""
    files = sorted(WINDOW_DIR.glob("trns_usage_dam_*.parquet"))
    if not files:
        raise SystemExit(f"no staged windows under {WINDOW_DIR}")
    w = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    w = w.drop_duplicates(KEY, keep="last").sort_values(KEY, ignore_index=True)
    opr_year = w["interval_start_utc"].dt.tz_convert(PACIFIC).dt.year
    written: list[Path] = []
    for year, part in w.groupby(opr_year):
        path = RAW_DIR / f"caiso_trns_usage_dam_{year}.parquet"
        part.reset_index(drop=True).to_parquet(path, compression="zstd", index=False)
        written.append(path)
        print(f"{year}: {len(part)} rows -> {path} ({path.stat().st_size:,} B)")
    sums = [
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}"
        for p in sorted(RAW_DIR.glob("caiso_trns_usage_dam_*.parquet"))
    ]
    (RAW_DIR / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n")
    return written


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", type=dt.date.fromisoformat, default=dt.date(2023, 6, 19))
    ap.add_argument("--end", type=dt.date.fromisoformat, default=dt.date(2026, 1, 1))
    ap.add_argument("--window", type=int, default=11, help="days per request")
    ap.add_argument("--sleep", type=float, default=6.0, help="seconds between requests")
    ap.add_argument("--retries", type=int, default=4)
    ap.add_argument("--fold", action="store_true", help="fold staged windows only")
    args = ap.parse_args()
    if args.fold:
        fold()
        return
    fetch(args.start, args.end, args.window, args.sleep, args.retries)


if __name__ == "__main__":
    main()
