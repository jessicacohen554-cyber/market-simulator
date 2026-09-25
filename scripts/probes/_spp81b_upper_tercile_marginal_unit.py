"""SPP-81b (zero LP): who is marginal in SPP's 2023-24 upper tercile, real vs keeper?

Charter: the SPP-81 handoff (``docs/handoffs/FINDING-spp-81-upper-tercile-residual-2026-09-25.md``).
Parents: SPP-80 / SPP-81 (``FINDING-spp-80-upper-tercile-premium``,
``FINDING-spp-81-residual-upper-tercile``). Hour set: SPP-80's exactly (RT p67-p99, Feb
excluded, interval-level scarcity hours dropped), via ``_spp81_residual_upper_tercile``.

Legs, all on committed data plus a ``fleet_only`` rebuild of the keeper bundle
``results/calibration/rspp_span`` (no LP, ``scripts.lib.bundle_fleet``):

  A. **Model price setter.** Per upper-tercile hour and zone, the AVAILABLE keeper row whose
     assembled offer (``mc_base``) is nearest the zone's P1 price; its class, offer heat rate
     ((mc - vom) / fuel) and fuel price. Match = within $1/MWh.
  B. **Class-aware donor pool.** The same rebuild with ``class_aware_fuel_price_fallback``
     forced on (runtime patch, probe only); the setter-row and merit re-clear price shift.
  C. **Per-plant heat rate.** CAMPD SWPP-BA upper-tercile heat rate over each unit's
     dispatchable range (SPP-81's proxy) against the keeper's offer heat rate for the same
     plant and class; the incremental (OLS slope) heat rate against the average.
  D. **Cost coverage.** Per hour, each running gas unit's fuel cost at its CAMPD heat rate and
     the keeper's own F923 plant-month gas price, plus the keeper's class VOM; how often the
     hub MEC exceeds every running unit's cost, and MEC minus the MW-weighted p90.
  E. **Timing, wind, setter class.** Hour-of-day share of the tercile, the residual by wind
     share and season, and the RT - model gap by the model's setter class.
  F. **Additive or heat-rate?** Month-level OLS of upper-tercile MEC (and the model price) on
     that month's delivered KS/OK/NE gas.

Solves nothing and writes only to ``--cache``. Usage:
``python scripts/probes/_spp81b_upper_tercile_marginal_unit.py --cache <dir> [--years 2019 2020 2023 2024]``
"""

from __future__ import annotations

import argparse
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.probes._spp73_commitment_reach import swpp_gas_units  # noqa: E402
from scripts.probes._spp81_residual_upper_tercile import (  # noqa: E402
    FLEX_PAD,
    HR_VALID,
    MIN_MW,
    campd_gas,
    delivered_gas_monthly,
    frame,
    upper,
)

BUNDLE = REPO_ROOT / "results/calibration/rspp_span"
MATCH_TOL = 1.0  # $/MWh: a row "sets" the zone price when its offer is this close to it
GAS = ("gas_cc", "gas_ct", "gas_st")
CAMPD_TO_GROUP = {"CC": "CC_REGULAR", "CT": "CT_PEAKER", "ST_GAS": "ST_GAS"}
# Keeper SPP VOMs by CAMPD class, read off the rebuilt fleet rows (gas_cc 2.0, gas_ct 3.5,
# gas_st 4.0 $/MWh) -- used only to put a CAMPD unit's fuel cost on the offer basis.
VOM = {"CC": 2.0, "CT": 3.5, "ST_GAS": 4.0}


