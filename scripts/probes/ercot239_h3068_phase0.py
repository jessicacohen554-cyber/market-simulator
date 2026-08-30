"""ercot-239 round 3: Phase-0 bounded diagnosis of h3068-2024 (May 8, 20:00).

ZERO-SOLVE. Reads the FORWARD keeper's committed 2024 sidecars
(``results/calibration/ercot234_eastex_identity``), the committed actuals,
the EIA-930 wide extract and the measured ORDC/reserves series, and measures
WHY the model holds $798 at the hour reality printed $110.41 — the standing
band-top-blind hour (FINDING-ercot225 section 1). Per
``docs/PRECOMMIT-ercot239-h3068-phase0-2026-08-30.md`` (pushed and
blob-verified before this ran). No lever, no gate change, no matrix verdict.

Run:
    python scripts/probes/ercot239_h3068_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "ercot234_eastex_identity"
ACTUALS = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
EIA_WIDE = REPO / "data" / "raw" / "eia-930-hourly" / "ERCO hourly.parquet"
MEASURED_ORDC = REPO / "data" / "raw" / "ercot" / "ercot_2024_ordc_reserves_hourly.parquet"
OUT_JSON = REPO / "results" / "calibration" / "ercot239_h3068_phase0.json"

H = 3068
W0, W1 = 3060, 3078  # the precommit's event window (inclusive)
YEAR = 2024

THERMAL = (
    "CC_CHP", "CC_REGULAR", "COAL_LIGNITE", "COAL_PRB",
    "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS", "oil",
)


def _sidecar(name: str) -> pd.DataFrame:
    df = pd.read_parquet(BUNDLE / "hourly" / f"{name}_{YEAR}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df[df["year"] == YEAR] if "year" in df.columns else df


def _eia_2024() -> pd.DataFrame:
    df = pd.read_parquet(EIA_WIDE)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    local = utc.dt.tz_convert("America/Chicago").dt.tz_localize(None)
    hour_ending = local - pd.Timedelta(hours=1)
    keep = (hour_ending.dt.year == YEAR) & ~(
        (hour_ending.dt.month == 2) & (hour_ending.dt.day == 29)
    )
    out = df[keep].assign(_utc=utc[keep]).sort_values("_utc").reset_index(drop=True)
    assert len(out) == 8760, f"EIA-930 local-{YEAR} rows = {len(out)} != 8760"
    return out


def main() -> None:
    sys_df = _sidecar("system")
    g = sys_df.groupby("hour")
    rng = range(8760)
    num = (sys_df["price"] * sys_df["demand"]).groupby(sys_df["hour"]).sum()
    den = g["demand"].sum()
    m = np.nan_to_num((num / den).reindex(rng).to_numpy(float))

    a_df = pd.read_parquet(ACTUALS)
    a = a_df[a_df["year"] == YEAR].sort_values("hour")["rt"].to_numpy(float)[:8760]

    # V-0 (precommit section 1): the card's h3068 values reproduce.
    assert abs(m[H] - 798.20) <= 0.05, f"V-0 FAIL model h3068 {m[H]:.2f} != 798.20"
    assert abs(a[H] - 110.41) <= 0.05, f"V-0 FAIL actual h3068 {a[H]:.2f} != 110.41"

    def _s(series: pd.Series) -> np.ndarray:
        return np.nan_to_num(series.reindex(rng).to_numpy(float))

    slack = _s(g["slack"].sum())
    dump = _s(g["dump"].sum())
    rp = _s(g["reserve_price"].max())
    oa = _s(g["ordc_adder"].max())
    rto = (
        _s(g["rtordpa_overlay"].max())
        if "rtordpa_overlay" in sys_df.columns
        else np.zeros(8760)
    )
    pmin = _s(g["price"].min())
    pmax = _s(g["price"].max())
    mdl_dem = _s(g["demand"].sum())

    ch = _sidecar("class_hourly")

    def _k(mask) -> np.ndarray:
        return _s(ch[mask].groupby("hour")["mw"].sum())

    thermal = _k(ch["klass"].isin(THERMAL))
    wind = _k(ch["klass"] == "wind")
    solar = _k(ch["klass"] == "solar")

    st = _sidecar("storage").groupby("hour")
    chg = _s(st["charge_mw"].sum())
    dis = _s(st["discharge_mw"].sum())

    ad = _sidecar("adaptive").set_index("hour").reindex(rng)
    floor_usd = np.nan_to_num(ad["floor_usd"].to_numpy(float))
    p_hat = np.nan_to_num(ad["p_hat_day"].to_numpy(float))
    s_model = np.nan_to_num(ad["s_model_day"].to_numpy(float))

    rf = _sidecar("reserve_family")

    eia = _eia_2024()
    act_d = eia["Demand"].to_numpy(float)
    act_w = np.nan_to_num(eia["NG: WND"].to_numpy(float))
    act_s = np.nan_to_num(eia["NG: SUN"].to_numpy(float))
    act_nl = act_d - act_w - act_s
    ti = eia["Total interchange"].to_numpy(float)
    # Alignment (round-1 convention): model demand vs EIA Demand best at lag 0.
    lags = {
        lag: float(np.corrcoef(mdl_dem[3:-3], act_d[3 + lag : 8757 + lag])[0, 1])
        for lag in (-1, 0, 1)
    }
    assert max(lags, key=lags.get) == 0, f"alignment FAIL {lags}"
    mdl_nl = mdl_dem - wind - solar

    mo = pd.read_parquet(MEASURED_ORDC).sort_values("hour").reset_index(drop=True)
    rtolcap = mo["rtolcap"].to_numpy(float)
    rtorpa = mo["rtorpa"].to_numpy(float)
    rtordpa_meas = mo["rtordpa"].to_numpy(float)
    lam_meas = mo["system_lambda"].to_numpy(float)
    prc = mo["prc"].to_numpy(float)

    def _pctl(vals: np.ndarray, x: float) -> float:
        v = vals[~np.isnan(vals)]
        return round(float((v <= x).mean() * 100.0), 1)

    window = []
    for h in range(W0, W1 + 1):
        fam = rf[rf["hour"] == h]
        window.append(
            {
                "h": h,
                "hod": h % 24,
                "model_lw": round(float(m[h]), 2),
                "model_price_minmax": [round(float(pmin[h]), 1), round(float(pmax[h]), 1)],
                "actual_rt": round(float(a[h]), 2),
                "slack": round(float(slack[h]), 1),
                "dump": round(float(dump[h]), 1),
                "reserve_price": round(float(rp[h]), 2),
                "ordc_adder": round(float(oa[h]), 2),
                "rtordpa_overlay": round(float(rto[h]), 2),
                "families": {
                    r["family"]: {
                        "dual": round(float(r["dual"]), 2),
                        "short": round(float(r["shortfall_mw"]), 0),
                    }
                    for _, r in fam.iterrows()
                },
                "thermal": round(float(thermal[h]), 0),
                "wind": round(float(wind[h]), 0),
                "solar": round(float(solar[h]), 0),
                "storage_charge": round(float(chg[h]), 0),
                "storage_discharge": round(float(dis[h]), 0),
                "adaptive": {
                    "floor_usd": round(float(floor_usd[h]), 2),
                    "p_hat_day": round(float(p_hat[h]), 2),
                    "s_model_day": round(float(s_model[h]), 3),
                },
                "model_demand": round(float(mdl_dem[h]), 0),
                "model_net_load": round(float(mdl_nl[h]), 0),
                "actual_demand": round(float(act_d[h]), 0),
                "actual_net_load": round(float(act_nl[h]), 0),
                "interchange": round(float(ti[h]), 0),
                "measured": {
                    "rtolcap": round(float(rtolcap[h]), 0),
                    "rtolcap_pctl": _pctl(rtolcap, float(rtolcap[h])),
                    "prc": round(float(prc[h]), 0),
                    "rtorpa": round(float(rtorpa[h]), 2),
                    "rtordpa": round(float(rtordpa_meas[h]), 2),
                    "system_lambda": round(float(lam_meas[h]), 2),
                },
            }
        )

    # M-3 release comparison over the window.
    hw = np.arange(W0, W1 + 1)
    aw = a[W0 : W1 + 1]
    mw = m[W0 : W1 + 1]

    def _release_price(series: np.ndarray, thresh: float = 200.0):
        pk = int(np.nanargmax(series))
        for i in range(pk + 1, len(series)):
            if series[i] < thresh:
                return int(hw[i]), int(hw[pk])
        return None, int(hw[pk])

    def _release_nl(series: np.ndarray, drop: float = 2000.0):
        pk = int(np.nanargmax(series))
        for i in range(pk + 1, len(series)):
            if series[i] <= series[pk] - drop:
                return int(hw[i]), int(hw[pk])
        return None, int(hw[pk])

    ar, apk = _release_price(aw)
    mr, mpk = _release_price(mw)
    anr, anpk = _release_nl(act_nl[W0 : W1 + 1])
    mnr, mnpk = _release_nl(mdl_nl[W0 : W1 + 1])
    release = {
        "actual_price": {"peak_h": apk, "release_h": ar},
        "model_price": {"peak_h": mpk, "release_h": mr},
        "actual_net_load": {"peak_h": anpk, "release_h": anr},
        "model_net_load": {"peak_h": mnpk, "release_h": mnr},
        "price_release_lag_h": (mr - ar) if (mr is not None and ar is not None) else None,
        "netload_release_lag_h": (mnr - anr)
        if (mnr is not None and anr is not None)
        else None,
    }

    # M-4 marginal-setter attribution at h3067-h3069.
    attribution = {}
    for h in (3067, 3068, 3069):
        legs = {
            "adaptive_floor_usd": float(floor_usd[h]),
            "reserve_price": float(rp[h]),
            "ordc_adder": float(oa[h]),
        }
        lw_h = float(m[h])
        attribution[h] = {
            "model_lw": round(lw_h, 2),
            "legs": {k: round(v, 2) for k, v in legs.items()},
            "within_150": sorted(k for k, v in legs.items() if abs(lw_h - v) <= 150.0),
            "storage_discharge": round(float(dis[h]), 0),
        }

    fam_h = rf[rf["hour"] == H]
    priors = {
        "P1_adaptive_hold": {
            "lw_minus_floor": round(float(m[H] - floor_usd[H]), 2),
            "within_150": bool(abs(m[H] - floor_usd[H]) <= 150.0),
            "storage_discharge_ge_500": bool(dis[H] >= 500.0),
        },
        "P2_reality_released": {
            "actual_h3068_lt_200": bool(a[H] < 200.0),
            "actual_h3066_h3067_ge_500": [round(float(a[3066]), 2), round(float(a[3067]), 2)],
            "rtorpa_rtordpa_lt_50": bool(
                rtorpa[H] < 50.0 and rtordpa_meas[H] < 50.0
            ),
        },
        "P3_netload_lag_le_1": release["netload_release_lag_h"],
        "P4_no_reserve_scarcity": {
            "all_zero_shortfall": bool((fam_h["shortfall_mw"] <= 0.0).all()),
            "max_dual": round(float(fam_h["dual"].max()), 2),
        },
    }

    res = {
        "session": "ercot-239 round 3",
        "bundle": "ercot234_eastex_identity (forward keeper)",
        "precommit": "docs/PRECOMMIT-ercot239-h3068-phase0-2026-08-30.md",
        "v0": {"model_h3068": round(float(m[H]), 2), "actual_h3068": round(float(a[H]), 2)},
        "alignment_lag_corr": {str(k): round(v, 4) for k, v in lags.items()},
        "window": window,
        "release": release,
        "attribution": attribution,
        "priors": priors,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    print(json.dumps({"v0": res["v0"], "release": release, "attribution": attribution, "priors": priors}, indent=1))


if __name__ == "__main__":
    main()
