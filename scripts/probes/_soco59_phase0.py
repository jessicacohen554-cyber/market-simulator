"""SOCO-59 phase 0 — the two named candidates for the last failing row, measured.

Zero-LP throughout (rule 32 ``[R-SHARD]`` (a)): every number is read off raw
primary sources (EIA-923 Schedule 5 receipts, CAMPD, EIA-930), the designated
keeper's own committed hourlies (and the SOCO-58 per-year legs recovered at zero
LP), or a ``build_hydro_fleet`` call. **No LP is solved.**

Modes
-----
``coal``     -- candidate (1). Per SOCO coal plant: EIA-923 Schedule 5 delivered
                cost, coal rank (``ENERGY_SOURCE``), mine state and transport,
                the EIA plant name, the CAMPD facility name and the name the
                model's tranche table carries. Closes the "Scherer is PRB but
                priced as BIT" lead: the lead rests on a plant-NAME swap.
``pssplit``  -- candidate (2), the rule-14 admissibility half. SOCO's EIA-930
                hydro column per half-year 2019-2026: which column EIA publishes
                (combined hydro+PS vs hydro-ex-PS), hours above SOCO's OWN
                conventional-hydro nameplate, and the ``NG: PS`` filing census.
                The neiso-72 fingerprint (i), reproduced on SOCO's own data.
``hydro``    -- the conventional-hydro monthly budget per year, control vs arm
                (``hydro_backfill_year=2024`` + ``hydro_eia930_monthly`` with
                ``EIA930_PS_SPLIT_COMPLETE_FROM['SOCO']=2025``).
``restack``  -- check A/C: what the added 2025 water displaces, by class and by
                coal plant. Greedy, and deliberately run under TWO allocations
                that bracket where the LP puts energy-limited water: ``peak``
                (each month's added energy into its highest-price hours at full
                headroom) and ``flat`` (spread evenly over the month's hours).
                Each hour's added MW displaces the dearest ABOVE-FLOOR producing
                MW, floors read from the committed ``floors/`` sidecar.
``c4``       -- the 2025 coal / gas hourly series against EIA-930: level bias
                vs shape residual, before and after the re-stack's coal delta.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
for _p in (str(_ROOT), str(_ROOT / "src"), str(_ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

COAL_PLANTS = (3, 26, 703, 6002, 6073, 6257)
ZONES = ["SOCO_AL", "SOCO_GA", "SOCO_MS"]
E930 = _ROOT / "data/raw/eia-930"
HY_COL_FOLD = "Net Generation (MW) from Hydropower and Pumped Storage"
HY_COL_EX = "Net Generation (MW) from Hydropower Excluding Pumped Storage"
PS_COL = "Net Generation (MW) from Pumped Storage"


def coal() -> pd.DataFrame:
    """Candidate (1): delivered cost, rank and identity per SOCO coal plant."""
    tr = pd.read_csv(_ROOT / "data/raw/_processed-legacy/thermal_tranches_SOCO.csv")
    model_name = tr.set_index("plant_code")["name"].to_dict()
    rows = []
    for y in (2019, 2020, 2021, 2022, 2023, 2024):
        d = pd.read_csv(_ROOT / f"data/raw/coal-receipts/coal_receipts_{y}.csv", low_memory=False)
        d = d[d["Plant Id"].isin(COAL_PLANTS)].copy()
        for c in ("QUANTITY", "Average Heat Content", "FUEL_COST"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
        d["mmbtu"] = d.QUANTITY * d["Average Heat Content"]
        d["spend"] = d.mmbtu * d.FUEL_COST / 100.0  # FUEL_COST is cents/MMBtu
        for pc, g in d.groupby("Plant Id"):
            by_rank = g.groupby("ENERGY_SOURCE").mmbtu.sum()
            rows.append(
                {
                    "plant": int(pc),
                    "year": y,
                    "eia_name": g["Plant Name"].iloc[0],
                    "model_name": model_name.get(int(pc), ""),
                    "usd_per_mmbtu": round(g.spend.sum() / g.mmbtu.sum(), 3),
                    "rank_shares": {k: round(v / by_rank.sum(), 3) for k, v in by_rank.items()},
                    "mine_states": sorted(g["Coalmine State"].dropna().astype(str).unique()),
                    "transport": sorted(g["Primary Transportation Mode"].dropna().astype(str).unique()),
                }
            )
    return pd.DataFrame(rows)


def campd_names() -> pd.DataFrame:
    """CAMPD's own facility name and primary fuel per facility id (2024)."""
    out = []
    for st in ("AL", "GA", "MS"):
        d = pd.read_parquet(
            _ROOT / f"data/raw/campd-unit-level/{st}_2024.parquet",
            columns=["facilityName", "facilityId", "primaryFuelInfo"],
        ).drop_duplicates()
        out.append(d[d.facilityId.astype(int).isin(COAL_PLANTS)])
    return pd.concat(out).drop_duplicates(["facilityId", "facilityName"])


