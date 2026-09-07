"""nyiso-212 — score the pre-registered rule-29 screen gates S-1..S-5 for the
``cc_summer_derate_reconciled_basis`` arm (``PREREG-nyiso212-summer-seam-screen.md`` §6).

Reads the ARM bundle (``--arm DIR``: ``run_config.json``, ``dispatch/<year>_P1.parquet``,
``calibration_verdict.py --json``) against the KEEPER's committed artifacts
(``results/calibration/nyiso202_startup_aware`` + the committed payload
``frontend/data/backcast/runs/2026-09-06-nyiso-202-startup-aware.js`` — G-CTRL
form 4) and the phase-0 record (``_nyiso212_arm_phase0.json``) for the ceiling
deltas. STOP gates only; every value is written to the record whatever the verdict.

Run::

    uv run python scripts/probes/nyiso212_screen_gates.py --arm results/calibration/_nyiso212_screen_2025 --year 2025
"""

from __future__ import annotations

import argparse
import json
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    sys.path.insert(0, str(p))

import nyiso212_overceiling_decomposition as D  # noqa: E402
import nyiso212_summer_seam_census as C  # noqa: E402
from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

FLAG = "cc_summer_derate_reconciled_basis"
KEEPER_DIR = ROOT / "results/calibration/nyiso202_startup_aware"
KEEPER_PAYLOAD = ROOT / "frontend/data/backcast/runs/2026-09-06-nyiso-202-startup-aware.js"
PHASE0 = ROOT / "results/calibration/_nyiso212_arm_phase0.json"
RECON = ROOT / "data/raw/_processed-legacy/cc_capacity_reconcile_NYISO.csv"
LOAD_BEARING = ("fuelmix", "sysvol", "price_mean", "price_shape")
PROTECTIVE = ("governance", "forced_share")
T = 8760


def verdict_json(bundle: Path) -> dict:
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts/calibration_verdict.py"), "--json", str(bundle)],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    ).stdout
    return json.loads(out[out.index("{") :])


