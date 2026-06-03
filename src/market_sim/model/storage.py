"""Energy storage modeling.

Storage parameter structs and fleet construction. The state-of-charge
dynamics constraints themselves are built inside
:func:`market_sim.model.dispatch.build_constraints`; this module supplies the
data layer that feeds them -- per-unit attributes, their vectorized
struct-of-arrays form, and a default fleet builder.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from pydantic import BaseModel

from market_sim.config.constants import (
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_BASE_FLEET_MW,
    STORAGE_DEGRADATION_REPLACEMENT_FRACTION,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_ELCC_BY_DURATION,
    STORAGE_ELCC_SATURATION_EXPONENT,
    STORAGE_TECH_BUILD_SHARE_CAP,
    STORAGE_TECH_POWER_SHARE,
    STORAGE_TECHS,
    WRIGHT_REFERENCE_GW,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.capacity import CumulativeDeployment
from market_sim.policy.ira import ira_phaseout_fraction


class StorageUnit(BaseModel):
    """Attributes of a single energy-storage unit.

    ``eta_charge`` and ``eta_discharge`` are one-way efficiencies; their
    product is the round-trip efficiency. ``zone_idx`` is the integer code
    of ``zone`` within the enclosing ISO's zone ordering.
    """

    unit_id: str
    zone: str
    tech_name: str
    power_cap_mw: float
    energy_cap_mwh: float
    eta_charge: float = 1.0
    eta_discharge: float = 1.0
    zone_idx: int = 0


@dataclass
class StorageArrays:
    """Vectorized storage attributes for dispatch computation.

    Every per-unit scalar attribute is stored as a ``(n_storage,)`` array,
    aligned across all fields by storage-unit index.
    """

    power_cap: np.ndarray
    energy_cap: np.ndarray
    eta_chg: np.ndarray
    eta_dis: np.ndarray
    zone_idx: np.ndarray
    tech_names: np.ndarray

    @property
    def n_storage(self) -> int:
        """Return the number of storage units in the fleet."""
        return len(self.power_cap)


def storage_units_to_arrays(
    units: list[StorageUnit],
    zone_names: list[str],
) -> StorageArrays:
    """Convert a list of storage units into vectorized ``StorageArrays``.

    Each unit's ``zone`` is resolved to an integer index against
    ``zone_names`` so the result aligns with the dispatch zone ordering.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}
    return StorageArrays(
        power_cap=np.array([u.power_cap_mw for u in units], dtype=float),
        energy_cap=np.array([u.energy_cap_mwh for u in units], dtype=float),
        eta_chg=np.array([u.eta_charge for u in units], dtype=float),
        eta_dis=np.array([u.eta_discharge for u in units], dtype=float),
        zone_idx=np.array([zone_to_idx[u.zone] for u in units], dtype=int),
        tech_names=np.array([u.tech_name for u in units], dtype=str),
    )


def _distribute_storage(
    iso: ISOConfig,
    config: ScenarioConfig,
    total_mw: float,
) -> list[StorageUnit]:
    """Split ``total_mw`` of storage power across an ISO's zones and techs.

    Power is allocated to each load zone in proportion to its ``load_share``
    and across technologies by ``STORAGE_TECH_POWER_SHARE``. Each technology's
    duration and round-trip efficiency come from ``constants.STORAGE_TECHS``;
    the round-trip efficiency is split evenly into one-way charge and discharge
    efficiencies.

    Returns:
        One ``StorageUnit`` per (load zone, technology) pair with nonzero
        power capacity.
    """
    units: list[StorageUnit] = []
    for z_idx, zone in enumerate(iso.zones):
        if zone.load_share <= 0.0:
            continue
        for tech_name, tech in STORAGE_TECHS.items():
            share = STORAGE_TECH_POWER_SHARE.get(tech_name, 0.0)
            power_mw = total_mw * zone.load_share * share
            if power_mw <= 0.0:
                continue
            rte = float(tech["rte"])
            if tech_name == "li_ion_4hr":
                rte = config.storage_rte_4hr
            elif tech_name == "li_ion_8hr":
                rte = config.storage_rte_8hr
            eta = rte**0.5
            units.append(
                StorageUnit(
                    unit_id=f"{zone.name}_{tech_name}",
                    zone=zone.name,
                    tech_name=tech_name,
                    power_cap_mw=power_mw,
                    energy_cap_mwh=power_mw * float(tech["duration_hr"]),
                    eta_charge=eta,
                    eta_discharge=eta,
                    zone_idx=z_idx,
                )
            )
    return units


