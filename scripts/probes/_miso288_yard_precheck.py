#!/usr/bin/env python3
"""miso-288 pre-check (ZERO LP): coal budget at yard grain only vs the incumbent.

Pre-registered in ``docs/records/miso/PRECOMMIT-miso288-yard-only-precheck-2026-09-30.md``
(pushed at c4ffbefa before this probe was written; thresholds there, not here).

Each binding coal energy row acts in the LP as a $/MMBtu adder ``lam`` times the
row's heat-rate coefficient on the coal rows it covers. Per year, on the
fleet-only rebuild of the keeper recipe, the P1 bid stack (``mc_base`` +
startup markup, as ``_miso287_p1_residual``) is cleared hourly at the keeper's
P1 LP quantity with coal offers raised by ``lam_pool[m(t)] + lam_yard[yard(g)]``.
The ``lam`` vector is found by projected subgradient on row violations.

* INC  (incumbent): pooled monthly ``B/12`` rows + per-yard annual rows.
* YARD (candidate): per-yard annual rows only (``coal_fuel_inventory=False``).

Output: ``results/phase0/miso/_miso288_yard_precheck.json``. Rule 13: nothing
here feeds a solve.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
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

PAYLOAD = REPO / "frontend/data/backcast/runs/2026-09-28-miso-280-splitremap.js"
OUT = REPO / "results/phase0/miso/_miso288_yard_precheck.json"
MAX_IT = 200
T0 = time.time()
TOL = 0.01


def bench_coal_monthly(y: int) -> np.ndarray:
    """EIA-923-basis coal TWh by month from the keeper run payload ``volErr``."""
    s = PAYLOAD.read_text()
    p = json.loads(
        gzip.decompress(base64.b64decode(re.search(r'="([^"]+)"', s).group(1)))
    )
    ve = p["years"][str(y)]["volErr"]
    tot = np.zeros(12)
    for k, v in ve.items():
        if str(k).startswith("COAL"):
            for z in v["zoneMon"].values():
                tot += np.asarray(z["a"], dtype=float)
    return tot


def solve_lams(bid, mg, flex, q, add_pool, month_idx, pool_cap, yard_rows):
    """Projected subgradient for (lam_pool[12], lam_yard[n]); returns lams + stats.

    ``yard_rows``: list of (gen indices, coeff per gen, cap MMBtu). ``pool_cap``
    is None for YARD. ``add_pool`` is the pooled rows' per-gen coefficient.
    """
    n_y = len(yard_rows)
    lp = np.zeros(12)
    ly = np.zeros(n_y)
    sp = np.full(12, 0.5)
    sy = np.full(n_y, 0.5)
    prev_gp = np.zeros(12)
    prev_gy = np.zeros(n_y)
    yadd = np.zeros((n_y, bid.shape[0]))
    for i, (gi, cf, _cap) in enumerate(yard_rows):
        yadd[i, gi] = cf
    ycap = np.array([r[2] for r in yard_rows])
    worst = np.inf
    for it in range(MAX_IT):
        adder = ly @ yadd  # per-gen $/MWh from yard lams
        lam_t = lp[month_idx] if pool_cap is not None else np.zeros(T)
        _, d = clear_block(
            bid + adder[:, None] + add_pool[:, None] * lam_t[None, :], mg, flex, q
        )
        yb = yadd @ d.sum(1)
        gy = (yb - ycap) / np.maximum(ycap, 1.0)
        viol_y = np.where(ly > 0, np.abs(gy), np.maximum(gy, 0))
        if pool_cap is not None:
            pb = pd.Series(add_pool @ d).groupby(month_idx).sum().to_numpy()
            gp = (pb - pool_cap) / pool_cap
            viol_p = np.where(lp > 0, np.abs(gp), np.maximum(gp, 0))
        else:
            gp = np.zeros(12)
            viol_p = np.zeros(12)
        worst = float(max(viol_y.max(initial=0), viol_p.max()))
        print(
            f"  it {it} worst {worst:.4f} yards>0 {(ly > 0).sum()} "
            f"lam_pool max {lp.max():.2f} t {time.time() - T0:.0f}s",
            flush=True,
        )
        if worst <= TOL:
            break
        # adaptive per-row step: halve on sign flip, grow slowly otherwise
        sy = np.where(np.sign(gy) != np.sign(prev_gy), sy * 0.5, sy * 1.2)
        sp = np.where(np.sign(gp) != np.sign(prev_gp), sp * 0.5, sp * 1.2)
        ly = np.maximum(0.0, ly + sy * np.clip(gy, -1, 1) * 10.0)
        if pool_cap is not None:
            lp = np.maximum(0.0, lp + sp * np.clip(gp, -1, 1) * 10.0)
        prev_gy, prev_gp = gy, gp
    return lp, ly, yadd, {"iterations": it + 1, "max_rel_violation": round(worst, 4)}


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.data.coal_fuel_inventory import (
        build_coal_fuel_budget,
        build_coal_plant_budget,
        reconcile_floors_to_yard_budget,
    )
    from market_sim.model.commitment import compute_monthly_markup

    dec.KEEPER = KEEPER
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for y in args.years:
        hh = _henry_hub_actual(_load_reference(), y)
        st = run_year(y, "MISO", T, hh, {}, fleet_only=True, **dec.recipe(y, {}))
        cfg, fa, fleet = st["config"], st["fleet_arrays"], st["fleet"]
        n = len(fa.pmax)
        mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
        if mc.shape[1] == 1:
            mc = np.repeat(mc, T, axis=1)
        cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
        mg_raw = np.array(np.broadcast_to(np.asarray(fa.min_gen, float), cap.shape))

        yb = build_coal_plant_budget(fa, y, hours=T)
        pb = build_coal_fuel_budget(fa, y, hours=T)
        if yb is None or pb is None:
            print(y, "no coal budget (clean partitions absent?)", flush=True)
            return 1
        ygi, ybud, _ym, ycf, ygrp, yprov = yb
        reconcile_floors_to_yard_budget(mg_raw, ygi, ybud, ycf, ygrp)
        mg = np.minimum(mg_raw, cap)
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

        print(y, "rows", n, "rebuilt", round(time.time() - T0), "s", flush=True)
        _, d0 = clear_block(mc, mg, flex, q)
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

        pgi, pbud, pmonth, pcf, _pg, pprov = pb
        month_idx = np.asarray(pmonth)
        add_pool = np.zeros(n)
        add_pool[pgi] = pcf
        pool_cap = np.asarray(pbud, float).reshape(-1)
        ygrp = np.asarray(ygrp)
        yard_rows = [
            (ygi[ygrp == i], np.asarray(ycf)[ygrp == i], float(ybud[i, 0]))
            for i in range(ybud.shape[0])
        ]
        is_coal = np.zeros(n, bool)
        is_coal[pgi] = True
        is_coal[ygi] = True

        res = {}
        for arm, pc in (("INC", pool_cap), ("YARD", None)):
            lp, ly, yadd, stat = solve_lams(
                bid, mg, flex, q, add_pool, month_idx, pc, yard_rows
            )
            lam_t = lp[month_idx] if pc is not None else np.zeros(T)
            price, d = clear_block(
                bid + (ly @ yadd)[:, None] + add_pool[:, None] * lam_t[None, :],
                mg,
                flex,
                q,
            )
            coal = (
                pd.Series(d[is_coal].sum(0)).groupby(month_idx).sum().to_numpy() / 1e6
            )
            res[arm] = {
                "night_median": round(float(np.median(price[night])), 2),
                "mean": round(float(price.mean()), 2),
                "coal_twh_month": [round(float(v), 2) for v in coal],
                "coal_twh_annual": round(float(coal.sum()), 2),
                "lam_pool": [round(float(v), 3) for v in lp],
                "yards_binding": int((ly > 0).sum()),
                "yards": len(yard_rows),
                "binding_yard_coal_mw": round(
                    float(
                        sum(
                            np.asarray(fa.pmax, float)[r[0]].sum()
                            for r, v in zip(yard_rows, ly, strict=True)
                            if v > 0
                        )
                    ),
                    0,
                ),
                "coal_mw_total": round(
                    float(np.asarray(fa.pmax, float)[is_coal].sum()), 0
                ),
                **stat,
            }
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
        out[str(y)] = {
            "p1_night_median": round(float(np.median(pm[night])), 2),
            "p1_mean": round(float(pm.mean()), 2),
            "coal_twh_p1_month": [round(float(v), 2) for v in coal_p1],
            "coal_twh_p1_annual": round(float(coal_p1.sum()), 2),
            "coal_twh_bench_month": [round(float(v), 2) for v in bench],
            "coal_twh_bench_annual": round(float(bench.sum()), 2),
            "pool_annual_mmbtu_m": round(float(pprov.annual_budget_mmbtu) / 1e6, 1),
            "yard_annual_mmbtu_m": round(float(yprov.annual_budget_mmbtu) / 1e6, 1),
            **res,
        }
        print(y, json.dumps(out[str(y)]), flush=True)
        OUT.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
