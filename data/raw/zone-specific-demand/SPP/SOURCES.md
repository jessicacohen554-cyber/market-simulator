# SPP sub-regional demand provenance

`spp_subba_demand_2023-2025.csv` — hourly metered demand (MWh) by SPP EIA-930
**sub-balancing-area**, the calibration window. Landed by lane SPP-11
(`docs/handoffs/FINDING-spp-11-2026-09-06.md`; charter
`docs/multi-iso/spp-addition-plan-2026-09.md` §2.5, §6 row 2).

Schema is the committed `zone-specific-demand/<ISO>/` convention, identical to
`MISO/miso_subba_demand_2023-2025.csv`:

    period, subba, subba-name, parent, value, value-units

## Source

EIA **Hourly Electric Grid Monitor**, six-month bulk extracts — key-free, no
registration:

    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2023_Jan_Jun.csv
    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2023_Jul_Dec.csv
    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2024_Jan_Jun.csv
    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2024_Jul_Dec.csv
    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2025_Jan_Jun.csv
    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2025_Jul_Dec.csv

Rows filtered to `Balancing Authority == SWPP`. Pulled **2026-09-06**.

This is the same product MISO's committed files carry; MISO's 2023-2025 file
came from the credentialled API v2 `electricity/rto/region-sub-ba-data` route,
which this environment has no `EIA_API_KEY` for. The bulk extracts publish the
identical series — verified on MISO by the producer's own 2019 regression (see
below) — so the key-free route is used here.

**Producer:**

    python scripts/data/fetch_eia930_subba_demand.py --iso SPP \
        --years 2023 2024 2025 --combine

`--combine` writes the one `<iso>_subba_demand_<first>-<last>.csv` this file is,
rather than one file per year. The MISO path through that script is unchanged:
re-running `--iso MISO --years 2019` after the SPP edits reproduces
`miso_subba_demand_2019.csv` byte-identically.

## Sub-BA display names — the vintage question

The six-month extract carries only the **code** (`Sub-Region`), never a display
name, so `subba-name` cannot be read off it. The names are taken verbatim from
EIA's own key-free EIA-930 reference table —

    https://www.eia.gov/electricity/930-api/sub_bas/data

— the `DESCRIPTION` field of every row whose `PARENT_BA_ID` is `SWPP` (pulled
2026-09-06). That is the table the Grid Monitor itself renders these names
from; none is guessed.

EIA renamed sub-BAs in 2026, and MISO's committed files therefore carry
era-specific names (`miso_subba_demand_2023-2025.csv` even switches vintage
mid-file: `Zone 1 - MISO` in 2023, `Zone 1` in the 2025 rows). SPP has **no**
committed file whose vintage a later intake would have to match, so this file
uses the current (2026-09-06) vintage for every row. `subba-name` is a label,
not a key — every consumer joins on `subba`.

## Clock

`period` is the **UTC hour-ending** stamp, written verbatim from the extract's
`UTC Time at End of Hour` column. This is the committed convention (established
and verified for MISO against the API overlay: 4,343/4,343 exact matches, see
`../MISO/SOURCES.md`). The extract's own `Local Time at End of Hour` column is
NOT used — it is stamped at a fixed offset year-round, which is neither the
API's convention nor SWPP's Central clock (`SWPP → America/Chicago`,
`scripts/data/fetch_eia930_hourly.py`).

`parent` is the EIA **balancing-authority code** `SWPP`, not the model's ISO
name `SPP` — the same rule MISO's files follow, where the two happen to
coincide.

## Coverage

**447,049 rows** = 17 sub-BAs × 26,297 contiguous hours,
`2023-01-01T07` .. `2025-12-31T23` (UTC), **zero interior gaps** and zero
duplicate `(period, subba)` keys.

The file starts at `T07` rather than `T00`: SWPP is UTC−6, so the first seven
UTC hour-ending stamps of 2023-01-01 are the evening of 2022-12-31 local and are
published in the **2022** `Jul_Dec` extract, outside this file's requested span.
The interior year boundaries (2024-01-01T00..06, 2025-01-01T00..06) *are*
carried — they come from the preceding year's `Jul_Dec` extract, which the
combined pull reads.

Per-year hour counts: 8,753 (2023) / 8,784 (2024) / 8,760 (2025).

**Reconciliation against the BA total** (`../../eia-930-hourly/SWPP hourly.parquet`,
column `Demand`, summed on the same UTC year):

| Year | BA `Demand` TWh | Σ 17 sub-BAs TWh | ratio |
|---|---|---|---|
| 2023 | 284.16 | 284.03 | 0.9995 |
| 2024 | 290.00 | 289.95 | 0.9998 |
| 2025 | 299.48 | 299.46 | 0.9999 |

The residual is the seven missing 2023 hours plus per-row integer rounding; the
17 sub-BAs are a complete partition of SWPP demand.

## The 17 SWPP sub-BAs, with annual energy

