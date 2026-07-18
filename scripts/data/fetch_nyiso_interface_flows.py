"""Fetch NYISO per-interface flows + limits (P-32 ExternalLimitsFlows) hourly.

Downloads the monthly 5-minute "Interface Limits and Flows" zip archives from
the NYISO MIS public site and writes one hourly-aggregated CSV.GZ per year to
``data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<year>.csv.gz``.

This is Ask D1 of `docs/handoffs/nyiso-data-asks-2026-07.md`: measured gross
per-interface flows and their posted limits for the internal NYISO interfaces
(CENTRAL EAST - VC, TOTAL EAST, UPNY CONED, MOSES SOUTH, DYSINGER EAST, WEST
CENTRAL, SPR/DUN-SOUTH) and every external tie (SCH - HQ/NE/OH/PJ plus the
controllable wires NPX_1385, NPX_CSC, PJM_HTP, PJM_NEPTUNE, PJM_VFT and the
HQ CEDARS/IMPORT_EXPORT schedules). It separates gross two-way wheeling from
the net-interchange wedge behind the upstate shoulder-collapse diagnosis
(2026-07-04 calibration log).

Source URL pattern (no authentication):
    http://mis.nyiso.com/public/csv/ExternalLimitsFlows/<yyyymm01>ExternalLimitsFlows_csv.zip

Aggregation (5-minute -> hourly), documented per CLAUDE.md rule 14 as a
grain reconciliation, not a resample choice hiding data: the source posts
~288 5-minute observations per interface-day (~95 MB/year zipped), far above
the model's hourly grain and too heavy to commit raw. Per (interface,
hour-beginning UTC):

    flow_mw            = mean of the 5-minute "Flow (MWH)" observations
    positive_limit_mw  = min of "Positive Limit (MWH)"  (most-binding rating)
    negative_limit_mw  = max of "Negative Limit (MWH)"  (most-binding; limits
                         are negative, so max is closest to zero)
    n_intervals        = observation count (24 in the DST fall-back hour;
                         0 = interior gap filled from the adjacent actual)

Timestamps: the source is Eastern prevailing wall-clock with no EDT/EST flag.
Rows within each daily file are in chronological order, so the duplicated
fall-back hour is disambiguated by first-occurrence = EDT before converting
to UTC (pandas tz_localize ambiguous array); the spring-forward hour has no
source rows. Hourly keys are UTC; a naive local wall-clock column is carried
for readability.

Year range: 2018 through H1-2026. Out-of-training years (2018-2022, 2026)
are intaken under the session-logged owner authorization of 2026-07-10
(CLAUDE.md rule 22; itemized in docs/out-of-sample-results-2026-07.md §1).
The --end-month H1-2026 cap is enforced.

Run: ``python scripts/data/fetch_nyiso_interface_flows.py [--cache-dir DIR]``
"""

from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "raw" / "NYISO" / "interface-flows"

MIS_BASE = "http://mis.nyiso.com/public/csv/ExternalLimitsFlows"

# Authorized acquisition window (rule 22; owner authorization 2026-07-10).
START_MONTH = "2018-01"
END_MONTH = "2026-06"  # H1-2026 hard cap — never extend without authorization

_TZ = "America/New_York"


def _month_range(start: str, end: str) -> list[str]:
    """Inclusive list of YYYYMM month tokens between two YYYY-MM bounds."""
    return [p.strftime("%Y%m") for p in pd.period_range(start=start, end=end, freq="M")]


def _download(url: str, dest: Path, retries: int = 4) -> None:
    """Download ``url`` to ``dest`` unless already cached; simple retry loop."""
    if dest.is_file() and dest.stat().st_size > 0:
        return
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=180) as resp:
                dest.write_bytes(resp.read())
            return
        except OSError as exc:
            last = exc
    raise RuntimeError(f"failed to download {url}: {last}")


def _localize_daily(df: pd.DataFrame) -> pd.Series:
    """UTC timestamps for one daily file's Eastern wall-clock stamps.

    The duplicated DST fall-back hour appears twice in file order; mark the
    first occurrence of each duplicated (timestamp, interface) pair as DST
    (EDT) and the second as standard (EST).
    """
    ts = pd.to_datetime(df["Timestamp"], format="%m/%d/%Y %H:%M")
    first = ~pd.Series(list(zip(ts.values, df["Interface Name"].values))).duplicated(
        keep="first"
    )
    ambiguous = first.to_numpy()
    return ts.dt.tz_localize(
        _TZ, ambiguous=ambiguous, nonexistent="raise"
    ).dt.tz_convert("UTC")


