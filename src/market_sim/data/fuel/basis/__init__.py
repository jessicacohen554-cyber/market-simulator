"""Per-ISO zonal gas-basis appliers behind the ZONAL_BASIS_APPLIERS registry.

Each ISO's measured zonal-basis machinery lives in its own module —
:mod:`.nyiso`, :mod:`.ercot`, :mod:`.pjm`, :mod:`.miso`, :mod:`.caiso` — with
the shared capacity-weighted mean-zero core in :mod:`.meanzero`. Rule 25
(CLAUDE.md): every tuned/fitted per-ISO value stays in its ISO's module and
data file; the registry carries NO generic default entry, and no ISO's basis
ever applies to another ISO (each applier self-gates on ``config.iso``).
NEISO is deliberately absent: its constrained-hub mechanism is the hub-basis
overlay (:func:`market_sim.data.fuel.hubs.apply_hub_basis_overlay`), not a
zonal-basis applier.

Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion, apart from the registry itself (new — consumed by
:mod:`market_sim.data.fuel.resolve` in :data:`ZONAL_BASIS_ORDER`, pinned by
``tests/test_fuel_facade.py``).
"""

from __future__ import annotations

from collections.abc import Callable

from .caiso import apply_caiso_zonal_gas_basis, caiso_zonal_gas_basis_by_zone
from .ercot import (
    ERCOT_BIN_ASSIGNMENTS_PATH,
    ERCOT_ELECTRIC_POWER_GAS_PATH,
    ERCOT_GAS_TAKEORPAY_PATH,
    ERCOT_ZONAL_GAS_HUB_PATH,
    apply_ercot_west_netload_gas_shape,
    apply_ercot_zonal_gas_basis,
    ercot_electric_power_gas_basis,
    ercot_electric_power_gas_basis_monthly,
    ercot_gas_spot_share_by_plant,
    ercot_gas_spot_share_by_zone,
    ercot_waha_collapse_freq,
    ercot_west_oversupply_collapse_freq,
    ercot_zonal_gas_basis_by_zone,
    ercot_zonal_gas_basis_source_group,
)
from .meanzero import (
    CAISO_ZONAL_GAS_HUB_PATH,
    MISO_ZONAL_GAS_HUB_PATH,
    PJM_ZONAL_GAS_HUB_PATH,
)
from .miso import (
    apply_miso_gas_marginal_commodity,
    apply_miso_winter_citygate_daily,
    apply_miso_winter_gas_daily_delivered,
    apply_miso_zonal_gas_basis,
    miso_chicago_daily_shape_factors,
    miso_zonal_gas_basis_by_zone,
)
from .nyiso import (
    NYISO_DOWNSTATE_CT_GAS_BASIS_PATH,
    NYISO_DOWNSTATE_CT_ZONES,
    NYISO_GAS_HUB_REFERENCE_ZONE,
    NYISO_ZONAL_GAS_HUB_PATH,
    TRANSCO_IROQUOIS_MONTHLY_PATH,
    apply_nyiso_downstate_ct_gas_basis,
    apply_nyiso_downstate_ct_gas_daily,
    apply_nyiso_ldc_generator_delivered_gas,
    ldc_generator_transport_monthly,
    eia860_plant_gas_ldc,
    apply_nyiso_zonal_gas_basis,
    nyiso_downstate_ct_gas_premium,
    nyiso_reconciled_reference_monthly,
    nyiso_zonal_gas_offsets,
    nyiso_zonal_gas_ratios_monthly,
)
from .pjm import apply_pjm_zonal_gas_basis, pjm_zonal_gas_basis_by_zone

# The application order resolve_fuel_prices walks. Identical mutation sequence
# to the pre-split call list for every ISO: each applier is a no-op unless
# config.iso matches its key, so relative order between DIFFERENT ISOs is
# behaviour-free; the one real constraint (MISO winter-citygate before the MISO
# zonal basis) is enforced in resolve_fuel_prices itself.
ZONAL_BASIS_ORDER: tuple[str, ...] = ("NYISO", "ERCOT", "PJM", "MISO", "CAISO")

# ISO -> its own zonal gas-basis applier (rule 25: no generic default entry;
# a tuned basis never crosses an ISO boundary — every applier also self-gates
# on config.iso and its own config flag).
ZONAL_BASIS_APPLIERS: dict[str, Callable[..., None]] = {
    "NYISO": apply_nyiso_zonal_gas_basis,
    "ERCOT": apply_ercot_zonal_gas_basis,
    "PJM": apply_pjm_zonal_gas_basis,
    "MISO": apply_miso_zonal_gas_basis,
    "CAISO": apply_caiso_zonal_gas_basis,
}

__all__ = [
    "CAISO_ZONAL_GAS_HUB_PATH",
    "ERCOT_BIN_ASSIGNMENTS_PATH",
    "ERCOT_ELECTRIC_POWER_GAS_PATH",
    "ERCOT_GAS_TAKEORPAY_PATH",
    "ERCOT_ZONAL_GAS_HUB_PATH",
    "MISO_ZONAL_GAS_HUB_PATH",
    "NYISO_DOWNSTATE_CT_GAS_BASIS_PATH",
    "NYISO_DOWNSTATE_CT_ZONES",
    "NYISO_GAS_HUB_REFERENCE_ZONE",
    "NYISO_ZONAL_GAS_HUB_PATH",
    "PJM_ZONAL_GAS_HUB_PATH",
    "TRANSCO_IROQUOIS_MONTHLY_PATH",
    "ZONAL_BASIS_APPLIERS",
    "ZONAL_BASIS_ORDER",
    "apply_caiso_zonal_gas_basis",
    "apply_ercot_west_netload_gas_shape",
    "apply_ercot_zonal_gas_basis",
    "apply_miso_gas_marginal_commodity",
    "apply_miso_winter_citygate_daily",
    "apply_miso_winter_gas_daily_delivered",
    "apply_miso_zonal_gas_basis",
    "apply_nyiso_downstate_ct_gas_basis",
    "apply_nyiso_downstate_ct_gas_daily",
    "apply_nyiso_ldc_generator_delivered_gas",
    "ldc_generator_transport_monthly",
    "eia860_plant_gas_ldc",
    "apply_nyiso_zonal_gas_basis",
    "apply_pjm_zonal_gas_basis",
    "caiso_zonal_gas_basis_by_zone",
    "ercot_electric_power_gas_basis",
    "ercot_electric_power_gas_basis_monthly",
    "ercot_gas_spot_share_by_plant",
    "ercot_gas_spot_share_by_zone",
    "ercot_waha_collapse_freq",
    "ercot_west_oversupply_collapse_freq",
    "ercot_zonal_gas_basis_by_zone",
    "ercot_zonal_gas_basis_source_group",
    "miso_chicago_daily_shape_factors",
    "miso_zonal_gas_basis_by_zone",
    "nyiso_downstate_ct_gas_premium",
    "nyiso_reconciled_reference_monthly",
    "nyiso_zonal_gas_offsets",
    "nyiso_zonal_gas_ratios_monthly",
    "pjm_zonal_gas_basis_by_zone",
]
