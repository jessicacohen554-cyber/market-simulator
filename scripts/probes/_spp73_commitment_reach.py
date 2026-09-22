"""SPP-73 (lever b, commitment reach): could ANY hourly commitment lever price SPP's tail?

Zero-LP measurement, pre-registered in
``docs/handoffs/PRECOMMIT-spp-73-commitment-reach-2026-09-22.md`` (pushed at ``91df082f``
before any number below was read). Hour sets reuse SPP-72 exactly (top-88 by measured RT on
the fixed-CST model clock, ``_spp72_demand_tightness.model_clock_index``).

* **M1** — the DA bound. SPP's day-ahead market is a unit commitment clearing on real
  start-up / no-load / min-run offers; its price in the RT top-88 hours bounds what an
  hourly commitment representation could reach. phi = (med_DA - med_MOD) / (med_RT - med_MOD).
* **M1b** — the measured DA series scored AS IF IT WERE THE MODEL, with the scorer's own
  ``_nrmse`` and the committed benchmark ``avgLMP.rt`` / ``rt_mon``.
* **M1c** — C3a decomposition into the top-88 hours and the rest.
* **M2** — measured commitment state (CAMPD, SWPP-BA plants) vs the model's class_hourly.

Usage: ``uv run python scripts/probes/_spp73_commitment_reach.py --out <json>``
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
    measured_series,
    model_clock_index,
)

YEARS = range(2019, 2026)
RUNG, SPAN = "spp71_ensemble_rung", "spp71_ensemble_span"
# Trap (f) physical ceilings on EIA-930 SWPP fuel-type series (PRECOMMIT §1)
WND_CEIL_MW, SUN_CEIL_MW = 40_000.0, 20_000.0
BIN_PT = 5.0  # requirement-percentile bin width for the matched control (PRECOMMIT §1)
TOP10 = 876  # hours excluded from the control: top-10 % by RT (PRECOMMIT §1)
SPP_STATES = (
    "KS",
    "OK",
    "NE",
    "ND",
    "SD",
    "NM",
    "TX",
    "AR",
    "LA",
    "MO",
    "IA",
    "MN",
    "MT",
    "WY",
)
MST_STATES = {
    "NM",
    "MT",
    "WY",
}  # CAMPD local standard time -> +1 h to CST (PRECOMMIT §3)
MODEL_GROUPS = {
    "CT": ["CT_PEAKER"],
    "CT_CHP": ["CT_CHP"],
    "CC": ["CC_REGULAR", "CC_CHP"],
    "ST_GAS": ["ST_GAS"],
}


def bundle_for(y: int) -> str:
    """Rung bundle for 2019-2022, keeper span for 2023-2025."""
    return RUNG if y <= 2022 else SPAN


def fueltype_series(ft: pd.DataFrame, code: str, y: int, ceil: float) -> np.ndarray:
    """EIA-930 SWPP fuel-type series on the model clock, trap-(f) guarded."""
    s = ft[ft["fueltype"] == code].set_index("period")["value_mwh"]
    s.index = s.index - pd.Timedelta(hours=1)
    s = s[~s.index.duplicated()]
    out = s.reindex(model_clock_index(y)).astype(float)
    out[(out > ceil) | (out < 0)] = np.nan
    return out.interpolate(limit_direction="both").fillna(0.0).to_numpy()


def model_price_demand(y: int) -> tuple[np.ndarray, np.ndarray]:
    """Demand-weighted P1 price across zones and total demand, per model hour."""
    s = pd.read_parquet(
        REPO_ROOT / "results/calibration" / bundle_for(y) / f"hourly/system_{y}.parquet"
    )
    s = s[s["pass"] == "P1"]
    d = s.pivot(index="hour", columns="zone", values="demand").sort_index()
    p = s.pivot(index="hour", columns="zone", values="price").sort_index()
    tot = d.sum(axis=1).to_numpy()
    return (p * d).sum(axis=1).to_numpy() / tot, tot


def model_class(y: int) -> dict[str, np.ndarray]:
    """P1 class MW per model hour, grouped per PRECOMMIT §3."""
    c = pd.read_parquet(
        REPO_ROOT
        / "results/calibration"
        / bundle_for(y)
        / f"hourly/class_hourly_{y}.parquet"
    )
    c = c[c["pass"] == "P1"]
    out = {}
    for g, ks in MODEL_GROUPS.items():
        sub = c[c["klass"].astype(str).isin(ks)].groupby("hour")["mw"].sum()
        out[g] = sub.reindex(range(8760), fill_value=0.0).to_numpy()
    return out


def matched_weights(
    rpct: np.ndarray, top: np.ndarray, ctrl_mask: np.ndarray
) -> np.ndarray:
    """Per-hour weights so the control's requirement-bin histogram equals H_top's."""
    b = np.minimum((rpct // BIN_PT).astype(int), int(100 / BIN_PT) - 1)
    w = np.zeros(8760)
    n_top = np.bincount(b[top], minlength=20)
    n_ctl = np.bincount(b[ctrl_mask], minlength=20)
    keep = (n_top > 0) & (n_ctl > 0)
    for k in np.flatnonzero(keep):
        idx = ctrl_mask & (b == k)
        w[idx] = n_top[k] / n_ctl[k]
    w /= w.sum()
    return w, int(n_top[~keep].sum())


def swpp_gas_units() -> tuple[set[int], dict[int, set[str]]]:
    """SWPP-BA plant ids (EIA-860, trap d) and each plant's prime-mover set."""
    plant = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_plant.parquet")
    ba = plant["Balancing Authority Code"].astype(str).str.strip().str.upper()
    ids = set(
        pd.to_numeric(plant.loc[ba == "SWPP", "Plant Code"], errors="coerce")
        .dropna()
        .astype(int)
    )
    gen = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_generator_operable.parquet")
    gen["pc"] = pd.to_numeric(gen["Plant Code"], errors="coerce")
    gen = gen[gen["pc"].isin(ids)]
    pm = gen.groupby("pc")["Prime Mover"].agg(
        lambda s: set(s.astype(str).str.strip().str.upper())
    )
    return ids, {int(k): v for k, v in pm.items()}


