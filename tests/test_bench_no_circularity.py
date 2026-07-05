"""D-13 static half: AST-walk asserting the bench/benchmark-builder path never
reads dispatch (LP-solved) output to construct an "actual"/benchmark value —
the L11 BTM-benchmark-circularity pattern (docs/model-legitimacy-audit-
2026-07.md §4 L11: the CHP "actual" was computed from the model's OWN
dispatch, so every pre-fix keeper's CHP C1 pass was untrustworthy; fixed
2026-07-02 in ``scripts/run_calibration_full.py::_btm_frame``).

Two checks:

1. **Registered bench-builder functions never reference dispatch.** A small
   registry (mirroring the D-2 mechanism-registry pattern already used in
   ``scripts/legitimacy_diagnostics.py``) names the functions whose job is to
   compute a BENCHMARK ("actual") quantity purely from measured inputs
   (EIA-923/930, CAMPD) — today just ``_btm_frame``, the L11 fix site. Their
   AST is walked for any name/attribute/string-constant token that names a
   dispatch-output path or variable (``dispatch``, ``_P1.parquet``,
   ``_P2.parquet``, ``system.parquet``, ``storage.parquet``). A future edit
   that re-wires ``_btm_frame`` to read the model's own dispatch to size a
   benchmark trips this immediately — the L11 regression made structurally
   impossible rather than caught by a residual anomaly months later.

   Extend the ``BENCH_BUILDER_FUNCTIONS`` registry below whenever a new
   from-measured-inputs benchmark builder is added (the same "add to the
   registry, don't hand-wire a one-off check" discipline the D-2 mechanism
   registry already uses).

2. **Dashboard-data-writing scripts never import the LP solver.** The scripts
   whose entire job is to render/assemble the COMMITTED bench/manifest
   payloads (``render_backcast.py``, ``build_manifest.py``) have no business
   importing the dispatch/model-solve machinery directly — they only ever
   read already-solved parquet. This guards against a future regression where
   a bench script "computes" an actual by re-solving instead of reading a
   measured input.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# (module path relative to REPO, function name) -> the function whose AST must
# never reference a dispatch-output path/name. Add an entry here whenever a
# new pure-measured-input benchmark builder is introduced.
BENCH_BUILDER_FUNCTIONS: tuple[tuple[str, str], ...] = (
    ("scripts/run_calibration_full.py", "_btm_frame"),
)

# Tokens (identifier fragments / string-literal substrings) that indicate a
# dispatch (LP-solved) output rather than a measured benchmark input. Matched
# case-insensitively against ast.Name/ast.arg ids, ast.Attribute attrs, and
# ast.Constant string values.
FORBIDDEN_TOKENS: tuple[str, ...] = (
    "dispatch",
    "_p1.parquet",
    "_p2.parquet",
    "system.parquet",
    "storage.parquet",
)

# Scripts whose entire job is to write the committed dashboard bench/manifest
# data files — they must never import the LP dispatch/solve machinery
# directly (they only read already-solved parquet via bundle_input_path /
# render_calibration_html.build_payload).
DASHBOARD_WRITER_SCRIPTS: tuple[str, ...] = (
    "scripts/render_backcast.py",
    "scripts/build_manifest.py",
)

# Modules a dashboard-writer script must never import (the LP solve/dispatch
# core — CLAUDE.md's model/dispatch.py, model/commitment.py).
FORBIDDEN_SOLVE_IMPORTS: tuple[str, ...] = (
    "market_sim.model.dispatch",
    "market_sim.model.commitment",
)


def _find_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        ):
            return node
    raise AssertionError(f"function {name!r} not found")


def _docstring_node(func: ast.FunctionDef) -> ast.AST | None:
    """The function's own docstring Constant node, if any (excluded from the
    scan — it's prose, not code, and legitimately discusses "dispatch" as a
    concept, e.g. ``_btm_frame``'s own "the model's dispatch never enters")."""
    if (
        func.body
        and isinstance(func.body[0], ast.Expr)
        and isinstance(func.body[0].value, ast.Constant)
        and isinstance(func.body[0].value.value, str)
    ):
        return func.body[0].value
    return None


def _tokens_in(func: ast.FunctionDef) -> set[str]:
    """Every lowercased identifier / attribute / (non-docstring) string
    constant referenced in ``func``'s CODE — excludes the docstring so prose
    mentioning "dispatch" as a concept doesn't false-positive; a genuine
    regression (a new local var/param named after dispatch, or a hardcoded
    dispatch-parquet path) still shows up as a Name/arg/Attribute id or a
    non-docstring string literal.
    """
    skip_id = id(_docstring_node(func))
    found: set[str] = set()
    for n in ast.walk(func):
        if isinstance(n, ast.Name):
            found.add(n.id.lower())
        elif isinstance(n, ast.arg):
            found.add(n.arg.lower())
        elif isinstance(n, ast.Attribute):
            found.add(n.attr.lower())
        elif (
            isinstance(n, ast.Constant)
            and isinstance(n.value, str)
            and id(n) != skip_id
        ):
            found.add(n.value.lower())
    return found


def test_bench_builder_functions_registry_is_nonempty():
    """The registry itself must name at least the L11 fix site — an empty
    registry would make check 1 vacuously pass."""
    assert BENCH_BUILDER_FUNCTIONS


def test_registered_bench_builders_never_reference_dispatch_outputs():
    for rel_path, func_name in BENCH_BUILDER_FUNCTIONS:
        path = REPO / rel_path
        assert path.exists(), f"{rel_path} does not exist"
        tree = ast.parse(path.read_text(), filename=str(path))
        func = _find_function(tree, func_name)
        tokens = _tokens_in(func)
        hits = {
            forbidden
            for forbidden in FORBIDDEN_TOKENS
            if any(forbidden in t for t in tokens)
        }
        assert not hits, (
            f"{rel_path}::{func_name} references dispatch-output token(s) "
            f"{hits} — the L11 BTM-circularity pattern (a benchmark 'actual' "
            f"computed from the model's own dispatch). This function must "
            f"stay a pure function of measured inputs (EIA-923/930, CAMPD)."
        )


def test_dashboard_writer_scripts_never_import_the_lp_solver():
    for rel_path in DASHBOARD_WRITER_SCRIPTS:
        path = REPO / rel_path
        assert path.exists(), f"{rel_path} does not exist"
        tree = ast.parse(path.read_text(), filename=str(path))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
                imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        hits = {
            forbidden
            for forbidden in FORBIDDEN_SOLVE_IMPORTS
            if any(
                mod == forbidden or mod.startswith(forbidden + ".") for mod in imported
            )
        }
        assert not hits, (
            f"{rel_path} imports the LP solve/dispatch module(s) {hits} — a "
            f"dashboard-data writer must only read already-solved parquet, "
            f"never re-solve to construct a benchmark value."
        )


def test_forbidden_token_matcher_catches_a_synthetic_regression():
    """Sanity-check the matcher itself: a function that DOES reference a
    dispatch path must trip the same check the registered functions pass."""
    src = (
        "def _fake_btm_frame(bundle_dir):\n"
        "    disp = (bundle_dir / 'dispatch' / '2024_P1.parquet').read()\n"
        "    return disp\n"
    )
    tree = ast.parse(src)
    func = _find_function(tree, "_fake_btm_frame")
    tokens = _tokens_in(func)
    hits = {f for f in FORBIDDEN_TOKENS if any(f in t for t in tokens)}
    assert hits, "matcher failed to catch a synthetic dispatch-path reference"
