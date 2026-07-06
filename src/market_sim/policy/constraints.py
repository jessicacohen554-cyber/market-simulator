"""Policy-driven LP constraint assembly.

Extension point for constraint-type policies -- caps and standards that
enter the dispatch optimization as additional constraint rows rather than
as price adders. Examples include NOx emission caps and RPS energy
constraints.
"""

from __future__ import annotations

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.policy.cap_and_trade import (
    MassCapSpec,
    per_generator_membership,
    resolve_carbon_program,
)


def get_active_policy_constraints(
    config: ScenarioConfig, year: int, zone_names: list[str] | None = None
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
        zone_names: Optional runtime zone list (see
            :func:`market_sim.policy.cap_and_trade.resolve_carbon_program`);
            the caller MUST pass its already-interchange-extended zone list
            here so the cap row's membership vector matches
            ``fleet_arrays.zone_idx``.

    Returns:
        A list of :class:`MassCapSpec` (one per active mass cap); empty when no
        constraint-type policy binds.
    """
    resolution = resolve_carbon_program(config, year, zone_names=zone_names)
    if resolution is not None and resolution.cap_spec is not None:
        return [resolution.cap_spec]
    return []


def build_mass_cap_dispatch_kwargs(
    config: ScenarioConfig,
    year: int,
    zone_names: list[str],
    fleet_arrays,
) -> dict:
    """Return the ``solve_dispatch`` mass-cap kwargs for one (config, year).

    Extracted from ``runner.py``'s forecast-path ``mass_caps`` block so the
    backcast **calibration harness** (``scripts/run_calibration.py::run_year``,
    which ``scripts/run_calibration_full.py::solve_and_persist`` calls
    directly) can share the identical seam — previously it never called
    :func:`get_active_policy_constraints` at all, so ``mass_cap_enabled`` was
    inert there (G-29, ``docs/handoffs/emissions-mass-cap-plan-2026-07.md``
    "Non-blocking follow-ons"). Returns ``{}`` (no dispatch_kwargs change,
    identical LP) when no cap is active for this (ISO, year, config) — the
    default, since ``mass_cap_enabled`` defaults ``False``.

    Args:
        config: Scenario config supplying the mass-cap toggles.
        year: Simulation year.
        zone_names: The solve's runtime zone list, already extended for any
            runtime topology addition (e.g. PJM's external interchange zone)
            — see :func:`market_sim.policy.cap_and_trade.
            resolve_carbon_program`'s ``zone_names`` note; a caller passing
            the static ISO-config list when the runtime topology is longer
            under-sizes the membership broadcast.
        fleet_arrays: The scenario's built ``FleetArrays`` (needs
            ``zone_idx``, ``plant_code``, ``emission_rate``).

    Returns:
        ``{"mass_cap_coeffs", "mass_cap_rhs", "mass_cap_labels"}`` when a cap
        is active, else ``{}``.
    """
    mass_caps = get_active_policy_constraints(config, year, zone_names=zone_names)
    if not mass_caps:
        return {}
    cap_coeffs = np.vstack(
        [
            per_generator_membership(config.iso, year, spec.membership, fleet_arrays)
            * fleet_arrays.emission_rate
            for spec in mass_caps
        ]
    )
    return dict(
        mass_cap_coeffs=cap_coeffs,
        mass_cap_rhs=np.array([spec.cap_tons for spec in mass_caps], dtype=float),
        mass_cap_labels=[spec.label for spec in mass_caps],
    )
