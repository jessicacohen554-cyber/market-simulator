#!/usr/bin/env python3
"""miso-290 (ZERO LP): per-yard monthly coal pile + MISO contract take floor.

Pre-registered in ``docs/records/miso/PRECOMMIT-miso290-pile-take-floor-2026-09-30.md``.
Three modes:

``--census`` (identification only, no price): per year and coal yard row, the
yard's own contract take ``C`` (EIA-923 Page 5 purchase types C/NC/T, the same
prior two years that size its receipts rate ``R``), pile capacity ``S_max``
(largest month-end stock over ``[Y-3, Y-1]``), and the resulting cumulative
floor and clips.

``--solver-test`` (feasibility only, no candidate): the INC and PILE0 arms of
miso-289 re-run with the revised dual solver, so the solver is fixed on arms
that are not the candidate before the candidate is ever cleared.

default (the pre-check): INC vs CAND.

* ``INC``  incumbent: pooled monthly ``B/12`` rows + per-yard annual rows, keeper
  offers (regulated committed-band take-or-pay discount armed).
* ``CAND`` per-yard cumulative pile, ceiling ``S_dec + m/12 R - S_floor``
  (miso-289 minimum stock), soft cumulative floor
  ``max(0, S_dec - S_max + m/12 C) * hc`` priced at the yard's delivered coal
  cost; pooled limb off; ``coal_takeorpay_from_data`` and
  ``coal_committed_takeorpay_regulated`` disarmed (rule 19: the contract is
  carried once, by the floor's dual — the resolver's own stack guard).

Every sizing input predates the solve year (rule 13); zero fitted parameters.
Output: ``results/calibration/_miso290_pile_floor_{census,solver,precheck}.json``.
Nothing here feeds a solve.
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

OUT = {
    "census": REPO / "results/phase0/miso/_miso290_pile_floor_census.json",
    "solver": REPO / "results/phase0/miso/_miso290_pile_floor_solver.json",
    "precheck": REPO / "results/phase0/miso/_miso290_pile_floor_precheck.json",
    "diag": REPO / "results/phase0/miso/_miso290_pile_floor_diag.json",
}
SMAX_WINDOW = 3  # pile capacity window [Y-3, Y-1]; declared, never swept
N_RATE_YEARS = 2  # the budget's own receipts-rate window (build_coal_plant_budget)
MAX_IT = 240
TOL = 0.01
STEP0 = 2.0  # $/MMBtu per unit relative violation, first move
CAND_FLIPS = {
    "coal_takeorpay_from_data": False,
    "coal_committed_takeorpay_regulated": False,
}
T0 = time.time()


def contract_parts(fa, y: int, keys) -> tuple[dict, pd.DataFrame]:
    """Per yard row: ``(C * hc, (S_dec - S_max) * hc)`` MMBtu and a census frame.

    ``C`` = mean annual contract tons (purchase types C/NC/T) over the same
    ``N_RATE_YEARS`` prior years that size the yard's receipts rate, so
    ``C <= R`` by construction. ``S_max`` = largest month-end yard stock in
    ``[y-SMAX_WINDOW, y-1]``; ``S_dec`` = Dec ``y-1``. ``hc`` = the yard's own
    quantity-weighted heat content over the rate window (the budget's).
    A yard with no Dec ``y-1`` stock or no receipts gets no floor.
    """
    from market_sim.data.coal_fuel_inventory import (
        TAKE_PURCHASE_TYPES,
        coal_yard_groups,
    )
    from market_sim.data.coal_receipts import load_coal_receipts
    from market_sim.data.coal_stocks import load_coal_stocks

    yards = coal_yard_groups(fa)
    rc = load_coal_receipts([y - k for k in range(1, N_RATE_YEARS + 1)])
    n_src = max(int(rc["year"].nunique()), 1)
    st = load_coal_stocks(list(range(y - SMAX_WINDOW, y)))
    s_years = sorted(int(v) for v in st["year"].unique())
    parts, rows = {}, []
    for i, key in enumerate(keys):
        ids = yards.get(int(key), {int(key)})
        r = rc[rc["plant_id"].isin(ids)]
        s = st[st["plant_id"].isin(ids)]
        tons = float(r["quantity_tons"].sum())
        if tons <= 0 or s.empty:
            rows.append({"row": i, "key": int(key), "floored": False})
            continue
        bm = s.groupby(["year", "month"])["ending_stock_tons"].sum()
        if (y - 1, 12) not in bm.index:
            rows.append({"row": i, "key": int(key), "floored": False})
            continue
        hc = float((r["quantity_tons"] * r["heat_content_mmbtu_per_ton"]).sum()) / tons
        c_tons = (
            float(
                r.loc[
                    r["purchase_type"].isin(TAKE_PURCHASE_TYPES), "quantity_tons"
                ].sum()
            )
            / n_src
        )
        s_dec, s_max = float(bm[(y - 1, 12)]), float(bm.max())
        parts[i] = (c_tons * hc, (s_dec - s_max) * hc)
        rows.append(
            {
                "row": i,
                "key": int(key),
                "floored": True,
                "contract_share": c_tons * n_src / tons,
                "c_mmbtu": c_tons * hc,
                "r_mmbtu": tons / n_src * hc,
                "s_dec_mmbtu": s_dec * hc,
                "s_max_mmbtu": s_max * hc,
            }
        )
    return parts, pd.DataFrame(rows).assign(stock_years=str(s_years))


def build_year(y: int) -> dict:
    """INC rebuild (miso-289) + the CAND rebuild, pile rows and take floor."""
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.coal_fuel_inventory import (
        build_coal_monthly_pile,
        build_coal_plant_budget,
        coal_take_shortfall_price,
    )

    b = m289.build_year(y)
    dec.KEEPER = KEEPER
    hh = _henry_hub_actual(_load_reference(), y)
    stc = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, CAND_FLIPS))
    fac = stc["fleet_arrays"]
    ybc = build_coal_plant_budget(fac, y, hours=T)
    if ybc[5].yard_keys != b["yb"][5].yard_keys:
        raise RuntimeError(f"{y}: CAND rebuild yard rows differ from INC")
    ygi, ybud, _ym, ycf, ygrp, yprov = ybc
    keys = yprov.yard_keys
    parts, frame = contract_parts(fac, y, keys)
    stock = np.asarray(yprov.stock_mmbtu, float)
    ceil0, floor0, month_idx, pv = build_coal_monthly_pile(
        fac, ygi, ygrp, ycf, ybud, tuple(stock), parts, T
    )
    ceil1 = ceil0 - b["s_floor"][:, None]
    n_clip_ms = int((floor0 > ceil1 + 1e-6).sum())
    floor1 = np.maximum(np.minimum(floor0, ceil1), 0.0)
    price = coal_take_shortfall_price(
        stc["fuel_prices"], fac, ygi, ygrp, ycf, ybud.shape[0]
    )
    b.update(
        stc=stc,
        fac=fac,
        ybc=ybc,
        parts=parts,
        frame=frame,
        cand_ceil=ceil1,
        cand_floor=floor1,
        short_price=np.asarray(price, float),
        clip_ceiling=pv.floor_clipped_to_ceiling,
        clip_capacity=pv.floor_clipped_to_capacity,
        clip_minstock=n_clip_ms,
    )
    return b


def census(y: int, b: dict) -> dict:
    """Identification census for one year (no price)."""
    ygi, ybud, _m, _c, grp, _p = b["ybc"]
    pmax = np.asarray(b["fac"].pmax, float)
    mw = np.bincount(np.asarray(grp), weights=pmax[ygi], minlength=ybud.shape[0])
    f = b["frame"]
    fl = f[f["floored"]]
    rows = fl["row"].to_numpy(int)
    ann = b["cand_floor"][:, -1]
    pos = ann > 0
    first = np.where(
        (b["cand_floor"] > 0).any(axis=1), (b["cand_floor"] > 0).argmax(axis=1) + 1, 0
    )
    share = fl["contract_share"].to_numpy(float)
    return {
        "stock_years": f["stock_years"].iloc[0],
        "yard_rows": int(ybud.shape[0]),
        "rows_with_inputs": int(len(fl)),
        "rows_with_inputs_mw": round(float(mw[rows].sum()), 0),
        "rowed_mw": round(float(mw.sum()), 0),
        "contract_share_mw_weighted": round(
            float((share * mw[rows]).sum() / mw[rows].sum()), 3
        ),
        "contract_share_p10_p50_p90": [
            round(float(v), 2) for v in np.percentile(share, [10, 50, 90])
        ],
        "c_over_r_fleet": round(float(fl["c_mmbtu"].sum() / fl["r_mmbtu"].sum()), 3),
        "headroom_smax_minus_sdec_mmbtu_m": round(
            float((fl["s_max_mmbtu"] - fl["s_dec_mmbtu"]).sum()) / 1e6, 1
        ),
        "rows_positive_floor": int(pos.sum()),
        "positive_floor_mw": round(float(mw[pos].sum()), 0),
        "floor_first_month_p50": int(np.median(first[pos])) if pos.any() else None,
        "annual_floor_mmbtu_m": round(float(ann.sum()) / 1e6, 1),
        "annual_ceiling_mmbtu_m": round(float(b["cand_ceil"][:, -1].sum()) / 1e6, 1),
        "floor_over_ceiling_annual": round(
            float(ann.sum() / b["cand_ceil"][:, -1].sum()), 3
        ),
        "floor_by_month_mmbtu_m": [
            round(float(v) / 1e6, 1) for v in b["cand_floor"].sum(axis=0)
        ],
        "clip_to_ceiling_cells": b["clip_ceiling"],
        "clip_to_minstock_ceiling_cells": b["clip_minstock"],
        "clip_to_capacity_cells": b["clip_capacity"],
        "shortfall_price_p10_p50_p90": [
            round(float(v), 2) for v in np.percentile(b["short_price"], [10, 50, 90])
        ],
    }


def _revcum(a):
    return np.cumsum(a[:, ::-1], axis=1)[:, ::-1]


def solve_duals(bid, mg, flex, q, month_idx, gi, grp, cf, ceil, floor, pcap, pool):
    """Dual emulator for cumulative per-yard rows (ceiling, soft floor) + pooled.

    Row ``(y, m)`` duals: ``lam >= 0`` on the ceiling, ``mu >= 0`` on the floor.
    Hour ``t`` of yard ``y`` carries ``cf * nu[y, month(t)]`` with
    ``nu = revcumsum(lam - mu)`` clipped below at ``-pcap[y]`` — the soft
    floor's shortfall column, whose one unit enters every later month-end row
    exactly as a burned MMBtu does and costs ``pcap``. Where the clip binds the
    deficit is paid (cumulative shortfall carried forward), not violated.

    Revised step rule (miso-290, fixed before the candidate is cleared):
    per-coordinate adaptive steps start at ``STEP0`` $/MMBtu per unit relative
    violation, halve on a sign flip, grow x1.1 capped at ``STEP0``; tail dual
    averaging over the second half; the returned point is the lowest-residual
    of every iterate and the averaged duals (selected on feasibility only).
    """
    n, n_rows = bid.shape[0], ceil.shape[0]
    act_c = np.isfinite(ceil)
    act_f = floor > 0 if floor is not None else np.zeros_like(act_c)
    fl = np.nan_to_num(floor) if floor is not None else np.zeros_like(ceil)
    cap = pcap if pcap is not None else np.full(n_rows, np.inf)
    scale = np.maximum(np.where(act_c, ceil, 0.0).max(axis=1), 1.0)
    lam = np.zeros((n_rows, 12))
    mu = np.zeros((n_rows, 12))
    sl = np.full((n_rows, 12), STEP0)
    sm = np.full((n_rows, 12), STEP0)
    pg_c = np.zeros((n_rows, 12))
    pg_f = np.zeros((n_rows, 12))
    lp = np.zeros(12)
    sp = np.full(12, 0.5)
    prev_p = np.zeros(12)
    acc = [np.zeros_like(lam), np.zeros_like(mu), np.zeros(12), 0]
    best = (np.inf, None)

    def offsets(lam_, mu_, lp_):
        nu = np.maximum(_revcum(lam_ - mu_), -cap[:, None])
        add = np.zeros((n, 12))
        np.add.at(add, gi, cf[:, None] * nu[grp])
        off = add[:, month_idx]
        if pool is not None:
            off = off + pool[0][:, None] * lp_[month_idx][None, :]
        return off, nu

    def evaluate(lam_, mu_, lp_):
        off, nu = offsets(lam_, mu_, lp_)
        _, d = clear_block(bid + off, mg, flex, q)
        by_m = np.zeros((gi.size, 12))
        np.add.at(by_m.T, month_idx, d[gi].T)
        burn = np.zeros((n_rows, 12))
        np.add.at(burn, grp, cf[:, None] * by_m)
        burn = np.cumsum(burn, axis=1)
        clipped = nu <= -cap[:, None] + 1e-9
        short = np.maximum.accumulate(
            np.where(clipped & act_f, np.maximum(fl - burn, 0.0), 0.0), axis=1
        )
        g_c = np.where(act_c, (burn - np.nan_to_num(ceil)) / scale[:, None], 0.0)
        g_f = np.where(act_f, (fl - burn - short) / scale[:, None], 0.0)
        v_c = np.where(lam_ > 0, np.abs(g_c), np.maximum(g_c, 0.0))
        v_f = np.where(mu_ > 0, np.abs(g_f), np.maximum(g_f, 0.0))
        if pool is not None:
            pbm = pd.Series(pool[0] @ d).groupby(month_idx).sum().to_numpy()
            gp = (pbm - pool[1]) / pool[1]
            vp = np.where(lp_ > 0, np.abs(gp), np.maximum(gp, 0.0))
        else:
            gp = vp = np.zeros(12)
        worst = float(max(v_c.max(initial=0.0), v_f.max(initial=0.0), vp.max()))
        return worst, g_c, g_f, gp, short

    it = 0
    for it in range(MAX_IT):
        worst, g_c, g_f, gp, _s = evaluate(lam, mu, lp)
        if worst < best[0]:
            best = (worst, (lam.copy(), mu.copy(), lp.copy()), f"iterate {it}")
        print(
            f"  it {it} worst {worst:.4f} ceil>0 {(lam.sum(1) > 0).sum()} "
            f"floor>0 {(mu.sum(1) > 0).sum()} t {time.time() - T0:.0f}s",
            flush=True,
        )
        if worst <= TOL:
            break
        sl = np.where(
            np.sign(g_c) != np.sign(pg_c), sl * 0.5, np.minimum(sl * 1.1, STEP0)
        )
        sm = np.where(
            np.sign(g_f) != np.sign(pg_f), sm * 0.5, np.minimum(sm * 1.1, STEP0)
        )
        lam = np.where(act_c, np.maximum(0.0, lam + sl * np.clip(g_c, -1, 1)), 0.0)
        mu = np.where(act_f, np.maximum(0.0, mu + sm * np.clip(g_f, -1, 1)), 0.0)
        pg_c, pg_f = g_c, g_f
        if pool is not None:
            sp = np.where(np.sign(gp) != np.sign(prev_p), sp * 0.5, sp * 1.2)
            lp = np.maximum(0.0, lp + sp * np.clip(gp, -1, 1) * 10.0)
            prev_p = gp
        if it >= MAX_IT // 2:
            acc[0] += lam
            acc[1] += mu
            acc[2] += lp
            acc[3] += 1
    stat = {"iterations": it + 1, "last_iterate_residual": round(worst, 4)}
    if acc[3]:
        avg = (acc[0] / acc[3], acc[1] / acc[3], acc[2] / acc[3])
        w_avg = evaluate(*avg)[0]
        stat["averaged_residual"] = round(w_avg, 4)
        if w_avg < best[0]:
            best = (w_avg, avg, "tail average")
    lam, mu, lp = best[1]
    _w, _gc, _gf, _gp, short = evaluate(lam, mu, lp)
    off, nu = offsets(lam, mu, lp)
    stat.update(
        max_rel_violation=round(best[0], 4),
        returned=best[2],
        shortfall_mmbtu_m=round(float(short[:, -1].sum()) / 1e6, 2),
        rows_at_shortfall_cap=int((nu <= -cap[:, None] + 1e-9).any(axis=1).sum()),
    )
    return off, lam, mu, lp, stat


def _stack(st, fa):
    n = len(fa.pmax)
    mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
    if mc.shape[1] == 1:
        mc = np.repeat(mc, T, axis=1)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    mg = np.array(np.broadcast_to(np.asarray(fa.min_gen, float), cap.shape))
    return mc, cap, mg


def run_arms(y: int, b: dict, arms: tuple[str, ...]) -> dict:
    """Clear the requested arms for one year."""
    from market_sim.data.coal_fuel_inventory import reconcile_floors_to_yard_budget
    from market_sim.model.commitment import compute_monthly_markup

    st, fa = b["st"], b["fa"]
    cfg, fleet = st["config"], st["fleet"]
    mc, cap, mg_raw = _stack(st, fa)
    ygi, ybud, _ym, ycf, ygrp, _yp = b["yb"]
    ygi, ygrp, ycf = np.asarray(ygi), np.asarray(ygrp), np.asarray(ycf, float)
    month_idx = b["month_idx"]
    n = mc.shape[0]

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

    pgi, pbud, _pm, pcf, _pg, _pp = b["pb"]
    add_pool = np.zeros(n)
    add_pool[pgi] = pcf
    pool = (add_pool, np.asarray(pbud, float).reshape(-1))
    is_coal = np.zeros(n, bool)
    is_coal[pgi] = True
    is_coal[ygi] = True
    ann = np.full((ybud.shape[0], 12), np.nan)
    ann[:, -1] = ybud[:, 0]

    res = {}
    for arm in arms:
        print(y, arm, flush=True)
        bid = mc + mk
        floor = pcap = None
        n_scaled = None
        if arm == "INC":
            ceil, pl, mg_a = ann, pool, mg_inc
        elif arm == "PILE0":
            ceil, pl, mg_a = b["ceil0"], None, None
        elif arm == "CAND":
            mcc, capc, mgc = _stack(b["stc"], b["fac"])
            if mcc.shape != mc.shape:
                raise RuntimeError("CAND rebuild changed the generator set")
            bid = mcc + mk
            ceil, pl, mg_a = b["cand_ceil"], None, None
            floor, pcap = b["cand_floor"], b["short_price"]
        elif arm == "CAND_KO":
            # Diagnostic only (not gated): CAND's rows on the KEEPER offers,
            # i.e. the regulated take-or-pay discount left armed.
            ceil, pl, mg_a = b["cand_ceil"], None, None
            floor, pcap = b["cand_floor"], b["short_price"]
        else:
            raise ValueError(arm)
        if mg_a is None:
            mg_a = mg_raw.copy()
            n_scaled = m289.reconcile_monthly(mg_a, ygi, ygrp, ycf, ceil, month_idx)
            mg_a = np.minimum(mg_a, cap)
        flex = cap - mg_a
        off, lam, mu, lp, stat = solve_duals(
            bid, mg_a, flex, q, month_idx, ygi, ygrp, ycf, ceil, floor, pcap, pl
        )
        price, d = clear_block(bid + off, mg_a, flex, q)
        coal = pd.Series(d[is_coal].sum(0)).groupby(month_idx).sum().to_numpy() / 1e6
        res[arm] = {
            "night_median": round(float(np.median(price[night])), 2),
            "mean": round(float(price.mean()), 2),
            "night_median_by_month": [
                round(float(np.median(price[night & (month_idx == m)])), 2)
                for m in range(12)
            ],
            "coal_twh_month": [round(float(v), 2) for v in coal],
            "coal_twh_annual": round(float(coal.sum()), 2),
            "jan_apr_coal_twh": round(float(coal[:4].sum()), 2),
            "jul_aug_coal_twh": round(float(coal[6] + coal[7]), 2),
            "rows_ceiling_binding": int((lam.sum(1) > 0).sum()),
            "rows_floor_binding": int((mu.sum(1) > 0).sum()),
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
        "coal_twh_p1_month": [round(float(v), 2) for v in coal_p1],
        "coal_twh_p1_annual": round(float(coal_p1.sum()), 2),
        "coal_twh_bench_month": [round(float(v), 2) for v in bench],
        "coal_twh_bench_annual": round(float(bench.sum()), 2),
        "bench_jan_apr": round(float(bench[:4].sum()), 2),
        "bench_jul_aug": round(float(bench[6] + bench[7]), 2),
        **res,
    }


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--census", action="store_true")
    g.add_argument("--solver-test", action="store_true")
    g.add_argument("--diag", action="store_true", help="CAND_KO diagnostic")
    args = ap.parse_args()
    mode = (
        "census"
        if args.census
        else "solver"
        if args.solver_test
        else "diag"
        if args.diag
        else "precheck"
    )
    out_path = OUT[mode]
    out = json.loads(out_path.read_text()) if out_path.exists() else {}
    for y in args.years:
        b = build_year(y)
        print(y, "rebuilt", round(time.time() - T0), "s", flush=True)
        if mode == "census":
            out[str(y)] = census(y, b)
        elif mode == "diag":
            out[str(y)] = run_arms(y, b, ("CAND_KO",))
        elif mode == "solver":
            out[str(y)] = run_arms(y, b, ("INC", "PILE0"))
        else:
            out[str(y)] = run_arms(y, b, ("INC", "CAND"))
        print(y, json.dumps(out[str(y)]), flush=True)
        out_path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
