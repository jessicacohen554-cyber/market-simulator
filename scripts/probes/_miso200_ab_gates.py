"""miso-200 A/B scorer -- WRITTEN AND COMMITTED BLIND, before either leg's numbers.

===============================================================================
THE TWO DEFECTS OF THE miso-198 SCORER, DELIBERATELY NOT INHERITED
===============================================================================
``_miso198_ab_gates.py`` was left unrepaired on purpose (FINDING-miso198 section
5b reports its own scorer's verdict line as WRONG, against interest). This file
does not import it. Both of its defects are fixed here, and the fixes are stated
before any result exists:

1. **ORDERING.** miso-198 ordered the ``records_identical`` branch AHEAD of the
   kills-silent branch, so an arm that moved every value without flipping a
   status was reported ``INERT``. Here the order is: VOID (not a single delta)
   -> KILL FIRED -> **KILLS SILENT** -> INERT, and INERT is reachable ONLY when
   the arm moved nothing measurable.
2. **WHAT "IDENTICAL" MEANS.** miso-198 computed record identity from criterion
   STATUSES. A status is a coarse band; an arm can move a criterion's VALUE by
   a large margin without changing which band it lands in. Here inertness is
   measured on **VALUE MOVEMENT** -- the numeric C1 / C3a / C3b / C8 deltas --
   against an explicit epsilon, and the status map is carried only as a
   *report*, never as the inertness test.

===============================================================================
THE GATES, from PREREG-miso200 section 5, verbatim
===============================================================================
* **S-0** control integrity: BIT-IDENTICAL to the keeper's 12 committed
  sidecars, ``max_abs_diff`` 0.0. Drift is DISCLOSED, never silently absorbed.
* **S-1** single delta: exactly one ``ScenarioConfig`` field differs. A failure
  VOIDS the A/B -- it did not measure the lever.
* **S-2** liveness: the arm's ``(1403, ST_GAS)`` 2024 mean availability < 1.0
  AND the arm's ST_GAS forced energy < the control's. **Liveness only -- never
  a target.**
* **K-1** C1 band -- THE NAMED RISK, its arithmetic frozen in the PREREG before
  the solve: ``CC_REGULAR-2024`` at **+6.748** with **1.252 TWh** to the +-8.00
  edge and moving UP; ``ST_GAS-2024`` at **-7.553** with **0.447 TWh** and
  moving DOWN.
* **K-2** C3b no PASS->FAIL. **K-3** D-4: zero NEW off-window binding.
  **K-4** D-1 shape: no PASS->FAIL. **K-5** zero PASS->non-PASS anywhere.
  **K-6** DOF: replay bundles carry no attestation => **UNSCORED and disclosed
  as such, never counted as a PASS**.

**C3a is reported at full magnitude and is NEVER a gate** (rule 1
``[R-STRUCT]``). No branch below reads it.

===============================================================================
THE OWNER'S RE-SCOPED BAR (2026-09-02), recorded here BEFORE any result
===============================================================================
The owner directed, in this session and in these words, that *"if structural
integrity improves but gates regress that may still be a keeper"*. That does
NOT silence a kill and does not change a single threshold above: a fired kill
is still reported as fired, at full magnitude. What it changes is the
DISPOSITION of a fired-kill outcome -- from an automatic REJECT to an
**owner-decision** verdict that states the structural case and the regression
side by side and leaves the promotion to the owner. The scorer never promotes
on its own under that branch, and it never reclassifies a kill as a pass.

Usage:
    python3 scripts/probes/_miso200_ab_gates.py

Record: ``results/calibration/_miso200_ab_gates.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

KEEPER = REPO / "results" / "calibration" / "miso198_oom_B"
CONTROL = REPO / "results" / "calibration" / "miso200_control_A"
ARM = REPO / "results" / "calibration" / "miso200_unitroute_B"
OUT = REPO / "results" / "calibration" / "_miso200_ab_gates.json"
FIELD = "unit_outage_mixed_gas_routing"
YEARS = (2023, 2024, 2025)

# --- FROZEN, from the PREREG. Stated before either leg's numbers exist. ------
C1_BAND_TWH = 8.00
K1_NAMED = {                      # class|year -> (control value, headroom)
    "CC_REGULAR|2024": (+6.748, 1.252),
    "ST_GAS|2024": (-7.553, 0.447),
}
INERT_EPS = {"c1_twh": 0.010, "c3a_pp": 0.010, "c3b": 0.0005, "c8_share": 0.0005}


def _verdict_json(bundle: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json", str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _crit_status(v: dict) -> dict:
    out = {}
    for name, block in (v.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = rec.get("status")
    return out


def _c1(v: dict) -> dict:
    out = {}
    for rec in (v.get("criteria", {}).get("fuelmix") or {}).get("records", []):
        k, y = rec.get("key"), rec.get("year")
        if k is None or y is None:
            continue
        try:
            out[f"{k}|{y}"] = float(rec["model"]) - float(rec["actual"])
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _c3a(v: dict) -> dict:
    out = {}
    for rec in v["criteria"]["price_mean"]["records"]:
        if rec.get("benchmark") == "RT" and rec.get("key") is None:
            m, a = float(rec["model"]), float(rec["actual"])
            out[int(rec["year"])] = 100.0 * (m - a) / a
    return out


def _c3b(v: dict) -> dict:
    return {int(r["year"]): float(r["model"])
            for r in v["criteria"]["price_shape"]["records"]
            if r.get("key") is None and r.get("model") is not None}


def _led(b: Path) -> dict:
    p = b / "legitimacy_diagnostics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _rows(b: Path, block: str) -> list:
    return ((_led(b).get("diagnostics") or {}).get(block) or {}).get("rows", []) or []


def _d4_fail_keys(b: Path) -> set:
    return {(r.get("year"), r.get("check"), r.get("floor"), r.get("plant"))
            for r in _rows(b, "D4") if str(r.get("verdict", "pass")).lower() != "pass"}


def _d1(b: Path, klass: str = "ST_GAS") -> dict:
    return {int(r["year"]): {"profile_r": r.get("profile_r"), "cv_ratio": r.get("cv_ratio"),
                             "verdict": r.get("verdict")}
            for r in _rows(b, "D1") if r.get("class") == klass}


def _c8_share(b: Path, klass: str = "ST_GAS") -> dict:
    out = {}
    for r in _rows(b, "D2"):
        if r.get("class") != klass:
            continue
        y = int(r["year"])
        out[y] = out.get(y, 0.0) + float(r.get("forced_twh") or 0.0)
    tot = {}
    for r in _rows(b, "D2"):
        if r.get("class") == klass and r.get("class_total_twh"):
            tot[int(r["year"])] = float(r["class_total_twh"])
    return {y: (out[y] / tot[y] if tot.get(y) else None) for y in out}


# ------------------------------------------------------------------- gates
def s0_identity() -> dict:
    """S-0 -- does the control reproduce the keeper's committed sidecars?"""
    worst, checked, missing = 0.0, 0, []
    for year in YEARS:
        for stem in ("class_hourly", "system", "reserve_family"):
            a = KEEPER / "hourly" / f"{stem}_{year}.parquet"
            b = CONTROL / "hourly" / f"{stem}_{year}.parquet"
            if not a.exists() or not b.exists():
                missing.append(f"{stem}_{year}")
                continue
            da, db = pd.read_parquet(a), pd.read_parquet(b)
            if da.shape != db.shape or list(da.columns) != list(db.columns):
                worst = float("inf"); checked += 1; continue
            num = da.select_dtypes("number").columns
            d = float(np.nanmax(np.abs(da[num].to_numpy() - db[num].to_numpy()))) if len(num) else 0.0
            worst = max(worst, d); checked += 1
    return {"sidecars_checked": checked, "missing": missing, "max_abs_diff": worst,
            "passed": checked > 0 and worst == 0.0}


