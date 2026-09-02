"""MISO spec for the ``capacity-market-auction-supply`` datatype.

Source: MISO Planning Resource Auction (PRA) Results Postings — the
"Seasonal Supply Offered and Cleared Comparison Trend" category tables
(pp.22-25 of the PY2025-26 posting, which carries the PY2023-24 through
PY2025-26 trend) and each posting's seasonal "PRA Results by Zone"
System/subregion ledger rows. The unified CSV is hand-transcribed from the
sha256-recorded postings (see ``data/raw/miso-pra/SOURCES.md`` for the
identity records and re-fetch URLs); the generic
:func:`~scripts.lib.capacity_market_auction_supply.parse_unified_csv` reads it.
"""

from __future__ import annotations

from scripts.lib.capacity_market_auction_supply import IsoSpec, register

register(IsoSpec(iso="MISO"))
