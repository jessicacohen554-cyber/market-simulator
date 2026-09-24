#!/usr/bin/env python3
"""miso-270 Task C phase 0: localize the keeper's Oct-Nov 2021 low price.

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Nothing is solved. Keeper
``2026-09-24-miso-268-coal-yard`` is read from its committed hourly sidecars
and, for the offer-side legs, rebuilt with ``run_year(..., fleet_only=True)``
on its own recipe (the miso-269 ``rebuild``). Localize, never exclude: every
month is reported, and Sep / Dec 2021 are the adjacent controls.

LEGS (each one answers "is it this?"):

1. **Price, month x zone.** Keeper P1 load-weighted price vs the bench
   ``avgLMP.rt_lw_mon`` (the C3b scorer basis — reproduced first) and vs the
   zonal RT hub means, so the gap is placed in zones and hours.
2. **Volumes.** Keeper monthly class energy vs EIA-930 MISO BA net generation
   by fuel (coal, gas, wind, nuclear) and net interchange, and vs the bench
   per-plant CAMPD monthly energy by class group. A merit-order shift (too
   much coal, too little gas) or a seam / wind excess shows here.
3. **Reserve and scarcity.** Monthly mean reserve dual per family, shortfall,
   slack/dump.
4. **Offer side** (rebuild). Per month: available capacity by class
   (pmax x availability — the outage overlay), capacity-weighted fuel price and
   econ-band mc by class, and the price-setter census (miso-264 matcher, the
   miso-269 TOL, fixed, never swept).

Usage::

    uv run python scripts/probes/_miso270_octnov2021_phase0.py            # all legs
    uv run python scripts/probes/_miso270_octnov2021_phase0.py --no-rebuild  # legs 1-3
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.probes._miso269_transport_static_phase0 import (  # noqa: E402
    INTERNAL, KEEPER, TOL, actual_rt, rebuild,
)

YEAR = 2021
OUT = REPO / "results/calibration/_miso270_octnov2021_phase0.json"
BENCH = REPO / f"frontend/data/backcast/bench/MISO/{YEAR}.json.gz"
EIA930 = [REPO / f"data/raw/eia-930/EIA930_BALANCE_{YEAR}_{h}.parquet" for h in ("Jan_Jun", "Jul_Dec")]
MONTH = (pd.Timestamp(f"{YEAR}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month.to_numpy()
HOD = np.arange(8760) % 24
COAL = ("COAL", "COAL_BIT", "COAL_LIGNITE", "COAL_PRB")
GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP")


def _r(x, n=2):
    return [round(float(v), n) for v in x]


def leg_price(sysd: pd.DataFrame, bench: dict) -> dict:
    """Monthly LW price vs bench, zone split, HOD split for Sep-Dec."""
    piv = {c: sysd.pivot(index="hour", columns="zone", values=c)[list(INTERNAL)].to_numpy(float).T
           for c in ("price", "demand", "slack", "dump", "reserve_price")}
    p, d = piv["price"], piv["demand"]
    mm = np.array([(p * d)[:, MONTH == m].sum() / d[:, MONTH == m].sum() for m in range(1, 13)])
    am = np.array(bench["avgLMP"]["rt_lw_mon"], float)
    err = mm - am
    nrmse = float(np.sqrt(np.mean(err ** 2)) / am.mean())
    act = actual_rt(YEAR)
    zone = {}
    for zi, zz in enumerate(INTERNAL):
        ok = np.isfinite(act[zi])
        zone[zz] = {
            "model": _r([np.average(p[zi][(MONTH == m) & ok], weights=d[zi][(MONTH == m) & ok]) for m in range(1, 13)]),
            "actual": _r([np.average(act[zi][(MONTH == m) & ok], weights=d[zi][(MONTH == m) & ok]) for m in range(1, 13)]),
            "load_share_octnov": round(float(d[zi][(MONTH >= 10) & (MONTH <= 11)].sum() / d[:, (MONTH >= 10) & (MONTH <= 11)].sum()), 3),
        }
    hod = {}
    ok = np.isfinite(act)
    for m in (9, 10, 11, 12):
        row_m, row_a = [], []
        for h in range(24):
            k = ((MONTH == m) & (HOD == h))[None, :] & ok
            w = np.where(k, d, 0.0)
            row_m.append((p * w).sum() / w.sum())
            row_a.append((np.nan_to_num(act) * w).sum() / w.sum())
        hod[str(m)] = {"model": _r(row_m), "actual": _r(row_a)}
    # daily LW model vs actual (hub basis) for Sep-Dec: is the gap every day or a few days?
    day = np.arange(8760) // 24
    w = np.where(ok, d, 0.0)
    dm = np.bincount(day, (p * w).sum(0))[:365] / np.bincount(day, w.sum(0))[:365]
    da = np.bincount(day, (np.nan_to_num(act) * w).sum(0))[:365] / np.bincount(day, w.sum(0))[:365]
    doy = {m: np.unique(day[MONTH == m]) for m in (9, 10, 11, 12)}
    daily = {str(m): {"model": _r(dm[doy[m]]), "actual": _r(da[doy[m]]),
                      "days_model_low_gt10": int(((dm - da)[doy[m]] < -10).sum()),
                      "median_gap": round(float(np.median((dm - da)[doy[m]])), 2)} for m in doy}
    return {
        "monthly_model": _r(mm), "monthly_bench": _r(am), "monthly_err": _r(err),
        "sse_share": _r(err ** 2 / (err ** 2).sum(), 3),
        "c3b_nrmse": round(nrmse, 4),
        "slack_mwh_mon": _r([piv["slack"][:, MONTH == m].sum() for m in range(1, 13)], 0),
        "dump_mwh_mon": _r([piv["dump"][:, MONTH == m].sum() for m in range(1, 13)], 0),
        "reserve_price_lw_mon": _r([(piv["reserve_price"] * d)[:, MONTH == m].sum() / d[:, MONTH == m].sum() for m in range(1, 13)]),
        "zone": zone, "hod": hod, "daily": daily,
    }


def leg_volume(bench: dict) -> dict:
    """Keeper monthly class TWh vs EIA-930 and bench CAMPD per-plant monthly."""
    ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    ch["m"] = MONTH[ch["hour"].to_numpy()]
    mdl = ch.groupby(["klass", "m"], observed=True)["mw"].sum().unstack(fill_value=0.0) / 1e6
    agg = {
        "coal": mdl.reindex(COAL).fillna(0).sum(),
        "gas": mdl.reindex(GAS).fillna(0).sum(),
        "wind": mdl.loc["wind"], "nuclear": mdl.loc["nuclear"], "import": mdl.loc["import"],
        "hydro": mdl.loc["hydro"],
    }
    e = pd.concat([pd.read_parquet(f) for f in EIA930])
    e = e[e["Balancing Authority"] == "MISO"].copy()
    ts = pd.to_datetime(e["UTC Time at End of Hour"]) - pd.Timedelta(hours=6)  # EST, hour-ending
    e = e[ts.dt.year == YEAR]
    e["m"] = ts[ts.dt.year == YEAR].dt.month.to_numpy()

    def col(name):
        c = f"Net Generation (MW) from {name} (Adjusted)"
        return e.groupby("m")[c].sum() / 1e6

    eia = {"coal": col("Coal"), "gas": col("Natural Gas"), "wind": col("Wind"), "nuclear": col("Nuclear"),
           "hydro": col("Hydropower and Pumped Storage"),
           "net_import": -e.groupby("m")["Total Interchange (MW) (Adjusted)"].sum() / 1e6}
    # bench CAMPD monthly energy by class group (per-plant c_mon; TWh)
    camp: dict = {}
    for pl in bench["plants"].values():
        g = pl["group"]
        camp.setdefault(g, np.zeros(12))
        camp[g] += np.array(pl["c_mon"], float)
    mdl_cls = {k: _r(mdl.loc[k].reindex(range(1, 13)).fillna(0), 3) for k in mdl.index}
    return {
        "model": {k: _r(v.reindex(range(1, 13)).fillna(0), 3) for k, v in agg.items()},
        "eia930": {k: _r(v.reindex(range(1, 13)).fillna(0), 3) for k, v in eia.items()},
        "model_class": mdl_cls,
        "campd_class": {k: _r(v, 3) for k, v in camp.items()},
    }


def leg_reserve() -> dict:
    """Monthly mean dual / shortfall per reserve family."""
    r = pd.read_parquet(KEEPER / f"hourly/reserve_family_{YEAR}.parquet")
    r = r[r["pass"] == "P1"].copy()
    r["m"] = MONTH[r["hour"].to_numpy()]
    out = {}
    for fam, g in r.groupby("family", observed=True):
        gg = g.groupby("m")
        out[str(fam)] = {"dual": _r(gg["dual"].mean().reindex(range(1, 13))),
                         "shortfall_mwh": _r(gg["shortfall_mw"].sum().reindex(range(1, 13)), 0),
                         "held_over_req": _r((gg["held_mw"].mean() / gg["requirement_mw"].mean()).reindex(range(1, 13)), 3)}
    return out


def leg_offer(sysd: pd.DataFrame) -> dict:
    """Rebuild: capacity-in-service, fuel, mc and price-setter census by month."""
    piv = {c: sysd.pivot(index="hour", columns="zone", values=c)[list(INTERNAL)].to_numpy(float).T
           for c in ("price", "demand")}
    st = rebuild(YEAR, False)
    fa, fleet = st["fleet_arrays"], st["fleet"]
    mc = np.asarray(st["mc_base"], float)
    fp = np.asarray(st["fuel_prices"], float)
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    cap = pmax[:, None] * av
    zone = np.array([str(getattr(g, "zone", "") or "") for g in fleet])
    klass = np.array([str(getattr(g, "plant_group", "") or getattr(g, "fuel_type", "")) for g in fleet])
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    uid = np.asarray(fa.unit_ids, dtype=object)
    band = np.array([u.rsplit("_", 1)[-1] if "_" in u else "" for u in uid])
    fam = np.array([f"{k}|{f}|{b}" for k, f, b in zip(klass, fuel, band)])

    cls_cap, cls_fuel, cls_mc = {}, {}, {}
    for k in np.unique(klass):
        gi = klass == k
        cls_cap[k] = _r([cap[gi][:, MONTH == m].sum(0).mean() / 1e3 for m in range(1, 13)])  # GW in service
        pm = pmax[gi]
        cls_fuel[k] = _r([(fp[gi][:, MONTH == m].mean(1) * pm).sum() / max(pm.sum(), 1e-9) for m in range(1, 13)], 3)
        eg = gi & np.char.startswith(band.astype(str), "econ")
        if eg.any():
            pe = pmax[eg]
            cls_mc[k] = _r([(mc[eg][:, MONTH == m].mean(1) * pe).sum() / pe.sum() for m in range(1, 13)])
    census = {}
    for m in (9, 10, 11, 12):
        hmask = MONTH == m
        w: Counter = Counter()
        mcw: Counter = Counter()
        tot = matched = 0.0
        for zi, zz in enumerate(INTERNAL):
            p = piv["price"][zi]
            d = np.where(hmask, piv["demand"][zi], 0.0)
            tot += d.sum()
            done = np.zeros(8760, bool)
            for scope in ("local", "pooled"):
                gi = np.where(zone == zz)[0] if scope == "local" else np.arange(zone.size)
                hit = (cap[gi] > 1e-6) & (np.abs(mc[gi] - p[None, :]) <= TOL) & ~done[None, :]
                n = hit.sum(0)
                has = (n > 0) & hmask
                mwh = np.where(hit, 1.0, 0.0) / np.maximum(n, 1)[None, :] * np.where(has, d, 0.0)[None, :]
                per = mwh.sum(1)
                for j in np.nonzero(per > 0)[0]:
                    w[fam[gi[j]]] += per[j]
                    mcw[fam[gi[j]]] += float((mwh[j] * mc[gi[j]]).sum())
                matched += float(d[has].sum())
                done |= n > 0
        # coarse class-of-setter shares
        coarse: Counter = Counter()
        for k, v in w.items():
            c = k.split("|")[0]
            coarse["coal" if c in COAL else "gas" if c in GAS else c] += v
        census[str(m)] = {
            "matched_share": round(matched / tot, 4),
            "coarse": {k: round(v / max(matched, 1), 4) for k, v in coarse.most_common()},
            "top": [{"family": k, "share": round(v / max(matched, 1), 4), "mean_mc": round(mcw[k] / v, 2)}
                    for k, v in w.most_common(10)],
        }
    return {"cap_in_service_gw": cls_cap, "fuel_price_capw": cls_fuel, "econ_mc_capw": cls_mc,
            "setter_census": census, "coal_plants": leg_coal_plants(uid, klass, cap),
            "coal_budget": leg_coal_budget(fa)}


def leg_coal_budget(fa) -> dict:
    """Keeper coal-budget rows vs keeper coal burn, by month.

    The pooled miso-259 rows cap each MONTH at annual / 12 (flat); the miso-268
    yard rows cap each yard's YEAR. Model burn is class MWh x the coal fleet's
    capacity-weighted heat rate (an approximation stated as such: the sidecar
    carries MW, not MMBtu). CAMPD burn on the same basis is the bench per-plant
    monthly energy. A month whose model burn sits AT the flat cap while CAMPD
    burned above it is a month the flat timing limb binds against the measured
    seasonal shape.
    """
    from market_sim.data.coal_fuel_inventory import build_coal_fuel_budget, build_coal_plant_budget

    gi, budget, _, coeff, _, prov = build_coal_fuel_budget(fa, YEAR, hours=8760)
    hr = float((coeff * np.asarray(fa.pmax, float)[gi]).sum() / np.asarray(fa.pmax, float)[gi].sum())
    cp = build_coal_plant_budget(fa, YEAR, hours=8760)
    ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{YEAR}.parquet")
    ch = ch[(ch["pass"] == "P1") & ch["klass"].isin(COAL)]
    mdl = np.bincount(MONTH[ch["hour"].to_numpy()] - 1, ch["mw"].to_numpy(float), 12) / 1e6
    bench = json.load(gzip.open(BENCH))["bench"]["plants"]
    camp = sum(np.array(p_["c_mon"], float) for p_ in bench.values() if p_["group"].startswith("COAL")) / 1e3
    cap_twh = budget[0] / hr / 1e6
    return {"hr_capw": round(hr, 3), "pooled_monthly_cap_twh_equiv": _r(cap_twh, 3),
            "model_coal_twh": _r(mdl, 3), "campd_coal_twh": _r(camp, 3),
            "model_over_cap": _r(mdl / cap_twh, 3), "campd_over_cap": _r(camp / cap_twh, 3),
            "annual_pooled_twh_equiv": round(float(prov.annual_budget_mmbtu / hr / 1e6), 2),
            "annual_yard_rows_twh_equiv": round(float(cp[-1].annual_budget_mmbtu / hr / 1e6), 2) if cp else None,
            "yard_rows": int(cp[-1].n_entities) if cp else 0,
            # SOC-carry check (the miso-259 named successor), zero minimum stock:
            # cumulative allowance = opening stock + prior-years rate x m/12.
            "opening_twh_equiv": round(float(prov.opening_stock_tons * prov.mmbtu_per_ton / hr / 1e6), 2),
            "rate_twh_equiv_per_yr": round(float(prov.delivery_rate_tons_per_year * prov.mmbtu_per_ton / hr / 1e6), 2),
            "carry_headroom_campd_twh": _r(prov.opening_stock_tons * prov.mmbtu_per_ton / hr / 1e6
                                          + prov.delivery_rate_tons_per_year * prov.mmbtu_per_ton / hr / 1e6
                                          * np.arange(1, 13) / 12 - np.cumsum(camp), 2),
            "carry_headroom_model_twh": _r(prov.opening_stock_tons * prov.mmbtu_per_ton / hr / 1e6
                                          + prov.delivery_rate_tons_per_year * prov.mmbtu_per_ton / hr / 1e6
                                          * np.arange(1, 13) / 12 - np.cumsum(mdl), 2)}


def leg_coal_plants(uid: np.ndarray, klass: np.ndarray, cap: np.ndarray) -> dict:
    """Coal, plant grain: model in-service energy vs CAMPD monthly energy.

    A plant whose CAMPD month is DARK (< 5 % of its own max month) while the
    model keeps >= 50 % of its pmax in service is energy the model can burn
    that the real plant did not — an outage/lay-up the overlay misses, or a
    plant the real owner held off (conservation/economic reserve). Reported,
    never classified by the residual.
    """
    bench = json.load(gzip.open(BENCH))["bench"]["plants"]
    pid = np.array([(re.match(r"\D*(\d+)", u) or [None, ""])[1] for u in uid])
    coal = np.isin(klass, COAL)
    mon_mwh = np.stack([cap[:, MONTH == m].sum(1) for m in range(1, 13)], 1)  # MWh in service
    pmax_pl: dict = {}
    avail_pl: dict = {}
    for i in np.nonzero(coal)[0]:
        avail_pl.setdefault(pid[i], np.zeros(12))
        avail_pl[pid[i]] += mon_mwh[i]
        pmax_pl[pid[i]] = pmax_pl.get(pid[i], 0.0) + float(cap[i].max())
    hrs = np.array([(MONTH == m).sum() for m in range(1, 13)], float)
    rows, dark_model_on = [], np.zeros(12)
    tot_av, tot_c = np.zeros(12), np.zeros(12)
    for p_, av in avail_pl.items():
        b = bench.get(p_)
        if b is None or b.get("nodata"):
            continue
        c = np.array(b["c_mon"], float) * 1e3  # GWh -> MWh
        frac = av / np.maximum(pmax_pl[p_] * hrs, 1.0)
        dark = c < 0.05 * max(c.max(), 1e-9)
        hit = dark & (frac >= 0.5)
        dark_model_on += np.where(hit, av, 0.0)
        tot_av += av
        tot_c += c
        if hit[9:11].any():
            rows.append({"plant": p_, "name": b["name"], "zone": b["zone"], "pmax_mw": round(pmax_pl[p_], 1),
                         "campd_gwh_sep_dec": _r(c[8:] / 1e3, 1), "model_inservice_frac_sep_dec": _r(frac[8:], 2)})
    rows.sort(key=lambda r: -r["pmax_mw"])
    return {"inservice_twh": _r(tot_av / 1e6), "campd_twh": _r(tot_c / 1e6),
            "campd_cf_of_inservice": _r(tot_c / np.maximum(tot_av, 1), 3),
            "dark_month_model_inservice_twh": _r(dark_model_on / 1e6, 3),
            "octnov_dark_plants": rows}


def main() -> int:
    """CLI."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-rebuild", action="store_true")
    ap.add_argument("--budget-only", action="store_true")
    a = ap.parse_args()
    bench = json.load(gzip.open(BENCH))["bench"]
    sysd = pd.read_parquet(KEEPER / f"hourly/system_{YEAR}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    out["price"] = leg_price(sysd, bench)
    out["volume"] = leg_volume(bench)
    out["reserve"] = leg_reserve()
    if a.budget_only:
        out.setdefault("offer", {})["coal_budget"] = leg_coal_budget(rebuild(YEAR, False)["fleet_arrays"])
    elif not a.no_rebuild:
        out["offer"] = leg_offer(sysd)
    OUT.write_text(json.dumps(out, indent=1))
    print("C3b NRMSE", out["price"]["c3b_nrmse"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
