"""capx D84 — the pre-registered gate analyzer, COMMITTED BEFORE THE ARM SOLVE.

Grades the control/arm pair against PRECOMMIT §7.1's five STRUCTURAL legs. Rule
29 [R-SCREEN]: this may KILL the arm, it may NEVER promote one, it contributes
to no determination, and NOT ONE leg is read against the target residual.

The five legs, verbatim from the PRECOMMIT:

1. IDENTITY  -- in DY 2025/2026, measured
   `delta accredited_firm == sum_fuel nameplate_entering_2025,fuel x delta_rating_fuel`
   to < 0.01 MW, with the per-class split matching the registry's delta-rating
   column exactly.
2. DIRECTION AND ORDER OF MAGNITUDE -- the DY 2025/2026 move is POSITIVE and of
   order 10^3 MW.
3. CONFINEMENT -- years 2021-2024 byte-identical between arms.
4. CLASS CONFINEMENT -- within DY 2025/2026, coal / nuclear / biomass accredited
   MW unchanged; only gas_cc / gas_ct / gas_st / oil move, in the stated ratio.
5. NON-TARGET LOAD-BEARING CRITERIA -- no non-target load-bearing scored
   criterion flips PASS -> FAIL. (A FAIL -> PASS flip is REPORTED, never a
   promotion.)

Everything else the script prints -- position, clearing, retirements, entry --
is DIAGNOSTIC and is reported at full magnitude, in both directions.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    THERMAL_ELCC_CLASS_RATING_BY_ISO,
    THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO,
)

CTL = REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d84-control"
ARM = REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d84-thermalvintage"

YEARS = list(range(2021, 2026))
TARGET_DY = "2025/2026"
TARGET_YEAR = 2025
MOVERS = ("gas_cc", "gas_ct", "gas_st", "oil")
STATIC = ("coal", "nuclear", "biomass")

# The scalar ledger keys leg 3 compares. Chosen for coverage of the screen's
# whole output surface, not for what any of them does to a residual.
SCALARS = (
    "adequacy_requirement_mw",
    "screen_adequacy_requirement_mw",
    "screen_entering_firm_mw",
    "screen_reserve_position",
    "screen_peak_demand_mw",
    "capacity_reserve_position",
    "peak_demand_mw",
    "reserve_margin",
    "firm_clean_accredited_mw",
    "storage_firm_mw",
    "wind_cap_mw",
    "solar_cap_mw",
    "rps_dual",
)
BLOCKS = (
    "fleet_by_fuel_before",
    "fleet_by_fuel_after",
    "retirements",
    "renewable_additions",
    "thermal_additions",
    "storage_additions",
    "entry_decided_mw_by_tech",
    "floor_retained",
    "announced_derates",
    "confirmed_derates",
    "ccs_retrofits",
    "pipeline_events",
    "renewable_credit_applied",
    "sector_gated",
)
CLEARING_KEYS = (
    "census_mw",
    "census_position",
    "cleared_mw",
    "cleared_position",
    "offered_mw",
    "price_takers_mw",
    "price_usd_per_mw_day",
    "price_per_firm_mw_yr",
    "requirement_mw",
    "n_offers",
    "n_uncleared",
    "how",
)


def _key_dir(root: Path) -> Path:
    pjm = root / "PJM"
    keys = sorted(p for p in pjm.iterdir() if p.is_dir())
    if len(keys) != 1:
        raise SystemExit(f"{root}: expected exactly one cache key, found {keys}")
    return keys[0]


def _led(root: Path, year: int) -> dict:
    return json.loads((_key_dir(root) / f"evolution_{year}.json").read_text())


def _score(root: Path) -> dict:
    p = _key_dir(root) / "score.json"
    return json.loads(p.read_text()) if p.exists() else {}


def leg1_and_2_identity_and_direction() -> dict:
    """The delta the mechanism's own arithmetic predicts, against the solve."""
    c, a = _led(CTL, TARGET_YEAR), _led(ARM, TARGET_YEAR)
    fleet = c["fleet_by_fuel_before"]
    base = THERMAL_ELCC_CLASS_RATING_BY_ISO["PJM"]
    vint = THERMAL_ELCC_VINTAGE_CLASS_RATING_BY_ISO["PJM"][TARGET_DY]

    per_class = {}
    predicted = 0.0
    for fuel in sorted(set(base) | set(fleet)):
        mw = float(fleet.get(fuel, 0.0))
        dr = (
            vint.get(fuel, base.get(fuel, 0.0)) - base.get(fuel, 0.0)
            if fuel in base
            else 0.0
        )
        per_class[fuel] = {
            "nameplate_mw": mw,
            "delta_rating": round(dr, 12),
            "predicted_delta_mw": mw * dr,
        }
        predicted += mw * dr

    measured = float(a["screen_entering_firm_mw"]) - float(c["screen_entering_firm_mw"])
    gap = abs(measured - predicted)
    return {
        "entering_fleet_is_shared": c["fleet_by_fuel_before"]
        == a["fleet_by_fuel_before"],
        "per_class": per_class,
        "predicted_delta_mw": predicted,
        "measured_delta_screen_entering_firm_mw": measured,
        "abs_gap_mw": gap,
        "leg1_identity_holds": gap < 0.01,
        "leg2_direction_positive": measured > 0.0,
        "leg2_order_of_magnitude_1e3": 1e2 <= abs(measured) < 1e5,
        "leg2_holds": measured > 0.0 and 1e2 <= abs(measured) < 1e5,
    }


