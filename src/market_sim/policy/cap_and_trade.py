"""Unified carbon-program resolver: one channel, exactly one price source.

Every carbon path routes through the same two fleet quantities —
``emission_rate`` (tCO2/MWh) and a per-generator membership weight ``m[g]`` —
so backcast and forecast share one structure
(``docs/handoffs/emissions-mass-cap-plan-2026-07.md`` §3). The effective
carbon cost on a member generator is always ``emission_rate[g] * m[g] *
p_allowance``; only the *source* of ``p_allowance`` differs:

* **Adder path** (the faithful RGGI/CARB representation): a known-ex-ante
  allowance price — measured in backcast, projected forward — folded into
  marginal cost. This is what CAISO/NYISO/NEISO use, because RGGI/CARB clear
  in a banked, multi-sector market this power model does not contain (plan §2).
* **Row path** (the PP-2.1 IPM-parity mechanism, opt-in): a genuine
  power-sector mass budget whose LP dual is the endogenous allowance price.
  Faithfully represents EPA 111(d)/CSAPR or a user scenario cap — a
  power-sector-only, no-bank scenario price (plan §2, §8), NOT the RGGI/CARB
  market price.

:func:`resolve_carbon_program` returns the ISO's active resolution for a year
with EXACTLY ONE of ``price_adder`` / ``cap_spec`` set (invariant-asserted).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from market_sim.config.constants import (
    CAP_AND_TRADE_PROGRAMS,
    STATE_CARBON_PRICE_BY_ISO,
    CapAndTradeProgram,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig


@dataclass(frozen=True)
class MassCapSpec:
    """A single power-sector emissions mass-cap for the LP row path.

    Attributes:
        membership: Per-zone membership weight ``m_zone`` (len ``n_zones``);
            the dispatch builder broadcasts it to generators via
            ``fleet.zone_idx`` and multiplies by ``emission_rate`` to form the
            cap-row coefficient. Import/flow columns get zero coefficient.
        cap_tons: The annual emissions budget (tons CO2) — the row upper bound.
        label: Short program/pollutant label (e.g. ``"co2"``), surfaced on the
            reported allowance price.
    """

    membership: np.ndarray
    cap_tons: float
    label: str = "co2"


@dataclass(frozen=True)
class CarbonProgramResolution:
    """The active carbon-program resolution for one (ISO, year, solve).

    Exactly one of :attr:`price_adder` / :attr:`cap_spec` is non-``None`` — the
    core two-source design invariant (plan §6). ``membership`` is always set.

    Attributes:
        membership: Per-zone membership weight ``m_zone`` (len ``n_zones``).
        price_adder: The exogenous allowance price ($/tCO2) on the adder path,
            or ``None`` on the row path.
        cap_spec: The mass-cap row spec on the row path, or ``None`` on the
            adder path.
    """

    membership: np.ndarray
    price_adder: float | None = None
    cap_spec: MassCapSpec | None = None

    def __post_init__(self) -> None:
        has_adder = self.price_adder is not None
        has_cap = self.cap_spec is not None
        if has_adder == has_cap:
            raise ValueError(
                "CarbonProgramResolution must carry exactly one of "
                f"price_adder / cap_spec (got price_adder={self.price_adder!r}, "
                f"cap_spec={'set' if has_cap else None})"
            )


def _membership(program: CapAndTradeProgram, zone_names: list[str]) -> np.ndarray:
    """Return the per-zone membership weight ``m_zone`` for ``program``.

    Uniform 1.0 on every load zone (0.0 on named external/import nodes) unless
    the program supplies a fractional ``zone_share`` map (PJM's multi-state
    roll-up zones), in which case each zone takes its mapped share (absent →
    0.0). Forecast-reproducible: state boundaries and zone definitions are
    fixed (plan §5).
    """
    if program.zone_share is not None:
        return np.array(
            [float(program.zone_share.get(z, 0.0)) for z in zone_names], dtype=float
        )
    external = set(program.external_nodes)
    return np.array([0.0 if z in external else 1.0 for z in zone_names], dtype=float)


def measured_price(iso: str, year: int) -> float | None:
    """Return the measured backcast allowance price ($/tCO2), or ``None``.

    Looks up :data:`STATE_CARBON_PRICE_BY_ISO` — the CARB (CAISO) and RGGI
    (NYISO/NEISO) quarterly-auction annual averages, 2023-2025. ``None`` when
    the ISO has no measured series or the year is outside it.
    """
    series = STATE_CARBON_PRICE_BY_ISO.get(iso)
    if series is None or year not in series:
        return None
    return float(series[year])


def projected_price(program: CapAndTradeProgram, iso: str, year: int) -> float:
    """Return the projected forward-year allowance price ($/tCO2).

    Anchors on the last realized clearing price
    (:data:`STATE_CARBON_PRICE_BY_ISO`) and escalates it at the program's
    published price-containment-band rate (:attr:`CapAndTradeProgram.
    escalation_rate`). This is an explicitly-labelled scenario trajectory (a
    floor-band escalator, plan §7), NOT a market-price forecast, and it is
    never tuned to a residual (CLAUDE.md rule 1). Returns ``0.0`` when the ISO
    has no measured anchor series (PJM).
    """
    series = STATE_CARBON_PRICE_BY_ISO.get(iso)
    if not series:
        return 0.0
    last_year = max(series)
    anchor = float(series[last_year])
    if year <= last_year:
        return anchor
    return anchor * (1.0 + program.escalation_rate) ** (year - last_year)


def resolve_carbon_program(
    config: ScenarioConfig, year: int
) -> CarbonProgramResolution | None:
    """Resolve the ISO's active carbon program for ``year``.

    Returns ``None`` when the ISO has no cap-and-trade program (ERCOT/MISO) or
    ``state_carbon_pricing`` is off. Otherwise returns a
    :class:`CarbonProgramResolution` with the per-zone membership and exactly
    one price source:

    * **Row path** — when ``mass_cap_enabled`` is set and a power-sector cap is
      configured for the program/year (:func:`_power_sector_cap`): a
      :class:`MassCapSpec` whose LP dual is the endogenous allowance price.
    * **Adder path** — otherwise: the measured (backcast) or projected
      (forecast) exogenous allowance price. In forecast the projected program
      price is used only when the caller has not chosen an explicit exogenous
      RFF ``carbon_price_path`` (default ``"zero"``), so an explicit RFF path
      still wins (backward compatible with pre-EM-6 forecast configs). A
      nonzero explicit ``config.carbon_price`` scenario override is handled by
      the scalar wrapper :func:`market_sim.policy.carbon.resolve_carbon_price`
      and is not applied here.

    Args:
        config: Scenario config supplying ``iso``, ``mode`` and the toggles.
        year: Simulation year.

    Returns:
        The resolution, or ``None`` when no program applies.
    """
    program = CAP_AND_TRADE_PROGRAMS.get(config.iso)
    if program is None:
        return None
    if not getattr(config, "state_carbon_pricing", True):
        return None

    zone_names = get_iso_config(config.iso).zone_names
    membership = _membership(program, zone_names)

    # Row path: a genuine power-sector budget is configured for this run.
    if getattr(config, "mass_cap_enabled", False):
        cap_spec = _power_sector_cap(config, program, year, membership)
        if cap_spec is not None:
            return CarbonProgramResolution(membership=membership, cap_spec=cap_spec)

    # Adder path — the faithful RGGI/CARB representation.
    if config.mode == "backcast":
        price = measured_price(config.iso, year)
    else:
        # Forecast: an explicit exogenous RFF path (non-default) wins so
        # pre-EM-6 forecast configs keep their behaviour; otherwise carry the
        # projected program price (the EM-6 seam fix — forecast carbon is no
        # longer zero for a program ISO).
        if getattr(config, "carbon_price_path", "zero") not in ("zero", None):
            price = None
        else:
            price = projected_price(program, config.iso, year)
    return CarbonProgramResolution(
        membership=membership, price_adder=float(price or 0.0)
    )


def _power_sector_cap(
    config: ScenarioConfig,
    program: CapAndTradeProgram,
    year: int,
    membership: np.ndarray,
) -> MassCapSpec | None:
    """Return the configured power-sector mass-cap for the row path, or ``None``.

    Sources the annual tonnage budget from ``config.mass_cap_tons`` (an explicit
    scenario budget) when set. The published RGGI/CARB budget schedules land via
    the data-intake step; until a budget is supplied the row stays inert and this
    returns ``None`` (adder path used instead). The endogenous dual of a row
    built here is a power-sector, no-bank scenario allowance price (plan §2, §8).
    """
    cap_tons = getattr(config, "mass_cap_tons", None)
    if cap_tons is None:
        return None
    label = getattr(config, "mass_cap_program", None) or program.name.lower()
    return MassCapSpec(membership=membership, cap_tons=float(cap_tons), label=label)
