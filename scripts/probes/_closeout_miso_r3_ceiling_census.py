#!/usr/bin/env python3
"""Closeout MISO wave 1 (ZERO LP): census of the owner-ruled R-3 coal take ceiling.

Owner ruling R-3 (``docs/backcast-closeout-plan-2026-10.md`` §5.0): EIA-923
monthly coal receipts and month-end stocks are admissible as a BACKCAST
fuel-availability overlay (rule 13) — a per-plant monthly take ceiling
(receipts + stock envelope with a declared ``stock_min``), never the burn; the
forward analogue is the contract delivery rate.

THE CANDIDATE (per coal yard row ``y`` of the keeper's
``build_coal_plant_budget`` partition, month ``m`` of solve year ``Y``)::

    C[y, m] = R_meas[y, m] + max(0, S_meas[y, m-1] - S_min[y])      (MMBtu)

* ``R_meas`` — the yard's own same-year EIA-923 Page 5 receipts, every lot at
  its reported heat content (``coal_receipts``); a filer month with no lot is 0.
* ``S_meas[m-1]`` — the yard's EIA-923 Sch. 2 month-end stock (``coal_stocks``,
  all ranks summed; ``m = 1`` reads Dec ``Y-1``), converted at the yard's
  quantity-weighted Page 5 heat content over ``Y-2..Y-1`` (the budget's own
  ``hc``; fleet value when the yard has none). A missing ``S_meas[m-1]`` leaves
  that cell unconstrained (never substituted).
* ``S_min`` — DECLARED, not searched: miso-289's committed identification,
  ``S_min = d_min / 365 * R`` with ``d_min`` the yard's minimum month-end days on
  hand over ``[Y-3, Y-1]`` and ``R`` its prior-years receipts rate already in
  the keeper budget (``scripts/probes/_miso289_minstock_precheck.py::
  yard_min_days`` / ``build_year``). A yard with no identified ``d_min`` gets
  ``S_min = 0`` (miso-289's convention).

It is NOT cumulative and the stock state is MEASURED, so unlike the four killed
pile variants (miso-287..290, FINDING-miso290 §6) the LP cannot bank: no month's
row depends on the model's own burn in another month. Identity worth stating:
``C - burn_actual = S_meas[m] - S_min``, so the ceiling binds the REAL burn only
where the measured pile closed a month below ``S_min``.

Arms (rule 19 [R-ONE-MECH]):

* ``INC``  keeper rows: pooled monthly ``B/12`` limb (``build_coal_fuel_budget``)
  + per-yard ANNUAL rows (``build_coal_plant_budget``), floors reconciled to the
  annual rows (``reconcile_floors_to_yard_budget``).
* ``CAND`` the R-3 ceiling REPLACES the pooled ``B/12`` limb AND the per-yard
  annual rows. Reason from the code: ``build_coal_plant_budget``'s docstring
  defines the yard rows as "the plant grain of build_coal_fuel_budget's annual
  identity ... a refinement of one identity, never a second mechanism"; both
  are the prior-years fuel-availability identity (stock + prior receipts rate)
  and R-3 is the measured overlay of that same phenomenon (coal available at
  the yard), so keeping either would stack two availability limbs. Floors are
  reconciled per (yard, month) row to ``C`` (the same scale-to-fit rule as
  ``reconcile_floors_to_yard_budget``, applied at the row grain). Keeper offers
  (no take floor is added, so the take-or-pay discounts stay as in the keeper).

Emulator: the miso-288/289/290 zero-LP dual emulator (P1 bid stack ``mc_base`` +
monthly startup markup, cleared hour-by-hour at the keeper's P1 thermal
quantity by ``clear_block``; binding rows enter as ``lam * HR`` offer adders),
with miso-290's revised step rule (adaptive per-coordinate steps, tail dual
averaging, lowest-residual point returned). It clears ONE system price; the
price census therefore reports CAND - INC deltas and applies them as a STATIC
OVERLAY: keeper P1 zonal hourly price + emulator ``(CAND - INC)[t]`` in every
zone, re-aggregated to ``pMon``/``p`` with the keeper's own zonal demand and
scored with ``calibration_verdict.score_price_shape`` / ``score_price_mean``
(zone-resolved ``rt_lw`` basis, coverage mask). No network, flow, commitment or
year-evolution feedback is captured.

EX-ANTE READ (written into this docstring before any CAND number was computed):

* K1 binds in fall 2021: CAND ceiling binds (``lam > 0``) on >= 5 yard rows in
  Sep-Nov 2021 AND Sep-Nov 2021 CAND coal <= INC coal - 1.0 TWh.
* K2 summer 2021 near-slack: CAND ceiling binds on <= 5 yard rows in Jun-Aug
  2021 and Jun-Aug 2021 CAND coal >= INC coal - 0.5 TWh.
* K3 no gate crossing: no year 2019-2024 has a static C3a or C3b move that
  turns a PASS into a FAIL.
* K4 where it does not bind: in every year-month with no binding CAND row, the
  CAND monthly coal deviates from keeper P1 by <= 1.5 TWh.
* Expectation (not a gate): because ``C - burn_actual = S_meas[m] - S_min`` and
  the 2021 fleet held ~57.6 days against a MW-weighted ``d_min`` of 46.1
  (FINDING-miso295 §4.5), the fall-2021 ceiling sits ~11 days of burn above the
  actual burn — larger than the keeper's +1.7/+3.6/+3.3 TWh fall overburn — so
  aggregate slack in fall 2021 with binding only at yards that individually
  drew near their own ``d_min`` is the likely outcome; K1 may fail.

2025 has no plant-level stocks file (``data/raw/coal-stocks/README.md``): the
ceiling is unidentifiable there and the year is reported, not run.

Output: ``results/phase0/miso/_closeout_miso_r3_ceiling_census.json``.
Rule 13: nothing here feeds a solve. Usage::

    uv run python scripts/probes/_closeout_miso_r3_ceiling_census.py --years 2021
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso289_minstock_precheck as m289  # noqa: E402
from scripts.probes._miso287_carry_precheck import clear_block  # noqa: E402
from scripts.probes._miso287_p1_residual import (  # noqa: E402
    KEEPER,
    NIGHT_H,
    NON_LP,
    T,
    run_ratio,
)
from scripts.probes._miso288_yard_precheck import bench_coal_monthly  # noqa: E402

OUT = REPO / "results/phase0/miso/_closeout_miso_r3_ceiling_census.json"
RUN_ID = "2026-09-28-miso-280-splitremap"
N_RATE_YEARS = 2  # the budget's own heat-content window (build_coal_plant_budget)
MAX_IT = 240  # miso-290 solver settings, unchanged
TOL = 0.01
STEP0 = 2.0
MONTH_NAMES = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
T0 = time.time()


def measured_ceiling(fa, y: int, keys, s_min: np.ndarray) -> dict:
    """R-3 ceiling ``C (n_rows, 12)`` MMBtu plus its parts, rows aligned to ``keys``."""
    from market_sim.data.coal_fuel_inventory import coal_yard_groups
    from market_sim.data.coal_receipts import load_coal_receipts
    from market_sim.data.coal_stocks import load_coal_stocks

    yards = coal_yard_groups(fa)
    st = load_coal_stocks([y - 1, y])
    rc_y = load_coal_receipts([y])
    rc_p = load_coal_receipts([y - k for k in range(1, N_RATE_YEARS + 1)])
    s = st.groupby(["plant_id", "year", "month"])["ending_stock_tons"].sum()
    rc_y = rc_y.assign(_m=rc_y["quantity_tons"] * rc_y["heat_content_mmbtu_per_ton"])
    r_mon = rc_y.groupby(["plant_id", "month"])["_m"].sum()
    rc_p = rc_p.assign(_m=rc_p["quantity_tons"] * rc_p["heat_content_mmbtu_per_ton"])
    p_t = rc_p.groupby("plant_id")["quantity_tons"].sum()
    p_m = rc_p.groupby("plant_id")["_m"].sum()
    fleet_hc = float(rc_p["_m"].sum() / rc_p["quantity_tons"].sum())
    n = len(keys)
    S = np.full((n, 13), np.nan)  # col 0 = Dec(Y-1), col m = end of month m
    R = np.zeros((n, 12))
    hc = np.full(n, fleet_hc)
    for i, key in enumerate(keys):
        ids = yards.get(int(key), {int(key)})
        tons = sum(float(p_t.get(pid, 0.0)) for pid in ids)
        if tons > 0:
            hc[i] = sum(float(p_m.get(pid, 0.0)) for pid in ids) / tons
        for col, (yy, mm) in enumerate([(y - 1, 12)] + [(y, k) for k in range(1, 13)]):
            vals = [s.get((pid, yy, mm)) for pid in ids]
            vals = [v for v in vals if v is not None]
            if vals:
                S[i, col] = float(sum(vals))
        for mm in range(1, 13):
            R[i, mm - 1] = sum(float(r_mon.get((pid, mm), 0.0)) for pid in ids)
    S_mm = S * hc[:, None]
    head = np.maximum(S_mm[:, :12] - s_min[:, None], 0.0)
    C = R + head  # NaN where S[m-1] is missing -> cell unconstrained
    burn_act = S_mm[:, :12] + R - S_mm[:, 1:]
    return {"C": C, "R": R, "S_mm": S_mm, "hc": hc, "burn_act": burn_act}


def solve_rows(bid, mg, flex, q, month_idx, gi, grp, cf, cm, ca, pool):
    """Dual emulator: per-yard monthly rows ``cm``, per-yard annual rows ``ca``, pool.

    ``cm`` ``(n_rows, 12)`` MMBtu (NaN = inactive) or ``None``; ``ca`` ``(n_rows,)``
    or ``None``; ``pool`` ``(add_pool (n,), cap (12,))`` or ``None``. Step rule
    and returned point as miso-290 ``solve_duals`` (no floor family).
    """
    n = bid.shape[0]
    n_rows = cm.shape[0] if cm is not None else ca.shape[0]
    act_m = np.isfinite(cm) if cm is not None else np.zeros((n_rows, 12), bool)
    cmz = np.nan_to_num(cm) if cm is not None else np.zeros((n_rows, 12))
    sc_m = np.maximum(np.where(act_m, cmz, 0.0).max(axis=1), 1.0)
    act_a = np.isfinite(ca) if ca is not None else np.zeros(n_rows, bool)
    caz = np.nan_to_num(ca) if ca is not None else np.zeros(n_rows)
    sc_a = np.maximum(caz, 1.0)
    lm, la, lp = np.zeros((n_rows, 12)), np.zeros(n_rows), np.zeros(12)
    sm, sa = np.full((n_rows, 12), STEP0), np.full(n_rows, STEP0)
    pg_m, pg_a = np.zeros((n_rows, 12)), np.zeros(n_rows)
    sp, prev_p = np.full(12, 0.5), np.zeros(12)
    acc = [np.zeros_like(lm), np.zeros_like(la), np.zeros(12), 0]
    best = (np.inf, None, "")

    def offsets(lm_, la_, lp_):
        add = np.zeros((n, 12))
        np.add.at(add, gi, cf[:, None] * (lm_[grp] + la_[grp][:, None]))
        off = add[:, month_idx]
        if pool is not None:
            off = off + pool[0][:, None] * lp_[month_idx][None, :]
        return off

    def evaluate(lm_, la_, lp_):
        price, d = clear_block(bid + offsets(lm_, la_, lp_), mg, flex, q)
        by_m = np.zeros((gi.size, 12))
        np.add.at(by_m.T, month_idx, d[gi].T)
        burn = np.zeros((n_rows, 12))
        np.add.at(burn, grp, cf[:, None] * by_m)
        g_m = np.where(act_m, (burn - cmz) / sc_m[:, None], 0.0)
        g_a = np.where(act_a, (burn.sum(1) - caz) / sc_a, 0.0)
        v_m = np.where(lm_ > 0, np.abs(g_m), np.maximum(g_m, 0.0))
        v_a = np.where(la_ > 0, np.abs(g_a), np.maximum(g_a, 0.0))
        if pool is not None:
            pbm = pd.Series(pool[0] @ d).groupby(month_idx).sum().to_numpy()
            gp = (pbm - pool[1]) / pool[1]
            vp = np.where(lp_ > 0, np.abs(gp), np.maximum(gp, 0.0))
        else:
            gp = vp = np.zeros(12)
        worst = float(max(v_m.max(initial=0.0), v_a.max(initial=0.0), vp.max()))
        return worst, g_m, g_a, gp, burn

    it, worst = 0, np.inf
    for it in range(MAX_IT):
        worst, g_m, g_a, gp, _b = evaluate(lm, la, lp)
        if worst < best[0]:
            best = (worst, (lm.copy(), la.copy(), lp.copy()), f"iterate {it}")
        if it % 10 == 0:
            print(
                f"  it {it} worst {worst:.4f} m>0 {(lm > 0).sum()} a>0 {(la > 0).sum()} "
                f"t {time.time() - T0:.0f}s",
                flush=True,
            )
        if worst <= TOL:
            break
        sm = np.where(np.sign(g_m) != np.sign(pg_m), sm * 0.5, np.minimum(sm * 1.1, STEP0))
        sa = np.where(np.sign(g_a) != np.sign(pg_a), sa * 0.5, np.minimum(sa * 1.1, STEP0))
        lm = np.where(act_m, np.maximum(0.0, lm + sm * np.clip(g_m, -1, 1)), 0.0)
        la = np.where(act_a, np.maximum(0.0, la + sa * np.clip(g_a, -1, 1)), 0.0)
        pg_m, pg_a = g_m, g_a
        if pool is not None:
            sp = np.where(np.sign(gp) != np.sign(prev_p), sp * 0.5, sp * 1.2)
            lp = np.maximum(0.0, lp + sp * np.clip(gp, -1, 1) * 10.0)
            prev_p = gp
        if it >= MAX_IT // 2:
            acc[0] += lm
            acc[1] += la
            acc[2] += lp
            acc[3] += 1
    stat = {"iterations": it + 1, "last_iterate_residual": round(worst, 4)}
    if acc[3]:
        avg = (acc[0] / acc[3], acc[1] / acc[3], acc[2] / acc[3])
        w_avg = evaluate(*avg)[0]
        stat["averaged_residual"] = round(w_avg, 4)
        if w_avg < best[0]:
            best = (w_avg, avg, "tail average")
    lm, la, lp = best[1]
    _w, _gm, _ga, _gp, burn = evaluate(lm, la, lp)
    stat.update(max_rel_violation=round(best[0], 4), returned=best[2])
    return offsets(lm, la, lp), lm, la, lp, burn, stat


def reconcile_floors_monthly(mg, gi, grp, cf, cm, month_idx) -> int:
    """Scale floors per (yard, month) row to fit ``cm``; returns rows scaled."""
    n_rows = cm.shape[0]
    by_m = np.zeros((gi.size, 12))
    np.add.at(by_m.T, month_idx, mg[gi].T)
    draw = np.zeros((n_rows, 12))
    np.add.at(draw, grp, cf[:, None] * by_m)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.where(
            np.isfinite(cm) & (draw > cm), np.maximum(cm, 0.0) / draw, 1.0
        )
    s = np.nan_to_num(s, nan=1.0)
    mg[gi] *= s[grp][:, month_idx]
    return int((s < 1.0).sum())


def static_scores(y: int, delta: np.ndarray, art: dict) -> dict:
    """Keeper C3a/C3b, and with the emulator's hourly ``delta`` added in every zone."""
    import calibration_verdict as cv

    ypay = art["payload"]["years"][str(y)]
    ybench = art["bench"].get(y, {})
    s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    dem = s.pivot(index="hour", columns="zone", values="demand").reindex(range(T))
    mon = np.asarray(
        (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(T), unit="h")).month
        - 1
    )
    mon = np.minimum(mon, 11)
    adj = copy.deepcopy(ypay)
    for zn, z in adj["lmp"].items():
        if zn not in dem.columns:
            continue
        d = dem[zn].fillna(0.0).to_numpy()
        if d.sum() <= 0:
            continue
        z["p"] = z["p"] + float((d * delta).sum() / d.sum())
        pm = list(z["pMon"])
        for m in range(12):
            sel = mon == m
            dd = d[sel].sum()
            if pm[m] is not None and dd > 0:
                pm[m] = pm[m] + float((d[sel] * delta[sel]).sum() / dd)
        z["pMon"] = pm
    out = {}
    for tag, yp in (("keeper", ypay), ("static_cand", adj)):
        c3a = cv.score_price_mean(y, yp, ybench, "MISO")
        c3b = cv.score_price_shape(y, yp, ybench, "MISO")
        out[tag] = {
            "C3a": c3a.get("magnitude"),
            "C3a_status": c3a.get("status"),
            "C3a_model": c3a.get("model"),
            "C3a_actual": c3a.get("actual"),
            "C3b": c3b.get("model"),
            "C3b_status": c3b.get("status"),
        }
    # Model monthly (system load-weighted) and actual, to locate the C3b change.
    def sysmon(yp):
        vals = []
        for m in range(12):
            pr = [
                (z["pMon"][m], z["dMon"][m])
                for z in yp["lmp"].values()
                if z["pMon"][m] is not None
            ]
            w = sum(b for _, b in pr)
            vals.append(round(sum(a * b for a, b in pr) / w, 2) if w > 0 else None)
        return vals

    out["model_mon_keeper"] = sysmon(ypay)
    out["model_mon_static_cand"] = sysmon(adj)
    out["actual_rt_lw_mon"] = (ybench.get("avgLMP") or {}).get("rt_lw_mon")
    return out


