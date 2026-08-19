"""ercot-221 Phase-0: identify the adaptive-expectation storage offer rule.

Pre-registered in docs/PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md
(pushed + blob-verified before this probe ran). Read-only: no LP, no solve.

Instrument: the daily 2023 STORAGE (PWRSTR) evening offer surface —
MW-weighted p50 of above-LSL, HASL-capped SCED2 segments in h17-20 CST,
telemetered-ONLINE, ONTEST excluded (the ERCOT-154/161 population
discipline, construction copied from the committed ercot-210/218 instrument
and scoped to PWRSTR) — over the committed delivery-2023 corpus
(data/raw/ercot/SCED/). Rule family and gates: precommit §1-§3 verbatim.

Output: results/calibration/ercot221_adaptive_phase0.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data",
           REPO / "scripts" / "probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from derive_ercot_dam_cleared_share import _MONTH_START_HOUR  # noqa: E402
from derive_ercot_sced_offer_wall import (  # noqa: E402
    _SCED2_MW,
    _SCED2_PR,
    _delivery_year_rows,
    _sced_source_files,
    _weighted_quantiles,
)
from ercot155_dispersion_census import ONLINE_STATES  # noqa: E402

OUT = REPO / "results/calibration/ercot221_adaptive_phase0.json"
KEEPER = REPO / "results/calibration/ercot215_decontam_B"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"

# Precommit §1-§2 pinned conventions
VOLL = 5000.0
EVENT_USD = 1000.0        # spike-day threshold
TRAIL_DAYS = 120          # trailing window
WIN_H = (17, 18, 19, 20)  # evening net-peak window, CST hour-beginning
MIN_ROWS_DAY = 40         # day admissibility
ECRS_DOY = 160            # 2023-06-10, non-leap 0-indexed day (hour 3840)
FIT_LO, FIT_HI = ECRS_DOY, 364           # fit span Jun 10 - Dec 31
DECAY_FIT_HI = 272                        # Sep 30 (0-indexed doy 272 = Sep 30)
MSH = np.asarray(_MONTH_START_HOUR, dtype=int)

# committed ercot-218 T1 measured monthly p50s at the >=p98 tightness cut
# (fidelity targets for G-COV, +-10 % where both exist)
T1_MEASURED = {6: 5000.0, 7: 4999.9836, 8: 3361.1218, 9: 4052.4775,
               12: 271.8082}


def month_of_doy(doy: np.ndarray) -> np.ndarray:
    return np.searchsorted(MSH, np.asarray(doy, int) * 24, side="right")


def load_storage_segments(year: int, want_hoy: set[int]) -> pd.DataFrame:
    """PWRSTR above-LSL HASL-capped SCED2 segments at the wanted hours.

    The ercot-210/218 construction (ercot218_direct_driver_phase0.load_segments)
    scoped to PWRSTR, AS columns dropped (not used by this instrument).
    """
    online = set(ONLINE_STATES) | {"ONTEST"}
    base_cols = ["SCED Time Stamp", "Resource Name", "Resource Type",
                 "Telemetered Resource Status", "HASL", "LSL"] + \
        [c for pair in zip(_SCED2_MW, _SCED2_PR) for c in pair]
    out: list[pd.DataFrame] = []
    for p in _sced_source_files(year):
        import pyarrow.parquet as _pq
        have = set(_pq.ParquetFile(p).schema_arrow.names)
        df = pd.read_parquet(p, columns=[c for c in base_cols if c in have])
        df = _delivery_year_rows(df, year)
        if df.empty:
            continue
        df = df[df["Resource Type"] == "PWRSTR"]
        if df.empty:
            continue
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = df[stat.isin(online)].assign(status=stat[stat.isin(online)])
        if df.empty:
            continue
        ts = pd.to_datetime(df["SCED Time Stamp"],
                            format="%m/%d/%Y %H:%M:%S", errors="coerce")
        df, ts = df[ts.notna()], ts[ts.notna()]
        if df.empty:
            continue
        cst = (ts.dt.tz_localize("America/Chicago", ambiguous=True,
                                 nonexistent="shift_forward")
                 .dt.tz_convert("Etc/GMT+6"))
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        if not ok.any():
            continue
        df = df.loc[np.asarray(ok)].copy()
        hoy = MSH[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        sel = np.isin(hoy, list(want_hoy))
        if not sel.any():
            continue
        df = df.loc[sel].copy()
        df["hoy"] = hoy[sel]
        num = _SCED2_MW + _SCED2_PR + ["HASL", "LSL"]
        df[num] = df[num].apply(pd.to_numeric, errors="coerce")
        MW = df[_SCED2_MW].to_numpy(float)
        PR = df[_SCED2_PR].to_numpy(float)
        lsl = np.maximum(df["LSL"].to_numpy(float), 0.0)
        hasl = df["HASL"].to_numpy(float)
        acc_h, acc_m, acc_p, acc_s = [], [], [], []
        prev = lsl.copy()
        for k in range(MW.shape[1]):
            q, pr = MW[:, k], PR[:, k]
            valid = np.isfinite(q) & np.isfinite(pr)
            cap = np.minimum(q, hasl)
            seg = np.where(valid,
                           np.maximum(cap - np.maximum(prev, lsl), 0.0), 0.0)
            take = seg > 0
            if take.any():
                acc_h.append(df["hoy"].to_numpy()[take])
                acc_m.append(seg[take])
                acc_p.append(pr[take])
                acc_s.append(df["status"].to_numpy()[take])
            prev = np.where(valid, np.maximum(prev, q), prev)
        if acc_m:
            out.append(pd.DataFrame({
                "hoy": np.concatenate(acc_h), "mw": np.concatenate(acc_m),
                "price": np.concatenate(acc_p),
                "status": np.concatenate(acc_s)}))
    if not out:
        return pd.DataFrame(columns=["hoy", "mw", "price", "status"])
    seg = pd.concat(out, ignore_index=True)
    return seg[seg["status"] != "ONTEST"].reset_index(drop=True)


def p_trail(S: np.ndarray, half_life: float) -> np.ndarray:
    """Normalized trailing-EWMA of the spike indicator, strictly lagged."""
    n = S.size
    w = 0.5 ** (np.arange(1, TRAIL_DAYS + 1) / half_life)
    out = np.zeros(n)
    for d in range(n):
        k = min(d, TRAIL_DAYS)
        if k:
            out[d] = float((w[:k] * S[d - 1::-1][:k]).sum() / w[:k].sum())
    return out


def p_prior(n: int, tau0: float, has_golive: bool) -> np.ndarray:
    d = np.arange(n, dtype=float)
    if not has_golive:
        return np.zeros(n)
    x = np.where(d >= ECRS_DOY, np.exp(-(d - ECRS_DOY) / tau0), 0.0)
    return x


def fit_rule(days: np.ndarray, y: np.ndarray, S: np.ndarray,
             lo: int, hi: int) -> dict:
    """Grid over (half-life, tau0); OLS in (beta, P0), clipped nonnegative."""
    best = None
    sel = (days >= lo) & (days <= hi)
    for hl in (10.0, 15.0, 20.0, 30.0, 45.0, 60.0, 90.0):
        pt_all = p_trail(S, hl)
        for tau in (10.0, 15.0, 20.0, 30.0, 45.0, 60.0):
            pp_all = p_prior(365, tau, True)
            X = np.column_stack([pt_all[days[sel]], pp_all[days[sel]]])
            yy = y[sel]
            coef, *_ = np.linalg.lstsq(X, yy, rcond=None)
            beta, P0 = float(max(coef[0], 0.0)), float(min(max(coef[1], 0.0), 1.5))
            pred = np.clip(X @ np.array([beta, P0]), 0.0, 1.0)
            sse = float(((pred - yy) ** 2).sum())
            if best is None or sse < best["sse"]:
                best = dict(half_life=hl, tau0=tau, beta=beta, P0=P0, sse=sse)
    return best


def p_hat(S: np.ndarray, c: dict, has_golive: bool) -> np.ndarray:
    return np.clip(c["beta"] * p_trail(S, c["half_life"])
                   + c["P0"] * p_prior(S.size, c["tau0"], has_golive),
                   0.0, 1.0)


def keeper_path(year: int) -> np.ndarray:
    s = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    num = (s["price"] * s["demand"]).groupby(s["hour"]).sum()
    den = s.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(8760)).to_numpy(float)


def daily_max(hourly: np.ndarray) -> np.ndarray:
    return np.nanmax(hourly[: 365 * 24].reshape(365, 24), axis=1)


SURFACE_CACHE = REPO / "results/calibration/ercot221_daily_surface_2023.json"


def build_surface() -> dict:
    """Corpus scan -> daily surface + fidelity table, cached to disk."""
    if SURFACE_CACHE.exists():
        return json.loads(SURFACE_CACHE.read_text())
    want = {int(d * 24 + h) for d in range(365) for h in WIN_H}
    drv = pd.read_parquet(
        REPO / "data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet",
        columns=["hour", "prc"])
    prc = drv.sort_values("hour")["prc"].to_numpy(float)[:8760]
    tight = 1.0 - pd.Series(prc).rank(pct=True).to_numpy()
    p98_hours = set(np.where(tight >= np.nanquantile(tight, 0.98))[0].tolist())
    seg = load_storage_segments(2023, want | p98_hours)

    ev = seg[np.isin(seg["hoy"].to_numpy() % 24, WIN_H)].copy()
    ev["doy"] = ev["hoy"] // 24
    daily = {}
    for d, g in ev.groupby("doy"):
        if len(g) >= MIN_ROWS_DAY:
            daily[int(d)] = float(_weighted_quantiles(
                g["price"].to_numpy(float), g["mw"].to_numpy(float), [0.5])[0])

    fid = {}
    p98seg = seg[np.isin(seg["hoy"].to_numpy(), list(p98_hours))]
    for m, target in T1_MEASURED.items():
        rows = p98seg[month_of_doy(p98seg["hoy"] // 24) == m]
        if len(rows):
            got = float(_weighted_quantiles(
                rows["price"].to_numpy(float), rows["mw"].to_numpy(float),
                [0.5])[0])
            fid[m] = dict(measured_committed=target, reproduced=round(got, 1),
                          rel_err=round(got / target - 1, 4))
    out = {"daily": {str(k): v for k, v in daily.items()}, "fidelity": fid}
    SURFACE_CACHE.write_text(json.dumps(out, indent=1))
    return out


def main() -> None:
    surf = build_surface()
    daily = {int(k): float(v) for k, v in surf["daily"].items()}
    fid = {int(k): v for k, v in surf["fidelity"].items()}
    days = np.array(sorted(daily), int)
    y = np.array([daily[d] for d in days]) / VOLL   # implied P

    # measured spike days
    lmp = pd.read_parquet(ACTUAL)
    a23 = lmp[lmp["year"] == 2023].sort_values("hour")["rt"].to_numpy(float)[:8760]
    S = (daily_max(a23) >= EVENT_USD).astype(float)

    # --- fit (full span) and gates
    fit = fit_rule(days, y, S, FIT_LO, FIT_HI)
    sel = (days >= FIT_LO) & (days <= FIT_HI)
    ph = p_hat(S, fit, True)
    pred = ph[days[sel]]
    corr = float(np.corrcoef(pred, y[sel])[0, 1])

    months = month_of_doy(days)
    monthly = {}
    for m in range(6, 13):
        msel = sel & (months == m)
        if msel.sum() >= 10:
            mo_meas = float(np.median(y[msel]) * VOLL)
            mo_pred = float(np.median(ph[days[msel]]) * VOLL)
            monthly[m] = dict(n_days=int(msel.sum()),
                              measured_p50=round(mo_meas, 1),
                              predicted=round(mo_pred, 1),
                              rel_err=round(mo_pred / mo_meas - 1, 4),
                              in_band=bool(abs(mo_pred / mo_meas - 1) <= 0.35))
    n_adm = len(monthly)
    n_band = sum(v["in_band"] for v in monthly.values())

    # G-DECAY: fit Jun10-Sep30 only -> predict Oct/Nov/Dec
    fit_early = fit_rule(days, y, S, FIT_LO, DECAY_FIT_HI)
    ph_e = p_hat(S, fit_early, True)
    decay = {}
    for m in (10, 11, 12):
        msel = (days > DECAY_FIT_HI) & (months == m)
        if msel.sum() >= 5:
            mo_meas = float(np.median(y[msel]) * VOLL)
            mo_pred = float(np.median(ph_e[days[msel]]) * VOLL)
            decay[m] = dict(n_days=int(msel.sum()),
                            measured_p50=round(mo_meas, 1),
                            predicted=round(mo_pred, 1),
                            rel_err=round(mo_pred / mo_meas - 1, 4),
                            in_band=bool(abs(mo_pred / mo_meas - 1) <= 0.50))
    # beta=0 ablation (prior only) must fail the corr leg
    best_ab = None
    for tau in (10.0, 15.0, 20.0, 30.0, 45.0, 60.0):
        pp = p_prior(365, tau, True)[days[sel]]
        coef = float((pp @ y[sel]) / (pp @ pp)) if (pp @ pp) > 0 else 0.0
        predab = np.clip(coef * pp, 0, 1)
        c = float(np.corrcoef(predab, y[sel])[0, 1]) if predab.std() > 0 else 0.0
        if best_ab is None or c > best_ab:
            best_ab = c

    # G-SAFE / G-BOOT on the keeper's own model paths
    safe = {}
    for yr in (2024, 2025):
        Sm = (daily_max(keeper_path(yr)) >= EVENT_USD).astype(float)
        phm = p_hat(Sm, fit, False)     # no go-live prior outside 2023
        floors = phm * VOLL
        safe[yr] = dict(model_spike_days=int(Sm.sum()),
                        share_hours_floor_le_110=round(
                            float((floors <= 110.0).mean()), 4),
                        max_floor=round(float(floors.max()), 1))
    Sm23 = (daily_max(keeper_path(2023)) >= EVENT_USD).astype(float)
    phm23 = p_hat(Sm23, fit, True)
    aug1, sep30 = 212, 272
    boot_mean = float(np.mean(phm23[aug1:sep30 + 1]) * VOLL)

    gates_v1 = {
        "G-COV": dict(admissible_days=int(len(days)),
                      bar=">=300", fidelity=fid,
                      ok=bool(len(days) >= 300 and all(
                          abs(v["rel_err"]) <= 0.10 for v in fid.values()))),
        "G-ID": dict(daily_corr=round(corr, 4),
                     monthly=monthly, n_admissible=n_adm, n_in_band=n_band,
                     ok=bool(corr >= 0.6 and n_band >= 4)),
        "G-DECAY": dict(fit_early=fit_early, folds=decay,
                        prior_only_best_corr=round(best_ab, 4),
                        ok=bool(decay and all(v["in_band"]
                                              for v in decay.values())
                                and best_ab < 0.6)),
        "G-SAFE": dict(years={str(k): v for k, v in safe.items()},
                       ok=bool(all(v["share_hours_floor_le_110"] >= 0.95
                                   for v in safe.values()))),
        "G-BOOT": dict(model_spike_days_2023=int(Sm23.sum()),
                       aug_sep_mean_floor=round(boot_mean, 1), bar=750.0,
                       ok=bool(boot_mean >= 750.0)),
    }
    gates_v1["ALL_PASS"] = bool(all(g["ok"] for k, g in gates_v1.items()
                                    if isinstance(g, dict)))

    # ------------------------------------------------------------------
    # FAMILY v2 (precommit Amendment 1, pushed before this fit): the prior
    # term retired, two identified constants (half_life, beta); comparison
    # prediction max(beta*P_trail*VOLL, base), base = the measured pre-go-live
    # standing evening ask (median daily p50, Jan 1 - Jun 9 — disjoint window).
    # ------------------------------------------------------------------
    pre = (days < FIT_LO)
    base = float(np.median(y[pre]) * VOLL) if pre.any() else 0.0

    best2 = None
    for hl in (5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 45.0):
        pt = p_trail(S, hl)
        x = pt[days[sel]]
        beta = float(max((x @ y[sel]) / (x @ x), 0.0)) if (x @ x) > 0 else 0.0
        predv = np.maximum(np.clip(beta * x, 0.0, 1.0) * VOLL, base) / VOLL
        sse = float(((predv - y[sel]) ** 2).sum())
        if best2 is None or sse < best2["sse"]:
            best2 = dict(half_life=hl, beta=beta, sse=sse)
    fit2 = best2

    def v2_pred(S_arr: np.ndarray, hl: float, beta: float,
                with_base: bool) -> np.ndarray:
        raw = np.clip(beta * p_trail(S_arr, hl), 0.0, 1.0) * VOLL
        return np.maximum(raw, base) if with_base else raw

    pv2 = v2_pred(S, fit2["half_life"], fit2["beta"], True)
    corr2 = float(np.corrcoef(pv2[days[sel]] / VOLL, y[sel])[0, 1])
    monthly2 = {}
    for m in range(6, 13):
        msel = sel & (months == m)
        if msel.sum() >= 10:
            mo_meas = float(np.median(y[msel]) * VOLL)
            mo_pred = float(np.median(pv2[days[msel]]))
            monthly2[m] = dict(n_days=int(msel.sum()),
                               measured_p50=round(mo_meas, 1),
                               predicted=round(mo_pred, 1),
                               rel_err=round(mo_pred / mo_meas - 1, 4),
                               in_band=bool(abs(mo_pred / mo_meas - 1) <= 0.35))
    n_band2 = sum(v["in_band"] for v in monthly2.values())

    # G-DECAY v2: refit on Jun10-Sep30 only, predict Oct/Nov/Dec
    sel_e = (days >= FIT_LO) & (days <= DECAY_FIT_HI)
    best2e = None
    for hl in (5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 45.0):
        pt = p_trail(S, hl)
        x = pt[days[sel_e]]
        beta = float(max((x @ y[sel_e]) / (x @ x), 0.0)) if (x @ x) > 0 else 0.0
        predv = np.maximum(np.clip(beta * x, 0, 1) * VOLL, base) / VOLL
        sse = float(((predv - y[sel_e]) ** 2).sum())
        if best2e is None or sse < best2e["sse"]:
            best2e = dict(half_life=hl, beta=beta, sse=sse)
    pv2e = v2_pred(S, best2e["half_life"], best2e["beta"], True)
    decay2 = {}
    for m in (10, 11, 12):
        msel = (days > DECAY_FIT_HI) & (months == m)
        if msel.sum() >= 5:
            mo_meas = float(np.median(y[msel]) * VOLL)
            mo_pred = float(np.median(pv2e[days[msel]]))
            decay2[m] = dict(n_days=int(msel.sum()),
                             measured_p50=round(mo_meas, 1),
                             predicted=round(mo_pred, 1),
                             rel_err=round(mo_pred / mo_meas - 1, 4),
                             in_band=bool(abs(mo_pred / mo_meas - 1) <= 0.50))

    # G-SAFE v2 on the mechanism's ACTUAL windowed floor schedule (armed
    # floor carries NO base term); vom proxy <= $10 -> bar floor <= $110.
    safe2 = {}
    for yr in (2024, 2025):
        Sm = (daily_max(keeper_path(yr)) >= EVENT_USD).astype(float)
        fl_day = v2_pred(Sm, fit2["half_life"], fit2["beta"], False)  # per day
        hourly_floor = np.full(8760, 10.0)
        for h in WIN_H:
            hourly_floor[np.arange(365) * 24 + h] = np.maximum(
                fl_day, 10.0)
        safe2[str(yr)] = dict(
            model_spike_days=int(Sm.sum()),
            share_hours_floor_le_110=round(
                float((hourly_floor <= 110.0).mean()), 4),
            max_floor=round(float(hourly_floor.max()), 1))
    fl23 = v2_pred(Sm23, fit2["half_life"], fit2["beta"], False)
    boot2 = float(np.mean(fl23[aug1:sep30 + 1]))

    gates_v2 = {
        "G-COV": dict(admissible_days=int(len(days)), bar=">=300",
                      fidelity_flat_months={m: fid[m] for m in (6, 7, 12)
                                            if m in fid},
                      aug_sep_population_mismatch_disclosed=True,
                      ok=bool(len(days) >= 300 and all(
                          abs(fid[m]["rel_err"]) <= 0.01
                          for m in (6, 7, 12) if m in fid))),
        "G-ID": dict(daily_corr=round(corr2, 4), base_usd=round(base, 1),
                     monthly=monthly2, n_admissible=len(monthly2),
                     n_in_band=n_band2,
                     ok=bool(corr2 >= 0.6 and n_band2 >= 4)),
        "G-DECAY": dict(fit_early=best2e, folds=decay2,
                        prior_only_best_corr=round(best_ab, 4),
                        ok=bool(decay2 and all(v["in_band"]
                                               for v in decay2.values())
                                and best_ab < 0.6)),
        "G-SAFE": dict(years=safe2,
                       ok=bool(all(v["share_hours_floor_le_110"] >= 0.95
                                   for v in safe2.values()))),
        "G-BOOT": dict(model_spike_days_2023=int(Sm23.sum()),
                       aug_sep_mean_floor=round(boot2, 1), bar=750.0,
                       ok=bool(boot2 >= 750.0)),
    }
    gates_v2["ALL_PASS"] = bool(all(g["ok"] for k, g in gates_v2.items()
                                    if isinstance(g, dict)))

    out = {
        "probe": "ercot221_adaptive_phase0", "date": "2026-08-18",
        "precommit": "docs/PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md",
        "daily_surface_n_days": int(len(days)),
        "measured_spike_days_2023": int(S.sum()),
        "daily_monthly_measured_p50": {
            str(m): round(float(np.median(
                y[(months == m)]) * VOLL), 1)
            for m in range(1, 13) if (months == m).sum() >= 10},
        "v1": {"fitted_constants": fit, "gates": gates_v1},
        "v2": {"fitted_constants": fit2, "base_usd": round(base, 1),
               "gates": gates_v2},
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