Zone-share evidence for the SPP-DESK's card P1 (2-zone vs 3-zone topology) and
the input `curate_zonal_shares.py` will group, exactly as
`_MISO_SUBBA_ZONE_GROUPS` does for MISO. **This file states no zone grouping** —
that is SPP-20's registration decision and SPP-32's curation.

| Sub-BA | Name | 2023 TWh | 2024 TWh | 2025 TWh | share of 3-yr total |
|---|---|---|---|---|---|
| `CSWS` | AEPW American Electric Power West | 48.50 | 48.34 | 49.99 | 16.81 % |
| `OKGE` | Oklahoma Gas and Electric Co. | 36.35 | 38.54 | 40.67 | 13.23 % |
| `SPS` | Southwestern Public Service Company | 35.54 | 36.70 | 37.74 | 12.59 % |
| `WAUE` | Western Area Power Upper Great Plains East | 34.78 | 35.47 | 35.52 | 12.11 % |
| `WR` | Westar Energy | 32.13 | 32.26 | 32.29 | 11.07 % |
| `NPPD` | Nebraska Public Power District | 17.97 | 18.26 | 19.07 | 6.33 % |
| `KCPL` | Kansas City Power & Light | 16.44 | 16.67 | 17.33 | 5.77 % |
| `OPPD` | Omaha Public Power District | 13.66 | 14.93 | 16.59 | 5.17 % |
| `WFEC` | Western Farmers Electric Cooperative | 10.14 | 10.01 | 9.98 | 3.45 % |
| `MPS` | KCP&L Greater Missouri Operations | 9.24 | 9.15 | 9.55 | 3.20 % |
| `GRDA` | Grand River Dam Authority | 7.25 | 7.64 | 8.38 | 2.66 % |
| `SECI` | Sunflower Electric | 6.01 | 6.09 | 6.36 | 2.11 % |
| `EDE` | Empire District Electric Company | 5.56 | 5.46 | 5.62 | 1.90 % |
| `LES` | Lincoln Electric System | 3.56 | 3.52 | 3.64 | 1.23 % |
| `SPRM` | City of Springfield | 3.40 | 3.41 | 3.41 | 1.17 % |
| `KACY` | Kansas City Board of Public Utilities | 2.49 | 2.47 | 2.33 | 0.83 % |
| `INDN` | Independence Power & Light | 1.03 | 1.02 | 1.02 | 0.35 % |
| | **SWPP total** | **284.03** | **289.95** | **299.46** | 100 % |

## Back years — 2019–2022 LANDED 2026-09-06 (SPP-15)

