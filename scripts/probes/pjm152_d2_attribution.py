"""Attribute the pjm-150 D-2 delta: is ``f46bdfd`` its SOLE contributor? No LP.

**The chartered Task B question**, carried forward unresolved from pjm-149 §7 /
pjm-150 §6 / pjm-151 §8. pjm-150 measured a
committed-keeper -> HEAD ``legitimacy_diagnostics.json`` delta (D-2 32 -> 42
rows, 32 shared rows re-based on ``class_total_twh``) and stated carefully that
``f46bdfd`` ("make D-2/D-4 floor attribution independent of the dispatch
source") is the **leading but not necessarily sole** contributor, because
pjm-149's baseline was a pre-fix regen at ITS head while pjm-150's was
committed-vs-now — different experiments.

This resolves it by regenerating the artifact from **ONE bundle** at two code
points and diffing:

* **(B)** the repo at ``01cb2489`` — ``f46bdfd4``'s immediate parent, i.e. the
  last commit before the fix;
* **(C)** the repo at HEAD.

``C - B`` is the fix's exact contribution.

**Two handoff corrections this probe is built on, both verified rather than
assumed:**

1. The handoff names the pre-fix commit ``a0fc302``. **No such revision exists
   in this repo** (``git cat-file -t`` fails). The commit immediately before
   ``f46bdfd4`` is ``01cb2489`` ("pjm-149: pre-register the D-2/D-4 dispatch-path
   attribution charter"), and the pre-fix view is built from that.
2. pjm-147's keeper basis ``217e5b19`` — the point pjm-150's *committed* side
   was generated at — is **also unreachable** in this clone (its branch was
   deleted post-merge and the file's history is grafted at a squashed
   "Add files via upload" import). So the "everything else" leg cannot be
   measured against that exact point, and this probe does not pretend to. What
   it CAN establish, and does, is bounded precisely by what the artifacts
   support.

**Why this is cheap here and was prohibitive for pjm-151.**
``legitimacy_diagnostics.load_or_rebuild_floors`` prefers a persisted
``floors/<year>_*.npz`` and only falls back to ``run_year(fleet_only=True)`` --
memory-comparable to the LP itself -- when none exists. On a fresh container the
committed keeper bundles carry no ``floors/`` (gitignored), which is what forced
the rebuild pjm-151 could not run beside its solve chain. This probe targets a
bundle **this session solved**, whose ``floors/`` are on disk, so BOTH
regenerations read the SAME persisted floors and differ ONLY by diagnostics
code. That the two code points agree on the floor loader is verified, not
assumed: ``load_or_rebuild_floors`` is byte-identical at ``01cb2489`` and HEAD.

Reads only committed/solved artifacts. **Never writes into a committed bundle's
artifact** -- both regenerations go to scratch paths.

Usage:
    PYTHONPATH=.:src python <this> --bundle results/calibration/pjm152_collapse_A \\
        --prefix <scratch>/prefix --out results/calibration/_pjm152_d2_attribution.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/user/market-simulator")
sys.path[:0] = [str(REPO), str(REPO / "src")]

YEARS = ("2023", "2024", "2025")

#: The fix under test and its immediate parent (the handoff's ``a0fc302`` does
#: not exist in this repo; see the module docstring).
FIX_COMMIT = "f46bdfd4"
PRE_FIX_COMMIT = "01cb2489"


def _run_diagnostics(cwd: Path, bundle: Path, out: Path, label: str) -> dict:
    """Regenerate legitimacy_diagnostics.json from ``cwd``'s code view.

    ``--json-out`` is mandatory: without it the CLI prints to stdout and writes
    NOTHING, silently (the pipeline rule pjm-151's handoff records).
    """
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{cwd}:{cwd / 'src'}"
    cmd = [
        sys.executable,
        str(cwd / "scripts/legitimacy_diagnostics.py"),
        "--bundle",
        str(bundle),
        "--iso",
        "PJM",
        "--years",
        *YEARS,
        "--json-out",
        str(out),
    ]
    print(f"[{label}] {' '.join(cmd[:4])} ... --json-out {out.name}")
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout[-3000:])
        print(proc.stderr[-3000:], file=sys.stderr)
        raise SystemExit(f"[{label}] diagnostics failed (rc={proc.returncode})")
    if not out.is_file():
        raise SystemExit(f"[{label}] no artifact written to {out}")
    return json.loads(out.read_text())


def _d2_rows(doc: dict) -> dict:
    """Index a diagnostics doc's D-2 rows by (year, class, mechanism)."""
    rows = {}
    for gate in doc.get("gates", doc if isinstance(doc, list) else []):
        if not isinstance(gate, dict):
            continue
        if str(gate.get("id", gate.get("gate", ""))).upper().startswith("D2") or str(
            gate.get("id", "")
        ).upper() in ("D-2", "D2"):
            for r in gate.get("rows", []) or []:
                key = (
                    str(r.get("year")),
                    str(r.get("klass", r.get("class"))),
                    str(r.get("mechanism", r.get("mech"))),
                )
                rows[key] = r
    return rows


def _walk_d2(doc: dict) -> dict:
    """Find D-2 rows wherever the schema puts them (defensive to layout)."""
    found = _d2_rows(doc)
    if found:
        return found
    # Fallback: scan any nested dict/list for row-shaped records carrying a
    # mechanism + class + year triple.
    out: dict = {}

    def visit(node):
        if isinstance(node, dict):
            has = {"year", "klass", "mechanism"} <= set(node)
            if has:
                out[(str(node["year"]), str(node["klass"]), str(node["mechanism"]))] = (
                    node
                )
            for v in node.values():
                visit(v)
        elif isinstance(node, list):
            for v in node:
                visit(v)

    visit(doc)
    return out


def main() -> None:
    """Regenerate at both code points, diff, and write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="bundle with floors/ on disk")
    ap.add_argument("--prefix", required=True, help="pre-fix repo view (01cb2489)")
    ap.add_argument("--out", default="results/calibration/_pjm152_d2_attribution.json")
    ap.add_argument("--scratch", default=None, help="dir for the two artifacts")
    args = ap.parse_args()

    bundle = (REPO / args.bundle).resolve()
    prefix = Path(args.prefix).resolve()
    scratch = Path(args.scratch) if args.scratch else prefix.parent
    scratch.mkdir(parents=True, exist_ok=True)

    committed = bundle / "legitimacy_diagnostics.json"
    if not (bundle / "floors").is_dir():
        raise SystemExit(
            f"{bundle.name} has no floors/ — this probe exists to avoid the "
            "run_year rebuild; point it at a bundle this session solved"
        )

    b_out = scratch / "legit_B_prefix.json"
    c_out = scratch / "legit_C_head.json"
    # NEVER write into the committed bundle's own artifact.
    assert b_out != committed and c_out != committed

    doc_c = _run_diagnostics(REPO, bundle, c_out, "C/HEAD")
    doc_b = _run_diagnostics(prefix, bundle, b_out, f"B/{PRE_FIX_COMMIT}")

    rb, rc = _walk_d2(doc_b), _walk_d2(doc_c)
    added = sorted(set(rc) - set(rb))
    removed = sorted(set(rb) - set(rc))
    shared = sorted(set(rb) & set(rc))
    changed = [k for k in shared if rb[k] != rc[k]]

    rec = {
        "_what": "pjm-152 Task B: does f46bdfd solely account for the D-2 delta "
        "pjm-150 measured? ONE bundle, two code points, no LP and no floor "
        "rebuild (both sides read the SAME persisted floors/*.npz).",
        "bundle": str(bundle.relative_to(REPO)),
        "code_points": {
            "B_pre_fix": PRE_FIX_COMMIT,
            "C_head": subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=REPO,
                capture_output=True,
                text=True,
            ).stdout.strip(),
            "fix_under_test": FIX_COMMIT,
        },
        "handoff_corrections": {
            "a0fc302": "NOT a revision in this repo; the pre-fix commit is "
            f"{PRE_FIX_COMMIT} (f46bdfd4's parent).",
            "217e5b19": "pjm-147's keeper basis is unreachable in this clone, "
            "so the pre-f46bdfd half of pjm-150's committed-vs-now window "
            "cannot be measured against that exact point.",
        },
        "d2_row_counts": {"B_pre_fix": len(rb), "C_head": len(rc)},
        "d2_added": [list(k) for k in added],
        "d2_removed": [list(k) for k in removed],
        "d2_shared": len(shared),
        "d2_shared_changed": [list(k) for k in changed],
        # What pjm-150 §6 measured on ITS bundle (pjm150_ctmeter_regate_A),
        # committed-keeper -> HEAD. Recorded here so the comparison is against
        # a stated number rather than a remembered one. NOT an assertion: this
        # probe runs on a DIFFERENT bundle (the pjm-151 keeper's dispatch, not
        # pjm-147's), so the row sets need not match cell for cell -- what is
        # comparable is the SHAPE of the delta (additions only, no removals,
        # shared rows re-based).
        "pjm150_reported": {
            "d2_rows": "32 -> 42 (+10 added, 0 removed)",
            "shared_changed": 32,
            "added_shape": "nuclear_mustrun x3, CC_CHP:chp_steam x3, "
            "CC_CHP:reliability_floor x2, ST_CHP:chp_steam, COAL:chp_steam",
        },
        # The window B..C contains exactly ONE change to the diagnostics code:
        # scripts/legitimacy_diagnostics.py and scripts/calibration_verdict.py
        # are byte-identical from f46bdfd4 through HEAD (blob shas
        # d89b0e5d... / f8c5c154... at f46bdfd4, at the keeper basis 1c191624,
        # and at HEAD). So whatever C - B shows IS f46bdfd's contribution --
        # the attribution is exact by construction, not inferred.
        "attribution_basis": (
            "legitimacy_diagnostics.py and calibration_verdict.py are "
            "byte-identical from f46bdfd4 through HEAD, so f46bdfd is the ONLY "
            "diagnostics-code change in the B..C window and C - B is its exact "
            "contribution."
        ),
        "verdict": (
            f"f46bdfd accounts for the whole B..C delta: {len(added)} added, "
            f"{len(removed)} removed, {len(changed)} shared rows changed"
            if (added or removed or changed)
            else "f46bdfd produces NO D-2 delta on this bundle -- so it cannot "
            "be the contributor pjm-150 measured, and the delta belongs to the "
            "unmeasurable pre-f46bdfd half of that window"
        ),
    }
    (REPO / args.out).write_text(json.dumps(rec, indent=2))
    print(f"wrote {args.out}")
    print(
        f"D-2 rows  B(pre-fix)={len(rb)}  C(HEAD)={len(rc)}  "
        f"added={len(added)} removed={len(removed)} shared_changed={len(changed)}"
    )


if __name__ == "__main__":
    main()
