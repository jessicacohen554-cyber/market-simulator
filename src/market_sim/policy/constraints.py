"""Policy-driven LP constraint assembly.

Extension point for constraint-type policies -- caps and standards that
enter the dispatch optimization as additional constraint rows rather than
as price adders. Examples include NOx emission caps and RPS energy
constraints.
"""

from __future__ import annotations

from market_sim.config.scenarios import ScenarioConfig
from market_sim.policy.cap_and_trade import MassCapSpec, resolve_carbon_program


def get_active_policy_constraints(
    config: ScenarioConfig, year: int
) -> list[MassCapSpec]:
    """Return LP constraint-row specs for active constraint-type policies.

    Currently surfaces the emissions **mass-cap** row (the row path of the
    unified carbon resolver, :func:`market_sim.policy.cap_and_trade.
    resolve_carbon_program`). Returns ``[cap_spec]`` when ``mass_cap_enabled``
    is set and a power-sector tonnage budget is configured for the ISO's
    program/year; otherwise ``[]`` (the adder path, or no program, adds no
    row). Extension point for NOx caps and other constraint-type policies.

    Args:
        config: Scenario config supplying the active policy levers.
        year: Simulation year.

    Returns:
        A list of :class:`MassCapSpec` (one per active mass cap); empty when no
        constraint-type policy binds.
    """
    resolution = resolve_carbon_program(config, year)
    if resolution is not None and resolution.cap_spec is not None:
        return [resolution.cap_spec]
    return []
