"""closeout-PJM-decommit phase 0 (ZERO LP): reach of a coal decommitment mechanism (R-55).

Readings fixed ex ante in
``docs/records/pjm/closeout-pjm-decommit/PRECOMMIT-closeout-pjm-decommit-phase0-2026-10-03.md``.

Per keeper COAL_BIT plant and year (keeper ``2026-10-03-closeout-pjm-nuc-keeper``, bundle
``results/calibration/closeout_pjm_nuc_full_span``):

* (a0) friction posture: start-up + min-load + min-down 16 h, floors replaced by priced MW;
* (a1) three-part commitment: (a0) + measured CAMPD no-load (heat-input intercept) x own
  EIA-923 delivered coal, evaluated at the keeper zone price;
* (a1-real) (a1) at the real zonal DA (diagnostic, PRECOMMIT §1);
* (b1) ``coal_committed_nested_on_mustrun`` static reach;
* (b2) ``commitment_floor_window_netload`` ceiling (sync-floor MWh in real-dark hours).

Each (a*) is an exact price-taker DP per plant (on / off with an off-age counter to the
min-down), vectorized over plants, followed by a static re-clear of the net change against the
keeper's non-COAL_BIT spare headroom (zones pooled) for the C1 / C3a / C3b side effects.

Writes ``results/phase0/pjm/_closeoutpjm_decommit_reach.json``.
Run: ``.venv/bin/python scripts/probes/_closeoutpjm_decommit_reach.py [YEAR ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
from market_sim.data.eia923 import (  # noqa: E402
    EIA923_MONTHLY_COSTS_PATH,
    load_monthly_fuel_costs,
)
from market_sim.data.fleet.eia860 import (  # noqa: E402
    BIN_STARTUP_COST_PER_MW,
    COAL_BIN_MIN_DOWN_HOURS,
)

BUNDLE = REPO / "results/calibration/closeout_pjm_nuc_full_span/hourly"
OUT = REPO / "results/phase0/pjm/_closeoutpjm_decommit_reach.json"
UNIT_DIR = REPO / "data/raw/campd-unit-level"
RAW = REPO / "data/raw"
ACT_SYS = RAW / "_validation-source/actual_lmp_hourly_PJM.parquet"
ACT_ZONE = RAW / "_validation-source/actual_lmp_zonal_PJM.parquet"
TRANCHES = RAW / "_processed-legacy/thermal_tranches_PJM.csv"
GROUP = "COAL_BIT"
T = 8760
YEARS = tuple(range(2019, 2026))
FLOOR = ("mustrun", "sync")
MIN_DOWN = int(COAL_BIN_MIN_DOWN_HOURS)
STARTUP = float(BIN_STARTUP_COST_PER_MW[GROUP])
#: Keeper C1 COAL_BIT (model, actual) TWh, calibration_verdict on the keeper bundle.
C1_COAL = {
    2019: (189.21, 169.481),
    2020: (152.458, 139.722),
    2021: (175.716, 158.999),
    2022: (147.907, 140.939),
    2023: (106.416, 103.365),
    2024: (106.031, 105.436),
}
#: Keeper C1 other classes (model, actual) TWh for the B2 re-clear check.
C1_OTHER = {
    "CC_REGULAR": {2019: (272.46, 268.842), 2020: (289.5, 283.501), 2021: (280.209, 279.443),
                   2022: (306.921, 297.965), 2023: (329.116, 325.718), 2024: (330.675, 335.623)},
    "CT_PEAKER": {2019: (10.386, 15.871), 2020: (13.777, 18.814), 2021: (12.851, 20.769),
                  2022: (13.64, 19.024), 2023: (20.546, 21.741), 2024: (28.133, 24.161)},
}
BAND = 8.0
#: Keeper C3a (model, actual) mean $/MWh and C3b monthly NRMSE, calibration_verdict.
C3A = {2019: (27.69, 27.21), 2020: (23.7, 21.75), 2021: (39.63, 39.75), 2022: (66.13, 79.37),
       2023: (31.14, 30.82), 2024: (31.48, 33.29), 2025: (44.04, 49.83)}
C3B = {2019: 0.082, 2020: 0.138, 2021: 0.094, 2022: 0.293, 2023: 0.151, 2024: 0.175, 2025: 0.222}


def _kind(uid: pd.Series) -> pd.Series:
    """Tranche kind from the unit-id suffix (``econc07`` -> ``econc``)."""
    return uid.astype(str).str.rsplit("_", n=1).str[-1].str.replace(r"\d+$", "", regex=True)


def _runs(mask: np.ndarray):
    """(start, stop) of each maximal True run."""
    if not mask.any():
        return []
    idx = np.flatnonzero(np.diff(np.r_[0, mask.view(np.int8), 0]))
    return list(zip(idx[::2].tolist(), idx[1::2].tolist()))


def load_units(y: int) -> pd.DataFrame:
    """All P1 unit-hours of the keeper year."""
    u = pd.read_parquet(
        BUNDLE / f"unit_marginal_{y}.parquet",
        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"],
    )
    u["plant_group"] = u["plant_group"].astype(str)
    return u


def zone_prices(y: int) -> tuple[dict[str, np.ndarray], np.ndarray, np.ndarray, pd.DataFrame]:
    """Keeper P1 zone price, demand-weighted system price, total demand, and the frame."""
    s = pd.read_parquet(BUNDLE / f"system_{y}.parquet", columns=["zone", "hour", "price", "demand"])
    s = s[s["zone"] != "PJM_external"]
    zp = {z: g.set_index("hour")["price"].reindex(range(T)).to_numpy(float) for z, g in s.groupby("zone")}
    pv = s.pivot(index="hour", columns="zone", values="price").reindex(range(T))
    dv = s.pivot(index="hour", columns="zone", values="demand").reindex(range(T))
    psys = (pv * dv).sum(axis=1).to_numpy() / dv.sum(axis=1).to_numpy()
    return zp, psys, dv.sum(axis=1).to_numpy(), s


def real_zone_prices(y: int) -> dict[str, np.ndarray]:
    """Real zonal DA by hour."""
    a = pd.read_parquet(ACT_ZONE)
    a = a[a["year"] == y]
    return {z: g.set_index("hour")["da"].reindex(range(T)).to_numpy(float) for z, g in a.groupby("zone")}


def campd(y: int, plants: set[int]) -> pd.DataFrame:
    """CAMPD coal-fuel unit-hours (with heat input) for ``plants``."""
    fr = []
    cols = ["facilityId", "unitId", "date", "hour", "opTime", "grossLoad", "heatInput", "primaryFuelInfo"]
    for f in sorted(UNIT_DIR.glob(f"*_{y}.parquet")):
        x = ds.dataset(str(f), format="parquet").to_table(columns=cols).to_pandas()
        x["facilityId"] = pd.to_numeric(x["facilityId"], errors="coerce")
        fr.append(x[x["facilityId"].isin(plants)])
    d = pd.concat(fr, ignore_index=True)
    d["unitId"] = d["unitId"].astype(str)
    coal = d.groupby(["facilityId", "unitId"])["primaryFuelInfo"].agg(
        lambda v: v.dropna().astype(str).str.contains("Coal").any()
    )
    keep = set(coal[coal].index)
    d = d[[k in keep for k in zip(d["facilityId"], d["unitId"])]].copy()
    d["hoy"] = (pd.to_datetime(d["date"]) - pd.Timestamp(f"{y}-01-01")).dt.days * 24 + d["hour"].astype(int)
    return d[(d["hoy"] >= 0) & (d["hoy"] < T)]


def noload(d: pd.DataFrame) -> tuple[dict[int, float], list[dict]]:
    """Per plant no-load MMBtu/h per MW of coal-unit peak (B0 regression), plus unit fits."""
    fits = []
    for (pc, uid), g in d.groupby(["facilityId", "unitId"]):
        peak = float(np.nan_to_num(g["grossLoad"].max()))
        m = (g["opTime"] >= 1.0) & (g["grossLoad"] > 0) & (g["heatInput"] > 0)
        x, h = g.loc[m, "grossLoad"].to_numpy(float), g.loc[m, "heatInput"].to_numpy(float)
        if peak <= 0 or len(x) < 200 or np.ptp(x) < 0.1 * peak:
            fits.append({"plant": int(pc), "unit": uid, "peak": peak, "ok": False})
            continue
        b, a = np.polyfit(x, h, 1)
        r2 = 1.0 - np.sum((h - (a + b * x)) ** 2) / np.sum((h - h.mean()) ** 2)
        fits.append({"plant": int(pc), "unit": uid, "peak": peak, "ok": True, "a": float(a),
                     "b": float(b), "r2": float(r2), "avg_hr_full": float((a + b * peak) / peak)})
    nl: dict[int, float] = {}
    inc: dict[int, float] = {}
    by = pd.DataFrame(fits)
    for pc, g in by.groupby("plant"):
        ok = g[g["ok"]]
        if ok.empty:
            continue
        nl[int(pc)] = float(np.clip(ok["a"], 0.0, None).sum() / g["peak"].sum())
        inc[int(pc)] = float(np.average(ok["b"], weights=ok["peak"]))
    return nl, inc, fits


def coal_price(y: int, plants: dict[int, str]) -> dict[int, np.ndarray]:
    """Plant hourly delivered coal $/MMBtu: own month -> own-year mean -> PJM state-month mean."""
    f = load_monthly_fuel_costs(EIA923_MONTHLY_COSTS_PATH)
    f = f[(f["year"] == y) & (f["fuel_group"] == "Coal")]
    month = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")).month.to_numpy()
    own = f[f["plant_id"].isin(list(plants))]
    states = set(own["state"])
    st = f[f["state"].isin(states)].groupby("month").apply(
        lambda g: np.average(g["price_per_mmbtu"], weights=g["quantity"].clip(lower=1)),
        include_groups=False,
    )
    out = {}
    for pc in plants:
        g = own[own["plant_id"] == pc]
        mon = g.groupby("month").apply(
            lambda r: np.average(r["price_per_mmbtu"], weights=r["quantity"].clip(lower=1)),
            include_groups=False,
        )
        yr = float(np.average(g["price_per_mmbtu"], weights=g["quantity"].clip(lower=1))) if len(g) else np.nan
        mp = np.array([mon.get(m, np.nan) for m in range(1, 13)])
        mp = np.where(np.isnan(mp), yr, mp)
        mp = np.where(np.isnan(mp), np.array([st.get(m, np.nan) for m in range(1, 13)]), mp)
        out[pc] = mp[month - 1]
    return out


def plant_block(um: pd.DataFrame) -> dict[int, dict]:
    """Per COAL_BIT plant: tranche (kind, mw, cap, mc) arrays and zone."""
    c = um[um["plant_group"] == GROUP].copy()
    c["kind"] = _kind(c["unit_id"])
    out = {}
    for pc, g in c.groupby("plant_code", observed=True):
        tr = []
        for _, gu in g.groupby("unit_id", observed=True):
            h = gu["hour"].to_numpy()
            mw, cap, mc = np.zeros(T), np.zeros(T), np.full(T, np.nan)
            mw[h], cap[h], mc[h] = gu["mw"], gu["cap_mw"], gu["mc"]
            tr.append((str(gu["kind"].iloc[0]), mw, cap, mc))
        out[int(pc)] = {"zone": str(g["zone"].iloc[0]), "tr": tr}
    return out


def onhour(P: dict, price: np.ndarray, mlf: float, cost_floor: np.ndarray | None = None):
    """On-state dispatch and margin per hour (PRECOMMIT §2).

    Non-floor tranches keep the keeper's own P1 dispatch; floor MW are priced at the plant's
    committed offer and run only when in the money; output is raised to ``mlf·A`` at the
    cheapest remaining offers.
    """
    kinds = np.array([t[0] for t in P["tr"]])
    MW = np.vstack([t[1] for t in P["tr"]])
    CAP = np.vstack([t[2] for t in P["tr"]])
    MC = np.nan_to_num(np.vstack([t[3] for t in P["tr"]]), nan=1e6)
    fl = np.isin(kinds, FLOOR)
    com = kinds == "committed"
    ref = MC[com].min(0) if com.any() else np.where(fl[:, None], 1e6, MC).min(0)
    MCp = np.where(fl[:, None], ref[None, :], MC)
    X = np.where(fl[:, None], np.where(price[None, :] >= ref[None, :], CAP, 0.0), MW)
    if cost_floor is not None:  # post-hoc G variant: offers raised to measured incremental cost
        MCp = np.maximum(MCp, cost_floor[None, :])
        X = np.where(price[None, :] >= MCp, np.where(fl[:, None], CAP, MW), 0.0)
    A = CAP.sum(0)
    need = np.maximum(0.0, mlf * A - X.sum(0))
    order = np.argsort(MCp, axis=0)
    room = np.take_along_axis(CAP - X, order, 0)
    cum = np.cumsum(room, 0)
    add = np.clip(need[None, :] - (cum - room), 0.0, room)
    inv = np.argsort(order, axis=0)
    X = X + np.take_along_axis(add, inv, 0)
    margin = ((price[None, :] - MCp) * X).sum(0)
    return X.sum(0), margin, A, MW.sum(0), (MW * fl[:, None]).sum(0)


def dp(r_on: np.ndarray, s_cost: np.ndarray) -> np.ndarray:
    """Exact on/off DP with min-down; rows = plants. Returns the on mask (n, T)."""
    n = r_on.shape[0]
    K = MIN_DOWN
    NEG = -1e18
    von = np.zeros(n)
    voff = np.full((n, K), NEG)  # off-age 1..K (K = may start)
    from_start = np.zeros((n, T), bool)
    k_from_k = np.zeros((n, T), bool)  # off_K came from off_K (vs off_{K-1})
    for t in range(T):
        stay = von
        start = voff[:, K - 1] - s_cost[:, t]
        fs = start > stay
        nvon = np.where(fs, start, stay) + r_on[:, t]
        nvoff = np.empty_like(voff)
        nvoff[:, 0] = von
        nvoff[:, 1:K - 1] = voff[:, 0:K - 2]
        kk = voff[:, K - 1] >= voff[:, K - 2]
        nvoff[:, K - 1] = np.where(kk, voff[:, K - 1], voff[:, K - 2])
        from_start[:, t], k_from_k[:, t] = fs, kk
        von, voff = nvon, nvoff
    on = np.zeros((n, T), bool)
    best_off = voff.argmax(1)
    st = np.where(von >= voff.max(1), -1, best_off)  # -1 = on, else off-age index
    for t in range(T - 1, -1, -1):
        is_on = st == -1
        on[:, t] = is_on
        prev = np.empty(n, int)
        # on at t: previous on unless started (then off_K)
        prev[is_on] = np.where(from_start[is_on, t], K - 1, -1)
        o = ~is_on
        age = st[o]
        p = np.where(age == 0, -1, age - 1)
        p = np.where(age == K - 1, np.where(k_from_k[o, t], K - 1, K - 2), p)
        prev[o] = p
        st = prev
    return on


def real_dark(d: pd.DataFrame, plants: list[int], kstar: dict[int, float]) -> dict[int, np.ndarray]:
    """Real dark MW per plant-hour: K*·Σ_u w_u·1{opTime_u = 0}."""
    out = {}
    for pc in plants:
        g = d[d["facilityId"] == pc]
        dark = np.zeros(T)
        if g.empty:
            out[pc] = dark
            continue
        pk = g.groupby("unitId")["grossLoad"].max()
        pk = pk[pk > 0]
        for uid, gu in g[g["unitId"].isin(pk.index)].groupby("unitId"):
            op = np.zeros(T)
            op[gu["hoy"].to_numpy()] = gu["opTime"].fillna(0.0).to_numpy()
            dark += (pk[uid] / pk.sum()) * (op <= 0.0)
        out[pc] = kstar[pc] * dark
    return out


def reclear(um: pd.DataFrame, dsum: np.ndarray, psys: np.ndarray) -> tuple[dict, np.ndarray]:
    """Static re-clear of the hourly net coal change against non-COAL_BIT headroom."""
    o = um[(um["plant_group"] != GROUP) & ~um["plant_group"].str.startswith("VIRTUAL")]
    o = o[["plant_group", "hour", "mw", "cap_mw", "mc"]].copy()
    o["spare"] = (o["cap_mw"] - o["mw"]).clip(lower=0.0)
    o["grp"] = o["plant_group"].where(o["plant_group"] != "", "other")
    o = o.sort_values(["hour", "mc"])
    hours = o["hour"].to_numpy()
    starts = np.searchsorted(hours, np.arange(T + 1))
    mc, spare, mw, grp = o["mc"].to_numpy(), o["spare"].to_numpy(), o["mw"].to_numpy(), o["grp"].to_numpy()
    alloc: dict[str, float] = {}
    dp_ = np.zeros(T)
    for h in range(T):
        need = dsum[h]
        if abs(need) < 1e-6:
            continue
        s, e = starts[h], starts[h + 1]
        if need > 0:
            sel = mc[s:e] >= psys[h] - 1e-3
            idx = np.flatnonzero(sel & (spare[s:e] > 0)) + s
            cum = np.cumsum(spare[idx])
            k = int(np.searchsorted(cum, need))
            take = np.minimum(spare[idx[: k + 1]], np.maximum(0.0, need - (cum[: k + 1] - spare[idx[: k + 1]])))
            for gname, v in zip(grp[idx[: k + 1]], take):
                alloc[gname] = alloc.get(gname, 0.0) + float(v)
            last = mc[idx[min(k, len(idx) - 1)]] if len(idx) else psys[h]
            dp_[h] = max(0.0, last - psys[h])
        else:
            idx = np.flatnonzero(mw[s:e] > 0)[::-1] + s
            cum = np.cumsum(mw[idx])
            k = int(np.searchsorted(cum, -need))
            take = np.minimum(mw[idx[: k + 1]], np.maximum(0.0, -need - (cum[: k + 1] - mw[idx[: k + 1]])))
            for gname, v in zip(grp[idx[: k + 1]], take):
                alloc[gname] = alloc.get(gname, 0.0) - float(v)
            nxt = mc[idx[min(k + 1, len(idx) - 1)]] if len(idx) else psys[h]
            dp_[h] = min(0.0, nxt - psys[h])
    return {k: v / 1e6 for k, v in alloc.items()}, dp_


def monthly_nrmse(price: np.ndarray, dem: np.ndarray, actual: np.ndarray, y: int) -> float:
    """C3b-like monthly demand-weighted NRMSE vs the hourly RT reference."""
    m = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), "h")).month.to_numpy()
    mm = np.array([np.sum(price[m == k] * dem[m == k]) / np.sum(dem[m == k]) for k in range(1, 13)])
    am = np.array([np.nanmean(actual[m == k]) for k in range(1, 13)])
    return float(np.sqrt(np.mean((mm - am) ** 2)) / am.mean())


def run_year(y: int) -> dict:
    """Census one year (PRECOMMIT §2-§3)."""
    um = load_units(y)
    zp, psys, dem, _ = zone_prices(y)
    zr = real_zone_prices(y)
    kp = plant_block(um)
    plants = sorted(kp)
    d = campd(y, set(plants))
    nl, inc, fits = noload(d)
    fuel = coal_price(y, {pc: "" for pc in plants})
    tt = pd.read_csv(TRANCHES)
    tt = tt[tt["plant_group"] == "COAL"].set_index("plant_code")
    res: dict = {"fits": {}, "variants": {}}
    okf = [f for f in fits if f["ok"]]
    wpk = np.array([f["peak"] for f in fits])
    res["fits"] = {
        "units": len(fits),
        "ok_cap_share": float(sum(f["peak"] for f in okf) / max(wpk.sum(), 1e-9)),
        "pos_intercept_cap_share": float(sum(f["peak"] for f in okf if f["a"] > 0) / max(wpk.sum(), 1e-9)),
        "r2_wmedian": float(np.median(np.repeat([f["r2"] for f in okf], [max(1, int(f["peak"] / 10)) for f in okf]))) if okf else None,
        "avg_hr_full_wmean": float(np.average([f["avg_hr_full"] for f in okf], weights=[f["peak"] for f in okf])) if okf else None,
        "inc_hr_wmean": float(np.average([f["b"] for f in okf], weights=[f["peak"] for f in okf])) if okf else None,
        "nl_mmbtu_per_mw_wmean": float(np.mean(list(nl.values()))) if nl else None,
        "plants_with_nl": len(nl),
        "plants": len(plants),
    }
    kstar = {pc: float(np.vstack([t[2] for t in kp[pc]["tr"]]).sum(0).max()) for pc in plants}
    dark = real_dark(d, plants, kstar)

    def variant(name: str, with_nl: bool, real: bool, gcost: bool = False) -> dict:
        rows, mws, keeps, floors_, As = [], [], [], [], []
        scost = []
        for pc in plants:
            P = kp[pc]
            price = (zr if real else zp).get(P["zone"], psys)
            price = np.where(np.isnan(price), psys, price)
            mlf = (
                float(tt.loc[pc, "committed_pct"]) / 100.0
                if pc in tt.index and np.isfinite(tt.loc[pc, "committed_pct"])
                else None
            )
            if mlf is None:
                kinds = np.array([t[0] for t in P["tr"]])
                CAP = np.vstack([t[2] for t in P["tr"]])
                sel = np.isin(kinds, FLOOR + ("committed",))
                mlf = float(CAP[sel].sum() / max(CAP.sum(), 1e-9))
            fz = np.nan_to_num(fuel[pc], nan=np.nanmean(fuel[pc]) if np.isfinite(fuel[pc]).any() else 2.3)
            cf = inc.get(pc, 0.0) * fz if gcost else None
            x_on, margin, A, mwk, flk = onhour(P, price, mlf, cf)
            nlc = nl.get(pc, 0.0) * fz if with_nl else 0.0
            rows.append(margin - nlc * A)
            mws.append(x_on)
            keeps.append(mwk)
            floors_.append(flk)
            As.append(A)
            scost.append(STARTUP * A)
        R = np.vstack(rows)
        on = dp(R, np.vstack(scost))
        mw_dp = np.where(on, np.vstack(mws), 0.0)
        K = np.vstack(keeps)
        D = K - mw_dp
        Dp, Dm = np.clip(D, 0, None), np.clip(-D, 0, None)
        DK = np.vstack([dark[pc] for pc in plants])
        out = {
            "dec_pos_twh": float(Dp.sum() / 1e6),
            "dec_neg_twh": float(Dm.sum() / 1e6),
            "net_twh": float(D.sum() / 1e6),
            "dark_share": float(np.minimum(Dp, DK).sum() / max(Dp.sum(), 1e-9)),
            "off_plant_hours": int((~on).sum()),
            "starts": int((on[:, 1:] & ~on[:, :-1]).sum()),
            "floor_twh_keeper": float(np.vstack(floors_).sum() / 1e6),
        }
        if not real:
            alloc, dph = reclear(um, D.sum(0), psys)
            out["reclear_alloc_twh"] = alloc
            dmean = float(np.sum(dph * dem) / np.sum(dem))
            out["dp_mean"] = dmean
            mod, act = C3A[y]
            out["c3a_pct_new"] = 100.0 * (mod + dmean - act) / act
            a = pd.read_parquet(ACT_SYS)
            rt = a[a["year"] == y].set_index("hour")["rt"].reindex(range(T)).to_numpy(float)
            n0 = monthly_nrmse(psys, dem, rt, y)
            n1 = monthly_nrmse(psys + dph, dem, rt, y)
            out["c3b_probe_keeper"] = n0
            out["c3b_new"] = C3B[y] + (n1 - n0)
        return out

    res["variants"]["a0"] = variant("a0", False, False)
    res["variants"]["a1"] = variant("a1", True, False)
    res["variants"]["a1_real"] = variant("a1_real", True, True)
    # POST-HOC supplementary (not a pre-registered reading): offers floored at measured
    # incremental fuel cost b_inc x delivered coal, plus no-load, at the keeper price.
    res["variants"]["a1g_posthoc"] = variant("a1g_posthoc", True, False, gcost=True)

    # (b1) committed band nested on must-run: removed committed MW priced at cheapest econc.
    b1 = b1d = 0.0
    b1h = np.zeros(T)
    floor_dark = 0.0
    for pc in plants:
        P = kp[pc]
        kinds = np.array([t[0] for t in P["tr"]])
        MW = np.vstack([t[1] for t in P["tr"]])
        CAP = np.vstack([t[2] for t in P["tr"]])
        MC = np.nan_to_num(np.vstack([t[3] for t in P["tr"]]), nan=1e6)
        price = zp.get(P["zone"], psys)
        sync = kinds == "sync"
        floor_dark += float(np.minimum(MW[sync].sum(0), dark[pc]).sum())
        if pc not in tt.index or not (kinds == "committed").any():
            continue
        mr, mcp = float(tt.loc[pc, "mustrun_pct"]), float(tt.loc[pc, "committed_pct"])
        if not (np.isfinite(mr) and np.isfinite(mcp)) or mcp <= 0:
            continue
        frac = min(1.0, mr / mcp)
        com = kinds == "committed"
        econ = np.char.startswith(kinds.astype(str), "econ")
        emc = MC[econ].min(0) if econ.any() else np.full(T, 1e6)
        rem = np.minimum(frac * CAP[com].sum(0), MW[com].sum(0)) * (price < emc)
        b1 += float(rem.sum())
        b1h += rem
        b1d += float(np.minimum(rem, dark[pc]).sum())
    alloc, dph = reclear(um, b1h, psys)
    dmean = float(np.sum(dph * dem) / np.sum(dem))
    a = pd.read_parquet(ACT_SYS)
    rt = a[a["year"] == y].set_index("hour")["rt"].reindex(range(T)).to_numpy(float)
    mod, act = C3A[y]
    res["b1"] = {"dec_twh": b1 / 1e6, "dark_share": b1d / max(b1, 1e-9), "reclear_alloc_twh": alloc,
                 "dp_mean": dmean, "c3a_pct_new": 100.0 * (mod + dmean - act) / act,
                 "c3b_new": C3B[y] + monthly_nrmse(psys + dph, dem, rt, y) - monthly_nrmse(psys, dem, rt, y)}
    res["b2"] = {"sync_mwh_in_real_dark_twh": floor_dark / 1e6}
    return res


def _flips(y: int, vv: dict, net: float) -> list[str]:
    """B2/B3 PASS->FAIL list for one year of one candidate after the static re-clear."""
    flips = []
    if y in C1_COAL:
        m, a = C1_COAL[y]
        new = m - net - a
        if abs(m - a) <= BAND and abs(new) > BAND:
            flips.append(f"C1 COAL_BIT {y} {m - a:+.2f}->{new:+.2f}")
        for cls, tab in C1_OTHER.items():
            mm, aa = tab[y]
            nn = mm + vv["reclear_alloc_twh"].get(cls, 0.0) - aa
            if abs(mm - aa) <= BAND and abs(nn) > BAND:
                flips.append(f"C1 {cls} {y} {mm - aa:+.2f}->{nn:+.2f}")
            if abs(mm - aa) > BAND and abs(nn) > abs(mm - aa) + 1.0:
                flips.append(f"C1 {cls} {y} worsens {mm - aa:+.2f}->{nn:+.2f}")
    mod, act = C3A[y]
    if abs(100 * (mod - act) / act) <= 10 and abs(vv["c3a_pct_new"]) > 10:
        flips.append(f"C3a {y} -> {vv['c3a_pct_new']:+.1f}%")
    if C3B[y] <= 0.20 and vv["c3b_new"] > 0.20:
        flips.append(f"C3b {y} -> {vv['c3b_new']:.3f}")
    return flips


def readings(res: dict) -> dict:
    """Apply PRECOMMIT §3 to (a0), (a1), (a1-real), (b1), (b2)."""
    pool = [y for y in (2019, 2020, 2021) if y in res]
    need = {y: 0.5 * (C1_COAL[y][0] - C1_COAL[y][1] - BAND) for y in pool}
    fits = [res[y]["fits"] for y in res]
    b0 = all(
        f["pos_intercept_cap_share"] >= 0.8 and (f["r2_wmedian"] or 0) >= 0.9
        and 8.0 <= (f["avg_hr_full_wmean"] or 0) <= 14.0
        for f in fits
    )
    out = {"B0_measured_basis": b0, "B1_need_twh": need}
    for v in ("a0", "a1", "a1_real"):
        b1 = all(res[y]["variants"][v]["dec_pos_twh"] >= need[y] for y in pool)
        tot = sum(res[y]["variants"][v]["dec_pos_twh"] for y in pool)
        ds_pool = (
            sum(res[y]["variants"][v]["dec_pos_twh"] * res[y]["variants"][v]["dark_share"] for y in pool) / tot
            if tot else 0.0
        )
        b4 = ds_pool >= 0.6 and all(res[y]["variants"][v]["dark_share"] >= 0.6 for y in pool)
        r = {"B1": b1, "B4": b4, "dark_share_pool": ds_pool}
        if v != "a1_real":
            flips = [f for y in res for f in _flips(y, res[y]["variants"][v], res[y]["variants"][v]["net_twh"])]
            r["B2_B3_flips"] = flips
            r["B2_B3"] = not flips
            r["CHARTERED"] = b1 and b4 and not flips and (b0 if v == "a1" else True)
        out[v] = r
    b1fl = [f for y in res for f in _flips(y, res[y]["b1"], res[y]["b1"]["dec_twh"])]
    b1ds = sum(res[y]["b1"]["dec_twh"] * res[y]["b1"]["dark_share"] for y in pool) / max(
        sum(res[y]["b1"]["dec_twh"] for y in pool), 1e-9)
    out["b1"] = {
        "B2_B3_flips": b1fl,
        "B4": b1ds >= 0.6 and all(res[y]["b1"]["dark_share"] >= 0.6 for y in pool),
        "dark_share_pool": b1ds,
        "B1": all(res[y]["b1"]["dec_twh"] >= need[y] for y in pool),
        "dec_twh": {y: res[y]["b1"]["dec_twh"] for y in res},
    }
    out["b2"] = {
        "B1_ceiling": all(res[y]["b2"]["sync_mwh_in_real_dark_twh"] >= need[y] for y in pool),
        "ceiling_twh": {y: res[y]["b2"]["sync_mwh_in_real_dark_twh"] for y in res},
    }
    return out


def main(years: list[int]) -> None:
    """Run every year and write the JSON."""
    res = {}
    if OUT.exists():
        res = {int(k): v for k, v in json.loads(OUT.read_text()).get("years", {}).items()}
    for y in years:
        res[y] = run_year(y)
        print(y, json.dumps({k: v for k, v in res[y].items()}, default=str)[:3000], flush=True)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps({"years": res}, indent=2, default=str))
    out = {"years": res}
    if all(y in res for y in (2019, 2020, 2021)):
        out["readings"] = readings(res)
        print(json.dumps(out["readings"], indent=2, default=str))
    OUT.write_text(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
