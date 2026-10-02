"""PJM close-out E1 (zero-LP): Elliott phase 0 v2 -- season gate, winter certificate, de-biased instrument, gas leg.

Executes phase 0 (steps E1a-E1e) of
``docs/records/pjm/PRECOMMIT-pjm-closeout-elliott-cold-outage-v2-2026-10-02.md``.
Reads committed artifacts and raw data only; never solves; edits nothing in
``src/`` or ``scripts/data/``. Reuses the v1 probe
(``scripts/probes/_pjmco_e0_elliott_phase0.py``): its TMIN_sys loader, model
clock (row = doy0*24 + HE - 1), keeper capacity basis (per-unit max cap_mw as
pmax proxy; daily-mean cap_mw), CAMPD best-mustered-hour instrument, overlay
capture (class sum cap_mw vs a 3-day pre-window baseline) and the E0d/E0e code
(here E1d/E1e, definitions unchanged).

Functional form (PRECOMMIT v2 section 1)::

    excess_c(d) = 1[d in Dec-Feb] * min(cap_c, s_T,c * max(0, t0 - TMIN_d)
                                              + g * s_G,c * max(0, B_d - b0))

* B_d = Transco Z6 NY daily spot - Henry Hub daily spot
  (``data/raw/gas-prices/transco_z6_ny_daily.csv``). Calendar days carry the
  last trade date's print forward (staircase; weekends/holidays). b0 = median
  of the Dec-Feb TRADE-DAY prints 2018-2025; the window B threshold is the
  pooled Dec-Feb p90 of the same prints.
* g = 1 for CC_REGULAR / CT_PEAKER / ST_GAS units, 0 otherwise; a dual-fuel
  unit (``data.fleet.dual_fuel_plant_groups``, EIA-860 multifuel) has g = 0
  on a day it is switched, i.e. Transco Z6 daily spot (gas-side proxy) >= the
  PJM delivered oil parity (``data.fuel.dual_fuel_oil_price_series``,
  EIA-923 monthly). In the class-level fit the gas regressor carries the
  class's unswitched pmax share that day.
* Windows: maximal runs (gaps <= 2 d) of Dec-Feb days with TMIN <= t0 or
  B >= p90. Certified iff the window's peak daily-max EIA-930 net load >=
  the p99 of that winter's (Dec Y-1 .. Feb Y) hourly net load.
* Instrument: per class per day, best-mustered CAMPD hour fraction. Warm
  reference per class per winter = median over that winter's Dec-Feb days
  with TMIN > 0 and daily-max net load >= that winter's hourly p90.
  Excess = max(0, warm ref - muster). Anchor day of a window (reported) =
  min-TMIN day, or max-B day when the window's first day qualifies by B only.
* Fit: per class, 2-regressor non-negative LS through the origin over every
  instrumented day of every certified window in winters 2018/19..2024/25
  (closed-form active-set enumeration; scipy.optimize is not used). cap =
  max certified excess.
* Leap-year 31 Dec (2020, 2024) has no row on the 8760 model clock and is
  skipped by the residual (it carries no keeper capacity to derate).
* Residual: per class-day max(0, curve MW - overlay MW); overlay baseline =
  mean class cap over the 3 days before the rule-17 run (Dec-Feb days with
  TMIN <= t0 or B > b0, gaps <= 2 d) containing the day. Leap-year 31 Dec
  (2020, 2024) has no row on the 8760 model clock and is skipped.

Memory: the keeper sidecar and CAMPD are read one calendar year at a time
and reduced to compact arrays before the next year is touched.

Run: ``python scripts/probes/_pjmco_e1_elliott_phase0_v2.py``
Writes ``results/phase0/pjm/_pjmco_e1_elliott_phase0_v2.json`` plus
``_pjmco_e1_footprint.csv`` and ``_pjmco_e1_headroom_hourly.csv``.
"""

from __future__ import annotations

import gc
import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.fleet import dual_fuel_plant_groups  # noqa: E402
from market_sim.data.fuel import dual_fuel_oil_price_series  # noqa: E402

