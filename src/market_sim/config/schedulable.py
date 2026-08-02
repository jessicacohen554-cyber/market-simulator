"""The §2.1b solve-window cap, shared by every schedulable entry point.

The Forecast Finalization Program's §2.1b window cap (owner's "10-hour rule",
2026-07-19; `docs/forecast-development-plan-2026-07.md` §7.9) says no forecast
invocation may span more than :data:`MAX_UNAUTHORIZED_SOLVE_YEARS` solve-years
in the active phase — T2/T3/golden/PB-5/W4-campaign windows are DEFERRED until
the per-ISO gate conditions hold AND a per-campaign, session-logged owner
authorization exists.

The guard used to live in ``scripts/run_full_horizon.py`` and was reachable
from exactly two entry points (that runner and ``run_ces_leg.py``), leaving
``market-sim run/sweep/ensemble/matrix``, the PB-5 slice drivers and the
golden-fixture seed able to schedule a 15- or 25-solve-year campaign with no
refusal anywhere (forecast-readiness audit 2026-07-30, FR-25). This module is
the single implementation those entry points now share.

It lives under ``market_sim.config`` rather than ``scripts/lib`` because
``market_sim.runner``'s CLI is one of its callers: the ``market-sim`` console
script must build its parser without ``scripts`` on ``sys.path`` (it is not part
of the installed package). ``scripts/lib/schedulable.py`` re-exports it for the
script entry points, and ``run_full_horizon`` re-exports
:func:`assert_schedulable` so its existing importers and tests are unaffected.

Two entry shapes are supported:

* :func:`assert_schedulable` — an explicit ``(start_year, end_year)`` window,
  the original pure function (unchanged semantics).
* :func:`assert_config_schedulable` — a :class:`ScenarioConfig`, for the CLIs
  whose horizon arrives inside a scenario YAML rather than as year arguments.
  Backcast configs are out of scope: a backcast window is governed by rule 22's
  holdout tiers (``scripts/lib/holdout_policy.py`` + ``run_calibration_full``'s
  ``--holdout-authorized`` gate), not by §2.1b.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing only
    from market_sim.config.scenarios import ScenarioConfig

# §2.1b window cap (the owner's "10-hour rule", 2026-07-19). A forecast/hindcast
# invocation launched under the Forecast Finalization Program may span at most
# this many solve-years unless the campaign is owner-authorized (the FF-3E
# schedulability guard, mirroring run_calibration_full.py's rule-22 gate).
MAX_UNAUTHORIZED_SOLVE_YEARS = 5

_REFUSAL_TAIL = (
    "The schedulable instruments are T0, T1-F (2026-2030), T1-X (2023-2027), "
    "T1-H (2021-2025) — all ≤5 yr. T2/T3/golden/PB-5/W4-campaign windows are "
    "DEFERRED until the owner opens the gate for this ISO (plan §2.1b: backcast "
    "keeper + calibration-complete marker, green T1 POC gates, crossover gap + "
    "FF-3E readiness + projected cost, and explicit per-campaign owner "
    "authorization). Pass --full-solve-authorized ONLY when that authorization "
    "exists."
)


def assert_schedulable(
    start_year: int,
    end_year: int,
    full_solve_authorized: bool,
    entry_point: str = "full-horizon solve",
) -> int:
    """Enforce the §2.1b window cap; return the solve-year count.

    A forecast run solves every year in the closed window, so the solve-year
    count is ``end - start + 1``. A window wider than
    :data:`MAX_UNAUTHORIZED_SOLVE_YEARS` is REFUSED (``SystemExit``) unless the
    owner authorized the full-horizon campaign for this ISO
    (``full_solve_authorized``) — the FF-3E schedulability guard mirroring
    ``run_calibration_full.py``'s rule-22 ``--holdout-authorized`` gate (plan
    §2.1b / §2.4-0 / §7.9). A pure function, so the guard is unit-testable
    without a solve.

    Args:
        start_year: First solve year.
        end_year: Last solve year (inclusive).
        full_solve_authorized: Whether the owner authorized a > 5-year window.
        entry_point: Human label for the refusing entry point, so the message
            names the CLI the operator actually invoked.

    Returns:
        The number of solve-years in the window.

    Raises:
        SystemExit: When the window exceeds the cap and is unauthorized.
    """
    n_solve_years = end_year - start_year + 1
    if n_solve_years > MAX_UNAUTHORIZED_SOLVE_YEARS and not full_solve_authorized:
        raise SystemExit(
            f"REFUSING {entry_point}: {start_year}-{end_year} is "
            f"{n_solve_years} solve-years, over the §2.1b cap of "
            f"{MAX_UNAUTHORIZED_SOLVE_YEARS}. " + _REFUSAL_TAIL
        )
    return n_solve_years


def config_horizon(config: "ScenarioConfig") -> tuple[int, int]:
    """Return the ``(start_year, end_year)`` a run of ``config`` would solve.

    ``ScenarioConfig.start_year``/``end_year`` are optional overrides; the
    runner falls back to the module-level ``START_YEAR``/``END_YEAR`` constants
    when either is ``None`` (``runner.run_scenario``). Resolving them the same
    way here is what makes the guard bite on the CLIs whose YAML carries no
    year fields at all — the audit's "base YAML defaults to 2026-2050" case.

    Args:
        config: The scenario whose horizon to resolve.

    Returns:
        The inclusive ``(start_year, end_year)`` window.
    """
    from market_sim.config.constants import END_YEAR, START_YEAR

    start = config.start_year if config.start_year is not None else START_YEAR
    end = config.end_year if config.end_year is not None else END_YEAR
    return int(start), int(end)


def assert_config_schedulable(
    config: "ScenarioConfig",
    full_solve_authorized: bool,
    entry_point: str,
) -> int | None:
    """Apply :func:`assert_schedulable` to a config-carried horizon.

    Backcast configs are returned unchecked (``None``): §2.1b is the FORECAST
    program's cap, and a backcast window is gated instead by rule 22's holdout
    tiers. Forecast configs — including the hindcast harness's
    ``mode="forecast", hindcast=True`` legs, which are exactly the T1-H/T1-X
    instruments §2.1b sizes — are checked.

    Args:
        config: The scenario about to be solved.
        full_solve_authorized: Whether the owner authorized a > 5-year window.
        entry_point: Human label for the refusing entry point.

    Returns:
        The solve-year count, or ``None`` for a backcast config.

    Raises:
        SystemExit: When the window exceeds the cap and is unauthorized.
    """
    if config.mode != "forecast":
        return None
    start, end = config_horizon(config)
    return assert_schedulable(start, end, full_solve_authorized, entry_point)


def add_authorization_flag(parser, dest_help: str = "") -> None:
    """Add the standard ``--full-solve-authorized`` flag to an argparse parser.

    Kept here so every entry point spells the flag, its default and its
    warning identically — a differently-named flag on one CLI is how the
    original two-of-six enforcement gap stayed invisible.

    Args:
        parser: An ``argparse.ArgumentParser`` (or subparser) to extend.
        dest_help: Optional extra sentence appended to the flag's help text.
    """
    parser.add_argument(
        "--full-solve-authorized",
        action="store_true",
        help=(
            "Owner authorization for a window over the §2.1b "
            f"{MAX_UNAUTHORIZED_SOLVE_YEARS}-solve-year cap. Pass ONLY with an "
            "explicit, session-logged per-campaign authorization. " + dest_help
        ).strip(),
    )
