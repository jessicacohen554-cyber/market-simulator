"""Fetch MISO ASM market reports: zonal reserve MCPs + RT cleared reserve MW.

Data ask filed in ``docs/multi-iso/miso-scarcity-tail-diagnosis.md`` §5 and
restated in ``docs/multi-iso/miso-scarcity-posture-design-2026-07.md`` §A
(honesty gate) / §B (Midwest family): MISO's historical cleared reserve MW and
reserve MCPs by zone, 2023-25. MISO publishes both only as one-file-per-day
market reports (no annual archives):

    DA ex-ante MCP: https://docs.misoenergy.org/marketreports/YYYYMMDD_asm_exante_damcp.csv
    RT final MCP:   https://docs.misoenergy.org/marketreports/YYYYMMDD_asm_rtmcp_final.csv
    RT cleared:     https://docs.misoenergy.org/marketreports/YYYYMMDD_asm_rt_co.zip

The MCP files carry one row per (pnode, MCP type) but the value is the ZONE
clearing price repeated for every pnode in the zone, plus a market-wide
("MISO Wide"/"Miso-Wide") block; this script stages the *deduplicated
zone-level rows only* (key = zone x MCP type; values verbatim) — the same
source-subset pattern as ``fetch_miso_hub_lmp.py`` (D6). The cleared-offers
zip carries one row per (masked unit, market hour) with Region
(North/Central/South) and cleared MW per 5-minute interval (RegMW1-12,
SpinMW1-12, SuppMW1-12, STRMW1-12; published with a ~4-month lag); committing
~6 MB/day of masked unit rows is not viable, so this script stages the hourly
Region x product aggregate: ``cleared_mw`` = sum over units of
mean(MW1..MW12) — the measured regional cleared reserve series the honesty
gate needs (level + event-day direction), analogous to the staged PJM
``reserve_market_results_*.parquet`` holdings in ``data/raw/PJM-AS/``.

All hours are Hour-Ending 1-24 Eastern Standard Time year-round (each file's
header says so explicitly; MISO market reports never observe DST).

Outputs, one file per (year, dataset) under ``data/raw/MISO-AS/``:

    asm_damcp_zonal_<year>.parquet   date, zone, product, he01..he24
    asm_rtmcp_zonal_<year>.parquet   date, zone, product, he01..he24
    asm_rt_cleared_mw_<year>.parquet date, hour_end_est, region, product, cleared_mw

Usage:
    python scripts/fetch_miso_asm.py --years 2023 2024 2025
    python scripts/fetch_miso_asm.py --years 2024 --datasets mcp
"""

from __future__ import annotations

import argparse
import csv
import io
import logging
import time
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

import pandas as pd

from market_sim.config.paths import RAW_DIR

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("fetch_miso_asm")

OUT_DIR = RAW_DIR / "MISO-AS"

_MCP_URL = "https://docs.misoenergy.org/marketreports/{ymd}_{report}.csv"
_CO_URL = "https://docs.misoenergy.org/marketreports/{ymd}_asm_rt_co.zip"
_MCP_REPORT = {"da": "asm_exante_damcp", "rt": "asm_rtmcp_final"}

# Cleared-offer 5-minute MW column stems, by product label used downstream.
_CO_PRODUCTS = {"reg": "RegMW", "spin": "SpinMW", "supp": "SuppMW", "str": "STRMW"}

_RETRIES = 4
_TIMEOUT = 90


def _get(url: str) -> bytes | None:
    """Fetch ``url`` with retries; None on HTTP 404 (report never published)."""
    for attempt in range(_RETRIES):
        try:
            with urllib.request.urlopen(url, timeout=_TIMEOUT) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt == _RETRIES - 1:
                raise
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == _RETRIES - 1:
                raise
        time.sleep(2**attempt)
    return None


def _days(year: int) -> list[date]:
    d0, d1 = date(year, 1, 1), date(year, 12, 31)
    return [d0 + timedelta(days=i) for i in range((d1 - d0).days + 1)]


