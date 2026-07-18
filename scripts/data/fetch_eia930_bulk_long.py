#!/usr/bin/env python3
"""Fetch EIA-930 long-form (tidy) fuel-mix + demand-family rows for one BA and
year from EIA's legacy "Hourly Electric Grid Monitor" six-month bulk CSV
archive, for years the v2 API (``electricity/rto/*``, what
``fetch_eia930_long.py`` uses) does not serve.

The v2 API's earliest period for every respondent checked (PJM, MISO, ERCO)
is 2019-01-01T00 UTC — 2018 and earlier return zero rows, API-wide, not a
PJM/MISO-specific gap. EIA's bulk archive
(``gridmonitor/sixMonthFiles/EIA930_BALANCE_<year>_<Jan_Jun|Jul_Dec>.csv``, all
BAs, six months per file) carries the same underlying measurements and goes
back to 2015-H2, letting this API-side gap year be filled from a different,
still-EIA-published channel.

Two caveats from EIA's own collection history, not from this script:

* Per-fuel net-generation columns were added to the bulk file starting the
  2018 Jul-Dec half (BA fuel-mix reporting compliance phased in mid-2018) —
  2018 Jan-Jun (and 2017 and earlier) carries demand/generation/interchange
  only, no fuel breakdown at all. So ``fetch_fueltype`` for 2018 covers Jul 1
  onward only; that is a genuine partial-year source limit.
* Hour-ending UTC labels don't align with the bulk file's local-calendar
  ``Data Date`` grouping: a target year's first few UTC hours (e.g. 2018-01-01
  T00-T05 for PJM/MISO) are filed under the *prior* year's Jul-Dec six-month
  file (``Data Date=12/31/<year-1>``), and the target year's own Jul-Dec file
  tail spills into the *next* UTC year (the year filter below drops those --
  the next year owns them). This module always pulls ``{year-1} Jul-Dec`` +
  ``{year} Jan-Jun`` + ``{year} Jul-Dec`` and reconstructs the exact UTC year
  from all three. The resulting ``period`` convention matches
  ``fetch_eia930_long.py`` exactly (cross-validated byte-for-byte against the
  existing 2019 siblings on overlapping hours): the v2 API's ``period`` is
  this archive's "UTC Time at End of Hour" column, parsed as-is.

Usage:
    python scripts/data/fetch_eia930_bulk_long.py --ba PJM --year 2018 \
        --out-fueltype data/raw/eia-930/PJM_fueltype_2018.parquet \
        --out-region data/raw/eia-930/PJM_region_2018.parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from tempfile import gettempdir

import pandas as pd
import requests

# Reuse the exact type-name strings the v2-API-backed sibling script uses.
sys.path.insert(0, str(Path(__file__).parent))
from fetch_eia930_long import _REGION_TYPE_NAMES

BULK_URL_TMPL = (
    "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"
    "EIA930_BALANCE_{year}_{half}.csv"
)

_UTC_COL = "UTC Time at End of Hour"
_BA_COL = "Balancing Authority"

# bulk-CSV column -> tidy region ``type`` code. "(Adjusted)" is EIA's final
# vetted series (raw + imputation), matching what the v2 API serves; the
# forecast has no raw/imputed/adjusted split.
_REGION_SOURCE_COLUMNS: dict[str, str] = {
    "D": "Demand (MW) (Adjusted)",
    "DF": "Demand Forecast (MW)",
    "NG": "Net Generation (MW) (Adjusted)",
    "TI": "Total Interchange (MW) (Adjusted)",
}

# bulk-CSV fuel column -> (fueltype code, type_name), matching the exact
# code/type_name strings already used by the existing 2019-2021 sibling files.
_FUEL_SOURCE_COLUMNS: dict[str, tuple[str, str]] = {
    "Net Generation (MW) from Coal (Adjusted)": ("COL", "Coal"),
    "Net Generation (MW) from Natural Gas (Adjusted)": ("NG", "Natural Gas"),
    "Net Generation (MW) from Nuclear (Adjusted)": ("NUC", "Nuclear"),
    "Net Generation (MW) from All Petroleum Products (Adjusted)": ("OIL", "Petroleum"),
    "Net Generation (MW) from Hydropower and Pumped Storage (Adjusted)": (
        "WAT",
        "Hydro",
    ),
    "Net Generation (MW) from Solar (Adjusted)": ("SUN", "Solar"),
    "Net Generation (MW) from Wind (Adjusted)": ("WND", "Wind"),
    "Net Generation (MW) from Other Fuel Sources (Adjusted)": ("OTH", "Other"),
    "Net Generation (MW) from Unknown Fuel Sources (Adjusted)": ("UNK", "Unknown"),
}

_FUELTYPE_COLUMNS = ["period", "iso", "fueltype", "type_name", "value_mwh"]
_REGION_COLUMNS = ["period", "iso", "type", "type_name", "value_mwh"]


def _bulk_path(year: int, half: str, cache_dir: Path) -> Path:
    return cache_dir / f"EIA930_BALANCE_{year}_{half}.csv"


def _ensure_downloaded(year: int, half: str, cache_dir: Path) -> Path:
    """Download one six-month all-BA bulk CSV, reusing an on-disk cache."""
    path = _bulk_path(year, half, cache_dir)
    if path.exists():
        return path
    cache_dir.mkdir(parents=True, exist_ok=True)
    url = BULK_URL_TMPL.format(year=year, half=half)
    tmp = path.with_suffix(".csv.part")
    with requests.get(url, stream=True, timeout=300) as resp:
        resp.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.rename(path)
    return path


def _half_years_needed(year: int) -> list[tuple[int, str]]:
    """Six-month files covering a full UTC year, incl. hour-ending boundary spillover."""
    return [(year - 1, "Jul_Dec"), (year, "Jan_Jun"), (year, "Jul_Dec")]


def _load_ba_slice(
    year: int, ba: str, cache_dir: Path, columns: list[str]
) -> pd.DataFrame:
    """Concatenate one BA's rows across the 3 six-month files a year needs.

    A ``columns`` entry the file's own header lacks (older halves have no
    per-fuel columns at all -- a real reporting-history gap) comes back
    all-NaN for that half rather than raising.
    """
    frames = []
    for yr, half in _half_years_needed(year):
        path = _ensure_downloaded(yr, half, cache_dir)
        header = pd.read_csv(path, nrows=0).columns
        usecols = [c for c in (_BA_COL, _UTC_COL, *columns) if c in header]
        df = pd.read_csv(path, usecols=usecols, dtype=str)
        df = df[df[_BA_COL] == ba].copy()
        for col in columns:
            if col not in df.columns:
                df[col] = pd.NA
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["period"] = pd.to_datetime(
        out[_UTC_COL], format="%m/%d/%Y %I:%M:%S %p", utc=True
    ).astype("datetime64[ns, UTC]")
    return out[out["period"].dt.year == year].reset_index(drop=True)


def fetch_region(ba: str, year: int, cache_dir: Path) -> pd.DataFrame:
    """Tidy demand-family (D/DF/NG/TI) rows in the ``<BA>_region`` schema."""
    raw = _load_ba_slice(year, ba, cache_dir, list(_REGION_SOURCE_COLUMNS.values()))
    if raw.empty:
        return pd.DataFrame(columns=_REGION_COLUMNS).astype({"value_mwh": float})
    rows = []
    for code, col in _REGION_SOURCE_COLUMNS.items():
        rows.append(
            pd.DataFrame(
                {
                    "period": raw["period"],
                    "iso": ba,
                    "type": code,
                    "type_name": _REGION_TYPE_NAMES[code],
                    "value_mwh": pd.to_numeric(raw[col], errors="coerce"),
                }
            )
        )
    out = pd.concat(rows, ignore_index=True).dropna(subset=["value_mwh"])
    out["iso"] = out["iso"].astype("string").astype(object)
    out["type"] = out["type"].astype("string").astype(object)
    out["type_name"] = out["type_name"].astype("string").astype(object)
    out["value_mwh"] = out["value_mwh"].astype(float)
    return out.sort_values(["period", "type"], kind="stable").reset_index(drop=True)


def fetch_fueltype(ba: str, year: int, cache_dir: Path) -> pd.DataFrame:
    """Tidy per-fuel net-generation rows in the ``<BA>_fueltype`` schema.

    Only hours whose six-month file actually carries per-fuel columns
    contribute rows (2018 Jan-Jun and earlier have none); a fuel code that
    never has a real value for this BA (e.g. MISO has no Petroleum rows in the
    existing 2019-2021 siblings) is omitted entirely, matching that same
    per-BA convention rather than emitting an all-empty code.
    """
    cols = list(_FUEL_SOURCE_COLUMNS.keys())
    raw = _load_ba_slice(year, ba, cache_dir, cols)
    rows = []
    for col, (code, name) in _FUEL_SOURCE_COLUMNS.items():
        vals = pd.to_numeric(raw[col], errors="coerce")
        if vals.notna().sum() == 0:
            continue
        rows.append(
            pd.DataFrame(
                {
                    "period": raw["period"],
                    "iso": ba,
                    "fueltype": code,
                    "type_name": name,
                    "value_mwh": vals,
                }
            )
        )
    if not rows:
        return pd.DataFrame(columns=_FUELTYPE_COLUMNS).astype({"value_mwh": float})
    out = pd.concat(rows, ignore_index=True).dropna(subset=["value_mwh"])
    out["iso"] = out["iso"].astype("string").astype(object)
    out["fueltype"] = out["fueltype"].astype("string").astype(object)
    out["type_name"] = out["type_name"].astype("string").astype(object)
    out["value_mwh"] = out["value_mwh"].astype(float)
    return out.sort_values(["period", "fueltype"], kind="stable").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. PJM")
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out-fueltype", type=Path, required=True)
    ap.add_argument("--out-region", type=Path, required=True)
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=Path(gettempdir()) / "eia930_bulk_cache",
        help="Where to cache downloaded six-month all-BA CSVs (30-45MB each; "
        "reused across BAs/years run against the same cache dir).",
    )
    args = ap.parse_args()

    for name, fn, out in (
        ("fueltype", fetch_fueltype, args.out_fueltype),
        ("region", fetch_region, args.out_region),
    ):
        frame = fn(args.ba, args.year, args.cache_dir)
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(out, index=False)
        span = (
            f"{frame['period'].min()}..{frame['period'].max()}"
            if len(frame)
            else "empty"
        )
        print(f"wrote {out} — {len(frame):,} {name} rows ({span})")


if __name__ == "__main__":
    main()
