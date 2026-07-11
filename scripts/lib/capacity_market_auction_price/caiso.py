"""CAISO capacity-market-auction-price spec.

CAISO has no centralized capacity auction (bilateral Resource Adequacy
procurement) — this ISO is expected to contribute an empty (or near-empty)
partition. Registered for completeness and to record any CPM backstop
procurement event that does clear at a specific price, per the raw README.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="CAISO",
        default_area_type="rto",
        default_auction_round="cpm_backstop",
    )
)
