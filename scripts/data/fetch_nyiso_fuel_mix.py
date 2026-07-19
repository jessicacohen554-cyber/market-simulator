"""Fetch NYISO aggregate real-time fuel mix (P-63 RealTimeFuelMix) hourly.

Downloads the monthly 5-minute "Real-Time Fuel Mix" zip archives from the
NYISO MIS public site and writes one hourly-aggregated CSV.GZ per year to
``data/raw/NYISO/fuel-mix/NYISO_fuelmix_hourly_<year>.csv.gz``.

This is the NYISO analogue of the PJM "Generation by Fuel Type" feed
(``data/raw/ISO-specific-gen-data/PJM_<year>_gen_by_fuel.csv``): a system-wide
(NYCA) actual-generation-by-fuel-class series that gives a coarse class
envelope for the NYISO fuel-mix scoring target (CLAUDE.md C1). NYISO reports
seven fuel categories: Dual Fuel, Natural Gas, Nuclear, Hydro, Wind, Other
Renewables, Other Fossil Fuels. It is system-wide, not zonal — NYISO does NOT
publish cleared generation by zone as a public feed (only zonal LBMP *prices*,
which land under ``data/raw/lmp-data/NYISO``).

Source URL pattern (no authentication):
    http://mis.nyiso.com/public/csv/rtfuelmix/<yyyymm01>rtfuelmix_csv.zip

Aggregation (5-minute -> hourly), documented per CLAUDE.md rule 14 as a grain
reconciliation, not a resample choice hiding data: the source posts 12
5-minute observations per (fuel, hour) (~2,016 rows/day, ~110 MB/year zipped),
far above the model's hourly grain and too heavy to commit raw. Per
(fuel_category, hour-beginning):

    gen_mw       = mean of the 5-minute "Gen MW" observations
    n_intervals  = observation count (normally 12; 24 in the DST fall-back
                   hour; 0 = interior gap filled from the adjacent actual)

Timestamps: unlike ExternalLimitsFlows, this feed carries an explicit
``Time Zone`` column (EST/EDT), so the Eastern wall-clock stamp converts to UTC
exactly (EST = UTC-5, EDT = UTC-4) with no DST-ambiguity guessing. Hourly keys
are UTC; a naive local wall-clock column is carried for readability.

Year range: 2018 through H1-2026. Out-of-training years (2018-2022, 2026) are
intaken under the session-logged owner authorization of 2026-07-10 (CLAUDE.md
rule 22; itemized in docs/out-of-sample-results-2026-07.md §1.2). The
--end-month H1-2026 cap is enforced. This is a measured market *outcome* series
used only as a scoring target / bench (never fed back into the dispatch as an
input — rule 13), so it carries no forecast-input admissibility burden.

Run: ``python scripts/data/fetch_nyiso_fuel_mix.py [--cache-dir DIR]``
"""

from __future__ import annotations

import argparse
import io
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "raw" / "NYISO" / "fuel-mix"

MIS_BASE = "http://mis.nyiso.com/public/csv/rtfuelmix"

# Authorized acquisition window (rule 22; owner authorization 2026-07-10).
START_MONTH = "2018-01"
END_MONTH = "2026-06"  # H1-2026 hard cap — never extend without authorization

# Eastern offsets from UTC, indexed by the source's explicit Time Zone column.
_TZ_OFFSET_HOURS = {"EST": 5, "EDT": 4}


def _month_range(start: str, end: str) -> list[str]:
    """Inclusive list of YYYYMM month tokens between two YYYY-MM bounds."""
    return [p.strftime("%Y%m") for p in pd.period_range(start=start, end=end, freq="M")]


def _download(url: str, dest: Path, retries: int = 4) -> None:
    """Download ``url`` to ``dest`` unless already cached; simple retry loop."""
    if dest.is_file() and dest.stat().st_size > 0:
        return
    last: Exception | None = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=180) as resp:
                dest.write_bytes(resp.read())
            return
        except OSError as exc:
            last = exc
    raise RuntimeError(f"failed to download {url}: {last}")