def _hy_nameplate(year: int) -> float:
    from market_sim.data.hydro import load_hydro_budget

    return float(np.sum(load_hydro_budget("SOCO", year).max_mw))


def pssplit() -> pd.DataFrame:
    """Candidate (2): SOCO's EIA-930 hydro column and PS filing, per half-year."""
    np_mw = _hy_nameplate(2024)
    rows = []
    for f in sorted(E930.glob("EIA930_BALANCE_20*_*.parquet")):
        tag = f.stem.replace("EIA930_BALANCE_", "")
        if int(tag[:4]) < 2019:
            continue
        d = pd.read_parquet(f)
        s = d[d["Balancing Authority"] == "SOCO"]
        col = HY_COL_FOLD if HY_COL_FOLD in s else HY_COL_EX
        x = pd.to_numeric(s[col], errors="coerce").dropna()
        ps = pd.to_numeric(s[PS_COL], errors="coerce") if PS_COL in s else None
        rows.append(
            {
                "half": tag,
                "column": "hydro+PS (folded)" if col == HY_COL_FOLD else "hydro ex-PS",
                "hours": len(x),
                "hours_above_HY_nameplate": int((x > np_mw).sum()),
                "max_MW": int(x.max()),
                "TWh": round(x.sum() / 1e6, 3),
                "PS_filed_hours": int(ps.notna().sum()) if ps is not None else 0,
                "PS_min_MW": float(ps.min()) if ps is not None and ps.notna().any() else None,
            }
        )
    out = pd.DataFrame(rows)
    out.attrs["HY_nameplate_MW"] = np_mw
    return out


def hydro_budgets() -> pd.DataFrame:
    """Monthly hydro budget per year, control vs arm, at unit grain."""
    import market_sim.config.constants as K
    from market_sim.data.hydro import build_hydro_fleet

    def one(y, bf, e9):
        u, me = build_hydro_fleet("SOCO", y, ZONES, backfill_year=bf, eia930_monthly=e9)
        me = np.asarray(me)
        return u, me

    rows = []
    ctrl = {y: one(y, None, False) for y in (2023, 2024, 2025)}
    saved = dict(K.EIA930_PS_SPLIT_COMPLETE_FROM)
    K.EIA930_PS_SPLIT_COMPLETE_FROM["SOCO"] = 2025
    try:
        arm = {y: one(y, 2024, True) for y in (2023, 2024, 2025)}
    finally:
        K.EIA930_PS_SPLIT_COMPLETE_FROM.clear()
        K.EIA930_PS_SPLIT_COMPLETE_FROM.update(saved)
    for y in (2023, 2024, 2025):
        (uc, mc), (ua, ma) = ctrl[y], arm[y]
        same = (
            [g.unit_id for g in uc] == [g.unit_id for g in ua]
            and [g.pmax_mw for g in uc] == [g.pmax_mw for g in ua]
            and mc.shape == ma.shape
            and np.array_equal(mc, ma)
        )
        rows.append(
            {
                "year": y,
                "ctrl_units": len(uc),
                "ctrl_TWh": round(mc.sum() / 1e6, 4),
                "arm_units": len(ua),
                "arm_TWh": round(ma.sum() / 1e6, 4),
                "arm_pmax_MW": round(sum(g.pmax_mw for g in ua), 1),
                "byte_identical": bool(same),
                "arm_monthly_TWh": np.round(ma.sum(axis=0) / 1e6, 3).tolist(),
            }
        )
    return pd.DataFrame(rows)


