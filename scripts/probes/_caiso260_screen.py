"""caiso-260 rule-29 SCREEN scorer for the demand-artifact vintage re-derive.

Scores the UNREGISTERED screen bundle against the caiso-257 keeper's committed
bundle (G-CTRL form 4) on the STOP-only gates registered in
PRECOMMIT-caiso260-demand-vintage-rederive-2026-09-06.md sec 3:

* preconditions (ADDENDUM-caiso257 sec 7): seam cap mic_partition, hydro
  partition present / flag off, outage + tranche sha256 identical;
* G-IDENT: the arm's summed CAISO-zone demand equals the regenerated artifact
  to < 1 MW every hour, and its difference from the keeper's demand is the
  artifact delta;
* G-FOOT: nuclear / wind / solar each move < 0.5 pct of keeper energy; hydro,
  storage, import and every gas class REPORTED;
* S-3 (C1 stop): no class PASS -> FAIL against the keeper _verdict.json records;
* S-3b (C3b stop): C3b NRMSE <= 0.20;
* S-4 (C4): gas r / NRMSE by the caiso-252 construction - REPORTED, EXCLUDED;
* C3a: EXCLUDED both ways, reported once.

Adapted from scripts/probes/_caiso256_screen2023.py (helpers verbatim), re-pointed
at the caiso-257 keeper.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso260_screen.py \
        results/calibration/caiso260_screen2025 2025
"""

from __future__ import annotations

import base64
import json
import re
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

KEEPER_ID = (
    "2026-09-06-caiso-260-b1-demand"  # re-pointed caiso-261 (caiso-257 pruned, rule 15)
)
KEEPER = REPO / "results/calibration/caiso260_demand_vintage"
ART_DIR = REPO / "data/raw/reference/caiso-supply-consistent-demand"
T = 8760
MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MOH = np.repeat(np.arange(1, 13), np.array(MD) * 24)
CAISO_ZONES = ("NP15", "ZP26", "SP15_rest", "LA_BASIN", "SDGE")
FOOT_CLASSES = ("nuclear", "wind", "solar")
FOOT_MAX_FRAC = 0.005
C3B_MAX = 0.20
S4_R_MIN, S4_NRMSE_MAX = 0.70, 0.30
KEEPER_C4 = {
    2023: (0.881, 0.287),
    2024: (0.912, 0.260),
    2025: (0.877, 0.298),
}  # caiso-260 keeper
SEAM_CAP = {2023: 16055.0, 2024: 16452.0, 2025: 16148.0}


def _b64(cf: np.ndarray) -> str:
    a = np.clip(np.nan_to_num(cf), 0, 250).round().astype(np.uint8)
    return base64.b64encode(a[:T].tobytes()).decode()


