#!/usr/bin/env python3
"""Fetch EIA-930 long-form (tidy) fuel-mix + demand-family rows for one BA.

Produces the exact tidy schema of the existing bench actuals in ``data/raw``
(e.g. ``ERCO_fueltype.parquet`` / ``ERCO_region.parquet``, 2023-2025):

* ``<BA>_fueltype``: period (UTC, tz-aware ns), iso, fueltype, type_name,
  value_mwh — one row per (hour, fuel code) from the EIA v2
  ``electricity/rto/fuel-type-data`` route.
* ``<BA>_region``: period, iso, type, type_name, value_mwh — the demand
  family (D / DF / NG / TI) from ``electricity/rto/region-data``.

The 2023-2025 siblings were hand-uploaded bulk extracts; this script makes the
pull reproducible for extending coverage to new years (e.g. the 2022 /
H1-2026 holdout intake). Raw data is immutable: new years land as NEW
year-suffixed files beside the originals (``--out-fueltype/--out-region``),
never appended in place.

Usage:
    EIA_API_KEY=... python scripts/fetch_eia930_long.py --ba ERCO \
        --start 2022-01-01 --end 2022-12-31 \
        --out-fueltype data/raw/ERCO_fueltype_2022.parquet \
        --out-region data/raw/ERCO_region_2022.parquet
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Reuse the paging + key resolution of the wide-extract fetcher (same API).
sys.path.insert(0, str(Path(__file__).parent))
from fetch_eia930_hourly import FUEL_URL, REGION_URL, _api_key, _fetch

# region-data ``type`` code -> human-readable name, matching the uploaded
# 2023-2025 extracts (EIA's own type-name strings).
_REGION_TYPE_NAMES: dict[str, str] = {
    "D": "Demand",
    "DF": "Day-ahead demand forecast",
    "NG": "Net generation",
    "TI": "Total interchange",
}


def _params(ba: str, start: str, end: str) -> dict:
    """Common EIA v2 query params for one BA and inclusive date range.

    ``start``/``end`` are UTC dates (``YYYY-MM-DD``) or UTC hours
    (``YYYY-MM-DDTHH``). An hour-precise ``end`` lets a pull close exactly on a
    local-calendar boundary (EIA periods are UTC hour-ending), e.g.
    ``2026-07-01T05`` to include the last local hours of June 30 in ERCOT.
    """
    return {
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": ba,
        "start": start if "T" in start else f"{start}T00",
        "end": end if "T" in end else f"{end}T23",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
    }


_FUELTYPE_COLUMNS = ["period", "iso", "fueltype", "type_name", "value_mwh"]
_REGION_COLUMNS = ["period", "iso", "type", "type_name", "value_mwh"]


def fetch_fueltype(ba: str, start: str, end: str, key: str) -> pd.DataFrame:
    """Tidy per-fuel net-generation rows in the ``<BA>_fueltype`` schema.

    Some BA/date-range combinations have no EIA-930 fuel-type reporting at all
    (e.g. NYIS has no fuel-type breakout before 2019) — that is a real
    reporting gap, not a fetch error, so an empty API response yields an
    empty (but correctly-schemed) frame rather than raising.
    """
    rows = _fetch(FUEL_URL, _params(ba, start, end), key)
    if not rows:
        return pd.DataFrame(columns=_FUELTYPE_COLUMNS).astype({"value_mwh": float})
    df = pd.DataFrame(rows)
    out = pd.DataFrame(
        {
            # ns (not the pandas-3 default us) to match the 2023-2025 siblings.
            "period": pd.to_datetime(df["period"], utc=True).astype(
                "datetime64[ns, UTC]"
            ),
            "iso": df["respondent"].astype("string").astype(object),
            "fueltype": df["fueltype"].astype("string").astype(object),
            "type_name": df["type-name"].astype("string").astype(object),
            "value_mwh": pd.to_numeric(df["value"], errors="coerce").astype(float),
        }
    )
    return out.sort_values(["period", "fueltype"], kind="stable").reset_index(drop=True)


def fetch_region(ba: str, start: str, end: str, key: str) -> pd.DataFrame:
    """Tidy demand-family (D/DF/NG/TI) rows in the ``<BA>_region`` schema.

    Same empty-reporting-gap handling as ``fetch_fueltype``.
    """
    rows = _fetch(REGION_URL, _params(ba, start, end), key)
    if not rows:
        return pd.DataFrame(columns=_REGION_COLUMNS).astype({"value_mwh": float})
    df = pd.DataFrame(rows)
    df = df[df["type"].isin(_REGION_TYPE_NAMES)].copy()
    out = pd.DataFrame(
        {
            # ns (not the pandas-3 default us) to match the 2023-2025 siblings.
            "period": pd.to_datetime(df["period"], utc=True).astype(
                "datetime64[ns, UTC]"
            ),
            "iso": df["respondent"].astype("string").astype(object),
            "type": df["type"].astype("string").astype(object),
            "type_name": df["type"].map(_REGION_TYPE_NAMES).astype(object),
            "value_mwh": pd.to_numeric(df["value"], errors="coerce").astype(float),
        }
    )
    return out.sort_values(["period", "type"], kind="stable").reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ba", required=True, help="EIA-930 BA code, e.g. ERCO")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD (inclusive)")
    ap.add_argument("--out-fueltype", type=Path, required=True)
    ap.add_argument("--out-region", type=Path, required=True)
    args = ap.parse_args()

    key = _api_key()
    for name, fn, out in (
        ("fueltype", fetch_fueltype, args.out_fueltype),
        ("region", fetch_region, args.out_region),
    ):
        frame = fn(args.ba, args.start, args.end, key)
        out.parent.mkdir(parents=True, exist_ok=True)
        frame.to_parquet(out, index=False)
        span = f"{frame['period'].min()}..{frame['period'].max()}"
        print(f"wrote {out} — {len(frame):,} {name} rows ({span})")


if __name__ == "__main__":
    main()