BUNDLE = REPO / "results/calibration/pjmnext16_A_span/hourly"
CAMPD = REPO / "data/raw/campd-unit-level"
GAS = REPO / "data/raw/gas-prices/transco_z6_ny_daily.csv"
OUT = REPO / "results/phase0/pjm"
T0_C = -7.0
FIRST, LAST = 2018, 2025
KEEPER_YEARS = range(2019, 2026)
FIT_WINTERS = range(2019, 2026)  # winter Y = Dec Y-1 .. Feb Y; 2018/19 .. 2024/25
PJM_STATES = ("DC", "DE", "IL", "IN", "KY", "MD", "MI", "NC", "NJ", "OH", "PA", "TN", "VA", "WV")
FIT_CLASSES = ("COAL", "CC_REGULAR", "CT_PEAKER", "ST_GAS")
GAS_CLASSES = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")
COAL_SUB = ("COAL_BIT", "COAL_WC", "COAL_PRB", "COAL_LIGNITE")
ELLIOTT_DAYS = ("2022-12-24", "2022-12-25")
LOO_TOL = 0.30
E1D_BAND = (0.7, 1.3)
WINTER_MONTHS = (12, 1, 2)


def fit_class(k: str) -> str | None:
    """Model plant_group -> fit class (None = excluded)."""
    if k in COAL_SUB:
        return "COAL"
    return k if k in FIT_CLASSES else None


def winter_of(d: pd.Timestamp) -> int | None:
    """Winter label Y for Dec Y-1 .. Feb Y; None outside Dec-Feb."""
    if d.month == 12:
        return d.year + 1
    return d.year if d.month in (1, 2) else None


# ---------------------------------------------------------------- drivers
def tmin_sys() -> pd.Series:
    """Load-weighted PJM daily TMIN (v1 loader, iso_configs zone load_share)."""
    w = pd.concat([pd.read_csv(p) for p in sorted(glob.glob(str(REPO / "data/raw/pjm-weather/pjm_zone_temp_daily*.csv")))])
    w["date"] = pd.to_datetime(w.date)
    w = w.drop_duplicates(["date", "zone"]).dropna(subset=["tmin_c"])
    share = {z.name: z.load_share for z in get_iso_config("PJM").zones}
    w["wt"] = w.zone.map(share)
    return ((w.tmin_c * w.wt).groupby(w.date).sum() / w.wt.groupby(w.date).sum()).sort_index()


def gas_driver() -> tuple[pd.Series, pd.Series, pd.Series]:
    """(B calendar-day staircase, Z6 calendar-day staircase, B trade-day prints)."""
    g = pd.read_csv(GAS, parse_dates=["date"]).sort_values("date").set_index("date")
    b_trade = (g.transco_z6_ny_usd_mmbtu - g.henry_hub_usd_mmbtu).dropna()
    cal = pd.date_range(f"{FIRST}-01-01", f"{LAST}-12-31", freq="D")
    b = b_trade.reindex(cal).ffill()
    z6 = g.transco_z6_ny_usd_mmbtu.reindex(cal).ffill()
    return b, z6, b_trade


def netload() -> tuple[pd.Series, dict, dict]:
    """(daily max EIA-930 PJM net load, winter hourly p99, winter hourly p90)."""
    e = pd.read_parquet(REPO / "data/raw/eia-930-hourly/PJM hourly.parquet", columns=["Local date", "Demand", "NG: WND", "NG: SUN"])
    e["date"] = pd.to_datetime(e["Local date"])
    e["net"] = pd.to_numeric(e.Demand, errors="coerce") - pd.to_numeric(e["NG: WND"], errors="coerce").fillna(0) - pd.to_numeric(e["NG: SUN"], errors="coerce").fillna(0)
    e["winter"] = [winter_of(d) for d in e.date]
    dmax = e.groupby("date").net.max()
    ew = e[e.winter.notna()]
    complete = ew.groupby("winter").date.apply(lambda s: {d.month for d in s} >= {12, 1, 2})
    p99 = ew.groupby("winter").net.quantile(0.99).to_dict()
    p90 = ew.groupby("winter").net.quantile(0.90).to_dict()
    p99 = {int(k): float(v) for k, v in p99.items()}
    p90 = {int(k): float(v) for k, v in p90.items()}
    p99["_complete"] = {int(k): bool(v) for k, v in complete.items()}
    return dmax, p99, p90


