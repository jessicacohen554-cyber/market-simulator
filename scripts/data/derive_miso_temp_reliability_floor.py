"""Derive the MISO dual-limb, ZONAL weather-correlated reliability-floor coeffs.

Mirrors ``scripts/data/derive_neiso_temp_reliability_floor.py`` (dual-limb) and
``derive_nyiso_st_reliability_floor.py`` (per-zone), specialized for MISO, which
spans two OPPOSITE weather regimes within one ISO:

  * **MISO-South (Entergy LA/MS/AR/E-TX).** Summer-AC-peaking AND
    winter-gas-constrained. The steam-gas boilers (Little Gypsy, Sabine, Lewis
    Creek, Big Cajun, Nine Mile Pt) and the simple-cycle CTs are held online on
    hot summer afternoons (hot limb, TMAX) for local reliability, and again in
    deep-winter cold snaps (cold limb, TMIN) when the gas-electric constraint
    prices oil/gas-steam into merit.
  * **MISO-West/MISO-Plains (MN/ND/SD/MT + IA/MO).** Winter-peaking: the
    steam/CT fleet runs in the cold-snap morning/evening peaks (cold limb,
    TMIN), with a weak summer hot limb.
  * **MISO-Illinois/MISO-Indiana/MISO-East (IL + IN/KY + WI/MI).** Mixed; the
    steam fleet carries a modest hot-limb (summer) plus cold-limb (winter)
    signal.

So each zone is keyed to its OWN load-weighted daily TMAX/TMIN, and BOTH limbs
are fit per zone, exactly mirroring the NEISO dual-limb and NYISO per-zone
templates. Physical temperature->commitment rules (NOT a fit to a TWh residual),
forward-reproducible (a forecast year pins a weather year -> a TMAX/TMIN series)
and condition-responsive (hotter summers -> more CT/ST in the South; colder
winters -> more steam/coal everywhere), hence admissible in backcast AND
forecast (CLAUDE.md #10/#11).

Steps:
  1. Fetch NOAA GHCN-Daily TMAX + TMIN for each MISO zone's load-center stations
     and load-weight them into per-zone daily ``tmax``/``tmin`` series.
  2. Build the measured per-zone, per-class daily capacity factor from CAMPD
     unit-level grossLoad (bin_assignments_MISO plant codes), normalized by the
     model bin nameplate so the floor fraction matches the LP capacity basis.
  3. Regress the evening hot-limb CF on TMAX (T0=25 degC) and the winter-peak
     cold-limb CF on TMIN (per-zone T0) to recover slope / cap (p97) / base.
  4. Archive the per-zone daily TMAX/TMIN to
     ``data/raw/miso-weather/miso_zone_temp_daily.csv`` so the floor regenerates
     for a forward year from a pinned weather year.

Run with ``--no-fetch`` to re-derive from the archived weather file (no NOAA
network call). The printed coefficients become the
``transmission.MISO_*_FLOOR_COEFFS`` defaults consumed by
``transmission.inject_miso_temp_reliability_floor`` (enabled per-run via
``--miso-temp-reliability-floor``).
"""

from __future__ import annotations

import argparse
import json
import urllib.request

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

# NOAA GHCN-Daily load-center stations per MISO zone, weighted ~ load share
# within the zone (major-metro airports; mirrors
# data/raw/reference/iso_zone_weather_stations.csv). Fargo USW00014914 returns
# no data so the Dakotas (small load) drop out of MISO-West; MSP carries the
# deep-winter cold signal.
MISO_ZONE_STATIONS: dict[str, dict[str, float]] = {
    "MISO-West": {
        "USW00014922": 1.0,  # Minneapolis-St Paul (MN) — biggest West load
    },
    "MISO-Plains": {
        "USW00014933": 0.5,  # Des Moines (IA)
        "USW00013994": 0.5,  # St Louis Lambert (MO)
    },
    "MISO-Illinois": {
        "USW00094846": 1.0,  # Chicago O'Hare (IL)
    },
    "MISO-Indiana": {
        "USW00093819": 1.0,  # Indianapolis (IN)
    },
    "MISO-East": {
        "USW00094847": 0.6,  # Detroit Metro (MI)
        "USW00014839": 0.4,  # Milwaukee (WI)
    },
    "MISO-South": {
        "USW00012916": 0.35,  # New Orleans (LA) — Entergy core
        "USW00013963": 0.25,  # Little Rock (AR)
        "USW00013940": 0.20,  # Jackson (MS)
        "USW00013957": 0.20,  # Shreveport (LA/E-TX)
    },
}

