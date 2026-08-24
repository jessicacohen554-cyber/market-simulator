"""Fetch + consolidate MISO's regional (North/Central/South) hourly load and generation.

Two public daily market reports (no auth), the miso-183 South-seam
measurement-basis substrate — the ONLY public sources found that resolve
MISO's non-contiguous footprints at hourly grain:

* ``https://docs.misoenergy.org/marketreports/YYYYMMDD_rf_al.xls`` —
  "Forecasted and Actual Load Report": hourly MTLF + actual load (MWh) for
  North / Central / South / MISO. The file published on day P carries market
  days P-1 (complete) and P (partial), so market day D is taken from the
  publish D+1 file (fallback D+2..D+4).
* ``https://docs.misoenergy.org/marketreports/YYYYMMDD_sr_gfm.xlsx`` —
  "Real-Time State Estimator Generation Fuel Mix Report": hourly generation
  MW by fuel (Coal/Gas/Nuclear/Hydro/Wind/Solar/Other/Storage + Total) for
  Central / North / South (+ MISO Total block). Market date = publish - 1
  exactly, so market day D comes only from the publish D+1 file.

Hour labels are Market Hour ENDING 1..24 in EST (MISO market time is EST
year-round, no DST — the pbc-record convention, verified there over the full
archive). Region boundaries are MISO's reporting regions; "South" is the
post-2013 Entergy-footprint subregion on the South side of the RDT.

Unlike the pbc fetch (verbatim CSV mirror), the sources here are binary
xls/xlsx, so the consolidated files are PARSED EXTRACTIONS, not byte
mirrors — the daily files are the provenance (re-fetchable by this script;
staged under ``_daily/``, gitignored) and the consolidation is
deterministic:

    data/raw/miso-regional-balance/miso_regional_load_<year>.csv.gz
        market_date, he_est, region, mtlf_mw, actual_mw
    data/raw/miso-regional-balance/miso_regional_genmix_<year>.csv.gz
        market_date, he_est, region, fuel, mw

Quarantine guard (CLAUDE.md rule 22): market dates outside the 2023-2025
train window are REFUSED unless ``--allow-out-of-train`` is passed under a
session-logged owner authorization (publish-window edge files are fetched —
e.g. 2026-01-01 publishes carry 2025-12-31 — but only in-window MARKET
dates are consolidated).

Run (the repo default python3 lacks pandas):
  uv run --no-project --with pandas,xlrd,openpyxl --python 3.12 \
    python scripts/data/fetch_miso_regional_balance.py
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
import urllib.request
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import MISO_REGIONAL_BALANCE_DIR  # noqa: E402

BASE_URL = "https://docs.misoenergy.org/marketreports"

# CLAUDE.md rule 22: the calibration train window. Intake outside it needs
# explicit, session-logged owner authorization (--allow-out-of-train).
TRAIN_YEARS = (2023, 2024, 2025)

_DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")
LOAD_REGIONS = ("North", "Central", "South", "MISO")


def _daterange(start: date, end: date):
    """Yield dates from ``start`` to ``end`` inclusive."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _fetch(name: str, dest: Path) -> Path | None:
    """Download one market-report file into ``dest`` (skip if cached)."""
    out = dest / name
    if out.exists() and out.stat().st_size > 0:
        return out
    try:
        with urllib.request.urlopen(f"{BASE_URL}/{name}", timeout=60) as resp:
            out.write_bytes(resp.read())
        return out
    except Exception as exc:  # noqa: BLE001 — log and continue
        print(f"WARN {name}: {exc}", file=sys.stderr)
        return None


def download(years: list[int], dest: Path) -> None:
    """Download the publish window (market span + 4 lag days) for ``years``."""
    dest.mkdir(parents=True, exist_ok=True)
    start = date(min(years), 1, 1) + timedelta(days=1)
    end = date(max(years), 12, 31) + timedelta(days=4)
    names = []
    for d in _daterange(start, end):
        ymd = d.strftime("%Y%m%d")
        names.append(f"{ymd}_rf_al.xls")
        names.append(f"{ymd}_sr_gfm.xlsx")
    with ThreadPoolExecutor(max_workers=8) as ex:
        got = [p for p in ex.map(lambda n: _fetch(n, dest), names) if p]
    print(f"staged {len(got)}/{len(names)} files in {dest}")


