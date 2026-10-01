#!/usr/bin/env python3
"""miso-289 (ZERO LP): per-yard monthly coal pile with a prior-years minimum stock.

Pre-registered in ``docs/records/miso/PRECOMMIT-miso289-minstock-pile-2026-09-30.md``. Two
modes:

``--census`` (identification only, no price): per year, per coal yard row of the
keeper's fleet-only rebuild, the yard's own minimum days of burn on hand over
the prior-years window and the resulting stock floor. Answers "is the
identification admissible and non-degenerate" before any price is computed.

default (the pre-check): the miso-288 INC/YARD dual emulator generalised to
cumulative per-yard month-end rows. Arms:

* ``INC``   incumbent: pooled monthly ``B/12`` rows + per-yard annual rows.
* ``PILE0`` diagnostic: per-yard cumulative pile (NWPP-NEXT-8 ceiling, ratable
  receipts), no stock floor, pooled limb off.
* ``CAND``  candidate: ``PILE0`` with each yard's pile held at or above
  ``S_floor = min(S_min, S_dec)`` at every month-end.

Identification (every input predates the solve year Y, rule 13):

* ``d_min`` = the yard's minimum month-end days on hand over the stock years
  available in ``[Y-3, Y-1]``; days on hand = month-end stock / (that year's
  mean daily implied burn), implied burn = ``stock[m-1] + receipts[m] -
  stock[m]`` (EIA-923 Sch. 2 + Sch. 5).
* ``S_min`` = ``d_min / 365 * R`` with ``R`` the yard's receipts rate already in
  its budget (``budget - S_dec``), MMBtu.
* ``S_floor`` = ``min(S_min, S_dec)``: a yard that opens below its target holds
  what it has and never draws further.

Output: ``results/calibration/_miso289_minstock_{census,precheck}.json``.
Rule 13: nothing here feeds a solve.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso287_carry_precheck import clear_block  # noqa: E402
from scripts.probes._miso287_p1_residual import (  # noqa: E402
    KEEPER,
    NIGHT_H,
    NON_LP,
    T,
    run_ratio,
)
from scripts.probes._miso288_yard_precheck import bench_coal_monthly  # noqa: E402

OUT_C = REPO / "results/phase0/miso/_miso289_minstock_census.json"
OUT_P = REPO / "results/phase0/miso/_miso289_minstock_precheck.json"
WINDOW = 3
MAX_IT = 200
TOL = 0.01
T0 = time.time()


def yard_min_days(yards: dict, keys, year: int, window: int = WINDOW):
    """Per yard row: minimum month-end days on hand over ``[year-window, year-1]``.

    Returns ``(d_min (n,), source years used)``; NaN where the yard has no
    usable stock year (the floor is then zero, never substituted).
    """
    from market_sim.data.coal_receipts import load_coal_receipts
    from market_sim.data.coal_stocks import load_coal_stocks

    src = list(range(year - window, year))
    st = load_coal_stocks(src + [year - window - 1])
    rc = load_coal_receipts(src)
    used = sorted(int(y) for y in st["year"].unique() if int(y) in src)
    s = st.groupby(["plant_id", "year", "month"])["ending_stock_tons"].sum()
    r = rc.groupby(["plant_id", "year", "month"])["quantity_tons"].sum()
    d_min = np.full(len(keys), np.nan)
    for i, key in enumerate(keys):
        ids = yards.get(int(key), {int(key)})
        best = np.inf
        for y in used:
            sm = np.full(13, np.nan)  # index 0 = Dec(y-1)
            rm = np.zeros(13)
            for pid in ids:
                for m in range(1, 13):
                    v = s.get((pid, y, m))
                    if v is not None:
                        sm[m] = (0.0 if np.isnan(sm[m]) else sm[m]) + v
                    rm[m] += r.get((pid, y, m), 0.0)
                v = s.get((pid, y - 1, 12))
                if v is not None:
                    sm[0] = (0.0 if np.isnan(sm[0]) else sm[0]) + v
            if np.isnan(sm[1:]).all():
                continue
            burn = sm[:-1] + rm[1:] - sm[1:]
            rate = np.nanmean(burn) * 12.0 if np.isfinite(burn).any() else np.nan
            if not np.isfinite(rate) or rate <= 0.0:
                continue
            doh = sm[1:] / (rate / 365.0)
            best = min(best, float(np.nanmin(doh)))
        if np.isfinite(best):
            d_min[i] = max(best, 0.0)
    return d_min, used


def build_year(y: int):
    """Fleet-only rebuild + the incumbent's budget inputs for ``y``."""
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.coal_fuel_inventory import (
        build_coal_fuel_budget,
        build_coal_monthly_pile,
        build_coal_plant_budget,
        coal_yard_groups,
    )

    dec.KEEPER = KEEPER
    hh = _henry_hub_actual(_load_reference(), y)
    st = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, {}))
    fa = st["fleet_arrays"]
    yb = build_coal_plant_budget(fa, y, hours=T)
    pb = build_coal_fuel_budget(fa, y, hours=T)
    ygi, ybud, _ym, ycf, ygrp, yprov = yb
    keys = yprov.yard_keys
    stock = np.asarray(yprov.stock_mmbtu, float)
    d_min, used = yard_min_days(coal_yard_groups(fa), keys, y)
    rate = ybud[:, 0] - stock
    s_min = np.where(np.isfinite(d_min), d_min / 365.0 * np.maximum(rate, 0.0), 0.0)
    s_floor = np.minimum(s_min, np.maximum(stock, 0.0))
    ceil0, _f, month_idx, _pv = build_coal_monthly_pile(
        fa, ygi, ygrp, ycf, ybud, tuple(stock), None, T
    )
    ceil1 = ceil0 - s_floor[:, None]
    return {
        "st": st,
        "fa": fa,
        "yb": yb,
        "pb": pb,
        "stock": stock,
        "d_min": d_min,
        "used": used,
        "s_min": s_min,
        "s_floor": s_floor,
        "ceil0": ceil0,
        "ceil1": ceil1,
        "month_idx": np.asarray(month_idx),
    }