def rebuild(y: int, cache: Path, class_aware: bool) -> dict:
    """``fleet_only`` rebuild of the keeper's year ``y`` (cached), optionally class-aware."""
    p = cache / f"fleet_{y}{'_ca' if class_aware else ''}.pkl"
    if p.exists():
        return pickle.loads(p.read_bytes())
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    if class_aware:
        from market_sim.config.scenarios import ScenarioConfig

        orig = ScenarioConfig.__post_init__

        def _patched(self):
            orig(self)
            object.__setattr__(self, "class_aware_fuel_price_fallback", True)

        ScenarioConfig.__post_init__ = _patched
    try:
        st, _ = reconstruct_bundle_fleet(BUNDLE, y, verbose=False)
    finally:
        if class_aware:
            ScenarioConfig.__post_init__ = orig
    fa = st["fleet_arrays"]
    keys = ("unit_id", "fuel_type", "plant_group", "zone", "heat_rate", "vom", "plant_code")
    out = {
        "rows": [{k: getattr(g, k) for k in keys} for g in st["fleet"]],
        "mc": np.asarray(st["mc_base"], dtype=np.float32),
        "avail": (np.asarray(fa.pmax)[:, None] * np.asarray(fa.availability)).astype(np.float32),
        "fuel_prices": np.asarray(st["fuel_prices"], dtype=np.float32),
        "class_aware": bool(st["config"].class_aware_fuel_price_fallback),
    }
    p.write_bytes(pickle.dumps(out))
    return out


def setter(fl: dict, P: pd.DataFrame, hours: np.ndarray) -> pd.DataFrame:
    """Leg A: the nearest-offer available row per (hour, zone) and its offer heat rate."""
    r = pd.DataFrame(fl["rows"])
    cls = r.plant_group.replace("", np.nan).fillna(r.fuel_type).to_numpy()
    zn, mc, av, fp = r.zone.to_numpy(), fl["mc"], fl["avail"], fl["fuel_prices"]
    rec = []
    for t in hours:
        for z in P.columns:
            m = (zn == z) & (av[:, t] > 1.0)
            if not m.any():
                continue
            i = np.where(m)[0][np.argmin(np.abs(mc[m, t] - P.at[t, z]))]
            ohr = (mc[i, t] - r.vom.iat[i]) / fp[i, t] if fp[i, t] > 0.5 else np.nan
            rec.append((t, z, P.at[t, z], cls[i], abs(mc[i, t] - P.at[t, z]), ohr, fp[i, t], int(r.plant_code.iat[i]), i))
    R = pd.DataFrame(rec, columns=["h", "z", "p", "cls", "gap", "ohr", "fp", "plant", "row"])
    R["matched"] = R.gap < MATCH_TOL
    return R


def class_aware_shift(base: dict, ca: dict, R: pd.DataFrame, D: pd.DataFrame) -> tuple[float, float]:
    """Leg B: demand-weighted price shift, same setter row and merit re-clear at fixed quantity."""
    zn = pd.DataFrame(base["rows"]).zone.to_numpy()
    av, m0, m1 = base["avail"], base["mc"], ca["mc"]
    same, merit, w = [], [], []
    for t, z, p, i in R[R.matched][["h", "z", "p", "row"]].itertuples(index=False):
        m = (zn == z) & (av[:, t] > 1.0)
        same.append(m1[i, t] - m0[i, t])
        q = av[m, t][m0[m, t] <= p + 1e-6].sum()
        o1 = np.argsort(m1[m, t])
        j = min(np.searchsorted(np.cumsum(av[m, t][o1]), q - 1e-6), o1.size - 1)
        merit.append(m1[m, t][o1][j] - p)
        w.append(D.at[t, z])
    return float(np.average(same, weights=w)), float(np.average(merit, weights=w))