def runs(days: pd.DatetimeIndex, gap: int = 2) -> list[pd.DatetimeIndex]:
    """Maximal runs of sorted days with gaps <= ``gap`` days."""
    days = days.sort_values()
    if len(days) == 0:
        return []
    out, cur = [], [days[0]]
    for x in days[1:]:
        if (x - cur[-1]).days <= gap:
            cur.append(x)
        else:
            out.append(cur)
            cur = [x]
    out.append(cur)
    return [pd.DatetimeIndex(w) for w in out]


# ---------------------------------------------------------------- per-year compaction
def load_year(y: int, winter_days: pd.DatetimeIndex) -> dict:
    """Compact keeper + CAMPD view of calendar year y (frees the raw frames).

    Returns ``ut`` (unit table: plant_code, k, fc, pmax), ``capd`` (units x days
    float32 daily-mean cap_mw), ``kday`` (day x class cap sum), ``bf``
    {(fc, date): best-mustered fraction} for ``winter_days`` in y, ``capi``
    instrument capacity, and for 2022 hourly totals for E1d/E1e.
    """
    t = pq.read_table(BUNDLE / f"unit_marginal_{y}.parquet", columns=["unit_id", "plant_group", "plant_code", "fuel", "hour", "mw", "cap_mw"])
    x = t.to_pandas(strings_to_categorical=True)
    del t
    k = x.plant_group.astype(str)
    blank = (k == "") | (k == "nan")
    k = k.where(~blank, x.fuel.astype(str))
    keep = ~k.str.startswith("VIRTUAL").to_numpy()
    x = x[keep]
    k = k[keep]
    uid = x.unit_id.astype(str).to_numpy()
    codes, inv = np.unique(uid, return_inverse=True)
    hrs = x.hour.to_numpy()
    nh = int(hrs.max()) + 1
    cap = np.zeros((len(codes), nh), dtype=np.float32)
    cap[inv, hrs] = x.cap_mw.to_numpy()
    first = pd.Series(np.arange(len(uid))).groupby(inv).first().to_numpy()
    ut = pd.DataFrame({"plant_code": pd.to_numeric(x.plant_code.astype(str), errors="coerce").to_numpy()[first], "k": k.to_numpy()[first], "pmax": cap.max(axis=1)}, index=codes)
    ut["fc"] = ut.k.map(fit_class)
    nd = nh // 24
    capd = cap[:, : nd * 24].reshape(len(codes), nd, 24).mean(axis=2).astype(np.float32)
    kday = pd.DataFrame(capd, index=codes).groupby(ut.k.to_numpy()).sum().T
    d = {"ut": ut, "capd": capd, "kday": kday}
    if y == 2022:
        mw = np.zeros_like(cap)
        mw[inv, hrs] = x.mw.to_numpy()
        d["h22"] = pd.DataFrame({"cap": cap.sum(axis=0), "mw": mw.sum(axis=0)})
        th = ~ut.k.isin(["import", "hydro"]).to_numpy()
        d["th22"] = pd.Series(cap[th].sum(axis=0))
        d["th22_pmax"] = float(ut.pmax[th].sum())
        del mw
    del x, cap, uid, hrs, inv
    gc.collect()
    d["bf"], d["capi"] = campd_bestfrac(y, ut, winter_days)
    gc.collect()
    return d


def campd_type_class(unit_type: str, fuel: str) -> str:
    """CAMPD unitType/primaryFuel -> fit class (multi-class plants only; v1)."""
    ut, fu = str(unit_type).lower(), str(fuel).lower()
    if "coal" in fu:
        return "COAL"
    if "combined" in ut:
        return "CC_REGULAR"
    if "turbine" in ut:
        return "CT_PEAKER"
    return "ST_GAS"