def classify(unit_type: str, fuel: str, pms: set[str]) -> str | None:
    """CT / CC / ST_GAS per PRECOMMIT §3, or None for non-gas units."""
    ut, fu = str(unit_type).lower(), str(fuel).lower()
    if "gas" not in fu:
        return None
    has_cc = bool(pms & {"CA", "CT", "CS"})
    has_gt = bool(pms & {"GT", "IC"})
    if "boiler" in ut or "stoker" in ut or "tangentially" in ut or "cyclone" in ut:
        return "ST_GAS"
    if "combined cycle" in ut:
        return "CC"
    if "turbine" in ut or "engine" in ut:
        if has_cc and not has_gt:
            return "CC"
        return "CT"
    if has_cc and not has_gt:
        return "CC"
    if has_gt and not has_cc:
        return "CT"
    return None


def campd_state(y: int, ids: set[int], pm: dict[int, set[str]]) -> dict:
    """Unit-hour on-state and gross MW per class on the model clock."""
    clock = model_clock_index(y)
    local_cst = (clock - pd.Timedelta(hours=CST_OFFSET_H)).tz_localize(None)
    slot = pd.Series(np.arange(8760), index=local_cst)
    frames, missing = [], []
    for st in SPP_STATES:
        p = RAW_DATA_DIR / f"campd-unit-level/{st}_{y}.parquet"
        if not p.exists():
            missing.append(st)
            continue
        d = pd.read_parquet(
            p,
            columns=[
                "stateCode",
                "facilityId",
                "unitId",
                "date",
                "hour",
                "opTime",
                "grossLoad",
                "primaryFuelInfo",
                "unitType",
            ],
        )
        d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce")
        d = d[d["facilityId"].isin(ids)]
        if len(d):
            frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    ts = ts + pd.to_timedelta(d["stateCode"].isin(MST_STATES).astype(int), unit="h")
    d["slot"] = slot.reindex(ts.to_numpy()).to_numpy()
    d = d[np.isfinite(d["slot"])]
    d["slot"] = d["slot"].astype(int)
    ukey = d["facilityId"].astype(str) + "|" + d["unitId"].astype(str)
    meta = (
        d.assign(u=ukey)
        .groupby("u")
        .agg(
            fid=("facilityId", "first"),
            ut=("unitType", "first"),
            fu=("primaryFuelInfo", "first"),
        )
    )
    meta["klass"] = [
        classify(r.ut, r.fu, pm.get(int(r.fid), set())) for r in meta.itertuples()
    ]
    out = {"missing_states": missing}
    for k in ("CT", "CC", "ST_GAS"):
        units = meta.index[meta["klass"] == k]
        sub = d[ukey.isin(units)]
        uix = pd.Index(units)
        on = np.zeros((len(units), 8760), dtype=bool)
        mw = np.zeros((len(units), 8760))
        r = uix.get_indexer(ukey[sub.index])
        on[r, sub["slot"].to_numpy()] = sub["opTime"].fillna(0).to_numpy() > 0
        mw[r, sub["slot"].to_numpy()] = sub["grossLoad"].fillna(0).to_numpy()
        prev1 = np.concatenate([np.ones((len(units), 1), bool), on[:, :-1]], axis=1)
        prev2 = np.concatenate([np.ones((len(units), 2), bool), on[:, :-2]], axis=1)
        started = on & (~prev1 | ~prev2)
        out[k] = {
            "n_units": len(units),
            "on": on.sum(0),
            "mw": mw.sum(0),
            "started": started.sum(0),
        }
    return out


