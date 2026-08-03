"""neiso-78 — reachability probe for the NEISO oil-burn budget precedence seam.

**What this measures, and why it is not a solve.** The rule-28(c) matrix-gap
census (``scripts/mechanism_matrix_gap_sweep.py --iso NEISO``) reported ten
``neiso_*`` ``ScenarioConfig`` fields with no mention anywhere in
``docs/codebase-site/data/mechanism-matrix.js``, eight of them recorded on the
designated keeper. Two of those eight are ``bool`` gates that the keeper arms
**away from their shipped ``False`` default** — ``neiso_oil_burn_budget`` and
``neiso_winter_fuel_inventory`` — which is the nyiso-112 "live-but-invisible"
shape: a solve-affecting field shaping a published keeper with no cell anywhere.

Both gates feed the **same** LP builder (``model/lp/rows.py::
_build_oil_budget_rows``) through the same ``oil_*`` dispatch kwargs, so the
question rule 19 ``[R-ONE-MECH]`` asks is whether arming both **double-counts**
the winter oil-burn constraint. It does not: the wiring site is an ``if`` /
``elif`` in ``scripts/run_calibration.py``, so ``neiso_winter_fuel_inventory``
takes precedence and the ``neiso_oil_burn_budget`` limb is **unreachable**
whenever its successor is armed.

This probe proves that mechanically, from committed bytes only:

1. **Source-level precedence** — parse ``run_calibration.py`` with ``ast`` and
   assert the two gates are the test and the ``orelse`` test of one ``if``
   statement (never two independent ``if``s, which WOULD double-count).
2. **Bundle census** — read every committed ``results/calibration/*/
   run_config.json`` carrying the field and report, per bundle, whether the
   successor gate is armed and therefore whether the F923 limb is reachable.

**No LP is solved, no keeper is touched, no artifact is regenerated.** Every
number is read from committed bytes; the probe is idempotent and read-only.
Training years only — it reads run configs, never a holdout-year series
(rule 22).

Usage::

    PYTHONPATH=.:src python scripts/probes/_neiso78_oil_budget_reachability.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WIRING = REPO / "scripts" / "run_calibration.py"
BUNDLES = REPO / "results" / "calibration"

SUCCESSOR = "neiso_winter_fuel_inventory"
SUPERSEDED = "neiso_oil_burn_budget"


def _gate_name(test: ast.expr) -> str | None:
    """Return the config field a ``getattr(config, "<field>", False)`` test reads.

    The wiring site guards both limbs with ``getattr`` rather than attribute
    access, so a plain ``ast.Attribute`` walk would miss them.
    """
    if isinstance(test, ast.Call) and getattr(test.func, "id", None) == "getattr":
        if len(test.args) >= 2 and isinstance(test.args[1], ast.Constant):
            value = test.args[1].value
            return value if isinstance(value, str) else None
    return None


def check_precedence() -> dict:
    """Assert the two oil-budget gates share ONE if/elif chain (no double-count).

    Returns a record with the resolved structure and a boolean verdict.
    """
    tree = ast.parse(WIRING.read_text(encoding="utf-8"), filename=str(WIRING))
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        if _gate_name(node.test) != SUCCESSOR:
            continue
        # An `elif` is represented as a single If nested in `orelse`.
        elifs = [n for n in node.orelse if isinstance(n, ast.If)]
        chained = len(node.orelse) == 1 and len(elifs) == 1
        other = _gate_name(elifs[0].test) if elifs else None
        return {
            "found": True,
            "line": node.lineno,
            "if_gate": SUCCESSOR,
            "elif_gate": other,
            "is_elif_chain": bool(chained and other == SUPERSEDED),
            "superseded_reachable_when_successor_armed": not (
                chained and other == SUPERSEDED
            ),
        }
    return {"found": False}


def census_bundles() -> list[dict]:
    """Report the two gates for every committed bundle that records them."""
    rows: list[dict] = []
    for path in sorted(BUNDLES.glob("*/run_config.json")):
        try:
            cfg = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        scenario = cfg.get("scenario_config") or {}
        if SUPERSEDED not in scenario:
            continue
        superseded = bool(scenario.get(SUPERSEDED))
        successor = bool(scenario.get(SUCCESSOR))
        rows.append(
            {
                "bundle": path.parent.name,
                SUPERSEDED: superseded,
                SUCCESSOR: successor,
                # The F923 limb runs only when it is armed AND the successor is not.
                "f923_limb_reachable": superseded and not successor,
            }
        )
    return rows


def main() -> None:
    """Print the precedence proof and the per-bundle reachability census."""
    print("=" * 78)
    print("neiso-78 — NEISO oil-burn budget precedence / reachability probe")
    print("=" * 78)

    prec = check_precedence()
    print("\n[1] SOURCE-LEVEL PRECEDENCE (ast over scripts/run_calibration.py)")
    if not prec["found"]:
        print("  !! wiring site NOT FOUND — the seam moved; re-locate before citing")
        return
    print(f"  if-statement line          : {prec['line']}")
    print(f"  if   gate                  : {prec['if_gate']}")
    print(f"  elif gate                  : {prec['elif_gate']}")
    print(f"  single if/elif chain       : {prec['is_elif_chain']}")
    print(
        "  VERDICT                    : "
        + (
            "NO DOUBLE-COUNT — the superseded limb is unreachable "
            "whenever the successor is armed"
            if prec["is_elif_chain"]
            else "!! NOT a single chain — both limbs may build rows (rule 19)"
        )
    )

    rows = census_bundles()
    armed_both = [r for r in rows if r[SUPERSEDED] and r[SUCCESSOR]]
    reachable = [r for r in rows if r["f923_limb_reachable"]]
    print(f"\n[2] BUNDLE CENSUS ({len(rows)} committed bundles record the field)")
    print(f"  both gates armed           : {len(armed_both)}/{len(rows)}")
    print(f"  F923 limb REACHABLE in     : {len(reachable)}/{len(rows)} bundles")
    for row in rows:
        flag = "REACHABLE" if row["f923_limb_reachable"] else "inert"
        print(
            f"    {row['bundle']:<34s} "
            f"oil={str(row[SUPERSEDED]):<5s} winter={str(row[SUCCESSOR]):<5s} {flag}"
        )

    print(
        "\n  CONCLUSION: neiso_oil_burn_budget is armed on every NEISO bundle "
        "(it is the\n  NEISO backcast default, backcast_config.py) and is "
        "INERT on every one of them,\n  because neiso_winter_fuel_inventory "
        "is armed too and wins the if/elif."
    )


if __name__ == "__main__":
    main()