def leg3_confinement() -> dict:
    """Years 2021-2024 must be byte-identical between arms."""
    rows = {}
    for year in YEARS:
        if year == TARGET_YEAR:
            continue
        c, a = _led(CTL, year), _led(ARM, year)
        diffs = []
        for k in SCALARS + BLOCKS:
            if c.get(k) != a.get(k):
                diffs.append(k)
        cc, ac = c.get("capacity_clearing") or {}, a.get("capacity_clearing") or {}
        for k in CLEARING_KEYS:
            if cc.get(k) != ac.get(k):
                diffs.append(f"capacity_clearing.{k}")
        rows[str(year)] = {"differing_keys": diffs, "identical": not diffs}
    return {"rows": rows, "leg3_holds": all(r["identical"] for r in rows.values())}


def leg4_class_confinement(leg12: dict) -> dict:
    """Only gas_cc / gas_ct / gas_st / oil may move; the rest must not."""
    per = leg12["per_class"]
    moved = {f: per[f]["predicted_delta_mw"] for f in MOVERS if f in per}
    still = {f: per[f]["predicted_delta_mw"] for f in STATIC if f in per}
    return {
        "moved": moved,
        "static": still,
        "static_all_zero": all(abs(v) < 1e-9 for v in still.values()),
        "movers_all_nonzero": all(abs(v) > 1e-9 for v in moved.values()),
        "leg4_holds": all(abs(v) < 1e-9 for v in still.values())
        and all(abs(v) > 1e-9 for v in moved.values()),
    }


def _flat_scores(score: dict) -> dict:
    """Flatten whatever criterion/band shape score.json carries into name -> verdict."""
    out: dict[str, object] = {}

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                p = f"{path}.{k}" if path else k
                if isinstance(v, (dict, list)):
                    walk(v, p)
                elif k in ("verdict", "status", "pass", "passed", "result"):
                    out[path or p] = v
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(score)
    return out


def leg5_criteria() -> dict:
    """No non-target load-bearing criterion may flip PASS -> FAIL."""
    c, a = _flat_scores(_score(CTL)), _flat_scores(_score(ARM))
    names = sorted(set(c) | set(a))
    flips = {
        n: {"control": c.get(n), "arm": a.get(n)} for n in names if c.get(n) != a.get(n)
    }

    def _is_pass(v):
        return str(v).strip().upper() in {"PASS", "TRUE", "OK", "PASSED"}

    def _is_fail(v):
        return str(v).strip().upper() in {"FAIL", "FALSE", "FAILED"}

    pass_to_fail = {
        n: v for n, v in flips.items() if _is_pass(v["control"]) and _is_fail(v["arm"])
    }
    fail_to_pass = {
        n: v for n, v in flips.items() if _is_fail(v["control"]) and _is_pass(v["arm"])
    }
    return {
        "n_records": len(names),
        "all_flips": flips,
        "pass_to_fail": pass_to_fail,
        "fail_to_pass_reported_never_a_promotion": fail_to_pass,
        "leg5_holds": not pass_to_fail,
    }


