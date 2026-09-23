"""SPP-74 (the body): where does the rung's ordinary-hour / whole-month price error live?

Zero-LP measurement, pre-registered in
``docs/handoffs/PRECOMMIT-spp-74-price-body-2026-09-23.md`` (pushed at ``84833817`` before
any number below was read). Part A — committed hourly sidecars and measured series only:

* the scorer's month error ``e_m`` split exactly into a basis term and per-hour-type terms
  (PRECOMMIT §1), and the §2 ownership counterfactual (DIAGNOSTIC, never an input);
* (a) the low side: measured RT hours < 0 / < -26 vs model hours <= 0 / at the -26 clamp;
* (c, published half) EIA N3045 KS / OK monthly delivered-to-electric-power gas;
* (d) the CT overrun, model CT_PEAKER vs CAMPD SWPP-BA CT gross, per month;
* context: model vs EIA-930 monthly coal / gas / wind energy.

Part B (per-year reconstruction, (b) and the model gas series) is
``_spp74_marginal_fuel.py``.

Usage: ``uv run python scripts/probes/_spp74_body_decomposition.py --out <json>``
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR, REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.calibration_verdict import _nrmse  # noqa: E402
from scripts.probes._spp72_demand_tightness import (  # noqa: E402
    CST_OFFSET_H,
    N_TOP,
    model_clock_index,
)
from scripts.probes._spp73_commitment_reach import (  # noqa: E402
    campd_state,
    swpp_gas_units,
)

YEARS = (2019, 2020, 2021, 2022)
RUNG = "hydro5_spp_floor_rung"  # the CURRENT rung (PRECOMMIT §0)
C3B_BAND, C3A_BAND = 0.20, 10.0
CLAMP = -25.99  # model hours at/below this are at the -26.000 wind PTC floor
MCF_TO_MMBTU = (
    1.036  # EIA published average heat content of delivered gas (PRECOMMIT §3c)
)
# trap (f): physical ceilings on EIA-930 SWPP fuel-type series
CEIL = {"WND": 40_000.0, "SUN": 20_000.0, "COL": 40_000.0, "NG": 40_000.0}
TYPES = ("NEG", "LOW", "MID1", "MID2", "HIGH", "TOP")


def model_price_demand(y: int) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted P1 price across zones and total demand, per model hour."""
    s = pd.read_parquet(
        REPO_ROOT / "results/calibration" / RUNG / f"hourly/system_{y}.parquet"
    )
    s = s[s["pass"] == "P1"]
    d = s.pivot(index="hour", columns="zone", values="demand").sort_index()
    p = s.pivot(index="hour", columns="zone", values="price").sort_index()
    tot = d.sum(axis=1).to_numpy()
    return (p * d).sum(axis=1).to_numpy() / tot, tot


def model_class_mw(y: int) -> pd.DataFrame:
    """P1 MW per class per model hour (hour x klass)."""
    c = pd.read_parquet(
        REPO_ROOT / "results/calibration" / RUNG / f"hourly/class_hourly_{y}.parquet"
    )
    c = c[c["pass"] == "P1"]
    c["klass"] = c["klass"].astype(str)
    return (
        c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(8760), fill_value=0.0)
        .fillna(0.0)
    )


def fueltype(ft: pd.DataFrame, code: str, y: int) -> np.ndarray:
    """EIA-930 SWPP fuel-type MW on the model clock, trap-(f) guarded."""
    s = ft[ft["fueltype"] == code].set_index("period")["value_mwh"]
    s.index = s.index - pd.Timedelta(hours=1)
    s = s[~s.index.duplicated()]
    out = s.reindex(model_clock_index(y)).astype(float)
    out[(out > CEIL.get(code, 40_000.0)) | (out < 0)] = np.nan
    return out.interpolate(limit_direction="both").fillna(0.0).to_numpy()


def hour_types(a: np.ndarray) -> np.ndarray:
    """PRECOMMIT §1 hour-type label per hour, by measured RT."""
    lab = np.full(8760, "", dtype=object)
    ok = np.isfinite(a)
    lab[ok & (a <= 0)] = "NEG"
    lab[ok & (a > 0) & (a <= 10)] = "LOW"
    rest = ok & (a > 10)
    q1, q2 = np.nanpercentile(a[rest], [100 / 3, 200 / 3])
    lab[rest & (a <= q1)] = "MID1"
    lab[rest & (a > q1) & (a <= q2)] = "MID2"
    lab[rest & (a > q2)] = "HIGH"
    order = np.argsort(-np.where(ok, a, -np.inf), kind="stable")[:N_TOP]
    lab[order] = "TOP"
    return lab


