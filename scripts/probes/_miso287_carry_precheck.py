#!/usr/bin/env python3
"""miso-287 pre-check (ZERO LP): pooled coal stock-carry vs the flat 1/12 monthly rows.

Pre-registered in ``docs/PRECOMMIT-miso287-coal-carry-precheck-2026-09-29.md``
(committed before this probe was written; thresholds there, not here).

A binding coal energy row acts in the LP as a uniform adder ``lam`` ($/MMBtu,
times each coal row's heat-rate coefficient) on every coal row over the row's
hours. Per year, on the fleet-only rebuild of the keeper recipe:

* the P1 bid stack (``mc_base`` + startup markup, as ``_miso287_p1_residual``)
  is cleared at the keeper's P1 thermal quantity, hour by hour, with coal
  offers raised by ``lam_m * HR``;
* each month's coal MMBtu is tabulated on a ``lam`` grid (monotone in ``lam``);
* FLAT (incumbent ``build_coal_fuel_budget``): ``lam_m`` meets ``B/12`` per month;
* CARRY (candidate): cumulative month-end rows ``S_dec*hc + m/12*R*hc``, solved
  by the pooled-block pass (each block of months shares the ``lam`` of its most
  constraining cumulative end point).

Gate V: FLAT must reproduce the keeper's P1 2022 night median within +/-$1.5.
The per-yard annual rows are not emulated (CARRY is an upper bound on relief).

Output: ``results/calibration/_miso287_carry_precheck.json``. Rule 13: nothing
here feeds a solve.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from scripts.probes import _miso271_cc_decomp as dec  # noqa: E402
from scripts.probes._miso287_p1_residual import (  # noqa: E402
    KEEPER,
    NIGHT_H,
    NON_LP,
    T,
    clear_all,
    run_ratio,
)

LAM_GRID = np.concatenate([np.arange(0.0, 8.0, 0.1), np.arange(8.0, 40.01, 1.0)])


def clear_block(mc, mg, flex, q):
    """Vectorized merit clear over a block of hours: (price, dispatch)."""
    o = np.argsort(mc, axis=0, kind="stable")
    fs = np.take_along_axis(flex, o, axis=0)
    cum = mg.sum(0)[None, :] + np.cumsum(fs, axis=0)
    n = mc.shape[0]
    k = np.minimum((cum < q[None, :]).sum(0), n - 1)
    cols = np.arange(mc.shape[1])
    price = np.take_along_axis(mc, o, axis=0)[k, cols]
    prev = np.where(k > 0, cum[np.maximum(k - 1, 0), cols], mg.sum(0))
    rank = np.arange(n)[:, None]
    ds = np.where(rank < k[None, :], fs, 0.0)
    ds[k, cols] = np.maximum(0.0, q - prev)
    d = np.empty_like(ds)
    np.put_along_axis(d, o, ds, axis=0)
    return price, d + mg


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.coal_fuel_inventory import build_coal_fuel_budget
    from market_sim.model.commitment import compute_monthly_markup

    dec.KEEPER = KEEPER
    path = REPO / "results/calibration/_miso287_carry_precheck.json"
    out = json.loads(path.read_text()) if path.exists() else {}
    for y in args.years:
        hh = _henry_hub_actual(_load_reference(), y)
        st = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, {}))
        cfg, fa, fleet = st["config"], st["fleet_arrays"], st["fleet"]
        n = len(fa.pmax)
        mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
        if mc.shape[1] == 1:
            mc = np.repeat(mc, T, axis=1)
        pmax = np.asarray(fa.pmax, float)
        cap = pmax[:, None] * np.asarray(fa.availability, float)
        mg = np.minimum(np.asarray(fa.min_gen, float), cap)
        flex = cap - mg

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

        _, _, d0 = clear_all(mc, mg, flex, q)
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

        built = build_coal_fuel_budget(fa, y, hours=T)
        if built is None:
            print(y, "no coal budget (clean partitions absent?)", flush=True)
            return 1
        gidx, budget, month_idx, coeff, _grp, prov = built
        month_idx = np.asarray(month_idx)
        monthly_cap = np.asarray(budget, float).reshape(-1)
        hc_stock = prov.opening_stock_tons * prov.mmbtu_per_ton
        hc_rate = prov.delivery_rate_tons_per_year * prov.mmbtu_per_ton
        cum_cap = hc_stock + (np.arange(1, 13) / 12.0) * hc_rate
        add = np.zeros(n)
        add[gidx] = coeff
        is_coal = np.zeros(n, bool)
        is_coal[gidx] = True

        # Month burn (MMBtu) and coal MWh on the lam grid.
        burn = np.zeros((12, LAM_GRID.size))
        for m in range(12):
            hrs = np.where(month_idx == m)[0]
            for j, lam in enumerate(LAM_GRID):
                _, d = clear_block(
                    bid[:, hrs] + lam * add[:, None], mg[:, hrs], flex[:, hrs], q[hrs]
                )
                burn[m, j] = float((add[:, None] * d).sum())
            print(y, "month", m + 1, "burn@0", round(burn[m, 0] / 1e6, 1), flush=True)

        def lam_for(target, curve):
            """Smallest grid-interpolated lam with burn <= target (curve decreasing)."""
            if curve[0] <= target:
                return 0.0
            if curve[-1] > target:
                return float(LAM_GRID[-1])
            j = int(np.argmax(curve <= target))
            x0, x1, y0, y1 = LAM_GRID[j - 1], LAM_GRID[j], curve[j - 1], curve[j]
            return float(x0 + (y0 - target) * (x1 - x0) / max(y0 - y1, 1e-9))

        lam_flat = np.array([lam_for(monthly_cap[m], burn[m]) for m in range(12)])
        lam_carry = np.zeros(12)
        used, s0 = 0.0, 0
        while s0 < 12:
            best_lam, best_e = 0.0, s0
            for e in range(s0, 12):
                lam_e = lam_for(cum_cap[e] - used, burn[s0 : e + 1].sum(0))
                if lam_e > best_lam + 1e-9:
                    best_lam, best_e = lam_e, e
            if best_lam <= 0.0:
                break
            lam_carry[s0 : best_e + 1] = best_lam
            j = np.interp(best_lam, LAM_GRID, np.arange(LAM_GRID.size))
            used += sum(
                np.interp(j, np.arange(LAM_GRID.size), burn[m])
                for m in range(s0, best_e + 1)
            )
            s0 = best_e + 1

        def emulate(lams):
            """Final hourly clear under a per-month lam vector."""
            lam_t = lams[month_idx]
            price, d = clear_block(bid + lam_t[None, :] * add[:, None], mg, flex, q)
            coal_mwh = d[is_coal].sum(0)
            mon = pd.Series(coal_mwh).groupby(month_idx).sum() / 1e6
            return price, mon.to_numpy()

        p_none, coal_none = emulate(np.zeros(12))
        p_flat, coal_flat = emulate(lam_flat)
        p_carry, coal_carry = emulate(lam_carry)
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
        med = lambda p: round(float(np.median(p[night])), 2)  # noqa: E731
        out[str(y)] = {
            "p1_night_median": med(pm),
            "bid_stack_night_median": med(p_none),
            "flat_night_median": med(p_flat),
            "carry_night_median": med(p_carry),
            "carry_minus_flat_night_median": round(med(p_carry) - med(p_flat), 2),
            "p1_mean": round(float(pm.mean()), 2),
            "flat_mean": round(float(p_flat.mean()), 2),
            "carry_mean": round(float(p_carry.mean()), 2),
            "lam_flat": [round(float(v), 2) for v in lam_flat],
            "lam_carry": [round(float(v), 2) for v in lam_carry],
            "coal_twh_p1": [round(float(v), 2) for v in coal_p1],
            "coal_twh_flat": [round(float(v), 2) for v in coal_flat],
            "coal_twh_carry": [round(float(v), 2) for v in coal_carry],
            "coal_twh_unconstrained": [round(float(v), 2) for v in coal_none],
            "monthly_cap_mmbtu_m": round(float(monthly_cap[0]) / 1e6, 2),
            "cum_cap_mmbtu_m": [round(float(v) / 1e6, 2) for v in cum_cap],
            "unconstrained_burn_mmbtu_m": [
                round(float(v) / 1e6, 2) for v in burn[:, 0]
            ],
            "opening_stock_mmbtu_m": round(hc_stock / 1e6, 2),
            "annual_budget_mmbtu_m": round(float(prov.annual_budget_mmbtu) / 1e6, 2),
        }
        print(y, json.dumps(out[str(y)]), flush=True)
        path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
