# `nwpp-weim` — SOURCES

Every URL below was fetched successfully on **2026-09-13** by lane **NWPP-13**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §8 W1; PRECOMMIT
`docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md`). All three hosts are reachable
anonymously from a session. Checksums: `SHA256SUMS.txt`. Nothing in this
directory was written from memory; every number in a committed artifact came
through `scripts/data/build_nwpp_weim_price_index.py`.

## 1. CAISO OASIS (`oasis.caiso.com`) — the WEIM prices and transfer quantities

Endpoint: `https://oasis.caiso.com/oasisapi/SingleZip` (HTTP 200 anonymous;
strict rate limit — the builder waits ≥ 6 s between calls and backs off on 429;
**~39-month retention that slides one day per calendar day** — see README §3).

| product | query | notes |
|---|---|---|
| 15-minute market LMP at the default EIM load aggregation points | `queryname=PRC_RTPD_LMP&market_run_id=RTPD&version=1&node=<12 ELAP nodes, comma-separated>&startdatetime=<UTC>&enddatetime=<UTC>&resultformat=6` | one calendar month per call; 12 nodes × days × 96 intervals × 4 LMP components rows, checked per call |
| EIM transfer MW per BAA, 15-minute | `queryname=ENE_EIM_TRANSFER&version=2&market_run_id=RTPD&baa_grp_id=ALL&…` | all 23 WEIM BAAs stored; `version=1` and `version≥3` return `ERR 1001` (measured) |
| node catalogue (metadata, not committed) | `queryname=ATL_APNODE&APnode_type=ALL&version=1` | the `DEPZ` type is the default EIM LAP `ELAP_<BAA>-APND`; the node-set rule is PRECOMMIT §2 |

Datetime literal form: `YYYYMMDDTHH:MM-0000` (UTC).

## 2. EIA — ICE daily power indices (the Mid-C anchor)

`https://www.eia.gov/electricity/wholesale/xls/archive/ice_electric-<year>final.xlsx`
for 2023, 2024, 2025 (HTTP 200, 100,680 / 90,065 / 92,432 bytes). Sheet 1,
columns `Price hub · Trade date · Delivery start date · Delivery end date ·
High · Low · Wtd avg price $/MWh · Change · Daily volume MWh · Number of trades ·
Number of counterparties`. **Only the `Mid C Peak` rows are read**; the SP15,
NP15 and Palo Verde hubs in the same sheet are not read into any artifact
(plan §2.6, gate G17). EIA's page states the indices are physical firm power
contracts traded on ICE 06:00–11:00 CT on the day of publication.

## 3. CAISO / Western Energy Markets — WEIM quarterly benefits reports

`https://www.westerneim.com/documents/iso-western-energy-imbalance-market-benefits-report-q<q>-<year>.pdf`
for Q1-2023 … Q4-2025 (12 × HTTP 200). Appendix 2 ("WEIM Transfer Volume
(MWh)") lists per month and per ordered BAA pair the 15-minute and 5-minute
WEIM transfer volumes **with base-schedule transfers excluded**. Q1-2023 carries
no such appendix and Q2-2023 only a one-page summary, so the transcription
covers **2023-07 → 2025-12**; that gap is recorded, never padded.

## 4. EIA-930 (already committed — read, not fetched)

`data/raw/eia-930/EIA930_BALANCE_<year>_<half>.parquet`, column
`Demand (MW) (Adjusted)` for the 17 footprint BAs, UTC hour-beginning derived
from `UTC Time at End of Hour` − 1 h. The weighting series (PRECOMMIT §3).
