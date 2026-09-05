"""caiso-252 rule-29 SCREEN scorer for the evening-trim disarm arm (2025 first).

Scores an UNREGISTERED screen bundle exactly the way the registered scorer
would, from the bundle's own on-disk artifacts and the committed bench part:

* C4 gas (G-OWNER): per-plant model series built the way
  ``render_calibration_html`` builds ``mw_pc`` / ``mplants`` (dispatch
  ``<year>_P1.parquet`` -> ``apply_other_fossil_scoring`` -> (plant, class)
  slices -> ``_b64(100 * mw / npl)`` with the CHP flat add-back), then
  ``calibration_verdict._cems_gas_hourly_fit`` on the committed bench part.
* G-FOOT / G-DIR / G-OVERSHOOT / G-NOBREAK (PRECOMMIT Addendum A §A.5) from the
  bundle's ``hourly/`` sidecars, the keeper's committed sidecars and EIA-930.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso252_screen2025.py \
        results/calibration/caiso252_arm_notrim 2025
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
_argv = list(sys.argv)
sys.argv = [sys.argv[0]]

from scripts.calibration_verdict import (  # noqa: E402
    GAS_CLASSES,
    _cems_gas_hourly_fit,
    _nrmse,
    load_artifacts,
)
from scripts.lib import bench_multiclass as bm  # noqa: E402
from market_sim.data.fleet import apply_other_fossil_scoring  # noqa: E402
from market_sim.config.plant_taxonomy import fossil_classes  # noqa: E402

KEEPER_ID = "2026-09-05-caiso-251-b1-nomargin"
KEEPER = REPO / "results/calibration/caiso251_arm_nomargin"
T = 8760
HOD = np.arange(T) % 24
EVE = np.isin(HOD, (18, 19, 20, 21))
MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MOH = np.repeat(np.arange(1, 13), np.array(MD) * 24)
E930 = REPO / "data/raw/eia-930-hourly/CISO hourly.parquet"


def _b64(cf: np.ndarray) -> str:
    a = np.clip(np.nan_to_num(cf), 0, 250).round().astype(np.uint8)
    return base64.b64encode(a[:T].tobytes()).decode()


def plant_series(bundle: Path, year: int, bplants: dict) -> dict[str, dict]:
    """Model per-plant CF% b64 keyed like the payload (render's construction)."""
    from market_sim.data.fleet import OTHER_FOSSIL_CLASS

    fossil = [*fossil_classes(), OTHER_FOSSIL_CLASS]
    p = bundle / "dispatch" / f"{year}_P1.parquet"
    disp = apply_other_fossil_scoring(pd.read_parquet(p), year, plant_col="plant_code")
    dm = disp[(disp["plant_code"] > 0) & (disp["klass"].isin(fossil))]
    mw_pc: dict[tuple[int, str], np.ndarray] = {}
    for (code, klass), g in dm.groupby(["plant_code", "klass"], observed=True):
        mw_pc[(int(code), str(klass))] = (
            g.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy(float)
        )
    classes_p: dict[int, list[str]] = {}
    for _code, _klass in mw_pc:
        classes_p.setdefault(_code, []).append(_klass)
    multi_p = {c: ks for c, ks in classes_p.items() if len(ks) > 1}
    out = {}
    for (code, klass), mw in mw_pc.items():
        key = bm.slice_key(code, klass if code in multi_p else None)
        bp = bplants.get(key)
        if bp is None:
            continue
        cap = float(bp.get("npl") or 0.0) or 1.0
        if klass in ("CC_CHP", "CT_CHP", "ST_CHP"):
            mw = mw + float(bp.get("btm") or 0.0) * 1e6 / T  # render's flat CHP add-back
        out[key] = {"m": _b64(100.0 * mw / cap), "mw": mw, "group": klass}
    return out


def class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    d = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    d = d[d["pass"] == "P1"]
    piv = d.pivot_table(index="hour", columns="klass", values="mw").reindex(range(T)).fillna(0.0)
    return {k: piv[k].to_numpy(float) for k in piv.columns}


def system(bundle: Path, year: int) -> pd.DataFrame:
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    return s[s["pass"] == "P1"]


def measured_net_import(year: int) -> np.ndarray:
    d = pd.read_parquet(E930)
    lt = pd.to_datetime(d["Local time"]) - pd.Timedelta(hours=1)
    d = d.assign(lt=lt)
    d = d[(d["lt"].dt.year == year) & ~((d["lt"].dt.month == 2) & (d["lt"].dt.day == 29))]
    dt = pd.DatetimeIndex(d["lt"])
    doy = dt.dayofyear.to_numpy()
    if year % 4 == 0:
        doy = np.where(dt.month.to_numpy() > 2, doy - 1, doy)
    h = (doy - 1) * 24 + dt.hour.to_numpy()
    a = np.full(T, np.nan)
    a[h] = -d["Total interchange"].to_numpy(float)
    return a


def row_energy(bundle: Path, year: int, uid_substr: str) -> np.ndarray | None:
    """Hourly MW of one LP row from the dispatch parquet, if it carries unit ids."""
    p = bundle / "dispatch" / f"{year}_P1.parquet"
    d = pd.read_parquet(p)
    col = next((c for c in ("unit_id", "uid", "unit", "name", "gen_id") if c in d.columns), None)
    if col is None:
        return None
    r = d[d[col].astype(str).str.contains(uid_substr)]
    if r.empty:
        return None
    return r.groupby("hour")["mw"].sum().reindex(range(T), fill_value=0.0).to_numpy(float)


def main() -> None:
    bundle = Path(_argv[1]).resolve()
    year = int(_argv[2])
    arts = load_artifacts(KEEPER_ID)
    ybench = arts["bench"][year]
    kpay = arts["payload"]["years"][str(year)]
    # ---- C4 gas, the scorer's own construction ----
    ps = plant_series(bundle, year, ybench["plants"])
    ch = class_hourly(bundle, year)
    gas_twh = float(sum(ch[k].sum() for k in GAS_CLASSES if k in ch) / 1e6)
    ypay = {"plants": {k: {"m": v["m"]} for k, v in ps.items()},
            "fuelRows": [{"fuel": "gas", "m": round(gas_twh, 2)}]}
    fit = _cems_gas_hourly_fit(ypay, ybench, ypay["fuelRows"][0]["m"])
    kfit = _cems_gas_hourly_fit(kpay, ybench, next(r["m"] for r in kpay["fuelRows"] if r["fuel"] == "gas"))
    # ---- CC diurnal error on the CEMS basis (arm vs keeper) ----
    def cls_err(plants_m: dict, grp: str) -> np.ndarray:
        e = np.zeros(T)
        for key, bp in ybench["plants"].items():
            if bp.get("group") != grp or bp.get("nodata") or not bp.get("campd"):
                continue
            pm = plants_m.get(key)
            if not pm or not pm.get("m"):
                continue
            sc = float(bp["npl"]) / 100.0
            a = np.frombuffer(base64.b64decode(bp["campd"]), dtype=np.uint8)[:T].astype(float) * sc
            m = np.frombuffer(base64.b64decode(pm["m"]), dtype=np.uint8)[:T].astype(float) * sc
            e += m - a
        return e
    e_cc_arm = cls_err(ypay["plants"], "CC_REGULAR"); e_cc_k = cls_err(kpay["plants"], "CC_REGULAR")
    e_ct_arm = cls_err(ypay["plants"], "CT_PEAKER"); e_ct_k = cls_err(kpay["plants"], "CT_PEAKER")
    # ---- gates from sidecars ----
    kch = class_hourly(KEEPER, year)
    meas = measured_net_import(year)
    imp_arm, imp_k = ch["import"], kch["import"]
    eve_meas = float(np.nansum(meas[EVE]) / 1e6)
    eve_arm = float(imp_arm[EVE].sum() / 1e6); eve_k = float(imp_k[EVE].sum() / 1e6)
    row_arm = row_energy(bundle, year, "DSW_daytime_clean")
    d_imp = imp_arm - imp_k
    added_in_eve_share = float(d_imp[EVE].sum() / d_imp[d_imp > 0].sum()) if (d_imp > 0).any() else None
    cc_eve_arm = float(ch["CC_REGULAR"][EVE].sum() / 1e6); cc_eve_k = float(kch["CC_REGULAR"][EVE].sum() / 1e6)
    ct_eve_arm = float(ch["CT_PEAKER"][EVE].sum() / 1e6); ct_eve_k = float(kch["CT_PEAKER"][EVE].sum() / 1e6)
    # C3a / C3b proxies
    s = system(bundle, year); ks = system(KEEPER, year)
    def lw(sf):
        return float((sf["price"] * sf["demand"]).sum() / sf["demand"].sum())
    def lw_mon(sf):
        sf = sf.assign(mo=MOH[sf["hour"].to_numpy()])
        g = sf.groupby("mo"); return [float((x["price"] * x["demand"]).sum() / x["demand"].sum()) for _, x in g]
    avg = ybench["avgLMP"]
    c3a_arm, c3a_k = lw(s), lw(ks)
    c3b_arm = _nrmse(lw_mon(s), avg["rt_lw_mon"]); c3b_k = _nrmse(lw_mon(ks), avg["rt_lw_mon"])
    # class energies vs keeper (C1 proxy: no class moves across the ±5.27 TWh floored band; 2025 rows are SKIPPED anyway)
    cls_twh = {k: [float(ch[k].sum() / 1e6), float(kch[k].sum() / 1e6)] for k in sorted(ch)}
    res = {
        "bundle": str(bundle), "year": year,
        "c4_gas_arm": fit, "c4_gas_keeper": kfit, "gas_twh_arm": gas_twh,
        "G_OWNER_pass": bool(fit is not None and fit[1] <= 0.30 and fit[0] >= 0.70),
        "cc_err_by_hod_arm": [float(e_cc_arm[HOD == h].mean()) for h in range(24)],
        "cc_err_by_hod_keeper": [float(e_cc_k[HOD == h].mean()) for h in range(24)],
        "ct_err_by_hod_arm": [float(e_ct_arm[HOD == h].mean()) for h in range(24)],
        "cc_err_22_23_delta_mw": float((e_cc_arm - e_cc_k)[np.isin(HOD, (22, 23))].mean()),
        "import_twh": [float(imp_arm.sum() / 1e6), float(imp_k.sum() / 1e6)],
        "import_by_hod_arm": [float(imp_arm[HOD == h].mean()) for h in range(24)],
        "import_by_hod_keeper": [float(imp_k[HOD == h].mean()) for h in range(24)],
        "measured_net_import_by_hod": [float(np.nanmean(meas[HOD == h])) for h in range(24)],
        "evening_18_21_twh": {"measured": eve_meas, "arm": eve_arm, "keeper": eve_k, "arm_minus_measured": eve_arm - eve_meas},
        "G_OVERSHOOT_pass": bool(-0.5 <= (eve_arm - eve_meas) <= 0.8),
        "d_import_added_share_in_18_21": added_in_eve_share,
        "row_daytime_clean_twh_arm": float(row_arm.sum() / 1e6) if row_arm is not None else None,
        "row_daytime_clean_by_hod_arm": [float(row_arm[HOD == h].mean()) for h in range(24)] if row_arm is not None else None,
        "cc_18_21_twh": {"arm": cc_eve_arm, "keeper": cc_eve_k, "delta": cc_eve_arm - cc_eve_k},
        "ct_18_21_twh": {"arm": ct_eve_arm, "keeper": ct_eve_k, "delta": ct_eve_arm - ct_eve_k},
        "G_DIR_pass": bool(((row_arm.sum() / 1e6 if row_arm is not None else d_imp[d_imp > 0].sum() / 1e6) >= 0.5) and cc_eve_arm < cc_eve_k),
        "c3a_lw": {"arm": c3a_arm, "keeper": c3a_k, "actual_rt_lw": avg["rt_lw"], "arm_pct": (c3a_arm / avg["rt_lw"] - 1) * 100, "keeper_pct": (c3a_k / avg["rt_lw"] - 1) * 100},
        "c3b_nrmse": {"arm": c3b_arm, "keeper": c3b_k},
        "G_NOBREAK_pass": bool(abs(c3a_arm / avg["rt_lw"] - 1) <= 0.10 and (c3b_arm is None or c3b_arm <= 0.20)),
        "class_twh_arm_keeper": cls_twh,
    }
    out = REPO / "results/calibration" / f"_caiso252_screen{year}.json"
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    for k, v in res.items():
        if not isinstance(v, list) and not isinstance(v, dict):
            print(f"{k}: {v}")
    print("evening_18_21_twh", res["evening_18_21_twh"]); print("cc_18_21", res["cc_18_21_twh"]); print("c3a", res["c3a_lw"]); print("c3b", res["c3b_nrmse"])
    print("cc err by hod arm   ", [round(x) for x in res["cc_err_by_hod_arm"]])
    print("cc err by hod keeper", [round(x) for x in res["cc_err_by_hod_keeper"]])
    print("import by hod arm   ", [round(x) for x in res["import_by_hod_arm"]])
    print("import by hod meas  ", [round(x) for x in res["measured_net_import_by_hod"]])


if __name__ == "__main__":
    main()
