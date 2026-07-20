"""Repo-root API-key resolution for data-fetch scripts (stdlib-only).

Every ``scripts/data/fetch_*`` script needs one or more API keys (EIA, MISO,
ERCOT, data.gov). Keys are provided at runtime via the process environment or a
local, untracked ``.env`` at the repo root (see ``.env.example`` for the key
NAMES). This module is the single resolver those scripts share, replacing the
eight hand-rolled ``.env`` parsers that previously read the file inline.

Resolution order for :func:`get_api_key`:
  1. ``os.environ[name]`` if set and non-empty;
  2. a ``NAME=value`` line in the repo-root ``.env`` if that file exists;
  3. otherwise exit with a registration-URL hint when ``required`` (the
     default), or return ``None`` when ``required=False`` (the caller then
     supplies its own fallback, e.g. the EIA public ``DEMO_KEY``).

Never logs, prints, or otherwise emits a key value. Stdlib-only by design — it
is imported by fetch scripts that run standalone, before the package proper.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# scripts/lib/env_keys.py -> parents[2] is the repository root (holds ``.env``).
REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_env_file(name: str, env_path: Path) -> str | None:
    """Return the value of ``name`` from a ``KEY=value`` ``.env`` file, or None.

    Reads the first ``name=...`` line; blank values are treated as absent. The
    value is never logged.
    """
    if not env_path.is_file():
        return None
    prefix = f"{name}="
    for line in env_path.read_text().splitlines():
        if line.startswith(prefix):
            value = line.split("=", 1)[1].strip()
            return value or None
    return None


def get_api_key(name: str, *, required: bool = True, hint: str = "") -> str | None:
    """Resolve API key ``name`` from the environment, then the repo-root ``.env``.

    Checks ``os.environ`` first, then a ``NAME=value`` line in ``<repo>/.env``
    (untracked; see ``.env.example`` for the key names). When the key is absent:
    exit the process with a registration hint if ``required`` (default), or
    return ``None`` if ``required=False`` (the caller supplies its own
    fallback). ``hint`` is an optional registration URL / instruction appended
    to the exit message. The key value itself is never logged or printed.
    """
    key = os.environ.get(name, "").strip()
    if not key:
        key = _read_env_file(name, REPO_ROOT / ".env") or ""
    if key:
        return key
    if required:
        suffix = f" ({hint})" if hint else ""
        sys.exit(
            f"{name} not set -- export it or add it to the repo-root .env{suffix}."
        )
    return None