_NOAA_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations={station}&startDate={start}&endDate={end}"
    "&dataTypes=TMAX,TMIN&format=json"
)

# MISO footprint CAMPD state files (filed by state). Used to load the unit-level
# frames; the per-plant bin Zone then assigns each plant to a MISO zone.
MISO_STATES = (
    "MN",
    "ND",
    "SD",
    "IA",
    "MO",
    "WI",
    "IL",
    "IN",
    "MI",
    "AR",
    "LA",
    "MS",
    "TX",
)

# Hot-limb (summer evening) window + zero-crossing; cold-limb (winter peak)
# window + zero-crossing. Match transmission.MISO_*_FLOOR_HOURS / _T0_C.
HOT_HOURS = range(14, 21)  # HB14-20 inclusive (afternoon-evening AC ramp)
HOT_T0_C = 25.0
COLD_HOURS = (6, 7, 8, 9, 17, 18, 19, 20)  # winter morning + evening peaks
# Per-zone cold-limb zero-crossing (deg C): South hardens later (mild winters,
# T0=5), North/Central earlier (T0=10) where the deep-cold gas constraint binds.
COLD_T0_C: dict[str, float] = {
    "MISO-West": 10.0,
    "MISO-Plains": 10.0,
    "MISO-Illinois": 10.0,
    "MISO-Indiana": 10.0,
    "MISO-East": 10.0,
    "MISO-South": 5.0,
}
# Classes carrying a weather floor and which limbs they track per zone.
FLOOR_CLASSES = ("ST_GAS", "CT_PEAKER")


def fetch_zone_temp(stations: dict[str, float], start: str, end: str) -> pd.DataFrame:
    """Fetch + load-weight NOAA GHCN TMAX/TMIN into a daily temp frame for a zone."""
    rows = []
    for station, weight in stations.items():
        url = _NOAA_URL.format(station=station, start=start, end=end)
        with urllib.request.urlopen(url, timeout=90) as resp:  # noqa: S310
            data = json.loads(resp.read())
        df = pd.DataFrame(data)
        if df.empty:
            continue
        df["TMAX"] = pd.to_numeric(df.get("TMAX"), errors="coerce") / 10.0
        df["TMIN"] = pd.to_numeric(df.get("TMIN"), errors="coerce") / 10.0
        df["w"] = weight
        rows.append(df[["DATE", "TMAX", "TMIN", "w"]])
    allr = pd.concat(rows)

    def _wmean(g: pd.DataFrame, col: str) -> float:
        v, w = g[col], g["w"]
        m = v.notna()
        return float((v[m] * w[m]).sum() / w[m].sum()) if m.any() else np.nan

    out = allr.groupby("DATE").apply(
        lambda g: pd.Series({"tmax_c": _wmean(g, "TMAX"), "tmin_c": _wmean(g, "TMIN")})
    )
    out.index = pd.to_datetime(out.index)
    return out


def _campd(years: list[int]) -> pd.DataFrame:
    """Concatenate MISO-state CAMPD unit-level frames for the requested years."""
    frames = []
    for st in MISO_STATES:
        for yr in years:
            p = RAW_DIR / "campd-unit-level" / f"{st}_{yr}.parquet"
            if p.exists():
                frames.append(pd.read_parquet(p))
    c = pd.concat(frames)
    c["date"] = pd.to_datetime(c["date"])
    c["facilityId"] = c["facilityId"].astype(int)
    return c


def _zone_class_daily_cf(
    campd: pd.DataFrame, bins: pd.DataFrame, zone: str, group: str, hours
) -> tuple[pd.DataFrame, float]:
    """Daily capacity factor for a (zone, group) fleet over ``hours`` on model basis.

    CF is normalized by the bin nameplate (= the model's pmax for the group in
    the zone) and clipped to [0, 1] so the derived fraction is the share of the
    LP's available capacity the floor should hold online.
    """
    sub = bins[(bins["Plant_Group"] == group) & (bins["Zone"] == zone)]
    codes = set(sub["Plant_Code"].astype(int))
    nameplate = float(sub["Nameplate_MW"].sum())
    if nameplate <= 0.0 or not codes:
        return pd.DataFrame({"cf": []}), 0.0
    cc = campd[campd["facilityId"].isin(codes)]
    ev = cc[cc["hour"].isin(list(hours))]
    daily = (
        ev.groupby("date")["grossLoad"].sum() / (nameplate * len(list(hours)))
    ).clip(0.0, 1.0)
    return pd.DataFrame({"cf": daily}), nameplate


