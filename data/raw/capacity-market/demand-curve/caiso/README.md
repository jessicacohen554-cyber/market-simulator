# CAISO capacity-market-demand-curve (documented fixed proxy — no curve)

Drop the retrieved unified CSV here as **`caiso.csv`**. CAISO has no
centralized capacity auction or sloped demand curve (bilateral Resource
Adequacy). Only two scalar metrics apply:

- **metric:** `soft_offer_cap` (CAISO's Capacity Procurement Mechanism (CPM)
  price cap — tariff-published), `ra_report_price` (CPUC's annual Resource
  Adequacy Report observed bilateral price, where published).
- No `curve_point` rows — there is no curve; `point_index`/`x_value`/`x_unit`
  stay blank for every row.
- **delivery_year:** calendar year.
- **y_unit:** likely `usd_per_kw_month` or `usd_per_kw_yr` — record whichever
  the source actually publishes, do not convert.

## Authoritative sources

- CAISO Tariff / Business Practice Manual for Reliability Requirements (CPM
  soft offer cap): https://www.caiso.com/documents/ (search "Capacity
  Procurement Mechanism soft offer cap")
- CPUC Resource Adequacy Report: https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/electric-power-procurement/long-term-procurement-planning/resource-adequacy-homepage

**STATUS:** `caiso.csv` committed — CPM soft-offer cap for 2023-2025
($6.31/kW-month through 2024-05-31, $7.34/kW-month from 2024-06-01 per FERC
Docket ER24-1225-000) and CPUC RA Report bilateral prices for 2023-2025 (system
weighted-average plus the 2023 product breakdown: all-RA/local/flexible/
system-incl-import), from the CPUC 2023 Resource Adequacy Report (published
2025-08, the most current comprehensive CPUC RA report as of this intake).
Monthly-granularity RA prices (e.g. the Sept 2023 seasonal-peak spike to
$24.07/kW-month) were fetched but not transcribed — this schema's grain is
annual; see `docs/handoffs/capacity-market-intake-2026-07.md` if the monthly
series is wanted later.
