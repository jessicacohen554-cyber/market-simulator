# CAISO capacity-deliverability (LCR "Capacity Needed" / Maximum Import Capability)

Drop the retrieved unified CSV here as **`caiso.csv`**.

- **area_type:** `local_area` for LCR rows; `branch_group` for MIC rows;
  `rto` for the PRM row (area = CAISO).
- **delivery_year:** **calendar** study year, "2025" (CAISO has no capacity
  market; LCR for study year N is published ~April of N-1).
- **areas (LCR):** Humboldt, North Coast/North Bay, Sierra, Stockton, Greater
  Bay, Greater Fresno, Kern, Big Creek/Ventura, LA Basin, San Diego/Imperial
  Valley. **areas (MIC):** intertie / branch-group names (NOB, Malin/COTP, Palo
  Verde, Sylmar-AC, Eldorado, IPP, …).
- **native → canonical metric:** LCR "Capacity Needed" → `requirement`;
  Maximum Import Capability (MIC) → `import_limit` (a *seam* import limit, not an
  internal-LDA transfer — note this in `source_page`); PRM → `system_requirement`
  (`value_pu`).

## Authoritative sources

- LCT Final Reports (LCR "Capacity Needed" table, ~p.3):
  - 2023: https://www.caiso.com/Documents/Final2023LocalCapacityTechnicalReport.pdf
  - 2024: https://stakeholdercenter.caiso.com/InitiativeDocuments/Final-2024-Local-Capacity-Technical-Report.pdf
  - 2025: https://stakeholdercenter.caiso.com/InitiativeDocuments/Final2025LocalCapacityTechnicalReport.pdf
- Maximum Import Capability (prefer the import-allocation XLSX; the PDFs
  rasterize the number cells):
  - 2024 MIC: https://www.caiso.com/documents/isomaximumresourceadequacyimportcapabilityforyear2024.pdf
  - 2025 MIC: https://www.caiso.com/documents/iso-maximum-resource-adequacy-import-capability-for-year-2025.pdf
  - Import allocations: https://www.caiso.com/library/2024-import-allocations , https://www.caiso.com/library/2025-import-allocations
- CPUC binding local RA (cross-check): D.22-06-050 (2023–2025), D.23-06-029
  (2024–2026), proceeding R.23-10-011.

Required years (backcast): 2023, 2024, 2025.

**DATA COMMITTED:** `caiso.csv` — 138 rows covering 2023–2025 LCR (10 local
areas × 3 yr), MIC (36 branch groups × 3 yr, non-zero only), PRM (3 yr).
LCR totals: 25,449 / 22,080 / 22,782 MW. MIC totals: 16,055 / 16,452 / 16,148 MW.
PRM: 16% (2023), 17% (2024–2025) per CPUC D.23-06-029.