def rows(
    p: np.ndarray, d: np.ndarray, month: np.ndarray, b: dict
) -> tuple[float, float]:
    """(C3a %, C3b NRMSE) exactly as the scorer: demand-weighted model vs committed RT."""
    ann = float(np.sum(p * d) / d.sum())
    mon = [
        float(np.sum(p[month == m] * d[month == m]) / d[month == m].sum())
        for m in range(12)
    ]
    return 100 * (ann - b["rt"]) / b["rt"], float(_nrmse(mon, b["rt_mon"]))


def ownership(before: float, after: float, band: float, absval: bool) -> str:
    """PRECOMMIT §2 classification of removing one object's hourly error."""
    f = abs if absval else (lambda x: x)
    exc0, exc1 = f(before) - band, f(after) - band
    if exc1 <= 0:
        return "OWNS"
    if exc1 > exc0:
        return "OPPOSES"
    return "CONTRIBUTES" if (exc0 - exc1) >= 0.5 * exc0 else "MINOR"


def gas_published() -> pd.DataFrame:
    """EIA N3045 KS / OK monthly delivered-to-electric-power gas, $/MMBtu, + Henry Hub."""
    out = {}
    for st in ("KS", "OK"):
        g = pd.read_csv(
            RAW_DATA_DIR / f"gas-prices/eia_delivered_gas_{st}_monthly_2019-2022.csv"
        )
        g["v"] = pd.to_numeric(g["value"], errors="coerce") / MCF_TO_MMBTU
        out[st] = g.set_index("period")["v"]
    hh = pd.read_csv(RAW_DATA_DIR / "gas-prices/henry_hub_monthly.csv")
    hh["period"] = hh["year"].astype(str) + "-" + hh["month"].map("{:02d}".format)
    out["HH"] = hh.set_index("period")["price_usd_mmbtu"]
    return pd.DataFrame(out)


