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
    CARB_ALLOWANCE_BUDGET,
    RGGI_MEMBER_STATES_BY_YEAR,
    RGGI_STATE_CO2_BUDGET,
    SHORT_TON_TO_METRIC_TONNE,
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


def _zone_share_for_year(year_shares: "dict[int, float] | None", year: int) -> float:
    """Return one zone's membership share for ``year`` from its ``{year: share}`` map.

    Exact match when available; otherwise holds at the nearest computed year
    (the fleet's state-mix composition is assumed static outside the derived
    window — a structural, forecast-reproducible assumption, never a
    residual-tuned choice, mirroring how :func:`projected_price` anchors on
    the last measured value). Returns ``0.0`` for an absent/empty map (a zone
    with no member-state fossil fleet at all).
    """
    if not year_shares:
        return 0.0
    if year in year_shares:
        return float(year_shares[year])
    nearest = min(year_shares, key=lambda y: abs(y - year))
    return float(year_shares[nearest])


def _membership(
    program: CapAndTradeProgram, zone_names: list[str], year: int
) -> np.ndarray:
    """Return the per-zone membership weight ``m_zone`` for ``program``/``year``.

    Uniform 1.0 on every load zone (0.0 on named external/import nodes) unless
    the program supplies a fractional ``zone_share`` map (PJM's multi-state
    roll-up zones), in which case each zone takes its mapped share for
    ``year`` (:func:`_zone_share_for_year`; absent zone → 0.0). This is the
    *zone-level* membership consumed by the adder path and by any generator a
    per-unit lookup can't resolve (see :func:`per_generator_membership`).
    Forecast-reproducible: state boundaries and zone definitions are fixed
    (plan §5).
    """
    if program.zone_share is not None:
        return np.array(
            [_zone_share_for_year(program.zone_share.get(z), year) for z in zone_names],
            dtype=float,
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
    config: ScenarioConfig, year: int, zone_names: list[str] | None = None
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
        zone_names: Optional override of the ISO's model zones. Defaults to
            the static :func:`get_iso_config` topology; callers that have
            already extended the topology with an import/external node at
            runtime (``runner.py``'s ``apply_interchange_topology``, e.g.
            PJM's dynamically-appended external zone) MUST pass that extended
            list — the mass-cap row's per-generator coefficient vector is
            broadcast by ``fleet_arrays.zone_idx``, which indexes into the
            *runtime* zone list, not the static one. Passing the static list
            when the runtime topology is longer under-sizes ``membership``
            and index-errors downstream (the external node then implicitly
            gets 0.0 membership once included, as it should since it is
            outside the capped region — plan §4 leakage).
    """
    program = CAP_AND_TRADE_PROGRAMS.get(config.iso)
    if program is None:
        return None
    if not getattr(config, "state_carbon_pricing", True):
        return None

    if zone_names is None:
        zone_names = get_iso_config(config.iso).zone_names
    membership = _membership(program, zone_names, year)

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


def _published_power_sector_budget(
    program: CapAndTradeProgram, year: int
) -> float | None:
    """Return the program's published annual budget in **metric tonnes**, or ``None``.

    Sources the cited annual schedules landed in ``constants.py`` and converts
    each to the model's internal metric-tonne emission-rate unit so the value is
    directly comparable to ``emission_rate[g] * P[g,t]``:

    * **CARB** — :data:`CARB_ALLOWANCE_BUDGET` (MMT CO2e; 1 CA GHG allowance = 1
      metric tonne) scaled by ``1e6``. This is the whole-economy cap, so a CAISO
      power-sector row against it is deeply slack (plan §2).
    * **RGGI** — the SUM of the program's own member states' published
      per-state budgets (:data:`RGGI_STATE_CO2_BUDGET`, short tons, converted
      at :data:`SHORT_TON_TO_METRIC_TONNE`) for the states that are actual
      RGGI members in ``year`` (:data:`RGGI_MEMBER_STATES_BY_YEAR` ∩
      ``program.member_states`` — e.g. Virginia's row only counts toward
      PJM's 2023 budget). Falls back to the regional
      :data:`RGGI_STATE_CO2_BUDGET`\\ ``["RGGI"]`` total — a looser over-bound
      — only for years without a per-state breakdown (the 2027-2030
      projections).

    Returns ``None`` when the program has no published budget for ``year``
    (e.g. a holdout-quarantined year, or PJM which carries no budget), leaving
    the row inert and the adder path active.
    """
    if program.name == "CARB":
        mmt = CARB_ALLOWANCE_BUDGET.get(year)
        return None if mmt is None else float(mmt) * 1.0e6
    if program.name == "RGGI":
        member_states = RGGI_MEMBER_STATES_BY_YEAR.get(year)
        if member_states is not None:
            states = [s for s in program.member_states if s in member_states]
            per_state = [
                RGGI_STATE_CO2_BUDGET[s][year]
                for s in states
                if year in RGGI_STATE_CO2_BUDGET.get(s, {})
            ]
            if per_state:
                return sum(per_state) * SHORT_TON_TO_METRIC_TONNE
        short_tons = RGGI_STATE_CO2_BUDGET.get("RGGI", {}).get(year)
        return (
            None
            if short_tons is None
            else float(short_tons) * SHORT_TON_TO_METRIC_TONNE
        )
    return None


def _power_sector_cap(
    config: ScenarioConfig,
    program: CapAndTradeProgram,
    year: int,
    membership: np.ndarray,
) -> MassCapSpec | None:
    """Return the configured power-sector mass-cap for the row path, or ``None``.

    Sources the annual tonnage budget (metric tonnes CO2) in precedence order:

    1. An explicit ``config.mass_cap_tons`` scenario budget when set (a bespoke
       counterfactual cap; taken as-is, already in metric tonnes).
    2. Otherwise the ISO program's **published** budget for ``year``
       (:func:`_published_power_sector_budget`) — the RGGI/CARB schedules landed
       in ``constants.py``, unit-converted to metric tonnes.

    Returns ``None`` when neither is available (no explicit budget and no
    published schedule for the year, e.g. a holdout-quarantined year), leaving
    the row inert and the adder path active. The endogenous dual of a row built
    here is a power-sector, no-bank scenario allowance price (plan §2, §8).
    """
    cap_tons = getattr(config, "mass_cap_tons", None)
    if cap_tons is None:
        cap_tons = _published_power_sector_budget(program, year)
    if cap_tons is None:
        return None
    label = getattr(config, "mass_cap_program", None) or program.name.lower()
    return MassCapSpec(membership=membership, cap_tons=float(cap_tons), label=label)


# Cache of {iso: {plant_code: state}}, populated on first use per ISO (mirrors
# data.zone_assignment's own per-process eGRID cache).
_PLANT_STATE_CACHE: dict[str, dict[int, str]] = {}


def _plant_state_lookup(iso: str) -> dict[int, str]:
    """Return (and cache) ``{plant_code: state}`` for ``iso`` from EIA-860."""
    cached = _PLANT_STATE_CACHE.get(iso)
    if cached is None:
        from market_sim.data.zone_assignment import plant_state_lookup

        cached = plant_state_lookup(iso)
        _PLANT_STATE_CACHE[iso] = cached
    return cached


def per_generator_membership(
    iso: str,
    year: int,
    zone_membership: np.ndarray,
    fleet_arrays,
    plant_state: "dict[int, str] | None" = None,
) -> np.ndarray:
    """Return the per-generator membership weight ``m[g]``, per-unit where possible.

    Starts from the zone-level broadcast (``zone_membership[fleet_arrays.
    zone_idx]`` — today's approximation, exact for CAISO/NYISO/NEISO where
    membership is uniform, and PJM's fractional fallback for zones the fleet
    representation can't resolve further) and then, for every generator whose
    ``plant_code`` names a real physical plant (``plant_code > 0``), overrides
    it with the EXACT membership test against that plant's own state: 1.0 if
    the state is a program member in ``year``
    (:data:`RGGI_MEMBER_STATES_BY_YEAR` for RGGI; ``program.member_states`` for
    CARB, which is static), else 0.0. A unit with no resolvable state (missing
    from the EIA-860 plant file) or a synthetic aggregate unit (``plant_code
    <= 0`` — a legacy equal-width heat-rate bin spanning many plants/states)
    keeps the zone-level fallback (plan §5, §9.6).

    Args:
        iso: Model ISO name.
        year: Simulation year (selects the RGGI member-state set).
        zone_membership: The :class:`MassCapSpec`/adder-path ``m_zone``
            vector (len ``n_zones``) to broadcast as the fallback.
        fleet_arrays: The scenario's ``FleetArrays`` (needs ``zone_idx`` and
            ``plant_code``).
        plant_state: Optional injected ``{plant_code: state}`` map (for
            tests); defaults to the real EIA-860-backed, per-ISO-cached
            lookup (:func:`market_sim.data.zone_assignment.plant_state_lookup`).

    Returns:
        Per-generator membership array, shape ``(n_gen,)``.
    """
    baseline = np.asarray(zone_membership, dtype=float)[fleet_arrays.zone_idx]
    program = CAP_AND_TRADE_PROGRAMS.get(iso)
    if program is None or not program.member_states:
        return baseline

    lookup = _plant_state_lookup(iso) if plant_state is None else plant_state
    if not lookup:
        return baseline

    member_states = (
        RGGI_MEMBER_STATES_BY_YEAR.get(
            year, RGGI_MEMBER_STATES_BY_YEAR[max(RGGI_MEMBER_STATES_BY_YEAR)]
        )
        if program.name == "RGGI"
        else frozenset(program.member_states)
    )

    out = baseline.copy()
    codes = np.asarray(fleet_arrays.plant_code, dtype=int)
    for i, code in enumerate(codes):
        if code <= 0:
            continue
        state = lookup.get(int(code))
        if state is None:
            continue
        out[i] = 1.0 if state in member_states else 0.0
    return out