def parse_rf_al(path: Path) -> pd.DataFrame:
    """Parse one rf_al publish file → long (market_date, he_est, region, mtlf, actual)."""
    raw = pd.ExcelFile(path).parse(0, header=None)
    hdr = None
    for i in range(min(12, len(raw))):
        if any(isinstance(v, str) and "HourEnding" in v for v in raw.iloc[i]):
            hdr = i
            break
    if hdr is None:
        raise ValueError(f"{path.name}: no HourEnding header row")
    heads = {str(v).strip(): j for j, v in enumerate(raw.iloc[hdr]) if pd.notna(v)}
    day_col, he_col = heads["Market Day"], heads["HourEnding"]
    rows = []
    for _, r in raw.iloc[hdr + 1 :].iterrows():
        m = _DATE_RE.search(str(r.iloc[day_col]))
        he = pd.to_numeric(r.iloc[he_col], errors="coerce")
        if not m or not (1 <= (he or 0) <= 24):
            continue
        mdate = f"{m.group(3)}-{m.group(1)}-{m.group(2)}"
        for reg in LOAD_REGIONS:
            mtlf = heads.get(f"{reg} MTLF (MWh)")
            act = heads.get(f"{reg} ActualLoad (MWh)")
            if mtlf is None or act is None:
                continue
            rows.append(
                (
                    mdate,
                    int(he),
                    reg,
                    pd.to_numeric(r.iloc[mtlf], errors="coerce"),
                    pd.to_numeric(r.iloc[act], errors="coerce"),
                )
            )
    return pd.DataFrame(
        rows, columns=["market_date", "he_est", "region", "mtlf_mw", "actual_mw"]
    )


def parse_sr_gfm(path: Path) -> pd.DataFrame:
    """Parse one sr_gfm publish file → long (market_date, he_est, region, fuel, mw).

    Region block positions and per-block fuel columns are read from the
    file's own header rows (the South block layout drifts by one column
    across years), so no fixed column map is assumed.
    """
    raw = pd.ExcelFile(path).parse("RT Generation Fuel Mix", header=None)
    mdate = None
    for i in range(min(6, len(raw))):
        for v in raw.iloc[i]:
            if isinstance(v, str) and "Market Date" in v:
                mm = re.search(r"(\d{4})-(\d{2})-(\d{2})", v)
                if mm:
                    mdate = mm.group(0)
    if mdate is None:
        raise ValueError(f"{path.name}: no Market Date header")
    reg_row = col_row = None
    for i in range(min(8, len(raw))):
        vals = [str(v).strip() for v in raw.iloc[i] if pd.notna(v)]
        if {"Central", "North", "South"} <= set(vals):
            reg_row = i
        if any(v == "Market Hour Ending" for v in vals):
            col_row = i
    if reg_row is None or col_row is None:
        raise ValueError(f"{path.name}: region/column header rows not found")
    regions = [
        (j, str(v).strip())
        for j, v in enumerate(raw.iloc[reg_row])
        if str(v).strip() in ("Central", "North", "South", "Total")
    ]
    bounds = [
        (name, j, (regions[k + 1][0] if k + 1 < len(regions) else raw.shape[1]))
        for k, (j, name) in enumerate(regions)
    ]
    rows = []
    for _, r in raw.iloc[col_row + 1 :].iterrows():
        he = pd.to_numeric(r.iloc[0], errors="coerce")
        if not (1 <= (he or 0) <= 24):
            continue
        for name, j0, j1 in bounds:
            for j in range(j0, j1):
                fuel = raw.iloc[col_row, j]
                if pd.isna(fuel):
                    continue
                fuel = str(fuel).strip().replace("Total MW", "Total")
                if fuel in ("Sum:", "HE", "MISO"):
                    continue  # the Total block's odd sub-headers
                mw = pd.to_numeric(r.iloc[j], errors="coerce")
                rows.append((mdate, int(he), name, fuel, mw))
    return pd.DataFrame(rows, columns=["market_date", "he_est", "region", "fuel", "mw"])


