# FINDING soco-99 — FLA EIA-930 extract 2019–25 and the FPC / TAL `hr_by_year` cells (2026-10-02)

**Lane.** soco-99. Zero LP. Owner card → **"R-4 FLA 930 extend"** (SOCO-33 §7 R-4; FINDING-soco-98 §6). SOCO rests at
NOT-YET (7/4/0/3/0, keeper `2026-09-30-soco96-measured-oil-burn` unchanged). A **forecast-lane input, inert in every
backcast**.

## 1. What landed

| Item | Change |
|---|---|
| Producer | `scripts/data/extend_eia930_hourly_from_balance.py --region`: `build_region_rows` sums an EIA-930 region's member BAs from the BALANCE archive (membership per hour, `(Adjusted)` demand family, NaN unless every member files). |
| Data | `data/raw/eia-930-hourly/FLA hourly.parquet` +43,080 rows: local 2019-01-01 .. 2022-12-31 and 2025-02-01 .. 2025-12-31. The 18,288 committed rows and dtypes are byte-identical. |
| Registry | `INTERFACE_NEIGHBORS["SOCO"]` `SOCO_FPC` / `SOCO_TAL` `hr_by_year` = the producer's 2019–25 output. 2023–24 unchanged. Every other seam is unchanged. |
| Test | `tests/curation/test_extend_eia930_hourly_from_balance.py::test_region_rows_sum_members_per_hour`; `tests/iso/soco/test_soco_lambda_anchors.py` green (registry = producer output). |

**Why not the API route.** `fetch_eia930_hourly.py --ba FLA` needs `EIA_API_KEY`, absent in this container
(api.eia.gov answers `API_KEY_MISSING`). The BALANCE archive was already on disk for every year.

**Same quantity (rule 14).** EIA defines a region series as the sum of its member BAs. On the committed 2023–24 API
rows (17,544 h), the clock columns reproduce exactly. `Demand` matches within 1 MW in 98.4 % of hours (max 2.4 GW,
mean +0.03 %), which is revision vintage. The raw-column sum would carry member unit-slip spikes up to 65 GW, so the
`(Adjusted)` columns are the reconciled form. Unfiled hours stay NaN (2019: 947, mostly GVL 2019 H1; 2020: 85).

## 2. The cells (MMBtu/MWh)

| Seam | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SOCO_FPC | 8.37 | 8.03 | 8.08 | 9.42 | 8.66 | 9.69 | 8.69 |
| SOCO_TAL | 5.68 | 5.78 | 5.97 | 6.93 | 7.60 | 7.69 | 7.22 |

At exponent 1.0 the shape factor K = 1, so the cell is λ̄ / HH. The FLA extract gates *whether* a year is
derivable; the λ sets the value.

## 3. Flag: Tallahassee's λ basis

Annual-mean λ ($/MWh, filed zeros dropped):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TAL | 14.6 | 11.8 | 23.4 | 44.5 | 19.3 | 16.8 | 25.4 |
| FPC | 21.5 | 16.3 | 31.6 | 60.5 | 22.0 | 21.2 | 30.6 |
| JEA | 22.9 | 19.5 | 32.1 | 60.1 | 24.0 | 23.5 | 30.8 |
| FPL | 17.3 | 13.7 | 17.3 | 38.4 | 15.4 | 14.3 | 21.0 |

TAL sits 25–35 % below FPC / JEA every year, and its implied HR (5.7–7.7 at `gas_basis` 0) is below any
physical gas CC. This is the same symptom that holds back `SOCO_FPL`, only milder. soco-98 registered TAL's
2023–24 cells on the same basis, so this lane extends them as directed rather than adjusting anything (rule 13: no
haircut). The interface is 20 MW, so the weight is negligible. The FPL basis lane should resolve TAL in the same pass.

## 4. Inertness (zero LP, G-DRIFT)

- `model/interchange/spec.py` is outside `SURFACE_MODULES`. **Measured:** all 11 committed
  `results/calibration/*/run_config.json` give identical `cache_key()` before and after.
- `FLA` is read only as `proxy_ba` by the three Florida SOCO seams, which are gated on `reference_price_interface` /
  `priced_interchange` (off for SOCO). No other code reads it.
- Matrix cells `priced_interchange` / `reference_price_interface` stay `U` (no solve).

## 5. Open (routed)

- **FPL λ basis** (ferc-714 README "Flags"), now including TAL (§3), before `SOCO_FPL` is anchored.
- **Forward HR choice** (seam-own flat mean vs FINDING-soco-98 §3 elasticity fits). An owner card for the forecast lane.