def plant_series(bundle: Path, year: int, bplants: dict) -> dict[str, dict]:
    """Model per-plant CF% b64 keyed like the payload (render's construction; caiso-252)."""
    from market_sim.data.fleet import OTHER_FOSSIL_CLASS

    fossil = [*fossil_classes(), OTHER_FOSSIL_CLASS]
    disp = apply_other_fossil_scoring(
        pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet"),
        year,
        plant_col="plant_code",
    )
    dm = disp[(disp["plant_code"] > 0) & (disp["klass"].isin(fossil))]
    mw_pc: dict[tuple[int, str], np.ndarray] = {}
    for (code, klass), g in dm.groupby(["plant_code", "klass"], observed=True):
        mw_pc[(int(code), str(klass))] = (
            g.groupby("hour")["mw"]
            .sum()
            .reindex(range(T), fill_value=0.0)
            .to_numpy(float)
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
            mw = mw + float(bp.get("btm") or 0.0) * 1e6 / T
        out[key] = {"m": _b64(100.0 * mw / cap), "mw": mw, "group": klass}
    return out


def class_hourly(bundle: Path, year: int) -> dict[str, np.ndarray]:
    d = pd.read_parquet(bundle / f"hourly/class_hourly_{year}.parquet")
    d = d[d["pass"] == "P1"]
    piv = (
        d.pivot_table(index="hour", columns="klass", values="mw")
        .reindex(range(T))
        .fillna(0.0)
    )
    return {k: piv[k].to_numpy(float) for k in piv.columns}


def system(bundle: Path, year: int) -> pd.DataFrame:
    s = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    return s[s["pass"] == "P1"]


def _lw(sf: pd.DataFrame) -> float:
    return float((sf["price"] * sf["demand"]).sum() / sf["demand"].sum())


def _lw_mon(sf: pd.DataFrame) -> list[float]:
    sf = sf.assign(mo=MOH[sf["hour"].to_numpy()])
    return [
        float((x["price"] * x["demand"]).sum() / x["demand"].sum())
        for _, x in sf.groupby("mo")
    ]


def preconditions(bundle: Path, year: int) -> dict:
    arm = json.loads((bundle / "run_config.json").read_text())["resolved_inputs"]
    kee = json.loads((KEEPER / "run_config.json").read_text())["resolved_inputs"]
    sc = arm["seam_import_cap"]["by_year"][str(year)]
    out = {
        "seam_cap": {
            "source": sc.get("source"),
            "cap_mw": sc.get("cap_mw"),
            "pass": sc.get("source") == "mic_partition"
            and abs(float(sc.get("cap_mw", 0)) - SEAM_CAP[year]) < 0.5,
        },
        "hydro_partition_present": {
            "arm": arm["hydro_plant_modes"].get("partition_present"),
            "flag_armed": arm["hydro_plant_modes"].get("flag_armed"),
            "pass": arm["hydro_plant_modes"].get("partition_present") is True
            and arm["hydro_plant_modes"].get("flag_armed") is False,
        },
    }
    for k in ("campd_unit_outages", "thermal_tranches"):
        out[k] = {
            "arm_sha": arm[k].get("sha256"),
            "keeper_sha": kee[k].get("sha256"),
            "pass": arm[k].get("sha256") == kee[k].get("sha256"),
        }
    out["pass"] = all(v["pass"] for v in out.values() if isinstance(v, dict))
    return out


def main() -> None:
    bundle = Path(_argv[1]).resolve()
    year = int(_argv[2])
    tag = _argv[3] if len(_argv) > 3 else ""
    arts = load_artifacts(KEEPER_ID)
    ybench = arts["bench"][year]
    kpay = arts["payload"]["years"][str(year)]
    kverdict = json.loads((KEEPER / "_verdict.json").read_text())

    pre = preconditions(bundle, year)
    ch, kch = class_hourly(bundle, year), class_hourly(KEEPER, year)
    twh = {k: float(ch[k].sum() / 1e6) for k in ch}
    ktwh = {k: float(kch[k].sum() / 1e6) for k in kch}
    s, ks = system(bundle, year), system(KEEPER, year)

    # ---- G-IDENT ----
    art = pd.read_csv(ART_DIR / f"caiso_supply_consistent_demand_{year}.csv")[
        "demand_mw"
    ].to_numpy(float)
    dem = (
        s[s["zone"].isin(CAISO_ZONES)]
        .groupby("hour")["demand"]
        .sum()
        .reindex(range(T))
        .to_numpy(float)
    )
    kdem = (
        ks[ks["zone"].isin(CAISO_ZONES)]
        .groupby("hour")["demand"]
        .sum()
        .reindex(range(T))
        .to_numpy(float)
    )
    g_ident = {
        "max_abs_arm_minus_artifact_mw": float(np.nanmax(np.abs(dem - art))),
        "arm_minus_keeper_annual_gwh": float((dem - kdem).sum() / 1e3),
        "arm_minus_keeper_max_abs_mw": float(np.nanmax(np.abs(dem - kdem))),
        "pass": bool(np.nanmax(np.abs(dem - art)) < 1.0),
    }
    # ---- G-FOOT ----
    foot = {
        k: {
            "arm": twh.get(k),
            "keeper": ktwh.get(k),
            "frac": (abs(twh.get(k, 0) - ktwh.get(k, 0)) / ktwh[k])
            if ktwh.get(k)
            else None,
        }
        for k in ch
    }
    foot["pass"] = bool(
        all(
            foot[k]["frac"] is not None and foot[k]["frac"] < FOOT_MAX_FRAC
            for k in FOOT_CLASSES
        )
    )
    st = pd.read_parquet(bundle / f"hourly/storage_{year}.parquet")
    st = st[st["pass"] == "P1"]
    kst = pd.read_parquet(KEEPER / f"hourly/storage_{year}.parquet")
    kst = kst[kst["pass"] == "P1"]
    foot["storage_discharge_twh"] = {
        "arm": float(st["discharge_mw"].sum() / 1e6),
        "keeper": float(kst["discharge_mw"].sum() / 1e6),
    }
    # ---- S-3: C1 flips from the keeper verdict records ----
    s3 = {"records": [], "flips": []}
    for r in kverdict["criteria"]["fuelmix"]["records"]:
        if r.get("year") != year or r.get("status") == "SKIPPED":
            continue
        m = re.search(r"= ±([0-9.]+) TWh", r.get("tol", ""))
        if not m or r.get("actual") is None or r["key"] not in twh:
            continue
        tol, k = float(m.group(1)), r["key"]
        ok = abs(twh[k] - float(r["actual"])) <= tol
        s3["records"].append(
            {
                "key": k,
                "actual": r["actual"],
                "keeper_model": r["model"],
                "arm_model": round(twh[k], 3),
                "tol_twh": tol,
                "keeper_status": r["status"],
                "arm_twh_pass": ok,
            }
        )
        if r["status"] == "PASS" and not ok:
            s3["flips"].append(k)
    s3["pass"] = not s3["flips"]
    # ---- S-3b: C3b ----
    avg = ybench["avgLMP"]
    c3b = {
        "arm": _nrmse(_lw_mon(s), avg["rt_lw_mon"]),
        "keeper": _nrmse(_lw_mon(ks), avg["rt_lw_mon"]),
    }
    c3b["pass"] = bool(c3b["arm"] <= C3B_MAX)
    # ---- S-4: C4 (reported, excluded) ----
    ps = plant_series(bundle, year, ybench["plants"])
    gas_twh = float(sum(ch[k].sum() for k in GAS_CLASSES if k in ch) / 1e6)
    ypay = {
        "plants": {k: {"m": v["m"]} for k, v in ps.items()},
        "fuelRows": [{"fuel": "gas", "m": round(gas_twh, 2)}],
    }
    fit = _cems_gas_hourly_fit(ypay, ybench, ypay["fuelRows"][0]["m"])
    kfit = _cems_gas_hourly_fit(
        kpay, ybench, next(r["m"] for r in kpay["fuelRows"] if r["fuel"] == "gas")
    )
    s4 = {
        "arm_r_nrmse": fit,
        "keeper_recomputed": kfit,
        "keeper_head_scored": KEEPER_C4[year],
        "within_band": bool(
            fit is not None and fit[0] >= S4_R_MIN and fit[1] <= S4_NRMSE_MAX
        ),
        "gating": False,
    }
    c3a = {
        "arm_lw": _lw(s),
        "keeper_lw": _lw(ks),
        "actual_rt_lw": avg["rt_lw"],
        "arm_pct": (_lw(s) / avg["rt_lw"] - 1) * 100,
        "keeper_pct": (_lw(ks) / avg["rt_lw"] - 1) * 100,
        "gating": False,
    }
    stop = bool(
        pre["pass"] and g_ident["pass"] and foot["pass"] and s3["pass"] and c3b["pass"]
    )
    res = {
        "session": "caiso-260",
        "bundle": str(bundle.relative_to(REPO)),
        "year": year,
        "preconditions": pre,
        "G_IDENT": g_ident,
        "G_FOOT": foot,
        "S3_c1": s3,
        "S3b_c3b": c3b,
        "S4_c4_reported": s4,
        "C3a_reported": c3a,
        "class_twh": {
            k: {"arm": twh[k], "keeper": ktwh.get(k), "delta": twh[k] - ktwh.get(k, 0)}
            for k in twh
        },
        "STOP_GATES_ALL_PASS": stop,
    }
    out = REPO / f"results/calibration/_caiso260_screen{year}{tag}.json"
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print(
        f"preconditions {pre['pass']} | G-IDENT {g_ident['pass']} (max|arm-art| {g_ident['max_abs_arm_minus_artifact_mw']:.3f} MW; arm-keeper {g_ident['arm_minus_keeper_annual_gwh']:+.1f} GWh) | G-FOOT {foot['pass']} | S-3 C1 flips {s3['flips']} | C3b {c3b['arm']:.4f} vs keeper {c3b['keeper']:.4f} pass {c3b['pass']}"
    )
    print(
        f"C4 (reported) arm {fit} keeper {kfit} head {KEEPER_C4[year]} | C3a (reported) arm {c3a['arm_pct']:+.2f} % keeper {c3a['keeper_pct']:+.2f} %"
    )
    for k, v in sorted(res["class_twh"].items(), key=lambda kv: -abs(kv[1]["delta"])):
        print(
            f"   {k:12s} arm {v['arm']:8.3f} keeper {v['keeper']:8.3f} delta {v['delta']:+8.3f} TWh"
        )
    print(f"storage discharge arm/keeper TWh {foot['storage_discharge_twh']}")
    print(f"STOP GATES ALL PASS: {stop} | wrote {out}")


if __name__ == "__main__":
    main()
