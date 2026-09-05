"""caiso-252 phase 0 (ZERO LP): anatomy of the C4 gas-fleet hourly NRMSE cell.

Reproduces the scorer's own C4 gas construction (``calibration_verdict.
_cems_gas_hourly_fit``: CEMS-covered plants' hourly CF from the committed run
payload vs the bench part's CAMPD hourly, flat BTM removal on both sides, flat
cogen block on the actual, flat fill to the committed fuel-row level on the
model) plant-for-plant from committed artifacts only, then decomposes the
squared error EXACTLY by class (covariance attribution), hour-of-day, month and
plant, and differences the keeper against the prior keeper (rule 29(b): the
prior keeper's committed payload is the control). The import-displacement leg
reads the two bundles' ``hourly/class_hourly_<year>.parquet`` sidecars.

Registered: ``results/calibration/PRECOMMIT-caiso252-c4-gas-nrmse-anatomy-2026-09-05.md``.
Output: ``results/calibration/_caiso252_c4_gas_nrmse_anatomy.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso252_c4_gas_nrmse_anatomy.py
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.argv = [sys.argv[0]]  # calibration_verdict parses argv at import

from scripts.calibration_verdict import GAS_CLASSES, load_artifacts  # noqa: E402

KEEPER = "2026-09-05-caiso-251-b1-nomargin"
PRIOR = "2026-09-05-caiso-246-b1-spot"
BUNDLES = {
    KEEPER: REPO / "results/calibration/caiso251_arm_nomargin",
    PRIOR: REPO / "results/calibration/caiso246_b1_spot_coverage",
}
YEARS = (2023, 2024, 2025)
T = 8760
IMPORT_DROP_MW = -500.0  # P-4 subset threshold, fixed in the PRECOMMIT
EVENING = (17, 18, 19, 20, 21)
MIDDAY = (10, 11, 12, 13, 14, 15)
OUT = REPO / "results/calibration/_caiso252_c4_gas_nrmse_anatomy.json"

# Month boundaries on the non-leap 8760 clock (Feb-29 dropped by the solve).
_MDAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.repeat(np.arange(1, 13), np.array(_MDAYS) * 24)
HOD = np.arange(T) % 24


def _b64(s: str) -> np.ndarray:
    return np.frombuffer(base64.b64decode(s), dtype=np.uint8)[:T].astype(float)


def _fleet(ypay: dict, ybench: dict) -> dict:
    """Per-plant model/actual MW on the scorer's basis; returns the pieces."""
    e930 = ybench["e930"]
    cogen = float(e930["gas_cogen_grid"])
    bplants, pplants = ybench["plants"], ypay["plants"]
    model_twh = next(r["m"] for r in ypay["fuelRows"] if r["fuel"] == "gas")
    plants = {}
    btm_twh = 0.0
    for code, bp in bplants.items():
        if bp.get("group") not in GAS_CLASSES or bp.get("nodata"):
            continue
        cap = float(bp.get("npl") or 0.0)
        pp = pplants.get(str(code))
        if cap <= 0.0 or not bp.get("campd") or not pp or not pp.get("m"):
            continue
        scale = cap / 100.0
        plants[str(code)] = {
            "group": bp["group"],
            "name": bp.get("name"),
            "zone": bp.get("zone"),
            "npl": cap,
            "act": _b64(bp["campd"]) * scale,
            "mod": _b64(pp["m"]) * scale,
        }
        btm_twh += float(bp.get("btm") or 0.0)
    btm_mw = btm_twh * 1e6 / T
    core_twh = sum(p["mod"].sum() for p in plants.values()) / 1e6 - btm_twh
    fill_mw = (float(model_twh) - core_twh) * 1e6 / T
    act = sum(p["act"] for p in plants.values()) - btm_mw + cogen * 1e6 / T
    mod = sum(p["mod"] for p in plants.values()) - btm_mw + fill_mw
    return {
        "plants": plants, "act": act, "mod": mod, "e": mod - act,
        "k": fill_mw - cogen * 1e6 / T, "fill_mw": fill_mw,
        "cogen_mw": cogen * 1e6 / T, "btm_mw": btm_mw, "n_plants": len(plants),
        "model_twh": float(model_twh), "actual_twh": act.sum() / 1e6,
    }


def _fit(mod: np.ndarray, act: np.ndarray) -> tuple[float, float]:
    r = float(np.corrcoef(mod, act)[0, 1])
    nrmse = float(np.sqrt(np.mean((mod - act) ** 2)) / act.mean())
    return round(r, 3), round(nrmse, 3)


