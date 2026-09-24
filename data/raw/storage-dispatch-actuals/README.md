# storage-dispatch-actuals — measured hourly storage dispatch + SOC (ERCOT, CAISO)

**Report-only comparison data** for the Run Explorer "Storage Dispatch — Model vs
Actual" panel (`scripts/lib/storage_compare.py`). Never read by a solve, a scorer
or a gate (storage-dispatch left the rubric at v2.7). Measured outcomes used only as
the comparison side, so rule 13 `[R-MEASURED]` is not engaged.

Built by `scripts/data/build_storage_dispatch_actuals.py` (re-run = re-fetch).
Source downloads are cached under `_source/` (gitignored, ~177 MB); their identity is
`SHA256SUMS.txt`.

| File | Years | Dispatch source | SOC source |
|---|---|---|---|
| `CAISO_storage_hourly.parquet` | 2021–2025 | CAISO Today's Outlook history `/outlook/history/<YYYYMMDD>/storage.csv`, 5-min "Total batteries" (standalone + hybrid battery component) | CAISO Daily Energy Storage Report data (`storage-report-2023q1…2024q4.xlsx`, `storage-report-q1…q4-2025.xlsx`), `market_output`, RTD, LESR, SOC — **stand-alone batteries only**, 2023–2025 |
| `ERCOT_storage_hourly.parquet` | 2024 (Oct–Dec only), 2025 | EIA-930 `ERCO hourly` `NG: BAT + NG: UES` (net) | none published historically |

Columns: `year, hour, net_mw, discharge_mw, charge_mw, soc_mwh, source`. `hour` is the
model's fixed-standard-time, hour-beginning, non-leap 8760 slot (CAISO UTC−8, ERCOT
UTC−6). Unobserved hours are NaN, never 0.

Known source limits (surfaced as notes on the panel):

- **CAISO 2022**: discharge 2.82 TWh > charging 1.79 TWh — physically impossible for a
  fleet, so the 2022 Outlook series under-reports charging (co-located charging not
  metered as battery). Read shape, not net level. 2021 and 2023–2025 are consistent
  (charge ≥ discharge).
- **CAISO pumped storage** is folded into Large Hydro at the source → compared as
  batteries only (model `li_ion`).
- **CAISO SOC** covers stand-alone resources only → compared as % of own annual max.
- **ERCOT 2021–2023** have no hourly storage breakout in EIA-930. Candidate backfill:
  ERCOT Fuel Mix Report (15-min, incl. storage) — not yet fetched.
