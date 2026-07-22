"""Facade re-export tests for the ``dispatch`` → ``model/lp`` split.

The 4,974-line ``model/dispatch.py`` was split into the ``model/lp/``
package (layout / costs / rows / reserve_rows / bounds / model) on
2026-07-22 (refactor-consolidation plan §5 item 7), leaving a
``sys.modules``-alias facade at the historical path (the
``model/capacity.py`` / ``model/transmission.py`` pattern).

Pinned contracts:

* **Alias identity** — ``market_sim.model.dispatch`` and the
  ``market_sim.model.lp`` package are ONE namespace object, so every
  historical import spelling and monkeypatch / attribute write keeps
  working.
* **Historical surface** — the frozen inventory below lists every top-level
  name the pre-split module defined plus every name any src/scripts/tests
  importer pulls from ``market_sim.model.dispatch`` (AST census 2026-07-22:
  19 distinct imported names across 73 files). Extend, never prune.
* **Home identity** — each moved name resolves via the facade to the very
  object defined in its new home submodule.
* **Pickle identity** — ``DispatchResult``, ``CrossYearBasis`` and
  ``solve_dispatch`` are defined PHYSICALLY in ``lp/__init__`` with
  ``__module__`` pinned to ``market_sim.model.dispatch`` (plan §1: the
  committed ``p2_state`` pickles and the cross-year basis cache resolve
  them by that path; a plain re-export is not sufficient).
* **Patch transparency** — ``mock.patch("market_sim.model.dispatch.X")``
  intercepts a call-time ``from market_sim.model.dispatch import X`` (the
  ``pipeline/solve.py`` / ``pipeline/commitment.py`` pattern).
"""

from __future__ import annotations

import importlib
from unittest import mock

# Every top-level name the pre-split dispatch.py defined (module logger
# included — it was part of the historical namespace), superset of the
# 2026-07-22 importer census. This is the facade's minimum contractual
# surface.
HISTORICAL_SURFACE = (
    "CrossYearBasis",
    "DispatchModel",
    "DispatchResult",
    "VariableLayout",
    "_BASIS_BASIC",
    "_BASIS_LOWER",
    "_build_gen_group_cap_rows",
    "_build_hydro_rows",
    "_build_import_node_rows",
    "_build_interface_rows",
    "_build_local_capacity_rows",
    "_build_mass_cap_rows",
    "_build_oil_budget_rows",
    "_build_posture_energy_rows",
    "_build_ramp_rows",
    "_build_reserve_rows",
    "_build_reserve_rows_pergen",
    "_build_rps_row",
    "_build_storage_alloc_rows",
    "_build_storage_daily_cycle_rows",
    "_build_zone_gen_map",
    "_build_zone_storage_map",
    "_cross_year_column_map",
    "_vstack_csr_free",
    "build_constraints",
    "build_cost_vector",
    "build_variable_bounds",
    "logger",
    "solve_dispatch",
    "storage_reserve_mw",
)

# Every top-level name each new submodule defines (module loggers excluded);
# the facade must resolve each to the submodule's own object.
MOVED_SURFACE: dict[str, tuple[str, ...]] = {
    "market_sim.model.lp.layout": (
        "VariableLayout",
        "_build_zone_gen_map",
        "_build_zone_storage_map",
        "_vstack_csr_free",
    ),
    "market_sim.model.lp.costs": ("build_cost_vector",),
    "market_sim.model.lp.rows": (
        "_build_gen_group_cap_rows",
        "_build_hydro_rows",
        "_build_import_node_rows",
        "_build_interface_rows",
        "_build_local_capacity_rows",
        "_build_mass_cap_rows",
        "_build_oil_budget_rows",
        "_build_posture_energy_rows",
        "_build_ramp_rows",
        "_build_rps_row",
        "_build_storage_alloc_rows",
        "_build_storage_daily_cycle_rows",
        "build_constraints",
    ),
    "market_sim.model.lp.reserve_rows": (
        "_build_reserve_rows",
        "_build_reserve_rows_pergen",
        "storage_reserve_mw",
    ),
    "market_sim.model.lp.bounds": ("build_variable_bounds",),
    "market_sim.model.lp.model": (
        "_BASIS_BASIC",
        "_BASIS_LOWER",
        "DispatchModel",
        "_cross_year_column_map",
    ),
}