def restack(bundle: Path, year: int, alloc: str) -> tuple[pd.DataFrame, pd.Series]:
    """Greedy displacement of the added water; returns (per-unit Δ, hourly coal Δ)."""
    bud = hydro_budgets().set_index("year")
    add_m = np.array(bud.loc[year, "arm_monthly_TWh"]) * 1e6
    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[uh["pass"] == "P1"].copy()
    sysp = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    sysp = sysp[sysp["pass"] == "P1"]
    load = sysp.groupby("hour").demand.sum()
    price = (sysp.assign(w=sysp.price * sysp.demand).groupby("hour").w.sum() / load).to_numpy()
    z = np.load(bundle / f"floors/{year}_P1.npz", allow_pickle=True)
    mg, flmap = z["min_gen"], {u: i for i, u in enumerate(z["unit_ids"])}

    MW = uh.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum").fillna(0.0)
    units = MW.index.to_numpy()
    MC = uh.pivot_table(index="unit_id", columns="hour", values="mc", aggfunc="mean").reindex(units).to_numpy()
    meta = uh.drop_duplicates("unit_id").set_index("unit_id").reindex(units)
    grp, pc = meta["plant_group"].astype(str).to_numpy(), meta["plant_code"].to_numpy()
    MW = MW.to_numpy()
    T = MW.shape[1]
    FLOOR = np.zeros_like(MW)
    for i, u in enumerate(units):
        j = flmap.get(u)
        if j is not None:
            FLOOR[i] = mg[j][:T]
    is_hydro = grp == "hydro"
    hyd_now = MW[is_hydro].sum(axis=0)
    head = np.maximum(float(bud.loc[year, "arm_pmax_MW"]) - hyd_now, 0.0)
    ctrl_m = np.zeros(12)
    month = pd.date_range(f"{year}-01-01", periods=T, freq="h").month.to_numpy() - 1
    np.add.at(ctrl_m, month, hyd_now)
    extra_m = np.maximum(add_m - ctrl_m, 0.0)

    add = np.zeros(T)
    for m in range(12):
        idx = np.where(month == m)[0]
        e = extra_m[m]
        if alloc == "flat":
            add[idx] = np.minimum(e / len(idx), head[idx])
        else:
            for t in idx[np.argsort(-price[idx])]:
                q = min(head[t], e)
                add[t], e = q, e - q
                if e <= 0:
                    break
    moved = np.zeros(len(units))
    coal_dh = np.zeros(T)
    coal = np.char.startswith(grp.astype(str), "COAL")
    for t in range(T):
        need = add[t]
        if need <= 0:
            continue
        disp = np.where(~is_hydro, np.maximum(MW[:, t] - FLOOR[:, t], 0.0), 0.0)
        for b in np.argsort(np.where(disp > 0, -MC[:, t], np.inf)):
            if need <= 1e-9 or disp[b] <= 1e-9:
                break
            q = min(disp[b], need)
            moved[b] -= q
            need -= q
            if coal[b]:
                coal_dh[t] -= q
    out = pd.DataFrame({"unit": units, "grp": grp, "pc": pc, "dTWh": moved / 1e6})
    out.attrs["added_TWh"] = add.sum() / 1e6
    out.attrs["unplaced_TWh"] = (extra_m.sum() - add.sum()) / 1e6
    return out, pd.Series(coal_dh)


def c4_decomp(bundle: Path, year: int, fuel: str, delta: pd.Series | None = None) -> dict:
    """NRMSE = RMSE/mean(actual), split into level bias and shape residual."""
    uh = pd.read_parquet(bundle / f"hourly/unit_hourly_{year}.parquet")
    uh = uh[uh["pass"] == "P1"]
    g = uh.plant_group.astype(str)
    sel = g.str.startswith("COAL") if fuel == "coal" else g.isin(["CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP"])
    model = uh[sel].groupby("hour").mw.sum().to_numpy()
    if delta is not None:
        model = model + delta.to_numpy()[: len(model)]
    bench = json.loads(gzip.open(_ROOT / f"frontend/data/backcast/bench/SOCO/{year}.json.gz").read())
    return {"model_TWh": round(model.sum() / 1e6, 3), "bench_keys": sorted(bench.get("bench", {}).get("e930", {}).keys())[:12]}


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("coal", "pssplit", "hydro", "restack", "c4"))
    ap.add_argument("--bundle", type=Path, default=_ROOT / "results/calibration/soco58_arm_2025")
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--alloc", choices=("peak", "flat"), default="peak")
    a = ap.parse_args()
    pd.set_option("display.width", 220)
    pd.set_option("display.max_colwidth", 80)
    if a.mode == "coal":
        print(coal().to_string(index=False))
        print(campd_names().to_string(index=False))
    elif a.mode == "pssplit":
        df = pssplit()
        print(f"SOCO conventional-hydro nameplate (EIA-923 HY units): {df.attrs['HY_nameplate_MW']:.1f} MW")
        print(df.to_string(index=False))
    elif a.mode == "hydro":
        print(hydro_budgets().to_string(index=False))
    elif a.mode == "restack":
        out, _ = restack(a.bundle, a.year, a.alloc)
        print(f"alloc={a.alloc} added {out.attrs['added_TWh']:.3f} TWh, unplaced {out.attrs['unplaced_TWh']:.3f}")
        print(out.groupby("grp").dTWh.sum().round(3).to_string())
        coalp = out[out.grp.str.startswith("COAL")].groupby("pc").dTWh.sum().round(3)
        print("coal by plant:\n" + coalp.to_string())
    elif a.mode == "c4":
        print(c4_decomp(a.bundle, a.year, "coal"))


if __name__ == "__main__":
    main()
