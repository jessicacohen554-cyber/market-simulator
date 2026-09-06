"""capx D81 — grade the rule-29 screen gates G1-G6 (PRECOMMIT §3) from the two
legs' committed evolution ledgers. Zero LP, read-only.

Usage:
    uv run python docs/handoffs/d81/screen_compare.py \
        --ctl results/hindcast/pjm-2021-2023-realized-t1h-d81-control \
        --arm results/hindcast/pjm-2021-2023-realized-t1h-d81-arm \
        --phase0 docs/handoffs/d81/phase0_dated_block.json \
        --out docs/handoffs/d81/screen_compare.json

Every gate is STRUCTURAL and STOP-only: it may kill the arm, never promote it.
No gate reads retire.total_gw, false_retire, recall, precision or any residual.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402

SCREEN_YEAR = 2022
MW_TOL = 1e-3
OFFER_TOL = 1e-4
PRICE_TOL = 1e-6

# G6's "identical unless the mechanism claims it" key set.
G6_KEYS = (
    "announced_derates",
    "confirmed_derates",
    "ccs_retrofits",
    "sector_gated",
    "no_default_cap_price_takers",
    "peak_demand_mw",
    "screen_peak_demand_mw",
    "screen_adequacy_requirement_mw",
)


def find_ledgers(root: Path) -> dict[int, dict]:
    """Locate the run's ledgers under an --out-dir (CACHE_ROOT is the out-dir)."""
    direct = load_ledgers_for_run(root)
    if direct:
        return direct
    for p in sorted(root.rglob("evolution_*.json")):
        return load_ledgers_for_run(p.parent)
    raise SystemExit(f"no evolution_*.json under {root}")


def stack_rows(ledger: dict) -> dict[str, tuple]:
    """``{unit_id: (fuel, offer, accredited_mw, cleared)}`` from ``offer_stack``."""
    clearing = ledger.get("capacity_clearing") or {}
    return {r[0]: (r[1], float(r[2]), float(r[3]), bool(r[4])) for r in clearing.get("offer_stack", [])}


def decision_unit_ids(ledger: dict) -> set[str]:
    """Every unit id the year's ledger puts into a DECISION structure."""
    out: set[str] = set()
    for row in ledger.get("pipeline_events", []) or []:
        uid = row.get("unit_id") if isinstance(row, dict) else None
        if uid:
            out.add(str(uid))
    for row in ledger.get("retirements", []) or []:
        if isinstance(row, dict) and row.get("unit_id"):
            out.add(str(row["unit_id"]))
    for row in ledger.get("floor_retained", []) or []:
        if isinstance(row, dict) and row.get("unit_id"):
            out.add(str(row["unit_id"]))
    return out


def exogenous_retirements(ledger: dict) -> list:
    """The step-0/1/1b retirement rows — the ones the mechanism must not move."""
    return sorted(
        (
            (r.get("unit_id"), r.get("reason"), round(float(r.get("mw") or 0.0), 3))
            for r in (ledger.get("retirements") or [])
            if isinstance(r, dict) and r.get("reason") in ("confirmed", "announced")
        )
    )


