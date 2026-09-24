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
    "scripts/probes/",
    "results/calibration/",
    "docs/sessions/",
    "scope2-lce-portfolio/",
)
_CODE_SUFFIXES = (".py", ".sh", ".bash", ".yml", ".yaml")
# Left boundary: a match must not continue a longer path segment. Without it a
# nested ``tests/unit/scripts/<name>`` path was read as a repo-root script
# reference (the false positive recorded in
# docs/handoffs/soco-desk-ledger-2026-09.md R-k). A ``./`` or ``${ROOT}/``
# prefix still matches; a ``<word>/`` or ``<word>`` prefix does not.
_SCRIPT_REF_RE = re.compile(r"(?<![\w\-]/)(?<![\w\-])scripts/[\w/.\-]+\.py")

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
    # The CLI wrapper that produced the committed parasitic-load artifact
    # (data/raw/_processed-legacy/parasitic_load_factors.parquet) — never
    # committed (no delete in git history), the same never-synced condition as
    # build_nyiso_scr_edrp.py above. Referenced only by
    # fleet/campd_bins.py::_ramp_parasitic_factor_map's docstring, which cites
    # it ALONGSIDE the in-repo computation it wraps
    # (market_sim.data.campd.compute_parasitic_factors), so the rule-5
    # [R-NO-MAGIC] provenance chain for the net/gross factors is intact in-repo
    # without it. NOT restored deliberately: authoring a fresh deriver to
    # regenerate an already-committed artifact risks silently emitting a
    # different one, and rule 23 [R-FROZEN-DERIVE] re-derives only on a source-
    # data change.
    "scripts/data/derive_parasitic_factors.py": "never committed; rule-23 provenance citation only (compute_parasitic_factors is in-repo)",
    # Synthetic paths tests/test_file_integrity_guard.py (f05f5b0, 2026-07-26)
    # writes into its throwaway tmp-repo fixtures to exercise the rule-27
    # shrink guard. They must LOOK like guarded scripts/ files for the test to
    # mean anything, so the scanner necessarily sees them; none is a reference
    # to a script of this repo.
    "scripts/backfill.py": "file-integrity-guard test fixture path, not a reference",
    "scripts/big.py": "file-integrity-guard test fixture path, not a reference",
    "scripts/new_name.py": "file-integrity-guard test fixture path, not a reference",
    "scripts/old_name.py": "file-integrity-guard test fixture path, not a reference",
    "scripts/render.py": "file-integrity-guard test fixture path, not a reference",
    "scripts/small.py": "file-integrity-guard test fixture path, not a reference",
    # Deleted at FFR-2A (commit d12b4a8, "Fold the FF-2D crossover adapter into
    # score_crossover.py"); the fold was the point, and the two remaining
    # references are the comments RECORDING the deletion —
    # score_crossover.py:649 ("now deleted — rule 26") and
    # test_score_crossover.py:383 ("folded in from the deleted ..."). So the
    # scanner is matching a path inside the prose that documents its own
    # removal. Allowlisted rather than reworded: rule 26 [R-DELETE] wants the
    # provenance of a deleted module kept legible, and naming it is how. Found
    # 2026-08-03 by FFR-3D — it had been failing refactor-guards on main since
    # d12b4a8, reddening the gate for every PR (nobody's PR caused it).
    "scripts/_ff2d_crossover_adapter.py": "deleted at FFR-2A d12b4a8; deletion-provenance comments only",
    # Not a path at all: ``NNN`` is the run-number placeholder in
    # gen_caiso189_attestation.py's description of the per-promotion series
    # ("the bespoke gen_caisoNNN_attestation.py every CAISO promotion ships").
    # It appears both in that script's docstring and inside the governance-note
    # STRING the script writes into the caiso-189 attestation artifact, so
    # rewording would change what the recorded attestation text regenerates to;
    # allowlisted instead. Found reddening refactor-guards on main by the
    # 2026-08-14 debug sweep (ci.yml header had flagged it pre-existing).
    "scripts/gen_caisoNNN_attestation.py": "run-number placeholder in the caiso attestation-series prose, not a reference",
    # Synthetic path tests/scoring/test_bench_stamp_ast.py (Y-12, commit
    # 3d0fd19d, "hash the builder AST, not its bytes") writes into its tmp_path
    # fixture tree — `rel = "scripts/fake_builder.py"` at its `tree` fixture and
    # again in the absent-file test — to stand in for a builder source while it
    # exercises bench_stamp.builder_fingerprint(). It must LOOK like a
    # scripts/ path because BUILDER_SOURCES is monkeypatched to it, so the
    # scanner necessarily sees it; it is never a reference to a script of this
    # repo (same class as the file-integrity-guard fixture paths above). Found
    # reddening `Structural refactor guards` on main at 5cc1e7ce (Y-13).
    "scripts/fake_builder.py": "test_bench_stamp_ast.py tmp_path fixture path (Y-12, 3d0fd19d), not a reference",
}


def census_sibling_imports(verbose: bool = False) -> list[str]:
    """ADVISORY census of bare sibling-import sites in live ``scripts/`` files.

    A *bare sibling import* is ``import X`` / ``from X import …`` where ``X``
    is another script of this repo rather than an installed package — it
    resolves only through ``sys.path`` side effects (``sys.path[0]`` being the
    running script's own directory, or an inserted ``scripts/`` path), and it
    creates the second-module-copy hazard the header documents whenever the
    canonical ``scripts.*`` name is also loaded in one process. The scripts/
    README's sibling-import section carries the running count; this mode is
    that census made re-runnable, so the number can never silently drift.

    Advisory by design: the conversion of the residual web is chartered open
    work (per-file, with both-paths attribute verification and a direct-run
    ``sys.path`` bootstrap check), not a gate — this reports, never fails.
    Returns the site list as ``file:line: stmt`` strings.
    """
    import ast

    exclude = {"archive", "probes", "__pycache__"}
    scripts_dir = REPO / "scripts"
    live = [
        p
        for p in scripts_dir.rglob("*.py")
        if not (set(p.relative_to(scripts_dir).parts[:-1]) & exclude)
    ]
    # Any stem living anywhere under scripts/ (frozen record included — a live
    # file bare-importing a probe module is still a bare site).
    script_stems = {p.stem for p in scripts_dir.rglob("*.py")}
    sites: list[str] = []
    for f in sorted(live):
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            stmts: list[tuple[str, str]] = []
            if isinstance(node, ast.Import):
                stmts = [(a.name.split(".")[0], f"import {a.name}") for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                stmts = [(node.module.split(".")[0], f"from {node.module} import …")]
            for top, stmt in stmts:
                if top in ("scripts", "market_sim", "tests"):
                    continue
                if top in script_stems:
                    rel = f.relative_to(REPO)
                    sites.append(f"{rel}:{node.lineno}: {stmt}")
    n_files = len({s.split(":", 1)[0] for s in sites})
    print(f"sibling-census: {len(sites)} bare site(s) across {n_files} live file(s)")
    if verbose:
        for s in sites:
            print(f"  {s}")
    return sites


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
    ap.add_argument(
        "--sibling-census",
        action="store_true",
        help="ADVISORY: list bare sibling-import sites in live scripts/ (never fails)",
    )
    args = ap.parse_args(argv)
    if args.sibling_census:
        census_sibling_imports(verbose=True)
        return 0
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
