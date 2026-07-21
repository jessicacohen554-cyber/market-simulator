"""CAISO zonal gas basis (delegates to the shared mean-zero core).

Split out of ``data/fuel.py`` (W-D3) as pure code motion. Rule 25: CAISO's
measured per-zone citygate rows live in ``caiso_zonal_gas_hub.csv`` and apply
only under ``config.caiso_zonal_gas_basis`` + ``config.iso == "CAISO"``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .meanzero import (
    CAISO_ZONAL_GAS_HUB_PATH,
    _apply_meanzero_zonal_gas_basis,
    _zonal_gas_basis_by_zone,
)


def caiso_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for CAISO, or None.

    Same format and semantics as :func:`pjm_zonal_gas_basis_by_zone` but reads
    :data:`CAISO_ZONAL_GAS_HUB_PATH` (NP15/ZP26 on PG&E Citygate, LA_BASIN/
    SDGE/SP15_rest on SoCal Citygate — measured weekly EIA NG Weekly prints,
    month-balanced).
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else CAISO_ZONAL_GAS_HUB_PATH, year
    )


def apply_caiso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each CAISO gas unit's price by its zone's measured citygate basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the shared
    capacity-weighted mean-zero core PJM/MISO use. NP15/ZP26 price off PG&E
    Citygate and LA_BASIN/SDGE/SP15_rest off SoCal Citygate (measured weekly
    prints, :data:`CAISO_ZONAL_GAS_HUB_PATH`), so the two halves of CAISO stop
    sharing one blended CA-composite gas price and the measured north-south
    marginal-cost gradient reaches the merit order; the fleet-aggregate gas
    level (the calibrated composite + transport) is preserved by the
    mean-zero anchor.

    Gated on ``config.caiso_zonal_gas_basis`` and ``config.iso == "CAISO"``
    (default-off; see the field docstring on ScenarioConfig), so every other
    ISO and every existing CAISO keeper replay is byte-identical. Mutates
    ``fuel_prices`` in place; idempotent given the same inputs.
    """
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="CAISO",
        config_field="caiso_zonal_gas_basis",
        hub_path=CAISO_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
    )
