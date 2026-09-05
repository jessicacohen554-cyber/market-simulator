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

**STATUS (2026-08-02 addition, FFR-2C — the FR-19 re-anchor).** Extended forward
to **Capability Year 2026-2027**, the second annual update of the 2025-2029 DCR,
which NYISO was required to post by its tariff deadline of 2025-11-30 (presented
at the joint ICAPWG/MIWG/PRLWG session 2025-11-17). Source: the
currently-live "Demand Curve Parameters CY 2026-2027" one-pager linked from the
nyiso.com Installed Capacity Market page
(`documents/20142/54740429/Demand-Curve-Parameters-CY-2026-2027.pdf`, sha256
`713560dc6851e9d03e18c50c23c63520af8fe6ef67ad062c4e64700c981207cc`). This closes
the NYISO row of the parent `../README.md` forward-vintage backlog, which FF-G3
filed as NOT RETRIEVED — the document-library URL was simply not locatable then;
it is reachable now from the ICAP market page.

Identical sheet layout and identical representative zones to the 2025-2026 block
(F-Capital → NYCA, G-Hudson Valley (Dutchess) → G-J, J → NYC, K → LI), so the
two years are directly comparable. NYCA Annual Reference Value moves
**50.55 → 57.70 $/kW-Year (+14.1 %)**, decomposing into Gross CONE
127.71 → 131.94 (+3.3 %) and Net EAS Revenues 77.15 → 74.24 (−3.8 %) — i.e. most
of the move is a smaller energy-and-ancillary offset, not construction cost.

Two coverage notes, both deliberate:

- **`gross_cone` rows are new with this vintage.** The 2026-2027 block carries
  the published Gross Cost of New Entry alongside the Annual Reference Value, so
  the E&AS offset (their difference, = the published Net EAS Revenues line) is
  recoverable from the file. Earlier blocks were intaken before that need
  existed and carry `net_cone` only; they are not backfilled here.
- **No `irm` row for 2026-2027.** The Annual Reference Value one-pager does not
  publish the IRM — that comes from the NYSRC IRM Study for the capability year,
  which was not retrieved in this session. Left absent rather than carried
  forward from the 2025-2026 study (24.4 %), per the no-guessing rule.

**STATUS (2026-09-04 addition, capx D52 — the NYISO adequacy-requirement
devintage, D45 §5.2.4 items 1–2):** 19 NYCA rows intaken from the NYSRC
2026-2027 IRM Study Technical Report **Appendices** (Dec 2025; sha256
`714aeeb9156795108147982f93cf90f885ed110835e0a6f2fa257f809da419d5`, the D45 §8
document, re-fetched and hash-matched), Appendix D §D.1.1 **Table D.2 "New York
Control Area ICAP to UCAP Translation"** (report p.68 = PDF p.86), capability
years 2020-2021 … 2025-2026:

- `icap_market_forecast_peak` (mw) — Table D.2 "Forecast Peak Load (MW)", the
  ICAP-market forecast peak the NYCA requirement of that capability year was
  set on (32,296 / 32,333 / 31,767 / 32,049 / 31,542 / 31,469).
- `irm_adopted` (pct) — Table D.2 "Installed Capacity Requirement (%)" − 100,
  the EC-approved IRM (18.9 / 20.7 / 19.6 / 20.0 / 22.0 / 24.4). Distinct from
  the existing `irm` rows, which carry the IRM STUDY base-case value and differ
  in 2023-2024 (19.9 study → 20.0 adopted) and 2024-2025 (23.1 → 22.0); the
  NYSRC EC approval dates are in each row's `source_page`.
- `icap_ucap_translation_factor` (fraction) — one NEW row, 2025-2026 = 0.1300;
  the 2020-2021 … 2024-2025 rows already on disk (cited to the 2025-2026
  appendices) are byte-equal to the 2026-2027 table and were left as they are.
- `ucap_requirement` (mw) — Table D.2 "UCAP Requirement (MW)" (35,213 / 35,604 /
  34,277 / 34,559 / 33,397 / 34,059), a VALIDATION row for the identity
  `peak × (1 + IRM) × (1 − derate) = UCAP requirement` the registries are
  tested against (< 1 MW; the table rounds to MW) — never a fit target.

Consumers: `NYCA_ICAP_FORECAST_PEAK_MW_BY_ISO`, `NYCA_IRM_ADOPTED_BY_ISO`,
`NYCA_ICAP_UCAP_TRANSLATION_BY_ISO` (`config/capacity_market.py`), armed only by
the default-OFF `ScenarioConfig.nyiso_requirement_forecast_peak` /
`nyiso_requirement_vintage_factors` gates; reconciled row-for-row by
`tests/unit/model/test_capacity.py::TestNyisoRequirementDevintage`. The shipped
composite `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]` stays
pinned to the 2024-2025 factor (re-deriving it onto the 2025-2026 row is a
rule-23 owner decision, routed in `docs/handoffs/FINDING-capx-d52-2026-09-04.md`).

## capx D59 intake (2026-09-05): locality Gross CONE, 2023-2024 / 2024-2025 / 2025-2026

Twelve `gross_cone` rows (usd_per_kw_yr) — the "Gross Cost of New Entry ($/kW-Year) [1]"
row of the SAME three Demand Curve Parameters sheets the committed locality ARV /
reference-point / max-clearing rows already cite (ICAPWG annual-update decks 2022-11-14
p.31 and 2023-11-17 p.30; the posted 2025-2026 parameter sheet), per capacity region
(NYCA / G-J / NYC / LI); the 2026-2027 rows were already committed by FFR-2C. Values:
2023-24 120.04 / 157.61 / 212.81 / 168.15; 2024-25 132.98 / 174.72 / 229.11 / 186.37;
2025-26 127.71 / 127.58 / 222.73 / 137.03. Consumer: `LOCALITY_GROSS_CONE_BY_ISO`
(`config/capacity_market.py`) — the D59 locality entry siting leg scales a thermal
candidate's annualized fixed cost by the published `GrossCONE_locality / GrossCONE_NYCA`
ratio of the delivery year's vintage (NYISO's own peaking-plant cost differential; no
zone premium is invented), armed only by the default-OFF
`ScenarioConfig.locality_capacity_curves`. The locality CURVES themselves
(`net_cone` / `curve_point` / `price_cap` rows for NYC / LI) were already on disk and
were re-verified row-for-row against the fetched sheets this session (sha256 in
`docs/handoffs/DESIGN-capx-d59-nyiso-locality-2026-09-05.md` §9); they are reconciled
by `tests/unit/model/test_capacity.py::TestNyisoLocalityCapacityCurves`.
