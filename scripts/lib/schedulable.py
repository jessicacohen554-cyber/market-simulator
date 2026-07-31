"""Re-export of the §2.1b solve-window cap for the script entry points.

The implementation lives in :mod:`market_sim.config.schedulable` because
``market_sim.runner``'s ``market-sim`` CLI is one of its callers and must build
its parser without ``scripts`` on ``sys.path``. This shim keeps the import path
the script drivers use (``scripts.lib.schedulable``) pointing at that single
implementation — there is exactly one copy of the cap, which is the whole point
of the extraction (forecast-readiness audit FR-25).
"""

from __future__ import annotations

from market_sim.config.schedulable import (
    MAX_UNAUTHORIZED_SOLVE_YEARS,
    add_authorization_flag,
    assert_config_schedulable,
    assert_schedulable,
    config_horizon,
)

__all__ = [
    "MAX_UNAUTHORIZED_SOLVE_YEARS",
    "add_authorization_flag",
    "assert_config_schedulable",
    "assert_schedulable",
    "config_horizon",
]