def campd_bestfrac(y: int, ut: pd.DataFrame, days: pd.DatetimeIndex) -> tuple[dict, dict]:
    """Per (fit class, day) best-mustered CAMPD hour fraction for ``days`` (v1 instrument)."""
    ut = ut[ut.fc.notna()]
    pc = ut.groupby(["plant_code", "fc"]).pmax.sum().reset_index()
    groups = pc.groupby("plant_code").fc.apply(set)
    dset = {str(d.date()) for d in days}
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
                kk = next(iter(g))
            else:
                kk = campd_type_class(r.unitType, r.primaryFuelInfo)
                if kk not in g:
                    kk = max(g, key=lambda q: float(pc[(pc.plant_code == r.fid) & (pc.fc == q)].pmax.iloc[0]))
            cls[(r.fid, r.unitId)] = kk
            present.add((r.fid, kk))
        c["dstr"] = c.date.astype(str).str[:10]
        c = c[c.dstr.isin(dset)]
        c["fc"] = [cls[(a_, b_)] for a_, b_ in zip(c.fid, c.unitId)]
        c["g"] = pd.to_numeric(c.grossLoad, errors="coerce").fillna(0.0)
        parts.append(c.groupby(["fc", "dstr", "hour"]).g.sum())
        del c
    hr = pd.concat(parts).groupby(level=[0, 1, 2]).sum().reset_index()
    capi = pc[[(p_, k_) in present for p_, k_ in zip(pc.plant_code, pc.fc)]].groupby("fc").pmax.sum()
    hr["frac"] = hr.g / hr.fc.map(capi)
    best = hr.groupby(["fc", "dstr"]).frac.max()
    return {(kk, pd.Timestamp(dd)): float(v) for (kk, dd), v in best.items()}, {kk: float(v) for kk, v in capi.items()}


# ---------------------------------------------------------------- fit / curve
def nnls2(x1: np.ndarray, x2: np.ndarray, yv: np.ndarray) -> tuple[float, float]:
    """Two-regressor non-negative LS through the origin (active-set enumeration)."""
    cands = [(0.0, 0.0)]
    a = np.column_stack([x1, x2])
    if np.linalg.matrix_rank(a) == 2:
        s = np.linalg.lstsq(a, yv, rcond=None)[0]
        if (s >= 0).all():
            cands.append((float(s[0]), float(s[1])))
    if (x1 @ x1) > 0:
        cands.append((max(0.0, float(x1 @ yv / (x1 @ x1))), 0.0))
    if (x2 @ x2) > 0:
        cands.append((0.0, max(0.0, float(x2 @ yv / (x2 @ x2)))))
    sse = [float(((yv - p * x1 - q * x2) ** 2).sum()) for p, q in cands]
    return cands[int(np.argmin(sse))]


def fit(points: pd.DataFrame) -> dict:
    """Per class: s_T, s_G, cap from certified window-day points."""
    res = {}
    for c in FIT_CLASSES:
        p = points[points.fc == c]
        if p.empty:
            continue
        xg = p.x_g.to_numpy() if c in GAS_CLASSES else np.zeros(len(p))
        sT, sG = nnls2(p.x_t.to_numpy(), xg, p.excess.to_numpy())
        res[c] = {"s_T": round(sT, 5), "s_G": round(sG, 5), "cap": round(float(p.excess.max()), 4), "n_days": int(len(p)), "n_nonzero_excess": int((p.excess > 0).sum())}
    return res


def unit_frac(curve: dict, ut: pd.DataFrame, xt: float, xb: float, switched: np.ndarray) -> np.ndarray:
    """Per-unit excess fraction on a day (g = 0 for non-gas and switched dual-fuel units)."""
    f = np.zeros(len(ut))
    for c, v in curve.items():
        m = (ut.fc == c).to_numpy()
        g = np.isin(ut.k.to_numpy(), GAS_CLASSES) & ~switched
        val = v["s_T"] * xt + np.where(g, v["s_G"] * xb, 0.0)
        f[m] = np.clip(val[m], 0.0, v["cap"])
    return f


def day_rows(d: pd.Timestamp) -> np.ndarray:
    """Model-clock rows of local day d (0b convention)."""
    return np.arange(24) + (d.dayofyear - 1) * 24


