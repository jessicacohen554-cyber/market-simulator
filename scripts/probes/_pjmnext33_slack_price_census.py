"""PJM-NEXT-33 phase 0 (ZERO LP): slack-hour price census.

Readings pre-fixed in ``docs/records/pjm/FINDING-pjm-next-33-slack-hour-price-census-2026-10-03.md`` §1
(committed before this probe ran). The gap is the keeper P1 zone price minus the real zonal DA
(``actual_lmp_zonal_PJM.parquet``), over three zone-hour populations:

* ``D`` — NEXT-32 M+L uncovered real-dark coal-fuel MW of COAL_BIT plants, at the plant's zone;
* ``L`` — NEXT-29 real low hours (system DA / delivered gas < 6.5), keeper zone demand weights;
* ``A`` — all zone-hours, keeper zone demand weights.

Q1 level vs spread; Q2 setter cells (NEXT-28 anchoring); Q3 IMM marginal fuel buckets; Q4 CC
setter offer vs measured incremental cost; Q5 year discrimination.

Inputs are read-only: the keeper sidecars (tree, else the ``origin/main`` blob), the NEXT-32
CAMPD helpers, ``data/raw/pjm-marginal-fuel/by-year/`` and the ``_pjmco_0d`` plant artifact.
Run: ``.venv/bin/python scripts/probes/_pjmnext33_slack_price_census.py [YEAR ...]``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
sys.path.insert(0, str(REPO / "src"))
from _pjmnext28_sunk_noload import ANCHOR_TOL, VOM_CC, _parquet, gas_daily  # noqa: E402
from _pjmnext29_lowhour_setters import IMM_DIR, _cell, real_low_hours  # noqa: E402
from _pjmnext32_coal_commitment_census import (  # noqa: E402
    LONG_H,
    MIN_DOWN,
    T,
    _runs,
    coal_units,
    covered_masks,
    keeper_plants,
)

RAW = REPO / "data/raw"
ZONAL = RAW / "_validation-source/actual_lmp_zonal_PJM.parquet"
INC_HR = REPO / "results/phase0/pjm/_pjmco_0d_incremental_hr_census_plants.csv"
OUT = REPO / "results/phase0/pjm/_pjmnext33_slack_price_census.json"
YEARS = tuple(range(2019, 2026))
FAIL = (2019, 2020, 2021)
CTRL = (2023, 2024)
EXTERNAL = "PJM_external"
SPREAD_SHARE = 0.4
CONC_TOP2 = 0.6
COAL_FOR_GAS = 0.3
OFFER_SIDE = 0.5
DISC_USD = 2.0
DOMINANT = 0.5
SPECIAL_FUEL = ("import", "hydro", "nuclear")


def dark_weights(y: int) -> dict[str, np.ndarray]:
    """Zone -> hourly M+L uncovered real-dark coal-fuel MW (NEXT-32 ``K*·unc_ml``)."""
    kp = keeper_plants(y)
    d = coal_units(y, set(kp))
    cov = covered_masks(y)
    out: dict[str, np.ndarray] = {}
    for pc, g in d.groupby("facilityId"):
        P = kp.get(int(pc))
        if P is None:
            continue
        kstar = float(np.vstack([t[2] for t in P["tr"]]).sum(0).max())
        if kstar <= 0:
            continue
        units = {}
        for uid, gu in g.groupby("unitId"):
            gross = np.zeros(T)
            op = np.zeros(T)
            gross[gu["hoy"].to_numpy()] = gu["grossLoad"].fillna(0.0).to_numpy()
            op[gu["hoy"].to_numpy()] = gu["opTime"].fillna(0.0).to_numpy()
            if gross.max() > 0:
                units[uid] = (gross.max(), op <= 0.0)
        if not units:
            continue
        ptot = sum(v[0] for v in units.values())
        unc_ml = np.zeros(T)
        for uid, (pk, dark) in units.items():
            ud = dark & ~cov.get((int(pc), uid), np.zeros(T, bool))
            for s, e in _runs(ud):
                if e - s >= MIN_DOWN:  # M (< LONG_H) and L (>= LONG_H) bands
                    unc_ml[s:e] += pk / ptot
        w = out.setdefault(P["zone"], np.zeros(T))
        w += kstar * unc_ml
    assert LONG_H > MIN_DOWN
    return out


def imm_hourly(y: int) -> pd.DataFrame:
    """IMM time-weighted marginal-fuel shares (gas, coal) by hour of year."""
    d = pd.read_csv(IMM_DIR / f"pjm_marginal_fuel_{y}.csv")
    ts = pd.to_datetime(d["hour_beginning_ept"], format="%Y-%m-%d %H:%M")
    d["hoy"] = ((ts - pd.Timestamp(f"{y}-01-01")) / pd.Timedelta("1h")).astype(int)
    f = (
        d["fuel_type"]
        .map({"Natural Gas": "gas", "Coal": "coal", "Waste Coal": "coal"})
        .fillna("other")
    )
    w = d.assign(f=f).pivot_table(
        index="hoy", columns="f", values="percent_marginal", aggfunc="sum"
    )
    w = w.div(w.sum(axis=1), axis=0).fillna(0.0).reindex(range(T)).fillna(0.0)
    for c in ("gas", "coal", "other"):
        if c not in w:
            w[c] = 0.0
    w["bucket"] = np.where(
        w["gas"] >= DOMINANT, "gas", np.where(w["coal"] >= DOMINANT, "coal", "mixed")
    )
    return w


def inc_hr_table(y: int) -> dict[int, float]:
    """``_pjmco_0d`` measured CC incremental HR (net), year else plant mean."""
    a = pd.read_csv(INC_HR)
    a = a[np.isfinite(a["inc_hr_net"]) & (a["inc_hr_net"] > 0)]
    out = a.groupby("plant_code")["inc_hr_net"].mean().to_dict()
    out.update(a[a["year"] == y].set_index("plant_code")["inc_hr_net"].to_dict())
    return {int(k): float(v) for k, v in out.items()}


def _wmean(v: np.ndarray, w: np.ndarray) -> float | None:
    s = float(w.sum())
    return float((v * w).sum() / s) if s > 0 else None


def run_year(y: int, gas: pd.Series) -> dict:
    """Q1-Q4 for one year."""
    sysd = _parquet(
        f"system_{y}.parquet", columns=["pass", "zone", "hour", "price", "demand"]
    )
    sysd = sysd[sysd["pass"] == "P1"].drop(columns="pass")
    sysd["zone"] = sysd["zone"].astype(str)
    sysd = sysd[sysd["zone"] != EXTERNAL]
    real = pd.read_parquet(ZONAL)
    real = real[real["year"] == y][["zone", "hour", "da"]].rename(
        columns={"da": "p_real"}
    )
    real["zone"] = real["zone"].astype(str)
    x = sysd.merge(real, on=["zone", "hour"], how="inner")
    x = x[(x["hour"] >= 0) & (x["hour"] < T)].reset_index(drop=True)
    x["d"] = x["price"] - x["p_real"]
    tot = x.groupby("hour")["demand"].transform("sum")
    x["pk_sys"] = (x["price"] * x["demand"]).groupby(x["hour"]).transform("sum") / tot
    x["pr_sys"] = (x["p_real"] * x["demand"]).groupby(x["hour"]).transform("sum") / tot
    x["d_lvl"] = x["pk_sys"] - x["pr_sys"]
    x["d_spr"] = x["d"] - x["d_lvl"]

    # populations
    dw = dark_weights(y)
    x["wD"] = 0.0
    for z, w in dw.items():
        m = x["zone"] == z
        x.loc[m, "wD"] = w[x.loc[m, "hour"].to_numpy()]
    rl = real_low_hours(y, gas)
    low = rl["low"].reindex(range(T)).fillna(False).to_numpy(bool)
    x["wL"] = np.where(low[x["hour"].to_numpy()], x["demand"], 0.0)
    x["wA"] = x["demand"]
    gas_h = rl["gas"].reindex(range(T)).to_numpy(float)
    x["gas"] = gas_h[x["hour"].to_numpy()]

    q1 = {}
    for p in ("D", "L", "A"):
        w = x[f"w{p}"].to_numpy()
        q1[p] = {
            "weight_twh": float(w.sum()) / 1e6,
            "d": _wmean(x["d"].to_numpy(), w),
            "d_lvl": _wmean(x["d_lvl"].to_numpy(), w),
            "d_spr": _wmean(x["d_spr"].to_numpy(), w),
            "p_keeper": _wmean(x["price"].to_numpy(), w),
            "p_real": _wmean(x["p_real"].to_numpy(), w),
        }
    zd = x.groupby("zone").apply(
        lambda g: pd.Series(
            {
                "wD_share": g["wD"].sum() / max(x["wD"].sum(), 1e-9),
                "d": _wmean(g["d"].to_numpy(), g["wD"].to_numpy()),
                "d_spr": _wmean(g["d_spr"].to_numpy(), g["wD"].to_numpy()),
            }
        ),
        include_groups=False,
    )
    q1["D_by_zone"] = {
        z: {k: (None if pd.isna(v) else round(float(v), 3)) for k, v in r.items()}
        for z, r in zd.iterrows()
    }

    # --- Q2 anchoring (marginal == 1 units, nearest mc in ratio) -------------------
    cols = ["unit_id", "plant_group", "plant_code", "fuel", "hour", "mc"]
    m = _parquet(
        f"unit_marginal_{y}.parquet",
        columns=cols,
        filters=[("pass", "=", "P1"), ("marginal", "=", 1)],
    )
    m = m[m["mc"] > 0].copy()
    for c in ("unit_id", "plant_group", "fuel"):
        m[c] = m[c].astype(str)
    key = m[["unit_id", "plant_group", "fuel"]].drop_duplicates().reset_index(drop=True)
    cell = _cell(key)
    special = key["fuel"].isin(SPECIAL_FUEL)
    virt = key["plant_group"].str.startswith("VIRTUAL")
    cell = np.where(special, key["fuel"], np.where(virt, key["plant_group"], cell))
    m["cell"] = m["unit_id"].map(dict(zip(key["unit_id"], cell)))
    act = x[(x["wD"] > 0) | (x["wL"] > 0)][
        ["zone", "hour", "price", "p_real", "d", "wD", "wL", "gas"]
    ]
    a = act.merge(m[["hour", "cell", "fuel", "plant_code", "mc"]], on="hour")
    a["dev"] = (a["price"] / a["mc"] - 1.0).abs()
    a = a[a["dev"] <= ANCHOR_TOL]
    a = a.loc[a.groupby(["zone", "hour"])["dev"].idxmin()]
    act = act.merge(
        a[["zone", "hour", "cell", "fuel", "plant_code", "mc"]],
        on=["zone", "hour"],
        how="left",
    )
    act["cell"] = act["cell"].fillna("unanchored")
    imm = imm_hourly(y)
    act["imm_gas"] = imm["gas"].to_numpy()[act["hour"].to_numpy()]
    act["bucket"] = imm["bucket"].to_numpy()[act["hour"].to_numpy()]

    q2, q3, q4 = {}, {}, {}
    inc = inc_hr_table(y)
    for p in ("D", "L"):
        s = act[act[f"w{p}"] > 0]
        wd = s[f"w{p}"] * s["d"]
        totwd = float(wd.sum())
        anch = s["cell"] != "unanchored"
        by = (wd.groupby(s["cell"]).sum() / totwd).sort_values(ascending=False)
        q2[p] = {
            "sum_wd": totwd,
            "anchored_weight_share": float(
                s.loc[anch, f"w{p}"].sum() / s[f"w{p}"].sum()
            ),
            "cells": {k: round(float(v), 4) for k, v in by.head(12).items()},
            "anchored_sum_wd": float(wd[anch].sum()),
            "cell_mean_d": {
                k: _wmean(
                    s.loc[s["cell"] == k, "d"].to_numpy(),
                    s.loc[s["cell"] == k, f"w{p}"].to_numpy(),
                )
                for k in by.head(6).index
            },
        }
        q3[p] = {
            "bucket_share_wd": {
                b: float(wd[s["bucket"] == b].sum() / totwd)
                for b in ("gas", "coal", "mixed")
            },
            "bucket_weight_share": {
                b: float(s.loc[s["bucket"] == b, f"w{p}"].sum() / s[f"w{p}"].sum())
                for b in ("gas", "coal", "mixed")
            },
            "bucket_mean_d": {
                b: _wmean(
                    s.loc[s["bucket"] == b, "d"].to_numpy(),
                    s.loc[s["bucket"] == b, f"w{p}"].to_numpy(),
                )
                for b in ("gas", "coal", "mixed")
            },
            "coal_for_gas_share_wd": float(
                wd[(s["fuel"] == "coal") & (s["imm_gas"] >= DOMINANT)].sum() / totwd
            ),
            "imm_gas_mean": _wmean(s["imm_gas"].to_numpy(), s[f"w{p}"].to_numpy()),
        }
        # Q4: CC_REGULAR econ setters
        cc = s[s["cell"].str.match(r"^CC_REGULAR:econ")].copy()
        hr = cc["plant_code"].map(lambda v: inc.get(int(v)) if pd.notna(v) else None)
        cc = cc[hr.notna()]
        hr = hr[hr.notna()].astype(float)
        cc["p_meas"] = hr * cc["gas"] + VOM_CC
        w = cc[f"w{p}"].to_numpy()
        coal = s[s["cell"].str.match(r"^COAL_BIT:")]
        q4[p] = {
            "cc_wd_share": float((cc[f"w{p}"] * cc["d"]).sum() / totwd)
            if totwd
            else None,
            "cc_measured_cov": float(
                w.sum()
                / max(
                    s.loc[s["cell"].str.match(r"^CC_REGULAR:econ"), f"w{p}"].sum(), 1e-9
                )
            ),
            "cc_mean_d": _wmean(cc["d"].to_numpy(), w),
            "cc_offer_minus_meas": _wmean((cc["mc"] - cc["p_meas"]).to_numpy(), w),
            "cc_meas_minus_real": _wmean((cc["p_meas"] - cc["p_real"]).to_numpy(), w),
            "cc_median_mc_over_gas": float(np.median(cc["mc"] / cc["gas"]))
            if len(cc)
            else None,
            "cc_median_meas_hr": float(np.median(hr)) if len(hr) else None,
            "cc_median_real_over_gas": float(np.median(cc["p_real"] / cc["gas"]))
            if len(cc)
            else None,
            "coalbit_median_mc_over_gas": float(np.median(coal["mc"] / coal["gas"]))
            if len(coal)
            else None,
            "coalbit_median_real_over_gas": float(
                np.median(coal["p_real"] / coal["gas"])
            )
            if len(coal)
            else None,
        }
    return {"q1": q1, "q2": q2, "q3": q3, "q4": q4}


def readings(res: dict) -> dict:
    """Apply FINDING §1 Q1-Q5 and the decision rule as fixed."""
    fy = [y for y in FAIL if y in res]
    spr = [
        res[y]["q1"]["D"]["d_spr"] >= SPREAD_SHARE * res[y]["q1"]["D"]["d"] for y in fy
    ]
    q1 = "SPREAD" if sum(spr) >= 2 else "LEVEL"
    pool: dict[str, float] = {}
    anch = 0.0
    tot = 0.0
    cfg = 0.0
    for y in fy:
        q = res[y]["q2"]["D"]
        anch += q["anchored_sum_wd"]
        tot += q["sum_wd"]
        cfg += res[y]["q3"]["D"]["coal_for_gas_share_wd"] * q["sum_wd"]
        for c, v in q["cells"].items():
            pool[c] = pool.get(c, 0.0) + v * q["sum_wd"]
    ranked = sorted(
        ((c, v / anch) for c, v in pool.items() if c != "unanchored"),
        key=lambda t: -t[1],
    )
    top2 = sum(v for _, v in ranked[:2])
    q3 = "COAL-FOR-GAS" if cfg / tot >= COAL_FOR_GAS else "NOT COAL-FOR-GAS"
    off = []
    for y in fy:
        q = res[y]["q4"]["D"]
        off.append(
            q["cc_mean_d"] is not None
            and q["cc_offer_minus_meas"] >= OFFER_SIDE * q["cc_mean_d"]
        )
    q4 = "OFFER-SIDE" if sum(off) >= 2 else "REAL-BELOW-COST"
    q5 = {}
    for p in ("D", "L"):
        if all(y in res for y in FAIL + CTRL):
            lo = min(res[y]["q1"][p]["d"] for y in FAIL)
            hi = max(res[y]["q1"][p]["d"] for y in CTRL)
            q5[p] = {
                "fail_min": lo,
                "ctrl_max": hi,
                "reading": "DISCRIMINATING"
                if lo >= hi + DISC_USD
                else "NOT DISCRIMINATING",
            }
    return {
        "Q1": q1,
        "Q2": {
            "carrier": ranked[0][0] if ranked else None,
            "top_cells_anchored_share": [(c, round(v, 4)) for c, v in ranked[:6]],
            "top2": round(top2, 4),
            "reading": "CONCENTRATED" if top2 >= CONC_TOP2 else "DIFFUSE",
        },
        "Q3": {"coal_for_gas_pooled": round(cfg / tot, 4), "reading": q3},
        "Q4": q4,
        "Q5": q5,
    }


def main(years: list[int]) -> None:
    gas = gas_daily()
    res = {}
    for y in years:
        print(f"[{y}] ...", flush=True)
        res[y] = run_year(y, gas)
        print(json.dumps(res[y]["q1"]["D"]), flush=True)
    out = {"years": {str(k): v for k, v in res.items()}, "readings": readings(res)}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(json.dumps(out["readings"], indent=1))


if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or list(YEARS))
