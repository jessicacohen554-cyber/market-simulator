"""The ``data/clean`` read seam: one env gate, one lazy ``clean_io`` importer.

Nearly every ``data/`` loader carries the same two shims: a ``_use_clean()``
that reads the ``MARKET_SIM_USE_CLEAN`` flag, and a lazy import of the frozen
``scripts.lib.clean_io`` seam (the repo-root package that reads curated
Parquet). The audit found ~10 byte-identical copies. This module is the single
definition both collapse onto.

**Default is OFF.** :func:`use_clean` returns ``True`` only when
``MARKET_SIM_USE_CLEAN`` is one of ``1/true/yes/on`` (case-insensitive). Unset
or anything else keeps every loader on its raw-data path, unchanged. This module
does not flip any clean path on — it only centralises the gate the callers
already had.

``scripts.lib.clean_io`` lives at the repo root, outside the installed
``market_sim`` package, so :func:`get_clean_io` imports it lazily and adds the
repo root to ``sys.path`` if it is not already importable — the raw path never
pays that cost.
"""

from __future__ import annotations

import os

__all__ = ["use_clean", "get_clean_io", "USE_CLEAN_ENV"]

# The environment variable gating the clean-backed read path (default OFF).
USE_CLEAN_ENV: str = "MARKET_SIM_USE_CLEAN"
_TRUTHY: frozenset[str] = frozenset({"1", "true", "yes", "on"})


def use_clean() -> bool:
    """Whether the opt-in ``data/clean`` read path is enabled (default ``False``).

    Gated by ``MARKET_SIM_USE_CLEAN``; any of ``1/true/yes/on`` (case-
    insensitive) turns it on, everything else (including unset) keeps the raw
    read path.
    """
    return os.environ.get(USE_CLEAN_ENV, "").strip().lower() in _TRUTHY


def get_clean_io():
    """Lazily import and return the frozen ``scripts.lib.clean_io`` seam module.

    The seam lives at the repo root, outside the installed ``market_sim``
    package, so the repo root is added to ``sys.path`` if it is not already
    importable. We only ever read through this module (never edit it).
    """
    try:
        from scripts.lib import clean_io
    except ModuleNotFoundError:
        import sys

        from market_sim.config.paths import REPO_ROOT

        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))
        from scripts.lib import clean_io
    return clean_io
