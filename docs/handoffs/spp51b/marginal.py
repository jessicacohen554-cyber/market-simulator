"""SPP-51b phase 0.1 (ZERO LP): WHO sets the price in the rich hours, and what is
that unit's marginal cost made of?

Rebuilds the LP input arrays at HEAD on keeper-3's own recipe through the sanctioned
``run_year(fleet_only=True)`` seam (``scripts.replay_keeper.run_year_kwargs`` +
``derived_run_year_inputs`` -- the same reconstruction SPP-49's census and SPP-50's
array census used).  At HEAD that surface IS SPP-50's: SPP-50 §4 measured 17 of 22
arrays bit-identical to keeper-3 with the movers exactly the two SPP-49 seams and the
SPP-48 wind level rule, all of which are landed on ``main``.

For each hour it takes the run's own ISO price (recovered from the committed payload
by ``prices.py``) and identifies every fleet row whose marginal cost sits within a
tolerance of that price, weighted by AVAILABLE MW -- the merit-order lane's marginal
class instrument -- then decomposes those rows' ``mc = heat_rate x fuel + vom``.

usage:
    uv run python docs/handoffs/spp51b/marginal.py --build
    uv run python docs/handoffs/spp51b/marginal.py --report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

OUT = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "e7ea1db8-8d13-5aa9-9561-fc9c88bbd737/scratchpad/spp51b"
)
OUT.mkdir(parents=True, exist_ok=True)

KEEPER = "spp43_screened_B"
YEARS = (2023, 2024, 2025)
TOL = 0.25  # $/MWh band around the clearing price (the merit-order lane's value)
BANDS = [(0, 10), (10, 25), (25, 50), (50, 75), (75, 90), (90, 95), (95, 98), (98, 100)]


def build(year: int) -> None:
    arr_p, rows_p = OUT / f"head_arrays_{year}.npz", OUT / f"head_rows_{year}.csv"
    if arr_p.exists() and rows_p.exists():
        print(f"  {year}: cached")
        return
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / "results/calibration" / KEEPER
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    gp = float(meta["gas_prices"][str(year)])
    r = run_year(year, "SPP", 8760, gp, {}, fleet_only=True, **kw)
    fleet, fa = r["fleet"], r["fleet_arrays"]
    np.savez_compressed(
        arr_p,
        pmax=np.asarray(fa.pmax),
        pmin=np.asarray(fa.pmin),
        heat_rate=np.asarray(fa.heat_rate),
        vom=np.asarray(fa.vom),
        zone_idx=np.asarray(fa.zone_idx),
        availability=np.asarray(fa.availability),
        min_gen=np.asarray(fa.min_gen) if fa.min_gen is not None else np.zeros(1),
        mc_base=np.asarray(r["mc_base"]),
        fuel_prices=np.asarray(r["fuel_prices"]),
        demand=np.asarray(r["demand"]),
    )
    pd.DataFrame(
        [
            dict(
                g=g,
                unit_id=gen.unit_id,
                plant_code=int(gen.plant_code or 0),
                name=gen.name,
                zone=gen.zone,
                plant_group=gen.plant_group or "",
                fuel_type=gen.fuel_type,
                state=str(getattr(gen, "state", "") or ""),
                pmax=float(fa.pmax[g]),
                heat_rate=float(fa.heat_rate[g]),
                vom=float(fa.vom[g]),
            )
            for g, gen in enumerate(fleet)
        ]
    ).to_csv(rows_p, index=False)
    print(f"  {year}: {len(fleet)} units -> {arr_p.name}")


def report(year: int) -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    from prices import model_price, actual_rt

    a = np.load(OUT / f"head_arrays_{year}.npz")
    rows = pd.read_csv(OUT / f"head_rows_{year}.csv")
    mc, av, pmax = a["mc_base"], a["availability"], a["pmax"]
    hr, fuel, vom = a["heat_rate"], a["fuel_prices"], a["vom"]
    dem = a["demand"]
    T = mc.shape[1]

    price = model_price("2026-09-08-spp-50-rebaseline", year)[:T]
    act = actual_rt(year)[:T]
    load = dem.sum(axis=0) if dem.ndim == 2 else dem
    load = np.asarray(load)[:T]

    avail_mw = pmax[:, None] * av if av.ndim == 2 else pmax[:, None] * av[None, :]
    grp = rows["plant_group"].fillna("").to_numpy()
    grp = np.where(grp == "", rows["fuel_type"].astype(str).to_numpy(), grp)

    ok = np.isfinite(price) & np.isfinite(act) & np.isfinite(load)
    pct = np.full(T, np.nan)
    pct[ok] = pd.Series(load[ok]).rank(pct=True).to_numpy() * 100.0

    recs = []
    for lo, hi in BANDS:
        sel = ok & (pct >= lo) & ((pct < hi) if hi < 100 else True)
        if not sel.any():
            continue
        idx = np.where(sel)[0]
        near = np.abs(mc[:, idx] - price[idx][None, :]) <= TOL
        w = near * avail_mw[:, idx]
        tot = w.sum()
        if tot <= 0:
            continue
        share = pd.Series(w.sum(axis=1)).groupby(grp).sum() / tot
        # cost decomposition of the marginal rows, MW-weighted
        rw = w.sum(axis=1)
        fw = (near * avail_mw[:, idx] * fuel[:, idx]).sum() / tot
        hrw = float(np.average(hr, weights=rw)) if rw.sum() > 0 else np.nan
        vw = float(np.average(vom, weights=rw)) if rw.sum() > 0 else np.nan
        top = share.sort_values(ascending=False).head(4)
        recs.append(
            {
                "band": f"{lo}-{hi}",
                "hrs": int(sel.sum()),
                "model$": round(float(np.average(price[idx], weights=load[idx])), 2),
                "act$": round(float(np.average(act[idx], weights=load[idx])), 2),
                "err%": round(
                    100
                    * (
                        np.average(price[idx], weights=load[idx])
                        / np.average(act[idx], weights=load[idx])
                        - 1
                    ),
                    1,
                ),
                "marg_HR": round(hrw, 3),
                "marg_fuel$": round(float(fw), 3),
                "marg_vom$": round(vw, 2),
                "hr*fuel": round(hrw * float(fw), 2),
                "marginal classes (avail-MW share)": ", ".join(
                    f"{k} {v:.0%}" for k, v in top.items()
                ),
            }
        )
    print(
        f"\n### {year} — who is marginal, by system-load band (SPP-50 input surface, tol ±${TOL})"
    )
    print(pd.DataFrame(recs).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--years", type=int, nargs="*", default=list(YEARS))
    args = ap.parse_args()
    for y in args.years:
        if args.build:
            build(y)
        if args.report:
            report(y)


if __name__ == "__main__":
    main()
