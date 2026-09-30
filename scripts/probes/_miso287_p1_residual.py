#!/usr/bin/env python3
"""miso-287 phase 0 (ZERO LP): attribute the P1-over-P0-stack night residual.

miso-285 §4: at the keeper's own night thermal quantity, the base-cost (P0)
offer stack reproduces the P1 night median within +/-$0.3 in 5 of 7 years, but
P1 sits +$5.1 above it in 2022 and +$1.9 in 2025. This probe tests candidate
(a), the P1 startup-amortization markup, by rebuilding the P1 BID stack without
an LP:

1. Fleet-only rebuild of the keeper recipe (``miso280_span``), per year.
2. Clear the P0 stack (``mc_base``) at the keeper's P1 thermal quantity in
   EVERY hour; the per-row dispatch of that clear is the zero-LP stand-in for
   the P0 run pattern (the same proxy miso-286 validated against the keeper's
   P1 CC committed MW).
3. ``model.commitment.compute_monthly_markup`` on that proxy, with the keeper's
   own flags and the v4 condition-keyed run ratio rebuilt exactly as
   ``run_calibration.py`` builds it.
4. Clear ``mc_base + markup`` at the same night quantity and report the median
   beside P0-stack and P1, plus which class/band sets the night price in each
   stack and the markup it carries.

Output: ``results/calibration/_miso287_p1_residual.json``. Rule 13: nothing here
feeds a solve.
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

KEEPER = REPO / "results/calibration/miso280_span"
NIGHT_H = 6
T = 8760
# Classes in class_hourly that are NOT LP fleet rows: VRE (their own W/S
# columns) and the must-run residual classes run_calibration_full injects
# from EIA-923 and nets out of LP demand (_INJECTED_MUSTRUN_CLASSES). The
# miso-285 stack clear kept biomass + OTHER in its quantity (miso-287 §2).
NON_LP = ("wind", "solar", "biomass", "OTHER")


def clear_all(mc, mg, flex, q):
    """Merit clear per hour at quantity ``q``: (price, marginal row, dispatch)."""
    n = mc.shape[0]
    price = np.full(T, np.nan)
    marg = np.zeros(T, dtype=int)
    disp = np.zeros((n, T))
    for tt in range(T):
        o = np.argsort(mc[:, tt], kind="stable")
        base = mg[:, tt].sum()
        cum = base + np.cumsum(flex[o, tt])
        k = min(int(np.searchsorted(cum, q[tt])), n - 1)
        price[tt] = mc[o[k], tt]
        marg[tt] = o[k]
        d = mg[:, tt].copy()
        d[o[:k]] += flex[o[:k], tt]
        prev = cum[k - 1] if k > 0 else base
        d[o[k]] += max(0.0, q[tt] - prev)
        disp[:, tt] = d
    return price, marg, disp


def run_ratio(st, iso="MISO"):
    """The v4 condition-keyed run ratio, built exactly as run_calibration does."""
    from market_sim.data.fleet import campd_ct_run_band_ratios

    bands = campd_ct_run_band_ratios(iso)
    if bands is None:
        return None
    edges, ratios = bands
    nl = (
        st["demand"].sum(axis=0)
        - (st["solar_cap"][:, None] * st["solar_cf"]).sum(axis=0)
        - (st["wind_cap"][:, None] * st["wind_cf"]).sum(axis=0)
    )
    pct = (np.argsort(np.argsort(nl)) + 1.0) / float(nl.shape[0])
    idx = np.searchsorted(np.asarray(edges, dtype=float), pct, side="right")
    return np.asarray(ratios, dtype=float)[idx]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    from market_sim.model.commitment import compute_monthly_markup

    dec.KEEPER = KEEPER
    path = REPO / "results/calibration/_miso287_p1_residual.json"
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
        grp = np.asarray(fa.plant_group).astype(str)
        uid = np.asarray(list(fa.unit_ids)).astype(str)
        band = np.array([u.rsplit("_", 1)[-1] if "_" in u else "?" for u in uid])
        fam = np.where(np.char.startswith(band, "econ"), "econ", band)
        lab = np.char.add(np.char.add(grp, "|"), fam)

        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        pm = (
            s[(s["pass"] == "P1") & (s.zone == "MISO-Illinois")]
            .sort_values("hour")
            .price.to_numpy()
        )
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[(ch["pass"] == "P1") & ~ch.klass.astype(str).isin(NON_LP)]
        q = ch.groupby("hour").mw.sum().reindex(range(T)).fillna(0).to_numpy()
        t = np.where(np.arange(T) % 24 < NIGHT_H)[0]

        p0, m0, d0 = clear_all(mc, mg, flex, q)
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
        p1b, m1, _ = clear_all(mc + mk, mg, flex, q)

        def who(marg):
            v = pd.Series(lab[marg[t]]).value_counts(normalize=True)
            return {k: round(float(x), 3) for k, x in v.head(6).items()}

        mk_night = mk[:, t]
        on = d0[:, t] > 0.05 * pmax[:, None]
        mk_by = (
            pd.DataFrame({"lab": lab, "mk": (mk_night * on).sum(1), "n": on.sum(1)})
            .groupby("lab")[["mk", "n"]]
            .sum()
        )
        mk_by = mk_by[mk_by.n > 0]
        mk_by = (mk_by.mk / mk_by.n).sort_values(ascending=False)
        hd = pd.DataFrame(
            {
                "hour": np.arange(T),
                "p1": pm,
                "p0_stack": p0,
                "bid_stack": p1b,
                "q": q,
                "marg_p0": lab[m0],
                "marg_bid": lab[m1],
                "mc_marg_p0": mc[m0, np.arange(T)],
            }
        )
        hd.to_parquet(REPO / f"results/calibration/_miso287_hourly_{y}.parquet")
        out[str(y)] = {
            "p1_median": round(float(np.median(pm[t])), 2),
            "p0_stack_median": round(float(np.nanmedian(p0[t])), 2),
            "bid_stack_median": round(float(np.nanmedian(p1b[t])), 2),
            "p1_mean": round(float(np.mean(pm[t])), 2),
            "p0_stack_mean": round(float(np.nanmean(p0[t])), 2),
            "bid_stack_mean": round(float(np.nanmean(p1b[t])), 2),
            "all_hours_median": {
                "p1": round(float(np.median(pm)), 2),
                "p0_stack": round(float(np.nanmedian(p0)), 2),
                "bid_stack": round(float(np.nanmedian(p1b)), 2),
            },
            "marginal_p0_stack": who(m0),
            "marginal_bid_stack": who(m1),
            "marginal_row_markup_bid_stack_median": round(
                float(np.median(mk[m1[t], t])), 2
            ),
            "night_markup_when_online_by_label": {
                k: round(float(v), 2) for k, v in mk_by.head(8).items() if v > 0.05
            },
            "gas_price": round(float(hh), 2),
        }
        print(y, json.dumps(out[str(y)]), flush=True)
        path.write_text(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
