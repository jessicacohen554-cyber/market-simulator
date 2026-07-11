# PJM capacity-market-auction-price (BRA clearing prices)

Drop the retrieved unified CSV here as **`pjm.csv`**. `area=RTO` for the
system-wide price (`area_type=rto`); zonal LDA rows use `area_type=lda`.
`auction_round=base_residual_auction` (default) or `incremental_auction`.

## Authoritative sources

- PJM BRA Report per delivery year: https://www.pjm.com/markets-and-operations/rpm/rpm-auction-user-info
- PJM capacity market results summary: https://www.pjm.com/markets-and-operations/rpm

Delivery years <= 2026/2027 only (see parent-datatype governance note).

**STATUS:** `pjm.csv` committed — RTO clearing prices for delivery years
2015/2016-2026/2027 (13 years) plus full per-LDA breakdowns for 2025/2026 and
2026/2027 (15-16 LDAs each) and a partial 2024/2025 LDA set (BGE/MAAC/SWMAAC/
EMAAC), all from the BRA Report Table 2/3 series. 2026/2027 and 2027/2028 (the
latter excluded here — beyond the delivery-year cutoff) both cleared exactly
at the price cap on a supply shortfall; every LDA cleared at the RTO price in
those years. See `docs/handoffs/capacity-market-intake-2026-07.md` for the
zonal history gap (2016/17-2023/24 LDA breakdowns not yet fetched).