def bench_avg(y: int) -> dict:
    """Committed benchmark avgLMP (the scorer's actual side)."""
    with gzip.open(REPO_ROOT / f"frontend/data/backcast/bench/SPP/{y}.json.gz") as f:
        return json.load(f)["bench"]["avgLMP"]


def main() -> None:
    """Run M1/M1b/M1c/M2 for every year and write one JSON blob."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    region = pd.read_parquet(RAW_DATA_DIR / "SWPP_region.parquet")
    ft = pd.read_parquet(RAW_DATA_DIR / "SWPP_fueltype.parquet")
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    ids, pm = swpp_gas_units()
    res = {}
    for y in YEARS:
        ly = lmp[lmp["year"] == y].sort_values("hour")
        rt, da = ly["rt"].to_numpy(float), ly["da"].to_numpy(float)
        assert len(rt) == 8760
        valid = np.isfinite(rt)
        order = np.argsort(-np.where(valid, rt, -np.inf), kind="stable")
        top, top10 = order[:N_TOP], order[:TOP10]
        pm_, dem = model_price_demand(y)
        month = model_clock_index(y).tz_convert(None) - pd.Timedelta(hours=CST_OFFSET_H)
        month = month.month.to_numpy() - 1
        r = {}
        # --- M1: the DA bound -------------------------------------------------
        med = {
            k: float(np.nanmedian(v[top]))
            for k, v in (("rt", rt), ("da", da), ("mod", pm_))
        }
        num, den = med["da"] - med["mod"], med["rt"] - med["mod"]
        r["M1"] = {
            **{f"med_{k}": v for k, v in med.items()},
            "phi_num": num,
            "phi_den": den,
            "phi": num / den,
            "da_gt_200_in_top": int((da[top] > 200).sum()),
            "rt_gt_200_in_top": int((rt[top] > 200).sum()),
            "mean_rt_top": float(np.nanmean(rt[top])),
            "mean_da_top": float(np.nanmean(da[top])),
            "mean_mod_top": float(pm_[top].mean()),
        }
        # --- M1b: DA scored as if it were the model ---------------------------
        b = bench_avg(y)
        ok = np.isfinite(da)
        da_lw = float(np.sum(da[ok] * dem[ok]) / dem[ok].sum())
        da_eq = float(np.nanmean(da))
        mod_lw = float(np.sum(pm_ * dem) / dem.sum())
        da_mon_lw = [
            float(
                np.sum(da[ok & (month == m)] * dem[ok & (month == m)])
                / dem[ok & (month == m)].sum()
            )
            for m in range(12)
        ]
        da_mon_eq = [float(np.nanmean(da[month == m])) for m in range(12)]
        mod_mon = [
            float(np.sum(pm_[month == m] * dem[month == m]) / dem[month == m].sum())
            for m in range(12)
        ]
        rt_eq_mon = [float(np.nanmean(rt[month == m])) for m in range(12)]
        r["M1b"] = {
            "bench_rt": b["rt"],
            "bench_rt_mon": b["rt_mon"],
            "bench_da": b.get("da"),
            "repro_rt_eq": float(np.nanmean(rt)),
            "repro_rt_mon_eq": rt_eq_mon,
            "da_lw": da_lw,
            "da_eq": da_eq,
            "mod_lw_hub_proxy": mod_lw,
            "C3a_da_lw_pct": 100 * (da_lw - b["rt"]) / b["rt"],
            "C3a_da_eq_pct": 100 * (da_eq - b["rt"]) / b["rt"],
            "C3a_mod_proxy_pct": 100 * (mod_lw - b["rt"]) / b["rt"],
            "C3b_da_lw": _nrmse(da_mon_lw, b["rt_mon"]),
            "C3b_da_eq": _nrmse(da_mon_eq, b["rt_mon"]),
            "C3b_mod_proxy": _nrmse(mod_mon, b["rt_mon"]),
            "da_mon_lw": da_mon_lw,
            "mod_mon": mod_mon,
        }
        # --- M1c: C3a decomposition (equal-hour, hub) --------------------------
        diff = pm_ - rt
        mask_top = np.zeros(8760, bool)
        mask_top[top] = True
        n = valid.sum()
        r["M1c"] = {
            "gap_total": float(np.nansum(diff[valid]) / n),
            "gap_top": float(np.nansum(diff[valid & mask_top]) / n),
            "gap_rest": float(np.nansum(diff[valid & ~mask_top]) / n),
            "mean_rt": float(np.nanmean(rt)),
            "mean_mod_eq": float(pm_.mean()),
        }
        # --- M2: commitment state ----------------------------------------------
        load = measured_series(region, "D", y)
        ti = measured_series(region, "TI", y)
        req = (
            load
            + ti
            - fueltype_series(ft, "WND", y, WND_CEIL_MW)
            - fueltype_series(ft, "SUN", y, SUN_CEIL_MW)
        )
        rpct = pd.Series(req).rank(pct=True).to_numpy() * 100.0
        ctrl_mask = np.ones(8760, bool)
        ctrl_mask[top10] = False
        w, dropped = matched_weights(rpct, top, ctrl_mask)
        mc = model_class(y)
        cs = campd_state(y, ids, pm)
        m2 = {
            "missing_states": cs["missing_states"],
            "top_hours_in_unmatched_bins": dropped,
            "req_pct_top_median": float(np.median(rpct[top])),
        }
        for k in ("CT", "CC", "ST_GAS"):
            c = cs[k]
            mw_t, mw_c = float(c["mw"][top].mean()), float(np.sum(c["mw"] * w))
            md_t, md_c = float(mc[k][top].mean()), float(np.sum(mc[k] * w))
            on_t, on_c = float(c["on"][top].mean()), float(np.sum(c["on"] * w))
            s2_t = float(c["started"][top].sum() / max(c["on"][top].sum(), 1))
            s2_c = float(np.sum(c["started"] * w) / max(np.sum(c["on"] * w), 1e-9))
            m2[k] = {
                "n_units": c["n_units"],
                "meas_mw_top": mw_t,
                "meas_mw_ctrl": mw_c,
                "rho_meas": mw_t / mw_c if mw_c else None,
                "mod_mw_top": md_t,
                "mod_mw_ctrl": md_c,
                "rho_mod": md_t / md_c if md_c else None,
                "meas_units_on_top": on_t,
                "meas_units_on_ctrl": on_c,
                "s2_top": s2_t,
                "s2_ctrl": s2_c,
                "s3_meas_share_hours_on": float((c["mw"] > 0).mean()),
                "s3_mod_share_hours_on": float((mc[k] > 0).mean()),
                "s4_meas_mean_mw": float(c["mw"].mean()),
                "s4_mod_mean_mw": float(mc[k].mean()),
                "meas_units_on_mean": float(c["on"].mean()),
            }
        ct = m2["CT"]
        m2["V2"] = bool(
            ct["rho_meas"]
            and ct["rho_mod"]
            and ct["rho_meas"] >= 1.5 * ct["rho_mod"]
            and ct["s2_top"] >= 2 * ct["s2_ctrl"]
        )
        m2["CT_CHP_model"] = {
            "mod_mw_top": float(mc["CT_CHP"][top].mean()),
            "s4_mod_mean_mw": float(mc["CT_CHP"].mean()),
        }
        r["M2"] = m2
        res[y] = r
        print(
            y,
            json.dumps(
                {
                    "M1": r["M1"],
                    "C3a_da": r["M1b"]["C3a_da_lw_pct"],
                    "C3b_da": r["M1b"]["C3b_da_lw"],
                    "V2": m2["V2"],
                },
                default=float,
            ),
        )
    rung = [2019, 2021, 2022]
    phis = {y: res[y]["M1"]["phi"] for y in YEARS}
    n_hi = sum(phis[y] >= 0.5 for y in rung)
    n_lo = sum(phis[y] < 0.5 for y in rung)
    v1 = (
        "REAL"
        if phis[2020] >= 0.5 and n_hi >= 2
        else ("NOT REAL" if phis[2020] < 0.5 and n_lo >= 2 else "MIXED")
    )
    res["verdict"] = {"V1": v1, "phi": phis, "V2_2020": res[2020]["M2"]["V2"]}
    print(json.dumps(res["verdict"]))
    with open(args.out, "w") as f:
        json.dump(
            res,
            f,
            indent=1,
            default=lambda o: o.tolist() if hasattr(o, "tolist") else float(o),
        )


if __name__ == "__main__":
    main()
