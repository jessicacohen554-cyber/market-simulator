# Capacity-market data intake — 2026-07-11 (P-0B)

Intake session for `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`
§3-4 (N1-N6): capacity-market demand-curve parameters, auction/spot clearing-
price history, and ELCC/accreditation curves for the five capacity-market ISOs
(PJM, NYISO, ISO-NE, MISO, CAISO). ERCOT excluded (energy-only).

Delivered: three new datatypes (`capacity-market-demand-curve`,
`capacity-market-auction-price`, `capacity-market-elcc`) under
`data/raw/capacity-market/`, each schema-first with a per-ISO registry, a
curation script, and a tmp-CLEAN_DIR test — see the `data-intake` skill
recipe. All 15 ISO×datatype partitions (636 rows total) curate cleanly with
real, cited data; no LP solves were run.

Row counts by datatype × ISO (`python -m scripts.curate_capacity_market_<name>`):

| datatype | PJM | NYISO | NEISO | MISO | CAISO |
|---|---|---|---|---|---|
| demand-curve | 26 | 29 | 21 | 45 | 10 |
| auction-price | 47 | 24 | 22 | 100 | 5 |
| elcc | 134 | 61 | 27 | 35 | 46 |

## Notable data-modeling findings during intake

- **PJM's VRR curve is formula-defined, not point-published.** PJM Manual 18
  gives the curve's shape as a formula (Net CONE, Gross CONE, IRM, an
  accredited-UCAP factor) whose price at most points is not itself a
  published number — only the point's x-position (reserve-requirement
  fraction) is public, plus the zero-price point. The schema's
  `validate_tidy` was relaxed to accept a `curve_point` row with only
  `x_value` (no guessed `y_value`); scalar metrics still require a value.
- **PJM ICAP vs UCAP basis.** The 2025/2026 filing's own "Pool Wide Accredited
  UCAP Factor" (79.69%) differs from the *retrospective* "Reference Resource
  AUCAP Factor" (79.00%) used to derive that same year's published Net CONE
  UCAP figure — confirmed by reproducing PJM's own arithmetic
  ($65,978 ÷ 365 ÷ 0.79 = $228.81/MW-day). This basis ambiguity is exactly the
  #1532 FPR/ICAP-UCAP flag the plan's P-2B session is meant to adjudicate —
  both figures are captured (`net_cone` in `usd_per_mw_yr`/`usd_per_mw_day`;
  `price_cap`/`price_floor` carry both the UCAP-basis and the
  `usd_per_mw_day_icap` pre-conversion figure).
- **NYISO has two live vintages of the same delivery year's demand-curve
  parameters** ~10% apart (a "Staff Final DCR Recommendations" filing vs. the
  currently-posted "Demand Curve Parameters 2025-2026" sheet, likely a
  Board-directed post-filing adjustment per FERC Docket ER25-596). Only the
  currently-live sheet is committed, to avoid a key collision; the older
  vintage's values are noted in the NYISO README for reconciliation.
- **MISO's Reliability-Based Demand Curve (RBDC, live PY2025-26+) publishes
  only one labeled clearing-intersection point per season/subregion chart**
  — the full curve exists only as an image (orange line in each PRA-results
  chart), not a data table. Digitizing it further would be estimation, so
  only the labeled points are captured.
- **CAISO's CPM designations all cleared at exactly the soft-offer cap** — the
  regulatory ceiling, not a competed price. This is itself a finding: CAISO's
  adequacy mechanism has no genuine price discovery, confirming the plan's
  "documented low-fidelity proxy" framing for CR-1.
- **No ISO except MISO (and, third-party, NY-BEST for NYISO / GE-NRDC and
  E3 for ISO-NE) publishes a genuine ELCC-vs-penetration curve.** PJM's
  closest analogue is a 9-year *forecast-delivery-year* indexed table
  (declining ELCC as buildout increases over time), not a penetration-%
  axis — captured but flagged as a different shape than what CR-3.1 modeled.
- **Resource-class/geography granularity exceeds the schema's key in two
  places** (CAISO's CA/WY/NM wind sub-geographies; NYISO's ROS/GHI/NYC/LI
  regional CAF breakdown) — both collapse onto the same `resource_class` with
  the distinguishing detail carried only in `source_page`, not a key column.
  Flagged in each ISO's README as a known limitation; a future schema
  revision could add a `sub_region`/`geography` column if this data sees
  heavy consumption.
- **Governance note applied:** `capacity-market-auction-price` intake
  excluded any row whose delivery year exceeds 2026/27 (PJM 2027/2028 BRA,
  ISO-NE FCA18/CCP2027-2028) even where the primary source had already
  published the cleared price — `validate_tidy` enforces this and would raise
  if such a row were added. `capacity-market-demand-curve` (a mechanism
  input, not an outcome) carries no such restriction and includes PJM
  2027/2028 planning parameters.

## MANUAL DOWNLOADS NEEDED (blocked or not located this pass)

### PJM
- BRA zonal/LDA clearing prices for delivery years 2016/17-2023/24 (11 years)
  — only RTO-level figures were extracted for those years; each year's own
  BRA Report PDF would carry the full Table 3 zonal breakdown. Not a
  paywall/technical block, just not fetched in this pass (time budget).
- IMM (Monitoring Analytics) "Analysis of the RPM Base Residual Auction"
  reports for 2025/26-2027/28 — identified by URL, not fetched (would be a
  cross-check, not needed once primary BRA Report PDFs were parsed).
