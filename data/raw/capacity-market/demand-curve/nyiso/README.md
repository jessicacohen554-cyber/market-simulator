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

**STATUS (2026-07-15 addition):** Extended back to the full prior DCR cycle —
capability years 2021-2022, 2022-2023, 2023-2024, and 2024-2025 (all four years
of the 2021-2025 ICAP Demand Curve Reset) — from NYISO's ICAPWG "Annual Update
for CY ICAP Demand Curves" stakeholder decks (posted nyiso.com) and the
matching NYSRC IRM Study Technical Reports (2021/2022/2023/2024 studies).
Coverage is uneven by design, not oversight:

- **2023-2024 and 2024-2025** have the full parameter set (irm, net_cone,
  price_cap, 2-point curve) — pulled from the "Current Year" summary table
  embedded in that year's own Annual Update deck (cross-checked for
  2024-2025 against the standalone "Demand Curve Parameters CY 2024-2025"
  one-pager, identical figures).
- **2021-2022 and 2022-2023** carry only `irm` and the reference-price
  `curve_point` (index 0) + derived zero-crossing (index 1) — the
  "Current Year" summary table (with `net_cone`/`price_cap`) was not part of
  those two years' Annual Update decks, and no standalone parameter
  one-pager could be located for either year (see MANUAL DOWNLOADS NEEDED
  below); the Sept/Oct 2020 preliminary DCR-study figures for 2021-2022 were
  deliberately **not** substituted in, since they were revised before Board
  approval/FERC filing and no longer match the "Final" figures used
  everywhere else in this file.
- **`season` is blank on every 2021-2022 through 2024-2025 row.** Confirmed
  directly from NYISO training material ("ICAP Demand Curve" intermediate
  course deck, 2026): ICAP Demand Curves were **not** split by Summer/Winter
  Capability Period before the 2025-2029 DCR — one reference price, one max
  clearing price, and one zero-crossing % applied year-round per locality.
  The 2025-2026 row block (season = summer/winter) is the **first**
  season-split vintage; do not backfill season onto the older rows.
- **`Demand Curve Length` (the zero-crossing shape parameter) is fixed for
  the entire 2021-2025 DCR cycle** at 12%/15%/18%/18% (NYCA/G-J/NYC/LI) —
  confirmed identical in the original Aug-2020 Analysis Group DCR study and
  in the finalized CY2023-2024 and CY2024-2025 postings. It is not one of
  the 3 parameters NYISO's annual-update formula touches (only Net EAS
  revenue, Gross CONE escalation, and the winter-to-summer ratio update
  annually), so the same 12/15/18/18 is used for 2021-2022 and 2022-2023
  too, with that invariance documented in each row's citation rather than
  guessed.
- **Representative zone changed between DCR cycles.** The 2021-2025 DCR
  (these new rows) reports one reference price per locality using zones
  **C-Central** (→ `area=NYCA`) and **G-Hudson Valley/Rockland**
  (→ `area=G-J`); the already-committed 2025-2026 row block (2025-2029 DCR)
  uses **F-Capital** (→ `NYCA`) and **G-Hudson Valley/Dutchess** (→ `G-J`)
  instead. NYC (Zone J) and LI (Zone K) are unchanged across cycles. This is
  a genuine methodology change documented in NYISO's own filings, not a
  zone-mapping inconsistency in this file.
