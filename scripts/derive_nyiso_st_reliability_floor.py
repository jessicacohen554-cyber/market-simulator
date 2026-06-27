"""Derive the NYISO ST_GAS (steam-gas) local-reliability floor coefficients.

Companion to ``scripts/derive_nyiso_ct_reliability_floor.py``. NYISO's downstate
gas-steam fleet runs a persistent in-city / cable-islanded reliability baseline
plus a strong summer hot-limb that an energy-only LP zeroes out (it imports
cheaper upstate/NYC combined cycle instead), so the backcast under-runs ST_GAS.
Unlike the CT floor (one pooled NYC-metro TMAX series), the steam fleet sits in
three distinct weather regimes, so each zone is keyed to its OWN load-center
daily max temperature:

  * **Long_Island** (Islip, USW00004781) — strong hot-limb, cable-islanded.
  * **NYC**         (Central Park, USW00094728) — persistent in-city must-run
    (Ravenswood / Arthur Kill / Astoria) PLUS a hot-limb on top.
  * **Capital_Hudson** (Albany, USW00014735) — weak hot-limb, small class.
  * **Upstate_West**  (Buffalo, USW00014733) — flat vs temperature (baseload
    cogen-like); printed for completeness, not floored.

Steps:
  1. Fetch NOAA GHCN-Daily TMAX for each zone's load-center station and archive
     a per-zone daily series to
     ``data/raw/nyiso-weather/nyiso_zone_tmax_daily.csv`` (columns date, zone,
     tmax_c) so the floor regenerates for a forward year from a pinned weather
     year. The NYC column is the Central Park station already used by the CT
     floor, re-archived here in the per-zone file for a self-contained ST input.
  2. Build the measured per-zone ST_GAS fleet evening (HB14-21) capacity factor
     per day from CAMPD unit-level grossLoad (the bin_assignments_NYISO ST_GAS
     plants in each zone).
  3. Regress evening CF on the zone TMAX to recover the hot-limb (slope above
     T0=25 degC), the hottest-day ceiling (cap = p97), and the cool-day evening
     baseline (base_ev = cool-day evening p25) per zone — a physical
     temperature->commitment rule, NOT a fit to a TWh residual. Print Pearson r
     and hot/mild CF so a weak class (Capital) can be judged on the data, not
     forced.
  4. Also recover the PERSISTENT 24-hour baseline (base_24h = cool-day ALL-hours
     p25) per zone: the in-city / cable-islanded steam fleet runs an in-merit
     reliability minimum overnight and midday too, not only on the evening ramp
     (measured cool-day CF is ~80% of the evening level overnight). This is the
     Task-C "must-run when available" baseline — floored over ALL hours, with the
     evening hot-limb layered on top via maximum.

Run with no network (``--no-fetch``) to re-derive from the archived TMAX file.
The printed per-zone coefficients become the ``transmission.NYISO_ST_FLOOR_COEFFS``
defaults consumed by ``transmission.inject_nyiso_st_reliability_floor`` (enabled
by ``ScenarioConfig.nyiso_st_reliability_floor`` / ``--nyiso-st-reliability-floor``).
"""

from __future__ import annotations

import argparse
import json
import urllib.request

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

# NOAA GHCN-Daily load-center station per NYISO ST_GAS zone. Each downstate
# steam pocket sits in its own weather regime, so (unlike the pooled NYC-metro
# CT floor) the steam floor keys each zone to its local daily max temperature.
ZONE_TMAX_STATION: dict[str, str] = {
    "Long_Island": "USW00004781",  # Islip
    "NYC": "USW00094728",  # Central Park (same station as the CT floor)
    "Capital_Hudson": "USW00014735",  # Albany
    "Upstate_West": "USW00014733",  # Buffalo
}

_NOAA_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations={station}&startDate={start}&endDate={end}&dataTypes=TMAX&format=json"
)

EVENING_HOURS = range(14, 22)  # HB14-21 inclusive (matches the CT floor window)
T0_C = 25.0


def fetch_station_tmax(station: str, start: str, end: str) -> pd.Series:
    """Fetch a single NOAA GHCN station's daily TMAX (deg C) over a date range."""
    url = _NOAA_URL.format(station=station, start=start, end=end)
    with urllib.request.urlopen(url, timeout=90) as resp:  # noqa: S310
        data = json.loads(resp.read())
    df = pd.DataFrame(data)
    if df.empty:
        return pd.Series(dtype=float)
    df["TMAX"] = pd.to_numeric(df["TMAX"]) / 10.0  # GHCN tenths degC -> degC
    return df.set_index("DATE")["TMAX"]


