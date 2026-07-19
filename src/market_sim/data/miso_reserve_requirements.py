"""Facade: MISO measured operating-reserve requirement loader (Lane-2, miso-56).

The implementation now lives in the unified spec-table module
:mod:`market_sim.data.reserve_requirements` (the single home for the
NYISO/NEISO/MISO measured reserve-requirement loaders, their per-ISO sources,
and the EXACT hard-error semantics). This module re-exports the MISO surface
unchanged so existing imports keep working: the solve path
(``config.reserve_config._miso_design`` imports the loader by name, and its
monkeypatch tests target *this* module's attribute) and the MISO attestation
scripts / tests (``_to_model_hour``, the region/zone constants).

See :mod:`market_sim.data.reserve_requirements` for the full data contract
(the MISO real-time ASM cleared-offers intake, the market-wide/South/Midwest
legs, and the documented basis caveats).
"""

from __future__ import annotations

from market_sim.data.reserve_requirements import (
    MIDWEST_REGIONS,
    MIDWEST_ZONE,
    MISO_AS_DIR,
    OR_PRODUCTS,
    SOUTH_REGION,
    SOUTH_ZONE,
    cleared_mw_path,
    load_miso_reserve_requirements,
)

# Private helpers re-exported for test imports (kept out of __all__).
from market_sim.data.reserve_requirements import (
    _MAX_MISSING_HOURS as _MAX_MISSING_HOURS,
)
from market_sim.data.reserve_requirements import _to_model_hour as _to_model_hour

__all__ = [
    "MIDWEST_REGIONS",
    "MIDWEST_ZONE",
    "MISO_AS_DIR",
    "OR_PRODUCTS",
    "SOUTH_REGION",
    "SOUTH_ZONE",
    "cleared_mw_path",
    "load_miso_reserve_requirements",
]
