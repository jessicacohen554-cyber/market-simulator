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

from market_sim.config.constants import STORAGE_TECHS
from market_sim.config.iso_configs import ISOConfig
from market_sim.config.scenarios import ScenarioConfig

# Total storage power capacity (MW) deployed across the fleet, by pace.
STORAGE_DEPLOYMENT_MW: dict[str, float] = {
    "low": 3_000.0,
    "mid": 8_000.0,
    "high": 20_000.0,
}

# Share of total deployed power allocated to each storage technology.
_TECH_POWER_SHARE: dict[str, float] = {
    "li_ion_4hr": 0.70,
    "li_ion_8hr": 0.25,
    "iron_air": 0.05,
}


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


def build_default_storage(
    iso: ISOConfig,
    config: ScenarioConfig,
) -> list[StorageUnit]:
    """Build a default storage fleet for an ISO and scenario.

    The total deployed power is set by ``config.storage_deployment`` (see
    ``STORAGE_DEPLOYMENT_MW``), split across load zones in proportion to each
    zone's ``load_share`` and across technologies by ``_TECH_POWER_SHARE``.
    Each technology's duration and round-trip efficiency come from
    ``constants.STORAGE_TECHS``; the round-trip efficiency is split evenly
    into one-way charge and discharge efficiencies.

    Args:
        iso: ISO topology supplying the zones and their load shares.
        config: Scenario config supplying the ``storage_deployment`` pace.

    Returns:
        One ``StorageUnit`` per (load zone, technology) pair with nonzero
        power capacity.

    Raises:
        ValueError: if ``config.storage_deployment`` is not a known pace.
    """
    pace = config.storage_deployment
    if pace not in STORAGE_DEPLOYMENT_MW:
        supported = ", ".join(sorted(STORAGE_DEPLOYMENT_MW))
        raise ValueError(
            f"Unknown storage_deployment '{pace}'. Supported: {supported}"
        )
    total_mw = STORAGE_DEPLOYMENT_MW[pace]

    units: list[StorageUnit] = []
    for z_idx, zone in enumerate(iso.zones):
        if zone.load_share <= 0.0:
            continue
        for tech_name, tech in STORAGE_TECHS.items():
            share = _TECH_POWER_SHARE.get(tech_name, 0.0)
            power_mw = total_mw * zone.load_share * share
            if power_mw <= 0.0:
                continue
            eta = float(tech["rte"]) ** 0.5
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
