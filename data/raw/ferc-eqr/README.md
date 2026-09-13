# `ferc-eqr` — FERC Electric Quarterly Report transactions at SOCO delivery points

Opened **2026-09-13** by lane **SOCO-13** (`docs/multi-iso/soco-addition-plan-2026-09.md`
§5 row SOCO-13 / §8 W1; owner ruling card **S2**, both limbs). This is the raw store
behind the STOP-gated SOCO price benchmark: PRECOMMIT
`docs/handoffs/PRECOMMIT-soco-13-2026-09-13.md` (every filter, allocation rule and
threshold, fixed before any value was read; addendum A corrects the D3 anchor's
source before any index value existed) and FINDING
`docs/handoffs/FINDING-soco-13-2026-09-13.md` (every measured cell, the verdict).
Builder: `scripts/data/build_soco_eqr_price_index.py`. Exact URLs and host probes:
`SOURCES.md`. Checksums of every artifact, tracked or not: `SHA256SUMS.txt`.

**What the price IS:** the MWh-weighted price, per hour, of the short-term wholesale
energy that FERC-jurisdictional sellers reported delivering **inside the `SOCO`
balancing authority** — every EQR transaction row whose
`point_of_delivery_balancing_authority` is `SOCO` and whose product is `ENERGY`,
class `F`/`NF`, term `ST`, pricing increment `5`/`15`/`H`/`D`, not index- or
RTO-priced, in an energy unit, and not an intra-Southern transfer, with each
row's MWh spread uniformly over the clock hours it covers (rows spanning more than
25 h excluded). **What it is NOT:** an LMP (no market clears one), a day-ahead
price, or the price of all the footprint's energy (Southern's own cost-based
dispatch never transacts). Whether the traded slice is deep enough and prices the
region's marginal energy is what the gate measured — see the FINDING.

## 1. What is and is not tracked

| Artifact | Rows | Tracked? | What |
|---|---:|:--:|---|
| `eqr_soco_pod_transactions.parquet` | 981,070 | **yes** | every EQR transaction row with POD BA `SOCO`, 2023 Q1 → 2025 Q4, all 26 EQR fields as text plus `filing_member`, `quarter`, `salvaged` — the footprint's raw extract; everything below regenerates from it without a 43 GB re-fetch |
| `soco_eqr_hourly_utc.parquet` | 26,286 | **yes** | `hour_utc · mwh · n_rows · n_sellers · mwh_15min · price · thin` — the per-UTC-hour product after the PRECOMMIT §2–§4 filters; `price` NaN where the thin-hour rule says so |
| `seem_auditor_monthly_prices.csv` | 100 | **yes** | gate D3's anchor: the SEEM auditor's monthly clearing prices — `method=text` rows (2025, as printed in the monthly reports) and `method=digitised` rows (Peak / Off-Peak monthly weighted-average settlement price from the annual-report figures, §3), each with source, page, resolution and basis |
| `fuel_cost_anchor_monthly.csv` | 96 | **yes** | gate D4's anchor: EIA delivered gas AL / GA / MS ($/Mcf → $/MMBtu → F-class CC fuel cost $/MWh) |
| `filter_ledger.json` | — | **yes** | rows and MWh removed by each PRECOMMIT rule, seller concentration, MWh shares by rate type and increment |
| `gate.json` | — | **yes** | every measured cell of the PRECOMMIT §5 gate — **verdict `NO`** |
| `_pulls/` | ~44 GB transient | **no** | the 12 bulk quarterly zips (hashed, then deleted after extraction), `manifest_<quarter>.json` per quarter (zip sha256, byte length, filing and row counts, defective inner zips), the per-quarter `soco_pod_<quarter>.parquet` extracts, the SEEM PDFs, `bulk_links.json`, the allocated-rows intermediate |

## 2. The footprint and product filters, in one table (PRECOMMIT §2–§4)

| rule | admitted |
|---|---|
| footprint | `point_of_delivery_balancing_authority == SOCO` (the only spelling in use); rows whose BA is `MISO` / `TVA` / `HUB` but whose location string names SOCO are **not** admitted |
| product · class · term · increment | `ENERGY` · `F`, `NF` · `ST` · `5`, `15`, `H`, `D` (the **pricing** increment — a monthly-priced product itemised hourly is still monthly, and excluded) |
| rate type · units | not `Electric Index`, not `RTO/ISO` (gate G17: an index or an RTO settlement is a neighbouring market's price) · `$/MWH`, `$/KWH` |
| counterparties | any, except rows where seller **and** customer are both Southern Company subsidiaries |
| quantities | FERC's `standardized_quantity` (MWh) and `standardized_price` ($/MWh), both numeric, quantity > 0 |
| time | `YYYYMMDDHHMM` in the row's `time_zone` (`CP`/`EP`/`MP` prevailing; `CS`/`CD`/`ES`/`ED`/`PS` fixed) → UTC; `:59`/`:14`/`:29`/`:44` ends read +1 min; `end ≤ begin` reads one hour; MWh split uniformly over the covered clock hours; spans > 25 h excluded |
| thin hours | fewer than 2 source rows or < 20 MWh → NaN; never carried, never interpolated |
| clock (on landing) | the model's fixed non-leap 8760 on Central STANDARD time (`Etc/GMT+6`) through `derive_actual_lmp._std_hour_index` — the `SOCO` BA's EIA-930 clock (SOCO-10 gate G19) |

## 3. The SEEM anchor's digitisation

The auditor's monthly reports state a monthly clearing price in text only from
2025-01. The annual reports carry the same statistic — monthly weighted-average
settlement price, Peak and Off-Peak, with monthly max/min whiskers — as a figure
whose bars are a raster over a labelled axis. `fetch-seem` reads each bar's
height in pixels against the gridline spacing ($10 per gridline: 2024 and 2025
from the PDF's vector axis and text-layer tick labels, 2023 from the figure's
alpha-mask labels, verified by eye), at $0.09–0.14/MWh per pixel. Categories:
2023 figure = Jan 2023 → Apr 2024 (no Avg. bar); 2024 = Avg. + Jan → Dec 2024;
2025 = Avg. + Dec 2024 → Dec 2025. Where two figures carry the same month the
month's own-year report is used and the pair is reported (`gate.json`
`D3.shape.cross_report_overlap`). The `Avg.` bars are recorded and not used.

## 4. Reproduce

```
python scripts/data/build_soco_eqr_price_index.py links        # bulk URLs from the viewer
#   run _pulls/download_loop.sh (or fetch each CSV_<y>_Q<q>.zip into _pulls/)
python scripts/data/build_soco_eqr_price_index.py extract --wait
python scripts/data/build_soco_eqr_price_index.py fetch-seem
python scripts/data/build_soco_eqr_price_index.py build
python scripts/data/build_soco_eqr_price_index.py gate [--land]
```

A forward year regenerates from the same bulk files with no rule change (CLAUDE.md
rule 13 `[R-MEASURED]`'s forward test). `gate --land` writes
`data/raw/_validation-source/actual_lmp_hourly_SOCO.parquet` only when every gate
cell passes.
