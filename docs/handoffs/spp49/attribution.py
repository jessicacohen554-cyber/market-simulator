"""SPP-49 §4: reproduce SPP-46's plant-level attribution on the pre- and post-repair arrays.

SPP-46 (`docs/handoffs/spp46/attribution.py`, PRECOMMIT §3 (E)) attributed keeper-3's 2024 gas
split plant by plant: model in-merit energy at keeper-3's OWN P1 zonal prices (strict + half the
marginal band) minus CAMPD measured gross generation, grouped by an INPUT flag read off the row.
This instrument re-runs that construction on the arrays `census.py` saved — `pre` (the committed
keeper's inputs, rebuilt) and `post` (the repaired tree's inputs, rebuilt) — with ONE difference in
the flag reference: the plant's OWN state's N3045 series (US fallback where unpublished; SPP-46 used
KS/OK/TX/NM with a zone-state fallback) and 1.036 $/Mcf->$/MMBtu (SPP-46: 1.037). The flags are
computed once, on the PRE arrays, so the same plant groups are compared before and after.

What "reproduced" means here: the pre-repair groups land near SPP-46's numbers (CT hr_flag +5,013,
CT fuel_low +8,121, CT clean -244, ST_GAS fuel_low +6,136, ST_GAS clean -5,949 GWh in 2024), and
the post-repair arrays move the FLAGGED groups by roughly those amounts while the clean cohorts
stay put. Zero LP: the keeper's dispatch and prices are the committed sidecars; only the row
marginal costs change between pre and post.

Usage: uv run python docs/handoffs/spp49/attribution.py [--tags pre post]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "docs/handoffs/spp49"))
from census import SCRATCH, reference, ref_month  # noqa: E402
from market_sim.data.eia923 import plant_month_price_grid  # noqa: E402
from market_sim.data.fuel.plant_prices import _load_monthly_cache  # noqa: E402

OUT = REPO / "docs/handoffs/spp49"
SPP46 = REPO / "docs/handoffs/spp46"
BUNDLE = REPO / "results/calibration/spp43_screened_B"
YEARS = (2023, 2024, 2025)
TOL = 0.25
CLASSES = {"CC_REGULAR": "cc", "CT_PEAKER": "ct", "ST_GAS": "st"}
NAMED = [57881, 58835, 56326, 3482, 2454, 2446, 6193, 2952, 2956, 4940, 55065, 55463, 2963]


def flags(rows: pd.DataFrame, year: int, ref) -> pd.DataFrame:
    costs = _load_monthly_cache(None)
    plant_state = costs.groupby("plant_id")["state"].first()
    grid = plant_month_price_grid(costs, year, "Natural Gas")
    low = np.zeros(len(rows), bool)
    high = np.zeros(len(rows), bool)
    for g in range(len(rows)):
        if not str(rows.fuel_type[g]).startswith("gas"):
            continue
        pc = int(rows.plant_code[g])
        own = grid.get(pc)
        if own is None:
            continue
        st = str(plant_state.get(pc, ""))
        for m in range(12):
            if np.isnan(own[m]):
                continue
            R, prov = ref_month(ref, st, year, m + 1)
            if prov == "none" or R <= 0:
                continue
            if own[m] < 0.5 * R:
                low[g] = True
            elif own[m] > 2.0 * R:
                high[g] = True
    pg = rows.plant_group.fillna("").astype(str)
    klass = pg.where(pg != "", rows.fuel_type.astype(str)).to_numpy()
    hr = rows.heat_rate.to_numpy().astype(float)
    hr_flag = ((klass == "CT_PEAKER") & (hr < 6.0)) | ((klass == "CC_REGULAR") & (hr > 10.0))
    return pd.DataFrame(dict(klass=klass, flag_low=low, flag_high=high, flag_hr=hr_flag))


def in_merit_energy(rows: pd.DataFrame, arr: dict, year: int) -> np.ndarray:
    mc, av = arr["mc"].astype(float), arr["avail"].astype(float)
    cap = rows.pmax.to_numpy()[:, None] * av
    sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sysp = sysp[sysp["pass"] == "P1"]
    P = sysp.pivot_table(index="hour", columns="zone", values="price").sort_index()
    zone = rows.zone.to_numpy()
    p_row = np.vstack([P[z].to_numpy() for z in zone])
    strict = mc < p_row - TOL
    marg = np.abs(mc - p_row) <= TOL
    return (cap * (strict + 0.5 * marg)).sum(axis=1) / 1e3  # GWh


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tags", nargs="*", default=["pre", "post"])
    a = ap.parse_args()
    ref = reference()
    pd.set_option("display.width", 250)
    for year in YEARS:
        rows_pre = pd.read_csv(SCRATCH / f"rows_pre_SPP_{year}.csv")
        fl = flags(rows_pre, year, ref)
        fl["flag"] = np.select([fl.flag_hr, fl.flag_low, fl.flag_high], ["HR", "fuel_low", "fuel_high"], "clean")
        results = {}
        for tag in a.tags:
            arr_p = SCRATCH / f"arrays_{tag}_SPP_{year}.npz"
            if not arr_p.exists():
                print(f"{year}: no {tag} arrays yet")
                continue
            rows = pd.read_csv(SCRATCH / f"rows_{tag}_SPP_{year}.csv")
            assert (rows.unit_id.to_numpy() == rows_pre.unit_id.to_numpy()).all(), "row identity moved"
            z = np.load(arr_p)
            arr = {k: z[k] for k in z.files}
            e = in_merit_energy(rows, arr, year)
            df = rows[["plant_code", "name", "pmax", "heat_rate", "fuel_mean"]].copy()
            df["klass"] = fl.klass
            df["flag"] = fl.flag
            df["e_model"] = e
            results[tag] = df
        if not results:
            continue
        print(f"\n================ SPP {year} ================")
        for grp, tag in CLASSES.items():
            cen = pd.read_csv(SPP46 / f"census_{year}_{tag}.csv").set_index("plant_code")
            table = []
            for arm, df in results.items():
                sub = df[df.klass == grp]
                pl = sub.groupby("plant_code").agg(name=("name", "first"), mw=("pmax", "sum"), flag=("flag", "first"),
                                                  e_model=("e_model", "sum"), hr=("heat_rate", "first"), fuel=("fuel_mean", "mean"))
                pl["e_campd"] = cen["gen_gwh"].reindex(pl.index).fillna(0.0)
                pl["delta"] = pl.e_model - pl.e_campd
                gs = pl.groupby("flag").agg(plants=("mw", "size"), mw=("mw", "sum"), e_model=("e_model", "sum"),
                                            e_campd=("e_campd", "sum"), delta=("delta", "sum")).round(1)
                gs.insert(0, "arm", arm)
                table.append(gs.reset_index())
                pl.to_csv(OUT / f"attribution_{arm}_{year}_{tag}.csv")
            t = pd.concat(table).pivot_table(index="flag", columns="arm", values=["plants", "mw", "e_model", "e_campd", "delta"], aggfunc="first")
            print(f"--- {grp} (GWh; model in-merit at keeper-3's P1 prices vs CAMPD)")
            print(t.round(1).to_string())
            for arm, df in results.items():
                sub = df[(df.klass == grp) & (df.plant_code.isin(NAMED))]
                if len(sub):
                    pl = sub.groupby("plant_code").agg(name=("name", "first"), mw=("pmax", "sum"), hr=("heat_rate", "first"),
                                                      fuel=("fuel_mean", "mean"), e_model=("e_model", "sum"))
                    pl["e_campd"] = cen["gen_gwh"].reindex(pl.index).fillna(0.0)
                    pl["delta"] = pl.e_model - pl.e_campd
                    print(f"  named plants, {arm}:\n{pl.round(2).to_string()}")


if __name__ == "__main__":
    main()
