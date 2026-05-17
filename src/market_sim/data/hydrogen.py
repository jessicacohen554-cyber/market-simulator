"""Derived hydrogen fuel economics.

Hydrogen is not modeled as storage. H2 turbines are thermal generators
whose delivered fuel cost is *derived* from the cost of the renewable
electricity used to produce the hydrogen and the efficiency of the
electrolyzer that converts it::

    h2_fuel_cost_$/MMBtu = (min(wind_lcoe, solar_lcoe) / eta) / MMBTU_PER_MWH

This keeps the hydrogen fuel cost physically grounded in production
economics without an exogenous price path: as renewables get cheaper and
electrolyzers improve, the H2 fuel cost falls automatically. It also
avoids circularity -- the model never prices its own fuel.
"""

from __future__ import annotations

from market_sim.config.constants import ELECTROLYZER_PARAMS, MMBTU_PER_MWH
from market_sim.config.scenarios import ScenarioConfig

# Milestone years for electrolyzer-efficiency interpolation. The base year
# uses the ``efficiency`` field; the later years use the projected fields.
_EFFICIENCY_MILESTONES: tuple[tuple[int, str], ...] = (
    (2026, "efficiency"),
    (2035, "efficiency_2035"),
    (2045, "efficiency_2045"),
)


def get_electrolyzer_efficiency(year: int, config: ScenarioConfig) -> float:
    """Return the electrolyzer efficiency (MWh_H2 / MWh_electricity).

    Efficiency is interpolated linearly between the 2026 base, 2035 and
    2045 milestone values of :data:`ELECTROLYZER_PARAMS` for the scenario's
    ``electrolyzer_type``. Years at or before 2026 use the base value;
    years at or after 2045 use the 2045 value (no extrapolation). When
    ``config.electrolyzer_efficiency_override`` is set it supersedes the
    lookup entirely.

    Args:
        year: Calendar year.
        config: Scenario configuration supplying ``electrolyzer_type`` and
            the optional efficiency override.

    Returns:
        The electrolyzer efficiency as a fraction.
    """
    if config.electrolyzer_efficiency_override is not None:
        return config.electrolyzer_efficiency_override

    params = ELECTROLYZER_PARAMS[config.electrolyzer_type]
    milestones = [(yr, params[key]) for yr, key in _EFFICIENCY_MILESTONES]

    if year <= milestones[0][0]:
        return milestones[0][1]
    if year >= milestones[-1][0]:
        return milestones[-1][1]

    for (y0, e0), (y1, e1) in zip(milestones, milestones[1:]):
        if y0 <= year <= y1:
            return e0 + (e1 - e0) * (year - y0) / (y1 - y0)
    return milestones[-1][1]


def h2_fuel_cost_per_mmbtu(
    renewable_lcoe: float, electrolyzer_efficiency: float
) -> float:
    """Return the hydrogen fuel cost in $/MMBtu.

    Converts the cost of the renewable electricity feeding an electrolyzer
    into a delivered hydrogen fuel cost::

        h2_$/MWh    = renewable_lcoe / electrolyzer_efficiency
        h2_$/MMBtu  = h2_$/MWh / MMBTU_PER_MWH

    Args:
        renewable_lcoe: Levelized cost of the renewable electricity in
            $/MWh.
        electrolyzer_efficiency: MWh of hydrogen (LHV) produced per MWh of
            electricity consumed.

    Returns:
        The hydrogen fuel cost in $/MMBtu.
    """
    h2_cost_per_mwh = renewable_lcoe / electrolyzer_efficiency
    return h2_cost_per_mwh / MMBTU_PER_MWH


def compute_h2_fuel_cost(year: int, config: ScenarioConfig, iso: str) -> float:
    """Derive the delivered hydrogen fuel cost in $/MMBtu.

    The cheaper of the wind and solar levelized cost of energy for the
    given ISO-year sets the renewable electricity price; dividing by the
    electrolyzer efficiency and converting MWh to MMBtu gives the fuel
    cost. The result is ISO-specific because renewable LCOEs differ between
    markets (ERCOT wind is cheap, CAISO solar is cheap).

    Args:
        year: Calendar year.
        config: Scenario configuration.
        iso: ISO identifier (carried for API symmetry; renewable LCOE is
            resolved through :func:`compute_lcoe`, which reads ``config``).

    Returns:
        The hydrogen fuel cost in $/MMBtu.
    """
    # Imported here to avoid a circular import: model.capacity imports this
    # module for the new-entry hydrogen LCOE screen.
    from market_sim.model.capacity import compute_lcoe

    wind_lcoe = compute_lcoe("wind", year, config)
    solar_lcoe = compute_lcoe("solar", year, config)
    renewable_lcoe = min(wind_lcoe, solar_lcoe)
    eta = get_electrolyzer_efficiency(year, config)
    return h2_fuel_cost_per_mmbtu(renewable_lcoe, eta)