def _fit_limb(df: pd.DataFrame, temp_col: str, t0: float, cold: bool):
    """Return (slope, cap, base, rho, n) for one temperature limb."""
    df = df.dropna(subset=["cf", temp_col])
    if df.empty:
        return None
    if cold:
        # Coldness drive = t0 - T (rises as it gets colder); fit on cold days.
        active = df[df[temp_col] < t0]
        drive = t0 - active[temp_col]
    else:
        active = df[df[temp_col] >= t0]
        drive = active[temp_col] - t0
    if len(active) < 10:
        return None
    slope = float(np.polyfit(drive, active["cf"], 1)[0])
    cap = float(df["cf"].quantile(0.97))
    # Base = the off-limb (mild) p25 CF — the persistent baseline below T0.
    off = df[df[temp_col] >= t0] if cold else df[df[temp_col] < t0]
    base = float(off["cf"].quantile(0.25)) if len(off) else 0.0
    rho = float(drive.corr(active["cf"], method="spearman"))
    return slope, cap, base, rho, len(active)


def main() -> None:
    """Derive per-zone dual-limb coefficients, archive the weather series, print."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Re-derive from the archived weather file (no NOAA network call).",
    )
    args = ap.parse_args()

    archive = RAW_DIR / "miso-weather" / "miso_zone_temp_daily.csv"
    if args.no_fetch:
        wx_all = pd.read_csv(archive, parse_dates=["date"])
    else:
        frames = []
        for zone, stations in MISO_ZONE_STATIONS.items():
            zf = pd.concat(
                fetch_zone_temp(stations, f"{y}-01-01", f"{y}-12-31")
                for y in args.years
            )
            zf = zf.reset_index()
            zf.columns = ["date", "tmax_c", "tmin_c"]
            zf["zone"] = zone
            frames.append(zf)
        wx_all = pd.concat(frames)
        wx_all["date"] = pd.to_datetime(wx_all["date"]).dt.strftime("%Y-%m-%d")
        archive.parent.mkdir(parents=True, exist_ok=True)
        wx_all = wx_all[["date", "zone", "tmax_c", "tmin_c"]].sort_values(
            ["zone", "date"]
        )
        wx_all.to_csv(archive, index=False)
        print(f"archived {len(wx_all)} zone-days -> {archive}")
        wx_all["date"] = pd.to_datetime(wx_all["date"])

    bins = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_MISO.csv")
    campd = _campd(args.years)

    print("\n# MISO_ST_FLOOR_COEFFS / MISO_CT_FLOOR_COEFFS candidate values")
    print(
        "# zone: (hot_slope, hot_t0, hot_cap, hot_base, cold_slope, cold_t0, cold_cap)"
    )
    for group in FLOOR_CLASSES:
        print(f"\n================= {group} =================")
        for zone in MISO_ZONE_STATIONS:
            wx = wx_all[wx_all["zone"] == zone].set_index("date")
            # Hot limb (summer evening).
            dfh, npmw = _zone_class_daily_cf(campd, bins, zone, group, HOT_HOURS)
            if npmw <= 0.0:
                print(f"  {zone}: no {group} bins")
                continue
            dfh["tmax"] = dfh.index.map(wx["tmax_c"])
            hot = _fit_limb(dfh, "tmax", HOT_T0_C, cold=False)
            # Cold limb (winter peaks).
            dfc, _ = _zone_class_daily_cf(campd, bins, zone, group, COLD_HOURS)
            dfc["tmin"] = dfc.index.map(wx["tmin_c"])
            t0c = COLD_T0_C[zone]
            cold = _fit_limb(dfc, "tmin", t0c, cold=True)
            print(f"  --- {zone} (nameplate {npmw:.0f} MW) ---")
            if hot:
                s, cap, base, rho, n = hot
                print(
                    f"    HOT  slope={s:+.4f} t0={HOT_T0_C:.0f} cap={cap:.3f} "
                    f"base={base:.3f}  rho={rho:+.2f} n={n}"
                )
            if cold:
                s, cap, base, rho, n = cold
                print(
                    f"    COLD slope={s:+.4f} t0={t0c:.0f} cap={cap:.3f} "
                    f"base={base:.3f}  rho={rho:+.2f} n={n}"
                )


if __name__ == "__main__":
    main()