def statuses(v: dict, year: int) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for cid, c in v["criteria"].items():
        out[cid] = {
            str(r.get("key")): r["status"] for r in c["records"] if r.get("year") == year
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    arm = Path(a.arm)
    year = a.year
    sm = C.summer_mask()
    recon = pd.read_csv(RECON)
    cap_plants = sorted(recon[recon["mode"] == "cap"].plant_code.astype(int))
    raise_plants = sorted(recon[recon["mode"] == "raise"].plant_code.astype(int))
    listed = cap_plants + raise_plants
    ph0 = json.load(open(PHASE0))["by_year"][str(year)]
    rec: dict = {"session": "nyiso-212", "arm": str(arm), "year": year, "gates": {}}

    # ---- S-1 recipe identity
    k_cfg = json.load(open(KEEPER_DIR / "run_config.json"))["scenario_config"]
    a_cfg = json.load(open(arm / "run_config.json"))["scenario_config"]
    diff = {k: (k_cfg.get(k), a_cfg.get(k)) for k in set(k_cfg) | set(a_cfg) if k_cfg.get(k) != a_cfg.get(k)}
    new_defaults = {k: v for k, v in diff.items() if k not in k_cfg}
    live = {k: v for k, v in diff.items() if k in k_cfg}
    s1 = set(live) == {FLAG} and a_cfg.get(FLAG) is True and not k_cfg.get(FLAG, False)
    rec["gates"]["S1"] = {
        "pass": bool(s1),
        "live_diff": live,
        "new_dataclass_defaults_reported_not_counted": new_defaults,
    }

    # ---- keeper 2025 per-plant summer / off-summer dispatch from the committed payload
    payload = decode_run_js(KEEPER_PAYLOAD.read_text())["years"][str(year)]["plants"]

    def keeper_plant(code: int) -> tuple[float, float, float]:
        e = payload.get(str(code)) or payload.get(f"{code}:CC_REGULAR")
        if e is None:
            return (np.nan, np.nan, np.nan)
        mm = e["m_mon"]
        return (float(e["m_ann"]) * 1e3, float(sum(mm[5:9])), float(sum(mm[:5]) + sum(mm[9:])))

    # ---- arm per-plant dispatch from its own P1 frame
    disp = pd.read_parquet(arm / "dispatch" / f"{year}_P1.parquet", columns=["plant_code", "klass", "hour", "mw"])
    disp = disp[disp.plant_code.isin(listed)]
    disp["summer"] = sm[disp.hour.to_numpy() % T]
    g = disp.groupby(["plant_code", "summer"]).mw.sum().unstack(fill_value=0.0) / 1e3  # GWh

    def arm_plant(code: int) -> tuple[float, float]:
        if code not in g.index:
            return (0.0, 0.0)
        return (float(g.loc[code].get(True, 0.0)), float(g.loc[code].get(False, 0.0)))

    per_plant = {}
    for code in listed:
        k_ann, k_sum, k_off = keeper_plant(code)
        a_sum, a_off = arm_plant(code)
        ceil = ph0["F2_per_plant"].get(str(code), {})
        per_plant[str(code)] = {
            "mode": "cap" if code in cap_plants else "raise",
            "keeper_summer_gwh": round(k_sum, 2),
            "arm_summer_gwh": round(a_sum, 2),
            "delta_summer_gwh": round(a_sum - k_sum, 2),
            "keeper_offsummer_gwh": round(k_off, 2),
            "arm_offsummer_gwh": round(a_off, 2),
            "delta_offsummer_gwh": round(a_off - k_off, 2),
            "ceiling_delta_summer_gwh": round(
                (ceil.get("summer_capability_on_mw", 0.0) - ceil.get("summer_capability_off_mw", 0.0)) * int(sm.sum()) / 1e3, 2
            )
            if ceil
            else None,
        }
    cv = per_plant["57185"]
    cv_ceiling_delta = ph0["F3_cricket_valley"]["summer_available_gwh_on"] - ph0["F3_cricket_valley"]["summer_available_gwh_off"]
    cap_delta = sum(per_plant[str(c)]["delta_summer_gwh"] for c in cap_plants)
    cap_ceiling_delta = sum((per_plant[str(c)]["ceiling_delta_summer_gwh"] or 0.0) for c in cap_plants)
    raise_ok = all(
        per_plant[str(c)]["delta_summer_gwh"] <= 0.01 * max(per_plant[str(c)]["keeper_summer_gwh"], 1e-9)
        for c in raise_plants
    )
    s2a = 0.0 < cv["delta_summer_gwh"] <= cv_ceiling_delta + 1e-6
    s2b = 0.0 < cap_delta <= cap_ceiling_delta + 1e-6
    rec["gates"]["S2"] = {
        "pass": bool(s2a and s2b and raise_ok),
        "a_57185": {"delta_summer_gwh": cv["delta_summer_gwh"], "bound_gwh": round(cv_ceiling_delta, 2), "pass": bool(s2a)},
        "b_cap_plants": {"delta_summer_gwh": round(cap_delta, 2), "bound_gwh": round(cap_ceiling_delta, 2), "pass": bool(s2b)},
        "c_raise_plants": {str(c): per_plant[str(c)]["delta_summer_gwh"] for c in raise_plants} | {"pass": bool(raise_ok)},
        "per_plant": per_plant,
    }

    # ---- S-3 footprint confinement: class annual energy, arm vs keeper (committed class_hourly)
    kh = pd.read_parquet(KEEPER_DIR / "hourly" / f"class_hourly_{year}.parquet")
    kh = kh[kh["pass"] == "P1"].groupby("klass").mw.sum() / 1e3
    ah_path = arm / "hourly" / f"class_hourly_{year}.parquet"
    if ah_path.exists():
        ah = pd.read_parquet(ah_path)
        ah = ah[ah["pass"] == "P1"].groupby("klass").mw.sum() / 1e3
    else:
        full = pd.read_parquet(arm / "dispatch" / f"{year}_P1.parquet", columns=["klass", "mw"])
        ah = full.groupby("klass").mw.sum() / 1e3
    classes = sorted(set(kh.index) | set(ah.index))
    class_delta = {k: round(float(ah.get(k, 0.0) - kh.get(k, 0.0)), 2) for k in classes}
    ccr = class_delta.get("CC_REGULAR", 0.0)
    s3 = 0.0 <= ccr <= ph0["class_available_energy_delta_gwh"].get("CC_REGULAR", 0.0) + 1e-6
    rec["gates"]["S3"] = {
        "pass": bool(s3),
        "cc_regular_delta_gwh": ccr,
        "bound_gwh": ph0["class_available_energy_delta_gwh"].get("CC_REGULAR"),
        "class_delta_gwh": class_delta,
        "sum_all_classes_delta_gwh": round(float(sum(class_delta.values())), 2),
        "offsummer_delta_15_plants_gwh": round(float(sum(per_plant[str(c)]["delta_offsummer_gwh"] for c in listed)), 2),
    }

    # ---- S-4 no non-target load-bearing PASS -> FAIL flip
    kv = verdict_json(KEEPER_DIR)
    av = verdict_json(arm)
    ks, as_ = statuses(kv, year), statuses(av, year)
    flips = []
    for cid in LOAD_BEARING + PROTECTIVE:
        for key, st in ks.get(cid, {}).items():
            if cid == "fuelmix" and key == "CC_REGULAR":
                continue  # target criterion — never gated
            new = as_.get(cid, {}).get(key)
            if st == "PASS" and new == "FAIL":
                flips.append((cid, key, st, new))
    changed = {
        cid: {k: (ks[cid].get(k), as_[cid].get(k)) for k in set(ks.get(cid, {})) | set(as_.get(cid, {})) if ks.get(cid, {}).get(k) != as_.get(cid, {}).get(k)}
        for cid in set(ks) | set(as_)
    }
    changed = {k: v for k, v in changed.items() if v}
    rec["gates"]["S4"] = {
        "pass": not flips and av["criteria"]["governance"]["status"] == "PASS",
        "flips_pass_to_fail": flips,
        "all_status_changes_2025": changed,
        "arm_determination": av["determination"],
        "keeper_determination": kv["determination"],
        "arm_grade": av["grade_summary"],
        "keeper_grade": kv["grade_summary"],
        "magnitudes_2025": {
            cid: {str(r.get("key")): (r.get("magnitude"), r["status"]) for r in av["criteria"][cid]["records"] if r.get("year") == year}
            for cid in ("price_mean", "price_shape", "price_tail", "forced_share", "fuelmix", "sysvol")
        },
    }

    # ---- S-5 the contradiction removed at 57185 in the screen year
    st_on = pickle.load(open(D.CACHE / f"arm_{year}_on.pkl", "rb"))
    U = st_on["units"]
    cvu = U[(U.plant == D.PLANT) & (U.group == "CC_REGULAR")]
    ceil = (st_on["avail"][cvu.i.to_numpy()] * cvu.pmax.to_numpy()[:, None]).sum(axis=0)
    meter = C.facility_gross(D.PLANT, year)
    cvd = pd.read_parquet(arm / "dispatch" / f"{year}_P1.parquet", columns=["plant_code", "hour", "mw"])
    cvd = cvd[cvd.plant_code == D.PLANT].groupby("hour").mw.sum().reindex(range(T), fill_value=0.0).to_numpy()
    months_over = [
        m + 1
        for m in range(12)
        if meter[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum() > ceil[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()
    ]
    rec["gates"]["S5"] = {
        "pass": bool(not months_over and (cvd <= ceil + 1e-3).all()),
        "months_meter_over_arm_ceiling": months_over,
        "max_dispatch_over_ceiling_mw": round(float((cvd - ceil).max()), 4),
        "arm_57185_month_gwh": [round(float(cvd[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()) / 1e3, 1) for m in range(12)],
        "meter_57185_month_gwh": [round(float(meter[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()) / 1e3, 1) for m in range(12)],
        "ceiling_57185_month_gwh": [round(float(ceil[D.MONTH_STARTS[m] : D.MONTH_STARTS[m + 1]].sum()) / 1e3, 1) for m in range(12)],
    }
    rec["verdict"] = "CLEARS" if all(g["pass"] for g in rec["gates"].values()) else "KILLED"
    dest = Path(a.out) if a.out else ROOT / f"results/calibration/_nyiso212_screen_gates_{year}.json"
    dest.write_text(json.dumps(rec, indent=1, default=str))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_plant"} for k, v in rec["gates"].items()}, indent=1, default=str))
    print("VERDICT:", rec["verdict"])


if __name__ == "__main__":
    main()
