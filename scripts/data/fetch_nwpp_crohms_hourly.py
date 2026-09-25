#!/usr/bin/env python3
"""Fetch the USACE CROHMS hourly project series for the Columbia / lower Snake chain (NWPP-36).

The raw measured input behind the Columbia mainstem hydraulic-coupling mechanism
(owner ruling N3; ``docs/handoffs/PRECOMMIT-nwpp-36-2026-09-16.md`` §4). The lag
``τ`` per link, the operated pondage band per plant, the water-to-energy ratio per
plant-month and the monthly side inflow / head spill are all DERIVED from this pull
by ``scripts/data/build_nwpp_hydro_cascade.py`` — nothing here is modelled, and the
hourly operation of any plant never enters the LP directly (rule 13
``[R-MEASURED]``: the hourly series enter only through ``τ``, the band and monthly
means).

Source: ``https://public.crohms.org/dd/common/web_service/webexec/getjson`` — the
Columbia Basin Water Management Division's public DataQuery web service, the same
feed the 2004 HRFCPPA cites for its compliance data. Query form (verified
2026-09-16)::

    getjson?query=["<STATION>.<series>", ...]&startdate=MM/DD/YYYY HH:MM&enddate=MM/DD/YYYY HH:MM

The service returns, per station, each series' ``values`` as
``[timestamp, value, quality_code]`` triples in the service's fixed standard time
(no DST shift — the 2023-03-12 02:00 hour is present). Series pulled per station:

* ``Flow-Out.Ave.1Hour.1Hour.CBT-REV`` — total project outflow, kcfs (hourly mean)
* ``Flow-Spill.Ave.1Hour.1Hour.CBT-REV`` — spill, kcfs
* ``Flow-Gen.Ave.1Hour.1Hour.CBT-REV`` — turbine (generation) flow, kcfs
* ``Elev-Forebay.Inst.1Hour.0.CBT-REV`` — forebay elevation, ft (instantaneous)
* ``Power.Total.1Hour.1Hour.CBT-RAW`` — gross generation, MW

The Idaho Power Hells Canyon complex carries only DAILY series on CROHMS
(``BRN.Flow-Out.Inst.~1Day.0.IDP-COMPUTED-REV``, ``HCD.Flow-Out.Ave.~1Day.1Day.IDP-REV``,
and nothing for Oxbow); they are pulled for the record so the FINDING's
"unmeasurable at hourly precision" statement is checkable, never used to couple.

Outputs (``data/raw/nwpp-hydro/crohms/``):

* ``nwpp_crohms_hourly.parquet`` — long form ``station, series, ts, value, quality``
* ``nwpp_crohms_daily_idp.parquet`` — the Idaho Power daily series, same columns
* ``nwpp_crohms_catalog.json`` — the ``tscatalog`` response for every station
  (coordinates, datum, the series inventory), the source of the station
  coordinates the celerity sanity check uses
* ``SHA256SUMS.txt``

Usage:
    python scripts/data/fetch_nwpp_crohms_hourly.py             # full 2023-01-01 -> 2026-01-01
    python scripts/data/fetch_nwpp_crohms_hourly.py --end 2024-01-01   # shorter range

Extending the committed pull (NWPP-NEXT-2, 2019-2022). The fetch OVERWRITES its
``--out-dir``, so a new range is pulled into a SCRATCH dir and then merged::

    python scripts/data/fetch_nwpp_crohms_hourly.py --start 2019-01-01 \
        --end 2023-01-01 --out-dir /tmp/crohms1922
    python scripts/data/fetch_nwpp_crohms_hourly.py --merge-only /tmp/crohms1922

``--merge-only`` adds the scratch pull's hourly and daily rows to the committed
parquets (no network). Every committed row is kept unchanged; an overlapping
``(station, series, ts)`` key is refused unless value and quality agree exactly.
The committed catalog is kept (it is the celerity check's coordinate source,
frozen with the links it produced) and ``SHA256SUMS.txt`` is rewritten.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

OUT_DIR = RAW_DATA_DIR / "nwpp-hydro" / "crohms"
BASE_URL = "https://public.crohms.org/dd/common/web_service/webexec/getjson"

# Every hourly-instrumented project on the coupled chain (PRECOMMIT §2), in
# hydraulic order: mainstem GCL -> BON, lower Snake DWR/LWG -> IHR.
HOURLY_STATIONS: tuple[str, ...] = (
    "GCL",
    "CHJ",
    "WEL",
    "RRH",
    "RIS",
    "WAN",
    "PRD",
    "MCN",
    "JDA",
    "TDA",
    "BON",
    "DWR",
    "LWG",
    "LGS",
    "LMN",
    "IHR",
)
HOURLY_SERIES: tuple[str, ...] = (
    "Flow-Out.Ave.1Hour.1Hour.CBT-REV",
    "Flow-Spill.Ave.1Hour.1Hour.CBT-REV",
    "Flow-Gen.Ave.1Hour.1Hour.CBT-REV",
    "Elev-Forebay.Inst.1Hour.0.CBT-REV",
    "Power.Total.1Hour.1Hour.CBT-RAW",
)
# Idaho Power's Hells Canyon complex: daily only on CROHMS (record, never coupled).
DAILY_IDP_SERIES: tuple[str, ...] = (
    "BRN.Flow-Out.Inst.~1Day.0.IDP-COMPUTED-REV",
    "HCD.Flow-Out.Ave.~1Day.1Day.IDP-REV",
)
CATALOG_STATIONS: tuple[str, ...] = HOURLY_STATIONS + ("BRN", "HCD", "OXB")

logger = logging.getLogger("fetch_nwpp_crohms_hourly")


def _get(url: str, retries: int = 5) -> dict:
    """GET ``url`` and parse JSON, retrying on transport errors."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urlopen(
                Request(url, headers={"User-Agent": "market-sim/nwpp-36"}), timeout=180
            ) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 — retry any transport failure
            last = exc
            time.sleep(2**attempt)
    raise RuntimeError(f"CROHMS fetch failed after {retries} attempts: {url}") from last