def census(y: int, b: dict) -> dict:
    """Identification census for one year (no price)."""
    ygi, ybud = b["yb"][0], b["yb"][1]
    pmax = np.asarray(b["fa"].pmax, float)
    grp = np.asarray(b["yb"][4])
    mw = np.bincount(grp, weights=pmax[ygi], minlength=ybud.shape[0])
    d = b["d_min"]
    fin = np.isfinite(d)
    clip = b["s_min"] > b["stock"] + 1e-6
    return {
        "stock_years_used": b["used"],
        "yard_rows": int(ybud.shape[0]),
        "rows_identified": int(fin.sum()),
        "rows_identified_mw": round(float(mw[fin].sum()), 0),
        "rowed_mw": round(float(mw.sum()), 0),
        "d_min_p10_p50_p90": [
            round(float(v), 1) for v in np.percentile(d[fin], [10, 50, 90])
        ]
        if fin.any()
        else None,
        "d_min_mw_weighted": round(float((d[fin] * mw[fin]).sum() / mw[fin].sum()), 1)
        if fin.any()
        else None,
        "rows_opening_below_target": int(clip.sum()),
        "mw_opening_below_target": round(float(mw[clip].sum()), 0),
        "annual_budget_inc_mmbtu_m": round(float(ybud.sum()) / 1e6, 1),
        "stock_open_mmbtu_m": round(float(b["stock"].sum()) / 1e6, 1),
        "s_min_mmbtu_m": round(float(b["s_min"].sum()) / 1e6, 1),
        "s_floor_mmbtu_m": round(float(b["s_floor"].sum()) / 1e6, 1),
        "annual_budget_cand_mmbtu_m": round(float(b["ceil1"][:, -1].sum()) / 1e6, 1),
        "annual_cut_pct": round(
            100.0 * float(b["s_floor"].sum()) / float(ybud.sum()), 1
        ),
    }