def _resolve_pace(config: ScenarioConfig) -> str:
    """Return the validated ``storage_deployment`` pace from ``config``.

    Raises:
        ValueError: if ``config.iso`` or ``config.storage_deployment`` is not
            a known key of :data:`STORAGE_BASE_FLEET_MW`.
    """
    if config.iso not in STORAGE_BASE_FLEET_MW:
        supported = ", ".join(sorted(STORAGE_BASE_FLEET_MW))
        raise ValueError(
            f"Unknown iso '{config.iso}'. Supported: {supported}"
        )
    paces = STORAGE_BASE_FLEET_MW[config.iso]
    pace = config.storage_deployment
    if pace not in paces:
        supported = ", ".join(sorted(paces))
        raise ValueError(
            f"Unknown storage_deployment '{pace}'. Supported: {supported}"
        )
    return pace


def build_default_storage(
    iso: ISOConfig,
    config: ScenarioConfig,
) -> list[StorageUnit]:
    """Build a default storage fleet for an ISO and scenario.

    The total deployed power is the base-year capacity set by
    ``config.storage_deployment`` (see ``STORAGE_BASE_FLEET_MW``), split across
    load zones in proportion to each zone's ``load_share`` and across
    technologies by ``STORAGE_TECH_POWER_SHARE``.

    Args:
        iso: ISO topology supplying the zones and their load shares.
        config: Scenario config supplying the ``storage_deployment`` pace.

    Returns:
        One ``StorageUnit`` per (load zone, technology) pair with nonzero
        power capacity.

    Raises:
        ValueError: if ``config.storage_deployment`` is not a known pace.
    """
    pace = _resolve_pace(config)
    return _distribute_storage(
        iso, config, STORAGE_BASE_FLEET_MW[config.iso][pace]
    )


# Duration (hours) assumed for an EIA-860 storage unit whose energy
# capacity is blank — a rare gap; ERCOT's 2023 fleet reports it in full.
_EIA860_STORAGE_FALLBACK_DURATION_HR: float = 2.0


def load_eia860_storage(
    iso: str, year: int, config: ScenarioConfig
) -> list[StorageUnit]:
    """Build a storage fleet from EIA-860 operable energy-storage data.

    Reads the EIA-860 operable energy-storage schedule, keeps units online
    by the end of ``year``, assigns each to a model zone via the eGRID
    ORIS->zone lookup, and aggregates power and energy capacity per zone
    into one ``StorageUnit`` each. This grounds a calibration backcast in
    the historical battery fleet rather than the forward-looking
    ``STORAGE_BASE_FLEET_MW`` scenario constant.

    EIA-860 does not report round-trip efficiency, so the 4-hour lithium-ion
    RTE is applied uniformly. It is read through :func:`_storage_rte`, so a
    calibration sweep of ``config.storage_rte_4hr`` reaches the backcast
    fleet exactly as it reaches the forward-entry path -- rather than being
    silently pinned to the :data:`STORAGE_TECHS` constant.

    Args:
        iso: ISO identifier; zones come from its topology config.
        year: Backcast year; units commissioned after it are excluded.
        config: Scenario config; supplies the ``storage_rte_4hr`` override.

    Returns:
        One aggregated ``StorageUnit`` per zone with nonzero storage
        capacity. Empty when the EIA-860 file is missing or no operable
        units fall inside the ISO.
    """
    from market_sim.data.fleet import EIA_860_DIR
    from market_sim.data.zone_assignment import build_zone_lookup

    path = EIA_860_DIR / "eia860_energy_storage_operable.parquet"
    if not path.exists():
        return []
    try:
        zone_lookup = build_zone_lookup(iso)
    except Exception:
        return []
    if not zone_lookup:
        return []

    df = pd.read_parquet(path)
    df = df[df["Status"].astype(str).str.strip().str.upper() == "OP"]
    power = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
    energy = pd.to_numeric(
        df["Nameplate Energy Capacity (MWh)"], errors="coerce"
    )
    op_year = pd.to_numeric(df["Operating Year"], errors="coerce")

    per_zone_power: dict[str, float] = {}
    per_zone_energy: dict[str, float] = {}
    for code, p_mw, e_mwh, oy in zip(
        df["Plant Code"], power, energy, op_year
    ):
        if p_mw != p_mw or p_mw <= 0.0:  # NaN or non-positive
            continue
        if oy == oy and oy > year:  # commissioned after the backcast year
            continue
        try:
            zone = zone_lookup.get(int(code))
        except (TypeError, ValueError):
            zone = None
        if zone is None:
            continue
        if e_mwh != e_mwh or e_mwh <= 0.0:  # blank energy capacity
            e_mwh = p_mw * _EIA860_STORAGE_FALLBACK_DURATION_HR
        per_zone_power[zone] = per_zone_power.get(zone, 0.0) + float(p_mw)
        per_zone_energy[zone] = per_zone_energy.get(zone, 0.0) + float(e_mwh)

    eta = _storage_rte("li_ion_4hr", config) ** 0.5
    return [
        StorageUnit(
            unit_id=f"{zone}_eia860_storage",
            zone=zone,
            tech_name="li_ion",
            power_cap_mw=per_zone_power[zone],
            energy_cap_mwh=per_zone_energy[zone],
            eta_charge=eta,
            eta_discharge=eta,
            zone_idx=z_idx,
        )
        for z_idx, zone in enumerate(get_iso_config(iso).zone_names)
        if per_zone_power.get(zone, 0.0) > 0.0
    ]


