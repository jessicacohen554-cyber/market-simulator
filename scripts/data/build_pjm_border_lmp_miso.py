#!/usr/bin/env python3
"""Build MISO's measured PJM border-hub hourly LMP input from the committed
PJM Data Miner hub-level LMP CSVs.

The model's ``miso_pjm_lmp_import_pricing`` mechanism (the MISO analog of
CAISO's ``caiso_import_hub_prices``) prices each PJM import tranche on the
reference-price seam at the **measured hourly PJM Day-Ahead LMP** at the
MISO-facing western border hubs, replacing the synthetic gas × heat-rate ×
load-shape ladder that is too flat / too high to reproduce the off-peak price
dips that drive real PJM-to-MISO import.

Source: ``data/raw/lmp-data/PJM_{year}_rt_da_monthly_lmps.csv`` — PJM Data
Miner 2 ``da_hrl_lmps`` (and RT) for all PJM hubs, hourly, columns
``datetime_beginning_ept`` (EPT = Eastern Prevailing Time),
``pnode_name``, ``total_lmp_da``, ``total_lmp_rt``.

Output: ``data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet``
  columns: year (int), hour (int, 0..8759 on MISO's fixed non-leap Central-
  time calendar), hub (str, ``PJM_WEST``), price (float, $/MWh DA total LMP).

The hub ``PJM_WEST`` is the equal-weight mean of the three MISO-facing PJM
generator hubs (CHICAGO GEN HUB, AEP GEN HUB, ATSI GEN HUB) — the same
border-zone decomposition the ``MISO_PJM_BORDER_HR_BY_YEAR`` derivation uses
(constants.py). These are the generator hubs co-located with the transmission
border zones declared in ``INTERFACE_NEIGHBORS["PJM"]`` as
``border_zones=("PJM_ComEd", "PJM_AEP_Ohio", "PJM_ATSI")``.

Usage:
    python scripts/data/build_pjm_border_lmp_miso.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.utils.hour_calendar import hour_index  # noqa: E402

LMP_DIR = REPO / "data" / "raw" / "lmp-data"
OUT_PARQUET = (
    REPO / "data" / "raw" / "_validation-source" / "pjm_border_lmp_hourly_MISO.parquet"
)

BORDER_HUBS = ["CHICAGO GEN HUB", "AEP GEN HUB", "ATSI GEN HUB"]
HUB_NAME = "PJM_WEST"

MISO_TZ = "America/Chicago"
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760


# Local timestamps -> fixed non-leap hour-of-year (Feb 29 -> -1); shared helper.
_hour_index = hour_index


def build_year(year: int) -> pd.DataFrame | None:
    """Read PJM hub LMP CSV for ``year`` and return dense (8760, 4) DataFrame."""
    path = LMP_DIR / f"PJM_{year}_rt_da_monthly_lmps.csv"
    if not path.exists():
        print(f"  {path.name}: not found — skipped", file=sys.stderr)
        return None

    df = pd.read_csv(path)
    # Filter to the three MISO-facing border hubs.
    df = df[df["pnode_name"].isin(BORDER_HUBS)].copy()
    if df.empty:
        print(f"  {year}: no border-hub rows found", file=sys.stderr)
        return None

    # Parse EPT timestamps -> Central time -> hour-of-year.
    # EPT = Eastern Prevailing Time (EST/EDT); convert to MISO's Central clock.
    df["dt_ept"] = pd.to_datetime(df["datetime_beginning_ept"])
    df["dt_ept"] = df["dt_ept"].dt.tz_localize(
        "America/New_York", ambiguous="NaT", nonexistent="NaT"
    )
    df["dt_central"] = df["dt_ept"].dt.tz_convert(MISO_TZ)

    # Drop any rows where tz conversion failed (DST ambiguity).
    df = df.dropna(subset=["dt_central"])

    # Map to hour-of-year on the fixed non-leap calendar.
    hi = _hour_index(df["dt_central"])
    df["hour"] = hi
    df = df[(df["hour"] >= 0) & (df["hour"] < _HOURS_PER_YEAR)].copy()

    # Average the three border hubs' DA total LMP per hour.
    hourly = (
        df.groupby("hour")["total_lmp_da"].mean().reindex(np.arange(_HOURS_PER_YEAR))
    )

    # Interpolate isolated DST gaps (limit=2, same as CAISO pattern).
    price = hourly.interpolate(limit=2).to_numpy(dtype=float)

    n_finite = np.sum(np.isfinite(price))
    n_nan = _HOURS_PER_YEAR - n_finite
    print(
        f"  {year}: {n_finite}/{_HOURS_PER_YEAR} hours, "
        f"DA mean ${np.nanmean(price):.2f}/MWh"
        + (f" ({n_nan} NaN hours)" if n_nan > 0 else "")
    )

    records = []
    for h in range(_HOURS_PER_YEAR):
        val = float(price[h])
        records.append(
            {
                "year": year,
                "hour": h,
                "hub": HUB_NAME,
                "price": round(val, 4) if np.isfinite(val) else np.nan,
            }
        )
    return pd.DataFrame.from_records(records)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()

    frames = []
    for year in args.years:
        print(f"=== {year} ===", flush=True)
        frame = build_year(year)
        if frame is not None:
            frames.append(frame)

    if not frames:
        print("no data built — nothing written.", file=sys.stderr)
        sys.exit(1)

    out = pd.concat(frames, ignore_index=True)
    out = out.sort_values(["year", "hub", "hour"]).reset_index(drop=True)
    OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    out.to_parquet(OUT_PARQUET, index=False)
    print(
        f"\nwrote {OUT_PARQUET.relative_to(REPO)} ({len(out)} rows, "
        f"years {sorted(out['year'].unique())})"
    )


if __name__ == "__main__":
    main()
