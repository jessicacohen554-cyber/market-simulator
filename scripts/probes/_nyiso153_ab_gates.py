#!/usr/bin/env python3
"""nyiso-153 — score ARM O (nyiso_incity_commitment_obligation) against PREREG-nyiso153.

Evaluates the pre-registered gates of
``results/calibration/PREREG-nyiso153-incity-obligation-2026-08-22.md`` on the
solved arm bundle plus its solve log — no solve, no LP. Control: the committed
keeper bundle ``nyiso152_armSE`` (`2026-08-22-nyiso-152-duty-complete`; no
control re-solve — zero solve-affecting commits since it solved, prereg §3).
The O-K5 criteria leg is recorded by the session from ``calibration_verdict``
on the registered run.

Writes ``results/calibration/_nyiso153_ab_gates.json``. Exit 0 whatever the
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
ARM = REPO / "results/calibration/nyiso153_armO"
OUT = REPO / "results/calibration/_nyiso153_ab_gates.json"

YEARS = (2023, 2024, 2025)
FLAG = "nyiso_incity_commitment_obligation"
FAMILIES = (("NYC", "nyc_10min_total"), ("Long_Island", "li_10min_total"))
SHORTFALL_BAR_H = 2000  # O-K3 REJECT branch threshold (prereg §4)
RHO = 0.301384269761953


def _meta(bundle: Path) -> dict:
    return json.loads((bundle / "meta.json").read_text())


def _diag(bundle: Path) -> dict:
    return json.loads((bundle / "legitimacy_diagnostics.json").read_text())


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


def _family_year(bundle: Path, year: int, fam: str) -> dict:
    rf = pd.read_parquet(bundle / "hourly" / f"reserve_family_{year}.parquet")
    rf = rf[(rf["pass"] == "P1") & (rf["family"] == fam)].sort_values("hour")
    short = rf["shortfall_mw"].to_numpy(dtype=float)
    dual = rf["dual"].to_numpy(dtype=float)
    return {
        "reserve_class": int(rf["reserve_class"].iloc[0]),
        "shortfall_hours": int((short > 1e-3).sum()),
        "shortfall_mwh": float(short.sum()),
        "dual_pos_hours": int((dual > 1e-6).sum()),
        "mean_dual_when_pos": (
            float(dual[dual > 1e-6].mean()) if (dual > 1e-6).any() else 0.0
        ),
        "held_p50_mw": float(np.percentile(rf["held_mw"].to_numpy(), 50)),
        "requirement_p50_mw": float(
            np.percentile(rf["requirement_mw"].to_numpy(), 50)
        ),
    }


def _inpocket_online_p50(bundle: Path, year: int, zone: str) -> float:
    uh = pd.read_parquet(
        bundle / "hourly" / f"unit_hourly_{year}.parquet",
        columns=["pass", "zone", "fuel", "plant_group", "hour", "mw"],
        filters=[("pass", "==", "P1"), ("zone", "==", zone)],
    )
    ob = uh[(uh["fuel"].isin(["gas_ct", "oil"])) | (uh["plant_group"] == "ST_GAS")]
    on_p = ob.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0)
    return float(np.percentile(on_p.to_numpy(), 50))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-log", type=Path, required=True)
    args = ap.parse_args()
    gates = [_k1(_meta(CONTROL), _meta(ARM), [FLAG], "O")]

    log_txt = args.arm_log.read_text()
    n_rho = log_txt.count("MEASURED online_rho=0.3014")
    cls_rows, cls_ok = {}, True
    for zone, fam in FAMILIES:
        for year in YEARS:
            a = _family_year(ARM, year, fam)
            c = _family_year(CONTROL, year, fam)
            cls_ok = cls_ok and a["reserve_class"] == 2 and c["reserve_class"] == 1
            cls_rows[f"{fam}_{year}"] = {"arm_class": a["reserve_class"],
                                         "ctl_class": c["reserve_class"]}
    gates.append({
        "gate": "O-K2 liveness (measured-rho log line every year; families "
                "re-classed 1 -> 2)",
        "rho_log_lines": n_rho,
        "classes": cls_rows,
        "passed": n_rho >= len(YEARS) and cls_ok,
    })

    k3_rows, reject_branch = [], False
    for zone, fam in FAMILIES:
        for year in YEARS:
            a = _family_year(ARM, year, fam)
            row = {
                "zone": zone, "family": fam, "year": year,
                "shortfall_hours": a["shortfall_hours"],
                "shortfall_mwh": round(a["shortfall_mwh"], 0),
                "dual_pos_hours": a["dual_pos_hours"],
                "mean_dual_when_pos": round(a["mean_dual_when_pos"], 2),
                "held_p50_mw": round(a["held_p50_mw"], 1),
                "requirement_p50_mw": round(a["requirement_p50_mw"], 1),
                "onlineP_p50_ctl": round(_inpocket_online_p50(CONTROL, year, zone), 0),
                "onlineP_p50_arm": round(_inpocket_online_p50(ARM, year, zone), 0),
            }
            if fam == "nyc_10min_total" and a["shortfall_hours"] >= SHORTFALL_BAR_H:
                reject_branch = True
            k3_rows.append(row)
    gates.append({
        "gate": f"O-K3 adjudication (REJECT branch iff nyc_10min_total "
                f"shortfall hours >= {SHORTFALL_BAR_H} in any year)",
        "rows": k3_rows,
        "branch": "REJECT" if reject_branch else "STRUCTURAL-PASS-CANDIDATE",
        "passed": None,  # a branch selector, not a pass/fail
    })
    gates.append(_k4(_diag(CONTROL), _diag(ARM), "O"))
    gates.append({"gate": "O-K5 gated criteria",
                  "note": "calibration_verdict.py on the registered arm",
                  "passed": None})

    result = {"session": "nyiso-153", "control": CONTROL.name,
              "arm": ARM.name, "gates": gates}
    print(f"--- ARM O ({result['arm']}) ---")
    for g in gates:
        state = {True: "PASS", False: "FAIL", None: "REPORTED"}[g["passed"]]
        print(f"{state:9s} {g['gate']}")
        if "branch" in g:
            print(f"          BRANCH: {g['branch']}")
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
