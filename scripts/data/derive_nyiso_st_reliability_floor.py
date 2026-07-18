"""Derive the NYISO ST_GAS (steam-gas) local-reliability floor coefficients.

Companion to ``scripts/data/derive_nyiso_ct_reliability_floor.py``. NYISO's downstate
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


# Plants excluded from the steam reliability floor / its regression — none;
# mirrors transmission.NYISO_ST_FLOOR_EXCLUDE_PLANTS. Ravenswood (2500)'s
# over-availability (CC-tagged outages) is fixed at the source
# (data.outages._FLEET_GROUP_OVERRIDE), so it is included like the other steam.
EXCLUDE_PLANTS: frozenset[int] = frozenset()


def zone_steam_plant_codes(zone: str) -> tuple[dict[int, float], float]:
    """Return a zone's ST_GAS ``{plant_code: bin nameplate MW}`` and the total."""
    b = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NYISO.csv")
    z = b[(b["Plant_Group"] == "ST_GAS") & (b["Zone"] == zone)]
    z = z[~z["Plant_Code"].astype(int).isin(EXCLUDE_PLANTS)]
    by_plant = dict(zip(z["Plant_Code"].astype(int), z["Nameplate_MW"].astype(float)))
    return by_plant, float(z["Nameplate_MW"].sum())


def zone_available_capacity(
    plant_npl: dict[int, float], index: pd.DatetimeIndex
) -> pd.Series:
    """Hourly AVAILABLE capacity (MW) for a zone's ST_GAS fleet.

    ``nameplate`` minus the per-plant ``unit_pct_of_plant`` share of any unit on a
    detected CAMPD outage (``campd-unit-outages-NYISO.csv``, the SAME extract and
    the SAME ``unit_capacity_mw / plant_capacity_mw`` share basis the model derates
    bin availability with — :func:`market_sim.data.outages.unit_outage_derate_
    factors`), so the CF denominator excludes outage downtime. Using the NORMALISED
    pct-of-plant (which sums to 100% per plant) rather than the raw
    ``unit_capacity_mw`` is essential: CAMPD splits each steam unit's reheat /
    superheat sections into separate rows (Astoria 31RH+32SH, 51RH+52SH) that each
    carry the FULL section nameplate, so the raw caps sum to ~2x the plant
    nameplate; ``plant_capacity_mw`` is that same inflated sum, so the share
    ``unit_capacity_mw / plant_capacity_mw`` is the correct fraction.

    The when-available CF is the basis the floor is applied on (``frac`` x ``pmax``
    x ``availability``); normalising by nameplate over all hours instead would
    double-discount the outage time (the all-hours CF is already deflated by
    downtime, then the injector multiplies by availability again, leaving the
    costly in-city reliability units floored near zero — the documented Astoria /
    Arthur Kill suppression).
    """
    nameplate = float(sum(plant_npl.values()))
    avail = pd.Series(nameplate, index=index)
    path = RAW_DIR / "campd-unit-outages-NYISO.csv"
    if not path.exists():
        return avail
    o = pd.read_csv(path)
    o["facility_id"] = pd.to_numeric(o["facility_id"], errors="coerce")
    o = o[o["facility_id"].isin(plant_npl)].copy()
    o["outage_start"] = pd.to_datetime(o["outage_start"])
    o["outage_end"] = pd.to_datetime(o["outage_end"])
    # Derate each plant by its out units' capacity SHARE (unit_capacity_mw /
    # plant_capacity_mw) of THAT plant's bin nameplate — matching the model's
    # unit-outage derate. Per-plant so a zone with several plants is correct.
    for _, e in o.iterrows():
        pcap = float(e["plant_capacity_mw"]) or 1.0
        pnpl = float(plant_npl.get(int(e["facility_id"]), 0.0))
        share_mw = pnpl * float(e["unit_capacity_mw"]) / pcap
        mask = (index >= e["outage_start"]) & (index < e["outage_end"])
        avail.loc[mask] -= share_mw
    return avail.clip(lower=0.0)


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
        plant_npl, nameplate = zone_steam_plant_codes(zone)
        codes = set(plant_npl)
        if not codes or nameplate <= 0.0:
            continue
        pooled, pooled24 = [], []
        for yr, tser in tmax[zone].items():
            path = RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet"
            if not path.exists():
                continue
            c = pd.read_parquet(path)
            c = c[c["facilityId"].astype(int).isin(codes)].copy()
            c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
            c["date"] = pd.to_datetime(c["date"])
            # Hourly fleet gross + AVAILABLE capacity (nameplate net of unit
            # outages); CF is normalised by available capacity, not nameplate.
            gross_h = c.groupby("ts")["grossLoad"].sum()
            avail_h = zone_available_capacity(plant_npl, gross_h.index)
            g = pd.DataFrame({"gross": gross_h, "avail": avail_h})
            g["date"] = g.index.normalize()
            g["hour"] = g.index.hour
            ev = g[g["hour"].isin(EVENING_HOURS)]
            ev_day = ev.groupby("date").agg(
                gross=("gross", "sum"), avail=("avail", "sum")
            )
            daily = (ev_day["gross"] / ev_day["avail"]).where(ev_day["avail"] > 0)
            df = pd.DataFrame({"cf": daily})
            df["tmax"] = df.index.map(tser)
            pooled.append(df.dropna())
            # 24-hour daily WHEN-AVAILABLE CF for the persistent baseline.
            all_day = g.groupby("date").agg(
                gross=("gross", "sum"), avail=("avail", "sum")
            )
            daily24 = (all_day["gross"] / all_day["avail"]).where(all_day["avail"] > 0)
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
        print(f"\n=== {zone} ST_GAS WHEN-AVAILABLE CF, pooled {args.years} ===")
        print(f"  nameplate                 = {nameplate:.0f} MW, {len(codes)} plants")
        print(f"  corr(CF, TMAX) [evening]  = {corr:+.3f}")
        print(f"  hot-day (>=25C) median CF = {hot['cf'].median():.3f}")
        print(f"  mild-day (<25C) median CF = {cool['cf'].median():.3f}")
        print(f"  nyiso_st_floor_t0_c       = {T0_C:.1f}")
        print(f"  nyiso_st_floor_slope_per_c= {slope:.4f}   (hot-limb, TMAX>=T0)")
        print(f"  nyiso_st_floor_cap        = {cap:.3f}    (p97 evening avail-CF)")
        print(
            f"  nyiso_st_floor_base_ev    = {base:.3f}    (cool-day evening avail-p25)"
        )
        print(f"  nyiso_st_floor_base_24h   = {base24:.3f}    (cool-day 24h avail-p25)")


if __name__ == "__main__":
    main()
