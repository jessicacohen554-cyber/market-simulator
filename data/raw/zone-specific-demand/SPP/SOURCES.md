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

## Back years

2019–2022 and H1-2026 are a rule-22 **intake** batch, not part of this lane
(plan §6 row 15). The producer serves them from the same extracts
(`--years 2019 …`, which reach back to 2018-07-01); the *spend* — solving or
scoring an out-of-training year — stays gated by SPP's tier markers, which do
not exist.
