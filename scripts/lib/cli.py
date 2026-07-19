"""Shared CLI building blocks for ``scripts/`` entry points.

Two things live here so the standing tooling spells its command line the same
way everywhere instead of hand-copying argparse boilerplate:

* the repo-root **bootstrap** every ``scripts.*``-importing tool needs, and
* canonical ``add_*_arg`` helpers for the four arguments that recur across the
  calibration / governance / dashboard scripts (``--iso``, ``--year``,
  ``--out-dir``, ``--bundle``).

Bootstrap
---------
``market_sim`` is always importable (editable install), but the ``scripts``
package is only importable with the repo root on ``sys.path``. The canonical
three-line header a script writes at the top — before any ``from scripts.…``
import — is::

    import sys
    from market_sim.config.paths import REPO_ROOT
    sys.path.insert(0, str(REPO_ROOT))

after which ``from scripts.lib.cli import add_iso_arg`` (etc.) resolves
regardless of the script's depth or the process's working directory.
:func:`repo_root` re-exports the same ``REPO_ROOT`` for tools that want the path
object directly rather than the bootstrap side effect.

The stdlib-only dashboard-deploy trio (``build_manifest.py``,
``build_codebase_site_backcast.py``, ``register_hindcast.py``) runs on a bare
``python3`` with no installed deps and must NOT import this module — it keeps
its own stdlib bootstrap (see CLAUDE.md, Git & Pushing §3).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from market_sim.config.iso_configs import SUPPORTED_ISOS
from market_sim.config.paths import REPO_ROOT

__all__ = [
    "SUPPORTED_ISOS",
    "CALIBRATION_YEARS",
    "repo_root",
    "add_iso_arg",
    "add_years_arg",
    "add_out_dir_arg",
    "add_bundle_arg",
]

# Train/calibration tier (CLAUDE.md rule 22). The only years tuned against; the
# default for ``--year`` and the set the holdout gate enforces. Kept next to the
# --year help text so the tuple and its documentation share one literal.
CALIBRATION_YEARS: tuple[int, ...] = (2023, 2024, 2025)


def repo_root() -> Path:
    """Return the repository root (re-export of ``config.paths.REPO_ROOT``)."""
    return REPO_ROOT


def add_iso_arg(
    parser: argparse.ArgumentParser,
    *,
    required: bool = False,
    multi: bool = False,
    default: str | None = None,
    help: str | None = None,
) -> argparse.Action:
    """Add a ``--iso`` argument constrained to :data:`SUPPORTED_ISOS`.

    Args:
        parser: the argparse parser to add ``--iso`` to.
        required: make ``--iso`` mandatory.
        multi: accept one or more ISOs (``nargs="+"``); the parsed value is a
            list. Otherwise a single ISO string.
        default: default value when neither ``required`` nor a caller value is
            given (single-ISO form only).
        help: override the default help text.

    Returns:
        The :class:`argparse.Action` argparse creates, so callers can tweak it.
    """
    kwargs: dict = {
        "choices": SUPPORTED_ISOS,
        "help": help
        or "ISO to operate on (one of the registered ISOs: "
        + ", ".join(SUPPORTED_ISOS)
        + ").",
    }
    if multi:
        kwargs["nargs"] = "+"
    if required:
        kwargs["required"] = True
    elif default is not None:
        kwargs["default"] = default
    return parser.add_argument("--iso", **kwargs)


def add_years_arg(
    parser: argparse.ArgumentParser,
    *,
    default: tuple[int, ...] = CALIBRATION_YEARS,
    flag: str = "--year",
    dest: str | None = None,
    help: str | None = None,
) -> argparse.Action:
    """Add a multi-value ``--year`` argument defaulting to the calibration tier.

    The help text names the rule-22 holdout gate so every tool that scores or
    solves years documents the same constraint: only 2023-2025 are tunable;
    solving a holdout year (2022, 2019, H1-2026) requires explicit
    authorization and a calibration-complete marker.

    Args:
        parser: the parser to add ``--year`` to.
        default: default year tuple (materialized as a list for argparse).
        flag: the option string (``"--year"`` by convention; ``"--years"`` for
            tools that spell it plural).
        dest: explicit destination attribute name when it must differ from the
            flag-derived default.
        help: override the default help text.

    Returns:
        The :class:`argparse.Action` for the added argument.
    """
    kwargs: dict = {
        "nargs": "+",
        "type": int,
        "default": list(default),
        "help": help
        or (
            "Year(s) to operate on (default "
            + " ".join(str(y) for y in default)
            + ", the rule-22 train/calibration tier). Only 2023-2025 are "
            "tunable; a holdout year (2022, 2019, H1-2026) requires explicit "
            "authorization and the ISO's calibration-complete marker "
            "(CLAUDE.md rule 22)."
        ),
    }
    if dest is not None:
        kwargs["dest"] = dest
    return parser.add_argument(flag, **kwargs)


def add_out_dir_arg(
    parser: argparse.ArgumentParser,
    *,
    flag: str = "--out-dir",
    required: bool = False,
    default: Path | None = None,
    help: str | None = None,
) -> argparse.Action:
    """Add an output-directory argument (a :class:`~pathlib.Path`).

    Args:
        parser: the parser to add the flag to.
        flag: the option string (``"--out-dir"`` by convention).
        required: make the flag mandatory.
        default: default output directory.
        help: override the default help text.

    Returns:
        The :class:`argparse.Action` for the added argument.
    """
    kwargs: dict = {
        "type": Path,
        "help": help or "Output directory for generated artifacts.",
    }
    if required:
        kwargs["required"] = True
    if default is not None:
        kwargs["default"] = default
    return parser.add_argument(flag, **kwargs)


def add_bundle_arg(
    parser: argparse.ArgumentParser,
    *,
    positional: bool = False,
    required: bool = False,
    help: str | None = None,
) -> argparse.Action:
    """Add a bundle argument (a run id or a ``results/calibration/<name>`` path).

    Pairs with :func:`scripts.lib.bundle_io.resolve_bundle`, which accepts either
    spelling.

    Args:
        parser: the parser to add the argument to.
        positional: add it as a positional ``bundle`` argument instead of the
            ``--bundle`` option.
        required: make the ``--bundle`` option mandatory (ignored when
            ``positional`` — a positional is required by construction).
        help: override the default help text.

    Returns:
        The :class:`argparse.Action` for the added argument.
    """
    text = help or "Calibration bundle: a run id or a results/calibration/<name> path."
    if positional:
        return parser.add_argument("bundle", help=text)
    kwargs: dict = {"help": text}
    if required:
        kwargs["required"] = True
    return parser.add_argument("--bundle", **kwargs)
