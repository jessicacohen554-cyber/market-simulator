"""caiso-256 rule-29 SCREEN scorer for the CT-only partition arm (2023 first).

Scores the UNREGISTERED screen bundle against the keeper's committed bundle
(G-CTRL form 4) on the gates registered in PRECOMMIT-caiso255 §7.2 and fixed
to numbers in ADDENDUM-caiso256-partition-screen §4-§5:

* S-1  RE-CHARTERED by owner ruling 2026-09-06 (ADDENDUM-caiso257-s1-recharter
       2026-09-06 sec 2): CT_PEAKER 2023 energy RISES by [87.2, 784.5] GWh --
       dE_DEDUP 261.5 GWh over 79 plants, factor 3 both ways. The superseded
       operand was the price-held-fixed tranche count dE_implied 935.5 GWh with
       band [311.8, 2,806.4], which over-counted 4.26x because sibling tranches
       of ONE plant whose bands all contain lambda were each charged their full
       pmax in the same hour (caiso-256 scored on it and the arm DIED there;
       that verdict stands and is not re-scored). The re-chartered operand
       charges at most ONE tranche's worth of MW per (plant, hour) -- a plant
       cannot displace its capacity twice in one hour -- and is adopted on THAT
       construction, never because it passes. Its own bias is LOW (a plant whose
       several tranches genuinely clear together displaces their SUM, not their
       max), so the two estimators bracket the truth and the factor of 3 is
       carried unchanged as the absorber. FAIL => the arm dies; NO third
       estimator (ADDENDUM-caiso257 sec 8.3).
* R-3  reproduction: the screen must reproduce caiso-256's CT_PEAKER
       +219.8 GWh (1.6447 -> 1.8645 TWh) within +/-5 GWh, else STOP -- the
       solve path drifted in a way the G-DRIFT identity measurement missed.
* S-2  nuclear / hydro / wind / solar each move < 0.5 % of keeper energy.
* S-3  C1 stop gate: arm class TWh vs the keeper _verdict.json C1 records'
       actual +/- tol; a PASS -> FAIL flip STOPS and ESCALATES.
* S-4  C4 stop gate: gas r / NRMSE via the caiso-252 construction on the
       committed bench part vs the HEAD-scored keeper 0.880 / 0.285; a flip
       (r < 0.70 or NRMSE > 0.30) STOPS and ESCALATES.
* preconditions (ADDENDUM §3): resolved seam cap = mic_partition 16,055 MW,
  hydro partition present, outage/tranche sha256 identical to the keeper's.

C3a is EXCLUDED both ways (reported only); neither C3a nor C4 promotes.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso256_screen2023.py \
        results/calibration/caiso256_screen2023 2023
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

KEEPER_ID = "2026-09-05-caiso-252-b1-notrim"
KEEPER = REPO / "results/calibration/caiso252_b1_notrim"
T = 8760
MD = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MOH = np.repeat(np.arange(1, 13), np.array(MD) * 24)
#: ADDENDUM-caiso257-s1-recharter §2.3, fixed before the artifact pair is
#: re-applied and before the solve. Owner ruling 2026-09-06.
S1_BAND_GWH = (87.2, 784.5)
#: ADDENDUM-caiso257 §4 R-3: caiso-256's measured 2023 rise, reproduced or STOP.
R3_REPRO_GWH = (219.8, 5.0)
S2_CLASSES = ("nuclear", "hydro", "wind", "solar")
S2_MAX_FRAC = 0.005
S4_R_MIN, S4_NRMSE_MAX = 0.70, 0.30
KEEPER_C4 = {2023: (0.880, 0.285), 2024: (0.909, 0.261), 2025: (0.877, 0.297)}
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
    arts = load_artifacts(KEEPER_ID)
    ybench = arts["bench"][year]
    kpay = arts["payload"]["years"][str(year)]
    kverdict = json.loads((KEEPER / "_verdict.json").read_text())

    pre = preconditions(bundle, year)
    ch, kch = class_hourly(bundle, year), class_hourly(KEEPER, year)
    twh = {k: float(ch[k].sum() / 1e6) for k in ch}
    ktwh = {k: float(kch[k].sum() / 1e6) for k in kch}

    # ---- S-1 ----
    d_ct_gwh = (twh["CT_PEAKER"] - ktwh["CT_PEAKER"]) * 1e3
    s1 = {
        "ct_peaker_twh": {"arm": twh["CT_PEAKER"], "keeper": ktwh["CT_PEAKER"]},
        "rise_gwh": d_ct_gwh,
        "band_gwh": S1_BAND_GWH,
        "pass": bool(S1_BAND_GWH[0] <= d_ct_gwh <= S1_BAND_GWH[1]),
    }
    # ---- R-3 (ADDENDUM-caiso257 sec 4): reproduce caiso-256's measured rise.
    # A STOP gate, not a tolerance to widen afterwards: the screen bundle
    # caiso-256 produced was deleted under rule 29(c), so this is the only
    # remaining check that the solve path at THIS head still gives that answer.
    # Scored only in the screen year the re-charter re-runs (2023).
    r3 = None
    if year == 2023:
        tgt, tol = R3_REPRO_GWH
        r3 = {
            "caiso256_rise_gwh": tgt,
            "measured_rise_gwh": round(d_ct_gwh, 3),
            "tol_gwh": tol,
            "abs_diff_gwh": round(abs(d_ct_gwh - tgt), 3),
            "pass": bool(abs(d_ct_gwh - tgt) <= tol),
        }
    # ---- S-2 ----
    s2 = {
        k: {
            "arm": twh.get(k),
            "keeper": ktwh.get(k),
            "frac": (abs(twh.get(k, 0) - ktwh.get(k, 0)) / ktwh[k])
            if ktwh.get(k)
            else None,
        }
        for k in S2_CLASSES
    }
    s2["pass"] = bool(
        all(
            v["frac"] is not None and v["frac"] < S2_MAX_FRAC
            for k, v in s2.items()
            if k in S2_CLASSES
        )
    )
    # ---- S-3: C1 from the keeper's verdict records (same tolerance) ----
    s3 = {"records": [], "flips": []}
    for r in kverdict["criteria"]["fuelmix"]["records"]:
        if r.get("year") != year or r.get("status") == "SKIPPED":
            continue
        m = re.search(r"= ±([0-9.]+) TWh", r.get("tol", ""))
        if not m or r.get("actual") is None:
            continue
        tol = float(m.group(1))
        k = r["key"]
        if k not in twh:
            continue
        ok_twh = abs(twh[k] - float(r["actual"])) <= tol
        rec = {
            "key": k,
            "actual": r["actual"],
            "keeper_model": r["model"],
            "arm_model": round(twh[k], 3),
            "tol_twh": tol,
            "keeper_status": r["status"],
            "arm_twh_pass": ok_twh,
        }
        s3["records"].append(rec)
        if r["status"] == "PASS" and not ok_twh:
            s3["flips"].append(k)
    s3["pass"] = not s3["flips"]
    # ---- S-4: C4 gas, the scorer's own construction ----
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
        "pass": bool(fit is not None and fit[0] >= S4_R_MIN and fit[1] <= S4_NRMSE_MAX),
    }
    # ---- reported, never gating ----
    s, ks = system(bundle, year), system(KEEPER, year)
    avg = ybench["avgLMP"]
    c3a = {
        "arm_lw": _lw(s),
        "keeper_lw": _lw(ks),
        "actual_rt_lw": avg["rt_lw"],
        "arm_pct": (_lw(s) / avg["rt_lw"] - 1) * 100,
        "keeper_pct": (_lw(ks) / avg["rt_lw"] - 1) * 100,
    }
    c3b = {
        "arm": _nrmse(_lw_mon(s), avg["rt_lw_mon"]),
        "keeper": _nrmse(_lw_mon(ks), avg["rt_lw_mon"]),
    }
    res = {
        "session": "caiso-257",
        "bundle": str(bundle.relative_to(REPO)),
        "year": year,
        "preconditions": pre,
        "R3_reproduction": r3,
        "S1": s1,
        "S2": s2,
        "S3_C1": s3,
        "S4_C4": s4,
        "reported": {
            "c3a_excluded": c3a,
            "c3b": c3b,
            "class_twh_arm_keeper": {
                k: [twh.get(k), ktwh.get(k)] for k in sorted(set(twh) | set(ktwh))
            },
        },
        "screen_clears": bool(
            pre["pass"]
            and (r3 is None or r3["pass"])
            and s1["pass"]
            and s2["pass"]
            and s3["pass"]
            and s4["pass"]
        ),
    }
    out = REPO / "results/calibration" / f"_caiso257_screen{year}.json"
    out.write_text(json.dumps(res, indent=1, default=float) + "\n")
    print("preconditions:", json.dumps(pre, default=float))
    print("R-3 reproduction:", json.dumps(r3, default=float))
    print("S1:", json.dumps(s1, default=float))
    print("S2:", json.dumps(s2, default=float))
    print(
        "S3 flips:",
        s3["flips"],
        [(r["key"], r["arm_model"], r["actual"], r["tol_twh"]) for r in s3["records"]],
    )
    print("S4:", json.dumps(s4, default=float))
    print(
        "C3a (excluded):",
        json.dumps(c3a, default=float),
        "C3b:",
        json.dumps(c3b, default=float),
    )
    print(
        "class TWh arm/keeper:",
        {
            k: [round(a or 0, 3), round(b or 0, 3)]
            for k, (a, b) in res["reported"]["class_twh_arm_keeper"].items()
        },
    )
    print("SCREEN CLEARS:", res["screen_clears"])


if __name__ == "__main__":
    main()
