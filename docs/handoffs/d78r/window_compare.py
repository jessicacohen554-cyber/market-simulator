"""capx D78-R full-window differencing — control-P vs the repaired arm over
2021-2025, read off the two bundles' committed ledgers and ``score.json``.
Zero LP. Grades the PRECOMMIT §3 gates W0-W5, computes the §3.3 W4 band from
the CONTROL leg alone, and writes every number the FINDING cites (rule 29(c):
the control bundle is deleted before merge; this JSON and the FINDING are the
record).

    # after control-P, BEFORE the arm — the §3.3 addendum band:
    uv run python docs/handoffs/d78r/window_compare.py --ctl <ctl-dir> --band-only

    # after both legs — the full grade:
    uv run python docs/handoffs/d78r/window_compare.py --ctl <ctl-dir> --arm <arm-dir>

The sector map is the EIA-860 2020-vintage plant table (the gate's own key,
``plant_code``), joined exactly as D78's ``screen_compare.py`` did — which this
module imports rather than re-implements, so the two lanes cannot drift.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "d78"))

from screen_compare import (  # noqa: E402  (path-inserted above)
    FOOTPRINT_KEYS,
    bundle_dir,
    fail_rows,
    ledger,
    sector_of,
    sectors,
    stack_diff,
    stack_rows,
)

YEARS = (2021, 2022, 2023, 2024, 2025)

# D78's measured 2022 screen (FINDING-capx-d78 §2, §3.1, §4) — the W0 known
# answers. The full window re-solves 2021->2022 on a path identical to D78's
# screen span, so these must come back to the digit on BOTH legs.
D78_2022 = {
    "ctl": {
        "failing_rows": 677,
        "failing_mw": 29727.898,
        "n_offers": 1370,
        "offered_mw": 150857.184,
        "price_takers_mw": 30577.888,
        "price": 67.760162,
        "decided_rows": 79,
        "decided_mw": 13177.472,
        "executed_mw": 7333.7,
    },
    "arm": {
        "failing_rows": 451,
        "failing_mw": 26251.375,
        "n_offers": 1370,
        "offered_mw": 150857.184,
        "price_takers_mw": 30577.888,
        "price": 67.760162,
        "decided_rows": 128,
        "decided_mw": 13354.701,
        "executed_mw": 8736.687,
    },
}
MW_TOL = 0.001
PRICE_TOL = 1e-6


# --------------------------------------------------------------------------
# ledger readers
# --------------------------------------------------------------------------
def events(led: dict, kind: str) -> dict[str, float]:
    return {
        e["unit_id"]: float(e.get("mw") or 0.0)
        for e in led.get("pipeline_events") or []
        if e.get("event") == kind
    }


def econ_exits(led: dict) -> dict[str, float]:
    return {
        r["unit_id"]: float(r.get("mw") or 0.0)
        for r in led.get("retirements") or []
        if r.get("reason") == "economic"
    }


def all_exits(led: dict) -> dict[str, float]:
    return {
        r["unit_id"]: float(r.get("mw") or 0.0) for r in led.get("retirements") or []
    }


def by_sector(rows: dict[str, float], sec) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"rows": 0, "mw": 0.0})
    for uid, mw in rows.items():
        s = out[sector_of(uid, sec)]
        s["rows"] += 1
        s["mw"] += mw
    return {k: {"rows": v["rows"], "mw": round(v["mw"], 3)} for k, v in sorted(out.items())}


def load_legs(out_dir: Path) -> dict[int, dict]:
    b = bundle_dir(out_dir)
    return {y: led for y in YEARS if (led := ledger(b, y)) is not None}


# --------------------------------------------------------------------------
# per-year summary
# --------------------------------------------------------------------------
def summarise(leds: dict[int, dict], sec) -> dict:
    out: dict[str, dict] = {}
    for y, led in leds.items():
        cc = led.get("capacity_clearing") or {}
        pool = fail_rows(led)
        dec, cap = events(led, "decided"), events(led, "entry_capped")
        econ = econ_exits(led)
        stack = stack_rows(led)
        s1_stack = [r for u, r in stack.items() if sector_of(u, sec) == "1"]
        out[str(y)] = {
            "pool_rows": len(pool),
            "pool_mw": round(sum(pool.values()), 3),
            "pool_by_sector": by_sector(pool, sec),
            "pool_max_row_mw": round(max(pool.values()), 3) if pool else 0.0,
            "decided_rows": len(dec),
            "decided_mw": round(sum(dec.values()), 3),
            "decided_by_sector": by_sector(dec, sec),
            "capped_rows": len(cap),
            "capped_mw": round(sum(cap.values()), 3),
            "capped_by_sector": by_sector(cap, sec),
            "executed_economic_rows": len(econ),
            "executed_economic_mw": round(sum(econ.values()), 3),
            "executed_economic_by_sector": by_sector(econ, sec),
            "retirements_all_mw": round(sum(all_exits(led).values()), 3),
            "floor_retained_mw": round(
                sum(events(led, "floor_retained").values()), 3
            ),
            "throughput_deferred_mw": round(
                sum(events(led, "throughput_deferred").values()), 3
            ),
            "sector1_pipeline_rows": sum(
                1
                for e in (led.get("pipeline_events") or [])
                if sector_of(e["unit_id"], sec) == "1"
            ),
            "unknown_pipeline_rows": sum(
                1
                for e in (led.get("pipeline_events") or [])
                if sector_of(e["unit_id"], sec) == "unknown"
            ),
            "clearing": {k: v for k, v in cc.items() if not isinstance(v, (list, dict))},
            "uncleared_mw_by_fuel": cc.get("uncleared_mw_by_fuel"),
            "sector1_in_stack": {
                "units": len(s1_stack),
                "accredited_mw": round(sum(r[3] for r in s1_stack), 3),
            },
            "sector_gated": led.get("sector_gated"),
            "footprint": {k: led.get(k) for k in FOOTPRINT_KEYS},
        }
    return out


# --------------------------------------------------------------------------
# W4 — the band, computed on the CONTROL leg alone
# --------------------------------------------------------------------------
def w4_band(ctl_sum: dict) -> dict:
    """PRECOMMIT §3.1 W4: sum decided_mw(ctl) +/- sum g_y, with

    g_y := the largest single-row MW in control-P's year-y failing pool
    (decided u entry_capped) -- the granularity of one whole-unit admission at
    the budget boundary. A year with no capped rows contributes g_y = 0 (its
    decided MW is pool-determined, not budget-determined, so the arm's cannot
    exceed the control's there).
    """
    per_year = {}
    total_dec = 0.0
    total_g = 0.0
    for y, s in sorted(ctl_sum.items()):
        g = s["pool_max_row_mw"] if s["capped_mw"] > 0 else 0.0
        per_year[y] = {
            "decided_mw": s["decided_mw"],
            "capped_mw": s["capped_mw"],
            "cap_binds": s["capped_mw"] > 0,
            "g_y_mw": round(g, 3),
        }
        total_dec += s["decided_mw"]
        total_g += g
    return {
        "per_year": per_year,
        "sum_decided_mw_control": round(total_dec, 3),
        "sum_g_mw": round(total_g, 3),
        "band_lo_mw": round(total_dec - total_g, 3),
        "band_hi_mw": round(total_dec + total_g, 3),
        "definition": (
            "sum_y decided_mw(control-P) +/- sum_y g_y; "
            "g_y = max single-row MW in control-P's year-y failing pool "
            "(decided u entry_capped), 0 where the cap does not bind"
        ),
    }


# --------------------------------------------------------------------------
# gates
# --------------------------------------------------------------------------
def grade(ctl_leds, arm_leds, ctl_sum, arm_sum, sec, band) -> dict:
    g: dict = {}

    # ---- W0: D78's 2022 screen reproduced on both legs -------------------
    def w0_side(tag, s):
        k = D78_2022[tag]
        cl = s["clearing"]
        checks = {
            "failing_rows": (s["pool_rows"], k["failing_rows"], 0),
            "failing_mw": (s["pool_mw"], k["failing_mw"], MW_TOL),
            "n_offers": (cl.get("n_offers"), k["n_offers"], 0),
            "offered_mw": (cl.get("offered_mw"), k["offered_mw"], MW_TOL),
            "price_takers_mw": (cl.get("price_takers_mw"), k["price_takers_mw"], MW_TOL),
            "price": (cl.get("price"), k["price"], PRICE_TOL),
            "decided_rows": (s["decided_rows"], k["decided_rows"], 0),
            "decided_mw": (s["decided_mw"], k["decided_mw"], MW_TOL),
            "executed_mw": (s["executed_economic_mw"], k["executed_mw"], MW_TOL),
        }
        rows = {}
        ok = True
        for name, (got, want, tol) in checks.items():
            hit = got is not None and abs(float(got) - float(want)) <= tol
            rows[name] = {"measured": got, "d78": want, "match": hit}
            ok &= hit
        return {"rows": rows, "pass": bool(ok)}

    g["W0"] = {
        "control": w0_side("ctl", ctl_sum["2022"]),
        "arm": w0_side("arm", arm_sum["2022"]),
    }
    g["W0"]["pass"] = g["W0"]["control"]["pass"] and g["W0"]["arm"]["pass"]

    # ---- prior-year exit sets, for the fleet-delta explanation ------------
    def exits_before(leds, y):
        out: set[str] = set()
        for yy, led in leds.items():
            if yy < y:
                out |= set(all_exits(led))
        return out

    # ---- W1: candidate identity ------------------------------------------
    w1: dict = {"per_year": {}, "pass": True}
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        c, a = fail_rows(ctl_leds[y]), fail_rows(arm_leds[y])
        only_c, only_a, both = set(c) - set(a), set(a) - set(c), set(c) & set(a)
        shared_identical = all(abs(c[u] - a[u]) <= 1e-6 for u in both)
        c_gone = exits_before(ctl_leds, y)
        a_gone = exits_before(arm_leds, y)
        # every control-only row is sector-1, or gone from the arm's fleet
        unexplained_c = sorted(
            u for u in only_c if sector_of(u, sec) != "1" and u not in a_gone
        )
        # every arm-only row must be a fleet-delta row (the control retired it earlier)
        unexplained_a = sorted(u for u in only_a if u not in c_gone)
        exact = y <= 2022  # identical fleets: no exits have executed yet in either leg
        row = {
            "form": "exact" if exact else "fleet-delta",
            "only_control_rows": len(only_c),
            "only_control_mw": round(sum(c[u] for u in only_c), 3),
            "only_control_by_sector": by_sector({u: c[u] for u in only_c}, sec),
            "only_arm_rows": len(only_a),
            "only_arm_mw": round(sum(a[u] for u in only_a), 3),
            "only_arm_by_sector": by_sector({u: a[u] for u in only_a}, sec),
            "shared_rows": len(both),
            "shared_mw_identical": shared_identical,
            "unexplained_control_only": unexplained_c[:20],
            "n_unexplained_control_only": len(unexplained_c),
            "unexplained_arm_only": unexplained_a[:20],
            "n_unexplained_arm_only": len(unexplained_a),
        }
        if exact:
            row["pass"] = bool(
                shared_identical
                and not only_a
                and all(sector_of(u, sec) == "1" for u in only_c)
            )
        else:
            row["pass"] = bool(
                shared_identical and not unexplained_c and not unexplained_a
            )
        w1["per_year"][str(y)] = row
        w1["pass"] &= row["pass"]
    g["W1"] = w1

    # ---- W2: zero sector-1 in ANY arm decision ledger ---------------------
    w2: dict = {"per_year": {}, "pass": True}
    for y, led in sorted(arm_leds.items()):
        counts = {
            kind: sum(
                1 for u in events(led, kind) if sector_of(u, sec) == "1"
            )
            for kind in (
                "decided",
                "entry_capped",
                "floor_retained",
                "throughput_deferred",
            )
        }
        counts["pipeline_events_any"] = sum(
            1
            for e in (led.get("pipeline_events") or [])
            if sector_of(e["unit_id"], sec) == "1"
        )
        counts["retirements_economic"] = sum(
            1 for u in econ_exits(led) if sector_of(u, sec) == "1"
        )
        counts["unknown_sector_pipeline"] = sum(
            1
            for e in (led.get("pipeline_events") or [])
            if sector_of(e["unit_id"], sec) == "unknown"
        )
        row = {"sector1_counts": counts, "pass": all(v == 0 for v in counts.values())}
        w2["per_year"][str(y)] = row
        w2["pass"] &= row["pass"]
    g["W2"] = w2

    # ---- W3: decided-cohort provenance ------------------------------------
    w3: dict = {"per_year": {}, "pass": True}
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        cdec, adec = events(ctl_leds[y], "decided"), events(arm_leds[y], "decided")
        ccap = events(ctl_leds[y], "entry_capped")
        c_gone = exits_before(ctl_leds, y)
        arm_only = set(adec) - set(cdec)
        unexplained = sorted(
            u for u in arm_only if u not in ccap and u not in c_gone
        )
        cecon, aecon = econ_exits(ctl_leds[y]), econ_exits(arm_leds[y])
        exec_only = set(aecon) - set(cecon)
        exec_unexplained = sorted(
            u for u in exec_only if u not in ccap and u not in cdec and u not in c_gone
        )
        row = {
            "arm_only_decided_rows": len(arm_only),
            "arm_only_decided_mw": round(sum(adec[u] for u in arm_only), 3),
            "from_control_entry_capped": sum(1 for u in arm_only if u in ccap),
            "from_fleet_delta": sum(
                1 for u in arm_only if u not in ccap and u in c_gone
            ),
            "n_unexplained_decided": len(unexplained),
            "unexplained_decided": unexplained[:20],
            "arm_only_executed_rows": len(exec_only),
            "arm_only_executed_mw": round(sum(aecon[u] for u in exec_only), 3),
            "n_unexplained_executed": len(exec_unexplained),
            "unexplained_executed": exec_unexplained[:20],
        }
        row["pass"] = not unexplained and not exec_unexplained
        w3["per_year"][str(y)] = row
        w3["pass"] &= row["pass"]
    g["W3"] = w3

    # ---- W4: the window decided total inside the control-derived band -----
    arm_total = round(sum(s["decided_mw"] for s in arm_sum.values()), 3)
    g["W4"] = {
        "band": band,
        "arm_sum_decided_mw": arm_total,
        "delta_vs_control_mw": round(arm_total - band["sum_decided_mw_control"], 3),
        "delta_frac": (
            round(
                (arm_total - band["sum_decided_mw_control"])
                / band["sum_decided_mw_control"],
                5,
            )
            if band["sum_decided_mw_control"]
            else None
        ),
        "pass": bool(band["band_lo_mw"] <= arm_total <= band["band_hi_mw"]),
    }

    # ---- W5: no non-target flip -------------------------------------------
    w5: dict = {"per_year": {}, "pass": True}
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        cl, al = ctl_leds[y], arm_leds[y]
        fp = {
            k: {
                "identical": cl.get(k) == al.get(k),
                "control": cl.get(k) if not isinstance(cl.get(k), (list, dict)) else "…",
                "arm": al.get(k) if not isinstance(al.get(k), (list, dict)) else "…",
            }
            for k in FOOTPRINT_KEYS
        }
        ccc = cl.get("capacity_clearing") or {}
        acc = al.get("capacity_clearing") or {}
        scalar_keys = sorted(
            {k for k, v in ccc.items() if not isinstance(v, (list, dict))}
            | {k for k, v in acc.items() if not isinstance(v, (list, dict))}
        )
        clearing = {
            k: {
                "control": ccc.get(k),
                "arm": acc.get(k),
                "identical": (
                    ccc.get(k) == acc.get(k)
                    if not isinstance(ccc.get(k), float)
                    else abs(float(ccc.get(k)) - float(acc.get(k) or 0.0)) <= 1e-6
                ),
            }
            for k in scalar_keys
        }
        sd = stack_diff(cl, al)
        exact = y <= 2022
        row = {
            "form": "exact" if exact else "fleet-delta",
            "footprint": fp,
            "footprint_all_identical": all(v["identical"] for v in fp.values()),
            "clearing": clearing,
            "clearing_all_identical": all(v["identical"] for v in clearing.values()),
            "stack": sd,
        }
        if exact:
            row["pass"] = bool(
                row["footprint_all_identical"]
                and row["clearing_all_identical"]
                and sd["changed"] == 0
                and sd["only_first"] == 0
                and sd["only_second"] == 0
            )
        else:
            # fleet-delta form: shared rows identical, requirement identical;
            # the census/offer-count delta is the exits' own and is reported.
            row["pass"] = bool(
                sd["changed"] == 0
                and clearing.get("requirement_mw", {}).get("identical", False)
            )
        w5["per_year"][str(y)] = row
        w5["pass"] &= row["pass"]
    g["W5"] = w5

    g["ALL_PASS"] = all(g[k]["pass"] for k in ("W0", "W1", "W2", "W3", "W4", "W5"))
    return g


# --------------------------------------------------------------------------
# reported-only quantities (never gates)
# --------------------------------------------------------------------------
def reported(ctl_sum, arm_sum, ctl_score, arm_score) -> dict:
    def tot(s, key):
        return round(sum(v[key] for v in s.values()), 3)

    out = {
        "executed_economic_by_year": {
            y: {
                "control": ctl_sum.get(y, {}).get("executed_economic_mw"),
                "arm": arm_sum.get(y, {}).get("executed_economic_mw"),
            }
            for y in sorted(set(ctl_sum) | set(arm_sum))
        },
        "window_executed_economic_mw": {
            "control": tot(ctl_sum, "executed_economic_mw"),
            "arm": tot(arm_sum, "executed_economic_mw"),
        },
        "window_retirements_all_mw": {
            "control": tot(ctl_sum, "retirements_all_mw"),
            "arm": tot(arm_sum, "retirements_all_mw"),
        },
        "decided_by_year": {
            y: {
                "control": ctl_sum.get(y, {}).get("decided_mw"),
                "arm": arm_sum.get(y, {}).get("decided_mw"),
            }
            for y in sorted(set(ctl_sum) | set(arm_sum))
        },
    }
    if ctl_score and arm_score:

        def fc3(sc):
            r = sc.get("retirements") or {}
            prec = ((r.get("plant_release_precision") or {}).get("window") or {})
            return {
                "total_gw": r.get("total_gw"),
                "unit_recall_gt300": {
                    k: (r.get("unit_recall_gt300") or {}).get(k)
                    for k in ("recall", "matched", "n_big_actual", "band",
                              "plant_recall_frac", "plant_matched")
                },
                "false_retire": r.get("false_retire"),
                "release_precision_window": prec,
                "per_fuel": r.get("per_fuel"),
            }

        def loyo(sc):
            lo = sc.get("loyo") or {}
            return {
                "folds": {
                    k: {
                        kk: v.get(kk)
                        for kk in ("recall", "recall_band", "matched",
                                   "n_big_actual", "false_retire_gw_raw",
                                   "false_retire_band_raw", "tr10a", "tr10b")
                    }
                    for k, v in (lo.get("folds") or {}).items()
                },
                "holds_2of3": lo.get("holds_2of3"),
            }

        out["score"] = {
            "control": {"fc3": fc3(ctl_score), "loyo": loyo(ctl_score)},
            "arm": {"fc3": fc3(arm_score), "loyo": loyo(arm_score)},
        }
    return out


def flip_condition(g: dict, rep: dict) -> dict:
    """PRECOMMIT §6 (a)-(d), graded. ARM iff all four MET."""
    a = g["W5"]["pass"]
    b = g["W1"]["pass"] and g["W2"]["pass"] and g["W3"]["pass"]
    sc = rep.get("score")
    c = d = None
    detail: dict = {}
    if sc:
        cp = (sc["control"]["fc3"]["release_precision_window"] or {}).get("economic") or {}
        ap = (sc["arm"]["fc3"]["release_precision_window"] or {}).get("economic") or {}
        cprec, aprec = cp.get("precision"), ap.get("precision")
        c = bool(
            cprec is not None and aprec is not None and aprec >= cprec
        ) and g["W2"]["pass"]
        detail["c"] = {
            "control_precision": cprec,
            "arm_precision": aprec,
            "every_row_non_sector1": g["W2"]["pass"],
        }
        cf = sc["control"]["loyo"]["folds"]
        af = sc["arm"]["loyo"]["folds"]
        lost = [
            y
            for y in cf
            if cf[y].get("recall_band") == "PASS"
            and af.get(y, {}).get("recall_band") != "PASS"
        ]
        d = not lost
        detail["d"] = {
            "control_folds": {y: cf[y].get("recall_band") for y in sorted(cf)},
            "arm_folds": {y: af.get(y, {}).get("recall_band") for y in sorted(af)},
            "folds_lost": lost,
            "holds_2of3_control": sc["control"]["loyo"]["holds_2of3"],
            "holds_2of3_arm": sc["arm"]["loyo"]["holds_2of3"],
        }
    limbs = {"a_purity": a, "b_fidelity": b, "c_composition": c, "d_loyo": d}
    if all(v is True for v in limbs.values()):
        rec = "ARM"
    elif a is False:
        rec = "HOLD-and-route"
    elif any(v is False for v in limbs.values()):
        rec = "DECLINE"
    else:
        rec = "NOT ADJUDICABLE"
    return {"limbs": limbs, "detail": detail, "recommendation": rec}


def score_of(out_dir: Path) -> dict | None:
    p = bundle_dir(out_dir) / "score.json"
    return json.loads(p.read_text()) if p.exists() else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctl", required=True, type=Path)
    ap.add_argument("--arm", type=Path)
    ap.add_argument("--band-only", action="store_true")
    ap.add_argument("--out", type=Path, default=HERE / "window_compare.json")
    args = ap.parse_args()

    sec = sectors()
    ctl_leds = load_legs(args.ctl)
    ctl_sum = summarise(ctl_leds, sec)
    band = w4_band(ctl_sum)

    if args.band_only or args.arm is None:
        payload = {"control": ctl_sum, "w4_band": band}
        out = HERE / "control_band.json"
        out.write_text(json.dumps(payload, indent=2))
        print(json.dumps(band, indent=2))
        print(f"\n-> {out}")
        return

    arm_leds = load_legs(args.arm)
    arm_sum = summarise(arm_leds, sec)
    g = grade(ctl_leds, arm_leds, ctl_sum, arm_sum, sec, band)
    rep = reported(ctl_sum, arm_sum, score_of(args.ctl), score_of(args.arm))
    payload = {
        "control": ctl_sum,
        "arm": arm_sum,
        "gates": g,
        "reported": rep,
        "flip_condition": flip_condition(g, rep),
    }
    args.out.write_text(json.dumps(payload, indent=2))
    print(
        json.dumps(
            {
                "gates": {
                    k: g[k]["pass"] for k in ("W0", "W1", "W2", "W3", "W4", "W5")
                },
                "ALL_PASS": g["ALL_PASS"],
                "W4": {k: v for k, v in g["W4"].items() if k != "band"},
                "flip_condition": payload["flip_condition"]["limbs"],
                "recommendation": payload["flip_condition"]["recommendation"],
            },
            indent=2,
        )
    )
    print(f"\n-> {args.out}")


if __name__ == "__main__":
    main()
