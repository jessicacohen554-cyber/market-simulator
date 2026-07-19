"""ERCOT transmission-expansion spec.

Binding instruments: PUCT orders adopting the Permian Basin Reliability Plan
(and its 765 kV backbone election) plus ERCOT board / RPG-endorsed Tier 1
projects with committed sponsors. Public sources to re-query: PUCT interchange
(Docket 55718 lineage), ERCOT RPG project tracking / Transmission Project
Information Tracking (TPIT). Base statics are the measured 2023-24 GTC limits
(WESTEX/PNHNDL/NE_LOB) plus the Tier-3 interior estimates, so only work
in-service after :data:`~market_sim.data.transmission_expansion
.TRANSMISSION_BASE_STATIC_VINTAGE` ("ERCOT") is additive.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="ERCOT",
        source_note=(
            "PUCT Permian Basin Reliability Plan orders + ERCOT 765 kV "
            "backbone election; ERCOT RPG/TPIT project tracking."
        ),
    )
)
