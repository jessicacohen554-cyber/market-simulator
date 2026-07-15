# PJM capacity-market-avoidable-cost-rate

Drop the retrieved unified CSV here as **`pjm.csv`** (canonical columns; see
the parent `README.md`). One row per (source_type, technology_class,
capacity_bin, cost_component, vintage) — PJM publishes one RTO-wide default
ACR table (no locality split).

- **source_type:** `pjm_manual18_default` (PJM's own Tariff/Manual 18 default
  gross ACR table) | `monitoring_analytics_som` (the Independent Market
  Monitor's own benchmark, State of the Market report) — see STATUS for why
  only the first is populated.
- **cost_component:** `gross_acr` for every row committed so far — PJM's table
  publishes only the headline gross rate, no capital/fixed-O&M/variable-O&M
  sub-component breakdown.
- **unit:** `usd_per_mw_day` throughout (PJM's table is denominated in
  $/MW-day, nameplate).

## Authoritative sources

- PJM Manual 18: PJM Capacity Market, Revision 62, effective 2025-12-17 (the
  same manual already cited by `../../demand-curve/pjm/pjm.csv`'s curve-point
  rows): https://www.pjm.com/-/media/DotCom/documents/manuals/m18.ashx
  — Section 5.4.8.4(B), "Default Gross Avoidable Cost Rate for Determination
  of Cleared MOPR Floor Offer Prices" (printed page 147).
- Monitoring Analytics, "2025 State of the Market Report for PJM", Section 5
  (Capacity), published 2026: https://www.monitoringanalytics.com/reports/PJM_State_of_the_Market/2025/2025-som-pjm-sec5.pdf
  — searched exhaustively for an independent numeric ACR-by-technology-class
  benchmark; none found (see STATUS).

**STATUS (2026-07-15, initial population):** `pjm.csv` committed — 15 rows,
all `source_type=pjm_manual18_default`, from Manual 18 Rev. 62 Section
5.4.8.4(B)'s "Default Gross ACR Values used to determine MOPR Floor Offer
Price of Existing Capacity Resource" table. This is the single canonical
default-ACR-by-technology-class table in the current manual: its own text
confirms it is reused for *both* purposes named in the schema header — the
MOPR Cleared Floor Offer Price calculation (5.4.8.4(B) itself) *and* the
must-offer-exception default sell-offer cap (5.3, "may, at its election,
utilize an offer cap based on the default gross Avoidable Cost Rate of the
applicable resource type, if available" — the same table is cross-referenced,
not a separate one). There is no separate "deactivation" technology-class
table distinct from this one; PJM's genuinely deactivation-specific mechanism
(the Deactivation Avoidable Cost Rate / DACR, OATT §114) is a *unit-specific*
formula rate individually filed per retiring unit for Part V (RMR)
compensation, not a generic technology-class benchmark, and is out of scope
for this schema's technology_class-keyed shape (see below).

The table carries two vintages of the same eight resource-type rows, both
captured (with a distinguishing `vintage` string since `capacity_bin` is
null for every row and can't disambiguate them):

- **"Through the 2025/2026 Delivery Years"** column (2022/2023 $/MW-Day
  basis): 7 rows. Steam Oil & Gas is `NA` in this column in the source — no
  row was added for it (dropped, not guessed).
- **"For the 2026/2027 Delivery Year and Subsequent Delivery Years"** column:
  8 rows (all eight classes populated, including Steam Oil & Gas).

Two source-fidelity notes, both transcribed as-is rather than corrected:

- The second column's own header is printed in the source PDF as `(20267/
  2027)` — an apparent PJM typo for "2026/2027". Reproduced verbatim in each
  row's `vintage` string with the typo flagged, not silently fixed.
- The **Onshore Wind** row's second-column cell is printed as bare `147`
  with no leading `$`, unlike every sibling cell in that column (`$591`,
  `$537`, `$94`, `$113`, `$52`, `$64`, `$70`). Word-level PDF coordinate
  extraction (`page.get_text("words")` in PyMuPDF) confirms `147` sits at
  the identical x-range as the other price cells on that row and is
  vertically aligned with "Onshore Wind" / `$83` — i.e. it is genuinely the
  table's own data cell, not page-footer text swept in by accident.
  Transcribed as `$147/MW-day`, flagged as a probable source typo (missing
  `$` glyph) rather than corrected or dropped.

**`monitoring_analytics_som` — searched, not found, no rows added.** The
2025 State of the Market Report for PJM, Section 5 (Capacity) — the natural
home for RPM/ACR/MOPR/deactivation material — was fetched and searched in
full (all ~365 pages of extracted text, every `Table 5-NN` scanned). It
contains: (a) extensive narrative critique of PJM's default-ACR
methodology (escalation method, the mothball/retirement distinction, the
CPQR segmented-offer-cap rules) with no accompanying numeric table of the
MMU's own; (b) `Table 5-18`, usage *statistics* (how many units elected
default ACR vs. unit-specific ACR/opportunity-cost — percentages of unit
counts, not dollar figures); (c) `Table 5-33`/`Table 5-34`, actual
historical Part V (RMR) compensation rates and costs for ~20 *named,
individual* deactivating units (nearly all coal, e.g. Yorktown 1 at
$159/MW-day, Eastlake 1-3 at $109/MW-day each) — real, cited, and available
if a future session wants a differently-shaped (per-unit) datatype, but each
is that specific unit's own filed/negotiated formula rate, not a generic
"Coal" class benchmark, so forcing them into this schema's
`technology_class`-keyed shape would misrepresent unit-specific outcomes as
a generic estimate; and (d) `Table 5-27`/`5-28`/`5-29`, Capital Recovery
Factor (CRF) values — a genuinely relevant input to the APIR/capital-recovery
sub-component of ACR, but a dimensionless multiplier (e.g. 0.096), not a
dollar rate, so it doesn't fit this schema's `value`/`unit` columns without
picking an arbitrary capital-cost figure to multiply by (which would be an
estimate, not a transcription). No genuine independent numeric
technology-class ACR benchmark table was found. This is reported as a
finding, not left silent — see the intake session's report for the exact
search trail.

See `docs/handoffs/capacity-market-intake-2026-07.md` for the sibling
demand-curve/auction-price/ELCC intake this datatype's scaffolding follows,
and the 2026-07-15 intake session report for the full manual-downloads list.
