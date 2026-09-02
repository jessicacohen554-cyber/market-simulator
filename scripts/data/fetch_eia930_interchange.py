#!/usr/bin/env python3
"""Fetch the EIA-930 BA-to-BA hourly net interchange (``TI`` family) for one BA.

Produces the exact long-form schema of the existing extracts in
``data/raw/eia-930-interchange/`` (``CISO interchange hourly.parquet``,
``MISO interchange hourly.parquet``):

* ``diba`` (category) — the directly-interconnected balancing authority.
* ``mw`` (float32) — net interchange, EIA sign convention: positive = the
  fetched BA exports to the DIBA.
* ``local_time`` (datetime64[us], naive) — hour-ending timestamp on the BA's
  local clock (the UTC period converted to the BA timezone), spanning the
  requested local calendar years, e.g. 2023-01-01 01:00 .. 2026-01-01 00:00
  for ``--years 2023 2024 2025``.

The CISO/MISO siblings were manual pulls (their README documented this route
as the regeneration path); this script makes the pull reproducible and adds
new BAs (e.g. ISNE for the NEISO per-seam import-tranche calibration: DIBAs
HQT, NBSO, NYIS). Raw data is immutable: an existing output file is never
overwritten unless ``--force`` is passed.

Two interchangeable sources (``--source``), both EIA-published:

* ``api`` (default) — the EIA Open Data v2 ``interchange-data`` route. Needs
  an ``EIA_API_KEY``.
* ``bulk`` — EIA's "Hourly Electric Grid Monitor" six-month bulk CSVs
  (``gridmonitor/sixMonthFiles/EIA930_INTERCHANGE_<year>_<Jan_Jun|Jul_Dec>.csv``),
  the same archive family ``fetch_eia930_bulk_long.py`` already uses for the
  BALANCE product. **Requires NO API key**, which is what makes an
  out-of-training back-fill possible in an environment that has no key. The
  bulk file carries ``Local Time at End of Hour`` directly, so it lands on the
  same hour-ending local clock as the API path with no timezone round-trip.
  Rows are filtered to the requested BA while streaming, so the 100 MB+ CSVs
  are never written to disk. Verified equivalent to the ``api`` route over the
  committed 2023-2025 ISNE span (neiso-93, 2026-08-14).

Usage:
    EIA_API_KEY=... python scripts/data/fetch_eia930_interchange.py --ba ISNE \
        --years 2023 2024 2025
    python scripts/data/fetch_eia930_interchange.py --ba ISNE --source bulk \
        --years 2019 2020 2021 2022 --merge
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Reuse the paging + key resolution + BA-timezone map of the wide-extract
# fetcher (same EIA API v2).
sys.path.insert(
    0, str(Path(__file__).resolve().parents[2])
)  # repo root: canonical sibling import
from scripts.data.fetch_eia930_hourly import BA_TIMEZONE, _api_key, _fetch  # noqa: E402

INTERCHANGE_URL = "https://api.eia.gov/v2/electricity/rto/interchange-data/data/"
OUT_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "raw"
    / "eia-930-interchange"
)


def fetch_interchange(ba: str, years: list[int], key: str) -> pd.DataFrame:
    """Return the per-DIBA hourly net interchange for ``ba``'s local ``years``.

    Fetches ``facets[fromba]=ba`` from the EIA v2 ``interchange-data`` route
    (one row per UTC period per DIBA), converts the UTC hour-ending period to
    the BA's local clock, and trims to the hour-ending local span
    ``(Jan 1 00:00 of years[0], Jan 1 00:00 of years[-1]+1]``.
    """
    tz = BA_TIMEZONE.get(ba, "America/New_York")
    lo = pd.Timestamp(f"{years[0]}-01-01 00:00", tz=tz)
    hi = pd.Timestamp(f"{years[-1] + 1}-01-01 00:00", tz=tz)
    params = {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[fromba][]": ba,
        # UTC bounds enveloping the local span (hour-ending periods).
        "start": lo.tz_convert("UTC").strftime("%Y-%m-%dT%H"),
        "end": hi.tz_convert("UTC").strftime("%Y-%m-%dT%H"),
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }
    df = pd.DataFrame(_fetch(INTERCHANGE_URL, params, key))
    if df.empty:
        sys.exit(f"no interchange rows returned for {ba}")
    utc = pd.to_datetime(df["period"], utc=True)
    local = utc.dt.tz_convert(tz)
    out = pd.DataFrame(
        {
            "diba": df["toba"].astype("category"),
            "mw": pd.to_numeric(df["value"], errors="coerce").astype("float32"),
            "local_time": local.dt.tz_localize(None).astype("datetime64[us]"),
        }
    )
    keep = (local > lo) & (local <= hi)
    out = out[keep.to_numpy()]
    return out.sort_values(["local_time", "diba"], kind="stable").reset_index(drop=True)


BULK_URL = (
    "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/"
    "EIA930_INTERCHANGE_{year}_{half}.csv"
)
# Bulk-CSV column -> the tidy schema above. "Local Time at End of Hour" is
# already the hour-ending local clock the API path derives by tz-converting
# the UTC period, so no conversion is applied to it.
_BULK_COLS = {
    "Balancing Authority": "ba",
    "Directly Interconnected Balancing Authority": "diba",
    "Interchange (MW)": "mw",
    "Local Time at End of Hour": "local_time",
}


def fetch_interchange_bulk(ba: str, years: list[int]) -> pd.DataFrame:
    """Return the per-DIBA hourly net interchange for ``ba`` from the bulk CSVs.

    The keyless counterpart of :func:`fetch_interchange`. Each six-month bulk
    file is streamed and filtered to ``ba`` chunk-by-chunk so the full 100 MB+
    CSV never lands on disk, then trimmed to the same hour-ending local span
    the API path returns.
    """
    import requests  # local import: the api path does not need it

    # No timezone conversion here: unlike the api path (which tz-converts a UTC
    # period), the bulk CSV already carries the BA's local hour-ending clock.
    lo = pd.Timestamp(f"{years[0]}-01-01 00:00")
    hi = pd.Timestamp(f"{years[-1] + 1}-01-01 00:00")
    frames: list[pd.DataFrame] = []
    for year in years:
        for half in ("Jan_Jun", "Jul_Dec"):
            url = BULK_URL.format(year=year, half=half)
            with requests.get(url, stream=True, timeout=300) as resp:
                if resp.status_code != 200:
                    print(f"  {year} {half}: HTTP {resp.status_code} — skipped")
                    continue
                resp.raw.decode_content = True
                kept = 0
                for chunk in pd.read_csv(
                    resp.raw,
                    usecols=list(_BULK_COLS),
                    dtype=str,
                    chunksize=500_000,
                ):
                    chunk = chunk.rename(columns=_BULK_COLS)
                    sel = chunk[chunk["ba"] == ba]
                    if not sel.empty:
                        frames.append(sel.drop(columns=["ba"]))
                        kept += len(sel)
                print(f"  {year} {half}: {kept:,} {ba} rows")
    if not frames:
        sys.exit(f"no bulk interchange rows returned for {ba}")

    raw = pd.concat(frames, ignore_index=True)
    local = pd.to_datetime(raw["local_time"], format="%m/%d/%Y %I:%M:%S %p")
    out = pd.DataFrame(
        {
            "diba": raw["diba"].astype("category"),
            # The bulk CSV thousands-separates its MW values ("1,091").
            "mw": pd.to_numeric(
                raw["mw"].str.replace(",", "", regex=False), errors="coerce"
            ).astype("float32"),
            "local_time": local.astype("datetime64[us]"),
        }
    )
    out = out[(out["local_time"] > lo) & (out["local_time"] <= hi)]
    return out.sort_values(["local_time", "diba"], kind="stable").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. ISNE")
    ap.add_argument(
        "--source",
        choices=("api", "bulk"),
        default="api",
        help="api = EIA Open Data v2 (needs EIA_API_KEY); bulk = the keyless "
        "Grid Monitor six-month CSVs (default api).",
    )
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024, 2025],
        help="Local calendar years to cover (default 2023 2024 2025).",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output parquet (default data/raw/eia-930-interchange/"
        "'<BA> interchange hourly.parquet').",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output file (raw data is otherwise "
        "immutable — refuse to clobber).",
    )
    ap.add_argument(
        "--merge",
        action="store_true",
        help="Merge the fetched years into an existing output instead of "
        "replacing it: every already-committed (local_time, diba) row is kept "
        "byte-identical and only hours the file does not carry are added, so "
        "a holdout back-fill cannot move an in-sample year.",
    )
    ap.add_argument(
        "--end-date",
        type=pd.Timestamp,
        default=None,
        help="Drop fetched rows at or after this naive local timestamp "
        "(YYYY-MM-DD); pins a partial year to an exact window, e.g. "
        "2026-07-01 for the H1-2026 holdout edge.",
    )
    args = ap.parse_args()

    out = args.out or OUT_DIR / f"{args.ba} interchange hourly.parquet"
    if out.exists() and not (args.force or args.merge):
        sys.exit(
            f"{out} exists — pass --merge to back-fill it, or --force to "
            "overwrite (data/raw is otherwise immutable)."
        )

    years = sorted(args.years)
    if args.source == "bulk":
        frame = fetch_interchange_bulk(args.ba, years)
    else:
        frame = fetch_interchange(args.ba, years, _api_key())
    if args.end_date is not None:
        frame = frame[frame["local_time"] < args.end_date].reset_index(drop=True)
    if args.merge and out.exists():
        existing = pd.read_parquet(out)
        # Drop every fetched row whose (local_time, diba) the file ALREADY
        # carries, then concatenate — the committed rows pass through
        # untouched. A blanket drop_duplicates would be wrong: the DST
        # fall-back hour legitimately repeats a (local_time, diba) key twice
        # (naive local clock), and de-duplicating would silently delete one of
        # the two committed rows for that hour.
        have = set(map(tuple, existing[["local_time", "diba"]].to_numpy()))
        keys = map(tuple, frame[["local_time", "diba"]].to_numpy())
        fresh = frame[[k not in have for k in keys]]
        combined = pd.concat([existing, fresh], ignore_index=True)
        combined["diba"] = combined["diba"].astype("category")
        frame = combined.sort_values(["local_time", "diba"], kind="stable").reset_index(
            drop=True
        )
        print(f"merge: kept {len(existing):,} rows, file now {len(frame):,}")
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(out, index=False)
    span = f"{frame['local_time'].min()}..{frame['local_time'].max()}"
    dibas = ", ".join(sorted(frame["diba"].cat.categories))
    print(f"wrote {out} — {len(frame):,} rows ({span}; DIBAs: {dibas})")


if __name__ == "__main__":
    main()
