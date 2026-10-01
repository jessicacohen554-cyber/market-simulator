# CAISO OASIS `PUB_RTM_GRP`: storage end-of-hour SOC bid bounds (compact extract)

Intake: R-CAISO-31 (2026-10-01). **Report-only diagnostic. Never a solve input** (rule 13: the bound is an
optional, participant-declared conduct parameter with no forward driver; R-CAISO-28 FINDING §1 point 4).

## What it is

`MINEOHSTATEOFCHARGE` / `MAXEOHSTATEOFCHARGE`: the ESDER 4 end-of-hour state-of-charge bid parameter
(FERC-approved May 2021). It is an optional, real-time-only hourly [min, max] MWh range a scheduling
coordinator may submit for a storage (NGR) resource (DMM 2024 Battery Special Report §2.2). It is empty in
every DAM row. Resource identity is masked (`RESOURCEBID_SEQ`, persistent across days).

## Files (all committed)

| file | grain | columns |
|---|---|---|
| `caiso_rtm_eoh_soc_<year>.parquet` | resource × bid hour carrying a bound | `trade_date`, `interval_start_utc`, `resourcebid_seq`, `sc_seq`, `min_eoh_soc_mwh`, `max_eoh_soc_mwh` |
| `caiso_rtm_storage_universe_<year>.parquet` | trade date × resource | `en_min_mw`, `en_max_mw`, `n_en_hours`, `is_storage_s1`, `submits_eoh` |
| `manifest_<year>.csv` | trade date | source zip name, bytes, sha256, CSV rows, counts |
| `SHA256SUMS.txt` | — | identity of the files above |

Years are Pacific trade-date years. The storage universe is the caiso-178 S1 test (an EN bid curve spanning
≤ −1 MW and ≥ +1 MW) plus any EOH submitter. The bound is constant across every product and segment row of a
resource-hour, and the extractor asserts this per day, so the reshape loses nothing for the two EOH fields.

**Dropped:** every bid-curve price and segment, AS bids, self-schedules, non-storage generators, interties
and participating loads. The full daily zips (~1.5 MB each, 1.7 GB for 2023–25) are gitignored under
`data/raw/caiso-public-bids/zips-rtm/` and can be re-fetched only while OASIS retains them.

## Coverage

| year | trade dates | EOH resource-hours | distinct submitters | submitters' share of storage MW |
|---|---|---|---|---|
| 2023 | 365 / 365 | 9,351 | 30 | 2.7 % |
| 2024 | 365 / 366 | 142,218 | 62 | 12.2 % |
| 2025 | 365 / 365 | 351,264 | 95 | 19.8 % |

The single missing date, **2024-07-03**, is an OASIS archive hole. The API returns `ERR_CODE 1000` "No data
returned" there. It is an RTM-only hole, and caiso-283 recorded the same one (`docs/records/caiso/RESULT-caiso283-rtm-flat-2026-09-16.md`).

## Retention: what is lost

The GroupZip bid archive rolls. **Measured 2026-10-01, the earliest RTM trade date served is 2021-09-01**
(2021-08-31 returns `ERR_CODE 1000`, settled). caiso-281 measured 2021-08-15 on 2026-09-14, so the boundary
moves about one day per calendar day (≈ 5 years + 1 month).

- **Lost since caiso-281:** 2021-08-15 to 2021-08-31.
- **Lost overall:** everything before 2021-09-01 (2020, and H1 2021 were already gone).
- **2023–25:** nothing lost. 2023-01-01 should age out around late 2027, so this extract becomes the only
  copy from then on.

GroupZip is asynchronous: the first request for a cold date returns `ERR_CODE 1015` ("in processing", member
`*_N.xml`, ~645 B), and only the next request gives the real answer. A single-shot probe must not read 1015 as
"dead" (caiso-281 2020 Q1 FINDING §2). The committed fetcher retries through it.

## Re-generate

```
python scripts/data/fetch_caiso_public_bids.py --market rtm --years 2023 2024 2025 --sleep 8
python scripts/data/extract_caiso_rtm_eoh_soc.py --years 2023 2024 2025
python scripts/data/curate_storage_soc_bounds.py          # -> data/clean/storage-soc-bounds/CAISO/
```

Three or more concurrent fetch streams draw HTTP 429s (155 retried in this intake), and throughput stays at
about 6 days per minute however many streams run. The `07Z`/`08Z` Pacific-boundary rule matters for
SingleZip windows (R-CAISO-30), not here: GroupZip returns the same Pacific trade day for a `T07` or `T08`
start (tested on 2024-07-10).
