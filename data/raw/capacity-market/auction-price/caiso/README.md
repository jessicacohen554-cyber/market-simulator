# CAISO capacity-market-auction-price (expected empty — no centralized auction)

CAISO procures Resource Adequacy bilaterally; there is no centralized capacity
auction to clear a price. This subdirectory is expected to stay empty unless a
CPM (Capacity Procurement Mechanism) backstop-procurement event clears at a
specific, published price for a specific year/area — if so, drop it here as
**`caiso.csv`** with `auction_round=cpm_backstop`.

## Authoritative sources (for any CPM backstop event)

- CAISO Capacity Procurement Mechanism designations: https://www.caiso.com/documents/ (search "CPM designation")

**STATUS:** `caiso.csv` committed — 5 individual CPM designation events (2023),
each clearing at the then-effective soft-offer cap ($6.31/kW-month), from the
CPUC 2023 RA Report Table 13. This confirms the "no centralized auction"
structural point directly: every CPM designation cleared at exactly the
regulatory price ceiling, not a price discovered through competing bids — a
qualitatively different mechanism from PJM/NYISO/ISO-NE/MISO's demand-curve
auctions. See the `capacity-market-demand-curve/caiso/` subdir for CAISO's
documented fixed-price proxy.
