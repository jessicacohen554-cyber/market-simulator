"""soco-91 zero-LP intra-day census: by hour of day, who sets SOCO's price, at what
offer and loading, and where does the model-minus-lambda gap sit?

Owner ruling 2026-09-29 (soco-90 card): "Zero-LP intra-day census". Rule 32
``[R-SHARD]`` (a): this never solves. Per year it does one ``fleet_only`` rebuild of
the keeper recipe (``results/calibration/soco87_span``, the soco-89/90 construction)
for each unit's ``mc_base[g,t]``, ``pmax``, ``availability``, ``min_gen`` and its D-2
``min_gen_mechanism``, then reads the keeper's committed hourly sidecars
(``system`` / ``class_band_hourly`` / ``class_hourly`` / ``storage``), Southern's
FERC-714 lambda on the bench builder's dense CST 8760 (``derive_actual_lmp._soco``)
and the EIA-930 ``SOCO hourly`` frame on the model's own positional clock
(``_eia_hourly_frame_filled``).

Setter attribution (tighter than soco-89's ±$0.50 match): a unit is a price-setter
candidate only if its offer is within ``TOL`` of the system price AND its
class-band is INTERIOR in that hour (dispatched strictly between its floor and its
available capacity). In a pure LP a unit at its floor or at its cap cannot set the
dual, so this removes most of soco-89's ambiguity. Hours with no thermal candidate
are labelled ``hydro/storage`` when the hydro or pumped-storage fleet is interior
(its budget/SOC dual then sets the price), else ``UNMATCHED``.

Out-of-merit MW: for each class-band-hour, ``max(0, mw - Σ cap of its units offered
at or below the price)`` — the MW dispatched above the price, which only a floor
can force.

Usage::

    uv run python scripts/probes/_soco91_intraday_census.py --out DIR [--years ...]
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT)]

SPAN = ROOT / "results/calibration/soco87_span"
YEARS = tuple(range(2019, 2026))
T = 8760
TOL = 0.50  # $/MWh offer-to-price match window (diagnostic only; soco-89's value)
EPS_MW = 1.0  # MW margin for "interior" (strictly between floor and cap)
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH = np.repeat(np.arange(12), np.array(_DAYS) * 24)
HOD = np.arange(T) % 24
SEASON = np.select(
    [np.isin(MONTH, (11, 0, 1)), np.isin(MONTH, (2, 3, 4)), np.isin(MONTH, (5, 6, 7))],
    ["DJF", "MAM", "JJA"],
    "SON",
)
BANDS = ("mustrun", "committed", "econlo", "econ", "econhi", "peak")
COAL = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC")
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")


def _band(uid: str, klass: str) -> str:
    """Tranche band from the unit id suffix; unbanded units carry ''."""
    s = uid.rsplit("_", 1)[-1]
    for b in ("committed", "econlo", "econhi", "peak", "mustrun", "econ"):
        if s.startswith(b):
            return b
    return ""


def _klass(group: str, fuel: str) -> str:
    """Class label matching ``class_band_hourly.klass``."""
    if group:
        return group
    return {"nuclear": "nuclear", "oil": "oil", "biomass": "biomass"}.get(fuel, "OTHER")


def rebuild(year: int, cache: Path) -> dict:
    """``fleet_only`` rebuild of the keeper recipe (cached per year)."""
    f = cache / f"fleet91_{year}.npz"
    if f.exists():
        z = np.load(f, allow_pickle=True)
        return {k: z[k] for k in z.files}
    from replay_keeper import derived_run_year_inputs, run_year_kwargs
    from run_calibration import run_year
    from scripts.lib.bundle_fleet import clear_fleet_caches

    meta = copy.deepcopy(json.loads((SPAN / "meta.json").read_text()))
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(str(SPAN), year))
    clear_fleet_caches()
    with (
        contextlib.redirect_stderr(io.StringIO()),
        contextlib.redirect_stdout(io.StringIO()),
    ):
        st = run_year(
            year,
            meta["iso"],
            T,
            float(meta["gas_prices"][str(year)]),
            {},
            fleet_only=True,
            **kw,
        )
    fa = st["fleet_arrays"]
    ids = np.array([str(g.unit_id) for g in st["fleet"]])
    klass = np.array(
        [_klass(str(g.plant_group), str(g.fuel_type)) for g in st["fleet"]]
    )

    def _2d(a):
        a = np.asarray(a, float)
        return a if a.ndim == 2 else np.repeat(a[:, None], T, 1)

    r = dict(
        ids=ids,
        klass=klass,
        band=np.array([_band(u, k) for u, k in zip(ids, klass)]),
        hr=np.asarray(fa.heat_rate, float),
        fuel=_2d(st["fuel_prices"]).astype(np.float32),
        mc=_2d(st["mc_base"]).astype(np.float32),
        cap=(np.asarray(fa.pmax, float)[:, None] * _2d(fa.availability)).astype(
            np.float32
        ),
        floor=_2d(fa.min_gen).astype(np.float32),
        mech=np.asarray(fa.min_gen_mechanism, np.int8),
    )
    np.savez(f, **r)
    return r


def lambda_cst(year: int) -> np.ndarray:
    """Southern's lambda on the bench builder's dense CST 8760 calendar."""
    from data.derive_actual_lmp import _soco

    _rec, hourly = _soco(year)
    return hourly["rt"].to_numpy(float)


def eia930(year: int) -> pd.DataFrame:
    """EIA-930 SOCO hourly frame on the model's positional clock (row k = hour k)."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    fr = _eia_hourly_frame_filled("SOCO", year).reset_index(drop=True)
    # NG: PS exists only from 2024-07-15 (before that NG: WAT folds PS
    # discharge); never interpolate it across the split.
    ps = fr["NG: PS"].copy() if "NG: PS" in fr.columns else None
    fr = fr.interpolate(limit_direction="both")
    if ps is not None:
        fr["NG: PS"] = ps
    return fr


