# `soco-energy-auction`: Southern Company Energy Auction clearing prices, 2019–2025

Lane **soco-84** opened this store on 2026-09-28. **REPORTED-ONLY** (owner ruling 2026-09-28, decision card
"Yes, reported-only"). The series feeds **no gate, no scorer and no LP**. It is shown on the SOCO Calibration
Status panel beside Southern's FERC-714 system lambda (`frontend/data/backcast/reference/system_lambda.json`,
`scripts/data/derive_system_lambda_reference.py`). The soco-83 price search found this source.

**What it is.** Southern Company runs a voluntary hour-ahead and day-ahead energy auction. The operator publishes
one CSV per auction date and kind. The market is thin: it clears only in some hours (154–2,121 cleared hours per
year here). It is a spot check on Southern's marginal cost, not a price benchmark.

## Files

| Path | Count | What |
|---|---:|---|
| `hourly/YYYY-MM-DD_HOURLY_CLEARING_PRICES.CSV` | 1,082 | Hour-ahead auction. Columns `UTC_FLOW_HOUR, CPT_FLOW_HOUR, CPT_HOUR_END, PRICE, TLU`. One row per cleared flow hour. `UTC_FLOW_HOUR` is the hour's **beginning** in UTC; `CPT_*` is Central **prevailing** time. `PRICE` is $/MWh. 5,082 rows in total, with no duplicate UTC hours. |
| `daily/YYYY-MM-DD_DAILY_CLEARING_PRICES.CSV` | 43 | Day-ahead auction. Columns `CLEARING_DATE, FLOW_DATE, PRODUCT, HEATRATE, PRICE, TLU`. One row per cleared product (e.g. `Firm-LD`) and flow date. 47 rows; only 2022, 2024 and 2025 appear. |
| `links.csv` | 1,127 | Every in-window link on the index, with its HTTP status and byte count at fetch time. |
| `SHA256SUMS.txt` | — | Identity record for every CSV above. |

Files are byte-for-byte as downloaded. Nothing is edited.

## Source and how to re-fetch

- Index: `https://www.southerngeneration.com/auctionpub/index.html`
- Files: `https://www.southerngeneration.com/auctionpub/ClearingData/YYYY-MM-DD_{HOURLY,DAILY}_CLEARING_PRICES.CSV`
- File specification: `https://www.southerngeneration.com/auctionpub/FileSpecification.doc`
- Re-fetch: `python3 scripts/data/fetch_soco_energy_auction.py [--years 2019 ... 2025]`. It rewrites `hourly/`,
  `daily/`, `links.csv` and `SHA256SUMS.txt`.
- Fetched 2026-09-28. **1,127 links; 1,125 HTTP 200; 2 HTTP 404**: `2020-03-22_HOURLY` and `2020-03-30_HOURLY`.
  soco-83's earlier count the same day was 1,113 / 14 404s, so the server's availability moves; `links.csv` is the
  record of this fetch.

## Loader

`market_sim.data.soco_energy_auction.load_soco_energy_auction_hourly()` returns the hour-ahead price on a naive-UTC,
hour-beginning index, which is the FERC-714 lambda extract's clock. `load_soco_energy_auction_daily()` returns the
day-ahead records. The path constant is `config.paths.SOCO_ENERGY_AUCTION_DIR`.

## How it is compared

The panel compares the auction mean with the lambda **in the same cleared hours** only, and reports the hourly r.
A plain annual mean would compare different hours. Same-hour results for 2019–2025: auction $27.33 / 21.48 / 44.93 /
61.44 / 30.92 / 32.14 / 48.08 against lambda $25.40 / 20.32 / 47.26 / 59.41 / 31.70 / 34.67 / 45.08, with r
0.66–0.90.

DATA NEEDED: none for 2019–2025.
