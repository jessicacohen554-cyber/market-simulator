"""closeout-NEISO W0 regression guard: compare a control and an arm census and apply the tripwires.

Inputs are two ``w0_guard_census.py`` outputs for the same year. Exit 0 = every
zero-LP tripwire in SPEC-closeout-neiso-w0-regression-guard-2026-10-02.md §2 holds;
exit 1 = at least one trips (each is printed); class energy / mc moves are printed as MOVE lines. The post-solve C3a tripwire (§3) is
read from the scored bundles, not here.

Usage:
    python docs/records/neiso/closeout-w1/w0_guard_compare.py control_2019.json arm_2019.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

#: W0 census tolerances (owner ruling D-P2 / R-2; closeout plan §2.1 row 6): class
#: capacity within 1 %, total capacity within 0.5 %. The plan's third tolerance (3 %)
#: is model-vs-ISO-report and has no control-vs-arm analogue, so it is not applied.
#: Available-energy and mean-mc moves are REPORTED, not tripped: the price-side
#: tripwire is the post-solve C3a move (spec §3), not an invented input threshold.
CAP_TOL = 0.01
TOTAL_CAP_TOL = 0.005


def _rel(a: float, b: float) -> float:
    """Relative difference of b against a (0 when both are zero)."""
    return abs(b - a) / abs(a) if a else (0.0 if b == 0 else float("inf"))


def compare(control: dict, arm: dict) -> list[str]:
    """Return the list of tripped wires (empty = pass)."""
    trips: list[str] = []
    y = control["year"]
    key = lambda r: r["unit_id"]  # noqa: E731
    c_watch = {key(r): r for r in control["watch"]}
    a_watch = {key(r): r for r in arm["watch"]}
    for uid in sorted(set(c_watch) | set(a_watch)):
        if uid not in a_watch or uid not in c_watch:
            trips.append(f"{y} watched unit {uid} {'lost' if uid in c_watch else 'added'}")
            continue
        if c_watch[uid] != a_watch[uid]:
            diff = {k: (c_watch[uid][k], a_watch[uid][k])
                    for k in c_watch[uid] if c_watch[uid][k] != a_watch[uid].get(k)}
            trips.append(f"{y} watched unit {uid} not byte-stable: {diff}")
    for cls in sorted(set(control["by_class"]) | set(arm["by_class"])):
        c, a = control["by_class"].get(cls), arm["by_class"].get(cls)
        if c is None or a is None:
            trips.append(f"{y} class {cls} {'lost' if a is None else 'added'}")
            continue
        if _rel(c["cap_mw"], a["cap_mw"]) > CAP_TOL:
            trips.append(f"{y} class {cls} capacity {c['cap_mw']} -> {a['cap_mw']} MW (> {CAP_TOL:.0%})")
    c_tot = sum(v["cap_mw"] for v in control["by_class"].values())
    a_tot = sum(v["cap_mw"] for v in arm["by_class"].values())
    if _rel(c_tot, a_tot) > TOTAL_CAP_TOL:
        trips.append(f"{y} total capacity {c_tot:.1f} -> {a_tot:.1f} MW (> {TOTAL_CAP_TOL:.1%})")
    return trips


def report_moves(control: dict, arm: dict) -> list[str]:
    """Per-class available-energy and mean-mc moves (reported, never tripped)."""
    lines = []
    for cls in sorted(set(control["by_class"]) & set(arm["by_class"])):
        c, a = control["by_class"][cls], arm["by_class"][cls]
        if (c["avail_twh"], c["mc_base_mean"]) != (a["avail_twh"], a["mc_base_mean"]):
            lines.append(f"{cls}: avail {c['avail_twh']} -> {a['avail_twh']} TWh, "
                         f"mean mc {c['mc_base_mean']} -> {a['mc_base_mean']}")
    return lines


def main() -> int:
    """CLI: compare two census files and report."""
    control, arm = (json.loads(Path(p).read_text()) for p in sys.argv[1:3])
    moved = sorted(k for k in control["digest"] if control["digest"][k] != arm["digest"][k])
    print(f"{control['year']}: units {control['n_units']} -> {arm['n_units']}; "
          f"LP-input arrays moved: {moved or 'none'}")
    for line in report_moves(control, arm):
        print("MOVE", line)
    trips = compare(control, arm)
    for t in trips:
        print("TRIP", t)
    print("PASS" if not trips else f"FAIL ({len(trips)} trips)")
    return 1 if trips else 0


if __name__ == "__main__":
    raise SystemExit(main())
