# Retirement-lane data intake — 2026-07-15 (RC-0A)

Intake session for `docs/handoffs/forecast-retirement-calibration-plan-2026-07.md`
§1/§2/§5 (RD-1, RD-2, RD-3, RD-4, RD-5, RD-6, RD-9, RD-10): per-delivery-year
capacity-curve vintages for PJM/NYISO/MISO, a new PJM Avoidable Cost Rate
datatype, the retired-sheet actuals-coverage fix (Indian Point 3 / Palisades),
RTO deactivation-notice citations, and the NYISO/ISO-NE accreditation-pairing
research memos (R5a/R5b).

**No LP solves were run. No holdout year (2022, 2019, ≤2021, H1-2026) was
touched or scored. Nothing was registered on the backcast dashboard.** All
new/extended datatypes were extended in place (schema-first, per-ISO registry
modules, `write_clean`/`read_clean`) — no parallel datatypes were created for
items already covered by the P-0B `capacity-market-demand-curve` datatype.

Published market-design parameters and outcomes captured here are
rule-13-admissible inputs / validation observables — every schema explicitly
marks auction/clearing-price outcomes as never-a-fit-target; the parameters
intook here (Net CONE, IRM, FPR, curve points, ACR) are mechanism inputs, not
outcomes.

## Delivered

| # | Item | Datatype / location | Rows added |
|---|---|---|---|
| 1 | PJM demand-curve, 4 pre-CIFP vintages (2021/22–2024/25) | `capacity-market-demand-curve` (extended) | 28 |
| 2 | NYISO ICAP demand-curve, 4 vintages (2021-22–2024-25) | `capacity-market-demand-curve` (extended) | 52 |
| 3 | MISO PRA history, pre-RBDC + PY26/27 | `capacity-market-demand-curve` (extended) | 70 |
| 4 | PJM Avoidable Cost Rate | `capacity-market-avoidable-cost-rate` (**new**) | 15 |
| 5 | Actuals-coverage fix (Indian Point 3, Palisades) | `data/raw/_validation-source/retired_sheet_coverage_gaps.csv` (**new**, no schema — see §5) | 2 |
| 6 | Deactivation-notice/lead-time citations | `data/raw/capacity-market/deactivation-notice-periods/` (**new**, citation table, no schema — see §6) | 13 |
| 7a | R5a — NYISO IRM→UCAP translation | `data/raw/capacity-market/accreditation-filings/nyiso/README.md` (**new**, memo only) | — |
| 7b | R5b — ISO-NE qualified-capacity/EFORd | `data/raw/capacity-market/accreditation-filings/neiso/README.md` (**new**, memo only) | — |

Final per-ISO `capacity-market-demand-curve` coverage after this session
(validated via a real `curate()` round-trip, tmp `CLEAN_DIR`):

| ISO | delivery years | rows |
|---|---|---|
| PJM | 2021/2022 – 2027/2028 (7 years) | 57 |
| NYISO | 2021-2022 – 2025-2026 (5 years — full 2021-2025 window) | 81 |
| MISO | 2021-2022 – 2026-2027 (6 years) | 115 |
| NEISO | 2020-2021 – 2027-2028 (unchanged, already adequate) | 21 |
| CAISO | 2023 – 2025 (unchanged) | 10 |

## 1. PJM demand-curve vintages 2021/22–2024/25 (RD-1)

28 rows appended to `data/raw/capacity-market/demand-curve/pjm/pjm.csv`
(7/year: `net_cone`×2, `irm`, `forecast_pool_requirement`, `curve_point`×3);
all 29 pre-existing rows preserved byte-for-byte. Sources: each year's own
RPM BRA "Planning Period Parameters" PDF and/or its companion XLSX workbook
(URLs in `pjm/README.md`).

**FPR/basis-vocabulary finding (the open question this item was scoped to
resolve).** PJM published a "Forecast Pool Requirement (FPR)" by that exact
name in all four pre-reform years — the *concept* is not new at CIFP. What
changed is the *formula*: pre-reform `FPR = (1+IRM) × (1 − Pool-Wide 5-Year
EFORd)` gives FPR **> 1** (1.0868–1.0901 across the four years); post-CIFP
`FPR = (1+IRM) × Reference-Resource-Accredited-UCAP-Factor` gives FPR **well
under 1** (0.917–0.938). Both are the same ratio dimensionally (UCAP-MW
requirement ÷ ICAP-MW forecast peak), so both are recorded under the same
`forecast_pool_requirement` metric — the >1-to-<1 flip across the reform
boundary is itself a citable magnitude marker of how much the accreditation
reform tightened effective capacity credit.

