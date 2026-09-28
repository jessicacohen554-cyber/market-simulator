"""R-CAISO-13 (ZERO LP): battery discharge timing vs the evening price plateau.

Reads only committed artifacts: the keeper span bundle's hourly sidecars
(``rcaiso11_A_span``), the measured CAISO Outlook battery series
(``data/raw/storage-dispatch-actuals``, fixed-PST hour-beginning, per its
README and ``build_storage_dispatch_actuals.std_hour_of_year``), EIA-930 CISO
solar (hour-ENDING UTC -> start = UTC - 1 h) as a clock witness, and OASIS DAM
TH_SP15.

Questions:
1. CLOCK: is the measured series on the model clock? Witness: the measured
   charge centroid against the EIA-930 solar centroid and the model's own
   charge centroid.
2. LAG: does the ~1 h late discharge survive on the correct clock?
3. CAUSALITY: is storage following a flat price or making it flat? Test: the
   LP optimality identity -- in hours where the fleet discharges strictly
   inside its bounds, price must equal the SOC dual times eta_dis, so it is
   the same number in every such hour of a day. Report the within-day spread
   of price across interior-discharge hours, and the evening plateau's width
   vs the discharging hours.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso13_storage_timing.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path("results/calibration/rcaiso11_A_span/hourly")
MEAS = Path("data/raw/storage-dispatch-actuals/CAISO_storage_hourly.parquet")
EIA = Path("data/raw/eia-930-hourly/CISO hourly.parquet")
DAM = "data/raw/lmp-data/CAISO/CAISO_dam_hourly_{y}.csv"
OUT = Path("results/calibration/_rcaiso13/storage_timing.json")
T, D = 8760, 365
YEARS = (2022, 2023, 2024, 2025)
SUMMER = slice(151 * 24, 273 * 24)  # Jun 1 - Sep 30 (non-leap day index)
_MS = np.cumsum((0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)) * 24


def slot(utc: pd.Series, y: int) -> np.ndarray:
    """Model fixed-PST hour-beginning non-leap slot (Feb 29 -> -1)."""
    s = pd.DatetimeIndex(pd.to_datetime(utc, utc=True)).tz_convert("Etc/GMT+8")
    ok = (s.year == y) & ~((s.month == 2) & (s.day == 29))
    idx = _MS[s.month - 1] + (s.day - 1) * 24 + s.hour
    return np.where(ok, idx, -1)


def on_clock(vals: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """Scatter values onto an 8760 vector (NaN where unobserved)."""
    out = np.full(T, np.nan)
    k = idx >= 0
    out[idx[k]] = vals[k]
    return out


def hod(x: np.ndarray, sl: slice = slice(None)) -> np.ndarray:
    """Hour-of-day mean over the day window ``sl``."""
    v = np.full(T, np.nan)
    v[sl] = x[sl]
    return np.nanmean(v.reshape(D, 24), axis=0)


def centroid(p: np.ndarray, lo: int = 5, hi: int = 20) -> float:
    """Hour-beginning centroid (+0.5 = mid-hour) of a positive profile."""
    h = np.arange(24)[lo:hi]
    w = np.clip(p[lo:hi], 0, None)
    return float((h + 0.5) @ w / w.sum())


def xcorr_lag(a: np.ndarray, b: np.ndarray, lags=range(-3, 4)) -> dict:
    """Pearson r of daily-profile a(h) vs b(h+lag); + lag = b is late."""
    out = {}
    for L in lags:
        out[L] = float(np.corrcoef(a, np.roll(b, -L))[0, 1])
    return out


def year(y: int) -> dict:
    """Clock, lag and causality census for year ``y``."""
    st = pd.read_parquet(BUNDLE / f"storage_{y}.parquet")
    li = st[st.tech == "li_ion"].set_index("hour").reindex(range(T))
    m_dis, m_chg = li.discharge_mw.to_numpy(), li.charge_mw.to_numpy()
    m_net, soc = m_dis - m_chg, li.soc_mwh.to_numpy()
    ecap = float(li.energy_cap_mwh.max())

    me = pd.read_parquet(MEAS)
    me = me[me.year == y].set_index("hour").reindex(range(T))
    a_net = me.net_mw.to_numpy()
    a_dis, a_chg = me.discharge_mw.to_numpy(), me.charge_mw.to_numpy()

    e = pd.read_parquet(EIA, columns=["UTC time", "NG: SUN"])
    sun = on_clock(
        e["NG: SUN"].to_numpy(float),
        slot(
            pd.to_datetime(e["UTC time"]).dt.tz_localize("UTC") - pd.Timedelta(hours=1),
            y,
        ),
    )

    sy = pd.read_parquet(BUNDLE / f"system_{y}.parquet")
    pz = sy.pivot(index="hour", columns="zone", values="price").reindex(range(T))
    dz = sy.pivot(index="hour", columns="zone", values="demand").reindex(range(T))
    cz = [z for z in pz.columns if not z.startswith("WECC")]
    price = (pz[cz] * dz[cz]).sum(1).to_numpy() / dz[cz].sum(1).to_numpy()
    sp15 = pz["SP15_rest"].to_numpy()

    dam = None
    p = Path(DAM.format(y=y))
    if p.exists():
        d = pd.read_csv(p)
        d = d[d.node == "TH_SP15_GEN-APND"]
        dam = on_clock(d.LMP.to_numpy(float), slot(d.interval_start_gmt, y))

    r = {
        "energy_cap_mwh": round(ecap),
        "model_dis_max_mw": round(float(np.nanmax(m_dis))),
    }
    for tag, sl in (("all", slice(None)), ("jun_sep", SUMMER)):
        md, ad, mc, ac = hod(m_dis, sl), hod(a_dis, sl), hod(m_chg, sl), hod(a_chg, sl)
        mn, an = hod(m_net, sl), hod(a_net, sl)
        block = {
            "model_net_gw": [round(v / 1e3, 2) for v in mn],
            "meas_net_gw": [round(v / 1e3, 2) for v in an],
            "model_price_sp15": [round(v, 1) for v in hod(sp15, sl)],
            "model_price_loadwt": [round(v, 1) for v in hod(price, sl)],
            # CLOCK witnesses: charge centroids vs solar centroid
            "centroid_sun_eia930": round(centroid(hod(sun, sl)), 2),
            "centroid_charge_meas": round(centroid(ac), 2),
            "centroid_charge_model": round(centroid(mc), 2),
            "centroid_dis_meas_h12_24": round(centroid(ad, 12, 24), 2),
            "centroid_dis_model_h12_24": round(centroid(md, 12, 24), 2),
            "net_profile_xcorr_model_lag_vs_meas": {
                str(k): round(v, 3) for k, v in xcorr_lag(an, mn).items()
            },
        }
        if dam is not None:
            block["dam_sp15"] = [round(v, 1) for v in hod(dam, sl)]
            block["centroid_dis_vs_dam_peak_hour"] = int(np.nanargmax(hod(dam, sl)))
            block["model_price_peak_hour"] = int(np.nanargmax(hod(sp15, sl)))
        r[tag] = block

    # CAUSALITY: LP identity on interior-discharge hours, per day.
    pd_, dd, sd = sp15.reshape(D, 24), m_dis.reshape(D, 24), soc.reshape(D, 24)
    dmax = np.nanmax(m_dis)
    interior = (dd > 1.0) & (dd < 0.98 * dmax) & (sd > 0.01 * ecap) & (sd < 0.99 * ecap)
    spreads, n_int, eve_active = [], [], []
    for k in range(D):
        h = interior[k]
        if h.sum() >= 2:
            v = pd_[k, h]
            spreads.append(float(v.max() - v.min()))
            n_int.append(int(h.sum()))
        eve_active.append(int((dd[k, 16:24] > 1.0).sum()))
    r["lp_identity"] = {
        "days_with_2plus_interior_dis_hours": len(spreads),
        "median_price_spread_across_interior_dis_hours": round(
            float(np.median(spreads)), 2
        ),
        "p90_price_spread_across_interior_dis_hours": round(
            float(np.percentile(spreads, 90)), 2
        ),
        "median_interior_dis_hours_per_day": float(np.median(n_int)),
        "median_discharging_hours_h16_23": float(np.median(eve_active)),
    }
    # How flat is the model plateau vs DAM, and where is the fleet?
    if dam is not None:
        dm = dam.reshape(D, 24)
        r["plateau"] = {
            "model_h18_22_daily_cv_median": round(
                float(
                    np.nanmedian(
                        pd_[:, 18:23].std(1) / np.maximum(pd_[:, 18:23].mean(1), 1)
                    )
                ),
                3,
            ),
            "dam_h18_22_daily_cv_median": round(
                float(
                    np.nanmedian(
                        np.nanstd(dm[:, 18:23], 1)
                        / np.maximum(np.nanmean(dm[:, 18:23], 1), 1)
                    )
                ),
                3,
            ),
        }
    return r


def main() -> None:
    """Run the census for every span year and write the JSON."""
    out = {str(y): year(y) for y in YEARS}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    for y, r in out.items():
        b = r["jun_sep"]
        print(
            y,
            "sun",
            b["centroid_sun_eia930"],
            "chgM",
            b["centroid_charge_meas"],
            "chgX",
            b["centroid_charge_model"],
            "disM",
            b["centroid_dis_meas_h12_24"],
            "disX",
            b["centroid_dis_model_h12_24"],
            "lag",
            b["net_profile_xcorr_model_lag_vs_meas"],
        )
        print("  lp", r["lp_identity"], r.get("plateau"))


if __name__ == "__main__":
    main()
