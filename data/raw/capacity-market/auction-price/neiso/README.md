# ISO-NE capacity-market-auction-price (FCA clearing prices)

Drop the retrieved unified CSV here as **`neiso.csv`**. Use `iso=NEISO`.
`area=SYSTEM` (`area_type=rto`) for the system-wide price; capacity-zone rows
use `area_type=capacity_zone`; the New Brunswick external tie uses
`area_type=import_interface`. `auction_round=forward_capacity_auction`.

## Authoritative sources

- ISO-NE FCA Results: https://www.iso-ne.com/markets-operations/markets/forward-capacity-market/fcm-participation
- ISO-NE FCA results press releases (per auction)

Delivery years <= 2026/2027 only.

**STATUS:** `neiso.csv` committed — FCA system-wide (and, where published,
zonal/interface) clearing prices for Capability Years 2016/2017-2026/2027 (FCA
7 through FCA 17), from ISO-NE's FCA results press releases and the
`key-stats/markets` clearing-price history table. FCA18's cleared price
($3.580/kW-month, CCP 2027/2028) was fetched but excluded — its delivery year
is beyond the 2026/27 cutoff. FCA1-FCA6 individual clearing prices were not
locatable (only an aggregated 2010-2016 range is published); see
`docs/handoffs/capacity-market-intake-2026-07.md`.
