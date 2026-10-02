"""PJM close-out E0 (zero-LP): cold-correlated forced-outage curve, Elliott residual.

Executes phase 0 (steps E0a-E0e) of
``docs/records/pjm/PRECOMMIT-pjm-closeout-elliott-cold-outage-2026-10-02.md``.
Reads committed artifacts and raw data only; never solves; edits nothing in
``src/`` and does not touch ``scripts/data/derive_correlated_outage_curve.py``
-- that script's ERCOT method is REPRODUCED here for PJM.

Method (the ERCOT derive, transposed)
-------------------------------------
* TMIN_sys: PJM system daily minimum temperature = load-weighted mean of
  ``tmin_c`` over the eight model zones (``data/raw/pjm-weather/
  pjm_zone_temp_daily*.csv``). Weights = the static zone ``load_share`` in
  ``config/iso_configs.py`` (PJM 2023 hourly metered load; no per-year zonal
  load on disk). Plain mean is computed alongside for comparison.
* Cold windows: maximal runs of days with TMIN_sys <= T0 = -7 degC, gaps <= 2 d,
  2018-2025.
* In-merit certificate: a window day (or the +1 recovery day) whose daily-max
  EIA-930 PJM net load (Demand - NG:WND - NG:SUN, ``data/raw/eia-930-hourly/
  PJM hourly.parquet``; ``PJM_region.parquet`` only covers 2023+) is >= that
  year's hourly 99th percentile.
* Instrument: per class, best-mustered hour of the CAMPD gross load
  (``data/raw/campd-unit-level/<ST>_<y>.parquet``) / class capacity, at the
  window's coldest day. Excess = clip((1 - EFORd) - bestfrac, 0, 1).
  Classes: COAL (COAL_BIT+COAL_WC+COAL_PRB pooled, as the ERCOT curve is one
  coal curve carried to every subclass), CC_REGULAR, CT_PEAKER, ST_GAS.
  CHP, nuclear, oil (blank plant_group), hydro, imports excluded.
* Class membership: keeper ``results/calibration/pjmnext16_A_span/hourly/
  unit_marginal_<y>.parquet`` plant_code -> plant_group. Plants carrying more
  than one class split CAMPD units by CAMPD unitType/fuel. Capacity = per-unit
  max ``cap_mw`` over the year (keeper pmax proxy; pmax not in the sidecar),
  restricted for the instrument to (plant, class) pairs with a CAMPD trace.
* Fit: single era (pooled 2018-2025; no PJM winterization break is chartered),
  through-origin LS slope on one point per certified window, cap = max excess.

Residual (backcast form, PRECOMMIT section 2)
---------------------------------------------
Per class-day: curve MW = sum_units min(excess(T) * pmax_proxy, daily-mean
cap_mw); overlay MW = max(0, class sum cap_mw pre-window baseline (mean of the
3 days before the window) - class sum cap_mw that day); residual =
max(0, curve - overlay). Clock = 0b's (row = doy0*24 + HE - 1, DST nets out
outside Mar-Nov).

Run: ``python scripts/probes/_pjmco_e0_elliott_phase0.py``
Writes ``results/phase0/pjm/_pjmco_e0_elliott_phase0.json`` plus
``_pjmco_e0_footprint.csv`` and ``_pjmco_e0_headroom_hourly.csv``.
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.constants import EFORD  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext16_A_span/hourly"
CAMPD = REPO / "data/raw/campd-unit-level"
OUT = REPO / "results/phase0/pjm"
T0_C = -7.0
CERT_PCTL = 0.99
FIRST, LAST = 2018, 2025
KEEPER_YEARS = range(2019, 2026)
PJM_STATES = ("DC", "DE", "IL", "IN", "KY", "MD", "MI", "NC", "NJ", "OH", "PA", "TN", "VA", "WV")
CLASS_EFORD = {"COAL": "coal", "CC_REGULAR": "gas_cc", "CT_PEAKER": "gas_ct", "ST_GAS": "gas_st"}
COAL_SUB = ("COAL_BIT", "COAL_WC", "COAL_PRB", "COAL_LIGNITE")
ELLIOTT = ("2022-12-20", "2023-01-05")
LOO_TOL = 0.30
E0D_BAND = (0.7, 1.3)


def fit_class(k: str) -> str | None:
    """Model plant_group -> fit class (None = excluded)."""
    if k in COAL_SUB:
        return "COAL"
    return k if k in CLASS_EFORD else None


def tmin_sys() -> tuple[pd.Series, pd.Series, str]:
    """(load-weighted TMIN_sys, plain-mean TMIN_sys, weight description)."""
    w = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(str(REPO / "data/raw/pjm-weather/pjm_zone_temp_daily*.csv")))])
    w["date"] = pd.to_datetime(w.date)
    w = w.drop_duplicates(["date", "zone"]).dropna(subset=["tmin_c"])
    share = {z.name: z.load_share for z in get_iso_config("PJM").zones}
    w["wt"] = w.zone.map(share)
    lw = (w.tmin_c * w.wt).groupby(w.date).sum() / w.wt.groupby(w.date).sum()
    return lw.sort_index(), w.groupby("date").tmin_c.mean().sort_index(), json.dumps(share)


def certified_days() -> tuple[pd.Series, pd.Series, pd.Series]:
    """(bool per day, daily max net load, per-year p99) from EIA-930 PJM."""
    e = pd.read_parquet(REPO / "data/raw/eia-930-hourly/PJM hourly.parquet")
    e["date"] = pd.to_datetime(e["Local date"])
    e["net"] = pd.to_numeric(e.Demand, errors="coerce") - pd.to_numeric(e["NG: WND"], errors="coerce").fillna(0) - pd.to_numeric(e["NG: SUN"], errors="coerce").fillna(0)
    dmax = e.groupby("date").net.max()
    p = e.groupby(e.date.dt.year).net.quantile(CERT_PCTL)
    return dmax >= dmax.index.year.map(p), dmax, p


def cold_windows(t: pd.Series) -> list[pd.DatetimeIndex]:
    """Maximal runs (gaps <= 2 d) of days with TMIN_sys <= T0 in FIRST..LAST."""
    d = t[(t <= T0_C) & (t.index >= f"{FIRST}-01-01") & (t.index < f"{LAST + 1}-01-01")].index.sort_values()
    out, cur = [], [d[0]]
    for x in d[1:]:
        if (x - cur[-1]).days <= 2:
            cur.append(x)
        else:
            out.append(cur)
            cur = [x]
    out.append(cur)
    return [pd.DatetimeIndex(w) for w in out]


_YD: dict[int, dict] = {}


def year_data(y: int) -> dict:
    """Compact per-year keeper view (memory-bounded; raw frame dropped).

    Keys: ``ut`` unit table (plant_code, class k, fit class fc, pmax proxy =
    max cap_mw), ``capd`` unit x day mean cap_mw, ``kday`` day x class sum of
    daily-mean cap_mw, and for 2022 ``h22`` hourly cap/mw sums (all units) and
    ``th22`` hourly thermal cap sums.
    """
    if y in _YD:
        return _YD[y]
    x = pd.read_parquet(BUNDLE / f"unit_marginal_{y}.parquet", columns=["unit_id", "plant_group", "plant_code", "fuel", "hour", "mw", "cap_mw"])
    k = x.plant_group.astype(str)
    blank = k == ""
    k[blank] = x.fuel.astype(str)[blank]
    keep = ~k.str.startswith("VIRTUAL")
    x = x[keep]
    k = k[keep]
    uid = x.unit_id.astype(str).to_numpy()
    codes, inv = np.unique(uid, return_inverse=True)
    hrs = x.hour.to_numpy()
    nh = int(hrs.max()) + 1
    cap = np.zeros((len(codes), nh), dtype=np.float32)
    cap[inv, hrs] = x.cap_mw.to_numpy()
    first = pd.Series(np.arange(len(uid))).groupby(inv).first().to_numpy()
    ut = pd.DataFrame({"plant_code": x.plant_code.to_numpy()[first], "k": k.to_numpy()[first], "pmax": cap.max(axis=1)}, index=codes)
    ut["fc"] = ut.k.map(fit_class)
    nd = nh // 24
    capd = cap[:, : nd * 24].reshape(len(codes), nd, 24).mean(axis=2)
    kday = pd.DataFrame(capd, index=codes).groupby(ut.k.to_numpy()).sum().T
    d = {"ut": ut, "capd": pd.DataFrame(capd, index=codes), "kday": kday}
    if y == 2022:
        mw = np.zeros_like(cap)
        mw[inv, hrs] = x.mw.to_numpy()
        d["h22"] = pd.DataFrame({"cap": cap.sum(axis=0), "mw": mw.sum(axis=0)})
        th = ~ut.k.isin(["import", "hydro"]).to_numpy()
        d["th22"] = pd.Series(cap[th].sum(axis=0))
        d["th22_pmax"] = float(ut.pmax[th].sum())
        del mw
    del x, cap
    _YD[y] = d
    return d


def unit_table(y: int) -> pd.DataFrame:
    """Per unit: plant_code, class k, fit class, pmax proxy (max cap_mw)."""
    return year_data(y)["ut"]


_CAMPD: dict[int, pd.DataFrame] = {}


def campd_type_class(unit_type: str, fuel: str) -> str:
    """CAMPD unitType/primaryFuel -> fit class (multi-class plants only)."""
    ut, fu = str(unit_type).lower(), str(fuel).lower()
    if "coal" in fu:
        return "COAL"
    if "combined cycle" in ut or "combined" in ut:
        return "CC_REGULAR"
    if "turbine" in ut:
        return "CT_PEAKER"
    return "ST_GAS"


def campd_class_hourly(y: int) -> tuple[pd.DataFrame, dict]:
    """Whole-year CAMPD gross load summed per (fit class, date, hour) + instrument capacity."""
    if y in _CAMPD:
        return _CAMPD[y]
    ut = unit_table(y)
    ut = ut[ut.fc.notna()]
    pc = ut.groupby(["plant_code", "fc"]).pmax.sum().reset_index()
    groups = pc.groupby("plant_code").fc.apply(set)
    parts, present = [], set()
    for st in PJM_STATES:
        f = CAMPD / f"{st}_{y}.parquet"
        if not f.exists():
            continue
        c = pd.read_parquet(f, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType", "primaryFuelInfo"])
        c["fid"] = pd.to_numeric(c.facilityId, errors="coerce")
        c = c[c.fid.isin(groups.index)]
        uu = c.drop_duplicates(["fid", "unitId"])
        cls = {}
        for r in uu.itertuples():
            g = groups[r.fid]
            if len(g) == 1:
                k = next(iter(g))
            else:
                k = campd_type_class(r.unitType, r.primaryFuelInfo)
                if k not in g:
                    k = max(g, key=lambda q: float(pc[(pc.plant_code == r.fid) & (pc.fc == q)].pmax.iloc[0]))
            cls[(r.fid, r.unitId)] = k
            present.add((r.fid, k))
        c["fc"] = [cls[(a_, b_)] for a_, b_ in zip(c.fid, c.unitId)]
        c["g"] = pd.to_numeric(c.grossLoad, errors="coerce").fillna(0.0)
        parts.append(c.groupby(["fc", "date", "hour"]).g.sum())
        del c
    hr = pd.concat(parts).groupby(level=[0, 1, 2]).sum().reset_index()
    capi = pc[[(p_, k_) in present for p_, k_ in zip(pc.plant_code, pc.fc)]].groupby("fc").pmax.sum()
    hr["frac"] = hr.g / hr.fc.map(capi)
    _CAMPD[y] = (hr, capi.to_dict())
    return _CAMPD[y]


def bestfrac(y: int, days: pd.DatetimeIndex) -> tuple[dict, dict]:
    """Per (class, day) best-mustered-hour fraction; plus instrument capacity."""
    hr, capi = campd_class_hourly(y)
    hr = hr[hr.date.isin(days)]
    out = hr.groupby(["fc", "date"]).frac.max()
    return {(k, pd.Timestamp(d)): float(v) for (k, d), v in out.items()}, capi


def fit(points: dict) -> dict:
    """Through-origin hinge slope and cap per class."""
    res = {}
    for k, p in points.items():
        x = np.array([T0_C - t for t, _, _ in p])
        yv = np.array([e for _, e, _ in p])
        s = float((x * yv).sum() / (x * x).sum()) if (x * x).sum() > 0 else 0.0
        res[k] = {"slope_per_c": round(s, 4), "cap": round(float(yv.max()), 3), "n_windows": len(p), "anchors": [d for _, _, d in p]}
    return res


def curve_frac(curve: dict, k: str, t: float) -> float:
    """Excess fraction of fit class k at TMIN t."""
    c = curve.get(k)
    return 0.0 if c is None else float(np.clip(c["slope_per_c"] * (T0_C - t), 0.0, c["cap"]))


def day_rows(d: pd.Timestamp) -> np.ndarray:
    """Model-clock rows of local day d (0b convention)."""
    return np.arange(24) + (d.dayofyear - 1) * 24


def residual_table(curve: dict, tw: pd.Series, windows: list[pd.DatetimeIndex], years=KEEPER_YEARS) -> pd.DataFrame:
    """Per class-day curve MW, overlay MW, residual MW for every TMIN<=T0 day."""
    rows = []
    for w in windows:
        for d in w:
            if d.year not in years:
                continue
            y = d.year
            ut = unit_table(y)
            dcap = year_data(y)["capd"][d.dayofyear - 1]
            caps = year_data(y)["kday"]
            base_days = [w[0] - pd.Timedelta(days=i) for i in (1, 2, 3)]
            base = []
            for b in base_days:
                if b.year in years:
                    base.append(year_data(b.year)["kday"].loc[b.dayofyear - 1])
            base = pd.concat(base, axis=1).mean(axis=1) if base else None
            t = float(tw[d])
            for k in sorted(ut[ut.fc.notna()].k.unique()):
                f = curve_frac(curve, fit_class(k), t)
                if f <= 0:
                    continue
                u = ut[ut.k == k]
                cmw = float(np.minimum(f * u.pmax, dcap.reindex(u.index).fillna(0)).sum())
                ov = max(0.0, float(base[k]) - float(caps.loc[d.dayofyear - 1, k])) if base is not None and k in base else np.nan
                rows.append({"date": str(d.date()), "class": k, "tmin_sys": round(t, 2), "excess_frac": round(f, 4), "curve_mw": cmw, "overlay_mw": ov, "residual_mw": max(0.0, cmw - (0.0 if np.isnan(ov) else ov))})
    return pd.DataFrame(rows)


def main() -> dict:
    """Run E0a-E0e and write outputs."""
    OUT.mkdir(parents=True, exist_ok=True)
    tw, tp, wdesc = tmin_sys()
    cert, dmax, p99 = certified_days()
    windows = cold_windows(tw)
    windows_plain = cold_windows(tp)

    # ---- E0a
    wtab, points, ctrl = [], {}, {}
    for w in windows:
        ext = w.append(pd.DatetimeIndex([w[-1] + pd.Timedelta(days=1)]))
        cd = cert.reindex(ext).fillna(False)
        coldest = w[int(np.argmin(tw[w].to_numpy()))]
        ratio = float((dmax.reindex(ext) / ext.year.map(p99)).max())
        row = {"window": f"{w[0].date()}..{w[-1].date()}", "n_days": len(w), "coldest": str(coldest.date()), "tmin_min": round(float(tw[coldest]), 2), "max_netload_over_p99": round(ratio, 3), "certified": bool(cd.any())}
        if not row["certified"]:
            row["why"] = f"net-load certificate failed (max daily-max/p99 = {ratio:.3f})"
        elif not (CAMPD / f"PA_{coldest.year}.parquet").exists() or coldest.year not in KEEPER_YEARS:
            row["why"] = "certified but not instrumentable: no CAMPD/keeper class map for that year on disk"
            row["instrumented"] = False
        else:
            bf, capi = bestfrac(coldest.year, pd.DatetimeIndex([coldest]))
            row["instrumented"] = True
            row["classes"] = {}
            for k, ek in CLASS_EFORD.items():
                fr = bf.get((k, coldest))
                if fr is None:
                    continue
                ex = float(np.clip((1 - EFORD[ek]) - min(1.0, fr), 0, 1))
                points.setdefault(k, []).append((float(tw[coldest]), ex, str(coldest.date())))
                row["classes"][k] = {"best": round(fr, 3), "excess": round(ex, 3), "inst_cap_mw": round(capi.get(k, 0.0))}
        wtab.append(row)
    curve = fit(points)
    used = [r for r in wtab if r.get("instrumented")]
    non_elliott = [r for r in used if not (ELLIOTT[0] <= r["coldest"] <= ELLIOTT[1])]
    stop = len(non_elliott) < 2

    # Informational control: same instrument on the year's warm certified days (TMIN_sys > 0).
    for y in KEEPER_YEARS:
        days = cert[cert & (cert.index.year == y)].index
        days = pd.DatetimeIndex([d for d in days if d in tw.index and tw[d] > 0])
        if len(days) == 0:
            continue
        bf, _ = bestfrac(y, days)
        ctrl[y] = {k: round(float(np.median([v for (kk, _), v in bf.items() if kk == k])), 3) for k in CLASS_EFORD if any(kk == k for kk, _ in bf)}
        ctrl[y]["n_days"] = len(days)

    # ---- E0c (full curve) and E0b (LOO)
    foot = residual_table(curve, tw, windows)
    pts_loo = {k: [p for p in v if not (ELLIOTT[0] <= p[2] <= ELLIOTT[1])] for k, v in points.items()}
    curve_loo = fit({k: v for k, v in pts_loo.items() if v})
    foot_loo = residual_table(curve_loo, tw, windows)
    el = ["2022-12-24", "2022-12-25"]
    r_full = foot[foot.date.isin(el)].groupby("date").residual_mw.sum() if len(foot) else pd.Series(dtype=float)
    r_loo = foot_loo[foot_loo.date.isin(el)].groupby("date").residual_mw.sum() if len(foot_loo) else pd.Series(dtype=float)
    r_full = r_full.reindex(el).fillna(0.0)
    r_loo = r_loo.reindex(el).fillna(0.0)
    tot_full, tot_loo = float(r_full.sum()), float(r_loo.sum())
    loo_chg = (tot_loo - tot_full) / tot_full if tot_full > 0 else np.nan
    e0b = {"residual_full_mw": r_full.round(0).to_dict(), "residual_loo_mw": r_loo.round(0).to_dict(), "change_24_25_sum": None if np.isnan(loo_chg) else round(loo_chg, 3), "curve_loo": curve_loo, "verdict": ("PASS" if abs(loo_chg) <= LOO_TOL else "FAIL (Elliott-dependent)") if not np.isnan(loo_chg) else "n/a (zero full residual)"}

    fdays = foot[foot.residual_mw > 0] if len(foot) else foot
    out_season = sorted({d for d in fdays.date if pd.Timestamp(d).month not in (12, 1, 2)}) if len(fdays) else []
    foot.to_csv(OUT / "_pjmco_e0_footprint.csv", index=False)
    by_day = foot.groupby("date").agg(tmin=("tmin_sys", "first"), curve_mw=("curve_mw", "sum"), overlay_mw=("overlay_mw", "sum"), residual_mw=("residual_mw", "sum")).round(0) if len(foot) else pd.DataFrame()

    # ---- E0d
    pub = pd.read_csv(REPO / "data/raw/pjm-outages/by-year/gen_outages_by_type_2022.csv")
    pub = pub[(pub.region == "PJM RTO") & (pub.lead_days == 0)].copy()
    pub["date"] = pd.to_datetime(pub.forecast_date)
    pub = pub.set_index("date").forced_outages_mw
    y22 = year_data(2022)
    dd = list(range(20, 29))
    unav = {}
    for d in dd:
        hrs = day_rows(pd.Timestamp(2022, 12, d))
        unav[d] = float(y22["th22_pmax"] - y22["th22"].iloc[hrs].mean())
    res_day = {d: float(foot[foot.date == f"2022-12-{d:02d}"].residual_mw.sum()) if len(foot) else 0.0 for d in dd}
    base_m = np.mean([unav[d] for d in (20, 21, 22)])
    base_r = np.mean([unav[d] + res_day[d] for d in (20, 21, 22)])
    base_p = float(pub.loc["2022-12-20":"2022-12-22"].mean())
    e0d = {}
    for d in (24, 25):
        p_rise = float(pub.loc[f"2022-12-{d}"]) - base_p
        m_rise = unav[d] - base_m
        mr_rise = unav[d] + res_day[d] - base_r
        e0d[f"Dec{d}"] = {"published_rise_mw": round(p_rise), "model_own_rise_mw": round(m_rise), "missing_increment_mw": round(p_rise - m_rise), "residual_mw": round(res_day[d]), "model_rise_with_residual_mw": round(mr_rise), "ratio_primary": round(mr_rise / p_rise, 3), "ratio_strict_residual_over_missing": round((mr_rise - m_rise) / (p_rise - m_rise), 3)}
    e0d_pass = all(E0D_BAND[0] <= v["ratio_primary"] <= E0D_BAND[1] for v in e0d.values())

    # ---- E0e
    hrs = np.concatenate([day_rows(pd.Timestamp(2022, 12, d)) for d in (23, 24, 25, 26)])
    h = y22["h22"].iloc[hrs].copy()
    h["day"] = 23 + (h.index - hrs[0]) // 24
    h["he"] = (h.index - hrs[0]) % 24 + 1
    h["residual"] = h.day.map(lambda d: res_day.get(int(d), 0.0))
    h["headroom_raw"] = h.cap - h.mw
    h["headroom"] = h.headroom_raw - h.residual
    rf = pd.read_parquet(BUNDLE / "reserve_family_2022.parquet")
    req = rf[rf.family == "pjm_primary"].groupby("hour").requirement_mw.sum()
    h["pjm_primary_req"] = req.reindex(h.index).to_numpy()
    h["below"] = h.headroom < h.pjm_primary_req
    h.to_csv(OUT / "_pjmco_e0_headroom_hourly.csv")
    e0e = {"hours_below_pjm_primary": int(h.below.sum()), "min_headroom_mw": round(float(h.headroom.min())), "min_at": f"Dec{int(h.loc[h.headroom.idxmin(), 'day'])} HE{int(h.loc[h.headroom.idxmin(), 'he'])}", "min_headroom_by_day": h.groupby("day").headroom.min().round(0).to_dict(), "req_range": [round(float(h.pjm_primary_req.min())), round(float(h.pjm_primary_req.max()))]}

    # Published cross-check (never a fit target): curve MW vs published forced rise on window days.
    res = {
        "probe": "pjmco-E0 Elliott cold-correlated outage phase 0 (zero-LP)",
        "tmin_weights": "load-weighted, iso_configs PJM zone load_share (2023 metered load): " + wdesc,
        "windows_loadweighted": wtab,
        "windows_plainmean": [f"{w[0].date()}..{w[-1].date()} tmin={float(tp[w].min()):.1f}" for w in windows_plain],
        "e0a": {"curve": curve, "instrumented_windows": len(used), "non_elliott_instrumented": len(non_elliott), "verdict": "STOP" if stop else "PASS"},
        "control_warm_certified_bestfrac_median": ctrl,
        "e0b": e0b,
        "e0c": {"days_nonzero_residual": int(fdays.date.nunique()) if len(fdays) else 0, "days_outside_dec_feb": out_season, "verdict": "PASS" if not out_season else "FAIL (construction defect)", "by_day": by_day.reset_index().to_dict(orient="records") if len(by_day) else []},
        "e0d": {"by_day": e0d, "definition": "primary = (model thermal unavail rise over 20-22 Dec mean, residual applied on every day) / (published forced rise over its 20-22 Dec mean); strict = residual's added rise / (published rise - model own rise)", "band": E0D_BAND, "verdict": "PASS" if e0d_pass else "FAIL"},
        "e0e": e0e,
        "stop_label": "E0b-E0e computed INFORMATIONALLY (E0a STOP)" if stop else None,
    }
    (OUT / "_pjmco_e0_elliott_phase0.json").write_text(json.dumps(res, indent=1, default=str))
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k != "tmin_weights"}, indent=1, default=str))
