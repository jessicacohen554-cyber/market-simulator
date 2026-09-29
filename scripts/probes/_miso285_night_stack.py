#!/usr/bin/env python3
"""miso-285 phase 0 (ZERO LP): the keeper's night offer stack between the hub price and its own price.

Fleet-only rebuild of the designated keeper's recipe (``miso280_span``) per year.
Over night hours h0-5, per hour: the thermal MW the model offers at or below
the measured ILLINOIS.HUB RT price vs at or below its own MISO-Illinois price
(availability x pmax above the min-gen floor, P0 ``mc_base``), split by class
and band family. The difference is the MW the model's stack carries inside the
overshoot. Also the stack slope ($/GW) at the model's clearing point and the
offer decomposition (fuel x HR, VOM, rest) of the tranches inside the gap.

Output: ``results/calibration/_miso285_night_stack.json``. Rule 13: nothing here feeds a solve.

miso-286 (``--cf4``): the PRE-REGISTERED zero-LP pre-check of the chartered
``miso_gas_ecomin_online_floor`` (charter §3). CF4 floors ONLY the rows the
mechanism floors — ``pipeline.commitment.miso_gas_ecomin_min_load_fracs``: each
plant's base startup-bearing gas_cc tranche (min-down >= 4 h), CHP excluded —
at the MEASURED plant-basis ``min_load_frac`` (MISO CAMPD, 0.3238), capped at
the tranche's own capacity, and ONLY in hours the unit is online. The online
pattern is the stack's OWN per-hour P0 clear (a row dispatched above the
detector's 5 % run threshold), the zero-LP analogue of the P0 run pattern; the
keeper's P1 class-band committed MW is reported beside it as the check on that
proxy. Kill rule (fixed ex ante): a night-median move < $0.5 in >= 4 of 7 years
stops the lane. Output key ``cf4`` per year in the same JSON.
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
from scripts.probes._miso283_premium_localize import hub  # noqa: E402

KEEPER = REPO / "results/calibration/miso280_span"
NIGHT_H = 6


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2019, 2026)))
    ap.add_argument("--cf4", action="store_true", help="miso-286 pre-check only")
    ap.add_argument("--min-load-frac", type=float, default=None)
    args = ap.parse_args()
    from scripts.run_calibration import _load_reference, run_year  # type: ignore
    from scripts.run_calibration_full import _henry_hub_actual  # type: ignore

    dec.KEEPER = KEEPER
    path = REPO / "results/calibration/_miso285_night_stack.json"
    out = json.loads(path.read_text()) if path.exists() else {}
    for y in args.years:
        hh = _henry_hub_actual(_load_reference(), y)
        st = run_year(y, "MISO", 8760, hh, {}, fleet_only=True, **dec.recipe(y, {}))
        fa = st["fleet_arrays"]
        n = len(fa.pmax)
        mc = np.asarray(st["mc_base"], dtype=float).reshape(n, -1)
        if mc.shape[1] == 1:
            mc = np.repeat(mc, 8760, axis=1)
        cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
        mg = np.minimum(np.asarray(fa.min_gen, float), cap)
        flex = cap - mg
        grp = np.asarray(fa.plant_group).astype(str)
        uid = np.asarray(list(fa.unit_ids)).astype(str)
        band = np.array([u.rsplit("_", 1)[-1] if "_" in u else "?" for u in uid])
        fam = np.where(np.char.startswith(band, "econ"), "econ", band)
        s = pd.read_parquet(KEEPER / f"hourly/system_{y}.parquet")
        pm = (
            s[(s["pass"] == "P1") & (s.zone == "MISO-Illinois")]
            .sort_values("hour")
            .price.to_numpy()
        )
        ph = hub(y, "rt")["ILLINOIS.HUB"].to_numpy()
        t = np.where((np.arange(8760) % 24 < NIGHT_H) & ~np.isnan(ph))[0]
        inside = (mc[:, t] > ph[None, t]) & (mc[:, t] <= pm[None, t])
        gap_mw = flex[:, t] * inside
        key = pd.Series(grp + "|" + fam)
        by = pd.DataFrame(gap_mw).groupby(key.values).sum().sum(axis=1) / len(t)
        # stack slope at the model price: flex MW offered within +/-$2 of p_model
        near = np.abs(mc[:, t] - pm[None, t]) <= 2.0
        slope_mw_per_4usd = float((flex[:, t] * near).sum(0).mean())
        # offer decomposition of the gap tranches (MW-weighted)
        fp = np.asarray(st["fuel_prices"], float)
        fp = fp if fp.ndim == 2 else np.repeat(fp[:, None], 8760, axis=1)
        hr = np.asarray(fa.heat_rate, float)[:, None]
        vom = np.asarray(fa.vom, float)[:, None]
        w = gap_mw
        dec_rows = {}
        for g in [
            "CC_REGULAR",
            "COAL_PRB",
            "COAL_BIT",
            "ST_GAS",
            "CC_CHP",
            "CT_CHP",
            "ST_CHP",
            "OTHER",
            "import",
        ]:
            m = grp == g
            ww = w[m].sum()
            if ww <= 0:
                continue
            fc = hr[m] * fp[m][:, t]
            dec_rows[g] = {
                "gap_mw": round(float(ww / len(t)), 0),
                "offer": round(float((mc[m][:, t] * w[m]).sum() / ww), 2),
                "hr_x_fuel": round(float((fc * w[m]).sum() / ww), 2),
                "vom": round(float((vom[m] * w[m]).sum() / ww), 2),
                "rest": round(
                    float(((mc[m][:, t] - fc - vom[m]) * w[m]).sum() / ww), 2
                ),
                "hr": round(float((hr[m] * w[m]).sum() / ww), 3),
                "fuel": round(float((fp[m][:, t] * w[m]).sum() / ww), 3),
            }
        # P0-offer stack cleared at the model's own night fleet dispatch
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[(ch["pass"] == "P1") & ~ch.klass.astype(str).isin(["wind", "solar"])]
        q = ch.groupby("hour").mw.sum().reindex(range(8760)).fillna(0).to_numpy()[t]

        def clear(mc_, mg_, flex_):
            """Mean/median P0-stack price at the model's own night quantity."""
            pr = np.full(len(t), np.nan)
            for j, tt in enumerate(t):
                o = np.argsort(mc_[:, tt])
                cum = mg_[:, tt].sum() + np.cumsum(flex_[o, tt])
                k = np.searchsorted(cum, q[j])
                pr[j] = mc_[o[min(k, n - 1)], tt]
            return pr

        p0 = clear(mc, mg, flex)
        if args.cf4:
            out.setdefault(str(y), {})["cf4"] = _cf4(
                st, mc, cap, mg, flex, grp, fam, t, q, pm, ph, p0, args.min_load_frac
            )
            cb = pd.read_parquet(KEEPER / f"hourly/class_band_hourly_{y}.parquet")
            cb = cb[
                (cb["pass"] == "P1")
                & cb.klass.astype(str).isin(["CC_REGULAR", "CC_INTERMEDIATE"])
                & (cb.band.astype(str) == "committed")
            ]
            kc = cb.groupby("hour").mw.sum().reindex(range(8760)).fillna(0)
            out[str(y)]["cf4"]["keeper_p1_cc_committed_night_mw"] = round(
                float(kc.to_numpy()[t].mean()), 0
            )
            print(y, json.dumps(out[str(y)]["cf4"]), flush=True)
            path.write_text(json.dumps(out, indent=1))
            continue

        # Counterfactual stacks (SIZING ONLY, no mechanism is proposed by them):
        # CF1 CC_REGULAR committed band price-taking (commitment non-convexity);
        # CF2 every gas committed band price-taking; CF3 all fossil econ bands
        # at their own phys multipliers is not rebuildable here, so CF3 sizes
        # a uniform -1 $/MWh on every CC econ tranche (stack slope probe).
        def taker(mask):
            mg2 = mg.copy()
            f2 = flex.copy()
            mg2[mask] = cap[mask]
            f2[mask] = 0.0
            return clear(mc, mg2, f2)

        is_comm = fam == "committed"
        gas_g = np.isin(
            grp,
            ["CC_REGULAR", "CC_INTERMEDIATE", "CC_CHP", "CT_CHP", "ST_CHP", "ST_GAS"],
        )
        cf = {
            "CF1_cc_regular_committed_taker": taker(
                is_comm & np.isin(grp, ["CC_REGULAR", "CC_INTERMEDIATE"])
            ),
            "CF2_gas_committed_taker": taker(is_comm & gas_g),
        }
        mc3 = mc.copy()
        cce = np.isin(grp, ["CC_REGULAR", "CC_INTERMEDIATE"]) & (fam == "econ")
        mc3[cce] -= 1.0
        cf["CF3_cc_econ_minus_1usd"] = clear(mc3, mg, flex)
        cf_out = {
            k: {
                "mean": round(float(np.nanmean(v)), 2),
                "median": round(float(np.nanmedian(v)), 2),
            }
            for k, v in cf.items()
        }
        out[str(y)] = {
            "p0_stack_price_at_model_q": round(float(np.nanmean(p0)), 2),
            "p0_stack_price_median": round(float(np.nanmedian(p0)), 2),
            "counterfactual_clears": cf_out,
            "p_model_median": round(float(np.median(pm[t])), 2),
            "p_hub_median": round(float(np.median(ph[t])), 2),
            "night_hours": int(len(t)),
            "p_model": round(float(pm[t].mean()), 2),
            "p_hub": round(float(ph[t].mean()), 2),
            "gap_flex_mw_total": round(float(gap_mw.sum(0).mean()), 0),
            "gap_flex_mw_by_class_band": {
                k: round(float(v), 0)
                for k, v in by.sort_values(ascending=False).items()
                if v > 20
            },
            "flex_mw_within_2usd_of_p_model": round(slope_mw_per_4usd, 0),
            "gap_offer_decomp": dec_rows,
            "night_floor_mw": round(float(mg[:, t].sum(0).mean()), 0),
            "night_floor_by_class": {
                k: round(float(v), 0)
                for k, v in pd.Series(mg[:, t].sum(1) / len(t))
                .groupby(grp)
                .sum()
                .sort_values(ascending=False)
                .items()
                if v > 50
            },
        }
        print(y, json.dumps(out[str(y)])[:1500], flush=True)
        path.write_text(json.dumps(out, indent=1))
    return 0