def _cov(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.mean((a - a.mean()) * (b - b.mean())))


def _class_terms(fl: dict) -> dict:
    e = fl["e"]
    var_e = float(e.var())
    out = {}
    for c in GAS_CLASSES:
        ps = [p for p in fl["plants"].values() if p["group"] == c]
        if not ps:
            continue
        ec = sum(p["mod"] - p["act"] for p in ps)
        mse_c = _cov(ec, e)
        out[c] = {
            "n_plants": len(ps),
            "mse_c_cov": mse_c,
            "share_of_var": mse_c / var_e if var_e else None,
            "rmse_own": float(np.sqrt(np.mean(ec**2))),
            "bias_mw": float(ec.mean()),
            "bias2_share_of_own_mse": float(ec.mean() ** 2 / np.mean(ec**2)) if np.mean(ec**2) else None,
            "model_twh_cems": float(sum(p["mod"].sum() for p in ps)) / 1e6,
            "actual_twh_cems": float(sum(p["act"].sum() for p in ps)) / 1e6,
            "e_by_hod_mw": [float(ec[HOD == h].mean()) for h in range(24)],
        }
    return out


def _by_hod(e2: np.ndarray) -> list[float]:
    return [float(e2[HOD == h].mean()) for h in range(24)]


def _by_month(e2: np.ndarray) -> list[float]:
    return [float(e2[MONTH_OF_HOUR == m].mean()) for m in range(1, 13)]


def _class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    d = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    d = d[d["pass"] == "P1"]
    piv = d.pivot_table(index="hour", columns="klass", values="mw").reindex(range(T))
    return {k: piv[k].to_numpy(float) for k in piv.columns}


