#!/usr/bin/env python3
"""Build NEISO's measured neighbor-seam hourly price input from the NYISO
public DAM zonal LBMP archives.

NEISO's import tranches (``IMPORT_TRANCHES["NEISO"]``) were fitted seam
price/volume ladders (model-legitimacy audit C-6). The measured re-grounding
prices each seam on a *public, measured* neighbor-market price series:

* ``NYISO_NPX`` — NYISO's New England proxy bus ("NPX"): the NYISO-side
  Day-Ahead LBMP at the NY–NE interface, i.e. the measured source price New
  England pays for imports scheduled from New York (and is paid for exports
  into New York).
* ``NYISO_HQ`` — NYISO's Hydro-Québec proxy bus ("H Q"): the measured
  Day-Ahead price Hydro-Québec can earn in its alternative export market.
  HQ has no public hub of its own (it is not an organized market), so its
  New England export opportunity cost is proxied by what the same energy
  clears at on the NY border — the nearest public measured price for HQ
  energy, used by ``derive_neiso_import_tranches.py`` to ground the
  HQ Phase II / Highgate tranche costs.

Source: ``data/raw/lmp-data/NYISO/YYYYMM01damlbmp_zone_csv.zip`` — the NYISO
MIS public monthly archives (http://mis.nyiso.com/public/csv/damlbmp/) of the
daily Day-Ahead zonal LBMP CSVs, columns ``Time Stamp`` (local hour-beginning,
America/New_York), ``Name``, ``PTID``, ``LBMP ($/MWHr)``, marginal loss and
congestion components. The proxy buses appear as zones "H Q" and "NPX".

Output: ``data/raw/_validation-source/nyiso_proxy_lmp_hourly_NEISO.parquet``
(border-lmp schema): columns year (int), hour (int, 0..8759 on the model's
fixed non-leap Eastern-time calendar), hub (str, ``NYISO_HQ``/``NYISO_NPX``),
price (float, $/MWh DA total LBMP). Feb 29 dropped; DST-ambiguous hours
dropped then interpolated (limit=2), matching the CAISO/MISO border-lmp
builders.

Usage:
    python scripts/data/build_nyiso_proxy_lmp_neiso.py [--years 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
NYISO_DIR = REPO / "data" / "raw" / "lmp-data" / "NYISO"
OUT_PARQUET = (
    REPO
    / "data"
    / "raw"
    / "_validation-source"
    / "nyiso_proxy_lmp_hourly_NEISO.parquet"
)

# NYISO proxy-bus zone name -> output hub id.
PROXY_HUBS: dict[str, str] = {"H Q": "NYISO_HQ", "NPX": "NYISO_NPX"}

# NYISO and the NEISO model calendar share the Eastern clock.
TZ = "America/New_York"
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760


def _hour_index(ts: pd.Series) -> np.ndarray:
    """Local timestamps -> fixed non-leap hour-of-year (Feb 29 -> -1)."""
    base = np.asarray([_MONTH_START_HOUR[m - 1] for m in ts.dt.month])
    idx = base + (ts.dt.day.to_numpy() - 1) * 24 + ts.dt.hour.to_numpy()
    return np.where((ts.dt.month == 2) & (ts.dt.day == 29), -1, idx)


def _read_month(path: Path) -> pd.DataFrame:
    """Read one monthly zip of daily DAM zonal CSVs, proxy-bus rows only."""
    frames = []
    with zipfile.ZipFile(path) as zf:
        for name in sorted(zf.namelist()):
            if not name.endswith(".csv"):
                continue
            df = pd.read_csv(io.BytesIO(zf.read(name)))
            df = df[df["Name"].isin(PROXY_HUBS)]
            if not df.empty:
                frames.append(df[["Time Stamp", "Name", "LBMP ($/MWHr)"]])
    if not frames:
        return pd.DataFrame(columns=["Time Stamp", "Name", "LBMP ($/MWHr)"])
    return pd.concat(frames, ignore_index=True)


def build_year(year: int) -> pd.DataFrame | None:
    """Return the dense (8760 x hubs, 4-col) frame for ``year``."""
    months = sorted(NYISO_DIR.glob(f"{year}??01damlbmp_zone_csv.zip"))
    if len(months) < 12:
        print(
            f"  {year}: only {len(months)}/12 monthly archives present — skipped",
            file=sys.stderr,
        )
        return None

    df = pd.concat([_read_month(p) for p in months], ignore_index=True)
    # Local hour-beginning timestamps; the November fall-back hour appears as
    # a duplicated wall-clock hour the zone CSV cannot disambiguate — drop
    # both (ambiguous="NaT") and interpolate, matching the PJM/CAISO builders.
    ts = pd.to_datetime(df["Time Stamp"], format="%m/%d/%Y %H:%M")
    df["dt_local"] = ts.dt.tz_localize(TZ, ambiguous="NaT", nonexistent="NaT")
    df = df.dropna(subset=["dt_local"])
    df["hour"] = _hour_index(df["dt_local"])
    df = df[(df["hour"] >= 0) & (df["hour"] < _HOURS_PER_YEAR)]

    records = []
    for zone_name, hub in PROXY_HUBS.items():
        g = df[df["Name"] == zone_name]
        hourly = (
            g.groupby("hour")["LBMP ($/MWHr)"]
            .mean()
            .reindex(np.arange(_HOURS_PER_YEAR))
        )
        price = hourly.interpolate(limit=2).to_numpy(dtype=float)
        n_finite = int(np.sum(np.isfinite(price)))
        print(
            f"  {year} {hub}: {n_finite}/{_HOURS_PER_YEAR} hours, "
            f"DA mean ${np.nanmean(price):.2f}/MWh"
        )
        records.append(
            pd.DataFrame(
                {
                    "year": year,
                    "hour": np.arange(_HOURS_PER_YEAR),
                    "hub": hub,
                    "price": np.round(price, 4),
                }
            )
        )
    return pd.concat(records, ignore_index=True)


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
    print(f"wrote {OUT_PARQUET} — {len(out):,} rows")


if __name__ == "__main__":
    main()