def s1_single_delta() -> dict:
    ca = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    cb = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    diffs = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
    return {"n_fields": len(set(ca) | set(cb)), "diffs": diffs,
            "passed": diffs == [FIELD]}


def s2_liveness() -> dict:
    """Liveness only. Never a target, and no branch treats it as one."""
    from market_sim.data.outages import unit_outage_derate_factors
    kw = dict(cc_steam_part_reclass=False, cc_nameplate_basis=False, fleet_status_scope=True)
    fac = unit_outage_derate_factors(2024, 8760, "", iso="MISO", mixed_gas_routing=True, **kw)
    arr = fac.get((1403, "ST_GAS"))
    avail = float(np.mean(arr)) if arr is not None else 1.0
    fc, fa = _c8_share(CONTROL), _c8_share(ARM)
    forced_down = {y: (fa.get(y) is not None and fc.get(y) is not None and fa[y] < fc[y])
                   for y in sorted(set(fc) | set(fa))}
    return {"arm_1403_st_gas_mean_availability_2024": round(avail, 4),
            "availability_below_one": avail < 1.0,
            "st_gas_forced_share_control": fc, "st_gas_forced_share_arm": fa,
            "forced_share_fell": forced_down,
            "passed": avail < 1.0 and any(forced_down.values())}


