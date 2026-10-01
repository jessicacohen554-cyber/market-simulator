"""Regression tripwires for the persisted-artifact surfaces later refactors depend on.

* **Pickle-borne class identity.** Committed ``p2_state`` pickles bind classes
  to their exact module paths; each must resolve there with that ``__module__``.
* **Backcast coercion lands on defaults.** A registered cache-key-optional field
  coerced off its default in backcast silently re-keys every backcast bundle.
* **Checkout-path invariance.** Neither the solve surface nor ``cache_key()``
  may depend on where the checkout lives.
* **No module-level import cycles** in ``src/market_sim``.
"""

from __future__ import annotations

import ast
import dataclasses
import importlib
from pathlib import Path

import pytest

from market_sim.config import scenarios as scen
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.solve_surface import SURFACE_ISOS as _SURFACE_ISOS
from tests.helpers import REPO_ROOT

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


# Registered cache-key-optional fields whose backcast coercion is KNOWINGLY off
# their default (each a deliberate backcast re-key). Only these are exempt from
# ``test_no_registered_optional_field_is_backcast_coerced_off_its_default``.
_DECLARED_BACKCAST_COERCION_REKEYS: dict[str, str] = {
    "storage_entry_availability_gate": (
        "R-A arming 2026-08-31: forecast-only storage entry screen. Coercing to "
        "the dataclass default would ARM it in a multi-year backcast through "
        "runner.run_scenario_iso, so the coercion stays and the re-key was paid "
        "at the pin above"
    ),
    "storage_entry_cost_normalized_rank": (
        "R-A arming 2026-08-31: same posture, same reason — the two are armed "
        "as one mechanism pair and coerced off together"
    ),
    "eia860_vintage_tracks_solve_year": (
        "F1 2026-09-24: backcast-default ON, coerced to its frozen False outside "
        "a backcast; the backcast re-key was paid at the pin above"
    ),
    "measured_ct_heat_rates": (
        "F1 2026-09-24: backcast-default ON, coerced to its frozen False outside "
        "a backcast; the backcast re-key was paid at the pin above"
    ),
    "measured_coal_heat_rates": (
        "F1 2026-09-24: backcast-default ON, coerced to its frozen False outside "
        "a backcast; the backcast re-key was paid at the pin above"
    ),
    "measured_st_heat_rates": (
        "F1 2026-09-24: backcast-default ON, coerced to its frozen False outside "
        "a backcast; the backcast re-key was paid at the pin above"
    ),
    "measured_cc_heat_rates": (
        "F1 2026-09-24: backcast-default ON, coerced to its frozen False outside "
        "a backcast; the backcast re-key was paid at the pin above"
    ),
    "measured_chp_heat_rates": (
        "F1 2026-09-24: backcast-default ON, coerced to its frozen False outside "
        "a backcast; the backcast re-key was paid at the pin above"
    ),
}


@pytest.fixture
def config_identity_only(monkeypatch):
    """Neutralize the solve surface, so a key comparison measures the CONFIG alone."""
    monkeypatch.setattr(scen, "moved_rows", lambda iso: {})
    monkeypatch.setattr(scen, "applicable_epochs", lambda config: [])


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


def test_no_registered_optional_field_is_backcast_coerced_off_its_default() -> None:
    """Backcast coercion must land every registered field on its default.

    The general form of the invariant above. ``_CACHE_KEY_OPTIONAL_FIELDS`` is
    cache-neutral **at the default only**, so a backcast coercion that lands on
    anything else silently re-keys every backcast bundle. Checking the property
    (rather than only the digest) names the offending field directly.

    A field may leave the property ONLY through
    :data:`_DECLARED_BACKCAST_COERCION_REKEYS`; an undeclared offender fails.
    """
    from market_sim.config import scenarios as scen

    defaults = ScenarioConfig()
    backcast = ScenarioConfig(mode="backcast")
    offenders = {
        name: (getattr(defaults, name), getattr(backcast, name))
        for name in scen._CACHE_KEY_OPTIONAL_FIELDS
        if getattr(backcast, name) != getattr(defaults, name)
        and name not in _DECLARED_BACKCAST_COERCION_REKEYS
    }
    assert not offenders, (
        "registered cache-key-optional field(s) are coerced OFF their default "
        f"in backcast, so they enter the backcast hash: {offenders}. Coerce to "
        "the dataclass default (see net_cone_forward_escalation in "
        "scenarios.py::__post_init__), or accept the re-key deliberately by "
        "adding the field to _DECLARED_BACKCAST_COERCION_REKEYS with its reason."
    )


