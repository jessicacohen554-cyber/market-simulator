# coal-prices sources

## EIA Annual Coal Report (via EIA Open Data API v2)

- **Routes:** `coal/market-sales-price` (region x market-type: CAP/OM/TOT,
  all ranks), `coal/price-by-rank` (region x rank: BIT/SUB/LIG/ANT/TOT).
- **Coverage:** 2001-2024 annual, 52 producing regions/states each
  (Appalachia Central/Northern/Southern, Illinois Basin, Powder River Basin,
  Uinta Basin, every individual producing state, and Census-division
  aggregates for non-producing states).
- **Units:** `price_usd_per_ton` = $/short ton at the mine (f.o.b., excludes
  transportation); `sales_short_tons` (market-sales-price rows only).
- **API base:** `https://api.eia.gov/v2/coal/`. Docs:
  <https://www.eia.gov/opendata/documentation.php>. Free key:
  <https://www.eia.gov/opendata/register.php> (this repo's `.env` carries a
  committed free/rate-limited key per the existing `fetch-eia-gas-prices.yml`
  convention).
- **Pulled:** 2026-07-08 via `scripts/fetch_eia_coal_prices.py`.
- **License:** U.S. government work, public domain (17 U.S.C. §105); EIA's
  own Copyright & Reuse Policy explicitly permits redistribution. See
  `docs/data-licensing.md` §1.
- **NOT this source:** the EIA "Coal Markets" *weekly* report (daily basin
  spot indices for Central Appalachia / Northern Appalachia / Illinois
  Basin / Powder River Basin / Uinta Basin, $/ton and $/MMBtu). Verified via
  direct fetch of <https://www.eia.gov/coal/markets/> (2026-07-08): that page
  is licensed "With permission, S&P Global"; its historical data "are
  proprietary" and "cannot be released by EIA." Its archive
  (`includes/archive2.cfm`) is the same S&P-sourced series at older
  vintages — not a separate free source. **Not collected, per the task's
  explicit instruction not to buy or scrape S&P/Argus/McCloskey data.**

## BLS Producer Price Index

- **Series:** `WPU051` (PPI commodity "Coal", national, monthly),
  `PCU2121--2121--` (PPI industry "Coal Mining" NAICS 2121, national,
  monthly).
- **Coverage:** 2010-2026 (the unregistered API's per-request cap is a
  10-year span; the fetch script pages across overlapping windows).
- **Checked but not usable:** `WPU0512`, `WPU05130111/112/113`,
  `PCU212111212111`, `PCU212112212112` — none resolve (no BLS series exists
  broken out by coal rank or by state/region for this commodity/industry;
  the commodity and industry PPI programs are national-only for coal).
  `WPU0513` resolves but returns byte-identical values to `WPU051` over
  2015-2024 (not a distinct series) — dropped from the output.
- **API base:** `https://api.bls.gov/publicAPI/v2/timeseries/data/`. Docs:
  <https://www.bls.gov/developers/api_signature_v2.htm>. No registration key
  needed for the free/unregistered tier used here.
- **Pulled:** 2026-07-08 via `scripts/fetch_bls_coal_ppi.py`.
- **License:** U.S. government work, public domain (17 U.S.C. §105); BLS is
  a federal statistical agency, same statutory basis as EIA/EPA. See
  `docs/data-licensing.md` §1.

## No proprietary data used

**Explicit statement, per the intake task's requirement:** no S&P Global,
Argus, or McCloskey data (licensed or otherwise) was purchased, scraped, or
otherwise incorporated into this directory or its derived clean datatypes
(`coal-basin-price`, `coal-mining-ppi`). Every row in
`eia_coal_market_sales_price.csv`, `eia_coal_price_by_rank.csv`, and
`bls_coal_ppi.csv` traces to a U.S. federal government public-domain API
response, captured verbatim (rounded to the API's own reported precision) —
verified above by fetching EIA's own coal-markets page and confirming its
S&P Global license notice, and by confirming (not assuming) which BLS series
ids do and do not exist.
