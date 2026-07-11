"""MISO capacity-market-auction-price spec.

MISO's Planning Resource Auction (PRA) clears per Local Resource Zone (LRZ
1-10) in $/MW-day; annual through Planning Year 2024-25, seasonal
(summer/fall/winter/spring) from PY2025-26 onward.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="MISO",
        default_area_type="lrz",
        default_auction_round="planning_resource_auction",
    )
)
