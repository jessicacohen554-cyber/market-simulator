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
| `weim_rtpd_lmp_15min.parquet` | see FINDING | **yes** | `interval_start_utc · baa · lmp · mce · mcc · mcl` — `PRC_RTPD_LMP` at the 12 nodes below, all four components, float32 |
| `weim_transfer_15min.parquet` | see FINDING | **yes** | `interval_start_utc · baa · xfer_mw` — `ENE_EIM_TRANSFER` (v2, RTPD) for all 23 WEIM BAAs |
| `weim_hourly_by_ba.parquet` | 3 × 8,760 × 12 | **yes** | `year · hour · baa · lmp` — the per-BA hourly LMP on the model's fixed-PST non-leap clock (PRECOMMIT §4). **The per-BA product**: card N5's zones are a re-group of this file |
| `midc_peak_daily.parquet` | 698 | **yes** | the `Mid C Peak` rows of EIA's ICE workbooks 2023–2025 (`single_day` flags delivery start = end) — the anchor, never the benchmark |
| `weim_benefits_appendix2_transfers.csv` | 4,922 | **yes** | Appendix 2 of the WEIM quarterly benefits reports, 2023-07 → 2025-12, per month × ordered BAA pair, 15-min and 5-min MWh, with `report` + `page` per row |
| `gate.json` | — | **yes** | every measured cell of the PRECOMMIT §5 gate |
| `_pulls/` | — | **no** | the raw OASIS CSV pulls, the ICE workbooks, the 12 benefits PDFs, the fetch logs/manifests and the UTC-hourly intermediates. Re-fetchable (`SOURCES.md`); hashes in `SHA256SUMS.txt` |

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
fetch time (see `_pulls/fetch_*_manifest.json` and the FINDING): **no data at or
before 2023-05-31; data from 2023-06-01** for both products. So **2023 is a partial
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
- `da` in the landed sidecar is **all NaN** — there was no day-ahead market.
