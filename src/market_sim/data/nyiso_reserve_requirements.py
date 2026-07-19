"""Facade: NYISO measured reserve-requirement loader.

The implementation now lives in the unified spec-table module
:mod:`market_sim.data.reserve_requirements` (the single home for the
NYISO/NEISO/MISO measured reserve-requirement loaders, their per-ISO sources,
and the EXACT hard-error semantics). This module re-exports the NYISO surface
unchanged so existing imports keep working: the solve path
(``config.reserve_config._nyiso_design`` imports the loader by name, and its
monkeypatch tests target *this* module's attribute) and
``scripts/data/derive_nyiso_reserve_requirements_hourly.py``
(``FAMILY_BY_REGION_PRODUCT`` + ``NYISO_RESERVE_REQUIREMENTS_DIR``).

See :mod:`market_sim.data.reserve_requirements` for the full data contract
(the NYISO issue-#1344 Ask-B intake, rule-13 admissibility, and the
measured-series conventions).
"""

from __future__ import annotations

from market_sim.data.reserve_requirements import (
    FAMILY_BY_REGION_PRODUCT,
    NYISO_RESERVE_REQUIREMENTS_DIR,
    load_nyiso_reserve_requirements,
    requirements_path,
)

__all__ = [
    "FAMILY_BY_REGION_PRODUCT",
    "NYISO_RESERVE_REQUIREMENTS_DIR",
    "load_nyiso_reserve_requirements",
    "requirements_path",
]