def reconcile_monthly(mg, gi, grp, cf, ceil, month_idx):
    """Scale each yard's floors so their cumulative draw fits every month-end ceiling."""
    n_rows, n_m = ceil.shape
    by_m = np.zeros((gi.size, n_m))
    np.add.at(by_m.T, month_idx, mg[gi].T)
    draw = np.zeros((n_rows, n_m))
    np.add.at(draw, grp, cf[:, None] * by_m)
    draw = np.cumsum(draw, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(draw > 0, np.maximum(ceil, 0.0) / draw, np.inf)
    s = np.minimum(1.0, ratio.min(axis=1))
    mg[gi] *= s[grp][:, None]
    return int((s < 1.0).sum())


def solve_lams(bid, mg, flex, q, month_idx, gi, grp, cf, ceil, pool):
    """Projected subgradient for yard rows (annual or cumulative month-end) + pooled.

    ``ceil`` is ``(n_rows, 12)`` cumulative MMBtu (annual rows: NaN except the
    last column). ``pool`` is ``(add_pool (n,), pool_cap (12,))`` or ``None``.
    """
    n, n_rows = bid.shape[0], ceil.shape[0]
    active = np.isfinite(ceil)
    lam = np.zeros((n_rows, 12))
    step = np.full((n_rows, 12), 0.5)
    prev = np.zeros((n_rows, 12))
    lp = np.zeros(12)
    sp = np.full(12, 0.5)
    prev_p = np.zeros(12)
    scale = np.maximum(np.nanmax(np.where(active, ceil, np.nan), axis=1), 1.0)
    worst = np.inf
    for it in range(MAX_IT):
        lc = np.cumsum(lam[:, ::-1], axis=1)[:, ::-1]  # sum over m >= month
        add = np.zeros((n, 12))
        np.add.at(add, gi, cf[:, None] * lc[grp])
        off = add[:, month_idx]
        if pool is not None:
            off = off + pool[0][:, None] * lp[month_idx][None, :]
        _, d = clear_block(bid + off, mg, flex, q)
        by_m = np.zeros((gi.size, 12))
        np.add.at(by_m.T, month_idx, d[gi].T)
        burn = np.zeros((n_rows, 12))
        np.add.at(burn, grp, cf[:, None] * by_m)
        burn = np.cumsum(burn, axis=1)
        g = np.where(active, (burn - np.nan_to_num(ceil)) / scale[:, None], 0.0)
        viol = np.where(lam > 0, np.abs(g), np.maximum(g, 0.0))
        if pool is not None:
            pbm = pd.Series(pool[0] @ d).groupby(month_idx).sum().to_numpy()
            gp = (pbm - pool[1]) / pool[1]
            vp = np.where(lp > 0, np.abs(gp), np.maximum(gp, 0.0))
        else:
            gp = vp = np.zeros(12)
        worst = float(max(viol.max(initial=0.0), vp.max()))
        print(
            f"  it {it} worst {worst:.4f} rows>0 {(lam.sum(1) > 0).sum()} "
            f"t {time.time() - T0:.0f}s",
            flush=True,
        )
        if worst <= TOL:
            break
        step = np.where(np.sign(g) != np.sign(prev), step * 0.5, step * 1.2)
        lam = np.where(
            active, np.maximum(0.0, lam + step * np.clip(g, -1, 1) * 10.0), 0.0
        )
        prev = g
        if pool is not None:
            sp = np.where(np.sign(gp) != np.sign(prev_p), sp * 0.5, sp * 1.2)
            lp = np.maximum(0.0, lp + sp * np.clip(gp, -1, 1) * 10.0)
            prev_p = gp
    lc = np.cumsum(lam[:, ::-1], axis=1)[:, ::-1]
    add = np.zeros((n, 12))
    np.add.at(add, gi, cf[:, None] * lc[grp])
    off = add[:, month_idx]
    if pool is not None:
        off = off + pool[0][:, None] * lp[month_idx][None, :]
    return off, lam, lp, {"iterations": it + 1, "max_rel_violation": round(worst, 4)}


def precheck(y: int, b: dict) -> dict:
    """INC / PILE0 / CAND emulation for one year."""
    from market_sim.data.coal_fuel_inventory import reconcile_floors_to_yard_budget
    from market_sim.model.commitment import compute_monthly_markup

    st, fa = b["st"], b["fa"]
    cfg, fleet = st["config"], st["fleet"]
    n = len(fa.pmax)
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, T, axis=1)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    mg_raw = np.array(np.broadcast_to(np.asarray(fa.min_gen, float), cap.shape))
    ygi, ybud, _ym, ycf, ygrp, _yp = b["yb"]
    ygi, ygrp, ycf = np.asarray(ygi), np.asarray(ygrp), np.asarray(ycf, float)
    month_idx = b["month_idx"]

    s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
    pm = (
        s[(s["pass"] == "P1") & (s.zone == "MISO-Illinois")]
        .sort_values("hour")
        .price.to_numpy()
    )
    ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
    ch_lp = ch[(ch["pass"] == "P1") & ~ch.klass.astype(str).isin(NON_LP)]
    q = ch_lp.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
    night = np.arange(T) % 24 < NIGHT_H

    # Markup from the incumbent's floors, shared by every arm (as miso-288).
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

    pgi, pbud, pmonth, pcf, _pg, _pp = b["pb"]
    add_pool = np.zeros(n)
    add_pool[pgi] = pcf
    pool = (add_pool, np.asarray(pbud, float).reshape(-1))
    is_coal = np.zeros(n, bool)
    is_coal[pgi] = True
    is_coal[ygi] = True
    ann = np.full((ybud.shape[0], 12), np.nan)
    ann[:, -1] = ybud[:, 0]

    arms = {
        "INC": (ann, pool, mg_inc),
        "PILE0": (b["ceil0"], None, None),
        "CAND": (b["ceil1"], None, None),
    }
    pmax = np.asarray(fa.pmax, float)
    res = {}
    for arm, (ceil, pl, mg_a) in arms.items():
        print(y, arm, flush=True)
        n_scaled = None
        if mg_a is None:
            mg_a = mg_raw.copy()
            n_scaled = reconcile_monthly(mg_a, ygi, ygrp, ycf, ceil, month_idx)
            mg_a = np.minimum(mg_a, cap)
        flex = cap - mg_a
        off, lam, lp, stat = solve_lams(
            bid, mg_a, flex, q, month_idx, ygi, ygrp, ycf, ceil, pl
        )
        price, d = clear_block(bid + off, mg_a, flex, q)
        coal = pd.Series(d[is_coal].sum(0)).groupby(month_idx).sum().to_numpy() / 1e6
        bind = lam.sum(1) > 0
        res[arm] = {
            "night_median": round(float(np.median(price[night])), 2),
            "mean": round(float(price.mean()), 2),
            "night_median_by_month": [
                round(float(np.median(price[night & (month_idx == m)])), 2)
                for m in range(12)
            ],
            "coal_twh_month": [round(float(v), 2) for v in coal],
            "coal_twh_annual": round(float(coal.sum()), 2),
            "jul_aug_coal_twh": round(float(coal[6] + coal[7]), 2),
            "lam_pool": [round(float(v), 3) for v in lp],
            "rows_binding": int(bind.sum()),
            "binding_coal_mw": round(
                float(sum(pmax[ygi[ygrp == i]].sum() for i in np.where(bind)[0])), 0
            ),
            "coal_mw_total": round(float(pmax[is_coal].sum()), 0),
            "rows_floor_scaled": n_scaled,
            **stat,
        }
        print(y, arm, json.dumps(res[arm]), flush=True)
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
    bench = bench_coal_monthly(y)
    return {
        "p1_night_median": round(float(np.median(pm[night])), 2),
        "p1_mean": round(float(pm.mean()), 2),
        "coal_twh_p1_month": [round(float(v), 2) for v in coal_p1],
        "coal_twh_p1_annual": round(float(coal_p1.sum()), 2),
        "coal_twh_bench_month": [round(float(v), 2) for v in bench],
        "coal_twh_bench_annual": round(float(bench.sum()), 2),
        "bench_jul_aug": round(float(bench[6] + bench[7]), 2),
        **res,
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--census", action="store_true")
    args = ap.parse_args()
    out_path = OUT_C if args.census else OUT_P
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    for y in args.years:
        b = build_year(y)
        print(y, "rebuilt", round(time.time() - T0), "s", flush=True)
        out[str(y)] = census(y, b) if args.census else precheck(y, b)
        if args.census:
            print(y, json.dumps(out[str(y)]), flush=True)
        out_path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