def _parse_mcp(raw: bytes, day: date) -> list[dict]:
    """Deduplicated zone-level MCP rows from one daily MCP csv."""
    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for rec in csv.reader(io.StringIO(raw.decode("utf-8", "replace"))):
        if len(rec) < 27:
            continue
        first, second, mcp_type = rec[0].strip(), rec[1].strip(), rec[2].strip()
        if not mcp_type or mcp_type == "MCP Type":
            continue
        # Market-wide block: ("MISO Wide"/"Miso-Wide", "-", type). Zonal block:
        # (pnode, "Zone N", type) — the value is the zone price, dedupe on zone.
        zone = first if second in ("-", "") else second
        key = (zone, mcp_type)
        if key in seen:
            continue
        seen.add(key)
        row: dict = {"date": day.isoformat(), "zone": zone, "product": mcp_type}
        for h in range(24):
            v = rec[3 + h].strip()
            try:
                row[f"he{h + 1:02d}"] = float(v) if v else float("nan")
            except ValueError:
                row[f"he{h + 1:02d}"] = float("nan")
        rows.append(row)
    return rows


def _parse_co(raw: bytes, day: date) -> list[dict]:
    """Hourly Region x product cleared-MW aggregate from one asm_rt_co zip."""
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = next(n for n in zf.namelist() if n.endswith(".csv"))
        text = zf.read(name).decode("utf-8", "replace")
    # agg[(hour_end, region, product)] = summed MW
    agg: dict[tuple[int, str, str], float] = {}
    for rec in csv.DictReader(io.StringIO(text)):
        region = (rec.get("Region") or "").strip()
        begin = (rec.get("Mkthour Begin (EST)") or "").strip()
        if not region or not begin:
            continue
        try:
            hour_end = int(begin.split(" ")[1].split(":")[0]) + 1
        except (IndexError, ValueError):
            continue
        for product, stem in _CO_PRODUCTS.items():
            total, n = 0.0, 0
            for i in range(1, 13):
                v = (rec.get(f"{stem}{i}") or "").strip()
                if v:
                    try:
                        total += float(v)
                        n += 1
                    except ValueError:
                        pass
            if n:
                key = (hour_end, region, product)
                agg[key] = agg.get(key, 0.0) + total / n
    return [
        {
            "date": day.isoformat(),
            "hour_end_est": h,
            "region": r,
            "product": p,
            "cleared_mw": mw,
        }
        for (h, r, p), mw in sorted(agg.items())
    ]


def _fetch_year_mcp(year: int, market: str, workers: int) -> None:
    out = OUT_DIR / f"asm_{'damcp' if market == 'da' else 'rtmcp'}_zonal_{year}.parquet"
    if out.exists():
        log.info("%s exists, skipping", out.name)
        return
    report = _MCP_REPORT[market]

    def one(day: date) -> list[dict]:
        raw = _get(_MCP_URL.format(ymd=day.strftime("%Y%m%d"), report=report))
        if raw is None:
            log.warning("%s %s: 404, skipped", report, day)
            return []
        return _parse_mcp(raw, day)

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for chunk in ex.map(one, _days(year)):
            rows.extend(chunk)
    df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    log.info("wrote %s (%d rows)", out, len(df))


def _fetch_year_co(year: int, workers: int) -> None:
    out = OUT_DIR / f"asm_rt_cleared_mw_{year}.parquet"
    if out.exists():
        log.info("%s exists, skipping", out.name)
        return

    def one(day: date) -> list[dict]:
        raw = _get(_CO_URL.format(ymd=day.strftime("%Y%m%d")))
        if raw is None:
            log.warning("asm_rt_co %s: 404, skipped", day)
            return []
        return _parse_co(raw, day)

    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, chunk in enumerate(ex.map(one, _days(year))):
            rows.extend(chunk)
            if (i + 1) % 60 == 0:
                log.info("asm_rt_co %d: %d/%d days", year, i + 1, len(_days(year)))
    df = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out, index=False)
    log.info("wrote %s (%d rows)", out, len(df))


def main() -> None:
    """CLI entrypoint: fetch the requested years/datasets into data/raw/MISO-AS."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument(
        "--datasets",
        nargs="+",
        default=["mcp", "co"],
        choices=["mcp", "co"],
        help="mcp = DA ex-ante + RT final zonal MCPs; co = RT cleared MW aggregate",
    )
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    for year in args.years:
        if "mcp" in args.datasets:
            _fetch_year_mcp(year, "da", args.workers)
            _fetch_year_mcp(year, "rt", args.workers)
        if "co" in args.datasets:
            _fetch_year_co(year, args.workers)


if __name__ == "__main__":
    main()
