"""Derive the NEISO dual-limb weather-correlated reliability-floor coefficients.

Mirrors ``scripts/data/derive_caiso_ct_reliability_floor.py`` /
``derive_nyiso_ct_reliability_floor.py`` for ISO-NE, which — unlike the
summer-only CAISO/NYISO peaker floors — is a **dual-limb** weather system:

  * **CT_PEAKER (hot limb).** Simple-cycle gas peakers track the summer cooling
    ramp; their measured evening CF rises with the daily max temperature (TMAX).
  * **COAL + ST_GAS (cold limb).** ISO-NE's lone Merrimack-class coal unit and
    lone steam-gas unit run almost exclusively during deep-winter cold snaps,
    when the gas-electric constraint prices these oil/coal/steam reliability
    units into merit; their CF rises as the daily min temperature (TMIN) falls
    and is ~uncorrelated with TMAX.

Steps:
  1. Fetch NOAA GHCN-Daily TMAX + TMIN for the six ISO-NE load-center stations
     (Boston Logan, Providence, Hartford-Bradley, Portland-ME, Concord-NH,
     Burlington-VT) and load-weight them into daily ``tmax``/``tmin`` series.
  2. Build the measured per-class daily capacity factor from CAMPD unit-level
     grossLoad (bin_assignments_NEISO plant codes), normalized by the model's
     bin nameplate so the floor fraction matches the LP capacity basis.
  3. Regress CT evening (HB16-21) CF on TMAX (hot limb, T0=25 degC) and COAL /
     ST_GAS winter-peak (HB6-9+17-20) CF on TMIN (cold limb, per-group T0) to
     recover slope / cap (p97) / base — physical temperature->commitment rules,
     NOT a fit to a TWh residual.
  4. Archive the daily TMAX/TMIN series to
     ``data/raw/neiso-weather/neiso_load_weighted_temp_daily.csv`` so the floor
     regenerates for a forward year from a pinned weather year.

Run with ``--no-fetch`` to re-derive from the archived weather file (no NOAA
network call). The coefficients become the ScenarioConfig defaults
(``neiso_ct_floor_*`` / ``neiso_coldsnap_floor_*``) consumed by
``transmission.inject_neiso_temp_reliability_floor``.
"""

from __future__ import annotations

import argparse
import json
import urllib.request

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR

# NOAA GHCN-Daily stations for the ISO-NE load centers, weighted ~ zonal load
# share (North ME/NH/VT, Central WCMA/SEMA/RI, Boston NEMA, Connecticut).
NEISO_TMAX_STATIONS: dict[str, float] = {
    "USW00014739": 0.30,  # Boston Logan (Boston/WCMA)
    "USW00014765": 0.20,  # Providence T.F. Green (SEMA/RI)
    "USW00014740": 0.29,  # Hartford / Windsor Locks Bradley (Connecticut)
    "USW00014764": 0.10,  # Portland ME Intl Jetport (ME)
    "USW00014745": 0.06,  # Concord NH (NH)
    "USW00014742": 0.05,  # Burlington VT (VT)
}

_NOAA_URL = (
    "https://www.ncei.noaa.gov/access/services/data/v1?dataset=daily-summaries"
    "&stations={station}&startDate={start}&endDate={end}"
    "&dataTypes=TMAX,TMIN&format=json"
)

# NEISO CAMPD is filed by state; ISO-NE = the six New England states.
NEISO_STATES = ("CT", "MA", "ME", "NH", "RI", "VT")

# Hot-limb (CT_PEAKER) evening window + zero-crossing (matches transmission.
# NEISO_CT_FLOOR_HOURS); cold-limb (COAL/ST_GAS) winter-peak window + per-group
# zero-crossings (matches transmission.NEISO_COLDSNAP_FLOOR_HOURS / _T0_C).
HOT_HOURS = range(16, 22)  # HB16-21 inclusive
HOT_T0_C = 25.0
COLD_HOURS = (6, 7, 8, 9, 17, 18, 19, 20)
COLD_T0_C = {"COAL": 5.0, "ST_GAS": 0.0}


def fetch_neiso_temp(start: str, end: str) -> pd.DataFrame:
    """Fetch + load-weight NOAA GHCN TMAX/TMIN into a daily NEISO temp frame."""
    rows = []
    for station, weight in NEISO_TMAX_STATIONS.items():
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
    """Concatenate NEISO-state CAMPD unit-level frames for the requested years."""
    frames = []
    for st in NEISO_STATES:
        for yr in years:
            p = RAW_DIR / "campd-unit-level" / f"{st}_{yr}.parquet"
            if p.exists():
                frames.append(pd.read_parquet(p))
    c = pd.concat(frames)
    c["date"] = pd.to_datetime(c["date"])
    c["facilityId"] = c["facilityId"].astype(int)
    return c


