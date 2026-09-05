"""miso-217 A/B gates — the `phys_*` coverage-gap arm, scored on the PREREG's own rule.

**COMMITTED BEFORE THE SOLVE.** Every band, bar and named face below is frozen from
``results/calibration/PREREG-miso217-intermediate-phys-arm-2026-09-05.md`` (pushed
BLIND at ``76c2574c``) and from the CONTROL's own committed verdict, which is the
keeper and is never re-solved.

Arm: ``miso_intermediate_gas_offer_margin=true`` — one MISO-gated ``ScenarioConfig``
boolean, zero free parameters, merging the PARENT gas class's already-registered,
already-frozen ``phys_econ_low`` / ``phys_econ_high`` onto the three duty-split
``*_INTERMEDIATE`` offer curves so ``gas_offer_net_revenue_margin`` stops skipping
38,501.0 MW = 58.4 % of MISO's assembled gas capacity. ECON-ONLY by design.

Gates: **S-0** control identity inherited (the keeper IS the control); **S-1** exactly
one field differs over the RECORDED configs; **S-2** liveness (markup appears on the
cohorts' econ tranches, and flag-off is byte-identical). Kills **K-1 … K-6** exactly as
pre-registered, with rule 1 ``[R-STRUCT]`` honoured: an adverse C1/C3a residual that
stays in band is NOT a kill and is reported at full magnitude, never argued.

Usage::

    PYTHONPATH=src .venv/bin/python scripts/probes/_miso217_ab_gates.py

Record: ``results/calibration/_miso217_ab_gates.json``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results" / "calibration" / "miso213_layering_B"
CONTROL = KEEPER  # the charter: the keeper IS the control, never re-solved
ARM = REPO / "results" / "calibration" / "miso217_intermphys_B"
OUT = REPO / "results" / "calibration" / "_miso217_ab_gates.json"
YEARS = (2023, 2024, 2025)
FIELD = "miso_intermediate_gas_offer_margin"

# ---- FROZEN FROM THE PREREG (§5) AND THE CONTROL'S OWN COMMITTED VERDICT ----
C1_BAND_TWH = 8.00
#: Every C1 cell of the CONTROL, read from its own `calibration_verdict --json`
#: BEFORE the arm solved. K-1 is a BAND-EXIT test over all of them, not only the
#: named face — CT_PEAKER|2023 at -5.121 (2.879 TWh of headroom) is the second
#: exposure and was surfaced while freezing this table, before any arm number
#: existed. It is covered by K-1 as the PREREG wrote it.
C1_CONTROL = {
    "CC_CHP|2023": -0.971, "CC_CHP|2024": 0.161, "CC_CHP|2025": 1.917,
    "CC_REGULAR|2023": -2.774, "CC_REGULAR|2024": 7.419, "CC_REGULAR|2025": -2.423,
    "COAL_BIT|2023": -2.348, "COAL_BIT|2024": -3.644, "COAL_BIT|2025": -1.451,
    "COAL_LIGNITE|2023": -0.577, "COAL_LIGNITE|2024": -0.776, "COAL_LIGNITE|2025": -0.724,
    "COAL_PRB|2023": 0.835, "COAL_PRB|2024": -3.166, "COAL_PRB|2025": -4.208,
    "CT_PEAKER|2023": -5.121, "CT_PEAKER|2024": -0.884, "CT_PEAKER|2025": -3.194,
    "ST_CHP|2023": -2.869, "ST_CHP|2024": -2.902, "ST_CHP|2025": -2.173,
    "ST_GAS|2023": -2.182, "ST_GAS|2024": -6.803, "ST_GAS|2025": -5.748,
}
#: The PREREG's named face and its headroom (§5 K-1).
K1_NAMED = "CC_REGULAR|2024"
#: PREREG §5 K-2: C8 CT_PEAKER-2023 is ALREADY over the 0.15 peaker budget and
#: passes only on rule 20's conditional provenance+shape route. A RISE is not a
#: kill; the conditional route ceasing to clear is.
C8_CONTROL_CT_2023 = 0.2044
C8_PEAKER_BUDGET = 0.15
#: PREREG §7 prediction bands, frozen. Scored, never renegotiated.
P1_EXPECTED_TRANCHES = 534          # 264 CT + 234 CC + 36 ST econ tranches
P2_LP_OVER_SCREEN_BAR = 0.75        # |LP delta| <= this x |screen delta|
P2_SCREEN_CT = {2023: -1.4746, 2024: -5.2847, 2025: 1.4566}
P3_CC2024_BAND = (7.2, 8.0)
P4_C8_CT2023_BAND = (0.21, 0.26)
P5_C3A_2025_PP = 0.5
P5_C3A_OTHER_PP = 1.5
#: PREREG §6: the F-4 footprint disposition, in percentage points of the
#: cohort's own offer, against CT_PEAKER's already-accepted 24-30 %.
F4_DISPOSITION_PP = 5.0


def _verdict(bundle: Path) -> dict:
    res = subprocess.run(
        [sys.executable, str(REPO / "scripts/calibration_verdict.py"), "--json", str(bundle)],
        capture_output=True, text=True, check=False,
    )
    if not res.stdout.strip():
        raise SystemExit(f"no JSON for {bundle}: {res.stderr[-800:]}")
    return json.loads(res.stdout)


def _c1(v: dict) -> dict:
    out = {}
    for rec in (v.get("criteria", {}).get("fuelmix") or {}).get("records", []):
        k, y = rec.get("key"), rec.get("year")
        if k is None or y is None:
            continue
        try:
            out[f"{k}|{y}"] = round(float(rec["model"]) - float(rec["actual"]), 4)
        except (KeyError, TypeError, ValueError):
            continue
    return out


def _c3a(v: dict) -> dict:
    return {
        int(r["year"]): round(100.0 * (float(r["model"]) - float(r["actual"])) / float(r["actual"]), 4)
        for r in v["criteria"]["price_mean"]["records"]
        if r.get("benchmark") == "RT" and r.get("key") is None
    }


def _status(v: dict) -> dict:
    out = {}
    for name, block in (v.get("criteria") or {}).items():
        for rec in (block or {}).get("records", []) or []:
            out[f"{rec.get('criterion', name)}|{rec.get('key')}|{rec.get('year')}"] = rec.get("status")
    return out


def _led(b: Path) -> dict:
    p = b / "legitimacy_diagnostics.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _rows(b: Path, block: str) -> list:
    return ((_led(b).get("diagnostics") or {}).get(block) or {}).get("rows", []) or []


def _c8(b: Path, klass: str) -> dict:
    forced: dict = {}
    tot: dict = {}
    for r in _rows(b, "D2"):
        if r.get("class") != klass:
            continue
        y = int(r["year"])
        forced[y] = forced.get(y, 0.0) + float(r.get("forced_twh") or 0.0)
        if r.get("class_total_twh"):
            tot[y] = float(r["class_total_twh"])
    return {y: (round(forced[y] / tot[y], 4) if tot.get(y) else None) for y in forced}


def _d4_fails(b: Path) -> list:
    return [
        {k: r.get(k) for k in ("year", "check", "floor", "plant", "verdict")}
        for r in _rows(b, "D4")
        if str(r.get("verdict", "pass")).lower() != "pass"
    ]


def _d1(b: Path, klass: str) -> dict:
    return {
        int(r["year"]): {"profile_r": r.get("profile_r"), "cv_ratio": r.get("cv_ratio"),
                         "verdict": r.get("verdict")}
        for r in _rows(b, "D1") if r.get("class") == klass
    }


def main() -> dict:
    if not (ARM / "run_config.json").exists():
        raise SystemExit(f"arm bundle missing: {ARM} — solve it before scoring")

    vc, va = _verdict(CONTROL), _verdict(ARM)
    c1c, c1a = _c1(vc), _c1(va)
    c3c_, c3a_ = _c3a(vc), _c3a(va)
    stc, sta = _status(vc), _status(va)

    rep: dict = {
        "charter": "miso-217 A/B — the phys_* coverage-gap arm; scorer COMMITTED BEFORE THE SOLVE.",
        "prereg": "results/calibration/PREREG-miso217-intermediate-phys-arm-2026-09-05.md @ 76c2574c",
        "control": str(CONTROL.relative_to(REPO)),
        "arm": str(ARM.relative_to(REPO)),
        "field": FIELD,
        "rule_1_note": "An adverse C1/C3a residual that stays in band is EXPECTED (PREREG F-5) and is NOT a kill. It is reported at full magnitude and never argued.",
    }

    # ---------------- S-0 ------------------------------------------------
    present, missing = 0, []
    for year in YEARS:
        for stem in ("class_hourly", "class_band_hourly", "system", "reserve_family"):
            (present := present + 1) if (KEEPER / "hourly" / f"{stem}_{year}.parquet").exists() \
                else missing.append(f"{stem}_{year}")
    rep["S0"] = {
        "control_is_keeper_bundle": CONTROL == KEEPER,
        "keeper_sidecars_present": present, "missing": missing,
        "note": "S-0 inherited: the control is the keeper's OWN committed bundle, not a re-solve, so bit-identity is definitional.",
        "passed": bool(not missing and CONTROL == KEEPER),
    }

    # ---------------- S-1 ------------------------------------------------
    rc = json.loads((CONTROL / "run_config.json").read_text())["scenario_config"]
    ra = json.loads((ARM / "run_config.json").read_text())["scenario_config"]
    shared = set(rc) & set(ra)
    diffs = sorted(k for k in shared if rc[k] != ra[k])
    arm_only = sorted(set(ra) - set(rc))
    arm_only_nondefault = {}
    try:
        import dataclasses

        from market_sim.config.scenarios import ScenarioConfig
        defaults = {f.name: f.default for f in dataclasses.fields(ScenarioConfig)}
        for k in arm_only:
            if k in defaults and ra[k] != defaults[k] and k != FIELD:
                arm_only_nondefault[k] = [defaults[k], ra[k]]
    except Exception as exc:  # pragma: no cover - reporting only
        arm_only_nondefault = {"_error": str(exc)}
    rep["S1"] = {
        "fields_in_both": len(shared),
        "diffs": {k: [rc[k], ra[k]] for k in diffs},
        "arm_only_fields": arm_only,
        "arm_only_at_nondefault": arm_only_nondefault,
        "expected_single_delta": FIELD,
        "passed": bool(
            (diffs == [FIELD] or (diffs == [] and FIELD in arm_only and ra.get(FIELD) is True))
            and not arm_only_nondefault
        ),
    }

    # ---------------- S-2 liveness (from the arm's own phase-0 record) ----
    p0 = REPO / "results" / "calibration" / "_miso217_liveness.json"
    live = json.loads(p0.read_text()) if p0.exists() else {}
    n_live = live.get("n_tranches_marked_up_new")
    rep["S2"] = {
        "source": str(p0.relative_to(REPO)) if p0.exists() else None,
        "n_newly_marked_up_tranches": n_live,
        "P1_expected": P1_EXPECTED_TRANCHES,
        "by_cohort": live.get("by_cohort"),
        "flag_off_byte_identical": live.get("flag_off_byte_identical"),
        "passed": bool(n_live and n_live > 0 and live.get("flag_off_byte_identical") is True),
    }

    # ---------------- K-1 C1 band exit -----------------------------------
    exits, moves = [], {}
    for k, base in C1_CONTROL.items():
        arm_v = c1a.get(k)
        if arm_v is None:
            continue
        moves[k] = {"control": base, "arm": arm_v, "delta": round(arm_v - base, 4),
                    "control_headroom": round(C1_BAND_TWH - abs(base), 4)}
        if abs(base) <= C1_BAND_TWH and abs(arm_v) > C1_BAND_TWH:
            exits.append(k)
    rep["K1_c1_band_exit"] = {
        "band_twh": C1_BAND_TWH, "named_face": K1_NAMED,
        "named_face_control": C1_CONTROL[K1_NAMED],
        "named_face_arm": c1a.get(K1_NAMED),
        "second_exposure_note": "CT_PEAKER|2023 at -5.121 has 2.879 TWh of headroom — the second exposure, surfaced while FREEZING this table before the solve, and covered by K-1 as the PREREG wrote it.",
        "cells": moves, "band_exits": exits,
        "backfill_note": "the phase-0 static screen is BLIND to cross-class backfill (it holds price fixed); this gate is the only instrument that can see it.",
        "FIRES": bool(exits),
    }

    # ---------------- K-2 C8 ---------------------------------------------
    c8c, c8a = _c8(CONTROL, "CT_PEAKER"), _c8(ARM, "CT_PEAKER")
    d4c, d4a = _d4_fails(CONTROL), _d4_fails(ARM)
    d1c, d1a = _d1(CONTROL, "CT_PEAKER"), _d1(ARM, "CT_PEAKER")
    new_d4 = [r for r in d4a if r not in d4c]
    d1_regress = [
        y for y, v in d1a.items()
        if str(v.get("verdict", "pass")).lower() != "pass"
        and str((d1c.get(y) or {}).get("verdict", "pass")).lower() == "pass"
    ]
    rep["K2_c8_conditional_route"] = {
        "budget": C8_PEAKER_BUDGET,
        "ct_peaker_share_control": c8c, "ct_peaker_share_arm": c8a,
        "control_2023": C8_CONTROL_CT_2023,
        "d4_new_failures": new_d4, "d1_new_failures_ct_peaker": d1_regress,
        "note": "a RISE is not a kill (PREREG §5 K-2); the conditional provenance+shape route ceasing to clear is.",
        "FIRES": bool(new_d4 or d1_regress),
    }

    # ---------------- K-3 caveats ----------------------------------------
    cav_c, cav_a = vc.get("caveats") or {}, va.get("caveats") or {}
    rep["K3_caveat_budget"] = {
        "control": cav_c, "arm": cav_a,
        "n_ledgered_arm": len((cav_a.get("ledgered") or [])),
        "n_protective_arm": len((cav_a.get("protective") or [])),
        "FIRES": bool(len(cav_a.get("ledgered") or []) > 1
                      or len(cav_a.get("protective") or []) > 0),
    }

    # ---------------- K-4 determination class ----------------------------
    fails_c = sorted(k for k, s in stc.items() if s == "FAIL")
    fails_a = sorted(k for k, s in sta.items() if s == "FAIL")
    rep["K4_determination"] = {
        "control": vc.get("determination"), "arm": va.get("determination"),
        "control_fails": fails_c, "arm_fails": fails_a,
        "new_fails": sorted(set(fails_a) - set(fails_c)),
        "FIRES": bool(set(fails_a) - set(fails_c)),
    }

    # ---------------- K-5 instrument -------------------------------------
    rep["K5_instrument"] = {
        "S1_passed": rep["S1"]["passed"], "S2_passed": rep["S2"]["passed"],
        "FIRES": bool(not rep["S1"]["passed"] or not rep["S2"]["passed"]),
    }

    # ---------------- K-6 any other PASS -> FAIL -------------------------
    flips = sorted(k for k in set(stc) & set(sta) if stc[k] == "PASS" and sta[k] == "FAIL")
    rep["K6_pass_to_fail"] = {"flips": flips, "FIRES": bool(flips)}

    # ---------------- reported, never argued -----------------------------
    rep["reported_never_argued"] = {
        "C3a_control": c3c_, "C3a_arm": c3a_,
        "C3a_delta_pp": {y: round(c3a_.get(y, float("nan")) - c3c_.get(y, float("nan")), 4)
                         for y in sorted(set(c3c_) & set(c3a_))},
        "P5_bars": {"2025_pp": P5_C3A_2025_PP, "other_pp": P5_C3A_OTHER_PP},
        "C1_largest_movers": sorted(
            ({"cell": k, **v} for k, v in moves.items()),
            key=lambda r: -abs(r["delta"]))[:8],
        "P3_cc2024_band": list(P3_CC2024_BAND),
        "P4_c8_ct2023_band": list(P4_C8_CT2023_BAND),
        "P2_screen_ct_bound": P2_SCREEN_CT,
        "P2_bar": P2_LP_OVER_SCREEN_BAR,
        "miso214_standing": "62-70 % of the missed CT energy was produced BELOW the plant's own delivered cost at the market's own price and is unreachable by any offer or price mechanism; this arm reaches at most bucket C and part of bucket A.",
    }

    fired = [k for k, v in rep.items()
             if isinstance(v, dict) and v.get("FIRES") is True]
    rep["verdict"] = {
        "kills_fired": fired,
        "gates_passed": all(rep[g]["passed"] for g in ("S0", "S1", "S2")),
        "PROMOTE_ELIGIBLE": bool(not fired
                                 and all(rep[g]["passed"] for g in ("S0", "S1", "S2"))),
        "note": "PROMOTE_ELIGIBLE is necessary, not sufficient: PREREG §6's F-4 footprint disposition is adjudicated in the FINDING, not here.",
    }

    OUT.write_text(json.dumps(rep, indent=2) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for g in ("S0", "S1", "S2"):
        print(f"  {g}: passed={rep[g]['passed']}")
    for k in [x for x in rep if x.startswith("K")]:
        print(f"  {k}: FIRES={rep[k]['FIRES']}")
    print(f"  VERDICT: {rep['verdict']}")
    return rep


if __name__ == "__main__":
    main()