def campd_legs(y: int, fl: dict, ns: pd.DataFrame, ids, pm) -> tuple[dict, pd.DataFrame]:
    """Legs C and D on CAMPD SWPP-BA gas unit-hours in the tercile's non-scarcity hours."""
    r = pd.DataFrame(fl["rows"])
    gr = r[r.fuel_type.isin(GAS)]
    fp_plant = {int(p): fl["fuel_prices"][i] for p, i in zip(gr.plant_code, gr.index)}
    ohr = gr.groupby(["plant_code", "plant_group"]).heat_rate.first()
    H = ns.index.to_numpy()
    cls, mw, hi = campd_gas(y, ids, pm)
    fid = np.array([int(k.split("|")[0]) for k in cls.index])
    run = mw >= MIN_MW
    hr = np.divide(hi, mw, out=np.full_like(mw, np.nan), where=run)
    ok = run & (hr >= HR_VALID[0]) & (hr <= HR_VALID[1])
    umax = np.nanpercentile(np.where(run, mw, np.nan), 99, axis=1)
    umin = np.nanpercentile(np.where(run, mw, np.nan), 10, axis=1)
    flex = ok & (mw > (umin + FLEX_PAD * umax)[:, None]) & (mw < ((1 - FLEX_PAD) * umax)[:, None])
    fp = np.vstack([fp_plant.get(p, np.full(8760, np.nan)) for p in fid])
    cost = hr * fp + np.array([VOM[c] for c in cls])[:, None]
    mec = ns.mec.to_numpy()
    maxrun = np.nanmax(np.where(ok[:, H], cost[:, H], np.nan), 0)
    p90 = np.full(H.size, np.nan)
    for j, t in enumerate(H):
        m = flex[:, t] & np.isfinite(cost[:, t])
        if m.sum() >= 3:
            c, w = cost[m, t], mw[m, t]
            o = np.argsort(c)
            p90[j] = c[o][np.searchsorted(np.cumsum(w[o]) / w.sum(), 0.9)]
    inc = np.full(len(cls), np.nan)
    for i in range(len(cls)):
        m = ok[i]
        if m.sum() > 50 and np.ptp(mw[i, m]) > 0.2 * umax[i]:
            inc[i] = np.polyfit(mw[i, m], hi[i, m], 1)[0]
    W = np.where(flex[:, H], mw[:, H], 0).sum(1)
    Q = np.where(flex[:, H], hi[:, H], 0).sum(1)
    k = np.isfinite(inc) & (inc > 4) & (inc < 25) & (W > 0)
    out = {
        "cost_p90flex": np.nanmean(p90),
        "mec_minus_p90flex": np.nanmean(mec - p90),
        "share_mec_above_every_running_unit": np.nanmean(mec > maxrun),
        "hr_avg_flex": Q.sum() / W.sum(),
        "hr_incremental_flex": (inc[k] * W[k]).sum() / W[k].sum(),
        "hr_avg_same_units": Q[k].sum() / W[k].sum(),
    }
    pp = []
    for p in np.unique(fid):
        m = fid == p
        if W[m].sum() < 1000:
            continue
        c = cls[m].iloc[0]
        pp.append({"plant": p, "cls": c, "mwh": W[m].sum(), "campd_hr": Q[m].sum() / W[m].sum(),
                   "offer_hr": ohr.get((p, CAMPD_TO_GROUP[c]), np.nan)})
    return out, pd.DataFrame(pp)


def month_fit(d: pd.DataFrame, col: str) -> tuple[float, float]:
    """OLS ``col = a + b * gas`` over month rows; returns (a, b)."""
    X = np.c_[np.ones(len(d)), d.gas]
    b = np.linalg.lstsq(X, d[col], rcond=None)[0]
    return float(b[0]), float(b[1])


