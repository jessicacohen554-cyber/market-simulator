"""Regression tripwires for the persisted-artifact surfaces every later
refactor depends on.

Three independent guards:

* **Pickle-borne class identity.** The committed ``p2_state`` pickles bind a
  fixed set of classes to their exact module paths. Unpickling resolves a class
  by its ``__module__``/qualname, so if a split moves any of these classes to a
  different module (or a facade re-exports it without defining it physically at
  the frozen path, changing ``__module__``), every committed pickle silently
  fails to load. This test asserts each class both *resolves* at its frozen path
  and reports that path as its ``__module__``.
* **``ScenarioConfig`` cache-key stability.** ``cache_key()`` hashes
  ``asdict(self)``; any change to field names/defaults that reaches the hash
  orphans every on-disk cache and breaks keeper reproducibility. Pinned to a
  literal so a drift is caught here, not in a stale-cache mystery months later.
* **No module-level import cycles.** The package breaks would-be cycles with
  lazy (in-function) imports; a cycle introduced at module scope is an import-
  time crash waiting for the wrong import order. An AST walk asserts the
  module-level import graph of ``src/market_sim`` is acyclic.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

from market_sim.config.scenarios import ScenarioConfig

# The classes bound by the committed p2_state pickles to their exact module
# paths (refactor-consolidation plan §1 "Pickle identity is frozen"). Kept in
# lockstep with docs/refactor-consolidation-plan-2026-07.md.
FROZEN_PICKLE_PATHS: dict[str, list[str]] = {
    "market_sim.data.fleet": ["Generator", "FleetArrays"],
    "market_sim.model.dispatch": ["DispatchResult"],
    "market_sim.config.scenarios": ["ScenarioConfig"],
    "market_sim.model.storage": ["StorageUnit"],
    "market_sim.results.outputs": ["FleetContext"],
    "market_sim.config.iso_configs": ["TransferLink"],
}

# ScenarioConfig().cache_key() with the current frozen field set/defaults.
# Recompute intentionally (never to "fix" a failure): a change here means a
# field that reaches asdict() moved, which orphans every on-disk cache.
#
# 2026-07-20 advance 2a1cb71048210ebf -> edbc1b103207170a. Investigated (field-set
# diff of ScenarioConfig between baseline 0ba2bb0 and HEAD) and every difference is
# traceable to four merged, attributed FF/calibration commits — no removed/renamed
# field, and the ONLY pre-existing-field default change is the intended, owner-
# signed-off FF-2C flip:
#   - 9752a64 (ERCOT-91): +gas_st_drag_seasonal (=False), +gas_st_drag_seasonal_path
#     (=None) — new default-off fields.
#   - 0cc47af (caiso-104): +caiso_charge_allocation_schedule (=False) — new
#     default-off field.
#   - 85c261f (ERCOT-89): +ercot_shoulder_online_span (=False),
#     +ercot_shoulder_online_span_path (=None) — new default-off fields.
#   - dbbae9c (FF-2C): capacity_market_clearing_by_iso default FLIPPED None ->
#     {"PJM","MISO","CAISO","NEISO": True} (NOT a new field — a pre-existing
#     field's default changed). It is not in _CACHE_KEY_OPTIONAL_FIELDS and the
#     default config is mode="forecast" (no __post_init__ backcast coercion), so
#     the dict enters the hash and is the dominant contributor to this change.
PINNED_DEFAULT_CACHE_KEY = "edbc1b103207170a"


@pytest.mark.parametrize(
    ("module_path", "class_name"),
    [(mod, cls) for mod, classes in FROZEN_PICKLE_PATHS.items() for cls in classes],
)
def test_pickle_class_resolves_at_frozen_path(
    module_path: str, class_name: str
) -> None:
    """Each pickle-borne class resolves at its frozen path AND ``__module__``
    equals that path (both directions of the unpickle contract)."""
    module = importlib.import_module(module_path)
    assert hasattr(module, class_name), (
        f"{class_name} no longer resolves at {module_path} — this breaks every "
        "committed p2_state pickle"
    )
    cls = getattr(module, class_name)
    assert cls.__module__ == module_path, (
        f"{module_path}.{class_name}.__module__ is {cls.__module__!r}, not "
        f"{module_path!r}. A facade re-export is not enough: unpickling keys on "
        "__module__, so the class must be DEFINED at the frozen path."
    )


def test_default_scenario_config_cache_key_is_pinned() -> None:
    """``ScenarioConfig().cache_key()`` equals the pinned literal."""
    assert ScenarioConfig().cache_key() == PINNED_DEFAULT_CACHE_KEY, (
        "The default ScenarioConfig cache_key changed. A field that reaches "
        "asdict() moved or changed its default; this orphans every on-disk "
        "cache and breaks keeper reproducibility. Do not update the literal to "
        "silence this — find what changed."
    )


# --------------------------------------------------------------------------
# Module-level import-cycle guard
# --------------------------------------------------------------------------

_SRC = Path(__file__).resolve().parent.parent / "src"
_PKG_ROOT = _SRC / "market_sim"


def _module_name(path: Path) -> str:
    """Dotted module name for a .py file under ``src/`` (``__init__`` → package)."""
    parts = list(path.relative_to(_SRC).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _is_type_checking(node: ast.If) -> bool:
    """True when an ``if`` guards a ``TYPE_CHECKING`` block (not run at import)."""
    test = node.test
    if isinstance(test, ast.Name):
        return test.id == "TYPE_CHECKING"
    if isinstance(test, ast.Attribute):
        return test.attr == "TYPE_CHECKING"
    return False


def _module_level_imports(tree: ast.AST):
    """Yield Import/ImportFrom nodes that execute at import time.

    Descends into module-body compound statements (``if``/``try``/``with``/loops
    and class bodies — all run at import) but NOT into function bodies (lazy
    imports, the intentional cycle break) and NOT into ``TYPE_CHECKING`` guards.
    """

    def walk(node, in_func):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield from walk(child, True)
            elif isinstance(child, ast.If) and _is_type_checking(child):
                for sub in child.orelse:  # the else-branch still runs
                    yield from walk(sub, in_func)
            else:
                if not in_func and isinstance(child, (ast.Import, ast.ImportFrom)):
                    yield child
                yield from walk(child, in_func)

    yield from walk(tree, False)


def _resolve_targets(node, module_name: str, is_package: bool, known: set[str]):
    """Return the set of intra-package modules an import statement executes."""
    targets: set[str] = set()
    if isinstance(node, ast.Import):
        for alias in node.names:
            targets.add(alias.name)
    else:  # ImportFrom
        if node.level:
            # Relative import anchor: a package's own name, else its parent.
            anchor = module_name.split(".")
            if not is_package:
                anchor = anchor[:-1]
            if node.level > 1:
                anchor = anchor[: len(anchor) - (node.level - 1)]
            prefix = ".".join(anchor)
            full = f"{prefix}.{node.module}" if node.module else prefix
        else:
            full = node.module or ""
        if full:
            targets.add(full)
            for alias in node.names:
                targets.add(f"{full}.{alias.name}")
    return {t for t in targets if t in known and t != module_name}


def _import_graph() -> dict[str, set[str]]:
    files = sorted(_PKG_ROOT.rglob("*.py"))
    known = {_module_name(f) for f in files}
    graph: dict[str, set[str]] = {m: set() for m in known}
    for path in files:
        module_name = _module_name(path)
        is_package = path.name == "__init__.py"
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in _module_level_imports(tree):
            graph[module_name] |= _resolve_targets(node, module_name, is_package, known)
    return graph


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Return every non-trivial strongly-connected component (Tarjan)."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    on_stack: dict[str, bool] = {}
    stack: list[str] = []
    counter = [0]
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        index[v] = low[v] = counter[0]
        counter[0] += 1
        stack.append(v)
        on_stack[v] = True
        for w in graph[v]:
            if w not in index:
                strongconnect(w)
                low[v] = min(low[v], low[w])
            elif on_stack.get(w):
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                comp.append(w)
                if w == v:
                    break
            sccs.append(comp)

    for v in graph:
        if v not in index:
            strongconnect(v)
    cycles = [sorted(c) for c in sccs if len(c) > 1]
    cycles += [[v] for v in graph if v in graph[v]]  # self-loops
    return cycles


def test_no_module_level_import_cycles() -> None:
    """``src/market_sim`` has zero module-level (import-time) import cycles."""
    cycles = _find_cycles(_import_graph())
    assert not cycles, (
        "Module-level import cycle(s) introduced — break them with a lazy "
        "(in-function) import:\n" + "\n".join("  " + " <-> ".join(c) for c in cycles)
    )
