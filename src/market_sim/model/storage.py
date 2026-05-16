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
    START_YEAR,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_DEPLOYMENT_MW,
    STORAGE_GROWTH_RATE,
    STORAGE_TECH_POWER_SHARE,
    STORAGE_TECHS,
)
from market_sim.config.iso_configs import ISOConfig
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
    if pace not in STORAGE_DEPLOYMENT_MW:
        supported = ", ".join(sorted(STORAGE_DEPLOYMENT_MW))
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
    ``config.storage_deployment`` (see ``STORAGE_DEPLOYMENT_MW``), split across
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
    return _distribute_storage(iso, config, STORAGE_DEPLOYMENT_MW[pace])


def build_storage_for_year(
    iso: ISOConfig, config: ScenarioConfig, year: int
) -> list[StorageUnit]:
    """Build the storage fleet for a specific simulation year.

    Total power grows from ``STORAGE_DEPLOYMENT_MW`` base at the annual
    growth rate for the configured deployment pace. The grown total is
    capped at ``STORAGE_DEPLOYMENT_CEILING_MW`` to prevent runaway growth,
    then distributed across zones and techs as in ``build_default_storage``.

    Args:
        iso: ISO topology supplying the zones and their load shares.
        config: Scenario config supplying the ``storage_deployment`` pace.
        year: Simulation year; capacity compounds from :data:`START_YEAR`.

    Returns:
        One ``StorageUnit`` per (load zone, technology) pair with nonzero
        power capacity.

    Raises:
        ValueError: if ``config.storage_deployment`` is not a known pace.
    """
    pace = _resolve_pace(config)
    base_mw = STORAGE_DEPLOYMENT_MW[pace]
    growth_rate = STORAGE_GROWTH_RATE[pace]
    total_mw = base_mw * (1.0 + growth_rate) ** (year - START_YEAR)
    total_mw = min(total_mw, STORAGE_DEPLOYMENT_CEILING_MW)
    return _distribute_storage(iso, config, total_mw)