- Brattle "Sixth Review of PJM's Variable Resource Requirement Curve" —
  identified, not fetched (curve-shape rationale; operative numbers already
  sourced from PJM's own filings).
- "Preliminary ELCC Class Ratings for Period 2027/2028 through 2035/2036"
  (newer vintage of the 9-year indicative table) and most of the 2025 ELCC/
  RRS Study's non-class-rating appendices (Tables 4-39, weather-bin
  methodology) — not fully mined, only the class-rating/installed-MW tables.
- Tooling note (not a real block): WebFetch's summarizer cannot parse any of
  PJM's PDFs ("encoded image data" false positive on genuine text-layer
  PDFs) — worked around with `pdftotext -layout` on locally-cached copies.

### NYISO
- Monthly-granularity Spot Market Auction prices — NYISO's own portal
  (`icappublic.nyiso.com/ucap/public/...`) is an interactive Java form with
  no static-file export; used Potomac Economics' annual averages instead.
- The specific FERC-filed eTariff compliance filing that would show the
  final 2025-2026 Demand Curve parameters byte-for-byte (to reconcile the two
  live vintages noted above) — not located.
- An official NYISO-adopted (not NY-BEST-commissioned) ELCC-vs-penetration
  curve table — none found; NYISO's own materials publish only the current-
  year CAF.

### ISO-NE
- FCA1-FCA6 individual clearing prices — only an aggregated 2010-2016 range
  ("$2.951-$4.500") is published; per-year floor/starting prices were found
  in `fca_parameters_final_table.xlsx` but floor price ≠ confirmed clearing
  price, so not reported as a clearing price.
- FCA18's exact piecewise demand-curve breakpoints (the discrete MW/$ table
  analogous to the FCA11 one that was found) — the FCA18 ICR-assumptions PDF
  gives Net CONE/Gross CONE/Starting Price/MCL/ICR but not the resulting
  curve's discrete points; the equivalent presentation was not located.
- FCA17's separate New Brunswick-interface clearing price
  ($2.551/kW-month) — appeared only in secondary commentary, not confirmed
  against a primary ISO-NE document; excluded.
- No official ISO-NE-adopted ELCC/accreditation percentage table exists yet
  (Resource Capacity Accreditation reform still open, CAR-SA expected Q4
  2026) — not a retrieval gap, the number doesn't exist yet.

### MISO
- **PY2026-27 PRA Results Posting** (the primary source for exact zonal
  seasonal clearing prices, CONE by zone, PRMR) — returned HTTP 403 on 6
  repeated attempts (direct curl, browser User-Agent, Referer header,
  WebFetch, Wayback Machine mirror unreachable). A secondary source (Modo
  Energy) was found with summary figures but excluded from the committed CSV
  per this intake's primary-source-only policy.
- 2022/23 and 2020/21 PRA Results Postings — HTTP 403 on repeated attempts;
  would give exact zonal breakdowns for those years (a sparser historical
  series from a later report's comparison table was used instead).
- The FERC order/docket (ER23-2977) with the final approved RBDC tariff
  language and confirmed Net CONE values — only MISO's own draft "Conceptual
  Design White Paper" and RASC slide decks were retrieved, not the FERC order
  text itself.
- No MISO storage-ELCC-by-duration report was located (search focused on
  wind/solar per the task).
- PY2023-24 zonal cleared-MW breakdown beyond the ACP-by-zone table (p.4 of
  the 2023 PRA Results doc likely has a fuller MW table, not pulled this
  pass).

### CAISO
- CAISO Business Practice Manual for Reliability Requirements — not fetched;
  would give operational-detail confirmation of CPM mechanics beyond the
  Tariff/FERC order already confirming the $7.34/kW-month figure.
- CAISO Appendix A (Master Definition Supplement) — WebFetch could not decode
  the PDF's binary/compressed stream; the FERC order already independently
  confirms the figure and its Appendix A location, so not re-fetched via the
  page-image method.
- CPUC "2025 Resource Adequacy Market Price Benchmark" filing — found by URL,
  not fetched (a related but distinct PCIA price concept, flagged in case a
  future intake wants MPB data specifically).
- CPUC "2024 Resource Adequacy Report" does not appear to exist yet (CPUC RA
  reports run ~18-20 months behind the compliance year; the 2023 report,
  published 2025-08, is confirmed the most current as of this intake).
- CAISO's marginal-ELCC heatmap surface (Figure 13 of the E3/Astrapé study, a
  2-D solar-GW × storage-GW grid for 2030) — not transcribed since it's a
  joint 2-D surface, not a simple penetration series; flagged for a follow-up
  pass if the marginal joint surface is specifically wanted.

## Not attempted this pass (scope trims, not blocks)

- MISO's per-zone-per-season PRMR (MW) breakdown (40 rows) — season-level %
  IRM was captured instead; the MW table exists in the source if needed.
- CAISO's monthly (not annual) RA report prices, e.g. the Sept 2023
  seasonal-peak spike to $24.07/kW-month — fetched by the research agent but
  intentionally excluded; this schema's grain is annual.
- PJM's thermal-class ELCC ratings (nuclear, coal, gas CC/CT, diesel, steam,
  oil) — PJM's 2025/26 ELCC overhaul rates these too, but they're out of
  scope for this datatype's CR-3.1 (wind/solar/storage accreditation) intent;
  fetched and available if a future session wants them.

## Next steps (per the plan's Wave 1)

CR-1 (P-1B, sloped demand curve) can now build on real PJM/NYISO/ISO-NE/MISO
curve parameters and CAISO's re-cited proxy. CR-2 (P-2A, validate against
auction history) has real clearing-price series for all five ISOs to compare
against. CR-3.1 (P-2C, marginal-ELCC curves) has a genuine multi-point curve
for MISO wind/solar and CAISO wind/solar/storage; PJM/NYISO/ISO-NE fall back
to single-point or third-party-study curves per their README notes.
