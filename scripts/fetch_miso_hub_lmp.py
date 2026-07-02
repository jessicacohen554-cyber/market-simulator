"""Fetch MISO daily market-report LMP files and stage the eight named trading hubs.

Scope decision D6 (docs/multi-iso/miso-zonal-refinement-scope.md §7/§8): the
zonal-spread gate needs measured per-hub RT and DA hourly LMPs. MISO publishes
them only as one-file-per-day all-node market reports (no annual archives):

    DA ex-post: https://docs.misoenergy.org/marketreports/YYYYMMDD_da_expost_lmp.csv
    RT final:   https://docs.misoenergy.org/marketreports/YYYYMMDD_rt_lmp_final.csv

Each file carries every node's LMP/MCC/MLC per hour-ending 1-24, Eastern
Standard Time year-round (no DST — the header says so explicitly). Committing
~2,200 all-node daily files (~1 MB each) is not viable, so this script stages
the *verbatim rows for the eight named trading hubs only* (ARKANSAS.HUB,
ILLINOIS.HUB, INDIANA.HUB, LOUISIANA.HUB, MICHIGAN.HUB, MINN.HUB, MS.HUB,
TEXAS.HUB — all three Value rows: LMP, MCC, MLC) into one compact gzip CSV per
(year, market) under ``data/raw/lmp-data/MISO/``:

    miso_hub_lmp_<year>_<da|rt>.csv.gz
    columns: date,node,type,value,he01..he24   (values verbatim from the source)

The only transformation is filtering to the hub rows and prepending the
file's date (which the source carries in its header line, not per row) — the
same source-subset pattern as the ERCOT ``DAMLZHBSPP_*.zip`` holdings (LZ/HB/
SPP settlement points only). Downstream,
``scripts/derive_miso_hub_lmp.py`` reduces these to the zonal validation
parquet ``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``.

Usage:
    python scripts/fetch_miso_hub_lmp.py --years 2023 2024 2025
    python scripts/fetch_miso_hub_lmp.py --years 2024 --markets rt
"""

from __future__ import annotations

import argparse
import csv
import gzip
import io
import logging
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from market_sim.config.paths import RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_miso_hub_lmp")

OUT_DIR = RAW_DIR / "lmp-data" / "MISO"

_URL = "https://docs.misoenergy.org/marketreports/{ymd}_{report}.csv"
_REPORT = {"da": "da_expost_lmp", "rt": "rt_lmp_final"}

# The eight named MISO trading hubs (scope decision D6). Everything else in
# the daily files (load zones, gennodes, interfaces, the *.AZ accounting hubs)
# is dropped at stage time.
HUBS: frozenset[str] = frozenset(
    {
        "ARKANSAS.HUB",
        "ILLINOIS.HUB",
        "INDIANA.HUB",
        "LOUISIANA.HUB",
        "MICHIGAN.HUB",
        "MINN.HUB",
        "MS.HUB",
        "TEXAS.HUB",
    }
)

_N_HOURS = 24  # HE 1-24, EST year-round (no DST hour in these reports)
_FETCH_WORKERS = 8
_RETRIES = 3
_TIMEOUT_S = 60


def _fetch(url: str) -> bytes:
    """Return the response body for ``url``, retrying transient failures."""
    last: Exception | None = None
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT_S) as resp:
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - retry then re-raise
            last = exc
            log.warning("retry %d/%d %s (%s)", attempt + 1, _RETRIES, url, exc)
    raise RuntimeError(f"failed after {_RETRIES} attempts: {url}") from last


def _hub_rows(day: date, market: str) -> list[list[str]]:
    """Fetch one daily report and return the hub rows as staged-CSV records.

    Each record is ``[date, node, type, value, he01..he24]`` with the 24
    hourly strings passed through verbatim (blank stays blank).
    """
    ymd = day.strftime("%Y%m%d")
    body = _fetch(_URL.format(ymd=ymd, report=_REPORT[market]))
    rows: list[list[str]] = []
    reader = csv.reader(io.StringIO(body.decode("utf-8", errors="replace")))
    for rec in reader:
        if len(rec) < 3 + _N_HOURS or rec[0] not in HUBS:
            continue
        rows.append([day.isoformat(), rec[0], rec[1], rec[2], *rec[3 : 3 + _N_HOURS]])
    if len(rows) != len(HUBS) * 3:  # 8 hubs x LMP/MCC/MLC
        log.warning(
            "%s %s: expected %d hub rows, got %d",
            ymd,
            market,
            len(HUBS) * 3,
            len(rows),
        )
    return rows


def stage_year(year: int, market: str) -> Path:
    """Fetch every day of ``year`` for ``market`` and write the staged gzip CSV."""
    days = []
    d = date(year, 1, 1)
    while d.year == year:
        days.append(d)
        d += timedelta(days=1)
    with ThreadPoolExecutor(max_workers=_FETCH_WORKERS) as pool:
        per_day = list(pool.map(lambda dd: _hub_rows(dd, market), days))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"miso_hub_lmp_{year}_{market}.csv.gz"
    header = ["date", "node", "type", "value"] + [
        f"he{h:02d}" for h in range(1, _N_HOURS + 1)
    ]
    with gzip.open(out, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for rows in per_day:
            w.writerows(rows)
    n = sum(len(r) for r in per_day)
    log.info("wrote %s (%d rows, %d days)", out, n, len(days))
    return out


def main() -> None:
    """CLI: stage the requested years/markets."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--markets", nargs="+", choices=sorted(_REPORT), default=sorted(_REPORT)
    )
    args = ap.parse_args()
    for year in args.years:
        for market in args.markets:
            stage_year(year, market)


if __name__ == "__main__":
    main()