def consolidate(src: Path, years: list[int]) -> None:
    """Build the per-year consolidated csv.gz files from the staged dailies."""
    MISO_REGIONAL_BALANCE_DIR.mkdir(parents=True, exist_ok=True)
    warnings.filterwarnings("ignore")
    # -- load: market day D from publish D+1, fallback D+2..D+4
    load_parts: dict[str, pd.DataFrame] = {}
    for y in years:
        for d in _daterange(date(y, 1, 1), date(y, 12, 31)):
            key = d.isoformat()
            for lag in (1, 2, 3, 4):
                p = src / f"{(d + timedelta(days=lag)).strftime('%Y%m%d')}_rf_al.xls"
                if not p.exists():
                    continue
                try:
                    df = parse_rf_al(p)
                except Exception as exc:  # noqa: BLE001
                    print(f"WARN parse {p.name}: {exc}", file=sys.stderr)
                    continue
                day = df[df["market_date"] == key]
                if len(day) and day["actual_mw"].notna().any():
                    load_parts[key] = day
                    break
    # -- genmix: market day D only in publish D+1
    gen_parts: dict[str, pd.DataFrame] = {}
    for y in years:
        for d in _daterange(date(y, 1, 1), date(y, 12, 31)):
            p = src / f"{(d + timedelta(days=1)).strftime('%Y%m%d')}_sr_gfm.xlsx"
            if not p.exists():
                continue
            try:
                df = parse_sr_gfm(p)
            except Exception as exc:  # noqa: BLE001
                print(f"WARN parse {p.name}: {exc}", file=sys.stderr)
                continue
            if df["market_date"].iloc[0] == d.isoformat():
                gen_parts[d.isoformat()] = df
    for stem, parts in (
        ("miso_regional_load", load_parts),
        ("miso_regional_genmix", gen_parts),
    ):
        if not parts:
            continue
        allp = pd.concat(parts.values(), ignore_index=True)
        allp["year"] = allp["market_date"].str[:4].astype(int)
        for y in years:
            sub = allp[allp["year"] == y].drop(columns="year")
            sub = sub.sort_values(["market_date", "he_est", "region"], kind="stable")
            out = MISO_REGIONAL_BALANCE_DIR / f"{stem}_{y}.csv.gz"
            with gzip.open(out, "wt") as fh:
                sub.to_csv(fh, index=False)
            days = sub["market_date"].nunique()
            print(f"{out.name}: {len(sub)} rows, {days} market days")


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=list(TRAIN_YEARS),
        help="market-date years to consolidate (default: the train window)",
    )
    ap.add_argument(
        "--from-dir",
        type=Path,
        default=None,
        help="consolidate an existing staging directory (no network)",
    )
    ap.add_argument(
        "--download-dir",
        type=Path,
        default=None,
        help="where to stage per-day downloads (default: <raw>/_daily)",
    )
    ap.add_argument(
        "--allow-out-of-train",
        action="store_true",
        help=(
            "permit market-date years outside 2023-2025 (rule 22: requires "
            "explicit session-logged owner authorization)"
        ),
    )
    args = ap.parse_args()

    bad = [y for y in args.years if y not in TRAIN_YEARS]
    if bad and not args.allow_out_of_train:
        raise SystemExit(
            f"years {bad} are outside the 2023-2025 train window (CLAUDE.md "
            "rule 22). Pass --allow-out-of-train ONLY under explicit, "
            "session-logged owner authorization."
        )

    src = args.from_dir
    if src is None:
        src = args.download_dir or (MISO_REGIONAL_BALANCE_DIR / "_daily")
        download(args.years, src)
    consolidate(src, args.years)


if __name__ == "__main__":
    main()
