"""capx D78-R2 full-window differencing — control-P vs the sector-gate arm over
2021-2025, read off the two bundles' committed ledgers and ``score.json``.
Zero LP.

This is D78-R's ``window_compare.py`` with **three changes**, each mandated by
the D78-R2 charter and each pre-registered in
``PRECOMMIT-capx-d78r2-full-window-2026-09-06.md`` before any leg is solved:

* **W4'** — the band's LOWER edge is the mechanism's own arithmetic,
  ``Sum decided_ctl - Sum (sector-1 decided_ctl)``, not D78-R's mis-derived
  ``-Sum g_y``. Both edges are computed on the SAME-HEAD control leg after it
  solves and before the arm (D74 §9 item 3's procedure). The lower edge is
  also the **point value** — the exact-partition prediction.
* **W5'** — purity, restated to admit the E&AS propagation D78-R discovered and
  to TEST it rather than assume it. See :func:`w5_prime`.
* **The WHOLE-LEDGER DIFF** (FINDING-capx-d81 §8 item 4): every top-level block
  of every year's ``evolution_<year>.json`` is differenced and classified. An
  assertion list is the floor, not the ceiling.

W0 is DROPPED, not restated: D78-R discharged its residual known-answer content
(its §2 W0' closed the attribution to D67-ARM and D81 exactly), and both of this
lane's legs are solved at ONE code state, so there is no cross-HEAD known answer
left for it to check. W1 / W2 / W3 are D78-R's, unchanged, and read through the
SAME reader functions (imported, never re-implemented) so the two lanes cannot
drift on what a "failing pool" or a "decided row" is.

    # after control-P, BEFORE the arm — the W4' band addendum:
    uv run python docs/handoffs/d78r2/window_compare2.py --ctl <ctl-dir> --band-only

    # after both legs — the full grade:
    uv run python docs/handoffs/d78r2/window_compare2.py --ctl <ctl> --arm <arm>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "d78"))
sys.path.insert(0, str(HERE.parent / "d78r"))

from screen_compare import (  # noqa: E402  (path-inserted above)
    fail_rows,
    sector_of,
    sectors,
    stack_rows,
)
from window_compare import (  # noqa: E402  (path-inserted above)
    all_exits,
    by_sector,
    econ_exits,
    events,
    load_legs,
    reported,
    score_of,
    summarise,
    w4_band,
)

MW_TOL = 0.001
OFFER_TOL = 1e-9
AG_TOL = 1e-6

#: The fuel vocabulary the screen can emit into an offer stack — the keys of
#: ``retirements._THERMAL_FOM``. A stack row carrying anything else is a STOP,
#: never a silent skip: it would mean the zero-E&AS partition below is
#: incomplete and W5' would be grading a set it does not know the shape of.
FUEL_VOCAB = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "gas_cc_ccs", "coal", "oil", "nuclear"}
)

#: Classes whose E&AS operand is ZERO in the hindcast prices, DECLARED EX ANTE
#: from the record, never selected on this lane's own measurement:
#: ``FINDING-capx-d57-2026-09-05.md`` §8.1 names the "CT / ST / oil E&AS operand
#: is zero in the hindcast prices" as the successor question, and
#: ``FINDING-capx-d81-2026-09-06.md`` §8 item 3 restates it. A unit whose EAS_g
#: is zero offers at its FULL net-ACR bar, ``GFC_g / (A_g x 365)``, which reads
#: no price vector at all — so its offer CANNOT move through the prior-year
#: price channel. That makes "these units' offers do not move" a falsifiable
#: prediction of the propagation story rather than a restatement of it.
ZERO_EAS_FUELS = frozenset({"gas_ct", "gas_st", "oil"})

#: Ledger blocks whose rows are per-unit records (a list of dicts carrying
#: ``unit_id``). These are where a SECOND SEAM would show, so a per-unit row
#: difference that classifies under none of R1-R3 (see module docstring and the
#: PRECOMMIT) is a STOP. Everything else is an aggregate: differenced and
#: REPORTED for narrative explanation, never silently dropped.
PER_UNIT_BLOCKS = (
    "retirements",
    "pipeline_events",
    "floor_retained",
    "confirmed_derates",
    "announced_derates",
    "ccs_retrofits",
    "thermal_additions",
    "renewable_additions",
)


# --------------------------------------------------------------------------
# fleet-divergence bookkeeping
# --------------------------------------------------------------------------
def exits_before(leds: dict[int, dict], y: int) -> set[str]:
    out: set[str] = set()
    for yy, led in leds.items():
        if yy < y:
            out |= set(all_exits(led))
    return out


def first_divergent_year(ctl_leds, arm_leds) -> int | None:
    """The first solved year whose SCREEN sees different fleets in the two legs.

    A year whose prior-exit sets are equal presents identical fleets, so every
    stack row is directly comparable ("exact" form). The first year at which
    they differ is where the fleet delta enters — and it is still a year in
    which OFFERS must be identical, because the net-ACR offer's E&AS operand
    reads the PRIOR year's prices, and that year's solve was on equal fleets.
    """
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        if exits_before(ctl_leds, y) != exits_before(arm_leds, y):
            return y
    return None


# --------------------------------------------------------------------------
# W4' — the corrected band, computed on the CONTROL leg alone
# --------------------------------------------------------------------------
def w4_prime_band(ctl_sum: dict, ctl_leds: dict, sec) -> dict:
    """``[Sum decided_ctl - Sum sector1_decided_ctl , Sum decided_ctl + Sum g_y]``.

    The UPPER edge is D78-R's and is unchanged: ``g_y`` is the granularity of
    one whole-unit admission at the budget boundary, which bounds how far a
    re-fill can overshoot in a year whose admission cap binds.

    The LOWER edge is the repair. A candidate-set gate can only REMOVE
    candidates; the most it can subtract from the window's decided total is
    exactly the decided MW of the candidates it removes — the control's own
    sector-1 decided MW. D78-R bracketed the downside by ``g_y`` instead, a
    quantity about the cap's granularity rather than about the partition, and
    its arm landed 1,117 MW below the resulting edge (D78-R §4).

    The lower edge is therefore ALSO the point value: an exact partition with
    no re-fill lands ON it.
    """
    base = w4_band(ctl_sum)
    per_year = {}
    total_s1 = 0.0
    for y, led in sorted(ctl_leds.items()):
        dec = events(led, "decided")
        s1 = {u: mw for u, mw in dec.items() if sector_of(u, sec) == "1"}
        per_year[str(y)] = {
            "decided_mw": round(sum(dec.values()), 3),
            "sector1_decided_rows": len(s1),
            "sector1_decided_mw": round(sum(s1.values()), 3),
        }
        total_s1 += sum(s1.values())
    lo = base["sum_decided_mw_control"] - total_s1
    return {
        "per_year": per_year,
        "g_y_per_year": base["per_year"],
        "sum_decided_mw_control": base["sum_decided_mw_control"],
        "sum_sector1_decided_mw_control": round(total_s1, 3),
        "sum_g_mw": base["sum_g_mw"],
        "band_lo_mw": round(lo, 3),
        "band_hi_mw": base["band_hi_mw"],
        "point_value_exact_partition_mw": round(lo, 3),
        "definition": (
            "[sum_y decided_mw(ctl) - sum_y sector1_decided_mw(ctl), "
            "sum_y decided_mw(ctl) + sum_y g_y]; g_y = max single-row MW in "
            "control-P's year-y failing pool (decided u entry_capped), 0 where "
            "the admission cap does not bind. The lower edge is the exact-"
            "partition point value."
        ),
        "d78r_band_for_reference": {
            "band_lo_mw": base["band_lo_mw"],
            "band_hi_mw": base["band_hi_mw"],
            "note": "D78-R's symmetric +/- sum g_y bracket; its lower edge is "
            "the construction error FINDING-capx-d78r §4 records.",
        },
    }


# --------------------------------------------------------------------------
# W5' — purity, restated and TESTED
# --------------------------------------------------------------------------
def w5_prime(ctl_leds, arm_leds, divergent: int | None) -> dict:
    """Shared-stack purity, in the form the E&AS propagation makes coherent.

    Per year, over the units present in BOTH legs' offer stacks:

    **Structural limbs (hard, EVERY year).** ``A_g`` identical to
    ``AG_TOL`` and ``fuel`` identical. Neither can move through any channel
    this mechanism owns; a difference is a second seam by definition.

    **Exactness limbs (hard, every year up to and including the first
    divergent year D).** Shared-stack OFFERS identical to ``OFFER_TOL`` and
    CLEARED FLAGS identical. Up to D the offers read a prior-year price vector
    the two legs share, so they must agree; and where the offers agree the
    clearing must agree too.

    **Propagation limbs (hard, every year after D), TESTED not assumed.**
    After D the offers may differ, but ONLY through the prior year's price
    vector. Two falsifiable consequences are gated:

    (i) every shared unit whose fuel is in :data:`ZERO_EAS_FUELS` carries an
        offer delta of EXACTLY zero — its offer is its full net-ACR bar and
        reads no price at all; and
    (ii) every shared unit whose offer DOES differ is outside
         :data:`ZERO_EAS_FUELS`.

    A cleared-flag difference after D is **REPORTED, not gated**: the flag is
    a function of the offer stack's ordering against the demand curve, so
    gating it would gate the very propagation limb (i)/(ii) already grades —
    the same phenomenon twice (rule 19 ``[R-ONE-MECH]`` in spirit), and it is
    the class of mis-derived edge that fired D78-R's W4. It is differenced and
    printed so a reader can see it.
    """
    out: dict = {
        "first_divergent_year": divergent,
        "zero_eas_fuels": sorted(ZERO_EAS_FUELS),
        "per_year": {},
        "pass": True,
    }
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        cs, as_ = stack_rows(ctl_leds[y]), stack_rows(arm_leds[y])
        shared = sorted(set(cs) & set(as_))
        exact = divergent is None or y <= divergent

        bad_fuel = sorted(
            {r[1] for r in list(cs.values()) + list(as_.values())} - FUEL_VOCAB
        )
        ag_diff = [
            u for u in shared if abs(float(cs[u][3]) - float(as_[u][3])) > AG_TOL
        ]
        fuel_diff = [u for u in shared if cs[u][1] != as_[u][1]]
        offer_diff = [
            u for u in shared if abs(float(cs[u][2]) - float(as_[u][2])) > OFFER_TOL
        ]
        cleared_diff = [u for u in shared if bool(cs[u][4]) != bool(as_[u][4])]

        zero_eas_shared = [u for u in shared if cs[u][1] in ZERO_EAS_FUELS]
        zero_eas_moved = [u for u in zero_eas_shared if u in set(offer_diff)]
        moved_inside_zero_eas = sorted(
            u for u in offer_diff if cs[u][1] in ZERO_EAS_FUELS
        )

        row = {
            "form": "exact" if exact else "post-divergence",
            "shared_rows": len(shared),
            "only_control_rows": len(set(cs) - set(as_)),
            "only_arm_rows": len(set(as_) - set(cs)),
            "unknown_fuels": bad_fuel,
            "ag_diff_rows": len(ag_diff),
            "fuel_diff_rows": len(fuel_diff),
            "offer_diff_rows": len(offer_diff),
            "cleared_diff_rows": len(cleared_diff),
            "cleared_diff_units": cleared_diff[:20],
            "zero_eas_shared_rows": len(zero_eas_shared),
            "zero_eas_offer_diff_rows": len(zero_eas_moved),
            "zero_eas_offer_diff_units": moved_inside_zero_eas[:20],
            "offer_diff_by_fuel": {
                f: sum(1 for u in offer_diff if cs[u][1] == f)
                for f in sorted({cs[u][1] for u in offer_diff})
            },
        }
        structural = not bad_fuel and not ag_diff and not fuel_diff
        if exact:
            row["limbs"] = {
                "structural": structural,
                "offers_identical": not offer_diff,
                "cleared_identical": not cleared_diff,
            }
        else:
            row["limbs"] = {
                "structural": structural,
                "zero_eas_offers_unmoved": not zero_eas_moved,
                "every_mover_outside_zero_eas": not moved_inside_zero_eas,
            }
        row["pass"] = all(row["limbs"].values())
        out["per_year"][str(y)] = row
        out["pass"] &= row["pass"]
    out["pass"] = bool(out["pass"])
    return out


# --------------------------------------------------------------------------
# THE WHOLE-LEDGER DIFF (FINDING-capx-d81 §8 item 4)
# --------------------------------------------------------------------------
def _rows_by_unit(block) -> dict[str, dict] | None:
    if not isinstance(block, list):
        return None
    if not all(isinstance(r, dict) and "unit_id" in r for r in block):
        return None
    return {r["unit_id"]: r for r in block}


def whole_ledger_diff(ctl_leds, arm_leds, sec, divergent) -> dict:
    """Difference EVERY top-level block of EVERY year, and classify each.

    D81's own lesson (§8 item 4): three of six gates in that lane were
    mis-specified and the mechanism's real effect was found by differencing
    every committed block, not by the gate table. So this walks the union of
    both legs' ledger keys rather than an allowlist.

    Classification, declared ex ante:

    * **R1 sector-1 partition** — the differing per-unit rows are all at
      sector-1 plants (the mechanism's own candidate set).
    * **R2 fleet-delta** — the differing per-unit rows are units exactly one
      leg had already retired in an earlier year.
    * **R3 E&AS propagation** — an ``offer_stack`` OFFER value differing in a
      year after the first divergent year, on a unit outside
      :data:`ZERO_EAS_FUELS`.
    * **R4 aggregate** — a scalar or by-fuel/by-tech roll-up. Differenced and
      REPORTED for narrative explanation in the FINDING; never a STOP, because
      an aggregate cannot localise a seam.

    **A per-unit row difference classified by none of R1-R3 is a STOP.** That
    is where a second seam would appear, and it is the only place this diff
    refuses rather than reports.
    """
    out: dict = {"per_year": {}, "stops": [], "pass": True}
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        cl, al = ctl_leds[y], arm_leds[y]
        c_gone, a_gone = exits_before(ctl_leds, y), exits_before(arm_leds, y)
        fleet_delta = c_gone ^ a_gone
        year_rows: dict[str, dict] = {}
        for key in sorted(set(cl) | set(al)):
            cv, av = cl.get(key), al.get(key)
            if cv == av:
                continue
            crows, arows = _rows_by_unit(cv), _rows_by_unit(av)
            if key in PER_UNIT_BLOCKS and crows is not None and arows is not None:
                only_c = sorted(set(crows) - set(arows))
                only_a = sorted(set(arows) - set(crows))
                changed = sorted(
                    u for u in set(crows) & set(arows) if crows[u] != arows[u]
                )
                unclassified = sorted(
                    u
                    for u in set(only_c) | set(only_a) | set(changed)
                    if sector_of(u, sec) != "1" and u not in fleet_delta
                )
                rec = {
                    "kind": "per-unit",
                    "only_control": len(only_c),
                    "only_arm": len(only_a),
                    "changed_shared": len(changed),
                    "by_sector_only_control": by_sector(
                        {u: float(crows[u].get("mw") or 0.0) for u in only_c}, sec
                    ),
                    "by_sector_only_arm": by_sector(
                        {u: float(arows[u].get("mw") or 0.0) for u in only_a}, sec
                    ),
                    "classified_R1_sector1": sum(
                        1
                        for u in set(only_c) | set(only_a) | set(changed)
                        if sector_of(u, sec) == "1"
                    ),
                    "classified_R2_fleet_delta": sum(
                        1
                        for u in set(only_c) | set(only_a) | set(changed)
                        if sector_of(u, sec) != "1" and u in fleet_delta
                    ),
                    "unclassified_units": unclassified[:20],
                    "n_unclassified": len(unclassified),
                    "stop": bool(unclassified),
                }
                if rec["stop"]:
                    out["stops"].append(
                        {"year": y, "block": key, "n": len(unclassified)}
                    )
                    out["pass"] = False
            elif key == "capacity_clearing":
                rec = _clearing_diff(cv or {}, av or {}, y, divergent)
            else:
                rec = {
                    "kind": "aggregate",
                    "control": cv if not isinstance(cv, (list, dict)) else "…",
                    "arm": av if not isinstance(av, (list, dict)) else "…",
                    "detail": _aggregate_detail(cv, av),
                    "stop": False,
                }
            year_rows[key] = rec
        year_rows_ident = sorted(k for k in set(cl) | set(al) if cl.get(k) == al.get(k))
        out["per_year"][str(y)] = {
            "blocks_identical": year_rows_ident,
            "blocks_differing": year_rows,
        }
    out["pass"] = bool(out["pass"])
    return out


def _aggregate_detail(cv, av):
    if isinstance(cv, dict) and isinstance(av, dict):
        return {
            k: {"control": cv.get(k), "arm": av.get(k)}
            for k in sorted(set(cv) | set(av))
            if cv.get(k) != av.get(k)
        }
    if isinstance(cv, list) and isinstance(av, list):
        return {"control_len": len(cv), "arm_len": len(av)}
    return None


def _clearing_diff(cc: dict, ac: dict, year: int, divergent) -> dict:
    """``capacity_clearing`` gets its own reader: its ``offer_stack`` is a list
    of LISTS (not dicts), so the per-unit walker cannot key it, and its scalars
    are the auction's own outputs."""
    scal = sorted(
        {k for k, v in cc.items() if not isinstance(v, (list, dict))}
        | {k for k, v in ac.items() if not isinstance(v, (list, dict))}
    )
    cs = {r[0]: tuple(r) for r in cc.get("offer_stack", [])}
    as_ = {r[0]: tuple(r) for r in ac.get("offer_stack", [])}
    shared = set(cs) & set(as_)
    post = divergent is not None and year > divergent
    movers = [u for u in shared if abs(float(cs[u][2]) - float(as_[u][2])) > OFFER_TOL]
    unclassified = sorted(u for u in movers if not post or cs[u][1] in ZERO_EAS_FUELS)
    return {
        "kind": "capacity_clearing",
        "scalars": {
            k: {"control": cc.get(k), "arm": ac.get(k)}
            for k in scal
            if cc.get(k) != ac.get(k)
        },
        "stack_only_control": len(set(cs) - set(as_)),
        "stack_only_arm": len(set(as_) - set(cs)),
        "stack_shared": len(shared),
        "stack_offer_movers": len(movers),
        "classified_R3_eas_propagation": len(movers) - len(unclassified),
        "n_unclassified": len(unclassified),
        "unclassified_units": unclassified[:20],
        "stop": False,  # graded by W5'; reported here so the diff is complete
    }


# --------------------------------------------------------------------------
# W1 / W2 / W3 — D78-R's, on D78-R's readers
# --------------------------------------------------------------------------
def w123(ctl_leds, arm_leds, sec) -> dict:
    g: dict = {}
    w1: dict = {"per_year": {}, "pass": True}
    div = first_divergent_year(ctl_leds, arm_leds)
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        c, a = fail_rows(ctl_leds[y]), fail_rows(arm_leds[y])
        only_c, only_a, both = set(c) - set(a), set(a) - set(c), set(c) & set(a)
        shared_identical = all(abs(c[u] - a[u]) <= 1e-6 for u in both)
        c_gone, a_gone = exits_before(ctl_leds, y), exits_before(arm_leds, y)
        unexplained_c = sorted(
            u for u in only_c if sector_of(u, sec) != "1" and u not in a_gone
        )
        unexplained_a = sorted(u for u in only_a if u not in c_gone)
        exact = div is None or y <= div
        row = {
            "form": "exact" if exact else "fleet-delta",
            "only_control_rows": len(only_c),
            "only_control_mw": round(sum(c[u] for u in only_c), 3),
            "only_control_by_sector": by_sector({u: c[u] for u in only_c}, sec),
            "only_arm_rows": len(only_a),
            "only_arm_mw": round(sum(a[u] for u in only_a), 3),
            "shared_rows": len(both),
            "shared_mw_identical": shared_identical,
            "n_unexplained_control_only": len(unexplained_c),
            "unexplained_control_only": unexplained_c[:20],
            "n_unexplained_arm_only": len(unexplained_a),
            "unexplained_arm_only": unexplained_a[:20],
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
    w1["pass"] = bool(w1["pass"])
    g["W1"] = w1

    w2: dict = {"per_year": {}, "pass": True}
    for y, led in sorted(arm_leds.items()):
        counts = {
            kind: sum(1 for u in events(led, kind) if sector_of(u, sec) == "1")
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
    w2["pass"] = bool(w2["pass"])
    g["W2"] = w2

    w3: dict = {"per_year": {}, "pass": True}
    for y in sorted(set(ctl_leds) & set(arm_leds)):
        cdec, adec = events(ctl_leds[y], "decided"), events(arm_leds[y], "decided")
        ccap = events(ctl_leds[y], "entry_capped")
        c_gone = exits_before(ctl_leds, y)
        arm_only = set(adec) - set(cdec)
        unexplained = sorted(u for u in arm_only if u not in ccap and u not in c_gone)
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
            "n_unexplained_executed": len(exec_unexplained),
            "unexplained_executed": exec_unexplained[:20],
        }
        row["pass"] = not unexplained and not exec_unexplained
        w3["per_year"][str(y)] = row
        w3["pass"] &= row["pass"]
    w3["pass"] = bool(w3["pass"])
    g["W3"] = w3
    return g


# --------------------------------------------------------------------------
# the four-limb flip condition (D78 PRECOMMIT §7 / D58 §5), on W5'
# --------------------------------------------------------------------------
def flip_condition(g: dict, rep: dict) -> dict:
    a = g["W5prime"]["pass"]
    b = g["W1"]["pass"] and g["W2"]["pass"] and g["W3"]["pass"]
    sc = rep.get("score")
    c = d = None
    detail: dict = {}
    if sc:
        cp = (sc["control"]["fc3"]["release_precision_window"] or {}).get(
            "economic"
        ) or {}
        ap = (sc["arm"]["fc3"]["release_precision_window"] or {}).get("economic") or {}
        cprec, aprec = cp.get("precision"), ap.get("precision")
        c = (
            bool(cprec is not None and aprec is not None and aprec >= cprec)
            and g["W2"]["pass"]
        )
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
        # An ABSENT loyo block is NOT ADJUDICABLE, never a vacuous pass
        # (D78-R §7 limitation 5). Run with --flip-gate-extras to populate it.
        d = None if not cf else not lost
        detail["d"] = {
            "folds_computed": bool(cf),
            "control_folds": {y: cf[y].get("recall_band") for y in sorted(cf)},
            "arm_folds": {y: af.get(y, {}).get("recall_band") for y in sorted(af)},
            "folds_lost": lost,
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctl", required=True, type=Path)
    ap.add_argument("--arm", type=Path)
    ap.add_argument("--band-only", action="store_true")
    ap.add_argument("--out", type=Path, default=HERE / "window_compare2.json")
    args = ap.parse_args()

    sec = sectors()
    ctl_leds = load_legs(args.ctl)
    ctl_sum = summarise(ctl_leds, sec)
    band = w4_prime_band(ctl_sum, ctl_leds, sec)

    if args.band_only or args.arm is None:
        payload = {"control": ctl_sum, "w4_prime_band": band}
        out = HERE / "control_band.json"
        out.write_text(json.dumps(payload, indent=2))
        print(json.dumps(band, indent=2))
        print(f"\n-> {out}")
        return

    arm_leds = load_legs(args.arm)
    arm_sum = summarise(arm_leds, sec)
    div = first_divergent_year(ctl_leds, arm_leds)

    g = w123(ctl_leds, arm_leds, sec)
    g["W5prime"] = w5_prime(ctl_leds, arm_leds, div)
    arm_total = round(sum(s["decided_mw"] for s in arm_sum.values()), 3)
    g["W4prime"] = {
        "band": band,
        "arm_sum_decided_mw": arm_total,
        "delta_vs_control_mw": round(arm_total - band["sum_decided_mw_control"], 3),
        "on_point_value": abs(arm_total - band["point_value_exact_partition_mw"])
        <= MW_TOL,
        "pass": bool(band["band_lo_mw"] - MW_TOL <= arm_total <= band["band_hi_mw"]),
    }
    g["LEDGER"] = whole_ledger_diff(ctl_leds, arm_leds, sec, div)
    g["ALL_PASS"] = all(
        g[k]["pass"] for k in ("W1", "W2", "W3", "W4prime", "W5prime", "LEDGER")
    )

    rep = reported(ctl_sum, arm_sum, score_of(args.ctl), score_of(args.arm))
    payload = {
        "first_divergent_year": div,
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
                "first_divergent_year": div,
                "gates": {
                    k: g[k]["pass"]
                    for k in ("W1", "W2", "W3", "W4prime", "W5prime", "LEDGER")
                },
                "ALL_PASS": g["ALL_PASS"],
                "W4prime": {k: v for k, v in g["W4prime"].items() if k != "band"},
                "ledger_stops": g["LEDGER"]["stops"],
                "flip_condition": payload["flip_condition"]["limbs"],
                "recommendation": payload["flip_condition"]["recommendation"],
            },
            indent=2,
        )
    )
    print(f"\n-> {args.out}")


if __name__ == "__main__":
    main()
