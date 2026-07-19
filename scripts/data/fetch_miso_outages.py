"""Fetch + consolidate MISO's published generation-outage / capacity-availability record.

Source: the public daily market report
``https://docs.misoenergy.org/marketreports/YYYYMMDD_mom.xlsx`` (Multiday
Operating Margin Forecast Report, no auth), **OUTAGE** sheet. Each file carries
two blocks of MISO's own outage bookkeeping, in MW, by operating **region**
(North / Central / South, and the ``MISO`` system total = North+Central+South)
and by **cause type** (Derated / Forced / Planned / Unplanned):

  * a **7-day look-ahead** forecast block (published on the filename date), and
  * a **30-day look-back** *estimated* (actual) block -- MISO's settled
    estimate of how much capacity was actually offline each of the prior 30
    days.

This is the MISO analog of the measured DAM capacity-availability record the
model overlays for ERCOT (``ercot-thermal-dam-availability.csv``, from ERCOT's
60-Day DAM disclosure). Unlike the ERCOT DAM disclosure it is **aggregate
grain only** -- the public report carries no unit or fuel-class identity, only a
regional cause-type total -- so it enters the model as a region availability
*envelope*, not a per-unit derate. See ``market_sim.data.miso_outages`` for the
loader and ``docs/data-licensing.md`` for the licence/citation.

**Coverage.** MISO began publishing ``_mom.xlsx`` on **2023-01-01**; earlier
dates 404 (verified 2018-2022). So the honest maximum span is 2023-01-01 ->
present, well short of the requested 2018 floor -- MISO does not publish this
series before 2023.

**Reconstruction.** Because each file's estimated block re-states the prior 30
days and MISO revises the estimate as the days settle, the script downloads
files on a fixed stride (default weekly), then for each
``(region, cause_type, interval_date)`` keeps the estimate from the **latest
publishing file that still covers that day** -- i.e. the most-settled estimate,
bounded to <= ~30 days after the fact by the 30-day look-back window. Weekly
stride guarantees full day coverage (consecutive 30-day windows overlap by ~23
days) with ~4 overlapping estimates per day to settle from. Two parquets are
written:

    data/raw/miso-generation-outages/miso_generation_outages_estimated.parquet
    data/raw/miso-generation-outages/miso_generation_outages_forecast.parquet

The estimated parquet is the backcast intake (the actuals); the forecast
parquet is the forward-looking outage signal (kept for provenance / a future
forecast-mode use). A ``_SOURCE.md`` sidecar records the citation + disclaimer.

**Quarantine guard (CLAUDE.md rule 22).** Intake is permitted for any period
under explicit, session-logged owner authorization, but this is DATA INTAKE
only -- no solve, no scoring. The script refuses interval years outside the
2023-2025 calibration train window unless ``--allow-out-of-train`` is passed
(the 2026 forward-edge partition is in scope for this authorized intake). No
downloaded file is ever fed to an LP by this script.

Usage::

    # authorized full available span (2023-01-01 -> yesterday), incl. 2026
    python scripts/data/fetch_miso_outages.py --allow-out-of-train

    # train window only
    python scripts/data/fetch_miso_outages.py --start 2023-01-01 --end 2025-12-31

    # offline re-consolidation from a prior download cache (no network)
    python scripts/data/fetch_miso_outages.py --from-cache --cache-dir /path/to/xlsx
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "raw" / "miso-generation-outages"
BASE_URL = "https://docs.misoenergy.org/marketreports"

# MISO started publishing the mom report here; earlier dates 404.
EARLIEST_AVAILABLE = date(2023, 1, 1)

# CLAUDE.md rule 22: the calibration train window. Interval dates outside it
# need explicit, session-logged owner authorization (--allow-out-of-train).
TRAIN_YEARS = (2023, 2024, 2025)

# OUTAGE-sheet vocabulary (the 4 regions x 4 cause types the report tabulates).
REGIONS = ("North", "Central", "South", "MISO")
CAUSE_TYPES = ("Derated", "Forced", "Planned", "Unplanned")
_REGIONS_LC = {r.lower(): r for r in REGIONS}
_TYPES_LC = {t.lower(): t for t in CAUSE_TYPES}

# Each 30-day look-back file covers [publish-29, publish]. Consecutive weekly
# files overlap by ~23 days, so weekly stride fully tiles the day axis.
DEFAULT_STRIDE_DAYS = 7
# When a scheduled publish date 404s (rare gaps), try the next few days so the
# stride keeps roughly its cadence rather than opening a hole.
FALLBACK_DAYS = 3
RETRIES = 4  # network retries per URL (exponential backoff 2/4/8/16s)


def _daterange(start: date, end: date, stride: int):
    """Yield dates from ``start`` to ``end`` inclusive on a fixed stride."""
    d = start
    while d <= end:
        yield d
        d += timedelta(days=stride)


def _url_for(d: date) -> str:
    return f"{BASE_URL}/{d.strftime('%Y%m%d')}_mom.xlsx"


def _download(d: date, cache_dir: Path, verbose: bool) -> Path | None:
    """Download one day's mom.xlsx into ``cache_dir``; return its path or None.

    Cached files are reused. A 404 returns None (caller handles the gap);
    transient network errors retry with exponential backoff.
    """
    dest = cache_dir / f"{d.strftime('%Y%m%d')}_mom.xlsx"
    if dest.exists() and dest.stat().st_size > 1000:
        return dest
    url = _url_for(d)
    for attempt in range(RETRIES):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "market-sim/1.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if len(data) < 1000:
                return None
            dest.write_bytes(data)
            if verbose:
                print(f"  downloaded {url} ({len(data):,} bytes)")
            return dest
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            if attempt == RETRIES - 1:
                print(
                    f"  WARN {url}: HTTP {exc.code} after {RETRIES} tries",
                    file=sys.stderr,
                )
                return None
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == RETRIES - 1:
                print(f"  WARN {url}: {exc} after {RETRIES} tries", file=sys.stderr)
                return None
        time.sleep(2 ** (attempt + 1))
    return None


def _download_with_fallback(d: date, cache_dir: Path, verbose: bool) -> Path | None:
    """Download ``d``'s file, falling forward up to FALLBACK_DAYS on a 404."""
    for offset in range(FALLBACK_DAYS + 1):
        path = _download(d + timedelta(days=offset), cache_dir, verbose)
        if path is not None:
            return path
    return None


