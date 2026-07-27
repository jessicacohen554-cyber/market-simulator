"""Regression guards for the physically-defined fleet classes.

The Wave-3H split defines :class:`Generator` and :class:`FleetArrays`
PHYSICALLY in ``src/market_sim/data/fleet/__init__.py`` so the committed
``p2_state`` pickles resolve them at the frozen module path
``market_sim.data.fleet`` (refactor-consolidation plan §1 "Pickle identity is
frozen"). Two guards:

* **Single definition.** The split initially carried each class TWICE at
  module level; last-binding-wins made the first copy dead code and an
  editing trap (an edit to the first copy silently did nothing). An AST walk
  asserts each class is defined exactly once at module level in this file, so
  the duplication cannot silently return — and, because the count must be
  exactly one (not zero), that the class stays defined physically here rather
  than re-exported from a submodule.
* **Pickle round-trip identity.** A ``Generator`` and a ``FleetArrays``
  instance survive ``pickle.dumps``/``loads`` with ``__module__`` and
  ``__qualname__`` unchanged — the two attributes the unpickle contract keys
  on.
"""

from __future__ import annotations

import ast
import pickle

import numpy as np
import pytest

from market_sim.data.fleet import FleetArrays, Generator
from tests.helpers import REPO_ROOT

_FLEET_INIT = REPO_ROOT / "src" / "market_sim" / "data" / "fleet" / "__init__.py"
_FROZEN_MODULE = "market_sim.data.fleet"


def _module_level_class_def_count(name: str) -> int:
    """Count module-level ``class <name>`` statements in ``fleet/__init__.py``."""
    tree = ast.parse(_FLEET_INIT.read_text(), filename=str(_FLEET_INIT))
    return sum(
        1 for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name
    )


@pytest.mark.parametrize("class_name", ["Generator", "FleetArrays"])
def test_class_defined_exactly_once_at_module_level(class_name: str) -> None:
    """Each pickle-borne fleet class has exactly one module-level definition.

    More than one means the duplication returned (every copy but the last is
    dead code and an editing trap); zero means the class was moved out of the
    package ``__init__``, which changes ``__module__`` and breaks every
    committed ``p2_state`` pickle.
    """
    count = _module_level_class_def_count(class_name)
    assert count == 1, (
        f"{class_name} is defined {count} times at module level in "
        f"{_FLEET_INIT}. It must be defined exactly once, physically in the "
        "package __init__ (frozen pickle path market_sim.data.fleet)."
    )


def test_generator_pickle_round_trip_identity() -> None:
    """A ``Generator`` round-trips through pickle at the frozen module path."""
    gen = Generator(
        unit_id="u1",
        name="Unit 1",
        zone="Z1",
        fuel_type="gas_cc",
        pmax_mw=100.0,
    )
    loaded = pickle.loads(pickle.dumps(gen))
    assert type(loaded) is Generator
    assert Generator.__module__ == _FROZEN_MODULE
    assert type(loaded).__module__ == _FROZEN_MODULE
    assert Generator.__qualname__ == "Generator"
    assert type(loaded).__qualname__ == "Generator"
    assert loaded == gen


def test_fleet_arrays_pickle_round_trip_identity() -> None:
    """A ``FleetArrays`` round-trips through pickle at the frozen module path."""
    n_gen, hours = 2, 4
    arrays = FleetArrays(
        pmax=np.array([100.0, 50.0]),
        pmin=np.zeros(n_gen),
        heat_rate=np.array([7.5, 10.0]),
        vom=np.zeros(n_gen),
        emission_rate=np.zeros(n_gen),
        nox_rate=np.zeros(n_gen),
        so2_rate=np.zeros(n_gen),
        zone_idx=np.zeros(n_gen, dtype=int),
        fuel_type_idx=np.zeros(n_gen, dtype=int),
        availability=np.ones((n_gen, hours)),
        unit_ids=["u1", "u2"],
        efficiency_bin=np.array(["default", "default"], dtype=object),
        plant_code=np.zeros(n_gen, dtype=int),
    )
    loaded = pickle.loads(pickle.dumps(arrays))
    assert type(loaded) is FleetArrays
    assert FleetArrays.__module__ == _FROZEN_MODULE
    assert type(loaded).__module__ == _FROZEN_MODULE
    assert FleetArrays.__qualname__ == "FleetArrays"
    assert type(loaded).__qualname__ == "FleetArrays"
    assert loaded.n_gen == n_gen
    np.testing.assert_array_equal(loaded.pmax, arrays.pmax)
    np.testing.assert_array_equal(loaded.availability, arrays.availability)
    assert loaded.unit_ids == arrays.unit_ids
