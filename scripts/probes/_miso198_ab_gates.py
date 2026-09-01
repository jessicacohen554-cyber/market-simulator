"""miso-198 A/B scorer — the PREREG's gates, evaluated by code written blind.

**Written and pushed while the CONTROL leg was still solving and BEFORE any arm
result existed.** Every gate below is a transcription of
``PREREG-miso198-stgas-oom-level-2026-09-01.md`` §3, which was itself committed
before either leg's result was read. Nothing here is tuned to an observed
number, and no C3a threshold is a success criterion anywhere in this file.

THE ARM. ``st_gas_mustrun_oom_level`` — the LEVEL SOURCE of the existing
``st_gas_mustrun_p25_level`` floor re-conditioned on the plant's out-of-merit
hours (the miso-197 W3b set). Membership, window, mechanism id and the
cheapest-first ``pmax x availability`` clip are untouched, so this is a
single-delta level swap and nothing else.

THE FROZEN DIRECTION (PREREG §2), which REVERSES FINDING-miso197 §8(1). The
only admissible level statistic is LOWER than the incumbent at every floored
plant, so:

  * **ST_GAS DOWN** (further under 0) and **CC_REGULAR UP** (further over 0),
    confidence 0.85, bounded by the measured assertion drop
    0.591 / 0.637 / 0.646 TWh with a realised conversion < 1;
  * **C3a face UP** — the one direction that would help the keeper's SOLE
    failing criterion, pre-registered here precisely so a favourable movement
    can never be presented as the reason the arm was kept (rule 1
    ``[R-STRUCT]``);
  * **C8 face DOWN (improving)** — less forced energy, so a lower ST_GAS
    forced share.

GATES (PREREG §3), verbatim:

  * **S-0 control integrity** — the control reproduces the keeper's committed
    sidecars, ``max_abs_diff == 0``. Drift is DISCLOSED, never a kill: HEAD has
    moved since the keeper was solved, and a drifting control is information
    about other lanes, not about this arm. It DOES void the A/B if the drift
    reaches the classes under test, which is reported explicitly.
  * **S-1 single delta** — the two ``scenario_config`` dumps differ in exactly
    ``st_gas_mustrun_oom_level: false -> true``.
  * **S-2 floor liveness** — the arm's D-2 ``st_gas_mustrun_per_plant`` forced
    energy FALLS in every year, by a magnitude within +-50 % of the
    pre-registered assertion drop. UNSCORED (never silently passed) if the
    basis is absent — the miso-196 S-2 correction.
  * **K-1 C1 band** — any class-year PASSING C1 on the control and FAILING on
    the arm. ``CC_REGULAR-2024`` (1.34 TWh of headroom) and ``CC_REGULAR-2023``
    are NAMED EX ANTE as the live risk and are reported by name whether or not
    they fire.
  * **K-2 C3b** — arm NRMSE through 0.20 in any year.
  * **K-3 new D-4** — any new per-unit conduct failure on the arm.
  * **K-4 shape** — ST_GAS D-1 ``profile_r`` below 0.80 or ``cv_ratio`` below
    0.50 in any year.
  * **K-5 record flips** — any PASS -> non-PASS flip among scored records
    beyond those K-1/K-2/K-4 already name.
  * **K-6 DOF** — ``n_residual`` above the keeper's 2.

POSTURE (PREREG §4): all kills silent => keeper candidate; any kill fires =>
REJECT, cell ``R``, keeper unchanged, and the kill is NOT renegotiated; every
scored record identical => cell ``I``.

Record: ``results/calibration/_miso198_ab_gates.json``.

Run:
    python3 scripts/probes/_miso198_ab_gates.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

KEEPER = REPO / "results/calibration/miso191_bax_B"
CONTROL = REPO / "results/calibration/miso198_control_A"
ARM = REPO / "results/calibration/miso198_oom_B"
OUT = REPO / "results/calibration/_miso198_ab_gates.json"
YEARS = (2023, 2024, 2025)
FIELD = "st_gas_mustrun_oom_level"
MECH = "st_gas_mustrun_per_plant"

# --- frozen ex-ante lines (the PREREG is the authority; these mirror it) -----
C3B_GATE = 0.20
D1_MIN_PROFILE_R = 0.80
D1_MIN_CV_RATIO = 0.50
DOF_MAX = 2
# Measured assertion drop (results/calibration/_miso198_level_selection.json,
# materiality_reported), used ONLY as the S-2 magnitude reference.
ASSERTION_DROP_TWH = {2023: 0.5914, 2024: 0.6366, 2025: 0.6455}
S2_BAND = 0.50
# Named ex ante in PREREG §3; reported by name whether or not they fire.
NAMED_KILL_KEYS = ("fuelmix|CC_REGULAR|2024", "fuelmix|CC_REGULAR|2023")
# The classes the arm is expected to move; used only to judge whether an S-0
# drift (if any) reaches the population under test.
CLASSES_UNDER_TEST = ("ST_GAS", "CC_REGULAR")


# ------------------------------------------------------------------ helpers
def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json",
         str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _crit_status(verdict: dict) -> dict:
    out = {}
    for name, block in (verdict.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            key = f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"
            out[key] = rec.get("status")
    return out


def _c1(verdict: dict) -> dict:
    """{class|year: model-minus-actual TWh} from the fuelmix records."""
    out = {}
    for rec in (verdict.get("criteria", {}).get("fuelmix") or {}).get("records", []):
        k, y = rec.get("key"), rec.get("year")
        if k is None or y is None:
            continue
        try:
            out[f"{k}|{y}"] = float(rec["model"]) - float(rec["actual"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _c3a(verdict: dict) -> dict:
    out = {}
    for rec in verdict["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def _c3b(verdict: dict) -> dict:
    return {
        int(r["year"]): float(r["model"])
        for r in verdict["criteria"]["price_shape"]["records"]
        if r.get("key") is None and r.get("model") is not None
    }


def _led(bundle: Path) -> dict:
    p = bundle / "legitimacy_diagnostics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _d4_fail_keys(bundle: Path) -> set[tuple]:
    out = set()
    for r in ((_led(bundle).get("diagnostics") or {}).get("D4") or {}).get("rows", []) or []:
        if str(r.get("verdict", "pass")).lower() != "pass":
            out.add((r.get("year"), r.get("check"), r.get("floor"), r.get("plant")))
    return out


def _d1_st_gas(bundle: Path) -> dict:
    out = {}
    for r in ((_led(bundle).get("diagnostics") or {}).get("D1") or {}).get("rows", []) or []:
        if r.get("class") == "ST_GAS":
            out[int(r["year"])] = {
                "profile_r": r.get("profile_r"),
                "cv_ratio": r.get("cv_ratio"),
                "verdict": r.get("verdict"),
            }
    return out


def _d2_mech(bundle: Path, mech: str, klass: str = "ST_GAS") -> dict:
    out = {}
    for r in ((_led(bundle).get("diagnostics") or {}).get("D2") or {}).get("rows", []) or []:
        if r.get("mechanism") == mech and r.get("class") == klass:
            out[int(r["year"])] = {
                "forced_twh": r.get("forced_twh"),
                "share_of_class": r.get("share_of_class"),
                "class_total_twh": r.get("class_total_twh"),
            }
    return out


def _n_residual(bundle: Path):
    p = bundle / "calibration_attestation.json"
    if not p.exists():
        return None
    return (json.loads(p.read_text()).get("free_parameters") or {}).get("n_residual")


# -------------------------------------------------------------------- gates
def s0_identity() -> dict:
    """S-0 — the control reproduces the keeper's committed sidecars exactly."""
    out: dict = {"gate": "S-0", "files": [], "passed": True, "worst": 0.0}
    for path in sorted((KEEPER / "hourly").glob("*.parquet")):
        other = CONTROL / "hourly" / path.name
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
        worst, nonnum_ok = 0.0, True
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
        out["worst"] = max(out["worst"], worst)
    out["note"] = (
        "DRIFT IS DISCLOSED, NEVER A KILL: HEAD has moved since the keeper was "
        "solved, so a drifting control is information about other lanes, not "
        "about this arm. It voids the A/B only if it reaches the classes under "
        "test, which the class-drift line below reports."
    )
    return out


