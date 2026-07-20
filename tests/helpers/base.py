"""unittest base classes and the shared raw-data skip helper.

* :class:`CleanDirTestCase` — replaces the hand-rolled "save ``paths.CLEAN_DIR``,
  point it at a tempdir, restore it in ``tearDown``" dance repeated across ~60
  curation tests with a one-line base-class swap.
* :class:`RawFixtureTestCase` — same tmp-dir lifecycle plus a ``raw_dir`` for
  tests that build synthetic raw inputs (pairs with :mod:`tests.helpers.raw_fixtures`).
* :func:`requires_raw` — the single decorator that supersedes the ~23 ad-hoc
  ``@pytest.mark.skipif(not _raw_present(), ...)`` gates: it marks the test
  ``fulldata`` (so the fast lane deselects it) AND skips it when the required
  raw path is genuinely absent.

``paths.CLEAN_DIR`` is mutated in place because ``scripts.lib.clean_io`` reaches
it as ``paths.CLEAN_DIR`` / ``paths.clean_path(...)`` at call time (the module
attribute), which is exactly what the original per-test dance relied on.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from market_sim.config import paths


class CleanDirTestCase(unittest.TestCase):
    """Mixin: redirect ``paths.CLEAN_DIR`` to a per-test tempdir and restore it.

    Subclasses that need their own ``setUp`` (to write raw fixtures, say) must
    call ``super().setUp()`` first — ``self.tmp_path`` and ``self.clean_dir``
    are available afterward. ``tearDown`` restores the original ``CLEAN_DIR``
    and removes the tempdir even if the test raised.
    """

    def setUp(self) -> None:
        super().setUp()
        self._clean_tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._clean_tmp.name)
        self.clean_dir = self.tmp_path / "clean"
        self._orig_clean_dir = paths.CLEAN_DIR
        paths.CLEAN_DIR = self.clean_dir

    def tearDown(self) -> None:
        paths.CLEAN_DIR = self._orig_clean_dir
        self._clean_tmp.cleanup()
        super().tearDown()


class RawFixtureTestCase(CleanDirTestCase):
    """``CleanDirTestCase`` plus a ``raw_dir`` for synthetic raw inputs.

    Tests that curate a tiny hand-built raw fixture into clean Parquet get both
    a redirected ``CLEAN_DIR`` and a scratch ``raw_dir`` under the same tempdir,
    so nothing touches the real ``data/raw`` or ``data/clean`` trees.
    """

    def setUp(self) -> None:
        super().setUp()
        self.raw_dir = self.tmp_path / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)


def requires_raw(*paths_required: str | Path, reason: str = "raw data input absent"):
    """Decorator: mark ``fulldata`` and skip when a required raw path is absent.

    Supersedes the per-file ``@pytest.mark.skipif(not _raw_present(), ...)``
    idiom. Pass the concrete filesystem path(s) the test reads (usually under
    ``data/raw``); the test is skipped if any is missing and is always tagged
    ``fulldata`` so ``-m "not fulldata"`` (the fast lane) deselects it whether
    or not the data happens to be on this host.

    Usage::

        from market_sim.config import paths
        RAW = paths.DATA_ROOT / "data" / "raw" / "eia-860"

        @requires_raw(RAW)
        def test_reads_eia860(): ...
    """
    missing = [str(p) for p in paths_required if not Path(p).exists()]
    skip = pytest.mark.skipif(bool(missing), reason=f"{reason}: missing {missing}")

    def deco(obj):
        return pytest.mark.fulldata(skip(obj))

    return deco
