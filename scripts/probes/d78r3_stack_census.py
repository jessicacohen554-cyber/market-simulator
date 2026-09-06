#!/usr/bin/env python3
"""capx D78-R3 — the two READ-ONLY instruments of the per-delivery-year lane.

Declared in ``PRECOMMIT-capx-d78r3-perdy-set-2026-09-06.md`` §5.3 before any
value was opened. Read-only in the strict sense: it opens committed JSON and
solved ledgers, writes two JSON instruments under ``docs/handoffs/d78r3/``, and
touches no config, no default, no solve path and no ``ScenarioConfig`` field.

Two modes, one file, because the PRECOMMIT declared one helper:

``--census``
    **STEP 1, the derivation.** Runs the PRECOMMIT §2 rule — quoted verbatim
    from ``FINDING-capx-d78r2`` §9 item 2, *"a class sits at its full bar in DY
    iff every one of its offers in the control's DY stack is the same value"* —
    over the CONTROL leg's ``capacity_clearing.offer_stack``, per delivery year,
    per fuel class. Emits ``zero_eas_set.json``: ``n_distinct_exact`` (the
    deciding count, exact IEEE-754 equality) and ``n_distinct_1e6`` (the
    reported clustering lens) per class, the derived set, the declared set, and
    the subset check.

    The rule is ONE-SIDED and the PRECOMMIT says so in advance: a unit's bar is
    ``GFC_g / (A_g x 365)``, so a class every one of whose units sits at its own
    bar still shows ``n_distinct > 1`` wherever ``GFC_g`` or ``A_g`` varies
    within the class. The derived set is therefore a LOWER BOUND on the at-bar
    set, ``derived != declared`` is expected, and the DECLARED set governs W5''
    either way.

``--regrade``
    **STEP 2, the re-grade.** Re-grades W5'' on the per-delivery-year declared
    set, from the COMMITTED instrument output plus the merged documentary
    record. It does NOT re-solve, and it does not read the arm: neither leg's
    bundle exists on ``main`` (the control-P was deleted before merge under rule
    29(c); the D78-R2 arm was never registered — merge ``80c88b76`` landed docs
    and JSON only), so the operands are, per PRECOMMIT §5.2:

    * moved shared rows per fuel per year — PRIMARY, machine-readable:
      ``window_compare2.json`` -> ``gates.W5prime.per_year[y].offer_diff_by_fuel``
      (a fuel absent from that dict has zero movers, by its construction);
    * shared rows per fuel per year — documentary, rule 29(c):
      ``FINDING-capx-d78r2`` §5.1's per-fuel table, transcribed in
      :data:`SHARED_ROWS_BY_FUEL` and cross-checked against the committed
      totals before any verdict is written (STOP S2).

    ``max_abs_delta`` is emitted as ``null`` with its reason: no committed
    artifact holds offer VALUES for either leg, and the arm is not re-solved to
    manufacture one. It is reporting detail, never the verdict operand — the
    gate is "delta exactly zero at ``OFFER_TOL``", which the mover count
    answers exactly.

Usage::

    uv run python scripts/probes/d78r3_stack_census.py --regrade
    uv run python scripts/probes/d78r3_stack_census.py --census --ctl <bundle>
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT_DIR = REPO / "docs" / "handoffs" / "d78r3"
D78R2 = REPO / "docs" / "handoffs" / "d78r2"

#: Offer-delta tolerance, the instrument's own (``window_compare2.py``).
OFFER_TOL = 1e-9

#: The reported clustering lens for the derivation. NEVER the deciding test —
#: PRECOMMIT §2 fixes exact IEEE-754 equality as that.
CLUSTER_TOL = 1e-6

#: Solve year -> delivery year, from ``FINDING-capx-d57`` §3.1's own
#: ``screen -> DY`` column (2022 -> 2022/23, ...). The 2021 ledger carries an
#: empty stack, so there is no DY2021/22.
DY_OF_YEAR = {2022: "2022/23", 2023: "2023/24", 2024: "2024/25", 2025: "2025/26"}

#: PRECOMMIT §1 (a). Quoted from ``FINDING-capx-d57-2026-09-05.md`` §4's arm-A
#: ROWS — the basis actually armed by its §8.1 — never its headline. A DY whose
#: value is ``None`` has NO published at-bar set and is NOT EVALUABLE; its
#: measurements are reported, never gated.
DECLARED_SET_BY_DY: dict[str, frozenset[str] | None] = {
    "2022/23": frozenset({"gas_ct", "gas_st", "oil"}),
    "2023/24": frozenset({"gas_ct", "gas_st"}),
    "2024/25": frozenset({"oil"}),
    "2025/26": None,
}

#: The D57 §4 arm-A row each declared set is quoted from, for the record.
DECLARED_SET_CITATION = {
    "2022/23": "D57 §4 arm A, DY2022/23 ($50.00): gas_ct 404 / 24,244 · "
    "gas_st 115 / 8,802 · oil 421 / 3,723 · gas_cc 40 / 1,145 · coal 2 / 30 "
    "— gas_cc and coal are PARTIAL fleets and are excluded (class-level set)",
    "2023/24": "D57 §4 arm A, DY2023/24 ($34.13): gas_ct 403 / 24,243 · "
    "gas_st 77 / 1,982 · gas_cc 1 / 73 — gas_cc partial and excluded; gas_st "
    "is partial (77/115) and INCLUDED per D78-R2 §9 item 1, which can only "
    "make the gate stricter",
    "2024/25": "D57 §4 arm A, DY2024/25 ($28.92): oil 8 / 3,723 "
    '"(the CT fleet\'s 2024 margin is small but non-zero)"',
    "2025/26": "NO ROW EXISTS — D57 §4's arm-A panel stops at 2024/25; §3.1's "
    "2025 row is at the price cap where every offer clears, so no at-bar set "
    "was tabulated. NOT EVALUABLE (PRECOMMIT §1 reading 2)",
}

#: ``FINDING-capx-d78r2-2026-09-06.md`` §5.1's per-fuel shared-row table, the
#: documentary record under rule 29(c) of two bundles that no longer exist.
#: Cross-checked against ``window_compare2.json``'s own totals by
#: :func:`_check_sources` before any verdict is written (STOP S2). A fuel absent
#: from a year's dict was absent from that year's shared stack.
SHARED_ROWS_BY_FUEL: dict[int, dict[str, int]] = {
    2022: {
        "oil": 421,
        "gas_st": 118,
        "nuclear": 31,
        "gas_ct": 404,
        "gas_cc": 237,
        "coal": 188,
    },
    2023: {"nuclear": 31, "gas_ct": 403, "gas_cc": 231, "coal": 184},
    2024: {"oil": 8, "nuclear": 31, "gas_ct": 404, "gas_cc": 212, "coal": 180},
    2025: {"oil": 8, "nuclear": 31, "gas_ct": 404, "gas_cc": 212, "coal": 166},
}

#: The zero-E&AS set ``window_compare2.py`` itself declared — YEAR-INVARIANT,
#: which is the construction defect this lane repairs. Used only to reproduce
#: D78-R2's own verdict beside the corrected one.
D78R2_YEAR_INVARIANT_SET = frozenset({"gas_ct", "gas_st", "oil"})

MAX_ABS_DELTA_REASON = (
    "not recoverable: no committed artifact holds offer VALUES for either leg "
    "(control-P deleted before merge, rule 29(c); the D78-R2 arm was never "
    "registered), and the arm is NOT re-solved. window_compare2.json records "
    "mover COUNTS, not offers. Reporting detail only — the gate is 'delta "
    f"exactly zero at OFFER_TOL={OFFER_TOL}', which the mover count answers."
)


# --------------------------------------------------------------------------
# STEP 2 — the re-grade
# --------------------------------------------------------------------------
def _check_sources(w5: dict) -> dict:
    """STOP S2 — the documentary table must agree with the committed totals.

    ``SHARED_ROWS_BY_FUEL`` is a partition of ``shared_rows``; its
    ``ZERO_EAS``-fuel part is a partition of ``zero_eas_shared_rows``; and its
    mover side must reproduce ``offer_diff_rows``. Three independent identities
    over two sources that were not copied from each other.
    """
    rows = []
    ok = True
    for year, by_fuel in SHARED_ROWS_BY_FUEL.items():
        r = w5["per_year"][str(year)]
        movers = r["offer_diff_by_fuel"]
        doc_total = sum(by_fuel.values())
        doc_zero_eas = sum(
            n for f, n in by_fuel.items() if f in D78R2_YEAR_INVARIANT_SET
        )
        unknown = sorted(set(movers) - set(by_fuel))
        over = sorted(f for f, n in movers.items() if n > by_fuel.get(f, 0))
        row = {
            "year": year,
            "doc_shared_total": doc_total,
            "json_shared_rows": r["shared_rows"],
            "shared_total_agrees": doc_total == r["shared_rows"],
            "doc_zero_eas_shared": doc_zero_eas,
            "json_zero_eas_shared_rows": r["zero_eas_shared_rows"],
            "zero_eas_agrees": doc_zero_eas == r["zero_eas_shared_rows"],
            "json_offer_diff_rows": r["offer_diff_rows"],
            "movers_sum": sum(movers.values()),
            "movers_sum_agrees": sum(movers.values()) == r["offer_diff_rows"],
            "movers_in_unknown_fuel": unknown,
            "movers_exceeding_shared": over,
        }
        row["pass"] = bool(
            row["shared_total_agrees"]
            and row["zero_eas_agrees"]
            and row["movers_sum_agrees"]
            and not unknown
            and not over
        )
        ok &= row["pass"]
        rows.append(row)
    return {"per_year": rows, "pass": bool(ok)}


def regrade() -> dict:
    """Re-grade W5'' on the per-delivery-year declared set (PRECOMMIT §3)."""
    wc = json.loads((D78R2 / "window_compare2.json").read_text())
    w5 = wc["gates"]["W5prime"]

    sources = _check_sources(w5)
    if not sources["pass"]:
        return {"STOP": "S2 — source disagreement", "source_check": sources}

    per_dy: dict[str, dict] = {}
    evaluable_verdicts: list[bool] = []

    for year, dy in sorted(DY_OF_YEAR.items()):
        r = w5["per_year"][str(year)]
        movers = r["offer_diff_by_fuel"]
        shared = SHARED_ROWS_BY_FUEL[year]
        declared = DECLARED_SET_BY_DY[dy]

        classes: dict[str, dict] = {}
        for fuel in sorted(set(shared) | set(movers)):
            n_shared = shared.get(fuel, 0)
            n_moved = movers.get(fuel, 0)
            in_set = declared is not None and fuel in declared
            if not in_set:
                status = "REPORTED (outside the DY's declared set)"
            elif n_shared == 0:
                status = "VACUOUS (declared, zero shared rows)"
            else:
                status = "PASS" if n_moved == 0 else "FAIL"
            classes[fuel] = {
                "in_declared_set": in_set,
                "shared_rows": n_shared,
                "moved_rows": n_moved,
                "unmoved_rows": n_shared - n_moved,
                "max_abs_delta": None,
                "max_abs_delta_reason": MAX_ABS_DELTA_REASON,
                "status": status,
            }
        # a declared class absent from BOTH dicts is vacuous and must still show
        for fuel in sorted(declared or ()):
            if fuel not in classes:
                classes[fuel] = {
                    "in_declared_set": True,
                    "shared_rows": 0,
                    "moved_rows": 0,
                    "unmoved_rows": 0,
                    "max_abs_delta": None,
                    "max_abs_delta_reason": MAX_ABS_DELTA_REASON,
                    "status": "VACUOUS (declared, zero shared rows)",
                }

        gated = {f: c for f, c in classes.items() if c["status"] in ("PASS", "FAIL")}
        vacuous = sorted(f for f, c in classes.items() if c["status"].startswith("VAC"))

        if declared is None:
            verdict, reason = (
                "NOT EVALUABLE",
                "no published at-bar set for this DY (PRECOMMIT §1)",
            )
        elif not gated:
            verdict, reason = (
                "NOT EVALUABLE",
                "every declared class is vacuous (PRECOMMIT §3)",
            )
        else:
            failed = sorted(f for f, c in gated.items() if c["status"] == "FAIL")
            verdict = "FAIL" if failed else "PASS"
            reason = (
                f"failing classes: {failed}"
                if failed
                else f"{sum(c['shared_rows'] for c in gated.values())} gated shared "
                f"rows across {sorted(gated)}, 0 moved"
            )
            evaluable_verdicts.append(verdict == "PASS")

        per_dy[dy] = {
            "solve_year": year,
            "declared_set": sorted(declared) if declared is not None else None,
            "declared_set_citation": DECLARED_SET_CITATION[dy],
            "form": r["form"],
            "shared_rows_total": r["shared_rows"],
            "offer_diff_rows_total": r["offer_diff_rows"],
            "classes": classes,
            "gated_classes": sorted(gated),
            "vacuous_classes": vacuous,
            "verdict": verdict,
            "reason": reason,
        }

    window = "PASS" if all(evaluable_verdicts) else "FAIL"
    return {
        "instrument": "d78r3_stack_census.py --regrade",
        "graded_on": {
            "primary": "docs/handoffs/d78r2/window_compare2.json -> "
            "gates.W5prime.per_year[y].offer_diff_by_fuel",
            "documentary": "FINDING-capx-d78r2-2026-09-06.md §5.1 (rule 29(c))",
            "arm_re_solved": False,
            "control_re_solved_for_this_grade": False,
        },
        "first_divergent_year": wc["first_divergent_year"],
        "source_check_S2": sources,
        "per_dy": per_dy,
        "evaluable_dys": [d for d, v in per_dy.items() if v["verdict"] != "NOT EVALUABLE"],
        "window_verdict": window,
        "d78r2_year_invariant_verdict": {
            "set": sorted(D78R2_YEAR_INVARIANT_SET),
            "window_pass": w5["pass"],
            "note": "D78-R2's own W5' verdict, reproduced from the same committed "
            "instrument: the SAME measurement, graded on a year-invariant set. "
            "Nothing measured changed between the two grades.",
        },
    }


# --------------------------------------------------------------------------
# STEP 1 — the derivation
# --------------------------------------------------------------------------
def _cluster_count(vals: list[float], tol: float) -> int:
    """Count clusters of ``vals`` under a chaining tolerance ``tol``."""
    n = 0
    prev: float | None = None
    for v in sorted(vals):
        if prev is None or (v - prev) > tol:
            n += 1
        prev = v
    return n


def census(ctl_dir: Path) -> dict:
    """Run the PRECOMMIT §2 derivation over the control's per-DY stacks."""
    sys.path.insert(0, str(REPO / "docs" / "handoffs" / "d78"))
    from screen_compare import stack_rows  # noqa: E402  (path-inserted above)

    leds = {}
    for p in sorted(ctl_dir.rglob("evolution_*.json")):
        year = int(p.stem.split("_")[1])
        leds[year] = json.loads(p.read_text())

    per_dy: dict[str, dict] = {}
    for year, dy in sorted(DY_OF_YEAR.items()):
        if year not in leds:
            per_dy[dy] = {"solve_year": year, "status": "LEDGER ABSENT"}
            continue
        rows = stack_rows(leds[year])
        by_fuel: dict[str, list[float]] = defaultdict(list)
        for _uid, (_u, fuel, offer, _ag, _cl) in rows.items():
            by_fuel[fuel].append(float(offer))

        declared = DECLARED_SET_BY_DY[dy]
        classes: dict[str, dict] = {}
        derived: set[str] = set()
        for fuel in sorted(by_fuel):
            vals = by_fuel[fuel]
            n_exact = len(set(vals))
            n_cluster = _cluster_count(vals, CLUSTER_TOL)
            at_bar = n_exact == 1
            if at_bar:
                derived.add(fuel)
            classes[fuel] = {
                "rows": len(vals),
                "n_distinct_exact": n_exact,
                "n_distinct_1e6": n_cluster,
                "counts_disagree": n_exact != n_cluster,
                "derived_at_bar": at_bar,
                "in_declared_set": declared is not None and fuel in declared,
                "offer_min": round(min(vals), 6),
                "offer_max": round(max(vals), 6),
            }

        excess = sorted(derived - (declared or frozenset()))
        missing = sorted((declared or frozenset()) - derived)
        per_dy[dy] = {
            "solve_year": year,
            "stack_rows": len(rows),
            "classes": classes,
            "derived_set": sorted(derived),
            "declared_set": sorted(declared) if declared is not None else None,
            "declared_set_citation": DECLARED_SET_CITATION[dy],
            "subset_check": {
                "derived_subset_of_declared": not excess,
                "in_derived_not_declared": excess,
                "in_declared_not_derived": missing,
                "note": "PRECOMMIT §2: the rule is ONE-SIDED, so "
                "in_declared_not_derived is EXPECTED and is not evidence "
                "against a declared class. in_derived_not_declared is NEVER "
                "admitted to the gate — it is reported and the DECLARED set "
                "governs W5'' regardless.",
            },
        }

    return {
        "instrument": "d78r3_stack_census.py --census",
        "rule": "PRECOMMIT §2, verbatim from FINDING-capx-d78r2 §9 item 2: a "
        "class sits at its full bar in DY iff every one of its offers in the "
        "control's DY stack is the same value.",
        "tolerance": {
            "deciding": "exact IEEE-754 float equality (n_distinct_exact == 1)",
            "reported_lens": f"clustering at {CLUSTER_TOL} $/MW-day "
            "(n_distinct_1e6) — never substituted for the deciding test",
        },
        "read_from": str(ctl_dir.relative_to(REPO)),
        "per_dy": per_dy,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--regrade", action="store_true", help="STEP 2")
    ap.add_argument("--census", action="store_true", help="STEP 1")
    ap.add_argument("--ctl", type=Path, help="control bundle dir (--census)")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.regrade:
        payload = regrade()
        out = OUT_DIR / "w5_regrade.json"
        out.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"-> {out}")
        print(
            json.dumps(
                {
                    "S2": payload.get("source_check_S2", {}).get("pass"),
                    "per_dy": {
                        k: v["verdict"] for k, v in payload.get("per_dy", {}).items()
                    },
                    "window_verdict": payload.get("window_verdict"),
                },
                indent=2,
            )
        )
    if args.census:
        if not args.ctl:
            ap.error("--census needs --ctl")
        payload = census(args.ctl)
        out = OUT_DIR / "zero_eas_set.json"
        out.write_text(json.dumps(payload, indent=2) + "\n")
        print(f"-> {out}")
        print(
            json.dumps(
                {
                    k: {
                        "derived": v.get("derived_set"),
                        "declared": v.get("declared_set"),
                        "subset_ok": v.get("subset_check", {}).get(
                            "derived_subset_of_declared"
                        ),
                    }
                    for k, v in payload["per_dy"].items()
                },
                indent=2,
            )
        )
    if not (args.regrade or args.census):
        ap.error("pick --regrade and/or --census")


if __name__ == "__main__":
    main()
