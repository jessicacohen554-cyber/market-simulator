"""PJM RUBRIC-RESIDUAL — grade the screen against the PRECOMMIT's six gates.

Written and committed BEFORE the screen solved, so the gates cannot be shaped
to the result (rule 29 [R-SCREEN]). Every threshold here is the one
``PRECOMMIT-pjm-eas-operand-2026-09-07.md`` §5 states.

The gates are STRUCTURAL and STOP-only. They may kill the arm; they may never
promote it. None of them reads a retirement band: ``retire.total_gw``,
``unit_recall_gt300``, ``false_retire``, coal and gas_st exits are REPORTED at
full magnitude and gate in NEITHER direction.

    python3 docs/handoffs/pjmeas/grade_screen.py <arm-bundle-dir>
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CONTROL = ROOT / "results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm"
CONTROL_LEDGERS = CONTROL / "PJM/fb16fda2ddb0a94a"

# --- the PRECOMMIT's declared numbers, verbatim ----------------------------
# CORRECTED by ADDENDUM-pjm-eas-key-window-2026-09-07.md: the PRECOMMIT §4 key
# cf9b7dc1ca285c35 was computed on the control's recorded FULL-SPAN window
# (2021-2025) while §5 declared a truncated screen (2021-2022), and
# ScenarioConfig.cache_key() includes the window. Recomputed from first
# principles off the SAME committed control config by the SAME three-flag delta.
# No gate, threshold, band or point prediction is changed by that addendum.
DECLARED_ARM_KEY = "8966e7cea75efc4e"       # arm, window 2021-2022
DECLARED_ARM_KEY_FULL_SPAN = "cf9b7dc1ca285c35"  # arm, window 2021-2025 (PRECOMMIT §4)
CONTROL_SCREEN_PRICE_MAX = 52.7715          # $/MWh, control, every decided row
G2_FLOOR_USD_MWH = 60.0                     # STOP below
G3_FLOOR_USD_PER_ACCREDITED_MW_DAY = 12.7   # STOP below (phase-0 C threshold)
G3_PREDICTED_BAND = (25.0, 65.0)            # phase-0 D per-unit min/max
G3_PREDICTED_MEAN = 40.656                  # phase-0 D MW-weighted mean
# phase-0 C, Delta = 40 $/MW-day row — the falsifiable point prediction.
PREDICTED_2022 = {
    "price_usd_per_mw_day": 67.760,
    "cleared_position": 1.04835,
    "uncleared_mw_by_fuel": {"coal": 6647.812, "gas_cc": 3605.197},
}


def _ledger(base: Path, year: int) -> dict:
    return json.loads((base / f"evolution_{year}.json").read_text())


def _arm_ledgers(bundle: Path) -> Path:
    key = json.loads((bundle / "meta.json").read_text())["cache_key"]
    return bundle / "PJM" / key, key


def _eas_per_accredited_mw_day(led: dict) -> dict:
    rows = [e for e in led["pipeline_events"] if e["event"] == "decided"]
    out = defaultdict(lambda: {"mw": 0.0, "eas": 0.0, "acc": 0.0, "n": 0})
    for e in rows:
        b = out[e["fuel"]]
        b["n"] += 1
        b["mw"] += e["mw"]
        b["eas"] += e["energy_margin_usd"] + e["reserve_uplift_usd"]
        b["acc"] += e["capacity_accredited_mw"]
    return {
        f: {
            "n": v["n"],
            "mw": round(v["mw"], 1),
            "eas_usd": round(v["eas"], 0),
            "accredited_mw": round(v["acc"], 3),
            "eas_per_accredited_mw_day": (
                round(v["eas"] / (v["acc"] * 365.0), 4) if v["acc"] > 0 else None
            ),
        }
        for f, v in sorted(out.items())
    }


def _screen_prices(led: dict) -> dict:
    rows = [e for e in led["pipeline_events"] if e["event"] == "decided"]
    if not rows:
        return {"n": 0}
    return {
        "n": len(rows),
        "max": round(float(np.max([r["screen_price_max_usd_mwh"] for r in rows])), 4),
        "mean": round(float(np.mean([r["screen_price_mean_usd_mwh"] for r in rows])), 4),
        "reserve_signal_mean": round(
            float(np.mean([r["reserve_signal_mean_usd_mwh"] for r in rows])), 4
        ),
    }


def _uncleared(led: dict) -> dict:
    cc = led.get("capacity_clearing")
    if not cc:
        return {}
    return {
        "price_usd_per_mw_day": round(cc["price_usd_per_mw_day"], 4),
        "cleared_position": round(cc["cleared_position"], 6),
        "n_uncleared": cc["n_uncleared"],
        "uncleared_mw_by_fuel": {k: round(v, 3) for k, v in cc["uncleared_mw_by_fuel"].items()},
        "marginal_unit": cc["marginal_unit"],
    }


def _retirements(base: Path, years) -> dict:
    agg = defaultdict(float)
    for y in years:
        p = base / f"evolution_{y}.json"
        if not p.exists():
            continue
        for e in json.loads(p.read_text())["retirements"]:
            agg[(e["fuel"], e["reason"])] += e["mw"]
    return {f"{f}/{r}": round(v, 1) for (f, r), v in sorted(agg.items())}


def main() -> None:
    bundle = Path(sys.argv[1])
    arm_base, arm_key = _arm_ledgers(bundle)
    res: dict = {"arm_bundle": str(bundle), "arm_key": arm_key}

    # ---- key guard: nothing downstream is read unless the arm is the arm ----
    res["key_matches_declared"] = arm_key == DECLARED_ARM_KEY
    if not res["key_matches_declared"]:
        res["STOP"] = f"realized key {arm_key} != declared {DECLARED_ARM_KEY}"
        print(json.dumps(res, indent=1))
        return

    ctl22, arm22 = _ledger(CONTROL_LEDGERS, 2022), _ledger(arm_base, 2022)

    # ---- G1 REACHABILITY ---------------------------------------------------
    ctl_p, arm_p = _screen_prices(ctl22), _screen_prices(arm22)
    res["G1_reachability"] = {
        "control_screen_prices": ctl_p,
        "arm_screen_prices": arm_p,
        "price_surface_moved": arm_p.get("max") != ctl_p.get("max")
        or arm_p.get("mean") != ctl_p.get("mean"),
        "PASS": bool(
            arm_p.get("n", 0) >= 0
            and (arm_p.get("max") != ctl_p.get("max") or arm_p.get("mean") != ctl_p.get("mean"))
        ),
    }

    # ---- G2 PRICE-SURFACE DIRECTION AND ORDER ------------------------------
    arm_max = arm_p.get("max")
    res["G2_price_surface"] = {
        "control_max_usd_mwh": CONTROL_SCREEN_PRICE_MAX,
        "arm_max_usd_mwh": arm_max,
        "direction_up": (arm_max is not None and arm_max >= CONTROL_SCREEN_PRICE_MAX),
        "floor_usd_mwh": G2_FLOOR_USD_MWH,
        "PASS": bool(arm_max is not None and arm_max >= G2_FLOOR_USD_MWH),
    }

    # ---- G3 THE OPERAND ----------------------------------------------------
    ctl_e, arm_e = _eas_per_accredited_mw_day(ctl22), _eas_per_accredited_mw_day(arm22)
    vals = [
        v["eas_per_accredited_mw_day"]
        for v in arm_e.values()
        if v["eas_per_accredited_mw_day"] is not None
    ]
    observed = max(vals) if vals else None
    res["G3_operand"] = {
        "control_by_fuel": ctl_e,
        "arm_by_fuel": arm_e,
        "arm_max_eas_per_accredited_mw_day": observed,
        "floor": G3_FLOOR_USD_PER_ACCREDITED_MW_DAY,
        "predicted_band": G3_PREDICTED_BAND,
        "predicted_mw_weighted_mean": G3_PREDICTED_MEAN,
        "in_predicted_band": (
            observed is not None and G3_PREDICTED_BAND[0] <= observed <= G3_PREDICTED_BAND[1]
        ),
        "PASS": bool(observed is not None and observed >= G3_FLOOR_USD_PER_ACCREDITED_MW_DAY),
        "NOTE": (
            "an EMPTY arm decided cohort is NOT a G3 failure by itself — it is the "
            "predicted outcome when the operand clears every unit off the failing "
            "set; read it with G5 and the clearing below."
        ),
    }

    # ---- G4 FOOTPRINT CONFINEMENT ------------------------------------------
    ctl_offer = {r[0]: r[2] for r in ctl22["capacity_clearing"]["offer_stack"]}
    arm_offer = {r[0]: r[2] for r in arm22["capacity_clearing"]["offer_stack"]}
    moved = {u for u in set(ctl_offer) & set(arm_offer) if abs(ctl_offer[u] - arm_offer[u]) > 1e-4}
    res["G4_footprint"] = {
        "units_in_both_stacks": len(set(ctl_offer) & set(arm_offer)),
        "units_only_in_control": len(set(ctl_offer) - set(arm_offer)),
        "units_only_in_arm": len(set(arm_offer) - set(ctl_offer)),
        "offers_moved": len(moved),
        "NOTE": (
            "a moved offer must be an E&AS change: the offer is "
            "max(0, GFC - EAS)/(A*365) and no other term in it is touched by the arm."
        ),
    }

    # ---- G5 I2 IDENTITY ----------------------------------------------------
    cc = arm22["capacity_clearing"]
    uncleared_ids = {r[0] for r in cc["offer_stack"] if not r[4]}
    failing_ids = {
        e["unit_id"] for e in arm22["pipeline_events"] if e["event"] == "decided"
    }
    marginal = cc.get("marginal_unit")
    res["G5_identity_I2"] = {
        "n_uncleared": len(uncleared_ids),
        "n_failing": len(failing_ids),
        "failing_not_uncleared": sorted(failing_ids - uncleared_ids - {marginal})[:10],
        "uncleared_not_failing": sorted(uncleared_ids - failing_ids - {marginal})[:10],
        "marginal_unit": marginal,
        "PASS": bool(
            not (failing_ids - uncleared_ids - {marginal})
        ),
    }

    # ---- the clearing, against the falsifiable point prediction ------------
    res["clearing_2022"] = {
        "control": _uncleared(ctl22),
        "arm": _uncleared(arm22),
        "predicted_from_phase0_C_delta40": PREDICTED_2022,
    }

    # ---- REPORTED AT FULL MAGNITUDE, GATING IN NEITHER DIRECTION -----------
    res["REPORTED_NOT_GATING"] = {
        "control_retirements_2021_2022": _retirements(CONTROL_LEDGERS, (2021, 2022)),
        "arm_retirements_2021_2022": _retirements(arm_base, (2021, 2022)),
        "RULE": (
            "rule 1 [R-STRUCT]: these are reported, never gating. A screen that "
            "read 'did unit_recall improve' would be the fitted-mechanism "
            "selection the rule forbids, done one year at a time."
        ),
    }

    gates = {k: v.get("PASS") for k, v in res.items() if k.startswith("G") and isinstance(v, dict)}
    res["GATES"] = gates
    res["VERDICT"] = (
        "SCREEN CLEARS — the arm may proceed to the full span"
        if all(v for v in gates.values() if v is not None)
        else "SCREEN KILLS THE ARM — reported as the session's result"
    )
    out = Path(__file__).with_name("screen-grade-2026-09-07.json")
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k in ("arm_key", "GATES", "VERDICT")}, indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
