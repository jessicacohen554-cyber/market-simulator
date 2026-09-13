# `nwpp-weim` — CAISO WEIM prices and transfer quantities for the NWPP footprint

Opened **2026-09-13** by lane **NWPP-13** (`docs/multi-iso/nwpp-addition-plan-2026-09.md`
§5 row NWPP-13 / §8 W1; owner ruling card **N2**, both limbs). This is the raw store
behind the STOP-gated NWPP price benchmark: PRECOMMIT
`docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md` (every rule and threshold, fixed
before any value was read) and FINDING `docs/handoffs/FINDING-nwpp-13-2026-09-13.md`
(every measured cell, the verdict). Builder:
`scripts/data/build_nwpp_weim_price_index.py`. Exact URLs: `SOURCES.md`.
Checksums of every artifact, tracked or not: `SHA256SUMS.txt`.

**What the price IS:** the Western Energy Imbalance Market's 15-minute LMP at each
participating BAA's default EIM load aggregation point (`ELAP_<BAA>-APND`, OASIS
apnode type `DEPZ`), i.e. the price at which that BAA's real-time load imbalance
settles. **What it is NOT:** a day-ahead price (none existed in 2023–2025), or the
price of all the footprint's energy (base schedules are bilateral). Whether that
gap is a misalignment is what the gate measures — see the FINDING.

## 1. What is and is not tracked

| Artifact | Rows | Tracked? | What |
|---|---:|:--:|---|
| `weim_rtpd_lmp_15min.parquet` | 1,088,688 | **yes** | `interval_start_utc · baa · lmp · mce · mcc · mcl` — `PRC_RTPD_LMP` at the 12 nodes below, all four components, float32 |
| `weim_transfer_15min.parquet` | 2,083,676 | **yes** | `interval_start_utc · baa · xfer_mw` — `ENE_EIM_TRANSFER` (v2, RTPD) for all 23 WEIM BAAs |
| `weim_hourly_by_ba.parquet` | 315,360 | **yes** | `year · hour · baa · lmp` — the per-BA hourly LMP on the model's fixed-PST non-leap clock (PRECOMMIT §4). **The per-BA product**: card N5's zones are a re-group of this file |
| `midc_peak_daily.parquet` | 698 | **yes** | the `Mid C Peak` rows of EIA's ICE workbooks 2023–2025 (`single_day` flags delivery start = end) — the anchor, never the benchmark |
| `weim_benefits_appendix2_transfers.csv` | 4,922 | **yes** | Appendix 2 of the WEIM quarterly benefits reports, 2023-07 → 2025-12, per month × ordered BAA pair, 15-min and 5-min MWh, with `report` + `page` per row |
| `gate.json` | — | **yes** | every measured cell of the PRECOMMIT §5 gate — **verdict `NO`** (D3: the WEIM on-peak price sits 22.6–37.5 % below the Mid-C Peak index against a 10 % bar; D1, D2, D4 pass) |
| `d2_tie_reconciliation.json` | — | **yes** | one month (2024-07) of tie-level transfers establishing that `ENE_EIM_TRANSFER` is the BAA's NET position and Appendix 2 the pairwise GROSS (gross identity 1.046, net identity 0.985) |
| `_pulls/` | 916 MB | **no** | the raw OASIS CSV pulls (31 + 31 monthly windows), the ICE workbooks, the 12 benefits PDFs, the tie-level month, the fetch logs/manifests and the UTC-hourly intermediates. Re-fetchable (`SOURCES.md`) inside retention; hashes in `SHA256SUMS.txt` |

The untracked payload follows the repo's convention for raw exports (the ERCOT /
NYISO / SPP LMP source zips are likewise not committed): **the reduced parquet is
the durable record.** That matters more here than elsewhere — see §3.

## 2. The node set (PRECOMMIT §2) — 12 `DEPZ` nodes, constant over the window

| BA | node | effective | 2024 load share | BA | node | effective | 2024 load share |
|---|---|---|---:|---|---|---|---:|
| BPAT | `ELAP_BPAT-APND` | 2022-05-03 | 20.26 % | IPCO | `ELAP_IPCO-APND` | 2018-04-04 | 6.43 % |
| PACE | `ELAP_PACE-APND` | 2014-10-15 | 18.10 % | AVA | `ELAP_AVA-APND` | 2022-03-02 | 4.44 % |
| NEVP | `ELAP_NEVP-APND` | 2015-12-01 | 14.11 % | NWMT | `ELAP_NWMT-APND` | 2021-06-16 | 4.18 % |
| PSEI | `ELAP_PSEI-APND` | 2016-10-01 | 8.53 % | SCL | `ELAP_SCL-APND` | 2020-04-01 | 3.23 % |
| PGE | `ELAP_PGE-APND` | 2017-10-01 | 7.79 % | TPWR | `ELAP_TPWR-APND` | 2022-03-02 | 1.56 % |
| PACW | `ELAP_PACW-APND` | 2014-10-15 | 7.30 % | AVRN | `ELAP_AVRN-APND` | 2023-04-05 | 0 (generation-only) |

Priced load = 95.93 % of the 2024 footprint. **Unpriced** (WEIM non-participants,
no published price — probed): CHPD 0.68 % · DOPD 0.82 % · GCPD 2.29 % · WAUW 0.28 %.
`EIMT` transfer nodes and the `CASP` `CGAP_*_MIDC` CAISO scheduling points are
deliberately not used (PRECOMMIT §2; plan §2.6 gate G17).

## 3. Retention — why the parquet is the record

OASIS serves ~39 months and the edge slides one day per calendar day. Measured at
fetch time 2026-09-13 (`_pulls/fetch_*_manifest.json`): **no data at or
before 2023-05-31; data from 2023-06-01** for both products — every one of the
31 monthly LMP windows returned exactly its expected row count. So **2023 is a partial
year by retention (Jun 1 – Dec 31 at most)**, declared in the PRECOMMIT before the
fetch, and an anonymous re-fetch a year from now will not reproduce it at all. A
forward year regenerates from the same query (CLAUDE.md rule 13's forward test);
a backcast re-run beyond retention reads these parquets. Never "re-fetch to
refresh" the committed years — that would silently shorten them.

## 4. Conventions

- **Clock.** `weim_hourly_by_ba.parquet` and the landed sidecar are on the model's
  fixed non-leap 8760-hour clock in Pacific **standard** time (`Etc/GMT+8`, the
  CAISO sidecar's `derive_actual_lmp._STD_TZ` convention; Feb 29 dropped). The
  15-minute stores keep the **UTC instant**, so any other canonical hour (card N6)
  is a re-index of committed bytes.
- **Hour = simple mean of the 4 settlement intervals**; fewer than 3 → NaN. Nothing
  is carried or interpolated.
- **Footprint price = demand-weighted mean** over the 11 load-carrying priced BAs,
  weights EIA-930 `Demand (MW) (Adjusted)`; an hour whose priced BAs carry < 90 % of
  the 11-BA demand is NaN.
- `da` in a landed sidecar would be **all NaN** — there was no day-ahead market.
  **No sidecar was landed** (the gate read `NO`); `gate --land` refuses unless every
  cell passes, and a desk ruling to use the series as a labelled imbalance-price
  benchmark would be a new owner decision, not a re-run of this gate.
- The published LMP does not equal `MCE + MCC + MCL` in 56.5 % of intervals
  (p99 of the gap $27/MWh, max $175) — the index uses the published `LMP_PRC`
  (the settlement price) as the PRECOMMIT declares; the components are stored
  and the identity is reported, not assumed.
