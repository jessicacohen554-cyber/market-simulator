"""Fast structural guards for the refactor-consolidation lane (CI job `refactor-guards`).

Two checks, both seconds-fast and dependency-light, that catch the failure modes
a large code-motion refactor introduces without running a single LP solve:

* ``--import-walk`` — ``pkgutil.walk_packages`` over ``market_sim`` and import
  every module. A god-file split that leaves a package ``__init__`` re-export
  broken, or a moved module with a dangling intra-package import, fails here
  immediately (the lazy-import cycles the codebase relies on are deferred, so a
  clean top-level import of every module is the contract this asserts).

* ``--script-refs`` — regex-scan tracked EXECUTABLE / CONFIG files for
  ``scripts/<path>.py`` references and assert each path exists, so a script
  move/rename that leaves a live invocation dangling fails the gate. Scope note:
  this scans code + config (``.py``/``.sh``/``.yml``/``.yaml``/``Makefile``),
  NOT prose docs or ``data/raw`` READMEs — those carry pre-PR#2486 flat paths and
  forward-references to not-yet-built modules by design (doc-drift owned by the
  refactor plan's Workstream E/G, not a code-correctness signal). The residual
  ``KNOWN_DANGLING`` allowlist below is the exhaustive set the code scan still
  finds; a NEW dangling reference (not in the allowlist) fails the gate.

Run with no flags to execute both. Exit 1 on any failure.
"""

from __future__ import annotations

import argparse
import importlib
import pkgutil
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# Directories whose script references are out of scope for the code scan:
# the frozen calibration record (archive/probes), bundle artifacts (results),
# historical session logs, and scope2-lce-portfolio (a separate sub-project
# with its OWN scripts/ namespace — its `scripts/...` paths resolve there, not
# at this repo root, so scanning it yields only false positives).
_EXCL_DIRS = (
    "scripts/archive/",
    "scripts/probes/",
    "results/calibration/",
    "docs/sessions/",
    "scope2-lce-portfolio/",
)
_CODE_SUFFIXES = (".py", ".sh", ".bash", ".yml", ".yaml")
_SCRIPT_REF_RE = re.compile(r"scripts/[\w/.\-]+\.py")

# The current residual — every dangling `scripts/*.py` reference the CODE scan
# finds on the tree (2026-07-20). Each is a benign, tracked non-defect; a
# reference to a path NOT in this set fails the gate. Keep this list exhaustive
# and prune an entry the moment its target script lands.
KNOWN_DANGLING: dict[str, str] = {
    # Deleted 2026-07-17 (facility-summed CAMPD outage detector; superseded by
    # the per-unit scripts/data/derive_campd_unit_outages.py + the shared
    # scripts/lib/outage_detect.py). Remaining references are rule-23 provenance
    # citations in comments/schema that intentionally name the deleted origin.
    "scripts/derive_campd_outages.py": "deleted 2026-07-17; rule-23 provenance citations only",
    # The NYISO SCR/EDRP data-build script for the nyiso-65 keeper lane — never
    # committed (the same un-synced condition as the nyiso-65 bundle/payload;
    # see scripts/lib/known_unsynced_keepers.py). Referenced in
    # nyiso_demand_response.py's docstring + a build-hint error string. Tracked
    # with the nyiso-65 re-sync follow-up.
    "scripts/data/build_nyiso_scr_edrp.py": "un-synced nyiso-65 SCR/EDRP lane; re-sync owed",
}


def check_import_walk() -> list[str]:
    """Import every module under ``market_sim``; return a list of failures."""
    import market_sim  # noqa: F401  (import here so a total failure is a clear error)

    failures: list[str] = []
    pkg = importlib.import_module("market_sim")
    for mod in pkgutil.walk_packages(pkg.__path__, prefix="market_sim."):
        try:
            importlib.import_module(mod.name)
        except Exception as exc:  # noqa: BLE001 — any import error is a guard failure
            failures.append(f"{mod.name}: {type(exc).__name__}: {exc}")
    return failures


def check_script_refs() -> list[str]:
    """Assert every code/config ``scripts/*.py`` reference resolves; return failures."""
    tracked = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=REPO, check=True
    ).stdout.split()
    failures: list[str] = []
    for rel in tracked:
        if any(rel.startswith(p) for p in _EXCL_DIRS):
            continue
        path = REPO / rel
        if not (path.suffix in _CODE_SUFFIXES or path.name == "Makefile"):
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for match in set(_SCRIPT_REF_RE.findall(text)):
            ref = match.rstrip(".")
            if (REPO / ref).exists() or ref in KNOWN_DANGLING:
                continue
            failures.append(f"{rel}: references missing script {ref!r}")
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--import-walk", action="store_true", help="only the import walk")
    ap.add_argument(
        "--script-refs", action="store_true", help="only the script-ref lint"
    )
    args = ap.parse_args(argv)
    run_all = not (args.import_walk or args.script_refs)

    failures: list[str] = []
    if run_all or args.import_walk:
        walk = check_import_walk()
        print(f"import-walk: {'OK' if not walk else f'{len(walk)} FAILURE(S)'}")
        failures += walk
    if run_all or args.script_refs:
        refs = check_script_refs()
        print(
            f"script-refs: {'OK' if not refs else f'{len(refs)} FAILURE(S)'} "
            f"({len(KNOWN_DANGLING)} known-dangling tolerated)"
        )
        failures += refs

    if failures:
        print("\nrefactor-guards FAILED:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("refactor-guards passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
