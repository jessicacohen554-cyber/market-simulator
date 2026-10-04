"""Close-out CAISO w4, step 0 (ZERO LP): the closeout-caiso-2 CC_REGULAR decomposition re-run on the w3 probe bundle.

Reads only committed / hash-verified artifacts:

* the keeper bundle ``results/calibration/closeout_caiso_w1_a2_span`` (P1
  ``unit_marginal_<y>``, ``class_hourly_<y>``, ``system_<y>``, ``storage_<y>``);
* its shared benchmark frames (``results/calibration/_shared/CAISO/eia923-*``,
  ``campd-*``, ``eia930-*``; restore with
  ``run_calibration_full.py --restore-shared-inputs <bundle>``, hash-verified);
* the committed bench parts ``frontend/data/backcast/bench/CAISO/<y>.json.gz``
  (``classFull``, the scored actual, and the per-plant ``e_mon``);
* EIA-930 CISO hourly demand (``data/raw/eia-930-hourly/CISO hourly.parquet``).

Buckets (charter step 1):

* **bench** — the scored actual (``classFull``) against the plant-level EIA-923
  grid record: ``reconcile_vintage_classes`` scales every fossil class to the
  EIA-930 gas cell net of the geothermal+biomass fold-in deflation. Reported
  with the SOCO-60 fold test (``benchmark_semantics.EIA930_GAS_FOLD_REFUTED``:
  a fold of F TWh makes 930 gas exceed the 923 gas classes by ~F).
* **(a)** availability above demonstrated capability: per plant, model MW above
  the plant's CEMS net hourly p99.9 (EIA-923-levelled), by season (a1, the
  capability reading) and by month (a2, an upper bound that also counts
  outages/derates and economic part-load months).
* **(b)/(d)** the CISO energy balance, model minus actual by component, on all
  hours and on the CC over-run hours (model CC_REGULAR above its EIA-923-levelled
  CEMS hourly): demand (EIA-930 Demand), net imports (EIA-930 interchange),
  hydro (EIA-930 shape, EIA-923 monthly level), other gas classes (CEMS shape,
  EIA-923 level), nuclear / solar / wind (EIA-930), geothermal+biomass (EIA-923
  monthly, flat), storage (model; no measured CISO series 2019-21).
* **(c)** the RA must-offer bridge: D-2 forced CC_REGULAR TWh from the bundle's
  ``legitimacy_diagnostics.json`` (an upper bound on what removing it could do).

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_2_cc_object.py [--out PATH]
"""

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results/calibration/closeout_caiso_w3_a1_span"
SHARED = ROOT / "results/calibration/_shared/CAISO"
BENCH = ROOT / "frontend/data/backcast/bench/CAISO"
E930_HOURLY = ROOT / "data/raw/eia-930-hourly/CISO hourly.parquet"
YEARS = (2020,)
T = 8760
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
SUMMER = (MONTH >= 6) & (MONTH <= 9)
GAS_OTHER = ("CC_CHP", "CT_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP", "OTHER_FOSSIL")
CC = "CC_REGULAR"
P_CEIL = 99.9


def _shared(prefix: str) -> pd.DataFrame:
    meta = json.loads((BUNDLE / "meta.json").read_text())
    return pd.read_parquet(BUNDLE / meta["shared_inputs"][prefix])


def _bench(year: int) -> dict:
    return json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]


def _dense(df: pd.DataFrame, col: str) -> np.ndarray:
    return df.set_index("hour")[col].reindex(range(T)).fillna(0.0).to_numpy(float)


def _demand_930(year: int) -> np.ndarray:
    """EIA-930 CISO Demand on the model clock (Pacific standard time, hour-ending -> start)."""
    d = pd.read_parquet(E930_HOURLY, columns=["UTC time", "Demand"])
    pst = pd.to_datetime(d["UTC time"]) - pd.Timedelta(
        hours=9
    )  # hour-ending UTC -> PST start
    keep = (pst.dt.year == year) & ~((pst.dt.month == 2) & (pst.dt.day == 29))
    pst, val = pst[keep], d.loc[keep, "Demand"].to_numpy(float)
    start = np.cumsum([0, *_DAYS[:-1]]) * 24
    hour = (
        start[pst.dt.month.to_numpy() - 1]
        + (pst.dt.day.to_numpy() - 1) * 24
        + pst.dt.hour.to_numpy()
    )
    out = np.full(T, np.nan)
    out[hour] = val
    return pd.Series(out).interpolate(limit_direction="both").to_numpy()


