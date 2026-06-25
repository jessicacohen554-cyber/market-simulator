#!/usr/bin/env python
"""Derive the CAISO CT_PEAKER temperature-driven reliability-commitment floor.

CAISO commits its simple-cycle gas peakers (CT_PEAKER) for **local Resource
Adequacy** during the summer evening net-load ramp: as the afternoon heat drives
the load-pocket cooling load and solar collapses at sunset, fast-start CTs in the
LA Basin / Big-Creek-Ventura / Bay-Area local capacity areas are committed for
local reliability regardless of whether they are in-the-money on system energy.
An energy-only LP never dispatches them (they sit at the top of the merit order),
so the backcast under-runs CT_PEAKER (~0.15 TWh vs ~3-5 TWh measured) and the
freed energy spills onto the cheaper combined-cycle fleet (CC_REGULAR over-runs).

This script derives the **physical, weather-grounded** floor that replaces that
missing commitment, mirroring the ERCOT gas-steam net-load drag derivation
(``docs/ercot-st-gas-netload-drag-2026-06.md``) but keyed to **temperature**,
because — unlike ERCOT's bimodal overnight steam — CAISO CT operation has a clean
**monotonic hot-limb** relationship with temperature (it is a summer-heat peaker
fleet, not a winter+summer reliability fleet):

  1. Fetch NOAA GHCN-Daily TMAX for the major CAISO load-center metros and
     load-weight them into a single CAISO daily max temperature (archived to
     ``data/raw/caiso-weather/`` so the floor regenerates from a forward weather
     year exactly as the load / wind / solar shapes do).
  2. Regress measured CAISO CT_PEAKER evening (15-22 local) capacity factor
     (EPA CAMPD simple-cycle combustion-turbine units, 2023-2025) on that daily
     TMAX. The relationship is a clipped line: zero below ~25 deg C, rising
     ~4.8%/deg C above it, capped near the hottest observed days. These
     coefficients become the ``ScenarioConfig`` defaults — a measured
     temperature->commitment rule, NOT a fit to a generation/TWh residual.

Run with no network (``--no-fetch``) to re-derive from the archived TMAX file.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

# NOAA GHCN-Daily stations for CAISO load-center metros, with a rough load weight
# (south/inland — the hot load pockets that drive local-RA CT commitment — carry
# more weight than the mild coast). The weights only set the *shape* of a single
# system temperature index; the floor magnitude comes from the regression below.
CAISO_TMAX_STATIONS: dict[str, float] = {
    "USW00023174": 0.20,  # Los Angeles Intl (LA Basin)
    "USW00023152": 0.15,  # Burbank (LA Basin inland)
    "USW00023188": 0.10,  # San Diego (SDG&E)
    "USW00093193": 0.15,  # Fresno (Central Valley)
    "USW00023232": 0.15,  # Sacramento (Central Valley / PG&E)
    "USW00023293": 0.15,  # San Jose (Bay Area inland)
    "USW00023234": 0.10,  # San Francisco (Bay Area coast)
}

# Local hours over which the local-RA CT commitment binds: the afternoon-evening
# net-load ramp / duck-curve neck. On hot days (TMAX >= 30 deg C) this window
# carries ~80% of measured CT_PEAKER energy; outside it the fleet dispatches
# purely on price. A documented operating window, mirroring the midday gas-floor
# window in transmission.CAISO_GAS_FLOOR_HOURS.
CT_FLOOR_HOURS: tuple[int, int] = (15, 22)

OUT_DIR: Path = RAW_DATA_DIR / "caiso-weather"
OUT_CSV: Path = OUT_DIR / "caiso_load_weighted_tmax_daily.csv"

_NOAA_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations={station}&startDate={start}&endDate={end}&dataTypes=TMAX&format=json"
)


def fetch_load_weighted_tmax(start: str, end: str) -> pd.DataFrame:
    """Fetch + load-weight NOAA GHCN TMAX into a daily CAISO max-temp series."""
    series = []
    weights = []
    for station, weight in CAISO_TMAX_STATIONS.items():
        url = _NOAA_URL.format(station=station, start=start, end=end)
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
            rows = json.load(resp)
        df = pd.DataFrame(rows)
        # GHCN TMAX is in tenths of deg C.
        tmax_c = pd.to_numeric(df["TMAX"], errors="coerce") / 10.0
        s = pd.Series(tmax_c.to_numpy(), index=pd.to_datetime(df["DATE"]), name=station)
        series.append(s)
        weights.append(weight)
    wide = pd.concat(series, axis=1)
    w = np.asarray(weights, dtype=float)
    w = w / w.sum()
    daily = (wide * w).sum(axis=1, min_count=1)
    out = daily.rename("tmax_c").to_frame()
    out.index.name = "date"
    return out.dropna()


def derive_curve(tmax: pd.DataFrame, years: tuple[int, ...]) -> dict[str, float]:
    """Regress measured CT_PEAKER evening CF on daily TMAX -> floor coefficients."""
    from market_sim.config.paths import RAW_DIR

    # Measured CAISO CT_PEAKER fleet: EPA CAMPD simple-cycle combustion turbines.
    frames = []
    for year in years:
        path = RAW_DIR / "campd-unit-level" / f"CA_{year}.parquet"
        d = pd.read_parquet(path)
        d = d[d["unitType"].astype(str).str.contains("Combustion turbine", na=False)]
        frames.append(d)
    ca = pd.concat(frames, ignore_index=True)
    ca["dt"] = pd.to_datetime(ca["date"]) + pd.to_timedelta(
        ca["hour"].astype(int), unit="h"
    )
    ct = ca.groupby("dt")["grossLoad"].sum()
    ct = ct[~ct.index.duplicated()]
    cap = (
        ca.groupby(["facilityId", "unitId"])["grossLoad"].max().sum()
    )  # CEMS fleet nameplate proxy

    df = ct.rename("ct_mw").to_frame()
    df["date"] = df.index.normalize()
    df["hod"] = df.index.hour
    df = df.join(tmax, on="date").dropna()
    start, end = CT_FLOOR_HOURS
    ev = df[(df["hod"] >= start) & (df["hod"] <= end)].copy()
    ev["frac"] = ev["ct_mw"] / cap

    hot = ev[ev["tmax_c"] >= 26.0]
    slope, intercept = np.polyfit(hot["tmax_c"], hot["frac"], 1)
    t0 = -intercept / slope
    cap_frac = float(ev["frac"].quantile(0.97))
    return {
        "slope_per_c": round(float(slope), 3),
        "t0_c": round(float(t0)),
        "cap": round(cap_frac, 2),
        "cems_cap_mw": round(float(cap)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Skip the NOAA download; re-derive from the archived TMAX CSV.",
    )
    args = ap.parse_args()
    years = tuple(args.years)

    if args.no_fetch:
        tmax = pd.read_csv(OUT_CSV, parse_dates=["date"]).set_index("date")
    else:
        tmax = fetch_load_weighted_tmax(f"{years[0]}-01-01", f"{years[-1]}-12-31")
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        tmax.to_csv(OUT_CSV)
        print(f"wrote {OUT_CSV} ({len(tmax)} days)")

    coeffs = derive_curve(tmax, years)
    print("Derived CT reliability-floor curve (frac = clip(slope*(TMAX-T0),0,cap)):")
    print(json.dumps(coeffs, indent=2))


if __name__ == "__main__":
    main()
