"""ercot-243 Phase-0: census of the 2024/2025 event-exit-hour population.

ZERO-SOLVE. Reads the FORWARD keeper's committed sidecars
(``results/calibration/ercot234_eastex_identity``), the committed actuals,
the EIA-930 wide extract and the measured ORDC/reserves series, and applies
the census signature, trailing-edge separation measurement, priors and
kills declared ex ante in
``docs/PRECOMMIT-ercot243-release-exit-phase0-2026-08-30.md`` (pushed and
blob-verified before this ran). No lever, no gate change, no solve.

Run:
    python scripts/probes/ercot243_release_exit_phase0.py
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
MEASURED_ORDC = REPO / "data" / "raw" / "ercot" / "ercot_{year}_ordc_reserves_hourly.parquet"
OUT_JSON = REPO / "results" / "calibration" / "ercot243_release_exit_phase0.json"

YEARS = (2024, 2025)
WINDOW_HODS = (17, 18, 19, 20)  # ERCOT_ADAPTIVE_WINDOW_HOURS (results/scarcity.py)
VOLL = 5000.0  # keeper run_config ordc_voll; asserted against floor identity below
FAMILIES = ("RegUp_withheld", "RRS_withheld", "ECRS_withheld", "NonSpin", "ercot_ordc_total")


def _sidecar(name: str, year: int) -> pd.DataFrame:
    df = pd.read_parquet(BUNDLE / "hourly" / f"{name}_{year}.parquet")
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    return df[df["year"] == year] if "year" in df.columns else df


def _eia_year(year: int) -> pd.DataFrame:
    """EIA-930 wide extract mapped to the local 8760, ercot-239 convention."""
    df = pd.read_parquet(EIA_WIDE)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    local = utc.dt.tz_convert("America/Chicago").dt.tz_localize(None)
    hour_ending = local - pd.Timedelta(hours=1)
    keep = (hour_ending.dt.year == year) & ~(
        (hour_ending.dt.month == 2) & (hour_ending.dt.day == 29)
    )
    out = df[keep].assign(_utc=utc[keep]).sort_values("_utc").reset_index(drop=True)
    assert len(out) == 8760, f"EIA-930 local-{year} rows = {len(out)} != 8760"
    return out


def _series_for_year(year: int) -> dict[str, np.ndarray]:
    rng = range(8760)
    sys_df = _sidecar("system", year)
    g = sys_df.groupby("hour")

    def _s(series: pd.Series) -> np.ndarray:
        return np.nan_to_num(series.reindex(rng).to_numpy(float))

    num = (sys_df["price"] * sys_df["demand"]).groupby(sys_df["hour"]).sum()
    den = g["demand"].sum()
    m = np.nan_to_num((num / den).reindex(rng).to_numpy(float))
    mdl_dem = _s(g["demand"].sum())

    ch = _sidecar("class_hourly", year)
    wind = _s(ch[ch["klass"] == "wind"].groupby("hour")["mw"].sum())
    solar = _s(ch[ch["klass"] == "solar"].groupby("hour")["mw"].sum())

    st = _sidecar("storage", year).groupby("hour")
    dis = _s(st["discharge_mw"].sum())

    ad = _sidecar("adaptive", year).set_index("hour").reindex(rng)
    floor_usd = np.nan_to_num(ad["floor_usd"].to_numpy(float))
    p_hat = np.nan_to_num(ad["p_hat_day"].to_numpy(float))

    rf = _sidecar("reserve_family", year)
    rf = rf[rf["family"].isin(FAMILIES)]
    fam_dual = _s(rf.groupby("hour")["dual"].max())
    tot = rf[rf["family"] == "ercot_ordc_total"]
    tot_short = _s(tot.groupby("hour")["shortfall_mw"].max())

    a_df = pd.read_parquet(ACTUALS)
    a = a_df[a_df["year"] == year].sort_values("hour")["rt"].to_numpy(float)[:8760]

    eia = _eia_year(year)
    act_nl = (
        eia["Demand"].to_numpy(float)
        - np.nan_to_num(eia["NG: WND"].to_numpy(float))
        - np.nan_to_num(eia["NG: SUN"].to_numpy(float))
    )
    act_d = eia["Demand"].to_numpy(float)
    mdl_nl = mdl_dem - wind - solar

    lags = {}
    for lag in (-1, 0, 1):
        x, y_ = mdl_dem[3:-3], act_d[3 + lag : 8757 + lag]
        ok = np.isfinite(x) & np.isfinite(y_)
        lags[lag] = float(np.corrcoef(x[ok], y_[ok])[0, 1])
    assert max(lags, key=lags.get) == 0, f"alignment FAIL {year}: {lags}"

    mo = pd.read_parquet(str(MEASURED_ORDC).format(year=year)).sort_values("hour")
    return {
        "m": m, "a": a, "dis": dis, "floor": floor_usd, "p_hat": p_hat,
        "fam_dual": fam_dual, "tot_short": tot_short,
        "mdl_nl": mdl_nl, "act_nl": act_nl, "lags": lags,
        "rtorpa": mo["rtorpa"].to_numpy(float)[:8760],
        "rtordpa": mo["rtordpa"].to_numpy(float)[:8760],
    }


def _v0(s24: dict[str, np.ndarray]) -> dict[str, float]:
    """Precommit section 1: the committed ercot-239 h3068 record reproduces."""
    H = 3068
    assert abs(s24["m"][H] - 798.20) <= 0.05, f"V-0 FAIL model {s24['m'][H]:.2f}"
    assert abs(s24["a"][H] - 110.41) <= 0.05, f"V-0 FAIL actual {s24['a'][H]:.2f}"
    assert abs(s24["floor"][H] - 523.12) <= 0.01, f"V-0 FAIL floor {s24['floor'][H]:.2f}"
    assert s24["dis"][H] <= 0.5, f"V-0 FAIL dis3068 {s24['dis'][H]:.1f}"
    assert s24["dis"][3069] >= 1000.0, f"V-0 FAIL dis3069 {s24['dis'][3069]:.1f}"
    # Floor identity: floor = p_hat x VOLL at the held window hour.
    assert abs(s24["p_hat"][H] * VOLL - s24["floor"][H]) <= 0.01, "V-0 FAIL VOLL identity"
    return {
        "model_h3068": round(float(s24["m"][H]), 2),
        "actual_h3068": round(float(s24["a"][H]), 2),
        "floor_h3068": round(float(s24["floor"][H]), 2),
    }


def _hour_row(s: dict[str, np.ndarray], year: int, h: int) -> dict:
    return {
        "year": year, "h": h, "hod": h % 24,
        "model_lw": round(float(s["m"][h]), 2),
        "actual_rt": round(float(s["a"][h]), 2),
        "actual_prev6_max": round(float(s["a"][max(0, h - 6) : h].max()), 2),
        "floor_usd": round(float(s["floor"][h]), 2),
        "fam_dual_max": round(float(s["fam_dual"][h]), 2),
        "ordc_total_short": round(float(s["tot_short"][h]), 1),
        "storage_dis": round(float(s["dis"][h]), 1),
        "storage_dis_next2": [
            round(float(s["dis"][k]), 1) for k in (h + 1, h + 2) if k < 8760
        ],
        "model_next2": [round(float(s["m"][k]), 2) for k in (h + 1, h + 2) if k < 8760],
        "netload_gap": round(float(s["mdl_nl"][h] - s["act_nl"][h]), 0),
        "rtorpa": round(float(s["rtorpa"][h]), 2),
        "rtordpa": round(float(s["rtordpa"][h]), 2),
    }


def main() -> None:
    series = {y: _series_for_year(y) for y in YEARS}
    v0 = _v0(series[2024])

    population, s1_ext, s2_nonguard, s3_already = [], [], [], []
    trailing, floored_counts = [], {}

    for year in YEARS:
        s = series[year]
        m, a = s["m"], s["a"]
        hod = np.arange(8760) % 24
        in_win = np.isin(hod, WINDOW_HODS)
        floored = in_win & (s["floor"] >= 10.0)
        released = in_win & (s["floor"] == 0.0) & (s["p_hat"] * VOLL >= 10.0)
        floored_counts[year] = {
            "floored_window_hours": int(floored.sum()),
            "guard_released_window_hours": int(released.sum()),
        }

        # Trailing set: floored window hours after the day's first release.
        for d in np.unique(np.where(released)[0] // 24):
            day_h = np.arange(d * 24, min((d + 1) * 24, 8760))
            rel_h = day_h[released[day_h]]
            first_rel = int(rel_h.min())
            for h in day_h[floored[day_h]]:
                if h > first_rel:
                    row = _hour_row(s, year, int(h))
                    row["day_released_hods"] = [int(x % 24) for x in rel_h]
                    row["classification"] = (
                        "release-RIGHT" if a[h] < 200.0 else "release-WRONG"
                    )
                    trailing.append(row)

        for h in range(1, 8760):
            # A1-A3: first collapsed hour after a real event.
            if not (a[h] < 200.0 and a[h - 1] >= 200.0 and a[max(0, h - 6) : h].max() >= 500.0):
                continue
            row = _hour_row(s, year, h)
            m1 = m[h] >= 200.0 and (s["fam_dual"][h] >= 100.0 or s["tot_short"][h] > 0.0)
            if m[h] < 200.0:
                s3_already.append(row)
                continue
            if not m1:
                continue  # model above census line without reserve steps: not an event hold
            m5 = abs(s["mdl_nl"][h] - s["act_nl"][h]) <= 2500.0
            m6 = s["rtorpa"][h] < 50.0 and s["rtordpa"][h] < 50.0
            if not (m5 and m6):
                row["failed"] = [k for k, v in (("M5", m5), ("M6", m6)) if not v]
                s2_nonguard.append(row) if s["floor"][h] < 10.0 else s1_ext.append(row)
                continue
            if s["floor"][h] < 10.0:
                s2_nonguard.append(row)
                continue
            m3 = s["dis"][h] <= 100.0 and max(
                (s["dis"][k] for k in (h + 1, h + 2) if k < 8760), default=0.0
            ) >= 300.0
            m4 = min((m[k] for k in (h + 1, h + 2) if k < 8760), default=np.inf) < 200.0
            if m3 and m4:
                population.append(row)
            else:
                row["failed"] = [k for k, v in (("M3", m3), ("M4", m4)) if not v]
                s1_ext.append(row)

    pop_keys = {(r["year"], r["h"]) for r in population}
    trail_keys = {(r["year"], r["h"]) for r in trailing}
    n_wrong = sum(1 for r in trailing if r["classification"] == "release-WRONG")
    t1 = pop_keys <= trail_keys
    t2 = n_wrong == 0

    kills = {
        "K1_population_h3068_alone_or_empty": pop_keys <= {(2024, 3068)},
        "K2_T1_fails": not t1,
        "K3_T2_fails_release_wrong_gt_0": not t2,
        "K4_S2_exceeds_population": len(s2_nonguard) > len(population),
    }
    verdict = (
        "KILL: " + ", ".join(k for k, v in kills.items() if v)
        if any(kills.values())
        else "RE-IDENTIFICATION LICENSED: structural trailing-edge exit condition"
    )

    res = {
        "session": "ercot-243 Phase-0",
        "bundle": "ercot234_eastex_identity (forward keeper)",
        "precommit": "docs/PRECOMMIT-ercot243-release-exit-phase0-2026-08-30.md",
        "v0": v0,
        "alignment_lag_corr": {
            y: {str(k): round(v, 4) for k, v in series[y]["lags"].items()} for y in YEARS
        },
        "floored_counts": floored_counts,
        "population": population,
        "strata": {
            "S1_extended_holds": s1_ext,
            "S2_nonguard_exit_lags": s2_nonguard,
            "S3_model_already_released_count": len(s3_already),
        },
        "trailing_set": trailing,
        "separation": {
            "T1_population_in_trailing_set": t1,
            "T2_release_wrong_zero": t2,
            "n_trailing": len(trailing),
            "n_release_right": len(trailing) - n_wrong,
            "n_release_wrong": n_wrong,
        },
        "prior_check": {
            "declared_population_prior": "1-3 (point 2)",
            "observed": len(population),
            "order_of_magnitude_breach": len(population) >= 10,
        },
        "kills": kills,
        "verdict": verdict,
    }
    OUT_JSON.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in (
        "v0", "floored_counts", "population", "separation", "prior_check", "kills", "verdict"
    )}, indent=1, default=str))
    print(f"S1={len(s1_ext)} S2={len(s2_nonguard)} S3={len(s3_already)}")


if __name__ == "__main__":
    main()