def _to_utc(df: pd.DataFrame) -> pd.Series:
    """UTC timestamps from the Eastern wall-clock + explicit EST/EDT column."""
    ts = pd.to_datetime(df["Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    offsets = df["Time Zone"].astype(str).str.strip().map(_TZ_OFFSET_HOURS)
    if offsets.isna().any():
        bad = sorted(df.loc[offsets.isna(), "Time Zone"].astype(str).unique())
        raise ValueError(f"unrecognised Time Zone value(s): {bad}")
    utc = ts + pd.to_timedelta(offsets, unit="h")
    return utc.dt.tz_localize("UTC")


def _read_month(zpath: Path) -> pd.DataFrame:
    """Parse one monthly zip into a 5-minute frame with UTC timestamps."""
    parts: list[pd.DataFrame] = []
    with zipfile.ZipFile(zpath) as zf:
        for member in sorted(zf.namelist()):
            df = pd.read_csv(io.BytesIO(zf.read(member)))
            df = df.rename(columns=lambda c: c.strip())
            df["timestamp_utc"] = _to_utc(df)
            parts.append(df)
    return pd.concat(parts, ignore_index=True)


def _aggregate_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate the 5-minute frame to hour-beginning per fuel category."""
    df = df.assign(hour_utc=df["timestamp_utc"].dt.floor("h"))
    g = df.groupby(["Fuel Category", "hour_utc"], sort=True)
    out = g.agg(
        gen_mw=("Gen MW", "mean"),
        n_intervals=("Gen MW", "size"),
    ).reset_index()
    out = out.rename(
        columns={"Fuel Category": "fuel_category", "hour_utc": "interval_start_utc"}
    )
    out = _fill_interior_gaps(out)
    local = (
        out["interval_start_utc"].dt.tz_convert("America/New_York").dt.tz_localize(None)
    )
    out.insert(1, "interval_start_local", local)
    out["gen_mw"] = out["gen_mw"].round(2)
    return out.sort_values(["fuel_category", "interval_start_utc"], ignore_index=True)


def _fill_interior_gaps(hourly: pd.DataFrame) -> pd.DataFrame:
    """Fill missing interior hours from adjacent actuals (mirrors interface-flows).

    The MIS source occasionally drops a handful of hours per year. Per fuel
    category, reindex the UTC hourly range between that category's FIRST and
    LAST observed hour and forward-fill ``gen_mw`` from the previous actual
    (back-fill only for a gap at the very start). Filled rows carry
    ``n_intervals = 0`` so consumers can always separate measured from
    gap-filled hours. Hours outside a category's observed span are never
    invented.
    """
    parts: list[pd.DataFrame] = []
    for fuel, g in hourly.groupby("fuel_category"):
        g = g.set_index("interval_start_utc").sort_index()
        full = pd.date_range(g.index.min(), g.index.max(), freq="h", tz="UTC")
        g = g.reindex(full)
        g.index.name = "interval_start_utc"
        g["fuel_category"] = fuel
        g["n_intervals"] = g["n_intervals"].fillna(0).astype("int64")
        g["gen_mw"] = g["gen_mw"].ffill().bfill()
        parts.append(g.reset_index())
    return pd.concat(parts, ignore_index=True)


def fetch(
    cache_dir: Path, start: str = START_MONTH, end: str = END_MONTH
) -> list[Path]:
    """Download, aggregate and write the per-year hourly fuel-mix CSVs.

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
            fname = f"{month}01rtfuelmix_csv.zip"
            zpath = cache_dir / fname
            _download(f"{MIS_BASE}/{fname}", zpath)
            frames.append(_read_month(zpath))
        five_min = pd.concat(frames, ignore_index=True)
        hourly = _aggregate_hourly(five_min)
        # Keep the file boundary on the LOCAL calendar year so each file is
        # exactly one NYISO year (a Dec-31 23:xx EST hour floors to Jan-1 UTC).
        local_year = hourly["interval_start_local"].dt.year
        hourly = hourly[local_year == year].reset_index(drop=True)
        out = OUT_DIR / f"NYISO_fuelmix_hourly_{year}.csv.gz"
        hourly.to_csv(out, index=False, compression="gzip")
        written.append(out)
        print(
            f"wrote {out}  ({len(hourly)} rows, "
            f"{hourly['fuel_category'].nunique()} fuel categories)"
        )
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/tmp/nyiso-rtfuelmix-cache"),
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
