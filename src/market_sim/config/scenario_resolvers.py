"""PB-1 uncertainty-lever resolvers for :class:`ScenarioConfig`.

Extracted verbatim from ``config.scenarios`` (refactor-consolidation plan
2026-07 §5 item 9 — code motion only, no value changes). ``config.scenarios``
re-exports every name here, so both import paths stay live; the historical
``from market_sim.config.scenarios import resolve_*`` spelling is pinned by
``tests/test_scenarios_facade.py``. ``resolve_real_discount_rate`` (an FF-1E
financing option, not a PB-1 lever) stays defined in ``config.scenarios``.

Pure, config-build-time resolvers for the probability-bounds levers
(docs/handoffs/probability-bounds-plan-2026-07.md). Each pairs a discrete
"_path" field (the §1 deterministic scenario-matrix axis) with a
continuous "_percentile" field (the §2 multivariate sampler axis, 0.0=low,
0.5=mid, 1.0=high). At every field's neutral default the resolved value is
byte-identical to today's behavior; a percentile only takes effect when
moved off its neutral 0.5 midpoint, so the two axes never fight silently.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from market_sim.config.scenarios import ScenarioConfig

_PERCENTILE_BY_PATH_LABEL: dict[str, float] = {"low": 0.0, "mid": 0.5, "high": 1.0}
_NEUTRAL_PERCENTILE: float = 0.5


def _interpolate_low_mid_high(
    percentile: float, low: float, mid: float, high: float
) -> float:
    """Piecewise-linear interpolation across (0.0, 0.5, 1.0) -> (low, mid, high).

    Shared by every PB-1 "_percentile" lever (:func:`resolve_new_entry_costs`,
    :func:`resolve_demand_growth_rate`): 0.0 returns ``low``, 0.5 returns
    ``mid`` exactly, 1.0 returns ``high``, and values in between interpolate
    linearly on each half. Clamped to [0.0, 1.0] so an out-of-range draw
    cannot silently extrapolate past the cited low/high levels.
    """
    p = min(1.0, max(0.0, percentile))
    if p <= _NEUTRAL_PERCENTILE:
        frac = p / _NEUTRAL_PERCENTILE
        return low + (mid - low) * frac
    frac = (p - _NEUTRAL_PERCENTILE) / (1.0 - _NEUTRAL_PERCENTILE)
    return mid + (high - mid) * frac


def _effective_percentile(path_label: str, percentile: float) -> float:
    """Resolve the effective 0-1 percentile for a path/percentile field pair.

    The continuous ``percentile`` field wins whenever it has been moved off
    its neutral 0.5 midpoint (the sampler's job, PB-1 §2); otherwise the
    discrete ``path_label`` field's own selection is used (the scenario
    matrix's job, PB-1 §1). Both at their defaults resolve to 0.5 either way,
    so this is a no-op unless a caller actually sets one of the two levers.
    """
    if percentile != _NEUTRAL_PERCENTILE:
        return percentile
    return _PERCENTILE_BY_PATH_LABEL[path_label]


def resolve_new_entry_costs(config: "ScenarioConfig") -> dict[str, dict[str, float]]:
    """Return :data:`constants.NEW_ENTRY_COSTS` scaled by the tech-cost lever.

    Interpolates each technology's ``capex_per_kw`` and ``learning_rate``
    across :data:`constants.TECH_COST_MULTIPLIERS`' low/mid/high cases (NREL
    ATB 2024 Advanced/Moderate/Conservative) using the effective percentile
    from ``config.tech_cost_path``/``config.tech_cost_percentile`` (PB-1
    §1.1/§2.1). ``base_cf`` and ``lifetime_yr`` are untouched -- the tech-cost
    lever is a cost lever, not a performance one. At the neutral default
    ("mid"/0.5, multiplier 1.0 on every tech) this returns values identical to
    :data:`constants.NEW_ENTRY_COSTS`.

    Args:
        config: Scenario config supplying ``tech_cost_path`` and
            ``tech_cost_percentile``.

    Returns:
        A new ``{tech: {param: value}}`` dict, the same shape as
        :data:`constants.NEW_ENTRY_COSTS`.
    """
    from market_sim.config.constants import NEW_ENTRY_COSTS, TECH_COST_MULTIPLIERS

    percentile = _effective_percentile(
        config.tech_cost_path, config.tech_cost_percentile
    )
    resolved: dict[str, dict[str, float]] = {}
    for tech, costs in NEW_ENTRY_COSTS.items():
        scaled = dict(costs)
        multipliers = TECH_COST_MULTIPLIERS.get(tech)
        if multipliers is not None:
            for param in ("capex_per_kw", "learning_rate"):
                mult = _interpolate_low_mid_high(
                    percentile,
                    multipliers["low"][param],
                    multipliers["mid"][param],
                    multipliers["high"][param],
                )
                scaled[param] = costs[param] * mult
        resolved[tech] = scaled
    return resolved


def resolve_demand_growth_rate(config: "ScenarioConfig", year: int) -> float:
    """Return the demand growth rate for ``year`` under the PB-1 load lever.

    Selects the near/long era from ``constants.DEMAND_GROWTH_TRANSITION_YEAR``,
    then interpolates :data:`constants.DEMAND_GROWTH_RATES`' low/mid/high era
    rates at the effective percentile from ``config.demand_growth_path``/
    ``config.demand_growth_percentile`` (PB-1 §1.1/§2.1; both eras move
    together). Falls back to ``config.demand_growth_rate`` exactly as the
    legacy path-only lookup did, when the config's ISO or
    ``demand_growth_path`` has no entry in the table (e.g. MISO).

    Args:
        config: Scenario config supplying the ISO and both growth levers.
        year: Simulation year.

    Returns:
        The annual demand growth rate (fraction, e.g. 0.03 = 3%/yr).
    """
    from market_sim.config.constants import (
        DEMAND_GROWTH_RATES,
        DEMAND_GROWTH_TRANSITION_YEAR,
    )

    iso_rates = DEMAND_GROWTH_RATES.get(config.iso, {})
    path_rates = iso_rates.get(config.demand_growth_path)
    if not isinstance(path_rates, dict):
        return config.demand_growth_rate

    era = "near" if year <= DEMAND_GROWTH_TRANSITION_YEAR else "long"
    low = iso_rates.get("low", {}).get(era)
    mid = iso_rates.get("mid", {}).get(era)
    high = iso_rates.get("high", {}).get(era)
    if low is None or mid is None or high is None:
        return path_rates[era]

    percentile = _effective_percentile(
        config.demand_growth_path, config.demand_growth_percentile
    )
    return _interpolate_low_mid_high(percentile, low, mid, high)


# Underlying-field overrides per named policy bundle (PB-1 §1.2). "current"
# is empty -- every field keeps its own legislated-default value. IRA year
# offsets apply to every ira_*_last_year field uniformly.
_IRA_LAST_YEAR_FIELDS: tuple[str, ...] = (
    "ira_wind_solar_last_year",
    "ira_45u_last_year",
    "ira_other_clean_last_full_year",
    "ira_other_clean_75pct_year",
    "ira_other_clean_50pct_year",
    "ira_other_clean_phaseout_end",
    "ira_h2_45v_last_year",
    "ira_ccus_45q_last_year",
)

_POLICY_BUNDLES: dict[str, dict] = {
    "current": {},
    "tight": {
        # RFF mid carbon path; IRA horizons extended +5yr (plan §1.2).
        "carbon_price_path": "mid",
        "ira_year_offset": 5,
    },
    "rollback": {
        # No federal carbon price (same as current); state programs frozen
        # off rather than left escalating -- the nearest existing-field
        # expression of "no further state-program pricing," since a genuine
        # flat-forward-freeze trajectory mechanism doesn't exist yet (a
        # disclosed simplification, PB-1 §1.2). IRA sunset pulled -2yr.
        "carbon_price_path": "zero",
        "state_carbon_pricing": False,
        "ira_year_offset": -2,
    },
}


def resolve_policy_bundle(config: "ScenarioConfig") -> "ScenarioConfig":
    """Resolve ``config.policy_bundle`` to its underlying fields (PB-1 §1.2).

    Returns a copy of ``config`` with ``carbon_price_path``,
    ``state_carbon_pricing``, and every ``ira_*_last_year`` field replaced
    per the named bundle -- a resolver, not hidden state, so the RESOLVED
    fields (not the ``policy_bundle`` label) are what a caller should record
    to ``run_config.json``. "current" overrides nothing and returns ``config``
    unchanged.

    Args:
        config: Scenario config supplying ``policy_bundle`` and the fields it
            resolves.

    Returns:
        ``config`` with the bundle's field overrides applied (or ``config``
        itself, unchanged, for "current").

    Raises:
        ValueError: If ``config.policy_bundle`` is not a registered bundle.
    """
    if config.policy_bundle not in _POLICY_BUNDLES:
        raise ValueError(
            f"ScenarioConfig.policy_bundle must be one of "
            f"{sorted(_POLICY_BUNDLES)}, got {config.policy_bundle!r}"
        )
    spec = _POLICY_BUNDLES[config.policy_bundle]
    overrides = {k: v for k, v in spec.items() if k != "ira_year_offset"}
    offset = spec.get("ira_year_offset", 0)
    if offset:
        for field_name in _IRA_LAST_YEAR_FIELDS:
            overrides[field_name] = getattr(config, field_name) + offset
    if not overrides:
        return config
    return replace(config, **overrides)