def _query_url(series: list[str], start: date, end: date) -> str:
    q = quote(json.dumps(series, separators=(",", ":")), safe="")
    s = quote(f"{start.month:02d}/{start.day:02d}/{start.year} 00:00", safe="")
    e = quote(f"{end.month:02d}/{end.day:02d}/{end.year} 00:00", safe="")
    return f"{BASE_URL}?query={q}&startdate={s}&enddate={e}"


def _quarter_windows(start: date, end: date) -> list[tuple[date, date]]:
    """Calendar-quarter windows ``[start, end)`` — the service refuses a full year."""
    out: list[tuple[date, date]] = []
    cur = start
    while cur < end:
        m = cur.month + 3
        nxt = date(cur.year + (m - 1) // 12, (m - 1) % 12 + 1, 1)
        out.append((cur, min(nxt, end)))
        cur = nxt
    return out


def _rows_from_response(payload: dict) -> list[tuple]:
    rows: list[tuple] = []
    for station, body in payload.items():
        for key, ts in body.get("timeseries", {}).items():
            for stamp, value, qual in ts.get("values", []):
                rows.append((station, key.split(".", 1)[1], stamp, value, qual))
    return rows


def fetch_hourly(start: date, end: date) -> pd.DataFrame:
    """Pull every hourly station × series over ``[start, end)`` quarter by quarter."""
    rows: list[tuple] = []
    windows = _quarter_windows(start, end)
    for station in HOURLY_STATIONS:
        series = [f"{station}.{s}" for s in HOURLY_SERIES]
        for w0, w1 in windows:
            payload = _get(_query_url(series, w0, w1))
            got = _rows_from_response(payload)
            logger.info("%s %s -> %s: %d values", station, w0, w1, len(got))
            rows.extend(got)
    df = pd.DataFrame(rows, columns=["station", "series", "ts", "value", "quality"])
    df["ts"] = pd.to_datetime(df["ts"])
    df["value"] = df["value"].astype(float)
    df["quality"] = df["quality"].astype(int)
    # Window ends are inclusive on the service side, so the boundary hour is
    # returned twice; keep the first occurrence (identical values).
    df = df.drop_duplicates(["station", "series", "ts"]).sort_values(
        ["station", "series", "ts"]
    )
    return df.reset_index(drop=True)


def fetch_daily_idp(start: date, end: date) -> pd.DataFrame:
    rows: list[tuple] = []
    for w0, w1 in _quarter_windows(start, end):
        payload = _get(_query_url(list(DAILY_IDP_SERIES), w0, w1))
        rows.extend(_rows_from_response(payload))
    df = pd.DataFrame(rows, columns=["station", "series", "ts", "value", "quality"])
    if len(df):
        df["ts"] = pd.to_datetime(df["ts"])
        df["value"] = df["value"].astype(float)
        df["quality"] = df["quality"].astype(int)
        df = df.drop_duplicates(["station", "series", "ts"]).sort_values(
            ["station", "series", "ts"]
        )
    return df.reset_index(drop=True)


def fetch_catalog() -> dict:
    q = quote(json.dumps(list(CATALOG_STATIONS), separators=(",", ":")), safe="")
    return _get(f"{BASE_URL}?tscatalog={q}")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_sums(out: Path) -> Path:
    sums = out / "SHA256SUMS.txt"
    with open(sums, "w") as f:
        for p in sorted(out.iterdir()):
            if p.name != sums.name and p.is_file():
                f.write(f"{_sha256(p)}  {p.name}\n")
    return sums


def merge_frames(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Union two long pulls; every ``existing`` row is kept, overlaps must agree."""
    key = ["station", "series", "ts"]
    both = existing.merge(new, on=key, how="inner", suffixes=("_old", "_new"))
    bad = both[
        ~(
            (both["value_old"] == both["value_new"])
            | (both["value_old"].isna() & both["value_new"].isna())
        )
        | (both["quality_old"] != both["quality_new"])
    ]
    if len(bad):
        raise ValueError(
            f"{len(bad)} overlapping (station, series, ts) keys disagree between "
            f"the committed pull and the new one, e.g. {bad.head(3).to_dict('records')}"
        )
    add = new.merge(existing[key], on=key, how="left", indicator=True)
    add = add[add["_merge"] == "left_only"].drop(columns="_merge")
    out = pd.concat([existing, add[existing.columns]], ignore_index=True)
    out = out.astype(existing.dtypes.to_dict())
    return out.sort_values(key, kind="mergesort").reset_index(drop=True)


def merge_only(new_dir: Path, out: Path) -> int:
    """Merge a scratch pull in ``new_dir`` into the committed pull in ``out``."""
    for name in ("nwpp_crohms_hourly.parquet", "nwpp_crohms_daily_idp.parquet"):
        existing = pd.read_parquet(out / name)
        new = pd.read_parquet(new_dir / name)
        merged = merge_frames(existing, new)
        merged.to_parquet(out / name, index=False)
        logger.info(
            "%s: %d committed + %d new = %d rows (%s -> %s)",
            name,
            len(existing),
            len(merged) - len(existing),
            len(merged),
            merged["ts"].min(),
            merged["ts"].max(),
        )
    logger.info("kept the committed catalog; wrote %s", _write_sums(out))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--start", default="2023-01-01")
    ap.add_argument("--end", default="2026-01-01")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument(
        "--merge-only",
        default=None,
        metavar="NEW_DIR",
        help="no fetch: merge the pull in NEW_DIR into --out-dir (committed rows kept)",
    )
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    if args.merge_only:
        return merge_only(Path(args.merge_only), Path(args.out_dir))

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    catalog = fetch_catalog()
    (out / "nwpp_crohms_catalog.json").write_text(
        json.dumps(catalog, indent=1, sort_keys=True)
    )

    hourly = fetch_hourly(start, end)
    hourly.to_parquet(out / "nwpp_crohms_hourly.parquet", index=False)
    logger.info(
        "hourly: %d rows, %d stations, %s -> %s",
        len(hourly),
        hourly["station"].nunique(),
        hourly["ts"].min(),
        hourly["ts"].max(),
    )

    daily = fetch_daily_idp(start, end)
    daily.to_parquet(out / "nwpp_crohms_daily_idp.parquet", index=False)
    logger.info("daily IDP: %d rows", len(daily))

    logger.info("wrote %s", _write_sums(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
