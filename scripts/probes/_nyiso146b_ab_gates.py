#!/usr/bin/env python3
"""nyiso-146b — score the online-hours and reserve-duty arms against PREREG.

Evaluates the kill gates of
``results/calibration/PREREG-nyiso146b-online-hours-and-reserve-duty-2026-08-19.md``
on the committed bundles plus the arms' solve logs — no solve, no LP.
Arm B (``nyiso146b_online_arm``) and arm C (``nyiso146b_reserve_arm``) are
each ONE ``scenario_config`` field against the registered control
(``nyiso146_control``); the two are scored independently.

Writes ``results/calibration/_nyiso146b_ab_gates.json``. Exit 0 whatever the
verdict — this reports, it does not gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

CONTROL = REPO / "results/calibration/nyiso146_control"
ARM_B = REPO / "results/calibration/nyiso146b_online_arm"
ARM_C = REPO / "results/calibration/nyiso146b_reserve_arm"
YEARS = (2023, 2024, 2025)
BRIDGE = "nyiso_gas_commitment_bridge"
BRIDGE_MECH_CODE = 20
PHASE0 = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"
E923 = REPO / "data/raw/_processed-legacy/eia923_monthly_generation.parquet"
OUT = REPO / "results/calibration/_nyiso146b_ab_gates.json"

FLAG_B = "nyiso_gas_bridge_online_hours"
FLAG_C = "cc_reserve_duty_split"

# PREREG B-K2(a): capture-basis gas_cc leg predictions (TWh), ±5 %;
# gas_st held to the CONTROL SOLVE's own values ±2 %.
PRED_CC_LEG = {2023: 17.3213, 2024: 19.1247, 2025: 17.6596}
CTL_ST_LEG = {2023: 0.1109, 2024: 0.1544, 2025: 0.0965}

# PREREG C: the frozen cohort and the four object plants.
COHORT = (10620, 7784, 50744, 54593, 54592, 10621, 54034)
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

_LEG_RE = re.compile(
    r"NYISO gas bridge leg (\w+) \(min_load_frac [\d.]+, min_run [\w.]+\): "
    r"\d+ unit-hours floored, ([\d.]+) TWh floor volume"
)


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


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
    """Model P1 energy (GWh) for one plant from the bundle hourlies."""
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
    rec = json.loads(PHASE0.read_text())
    out = {}
    for p in rec["plants"]:
        for year, n in zip(YEARS, p.get("plant_runs_by_year") or []):
            out[(int(p["plant_code"]), year)] = int(n)
    return out


def _parse_leg_volumes(log: Path) -> dict[tuple[str, int], float]:
    vols = [(m.group(1), float(m.group(2))) for m in _LEG_RE.finditer(log.read_text())]
    per_fuel: dict[str, list[float]] = {}
    for fuel, v in vols:
        per_fuel.setdefault(fuel, []).append(v)
    out = {}
    for fuel, series in per_fuel.items():
        if len(series) != len(YEARS):
            raise SystemExit(f"{log}: expected {len(YEARS)} '{fuel}' lines")
        for year, v in zip(YEARS, series):
            out[(fuel, year)] = v
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


def _bridge_bind(diag: dict, code: int, year: int) -> float:
    return sum(
        float(r["floored_twh"])
        for r in diag["diagnostics"]["D4"]["rows"]
        if r.get("check") == "unit-conduct"
        and BRIDGE in str(r.get("floor", ""))
        and int(r["plant"]) == code
        and int(r["year"]) == year
    )


def _k1(mc: dict, ma: dict, flag: str) -> dict:
    provenance = {"timestamp", "note", "run_id", "git", "git_sha", "basis_sha",
                  "out_dir", "label"}
    diff = sorted(
        k for k in set(mc) | set(ma)
        if mc.get(k) != ma.get(k) and k not in provenance
    )
    return {
        "gate": f"K1 exactness ({flag})",
        "solve_field_diffs": diff,
        "passed": diff == [flag] and bool(ma.get(flag)) and not mc.get(flag),
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


def score_arm_b(arm_log: Path) -> list[dict]:
    mc, ma = _meta(CONTROL), _meta(ARM_B)
    dc, da = _diag(CONTROL), _diag(ARM_B)
    gates = [_k1(mc, ma, FLAG_B)]
    # B-K2(a)
    vols = _parse_leg_volumes(arm_log)
    legs, ok = [], True
    for year in YEARS:
        cc = vols.get(("gas_cc", year))
        st = vols.get(("gas_st", year))
        cc_ok = cc is not None and abs(cc - PRED_CC_LEG[year]) <= 0.05 * PRED_CC_LEG[year]
        st_ok = st is not None and abs(st - CTL_ST_LEG[year]) <= 0.02 * CTL_ST_LEG[year]
        ok = ok and cc_ok and st_ok
        legs.append({"year": year, "gas_cc": cc, "pred_cc": PRED_CC_LEG[year],
                     "cc_ok": cc_ok, "gas_st": st, "ctl_st": CTL_ST_LEG[year],
                     "st_ok": st_ok})
    corr = []
    for year in YEARS:
        for code in (2539, 57185):
            c, a = _bridge_bind(dc, code, year), _bridge_bind(da, code, year)
            rise = a > c
            ok = ok and rise
            corr.append({"year": year, "plant": code, "ctl": round(c, 4),
                         "arm": round(a, 4), "rises": rise})
    gates.append({"gate": "B-K2a floor delivery", "legs": legs,
                  "d4_corroboration": corr, "passed": ok})
    # B-K2(b) + B-K3
    metered = _metered_starts()
    beth, ok2b, ok3a = [], True, True
    for year in YEARS:
        c = _plant_starts(CONTROL, year, 2539)
        a = _plant_starts(ARM_B, year, 2539)
        drop = (c[0] - a[0]) / c[0] if c and c[0] else 0.0
        ok2b = ok2b and drop >= 0.60
        ok3a = ok3a and a[0] < c[0] and a[1] > c[1]
        beth.append({"year": year, "ctl": c[0], "arm": a[0],
                     "metered": metered.get((2539, year)),
                     "drop": round(drop, 3),
                     "ctl_med_h": c[1], "arm_med_h": a[1]})
    cohort, ok3b = [], True
    for code, year in NO_DEGRADE:
        c = _plant_starts(CONTROL, year, code)
        a = _plant_starts(ARM_B, year, code)
        m = metered.get((code, year))
        if c is None or a is None or m is None:
            cohort.append({"plant": code, "year": year, "skipped": True})
            continue
        ce, ae = abs(c[0] - m), abs(a[0] - m)
        hit = ae <= 1.5 * ce + 5
        ok3b = ok3b and hit
        cohort.append({"plant": code, "year": year, "metered": m, "ctl": c[0],
                       "arm": a[0], "ok": hit})
    flynn, ok3c = [], True
    for year in YEARS:
        c = _plant_starts(CONTROL, year, 7314)
        a = _plant_starts(ARM_B, year, 7314)
        hit = a[0] <= c[0]
        ok3c = ok3c and hit
        flynn.append({"year": year, "ctl": c[0], "arm": a[0],
                      "metered": metered.get((7314, year)), "ok": hit})
    gates.append({"gate": "B-K2b Bethlehem >=60% start fall", "years": beth,
                  "passed": ok2b})
    gates.append({"gate": "B-K3 object + no-degrade",
                  "legs": {"a_2539": ok3a, "b_cohort": ok3b, "c_flynn": ok3c},
                  "bethlehem": beth, "no_degrade": cohort, "flynn": flynn,
                  "passed": ok3a and ok3b and ok3c})
    gates.append(_k4(dc, da, "B"))
    gates.append({"gate": "B-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    return gates


def score_arm_c(arm_log: Path) -> list[dict]:
    mc, ma = _meta(CONTROL), _meta(ARM_C)
    dc, da = _diag(CONTROL), _diag(ARM_C)
    gates = [_k1(mc, ma, FLAG_C)]
    # C-K2: cohort armed + object-plant energy collapse
    log_txt = arm_log.read_text()
    armed = "cc_reserve_duty_split armed: 7 measured reserve-duty" in log_txt
    e923 = _e923_gwh()
    rows, ok = [], armed
    for code in OBJECT_PLANTS:
        for year in YEARS:
            c = _plant_energy(CONTROL, year, code)
            a = _plant_energy(ARM_C, year, code)
            act = e923.get((code, year))
            fall = (c - a) / c if c > 0 else 0.0
            gated = year in (2023, 2024)
            hit = (fall >= 0.80) if gated else None
            if gated:
                ok = ok and hit
            rows.append({"plant": code, "year": year, "ctl_gwh": round(c, 1),
                         "arm_gwh": round(a, 1), "e923_gwh": round(act, 1) if act else None,
                         "fall": round(fall, 3), "gated": gated, "ok": hit})
    gates.append({"gate": "C-K2 liveness (cohort armed + >=80% collapse)",
                  "cohort_log_line": armed, "object_plants": rows, "passed": ok})
    # C-K3 no-degrade (starts for non-cohort plants)
    metered = _metered_starts()
    cohort, ok3 = [], True
    for code, year in NO_DEGRADE + [(2539, y) for y in YEARS] + [(7314, y) for y in YEARS]:
        c = _plant_starts(CONTROL, year, code)
        a = _plant_starts(ARM_C, year, code)
        m = metered.get((code, year))
        if c is None or a is None or m is None:
            cohort.append({"plant": code, "year": year, "skipped": True})
            continue
        ce, ae = abs(c[0] - m), abs(a[0] - m)
        hit = ae <= 1.5 * ce + 5
        ok3 = ok3 and hit
        cohort.append({"plant": code, "year": year, "metered": m, "ctl": c[0],
                       "arm": a[0], "ok": hit})
    # Reported, not gated: Bethlehem's energy vs its EIA-923 net.
    beth_energy = [
        {"year": y, "ctl_gwh": round(_plant_energy(CONTROL, y, 2539), 1),
         "arm_gwh": round(_plant_energy(ARM_C, y, 2539), 1),
         "e923_gwh": round(e923.get((2539, y), 0.0), 1)}
        for y in YEARS
    ]
    gates.append({"gate": "C-K3 no-degrade", "rows": cohort,
                  "bethlehem_energy_reported": beth_energy, "passed": ok3})
    gates.append(_k4(dc, da, "C"))
    gates.append({"gate": "C-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arms",
                  "passed": None})
    return gates


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-b-log", type=Path, required=True)
    ap.add_argument("--arm-c-log", type=Path, required=True)
    args = ap.parse_args()
    result = {"session": "nyiso-146b", "control": CONTROL.name, "arms": {}}
    for tag, fn, log in (("B", score_arm_b, args.arm_b_log),
                         ("C", score_arm_c, args.arm_c_log)):
        gates = fn(log)
        result["arms"][tag] = gates
        print(f"--- ARM {tag} ---")
        for g in gates:
            state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
            print(f"{state:9s} {g['gate']}")
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
