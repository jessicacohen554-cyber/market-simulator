#!/usr/bin/env python3
"""capx D76 phase 2 — the rule-29 STRUCTURAL screen gate, per ISO. Zero LP.

Grades one phase-2 A/B (arm vs control at the SAME head) against the STOP gates
pre-registered in ``PRECOMMIT-capx-d76-p2-2026-09-06.md`` §4 — **and against
nothing else**. A STOP may KILL an arm; it can never promote one, it contributes
to no determination, and not one of these is gated on a residual. The §5
pre-declared expectations are REPORTED separately and marked not-a-gate.

Phase 1's grader (``screen_gate.py``) is the parent; two things are new here:

* **The whole-ledger diff (D81 rec 4).** Every key of every year's ledger is
  diffed and assigned to a PRE-DECLARED partition — INVARIANT (a move is a STOP
  kill), SEAM (the gate's own object), SCREEN (the rule-19 consumers phase 0 §4.2
  enumerated), DECISION, FLEET, ACCOUNTING. A key that moves and belongs to no
  declared class is reported ``UNCLASSIFIED`` and the FINDING must explain it;
  the partition is fixed here, before the solves, so it cannot be widened to
  absorb a surprise.
* **STOP 5 is testable for the full-span leg.** A truncated 2021-2023 window
  produces no scorer output at all (phase 1 §6.1); PJM's 2021-2025 span scores,
  so its FC rows are read and compared.

Input numbers (the measured peak the arm must produce, the control's seam peak)
are read from ``p2_predeclare.json`` — fixed at HEAD before any LP — never
recomputed here, so the identity test cannot drift onto the result.

Usage::

    python docs/handoffs/d76/p2_gate.py --iso PJM \
        --control results/hindcast/d76p2-pjm-control \
        --arm     results/hindcast/d76p2-pjm-arm
"""

import argparse
import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.iso_configs import apply_iso_scenario_defaults
from scripts.run_capacity_hindcast import build_config

HERE = Path(__file__).resolve().parent
PREDECLARE = HERE / "p2_predeclare.json"

# runner.py:2125 guards the requirement/position block on ``prior_results is not
# None``: the window's first year writes a ``screen_peak_demand_mw`` no screen
# consumed. 2021 is that year in every phase-2 leg.
PRE_SCREEN_YEAR = 2021

# --------------------------------------------------------------------------- #
# THE PRE-DECLARED LEDGER PARTITION (D81 rec 4). Fixed before any phase-2 solve.
# --------------------------------------------------------------------------- #

# Class A — INVARIANT. Pure functions of the MEASURED load, or run identity.
# Identical in both legs, in every year. A move is a STOP 4 KILL.
LEDGER_INVARIANT = frozenset({
    "peak_demand_mw", "adequacy_requirement_mw",
    "iso", "year", "ledger_version", "mode", "hindcast", "bridge",
})

# Class B — THE SEAM. The gate's own object; it moves by the pre-declared delta.
LEDGER_SEAM = frozenset({"screen_peak_demand_mw"})

# Class C — SCREEN CONSUMERS. The rule-19 enumeration of phase 0 §4.2, as it
# surfaces in the ledger: the requirement / entering-firm census / CR-1 position
# the three screens shared, and the D59 locality rows.
LEDGER_SCREEN = frozenset({
    "screen_adequacy_requirement_mw", "screen_entering_firm_mw",
    "screen_reserve_position", "capacity_reserve_position", "locality_capacity",
})

# Class D — DECISIONS the screens made against that operand.
LEDGER_DECISION = frozenset({
    "retirements", "thermal_additions", "renewable_additions",
    "storage_additions", "ccs_retrofits", "floor_retained", "entry_pipeline",
    "entry_decided_mw_by_tech", "entry_screen_diagnostics", "pipeline_events",
    "announced_derates", "confirmed_derates",
})

# Class E — FLEET STATE consequent on those decisions, and the accreditation
# trail computed off it. ``fleet_by_fuel_before`` is here because year Y+1's
# before IS year Y's after; in the FIRST year of the window it must be identical
# and the grader checks that separately.
LEDGER_FLEET = frozenset({
    "fleet_by_fuel_after", "fleet_by_fuel_before", "firm_clean_mw",
    "firm_clean_accredited_mw", "storage_firm_mw", "storage_power_mw",
    "wind_cap_mw", "solar_cap_mw", "renewable_credit_applied", "reserve_margin",
})

