"""Policy-driven LP constraint assembly.

Extension point for constraint-type policies -- caps and standards that
enter the dispatch optimization as additional constraint rows rather than
as price adders. Examples include NOx emission caps and RPS energy
constraints.
"""

from __future__ import annotations

from market_sim.config.scenarios import ScenarioConfig


def get_active_policy_constraints(config: ScenarioConfig, year: int) -> list:
    """Return LP constraint rows for active constraint-type policies.

    Currently returns an empty list. Extension point for NOx caps, RPS
    constraints, etc.

    Args:
        config: Scenario config supplying the active policy levers.
        year: Simulation year.

    Returns:
        A list of LP constraint rows; empty while no constraint-type
        policy is wired in.
    """
    return []