def _class_daily_cf(
    campd: pd.DataFrame, bins: pd.DataFrame, group: str, hours
) -> pd.DataFrame:
    """Daily capacity factor for a plant group over ``hours``, on the model basis.

    CF is normalized by the bin nameplate (= the model's pmax for the group) and
    clipped to [0, 1] so the derived fraction is the share of the LP's available
    capacity the floor should hold online.
    """
    sub = bins[bins["Plant_Group"] == group]
    codes = set(sub["Plant_Code"].astype(int))
    nameplate = float(sub["Nameplate_MW"].sum())
    cc = campd[campd["facilityId"].isin(codes)]
    ev = cc[cc["hour"].isin(list(hours))]
    daily = (
        ev.groupby("date")["grossLoad"].sum() / (nameplate * len(list(hours)))
    ).clip(0.0, 1.0)
    return pd.DataFrame({"cf": daily}), nameplate


def main() -> None:
    """Derive coefficients, archive the weather series, print the fits."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--no-fetch",
        action="store_true",
        help="Re-derive from the archived weather file (no NOAA network call).",
    )
    args = ap.parse_args()

    archive = RAW_DIR / "neiso-weather" / "neiso_load_weighted_temp_daily.csv"
    if args.no_fetch:
        wx = pd.read_csv(archive, parse_dates=["date"]).set_index("date")
    else:
        frames = [fetch_neiso_temp(f"{y}-01-01", f"{y}-12-31") for y in args.years]
        wx = pd.concat(frames)
        out = wx.reset_index()
        out.columns = ["date", "tmax_c", "tmin_c"]
        out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
        archive.parent.mkdir(parents=True, exist_ok=True)
        out.sort_values("date").to_csv(archive, index=False)
        print(f"archived {len(out)} days -> {archive}")

    bins = pd.read_csv(RAW_DIR / "_processed-legacy" / "bin_assignments_NEISO.csv")
    campd = _campd(args.years)

    # --- Hot limb: CT_PEAKER evening CF vs TMAX -----------------------------
    df, npmw = _class_daily_cf(campd, bins, "CT_PEAKER", HOT_HOURS)
    df["tmax"] = df.index.map(wx["tmax_c"])
    df = df.dropna()
    hot = df[df["tmax"] >= HOT_T0_C]
    slope = float(np.polyfit(hot["tmax"] - HOT_T0_C, hot["cf"], 1)[0])
    cap = float(df["cf"].quantile(0.97))
    base = float(df[df["tmax"] < HOT_T0_C]["cf"].quantile(0.25))
    rho = df["tmax"].corr(df["cf"], method="spearman")
    print(f"\n=== CT_PEAKER hot limb (evening HB16-21), pooled {args.years} ===")
    print(f"  nameplate basis           = {npmw:.0f} MW")
    print(f"  neiso_ct_floor_t0_c        = {HOT_T0_C:.1f}")
    print(f"  neiso_ct_floor_slope_per_c = {slope:.4f}   (hot limb, TMAX>=T0)")
    print(f"  neiso_ct_floor_cap         = {cap:.3f}    (p97 evening CF)")
    print(f"  neiso_ct_floor_base        = {base:.3f}    (cool-day evening p25)")
    print(f"  rho(TMAX, CF)              = {rho:+.3f}")

    # --- Cold limb: COAL + ST_GAS winter-peak CF vs TMIN --------------------
    cold_slopes = []
    for group in ("COAL", "ST_GAS"):
        df, npmw = _class_daily_cf(campd, bins, group, COLD_HOURS)
        df["tmin"] = df.index.map(wx["tmin_c"])
        df = df.dropna()
        t0 = COLD_T0_C[group]
        cold = df[df["tmin"] < t0]
        slope = float(np.polyfit(t0 - cold["tmin"], cold["cf"], 1)[0])
        cap = float(df["cf"].quantile(0.97))
        rho = (t0 - cold["tmin"]).corr(cold["cf"], method="spearman")
        cold_slopes.append(slope)
        print(f"\n=== {group} cold limb (winter peaks HB6-9+17-20) ===")
        print(f"  nameplate basis              = {npmw:.0f} MW")
        print(f"  zero-crossing T0 (TMIN)      = {t0:.1f} degC")
        print(f"  cold-limb slope_per_c        = {slope:.4f}")
        print(f"  cap (p97 winter-peak CF)     = {cap:.3f}")
        print(f"  rho(coldness, CF)            = {rho:+.3f}")
    print(
        f"\n  neiso_coldsnap_floor_slope_per_c = {np.mean(cold_slopes):.4f}  "
        f"(mean COAL/ST_GAS cold-limb slope)\n  neiso_coldsnap_floor_cap = 1.000  "
        "(deep-cold units saturate to full available capacity)"
    )


if __name__ == "__main__":
    main()
