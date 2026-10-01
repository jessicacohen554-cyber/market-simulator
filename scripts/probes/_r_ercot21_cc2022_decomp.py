"""R-ERCOT-21 phase 0 (zero LP): where the 2022 CC_REGULAR under-run lives.

Inputs: one keeper leg bundle (``dispatch/<Y>_P1.parquet``,
``hourly/unit_hourly_<Y>.parquet``, ``hourly/system_<Y>.parquet``,
``btm.parquet``) and the leg's benchmark frames rebuilt at zero LP with
``run_calibration_full.build_benchmark_frames`` (``eia923`` per plant-class
annual + monthly; ``campd`` per plant hourly net MW). Both sides pass through
``apply_other_fossil_scoring``, so the class totals are the scorer's C1 basis.

Reports, for the target class (CC_REGULAR) and the coal classes:

1. the C1 identity: model vs EIA-923 (gross, then net of the class BTM the
   bench subtracts) and the full class table, so the CC gap is placed against
   every other class's delta;
2. per plant: model TWh, available TWh (sum of hourly ``cap_mw``), EIA-923;
3. per month: model vs EIA-923 monthly;
4. per hour class (season x on/off-peak, and load quartile): model vs actual
   hourly (each plant's CEMS shape rescaled to its EIA-923 annual), plus the
   model's undispatched CC headroom split by whether the unit's offer was in
   merit (``mc <= own-zone price + 0.5``) — the test of whether the object is a
   CC availability/commitment one (in-merit headroom) or a merit-order one.

The bench's per-plant display rows (``bench.plants``) are NOT used: they omit
plants 7512 / 55501 / 55545 (10.0 TWh of 2022 CC_REGULAR) that ``classFull``
counts. Solves nothing.

Usage::

    PYTHONPATH=.:src:scripts uv run python scripts/probes/_r_ercot21_cc2022_decomp.py \
        --leg <leg dir> --e923 <eia923.parquet> --campd <campd.parquet> --year 2022 --out <json>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import render_calibration_html as R

T = 8760
COAL = ("COAL_PRB", "COAL_LIGNITE")


def _plant(u: pd.DataFrame) -> pd.Series:
    """Plant code of each unit row (split children keep their own code)."""
    pc = u.unit_id.astype(str).str.extract(r"_p(\d+)_")[0]
    return pc.fillna(u.plant_code.astype(str)).astype(int)


def main() -> None:
    """Print and dump the decomposition."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg", required=True)
    ap.add_argument("--e923", required=True)
    ap.add_argument("--campd", required=True)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--klass", default="CC_REGULAR")
    ap.add_argument("--out")
    a = ap.parse_args()
    y, K, leg = a.year, a.klass, Path(a.leg)
    G = (K, *COAL)
    out: dict = {"year": y, "klass": K, "leg": str(leg)}

    # --- 1. C1 identity on the scorer's basis
    d = R.apply_other_fossil_scoring(
        pd.read_parquet(leg / f"dispatch/{y}_P1.parquet", columns=["plant_code", "klass", "mw"]),
        y, plant_col="plant_code")
    e = pd.read_parquet(a.e923)
    e = R.apply_other_fossil_scoring(e[e.year == y], y, plant_col="plant_id")
    btm = pd.read_parquet(leg / "btm.parquet")
    btm = btm[(btm.year == y) & (btm["pass"] == "P1")].set_index("klass").btm_bench_twh
    m_cls = d.groupby("klass").mw.sum() / 1e6
    e_cls = e.groupby("klass").annual_mwh.sum() / 1e6 - btm.reindex(e.klass.unique()).fillna(0)
    cls = pd.DataFrame({"model": m_cls, "actual": e_cls}).fillna(0.0)
    cls["delta"] = cls.model - cls.actual
    out["class_table"] = cls.round(3).to_dict("index")
    out["class_btm_twh"] = btm.round(3).to_dict()
    print(cls.round(2).to_string())
    print(f"total: model {cls.model.sum():.2f} actual {cls.actual.sum():.2f} delta {cls.delta.sum():.2f}")

    # --- 2. per plant
    u = pd.read_parquet(leg / f"hourly/unit_hourly_{y}.parquet",
                        columns=["unit_id", "plant_code", "plant_group", "zone", "hour", "mw", "cap_mw", "mc"])
    u = u[u.plant_group.isin(G)].copy()
    u["plant"] = _plant(u)
    mp = d[d.klass.isin(G)].groupby(["klass", "plant_code"]).mw.sum() / 1e6
    av = u.groupby(["plant_group", "plant"]).cap_mw.sum() / 1e6
    ep = e[e.klass.isin(G)].groupby(["klass", "plant_id"]).annual_mwh.sum() / 1e6
    pl = pd.DataFrame({"model_twh": mp, "e923_twh": ep}).fillna(0.0)
    pl.index.names = ["klass", "plant"]
    pl["avail_twh"] = av.rename_axis(["klass", "plant"]).reindex(pl.index).fillna(0.0)
    pl["delta"] = pl.model_twh - pl.e923_twh
    pl = pl.reset_index().sort_values("delta")
    out["by_plant"] = pl.round(3).to_dict("records")
    for g in G:
        s = pl[pl.klass == g]
        print(f"\n{g}: n={len(s)} model {s.model_twh.sum():.2f} avail {s.avail_twh.sum():.2f} "
              f"e923(gross) {s.e923_twh.sum():.2f}; sum(neg) {s.delta[s.delta < 0].sum():.2f} "
              f"sum(pos) {s.delta[s.delta > 0].sum():.2f}")
        print(pd.concat([s.head(8), s.tail(4)]).round(2).to_string(index=False))

    # --- 3. per month
    hrs = pd.date_range(f"{y}-01-01", periods=T, freq="h")
    mon = hrs.month.to_numpy()
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    mrow = {}
    for g in G:
        hm = u[u.plant_group == g].groupby("hour").mw.sum().reindex(range(T), fill_value=0).to_numpy()
        mm = np.bincount(mon - 1, weights=hm, minlength=12) / 1e3
        em = e[e.klass == g][mcols].sum().to_numpy() / 1e3
        mrow[g] = {"model_gwh": mm.round(0).tolist(), "e923_gwh": em.round(0).tolist(),
                   "delta_gwh": (mm - em).round(0).tolist()}
    out["by_month"] = mrow
    print("\nBy month, model - EIA-923 (GWh, gross of BTM):")
    for g in G:
        print(f"  {g:13s}", [int(x) for x in mrow[g]["delta_gwh"]])

    # --- 4. per hour class
    c = pd.read_parquet(a.campd)
    c = c[c.year == y]
    cm = c.pivot_table(index="hour", columns="plant_id", values="net_mw", aggfunc="sum").reindex(range(T)).fillna(0.0)

    def act_hourly(g: str) -> np.ndarray:
        """Actual class MW by hour: each plant's CEMS shape scaled to its EIA-923 annual."""
        acc = np.zeros(T)
        for pid, mwh in (e[e.klass == g].groupby("plant_id").annual_mwh.sum()).items():
            if pid in cm.columns and cm[pid].sum() > 0:
                acc += cm[pid].to_numpy() * (mwh / cm[pid].sum())
            else:
                acc += mwh / T
        return acc

    sysd = pd.read_parquet(leg / f"hourly/system_{y}.parquet", columns=["zone", "hour", "price", "demand"])
    pz = sysd.set_index(["hour", "zone"]).price
    dz = sysd.pivot(index="hour", columns="zone", values="demand")
    sysp = ((sysd.pivot(index="hour", columns="zone", values="price") * dz).sum(axis=1) / dz.sum(axis=1)).reindex(range(T)).to_numpy()
    load = dz.sum(axis=1).reindex(range(T)).to_numpy()
    cc = u[u.plant_group == K].copy()
    cc["price"] = pz.reindex(pd.MultiIndex.from_arrays([cc.hour, cc.zone])).to_numpy()
    head = (cc.cap_mw - cc.mw).clip(lower=0)
    inm = cc.mc <= cc.price + 0.5
    h_in = head.where(inm, 0).groupby(cc.hour).sum().reindex(range(T), fill_value=0).to_numpy()
    h_out = head.where(~inm, 0).groupby(cc.hour).sum().reindex(range(T), fill_value=0).to_numpy()
    m_cc = cc.groupby("hour").mw.sum().reindex(range(T), fill_value=0).to_numpy()
    m_coal = u[u.plant_group.isin(COAL)].groupby("hour").mw.sum().reindex(range(T), fill_value=0).to_numpy()
    hod = hrs.hour.to_numpy()
    df = pd.DataFrame({
        "season": np.where(np.isin(mon, (6, 7, 8, 9)), "summer", np.where(np.isin(mon, (12, 1, 2)), "winter", "shoulder")),
        "tod": np.where((hod >= 7) & (hod <= 22), "on", "off"),
        "loadq": pd.qcut(load, 4, labels=["L1 low", "L2", "L3", "L4 high"]).astype(str),
        "m_cc": m_cc, "a_cc": act_hourly(K), "m_coal": m_coal, "a_coal": sum(act_hourly(g) for g in COAL),
        "h_in": h_in, "h_out": h_out, "p": sysp})
    tabs = {}
    for key in (["season", "tod"], ["loadq"]):
        g = df.groupby(key).agg(hours=("m_cc", "size"), cc_model=("m_cc", "sum"), cc_act=("a_cc", "sum"),
                                coal_model=("m_coal", "sum"), coal_act=("a_coal", "sum"),
                                cc_head_inmerit=("h_in", "sum"), cc_head_outmerit=("h_out", "sum"),
                                model_price=("p", "mean"))
        for col in ("cc_model", "cc_act", "coal_model", "coal_act", "cc_head_inmerit", "cc_head_outmerit"):
            g[col] = g[col] / 1e6
        g["cc_delta"] = g.cc_model - g.cc_act
        g["coal_delta"] = g.coal_model - g.coal_act
        print("\n", g[["hours", "cc_model", "cc_act", "cc_delta", "coal_delta", "cc_head_inmerit",
                       "cc_head_outmerit", "model_price"]].round(2).to_string())
        tabs["_".join(key)] = g.round(3).reset_index().to_dict("records")
    out["by_hour_class"] = tabs
    out["notes"] = ("per-plant / monthly / hourly actuals are EIA-923 GROSS of BTM (the bench subtracts the "
                    "class BTM in class_btm_twh); hourly actual = per-plant CEMS shape rescaled to its EIA-923 "
                    "annual (flat where no CEMS); headroom = cap_mw - mw per CC unit-hour; in-merit = "
                    "mc <= own-zone price + 0.5")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
