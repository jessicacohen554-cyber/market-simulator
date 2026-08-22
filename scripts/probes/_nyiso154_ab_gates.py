#!/usr/bin/env python3
"""nyiso-154 — score ARM D (`nyiso_gas_bridge_da_horizon` → False) against PREREG-nyiso154.

Evaluates the pre-registered gates on the solved arm bundle plus its solve
log — no solve, no LP. Control: the committed keeper bundle `nyiso152_armSE`
(`2026-08-22-nyiso-152-duty-complete`; no re-solve, prereg §3). The D-K5
criteria leg is recorded by the session from ``calibration_verdict`` on the
registered run.

Writes ``results/calibration/_nyiso154_ab_gates.json``. Exit 0 whatever the
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

CONTROL = REPO / "results/calibration/nyiso152_armSE"
ARM = REPO / "results/calibration/nyiso154_armD"
MINRUN = REPO / "results/calibration/_nyiso146_perplant_minrun_phase0.json"
OUT = REPO / "results/calibration/_nyiso154_ab_gates.json"

YEARS = (2023, 2024, 2025)
FLAG = "nyiso_gas_bridge_da_horizon"
BETH = 2539
MECH_BRIDGE = 20
# D-K3 phase-0 capture bands (prereg §4): predicted ~33-34 / 8 / 23, ±50 %.
BANDS = {2023: (17, 51), 2024: (4, 12), 2025: (12, 35)}
CTL_STARTS = {2023: 45, 2024: 13, 2025: 28}
# The 146-convention no-degrade comparator set (metered-start plants).
TRACKED = (2539, 56234, 56196, 7314, 55405, 54574, 50292, 2500, 56940, 57185)


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


def _runs(flag: np.ndarray) -> list[tuple[int, int]]:
    idx = np.flatnonzero(np.diff(np.concatenate(([0], flag.astype(np.int8), [0]))) != 0)
    return list(zip(idx[0::2], idx[1::2]))


def _plant_starts(bundle: Path, year: int, code: int) -> int | None:
    df = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "plant_code", "unit_id", "hour", "mw", "cap_mw"],
        filters=[("plant_code", "==", code), ("pass", "==", "P1")],
    )
    if df.empty:
        return None
    g = df.groupby("hour")[["mw", "cap_mw"]].sum().sort_index()
    s = g["mw"].to_numpy()
    return len(_runs(s > 0.05 * g["cap_mw"].to_numpy().max()))


def _beth_floor(bundle: Path, year: int) -> dict:
    z = np.load(bundle / "floors" / f"{year}_P1.npz", allow_pickle=True)
    i = np.flatnonzero(z["plant_code"] == BETH)
    mg = z["min_gen"][i].astype(float).sum(axis=0)
    floored = mg > 0
    segs = [e - s0 for s0, e in _runs(floored)]
    return {
        "floored_hours": int(floored.sum()),
        "segments_gt24h": int(sum(1 for L in segs if L > 24)),
        "longest_segment_h": int(max(segs)) if segs else 0,
    }


def _metered() -> dict[tuple[int, int], int]:
    rec = json.loads(MINRUN.read_text())
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-log", type=Path)
    args = ap.parse_args()
    gates = []

    mc, ma = _meta(CONTROL), _meta(ARM)
    provenance = {"timestamp", "note", "run_id", "git", "git_sha", "basis_sha",
                  "out_dir", "label"}
    diff = sorted(
        k for k in set(mc) | set(ma)
        if mc.get(k) != ma.get(k) and k not in provenance
    )
    gates.append({
        "gate": "D-K1 exactness (nyiso_gas_bridge_da_horizon True/None -> False)",
        "solve_field_diffs": diff,
        "ctl_value": mc.get(FLAG),
        "arm_value": ma.get(FLAG),
        "passed": diff == [FLAG] and ma.get(FLAG) is False
        and mc.get(FLAG) in (None, True),
    })

    k2_rows, k2_ok = {}, True
    for year in YEARS:
        c, a = _beth_floor(CONTROL, year), _beth_floor(ARM, year)
        grew = a["floored_hours"] > c["floored_hours"]
        glued = a["segments_gt24h"] >= 1
        k2_ok = k2_ok and grew and glued
        k2_rows[str(year)] = {"ctl": c, "arm": a, "grew": grew}
    log_txt = args.arm_log.read_text() if args.arm_log else ""
    gates.append({
        "gate": "D-K2 liveness (Bethlehem glue fires; >24h floored segments)",
        "bethlehem_floor": k2_rows,
        "log_gt24h_bucket_lines": log_txt.count(">24h"),
        "passed": k2_ok,
    })

    metered = _metered()
    k3_rows, k3_band, k3_fall, nd_ok = [], True, True, True
    for year in YEARS:
        a = _plant_starts(ARM, year, BETH)
        lo, hi = BANDS[year]
        in_band = a is not None and lo <= a <= hi
        falls = a is not None and a < CTL_STARTS[year]
        k3_band, k3_fall = k3_band and in_band, k3_fall and falls
        k3_rows.append({"year": year, "ctl_starts": CTL_STARTS[year],
                        "arm_starts": a, "band": [lo, hi], "in_band": in_band,
                        "metered": metered.get((BETH, year))})
    nd_rows = []
    for code in TRACKED:
        for year in YEARS:
            m = metered.get((code, year))
            if m is None:
                continue
            c = _plant_starts(CONTROL, year, code)
            a = _plant_starts(ARM, year, code)
            if c is None or a is None:
                continue
            ok = abs(a - m) <= 1.5 * abs(c - m) + 5
            nd_ok = nd_ok and ok
            nd_rows.append({"plant": code, "year": year, "metered": m,
                            "ctl": c, "arm": a, "ok": ok})
    gates.append({
        "gate": "D-K3 capture band + falls + no-degrade harness",
        "bethlehem": k3_rows,
        "no_degrade": nd_rows,
        "passed": k3_band and k3_fall and nd_ok,
    })

    dc, da = _diag(CONTROL), _diag(ARM)
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
    gates.append({
        "gate": "D-K4 (K6-prime; the bridge D-2 rise is DECLARED)",
        "new_d4_failures": new_d4,
        "cleared_d4": sorted(fc - fa),
        "forced_share_rises": rises,
        "new_d1_misses": new_d1,
        "passed": (not new_d4) and (not new_d1),
    })
    gates.append({"gate": "D-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arm",
                  "passed": None})

    result = {"session": "nyiso-154", "control": CONTROL.name,
              "arm": ARM.name, "gates": gates}
    print(f"--- ARM D ({result['arm']}) ---")
    for g in gates:
        state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
        print(f"{state:9s} {g['gate']}")
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
