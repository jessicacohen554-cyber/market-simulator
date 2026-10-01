"""SPP-51b phase 0.1b (ZERO LP): the model's OWN supply stack at mid load.

The mid-load residual is +24 to +35 % while the top-decile residual is -12 to -15 %,
so the object is a ROTATION.  This asks the structural question behind it: at the
hours where the model is dear, does it still HAVE cheap capacity available that it is
not clearing on -- i.e. is the marginal unit too inefficient because the efficient
units are absent/derated, or because something keeps them from setting the price?

Inputs: the HEAD (= SPP-50) LP input arrays from ``marginal.py --build``; the run's
own hourly ISO price from its committed payload; and keeper-3's committed
``class_hourly`` for the THERMAL RESIDUAL LOAD.  The residual is legitimate to take
from keeper-3 because the non-thermal side is common to both runs: SPP-50 measured
system wind delivered unchanged to 0.000000 TWh (only the N/S split moved) and LP
re-curtailment 0.0006-0.0017 %, and ``demand`` is bit-identical between the two.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).parent))

OUT = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "e7ea1db8-8d13-5aa9-9561-fc9c88bbd737/scratchpad/spp51b"
)
KH = REPO / "results/calibration/spp43_screened_B/hourly"
YEARS = (2023, 2024, 2025)
THERMAL_PREFIX = ("CC", "CT", "ST", "COAL", "OTHER")


def thermal_residual(year: int) -> np.ndarray:
    df = pd.read_parquet(KH / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    df = df[df["klass"].astype(str).str.startswith(THERMAL_PREFIX)]
    return df.groupby("hour")["mw"].sum().sort_index().to_numpy(dtype=float)


def startup_costs(year: int) -> pd.DataFrame:
    """Per-row startup cost ($/MW) through ``commitment._startup_cost``, cached.

    Read through the model's OWN accessor, never off a ``Generator`` attribute: a
    CAMPD bin carries its startup cost on the bin (``startup_cost_per_mw``) and a
    legacy row looks it up in the heat-rate-keyed table, so an attribute read
    reports $0.00 on every row and makes the markup look immaterial.  It is not --
    coal bins carry up to $100/MW and are the largest eligible block.
    """
    cache = OUT / f"startup_{year}.csv"
    if cache.exists():
        return pd.read_csv(cache)
    import json

    from market_sim.model.commitment import _startup_cost
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration/spp43_screened_B"
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    r = run_year(
        year,
        "SPP",
        8760,
        float(meta["gas_prices"][str(year)]),
        {},
        fleet_only=True,
        **kw,
    )
    fleet, fa = r["fleet"], r["fleet_arrays"]
    df = pd.DataFrame(
        [
            dict(
                g=g,
                fuel_type=gen.fuel_type,
                pmax=float(fa.pmax[g]),
                su=float(_startup_cost(gen, float(fa.heat_rate[g]))),
            )
            for g, gen in enumerate(fleet)
        ]
    )
    df.to_csv(cache, index=False)
    return df


def main() -> None:
    from prices import model_price, actual_rt

    for year in YEARS:
        a = np.load(OUT / f"head_arrays_{year}.npz")
        rows = pd.read_csv(OUT / f"head_rows_{year}.csv")
        mc, av, pmax = a["mc_base"], a["availability"], a["pmax"]
        dem = a["demand"]
        T = mc.shape[1]
        price = model_price("2026-09-08-spp-50-rebaseline", year)[:T]
        act = actual_rt(year)[:T]
        load = (dem.sum(axis=0) if dem.ndim == 2 else dem)[:T]
        res = thermal_residual(year)[:T]
        availmw = pmax[:, None] * (av if av.ndim == 2 else av[None, :])
        grp = rows["plant_group"].fillna("").to_numpy()
        grp = np.where(grp == "", rows["fuel_type"].astype(str).to_numpy(), grp)
        fam = np.where(
            np.char.startswith(grp.astype(str), "COAL"),
            "COAL",
            np.where(
                np.char.startswith(grp.astype(str), "CC"),
                "CC",
                np.where(
                    np.char.startswith(grp.astype(str), "CT"),
                    "CT",
                    np.where(np.char.startswith(grp.astype(str), "ST"), "ST", "OTH"),
                ),
            ),
        )

        ok = (
            np.isfinite(price) & np.isfinite(act) & np.isfinite(load) & np.isfinite(res)
        )
        pct = np.full(T, np.nan)
        pct[ok] = pd.Series(load[ok]).rank(pct=True).to_numpy() * 100.0
        mid = np.where(ok & (pct >= 25) & (pct < 75))[0]

        # Merit-order clearing on the model's OWN arrays at its OWN thermal residual.
        # The LP forces every row with pmin > 0 to generate at least min_gen, so the
        # marginal unit is chosen among HEADROOM (pmax*avail - min_gen) against the
        # residual NET of that forced block -- not among gross available MW.
        mg = a["min_gen"]
        mg = mg if mg.ndim == 2 and mg.shape[0] == len(pmax) else np.zeros_like(availmw)
        head = np.maximum(availmw - mg, 0.0)
        forced = mg.sum(axis=0)
        clear = np.full(len(mid), np.nan)
        clear_gross = np.full(len(mid), np.nan)
        cheap_below_act = np.zeros(len(mid))
        headroom = {k: np.zeros(len(mid)) for k in ("COAL", "CC", "CT", "ST")}
        for i, h in enumerate(mid):
            m = mc[:, h]
            o = np.argsort(m)
            cum = np.cumsum(head[o, h])
            j = int(np.searchsorted(cum, max(res[h] - forced[h], 0.0)))
            if j < len(o):
                clear[i] = m[o[j]]
            cg = np.cumsum(availmw[o, h])
            jg = int(np.searchsorted(cg, res[h]))
            if jg < len(o):
                clear_gross[i] = m[o[jg]]
            w = availmw[:, h]
            cheap_below_act[i] = w[m <= act[h]].sum()
            for k in headroom:
                sel = (fam == k) & (m <= act[h])
                headroom[k][i] = w[sel].sum()

        print(
            f"\n================ {year}  (mid-load 25-75 pct, {len(mid)} hours) ================"
        )
        print(f"  thermal residual load, mean            {res[mid].mean():>10,.0f} MW")
        print(
            f"  LP price (model), load-wtd mean        {np.average(price[mid], weights=load[mid]):>10.2f} $/MWh"
        )
        print(
            f"  merit order, GROSS available MW        {np.nanmean(clear_gross):>10.2f} $/MWh"
        )
        print(
            f"  merit order, HEADROOM net of forced min-gen "
            f"{np.nanmean(clear):>10.2f} $/MWh  <-- the LP's own choice set"
        )
        print(
            f"  forced min-gen block, mean             {forced[mid].mean():>10,.0f} MW "
            f"({100 * forced[mid].mean() / res[mid].mean():.1f} % of the thermal residual)"
        )
        print(
            f"  ACTUAL RT price, load-wtd mean         {np.average(act[mid], weights=load[mid]):>10.2f} $/MWh"
        )
        print(
            f"  available MW priced at or below the ACTUAL price, mean "
            f"{cheap_below_act.mean():>10,.0f} MW  "
            f"({100 * cheap_below_act.mean() / res[mid].mean():.1f} % of the residual)"
        )
        for k in ("COAL", "CC", "CT", "ST"):
            print(f"      of which {k:5s} {headroom[k].mean():>9,.0f} MW")
        short = res[mid] - cheap_below_act
        print(
            f"  SHORTFALL (residual - capacity below actual price), mean "
            f"{short.mean():>+10,.0f} MW; hours short: {int((short > 0).sum())}/{len(mid)}"
        )

        # ---- the P1 startup-amortization leg of the wedge attribution ----------
        # mc_bid = mc_base + compute_monthly_markup(...); markup = startup / avg_run.
        # The REALISED markup needs the P0 dispatch, which no committed artifact
        # carries, so the stack is re-cleared across a RANGE of average run lengths:
        # a bracket, never a point claim. ST_GAS is exempt on this recipe
        # (gas_st_startup_cost=False); coal is NOT (coal_warm_committed=False).
        su = startup_costs(year)
        sc, ftype = su["su"].to_numpy(), su["fuel_type"].astype(str).to_numpy()
        elig = (sc > 0) & (ftype != "gas_st")
        by = ", ".join(
            f"{lbl} {pmax[elig & (ftype == ft)].sum():,.0f}"
            for lbl, ft in (("coal", "coal"), ("CC", "gas_cc"), ("CT", "gas_ct"))
        )
        print(
            f"  P1 startup markup: {int(elig.sum())} eligible rows, "
            f"{pmax[elig].sum():,.0f} MW ({by})"
        )
        lp = float(np.average(price[mid], weights=load[mid]))
        base = float(np.nanmean(clear))
        for rh in (2, 6, 12, 24):
            bid = mc + np.where(elig, sc / rh, 0.0)[:, None]
            cl = np.empty(len(mid))
            for i, h in enumerate(mid):
                m = bid[:, h]
                o = np.argsort(m)
                cum = np.cumsum(head[o, h])
                k = int(np.searchsorted(cum, max(res[h] - forced[h], 0.0)))
                cl[i] = m[o[min(k, len(o) - 1)]]
            v = float(np.average(cl, weights=load[mid]))
            print(
                f"      avg run {rh:>3d} h -> mid-load ${v:6.2f}  "
                f"(+${v - base:.2f} on the base-cost merit price; the LP is ${lp:.2f})"
            )


if __name__ == "__main__":
    main()