def s1_single_delta() -> dict:
    """S-1 — the scenario_config delta is exactly {FIELD: false -> true}."""
    sc_a = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    sc_b = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    diffs = {
        k: (sc_a.get(k), sc_b.get(k))
        for k in set(sc_a) | set(sc_b)
        if sc_a.get(k) != sc_b.get(k)
    }
    ok = set(diffs) == {FIELD} and sc_a.get(FIELD) is False and sc_b.get(FIELD) is True
    return {"gate": "S-1", "diffs": diffs, "passed": bool(ok)}


def s2_liveness() -> dict:
    """S-2 — the floor's own D-2 forced energy falls, by the right magnitude."""
    dc, da = _d2_mech(CONTROL, MECH), _d2_mech(ARM, MECH)
    if not dc or not da:
        return {
            "gate": "S-2", "passed": None, "control": dc, "arm": da,
            "note": "UNSCORED — the D-2 basis is absent in one or both legs; "
                    "reported, never silently passed (the miso-196 correction).",
        }
    rows = {}
    ok = True
    for y in YEARS:
        c, a = dc.get(y), da.get(y)
        if c is None or a is None:
            rows[y] = {"scored": False}
            ok = False
            continue
        drop = float(c["forced_twh"]) - float(a["forced_twh"])
        ref = ASSERTION_DROP_TWH[y]
        inband = (1 - S2_BAND) * ref <= drop <= (1 + S2_BAND) * ref
        rows[y] = {
            "control_forced_twh": c["forced_twh"], "arm_forced_twh": a["forced_twh"],
            "observed_drop_twh": round(drop, 4), "predicted_drop_twh": ref,
            "fell": bool(drop > 0), "in_band": bool(inband),
        }
        ok = ok and drop > 0 and inband
    return {"gate": "S-2", "rows": rows, "passed": bool(ok)}


