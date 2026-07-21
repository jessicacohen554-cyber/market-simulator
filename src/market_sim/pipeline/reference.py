"""Calibration reference resolution (ex-``scripts/run_calibration.py``).

Orchestrator-unification lane, Stage-D reference half (refactor-consolidation
plan §5): the calibration reference — measured Henry Hub annual prices and
the rest of the ``calibration_reference.json`` benchmark inputs — was
resolved by private helpers in ``scripts/run_calibration.py``
(``_load_reference`` / ``_henry_hub_actual``), imported from there by
``run_calibration_full.py``, ``run_calibration_eia930.py``, and the
capture/replay tooling. Moved here verbatim; the script keeps permanent
same-name ``_``-prefixed aliases (its exported symbol names are a frozen
surface — 138 live importers).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from market_sim.config.paths import CALIBRATION_DIR, REPO_ROOT

logger = logging.getLogger(__name__)

__all__ = [
    "REFERENCE_PATH",
    "HENRY_HUB_FALLBACK",
    "load_reference",
    "henry_hub_actual",
]

REFERENCE_PATH: Path = CALIBRATION_DIR / "calibration_reference.json"

# Fallback measured Henry Hub annual averages ($/MMBtu) for backcast years
# when the calibration reference has not been built (EIA Henry Hub spot).
HENRY_HUB_FALLBACK: dict[int, float] = {
    2021: 3.72,
    2022: 6.45,
    2023: 2.54,
    2024: 2.19,
    2025: 3.52,
}


def load_reference() -> dict:
    """Return the calibration reference dict, or an empty dict if unbuilt."""
    if not REFERENCE_PATH.exists():
        logger.warning(
            "calibration reference %s not found — run "
            "build_calibration_reference.py first; using fallback gas prices",
            REFERENCE_PATH.relative_to(REPO_ROOT),
        )
        return {}
    return json.loads(REFERENCE_PATH.read_text())


def henry_hub_actual(reference: dict, year: int) -> float:
    """Return the measured Henry Hub price for ``year`` from the reference."""
    table = reference.get("henry_hub_actual", {})
    if str(year) in table:
        return float(table[str(year)])
    return HENRY_HUB_FALLBACK[year]