def _weekend(year: int) -> np.ndarray:
    """Weekend flag on the dense 8760 (Feb 29 dropped, as both sides do)."""
    d = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    d = d[~((d.month == 2) & (d.day == 29))]
    return np.repeat(d.dayofweek.to_numpy() >= 5, 24)[:T]


def _hod_mean(x: np.ndarray, m: np.ndarray, w: np.ndarray | None = None) -> list:
    """Mean of x over mask m, per hour of day (None where empty)."""
    out = []
    for h in range(24):
        mm = m & (HOD == h)
        if not mm.any():
            out.append(None)
            continue
        ww = np.ones(mm.sum()) if w is None else w[mm]
        out.append(round(float(np.average(x[mm], weights=ww)), 2))
    return out


def census(year: int, cache: Path) -> dict:
    """The intra-day census for one year."""
    f = rebuild(year, cache)
    s = pd.read_parquet(SPAN / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"].sort_values(["zone", "hour"])
    zn = sorted(s.zone.unique())
    Pz = np.vstack([s[s.zone == z].price.to_numpy() for z in zn])
    Dz = np.vstack([s[s.zone == z].demand.to_numpy() for z in zn])
    D = Dz.sum(0)
    P = (Pz * Dz).sum(0) / D
    lam = lambda_cst(year)
    gap = P - lam
    q40, q80 = np.quantile(lam, [0.4, 0.8])
    lo, hi = lam <= q40, lam > q80
    wk = _weekend(year)
    Wn = D / D.sum()

    cb = pd.read_parquet(SPAN / f"hourly/class_band_hourly_{year}.parquet")
    cb = cb[cb["pass"] == "P1"]
    cb["band"] = cb["band"].astype(str).replace({"": "_"})
    cb["klass"] = cb["klass"].astype(str)
    mw_b = {
        kb: g.set_index("hour").mw.reindex(range(T), fill_value=0.0).to_numpy(float)
        for kb, g in cb.groupby(["klass", "band"])
    }
    ch = pd.read_parquet(SPAN / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    mw_c = {
        str(k): g.set_index("hour").mw.reindex(range(T), fill_value=0.0).to_numpy(float)
        for k, g in ch.groupby("klass", observed=True)
    }
    stg = pd.read_parquet(SPAN / f"hourly/storage_{year}.parquet")
    stg = stg[stg["pass"] == "P1"]
    net_st = {
        str(k): (g.set_index("hour").discharge_mw - g.set_index("hour").charge_mw)
        .reindex(range(T), fill_value=0.0)
        .to_numpy(float)
        for k, g in stg.groupby("tech", observed=True)
    }

    # ---- per class-band capacity, floor, merit capacity --------------------
    kband = np.array(
        [f"{k}|{b if b else '_'}" for k, b in zip(f["klass"], f["band"])], dtype=object
    )
    mc, cap, flo = f["mc"].astype(float), f["cap"].astype(float), f["floor"]
    inmerit = mc <= P[None, :] + TOL
    stats = {}
    interior = {}
    oom = {}
    for kb in np.unique(kband):
        k, b = kb.split("|")
        m = kband == kb
        c_b = cap[m].sum(0)
        f_b = np.minimum(flo[m].astype(float), cap[m]).sum(0)
        mw = mw_b.get((k, b), np.zeros(T))
        interior[kb] = (mw > f_b + EPS_MW) & (mw < c_b - EPS_MW)
        oom[kb] = np.maximum(0.0, mw - (cap[m] * inmerit[m]).sum(0))
        stats[kb] = (c_b, f_b, mw)

    # ---- setter: offer within TOL of price AND its class-band interior ------
    cand = np.abs(mc - P[None, :]) <= TOL
    int_u = np.vstack([interior[kb] for kb in kband])
    ok = cand & int_u
    dist = np.where(ok, np.abs(mc - P[None, :]), np.inf)
    iu = dist.argmin(0)
    has = np.isfinite(dist[iu, np.arange(T)])
    hyd_int = interior.get("hydro|_", np.zeros(T, bool)) | (
        np.abs(net_st.get("pumped_storage", np.zeros(T))) > EPS_MW
    )
    setter = np.where(
        has, kband[iu], np.where(hyd_int, "hydro/storage", "UNMATCHED")
    ).astype(object)
    s_mc = np.where(has, mc[iu, np.arange(T)], np.nan)
    s_hr = np.where(has, f["hr"][iu], np.nan)
    s_fuel = np.where(has, f["fuel"][iu, np.arange(T)], np.nan)
    s_load = np.full(T, np.nan)
    for kb in np.unique(setter[has]):
        c_b, _f, mw = stats[kb]
        m = setter == kb
        s_load[m] = mw[m] / np.where(c_b[m] > 0, c_b[m], np.nan)
    n_cand = (cand & int_u).sum(0)

    def share_tab(mask):
        w = Wn * mask
        tot = w.sum()
        out = {}
        for c in pd.unique(setter[mask]):
            m = mask & (setter == c)
            out[str(c)] = dict(
                share=round(float(w[m].sum() / tot), 3),
                P=round(float(np.average(P[m], weights=D[m])), 2),
                lam=round(float(np.average(lam[m], weights=D[m])), 2),
                offer=None
                if not np.isfinite(s_mc[m]).any()
                else round(float(np.nanmean(s_mc[m])), 2),
                hr=None
                if not np.isfinite(s_hr[m]).any()
                else round(float(np.nanmean(s_hr[m])), 3),
                fuel=None
                if not np.isfinite(s_fuel[m]).any()
                else round(float(np.nanmean(s_fuel[m])), 2),
                loading=None
                if not np.isfinite(s_load[m]).any()
                else round(float(np.nanmean(s_load[m])), 2),
                contrib=round(float((Wn * gap)[m].sum()), 3),
            )
        return dict(sorted(out.items(), key=lambda kv: -kv[1]["share"]))

    # ---- actual vs model supply by hour of day ------------------------------
    e = eia930(year)

    def col(c):
        return e[c].to_numpy(float) if c in e.columns else np.zeros(T)

    act = {
        "coal": col("NG: COL"),
        "gas": col("NG: NG"),
        "nuclear": col("NG: NUC"),
        "hydro": col("NG: WAT"),
        "pumped_storage": np.nan_to_num(col("NG: PS")),
        # discharge side, comparable across the split: WAT (+ PS discharge once split)
        "hydro_plus_ps_dis": col("NG: WAT")
        + np.clip(np.nan_to_num(col("NG: PS")), 0, None),
        "solar": col("NG: SUN"),
        "interchange_export": col("Total interchange"),
        "demand": col("Demand"),
    }
    gen_total = sum(mw_c.values()) + sum(net_st.values())
    mod = {
        "coal": sum(mw_c.get(c, 0) for c in COAL),
        "gas": sum(mw_c.get(c, 0) for c in GAS),
        "nuclear": mw_c.get("nuclear", np.zeros(T)),
        "hydro": mw_c.get("hydro", np.zeros(T)),
        "pumped_storage": net_st.get("pumped_storage", np.zeros(T)),
        "hydro_plus_ps_dis": mw_c.get("hydro", np.zeros(T))
        + np.clip(net_st.get("pumped_storage", np.zeros(T)), 0, None),
        "solar": mw_c.get("solar", np.zeros(T)),
        "interchange_export": gen_total - D,
        "demand": D,
    }

    # ---- floors: D-2 MW by mechanism, and out-of-merit MW ------------------
    mech_mw = {}
    for mid in np.unique(f["mech"]):
        if mid == 0:
            continue
        m = f["mech"] == mid  # (n_gen, T): tag of the binding floor
        mech_mw[int(mid)] = np.where(m, np.minimum(flo, cap), 0.0).sum(0)
    oom_tot = sum(oom.values())
    oom_top = {
        kb: round(float(v[lo].mean()), 1)
        for kb, v in sorted(oom.items(), key=lambda kv: -kv[1][lo].mean())[:6]
        if v[lo].mean() > 1
    }

    masks = {"all": np.ones(T, bool), "low40": lo, "top20": hi}
    out = dict(
        year=year,
        eia930_ps_split_share=round(float(np.isfinite(col("NG: PS")).mean()), 3),
        zonal_price_spread_max=round(float((Pz.max(0) - Pz.min(0)).max()), 3),
        c3a_pct=round(
            100 * (np.average(P, weights=D) / np.average(lam, weights=D) - 1), 1
        ),
        matched_share=round(float(has.mean()), 3),
        ambiguous_share=round(float((n_cand > 1).mean()), 3),
        low40_hod_count=[int((lo & (HOD == h)).sum()) for h in range(24)],
        top20_hod_count=[int((hi & (HOD == h)).sum()) for h in range(24)],
        gap_hod={k: _hod_mean(gap, m, D) for k, m in masks.items()},
        P_hod={k: _hod_mean(P, m, D) for k, m in masks.items()},
        lam_hod={k: _hod_mean(lam, m, D) for k, m in masks.items()},
        gap_split={
            f"{band}|{dw}|{se}": dict(
                n=int(mm.sum()),
                gap=round(float(np.average(gap[mm], weights=D[mm])), 2)
                if mm.any()
                else None,
            )
            for band, bm in (("low40", lo), ("top20", hi))
            for dw, dm in (("wkday", ~wk), ("wkend", wk))
            for se in ("DJF", "MAM", "JJA", "SON")
            for mm in [bm & dm & (SEASON == se)]
        },
        setter={k: share_tab(m) for k, m in masks.items()},
        setter_night_0_5_low40=share_tab(lo & (HOD < 6)),
        setter_aft_12_18_top20=share_tab(hi & (HOD >= 12) & (HOD <= 18)),
        supply_hod={
            k: dict(
                model_low40=_hod_mean(mod[k], lo),
                actual_low40=_hod_mean(act[k], lo),
                model_top20=_hod_mean(mod[k], hi),
                actual_top20=_hod_mean(act[k], hi),
            )
            for k in mod
        },
        supply_mean={
            k: dict(
                model_low40=round(float(mod[k][lo].mean()), 0),
                actual_low40=round(float(act[k][lo].mean()), 0),
                model_top20=round(float(mod[k][hi].mean()), 0),
                actual_top20=round(float(act[k][hi].mean()), 0),
            )
            for k in mod
        },
        floor_mw_by_mech={
            str(k): dict(
                low40=round(float(v[lo].mean()), 0),
                top20=round(float(v[hi].mean()), 0),
            )
            for k, v in mech_mw.items()
        },
        mustrun_band_mw={
            kb: dict(
                low40=round(float(stats[kb][2][lo].mean()), 0),
                top20=round(float(stats[kb][2][hi].mean()), 0),
            )
            for kb in stats
            if kb.endswith("|mustrun")
        },
        oom_mw=dict(
            low40=round(float(oom_tot[lo].mean()), 1),
            top20=round(float(oom_tot[hi].mean()), 1),
            low40_top_bands=oom_top,
        ),
        band_loading_low40={
            kb: round(
                float((stats[kb][2][lo] / np.maximum(stats[kb][0][lo], 1)).mean()), 2
            )
            for kb in stats
            if kb.split("|")[0] in COAL + GAS and stats[kb][0][lo].mean() > 50
        },
    )
    return out


RESTACK = GAS + COAL + ("oil",)
C1_KEYS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "COAL_BIT", "COAL_PRB")


def _greedy(demand: np.ndarray, cap: np.ndarray, mc: np.ndarray):
    """Merit-order fill (vectorized over t); dispatch and marginal offer (soco-90)."""
    order = np.argsort(mc, axis=0, kind="stable")
    cs = np.take_along_axis(cap, order, axis=0)
    ms = np.take_along_axis(mc, order, axis=0)
    cum = np.cumsum(cs, axis=0)
    fill = np.clip(demand[None, :] - (cum - cs), 0.0, cs)
    out = np.zeros_like(cap)
    np.put_along_axis(out, order, fill, axis=0)
    k = np.clip((cum < demand[None, :] - 1e-6).sum(axis=0), 0, cap.shape[0] - 1)
    return out, ms[k, np.arange(cap.shape[1])]


def _decompose(P, D, lam):
    """soco-89 §2.1: $/MWh contribution of the low 40 % / top 20 % lambda hours."""
    W = D / D.sum()
    gap = W * (P - lam)
    q = np.quantile(lam, [0.4, 0.8])
    return dict(
        low40=round(float(gap[lam <= q[0]].sum()), 2),
        top20=round(float(gap[lam > q[1]].sum()), 2),
        total=round(float(gap.sum()), 2),
    )


def hydro_shape_arm(year: int, cache: Path) -> dict:
    """Upper bound: the model's daily hydro + PS discharge MWh on the MEASURED shape.

    Per calendar day the model's discharge-side energy (conventional hydro + pumped
    storage discharge) is redistributed over the day's hours in proportion to EIA-930
    ``NG: WAT`` (+ ``NG: PS`` discharge once split); pumping is left as solved. The
    thermal residual moves by the difference and is re-stacked greedily (the soco-90
    instrument: non-must-run fossil, ``mc_base``, ``pmax x availability``); the greedy
    price delta is added to the LP price and re-scored through ``calibration_verdict``.
    Perfect hindsight on the shape, so it bounds what any hydro-shape mechanism can do.
    """
    import calibration_verdict as cv

    f = rebuild(year, cache)
    ch = pd.read_parquet(SPAN / f"hourly/class_hourly_{year}.parquet")
    hyd = (
        ch[(ch["pass"] == "P1") & (ch.klass == "hydro")]
        .set_index("hour")
        .mw.reindex(range(T), fill_value=0.0)
        .to_numpy(float)
    )
    stg = pd.read_parquet(SPAN / f"hourly/storage_{year}.parquet")
    ps = stg[(stg["pass"] == "P1") & (stg.tech == "pumped_storage")].set_index("hour")
    psd = ps.discharge_mw.reindex(range(T), fill_value=0.0).to_numpy(float)
    H = hyd + psd
    e = eia930(year)
    A = e["NG: WAT"].to_numpy(float) + np.clip(
        np.nan_to_num(e["NG: PS"].to_numpy(float)), 0, None
    )
    A = np.clip(A, 0, None)
    Hd, Ad = H.reshape(-1, 24), A.reshape(-1, 24)
    tgt = np.where(
        Ad.sum(1, keepdims=True) > 0,
        Hd.sum(1, keepdims=True) * Ad / np.maximum(Ad.sum(1, keepdims=True), 1e-9),
        Hd,
    ).ravel()
    dH = tgt - H
    # pumping: where EIA-930 reports NG: PS (2025; from 2024-07-15), reshape the
    # model's daily charge MWh onto the measured charge shape too
    psc = ps.charge_mw.reindex(range(T), fill_value=0.0).to_numpy(float)
    mps = e["NG: PS"].to_numpy(float)
    mchg = np.clip(-np.nan_to_num(mps), 0, None).reshape(-1, 24)
    split_day = np.isfinite(mps).reshape(-1, 24).all(1) & (mchg.sum(1) > 0)
    Cd = psc.reshape(-1, 24)
    ctgt = np.where(
        split_day[:, None],
        Cd.sum(1, keepdims=True) * mchg / np.maximum(mchg.sum(1, keepdims=True), 1e-9),
        Cd,
    ).ravel()
    dH = dH - (ctgt - psc)  # less pumping = more net supply

    band = f["band"]
    sel = np.isin(f["klass"], RESTACK) & (band != "mustrun")
    cap, mc, k = (
        f["cap"][sel].astype(float),
        f["mc"][sel].astype(float),
        f["klass"][sel],
    )
    cb = pd.read_parquet(SPAN / f"hourly/class_band_hourly_{year}.parquet")
    cb = cb[(cb["pass"] == "P1") & cb.klass.isin(RESTACK) & (cb.band != "mustrun")]
    dem0 = cb.groupby("hour").mw.sum().reindex(range(T), fill_value=0.0).to_numpy()
    dem1 = np.clip(dem0 - dH, 0, None)
    g0, p0 = _greedy(dem0, cap, mc)
    g1, p1 = _greedy(dem1, cap, mc)
    dp = p1 - p0
    dcls = {c: float((g1[k == c] - g0[k == c]).sum() / 1e6) for c in set(k)}

    s = pd.read_parquet(SPAN / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"].sort_values(["zone", "hour"])
    zn = sorted(s.zone.unique())
    Pz = np.vstack([s[s.zone == z].price.to_numpy() for z in zn])
    Dz = np.vstack([s[s.zone == z].demand.to_numpy() for z in zn])
    D = Dz.sum(0)
    P = (Pz * Dz).sum(0) / D
    lam = lambda_cst(year)
    q = np.quantile(lam, [0.4, 0.8])
    lo, hi = lam <= q[0], lam > q[1]

    art = cv.load_artifacts("2026-09-29-soco87-gas-hh-monthly")
    ypay = copy.deepcopy(art["payload"]["years"][str(year)])
    yb = art["bench"].get(year, {})
    base = {
        r["key"]: r
        for r in cv.score_fuelmix(year, ypay, yb, "SOCO")
        if r["status"] != "SKIPPED"
    }
    c3a0 = cv.score_price_mean(year, ypay, yb, "SOCO")
    c3b0 = cv.score_price_shape(year, ypay, yb, "SOCO")
    for c, dv in dcls.items():
        if c in ypay["gmModel"]:
            ypay["gmModel"][c] = float(ypay["gmModel"][c]) + dv
    if "hydro" in ypay["gmModel"]:
        ypay["gmModel"]["hydro"] = float(ypay["gmModel"]["hydro"])  # energy unchanged
    for zi, z in enumerate(zn):
        if z not in ypay["lmp"]:
            continue
        d, zz = Dz[zi], ypay["lmp"][z]
        zz["p"] = float(zz["p"]) + float((dp * d).sum() / d.sum())
        zz["pMon"] = [
            float(pm)
            + float((dp[MONTH == i] * d[MONTH == i]).sum() / d[MONTH == i].sum())
            if pm is not None
            else None
            for i, pm in enumerate(zz["pMon"])
        ]
    arm = {
        r["key"]: r
        for r in cv.score_fuelmix(year, ypay, yb, "SOCO")
        if r["status"] != "SKIPPED"
    }
    c3a1 = cv.score_price_mean(year, ypay, yb, "SOCO")
    c3b1 = cv.score_price_shape(year, ypay, yb, "SOCO")
    b0, b1 = _decompose(P, D, lam), _decompose(P + dp, D, lam)
    return dict(
        year=year,
        dH_low40_mw=round(float(dH[lo].mean()), 0),
        dH_top20_mw=round(float(dH[hi].mean()), 0),
        dp_low40=round(float(dp[lo].mean()), 2),
        dp_top20=round(float(dp[hi].mean()), 2),
        c3a=f"{c3a0['magnitude']} {c3a0['status']} -> {c3a1['magnitude']} {c3a1['status']}",
        c3b=f"{c3b0.get('model')} {c3b0['status']} -> {c3b1.get('model')} {c3b1['status']}",
        low40=f"{b0['low40']} -> {b1['low40']}",
        top20=f"{b0['top20']} -> {b1['top20']}",
        c1=" | ".join(
            f"{c} {base[c]['magnitude']}->{arm[c]['magnitude']} {arm[c]['status']}"
            for c in C1_KEYS
            if c in base and c in arm
        ),
    )


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(YEARS))
    ap.add_argument("--hydro-shape-arm", action="store_true")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    if a.hydro_shape_arm:
        rows = [hydro_shape_arm(y, a.out) for y in a.years]
        for r in rows:
            print(json.dumps(r), flush=True)
        pd.DataFrame(rows).to_csv(a.out / "soco91_hydro_shape_arm.csv", index=False)
        return
    for y in a.years:
        r = census(y, a.out)
        (a.out / f"census91_{y}.json").write_text(json.dumps(r, indent=1))
        print(
            y,
            "C3a",
            r["c3a_pct"],
            "matched",
            r["matched_share"],
            "ambig",
            r["ambiguous_share"],
            "oom low40",
            r["oom_mw"]["low40"],
            flush=True,
        )


if __name__ == "__main__":
    main()