def c3b_share(sc: dict, months: list[int]) -> dict:
    """SSE share of ``months`` (0-based) and the static change it carries."""
    a = sc["actual_rt_lw_mon"]
    k, c = sc["model_mon_keeper"], sc["model_mon_static_cand"]
    cells = [i for i in range(12) if a and a[i] is not None and k[i] is not None]
    sse_k = {i: (k[i] - a[i]) ** 2 for i in cells}
    sse_c = {i: (c[i] - a[i]) ** 2 for i in cells}
    tot_k = sum(sse_k.values())
    return {
        "sse_share_keeper": round(sum(sse_k[i] for i in months if i in sse_k) / tot_k, 3),
        "sse_window_keeper": round(sum(sse_k[i] for i in months if i in sse_k), 2),
        "sse_window_cand": round(sum(sse_c[i] for i in months if i in sse_c), 2),
        "sse_total_keeper": round(tot_k, 2),
        "sse_total_cand": round(sum(sse_c.values()), 2),
        # SSE that must leave for NRMSE to reach the cap: NRMSE ∝ sqrt(SSE).
        "sse_needed_for_cap": round(tot_k * (1 - (0.20 / 0.201) ** 2), 3),
    }


def run_year(y: int, art: dict) -> dict:
    """Identification + price census for one year."""
    from market_sim.data.coal_fuel_inventory import reconcile_floors_to_yard_budget
    from market_sim.model.commitment import compute_monthly_markup

    b = m289.build_year(y)
    st, fa = b["st"], b["fa"]
    cfg, fleet = st["config"], st["fleet"]
    ygi, ybud, _ym, ycf, ygrp, yprov = b["yb"]
    ygi, ygrp, ycf = np.asarray(ygi), np.asarray(ygrp), np.asarray(ycf, float)
    keys = yprov.yard_keys
    month_idx = b["month_idx"]
    ce = measured_ceiling(fa, y, keys, b["s_min"])
    C = ce["C"]
    n = len(fa.pmax)
    pmax = np.asarray(fa.pmax, float)
    row_mw = np.bincount(ygrp, weights=pmax[ygi], minlength=ybud.shape[0])

    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, T, axis=1)
    cap = pmax[:, None] * np.asarray(fa.availability, float)
    mg_raw = np.array(np.broadcast_to(np.asarray(fa.min_gen, float), cap.shape))
    s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    pm = s[(s["pass"] == "P1") & (s.zone == "MISO-Illinois")].sort_values("hour")
    pm = pm.price.to_numpy()
    ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
    ch_lp = ch[(ch["pass"] == "P1") & ~ch.klass.astype(str).isin(NON_LP)]
    q = ch_lp.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
    night = np.arange(T) % 24 < NIGHT_H

    mg_inc = mg_raw.copy()
    reconcile_floors_to_yard_budget(mg_inc, ygi, ybud, ycf, ygrp)
    mg_inc = np.minimum(mg_inc, cap)
    _, d0 = clear_block(mc, mg_inc, cap - mg_inc, q)
    mk = compute_monthly_markup(
        fleet,
        fa,
        d0,
        T,
        gas_st_season_spread=cfg.gas_st_startup_spread,
        gas_st_startup_cost=getattr(cfg, "gas_st_startup_cost", False),
        chp_startup_covered=getattr(cfg, "chp_startup_covered", False),
        coal_warm_committed=getattr(cfg, "coal_warm_committed", False),
        run_ratio_t=run_ratio(st)
        if getattr(cfg, "tranche_startup_conditional_runs", False)
        else None,
    )
    bid = mc + mk
    pgi, pbud, _pm, pcf, _pg, _pp = b["pb"]
    add_pool = np.zeros(n)
    add_pool[pgi] = pcf
    pool_cap = np.asarray(pbud, float).reshape(-1)
    is_coal = np.zeros(n, bool)
    is_coal[pgi] = True
    is_coal[ygi] = True
    hr = np.asarray(fa.heat_rate, float)

    res, burns, prices = {}, {}, {}
    for arm in ("INC", "CAND"):
        print(y, arm, flush=True)
        if arm == "INC":
            mg_a, cm, ca, pl = mg_inc, None, ybud[:, 0], (add_pool, pool_cap)
            n_scaled = None
        else:
            mg_a = mg_raw.copy()
            n_scaled = reconcile_floors_monthly(mg_a, ygi, ygrp, ycf, C, month_idx)
            mg_a = np.minimum(mg_a, cap)
            cm, ca, pl = C, None, None
        flex = cap - mg_a
        off, lm, la, lp, burn, stat = solve_rows(
            bid, mg_a, flex, q, month_idx, ygi, ygrp, ycf, cm, ca, pl
        )
        price, d = clear_block(bid + off, mg_a, flex, q)
        coal = pd.Series(d[is_coal].sum(0)).groupby(month_idx).sum().to_numpy() / 1e6
        coal_mmbtu = (
            pd.Series((hr[is_coal, None] * d[is_coal]).sum(0))
            .groupby(month_idx)
            .sum()
            .to_numpy()
        )
        bind = lm > 0
        prices[arm], burns[arm] = price, burn
        res[arm] = {
            "night_median": round(float(np.median(price[night])), 2),
            "mean": round(float(price.mean()), 2),
            "night_median_by_month": [
                round(float(np.median(price[night & (month_idx == m)])), 2)
                for m in range(12)
            ],
            "mean_by_month": [
                round(float(price[month_idx == m].mean()), 2) for m in range(12)
            ],
            "coal_twh_month": [round(float(v), 2) for v in coal],
            "coal_twh_annual": round(float(coal.sum()), 2),
            "coal_mmbtu_m_month": [round(float(v) / 1e6, 1) for v in coal_mmbtu],
            "lam_pool": [round(float(v), 3) for v in lp],
            "rows_annual_binding": int((la > 0).sum()),
            "rows_month_binding_by_month": [int(v) for v in bind.sum(0)],
            "binding_mw_by_month": [
                round(float(row_mw[bind[:, m]].sum()), 0) for m in range(12)
            ],
            "lam_month_mw_weighted_by_month": [
                round(
                    float((lm[:, m] * row_mw).sum() / max(row_mw[bind[:, m]].sum(), 1.0)),
                    3,
                )
                for m in range(12)
            ],
            "rows_floor_scaled": n_scaled,
            **stat,
        }
        print(y, arm, json.dumps({k: res[arm][k] for k in ("night_median", "mean", "coal_twh_annual", "max_rel_violation")}), flush=True)

    # Identification census.
    act = np.isfinite(C)
    rowed = act.all(axis=1)
    burn_inc = burns["INC"]
    short = np.where(act, np.maximum(burn_inc - np.nan_to_num(C), 0.0), 0.0)
    real_cut = np.where(act & np.isfinite(ce["burn_act"]), np.maximum(ce["burn_act"] - np.nan_to_num(C), 0.0), 0.0)
    coal_p1 = (
        ch[(ch["pass"] == "P1") & ch.klass.astype(str).str.startswith("COAL")]
        .groupby("hour")
        .mw.sum()
        .reindex(range(T))
        .fillna(0)
        .groupby(month_idx)
        .sum()
        / 1e6
    ).to_numpy()
    # Keeper class_hourly coal x heat rate: class HR = pmax-weighted HR of the
    # fleet's coal units in that class (declared approximation; class_hourly
    # carries MW only).
    pg = getattr(fa, "plant_group", None)
    cls = np.asarray(pg if pg is not None else [], dtype=object).astype(str)
    ch_c = ch[(ch["pass"] == "P1") & ch.klass.astype(str).str.startswith("COAL")]
    p1_mmbtu = np.zeros(12)
    hr_coal_w = float((hr[is_coal] * pmax[is_coal]).sum() / pmax[is_coal].sum())
    for k, g in ch_c.groupby(ch_c.klass.astype(str)):
        sel = is_coal & (cls == k) if cls.size == n else np.zeros(n, bool)
        hk = (
            float((hr[sel] * pmax[sel]).sum() / pmax[sel].sum()) if sel.any() else hr_coal_w
        )
        e = g.groupby("hour").mw.sum().reindex(range(T)).fillna(0).groupby(month_idx).sum().to_numpy()
        p1_mmbtu += e * hk
    bench = bench_coal_monthly(y)
    census = {
        "yard_rows_keeper": int(ybud.shape[0]),
        "rows_all_12_cells": int(rowed.sum()),
        "rows_any_cell": int(act.any(axis=1).sum()),
        "mw_all_12_cells": round(float(row_mw[rowed].sum()), 0),
        "mw_yard_rows": round(float(row_mw.sum()), 0),
        "mw_coal_fleet": round(float(pmax[is_coal].sum()), 0),
        "rows_with_d_min": int(np.isfinite(b["d_min"]).sum()),
        "d_min_mw_weighted": round(
            float(np.nansum(b["d_min"] * row_mw) / row_mw[np.isfinite(b["d_min"])].sum()), 1
        ),
        "s_min_mmbtu_m": round(float(b["s_min"].sum()) / 1e6, 1),
        "ceiling_sum_mmbtu_m_by_month": [
            round(float(np.nansum(C[:, m])) / 1e6, 1) for m in range(12)
        ],
        "receipts_mmbtu_m_by_month": [round(float(ce["R"][:, m].sum()) / 1e6, 1) for m in range(12)],
        "headroom_mmbtu_m_by_month": [
            round(float(np.nansum(C[:, m] - ce["R"][:, m])) / 1e6, 1) for m in range(12)
        ],
        "actual_burn_mmbtu_m_by_month": [
            round(float(np.nansum(ce["burn_act"][:, m])) / 1e6, 1) for m in range(12)
        ],
        "pool_B12_mmbtu_m_per_month": round(float(pool_cap[0]) / 1e6, 1),
        "yard_annual_sum_mmbtu_m": round(float(ybud.sum()) / 1e6, 1),
        "inc_rowed_burn_mmbtu_m_by_month": [
            round(float(burn_inc[:, m].sum()) / 1e6, 1) for m in range(12)
        ],
        "inc_all_coal_mmbtu_m_by_month": res["INC"]["coal_mmbtu_m_month"],
        "keeper_p1_coal_mmbtu_m_by_month_classHR": [round(float(v) / 1e6, 1) for v in p1_mmbtu],
        "cells_C_below_inc_burn_by_month": [int((short[:, m] > 0).sum()) for m in range(12)],
        "mw_C_below_inc_burn_by_month": [
            round(float(row_mw[short[:, m] > 0].sum()), 0) for m in range(12)
        ],
        "shortfall_vs_inc_mmbtu_m_by_month": [
            round(float(short[:, m].sum()) / 1e6, 2) for m in range(12)
        ],
        "cells_C_below_actual_burn_by_month": [int((real_cut[:, m] > 0).sum()) for m in range(12)],
        "shortfall_vs_actual_mmbtu_m_by_month": [
            round(float(real_cut[:, m].sum()) / 1e6, 2) for m in range(12)
        ],
    }
    delta = prices["CAND"] - prices["INC"]
    sc = static_scores(y, delta, art)
    out = {
        "census": census,
        "p1_night_median_illinois": round(float(np.median(pm[night])), 2),
        "p1_mean_illinois": round(float(pm.mean()), 2),
        "p1_night_median_by_month": [
            round(float(np.median(pm[night & (month_idx == m)])), 2) for m in range(12)
        ],
        "p1_mean_by_month": [round(float(pm[month_idx == m].mean()), 2) for m in range(12)],
        "coal_twh_p1_month": [round(float(v), 2) for v in coal_p1],
        "coal_twh_p1_annual": round(float(coal_p1.sum()), 2),
        "coal_twh_bench_month": [round(float(v), 2) for v in bench],
        "coal_twh_bench_annual": round(float(bench.sum()), 2),
        "delta_mean_by_month": [round(float(delta[month_idx == m].mean()), 2) for m in range(12)],
        "delta_night_mean_by_month": [
            round(float(delta[night & (month_idx == m)].mean()), 2) for m in range(12)
        ],
        "static_scores": sc,
        **res,
    }
    if y == 2021:
        out["c3b_2021_window"] = {
            "sep_nov": c3b_share(sc, [8, 9, 10]),
            "jun_aug": c3b_share(sc, [5, 6, 7]),
            "feb": c3b_share(sc, [1]),
        }
    # Kill-read helpers.
    cand_c, inc_c = np.array(res["CAND"]["coal_twh_month"]), np.array(res["INC"]["coal_twh_month"])
    nb = np.array(res["CAND"]["rows_month_binding_by_month"]) == 0
    out["k4_max_dev_vs_p1_nonbinding_months"] = (
        round(float(np.abs(cand_c - coal_p1)[nb].max()), 2) if nb.any() else None
    )
    out["max_dev_cand_vs_p1_all_months"] = round(float(np.abs(cand_c - coal_p1).max()), 2)
    out["max_dev_inc_vs_p1_all_months"] = round(float(np.abs(inc_c - coal_p1).max()), 2)
    out["runtime_s"] = round(time.time() - T0, 0)
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2025)))
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument(
        "--merge", type=Path, nargs="+", help="merge per-year shard outputs into OUT"
    )
    args = ap.parse_args()
    if args.merge:
        out = json.loads(OUT.read_text()) if OUT.exists() else {}
        for f in args.merge:
            out.update(json.loads(f.read_text()))
        OUT.write_text(json.dumps(dict(sorted(out.items())), indent=1))
        return 0
    import calibration_verdict as cv
    from scripts.probes import _miso271_cc_decomp as dec

    dec.KEEPER = KEEPER
    art = cv.load_artifacts(RUN_ID)
    out = json.loads(args.out.read_text()) if args.out.exists() else {}
    out["2025"] = {
        "unidentifiable": "no EIA-923 2025 plant-level coal stocks file "
        "(data/raw/coal-stocks/README.md); S_meas cannot be read"
    }
    for y in args.years:
        out[str(y)] = run_year(y, art)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(out, indent=1))
        print(y, "done", round(time.time() - T0), "s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