**Price cap/floor finding.** None of the four pre-reform vintages had a
separately-published price cap or floor — confirmed negatively (no
"cap"/"floor" language in any of the 8 PDFs/XLSXs) and positively via a
Monitoring-Analytics-reported quote that 2026/2027 was "the first time...
a VRR curve with both a defined maximum price and a defined minimum price."
No price_cap/price_floor rows were added for any of the 4 vintages.

**Bonus finding:** pre-reform VRR curve points were published as literal
(MW-level, $/day-price) pairs directly in each year's XLSX ("Point
(a)/(b)/(c) UCAP Price"/"UCAP Level" rows) — unlike the post-CIFP curve
(2025/26+), which is formula-defined with only the x-position public. All 12
new `curve_point` rows carry real, non-null `y_value` with `x_unit=mw`.

2024/2025 is a compressed-schedule vintage (BRA held ~17 months out, later
re-executed per FERC Docket ER23-729-002); no standalone narrative PDF exists
at the standard URL pattern (two guesses both 404'd) — all its rows cite the
XLSX workbook alone, which publishes Net CONE only in $/MW-Day terms (both
ICAP and UCAP bases, no $/MW-Year figure that year).

## 2. NYISO ICAP demand-curve vintages 2021-2025 (RD-2)

52 rows appended to `data/raw/capacity-market/demand-curve/nyiso/nyiso.csv`
across the 4 missing capability years; 29 pre-existing rows unchanged.
2023-2024 and 2024-2025 got the full parameter set (irm, net_cone, price_cap,
2-point curve); 2021-2022 and 2022-2023 carry only `irm` + the reference-price
curve point + derived zero-crossing — no standalone parameter one-pager for
those two years' "Current Year" summary table was located (see MANUAL
DOWNLOADS NEEDED). Read directly off NYISO's ICAPWG "Annual Update for CY
ICAP Demand Curves" stakeholder decks + the matching NYSRC IRM Study
Technical Reports.

**Structural findings, not gaps:**
- `season` is blank on every 2021-2025 row — confirmed from NYISO training
  material that ICAP Demand Curves were **not** split by Summer/Winter before
  the 2025-2029 DCR; the already-committed 2025-2026 block is the *first*
  season-split vintage. Do not backfill season onto the older rows.
- `Demand Curve Length` (the zero-crossing shape parameter) is fixed for the
  **entire 2021-2025 DCR cycle** at 12%/15%/18%/18% (NYCA/G-J/NYC/LI) — it is
  not one of the 3 parameters NYISO's annual-update formula touches (only Net
  EAS revenue, Gross CONE escalation, winter-to-summer ratio update
  annually), confirmed identical across the original Aug-2020 DCR study and
  the finalized CY2023-24/CY2024-25 postings.
- **Representative zone changed between DCR cycles.** The 2021-2025 DCR uses
  C-Central (→`NYCA`) and G-Rockland (→`G-J`); the already-committed
  2025-2026 block (2025-2029 DCR) uses F-Capital and G-Dutchess instead. NYC
  (Zone J) and LI (Zone K) are unchanged. A genuine methodology change in
  NYISO's own filings, not a mapping inconsistency in this file.

Rows were round-tripped through the real `capacity_market_demand_curve.parse_iso("NYISO", ...)` reader — all 81 rows pass `validate_tidy` cleanly.

## 3. MISO PRA history pre-RBDC + PY26/27 (RD-3)

70 rows appended to `data/raw/capacity-market/demand-curve/miso/miso.csv`
(PY2021-22, PY2022-23 new; PY2023-24/PY2024-25 CONE backfill; PY2026-27 new,
partial). **No `curve_point` rows added for any pre-RBDC year**, per
instruction — the pre-RBDC regime was vertical, not sloped (see below).