def _read_month(zpath: Path) -> pd.DataFrame:
    """Parse one monthly zip into a 5-minute frame with UTC timestamps."""
    parts: list[pd.DataFrame] = []
    with zipfile.ZipFile(zpath) as zf:
        for member in sorted(zf.namelist()):
            df = pd.read_csv(io.BytesIO(zf.read(member)))
            df = df.rename(columns=lambda c: c.strip())
            df["timestamp_utc"] = _localize_daily(df)
            parts.append(df)
    return pd.concat(parts, ignore_index=True)


def _aggregate_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the 5-minute frame to hour-beginning per interface."""
    df = df.assign(hour_utc=df["timestamp_utc"].dt.floor("h"))
    g = df.groupby(["Interface Name", "Point ID", "hour_utc"], sort=True)
    out = g.agg(
        flow_mw=("Flow (MWH)", "mean"),
        positive_limit_mw=("Positive Limit (MWH)", "min"),
        negative_limit_mw=("Negative Limit (MWH)", "max"),
        n_intervals=("Flow (MWH)", "size"),
    ).reset_index()
    out = out.rename(
        columns={
            "Interface Name": "interface",
            "Point ID": "point_id",
            "hour_utc": "interval_start_utc",
        }
    )
    out = _fill_interior_gaps(out)
    local = out["interval_start_utc"].dt.tz_convert(_TZ).dt.tz_localize(None)
    out.insert(3, "interval_start_local", local)
    out["flow_mw"] = out["flow_mw"].round(2)
    return out.sort_values(["interface", "interval_start_utc"], ignore_index=True)


def _fill_interior_gaps(hourly: pd.DataFrame) -> pd.DataFrame:
    """Fill missing hours from adjacent actual observations (owner 2026-07-10).

    The MIS source drops a handful of hours per year (1-3 system-wide, e.g.
    partial daily files). Per interface, reindex the UTC hourly range between
    that interface's FIRST and LAST observed hour and forward-fill flow and
    limits from the previous actual observation (back-fill only for a gap at
    the very start of the observed range). Filled rows carry
    ``n_intervals = 0`` so consumers can always separate measured from
    gap-filled hours. Hours before an interface first exists (e.g. CHPE
    pre-in-service in 2026) or after it last posts are NOT invented — only
    interior gaps are filled.
    """
    parts: list[pd.DataFrame] = []
    for (interface, point_id), g in hourly.groupby(["interface", "point_id"]):
        g = g.set_index("interval_start_utc").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq="h", tz="UTC")
        g = g.reindex(full)
        g.index.name = "interval_start_utc"
        g["interface"] = interface
        g["point_id"] = point_id
        g["n_intervals"] = g["n_intervals"].fillna(0).astype("int64")
        for col in ("flow_mw", "positive_limit_mw", "negative_limit_mw"):
            g[col] = g[col].ffill().bfill()
        parts.append(g.reset_index())
    return pd.concat(parts, ignore_index=True)


def fetch(
    cache_dir: Path, start: str = START_MONTH, end: str = END_MONTH
) -> list[Path]:
    """Download, aggregate and write the per-year hourly interface-flow CSVs.

    Returns the list of per-year ``.csv.gz`` paths written. Idempotent: monthly
    zips are cached in ``cache_dir`` and years are rebuilt from cache.
    """
    if end > END_MONTH:
        raise ValueError(
            f"end month {end} exceeds the authorized acquisition cap {END_MONTH} "
            "(CLAUDE.md rule 22 holdout quarantine)"
        )
    cache_dir.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    months = _month_range(start, end)
    by_year: dict[int, list[str]] = {}
    for m in months:
        by_year.setdefault(int(m[:4]), []).append(m)

    written: list[Path] = []
    for year, year_months in sorted(by_year.items()):
        frames = []
        for month in year_months:
            fname = f"{month}01ExternalLimitsFlows_csv.zip"
            zpath = cache_dir / fname
            _download(f"{MIS_BASE}/{fname}", zpath)
            frames.append(_read_month(zpath))
        five_min = pd.concat(frames, ignore_index=True)
        hourly = _aggregate_hourly(five_min)
        # Guard: a UTC-floored December 31 23:xx EST hour belongs to Jan 1
        # UTC of the next year; keep the file boundary on the LOCAL year so
        # each file is exactly one NYISO calendar year.
        local_year = hourly["interval_start_local"].dt.year
        hourly = hourly[local_year == year].reset_index(drop=True)
        out = OUT_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz"
        hourly.to_csv(out, index=False, compression="gzip")
        written.append(out)
        print(
            f"wrote {out}  ({len(hourly)} rows, {hourly['interface'].nunique()} interfaces)"
        )
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/tmp/nyiso-mis-cache"),
        help="scratch directory for the downloaded monthly zips",
    )
    parser.add_argument("--start-month", default=START_MONTH, help="YYYY-MM")
    parser.add_argument(
        "--end-month", default=END_MONTH, help="YYYY-MM (capped at H1-2026)"
    )
    args = parser.parse_args(argv)
    fetch(args.cache_dir, args.start_month, args.end_month)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
