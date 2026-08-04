"""pjm-153 — reachability adjudication for ``pjm_reserve_supply_cap`` (no LP).

pjm-151 §"filed as an observation" recorded, but explicitly declined to
adjudicate (rule 28(d): a census does not rule on mechanisms), that the PJM
keeper ``2026-08-03-pjm-151-seam-envelope`` arms ``pjm_reserve_supply_cap=True``
alongside ``pjm_reserve_pergen=True`` while *both* of that flag's read paths look
gated off by pergen. This probe settles it mechanically, from committed bytes:

1. **Census every read site** of ``pjm_reserve_supply_cap`` in ``src/`` -- so the
   adjudication rests on the set of readers the code actually has, not on the two
   the observation happened to name. (It names two; there are three.)

2. **Prove the pergen early-return dominates**, with ``ast``: inside
   ``model/reserves/spec.py``'s design builder, the ``if
   getattr(config, "pjm_reserve_pergen", False):`` block returns on *every*
   path, and the ``supply_cap = ...`` assignment is a later sibling statement at
   the same nesting depth. A statement after a block that always returns is
   unreachable whenever that block is entered -- that is the whole proof, and it
   is structural rather than a reading of the docstring.

3. **Prove the pergen ``ReserveDesign`` never receives a supply cap** -- the
   returned design's keyword arguments are enumerated and ``supply_cap`` is
   asserted absent, so the flag cannot reach the LP by that path either.

4. **Prove the commitment-prep reader is gated off** -- ``pipeline/commitment.py
   ::build_pjm_reserve_p1_prep`` returns ``(None, None)`` on a
   ``pjm_reserve_commitment_scoped`` guard placed before its
   ``pjm_reserve_supply_cap`` read; the keeper sets that flag ``False``.

5. **Replay the verdict against every committed PJM bundle** that records the
   field, so the finding covers the keeper line rather than one run.

**No LP is solved and nothing is deleted.** Rule 26 ``[R-DELETE]`` action on a
keeper-armed field is an owner call; this probe produces the evidence for it.
Training years only (it reads run configs, never a holdout series), rule 22.

Usage::

    PYTHONPATH=.:src python scripts/probes/pjm153_reserve_supply_cap_reachability.py
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src" / "market_sim"
SPEC = SRC / "model" / "reserves" / "spec.py"
PREP = SRC / "pipeline" / "commitment.py"
BUNDLES = REPO / "results" / "calibration"

FIELD = "pjm_reserve_supply_cap"
PERGEN = "pjm_reserve_pergen"
SCOPED = "pjm_reserve_commitment_scoped"
CAP_FN = "pjm_reserve_deliverable_supply_cap_mw"
PREP_FN = "build_pjm_reserve_p1_prep"


# --------------------------------------------------------------------------
# ast helpers
# --------------------------------------------------------------------------
def _gate_name(test: ast.expr) -> str | None:
    """Return the config field a gate tests, for the two forms the code uses.

    Both ``getattr(config, "<field>", False)`` and ``not getattr(...)`` appear at
    these sites, so a plain ``ast.Attribute`` walk would miss them.
    """
    node = test
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        node = node.operand
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "getattr":
        if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
            value = node.args[1].value
            return value if isinstance(value, str) else None
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _negated(test: ast.expr) -> bool:
    return isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not)


def _always_returns(body: list[ast.stmt]) -> bool:
    """True when every control-flow path through ``body`` ends in return/raise.

    Conservative by construction: a construct this does not understand yields
    ``False``, so the proof can only ever *under*-claim unreachability.
    """
    for stmt in body:
        if isinstance(stmt, (ast.Return, ast.Raise)):
            return True
        if isinstance(stmt, ast.If):
            # An if/else terminates only when BOTH limbs do; a bare `if` never
            # does, since the false path falls through.
            if stmt.orelse and _always_returns(stmt.body) and _always_returns(stmt.orelse):
                return True
        if isinstance(stmt, ast.With):
            if _always_returns(stmt.body):
                return True
        if isinstance(stmt, ast.Try):
            # Only a finally that always returns is unconditional.
            if stmt.finalbody and _always_returns(stmt.finalbody):
                return True
    return False


def _enclosing_functions(tree: ast.AST) -> list[ast.FunctionDef]:
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _read_sites(root: Path) -> list[dict]:
    """Every source location that reads ``FIELD``, with its enclosing function."""
    sites: list[dict] = []
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if FIELD not in text:
            continue
        tree = ast.parse(text, filename=str(path))
        owners: dict[int, str] = {}
        for fn in _enclosing_functions(tree):
            for node in ast.walk(fn):
                if hasattr(node, "lineno"):
                    owners.setdefault(node.lineno, fn.name)
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.Constant) and node.value == FIELD:
                name = FIELD
            elif isinstance(node, ast.Attribute) and node.attr == FIELD:
                name = FIELD
            if name is None:
                continue
            sites.append(
                {
                    "file": str(path.relative_to(REPO)),
                    "line": node.lineno,
                    "function": owners.get(node.lineno),
                }
            )
    # Collapse duplicates produced by nested nodes on one line.
    seen, uniq = set(), []
    for s in sites:
        key = (s["file"], s["line"])
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    return uniq


# --------------------------------------------------------------------------
# the three structural proofs
# --------------------------------------------------------------------------
def prove_spec_dominance() -> dict:
    """Prove the pergen block dominates the ``supply_cap`` assignment in spec.py."""
    tree = ast.parse(SPEC.read_text(encoding="utf-8"), filename=str(SPEC))
    for fn in _enclosing_functions(tree):
        # Locate the function whose *top-level* body holds both the pergen gate
        # and the supply_cap assignment; anything deeper is not the seam.
        pergen_if = None
        pergen_pos = None
        cap_pos = None
        for i, stmt in enumerate(fn.body):
            if (
                isinstance(stmt, ast.If)
                and _gate_name(stmt.test) == PERGEN
                and not _negated(stmt.test)
            ):
                pergen_if, pergen_pos = stmt, i
            if isinstance(stmt, ast.Assign):
                val = stmt.value
                if isinstance(val, ast.Call) and getattr(val.func, "id", None) == CAP_FN:
                    cap_pos = i
        if pergen_if is None or cap_pos is None:
            continue

        terminates = _always_returns(pergen_if.body)
        # The pergen limb's own returned ReserveDesign: does it pass supply_cap?
        kwargs_seen: list[str] = []
        for node in ast.walk(pergen_if):
            if isinstance(node, ast.Return) and isinstance(node.value, ast.Call):
                call = node.value
                if getattr(call.func, "id", None) == "ReserveDesign":
                    kwargs_seen = [k.arg for k in call.keywords if k.arg]
        return {
            "file": str(SPEC.relative_to(REPO)),
            "function": fn.name,
            "pergen_gate_line": pergen_if.lineno,
            "supply_cap_assign_line": fn.body[cap_pos].lineno,
            "same_nesting_depth": True,
            "supply_cap_assign_is_after_gate": cap_pos > (pergen_pos or -1),
            "pergen_block_always_returns": terminates,
            "pergen_returned_reservedesign_kwargs": sorted(kwargs_seen),
            "pergen_design_passes_supply_cap": "supply_cap" in kwargs_seen,
            "unreachable_when_pergen_true": bool(
                terminates and cap_pos > (pergen_pos or -1) and "supply_cap" not in kwargs_seen
            ),
        }
    return {"error": "seam not found in spec.py"}


def prove_prep_gate() -> dict:
    """Prove ``build_pjm_reserve_p1_prep`` returns before it reads ``FIELD``."""
    tree = ast.parse(PREP.read_text(encoding="utf-8"), filename=str(PREP))
    for fn in _enclosing_functions(tree):
        if fn.name != PREP_FN:
            continue
        guard_line = None
        for stmt in ast.walk(fn):
            if (
                isinstance(stmt, ast.If)
                and _gate_name(stmt.test) == SCOPED
                and _negated(stmt.test)
                and _always_returns(stmt.body)
            ):
                guard_line = stmt.lineno
        read_lines = [
            n.lineno
            for n in ast.walk(fn)
            if isinstance(n, ast.Constant) and n.value == FIELD
        ]
        return {
            "file": str(PREP.relative_to(REPO)),
            "function": fn.name,
            "scoped_guard_line": guard_line,
            "supply_cap_read_lines": sorted(read_lines),
            "guard_precedes_every_read": bool(
                guard_line is not None and read_lines and all(guard_line < r for r in read_lines)
            ),
        }
    return {"error": f"{PREP_FN} not found"}


def bundle_census() -> list[dict]:
    """Every committed PJM bundle recording the field, with its gating flags."""
    rows = []
    for cfg in sorted(BUNDLES.glob("*/run_config.json")):
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        sc = data.get("scenario_config", data)
        if not isinstance(sc, dict) or FIELD not in sc:
            continue
        if str(sc.get("iso", data.get("iso", ""))).upper() not in ("PJM", ""):
            continue
        cap = bool(sc.get(FIELD))
        pergen = bool(sc.get(PERGEN))
        scoped = bool(sc.get(SCOPED))
        rows.append(
            {
                "bundle": cfg.parent.name,
                FIELD: cap,
                PERGEN: pergen,
                SCOPED: scoped,
                # The flag can only reach the LP through the non-pergen design
                # path; the prep path additionally needs the scoped gate.
                "cap_observable": cap and not pergen,
            }
        )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=str(REPO / "results/calibration/_pjm153_supply_cap_reachability.json"),
    )
    args = ap.parse_args()

    record = {
        "_what": (
            "pjm-153: adjudicates the pjm-151 filed observation on "
            "pjm_reserve_supply_cap. Static (ast) reachability + bundle census; "
            "no LP, no deletion."
        ),
        "read_sites": _read_sites(SRC),
        "spec_dominance": prove_spec_dominance(),
        "prep_gate": prove_prep_gate(),
        "bundles": bundle_census(),
    }
    dom = record["spec_dominance"]
    prep = record["prep_gate"]
    record["verdict"] = {
        "inert_on_the_keeper": bool(
            dom.get("unreachable_when_pergen_true") and prep.get("guard_precedes_every_read")
        ),
        "basis": (
            "Both LP-facing readers are dominated by a gate the keeper sets "
            "against them: the design builder returns inside the pergen block "
            "before the supply_cap assignment (and its ReserveDesign passes no "
            "supply_cap), and the P1 prep returns on the commitment-scoped guard "
            "before its read."
        ),
    }

    out = Path(args.out)
    out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")

    print("=" * 72)
    print(f"pjm-153 — {FIELD} reachability (static, no LP)")
    print("=" * 72)
    print(f"\n[1] READ SITES in src/ ({len(record['read_sites'])})")
    for s in record["read_sites"]:
        print(f"    {s['file']}:{s['line']}  in {s['function']}")
    print("\n[2] spec.py dominance proof")
    for k, v in dom.items():
        print(f"    {k} = {v}")
    print("\n[3] pipeline/commitment.py gate proof")
    for k, v in prep.items():
        print(f"    {k} = {v}")
    print("\n[4] committed PJM bundles recording the field")
    for r in record["bundles"]:
        print(
            f"    {r['bundle']:<34} cap={str(r[FIELD]):<5} pergen={str(r[PERGEN]):<5}"
            f" scoped={str(r[SCOPED]):<5} → observable={r['cap_observable']}"
        )
    print(f"\nVERDICT inert_on_the_keeper = {record['verdict']['inert_on_the_keeper']}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