# Class F — LP / solver accounting that follows the fleet.
LEDGER_ACCOUNTING = frozenset({"rps_dual", "solve_counts"})

CLASSES = (
    ("INVARIANT", LEDGER_INVARIANT), ("SEAM", LEDGER_SEAM),
    ("SCREEN", LEDGER_SCREEN), ("DECISION", LEDGER_DECISION),
    ("FLEET", LEDGER_FLEET), ("ACCOUNTING", LEDGER_ACCOUNTING),
)

# Per-leg bookkeeping in run_config.json that NAMES the leg and must differ
# between any two runs. The PRECOMMIT's STOP 3 object is "every GATE recorded in
# run_config.json", which lives in the nested ``scenario_config`` blob.
RUN_CONFIG_LEG_BOOKKEEPING = frozenset(
    {"cache_key", "run_dir", "scenario_config", "scenario_config_source", "timestamp"}
)

ALL_ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM")


def classify(key: str) -> str:
    """Return the pre-declared partition class of one ledger key."""
    for name, members in CLASSES:
        if key in members:
            return name
    return "UNCLASSIFIED"


def summarize(v):
    """A compact, diffable rendering of one ledger value."""
    if isinstance(v, list):
        return f"list[{len(v)}]"
    if isinstance(v, dict):
        return {k: v[k] for k in sorted(v)}
    return v


def ledgers(bundle: Path, iso: str) -> dict[int, dict]:
    """Load a bundle's committed per-year evolution ledgers."""
    root = bundle / iso
    keys = [p for p in root.iterdir() if p.is_dir()]
    if len(keys) != 1:
        raise RuntimeError(f"{bundle}: expected one cache-key dir, got {keys}")
    return {
        int(p.name[len("evolution_"): -len(".json")]): json.loads(p.read_text())
        for p in sorted(keys[0].glob("evolution_*.json"))
    }


def run_config(bundle: Path) -> dict:
    """Return the bundle's recorded ``run_config.json``."""
    return json.loads((bundle / "run_config.json").read_text())


def predeclared(iso: str) -> dict:
    """The pre-solve numbers for this ISO, from ``p2_predeclare.json``."""
    blob = json.loads(PREDECLARE.read_text())
    for blk in blob["predeclare"]:
        if blk["iso"] == iso:
            return {"years": {int(y): r for y, r in blk["years"].items()},
                    "keys": blob["leg_keys"][iso]}
    raise RuntimeError(f"{iso}: no pre-declaration recorded")


# --------------------------------------------------------------------------- #
# STOPs
# --------------------------------------------------------------------------- #

def stop1() -> tuple[bool, list[str]]:
    """STOP 1 — 'no pre-existing cache key moves', re-asserted at this head."""
    notes, ok = [], True
    for iso in ALL_ISOS:
        for label, kw in (("t1h", {}), ("t1x", {"crossover": True})):
            span = (2023, 2027) if kw else (2021, 2025)
            vintage = 2023 if kw else 2020

            def key(**over):
                return apply_iso_scenario_defaults(
                    build_config(iso, span[0], span[1], "realized",
                                 vintage=vintage, **kw, **over), iso).cache_key()

            bare = key()
            if key(capacity_screen_peak_measured_hindcast=False) != bare:
                ok = False
                notes.append(f"{iso}/{label}: explicit-OFF != bare")
            if key(capacity_screen_peak_measured_hindcast=True) == bare:
                ok = False
                notes.append(f"{iso}/{label}: armed key did not move")
    return ok, notes or ["12 recipe keys: explicit-OFF == bare, armed distinct"]


def stop2(arm: dict[int, dict], pre: dict) -> tuple[bool, list[str]]:
    """STOP 2 — the identity, to the MW.

    The arm's ``screen_peak_demand_mw`` equals the year's PRE-DECLARED measured
    peak to the MW in every binding year, and equals the ledger's own
    ``peak_demand_mw`` in every solved year. A miss of more than 0.001 MW kills.
    """
    notes, ok = [], True
    for year, row in sorted(pre["years"].items()):
        if year not in arm:
            continue
        got = arm[year].get("screen_peak_demand_mw")
        want = row["measured_peak_mw"]
        d = abs(float(got) - float(want))
        notes.append(
            f"{year}: screen peak {got:,.3f} vs pre-declared measured "
            f"{want:,.3f} -> Δ {d:.3f} MW"
            + ("  (binding)" if row["screen_binds"] else "  (pre-screen year)")
        )
        if d > 0.001:
            ok = False
    for year, led in sorted(arm.items()):
        lp = led.get("peak_demand_mw")
        if lp is None:
            continue  # bridge year: evolved, never solved -- no LP peak exists
        d = abs(float(led["screen_peak_demand_mw"]) - float(lp))
        notes.append(f"{year}: screen peak vs the LP's own peak -> Δ {d:.3f} MW")
        if d > 0.001:
            ok = False
    return ok, notes


