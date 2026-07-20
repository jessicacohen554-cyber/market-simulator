"""pytest fixtures shared across the test suite.

The repo-root ``conftest.py`` (one level up) only fixes ``sys.path``; this one
provides the reusable fixtures. Both the fixtures here and the unittest mixins
in :mod:`tests.helpers.base` redirect ``paths.CLEAN_DIR`` the same way — use the
fixture in pytest-style tests, the mixin in ``unittest.TestCase`` classes.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market_sim.config import paths
from tests.helpers import REPO_ROOT

# Full-8760 LP-solving test classes that are genuinely slow (measured: the
# TestEndToEnd runner cases ~1-13 s each, the TestPerformance 8760 solve ~27 s)
# but live in a 900+-line module. Marking them here (rather than editing that
# large file) keeps the slow gate close to the lane config and avoids a
# rule-27 full-file rewrite. Matched by nodeid substring at collection time.
_SLOW_NODEID_SUBSTRINGS = (
    "test_soundness.py::TestEndToEnd",
    "test_soundness.py::TestPerformance",
)


def pytest_collection_modifyitems(config, items):
    """Tag the measured-slow full-8760 LP test classes with ``slow``."""
    slow = pytest.mark.slow
    for item in items:
        if any(sub in item.nodeid for sub in _SLOW_NODEID_SUBSTRINGS):
            item.add_marker(slow)


@pytest.fixture
def repo_root() -> Path:
    """The repository root (directory holding ``pyproject.toml``)."""
    return REPO_ROOT


@pytest.fixture
def tmp_clean_dir(tmp_path, monkeypatch) -> Path:
    """Redirect ``paths.CLEAN_DIR`` to a tempdir for one test.

    The pytest-native counterpart to :class:`tests.helpers.base.CleanDirTestCase`:
    ``monkeypatch`` restores the original attribute automatically at teardown,
    so a curation test can ``write_clean``/``read_clean`` against a scratch tree
    without touching the real ``data/clean``. Yields the redirected directory.
    """
    clean = tmp_path / "clean"
    monkeypatch.setattr(paths, "CLEAN_DIR", clean)
    return clean