def kills(vc: dict, va: dict) -> dict:
    out: dict = {}
    c1c, c1a = _c1(vc), _c1(va)
    exits, named = [], {}
    for k in sorted(set(c1c) | set(c1a)):
        b, a = c1c.get(k), c1a.get(k)
        if b is None or a is None:
            continue
        if abs(b) <= C1_BAND_TWH and abs(a) > C1_BAND_TWH:
            exits.append({"class_year": k, "control": round(b, 3), "arm": round(a, 3)})
    for k, (pre, head) in K1_NAMED.items():
        named[k] = {"prereg_control": pre, "prereg_headroom": head,
                    "measured_control": round(c1c.get(k), 3) if c1c.get(k) is not None else None,
                    "measured_arm": round(c1a.get(k), 3) if c1a.get(k) is not None else None,
                    "band_exit": bool(c1a.get(k) is not None and abs(c1a[k]) > C1_BAND_TWH)}
    out["K1"] = {"band_twh": C1_BAND_TWH, "named_ex_ante": named,
                 "all_band_exits": exits, "passed": not exits}

    b3c, b3a = _c3b(vc), _c3b(va)
    sc, sa = _crit_status(vc), _crit_status(va)
    c3b_flip = [k for k in sc if k.startswith("price_shape")
                and sc[k] == "PASS" and sa.get(k) not in (None, "PASS")]
    out["K2"] = {"control": b3c, "arm": b3a, "pass_to_fail": c3b_flip, "passed": not c3b_flip}

    new_d4 = sorted(map(str, _d4_fail_keys(ARM) - _d4_fail_keys(CONTROL)))
    out["K3"] = {"new_d4_failures": new_d4,
                 "cleared": sorted(map(str, _d4_fail_keys(CONTROL) - _d4_fail_keys(ARM))),
                 "passed": not new_d4}

    d1c, d1a = _d1(CONTROL), _d1(ARM)
    d1_flip = [y for y in d1c if str(d1c[y].get("verdict", "")).lower() == "pass"
               and str(d1a.get(y, {}).get("verdict", "")).lower() != "pass"]
    out["K4"] = {"control": d1c, "arm": d1a, "pass_to_fail": d1_flip, "passed": not d1_flip}

    flips = [{"record": k, "control": sc[k], "arm": sa.get(k)}
             for k in sorted(sc) if sc[k] == "PASS" and sa.get(k) not in (None, "PASS")]
    out["K5"] = {"pass_to_non_pass": flips, "passed": not flips}

    att = (ARM / "calibration_attestation.json").exists() and \
          (CONTROL / "calibration_attestation.json").exists()
    out["K6"] = {"attestation_present": att,
                 "status": "SCORED" if att else "UNSCORED — replay bundles carry no attestation",
                 "passed": True if att else None}   # None => never counted as a PASS
    return out