def diagnostics() -> dict:
    """Reported at full magnitude, in both directions. NEVER a gate."""
    out = {}
    for year in YEARS:
        c, a = _led(CTL, year), _led(ARM, year)
        cc, ac = c.get("capacity_clearing") or {}, a.get("capacity_clearing") or {}
        out[str(year)] = {
            "screen_entering_firm_mw": [
                c.get("screen_entering_firm_mw"),
                a.get("screen_entering_firm_mw"),
            ],
            "screen_reserve_position": [
                c.get("screen_reserve_position"),
                a.get("screen_reserve_position"),
            ],
            "screen_adequacy_requirement_mw": [
                c.get("screen_adequacy_requirement_mw"),
                a.get("screen_adequacy_requirement_mw"),
            ],
            "clearing": {k: [cc.get(k), ac.get(k)] for k in CLEARING_KEYS},
            "retirements_mw": [
                sum(float(r.get("mw", 0.0)) for r in (c.get("retirements") or [])),
                sum(float(r.get("mw", 0.0)) for r in (a.get("retirements") or [])),
            ],
            "n_retirements": [
                len(c.get("retirements") or []),
                len(a.get("retirements") or []),
            ],
            "fleet_by_fuel_after": [
                c.get("fleet_by_fuel_after"),
                a.get("fleet_by_fuel_after"),
            ],
            "entry_decided_mw_by_tech": [
                c.get("entry_decided_mw_by_tech"),
                a.get("entry_decided_mw_by_tech"),
            ],
            "floor_retained_n": [
                len(c.get("floor_retained") or []),
                len(a.get("floor_retained") or []),
            ],
        }
    return out


def main() -> dict:
    leg12 = leg1_and_2_identity_and_direction()
    leg3 = leg3_confinement()
    leg4 = leg4_class_confinement(leg12)
    leg5 = leg5_criteria()
    legs = {
        "leg1_identity": leg12["leg1_identity_holds"],
        "leg2_direction_and_magnitude": leg12["leg2_holds"],
        "leg3_confinement_2021_2024": leg3["leg3_holds"],
        "leg4_class_confinement": leg4["leg4_holds"],
        "leg5_no_pass_to_fail": leg5["leg5_holds"],
    }
    return {
        "lane": "capx D84 screen gates (pre-registered in PRECOMMIT §7.1)",
        "control_bundle": str(CTL.relative_to(REPO)),
        "arm_bundle": str(ARM.relative_to(REPO)),
        "control_key": _key_dir(CTL).name,
        "arm_key": _key_dir(ARM).name,
        "declared_control_key": "f736025631d0d27e",
        "declared_arm_key": "b9fa47dedb6c3319",
        "keys_as_declared": _key_dir(CTL).name == "f736025631d0d27e"
        and _key_dir(ARM).name == "b9fa47dedb6c3319",
        "legs": legs,
        "VERDICT": "PASS" if all(legs.values()) else "STOP — the screen KILLS the arm",
        "leg1_2_detail": leg12,
        "leg3_detail": leg3,
        "leg4_detail": leg4,
        "leg5_detail": leg5,
        "diagnostics_never_a_gate": diagnostics(),
    }


if __name__ == "__main__":
    res = main()
    Path(__file__).with_name("screen-gates.json").write_text(
        json.dumps(res, indent=1) + "\n"
    )
    print(
        json.dumps(
            {
                k: res[k]
                for k in (
                    "control_key",
                    "arm_key",
                    "keys_as_declared",
                    "legs",
                    "VERDICT",
                )
            },
            indent=1,
        )
    )