def _levelled(campd: np.ndarray, e_mon_mwh: np.ndarray) -> np.ndarray:
    """CEMS hourly shape levelled to the EIA-923 monthly record (flat where CEMS is empty)."""
    out = np.zeros(T)
    for m in range(1, 13):
        k = MONTH == m
        c = campd[k]
        if c.sum() > 0:
            out[k] = c * (e_mon_mwh[m - 1] / c.sum())
        else:
            out[k] = e_mon_mwh[m - 1] / k.sum()
    return out


def census_year(
    year: int, e923: pd.DataFrame, campd: pd.DataFrame, e930: pd.DataFrame, diag: dict
) -> dict:
    """Return the bucket census for one year."""
    b = _bench(year)
    cf = b["classFull"]
    um = pd.read_parquet(
        BUNDLE / f"hourly/unit_marginal_{year}.parquet",
        columns=["plant_code", "plant_group", "fuel", "zone", "hour", "mw", "cap_mw"],
    )
    um["plant_group"] = um["plant_group"].astype(str)
    group_of = um.groupby("plant_code").plant_group.agg(lambda s: s.mode().iat[0])
    ey = e923[e923.year == year]
    mcols = [f"m{i:02d}" for i in range(1, 13)]
    cy = campd[campd.year == year]
    cmap = {int(p): _dense(g, "net_mw") for p, g in cy.groupby("plant_id")}

    # ---- bench basis ------------------------------------------------------
    cls923 = ey.groupby("klass").annual_mwh.sum() / 1e6
    cc923 = float(cls923.get(CC, 0.0))
    w = e930[e930.year == year].groupby("series").mw.sum() / 1e6
    fold_f = float(
        cls923.get("OTHER", 0) + cls923.get("biomass", 0) - w.get("other", 0)
    )
    gas_fam_scored = sum(float(cf.get(k, 0)) for k in (CC, *GAS_OTHER))
    scale = float(cf[CC]) / cc923 if cc923 else float("nan")
    gas_fam_grid = gas_fam_scored / scale
    bench = {
        "cc_classfull_twh": round(float(cf[CC]), 3),
        "cc_eia923_plant_twh": round(cc923, 3),
        "reconcile_scale": round(scale, 4),
        "bench_component_twh": round(cc923 - float(cf[CC]), 3),
        "gas_family_scored_twh": round(gas_fam_scored, 2),
        "gas_family_923_grid_twh": round(gas_fam_grid, 2),
        "gas_family_923_full_twh": round(
            float(cls923.reindex([CC, *GAS_OTHER]).fillna(0).sum()), 2
        ),
        "e930_gas_twh": round(float(w["gas"]), 2),
        "cems_anchor_fossil_grid_twh": b["e930"].get("fossil_cems_grid"),
        "fold_deflation_F_twh": round(fold_f, 2),
        "e930_gas_minus_923_grid_twh": round(float(w["gas"]) - gas_fam_grid, 2),
    }

    # ---- model vs EIA-923 by plant-month (CC_REGULAR) ---------------------
    mcc = um[um.plant_group == CC]
    cc_codes = sorted(
        set(mcc.plant_code.unique()) | set(ey[ey.klass == CC].plant_id.astype(int))
    )
    model_h = {
        int(p): _dense(g.groupby("hour", as_index=False).mw.sum(), "mw")
        for p, g in mcc.groupby("plant_code")
    }
    e_cc = ey[ey.klass == CC].groupby("plant_id")[mcols].sum()
    rows = []
    act_cc = np.zeros(T)
    mod_cc = np.zeros(T)
    a1 = a2 = 0.0
    for p in cc_codes:
        m = model_h.get(p, np.zeros(T))
        e_mon = e_cc.loc[p].to_numpy(float) if p in e_cc.index else np.zeros(12)
        act = _levelled(cmap.get(p, np.zeros(T)), e_mon)
        act_cc += act
        mod_cc += m
        # (a1) seasonal capability ceiling, (a2) monthly demonstrated ceiling
        for mask in (SUMMER, ~SUMMER):
            ceil = np.percentile(act[mask], P_CEIL) if act[mask].any() else 0.0
            a1 += np.clip(m[mask] - ceil, 0, None).sum()
        for mo in range(1, 13):
            k = MONTH == mo
            ceil = np.percentile(act[k], P_CEIL) if act[k].any() else 0.0
            a2 += np.clip(m[k] - ceil, 0, None).sum()
        for mo in range(1, 13):
            k = MONTH == mo
            rows.append((p, mo, m[k].sum() / 1e3, e_mon[mo - 1] / 1e3))
    pm = pd.DataFrame(rows, columns=["plant", "month", "model_gwh", "e923_gwh"])
    pm["d"] = pm.model_gwh - pm.e923_gwh
    pm["group_in_model"] = pm.plant.map(group_of).fillna("absent")
    by_month = pm.groupby("month")[["model_gwh", "e923_gwh", "d"]].sum() / 1e3
    by_plant = pm.groupby("plant")[["model_gwh", "e923_gwh", "d"]].sum() / 1e3
    top = by_plant.sort_values("d", ascending=False)
    pos = float(pm.d.clip(lower=0).sum() / 1e3)
    neg = float(pm.d.clip(upper=0).sum() / 1e3)

    # ---- CISO energy balance: model minus actual by component -------------
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    chm = {str(k): _dense(g, "mw") for k, g in ch.groupby("klass", observed=True)}
    sysh = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    dem_m = sysh.groupby("hour").demand.sum().reindex(range(T)).to_numpy(float)
    st = pd.read_parquet(BUNDLE / f"hourly/storage_{year}.parquet")
    sto_m = (
        (st.groupby("hour").discharge_mw.sum() - st.groupby("hour").charge_mw.sum())
        .reindex(range(T))
        .fillna(0)
        .to_numpy()
    )
    e930y = e930[e930.year == year]
    ws = {s: _dense(g, "mw") for s, g in e930y.groupby("series")}
    dem_a = _demand_930(year)

    def act_class(klass: str) -> np.ndarray:
        """EIA-923 (plant rows of ``klass``) levelled onto each plant's CEMS shape."""
        e = ey[ey.klass == klass].groupby("plant_id")[mcols].sum()
        out = np.zeros(T)
        for p, r in e.iterrows():
            out += _levelled(cmap.get(int(p), np.zeros(T)), r.to_numpy(float))
        return out

    def act_flat(klasses) -> np.ndarray:
        mon = ey[ey.klass.isin(klasses)][mcols].sum().to_numpy(float)
        return mon[MONTH - 1] / _DAYS[MONTH - 1] / 24

    hydro_mon = ey[ey.klass == "hydro"][mcols].sum().to_numpy(float)
    wh = ws["hydro"]
    hydro_a = np.zeros(T)
    for mo in range(1, 13):
        k = MONTH == mo
        hydro_a[k] = (
            wh[k] * (hydro_mon[mo - 1] / wh[k].sum())
            if wh[k].sum() > 0
            else hydro_mon[mo - 1] / k.sum()
        )
    btm = {k: float(cls923.get(k, 0)) - float(cf.get(k, 0)) / scale for k in GAS_OTHER}
    comps = {
        "CC_REGULAR": (mod_cc, act_cc),
        "net_imports": (chm.get("import", np.zeros(T)), -ws["interchange"]),
        "hydro": (chm.get("hydro", np.zeros(T)), hydro_a),
        "nuclear": (chm.get("nuclear", np.zeros(T)), ws["nuclear"]),
        "solar": (chm.get("solar", np.zeros(T)), ws["solar"]),
        "wind": (chm.get("wind", np.zeros(T)), ws["wind"]),
        "geo_biomass": (
            chm.get("OTHER", np.zeros(T)) + chm.get("biomass", np.zeros(T)),
            act_flat(("OTHER", "biomass")),
        ),
        "storage_net": (sto_m, np.zeros(T)),
        "coal_oil": (
            chm.get("COAL_BIT", np.zeros(T)) + chm.get("oil", np.zeros(T)),
            act_flat(("COAL_BIT", "oil")),
        ),
    }
    for k in GAS_OTHER:
        a = act_class(k)
        # grid basis: remove the bench's BTM host share proportionally
        full = a.sum()
        if full > 0:
            a = a * max(0.0, (full / 1e6 - btm[k]) / (full / 1e6))
        comps[k] = (chm.get(k, np.zeros(T)), a)
    over = (mod_cc - act_cc) > 0
    bal = {}
    for k, (m, a) in comps.items():
        bal[k] = {
            "model_twh": round(m.sum() / 1e6, 3),
            "actual_twh": round(a.sum() / 1e6, 3),
            "delta_twh": round((m - a).sum() / 1e6, 3),
            "delta_overrun_h_twh": round((m - a)[over].sum() / 1e6, 3),
        }
    sup_m = sum(m for m, _ in comps.values())
    sup_a = sum(a for _, a in comps.values())
    bal["demand"] = {
        "model_twh": round(dem_m.sum() / 1e6, 3),
        "actual_twh": round(dem_a.sum() / 1e6, 3),
        "delta_twh": round((dem_m - dem_a).sum() / 1e6, 3),
        "delta_overrun_h_twh": round((dem_m - dem_a)[over].sum() / 1e6, 3),
    }
    bal["_model_supply_minus_demand_twh"] = round((sup_m - dem_m).sum() / 1e6, 3)
    bal["_actual_supply_minus_930demand_twh"] = round((sup_a - dem_a).sum() / 1e6, 3)
    bal["_actual_supply_minus_930demand_overrun_h_twh"] = round(
        (sup_a - dem_a)[over].sum() / 1e6, 3
    )
    bal["_overrun_hours"] = int(over.sum())

    d2 = [
        r
        for r in diag["diagnostics"]["D2"]["summary"]
        if r["year"] == year and r["class"] == CC
    ]
    hourly_r = float(np.corrcoef(mod_cc, act_cc)[0, 1])
    return {
        "scored_miss_twh": round(mod_cc.sum() / 1e6 - float(cf[CC]), 3),
        "model_cc_twh": round(mod_cc.sum() / 1e6, 3),
        "raw923_miss_twh": round(mod_cc.sum() / 1e6 - cc923, 3),
        "bench": bench,
        "plant_month": {
            "positive_sum_twh": round(pos, 2),
            "negative_sum_twh": round(neg, 2),
            "by_month_delta_twh": {int(k): round(v, 2) for k, v in by_month.d.items()},
            "top10_plants": [
                {
                    "plant": int(p),
                    "model_twh": round(r.model_gwh, 2),
                    "e923_twh": round(r.e923_gwh, 2),
                    "d_twh": round(r.d, 2),
                }
                for p, r in top.head(10).iterrows()
            ],
            "bottom5_plants": [
                {
                    "plant": int(p),
                    "model_twh": round(r.model_gwh, 2),
                    "e923_twh": round(r.e923_gwh, 2),
                    "d_twh": round(r.d, 2),
                }
                for p, r in top.tail(5).iterrows()
            ],
            "plants_absent_from_model_e923_twh": round(
                float(pm[pm.group_in_model == "absent"].e923_gwh.sum() / 1e3), 3
            ),
        },
        "a1_above_seasonal_capability_twh": round(a1 / 1e6, 3),
        "a2_above_monthly_demonstrated_twh": round(a2 / 1e6, 3),
        "balance": bal,
        "c_bridge_forced_twh": d2[0]["forced_twh"] if d2 else None,
        "cc_hourly_r_vs_levelled_cems": round(hourly_r, 3),
    }


def main() -> None:
    """Run the census for every year and print / write the JSON."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    e923 = _shared("eia923")
    campd = _shared("campd")
    e930 = _shared("eia930")
    diag = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    out = {str(y): census_year(y, e923, campd, e930, diag) for y in YEARS}
    text = json.dumps(out, indent=1, default=float)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