**Pre-RBDC vertical-curve regime — confirmed with primary sources, and one
correction to the task's own framing: the curve was capped at CONE, not
VOLL.** FERC's order accepting the RBDC (187 FERC ¶ 61,202, Docket ER23-2977,
issued 2024-06-27) states MISO "used a vertical demand curve... since the
Auction's inception in the 2009/2010 Planning Year" and set price "at or near
the Cost of New Entry (CONE) if there is any shortfall." MISO's own VOLL
white paper confirms VOLL ($3,500/MWh 2009→2025, then $10,000/MWh) serves
four functions entirely scoped to Day-Ahead/Real-Time energy and reserve
markets — never the PRA. Documented in full (direct quotes + page citations)
in `miso/README.md`.

**PY2026-27 was found** (MISO's PRA cleared 2026-04-28, confirmed via
WebSearch), but its PRA Results Posting PDF (which would carry the RBDC
curve-point chart intersections) hit the same `cdn.misoenergy.org` HTTP 403
documented in the P-0B precedent, and no alternate mirror was located this
time. Substituted two other real, own-year primary sources instead: MISO's
FERC Docket ER26-139-000 CONE/Net-CONE filing (2025-10-15, the first year
MISO breaks Net CONE out by individual LRZ rather than by System/subregion)
and the PY2026-27 LOLE Study Report (pre-auction seasonal IRM estimate,
flagged in `vintage` as not the finalized post-auction PRMR).

**Notable finding:** two documents fetched by CDN URL from search results
turned out to be different planning years than their search-result titles
implied (e.g. "2023 Planning Resource Auction (PRA) Results" is actually the
PY2023-24 posting) — verified by reading each PDF's own title page before
trusting any figure.

## 4. PJM Avoidable Cost Rate — new datatype (RD-4)

