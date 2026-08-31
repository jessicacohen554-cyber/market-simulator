"""miso-193 A/B scorer — the ``cc_duct_peaking_cap_pct=8.0`` cap arm.

Implements PREREG-miso193-cc-duct-peaking-cap-2026-08-31.md §4–§5 (control
``miso193_control_A``, arm ``miso193_cap_B``, keeper ``miso191_bax_B`` =
``2026-08-30-miso-191-bexit``):

* S-0 CONTROL INTEGRITY: every hourly sidecar of the control value-identical
  to the committed keeper's (drift is disclosed; A/B still scores
  control-vs-arm).
* S-1 SINGLE DELTA (KILL): the arm's ``scenario_config`` differs from the
  control's in exactly ``cc_duct_peaking_cap_pct: null -> 8.0``.
* S-2 CAPACITY-GRAIN LIVENESS (KILL, relational — miso-191 mis-freeze
  lesson): on each year's ``dispatch/<year>_P1_fleet.parquet``, per-plant CC
  peak-tranche MW (unit_id suffix ``peak``/``peakN``): (a) the total falls
  arm-vs-control in every year; (b) the fall is confined to duct-flagged
  plants with EIA-860 gap > 8 (any other CC plant's peak band moves ≤ 1 MW).
* K-1 (KILL): any criterion-year PASS -> FAIL flip vs the control.
* K-2 (KILL): arm C3b monthly NRMSE > 0.20 in any year.
* K-3 (KILL): any NEW D-4 conduct failure vs the control.
* K-4 (KILL, analytic): the cap is engineering-identified (F-class
  supplementary-firing max, the PJM-default constant) — no residual
  identification is introduced; the arm's DOF ledger on promotion records it
  as measured/engineering, n_residual stays 2.
* §5 PROMOTION: all kills silent AND adverse C3a face (arm-minus-control
  worsening) ≤ 1.5 pp in every year → PROMOTE; face exceeded → OWNER
  ESCALATION; kill fires → REJECT the cap leg.

Directional prereg (frozen in phase 0): C3a DOWN, confidence 0.8 — scored
and reported at full magnitude either way.

Record: ``results/calibration/_miso193_ab_gates.json``.

Run:
    python3 scripts/probes/_miso193_ab_gates.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso191_bax_B"
CONTROL = REPO / "results/calibration/miso193_control_A"
ARM = REPO / "results/calibration/miso193_cap_B"
OUT = REPO / "results/calibration/_miso193_ab_gates.json"
YEARS = (2023, 2024, 2025)
FIELD = "cc_duct_peaking_cap_pct"
ADVERSE_FACE_PP = 1.5
C3B_GATE = 0.20
CC_GROUPS = ("CC_REGULAR", "CC_CHP")
_UNIT_RE = re.compile(r"^(CC_REGULAR|CC_CHP)_.+_p(\d+)(?:_r\d{6})?_(.+)$")


def identity(control: Path, keeper: Path) -> dict:
    """S-0 — every hourly sidecar value-identical to the keeper's."""
    out: dict = {"gate": "S-0", "files": [], "passed": True}
    for path in sorted((keeper / "hourly").glob("*.parquet")):
        other = control / "hourly" / path.name
        rec: dict = {"file": path.name}
        if not other.exists():
            rec.update(present=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        a, b = pd.read_parquet(path), pd.read_parquet(other)
        if list(a.columns) != list(b.columns) or len(a) != len(b):
            rec.update(shape_match=False, passed=False)
            out["files"].append(rec)
            out["passed"] = False
            continue
        worst = 0.0
        nonnum_ok = True
        for col in a.columns:
            if pd.api.types.is_numeric_dtype(a[col]):
                d = np.abs(a[col].to_numpy(dtype=float) - b[col].to_numpy(dtype=float))
                worst = max(worst, float(np.nanmax(d)) if len(d) else 0.0)
            else:
                nonnum_ok &= bool(a[col].equals(b[col]))
        ok = worst == 0.0 and nonnum_ok
        rec.update(max_abs_diff=worst, nonnumeric_equal=nonnum_ok, passed=ok)
        out["files"].append(rec)
        out["passed"] = bool(out["passed"] and ok)
    return out


def s1_single_delta() -> dict:
    """S-1 — the scenario_config delta is exactly {FIELD: null -> 8.0}."""
    sc_a = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    sc_b = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    diffs = {
        k: (sc_a.get(k), sc_b.get(k))
        for k in set(sc_a) | set(sc_b)
        if sc_a.get(k) != sc_b.get(k)
    }
    ok = set(diffs) == {FIELD} and sc_a.get(FIELD) is None and sc_b.get(FIELD) == 8.0
    return {"gate": "S-1", "diffs": diffs, "passed": bool(ok)}


def _cc_peak_by_plant(bundle: Path, year: int) -> dict[int, float]:
    df = pd.read_parquet(bundle / "dispatch" / f"{year}_P1_fleet.parquet")
    out: dict[int, float] = {}
    for uid, pmax in zip(df["unit_id"].astype(str), df["pmax_mw"].astype(float)):
        m = _UNIT_RE.match(uid)
        if m and m.group(3).startswith("peak"):
            code = int(m.group(2))
            out[code] = out.get(code, 0.0) + pmax
    return out


def s2_liveness() -> dict:
    """S-2 — the cap clips peak-band MW, only on flagged gap>8 plants."""
    from market_sim.data.fleet.campd_bins import cc_duct_peaking_pct

    duct = cc_duct_peaking_pct()
    gt8 = {c for c, v in duct.items() if v is not None and v > 8.0}
    out: dict = {"gate": "S-2", "years": {}, "passed": True}
    for year in YEARS:
        pc = _cc_peak_by_plant(CONTROL, year)
        pa = _cc_peak_by_plant(ARM, year)
        codes = set(pc) | set(pa)
        fall = sum(pc.get(c, 0.0) - pa.get(c, 0.0) for c in codes)
        offenders = {
            c: round(pc.get(c, 0.0) - pa.get(c, 0.0), 2)
            for c in codes
            if c not in gt8 and abs(pc.get(c, 0.0) - pa.get(c, 0.0)) > 1.0
        }
        yr_ok = fall > 0.0 and not offenders
        out["years"][str(year)] = {
            "total_fall_mw": round(fall, 2),
            "clipped_plants": int(
                sum(1 for c in codes if c in gt8 and pc.get(c, 0.0) - pa.get(c, 0.0) > 1.0)
            ),
            "non_flagged_movers": offenders,
            "passed": bool(yr_ok),
        }
        out["passed"] = bool(out["passed"] and yr_ok)
    return out


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [
            sys.executable,
            str(REPO / "scripts" / "calibration_verdict.py"),
            "--json",
            str(bundle),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(
            f"calibration_verdict.py produced no JSON for {bundle}: {res.stderr[-800:]}"
        )
    return json.loads(res.stdout)


def _d4_fail_keys(bundle: Path) -> set[tuple]:
    led = json.loads((bundle / "legitimacy_diagnostics.json").read_text())
    out = set()
    for r in ((led.get("diagnostics") or {}).get("D4") or {}).get("rows", []) or []:
        if str(r.get("verdict", "pass")).lower() != "pass":
            out.add((r.get("year"), r.get("check"), r.get("floor"), r.get("plant")))
    return out


def _crit_status(verdict: dict) -> dict:
    out = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = (
                rec.get("status")
            )
    return out


def _c3a(verdict: dict) -> dict:
    out = {}
    for rec in verdict["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def _c3b_nrmse(verdict: dict) -> dict:
    out = {}
    for rec in verdict["criteria"]["price_shape"]["records"]:
        if rec.get("model") is not None:
            out[int(rec["year"])] = float(rec["model"])
    return out


def kills_and_scoring() -> dict:
    out: dict = {}
    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    sc, sa = _crit_status(vc), _crit_status(va)
    flips = {
        k: f"{sc.get(k)} -> {sa.get(k)}"
        for k in set(sc) | set(sa)
        if sc.get(k) != sa.get(k)
    }
    bad_flips = {
        k: v for k, v in flips.items() if sc.get(k) == "PASS" and sa.get(k) == "FAIL"
    }
    c3b_a = _c3b_nrmse(va)
    c3b_kill = {y: v for y, v in c3b_a.items() if v > C3B_GATE}
    d4_c, d4_a = _d4_fail_keys(CONTROL), _d4_fail_keys(ARM)
    new_d4 = sorted(map(list, d4_a - d4_c))
    c3a_c, c3a_a = _c3a(vc), _c3a(va)
    # Adverse worsening per year: movement away from actual (|err| grows).
    face = {
        y: round(abs(c3a_a.get(y, 0.0)) - abs(c3a_c.get(y, 0.0)), 4)
        for y in YEARS
        if y in c3a_c and y in c3a_a
    }
    out["K1"] = {"pass_to_fail_flips": bad_flips, "all_flips": flips,
                 "passed": not bad_flips}
    out["K2"] = {"c3b_arm_nrmse": c3b_a, "c3b_control_nrmse": _c3b_nrmse(vc),
                 "over_gate": c3b_kill, "passed": not c3b_kill}
    out["K3"] = {"d4_fail_control": sorted(map(list, d4_c)),
                 "d4_fail_arm": sorted(map(list, d4_a)),
                 "new_d4_fails": new_d4, "passed": not new_d4}
    out["K4"] = {
        "note": "cap identified from engineering practice (F-class supplementary-"
        "firing max; the PJM-default constant) — no residual identification; "
        "n_residual stays 2 on the promotion attestation",
        "passed": True,
    }
    out["scoring"] = {
        "c3a_control_pct": {y: round(v, 4) for y, v in c3a_c.items()},
        "c3a_arm_pct": {y: round(v, 4) for y, v in c3a_a.items()},
        "c3a_adverse_face_pp": face,
        "direction_prediction": "DOWN (conf 0.8, frozen in phase 0)",
        "direction_observed": {
            y: ("DOWN" if c3a_a[y] < c3a_c[y] else "UP" if c3a_a[y] > c3a_c[y] else "FLAT")
            for y in face
        },
        "determination_control": vc.get("determination"),
        "determination_arm": va.get("determination"),
    }
    out["_face_exceeded"] = any(v > ADVERSE_FACE_PP for v in face.values())
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso193-cc-duct-peaking-cap-2026-08-31.md §4-§5",
        "keeper": "2026-08-30-miso-191-bexit",
        "control": CONTROL.name,
        "arm": ARM.name,
    }
    out["S0"] = identity(CONTROL, KEEPER)
    print("S-0", "PASS" if out["S0"]["passed"] else "FAIL (disclosed, not a kill)",
          flush=True)
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else "FAIL", out["S1"]["diffs"] or "",
          flush=True)
    out["S2"] = s2_liveness()
    print("S-2", "PASS" if out["S2"]["passed"] else "FAIL",
          {y: v["total_fall_mw"] for y, v in out["S2"]["years"].items()}, flush=True)
    out.update(kills_and_scoring())
    for k in ("K1", "K2", "K3", "K4"):
        print(k, "PASS" if out[k]["passed"] else "KILL", flush=True)
    print("scoring", json.dumps(out["scoring"], indent=1), flush=True)
    kills_silent = all(out[k]["passed"] for k in ("K1", "K2", "K3", "K4"))
    if not (out["S1"]["passed"] and out["S2"]["passed"] and kills_silent):
        out["verdict"] = "REJECT (kill gate failed)"
    elif out["_face_exceeded"]:
        out["verdict"] = (
            "GATES SILENT; ADVERSE FACE EXCEEDED (>1.5 pp) -> OWNER ESCALATION, "
            "no self-promotion"
        )
    else:
        out["verdict"] = "PROMOTE per PREREG-miso193 §5 (all gates clean, face in bound)"
    print("VERDICT:", out["verdict"], flush=True)
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