def movement(vc: dict, va: dict) -> dict:
    """Inertness measured on VALUE MOVEMENT, not on status identity."""
    c1c, c1a = _c1(vc), _c1(va)
    ac, aa = _c3a(vc), _c3a(va)
    bc, ba = _c3b(vc), _c3b(va)
    sc8, sa8 = _c8_share(CONTROL), _c8_share(ARM)
    d_c1 = {k: round(c1a[k] - c1c[k], 4) for k in sorted(set(c1c) & set(c1a))}
    d_c3a = {y: round(aa[y] - ac[y], 4) for y in sorted(set(ac) & set(aa))}
    d_c3b = {y: round(ba[y] - bc[y], 5) for y in sorted(set(bc) & set(ba))}
    d_c8 = {y: (round(sa8[y] - sc8[y], 5) if sa8.get(y) is not None and sc8.get(y) is not None
                else None) for y in sorted(set(sc8) | set(sa8))}
    moved = (any(abs(v) > INERT_EPS["c1_twh"] for v in d_c1.values())
             or any(abs(v) > INERT_EPS["c3a_pp"] for v in d_c3a.values())
             or any(abs(v) > INERT_EPS["c3b"] for v in d_c3b.values())
             or any(v is not None and abs(v) > INERT_EPS["c8_share"] for v in d_c8.values()))
    return {"epsilons": INERT_EPS, "d_c1_twh": d_c1,
            "c3a_control": ac, "c3a_arm": aa, "d_c3a_pp": d_c3a,
            "d_c3b": d_c3b, "c8_share_control": sc8, "c8_share_arm": sa8, "d_c8_share": d_c8,
            "status_map_identical": _crit_status(vc) == _crit_status(va),
            "arm_moved_values": moved}


def main() -> dict:
    out: dict = {
        "prereg": "PREREG-miso200-outage-routing-mixedgas-2026-09-02.md §5",
        "keeper_at_open": "2026-09-01-miso-198-oomlevel",
        "field": FIELD, "control": CONTROL.name, "arm": ARM.name,
        "scorer_written_and_committed_before_any_arm_result": True,
        "miso198_scorer_defects_not_inherited": [
            "ordering: kills-silent is evaluated BEFORE inertness",
            "inertness measured on VALUE MOVEMENT, not criterion-status identity",
        ],
    }
    out["S0"] = s0_identity()
    print("S-0", "PASS — BIT-IDENTICAL" if out["S0"]["passed"]
          else f"DRIFT max|diff|={out['S0']['max_abs_diff']} (DISCLOSED, not a kill)")
    out["S1"] = s1_single_delta()
    print("S-1", "PASS" if out["S1"]["passed"] else f"VOID {out['S1']['diffs']}")
    out["S2"] = s2_liveness()
    print("S-2", "PASS" if out["S2"]["passed"] else "NOT LIVE")

    vc, va = _verdict_json(CONTROL), _verdict_json(ARM)
    out.update(kills(vc, va))
    out["movement"] = movement(vc, va)
    for k in ("K1", "K2", "K3", "K4", "K5", "K6"):
        p = out[k]["passed"]
        print(k, "PASS" if p is True else ("UNSCORED" if p is None else "KILL"))

    fired = [k for k in ("K1", "K2", "K3", "K4", "K5") if out[k]["passed"] is False]
    out["kills_fired"] = fired
    moved = out["movement"]["arm_moved_values"]

    # ORDER: VOID -> KILL FIRED -> KILLS SILENT -> INERT.  INERT is reachable
    # ONLY when the arm moved nothing measurable (the miso-198 defect repaired).
    if not out["S1"]["passed"]:
        out["verdict"] = "VOID — not a single delta; the A/B does not measure the lever"
    elif fired:
        out["verdict"] = (
            f"KILL FIRED ({', '.join(fired)}) — reported at full magnitude and NOT "
            "renegotiated. Under the owner's 2026-09-02 re-scoped bar this is an "
            "OWNER DECISION, not an automatic reject: the structural case and the "
            "regression are stated side by side and the scorer does not promote."
        )
    elif moved:
        out["verdict"] = (
            "KILLS SILENT and the arm MOVED values -> keeper candidate on its own "
            "gates. C3a is reported at full magnitude and is NEVER the justification."
        )
    else:
        out["verdict"] = "INERT — no scored VALUE moved beyond epsilon; keeper unchanged."
    print("VERDICT:", out["verdict"])
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    main()