def main() -> None:
    arts = {rid: load_artifacts(rid) for rid in (KEEPER, PRIOR)}
    verdicts = {}
    for rid, b in BUNDLES.items():
        v = json.loads((b / "_verdict.json").read_text())
        for r in v["criteria"]["dispatch_corr"]["records"]:
            if r["key"] == "gas":
                rr, nr = r["model"].replace("r=", "").replace("nrmse=", "").split()
                verdicts[(rid, int(r["year"]))] = (float(rr), float(nr))
    res: dict = {"keeper": KEEPER, "prior": PRIOR, "years": {}, "g_repro": {}}
    fleets: dict = {}
    for y in YEARS:
        fleets[y] = {}
        for rid in (KEEPER, PRIOR):
            a = arts[rid]
            fl = _fleet(a["payload"]["years"][str(y)], a["bench"][y])
            fleets[y][rid] = fl
            r, n = _fit(fl["mod"], fl["act"])
            vr, vn = verdicts[(rid, y)]
            res["g_repro"][f"{rid}:{y}"] = {
                "recomputed": [r, n], "verdict": [vr, vn],
                "pass": abs(r - vr) <= 0.001 + 1e-9 and abs(n - vn) <= 0.001 + 1e-9,
                "n_plants": fl["n_plants"],
            }
    res["g_repro"]["all_pass"] = all(v["pass"] for k, v in res["g_repro"].items() if ":" in k)

    for y in YEARS:
        K, P = fleets[y][KEEPER], fleets[y][PRIOR]
        eK, eP = K["e"], P["e"]
        mseK, mseP = float(np.mean(eK**2)), float(np.mean(eP**2))
        clsK, clsP = _class_terms(K), _class_terms(P)
        d_mse = mseK - mseP
        d_e2 = eK**2 - eP**2
        # import-displacement leg
        chK, chP = _class_hourly(BUNDLES[KEEPER], y), _class_hourly(BUNDLES[PRIOR], y)
        dimp = chK["import"] - chP["import"]
        dcc = chK["CC_REGULAR"] - chP["CC_REGULAR"]
        dct = chK["CT_PEAKER"] - chP["CT_PEAKER"]
        dst = chK["ST_GAS"] - chP["ST_GAS"]
        sub = dimp < IMPORT_DROP_MW
        # plant grain
        plants = []
        for code, p in K["plants"].items():
            ep = p["mod"] - p["act"]
            epP = P["plants"][code]["mod"] - P["plants"][code]["act"]
            plants.append({
                "code": code, "name": p["name"], "group": p["group"], "zone": p["zone"],
                "npl": p["npl"], "cov_share": _cov(ep, eK) / eK.var(),
                "d_cov": _cov(ep, eK) - _cov(epP, eP),
                "bias_mw": float(ep.mean()), "rmse_mw": float(np.sqrt(np.mean(ep**2))),
                "model_twh": float(p["mod"].sum() / 1e6), "actual_twh": float(p["act"].sum() / 1e6),
            })
        plants.sort(key=lambda d: -d["cov_share"])
        top5 = sum(d["cov_share"] for d in plants[:5])
        hodK = _by_hod(eK**2)
        res["years"][y] = {
            "keeper": {
                "r_nrmse": _fit(K["mod"], K["act"]), "mse": mseK, "var_e": float(eK.var()),
                "mean_e_mw": float(eK.mean()), "mean_act_mw": float(K["act"].mean()),
                "fill_mw": K["fill_mw"], "cogen_mw": K["cogen_mw"], "btm_mw": K["btm_mw"],
                "model_twh": K["model_twh"], "actual_twh": K["actual_twh"],
                "classes": clsK,
                "mse_by_hod": hodK,
                "hod_share_evening_17_21": float(sum(hodK[h] for h in EVENING) / 24 / mseK),
                "hod_share_midday_10_15": float(sum(hodK[h] for h in MIDDAY) / 24 / mseK),
                "mse_by_month": _by_month(eK**2),
                "month_share": [float(np.sum((eK**2)[MONTH_OF_HOUR == m]) / np.sum(eK**2)) for m in range(1, 13)],
                "top_class": max(clsK, key=lambda c: clsK[c]["mse_c_cov"]),
                "plants_top10": plants[:10],
                "top5_plant_cov_share": top5,
            },
            "prior": {
                "r_nrmse": _fit(P["mod"], P["act"]), "mse": mseP, "var_e": float(eP.var()),
                "mean_e_mw": float(eP.mean()), "classes": clsP,
                "top_class": max(clsP, key=lambda c: clsP[c]["mse_c_cov"]),
            },
            "delta": {
                "d_mse": d_mse,
                "d_nrmse_unrounded": float(np.sqrt(mseK) / K["act"].mean() - np.sqrt(mseP) / P["act"].mean()),
                "d_mse_by_class": {c: clsK[c]["mse_c_cov"] - clsP[c]["mse_c_cov"] for c in clsK if c in clsP},
                "d_mean2": float(eK.mean() ** 2 - eP.mean() ** 2),
                "d_mse_by_hod": _by_hod(d_e2),
                "d_mse_by_month": _by_month(d_e2),
                "d_mse_month_share": [float(np.sum(d_e2[MONTH_OF_HOUR == m]) / np.sum(d_e2)) for m in range(1, 13)],
                "d_mse_share_sep_nov": float(np.sum(d_e2[(MONTH_OF_HOUR >= 9) & (MONTH_OF_HOUR <= 11)]) / np.sum(d_e2)),
                "import_leg": {
                    "d_import_twh": float(dimp.sum() / 1e6), "d_cc_twh": float(dcc.sum() / 1e6),
                    "d_ct_twh": float(dct.sum() / 1e6), "d_stgas_twh": float(dst.sum() / 1e6),
                    "r_dcc_dimport": float(np.corrcoef(dcc, dimp)[0, 1]),
                    "r_dct_dimport": float(np.corrcoef(dct, dimp)[0, 1]),
                    "n_hours_import_drop_gt500": int(sub.sum()), "hour_share": float(sub.mean()),
                    "d_mse_share_in_subset": float(np.sum(d_e2[sub]) / np.sum(d_e2)),
                    "d_cc_mean_in_subset_mw": float(dcc[sub].mean()) if sub.any() else None,
                    "d_cc_mean_outside_mw": float(dcc[~sub].mean()),
                },
                "plants_top10_by_d_cov": sorted(plants, key=lambda d: -d["d_cov"])[:10],
            },
        }
    y25 = res["years"][2025]
    cc = y25["keeper"]["classes"]["CC_REGULAR"]
    dcls = y25["delta"]["d_mse_by_class"]
    dm = y25["delta"]["d_mse"]
    preds = {
        "P-1": res["g_repro"]["all_pass"],
        "P-2": 0.45 <= cc["share_of_var"] <= 0.75,
        "P-3": dcls["CC_REGULAR"] >= 0.60 * dm,
        "P-4": (y25["delta"]["import_leg"]["r_dcc_dimport"] <= -0.50
                and y25["delta"]["import_leg"]["d_mse_share_in_subset"] >= 0.50
                and y25["delta"]["import_leg"]["hour_share"] < 0.40),
        "P-5": y25["keeper"]["hod_share_evening_17_21"] >= 0.35 and y25["keeper"]["hod_share_midday_10_15"] <= 0.15,
        "P-6": 40.0 <= cc["bias_mw"] <= 150.0 and cc["bias2_share_of_own_mse"] < 0.25,
        "P-7": y25["delta"]["d_mse_share_sep_nov"] <= 0.40 and max(y25["keeper"]["month_share"]) <= 0.20,
        "P-8": all(res["years"][y]["keeper"]["top_class"] == "CC_REGULAR" for y in YEARS),
        "P-9": y25["keeper"]["top5_plant_cov_share"] >= 0.40,
        "P-10": all(res["years"][y]["delta"]["d_mse_by_class"]["CT_PEAKER"] < 0 for y in (2024, 2025)),
    }
    preds = {k: bool(v) for k, v in preds.items()}
    res["predictions"] = preds
    res["post_registration_extras"] = extras(fleets)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(json.dumps(res["g_repro"], indent=1))
    print("predictions", json.dumps(preds, indent=1))



