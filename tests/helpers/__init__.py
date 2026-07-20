"""Shared test-layer helpers (Workstream F, refactor-consolidation plan §6).

A single home for the fixture/builder/solve/CLEAN_DIR patterns that were
copy-pasted across the suite: ``make_gen``/``make_fleet``/``base_scenario``
builders, the ``solve_tiny`` 1-gen/1-zone/24h wrapper, the ``CleanDirTestCase``
mixin that replaces the hand-rolled CLEAN_DIR redirect dance, the raw-fixture
writers, and the clean-output assertions.

Import from the sub-modules directly (``from tests.helpers.builders import
make_fleet``) or from this package root for the most common handful.

``REPO_ROOT`` is the repository root (the directory holding ``pyproject.toml``),
exported here so tests locate committed fixtures without their own
``Path(__file__).parents[...]`` depth-counting.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]

from tests.helpers.base import (  # noqa: E402  (REPO_ROOT must precede these)
    CleanDirTestCase,
    RawFixtureTestCase,
    requires_raw,
)
from tests.helpers.builders import (  # noqa: E402
    backcast_scenario,
    base_scenario,
    make_fleet,
    make_gen,
)
from tests.helpers.clean_asserts import (  # noqa: E402
    assert_clean_valid,
    read_clean_or_fail,
)
from tests.helpers.solve import solve_tiny  # noqa: E402

__all__ = [
    "REPO_ROOT",
    "CleanDirTestCase",
    "RawFixtureTestCase",
    "requires_raw",
    "make_gen",
    "make_fleet",
    "base_scenario",
    "backcast_scenario",
    "solve_tiny",
    "assert_clean_valid",
    "read_clean_or_fail",
]
