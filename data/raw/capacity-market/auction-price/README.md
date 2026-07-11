# capacity-market-auction-price (raw)

Published auction/spot capacity clearing-price history for each
capacity-market ISO, delivery years <= 2026/27 only (see the parent
`README.md` "Governance note"). A validation observable (CR-2 / T3.1) — never
a fit target.

## Layout

One subdirectory per ISO; each holds a single **unified CSV** named
`<iso>.csv` with exactly the canonical columns:

```
iso,delivery_year,season,area,area_type,auction_round,clearing_price,price_unit,cleared_mw,source_doc,source_page
```

`scripts/curate_capacity_market_auction_price.py` reads each subdir and writes
the clean partition `data/clean/capacity-market-auction-price/<ISO>/…parquet`.
`validate_tidy` (`scripts/lib/capacity_market_auction_price/__init__.py`)
rejects any row whose `delivery_year` starts after 2026 — a source that
publishes a later delivery year must not be added here yet.

- `season` ∈ {annual, summer, fall, winter, spring} — only MISO
  (PY2025-26+) and NYISO (where published by capability period) use
  non-annual seasons.
- `area_type` ∈ {lda, lrz, locality, capacity_zone, rto}.
- `auction_round` ∈ {base_residual_auction, incremental_auction, spot,
  forward_capacity_auction, planning_resource_auction, cpm_backstop}.
- `price_unit` ∈ {usd_per_mw_day, usd_per_kw_month, usd_per_kw_yr,
  usd_per_mw_yr} — record as published, do not convert.
- Leave a value cell blank rather than guess; a row needs at least one of
  `clearing_price` / `cleared_mw` or it is dropped at intake.

## Per-ISO status & sources

| ISO | subdir | auction | status |
|-----|--------|---------|--------|
| PJM | `pjm/` | Base Residual Auction (RTO + LDA) | see `pjm/README.md` |
| NYISO | `nyiso/` | monthly Spot Market Auction (NYCA + locality) | see `nyiso/README.md` |
| ISO-NE | `isone/` | Forward Capacity Auction | see `isone/README.md` |
| MISO | `miso/` | Planning Resource Auction (per LRZ, seasonal from PY2025-26) | see `miso/README.md` |
| CAISO | `caiso/` | none (bilateral RA) — expected empty | see `caiso/README.md` |
| ERCOT | — | — | **excluded** (energy-only, no capacity market) |
