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

DEFAULT_SCREEN_YEAR = 2022
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
    return {
        r[0]: (r[1], float(r[2]), float(r[3]), bool(r[4]))
        for r in clearing.get("offer_stack", [])
    }


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
    ap.add_argument(
        "--screen-year",
        type=int,
        default=DEFAULT_SCREEN_YEAR,
        help="The DY the G1-G6 gate table is graded on (PRECOMMIT §3).",
    )
    args = ap.parse_args()
    SCREEN_YEAR = args.screen_year

    ctl = find_ledgers(args.ctl)
    arm = find_ledgers(args.arm)
    p0 = json.loads(args.phase0.read_text())
    dated = {u["unit_id"]: u for u in p0["years"][str(SCREEN_YEAR)]["units"]}

    y = SCREEN_YEAR
    if y not in ctl or y not in arm:
        raise SystemExit(
            f"screen year {y} missing: ctl {sorted(ctl)} arm {sorted(arm)}"
        )
    c_led, a_led = ctl[y], arm[y]
    c_cl = c_led.get("capacity_clearing") or {}
    a_cl = a_led.get("capacity_clearing") or {}
    if not c_cl or not a_cl:
        raise SystemExit(
            "capacity_clearing block absent — the D57 clearing did not arm"
        )

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
            float(cl["price_takers_mw"])
            + float(cl["offered_mw"])
            - float(cl["census_mw"]),
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
            and abs(float(c_cl["requirement_mw"]) - float(a_cl["requirement_mw"]))
            <= MW_TOL
            and abs(float(c_cl["census_mw"]) - float(a_cl["census_mw"])) <= MW_TOL
            and abs(float(c_cl["census_position"]) - float(a_cl["census_position"]))
            <= PRICE_TOL
        ),
    }

    # A shared row is "identical" only if its fuel, offer, accredited MW AND
    # ITS CLEARED FLAG all match. The cleared flag was MISSING from this
    # comparison until the full window was read (FINDING §5.2): the mechanism's
    # real effect is a re-composition of the marginal tie band, which is
    # invisible to a fuel/offer/A_g comparison. Repaired STRICTLY — the gate now
    # catches a difference it previously passed over — and reported as the third
    # instrument defect rather than silently fixed.
    shared_mismatch = [
        u
        for u in shared
        if c_stack[u][0] != a_stack[u][0]
        or abs(c_stack[u][1] - a_stack[u][1]) > OFFER_TOL
        or abs(c_stack[u][2] - a_stack[u][2]) > MW_TOL
        or c_stack[u][3] != a_stack[u][3]
    ]
    cleared_flips = [u for u in shared if c_stack[u][3] != a_stack[u][3]]
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
        "n_shared_cleared_flag_flips": len(cleared_flips),
        "shared_cleared_flag_flips": cleared_flips[:20],
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
        "price_usd_per_mw_day": [
            c_cl["price_usd_per_mw_day"],
            a_cl["price_usd_per_mw_day"],
        ],
        "cleared_position": [c_cl["cleared_position"], a_cl["cleared_position"]],
        "cleared_mw": [c_cl["cleared_mw"], a_cl["cleared_mw"]],
        "how": [c_cl.get("how"), a_cl.get("how")],
        "marginal_unit": [c_cl.get("marginal_unit"), a_cl.get("marginal_unit")],
        "pass": (
            float(a_cl["price_usd_per_mw_day"])
            >= float(c_cl["price_usd_per_mw_day"]) - PRICE_TOL
            and float(a_cl["cleared_position"])
            <= float(c_cl["cleared_position"]) + PRICE_TOL
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

    # --- DIAGNOSIS (PRECOMMIT Addendum A) ---------------------------------
    # The literal G1 / G4 gates above are reported verbatim and are NEVER
    # rewritten to fit a result. This block is the SEPARATE, per-year
    # re-measurement that says whether a literal miss is the MECHANISM or the
    # INSTRUMENT, and it is declared in Addendum A before the full window runs.
    #
    #  * G1's tolerance (±0.001 MW) was specified for one rounded quantity, but
    #    the comparand is a SUM of n rows each rounded to 3 dp by
    #    ``CapacityClearing.as_ledger``, so the achievable bound is n × 0.0005
    #    MW, not 0.001. The identity the gate exists to test —
    #    ``Δoffered == Δprice_takers`` — is checked here with no tolerance at
    #    all, on the ledger's own digits.
    #  * G4 asked whether the SCREEN YEAR's block appears in ANY year's
    #    decision rows. A plant whose last pending row COMPLETES re-enters the
    #    screen as an undated residual plant in the following year (the
    #    documented behaviour of ``dated_plant_unit_ids``), where facing the
    #    decision is correct. The per-year question — year Y's block against
    #    year Y's decision rows — is the one that tests the mechanism.
    diagnosis: dict[str, dict] = {}
    for yy in sorted(set(ctl) & set(arm)):
        blk_rows = (p0["years"].get(str(yy)) or {}).get("units")
        if blk_rows is None:
            continue
        blk = {u["unit_id"] for u in blk_rows}
        cc = ctl[yy].get("capacity_clearing") or {}
        ac = arm[yy].get("capacity_clearing") or {}
        if not cc or not ac:
            continue
        cs, as_ = stack_rows(ctl[yy]), stack_rows(arm[yy])
        add = sorted(set(as_) - set(cs))
        drop = sorted(set(cs) - set(as_))
        sh = sorted(set(as_) & set(cs))
        mism = [
            u
            for u in sh
            if cs[u][0] != as_[u][0]
            or abs(cs[u][1] - as_[u][1]) > OFFER_TOL
            or abs(cs[u][2] - as_[u][2]) > MW_TOL
        ]
        d_off = round(float(ac["offered_mw"]) - float(cc["offered_mw"]), 3)
        d_pt = round(float(cc["price_takers_mw"]) - float(ac["price_takers_mw"]), 3)
        sum_a = round(sum(as_[u][2] for u in add), 3)
        diagnosis[str(yy)] = {
            "phase0_block_units": len(blk),
            "phase0_block_accredited_mw": (p0["years"][str(yy)])[
                "offering_accredited_mw"
            ],
            "stack_rows_added": len(add),
            "stack_rows_dropped": len(drop),
            "added_all_in_block": not [u for u in add if u not in blk],
            "shared_rows": len(sh),
            "shared_rows_not_identical": len(mism),
            "d_offered_mw": d_off,
            "d_price_takers_mw": d_pt,
            "conservation_exact_on_ledger_digits": d_off == d_pt,
            "sum_added_accredited_mw": sum_a,
            "sum_vs_total_residual_mw": round(abs(d_off - sum_a), 6),
            "rounding_bound_mw": round(len(add) * 0.0005, 4),
            "within_rounding_bound": abs(d_off - sum_a) <= len(add) * 0.0005,
            "block_cleared_mw": round(
                sum(as_[u][2] for u in blk if u in as_ and as_[u][3]), 3
            ),
            "block_uncleared_mw": round(
                sum(as_[u][2] for u in blk if u in as_ and not as_[u][3]), 3
            ),
            "merchant_rows_flipped_to_cleared": len(
                [u for u in sh if not cs[u][3] and as_[u][3]]
            ),
            "merchant_rows_flipped_to_uncleared": len(
                [u for u in sh if cs[u][3] and not as_[u][3]]
            ),
            "merchant_flipped_accredited_mw": round(
                sum(as_[u][2] for u in sh if cs[u][3] != as_[u][3]), 3
            ),
            "cleared_mw": [cc["cleared_mw"], ac["cleared_mw"]],
            "n_uncleared": [cc["n_uncleared"], ac["n_uncleared"]],
            "marginal_unit": [cc.get("marginal_unit"), ac.get("marginal_unit")],
            "pipeline_rows": [
                len(ctl[yy].get("pipeline_events") or []),
                len(arm[yy].get("pipeline_events") or []),
            ],
            "block_units_in_SAME_year_decision_rows": {
                "ctl": len(decision_unit_ids(ctl[yy]) & blk),
                "arm": len(decision_unit_ids(arm[yy]) & blk),
            },
            "price_usd_per_mw_day": [
                cc["price_usd_per_mw_day"],
                ac["price_usd_per_mw_day"],
            ],
            "cleared_position": [cc["cleared_position"], ac["cleared_position"]],
            "census_mw": [cc["census_mw"], ac["census_mw"]],
            "economic_retirement_mw": [economic_mw(ctl[yy]), economic_mw(arm[yy])],
        }

    out = {
        "screen_year": SCREEN_YEAR,
        "legs": {"ctl": str(args.ctl), "arm": str(args.arm)},
        "diagnosis_by_year": diagnosis,
        "years": {"ctl": sorted(ctl), "arm": sorted(arm)},
        "clearing": {
            "ctl": {
                k: c_cl.get(k)
                for k in (
                    "n_offers",
                    "offered_mw",
                    "price_takers_mw",
                    "census_mw",
                    "requirement_mw",
                    "price_usd_per_mw_day",
                    "cleared_mw",
                    "cleared_position",
                    "census_position",
                    "n_uncleared",
                    "how",
                )
            },
            "arm": {
                k: a_cl.get(k)
                for k in (
                    "n_offers",
                    "offered_mw",
                    "price_takers_mw",
                    "census_mw",
                    "requirement_mw",
                    "price_usd_per_mw_day",
                    "cleared_mw",
                    "cleared_position",
                    "census_position",
                    "n_uncleared",
                    "how",
                )
            },
        },
        "phase0_block_accredited_mw": p0["years"][str(SCREEN_YEAR)][
            "offering_accredited_mw"
        ],
        "gates": gates,
        "verdict": "PASS" if all(g["pass"] for g in gates.values()) else "STOP",
    }
    args.out.write_text(json.dumps(out, indent=2, default=str) + "\n")
    for name, g in gates.items():
        print(f"{name}: {'PASS' if g['pass'] else 'FAIL'}  — {g['question']}")
    print(f"VERDICT {out['verdict']}  -> {args.out}")


if __name__ == "__main__":
    main()