# Economic life (years) over which storage capital cost is annualized.
_STORAGE_ECONOMIC_LIFE_YR: int = 20


def _capital_recovery_factor(rate: float, lifetime_yr: float) -> float:
    """Return the capital recovery factor for a given rate and lifetime."""
    if rate <= 0.0:
        return 1.0 / lifetime_yr
    growth = (1.0 + rate) ** lifetime_yr
    return rate * growth / (growth - 1.0)


def _storage_rte(tech_name: str, config: ScenarioConfig) -> float:
    """Return a tech's round-trip efficiency, honoring ``config`` overrides."""
    if tech_name == "li_ion_4hr":
        return config.storage_rte_4hr
    if tech_name == "li_ion_8hr":
        return config.storage_rte_8hr
    return float(STORAGE_TECHS[tech_name]["rte"])


def _arbitrage_block_days(duration_hr: int) -> int:
    """Length (days) of the arbitrage cycle window for a given duration.

    Storage completes one charge/discharge cycle per window. Short-duration
    storage cycles daily; long-duration storage shifts energy across multiple
    days, so its window widens with duration. The window is sized so a full
    ``duration_hr`` charge and a full ``duration_hr`` discharge never overlap
    (``2 × duration_hr <= 24 × block_days``), which both prevents
    double-counting and lets a 100-hour asset realize the multi-day value a
    fixed 24-hour window structurally hides.
    """
    return max(1, math.ceil(duration_hr / 12.0))


def estimate_storage_revenue(
    prices: np.ndarray,
    duration_hr: int,
    rte: float,
    degradation_cost_per_mwh: float = 0.0,
) -> float:
    """Annual arbitrage revenue per MW from prior year's price profile.

    The year is split into windows of :func:`_arbitrage_block_days` days. For
    each window: sort its prices, charge during the cheapest ``duration_hr``
    hours, discharge during the most expensive ``duration_hr`` hours, for one
    cycle per window. Margin per MWh discharged =
    ``avg_discharge_price - avg_charge_price / rte - degradation_cost_per_mwh``.
    Positive margins are summed × duration across all windows.

    Sizing the window to duration is what lets long-duration storage capture
    multi-day arbitrage: a fixed 24-hour window collapses the spread to zero
    for any duration at or beyond a day (the cheap and expensive hour-sets
    overlap), so iron-air and other LDES would screen as worthless.

    prices: (n_zones, T) or (T,). If multi-zone, uses the zone with the
    highest spread in each window. Returns $/MW-yr.

    Fully vectorized — no Python loop over windows.
    """
    price_arr = np.asarray(prices, dtype=float)
    if price_arr.ndim == 1:
        price_arr = price_arr[None, :]
    n_zones, total_hours = price_arr.shape
    d = int(duration_hr)
    if d <= 0:
        return 0.0

    block_hours = _arbitrage_block_days(d) * 24
    n_blocks = total_hours // block_hours
    if n_blocks == 0:
        return 0.0

    # Reshape to (n_zones, n_blocks, block_hours) and sort each window.
    block = price_arr[:, :n_blocks * block_hours].reshape(
        n_zones, n_blocks, block_hours
    )
    ordered = np.sort(block, axis=2)

    # Cheapest d hours (charge) and most expensive d hours (discharge).
    charge_avg = ordered[:, :, :d].mean(axis=2)       # (n_zones, n_blocks)
    discharge_avg = ordered[:, :, -d:].mean(axis=2)   # (n_zones, n_blocks)

    # For each window, pick the zone with the widest spread.
    spread = discharge_avg - charge_avg               # (n_zones, n_blocks)
    best_zone = np.argmax(spread, axis=0)             # (n_blocks,)
    blocks_idx = np.arange(n_blocks)

    margin = (
        discharge_avg[best_zone, blocks_idx]
        - charge_avg[best_zone, blocks_idx] / rte
        - degradation_cost_per_mwh
    )
    margin = np.maximum(margin, 0.0)
    return float(margin.sum() * d)


