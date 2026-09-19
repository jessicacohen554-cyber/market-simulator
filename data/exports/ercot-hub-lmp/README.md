# `data/exports/ercot-hub-lmp` — ERCOT hub price CSV cuts

Human-facing CSV extracts of a single ERCOT settlement point's real-time
Settlement Point Prices, produced on request so the exact bytes handed to a
reader are on the record.

**These are hand-off artifacts, not model inputs.** Nothing under
`src/market_sim/` reads this tree and no curator writes it. The model's own
ERCOT price series is `data/raw/_validation-source/actual_lmp_zonal_ERCOT.parquet`,
built from the same archives by `scripts/data/derive_ercot_zonal_lmp.py`.

| | |
|---|---|
| Source | `data/raw/lmp-data/RTMLZHBSPP_{2023,2024,2025}.zip` — ERCOT MIS LZ/HB/SPP real-time archive, one `.xlsx` per year, 12 monthly sheets, manual download |
| Regeneration | `python3 scripts/data/derive_ercot_hub_rt_lmp_csv.py --settlement-point HB_NORTH --years 2023 2024 2025` |
| Units | $/MWh |
| Clock | Central Prevailing Time, interval- and hour-**ending**, as ERCOT publishes |

## Current contents

`HB_NORTH` — the ERCOT North hub, quoted as "ERCOTN" in the trade press.
`LZ_NORTH` is the North *load zone* and a different settlement point; it is
not in this export.

| File | Rows |
|---|---|
| `ERCOT_HB_NORTH_rt_15min_{2023,2024,2025}.csv` | 35,040 / 35,136 / 35,040 |
| `ERCOT_HB_NORTH_rt_hourly_{2023,2024,2025}.csv` | 8,760 / 8,784 / 8,760 |
| `ERCOT_HB_NORTH_rt_{15min,hourly}_2023-2025.csv` | the three years concatenated |

Hourly is the simple mean of the four 15-minute intervals in each delivery
hour — the convention `derive_ercot_zonal_lmp.py` uses.

## Published calendar, NOT the model's 8760 clock

The validation parquet drops Feb 29 and folds DST onto a fixed non-leap
8760-hour grid. This export deliberately does not: it preserves ERCOT's own
delivery calendar, so

- 2024 keeps Feb 29 (hence 8,784 hours, not 8,760);
- the spring-forward delivery hour is **absent** (Mar 12 2023 runs 1, 2, 4, …);
- the fall-back hour appears **twice**, the second pass carrying
  `Repeated Hour Flag = Y`.

A consumer joining these CSVs to model output must map onto the 8760 clock
first, exactly as `derive_ercot_zonal_lmp.py` does.

## Verification at the 2026-09-18 cut

Every hour is a full four-interval mean (`n_intervals == 4`, no gaps), and the
annual means reproduce the independently-built validation parquet to three
decimals:

| Year | This export | `actual_lmp_zonal_ERCOT.parquet` |
|---|---|---|
| 2023 | 48.30 | 48.304 |
| 2024 | 25.89 | 25.886 |
| 2025 | 32.02 | 32.016 |

(The min/max differ between the two by construction — this export's extrema are
over 15-minute intervals, the parquet's over hourly averages.)
