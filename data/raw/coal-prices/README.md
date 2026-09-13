# coal-prices — raw

Free, public-domain coal commodity price series collected to unblock the
coal-vs-gas passthrough sigmoid re-derivation (issue #1347, gap G-26). See
`docs/handoffs/coal-price-data-intake-2026-07.md` for the full intake memo and
`data/raw/reference/coal_region_crosswalk.csv` for the region -> ISO-plant map.

| File | Source | Regeneration |
|---|---|---|
| `eia_coal_market_sales_price.csv` | EIA Annual Coal Report, `coal/market-sales-price` route (region x market-type: captive/open-market/total, all coal ranks), EIA API v2 | `scripts/fetch_eia_coal_prices.py` |
| `eia_coal_price_by_rank.csv` | EIA Annual Coal Report, `coal/price-by-rank` route (region x coal rank: bituminous/subbituminous/lignite/anthracite/all), EIA API v2 | `scripts/fetch_eia_coal_prices.py` |
| `bls_coal_ppi.csv` | BLS Producer Price Index, series `WPU051` (commodity: Coal) + `PCU2121--2121--` (industry: Coal Mining, NAICS 2121), BLS Public Data API v2 | `scripts/fetch_bls_coal_ppi.py` |
| `SOURCES.md` | per-series provenance detail + licensing statement | — |
| `SOURCES_nwpp_coal.md` | **NWPP** (lane NWPP-12, 2026-09-13): no new series — the footprint's per-plant delivered coal price, its PRB / Green River / Uinta basin split measured off the committed EIA-923 receipts, the **measured absence** of any price for Colstrip and Centralia (26.7 % of footprint coal capacity), and the coal-exit instrument-vs-intention table | — (a provenance note; nothing regenerates) |

**On-disk layout note:** the two EIA CSVs are committed as numbered,
header-repeating parts (`eia_coal_market_sales_price.part0.csv`,
`.part1.csv`, ... and `eia_coal_price_by_rank.part0.csv`, ...) rather than
one file each — an artifact of this session's push tooling (the git-API
push path used here caps individual file-content size), not a change to the
data. `scripts/curate_coal_basin_price.py` reads the single-file name if
present, else concatenates the parts; both layouts are byte-identical once
joined. A future `fetch_eia_coal_prices.py` re-run writes a single file
again, which the curate script also reads fine.

**Coverage:** EIA ACR data spans 2001-2024 (annual, ~8-month publication
lag past calendar year-end — the 2025 ACR is not yet published as of this
intake). BLS PPI spans 2010-2026 (monthly, current). Both regenerate
automatically each publication cycle by re-running the fetch scripts — no
manual re-derivation needed.

**What this covers, and what it doesn't:**

- **Covers** every EIA-published producing region: Appalachia (Central /
  Northern / Southern), Illinois Basin, Powder River Basin, Uinta Basin,
  every individual coal-producing state (TX, ND, LA, MS, MT, WV split
  Northern/Southern, KY split East/West, ...), and every U.S. Census Bureau
  division aggregate (used as a fallback for states without a dedicated
  code — see `derive_coal_region_crosswalk.py`).
- **Does NOT cover** the daily basin spot indices (PRB 8800, Illinois
  Basin, NAPP, CAPP, Uinta) — those are S&P Global/Argus/McCloskey-licensed.
  **Even EIA's own current "Coal Markets" weekly report is licensed FROM
  S&P Global** ("With permission, S&P Global"; historical data "are
  proprietary" and "cannot be released by EIA" —
  <https://www.eia.gov/coal/markets/>). No free legacy pre-2023 weekly
  archive exists either — the report's own archive (`includes/archive2.cfm`)
  is the same S&P-sourced series, just older vintages of it. This is a
  confirmed, not assumed, gap.

**DATA NEEDED:** none for the ACR/PPI series above (both are complete for
their published coverage windows). If the daily basin spot indices are ever
licensed (a paid S&P/Argus/McCloskey subscription), they would land in a
*separate* raw directory (e.g. `coal-spot-daily/`) — never merged into this
one, so the free-vs-licensed provenance boundary stays visible on disk.

**Consumer:** none yet (collection + intake only this session, per rule 23 —
sigmoids re-derive only when source data updates, and that re-derivation,
and any resulting offer-curve change, is a separate per-ISO owner keeper
decision). Future consumer: a re-derivation of
`config.scenarios.COAL_SIGMOID_DEFAULTS` (see
`src/market_sim/data/coal.py` and `src/market_sim/data/fuel.py`).