def stop3(c: dict[int, dict], a: dict[int, dict],
          cb: Path, ab: Path) -> tuple[bool, list[str]]:
    """STOP 3 — 'every non-peak operand byte-identical'.

    The gate object is every GATE recorded in ``run_config.json`` (the nested
    ``scenario_config``), plus the pre-screen year's DECISION fields.

    **Pre-registered correction, made before any phase-2 result existed.** Phase
    1 required the 2021 ledger to be *identical* and took a LITERAL MISS on
    ``screen_peak_demand_mw`` — the D52 observability field ``runner.py`` writes
    unconditionally in a year where no screen consumes it. Phase 2 pre-registers
    the corrected text: 2021 must be identical in every field EXCEPT that one,
    and any DECISION field moving there kills the arm.
    """
    notes, ok = [], True
    rc_c, rc_a = run_config(cb), run_config(ab)
    top_diff = [k for k in sorted(set(rc_c) | set(rc_a)) if rc_c.get(k) != rc_a.get(k)]
    extra = sorted(set(top_diff) - RUN_CONFIG_LEG_BOOKKEEPING)
    notes.append(f"run_config top-level differs in {len(top_diff)}: {top_diff} "
                 f"(beyond per-leg bookkeeping: {extra or 'none'})")
    if extra:
        ok = False
        notes.append("UNEXPECTED non-bookkeeping run_config difference")
    sc, sa = rc_c.get("scenario_config") or {}, rc_a.get("scenario_config") or {}
    gate_diff = [k for k in sorted(set(sc) | set(sa)) if sc.get(k) != sa.get(k)]
    notes.append(f"scenario_config (THE pre-registered object) differs in: {gate_diff}")
    if gate_diff != ["capacity_screen_peak_measured_hindcast"]:
        ok = False
        notes.append("UNEXPECTED gate difference -- more than this lane's own gate moved")
    lc, la = c.get(PRE_SCREEN_YEAR) or {}, a.get(PRE_SCREEN_YEAR) or {}
    changed = [k for k in sorted(set(lc) | set(la)) if lc.get(k) != la.get(k)]
    allowed = sorted(LEDGER_SEAM)
    notes.append(f"{PRE_SCREEN_YEAR} pre-screen ledger differs in {changed} "
                 f"of {len(set(lc) | set(la))} fields (allowed: {allowed})")
    for k in changed:
        if k not in LEDGER_SEAM:
            ok = False
            notes.append(f"{PRE_SCREEN_YEAR}.{k} moved [{classify(k)}] -- STOP 3 KILL")
    return ok, notes


def stop4(c: dict[int, dict], a: dict[int, dict]) -> tuple[bool, list[str]]:
    """STOP 4 — 'the footprint is confined to the rows the mechanism claims'.

    Every Class-A INVARIANT key is identical in every year, and no key moves
    that belongs to no declared class.
    """
    notes, ok = [], True
    for year in sorted(set(c) & set(a)):
        for f in sorted(LEDGER_INVARIANT):
            cv, av = c[year].get(f), a[year].get(f)
            if cv is None and av is None:
                continue
            if cv != av:
                ok = False
                notes.append(f"{year}.{f}: {cv} -> {av}  ** NOT INVARIANT — KILL **")
    for year in sorted(set(c) & set(a)):
        for k in sorted(set(c[year]) | set(a[year])):
            if c[year].get(k) != a[year].get(k) and classify(k) == "UNCLASSIFIED":
                ok = False
                notes.append(f"{year}.{k} moved and is UNCLASSIFIED -- KILL")
    if ok:
        notes.append(
            f"every Class-A invariant identical in {sorted(set(c) & set(a))}; "
            "no unclassified key moved")
    return ok, notes


def whole_ledger_diff(c: dict[int, dict], a: dict[int, dict]) -> dict:
    """D81 rec 4 — diff EVERY key of EVERY year and class each difference."""
    out = {}
    for year in sorted(set(c) | set(a)):
        lc, la = c.get(year) or {}, a.get(year) or {}
        rows = {}
        for k in sorted(set(lc) | set(la)):
            if lc.get(k) == la.get(k):
                continue
            rows[k] = {"class": classify(k),
                       "control": summarize(lc.get(k)), "arm": summarize(la.get(k))}
        out[year] = {"n_fields": len(set(lc) | set(la)), "n_moved": len(rows),
                     "moved": rows}
    return out


