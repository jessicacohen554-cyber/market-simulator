"""Facade: NEISO measured reserve-requirement loader (Limb A).

The implementation now lives in the unified spec-table module
:mod:`market_sim.data.reserve_requirements` (the single home for the
NYISO/NEISO/MISO measured reserve-requirement loaders, their per-ISO sources,
and the EXACT hard-error semantics). This module re-exports the NEISO surface
unchanged so the solve path keeps working: ``config.reserve_config._neiso_design``
imports the loader by name, and its monkeypatch tests target *this* module's
attribute (``market_sim.data.neiso_reserve_requirements.load_neiso_reserve_requirements``).

See :mod:`market_sim.data.reserve_requirements` for the full data contract
(the ISO-NE Express Hourly Reserve Requirements intake, the
``reserve-requirements`` clean datatype, and rule-13 admissibility).
"""

from __future__ import annotations

from market_sim.data.reserve_requirements import (
    FAMILY_BY_LOCATION_PRODUCT,
    load_neiso_reserve_requirements,
)

__all__ = [
    "FAMILY_BY_LOCATION_PRODUCT",
    "load_neiso_reserve_requirements",
]
