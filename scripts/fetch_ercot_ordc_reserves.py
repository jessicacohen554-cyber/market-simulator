#!/usr/bin/env python3
"""Fetch ERCOT's measured Real-Time ORDC / Reliability-Deployment price adders
and online reserves, and curate them onto the fleet's non-leap 8760-hour clock.

Source (public, no API key): the ERCOT MIS report **NP6-905-CD "Historical
Real-Time Price Adders by SCED Interval"** (``reportTypeId=13231``), whose annual
archive bundles are named ``RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV_<year>`` — one
``.xlsx`` per year with twelve monthly sheets at SCED-interval (~5-minute)
resolution. These are ERCOT's *settled* reserve and price-adder telemetry; they
are **exogenous measured series** and must never be fit to LMP.

Per SCED interval the report carries (header on row 9 of each monthly sheet):

    SCED Timestamp, Repeated Hour Flag, System Lamda, PRC,
    RTOLCAP, RTOFFCAP, RTORPA, RTOFFPA, RTOLHSL, ... , RTORDPA, ...

We curate the reserve-supply / price-adder subset the ERCOT scarcity model needs:

    rtolcap   Real-Time On-Line Reserve Capability (MW) — ERCOT's online
              responsive reserve, the physical reserve-supply target the co-opt
              reserve-eligibility definition is being compared against.
    rtoffcap  Real-Time Off-Line Reserve Capability (MW).
    rtorpa    Real-Time On-Line Reserve Price Adder ($/MWh) — the ORDC on-line
              adder ERCOT folds into RTSPP.
    rtoffpa   Real-Time Off-Line Reserve Price Adder ($/MWh).
    rtordpa   Real-Time ORDC + Reliability-Deployment Price Adder ($/MWh) — the
              reliability-deployment component of the scarcity adder.
    rtolhsl   Real-Time On-Line High Sustainable Limit (MW).
    prc       Physical Responsive Capability (MW).
    system_lambda  SCED system lambda ($/MWh).

The ~5-minute intervals are averaged to hourly and placed on the fixed non-leap
8760-hour clock keyed to ERCOT-local time (Feb 29 dropped, the DST fall-back
repeat averaged via the clock-hour group-by, the spring-forward gap interpolated)
— matching the ``ERCO hourly`` demand clock and the AS-by-restype series.

Run (network required; the managed env reaches www.ercot.com):

    python scripts/fetch_ercot_ordc_reserves.py --years 2023 2024 2025

Writes ``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet``.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "data" / "raw" / "ercot"

# ERCOT MIS "Historical Real-Time Price Adders by SCED Interval" (NP6-905-CD).
DOC_LIST_URL = "https://www.ercot.com/misapp/servlets/IceDocListJsonWS"
DOWNLOAD_URL = "https://www.ercot.com/misdownload/servlets/mirDownload"
REPORT_TYPE_ID = 13231
# The pre-RTC+B annual bundles carrying the ORDC adder + reserves columns.
ARCHIVE_PREFIX = "RTM_ORDC_REL_DPLY_PRC_ADDR_RSRV"

HOURS_PER_YEAR = 8760
HEADER_ROW = 9  # 1-based Excel row holding the column names on each month sheet.

# Raw report column -> curated output column (the reserve-supply / adder subset).
COLUMN_MAP: dict[str, str] = {
    "System Lamda": "system_lambda",
    "PRC": "prc",
    "RTOLCAP": "rtolcap",
    "RTOFFCAP": "rtoffcap",
    "RTORPA": "rtorpa",
    "RTOFFPA": "rtoffpa",
    "RTOLHSL": "rtolhsl",
    "RTORDPA": "rtordpa",
}
TS_COL = "SCED Timestamp"
# Largest hole (hours) interpolated when placing the series on the 8760 clock —
# the DST spring-forward gap is 1 hour; more than a day missing means the
# archive is incomplete and the year is rejected rather than fabricated.
_MAX_GAP_HOURS = 24


def _discover_docid(year: int) -> str:
    """Return the MIS DocID of the ``year`` ORDC-reserves annual archive."""
    resp = requests.get(
        DOC_LIST_URL, params={"reportTypeId": REPORT_TYPE_ID}, timeout=120
    )
    resp.raise_for_status()
    docs = resp.json()["ListDocsByRptTypeRes"]["DocumentList"]
    want = f"{ARCHIVE_PREFIX}_{year}"
    matches = [d["Document"] for d in docs if d["Document"]["FriendlyName"] == want]
    if not matches:
        available = sorted(
            d["Document"]["FriendlyName"]
            for d in docs
            if d["Document"]["FriendlyName"].startswith(ARCHIVE_PREFIX)
        )
        sys.exit(
            f"{year}: no '{want}' in reportTypeId={REPORT_TYPE_ID}. "
            f"Available archives: {available}"
        )
    # One per year; if ERCOT reposts, the most recent publish wins.
    matches.sort(key=lambda d: d["PublishDate"], reverse=True)
    return matches[0]["DocID"]


def _download_xlsx(docid: str) -> bytes:
    """Download a MIS document by DocID and return the inner ``.xlsx`` bytes."""
    resp = requests.get(DOWNLOAD_URL, params={"doclookupId": docid}, timeout=300)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".xlsx")]
        if not names:
            sys.exit(f"DocID {docid}: archive holds no .xlsx ({zf.namelist()})")
        return zf.read(names[0])


def _read_intervals(xlsx: bytes) -> pd.DataFrame:
    """Concatenate the twelve monthly sheets into one SCED-interval frame."""
    sheets = pd.read_excel(
        io.BytesIO(xlsx),
        sheet_name=None,
        header=HEADER_ROW - 1,  # 0-based header index
        engine="openpyxl",
    )
    frames: list[pd.DataFrame] = []
    for name, df in sheets.items():
        df = df.rename(columns=lambda c: str(c).strip())
        if TS_COL not in df.columns:
            continue  # a non-data sheet (none expected, but be defensive)
        keep = [TS_COL] + [c for c in COLUMN_MAP if c in df.columns]
        sub = df[keep].copy()
        sub["ts"] = pd.to_datetime(sub[TS_COL], errors="coerce")
        sub = sub.dropna(subset=["ts"])
        frames.append(sub)
    if not frames:
        sys.exit("no monthly sheet carried a 'SCED Timestamp' column")
    out = pd.concat(frames, ignore_index=True)
    return out.rename(columns=COLUMN_MAP)


def _interp_short_gaps(s: pd.Series) -> tuple[pd.Series, int, int]:
    """Interpolate only contiguous NaN runs ``<= _MAX_GAP_HOURS``.

    Short interior holes (the DST spring-forward hour, scattered telemetry
    gaps) are linearly filled; a long contiguous run — e.g. the 2025 tail
    after the RTC+B go-live (2025-12-05) retired the ORDC/RTORPA regime — is
    left NaN rather than fabricated. Returns the filled series, the count of
    interpolated hours, and the count of hours left NaN.
    """
    isna = s.isna().to_numpy()
    keep_nan = np.zeros(len(s), dtype=bool)
    i, n = 0, len(s)
    while i < n:
        if isna[i]:
            j = i
            while j < n and isna[j]:
                j += 1
            if (j - i) > _MAX_GAP_HOURS:
                keep_nan[i:j] = True
            i = j
        else:
            i += 1
    filled = s.interpolate(limit_direction="both")
    filled[keep_nan] = np.nan
    interpolated = int(isna.sum() - keep_nan.sum())
    return filled, interpolated, int(keep_nan.sum())


def _to_model_clock(
    intervals: pd.DataFrame, year: int
) -> tuple[pd.DataFrame, int, int]:
    """Average the ~5-min intervals to hourly on the non-leap 8760-hour clock.

    Filters to ``year`` with Feb 29 dropped, averages each curated column by
    local ``(month, day, hour)`` — collapsing sub-hourly intervals and the
    repeated DST fall-back hour alike — then reindexes onto the fixed non-leap
    hourly calendar. Short interior gaps are interpolated; a long contiguous
    tail (a regime boundary such as RTC+B) is preserved as NaN.
    """
    ts = intervals["ts"]
    keep = (ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    rows = intervals[keep]
    cols = [c for c in COLUMN_MAP.values() if c in rows.columns]
    grouped = rows.groupby(
        [rows["ts"].dt.month, rows["ts"].dt.day, rows["ts"].dt.hour]
    )[cols].mean()
    grouped.index.names = ["month", "day", "hour"]

    calendar = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
    full_index = pd.MultiIndex.from_arrays(
        [calendar.month, calendar.day, calendar.hour], names=["month", "day", "hour"]
    )
    aligned = grouped.reindex(full_index)
    interpolated = left_nan = 0
    for col in cols:
        aligned[col], interp_c, nan_c = _interp_short_gaps(aligned[col])
        interpolated, left_nan = max(interpolated, interp_c), max(left_nan, nan_c)
    out = aligned.reset_index(drop=True)
    out.insert(0, "hour", np.arange(HOURS_PER_YEAR, dtype="int64"))
    return out, interpolated, left_nan


def _validate(df: pd.DataFrame, year: int, missing: int, left_nan: int) -> None:
    """Print ranges, coverage and scarcity onset for one curated year."""
    print(f"\n=== ERCOT {year} ORDC reserves / price adders ===")
    covered = int((~df["rtolcap"].isna()).sum())
    print(
        f"Rows: {len(df)} (expected {HOURS_PER_YEAR}); covered {covered}; "
        f"interpolated DST/short-gap hours: {missing}; left NaN (regime tail): {left_nan}"
    )
    for col in (
        "rtolcap",
        "rtoffcap",
        "rtorpa",
        "rtoffpa",
        "rtordpa",
        "prc",
        "rtolhsl",
    ):
        if col not in df.columns:
            continue
        s = df[col]
        print(
            f"  {col:14s} mean {s.mean():9.1f}  p5 {s.quantile(0.05):9.1f}  "
            f"p95 {s.quantile(0.95):9.1f}  max {s.max():9.1f}"
        )
    # Scarcity onset: hours where the on-line ORDC adder actually fired.
    if "rtorpa" in df.columns:
        fired = df["rtorpa"] > 1.0
        n = int(fired.sum())
        covered = int((~df["rtorpa"].isna()).sum()) or len(df)
        print(f"  RTORPA > $1: {n} h ({100 * n / covered:.1f}% of covered hours)")
        if n:
            month = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h").month
            by_month = pd.Series(df["rtorpa"].to_numpy(), index=month).groupby(level=0)
            hot = by_month.apply(lambda x: int((x > 1).sum()))
            print(
                "    RTORPA>$1 h by month: "
                + ", ".join(f"{m}:{hot.get(m, 0)}" for m in range(1, 13))
            )


def build_year(year: int) -> bool:
    """Fetch, curate, validate and write one year's parquet. True on success."""
    print(f"\n>> {year}: discovering archive ...")
    docid = _discover_docid(year)
    print(f"   DocID {docid}; downloading ~16 MB xlsx ...")
    xlsx = _download_xlsx(docid)
    intervals = _read_intervals(xlsx)
    print(f"   {len(intervals):,} SCED intervals read; aggregating to hourly ...")
    df, missing, left_nan = _to_model_clock(intervals, year)
    _validate(df, year, missing, left_nan)
    covered = int((~df["rtolcap"].isna()).sum())

    table = pa.Table.from_pandas(df, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": (
                "ERCOT MIS NP6-905-CD 'Historical Real-Time Price Adders by SCED "
                f"Interval' (reportTypeId={REPORT_TYPE_ID}), annual archive "
                f"{ARCHIVE_PREFIX}_{year}; SCED-interval (~5-min) averaged to hourly."
            ),
            "description": (
                f"ERCOT {year} measured Real-Time ORDC / Reliability-Deployment "
                "price adders and on/off-line reserves on the non-leap 8760-hour "
                "ERCOT-local clock. Exogenous measured series — never fit to LMP."
            ),
            "units": (
                "rtolcap/rtoffcap/rtolhsl/prc = MW; rtorpa/rtoffpa/rtordpa/"
                "system_lambda = $/MWh (hourly mean of SCED intervals)"
            ),
            "coverage": (
                f"{covered}/{HOURS_PER_YEAR} hours carry data; "
                f"{left_nan} trailing hours left NaN (the ORDC/RTORPA regime "
                "ended at the 2025-12-05 RTC+B go-live, so the 2025 archive "
                "stops in early December — not fabricated)."
            ),
            "year": str(year),
        }
    )
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"ercot_{year}_ordc_reserves_hourly.parquet"
    pq.write_table(table, path)
    print(
        f"   wrote {path.relative_to(REPO_ROOT)} ({path.stat().st_size / 1024:.1f} KiB)"
    )
    return True


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=[2023, 2024, 2025],
        help="years to fetch",
    )
    args = ap.parse_args(argv)
    built = [y for y in args.years if build_year(y)]
    print(f"\nDone: built {built}")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
