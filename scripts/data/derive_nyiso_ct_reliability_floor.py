"""Derive the NYISO downstate CT_PEAKER local-reliability floor coefficients.

Mirrors ``scripts/data/derive_caiso_ct_reliability_floor.py`` for NYISO's
cable-constrained downstate load pockets (NYC zone J, Long Island zone K, Lower
Hudson). The downstate simple-cycle gas-peaker fleet is held online through the
hot-day afternoon-evening AC ramp for local capacity-area reliability when the
UPNY-SENY / Long-Island-cable import limits bind; an energy-only LP imports
cheap upstate/NYC combined cycle instead and under-runs CT_PEAKER.

Steps:
  1. Fetch NOAA GHCN-Daily TMAX for the NYC-metro stations (Central Park,
     LaGuardia, JFK) and average them into a daily NYC max-temp series.
  2. Build the measured downstate CT_PEAKER fleet evening (HB14-21) capacity
     factor per day from CAMPD unit-level grossLoad (the bin_assignments_NYISO
     CT_PEAKER plants in the downstate zones).
  3. Regress evening CF on TMAX to recover the hot-limb (slope above T0=25 degC),
     the hottest-day ceiling (cap = p97), and the cool-day baseline
     (base = cool-day evening p25) — a physical temperature->commitment rule, NOT
     a fit to a TWh residual.
  4. Archive the daily TMAX series to
     ``data/raw/nyiso-weather/nyiso_downstate_tmax_daily.csv`` so the floor
     regenerates for a forward year from a pinned weather year.

Run with no network (``--no-fetch``) to re-derive from the archived TMAX file.
The coefficients become the ScenarioConfig defaults
(``nyiso_ct_floor_slope_per_c`` / ``_t0_c`` / ``_cap`` / ``_base``) consumed by
``transmission.inject_nyiso_ct_reliability_floor``.
"""

from __future__ import annotations

import argparse
import json
import urllib.request

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

# NOAA GHCN-Daily stations for the NYC metro (simple mean — the downstate load
# pockets share one weather regime).
NYC_TMAX_STATIONS = (
    "USW00094728",  # Central Park
    "USW00014732",  # LaGuardia
    "USW00094789",  # JFK
)

_NOAA_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations={station}&startDate={start}&endDate={end}&dataTypes=TMAX&format=json"
)

# Downstate load pockets the floor applies to (matches transmission.
# NYISO_CT_FLOOR_ZONES); the afternoon-evening floor window (matches
# transmission.NYISO_CT_FLOOR_HOURS); the hot-limb zero-crossing.
DOWNSTATE_ZONES = ("NYC", "Long_Island", "Lower_Hudson")
EVENING_HOURS = range(14, 22)  # HB14-21 inclusive
T0_C = 25.0


def fetch_nyc_tmax(start: str, end: str) -> pd.Series:
    """Fetch + average NOAA GHCN TMAX into a daily NYC-metro max-temp series."""
    frames = []
    for station in NYC_TMAX_STATIONS:
        url = _NOAA_URL.format(station=station, start=start, end=end)
        with urllib.request.urlopen(url, timeout=90) as resp:  # noqa: S310
            data = json.loads(resp.read())
        df = pd.DataFrame(data)
        if df.empty:
            continue
        df["TMAX"] = pd.to_numeric(df["TMAX"]) / 10.0  # GHCN tenths degC -> degC
        frames.append(df[["DATE", "TMAX"]].rename(columns={"DATE": "date"}))
    return pd.concat(frames).groupby("date")["TMAX"].mean()


def downstate_peaker_plant_codes() -> tuple[set[int], float]:
    """Return the downstate CT_PEAKER plant codes and their nameplate (MW)."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    ds = b[(b["Plant_Group"] == "CT_PEAKER") & (b["Zone"].isin(DOWNSTATE_ZONES))]
    return set(ds["Plant_Code"].astype(int)), float(ds["Nameplate_MW"].sum())


def main() -> None:
    """Derive coefficients, archive the TMAX series, print the fit."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Re-derive from the archived TMAX file (no NOAA network call).",
    )
    args = ap.parse_args()

    codes, nameplate = downstate_peaker_plant_codes()
    print(f"downstate CT_PEAKER: {len(codes)} plants, {nameplate:.0f} MW nameplate")

    archive_path = RAW_DIR / "nyiso-weather" / "nyiso_downstate_tmax_daily.csv"
    tmax_by_year: dict[int, pd.Series] = {}
    if args.no_fetch:
        arch = pd.read_csv(archive_path, parse_dates=["date"])
        for yr in args.years:
            s = arch[arch["date"].dt.year == yr].set_index("date")["tmax_c"]
            if not s.empty:
                tmax_by_year[yr] = s
    else:
        archive_rows = []
        for yr in args.years:
            s = fetch_nyc_tmax(f"{yr}-01-01", f"{yr}-12-31")
            s.index = pd.to_datetime(s.index)
            tmax_by_year[yr] = s
            archive_rows.append(
                s.rename("tmax_c").reset_index().rename(columns={"index": "date"})
            )
        arch = pd.concat(archive_rows)[["date", "tmax_c"]].sort_values("date")
        arch["date"] = pd.to_datetime(arch["date"]).dt.strftime("%Y-%m-%d")
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        arch.to_csv(archive_path, index=False)
        print(f"archived {len(arch)} days -> {archive_path}")

    # Build the pooled downstate evening (HB14-21) daily CF vs TMAX.
    pooled = []
    for yr, tmax in tmax_by_year.items():
        path = RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet"
        if not path.exists():
            continue
        c = pd.read_parquet(path)
        c = c[c["facilityId"].astype(int).isin(codes)].copy()
        c["date"] = pd.to_datetime(c["date"])
        ev = c[c["hour"].isin(EVENING_HOURS)]
        daily = ev.groupby("date")["grossLoad"].sum() / (nameplate * len(EVENING_HOURS))
        df = pd.DataFrame({"cf": daily})
        df["tmax"] = df.index.map(tmax)
        pooled.append(df.dropna())

    P = pd.concat(pooled)
    cool, hot = P[P["tmax"] < T0_C], P[P["tmax"] >= T0_C]
    slope, intercept = np.polyfit(hot["tmax"] - T0_C, hot["cf"], 1)
    cap = float(P["cf"].quantile(0.97))
    base = float(cool["cf"].quantile(0.25))
    print(
        f"\n=== NYISO downstate CT_PEAKER evening (HB14-21) CF, pooled {args.years} ==="
    )
    print(f"  cool-day (TMAX<{T0_C:.0f}) median CF = {cool['cf'].median():.3f}")
    print(f"  nyiso_ct_floor_t0_c       = {T0_C:.1f}")
    print(f"  nyiso_ct_floor_slope_per_c= {slope:.4f}   (hot-limb, TMAX>=T0)")
    print(f"  nyiso_ct_floor_cap        = {cap:.3f}    (p97 evening CF)")
    print(f"  nyiso_ct_floor_base       = {base:.3f}    (cool-day evening p25)")


if __name__ == "__main__":
    main()
