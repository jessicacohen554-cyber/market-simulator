# PJM-AS — raw

PJM ancillary-services market data and reference manuals:

- `reserve_market_results_<year>.parquet` / `da_reserve_market_results_<year>.parquet`
  — PJM DataMiner2 "Ancillary Services Market Results — Reserve Market
  Results" (RT / DA), 2023–2025.
- `ancillary_services_<year>.parquet` / `da_ancillary_services_<year>.parquet`
  — PJM's long/tall AS product-price feed (product in `ancillary_service`,
  price in `value`).
- `pjm_<year>_as_up_mw.parquet` — derived AS-withholding MW series (see
  below).
- `m11.pdf`, `m11v127-*.pdf`, `m11v129-*.pdf` — PJM Manual 11 (Energy &
  Ancillary Services Market Operations) revisions.
- `shortage-pricing-fact-sheet.pdf`, `E-3-052120.pdf` — PJM reference/
  methodology documents. Not read by any script — background only.

**Source:** PJM DataMiner2 (`dataminer2.pjm.com`).

**Regeneration: hand-assembled — no fetch script for the raw DataMiner2
parquets in this checkout.** The `reserve_market_results_*` /
`da_reserve_market_results_*` / `ancillary_services_*` /
`da_ancillary_services_*` parquets were pulled manually from DataMiner2; no
`fetch_*.py` script produces them. `pjm_<year>_as_up_mw.parquet` **is**
regenerable — `scripts/build_pjm_as_withholding.py` derives it from the
`reserve_market_results_<year>.parquet` files already on disk.

**Known bug in a consumer.** `scripts/derive_pjm_ordc_overlay.py` (which
reads `reserve_market_results_{year}.parquet` / `da_reserve_market_results_{year}.parquet`)
still points its `RAW_DIR` at the pre-relocation path
`inputs/raw-data/PJM-AS` rather than `data/raw/PJM-AS` — fix before relying
on it to find these files.

**Licensing note:** PJM DataMiner2 data carries redistribution conditions —
see `docs/data-licensing.md` §4.

**Consumers:** `scripts/curate_ancillary_services.py`,
`scripts/build_pjm_as_withholding.py`, `scripts/derive_pjm_ordc_overlay.py`.