def main() -> None:
    """Part A for 2019-2022; one JSON blob."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    ft = pd.read_parquet(RAW_DATA_DIR / "SWPP_fueltype.parquet")
    gp = gas_published()
    ids, pm = swpp_gas_units()
    res = {"gas_published": gp.loc["2019-01":"2022-12"].to_dict(orient="index")}
    for y in YEARS:
        ly = lmp[lmp["year"] == y].sort_values("hour")
        a = ly["rt"].to_numpy(float)
        assert len(a) == 8760
        p, d = model_price_demand(y)
        clock = model_clock_index(y).tz_convert(None) - pd.Timedelta(hours=CST_OFFSET_H)
        month = clock.month.to_numpy() - 1
        with gzip.open(
            REPO_ROOT / f"frontend/data/backcast/bench/SPP/{y}.json.gz"
        ) as f:
            b = json.load(f)["bench"]["avgLMP"]
        c3a, c3b = rows(p, d, month, b)
        lab = hour_types(a)
        ok = np.isfinite(a)
        r = {"C3a": c3a, "C3b": c3b, "bench_rt": b["rt"], "bench_rt_mon": b["rt_mon"]}
        # --- the exact month split (PRECOMMIT §1) --------------------------------
        mons = []
        for m in range(12):
            mm = month == m
            n = int(mm.sum())
            wm = float(np.sum(p[mm] * d[mm]) / d[mm].sum())
            row = {
                "month": m + 1,
                "model_dw": wm,
                "rt_bench": b["rt_mon"][m],
                "e_m": wm - b["rt_mon"][m],
                "B_basis": wm - float(p[mm].mean()),
                "recon": float(np.nanmean(a[mm])) - b["rt_mon"][m],
                "n_nan_rt": int((mm & ~ok).sum()),
                "rt_lt0": int((mm & ok & (a < 0)).sum()),
                "rt_lt_m26": int((mm & ok & (a < -26)).sum()),
                "mod_le0": int((mm & (p <= 0)).sum()),
                "mod_clamp": int((mm & (p <= CLAMP)).sum()),
                "rt_mean": float(np.nanmean(a[mm])),
                "mod_eq_mean": float(p[mm].mean()),
            }
            for k in TYPES:
                hk = mm & ok & (lab == k)
                row[f"S_{k}"] = float(np.sum(p[hk] - a[hk]) / n)
                row[f"n_{k}"] = int(hk.sum())
                row[f"modmean_{k}"] = float(p[hk].mean()) if hk.any() else None
                row[f"rtmean_{k}"] = float(a[hk].mean()) if hk.any() else None
            mons.append(row)
        r["months"] = mons
        # annual split (equal-hour) for C3a
        n = ok.sum()
        r["annual_S"] = {k: float(np.sum((p - a)[ok & (lab == k)]) / n) for k in TYPES}
        r["annual_n"] = {k: int((ok & (lab == k)).sum()) for k in TYPES}
        r["annual_gap_eq"] = float(np.sum((p - a)[ok]) / n)
        r["annual_basis"] = float(np.sum(p * d) / d.sum() - p.mean())
        # --- §2 ownership (diagnostic counterfactual) ----------------------------
        objs = {
            "a_low_side": np.isin(lab, ["NEG", "LOW"]),
            "NEG": lab == "NEG",
            "LOW": lab == "LOW",
            "ordinary_MID": np.isin(lab, ["MID1", "MID2"]),
            "HIGH_exTOP": lab == "HIGH",
            "TOP": lab == "TOP",
        }
        own = {}
        for nm, mask in objs.items():
            q = p.copy()
            q[mask & ok] = a[mask & ok]
            a1, b1 = rows(q, d, month, b)
            own[nm] = {
                "C3a_after": a1,
                "C3b_after": b1,
                "C3a_class": ownership(c3a, a1, C3A_BAND, True),
                "C3b_class": ownership(c3b, b1, C3B_BAND, False),
            }
        r["ownership"] = own
        # --- (d) CT overrun + context energies -----------------------------------
        cm = model_class_mw(y)
        cs = campd_state(y, ids, pm)
        ct_meas = cs["CT"]["mw"]
        ct_mod = cm.get("CT_PEAKER", pd.Series(0.0, index=cm.index)).to_numpy()
        coal_mod = (
            cm[[c for c in cm.columns if c.startswith("COAL")]].sum(axis=1).to_numpy()
        )
        gas_mod = (
            cm[[c for c in cm.columns if c.startswith(("CC_", "CT_", "ST_"))]]
            .sum(axis=1)
            .to_numpy()
        )
        wind_mod = cm.get("wind", 0.0)
        wind_mod = np.asarray(wind_mod, float)
        meas = {
            k: fueltype(ft, k, y) for k in ("COL", "NG", "WND", "SUN", "OIL", "OTH")
        }
        mon_e = []
        for m in range(12):
            mm = month == m
            mon_e.append(
                {
                    "month": m + 1,
                    "ct_mod": float(ct_mod[mm].mean()),
                    "ct_campd": float(ct_meas[mm].mean()),
                    "coal_mod": float(coal_mod[mm].mean()),
                    "coal_930": float(meas["COL"][mm].mean()),
                    "gas_mod": float(gas_mod[mm].mean()),
                    "gas_930": float(meas["NG"][mm].mean()),
                    "wind_mod": float(wind_mod[mm].mean()),
                    "wind_930": float(meas["WND"][mm].mean()),
                    "therm_mod": float((coal_mod + gas_mod)[mm].mean()),
                    "therm_930": float((meas["COL"] + meas["NG"])[mm].mean()),
                }
            )
        r["energy_monthly"] = mon_e
        over = np.array([x["ct_mod"] - x["ct_campd"] for x in mon_e])
        em = np.array([x["e_m"] for x in mons])
        big2 = np.argsort(-np.abs(em))[:2]
        r["d_ct"] = {
            "overrun_mw": over.tolist(),
            "corr_overrun_em": float(np.corrcoef(over, em)[0, 1]),
            "big2_months": (big2 + 1).tolist(),
            "big2_overrun_above_median": [
                bool(over[i] > np.median(over)) for i in big2
            ],
            "annual_ct_mod": float(ct_mod.mean()),
            "annual_ct_campd": float(ct_meas.mean()),
            "missing_states": cs["missing_states"],
        }
        res[y] = r
        print(
            y,
            f"C3a {c3a:+.2f}%  C3b {c3b:.3f}",
            json.dumps({k: round(v["C3b_after"], 3) for k, v in own.items()}),
        )
    with open(args.out, "w") as f:
        json.dump(
            res,
            f,
            indent=1,
            default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o),
        )


if __name__ == "__main__":
    main()
