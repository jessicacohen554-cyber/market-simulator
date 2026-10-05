# eia-923-disposition — raw

EIA Form 923 Schedules 6/7, **"Annual Source and Disposition of Electricity for Non-Utility
Generators"**, one row per plant-year, 2019–2025, every US plant:

`eia923_disposition_2019_2025.csv` — `year, plant_id, plant_name, plant_state, sector_code, chp,
gross_mwh, incoming_mwh, station_use_mwh, direct_use_mwh, retail_sales_mwh, sales_for_resale_mwh,
tolling_mwh, outgoing_mwh` (MWh).

**Why it is here (closeout-CAISO-w6, 2026-10-05).** This is the plant owner's own electricity
balance. It separates what a self-generator or cogeneration plant sends to the wholesale grid
(sales for resale, tolling, outgoing) from what it or its host consumes on site.

It is used for two things:
- `scripts/data/derive_caiso_chp_btm_share.py` derives the measured CAISO CHP behind-the-meter
  share from it (`ScenarioConfig.caiso_chp_btm_measured`).
- It answers whether industrial self-generators such as THUMS (56051) and New-Indy Ontario
  (10427) are grid-visible. See `docs/records/caiso/closeout-caiso-w6/`.

**Source:** EIA, public domain. `https://www.eia.gov/electricity/data/eia923/xls/f923_<year>.zip`,
or `.../archive/xls/f923_<year>.zip` for older releases. Workbook
`EIA923_Schedules_6_7_NU_SourceNDisposition_<year>_Final*.xlsx`, first sheet, header row 5.
Fetched 2026-10-05. The ZIPs are the same releases as `../eia-923-generation-fuel/` (identical
SHA-256).

**Regeneration:** `python3 scripts/data/fetch_eia923_disposition.py` (optionally `--zip-dir <dir>`).
`SHA256SUMS.txt` records the CSV and the seven source ZIPs.
