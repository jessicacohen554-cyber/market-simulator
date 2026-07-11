# NYISO capacity-market-auction-price (Spot Market Auction ICAP prices)

Drop the retrieved unified CSV here as **`nyiso.csv`**. `area` = NYCA/NYC/LI/
G-J; NYCA rows must set `area_type=rto` explicitly (default is `locality`).
`auction_round=spot`.

## Authoritative sources

- NYISO ICAP Market Reports (monthly spot auction summaries):
  https://www.nyiso.com/icap-mkt-actvts
- NYISO Load & Capacity Data ("Gold Book") capacity price tables:
  https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Final.pdf
- Potomac Economics NYISO State of the Market reports (capacity price
  tables): https://www.potomaceconomics.com/markets-monitored/nyiso/

Delivery years <= 2026/2027 only.

**STATUS:** `nyiso.csv` committed — annual-average spot ICAP prices for NYCA/
G-J/NYC/LI, Capability Years 2020/21-2025/26, transcribed from Potomac
Economics' NYISO State of the Market Report annual tables (Table 9/11/12/14
across report vintages). Monthly-granularity spot data exists on NYISO's ICAP
public portal but is behind an interactive form (not a static file) — logged
in `docs/handoffs/capacity-market-intake-2026-07.md`.