New datatype `capacity-market-avoidable-cost-rate` (schema, per-ISO registry,
curate script, tmp-CLEAN_DIR tests — all built this session, see §6 of
CLAUDE.md's data-intake skill). 15 rows in
`data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv`, all
`source_type=pjm_manual18_default`, from Manual 18 Revision 62 §5.4.8.4(B)
"Default Gross Avoidable Cost Rate for Determination of Cleared MOPR Floor
Offer Prices" (two vintage columns: through 2025/2026, and 2026/2027-onward).

**`monitoring_analytics_som` — searched exhaustively (the full 2025 State of
the Market Report for PJM, Section 5, ~365 pages), zero rows added.** The IMM
critiques PJM's Manual-18 methodology and tabulates named-unit historical RMR
rates, but does **not** publish an independent generic technology-class
avoidable-cost benchmark of its own. This is a documented negative finding
(the RD-4 task explicitly wanted this comparison point), not a shortcut — see
`avoidable-cost-rate/pjm/README.md` for exactly which SOM tables were checked
(5-18, 5-33, 5-34, 5-27/28/29) and ruled out.

**Two apparent typos in Manual 18's own table, transcribed as-is and
flagged** (word-level PDF coordinate extraction confirms both are genuine
data cells, not OCR/extraction artifacts): the "2026/2027" column header
prints as "(20267/2027)"; the Onshore Wind 2026/2027+ cell prints as bare
"147" with no leading "$" (every sibling cell in that column is "$NNN").

Both PJM demand-curve and ACR files were round-tripped through the real
curation scripts with `CLEAN_DIR` redirected — schema-validated, correct row
counts, all pre-existing tests still pass.

## 5. Actuals-coverage fix — Indian Point 3 / Palisades (RD-5)

The committed EIA-860 retired sheet
(`data/raw/eia-860/eia860_generator_retired_and_canceled.parquet`, "2025
Early Release") omits both flagged plants:

- **Indian Point 3** (plant 8907, NY/NYISO, 1012 MW nuclear, retired
  2021-04): absent from **every** sheet of the current top-level snapshot
  (plant, operable, generators, retired_and_canceled) — EIA appears to have
  fully dropped this plant code, not just moved it between sheets.
- **Palisades** (plant 1715, MI/MISO, 811.8 MW nuclear, retired 2022-06):
  present in the current **operable** sheet (Status "OA") because Palisades
  **restarted generation in 2025** — the first US commercial restart of a
  retired nuclear plant, under a DOE loan + NRC-approved restart. Its 2022
  retirement genuinely happened; the current snapshot just no longer carries
  it as a retirement because the plant un-retired.

Both retirement rows were transcribed **verbatim** from this repo's own
already-committed EIA-860 vintage snapshots (`vintage_2021` for Indian Point
3, `vintage_2022` for Palisades) — the same EIA-860 survey data, read at the
vintage where each plant was still in that release's retired sheet, not a new
external source. New file: `data/raw/_validation-source/retired_sheet_coverage_gaps.csv`,
unioned into `scripts/data/build_capacity_actuals.py::build_retirements` (before
the BA + WINDOW filters, deduplicated against the main sheet's own rows).
Note this file lives under `_validation-source/`, not `eia-860/`, because
`data/raw/eia-860/*.csv` is `.gitignore`d as a local-override convention (see
the file's own header for the full explanation).

`capacity_actuals_nyiso.csv` and `capacity_actuals_miso.csv` were regenerated
via `scripts/data/build_capacity_actuals.py --iso {NYISO,MISO}`; each now carries
exactly one new retirement row (`8907_3`/nuclear/1012.0/2021 and
`1715_1`/nuclear/811.8/2022 respectively). `capacity_actuals_{ercot,pjm}.csv`
were regenerated too as a verification step and confirmed **byte-identical**
except the build-date stamp, then reverted to their originally-committed
content (out of RD-5's scope — neither plant maps to those ISOs' BAs).

**Palisades' restart makes its 2022 retirement scoring-ambiguous** — a model
that "retired" Palisades on schedule and a model that never touched it are
arguably both defensible against a plant that came back. This fix restores
the underlying EIA-860 *fact*; it deliberately does not adjudicate how a
since-reversed retirement should score against a 2021-2025 hindcast. That
call belongs to RC-0B (`forecast-retirement-calibration-plan-2026-07.md`
§1.1 item 3) — documented in both `data/raw/eia-860/README.md` and
`data/raw/_validation-source/README.md`.

## 6. Deactivation-notice/lead-time citations (RD-6)

13 rows in `data/raw/capacity-market/deactivation-notice-periods/notice_periods.csv`
(ERCOT 5, PJM 5, MISO 3) — a standalone citation dataset (no schema/clean_io
treatment; "citation rows," not a per-row LP input). Exists to ground the
currently-uncited `staged_oversupply_thinning` code comment in
`src/market_sim/config/scenarios.py` ("RTO deactivation-notice periods (ERCOT
§3.14 / PJM ~90-day + RMR study)...") for a future wiring session — **no
model code was edited this session.**

**Headline findings (both confirm and materially update the original
uncited comment):**

- **ERCOT** Nodal Protocols §3.14.1.1 (fetched directly, current as of
  2026-07-11): **150 days** standard notice (retirement/indefinite
  suspension >180 days), **90 days** for seasonal mothballing. The repo
  comment's "§3.14" reference is correct; its informal "~90 days" framing
  is only the seasonal-mothball case, not the general rule.
- **PJM**: the commonly-repeated "~90 days" traces only to a 2019 PJM blog
  post, not a verbatim tariff quote (agreements.pjm.com's eTariff viewer is
  an unrenderable JS SPA — see MANUAL DOWNLOADS NEEDED). More importantly,
  **the process has changed**: the current PJM Manual 14D (Revision 70,
  effective 2025-12-17, read in full) codifies a quarterly filing cadence
  with a stated minimum lead of "at least two quarters" (PJM's own
  2026-04-20 fact sheet), a clean 12-month notice for Black Start units, and
  a citable 30/45/60-day reliability-determination timeline (Manual 14D
  §9.1.3) as the real analogue to "RMR study." **Unresolved internal PJM
  discrepancy flagged, not resolved:** Manual 14D's own revision history
  claims Revision 69 "Updated Section 9.1 to reflect a 12 month deactivation
  notification period," but the Revision-70 body text in force shows the
  quarterly-cadence rule for ordinary units instead (the Black Start
  12-month rule may be what the revision-history bullet actually describes).
- **MISO**: 26 weeks (pre-2023) → ~12 months / four quarterly study periods
  (post FERC Docket ER23-630, order 2023-02-10), plus a 60-day
  System-Support-Resource (SSR, MISO's RMR-equivalent) filing figure — **all
  three MISO rows are secondary-sourced only**, flagged accordingly.
  `misoenergy.org`/`docs.misoenergy.org`/`cdn.misoenergy.org` all returned
  HTTP 403 to every method tried (curl with browser UA, WebFetch, Wayback
  Machine), consistent with the P-0B precedent's documented MISO-403
  pattern.
- **Coal rail/take-or-pay wind-down** and **decommissioning lead time** (the
  other two drivers named in the original code comment): out of scope for
  this RTO-tariff-focused pass, still entirely uncited.

## 7. R5a/R5b accreditation-pairing filings (RD-9/RD-10)

Raw documents + extracted parameters only — **no schema, no clean_io
treatment, no model wiring**, per the task's explicit framing.

**R5a — NYISO IRM→UCAP translation**
(`data/raw/capacity-market/accreditation-filings/nyiso/README.md`).
**NYISO does not publish a single forward ICAP→UCAP ratio the way PJM's FPR
or MISO's `(1+PRM_UCAP)/(1+PRM_ICAP)` do.** Its ICAP Manual (v18.0, eff.
2026-07-07) §2.5/§2.6 defines a "translation factor" formula instead:

```
NYCA_translation_factor = 1 − [ Σ(UCAP of qualified fleet) / Σ(ICAP of qualified fleet) ]
NYCA_Minimum_UCAP_Requirement = NYCA_Minimum_ICAP_Requirement × (1 − NYCA_translation_factor)
```

— the system-wide capacity-weighted average forced-outage derate, **recomputed
twice per Capability Year from the realized fleet's own EFORd-based UCAP
accreditation**, not a filed planning parameter. A worked numeric example
(NYISO training deck, 2026-05-20/21) gives a concrete in-effect number: NYC's
Locational translation factor for Summer 2025 was **5.18%**. This is a real
structural difference from PJM/MISO, not a research gap — a forecasting model
wanting NYISO's UCAP-basis requirement for a future year cannot simply carry
forward a published ratio; it would need to compute the same roll-up from its
own forecast fleet, or use the most-recently-realized factor as a forward
proxy (no recommendation made this session — a modeling decision, out of
scope for a raw-document intake).

**R5b — ISO-NE qualified-capacity/EFORd-derate**
(`data/raw/capacity-market/accreditation-filings/neiso/README.md`).
**No.** ISO-NE's Qualified Capacity is **not** EFORd-derated. Market Rule 1
§III.13.1.2.2.1.1 (eff. 2025-05-03) defines an Existing Generating Capacity
Resource's summer QC as the median of its own last 5 years of Seasonal
Claimed Capability — an undiscounted claimed-output figure; a full-text
search of the 235-page III.13/III.14 tariff text for "EFORd" returns zero
matches. EFORd instead enters only the system-wide GE MARS/ICR reliability
simulation (ICR Reference Guide §5.6.1) that sizes the *aggregate* Forward
Capacity Auction procurement target — not any individual resource's own
accredited value. Individual forced-outage/performance risk is priced
separately, ex post, through Pay-for-Performance: got the full verbatim
Capacity Scarcity Condition trigger (§III.13.7.2.1) and Performance Payment
Rate schedule (§III.13.7.2.5) — $2,000 → $3,500 → $5,455 →
**$9,337/MWh (current)**, with ISO-NE's own pending FERC petition to cut it
to $3,500/MWh. **Dating caveat:** the FCM itself sunsets after the
CCP2027-2028 delivery year (final FCA already held, February 2024); the
QC/PFP mechanism described is the current-through-sunset one, not
researched against whatever accreditation-reform process succeeds it.

## MANUAL DOWNLOADS NEEDED (consolidated, blocked or not located this pass)

### PJM
- 2024/2025 RPM BRA "Planning Period Parameters" narrative PDF — both the
  `-pdf.pdf` and `-pdf.ashx` URL patterns 404 (fetched from two different
  search hits each). Likely genuinely never published as a standalone PDF
  for this compressed-schedule year; the XLSX workbook was used instead.
- Monitoring Analytics independent avoidable-cost benchmark table — not a
  fetch failure, a documented negative search result (see §4 above; the full
  2025 SOM Section 5 was searched and does not contain one).
- `agreements.pjm.com/oatt/*` and `.../eTariff/transformedTariffs/oatt/Sections/*.html`
  for OATT Part V §113.1 (Notice of Deactivation) — the `oatt/<id>` route is
  an unrenderable Angular SPA (844-byte shell); the `Sections/<id>.html`
  route *does* serve static HTML (confirmed on other section ids) but no
  document id mapping to Part V/§113 was found (no sitemap/search endpoint
  worked). Would settle the Manual-14D revision-history discrepancy (§6).

### NYISO
- Standalone "Demand Curve Parameters CY 2021-2022/2022-2023" one-pagers (if
  they exist) — not located; `net_cone`/`price_cap` are absent from this
  intake for those two years as a result.
- NYSRC IRM Study "Appendices" PDFs (separate from the Report Body fetched)
  — referenced by the Report Body's own text as containing "Appendix D,
  Table D.1.1," a numeric year-by-year UCAP-reserve-margin-trend table that
  would give exact historical NYISO translation-factor values (R5a); not
  fetched this session.
- A NYCA-wide (non-locational) worked UCAP-translation numeric example —
  only the NYC-specific (5.18%) example was found.
- `web.archive.org` is unreachable from this environment (both curl and
  WebFetch) — blocked all Wayback Machine lookups attempted across every
  agent this session.

### MISO
- PY2026-27 PRA Results Posting
  (`cdn.misoenergy.org/2026%20PRA%20Results%20Posting%2020260428754715.pdf`)
  — HTTP 403 direct and via the misoenergy.org events page; no state-PSC
  mirror located yet (likely too soon after the April 2026 auction).
- `https://www.misoenergy.org/legal/rules-manuals-and-agreements/tariff/`
  and every `cdn.misoenergy.org`/`docs.misoenergy.org` Attachment Y URL
  tried — **HTTP 403 on every attempt, every agent, this entire session.**
  This is the same MISO-403 pattern documented in the P-0B precedent
  (`docs/handoffs/capacity-market-intake-2026-07.md`) and in the pre-existing
  `data/raw/miso-pra/SOURCES.md`. Given three independent agents hit this
  identically across `misoenergy.org`, `docs.misoenergy.org`, and
  `cdn.misoenergy.org` today, **this reads as a standing egress-policy block
  for this domain in this environment, not an intermittent site-side
  issue** — flagging for the owner per the proxy README's "report the
  blocked host" instruction, since no amount of retrying or technique-
  switching will resolve it from inside this session.
- `ferc.gov/news-events/news/...` (the ER23-630 order/concurrence) and
  `ferc.gov/media/er23-630-000` — HTTP 403 via both curl and WebFetch.
  `etariff.ferc.gov/TariffBrowser.aspx?tid=1162` returns HTTP 200 but is a
  JS-shell with no server-rendered content at the entry URL.

## Pre-existing repo issues noted (not caused by, not fixed by this session)

- `tests/test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`
  and `tests/test_data_dictionary_sync.py::test_every_schema_has_a_section`
  both fail **pre-existing on origin/main**, unrelated to this session:
  roughly 11 datatypes with a committed `schema.yaml` were never added to
  `scripts/regenerate_clean.py::DATATYPES` / `tests/test_clean_io.py::ALL_DATATYPES`
  / `scripts/render_data_dictionary.py::DATATYPE_ORDER` by whichever session
  added each of them (`storage-as-awards`, `nrel-atb`,
  `uranium-marketing-price`, `ira-credit-parameters`,
  `carbon-auction-results`, `eia-aeo-fuel-prices`, and others). This
  session's own new `capacity-market-avoidable-cost-rate` datatype **is**
  correctly registered in `regenerate_clean.DATATYPES` and
  `test_clean_io.py::ALL_DATATYPES` (verified: adds zero new drift to either
  test), but was deliberately **not** added to
  `render_data_dictionary.py`/`data/dictionary/data-dictionary.md` — a full
  regeneration of the doc would also have pulled in an unrelated
  `transfer-constraint-binding` coverage-matrix regression (this session's
  local `data/clean` is empty, so a fresh render shows it losing its
  previously-recorded 2023–2025 span) and a stale pre-existing demand-curve
  doc/schema drift, both out of this session's scope to fix. A future
  session should add `"capacity-market-avoidable-cost-rate"` to
  `DATATYPE_ORDER` plus a `NARRATIVE` entry (trivially reconstructable from
  the schema's own docstring) and re-run
  `python scripts/render_data_dictionary.py` from an environment with the
  clean tree regenerated first.