def _cf4(st, mc, cap, mg, flex, grp, fam, t, q, pm, ph, p0, frac_arg):
    """miso-286 CF4: floor only detector-eligible CC committed rows while online."""
    frac = frac_arg
    if frac is None:
        src = REPO / (
            "data/raw/_processed-legacy/campd_gas_commitment_params_plant_MISO.csv"
        )
        tab = pd.read_csv(src)
        frac = float(tab.loc[tab.plant_class == "CC_REGULAR", "min_load_frac"].iloc[0])
    fa = st["fleet_arrays"]
    fleet = st["fleet"]
    n = len(fleet)
    pmax = np.asarray(fa.pmax, float)
    avail = np.asarray(fa.availability, float)
    plant_pmax: dict[str, float] = {}
    for g, gen in enumerate(fleet):
        if getattr(gen, "is_campd_bin", False):
            k = gen.unit_id.rpartition("_")[0]
            plant_pmax[k] = plant_pmax.get(k, 0.0) + pmax[g]
    from market_sim.pipeline.commitment import miso_gas_ecomin_min_load_fracs

    fr = miso_gas_ecomin_min_load_fracs(fleet, fa, frac)
    target = np.zeros(n)
    for g, gen in enumerate(fleet):
        if fr[g] <= 0.0:
            continue
        pp = (
            plant_pmax.get(gen.unit_id.rpartition("_")[0], pmax[g])
            if getattr(gen, "is_campd_bin", False)
            else pmax[g]
        )
        target[g] = min(fr[g] * pp, pmax[g])
    elig = target > 0.0
    pr0 = np.full(len(t), np.nan)
    pr4 = np.full(len(t), np.nan)
    comm_mw = np.zeros(len(t))
    floored_add = np.zeros(len(t))
    for j, tt in enumerate(t):
        o = np.argsort(mc[:, tt])
        cum = mg[:, tt].sum() + np.cumsum(flex[o, tt])
        k = min(int(np.searchsorted(cum, q[j])), n - 1)
        pr0[j] = mc[o[k], tt]
        disp = np.zeros(n)
        disp[o[:k]] = flex[o[:k], tt]
        prev = cum[k - 1] if k > 0 else mg[:, tt].sum()
        disp[o[k]] = max(0.0, q[j] - prev)
        disp += mg[:, tt]
        online = elig & (disp > 0.05 * pmax)
        comm_mw[j] = disp[elig].sum()
        fl = np.where(online, target * avail[:, tt], 0.0)
        # Only floored rows change: a zeros-init max() would collapse the
        # priced export sinks' pmin < 0 to 0 (the caiso-138 §D defect the
        # mechanism avoids with preserve_absorption=True).
        mg2 = np.where(
            online, np.maximum(mg[:, tt], np.minimum(fl, cap[:, tt])), mg[:, tt]
        )
        floored_add[j] = (mg2 - mg[:, tt]).sum()
        f2 = cap[:, tt] - mg2
        cum2 = mg2.sum() + np.cumsum(f2[o])
        k2 = min(int(np.searchsorted(cum2, q[j])), n - 1)
        pr4[j] = mc[o[k2], tt]
    return {
        "min_load_frac": round(frac, 4),
        "eligible_rows": int(elig.sum()),
        "eligible_mw": round(float(pmax[elig].sum()), 0),
        "eligible_groups": sorted(set(grp[elig].tolist())),
        "p0_median": round(float(np.nanmedian(pr0)), 2),
        "cf4_median": round(float(np.nanmedian(pr4)), 2),
        "delta_median": round(float(np.nanmedian(pr4) - np.nanmedian(pr0)), 2),
        "delta_mean": round(float(np.nanmean(pr4) - np.nanmean(pr0)), 2),
        "hub_median": round(float(np.nanmedian(ph[t])), 2),
        "p1_median": round(float(np.median(pm[t])), 2),
        "stack_online_eligible_committed_mw": round(float(comm_mw.mean()), 0),
        "floor_mw_added_vs_min_gen": round(float(floored_add.mean()), 0),
        "hours_price_moved": int((np.abs(pr4 - pr0) > 0.01).sum()),
        "night_hours": int(len(t)),
    }


if __name__ == "__main__":
    raise SystemExit(main())
