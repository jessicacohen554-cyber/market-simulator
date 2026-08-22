#!/usr/bin/env python3
"""nyiso-151 — score ARM H (egrid_identity_heat_rates) and ARM HC (repair +
cc_reserve_duty_split re-gate) against PREREG-nyiso151.

Evaluates the kill gates of
``results/calibration/PREREG-nyiso151-egrid-identity-hr-and-regate-2026-08-22.md``
on the solved bundles plus the arms' solve logs — no solve, no LP. Control:
``nyiso151_control`` (the keeper recipe at the post-merge HEAD; Amendment 1).
The H-K5 / HC-K5 criteria legs are recorded by the session from
``calibration_verdict.py`` on the registered runs.

Writes ``results/calibration/_nyiso151_ab_gates.json``. Exit 0 whatever the
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

KEEPER = REPO / "results/calibration/nyiso149_armF"
CONTROL = REPO / "results/calibration/nyiso151_control"
ARM_H = REPO / "results/calibration/nyiso151_armH"
ARM_HC = REPO / "results/calibration/nyiso151_armHC"
E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
PHASE0_MINRUN = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"
OUT = REPO / "results/calibration/_nyiso151_ab_gates.json"

YEARS = (2023, 2024, 2025)
ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]
FLAG_H = "egrid_identity_heat_rates"
FLAG_C = "cc_reserve_duty_split"
ALLEGANY = 7784
OBJECT_PLANTS = (50744, 54592, 54593, 7784)
NO_DEGRADE = (
    [(56940, y) for y in YEARS]
    + [(55405, y) for y in YEARS]
    + [(56196, y) for y in YEARS]
    + [(2511, y) for y in YEARS]
    + [(2500, y) for y in YEARS]
    + [(50292, y) for y in YEARS]
    + [(57185, 2024), (57185, 2025), (56234, 2024), (56234, 2025)]
)


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _system(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return df[(df["pass"] == "P1") & (df["zone"].isin(ZONES))].copy()


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _plant_starts(bundle: Path, year: int, code: int) -> tuple[int, float] | None:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "unit_id", "hour", "mw", "cap_mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    if df.empty:
        return None
    cap = float(df.groupby("unit_id")["cap_mw"].max().sum())
    s = df.groupby("hour")["mw"].sum().sort_index().to_numpy()
    on = s > 0.05 * cap
    r = _runs(on)
    lens = [e - s0 for s0, e in r]
    return len(r), (float(np.median(lens)) if lens else 0.0)


def _plant_energy(bundle: Path, year: int, code: int) -> float:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    return float(df["mw"].sum()) / 1e3 if not df.empty else 0.0


def _e923_gwh() -> dict[tuple[int, int], float]:
    d = pd.read_parquet(E923)
    d = d[(d["ba_code"] == "NYIS") & (d["year"].isin(YEARS))]
    g = d.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()
    return {(int(p), int(y)): v / 1e3 for (p, y), v in g.items()}


def _metered_starts() -> dict[tuple[int, int], int]:
    rec = json.loads(PHASE0_MINRUN.read_text())
    out = {}
    for p in rec["plants"]:
        for year, n in zip(YEARS, p.get("plant_runs_by_year") or []):
            out[(int(p["plant_code"]), year)] = int(n)
    return out


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
        a = _system(KEEPER, year).sort_values(["zone", "hour"])["price"].to_numpy()
        b = _system(CONTROL, year).sort_values(["zone", "hour"])["price"].to_numpy()
        worst = max(worst, float(np.abs(a - b).max()))
    return {"gate": "IDENT control == keeper (post-merge HEAD)",
            "max_abs_dprice": worst, "passed": worst == 0.0}


def _no_degrade(arm: Path) -> tuple[list[dict], bool]:
    metered = _metered_starts()
    rows, ok = [], True
    for code, year in NO_DEGRADE + [(2539, y) for y in YEARS] + [(7314, y) for y in YEARS]:
        c = _plant_starts(CONTROL, year, code)
        a = _plant_starts(arm, year, code)
        m = metered.get((code, year))
        if c is None or a is None or m is None:
            rows.append({"plant": code, "year": year, "skipped": True})
            continue
        hit = abs(a[0] - m) <= 1.5 * abs(c[0] - m) + 5
        ok = ok and hit
        rows.append({"plant": code, "year": year, "metered": m, "ctl": c[0],
                     "arm": a[0], "ok": hit})
    return rows, ok


def score_arm_h(arm_log: Path) -> list[dict]:
    gates = [_k1(_meta(CONTROL), _meta(ARM_H), [FLAG_H], "H")]
    log_txt = arm_log.read_text()
    n_apply = log_txt.count(
        "eGRID identity-reconciled heat rates applied to 2 generator(s)"
    )
    gates.append({"gate": "H-K2 construction (apply line every year)",
                  "apply_lines": n_apply, "passed": n_apply >= len(YEARS)})
    e923 = _e923_gwh()
    rows, ok = [], True
    for year in YEARS:
        c = _plant_energy(CONTROL, year, ALLEGANY)
        a = _plant_energy(ARM_H, year, ALLEGANY)
        hit = a < c
        ok = ok and hit
        rows.append({"year": year, "ctl_gwh": round(c, 1), "arm_gwh": round(a, 1),
                     "e923_gwh": round(e923.get((ALLEGANY, year), 0.0), 1),
                     "falls": hit})
    nd_rows, nd_ok = _no_degrade(ARM_H)
    gates.append({"gate": "H-K3 Allegany energy falls each year + no-degrade",
                  "allegany": rows, "no_degrade_ok": nd_ok,
                  "no_degrade": nd_rows, "passed": ok and nd_ok})
    gates.append(_k4(_diag(CONTROL), _diag(ARM_H), "H"))
    gates.append({"gate": "H-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    gates.append({"gate": "H-K6 LOYO (derive-side in artifact; gate-side = per-year H-K3)",
                  "passed": ok})
    return gates


def score_arm_hc(arm_log: Path) -> list[dict]:
    gates = [_k1(_meta(CONTROL), _meta(ARM_HC), [FLAG_H, FLAG_C], "HC")]
    gates.append(_k1(_meta(ARM_H), _meta(ARM_HC), [FLAG_C], "HC-vs-H"))
    log_txt = arm_log.read_text()
    armed = "cc_reserve_duty_split armed: 7 measured reserve-duty" in log_txt
    e923 = _e923_gwh()
    rows, ok = [], armed
    for code in OBJECT_PLANTS:
        for year in YEARS:
            c = _plant_energy(CONTROL, year, code)
            a = _plant_energy(ARM_HC, year, code)
            h = _plant_energy(ARM_H, year, code)
            act = e923.get((code, year))
            fall = (c - a) / c if c > 0 else 0.0
            gated = year in (2023, 2024)
            hit = (fall >= 0.80) if gated else None
            if gated:
                ok = ok and bool(hit)
            rows.append({"plant": code, "year": year, "ctl_gwh": round(c, 1),
                         "armH_gwh": round(h, 1), "armHC_gwh": round(a, 1),
                         "e923_gwh": round(act, 1) if act else None,
                         "fall_vs_ctl": round(fall, 3), "gated": gated, "ok": hit})
    gates.append({"gate": "HC-K2 liveness (cohort armed + >=80% collapse incl. 7784)",
                  "cohort_log_line": armed, "object_plants": rows, "passed": ok})
    nd_rows, nd_ok = _no_degrade(ARM_HC)
    gates.append({"gate": "HC-K3 no-degrade", "rows": nd_rows, "passed": nd_ok})
    gates.append(_k4(_diag(CONTROL), _diag(ARM_HC), "HC"))
    gates.append({"gate": "HC-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    per_year = all(r["ok"] for r in rows if r["gated"])
    gates.append({"gate": "HC-K6 LOYO (gate-side: HC-K2 per-year)",
                  "passed": per_year})
    return gates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-h-log", type=Path)
    ap.add_argument("--arm-hc-log", type=Path)
    ap.add_argument("--ident-only", action="store_true")
    args = ap.parse_args()
    result: dict = {"session": "nyiso-151", "control": CONTROL.name, "arms": {}}
    result["ident"] = ident_gate()
    print(f"{'PASS' if result['ident']['passed'] else 'FAIL':9s} IDENT "
          f"(max |dprice| {result['ident']['max_abs_dprice']})")
    if not args.ident_only:
        if args.arm_h_log:
            gates = score_arm_h(args.arm_h_log)
            result["arms"]["H"] = gates
            print("--- ARM H ---")
            for g in gates:
                state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
                print(f"{state:9s} {g['gate']}")
        if args.arm_hc_log:
            gates = score_arm_hc(args.arm_hc_log)
            result["arms"]["HC"] = gates
            print("--- ARM HC ---")
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