def _elcc_for_duration(duration_hr: float) -> float:
    """Interpolate the storage capacity credit (ELCC) for a duration.

    Linear interpolation over :data:`STORAGE_ELCC_BY_DURATION`, clamped at the
    table's endpoints.
    """
    durations = [d for d, _ in STORAGE_ELCC_BY_DURATION]
    credits = [c for _, c in STORAGE_ELCC_BY_DURATION]
    return float(np.interp(duration_hr, durations, credits))


def _degradation_cost_per_mwh(tech_name: str, config: ScenarioConfig) -> float:
    """Per-MWh-discharged cycling-degradation cost for a storage tech.

    Returns ``0.0`` when ``config.storage_degradation`` is off. Otherwise a
    slice of the energy-capacity capex amortized over the tech's rated cycle
    life (see :data:`STORAGE_DEGRADATION_REPLACEMENT_FRACTION`). High-cycling
    short-duration storage pays this on every arbitraged MWh; long-life flow /
    CAES / iron-air pay far less, reflecting their cycle-life advantage.
    """
    if not config.storage_degradation:
        return 0.0
    tech = STORAGE_TECHS[tech_name]
    cycles = float(tech.get("cycles", 0.0))
    if cycles <= 0.0:
        return 0.0
    capex_per_mwh = float(tech["capex_per_kwh"]) * 1000.0
    return (
        capex_per_mwh / cycles * STORAGE_DEGRADATION_REPLACEMENT_FRACTION
    )


def estimate_capacity_value(
    tech_name: str,
    existing_mw: float,
    config: ScenarioConfig,
    iso: str,
) -> float:
    """Resource-adequacy capacity value per MW-yr for the next unit built.

    Zero unless the ISO's :data:`MARKET_DESIGN` has a capacity market and
    ``config.storage_capacity_value`` is on. Otherwise:

        net_cone × 1000 × ELCC(duration) × (1 - penetration)^exponent

    The ELCC credit rises with duration; the saturation derate falls as
    existing storage approaches the deployment ceiling. Together they make
    short-duration capacity value collapse at high penetration while
    long-duration storage retains its firm-capacity credit — the mechanism
    that tilts new entry toward longer durations as storage saturates.
    """
    if not config.storage_capacity_value:
        return 0.0
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)
    if not design.capacity_market or design.net_cone_per_kw_yr <= 0.0:
        return 0.0

    duration_hr = float(STORAGE_TECHS[tech_name]["duration_hr"])
    elcc = _elcc_for_duration(duration_hr)

    ceiling = STORAGE_DEPLOYMENT_CEILING_MW.get(iso, 0.0)
    penetration = 0.0 if ceiling <= 0.0 else min(1.0, existing_mw / ceiling)
    derate = (1.0 - penetration) ** STORAGE_ELCC_SATURATION_EXPONENT

    return design.net_cone_per_kw_yr * 1000.0 * elcc * derate


def compute_storage_annual_cost(
    tech_name: str, year: int, config: ScenarioConfig,
    cumulative_gw: float | None = None,
) -> float:
    """Annualized storage cost per MW-yr.

    cost = capex_per_kw * CRF + fom_per_kw_yr, converted to $/MW-yr.
    Capex is first discounted along a Wright's-Law learning curve when
    ``cumulative_gw`` is supplied, then the IRA ITC is applied along the
    graduated phaseout schedule for non-wind/solar clean tech. Uses a
    20-year economic life for CRF.
    """
    tech = STORAGE_TECHS[tech_name]
    capex_per_kw = float(tech["capex_per_kw"])

    # Wright's Law learning curve. Both li-ion durations share the "li_ion"
    # manufacturing learning curve; iron-air maps to its own reference.
    if cumulative_gw is not None:
        ref_key = "li_ion" if "li_ion" in tech_name else tech_name
        reference_gw = WRIGHT_REFERENCE_GW.get(ref_key)
        if reference_gw is not None and cumulative_gw > 0:
            lr = float(tech["learning_rate"])
            capex_per_kw = capex_per_kw * (cumulative_gw / reference_gw) ** (-lr)

    frac = ira_phaseout_fraction(year, config)
    if frac > 0.0:
        capex_per_kw *= 1.0 - config.ira_itc_storage * frac
    crf = _capital_recovery_factor(
        config.real_discount_rate, _STORAGE_ECONOMIC_LIFE_YR
    )
    annual_cost_per_kw = capex_per_kw * crf + float(tech["fom_per_kw_yr"])
    return annual_cost_per_kw * 1000.0


