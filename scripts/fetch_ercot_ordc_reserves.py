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

The report's SCED timestamps are Central *Prevailing* Time (CPT: CDT in
summer), with the fall-back repeated hour disambiguated by the report's own
"Repeated Hour Flag" column. They are converted CPT -> CST (fixed UTC-6, the
model clock — reusing ``build_ercot_hsl._prevailing_to_standard``) BEFORE
placement, then the ~5-minute intervals are averaged to hourly on the fixed
non-leap 8760-hour clock (Feb 29 dropped) — matching the ``ERCO hourly``
demand clock. (The pre-2026-07-07 build placed the CPT labels unconverted, so
the whole mid-Mar–early-Nov series ran one hour late — Jan best lag 0 / Jul
best lag +1 vs EIA-930 across all three years, the same placement defect class
as the NP4-732/737 HSL intake; see
``docs/handoffs/ercot-g22-demand-side-design-2026-07.md`` §7.)

Physically impossible interval values (an MW capability outside
``[0, _MW_PLAUSIBLE_MAX]``, e.g. the corrupt 2024 PRC interval that dragged an
hourly mean to -56M MW) are nulled as telemetry corruption and interpolated,
with the nulled count flagged in the parquet metadata — never ingested as
measured.

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

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from build_ercot_hsl import _prevailing_to_standard  # noqa: E402

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
# The report's own fall-back disambiguator: 'Y' marks the second occurrence of
# the repeated 01:00-02:00 prevailing hour (already back on CST).
FLAG_COL = "Repeated Hour Flag"
# Largest hole (hours) interpolated when placing the series on the 8760 clock —
# more than a day missing means the archive is incomplete and the year is
# rejected rather than fabricated. (After the CPT->CST conversion the clock is
# gapless by construction, so interior holes are genuine telemetry gaps.)
_MAX_GAP_HOURS = 24

# Physical plausibility ceiling for the MW capability/reserve columns: the
# entire ERCOT fleet is < 200 GW installed, so any interval value outside
# [0, 200 GW] is telemetry corruption (e.g. the corrupt 2024 PRC interval,
# hourly-mean min -56,246,692 MW in the pre-fix parquet), nulled + flagged and
# interpolated — never ingested as measured. Price columns are NOT bounded
# (negative lambda is legitimate).
_MW_PLAUSIBLE_MAX = 200_000.0
_MW_COLS = ("prc", "rtolcap", "rtoffcap", "rtolhsl")


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
    """Concatenate the twelve monthly sheets into one SCED-interval frame.

    The SCED timestamps are Central Prevailing Time and are converted to the
    fixed CST model clock here (``_prevailing_to_standard``), with the report's
    "Repeated Hour Flag" disambiguating the fall-back repeated hour. A stamp
    that cannot be placed (an unflagged ambiguous repeat / malformed
    spring-forward row) becomes NaT and is dropped.
    """
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
        raw_ts = pd.to_datetime(sub[TS_COL], errors="coerce")
        flag = df[FLAG_COL] if FLAG_COL in df.columns else None
        sub["ts"] = _prevailing_to_standard(raw_ts, flag)
        sub = sub.dropna(subset=["ts"])
        frames.append(sub)
    if not frames:
        sys.exit("no monthly sheet carried a 'SCED Timestamp' column")
    out = pd.concat(frames, ignore_index=True)
    return out.rename(columns=COLUMN_MAP)


def _null_implausible_mw(intervals: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Null MW-capability interval values outside the physical bound.

    Returns the cleaned frame and the count of nulled cells (telemetry
    corruption, e.g. the cited corrupt 2024 PRC interval). Nulled cells become
    interior NaN holes that ``_interp_short_gaps`` fills like any other
    telemetry gap.
    """
    nulled = 0
    for col in _MW_COLS:
        if col not in intervals.columns:
            continue
        vals = pd.to_numeric(intervals[col], errors="coerce")
        bad = (vals < 0.0) | (vals > _MW_PLAUSIBLE_MAX)
        nulled += int(bad.sum())
        intervals[col] = vals.mask(bad)
    return intervals, nulled


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
    CST ``(month, day, hour)`` — collapsing sub-hourly intervals (timestamps
    are already on the fixed CST clock, so DST needs no handling here) — then
    reindexes onto the fixed non-leap hourly calendar. Short interior gaps are
    interpolated; a long contiguous tail (a regime boundary such as RTC+B) is
    preserved as NaN.
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
    intervals, nulled = _null_implausible_mw(intervals)
    if nulled:
        print(
            f"   {nulled} physically-impossible MW interval value(s) nulled "
            f"(outside [0, {_MW_PLAUSIBLE_MAX:.0f}] MW) and interpolated"
        )
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
            "clock": (
                "Fixed non-leap 8760h ERCOT-local STANDARD time (CST, UTC-6): "
                "the report's Central-Prevailing SCED stamps are converted "
                "CPT->CST before placement (Repeated Hour Flag disambiguates "
                "the fall-back repeat), matching the EIA-930 demand clock."
            ),
            "quality": (
                f"{nulled} physically-impossible MW interval value(s) "
                f"(outside [0, {_MW_PLAUSIBLE_MAX:.0f}] MW) nulled as telemetry "
                "corruption and interpolated."
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
