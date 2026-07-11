"""NYISO capacity-market-auction-price spec.

NYISO's monthly Spot Market Auction clears ICAP prices ($/kW-month) for NYCA
and each locality (NYC, LI, G-J). ``area_type`` defaults to ``locality``; NYCA
system-wide rows use ``area_type=rto`` via an explicit CSV column (the default
only applies when the CSV leaves the cell blank, so NYCA rows must set it).
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="NYISO",
        default_area_type="locality",
        default_auction_round="spot",
    )
)
