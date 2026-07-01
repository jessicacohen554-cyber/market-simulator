# ISO-NE capacity-deliverability (LSR / MCL / interface import limit by zone)

Drop the retrieved unified CSV here as **`isone.csv`**.

- **area_type:** `capacity_zone` (system ICR row uses `rto`, area = RestOfSystem).
- **delivery_year:** capacity-commitment-period label, "2024/2025"
  (June 1 – May 31). Auction → CCP: FCA 14 → 2023/24, FCA 15 → 2024/25,
  FCA 16 → 2025/26.
- **areas:** SENE (Southeast New England, import-constrained), NNE (Northern New
  England, export-constrained), Maine (nested, export-constrained), RestOfPool
  (unconstrained), plus RestOfSystem for the system ICR.
- **native → canonical metric:** LSR → `requirement` (import zones); MCL →
  `export_limit` (export zones); transmission interface (import) limit →
  `import_limit`; ICR / net-ICR → `system_requirement`.
- Where "with Mystic 8 & 9" vs "without" variants exist, use the WITH-Mystic
  value and note the alternate in `source_page`.

## Authoritative sources

FCA Informational Filings (Section IV.A: LSR/MCL + interface limits); companion
ICR-Related Values filings restate them.

- FCA 14 (2023-24 CCP): https://www.iso-ne.com/static-assets/documents/2019/11/er20-___-000_11-5-19_fca_14_info_filing.pdf
- FCA 15 (2024-25 CCP): https://www.iso-ne.com/static-assets/documents/2020/11/public_info_filing_for_fca_15.pdf
- FCA 16 (2025-26 CCP): ISO-NE FCM filings page /static-assets/documents/2021/11/ ; ICR acceptance: https://isonewswire.com/2022/01/26/ferc-accepts-capacity-requirements-for-2025-2026-forward-capacity-auction-16-set-for-february-7/
- FCA results & parameters (LSR/MCL spreadsheet): https://www.iso-ne.com/isoexpress/web/reports/auctions/-/tree/fca-results
- Zone/LSR/MCL definitions: https://www.iso-ne.com/markets-operations/markets/forward-capacity-market/fcm-participation-guide/capacity-zone-development

Required years (backcast): 2023/2024, 2024/2025, 2025/2026.

**DATA COMMITTED:** `isone.csv` — 15 rows, 3 CCPs (2023/24–2025/26), sourced from
FCA 14/15/16 Informational Filings. 2023/24 values are the with-Mystic-8&9
variant; alternates noted in `source_page`.