def zone_steam_plant_codes(zone: str) -> tuple[set[int], float]:
    """Return a zone's ST_GAS plant codes and their nameplate (MW)."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    z = b[(b["Plant_Group"] == "ST_GAS") & (b["Zone"] == zone)]
    return set(z["Plant_Code"].astype(int)), float(z["Nameplate_MW"].sum())


def main() -> None:
    """Derive per-zone coefficients, archive the TMAX series, print the fits."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Re-derive from the archived per-zone TMAX file (no NOAA network).",
    )
    args = ap.parse_args()

    archive_path = RAW_DIR / "nyiso-weather" / "nyiso_zone_tmax_daily.csv"

    # --- TMAX per zone per year --------------------------------------------
    # zone -> {year -> Series(date -> tmax_c)}
    tmax: dict[str, dict[int, pd.Series]] = {z: {} for z in ZONE_TMAX_STATION}
    if args.no_fetch:
        arch = pd.read_csv(archive_path, parse_dates=["date"])
        for zone in ZONE_TMAX_STATION:
            za = arch[arch["zone"] == zone]
            for yr in args.years:
                s = za[za["date"].dt.year == yr].set_index("date")["tmax_c"]
                if not s.empty:
                    tmax[zone][yr] = s
    else:
        archive_rows = []
        for zone, station in ZONE_TMAX_STATION.items():
            for yr in args.years:
                s = fetch_station_tmax(station, f"{yr}-01-01", f"{yr}-12-31")
                if s.empty:
                    continue
                s.index = pd.to_datetime(s.index)
                tmax[zone][yr] = s
                row = s.rename("tmax_c").reset_index()
                row.columns = ["date", "tmax_c"]
                row["zone"] = zone
                archive_rows.append(row)
        arch = pd.concat(archive_rows)[["date", "zone", "tmax_c"]]
        arch["date"] = pd.to_datetime(arch["date"]).dt.strftime("%Y-%m-%d")
        arch = arch.sort_values(["zone", "date"])
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        arch.to_csv(archive_path, index=False)
        print(f"archived {len(arch)} zone-days -> {archive_path}")

    # --- per-zone evening CF vs zone TMAX regression -----------------------
    for zone in ZONE_TMAX_STATION:
        codes, nameplate = zone_steam_plant_codes(zone)
        if not codes or nameplate <= 0.0:
            continue
        pooled, pooled24 = [], []
        for yr, tser in tmax[zone].items():
            path = RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet"
            if not path.exists():
                continue
            c = pd.read_parquet(path)
            c = c[c["facilityId"].astype(int).isin(codes)].copy()
            c["date"] = pd.to_datetime(c["date"])
            ev = c[c["hour"].isin(EVENING_HOURS)]
            daily = ev.groupby("date")["grossLoad"].sum() / (
                nameplate * len(EVENING_HOURS)
            )
            df = pd.DataFrame({"cf": daily})
            df["tmax"] = df.index.map(tser)
            pooled.append(df.dropna())
            # 24-hour daily fleet CF (all hours) for the persistent baseline.
            daily24 = c.groupby("date")["grossLoad"].sum() / (nameplate * 24)
            d24 = pd.DataFrame({"cf": daily24})
            d24["tmax"] = d24.index.map(tser)
            pooled24.append(d24.dropna())
        if not pooled:
            continue
        P = pd.concat(pooled)
        P24 = pd.concat(pooled24)
        cool, hot = P[P["tmax"] < T0_C], P[P["tmax"] >= T0_C]
        cool24 = P24[P24["tmax"] < T0_C]
        corr = float(P["cf"].corr(P["tmax"]))
        cap = float(P["cf"].quantile(0.97))
        base = float(cool["cf"].quantile(0.25))
        base24 = float(cool24["cf"].quantile(0.25))
        slope = (
            float(np.polyfit(hot["tmax"] - T0_C, hot["cf"], 1)[0])
            if len(hot) >= 2
            else 0.0
        )
        print(f"\n=== {zone} ST_GAS CF, pooled {args.years} ===")
        print(f"  nameplate                 = {nameplate:.0f} MW, {len(codes)} plants")
        print(f"  corr(CF, TMAX) [evening]  = {corr:+.3f}")
        print(f"  hot-day (>=25C) median CF = {hot['cf'].median():.3f}")
        print(f"  mild-day (<25C) median CF = {cool['cf'].median():.3f}")
        print(f"  nyiso_st_floor_t0_c       = {T0_C:.1f}")
        print(f"  nyiso_st_floor_slope_per_c= {slope:.4f}   (hot-limb, TMAX>=T0)")
        print(f"  nyiso_st_floor_cap        = {cap:.3f}    (p97 evening CF)")
        print(f"  nyiso_st_floor_base_ev    = {base:.3f}    (cool-day evening p25)")
        print(f"  nyiso_st_floor_base_24h   = {base24:.3f}    (cool-day ALL-hours p25)")


if __name__ == "__main__":
    main()
