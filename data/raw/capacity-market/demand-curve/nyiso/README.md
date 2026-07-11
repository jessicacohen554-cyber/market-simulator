# NYISO capacity-market-demand-curve (ICAP Demand Curves)

Drop the retrieved unified CSV here as **`nyiso.csv`**. NYISO publishes a
separate curve per locality — populate the `area` column (NYCA, NYC, LI,
G-J) per row.

- **metric:** `net_cone` (NYISO's demand-curve reference point is the Net-CONE
  analog; native alias `reference_point_price`), `irm`, `curve_point` (native
  alias `icap_demand_curve_point`).
- **delivery_year:** NYISO capability-year label.
- **y_unit:** NYISO publishes ICAP prices in $/kW-month.

## Authoritative sources

- NYISO ICAP Demand Curve Reset filings (triennial): https://www.nyiso.com/icap-demand-curves
- NYISO ICAP Manual: https://www.nyiso.com/documents/20142/2923301/icap_mnl.pdf
- NYISO Load & Capacity Data ("Gold Book"): https://www.nyiso.com/documents/20142/2226333/2024-Gold-Book-Final.pdf

**STATUS:** `nyiso.csv` committed — Net CONE, price cap, and 2-point curve (reference price + derived zero-crossing) per locality (NYCA/G-J/NYC/LI) × season (summer/winter) for the 2025-2026 Capability Year, from NYISO's "Demand Curve Parameters 2025-2026" reference sheet (the currently-live nyiso.com posting); NYCA IRM (24.4%) from the NYSRC 2025-2026 IRM Study. An older "Staff Final 2025-2029 DCR Recommendations" vintage gives systematically lower figures (~10% lower, likely a Board-directed post-filing adjustment) — not included to avoid a key collision; noted here for reconciliation. See `docs/handoffs/capacity-market-intake-2026-07.md`.