def _build_new_storage_units(
    iso: ISOConfig,
    tech_name: str,
    config: ScenarioConfig,
    total_mw: float,
    year: int,
    seq: int,
) -> list[StorageUnit]:
    """Distribute a single tech's new build across an ISO's load zones.

    Power is split by ``load_share``; zero-load zones get nothing.
    """
    tech = STORAGE_TECHS[tech_name]
    duration_hr = float(tech["duration_hr"])
    eta = _storage_rte(tech_name, config) ** 0.5
    units: list[StorageUnit] = []
    for z_idx, zone in enumerate(iso.zones):
        if zone.load_share <= 0.0:
            continue
        power_mw = total_mw * zone.load_share
        if power_mw <= 0.0:
            continue
        units.append(
            StorageUnit(
                unit_id=f"{zone.name}_{tech_name}_new_{year}_{seq}",
                zone=zone.name,
                tech_name=tech_name,
                power_cap_mw=power_mw,
                energy_cap_mwh=power_mw * duration_hr,
                eta_charge=eta,
                eta_discharge=eta,
                zone_idx=z_idx,
            )
        )
    return units


def apply_storage_new_entry(
    existing_storage: list[StorageUnit],
    prices: np.ndarray,
    year: int,
    config: ScenarioConfig,
    iso: str,
    cumulative: CumulativeDeployment | None = None,
) -> list[StorageUnit]:
    """Add storage whose stacked value beats its annualized cost.

    Each tech in STORAGE_TECHS is screened on a value stack:
    - **Energy arbitrage** over duration-sized windows (so long-duration
      storage captures multi-day value), net of cycling degradation.
    - **Capacity value** — resource-adequacy revenue, paid only in ISOs whose
      MARKET_DESIGN has a capacity market and when
      ``config.storage_capacity_value`` is on. Its duration-rising ELCC credit
      and penetration-falling saturation derate tilt entry toward longer
      durations as storage saturates the peak.

    Profitable techs are ranked by margin and built in merit order, but no
    single tech may take more than ``STORAGE_TECH_BUILD_SHARE_CAP`` of one
    year's budget, so the build diversifies across durations rather than the
    top-margin tech monopolizing it. Two caps bind independently:
    - STORAGE_ANNUAL_BUILD_CAP_MW per ISO per year
    - STORAGE_DEPLOYMENT_CEILING_MW cumulative per ISO

    New units distributed across load zones by load_share. Uses
    config.storage_rte_4hr / storage_rte_8hr overrides when applicable.
    When ``cumulative`` is supplied, each tech's capex follows a
    Wright's-Law learning curve. Returns the full storage fleet
    (existing + new).
    """
    iso = iso.upper()
    iso_config = get_iso_config(iso)
    fleet = list(existing_storage)

    existing_mw = sum(u.power_cap_mw for u in existing_storage)
    ceiling = STORAGE_DEPLOYMENT_CEILING_MW.get(iso, 0.0)
    annual_cap = STORAGE_ANNUAL_BUILD_CAP_MW.get(iso, 0.0)
    budget = min(annual_cap, max(0.0, ceiling - existing_mw))
    if budget <= 0.0:
        return fleet

    margins: list[tuple[float, str]] = []
    for tech_name, tech in STORAGE_TECHS.items():
        revenue = estimate_storage_revenue(
            prices,
            int(tech["duration_hr"]),
            _storage_rte(tech_name, config),
            degradation_cost_per_mwh=_degradation_cost_per_mwh(
                tech_name, config
            ),
        )
        capacity_value = estimate_capacity_value(
            tech_name, existing_mw, config, iso
        )
        ref_key = "li_ion" if "li_ion" in tech_name else tech_name
        cum_gw = cumulative.get(ref_key) if cumulative else None
        cost = compute_storage_annual_cost(
            tech_name, year, config, cumulative_gw=cum_gw
        )
        margin = revenue + capacity_value - cost
        if margin > 0.0:
            margins.append((margin, tech_name))

    margins.sort(key=lambda m: m[0], reverse=True)

    # No single tech may take more than the share cap of the year's budget, so
    # a diverse build spreads across the profitable durations.
    per_tech_cap = budget * STORAGE_TECH_BUILD_SHARE_CAP
    remaining = budget
    for seq, (_, tech_name) in enumerate(margins):
        if remaining <= 0.0:
            break
        build_mw = min(remaining, per_tech_cap)
        remaining -= build_mw
        fleet.extend(
            _build_new_storage_units(
                iso_config, tech_name, config, build_mw, year, seq
            )
        )
    return fleet
