"""Fold raw NYISO OASIS ``pal`` actual-load zips into hourly per-year CSVs.

Companion to the NYISO zonal-load loader
(:func:`market_sim.data.eia_loader.nyiso_zonal_load_shares`, upload U3). The
raw downloads are monthly zips of *daily* 5-minute integrated-load CSVs
(``data/raw/zone-specific-demand/NYISO/raw/<YYYYMM01>pal_csv.zip``),
each row ``Time Stamp, Time Zone, Name, PTID, Load`` for the eleven NYISO
settlement zones (WEST, GENESE, CENTRL, NORTH, MHK VL, CAPITL, HUD VL,
MILLWD, DUNWOD, N.Y.C., LONGIL). That is ~1M rows/zone-year at 5-minute
resolution — far too bulky to keep, and the loader only needs hour-by-hour
*shares*, so this aggregates each zone's 5-minute readings to the
hour-beginning mean (the standard hourly-integrated load) and writes one
compact CSV per year:

* ``data/raw/zone-specific-demand/NYISO/NYISO_load_actuals_{year}.csv``
  -- columns ``Time Stamp`` (Eastern wall-clock, hour-beginning), ``Name``
  (the NYISO OASIS zone name), ``Load`` (MW). This is exactly the format
  ``nyiso_zonal_load_shares`` detects.

Timestamps are kept as naive Eastern wall-clock (matching the raw); the
loader re-localizes to America/New_York and handles the DST fall-back hour
and Feb 29. Aggregation is by naive wall-clock hour, so the fall-back hour's
two passes merge into one row (one hour/year, back-filled downstream).

Run: ``python scripts/data/process_nyiso_zonal_load.py [--years 2023 2024 2025]``
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import ZONE_DEMAND_DIR  # noqa: E402

# NYISO zonal-load downloads under the single W1 data root
# (paths.ZONE_DEMAND_DIR = data/raw/zone-specific-demand); the pre-W1
# ``inputs/raw-data`` path was removed by the relocation.
NYISO_DIR = ZONE_DEMAND_DIR / "NYISO"
RAW_DIR = NYISO_DIR / "raw"

# The eleven NYISO settlement-zone names as they appear in the pal CSVs.
NYISO_ZONES = (
    "WEST",
    "GENESE",
    "CENTRL",
    "NORTH",
    "MHK VL",
    "CAPITL",
    "HUD VL",
    "MILLWD",
    "DUNWOD",
    "N.Y.C.",
    "LONGIL",
)


def _read_zip(path: Path) -> pd.DataFrame:
    """Read every daily pal CSV inside one monthly zip into one frame."""
    frames = []
    with zipfile.ZipFile(path) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".csv"):
                continue
            with zf.open(name) as fh:
                frames.append(
                    pd.read_csv(
                        io.BytesIO(fh.read()),
                        usecols=["Time Stamp", "Name", "Load"],
                    )
                )
    if not frames:
        return pd.DataFrame(columns=["Time Stamp", "Name", "Load"])
    return pd.concat(frames, ignore_index=True)


def process_year(year: int) -> Path | None:
    """Aggregate one year's monthly zips to the hourly per-year actuals CSV."""
    zips = sorted(RAW_DIR.glob(f"{year}*pal_csv.zip"))
    if not zips:
        print(f"  {year}: no raw pal zips under {RAW_DIR} — skipping")
        return None

    parts = [_read_zip(z) for z in zips]
    df = pd.concat(parts, ignore_index=True)
    df["Name"] = df["Name"].astype(str).str.strip()
    df = df[df["Name"].isin(NYISO_ZONES)]
    ts = pd.to_datetime(df["Time Stamp"], errors="coerce")
    df = df[ts.notna()].copy()
    ts = ts[ts.notna()]
    # Hour-beginning, naive Eastern wall-clock: floor the 5-minute reading.
    df["Time Stamp"] = ts.dt.floor("h")
    df["Load"] = pd.to_numeric(df["Load"], errors="coerce")
    df = df.dropna(subset=["Load"])

    hourly = (
        df.groupby(["Time Stamp", "Name"], observed=True)["Load"]
        .mean()
        .reset_index()
        .sort_values(["Time Stamp", "Name"])
    )
    out_path = NYISO_DIR / f"NYISO_load_actuals_{year}.csv"
    hourly.to_csv(out_path, index=False)

    n_zone = hourly["Name"].nunique()
    n_hours = hourly["Time Stamp"].nunique()
    sys_mean = hourly.groupby("Time Stamp")["Load"].sum().mean()
    print(
        f"  {year}: {len(zips)} zips -> {len(hourly):,} rows "
        f"({n_zone} zones x {n_hours:,} hours), system mean "
        f"{sys_mean:,.0f} MW -> {out_path.name}"
    )
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    print(f"processing NYISO pal zonal load from {RAW_DIR}")
    for year in args.years:
        process_year(year)


if __name__ == "__main__":
    main()