# The three names defined PHYSICALLY in lp/__init__ with __module__ pinned to
# the frozen pickle path (plan §1). tests/test_persisted_identity.py owns the
# DispatchResult assertion; this pins all three against regression.
PHYSICAL_INIT_NAMES = ("CrossYearBasis", "DispatchResult", "solve_dispatch")
FROZEN_MODULE_PATH = "market_sim.model.dispatch"

# Names dispatch.py historically re-exported from its own module-level
# imports (facade passthroughs) → their canonical defining homes.
PASSTHROUGHS: dict[str, tuple[str, ...]] = {
    "market_sim.config.constants": (
        "HOURS_PER_YEAR",
        "STORAGE_TIEBREAKER_EPSILON",
    ),
    "market_sim.data.fleet": (
        "FUEL_TYPE_MAP",
        "FleetArrays",
        "_hour_to_month_index",
        "assemble_mc",
    ),
}


def _facade():
    return importlib.import_module("market_sim.model.dispatch")


def _package():
    return importlib.import_module("market_sim.model.lp")


class TestAliasIdentity:
    def test_facade_is_the_lp_package(self):
        assert _facade() is _package(), (
            "market_sim.model.dispatch must alias the model/lp package "
            "(sys.modules self-replacement), not re-export a copy"
        )

    def test_historical_surface_resolves(self):
        facade = _facade()
        missing = [n for n in HISTORICAL_SURFACE if not hasattr(facade, n)]
        assert not missing, (
            "facade lost historically-imported names (breaking src/scripts/"
            f"tests importers): {missing}"
        )


class TestMovedSurface:
    def test_every_moved_name_is_the_home_object(self):
        facade = _facade()
        bad = []
        for home_path, names in MOVED_SURFACE.items():
            home = importlib.import_module(home_path)
            for n in names:
                if not hasattr(facade, n):
                    bad.append(f"{n} missing from facade")
                elif getattr(facade, n) is not getattr(home, n):
                    bad.append(f"{n} is not {home_path}.{n}")
        assert not bad, "\n".join(bad)

    def test_passthroughs_are_the_canonical_objects(self):
        facade = _facade()
        bad = []
        for home_path, names in PASSTHROUGHS.items():
            home = importlib.import_module(home_path)
            for n in names:
                if not hasattr(facade, n):
                    bad.append(f"{n} missing from facade")
                elif getattr(facade, n) is not getattr(home, n):
                    bad.append(f"{n} is not {home_path}.{n}")
        assert not bad, "\n".join(bad)


class TestPickleIdentity:
    def test_physical_init_names_pin_the_frozen_module_path(self):
        """The p2_state pickles (and the cross-year basis cache) resolve these
        by ``__module__`` — the classes/function must be defined physically in
        lp/__init__ with the pin, never plain-re-exported from a submodule."""
        pkg = _package()
        bad = []
        for n in PHYSICAL_INIT_NAMES:
            obj = getattr(pkg, n)
            if obj.__module__ != FROZEN_MODULE_PATH:
                bad.append(f"{n}.__module__ == {obj.__module__!r}")
        assert not bad, (
            f"pickle-identity pins broken (expected {FROZEN_MODULE_PATH!r}): "
            + "; ".join(bad)
        )

    def test_unpickle_path_resolves_through_the_facade(self):
        """Both directions of the unpickle contract: import the frozen path,
        getattr the class — and the class round-trips to the same object."""
        mod = importlib.import_module(FROZEN_MODULE_PATH)
        for n in ("DispatchResult", "CrossYearBasis"):
            cls = getattr(mod, n)
            again = getattr(importlib.import_module(cls.__module__), cls.__qualname__)
            assert again is cls, f"{n} does not round-trip via __module__"


class TestPatchTransparency:
    def test_string_patch_intercepts_call_time_import(self):
        """A mock.patch through the historical dotted path must intercept
        production code that resolves the name at call time via the same path
        (``pipeline/solve.py``'s function-local
        ``from market_sim.model.dispatch import solve_dispatch``)."""
        with mock.patch("market_sim.model.dispatch.solve_dispatch") as spy:
            from market_sim.model.dispatch import solve_dispatch

            assert solve_dispatch is spy
        # ... and the patch unwinds: the real function is restored, still
        # carrying the frozen-module pin.
        restored = _facade().solve_dispatch
        assert restored is _package().solve_dispatch
        assert restored.__module__ == FROZEN_MODULE_PATH
