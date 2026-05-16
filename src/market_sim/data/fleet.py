"""Generation fleet inventory and attributes."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel

# Integer codes for fuel types, used to index into fuel-keyed arrays.
FUEL_TYPE_MAP: dict[str, int] = {
    "gas_cc": 0,
    "gas_ct": 1,
    "coal": 2,
    "nuclear": 3,
    "wind": 4,
    "solar": 5,
    "hydro": 6,
    "import": 7,
}


class Generator(BaseModel):
    """Attributes of a single generating unit."""

    unit_id: str
    name: str
    zone: str
    fuel_type: str
    efficiency_bin: str = "default"
    pmax_mw: float
    pmin_mw: float = 0.0
    heat_rate: float = 0.0
    vom: float = 0.0
    emission_rate_co2: float = 0.0
    nox_rate: float = 0.0
    eford: float = 0.05
    online_year: int = 2000
    retirement_year: int | None = None
    is_must_run: bool = False


@dataclass
class FleetArrays:
    """Vectorized fleet attributes for dispatch computation.

    Per-generator scalar attributes are stored as ``(n_gen,)`` arrays;
    availability is stored as ``(n_gen, T)`` to allow hour-varying derates.
    """

    pmax: np.ndarray
    pmin: np.ndarray
    heat_rate: np.ndarray
    vom: np.ndarray
    emission_rate: np.ndarray
    nox_rate: np.ndarray
    zone_idx: np.ndarray
    fuel_type_idx: np.ndarray
    availability: np.ndarray
    unit_ids: list[str]

    @property
    def n_gen(self) -> int:
        """Return the number of generators in the fleet."""
        return len(self.unit_ids)


def generators_to_fleet_arrays(
    generators: list[Generator],
    zone_names: list[str],
    hours: int = 8760,
) -> FleetArrays:
    """Convert a list of generators into vectorized ``FleetArrays``.

    Availability is set to ``1 - eford`` for every hour; seasonal and
    maintenance derate factors are applied later in the pipeline.
    """
    zone_to_idx = {name: i for i, name in enumerate(zone_names)}

    n_gen = len(generators)
    pmax = np.array([g.pmax_mw for g in generators], dtype=float)
    pmin = np.array([g.pmin_mw for g in generators], dtype=float)
    heat_rate = np.array([g.heat_rate for g in generators], dtype=float)
    vom = np.array([g.vom for g in generators], dtype=float)
    emission_rate = np.array([g.emission_rate_co2 for g in generators], dtype=float)
    nox_rate = np.array([g.nox_rate for g in generators], dtype=float)
    zone_idx = np.array([zone_to_idx[g.zone] for g in generators], dtype=int)
    fuel_type_idx = np.array(
        [FUEL_TYPE_MAP[g.fuel_type] for g in generators], dtype=int
    )

    eford = np.array([g.eford for g in generators], dtype=float)
    availability = np.broadcast_to(
        (1.0 - eford)[:, np.newaxis], (n_gen, hours)
    ).copy()

    return FleetArrays(
        pmax=pmax,
        pmin=pmin,
        heat_rate=heat_rate,
        vom=vom,
        emission_rate=emission_rate,
        nox_rate=nox_rate,
        zone_idx=zone_idx,
        fuel_type_idx=fuel_type_idx,
        availability=availability,
        unit_ids=[g.unit_id for g in generators],
    )