def economic_mw(ledger: dict) -> float:
    return round(
        sum(
            float(r.get("mw") or 0.0)
            for r in (ledger.get("retirements") or [])
            if isinstance(r, dict) and r.get("reason") == "economic"
        ),
        3,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ctl", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--phase0", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    ctl = find_ledgers(args.ctl)
    arm = find_ledgers(args.arm)
    p0 = json.loads(args.phase0.read_text())
    dated = {
        u["unit_id"]: u for u in p0["years"][str(SCREEN_YEAR)]["units"]
    }

    y = SCREEN_YEAR
    if y not in ctl or y not in arm:
        raise SystemExit(f"screen year {y} missing: ctl {sorted(ctl)} arm {sorted(arm)}")
    c_led, a_led = ctl[y], arm[y]
    c_cl = c_led.get("capacity_clearing") or {}
    a_cl = a_led.get("capacity_clearing") or {}
    if not c_cl or not a_cl:
        raise SystemExit("capacity_clearing block absent — the D57 clearing did not arm")

    c_stack, a_stack = stack_rows(c_led), stack_rows(a_led)
    added = sorted(set(a_stack) - set(c_stack))
    dropped = sorted(set(c_stack) - set(a_stack))
    shared = sorted(set(a_stack) & set(c_stack))
    added_mw = round(sum(a_stack[u][2] for u in added), 3)

    d_offered = round(float(a_cl["offered_mw"]) - float(c_cl["offered_mw"]), 3)
    d_takers = round(float(c_cl["price_takers_mw"]) - float(a_cl["price_takers_mw"]), 3)
    d_offers = int(a_cl["n_offers"]) - int(c_cl["n_offers"])

    gates: dict[str, dict] = {}

    gates["G1"] = {
        "question": "conservation, to the MW",
        "d_offered_mw": d_offered,
        "d_price_takers_mw": d_takers,
        "added_stack_accredited_mw": added_mw,
        "d_n_offers": d_offers,
        "n_added_units": len(added),
        "pass": (
            abs(d_offered - d_takers) <= MW_TOL
            and abs(d_offered - added_mw) <= MW_TOL
            and d_offers == len(added)
            and len(added) <= len(dated)
        ),
    }

    def _i1(cl):
        return round(
            float(cl["price_takers_mw"]) + float(cl["offered_mw"]) - float(cl["census_mw"]),
            6,
        )

    gates["G2"] = {
        "question": "invariant I1 and the unmoved denominators",
        "i1_residual_ctl_mw": _i1(c_cl),
        "i1_residual_arm_mw": _i1(a_cl),
        "requirement_mw": [c_cl["requirement_mw"], a_cl["requirement_mw"]],
        "census_mw": [c_cl["census_mw"], a_cl["census_mw"]],
        "census_position": [c_cl["census_position"], a_cl["census_position"]],
        "pass": (
            abs(_i1(c_cl)) <= MW_TOL
            and abs(_i1(a_cl)) <= MW_TOL
            and abs(float(c_cl["requirement_mw"]) - float(a_cl["requirement_mw"])) <= MW_TOL
            and abs(float(c_cl["census_mw"]) - float(a_cl["census_mw"])) <= MW_TOL
            and abs(float(c_cl["census_position"]) - float(a_cl["census_position"])) <= PRICE_TOL
        ),
    }

    shared_mismatch = [
        u
        for u in shared
        if c_stack[u][0] != a_stack[u][0]
        or abs(c_stack[u][1] - a_stack[u][1]) > OFFER_TOL
        or abs(c_stack[u][2] - a_stack[u][2]) > MW_TOL
    ]
    non_dated_added = [u for u in added if u not in dated]
    gates["G3"] = {
        "question": "footprint confined to the rows the mechanism claims",
        "added_units": len(added),
        "added_not_in_phase0_block": non_dated_added[:20],
        "n_added_not_in_block": len(non_dated_added),
        "dropped_units": dropped[:20],
        "n_dropped": len(dropped),
        "phase0_block_units": len(dated),
        "block_units_absent_from_arm_stack": sorted(set(dated) - set(a_stack))[:20],
        "shared_rows": len(shared),
        "shared_rows_not_byte_identical": shared_mismatch[:20],
        "n_shared_mismatch": len(shared_mismatch),
        "pass": (
            not non_dated_added and not dropped and not shared_mismatch and bool(added)
        ),
    }

    impure = {}
    for leg, leds in (("ctl", ctl), ("arm", arm)):
        hits = {}
        for yy, led in leds.items():
            bad = sorted(decision_unit_ids(led) & set(dated))
            if bad:
                hits[str(yy)] = bad[:20]
        impure[leg] = hits
    gates["G4"] = {
        "question": "decision purity — the block is out of the decision in BOTH legs",
        "dated_units_in_decision_structures": impure,
        "pass": not impure["ctl"] and not impure["arm"],
    }

    gates["G5"] = {
        "question": "direction (D54 §4.2's stated bias, reversed)",
        "price_usd_per_mw_day": [c_cl["price_usd_per_mw_day"], a_cl["price_usd_per_mw_day"]],
        "cleared_position": [c_cl["cleared_position"], a_cl["cleared_position"]],
        "cleared_mw": [c_cl["cleared_mw"], a_cl["cleared_mw"]],
        "how": [c_cl.get("how"), a_cl.get("how")],
        "marginal_unit": [c_cl.get("marginal_unit"), a_cl.get("marginal_unit")],
        "pass": (
            float(a_cl["price_usd_per_mw_day"]) >= float(c_cl["price_usd_per_mw_day"]) - PRICE_TOL
            and float(a_cl["cleared_position"]) <= float(c_cl["cleared_position"]) + PRICE_TOL
        ),
    }

    g6_diffs: dict[str, list[str]] = {}
    for yy in sorted(set(ctl) & set(arm)):
        bad = [k for k in G6_KEYS if ctl[yy].get(k) != arm[yy].get(k)]
        if exogenous_retirements(ctl[yy]) != exogenous_retirements(arm[yy]):
            bad.append("retirements[confirmed|announced]")
        if yy == min(set(ctl) & set(arm)) and ctl[yy] != arm[yy]:
            bad.append("base-year ledger not identical")
        if bad:
            g6_diffs[str(yy)] = bad
    gates["G6"] = {
        "question": "no non-target flip",
        "differing_blocks_by_year": g6_diffs,
        "reported_not_gated": {
            str(yy): {
                "economic_retirement_mw": [economic_mw(ctl[yy]), economic_mw(arm[yy])],
                "thermal_additions": [
                    len(ctl[yy].get("thermal_additions") or []),
                    len(arm[yy].get("thermal_additions") or []),
                ],
            }
            for yy in sorted(set(ctl) & set(arm))
        },
        "pass": not g6_diffs,
    }

    out = {
        "screen_year": SCREEN_YEAR,
        "legs": {"ctl": str(args.ctl), "arm": str(args.arm)},
        "years": {"ctl": sorted(ctl), "arm": sorted(arm)},
        "clearing": {
            "ctl": {k: c_cl.get(k) for k in ("n_offers", "offered_mw", "price_takers_mw", "census_mw", "requirement_mw", "price_usd_per_mw_day", "cleared_mw", "cleared_position", "census_position", "n_uncleared", "how")},
            "arm": {k: a_cl.get(k) for k in ("n_offers", "offered_mw", "price_takers_mw", "census_mw", "requirement_mw", "price_usd_per_mw_day", "cleared_mw", "cleared_position", "census_position", "n_uncleared", "how")},
        },
        "phase0_block_accredited_mw": p0["years"][str(SCREEN_YEAR)]["offering_accredited_mw"],
        "gates": gates,
        "verdict": "PASS" if all(g["pass"] for g in gates.values()) else "STOP",
    }
    args.out.write_text(json.dumps(out, indent=2, default=str) + "\n")
    for name, g in gates.items():
        print(f"{name}: {'PASS' if g['pass'] else 'FAIL'}  — {g['question']}")
    print(f"VERDICT {out['verdict']}  -> {args.out}")


if __name__ == "__main__":
    main()
