"""PJM spec for the ``capacity-market-auction-supply`` datatype.

Source: PJM RPM Base Residual Auction Results reports — the per-delivery-year
Demand Resource offered / cleared quantities in UCAP MW (the 2021/22–2023/24
reports' Demand Resources section + Table 3A, the 2024/25 report's Table 6
"Auction Results" trend rows, the 2025/26 report's Table 8 by resource type;
capx D48, 2026-09-04). The unified CSV is hand-transcribed from the
sha256-recorded reports (identity records and re-fetch URLs in
``data/raw/capacity-market/auction-supply/pjm/README.md``); the generic
:func:`~scripts.lib.capacity_market_auction_supply.parse_unified_csv` reads
it. ``planning_year`` carries PJM's own ``"YYYY/YYYY+1"`` delivery-year label
(the sibling ``demand-curve`` / ``auction-price`` convention); ``unit`` is
``mw_ucap`` (PJM's Unforced Capacity basis).
"""

from __future__ import annotations

from scripts.lib.capacity_market_auction_supply import IsoSpec, register

register(IsoSpec(iso="PJM"))
