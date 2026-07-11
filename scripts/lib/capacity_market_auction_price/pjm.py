"""PJM capacity-market-auction-price spec (reference ISO implementation).

PJM's Base Residual Auction (BRA) clears RTO-wide and per-LDA prices in
$/MW-day, published per delivery year in the BRA Report. Incremental
Auctions (IAs) clear separately and are recorded with
``auction_round=incremental_auction`` when the retrieval CSV distinguishes
them; the unified-CSV default (``base_residual_auction``) covers the BRA rows.
"""

from __future__ import annotations

from . import IsoSpec, register

SPEC = register(
    IsoSpec(
        iso="PJM",
        default_area_type="lda",
        default_auction_round="base_residual_auction",
    )
)
