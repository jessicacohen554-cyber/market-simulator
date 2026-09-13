# `ferc-eqr` — SOURCES

Every URL below was fetched on **2026-09-13** by lane **SOCO-13**
(`docs/multi-iso/soco-addition-plan-2026-09.md` §8 W1; PRECOMMIT
`docs/handoffs/PRECOMMIT-soco-13-2026-09-13.md`, pushed at `ee32cf75` before any
value was read; addendum A at `535d87c5`). Checksums: `SHA256SUMS.txt`. Nothing in
this directory was written from memory; every number in a committed artifact came
through `scripts/data/build_soco_eqr_price_index.py`.

## 1. FERC EQR Report Viewer (`eqrreportviewer.ferc.gov`) — the transaction rows

The viewer is an ASP.NET WebForms application. Its *Downloads → Quarterly
Filings → All Companies* panel is rendered only after a postback that activates
the Downloads tab (`__EVENTTARGET=TabContainerReportViewer`,
`__EVENTARGUMENT=activeTabChanged:1`, the page's own hidden fields replayed);
`build_soco_eqr_price_index.py links` does that and writes `_pulls/bulk_links.json`
(52 quarters, 2013 Q3 → 2026 Q2, resolved 2026-09-13).

| what | URL grammar | measured 2026-09-13 |
|---|---|---|
| bulk quarterly CSV zip (all companies) | `https://eqrreportviewer.ferc.gov/DownloadRepositoryProd/<repository token>/BulkNew/CSV/CSV_<year>_Q<q>.zip` | HTTP 200 anonymous; `Accept-Ranges: bytes`; 3.29–3.94 GB per quarter 2023 Q1 → 2025 Q4; ~10 MB/s through this egress; the token is a 128-hex-character path segment read from the page (not assumed stable) |
| inside each bulk zip | 3,400–3,600 per-filing zips `CSV_<year>_Q<q>_<filing id>_<n>.ZIP`, each holding `<yyyymm>_<Seller>_{ident,contracts,transactions,indexPub}.CSV` | one inner zip per quarter or so is truncated by the filer (no end-of-central-directory record); its local headers are walked and the recoverable members inflated (`_salvage_members`), flagged in the quarter's manifest |
| `transactions.CSV` header (26 fields) | `transaction_unique_id, seller_company_name, customer_company_name, ferc_tariff_reference, contract_service_agreement, transaction_unique_identifier, transaction_begin_date, transaction_end_date, trade_date, exchange_brokerage_service, type_of_rate, time_zone, point_of_delivery_balancing_authority, point_of_delivery_specific_location, class_name, term_name, increment_name, increment_peaking_name, product_name, transaction_quantity, price, rate_units, standardized_quantity, standardized_price, total_transmission_charge, total_transaction_charge` | datetimes are `YYYYMMDDHHMM` wall-clock in the row's `time_zone` code |

Hosts that do **not** serve from this egress, recorded so nobody re-probes them:
`www.ferc.gov` / `ferc.gov` → HTTP 403 (WAF) on every path including the EQR data
dictionary PDF; `eqrds.ferc.gov` (the legacy EQR download host) → CONNECT tunnel
502 from the proxy; `data.ferc.gov` → reachable (200) but its data catalogue
carries no EQR dataset and its developer API is key-gated; `eqronline.ferc.gov`
and `eqrweb.ferc.gov` → filing portals (200), no public data. The
`EQRSubmissionFilingGuide.pdf` and `EQRLinks.pdf` on `eqronline.ferc.gov` were
read for host and mechanics only.

The bulk zips are **not committed** (43 GB across the 12 quarters; each is hashed
in `SHA256SUMS.txt` before deletion and its `Last-Modified` and byte length are
in `_pulls/manifest_<quarter>.json`). FERC republishes a quarter's bulk file when
a filer refiles — the `Last-Modified` dates seen ran from 2026-08-24 to
2026-09-13 — so a re-fetch may differ in rows; the committed
`eqr_soco_pod_transactions.parquet` is the durable record of what was read.

## 2. SEEM Independent Market Auditor (`southeastenergymarket.com`) — gate D3's anchor

`https://southeastenergymarket.com/auditor-reports/` (public, no login) lists the
monthly reports `wp-content/uploads/SEEM-Audit-Report-<yyyy>_<m>[-Final|-Rev|-Rev-RL|-Errata].pdf`
2022-11 → 2026-07 and the annual reports. Fetched (all HTTP 200):

| file | used for |
|---|---|
| the 39 monthly reports 2023-01 → 2025-12 (three November-2025 revisions and a May-2024 errata included) | the text sentence *"The average clearing price [in <month>] was $X/<unit>"* — present only from 2025-01 (page 6–7); transcribed as printed, unit as printed |
| `SEEM-Audit-Report-Annual-Rpt-2023FINAL.pdf` (p. 10, Figure 4), `SEEM-Audit-Report-Annual-2024-F.pdf` (p. 15, Figure 9), `SEEM-Audit-Report-Annual-2025-Final.pdf` (p. 9, Figure 5; the same file SOCO-12 committed under `soco-planning/`) | *Monthly Clearing Prices and Natural Gas Costs*: the monthly weighted-average settlement price, Peak and Off-Peak, digitised (README §3); the annual *"average price was about $30 / $23 / $32 per MWh for all segments"* sentences |

## 3. EIA delivered natural gas to electric power (the D4 fuel-cost anchor)

The committed `data/raw/gas-prices/eia_delivered_gas_{AL,GA,MS}_monthly_2023-2025.csv`
(lane SOCO-12, EIA `N3045<ST>3`, $/Mcf, key-free dnav route;
`gas-prices/SOURCES_soco_gas.md`). Alabama is complete through 2025-12; Georgia
and Mississippi stop at 2024-12 at source. Converted at
`market_sim.data.fuel.electric_power.MCF_TO_MMBTU = 1.036` and
`constants.HEAT_RATE_BINS["gas_cc"]["f_class"] = 6.7` MMBtu/MWh.

## 4. EIA-930 SOCO demand (the D2 denominator)

The committed `data/raw/eia-930-hourly/SOCO hourly.parquet` (`UTC time`, `Demand`;
lane SOCO-10's audited series, `docs/multi-iso/soco-data-audit.md` §3).
