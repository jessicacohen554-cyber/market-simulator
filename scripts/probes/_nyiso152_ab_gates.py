#!/usr/bin/env python3
"""nyiso-152 — score ARM SE (cc_reserve_duty_split + the bridge reserve-duty
membership exclusion) against PREREG-nyiso152.

Evaluates the pre-registered gates of
``results/calibration/PREREG-nyiso152-bridge-reserve-duty-exclusion-2026-08-22.md``
on the solved bundles plus the SE solve log — no solve, no LP. Control:
``nyiso152_control`` (the keeper recipe at the post-#4203-merge HEAD); the
committed ``nyiso151_armHC`` is the mid-rung isolating the exclusion. The K5
criteria leg is recorded by the session from ``calibration_verdict.py`` on
the registered runs.

Writes ``results/calibration/_nyiso152_ab_gates.json``. Exit 0 whatever the
verdict — this reports, it does not gate.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

IDENT_REF = REPO / "results/calibration/nyiso151_control"
CONTROL = REPO / "results/calibration/nyiso152_control"
ARM_SE = REPO / "results/calibration/nyiso152_armSE"
MIDRUNG = REPO / "results/calibration/nyiso151_armHC"
E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
OUT = REPO / "results/calibration/_nyiso152_ab_gates.json"

YEARS = (2023, 2024, 2025)
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
FLAG_S = "cc_reserve_duty_split"
FLAG_E = "nyiso_gas_bridge_reserve_duty_exclusions"
ALLEGANY = 7784
SPLIT_PLANTS = (50744, 54592, 54593)  # Sterling / Massena / Batavia
MECH_BRIDGE = 20  # MECH_NYISO_GAS_COMMITMENT_BRIDGE
# K3(ii) control-side capture: armHC's above-floor piece, predicted BEFORE the
# solve from the committed phase-0 record (_nyiso152_phase0.json), +/-50 %.
PREDICTED_GWH = {2023: 90.4, 2024: 111.8, 2025: 0.0}
BAND = 0.50


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))].copy()


def _plant_energy(bundle: Path, year: int, code: int) -> float:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    return float(df["mw"].sum()) / 1e3 if not df.empty else 0.0


def _allegany_floor(bundle: Path, year: int) -> dict:
    """Allegany's bridge-floor footprint from the bundle's floors npz."""
    z = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=True)
    i = np.flatnonzero(z["plant_code"] == ALLEGANY)
    if not len(i):
        return {"floored_hours": 0, "mech": [], "riding_gwh": 0.0}
    mg = z["min_gen"][i].astype(float).sum(axis=0)
    mech = sorted(set(z["mechanism"][i][:, mg > 0].ravel().tolist())) if (mg > 0).any() else []
    uh = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "hour", "mw"],
        filters=[("plant_code", "==", ALLEGANY), ("pass", "==", "P1")],
    )
    mw = uh.groupby("hour")["mw"].sum().sort_index().to_numpy(dtype=float)
    riding = (mg > 0) & (np.abs(mw - mg) <= 0.05)
    return {
        "floored_hours": int((mg > 0).sum()),
        "mech": [int(m) for m in mech if m],
        "riding_gwh": round(float(mw[riding].sum()) / 1e3, 1),
    }


def _e923_gwh() -> dict[tuple[int, int], float]:
    d = pd.read_parquet(E923)
    d = d[(d["ba_code"] == "NYIS") & (d["year"].isin(YEARS))]
    g = d.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()
    return {(int(p), int(y)): v / 1e3 for (p, y), v in g.items()}


def _d4_fails(diag: dict) -> set[tuple]:
    return {
        (int(r["year"]), str(r["floor"]), str(r["plant"]))
        for r in diag["diagnostics"]["D4"]["rows"]
        if str(r.get("verdict", "")).upper() == "FAIL"
    }


def _d2_shares(diag: dict) -> dict:
    return {
        (int(r["year"]), str(r["mechanism"]), str(r["class"])): float(
            r["share_of_class"]
        )
        for r in diag["diagnostics"]["D2"]["rows"]
    }


def _d1_miss(diag: dict) -> set:
    return {
        (int(r["year"]), str(r["class"]))
        for r in diag["diagnostics"]["D1"]["rows"]
        if str(r.get("verdict", "")).lower() not in ("pass", "exempt", "skip")
    }


def _k1(mc: dict, ma: dict, flags: list[str], tag: str) -> dict:
    provenance = {"timestamp", "note", "run_id", "git", "git_sha", "basis_sha",
                  "out_dir", "label"}
    diff = sorted(
        k for k in set(mc) | set(ma)
        if mc.get(k) != ma.get(k) and k not in provenance
    )
    return {
        "gate": f"{tag}-K1 exactness ({'+'.join(flags)})",
        "solve_field_diffs": diff,
        "passed": diff == sorted(flags)
        and all(bool(ma.get(f)) and not mc.get(f) for f in flags),
    }


def _k4(dc: dict, da: dict, tag: str) -> dict:
    fc, fa = _d4_fails(dc), _d4_fails(da)
    new_d4 = sorted(fa - fc)
    sc, sa = _d2_shares(dc), _d2_shares(da)
    rises = sorted(
        (
            {"key": list(k), "ctl": round(sc.get(k, 0.0), 4), "arm": round(v, 4)}
            for k, v in sa.items()
            if v > sc.get(k, 0.0) + 1e-6
        ),
        key=lambda r: r["key"],
    )
    new_d1 = sorted(_d1_miss(da) - _d1_miss(dc))
    escalated = bool(rises)
    return {
        "gate": f"{tag}-K4 D-4/D-2 (K6-prime)",
        "new_d4_failures": new_d4,
        "cleared_d4": sorted(fc - fa),
        "forced_share_rises": rises,
        "escalated": escalated,
        "new_d1_misses": new_d1,
        "passed": (not new_d4) and ((not escalated) or not new_d1),
    }


def ident_gate() -> dict:
    worst = 0.0
    for year in YEARS:
        a = _system(IDENT_REF, year).sort_values(["zone", "hour"])["price"].to_numpy()
        b = _system(CONTROL, year).sort_values(["zone", "hour"])["price"].to_numpy()
        worst = max(worst, float(np.abs(a - b).max()))
    return {"gate": "IDENT control == nyiso151_control == keeper (post-#4203 HEAD)",
            "max_abs_dprice": worst, "passed": worst == 0.0}


def score_arm_se(arm_log: Path) -> list[dict]:
    gates = [
        _k1(_meta(CONTROL), _meta(ARM_SE), [FLAG_S, FLAG_E], "SE"),
        _k1(_meta(MIDRUNG), _meta(ARM_SE), [FLAG_E], "SE-vs-armHC"),
    ]
    log_txt = arm_log.read_text()
    n_duty = log_txt.count("reserve-duty membership correction")
    named = log_txt.count("7784")
    floor_rows = {y: _allegany_floor(ARM_SE, y) for y in YEARS}
    k2_ok = (
        n_duty >= len(YEARS)
        and named >= len(YEARS)
        and all(r["floored_hours"] == 0 for r in floor_rows.values())
    )
    gates.append({
        "gate": "SE-K2 liveness (duty log line every year, 7784 named, "
                "Allegany bridge floor = 0)",
        "duty_log_lines": n_duty,
        "log_names_7784": named,
        "allegany_floor_by_year": {str(y): floor_rows[y] for y in YEARS},
        "passed": k2_ok,
    })

    e923 = _e923_gwh()
    k3_rows, k3i_ok, k3ii_ok = [], True, True
    for year in YEARS:
        c = _plant_energy(CONTROL, year, ALLEGANY)
        a = _plant_energy(ARM_SE, year, ALLEGANY)
        pred = PREDICTED_GWH[year]
        lo, hi = pred * (1 - BAND), pred * (1 + BAND)
        in_band = (a <= 1.0) if pred == 0.0 else (lo <= a <= hi)
        k3i = floor_rows[year]["riding_gwh"] == 0.0 and floor_rows[year]["floored_hours"] == 0
        k3i_ok, k3ii_ok = k3i_ok and k3i, k3ii_ok and in_band
        k3_rows.append({
            "year": year, "ctl_gwh": round(c, 1), "armSE_gwh": round(a, 1),
            "predicted_gwh": pred, "band": [round(lo, 1), round(hi, 1)],
            "in_band": in_band,
            "e923_gwh": round(e923.get((ALLEGANY, year), 0.0), 1),
            "fall_vs_ctl_pct_REPORTED": round(100 * (c - a) / c, 1) if c > 0 else None,
        })
    split_rows, k3iii_ok = [], True
    for code in SPLIT_PLANTS:
        for year in (2023, 2024):
            c = _plant_energy(CONTROL, year, code)
            a = _plant_energy(ARM_SE, year, code)
            fall = (c - a) / c if c > 0 else 0.0
            hit = fall >= 0.80
            k3iii_ok = k3iii_ok and hit
            split_rows.append({"plant": code, "year": year,
                               "ctl_gwh": round(c, 1), "armSE_gwh": round(a, 1),
                               "fall": round(fall, 3), "ok": hit})
    gates.append({
        "gate": "SE-K3 mechanism-scoped target (floor removed; total in "
                "predicted band; split collapses reproduce)",
        "allegany": k3_rows,
        "split_plants": split_rows,
        "note_80pct_headline": "REPORTED not gated (prereg SS4): the 150/151 "
                               ">=80% total-fall bar belonged to the "
                               "split-as-offer-lever arms; its rejections stand",
        "passed": k3i_ok and k3ii_ok and k3iii_ok,
    })
    gates.append(_k4(_diag(CONTROL), _diag(ARM_SE), "SE"))
    gates.append({"gate": "SE-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    return gates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-se-log", type=Path)
    ap.add_argument("--ident-only", action="store_true")
    args = ap.parse_args()
    result: dict = {"session": "nyiso-152", "control": CONTROL.name, "arms": {}}
    result["ident"] = ident_gate()
    print(f"{'PASS' if result['ident']['passed'] else 'FAIL':9s} IDENT "
          f"(max |dprice| {result['ident']['max_abs_dprice']})")
    if not args.ident_only and args.arm_se_log:
        gates = score_arm_se(args.arm_se_log)
        result["arms"]["SE"] = gates
        print("--- ARM SE ---")
        for g in gates:
            state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
            print(f"{state:9s} {g['gate']}")
    if OUT.exists():
        prior = json.loads(OUT.read_text())
        prior.update({k: v for k, v in result.items() if k != "arms"})
        prior.setdefault("arms", {}).update(result["arms"])
        result = prior
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