def _parse_date_header(cell: object) -> date | None:
    """Parse an OUTAGE date-header cell (e.g. '6/16/24 **') to a date."""
    if cell is None:
        return None
    if isinstance(cell, datetime):
        return cell.date()
    if isinstance(cell, date):
        return cell
    s = str(cell).replace("**", "").strip()
    if not s:
        return None
    for fmt in ("%m/%d/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _parse_outage_sheet(xlsx_path: Path, publish_date: date):
    """Parse one file's OUTAGE sheet into forecast + estimated long records.

    Returns ``(forecast_rows, estimated_rows)`` where each row is a dict
    ``{publish_date, region, cause_type, interval_date, outage_mw}``. Robust to
    row shifts: it locates each block by its 'look-ahead' / 'look back' marker,
    reads the following date-header row, then the consecutive (region, type)
    data rows -- rather than hardcoding sheet offsets.
    """
    import openpyxl

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        if "OUTAGE" not in wb.sheetnames:
            return [], []
        ws = wb["OUTAGE"]
        rows = [list(r) for r in ws.iter_rows(values_only=True)]

    def _block_marker(row, needle: str) -> bool:
        return any(
            isinstance(c, str) and needle in c.lower().replace("-", " ") for c in row
        )

    def _extract(marker_idx: int) -> list[dict]:
        # The date header is the first row after the marker that parses >= 1
        # date in cols >= 2; data rows follow until the region/type run ends.
        hdr_idx = None
        for i in range(marker_idx + 1, min(marker_idx + 4, len(rows))):
            dates = [_parse_date_header(c) for c in rows[i][2:]]
            if any(d is not None for d in dates):
                hdr_idx = i
                break
        if hdr_idx is None:
            return []
        header_dates = [_parse_date_header(c) for c in rows[hdr_idx][2:]]
        out: list[dict] = []
        for i in range(hdr_idx + 1, len(rows)):
            row = rows[i]
            region_cell = row[0] if len(row) > 0 else None
            type_cell = row[1] if len(row) > 1 else None
            region = (
                _REGIONS_LC.get(str(region_cell).strip().lower())
                if region_cell
                else None
            )
            ctype = _TYPES_LC.get(str(type_cell).strip().lower()) if type_cell else None
            if region is None or ctype is None:
                # allow a single blank row inside a block; stop after the run
                if out and (region_cell is None and type_cell is None):
                    break
                continue
            for j, idate in enumerate(header_dates):
                if idate is None:
                    continue
                val = row[2 + j] if len(row) > 2 + j else None
                if val is None or (isinstance(val, str) and not val.strip()):
                    continue
                try:
                    mw = float(val)
                except (TypeError, ValueError):
                    continue
                out.append(
                    {
                        "publish_date": publish_date,
                        "region": region,
                        "cause_type": ctype,
                        "interval_date": idate,
                        "outage_mw": mw,
                    }
                )
        return out

    fore_idx = est_idx = None
    for i, row in enumerate(rows):
        if fore_idx is None and _block_marker(row, "look ahead"):
            fore_idx = i
        elif est_idx is None and _block_marker(row, "look back"):
            est_idx = i
    forecast = _extract(fore_idx) if fore_idx is not None else []
    estimated = _extract(est_idx) if est_idx is not None else []
    return forecast, estimated


def _settle_estimated(rows: list[dict]) -> pd.DataFrame:
    """Collapse overlapping estimated rows to the most-settled per interval.

    For each ``(region, cause_type, interval_date)`` keep the record from the
    file with the latest ``publish_date`` (the settled estimate; bounded to
    <= ~30 days after the fact by the look-back window).
    """
    if not rows:
        return pd.DataFrame(
            columns=[
                "interval_date",
                "region",
                "cause_type",
                "outage_mw",
                "publish_date",
            ]
        )
    df = pd.DataFrame(rows)
    df = df.sort_values("publish_date")
    df = df.drop_duplicates(
        subset=["region", "cause_type", "interval_date"], keep="last"
    )
    return df.sort_values(["interval_date", "region", "cause_type"]).reset_index(
        drop=True
    )


def _finalize(df: pd.DataFrame) -> pd.DataFrame:
    """Type-normalize a long outage frame for compact parquet storage."""
    if df.empty:
        return df
    df = df.copy()
    df["interval_date"] = pd.to_datetime(df["interval_date"]).dt.date.astype(
        "datetime64[ns]"
    )
    df["publish_date"] = pd.to_datetime(df["publish_date"]).dt.date.astype(
        "datetime64[ns]"
    )
    df["region"] = df["region"].astype("category")
    df["cause_type"] = df["cause_type"].astype("category")
    df["outage_mw"] = df["outage_mw"].astype("float32")
    return df


def _write_source_sidecar(out_dir: Path, start: date, end: date, n_files: int) -> None:
    sidecar = out_dir / "_SOURCE.md"
    text = f"""# MISO generation-outage / capacity-availability record

**Source:** MISO Multiday Operating Margin Forecast Report, `OUTAGE` sheet
`https://docs.misoenergy.org/marketreports/YYYYMMDD_mom.xlsx` (public, no auth).

**Publisher:** Midcontinent Independent System Operator (MISO).

**What it is:** MISO's own bookkeeping of generation capacity offline, in MW,
by operating region (North / Central / South; `MISO` = the system total =
North+Central+South) and by cause type (Derated / Forced / Planned /
Unplanned). Each daily file carries a 7-day-ahead forecast block and a
30-day-look-back *estimated* (actual) block. Aggregate grain only -- no unit or
fuel-class identity (the public report does not disclose it).

**Files (committed, text — the in-repo source of truth):**
- `miso_outages_estimated_<year>.csv` -- the settled 30-day-look-back actuals
  (the backcast intake), one compact **wide** file per calendar year: an
  `interval_date` column + one `<Region>_<CauseType>` column per region×cause,
  integer MW. `outage_mw` is the most-settled estimate (from the latest file
  whose look-back window still covered the day). CSV rather than parquet because
  this repo's web-session push path is API-only (text) and cannot carry a binary
  parquet blob; the wide layout keeps each year ~34 KB.

**Files (local, efficient — gitignored; regenerate with this script):**
- `miso_generation_outages_estimated.parquet` -- the same actuals in long form
  with un-rounded MW + `publish_date` provenance.
- `miso_generation_outages_forecast.parquet` -- the 7-day-ahead forecast block
  (one row per publish_date, region, cause_type, interval_date); forward signal.

**Coverage built:** {start.isoformat()} -> {end.isoformat()} ({n_files} source
files). MISO does not publish `_mom.xlsx` before 2023-01-01 (2018-2022 dates
404), so the record cannot extend earlier.

**Rebuild:** `python scripts/data/fetch_miso_outages.py --allow-out-of-train`

**MISO disclaimer (verbatim from the report):** "MISO MAKES NO REPRESENTATIONS
OR WARRANTIES OF ANY KIND, EXPRESS OR IMPLIED, WITH RESPECT TO THE ACCURACY OR
ADEQUACY OF THE INFORMATION CONTAINED HEREIN." The data is provided by MISO for
informational purposes; see MISO's website terms of use.
"""
    sidecar.write_text(text)


def _write_wide_csvs(est: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Write the settled estimated series as compact per-year wide CSVs.

    One file per calendar year (``miso_outages_estimated_<year>.csv``): an
    ``interval_date`` column + one ``<Region>_<CauseType>`` column per
    region×cause (fixed order), integer MW. This is the committed in-repo form
    (text, pushable). Returns the paths written. Any prior wide CSVs are cleared
    first so a re-run never leaves a stale year behind.
    """
    for old in out_dir.glob("miso_outages_estimated_*.csv"):
        old.unlink()
    if est.empty:
        return []
    df = est.copy()
    df["col"] = df["region"].astype(str) + "_" + df["cause_type"].astype(str)
    wide = df.pivot_table(index="interval_date", columns="col", values="outage_mw")
    order = [f"{r}_{t}" for r in REGIONS for t in CAUSE_TYPES]
    wide = wide.reindex(columns=[c for c in order if c in wide.columns])
    wide = wide.round().astype("Int64")
    wide.index = pd.to_datetime(wide.index)
    written: list[Path] = []
    for year, sub in wide.groupby(wide.index.year):
        sub = sub.copy()
        sub.index = sub.index.date
        p = out_dir / f"miso_outages_estimated_{int(year)}.csv"
        sub.to_csv(p, index_label="interval_date")
        written.append(p)
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--start",
        default=EARLIEST_AVAILABLE.isoformat(),
        help="first publish date (YYYY-MM-DD; default 2023-01-01)",
    )
    ap.add_argument(
        "--end",
        default=(date.today() - timedelta(days=1)).isoformat(),
        help="last publish date (YYYY-MM-DD; default yesterday)",
    )
    ap.add_argument(
        "--stride-days",
        type=int,
        default=DEFAULT_STRIDE_DAYS,
        help="download cadence in days (default 7; <=30 tiles fully)",
    )
    ap.add_argument(
        "--cache-dir",
        default=None,
        help="dir for downloaded xlsx (default: a repo-local scratch dir)",
    )
    ap.add_argument(
        "--from-cache", action="store_true", help="parse cached xlsx only, no network"
    )
    ap.add_argument(
        "--allow-out-of-train",
        action="store_true",
        help="permit interval years outside 2023-2025 (rule 22; needs owner auth)",
    )
    ap.add_argument(
        "--include-forecast",
        action="store_true",
        default=True,
        help="also write the 7-day forecast parquet (default on)",
    )
    ap.add_argument("--no-forecast", dest="include_forecast", action="store_false")
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if start < EARLIEST_AVAILABLE:
        print(
            f"note: clamping --start {start} -> {EARLIEST_AVAILABLE} "
            f"(MISO publishes no mom.xlsx before then)"
        )
        start = EARLIEST_AVAILABLE
    if args.stride_days < 1 or args.stride_days > 30:
        ap.error("--stride-days must be in [1, 30] to fully tile the day axis")

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = Path(args.cache_dir) if args.cache_dir else (out_dir / "_xlsx_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Gather source files.
    if args.from_cache:
        files = sorted(cache_dir.glob("*_mom.xlsx"))
        print(f"parsing {len(files)} cached files from {cache_dir}")
    else:
        files = []
        scheduled = list(_daterange(start, end, args.stride_days))
        # Always include the true end date so the tail is covered.
        if scheduled and scheduled[-1] != end:
            scheduled.append(end)
        print(
            f"downloading ~{len(scheduled)} files ({start} -> {end}, stride {args.stride_days}d)"
        )
        for d in scheduled:
            path = _download_with_fallback(d, cache_dir, args.verbose)
            if path is not None:
                files.append(path)
        files = sorted(set(files))
        print(f"downloaded/parsable: {len(files)} files")

    if not files:
        print("no source files obtained; nothing to write", file=sys.stderr)
        return 1

    all_forecast: list[dict] = []
    all_estimated: list[dict] = []
    for path in files:
        try:
            pub = datetime.strptime(path.stem[:8], "%Y%m%d").date()
        except ValueError:
            continue
        forecast, estimated = _parse_outage_sheet(path, pub)
        all_forecast.extend(forecast)
        all_estimated.extend(estimated)

    est = _settle_estimated(all_estimated)

    # Rule-22 quarantine: refuse out-of-train interval years unless authorized.
    if not est.empty:
        years = sorted({d.year for d in pd.to_datetime(est["interval_date"]).dt.date})
        out_of_train = [y for y in years if y not in TRAIN_YEARS]
        if out_of_train and not args.allow_out_of_train:
            print(
                f"ERROR: estimated series contains out-of-train interval years "
                f"{out_of_train}; pass --allow-out-of-train under session-logged "
                f"owner authorization (CLAUDE.md rule 22). No file written.",
                file=sys.stderr,
            )
            return 2

    est = _finalize(est)
    # Local efficient artifact (gitignored): long form, un-rounded MW + publish.
    est_path = out_dir / "miso_generation_outages_estimated.parquet"
    est.to_parquet(est_path, engine="pyarrow", compression="zstd", index=False)
    # Committed in-repo form: compact per-year wide CSV (integer MW).
    csv_paths = _write_wide_csvs(est, out_dir)
    print(
        f"wrote {est_path}  ({len(est):,} rows, "
        f"{est['interval_date'].min().date() if len(est) else '-'} -> "
        f"{est['interval_date'].max().date() if len(est) else '-'})"
    )
    print(
        f"wrote {len(csv_paths)} per-year wide CSV(s): "
        f"{', '.join(p.name for p in csv_paths)}"
    )

    if args.include_forecast and all_forecast:
        fdf = pd.DataFrame(all_forecast)
        fdf = fdf.drop_duplicates(
            subset=["publish_date", "region", "cause_type", "interval_date"],
            keep="last",
        )
        if not args.allow_out_of_train:
            fdf = fdf[pd.to_datetime(fdf["interval_date"]).dt.year.isin(TRAIN_YEARS)]
        fdf = _finalize(
            fdf.sort_values(["publish_date", "interval_date", "region", "cause_type"])
        )
        fpath = out_dir / "miso_generation_outages_forecast.parquet"
        fdf.to_parquet(fpath, engine="pyarrow", compression="zstd", index=False)
        print(f"wrote {fpath}  ({len(fdf):,} rows)")

    _write_source_sidecar(out_dir, start, end, len(files))
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
