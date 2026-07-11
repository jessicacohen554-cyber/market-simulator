"""ISO-NE capacity-market-auction-price spec.

ISO-NE's Forward Capacity Auction (FCA) clears a system-wide price and,
where a capacity zone separates, a zonal price, in $/kW-month. Uses the
``NEISO`` ISO label (matching ``config/iso_configs.py``), not "ISO-NE".
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NEISO",
        default_area_type="rto",
        default_auction_round="forward_capacity_auction",
    )
)