`spp_subba_demand_2019.csv` … `_2022.csv` — one file **per year**, mirroring
`MISO/miso_subba_demand_2019.csv … _2022.csv`. Landed by lane SPP-15
(`docs/handoffs/FINDING-spp-15-2026-09-06.md`; charter
`docs/multi-iso/spp-addition-plan-2026-09.md` §8 SPP-15, r#4 am.1; §6 row 15).

    python scripts/data/fetch_eia930_subba_demand.py --iso SPP \
        --years 2019 2020 2021 2022

No `--combine` — the per-year shape is the committed MISO back-file shape. Same
source (the `EIA930_SUBREGION_<year>_<half>.csv` six-month extracts, eight of
them, `Balancing Authority == SWPP`), same producer, unmodified; pulled
**2026-09-06**. **Naming vintage: all four files carry the current
(2026-09-06) vintage**, byte-identical `subba-name` values to
`spp_subba_demand_2023-2025.csv` on all 17 codes — the producer keys SPP's
names off one `SUBBA_NAMES["SPP"]` table for every year, which is correct here
because SPP has no era-specific committed file to match (see the vintage
section above). MISO's era split does not apply.

**Rule 22 `[R-HOLDOUT]`: this is DATA PREP, not a spend.** What is held out is
the *score*, never the data. Nothing here is solved, scored or registered; SPP
holds no tier marker and none is claimed.

| Year | rows | sub-BAs | first period (UTC hr-ending) | last period | hours | dup keys | interior gaps |
|---|---|---|---|---|---|---|---|
| 2019 | 147,169 | 17 | `2019-01-01T07` | `2019-12-31T23` | 8,657 | 0 | **96 h** (below) |
| 2020 | 149,209 | 17 | `2020-01-01T07` | `2020-12-31T23` | 8,777 | 0 | 0 |
| 2021 | 148,801 | 17 | `2021-01-01T07` | `2021-12-31T23` | 8,753 | 0 | 0 |
| 2022 | 148,801 | 17 | `2022-01-01T07` | `2022-12-31T23` | 8,753 | 0 | 0 |

**Reconciliation against the BA total** (`../../eia-930-hourly/SWPP hourly.parquet`,
column `Demand`, summed over the *same* UTC hours each file carries):

| Year | BA `Demand` TWh | Σ 17 sub-BAs TWh | ratio |
|---|---|---|---|
| 2019 | 266.284 | 266.284 | 1.000000 |
| 2020 | 261.847 | 261.847 | 1.000000 |
| 2021 | 267.338 | 267.339 | 1.000002 |
| 2022 | 282.302 | 282.419 | 1.000416 |

The 17 sub-BAs are a complete partition of SWPP demand in every back year, to
tighter than the 2023–2025 window's 0.9995–0.9999 (which is measured over the
whole calendar year, so it also carries that window's own missing hours).

### Two coverage facts a consumer must handle

1. **Every per-year file starts at `T07`, not `T00`** — the same span-boundary
   property the 2023–2025 file has at its own start, but here it recurs at
   *every* year boundary because these are per-year partitions. SWPP is UTC−6,
   so the seven UTC hour-ending stamps `<Y>-01-01T00..06` are the evening of
   `<Y-1>-12-31` local and are published in the **previous** year's `Jul_Dec`
   extract; the per-year period filter assigns them to neither file, so they
   are absent from this directory. (The producer's `--combine` path keeps
   interior boundaries — that is what it is for — but the committed MISO
   back-file shape is per-year, and this mirrors it.) 7 hours × 4 years = 28
   hours, 0.08 % of the span. A consumer stitching 2019→2022 into one series
   sees a 7-hour hole at each January 1; **do not interpolate it as an
   outage** — re-pull it with `--combine` if a contiguous series is needed.
2. **2019 has 96 hours EIA never published at sub-BA level**, in three blocks
   — `2019-06-12T06 .. 06-13T05`, `2019-06-14T06 .. 06-15T05`,
   `2019-06-19T06 .. 06-21T05` UTC (i.e. the local calendar days 2019-06-12,
   06-14 and 06-19/20 Central). The **BA-level** file carries all 96 of those
   hours (2.997 TWh of SWPP demand), so this is a sub-BA reporting gap in
   EIA's own product, not a fetch artifact. It is carried as absence, never
   filled (rule 14 `[R-ACCURATE]`). **Routed to SPP-32**: a zonal-share
   curation that divides by the sub-BA sum must handle those hours explicitly.

### The 17 SWPP sub-BAs, annual energy 2019–2022

Extends the 2023–2025 table above; **no zone grouping is asserted** (SPP-20's
registration, SPP-32's curation).

| Sub-BA | Name | 2019 TWh | 2020 TWh | 2021 TWh | 2022 TWh | share of 4-yr |
|---|---|---|---|---|---|---|
| `CSWS` | AEPW American Electric Power West | 47.89 | 45.77 | 46.34 | 49.02 | 17.54 % |
| `OKGE` | Oklahoma Gas and Electric Co. | 33.47 | 32.31 | 33.39 | 35.86 | 12.53 % |
| `SPS` | Southwestern Public Service Company | 33.49 | 33.34 | 31.99 | 33.89 | 12.31 % |
| `WR` | Westar Energy | 31.87 | 30.97 | 32.04 | 33.22 | 11.88 % |
| `WAUE` | Western Area Power Upper Great Plains East | 30.27 | 29.91 | 31.61 | 32.82 | 11.56 % |
| `NPPD` | Nebraska Public Power District | 16.15 | 16.94 | 17.43 | 18.66 | 6.42 % |
| `KCPL` | Kansas City Power & Light | 16.36 | 15.85 | 16.00 | 16.72 | 6.02 % |
| `OPPD` | Omaha Public Power District | 11.77 | 12.15 | 12.66 | 13.21 | 4.62 % |
| `WFEC` | Western Farmers Electric Cooperative | 9.24 | 9.06 | 9.23 | 10.18 | 3.50 % |
| `MPS` | KCP&L Greater Missouri Operations | 8.77 | 8.66 | 8.93 | 9.44 | 3.32 % |
| `GRDA` | Grand River Dam Authority | 5.83 | 6.29 | 6.71 | 7.17 | 2.41 % |
| `SECI` | Sunflower Electric | 5.72 | 5.55 | 5.65 | 6.00 | 2.13 % |
| `EDE` | Empire District Electric Company | 5.28 | 5.09 | 5.25 | 5.64 | 1.97 % |
| `LES` | Lincoln Electric System | 3.41 | 3.38 | 3.41 | 3.53 | 1.27 % |
| `SPRM` | City of Springfield | 3.29 | 3.19 | 3.27 | 3.45 | 1.22 % |
| `KACY` | Kansas City Board of Public Utilities | 2.44 | 2.33 | 2.37 | 2.55 | 0.90 % |
| `INDN` | Independence Power & Light | 1.04 | 1.05 | 1.06 | 1.06 | 0.39 % |
| | **SWPP total** | **266.28** | **261.85** | **267.34** | **282.42** | 100 % |

The rank order is stable against 2023–2025 with one swap: `WR` (Westar) sits
above `WAUE` in every back year and below it from 2023. `SPS` is 12.3 % of
demand across 2019–2022, essentially its 12.6 % share of 2023–2025 — the card
P1 load-side reading does not move on four more years of data.

### Still out of scope here

H1-2026 sub-BA demand is not landed by this lane (the producer serves it from
the 2026 extracts). The *spend* — solving or scoring an out-of-training year —
stays gated by SPP's tier markers, which do not exist.