# ---------------------------------------------------------------------------
# POST-REGISTRATION LEGS (labelled as such in the FINDING; none is scored).
# (h) the full diurnal error budget against EIA-930 — names the CC counterpart;
# (i) the measured-vs-model λ–hub spread by day-block — tests whether the
#     missing night/evening imports were ECONOMIC in the real market;
# (j) the CT_PEAKER plant ranking (object C's carrier);
# (k) the CEMS-basis monthly class table (the 2025 CC level over-run).
# ---------------------------------------------------------------------------
BLOCKS = {
    "night22-05": [22, 23, 0, 1, 2, 3, 4, 5],
    "morn06-08": [6, 7, 8],
    "day09-15": [9, 10, 11, 12, 13, 14, 15],
    "eve16-21": [16, 17, 18, 19, 20, 21],
}
# PNW_midC / DSW_CCGT delivery basis over the hub (spec.CAISO_IMPORT_DELIVERY_BASIS).
WHEEL = {"MALIN": (0.05, 5.0), "PALOVRDE": (0.03, 4.0)}
E930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"
LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
HUBS = REPO / "data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet"


def _model_hour(ts: pd.Series, year: int) -> np.ndarray:
    """caiso-168's non-leap 8760 mapping (Feb-29 dropped by the caller)."""
    dt = pd.DatetimeIndex(ts)
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    return (doy - 1) * 24 + dt.hour.to_numpy()


def _measured_930(year: int) -> dict[str, np.ndarray]:
    d = pd.read_parquet(E930)
    lt = pd.to_datetime(d["Local time"]) - pd.Timedelta(hours=1)  # hour-ending -> beginning
    d = d.assign(lt=lt)
    d = d[(d["lt"].dt.year == year) & ~((d["lt"].dt.month == 2) & (d["lt"].dt.day == 29))]
    h = _model_hour(d["lt"], year)
    out = {}
    for col, name in [("Demand", "demand"), ("Total interchange", "ti"), ("NG: SUN", "solar"),
                      ("NG: WND", "wind"), ("NG: WAT", "hydro"), ("NG: NUC", "nuclear"), ("NG: OTH", "oth")]:
        a = np.full(T, np.nan)
        a[h] = d[col].to_numpy(float)
        out[name] = a
    return out


def _hod(x: np.ndarray) -> list[float]:
    return [float(np.nanmean(x[HOD == h])) for h in range(24)]


