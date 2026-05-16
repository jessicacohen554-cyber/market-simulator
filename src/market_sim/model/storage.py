"""Energy storage modeling.

Storage parameter structs and fleet construction. The state-of-charge
dynamics constraints themselves are built inside
:func:`market_sim.model.dispatch.build_constraints`; this module supplies the
data layer that feeds them -- per-unit attributes, their vectorized
struct-of-arrays form, and a default fleet builder.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel

from market_sim.config.constants import (
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_BASE_FLEET_MW,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_TECH_POWER_SHARE,
    STORAGE_TECHS,
)
from market_sim.config.iso_configs import ISOConfig, get_iso_config
from market_sim.config.scenarios import ScenarioConfig


class StorageUnit(BaseModel):
    """Attributes of a single energy-storage unit.

    ``eta_charge`` and ``eta_discharge`` are one-way efficiencies; their
    product is the round-trip efficiency. ``zone_idx`` is the integer code
    of ``zone`` within the enclosing ISO's zone ordering.
    """

    unit_id: str
    zone: str
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
        ValueError: if ``config.storage_deployment`` is not a known pace.
    """
    pace = config.storage_deployment
    if pace not in STORAGE_BASE_FLEET_MW:
        supported = ", ".join(sorted(STORAGE_BASE_FLEET_MW))
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
    return _distribute_storage(iso, config, STORAGE_BASE_FLEET_MW[pace])


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


def estimate_storage_revenue(
    prices: np.ndarray, duration_hr: int, rte: float,
) -> float:
    """Annual arbitrage revenue per MW from prior year's price profile.

    For each day: sort 24 prices, charge during cheapest ``duration_hr``
    hours, discharge during most expensive ``duration_hr`` hours.
    Margin = avg_discharge_price - avg_charge_price / rte.
    Sum positive margins × duration across 365 days.

    prices: (n_zones, T) or (T,). If multi-zone, uses zone with
    highest daily spread. Returns $/MW-yr.
    """
    price_arr = np.asarray(prices, dtype=float)
    if price_arr.ndim == 1:
        price_arr = price_arr[None, :]
    _, total_hours = price_arr.shape
    n_days = total_hours // 24
    d = int(duration_hr)
    if n_days == 0 or d <= 0:
        return 0.0

    revenue = 0.0
    for day in range(n_days):
        block = price_arr[:, day * 24:(day + 1) * 24]
        ordered = np.sort(block, axis=1)
        charge_avg = ordered[:, :d].mean(axis=1)
        discharge_avg = ordered[:, -d:].mean(axis=1)
        # When multi-zone, screen the zone with the widest daily spread.
        best = int(np.argmax(discharge_avg - charge_avg))
        margin = discharge_avg[best] - charge_avg[best] / rte
        if margin > 0.0:
            revenue += margin * d
    return float(revenue)


def compute_storage_annual_cost(
    tech_name: str, year: int, config: ScenarioConfig,
) -> float:
    """Annualized storage cost per MW-yr.

    cost = capex_per_kw * CRF + fom_per_kw_yr, converted to $/MW-yr.
    Applies IRA ITC to capex if year <= config.ira_expiry_year.
    Uses a 20-year economic life for CRF.
    """
    tech = STORAGE_TECHS[tech_name]
    capex_per_kw = float(tech["capex_per_kw"])
    if year <= config.ira_expiry_year:
        capex_per_kw *= 1.0 - config.ira_itc_storage
    crf = _capital_recovery_factor(
        config.discount_rate, _STORAGE_ECONOMIC_LIFE_YR
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
) -> list[StorageUnit]:
    """Add storage if arbitrage revenue > annualized cost.

    Screens each tech in STORAGE_TECHS. Ranks profitable techs by
    margin, builds highest-margin first. Two caps bind independently:
    - STORAGE_ANNUAL_BUILD_CAP_MW per ISO per year
    - STORAGE_DEPLOYMENT_CEILING_MW cumulative per ISO

    New units distributed across load zones by load_share. Uses
    config.storage_rte_4hr / storage_rte_8hr overrides when applicable.
    Returns the full storage fleet (existing + new).
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
            prices, int(tech["duration_hr"]), _storage_rte(tech_name, config)
        )
        cost = compute_storage_annual_cost(tech_name, year, config)
        margin = revenue - cost
        if margin > 0.0:
            margins.append((margin, tech_name))

    margins.sort(key=lambda m: m[0], reverse=True)

    remaining = budget
    for seq, (_, tech_name) in enumerate(margins):
        if remaining <= 0.0:
            break
        build_mw = remaining
        remaining -= build_mw
        fleet.extend(
            _build_new_storage_units(
                iso_config, tech_name, config, build_mw, year, seq
            )
        )
    return fleet