def _mw(rows) -> float:
    """Total MW of a ledger row list (rows carry ``mw``; ``capacity_mw`` on some)."""
    return sum(float(r.get("capacity_mw") or r.get("mw") or 0) for r in rows)


def report(c: dict[int, dict], a: dict[int, dict]) -> dict:
    """PRECOMMIT §5 — pre-declared expectations. REPORTED, never a gate."""
    out = {}
    for year in sorted(set(c) & set(a)):
        out[year] = {f: {"control": c[year].get(f), "arm": a[year].get(f)}
                     for f in ("screen_peak_demand_mw",
                               "screen_adequacy_requirement_mw",
                               "screen_entering_firm_mw", "screen_reserve_position",
                               "reserve_margin")}
        for f in ("retirements", "thermal_additions", "renewable_additions",
                  "storage_additions", "floor_retained"):
            cl, al = c[year].get(f) or [], a[year].get(f) or []
            out[year][f] = {
                "control_rows": len(cl), "arm_rows": len(al),
                "control_mw": round(_mw(cl), 3), "arm_mw": round(_mw(al), 3),
            }
            # Retirement rows carry a ``reason`` (announced / confirmed /
            # economic). The gate's channel is the ECONOMIC screen, so an
            # aggregate row count hides whether an exogenous exit moved -- it
            # must not. Split by reason so the FINDING can say which did.
            if f == "retirements":
                reasons = sorted({r.get("reason") for r in cl} | {r.get("reason") for r in al})
                out[year]["retirements_by_reason"] = {
                    str(rs): {
                        "control_rows": sum(1 for r in cl if r.get("reason") == rs),
                        "arm_rows": sum(1 for r in al if r.get("reason") == rs),
                        "control_mw": round(_mw([r for r in cl if r.get("reason") == rs]), 3),
                        "arm_mw": round(_mw([r for r in al if r.get("reason") == rs]), 3),
                    }
                    for rs in reasons
                }
        fc = c[year].get("fleet_by_fuel_after") or {}
        fa = a[year].get("fleet_by_fuel_after") or {}
        out[year]["fleet_by_fuel_after_delta"] = {
            k: round(float(fa.get(k, 0.0)) - float(fc.get(k, 0.0)), 3)
            for k in sorted(set(fc) | set(fa))
            if abs(float(fa.get(k, 0.0)) - float(fc.get(k, 0.0))) > 1e-6
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", required=True)
    ap.add_argument("--control", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    pre = predeclared(args.iso)
    ctrl, arm = ledgers(args.control, args.iso), ledgers(args.arm, args.iso)
    results = {}
    for name, fn, fnargs in (
        ("STOP 1 cache keys", stop1, ()),
        ("STOP 2 identity", stop2, (arm, pre)),
        ("STOP 3 non-peak operands", stop3, (ctrl, arm, args.control, args.arm)),
        ("STOP 4 footprint", stop4, (ctrl, arm)),
    ):
        ok, notes = fn(*fnargs)
        results[name] = {"pass": ok, "notes": notes}
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        for n in notes:
            print(f"        {n}")
        print()

    diff = whole_ledger_diff(ctrl, arm)
    print("WHOLE-LEDGER DIFF (D81 rec 4) — every moved key, classed:")
    for year, blk in diff.items():
        print(f"  {year}: {blk['n_moved']}/{blk['n_fields']} fields moved")
        for k, r in blk["moved"].items():
            print(f"      [{r['class']:<12}] {k}")
    print()

    verdict = "PASS" if all(r["pass"] for r in results.values()) else "FAIL"
    print(f"SCREEN GATE (STOPs 1-4, structural), {args.iso}: {verdict}")
    print("STOP 5 (no non-target load-bearing flip) is graded separately from "
          "the scorer output, and only where the window produces one.")

    out = args.out or (HERE / f"p2_gate_{args.iso.lower()}.json")
    out.write_text(json.dumps({
        "iso": args.iso, "verdict": verdict, "leg_keys": pre["keys"],
        "stops": results, "whole_ledger_diff": diff,
        "reported_not_gated": report(ctrl, arm),
    }, indent=2) + "\n")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