def extras(fleets: dict) -> dict:
    out: dict = {}
    lmp = pd.read_parquet(LMP)
    hub = pd.read_parquet(HUBS)
    for y in YEARS:
        K = fleets[y][KEEPER]
        m = _measured_930(y)
        c = _class_hourly(BUNDLES[KEEPER], y)
        s = pd.read_parquet(BUNDLES[KEEPER] / f"hourly/storage_{y}.parquet")
        s = s[s["pass"] == "P1"]
        sn = (s.groupby("hour")["discharge_mw"].sum() - s.groupby("hour")["charge_mw"].sum()).reindex(range(T)).to_numpy()
        sysf = pd.read_parquet(BUNDLES[KEEPER] / f"hourly/system_{y}.parquet")
        sysf = sysf[sysf["pass"] == "P1"]
        D = sysf.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy()
        lam = ((sysf["price"] * sysf["demand"]).groupby(sysf["hour"]).sum() / sysf["demand"].groupby(sysf["hour"]).sum()).reindex(range(T)).to_numpy()
        zon = {z: g.set_index("hour")["price"].reindex(range(T)).to_numpy() for z, g in sysf.groupby("zone")}
        gasA = sum(p["act"] for p in K["plants"].values())
        gasM = sum(p["mod"] for p in K["plants"].values())
        budget = {
            "demand": (D, m["demand"]), "net_import": (c["import"], -m["ti"]),
            "solar": (c["solar"], m["solar"]), "wind": (c["wind"], m["wind"]),
            "hydro": (c["hydro"], m["hydro"]), "nuclear": (c["nuclear"], m["nuclear"]),
            "gas_cems_basis": (gasM, gasA),
        }
        out[y] = {
            "diurnal_budget_model_minus_measured_mw": {k: _hod(mm - aa) for k, (mm, aa) in budget.items()},
            "measured_net_import_hod": _hod(-m["ti"]), "model_import_hod": _hod(c["import"]),
            "model_storage_net_hod": _hod(sn), "measured_oth_930_hod": _hod(m["oth"]),
            "annual_twh": {k: [float(np.nansum(mm)) / 1e6, float(np.nansum(aa)) / 1e6] for k, (mm, aa) in budget.items()},
        }
        # (i) spread test
        ml = lmp[lmp["year"] == y].set_index("hour")
        da = ml["da"].reindex(range(T)).to_numpy(); rt = ml["rt"].reindex(range(T)).to_numpy()
        hh = {k: g.set_index("hour")["price"].reindex(range(T)).to_numpy() for k, g in hub[hub["year"] == y].groupby("hub")}
        sp = {}
        for hb, (pct, add) in WHEEL.items():
            deliv = hh[hb] * (1 + pct) + add
            zname = "NP15" if hb == "MALIN" else "SP15_rest"
            sp[hb] = {}
            for bn, hs in BLOCKS.items():
                sel = np.isin(HOD, hs) & ~np.isnan(hh[hb]) & ~np.isnan(da)
                sp[hb][bn] = {
                    "hub_mean": float(hh[hb][sel].mean()), "da_mean": float(da[sel].mean()),
                    "rt_mean": float(rt[sel].mean()), "lam_mean": float(lam[sel].mean()),
                    "da_minus_hub": float((da - hh[hb])[sel].mean()), "rt_minus_hub": float((rt - hh[hb])[sel].mean()),
                    "lam_minus_hub": float((lam - hh[hb])[sel].mean()), "zone_minus_hub": float((zon[zname] - hh[hb])[sel].mean()),
                    "share_da_gt_delivered": float((da > deliv)[sel].mean()), "share_rt_gt_delivered": float((rt > deliv)[sel].mean()),
                    "share_lam_gt_delivered": float((lam > deliv)[sel].mean()), "share_zone_gt_delivered": float((zon[zname] > deliv)[sel].mean()),
                    "n_hours": int(sel.sum()),
                }
        out[y]["spread_test"] = sp
        # (j) CT plant ranking; (k) monthly class table
        P = fleets[y][PRIOR]
        ct = []
        for code, p in K["plants"].items():
            if p["group"] != "CT_PEAKER":
                continue
            ct.append({"code": code, "name": p["name"], "zone": p["zone"], "npl": p["npl"],
                       "actual_twh": float(p["act"].sum() / 1e6), "keeper_twh": float(p["mod"].sum() / 1e6),
                       "prior_twh": float(P["plants"][code]["mod"].sum() / 1e6),
                       "actual_hod_mw": _hod(p["act"]), "hours_act_gt_half_npl": int((p["act"] > 0.5 * p["npl"]).sum())})
        ct.sort(key=lambda d: -d["actual_twh"])
        out[y]["ct_peaker_plants_by_actual"] = ct[:12]
        out[y]["ct_peaker_totals_twh"] = {"actual": sum(d["actual_twh"] for d in ct), "keeper": sum(d["keeper_twh"] for d in ct), "prior": sum(d["prior_twh"] for d in ct)}
        mon = {}
        for cls in ("CC_REGULAR", "CT_PEAKER"):
            ps = [p for p in K["plants"].values() if p["group"] == cls]
            a = sum(p["act"] for p in ps); mm = sum(p["mod"] for p in ps)
            mon[cls] = {"actual_gwh": [float(a[MONTH_OF_HOUR == i].sum() / 1e3) for i in range(1, 13)],
                        "keeper_gwh": [float(mm[MONTH_OF_HOUR == i].sum() / 1e3) for i in range(1, 13)]}
        out[y]["monthly_cems_basis"] = mon
    return out


if __name__ == "__main__":
    main()
