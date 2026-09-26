"""PJM zonal gas basis (delegates to the shared mean-zero core).

Split out of ``data/fuel.py`` (W-D3) as pure code motion. Rule 25: PJM's
measured per-zone basis rows live in ``pjm_zonal_gas_hub.csv`` and apply only
under ``config.pjm_zonal_gas_basis`` + ``config.iso == "PJM"``.
"""

from __future__ import annotations

from pathlib import Path

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

import numpy as np

from .meanzero import (
    PJM_ZONAL_GAS_HUB_PATH,
    _apply_meanzero_zonal_gas_basis,
    _zonal_gas_basis_by_zone,
)


def pjm_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for PJM, or None.

    The raw measured per-zone basis (each PJM zone's primary-state EIA
    delivered-to-electric-power gas price minus Henry Hub;
    :data:`PJM_ZONAL_GAS_HUB_PATH`). The mean-zero re-centring that preserves the
    calibrated fleet-aggregate level is done in :func:`apply_pjm_zonal_gas_basis`,
    which weights by each zone's gas capacity. Returns ``None`` when the table is
    missing or has no rows for ``year`` (e.g. a forward year).
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else PJM_ZONAL_GAS_HUB_PATH, year
    )


def apply_pjm_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    skip_cells: np.ndarray | None = None,
) -> None:
    """Shift each PJM gas unit's price by its zone's measured regional gas basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the shared
    capacity-weighted mean-zero core that PJM and MISO both use. See that
    function's docstring for the mechanics.

    Gated on ``config.pjm_zonal_gas_basis`` and ``config.iso == "PJM"`` (a
    default-off diagnostic; see the field docstring on ScenarioConfig), so every
    other ISO and all forecasts are byte-identical. Mutates ``fuel_prices`` in
    place; idempotent given the same inputs.

    ``skip_cells`` (PJM-NEXT-2): the print-derived-cell mask returned by
    :func:`~..plant_prices.apply_plant_monthly_fuel_prices`. Honoured ONLY when
    ``config.pjm_zonal_gas_basis_skip_923_priced`` is set, so the flag-off
    behaviour is byte-identical whatever the caller passes. On masked cells the
    increment is not added (rule 19 ``[R-ONE-MECH]``: the EIA-923 print already
    carries the regional delivered premium); unmasked cells still receive it.
    """
    use_skip = skip_cells is not None and bool(
        getattr(config, "pjm_zonal_gas_basis_skip_923_priced", False)
    )
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="PJM",
        config_field="pjm_zonal_gas_basis",
        hub_path=PJM_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
        skip_cells=skip_cells if use_skip else None,
    )