def main() -> dict:
    """Run E1a-E1e and write outputs."""
    OUT.mkdir(parents=True, exist_ok=True)
    tw = tmin_sys()
    b, z6, b_trade = gas_driver()
    dmax, p99, p90 = netload()
    complete = p99.pop("_complete")

    bw_trade = b_trade[[d.month in WINTER_MONTHS and FIRST <= d.year <= LAST for d in b_trade.index]]
    b0 = float(bw_trade.median())
    bp90 = float(bw_trade.quantile(0.90))
    cal = pd.date_range(f"{FIRST}-01-01", f"{LAST}-12-31", freq="D")
    wdays = pd.DatetimeIndex([d for d in cal if d.month in WINTER_MONTHS])
    bw_cal = b.reindex(wdays)
    b0_cal = float(bw_cal.median())

    # Dual-fuel switch per day (gas-side proxy: Z6 spot >= delivered oil parity).
    capable = dual_fuel_plant_groups()
    cfg = ScenarioConfig(iso="PJM", mode="backcast")
    oil = {}
    for y in range(FIRST, LAST + 1):
        o = dual_fuel_oil_price_series(cfg, y)
        for d in wdays[wdays.year == y]:
            oil[d] = float(o[min(d.dayofyear - 1, 364) * 24])
    switched_day = pd.Series({d: bool(z6.get(d, np.nan) >= oil[d]) for d in wdays})

    # ---- windows (section 2)
    trig_t = (tw.reindex(wdays) <= T0_C).fillna(False)
    trig_b = (b.reindex(wdays) >= bp90).fillna(False)
    windows = runs(wdays[(trig_t | trig_b).to_numpy()])

    # ---- per-year compaction (one year at a time)
    need_days = {y: wdays[wdays.year == y] for y in KEEPER_YEARS}
    YD: dict[int, dict] = {}
    for y in KEEPER_YEARS:
        YD[y] = load_year(y, need_days[y])
        print(f"[year {y}] units={len(YD[y]['ut'])} bf={len(YD[y]['bf'])}", flush=True)
        gc.collect()

    def gshare(c: str, d: pd.Timestamp) -> float:
        """Unswitched pmax share of class c's units on day d (1.0 when no unit switches)."""
        if c not in GAS_CLASSES or d.year not in YD:
            return 1.0 if c in GAS_CLASSES else 0.0
        ut = YD[d.year]["ut"]
        u = ut[ut.fc == c]
        if not switched_day.get(d, False) or u.pmax.sum() <= 0:
            return 1.0
        df = np.array([(int(p) if pd.notna(p) else -1, k) in capable for p, k in zip(u.plant_code, u.k)])
        return float(1.0 - u.pmax[df].sum() / u.pmax.sum())

    # ---- warm reference muster per class per winter
    warm = {}
    for wy in FIT_WINTERS:
        days = [d for d in wdays if winter_of(d) == wy and d in tw.index and tw[d] > 0 and dmax.get(d, -np.inf) >= p90.get(wy, np.inf) and d.year in YD]
        warm[wy] = {"n_days": len(days)}
        for c in FIT_CLASSES:
            v = [YD[d.year]["bf"][(c, d)] for d in days if (c, d) in YD[d.year]["bf"]]
            if v:
                warm[wy][c] = round(float(np.median(v)), 4)

    # ---- E1a
    wtab, pts = [], []
    for w in windows:
        wy = winter_of(w[0])
        peak = float(dmax.reindex(w).max())
        ratio = peak / p99[wy] if wy in p99 else np.nan
        first_b_only = bool(trig_b[w[0]] and not trig_t[w[0]])
        anchor = w[int(np.argmax(b.reindex(w).to_numpy()))] if first_b_only else w[int(np.argmin(tw.reindex(w).to_numpy()))]
        cert = bool(ratio >= 1.0) if not np.isnan(ratio) else False
        row = {"window": f"{w[0].date()}..{w[-1].date()}", "winter": f"{wy - 1}/{str(wy)[2:]}", "n_days": len(w), "n_tmin_days": int(trig_t[w].sum()), "n_b_days": int(trig_b[w].sum()), "anchor": str(anchor.date()), "anchor_rule": "max B (B first)" if first_b_only else "min TMIN", "tmin_min": round(float(tw.reindex(w).min()), 2), "b_max": round(float(b.reindex(w).max()), 2), "peak_over_winter_p99": round(ratio, 3), "winter_complete": complete.get(wy, False), "in_fit_winters": wy in FIT_WINTERS, "certified": cert}
        if not cert:
            row["why"] = f"winter certificate failed (peak/p99 = {ratio:.3f})"
        elif wy not in FIT_WINTERS:
            row["why"] = "certified, outside fit winters 2018/19..2024/25"
        if cert:
            row["anchor_excess"] = {}
            for d in w:
                if d.year not in YD or wy not in warm:
                    continue
                for c in FIT_CLASSES:
                    if (c, d) not in YD[d.year]["bf"] or c not in warm[wy]:
                        continue
                    m = YD[d.year]["bf"][(c, d)]
                    ex = max(0.0, warm[wy][c] - min(1.0, m))
                    xt = max(0.0, T0_C - float(tw[d]))
                    xg = gshare(c, d) * max(0.0, float(b[d]) - b0)
                    pts.append({"window": row["window"], "winter": wy, "date": d, "fc": c, "muster": m, "warm_ref": warm[wy][c], "excess": ex, "x_t": xt, "x_g": xg, "fit": wy in FIT_WINTERS})
                    if d == anchor:
                        row["anchor_excess"][c] = round(ex, 4)
            row["instrumented_days"] = len({p["date"] for p in pts if p["window"] == row["window"]})
        wtab.append(row)
    pts = pd.DataFrame(pts)
    fitpts = pts[pts.fit] if len(pts) else pts
    cert_fit = [r for r in wtab if r["certified"] and r["in_fit_winters"]]
    cert_fit_instr = [r for r in cert_fit if r.get("instrumented_days", 0) > 0]
    outside_dec22 = [r for r in cert_fit if not r["window"].startswith("2022-12")]
    e1a_pass = len(cert_fit) >= 3 and len(outside_dec22) >= 2
    curve = fit(fitpts) if len(fitpts) else {}

    # ---- residual machinery (rule-17 runs for the overlay baseline)
    r17 = (tw.reindex(wdays) <= T0_C).fillna(False) | (b.reindex(wdays) > b0).fillna(False)
    r17_runs = runs(wdays[r17.to_numpy()])
    run_start = {d: r[0] for r in r17_runs for d in r}

    def kday_row(d: pd.Timestamp) -> pd.Series | None:
        if d.year not in YD or d.dayofyear - 1 >= len(YD[d.year]["kday"]):
            return None
        return YD[d.year]["kday"].loc[d.dayofyear - 1]

    def residual(cv: dict, days: list[pd.Timestamp]) -> pd.DataFrame:
        rows = []
        for d in days:
            if d.year not in YD or d.month not in WINTER_MONTHS or d.dayofyear - 1 >= YD[d.year]["capd"].shape[1]:
                continue  # leap-year 31 Dec has no row on the 8760 model clock
            yd = YD[d.year]
            ut = yd["ut"]
            xt = max(0.0, T0_C - float(tw.get(d, np.nan))) if d in tw.index else 0.0
            xb = max(0.0, float(b[d]) - b0)
            sw = np.zeros(len(ut), dtype=bool)
            if switched_day.get(d, False):
                sw = np.array([(int(p) if pd.notna(p) else -1, k) in capable for p, k in zip(ut.plant_code, ut.k)])
            f = unit_frac(cv, ut, xt, xb, sw)
            if not (f > 0).any():
                continue
            cmw_u = np.minimum(f * ut.pmax.to_numpy(), yd["capd"][:, d.dayofyear - 1])
            cmw = pd.Series(cmw_u).groupby(ut.k.to_numpy()).sum()
            st = run_start.get(d, d)
            base = [kday_row(st - pd.Timedelta(days=i)) for i in (1, 2, 3)]
            base = [x for x in base if x is not None]
            base = pd.concat(base, axis=1).mean(axis=1) if base else None
            today = yd["kday"].loc[d.dayofyear - 1]
            for k, v in cmw.items():
                if v <= 0:
                    continue
                ov = max(0.0, float(base[k]) - float(today[k])) if base is not None and k in base.index else np.nan
                rows.append({"date": str(d.date()), "class": k, "tmin_sys": round(float(tw.get(d, np.nan)), 2), "b": round(float(b[d]), 3), "dualfuel_switched_day": bool(switched_day.get(d, False)), "run_start": str(st.date()), "curve_mw": float(v), "overlay_mw": ov, "residual_mw": max(0.0, float(v) - (0.0 if np.isnan(ov) else ov))})
        return pd.DataFrame(rows)

    all_days = [d for d in pd.date_range("2019-01-01", "2025-12-31") if d.month in WINTER_MONTHS]
    foot = residual(curve, all_days)

    # ---- E1b
    el_win = [r["window"] for r in wtab if r["window"] <= "2022-12-24" and r["window"].split("..")[1] >= "2022-12-24"]
    loo_pts = fitpts[~fitpts.window.isin(el_win)] if len(fitpts) else fitpts
    curve_loo = fit(loo_pts) if len(loo_pts) else {}
    eld = [pd.Timestamp(x) for x in ELLIOTT_DAYS]
    foot_loo = residual(curve_loo, eld)
    rf_ = foot[foot.date.isin(ELLIOTT_DAYS)].groupby("date").residual_mw.sum().reindex(list(ELLIOTT_DAYS)).fillna(0.0) if len(foot) else pd.Series(0.0, index=list(ELLIOTT_DAYS))
    rl_ = foot_loo.groupby("date").residual_mw.sum().reindex(list(ELLIOTT_DAYS)).fillna(0.0) if len(foot_loo) else pd.Series(0.0, index=list(ELLIOTT_DAYS))
    tf, tl = float(rf_.sum()), float(rl_.sum())
    chg = (tl - tf) / tf if tf > 0 else np.nan
    e1b = {"elliott_window_dropped": el_win, "elliott_window_in_fit": bool(len(el_win) and len(fitpts) and fitpts.window.isin(el_win).any()), "residual_full_mw": rf_.round(0).to_dict(), "residual_loo_mw": rl_.round(0).to_dict(), "per_day_change": {k: (round((rl_[k] - rf_[k]) / rf_[k], 3) if rf_[k] > 0 else None) for k in ELLIOTT_DAYS}, "change_24_25_sum": None if np.isnan(chg) else round(chg, 3), "curve_loo": curve_loo, "verdict": ("PASS" if abs(chg) <= LOO_TOL else "FAIL") if not np.isnan(chg) else "FAIL (zero full residual; undefined)"}

    # ---- E1c
    fpos = foot[foot.residual_mw > 0] if len(foot) else foot
    out_season = sorted({d for d in fpos.date if pd.Timestamp(d).month not in WINTER_MONTHS}) if len(fpos) else []
    foot.to_csv(OUT / "_pjmco_e1_footprint.csv", index=False)
    by_day = foot.groupby("date").agg(tmin=("tmin_sys", "first"), b=("b", "first"), curve_mw=("curve_mw", "sum"), overlay_mw=("overlay_mw", "sum"), residual_mw=("residual_mw", "sum")).round(1) if len(foot) else pd.DataFrame()
    fcls = fpos.assign(fc=fpos["class"].map(fit_class)).groupby("fc").residual_mw.agg(["count", "sum", "max"]).round(0) if len(fpos) else pd.DataFrame()
    e1c = {"days_nonzero_residual": int(fpos.date.nunique()) if len(fpos) else 0, "days_by_winter": fpos.date.map(lambda s: winter_of(pd.Timestamp(s))).value_counts().sort_index().to_dict() if len(fpos) else {}, "days_outside_dec_feb": out_season, "class_day_stats_mw": fcls.to_dict(orient="index") if len(fcls) else {}, "verdict": "PASS" if not out_season else "FAIL"}

    # ---- E1d (v1 E0d definition, unchanged)
    pub = pd.read_csv(REPO / "data/raw/pjm-outages/by-year/gen_outages_by_type_2022.csv")
    pub = pub[(pub.region == "PJM RTO") & (pub.lead_days == 0)].copy()
    pub["date"] = pd.to_datetime(pub.forecast_date)
    pub = pub.set_index("date").forced_outages_mw
    y22 = YD[2022]
    dd = list(range(20, 29))
    unav = {d: float(y22["th22_pmax"] - y22["th22"].iloc[day_rows(pd.Timestamp(2022, 12, d))].mean()) for d in dd}
    res_day = {d: float(foot[foot.date == f"2022-12-{d:02d}"].residual_mw.sum()) if len(foot) else 0.0 for d in dd}
    base_m = np.mean([unav[d] for d in (20, 21, 22)])
    base_r = np.mean([unav[d] + res_day[d] for d in (20, 21, 22)])
    base_p = float(pub.loc["2022-12-20":"2022-12-22"].mean())
    e1d = {}
    for d in (24, 25):
        p_rise = float(pub.loc[f"2022-12-{d}"]) - base_p
        m_rise = unav[d] - base_m
        mr_rise = unav[d] + res_day[d] - base_r
        e1d[f"Dec{d}"] = {"published_rise_mw": round(p_rise), "model_own_rise_mw": round(m_rise), "residual_mw": round(res_day[d]), "residual_20_22_mean_mw": round(float(np.mean([res_day[x] for x in (20, 21, 22)]))), "model_rise_with_residual_mw": round(mr_rise), "ratio_primary": round(mr_rise / p_rise, 3)}
    e1d_pass = all(E1D_BAND[0] <= v["ratio_primary"] <= E1D_BAND[1] for v in e1d.values())
    elliott_by_day = {f"2022-12-{d:02d}": {"tmin": round(float(tw[pd.Timestamp(2022, 12, d)]), 2), "b": round(float(b[pd.Timestamp(2022, 12, d)]), 2), "switched": bool(switched_day[pd.Timestamp(2022, 12, d)]), "curve_mw": round(float(foot[foot.date == f"2022-12-{d:02d}"].curve_mw.sum())) if len(foot) else 0, "overlay_mw": round(float(foot[foot.date == f"2022-12-{d:02d}"].overlay_mw.sum())) if len(foot) else 0, "residual_mw": round(res_day[d])} for d in dd}

    # ---- E1e
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
    h.to_csv(OUT / "_pjmco_e1_headroom_hourly.csv")
    imin = h.headroom.idxmin()
    e1e = {"hours_below_pjm_primary": int(h.below.sum()), "min_headroom_mw": round(float(h.headroom.min())), "min_at": f"Dec{int(h.loc[imin, 'day'])} HE{int(h.loc[imin, 'he'])}", "min_headroom_by_day": h.groupby("day").headroom.min().round(0).to_dict(), "req_range": [round(float(h.pjm_primary_req.min())), round(float(h.pjm_primary_req.max()))]}

    res = {
        "probe": "pjmco-E1 Elliott phase 0 v2 (zero-LP)",
        "gas_driver": {"b0_trade_day_median": round(b0, 4), "b0_calendar_staircase_median_info": round(b0_cal, 4), "b_p90_trade_day": round(bp90, 4), "n_trade_days_dec_feb": int(len(bw_trade))},
        "dual_fuel": {"capable_pairs": len(capable), "switched_winter_days": int(switched_day.sum()), "switched_days_list": [str(d.date()) for d in switched_day[switched_day].index], "rule": "switched iff Transco Z6 daily spot >= PJM delivered oil parity (EIA-923 monthly via dual_fuel_oil_price_series)"},
        "winter_p99": {f"{k - 1}/{str(k)[2:]}": round(v) for k, v in p99.items()},
        "winter_p90": {f"{k - 1}/{str(k)[2:]}": round(v) for k, v in p90.items()},
        "warm_reference": warm,
        "windows": wtab,
        "e1a": {"certified_in_fit_winters": len(cert_fit), "certified_instrumented": len(cert_fit_instr), "certified_outside_dec2022": len(outside_dec22), "curve": curve, "verdict": "PASS" if e1a_pass else "STOP = FAIL"},
        "e1b": e1b,
        "e1c": e1c,
        "e1c_by_day": by_day.reset_index().to_dict(orient="records") if len(by_day) else [],
        "e1d": {"by_day": e1d, "band": E1D_BAND, "verdict": "PASS" if e1d_pass else "FAIL"},
        "elliott_by_day": elliott_by_day,
        "e1e": e1e,
        "fit_points": len(fitpts),
    }
    (OUT / "_pjmco_e1_elliott_phase0_v2.json").write_text(json.dumps(res, indent=1, default=str))
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k not in ("e1c_by_day", "warm_reference")}, indent=1, default=str))
