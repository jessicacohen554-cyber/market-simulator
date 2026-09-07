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
T = 8760


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
    # The keeper's run_config.json is the 2023-2025 bundle's record (weather_year
    # 2023, gas_price_override 2.54 = its first year); a one-year replay records
    # its own year. These two keys encode the --year selection, not the recipe.
    year_keys = {k: v for k, v in live.items() if k in ("weather_year", "gas_price_override")}
    recipe_live = {k: v for k, v in live.items() if k not in year_keys}
    s1_literal = set(live) == {FLAG}
    s1_recipe = set(recipe_live) == {FLAG} and a_cfg.get(FLAG) is True and not k_cfg.get(FLAG, False)
    rec["gates"]["S1"] = {
        "pass": bool(s1_literal),
        "pass_excluding_year_selection_keys": bool(s1_recipe),
        "live_diff": live,
        "year_selection_keys": year_keys,
        "recipe_diff_excluding_year_keys": recipe_live,
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
    # Sign-correct reading (from the phase-0 record committed BEFORE the PREREG):
    # a plant whose summer ceiling ROSE must satisfy 0 < delta <= ceiling delta,
    # one whose ceiling FELL must satisfy delta <= +1 % of its keeper summer.
    sign_correct = {}
    for c in raise_plants:
        pp = per_plant[str(c)]
        cd = pp["ceiling_delta_summer_gwh"] or 0.0
        if cd > 0:
            sign_correct[str(c)] = {"ceiling_rose_by_gwh": cd, "delta": pp["delta_summer_gwh"], "ok": bool(0.0 < pp["delta_summer_gwh"] <= cd + 1e-6)}
        else:
            sign_correct[str(c)] = {"ceiling_fell_by_gwh": cd, "delta": pp["delta_summer_gwh"], "ok": bool(pp["delta_summer_gwh"] <= 0.01 * max(pp["keeper_summer_gwh"], 1e-9))}
    rec["gates"]["S2"] = {
        "pass": bool(s2a and s2b and raise_ok),
        "c_raise_plants_sign_correct_reading_POST_HOC": sign_correct,
        "pass_under_sign_correct_reading": bool(s2a and s2b and all(v["ok"] for v in sign_correct.values())),
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

    # ---- S-4 no non-target load-bearing PASS -> FAIL flip.
    # An unregistered screen bundle has no sidecar, so calibration_verdict's
    # run-id path cannot score it. Score it the way nyiso-202 did: rebuild the
    # payload year-block the scorer reads from the bundle's OWN hourly parquets
    # (verified against the keeper: lmp.p / pMon are demand-weighted zone means,
    # d / dMon demand TWh, gmModel the class_hourly TWh -- all reproduce the
    # committed payload to the last digit) and call the same score_* functions
    # on keeper and arm. C8 (D-2 forced share) needs legitimacy_diagnostics.json,
    # which only the register path writes; it is REPORTED as not computable.
    import gzip

    import calibration_verdict as cv

    def year_block(bundle: Path, base: dict) -> dict:
        sysd = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        sysd = sysd[sysd["pass"] == "P1"]
        yb = json.loads(json.dumps(base))
        mon = np.searchsorted(D.MONTH_STARTS, np.arange(T), side="right") - 1
        for z, sub in sysd.groupby("zone"):
            sub = sub.sort_values("hour")
            pr, dm = sub.price.to_numpy(), sub.demand.to_numpy()
            mo = mon[sub.hour.to_numpy() % T]
            def _wm(x, w):
                # Demand-weighted mean; a zero-demand zone (the external node)
                # falls back to the simple mean, exactly as the committed payload
                # does (NYISO_external p 56.81 = simple mean, d 0.0).
                return float((x * w).sum() / w.sum()) if w.sum() > 0 else float(x.mean())

            yb["lmp"][z] = {
                "p": round(_wm(pr, dm), 2),
                "d": round(float(dm.sum() / 1e6), 4),
                "pMon": [round(_wm(pr[mo == k], dm[mo == k]), 2) for k in range(12)],
                "dMon": [round(float(dm[mo == k].sum() / 1e6), 4) for k in range(12)],
            }
        ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
        for k in list(yb["gmModel"]):
            yb["gmModel"][k] = round(float(ch.get(k, 0.0)), 4)
        return yb

    base = decode_run_js(KEEPER_PAYLOAD.read_text())["years"][str(year)]
    bench = json.load(gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{year}.json.gz"))["bench"]
    yk, ya = year_block(KEEPER_DIR, base), year_block(arm, base)
    rebuild_identity = {
        "lmp_p_max_abs_diff": max(abs(yk["lmp"][z]["p"] - base["lmp"][z]["p"]) for z in base["lmp"]),
        "lmp_pMon_max_abs_diff": max(abs(a - b) for z in base["lmp"] for a, b in zip(yk["lmp"][z]["pMon"], base["lmp"][z]["pMon"])),
        "gmModel_max_abs_diff": max(abs(yk["gmModel"][k] - base["gmModel"][k]) for k in base["gmModel"]),
        "zones_rebuilt_equal_payload_zones": sorted(yk["lmp"]) == sorted(base["lmp"]),
    }
    sc = {}
    for label, yb in (("keeper", yk), ("arm", ya)):
        sc[label] = {
            "C1": {r["key"]: (r["status"], r.get("magnitude")) for r in cv.score_fuelmix(year, yb, bench, "NYISO")},
            "C2": {r["key"]: (r["status"], r.get("magnitude")) for r in cv.score_sysvol(year, yb, bench, "NYISO")},
            "C3a": (lambda r: (r["status"], r.get("magnitude"), r.get("model"), r.get("actual")))(cv.score_price_mean(year, yb, bench)),
            "C3b": (lambda r: (r["status"], r.get("magnitude")))(cv.score_price_shape(year, yb, bench)),
        }
    flips = []
    for cid in ("C1", "C2"):
        for key, (st, _m) in sc["keeper"][cid].items():
            if cid == "C1" and key == "CC_REGULAR":
                continue  # target criterion -- never gated
            if st == "PASS" and sc["arm"][cid].get(key, ("?",))[0] == "FAIL":
                flips.append((cid, key))
    for cid in ("C3a", "C3b"):
        if sc["keeper"][cid][0] == "PASS" and sc["arm"][cid][0] == "FAIL":
            flips.append((cid, None))
    sysk = pd.read_parquet(KEEPER_DIR / "hourly" / f"system_{year}.parquet")
    sysa = pd.read_parquet(arm / "hourly" / f"system_{year}.parquet")

    def _tail(df):
        pv = df[df["pass"] == "P1"].pivot(index="hour", columns="zone", values="price")
        mx = pv.max(axis=1).to_numpy()
        return {"hours_max_zonal_gt_300": int((mx > 300).sum()), "system_mean": round(float(pv.mean(axis=1).mean()), 3)}

    rec["gates"]["S4"] = {
        "pass": not flips,
        "flips_pass_to_fail": flips,
        "scores": sc,
        "payload_rebuild_identity_vs_committed": rebuild_identity,
        "C3c_tail_reported": {"keeper": _tail(sysk), "arm": _tail(sysa)},
        "C8_forced_share": "NOT COMPUTABLE for an unregistered screen bundle (needs legitimacy_diagnostics.json, written only by the register path); the arm moves Jun-Sep availability at 15 CC_REGULAR plants and no floor, so the D-2 forced volume is untouched by construction -- REPORTED, and re-scored on the full-span bundle if the span is spent",
        "C6_governance": "attestation is written at registration; the arm is the keeper recipe plus one declared, default-off, zero-DOF construction flag (S-1)",
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