def test_declared_backcast_rekeys_are_still_really_coerced_off() -> None:
    """Every declared exemption must still BE one — no stale allowlist entries.

    The allowlist suppresses a real invariant, so it may only ever name fields
    that genuinely are coerced off their default today. A field that later
    stops being coerced (or whose default moves back) must leave the list, or
    it would silently license a future re-key nobody paid for.
    """
    from market_sim.config import scenarios as scen

    defaults = ScenarioConfig()
    backcast = ScenarioConfig(mode="backcast")
    stale = [
        name
        for name in _DECLARED_BACKCAST_COERCION_REKEYS
        if name not in scen._CACHE_KEY_OPTIONAL_FIELDS
        or getattr(backcast, name) == getattr(defaults, name)
    ]
    assert not stale, (
        f"stale _DECLARED_BACKCAST_COERCION_REKEYS entries: {stale}. Each is "
        "either no longer cache-key-registered or no longer coerced off its "
        "default, so its exemption is dead and must be removed."
    )


def test_solve_surface_is_checkout_path_invariant(monkeypatch) -> None:
    """A relocated checkout hashes the SAME surface (capx D79).

    The surface has no paths in it by construction — it hashes registry VALUES,
    and the seven modules read no file at import. This pins that property rather
    than trusting it: a table that ever came to hold a checkout-absolute path
    would put the checkout directory into every cache key, which is exactly the
    2026-07-27 defect the block above records, one layer down.
    """
    import market_sim.config.paths as paths_mod
    from market_sim.config.solve_surface import reset_caches, surface_rows

    before = {iso: surface_rows(iso) for iso in _SURFACE_ISOS}
    elsewhere = Path("/home/runner/work/market-simulator/market-simulator")
    monkeypatch.setattr(paths_mod, "REPO_ROOT", elsewhere)
    monkeypatch.setattr(paths_mod, "DATA_ROOT", elsewhere)
    reset_caches()
    try:
        for iso, rows in before.items():
            assert surface_rows(iso) == rows, (
                f"{iso}'s solve surface is checkout-path-dependent: a registry "
                "value moved when the path roots did. Some surface table now "
                "holds an absolute path; make it relative or move it off the "
                "surface, or every cache key encodes where the checkout lives."
            )
    finally:
        reset_caches()


def test_default_cache_key_is_checkout_path_invariant(
    monkeypatch, config_identity_only
) -> None:
    """The default key is identical whatever directory the checkout lives in.

    Simulates a relocated checkout by moving the path roots AND the stored path
    values together, as a real clone elsewhere would, and compares against the
    key computed in place (both under ``config_identity_only``).
    """
    import market_sim.config.paths as paths_mod

    elsewhere = "/home/runner/work/market-simulator/market-simulator"
    here = str(paths_mod.REPO_ROOT)
    base = ScenarioConfig()
    expected = base.cache_key()

    relocated_values = {
        f.name: getattr(base, f.name).replace(here, elsewhere)
        for f in dataclasses.fields(base)
        if isinstance(getattr(base, f.name), str)
        and getattr(base, f.name).startswith(here + "/")
    }
    assert relocated_values, (
        "No absolute repo-rooted path fields found — if the defaults became "
        "relative this test is obsolete, but do not delete it silently."
    )

    monkeypatch.setattr(paths_mod, "REPO_ROOT", Path(elsewhere))
    monkeypatch.setattr(paths_mod, "DATA_ROOT", Path(elsewhere))
    relocated = base.with_overrides(**relocated_values)

    assert relocated.cache_key() == expected, (
        "cache_key() is checkout-path-dependent again: a config identical up to "
        "the checkout directory hashed differently. A new absolute-path field "
        "must be folded by scenarios.py::_normalize_cache_key_paths."
    )


def test_cache_key_still_forks_on_a_genuinely_different_file() -> None:
    """Normalization must not collapse distinct data sources onto one key."""
    base = ScenarioConfig()
    for other in (
        base.with_overrides(campd_bins_path=base.campd_bins_path + ".alt"),
        base.with_overrides(campd_bins_path="/mnt/external/bins.csv"),
    ):
        assert other.cache_key() != base.cache_key()


# --------------------------------------------------------------------------
# Module-level import-cycle guard
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------

_SRC = REPO_ROOT / "src"
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
