"""Per-ISO base thermal offer-curve constants, selected by dict.

Refactor-consolidation plan §5 (orchestrator-unification lane, Stage E):
``backcast_config``'s per-band ``if iso == ...`` tuned ternaries (the base
``offer_curve_by_group`` construction) converted to per-ISO constant
modules — :mod:`.generic` (the else-branch values) overlaid by each ISO's
delta module (:mod:`.ercot`, :mod:`.pjm`) via :data:`BASE_OFFER_CURVE_DELTAS_BY_ISO`.
Values are byte-for-byte transplants (rules 23/25; parity-pinned by
``tests/test_offer_curve_base_parity.py`` against the frozen ternary
construction). Selection is the same case-sensitive comparison the
ternaries used (``iso == "ERCOT"`` / ``iso == "PJM"``): an unknown or
differently-cased ISO string gets the pure generic curve, exactly as the
else-branches did.

The per-ISO *merge* curves that deep-merge on top downstream
(``_PJM_OFFER_CURVE`` / ``_NYISO_OFFER_CURVE`` / …) are a separate, later
consolidation step and stay in ``backcast_config``.
"""

from __future__ import annotations

from market_sim.pipeline.offer_curve_base.ercot import ERCOT_BASE_OFFER_CURVE_DELTAS
from market_sim.pipeline.offer_curve_base.generic import GENERIC_BASE_OFFER_CURVE
from market_sim.pipeline.offer_curve_base.pjm import PJM_BASE_OFFER_CURVE_DELTAS

__all__ = [
    "GENERIC_BASE_OFFER_CURVE",
    "ERCOT_BASE_OFFER_CURVE_DELTAS",
    "PJM_BASE_OFFER_CURVE_DELTAS",
    "BASE_OFFER_CURVE_DELTAS_BY_ISO",
    "base_offer_curve_by_group",
]

BASE_OFFER_CURVE_DELTAS_BY_ISO: dict[str, dict[str, dict[str, float]]] = {
    "ERCOT": ERCOT_BASE_OFFER_CURVE_DELTAS,
    "PJM": PJM_BASE_OFFER_CURVE_DELTAS,
}


def base_offer_curve_by_group(iso: str) -> dict[str, dict[str, float]]:
    """Return the base ``offer_curve_by_group`` dict for ``iso``.

    A fresh nested copy of the generic curve with the ISO's tuned band
    deltas applied — value-identical to the former inline ternary dict for
    every ISO (parity-tested). Case-sensitive raw-``iso`` selection mirrors
    the ternaries' ``iso == "..."`` comparisons exactly.
    """
    curve = {group: dict(bands) for group, bands in GENERIC_BASE_OFFER_CURVE.items()}
    for group, bands in BASE_OFFER_CURVE_DELTAS_BY_ISO.get(iso, {}).items():
        curve[group].update(bands)
    return curve