def main() -> None:
    """Print legs A-F per year."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, type=Path)
    ap.add_argument("--years", nargs="+", type=int, default=[2019, 2020, 2023, 2024])
    a = ap.parse_args()
    a.cache.mkdir(parents=True, exist_ok=True)
    lmp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet")
    comp = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_components_hourly_zonal_SPP.parquet")
    ids, pm = swpp_gas_units()
    pd.set_option("display.width", 250)
    rows, pps, gaps, months = [], [], [], []
    for y in a.years:
        f = frame(y, lmp, comp)
        ns = upper(f)
        ns = ns[~ns.scar].copy()
        H = ns.index.to_numpy()
        s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
        s = s[s["pass"] == "P1"]
        P = s.pivot(index="hour", columns="zone", values="price")
        D = s.pivot(index="hour", columns="zone", values="demand")
        base, ca = rebuild(y, a.cache, False), rebuild(y, a.cache, True)
        R = setter(base, P, H)
        Rm = R[R.matched]
        gset = Rm.cls.isin(["CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP"])
        gm = delivered_gas_monthly(y)
        row = {"year": y, "n_hours": H.size, "rt_mec": ns.mec.mean(), "model_p": ns.m.mean(),
               "gas923_monthly": ns.mon.map(gm).mean(), "setter_match": R.matched.mean(),
               "setter_gas_share": gset.mean(), "setter_offer_hr_gas": Rm[gset].ohr.mean(),
               "setter_fuel_gas": Rm[gset].fp.mean()}
        row.update({f"setter_{k}": v for k, v in Rm.cls.value_counts(normalize=True).items() if v >= 0.005})
        row["ca_dP_same_row"], row["ca_dP_merit"] = class_aware_shift(base, ca, R, D)
        c, pp = campd_legs(y, base, ns, ids, pm)
        row.update(c)
        hod = pd.Series(H) % 24
        row["share_HE17_21"], row["share_HE10_15"] = hod.between(16, 20).mean(), hod.between(9, 14).mean()
        ns["hr"] = ns.mec / ns.mon.map(gm)
        ns["wsh"] = ns.wind / (ns.wind + ns.net)
        for lo, hi_ in ((0, 0.15), (0.15, 0.3), (0.3, 0.45), (0.45, 1.0)):
            row[f"hr_wind_{lo:.2f}"] = ns.hr[(ns.wsh > lo) & (ns.wsh <= hi_)].mean()
        row["hr_MAM"] = ns.hr[ns.mon.isin([3, 4, 5])].mean()
        row["hr_JJAS"] = ns.hr[ns.mon.isin([6, 7, 8, 9])].mean()
        rows.append(row)
        pp["year"] = y
        pps.append(pp)
        top = Rm.groupby("h").apply(lambda d: d.sort_values("p").cls.iloc[-1])
        g = ns.join(top.rename("setcls"))
        g["setcls"] = g.setcls.map(lambda k: "COAL" if str(k).startswith("COAL") else k)
        gaps.append(g.groupby("setcls").apply(lambda d: pd.Series({"share": len(d) / len(g), "gap": (d.mec - d.m).mean()})).assign(year=y))
        mm = ns.groupby("mon").agg(mec=("mec", "mean"), model=("m", "mean"), n=("mec", "size"))
        mm["gas"], mm["year"] = gm.reindex(mm.index), y
        months.append(mm[mm.n >= 30])
        print(f"{y} done", flush=True)
    T = pd.DataFrame(rows).set_index("year")
    print("\n== legs A, B, D, E per year ==\n" + T.round(3).T.to_string())
    PP = pd.concat(pps)
    PP = PP.dropna(subset=["offer_hr"])
    print("\n== leg C: CAMPD upper-tercile HR vs keeper offer HR (MWh-weighted, same plants) ==")
    print(PP.groupby(["year", "cls"]).apply(lambda d: pd.Series({
        "n": len(d), "campd_hr": np.average(d.campd_hr, weights=d.mwh),
        "offer_hr": np.average(d.offer_hr, weights=d.mwh),
        "offer_over_campd": np.average(d.offer_hr, weights=d.mwh) / np.average(d.campd_hr, weights=d.mwh)})).round(3).to_string())
    G = pd.concat(gaps).reset_index().pivot(index="setcls", columns="year", values=["share", "gap"])
    print("\n== leg E: RT MEC - model price by the model's setter class ==\n" + G.round(2).to_string())
    M = pd.concat(months)
    print("\n== leg F: month-level OLS of upper-tercile price on delivered gas ==")
    base_years = [y for y in a.years if y <= 2020]
    for lab, ys in (("base " + "-".join(map(str, base_years)), base_years),
                    *((str(y), [y]) for y in a.years if y >= 2023)):
        d = M[M.year.isin(ys)]
        if len(d) < 3:
            continue
        (ra, rb), (ma, mb) = month_fit(d, "mec"), month_fit(d, "model")
        print(f"{lab:>14}: RT MEC = {ra:6.2f} + {rb:5.2f}*gas | model = {ma:6.2f} + {mb:5.2f}*gas | n={len(d)}")
    if base_years:
        a0, b0 = month_fit(M[M.year.isin(base_years)], "mec")
        for y in a.years:
            if y >= 2023:
                d = M[M.year == y]
                print(f"{y}: intercept at the base slope {(d.mec - b0 * d.gas).mean():.2f} vs base {a0:.2f}")


if __name__ == "__main__":
    main()