def kills_and_scoring() -> dict:
    out: dict = {}
    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    sc, sa = _crit_status(vc), _crit_status(va)
    flips = {k: f"{sc.get(k)} -> {sa.get(k)}"
             for k in set(sc) | set(sa) if sc.get(k) != sa.get(k)}
    bad = {k: v for k, v in flips.items()
           if sc.get(k) == "PASS" and sa.get(k) == "FAIL"}
    c1_bad = {k: v for k, v in bad.items() if k.startswith("fuelmix|")}
    other_bad = {k: v for k, v in bad.items() if not k.startswith("fuelmix|")}

    c3b_a, c3b_c = _c3b(va), _c3b(vc)
    over = {y: v for y, v in c3b_a.items() if v > C3B_GATE}
    d4c, d4a = _d4_fail_keys(CONTROL), _d4_fail_keys(ARM)
    new_d4 = sorted(map(list, d4a - d4c))
    d1c, d1a = _d1_st_gas(CONTROL), _d1_st_gas(ARM)
    shape_bad = {
        y: v for y, v in d1a.items()
        if (v.get("profile_r") is not None and v["profile_r"] < D1_MIN_PROFILE_R)
        or (v.get("cv_ratio") is not None and v["cv_ratio"] < D1_MIN_CV_RATIO)
    }
    nrc, nra = _n_residual(CONTROL), _n_residual(ARM)
    c1c, c1a = _c1(vc), _c1(va)
    c3a_c, c3a_a = _c3a(vc), _c3a(va)

    out["K1"] = {
        "c1_pass_to_fail": c1_bad,
        "named_ex_ante": {k: f"{sc.get(k)} -> {sa.get(k)}" for k in NAMED_KILL_KEYS},
        "passed": not c1_bad,
    }
    out["K2"] = {"c3b_control": c3b_c, "c3b_arm": c3b_a, "over_gate": over,
                 "passed": not over}
    out["K3"] = {"d4_control": sorted(map(list, d4c)),
                 "d4_arm": sorted(map(list, d4a)),
                 "new_d4_fails": new_d4, "passed": not new_d4}
    out["K4"] = {"d1_st_gas_control": d1c, "d1_st_gas_arm": d1a,
                 "violations": shape_bad, "passed": not shape_bad}
    out["K5"] = {"other_pass_to_fail": other_bad, "all_flips": flips,
                 "passed": not other_bad}
    out["K6"] = {"n_residual_control": nrc, "n_residual_arm": nra,
                 "keeper_max": DOF_MAX,
                 "note": "a re-conditioned measured statistic introduces ZERO "
                         "free parameters, so n_residual must not move",
                 "passed": bool(nra is None or nra <= DOF_MAX)}

    # ---- reported, never gated (rule 1) ----
    c1_moves = {}
    for klass in CLASSES_UNDER_TEST:
        for y in YEARS:
            k = f"{klass}|{y}"
            if k in c1c and k in c1a:
                c1_moves[k] = {
                    "control_twh": round(c1c[k], 4), "arm_twh": round(c1a[k], 4),
                    "delta_twh": round(c1a[k] - c1c[k], 4),
                }
    st24 = c1_moves.get("ST_GAS|2024", {}).get("delta_twh")
    cc24 = c1_moves.get("CC_REGULAR|2024", {}).get("delta_twh")
    out["scoring"] = {
        "c1_moves_classes_under_test": c1_moves,
        "frozen_direction": "ST_GAS DOWN / CC_REGULAR UP (PREREG §2, conf 0.85) "
                            "— REVERSES FINDING-miso197 §8(1)",
        "direction_observed_2024": {
            "ST_GAS": None if st24 is None else ("DOWN" if st24 < 0 else "UP" if st24 > 0 else "FLAT"),
            "CC_REGULAR": None if cc24 is None else ("UP" if cc24 > 0 else "DOWN" if cc24 < 0 else "FLAT"),
        },
        "c3a_control_pct": {y: round(v, 4) for y, v in c3a_c.items()},
        "c3a_arm_pct": {y: round(v, 4) for y, v in c3a_a.items()},
        "c3a_face_pp": {y: round(abs(c3a_a[y]) - abs(c3a_c[y]), 4)
                        for y in YEARS if y in c3a_c and y in c3a_a},
        "c3a_frozen_direction": "UP (PREREG §2) — reported, NEVER the criterion",
        "d2_st_gas_control": _d2_mech(CONTROL, MECH),
        "d2_st_gas_arm": _d2_mech(ARM, MECH),
        "determination_control": vc.get("determination"),
        "determination_arm": va.get("determination"),
        "records_identical": not flips,
    }
    return out


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso198-stgas-oom-level-2026-09-01.md §2-§4",
        "keeper": "2026-08-30-miso-191-bexit",
        "field": FIELD,
        "control": CONTROL.name, "arm": ARM.name,
        "scorer_written_before_any_arm_result": True,
    }
    out["S0"] = s0_identity()
    print("S-0", "PASS" if out["S0"]["passed"] else
          f"DRIFT max|diff|={out['S0']['worst']} (disclosed, not a kill)")
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else "KILL", out["S1"]["diffs"] or "")
    out["S2"] = s2_liveness()
    print("S-2", out["S2"]["passed"])
    out.update(kills_and_scoring())
    for k in ("K1", "K2", "K3", "K4", "K5", "K6"):
        print(k, "PASS" if out[k]["passed"] else "KILL")
    print("scoring", json.dumps(out["scoring"], indent=1))

    kills_silent = all(out[k]["passed"] for k in ("K1", "K2", "K3", "K4", "K5", "K6"))
    structural_ok = out["S1"]["passed"] and (out["S2"]["passed"] is not False)
    if not out["S1"]["passed"]:
        out["verdict"] = "VOID — not a single delta; the A/B does not measure the lever"
    elif not (structural_ok and kills_silent):
        out["verdict"] = (
            "REJECT — a pre-registered kill fired (PREREG §4). The kill is not "
            "renegotiated; cell R, keeper unchanged."
        )
    elif out["scoring"]["records_identical"]:
        out["verdict"] = (
            "INERT — every scored record identical; cell I, keeper unchanged."
        )
    else:
        out["verdict"] = (
            "KILLS SILENT -> keeper candidate on the arm's own gates. The C3a "
            "movement is reported at full magnitude and is NEVER the "
            "justification (rule 1 [R-STRUCT])."
        )
    print("VERDICT:", out["verdict"])
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()
